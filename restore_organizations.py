
from app import create_app, db
from app.core.models import Organization
import os

app = create_app(os.getenv('FLASK_CONFIG') or 'default')

with app.app_context():
    # Restore ncpower
    if not Organization.query.filter_by(slug='ncpower').first():
        print("Restoring 'ncpower'...")
        org_nc = Organization(
            name="NC Power Equipment",
            slug="ncpower",
            is_active=True,
            onboarding_complete=True,
            modules={"ari": True, "facebook": True},
            theme_config={"primaryColor": "#ff0000"} 
        )
        db.session.add(org_nc)
    else:
        print("'ncpower' already exists.")

    # Restore kens-mowers
    if not Organization.query.filter_by(slug='kens-mowers').first():
        print("Restoring 'kens-mowers'...")
        org_km = Organization(
            name="Ken's Mowers",
            slug="kens-mowers",
            is_active=True,
            onboarding_complete=True,
            modules={"pos": "ideal"},
            theme_config={"primaryColor": "#00ff00"}
        )
        db.session.add(org_km)
    else:
        print("'kens-mowers' already exists.")

    db.session.commit()
    print("✅ Restoration complete.")
