"""Tests for agent factory with persona-based agent creation."""

from unittest.mock import Mock, patch

import pytest

# Import the module to ensure it's loaded for coverage
from src.system.agent import UniversalAgent
from src.system.factory import (
    AgentRegistry,
    create_agent,
    get_registry,
    list_personas,
)
from src.system.loader import PersonaLoader
from src.system.specs import PersonaIdentity, PersonaSpec


class TestAgentRegistry:
    """Test AgentRegistry class."""

    @pytest.fixture
    def mock_persona_loader(self):
        """Create a mock PersonaLoader."""
        mock_loader = Mock(spec=PersonaLoader)
        return mock_loader

    @pytest.fixture
    def sample_persona_spec(self):
        """Create a sample PersonaSpec for testing."""
        identity = PersonaIdentity(
            name="Test Developer",
            id="test-dev",
            title="Test Developer",
            role="developer",
        )
        return PersonaSpec(identity=identity)

    @pytest.fixture
    def registry(self, mock_persona_loader):
        """Create an AgentRegistry with mocked dependencies."""
        with patch(
            "src.system.factory.PersonaLoader", return_value=mock_persona_loader
        ):
            return AgentRegistry()

    def test_agent_registry_initialization(self, mock_persona_loader):
        """Test AgentRegistry initialization."""
        with patch(
            "src.system.factory.PersonaLoader", return_value=mock_persona_loader
        ):
            registry = AgentRegistry()

            assert registry._persona_loader == mock_persona_loader

    def test_create_agent_success(
        self, registry, mock_persona_loader, sample_persona_spec
    ):
        """Test successful agent creation."""
        # Setup mock
        mock_persona_loader.load_persona.return_value = sample_persona_spec

        with patch("src.system.factory.UniversalAgent") as mock_universal_agent:
            mock_agent = Mock(spec=UniversalAgent)
            mock_universal_agent.return_value = mock_agent

            # Create agent
            result = registry.create("test-dev")

            # Verify calls
            mock_persona_loader.load_persona.assert_called_once_with("test-dev")
            mock_universal_agent.assert_called_once_with(
                persona_id="test-dev", persona_spec=sample_persona_spec
            )
            assert result == mock_agent

    def test_create_agent_persona_not_found(self, registry, mock_persona_loader):
        """Test agent creation when persona is not found."""
        # Setup mock to return None (persona not found)
        mock_persona_loader.load_persona.return_value = None
        mock_persona_loader.list_personas.return_value = [
            "dev",
            "security-dev",
            "frontend-dev",
        ]

        # Test that ValueError is raised
        with pytest.raises(ValueError) as exc_info:
            registry.create("nonexistent-persona")

        error_message = str(exc_info.value)
        assert "Persona 'nonexistent-persona' not found" in error_message
        assert "Available personas: dev, security-dev, frontend-dev" in error_message

        # Verify calls
        mock_persona_loader.load_persona.assert_called_once_with("nonexistent-persona")
        mock_persona_loader.list_personas.assert_called_once()

    def test_create_agent_empty_persona_spec(self, registry, mock_persona_loader):
        """Test agent creation when persona spec is empty/falsy."""
        # Setup mock to return empty spec
        mock_persona_loader.load_persona.return_value = None
        mock_persona_loader.list_personas.return_value = ["available-persona"]

        with pytest.raises(ValueError) as exc_info:
            registry.create("empty-persona")

        assert "Persona 'empty-persona' not found" in str(exc_info.value)

    def test_list_personas(self, registry, mock_persona_loader):
        """Test listing available personas."""
        expected_personas = ["dev", "security-dev", "frontend-dev", "backend-dev"]
        mock_persona_loader.list_personas.return_value = expected_personas

        result = registry.list_personas()

        assert result == expected_personas
        mock_persona_loader.list_personas.assert_called_once()

    def test_list_personas_empty(self, registry, mock_persona_loader):
        """Test listing personas when none are available."""
        mock_persona_loader.list_personas.return_value = []

        result = registry.list_personas()

        assert result == []
        mock_persona_loader.list_personas.assert_called_once()

    def test_get_persona_spec_found(
        self, registry, mock_persona_loader, sample_persona_spec
    ):
        """Test getting persona spec when it exists."""
        mock_persona_loader.load_persona.return_value = sample_persona_spec

        result = registry.get_persona_spec("test-dev")

        assert result == sample_persona_spec
        mock_persona_loader.load_persona.assert_called_once_with("test-dev")

    def test_get_persona_spec_not_found(self, registry, mock_persona_loader):
        """Test getting persona spec when it doesn't exist."""
        mock_persona_loader.load_persona.return_value = None

        result = registry.get_persona_spec("nonexistent")

        assert result is None
        mock_persona_loader.load_persona.assert_called_once_with("nonexistent")

    def test_reload_personas(self, registry, mock_persona_loader):
        """Test reloading personas from disk."""
        registry.reload_personas()

        mock_persona_loader.reload_all.assert_called_once()

    @patch("src.system.factory.logger")
    def test_create_agent_logging(
        self, mock_logger, registry, mock_persona_loader, sample_persona_spec
    ):
        """Test that agent creation is properly logged."""
        mock_persona_loader.load_persona.return_value = sample_persona_spec

        with patch("src.system.factory.UniversalAgent") as mock_universal_agent:
            mock_agent = Mock(spec=UniversalAgent)
            mock_universal_agent.return_value = mock_agent

            registry.create("test-dev")

            mock_logger.info.assert_called_with(
                f"Creating agent with persona: {sample_persona_spec.display_name}"
            )

    @patch("src.system.factory.logger")
    def test_reload_personas_logging(self, mock_logger, registry, mock_persona_loader):
        """Test that persona reload is properly logged."""
        registry.reload_personas()

        mock_logger.info.assert_called_with("Personas reloaded")


