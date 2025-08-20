# Technical Assumptions

## Repository Structure: Monorepo

The AI Dev Team Orchestrator will be developed as a monorepo with clear separation between:

- Agent logic and behaviors
- Workflow orchestration layer
- Integration adapters (GitHub, communication platforms)
- Vector database and knowledge management layer
- User interface components

## Service Architecture

**CRITICAL DECISION:** The system will use OpenAI's Agents SDK for multi-agent orchestration within Temporal workflows, combining the benefits of both frameworks:

- **OpenAI Agents SDK:** Handles agent definition, handoffs, guardrails, and tracing
- **Temporal Workflows:** Provides durability, fault tolerance, and long-running process management
- **Architecture Pattern:** Temporal workflows orchestrate OpenAI agent handoff sequences
- **Deployment:** Agents run within Temporal activities for maximum reliability

## Testing Requirements

**CRITICAL DECISION:** The system requires a full testing pyramid including:

- Unit tests for agent logic and utility functions
- Integration tests for agent-to-agent handoffs and external API interactions
- End-to-end tests for complete workflow scenarios
- Manual testing procedures for validating generated code quality

## Additional Technical Assumptions and Requests

- **OpenAI Agents SDK** provides production-ready multi-agent framework with handoffs, guardrails, and observability
- **GPT-4o model** will be used as primary language model for all agents
- **Temporal Cloud** will provide workflow orchestration and durability for agent sequences
- **GitHub API** rate limits will accommodate expected usage patterns without significant delays
- **Development team** has expertise in Python/TypeScript for OpenAI SDK and Temporal integration
- **Cloud infrastructure** supports auto-scaling for Temporal workers and OpenAI API calls
- **Container orchestration** (Docker/Kubernetes) for production deployment of Temporal workers
- **Vector Database** (Pinecone, Weaviate, or Qdrant) with dynamic upsert capabilities and versioning
- **Embedding Model** (OpenAI text-embedding-3-large) for real-time vectorization and knowledge evolution
- **Knowledge Versioning System** for concurrent agent updates and conflict resolution
- **Real-time Knowledge Synchronization** ensuring agents see latest knowledge updates
- **Knowledge Quality Scoring** to validate and rank knowledge improvements
