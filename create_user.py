from app import create_app, db
from app.core.models import User, Organization
from werkzeug.security import generate_password_hash

app = create_app('dev')

with app.app_context():
    # Ensure Org 1 exists
    org = Organization.query.get(1)
    if not org:
        print("Creating default Organization...")
        org = Organization(name="Demo Dealer", settings={}, modules={"ari": True})
        db.session.add(org)
        db.session.commit()

    # Create User
    user = User.query.filter_by(username='admin').first()
    if not user:
        print("Creating admin user...")
        user = User(
            username='admin',
            password=generate_password_hash('password'),
            organization_id=org.id,
            role='admin'
        )
        db.session.add(user)
        db.session.commit()
        print("User 'admin' created with password 'password'.")
    else:
        print("User 'admin' already exists.")
