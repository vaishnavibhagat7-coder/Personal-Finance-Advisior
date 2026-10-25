from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, SelectField, TextAreaField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Optional, NumberRange, EqualTo
from app.auth.forms import OCCUPATION_CHOICES, CURRENCY_CHOICES


class ProfileForm(FlaskForm):
    full_name = StringField('Full Name', validators=[
        DataRequired(message='Full name is required.'),
        Length(min=2, max=100)
    ])
    email = StringField('Email Address', validators=[
        DataRequired(message='Email is required.'),
        Email()
    ])
    occupation = SelectField('Occupation', choices=OCCUPATION_CHOICES)
    currency = SelectField('Default Currency Symbol', choices=CURRENCY_CHOICES)
    monthly_income_target = DecimalField('Monthly Income Target', places=2, default=0.00, validators=[
        Optional(),
        NumberRange(min=0.00)
    ])
    monthly_savings_target = DecimalField('Monthly Savings Target', places=2, default=0.00, validators=[
        Optional(),
        NumberRange(min=0.00)
    ])
    financial_priorities = TextAreaField('Financial Priorities', validators=[
        Optional(),
        Length(max=500, message='Priorities text must be under 500 characters.')
    ])
    financial_notes = TextAreaField('Financial Notes / Context for AI Advisor', validators=[
        Optional(),
        Length(max=1000, message='Notes must be under 1000 characters.')
    ])
    submit = SubmitField('Update Financial Profile')


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[
        DataRequired(message='Please enter your current password.')
    ])
    new_password = PasswordField('New Password', validators=[
        DataRequired(message='Please enter a new password.'),
        Length(min=6, message='Password must be at least 6 characters long.')
    ])
    confirm_new_password = PasswordField('Confirm New Password', validators=[
        DataRequired(message='Please confirm your new password.'),
        EqualTo('new_password', message='New passwords must match.')
    ])
    submit = SubmitField('Change Password')
