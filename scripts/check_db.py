
import os
from sqlalchemy import create_engine, inspect

# Get DB_URI from env or use the one from docker-compose (needs to be adapted for localhost if running from outside)
# Since I'm in the container or on the host, I'll try to connect. 
# Identifying how to connect: 
# The user is on 'linux', likely the host machine.
# The app connects via 'postgresql://user:password@db:5432/dealer_dashboard' (from docker-compose).
# 'db' hostname only works inside docker network.
# From host, port 5435 is mapped to 5432.
# So I should use: postgresql://user:password@localhost:5435/dealer_dashboard

DB_URI = 'postgresql://user:password@127.0.0.1:5435/dealer_dashboard'

def check_schema():
    try:
        engine = create_engine(DB_URI)
        inspector = inspect(engine)
        
        print("Checking Organization columns:")
        columns = [c['name'] for c in inspector.get_columns('organization')]
        print(f"Columns: {columns}")
        print(f"Has modules? {'modules' in columns}")
        print(f"Has theme_config? {'theme_config' in columns}")

        print("\nChecking Dealer columns:")
        d_columns = inspector.get_columns('dealer')
        for c in d_columns:
            if c['name'] == 'labor_rate':
                print(f"labor_rate type: {c['type']}")
        
        labor_rate_names = [c['name'] for c in d_columns]
        print(f"Has labor_rate? {'labor_rate' in labor_rate_names}")

    except Exception as e:
        print(f"Error connecting: {e}")

if __name__ == "__main__":
    check_schema()
