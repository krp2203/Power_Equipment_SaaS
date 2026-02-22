import os
import sqlalchemy
from sqlalchemy import create_engine, inspect

db_uri = os.environ.get('DB_URI', 'sqlite:////home/clawd_operator/app-saas-dev/instance/dev.db')
print(f"Checking database at: {db_uri}")

try:
    # Strip sqlite:/// prefix if exists for os.path check
    path = db_uri.replace('sqlite:///', '')
    if os.path.exists(path):
        print(f"File exists. Size: {os.path.getsize(path)} bytes")
    else:
        print("File DOES NOT exist!")

    engine = create_engine(db_uri)
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"Tables found: {tables}")
    
    if 'organization' in tables:
        print("SUCCESS: organization table found!")
    else:
        print("FAILURE: organization table is MISSING!")
except Exception as e:
    print(f"ERROR: {str(e)}")
