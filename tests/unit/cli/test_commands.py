"""
Tests for orchestra/cli/commands.py

Tests command-line interface commands for agent management, persona execution,
and resource processing functionality.
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from orchestra.cli.commands import (
    agent_cmd,
    bmad_cmd,
    config_cmd,
    create_basic_command_group,
    dev_cmd,
    get_persona_loader,
    overlay_cmd,
    workflow_cmd,
)


class TestAgentManagementCommands:
    """Test agent management commands (FR1, FR2)."""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def mock_persona_spec(self):
        """Create a mock persona specification."""
        mock_identity = Mock()
        mock_identity.name = "Test Agent"
        mock_identity.id = "test-agent"
        mock_identity.role = "Testing"
        mock_identity.title = "Test Agent"
        mock_identity.icon = "🧪"
        mock_identity.when_to_use = "For testing purposes"
        mock_identity.style = "Systematic"
        mock_identity.focus = "Quality assurance"

        mock_behavioral = Mock()
        mock_behavioral.core_principles = ["Test everything", "Be thorough"]
        mock_behavioral.work_style = "Systematic"
        mock_behavioral.communication_style = "Clear and concise"
        mock_behavioral.interaction_style = "Professional"

        mock_command_interface = Mock()
        mock_command_interface.commands = {"test": Mock()}

        mock_resource_deps = Mock()
        mock_resource_deps.tools = ["pytest", "coverage"]
        mock_resource_deps.knowledge_sources = ["docs", "tests"]
        mock_resource_deps.required_services = ["test-db", "ci"]
        mock_resource_deps.tasks = []
        mock_resource_deps.templates = []

        mock_persona = Mock()
        mock_persona.identity = mock_identity
        mock_persona.behavioral_contract = mock_behavioral
        mock_persona.command_interface = mock_command_interface
        mock_persona.resource_dependencies = mock_resource_deps

        return mock_persona

    def test_list_agents_success(self, runner):
        """Test list-agents command with successful agent discovery."""
        with patch("orchestra.cli.commands.get_registry") as mock_get_registry:
            mock_registry = Mock()
            mock_agent1 = Mock()
            mock_agent1.name = "Test Agent 1"
            mock_agent1.description = "First test agent"
            mock_agent2 = Mock()
            mock_agent2.name = "Test Agent 2"
            mock_agent2.description = "Second test agent"
            mock_registry.list_agents.return_value = [mock_agent1, mock_agent2]
            mock_get_registry.return_value = mock_registry

            result = runner.invoke(agent_cmd, ["list"])
            assert result.exit_code == 0

    def test_list_agents_no_agents(self, runner):
        """Test list-agents command when no agents are found."""
        with patch("orchestra.cli.commands.get_registry") as mock_get_registry:
            mock_registry = Mock()
            mock_registry.list_agents.return_value = []
            mock_get_registry.return_value = mock_registry

            result = runner.invoke(agent_cmd, ["list"])
            assert result.exit_code == 0

    def test_list_agents_exception(self, runner):
        """Test list-agents command exception handling."""
        with patch("orchestra.cli.commands.get_registry") as mock_get_registry:
            mock_get_registry.side_effect = Exception("Registry error")

            result = runner.invoke(agent_cmd, ["list"])
            assert result.exit_code == 1

    def test_agent_status_success(self, runner):
        """Test agent status command with successful agent lookup."""
        with patch("orchestra.cli.commands.get_registry") as mock_get_registry:
            mock_registry = Mock()
            mock_agent = Mock(name="Test Agent")
            mock_registry.get_agent.return_value = mock_agent
            mock_get_registry.return_value = mock_registry

            result = runner.invoke(agent_cmd, ["status", "test-agent"])
            assert result.exit_code == 0

    def test_agent_status_not_found(self, runner):
        """Test agent status command when agent is not found."""
        with patch("orchestra.cli.commands.get_registry") as mock_get_registry:
            mock_registry = Mock()
            mock_registry.get_agent.return_value = None
            mock_get_registry.return_value = mock_registry

            result = runner.invoke(agent_cmd, ["status", "nonexistent"])
            assert result.exit_code == 1

    def test_agent_status_exception(self, runner):
        """Test agent status command exception handling."""
        with patch("orchestra.cli.commands.get_registry") as mock_get_registry:
            mock_get_registry.side_effect = Exception("Registry error")

            result = runner.invoke(agent_cmd, ["status", "test-agent"])
            assert result.exit_code == 1

    def test_list_personas_with_category_filter(self, runner, mock_persona_spec):
        """Test list-personas command with category filtering."""
        with patch("orchestra.cli.commands.get_persona_loader") as mock_get_loader:
            mock_loader = Mock()
            mock_loader.discover_personas.return_value = {
                "dev": Path("dev.yaml"),
                "pm": Path("pm.yaml"),
                "qa": Path("qa.yaml"),
            }
            mock_loader.load_persona.return_value = mock_persona_spec
            mock_get_loader.return_value = mock_loader

            result = runner.invoke(
                agent_cmd, ["list-personas", "--category", "development"]
            )
            assert result.exit_code == 0

    def test_list_personas_no_category_match(self, runner):
        """Test list-personas command when no personas match category."""
        with patch("orchestra.cli.commands.get_persona_loader") as mock_get_loader:
            mock_loader = Mock()
            mock_loader.discover_personas.return_value = {
                "dev": Path("dev.yaml"),
            }
            mock_get_loader.return_value = mock_loader

            result = runner.invoke(
                agent_cmd, ["list-personas", "--category", "nonexistent"]
            )
            assert result.exit_code == 0

    def test_describe_persona_not_found(self, runner):
        """Test describe-persona command when persona is not found."""
        with patch("orchestra.cli.commands.get_persona_loader") as mock_get_loader:
            mock_loader = Mock()
            mock_loader.load_persona.return_value = None
            mock_loader.discover_personas.return_value = {"dev": Path("dev.yaml")}
            mock_get_loader.return_value = mock_loader

            result = runner.invoke(agent_cmd, ["describe", "nonexistent"])
            assert result.exit_code == 1

    def test_describe_persona_exception(self, runner):
        """Test describe-persona command exception handling."""
        with patch("orchestra.cli.commands.get_persona_loader") as mock_get_loader:
            mock_get_loader.side_effect = Exception("Loader error")

            result = runner.invoke(agent_cmd, ["describe", "test-agent"])
            assert result.exit_code == 1

    def test_activate_persona_exception(self, runner):
        """Test activate-persona command exception handling."""
        with patch("orchestra.cli.commands.get_persona_loader") as mock_get_loader:
            mock_get_loader.side_effect = Exception("Loader error")

            result = runner.invoke(agent_cmd, ["activate", "test-agent"])
            assert result.exit_code == 1

    def test_list_persona_commands_no_active_persona(self, runner):
        """Test list-persona-commands when no persona is active."""
        result = runner.invoke(agent_cmd, ["commands"])
        assert result.exit_code == 0

    def test_list_persona_commands_no_commands(self, runner):
        """Test list-persona-commands when persona has no commands."""
        with patch("orchestra.cli.commands._active_persona") as mock_active:
            mock_active.identity.name = "Test Agent"
            mock_active.command_interface.commands = {}

            result = runner.invoke(agent_cmd, ["commands"])
            assert result.exit_code == 0

    def test_list_persona_commands_with_commands(self, runner):
        """Test list-persona-commands when persona has commands."""
        with patch("orchestra.cli.commands._active_persona") as mock_active:
            mock_active.identity.name = "Test Agent"
            mock_cmd = Mock()
            mock_cmd.description = "Test command"
            mock_cmd.parameters = {"param1": {"type": "string", "required": True}}
            mock_active.command_interface.commands = {"test": mock_cmd}

            result = runner.invoke(agent_cmd, ["commands"])
            assert result.exit_code == 0

    def test_execute_persona_command_no_active_persona(self, runner):
        """Test execute-persona-command when no persona is active."""
        result = runner.invoke(agent_cmd, ["exec", "test-command"])
        assert result.exit_code == 1

    def test_execute_persona_command_not_found(self, runner):
        """Test execute-persona-command when command is not found."""
        with patch("orchestra.cli.commands._active_persona") as mock_active:
            mock_active.identity.name = "Test Agent"
            mock_active.command_interface.commands = {"other": Mock()}

            result = runner.invoke(agent_cmd, ["exec", "nonexistent"])
            assert result.exit_code == 1

    def test_execute_persona_command_success(self, runner):
        """Test execute-persona-command with successful execution."""
        with patch("orchestra.cli.commands._active_persona") as mock_active:
            mock_active.identity.id = "test-agent"
            mock_active.identity.name = "Test Agent"
            mock_active.command_interface.commands = {"test": Mock()}

            result = runner.invoke(agent_cmd, ["exec", "test"])
            assert result.exit_code == 0

    def test_execute_persona_command_exception(self, runner):
        """Test execute-persona-command exception handling."""
        with patch("orchestra.cli.commands._active_persona") as mock_active:
            mock_active.identity.name = "Test Agent"
            mock_active.command_interface.commands = {"test": Mock()}

            with patch("orchestra.cli.commands.logger") as mock_logger:
                mock_logger.info.side_effect = Exception("Logging error")

                result = runner.invoke(agent_cmd, ["exec", "test"])
                assert result.exit_code == 1

    def test_show_command_help_no_active_persona(self, runner):
        """Test show-command-help when no persona is active."""
        result = runner.invoke(agent_cmd, ["help", "test-command"])
        assert result.exit_code == 1

    def test_show_command_help_command_not_found(self, runner):
        """Test show-command-help when command is not found."""
        with patch("orchestra.cli.commands._active_persona") as mock_active:
            mock_active.identity.name = "Test Agent"
            mock_active.command_interface.commands = {"other": Mock()}

            result = runner.invoke(agent_cmd, ["help", "nonexistent"])
            assert result.exit_code == 1

    def test_show_command_help_success(self, runner):
        """Test show-command-help with successful help display."""
        with patch("orchestra.cli.commands._active_persona") as mock_active:
            mock_active.identity.name = "Test Agent"
            mock_cmd = Mock()
            mock_cmd.description = "Test command description"
            mock_cmd.parameters = {"param1": {"type": "string", "required": True}}
            mock_active.command_interface.commands = {"test": mock_cmd}

            result = runner.invoke(agent_cmd, ["help", "test"])
            assert result.exit_code == 0

    def test_show_command_help_exception(self, runner):
        """Test show-command-help exception handling."""
        with patch("orchestra.cli.commands._active_persona") as mock_active:
            mock_active.identity.name = "Test Agent"
            mock_active.command_interface.commands = {"test": Mock()}

            with patch("orchestra.cli.commands.console") as mock_console:
                mock_console.print.side_effect = Exception("Display error")

                result = runner.invoke(agent_cmd, ["help", "test"])
                assert result.exit_code == 1


class TestBasicCommandGroup:
    """Test basic command group creation."""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    def test_create_basic_command_group(self, runner):
        """Test create_basic_command_group function."""

        app = create_basic_command_group("test-group", "Test command group")
        assert app.info.name == "test-group"

        # Test list command
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0

        # Test status command
        result = runner.invoke(app, ["status"])
        assert result.exit_code == 0


class TestPersonaLoader:
    """Test persona loader functionality."""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    def test_get_persona_loader_singleton(self):
        """Test that get_persona_loader returns a singleton."""
        # Reset global state
        import orchestra.cli.commands

        orchestra.cli.commands._persona_loader = None

        loader1 = get_persona_loader()
        loader2 = get_persona_loader()

        assert loader1 is loader2


class TestMissingFunctionality:
    """Test missing functionality to improve coverage."""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def mock_persona_spec(self):
        """Create a mock persona specification."""
        mock_identity = Mock()
        mock_identity.name = "Test Agent"
        mock_identity.id = "test-agent"
        mock_identity.role = "Testing"
        mock_identity.title = "Test Agent"
        mock_identity.icon = "🧪"
        mock_identity.when_to_use = "For testing purposes"
        mock_identity.style = "Systematic"
        mock_identity.focus = "Quality assurance"

        mock_behavioral = Mock()
        mock_behavioral.core_principles = ["Test everything", "Be thorough"]
        mock_behavioral.work_style = "Systematic"
        mock_behavioral.communication_style = "Clear and concise"
        mock_behavioral.interaction_style = "Professional"

        mock_command_interface = Mock()
        mock_command_interface.commands = {"test": Mock()}

        mock_resource_deps = Mock()
        mock_resource_deps.tools = ["pytest", "coverage"]
        mock_resource_deps.knowledge_sources = ["docs", "tests"]
        mock_resource_deps.required_services = ["test-db", "ci"]
        mock_resource_deps.tasks = []
        mock_resource_deps.templates = []

        mock_persona = Mock()
        mock_persona.identity = mock_identity
        mock_persona.behavioral_contract = mock_behavioral
        mock_persona.command_interface = mock_command_interface
        mock_persona.resource_dependencies = mock_resource_deps

        return mock_persona

    def test_list_personas_no_personas_found(self, runner):
        """Test list-personas command when no personas are found."""
        with patch("orchestra.cli.commands.get_persona_loader") as mock_get_loader:
            mock_loader = Mock()
            mock_loader.discover_personas.return_value = {}
            mock_get_loader.return_value = mock_loader

            result = runner.invoke(agent_cmd, ["list-personas"])
            assert result.exit_code == 0

    def test_list_personas_category_filter_no_matches(self, runner):
        """Test list-personas command with category filter that has no matches."""
        with patch("orchestra.cli.commands.get_persona_loader") as mock_get_loader:
            mock_loader = Mock()
            mock_loader.discover_personas.return_value = {
                "dev": Path("dev.yaml"),
            }
            mock_get_loader.return_value = mock_loader

            result = runner.invoke(
                agent_cmd, ["list-personas", "--category", "nonexistent"]
            )
            assert result.exit_code == 0

    def test_describe_persona_success(self, runner, mock_persona_spec):
        """Test describe-persona command with successful persona load."""
        with patch("orchestra.cli.commands.get_persona_loader") as mock_get_loader:
            mock_loader = Mock()
            mock_loader.load_persona.return_value = mock_persona_spec
            mock_get_loader.return_value = mock_loader

            result = runner.invoke(agent_cmd, ["describe", "test-agent"])
            assert result.exit_code == 0

    def test_describe_persona_not_found(self, runner):
        """Test describe-persona command when persona is not found."""
        with patch("orchestra.cli.commands.get_persona_loader") as mock_get_loader:
            mock_loader = Mock()
            mock_loader.load_persona.return_value = None
            mock_loader.discover_personas.return_value = {
                "other-agent": Path("other.yaml")
            }
            mock_get_loader.return_value = mock_loader

            result = runner.invoke(agent_cmd, ["describe", "nonexistent-agent"])
            assert result.exit_code == 1

    def test_activate_persona_success(self, runner, mock_persona_spec):
        """Test activate-persona command with successful activation."""
        with patch("orchestra.cli.commands.get_persona_loader") as mock_get_loader:
            mock_loader = Mock()
            mock_loader.load_persona.return_value = mock_persona_spec
            mock_get_loader.return_value = mock_loader

            result = runner.invoke(agent_cmd, ["activate", "test-agent"])
            assert result.exit_code == 0

    def test_activate_persona_with_team_context(self, runner, mock_persona_spec):
        """Test activate-persona command with team context."""
        with patch("orchestra.cli.commands.get_persona_loader") as mock_get_loader:
            mock_loader = Mock()
            mock_loader.load_persona.return_value = mock_persona_spec
            mock_get_loader.return_value = mock_loader

            result = runner.invoke(
                agent_cmd, ["activate", "test-agent", "--team", "backend"]
            )
            assert result.exit_code == 0

    def test_activate_persona_with_project_context(self, runner, mock_persona_spec):
        """Test activate-persona command with project context."""
        with patch("orchestra.cli.commands.get_persona_loader") as mock_get_loader:
            mock_loader = Mock()
            mock_loader.load_persona.return_value = mock_persona_spec
            mock_get_loader.return_value = mock_loader

            result = runner.invoke(
                agent_cmd, ["activate", "test-agent", "--project", "ecommerce"]
            )
            assert result.exit_code == 0

    def test_activate_persona_not_found(self, runner):
        """Test activate-persona command when persona is not found."""
        with patch("orchestra.cli.commands.get_persona_loader") as mock_get_loader:
            mock_loader = Mock()
            mock_loader.load_persona.return_value = None
            mock_loader.discover_personas.return_value = {
                "other-agent": Path("other.yaml")
            }
            mock_get_loader.return_value = mock_loader

            result = runner.invoke(agent_cmd, ["activate", "nonexistent-agent"])
            assert result.exit_code == 1

    def test_current_persona_no_active(self, runner):
        """Test current-persona command when no persona is active."""
        result = runner.invoke(agent_cmd, ["current"])
        assert result.exit_code == 0

    def test_current_persona_active(self, runner):
        """Test current-persona command when persona is active."""
        with patch("orchestra.cli.commands._active_persona") as mock_active:
            mock_active.identity.name = "Test Agent"
            mock_active.identity.id = "test-agent"
            mock_active.identity.role = "Testing"
            mock_active.identity.title = "Test Agent"
            mock_active.identity.icon = "🧪"
            mock_active.identity.when_to_use = "For testing"
            mock_active.identity.style = "Systematic"
            mock_active.identity.focus = "Quality"

            result = runner.invoke(agent_cmd, ["current"])
            assert result.exit_code == 0

    def test_deactivate_persona_no_active(self, runner):
        """Test deactivate-persona command when no persona is active."""
        result = runner.invoke(agent_cmd, ["deactivate"])
        assert result.exit_code == 0

    def test_deactivate_persona_active(self, runner):
        """Test deactivate-persona command when persona is active."""
        with patch("orchestra.cli.commands._active_persona") as mock_active:
            mock_active.identity.name = "Test Agent"

            result = runner.invoke(agent_cmd, ["deactivate"])
            assert result.exit_code == 0

    def test_search_personas_by_id(self, runner, mock_persona_spec):
        """Test search-personas command with ID match."""
        with patch("orchestra.cli.commands.get_persona_loader") as mock_get_loader:
            mock_loader = Mock()
            mock_loader.discover_personas.return_value = {
                "test-agent": Path("test-agent.yaml"),
            }
            mock_loader.load_persona.return_value = mock_persona_spec
            mock_get_loader.return_value = mock_loader

            result = runner.invoke(agent_cmd, ["search", "test"])
            assert result.exit_code == 0

    def test_search_personas_by_name(self, runner, mock_persona_spec):
        """Test search-personas command with name match."""
        with patch("orchestra.cli.commands.get_persona_loader") as mock_get_loader:
            mock_loader = Mock()
            mock_loader.discover_personas.return_value = {
                "test-agent": Path("test-agent.yaml"),
            }
            mock_loader.load_persona.return_value = mock_persona_spec
            mock_get_loader.return_value = mock_loader

            result = runner.invoke(agent_cmd, ["search", "Test"])
            assert result.exit_code == 0

    def test_search_personas_by_role(self, runner, mock_persona_spec):
        """Test search-personas command with role match."""
        with patch("orchestra.cli.commands.get_persona_loader") as mock_get_loader:
            mock_loader = Mock()
            mock_loader.discover_personas.return_value = {
                "test-agent": Path("test-agent.yaml"),
            }
            mock_loader.load_persona.return_value = mock_persona_spec
            mock_get_loader.return_value = mock_loader

            result = runner.invoke(agent_cmd, ["search", "Testing"])
            assert result.exit_code == 0

    def test_search_personas_by_principle(self, runner, mock_persona_spec):
        """Test search-personas command with principle match."""
        with patch("orchestra.cli.commands.get_persona_loader") as mock_get_loader:
            mock_loader = Mock()
            mock_loader.discover_personas.return_value = {
                "test-agent": Path("test-agent.yaml"),
            }
            mock_loader.load_persona.return_value = mock_persona_spec
            mock_get_loader.return_value = mock_loader

            result = runner.invoke(agent_cmd, ["search", "thorough"])
            assert result.exit_code == 0

    def test_search_personas_no_matches(self, runner):
        """Test search-personas command with no matches."""
        with patch("orchestra.cli.commands.get_persona_loader") as mock_get_loader:
            mock_loader = Mock()
            mock_loader.discover_personas.return_value = {
                "other-agent": Path("other.yaml"),
            }
            # Mock load_persona to return None for the search test
            mock_loader.load_persona.return_value = None
            mock_get_loader.return_value = mock_loader

            result = runner.invoke(agent_cmd, ["search", "nonexistent"])
            assert result.exit_code == 0

    def test_list_personas_detailed_output(self, runner, mock_persona_spec):
        """Test list-personas command with detailed output."""
        with patch("orchestra.cli.commands.get_persona_loader") as mock_get_loader:
            mock_loader = Mock()
            mock_loader.discover_personas.return_value = {
                "test-agent": Path("test-agent.yaml"),
            }
            mock_loader.load_persona.return_value = mock_persona_spec
            mock_get_loader.return_value = mock_loader

            result = runner.invoke(agent_cmd, ["list-personas", "--detailed"])
            assert result.exit_code == 0

    def test_list_personas_detailed_load_error(self, runner):
        """Test list-personas command with detailed output when persona load fails."""
        with patch("orchestra.cli.commands.get_persona_loader") as mock_get_loader:
            mock_loader = Mock()
            mock_loader.discover_personas.return_value = {
                "test-agent": Path("test-agent.yaml"),
            }
            mock_loader.load_persona.return_value = None
            mock_get_loader.return_value = mock_loader

            result = runner.invoke(agent_cmd, ["list-personas", "--detailed"])
            assert result.exit_code == 0

    def test_list_personas_bmad_converted_type(self, runner):
        """Test list-personas command with BMad converted persona type detection."""
        with patch("orchestra.cli.commands.get_persona_loader") as mock_get_loader:
            mock_loader = Mock()
            mock_loader.discover_personas.return_value = {
                "dev": Path("bmad/dev.yaml"),
            }
            mock_get_loader.return_value = mock_loader

            result = runner.invoke(agent_cmd, ["list-personas"])
            assert result.exit_code == 0

    def test_list_personas_orchestra_native_type(self, runner):
        """Test list-personas command with Orchestra native persona type detection."""
        with patch("orchestra.cli.commands.get_persona_loader") as mock_get_loader:
            mock_loader = Mock()
            mock_loader.discover_personas.return_value = {
                "dev": Path("orchestra/personas/dev.yaml"),
            }
            mock_get_loader.return_value = mock_loader

            result = runner.invoke(agent_cmd, ["list-personas"])
            assert result.exit_code == 0


class TestWorkflowCommands:
    """Test workflow orchestration commands."""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    def test_list_workflows(self, runner):
        """Test list-workflows command."""
        result = runner.invoke(workflow_cmd, ["list"])
        assert result.exit_code == 0

    def test_workflow_status(self, runner):
        """Test workflow-status command."""
        result = runner.invoke(workflow_cmd, ["status"])
        assert result.exit_code == 0


class TestConfigurationCommands:
    """Test configuration management commands."""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    def test_show_config(self, runner):
        """Test show-config command."""
        result = runner.invoke(config_cmd, ["show"])
        assert result.exit_code == 0

    def test_validate_config(self, runner):
        """Test validate-config command."""
        result = runner.invoke(config_cmd, ["validate"])
        assert result.exit_code == 0


class TestDevelopmentCommands:
    """Test development tools and utilities."""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    def test_dev_test(self, runner):
        """Test dev-test command."""
        result = runner.invoke(dev_cmd, ["test"])
        assert result.exit_code == 0

    def test_dev_lint(self, runner):
        """Test dev-lint command."""
        result = runner.invoke(dev_cmd, ["lint"])
        assert result.exit_code == 0


class TestBMadCommands:
    """Test BMad content management commands."""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    def test_bmad_inventory_basic(self, runner):
        """Test bmad-inventory command basic functionality."""
        with patch(
            "orchestra.cli.commands.BmadContentInventory"
        ) as mock_inventory_class:
            mock_inventory = Mock()
            mock_inventory.scan_all.return_value = None
            mock_inventory.generate_report.return_value = {
                "summary": {
                    "total_items": 10,
                    "by_type": {"personas": 5, "tasks": 3, "templates": 2},
                }
            }
            mock_inventory.conversion_strategy.get_validation_rules.return_value = {
                "json_schemas": ["persona", "task"],
                "ci_checks": ["validation", "conversion"],
            }
            mock_inventory.conversion_strategy.plan_directory_structure.return_value = {
                "orchestra/personas": ["dev", "pm", "qa"],
                "orchestra/tasks": ["create-doc", "implement-feature"],
            }
            mock_inventory_class.return_value = mock_inventory

            result = runner.invoke(bmad_cmd, ["inventory"])
            assert result.exit_code == 0

    def test_bmad_inventory_with_output_file(self, runner, tmp_path):
        """Test bmad-inventory command with output file."""
        output_file = tmp_path / "inventory.json"

        with patch(
            "orchestra.cli.commands.BmadContentInventory"
        ) as mock_inventory_class:
            mock_inventory = Mock()
            mock_inventory.scan_all.return_value = None
            mock_inventory.generate_report.return_value = {
                "summary": {"total_items": 5, "by_type": {"personas": 3, "tasks": 2}}
            }
            mock_inventory.conversion_strategy.get_validation_rules.return_value = {
                "json_schemas": ["persona"],
                "ci_checks": ["validation"],
            }
            mock_inventory.conversion_strategy.plan_directory_structure.return_value = {
                "orchestra/personas": ["dev", "pm"]
            }
            mock_inventory_class.return_value = mock_inventory

            result = runner.invoke(
                bmad_cmd, ["inventory", "--output", str(output_file)]
            )
            assert result.exit_code == 0

    def test_bmad_inventory_verbose(self, runner):
        """Test bmad-inventory command with verbose output."""
        with patch(
            "orchestra.cli.commands.BmadContentInventory"
        ) as mock_inventory_class:
            mock_inventory = Mock()
            mock_inventory.scan_all.return_value = None
            mock_inventory.generate_report.return_value = {
                "summary": {"total_items": 3, "by_type": {"personas": 3}},
                "personas": [{"name": "dev"}, {"name": "pm"}, {"name": "qa"}],
                "tasks": [{"name": "create-doc"}],
                "templates": [{"name": "prd-template"}],
                "checklists": [{"name": "release-checklist"}],
            }

            # Create proper mock strategy with real dictionaries
            mock_strategy = Mock()
            mock_strategy.get_validation_rules.return_value = {
                "json_schemas": ["persona"],
                "ci_checks": ["validation"],
            }
            mock_strategy.plan_directory_structure.return_value = {
                "orchestra/personas": ["dev", "pm", "qa"]
            }
            mock_inventory.conversion_strategy = mock_strategy
            mock_inventory_class.return_value = mock_inventory

            result = runner.invoke(bmad_cmd, ["inventory", "--verbose"])
            assert result.exit_code == 0

    def test_convert_persona_success(self, runner):
        """Test convert-persona command with successful conversion."""
        with patch(
            "orchestra.cli.commands.BmadContentInventory"
        ) as mock_inventory_class:
            mock_inventory = Mock()
            mock_agent = Mock()
            mock_agent.name = "dev.md"
            mock_inventory.scan_agents.return_value = [mock_agent]

            # Mock conversion strategy
            mock_strategy = Mock()
            mock_schema = Mock()
            mock_schema.schema_type = "PersonaSpec"
            mock_schema.version = "1.0.0"
            mock_schema.is_valid.return_value = True
            mock_schema.get_validation_errors.return_value = []
            mock_schema.schema_definition = {"identity": {"name": "dev"}}
            mock_strategy.convert_persona.return_value = mock_schema
            mock_inventory.conversion_strategy = mock_strategy

            mock_inventory_class.return_value = mock_inventory

            result = runner.invoke(bmad_cmd, ["convert-persona", "dev.md"])
            assert result.exit_code == 0

    def test_convert_persona_not_found(self, runner):
        """Test convert-persona command when persona is not found."""
        with patch(
            "orchestra.cli.commands.BmadContentInventory"
        ) as mock_inventory_class:
            mock_inventory = Mock()
            mock_inventory.scan_agents.return_value = []
            mock_inventory_class.return_value = mock_inventory

            result = runner.invoke(bmad_cmd, ["convert-persona", "nonexistent.md"])
            assert result.exit_code == 1

    def test_convert_all_personas_dry_run(self, runner):
        """Test convert-all-personas command with dry run."""
        with patch(
            "orchestra.cli.commands.BmadContentInventory"
        ) as mock_inventory_class:
            with patch(
                "orchestra.cli.commands.BmadPersonaConverter"
            ) as mock_converter_class:
                mock_inventory = Mock()
                mock_agent = Mock()
                mock_agent.name = "dev.md"
                mock_agent.path.exists.return_value = True
                mock_inventory.scan_agents.return_value = [mock_agent]
                mock_inventory_class.return_value = mock_inventory

                mock_converter = Mock()
                mock_converter.identify_target_personas.return_value = [mock_agent]
                mock_converter_class.return_value = mock_converter

                result = runner.invoke(bmad_cmd, ["convert-all-personas", "--dry-run"])
                assert result.exit_code == 0

    def test_convert_all_personas_success(self, runner):
        """Test convert-all-personas command with successful conversion."""
        with patch(
            "orchestra.cli.commands.BmadContentInventory"
        ) as mock_inventory_class:
            with patch(
                "orchestra.cli.commands.BmadPersonaConverter"
            ) as mock_converter_class:
                mock_inventory = Mock()
                mock_agent = Mock()
                mock_agent.name = "dev.md"
                mock_agent.path = Mock()
                mock_agent.path.exists.return_value = True
                mock_inventory.scan_agents.return_value = [mock_agent]
                mock_inventory_class.return_value = mock_inventory

                mock_converter = Mock()
                mock_converter.identify_target_personas.return_value = [mock_agent]
                mock_converter.convert_and_save_all.return_value = [
                    Mock(success=True, persona_id="dev", validation_errors=[])
                ]
                mock_converter_class.return_value = mock_converter

                result = runner.invoke(bmad_cmd, ["convert-all-personas"])
                assert result.exit_code == 0

    def test_convert_all_personas_with_force(self, runner):
        """Test convert-all-personas command with force flag."""
        with patch(
            "orchestra.cli.commands.BmadContentInventory"
        ) as mock_inventory_class:
            with patch(
                "orchestra.cli.commands.BmadPersonaConverter"
            ) as mock_converter_class:
                mock_inventory = Mock()
                mock_agent = Mock()
                mock_agent.name = "dev.md"
                mock_agent.path.exists.return_value = True
                mock_inventory.scan_agents.return_value = [mock_agent]
                mock_inventory_class.return_value = mock_inventory

                mock_converter = Mock()
                mock_converter.identify_target_personas.return_value = [mock_agent]
                mock_converter.convert_and_save_all.return_value = [
                    Mock(success=True, persona_id="dev", validation_errors=[])
                ]
                mock_converter_class.return_value = mock_converter

                result = runner.invoke(bmad_cmd, ["convert-all-personas", "--force"])
                assert result.exit_code == 0

    def test_convert_all_personas_with_output_dir(self, runner):
        """Test convert-all-personas command with custom output directory."""
        with patch(
            "orchestra.cli.commands.BmadContentInventory"
        ) as mock_inventory_class:
            with patch(
                "orchestra.cli.commands.BmadPersonaConverter"
            ) as mock_converter_class:
                mock_inventory = Mock()
                mock_agent = Mock()
                mock_agent.name = "dev.md"
                mock_agent.path = Mock()
                mock_agent.path.exists.return_value = True
                mock_inventory.scan_agents.return_value = [mock_agent]
                mock_inventory_class.return_value = mock_inventory

                mock_converter = Mock()
                mock_converter.identify_target_personas.return_value = [mock_agent]
                mock_converter.convert_and_save_all.return_value = [
                    Mock(success=True, persona_id="dev", validation_errors=[])
                ]
                mock_converter_class.return_value = mock_converter

                result = runner.invoke(
                    bmad_cmd, ["convert-all-personas", "--output-dir", "custom/output"]
                )
                assert result.exit_code == 0

    def test_convert_all_personas_no_agents(self, runner):
        """Test convert-all-personas command when no agents are found."""
        with patch(
            "orchestra.cli.commands.BmadContentInventory"
        ) as mock_inventory_class:
            mock_inventory = Mock()
            mock_inventory.scan_agents.return_value = []
            mock_inventory_class.return_value = mock_inventory

            result = runner.invoke(bmad_cmd, ["convert-all-personas"])
            assert result.exit_code == 0

    def test_validate_converted_personas_success(self, runner, tmp_path):
        """Test validate-converted-personas command with valid personas."""
        personas_dir = tmp_path / "personas"
        personas_dir.mkdir()
        (personas_dir / "dev.yaml").write_text(
            """identity:
  name: Developer
  id: dev
  title: Developer
  role: Development
  icon: 👨‍💻
  when_to_use: For development tasks
  style: Technical
  focus: Code quality
