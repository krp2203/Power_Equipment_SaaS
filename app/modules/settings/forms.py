from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SelectField, SubmitField, TextAreaField, PasswordField
from wtforms.validators import DataRequired, Email, Length
from flask_wtf.file import FileField, FileAllowed

class OrganizationSettingsForm(FlaskForm):
    primary_color = StringField('Primary Theme Color', validators=[DataRequired()], description="Hex code (e.g. #DC2626)")
    company_logo = FileField('Company Logo', validators=[FileAllowed(['jpg', 'png'], 'Images only!')])

    slug = StringField('SaaS Subdomain Slug', description="Unique ID for your website URL (e.g. 'dealername').")
    
    enable_ari = BooleanField('Enable ARI PartSmart')
    ari_dealer_id = StringField('ARI Dealer ID')
    
    enable_pos = BooleanField('Enable POS Integration')
    pos_provider = SelectField('POS Provider', choices=[('ideal', 'Ideal'), ('csystems', 'C-Systems'), ('commander', 'Commander'), ('none', 'None')], default='none')
    pos_bridge_key = StringField('POS Bridge Key', description="Secret key for local sync script.")
    
    # Module Toggles (For Admin use)
    module_pos_sync = BooleanField('Module: POS Sync')
    module_facebook = BooleanField('Module: Facebook Marketing')
    module_ari = BooleanField('Module: ARI PartSmart')

    facebook_page_id = StringField('Facebook Page ID')
    facebook_access_token = StringField('Facebook Access Token')

    # Hero Customization
    hero_title = StringField('Hero Title', description="Main headline on the homepage")
    hero_tagline = StringField('Hero Tagline', description="Sub-headline below the title")
    hero_show_logo = BooleanField('Show Logo in Hero Section', description="Display the company logo above the title")
    
    # Brands Customization
    brand_logo_1 = FileField('Brand Logo 1', validators=[FileAllowed(['jpg', 'png', 'webp'], 'Images only!')])
    brand_logo_2 = FileField('Brand Logo 2', validators=[FileAllowed(['jpg', 'png', 'webp'], 'Images only!')])
    brand_logo_3 = FileField('Brand Logo 3', validators=[FileAllowed(['jpg', 'png', 'webp'], 'Images only!')])
    brand_logo_4 = FileField('Brand Logo 4', validators=[FileAllowed(['jpg', 'png', 'webp'], 'Images only!')])
    brand_logo_5 = FileField('Brand Logo 5', validators=[FileAllowed(['jpg', 'png', 'webp'], 'Images only!')])
    brand_logo_6 = FileField('Brand Logo 6', validators=[FileAllowed(['jpg', 'png', 'webp'], 'Images only!')])
    brand_logo_7 = FileField('Brand Logo 7', validators=[FileAllowed(['jpg', 'png', 'webp'], 'Images only!')])
    brand_logo_8 = FileField('Brand Logo 8', validators=[FileAllowed(['jpg', 'png', 'webp'], 'Images only!')])

    # Features Customization
    feat_inventory_title = StringField('Inventory Section Title')
    feat_inventory_text = TextAreaField('Inventory Section Description')
    feat_parts_title = StringField('Parts Section Title')
    feat_parts_text = TextAreaField('Parts Section Description')
    feat_service_title = StringField('Service Section Title')
    feat_service_text = TextAreaField('Service Section Description')

    # Contact Customization
    contact_phone = StringField('Contact Phone')
    contact_email = StringField('Contact Email')
    contact_address = TextAreaField('Contact Address')
    contact_text = TextAreaField('Contact Page Message', description="Message above contact details")
    
    submit = SubmitField('Save Settings')

class AddUserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    password = PasswordField('Temporary Password', validators=[DataRequired(), Length(min=6)])
    role = SelectField('Role', choices=[('admin', 'Admin'), ('user', 'User')], default='user')
    submit = SubmitField('Add User')

class EditUserForm(FlaskForm):
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    role = SelectField('Role', choices=[('admin', 'Admin'), ('user', 'User')])
    submit = SubmitField('Save Changes')
