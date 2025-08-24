from pathlib import Path


def test_namespace_model_defined_story_1_8():
    """Story 1.8 AC1: Namespace model with naming conventions must be defined.

    This intentionally fails (RED) until the namespace model is implemented.
    """

    expected_module = Path("orchestra/system/namespace_model.py")
    assert expected_module.exists(), (
        "Expected namespace model module to exist for Story 1.8."
    )

