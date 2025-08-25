"""Tests for orchestra/utils/circuit_breaker.py."""

import asyncio
import time
from unittest.mock import patch

import pytest

# Import to ensure module is loaded for coverage
from orchestra.utils.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerError,
    CircuitBreakerRegistry,
    CircuitBreakerStats,
    CircuitState,
    circuit_breaker_health_check,
    get_circuit_breaker,
    get_qdrant_circuit_breaker,
    get_temporal_circuit_breaker,
    protect_external_service,
    protect_external_service_async,
    reset_all_circuit_breakers,
)


@pytest.fixture(autouse=True)
def clear_circuit_breaker_registry():
    """Clear the global circuit breaker registry before each test to prevent state pollution."""
    # Reset all circuit breakers
    reset_all_circuit_breakers()
    yield
    # Also reset after the test
    reset_all_circuit_breakers()


class TestCircuitBreakerError:
    """Test CircuitBreakerError exception class."""

    def test_circuit_breaker_error_init(self):
        """Test CircuitBreakerError initialization (lines 62-64)."""
        error = CircuitBreakerError(
            service_name="test_service",
            state=CircuitState.OPEN,
            message="Circuit is open",
        )

        assert error.service_name == "test_service"
        assert error.state == CircuitState.OPEN
        assert str(error) == "Circuit is open"


class TestCircuitBreakerConfig:
    """Test circuit breaker configuration."""

    def test_circuit_breaker_config_defaults(self):
        """Test CircuitBreakerConfig default values."""
        config = CircuitBreakerConfig()
        assert config.failure_threshold == 5
        assert config.success_threshold == 2
        assert config.timeout == 60.0
        assert config.recovery_timeout == 300.0
        assert config.max_retry_attempts == 3
        assert config.request_timeout == 30.0

    def test_circuit_breaker_config_custom(self):
        """Test CircuitBreakerConfig with custom values."""
        custom_config = CircuitBreakerConfig(
            failure_threshold=3, timeout=30.0, max_retry_attempts=2
        )
        assert custom_config.failure_threshold == 3
        assert custom_config.timeout == 30.0
        assert custom_config.max_retry_attempts == 2


class TestCircuitBreakerStats:
    """Test circuit breaker statistics."""

    def test_circuit_breaker_stats_defaults(self):
        """Test CircuitBreakerStats default values."""
        stats = CircuitBreakerStats()
        assert stats.total_requests == 0
        assert stats.successful_requests == 0
        assert stats.failed_requests == 0
        assert stats.rejected_requests == 0
        assert stats.state_changes == 0
        assert stats.last_failure_time is None
        assert stats.last_success_time is None
        assert stats.created_time is not None


class TestCircuitBreakerCore:
    """Test core circuit breaker functionality."""

    def test_circuit_breaker_initialization(self):
        """Test CircuitBreaker initialization."""
        cb = CircuitBreaker("test_service")

        assert cb.name == "test_service"
        assert cb.state == CircuitState.CLOSED
        assert cb.consecutive_failures == 0
        assert cb.consecutive_successes == 0
        assert cb.config.failure_threshold == 5

    def test_circuit_breaker_initialization_with_config(self):
        """Test CircuitBreaker initialization with custom config."""
        config = CircuitBreakerConfig(failure_threshold=3, timeout=30.0)
        cb = CircuitBreaker("test_service", config)

        assert cb.name == "test_service"
        assert cb.config.failure_threshold == 3
        assert cb.config.timeout == 30.0

    def test_circuit_breaker_sync_decorator(self):
        """Test CircuitBreaker __call__ decorator (lines 104-108)."""
        cb = CircuitBreaker("test_service")

        @cb
        def test_func(value):
            return f"success_{value}"

        result = test_func("test")
        assert result == "success_test"
        assert cb.stats.total_requests == 1
        assert cb.stats.successful_requests == 1

    def test_circuit_breaker_async_decorator(self):
        """Test CircuitBreaker async_call decorator (lines 113-117)."""
        cb = CircuitBreaker("test_service")

        @cb.async_call
        async def test_async_func(value):
            return f"async_success_{value}"

        async def run_test():
            result = await test_async_func("test")
            assert result == "async_success_test"
            return result

        # Run the async test
        result = asyncio.run(run_test())
        assert result == "async_success_test"

    def test_protect_external_service_decorator(self):
        """Test protect_external_service decorator."""

        @protect_external_service("test_service")
        def test_function():
            return "success"

        result = test_function()
        assert result == "success"


