import os
import sys

sys.path.append(os.getcwd())
# Ensure we use explicit absolute path just in case
os.environ['DB_URI'] = 'sqlite:////home/clawd_operator/app-saas-dev/instance/dev.db'

from app import create_app, db
from app.core.models import User, Organization
from werkzeug.security import generate_password_hash

app = create_app('dev')

with app.app_context():
    print("Creating tables...")
    db.create_all()
    
    # Check Org
    if not Organization.query.get(1):
        print("Creating Master Org...")
        org = Organization(
            name="Bob's Demo Shop",
            slug="bob-demo",
            is_active=True,
            theme_config={"brand_logos": []} 
        )
        db.session.add(org)
        db.session.commit() # Get ID
        print(f"Org created with ID: {org.id}")
    else:
        print("Org 1 exists.")
        org = Organization.query.get(1)

    # Check User
    u = User.query.filter_by(username='admin').first()
    if not u:
        print("Creating Admin User...")
        u = User(
            username='admin',
            email='admin@bentcrankshaft.com',
            password=generate_password_hash('BobBuilder2026!'),
            role='super_admin',
            organization_id=org.id,
            password_reset_required=False
        )
        db.session.add(u)
        db.session.commit()
        print("✅ Admin user created.")
    else:
        print("Admin user exists. Updating password...")
        u.password = generate_password_hash('BobBuilder2026!')
        db.session.commit()
        print("✅ Admin password reset.")

