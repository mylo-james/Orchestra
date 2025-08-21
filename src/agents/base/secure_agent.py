"""Base secure agent built on OpenAI Agents SDK.

Provides Agent creation using OpenAI Agents SDK patterns with session management,
tracing, and proper tool integration. All operations are async for Temporal compatibility.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional, TypeVar
from dataclasses import dataclass

from agents import Agent, Runner, FunctionTool, Session, SQLiteSession
from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel

from src.config.settings import get_settings
from src.utils.logging import get_logger, set_agent_context

from .monitoring import AgentMonitor

logger = get_logger(__name__)

TContext = TypeVar("TContext")


@dataclass
class AgentContext:
    """Context object passed to agent tools and operations."""

    correlation_id: Optional[str] = None
    agent_name: Optional[str] = None
    session_data: Dict[str, Any] = None

    def __post_init__(self):
        if self.session_data is None:
            self.session_data = {}


@dataclass
class ModelConfig:
    """Configuration for OpenAI model parameters."""

    model: str
    temperature: float
    max_tokens: int


class SecureAgent:
    """Base class for all agents using OpenAI Agents SDK with monitoring."""

    agent_name: str = "secure_agent"

    def __init__(
        self,
        settings=None,
        model_cfg: Optional[ModelConfig] = None,
        instructions: Optional[str] = None,
        tools: Optional[List[FunctionTool]] = None
    ):
        self.settings = settings or get_settings()
        set_agent_context(self.agent_name)
        self.monitor = AgentMonitor(self.agent_name)

        # Configure model with settings
        default_cfg = ModelConfig(
            model=self.settings.openai.model,
            temperature=self.settings.openai.temperature,
            max_tokens=self.settings.openai.max_tokens,
        )
        self.model_cfg = model_cfg or default_cfg

        # Create OpenAI model instance for Agents SDK
        self.model = OpenAIChatCompletionsModel(
            model_name=self.model_cfg.model,
            api_key=self.settings.openai.api_key,
            temperature=self.model_cfg.temperature,
            max_tokens=self.model_cfg.max_tokens,
        )

        # Create the Agent using OpenAI Agents SDK
        self.agent = Agent[AgentContext](
            name=self.agent_name,
            model=self.model,
            instructions=instructions or f"You are {self.agent_name}, a helpful AI assistant.",
            tools=tools or [],
        )

        # Session for conversation management
        self.session: Optional[Session] = None
        self.runner = Runner()

    async def start(self) -> None:
        """Initialize the agent and create a session."""
        logger.info("agent_started", agent=self.agent_name)

        # Create SQLite session for conversation persistence
        self.session = SQLiteSession(
            database_path=f".ai/sessions/{self.agent_name}_sessions.db"
        )

    async def stop(self) -> None:
        """Stop the agent and clean up resources."""
        logger.info("agent_stopped", agent=self.agent_name)
        if self.session:
            await asyncio.get_event_loop().run_in_executor(None, self.session.close)

    async def ask(self, user_message: str, context: Optional[AgentContext] = None) -> str:
        """Run a conversation using the OpenAI Agents SDK."""
        if not self.session:
            await self.start()

        # Create or use provided context
        if context is None:
            context = AgentContext(
                agent_name=self.agent_name,
                correlation_id=f"{self.agent_name}_{asyncio.current_task()}"
            )

        async with self.monitor.time("agent_run", {"message_length": len(user_message)}):
            try:
                # Run the agent with the user message
                result = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.runner.run_sync(
                        agent=self.agent,
                        messages=[user_message],
                        context=context,
                        session=self.session,
                    )
                )

                # Extract the final output from the result
                if hasattr(result, 'final_output') and result.final_output:
                    response = str(result.final_output)
                elif hasattr(result, 'messages') and result.messages:
                    # Get the last message from the agent
                    response = str(result.messages[-1].content) if result.messages[-1].content else ""
                else:
                    response = "No response generated"

                logger.info(
                    "agent_run_success",
                    agent=self.agent_name,
                    input_length=len(user_message),
                    output_length=len(response)
                )
                return response

            except Exception as e:
                logger.error("agent_run_failure", agent=self.agent_name, error=str(e))
                raise

    def add_tool(self, tool: FunctionTool) -> None:
        """Add a tool to the agent's toolkit."""
        if tool not in self.agent.tools:
            self.agent.tools.append(tool)
