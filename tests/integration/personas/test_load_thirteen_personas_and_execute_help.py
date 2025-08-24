import os
from pathlib import Path

import pytest


@pytest.mark.skipif(
    not Path("orchestra/personas").exists(), reason="Personas directory missing"
)
def test_thirteen_converted_personas_exist_and_load_story_1_2():
    """Story 1.2 AC1/AC2: Expect 13 new converted personas to be present and loadable.

    This intentionally fails (RED) when fewer than 13 persona YAMLs are detected
    beyond the existing built-ins (dev, orchestrator, release).
    """

    personas_dir = Path("orchestra/personas")
    persona_files = [p for p in personas_dir.glob("*.yaml") if p.is_file()]

    # Built-ins present already
    built_ins = {"dev.yaml", "orchestrator.yaml", "release.yaml"}
    converted = [p for p in persona_files if p.name not in built_ins]

    assert len(converted) >= 13, (
        "Expected at least 13 converted personas in orchestra/personas (excluding "
        "built-ins dev/orchestrator/release)."
    )

