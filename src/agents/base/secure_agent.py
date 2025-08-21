"""Base secure agent and OpenAI client wrapper built on OpenAI SDK v1.x.

All I/O is async for Temporal compatibility. Includes correlation ID logging and
simple retry logic.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Dict, Optional

import openai
from openai import AsyncOpenAI

from src.config.settings import get_settings
from src.utils.logging import get_logger, set_agent_context
from .monitoring import AgentMonitor


logger = get_logger(__name__)


@dataclass
class ModelConfig:
    model: str
    temperature: float
    max_tokens: int


class OpenAIClient:
    """Shared Async OpenAI client with minimal retries and logging."""

    def __init__(self, api_key: str, model_cfg: ModelConfig):
        self._client = AsyncOpenAI(api_key=api_key)
        self._model_cfg = model_cfg

    async def chat(self, messages: list[dict[str, str]], *, model: Optional[str] = None,
                   temperature: Optional[float] = None, max_tokens: Optional[int] = None,
                   retries: int = 2) -> str:
        attempt = 0
        last_error: Optional[Exception] = None
        selected_model = model or self._model_cfg.model
        selected_temp = temperature if temperature is not None else self._model_cfg.temperature
        selected_max = max_tokens if max_tokens is not None else self._model_cfg.max_tokens

        while attempt <= retries:
            try:
                resp = await self._client.chat.completions.create(
                    model=selected_model,
                    messages=messages,
                    temperature=selected_temp,
                    max_tokens=selected_max,
                )
                # Some test doubles might return a coroutine-like object.
                if asyncio.iscoroutine(resp):
                    resp = await resp  # type: ignore[assignment]
                content = resp.choices[0].message.content or ""
                logger.info("openai_chat_success", model=selected_model, tokens=selected_max)
                return content
            except Exception as e:  # noqa: BLE001
                last_error = e
                logger.warning("openai_chat_retry", attempt=attempt, error=str(e))
                await asyncio.sleep(min(0.5 * (2 ** attempt), 2.0))
                attempt += 1

        logger.error("openai_chat_failure", error=str(last_error))
        raise last_error  # type: ignore[misc]


class SecureAgent:
    """Base class for all agents with OpenAI client and monitoring."""

    agent_name: str = "secure_agent"

    def __init__(self, settings=None, model_cfg: Optional[ModelConfig] = None):
        self.settings = settings or get_settings()
        set_agent_context(self.agent_name)
        self.monitor = AgentMonitor(self.agent_name)

        default_cfg = ModelConfig(
            model=self.settings.openai.model,
            temperature=self.settings.openai.temperature,
            max_tokens=self.settings.openai.max_tokens,
        )
        self.openai = OpenAIClient(api_key=self.settings.openai.api_key, model_cfg=model_cfg or default_cfg)

    async def start(self) -> None:
        logger.info("agent_started", agent=self.agent_name)

    async def stop(self) -> None:
        logger.info("agent_stopped", agent=self.agent_name)

    async def ask(self, user_message: str, system_prompt: str | None = None) -> str:
        """Default chat behavior using OpenAI client."""
        messages: list[Dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_message})

        async with self.monitor.time("openai_chat", {"length": len(user_message)}):
            return await self.openai.chat(messages)

