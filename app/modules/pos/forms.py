from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Optional, Email


class CustomerForm(FlaskForm):
    first_name = StringField('First Name', validators=[Optional()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    company = StringField('Company', validators=[Optional()])
    address = StringField('Address', validators=[Optional()])
    phone = StringField('Phone', validators=[Optional()])
    email = StringField('Email', validators=[Optional(), Email()])
    tax_exempt = BooleanField('Tax Exempt')
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Save Customer')
