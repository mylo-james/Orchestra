"""Simple tests to boost circuit breaker coverage from 59% to 70%+."""

import pytest

from src.utils.circuit_breaker import (
    CircuitBreakerConfig,
    get_circuit_breaker_stats,
    get_failing_services,
    get_openai_circuit_breaker,
    get_github_circuit_breaker,
    get_pinecone_circuit_breaker,
    get_temporal_circuit_breaker,
    protect_external_service,
    protect_external_service_async,
)


class TestCircuitBreakerUtilities:
    """Test circuit breaker utility functions."""

    def test_get_circuit_breaker_stats(self):
        """Test getting circuit breaker statistics."""
        stats = get_circuit_breaker_stats()
        assert isinstance(stats, dict)
        # Stats dict may be empty initially - that's ok

    def test_get_failing_services(self):
        """Test getting list of failing services."""
        failing = get_failing_services()
        assert isinstance(failing, list)

    def test_get_specific_circuit_breakers(self):
        """Test getting specific circuit breakers."""
        openai_cb = get_openai_circuit_breaker()
        assert openai_cb is not None

        github_cb = get_github_circuit_breaker()
        assert github_cb is not None

        pinecone_cb = get_pinecone_circuit_breaker()
        assert pinecone_cb is not None

        temporal_cb = get_temporal_circuit_breaker()
        assert temporal_cb is not None

    def test_protect_external_service_decorator(self):
        """Test the protect_external_service decorator."""

        @protect_external_service("test_service")
        def test_sync_function():
            return "sync_success"

        result = test_sync_function()
        assert result == "sync_success"

    @pytest.mark.asyncio
    async def test_protect_external_service_async_decorator(self):
        """Test the async decorator."""

        @protect_external_service_async("test_async_service")
        async def test_async_function():
            return "async_success"

        result = await test_async_function()
        assert result == "async_success"

    def test_circuit_breaker_config_variations(self):
        """Test CircuitBreakerConfig with different values."""
        # Test default config
        config1 = CircuitBreakerConfig()
        assert config1.failure_threshold == 5

        # Test custom config
        config2 = CircuitBreakerConfig(
            failure_threshold=3,
            success_threshold=1,
            timeout=30.0,
            recovery_timeout=120.0,
        )
        assert config2.failure_threshold == 3
        assert config2.success_threshold == 1
        assert config2.timeout == 30.0

    def test_circuit_breaker_with_different_configs(self):
        """Test creating circuit breakers with different configurations."""
        from src.utils.circuit_breaker import CircuitBreakerRegistry

        registry = CircuitBreakerRegistry()

        # Test with custom config
        config = CircuitBreakerConfig(failure_threshold=2, timeout=15.0)
        cb = registry.get_or_create("custom_service", config)
        assert cb is not None

        # Test getting existing breaker
        cb2 = registry.get_or_create("custom_service", config)
        assert cb2 is cb  # Should be same instance
