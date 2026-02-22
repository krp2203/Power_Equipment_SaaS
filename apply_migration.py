import os
from sqlalchemy import create_engine, text

# Connect to the Docker Postgres via exposed port 5435
# Standard user/pass from docker-compose.yml
DB_URI = "postgresql://user:password@localhost:5435/dealer_dashboard"

engine = create_engine(DB_URI)

def run_migration():
    print(f"Connecting to {DB_URI}...")
    try:
        with engine.connect() as conn:
            print("--- Updating Organization Table ---")
            
            # Helper to safely add column
            def add_col(table, col_def):
                try:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col_def}"))
                    print(f"[OK] Added {col_def}")
                except Exception as e:
                    if "already exists" in str(e):
                        print(f"[SKIP] {col_def} (Column likely exists)")
                    else:
                        print(f"[Error] {e}")

            add_col("organization", "slug VARCHAR(50)")
            add_col("organization", "ari_dealer_id VARCHAR(50)")
            add_col("organization", "pos_provider VARCHAR(50) DEFAULT 'none'")
            add_col("organization", "pos_bridge_key VARCHAR(100)")
            add_col("organization", "facebook_page_id VARCHAR(100)")
            add_col("organization", "facebook_access_token TEXT")
            
            # Try to add index for slug
            try:
                conn.execute(text("CREATE UNIQUE INDEX ix_organization_slug ON organization (slug)"))
                print("[OK] Created index ix_organization_slug")
            except Exception as e:
                 print(f"[SKIP] Index ix_organization_slug: {e}")

            print("--- Updating Unit Table ---")
            add_col("unit", "is_owned BOOLEAN DEFAULT FALSE")
            add_col("unit", "display_on_web BOOLEAN DEFAULT FALSE")
            add_col("unit", "push_to_facebook BOOLEAN DEFAULT FALSE")
            
            print("--- Data Patching ---")
            # Set default slug for Org 1 if needed
            try:
                result = conn.execute(text("UPDATE organization SET slug='demo' WHERE id=1 AND slug IS NULL"))
                if result.rowcount > 0:
                     print("[OK] Set slug='demo' for Organization #1")
            except Exception as e:
                print(f"[Error] Patching Org 1: {e}")

            conn.commit()
            print("Migration completed successfully.")
            
    except Exception as e:
        print(f"Connection failed: {e}")
        print("Please ensure 'docker compose up db' is running and port 5435 is mapped.")

if __name__ == "__main__":
    run_migration()
