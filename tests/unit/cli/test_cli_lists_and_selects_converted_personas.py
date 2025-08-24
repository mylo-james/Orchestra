from pathlib import Path


def test_cli_persona_discovery_integration_module_exists_story_1_4():
    """Story 1.4 AC1: CLI should discover personas from resource registry.

    This intentionally fails (RED) until discovery integration exists.
    """

    expected_module = Path("orchestra/cli/persona_discovery.py")
    assert expected_module.exists(), (
        "Expected CLI discovery integration module to exist for Story 1.4."
    )


def test_cli_persona_activation_flow_component_exists_story_1_4():
    """Story 1.4 AC1/AC2: Selection/activation flow should be implemented.

    This intentionally fails (RED) until activation flow adapter exists.
    """

    expected_adapter = Path("orchestra/cli/persona_activation.py")
    assert expected_adapter.exists(), (
        "Expected CLI persona activation adapter to exist for Story 1.4."
    )

