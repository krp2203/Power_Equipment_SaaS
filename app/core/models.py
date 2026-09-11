from datetime import datetime
from flask_login import UserMixin
from sqlalchemy import UniqueConstraint, func, text
from sqlalchemy.ext.hybrid import hybrid_property
from app.core.extensions import db
import json
from decimal import Decimal, InvalidOperation

class Organization(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    settings = db.Column(db.JSON, default={}) # Stores active plugins, API keys etc.
    modules = db.Column(db.JSON, default={}) # Stores active Add-On flags e.g. {"ari": true}
    theme_config = db.Column(db.JSON, default={}) # Stores frontend branding e.g. colors, logo
    
    # Marketing Interface / SaaS Fields
    slug = db.Column(db.String(50), unique=True, index=True) # Identifying subdomain
    custom_domain = db.Column(db.String(255), unique=True, index=True, nullable=True) # Custom domain mapping (e.g., ncpowerequipment.com)

    # Integrations
    ari_dealer_id = db.Column(db.String(50))

    # Social Media
    # Social Media
    facebook_page_id = db.Column(db.String(100))
    facebook_access_token = db.Column(db.Text)
    facebook_user_token = db.Column(db.Text) # Long-lived user token
    facebook_page_token_expires = db.Column(db.DateTime, nullable=True)

    # Billing / Square
    customer_id = db.Column(db.String(100), nullable=True) # Square Customer ID
    subscription_id = db.Column(db.String(100), nullable=True) # Square Subscription ID
    subscription_status = db.Column(db.String(50), default='trial') # trial, active, past_due, canceled, exempt (billing permanently opted-out, e.g. a personal test/goodwill account)
    plan_type = db.Column(db.String(50), default='base') # base, base_plus_fb, etc.
    monthly_price = db.Column(db.Integer, default=4900) # Cents. Per-org override, defaults to $49/mo base plan.
    trial_ends_at = db.Column(db.DateTime, nullable=True) # 10-day free trial expiry; no auto-action taken on expiry.

    is_active = db.Column(db.Boolean, default=True, nullable=False)
    onboarding_complete = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    users = db.relationship('User', backref='organization', lazy=True)
    invoice_payment_options = db.relationship(
        'InvoicePaymentOption', backref='organization', lazy=True,
        order_by='InvoicePaymentOption.sort_order, InvoicePaymentOption.id',
        cascade='all, delete-orphan')

    def _settings_decimal(self, key):
        try:
            v = (self.settings or {}).get(key)
            return Decimal(str(v)) if v not in (None, '') else None
        except (InvalidOperation, TypeError, ValueError):
            return None

    @property
    def default_tax_rate(self):
        """Default sales-tax percent for new invoices (from Settings)."""
        return self._settings_decimal('default_tax_rate') or Decimal('0')

    @property
    def default_labor_rate(self):
        """Shop labor rate per hour, used when a technician has no personal rate."""
        return self._settings_decimal('default_labor_rate')

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

    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True)

    cases = db.relationship('Case', backref='unit', lazy=True)
    images = db.relationship('UnitImage', backref='unit', lazy=True, cascade="all, delete-orphan")
    components = db.relationship('UnitComponent', backref='unit', lazy=True,
                                order_by='UnitComponent.id', cascade="all, delete-orphan")

    # Inventory Specific
    price = db.Column(db.Numeric(10, 2), nullable=True)
    year = db.Column(db.Integer, nullable=True)
    condition = db.Column(db.String(50), default='New') # New, Used
    status = db.Column(db.String(50), default='Available') # Available, Sold, Pending
    description = db.Column(db.Text)
    is_inventory = db.Column(db.Boolean, default=False)

    __table_args__ = (
        db.Index('ix_unit_org_customer', 'organization_id', 'customer_id'),
        db.Index('ix_unit_org_inventory', 'organization_id', 'is_inventory'),
    )

class UnitImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('unit.id'), nullable=False)
    image_url = db.Column(db.String(500), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class UnitComponent(db.Model):
    """Make/model/serial for a sub-assembly of a Unit - engine, transmission,
    deck, PTO, or an attachment."""
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('unit.id'), nullable=False)

    component_type = db.Column(db.String(60), nullable=False)  # Engine, Transmission, Deck, Attachment, ...
    manufacturer = db.Column(db.String(100))
    model_number = db.Column(db.String(100))
    serial_number = db.Column(db.String(100))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.Index('ix_unit_component_unit', 'unit_id'),
    )

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
    invoiced = db.Column(db.Boolean, default=False, nullable=False)

class LaborEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)

    case_id = db.Column(db.Integer, db.ForeignKey('case.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    hours_spent = db.Column(db.Numeric(10, 2), nullable=False)
    rate_at_time_of_log = db.Column(db.Numeric(10, 2), nullable=False)
    description = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    invoiced = db.Column(db.Boolean, default=False, nullable=False)

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

    # When True, this part appears on the dealer's public website parts list.
    # Off by default so price-file imports never dump the whole catalog online;
    # the part is always available in POS sales and service tickets regardless.
    display_on_web = db.Column(db.Boolean, default=False, nullable=False, server_default=db.false())

    # Pricing (from manufacturer/vendor price files)
    dealer_cost = db.Column(db.Numeric(10, 2), nullable=True)      # What the dealer pays the vendor
    retail_price = db.Column(db.Numeric(10, 2), nullable=True)     # Vendor's suggested/list retail price
    extended_price = db.Column(db.Numeric(10, 2), nullable=True)   # Dealer's actual selling price, computed from dealer_cost + MarkupTier
    upc = db.Column(db.String(50), nullable=True)
    superseded_to = db.Column(db.String(100), nullable=True)       # Replacement part number, if this one's discontinued

    vendor_id = db.Column(db.Integer, db.ForeignKey('vendor.id'), nullable=True)

    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('part_number', 'manufacturer', 'organization_id', name='_part_manuf_org_uc'),
        db.Index('ix_part_inventory_org', 'organization_id'),
        # Manufacturer filter + "distinct manufacturers" dropdown on the Parts page.
        db.Index('ix_part_inventory_org_mfg', 'organization_id', 'manufacturer'),
        # Trigram indexes so the "search as you type" part picker stays fast at
        # 100k+ parts per dealer (ILIKE '%term%' on part number / description).
        db.Index('ix_part_inventory_part_number_trgm', 'part_number',
                 postgresql_using='gin', postgresql_ops={'part_number': 'gin_trgm_ops'}),
        db.Index('ix_part_inventory_description_trgm', 'description',
                 postgresql_using='gin', postgresql_ops={'description': 'gin_trgm_ops'}),
        # Fast "negative stock" report / badge count.
        db.Index('ix_part_inventory_negative_stock', 'organization_id',
                 postgresql_where=text('stock_on_hand < 0')),
        # Fast "on the website" filter / badge count.
        db.Index('ix_part_inventory_web', 'organization_id',
                 postgresql_where=text('display_on_web')),
    )


class MarkupTier(db.Model):
    """Per-organization cost-range -> markup% rules, used to compute PartInventory.extended_price from dealer_cost."""
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)

    min_cost = db.Column(db.Numeric(10, 2), nullable=False)
    max_cost = db.Column(db.Numeric(10, 2), nullable=True)  # NULL = "and above", no upper bound
    markup_percent = db.Column(db.Numeric(6, 2), nullable=False)  # e.g. 100.00 for 100%

    def applies_to(self, cost):
        if cost is None:
            return False
        if cost < self.min_cost:
            return False
        if self.max_cost is not None and cost > self.max_cost:
            return False
        return True

