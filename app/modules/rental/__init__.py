from flask import Blueprint
from app.core.module_guards import require_rental_module

rental_bp = Blueprint('rental', __name__, template_folder='templates')

rental_bp.before_request(require_rental_module)

from . import routes
