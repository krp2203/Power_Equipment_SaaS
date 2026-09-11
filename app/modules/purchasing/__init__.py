from flask import Blueprint
from app.core.module_guards import require_pos_module

purchasing_bp = Blueprint('purchasing', __name__, template_folder='templates')

purchasing_bp.before_request(require_pos_module)

from . import routes
