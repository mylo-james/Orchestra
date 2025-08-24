from pathlib import Path


def test_overlays_directory_scaffolding_exists_story_1_6():
    """Story 1.6 AC1/AC2: Expect teams/ and projects/ scaffolding with examples.

    This intentionally fails (RED) until scaffolding is created.
    """

    teams_dir = Path("teams")
    projects_dir = Path("projects")
    assert teams_dir.exists(), "Expected teams/ directory to exist."
    assert projects_dir.exists(), "Expected projects/ directory to exist."

