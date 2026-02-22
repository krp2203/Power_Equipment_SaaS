import json
import re
from flask import render_template, request, flash, redirect, url_for, g, abort, jsonify
from flask_login import login_required, current_user
from app.core.extensions import db
from app.core.models import Dealer, Contact, DealerNote, User, Notification, Organization
from app.core.constants import ALL_MANUFACTURERS
from app.core.utils import render_note_html
from . import dealers_bp

# Admin requirement decorator placeholder - adapt as needed for RBAC
def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Allow if superuser or if user role is admin (implement role logic later)
        # For now, just pass through or check a flag if needed. 
        # Assuming all logged in users can manage for now based on legacy app.py usually having this.
        # Legacy had @admin_required. We can check g.current_user.is_admin if that field exists.
        # But User model doesn't have is_admin yet, only username/password/org. 
        # We will iterate on RBAC later.
        return f(*args, **kwargs)
    return decorated_function

@dealers_bp.route('/dealers')
@login_required
def index():
    """List all dealers."""
    search_term = request.args.get('search', '').strip()
    query = Dealer.query
    if search_term:
        query = query.filter(Dealer.name.ilike(f'%{search_term}%'))
    
    dealers = query.order_by(Dealer.name.asc()).all()
    return render_template('dealers/index.html', dealers=dealers, search_term=search_term)

@dealers_bp.route('/dealers/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        # Create Dealer
        new_dealer = Dealer(
            name=request.form['dealer_name'],
            dealer_dba=request.form.get('dealer_dba'),
            dealer_code=request.form.get('dealer_code'),
            address=request.form.get('address'),
            labor_rate=request.form.get('labor_rate'),
            notes=request.form.get('notes'),
            manufacturers=','.join(request.form.getlist('manufacturers')),
            organization_id=g.current_org_id # Explicitly set Org ID
        )
        db.session.add(new_dealer)
        db.session.flush()

        # Add Contacts
        contact_names = request.form.getlist('contact_names')
        contact_roles = request.form.getlist('contact_roles')
        contact_emails = request.form.getlist('contact_emails')
        contact_phones = request.form.getlist('contact_phones')

        for i in range(len(contact_names)):
            if contact_names[i]:
                new_contact = Contact(
                    dealer_id=new_dealer.id,
                    name=contact_names[i],
                    role=contact_roles[i] if i < len(contact_roles) else None,
                    email=contact_emails[i] if i < len(contact_emails) else None,
                    phone=contact_phones[i] if i < len(contact_phones) else None,
                    organization_id=g.current_org_id
                )
                db.session.add(new_contact)

        db.session.commit()
        flash(f'Dealer "{new_dealer.name}" created successfully!', 'success')
        return redirect(url_for('dealers.index'))
    
    return render_template('dealers/add.html', all_manufacturers=ALL_MANUFACTURERS)

@dealers_bp.route('/dealers/<int:dealer_id>')
@login_required
def view(dealer_id):
    dealer = Dealer.query.get_or_404(dealer_id)
    # The multitenancy listener handles filtering cases/notes by org implicitly via relationships
    # provided the relationships are established correctly or queries are direct.
    # Dealer.cases is a relationship.
    
    # Legacy fetched all users for @mentions
    users = User.query.order_by(User.username).all()
    mention_data = json.dumps([
        {'key': f"{u.username} ({u.username})", 'value': u.username} for u in users
    ])

    return render_template('dealers/detail.html', 
                           dealer=dealer, 
                           users=users, 
                           mention_data=mention_data,
                           render_note_html=render_note_html) # Pass helper to template

@dealers_bp.route('/dealers/<int:dealer_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(dealer_id):
    dealer = Dealer.query.get_or_404(dealer_id)
    if request.method == 'POST':
        dealer.name = request.form['dealer_name']
        dealer.dealer_dba = request.form.get('dealer_dba')
        dealer.dealer_code = request.form.get('dealer_code')
        dealer.address = request.form.get('address')
        dealer.labor_rate = request.form.get('labor_rate')
        dealer.manufacturers = ','.join(request.form.getlist('manufacturers'))
        dealer.notes = request.form.get('notes')
        db.session.commit()
        flash(f'Dealer "{dealer.name}" updated.', 'success')
        return redirect(url_for('dealers.view', dealer_id=dealer.id))
    
    # Pre-process manufacturers for checkboxes
    current_manufacturers = dealer.manufacturers.split(',') if dealer.manufacturers else []
    return render_template('dealers/edit.html', dealer=dealer, 
                           all_manufacturers=ALL_MANUFACTURERS,
                           current_manufacturers=current_manufacturers)

@dealers_bp.route('/dealers/<int:dealer_id>/notes/add', methods=['POST'])
@login_required
def add_note(dealer_id):
    dealer = Dealer.query.get_or_404(dealer_id)
    note_text = request.form.get('note_text')
    parent_note_id = request.form.get('parent_note_id')
    
    if note_text:
        new_note = DealerNote(
            dealer_id=dealer.id,
            text=note_text,
            user=current_user.username,
            parent_id=int(parent_note_id) if parent_note_id else None,
            organization_id=g.current_org_id,
            # timestamp handles itself via default
        )
        db.session.add(new_note)
        db.session.commit()
        flash('Note added.', 'success')
    else:
        flash('Note cannot be empty.', 'warning')
        
    return redirect(url_for('dealers.view', dealer_id=dealer_id, _anchor='notes-section'))
