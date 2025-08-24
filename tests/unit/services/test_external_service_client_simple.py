"""Simplified tests for external service client."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from orchestra.services.external_service_client import (
    ExternalServiceClient,
    SecureAIAgent,
)
from orchestra.utils.circuit_breaker import CircuitBreakerError, CircuitState


class TestExternalServiceClient:
    """Test external service client basic functionality."""

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings."""
        settings = Mock()
        settings.openai.api_key = "test-openai-key"
        settings.github.token = "test-github-token"
        settings.github.repo = "test-org/test-repo"
        return settings

    @patch("orchestra.services.external_service_client.openai.Client")
    @patch("orchestra.services.external_service_client.httpx.AsyncClient")
    def test_initialization(self, mock_httpx, mock_openai, mock_settings):
        """Test service client initialization."""
        client = ExternalServiceClient(mock_settings)

        assert client.settings == mock_settings
        mock_openai.assert_called_once_with(api_key="test-openai-key")
        mock_httpx.assert_called_once_with(timeout=30.0)

    @patch("orchestra.services.external_service_client.openai.Client")
    @patch("orchestra.services.external_service_client.httpx.AsyncClient")
    @patch("orchestra.services.external_service_client.protect_external_service")
    def test_generate_code_with_openai(
        self, mock_protect, mock_httpx, mock_openai, mock_settings
    ):
        """Test OpenAI code generation."""
        # Mock the decorator to call the function directly
        mock_protect.side_effect = lambda service, fallback_result: lambda func: func

        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "def hello(): return 'world'"

        client = ExternalServiceClient(mock_settings)
        client.openai_client.chat.completions.create.return_value = mock_response

        result = client.generate_code_with_openai("Create hello function")

        assert result == "def hello(): return 'world'"
        client.openai_client.chat.completions.create.assert_called_once()

    @pytest.mark.asyncio
    @patch("orchestra.services.external_service_client.openai.Client")
    @patch("orchestra.services.external_service_client.httpx.AsyncClient")
    @patch("orchestra.services.external_service_client.protect_external_service_async")
    async def test_create_github_pr(
        self, mock_protect, mock_httpx, mock_openai, mock_settings
    ):
        """Test GitHub PR creation."""
        mock_protect.side_effect = lambda service, fallback_result: lambda func: func

        # Mock HTTP response
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": 123,
            "url": "https://github.com/test/pull/123",
        }

        client = ExternalServiceClient(mock_settings)
        client.http_client = AsyncMock()
        client.http_client.post = AsyncMock(return_value=mock_response)

        result = await client.create_github_pr("Test PR", "Description", "branch")

        assert result["id"] == 123
        assert result["url"] == "https://github.com/test/pull/123"

    @pytest.mark.asyncio
    @patch("orchestra.services.external_service_client.openai.Client")
    @patch("orchestra.services.external_service_client.httpx.AsyncClient")
    @patch("orchestra.services.external_service_client.protect_external_service_async")
    async def test_query_qdrant_knowledge(
        self, mock_protect, mock_httpx, mock_openai, mock_settings
    ):
        """Test Qdrant knowledge query."""
        mock_protect.side_effect = lambda service, fallback_result: lambda func: func

        client = ExternalServiceClient(mock_settings)
        result = await client.query_qdrant_knowledge("test query")

        assert len(result) == 2
        assert result[0]["id"] == "doc1"
        assert "test query" in result[0]["text"]

    @pytest.mark.asyncio
    @patch("orchestra.services.external_service_client.openai.Client")
    @patch("orchestra.services.external_service_client.httpx.AsyncClient")
    @patch("orchestra.services.external_service_client.protect_external_service_async")
    async def test_start_temporal_workflow(
        self, mock_protect, mock_httpx, mock_openai, mock_settings
    ):
        """Test Temporal workflow start."""
        mock_protect.side_effect = lambda service, fallback_result: lambda func: func

        client = ExternalServiceClient(mock_settings)
        result = await client.start_temporal_workflow(
            "test_workflow", {"param": "value"}
        )

        assert result["status"] == "started"
        assert result["workflow_type"] == "test_workflow"
        assert "workflow_" in result["workflow_id"]

    @pytest.mark.asyncio
    @patch("orchestra.services.external_service_client.openai.Client")
    @patch("orchestra.services.external_service_client.httpx.AsyncClient")
    async def test_close(self, mock_httpx, mock_openai, mock_settings):
        """Test HTTP client cleanup."""
        client = ExternalServiceClient(mock_settings)
        client.http_client = AsyncMock()

        await client.close()

        client.http_client.aclose.assert_called_once()


