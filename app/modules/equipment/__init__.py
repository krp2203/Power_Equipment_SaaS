from flask import Blueprint
from app.core.module_guards import require_pos_module

equipment_bp = Blueprint('equipment', __name__, template_folder='templates')

equipment_bp.before_request(require_pos_module)

from . import routes  # noqa: E402,F401