class TestGlobalRegistry:
    """Test global registry functionality."""

    def setup_method(self):
        """Reset global registry before each test."""
        global _global_registry
        _global_registry = None

    def teardown_method(self):
        """Clean up global registry after each test."""
        global _global_registry
        _global_registry = None

    @patch("src.system.factory._global_registry", None)
    @patch("src.system.factory.AgentRegistry")
    @patch("src.system.factory.logger")
    def test_get_registry_first_call(self, mock_logger, mock_agent_registry):
        """Test get_registry creates registry on first call."""
        mock_registry_instance = Mock(spec=AgentRegistry)
        mock_agent_registry.return_value = mock_registry_instance

        result = get_registry()

        assert result == mock_registry_instance
        mock_agent_registry.assert_called_once()
        mock_logger.info.assert_called_with("Agent registry initialized")

    def test_get_registry_subsequent_calls(self):
        """Test get_registry returns same instance on subsequent calls."""
        # First call
        result1 = get_registry()
        # Second call
        result2 = get_registry()

        assert result1 is result2  # Same instance
        assert isinstance(result1, AgentRegistry)

    def test_get_registry_singleton_behavior(self):
        """Test that get_registry implements singleton pattern."""
        registry1 = get_registry()
        registry2 = get_registry()

        assert registry1 is registry2
        assert isinstance(registry1, AgentRegistry)


class TestConvenienceFunctions:
    """Test convenience functions."""

    def setup_method(self):
        """Reset global registry before each test."""
        global _global_registry
        _global_registry = None

    def teardown_method(self):
        """Clean up global registry after each test."""
        global _global_registry
        _global_registry = None

    @patch("src.system.factory.get_registry")
    def test_create_agent_convenience(self, mock_get_registry):
        """Test create_agent convenience function."""
        mock_registry = Mock(spec=AgentRegistry)
        mock_agent = Mock(spec=UniversalAgent)
        mock_registry.create.return_value = mock_agent
        mock_get_registry.return_value = mock_registry

        result = create_agent("test-persona")

        assert result == mock_agent
        mock_get_registry.assert_called_once()
        mock_registry.create.assert_called_once_with("test-persona")

    @patch("src.system.factory.get_registry")
    def test_list_personas_convenience(self, mock_get_registry):
        """Test list_personas convenience function."""
        mock_registry = Mock(spec=AgentRegistry)
        expected_personas = ["dev", "security-dev"]
        mock_registry.list_personas.return_value = expected_personas
        mock_get_registry.return_value = mock_registry

        result = list_personas()

        assert result == expected_personas
        mock_get_registry.assert_called_once()
        mock_registry.list_personas.assert_called_once()

    @patch("src.system.factory.get_registry")
    def test_create_agent_integration_with_registry(self, mock_get_registry):
        """Test create_agent integrates properly with registry."""
        mock_registry = Mock(spec=AgentRegistry)
        mock_agent = Mock(spec=UniversalAgent)
        mock_registry.create.return_value = mock_agent
        mock_get_registry.return_value = mock_registry

        result = create_agent("integration-test")

        assert result == mock_agent
        mock_get_registry.assert_called_once()
        mock_registry.create.assert_called_once_with("integration-test")

    @patch("src.system.factory.get_registry")
    def test_list_personas_integration_with_registry(self, mock_get_registry):
        """Test list_personas integrates properly with registry."""
        mock_registry = Mock(spec=AgentRegistry)
        expected_personas = ["dev", "security-dev", "frontend-dev"]
        mock_registry.list_personas.return_value = expected_personas
        mock_get_registry.return_value = mock_registry

        result = list_personas()

        assert result == expected_personas
        mock_get_registry.assert_called_once()
        mock_registry.list_personas.assert_called_once()


