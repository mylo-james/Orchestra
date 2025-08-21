"""Developer agent tools registry binding GitHub tools."""

from __future__ import annotations

from src.agents.tools import ToolRegistry
from src.agents.tools.github import create_pr_tool


def developer_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(create_pr_tool)
    return registry

