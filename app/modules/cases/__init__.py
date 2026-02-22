from flask import Blueprint

cases_bp = Blueprint('cases', __name__, template_folder='../../templates/cases')

from . import routes
