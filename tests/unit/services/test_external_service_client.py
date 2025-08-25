"""Fixed tests for External Service Client using proper 4-step methodology.

Step 1: PRD Analysis - Epic 4.1 AC1-2 GitHub API client, FR5-6 GitHub integration, FR9 tools integration
Step 2: Code Analysis - Verified actual method signatures and async/sync patterns
Step 3: Test Analysis - Identified non-existent method calls and async/sync mismatches
Step 4: Align Misalignments - Create PRD-aligned tests that import/execute real code
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from orchestra.services.external_service_client import (
    ExternalServiceClient,
    SecureAIAgent,
)


class TestExternalServiceClientInitialization:
    """Test client initialization with actual implementation."""

    def test_client_initialization(self):
        """Test client initializes with required components (Epic 4.1 AC1)."""
        mock_settings = Mock()
        mock_settings.openai.api_key = "test-api-key"

        # Test actual initialization - no over-mocking
        client = ExternalServiceClient(mock_settings)

        assert client.settings == mock_settings
        assert client.openai_client is not None
        assert client.http_client is not None

    def test_client_initialization_logging(self):
        """Test client logs initialization properly."""
        mock_settings = Mock()
        mock_settings.openai.api_key = "test-api-key"

        with patch("orchestra.services.external_service_client.logger") as mock_logger:
            ExternalServiceClient(mock_settings)

            mock_logger.info.assert_called_with(
                "External service client initialized with circuit breaker protection"
            )


class TestOpenAICodeGeneration:
    """Test OpenAI code generation with actual implementation."""

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings for testing."""
        settings = Mock()
        settings.openai.api_key = "test-api-key"
        return settings

    @pytest.fixture
    def client(self, mock_settings):
        """Create client instance for testing."""
        return ExternalServiceClient(mock_settings)

    def test_generate_code_with_openai_sync(self, client):
        """Test sync code generation method (actual implementation)."""
        # Mock OpenAI client response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "def hello(): return 'Hello'"

        with patch.object(
            client.openai_client.chat.completions, "create"
        ) as mock_create:
            mock_create.return_value = mock_response

            # Test actual method signature and execution
            result = client.generate_code_with_openai("Create a hello function")

            assert isinstance(result, str)
            assert "def hello" in result
            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_code_with_openai_async(self, client):
        """Test async code generation method (actual implementation)."""
        # Mock OpenAI client response for async method
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = (
            "async def hello(): return 'Hello Async'"
        )

        with patch.object(
            client.openai_client.chat.completions, "create"
        ) as mock_create:
            # For async methods, need AsyncMock
            mock_create.return_value = AsyncMock(return_value=mock_response)()

            # Test actual async method
            result = await client.generate_code_with_openai_async(
                "Create async hello function"
            )

            assert isinstance(result, str)
            assert "async def hello" in result
            mock_create.assert_called_once()


class TestGitHubIntegration:
    """Test GitHub PR creation with actual implementation (Epic 4.1 AC2)."""

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings for GitHub testing."""
        settings = Mock()
        settings.openai.api_key = "test-api-key"
        settings.github.token = "test-github-token"
        settings.github.owner = "test-owner"
        settings.github.repo = "test-repo"
        return settings

    @pytest.fixture
    def client(self, mock_settings):
        """Create client for GitHub testing."""
        return ExternalServiceClient(mock_settings)

    @pytest.mark.asyncio
    async def test_create_github_pr_async_method(self, client):
        """Test GitHub PR creation with CORRECT async method (FR6)."""
        # Mock httpx response for actual GitHub API call
        mock_response = Mock()
        mock_response.json.return_value = {
            "html_url": "https://github.com/test/repo/pull/1",
            "number": 1,
            "title": "Test PR",
        }
        mock_response.status_code = 201

        with patch.object(client.http_client, "post") as mock_post:
            mock_post.return_value = mock_response

            # Test ACTUAL async method signature
            result = await client.create_github_pr(
                title="Test PR", description="Test PR description", branch="test-branch"
            )

            # Verify actual return format
            assert isinstance(result, dict)
            assert "html_url" in result
            assert result["html_url"] == "https://github.com/test/repo/pull/1"
            mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_github_pr_error_handling(self, client):
        """Test PR creation error handling (Epic 4.1 AC5)."""
        # Mock HTTP error response
        with patch.object(client.http_client, "post") as mock_post:
            mock_post.side_effect = Exception("GitHub API error")

            # Should handle errors gracefully per circuit breaker pattern
            with pytest.raises(Exception):
                await client.create_github_pr(
                    title="Test PR",
                    description="Test description",
                    branch="test-branch",
                )


class TestClientLifecycle:
    """Test client lifecycle management with actual implementation."""

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings for lifecycle testing."""
        settings = Mock()
        settings.openai.api_key = "test-api-key"
        return settings

    @pytest.fixture
    def client(self, mock_settings):
        """Create client for lifecycle testing."""
        return ExternalServiceClient(mock_settings)

    @pytest.mark.asyncio
    async def test_close_method_actual_signature(self, client):
        """Test client close method with CORRECT signature (not aclose)."""
        # Mock http_client.aclose method
        with patch.object(client.http_client, "aclose") as mock_aclose:
            # Test actual method name: close (not aclose)
            await client.close()

            # Should call http_client.aclose internally
            mock_aclose.assert_called_once()

    def test_client_lifecycle_methods_exist(self, client):
        """Test that client has proper lifecycle methods."""
        # Verify actual methods exist (not assumed ones)
        assert hasattr(client, "close")  # Actual method
        assert callable(client.close)


