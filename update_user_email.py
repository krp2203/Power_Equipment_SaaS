#!/usr/bin/env python3
"""
Update a user's email address.
"""

import sys
sys.path.insert(0, '/root/power_equip_saas')

from app import create_app
from app.core.models import Organization, User
from app.core.extensions import db

app = create_app()

def update_user_email(org_name, new_email):
    """Update the primary user's email for an organization."""
    try:
        with app.app_context():
            org = Organization.query.filter_by(name=org_name).first()
            if not org:
                print(f"❌ Organization '{org_name}' not found")
                return False

            user = User.query.filter_by(organization_id=org.id).first()
            if not user:
                print(f"❌ No users found for {org_name}")
                return False

            print(f"\n{'='*60}")
            print(f"Updating User Email: {org_name}")
            print(f"{'='*60}")

            print(f"\nBefore:")
            print(f"  - Username: {user.username}")
            print(f"  - Email: {user.email}")

            user.email = new_email
            db.session.commit()

            print(f"\nAfter:")
            print(f"  - Username: {user.username}")
            print(f"  - Email: {user.email}")

            print(f"\n✅ Email updated successfully!")
            print(f"\n{'='*60}\n")
            return True

    except Exception as e:
        db.session.rollback()
        print(f"\n❌ Error: {str(e)}")
        return False

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python update_user_email.py '<org_name>' '<email>'")
        sys.exit(1)

    org_name = sys.argv[1]
    new_email = sys.argv[2]
    update_user_email(org_name, new_email)
