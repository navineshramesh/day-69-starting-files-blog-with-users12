import captcha
from flask import Flask, abort, render_template, redirect, url_for, flash, request, session
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor,CKEditorField
from flask_gravatar import Gravatar
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
from functools import wraps
import transformers
from captcha.image import ImageCaptcha
import requests
import datetime as dt
import smtplib
import random
import torch
import string
import os
import sqlite3

# Import your forms from forms.py
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from generator import generate_long_paragraph
import flask_bootstrap

class CommentForm(FlaskForm):
    comment = CKEditorField("Comment", validators=[DataRequired()])
    submit = SubmitField("Submit Comment")
# Initialize the Flask app and configurations
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("Flask_key")
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DB_URI")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

ckeditor = CKEditor(app)
Bootstrap5(app)



# Initialize SQLAlchemy and Flask-Login
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
list_of_companies = ["Tesla Inc", "Apple Inc", "Microsoft Corporation"]
listed_companies= random.choice(list_of_companies)

db.init_app(app)
STOCK = "TSLA"

NEWS_URL = "https://newsapi.org/v2/everything?"
news_apikey = os.environ.get("Api_key")
COMPANY_NAME = f"{listed_companies}"

news_parameters = {
    "qInTitle": COMPANY_NAME,
    "apiKey": news_apikey,
    "PageSize":5
}

news_response = requests.get(url=NEWS_URL, params=news_parameters)
articles = news_response.json().get("articles", [])
ten_articles = articles[:6]
# Gravatar setup
gravatar = Gravatar(app, size=100, rating='g', default='retro')

# CAPTCHA setup
CAPTCHA_FOLDER = "static/captchas"
if not os.path.exists(CAPTCHA_FOLDER):
    os.makedirs(CAPTCHA_FOLDER)

# Database Models
class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str] = mapped_column(String(250), nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)
    comments = relationship("Comment", back_populates="parent_post")


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(100))
    comments = relationship("Comment", back_populates="comment_author")

class Comment(db.Model):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    # Child relationship:"users.id" The users refers to the tablename of the User class.
    # "comments" refers to the comments property in the User class.
    author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    comment_author = relationship("User", back_populates="comments")
    # Child Relationship to the BlogPosts
    post_id: Mapped[str] = mapped_column(Integer, db.ForeignKey("blog_posts.id"))
    parent_post = relationship("BlogPost", back_populates="comments")



with app.app_context():
    db.create_all()


with app.app_context():
        try:
            with open("specified_number.txt", 'r') as file:
                number = int(file.read().strip())
        except (FileNotFoundError, ValueError):
            number = 0

        for article_number, article in enumerate(ten_articles, start=1):
            title = article["title"]

            link = article["url"]

            # Only increment the number if the title is unique
            existing_post = BlogPost.query.filter_by(title=title).first()
            if existing_post:
                print(f"Skipping duplicate article: {title}")
                continue

            number += 1
            with open("specified_number.txt", 'w') as file:
                file.write(str(number))
            description = generate_long_paragraph(title,max_length=450)
            new_post = BlogPost(
                title=title,
                subtitle="Breaking News",
                body=f"{description}\n<a href='{link}'>Click here for more info</a>",
                author="Navinesh Ramesh",
                img_url="https://imgs.search.brave.com/BW__i2u-_aUDX7WcqOc0ZZIrdXUDN73s-jcnwRqSN8k/rs:fit:1024:704:1/g:ce/aHR0cHM6Ly9zdGF0/aWMwMS5ueXQuY29t/L2ltYWdlcy8yMDEx/LzAxLzE0L2FydHMv/MTRNT1ZJTkctc3Bh/bi9NT1ZJTkctanVt/Ym8uanBn",
                date=str(dt.datetime.today())
            )

            db.session.add(new_post)
            db.session.commit()
            print("Article added successfully.")


# Helper Functions for CAPTCHA
def generate_captcha_text(length=5):
    letters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(letters) for _ in range(length))


def generate_captcha_image(text):
    image = ImageCaptcha(width=280, height=90)
    image_path = f"{CAPTCHA_FOLDER}/{text}.png"
    image.write(text, image_path)
    return f"{text}.png"


# User Loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# Admin-only decorator
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.id != 1:
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function


