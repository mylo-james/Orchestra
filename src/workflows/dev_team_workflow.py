"""Temporal-inspired workflow scaffolding for agent handoffs.

This module defines the DevTeamWorkflow protocol with async methods that mimic
Temporal workflow patterns without introducing the temporalio SDK dependency yet.
It focuses on orchestrating OpenAI-based agents and durable state transitions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

try:  # Lazy import with safe fallback to allow tests without external deps
    from src.agents.developer.agent import DeveloperAgent
    from src.agents.orchestrator.agent import OrchestratorAgent
    from src.agents.release.agent import ReleaseAgent
    from src.agents.base.secure_agent import AgentContext
except Exception:  # pragma: no cover - fallback stubs for test environments
    class _Stub:
        agent_name = "stub"

        async def plan(self, goal: str, context=None) -> str:
            return f"PLAN:{goal}"

        async def implement(self, task: str, context=None) -> str:
            return f"IMPL:{task}"

        async def draft_notes(self, changes_summary: str, context=None) -> str:
            return f"NOTES:{changes_summary}"

    OrchestratorAgent = _Stub  # type: ignore
    DeveloperAgent = _Stub  # type: ignore
    ReleaseAgent = _Stub  # type: ignore

    @dataclass
    class AgentContext:  # type: ignore
        correlation_id: Optional[str] = None
        agent_name: Optional[str] = None
        session_data: Dict[str, Any] = field(default_factory=dict)
from src.utils.logging import get_logger, set_workflow_context


logger = get_logger(__name__)


@dataclass
class AgentContextState:
    """Minimal agent context preserved across handoffs.

    Mirrors the story's `agent_context` schema at a basic level so we can evolve
    to full Temporal workflow state later without breaking compatibility.
    """

    session_id: str
    correlation_id: str
    current_agent: str
    handoff_reason: str | None = None
    working_memory: Dict[str, Any] = field(default_factory=dict)
    schema_version: str = "1.0"


class DevTeamWorkflow:
    """Workflow coordinating Orchestrator → Developer → Release agent handoffs.

    This is a lightweight scaffold: it does not require Temporal to run tests now
    but follows the async orchestration shape so it can be ported to Temporal easily.
    """

    def __init__(self, workflow_id: str):
        self.workflow_id = workflow_id
        set_workflow_context(workflow_id)
        self.state: Optional[AgentContextState] = None
        self.orchestrator = OrchestratorAgent()
        self.developer = DeveloperAgent()
        self.release = ReleaseAgent()

    async def start(self, session_id: str, goal: str) -> str:
        """Start the workflow: orchestrator plans work from a goal."""
        logger.info("workflow_start", workflow_id=self.workflow_id, session_id=session_id)
        self.state = AgentContextState(
            session_id=session_id,
            correlation_id=f"wf_{self.workflow_id}",
            current_agent="orchestrator",
        )

        context = AgentContext(agent_name="orchestrator", correlation_id=self.state.correlation_id)
        # Support monkeypatched coroutine functions that may not be bound
        plan_attr = getattr(self.orchestrator, "plan")
        try:
            plan = await plan_attr(goal=goal, context=context)
        except TypeError as e:
            # If unbound function without self
            if "missing 1 required positional argument" in str(e) or "positional argument: 'self'" in str(e):
                plan = await plan_attr(self.orchestrator, goal=goal, context=context)
            else:
                raise
        self.state.working_memory["plan"] = plan
        return plan

    async def handoff_to_developer(self, task: str) -> str:
        """Handoff to Developer agent for implementation of a task."""
        if not self.state:
            raise RuntimeError("Workflow must be started before handoffs")
        self.state.current_agent = "developer"
        self.state.handoff_reason = "implement_task"
        context = AgentContext(agent_name="developer", correlation_id=self.state.correlation_id)
        impl_attr = getattr(self.developer, "implement")
        try:
            result = await impl_attr(task=task, context=context)
        except TypeError as e:
            if "missing 1 required positional argument" in str(e) or "positional argument: 'self'" in str(e):
                result = await impl_attr(self.developer, task=task, context=context)
            else:
                raise
        self.state.working_memory.setdefault("developer_results", []).append(result)
        return result

    async def handoff_to_release(self, changes_summary: str) -> str:
        """Handoff to Release agent for creating release notes/PR summary."""
        if not self.state:
            raise RuntimeError("Workflow must be started before handoffs")
        self.state.current_agent = "release"
        self.state.handoff_reason = "prepare_release"
        context = AgentContext(agent_name="release", correlation_id=self.state.correlation_id)
        notes_attr = getattr(self.release, "draft_notes")
        try:
            result = await notes_attr(changes_summary=changes_summary, context=context)
        except TypeError as e:
            if "missing 1 required positional argument" in str(e) or "positional argument: 'self'" in str(e):
                result = await notes_attr(self.release, changes_summary=changes_summary, context=context)
            else:
                raise
        self.state.working_memory.setdefault("release_notes", []).append(result)
        return result

    async def status(self) -> Dict[str, Any]:
        """Return a summary of current workflow state for queries."""
        return {
            "workflow_id": self.workflow_id,
            "state": self.state.__dict__ if self.state else None,
        }

