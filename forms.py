from flask import Flask
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, URL, Email
from flask_ckeditor import CKEditorField
from flask_wtf.recaptcha import RecaptchaField
app = Flask(__name__)

app.config['RECAPTCHA_PUBLIC_KEY'] = '6LfPMYsqAAAAADWYYlBcpO2ngC8M6t5bfIfXRbTO'  # Public key (Site key)
app.config['RECAPTCHA_PRIVATE_KEY'] = '6LfPMYsqAAAAAHVtW7ll9IY5dh-Uj_WKb8GlrMIZ'  # Private key (Secret key)

# WTForm for creating a blog post
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")

class ChatForm(FlaskForm):
    chat_message= StringField("Chat_message", validators=[DataRequired()])


# Create a form to register new users
class RegisterForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    recaptcha = RecaptchaField()  # This is the reCAPTCHA field  # Ensure this line is present
    submit = SubmitField('Register')

# TODO: Create a LoginForm to login existing users
class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    recaptcha = RecaptchaField()  # This is the reCAPTCHA field  # Ensure this line is present
    submit = SubmitField("Login")


# TODO: Create a CommentForm so users can leave comments below posts
class CommentForm(FlaskForm):
    comment = CKEditorField('Comment', validators=[DataRequired()])
    submit = SubmitField('Submit')
