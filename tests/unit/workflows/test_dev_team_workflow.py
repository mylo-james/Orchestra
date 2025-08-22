"""Unit tests for DevTeamWorkflow."""

import asyncio
from unittest.mock import AsyncMock

import pytest
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from src.workflows.dev_team_workflow import (
    AgentType,
    DevTeamWorkflow,
    SecurityContext,
    TaskState,
    WorkflowInput,
    WorkflowOutput,
)


@pytest.fixture
async def workflow_env():
    """Create a test workflow environment."""
    async with WorkflowEnvironment() as env:
        yield env


@pytest.fixture
def mock_activities():
    """Create mock activities for testing."""
    mocks = {
        "execute_agent": AsyncMock(
            return_value={
                "conversation": {"role": "test", "content": "Test"},
                "confidence": 0.9,
                "memory_updates": {},
                "next_action": "continue",
            }
        ),
        "validate_context": AsyncMock(return_value={"valid": True, "errors": []}),
        "create_github_pr": AsyncMock(
            return_value={
                "success": True,
                "url": "https://github.com/test/pr/1",
                "pr_number": 1,
            }
        ),
        "validate_security": AsyncMock(
            return_value={
                "valid": True,
                "reason": "Valid",
            }
        ),
        "audit_log": AsyncMock(return_value={"success": True}),
    }
    return mocks


async def test_workflow_successful_execution(workflow_env, mock_activities):
    """Test successful workflow execution."""
    # Register workflow and activities
    async with Worker(
        workflow_env.client,
        task_queue="test-queue",
        workflows=[DevTeamWorkflow],
        activities=[
            mock_activities["execute_agent"],
            mock_activities["validate_context"],
            mock_activities["create_github_pr"],
            mock_activities["validate_security"],
            mock_activities["audit_log"],
        ],
    ):
        # Create workflow input
        workflow_input = WorkflowInput(
            request="Test request",
            user_id="test_user",
            project_context={"project": "test"},
            priority="normal",
        )

        # Execute workflow
        result = await workflow_env.client.execute_workflow(
            DevTeamWorkflow.run,
            workflow_input,
            id="test-workflow-1",
            task_queue="test-queue",
        )

        # Verify result
        assert isinstance(result, WorkflowOutput)
        assert result.success is True
        assert result.session_id is not None
        assert result.correlation_id is not None


async def test_workflow_security_validation_failure(workflow_env):
    """Test workflow handling of security validation failure."""

    # Mock security validation to fail
    async def failing_security_validation(context):
        return {"valid": False, "reason": "Invalid user"}

    async with Worker(
        workflow_env.client,
        task_queue="test-queue",
        workflows=[DevTeamWorkflow],
        activities=[
            failing_security_validation,
            AsyncMock(),  # Other activities won't be called
        ],
    ):
        workflow_input = WorkflowInput(
            request="Test request",
            user_id="invalid_user",
        )

        # Execute workflow - should fail
        with pytest.raises(Exception) as exc_info:
            await workflow_env.client.execute_workflow(
                DevTeamWorkflow.run,
                workflow_input,
                id="test-workflow-2",
                task_queue="test-queue",
            )

        assert "Security validation failed" in str(exc_info.value)


async def test_workflow_agent_handoff():
    """Test agent handoff during workflow execution."""
    # Track which agents were called
    agents_called = []

    async def track_agent_execution(params):
        agents_called.append(params["agent_type"])
        return {
            "conversation": {"role": params["agent_type"], "content": "Test"},
            "confidence": 0.9,
            "memory_updates": {},
            "next_action": (
                "implement" if params["agent_type"] == "orchestrator" else "complete"
            ),
        }

    async with WorkflowEnvironment() as env:
        async with Worker(
            env.client,
            task_queue="test-queue",
            workflows=[DevTeamWorkflow],
            activities=[
                track_agent_execution,
                AsyncMock(return_value={"valid": True}),  # validate_context
                AsyncMock(return_value={"valid": True}),  # validate_security
                AsyncMock(return_value={"success": True}),  # audit_log
            ],
        ):
            workflow_input = WorkflowInput(
                request="Test request",
                user_id="test_user",
            )

            result = await env.client.execute_workflow(
                DevTeamWorkflow.run,
                workflow_input,
                id="test-workflow-3",
                task_queue="test-queue",
            )

            # Verify agent handoff occurred
            assert AgentType.ORCHESTRATOR in agents_called
            assert len(agents_called) >= 2  # At least orchestrator and one other


