"""Development team workflow orchestrating agent handoffs using Temporal."""

import uuid
from dataclasses import dataclass, field
from datetime import timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from temporalio import workflow
from temporalio.common import RetryPolicy

from orchestra.temporal.activities.base import (
    create_github_pr_activity,
    execute_agent_activity,
    validate_context_activity,
)
from orchestra.temporal.activities.security import (
    audit_log_activity,
    validate_security_activity,
)
from orchestra.utils.logging import get_logger

logger = get_logger(__name__)


class AgentType(str, Enum):
    """Available agent types in the system."""

    ORCHESTRATOR = "orchestrator"
    DEVELOPER = "developer"
    RELEASE = "release"


class TaskState(str, Enum):
    """Current state of the task being processed."""

    PLANNING = "planning"
    IMPLEMENTING = "implementing"
    REVIEWING = "reviewing"
    RELEASING = "releasing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class SecurityContext:
    """Security context for agent operations."""

    user_id: str
    permissions: List[str]
    auth_token: Optional[str] = None
    validated: bool = False


@dataclass
class RetryContext:
    """Context for retry operations with exponential backoff."""

    attempt_count: int = 0
    last_attempt_time: Optional[float] = None
    backoff_seconds: float = 1.0
    max_attempts: int = 3


@dataclass
class WorkflowContext:
    """Context passed between agents during handoffs."""

    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    current_agent: Optional[AgentType] = None
    handoff_reason: Optional[str] = None
    confidence_scores: Dict[str, float] = field(default_factory=dict)
    working_memory: Dict[str, Any] = field(default_factory=dict)
    task_state: TaskState = TaskState.PLANNING
    security_context: Optional[SecurityContext] = None
    schema_version: str = "1.0.0"
    retry_metadata: RetryContext = field(default_factory=RetryContext)
    resource_constraints: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowInput:
    """Input parameters for the development team workflow."""

    request: str
    user_id: str
    project_context: Dict[str, Any] = field(default_factory=dict)
    priority: str = "normal"
    security_context: Optional[SecurityContext] = None


@dataclass
class WorkflowOutput:
    """Output from the development team workflow."""

    success: bool
    session_id: str
    correlation_id: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    agents_involved: List[AgentType] = field(default_factory=list)
    total_duration_seconds: float = 0.0


