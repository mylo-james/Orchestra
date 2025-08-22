# Orchestra Makefile - Common development tasks

.PHONY: help install test lint format security ci clean docker docs

# Default target
help:
	@echo "🎼 Orchestra Development Commands"
	@echo "=================================="
	@echo ""
	@echo "Setup & Installation:"
	@echo "  install     - Install dependencies and setup development environment"
	@echo "  setup       - Run full development setup (install + docker + db)"
	@echo ""
	@echo "Code Quality:"
	@echo "  format      - Format code with Black and isort"
	@echo "  lint        - Run linting with Ruff"
	@echo "  type-check  - Run type checking with MyPy"
	@echo "  quality     - Run all code quality checks"
	@echo "  fix         - Auto-fix code quality issues"
	@echo ""
	@echo "Testing:"
	@echo "  test        - Run all tests"
	@echo "  test-unit   - Run unit tests only"
	@echo "  test-int    - Run integration tests only"
	@echo "  test-sec    - Run security tests only"
	@echo "  coverage    - Run tests with coverage report"
	@echo ""
	@echo "Security:"
	@echo "  security    - Run security scans (Bandit + Safety)"
	@echo "  bandit      - Run Bandit security scan"
	@echo "  safety      - Run Safety dependency check"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build - Build Docker image"
	@echo "  docker-up   - Start Docker services"
	@echo "  docker-down - Stop Docker services"
	@echo "  docker-logs - View Docker logs"
	@echo ""
	@echo "CI/CD:"
	@echo "  ci          - Run full CI pipeline locally"
	@echo "  pre-commit  - Run pre-commit hooks"
	@echo ""
	@echo "Utilities:"
	@echo "  clean       - Clean up generated files"
	@echo "  docs        - Generate documentation"
	@echo "  health      - Check system health"

# Setup & Installation
install:
	@echo "📦 Installing dependencies..."
	poetry install
	poetry run pre-commit install
	@echo "✅ Installation complete!"

setup:
	@echo "🚀 Running full development setup..."
	poetry run python scripts/setup.py
	@echo "✅ Setup complete!"

# Code Quality
format:
	@echo "🎨 Formatting code..."
	poetry run black src/ tests/
	poetry run isort src/ tests/
	@echo "✅ Code formatted!"

lint:
	@echo "🔍 Running linting..."
	poetry run ruff check src/ tests/

type-check:
	@echo "🏷️  Running type checking..."
	poetry run mypy src/

quality: format lint type-check
	@echo "✅ All code quality checks completed!"

fix:
	@echo "🔧 Auto-fixing code quality issues..."
	python scripts/fix_code_quality.py

# Testing
test:
	@echo "🧪 Running all tests..."
	poetry run pytest tests/ -v

test-unit:
	@echo "🧪 Running unit tests..."
	poetry run pytest tests/unit/ -v

test-int:
	@echo "🧪 Running integration tests..."
	poetry run pytest tests/integration/ -v

test-sec:
	@echo "🧪 Running security tests..."
	poetry run pytest tests/security/ -v

coverage:
	@echo "📊 Running tests with coverage..."
	poetry run pytest tests/ --cov=src --cov-report=html --cov-report=term-missing
	@echo "📋 Coverage report generated in htmlcov/"

# Security
security: bandit safety
	@echo "✅ Security scans completed!"

bandit:
	@echo "🔒 Running Bandit security scan..."
	poetry run bandit -r src/ -c bandit.yaml

safety:
	@echo "🛡️  Running Safety dependency check..."
	poetry run safety scan

# Docker
docker-build:
	@echo "🐳 Building Docker image..."
	docker compose build

docker-up:
	@echo "🐳 Starting Docker services..."
	docker compose up -d
	@echo "✅ Services started! Check with: make docker-logs"

docker-down:
	@echo "🐳 Stopping Docker services..."
	docker compose down

docker-logs:
	@echo "📋 Docker service logs:"
	docker compose logs -f

# CI/CD
ci:
	@echo "🔄 Running full CI pipeline locally..."
	python scripts/run_ci_locally.py

pre-commit:
	@echo "🪝 Running pre-commit hooks..."
	poetry run pre-commit run --all-files

# Utilities
clean:
	@echo "🧹 Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ htmlcov/ .coverage
	rm -f bandit-report.json safety-report.json
	@echo "✅ Cleanup complete!"

docs:
	@echo "📚 Generating documentation..."
	@echo "📋 Documentation is in README.md and docs/ directory"
	@echo "🌐 API documentation would be generated here in a full implementation"

health:
	@echo "🏥 Checking system health..."
	poetry run python -m src.cli.main health

# Development shortcuts
dev-install: install
	@echo "🛠️  Development environment ready!"

dev-test: test coverage
	@echo "🧪 Development testing complete!"

dev-quality: format lint type-check pre-commit
	@echo "✨ Code quality checks complete!"

# Quick commands for common workflows
quick-check: format lint test-unit
	@echo "⚡ Quick checks complete!"

pre-push: format lint test security
	@echo "🚀 Ready to push!"

# Help for specific commands
help-docker:
	@echo "🐳 Docker Commands Help:"
	@echo "  make docker-build  - Build the Orchestra Docker image"
	@echo "  make docker-up     - Start all services (Temporal, PostgreSQL, Orchestra)"
	@echo "  make docker-down   - Stop all services"
	@echo "  make docker-logs   - View real-time logs from all services"
	@echo ""
	@echo "Service URLs:"
	@echo "  - Orchestra API: http://localhost:8000"
	@echo "  - Temporal Web UI: http://localhost:8233"
	@echo "  - PostgreSQL: localhost:5432"

help-testing:
	@echo "🧪 Testing Commands Help:"
	@echo "  make test          - Run all tests (unit + integration + security)"
	@echo "  make test-unit     - Run only unit tests (fast)"
	@echo "  make test-int      - Run only integration tests"
	@echo "  make test-sec      - Run only security tests"
	@echo "  make coverage      - Run tests with HTML coverage report"
	@echo ""
	@echo "Test markers:"
	@echo "  poetry run pytest -m unit        - Unit tests only"
	@echo "  poetry run pytest -m integration - Integration tests only"
	@echo "  poetry run pytest -m security    - Security tests only"
	@echo "  poetry run pytest -m \"not slow\" - Exclude slow tests"
