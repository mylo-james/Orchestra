from pathlib import Path


def test_policy_versioning_model_exists_story_1_12():
    """Story 1.12 AC1: Policy versioning model with metadata required.

    This intentionally fails (RED) until model is added.
    """

    expected_module = Path("orchestra/system/policy_versioning.py")
    assert expected_module.exists(), (
        "Expected policy versioning module to exist for Story 1.12."
    )

