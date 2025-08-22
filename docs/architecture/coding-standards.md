# Coding Standards

## Core Standards

- **Languages & Runtimes:** Python 3.12+ (backend), TypeScript 5.3+ (frontend)
- **Style & Linting:** Black + isort (Python), ESLint + Prettier (TypeScript)
- **Test Organization:** `*.test.ts` (frontend), `test_*.py` (backend)

## Naming Conventions

| Element              | Convention           | Example                |
| -------------------- | -------------------- | ---------------------- |
| **Components**       | PascalCase           | `ChatInterface.tsx`    |
| **Hooks**            | camelCase with 'use' | `useWorkflow.ts`       |
| **API Routes**       | kebab-case           | `/api/workflows`       |
| **Database Tables**  | snake_case           | `workflow_executions`  |
| **Python Classes**   | PascalCase           | `OrchestratorAgent`    |
| **Python Functions** | snake_case           | `process_user_request` |

## Critical Rules

- **Agent Tool Functions:** All agent tools must include comprehensive docstrings and type hints for OpenAI SDK schema generation
- **Vector Database Access:** Only Orchestrator agent may perform vector database operations - never direct access from other agents
- **Temporal Activities:** All external API calls (OpenAI, GitHub) and Qdrant operations must be wrapped in Temporal activities for durability
- **Error Context:** All exceptions must include correlation IDs for tracing across agent handoffs
- **Knowledge Updates:** All knowledge upserts must include version information and confidence scoring
- **Session Management:** Agent conversations must maintain session context through OpenAI SDK session management
- **Async Patterns:** All I/O operations must be async/await for optimal Temporal integration
