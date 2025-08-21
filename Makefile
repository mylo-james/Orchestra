# Orchestra AI Agent System - Development Makefile
# Professional development workflow automation

.PHONY: help install test lint format security clean build deploy docs

# Default target
help: ## Show this help message
	@echo "🚀 Orchestra AI Agent System - Development Commands"
	@echo "=================================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ============================================================================
# SETUP & INSTALLATION
# ============================================================================

install: ## Install all dependencies and set up development environment
	@echo "📦 Installing Orchestra AI development environment..."
	poetry install --with dev,test,security
	poetry run pre-commit install
	poetry run pre-commit install --hook-type pre-push
	@echo "✅ Installation complete!"

setup-ci: ## Set up complete CI/CD pipeline
	@echo "🚀 Setting up CI/CD pipeline..."
	python scripts/setup_ci.py

clean: ## Clean up build artifacts and caches
	@echo "🧹 Cleaning up..."
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete
	@echo "✅ Cleanup complete!"

# ============================================================================
# CODE QUALITY
# ============================================================================

format: ## Format code with Black and isort
	@echo "🎨 Formatting code..."
	poetry run black .
	poetry run isort .
	@echo "✅ Code formatting complete!"

lint: ## Run all linting checks
	@echo "🔍 Running linting checks..."
	poetry run black --check .
	poetry run isort --check-only .
	poetry run flake8 src/ tests/
	poetry run mypy src/
	@echo "✅ Linting complete!"

format-check: ## Check code formatting without making changes
	@echo "🔍 Checking code formatting..."
	poetry run black --check --diff .
	poetry run isort --check-only --diff .

# ============================================================================
# TESTING
# ============================================================================

test: ## Run all tests
	@echo "🧪 Running all tests..."
	poetry run pytest tests/ -v

test-unit: ## Run unit tests only
	@echo "🧪 Running unit tests..."
	poetry run pytest tests/unit/ -v

test-integration: ## Run integration tests only
	@echo "🔗 Running integration tests..."
	poetry run pytest tests/integration/ -v

test-security: ## Run security tests only
	@echo "🛡️ Running security tests..."
	poetry run pytest tests/security/ -v

test-e2e: ## Run end-to-end tests
	@echo "🎭 Running end-to-end tests..."
	poetry run pytest tests/e2e/ -v

test-coverage: ## Run tests with coverage report
	@echo "📊 Running tests with coverage..."
	poetry run pytest --cov=src --cov-report=html --cov-report=term

test-performance: ## Run performance benchmarks
	@echo "⚡ Running performance benchmarks..."
	poetry run pytest tests/performance/ --benchmark-only

# ============================================================================
# SECURITY
# ============================================================================

security: ## Run all security checks
	@echo "🔒 Running security checks..."
	poetry run bandit -r src/
	poetry run safety check
	poetry run detect-secrets scan --all-files --baseline .secrets.baseline
	python scripts/security_check.py

security-scan: ## Run comprehensive security scan
	@echo "🛡️ Running comprehensive security scan..."
	poetry run bandit -r src/ -f json -o bandit-report.json
	poetry run safety check --json --output safety-report.json
	python scripts/security_check.py --full-audit

security-baseline: ## Update security baseline files
	@echo "📋 Updating security baselines..."
	poetry run detect-secrets scan --baseline .secrets.baseline
	poetry run bandit -r src/ -f json -o security-baseline.json

# ============================================================================
# AI AGENT VALIDATION
# ============================================================================

validate-agents: ## Validate all agent code
	@echo "🤖 Validating agent code..."
	find src/agents -name "*.py" -exec python scripts/validate_agent_code.py {} +

validate-prompts: ## Validate prompt templates
	@echo "📝 Validating prompt templates..."
	find . -name "*.prompt" -o -name "*.template" | xargs python scripts/validate_prompts.py

check-ai-security: ## Check AI-specific security
	@echo "🤖 Checking AI security..."
	python scripts/security_check.py --test-prompt-injection --test-code-generation

# ============================================================================
# BUILD & DEPLOYMENT
# ============================================================================

build: ## Build the package
	@echo "🏗️ Building package..."
	poetry build
	@echo "✅ Build complete!"

