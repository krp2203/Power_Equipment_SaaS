from app import create_app
from app.core.models import User
from app.core.extensions import db
app = create_app()
with app.app_context():
    user = User.query.filter_by(username='saas_admin').first()
    if user:
        user.password = 'admin123'
        db.session.commit()
        print('Password for saas_admin reset to admin123')
    else:
        print('User saas_admin not found')