behavioral_contract:
  core_principles: []
  work_style: ""
  communication_style: ""
command_interface:
  commands: {}
resource_dependencies:
  tools: []
  knowledge_sources: []
  required_services: []
version: 1.0.0"""
        )

        with patch(
            "orchestra.cli.commands.BmadPersonaConverter"
        ) as mock_converter_class:
            mock_converter = Mock()
            mock_converter.validate_persona_schema.return_value = Mock(
                is_valid=True, errors=[]
            )
            mock_converter_class.return_value = mock_converter

            result = runner.invoke(
                bmad_cmd, ["validate-converted-personas", str(personas_dir)]
            )
            assert result.exit_code == 0

    def test_validate_converted_personas_no_files(self, runner, tmp_path):
        """Test validate-converted-personas command when no YAML files exist."""
        personas_dir = tmp_path / "personas"
        personas_dir.mkdir()
        # Create a non-YAML file
        (personas_dir / "readme.txt").write_text("This is not a YAML file")

        with patch(
            "orchestra.cli.commands.BmadPersonaConverter"
        ) as mock_converter_class:
            mock_converter = Mock()
            mock_converter.validate_persona_schema.return_value = Mock(
                is_valid=True, errors=[]
            )
            mock_converter_class.return_value = mock_converter

            result = runner.invoke(
                bmad_cmd, ["validate-converted-personas", str(personas_dir)]
            )
            assert result.exit_code == 0

    def test_validate_converted_personas_validation_error(self, runner, tmp_path):
        """Test validate-converted-personas command with validation errors."""
        personas_dir = tmp_path / "personas"
        personas_dir.mkdir()
        (personas_dir / "dev.yaml").write_text(
            """identity:
  name: Developer
  id: dev
  title: Developer
  role: Development
  icon: 👨‍💻
  when_to_use: For development tasks
  style: Technical
  focus: Code quality
