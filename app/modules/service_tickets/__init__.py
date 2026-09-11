from flask import Blueprint
from app.core.module_guards import require_pos_module

service_tickets_bp = Blueprint('service_tickets', __name__, template_folder='templates')

service_tickets_bp.before_request(require_pos_module)

from . import routes