class InvoicePaymentOption(db.Model):
    """A dealer-configurable payment button / QR code / note that renders on
    every invoice (on screen, in print, and in the emailed copy)."""
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)

    sort_order = db.Column(db.Integer, nullable=False, default=0)
    kind = db.Column(db.String(10), nullable=False)  # 'link', 'qr', 'text'
    label = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(500))          # 'link' target; also the source for a generated 'qr'
    image_url = db.Column(db.String(255))    # 'qr' image (generated or uploaded), e.g. /static/uploads/...
    body_text = db.Column(db.Text)           # 'text' body
    # Show even on a Paid invoice (e.g. a "leave a review" link).
    always_show = db.Column(db.Boolean, nullable=False, default=False, server_default=db.false())
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.Index('ix_invoice_payment_option_org', 'organization_id'),
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


class Customer(db.Model):
    """An end customer of the dealer (equipment owner / invoice bill-to), distinct from Dealer/Contact (sub-dealer network)."""
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)

    first_name = db.Column(db.String(80))
    last_name = db.Column(db.String(80), nullable=False, server_default='')
    company = db.Column(db.String(150))
    address = db.Column(db.String(255))
    phone = db.Column(db.String(50))
    email = db.Column(db.String(120))
    tax_exempt = db.Column(db.Boolean, default=False)
    is_commercial = db.Column(db.Boolean, default=False, nullable=False, server_default=db.false())
    # Pre-fills the checkout discount when this customer is picked; still editable per-sale.
    default_discount_percent = db.Column(db.Numeric(5, 2), nullable=True)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    units = db.relationship('Unit', backref='customer', lazy=True)
    invoices = db.relationship('Invoice', backref='customer', lazy=True)

    @hybrid_property
    def name(self):
        """Full name, composed from first + last. Kept so existing callers/templates keep working."""
        return " ".join(p for p in [self.first_name, self.last_name] if p).strip()

    @name.expression
    def name(cls):
        return func.trim(func.concat(func.coalesce(cls.first_name, ''), ' ', func.coalesce(cls.last_name, '')))


class Vendor(db.Model):
    """A parts/whole-goods supplier the dealer orders from."""
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)

    name = db.Column(db.String(150), nullable=False)
    account_number = db.Column(db.String(100))  # dealer's account # with this vendor
    contact_name = db.Column(db.String(100))
    phone = db.Column(db.String(50))
    email = db.Column(db.String(120))
    address = db.Column(db.String(255))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    parts = db.relationship('PartInventory', backref='vendor', lazy=True)
    purchase_orders = db.relationship('PurchaseOrder', backref='vendor', lazy=True)
    manufacturers = db.relationship('VendorManufacturer', backref='vendor', lazy=True,
                                    cascade="all, delete-orphan")


class VendorManufacturer(db.Model):
    """Which manufacturers a vendor supplies. Used to pick the vendor to
    special-order a part from (part.manufacturer -> primary vendor)."""
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendor.id'), nullable=False)
    manufacturer = db.Column(db.String(100), nullable=False)
    # When a manufacturer is carried by more than one vendor, the primary one
    # is used for automatic special orders.
    is_primary = db.Column(db.Boolean, default=False, nullable=False, server_default=db.false())

    __table_args__ = (
        UniqueConstraint('vendor_id', 'manufacturer', name='_vendor_mfg_uc'),
        db.Index('ix_vendor_mfg_org_mfg', 'organization_id', 'manufacturer'),
    )


