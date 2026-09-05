import os
from flask import render_template, request, flash, redirect, url_for, g, session, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from app.core.extensions import db
from app.core.models import Organization, User
from . import super_admin_bp
from .forms import CreateTenantForm

@super_admin_bp.route('/tenants/add', methods=['GET', 'POST'])
@login_required
def add_tenant():
    # Security: Ensure only Super Admin (Org 1) can do this
    if g.current_org_id != 1 and not session.get('impersonation_origin_org'):
         flash("Unauthorized. Master access required.", "danger")
         return redirect(url_for('marketing.dashboard'))
    
    form = CreateTenantForm()
    
    if form.validate_on_submit():
        import secrets
        import string
        
        # 0. Handle Admin Password (Auto-gen if empty)
        raw_password = form.admin_password.data
        was_auto_gen = False
        if not raw_password:
            alphabet = string.ascii_letters + string.digits
            raw_password = ''.join(secrets.choice(alphabet) for _ in range(12))
            was_auto_gen = True
            
        # 1. Create Organization
        from datetime import datetime, timedelta

        new_org = Organization(
            name=form.org_name.data,
            slug=form.slug.data.lower(), # Enforce lowercase for subdomains
            custom_domain=form.custom_domain.data.lower() if form.custom_domain.data else None,
            settings={},
            modules={'ari': False, 'pos': 'none'},
            theme_config={'primaryColor': '#2563EB', 'logo_url': None}, # Default Blue

            # Auto-generate keys
            pos_bridge_key=secrets.token_hex(32),
            pos_provider='none',

            # Manually-created dealers also start on a free trial, same as
            # public self-service signups; convert via Site Manager's "Start Plan".
            subscription_status='trial',
            trial_ends_at=datetime.utcnow() + timedelta(days=10)
        )
        db.session.add(new_org)
        db.session.flush() # Get ID
        
        # 2. Create Admin User for that Org
        new_user = User(
            username=form.admin_username.data,
            email=form.dealer_email.data or None,
            password=generate_password_hash(raw_password),
            organization_id=new_org.id,
            password_reset_required=True # ALWAYS force change on first login for new sites
            # role='admin' # If/When we have role field
        )
        db.session.add(new_user)
        db.session.commit()

        # 3. Send Dealer Welcome Email (only if an email was provided)
        if form.dealer_email.data:
            try:
                from app.core.email import send_welcome_email
                send_welcome_email(
                    dealer_name=new_org.name,
                    dealer_email=form.dealer_email.data,
                    username=new_user.username,
                    dealer_slug=new_org.slug,
                    temp_password=raw_password,
                    custom_domain=new_org.custom_domain
                )
            except Exception as e:
                print(f"Warning: Failed to send welcome email: {e}")

        # 4. Send Admin Notification Email
        try:
            from app.core.email import send_dealer_admin_notification
            send_dealer_admin_notification(
                dealer_name=new_org.name,
                dealer_slug=new_org.slug,
                custom_domain=new_org.custom_domain
            )
        except Exception as e:
            print(f"Warning: Failed to send admin notification: {e}")

        msg = f"Site '{new_org.name}' created successfully!"
        if was_auto_gen:
            msg += f" TEMP CREDENTIALS -> User: {new_user.username} | Pass: {raw_password}"

        flash(msg, "success")
        return redirect(url_for('super_admin.add_tenant'))
        
    return render_template('super_admin/add.html', form=form)

