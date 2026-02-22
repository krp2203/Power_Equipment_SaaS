from app import create_app, db
from sqlalchemy import text

def migrate():
    app = create_app()
    with app.app_context():
        print("Starting Inventory Migration...")
        
        # 1. Create new table UnitImage
        # db.create_all() only creates tables that don't satisfy, but it might be safer to be explicit or trust create_all
        try:
            db.create_all() # This should create unit_image
            print("Created all missing tables (including unit_image).")
        except Exception as e:
            print(f"Error creating tables: {e}")

        # 2. Add columns to Unit table
        # We use raw SQL because migration tools (alembic) might not be fully configured/synced
        columns_to_add = [
            ("price", "NUMERIC(10, 2)"),
            ("year", "INTEGER"),
            ("condition", "VARCHAR(50) DEFAULT 'New'"),
            ("status", "VARCHAR(50) DEFAULT 'Available'"),
            ("description", "TEXT"),
            ("is_inventory", "BOOLEAN DEFAULT FALSE")
        ]

        with db.engine.connect() as conn:
            for col_name, col_type in columns_to_add:
                try:
                    conn.execute(text(f"ALTER TABLE unit ADD COLUMN {col_name} {col_type}"))
                    print(f"Added column: {col_name}")
                except Exception as e:
                    if "already exists" in str(e):
                        print(f"Column {col_name} already exists.")
                    else:
                        print(f"Error adding {col_name}: {e}")
            conn.commit()
            
        print("Inventory Migration Complete.")

if __name__ == "__main__":
    migrate()