class TestSecureAIAgent:
    """Test SecureAIAgent functionality."""

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings."""
        settings = Mock()
        settings.openai.api_key = "test-key"
        settings.github.token = "test-token"
        settings.github.repo = "test-org/test-repo"
        return settings

    @patch("orchestra.services.external_service_client.ExternalServiceClient")
    def test_initialization(self, mock_client_class, mock_settings):
        """Test SecureAIAgent initialization."""
        agent = SecureAIAgent("test-agent", mock_settings)

        assert agent.agent_id == "test-agent"
        mock_client_class.assert_called_once_with(mock_settings)

    @pytest.mark.asyncio
    @patch("orchestra.services.external_service_client.ExternalServiceClient")
    async def test_generate_and_commit_code_success(
        self, mock_client_class, mock_settings
    ):
        """Test successful code generation workflow."""
        # Mock external client
        mock_client = Mock()
        mock_client.query_qdrant_knowledge = AsyncMock(return_value=[{"id": "doc1"}])
        mock_client.generate_code_with_openai_async = AsyncMock(
            return_value="def test(): pass"
        )
        mock_client.create_github_pr = AsyncMock(return_value={"id": 123})
        mock_client.start_temporal_workflow = AsyncMock(
            return_value={"workflow_id": "wf123"}
        )
        mock_client_class.return_value = mock_client

        agent = SecureAIAgent("test-agent", mock_settings)
        result = await agent.generate_and_commit_code("Create test function")

        assert result["success"] is True
        assert result["agent_id"] == "test-agent"
        assert result["generated_code"] == "def test(): pass"
        assert result["fallbacks_used"] == []

    @pytest.mark.asyncio
    @patch("orchestra.services.external_service_client.ExternalServiceClient")
    async def test_generate_and_commit_code_with_fallbacks(
        self, mock_client_class, mock_settings
    ):
        """Test code generation workflow with circuit breaker fallbacks."""
        # Mock external client with circuit breaker errors
        mock_client = Mock()
        mock_client.query_qdrant_knowledge = AsyncMock(
            side_effect=CircuitBreakerError("qdrant", CircuitState.OPEN, "Qdrant down")
        )
        mock_client.generate_code_with_openai_async = AsyncMock(
            side_effect=CircuitBreakerError("openai", CircuitState.OPEN, "OpenAI down")
        )
        mock_client.create_github_pr = AsyncMock(
            side_effect=CircuitBreakerError("github", CircuitState.OPEN, "GitHub down")
        )
        mock_client.start_temporal_workflow = AsyncMock(
            side_effect=CircuitBreakerError(
                "temporal", CircuitState.OPEN, "Temporal down"
            )
        )
        mock_client_class.return_value = mock_client

        agent = SecureAIAgent("test-agent", mock_settings)
        result = await agent.generate_and_commit_code("Create test function")

        assert result["success"] is True
        assert len(result["fallbacks_used"]) == 4
        assert "qdrant_fallback" in result["fallbacks_used"]
        assert "openai_fallback" in result["fallbacks_used"]
        assert "github_fallback" in result["fallbacks_used"]
        assert "temporal_fallback" in result["fallbacks_used"]

        # Check fallback values
        assert result["knowledge_context"] == []
        assert "Code generation temporarily unavailable" in result["generated_code"]
        assert result["pr_created"]["error"] == "GitHub temporarily unavailable"
        assert result["workflow_started"]["status"] == "degraded_mode"

    @pytest.mark.asyncio
    @patch("orchestra.services.external_service_client.ExternalServiceClient")
    async def test_generate_and_commit_code_with_exception(
        self, mock_client_class, mock_settings
    ):
        """Test code generation workflow with unexpected exception."""
        # Mock external client to raise unexpected exception
        mock_client = Mock()
        mock_client.query_qdrant_knowledge = AsyncMock(
            side_effect=Exception("Unexpected error")
        )
        mock_client_class.return_value = mock_client

        agent = SecureAIAgent("test-agent", mock_settings)
        result = await agent.generate_and_commit_code("Create test function")

        assert result["success"] is False
        assert result["error"] == "Unexpected error"


class TestCircuitBreakerIntegration:
    """Test circuit breaker integration."""

    @pytest.mark.asyncio
    @patch("orchestra.services.external_service_client.get_openai_circuit_breaker")
    @patch("orchestra.services.external_service_client.get_temporal_circuit_breaker")
    @patch("orchestra.services.external_service_client.get_qdrant_circuit_breaker")
    @patch("orchestra.services.external_service_client.get_github_circuit_breaker")
    @patch("orchestra.services.external_service_client.get_circuit_breaker_stats")
    @patch("orchestra.services.external_service_client.get_failing_services")
    async def test_circuit_breaker_test_function(
        self,
        mock_failing,
        mock_stats,
        mock_github,
        mock_qdrant,
        mock_temporal,
        mock_openai,
    ):
        """Test the circuit breaker test function."""
        from orchestra.services.external_service_client import test_circuit_breakers

        # Mock circuit breaker states
        mock_openai.return_value.state.value = "CLOSED"
        mock_temporal.return_value.state.value = "CLOSED"
        mock_qdrant.return_value.state.value = "CLOSED"
        mock_github.return_value.state.value = "CLOSED"

        mock_stats.return_value = {"openai": {}, "temporal": {}}
        mock_failing.return_value = []

        # Should run without errors
        await test_circuit_breakers()

        # Verify all circuit breakers were checked
        mock_openai.assert_called_once()
        mock_temporal.assert_called_once()
        mock_qdrant.assert_called_once()
        mock_github.assert_called_once()
        mock_stats.assert_called_once()
        mock_failing.assert_called_once()
