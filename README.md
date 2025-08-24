# 🎼 Orchestra - AI Agent System for Development Team Orchestration

Orchestra is a sophisticated AI agent system designed to orchestrate complex development workflows through coordinated multi-agent collaboration. Built with security, observability, and production-readiness in mind.

## 🌟 Features

- **Multi-Agent Coordination**: Orchestrates specialized AI agents (Developer, Release, QA) through structured workflows
- **Temporal Integration**: Durable workflow execution with fault tolerance and state persistence
- **Security-First Design**: Comprehensive input validation, output scanning, and audit logging
- **Vector Knowledge Base**: Qdrant-powered local semantic search for project knowledge and context
- **Rich CLI Interface**: Beautiful command-line interface with progress tracking and formatted output
- **Docker Support**: Complete containerized development environment
- **Comprehensive Testing**: Unit, integration, and security test suites

## 🏗️ Architecture

Orchestra follows a modular architecture with a unique persona-based agent system:

```
orchestra/
├── cli/                    # Command-line interface
├── personas/               # YAML persona definitions
│   ├── orchestrator.yaml  # Orchestrator persona (Brendan)
│   ├── dev.yaml           # Developer persona (Alex)
│   └── release.yaml       # Release persona (Riley)
├── system/                 # Agent system implementation
│   ├── agent.py           # UniversalAgent class
│   ├── loader.py          # PersonaLoader
│   └── specs.py           # Persona specifications
├── workflows/              # Temporal workflows
├── services/               # Business logic services
├── security/               # Security framework
├── config/                 # Configuration management
└── utils/                  # Shared utilities
```

### Core Architecture Principles

- **UniversalAgent**: Single agent class that embodies different personas through YAML configuration
- **Persona-Based System**: Identity, behavior, and capabilities defined in YAML files
- **Command-Driven Interface**: Each persona has specific commands with execution patterns
- **Security-First**: Comprehensive validation, audit logging, and security monitoring

## 🚀 Quick Start

### Prerequisites

- Python 3.13.0+
- Poetry 1.8.3+
- Docker and Docker Compose
- Git

### 1. Clone and Setup

```bash
git clone <repository-url>
cd orchestra
```

### 2. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys and configuration
nano .env
```

**Required Environment Variables:**

- `OPENAI_API_KEY`: Your OpenAI API key (get from [OpenAI Platform](https://platform.openai.com/api-keys))
- `QDRANT_HOST`: Qdrant server host (default: localhost)
- `QDRANT_PORT`: Qdrant HTTP port (default: 6333)

### 3. Install Dependencies

```bash
# Install Poetry (if not already installed)
curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies
poetry install

# Install pre-commit hooks
poetry run pre-commit install
```

### 4. Start Development Environment

```bash
# Start all services (Temporal, PostgreSQL, Orchestra)
docker-compose up -d

# Check service health
docker-compose ps

# View logs
docker-compose logs -f orchestra
```

### 5. Verify Installation

```bash
# Check system health
poetry run orchestra health

# Run basic commands
poetry run orchestra --help
poetry run orchestra version
```

## 🛠️ Development

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run specific test types
poetry run pytest tests/unit/           # Unit tests
poetry run pytest tests/integration/    # Integration tests
poetry run pytest tests/security/       # Security tests

# Run with coverage
poetry run pytest --cov=orchestra --cov-report=html

# Run only fast tests (exclude slow tests)
poetry run pytest -m "not slow"
```

### Code Quality

```bash
# Format code
poetry run black orchestra/ tests/
poetry run isort orchestra/ tests/

# Lint code
poetry run ruff check orchestra/ tests/

# Security scanning
poetry run bandit -r orchestra/ -f json -o bandit-report.json

# Type checking
poetry run mypy orchestra/

# Run all quality checks
poetry run pre-commit run --all-files
```

### CLI Usage

```bash
# Basic CLI commands
poetry run orchestra --help
poetry run orchestra version
poetry run orchestra health

# Agent management
poetry run orchestra agent list
poetry run orchestra agent status
poetry run orchestra agent start orchestrator

# Workflow management
poetry run orchestra workflow list
poetry run orchestra workflow run dev-workflow

# Configuration management
poetry run orchestra config show
poetry run orchestra config validate

# Development tools
poetry run orchestra dev test
poetry run orchestra dev lint
poetry run orchestra dev security-scan
```

### Development Mode

```bash
# Start development services
docker-compose --profile dev up -d

# Access development tools container
docker-compose exec dev-tools bash

# Run Orchestra in development mode
poetry run orchestra serve --reload
```

## ✅ CI

The GitHub Actions pipeline runs on pushes and pull requests to `main` and `develop`, with a nightly scheduled run:

- Quality: Black/isort checks, Ruff, MyPy, and pre-commit (style-only)
- Security: Bandit scan and dependency audit with pip-audit
- Tests + Coverage: pytest with a hard 90% gate, Codecov upload, HTML coverage artifact
- Docker (non-PR): Build image and run a smoke test

Codecov requires `CODECOV_TOKEN` in repository secrets (tokenless for public repos may work). Run `make ci` locally to mirror the pipeline.

## 🔒 Security

Orchestra implements comprehensive security measures:

### Input Validation

- Pydantic models for structured data validation
- Input sanitization and validation
- File type and size restrictions

### Output Scanning

- Generated code security analysis
- Bandit integration for Python security scanning
- Pattern-based secret detection

### Audit Logging