behavioral_contract:
  core_principles: []
  work_style: ""
  communication_style: ""
command_interface:
  commands: {}
resource_dependencies:
  tools: []
  knowledge_sources: []
  required_services: []
version: 1.0.0"""
        )

        with patch(
            "orchestra.cli.commands.BmadPersonaConverter"
        ) as mock_converter_class:
            mock_converter = Mock()
            mock_converter.validate_persona_schema.return_value = Mock(
                is_valid=False, errors=["Missing required field"]
            )
            mock_converter_class.return_value = mock_converter

            result = runner.invoke(
                bmad_cmd, ["validate-converted-personas", str(personas_dir)]
            )
            assert result.exit_code == 1

    def test_validate_converted_personas_verbose(self, runner, tmp_path):
        """Test validate-converted-personas command with verbose output."""
        personas_dir = tmp_path / "personas"
        personas_dir.mkdir()
        (personas_dir / "dev.yaml").write_text(
            """identity:
  name: Developer
  id: dev
  title: Developer
  role: Development
  icon: 👨‍💻
  when_to_use: For development tasks
  style: Technical
  focus: Code quality
behavioral_contract:
  core_principles: []
  work_style: ""
  communication_style: ""
command_interface:
  commands: {}
resource_dependencies:
  tools: []
  knowledge_sources: []
  required_services: []
