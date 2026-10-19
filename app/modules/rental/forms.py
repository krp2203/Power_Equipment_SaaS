from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, NumberRange
from flask_wtf.file import FileField, FileAllowed


class RentalItemForm(FlaskForm):
    name = StringField('Item Name', validators=[DataRequired(), Length(max=150)])
    category = StringField('Category (optional)', validators=[Optional(), Length(max=100)],
        description="e.g. Lawn and Garden, Construction Equipment - groups items on your public page.")
    rate_hourly = DecimalField('Hourly Rate ($, optional)', places=2,
        validators=[Optional(), NumberRange(min=0, message="Rate can't be negative.")],
        description="Leave blank to hide this tier on your public page.")
    rate_4hr = DecimalField('4 Hour Rate ($, optional)', places=2,
        validators=[Optional(), NumberRange(min=0, message="Rate can't be negative.")],
        description="Leave blank to hide this tier on your public page.")
    rate_8hr = DecimalField('8 Hour Rate ($, optional)', places=2,
        validators=[Optional(), NumberRange(min=0, message="Rate can't be negative.")],
        description="Leave blank to hide this tier on your public page.")
    rate_24hr = DecimalField('24 Hour Rate ($, optional)', places=2,
        validators=[Optional(), NumberRange(min=0, message="Rate can't be negative.")],
        description="Leave blank to hide this tier on your public page.")
    rate_weekly = DecimalField('Weekly Rate ($, optional)', places=2,
        validators=[Optional(), NumberRange(min=0, message="Rate can't be negative.")],
        description="Leave blank to hide this tier on your public page.")
    deposit = DecimalField('Deposit ($, optional)', places=2,
        validators=[Optional(), NumberRange(min=0, message="Deposit can't be negative.")],
        description="Refundable deposit required to rent this item.")
    minimum_rental_price = DecimalField('Minimum Rental Price ($, optional)', places=2,
        validators=[Optional(), NumberRange(min=0, message="Price can't be negative.")],
        description="e.g. $48.00 for a 2 hour minimum - set alongside Minimum Rental Hours.")
    minimum_rental_hours = IntegerField('Minimum Rental Hours (optional)',
        validators=[Optional(), NumberRange(min=0, message="Hours can't be negative.")],
        description="e.g. 2, to show \"$48.00 / 2 hours\".")
    image = FileField('Image (optional)', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'webp', 'gif'], 'Images only!')],
        description="Leave blank to use a generic icon for this item.")
    submit = SubmitField('Save Rental Item')
