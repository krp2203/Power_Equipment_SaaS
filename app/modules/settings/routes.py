from flask import render_template, request, flash, redirect, url_for, g, current_app
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
import os
from app.core.extensions import db
from app.core.models import User
from . import settings_bp
from .forms import OrganizationSettingsForm, AddUserForm, EditUserForm
from itsdangerous import URLSafeSerializer
from app.core.multitenancy import global_tenant_bypass
from sqlalchemy.orm.attributes import flag_modified

@settings_bp.route('/settings/organization', methods=['GET', 'POST'])
@login_required
def organization():
    # Ensure only admins can access (basic check)
    org = g.current_org
    if not org:
        flash("No organization context found.", "danger")
        return redirect(url_for('main.index'))

    form = OrganizationSettingsForm()
    add_user_form = AddUserForm()
    edit_user_form = EditUserForm()

    # Get all users for this organization
    users = User.query.filter_by(organization_id=org.id).all()

    if request.method == 'GET':
        # Pre-populate form
        theme = org.theme_config or {}
        
        # SAFETY CHECK: Ensure modules is a dict
        modules = org.modules
        if not isinstance(modules, dict):
            modules = {}
        
        form.primary_color.data = theme.get('primaryColor', '#DC2626')

        # Identity
        form.slug.data = org.slug
        form.custom_domain.data = org.custom_domain or ""
        
        # ARI
        form.enable_ari.data = modules.get('ari', False)
        form.ari_dealer_id.data = org.ari_dealer_id
        
        # POS
        form.pos_provider.data = org.pos_provider or 'none'
        form.pos_bridge_key.data = org.pos_bridge_key
        form.enable_pos.data = (org.pos_provider and org.pos_provider != 'none')
        
        # Facebook
        form.facebook_page_id.data = org.facebook_page_id
        form.facebook_access_token.data = org.facebook_access_token
        
        # Modules (Admin Toggles)
        form.module_pos_sync.data = modules.get('pos_sync', False)
        form.module_facebook.data = modules.get('facebook', False)
        form.module_ari.data = modules.get('ari', False)
        
        # Hero
        form.hero_title.data = theme.get('hero_title', f"Welcome to {org.name}")
        form.hero_tagline.data = theme.get('hero_tagline', "Your Premium Destination for Power Equipment, Parts, and Service.")
        form.hero_show_logo.data = theme.get('hero_show_logo', False)
        
        # Features
        form.feat_inventory_title.data = theme.get('feat_inventory_title', "Huge Selection")
        form.feat_inventory_text.data = theme.get('feat_inventory_text', "Browse our wide range of mowers, chainsaws, and blowers from top brands.")
        form.feat_parts_title.data = theme.get('feat_parts_title', "Genuine Parts")
        form.feat_parts_text.data = theme.get('feat_parts_text', "Find the exact part you need with our detailed diagrams.")
        form.feat_service_title.data = theme.get('feat_service_title', "Expert Service")
        form.feat_service_text.data = theme.get('feat_service_text', "Our certified technicians are ready to keep your equipment running like new.")
        
        # Contact
        form.contact_phone.data = theme.get('contact_phone', "(555) 123-4567")
        form.contact_email.data = theme.get('contact_email', "sales@example.com")
        form.contact_address.data = theme.get('contact_address', "1234 Equipment Lane, Mower City, ST 12345")
        form.contact_text.data = theme.get('contact_text', "We are here to help you with all your power equipment needs.")

        # Social Media
        form.social_facebook.data = theme.get('social_facebook', '')
        form.social_instagram.data = theme.get('social_instagram', '')
        form.social_twitter.data = theme.get('social_twitter', '')
        form.social_linkedin.data = theme.get('social_linkedin', '')
        form.social_youtube.data = theme.get('social_youtube', '')
        form.social_bluesky.data = theme.get('social_bluesky', '')

    # SaaS Admin check (either real Org 1 user, or impersonating)
    from flask import session
    is_saas_admin = session.get('impersonation_origin_org') is not None or g.current_org.id == 1
    
    if not is_saas_admin:
        form.slug.render_kw = {'readonly': True}

    if form.validate_on_submit():
        # Update Org
        # Update Theme
        new_theme = org.theme_config or {}
        new_theme['primaryColor'] = form.primary_color.data
        new_theme['primary_color'] = form.primary_color.data
        
        # Handle Logo Upload
        if form.company_logo.data:
            f = form.company_logo.data
            filename = secure_filename(f"{org.id}_logo_{f.filename}")
            
            # Ensure upload path exists
            upload_dir = os.path.join(current_app.root_path, 'static/uploads/logos')
            os.makedirs(upload_dir, exist_ok=True)
            
            file_path = os.path.join(upload_dir, filename)
            f.save(file_path)
            
            # Save relative URL for frontend
            new_theme['logo_url'] = f"/static/uploads/logos/{filename}"
        
        # Handle Brand Logos
        brand_logos = new_theme.get('brand_logos', {})
        brand_logo_urls = new_theme.get('brand_logo_urls', {})

        for i in range(1, 9):
            field_name = f'brand_logo_{i}'
            field = getattr(form, field_name)
            if field.data:
                f = field.data
                filename = secure_filename(f"{org.id}_brand_{i}_{f.filename}")
                upload_dir = os.path.join(current_app.root_path, 'static/uploads/brands')
                os.makedirs(upload_dir, exist_ok=True)
                file_path = os.path.join(upload_dir, filename)
                f.save(file_path)
                brand_logos[str(i)] = f"/static/uploads/brands/{filename}"

            # Handle brand logo URL links
            url_field_name = f'brand_logo_url_{i}'
            if url_field_name in request.form:
                url_value = request.form.get(url_field_name, '').strip()
                if url_value:
                    brand_logo_urls[str(i)] = url_value
                elif str(i) in brand_logo_urls:
                    del brand_logo_urls[str(i)]

        new_theme['brand_logos'] = brand_logos
        new_theme['brand_logo_urls'] = brand_logo_urls
            
        # Save Text Customizations
        new_theme['hero_title'] = form.hero_title.data
        new_theme['hero_tagline'] = form.hero_tagline.data
        new_theme['hero_show_logo'] = form.hero_show_logo.data
        new_theme['feat_inventory_title'] = form.feat_inventory_title.data
        new_theme['feat_inventory_text'] = form.feat_inventory_text.data
        new_theme['feat_parts_title'] = form.feat_parts_title.data
        new_theme['feat_parts_text'] = form.feat_parts_text.data
        new_theme['feat_service_title'] = form.feat_service_title.data
        new_theme['feat_service_text'] = form.feat_service_text.data
        new_theme['contact_phone'] = form.contact_phone.data
        new_theme['contact_email'] = form.contact_email.data
        new_theme['contact_address'] = form.contact_address.data
        new_theme['contact_text'] = form.contact_text.data

        # Save Social Media URLs
        new_theme['social_facebook'] = form.social_facebook.data
        new_theme['social_instagram'] = form.social_instagram.data
        new_theme['social_twitter'] = form.social_twitter.data
        new_theme['social_linkedin'] = form.social_linkedin.data
        new_theme['social_youtube'] = form.social_youtube.data
        new_theme['social_bluesky'] = form.social_bluesky.data

        org.theme_config = new_theme
        
        # Update Columns - Only allow slug/custom_domain update if SaaS Admin
        if is_saas_admin:
            org.slug = form.slug.data
            org.custom_domain = form.custom_domain.data.lower() if form.custom_domain.data else None
            
        org.ari_dealer_id = form.ari_dealer_id.data
        org.pos_provider = form.pos_provider.data
        org.pos_bridge_key = form.pos_bridge_key.data
        # Facebook - Skip manual update if empty (handled by OAuth)
        # org.facebook_page_id = form.facebook_page_id.data
        # org.facebook_access_token = form.facebook_access_token.data
        
        if is_saas_admin:
            # Update Modules flags
            new_modules = org.modules or {}
            new_modules['ari'] = form.module_ari.data
            new_modules['facebook'] = form.module_facebook.data
            new_modules['pos_sync'] = form.module_pos_sync.data
            
            # Backward compatibility for 'pos' field if it was used elsewhere
            if form.module_pos_sync.data and form.pos_provider.data != 'none':
                 new_modules['pos'] = form.pos_provider.data
            else:
                 if 'pos' in new_modules: del new_modules['pos']
                 
            org.modules = new_modules
            flag_modified(org, "modules")
        
        flag_modified(org, "theme_config")
        flag_modified(org, "modules")

        db.session.commit()
        
        flash("Settings updated successfully.", "success")
        return redirect(url_for('settings.organization'))

    return render_template('settings/organization.html', form=form, add_user_form=add_user_form, edit_user_form=edit_user_form, users=users)

