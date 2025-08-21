"""Workflow service to manage DevTeamWorkflow lifecycle in-process.

This provides a stable interface that can later be swapped with Temporal client
without changing callers.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict

from src.workflows.dev_team_workflow import DevTeamWorkflow
from src.workflows.security_activities import validate_state_integrity, sanitize_agent_context


class WorkflowService:
    """Facade for managing workflow execution and state interactions."""

    def __init__(self):
        self._workflows: Dict[str, DevTeamWorkflow] = {}

    def get_or_create(self, workflow_id: str) -> DevTeamWorkflow:
        if workflow_id not in self._workflows:
            self._workflows[workflow_id] = DevTeamWorkflow(workflow_id)
        return self._workflows[workflow_id]

    async def start(self, workflow_id: str, session_id: str, goal: str) -> str:
        wf = self.get_or_create(workflow_id)
        plan = await wf.start(session_id=session_id, goal=goal)
        validate_state_integrity({
            "session_id": session_id,
            "correlation_id": f"wf_{workflow_id}",
            "current_agent": "orchestrator",
        })
        return plan

    async def developer_step(self, workflow_id: str, task: str) -> str:
        wf = self.get_or_create(workflow_id)
        return await wf.handoff_to_developer(task)

    async def release_step(self, workflow_id: str, summary: str) -> str:
        wf = self.get_or_create(workflow_id)
        return await wf.handoff_to_release(summary)

    async def get_status(self, workflow_id: str) -> Dict[str, Any]:
        wf = self.get_or_create(workflow_id)
        return await wf.status()

