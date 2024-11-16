from datetime import date
from sqlalchemy import ForeignKey, Integer, String, Text
from flask import Flask, abort, render_template, redirect, url_for, flash,request
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user,login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
# Import your forms from the forms.py
from forms import CreatePostForm
import requests
import datetime as dt
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm
from captcha.image import ImageCaptcha
import random
import string
import os
from flask import Flask, render_template, redirect, url_for, request, session
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email
import time
from forms import CommentForm
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email
import random
from flask_ckeditor import CKEditor,CKEditorField
'''
Make sure the required packages are installed: 
Open the Terminal in PyCharm (bottom left). 

On Windows type:
python -m pip install -r requirements.txt

On MacOS type:
pip3 install -r requirements.txt

This will install the packages from the requirements.txt for this project.
'''

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
ckeditor = CKEditor(app)
Bootstrap5(app)

# TODO: Configure Flask-Login


# CREATE DATABASE
class Base(DeclarativeBase):
    pass# Database setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
list_of_companies = ["Tesla Inc", "Apple Inc", "Microsoft Corporation"]
listed_companies= random.choice(list_of_companies)
db = SQLAlchemy(model_class=Base)
db.init_app(app)
STOCK = "TSLA"
OWN_EMAIL = "abc066194@gmail.com"
OWN_PASSWORD = "lnwljxkdoguhavqm"
NEWS_URL = "https://newsapi.org/v2/everything?"
news_apikey = "b63590d06cb6464199b88a36800af0d7"
COMPANY_NAME = f"{listed_companies}"

news_parameters = {
    "qInTitle": COMPANY_NAME,
    "apiKey": news_apikey
}

news_response = requests.get(url=NEWS_URL, params=news_parameters)
articles = news_response.json().get("articles", [])
ten_articles = articles[:6]
site_key = "6LdJ82wqAAAAABhfgOo4teRsWDhTejwHXQ9B8Y_Q"
secret_key = "6LdJ82wqAAAAABuFMKsttcj5xuC7cLUZgyyJcVul"
login_manager = LoginManager()
login_manager.init_app(app)

# Define the login view
login_manager.login_view = 'login'
# CONFIGURE TABLES


gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)
# User model
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(100))

# BlogPost model
class BlogPost(db.Model):
    __tablename__ = 'blog_posts'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    subtitle: Mapped[str] = mapped_column(String(100), nullable=True)
    date: Mapped[str] = mapped_column(String(20), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str] = mapped_column(String(250), nullable=False)
    img_url: Mapped[str] = mapped_column(String(300), nullable=True)

# Comment model
class Comment(db.Model):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
with app.app_context():
    db.create_all()


with app.app_context():
        try:
            with open("../specified_number.txt", 'r') as file:
                number = int(file.read().strip())
        except (FileNotFoundError, ValueError):
            number = 0

        for article_number, article in enumerate(ten_articles, start=1):
            title = article["title"]
            description = article.get("description", "")
            link = article["url"]

            # Only increment the number if the title is unique
            existing_post = BlogPost.query.filter_by(title=title).first()
            if existing_post:
                print(f"Skipping duplicate article: {title}")
                continue

            number += 1
            with open("../specified_number.txt", 'w') as file:
                file.write(str(number))

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


class CaptchaForm(FlaskForm):
    captcha = StringField("Enter the CAPTCHA", validators=[DataRequired()])
    submit = SubmitField("Submit")

CAPTCHA_FOLDER = "static/captchas"
if not os.path.exists(CAPTCHA_FOLDER):
    os.makedirs(CAPTCHA_FOLDER)

class CommentForm(FlaskForm):
    comment_text = CKEditorField("Comment", validators=[DataRequired()])
    submit = SubmitField("Submit Comment")
# Function to generate random CAPTCHA text

# Function to generate CAPTCHA image

# Function to generate random CAPTCHA text

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def generate_captcha_text(length=5):
    letters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(letters) for _ in range(length))


def generate_captcha_image(text):
    image = ImageCaptcha(width=280, height=90)
    image_path = f"{CAPTCHA_FOLDER}/{text}.png"
    image.write(text, image_path)
    return f"{text}.png"
def generate_and_store_captcha():
    captcha_text = generate_captcha_text()
    captcha_image_path = generate_captcha_image(captcha_text)
    session["captcha_text"] = captcha_text
    session["captcha_image_path"] = captcha_image_path
    return captcha_image_path


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
    posts = BlogPost.query.all()
    return render_template("index.html", all_posts=posts)


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
        print(session.get("captch_text"))

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
            img_url=form.img_url.data,
            author=current_user  # Link to the User instance
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
    requested_post = BlogPost.query.get_or_404(post_id)
    comment_form = CommentForm()

    if comment_form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to login or register to comment.")
            return redirect(url_for("login"))

        new_comment = Comment(
            text=comment_form.comment_text.data,
            comment_author=current_user,
            parent_post=requested_post
        )
        db.session.add(new_comment)
        db.session.commit()
        flash("Comment added!", "success")
        return redirect(url_for("show_post", post_id=post_id))

    return render_template("post.html", post=requested_post, current_user=current_user, form=comment_form)
@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


if __name__ == "__main__":
    app.run(debug=True, port=5002)