class TestCircuitBreakerSyncCall:
    """Test synchronous call functionality."""

    def test_sync_call_success(self):
        """Test successful synchronous call."""
        cb = CircuitBreaker("test_service_sync")

        def test_func():
            return "success"

        result = cb.call(test_func)
        assert result == "success"
        assert cb.stats.successful_requests == 1
        assert cb.consecutive_failures == 0
        assert cb.consecutive_successes == 1

    def test_sync_call_with_retries(self):
        """Test synchronous call with retries (lines 146-161)."""
        cb = CircuitBreaker("test_service_sync_retry")
        call_count = 0

        def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return "success_after_retry"

        # Mock time.sleep to speed up test
        with patch("time.sleep"):
            result = cb.call(failing_func)

        assert result == "success_after_retry"
        assert call_count == 3
        assert cb.stats.successful_requests == 1

    def test_sync_call_all_retries_fail(self):
        """Test synchronous call where all retries fail."""
        cb = CircuitBreaker(
            "test_service_sync_fail", CircuitBreakerConfig(max_retry_attempts=2)
        )

        def failing_func():
            raise Exception("Always fails")

        with patch("time.sleep"):
            with pytest.raises(Exception, match="Always fails"):
                cb.call(failing_func)

        assert cb.stats.failed_requests == 1
        assert cb.consecutive_failures == 1

    def test_sync_call_rejected_by_open_circuit(self):
        """Test request rejection when circuit is open (lines 123-124)."""
        cb = CircuitBreaker("test_service_sync_reject")
        cb.state = CircuitState.OPEN

        def test_func():
            return "should_not_execute"

        with pytest.raises(CircuitBreakerError):
            cb.call(test_func)

        assert cb.stats.rejected_requests == 1


class TestCircuitBreakerAsyncCall:
    """Test asynchronous call functionality."""

    @pytest.mark.asyncio
    async def test_async_call_success(self):
        """Test successful asynchronous call (lines 165-211)."""
        cb = CircuitBreaker("test_service_async")

        async def test_async_func():
            return "async_success"

        result = await cb.call_async(test_async_func)
        assert result == "async_success"
        assert cb.stats.successful_requests == 1
        assert cb.consecutive_successes == 1

    @pytest.mark.asyncio
    async def test_async_call_with_timeout(self):
        """Test async call with timeout handling."""
        cb = CircuitBreaker(
            "test_service_async_timeout", CircuitBreakerConfig(request_timeout=0.1)
        )

        async def slow_func():
            await asyncio.sleep(0.2)  # Longer than timeout
            return "too_slow"

        with pytest.raises(asyncio.TimeoutError):
            await cb.call_async(slow_func)

        assert cb.stats.failed_requests == 1

    @pytest.mark.asyncio
    async def test_async_call_with_retries(self):
        """Test async call with retries."""
        cb = CircuitBreaker("test_service_async_retry")
        call_count = 0

        async def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("Async failure")
            return "async_success_after_retry"

        result = await cb.call_async(failing_func)
        assert result == "async_success_after_retry"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_async_call_rejected_by_open_circuit(self):
        """Test async request rejection when circuit is open."""
        cb = CircuitBreaker("test_service_async_reject")
        cb.state = CircuitState.OPEN

        async def test_func():
            return "should_not_execute"

        with pytest.raises(CircuitBreakerError):
            await cb.call_async(test_func)

        assert cb.stats.rejected_requests == 1


