"""Orchestra System - Core persona-based agent system."""

from orchestra.system.agent import UniversalAgent
from orchestra.system.base import AgentContext, SecureAgent
from orchestra.system.factory import create_agent, get_registry, list_personas
from orchestra.system.loader import PersonaLoader
from orchestra.system.monitoring import AgentMonitor
from orchestra.system.specs import (
    BehavioralContract,
    CommandDefinition,
    CommandInterface,
    KnowledgeContext,
    PersonaIdentity,
    PersonaSpec,
    ResourceDependencies,
)
from orchestra.system.tools import create_github_pr_tool, list_repositories_tool

__all__ = [
    # Core classes
    "UniversalAgent",
    "SecureAgent",
    "AgentContext",
    "AgentMonitor",
    # Factory functions
    "create_agent",
    "get_registry",
    "list_personas",
    # Persona system
    "PersonaLoader",
    "PersonaSpec",
    "PersonaIdentity",
    "BehavioralContract",
    "CommandInterface",
    "CommandDefinition",
    "ResourceDependencies",
    "KnowledgeContext",
    # Tools
    "create_github_pr_tool",
    "list_repositories_tool",
]
