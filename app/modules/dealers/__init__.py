from flask import Blueprint

dealers_bp = Blueprint('dealers', __name__, template_folder='../../templates/dealers')

from . import routes