class TestAgentRegistryErrorHandling:
    """Test error handling in AgentRegistry."""

    @pytest.fixture
    def mock_persona_loader(self):
        """Create a mock PersonaLoader."""
        return Mock(spec=PersonaLoader)

    @pytest.fixture
    def registry(self, mock_persona_loader):
        """Create an AgentRegistry with mocked dependencies."""
        with patch(
            "src.system.factory.PersonaLoader", return_value=mock_persona_loader
        ):
            return AgentRegistry()

    def test_create_agent_with_loader_exception(self, registry, mock_persona_loader):
        """Test agent creation when PersonaLoader raises an exception."""
        mock_persona_loader.load_persona.side_effect = Exception("Loader error")

        with pytest.raises(Exception) as exc_info:
            registry.create("test-persona")

        assert "Loader error" in str(exc_info.value)

    def test_create_agent_with_universal_agent_exception(
        self, registry, mock_persona_loader
    ):
        """Test agent creation when UniversalAgent constructor raises an exception."""
        identity = PersonaIdentity(name="Test", id="test", title="Test", role="test")
        persona_spec = PersonaSpec(identity=identity)
        mock_persona_loader.load_persona.return_value = persona_spec

        with patch(
            "src.system.factory.UniversalAgent",
            side_effect=Exception("Agent creation error"),
        ):
            with pytest.raises(Exception) as exc_info:
                registry.create("test-persona")

            assert "Agent creation error" in str(exc_info.value)

    def test_list_personas_with_loader_exception(self, registry, mock_persona_loader):
        """Test list_personas when PersonaLoader raises an exception."""
        mock_persona_loader.list_personas.side_effect = Exception("List error")

        with pytest.raises(Exception) as exc_info:
            registry.list_personas()

        assert "List error" in str(exc_info.value)

    def test_get_persona_spec_with_loader_exception(
        self, registry, mock_persona_loader
    ):
        """Test get_persona_spec when PersonaLoader raises an exception."""
        mock_persona_loader.load_persona.side_effect = Exception("Load error")

        with pytest.raises(Exception) as exc_info:
            registry.get_persona_spec("test")

        assert "Load error" in str(exc_info.value)

    def test_reload_personas_with_loader_exception(self, registry, mock_persona_loader):
        """Test reload_personas when PersonaLoader raises an exception."""
        mock_persona_loader.reload_all.side_effect = Exception("Reload error")

        with pytest.raises(Exception) as exc_info:
            registry.reload_personas()

        assert "Reload error" in str(exc_info.value)


