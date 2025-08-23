#!/usr/bin/env python3
"""
Security Setup Script for Orchestra
Initializes security tools and configurations.
"""

import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


# ANSI colors for output
class Colors:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    END = "\033[0m"


def print_error(msg: str) -> None:
    print(f"{Colors.RED}❌ ERROR: {msg}{Colors.END}", file=sys.stderr)


def print_success(msg: str) -> None:
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")


def print_warning(msg: str) -> None:
    print(f"{Colors.YELLOW}⚠️  WARNING: {msg}{Colors.END}")


def print_info(msg: str) -> None:
    print(f"{Colors.CYAN}ℹ️  {msg}{Colors.END}")


def print_header(msg: str) -> None:
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{msg.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")


def run_command(
    cmd: List[str], description: str, check: bool = True
) -> Tuple[bool, str]:
    """Run a command and return success status and output."""
    print_info(f"Running: {description}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=check)

        if result.returncode == 0:
            print_success(f"{description} completed")
            return True, result.stdout
        else:
            print_error(f"{description} failed")
            if result.stderr:
                print(f"Error: {result.stderr}")
            return False, result.stderr

    except subprocess.CalledProcessError as e:
        print_error(f"{description} failed: {e}")
        return False, str(e)
    except FileNotFoundError:
        print_error(f"Command not found: {cmd[0]}")
        return False, f"Command not found: {cmd[0]}"


def setup_pre_commit():
    """Set up and install pre-commit hooks."""
    print_header("Pre-commit Setup")

    # Install pre-commit hooks
    success, _ = run_command(
        ["poetry", "run", "pre-commit", "install"], "Install pre-commit hooks"
    )

    if success:
        print_success("Pre-commit hooks installed")

        # Run pre-commit on all files to initialize
        print_info("Running pre-commit on all files (initial setup)...")
        run_command(
            ["poetry", "run", "pre-commit", "run", "--all-files"],
            "Initial pre-commit run",
            check=False,  # Don't fail if there are issues to fix
        )

    return success


def setup_secrets_baseline():
    """Set up secrets detection baseline."""
    print_header("Secrets Detection Setup")

    baseline_path = Path(".secrets.baseline")

    if not baseline_path.exists():
        print_warning("Secrets baseline not found, creating initial baseline...")

        # Create initial baseline
        success, _ = run_command(
            [
                "poetry",
                "run",
                "detect-secrets",
                "scan",
                "--baseline",
                ".secrets.baseline",
            ],
            "Create secrets baseline",
        )

        if success:
            print_success("Secrets baseline created")
        return success
    else:
        print_info("Secrets baseline already exists")

        # Update baseline with any new files
        success, _ = run_command(
            [
                "poetry",
                "run",
                "detect-secrets",
                "scan",
                "--baseline",
                ".secrets.baseline",
                "--update",
            ],
            "Update secrets baseline",
            check=False,
        )

        return True


def setup_git_hooks():
    """Set up additional Git hooks for security."""
    print_header("Git Hooks Setup")

    git_hooks_dir = Path(".git/hooks")

    if not git_hooks_dir.exists():
        print_warning("Git hooks directory not found")
        return False

    # Create pre-push hook to run security checks
    pre_push_hook = git_hooks_dir / "pre-push"

    hook_content = """#!/bin/bash
# Pre-push hook: Run security checks before pushing

set -e

echo "🔒 Running security checks before push..."

# Run bandit security scan
echo "Running Bandit security scan..."
if ! poetry run bandit -r src/ -c bandit.yaml --quiet; then
    echo "❌ Bandit security scan failed"
    exit 1
fi

# Run safety check for vulnerable dependencies
echo "Running Safety dependency check..."
if ! poetry run safety check --short-report; then
    echo "❌ Safety check found vulnerabilities"
    exit 1
fi

# Run secrets detection
echo "Running secrets detection..."
if ! poetry run detect-secrets scan --baseline .secrets.baseline --force-use-all-plugins; then
    echo "❌ Secrets detected"
    exit 1
fi

echo "✅ Security checks passed"
exit 0
"""

    try:
        pre_push_hook.write_text(hook_content)
        pre_push_hook.chmod(0o755)  # Make executable
        print_success("Pre-push security hook installed")
        return True
    except Exception as e:
        print_error(f"Failed to create pre-push hook: {e}")
        return False


def setup_security_directories():
    """Create necessary security-related directories."""
    print_header("Security Directories Setup")

    directories = [
        "logs/security",
        "backups/security",
        ".security",
    ]

    for directory in directories:
        dir_path = Path(directory)
        dir_path.mkdir(parents=True, exist_ok=True)
        print_info(f"Created directory: {directory}")

        # Add .gitkeep to ensure directories are tracked
        gitkeep = dir_path / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()

    print_success("Security directories created")
    return True


def validate_security_tools():
    """Validate that security tools are properly installed."""
    print_header("Security Tools Validation")

    tools = [
        (["poetry", "run", "bandit", "--version"], "Bandit"),
        (["poetry", "run", "safety", "--version"], "Safety"),
        (["poetry", "run", "detect-secrets", "--version"], "Detect-Secrets"),
        (["poetry", "run", "pre-commit", "--version"], "Pre-commit"),
    ]

    all_valid = True

    for cmd, tool in tools:
        success, output = run_command(cmd, f"Validate {tool}", check=False)
        if not success:
            print_error(f"{tool} validation failed")
            all_valid = False
        else:
            version = output.strip().split("\n")[0] if output else "unknown"
            print_info(f"{tool}: {version}")

    if all_valid:
        print_success("All security tools validated")
    else:
        print_error("Some security tools failed validation")

    return all_valid


def run_initial_security_scan():
    """Run initial security scan to establish baseline."""
    print_header("Initial Security Scan")

    print_info("Running comprehensive security scan...")

    # Run the security check script if it exists
    security_script = Path("scripts/security_check.py")
    if security_script.exists():
        success, _ = run_command(
            ["python", str(security_script)], "Run security check script", check=False
        )

        if success:
            print_success("Initial security scan completed")
        else:
            print_warning("Security scan completed with issues (review output)")
    else:
        print_warning("Security check script not found, skipping initial scan")

    return True


def create_security_documentation():
    """Create security documentation and guidelines."""
    print_header("Security Documentation")

    docs_dir = Path("docs/security")
    docs_dir.mkdir(parents=True, exist_ok=True)

    security_guide = docs_dir / "SECURITY_GUIDE.md"

    if not security_guide.exists():
        guide_content = """# Orchestra Security Guide

## Overview

This document outlines security practices and tools used in the Orchestra project.

## Security Tools

### Pre-commit Hooks
- **Black**: Code formatting
- **Ruff**: Fast linting
- **Bandit**: Security vulnerability scanning
- **Detect-Secrets**: Secret detection
- **ShellCheck**: Shell script analysis
- **Hadolint**: Dockerfile linting

### Security Scanning
- **Bandit**: Static security analysis for Python
- **Safety**: Dependency vulnerability checking
- **Detect-Secrets**: Prevent secrets in code

### Safe Script Execution
Use the `scripts/safe-runner.py` to validate and execute scripts safely:

```bash
# Validate a script
python scripts/safe-runner.py --validate-only scripts/setup.py

# Run a script safely
python scripts/safe-runner.py scripts/daily-backup.sh

# Dry run (validate only, don't execute)
python scripts/safe-runner.py --dry-run scripts/security_check.py
```

## Security Best Practices

### Code Security
1. Never commit secrets or API keys
2. Use environment variables for sensitive data
3. Validate all inputs
4. Use secure coding practices

### Script Security
1. Always use the safe runner for script execution
2. Review scripts before execution
3. Check file permissions
4. Validate script sources

### Dependency Security
1. Regularly update dependencies
2. Scan for vulnerabilities with Safety
3. Review dependency changes

### Infrastructure Security
1. Use strong authentication
2. Enable branch protection
3. Require security checks in CI/CD
4. Regular security audits

## Incident Response

If you discover a security issue:
1. Do not commit the issue to version control
2. Report to the security team immediately
3. Document the incident
4. Follow remediation procedures

## Regular Security Tasks

### Daily
- Review security logs
- Monitor dependency vulnerabilities

### Weekly
- Run comprehensive security scans
- Review access permissions
- Update security tools

### Monthly
- Security audit
- Update security documentation
- Review and test incident response procedures

## Security Contacts

- Security Team: [Add contact information]
- Incident Response: [Add emergency contact]

---

Last Updated: [Current Date]
"""

        security_guide.write_text(guide_content)
        print_success("Security guide created")
    else:
        print_info("Security guide already exists")

    return True


def main():
    """Main setup function."""
    print(f"{Colors.BOLD}{Colors.CYAN}")
    print("🔒 Orchestra Security Setup")
    print("Initializing security tools and configurations")
    print(f"{Colors.END}")

    # Check if we're in a Poetry project
    if not Path("pyproject.toml").exists():
        print_error("Not in a Poetry project directory")
        sys.exit(1)

    setup_tasks = [
        ("Security Directories", setup_security_directories),
        ("Security Tools Validation", validate_security_tools),
        ("Secrets Detection Baseline", setup_secrets_baseline),
        ("Pre-commit Hooks", setup_pre_commit),
        ("Git Hooks", setup_git_hooks),
        ("Security Documentation", create_security_documentation),
        ("Initial Security Scan", run_initial_security_scan),
    ]

    failed_tasks = []

    for task_name, task_func in setup_tasks:
        print_info(f"Starting: {task_name}")

        try:
            if not task_func():
                failed_tasks.append(task_name)
                print_warning(f"Task failed: {task_name}")
        except Exception as e:
            failed_tasks.append(task_name)
            print_error(f"Task error: {task_name} - {e}")

    # Summary
    print_header("Setup Summary")

    if failed_tasks:
        print_warning(f"Security setup completed with {len(failed_tasks)} issues:")
        for task in failed_tasks:
            print(f"  - {task}")
        print_info("Review the errors above and fix any issues")
    else:
        print_success("Security setup completed successfully! 🎉")

    print("\nNext steps:")
    print("1. Review the security guide: docs/security/SECURITY_GUIDE.md")
    print("2. Run a test security scan: python scripts/security_check.py")
    print("3. Test safe script execution: python scripts/safe-runner.py --help")
    print("4. Commit your changes: git add . && git commit -m 'Setup security tools'")

    sys.exit(1 if failed_tasks else 0)


if __name__ == "__main__":
    main()
