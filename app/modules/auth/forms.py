from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


class ProfileForm(FlaskForm):
    first_name = StringField('First Name', validators=[Length(max=100)])
    last_name = StringField('Last Name', validators=[Length(max=100)])
    email = StringField('Email Address', validators=[Email(), Length(max=120)])
    submit_profile = SubmitField('Update Profile')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6, message="Password must be at least 6 characters.")])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password', message='Passwords must match.')])
    submit_password = SubmitField('Change Password')

from wtforms import HiddenField, BooleanField
from app.core.models import User, Organization
from wtforms.validators import ValidationError

class SignupForm(FlaskForm):
    # Organization Details
    org_name = StringField('Business Name', validators=[DataRequired(), Length(min=2, max=100)])
    subdomain = StringField('Desired Subdomain', validators=[DataRequired(), Length(min=3, max=20)])
    address = StringField('Business Address', validators=[DataRequired()])
    
    # Manager Details
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    
    # Plan Selection
    add_facebook = BooleanField('Add Facebook Marketing Module (+$69/mo)')
    
    # Payment
    card_nonce = HiddenField('card_nonce', validators=[]) # Populated by JS
    
    submit = SubmitField('Complete & Pay')

    def validate_subdomain(self, field):
        if Organization.query.filter_by(slug=field.data.lower()).first():
            raise ValidationError('This subdomain is already taken. Please choose another.')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError('This email is already registered.')


