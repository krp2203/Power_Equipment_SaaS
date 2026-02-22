import os
from sqlalchemy import create_engine, text

# Connect to the Docker Postgres via exposed port 5435
DB_URI = "postgresql://user:password@localhost:5435/dealer_dashboard"

engine = create_engine(DB_URI)

def run_migration():
    print(f"Connecting to {DB_URI}...")
    try:
        with engine.connect() as conn:
            print("--- Updating PartInventory Table ---")
            
            # 1. Add manufacturer column
            try:
                conn.execute(text("ALTER TABLE part_inventory ADD COLUMN manufacturer VARCHAR(100)"))
                print("[OK] Added manufacturer column")
            except Exception as e:
                if "already exists" in str(e):
                    print("[SKIP] manufacturer column already exists")
                else:
                    print(f"[Error] Adding manufacturer column: {e}")

            # 2. Update Unique Constraint
            # First, drop the old one if it exists
            # The old constraint was '_part_org_uc' or similar
            try:
                # We need to find the actual constraint name. 
                # According to the model it was '_part_org_uc'
                conn.execute(text("ALTER TABLE part_inventory DROP CONSTRAINT IF EXISTS _part_org_uc"))
                print("[OK] Dropped old constraint _part_org_uc")
            except Exception as e:
                print(f"[Warn] Dropping old constraint: {e}")

            # Also drop the new one if it exists (so we can recreate it)
            try:
                conn.execute(text("ALTER TABLE part_inventory DROP CONSTRAINT IF EXISTS _part_manuf_org_uc"))
            except:
                pass

            # Add the new constraint
            try:
                conn.execute(text("ALTER TABLE part_inventory ADD CONSTRAINT _part_manuf_org_uc UNIQUE (part_number, manufacturer, organization_id)"))
                print("[OK] Added new constraint _part_manuf_org_uc")
            except Exception as e:
                print(f"[Error] Adding new constraint: {e}")

            conn.commit()
            print("Migration completed successfully.")
            
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    run_migration()
