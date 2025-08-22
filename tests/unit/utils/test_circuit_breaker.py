"""Tests for src/utils/circuit_breaker.py."""

# Import to ensure module is loaded for coverage
import src.utils.circuit_breaker
from src.utils.circuit_breaker import (
    CircuitBreakerConfig,
    get_circuit_breaker_stats,
    get_failing_services,
    get_openai_circuit_breaker,
    get_github_circuit_breaker,
    protect_external_service,
)


class TestCircuitBreaker:
    """Test circuit breaker functionality."""

    def test_circuit_breaker_module_loads(self):
        """Test that circuit breaker module loads."""
        assert src.utils.circuit_breaker is not None

    def test_circuit_breaker_config(self):
        """Test CircuitBreakerConfig."""
        config = CircuitBreakerConfig()
        assert config.failure_threshold == 5

        custom_config = CircuitBreakerConfig(failure_threshold=3, timeout=30.0)
        assert custom_config.failure_threshold == 3

    def test_circuit_breaker_functions(self):
        """Test circuit breaker utility functions."""
        stats = get_circuit_breaker_stats()
        assert isinstance(stats, dict)

        failing = get_failing_services()
        assert isinstance(failing, list)

        openai_cb = get_openai_circuit_breaker()
        assert openai_cb is not None

        github_cb = get_github_circuit_breaker()
        assert github_cb is not None

    def test_protect_external_service_decorator(self):
        """Test protect_external_service decorator."""

        @protect_external_service("test_service")
        def test_function():
            return "success"

        result = test_function()
        assert result == "success"
