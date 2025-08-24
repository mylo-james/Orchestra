"""Coverage tests for CLI commands."""

from src.cli.commands import agent_cmd, config_cmd, dev_cmd, workflow_cmd


class TestCommandGroupCoverage:
    """Test command group coverage."""

    def test_all_command_groups_imported(self):
        """Test that all command groups are imported."""
        assert agent_cmd is not None
        assert config_cmd is not None
        assert dev_cmd is not None
        assert workflow_cmd is not None

    def test_command_groups_have_commands(self):
        """Test that command groups have commands registered."""
        # Agent commands
        assert len(agent_cmd.registered_commands) > 0

        # Config commands
        assert len(config_cmd.registered_commands) > 0

        # Dev commands
        assert len(dev_cmd.registered_commands) > 0

        # Workflow commands
        assert len(workflow_cmd.registered_commands) > 0
