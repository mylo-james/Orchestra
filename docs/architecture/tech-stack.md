# Tech Stack

## Technology Stack Table

| Category                   | Technology              | Version        | Purpose                                              | Rationale                                                                            |
| -------------------------- | ----------------------- | -------------- | ---------------------------------------------------- | ------------------------------------------------------------------------------------ |
| **Primary Language**       | Python                  | 3.12.0         | Agent orchestration and CLI                          | Excellent OpenAI SDK support, strong Temporal integration, mature security libraries |
| **CLI Framework**          | Typer                   | 0.9.0          | Command-line interface                               | Type-safe CLI with excellent developer experience and security validation            |
| **CLI Output**             | Rich                    | 13.7.0         | Beautiful CLI output formatting                      | Enhanced user experience with progress bars and formatted output                     |
| **Agent Framework**        | OpenAI Agents SDK       | 1.0.0          | Multi-agent coordination                             | Native handoffs, built-in guardrails, observability, official OpenAI support         |
| **AI Models**              | GPT-4o                  | latest         | Primary language model for all agents                | Latest production model with improved safety and reasoning capabilities              |
| **Workflow Orchestration** | Temporal                | 1.24.0         | Durable workflow execution                           | Production-ready agent orchestration, fault tolerance, state persistence             |
| **Vector Database**        | Pinecone                | 2.2.4          | Project knowledge and semantic search                | Specialized for AI applications, excellent performance, security features            |
| **Embedding Model**        | text-embedding-3-large  | latest         | Knowledge vectorization                              | Latest OpenAI embedding model with improved safety and accuracy                      |
| **Local Database**         | SQLite                  | 3.45.0         | Local workflow and metadata storage                  | Simple, reliable, perfect for CLI MVP development                                    |
| **Input Validation**       | Pydantic                | 2.5.0          | Structured input validation and safety               | Comprehensive validation with security features and type safety                      |
| **Code Security Analysis** | Bandit                  | 1.7.5          | Python security vulnerability scanning               | Industry-standard static analysis for generated code security                        |
| **Code Quality**           | Ruff                    | 0.1.9          | Fast Python linting and formatting                   | Modern, fast linting with security-focused rules                                     |
| **Git Integration**        | GitPython               | 3.1.40         | Local repository operations                          | Secure local Git operations with validation and safety checks                        |
| **HTTP Client**            | httpx                   | 0.26.0         | Async HTTP client for API calls                      | Modern async client with excellent security and retry capabilities                   |
| **Testing Framework**      | pytest + pytest-asyncio | 7.4.4 + 0.23.0 | Comprehensive testing with async support             | Robust testing for agent workflows and security validation                           |
| **Security Framework**     | python-security         | 1.7.1          | Security utilities and validators                    | Comprehensive security validation toolkit for AI applications                        |
| **Configuration**          | pydantic-settings       | 2.1.0          | Secure configuration management                      | Type-safe config with secrets protection and validation                              |
| **Logging**                | structlog               | 23.2.0         | Structured logging with correlation IDs              | Security-focused logging with audit trails and correlation                           |
| **Dependency Management**  | Poetry                  | 1.7.1          | Python dependency and virtual environment management | Secure dependency resolution and lock file management                                |
