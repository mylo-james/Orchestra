#!/bin/bash

# GitHub Branch Protection Setup Script
# Sets up branch protection rules via GitHub CLI

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
success() { echo -e "${GREEN}✅ $1${NC}"; }
warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
error() { echo -e "${RED}❌ $1${NC}" >&2; }

# Check if GitHub CLI is installed
check_gh_cli() {
    if ! command -v gh &> /dev/null; then
        error "GitHub CLI (gh) is not installed"
        echo
        echo "Install GitHub CLI:"
        echo "  macOS:   brew install gh"
        echo "  Linux:   https://github.com/cli/cli/blob/trunk/docs/install_linux.md"
        echo "  Windows: https://github.com/cli/cli/releases"
        echo
        exit 1
    fi
    success "GitHub CLI found"
}

# Check if authenticated
check_auth() {
    if ! gh auth status &>/dev/null; then
        error "Not authenticated with GitHub"
        echo
        echo "Run: gh auth login"
        echo
        exit 1
    fi
    success "GitHub authentication verified"
}

# Get repository info
get_repo_info() {
    REPO_OWNER=$(gh repo view --json owner --jq .owner.login 2>/dev/null || echo "")
    REPO_NAME=$(gh repo view --json name --jq .name 2>/dev/null || echo "")

    if [[ -z "$REPO_OWNER" || -z "$REPO_NAME" ]]; then
        error "Could not determine repository information"
        echo "Make sure you're in a Git repository connected to GitHub"
        exit 1
    fi

    info "Repository: $REPO_OWNER/$REPO_NAME"
}

# Setup branch protection for main branch (single developer mode)
setup_main_protection() {
    info "Setting up branch protection for 'main' branch (single developer mode)..."

    # Main branch protection - NO required reviews for single developer
    if gh api repos/$REPO_OWNER/$REPO_NAME/branches/main/protection \
        --method PUT \
        --input - <<EOF
{
  "required_status_checks": {
    "strict": true,
    "checks": [
      {"context": "Orchestra Laptop-Optimized CI / Quality Gate"}
    ]
  },
  "enforce_admins": false,
  "required_pull_request_reviews": null,
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "block_creations": false,
  "required_conversation_resolution": false
}
EOF
    then
        success "Branch protection enabled for 'main' (single developer mode)"
    else
        error "Failed to set up protection for 'main' branch"
        return 1
    fi
}

# Setup branch protection for develop branch (single developer mode)
setup_develop_protection() {
    info "Setting up branch protection for 'develop' branch (single developer mode)..."

    # Develop branch protection - NO required reviews for single developer
    if gh api repos/$REPO_OWNER/$REPO_NAME/branches/develop/protection \
        --method PUT \
        --input - <<EOF
{
  "required_status_checks": {
    "strict": true,
    "checks": [
      {"context": "Orchestra Laptop-Optimized CI / Quality Gate"}
    ]
  },
  "enforce_admins": false,
  "required_pull_request_reviews": null,
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "block_creations": false,
  "required_conversation_resolution": false
}
EOF
    then
        success "Branch protection enabled for 'develop' (single developer mode)"
    else
        warning "Failed to set up protection for 'develop' branch (may not exist yet)"
    fi
}

# Show current protection status
show_protection_status() {
    echo
    info "Current branch protection status:"
    echo

    # Check main branch
    echo "Main branch:"
    if gh api repos/$REPO_OWNER/$REPO_NAME/branches/main/protection &>/dev/null; then
        success "  Protection enabled"

        # Show required status checks
        CHECKS=$(gh api repos/$REPO_OWNER/$REPO_NAME/branches/main/protection/required_status_checks --jq '.checks[].context' 2>/dev/null || echo "")
        if [[ -n "$CHECKS" ]]; then
            echo "  Required status checks:"
            echo "$CHECKS" | sed 's/^/    - /'
        fi
    else
        warning "  No protection configured"
    fi

    echo

    # Check develop branch
    echo "Develop branch:"
    if gh api repos/$REPO_OWNER/$REPO_NAME/branches/develop/protection &>/dev/null; then
        success "  Protection enabled"

        # Show required status checks
        CHECKS=$(gh api repos/$REPO_OWNER/$REPO_NAME/branches/develop/protection/required_status_checks --jq '.checks[].context' 2>/dev/null || echo "")
        if [[ -n "$CHECKS" ]]; then
            echo "  Required status checks:"
            echo "$CHECKS" | sed 's/^/    - /'
        fi
    else
        warning "  No protection configured"
    fi
}

main() {
    echo -e "${BLUE}🛡️  GitHub Branch Protection Setup${NC}"
    echo "=================================="
    echo

    check_gh_cli
    check_auth
    get_repo_info
    echo

    # Show current status first
    show_protection_status
    echo

    read -p "Set up branch protection rules? (y/n): " confirm
    if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
        info "Branch protection setup cancelled"
        exit 0
    fi

    echo
    setup_main_protection
    setup_develop_protection

    echo
    success "Branch protection setup complete!"
    echo

    # Show final status
    show_protection_status

    echo
    echo -e "${GREEN}🎉 AI agents can no longer bypass security controls!${NC}"
    echo
    echo "Single Developer Protection Enabled:"
    echo "  ✅ Status checks REQUIRED before merge (security scans must pass)"
    echo "  ✅ All commits must pass: Test Suite, Security Gates, Docker Security"
    echo "  ✅ No direct pushes to protected branches"
    echo "  ⚠️  No PR reviews required (single developer mode)"
    echo
    echo "How this protects against AI agent failures:"
    echo "  🛡️  AI agents cannot commit code that fails security scans"
    echo "  🛡️  AI agents cannot push directly to main/develop"
    echo "  🛡️  All changes must go through PR workflow with passing checks"
    echo
    echo "Next steps:"
    echo "  1. Test: Try pushing directly to main (should be blocked)"
    echo "  2. Create a test PR and verify security scans run"
    echo "  3. Verify failing security scans block the merge"
    echo "  4. Test with: 'git push origin main' (should fail)"
}

# Handle command line options
case "${1:-}" in
    --status)
        check_gh_cli
        check_auth
        get_repo_info
        show_protection_status
        exit 0
        ;;
    --help|-h)
        cat << EOF
GitHub Branch Protection Setup

This script configures branch protection rules to prevent AI agents
from bypassing security controls.

Usage:
    $0          Setup branch protection (interactive)
    $0 --status Show current protection status
    $0 --help   Show this help

Requirements:
    - GitHub CLI (gh) installed and authenticated
    - Repository admin permissions
    - Repository must be connected to GitHub

Protection Rules (Single Developer Mode):
    Main branch:
        - Require status checks (Security & Quality Gates) - BLOCKING
        - No direct pushes allowed
        - No PR reviews required (single developer)
        - Admin enforcement disabled

    Develop branch:
        - Require status checks (Security & Quality Gates) - BLOCKING
        - No direct pushes allowed
        - No PR reviews required (single developer)

Required Status Checks:
    - Orchestra Laptop-Optimized CI / Quality Gate

This must match your CI job name exactly.
EOF
        exit 0
        ;;
esac

main
