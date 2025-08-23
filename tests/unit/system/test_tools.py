"""Tests for system tools module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from src.system.tools import (
    FunctionTool,
    create_github_pr_tool,
    list_repositories_tool
)


class TestFunctionTool:
    """Test FunctionTool functionality."""

    def test_initialization(self):
        """Test FunctionTool initialization."""
        def test_function(param: str) -> str:
            return f"Hello {param}"
        
        tool = FunctionTool(
            name="test_tool",
            description="A test tool",
            func=test_function,
            parameters={"param": {"type": "string", "description": "Test parameter"}}
        )
        
        assert tool.name == "test_tool"
        assert tool.description == "A test tool"
        assert tool.func == test_function
        assert tool.parameters == {"param": {"type": "string", "description": "Test parameter"}}

    def test_basic_functionality(self):
        """Test basic FunctionTool functionality."""
        def test_function(param: str) -> str:
            return f"Hello {param}"
        
        tool = FunctionTool(
            name="test_tool",
            description="A test tool",
            func=test_function,
            parameters={"param": {"type": "string", "description": "Test parameter"}}
        )
        
        # Test that the tool has the expected attributes
        assert hasattr(tool, 'name')
        assert hasattr(tool, 'description')
        assert hasattr(tool, 'func')
        assert hasattr(tool, 'parameters')


class TestGitHubTools:
    """Test GitHub tool functions."""

    @patch('src.system.tools.ExternalServiceClient')
    def test_create_github_pr_tool(self, mock_client_class):
        """Test GitHub PR creation tool."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        tool = create_github_pr_tool()
        
        assert tool.name == "create_github_pr"
        assert "Create a GitHub pull request" in tool.description
        assert tool.parameters is not None

    @patch('src.system.tools.ExternalServiceClient')
    def test_list_repositories_tool(self, mock_client_class):
        """Test GitHub repository listing tool."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        tool = list_repositories_tool()
        
        assert tool.name == "list_repositories"
        assert "List GitHub repositories" in tool.description
        assert tool.parameters is not None

    @patch('src.system.tools.ExternalServiceClient')
    def test_create_github_pr_tool_creation(self, mock_client_class):
        """Test GitHub PR creation tool creation."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        tool = create_github_pr_tool()
        
        assert tool.name == "create_github_pr"
        assert "Create a GitHub pull request" in tool.description
        assert tool.parameters is not None

    @patch('src.system.tools.ExternalServiceClient')
    def test_list_repositories_tool_creation(self, mock_client_class):
        """Test GitHub repository listing tool creation."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        tool = list_repositories_tool()
        
        assert tool.name == "list_repositories"
        assert "List GitHub repositories" in tool.description
        assert tool.parameters is not None


class TestToolUtilities:
    """Test tool utility functions."""

    def test_function_tool_creation(self):
        """Test FunctionTool creation and basic functionality."""
        def test_function(param: str) -> str:
            return f"Hello {param}"
        
        tool = FunctionTool(
            name="test_tool",
            description="A test tool",
            func=test_function,
            parameters={"param": {"type": "string", "description": "Test parameter"}}
        )
        
        assert tool.name == "test_tool"
        assert tool.description == "A test tool"
        assert tool.func == test_function


class TestToolIntegration:
    """Test tool integration scenarios."""

    @patch('src.system.tools.ExternalServiceClient')
    def test_github_tools_integration(self, mock_client_class):
        """Test integration between GitHub tools."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Test both tools can be created with the same client
        pr_tool = create_github_pr_tool()
        repo_tool = list_repositories_tool()
        
        assert pr_tool.name == "create_github_pr"
        assert repo_tool.name == "list_repositories"
        assert pr_tool.parameters is not None
        assert repo_tool.parameters is not None

    def test_tool_creation_consistency(self):
        """Test that tools are created consistently."""
        pr_tool = create_github_pr_tool()
        repo_tool = list_repositories_tool()
        
        # Check that both tools have the expected structure
        assert hasattr(pr_tool, 'name')
        assert hasattr(pr_tool, 'description')
        assert hasattr(pr_tool, 'func')
        assert hasattr(pr_tool, 'parameters')
        
        assert hasattr(repo_tool, 'name')
        assert hasattr(repo_tool, 'description')
        assert hasattr(repo_tool, 'func')
        assert hasattr(repo_tool, 'parameters')
