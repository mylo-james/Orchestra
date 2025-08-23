import pytest

from src.system.tools import create_github_pr_tool, list_repositories_tool


@pytest.mark.asyncio
async def test_github_create_pr_tool():
    """Test GitHub PR creation tool."""
    # The tool is a FunctionTool instance
    assert create_github_pr_tool is not None
    assert hasattr(create_github_pr_tool, "name")
    assert create_github_pr_tool.name == "create_github_pr"
    assert hasattr(create_github_pr_tool, "description")
    assert hasattr(create_github_pr_tool, "func")


@pytest.mark.asyncio
async def test_github_list_repos_tool():
    """Test GitHub repository listing tool."""
    # The tool is a FunctionTool instance
    assert list_repositories_tool is not None
    assert hasattr(list_repositories_tool, "name")
    assert list_repositories_tool.name == "list_repositories"
    assert hasattr(list_repositories_tool, "description")
    assert hasattr(list_repositories_tool, "func")
