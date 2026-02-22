from datetime import datetime
from flask_login import UserMixin
from sqlalchemy import UniqueConstraint
from app.core.extensions import db
import json
from decimal import Decimal

class Organization(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    settings = db.Column(db.JSON, default={}) # Stores active plugins, API keys etc.
    modules = db.Column(db.JSON, default={}) # Stores active Add-On flags e.g. {"ari": true}
    theme_config = db.Column(db.JSON, default={}) # Stores frontend branding e.g. colors, logo
    
    # Marketing Interface / SaaS Fields
    slug = db.Column(db.String(50), unique=True, index=True) # Identifying subdomain
    
    # Integrations
    ari_dealer_id = db.Column(db.String(50))
    pos_provider = db.Column(db.String(50), default='none')
    pos_bridge_key = db.Column(db.String(100))
    
    # Social Media
    # Social Media
    facebook_page_id = db.Column(db.String(100))
    facebook_access_token = db.Column(db.Text)
    facebook_user_token = db.Column(db.Text) # Long-lived user token
    facebook_page_token_expires = db.Column(db.DateTime, nullable=True)

    # Billing / Square
    customer_id = db.Column(db.String(100), nullable=True) # Square Customer ID
    subscription_id = db.Column(db.String(100), nullable=True) # Square Subscription ID
    subscription_status = db.Column(db.String(50), default='inactive') # active, past_due, canceled
    plan_type = db.Column(db.String(50), default='base') # base, base_plus_fb, etc.

    last_bridge_heartbeat = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    onboarding_complete = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    users = db.relationship('User', backref='organization', lazy=True)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    
    username = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='user')
    
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    
    # Standard Fields
    cell_phone = db.Column(db.String(50))
    title = db.Column(db.String(100))
    labor_rate = db.Column(db.Numeric(10, 2), nullable=True)
    
    # Settings
    password_reset_required = db.Column(db.Boolean, default=False, nullable=False)
    receive_automated_reports = db.Column(db.Boolean, default=False, nullable=False)
    
    notifications = db.relationship('Notification', backref='recipient', lazy=True, cascade="all, delete-orphan")
    labor_entries = db.relationship('LaborEntry', backref='user_rel', lazy=True)

    # Constraints
    __table_args__ = (
        UniqueConstraint('username', 'organization_id', name='_user_org_uc'),
        UniqueConstraint('email', 'organization_id', name='_email_org_uc'),
    )

class Dealer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)

    name = db.Column(db.String(150), nullable=False)
    address = db.Column(db.String(300))
    dealer_code = db.Column(db.String(50))
    dealer_dba = db.Column(db.String(150))
    notes = db.Column(db.Text)
    labor_rate = db.Column(db.Numeric(10, 2), nullable=True)
    username = db.Column(db.String(80))
    password = db.Column(db.String(80))
    manufacturers = db.Column(db.Text) 
    
    contacts = db.relationship('Contact', backref='dealer', cascade="all, delete-orphan", lazy=True)
    cases = db.relationship('Case', backref='dealer', lazy=True)
    dealer_notes = db.relationship('DealerNote', backref='dealer', cascade="all, delete-orphan", lazy=True)

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    
    dealer_id = db.Column(db.Integer, db.ForeignKey('dealer.id'), nullable=False)
    name = db.Column(db.String(100))
    role = db.Column(db.String(100))
    email = db.Column(db.String(100))
    phone = db.Column(db.String(50))

