#!/usr/bin/env python3
"""
Check user email for Ken's Mowers.
"""

import sys
sys.path.insert(0, '/root/power_equip_saas')

from app import create_app
from app.core.models import Organization, User

app = create_app()

with app.app_context():
    org = Organization.query.filter_by(name="Ken's Mowers").first()
    if org:
        users = User.query.filter_by(organization_id=org.id).all()
        print(f"\nKen's Mowers Users:")
        print("=" * 60)
        for user in users:
            print(f"  Username: {user.username}")
            print(f"  Email: {user.email}")
            print(f"  First Name: {user.first_name}")
            print(f"  Last Name: {user.last_name}")
            print()
