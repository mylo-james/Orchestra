from pathlib import Path


def test_overlay_merge_engine_module_exists_story_1_5():
    """Story 1.5 AC1/AC3: Deterministic overlay merge engine required.

    This intentionally fails (RED) until merge engine exists.
    """

    expected_module = Path("orchestra/system/overlay_merge_engine.py")
    assert expected_module.exists(), (
        "Expected overlay merge engine module to exist for Story 1.5."
    )


def test_overlay_schema_exists_story_1_5():
    """Story 1.5 AC2/AC5: Overlay JSON Schema required with CI validation.

    This intentionally fails (RED) until schema file exists.
    """

    expected_schema = Path("orchestra/schemas/overlay.schema.json")
    assert expected_schema.exists(), "Expected overlay JSON Schema to exist."

