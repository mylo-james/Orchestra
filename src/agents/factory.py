"""Agent factory and registry."""

from __future__ import annotations

from typing import Callable, Dict, Type

from src.agents.base.secure_agent import SecureAgent
from src.agents.developer.agent import DeveloperAgent
from src.agents.orchestrator.agent import OrchestratorAgent
from src.agents.release.agent import ReleaseAgent


AgentCtor = Callable[[], SecureAgent]


class AgentRegistry:
    """Simple registry mapping agent names to constructors."""

    def __init__(self) -> None:
        self._registry: Dict[str, AgentCtor] = {}

    def register(self, name: str, constructor: AgentCtor) -> None:
        self._registry[name] = constructor

    def create(self, name: str) -> SecureAgent:
        if name not in self._registry:
            raise KeyError(f"Unknown agent: {name}")
        return self._registry[name]()


def default_registry() -> AgentRegistry:
    registry = AgentRegistry()
    registry.register("orchestrator", OrchestratorAgent)
    registry.register("developer", DeveloperAgent)
    registry.register("release", ReleaseAgent)
    return registry

