# External APIs

## OpenAI API

- **Purpose:** AI model access for all agent operations
- **Documentation:** <https://platform.openai.com/docs/>
- **Base URL(s):** <https://api.openai.com/v1>
- **Authentication:** Bearer token (API key)
- **Rate Limits:** 10,000 requests/minute for GPT-4o

**Key Endpoints Used:**

- `POST /chat/completions` - Agent conversation processing
- `POST /embeddings` - Knowledge vectorization

**Integration Notes:** Centralized client with retry logic and rate limit handling

## GitHub API

- **Purpose:** Repository operations for code commits and Pull Request management
- **Documentation:** <https://docs.github.com/en/rest>
- **Base URL(s):** <https://api.github.com>
- **Authentication:** GitHub App or Personal Access Token
- **Rate Limits:** 5,000 requests/hour for authenticated requests

**Key Endpoints Used:**

- `POST /repos/{owner}/{repo}/git/blobs` - Create code files
- `POST /repos/{owner}/{repo}/git/commits` - Commit changes
- `POST /repos/{owner}/{repo}/pulls` - Create Pull Requests
- `GET /repos/{owner}/{repo}/contents/{path}` - Read existing code

**Integration Notes:** Implemented as OpenAI SDK tools within Release Agent

## Temporal Cloud API

- **Purpose:** Workflow orchestration, state management, and durability
- **Documentation:** <https://docs.temporal.io/>
- **Base URL(s):** Customer-specific Temporal Cloud endpoint
- **Authentication:** mTLS certificates or API keys
- **Rate Limits:** Based on Temporal Cloud plan

**Key Endpoints Used:**

- Workflow execution via Temporal SDK
- Workflow monitoring and signals
- Activity retry and failure handling

**Integration Notes:** Primary orchestration layer wrapping all agent handoffs

## Pinecone API

- **Purpose:** Vector database for semantic search and knowledge management
- **Documentation:** <https://docs.pinecone.io/>
- **Base URL(s):** <https://controller.{region}.pinecone.io>
- **Authentication:** API key
- **Rate Limits:** Based on Pinecone plan

**Key Endpoints Used:**

- `POST /query` - Semantic search for knowledge retrieval
- `POST /upsert` - Knowledge storage and updates
- `POST /delete` - Knowledge cleanup

**Integration Notes:** Centralized through Knowledge Service with connection pooling