class TestPRDComplianceValidation:
    """Test compliance with actual PRD requirements."""

    def test_epic_4_1_ac1_github_api_client_implementation(self):
        """Test Epic 4.1 AC1: GitHub API client implemented as OpenAI SDK tool functions."""
        mock_settings = Mock()
        mock_settings.openai.api_key = "test-api-key"

        # Test actual client implementation
        client = ExternalServiceClient(mock_settings)

        # Should have GitHub integration capabilities
        assert hasattr(client, "create_github_pr")
        assert callable(client.create_github_pr)

        # Should have OpenAI integration
        assert hasattr(client, "generate_code_with_openai")
        assert hasattr(client, "generate_code_with_openai_async")

    def test_fr6_pull_requests_creation(self):
        """Test FR6: Open Pull Requests with auto-generated descriptions."""
        mock_settings = Mock()
        mock_settings.openai.api_key = "test-api-key"

        client = ExternalServiceClient(mock_settings)

        # Should have PR creation capability
        assert hasattr(client, "create_github_pr")
        assert callable(client.create_github_pr)

    def test_fr9_github_api_operations_as_tools(self):
        """Test FR9: Integrate GitHub API operations as tools within agents."""
        mock_settings = Mock()
        mock_settings.openai.api_key = "test-api-key"

        # Test both client and agent integration
        client = ExternalServiceClient(mock_settings)
        agent = SecureAIAgent("test-agent", mock_settings)

        # Client should provide GitHub operations
        assert hasattr(client, "create_github_pr")

        # Agent should integrate these operations
        assert hasattr(agent, "generate_and_commit_code")
        assert hasattr(agent, "external_client")  # Actual attribute name


class TestCircuitBreakerIntegration:
    """Test circuit breaker integration with actual implementation."""

    def test_circuit_breaker_protection_applied(self):
        """Test that circuit breaker protection is properly applied to methods."""
        mock_settings = Mock()
        mock_settings.openai.api_key = "test-api-key"

        client = ExternalServiceClient(mock_settings)

        # Key methods should have circuit breaker protection
        protected_methods = [
            "generate_code_with_openai",
        ]

        for method_name in protected_methods:
            method = getattr(client, method_name)
            # Should be decorated with circuit breaker
            assert hasattr(
                method, "__wrapped__"
            ), f"{method_name} should have circuit breaker protection"

    def test_circuit_breaker_functionality(self):
        """Test circuit breaker functionality integration."""
        # Test that circuit breaker functions are properly integrated
        from orchestra.services.external_service_client import (
            get_circuit_breaker_stats,
            get_failing_services,
        )

        # Should be able to get circuit breaker stats
        stats = get_circuit_breaker_stats()
        assert isinstance(stats, dict)

        # Should be able to get failing services
        failing = get_failing_services()
        assert isinstance(failing, list)


