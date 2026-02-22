from app import create_app, db
from app.core.models import Organization

app = create_app('dev')

with app.app_context():
    org = Organization.query.get(1)
    if org:
        print(f"Current Modules: {org.modules}")
        print(f"Current Theme: {org.theme_config}")
        
        # Update settings
        org.modules = {"ari": True, "pos": "ideal"}
        org.theme_config = {"primaryColor": "#2563EB"} # Blue
        
        db.session.commit()
        print("Updated Organization 1: ARI Enabled, Theme Blue.")
    else:
        print("Organization 1 not found.")
