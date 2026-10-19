from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, NumberRange
from flask_wtf.file import FileField, FileAllowed


class RentalItemForm(FlaskForm):
    name = StringField('Item Name', validators=[DataRequired(), Length(max=150)])
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
    image = FileField('Image (optional)', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'webp', 'gif'], 'Images only!')],
        description="Leave blank to use a generic icon for this item.")
    submit = SubmitField('Save Rental Item')
