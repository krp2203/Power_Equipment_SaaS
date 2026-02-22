import os
import sys

sys.path.append(os.getcwd())
os.environ['DB_URI'] = 'sqlite:////home/clawd_operator/app-saas-dev/instance/dev.db'

from app import create_app, db
from app.core.models import User
from werkzeug.security import generate_password_hash

app = create_app('dev')

with app.app_context():
    u = User.query.filter_by(username='admin').first()
    if u:
        print(f"Resetting password for {u.username} (ID: {u.id})...")
        # CRITICAL FIX: The column identifier is 'password', not 'password_hash'
        u.password = generate_password_hash("BobBuilder2026!")
        db.session.commit()
        print("✅ PASSWORD RESET SUCCESSFUL (Correct column updated)")
    else:
        print("❌ Admin user not found")
