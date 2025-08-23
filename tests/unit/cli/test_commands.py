"""Tests for src/cli/commands.py following 1:1 source-to-test mapping."""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

# Import the actual modules to ensure they're loaded for coverage
from src.cli.commands import (
    agent_cmd,
    config_cmd,
    dev_cmd,
    health_check,
    list_agents,
    list_personas,
    list_workflows,
    reload_personas,
    show_config,
    start_agent,
    start_workflow,
    test_circuit_breaker,
    test_security,
    validate_config,
    validate_persona,
    workflow_cmd,
)

runner = CliRunner()


class TestAgentCommands:
    """Test agent-related commands."""

    def test_start_agent(self):
        """Test start_agent command."""
        with patch("src.cli.commands.get_registry") as mock_registry:
            mock_agent = MagicMock()
            mock_registry.return_value.create.return_value = mock_agent

            # Call the function directly
            start_agent("test-persona")

            mock_registry.return_value.create.assert_called_once_with("test-persona")

    def test_list_agents(self):
        """Test list_agents command."""
        with patch("src.cli.commands.get_registry") as mock_registry:
            # Return list of persona IDs (strings), not dicts
            mock_registry.return_value.list_personas.return_value = ["test1", "test2"]
            # Mock get_persona_spec to return None (will skip the row)
            mock_registry.return_value.get_persona_spec.return_value = None

            # Should run without error
            list_agents()

            mock_registry.return_value.list_personas.assert_called_once()

    def test_list_personas(self):
        """Test list_personas command."""
        with patch("src.cli.commands.PersonaLoader") as mock_loader:
            mock_instance = MagicMock()
            mock_loader.return_value = mock_instance
            mock_instance.list_personas.return_value = ["persona1", "persona2"]
            # Mock load_persona to return None (will skip the row)
            mock_instance.load_persona.return_value = None

            # Should run without error
            list_personas()

            mock_instance.list_personas.assert_called_once()

    def test_validate_persona(self):
        """Test validate_persona command."""
        with patch("src.cli.commands.PersonaLoader") as mock_loader:
            mock_instance = MagicMock()
            mock_loader.return_value = mock_instance
            # Mock load_persona to return a valid spec
            mock_spec = MagicMock()
            mock_spec.validate.return_value = []  # No errors
            mock_instance.load_persona.return_value = mock_spec

            # Should run without error
            validate_persona("test-persona")

            mock_instance.load_persona.assert_called_once_with("test-persona")

    def test_reload_personas(self):
        """Test reload_personas command."""
        with patch("src.cli.commands.PersonaLoader") as mock_loader:
            with patch("src.cli.commands.get_registry") as mock_registry:
                mock_loader_instance = MagicMock()
                mock_loader.return_value = mock_loader_instance
                mock_loader_instance.list_personas.return_value = ["p1", "p2"]

                # Should run without error
                reload_personas()

                # Verify the loader was used
                mock_loader_instance.reload_all.assert_called_once()


class TestWorkflowCommands:
    """Test workflow-related commands."""

    def test_start_workflow(self):
        """Test start_workflow command."""
        # Should run without error
        start_workflow("test-workflow")

    def test_list_workflows(self):
        """Test list_workflows command."""
        # Should run without error
        list_workflows()


class TestConfigCommands:
    """Test config-related commands."""

    def test_show_config(self):
        """Test show_config command."""
        # Should run without error
        show_config()

    def test_validate_config(self):
        """Test validate_config command."""
        # Should run without error
        validate_config()


class TestDevCommands:
    """Test dev-related commands."""

    def test_test_security(self):
        """Test test_security command."""
        with patch("src.cli.commands.AIAgentMonitor") as mock_monitor:
            with patch("src.cli.commands.AIAgentValidator") as mock_validator:
                # Mock validator to accept agent_id parameter
                mock_validator_instance = MagicMock()
                mock_validator.return_value = mock_validator_instance

                # Should run without error
                test_security()

    def test_test_circuit_breaker(self):
        """Test test_circuit_breaker command."""
        with patch("src.cli.commands.CircuitBreaker") as mock_cb:
            # Mock CircuitBreaker with correct parameters
            mock_cb_instance = MagicMock()
            mock_cb.return_value = mock_cb_instance

            # Should run without error
            test_circuit_breaker()

    def test_health_check(self):
        """Test health_check command."""
        with patch("src.cli.commands.get_registry") as mock_registry:
            with patch("src.cli.commands.PersonaLoader") as mock_loader:
                # Mock registry to have list_personas method
                mock_registry.return_value.list_personas.return_value = []
                # Mock loader
                mock_loader.return_value.list_personas.return_value = []

                # Should run without error
                health_check()


class TestCommandGroups:
    """Test command group creation."""

    def test_agent_cmd_group(self):
        """Test agent command group."""
        assert agent_cmd is not None
        # Test via CLI runner
        result = runner.invoke(agent_cmd, ["--help"])
        assert result.exit_code == 0

    def test_workflow_cmd_group(self):
        """Test workflow command group."""
        assert workflow_cmd is not None
        result = runner.invoke(workflow_cmd, ["--help"])
        assert result.exit_code == 0

    def test_config_cmd_group(self):
        """Test config command group."""
        assert config_cmd is not None
        result = runner.invoke(config_cmd, ["--help"])
        assert result.exit_code == 0

    def test_dev_cmd_group(self):
        """Test dev command group."""
        assert dev_cmd is not None
        result = runner.invoke(dev_cmd, ["--help"])
        assert result.exit_code == 0