- Comprehensive security audit trails
- Correlation IDs for request tracing
- Agent handoff logging

### Configuration Security

- Environment variable validation
- Secret masking in logs and outputs
- Secure defaults for all settings

### Security Testing

```bash
# Run security tests
poetry run pytest tests/security/

# Run security scan
poetry run bandit -r orchestra/

# Check for secrets
poetry run detect-secrets scan --all-files
```

## 🐳 Docker

### Development Environment

```bash
# Start all services
docker-compose up -d

# View service status
docker-compose ps

# View logs
docker-compose logs -f [service-name]

# Stop services
docker-compose down
```

### Services

- **orchestra**: Main application container
- **temporal**: Temporal workflow server
- **postgresql**: Database for Temporal
- **dev-tools**: Development tools container (dev profile)

### Service URLs

- Orchestra API: http://localhost:8000
- Temporal Web UI: http://localhost:8233
- PostgreSQL: localhost:5432

## 📊 Monitoring and Observability

### Logging

Orchestra uses structured logging with correlation IDs:

```python
from orchestra.utils.logging import get_logger, set_correlation_id

logger = get_logger(__name__)
correlation_id = set_correlation_id()

logger.info("Operation started", operation="test", correlation_id=correlation_id)
```

### Metrics

- Agent performance metrics
- Workflow execution metrics
- Security event tracking
- API call monitoring

### Health Checks

```bash
# Application health check
poetry run orchestra health

# Docker health checks
docker-compose ps
```

## 🔧 Configuration

### Environment Variables

See `.env.example` for all available configuration options.

### Key Configuration Sections

- **Application**: Basic app settings
- **OpenAI**: AI model configuration
- **Qdrant**: Vector database settings
- **Temporal**: Workflow orchestration
- **Database**: PostgreSQL configuration
- **Security**: Security feature toggles
- **Logging**: Log levels and formats

### Configuration Validation

```bash
# Validate current configuration
poetry run orchestra config validate

# Show configuration (sensitive values masked)
poetry run orchestra config show
```

## 🧪 Testing Strategy

### Test Organization

```
tests/
├── unit/           # Unit tests for individual components
├── integration/    # Integration tests for component interactions
├── security/       # Security-focused tests
└── fixtures/       # Test data and fixtures
```

### Test Types

- **Unit Tests**: Fast, isolated component tests
- **Integration Tests**: Multi-component interaction tests
- **Security Tests**: Input validation, secret detection, audit logging
- **Performance Tests**: Load and performance validation

### Test Markers

```bash
# Run tests by marker
poetry run pytest -m unit           # Unit tests only
poetry run pytest -m integration    # Integration tests only
poetry run pytest -m security       # Security tests only
poetry run pytest -m "not slow"     # Exclude slow tests
```

## 📚 API Reference

### CLI Commands

| Command                           | Description                      |
| --------------------------------- | -------------------------------- |
| `orchestra --help`                | Show help and available commands |
| `orchestra version`               | Display version information      |
| `orchestra health`                | Check system health              |
| `orchestra serve`                 | Start API server                 |
| `orchestra agent <subcommand>`    | Agent management                 |
| `orchestra workflow <subcommand>` | Workflow management              |
| `orchestra config <subcommand>`   | Configuration management         |
| `orchestra dev <subcommand>`      | Development tools                |

### Available Personas

- **Orchestrator (Brendan)**: Strategic planner and workflow coordinator who analyzes user requests and creates implementation plans
- **Developer (Alex)**: Expert Python/Temporal developer specializing in implementation, testing, and refactoring
- **Release (Riley)**: Release management specialist handling deployments, PRs, and version control

## 🔍 Troubleshooting

### Common Issues

#### 1. API Key Issues

```bash
# Check API key configuration
poetry run orchestra config show --section openai

# Validate API keys
poetry run orchestra health
```

#### 2. Docker Issues

```bash
# Check service status
docker-compose ps

# View service logs
docker-compose logs temporal
docker-compose logs postgresql

# Restart services
docker-compose restart
```

#### 3. Dependency Issues

```bash
# Reinstall dependencies
poetry install --no-cache

# Update dependencies
poetry update
```

#### 4. Permission Issues

```bash
# Fix file permissions
chmod +x scripts/*.py

# Check Docker permissions
docker-compose exec orchestra whoami
```

### Debug Mode

```bash
# Enable verbose logging
poetry run orchestra --verbose <command>

# Enable debug mode
export DEBUG=true
poetry run orchestra <command>
```

### Log Analysis

```bash
# View application logs
docker-compose logs -f orchestra

# View Temporal logs
docker-compose logs -f temporal

# Search logs for errors
docker-compose logs orchestra | grep ERROR
```

## 🤝 Contributing

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and quality checks
5. Submit a pull request

### Code Standards

- Follow PEP 8 and project coding standards
- Write comprehensive docstrings
- Include type hints
- Add appropriate tests
- Update documentation

### Pre-commit Hooks

```bash
# Install pre-commit hooks
poetry run pre-commit install

# Run hooks manually
poetry run pre-commit run --all-files
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- OpenAI for the Agents SDK and language models
- Temporal for workflow orchestration
- Qdrant for local vector database services
- The Python community for excellent tooling

## 📞 Support

For support and questions:

1. Check the troubleshooting section above
2. Search existing issues
3. Create a new issue with detailed information
4. Include logs and configuration (without secrets)

---

**Orchestra** - Orchestrating AI agents for seamless development workflows 🎼
