from importlib import import_module


def test_context_aware_loader_api_exists_story_1_7():
    """Story 1.7 AC1: load_persona(pid, team_id, project_id) API must exist.

    This intentionally fails (RED) until the module and function exist.
    """

    try:
        mod = import_module("orchestra/system/context_loader")
        has_api = hasattr(mod, "load_persona")
    except Exception:
        has_api = False

    assert has_api, (
        "Expected context-aware loader API 'load_persona(pid, team_id, project_id)'."
    )

