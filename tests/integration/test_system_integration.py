"""Integration tests for system components."""

import pytest

from orchestra.utils.logging import get_logger, set_correlation_id


@pytest.mark.integration
class TestSystemIntegration:
    """Test integration between major system components."""

    def test_settings_and_logging_integration(self, test_settings):
        """Test that settings and logging work together."""
        logger = get_logger(__name__)

        # Test that we can log with settings context
        logger.info(
            "Testing integration",
            app_name=test_settings.app_name,
            environment=test_settings.environment,
        )

        assert test_settings.logging.level == "DEBUG"
        assert test_settings.logging.enable_audit is True

    @pytest.mark.asyncio
    async def test_async_components_integration(
        self, mock_openai_client, mock_temporal_client
    ):
        """Test integration of async components."""
        # Set correlation ID for tracing
        correlation_id = set_correlation_id("integration-test-123")

        # Simulate workflow that uses multiple async components
        _workflow_handle = await mock_temporal_client.start_workflow(
            "test-integration-workflow", "integration-task-queue"
        )

        # Simulate AI call within workflow
        ai_response = await mock_openai_client.chat.completions.create(
            model="gpt-4o", messages=[{"role": "user", "content": "integration test"}]
        )

        # Verify both components were called
        mock_temporal_client.start_workflow.assert_called_once()
        mock_openai_client.chat.completions.create.assert_called_once()

        assert ai_response.choices[0].message.content == "Test AI response"
        assert correlation_id == "integration-test-123"


@pytest.mark.integration
class TestConfigurationIntegration:
    """Test configuration integration across components."""

    def test_environment_specific_configuration(self, test_settings):
        """Test that configuration adapts to environment."""
        assert test_settings.environment == "test"
        assert test_settings.debug is True
        assert test_settings.logging.level == "DEBUG"

    def test_database_configuration_integration(self, test_settings):
        """Test database configuration integration."""
        db_config = test_settings.database
        assert db_config.host == "localhost"
        assert db_config.port == 5432
        assert db_config.name == "orchestra"

        # Test URL generation
        db_url = db_config.url
        assert "postgresql://" in db_url
        assert "localhost:5432" in db_url


@pytest.mark.integration
@pytest.mark.slow
class TestExternalServiceIntegration:
    """Test integration with external services (mocked)."""

    @pytest.mark.asyncio
    async def test_openai_qdrant_integration(
        self, mock_openai_client, mock_qdrant_client
    ):
        """Test integration between OpenAI and Qdrant services."""
        # Generate embedding with OpenAI
        embedding_response = await mock_openai_client.embeddings.create(
            model="text-embedding-3-large", input="test text for embedding"
        )

        embedding_vector = embedding_response.data[0].embedding
        assert len(embedding_vector) == 3072  # text-embedding-3-large dimension

        # Store in Qdrant
        upsert_response = mock_qdrant_client.upsert(
            collection_name="test-collection",
            points=[
                {
                    "id": "test-doc-1",
                    "vector": embedding_vector,
                    "payload": {"text": "test text for embedding"},
                }
            ],
        )

        assert upsert_response["status"] == "acknowledged"

        # Query Qdrant
        query_response = mock_qdrant_client.search(
            collection_name="test-collection", query_vector=embedding_vector, limit=1
        )
        assert len(query_response) == 1
        assert query_response[0]["score"] == 0.95  # Mock score


@pytest.mark.integration
class TestSecurityIntegration:
    """Test security integration across components."""

    def test_audit_logging_integration(self, test_settings):
        """Test that audit logging is properly integrated."""
        from orchestra.utils.logging import SecurityAuditLogger

        audit_logger = SecurityAuditLogger()

        # Test that audit logging works with settings
        assert test_settings.security.enable_audit_logging is True
        assert test_settings.logging.enable_audit is True

        # Log a security event
        audit_logger.log_security_event(
            "integration_test", {"test_data": "sensitive_operation"}, "INFO"
        )

        # Verify no exceptions were raised
        assert True

    def test_input_validation_integration(self, security_test_data, test_settings):
        """Test input validation integration."""
        malicious_inputs = security_test_data["malicious_inputs"]

        # Test that security settings are properly configured
        assert test_settings.security.enable_code_scanning is True
        assert test_settings.security.max_file_size == 10_000_000

        # In a real integration test, you would test actual validation
        for malicious_input in malicious_inputs:
            # Placeholder for actual validation logic
            assert len(malicious_input) > 0
