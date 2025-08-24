"""Tests for workflow activities based on PRD requirements."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from orchestra.system.agent import UniversalAgent
from orchestra.workflows.activities import (
    _determine_next_action,
    _execute_with_universal_agent,
    create_github_pr_activity,
    execute_agent_activity,
    validate_context_activity,
)


class TestExecuteAgentActivity:
    """Test main agent execution activity."""

    @pytest.mark.asyncio
    @patch("orchestra.workflows.activities.get_registry")
    async def test_execute_agent_activity_with_universal_agent(self, mock_get_registry):
        """Test agent execution with UniversalAgent."""
        # Mock registry and agent
        mock_registry = Mock()
        mock_agent = Mock(spec=UniversalAgent)
        mock_agent.persona_id = "orchestrator"
        mock_agent.execute_command = AsyncMock(
            return_value={"success": True, "result": {"plan": "test plan"}}
        )

        mock_registry.create.return_value = mock_agent
        mock_get_registry.return_value = mock_registry

        params = {
            "agent_type": "orchestrator",
            "operation": "plan",
            "context": {
                "session_id": "test-session",
                "correlation_id": "test-correlation",
                "working_memory": {"request": "Create a test feature"},
            },
        }

        result = await execute_agent_activity(params)

        assert result["conversation"]["role"] == "orchestrator"
        assert result["confidence"] == 0.85
        assert result["next_action"] == "implement"
        assert "plan" in result["conversation"]["content"]

        # Verify agent was created and executed
        mock_registry.create.assert_called_once_with("orchestrator")
        mock_agent.execute_command.assert_called_once_with(
            "plan",
            {
                "context": params["context"],
                "working_memory": params["context"]["working_memory"],
                "request": "Create a test feature",
            },
        )

    @pytest.mark.asyncio
    @patch("orchestra.workflows.activities.get_registry")
    async def test_execute_agent_activity_with_non_universal_agent(
        self, mock_get_registry
    ):
        """Test agent execution with non-UniversalAgent raises error."""
        # Mock registry and non-universal agent
        mock_registry = Mock()
        mock_agent = Mock()  # Not a UniversalAgent
        mock_registry.create.return_value = mock_agent
        mock_get_registry.return_value = mock_registry

        params = {
            "agent_type": "orchestrator",
            "operation": "plan",
            "context": {
                "session_id": "test-session",
                "correlation_id": "test-correlation",
                "working_memory": {"request": "Create a test feature"},
            },
        }

        with pytest.raises(ValueError, match="Agent must be a UniversalAgent instance"):
            await execute_agent_activity(params)

    @pytest.mark.asyncio
    @patch("orchestra.workflows.activities.get_registry")
    async def test_execute_agent_activity_persona_mapping(self, mock_get_registry):
        """Test persona mapping for different agent types."""
        mock_registry = Mock()
        mock_agent = Mock(spec=UniversalAgent)
        mock_agent.persona_id = "dev"
        mock_agent.execute_command = AsyncMock(
            return_value={"success": True, "result": {"test": "result"}}
        )
        mock_registry.create.return_value = mock_agent
        mock_get_registry.return_value = mock_registry

        # Test developer -> dev mapping
        params = {
            "agent_type": "developer",
            "operation": "implement",
            "context": {
                "session_id": "test",
                "correlation_id": "test",
                "working_memory": {},
            },
        }

        await execute_agent_activity(params)
        mock_registry.create.assert_called_with("dev")

        # Test direct mapping for unknown types
        mock_registry.reset_mock()
        mock_agent.persona_id = "custom_agent"
        params["agent_type"] = "custom_agent"
        await execute_agent_activity(params)
        mock_registry.create.assert_called_with("custom_agent")

    @pytest.mark.asyncio
    @patch("orchestra.workflows.activities.get_registry")
    async def test_execute_agent_activity_unknown_operation(self, mock_get_registry):
        """Test agent execution with unknown operation uses operation as command."""
        mock_registry = Mock()
        mock_agent = Mock(spec=UniversalAgent)
        mock_agent.persona_id = "orchestrator"
        mock_agent.execute_command = AsyncMock(
            return_value={"success": True, "result": {"custom": "result"}}
        )
        mock_registry.create.return_value = mock_agent
        mock_get_registry.return_value = mock_registry

        params = {
            "agent_type": "orchestrator",
            "operation": "unknown_operation",
            "context": {
                "session_id": "test",
                "correlation_id": "test",
                "working_memory": {},
            },
        }

        result = await execute_agent_activity(params)

        assert result["conversation"]["role"] == "orchestrator"
        assert result["confidence"] == 0.85

        # Should use operation directly as command
        mock_agent.execute_command.assert_called_once_with(
            "unknown_operation",
            {"context": params["context"], "working_memory": {}, "request": ""},
        )

    @pytest.mark.asyncio
    @patch("orchestra.workflows.activities.get_registry")
    async def test_execute_agent_activity_exception_handling(self, mock_get_registry):
        """Test agent execution with exception handling."""
        mock_registry = Mock()
        mock_registry.create.side_effect = Exception("Registry error")
        mock_get_registry.return_value = mock_registry

        params = {
            "agent_type": "orchestrator",
            "operation": "plan",
            "context": {"session_id": "test", "correlation_id": "test"},
        }

        with pytest.raises(Exception, match="Registry error"):
            await execute_agent_activity(params)


class TestUniversalAgentExecution:
    """Test UniversalAgent execution functionality."""

    @pytest.mark.asyncio
    async def test_execute_with_universal_agent_success(self):
        """Test successful UniversalAgent command execution."""
        mock_agent = Mock(spec=UniversalAgent)
        mock_agent.persona_id = "dev"
        mock_agent.execute_command = AsyncMock(
            return_value={
                "success": True,
                "result": {"code": "def test(): pass", "tests": ["test_test.py"]},
            }
        )

        context = {
            "working_memory": {"request": "Create test function"},
            "session_id": "test-session",
        }

        result = await _execute_with_universal_agent(mock_agent, "implement", context)

        assert result["conversation"]["role"] == "dev"
        assert result["confidence"] == 0.85
        assert result["next_action"] == "release"
        assert "Executed implement-story" in result["conversation"]["content"]

        # Verify command execution
        mock_agent.execute_command.assert_called_once_with(
            "implement-story",
            {
                "context": context,
                "working_memory": context["working_memory"],
                "request": "Create test function",
            },
        )

    @pytest.mark.asyncio
    async def test_execute_with_universal_agent_command_failure(self):
        """Test UniversalAgent command execution failure."""
        mock_agent = Mock(spec=UniversalAgent)
        mock_agent.persona_id = "orchestrator"
        mock_agent.execute_command = AsyncMock(
            return_value={"success": False, "error": "Command execution failed"}
        )

        context = {"working_memory": {}}

        with pytest.raises(Exception, match="Command execution failed"):
            await _execute_with_universal_agent(mock_agent, "plan", context)

    @pytest.mark.asyncio
    async def test_execute_with_universal_agent_unknown_operation(self):
        """Test UniversalAgent with unknown operation."""
        mock_agent = Mock(spec=UniversalAgent)
        mock_agent.persona_id = "orchestrator"
        mock_agent.execute_command = AsyncMock(
            return_value={"success": True, "result": {}}
        )

        context = {"working_memory": {}}

        # Should use operation directly as command
        result = await _execute_with_universal_agent(
            mock_agent, "custom_command", context
        )

        assert result["conversation"]["role"] == "orchestrator"
        mock_agent.execute_command.assert_called_once_with(
            "custom_command", {"context": context, "working_memory": {}, "request": ""}
        )


class TestNextActionDetermination:
    """Test next action determination logic."""

    def test_determine_next_action_orchestrator_plan(self):
        """Test next action for orchestrator planning."""
        next_action = _determine_next_action("orchestrator", "plan")
        assert next_action == "implement"

    def test_determine_next_action_dev_implement(self):
        """Test next action for developer implementation."""
        next_action = _determine_next_action("dev", "implement")
        assert next_action == "release"

    def test_determine_next_action_release(self):
        """Test next action for release agent."""
        next_action = _determine_next_action("release", "any_operation")
        assert next_action == "complete"

    def test_determine_next_action_default(self):
        """Test default next action."""
        next_action = _determine_next_action("unknown", "unknown")
        assert next_action == "continue"


class TestValidateContextActivity:
    """Test context validation activity."""

    @pytest.mark.asyncio
    async def test_validate_context_activity_valid(self):
        """Test context validation with valid context."""
        context = {
            "session_id": "test-session-123",
            "correlation_id": "test-correlation-456",
            "security_context": {"user_id": "test-user"},
            "schema_version": "1.0",
            "task_state": "planning",
        }

        result = await validate_context_activity(context)

        assert result["valid"] is True
        assert result["errors"] == []

    @pytest.mark.asyncio
    async def test_validate_context_activity_missing_session_id(self):
        """Test context validation with missing session_id."""
        context = {
            "correlation_id": "test-correlation-456",
            "security_context": {"user_id": "test-user"},
            "schema_version": "1.0",
        }

        result = await validate_context_activity(context)

        assert result["valid"] is False
        assert "Missing session_id" in result["errors"]

    @pytest.mark.asyncio
    async def test_validate_context_activity_missing_correlation_id(self):
        """Test context validation with missing correlation_id."""
        context = {
            "session_id": "test-session-123",
            "security_context": {"user_id": "test-user"},
            "schema_version": "1.0",
        }

        result = await validate_context_activity(context)

        assert result["valid"] is False
        assert "Missing correlation_id" in result["errors"]

    @pytest.mark.asyncio
    async def test_validate_context_activity_missing_security_context(self):
        """Test context validation with missing security_context."""
        context = {
            "session_id": "test-session-123",
            "correlation_id": "test-correlation-456",
            "schema_version": "1.0",
        }

        result = await validate_context_activity(context)

        assert result["valid"] is False
        assert "Missing security_context" in result["errors"]

    @pytest.mark.asyncio
    async def test_validate_context_activity_invalid_schema_version(self):
        """Test context validation with invalid schema version."""
        context = {
            "session_id": "test-session-123",
            "correlation_id": "test-correlation-456",
            "security_context": {"user_id": "test-user"},
            "schema_version": "2.0",
        }

        result = await validate_context_activity(context)

        assert result["valid"] is False
        assert "Unsupported schema version: 2.0" in result["errors"]

    @pytest.mark.asyncio
    async def test_validate_context_activity_invalid_task_state(self):
        """Test context validation with invalid task state."""
        context = {
            "session_id": "test-session-123",
            "correlation_id": "test-correlation-456",
            "security_context": {"user_id": "test-user"},
            "schema_version": "1.0",
            "task_state": "invalid_state",
        }

        result = await validate_context_activity(context)

        assert result["valid"] is False
        assert "Invalid task_state: invalid_state" in result["errors"]

    @pytest.mark.asyncio
    async def test_validate_context_activity_multiple_errors(self):
        """Test context validation with multiple errors."""
        context = {"schema_version": "2.0", "task_state": "invalid_state"}

        result = await validate_context_activity(context)

        assert result["valid"] is False
        assert (
            len(result["errors"]) >= 4
        )  # Missing session_id, correlation_id, security_context, plus invalid schema and task_state

    @pytest.mark.asyncio
    async def test_validate_context_activity_valid_task_states(self):
        """Test context validation with all valid task states."""
        base_context = {
            "session_id": "test-session-123",
            "correlation_id": "test-correlation-456",
            "security_context": {"user_id": "test-user"},
            "schema_version": "1.0",
        }

        valid_states = [
            "planning",
            "implementing",
            "reviewing",
            "releasing",
            "completed",
            "failed",
            None,
        ]

        for state in valid_states:
            context = base_context.copy()
            if state is not None:
                context["task_state"] = state

            result = await validate_context_activity(context)
            assert result["valid"] is True, f"Task state '{state}' should be valid"


class TestCreateGitHubPRActivity:
    """Test GitHub PR creation activity."""

    @pytest.mark.asyncio
    async def test_create_github_pr_activity_success(self):
        """Test successful GitHub PR creation."""
        params = {
            "title": "Add new feature",
            "body": "This PR adds a new feature with tests",
            "branch": "feature/new-feature",
            "context": {
                "session_id": "test-session",
                "correlation_id": "test-correlation",
            },
        }

        result = await create_github_pr_activity(params)

        assert result["success"] is True
        assert result["url"].startswith("https://github.com/org/repo/pull/")
        assert result["branch"] == "feature/new-feature"
        assert isinstance(result["pr_number"], int)

    @pytest.mark.asyncio
    async def test_create_github_pr_activity_with_exception(self):
        """Test GitHub PR creation with simulated exception."""
        params = {
            "title": "Test PR",
            "body": "Test body",
            "branch": "test-branch",
            "context": {"session_id": "test"},
        }

        # Patch asyncio.sleep to raise an exception
        with patch(
            "orchestra.workflows.activities.asyncio.sleep",
            side_effect=Exception("GitHub API Error"),
        ):
            with pytest.raises(Exception, match="GitHub API Error"):
                await create_github_pr_activity(params)


class TestWorkflowActivitiesIntegration:
    """Test integration scenarios for workflow activities."""

    @pytest.mark.asyncio
    @patch("orchestra.workflows.activities.get_registry")
    async def test_complete_workflow_sequence(self, mock_get_registry):
        """Test complete workflow sequence: plan -> implement -> release."""
        mock_registry = Mock()
        mock_get_registry.return_value = mock_registry

        # Mock UniversalAgent for each step
        def create_agent(persona_id):
            agent = Mock(spec=UniversalAgent)
            agent.persona_id = persona_id

            if persona_id == "orchestrator":
                agent.execute_command = AsyncMock(
                    return_value={
                        "success": True,
                        "result": {
                            "plan": {"steps": ["analyze", "design", "implement"]}
                        },
                    }
                )
            elif persona_id == "dev":
                agent.execute_command = AsyncMock(
                    return_value={
                        "success": True,
                        "result": {"implementation": {"files_created": ["auth.py"]}},
                    }
                )
            elif persona_id == "release":
                agent.execute_command = AsyncMock(
                    return_value={
                        "success": True,
                        "result": {"release_info": {"version": "1.0.0"}},
                    }
                )

            return agent

        mock_registry.create.side_effect = create_agent

        base_context = {
            "session_id": "workflow-session",
            "correlation_id": "workflow-correlation",
            "security_context": {"user_id": "test-user"},
            "working_memory": {"request": "Create user authentication system"},
        }

        # Step 1: Planning
        plan_params = {
            "agent_type": "orchestrator",
            "operation": "plan",
            "context": base_context,
        }

        plan_result = await execute_agent_activity(plan_params)
        assert plan_result["next_action"] == "implement"
        assert plan_result["conversation"]["role"] == "orchestrator"

        # Step 2: Implementation
        impl_params = {
            "agent_type": "developer",
            "operation": "implement",
            "context": base_context,
        }

        impl_result = await execute_agent_activity(impl_params)
        assert impl_result["next_action"] == "release"
        assert impl_result["conversation"]["role"] == "dev"

        # Step 3: Release
        release_params = {
            "agent_type": "release",
            "operation": "release",
            "context": base_context,
        }

        release_result = await execute_agent_activity(release_params)
        assert release_result["next_action"] == "complete"
        assert release_result["conversation"]["role"] == "release"

    @pytest.mark.asyncio
    async def test_performance_requirements(self):
        """Test that activities complete within performance requirements."""
        import time

        # Test context validation performance
        context = {
            "session_id": "perf-test",
            "correlation_id": "perf-correlation",
            "security_context": {"user_id": "test"},
            "schema_version": "1.0",
        }

        start_time = time.time()
        result = await validate_context_activity(context)
        end_time = time.time()

        assert result["valid"] is True
        assert end_time - start_time < 0.1  # Should be very fast

        # Test PR creation performance
        pr_params = {
            "title": "Performance test PR",
            "body": "Test body",
            "branch": "perf-test",
            "context": {"session_id": "perf-test"},
        }

        start_time = time.time()
        pr_result = await create_github_pr_activity(pr_params)
        end_time = time.time()

        assert pr_result["success"] is True
        assert end_time - start_time < 1.0  # Should complete within 1 second
