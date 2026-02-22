#!/usr/bin/env python3
"""
Mark NC Power Equipment as needing onboarding.
"""

import sys
sys.path.insert(0, '/root/power_equip_saas')

from app import create_app
from app.core.models import Organization, User
from app.core.extensions import db

app = create_app()

def mark_for_onboarding(org_name):
    """Mark an organization for onboarding."""
    try:
        with app.app_context():
            org = Organization.query.filter_by(name=org_name).first()
            if not org:
                print(f"❌ Organization '{org_name}' not found")
                return False

            print(f"\n{'='*60}")
            print(f"Marking for Onboarding: {org_name}")
            print(f"{'='*60}")

            # Check current status
            print(f"\nCurrent Status:")
            print(f"  - Organization: {org.name}")
            print(f"  - Slug: {org.slug}")
            print(f"  - Onboarding Complete: {org.onboarding_complete}")

            # Get users
            users = User.query.filter_by(organization_id=org.id).all()
            print(f"\n  Users ({len(users)}):")
            for user in users:
                print(f"    - Username: {user.username}")
                print(f"      Email: {user.email}")
                print(f"      Active: {user.is_active}")

            # Mark as needing onboarding
            org.onboarding_complete = False
            db.session.commit()

            print(f"\n✅ {org.name} has been marked for onboarding!")
            print(f"   Next login will redirect to: /settings/onboarding")
            print(f"\n{'='*60}\n")
            return True

    except Exception as e:
        db.session.rollback()
        print(f"\n❌ Error: {str(e)}")
        return False

if __name__ == '__main__':
    import sys
    dealer_name = sys.argv[1] if len(sys.argv) > 1 else "NC Power Equipment Inc."
    mark_for_onboarding(dealer_name)
