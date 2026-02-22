
import os
from app import create_app
from app.core.extensions import db
from app.core.models import Organization, User, Dealer

app = create_app()
with app.app_context():
    orgs = Organization.query.all()
    print(f"Total Organizations: {len(orgs)}")
    for org in orgs:
        users = User.query.filter_by(organization_id=org.id).all()
        dealers = Dealer.query.filter_by(organization_id=org.id).all()
        print(f"Org: {org.name} (ID: {org.id}, Slug: {org.slug})")
        print(f"  Users: {[u.username for u in users]}")
        print(f"  Dealers: {[d.name for d in dealers]}")
        print("-" * 20)
