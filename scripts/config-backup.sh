#!/bin/bash

# Orchestra Configuration Backup Script
# Backs up all configuration files, environment settings, and critical project files

set -euo pipefail  # Exit on any error

# Configuration
BACKUP_DIR="${BACKUP_DIR:-$(pwd)/backups/config}"
PROJECT_DIR="${PROJECT_DIR:-$(pwd)}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/orchestra_config_$TIMESTAMP.tar.gz"
RETENTION_DAYS=60  # Keep config backups longer than database backups
LOG_FILE="$BACKUP_DIR/config_backup.log"

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

# Files and directories to backup
get_backup_list() {
    cat << 'EOF'
# Core configuration files
.env
.env.example
pyproject.toml
poetry.lock
docker-compose.yml
Dockerfile
Makefile
bandit.yaml
codecov.yml

# GitHub workflows and CI/CD
.github/
.gitignore

# Documentation and architecture
docs/
README.md

# Scripts and utilities
scripts/

# BMad infrastructure (if exists)
.bmad-infrastructure-devops/
.bmad-core/

# Security logs and reports (recent ones)
logs/security/
backups/orchestra/backup.log

# Project structure files
src/__init__.py
tests/conftest.py

# IDE/Editor settings (if they exist)
.vscode/
.cursor/
.idea/

# Environment and deployment configs
temporal-config/
EOF
}

