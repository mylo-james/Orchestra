"""
Circuit Breaker Pattern Implementation for External Service Protection

Prevents AI agents from overwhelming failing external services and causing cascade failures.
"""

import asyncio
import functools
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, Optional, TypeVar

logger = logging.getLogger(__name__)

# Type variables
T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., Any])
AsyncF = TypeVar("AsyncF", bound=Callable[..., Awaitable[Any]])


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation - requests flow through
    OPEN = "open"  # Failure mode - requests blocked immediately
    HALF_OPEN = "half_open"  # Testing mode - limited requests allowed


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior."""

    failure_threshold: int = 5  # Number of failures before opening
    success_threshold: int = 2  # Number of successes to close from half-open
    timeout: float = 60.0  # Seconds to wait before trying half-open
    recovery_timeout: float = 300.0  # Seconds to wait before full recovery
    max_retry_attempts: int = 3  # Max retries before marking as failure
    request_timeout: float = 30.0  # Timeout for individual requests


@dataclass
class CircuitBreakerStats:
    """Statistics tracking for circuit breaker."""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    rejected_requests: int = 0
    state_changes: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    created_time: datetime = field(default_factory=datetime.utcnow)


class CircuitBreakerError(Exception):
    """Raised when circuit breaker rejects a request."""

    def __init__(self, service_name: str, state: CircuitState, message: str):
        self.service_name = service_name
        self.state = state
        super().__init__(message)


class CircuitBreaker:
    """
    Circuit breaker implementation for protecting external services.

    States:
    - CLOSED: Normal operation, all requests pass through
    - OPEN: Service is failing, all requests immediately rejected
    - HALF_OPEN: Testing recovery, limited requests allowed

    The circuit breaker prevents AI agents from overwhelming failing services
    and causing cascade failures across multiple external dependencies.
    """

    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.stats = CircuitBreakerStats()

        # Failure tracking
        self.consecutive_failures = 0
        self.consecutive_successes = 0
        self.last_failure_time: Optional[float] = None
        self.last_state_change: float = time.time()

        # Thread safety
        self._lock = asyncio.Lock()

        logger.info(
            f"Circuit breaker '{name}' initialized", config=self.config.__dict__
        )

    def __call__(self, func: F) -> F:
        """Decorator for sync functions."""

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return self.call(func, *args, **kwargs)

        return wrapper

    def async_call(self, func: AsyncF) -> AsyncF:
        """Decorator for async functions."""

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await self.call_async(func, *args, **kwargs)

        return wrapper

    def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function with circuit breaker protection."""
        # Check if request should be allowed
        if not self._should_allow_request():
            self.stats.rejected_requests += 1
            raise CircuitBreakerError(
                self.name,
                self.state,
                f"Circuit breaker '{self.name}' is {self.state.value} - request rejected",
            )

        self.stats.total_requests += 1

        # Execute with timeout and retry logic
        start_time = time.time()
        last_exception = None

        for attempt in range(self.config.max_retry_attempts):
            try:
                result = func(*args, **kwargs)

                # Success - record and potentially close circuit
                duration = time.time() - start_time
                self._record_success(duration)

                return result

            except Exception as e:
                last_exception = e
                logger.warning(
                    f"Circuit breaker '{self.name}' - attempt {attempt + 1} failed: {e}"
                )

                if attempt < self.config.max_retry_attempts - 1:
                    # Exponential backoff for retries
                    wait_time = min(2**attempt, 10)
                    time.sleep(wait_time)

        # All retries failed - record failure and potentially open circuit
        duration = time.time() - start_time
        self._record_failure(duration, last_exception)

        raise last_exception

    async def call_async(self, func: Callable[..., Awaitable[T]], *args, **kwargs) -> T:
        """Execute async function with circuit breaker protection."""
        async with self._lock:
            # Check if request should be allowed
            if not self._should_allow_request():
                self.stats.rejected_requests += 1
                raise CircuitBreakerError(
                    self.name,
                    self.state,
                    f"Circuit breaker '{self.name}' is {self.state.value} - request rejected",
                )

        self.stats.total_requests += 1

        # Execute with timeout and retry logic
        start_time = time.time()
        last_exception = None

        for attempt in range(self.config.max_retry_attempts):
            try:
                # Apply timeout to the async function
                result = await asyncio.wait_for(
                    func(*args, **kwargs), timeout=self.config.request_timeout
                )

                # Success - record and potentially close circuit
                duration = time.time() - start_time
                async with self._lock:
                    self._record_success(duration)

                return result

            except (asyncio.TimeoutError, Exception) as e:
                last_exception = e
                logger.warning(
                    f"Circuit breaker '{self.name}' - async attempt {attempt + 1} failed: {e}"
                )

                if attempt < self.config.max_retry_attempts - 1:
                    # Exponential backoff for retries
                    wait_time = min(2**attempt, 10)
                    await asyncio.sleep(wait_time)

        # All retries failed - record failure and potentially open circuit
        duration = time.time() - start_time
        async with self._lock:
            self._record_failure(duration, last_exception)

        raise last_exception

    def _should_allow_request(self) -> bool:
        """Determine if request should be allowed based on circuit state."""
        current_time = time.time()

        if self.state == CircuitState.CLOSED:
            return True
        elif self.state == CircuitState.OPEN:
            # Check if we should try half-open
            if (current_time - self.last_state_change) >= self.config.timeout:
                self._transition_to_half_open()
                return True
            return False
        elif self.state == CircuitState.HALF_OPEN:
            # Allow limited requests in half-open state
            return True

        return False

    def _record_success(self, duration: float) -> None:
        """Record successful operation."""
        self.stats.successful_requests += 1
        self.stats.last_success_time = datetime.utcnow()
        self.consecutive_failures = 0
        self.consecutive_successes += 1

        logger.debug(f"Circuit breaker '{self.name}' - success in {duration:.2f}s")

        # If in half-open, check if we should close
        if self.state == CircuitState.HALF_OPEN:
            if self.consecutive_successes >= self.config.success_threshold:
                self._transition_to_closed()

    def _record_failure(self, duration: float, exception: Optional[Exception]) -> None:
        """Record failed operation."""
        self.stats.failed_requests += 1
        self.stats.last_failure_time = datetime.utcnow()
        self.consecutive_successes = 0
        self.consecutive_failures += 1
        self.last_failure_time = time.time()

        logger.warning(
            f"Circuit breaker '{self.name}' - failure in {duration:.2f}s: {exception}"
        )

        # Check if we should open the circuit
        if (
            self.state in [CircuitState.CLOSED, CircuitState.HALF_OPEN]
            and self.consecutive_failures >= self.config.failure_threshold
        ):
            self._transition_to_open()

    def _transition_to_open(self) -> None:
        """Transition circuit to OPEN state."""
        old_state = self.state
        self.state = CircuitState.OPEN
        self.last_state_change = time.time()
        self.stats.state_changes += 1

        logger.error(
            f"Circuit breaker '{self.name}' opened - {self.consecutive_failures} consecutive failures"
        )
        self._log_state_change(old_state, self.state)

    def _transition_to_half_open(self) -> None:
        """Transition circuit to HALF_OPEN state."""
        old_state = self.state
        self.state = CircuitState.HALF_OPEN
        self.last_state_change = time.time()
        self.consecutive_successes = 0
        self.stats.state_changes += 1

        logger.info(f"Circuit breaker '{self.name}' half-open - testing recovery")
        self._log_state_change(old_state, self.state)

    def _transition_to_closed(self) -> None:
        """Transition circuit to CLOSED state."""
        old_state = self.state
        self.state = CircuitState.CLOSED
        self.last_state_change = time.time()
        self.consecutive_failures = 0
        self.stats.state_changes += 1

        logger.info(f"Circuit breaker '{self.name}' closed - service recovered")
        self._log_state_change(old_state, self.state)

    def _log_state_change(
        self, old_state: CircuitState, new_state: CircuitState
    ) -> None:
        """Log circuit breaker state changes."""
        logger.info(
            "Circuit breaker state change",
            circuit_name=self.name,
            old_state=old_state.value,
            new_state=new_state.value,
            consecutive_failures=self.consecutive_failures,
            consecutive_successes=self.consecutive_successes,
            stats=self.stats.__dict__,
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics."""
        return {
            "name": self.name,
            "state": self.state.value,
            "config": self.config.__dict__,
            "stats": self.stats.__dict__,
            "consecutive_failures": self.consecutive_failures,
            "consecutive_successes": self.consecutive_successes,
            "last_state_change": self.last_state_change,
            "success_rate": (
                self.stats.successful_requests / max(self.stats.total_requests, 1)
            ),
            "failure_rate": (
                self.stats.failed_requests / max(self.stats.total_requests, 1)
            ),
        }

    def reset(self) -> None:
        """Manually reset circuit breaker to closed state."""
        old_state = self.state
        self.state = CircuitState.CLOSED
        self.consecutive_failures = 0
        self.consecutive_successes = 0
        self.last_state_change = time.time()
        self.stats.state_changes += 1

        logger.info(f"Circuit breaker '{self.name}' manually reset")
        self._log_state_change(old_state, self.state)


class CircuitBreakerRegistry:
    """
    Registry for managing multiple circuit breakers.

    Provides centralized management of circuit breakers for different external services.
    """

    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {}
        logger.info("Circuit breaker registry initialized")

    def get_or_create(
        self, name: str, config: Optional[CircuitBreakerConfig] = None
    ) -> CircuitBreaker:
        """Get existing circuit breaker or create new one."""
        if name not in self._breakers:
            self._breakers[name] = CircuitBreaker(name, config)
            logger.info(f"Created circuit breaker for service: {name}")

        return self._breakers[name]

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all circuit breakers."""
        return {name: breaker.get_stats() for name, breaker in self._breakers.items()}

    def reset_all(self) -> None:
        """Reset all circuit breakers."""
        for breaker in self._breakers.values():
            breaker.reset()
        logger.info("All circuit breakers reset")

    def get_failing_services(self) -> list[str]:
        """Get list of services with open circuit breakers."""
        return [
            name
            for name, breaker in self._breakers.items()
            if breaker.state == CircuitState.OPEN
        ]


# Global registry instance
_registry = CircuitBreakerRegistry()


def get_circuit_breaker(
    service_name: str, config: Optional[CircuitBreakerConfig] = None
) -> CircuitBreaker:
    """
    Get circuit breaker for a service.

    Args:
        service_name: Name of the external service
        config: Optional configuration (uses defaults if not provided)

    Returns:
        Circuit breaker instance for the service
    """
    return _registry.get_or_create(service_name, config)


def protect_external_service(
    service_name: str,
    config: Optional[CircuitBreakerConfig] = None,
    fallback_result: Any = None,
):
    """
    Decorator to protect external service calls with circuit breaker.

    Args:
        service_name: Name of the external service
        config: Circuit breaker configuration
        fallback_result: Result to return when circuit is open

    Usage:
        @protect_external_service("openai_api")
        def call_openai_api(prompt: str) -> str:
            # OpenAI API call logic
            return response
    """

    def decorator(func: F) -> F:
        circuit_breaker = get_circuit_breaker(service_name, config)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return circuit_breaker.call(func, *args, **kwargs)
            except CircuitBreakerError as e:
                logger.warning(f"Circuit breaker blocked call to {service_name}: {e}")
                if fallback_result is not None:
                    logger.info(f"Using fallback result for {service_name}")
                    return fallback_result
                raise

        return wrapper

    return decorator


def protect_external_service_async(
    service_name: str,
    config: Optional[CircuitBreakerConfig] = None,
    fallback_result: Any = None,
):
    """
    Decorator to protect async external service calls with circuit breaker.

    Args:
        service_name: Name of the external service
        config: Circuit breaker configuration
        fallback_result: Result to return when circuit is open
    """

    def decorator(func: AsyncF) -> AsyncF:
        circuit_breaker = get_circuit_breaker(service_name, config)

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await circuit_breaker.call_async(func, *args, **kwargs)
            except CircuitBreakerError as e:
                logger.warning(
                    f"Circuit breaker blocked async call to {service_name}: {e}"
                )
                if fallback_result is not None:
                    logger.info(f"Using fallback result for {service_name}")
                    return fallback_result
                raise

        return wrapper

    return decorator


# Pre-configured circuit breakers for Orchestra's external services
def get_openai_circuit_breaker() -> CircuitBreaker:
    """Get circuit breaker configured for OpenAI API."""
    config = CircuitBreakerConfig(
        failure_threshold=3,  # OpenAI failures happen fast
        success_threshold=2,  # Quick recovery test
        timeout=30.0,  # 30 seconds before retry
        recovery_timeout=180.0,  # 3 minutes full recovery
        max_retry_attempts=2,  # Don't overwhelm OpenAI
        request_timeout=60.0,  # OpenAI can be slow
    )
    return get_circuit_breaker("openai_api", config)


def get_temporal_circuit_breaker() -> CircuitBreaker:
    """Get circuit breaker configured for Temporal Cloud."""
    config = CircuitBreakerConfig(
        failure_threshold=5,  # Temporal more resilient
        success_threshold=3,  # Thorough recovery test
        timeout=60.0,  # 1 minute before retry
        recovery_timeout=300.0,  # 5 minutes full recovery
        max_retry_attempts=3,  # Temporal handles retries well
        request_timeout=45.0,  # Temporal operations can be slow
    )
    return get_circuit_breaker("temporal_cloud", config)


def get_pinecone_circuit_breaker() -> CircuitBreaker:
    """Get circuit breaker configured for Pinecone vector database."""
    config = CircuitBreakerConfig(
        failure_threshold=4,  # Vector DB can handle some load
        success_threshold=2,  # Quick recovery
        timeout=45.0,  # 45 seconds before retry
        recovery_timeout=240.0,  # 4 minutes full recovery
        max_retry_attempts=3,  # Reasonable for vector DB
        request_timeout=30.0,  # Vector queries should be fast
    )
    return get_circuit_breaker("pinecone_vector_db", config)


def get_github_circuit_breaker() -> CircuitBreaker:
    """Get circuit breaker configured for GitHub API."""
    config = CircuitBreakerConfig(
        failure_threshold=6,  # GitHub handles high load well
        success_threshold=2,  # Quick recovery test
        timeout=120.0,  # 2 minutes before retry (rate limits)
        recovery_timeout=600.0,  # 10 minutes full recovery
        max_retry_attempts=2,  # Respect GitHub rate limits
        request_timeout=30.0,  # GitHub usually fast
    )
    return get_circuit_breaker("github_api", config)


# Convenience functions for AI agents
def get_circuit_breaker_stats() -> Dict[str, Dict[str, Any]]:
    """Get stats for all circuit breakers."""
    return _registry.get_all_stats()


def get_failing_services() -> list[str]:
    """Get list of currently failing external services."""
    return _registry.get_failing_services()


def reset_all_circuit_breakers() -> None:
    """Reset all circuit breakers - use with caution."""
    _registry.reset_all()
    logger.warning("All circuit breakers have been manually reset")


# Health check function
def circuit_breaker_health_check() -> Dict[str, Any]:
    """
    Check health of all circuit breakers.

    Returns:
        Health status and statistics
    """
    stats = get_circuit_breaker_stats()
    failing_services = get_failing_services()

    total_breakers = len(stats)
    open_breakers = len(failing_services)

    health_status = {
        "healthy": open_breakers == 0,
        "total_circuit_breakers": total_breakers,
        "open_circuit_breakers": open_breakers,
        "failing_services": failing_services,
        "all_stats": stats,
        "summary": f"{total_breakers - open_breakers}/{total_breakers} services healthy",
    }

    if open_breakers > 0:
        logger.warning(
            f"Circuit breaker health check: {open_breakers} services failing"
        )
    else:
        logger.info(
            f"Circuit breaker health check: All {total_breakers} services healthy"
        )

    return health_status
