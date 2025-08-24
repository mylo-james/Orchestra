from pathlib import Path


def test_tag_schema_and_registry_support_exist_story_1_10():
    """Story 1.10 AC1/AC2: Tag schema and registry support required.

    This intentionally fails (RED) until schema and registry APIs exist.
    """

    expected_schema = Path("orchestra/schemas/tags.schema.json")
    expected_registry_module = Path("orchestra/system/tag_registry.py")
    assert expected_schema.exists(), "Expected tags schema to exist."
    assert expected_registry_module.exists(), "Expected tag registry module."