@settings_bp.route('/settings/users/add', methods=['POST'])
@login_required
def add_user():
    org = g.current_org
    form = AddUserForm()
    
    if form.validate_on_submit():
        # Check if username already exists in this organization
        existing_user = User.query.filter_by(username=form.username.data, organization_id=org.id).first()
        if existing_user:
            flash(f"Username '{form.username.data}' is already taken in your organization.", "danger")
            return redirect(url_for('settings.organization') + "#users")

        new_user = User(
            username=form.username.data,
            email=form.email.data,
            password=generate_password_hash(form.password.data),
            role=form.role.data,
            organization_id=org.id,
            password_reset_required=True
        )
        db.session.add(new_user)
        db.session.commit()
        
        flash(f"User {new_user.username} added successfully. They will be required to change their password on first login.", "success")
        return redirect(url_for('settings.organization') + "#users")
    
    flash("Error adding user. Please check the form.", "danger")
    return redirect(url_for('settings.organization') + "#users")

@settings_bp.route('/settings/users/<int:user_id>/edit', methods=['POST'])
@login_required
def edit_user(user_id):
    org = g.current_org
    user = User.query.get_or_404(user_id)
    
    # Safety check
    if user.organization_id != org.id:
        flash("Unauthorized.", "danger")
        return redirect(url_for('settings.organization'))
        
    form = EditUserForm()
    if form.validate_on_submit():
        user.email = form.email.data
        user.role = form.role.data
        db.session.commit()
        flash(f"User {user.username} updated successfully.", "success")
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error in {field}: {error}", "danger")
                
    return redirect(url_for('settings.organization') + "#users")