class TestQdrantVectorDatabase:
    """Test Qdrant vector database integration (FR5 - knowledge integration)."""

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings for testing."""
        settings = Mock()
        settings.openai.api_key = "test-api-key"
        return settings

    @pytest.fixture
    def client(self, mock_settings):
        """Create client instance for testing."""
        return ExternalServiceClient(mock_settings)

    @pytest.mark.asyncio
    async def test_query_qdrant_knowledge_success(self, client):
        """Test Qdrant knowledge query success (FR5)."""
        result = await client.query_qdrant_knowledge("test query")

        # Verify return structure matches PRD knowledge requirements
        assert isinstance(result, list)
        assert len(result) > 0
        assert all("id" in item for item in result)
        assert all("score" in item for item in result)
        assert all("text" in item for item in result)

    @pytest.mark.asyncio
    async def test_query_qdrant_knowledge_with_top_k(self, client):
        """Test Qdrant query with custom top_k parameter."""
        result = await client.query_qdrant_knowledge("test query", top_k=3)

        assert isinstance(result, list)
        # In the mock implementation, it always returns 2 items

    @pytest.mark.asyncio
    async def test_query_qdrant_knowledge_exception_handling(self, client):
        """Test Qdrant exception handling."""
        with patch("asyncio.sleep", side_effect=Exception("Qdrant connection error")):
            with pytest.raises(Exception, match="Qdrant connection error"):
                await client.query_qdrant_knowledge("test query")


class TestTemporalWorkflow:
    """Test Temporal workflow management (FR8 - adaptive workflows)."""

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings for testing."""
        settings = Mock()
        settings.openai.api_key = "test-api-key"
        return settings

    @pytest.fixture
    def client(self, mock_settings):
        """Create client instance for testing."""
        return ExternalServiceClient(mock_settings)

    @pytest.mark.asyncio
    async def test_start_temporal_workflow_success(self, client):
        """Test Temporal workflow start success (FR8)."""
        workflow_input = {"task": "process_data", "params": {"limit": 100}}

        result = await client.start_temporal_workflow("data_processing", workflow_input)

        # Verify return structure matches PRD workflow requirements
        assert isinstance(result, dict)
        assert "workflow_id" in result
        assert "status" in result
        assert "workflow_type" in result
        assert result["status"] == "started"
        assert result["workflow_type"] == "data_processing"

    @pytest.mark.asyncio
    async def test_start_temporal_workflow_exception_handling(self, client):
        """Test Temporal workflow exception handling."""
        with patch("asyncio.sleep", side_effect=Exception("Temporal connection error")):
            with pytest.raises(Exception, match="Temporal connection error"):
                await client.start_temporal_workflow("test_workflow", {})


