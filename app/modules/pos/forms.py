from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, DecimalField, SubmitField
from wtforms.validators import DataRequired, Optional, Email, NumberRange


class CustomerForm(FlaskForm):
    first_name = StringField('First Name', validators=[Optional()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    company = StringField('Company', validators=[Optional()])
    address = StringField('Address', validators=[Optional()])
    phone = StringField('Phone', validators=[Optional()])
    email = StringField('Email', validators=[Optional(), Email()])
    tax_exempt = BooleanField('Tax Exempt')
    is_commercial = BooleanField('Commercial Account')
    default_discount_percent = DecimalField('Default Discount %', validators=[Optional(), NumberRange(min=0, max=100)], places=2)
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Save Customer')
