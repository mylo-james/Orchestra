# Components

## Orchestrator Service

**Responsibility:** Central coordination hub managing user interactions, workflow orchestration, and knowledge management

**Key Interfaces:**

- `/api/chat` - User conversation interface
- `/api/workflows` - Workflow management
- `/internal/knowledge` - Vector database operations

**Dependencies:** OpenAI Agents SDK, Temporal Client, Pinecone Client, FastAPI

**Technology Stack:** Python 3.12 + FastAPI + OpenAI Agents SDK + Temporal SDK

## Developer Agent Service

**Responsibility:** Specialized code generation and modification based on implementation plans

**Key Interfaces:**

- Internal handoff from Orchestrator
- Code generation tools
- Repository analysis tools

**Dependencies:** OpenAI API, GitHub API (read-only), Code analysis tools

**Technology Stack:** Python 3.12 + OpenAI Agents SDK + GitHub API client

## Release Agent Service

**Responsibility:** Repository operations, Pull Request creation, and deployment validation

**Key Interfaces:**

- Internal handoff from Orchestrator
- GitHub API operations
- Deployment validation tools

**Dependencies:** GitHub API, CI/CD integration tools, Code quality validators

**Technology Stack:** Python 3.12 + OpenAI Agents SDK + GitHub API client

## Vector Knowledge Service

**Responsibility:** Dynamic project knowledge storage, retrieval, and evolution management

**Key Interfaces:**

- `/knowledge/query` - Semantic search
- `/knowledge/upsert` - Knowledge updates
- `/knowledge/evolution` - Version management

**Dependencies:** Pinecone, OpenAI Embeddings API, PostgreSQL

**Technology Stack:** Python 3.12 + Pinecone + text-embedding-3-large

## Frontend Application

**Responsibility:** User interface for agent interaction, workflow monitoring, and result visualization

**Key Interfaces:**

- Chat interface for user-agent communication
- Workflow status dashboard
- Code review and PR integration views

**Dependencies:** Orchestrator API, Authentication service

**Technology Stack:** Next.js 14 + TypeScript + Tailwind CSS + shadcn/ui

## Component Diagrams

```mermaid
graph TB
    subgraph "Frontend Layer"
        UI[React Components]
        State[Zustand Store]
        API[API Client]
    end

    subgraph "Backend Services"
        Orch[Orchestrator Service]
        Dev[Developer Agent]
        Rel[Release Agent]
        Know[Knowledge Service]
    end

    subgraph "External Services"
        OpenAI[OpenAI API]
        Temporal[Temporal Cloud]
        Pinecone[Pinecone]
        GitHub[GitHub API]
    end

    UI --> State
    State --> API
    API --> Orch

    Orch --> Know
    Orch --> |Temporal Workflow| Dev
    Orch --> |Temporal Workflow| Rel

    Orch --> OpenAI
    Dev --> OpenAI
    Rel --> OpenAI

    Orch --> Temporal
    Know --> Pinecone
    Rel --> GitHub
```
