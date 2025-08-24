from pathlib import Path


def test_inventory_scanner_module_exists_for_bmad_content_inventory_story_1_1():
    """Story 1.1 AC1: Expect a dedicated inventory scanner module to exist.

    This intentionally fails (RED) until `orchestra/system/resource_inventory.py`
    is implemented to scan `.bmad-core/{agents,tasks,templates,checklists}` and
    produce a categorized inventory with versions/IDs.
    """

    expected_module = Path("orchestra/system/resource_inventory.py")
    assert expected_module.exists(), (
        "Expected resource inventory scanner module to exist for Story 1.1 "
        "(implement scanning and categorization of BMad content)."
    )


def test_inventory_scanner_outputs_plan_with_directory_structure_story_1_1():
    """Story 1.1 AC5: Expect a plan output (dir structure + filenames) to be generated.

    This intentionally fails (RED) until the conversion plan generator writes an
    artifact, e.g., `docs/inventory/conversion-plan.json` or similar.
    """

    # The exact filename can be adjusted during implementation; this asserts that
    # a concrete artifact is produced as part of the inventory/conversion planning.
    expected_plan_artifact = Path("docs/inventory/conversion-plan.json")
    assert expected_plan_artifact.exists(), (
        "Expected conversion plan artifact (directory structure + filenames) "
        "for Story 1.1 to exist at docs/inventory/conversion-plan.json."
    )

