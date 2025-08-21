"""Activity wrappers for external calls used by workflows.

These mimic Temporal activities by isolating external side effects, adding
timeouts, retries, and circuit breaker protections.
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Awaitable

from src.utils.circuit_breaker import (
    protect_external_service_async,
    get_openai_circuit_breaker,
)
from src.utils.logging import get_logger


logger = get_logger(__name__)


def with_timeout(timeout_seconds: float):
    """Decorator to enforce async timeout using asyncio.wait_for."""

    def decorator(func: Callable[..., Awaitable[Any]]):
        async def wrapper(*args, **kwargs):
            return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout_seconds)

        return wrapper

    return decorator


@protect_external_service_async("openai_api", fallback_result="fallback:openai")
@with_timeout(30.0)  # Planning operations default
async def run_planning_activity(callable_fn: Callable[[], Awaitable[str]]) -> str:
    """Run a planning operation safeguarded as an activity."""
    return await callable_fn()


@protect_external_service_async("openai_api", fallback_result="fallback:codegen")
@with_timeout(120.0)  # Code generation operations
async def run_code_generation_activity(callable_fn: Callable[[], Awaitable[str]]) -> str:
    """Run code generation safeguarded as an activity."""
    return await callable_fn()


@protect_external_service_async("github_api", fallback_result="fallback:pr")
@with_timeout(60.0)  # PR creation operations
async def run_pr_activity(callable_fn: Callable[[], Awaitable[str]]) -> str:
    """Run PR-related operations safeguarded as an activity."""
    return await callable_fn()


@protect_external_service_async("openai_api", fallback_result="fallback:knowledge")
@with_timeout(10.0)  # Knowledge lookups
async def run_knowledge_activity(callable_fn: Callable[[], Awaitable[str]]) -> str:
    """Run knowledge operations safeguarded as an activity."""
    return await callable_fn()

