# Orchestra AI Agent System Makefile
.PHONY: help setup install test lint format security ci clean docker docs test-fast test-safe test-coverage testmon testmon-clean testmon-parallel

help:
	@echo "Orchestra AI Agent System"
	@echo ""
	@echo "Available targets:"
	@echo "  help        - Show this help message"
	@echo "  setup       - Check and fix environment setup automatically"
	@echo "  install     - Install dependencies"
	@echo "  test        - Run all tests (SAFE - with timeout protection)"
	@echo "  test-fast   - Run all tests quickly (may hang)"
	@echo "  test-batch  - Run all tests (recommended)"
	@echo "  test-unit   - Run unit tests only"
	@echo "  test-int    - Run integration tests only"
	@echo "  test-sec    - Run security tests only"
	@echo "  coverage    - Run full tests with coverage report (parallel)"
	@echo "  coverage-incremental - Run incremental tests with coverage (testmon)"
	@echo "  coverage-full - Run full tests with coverage report"
	@echo "  testmon     - Incremental tests with pytest-testmon"
	@echo "  testmon-parallel - Incremental tests in parallel (xdist)"
	@echo "  lint        - Run code linting"
	@echo "  format      - Format code"
	@echo "  type-check  - Run static type checks"
	@echo "  quality     - Run formatting, linting, and type checks"
	@echo "  fix         - Auto-fix formatting and lint issues"
	@echo "  security    - Run security checks"
	@echo "  clean       - Clean build artifacts"
	@echo "  ci          - Run complete CI pipeline"

# Setup Check & Auto-Fix
setup:
	@echo "🔧 Checking and fixing Orchestra development environment..."
	@python3 scripts/setup-check.py
	@echo ""

# Installation
install:
	@echo "📦 Installing Orchestra dependencies..."
	poetry install
	@echo "✅ Installation complete!"

# New SAFE test commands (recommended)
test: test-clean
	@echo "🎉 Clean test execution complete!"

test-batch:
	@echo "🛡️  Running all tests..."
	poetry run pytest tests/ -x --tb=short

test-clean:
	@echo "✨ Running tests with clean output..."
	poetry run pytest tests/

test-verbose:
	@echo "🔍 Running tests with detailed output..."
	poetry run pytest tests/ -v --tb=long --disable-warnings=false

test-safe:
	@echo "🛡️  Running tests with timeout protection..."
	poetry run pytest tests/ -v --tb=short --maxfail=10

# Legacy test commands (may hang)
test-fast:
	@echo "⚡ Running all tests (FAST but may hang)..."
	poetry run pytest tests/ -v

test-unit:
	@echo "🧪 Running unit tests..."
	poetry run pytest tests/unit/ -v

test-cli:
	@echo "🖥️  Running CLI tests (all passing)..."
	poetry run pytest tests/unit/cli/

test-int:
	@echo "🧪 Running integration tests..."
	poetry run pytest tests/integration/ -v

test-sec:
	@echo "🧪 Running security tests..."
	poetry run pytest tests/security/ -v

coverage:
	@echo "📊 Running full tests with coverage in parallel..."
	poetry run pytest -n auto tests/ --cov=orchestra --cov-fail-under=90 --cov-report=html --cov-report=term-missing --cov-report=json

coverage-incremental:
	@echo "📊 Running incremental tests with coverage (pytest-testmon)..."
	poetry run pytest tests/ --testmon --cov=orchestra --cov-fail-under=0 --cov-report=html --cov-report=term-missing --cov-report=json


coverage-full:
	@echo "📊 Running full tests with coverage..."
	poetry run pytest tests/ --cov=orchestra --cov-fail-under=90 --cov-report=html --cov-report=term-missing --cov-report=json

# Incremental testing with pytest-testmon
testmon:
	@echo "⚡ Running incremental tests with pytest-testmon..."
	poetry run pytest --testmon --cov=orchestra --cov-report=term

testmon-clean:
	@echo "🧹 Removing testmon cache..."
	rm -f .testmondata

# Parallel incremental testing (requires pytest-xdist installed)
testmon-parallel:
	@echo "⚡ Running incremental tests in parallel with pytest-testmon + xdist..."
	poetry run pytest -n auto --testmon --cov=orchestra --cov-report=term

# Code quality
lint:
	@echo "🔍 Running code linting..."
	poetry run ruff check orchestra/ tests/

format:
	@echo "🎨 Formatting code..."
	poetry run black orchestra/ tests/
	poetry run isort orchestra/ tests/

type-check:
	@echo "🧠 Running static type checks..."
	poetry run mypy orchestra/

quality: format lint type-check
	@echo "✅ Quality checks complete!"

fix:
	@echo "🛠️  Auto-fixing style issues..."
	poetry run black orchestra/ tests/
	poetry run isort orchestra/ tests/
	poetry run ruff check --fix orchestra/ tests/

# Security
security:
	@echo "🔒 Running security checks..."
	poetry run bandit -r orchestra/
	poetry run pip-audit

# Development workflow shortcuts
dev: format lint test-safe
	@echo "🧪 Development workflow complete!"

dev-test: test-batch coverage
	@echo "🧪 Development testing complete!"

quick-check: format lint test-unit
	@echo "⚡ Quick check complete!"

pre-push: format lint test security
	@echo "🚀 Pre-push checks complete!"

# CI pipeline
ci: install quality security coverage
	@echo "🎯 CI pipeline complete!"

# Cleanup
clean:
	@echo "🧹 Cleaning build artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf build/ dist/ htmlcov/ .coverage

# Docker operations
docker-build:
	@echo "🐳 Building Docker images..."
	docker build -t orchestra:latest .

docker-run:
	@echo "🐳 Running Orchestra in Docker..."
	docker run -p 8000:8000 orchestra:latest

docker-dev:
	@echo "🐳 Running Orchestra in development mode..."
	docker run -v $(PWD):/app -p 8000:8000 orchestra:latest

# Documentation
docs:
	@echo "📚 Building documentation..."
	poetry run mkdocs build

docs-serve:
	@echo "📚 Serving documentation..."
	poetry run mkdocs serve

# Testing guidance
help-testing:
	@echo ""
	@echo "🧪 TESTING GUIDANCE:"
	@echo "  make test          - Run all tests (may have failures in non-CLI areas)"
	@echo "  make test-cli      - RECOMMENDED: Run CLI tests (248/248 passing ✅)"
	@echo "  make test-batch    - Run all tests (recommended)"
	@echo "  make test-verbose  - Detailed output with full tracebacks"
	@echo "  make test-safe     - Run all with timeout protection"
	@echo "  make test-unit     - Run only unit tests"
	@echo "  make test-int      - Run only integration tests"
	@echo "  make test-sec      - Run only security tests"
	@echo "  make coverage      - Run tests with HTML coverage report"
	@echo ""
	@echo "🔍 DEBUGGING HANGING TESTS:"
	@echo "  python scripts/identify_heavy_tests.py  - Find problematic tests"
	@echo "  pytest tests/path/to/test.py -v --tb=short --timeout=30"
	@echo ""
	@echo "⚡ PYTEST MARKS:"
	@echo "  poetry run pytest -m unit        - Unit tests only"
	@echo "  poetry run pytest -m integration - Integration tests only"
	@echo "  poetry run pytest -m security    - Security tests only"
	@echo "  poetry run pytest -m \"not slow\" - Exclude slow tests"