class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)

    invoice_number = db.Column(db.Integer, nullable=False)  # sequential per org, assigned at creation
    invoice_type = db.Column(db.String(20), nullable=False)  # parts, whole_good, service
    service_ticket_id = db.Column(db.Integer, db.ForeignKey('service_ticket.id'), nullable=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True)

    # Snapshot bill-to fields, so an invoice stays accurate even if the
    # Customer record (or Unit owner info it was copied from) changes later.
    bill_to_name = db.Column(db.String(150))
    bill_to_company = db.Column(db.String(150))
    bill_to_address = db.Column(db.String(255))
    bill_to_phone = db.Column(db.String(50))
    bill_to_email = db.Column(db.String(120))

    status = db.Column(db.String(20), default='draft')  # draft, finalized, paid, partial, void

    subtotal = db.Column(db.Numeric(10, 2), default=0)
    # Applied to the subtotal before tax - e.g. a commercial-account rate or a one-off deal at checkout.
    discount_percent = db.Column(db.Numeric(5, 2), nullable=True)
    discount_amount = db.Column(db.Numeric(10, 2), nullable=True, default=0)
    tax_rate = db.Column(db.Numeric(5, 2), default=0)  # percent, e.g. 7.25
    tax_amount = db.Column(db.Numeric(10, 2), default=0)
    total = db.Column(db.Numeric(10, 2), default=0)

    payment_method = db.Column(db.String(20), nullable=True)  # cc, check, cash, other
    payment_reference = db.Column(db.String(100), nullable=True)  # check #, last 4, etc.
    paid_amount = db.Column(db.Numeric(10, 2), default=0)
    paid_at = db.Column(db.DateTime, nullable=True)

    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    line_items = db.relationship('InvoiceLineItem', backref='invoice', lazy=True, cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('organization_id', 'invoice_number', name='_invoice_number_org_uc'),
    )


class InvoiceLineItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=False)

    line_type = db.Column(db.String(20), nullable=False)  # part, labor, whole_good, misc
    description = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Numeric(10, 2), default=1)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    line_total = db.Column(db.Numeric(10, 2), nullable=False)

    part_inventory_id = db.Column(db.Integer, db.ForeignKey('part_inventory.id'), nullable=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('unit.id'), nullable=True)
    # Set when this part line was short on stock and got special-ordered.
    po_line_item_id = db.Column(db.Integer, db.ForeignKey('purchase_order_line_item.id'), nullable=True)

    @property
    def on_order(self):
        li = self.po_line_item
        return bool(li and li.quantity_received < li.quantity_ordered)


class PurchaseOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendor.id'), nullable=False)

    po_number = db.Column(db.Integer, nullable=False)  # sequential per org
    status = db.Column(db.String(20), default='draft')  # draft, ordered, partially_received, received, closed
    # True for the rolling draft PO that automatic special orders accumulate onto,
    # until staff review it and Mark Ordered (which starts a fresh one).
    is_auto_draft = db.Column(db.Boolean, default=False, nullable=False, server_default=db.false())
    order_date = db.Column(db.Date, nullable=True)
    expected_date = db.Column(db.Date, nullable=True)
    shipping_cost = db.Column(db.Numeric(10, 2), nullable=True, default=0)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    line_items = db.relationship('PurchaseOrderLineItem', backref='purchase_order', lazy=True, cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('organization_id', 'po_number', name='_po_number_org_uc'),
    )


class PurchaseOrderLineItem(db.Model):
    """
    line_type='part': received quantity increments PartInventory.stock_on_hand.
    line_type='whole_good': represents ONE physical unit (quantity_ordered is
    normally 1 - each serialized unit gets its own line); receiving it prompts
    for a serial number and creates a Unit record, linked via unit_id.
    """
    id = db.Column(db.Integer, primary_key=True)
    purchase_order_id = db.Column(db.Integer, db.ForeignKey('purchase_order.id'), nullable=False)

    line_type = db.Column(db.String(20), nullable=False, default='part')  # part, whole_good
    part_inventory_id = db.Column(db.Integer, db.ForeignKey('part_inventory.id'), nullable=True)

    # For 'part' lines ordering something not yet in PartInventory, or as a
    # readable snapshot regardless; for 'whole_good' lines, describes the unit.
    part_number = db.Column(db.String(100), nullable=True)
    manufacturer = db.Column(db.String(100), nullable=True)
    description = db.Column(db.String(255), nullable=True)

    quantity_ordered = db.Column(db.Integer, nullable=False, default=1)
    quantity_received = db.Column(db.Integer, nullable=False, default=0)
    unit_cost = db.Column(db.Numeric(10, 2), nullable=True)

    unit_id = db.Column(db.Integer, db.ForeignKey('unit.id'), nullable=True)  # set once a whole_good line is received

    # If this line was auto-generated to special-order a part for a job, which job.
    service_ticket_id = db.Column(db.Integer, db.ForeignKey('service_ticket.id'), nullable=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=True)

    service_ticket = db.relationship('ServiceTicket', backref='po_line_items')
    invoice = db.relationship('Invoice', backref='po_line_items')
    invoice_lines = db.relationship('InvoiceLineItem', backref='po_line_item', lazy=True)


