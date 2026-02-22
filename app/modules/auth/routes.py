from flask import render_template, redirect, url_for, flash, request, session, g
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from app.core.models import User, Organization
from app.core.extensions import db
from . import auth_bp
from .forms import ProfileForm, ChangePasswordForm, LoginForm
import sys

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        # Instead of auto-redirecting (which traps users in the wrong tenant context),
        # show them a choice: Continue or Logout.
        return render_template('auth/already_logged_in.html')
    
    form = LoginForm()
    
    if form.validate_on_submit():
        print("DEBUG: Login POST received")
        username = form.username.data.strip() if form.username.data else ""
        password = form.password.data
        print(f"DEBUG: Attempting to login user: '{username}'")
        
        # 1. Find User (Try exact match, then try lowercase fallback)
        users = User.query.filter_by(username=username).all()
        if not users and username:
             # Try lowercase match just in case
             users = User.query.filter_by(username=username.lower()).all()

        user_to_login = None
        
        for user in users:
            if user.password and check_password_hash(user.password, password):
                user_to_login = user
                break
            else:
                print(f"DEBUG: Password check failed for user ID {user.id} in Org {user.organization_id}")
        
        if user_to_login:
            print("DEBUG: User found and password verified.")
            # 2. Login User
            try:
                login_user(user_to_login)
                print("DEBUG: login_user successful")
            except Exception as e:
                print(f"ERROR in login_user: {e}")
                raise e
            
            # 3. Set Tenant Context
            session['organization_id'] = user_to_login.organization_id
            print(f"DEBUG: Session Org ID set to {user_to_login.organization_id}")
            
            # 4. Check for mandatory password reset
            if user_to_login.password_reset_required:
                flash('Welcome! Please set a permanent password for your new account.', 'warning')
                return redirect(url_for('auth.force_reset'))
            
            next_page = request.args.get('next')
            return redirect(next_page or url_for('marketing.dashboard'))
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
def logout():
    try:
        print("DEBUG: Logout Route Hit")
        print(f"DEBUG: Current User before logout: {current_user}")
        
        logout_user()
        
        # Explicitly clear all relevant session data
        session.clear() 
        
        print("DEBUG: Session cleared and user logged out.")
        
        response = redirect(url_for('auth.login'))
        
        # Force delete cookies for all possible domains
        response.delete_cookie('pes_session_v2', domain='.bentcrankshaft.com', path='/')
        response.delete_cookie('pes_session_v2', path='/')
        
        flash('You have been logged out.', 'info')
        return response
    except Exception as e:
        print(f"ERROR in logout: {e}")
        return str(e), 500

# Temporary route to verify auth works
@auth_bp.route('/')
@login_required
def index():
    return render_template('auth/dashboard_stub.html')

@auth_bp.route('/force-reset', methods=['GET', 'POST'])
@login_required
def force_reset():
    """Route for users who MUST change their password before proceeding."""
    if not current_user.password_reset_required:
        return redirect(url_for('marketing.dashboard'))
        
    form = ChangePasswordForm()
    # Profile update part not needed here, only password
    if form.validate_on_submit():
        if check_password_hash(current_user.password, form.current_password.data):
            current_user.password = generate_password_hash(form.new_password.data)
            current_user.password_reset_required = False
            db.session.commit()
            flash('Your password has been set. Welcome to your dashboard!', 'success')
            return redirect(url_for('marketing.dashboard'))
        else:
            flash('Incorrect current password.', 'danger')
            
    return render_template('auth/force_reset.html', form=form)

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    profile_form = ProfileForm()
    password_form = ChangePasswordForm()
    
    # Handle Profile Update
    if profile_form.submit_profile.data and profile_form.validate():
        current_user.first_name = profile_form.first_name.data
        current_user.last_name = profile_form.last_name.data
        current_user.email = profile_form.email.data
        db.session.commit()
        flash('Profile details updated.', 'success')
        return redirect(url_for('auth.profile'))
        
    # Handle Password Change
    if password_form.submit_password.data and password_form.validate():
        if check_password_hash(current_user.password, password_form.current_password.data):
            current_user.password = generate_password_hash(password_form.new_password.data)
            db.session.commit()
            flash('Password changed successfully.', 'success')
            return redirect(url_for('auth.profile'))
        else:
            flash('Incorrect current password.', 'danger')
            
    # Pre-populate Profile Form
    if request.method == 'GET':
        profile_form.first_name.data = current_user.first_name
        profile_form.last_name.data = current_user.last_name
        profile_form.email.data = current_user.email

    return render_template('auth/profile.html', profile_form=profile_form, password_form=password_form)

