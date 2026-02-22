from flask import jsonify, g
from flask_login import login_required, current_user
from app.modules.api import api_bp

@api_bp.route('/v1/auth/me', methods=['GET'])
def api_me():
    """Check current authentication status and return user info"""
    if not current_user.is_authenticated:
        return jsonify({'authenticated': False}), 401
        
    return jsonify({
        'authenticated': True,
        'user': {
            'id': current_user.id,
            'username': current_user.username,
            'organization_id': current_user.organization_id
        }
    }), 200
