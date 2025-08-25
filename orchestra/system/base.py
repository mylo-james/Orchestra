"""Base secure agent built on OpenAI SDK.

Provides Agent creation using OpenAI SDK patterns with session management,
tracing, and proper tool integration. All operations are async for Temporal compatibility.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional, TypeVar

from openai import AsyncOpenAI

from orchestra.config.settings import get_settings
from orchestra.system.monitoring import AgentMonitor
from orchestra.utils.logging import get_logger, set_agent_context

logger = get_logger(__name__)

T = TypeVar("T")


@dataclass
class AgentContext:
    """Context for agent operations."""

    correlation_id: str
    agent_name: str
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class SecureAgent:
    """
    Base secure agent class for Orchestra.

    Provides security validation, audit logging, and monitoring
    without depending on external agent frameworks.
    """

    def __init__(
        self,
        name: str,
        correlation_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ):
        """
        Initialize the secure agent.

        Args:
            name: Agent name for identification
            correlation_id: Correlation ID for tracing
            session_id: Session ID for state management
        """
        self.name = name
        if correlation_id:
            self.correlation_id = correlation_id
        else:
            try:
                current_task = asyncio.current_task()
                task_name = current_task.get_name() if current_task else "sync"
            except RuntimeError:
                # No event loop running
                task_name = "sync"
            self.correlation_id = f"agent-{name}-{task_name}"
        self.session_id = session_id
        self.settings = get_settings()
        self.monitor = AgentMonitor(agent_name=name)
        self.client = AsyncOpenAI(api_key=self.settings.openai.api_key)

        # Set logging context
        set_agent_context(self.name)

        logger.info(f"Initialized SecureAgent: {name}")

    async def execute_with_monitoring(
        self, operation: str, func: Callable[..., Any], *args, **kwargs
    ) -> Any:
        """
        Execute an operation with monitoring and error handling.

        Args:
            operation: Name of the operation for monitoring
            func: Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            Result of the function execution
        """
        async with self.monitor.time(operation):
            logger.info(f"Starting operation: {operation}")

            # Execute the function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            logger.info(f"Completed operation: {operation}")
            return result

    async def validate_input(self, input_data: Any) -> bool:
        """
        Validate input data for security and correctness.

        Args:
            input_data: Data to validate

        Returns:
            True if valid, False otherwise
        """
        # Basic validation - can be extended
        if input_data is None:
            return False

        # Add more validation logic as needed
        return True

    async def validate_output(self, output_data: Any) -> bool:
        """
        Validate output data for security and correctness.

        Args:
            output_data: Data to validate

        Returns:
            True if valid, False otherwise
        """
        # Basic validation - can be extended
        if output_data is None:
            return False

        # Add more validation logic as needed
        return True

    def get_context(self) -> AgentContext:
        """Get the current agent context."""
        return AgentContext(
            correlation_id=self.correlation_id,
            agent_name=self.name,
            session_id=self.session_id,
        )

    async def cleanup(self) -> None:
        """Clean up agent resources."""
        logger.info(f"Cleaning up SecureAgent: {self.name}")

        # Close OpenAI client if needed
        if hasattr(self.client, "close"):
            await self.client.close()


class FunctionTool:
    """Simple function tool wrapper for compatibility."""

    def __init__(self, name: str, description: str, func: Callable[..., Any]):
        """Initialize function tool."""
        self.name = name
        self.description = description
        self.func = func

    async def execute(self, *args, **kwargs) -> Any:
        """Execute the tool function."""
        if asyncio.iscoroutinefunction(self.func):
            return await self.func(*args, **kwargs)
        else:
            return self.func(*args, **kwargs)
