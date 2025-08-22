"""Agent factory with persona-based agent creation."""

from typing import List, Optional

from src.system.agent import UniversalAgent
from src.system.loader import PersonaLoader
from src.system.specs import PersonaSpec
from src.utils.logging import get_logger

logger = get_logger(__name__)


class AgentRegistry:
    """
    Registry for persona-based agent creation.

    All agents are created as UniversalAgent instances with
    different personas loaded from YAML files.
    """

    def __init__(self):
        """Initialize the agent registry."""
        self._persona_loader = PersonaLoader()

    def create(self, persona_id: str) -> UniversalAgent:
        """
        Create an agent with the specified persona.

        Args:
            persona_id: ID of the persona to load

        Returns:
            UniversalAgent instance with the specified persona

        Raises:
            ValueError: If persona not found or invalid
        """
        persona_spec = self._persona_loader.load_persona(persona_id)
        if not persona_spec:
            available = self.list_personas()
            raise ValueError(
                f"Persona '{persona_id}' not found. "
                f"Available personas: {', '.join(available)}"
            )

        logger.info(f"Creating agent with persona: {persona_spec.display_name}")
        return UniversalAgent(persona_id=persona_id, persona_spec=persona_spec)

    def list_personas(self) -> List[str]:
        """
        List all available persona IDs.

        Returns:
            List of persona IDs
        """
        return self._persona_loader.list_personas()

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
        _global_registry = AgentRegistry()
        logger.info("Agent registry initialized")
    return _global_registry


# Convenience functions
def create_agent(persona_id: str) -> UniversalAgent:
    """
    Create an agent with the specified persona.

    Args:
        persona_id: ID of the persona to use

    Returns:
        UniversalAgent instance
    """
    return get_registry().create(persona_id)


def list_personas() -> List[str]:
    """
    List all available personas.

    Returns:
        List of persona IDs
    """
    return get_registry().list_personas()
