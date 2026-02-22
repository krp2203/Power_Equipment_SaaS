from flask import Blueprint

service_bulletins_bp = Blueprint('service_bulletins', __name__, template_folder='../../templates/service_bulletins')

from . import routes
