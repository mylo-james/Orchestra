# Development Security Setup

## Current Configuration (Minimal)

This project uses a **minimal security setup** optimized for development speed while maintaining essential protections.

### Active Security Tools

#### 1. Pre-commit Hooks

- **Black** - Code formatting
- **Ruff** - Fast Python linting with auto-fix
- **Bandit** - Essential security vulnerability scanning
- **Basic file checks** - YAML/JSON validation, merge conflicts, large files

#### 2. Security Scanning

- **Bandit** with essential checks only:
  - Hardcoded passwords/secrets
  - SQL injection patterns
  - Dangerous subprocess calls
  - eval() usage

#### 3. Safe Script Execution

- `scripts/safe-runner.py` for validating scripts before execution
- `scripts/validate-all-scripts.py` for comprehensive script validation

### What's Disabled (For Now)

These enterprise features are commented out but ready to enable:

- **Detect-secrets** - Advanced secret detection (too noisy for dev)
- **ShellCheck** - Shell script linting (too strict for dev)
- **Hadolint** - Dockerfile linting
- **Additional Bandit checks** - Comprehensive security scanning
- **Private key detection** - Flags test keys

## Quick Commands

```bash
# Test current security setup
poetry run python scripts/security_check.py

# Fix code quality issues
poetry run python scripts/fix_code_quality.py

# Validate all scripts
python scripts/validate-all-scripts.py

# Run script safely
python scripts/safe-runner.py scripts/daily-backup.sh

# Install/update pre-commit hooks
poetry run pre-commit install
poetry run pre-commit run --all-files
```

## Upgrading to Enterprise Security

When ready for production/enterprise security, uncomment sections in:

1. **`.pre-commit-config.yaml`** - Uncomment enterprise features
2. **`pyproject.toml`** - Uncomment additional security tools
3. **`bandit.yaml`** - Copy from `bandit.enterprise.yaml` (when created)

### Enterprise Upgrade Steps

```bash
# 1. Enable additional security tools in pyproject.toml
poetry add detect-secrets pip-audit semgrep

# 2. Uncomment enterprise hooks in .pre-commit-config.yaml
# (Edit file manually)

# 3. Create comprehensive secrets baseline
poetry run detect-secrets scan --baseline .secrets.baseline

# 4. Run full security setup
python scripts/setup-security.py

# 5. Update branch protection (for CI/CD)
scripts/setup-branch-protection.sh
```

## Security Philosophy

**Development**: Fast feedback, minimal friction, catch obvious issues
**Enterprise**: Comprehensive scanning, strict policies, compliance-ready

The current setup catches ~80% of security issues with ~20% of the complexity.
