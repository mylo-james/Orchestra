# CI/CD Pipeline Documentation

This document describes the Continuous Integration and Continuous Deployment (CI/CD) pipeline for the Orchestra AI Agent System.

## Overview

Orchestra uses GitHub Actions for CI/CD with a comprehensive pipeline that includes:

- **Code Quality**: Formatting, linting, type checking
  - Note: Type checking is advisory in CI (non-blocking) due to ongoing typing work
- **Security**: Vulnerability scanning, secret detection
- **Testing**: Unit, integration, and security tests
- **Coverage**: Code coverage reporting with Codecov
- **Docker**: Container building and testing
- **Dependencies**: Automated dependency updates with Dependabot

## Workflows

### 1. Main CI Pipeline (`.github/workflows/ci.yml`)

Triggered on:

- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`
- Daily schedule (2 AM UTC) for security checks

#### Jobs:

**Quality Job**

- Code formatting checks: Black (check), isort (check-only)
- Linting: Ruff
- Type checking: MyPy
- Pre-commit hooks: run with `SKIP=coverage-check` to avoid re-running tests

**Security Job**

- Static analysis: Bandit (configured via `bandit.yaml`)
- Dependency audit: pip-audit

**Tests + Coverage Job**

- Run pytest with a hard 90% coverage gate
- Generate `coverage.xml` and upload to Codecov
- Upload `htmlcov/` as a build artifact

**Docker Build Job** (optional, non-PR)

- Build Docker image and run a basic smoke test

### 2. Pre-commit Pipeline (`.github/workflows/pre-commit.yml`)

Triggered on pull requests to ensure code quality standards.

### 3. Release Pipeline (`.github/workflows/release.yml`)

Triggered on:

- Git tags matching `v*` pattern
- Manual workflow dispatch

#### Release Process:

1. Validate release version format
2. Run full test suite
3. Build and publish Docker image
4. Build and publish Python package to PyPI
5. Create GitHub release with changelog
6. Send notifications

## Local Development

### Quick Commands (Makefile)

```bash
# Setup
make install          # Install dependencies
make setup           # Full development setup

# Code Quality
make format          # Format code
make lint           # Run linting
make quality        # All quality checks
make fix            # Auto-fix issues

# Testing
make test           # All tests
make test-unit      # Unit tests only
make coverage       # Tests with coverage

# Security
make security       # Security scans
make bandit         # Bandit scan
make safety         # Dependency check

# Docker
make docker-up      # Start services
make docker-down    # Stop services
make docker-logs    # View logs

# CI
make ci             # Run full CI locally
make pre-commit     # Run pre-commit hooks
```

### Local CI Runner

Run the complete CI pipeline locally before pushing:

```bash
# Run all checks locally
python scripts/run_ci_locally.py

