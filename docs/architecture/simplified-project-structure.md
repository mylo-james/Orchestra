# Simplified Project Structure

```plaintext
ai-dev-team-orchestrator/
├── src/
│   ├── cli/                    # Command-line interface
│   │   ├── __init__.py
│   │   ├── main.py            # Main CLI entry point
│   │   ├── commands.py        # CLI command definitions
│   │   └── output.py          # Rich output formatting
│   ├── agents/                 # Agent implementations with security
│   │   ├── __init__.py
│   │   ├── base/              # Base agent classes with security
│   │   │   ├── secure_agent.py
│   │   │   └── monitoring.py
│   │   ├── orchestrator/      # Orchestrator agent
│   │   │   ├── agent.py
│   │   │   ├── tools.py
│   │   │   └── security.py
│   │   ├── developer/         # Developer agent with code validation
│   │   │   ├── agent.py
│   │   │   ├── code_generator.py
│   │   │   └── code_validator.py
│   │   └── release/           # Release agent with GitHub security
│   │       ├── agent.py
│   │       ├── github_integration.py
│   │       └── security_scanner.py
│   ├── workflows/              # Temporal workflows
│   │   ├── __init__.py
│   │   ├── dev_team_workflow.py
│   │   ├── activities.py
│   │   └── security_activities.py
│   ├── services/               # Business logic services
│   │   ├── __init__.py
│   │   ├── knowledge_service.py
│   │   ├── workflow_service.py
│   │   ├── security_service.py
│   │   └── github_service.py
│   ├── models/                 # Data models with validation
│   │   ├── __init__.py
│   │   ├── workflow.py
│   │   ├── knowledge.py
│   │   ├── security.py
│   │   └── user.py
│   ├── security/               # Security framework
│   │   ├── __init__.py
│   │   ├── input_validator.py
│   │   ├── output_scanner.py
│   │   ├── code_analyzer.py
│   │   └── audit_logger.py
│   ├── config/                 # Secure configuration
│   │   ├── __init__.py
│   │   ├── settings.py
│   │   └── secrets.py
│   └── utils/                  # Shared utilities
│       ├── __init__.py
│       ├── logging.py
│       └── monitoring.py
├── tests/                      # Comprehensive test suite
│   ├── unit/
│   ├── integration/
│   ├── security/              # Security-focused tests
│   └── fixtures/
├── scripts/                    # Setup and utility scripts
│   ├── setup.py
│   ├── init_db.py
│   └── security_check.py
├── docs/                       # Documentation
│   ├── prd.md
│   ├── brief.md
│   ├── architecture.md
│   └── security.md
├── .env.example                # Environment template (no secrets)
├── pyproject.toml              # Poetry configuration
├── bandit.yaml                 # Security scanning config
├── .gitignore                  # Comprehensive gitignore with security patterns
└── README.md
```
