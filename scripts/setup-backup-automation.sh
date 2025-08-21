#!/bin/bash

# Orchestra Backup Automation Setup
# Sets up automated daily backups via cron

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DB_BACKUP_SCRIPT="$SCRIPT_DIR/daily-backup.sh"
CONFIG_BACKUP_SCRIPT="$SCRIPT_DIR/config-backup.sh"

# Cron jobs
DB_CRON_COMMENT="# Orchestra AI Agent Database Backup"
DB_CRON_JOB="0 2 * * * cd $PROJECT_DIR && $DB_BACKUP_SCRIPT"

CONFIG_CRON_COMMENT="# Orchestra Configuration Backup"
CONFIG_CRON_JOB="0 3 * * 0 cd $PROJECT_DIR && $CONFIG_BACKUP_SCRIPT"  # Weekly on Sunday at 3 AM

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
success() { echo -e "${GREEN}✅ $1${NC}"; }
warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
error() { echo -e "${RED}❌ $1${NC}" >&2; }

main() {
    echo -e "${BLUE}🔄 Orchestra Backup Automation Setup${NC}"
    echo "====================================="
    echo
    
    # Verify backup scripts exist
    if [[ ! -x "$DB_BACKUP_SCRIPT" ]]; then
        error "Database backup script not found or not executable: $DB_BACKUP_SCRIPT"
        exit 1
    fi
    success "Database backup script found: $DB_BACKUP_SCRIPT"
    
    if [[ ! -x "$CONFIG_BACKUP_SCRIPT" ]]; then
        error "Configuration backup script not found or not executable: $CONFIG_BACKUP_SCRIPT"
        exit 1
    fi
    success "Configuration backup script found: $CONFIG_BACKUP_SCRIPT"
    
    # Create backup directories
    info "Creating backup directories..."
    mkdir -p "$PROJECT_DIR/backups/orchestra"
    mkdir -p "$PROJECT_DIR/backups/config"
    mkdir -p "$PROJECT_DIR/data"
    success "Backup directories created"
    
    # Test backup scripts
    info "Testing database backup script..."
    if "$DB_BACKUP_SCRIPT" --health-check; then
        success "Database backup script health check passed"
    else
        warning "Database backup script health check failed (expected if no database exists yet)"
    fi
    
    info "Testing configuration backup script..."
    if "$CONFIG_BACKUP_SCRIPT" --health-check; then
        success "Configuration backup script health check passed"
    else
        warning "Configuration backup script health check failed"
    fi
    
    # Check if cron jobs already exist
    info "Checking existing cron jobs..."
    EXISTING_DB_CRON=$(crontab -l 2>/dev/null | grep -F "$DB_BACKUP_SCRIPT" || echo "")
    EXISTING_CONFIG_CRON=$(crontab -l 2>/dev/null | grep -F "$CONFIG_BACKUP_SCRIPT" || echo "")
    
    if [[ -n "$EXISTING_DB_CRON" || -n "$EXISTING_CONFIG_CRON" ]]; then
        warning "Some backup cron jobs already exist"
        echo
        echo "Current backup cron jobs:"
        [[ -n "$EXISTING_DB_CRON" ]] && echo "  Database: $EXISTING_DB_CRON"
        [[ -n "$EXISTING_CONFIG_CRON" ]] && echo "  Config: $EXISTING_CONFIG_CRON"
        echo
        
        read -p "Do you want to update the existing cron jobs? (y/n): " update_cron
        if [[ "$update_cron" != "y" && "$update_cron" != "Y" ]]; then
            info "Skipping cron job setup"
            echo
            show_manual_setup
            exit 0
        fi
        
        # Remove existing cron jobs
        info "Removing existing backup cron jobs..."
        (crontab -l 2>/dev/null | grep -v -F "$DB_BACKUP_SCRIPT" | grep -v -F "$CONFIG_BACKUP_SCRIPT") | crontab -
    fi
    
    # Add new cron jobs
    info "Adding backup cron jobs..."
    (
        crontab -l 2>/dev/null
        echo "$DB_CRON_COMMENT"
        echo "$DB_CRON_JOB"
        echo "$CONFIG_CRON_COMMENT"  
        echo "$CONFIG_CRON_JOB"
    ) | crontab -
    success "Backup cron jobs added"
    
    # Verify cron jobs were added
    echo
    info "Verifying cron job installation..."
    if crontab -l 2>/dev/null | grep -F "$DB_BACKUP_SCRIPT" > /dev/null && 
       crontab -l 2>/dev/null | grep -F "$CONFIG_BACKUP_SCRIPT" > /dev/null; then
        success "Cron jobs successfully installed"
        echo
        echo "Installed cron jobs:"
        crontab -l 2>/dev/null | grep -A1 -F "Orchestra" | sed 's/^/  /'
    else
        error "Failed to install cron jobs"
        exit 1
    fi
    
    # Show summary
    echo
    echo -e "${GREEN}🎉 Backup automation setup complete!${NC}"
    echo
    echo "Summary:"
    echo "  - Database backups: Daily at 2:00 AM (30 day retention)"
    echo "  - Config backups: Weekly on Sunday at 3:00 AM (60 day retention)"
    echo "  - Database backups stored in: $PROJECT_DIR/backups/orchestra/"
    echo "  - Config backups stored in: $PROJECT_DIR/backups/config/"
    echo
    echo "Commands:"
    echo "  Database Backup:"
    echo "    - Test backup:       $DB_BACKUP_SCRIPT"
    echo "    - Check health:      $DB_BACKUP_SCRIPT --health-check"
    echo "    - Restore backup:    $SCRIPT_DIR/restore-backup.sh"
    echo "    - List backups:      $SCRIPT_DIR/restore-backup.sh --list"
    echo
    echo "  Configuration Backup:"
    echo "    - Test backup:       $CONFIG_BACKUP_SCRIPT"
    echo "    - Check health:      $CONFIG_BACKUP_SCRIPT --health-check"
    echo "    - List backups:      $CONFIG_BACKUP_SCRIPT --list"
    echo
    
    # Run initial backups
    read -p "Run initial backups now? (y/n): " run_backup
    if [[ "$run_backup" == "y" || "$run_backup" == "Y" ]]; then
        echo
        info "Running initial database backup..."
        if "$DB_BACKUP_SCRIPT"; then
            success "Initial database backup completed!"
        else
            warning "Initial database backup failed (normal if no database exists yet)"
        fi
        
        echo
        info "Running initial configuration backup..."
        if "$CONFIG_BACKUP_SCRIPT"; then
            success "Initial configuration backup completed!"
        else
            warning "Initial configuration backup failed"
        fi
    fi
    
    echo
    success "Backup automation is now active!"
}

