from pathlib import Path


def test_context_init_command_module_exists_story_1_9():
    """Story 1.9 AC1: CLI context init command should exist.

    This intentionally fails (RED) until the command module is present.
    """

    expected_module = Path("orchestra/cli/context_commands.py")
    assert expected_module.exists(), (
        "Expected CLI context commands module to exist for Story 1.9."
    )

