from flask import render_template, request, g, redirect, url_for
from flask_login import login_required, current_user
from app.core.extensions import db
from app.core.models import Case, User, Organization
from datetime import datetime, timedelta
from sqlalchemy import select, func

from . import main_bp

@main_bp.route('/')
def index():
    # Check hostname to determine if we should show the public landing page
    # In production, this would look for 'bentcrankshaft.com'
    # We also include localhost for testing
    host = request.host.split(':')[0]
    public_hosts = ['bentcrankshaft.com', 'www.bentcrankshaft.com']
    
    if host in public_hosts and not current_user.is_authenticated:
        return render_template('main/demo_landing.html')

    # Redirect root to the new dashboard location
    # If not logged in, this will trigger the login page via the dashboard's @login_required
    return redirect(url_for('marketing.dashboard'))

@main_bp.route('/update-modules-ajax-wrapper/<int:org_id>', methods=['POST'])
@login_required
def update_modules_ajax_wrapper(org_id):
    # This is a wrapper to handle the AJAX call from the dashboard
    # It avoids cross-module URL issues in dev
    from flask import jsonify
    from app.modules.super_admin.routes import update_modules_ajax
    return update_modules_ajax(org_id)

