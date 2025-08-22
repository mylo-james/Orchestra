"""Persona system for the Universal Agent framework."""

from src.personas.loader import PersonaLoader
from src.personas.specs import (
    BehavioralContract,
    CommandDefinition,
    CommandInterface,
    KnowledgeContext,
    PersonaIdentity,
    PersonaSpec,
    ResourceDependencies,
)

__all__ = [
    "PersonaLoader",
    "PersonaSpec",
    "PersonaIdentity",
    "BehavioralContract",
    "CommandInterface",
    "CommandDefinition",
    "ResourceDependencies",
    "KnowledgeContext",
]
