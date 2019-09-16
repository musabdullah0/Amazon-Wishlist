from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, DecimalField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Length, ValidationError, Email, EqualTo
from flask_login import current_user
from amazon_wishlist.models import User, Item


def validate_length(self, asin):
    if len(asin.data) != 10:
        raise ValidationError('ASIN must be 10 characters in length')


class ItemForm(FlaskForm):
    asin = StringField('Amazon Standard Identification Number',
                       validators=[DataRequired(), validate_length])
    alert_price = DecimalField(places=2)
    submit = SubmitField('Add Item')


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=10)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=2, max=10)])
    submit = SubmitField('Log In')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=10)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=2, max=10)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already taken')


class UpdateAccountForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=10)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    picture = FileField('Update Profile Pic', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Update Account')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Username already taken')

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Email already taken')


class UpdateItemForm(FlaskForm):
    title = StringField('Item Title', validators=[DataRequired()])
    price = DecimalField(places=2)
    alert_price = DecimalField(places=2)
    submit = SubmitField('Update Item')