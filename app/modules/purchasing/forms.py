from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, DateField, SelectField
from wtforms.validators import DataRequired, Optional, Email


class VendorForm(FlaskForm):
    name = StringField('Vendor Name', validators=[DataRequired()])
    account_number = StringField('Account Number', validators=[Optional()])
    contact_name = StringField('Contact Name', validators=[Optional()])
    phone = StringField('Phone', validators=[Optional()])
    email = StringField('Email', validators=[Optional(), Email()])
    address = StringField('Address', validators=[Optional()])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Save Vendor')


class PurchaseOrderForm(FlaskForm):
    vendor_id = SelectField('Vendor', coerce=int, validators=[DataRequired()])
    order_date = DateField('Order Date', validators=[Optional()])
    expected_date = DateField('Expected Date', validators=[Optional()])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Create Purchase Order')
