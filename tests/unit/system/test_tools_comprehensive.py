"""
Comprehensive tests for src/system/tools.py to achieve 90%+ coverage.

Tests GitHub tools implementation with OpenAI Agents SDK integration.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.system.tools import (
    CreatePRInput,
    FunctionTool,
    ToolContext,
    ToolDefinition,
    create_github_pr_tool,
    create_pr_tool,
    get_github_tools,
    list_repositories_tool,
)


class TestCreatePRInput:
    """Test CreatePRInput model."""

    def test_create_pr_input_valid(self):
        """Test creating valid PR input."""
        pr_input = CreatePRInput(
            title="Test PR",
            body="This is a test PR",
            branch="feature-branch",
            base="main",
        )

        assert pr_input.title == "Test PR"
        assert pr_input.body == "This is a test PR"
        assert pr_input.branch == "feature-branch"
        assert pr_input.base == "main"

    def test_create_pr_input_defaults(self):
        """Test PR input with defaults."""
        pr_input = CreatePRInput(title="Test PR", branch="feature-branch")

        assert pr_input.title == "Test PR"
        assert pr_input.body == ""  # Default empty body
        assert pr_input.branch == "feature-branch"
        assert pr_input.base == "main"  # Default base branch

    def test_create_pr_input_validation(self):
        """Test PR input validation."""
        # Title too long
        with pytest.raises(ValueError):
            CreatePRInput(title="x" * 201, branch="feature")  # Exceeds max length

        # Branch name too long
        with pytest.raises(ValueError):
            CreatePRInput(title="Test", branch="x" * 121)  # Exceeds max length


class TestToolDefinitionAndContext:
    """Test ToolDefinition and ToolContext classes."""

    def test_tool_definition_exists(self):
        """Test that ToolDefinition class exists."""
        td = ToolDefinition()
        assert td is not None

    def test_tool_context_exists(self):
        """Test that ToolContext class exists."""
        tc = ToolContext()
        assert tc is not None

    def test_function_tool_exists(self):
        """Test that FunctionTool class exists."""
        tool = FunctionTool(
            name="test", description="Test tool", func=lambda x: x, parameters={}
        )
        assert tool.name == "test"
        assert tool.description == "Test tool"
        assert tool.func is not None
        assert tool.parameters == {}


class TestCreateGitHubPRTool:
    """Test create_github_pr_tool function."""

    @patch("src.system.tools.ExternalServiceClient")
    @patch("src.system.tools.get_settings")
    @patch("src.system.tools.logger")
    def test_create_github_pr_tool_creation(
        self, mock_logger, mock_get_settings, mock_client_class
    ):
        """Test creating GitHub PR tool."""
        # Create the tool
        tool = create_github_pr_tool()

        assert isinstance(tool, FunctionTool)
        assert tool.name == "create_github_pr"
        assert "GitHub pull request" in tool.description
        assert tool.func is not None

    @pytest.mark.asyncio
    @patch("src.system.tools.ExternalServiceClient")
    @patch("src.system.tools.get_settings")
    async def test_create_pr_success(self, mock_get_settings, mock_client_class):
        """Test successful PR creation."""
        # Setup mocks
        mock_settings = MagicMock()
        mock_settings.github.token = "test-token"
        mock_settings.github.owner = "test-owner"
        mock_settings.github.repo = "test-repo"
        mock_get_settings.return_value = mock_settings

        mock_client = AsyncMock()
        mock_client.create_github_pr.return_value = {
            "html_url": "https://github.com/test-owner/test-repo/pull/123",
            "number": 123,
            "state": "open",
        }
        mock_client_class.return_value = mock_client

        # Create tool and execute
        tool = create_github_pr_tool()

        # Create mock context
        mock_context = MagicMock()
        mock_context.tool_call_id = "test-call-123"

        # Prepare parameters
        params = {
            "title": "Test PR",
            "body": "Test description",
            "branch": "feature-branch",
            "base": "main",
            "context": {"correlation_id": "test-correlation"},
        }
        params_json = json.dumps(params)

        # Execute the function
        result = await tool.func(mock_context, params_json)

        # Verify result (function returns string, not dict)
        assert "Successfully created PR" in result
        assert "pull/123" in result

        # Verify client was called correctly
        mock_client.create_github_pr.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.system.tools.ExternalServiceClient")
    @patch("src.system.tools.get_settings")
    async def test_create_pr_invalid_json(self, mock_get_settings, mock_client_class):
        """Test PR creation with invalid JSON."""
        tool = create_github_pr_tool()

        mock_context = MagicMock()
        mock_context.tool_call_id = "test-call-123"

        # Invalid JSON
        with pytest.raises(ValueError, match="Invalid parameters"):
            await tool.func(mock_context, "invalid json {")

    @pytest.mark.asyncio
    @patch("src.system.tools.ExternalServiceClient")
    @patch("src.system.tools.get_settings")
    async def test_create_pr_api_failure(self, mock_get_settings, mock_client_class):
        """Test PR creation when API fails."""
        # Setup mocks
        mock_settings = MagicMock()
        mock_settings.github.token = "test-token"
        mock_settings.github.owner = "test-owner"
        mock_settings.github.repo = "test-repo"
        mock_get_settings.return_value = mock_settings

        mock_client = AsyncMock()
        mock_client.create_github_pr.side_effect = Exception("API error")
        mock_client_class.return_value = mock_client

        tool = create_github_pr_tool()

        mock_context = MagicMock()
        mock_context.tool_call_id = "test-call-123"

        params = {"title": "Test PR", "branch": "feature-branch"}
        params_json = json.dumps(params)

        # Should raise RuntimeError
        with pytest.raises(RuntimeError, match="Failed to create GitHub PR"):
            await tool.func(mock_context, params_json)


class TestListRepositoriesTool:
    """Test list_repositories_tool function."""

    @patch("src.system.tools.ExternalServiceClient")
    @patch("src.system.tools.get_settings")
    def test_list_repositories_tool_creation(
        self, mock_get_settings, mock_client_class
    ):
        """Test creating list repositories tool."""
        tool = list_repositories_tool()

        assert isinstance(tool, FunctionTool)
        assert tool.name == "list_github_repositories"
        assert "List GitHub repositories" in tool.description
        assert tool.func is not None

    @pytest.mark.asyncio
    @patch("src.system.tools.ExternalServiceClient")
    @patch("src.system.tools.get_settings")
    async def test_list_repositories_execution(
        self, mock_get_settings, mock_client_class
    ):
        """Test list repositories tool execution."""
        # Setup mocks
        mock_settings = MagicMock()
        mock_settings.github.token = "test-token"
        mock_get_settings.return_value = mock_settings

        mock_client = AsyncMock()
        # list_repositories_tool returns a string, not a dictionary
        mock_client_class.return_value = mock_client

        tool = list_repositories_tool()

        mock_context = MagicMock()
        mock_context.tool_call_id = "test-list-123"

        params = {"org": "test-org"}
        params_json = json.dumps(params)

        result = await tool.func(mock_context, params_json)

        # The function returns a string, not a dictionary
        assert "Found 0 repositories" in result or "Found" in result


class TestCreatePRToolDefinition:
    """Test create_pr_tool function."""

    def test_create_pr_tool_definition(self):
        """Test creating PR tool definition."""
        tool_def = create_pr_tool()

        assert isinstance(tool_def, ToolDefinition)
        # Tool definition is a placeholder class
        assert tool_def is not None


class TestGetGitHubTools:
    """Test get_github_tools function."""

    @patch("src.system.tools.get_settings")
    def test_get_github_tools(self, mock_get_settings):
        """Test creating all GitHub tools."""
        mock_settings = MagicMock()
        mock_settings.github.token = "test-token"
        mock_get_settings.return_value = mock_settings

        tools = get_github_tools()

        assert isinstance(tools, list)
        assert len(tools) >= 2  # At least PR and list repos tools

        # Check tool names
        tool_names = [tool.name for tool in tools]
        assert "create_github_pr" in tool_names
        assert "list_github_repositories" in tool_names

    @patch("src.system.tools.get_settings")
    def test_get_github_tools_no_token(self, mock_get_settings):
        """Test creating GitHub tools without token."""
        mock_settings = MagicMock()
        mock_settings.github.token = None
        mock_get_settings.return_value = mock_settings

        tools = get_github_tools()

        # Should still create tools but PR tool might be limited
        assert isinstance(tools, list)
        assert len(tools) > 0


class TestIntegration:
    """Integration tests for tools module."""

    @pytest.mark.asyncio
    @patch("src.system.tools.ExternalServiceClient")
    @patch("src.system.tools.get_settings")
    async def test_full_pr_workflow(self, mock_get_settings, mock_client_class):
        """Test complete PR creation workflow."""
        # Setup
        mock_settings = MagicMock()
        mock_settings.github.token = "test-token"
        mock_settings.github.owner = "test-owner"
        mock_settings.github.repo = "test-repo"
        mock_get_settings.return_value = mock_settings

        mock_client = AsyncMock()
        mock_client.create_github_pr.return_value = {
            "html_url": "https://github.com/test-owner/test-repo/pull/456",
            "number": 456,
            "state": "open",
        }
        mock_client_class.return_value = mock_client

        # Create tools
        tools = get_github_tools()
        pr_tool = next(t for t in tools if t.name == "create_github_pr")

        # Execute PR creation
        mock_context = MagicMock()
        mock_context.tool_call_id = "workflow-123"

        params = {
            "title": "Feature: Add new functionality",
            "body": "This PR adds new features:\n- Feature A\n- Feature B",
            "branch": "feature/new-functionality",
            "base": "develop",
        }

        result = await pr_tool.func(mock_context, json.dumps(params))

        # The function returns a string, not a dictionary
        assert "Successfully created PR" in result
        assert "pull/456" in result

    def test_all_tools_have_descriptions(self):
        """Test that all tools have proper descriptions."""
        tools = get_github_tools()

        for tool in tools:
            assert tool.name
            assert tool.description
            assert len(tool.description) > 10  # Meaningful description
            assert tool.func is not None
