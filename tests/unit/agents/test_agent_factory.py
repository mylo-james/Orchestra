import pytest

from src.agents.factory import default_registry
from src.agents.orchestrator.agent import OrchestratorAgent
from src.agents.developer.agent import DeveloperAgent
from src.agents.release.agent import ReleaseAgent


def test_default_registry_creates_agents():
    registry = default_registry()

    orch = registry.create("orchestrator")
    dev = registry.create("developer")
    rel = registry.create("release")

    assert isinstance(orch, OrchestratorAgent)
    assert isinstance(dev, DeveloperAgent)
    assert isinstance(rel, ReleaseAgent)


def test_unknown_agent_raises():
    registry = default_registry()
    with pytest.raises(KeyError):
        registry.create("unknown")

