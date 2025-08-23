# Orchestra AI Agent System Source Tree

## Overview

This document provides the complete source tree structure for the Orchestra AI Agent System, showing the actual file organization and module relationships. This is the **real implementation** structure, not a template or idealized version.

## Complete Source Tree

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

## Key Module Purposes

### Core System Modules

- **`src/cli/`** - Rich command-line interface built with Typer

  - `main.py` - Entry point with command groups and global configuration
  - `commands.py` - Core command implementations for agents and workflows
  - `output.py` - Rich formatting and display utilities
  - `security_commands.py` - Security monitoring and validation commands
  - `circuit_breaker_commands.py` - External service circuit breaker management

- **`src/system/`** - Universal agent system core
  - `agent.py` - UniversalAgent class that can embody any persona
  - `base.py` - SecureAgent base class with security validation
  - `factory.py` - Agent factory pattern for creating agent instances
  - `loader.py` - PersonaLoader for loading YAML persona specifications
  - `specs.py` - PersonaSpec data models and validation
  - `tools.py` - Tool registry and GitHub integration tools
  - `monitoring.py` - Agent monitoring and metrics collection

### Agent Implementations

- **`src/system/`** - Agent system implementations
  - `base/` - Base agent classes and interfaces
  - `orchestrator/` - Orchestrator agent for workflow coordination
  - `developer/` - Developer agent for code generation
  - `release/` - Release agent for GitHub integration
  - `tools/` - Agent-specific tools and utilities

### Workflow and Services

- **`src/workflows/`** - Temporal workflow definitions

  - `dev_team_workflow.py` - Main development team workflow orchestration
  - `activities.py` - Workflow activities for agent handoffs
  - `security_activities.py` - Security-focused workflow activities

- **`src/services/`** - Business logic services
  - `knowledge_service.py` - Qdrant vector database operations
  - `conflict_resolution_service.py` - Knowledge conflict resolution
  - `embedding_service.py` - Text embedding generation with OpenAI
  - `external_service_client.py` - External API client implementations

### Security and Configuration

- **`src/security/`** - Comprehensive security framework

  - `ai_agent_monitor.py` - Agent behavior monitoring and validation
  - `ai_agent_validator.py` - Input/output validation and scanning

- **`src/personas/`** - YAML-driven agent behavior configuration

  - `orchestrator.yaml` - Orchestrator agent persona specification
  - `dev.yaml` - Developer agent persona specification
  - `release.yaml` - Release agent persona specification

- **`src/config/`** - Configuration management

  - `settings.py` - Pydantic-based settings with validation

- **`src/utils/`** - Shared utilities
  - `logging.py` - Structured logging setup with correlation IDs
  - `circuit_breaker.py` - Circuit breaker pattern for external services

## Test Structure

- **`tests/`** - Comprehensive test suite (42 test files)
  - `unit/` - Unit tests organized by module
  - `integration/` - Integration tests for component interactions
  - `security/` - Security-focused tests and validation

## Scripts and Tools

- **`scripts/`** - Development and operational scripts
  - `setup.py` - Development environment setup
  - `security_check.py` - Security validation and scanning
  - `run_ci_locally.py` - Local CI execution
  - `temporal-config/` - Temporal workflow configuration

## Documentation

- **`docs/`** - Comprehensive documentation
  - `architecture/` - Architecture documentation and diagrams
  - `prd/` - Product requirements and specifications
  - `stories/` - User stories and epic definitions

## Configuration Files

- **`pyproject.toml`** - Poetry configuration with dependencies and tooling
- **`docker-compose.yml`** - Local development environment
- **`.env.example`** - Environment variable template
- **`.bmad-core/`** - BMAD method framework and agent definitions

## Key Architectural Patterns

1. **CLI-First Design** - Rich command-line interface as primary user interface
2. **Universal Agent System** - Single agent class that can embody any persona
3. **YAML-Driven Configuration** - Persona specifications in YAML for flexibility
4. **Security at Every Layer** - Comprehensive validation and monitoring
5. **Temporal Workflow Orchestration** - Durable, fault-tolerant agent coordination
6. **Vector Knowledge Management** - Local Qdrant database for semantic search
7. **Modular Architecture** - Clear separation of concerns across modules

## File Relationships

- **Entry Point**: `src/cli/main.py` → `src/system/agent.py` → `src/workflows/`
- **Agent Creation**: `src/system/factory.py` → `src/system/loader.py` → `src/personas/`
- **Workflow Execution**: `src/workflows/dev_team_workflow.py` → `src/services/`
- **Security Validation**: `src/security/` → All agent interactions
- **Knowledge Management**: `src/services/knowledge_service.py` → Qdrant vector database

This source tree represents the actual implemented structure of the Orchestra AI Agent System, providing a clear map for understanding the codebase organization and module relationships.
