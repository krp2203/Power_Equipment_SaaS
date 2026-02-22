#!/usr/bin/env python3
"""
Send a test welcome email to a dealer.
"""

import sys
sys.path.insert(0, '/root/power_equip_saas')

from app import create_app
from app.core.models import Organization, User
from app.core.email import send_welcome_email

app = create_app()

def send_test_welcome(dealer_name):
    """Send a test welcome email to a dealer."""
    try:
        with app.app_context():
            org = Organization.query.filter_by(name=dealer_name).first()
            if not org:
                print(f"❌ Organization '{dealer_name}' not found")
                return False

            print(f"\n{'='*60}")
            print(f"Sending Test Welcome Email: {dealer_name}")
            print(f"{'='*60}")

            # Get primary user
            user = User.query.filter_by(organization_id=org.id).first()
            if not user:
                print(f"❌ No users found for {dealer_name}")
                return False

            print(f"\nOrganization: {org.name}")
            print(f"User: {user.username}")
            print(f"Email: {user.email}")

            # Send welcome email
            print(f"\n📤 Sending welcome email...")
            result = send_welcome_email(
                dealer_name=org.name,
                dealer_email=user.email,
                username=user.username,
                dealer_slug=org.slug
            )

            if result:
                print(f"\n✅ Welcome email sent successfully!")
                print(f"   Recipient: {user.email}")
                print(f"   From: noreply@mail.bentcrankshaft.com")
            else:
                print(f"\n❌ Failed to send welcome email")

            print(f"\n{'='*60}\n")
            return result

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False

if __name__ == '__main__':
    dealer_name = sys.argv[1] if len(sys.argv) > 1 else "Ken's Mowers"
    send_test_welcome(dealer_name)
