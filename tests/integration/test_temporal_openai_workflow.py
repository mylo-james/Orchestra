import pytest

from src.services.workflow_service import WorkflowService


@pytest.mark.asyncio
async def test_workflow_service_end_to_end_smoke(monkeypatch):
    async def fake_plan(self, goal: str, context=None):
        return "PLAN:smoke"

    async def fake_impl(self, task: str, context=None):
        return "IMPL:smoke"

    async def fake_notes(self, changes_summary: str, context=None):
        return "NOTES:smoke"

    service = WorkflowService()
    plan = await service.start("wf-smoke", session_id="sess-smoke", goal="Do work")
    assert plan == "PLAN:smoke"

    # Patch instances inside workflow after creation
    wf = service.get_or_create("wf-smoke")
    monkeypatch.setattr(wf.orchestrator, "plan", fake_plan, raising=True)
    monkeypatch.setattr(wf.developer, "implement", fake_impl, raising=True)
    monkeypatch.setattr(wf.release, "draft_notes", fake_notes, raising=True)

    dev = await service.developer_step("wf-smoke", task="Implement step")
    assert dev == "IMPL:smoke"

    rel = await service.release_step("wf-smoke", summary="Summarize changes")
    assert rel == "NOTES:smoke"

    status = await service.get_status("wf-smoke")
    assert status["workflow_id"] == "wf-smoke"