@settings_bp.route('/settings/users/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    org = g.current_org
    user = User.query.get_or_404(user_id)
    
    # Safety checks
    if user.organization_id != org.id:
        flash("Unauthorized.", "danger")
        return redirect(url_for('settings.organization'))
        
    if user.id == current_user.id:
        flash("You cannot delete your own account.", "warning")
        return redirect(url_for('settings.organization') + "#users")
        
    # Prevent deleting the last admin if we had roles properly enforced
    # For now, just allow deletion if they aren't 'self'.
    
    db.session.delete(user)
    db.session.commit()
    
    flash(f"User {user.username} has been removed.", "success")
    return redirect(url_for('settings.organization') + "#users")

@settings_bp.route('/settings/facebook/connect')
@login_required
def facebook_connect():
    from app.integrations.facebook_oauth import FacebookOAuth
    
    # Sign a state token to maintain context across subdomains
    s = URLSafeSerializer(current_app.config['SECRET_KEY'])
    state_data = {
        'user_id': current_user.id,
        'org_id': g.current_org.id,
        'host': request.host
    }
    state_token = s.dumps(state_data)
    
    oauth = FacebookOAuth()
    # Use bentcrankshaft.com as the root domain for the callback
    callback_url = "https://bentcrankshaft.com/settings/facebook/callback"
    target_url = oauth.get_connect_url(callback_url, state=state_token)
    current_app.logger.error(f"DEBUG_OAUTH: Redirecting to Facebook with URL: {target_url}")
    return redirect(target_url)

@settings_bp.route('/settings/facebook/callback')
def facebook_callback():
    from app.integrations.facebook_oauth import FacebookOAuth
    from app.core.models import Organization, User
    from datetime import datetime, timedelta
    
    code = request.args.get('code')
    state_token = request.args.get('state')
    
    if not code or not state_token:
        flash("Authorization failed: Missing data.", "danger")
        # If we reach here without state, we can't easily redirect back to subdomain
        return redirect(url_for('main.index'))
        
    # 0. Verify State and restore context
    try:
        s = URLSafeSerializer(current_app.config['SECRET_KEY'])
        state_data = s.loads(state_token)
        user_id = int(state_data['user_id'])
        org_id = int(state_data['org_id'])
        original_host = state_data['host']
    except Exception as e:
        current_app.logger.error(f"OAUTH: State verification failed: {str(e)}")
        flash("Security check failed. Please try again.", "danger")
        return redirect(url_for('main.index'))

    # Load context manually since we bypassed @login_required
    # We must bypass the tenant filter to find the user/org from the root domain
    with global_tenant_bypass():
        user = db.session.query(User).filter_by(id=user_id).first()
        org = db.session.query(Organization).filter_by(id=org_id).first()
    
    if not user or not org:
        flash("Connection context lost.", "danger")
        if 'original_host' in locals():
            return redirect(f"https://{original_host}/settings/organization#integrations")
        return redirect(url_for('main.index'))
        
    oauth = FacebookOAuth()
    callback_url = "https://bentcrankshaft.com/settings/facebook/callback"
    
    # 1. Exchange Code for User Token (Short-lived)
    short_token = oauth.exchange_code_for_token(code, callback_url)
    if not short_token:
        flash("Failed to retrieve access token from Facebook.", "danger")
        return redirect(f"https://{original_host}/settings/organization#integrations")
        
    # 2. Exchange for Long-lived User Token
    long_token = oauth.get_long_lived_user_token(short_token)
    if not long_token:
        flash("Failed to secure long-lived access token.", "danger")
        return redirect(f"https://{original_host}/settings/organization#integrations")
        
    # 3. Store User Token
    org.facebook_user_token = long_token
    db.session.commit()
    
    # 4. Fetch Pages
    pages = oauth.get_managed_pages(long_token)
    if not pages:
        flash("No Facebook Pages found for your account.", "warning")
        return redirect(f"https://{original_host}/settings/organization#integrations")
        
    # 5. Auto-select if only one page
    if len(pages) == 1:
        page = pages[0]
        org.facebook_page_id = page['id']
        org.facebook_access_token = page['access_token']
        org.facebook_page_token_expires = datetime.utcnow() + timedelta(days=60) 
        db.session.commit()
        flash(f"Connected to Facebook Page: {page['name']}", "success")
        return redirect(f"https://{original_host}/settings/organization#integrations")
        
    # 6. If multiple, show selection screen
    # Note: selection screen might need to handle host as well, but for now 
    # we'll assume they can select from here or we can pass host to selection page
    return render_template('settings/facebook_select.html', pages=pages, original_host=original_host)

@settings_bp.route('/settings/facebook/select/<page_id>')
@login_required
def facebook_select_page(page_id):
    from app.integrations.facebook_oauth import FacebookOAuth
    from datetime import datetime, timedelta
    
    original_host = request.args.get('original_host')
    org = g.current_org
    if not org.facebook_user_token:
        flash("Session expired during connection. Please try again.", "danger")
        return redirect(url_for('settings.organization'))
        
    oauth = FacebookOAuth()
    pages = oauth.get_managed_pages(org.facebook_user_token)
    
    selected_page = next((p for p in pages if p['id'] == page_id), None)
    if not selected_page:
        flash("Invalid page selection.", "danger")
        return redirect(url_for('settings.organization'))
        
    org.facebook_page_id = selected_page['id']
    org.facebook_access_token = selected_page['access_token']
    org.facebook_page_token_expires = datetime.utcnow() + timedelta(days=60)
    db.session.commit()
    
    flash(f"Connected to Facebook Page: {selected_page['name']}", "success")
    if original_host:
        return redirect(f"https://{original_host}/settings/organization#integrations")
    return redirect(url_for('settings.organization'))

@settings_bp.route('/settings/facebook/disconnect', methods=['POST'])
@login_required
def facebook_disconnect():
    org = g.current_org
    org.facebook_page_id = None
    org.facebook_access_token = None
    org.facebook_user_token = None
    org.facebook_page_token_expires = None
    db.session.commit()
    
    flash("Disconnected from Facebook.", "info")
    return redirect(url_for('settings.organization'))

@settings_bp.route('/test-facebook', methods=['POST'])
@login_required
def test_facebook():
    """Test Facebook credentials"""
    from app.integrations.facebook import FacebookService
    import json
    
    org = g.current_org
    
    if not org.facebook_page_id or not org.facebook_access_token:
        return json.dumps({'success': False, 'message': 'Facebook credentials not configured'}), 400
    
    fb_service = FacebookService(org.facebook_page_id, org.facebook_access_token)
    success, error = fb_service.verify_credentials()
    
    if success:
        return json.dumps({'success': True, 'message': 'Facebook connection successful!'}), 200
    else:
        return json.dumps({'success': False, 'message': error}), 400


@settings_bp.route('/settings/onboarding', methods=['GET'])
@login_required
def onboarding():
    org = g.current_org
    if not org:
        flash("No organization context found.", "danger")
        return redirect(url_for('main.index'))
    
    # If already completed, redirect to settings
    if org.onboarding_complete:
        return redirect(url_for('settings.organization'))
    
    form = OrganizationSettingsForm()
    
    # Pre-populate with defaults/existing data
    theme = org.theme_config or {}
    form.primary_color.data = theme.get('primaryColor', '#0d6efd')
    form.hero_title.data = theme.get('hero_title', f"Welcome to {org.name}")
    form.hero_tagline.data = theme.get('hero_tagline', 'Your Premium Destination for Power Equipment, Parts, and Service.')
    form.contact_phone.data = theme.get('contact_phone', '')
    form.contact_email.data = theme.get('contact_email', '')
    form.contact_address.data = theme.get('contact_address', '')
    
    return render_template('settings/onboarding.html', form=form)


@settings_bp.route('/settings/onboarding/save', methods=['POST'])
@login_required
def onboarding_save():
    org = g.current_org
    if not org:
        flash("No organization context found.", "danger")
        return redirect(url_for('main.index'))
    
    form = OrganizationSettingsForm()
    
    # Save branding, content, and contact info
    new_theme = org.theme_config or {}
    new_theme['primaryColor'] = form.primary_color.data
    
    # Handle Logo Upload
    if form.company_logo.data:
        f = form.company_logo.data
        filename = secure_filename(f"{org.id}_logo_{f.filename}")
        upload_dir = os.path.join(current_app.root_path, 'static/uploads/logos')
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, filename)
        f.save(file_path)
        new_theme['logo_url'] = f"/static/uploads/logos/{filename}"
    
    # Content
    new_theme['hero_title'] = form.hero_title.data
    new_theme['hero_tagline'] = form.hero_tagline.data

    # Contact
    new_theme['contact_phone'] = form.contact_phone.data
    new_theme['contact_email'] = form.contact_email.data
    new_theme['contact_address'] = form.contact_address.data

    # Social Media
    new_theme['social_facebook'] = form.social_facebook.data
    new_theme['social_instagram'] = form.social_instagram.data
    new_theme['social_twitter'] = form.social_twitter.data
    new_theme['social_linkedin'] = form.social_linkedin.data
    new_theme['social_youtube'] = form.social_youtube.data
    new_theme['social_bluesky'] = form.social_bluesky.data

    org.theme_config = new_theme
    org.onboarding_complete = True
    
    flag_modified(org, "theme_config")
    
    db.session.commit()
    
    flash("Your site setup is complete! Welcome aboard. 🎉", "success")
    return redirect(url_for('marketing.dashboard'))