class DealerNote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)

    dealer_id = db.Column(db.Integer, db.ForeignKey('dealer.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('dealer_note.id'), nullable=True)
    text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.Column(db.String(80))
    replies = db.relationship('DealerNote', backref=db.backref('parent', remote_side=[id]), lazy='dynamic', cascade="all, delete-orphan")
    notifications = db.relationship('Notification', backref='dealer_note', lazy=True, cascade="all, delete-orphan")

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False) # Removed unique contraint globally, unique per org implicitly via logic or adding constraint later

case_tags = db.Table('case_tags',
    db.Column('case_id', db.Integer, db.ForeignKey('case.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

class Unit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)

    manufacturer = db.Column(db.String(100))
    model_number = db.Column(db.String(100))
    serial_number = db.Column(db.String(100), nullable=True) # Removed global unique constraint
    engine_model = db.Column(db.String(100))
    engine_serial = db.Column(db.String(100))
    owner_name = db.Column(db.String(100))
    owner_company = db.Column(db.String(100))
    owner_address = db.Column(db.String(200))
    owner_phone = db.Column(db.String(50))
    owner_email = db.Column(db.String(100))
    unit_hours = db.Column(db.String(50))
    type = db.Column(db.String(50)) # e.g. Mower, Chainsaw, Blower
    
    # Marketing / Inventory Flags
    is_owned = db.Column(db.Boolean, default=False)
    display_on_web = db.Column(db.Boolean, default=False)
    push_to_facebook = db.Column(db.Boolean, default=False)
    
    cases = db.relationship('Case', backref='unit', lazy=True)
    images = db.relationship('UnitImage', backref='unit', lazy=True, cascade="all, delete-orphan")

    # Inventory Specific
    price = db.Column(db.Numeric(10, 2), nullable=True)
    year = db.Column(db.Integer, nullable=True)
    condition = db.Column(db.String(50), default='New') # New, Used
    status = db.Column(db.String(50), default='Available') # Available, Sold, Pending
    description = db.Column(db.Text)
    is_inventory = db.Column(db.Boolean, default=False)
    
    # __table_args__ = (
    #     UniqueConstraint('serial_number', 'organization_id', name='_serial_org_uc'),
    # )

class UnitImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('unit.id'), nullable=False)
    image_url = db.Column(db.String(500), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Case(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)

    dealer_id = db.Column(db.Integer, db.ForeignKey('dealer.id'))
    unit_id = db.Column(db.Integer, db.ForeignKey('unit.id'))
    status = db.Column(db.String(50), default='New')
    case_type = db.Column(db.String(50), nullable=False, default='Support')
    assigned_to = db.Column(db.String(80))
    channel = db.Column(db.String(50))
    reference = db.Column(db.Text)
    is_visit = db.Column(db.Boolean, default=False)
    creation_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    appointment_date = db.Column(db.Date)
    follow_up_date = db.Column(db.DateTime(timezone=True))
    closed_date = db.Column(db.DateTime, nullable=True)
    reopened_date = db.Column(db.DateTime, nullable=True)
    email_reply_token = db.Column(db.String(100), nullable=True, index=True) # Unique per org maybe? kept simple for now
    caller_name = db.Column(db.String(100))
    
    notes = db.relationship('Note', backref='case', lazy=True, cascade="all, delete-orphan")
    notifications = db.relationship('Notification', backref='case', lazy=True, cascade="all, delete-orphan")
    attachments = db.relationship('Attachment', backref='case', lazy=True, cascade="all, delete-orphan")
    tags = db.relationship('Tag', secondary=case_tags, lazy='select', backref=db.backref('cases', lazy=True))
    parts_used = db.relationship('PartUsed', backref='case', lazy=True, cascade="all, delete-orphan")
    labor_entries = db.relationship('LaborEntry', backref='case', lazy=True, cascade="all, delete-orphan")

    @property
    def total_parts_cost(self):
        if not self.parts_used:
            return Decimal('0.00')
        return sum(part.quantity * part.cost_at_time_of_use for part in self.parts_used)

    @property
    def total_labor_cost(self):
        if not self.labor_entries:
            return Decimal('0.00')
        return sum(entry.hours_spent * entry.rate_at_time_of_log for entry in self.labor_entries)

    @property
    def total_repair_cost(self):
        return self.total_parts_cost + self.total_labor_cost

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)

    case_id = db.Column(db.Integer, db.ForeignKey('case.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('note.id'), nullable=True)
    text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.Column(db.String(80))
    email_reply_token = db.Column(db.String(100), nullable=True, index=True)
    notifications = db.relationship('Notification', backref='note', lazy=True, cascade="all, delete-orphan")
    replies = db.relationship('Note', backref=db.backref('parent', remote_side=[id]), lazy='dynamic', cascade="all, delete-orphan")

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)

    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    case_id = db.Column(db.Integer, db.ForeignKey('case.id'), nullable=True)
    note_id = db.Column(db.Integer, db.ForeignKey('note.id'), nullable=True)
    message = db.Column(db.String(255), nullable=False)
    dealer_note_id = db.Column(db.Integer, db.ForeignKey('dealer_note.id'), nullable=True)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Attachment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)

    case_id = db.Column(db.Integer, db.ForeignKey('case.id'), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    original_filename = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class PartUsed(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)

    case_id = db.Column(db.Integer, db.ForeignKey('case.id'), nullable=False)
    part_number = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    cost_at_time_of_use = db.Column(db.Numeric(10, 2), nullable=False)
    description_at_time_of_use = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class LaborEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)

    case_id = db.Column(db.Integer, db.ForeignKey('case.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    hours_spent = db.Column(db.Numeric(10, 2), nullable=False)
    rate_at_time_of_log = db.Column(db.Numeric(10, 2), nullable=False)
    description = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    action = db.Column(db.String(50), nullable=False) # CREATE, UPDATE, DELETE
    resource_type = db.Column(db.String(50), nullable=False) # Case, User, Bulletin
    resource_id = db.Column(db.String(50)) 
    
    changes = db.Column(db.JSON) # Only store what changed
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class ServiceBulletin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    
    sb_number = db.Column(db.String(50), nullable=False)
    issue_date = db.Column(db.Date, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    pdf_filename = db.Column(db.String(255))
    pdf_original_name = db.Column(db.String(255))
    warranty_code = db.Column(db.String(50))
    labor_hours = db.Column(db.String(100))
    required_parts = db.Column(db.Text, default='[]')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    affected_models = db.relationship('ServiceBulletinModel', backref='bulletin', lazy=True, cascade='all, delete-orphan')
    completions = db.relationship('ServiceBulletinCompletion', backref='bulletin', lazy=True, cascade='all, delete-orphan')
    
    __table_args__ = (
        UniqueConstraint('organization_id', 'sb_number', name='_org_sb_uc'),
    )

    @property
    def parsed_required_parts(self):
        if not self.required_parts: return []
        try: return json.loads(self.required_parts)
        except: return []

class ServiceBulletinModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    
    bulletin_id = db.Column(db.Integer, db.ForeignKey('service_bulletin.id'), nullable=False)
    model_name = db.Column(db.String(100), nullable=False)
    serial_start = db.Column(db.String(50), nullable=False)
    serial_end = db.Column(db.String(50), nullable=False)

class ServiceBulletinCompletion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    
    bulletin_id = db.Column(db.Integer, db.ForeignKey('service_bulletin.id'), nullable=False)
    serial_number = db.Column(db.String(50), nullable=False)
    model_name = db.Column(db.String(100))
    
    # Optional link to Unit if exists in system
    unit_id = db.Column(db.Integer, db.ForeignKey('unit.id'), nullable=True)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    completion_date = db.Column(db.DateTime, default=datetime.utcnow)
    completion_date = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)
    parts_used = db.Column(db.Text, default='[]')
    status = db.Column(db.String(50), default='Completed')
    
    user = db.relationship('User', backref='bulletin_completions')

class PartInventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    
    part_number = db.Column(db.String(100), nullable=False)
    manufacturer = db.Column(db.String(100))
    description = db.Column(db.String(255))
    stock_on_hand = db.Column(db.Integer, default=0)
    bin_location = db.Column(db.String(50))
    image_url = db.Column(db.String(255))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('part_number', 'manufacturer', 'organization_id', name='_part_manuf_org_uc'),
    )

class FacebookPost(db.Model):
    """Track Facebook posts with status for user visibility"""
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Post Content
    title = db.Column(db.String(200))
    message = db.Column(db.Text)
    media_type = db.Column(db.String(20))  # 'text', 'photo', 'video'
    media_url = db.Column(db.Text)  # Local URL to uploaded media

    # Status Tracking
    status = db.Column(db.String(20), default='pending')  # pending, uploading, success, failed
    facebook_post_id = db.Column(db.String(100))  # FB post ID if successful
    error_message = db.Column(db.Text)  # Error details if failed

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    posted_at = db.Column(db.DateTime)  # When successfully posted to FB

    # Relationships
    organization = db.relationship('Organization', backref='facebook_posts')
    user = db.relationship('User', backref='facebook_posts')

class MediaContent(db.Model):
    """Unified media assets for promotions across all channels (FB, IG, Website Banner)"""
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)

    # Content
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    media_url = db.Column(db.String(500), nullable=False)  # Image or video
    thumbnail_url = db.Column(db.String(500))  # Auto-generated from image or provided for video
    media_type = db.Column(db.String(20), default='image')  # 'image' or 'video'
    link_url = db.Column(db.String(500))  # Optional click-through URL

    # Destination Flags
    post_to_facebook = db.Column(db.Boolean, default=False)
    post_to_instagram = db.Column(db.Boolean, default=False)
    post_to_banner = db.Column(db.Boolean, default=False)

    # Scheduling
    scheduled_post_time = db.Column(db.DateTime, nullable=True)  # NULL = post now
    status = db.Column(db.String(50), default='draft')  # 'draft', 'scheduled', 'posted', 'failed'

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    organization = db.relationship('Organization', backref='media_content')
    scheduled_posts = db.relationship('ScheduledPost', backref='media_content', cascade='all, delete-orphan')


class ScheduledPost(db.Model):
    """Tracks where and when media content has been posted"""
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    media_content_id = db.Column(db.Integer, db.ForeignKey('media_content.id'), nullable=False)

    # Destination
    destination = db.Column(db.String(20), nullable=False)  # 'facebook', 'instagram', 'banner'

    # Timing
    scheduled_time = db.Column(db.DateTime, nullable=False)
    posted_time = db.Column(db.DateTime, nullable=True)

    # Status & Tracking
    status = db.Column(db.String(50), default='pending')  # 'pending', 'posted', 'failed'
    facebook_post_id = db.Column(db.String(100), nullable=True)  # Reference to FB post
    error_message = db.Column(db.Text, nullable=True)

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    organization = db.relationship('Organization', backref='scheduled_posts')


class Banner(db.Model):
    """Website banner management"""
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)

    # Content
    image_url = db.Column(db.String(500), nullable=False)  # Full-size image URL
    thumbnail_url = db.Column(db.String(500))  # Small preview
    title = db.Column(db.String(200), nullable=False)
    link_url = db.Column(db.String(500))  # Click destination

    # Display Control
    sort_order = db.Column(db.Integer, default=0)  # Display order
    start_date = db.Column(db.Date, nullable=True)  # Active period start
    end_date = db.Column(db.Date, nullable=True)  # Active period end
    is_active = db.Column(db.Boolean, default=True)

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    organization = db.relationship('Organization', backref='banners')