# Create all tables
with app.app_context():
    db.create_all()


# Routes
@app.route('/')
def get_all_posts():
    # Query all blog posts ordered by 'id' in descending order (most recent first)
    posts = BlogPost.query.order_by(BlogPost.id.desc()).all()

    # Render the template with the posts
    return render_template("index.html", all_posts=posts,link=link,current_user=current_user)
@app.route("/terms")
def show_terms():
    return render_template("legalterms.html")
@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.captcha.data != session.get("captcha_text"):
            flash("Incorrect CAPTCHA, please try again.", "danger")
            return redirect(url_for('register'))

        session.pop("captcha_text", None)
        session.pop("captcha_image_path", None)

        if User.query.filter_by(email=form.email.data).first():
            flash("You've already signed up with that email, log in instead!", "info")
            return redirect(url_for('login'))

        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256', salt_length=8)
        new_user = User(email=form.email.data, name=form.name.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        flash("Registration successful! Welcome!", "success")
        return redirect(url_for("get_all_posts"))

    if "captcha_text" not in session:
        captcha_text = generate_captcha_text()
        captcha_image_path = generate_captcha_image(captcha_text)
        session["captcha_text"] = captcha_text
        session["captcha_image_path"] = captcha_image_path

    captcha_image = session.get("captcha_image_path")
    return render_template("register.html", form=form, captcha_image=captcha_image)


@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        if form.captcha.data != session.get("captcha_text"):
            flash("Incorrect CAPTCHA, please try again.", "danger")
            return redirect(url_for('login'))

        session.pop("captcha_text", None)
        session.pop("captcha_image_path", None)

        user = User.query.filter_by(email=form.email.data).first()
        if not user or not check_password_hash(user.password, form.password.data):
            flash("Invalid credentials, please try again.", "danger")
            return redirect(url_for('login'))

        login_user(user)
        return redirect(url_for('get_all_posts'))

    if "captcha_text" not in session:
        captcha_text = generate_captcha_text()
        captcha_image_path = generate_captcha_image(captcha_text)
        session["captcha_text"] = captcha_text
        session["captcha_image_path"] = captcha_image_path

    captcha_image = session.get("captcha_image_path")
    return render_template("login.html", form=form, captcha_image=captcha_image)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/new-post", methods=["GET", "POST"])
@login_required
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            date=date.today().strftime("%B %d, %Y"),
            body=form.body.data,
            author=current_user.name,
            img_url=form.img_url.data,
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)


@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@login_required
@admin_only
def edit_post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        body=post.body,
    )
    if form.validate_on_submit():
        post.title = form.title.data
        post.subtitle = form.subtitle.data
        post.img_url = form.img_url.data
        post.body = form.body.data
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)


@app.route("/delete/<int:post_id>")
@login_required
@admin_only
def delete_post(post_id):
    post_to_delete = BlogPost.query.get_or_404(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for("get_all_posts"))


@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    form = CommentForm()
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to log in to comment.")
            return redirect(url_for("login"))

        new_comment = Comment(
            text=form.comment.data,
            comment_author=current_user,
            parent_post=post
        )
        db.session.add(new_comment)
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))
    return render_template("post.html", post=post, form=form)
@app.route("/about")
def about():
    return render_template("about.html")
MAIL_ADDRESS = "defg0994@gmail.com"
MAIL_APP_PW = "gllaolnduoovudsq"
To_mail="navineshmail@gmail.com"

@app.route("/contact", methods=["GET", "POST"])
def contact():
   if request.method == "POST":
    data = request.form
    send_email(data["name"], data["email"], data["phone"], data["message"])
    return render_template("contact.html", msg_sent=True)
   return render_template("contact.html", msg_sent=False)
def send_email(name, email, phone, message):
   email_message = f"Subject:New Message\n\nName: {name}\nEmail: {email}\nPhone: {phone}\nMessage:{message}"
   with smtplib.SMTP("smtp.gmail.com", port=587) as connection:

         connection.starttls()
         connection.login(os.environ.get("Email"),os.environ.get("Password"))
         connection.sendmail(os.environ.get("Email"), os.environ.get("Toemail"), email_message)

if __name__ == "__main__":
    app.run(debug=False, port=5002)

