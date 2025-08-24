from pathlib import Path


def test_persona_mapping_schema_defined_story_1_1_and_1_2():
    """Story 1.1 AC2 and Story 1.2 AC2/AC3: persona schema validator expected.

    This intentionally fails (RED) until a JSON Schema and validator exist, e.g.,
    `orchestra/schemas/persona.schema.json` and a validation utility.
    """

    expected_schema = Path("orchestra/schemas/persona.schema.json")
    assert expected_schema.exists(), (
        "Expected persona JSON Schema for validating converted personas."
    )


def test_task_template_checklist_resource_schemas_defined_story_1_3():
    """Story 1.3 AC1/AC3: resource schemas for tasks/templates/checklists expected.

    This intentionally fails (RED) until JSON Schemas exist and CI validation is wired.
    """

    expected_task_schema = Path("orchestra/schemas/task.schema.json")
    expected_template_schema = Path("orchestra/schemas/template.schema.json")
    expected_checklist_schema = Path("orchestra/schemas/checklist.schema.json")

    assert expected_task_schema.exists(), "Expected task schema to be defined."
    assert expected_template_schema.exists(), "Expected template schema to be defined."
    assert expected_checklist_schema.exists(), "Expected checklist schema to be defined."

