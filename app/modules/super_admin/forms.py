from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length

class CreateTenantForm(FlaskForm):
    org_name = StringField('Organization / Dealer Name', validators=[DataRequired(), Length(min=3, max=100)], description="e.g. Bob's Mowers")
    slug = StringField('Subdomain Slug', validators=[DataRequired(), Length(min=3, max=50)], description="e.g. bobsmowers (for bobsmowers.bentcrankshaft.com)")
    admin_username = StringField('Admin Username', validators=[DataRequired(), Length(min=3, max=50)], default="admin", description="Default: admin")
    admin_password = PasswordField('Admin Password', description="Optional: Leave blank to auto-generate a temporary password")
    custom_domain = StringField('Custom Domain (Optional)', validators=[Length(min=0, max=255)], description="e.g. bobsmowers.com (dealer can add this later)")

    submit = SubmitField('Create New Site')
