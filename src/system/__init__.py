"""Orchestra System - Core persona-based agent system."""

from src.system.agent import UniversalAgent
from src.system.base import AgentContext, SecureAgent
from src.system.factory import create_agent, get_registry, list_personas
from src.system.loader import PersonaLoader
from src.system.monitoring import AgentMonitor
from src.system.specs import (
    BehavioralContract,
    CommandDefinition,
    CommandInterface,
    KnowledgeContext,
    PersonaIdentity,
    PersonaSpec,
    ResourceDependencies,
)
from src.system.tools import create_github_pr_tool, list_repositories_tool

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
