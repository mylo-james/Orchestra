"""Agent factory and registry with persona support."""

from __future__ import annotations

from typing import Callable, Dict, List, Optional

from src.agents.base.secure_agent import SecureAgent
from src.agents.developer.agent import DeveloperAgent
from src.agents.orchestrator.agent import OrchestratorAgent
from src.agents.release.agent import ReleaseAgent
from src.agents.universal_agent import UniversalAgent
from src.personas.loader import PersonaLoader
from src.personas.specs import PersonaSpec
from src.utils.logging import get_logger

logger = get_logger(__name__)

AgentCtor = Callable[[], SecureAgent]


class AgentRegistry:
    """
    Registry for agent creation with persona support.

    This registry supports both legacy hardcoded agents and new persona-based
    universal agents, providing backward compatibility while enabling the new
    persona system.
    """

    def __init__(self) -> None:
        self._registry: Dict[str, AgentCtor] = {}
        self._persona_loader = PersonaLoader()
        self._legacy_mapping = {
            "orchestrator": "orchestrator",
            "developer": "dev",
            "release": "release",
        }

    def register(self, name: str, constructor: AgentCtor) -> None:
        """Register a legacy agent constructor."""
        self._registry[name] = constructor
        logger.debug(f"Registered legacy agent: {name}")

    def create(
        self, name: str, persona_id: Optional[str] = None, use_persona: bool = True
    ) -> SecureAgent:
        """
        Create an agent by name or persona ID.

        Args:
            name: Agent name (for backward compatibility) or persona ID
            persona_id: Explicit persona ID to use (overrides name)
            use_persona: Whether to use persona system (default True)

        Returns:
            Agent instance
        """
        # If persona_id is explicitly provided, use it
        if persona_id:
            return self._create_persona_agent(persona_id)

        # Check if this is a known legacy agent name
        if name in self._legacy_mapping and use_persona:
            # Map to persona ID and create universal agent
            mapped_persona = self._legacy_mapping[name]
            logger.info(f"Mapping legacy agent '{name}' to persona '{mapped_persona}'")
            return self._create_persona_agent(mapped_persona)

        # Try to create as persona first if use_persona is True
        if use_persona:
            try:
                return self._create_persona_agent(name)
            except ValueError:
                # Fall back to legacy if persona not found
                logger.debug(f"Persona '{name}' not found, trying legacy registry")

        # Fall back to legacy registry
        if name in self._registry:
            logger.info(f"Creating legacy agent: {name}")
            return self._registry[name]()

        raise KeyError(f"Unknown agent or persona: {name}")

    def _create_persona_agent(self, persona_id: str) -> UniversalAgent:
        """
        Create a universal agent with the specified persona.

        Args:
            persona_id: ID of the persona to load

        Returns:
            UniversalAgent instance
        """
        persona_spec = self._persona_loader.load_persona(persona_id)
        if not persona_spec:
            raise ValueError(f"Failed to load persona: {persona_id}")

        logger.info(
            f"Creating universal agent with persona: {persona_spec.display_name}"
        )
        return UniversalAgent(persona_id=persona_id, persona_spec=persona_spec)

    def list_personas(self) -> List[str]:
        """
        List all available persona IDs.

        Returns:
            List of persona IDs
        """
        return self._persona_loader.list_personas()

    def list_agents(self) -> List[str]:
        """
        List all available agents (legacy and personas).

        Returns:
            List of agent/persona names
        """
        legacy_agents = list(self._registry.keys())
        personas = self.list_personas()

        # Combine and deduplicate
        all_agents = list(set(legacy_agents + personas))
        return sorted(all_agents)

    def get_persona_spec(self, persona_id: str) -> Optional[PersonaSpec]:
        """
        Get the persona specification for a given ID.

        Args:
            persona_id: Persona ID to look up

        Returns:
            PersonaSpec if found, None otherwise
        """
        return self._persona_loader.load_persona(persona_id)

    def reload_personas(self) -> None:
        """Reload all personas from disk."""
        self._persona_loader.reload_all()
        logger.info("Personas reloaded")


# Global registry instance
_global_registry: Optional[AgentRegistry] = None


def get_registry() -> AgentRegistry:
    """Get or create the global agent registry."""
    global _global_registry
    if _global_registry is None:
        _global_registry = default_registry()
    return _global_registry


def default_registry() -> AgentRegistry:
    """
    Create the default agent registry with legacy agents.

    Note: Legacy agents are still registered for backward compatibility,
    but the persona system is preferred for new agents.
    """
    registry = AgentRegistry()

    # Register legacy agents for backward compatibility
    registry.register("orchestrator_legacy", OrchestratorAgent)
    registry.register("developer_legacy", DeveloperAgent)
    registry.register("release_legacy", ReleaseAgent)

    logger.info("Agent registry initialized with persona support")
    return registry


# Convenience class for backward compatibility
class AgentFactory:
    """Backward compatibility wrapper for agent creation."""

    @staticmethod
    def create(agent_type: str, **kwargs) -> SecureAgent:
        """Create an agent of the specified type."""
        return get_registry().create(agent_type, **kwargs)

    @staticmethod
    def list_agents() -> List[str]:
        """List all available agents."""
        return get_registry().list_agents()

    @staticmethod
    def list_personas() -> List[str]:
        """List all available personas."""
        return get_registry().list_personas()
