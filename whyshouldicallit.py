
import re
from sqlalchemy import Integer, String, Text, DateTime
import psycopg2
from flask import Flask, abort, render_template, redirect, url_for, flash, request, session, make_response
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor, CKEditorField
from flask_gravatar import Gravatar  # <-- Gravatar import added here
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
from datetime import datetime # <-- datetime import added here
import bleach
from functools import wraps
import time
import requests
import smtplib
import random
import secrets
import string
import os
import sqlite3
from email.mime.text import MIMEText  # <-- MIMEText import added here
print(bleach.__version__)
# Import your forms from forms.py
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm, ChatForm
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

# Setup the PostgreSQL connection
DATABASE_URL ="postgresql://postgres:PsgEFHReaBQuSHWtzysgEyhhlijcsODG@autorack.proxy.rlwy.net:57256/railway"

# Create a connection to PostgreSQL
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

cur.execute('SELECT version();')
db_version = cur.fetchone()
print("Connected to database:", db_version)

# Initialize the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("Flask_key")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['RECAPTCHA_cPUBLIC_KEY'] = '6LfPMYsqAAAAADWYYlBcpO2ngC8M6t5bfIfXRbTO'  # Public key (Site key)
app.config['RECAPTCHA_PRIVATE_KEY'] = '6LfPMYsqAAAAAHVtW7ll9IY5dh-Uj_WKb8GlrMIZ'  # Private key (Secret key)

# Initialize Flask extensions
ckeditor = CKEditor(app)
Bootstrap5(app)

# Flask-Login Setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Define your models
class Base(DeclarativeBase):
    pass

class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = mapped_column(Integer, primary_key=True)
    title = mapped_column(String(250), unique=True, nullable=False)
    subtitle = mapped_column(String(250), nullable=False)
    date = mapped_column(String(250), nullable=False)
    body = mapped_column(Text, nullable=False)
    author = mapped_column(String(250), nullable=False)
    img_url = mapped_column(String(250), nullable=False)
    comments = relationship("Comment", back_populates="parent_post")

class Comment(db.Model):
    __tablename__ = "comments"
    id = mapped_column(Integer, primary_key=True)
    text = mapped_column(Text, nullable=False)
    author_id = mapped_column(Integer, db.ForeignKey("users.id"))
    comment_author = relationship("User", back_populates="comments")
    post_id = mapped_column(Integer, db.ForeignKey("blog_posts.id"))
    parent_post = relationship("BlogPost", back_populates="comments")

class Chat(db.Model):
    __tablename__ = "chat_messages"
    id = db.Column(Integer, primary_key=True)
    chat_message = mapped_column(String(250), nullable=False)
    sender_name = mapped_column(String(250), nullable=False)
    sender_email = mapped_column(String(250), nullable=False)
    time_sent = mapped_column(DateTime, default=datetime.utcnow)

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = mapped_column(Integer, primary_key=True)
    email = mapped_column(String(100), unique=True)
    password = mapped_column(String(100))
    name = mapped_column(String(100))
    comments = relationship("Comment", back_populates="comment_author")

# Create the database tables
with app.app_context():
    db.create_all()

# Flask-Login User Loader
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Gravatar setup
gravatar = Gravatar(app, size=100, rating='g', default='retro')  # <-- Gravatar initialization added here
@app.template_filter('remove_newlines')
def remove_newlines(value):
    # Use a regex to find '\\n\\n' and replace it with an empty string
    return re.sub(r'\\n\\n', '', value)
# Security headers
@app.after_request
def set_security_headers(response):
    nonce_value = secrets.token_hex(16)
    response.headers['Content-Security-Policy'] = (
        f"default-src 'self' *; "
        f"script-src 'self' 'unsafe-inline' 'unsafe-eval' * cdn.ckeditor.com; "
        f"style-src 'self' 'unsafe-inline' * cdn.ckeditor.com; "
        f"font-src 'self' *; "
        f"img-src 'self' * data:; "
        f"connect-src 'self' *; "
        f"object-src 'none'; "
        f"frame-ancestors 'none'; "
        f"base-uri 'self'; "
        f"form-action 'self';"
    )
    response.headers['Strict-Transport-Security'] = "max-age=31536000; includeSubDomains; preload"
    response.headers['Referrer-Policy'] = "strict-origin-when-cross-origin"
    response.headers['X-Content-Type-Options'] = "nosniff"
    response.headers['X-Frame-Options'] = "DENY"
    response.headers['Cross-Origin-Resource-Policy'] = "same-origin"
    return response

# Admin-only decorator
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.id != 1:
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function
# Routes
@app.route('/')
def get_all_posts():
    # Query all blog posts ordered by 'id' in descending order (most recent first)
    posts = BlogPost.query.order_by(BlogPost.id.desc()).all()

    # Render the template with the posts
    return render_template("index.html", all_posts=posts,current_user=current_user)
