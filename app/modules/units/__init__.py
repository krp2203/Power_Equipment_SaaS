from flask import Blueprint

units_bp = Blueprint('units', __name__, template_folder='../../templates/units')

from . import routes
