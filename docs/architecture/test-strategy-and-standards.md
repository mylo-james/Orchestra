# Test Strategy and Standards

## Testing Philosophy

- **Approach:** Test-Driven Development (TDD) for critical agent workflows with comprehensive integration testing
- **Coverage Goals:** 90% unit test coverage, 80% integration coverage, 100% critical path coverage
- **Test Pyramid:** Heavy unit testing, focused integration tests, targeted E2E for user journeys

## Test Types and Organization

### Unit Tests

- **Framework:** pytest (backend), Vitest (frontend)
- **File Convention:** `test_*.py` (backend), `*.test.ts` (frontend)
- **Location:** Adjacent to source files in `tests/` directories
- **Mocking Library:** pytest-mock (backend), Vitest mocks (frontend)
- **Coverage Requirement:** 90% for agent logic, 80% for utilities

**AI Agent Requirements:**

- Generate tests for all agent tool functions
- Cover handoff scenarios and error conditions
- Follow AAA pattern (Arrange, Act, Assert)
- Mock all external dependencies (OpenAI, GitHub, Pinecone)

### Integration Tests

- **Scope:** Agent handoffs, Temporal workflow coordination, external API integration
- **Location:** `apps/backend/tests/integration/`
- **Test Infrastructure:**
  - **PostgreSQL:** Testcontainers for isolated database testing
  - **Temporal:** Local Temporal server for workflow testing
  - **Vector DB:** Pinecone test environment with isolated indexes
  - **External APIs:** Mocked responses using responses library

### End-to-End Tests

- **Framework:** Playwright
- **Scope:** Complete user journeys from request to PR creation
- **Environment:** Staging environment with real external services
- **Test Data:** Dedicated test repositories and knowledge base

## Test Data Management

- **Strategy:** Factory pattern for test data generation with realistic agent contexts
- **Fixtures:** JSON fixtures for agent responses and knowledge base content
- **Factories:** Programmatic generation of workflow and knowledge test data
- **Cleanup:** Automatic cleanup of test workflows and knowledge entries

## Continuous Testing

- **CI Integration:** All tests run on PR creation, deployment gates on test success
- **Performance Tests:** Agent response time validation, workflow completion metrics
- **Security Tests:** Input validation testing, auth flow verification