@app.template_filter('regex_replace')
def regex_replace(value, pattern, replacement):
    return re.sub(pattern, replacement, value)
@app.route("/terms")
def show_terms():
    return render_template("privacyandpolicy.html")

@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()

    # Handle GET request: reset reCAPTCHA expiry time when the page is loaded
    if request.method == 'GET':
        # Reset the reCAPTCHA session expiry to 2 minutes after loading the page
        session['captcha_expiry'] = time.time() + 120  # 2 minutes from now

    # Handle POST request: when the user submits the registration form
    if form.validate_on_submit():
        # Check if the reCAPTCHA token has expired
        if 'captcha_expiry' in session and time.time() > session['captcha_expiry']:
            flash("Your session has expired, please refresh the page.", "warning")
            return redirect(url_for('register'))  # Reload the page to reset CAPTCHA

        # Retrieve the reCAPTCHA response token
        response_token = request.form.get('g-recaptcha-response')

        if not response_token:
            flash("Please verify your identity again.", "danger")
            return redirect(url_for('register'))  # Reload the page if no CAPTCHA token

        # Verify reCAPTCHA with the response token
        secret_key = app.config['RECAPTCHA_PRIVATE_KEY']
        if verify_recaptcha(response_token, secret_key):
            # Check if the email already exists in the database
            if User.query.filter_by(email=form.email.data).first():
                flash("You've already signed up with that email, log in instead!", "info")
                return redirect(url_for('login'))  # Redirect to login if email exists

            # Prevent the use of "php" in any of the form fields (for security reasons)
            if 'php' in form.email.data or 'php' in form.password.data or 'php' in form.name.data:
                abort(400, description="PHP links are not allowed.")


            # Hash the password before storing it in the database
            hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256', salt_length=8)
            sanitized_email = bleach.clean(form.email.data, tags=['b', 'i', 'u'])
            sanitized_name = bleach.clean(form.name.data, tags=['b', 'i', 'u'])

            # Create a new user and save them to the database
            new_user = User(email=sanitized_email, name=sanitized_name, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()

            # Log in the new user immediately after registration
            login_user(new_user)

            flash("Registration successful! Welcome!", "success")
            return redirect(url_for("get_all_posts"))  # Redirect to the main page after registration

        else:
            flash("Something went wrong, please try again.", "danger")
            return redirect(url_for('register'))  # Reload the page if reCAPTCHA fails

    return render_template("register.html", form=form)


@app.route('/chat', methods=['GET', 'POST'])
@login_required
def chat():
    form = ChatForm()

    # Handle form submission
    if form.validate_on_submit():
        # Create a new message
        new_message = Chat(chat_message=form.chat_message.data)

        # Sanitize the chat_message (the string) before saving it to the database
        sanitized_message = bleach.clean(new_message.chat_message, tags=['b', 'i', 'u'])

        # Update the new_message object with the sanitized message
        new_message.chat_message = sanitized_message
        sender_name = current_user.name
        sender_email = current_user.email
        time_sent = datetime.now()

        # Add the sanitized message to the database
        params = Chat(
            chat_message=sanitized_message,  # Ensure it's just the sanitized string
            sender_name=sender_name,
            sender_email=sender_email,
            time_sent=time_sent  # Corrected here
        )
        db.session.add(params)
        db.session.commit()

        # Redirect to the chat page to see the new message
        return redirect(url_for('chat'))

    # Fetch all chat messages from the database
    messages = Chat.query.order_by(Chat.id.desc()).all()


    return render_template('chat.html', form=form, messages=messages, current_user=current_user)
@app.route('/termsofuse')
def show_terms_of_use():
    return render_template('aup.html')
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    # Handle GET request, reset the CAPTCHA on page load
    if request.method == 'GET':
        # Ensure the reCAPTCHA session expires after 2 minutes (for fresh verification on next load)
        session['captcha_expiry'] = time.time() + 120  # 2 minutes from now

    # Handle POST request when user submits the form
    if form.validate_on_submit():
        # Check if CAPTCHA expired
        if 'captcha_expiry' in session and time.time() > session['captcha_expiry']:
            flash("Your session has expired, please refresh the page.", "warning")
            return redirect(url_for('login'))

        # Store the CAPTCHA expiry time for the next verification
        session['captcha_expiry'] = time.time() + 120  # Reset expiry time to 2 minutes

        response_token = request.form.get('g-recaptcha-response')

        # If the reCAPTCHA token is missing, return an error
        if not response_token:
            flash("reCAPTCHA verification failed. Please try again.", "danger")
            return redirect(url_for('login'))

        secret_key = app.config['RECAPTCHA_PRIVATE_KEY']

        try:
            # Verify the reCAPTCHA token with Google's API
            if not verify_recaptcha(response_token, secret_key):
                flash("reCAPTCHA verification failed. Please try again.", "danger")
                return redirect(url_for('login'))

            # Check user credentials
            user = User.query.filter_by(email=form.email.data).first()
            if not user or not check_password_hash(user.password, form.password.data):
                flash("Invalid credentials, please try again.", "danger")
            else:
                login_user(user)  # Log the user in
                flash("Login successful!", "success")
                return redirect(url_for('get_all_posts'))

        except Exception as e:
            flash("An error occurred during login. Please try again.", "danger")
            print(f"Error: {e}")
            return redirect(url_for('login'))  # Keep user on the login page

    return render_template("login.html", form=form)
@app.route('/profile')
def profile():

    user = current_user
    if not user:
        return "User not found", 404


    return render_template('profile-page.html', user=current_user, gravatar=gravatar)
@app.route('/delete_profile')
def delete_profile():
    user = current_user
    db.session.delete(user)
    db.session.commit()

    logout_user()
    flash("Successfully Deleted Account")
    return redirect(url_for('profile'))
def verify_recaptcha(response_token, secret_key):
    url = "https://www.google.com/recaptcha/api/siteverify"
    payload = {
        'secret': secret_key,
        'response': response_token,
        'remoteip': request.remote_addr  # Optional: Capture user's IP address
    }

    try:
        # Send POST request to Google's reCAPTCHA verification API
        response = requests.post(url, data=payload)
        response.raise_for_status()  # Raise HTTPError for bad status codes
        result = response.json()

        # Check if reCAPTCHA verification was successful
        if result.get('success'):
            return True
        else:
            # Handle reCAPTCHA error codes (e.g., timeout or duplicate)
            error_codes = result.get('error-codes', [])
            if 'timeout-or-duplicate' in error_codes:
                return True  # Ignore 'timeout-or-duplicate' error
            else:
                print("reCAPTCHA verification failed with errors:", error_codes)
                return False

    except requests.exceptions.RequestException as e:
        # Handle any request-related errors (e.g., network issues)
        print(f"Error during reCAPTCHA verification: {e}")
        return False
    except ValueError as e:
        # Handle JSON parsing errors
        print(f"Error parsing reCAPTCHA response JSON: {e}")
        return False



@app.route("/sitemap.xml")
def map():
    return  render_template("sitemap.xml")
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


@app.route("/post/<string:post_title>", methods=["GET", "POST"])
def show_post(post_title):
    # Assuming 'slug' or 'title' is a unique identifier for the post
    post = BlogPost.query.filter_by(title=post_title).first_or_404()  # Query by title or slug
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

        # Redirect to the same post after the comment is added
        return redirect(url_for("show_post", post_title=post.title))  # Use post_title instead of id

    return render_template("post.html", post=post, form=form)


@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact", methods=["GET", "POST"])
def contact():
   if request.method == "POST":
    data = request.form
    send_email(data["name"], data["email"], data["phone"], data["message"])
    try:
     text = f'Dear {data["name"]},\nThank you for reaching out to us. We’ve received your message and understand your concern. We sincerely apologize for any inconvenience you may have experienced.\nPlease rest assured that our team is currently reviewing the issue you raised. We take all feedback seriously and are committed to resolving your concern as quickly as possible. If we need any additional information from you to better address the matter, we will reach out.\nYour patience and understanding are greatly appreciated as we work toward a solution. Should you have any further questions or if there is anything else we can assist you with, please feel free to contact us.\nBest regards, Navinesh Ramesh'

     msg = MIMEText(text, 'plain', _charset='utf-8')
     send_reply(msg,data['email'])
     with (open("templates/complaints.html",'a') as file):

         file.write(f"\n<h1>{data['name']}<h1>\n<p>{data['message']}</p>")

    except Exception as e:
        print(e)
        return render_template("contact.html",msg_sent=False)
    return render_template("contact.html", msg_sent=True)
   return render_template("contact.html", msg_sent=False)
def send_email(name, email, phone, message):
   email_message = f"Subject:New Message\n\nName: {name}\nEmail: {email}\nPhone: {phone}\nMessage:{message}"
   with smtplib.SMTP("smtp.gmail.com", port=587) as connection:

         connection.starttls()
         connection.login(os.environ.get("Email"),os.environ.get("Password"))
         connection.sendmail(os.environ.get("Email"), os.environ.get("Toemail"), email_message)
def send_reply(message,to_email):

   with smtplib.SMTP("smtp.gmail.com", port=587) as connection:

         connection.starttls()
         connection.login(os.environ.get("Email"),os.environ.get("Password"))
         connection.sendmail(os.environ.get("Email"), to_email, msg=f"{message}")
@admin_only
@app.route('/complaints')
def complaints():
    return render_template("complaints.html")

if __name__ == "__main__":
    app.run(debug=True, port=5002)