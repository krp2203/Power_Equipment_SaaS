from flask import jsonify, request, session, g
from flask_login import login_required, current_user
from app.core.extensions import db
from app.core.models import Organization
from app.modules.api import api_bp

@api_bp.route('/v1/super_admin/tenants', methods=['GET'])
def api_list_tenants():
    """List all organizations as JSON for super admin"""
    if not current_user.is_authenticated:
        return jsonify({'error': 'Unauthenticated'}), 401
        
    print(f"DEBUG: api_list_tenants called. User: {current_user.username}. Org ID: {g.get('current_org_id')}")
    # Security: Ensure only Super Admin (Org 1) can do this
    if g.current_org_id != 1 and not session.get('impersonation_origin_org'):
        print(f"DEBUG: api_list_tenants Unauthorized. Org ID: {g.current_org_id}")
        return jsonify({'error': 'Unauthorized'}), 403
    
    orgs = Organization.query.order_by(Organization.id).all()
    return jsonify({
        'organizations': [{
            'id': org.id,
            'name': org.name,
            'modules': org.modules,
            'theme': org.theme_config
        } for org in orgs]
    })

@api_bp.route('/v1/super_admin/impersonate/<int:org_id>', methods=['POST'])
def api_impersonate(org_id):
    """Impersonate an organization (JSON response)"""
    if not current_user.is_authenticated:
        return jsonify({'error': 'Unauthenticated'}), 401
        
    # Security: Ensure only Super Admin (Org 1) can do this
    if g.current_org_id != 1 and not session.get('impersonation_origin_org'):
        return jsonify({'error': 'Unauthorized'}), 403

    target_org = Organization.query.get_or_404(org_id)
    
    # Store original org if this is the first hop
    if 'impersonation_origin_org' not in session:
        session['impersonation_origin_org'] = g.current_org_id
        
    # Switch Context
    session['organization_id'] = target_org.id
    
    response = jsonify({
        'success': True,
        'message': f'Now viewing as {target_org.name}',
        'organization_id': target_org.id
    })
    response.set_cookie('is_impersonating', 'true', path='/')
    return response

@api_bp.route('/v1/super_admin/exit_impersonation', methods=['POST'])
def api_exit_impersonation():
    """Exit impersonation mode (JSON response)"""
    if not current_user.is_authenticated:
        return jsonify({'error': 'Unauthenticated'}), 401
        
    print(f"DEBUG: api_exit_impersonation called. User: {current_user.username}")
    origin_id = session.get('impersonation_origin_org')
    
    response = jsonify({
        'success': True,
        'message': 'Restored original admin context' if origin_id else 'Cleared impersonation cookie',
        'organization_id': origin_id or 1 # Fallback to Master
    })
    
    if origin_id:
        print(f"DEBUG: Restoring origin Org ID: {origin_id}")
        session['organization_id'] = origin_id
        session.pop('impersonation_origin_org', None)
    else:
        print("DEBUG: No impersonation_origin_org in session, but clearing cookie anyway.")
        # If they are stuck, force them back to Org 1 if they are an admin
        if current_user.organization_id == 1:
            session['organization_id'] = 1

    response.delete_cookie('is_impersonating', path='/')
    return response