@super_admin_bp.route('/tenants/<int:org_id>/start-plan', methods=['GET', 'POST'])
@login_required
def start_plan(org_id):
    # Security: Ensure only Super Admin (Org 1) can do this
    if g.current_org_id != 1 and not session.get('impersonation_origin_org'):
        flash("Unauthorized. Master access required.", "danger")
        return redirect(url_for('marketing.dashboard'))

    org = Organization.query.get_or_404(org_id)
    admin_user = User.query.filter_by(organization_id=org.id, role='admin').first()

    if request.method == 'POST':
        from app.core.billing_service import activate_subscription, ActivationError
        card_nonce = request.form.get('card_nonce')
        try:
            activate_subscription(
                org,
                card_nonce=card_nonce,
                contact_email=(admin_user.email if admin_user else None) or 'billing@bentcrankshaft.com',
                contact_name=org.name
            )
            flash(f"'{org.name}' is now on an active paid plan.", "success")
        except ActivationError as e:
            flash(str(e), "danger")
        return redirect(url_for('marketing.dashboard'))

    return render_template(
        'super_admin/start_plan.html',
        org=org,
        SQUARE_ENVIRONMENT=os.environ.get('SQUARE_ENVIRONMENT', 'sandbox'),
        SQUARE_APP_ID=os.environ.get('SQUARE_APP_ID'),
        SQUARE_LOCATION_ID=os.environ.get('SQUARE_LOCATION_ID'),
        start_plan_action_url=url_for('super_admin.start_plan', org_id=org.id)
    )

@super_admin_bp.route('/tenants', methods=['GET'])
@login_required
def list_tenants():
    # Deprecated: Redirect content to SaaS Dashboard
    return redirect(url_for('marketing.dashboard'))

@super_admin_bp.route('/tenants/<int:org_id>/impersonate')
@login_required
def impersonate(org_id):
    # Security: Ensure only Super Admin (Org 1) can do this
    if g.current_org_id != 1 and not session.get('impersonation_origin_org'):
         flash("Unauthorized.", "danger")
         return redirect(url_for('main.index'))

    target_org = Organization.query.get_or_404(org_id)
    
    # Store original org if this is the first hop
    if 'impersonation_origin_org' not in session:
        session['impersonation_origin_org'] = g.current_org_id
        
    # Switch Context
    session['organization_id'] = target_org.id
    
    flash(f"Now viewing as {target_org.name}", "warning")
    return redirect(url_for('marketing.dashboard'))

@super_admin_bp.route('/impersonate/exit')
@login_required
def exit_impersonation():
    origin_id = session.get('impersonation_origin_org')
    if origin_id:
        session['organization_id'] = origin_id
        session.pop('impersonation_origin_org', None)
        flash("Restored original admin context.", "info")
    else:
        flash("No active impersonation session.", "secondary")
        
    return redirect(url_for('marketing.dashboard'))

@super_admin_bp.route('/tenants/<int:org_id>/toggle-active', methods=['POST'])
@login_required
def toggle_active(org_id):
    # Security: Ensure only Super Admin (Org 1) can do this
    if g.current_org_id != 1 and not session.get('impersonation_origin_org'):
         flash("Unauthorized.", "danger")
         return redirect(url_for('main.index'))

    # Prevent deactivating Org 1
    if org_id == 1:
        flash("Cannot deactivate master organization.", "danger")
        return redirect(url_for('marketing.dashboard'))

    org = Organization.query.get_or_404(org_id)
    org.is_active = not org.is_active
    db.session.commit()
    
    status_msg = "activated" if org.is_active else "deactivated"
    flash(f"Organization '{org.name}' has been {status_msg}.", "success")
    
    return redirect(url_for('marketing.dashboard'))

@super_admin_bp.route('/tenants/<int:org_id>/delete', methods=['POST'])
@login_required
def delete_tenant(org_id):
    # Security: Ensure only Super Admin (Org 1) can do this
    if g.current_org_id != 1 and not session.get('impersonation_origin_org'):
         flash("Unauthorized.", "danger")
         return redirect(url_for('main.index'))

    # Prevent deleting Org 1
    if org_id == 1:
        flash("Cannot delete master organization.", "danger")
        return redirect(url_for('marketing.dashboard'))

    org = Organization.query.get_or_404(org_id)
    
    # Safety: Only allow deletion if organization is already inactive
    if org.is_active:
        flash(f"Cannot delete active organization. Please deactivate '{org.name}' first.", "warning")
        return redirect(url_for('marketing.dashboard'))
    
    org_name = org.name
    
    # Delete organization (cascade will handle related records via SQLAlchemy relationships)
    db.session.delete(org)
    db.session.commit()
    
    flash(f"Organization '{org_name}' has been permanently deleted.", "success")
    return redirect(url_for('marketing.dashboard'))

