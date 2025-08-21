from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from pydantic import ValidationError

from src.personas.specs import PersonaSpec


PERSONA_DIR_PRIMARY = Path("src/agents/personas")
PERSONA_DIR_SECONDARY = Path(".bmad-core/agents/personas")


class PersonaNotFoundError(FileNotFoundError):
    pass


def _load_yaml_file(path: Path) -> dict:
    try:
        with path.open("r", encoding="utf-8") as f:
            # SafeLoader prevents code execution
            return yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        raise ValueError(f"YAML parsing error in {path}: {e}") from e


def _candidate_paths(persona_id: str) -> List[Path]:
    return [
        PERSONA_DIR_PRIMARY / f"{persona_id}.yaml",
        PERSONA_DIR_SECONDARY / f"{persona_id}.yaml",
    ]


@lru_cache(maxsize=64)
def load_persona(persona_id: str) -> PersonaSpec:
    """Load a persona by id with precedence: src/ > .bmad-core/.

    Caches successful loads for speed.
    """
    for path in _candidate_paths(persona_id):
        if path.exists():
            data = _load_yaml_file(path)
            try:
                return PersonaSpec.model_validate(data)
            except ValidationError as e:
                raise ValueError(f"Invalid persona spec in {path}: {e}") from e
    raise PersonaNotFoundError(f"Persona '{persona_id}' not found in {PERSONA_DIR_PRIMARY} or {PERSONA_DIR_SECONDARY}")


def list_personas() -> List[str]:
    """List available persona IDs from both directories, de-duplicated with primary precedence."""
    found: Dict[str, Path] = {}
    if PERSONA_DIR_SECONDARY.exists():
        for p in PERSONA_DIR_SECONDARY.glob("*.yaml"):
            found[p.stem] = p
    if PERSONA_DIR_PRIMARY.exists():
        for p in PERSONA_DIR_PRIMARY.glob("*.yaml"):
            # primary overrides
            found[p.stem] = p
    return sorted(found.keys())


def invalidate_cache(persona_id: Optional[str] = None) -> None:
    if persona_id is None:
        load_persona.cache_clear()
    else:
        try:
            load_persona.cache_pop(persona_id)
        except KeyError:
            pass