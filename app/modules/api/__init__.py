from flask import Blueprint

api_bp = Blueprint('api', __name__)

from . import routes, auth_routes, super_admin_routes, me, bridge_routes