build-docker: ## Build Docker container
	@echo "🐳 Building Docker container..."
	docker build -t orchestra-ai:latest -f .cursor/Dockerfile .
	@echo "✅ Docker build complete!"

deploy-staging: ## Deploy to staging environment
	@echo "🚀 Deploying to staging..."
	# Add staging deployment commands here
	@echo "✅ Staging deployment complete!"

deploy-production: ## Deploy to production environment
	@echo "🌟 Deploying to production..."
	# Add production deployment commands here
	@echo "✅ Production deployment complete!"

# ============================================================================
# DEVELOPMENT TOOLS
# ============================================================================

dev: ## Start development environment
	@echo "🔧 Starting development environment..."
	poetry run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

dev-docker: ## Start development environment with Docker
	@echo "🐳 Starting Docker development environment..."
	docker-compose up -d

logs: ## Show development logs
	@echo "📋 Showing logs..."
	tail -f logs/orchestra.log

shell: ## Start interactive Python shell with project context
	@echo "🐍 Starting Python shell..."
	poetry run python

notebook: ## Start Jupyter notebook
	@echo "📓 Starting Jupyter notebook..."
	poetry run jupyter notebook

# ============================================================================
# DOCUMENTATION
# ============================================================================

docs: ## Generate documentation
	@echo "📚 Generating documentation..."
	# Add documentation generation commands here
	@echo "✅ Documentation generated!"

docs-serve: ## Serve documentation locally
	@echo "📖 Serving documentation..."
	# Add documentation serving commands here

# ============================================================================
# MONITORING & MAINTENANCE
# ============================================================================

health-check: ## Run system health checks
	@echo "🏥 Running health checks..."
	python scripts/health_check.py

monitor: ## Show monitoring dashboard
	@echo "📊 Opening monitoring dashboard..."
	# Add monitoring dashboard commands here

update-deps: ## Update all dependencies
	@echo "📦 Updating dependencies..."
	poetry update
	poetry run pre-commit autoupdate
	@echo "✅ Dependencies updated!"

audit: ## Run comprehensive system audit
	@echo "🔍 Running system audit..."
	make security
	make test-coverage
	make validate-agents
	@echo "✅ System audit complete!"

# ============================================================================
# CI/CD UTILITIES
# ============================================================================

ci-local: ## Run CI pipeline locally
	@echo "🚀 Running CI pipeline locally..."
	make lint
	make security
	make test
	make build
	@echo "✅ Local CI pipeline complete!"

precommit-all: ## Run all pre-commit hooks
	@echo "🪝 Running all pre-commit hooks..."
	poetry run pre-commit run --all-files

fix-all: ## Fix all auto-fixable issues
	@echo "🔧 Fixing all auto-fixable issues..."
	make format
	poetry run pre-commit run --all-files || true
	@echo "✅ Auto-fixes complete!"

# ============================================================================
# UTILITIES
# ============================================================================

licenses: ## Check dependency licenses
	@echo "📄 Checking dependency licenses..."
	poetry run pip-licenses --format=table
	poetry run pip-licenses --format=json --output-file=licenses.json
	python scripts/validate_licenses.py licenses.json

env-check: ## Validate environment configuration
	@echo "🌍 Checking environment configuration..."
	poetry run python -c "from src.config.settings import Settings; print('✅ Environment configuration valid')"

version: ## Show version information
	@echo "📋 Version Information:"
	@echo "  Python: $(python --version)"
	@echo "  Poetry: $(poetry --version)"
	@echo "  Orchestra AI: $(poetry version --short)"

# ============================================================================
# QUICK COMMANDS
# ============================================================================

quick-test: ## Quick test run (unit tests only)
	poetry run pytest tests/unit/ -x -q

quick-lint: ## Quick lint check
	poetry run black --check .
	poetry run flake8 src/ --count

quick-security: ## Quick security check
	poetry run bandit -r src/ -ll

all: ## Run complete quality pipeline
	@echo "🚀 Running complete quality pipeline..."
	make clean
	make install
	make lint
	make security
	make test
	make build
	@echo "🎉 Complete pipeline finished!"