import os
from .forms import SignupForm

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('marketing.dashboard'))
        
    form = SignupForm()
    
    if form.validate_on_submit():
        try:
            # 1. Calculate Totals
            setup_fee = 4999 # $49.99
            base_plan_price = 2999 # $29.99
            facebook_addon_price = 6900 # $69.00
            
            monthly_total = base_plan_price
            if form.add_facebook.data:
                monthly_total += facebook_addon_price
            
            initial_charge_total = setup_fee + monthly_total
            full_name = f"{form.first_name.data} {form.last_name.data}"
            
            # BYPASS CHECK - must happen BEFORE Square instantiation
            if form.card_nonce.data == "fake-nonce-bypass":
                print("DEBUG: Bypassing Square Payment")
                customer_id = "cus_bypass_mode"
                success = True
                subscription_id = "sub_bypass_mode"
            else:
                # 2. Square: Create Customer & Process Initial Payment
                try:
                    from app.integrations.square_payments import SquarePaymentService
                    print("DEBUG: Instantiating SquarePaymentService inside route...", file=sys.stdout)
                    square = SquarePaymentService()
                    print("DEBUG: SquarePaymentService instantiated.", file=sys.stdout)
                except Exception as e:
                    print(f"CRITICAL ERROR instantiating SquarePaymentService: {e}", file=sys.stderr)
                    import traceback
                    traceback.print_exc()
                    flash('Payment Service Error: Please contact support.', 'danger')
                    square_env = os.environ.get('SQUARE_ENVIRONMENT', 'sandbox')
                    script_url = "https://sandbox.web.squareup.com/v1/square.js" if square_env == 'sandbox' else "https://web.squareup.com/v1/square.js"
                    return render_template('auth/signup.html', form=form, 
                                           SQUARE_APP_ID=os.environ.get('SQUARE_APP_ID'),
                                           SQUARE_V1_SCRIPT_URL=script_url)
                
                customer_id = square.create_customer(form.email.data, full_name)
                
                if not customer_id:
                    flash('Payment Gateway Error: Could not create customer. Please try again.', 'danger')
                    square_env = os.environ.get('SQUARE_ENVIRONMENT', 'sandbox')
                    script_url = "https://sandbox.web.squareup.com/v1/square.js" if square_env == 'sandbox' else "https://web.squareup.com/v1/square.js"
                    return render_template('auth/signup.html', form=form, 
                                           SQUARE_APP_ID=os.environ.get('SQUARE_APP_ID'),
                                           SQUARE_V1_SCRIPT_URL=script_url)
                
                # Process Payment
                success, result_id = square.charge_card(
                    source_id=form.card_nonce.data,
                    amount_cents=initial_charge_total,
                    customer_id=customer_id,
                    note=f"Setup Fee & First Month for {form.org_name.data}"
                )
                
                if not success:
                    flash(f"Payment Failed: {result_id}", 'danger')
                    square_env = os.environ.get('SQUARE_ENVIRONMENT', 'sandbox')
                    script_url = "https://sandbox.web.squareup.com/v1/square.js" if square_env == 'sandbox' else "https://web.squareup.com/v1/square.js"
                    return render_template('auth/signup.html', form=form, 
                                           SQUARE_APP_ID=os.environ.get('SQUARE_APP_ID'),
                                           SQUARE_V1_SCRIPT_URL=script_url)
                
                # 3. Create Subscription (Future)
                card_id = square.store_card(customer_id, form.card_nonce.data)
                
                plan_name = "Base + Facebook" if form.add_facebook.data else "Base Plan"
                plan_id = square.create_subscription_plan(plan_name, monthly_total)
                
                subscription_id = None
                if plan_id and card_id:
                    subscription_id = square.start_subscription(customer_id, card_id, plan_id)

            # 4. Create Organization
            from app.core.models import Organization, User
            from werkzeug.security import generate_password_hash
            
            org = Organization(
                name=form.org_name.data,
                slug=form.subdomain.data.lower(),
                modules={'facebook': form.add_facebook.data, 'ari': False},
                customer_id=customer_id,
                subscription_id=subscription_id,
                subscription_status='active' if success else 'pending',
                plan_type='base_plus_fb' if form.add_facebook.data else 'base'
            )
            db.session.add(org)
            db.session.flush() # Get ID
            
            # 5. Create User
            user = User(
                organization_id=org.id,
                username=form.email.data,
                email=form.email.data,
                password=generate_password_hash(form.password.data),
                role='admin',
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                password_reset_required=False
            )
            db.session.add(user)
            db.session.commit()

            # 6. Send Welcome Email
            try:
                from app.core.email import send_welcome_email
                send_welcome_email(
                    dealer_name=org.name,
                    dealer_email=form.email.data,
                    username=user.username,
                    dealer_slug=org.slug
                )
            except Exception as e:
                print(f"Warning: Failed to send welcome email: {e}")

            # 7. Login
            login_user(user)
            session['organization_id'] = org.id
            flash('Account created successfully! Welcome to your new dashboard.', 'success')
            return redirect(url_for('marketing.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            print(f"Signup Error: {e}")
            flash('An unexpected error occurred. Please try again.', 'danger')

    square_env = os.environ.get('SQUARE_ENVIRONMENT', 'sandbox')
    script_url = "https://sandbox.web.squareup.com/v1/square.js" if square_env == 'sandbox' else "https://web.squareup.com/v1/square.js"

    if form.errors:
        print(f"DEBUG: Form validation failed: {form.errors}")

    return render_template('auth/signup.html', form=form, 
                           SQUARE_APP_ID=os.environ.get('SQUARE_APP_ID'),
                           SQUARE_LOCATION_ID=os.environ.get('SQUARE_LOCATION_ID'),
                           SQUARE_V1_SCRIPT_URL=script_url)
