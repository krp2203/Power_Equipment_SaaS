#!/bin/bash

# Configuration
BACKUP_DIR="/root/power_equip_saas/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/db_backup_$TIMESTAMP.sql"
LATEST_LINK="$BACKUP_DIR/latest_backup.sql"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

echo "🚀 Starting database backup..."

# Perform pg_dump inside the docker container
# Using -f to specify output file inside the mount if we had one, 
# but we'll stream it to host for safety.
docker compose -f docker-compose.quick.yml exec db pg_dump -U user -d dealer_dashboard > "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "✅ Backup successful! Saved to: $BACKUP_FILE"
    
    # Update 'latest' symlink
    ln -sf "$BACKUP_FILE" "$LATEST_LINK"
    echo "🔗 Updated symlink: $LATEST_LINK"
    
    # Optional: Keep only last 7 days of backups
    find "$BACKUP_DIR" -name "db_backup_*.sql" -mtime +7 -delete
    echo "🧹 Cleaned up backups older than 7 days."
else
    echo "❌ Backup FAILED!"
    exit 1
fi