class TestAgentRegistryEdgeCases:
    """Test edge cases for AgentRegistry."""

    @pytest.fixture
    def mock_persona_loader(self):
        """Create a mock PersonaLoader."""
        return Mock(spec=PersonaLoader)

    @pytest.fixture
    def registry(self, mock_persona_loader):
        """Create an AgentRegistry with mocked dependencies."""
        with patch(
            "src.system.factory.PersonaLoader", return_value=mock_persona_loader
        ):
            return AgentRegistry()

    def test_create_agent_with_empty_string_persona_id(
        self, registry, mock_persona_loader
    ):
        """Test creating agent with empty string persona ID."""
        mock_persona_loader.load_persona.return_value = None
        mock_persona_loader.list_personas.return_value = ["valid-persona"]

        with pytest.raises(ValueError) as exc_info:
            registry.create("")

        assert "Persona '' not found" in str(exc_info.value)

    def test_create_agent_with_whitespace_persona_id(
        self, registry, mock_persona_loader
    ):
        """Test creating agent with whitespace-only persona ID."""
        mock_persona_loader.load_persona.return_value = None
        mock_persona_loader.list_personas.return_value = ["valid-persona"]

        with pytest.raises(ValueError) as exc_info:
            registry.create("   ")

        assert "Persona '   ' not found" in str(exc_info.value)

    def test_create_agent_with_special_characters(self, registry, mock_persona_loader):
        """Test creating agent with special characters in persona ID."""
        identity = PersonaIdentity(
            name="Test Dev v1.0",
            id="test-dev@v1.0",
            title="Test Dev v1.0",
            role="developer",
        )
        persona_spec = PersonaSpec(identity=identity)
        mock_persona_loader.load_persona.return_value = persona_spec

        with patch("src.system.factory.UniversalAgent") as mock_universal_agent:
            mock_agent = Mock(spec=UniversalAgent)
            mock_universal_agent.return_value = mock_agent

            result = registry.create("test-dev@v1.0")

            assert result == mock_agent
            mock_universal_agent.assert_called_with(
                persona_id="test-dev@v1.0", persona_spec=persona_spec
            )

    def test_list_personas_large_list(self, registry, mock_persona_loader):
        """Test listing a large number of personas."""
        large_persona_list = [f"persona-{i}" for i in range(1000)]
        mock_persona_loader.list_personas.return_value = large_persona_list

        result = registry.list_personas()

        assert result == large_persona_list
        assert len(result) == 1000

    def test_multiple_registries_independence(self):
        """Test that multiple registry instances are independent."""
        with patch("src.system.factory.PersonaLoader") as mock_loader_class:
            mock_loader1 = Mock(spec=PersonaLoader)
            mock_loader2 = Mock(spec=PersonaLoader)

            # Create two separate registries
            mock_loader_class.side_effect = [mock_loader1, mock_loader2]

            registry1 = AgentRegistry()
            registry2 = AgentRegistry()

            # Verify they use different loaders
            assert registry1._persona_loader == mock_loader1
            assert registry2._persona_loader == mock_loader2
            assert registry1._persona_loader != registry2._persona_loader


class TestFactoryIntegration:
    """Test integration scenarios for the factory."""

    def setup_method(self):
        """Reset global registry before each test."""
        global _global_registry
        _global_registry = None

    def teardown_method(self):
        """Clean up global registry after each test."""
        global _global_registry
        _global_registry = None

    @patch("src.system.factory.get_registry")
    def test_full_agent_creation_workflow(self, mock_get_registry):
        """Test complete agent creation workflow."""
        mock_registry = Mock(spec=AgentRegistry)
        mock_agent = Mock(spec=UniversalAgent)

        # Setup mock registry behavior
        mock_registry.list_personas.return_value = ["workflow-test", "other-persona"]
        mock_registry.create.return_value = mock_agent
        mock_get_registry.return_value = mock_registry

        # Test workflow: list -> create -> verify
        available_personas = list_personas()
        assert "workflow-test" in available_personas

        created_agent = create_agent("workflow-test")
        assert created_agent == mock_agent

        # Verify all expected calls were made
        assert mock_get_registry.call_count == 2  # Called for both list and create
        mock_registry.list_personas.assert_called_once()
        mock_registry.create.assert_called_once_with("workflow-test")

    def test_registry_persistence_across_calls(self):
        """Test that registry state persists across multiple calls."""
        # First call - should create registry
        registry1 = get_registry()

        # Second call - should return same registry
        registry2 = get_registry()

        assert registry1 is registry2
        assert isinstance(registry1, AgentRegistry)

    @patch("src.system.factory.get_registry")
    def test_error_propagation_through_convenience_functions(self, mock_get_registry):
        """Test that errors propagate properly through convenience functions."""
        mock_registry = Mock(spec=AgentRegistry)
        mock_registry.create.side_effect = ValueError("Persona 'nonexistent' not found")
        mock_get_registry.return_value = mock_registry

        # Test error propagation
        with pytest.raises(ValueError) as exc_info:
            create_agent("nonexistent")

        assert "Persona 'nonexistent' not found" in str(exc_info.value)
        mock_get_registry.assert_called_once()
        mock_registry.create.assert_called_once_with("nonexistent")