@workflow.defn
class DevTeamWorkflow:
    """
    Temporal workflow orchestrating multi-agent development team operations.

    This workflow manages the handoff between different specialized agents
    (Orchestrator, Developer, Release) to complete development tasks.
    """

    def __init__(self) -> None:
        """Initialize workflow state."""
        self.context: Optional[WorkflowContext] = None
        self.start_time: float = 0.0
        self.agents_involved: List[AgentType] = []

    @workflow.run
    async def run(self, input_data: WorkflowInput) -> WorkflowOutput:
        """
        Execute the development team workflow.

        Args:
            input_data: Workflow input containing request and context

        Returns:
            WorkflowOutput with results or error information
        """
        self.start_time = self._get_current_timestamp()

        # Initialize workflow context
        self.context = WorkflowContext(
            security_context=input_data.security_context
            or SecurityContext(
                user_id=input_data.user_id,
                permissions=["read", "write"],
            ),
            working_memory={
                "request": input_data.request,
                "project_context": input_data.project_context,
                "priority": input_data.priority,
            },
        )

        try:
            # Step 1: Security validation
            await self._validate_security()

            # Step 2: Orchestrator planning phase
            await self._execute_orchestrator_planning()

            # Step 3: Developer implementation phase
            if self.context.task_state == TaskState.IMPLEMENTING:
                await self._execute_developer_implementation()

            # Step 4: Release phase if needed
            if self.context.task_state == TaskState.RELEASING:
                await self._execute_release_operations()

            # Step 5: Final audit logging
            await self._audit_workflow_completion()

            # Calculate duration
            duration = self._get_current_timestamp() - self.start_time

            return WorkflowOutput(
                success=True,
                session_id=self.context.session_id,
                correlation_id=self.context.correlation_id,
                result=self.context.working_memory.get("final_result"),
                agents_involved=self.agents_involved,
                total_duration_seconds=duration,
            )

        except Exception as e:
            # Log error and return failure
            await self._audit_workflow_error(str(e))

            duration = self._get_current_timestamp() - self.start_time

            return WorkflowOutput(
                success=False,
                session_id=self.context.session_id if self.context else "",
                correlation_id=self.context.correlation_id if self.context else "",
                error=str(e),
                agents_involved=self.agents_involved,
                total_duration_seconds=duration,
            )

    async def _validate_security(self) -> None:
        """Validate security context before proceeding."""
        if self.context is None:
            raise ValueError("Workflow context is None")

        validation_result = await workflow.execute_activity(
            validate_security_activity,
            self.context.security_context,
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=RetryPolicy(
                maximum_attempts=2,
                initial_interval=timedelta(seconds=1),
            ),
        )  # type: ignore[misc]

        if not validation_result["valid"]:
            raise ValueError(
                f"Security validation failed: {validation_result.get('reason')}"
            )

        if self.context.security_context is not None:
            self.context.security_context.validated = True

    async def _execute_orchestrator_planning(self) -> None:
        """Execute orchestrator agent for planning phase."""
        if self.context is None:
            raise ValueError("Workflow context is None")

        self.context.current_agent = AgentType.ORCHESTRATOR
        self.context.task_state = TaskState.PLANNING
        self.agents_involved.append(AgentType.ORCHESTRATOR)

        # Validate context before agent execution
        await workflow.execute_activity(
            validate_context_activity,
            self.context,
            start_to_close_timeout=timedelta(seconds=10),
        )  # type: ignore[misc]

        # Execute orchestrator agent with 30s timeout for planning
        result = await workflow.execute_activity(
            execute_agent_activity,
            {
                "agent_type": AgentType.ORCHESTRATOR,
                "context": self.context,
                "operation": "plan",
            },
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(
                maximum_attempts=3,
                initial_interval=timedelta(seconds=2),
                backoff_coefficient=2.0,
            ),
        )  # type: ignore[misc]

        # Update context with orchestrator results
        if self.context.conversation_history is not None:
            self.context.conversation_history.append(result["conversation"])
        if self.context.confidence_scores is not None:
            self.context.confidence_scores["orchestrator"] = result.get(
                "confidence", 0.8
            )
        if self.context.working_memory is not None:
            self.context.working_memory.update(result.get("memory_updates", {}))

        # Determine next state based on orchestrator decision
        next_action = result.get("next_action", "implement")
        if next_action == "implement":
            self.context.task_state = TaskState.IMPLEMENTING
            self.context.handoff_reason = "Planning complete, ready for implementation"
        elif next_action == "release":
            self.context.task_state = TaskState.RELEASING
            self.context.handoff_reason = "Direct to release operations"
        else:
            self.context.task_state = TaskState.COMPLETED

    async def _execute_developer_implementation(self) -> None:
        """Execute developer agent for implementation phase."""
        if self.context is None:
            raise ValueError("Workflow context is None")

        self.context.current_agent = AgentType.DEVELOPER
        self.context.task_state = TaskState.IMPLEMENTING
        self.agents_involved.append(AgentType.DEVELOPER)

        # Execute developer agent with 120s timeout for code generation
        result = await workflow.execute_activity(
            execute_agent_activity,
            {
                "agent_type": AgentType.DEVELOPER,
                "context": self.context,
                "operation": "implement",
            },
            start_to_close_timeout=timedelta(seconds=120),
            retry_policy=RetryPolicy(
                maximum_attempts=3,
                initial_interval=timedelta(seconds=5),
                backoff_coefficient=2.0,
            ),
        )

        # Update context with developer results
        if self.context.conversation_history is not None:
            self.context.conversation_history.append(result["conversation"])
        if self.context.confidence_scores is not None:
            self.context.confidence_scores["developer"] = result.get("confidence", 0.85)
        if self.context.working_memory is not None:
            self.context.working_memory.update(result.get("memory_updates", {}))

        # Check if release is needed
        if result.get("needs_release", False):
            self.context.task_state = TaskState.RELEASING
            self.context.handoff_reason = "Implementation complete, ready for release"
        else:
            self.context.task_state = TaskState.COMPLETED
            if self.context.working_memory is not None:
                self.context.working_memory["final_result"] = result.get("output")

    async def _execute_release_operations(self) -> None:
        """Execute release agent for deployment operations."""
        if self.context is None:
            raise ValueError("Workflow context is None")

        self.context.current_agent = AgentType.RELEASE
        self.context.task_state = TaskState.RELEASING
        self.agents_involved.append(AgentType.RELEASE)

        # Create GitHub PR if needed
        if self.context.working_memory is not None and self.context.working_memory.get(
            "create_pr", False
        ):
            pr_result = await workflow.execute_activity(
                create_github_pr_activity,
                {
                    "title": self.context.working_memory.get(
                        "pr_title", "Auto-generated PR"
                    ),
                    "body": self.context.working_memory.get("pr_body", ""),
                    "branch": self.context.working_memory.get("branch", "feature/auto"),
                    "context": self.context,
                },
                start_to_close_timeout=timedelta(seconds=60),
                retry_policy=RetryPolicy(
                    maximum_attempts=3,
                    initial_interval=timedelta(seconds=5),
                    backoff_coefficient=2.0,
                ),
            )

            if self.context.working_memory is not None:
                self.context.working_memory["pr_url"] = pr_result.get("url")

        # Execute release agent
        result = await workflow.execute_activity(
            execute_agent_activity,
            {
                "agent_type": AgentType.RELEASE,
                "context": self.context,
                "operation": "release",
            },
            start_to_close_timeout=timedelta(seconds=60),
            retry_policy=RetryPolicy(
                maximum_attempts=2,
                initial_interval=timedelta(seconds=5),
            ),
        )

        # Update context with release results
        if self.context.conversation_history is not None:
            self.context.conversation_history.append(result["conversation"])
        if self.context.confidence_scores is not None:
            self.context.confidence_scores["release"] = result.get("confidence", 0.9)
        if self.context.working_memory is not None:
            self.context.working_memory["final_result"] = result.get("output")
        self.context.task_state = TaskState.COMPLETED

    def _get_current_timestamp(self) -> float:
        """Get current timestamp - testable helper method."""
        try:
            return workflow.now().timestamp()
        except Exception as e:
            # Fallback for testing environments without Temporal
            import time

            logger.debug(f"Using fallback timestamp due to Temporal error: {e}")
            return time.time()

    async def _audit_workflow_completion(self) -> None:
        """Audit log the workflow completion."""
        if self.context is None:
            raise ValueError("Workflow context is None")

        await workflow.execute_activity(
            audit_log_activity,
            {
                "event_type": "workflow_completed",
                "session_id": self.context.session_id,
                "correlation_id": self.context.correlation_id,
                "agents_involved": self.agents_involved,
                "duration_seconds": self._get_current_timestamp() - self.start_time,
                "success": True,
            },
            start_to_close_timeout=timedelta(seconds=5),
        )

    async def _audit_workflow_error(self, error: str) -> None:
        """Audit log workflow errors."""
        await workflow.execute_activity(
            audit_log_activity,
            {
                "event_type": "workflow_error",
                "session_id": self.context.session_id if self.context else "",
                "correlation_id": self.context.correlation_id if self.context else "",
                "error": error,
                "agents_involved": self.agents_involved,
                "duration_seconds": self._get_current_timestamp() - self.start_time,
                "success": False,
            },
            start_to_close_timeout=timedelta(seconds=5),
        )

    @workflow.signal
    async def update_priority(self, new_priority: str) -> None:
        """
        Signal to update workflow priority during execution.

        Args:
            new_priority: New priority level
        """
        if self.context:
            self.context.working_memory["priority"] = new_priority
            await self._audit_workflow_signal(
                "priority_updated", {"new_priority": new_priority}
            )

    @workflow.query
    def get_status(self) -> Dict[str, Any]:
        """
        Query current workflow status.

        Returns:
            Current workflow state and progress
        """
        if not self.context:
            return {"status": "not_started"}

        return {
            "session_id": self.context.session_id,
            "correlation_id": self.context.correlation_id,
            "current_agent": self.context.current_agent,
            "task_state": self.context.task_state,
            "agents_involved": self.agents_involved,
            "confidence_scores": self.context.confidence_scores,
            "duration_seconds": self._get_current_timestamp() - self.start_time,
        }

    async def _audit_workflow_signal(
        self, signal_type: str, data: Dict[str, Any]
    ) -> None:
        """Audit log workflow signals."""
        if self.context is None:
            raise ValueError("Workflow context is None")

        await workflow.execute_activity(
            audit_log_activity,
            {
                "event_type": f"workflow_signal_{signal_type}",
                "session_id": self.context.session_id,
                "correlation_id": self.context.correlation_id,
                "signal_data": data,
            },
            start_to_close_timeout=timedelta(seconds=5),
        )
