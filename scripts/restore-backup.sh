#!/bin/bash

# Orchestra Database Restore Script
# Restores SQLite database from backup with safety checks

set -euo pipefail  # Exit on any error

# Configuration
BACKUP_DIR="${BACKUP_DIR:-$(pwd)/backups/orchestra}"
DB_PATH="${DB_PATH:-$(pwd)/data/orchestra.db}"
LOG_FILE="$BACKUP_DIR/restore.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# Info logging
info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
    log "INFO: $1"
}

# List available backups
list_backups() {
    echo -e "${BLUE}Available Backups:${NC}"
    if [[ ! -d "$BACKUP_DIR" ]]; then
        echo "No backup directory found: $BACKUP_DIR"
        return 1
    fi

    local backups=($(find "$BACKUP_DIR" -name "orchestra_backup_*.db" -type f | sort -r))

    if [[ ${#backups[@]} -eq 0 ]]; then
        echo "No backups found in $BACKUP_DIR"
        return 1
    fi

    echo
    for i in "${!backups[@]}"; do
        local backup="${backups[$i]}"
        local basename=$(basename "$backup")
        local size=$(du -h "$backup" | cut -f1)
        local date=$(stat -c %y "$backup" | cut -d' ' -f1,2 | cut -d'.' -f1)
        printf "%2d. %s (%s) - %s\n" $((i+1)) "$basename" "$size" "$date"
    done
    echo
}

# Restore from backup
restore_backup() {
    local backup_file="$1"
    local create_backup_of_current="${2:-true}"

    log "=== Orchestra Database Restore Started ==="

    # Verify backup file exists and is readable
    if [[ ! -f "$backup_file" ]]; then
        error_exit "Backup file not found: $backup_file"
    fi

    if [[ ! -r "$backup_file" ]]; then
        error_exit "Backup file not readable: $backup_file"
    fi

    # Verify backup integrity
    info "Verifying backup integrity..."
    if ! sqlite3 "$backup_file" "PRAGMA integrity_check;" > /dev/null 2>&1; then
        error_exit "Backup integrity check failed: $backup_file"
    fi
    success "Backup integrity verified"

    # Create data directory if it doesn't exist
    mkdir -p "$(dirname "$DB_PATH")"

    # Backup current database if it exists
    if [[ -f "$DB_PATH" && "$create_backup_of_current" == "true" ]]; then
        local current_backup="$BACKUP_DIR/pre_restore_backup_$(date +%Y%m%d_%H%M%S).db"
        info "Creating backup of current database: $current_backup"

        if sqlite3 "$DB_PATH" ".backup $current_backup"; then
            success "Current database backed up to: $current_backup"
        else
            warning "Failed to backup current database - continuing with restore"
        fi
    fi

    # Perform restore
    info "Restoring database from: $backup_file"
    if ! cp "$backup_file" "$DB_PATH"; then
        error_exit "Failed to restore database"
    fi

    # Verify restored database
    info "Verifying restored database..."
    if ! sqlite3 "$DB_PATH" "PRAGMA integrity_check;" > /dev/null 2>&1; then
        error_exit "Restored database integrity check failed"
    fi
    success "Restored database integrity verified"

    # Get restored database info
    local table_count=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM sqlite_master WHERE type='table';" 2>/dev/null || echo "0")
    local db_size=$(du -h "$DB_PATH" | cut -f1)

    success "Database restore completed successfully!"
    info "Restored database info:"
    info "  - File: $DB_PATH"
    info "  - Size: $db_size"
    info "  - Tables: $table_count"

    log "=== Orchestra Database Restore Completed ==="
}

# Interactive mode
interactive_restore() {
    echo -e "${BLUE}🔄 Orchestra Database Restore${NC}"
    echo "=================================="
    echo

    list_backups || exit 1

    echo -e "${YELLOW}Select a backup to restore (or 'q' to quit):${NC}"
    read -p "Enter backup number: " selection

    if [[ "$selection" == "q" || "$selection" == "Q" ]]; then
        echo "Restore cancelled"
        exit 0
    fi

    # Validate selection
    if ! [[ "$selection" =~ ^[0-9]+$ ]]; then
        error_exit "Invalid selection: $selection"
    fi

    local backups=($(find "$BACKUP_DIR" -name "orchestra_backup_*.db" -type f | sort -r))
    local backup_index=$((selection - 1))

    if [[ $backup_index -lt 0 || $backup_index -ge ${#backups[@]} ]]; then
        error_exit "Invalid backup selection: $selection"
    fi

    local selected_backup="${backups[$backup_index]}"

    # Confirmation
    echo
    echo -e "${YELLOW}⚠️  This will replace the current database with:${NC}"
    echo "   $(basename "$selected_backup")"
    echo

    if [[ -f "$DB_PATH" ]]; then
        echo -e "${YELLOW}⚠️  Current database will be backed up before restore${NC}"
        echo
    fi

    read -p "Are you sure you want to proceed? (yes/no): " confirmation

    if [[ "$confirmation" != "yes" ]]; then
        echo "Restore cancelled"
        exit 0
    fi

    restore_backup "$selected_backup"
}

# Show help
show_help() {
    cat << EOF
Orchestra Database Restore Script

Usage:
    $0                      Interactive restore (list and select backup)
    $0 <backup_file>        Restore from specific backup file
    $0 --latest            Restore from latest backup
    $0 --list              List available backups
    $0 --help              Show this help

Options:
    --no-backup-current     Don't backup current database before restore

Environment Variables:
    BACKUP_DIR             Backup directory (default: ./backups/orchestra)
    DB_PATH               Database file path (default: ./data/orchestra.db)

Examples:
    $0                                    # Interactive mode
    $0 --latest                          # Restore latest backup
    $0 orchestra_backup_20231201_120000.db  # Restore specific backup
    $0 --list                            # List available backups

Safety Features:
- Verifies backup integrity before restore
- Creates backup of current database (unless --no-backup-current)
- Verifies restored database integrity
- Detailed logging of all operations
EOF
}

# Parse arguments
CREATE_BACKUP_OF_CURRENT="true"
BACKUP_FILE=""
MODE="interactive"

while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            show_help
            exit 0
            ;;
        --list)
            list_backups
            exit $?
            ;;
        --latest)
            BACKUP_FILE="$BACKUP_DIR/orchestra_backup_LATEST.db"
            MODE="restore"
            shift
            ;;
        --no-backup-current)
            CREATE_BACKUP_OF_CURRENT="false"
            shift
            ;;
        -*)
            error_exit "Unknown option: $1"
            ;;
        *)
            # If it contains a path separator or ends in .db, treat as backup file
            if [[ "$1" == */* || "$1" == *.db ]]; then
                BACKUP_FILE="$1"
                MODE="restore"
            else
                error_exit "Unknown argument: $1"
            fi
            shift
            ;;
    esac
done

# Execute based on mode
case $MODE in
    interactive)
        interactive_restore
        ;;
    restore)
        if [[ -z "$BACKUP_FILE" ]]; then
            error_exit "No backup file specified"
        fi

        # Handle relative paths
        if [[ "$BACKUP_FILE" != /* && "$BACKUP_FILE" != "$BACKUP_DIR"/* ]]; then
            BACKUP_FILE="$BACKUP_DIR/$BACKUP_FILE"
        fi

        restore_backup "$BACKUP_FILE" "$CREATE_BACKUP_OF_CURRENT"
        ;;
    *)
        error_exit "Invalid mode: $MODE"
        ;;
esac
