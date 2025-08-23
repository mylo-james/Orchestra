# Orchestra AI Agent System Brownfield Architecture Document

## Introduction

This document captures the CURRENT STATE of the Orchestra AI Agent System codebase, including technical debt, workarounds, and real-world patterns. It serves as a reference for AI agents working on enhancements and development tasks.

### Document Scope

Comprehensive documentation of entire system with focus on multi-agent orchestration, security framework, and CLI-first architecture.

### Change Log

| Date       | Version | Description                 | Author    |
| ---------- | ------- | --------------------------- | --------- |
| 2024-12-19 | 1.0     | Initial brownfield analysis | Architect |

## Quick Reference - Key Files and Entry Points

### Critical Files for Understanding the System

- **Main Entry**: `src/cli/main.py` - CLI entry point with Typer framework
- **Configuration**: `src/config/settings.py`, `.env.example`
- **Core Business Logic**: `src/services/`, `src/workflows/`
- **Agent System**: `src/system/agent.py`
- **Security Framework**: `src/security/ai_agent_monitor.py`, `src/security/ai_agent_validator.py`
- **Persona System**: `src/personas/*.yaml` - YAML-driven agent behavior
- **Workflow Orchestration**: `src/workflows/dev_team_workflow.py` - Temporal workflows
- **Knowledge Management**: `src/services/knowledge_service.py` - Qdrant vector database

## High Level Architecture

### Technical Summary

Orchestra is a Python-based CLI-first AI agent orchestration system that coordinates specialized agents (Orchestrator, Developer, Release) through Temporal workflows. It uses a universal agent system with YAML-driven personas, comprehensive security validation, and local Qdrant vector database for knowledge management. The system implements production-grade AI safety measures with input validation, output scanning, and audit logging.

### Actual Tech Stack (from pyproject.toml)

| Category        | Technology        | Version | Notes                            |
| --------------- | ----------------- | ------- | -------------------------------- |
| Runtime         | Python            | 3.13.0  | Modern Python with async support |
| CLI Framework   | Typer             | 0.16.0  | Rich CLI with command groups     |
| Agent Framework | OpenAI Agents SDK | 0.2.9   | Multi-agent orchestration        |
| Workflow Engine | Temporal          | 1.7.0   | Durable workflow execution       |
| Vector DB       | Qdrant Client     | 1.7.0   | Local semantic search            |
| HTTP Client     | httpx             | 0.27.0  | Async HTTP client                |
| Data Validation | Pydantic          | 2.11.0  | Type-safe data models            |
| Security        | cryptography      | 44.0.0  | Encryption and security          |
| Database        | aiosqlite         | 0.20.0  | Async SQLite for local storage   |
| Logging         | structlog         | 24.4.0  | Structured logging               |
| Testing         | pytest            | 8.3.0   | Comprehensive test suite         |

### Repository Structure Reality Check

- Type: Monorepo with clear module separation
- Package Manager: Poetry with dependency groups
- Notable: CLI-first architecture, security-focused design, YAML-driven personas

## Source Tree and Module Organization

### Project Structure (Actual)

