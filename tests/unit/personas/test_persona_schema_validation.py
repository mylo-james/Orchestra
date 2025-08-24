from pathlib import Path


def test_persona_schema_and_validator_exist_story_1_2():
    """Story 1.2 AC2/AC3: Persona schema and validator must exist.

    This test intentionally fails (RED) until the schema file and a validator
    utility are implemented.
    """

    schema_path = Path("orchestra/schemas/persona.schema.json")
    validator_module = Path("orchestra/system/persona_validator.py")

    assert schema_path.exists(), "Expected persona JSON Schema to exist."
    assert validator_module.exists(), "Expected persona validator module to exist."