@super_admin_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@login_required
def reset_user_password(user_id):
    # Security: Ensure only Super Admin (Org 1) can do this
    if g.current_org_id != 1 and not session.get('impersonation_origin_org'):
         flash("Unauthorized.", "danger")
         return redirect(url_for('main.index'))

    user = User.query.get_or_404(user_id)
    
    # Generate temporary password
    import secrets
    import string
    alphabet = string.ascii_letters + string.digits
    temp_pass = ''.join(secrets.choice(alphabet) for _ in range(12))
    
    user.password = generate_password_hash(temp_pass)
    user.password_reset_required = True
    db.session.commit()
    
    flash(f"Password reset for {user.username}. NEW TEMP PASS: {temp_pass}", "success")
    return redirect(url_for('marketing.dashboard'))

@super_admin_bp.route('/tenants/<int:org_id>/update-modules', methods=['POST'])
@login_required
def update_modules(org_id):
    # Security: Ensure only Super Admin (Org 1) can do this
    if g.current_org_id != 1 and not session.get('impersonation_origin_org'):
         return jsonify({"error": "Unauthorized"}), 403

    org = Organization.query.get_or_404(org_id)
    
    # Update modules based on form checkboxes
    # Use a copy to avoid mutation detection issues and reference sharing
    current_modules = dict(org.modules or {})
    
    # Track changes for logging
    changes = []
    
    # We expect these switches to be in the form if they are present in the row
    # Checkbox logic: Presence in form = True, Absence = False
    for key in ['pos_sync', 'facebook', 'ari']:
        new_val = key in request.form
        if current_modules.get(key) != new_val:
            changes.append(f"{key}: {current_modules.get(key)} -> {new_val}")
            current_modules[key] = new_val
    
    current_app.logger.info(f"Form data for Org {org_id}: {request.form}")

    if changes:
        current_app.logger.info(f"Updating modules for Org {org_id}: {', '.join(changes)}")
        org.modules = current_modules
        
        # Force SQLAlchemy to see the change in the JSON field
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(org, "modules")
        
        db.session.commit()
        flash(f"Modules updated for {org.name}.", "success")
    else:
        # If no changes were detected, it might be because the form was submitted 
        # but nothing was toggled. We still flash to show we processed it.
        flash(f"Checked modules for {org.name} - no changes needed.", "info")
    
    return redirect(url_for('marketing.dashboard'))

@super_admin_bp.route('/tenants/<int:org_id>/update-modules-ajax', methods=['POST'])
@login_required
def update_modules_ajax(org_id):
    # Security: Ensure only Super Admin (Org 1) can do this
    if g.current_org_id != 1 and not session.get('impersonation_origin_org'):
         return jsonify({"success": False, "error": "Unauthorized"}), 403

    org = Organization.query.get_or_404(org_id)
    data = request.get_json()
    
    module_key = data.get('module')
    is_enabled = data.get('enabled')
    
    if not module_key:
        return jsonify({"success": False, "error": "Module key missing"}), 400
        
    modules = org.modules
    if not isinstance(modules, dict):
        modules = {}
        
    modules[module_key] = is_enabled
    org.modules = modules
    
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(org, "modules")
    
    db.session.commit()
    
    return jsonify({"success": True})