```text
orchestra/
├── src/
│   ├── cli/                    # Command-line interface (Typer-based)
│   │   ├── main.py            # Main CLI entry point with command groups
│   │   ├── commands.py        # Core command implementations
│   │   ├── output.py          # Rich output formatting
│   │   ├── security_commands.py # Security monitoring commands
│   │   └── circuit_breaker_commands.py # External service circuit breakers
│   ├── system/                 # Universal agent system core
│   │   ├── agent.py           # UniversalAgent class with persona support
│   │   ├── base.py            # SecureAgent base class
│   │   ├── factory.py         # Agent factory pattern
│   │   ├── loader.py          # PersonaLoader for YAML specs
│   │   ├── specs.py           # PersonaSpec data models
│   │   ├── tools.py           # Tool registry and implementations
│   │   └── monitoring.py      # Agent monitoring and metrics
│   ├── agents/                 # Specialized agent implementations
│   │   ├── base/              # Base agent classes and interfaces
│   │   ├── orchestrator/      # Orchestrator agent (handles coordination)
│   │   ├── developer/         # Developer agent (code generation)
│   │   ├── release/           # Release agent (GitHub integration)
│   │   └── tools/             # Agent-specific tools
│   ├── workflows/              # Temporal workflow definitions
│   │   ├── dev_team_workflow.py # Main development team workflow
│   │   ├── activities.py      # Workflow activities
│   │   └── security_activities.py # Security-focused activities
│   ├── services/               # Business logic services
│   │   ├── knowledge_service.py # Vector database operations
│   │   ├── conflict_resolution_service.py # Knowledge conflict resolution
│   │   ├── embedding_service.py # Text embedding generation
│   │   └── external_service_client.py # External API clients
│   ├── security/               # Security framework
│   │   ├── ai_agent_monitor.py # Agent behavior monitoring
│   │   └── ai_agent_validator.py # Input/output validation
│   ├── personas/               # YAML persona specifications
│   │   ├── orchestrator.yaml  # Orchestrator agent persona
│   │   ├── dev.yaml           # Developer agent persona
│   │   └── release.yaml       # Release agent persona
│   ├── config/                 # Configuration management
│   │   └── settings.py        # Pydantic settings with validation
│   └── utils/                  # Shared utilities
│       ├── logging.py         # Structured logging setup
│       └── circuit_breaker.py # Circuit breaker pattern
├── tests/                      # Comprehensive test suite (42 test files)
│   ├── unit/                  # Unit tests by module
│   ├── integration/           # Integration tests
│   └── security/              # Security-focused tests
├── scripts/                    # Setup and utility scripts
│   ├── setup.py               # Development environment setup
│   ├── security_check.py      # Security validation
│   ├── run_ci_locally.py      # Local CI execution
│   └── temporal-config/       # Temporal configuration
├── docs/                       # Documentation
│   ├── architecture/          # Architecture documentation
│   ├── prd/                   # Product requirements
│   └── stories/               # User stories and epics
├── .bmad-core/                 # BMAD method framework
├── .env.example                # Environment template
├── pyproject.toml              # Poetry configuration
├── docker-compose.yml          # Local development environment
└── README.md                   # Project overview
```

### Key Modules and Their Purpose

- **Universal Agent System**: `src/system/agent.py` - Core agent framework with persona support
- **CLI Interface**: `src/cli/main.py` - Rich command-line interface with Typer
- **Workflow Orchestration**: `src/workflows/dev_team_workflow.py` - Temporal-based agent coordination
- **Knowledge Management**: `src/services/knowledge_service.py` - Qdrant vector database operations
- **Security Framework**: `src/security/ai_agent_monitor.py` - Comprehensive AI safety validation
- **Persona System**: `src/personas/*.yaml` - YAML-driven agent behavior configuration

## Data Models and APIs

### Data Models

- **PersonaSpec**: `src/system/specs.py` - YAML persona specification models
- **WorkflowContext**: `src/workflows/dev_team_workflow.py` - Temporal workflow context
- **SecurityContext**: `src/workflows/dev_team_workflow.py` - Security validation context
- **Settings**: `src/config/settings.py` - Pydantic-based configuration

### API Specifications

- **CLI Commands**: See `src/cli/main.py` for available commands
- **Agent Interface**: Universal agent API in `src/system/agent.py`
- **Workflow API**: Temporal workflow interface in `src/workflows/`
- **Security API**: Validation and monitoring in `src/security/`

## Technical Debt and Known Issues

### Critical Technical Debt

1. **Test Coverage Issues**: Some test files have collection errors (see test output)
2. **OpenAI Agents SDK Integration**: Still in development, some features may be incomplete
3. **Temporal Integration**: Workflow orchestration needs more testing
4. **Security Framework**: Comprehensive but needs more real-world validation

### Workarounds and Gotchas

- **Environment Setup**: Requires manual `.env` file creation (see `docs/mylo-todo.md`)
- **Test Execution**: Some tests have logging issues with OpenAI Agents SDK
- **Dependencies**: Poetry-based dependency management with strict versioning
- **Local Development**: Docker Compose required for full local environment

## Integration Points and External Dependencies

### External Services

