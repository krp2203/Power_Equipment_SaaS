from app import create_app
from app.core.models import User, Organization
from app.core.extensions import db

print("Creating app context...")
app = create_app('prod')

with app.app_context():
    print(f"Checking database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    # 1. Search by Username
    email = 'bob@oufalouski.com'
    print(f"Searching for username: {email}") # Using email variable as username check
    user_by_name = User.query.filter_by(username=email).first()
    if user_by_name:
        print(f"FOUND BY USERNAME: ID={user_by_name.id}, Email='{user_by_name.email}'")
    
    # 2. Search for Org
    org_name = "kens-mowers"
    print(f"Searching for Org Slug: {org_name}")
    org = Organization.query.filter_by(slug=org_name).first()
    if org:
         print(f"FOUND ORG: ID={org.id}, Name='{org.name}'")
         print("Users in this Org:")
         for u in org.users:
             print(f" - ID={u.id}, Username='{u.username}', Email='{u.email}'")
    else:
        print("Org 'kens-mowers' NOT found.")

    print("-" * 20)
    print("Listing ALL Users:")
    users = User.query.all()
    for u in users:
        print(f"ID={u.id} | Email='{u.email}' | Username='{u.username}' | OrgID={u.organization_id}")
