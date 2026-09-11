from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SelectField, SubmitField, TextAreaField, PasswordField, DecimalField
from wtforms.validators import DataRequired, InputRequired, Email, Length, NumberRange, Optional
from flask_wtf.file import FileField, FileAllowed

class OrganizationSettingsForm(FlaskForm):
    primary_color = StringField('Primary Theme Color', validators=[DataRequired()], description="Hex code (e.g. #DC2626)")
    company_logo = FileField('Company Logo', validators=[FileAllowed(['jpg', 'png'], 'Images only!')])

    slug = StringField('SaaS Subdomain Slug', description="Unique ID for your website URL (e.g. 'dealername').")
    custom_domain = StringField('Custom Domain', description="Optional: Use your own domain (e.g. 'bobsmowers.com'). Leave blank to use subdomain only.")
    
    ari_dealer_id = StringField('ARI Dealer ID')

    # Point of Sale / Service defaults
    default_tax_rate = DecimalField('Default Sales Tax %', validators=[Optional(), NumberRange(min=0, max=100)], places=3)
    default_labor_rate = DecimalField('Shop Labor Rate ($/hr)', validators=[Optional(), NumberRange(min=0)], places=2)

    facebook_page_id = StringField('Facebook Page ID')
    facebook_access_token = StringField('Facebook Access Token')

    # Hero Customization
    hero_title = StringField('Hero Title', description="Main headline on the homepage")
    hero_tagline = StringField('Hero Tagline', description="Sub-headline below the title")
    hero_show_logo = BooleanField('Show Logo in Hero Section', description="Display the company logo above the title")
    
    # Brands Customization
    brand_logo_1 = FileField('Brand Logo 1', validators=[FileAllowed(['jpg', 'png', 'webp', 'gif'], 'Images only!')])
    brand_logo_2 = FileField('Brand Logo 2', validators=[FileAllowed(['jpg', 'png', 'webp', 'gif'], 'Images only!')])
    brand_logo_3 = FileField('Brand Logo 3', validators=[FileAllowed(['jpg', 'png', 'webp', 'gif'], 'Images only!')])
    brand_logo_4 = FileField('Brand Logo 4', validators=[FileAllowed(['jpg', 'png', 'webp', 'gif'], 'Images only!')])
    brand_logo_5 = FileField('Brand Logo 5', validators=[FileAllowed(['jpg', 'png', 'webp', 'gif'], 'Images only!')])
    brand_logo_6 = FileField('Brand Logo 6', validators=[FileAllowed(['jpg', 'png', 'webp', 'gif'], 'Images only!')])
    brand_logo_7 = FileField('Brand Logo 7', validators=[FileAllowed(['jpg', 'png', 'webp', 'gif'], 'Images only!')])
    brand_logo_8 = FileField('Brand Logo 8', validators=[FileAllowed(['jpg', 'png', 'webp', 'gif'], 'Images only!')])

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

    # Social Media Links
    social_facebook = StringField('Facebook Profile URL', description="e.g. https://facebook.com/yourpage")
    social_instagram = StringField('Instagram Profile URL', description="e.g. https://instagram.com/yourprofile")
    social_twitter = StringField('Twitter/X Profile URL', description="e.g. https://twitter.com/yourhandle")
    social_linkedin = StringField('LinkedIn Company URL', description="e.g. https://linkedin.com/company/yourcompany")
    social_youtube = StringField('YouTube Channel URL', description="e.g. https://youtube.com/@yourchannel")
    social_bluesky = StringField('BlueSky Profile URL', description="e.g. https://bsky.app/profile/yourhandle.bsky.social")

    submit = SubmitField('Save Settings')

class AddUserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    password = PasswordField('Temporary Password', validators=[DataRequired(), Length(min=6)])
    role = SelectField('Role', choices=[('admin', 'Admin'), ('technician', 'Technician'), ('user', 'User')], default='user')
    submit = SubmitField('Add User')

class EditUserForm(FlaskForm):
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    role = SelectField('Role', choices=[('admin', 'Admin'), ('technician', 'Technician'), ('user', 'User')])
    submit = SubmitField('Save Changes')

class MarkupTierForm(FlaskForm):
    # InputRequired (not DataRequired) - DataRequired treats a parsed value of
    # 0 as "empty" and rejects it, which broke entering a tier starting at $0.00.
    min_cost = DecimalField('Cost From ($)', places=2,
        validators=[InputRequired(message="Enter a starting cost - use 0 for your lowest tier."),
                    NumberRange(min=0, message="Cost From can't be negative.")],
        description="The low end of this cost range, e.g. 0 for your first tier.")
    max_cost = DecimalField('Cost To ($, blank = no upper limit)', places=2,
        validators=[Optional(), NumberRange(min=0, message="Cost To can't be negative.")],
        description="The high end of this range. Leave blank for \"and up\" (no ceiling).")
    markup_percent = DecimalField('Markup %', places=2,
        validators=[InputRequired(message="Enter a markup percent - use 0 for no markup."),
                    NumberRange(min=0, message="Markup % can't be negative.")],
        description="How much to mark up dealer cost in this range, e.g. 55 for 55%.")
    submit = SubmitField('Save Tier')
