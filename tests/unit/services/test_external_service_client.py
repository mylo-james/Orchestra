"""Fixed tests for External Service Client using proper 4-step methodology.

Step 1: PRD Analysis - Epic 4.1 AC1-2 GitHub API client, FR5-6 GitHub integration, FR9 tools integration
Step 2: Code Analysis - Verified actual method signatures and async/sync patterns
Step 3: Test Analysis - Identified non-existent method calls and async/sync mismatches
Step 4: Align Misalignments - Create PRD-aligned tests that import/execute real code
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.services.external_service_client import ExternalServiceClient, SecureAIAgent


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

        with patch("src.services.external_service_client.logger") as mock_logger:
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
        from src.services.external_service_client import (
            get_circuit_breaker_stats,
            get_failing_services,
        )

        # Should be able to get circuit breaker stats
        stats = get_circuit_breaker_stats()
        assert isinstance(stats, dict)

        # Should be able to get failing services
        failing = get_failing_services()
        assert isinstance(failing, list)