| Service  | Purpose    | Integration Type | Key Files                            |
| -------- | ---------- | ---------------- | ------------------------------------ |
| OpenAI   | AI Models  | SDK              | `src/system/agent.py`                |
| Qdrant   | Vector DB  | Client           | `src/services/knowledge_service.py`  |
| GitHub   | Repository | API              | `src/system/tools.py`                |
| Temporal | Workflows  | SDK              | `src/workflows/dev_team_workflow.py` |

### Internal Integration Points

- **Agent Handoffs**: Temporal workflows coordinate agent transitions
- **Knowledge Sharing**: Vector database for context preservation
- **Security Validation**: Multi-layer validation at each agent interaction
- **CLI Commands**: Rich command interface for all operations

## Development and Deployment

### Local Development Setup

1. **Environment Setup**: Copy `.env.example` to `.env` and configure API keys
2. **Dependencies**: `poetry install` for dependency installation
3. **Services**: `docker-compose up -d` for local services (Temporal, Qdrant)
4. **Testing**: `poetry run pytest` for test execution

### Build and Deployment Process

- **Build Command**: `poetry build` for package creation
- **CLI Entry**: `poetry run orchestra` for command execution
- **Development**: `poetry run orchestra dev` for development commands
- **Testing**: `poetry run pytest` with coverage reporting

## Testing Reality

### Current Test Coverage

- Unit Tests: 42 test files across all modules
- Integration Tests: Basic integration test structure
- Security Tests: Dedicated security test suite
- Coverage Target: 80% minimum (configured in pyproject.toml)

### Running Tests

```bash
poetry run pytest           # Runs all tests
poetry run pytest --cov=src # With coverage reporting
poetry run pytest tests/unit/ # Unit tests only
```

### Known Test Issues

- Some test files have collection errors related to OpenAI Agents SDK
- Logging configuration issues in test environment
- Temporal workflow tests need more development

## Security Architecture

### Security Framework

- **Input Validation**: `src/security/ai_agent_validator.py` - Comprehensive input scanning
- **Output Monitoring**: `src/security/ai_agent_monitor.py` - Agent behavior monitoring
- **Audit Logging**: Structured logging with correlation IDs
- **Circuit Breakers**: External service protection in `src/utils/circuit_breaker.py`

### Security Commands

- `orchestra security health` - Security framework health check
- `orchestra security validate` - Input/output validation
- `orchestra circuit-breakers status` - Circuit breaker status

## Current Development Status

### Completed Features

- ✅ Universal agent system with YAML personas
- ✅ CLI interface with rich command groups
- ✅ Security framework with validation
- ✅ Knowledge service with Qdrant integration
- ✅ Temporal workflow orchestration
- ✅ Comprehensive test structure

### In Progress

- 🔄 OpenAI Agents SDK integration refinement
- 🔄 Test coverage improvements
- 🔄 Documentation updates
- 🔄 Security validation enhancements

### Known Limitations

- Some test collection errors need resolution
- Environment setup requires manual configuration
- Temporal workflow testing needs expansion
- Security framework needs more real-world validation

## Appendix - Useful Commands and Scripts

### Frequently Used Commands

```bash
poetry run orchestra --help     # Show all available commands
poetry run orchestra version    # Show version information
poetry run orchestra health     # System health check
poetry run orchestra agent list # List available agents
poetry run orchestra workflow start # Start a workflow
```

### Development Commands

```bash
poetry run orchestra dev setup  # Development environment setup
poetry run orchestra dev test   # Run test suite
poetry run orchestra dev lint   # Code quality checks
poetry run orchestra dev security # Security validation
```

### Debugging and Troubleshooting

- **Logs**: Structured logging with correlation IDs
- **Debug Mode**: `--verbose` flag for detailed logging
- **Security Issues**: Check `orchestra security health`
- **Environment**: Verify `.env` configuration

## Notes

- This is a CLI-first architecture optimized for AI agent orchestration
- Security is built-in at every layer with comprehensive validation
- YAML-driven personas enable flexible agent behavior configuration
- Temporal workflows provide durable, fault-tolerant agent coordination
- Local Qdrant vector database enables semantic knowledge management
- The system is designed for local development with cloud service integration
