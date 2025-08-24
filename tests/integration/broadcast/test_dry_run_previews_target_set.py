from pathlib import Path


def test_broadcast_dry_run_module_exists_story_1_11():
    """Story 1.11 AC1: Dry-run with preview of target set must exist.

    This intentionally fails (RED) until a broadcast module is available.
    """

    expected_module = Path("orchestra/system/broadcast.py")
    assert expected_module.exists(), "Expected broadcast module to exist."

