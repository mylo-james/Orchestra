"""
Comprehensive tests for src/utils/circuit_breaker.py to achieve 90%+ coverage.

Tests circuit breaker pattern implementation for external service protection.
Based on PRD Story 5.2 AC3: Circuit breaker patterns for external service failures.
"""

import asyncio
import time
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from src.utils.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerError,
    CircuitBreakerManager,
    CircuitBreakerStats,
    CircuitState,
    circuit_breaker,
    circuit_breaker_async,
    circuit_breaker_health_check,
)


class TestCircuitState:
    """Test CircuitState enum."""

    def test_circuit_states(self):
        """Test all circuit states are defined."""
        assert CircuitState.CLOSED.value == "closed"
        assert CircuitState.OPEN.value == "open"
        assert CircuitState.HALF_OPEN.value == "half_open"


class TestCircuitBreakerConfig:
    """Test CircuitBreakerConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = CircuitBreakerConfig()
        assert config.failure_threshold == 5
        assert config.success_threshold == 2
        assert config.timeout == 60.0
        assert config.recovery_timeout == 300.0
        assert config.max_retry_attempts == 3
        assert config.request_timeout == 30.0

    def test_custom_config(self):
        """Test custom configuration values."""
        config = CircuitBreakerConfig(
            failure_threshold=10,
            success_threshold=3,
            timeout=30.0,
            recovery_timeout=150.0,
            max_retry_attempts=5,
            request_timeout=15.0
        )
        assert config.failure_threshold == 10
        assert config.success_threshold == 3
        assert config.timeout == 30.0


class TestCircuitBreakerStats:
    """Test CircuitBreakerStats dataclass."""

    def test_default_stats(self):
        """Test default statistics values."""
        stats = CircuitBreakerStats()
        assert stats.total_requests == 0
        assert stats.successful_requests == 0
        assert stats.failed_requests == 0
        assert stats.rejected_requests == 0
        assert stats.state_changes == 0
        assert stats.last_failure_time is None
        assert stats.last_success_time is None
        assert isinstance(stats.created_time, datetime)


class TestCircuitBreakerError:
    """Test CircuitBreakerError exception."""

    def test_error_creation(self):
        """Test creating circuit breaker error."""
        error = CircuitBreakerError("test-service", CircuitState.OPEN, "Service unavailable")
        assert error.service_name == "test-service"
        assert error.state == CircuitState.OPEN
        assert str(error) == "Service unavailable"


class TestCircuitBreaker:
    """Test CircuitBreaker class."""

    def test_initialization(self):
        """Test circuit breaker initialization."""
        cb = CircuitBreaker("test-service")
        assert cb.name == "test-service"
        assert cb.state == CircuitState.CLOSED
        assert cb.consecutive_failures == 0
        assert cb.consecutive_successes == 0

    def test_initialization_with_config(self):
        """Test initialization with custom config."""
        config = CircuitBreakerConfig(failure_threshold=3)
        cb = CircuitBreaker("test-service", config)
        assert cb.config.failure_threshold == 3

    @pytest.mark.asyncio
    async def test_call_success(self):
        """Test successful call through circuit breaker."""
        cb = CircuitBreaker("test-service")
        
        async def success_func():
            return "success"
        
        result = await cb.call(success_func)
        assert result == "success"
        assert cb.stats.successful_requests == 1
        assert cb.stats.failed_requests == 0

    @pytest.mark.asyncio
    async def test_call_failure(self):
        """Test failed call through circuit breaker."""
        cb = CircuitBreaker("test-service")
        
        async def failure_func():
            raise Exception("Service error")
        
        with pytest.raises(Exception, match="Service error"):
            await cb.call(failure_func)
        
        assert cb.stats.failed_requests == 1
        assert cb.consecutive_failures == 1

    @pytest.mark.asyncio
    async def test_circuit_opens_after_threshold(self):
        """Test circuit opens after failure threshold."""
        config = CircuitBreakerConfig(failure_threshold=3)
        cb = CircuitBreaker("test-service", config)
        
        async def failure_func():
            raise Exception("Service error")
        
        # Trigger failures to open circuit
        for _ in range(3):
            with pytest.raises(Exception):
                await cb.call(failure_func)
        
        assert cb.state == CircuitState.OPEN
        assert cb.stats.state_changes == 1

    @pytest.mark.asyncio
    async def test_open_circuit_rejects_calls(self):
        """Test open circuit rejects calls immediately."""
        cb = CircuitBreaker("test-service")
        cb.state = CircuitState.OPEN
        cb.last_failure_time = time.time()
        
        async def test_func():
            return "should not execute"
        
        with pytest.raises(CircuitBreakerError) as exc_info:
            await cb.call(test_func)
        
        assert exc_info.value.state == CircuitState.OPEN
        assert cb.stats.rejected_requests == 1

    @pytest.mark.asyncio
    async def test_half_open_transition(self):
        """Test transition from open to half-open after timeout."""
        config = CircuitBreakerConfig(timeout=0.1)  # Short timeout for testing
        cb = CircuitBreaker("test-service", config)
        cb.state = CircuitState.OPEN
        cb.last_failure_time = time.time() - 1  # Past timeout
        
        async def success_func():
            return "success"
        
        # Should transition to half-open and allow call
        result = await cb.call(success_func)
        assert result == "success"
        assert cb.state == CircuitState.HALF_OPEN

    @pytest.mark.asyncio
    async def test_half_open_to_closed(self):
        """Test successful recovery from half-open to closed."""
        config = CircuitBreakerConfig(success_threshold=2)
        cb = CircuitBreaker("test-service", config)
        cb.state = CircuitState.HALF_OPEN
        
        async def success_func():
            return "success"
        
        # Two successful calls should close circuit
        for _ in range(2):
            await cb.call(success_func)
        
        assert cb.state == CircuitState.CLOSED
        assert cb.consecutive_successes == 0  # Reset after closing

    @pytest.mark.asyncio
    async def test_half_open_to_open(self):
        """Test failure in half-open returns to open."""
        cb = CircuitBreaker("test-service")
        cb.state = CircuitState.HALF_OPEN
        
        async def failure_func():
            raise Exception("Still failing")
        
        with pytest.raises(Exception):
            await cb.call(failure_func)
        
        assert cb.state == CircuitState.OPEN

    def test_is_open(self):
        """Test is_open method."""
        cb = CircuitBreaker("test-service")
        assert not cb.is_open()
        
        cb.state = CircuitState.OPEN
        assert cb.is_open()
        
        cb.state = CircuitState.HALF_OPEN
        assert not cb.is_open()

    def test_is_closed(self):
        """Test is_closed method."""
        cb = CircuitBreaker("test-service")
        assert cb.is_closed()
        
        cb.state = CircuitState.OPEN
        assert not cb.is_closed()

    def test_reset(self):
        """Test reset method."""
        cb = CircuitBreaker("test-service")
        cb.state = CircuitState.OPEN
        cb.consecutive_failures = 5
        cb.stats.failed_requests = 10
        
        cb.reset()
        
        assert cb.state == CircuitState.CLOSED
        assert cb.consecutive_failures == 0
        assert cb.consecutive_successes == 0

    def test_get_stats(self):
        """Test get_stats method."""
        cb = CircuitBreaker("test-service")
        cb.stats.total_requests = 100
        cb.stats.successful_requests = 80
        
        stats = cb.get_stats()
        
        assert stats["name"] == "test-service"
        assert stats["state"] == "closed"
        assert stats["total_requests"] == 100
        assert stats["successful_requests"] == 80
        assert "success_rate" in stats


class TestCircuitBreakerManager:
    """Test CircuitBreakerManager singleton."""

    def test_singleton_pattern(self):
        """Test manager is a singleton."""
        manager1 = CircuitBreakerManager()
        manager2 = CircuitBreakerManager()
        assert manager1 is manager2

    def test_get_or_create_breaker(self):
        """Test getting or creating circuit breakers."""
        manager = CircuitBreakerManager()
        manager._breakers.clear()  # Clear any existing breakers
        
        # Create new breaker
        cb1 = manager.get_or_create("service1")
        assert cb1.name == "service1"
        
        # Get existing breaker
        cb2 = manager.get_or_create("service1")
        assert cb1 is cb2

    def test_get_or_create_with_config(self):
        """Test creating breaker with custom config."""
        manager = CircuitBreakerManager()
        config = CircuitBreakerConfig(failure_threshold=10)
        
        cb = manager.get_or_create("service2", config)
        assert cb.config.failure_threshold == 10

    def test_get_breaker(self):
        """Test getting existing breaker."""
        manager = CircuitBreakerManager()
        manager.get_or_create("service3")
        
        cb = manager.get_breaker("service3")
        assert cb is not None
        assert cb.name == "service3"
        
        # Non-existent breaker
        assert manager.get_breaker("non-existent") is None

    def test_reset_breaker(self):
        """Test resetting a breaker."""
        manager = CircuitBreakerManager()
        cb = manager.get_or_create("service4")
        cb.state = CircuitState.OPEN
        
        manager.reset_breaker("service4")
        assert cb.state == CircuitState.CLOSED

    def test_reset_all(self):
        """Test resetting all breakers."""
        manager = CircuitBreakerManager()
        cb1 = manager.get_or_create("service5")
        cb2 = manager.get_or_create("service6")
        
        cb1.state = CircuitState.OPEN
        cb2.state = CircuitState.HALF_OPEN
        
        manager.reset_all()
        
        assert cb1.state == CircuitState.CLOSED
        assert cb2.state == CircuitState.CLOSED

    def test_get_all_stats(self):
        """Test getting stats for all breakers."""
        manager = CircuitBreakerManager()
        manager._breakers.clear()
        
        manager.get_or_create("service7")
        manager.get_or_create("service8")
        
        stats = manager.get_all_stats()
        assert len(stats) == 2
        assert any(s["name"] == "service7" for s in stats)
        assert any(s["name"] == "service8" for s in stats)


class TestCircuitBreakerDecorators:
    """Test circuit breaker decorators."""

    @pytest.mark.asyncio
    async def test_async_decorator(self):
        """Test async circuit breaker decorator."""
        @circuit_breaker_async(name="async-service")
        async def async_func(value):
            return f"async-{value}"
        
        result = await async_func("test")
        assert result == "async-test"

    @pytest.mark.asyncio
    async def test_async_decorator_with_config(self):
        """Test async decorator with custom config."""
        config = CircuitBreakerConfig(failure_threshold=2)
        
        @circuit_breaker_async(name="async-service2", config=config)
        async def async_func():
            raise Exception("Test error")
        
        # Should fail twice before opening
        for _ in range(2):
            with pytest.raises(Exception):
                await async_func()
        
        # Third call should be rejected
        with pytest.raises(CircuitBreakerError):
            await async_func()

    def test_sync_decorator(self):
        """Test sync circuit breaker decorator."""
        @circuit_breaker(name="sync-service")
        def sync_func(value):
            return f"sync-{value}"
        
        result = sync_func("test")
        assert result == "sync-test"

    def test_sync_decorator_with_failure(self):
        """Test sync decorator with failures."""
        config = CircuitBreakerConfig(failure_threshold=1)
        
        @circuit_breaker(name="sync-service2", config=config)
        def sync_func():
            raise Exception("Sync error")
        
        # First call fails and opens circuit
        with pytest.raises(Exception):
            sync_func()
        
        # Second call should be rejected
        with pytest.raises(CircuitBreakerError):
            sync_func()


class TestCircuitBreakerHealthCheck:
    """Test circuit breaker health check function."""

    def test_health_check_all_healthy(self):
        """Test health check with all breakers healthy."""
        manager = CircuitBreakerManager()
        manager._breakers.clear()
        
        cb1 = manager.get_or_create("health-service1")
        cb2 = manager.get_or_create("health-service2")
        
        cb1.state = CircuitState.CLOSED
        cb2.state = CircuitState.CLOSED
        
        health = circuit_breaker_health_check()
        
        assert health["healthy"] is True
        assert health["total_breakers"] == 2
        assert health["open_breakers"] == 0
        assert len(health["failing_services"]) == 0

    def test_health_check_with_failures(self):
        """Test health check with failing services."""
        manager = CircuitBreakerManager()
        manager._breakers.clear()
        
        cb1 = manager.get_or_create("health-service3")
        cb2 = manager.get_or_create("health-service4")
        cb3 = manager.get_or_create("health-service5")
        
        cb1.state = CircuitState.CLOSED
        cb2.state = CircuitState.OPEN
        cb3.state = CircuitState.HALF_OPEN
        
        health = circuit_breaker_health_check()
        
        assert health["healthy"] is False
        assert health["total_breakers"] == 3
        assert health["open_breakers"] == 1
        assert health["half_open_breakers"] == 1
        assert "health-service4" in health["failing_services"]

    def test_health_check_empty(self):
        """Test health check with no breakers."""
        manager = CircuitBreakerManager()
        manager._breakers.clear()
        
        health = circuit_breaker_health_check()
        
        assert health["healthy"] is True
        assert health["total_breakers"] == 0
        assert health["open_breakers"] == 0


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test request timeout handling."""
        config = CircuitBreakerConfig(request_timeout=0.1)
        cb = CircuitBreaker("timeout-service", config)
        
        async def slow_func():
            await asyncio.sleep(1)
            return "too slow"
        
        with pytest.raises(asyncio.TimeoutError):
            await cb.call(slow_func)
        
        assert cb.stats.failed_requests == 1

    @pytest.mark.asyncio
    async def test_concurrent_calls(self):
        """Test concurrent calls through circuit breaker."""
        cb = CircuitBreaker("concurrent-service")
        
        async def async_func(i):
            await asyncio.sleep(0.01)
            return i
        
        # Run multiple concurrent calls
        tasks = [cb.call(lambda: async_func(i)) for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 10
        assert cb.stats.successful_requests == 10

    def test_stats_calculation(self):
        """Test statistics calculation."""
        cb = CircuitBreaker("stats-service")
        cb.stats.total_requests = 100
        cb.stats.successful_requests = 75
        cb.stats.failed_requests = 20
        cb.stats.rejected_requests = 5
        
        stats = cb.get_stats()
        
        assert stats["success_rate"] == 0.75
        assert stats["failure_rate"] == 0.20
        assert stats["rejection_rate"] == 0.05