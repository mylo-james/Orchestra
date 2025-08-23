# Component Diagram (Current v0.1.0 Implementation)

```mermaid
graph TB
  CLI[Orchestra CLI] --> Commands[CLI Commands]
  Commands --> AgentCmd[Agent Commands]
  Commands --> WorkflowCmd[Workflow Commands]
  Commands --> ConfigCmd[Config Commands]
  Commands --> DevCmd[Dev Commands]

  AgentCmd --> UniversalAgent[UniversalAgent]
  UniversalAgent --> PersonaLoader[PersonaLoader]
  PersonaLoader --> YAMLPersonas[YAML Personas]

  subgraph "Persona System"
    YAMLPersonas --> Orchestrator[orchestrator.yaml<br/>Brendan]
    YAMLPersonas --> Developer[dev.yaml<br/>Alex]
    YAMLPersonas --> Release[release.yaml<br/>Riley]
  end

  UniversalAgent --> Tools[Tools & Services]
  Tools --> GitHub[GitHub API]
  Tools --> OpenAI[OpenAI API]
  Tools --> Temporal[Temporal Workflows]

  UniversalAgent --> Security[Security Framework]
  Security --> Validation[Input Validation]
  Security --> Monitoring[Security Monitoring]
  Security --> Audit[Audit Logging]

  CLI --> Qdrant[(Qdrant Vector DB)]
  CLI --> PostgreSQL[(PostgreSQL)]
```

## Current Architecture Notes

This diagram shows the **current v0.1.0 implementation**. The system uses:

- **Single UniversalAgent**: Dynamically configured through YAML personas
- **Three Active Personas**: Orchestrator, Developer, and Release specialists
- **Command-Driven Interface**: Each persona defines specific commands and execution patterns
- **Integrated Services**: Temporal, Qdrant, and PostgreSQL for workflow orchestration and data storage
