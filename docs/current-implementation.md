# Orchestra v0.1.0 - Current Implementation

## Overview

Orchestra v0.1.0 is an AI agent system for development team orchestration built around a unique **persona-based architecture**. Instead of hardcoded agent classes, Orchestra uses a single `UniversalAgent` that dynamically embodies different personas defined in YAML configuration files.

## Core Architecture

### UniversalAgent System

The heart of Orchestra is the `UniversalAgent` class (`orchestra/system/agent.py`) which:

- Dynamically loads persona specifications from YAML files
- Configures itself based on the loaded persona's behavioral contract
- Executes commands defined in the persona's command interface
- Maintains security validation and audit logging

### Persona System

Orchestra currently includes three active personas:

#### 1. Orchestrator (Brendan) - `orchestrator.yaml`

- **Role**: Strategic planner and workflow coordinator
- **Focus**: Analyzing user requests and creating implementation plans
- **Key Commands**: plan, clarify, coordinate, select-persona
- **When to Use**: Request analysis, multi-agent planning, workflow coordination

#### 2. Developer (Alex) - `dev.yaml`

- **Role**: Expert Python/Temporal developer
- **Focus**: Code implementation, testing, and refactoring
- **Key Commands**: implement-story, implement-feature, fix-bug, create-tests
- **When to Use**: Code implementation, debugging, technical problem solving

#### 3. Release (Riley) - `release.yaml`

- **Role**: Release management and deployment specialist
- **Focus**: Safe and reliable code releases, version control
- **Key Commands**: create-pr, create-release, deploy, rollback
- **When to Use**: Creating releases, managing branches, deploying code

## Technical Stack

### Core Technologies

- **Python 3.13** - Primary language with modern async/await patterns
- **Poetry** - Dependency management and packaging
- **Pydantic** - Data validation and settings management
- **Typer + Rich** - Beautiful CLI interface with progress tracking

### External Services

- **OpenAI API** - AI language model integration
- **Temporal** - Workflow orchestration with fault tolerance
- **Qdrant** - Local vector database for semantic search
- **PostgreSQL** - Database for Temporal state management

### Development Tools

- **pytest** - Testing framework with 90%+ coverage requirement
- **black + isort + ruff** - Code formatting and linting
- **bandit** - Security scanning
- **mypy** - Type checking
- **pre-commit** - Git hooks for quality checks

## CLI Interface

Orchestra provides a rich command-line interface organized into command groups:

```bash
orchestra --help                    # Show available commands
orchestra agent <subcommand>        # Agent management
orchestra workflow <subcommand>     # Workflow orchestration
orchestra config <subcommand>       # Configuration management
orchestra dev <subcommand>          # Development tools
orchestra security <subcommand>     # Security monitoring
orchestra circuit-breakers <cmd>    # Service health management
```

## Security Framework

Orchestra implements a comprehensive security-first approach:

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

### Circuit Breakers

- External service health monitoring
- Automatic failure handling
- Recovery and retry mechanisms

## File Structure

```
orchestra/
├── cli/                    # Command-line interface
│   ├── main.py            # Entry point and main app
│   ├── commands.py        # Core CLI commands
│   ├── security_commands.py
│   └── circuit_breaker_commands.py
├── personas/               # YAML persona definitions
│   ├── orchestrator.yaml  # Brendan - Strategic planner
│   ├── dev.yaml          # Alex - Developer specialist
│   └── release.yaml       # Riley - Release manager
├── system/                 # Agent system implementation
│   ├── agent.py           # UniversalAgent class
│   ├── loader.py          # PersonaLoader
│   ├── specs.py           # Persona specifications
│   ├── factory.py         # Agent factory
│   └── tools.py           # Tool implementations
├── workflows/              # Temporal workflows
├── services/               # Business logic services
├── security/               # Security framework
├── config/                 # Configuration management
└── utils/                  # Shared utilities
```

## Deployment

Orchestra is designed for **local laptop deployment** with:

- Docker Compose for service orchestration
- Local Qdrant instance for vector storage
- PostgreSQL for Temporal state management
- No external dependencies beyond OpenAI API

## Testing Strategy

### Test Coverage

- Target: **90% minimum** test coverage
- Current: Unit, integration, and security tests
- Framework: pytest with async support

### Test Organization

```
tests/
├── unit/           # Component-level tests
├── integration/    # Multi-component tests
└── security/       # Security validation tests
```

### Quality Gates

- All tests must pass before merge
- Security scans required
- Code coverage requirements enforced
- Pre-commit hooks for quality checks

## Key Features

### 1. Dynamic Persona Loading

- Runtime configuration of agent behavior
- No code changes required for new personas
- YAML-based persona definitions

### 2. Command-Driven Interface

- Each persona defines specific commands
- Execution patterns and parameters
- Timeout and confirmation handling

### 3. Security Integration

- Built-in validation and monitoring
- Comprehensive audit trails
- Circuit breaker patterns

### 4. Development Workflow Integration

- Git/GitHub integration
- Temporal workflow orchestration
- Rich CLI with progress tracking

## Configuration

### Environment Variables

- `OPENAI_API_KEY` - Required for AI integration
- `QDRANT_HOST/PORT` - Vector database connection
- Additional settings in `.env` file

### Persona Configuration

Each persona YAML includes:

- `identity` - Name, role, style, focus
- `behavioral_contract` - Core principles and constraints
- `command_interface` - Available commands and patterns
- `resource_dependencies` - Required tools and knowledge

## Future Evolution

This v0.1.0 implementation serves as the foundation for planned v2 features:

- Resource-driven infrastructure (ResourceLoader, TaskEngine, etc.)
- Advanced collaboration capabilities
- Memory and learning systems
- Dynamic team composition

The current persona-based architecture is designed to be extended without breaking existing functionality.
