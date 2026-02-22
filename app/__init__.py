import gevent.monkey
gevent.monkey.patch_all()

import os
from flask import Flask, g, request, session
from config import config_by_name
from app.core.extensions import db, login_manager, mail, celery, csrf

from flask_cors import CORS

def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'dev')
        
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    # Fix for SSL when behind proxy
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # Initialize Extensions
    db.init_app(app)
    from app.core.extensions import migrate
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    mail.init_app(app)
    csrf.init_app(app)
    # Celery init with autodiscovery
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask

    # Autodiscover tasks
    celery.autodiscover_tasks(['app.tasks'])
    
    # CORS is handled by same-origin proxying in Nginx, 
    # but we can enable it specifically if needed.
    CORS(app, supports_credentials=True)
    
    # Initialize Bootstrap
    from flask_bootstrap import Bootstrap
    Bootstrap(app)

    # Register Multitenancy Hooks
    from app.core.multitenancy import register_multitenancy_handlers
    with app.app_context():
        register_multitenancy_handlers(app)

    # Middleware: Tenant Context
    @app.before_request
    def load_tenant_context():
        import sys
        print(f"DEBUG: before_request called for {request.path}", file=sys.stderr)
        from app.core.models import Organization
        from flask import render_template, make_response
        print(f"DEBUG: Request Path: {request.path}, Host: {request.host}, Session Org ID: {session.get('organization_id')}", flush=True)
        
        # 0. Check for 'public' or 'www' (landing page) - Optional optimization
        # if request.host.startswith('www.') or request.host == app.config['SERVER_NAME']:
        #     g.current_org = None
        #     return

        # 1. Resolve Tenant via Subdomain FIRST (Source of Truth for the URL)
        tenant = None
        
        # Check Headers first (Nginx or Dev Proxy)
        header_host = request.headers.get('X-Forwarded-Host', request.host)
        host_parts = header_host.split('.')
        
        if len(host_parts) >= 3:
            potential_slug = host_parts[0]
            if potential_slug in ['www', 'app', 'saas', 'mail', 'api', 'admin']:
                print(f"DEBUG: Master subdomain detected: {potential_slug}", flush=True)
                tenant = Organization.query.get(1)
            else:
                tenant = Organization.query.filter_by(slug=potential_slug).first()
        elif 'localhost' in header_host or '127.0.0.1' in header_host:
             # Localhost Development: Default to Master Org if no subdomain
             tenant = Organization.query.get(1)
        else:
            # Check for custom domain mapping (e.g., ncpowerequipment.com)
            tenant = Organization.query.filter_by(custom_domain=header_host).first()

            if not tenant:
                # Root Domain (bentcrankshaft.com) or other unmapped domain
                # Special Case: Allow Impersonation

                # If a Super Admin is properly impersonating another org, let them seeing that org's context.
                if session.get('impersonation_origin_org'):
                     # Trust the session's target org
                     target_id = session.get('organization_id')
                     tenant = Organization.query.get(target_id)
                else:
                    # otherwise, FORCE context to Master Organization (ID 1)
                    print("DEBUG: DEFAULTING TO MASTER ORG (ID 1)", flush=True)
                    # Fallback to ID 1, or first available org if ID 1 is missing
                    tenant = Organization.query.get(1) or Organization.query.first()
                    print(f"DEBUG: Fallback tenant found: {tenant.name if tenant else 'None'}", flush=True)

        # 2. Reconcile with Session
        session_org_id = session.get('organization_id')
        impersonation_origin = session.get('impersonation_origin_org')
        
        # Determine if user is effectively a Superuser (Org 1 Admin)
        is_superuser = (session_org_id == 1 or impersonation_origin == 1)

        # Logic to decide current organization
        if tenant:
            # If we are visiting a subdomain, that IS the context.
            if session_org_id and session_org_id != tenant.id and not is_superuser:
                 # Security: Logged into Org A but visiting Org B (and not superuser).
                 # Clear session to force re-login for the correct tenant.
                 session.clear()
                 from flask_login import logout_user
                 logout_user()
            
            g.current_org = tenant
            g.current_org_id = tenant.id
        elif session_org_id:
            # Root domain or admin context without subdomain
            g.current_org = Organization.query.get(session_org_id)
            if not g.current_org:
                 # Orphan session with deleted org
                 session.clear()
                 from flask_login import logout_user
                 logout_user()
            g.current_org_id = session_org_id
        else:
            g.current_org = None
            g.current_org_id = None

        # 3. Finalize Global Context
        g.is_superuser = is_superuser
        
        if g.current_org:
            # Check if organization is inactive (suspended)
            is_exempt_route = (
                request.path.startswith('/api/') or
                request.path.startswith('/super_admin/') or
                request.path.startswith('/backend/') or
                request.path.startswith('/static/') or
                request.path.startswith('/auth/') or
                g.is_superuser
            )
            
            if not g.current_org.is_active and not is_exempt_route:
                response = make_response(render_template('suspended.html'), 503)
                response.headers['Retry-After'] = '3600'
                return response



    # Register Blueprints
    from app.modules.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.modules.main import main_bp
    app.register_blueprint(main_bp)

    from app.modules.dealers import dealers_bp
    app.register_blueprint(dealers_bp)

    from app.modules.units import units_bp
    app.register_blueprint(units_bp)

    from app.modules.cases import cases_bp
    app.register_blueprint(cases_bp)

    from app.modules.service_bulletins import service_bulletins_bp
    app.register_blueprint(service_bulletins_bp)

    from app.modules.api import api_bp
    # Exempt API blueprint from CSRF (uses X-Bridge-Key authentication)
    csrf.exempt(api_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

    from app.modules.marketing import marketing_bp
    app.register_blueprint(marketing_bp)
    
    from app.modules.inventory import inventory_bp
    app.register_blueprint(inventory_bp, url_prefix='/admin/inventory')
    
    from app.modules.settings import settings_bp
    app.register_blueprint(settings_bp)

    from app.modules.super_admin import super_admin_bp
    app.register_blueprint(super_admin_bp, url_prefix='/super_admin')

    # Register filters
    from app.core import filters
    filters.register_filters(app)

    # User Loader
    from app.core.models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @login_manager.unauthorized_handler
    def unauthorized():
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Unauthorized'}), 401
        from flask import redirect, url_for
        return redirect(url_for('auth.login', next=request.url))

    # Video Streaming Optimization
    @app.after_request
    def add_video_headers(response):
        """Add proper headers for video streaming and caching"""
        # Check if this is a video file
        if response.content_type and response.content_type.startswith('video/'):
            # Enable byte range requests for streaming (critical for buffering!)
            response.headers['Accept-Ranges'] = 'bytes'

            # Cache video files for 7 days (they're immutable after upload)
            response.headers['Cache-Control'] = 'public, max-age=604800'

            # Allow conditional requests for efficient caching
            response.headers['ETag'] = response.headers.get('ETag', '')
            response.headers['Vary'] = 'Accept-Encoding'

        return response

    return app