version: 1.0.0"""
        )

        with patch(
            "orchestra.cli.commands.BmadPersonaConverter"
        ) as mock_converter_class:
            mock_converter = Mock()
            mock_converter.validate_persona_schema.return_value = Mock(
                is_valid=True, errors=[]
            )
            mock_converter_class.return_value = mock_converter

            result = runner.invoke(
                bmad_cmd,
                ["validate-converted-personas", str(personas_dir), "--verbose"],
            )
            assert result.exit_code == 0

    def test_list_resources_basic(self, runner):
        """Test list-resources command basic functionality."""
        with patch("orchestra.cli.commands.ResourceLoader") as mock_loader_class:
            mock_loader = Mock()
            mock_resource = Mock()
            mock_resource.id = "create-doc"
            mock_resource.name = "Create Document"
            mock_resource.description = "Create a document"
            mock_resource.trust_level = "core"
            mock_resource.tags = ["documentation"]
            mock_loader.discover_resources.return_value = [mock_resource]
            mock_loader_class.return_value = mock_loader

            result = runner.invoke(bmad_cmd, ["list-resources"])
            assert result.exit_code == 0

    def test_list_resources_by_type(self, runner):
        """Test list-resources command with type filter."""
        with patch("orchestra.cli.commands.ResourceLoader") as mock_loader_class:
            mock_loader = Mock()
            mock_resource = Mock()
            mock_resource.id = "create-doc"
            mock_resource.name = "Create Document"
            mock_resource.description = "Create a document"
            mock_resource.trust_level = "core"
            mock_resource.tags = ["documentation"]
            mock_loader.discover_resources.return_value = [mock_resource]
            mock_loader_class.return_value = mock_loader

            result = runner.invoke(bmad_cmd, ["list-resources", "--type", "task"])
            assert result.exit_code == 0

    def test_list_resources_invalid_type(self, runner):
        """Test list-resources command with invalid type."""
        result = runner.invoke(bmad_cmd, ["list-resources", "--type", "invalid"])
        assert result.exit_code == 1

    def test_list_resources_no_resources(self, runner):
        """Test list-resources command when no resources are found."""
        with patch("orchestra.cli.commands.ResourceLoader") as mock_loader_class:
            mock_loader = Mock()
            mock_loader.discover_resources.return_value = []
            mock_loader_class.return_value = mock_loader

            result = runner.invoke(bmad_cmd, ["list-resources"])
            assert result.exit_code == 0

    def test_list_resources_with_tasks(self, runner):
        """Test list-resources command with task resources."""
        with patch("orchestra.cli.commands.ResourceLoader") as mock_loader_class:
            mock_loader = Mock()
            mock_resource = Mock()
            mock_resource.id = "create-doc"
            mock_resource.name = "Create Document"
            mock_resource.description = "Create a document"
            mock_resource.trust_level = "core"
            mock_resource.tags = ["documentation"]
            mock_loader.discover_resources.return_value = [mock_resource]
            mock_loader_class.return_value = mock_loader

            result = runner.invoke(bmad_cmd, ["list-resources", "--type", "task"])
            assert result.exit_code == 0

    def test_list_resources_with_templates(self, runner):
        """Test list-resources command with template resources."""
        with patch("orchestra.cli.commands.ResourceLoader") as mock_loader_class:
            mock_loader = Mock()
            mock_resource = Mock()
            mock_resource.id = "prd-template"
            mock_resource.name = "PRD Template"
            mock_resource.description = "Product Requirements Document template"
            mock_resource.trust_level = "core"
            mock_resource.tags = ["documentation", "product"]
            mock_loader.discover_resources.return_value = [mock_resource]
            mock_loader_class.return_value = mock_loader

            result = runner.invoke(bmad_cmd, ["list-resources", "--type", "template"])
            assert result.exit_code == 0

    def test_list_resources_with_checklists(self, runner):
        """Test list-resources command with checklist resources."""
        with patch("orchestra.cli.commands.ResourceLoader") as mock_loader_class:
            mock_loader = Mock()
            mock_resource = Mock()
            mock_resource.id = "release-checklist"
            mock_resource.name = "Release Checklist"
            mock_resource.description = "Pre-release verification checklist"
            mock_resource.trust_level = "core"
            mock_resource.tags = ["release", "quality"]
            mock_loader.discover_resources.return_value = [mock_resource]
            mock_loader_class.return_value = mock_loader

            result = runner.invoke(bmad_cmd, ["list-resources", "--type", "checklist"])
            assert result.exit_code == 0

    def test_execute_task_success(self, runner):
        """Test execute-task command with successful execution."""
        with patch("orchestra.cli.commands.ResourceLoader") as mock_loader_class:
            with patch("orchestra.cli.commands.TaskEngine") as mock_engine_class:
                mock_loader = Mock()
                mock_loader.load_resource.return_value = Mock(
                    success=True,
                    metadata=Mock(id="test-task"),
                    content="# Test Task\n\n## Steps\n- Step 1\n- Step 2",
                )
                mock_loader_class.return_value = mock_loader

                mock_engine = Mock()
                mock_engine.execute_task.return_value = Mock(
                    success=True,
                    execution_time=1.5,
                    steps_completed=2,
                    total_steps=2,
                    warnings=[],
                    outputs={"result": "success"},
                )
                mock_engine_class.return_value = mock_engine

                result = runner.invoke(bmad_cmd, ["execute-task", "test-task"])
                assert result.exit_code == 0

    def test_execute_task_load_failure(self, runner):
        """Test execute-task command when task loading fails."""
        with patch("orchestra.cli.commands.ResourceLoader") as mock_loader_class:
            mock_loader = Mock()
            mock_loader.load_resource.return_value = Mock(
                success=False, validation_errors=["Invalid task format"]
            )
            mock_loader_class.return_value = mock_loader

            result = runner.invoke(bmad_cmd, ["execute-task", "invalid-task"])
            assert result.exit_code == 1

    def test_execute_task_with_context_file(self, runner, tmp_path):
        """Test execute-task command with context file."""
        context_file = tmp_path / "context.json"
        context_file.write_text('{"project": "test-project", "user": "test-user"}')

        with patch("orchestra.cli.commands.ResourceLoader") as mock_loader_class:
            with patch("orchestra.cli.commands.TaskEngine") as mock_engine_class:
                mock_loader = Mock()
                mock_loader.load_resource.return_value = Mock(
                    success=True,
                    metadata=Mock(id="test-task"),
                    content="# Test Task\n\n## Steps\n- Step 1\n- Step 2",
                )
                mock_loader_class.return_value = mock_loader

                mock_engine = Mock()
                mock_engine.execute_task.return_value = Mock(
                    success=True,
                    execution_time=1.5,
                    steps_completed=2,
                    total_steps=2,
                    warnings=[],
                    outputs={"result": "success"},
                )
                mock_engine_class.return_value = mock_engine

                result = runner.invoke(
                    bmad_cmd,
                    ["execute-task", "test-task", "--context", str(context_file)],
                )
                assert result.exit_code == 0

    def test_execute_task_with_timeout(self, runner):
        """Test execute-task command with timeout."""
        with patch("orchestra.cli.commands.ResourceLoader") as mock_loader_class:
            with patch("orchestra.cli.commands.TaskEngine") as mock_engine_class:
                mock_loader = Mock()
                mock_loader.load_resource.return_value = Mock(
                    success=True,
                    metadata=Mock(id="test-task"),
                    content="# Test Task\n\n## Steps\n- Step 1\n- Step 2",
                )
                mock_loader_class.return_value = mock_loader

                mock_engine = Mock()
                mock_engine.execute_task.return_value = Mock(
                    success=True,
                    execution_time=1.5,
                    steps_completed=2,
                    total_steps=2,
                    warnings=[],
                    outputs={"result": "success"},
                )
                mock_engine_class.return_value = mock_engine

                result = runner.invoke(
                    bmad_cmd, ["execute-task", "test-task", "--timeout", "600"]
                )
                assert result.exit_code == 0

    def test_execute_task_with_warnings(self, runner):
        """Test execute-task command with warnings."""
        with patch("orchestra.cli.commands.ResourceLoader") as mock_loader_class:
            with patch("orchestra.cli.commands.TaskEngine") as mock_engine_class:
                mock_loader = Mock()
                mock_loader.load_resource.return_value = Mock(
                    success=True,
                    metadata=Mock(id="test-task"),
                    content="# Test Task\n\n## Steps\n- Step 1\n- Step 2",
                )
                mock_loader_class.return_value = mock_loader

                mock_engine = Mock()
                mock_engine.execute_task.return_value = Mock(
                    success=True,
                    execution_time=1.5,
                    steps_completed=2,
                    total_steps=2,
                    warnings=["Step 2 took longer than expected"],
                    outputs={"result": "success"},
                )
                mock_engine_class.return_value = mock_engine

                result = runner.invoke(bmad_cmd, ["execute-task", "test-task"])
                assert result.exit_code == 0

    def test_execute_task_context_file_error(self, runner, tmp_path):
        """Test execute-task command with invalid context file."""
        context_file = tmp_path / "invalid.json"
        context_file.write_text("invalid json content")

        result = runner.invoke(
            bmad_cmd, ["execute-task", "test-task", "--context", str(context_file)]
        )
        assert result.exit_code == 1

    def test_render_template_success(self, runner, tmp_path):
        """Test render-template command with successful rendering."""
        context_file = tmp_path / "context.json"
        context_file.write_text('{"name": "World"}')

        with patch("orchestra.cli.commands.ResourceLoader") as mock_loader_class:
            with patch(
                "orchestra.cli.commands.TemplateProcessor"
            ) as mock_processor_class:
                mock_loader = Mock()
                mock_loader.load_resource.return_value = Mock(
                    success=True,
                    metadata=Mock(id="test-template"),
                    content="# Test Template\n\nHello {{name}}!",
                )
                mock_loader_class.return_value = mock_loader

                mock_processor = Mock()
                mock_processor.render_template.return_value = Mock(
                    success=True,
                    render_time=0.5,
                    warnings=[],
                    rendered_content="Hello World!",
                )
                mock_processor_class.return_value = mock_processor

                result = runner.invoke(
                    bmad_cmd,
                    [
                        "render-template",
                        "test-template",
                        "--context",
                        str(context_file),
                    ],
                )
                assert result.exit_code == 0

    def test_execute_checklist_success(self, runner):
        """Test execute-checklist command with successful execution."""
        with patch("orchestra.cli.commands.ResourceLoader") as mock_loader_class:
            with patch("orchestra.cli.commands.ChecklistEngine") as mock_engine_class:
                mock_loader = Mock()
                mock_loader.load_resource.return_value = Mock(
                    success=True,
                    metadata=Mock(id="test-checklist"),
                    content="# Test Checklist\n\n- [ ] Item 1\n- [ ] Item 2",
                )
                mock_loader_class.return_value = mock_loader

                mock_engine = Mock()
                mock_engine.execute_checklist.return_value = Mock(
                    success=True,
                    execution_time=2.0,
                    completion_percentage=100.0,
                    completed_items=2,
                    total_items=2,
                    not_applicable_items=0,
                    auto_checked_items=0,
                    warnings=[],
                )
                mock_engine.export_checklist_report.return_value = (
                    "# Checklist Report\n\nAll items completed."
                )
                mock_engine_class.return_value = mock_engine

                result = runner.invoke(
                    bmad_cmd, ["execute-checklist", "test-checklist"]
                )
                assert result.exit_code == 0

    def test_execute_checklist_with_context_file(self, runner, tmp_path):
        """Test execute-checklist command with context file."""
        context_file = tmp_path / "context.json"
        context_file.write_text('{"project": "test-project", "user": "test-user"}')

        with patch("orchestra.cli.commands.ResourceLoader") as mock_loader_class:
            with patch("orchestra.cli.commands.ChecklistEngine") as mock_engine_class:
                mock_loader = Mock()
                mock_loader.load_resource.return_value = Mock(
                    success=True,
                    metadata=Mock(id="test-checklist"),
                    content="# Test Checklist\n\n- [ ] Item 1\n- [ ] Item 2",
                )
                mock_loader_class.return_value = mock_loader

                mock_engine = Mock()
                mock_engine.execute_checklist.return_value = Mock(
                    success=True,
                    execution_time=2.0,
                    completion_percentage=100.0,
                    completed_items=2,
                    total_items=2,
                    not_applicable_items=0,
                    auto_checked_items=0,
                    warnings=[],
                )
                mock_engine.export_checklist_report.return_value = (
                    "# Checklist Report\n\nAll items completed."
                )
                mock_engine_class.return_value = mock_engine

                result = runner.invoke(
                    bmad_cmd,
                    [
                        "execute-checklist",
                        "test-checklist",
                        "--context",
                        str(context_file),
                    ],
                )
                assert result.exit_code == 0

    def test_execute_checklist_with_auto_check(self, runner):
        """Test execute-checklist command with auto-check enabled."""
        with patch("orchestra.cli.commands.ResourceLoader") as mock_loader_class:
            with patch("orchestra.cli.commands.ChecklistEngine") as mock_engine_class:
                mock_loader = Mock()
                mock_loader.load_resource.return_value = Mock(
                    success=True,
                    metadata=Mock(id="test-checklist"),
                    content="# Test Checklist\n\n- [ ] Item 1\n- [ ] Item 2",
                )
                mock_loader_class.return_value = mock_loader

                mock_engine = Mock()
                mock_engine.execute_checklist.return_value = Mock(
                    success=True,
                    execution_time=2.0,
                    completion_percentage=100.0,
                    completed_items=2,
                    total_items=2,
                    not_applicable_items=0,
                    auto_checked_items=1,
                    warnings=[],
                )
                mock_engine.export_checklist_report.return_value = (
                    "# Checklist Report\n\nAll items completed."
                )
                mock_engine_class.return_value = mock_engine

                result = runner.invoke(
                    bmad_cmd, ["execute-checklist", "test-checklist", "--auto-check"]
                )
                assert result.exit_code == 0

    def test_execute_checklist_with_warnings(self, runner):
        """Test execute-checklist command with warnings."""
        with patch("orchestra.cli.commands.ResourceLoader") as mock_loader_class:
            with patch("orchestra.cli.commands.ChecklistEngine") as mock_engine_class:
                mock_loader = Mock()
                mock_loader.load_resource.return_value = Mock(
                    success=True,
                    metadata=Mock(id="test-checklist"),
                    content="# Test Checklist\n\n- [ ] Item 1\n- [ ] Item 2",
                )
                mock_loader_class.return_value = mock_loader

                mock_engine = Mock()
                mock_engine.execute_checklist.return_value = Mock(
                    success=True,
                    execution_time=2.0,
                    completion_percentage=100.0,
                    completed_items=2,
                    total_items=2,
                    not_applicable_items=0,
                    auto_checked_items=0,
                    warnings=["Item 2 was automatically completed"],
                )
                mock_engine.export_checklist_report.return_value = (
                    "# Checklist Report\n\nAll items completed."
                )
                mock_engine_class.return_value = mock_engine

                result = runner.invoke(
                    bmad_cmd, ["execute-checklist", "test-checklist"]
                )
                assert result.exit_code == 0

    def test_execute_checklist_context_file_error(self, runner, tmp_path):
        """Test execute-checklist command with invalid context file."""
        context_file = tmp_path / "invalid.json"
        context_file.write_text("invalid json content")

        result = runner.invoke(
            bmad_cmd,
            ["execute-checklist", "test-checklist", "--context", str(context_file)],
        )
        assert result.exit_code == 1

    def test_render_template_with_output_file(self, runner, tmp_path):
        """Test render-template command with output file."""
        context_file = tmp_path / "context.json"
        context_file.write_text('{"name": "World", "project": "test"}')
        output_file = tmp_path / "output.md"

        with patch("orchestra.cli.commands.ResourceLoader") as mock_loader_class:
            with patch(
                "orchestra.cli.commands.TemplateProcessor"
            ) as mock_processor_class:
                mock_loader = Mock()
                mock_loader.load_resource.return_value = Mock(
                    success=True,
                    metadata=Mock(id="test-template"),
                    content="# Test Template\n\nHello {{name}}!",
                )
                mock_loader_class.return_value = mock_loader

                mock_processor = Mock()
                mock_processor.render_template.return_value = Mock(
                    success=True,
                    render_time=0.5,
                    warnings=[],
                    rendered_content="Hello World!",
                )
                mock_processor_class.return_value = mock_processor

                result = runner.invoke(
                    bmad_cmd,
                    [
                        "render-template",
                        "test-template",
                        "--context",
                        str(context_file),
                        "--output",
                        str(output_file),
                    ],
                )
                assert result.exit_code == 0

    def test_render_template_with_warnings(self, runner, tmp_path):
        """Test render-template command with warnings."""
        context_file = tmp_path / "context.json"
        context_file.write_text('{"name": "World"}')

        with patch("orchestra.cli.commands.ResourceLoader") as mock_loader_class:
            with patch(
                "orchestra.cli.commands.TemplateProcessor"
            ) as mock_processor_class:
                mock_loader = Mock()
                mock_loader.load_resource.return_value = Mock(
                    success=True,
                    metadata=Mock(id="test-template"),
                    content="# Test Template\n\nHello {{name}}!",
                )
                mock_loader_class.return_value = mock_loader

                mock_processor = Mock()
                mock_processor.render_template.return_value = Mock(
                    success=True,
                    render_time=0.5,
                    warnings=["Variable 'title' not found in context"],
                    rendered_content="Hello World!",
                )
                mock_processor_class.return_value = mock_processor

                result = runner.invoke(
                    bmad_cmd,
                    [
                        "render-template",
                        "test-template",
                        "--context",
                        str(context_file),
                    ],
                )
                assert result.exit_code == 0

    def test_render_template_context_file_error(self, runner, tmp_path):
        """Test render-template command with invalid context file."""
        context_file = tmp_path / "invalid.json"
        context_file.write_text("invalid json content")

        result = runner.invoke(
            bmad_cmd,
            ["render-template", "test-template", "--context", str(context_file)],
        )
        assert result.exit_code == 1


class TestOverlayCommands:
    """Test overlay management commands."""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    def test_preview_merged_persona_success(self, runner):
        """Test preview-merged-persona command with successful preview."""
        with patch("orchestra.cli.commands.get_persona_loader") as mock_get_loader:
            mock_loader = Mock()
            mock_loader.load_persona.return_value = Mock(
                identity=Mock(name="Test Agent", id="test-agent", role="Testing"),
                behavioral_contract=Mock(core_principles=["Test everything"]),
                command_interface=Mock(commands={"test": Mock()}),
                resource_dependencies=Mock(tools=["tool1", "tool2"]),
            )
            mock_get_loader.return_value = mock_loader

            result = runner.invoke(
                overlay_cmd, ["preview", "test-agent", "--team", "backend"]
            )
            assert result.exit_code == 0

    def test_preview_merged_persona_not_found(self, runner):
        """Test preview-merged-persona command when persona is not found."""
        with patch("orchestra.cli.commands.get_persona_loader") as mock_get_loader:
            mock_loader = Mock()
            mock_loader.load_persona.return_value = None
            mock_get_loader.return_value = mock_loader

            result = runner.invoke(overlay_cmd, ["preview", "nonexistent-agent"])
            assert result.exit_code == 1

    def test_list_overlays_no_overlays(self, runner):
        """Test list-overlays command when no overlays exist."""
        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.return_value = False

            result = runner.invoke(overlay_cmd, ["list"])
            assert result.exit_code == 0

    def test_list_overlays_with_persona_filter(self, runner):
        """Test list-overlays command with persona filter."""
        with patch("pathlib.Path.exists") as mock_exists:
            with patch("pathlib.Path.iterdir") as mock_iterdir:
                mock_exists.return_value = True
                mock_iterdir.return_value = []

                result = runner.invoke(overlay_cmd, ["list", "--persona", "dev"])
                assert result.exit_code == 0


class TestErrorHandling:
    """Test error handling in CLI commands."""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    def test_list_agents_exception_handling(self, runner):
        """Test list-agents command exception handling."""
        with patch("orchestra.cli.commands.get_registry") as mock_get_registry:
            mock_get_registry.side_effect = Exception("Registry error")

            result = runner.invoke(agent_cmd, ["list"])
            assert result.exit_code == 1

    def test_list_personas_exception_handling(self, runner):
        """Test list-personas command exception handling."""
        with patch("orchestra.cli.commands.get_persona_loader") as mock_get_loader:
            mock_get_loader.side_effect = Exception("Loader error")

            result = runner.invoke(agent_cmd, ["list-personas"])
            assert result.exit_code == 1

    def test_describe_persona_exception_handling(self, runner):
        """Test describe-persona command exception handling."""
        with patch("orchestra.cli.commands.get_persona_loader") as mock_get_loader:
            mock_get_loader.side_effect = Exception("Loader error")

            result = runner.invoke(agent_cmd, ["describe", "test-agent"])
            assert result.exit_code == 1

    def test_search_personas_exception_handling(self, runner):
        """Test search-personas command exception handling."""
        with patch("orchestra.cli.commands.get_persona_loader") as mock_get_loader:
            mock_loader = Mock()
            mock_loader.discover_personas.side_effect = Exception("Search error")
            mock_get_loader.return_value = mock_loader

            result = runner.invoke(agent_cmd, ["search", "test"])
            assert result.exit_code == 1

    def test_activate_persona_exception_handling(self, runner):
        """Test activate-persona command exception handling."""
        with patch("orchestra.cli.commands.get_persona_loader") as mock_get_loader:
            mock_loader = Mock()
            mock_loader.load_persona.side_effect = Exception("Activation error")
            mock_get_loader.return_value = mock_loader

            result = runner.invoke(agent_cmd, ["activate", "test-agent"])
            assert result.exit_code == 1

    def test_bmad_inventory_exception_handling(self, runner):
        """Test bmad-inventory command exception handling."""
        with patch(
            "orchestra.cli.commands.BmadContentInventory"
        ) as mock_inventory_class:
            mock_inventory_class.side_effect = Exception("Inventory error")

            result = runner.invoke(bmad_cmd, ["inventory"])
            assert result.exit_code == 1

    def test_convert_persona_exception_handling(self, runner):
        """Test convert-persona command exception handling."""
        with patch(
            "orchestra.cli.commands.BmadContentInventory"
        ) as mock_inventory_class:
            mock_inventory_class.side_effect = Exception("Conversion error")

            result = runner.invoke(bmad_cmd, ["convert-persona", "dev.md"])
            assert result.exit_code == 1

    def test_convert_all_personas_exception_handling(self, runner):
        """Test convert-all-personas command exception handling."""
        with patch(
            "orchestra.cli.commands.BmadContentInventory"
        ) as mock_inventory_class:
            mock_inventory_class.side_effect = Exception("Batch conversion error")

            result = runner.invoke(bmad_cmd, ["convert-all-personas"])
            assert result.exit_code == 1

    def test_validate_converted_personas_exception_handling(self, runner):
        """Test validate-converted-personas command exception handling."""
        with patch(
            "orchestra.cli.commands.BmadPersonaConverter"
        ) as mock_converter_class:
            mock_converter_class.side_effect = Exception("Validation error")

            result = runner.invoke(
                bmad_cmd, ["validate-converted-personas", "nonexistent"]
            )
            assert result.exit_code == 1

    def test_list_resources_exception_handling(self, runner):
        """Test list-resources command exception handling."""
        with patch("orchestra.cli.commands.ResourceLoader") as mock_loader_class:
            mock_loader_class.side_effect = Exception("Resource loading error")

            result = runner.invoke(bmad_cmd, ["list-resources"])
            assert result.exit_code == 1

    def test_execute_task_exception_handling(self, runner):
        """Test execute-task command exception handling."""
        with patch("orchestra.cli.commands.ResourceLoader") as mock_loader_class:
            mock_loader_class.side_effect = Exception("Task execution error")

            result = runner.invoke(bmad_cmd, ["execute-task", "test-task"])
            assert result.exit_code == 1

    def test_render_template_exception_handling(self, runner):
        """Test render-template command exception handling."""
        with patch("orchestra.cli.commands.ResourceLoader") as mock_loader_class:
            mock_loader_class.side_effect = Exception("Template rendering error")

            result = runner.invoke(bmad_cmd, ["render-template", "test-template"])
            assert result.exit_code == 1

    def test_execute_checklist_exception_handling(self, runner):
        """Test execute-checklist command exception handling."""
        with patch("orchestra.cli.commands.ResourceLoader") as mock_loader_class:
            mock_loader_class.side_effect = Exception("Checklist execution error")

            result = runner.invoke(bmad_cmd, ["execute-checklist", "test-checklist"])
            assert result.exit_code == 1


class TestIntegrationScenarios:
    """Test integration scenarios for CLI commands."""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def mock_persona_spec(self):
        """Create a mock persona specification."""
        mock_identity = Mock()
        mock_identity.name = "Test Agent"
        mock_identity.id = "test-agent"
        mock_identity.role = "Testing"
        mock_identity.title = "Test Agent"
        mock_identity.icon = "🧪"
        mock_identity.when_to_use = "For testing purposes"
        mock_identity.style = "Systematic"
        mock_identity.focus = "Quality assurance"

        mock_behavioral = Mock()
        mock_behavioral.core_principles = ["Test everything", "Be thorough"]
        mock_behavioral.work_style = "Systematic"
        mock_behavioral.communication_style = "Clear and concise"
        mock_behavioral.interaction_style = "Professional"

        mock_command_interface = Mock()
        mock_command_interface.commands = {"test": Mock()}

        mock_resource_deps = Mock()
        mock_resource_deps.tools = ["pytest", "coverage"]
        mock_resource_deps.knowledge_sources = ["docs", "tests"]
        mock_resource_deps.required_services = ["test-db", "ci"]
        mock_resource_deps.tasks = []
        mock_resource_deps.templates = []

        mock_persona = Mock()
        mock_persona.identity = mock_identity
        mock_persona.behavioral_contract = mock_behavioral
        mock_persona.command_interface = mock_command_interface
        mock_persona.resource_dependencies = mock_resource_deps

        return mock_persona

    def test_full_persona_workflow(self, runner):
        """Test a complete persona workflow: list, describe, activate, execute."""
        with patch("orchestra.cli.commands.get_persona_loader") as mock_get_loader:
            mock_loader = Mock()
            mock_loader.discover_personas.return_value = {"dev": Path("dev.yaml")}

            # Create proper mock objects with string attributes
            mock_identity = Mock()
            mock_identity.name = "Developer"
            mock_identity.id = "dev"
            mock_identity.role = "Development"
            mock_identity.title = "Developer"
            mock_identity.icon = "👨‍💻"
            mock_identity.when_to_use = "For development tasks"
            mock_identity.style = "Technical"
            mock_identity.focus = "Code quality"

            mock_behavioral = Mock()
            mock_behavioral.core_principles = ["Write clean code", "Test everything"]
            mock_behavioral.work_style = "Systematic"
            mock_behavioral.communication_style = "Clear and concise"

            mock_command_interface = Mock()
            mock_command_interface.commands = {"implement": Mock()}

            mock_resource_deps = Mock()
            mock_resource_deps.tools = ["git", "python"]
            mock_resource_deps.knowledge_sources = ["docs", "api"]
            mock_resource_deps.required_services = ["github", "docker"]
            mock_resource_deps.tasks = []
            mock_resource_deps.templates = []

            mock_persona = Mock()
            mock_persona.identity = mock_identity
            mock_persona.behavioral_contract = mock_behavioral
            mock_persona.command_interface = mock_command_interface
            mock_persona.resource_dependencies = mock_resource_deps

            mock_loader.load_persona.return_value = mock_persona
            mock_get_loader.return_value = mock_loader

            # Test list personas
            result = runner.invoke(agent_cmd, ["list-personas"])
            assert result.exit_code == 0

            # Test describe persona
            result = runner.invoke(agent_cmd, ["describe", "dev"])
            assert result.exit_code == 0

            # Test activate persona
            result = runner.invoke(agent_cmd, ["activate", "dev"])
            assert result.exit_code == 0

    def test_full_bmad_workflow(self, runner):
        """Test a complete BMad workflow: inventory, convert, validate."""
        with patch(
            "orchestra.cli.commands.BmadContentInventory"
        ) as mock_inventory_class:
            with patch(
                "orchestra.cli.commands.BmadPersonaConverter"
            ) as mock_converter_class:
                mock_inventory = Mock()
                mock_inventory.scan_all.return_value = None

                # Return a real dictionary for the report
                mock_inventory.generate_report.return_value = {
                    "summary": {
                        "total_items": 5,
                        "by_type": {"personas": 3, "tasks": 2},
                    },
                    "personas": [
                        {"name": "dev.md"},
                        {"name": "pm.md"},
                        {"name": "qa.md"},
                    ],
                    "tasks": [{"name": "task1.md"}, {"name": "task2.md"}],
                    "templates": [],
                    "checklists": [],
                }

                mock_agent = Mock()
                mock_agent.name = "dev.md"
                mock_inventory.scan_agents.return_value = [mock_agent]
                mock_inventory_class.return_value = mock_inventory

                # Mock the conversion strategy
                mock_strategy = Mock()
                mock_strategy.get_validation_rules.return_value = {
                    "json_schemas": ["persona"],
                    "ci_checks": ["validation"],
                }
                mock_strategy.plan_directory_structure.return_value = {
                    "orchestra/personas": ["dev", "pm", "qa"]
                }
                mock_schema = Mock()
                mock_schema.schema_type = "persona"
                mock_schema.version = "1.0.0"
                mock_schema.is_valid.return_value = True
                mock_schema.get_validation_errors.return_value = []
                mock_schema.schema_definition = {
                    "identity": {"name": "Developer", "id": "dev"},
                    "behavioral_contract": {},
                    "command_interface": {},
                    "resource_dependencies": {},
                }
                mock_strategy.convert_persona.return_value = mock_schema
                mock_inventory.conversion_strategy = mock_strategy

                mock_converter = Mock()
                mock_converter.identify_target_personas.return_value = [mock_agent]
                mock_converter.validate_persona_schema.return_value = Mock(
                    is_valid=True, errors=[]
                )
                mock_converter_class.return_value = mock_converter

                # Test inventory
                result = runner.invoke(bmad_cmd, ["inventory"])
                assert result.exit_code == 0

                # Test convert persona
                result = runner.invoke(bmad_cmd, ["convert-persona", "dev.md"])
                assert result.exit_code == 0

                # Test validate converted personas - create a temporary directory with a valid persona file
                import tempfile

                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_path = Path(temp_dir)
                    (temp_path / "dev.yaml").write_text(
                        """identity:
  name: Developer
  id: dev
  title: Developer
  role: Development
  icon: 👨‍💻
  when_to_use: For development tasks
  style: Technical
  focus: Code quality
