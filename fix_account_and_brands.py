import os
import sys

# Setup Flask Environment
sys.path.append(os.getcwd())
os.environ['DB_URI'] = 'sqlite:////home/clawd_operator/app-saas-dev/instance/dev.db'

from app import create_app, db
from app.core.models import User, Organization
from werkzeug.security import generate_password_hash

app = create_app('dev')

with app.app_context():
    print("--- User Check ---")
    users = User.query.all()
    target_user = None
    for u in users:
        print(f"User: {u.id} | Email: {u.email} | Role: {u.role}")
        # Look for a likely admin
        if u.role in ['super_admin', 'admin', 'owner']:
             target_user = u
        if u.email == 'admin@bentcrankshaft.com': # Common default
             target_user = u
             break
    
    if not target_user and users:
        target_user = users[0] # Fallback to first user
        print(f"No specific admin found, defaulting to first user: {target_user.email}")

    if target_user:
        new_pass = "BobBuilder2026!"
        target_user.password_hash = generate_password_hash(new_pass)
        db.session.commit()
        print(f"\n✅ PASSWORD RESET SUCCESSFUL")
        print(f"Email: {target_user.email}")
        print(f"Password: {new_pass}")
    else:
        print("❌ No users found in database!")

    print("\n--- Brand Banner Injection ---")
    # Update Org 1 (Master) and Org 2 (Demo if exists)
    orgs = Organization.query.all()
    
    # Mock Logos
    brands = [
        {"name": "Scag", "logo_url": "https://www.scag.com/wp-content/uploads/2019/10/scag_logo.png"},
        {"name": "Echo", "logo_url": "https://www.echo-usa.com/getattachment/557d0774-726e-4c74-9494-0130932e652c/ECHO-Logo.aspx"},
        {"name": "Stihl", "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/12/Stihl-Logo.svg/2560px-Stihl-Logo.svg.png"}
    ]

    for org in orgs:
        # We need to update the settings/theme JSON
        # This depends on the model structure. Assuming 'theme_config' or 'settings' dict.
        # Based on previous output: "theme": { "brand_logos": ... }
        
        current_theme = org.theme_config or {}
        if not current_theme.get('brand_logos'):
            print(f"Injecting brands into Org {org.id} ({org.name})...")
            current_theme['brand_logos'] = brands
            org.theme_config = current_theme
            db.session.add(org)
    
    db.session.commit()
    print("✅ Brand Injection Complete")

