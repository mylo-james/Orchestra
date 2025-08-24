from pathlib import Path


def test_ci_schema_validation_hook_exists_story_1_3():
    """Story 1.3 AC3: CI schema validation must be present.

    This intentionally fails (RED) until a CI script/hook exists, e.g.,
    `scripts/validate-resources.py` or similar, and is wired into CI.
    """

    expected_validator = Path("scripts/validate-resources.py")
    assert expected_validator.exists(), (
        "Expected CI resource schema validation script to exist."
    )