main() {
    log "=== Orchestra Configuration Backup Started ==="
    
    # Create backup directory
    if ! mkdir -p "$BACKUP_DIR"; then
        error_exit "Failed to create backup directory: $BACKUP_DIR"
    fi
    
    # Create temporary file list
    TEMP_LIST=$(mktemp)
    trap "rm -f $TEMP_LIST" EXIT
    
    # Build list of files to backup
    info "Building backup file list..."
    BACKUP_COUNT=0
    MISSING_COUNT=0
    
    while IFS= read -r line; do
        # Skip comments and empty lines
        [[ "$line" =~ ^#.*$ ]] && continue
        [[ -z "$line" ]] && continue
        
        # Check if file/directory exists
        if [[ -e "$PROJECT_DIR/$line" ]]; then
            echo "$line" >> "$TEMP_LIST"
            BACKUP_COUNT=$((BACKUP_COUNT + 1))
        else
            MISSING_COUNT=$((MISSING_COUNT + 1))
            log "SKIP: $line (not found)"
        fi
    done < <(get_backup_list)
    
    info "Found $BACKUP_COUNT files/directories to backup ($MISSING_COUNT not found)"
    
    if [[ $BACKUP_COUNT -eq 0 ]]; then
        warning "No files found to backup"
        success "Configuration backup completed (nothing to backup)"
        exit 0
    fi
    
    # Create backup archive
    info "Creating configuration backup archive..."
    if ! tar -czf "$BACKUP_FILE" -C "$PROJECT_DIR" -T "$TEMP_LIST" 2>/dev/null; then
        error_exit "Failed to create backup archive"
    fi
    
    # Verify backup was created
    if [[ ! -f "$BACKUP_FILE" ]]; then
        error_exit "Backup file was not created: $BACKUP_FILE"
    fi
    
    # Get backup file size and file count
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    FILE_COUNT=$(tar -tzf "$BACKUP_FILE" 2>/dev/null | wc -l)
    
    success "Configuration backup created: $BACKUP_FILE ($BACKUP_SIZE, $FILE_COUNT files)"
    
    # Create backup manifest
    MANIFEST_FILE="$BACKUP_DIR/orchestra_config_$TIMESTAMP.manifest"
    {
        echo "# Orchestra Configuration Backup Manifest"
        echo "# Created: $(date)"
        echo "# Backup File: $BACKUP_FILE"
        echo "# Files Count: $FILE_COUNT"
        echo "# Backup Size: $BACKUP_SIZE"
        echo
        echo "Files included in backup:"
        tar -tzf "$BACKUP_FILE" | sort
    } > "$MANIFEST_FILE"
    
    info "Backup manifest created: $MANIFEST_FILE"
    
    # Create latest symlinks for easy access
    LATEST_BACKUP="$BACKUP_DIR/orchestra_config_LATEST.tar.gz"
    LATEST_MANIFEST="$BACKUP_DIR/orchestra_config_LATEST.manifest"
    
    if ln -sf "$BACKUP_FILE" "$LATEST_BACKUP" 2>/dev/null; then
        success "Created latest backup symlink: $LATEST_BACKUP"
    else
        warning "Failed to create latest backup symlink"
    fi
    
    if ln -sf "$MANIFEST_FILE" "$LATEST_MANIFEST" 2>/dev/null; then
        success "Created latest manifest symlink: $LATEST_MANIFEST"
    else
        warning "Failed to create latest manifest symlink"
    fi
    
    # Clean up old backups
    info "Cleaning up backups older than $RETENTION_DAYS days..."
    DELETED_COUNT=0
    
    # Delete old backup files
    while IFS= read -r -d '' file; do
        rm -f "$file"
        DELETED_COUNT=$((DELETED_COUNT + 1))
    done < <(find "$BACKUP_DIR" -name "orchestra_config_*.tar.gz" -mtime +$RETENTION_DAYS -print0 2>/dev/null)
    
    # Delete old manifest files
    while IFS= read -r -d '' file; do
        rm -f "$file"
    done < <(find "$BACKUP_DIR" -name "orchestra_config_*.manifest" -mtime +$RETENTION_DAYS -print0 2>/dev/null)
    
    if [[ $DELETED_COUNT -gt 0 ]]; then
        success "Cleaned up $DELETED_COUNT old backup(s)"
    else
        info "No old backups to clean up"
    fi
    
    # Backup statistics
    TOTAL_BACKUPS=$(find "$BACKUP_DIR" -name "orchestra_config_*.tar.gz" | wc -l)
    TOTAL_SIZE=$(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1 || echo "unknown")
    
    log "Configuration Backup Statistics:"
    log "  - Total config backups: $TOTAL_BACKUPS"
    log "  - Total backup directory size: $TOTAL_SIZE"
    log "  - Latest backup: $BACKUP_FILE ($BACKUP_SIZE, $FILE_COUNT files)"
    
    success "Configuration backup completed successfully!"
    log "=== Orchestra Configuration Backup Completed ==="
}

# Health check mode
if [[ "${1:-}" == "--health-check" ]]; then
    # Quick health check of config backup system
    if [[ ! -d "$BACKUP_DIR" ]]; then
        echo "❌ Config backup directory does not exist: $BACKUP_DIR"
        exit 1
    fi
    
    LATEST_BACKUP=$(find "$BACKUP_DIR" -name "orchestra_config_*.tar.gz" -type f -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2-)
    
    if [[ -z "$LATEST_BACKUP" ]]; then
        echo "⚠️  No config backups found"
        exit 0
    fi
    
    BACKUP_AGE_HOURS=$(( ($(date +%s) - $(stat -c %Y "$LATEST_BACKUP" 2>/dev/null || stat -f %m "$LATEST_BACKUP")) / 3600 ))
    
    if [[ $BACKUP_AGE_HOURS -gt 169 ]]; then  # 7 days for config
        echo "❌ Latest config backup is $BACKUP_AGE_HOURS hours old (too old)"
        exit 1
    else
        echo "✅ Latest config backup is $BACKUP_AGE_HOURS hours old (OK)"
        
        # Test backup integrity
        if tar -tzf "$LATEST_BACKUP" >/dev/null 2>&1; then
            echo "✅ Config backup integrity check passed"
            exit 0
        else
            echo "❌ Config backup integrity check failed"
            exit 1
        fi
    fi
fi

# List mode
if [[ "${1:-}" == "--list" ]]; then
    echo "📋 Available Configuration Backups:"
    if [[ ! -d "$BACKUP_DIR" ]]; then
        echo "No backup directory found: $BACKUP_DIR"
        exit 1
    fi
    
    backups=($(find "$BACKUP_DIR" -name "orchestra_config_*.tar.gz" -type f | sort -r))
    
    if [[ ${#backups[@]} -eq 0 ]]; then
        echo "No config backups found"
        exit 0
    fi
    
    for backup in "${backups[@]}"; do
        basename_file=$(basename "$backup")
        size=$(du -h "$backup" | cut -f1)
        date=$(stat -c %y "$backup" 2>/dev/null || stat -f %Sm "$backup")
        file_count=$(tar -tzf "$backup" 2>/dev/null | wc -l)
        
        echo "  $basename_file ($size, $file_count files) - $date"
    done
    exit 0
fi

# Display help
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    cat << EOF
Orchestra Configuration Backup Script

Usage:
    $0                  Run configuration backup
    $0 --health-check   Check backup system health
    $0 --list          List available backups
    $0 --help          Show this help

Environment Variables:
    BACKUP_DIR         Backup directory (default: ./backups/config)
    PROJECT_DIR        Project directory (default: current directory)

The script will backup:
- Configuration files (.env, pyproject.toml, docker-compose.yml, etc.)
- GitHub workflows and CI/CD configurations
- Documentation and architecture files
- Scripts and utilities
- BMad infrastructure files (if present)
- Security logs and reports
- Project structure files

Backup Features:
- Compressed archive with timestamp
- Backup manifest with file listing
- Automatic cleanup of old backups (60+ days)
- Latest backup symlinks for easy access
- Integrity checking and verification

Recovery:
    Use standard tar command to restore:
    tar -xzf orchestra_config_TIMESTAMP.tar.gz
EOF
    exit 0
fi

# Run main backup
main
