from flask import Blueprint

marketing_bp = Blueprint('marketing', __name__, template_folder='templates')

from . import routes
