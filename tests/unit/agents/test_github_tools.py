"""Tests for GitHub tools using OpenAI Agents SDK FunctionTool implementations."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from agents import FunctionTool

from src.system.base import AgentContext
from src.system.tools import (
    create_github_pr_tool,
    get_github_tools,
    list_repositories_tool,
)


@pytest.fixture
def mock_context():
    """Create a mock AgentContext for testing."""
    return AgentContext(agent_name="test_agent", correlation_id="test_123")


@pytest.mark.asyncio
async def test_create_github_pr_tool_creation():
    """Test GitHub PR tool creation returns proper FunctionTool."""
    tool = create_github_pr_tool()

    assert isinstance(tool, FunctionTool)
    assert tool.name == "create_github_pr"
    assert "GitHub pull request" in tool.description
    assert tool.on_invoke_tool is not None
    assert tool.params_json_schema is not None


@pytest.mark.asyncio
async def test_create_github_pr_success(mock_context):
    """Test successful GitHub PR creation."""
    tool = create_github_pr_tool()

    mock_result = {"html_url": "https://github.com/test/repo/pull/123", "number": 123}

    with patch("src.agents.tools.github.ExternalServiceClient") as mock_client_cls:
        with patch("src.agents.tools.github.get_settings") as mock_settings:
            mock_settings.return_value.github.token = "test_token"

            mock_client = AsyncMock()
            mock_client.create_github_pr = AsyncMock(return_value=mock_result)
            mock_client_cls.return_value = mock_client

            # Create mock tool context
            mock_tool_context = Mock()
            mock_tool_context.run_id = "test-run-123"

            params_json = '{"context": {"correlation_id": "test_123"}, "title": "Test PR", "body": "Test description", "branch": "feature/test", "base": "main"}'

            result = await tool.on_invoke_tool(mock_tool_context, params_json)

            assert "Successfully created PR" in result
            assert "https://github.com/test/repo/pull/123" in result
            mock_client.create_github_pr.assert_called_once_with(
                title="Test PR", description="Test description", branch="feature/test"
            )


@pytest.mark.asyncio
async def test_create_github_pr_validation_errors(mock_context):
    """Test GitHub PR creation with validation errors."""
    tool = create_github_pr_tool()

    # Create mock tool context
    mock_tool_context = Mock()
    mock_tool_context.run_id = "test-run-123"

    # Test empty title
    with pytest.raises(ValueError, match="Title must be 1-200 characters"):
        params_json = '{"context": {"correlation_id": "test_123"}, "title": "", "body": "Test", "branch": "test"}'
        await tool.on_invoke_tool(mock_tool_context, params_json)

    # Test title too long
    with pytest.raises(ValueError, match="Title must be 1-200 characters"):
        long_title = "x" * 201
        params_json = f'{{"context": {{"correlation_id": "test_123"}}, "title": "{long_title}", "body": "Test", "branch": "test"}}'
        await tool.on_invoke_tool(mock_tool_context, params_json)

    # Test unsafe characters in title
    with pytest.raises(ValueError, match="Title contains unsafe characters"):
        params_json = '{"context": {"correlation_id": "test_123"}, "title": "Test <script>alert()</script>", "body": "Test", "branch": "test"}'
        await tool.on_invoke_tool(mock_tool_context, params_json)

    # Test body too long
    with pytest.raises(ValueError, match="Body must not exceed 10000 characters"):
        long_body = "x" * 10001
        params_json = f'{{"context": {{"correlation_id": "test_123"}}, "title": "Test PR", "body": "{long_body}", "branch": "test"}}'
        await tool.on_invoke_tool(mock_tool_context, params_json)


@pytest.mark.asyncio
async def test_create_github_pr_no_token(mock_context):
    """Test GitHub PR creation without token configured."""
    tool = create_github_pr_tool()

    with patch("src.agents.tools.github.get_settings") as mock_settings:
        mock_settings.return_value.github.token = None

        # Create mock tool context
        mock_tool_context = Mock()
        mock_tool_context.run_id = "test-run-123"

        with pytest.raises(RuntimeError, match="GitHub token not configured"):
            params_json = '{"context": {"correlation_id": "test_123"}, "title": "Test PR", "body": "Test", "branch": "test"}'
            await tool.on_invoke_tool(mock_tool_context, params_json)


@pytest.mark.asyncio
async def test_list_repositories_tool_creation():
    """Test repositories listing tool creation."""
    tool = list_repositories_tool()

    assert isinstance(tool, FunctionTool)
    assert tool.name == "list_github_repositories"
    assert "repositories" in tool.description
    assert tool.on_invoke_tool is not None


@pytest.mark.asyncio
async def test_list_repositories_validation(mock_context):
    """Test repository listing validation."""
    tool = list_repositories_tool()

    # Create mock tool context
    mock_tool_context = Mock()
    mock_tool_context.run_id = "test-run-123"

    # Test invalid limit - too low
    with pytest.raises(ValueError, match="Limit must be between 1 and 100"):
        params_json = '{"context": {"correlation_id": "test_123"}, "limit": 0}'
        await tool.on_invoke_tool(mock_tool_context, params_json)

    # Test invalid limit - too high
    with pytest.raises(ValueError, match="Limit must be between 1 and 100"):
        params_json = '{"context": {"correlation_id": "test_123"}, "limit": 101}'
        await tool.on_invoke_tool(mock_tool_context, params_json)

    # Test org name too long
    with pytest.raises(ValueError, match="Organization name too long"):
        long_org = "x" * 40
        params_json = (
            f'{{"context": {{"correlation_id": "test_123"}}, "org": "{long_org}"}}'
        )
        await tool.on_invoke_tool(mock_tool_context, params_json)


@pytest.mark.asyncio
async def test_list_repositories_success(mock_context):
    """Test successful repository listing."""
    tool = list_repositories_tool()

    with patch("src.agents.tools.github.get_settings") as mock_settings:
        mock_settings.return_value.github.token = "test_token"

        # Create mock tool context
        mock_tool_context = Mock()
        mock_tool_context.run_id = "test-run-123"

        params_json = (
            '{"context": {"correlation_id": "test_123"}, "org": "testorg", "limit": 5}'
        )
        result = await tool.on_invoke_tool(mock_tool_context, params_json)

        # Currently returns a placeholder message
        assert "repositories" in result.lower()
        assert "0" in result  # Current implementation returns 0 count


def test_get_github_tools():
    """Test get_github_tools returns list of tools."""
    tools = get_github_tools()

    assert isinstance(tools, list)
    assert len(tools) == 2
    assert all(isinstance(tool, FunctionTool) for tool in tools)

    tool_names = [tool.name for tool in tools]
    assert "create_github_pr" in tool_names
    assert "list_github_repositories" in tool_names


@pytest.mark.asyncio
async def test_github_tools_with_logging(mock_context):
    """Test GitHub tools include proper logging."""
    tool = create_github_pr_tool()

    with patch("src.agents.tools.github.ExternalServiceClient") as mock_client_cls:
        with patch("src.agents.tools.github.get_settings") as mock_settings:
            with patch("src.agents.tools.github.logger") as mock_logger:
                mock_settings.return_value.github.token = "test_token"

                mock_client = AsyncMock()
                mock_client.create_github_pr = AsyncMock(
                    return_value={"html_url": "test"}
                )
                mock_client_cls.return_value = mock_client

                # Create mock tool context
                mock_tool_context = Mock()
                mock_tool_context.run_id = "test-run-123"

                params_json = '{"context": {"correlation_id": "test_123"}, "title": "Test PR", "body": "Test", "branch": "test"}'
                await tool.on_invoke_tool(mock_tool_context, params_json)

                # Verify logging calls
                mock_logger.info.assert_called()
                log_calls = [call[0][0] for call in mock_logger.info.call_args_list]
                assert "github_pr_create_start" in log_calls
                assert "github_pr_create_success" in log_calls


@pytest.mark.asyncio
async def test_github_pr_api_failure(mock_context):
    """Test GitHub PR creation handles API failures."""
    tool = create_github_pr_tool()

    with patch("src.agents.tools.github.ExternalServiceClient") as mock_client_cls:
        with patch("src.agents.tools.github.get_settings") as mock_settings:
            with patch("src.agents.tools.github.logger") as mock_logger:
                mock_settings.return_value.github.token = "test_token"

                mock_client = AsyncMock()
                mock_client.create_github_pr = AsyncMock(
                    side_effect=Exception("API Error")
                )
                mock_client_cls.return_value = mock_client

                # Create mock tool context
                mock_tool_context = Mock()
                mock_tool_context.run_id = "test-run-123"

                with pytest.raises(RuntimeError, match="Failed to create GitHub PR"):
                    params_json = '{"context": {"correlation_id": "test_123"}, "title": "Test PR", "body": "Test", "branch": "test"}'
                    await tool.on_invoke_tool(mock_tool_context, params_json)

                # Verify error logging
                mock_logger.error.assert_called_once()
                error_call = mock_logger.error.call_args[0]
                assert "github_pr_create_failure" in error_call
