import os
from sqlalchemy import create_engine, text

# Connect to the Docker Postgres via exposed port 5435
DB_URI = "postgresql://user:password@localhost:5435/dealer_dashboard"

engine = create_engine(DB_URI)

def run_migration():
    print(f"Connecting to {DB_URI}...")
    try:
        with engine.connect() as conn:
            print("--- Updating Organization Table ---")
            
            try:
                conn.execute(text("ALTER TABLE organization ADD COLUMN last_bridge_heartbeat TIMESTAMP"))
                print("[OK] Added last_bridge_heartbeat")
            except Exception as e:
                if "already exists" in str(e):
                    print(f"[SKIP] last_bridge_heartbeat (Column likely exists)")
                else:
                    print(f"[Error] last_bridge_heartbeat: {e}")

            print("--- Creating PartInventory Table ---")
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS part_inventory (
                id SERIAL PRIMARY KEY,
                organization_id INTEGER NOT NULL REFERENCES organization(id),
                part_number VARCHAR(100) NOT NULL,
                description VARCHAR(255),
                stock_on_hand INTEGER DEFAULT 0,
                bin_location VARCHAR(50),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT _part_org_uc UNIQUE (part_number, organization_id)
            );
            """
            try:
                conn.execute(text(create_table_sql))
                print("[OK] Created part_inventory table")
            except Exception as e:
                print(f"[Error] Creating part_inventory: {e}")

            conn.commit()
            print("Migration completed successfully.")
            
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    run_migration()
