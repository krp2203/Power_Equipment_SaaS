#!/bin/bash

# Configuration
BACKUP_DIR="/root/power_equip_saas/backups"
LATEST_LINK="$BACKUP_DIR/latest_backup.sql"

# Check if a file was provided as argument, otherwise use latest
if [ -z "$1" ]; then
    if [ -f "$LATEST_LINK" ]; then
        RESTORE_FILE="$LATEST_LINK"
    else
        echo "❌ No backup file specified and no 'latest_backup.sql' found."
        echo "Usage: $0 [path_to_backup.sql]"
        exit 1
    fi
else
    RESTORE_FILE="$1"
fi

if [ ! -f "$RESTORE_FILE" ]; then
    echo "❌ Backup file not found: $RESTORE_FILE"
    exit 1
fi

echo "⚠️  WARNING: This will overwrite the current database!"
read -p "Are you sure you want to proceed? (y/N) " confirm

if [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]]; then
    echo "🔄 Restoring database from: $RESTORE_FILE..."
    
    # Drop and recreate DB to ensure a clean slate (optional but safer)
    # docker compose -f docker-compose.quick.yml exec db dropdb -U user dealer_dashboard --if-exists
    # docker compose -f docker-compose.quick.yml exec db createdb -U user dealer_dashboard
    
    # Pipe the SQL file into psql
    cat "$RESTORE_FILE" | docker compose -f docker-compose.quick.yml exec -T db psql -U user -d dealer_dashboard
    
    if [ $? -eq 0 ]; then
        echo "✅ Restoration successful!"
    else
        echo "❌ Restoration FAILED!"
        exit 1
    fi
else
    echo "❌ Restoration cancelled."
fi
