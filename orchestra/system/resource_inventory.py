"""Resource inventory scanner for BMad content (Story 1.1).

This module will scan `.bmad-core/agents`, `.bmad-core/tasks`,
`.bmad-core/templates`, and `.bmad-core/checklists` to produce a categorized
inventory with optional version/ID metadata.

Current implementation is a placeholder to satisfy presence checks.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


@dataclass
class InventoryItem:
    path: Path
    type: str
    id: str
    version: str | None = None


def discover_bmad_content(root: Path = Path(".bmad-core")) -> Dict[str, List[InventoryItem]]:
    """Discover BMad content under the given root directory.

    Returns a dictionary keyed by content type.
    """
    types = {
        "agents": root / "agents",
        "tasks": root / "tasks",
        "templates": root / "templates",
        "checklists": root / "checklists",
    }

    inventory: Dict[str, List[InventoryItem]] = {k: [] for k in types}

    for content_type, base_dir in types.items():
        if not base_dir.exists():
            continue
        for p in base_dir.glob("**/*"):
            if p.is_file():
                inventory[content_type].append(
                    InventoryItem(path=p, type=content_type, id=p.stem)
                )

    return inventory