class TestSecureAIAgent:
    """Test SecureAIAgent class (agent coordination functionality)."""

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings for testing."""
        settings = Mock()
        settings.openai.api_key = "test-api-key"
        settings.github.token = "test-token"
        settings.github.repo = "test/repo"
        return settings

    @pytest.fixture
    def agent(self, mock_settings):
        """Create SecureAIAgent instance."""
        return SecureAIAgent("test-agent", mock_settings)

    def test_secure_ai_agent_initialization(self, agent):
        """Test SecureAIAgent initialization."""
        assert agent.agent_id == "test-agent"
        assert agent.external_client is not None
        assert isinstance(agent.external_client, ExternalServiceClient)

    @pytest.mark.asyncio
    async def test_generate_and_commit_code_success_flow(self, agent):
        """Test full generate and commit code workflow success."""
        # Mock all external service calls to simulate success
        with (
            patch.object(
                agent.external_client,
                "query_qdrant_knowledge",
                return_value=[{"text": "context"}],
            ),
            patch.object(
                agent.external_client,
                "generate_code_with_openai_async",
                return_value="def test(): pass",
            ),
            patch.object(
                agent.external_client,
                "create_github_pr",
                return_value={"html_url": "test-url"},
            ),
            patch.object(
                agent.external_client,
                "start_temporal_workflow",
                return_value={"workflow_id": "test-wf"},
            ),
        ):
            result = await agent.generate_and_commit_code("Create a test function")

            # Verify successful workflow completion
            assert result["success"] is True
            assert result["agent_id"] == "test-agent"
            assert result["generated_code"] == "def test(): pass"
            assert result["pr_created"]["html_url"] == "test-url"
            assert result["workflow_started"]["workflow_id"] == "test-wf"
            assert len(result["fallbacks_used"]) == 0

    @pytest.mark.asyncio
    async def test_generate_and_commit_code_with_fallbacks(self, agent):
        """Test workflow with circuit breaker fallbacks."""
        from orchestra.utils.circuit_breaker import CircuitBreakerError, CircuitState

        # Mock some services to fail with circuit breaker errors
        with (
            patch.object(
                agent.external_client,
                "query_qdrant_knowledge",
                side_effect=CircuitBreakerError(
                    "qdrant_service", CircuitState.OPEN, "Qdrant down"
                ),
            ),
            patch.object(
                agent.external_client,
                "generate_code_with_openai_async",
                side_effect=CircuitBreakerError(
                    "openai_service", CircuitState.OPEN, "OpenAI down"
                ),
            ),
            patch.object(
                agent.external_client,
                "create_github_pr",
                return_value={"html_url": "test-url"},
            ),
            patch.object(
                agent.external_client,
                "start_temporal_workflow",
                return_value={"workflow_id": "test-wf"},
            ),
        ):
            result = await agent.generate_and_commit_code("Create a test function")

            # Verify fallbacks were used
            assert "qdrant_fallback" in result["fallbacks_used"]
            assert "openai_fallback" in result["fallbacks_used"]
            assert result["knowledge_context"] == []
            assert (
                "# Code generation temporarily unavailable" in result["generated_code"]
            )

    @pytest.mark.asyncio
    async def test_generate_and_commit_code_total_failure(self, agent):
        """Test workflow when all critical services fail."""
        from orchestra.utils.circuit_breaker import CircuitBreakerError, CircuitState

        # Mock all services to fail
        with (
            patch.object(
                agent.external_client,
                "query_qdrant_knowledge",
                side_effect=CircuitBreakerError(
                    "qdrant_service", CircuitState.OPEN, "Qdrant down"
                ),
            ),
            patch.object(
                agent.external_client,
                "generate_code_with_openai_async",
                side_effect=CircuitBreakerError(
                    "openai_service", CircuitState.OPEN, "OpenAI down"
                ),
            ),
            patch.object(
                agent.external_client,
                "create_github_pr",
                side_effect=CircuitBreakerError(
                    "github_service", CircuitState.OPEN, "GitHub down"
                ),
            ),
            patch.object(
                agent.external_client,
                "start_temporal_workflow",
                side_effect=CircuitBreakerError(
                    "temporal_service", CircuitState.OPEN, "Temporal down"
                ),
            ),
        ):
            result = await agent.generate_and_commit_code("Create a test function")

            # Verify graceful degradation - system still reports success with fallbacks
            assert (
                result["success"] is True
            )  # System degrades gracefully rather than failing
            assert len(result["fallbacks_used"]) == 4
            assert "qdrant_fallback" in result["fallbacks_used"]
            assert "openai_fallback" in result["fallbacks_used"]
            assert "github_fallback" in result["fallbacks_used"]
            assert "temporal_fallback" in result["fallbacks_used"]

            # Verify fallback responses
            assert "Code generation temporarily unavailable" in result["generated_code"]
            assert result["pr_created"]["error"] == "GitHub temporarily unavailable"
            assert result["workflow_started"]["status"] == "degraded_mode"


class TestExceptionHandling:
    """Test exception handling in external service methods."""

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings for testing."""
        settings = Mock()
        settings.openai.api_key = "test-api-key"
        return settings

    @pytest.fixture
    def client(self, mock_settings):
        """Create client instance for testing."""
        return ExternalServiceClient(mock_settings)

    def test_generate_code_with_openai_sync_exception(self, client):
        """Test sync OpenAI code generation exception handling."""
        with patch.object(
            client.openai_client.chat.completions,
            "create",
            side_effect=Exception("API Error"),
        ):
            with pytest.raises(Exception, match="API Error"):
                client.generate_code_with_openai("test prompt")

    @pytest.mark.asyncio
    async def test_generate_code_with_openai_async_exception(self, client):
        """Test async OpenAI code generation exception handling."""
        with patch.object(
            client.openai_client.chat.completions,
            "create",
            side_effect=Exception("Async API Error"),
        ):
            with pytest.raises(Exception, match="Async API Error"):
                await client.generate_code_with_openai_async("test prompt")

    @pytest.mark.asyncio
    async def test_create_github_pr_exception(self, client):
        """Test GitHub PR creation exception handling."""
        client.settings.github = Mock()
        client.settings.github.token = "test-token"
        client.settings.github.repo = "test/repo"

        with patch.object(
            client.http_client, "post", side_effect=Exception("GitHub API Error")
        ):
            with pytest.raises(Exception, match="GitHub API Error"):
                await client.create_github_pr("title", "description", "branch")


class TestConnectionManagement:
    """Test connection management and cleanup."""

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings for testing."""
        settings = Mock()
        settings.openai.api_key = "test-api-key"
        return settings

    @pytest.fixture
    def client(self, mock_settings):
        """Create client instance for testing."""
        return ExternalServiceClient(mock_settings)

    @pytest.mark.asyncio
    async def test_client_close_cleanup(self, client):
        """Test client connection cleanup."""
        with patch.object(client.http_client, "aclose") as mock_close:
            await client.close()
            mock_close.assert_called_once()
