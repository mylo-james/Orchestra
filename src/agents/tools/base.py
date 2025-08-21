"""Simple tool definition and registry for agents."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, Optional, Type

from pydantic import BaseModel, ValidationError


ToolFunc = Callable[[BaseModel], Awaitable[Dict[str, Any]]]


@dataclass
class ToolDefinition:
    name: str
    description: str
    input_model: Type[BaseModel]
    func: ToolFunc


class ToolRegistry:
    """Registry for tools accessible to an agent."""

    def __init__(self) -> None:
        self._tools: Dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolDefinition:
        if name not in self._tools:
            raise KeyError(f"Unknown tool: {name}")
        return self._tools[name]

    async def call(self, name: str, payload: dict) -> Dict[str, Any]:
        tool = self.get(name)
        try:
            parsed = tool.input_model(**payload)
        except ValidationError as exc:  # noqa: PERF203
            raise ValueError(f"Invalid input for tool '{name}': {exc}") from exc
        return await tool.func(parsed)

