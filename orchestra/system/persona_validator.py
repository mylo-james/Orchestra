"""Persona validator placeholder (Story 1.2)."""

from __future__ import annotations

from pathlib import Path


def schema_path() -> Path:
    return Path("orchestra/schemas/persona.schema.json")


def validate_persona(path: Path) -> list[str]:
    """Placeholder validator returning an error if schema missing.

    This will be replaced by a real JSON Schema validation.
    """
    if not schema_path().exists():
        return ["persona schema missing"]
    # Real validation would go here
    return []