class ServiceTicket(db.Model):
    """
    A dealership's own repair/service job - distinct from Case, which is a
    separate distributor-side case/claim tracking system unrelated to this.
    """
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)

    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('unit.id'), nullable=True)
    technician_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    status = db.Column(db.String(30), nullable=False, default='Received')
    # Received, In Progress, Waiting on Parts, Ready for Pickup, Closed

    reported_issue = db.Column(db.Text)

    intake_date = db.Column(db.DateTime, default=datetime.utcnow)
    closed_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    customer = db.relationship('Customer', backref='service_tickets')
    unit = db.relationship('Unit', backref='service_tickets')
    technician = db.relationship('User', backref='assigned_service_tickets')
    parts_used = db.relationship('ServiceTicketPart', backref='service_ticket', lazy=True, cascade="all, delete-orphan")
    labor_entries = db.relationship('ServiceTicketLabor', backref='service_ticket', lazy=True, cascade="all, delete-orphan")
    notes = db.relationship('ServiceTicketNote', backref='service_ticket', lazy=True,
                            order_by='ServiceTicketNote.created_at.desc()', cascade="all, delete-orphan")
    invoices = db.relationship('Invoice', backref='service_ticket')

    @property
    def total_parts_cost(self):
        return sum((p.quantity * p.cost_at_time_of_use for p in self.parts_used), Decimal('0.00'))

    @property
    def total_labor_cost(self):
        return sum((l.hours_spent * l.rate_at_time_of_log for l in self.labor_entries), Decimal('0.00'))

    @property
    def total_cost(self):
        return self.total_parts_cost + self.total_labor_cost


class ServiceTicketPart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)

    service_ticket_id = db.Column(db.Integer, db.ForeignKey('service_ticket.id'), nullable=False)
    part_number = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    cost_at_time_of_use = db.Column(db.Numeric(10, 2), nullable=False)
    description_at_time_of_use = db.Column(db.Text)
    invoiced = db.Column(db.Boolean, default=False, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    part_inventory_id = db.Column(db.Integer, db.ForeignKey('part_inventory.id'), nullable=True)
    # Set when this part was short on stock and got special-ordered.
    po_line_item_id = db.Column(db.Integer, db.ForeignKey('purchase_order_line_item.id'), nullable=True)

    part = db.relationship('PartInventory')
    po_line_item = db.relationship('PurchaseOrderLineItem', backref='service_ticket_parts')

    @property
    def on_order(self):
        li = self.po_line_item
        return bool(li and li.quantity_received < li.quantity_ordered)


class ServiceTicketLabor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)

    service_ticket_id = db.Column(db.Integer, db.ForeignKey('service_ticket.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    hours_spent = db.Column(db.Numeric(10, 2), nullable=False)
    rate_at_time_of_log = db.Column(db.Numeric(10, 2), nullable=False)
    description = db.Column(db.Text)
    invoiced = db.Column(db.Boolean, default=False, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class ServiceTicketNote(db.Model):
    """A timestamped, append-only entry in a service ticket's work log."""
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    service_ticket_id = db.Column(db.Integer, db.ForeignKey('service_ticket.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    author = db.relationship('User')

    __table_args__ = (
        db.Index('ix_service_ticket_note_ticket', 'service_ticket_id'),
    )
