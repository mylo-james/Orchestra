"""Tests for workflow activities."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.workflows.activities import (
    execute_agent_activity,
    validate_context_activity,
    create_github_pr_activity,
    _execute_with_universal_agent,
    _determine_next_action,
)


@pytest.mark.asyncio
async def test_execute_agent_activity_success():
    """Test successful agent activity execution."""
    with patch("src.workflows.activities.create_agent") as mock_create:
        # Mock agent
        mock_agent = MagicMock()
        mock_agent.ask = AsyncMock(return_value="Task completed successfully")
        mock_create.return_value = mock_agent
        
        # Execute activity
        result = await execute_agent_activity({
            "agent_type": "dev",
            "prompt": "Implement feature X",
            "context": {"project": "test"}
        })
        
        # Verify
        assert "response" in result
        assert result["success"] is True
        assert "error" not in result
        mock_create.assert_called_once_with("dev")


@pytest.mark.asyncio
async def test_execute_agent_activity_with_error():
    """Test agent task execution with error handling."""
    with patch("src.workflows.activities.create_agent") as mock_create:
        # Mock agent that raises error
        mock_agent = MagicMock()
        mock_agent.ask = AsyncMock(side_effect=Exception("Agent error"))
        mock_create.return_value = mock_agent
        
        # Execute task - should handle error
        result = await execute_agent_task({
            "agent_type": "dev",
            "task": "Failing task",
            "context": {}
        })
        
        # Should return error result
        assert result["confidence"] == 0.0
        assert "error" in result["next_action"]


@pytest.mark.asyncio
async def test_validate_security_pass():
    """Test security validation passing."""
    with patch("src.workflows.activities.AIAgentValidator") as mock_validator:
        # Mock validator
        mock_instance = MagicMock()
        mock_instance.validate_request = AsyncMock(return_value=True)
        mock_instance.validate_response = AsyncMock(return_value=True)
        mock_validator.return_value = mock_instance
        
        # Validate
        result = await validate_security({
            "agent_id": "test_agent",
            "request": "test request",
            "response": "test response"
        })
        
        # Should pass
        assert result["passed"] is True
        assert result["risk_score"] < 0.5


@pytest.mark.asyncio
async def test_validate_security_fail():
    """Test security validation failing."""
    with patch("src.workflows.activities.AIAgentValidator") as mock_validator:
        # Mock validator that fails
        mock_instance = MagicMock()
        mock_instance.validate_request = AsyncMock(return_value=False)
        mock_validator.return_value = mock_instance
        
        # Validate
        result = await validate_security({
            "agent_id": "test_agent",
            "request": "malicious request",
            "response": "test response"
        })
        
        # Should fail
        assert result["passed"] is False
        assert len(result["violations"]) > 0


@pytest.mark.asyncio
async def test_perform_code_review():
    """Test code review activity."""
    with patch("src.workflows.activities.create_agent") as mock_create:
        # Mock review agent
        mock_agent = MagicMock()
        mock_agent.ask = AsyncMock(return_value="Code looks good with minor suggestions")
        mock_create.return_value = mock_agent
        
        # Perform review
        result = await perform_code_review({
            "code": "def hello(): return 'world'",
            "language": "python",
            "context": {"standards": "PEP8"}
        })
        
        # Verify
        assert "review" in result
        assert "suggestions" in result
        assert result["approved"] is not None


@pytest.mark.asyncio
async def test_run_tests_success():
    """Test running tests successfully."""
    with patch("src.workflows.activities.subprocess.run") as mock_run:
        # Mock successful test run
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="All tests passed",
            stderr=""
        )
        
        # Run tests
        result = await run_tests({
            "test_command": "pytest",
            "test_path": "tests/",
            "coverage_threshold": 70
        })
        
        # Should pass
        assert result["passed"] is True
        assert result["coverage"] >= 0


@pytest.mark.asyncio
async def test_run_tests_failure():
    """Test running tests with failures."""
    with patch("src.workflows.activities.subprocess.run") as mock_run:
        # Mock failed test run
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="1 test failed",
            stderr="Error in test"
        )
        
        # Run tests
        result = await run_tests({
            "test_command": "pytest",
            "test_path": "tests/",
            "coverage_threshold": 70
        })
        
        # Should fail
        assert result["passed"] is False
        assert len(result["failures"]) > 0


@pytest.mark.asyncio
async def test_generate_documentation():
    """Test documentation generation."""
    with patch("src.workflows.activities.create_agent") as mock_create:
        # Mock doc agent
        mock_agent = MagicMock()
        mock_agent.ask = AsyncMock(return_value="Generated comprehensive documentation")
        mock_create.return_value = mock_agent
        
        # Generate docs
        result = await generate_documentation({
            "code_path": "src/",
            "doc_type": "API",
            "format": "markdown"
        })
        
        # Verify
        assert "documentation" in result
        assert result["format"] == "markdown"
        assert len(result["sections"]) > 0


@pytest.mark.asyncio
async def test_execute_agent_task_with_tools():
    """Test agent task execution with tools."""
    with patch("src.workflows.activities.create_agent") as mock_create:
        # Mock agent with tools
        mock_agent = MagicMock()
        mock_agent.ask = AsyncMock(return_value="Task completed with tools")
        mock_agent.tools = ["github_pr", "code_search"]
        mock_create.return_value = mock_agent
        
        # Execute task
        result = await execute_agent_task({
            "agent_type": "dev",
            "task": "Create PR",
            "context": {"repo": "test/repo"},
            "use_tools": True
        })
        
        # Verify
        assert result["confidence"] > 0
        assert "tools_used" in result.get("metadata", {})


@pytest.mark.asyncio
async def test_validate_security_with_monitor():
    """Test security validation with monitoring."""
    with patch("src.workflows.activities.AIAgentValidator") as mock_validator:
        with patch("src.workflows.activities.AIAgentMonitor") as mock_monitor:
            # Mock validator and monitor
            mock_val_instance = MagicMock()
            mock_val_instance.validate_request = AsyncMock(return_value=True)
            mock_validator.return_value = mock_val_instance
            
            mock_mon_instance = MagicMock()
            mock_mon_instance.log_activity = AsyncMock()
            mock_monitor.return_value = mock_mon_instance
            
            # Validate with monitoring
            result = await validate_security({
                "agent_id": "test_agent",
                "request": "test",
                "response": "test",
                "enable_monitoring": True
            })
            
            # Should log activity
            assert result["passed"] is True
            mock_mon_instance.log_activity.assert_called()