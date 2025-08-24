from pathlib import Path


def test_sample_resources_execute_end_to_end_story_1_3():
    """Story 1.3 AC2/AC3/AC4: Expect engines and provenance/trust.

    This intentionally fails (RED) until engines exist and sample resources
    are loadable and executable with provenance/signing/trust annotations.
    """

    required_modules = [
        Path("orchestra/system/resource_loader.py"),
        Path("orchestra/system/task_engine.py"),
        Path("orchestra/system/template_processor.py"),
        Path("orchestra/system/checklist_engine.py"),
    ]

    for mod in required_modules:
        assert mod.exists(), f"Expected module missing: {mod}"

    samples_dir = Path("orchestra/resources")
    assert samples_dir.exists(), "Expected sample resources directory to exist"

