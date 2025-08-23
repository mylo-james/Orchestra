"""Simple tests for CLI commands."""

from src.cli.commands import (
    agent_cmd,
    config_cmd,
    dev_cmd,
    workflow_cmd,
)


class TestCommandGroupBasics:
    """Test basic command group functionality."""

    def test_command_groups_exist(self):
        """Test that command groups exist."""
        assert agent_cmd is not None
        assert config_cmd is not None
        assert dev_cmd is not None
        assert workflow_cmd is not None

    def test_command_groups_are_typer_instances(self):
        """Test that command groups are Typer instances."""
        import typer

        assert isinstance(agent_cmd, typer.Typer)
        assert isinstance(config_cmd, typer.Typer)
        assert isinstance(dev_cmd, typer.Typer)
        assert isinstance(workflow_cmd, typer.Typer)