async def test_workflow_query_status():
    """Test workflow status query."""
    async with WorkflowEnvironment() as env:
        # Start a long-running workflow
        async def slow_agent_execution(params):
            await asyncio.sleep(1)  # Simulate slow execution
            return {
                "conversation": {"role": "test", "content": "Test"},
                "confidence": 0.9,
                "memory_updates": {},
                "next_action": "complete",
            }

        async with Worker(
            env.client,
            task_queue="test-queue",
            workflows=[DevTeamWorkflow],
            activities=[
                slow_agent_execution,
                AsyncMock(return_value={"valid": True}),
                AsyncMock(return_value={"success": True}),
            ],
        ):
            workflow_input = WorkflowInput(
                request="Test request",
                user_id="test_user",
            )

            # Start workflow
            handle = await env.client.start_workflow(
                DevTeamWorkflow.run,
                workflow_input,
                id="test-workflow-4",
                task_queue="test-queue",
            )

            # Query status while running
            await asyncio.sleep(0.1)  # Let workflow start
            status = await handle.query(DevTeamWorkflow.get_status)

            assert status["session_id"] is not None
            assert status["correlation_id"] is not None
            assert "task_state" in status


async def test_workflow_signal_priority_update():
    """Test workflow signal to update priority."""
    async with WorkflowEnvironment() as env:
        async with Worker(
            env.client,
            task_queue="test-queue",
            workflows=[DevTeamWorkflow],
            activities=[
                AsyncMock(
                    return_value={
                        "conversation": {"role": "test", "content": "Test"},
                        "confidence": 0.9,
                        "memory_updates": {},
                        "next_action": "complete",
                    }
                ),
                AsyncMock(return_value={"valid": True}),
                AsyncMock(return_value={"success": True}),
            ],
        ):
            workflow_input = WorkflowInput(
                request="Test request",
                user_id="test_user",
                priority="normal",
            )

            # Start workflow
            handle = await env.client.start_workflow(
                DevTeamWorkflow.run,
                workflow_input,
                id="test-workflow-5",
                task_queue="test-queue",
            )

            # Send signal to update priority
            await handle.signal(DevTeamWorkflow.update_priority, "high")

            # Complete workflow
            result = await handle.result()
            assert result.success is True


def test_workflow_context_initialization():
    """Test WorkflowContext initialization."""
    from src.workflows.dev_team_workflow import WorkflowContext

    context = WorkflowContext()

    assert context.session_id is not None
    assert context.correlation_id is not None
    assert context.task_state == TaskState.PLANNING
    assert len(context.conversation_history) == 0
    assert context.schema_version == "1.0.0"


def test_security_context():
    """Test SecurityContext dataclass."""
    security_context = SecurityContext(
        user_id="test_user",
        permissions=["read", "write"],
        auth_token="test_token",
    )

    assert security_context.user_id == "test_user"
    assert "read" in security_context.permissions
    assert security_context.validated is False


def test_workflow_input_defaults():
    """Test WorkflowInput default values."""
    workflow_input = WorkflowInput(
        request="Test",
        user_id="user",
    )

    assert workflow_input.priority == "normal"
    assert workflow_input.project_context == {}
    assert workflow_input.security_context is None


def test_workflow_output_structure():
    """Test WorkflowOutput structure."""
    output = WorkflowOutput(
        success=True,
        session_id="test-session",
        correlation_id="test-correlation",
        result={"test": "data"},
        agents_involved=[AgentType.ORCHESTRATOR, AgentType.DEVELOPER],
        total_duration_seconds=10.5,
    )

    assert output.success is True
    assert output.session_id == "test-session"
    assert len(output.agents_involved) == 2
    assert output.error is None
