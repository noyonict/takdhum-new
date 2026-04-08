#!/bin/bash
# =============================================================================
# Takdhum MySQL Daily Backup Script
# Runs via PythonAnywhere Scheduled Tasks at 2:00 AM every day
# Keeps backups for the last 7 days, then deletes older ones
# =============================================================================

BACKUP_DIR="/home/romanahme/db_backups"
DB_NAME="romanahme\$takdhum4"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/takdhum_backup_${TIMESTAMP}.sql.gz"

echo "------------------------------------------------------------"
echo "[$(date)] Starting backup..."

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Dump and compress
mysqldump \
  --defaults-file=/home/romanahme/.my.cnf \
  --no-tablespaces \
  --column-statistics=0 \
  --single-transaction \
  "$DB_NAME" | gzip > "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    SIZE=$(du -sh "$BACKUP_FILE" | cut -f1)
    echo "[$(date)] Backup successful: $BACKUP_FILE ($SIZE)"
else
    echo "[$(date)] ERROR: Backup failed!"
    exit 1
fi

# Delete backups older than 7 days
DELETED=$(find "$BACKUP_DIR" -name "takdhum_backup_*.sql.gz" -mtime +7 -print -delete)
if [ -n "$DELETED" ]; then
    echo "[$(date)] Deleted old backups:"
    echo "$DELETED"
else
    echo "[$(date)] No old backups to delete."
fi

echo "[$(date)] Done."
echo "------------------------------------------------------------"
