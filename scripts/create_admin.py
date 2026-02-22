import sys
import os

# Add parent directory to path to import app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.core.extensions import db
from app.core.models import User
from werkzeug.security import generate_password_hash

def create_admin_user():
    app = create_app('dev')
    with app.app_context():
        # Check if admin exists
        admin = User.query.filter_by(username='admin').first()
        
        hashed_password = generate_password_hash('admin')
        
        if admin:
            print("Admin user already exists. Updating password...")
            admin.password_hash = hashed_password
            admin.organization_id = 1
        else:
            print("Creating new admin user...")
            admin = User(
                username='admin',
                email='admin@example.com',
                password=hashed_password,
                organization_id=1,
                role='admin'
            )
            db.session.add(admin)
        
        try:
            db.session.commit()
            print("Successfully created/updated admin user.")
            print("Username: admin")
            print("Password: admin")
        except Exception as e:
            db.session.rollback()
            print(f"Error creating admin user: {e}")

if __name__ == "__main__":
    create_admin_user()
