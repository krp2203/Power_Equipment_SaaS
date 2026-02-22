from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length

class CreateTenantForm(FlaskForm):
    org_name = StringField('Organization / Dealer Name', validators=[DataRequired(), Length(min=3, max=100)], description="e.g. Bob's Mowers")
    slug = StringField('Subdomain Slug', validators=[DataRequired(), Length(min=3, max=50)], description="e.g. bobsmowers (for bobsmowers.pes...)")
    admin_username = StringField('Admin Username', validators=[DataRequired(), Length(min=3, max=50)], default="admin", description="Default: admin")
    admin_password = PasswordField('Admin Password', description="Optional: Leave blank to auto-generate a temporary password")
    
    # In future we might want email, domain, etc.
    
    submit = SubmitField('Create New Site')
