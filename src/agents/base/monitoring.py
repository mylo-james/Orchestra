"""Agent monitoring utilities.

Provides lightweight observability hooks that integrate with the project's
structured logging and correlation ID tracking. These hooks are intentionally
simple and do not pull in additional metrics libraries. They can be wired into
external monitoring later if needed.
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncIterator, Optional

from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class AgentMetric:
    """Represents a single agent metric event."""

    name: str
    duration_ms: Optional[float] = None
    success: Optional[bool] = None
    details: Optional[dict] = None


class AgentMonitor:
    """Simple monitor for agent operations with timing and success flags."""

    def __init__(self, agent_name: str):
        self.agent_name = agent_name

    def emit(self, metric: AgentMetric) -> None:
        """Emit a metric via structured logs for dashboarding later."""
        logger.info(
            "agent_metric",
            agent=self.agent_name,
            metric=metric.name,
            duration_ms=metric.duration_ms,
            success=metric.success,
            details=metric.details or {},
        )

    @asynccontextmanager
    async def time(
        self, name: str, details: Optional[dict] = None
    ) -> AsyncIterator[None]:
        """Async context manager to record duration and success for a block."""
        start = time.perf_counter()
        try:
            yield
        except Exception:
            duration_ms = (time.perf_counter() - start) * 1000.0
            self.emit(
                AgentMetric(
                    name=name, duration_ms=duration_ms, success=False, details=details
                )
            )
            raise
        else:
            duration_ms = (time.perf_counter() - start) * 1000.0
            self.emit(
                AgentMetric(
                    name=name, duration_ms=duration_ms, success=True, details=details
                )
            )
