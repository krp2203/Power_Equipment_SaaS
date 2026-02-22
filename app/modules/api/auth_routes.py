from flask import jsonify, request
from flask_login import login_user
from werkzeug.security import check_password_hash
from app.core.models import User
from app.modules.api import api_bp

@api_bp.route('/v1/auth/login', methods=['POST'])
def api_login():
    """JSON login endpoint for Next.js frontend"""
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Username and password required'}), 400
    
    user = User.query.filter_by(username=data['username']).first()
    
    if not user or not check_password_hash(user.password, data['password']):
        print(f"DEBUG: API Login failed for user {data.get('username')}")
        return jsonify({'message': 'Invalid username or password'}), 401
    
    from flask import session
    login_user(user)
    session['organization_id'] = user.organization_id
    print(f"DEBUG: API Login successful for {user.username}. Org ID: {user.organization_id}")
    
    return jsonify({
        'success': True,
        'user': {
            'id': user.id,
            'username': user.username,
            'organization_id': user.organization_id
        }
    }), 200

@api_bp.route('/v1/auth/logout', methods=['POST'])
def api_logout():
    """JSON logout endpoint"""
    from flask_login import logout_user
    logout_user()
    return jsonify({'success': True}), 200
