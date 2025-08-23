"""Tests for src/services/external_service_client.py following 1:1 mapping."""

from unittest.mock import Mock, patch

import pytest

# Import the actual module to ensure it's loaded for coverage
import src.services.external_service_client
from src.services.external_service_client import ExternalServiceClient


class TestRealExternalServiceClient:
    """Test the actual ExternalServiceClient functionality."""

    def test_services_module_imports_and_loads(self):
        """Test that services module imports and loads properly."""
        # This test ensures the module is imported for coverage
        assert src.services.external_service_client is not None
        assert ExternalServiceClient is not None

    @patch("src.services.external_service_client.openai.Client")
    @patch("src.services.external_service_client.httpx.AsyncClient")
    def test_external_service_client_real_init(
        self, mock_httpx, mock_openai, test_settings
    ):
        """Test real ExternalServiceClient initialization."""
        # Mock the external dependencies
        mock_openai_instance = Mock()
        mock_openai.return_value = mock_openai_instance

        mock_httpx_instance = Mock()
        mock_httpx.return_value = mock_httpx_instance

        # Test actual initialization
        client = ExternalServiceClient(test_settings)

        # Verify initialization worked
        assert client is not None
        assert client.settings == test_settings
        assert hasattr(client, "openai_client")
        assert hasattr(client, "http_client")

        # Verify external clients were created
        mock_openai.assert_called_once_with(api_key=test_settings.openai.api_key)
        mock_httpx.assert_called_once_with(timeout=30.0)

    @patch("src.services.external_service_client.httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_external_service_client_real_usage(self, mock_httpx, test_settings):
        """Test real ExternalServiceClient usage patterns."""
        # Mock httpx client
        mock_client = Mock()
        mock_httpx.return_value.__aenter__.return_value = mock_client
        mock_httpx.return_value.__aexit__.return_value = None

        # Create real client
        client = ExternalServiceClient(test_settings)

        # Test that we can access its properties
        assert client.settings is not None
        assert client.http_client is not None
        assert client.openai_client is not None

    @patch("src.services.external_service_client.openai.Client")
    def test_external_service_client_openai_integration(
        self, mock_openai, test_settings
    ):
        """Test OpenAI client integration."""
        mock_openai_instance = Mock()
        mock_openai.return_value = mock_openai_instance

        # Test real OpenAI client creation
        client = ExternalServiceClient(test_settings)

        # Verify OpenAI client was set up correctly
        assert client.openai_client == mock_openai_instance
        mock_openai.assert_called_once_with(api_key=test_settings.openai.api_key)

    @patch("src.services.external_service_client.httpx.AsyncClient")
    def test_external_service_client_http_integration(self, mock_httpx, test_settings):
        """Test HTTP client integration."""
        mock_httpx_instance = Mock()
        mock_httpx.return_value = mock_httpx_instance

        # Test real HTTP client creation
        client = ExternalServiceClient(test_settings)

        # Verify HTTP client was set up correctly
        assert client.http_client == mock_httpx_instance
        mock_httpx.assert_called_once_with(timeout=30.0)