class TestCircuitBreakerStateTransitions:
    """Test circuit breaker state transitions."""

    def test_state_transitions_closed_to_open(self):
        """Test transition from CLOSED to OPEN (lines 266-274)."""
        config = CircuitBreakerConfig(failure_threshold=2, max_retry_attempts=1)
        cb = CircuitBreaker("test_service_transition", config)

        def failing_func():
            raise Exception("Failure")

        # Initially closed
        assert cb.state == CircuitState.CLOSED

        # Cause failures to open circuit
        with patch("time.sleep"):
            for _ in range(2):
                with pytest.raises(Exception):
                    cb.call(failing_func)

        # Should now be open
        assert cb.state == CircuitState.OPEN

    def test_state_transitions_open_to_half_open(self):
        """Test transition from OPEN to HALF_OPEN (lines 278-285)."""
        cb = CircuitBreaker("test_service_half_open")
        cb.state = CircuitState.OPEN
        cb.last_state_change = time.time() - 70  # Make it old enough to allow half-open

        def success_func():
            return "success"

        # Should transition to half-open and succeed
        result = cb.call(success_func)
        assert result == "success"
        assert cb.state == CircuitState.HALF_OPEN

    def test_state_transitions_half_open_to_closed(self):
        """Test transition from HALF_OPEN to CLOSED (lines 289-296, 242-243)."""
        config = CircuitBreakerConfig(success_threshold=2)
        cb = CircuitBreaker("test_service_closed", config)
        cb.state = CircuitState.HALF_OPEN

        def success_func():
            return "success"

        # First success - should stay half-open
        cb.call(success_func)
        assert cb.state == CircuitState.HALF_OPEN

        # Second success should close the circuit
        cb.call(success_func)
        assert cb.state == CircuitState.CLOSED

    def test_should_allow_request_logic(self):
        """Test _should_allow_request method logic (lines 219-229)."""
        cb = CircuitBreaker("test_service_allow")

        # CLOSED state should allow requests
        cb.state = CircuitState.CLOSED
        assert cb._should_allow_request() is True

        # OPEN state should not allow requests (unless timeout passed)
        cb.state = CircuitState.OPEN
        cb.last_state_change = time.time()  # Recent state change
        assert cb._should_allow_request() is False

        # HALF_OPEN state should allow requests
        cb.state = CircuitState.HALF_OPEN
        assert cb._should_allow_request() is True

        # Test the fallback return False case (line 229)
        # Set an invalid state to trigger the fallback
        cb.state = "invalid_state"  # This will not match any of the conditions
        assert cb._should_allow_request() is False


class TestCircuitBreakerStatsManagement:
    """Test circuit breaker statistics and management."""

    def test_get_stats(self):
        """Test get_stats method (lines 314-318)."""
        cb = CircuitBreaker("test_service_stats")

        # Execute some operations
        cb.call(lambda: "success")

        stats = cb.get_stats()

        assert stats["name"] == "test_service_stats"
        assert stats["state"] == CircuitState.CLOSED.value
        assert "config" in stats
        assert "stats" in stats
        assert stats["consecutive_failures"] == 0
        assert stats["consecutive_successes"] == 1
        assert stats["success_rate"] > 0
        assert stats["failure_rate"] == 0

    def test_reset_circuit_breaker(self):
        """Test reset method (lines 332-340)."""
        cb = CircuitBreaker("test_service_reset")

        # Force some failures and state change
        cb.consecutive_failures = 5
        cb.consecutive_successes = 2
        cb.state = CircuitState.OPEN

        old_state_changes = cb.stats.state_changes

        cb.reset()

        assert cb.state == CircuitState.CLOSED
        assert cb.consecutive_failures == 0
        assert cb.consecutive_successes == 0
        assert cb.stats.state_changes == old_state_changes + 1


class TestCircuitBreakerRegistryFull:
    """Test CircuitBreakerRegistry functionality."""

    def test_registry_get_or_create(self):
        """Test get_or_create method."""
        registry = CircuitBreakerRegistry()

        # Create new circuit breaker
        cb1 = registry.get_or_create("service1")
        assert cb1.name == "service1"
        assert len(registry._breakers) == 1

        # Get existing circuit breaker
        cb2 = registry.get_or_create("service1")
        assert cb1 is cb2  # Same instance
        assert len(registry._breakers) == 1

        # Create another circuit breaker
        cb3 = registry.get_or_create(
            "service2", CircuitBreakerConfig(failure_threshold=3)
        )
        assert cb3.name == "service2"
        assert cb3.config.failure_threshold == 3
        assert len(registry._breakers) == 2

    def test_registry_reset_all(self):
        """Test reset_all method (lines 370-372)."""
        registry = CircuitBreakerRegistry()

        # Create and modify some circuit breakers
        cb1 = registry.get_or_create("service1")
        cb2 = registry.get_or_create("service2")

        cb1.state = CircuitState.OPEN
        cb2.consecutive_failures = 5

        # Reset all
        registry.reset_all()

        assert cb1.state == CircuitState.CLOSED
        assert cb2.consecutive_failures == 0


