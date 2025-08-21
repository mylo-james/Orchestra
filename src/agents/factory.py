"""Persona-based agent factory."""

from __future__ import annotations

from typing import List

from src.agents.universal_agent import UniversalAgent
from src.personas.loader import list_personas as _list_personas


def create_persona_agent(persona_id: str) -> UniversalAgent:
    """Create a UniversalAgent for the given persona id."""
    return UniversalAgent(persona_id=persona_id)


def list_personas() -> List[str]:
    """List available persona ids."""
    return _list_personas()