show_manual_setup() {
    echo -e "${YELLOW}Manual Setup Instructions:${NC}"
    echo "========================="
    echo
    echo "To manually add the backup cron jobs:"
    echo "  1. Run: crontab -e"
    echo "  2. Add these lines:"
    echo "     $DB_CRON_JOB"
    echo "     $CONFIG_CRON_JOB"
    echo
    echo "To test the backup systems:"
    echo "  Database Backup:"
    echo "    - Run backup: $DB_BACKUP_SCRIPT"
    echo "    - Check health: $DB_BACKUP_SCRIPT --health-check"
    echo "    - List backups: $SCRIPT_DIR/restore-backup.sh --list"
    echo
    echo "  Configuration Backup:"
    echo "    - Run backup: $CONFIG_BACKUP_SCRIPT"
    echo "    - Check health: $CONFIG_BACKUP_SCRIPT --health-check"
    echo "    - List backups: $CONFIG_BACKUP_SCRIPT --list"
    echo
}

# Check if running on macOS (different cron behavior)
if [[ "$(uname)" == "Darwin" ]]; then
    warning "Running on macOS - you may need to grant Terminal/cron permission to access files"
    echo "If you encounter permission issues, go to:"
    echo "System Preferences > Security & Privacy > Privacy > Full Disk Access"
    echo "And add Terminal or your terminal application."
    echo
fi

# Check for command line arguments
case "${1:-}" in
    --help|-h)
        cat << EOF
Orchestra Backup Automation Setup

This script sets up automated daily backups for the Orchestra database.

Usage:
    $0              Setup automated backups (interactive)
    $0 --manual     Show manual setup instructions
    $0 --help       Show this help

The script will:
1. Verify backup scripts are available
2. Create necessary directories  
3. Test the backup system
4. Add a cron job for daily backups at 2:00 AM
5. Run an optional initial backup

Manual Commands:
    $BACKUP_SCRIPT                    # Run backup now
    $BACKUP_SCRIPT --health-check     # Check backup system
    $SCRIPT_DIR/restore-backup.sh     # Restore from backup
EOF
        exit 0
        ;;
    --manual)
        show_manual_setup
        exit 0
        ;;
    *)
        # Run main setup
        main
        ;;
esac
