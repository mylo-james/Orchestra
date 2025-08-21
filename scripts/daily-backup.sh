#!/bin/bash

# Orchestra Daily Backup Script
# Backs up SQLite database with integrity checking and retention management

set -euo pipefail  # Exit on any error

# Configuration
BACKUP_DIR="${BACKUP_DIR:-$(pwd)/backups/orchestra}"
DB_PATH="${DB_PATH:-$(pwd)/data/orchestra.db}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/orchestra_backup_$TIMESTAMP.db"
RETENTION_DAYS=30
LOG_FILE="$BACKUP_DIR/backup.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Error handling
error_exit() {
    echo -e "${RED}❌ ERROR: $1${NC}" >&2
    log "ERROR: $1"
    exit 1
}

# Success logging
success() {
    echo -e "${GREEN}✅ $1${NC}"
    log "SUCCESS: $1"
}

# Warning logging
warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    log "WARNING: $1"
}

main() {
    log "=== Orchestra Database Backup Started ==="

    # Create backup directory
    if ! mkdir -p "$BACKUP_DIR"; then
        error_exit "Failed to create backup directory: $BACKUP_DIR"
    fi

    # Check if database exists
    if [[ ! -f "$DB_PATH" ]]; then
        warning "Database file not found: $DB_PATH"
        log "Creating empty backup directory structure"
        success "Backup directory prepared (no database to backup yet)"
        exit 0
    fi

    # Check database integrity before backup
    log "Checking source database integrity..."
    if ! sqlite3 "$DB_PATH" "PRAGMA integrity_check;" > /dev/null 2>&1; then
        error_exit "Source database integrity check failed: $DB_PATH"
    fi
    success "Source database integrity verified"

    # Perform backup using SQLite backup command
    log "Creating backup: $BACKUP_FILE"
    if ! sqlite3 "$DB_PATH" ".backup $BACKUP_FILE"; then
        error_exit "Database backup failed"
    fi

    # Verify backup integrity
    log "Verifying backup integrity..."
    if ! sqlite3 "$BACKUP_FILE" "PRAGMA integrity_check;" > /dev/null 2>&1; then
        # Remove corrupted backup
        rm -f "$BACKUP_FILE"
        error_exit "Backup integrity check failed - backup deleted"
    fi
    success "Backup integrity verified"

    # Get backup file size
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    success "Database backup completed: $BACKUP_FILE ($BACKUP_SIZE)"

    # Clean up old backups
    log "Cleaning up backups older than $RETENTION_DAYS days..."
    DELETED_COUNT=$(find "$BACKUP_DIR" -name "orchestra_backup_*.db" -mtime +$RETENTION_DAYS -delete -print | wc -l)
    if [[ $DELETED_COUNT -gt 0 ]]; then
        success "Cleaned up $DELETED_COUNT old backup(s)"
    else
        log "No old backups to clean up"
    fi

    # Create latest symlink for easy access
    LATEST_LINK="$BACKUP_DIR/orchestra_backup_LATEST.db"
    if ln -sf "$BACKUP_FILE" "$LATEST_LINK" 2>/dev/null; then
        success "Created latest backup symlink: $LATEST_LINK"
    else
        warning "Failed to create latest backup symlink"
    fi

    # Backup statistics
    TOTAL_BACKUPS=$(find "$BACKUP_DIR" -name "orchestra_backup_*.db" | wc -l)
    TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)

    log "Backup Statistics:"
    log "  - Total backups: $TOTAL_BACKUPS"
    log "  - Total backup size: $TOTAL_SIZE"
    log "  - Latest backup: $BACKUP_FILE ($BACKUP_SIZE)"

    success "Daily backup completed successfully!"
    log "=== Orchestra Database Backup Completed ==="
}

# Health check mode
if [[ "${1:-}" == "--health-check" ]]; then
    # Quick health check of backup system
    if [[ ! -d "$BACKUP_DIR" ]]; then
        echo "❌ Backup directory does not exist: $BACKUP_DIR"
        exit 1
    fi

    LATEST_BACKUP=$(find "$BACKUP_DIR" -name "orchestra_backup_*.db" -type f -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2-)

    if [[ -z "$LATEST_BACKUP" ]]; then
        echo "⚠️  No backups found"
        exit 0
    fi

    BACKUP_AGE_HOURS=$(( ($(date +%s) - $(stat -c %Y "$LATEST_BACKUP")) / 3600 ))

    if [[ $BACKUP_AGE_HOURS -gt 25 ]]; then
        echo "❌ Latest backup is $BACKUP_AGE_HOURS hours old (too old)"
        exit 1
    else
        echo "✅ Latest backup is $BACKUP_AGE_HOURS hours old (OK)"
        exit 0
    fi
fi

# Display help
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    cat << EOF
Orchestra Database Backup Script

Usage:
    $0                  Run daily backup
    $0 --health-check   Check backup system health
    $0 --help          Show this help

Environment Variables:
    BACKUP_DIR         Backup directory (default: ./backups/orchestra)
    DB_PATH           Database file path (default: ./data/orchestra.db)

The script will:
1. Create backup directory if it doesn't exist
2. Check source database integrity
3. Create SQLite backup with timestamp
4. Verify backup integrity
5. Clean up old backups (30+ days)
6. Create 'LATEST' symlink for easy access
EOF
    exit 0
fi

# Run main backup
main
