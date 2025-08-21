import asyncio
import pytest

from src.workflows.dev_team_workflow import DevTeamWorkflow


@pytest.mark.asyncio
async def test_workflow_lifecycle_minimal(monkeypatch):
    # Stub agent methods to avoid network calls
    async def fake_plan(self, goal: str, context=None):
        return "PLAN: do X then Y"

    async def fake_impl(self, task: str, context=None):
        return f"IMPL:{task}"

    async def fake_notes(self, changes_summary: str, context=None):
        return f"NOTES:{changes_summary}"

    wf = DevTeamWorkflow("wf-123")
    # Patch methods on instances to avoid importing real agent modules
    monkeypatch.setattr(wf.orchestrator, "plan", fake_plan, raising=True)
    monkeypatch.setattr(wf.developer, "implement", fake_impl, raising=True)
    monkeypatch.setattr(wf.release, "draft_notes", fake_notes, raising=True)
    plan = await wf.start(session_id="sess-1", goal="Implement feature X")
    assert plan.startswith("PLAN:")

    dev_result = await wf.handoff_to_developer(task="Add unit tests")
    assert dev_result.startswith("IMPL:")

    rel_result = await wf.handoff_to_release(changes_summary="Added tests")
    assert rel_result.startswith("NOTES:")

    status = await wf.status()
    assert status["workflow_id"] == "wf-123"
    assert status["state"]["current_agent"] == "release"

