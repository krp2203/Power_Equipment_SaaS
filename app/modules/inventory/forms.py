from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DecimalField, IntegerField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Optional
from flask_wtf.file import FileField, FileAllowed

class InventoryItemForm(FlaskForm):
    manufacturer = StringField('Manufacturer', validators=[DataRequired()])
    model_number = StringField('Model Number', validators=[DataRequired()])
    type = StringField('Equipment Type', validators=[Optional()]) # e.g. Zero Turn, Tractor, etc.
    serial_number = StringField('Serial Number', validators=[Optional()])
    year = IntegerField('Year', validators=[Optional()])
    condition = SelectField('Condition', choices=[('New', 'New'), ('Used', 'Used')], default='New')
    price = DecimalField('Price ($)', validators=[DataRequired()])
    hours = StringField('Hours (if used)', validators=[Optional()])
    description = TextAreaField('Description')
    
    # Image upload (multiple not easily supported by standard FileField without custom widget, start with single/primary or handle specially)
    # We will use a simple file field for now, maybe add more later or handle multiple in route
    primary_image = FileField('Primary Image', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'webp'], 'Images only!')])
    
    status = SelectField('Status', choices=[('Available', 'Available'), ('Sold', 'Sold'), ('Pending', 'Pending')], default='Available')
    display_on_web = BooleanField('Display on Website', default=True)
    
    submit = SubmitField('Save Unit')

class PartInventoryForm(FlaskForm):
    part_number = StringField('Part Number', validators=[DataRequired()])
    manufacturer = StringField('Manufacturer', validators=[Optional()])
    description = StringField('Description', validators=[Optional()])
    stock_on_hand = IntegerField('Stock On Hand', default=0)
    bin_location = StringField('Bin Location', validators=[Optional()])
    image = FileField('Part Image', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'webp'], 'Images only!')])
    submit = SubmitField('Save Part')