behavioral_contract:
  core_principles: []
  work_style: ""
  communication_style: ""
command_interface:
  commands: {}
resource_dependencies:
  tools: []
  knowledge_sources: []
  required_services: []
version: 1.0.0"""
                    )

                    result = runner.invoke(
                        bmad_cmd, ["validate-converted-personas", temp_dir]
                    )
                    assert result.exit_code == 0

    def test_run_persona_task_no_active_persona(self, runner):
        """Test run-persona-task when no persona is active."""
        result = runner.invoke(agent_cmd, ["run-task", "test-task"])
        assert result.exit_code == 1

    def test_run_persona_task_context_file_error(self, runner, tmp_path):
        """Test run-persona-task with invalid context file."""
        with patch("orchestra.cli.commands._active_persona") as mock_active:
            mock_active.identity.id = "test-agent"
            mock_active.identity.name = "Test Agent"
            mock_active.identity.role = "Testing"

            # Create invalid JSON file
            context_file = tmp_path / "invalid.json"
            context_file.write_text("invalid json content")

            result = runner.invoke(
                agent_cmd, ["run-task", "test-task", "--context", str(context_file)]
            )
            assert result.exit_code == 1

    def test_run_persona_task_load_failure(self, runner):
        """Test run-persona-task when task loading fails."""
        with patch("orchestra.cli.commands._active_persona") as mock_active:
            mock_active.identity.id = "test-agent"
            mock_active.identity.name = "Test Agent"
            mock_active.identity.role = "Testing"

            with patch("orchestra.cli.commands.ResourceLoader") as mock_loader_class:
                mock_loader = Mock()
                mock_loader.load_resource.return_value = Mock(
                    success=False, validation_errors=["Task not found"]
                )
                mock_loader_class.return_value = mock_loader

                result = runner.invoke(agent_cmd, ["run-task", "nonexistent-task"])
                assert result.exit_code == 1

    def test_run_persona_task_missing_metadata(self, runner):
        """Test run-persona-task when task metadata is missing."""
        with patch("orchestra.cli.commands._active_persona") as mock_active:
            mock_active.identity.id = "test-agent"
            mock_active.identity.name = "Test Agent"
            mock_active.identity.role = "Testing"

            with patch("orchestra.cli.commands.ResourceLoader") as mock_loader_class:
                mock_loader = Mock()
                mock_loader.load_resource.return_value = Mock(
                    success=True, metadata=None, content="# Test Task"
                )
                mock_loader_class.return_value = mock_loader

                result = runner.invoke(agent_cmd, ["run-task", "test-task"])
                assert result.exit_code == 1

    def test_run_persona_task_execution_failure(self, runner):
        """Test run-persona-task when task execution fails."""
        with patch("orchestra.cli.commands._active_persona") as mock_active:
            mock_active.identity.id = "test-agent"
            mock_active.identity.name = "Test Agent"
            mock_active.identity.role = "Testing"

            with patch("orchestra.cli.commands.ResourceLoader") as mock_loader_class:
                with patch("orchestra.cli.commands.TaskEngine") as mock_engine_class:
                    mock_loader = Mock()
                    mock_loader.load_resource.return_value = Mock(
                        success=True,
                        metadata=Mock(id="test-task"),
                        content="# Test Task",
                    )
                    mock_loader_class.return_value = mock_loader

                    mock_engine = Mock()
                    mock_engine.execute_task.return_value = Mock(
                        success=False, errors=["Task execution failed"]
                    )
                    mock_engine_class.return_value = mock_engine

                    result = runner.invoke(agent_cmd, ["run-task", "test-task"])
                    assert result.exit_code == 1

    def test_run_persona_task_success(self, runner):
        """Test run-persona-task with successful execution."""
        with patch("orchestra.cli.commands._active_persona") as mock_active:
            mock_active.identity.id = "test-agent"
            mock_active.identity.name = "Test Agent"
            mock_active.identity.role = "Testing"

            with patch("orchestra.cli.commands.ResourceLoader") as mock_loader_class:
                with patch("orchestra.cli.commands.TaskEngine") as mock_engine_class:
                    mock_loader = Mock()
                    mock_loader.load_resource.return_value = Mock(
                        success=True,
                        metadata=Mock(id="test-task"),
                        content="# Test Task",
                    )
                    mock_loader_class.return_value = mock_loader

                    mock_engine = Mock()
                    mock_engine.execute_task.return_value = Mock(
                        success=True,
                        execution_time=1.5,
                        steps_completed=2,
                        total_steps=2,
                        warnings=[],
                    )
                    mock_engine_class.return_value = mock_engine

                    result = runner.invoke(agent_cmd, ["run-task", "test-task"])
                    assert result.exit_code == 0

    def test_run_persona_task_exception(self, runner):
        """Test run-persona-task exception handling."""
        with patch("orchestra.cli.commands._active_persona") as mock_active:
            mock_active.identity.id = "test-agent"
            mock_active.identity.name = "Test Agent"
            mock_active.identity.role = "Testing"

            with patch("orchestra.cli.commands.ResourceLoader") as mock_loader_class:
                mock_loader_class.side_effect = Exception("Loader error")

                result = runner.invoke(agent_cmd, ["run-task", "test-task"])
                assert result.exit_code == 1

    def test_render_persona_template_no_active_persona(self, runner):
        """Test render-persona-template when no persona is active."""
        result = runner.invoke(agent_cmd, ["render", "test-template"])
        assert result.exit_code == 1

    def test_render_persona_template_context_file_error(self, runner, tmp_path):
        """Test render-persona-template with invalid context file."""
        with patch("orchestra.cli.commands._active_persona") as mock_active:
            mock_active.identity.id = "test-agent"
            mock_active.identity.name = "Test Agent"
            mock_active.identity.role = "Testing"

            # Create invalid JSON file
            context_file = tmp_path / "invalid.json"
            context_file.write_text("invalid json content")

            result = runner.invoke(
                agent_cmd, ["render", "test-template", "--context", str(context_file)]
            )
            assert result.exit_code == 1

    def test_render_persona_template_load_failure(self, runner):
        """Test render-persona-template when template loading fails."""
        with patch("orchestra.cli.commands._active_persona") as mock_active:
            mock_active.identity.id = "test-agent"
            mock_active.identity.name = "Test Agent"
            mock_active.identity.role = "Testing"

            with patch("orchestra.cli.commands.ResourceLoader") as mock_loader_class:
                mock_loader = Mock()
                mock_loader.load_resource.return_value = Mock(
                    success=False, validation_errors=["Template not found"]
                )
                mock_loader_class.return_value = mock_loader

                result = runner.invoke(agent_cmd, ["render", "nonexistent-template"])
                assert result.exit_code == 1

    def test_render_persona_template_missing_metadata(self, runner):
        """Test render-persona-template when template metadata is missing."""
        with patch("orchestra.cli.commands._active_persona") as mock_active:
            mock_active.identity.id = "test-agent"
            mock_active.identity.name = "Test Agent"
            mock_active.identity.role = "Testing"

            with patch("orchestra.cli.commands.ResourceLoader") as mock_loader_class:
                mock_loader = Mock()
                mock_loader.load_resource.return_value = Mock(
                    success=True, metadata=None, content="# Test Template"
                )
                mock_loader_class.return_value = mock_loader

                result = runner.invoke(agent_cmd, ["render", "test-template"])
                assert result.exit_code == 1

    def test_render_persona_template_rendering_failure(self, runner):
        """Test render-persona-template when template rendering fails."""
        with patch("orchestra.cli.commands._active_persona") as mock_active:
            mock_active.identity.id = "test-agent"
            mock_active.identity.name = "Test Agent"
            mock_active.identity.role = "Testing"

            with patch("orchestra.cli.commands.ResourceLoader") as mock_loader_class:
                with patch(
                    "orchestra.cli.commands.TemplateProcessor"
                ) as mock_processor_class:
                    mock_loader = Mock()
                    mock_loader.load_resource.return_value = Mock(
                        success=True,
                        metadata=Mock(id="test-template"),
                        content="# Test Template",
                    )
                    mock_loader_class.return_value = mock_loader

                    mock_processor = Mock()
                    mock_processor.render_template.return_value = Mock(
                        success=False, errors=["Template rendering failed"]
                    )
                    mock_processor_class.return_value = mock_processor

                    result = runner.invoke(agent_cmd, ["render", "test-template"])
                    assert result.exit_code == 1

    def test_render_persona_template_success(self, runner):
        """Test render-persona-template with successful rendering."""
        with patch("orchestra.cli.commands._active_persona") as mock_active:
            mock_active.identity.id = "test-agent"
            mock_active.identity.name = "Test Agent"
            mock_active.identity.role = "Testing"

            with patch("orchestra.cli.commands.ResourceLoader") as mock_loader_class:
                with patch(
                    "orchestra.cli.commands.TemplateProcessor"
                ) as mock_processor_class:
                    mock_loader = Mock()
                    mock_loader.load_resource.return_value = Mock(
                        success=True,
                        metadata=Mock(id="test-template"),
                        content="# Test Template",
                    )
                    mock_loader_class.return_value = mock_loader

                    mock_processor = Mock()
                    mock_processor.render_template.return_value = Mock(
                        success=True,
                        render_time=0.5,
                        warnings=[],
                        rendered_content="Rendered content",
                    )
                    mock_processor_class.return_value = mock_processor

                    result = runner.invoke(agent_cmd, ["render", "test-template"])
                    assert result.exit_code == 0

    def test_render_persona_template_exception(self, runner):
        """Test render-persona-template exception handling."""
        with patch("orchestra.cli.commands._active_persona") as mock_active:
            mock_active.identity.id = "test-agent"
            mock_active.identity.name = "Test Agent"
            mock_active.identity.role = "Testing"

            with patch("orchestra.cli.commands.ResourceLoader") as mock_loader_class:
                mock_loader_class.side_effect = Exception("Loader error")

                result = runner.invoke(agent_cmd, ["render", "test-template"])
                assert result.exit_code == 1

    def test_execute_persona_checklist_no_active_persona(self, runner):
        """Test execute-persona-checklist when no persona is active."""
        result = runner.invoke(agent_cmd, ["check", "test-checklist"])
        assert result.exit_code == 1

    def test_execute_persona_checklist_context_file_error(self, runner, tmp_path):
        """Test execute-persona-checklist with invalid context file."""
        with patch("orchestra.cli.commands._active_persona") as mock_active:
            mock_active.identity.id = "test-agent"
            mock_active.identity.name = "Test Agent"
            mock_active.identity.role = "Testing"

            # Create invalid JSON file
            context_file = tmp_path / "invalid.json"
            context_file.write_text("invalid json content")

            result = runner.invoke(
                agent_cmd, ["check", "test-checklist", "--context", str(context_file)]
            )
            assert result.exit_code == 1

    def test_execute_persona_checklist_load_failure(self, runner):
        """Test execute-persona-checklist when checklist loading fails."""
        with patch("orchestra.cli.commands._active_persona") as mock_active:
            mock_active.identity.id = "test-agent"
            mock_active.identity.name = "Test Agent"
            mock_active.identity.role = "Testing"

            with patch("orchestra.cli.commands.ResourceLoader") as mock_loader_class:
                mock_loader = Mock()
                mock_loader.load_resource.return_value = Mock(
                    success=False, validation_errors=["Checklist not found"]
                )
                mock_loader_class.return_value = mock_loader

                result = runner.invoke(agent_cmd, ["check", "nonexistent-checklist"])
                assert result.exit_code == 1

    def test_execute_persona_checklist_missing_metadata(self, runner):
        """Test execute-persona-checklist when checklist metadata is missing."""
        with patch("orchestra.cli.commands._active_persona") as mock_active:
            mock_active.identity.id = "test-agent"
            mock_active.identity.name = "Test Agent"
            mock_active.identity.role = "Testing"

            with patch("orchestra.cli.commands.ResourceLoader") as mock_loader_class:
                mock_loader = Mock()
                mock_loader.load_resource.return_value = Mock(
                    success=True, metadata=None, content="# Test Checklist"
                )
                mock_loader_class.return_value = mock_loader

                result = runner.invoke(agent_cmd, ["check", "test-checklist"])
                assert result.exit_code == 1

    def test_execute_persona_checklist_execution_failure(self, runner):
        """Test execute-persona-checklist when checklist execution fails."""
        with patch("orchestra.cli.commands._active_persona") as mock_active:
            mock_active.identity.id = "test-agent"
            mock_active.identity.name = "Test Agent"
            mock_active.identity.role = "Testing"

            with patch("orchestra.cli.commands.ResourceLoader") as mock_loader_class:
                with patch(
                    "orchestra.cli.commands.ChecklistEngine"
                ) as mock_engine_class:
                    mock_loader = Mock()
                    mock_loader.load_resource.return_value = Mock(
                        success=True,
                        metadata=Mock(id="test-checklist"),
                        content="# Test Checklist",
                    )
                    mock_loader_class.return_value = mock_loader

                    mock_engine = Mock()
                    mock_engine.execute_checklist.return_value = Mock(
                        success=False, errors=["Checklist execution failed"]
                    )
                    mock_engine_class.return_value = mock_engine

                    result = runner.invoke(agent_cmd, ["check", "test-checklist"])
                    assert result.exit_code == 1

    def test_execute_persona_checklist_success(self, runner):
        """Test execute-persona-checklist with successful execution."""
        with patch("orchestra.cli.commands._active_persona") as mock_active:
            mock_active.identity.id = "test-agent"
            mock_active.identity.name = "Test Agent"
            mock_active.identity.role = "Testing"

            with patch("orchestra.cli.commands.ResourceLoader") as mock_loader_class:
                with patch(
                    "orchestra.cli.commands.ChecklistEngine"
                ) as mock_engine_class:
                    mock_loader = Mock()
                    mock_loader.load_resource.return_value = Mock(
                        success=True,
                        metadata=Mock(id="test-checklist"),
                        content="# Test Checklist",
                    )
                    mock_loader_class.return_value = mock_loader

                    mock_engine = Mock()
                    mock_engine.execute_checklist.return_value = Mock(
                        success=True,
                        execution_time=2.0,
                        completion_percentage=100.0,
                        completed_items=2,
                        total_items=2,
                        not_applicable_items=0,
                        auto_checked_items=0,
                        warnings=[],
                    )
                    mock_engine_class.return_value = mock_engine

                    result = runner.invoke(agent_cmd, ["check", "test-checklist"])
                    assert result.exit_code == 0

    def test_execute_persona_checklist_exception(self, runner):
        """Test execute-persona-checklist exception handling."""
        with patch("orchestra.cli.commands._active_persona") as mock_active:
            mock_active.identity.id = "test-agent"
            mock_active.identity.name = "Test Agent"
            mock_active.identity.role = "Testing"

            with patch("orchestra.cli.commands.ResourceLoader") as mock_loader_class:
                mock_loader_class.side_effect = Exception("Loader error")

                result = runner.invoke(agent_cmd, ["check", "test-checklist"])
                assert result.exit_code == 1

    def test_list_personas_detailed_output(self, runner, mock_persona_spec):
        """Test list-personas command with detailed output."""
        with patch("orchestra.cli.commands.get_persona_loader") as mock_get_loader:
            mock_loader = Mock()
            mock_loader.discover_personas.return_value = {
                "test-agent": Path("test-agent.yaml"),
            }
            mock_loader.load_persona.return_value = mock_persona_spec
            mock_get_loader.return_value = mock_loader

            result = runner.invoke(agent_cmd, ["list-personas", "--detailed"])
            assert result.exit_code == 0

    def test_list_personas_detailed_load_error(self, runner):
        """Test list-personas command with detailed output when persona load fails."""
        with patch("orchestra.cli.commands.get_persona_loader") as mock_get_loader:
            mock_loader = Mock()
            mock_loader.discover_personas.return_value = {
                "test-agent": Path("test-agent.yaml"),
            }
            mock_loader.load_persona.return_value = None
            mock_get_loader.return_value = mock_loader

            result = runner.invoke(agent_cmd, ["list-personas", "--detailed"])
            assert result.exit_code == 0

    def test_list_personas_bmad_converted_type(self, runner):
        """Test list-personas command with BMad converted persona type detection."""
        with patch("orchestra.cli.commands.get_persona_loader") as mock_get_loader:
            mock_loader = Mock()
            mock_loader.discover_personas.return_value = {
                "dev": Path("bmad/dev.yaml"),
            }
            mock_get_loader.return_value = mock_loader

            result = runner.invoke(agent_cmd, ["list-personas"])
            assert result.exit_code == 0

    def test_list_personas_orchestra_native_type(self, runner):
        """Test list-personas command with Orchestra native persona type detection."""
        with patch("orchestra.cli.commands.get_persona_loader") as mock_get_loader:
            mock_loader = Mock()
            mock_loader.discover_personas.return_value = {
                "dev": Path("orchestra/personas/dev.yaml"),
            }
            mock_get_loader.return_value = mock_loader

            result = runner.invoke(agent_cmd, ["list-personas"])
            assert result.exit_code == 0

    def test_search_personas_by_id(self, runner, mock_persona_spec):
        """Test search-personas command with ID match."""
        with patch("orchestra.cli.commands.get_persona_loader") as mock_get_loader:
            mock_loader = Mock()
            mock_loader.discover_personas.return_value = {
                "test-agent": Path("test-agent.yaml"),
            }
            mock_loader.load_persona.return_value = mock_persona_spec
            mock_get_loader.return_value = mock_loader

            result = runner.invoke(agent_cmd, ["search", "test"])
            assert result.exit_code == 0

    def test_search_personas_by_name(self, runner, mock_persona_spec):
        """Test search-personas command with name match."""
        with patch("orchestra.cli.commands.get_persona_loader") as mock_get_loader:
            mock_loader = Mock()
            mock_loader.discover_personas.return_value = {
                "test-agent": Path("test-agent.yaml"),
            }
            mock_loader.load_persona.return_value = mock_persona_spec
            mock_get_loader.return_value = mock_loader

            result = runner.invoke(agent_cmd, ["search", "Test"])
            assert result.exit_code == 0

    def test_search_personas_by_role(self, runner, mock_persona_spec):
        """Test search-personas command with role match."""
        with patch("orchestra.cli.commands.get_persona_loader") as mock_get_loader:
            mock_loader = Mock()
            mock_loader.discover_personas.return_value = {
                "test-agent": Path("test-agent.yaml"),
            }
            mock_loader.load_persona.return_value = mock_persona_spec
            mock_get_loader.return_value = mock_loader

            result = runner.invoke(agent_cmd, ["search", "Testing"])
            assert result.exit_code == 0

    def test_search_personas_by_principle(self, runner, mock_persona_spec):
        """Test search-personas command with principle match."""
        with patch("orchestra.cli.commands.get_persona_loader") as mock_get_loader:
            mock_loader = Mock()
            mock_loader.discover_personas.return_value = {
                "test-agent": Path("test-agent.yaml"),
            }
            mock_loader.load_persona.return_value = mock_persona_spec
            mock_get_loader.return_value = mock_loader

            result = runner.invoke(agent_cmd, ["search", "thorough"])
            assert result.exit_code == 0

    def test_search_personas_no_matches(self, runner):
        """Test search-personas command with no matches."""
        with patch("orchestra.cli.commands.get_persona_loader") as mock_get_loader:
            mock_loader = Mock()
            mock_loader.discover_personas.return_value = {
                "other-agent": Path("other.yaml"),
            }
            # Mock load_persona to return None for the search test
            mock_loader.load_persona.return_value = None
            mock_get_loader.return_value = mock_loader

            result = runner.invoke(agent_cmd, ["search", "nonexistent"])
            assert result.exit_code == 0

    def test_activate_persona_success(self, runner, mock_persona_spec):
        """Test activate-persona command with successful activation."""
        with patch("orchestra.cli.commands.get_persona_loader") as mock_get_loader:
            mock_loader = Mock()
            mock_loader.load_persona.return_value = mock_persona_spec
            mock_get_loader.return_value = mock_loader

            result = runner.invoke(agent_cmd, ["activate", "test-agent"])
            assert result.exit_code == 0

    def test_activate_persona_with_team_context(self, runner, mock_persona_spec):
        """Test activate-persona command with team context."""
        with patch("orchestra.cli.commands.get_persona_loader") as mock_get_loader:
            mock_loader = Mock()
            mock_loader.load_persona.return_value = mock_persona_spec
            mock_get_loader.return_value = mock_loader

            result = runner.invoke(
                agent_cmd, ["activate", "test-agent", "--team", "backend"]
            )
            assert result.exit_code == 0

    def test_activate_persona_with_project_context(self, runner, mock_persona_spec):
        """Test activate-persona command with project context."""
        with patch("orchestra.cli.commands.get_persona_loader") as mock_get_loader:
            mock_loader = Mock()
            mock_loader.load_persona.return_value = mock_persona_spec
            mock_get_loader.return_value = mock_loader

            result = runner.invoke(
                agent_cmd, ["activate", "test-agent", "--project", "ecommerce"]
            )
            assert result.exit_code == 0

    def test_activate_persona_not_found(self, runner):
        """Test activate-persona command when persona is not found."""
        with patch("orchestra.cli.commands.get_persona_loader") as mock_get_loader:
            mock_loader = Mock()
            mock_loader.load_persona.return_value = None
            mock_loader.discover_personas.return_value = {
                "other-agent": Path("other.yaml")
            }
            mock_get_loader.return_value = mock_loader

            result = runner.invoke(agent_cmd, ["activate", "nonexistent-agent"])
            assert result.exit_code == 1

    def test_current_persona_no_active(self, runner):
        """Test current-persona command when no persona is active."""
        result = runner.invoke(agent_cmd, ["current"])
        assert result.exit_code == 0

    def test_current_persona_active(self, runner):
        """Test current-persona command when persona is active."""
        with patch("orchestra.cli.commands._active_persona") as mock_active:
            mock_active.identity.name = "Test Agent"
            mock_active.identity.id = "test-agent"
            mock_active.identity.role = "Testing"
            mock_active.identity.title = "Test Agent"
            mock_active.identity.icon = "🧪"
            mock_active.identity.when_to_use = "For testing"
            mock_active.identity.style = "Systematic"
            mock_active.identity.focus = "Quality"

            result = runner.invoke(agent_cmd, ["current"])
            assert result.exit_code == 0

    def test_deactivate_persona_no_active(self, runner):
        """Test deactivate-persona command when no persona is active."""
        result = runner.invoke(agent_cmd, ["deactivate"])
        assert result.exit_code == 0

    def test_deactivate_persona_active(self, runner):
        """Test deactivate-persona command when persona is active."""
        with patch("orchestra.cli.commands._active_persona") as mock_active:
            mock_active.identity.name = "Test Agent"

            result = runner.invoke(agent_cmd, ["deactivate"])
            assert result.exit_code == 0

    def test_run_persona_task_with_context_file(self, runner, tmp_path):
        """Test run-persona-task command with context file."""
        context_file = tmp_path / "context.json"
        context_file.write_text('{"project": "test-project", "user": "test-user"}')

        with patch("orchestra.cli.commands._active_persona") as mock_active:
            mock_active.identity.id = "test-agent"
            mock_active.identity.name = "Test Agent"
            mock_active.identity.role = "Testing"

            with patch("orchestra.cli.commands.ResourceLoader") as mock_loader_class:
                with patch("orchestra.cli.commands.TaskEngine") as mock_engine_class:
                    mock_loader = Mock()
                    mock_loader.load_resource.return_value = Mock(
                        success=True,
                        metadata=Mock(id="test-task"),
                        content="# Test Task\n\n## Steps\n- Step 1\n- Step 2",
                    )
                    mock_loader_class.return_value = mock_loader

                    mock_engine = Mock()
                    mock_engine.execute_task.return_value = Mock(
                        success=True,
                        execution_time=1.5,
                        steps_completed=2,
                        total_steps=2,
                        warnings=[],
                        outputs={"result": "success"},
                    )
                    mock_engine_class.return_value = mock_engine

                    result = runner.invoke(
                        agent_cmd,
                        ["run-task", "test-task", "--context", str(context_file)],
                    )
                    assert result.exit_code == 0

    def test_run_persona_task_with_warnings(self, runner):
        """Test run-persona-task command with warnings."""
        with patch("orchestra.cli.commands._active_persona") as mock_active:
            mock_active.identity.id = "test-agent"
            mock_active.identity.name = "Test Agent"
            mock_active.identity.role = "Testing"

            with patch("orchestra.cli.commands.ResourceLoader") as mock_loader_class:
                with patch("orchestra.cli.commands.TaskEngine") as mock_engine_class:
                    mock_loader = Mock()
                    mock_loader.load_resource.return_value = Mock(
                        success=True,
                        metadata=Mock(id="test-task"),
                        content="# Test Task\n\n## Steps\n- Step 1\n- Step 2",
                    )
                    mock_loader_class.return_value = mock_loader

                    mock_engine = Mock()
                    mock_engine.execute_task.return_value = Mock(
                        success=True,
                        execution_time=1.5,
                        steps_completed=2,
                        total_steps=2,
                        warnings=["Step 2 took longer than expected"],
                        outputs={"result": "success"},
                    )
                    mock_engine_class.return_value = mock_engine

                    result = runner.invoke(agent_cmd, ["run-task", "test-task"])
                    assert result.exit_code == 0

    def test_render_persona_template_with_context(self, runner):
        """Test render-persona-template command with context."""
        with patch("orchestra.cli.commands._active_persona") as mock_active:
            mock_active.identity.id = "test-agent"
            mock_active.identity.name = "Test Agent"
            mock_active.identity.role = "Testing"

            with patch("orchestra.cli.commands.ResourceLoader") as mock_loader_class:
                with patch(
                    "orchestra.cli.commands.TemplateProcessor"
                ) as mock_processor_class:
                    mock_loader = Mock()
                    mock_loader.load_resource.return_value = Mock(
                        success=True,
                        metadata=Mock(id="test-template"),
                        content="# Test Template\n\nHello {{name}}!",
                    )
                    mock_loader_class.return_value = mock_loader

                    mock_processor = Mock()
                    mock_processor.render_template.return_value = Mock(
                        success=True,
                        render_time=0.5,
                        warnings=[],
                        rendered_content="Hello World!",
                    )
                    mock_processor_class.return_value = mock_processor

                    result = runner.invoke(
                        agent_cmd,
                        ["render", "test-template", "--context", '{"name": "World"}'],
                    )
                    assert result.exit_code == 0

    def test_render_persona_template_with_output_file(self, runner, tmp_path):
        """Test render-persona-template command with output file."""
        output_file = tmp_path / "output.md"

        with patch("orchestra.cli.commands._active_persona") as mock_active:
            mock_active.identity.id = "test-agent"
            mock_active.identity.name = "Test Agent"
            mock_active.identity.role = "Testing"

            with patch("orchestra.cli.commands.ResourceLoader") as mock_loader_class:
                with patch(
                    "orchestra.cli.commands.TemplateProcessor"
                ) as mock_processor_class:
                    mock_loader = Mock()
                    mock_loader.load_resource.return_value = Mock(
                        success=True,
                        metadata=Mock(id="test-template"),
                        content="# Test Template\n\nHello {{name}}!",
                    )
                    mock_loader_class.return_value = mock_loader

                    mock_processor = Mock()
                    mock_processor.render_template.return_value = Mock(
                        success=True,
                        render_time=0.5,
                        warnings=[],
                        rendered_content="Hello World!",
                    )
                    mock_processor_class.return_value = mock_processor

                    result = runner.invoke(
                        agent_cmd,
                        [
                            "render",
                            "test-template",
                            "--context",
                            '{"name": "World"}',
                            "--output",
                            str(output_file),
                        ],
                    )
                    assert result.exit_code == 0

    def test_render_persona_template_with_warnings(self, runner):
        """Test render-persona-template command with warnings."""
        with patch("orchestra.cli.commands._active_persona") as mock_active:
            mock_active.identity.id = "test-agent"
            mock_active.identity.name = "Test Agent"
            mock_active.identity.role = "Testing"

            with patch("orchestra.cli.commands.ResourceLoader") as mock_loader_class:
                with patch(
                    "orchestra.cli.commands.TemplateProcessor"
                ) as mock_processor_class:
                    mock_loader = Mock()
                    mock_loader.load_resource.return_value = Mock(
                        success=True,
                        metadata=Mock(id="test-template"),
                        content="# Test Template\n\nHello {{name}}!",
                    )
                    mock_loader_class.return_value = mock_loader

                    mock_processor = Mock()
                    mock_processor.render_template.return_value = Mock(
                        success=True,
                        render_time=0.5,
                        warnings=["Variable 'title' not found in context"],
                        rendered_content="Hello World!",
                    )
                    mock_processor_class.return_value = mock_processor

                    result = runner.invoke(
                        agent_cmd,
                        ["render", "test-template", "--context", '{"name": "World"}'],
                    )
                    assert result.exit_code == 0

    def test_execute_persona_checklist_with_context_file(self, runner, tmp_path):
        """Test execute-persona-checklist command with context file."""
        context_file = tmp_path / "context.json"
        context_file.write_text('{"project": "test-project", "user": "test-user"}')

        with patch("orchestra.cli.commands._active_persona") as mock_active:
            mock_active.identity.id = "test-agent"
            mock_active.identity.name = "Test Agent"
            mock_active.identity.role = "Testing"

            with patch("orchestra.cli.commands.ResourceLoader") as mock_loader_class:
                with patch(
                    "orchestra.cli.commands.ChecklistEngine"
                ) as mock_engine_class:
                    mock_loader = Mock()
                    mock_loader.load_resource.return_value = Mock(
                        success=True,
                        metadata=Mock(id="test-checklist"),
                        content="# Test Checklist\n\n- [ ] Item 1\n- [ ] Item 2",
                    )
                    mock_loader_class.return_value = mock_loader

                    mock_engine = Mock()
                    mock_engine.execute_checklist.return_value = Mock(
                        success=True,
                        execution_time=2.0,
                        completion_percentage=100.0,
                        completed_items=2,
                        total_items=2,
                        not_applicable_items=0,
                        auto_checked_items=0,
                        warnings=[],
                    )
                    mock_engine.export_checklist_report.return_value = (
                        "# Checklist Report\n\nAll items completed."
                    )
                    mock_engine_class.return_value = mock_engine

                    result = runner.invoke(
                        agent_cmd,
                        ["check", "test-checklist", "--context", str(context_file)],
                    )
                    assert result.exit_code == 0

    def test_execute_persona_checklist_with_auto_check(self, runner):
        """Test execute-persona-checklist command with auto-check enabled."""
        with patch("orchestra.cli.commands._active_persona") as mock_active:
            mock_active.identity.id = "test-agent"
            mock_active.identity.name = "Test Agent"
            mock_active.identity.role = "Testing"

            with patch("orchestra.cli.commands.ResourceLoader") as mock_loader_class:
                with patch(
                    "orchestra.cli.commands.ChecklistEngine"
                ) as mock_engine_class:
                    mock_loader = Mock()
                    mock_loader.load_resource.return_value = Mock(
                        success=True,
                        metadata=Mock(id="test-checklist"),
                        content="# Test Checklist\n\n- [ ] Item 1\n- [ ] Item 2",
                    )
                    mock_loader_class.return_value = mock_loader

                    mock_engine = Mock()
                    mock_engine.execute_checklist.return_value = Mock(
                        success=True,
                        execution_time=2.0,
                        completion_percentage=100.0,
                        completed_items=2,
                        total_items=2,
                        not_applicable_items=0,
                        auto_checked_items=1,
                        warnings=[],
                    )
                    mock_engine.export_checklist_report.return_value = (
                        "# Checklist Report\n\nAll items completed."
                    )
                    mock_engine_class.return_value = mock_engine

                    result = runner.invoke(
                        agent_cmd, ["check", "test-checklist", "--auto-check"]
                    )
                    assert result.exit_code == 0

    def test_execute_persona_checklist_with_warnings(self, runner):
        """Test execute-persona-checklist command with warnings."""
        with patch("orchestra.cli.commands._active_persona") as mock_active:
            mock_active.identity.id = "test-agent"
            mock_active.identity.name = "Test Agent"
            mock_active.identity.role = "Testing"

            with patch("orchestra.cli.commands.ResourceLoader") as mock_loader_class:
                with patch(
                    "orchestra.cli.commands.ChecklistEngine"
                ) as mock_engine_class:
                    mock_loader = Mock()
                    mock_loader.load_resource.return_value = Mock(
                        success=True,
                        metadata=Mock(id="test-checklist"),
                        content="# Test Checklist\n\n- [ ] Item 1\n- [ ] Item 2",
                    )
                    mock_loader_class.return_value = mock_loader

                    mock_engine = Mock()
                    mock_engine.execute_checklist.return_value = Mock(
                        success=True,
                        execution_time=2.0,
                        completion_percentage=100.0,
                        completed_items=2,
                        total_items=2,
                        not_applicable_items=0,
                        auto_checked_items=0,
                        warnings=["Item 2 was automatically completed"],
                    )
                    mock_engine.export_checklist_report.return_value = (
                        "# Checklist Report\n\nAll items completed."
                    )
                    mock_engine_class.return_value = mock_engine

                    result = runner.invoke(agent_cmd, ["check", "test-checklist"])
                    assert result.exit_code == 0
