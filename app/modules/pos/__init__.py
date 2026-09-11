from flask import Blueprint
from app.core.module_guards import require_pos_module

pos_bp = Blueprint('pos', __name__, template_folder='templates')

pos_bp.before_request(require_pos_module)

from . import routes
