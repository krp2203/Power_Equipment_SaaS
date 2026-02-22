from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from celery import Celery

db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
csrf = CSRFProtect()
migrate = Migrate()

# Initialize Celery with proper name and task includes
# The include parameter tells Celery which modules contain tasks
celery = Celery(
    'power_equip_saas',
    include=['app.tasks.marketing', 'app.tasks.pos_sync']
)