# Auto-fix code quality issues
python scripts/fix_code_quality.py
```

## Code Quality Standards

### Formatting

- **Black**: Code formatting with 88-character line length
- **isort**: Import sorting with Black profile

### Linting

- **Ruff**: Fast Python linting with security rules
- **MyPy**: Type checking with strict mode

### Security

- **Bandit**: Security vulnerability scanning
- **pip-audit**: Dependency vulnerability checking
- **Pre-commit**: Git hooks for quality enforcement

### Testing

- **pytest**: Testing framework with async support
- **Coverage**: Minimum 90% code coverage
- **Markers**: `unit`, `integration`, `security`, `slow`

## Coverage Requirements

| Type               | Target | Threshold       |
| ------------------ | ------ | --------------- |
| Overall Project    | 90%    | 2% drop allowed |
| New Code (Patches) | 95%    | 5% drop allowed |

### Coverage Exclusions

- Test files (`tests/`)
- Setup scripts (`scripts/`)
- Documentation (`docs/`)
- `__init__.py` files
- CLI output formatting

## Security Scanning

### Bandit Configuration

- Scans all Python code in `orchestra/`
- Custom rules for AI agent systems
- JSON and text output formats
- Baseline file for ignoring false positives

### Dependency Audit Configuration

- Checks all dependencies for known vulnerabilities
- Daily automated scans
- JSON reporting for tracking

### Secret Detection

- Pre-commit hooks scan for secrets
- Pattern-based detection for API keys
- Baseline file for legitimate patterns

## Docker Pipeline

### Build Process

1. Multi-stage Dockerfile with Poetry
2. Security-focused base image
3. Non-root user execution
4. Health checks included

### Testing

- Container functionality verification
- Docker Compose service integration
- Environment variable validation

## Dependency Management

### Dependabot Configuration

- **Python**: Weekly updates on Monday
- **Docker**: Weekly updates on Tuesday
- **GitHub Actions**: Weekly updates on Wednesday
- Target branch: `develop`
- Automatic labeling and assignment

### Update Strategy

- Direct and indirect dependencies
- Ignore patch updates for stable packages
- Maximum 5 open PRs per ecosystem

## Release Process

### Version Management

- Semantic versioning (vX.Y.Z)
- Git tags trigger releases
- Automated changelog generation

### Artifacts

- **Docker**: `orchestra/orchestra:vX.Y.Z`
- **PyPI**: `orchestra==X.Y.Z`
- **GitHub**: Release with artifacts

### Deployment

1. Tag creation triggers release workflow
2. Full test suite must pass
3. Docker image built and pushed
4. Python package published to PyPI
5. GitHub release created
6. Notifications sent

## Environment Variables

### Required for CI

```bash
# Secrets (set in GitHub repository settings)
DOCKER_USERNAME=<docker-hub-username>
DOCKER_PASSWORD=<docker-hub-token>
PYPI_TOKEN=<pypi-api-token>
CODECOV_TOKEN=<codecov-token>

# Optional
SLACK_WEBHOOK_URL=<slack-webhook-for-notifications>
```

### Test Environment

```bash
# Automatically set by CI
ENVIRONMENT=test
DEBUG=true
OPENAI_API_KEY=sk-test-key-for-ci-testing
QDRANT_HOST=localhost
QDRANT_PORT=6333
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=test_orchestra
POSTGRES_USER=test_user
POSTGRES_PASSWORD=test_password
```

## Monitoring and Notifications

### Failure Notifications

- Slack notifications on main branch failures
- Email notifications for security issues
- GitHub issue creation for dependency vulnerabilities

### Reporting

- **Codecov**: Coverage reports and trends
- **GitHub**: Test results and artifacts
- **Security**: Bandit and pip-audit reports

## Best Practices

### Before Pushing

1. Run `make ci` locally
2. Fix any code quality issues with `make fix`
3. Ensure all tests pass
4. Review security scan results

### Pull Request Guidelines

1. Target the `develop` branch
2. Include tests for new features
3. Update documentation if needed
4. Ensure CI passes before requesting review

### Release Guidelines

1. Update version in `pyproject.toml`
2. Create comprehensive changelog
3. Tag with `git tag vX.Y.Z`
4. Push tag to trigger release

## Troubleshooting

### Common CI Failures

**Code Quality Issues**

```bash
# Auto-fix most issues
make fix

# Manual fixes for remaining issues
make quality
```

**Test Failures**

```bash
# Run specific test types
make test-unit
make test-int
make test-sec

# Debug with verbose output
poetry run pytest tests/ -v -s
```

**Docker Build Issues**

```bash
# Test Docker build locally
make docker-build

# Check Docker Compose configuration
docker-compose config
```

**Security Scan Issues**

```bash
# Run security scans locally
make security

# Review and update security baseline
poetry run bandit -r orchestra/ -f json -o .bandit_baseline
```

### Performance Issues

- Use caching for dependencies
- Parallel job execution where possible
- Optimize Docker layer caching
- Use appropriate test markers to skip slow tests

## Future Enhancements

- [ ] Integration with external security scanners
- [ ] Performance regression testing
- [ ] Automated documentation generation
- [ ] Integration testing with real services
- [ ] Deployment to staging/production environments
- [ ] Chaos engineering tests
- [ ] Load testing automation
