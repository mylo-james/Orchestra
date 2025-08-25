"""Tests for UniversalAgent in system module."""

from unittest.mock import Mock, patch

import pytest

# Import the module to ensure it's loaded for coverage
from orchestra.system.agent import UniversalAgent
from orchestra.system.specs import (
    BehavioralContract,
    CommandInterface,
    PersonaIdentity,
    PersonaSpec,
    ResourceDependencies,
)


class TestUniversalAgent:
    """Test UniversalAgent functionality."""

    @pytest.fixture
    def mock_persona_spec(self):
        """Create a mock persona specification."""
        spec = Mock(spec=PersonaSpec)
        spec.identity = Mock(spec=PersonaIdentity)
        spec.identity.role = "Test Role"
        spec.identity.style = "Test Style"
        spec.identity.focus = "Test Focus"
        spec.identity.name = "Test Agent"
        spec.identity.title = "Test Title"
        spec.identity.when_to_use = "Testing scenarios"

        spec.behavioral_contract = Mock(spec=BehavioralContract)
        spec.behavioral_contract.core_principles = [
            "Test Principle 1",
            "Test Principle 2",
        ]
        spec.behavioral_contract.halt_conditions = [
            "Security validation failures",
            "Ambiguous requirements",
        ]
        spec.behavioral_contract.interaction_style = "Professional"

        spec.command_interface = Mock(spec=CommandInterface)
        spec.command_interface.execution_model = "sequential"
        spec.command_interface.commands = {"test_command": Mock(), "analyze": Mock()}

        spec.resource_dependencies = Mock(spec=ResourceDependencies)
        spec.resource_dependencies.tools = [
            "github-tools"
        ]  # This list is already iterable

        spec.display_name = "Test Agent"
        spec.get_command.return_value = Mock()

        return spec

    @pytest.fixture
    def universal_agent(self, mock_persona_spec):
        """Create a UniversalAgent instance for testing."""
        with patch("orchestra.system.agent.PersonaLoader"):
            agent = UniversalAgent(persona_spec=mock_persona_spec)
            return agent

    def test_initialization_with_persona_spec(self, mock_persona_spec):
        """Test UniversalAgent initialization with provided persona spec."""
        with patch("orchestra.system.agent.PersonaLoader"):
            agent = UniversalAgent(persona_spec=mock_persona_spec)

            assert agent.persona_spec == mock_persona_spec
            assert agent.persona_id == "orchestrator"  # default
            assert agent.agent_name == "universal_orchestrator"
            assert agent.agent_role == "Test Role"
            assert agent.agent_style == "Test Style"
            assert agent.agent_focus == "Test Focus"

    def test_initialization_with_persona_id(self, mock_persona_spec):
        """Test UniversalAgent initialization with persona ID."""
        mock_loader = Mock()
        mock_loader.load_persona.return_value = mock_persona_spec

        with patch("orchestra.system.agent.PersonaLoader", return_value=mock_loader):
            agent = UniversalAgent(persona_id="test-persona")

            mock_loader.load_persona.assert_called_once_with("test-persona")
            assert agent.persona_spec == mock_persona_spec

    def test_initialization_fails_with_invalid_persona(self):
        """Test UniversalAgent initialization fails with invalid persona."""
        mock_loader = Mock()
        mock_loader.load_persona.return_value = None

        with patch("orchestra.system.agent.PersonaLoader", return_value=mock_loader):
            with pytest.raises(
                ValueError, match="Failed to load persona: invalid-persona"
            ):
                UniversalAgent(persona_id="invalid-persona")

    def test_configure_from_persona(self, universal_agent, mock_persona_spec):
        """Test agent configuration from persona specification."""
        # Configuration should be done in __init__, verify it was applied
        assert universal_agent.agent_role == mock_persona_spec.identity.role
        assert universal_agent.agent_style == mock_persona_spec.identity.style
        assert universal_agent.agent_focus == mock_persona_spec.identity.focus
        assert (
            universal_agent.core_principles
            == mock_persona_spec.behavioral_contract.core_principles
        )
        assert (
            universal_agent.halt_conditions
            == mock_persona_spec.behavioral_contract.halt_conditions
        )
        assert (
            universal_agent.interaction_style
            == mock_persona_spec.behavioral_contract.interaction_style
        )
        assert (
            universal_agent.execution_model
            == mock_persona_spec.command_interface.execution_model
        )

    def test_load_persona_tools(self, universal_agent):
        """Test loading of persona tools."""
        # Tools should be loaded during initialization
        assert len(universal_agent.tools) > 0

    def test_resolve_tool_github_tools(self, universal_agent):
        """Test tool resolution for github-tools."""
        tool = universal_agent._resolve_tool("github-tools")
        assert tool is not None

    def test_resolve_tool_create_pr(self, universal_agent):
        """Test tool resolution for create-pr."""
        tool = universal_agent._resolve_tool("create-pr")
        assert tool is not None

    def test_resolve_tool_list_repos(self, universal_agent):
        """Test tool resolution for list-repos."""
        tool = universal_agent._resolve_tool("list-repos")
        assert tool is not None

    def test_resolve_tool_unknown(self, universal_agent):
        """Test tool resolution for unknown tool."""
        tool = universal_agent._resolve_tool("unknown-tool")
        assert tool is None

    @pytest.mark.asyncio
    async def test_execute_command_success(self, universal_agent, mock_persona_spec):
        """Test successful command execution."""
        mock_command = Mock()
        mock_command.requires_confirmation = False
        mock_command.timeout_seconds = 30
        mock_command.execution_pattern = (
            "analyze → execute → report"  # Make it a splittable string
        )
        mock_persona_spec.get_command.return_value = mock_command

        result = await universal_agent.execute_command("test_command")

        assert result["success"] is True
        assert result["command"] == "test_command"
        assert result["persona"] == "orchestrator"

    @pytest.mark.asyncio
    async def test_execute_command_not_found(self, universal_agent, mock_persona_spec):
        """Test command execution when command not found."""
        mock_persona_spec.get_command.return_value = None

        result = await universal_agent.execute_command("nonexistent_command")

        assert result["success"] is False
        assert "Command not found" in result["error"]
        assert "available_commands" in result

    @pytest.mark.asyncio
    async def test_execute_command_with_confirmation(
        self, universal_agent, mock_persona_spec
    ):
        """Test command execution with confirmation required."""
        mock_command = Mock()
        mock_command.requires_confirmation = True
        mock_command.timeout_seconds = 30
        mock_command.execution_pattern = (
            "validate → confirm → execute → report"  # Make it a splittable string
        )
        mock_persona_spec.get_command.return_value = mock_command

        result = await universal_agent.execute_command("test_command")

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_execute_command_timeout(self, universal_agent, mock_persona_spec):
        """Test command execution timeout handling."""
        mock_command = Mock()
        mock_command.requires_confirmation = False
        mock_command.timeout_seconds = 1
        mock_persona_spec.get_command.return_value = mock_command

        # Mock the execution to timeout
        import asyncio

        with patch.object(
            universal_agent, "_execute_pattern", side_effect=asyncio.TimeoutError()
        ):
            result = await universal_agent.execute_command("test_command")

            assert result["success"] is False
            assert "timed out" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_command_exception(self, universal_agent, mock_persona_spec):
        """Test command execution exception handling."""
        mock_command = Mock()
        mock_command.requires_confirmation = False
        mock_command.timeout_seconds = 30
        mock_persona_spec.get_command.return_value = mock_command

        # Mock the execution to raise an exception
        with patch.object(
            universal_agent, "_execute_pattern", side_effect=Exception("Test error")
        ):
            result = await universal_agent.execute_command("test_command")

            assert result["success"] is False
            assert "Test error" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_pattern_sequential(self, universal_agent):
        """Test sequential execution pattern."""
        mock_command = Mock()
        mock_command.execution_pattern = "read_story → implement → test"

        result = await universal_agent._execute_pattern(mock_command, {})

        assert isinstance(result, list)
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_execute_step_read_story(self, universal_agent):
        """Test read_story step execution."""
        result = await universal_agent._execute_step("read_story", {"file": "test.md"})

        assert result["action"] == "read_story"
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_execute_step_implement(self, universal_agent):
        """Test implement step execution."""
        result = await universal_agent._execute_step(
            "implement", {"requirements": "test"}
        )

        assert result["action"] == "implement"
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_execute_step_test(self, universal_agent):
        """Test test step execution."""
        result = await universal_agent._execute_step("test", {"test_suite": "unit"})

        assert result["action"] == "test"
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_execute_step_unknown(self, universal_agent):
        """Test unknown step execution."""
        result = await universal_agent._execute_step("unknown_step", {"param": "value"})

        assert result["step"] == "unknown_step"
        assert result["status"] == "completed"

    def test_should_halt_security_failure(self, universal_agent):
        """Test halt condition for security validation failures."""
        result = {"security_failed": True}

        assert universal_agent._should_halt(result) is True

    def test_should_halt_ambiguous_requirements(self, universal_agent):
        """Test halt condition for ambiguous requirements."""
        result = {"ambiguous": True}

        assert universal_agent._should_halt(result) is True

    def test_should_halt_no_conditions(self, universal_agent):
        """Test halt condition when no conditions are met."""
        result = {"normal": True}

        assert universal_agent._should_halt(result) is False

    def test_should_halt_no_halt_conditions(self, universal_agent):
        """Test halt condition when no halt conditions are defined."""
        universal_agent.halt_conditions = None

        result = {"any": True}

        assert universal_agent._should_halt(result) is False

    def test_get_system_prompt(self, universal_agent, mock_persona_spec):
        """Test system prompt generation."""
        prompt = universal_agent.get_system_prompt()

        assert "Test Agent" in prompt
        assert "Test Role" in prompt
        assert "Test Style" in prompt
        assert "Test Focus" in prompt
        assert "Test Principle 1" in prompt
        assert "Test Principle 2" in prompt
        assert "Testing scenarios" in prompt

    def test_get_available_commands(self, universal_agent, mock_persona_spec):
        """Test getting available commands."""
        commands = universal_agent.get_available_commands()

        assert "test_command" in commands
        assert "analyze" in commands

    def test_describe(self, universal_agent, mock_persona_spec):
        """Test agent description."""
        description = universal_agent.describe()

        assert "Test Agent" in description
        assert "Test Role" in description
        assert "test_command" in description
        assert "analyze" in description
        assert "github-tools" in description
        assert "sequential" in description

    @pytest.mark.asyncio
    async def test_placeholder_methods(self, universal_agent):
        """Test placeholder method implementations."""
        # Test all placeholder methods return expected structure
        methods = [
            universal_agent._read_story,
            universal_agent._implement_code,
            universal_agent._run_tests,
            universal_agent._validate_output,
            universal_agent._create_plan,
            universal_agent._analyze_request,
        ]

        for method in methods:
            result = await method({"test": "param"})
            assert isinstance(result, dict)
            assert "action" in result
            assert "status" in result
            assert result["status"] == "completed"