class TestServiceSpecificCircuitBreakersFull:
    """Test service-specific circuit breaker getters."""

    def test_get_temporal_circuit_breaker(self):
        """Test get_temporal_circuit_breaker function (lines 493-501)."""
        cb = get_temporal_circuit_breaker()
        assert cb.name == "temporal_cloud"
        assert cb.config.failure_threshold == 5
        assert cb.config.success_threshold == 3
        assert cb.config.timeout == 60.0

    def test_get_qdrant_circuit_breaker(self):
        """Test get_qdrant_circuit_breaker function (lines 506-514)."""
        cb = get_qdrant_circuit_breaker()
        assert cb.name == "qdrant_vector_db"
        assert cb.config.failure_threshold == 4
        assert cb.config.request_timeout == 15.0


class TestProtectExternalServiceDecoratorsFull:
    """Test decorator functions for protecting external services."""

    def test_protect_external_service_with_fallback(self):
        """Test protect_external_service with fallback result (lines 430-435)."""
        # Create a circuit breaker that's already open
        cb = get_circuit_breaker("fallback_test_service_3")
        cb.state = CircuitState.OPEN

        @protect_external_service("fallback_test_service_3", fallback_result="fallback")
        def failing_function():
            return "should_not_execute"  # This won't execute due to open circuit

        # Call should use fallback due to open circuit
        result = failing_function()
        assert result == "fallback"

    def test_protect_external_service_no_fallback_raises(self):
        """Test protect_external_service without fallback raises CircuitBreakerError (line 435)."""
        # Create a circuit breaker that's already open
        cb = get_circuit_breaker("no_fallback_test_service_2")
        cb.state = CircuitState.OPEN

        @protect_external_service("no_fallback_test_service_2")  # No fallback_result
        def failing_function():
            return "should_not_execute"

        # Should raise CircuitBreakerError with no fallback
        with pytest.raises(CircuitBreakerError):
            failing_function()

    @pytest.mark.asyncio
    async def test_protect_external_service_async_with_fallback(self):
        """Test protect_external_service_async with fallback (lines 456-474)."""
        # Create a circuit breaker that's already open
        cb = get_circuit_breaker("async_fallback_test_service_3")
        cb.state = CircuitState.OPEN

        @protect_external_service_async(
            "async_fallback_test_service_3", fallback_result="async_fallback"
        )
        async def async_failing_function():
            return "should_not_execute"  # This won't execute due to open circuit

        # Call should use fallback due to open circuit
        result = await async_failing_function()
        assert result == "async_fallback"

    @pytest.mark.asyncio
    async def test_protect_external_service_async_no_fallback_raises(self):
        """Test protect_external_service_async without fallback raises CircuitBreakerError (line 470)."""
        # Create a circuit breaker that's already open
        cb = get_circuit_breaker("async_no_fallback_test_service_2")
        cb.state = CircuitState.OPEN

        @protect_external_service_async(
            "async_no_fallback_test_service_2"
        )  # No fallback_result
        async def async_failing_function():
            return "should_not_execute"

        # Should raise CircuitBreakerError with no fallback
        with pytest.raises(CircuitBreakerError):
            await async_failing_function()


class TestGlobalFunctionsFull:
    """Test global utility functions."""

    def test_reset_all_circuit_breakers_function(self):
        """Test reset_all_circuit_breakers global function (lines 543-544)."""
        # Create and modify some circuit breakers
        cb1 = get_circuit_breaker("reset_test_service3")
        cb2 = get_circuit_breaker("reset_test_service4")

        cb1.state = CircuitState.OPEN
        cb2.consecutive_failures = 3

        reset_all_circuit_breakers()

        assert cb1.state == CircuitState.CLOSED
        assert cb2.consecutive_failures == 0

    def test_circuit_breaker_health_check_healthy(self):
        """Test circuit_breaker_health_check with healthy services (lines 555-579)."""
        # Reset all first
        reset_all_circuit_breakers()

        # Create some healthy circuit breakers
        get_circuit_breaker("healthy3")
        get_circuit_breaker("healthy4")

        health = circuit_breaker_health_check()

        assert health["healthy"] is True
        assert health["total_circuit_breakers"] >= 2
        assert health["open_circuit_breakers"] == 0
        assert len(health["failing_services"]) == 0
        assert "all_stats" in health
        assert "summary" in health

    def test_circuit_breaker_health_check_with_failures(self):
        """Test circuit_breaker_health_check with failing services."""
        # Create circuit breakers with some failures
        cb1 = get_circuit_breaker("failing_health_service_2")

        cb1.state = CircuitState.OPEN

        health = circuit_breaker_health_check()

        assert health["healthy"] is False
        assert health["open_circuit_breakers"] >= 1
        assert "failing_health_service_2" in health["failing_services"]