@super_admin_bp.route('/tenants/<int:org_id>/update-price', methods=['POST'])
@login_required
def update_price(org_id):
    # Security: Ensure only Super Admin (Org 1) can do this
    if g.current_org_id != 1 and not session.get('impersonation_origin_org'):
        flash("Unauthorized.", "danger")
        return redirect(url_for('main.index'))

    org = Organization.query.get_or_404(org_id)

    try:
        new_price_dollars = float(request.form.get('monthly_price_dollars', ''))
        new_price_cents = round(new_price_dollars * 100)
        if new_price_cents < 0:
            raise ValueError()
    except (TypeError, ValueError):
        flash("Invalid price.", "danger")
        return redirect(url_for('marketing.dashboard'))

    org.monthly_price = new_price_cents

    if org.subscription_status == 'active' and org.subscription_id:
        from app.integrations.square_payments import SquarePaymentService
        square = SquarePaymentService()
        if not square.update_subscription_price(org.subscription_id, new_price_cents):
            flash(f"Price saved locally, but updating the live Square subscription for '{org.name}' failed. Contact support.", "warning")
            db.session.commit()
            return redirect(url_for('marketing.dashboard'))

    db.session.commit()
    flash(f"'{org.name}' monthly price set to ${new_price_dollars:.2f}.", "success")
    return redirect(url_for('marketing.dashboard'))

@super_admin_bp.route('/tenants/bulk-raise-price', methods=['POST'])
@login_required
def bulk_raise_price():
    # Security: Ensure only Super Admin (Org 1) can do this
    if g.current_org_id != 1 and not session.get('impersonation_origin_org'):
        flash("Unauthorized.", "danger")
        return redirect(url_for('main.index'))

    try:
        raise_by_dollars = float(request.form.get('raise_by_dollars', ''))
        raise_by_cents = round(raise_by_dollars * 100)
        if raise_by_cents <= 0:
            raise ValueError()
    except (TypeError, ValueError):
        flash("Invalid raise amount.", "danger")
        return redirect(url_for('marketing.dashboard'))

    include_org_ids = {int(v) for v in request.form.getlist('include_org_id')}
    orgs = Organization.query.filter(
        Organization.id != 1,
        Organization.subscription_status == 'active',
        Organization.id.in_(include_org_ids)
    ).all() if include_org_ids else []

    if not orgs:
        flash("No active dealers were selected to raise.", "warning")
        return redirect(url_for('marketing.dashboard'))

    from app.integrations.square_payments import SquarePaymentService
    square = SquarePaymentService()
    updated, failed = [], []

    for org in orgs:
        new_price = (org.monthly_price or 4900) + raise_by_cents
        if org.subscription_id and not square.update_subscription_price(org.subscription_id, new_price):
            failed.append(org.name)
            continue
        org.monthly_price = new_price
        updated.append(org.name)

    db.session.commit()

    if updated:
        flash(f"Raised price by ${raise_by_dollars:.2f}/mo for: {', '.join(updated)}.", "success")
    if failed:
        flash(f"Failed to update live Square subscription for: {', '.join(failed)} (local price unchanged for these).", "danger")
    return redirect(url_for('marketing.dashboard'))

@super_admin_bp.route('/tenants/<int:org_id>/toggle-exempt', methods=['POST'])
@login_required
def toggle_exempt(org_id):
    # Security: Ensure only Super Admin (Org 1) can do this
    if g.current_org_id != 1 and not session.get('impersonation_origin_org'):
        flash("Unauthorized.", "danger")
        return redirect(url_for('main.index'))

    if org_id == 1:
        flash("Not applicable to the master organization.", "danger")
        return redirect(url_for('marketing.dashboard'))

    org = Organization.query.get_or_404(org_id)

    if org.subscription_status == 'exempt':
        org.subscription_status = 'inactive'
        flash(f"'{org.name}' is no longer exempt from billing.", "success")
    elif org.subscription_status == 'active':
        flash(f"'{org.name}' already has an active paid plan; remove/cancel that first.", "danger")
        return redirect(url_for('marketing.dashboard'))
    else:
        org.subscription_status = 'exempt'
        flash(f"'{org.name}' is now exempt from billing. Use 'Start Plan' any time to begin charging them.", "success")

    db.session.commit()
    return redirect(url_for('marketing.dashboard'))
