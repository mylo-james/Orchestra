"""Tests for persona loader system."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest
import yaml

# Import the module to ensure it's loaded for coverage
from orchestra.system.loader import PersonaLoader
from orchestra.system.specs import PersonaSpec


class TestPersonaLoader:
    """Test PersonaLoader class."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def sample_persona_yaml(self):
        """Create sample persona YAML data."""
        return {
            "identity": {
                "name": "Test Developer",
                "id": "test-dev",
                "title": "Test Developer Agent",
                "role": "developer",
                "icon": "👨‍💻",
                "when_to_use": "For testing purposes",
                "style": "professional",
                "focus": "code quality",
            },
            "behavioral_contract": {
                "core_principles": ["Write clean code", "Test everything"],
                "interaction_style": "helpful",
                "halt_conditions": ["syntax error", "security issue"],
                "decision_framework": "test-driven",
                "escalation_triggers": ["critical bug"],
            },
            "command_interface": {
                "execution_model": "sequential",
                "commands": {
                    "code": {
                        "description": "Generate code",
                        "execution_pattern": "analyze -> code -> test",
                        "parameters": {"language": "python"},
                        "requires_confirmation": False,
                        "timeout_seconds": 120,
                    }
                },
                "default_command": "code",
                "command_aliases": {"c": "code"},
            },
            "resource_dependencies": {
                "knowledge_sources": ["python-docs"],
                "tasks": ["code-generation"],
                "tools": ["pytest", "black"],
                "templates": ["python-class"],
                "required_services": ["github"],
            },
            "knowledge_context": {
                "domains": ["software-development"],
                "expertise_areas": ["python", "testing"],
                "learning_sources": ["documentation"],
                "context_window_size": 8192,
                "memory_retention_policy": "persistent",
            },
            "version": "1.2.0",
            "created_by": "test-user",
            "last_modified": "2024-01-01",
            "tags": ["developer", "python"],
            "enabled": True,
            "experimental": False,
            "deprecated": False,
        }

    @pytest.fixture
    def minimal_persona_yaml(self):
        """Create minimal persona YAML data."""
        return {
            "identity": {
                "name": "Minimal Agent",
                "id": "minimal",
                "title": "Minimal Agent",
                "role": "basic",
            }
        }

    def test_persona_loader_initialization_default(self):
        """Test PersonaLoader initialization with defaults."""
        loader = PersonaLoader()

        assert loader.cache_enabled is True
        assert loader._cache == {}
        assert loader._persona_paths == {}
        assert len(loader.search_paths) == 2
        assert Path("orchestra/personas") in loader.search_paths
        assert Path(".bmad-core/personas") in loader.search_paths

    def test_persona_loader_initialization_custom(self):
        """Test PersonaLoader initialization with custom settings."""
        loader = PersonaLoader(cache_enabled=False)

        assert loader.cache_enabled is False
        assert loader._cache == {}
        assert loader._persona_paths == {}

    def test_discover_personas_empty_paths(self):
        """Test persona discovery when no paths exist."""
        loader = PersonaLoader()

        with patch.object(Path, "exists", return_value=False):
            discovered = loader.discover_personas()

            assert discovered == {}
            assert loader._persona_paths == {}

    def test_discover_personas_with_files(self, temp_dir):
        """Test persona discovery with actual files."""
        # Create test directories
        orchestra_personas = temp_dir / "orchestra" / "personas"
        bmad_personas = temp_dir / ".bmad-core" / "personas"
        orchestra_personas.mkdir(parents=True)
        bmad_personas.mkdir(parents=True)

        # Create test files
        (orchestra_personas / "dev.yaml").touch()
        (orchestra_personas / "security-dev.yaml").touch()
        (bmad_personas / "frontend-dev.yaml").touch()
        (bmad_personas / "dev.yaml").touch()  # Should be overridden by orchestra

        # Mock search paths
        loader = PersonaLoader()
        loader.search_paths = [
            temp_dir / "orchestra" / "personas",
            temp_dir / ".bmad-core" / "personas",
        ]

        discovered = loader.discover_personas()

        # Should have 3 unique personas (orchestra/dev.yaml overrides bmad/dev.yaml)
        assert len(discovered) == 3
        assert "dev" in discovered
        assert "security-dev" in discovered
        assert "frontend-dev" in discovered

        # Verify precedence - orchestra should override bmad
        assert discovered["dev"] == orchestra_personas / "dev.yaml"
        assert discovered["security-dev"] == orchestra_personas / "security-dev.yaml"
        assert discovered["frontend-dev"] == bmad_personas / "frontend-dev.yaml"

    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_load_persona_success(self, mock_yaml_load, mock_file, sample_persona_yaml):
        """Test successful persona loading."""
        mock_yaml_load.return_value = sample_persona_yaml

        loader = PersonaLoader()
        loader._persona_paths = {"test-dev": Path("test-dev.yaml")}

        persona = loader.load_persona("test-dev")

        assert persona is not None
        assert isinstance(persona, PersonaSpec)
        assert persona.identity.name == "Test Developer"
        assert persona.identity.id == "test-dev"
        assert persona.version == "1.2.0"
        assert len(persona.behavioral_contract.core_principles) == 2
        assert "code" in persona.command_interface.commands

        # Verify caching
        assert "base:test-dev" in loader._cache  # Cache keys now include context
        assert loader._cache["base:test-dev"] == persona

    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_load_persona_from_cache(
        self, mock_yaml_load, mock_file, sample_persona_yaml
    ):
        """Test loading persona from cache."""
        mock_yaml_load.return_value = sample_persona_yaml

        loader = PersonaLoader()
        loader._persona_paths = {"test-dev": Path("test-dev.yaml")}

        # First load
        persona1 = loader.load_persona("test-dev")

        # Second load should come from cache
        persona2 = loader.load_persona("test-dev")

        assert persona1 is persona2
        # YAML should only be loaded once
        mock_yaml_load.assert_called_once()

    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_load_persona_force_reload(
        self, mock_yaml_load, mock_file, sample_persona_yaml
    ):
        """Test force reload bypasses cache."""
        mock_yaml_load.return_value = sample_persona_yaml

        loader = PersonaLoader()
        loader._persona_paths = {"test-dev": Path("test-dev.yaml")}

        # First load
        persona1 = loader.load_persona("test-dev")

        # Force reload should bypass cache
        persona2 = loader.load_persona("test-dev", force_reload=True)

        assert persona1 is not persona2  # Different instances
        assert persona1.identity.name == persona2.identity.name  # Same data
        # YAML should be loaded twice
        assert mock_yaml_load.call_count == 2

    def test_load_persona_not_found(self):
        """Test loading non-existent persona."""
        loader = PersonaLoader()
        loader._persona_paths = {}

        persona = loader.load_persona("nonexistent")

        assert persona is None

    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_load_persona_yaml_error(self, mock_yaml_load, mock_file):
        """Test handling YAML parsing errors."""
        mock_yaml_load.side_effect = yaml.YAMLError("Invalid YAML")

        loader = PersonaLoader()
        loader._persona_paths = {"bad-yaml": Path("bad-yaml.yaml")}

        persona = loader.load_persona("bad-yaml")

        assert persona is None

    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_load_persona_validation_error(self, mock_yaml_load, mock_file):
        """Test handling persona validation errors."""
        # Invalid persona data (missing required fields)
        invalid_data = {"identity": {}}
        mock_yaml_load.return_value = invalid_data

        loader = PersonaLoader()
        loader._persona_paths = {"invalid": Path("invalid.yaml")}

        persona = loader.load_persona("invalid")

        assert persona is None

    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_load_persona_file_error(self, mock_yaml_load, mock_file):
        """Test handling file reading errors."""
        mock_file.side_effect = IOError("File not found")

        loader = PersonaLoader()
        loader._persona_paths = {"missing": Path("missing.yaml")}

        persona = loader.load_persona("missing")

        assert persona is None

    def test_load_persona_cache_disabled(self):
        """Test loading with cache disabled."""
        loader = PersonaLoader(cache_enabled=False)

        # Valid persona data with core principles
        valid_data = {
            "identity": {"name": "Test", "id": "test", "title": "Test", "role": "test"},
            "behavioral_contract": {"core_principles": ["Test principle"]},
        }

        with patch.object(loader, "_persona_paths", {"test": Path("test.yaml")}):
            with patch("builtins.open", mock_open()):
                with patch("yaml.safe_load", return_value=valid_data):
                    persona = loader.load_persona("test")

                    assert persona is not None
                    # Should not be cached
                    assert "test" not in loader._cache

    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_parse_persona_data_complete(
        self, mock_yaml_load, mock_file, sample_persona_yaml
    ):
        """Test parsing complete persona data."""
        loader = PersonaLoader()

        persona = loader._parse_persona_data(sample_persona_yaml, "test-dev")

        # Verify identity
        assert persona.identity.name == "Test Developer"
        assert persona.identity.id == "test-dev"
        assert persona.identity.icon == "👨‍💻"

        # Verify behavioral contract
        assert len(persona.behavioral_contract.core_principles) == 2
        assert persona.behavioral_contract.interaction_style == "helpful"

        # Verify command interface
        assert persona.command_interface.execution_model == "sequential"
        assert "code" in persona.command_interface.commands
        assert persona.command_interface.default_command == "code"

        # Verify resource dependencies
        assert "python-docs" in persona.resource_dependencies.knowledge_sources
        assert "pytest" in persona.resource_dependencies.tools

        # Verify knowledge context
        assert persona.knowledge_context is not None
        assert "python" in persona.knowledge_context.expertise_areas
        assert persona.knowledge_context.context_window_size == 8192

        # Verify metadata
        assert persona.version == "1.2.0"
        assert persona.created_by == "test-user"
        assert "python" in persona.tags

    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_parse_persona_data_minimal(
        self, mock_yaml_load, mock_file, minimal_persona_yaml
    ):
        """Test parsing minimal persona data with defaults."""
        loader = PersonaLoader()

        persona = loader._parse_persona_data(minimal_persona_yaml, "minimal")

        # Verify identity with defaults
        assert persona.identity.name == "Minimal Agent"
        assert persona.identity.id == "minimal"
        assert persona.identity.icon == "🤖"  # Default

        # Verify defaults
        assert persona.behavioral_contract.core_principles == []
        assert persona.behavioral_contract.interaction_style == "conversational"
        assert persona.command_interface.execution_model == "sequential"
        assert persona.command_interface.commands == {}
        assert persona.resource_dependencies.tools == []
        assert persona.knowledge_context is None
        assert persona.version == "1.0.0"  # Default
        assert persona.enabled is True  # Default

    def test_parse_persona_data_command_parsing(self):
        """Test parsing command definitions."""
        data = {
            "identity": {"name": "Test", "id": "test", "title": "Test", "role": "test"},
            "command_interface": {
                "commands": {
                    "simple_cmd": "simple string",  # Should be ignored
                    "complex_cmd": {
                        "description": "Complex command",
                        "execution_pattern": "step1 -> step2",
                        "parameters": {"param1": "value1"},
                        "requires_confirmation": True,
                        "timeout_seconds": 300,
                    },
                }
            },
        }

        loader = PersonaLoader()
        persona = loader._parse_persona_data(data, "test")

        # Simple command should be ignored
        assert "simple_cmd" not in persona.command_interface.commands

        # Complex command should be parsed
        assert "complex_cmd" in persona.command_interface.commands
        cmd = persona.command_interface.commands["complex_cmd"]
        assert cmd.description == "Complex command"
        assert cmd.requires_confirmation is True
        assert cmd.timeout_seconds == 300

    def test_list_personas_empty(self):
        """Test listing personas when none exist."""
        loader = PersonaLoader()

        with patch.object(loader, "discover_personas", return_value={}):
            personas = loader.list_personas()

            assert personas == []

    def test_list_personas_with_data(self):
        """Test listing personas with data."""
        loader = PersonaLoader()
        loader._persona_paths = {
            "dev": Path("dev.yaml"),
            "security-dev": Path("security-dev.yaml"),
            "frontend-dev": Path("frontend-dev.yaml"),
        }

        personas = loader.list_personas()

        assert len(personas) == 3
        assert "dev" in personas
        assert "security-dev" in personas
        assert "frontend-dev" in personas

    def test_list_personas_auto_discover(self):
        """Test that list_personas triggers discovery if needed."""
        loader = PersonaLoader()

        # Mock the discovery to return specific personas and set the internal state
        def mock_discover():
            loader._persona_paths = {"test": Path("test.yaml")}
            return {"test": Path("test.yaml")}

        with patch.object(
            loader, "discover_personas", side_effect=mock_discover
        ) as mock_discover:
            personas = loader.list_personas()

            mock_discover.assert_called_once()
            assert personas == ["test"]

    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_validate_persona_file_valid(
        self, mock_yaml_load, mock_file, sample_persona_yaml
    ):
        """Test validating a valid persona file."""
        mock_yaml_load.return_value = sample_persona_yaml

        loader = PersonaLoader()
        errors = loader.validate_persona_file(Path("test.yaml"))

        assert errors == []

    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_validate_persona_file_invalid(self, mock_yaml_load, mock_file):
        """Test validating an invalid persona file."""
        # Invalid data - missing required fields
        invalid_data = {"identity": {}}
        mock_yaml_load.return_value = invalid_data

        loader = PersonaLoader()
        errors = loader.validate_persona_file(Path("invalid.yaml"))

        assert len(errors) > 0
        # Check for actual validation errors from PersonaSpec.validate()
        assert any(
            "Missing persona name" in error or "No core principles defined" in error
            for error in errors
        )

    @patch("builtins.open", new_callable=mock_open)
    def test_validate_persona_file_yaml_error(self, mock_file):
        """Test validating file with YAML errors."""
        mock_file.side_effect = yaml.YAMLError("Invalid YAML")

        loader = PersonaLoader()
        errors = loader.validate_persona_file(Path("bad.yaml"))

        assert len(errors) == 1
        assert "YAML parsing error" in errors[0]

    @patch("builtins.open", new_callable=mock_open)
    def test_validate_persona_file_general_error(self, mock_file):
        """Test validating file with general errors."""
        mock_file.side_effect = Exception("General error")

        loader = PersonaLoader()
        errors = loader.validate_persona_file(Path("error.yaml"))

        assert len(errors) == 1
        assert "Validation error" in errors[0]

    def test_clear_cache(self):
        """Test clearing the persona cache."""
        loader = PersonaLoader()
        loader._cache = {"test": Mock()}

        loader.clear_cache()

        assert loader._cache == {}

    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_reload_all_success(self, mock_yaml_load, mock_file, sample_persona_yaml):
        """Test reloading all personas successfully."""
        mock_yaml_load.return_value = sample_persona_yaml

        loader = PersonaLoader()
        loader._persona_paths = {
            "dev": Path("dev.yaml"),
            "security-dev": Path("security-dev.yaml"),
        }

        # Pre-populate cache
        loader._cache = {"old": Mock()}

        # Mock discover_personas to avoid finding real files
        with patch.object(
            loader, "discover_personas", return_value=loader._persona_paths
        ):
            loaded = loader.reload_all()

        # Cache should be cleared
        assert "old" not in loader._cache

        # Should have loaded 2 personas
        assert len(loaded) == 2
        assert "dev" in loaded
        assert "security-dev" in loaded

        # All loaded personas should be PersonaSpec instances
        for persona in loaded.values():
            assert isinstance(persona, PersonaSpec)

    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_reload_all_with_failures(self, mock_yaml_load, mock_file):
        """Test reloading all personas with some failures."""
        # First call succeeds, second fails
        mock_yaml_load.side_effect = [
            {
                "identity": {
                    "name": "Good",
                    "id": "good",
                    "title": "Good",
                    "role": "good",
                },
                "behavioral_contract": {"core_principles": ["Good principle"]},
            },
            yaml.YAMLError("Bad YAML"),
        ]

        loader = PersonaLoader()
        loader._persona_paths = {"good": Path("good.yaml"), "bad": Path("bad.yaml")}

        # Mock discover_personas to avoid finding real files
        with patch.object(
            loader, "discover_personas", return_value=loader._persona_paths
        ):
            loaded = loader.reload_all()

        # Should only have the successful one
        assert len(loaded) == 1
        assert "good" in loaded
        assert "bad" not in loaded

    def test_reload_all_empty(self):
        """Test reloading when no personas exist."""
        loader = PersonaLoader()
        loader._persona_paths = {}

        # Mock discover_personas to avoid finding real files
        with patch.object(loader, "discover_personas", return_value={}):
            loaded = loader.reload_all()

        assert loaded == {}


class TestPersonaLoaderIntegration:
    """Test PersonaLoader integration scenarios."""

    @pytest.fixture
    def temp_persona_structure(self):
        """Create a temporary persona directory structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)

            # Create directory structure
            orchestra_personas = base_path / "orchestra" / "personas"
            bmad_personas = base_path / ".bmad-core" / "personas"
            orchestra_personas.mkdir(parents=True)
            bmad_personas.mkdir(parents=True)

            # Create persona files
            dev_persona = {
                "identity": {
                    "name": "Developer",
                    "id": "dev",
                    "title": "Software Developer",
                    "role": "developer",
                },
                "behavioral_contract": {"core_principles": ["Clean code", "Testing"]},
            }

            security_persona = {
                "identity": {
                    "name": "Security Developer",
                    "id": "security-dev",
                    "title": "Security-Focused Developer",
                    "role": "security-developer",
                },
                "behavioral_contract": {
                    "core_principles": ["Security first", "Threat modeling"]
                },
            }

            override_persona = {
                "identity": {
                    "name": "Override Developer",
                    "id": "dev",
                    "title": "Override Developer",
                    "role": "override-developer",
                },
                "behavioral_contract": {"core_principles": ["Override principles"]},
            }

            # Write files
            with open(orchestra_personas / "dev.yaml", "w") as f:
                yaml.dump(override_persona, f)

            with open(orchestra_personas / "security-dev.yaml", "w") as f:
                yaml.dump(security_persona, f)

            with open(bmad_personas / "dev.yaml", "w") as f:
                yaml.dump(dev_persona, f)

            yield base_path, orchestra_personas, bmad_personas

    def test_precedence_system(self, temp_persona_structure):
        """Test that precedence system works correctly."""
        base_path, orchestra_personas, bmad_personas = temp_persona_structure

        loader = PersonaLoader()
        loader.search_paths = [
            base_path / "orchestra" / "personas",
            base_path / ".bmad-core" / "personas",
        ]

        # Discover personas
        discovered = loader.discover_personas()

        # Should find both personas
        assert len(discovered) == 2
        assert "dev" in discovered
        assert "security-dev" in discovered

        # dev should come from orchestra (override)
        assert discovered["dev"] == orchestra_personas / "dev.yaml"
        # security-dev should come from orchestra
        assert discovered["security-dev"] == orchestra_personas / "security-dev.yaml"

        # Load the overridden persona
        dev_persona = loader.load_persona("dev")
        assert dev_persona is not None
        assert dev_persona.identity.name == "Override Developer"
        assert "Override principles" in dev_persona.behavioral_contract.core_principles

    def test_full_workflow(self, temp_persona_structure):
        """Test complete workflow: discover -> list -> load -> validate."""
        base_path, orchestra_personas, bmad_personas = temp_persona_structure

        loader = PersonaLoader()
        loader.search_paths = [
            base_path / "orchestra" / "personas",
            base_path / ".bmad-core" / "personas",
        ]

        # 1. List personas (triggers discovery)
        personas = loader.list_personas()
        assert len(personas) == 2
        assert "dev" in personas
        assert "security-dev" in personas

        # 2. Load each persona
        dev_persona = loader.load_persona("dev")
        security_persona = loader.load_persona("security-dev")

        assert dev_persona is not None
        assert security_persona is not None
        assert dev_persona.identity.name == "Override Developer"
        assert security_persona.identity.name == "Security Developer"

        # 3. Validate files
        dev_errors = loader.validate_persona_file(orchestra_personas / "dev.yaml")
        security_errors = loader.validate_persona_file(
            orchestra_personas / "security-dev.yaml"
        )

        assert dev_errors == []
        assert security_errors == []

        # 4. Test caching
        dev_persona_cached = loader.load_persona("dev")
        assert dev_persona is dev_persona_cached

        # 5. Test reload
        loaded_personas = loader.reload_all()
        assert len(loaded_personas) == 2
        assert "dev" in loaded_personas
        assert "security-dev" in loaded_personas

    def test_error_handling_integration(self, temp_persona_structure):
        """Test error handling in integration scenarios."""
        base_path, orchestra_personas, bmad_personas = temp_persona_structure

        # Create invalid YAML file
        invalid_file = orchestra_personas / "invalid.yaml"
        with open(invalid_file, "w") as f:
            f.write("invalid: yaml: content: [")

        loader = PersonaLoader()
        loader.search_paths = [
            base_path / "orchestra" / "personas",
            base_path / ".bmad-core" / "personas",
        ]

        # Discovery should still work
        discovered = loader.discover_personas()
        assert "invalid" in discovered

        # Loading invalid persona should fail gracefully
        invalid_persona = loader.load_persona("invalid")
        assert invalid_persona is None

        # Validation should catch the error
        errors = loader.validate_persona_file(invalid_file)
        assert len(errors) > 0
        assert "YAML parsing error" in errors[0]

        # Reload should skip invalid personas
        loaded = loader.reload_all()
        assert "invalid" not in loaded
        assert len(loaded) == 2  # Only valid personas


class TestPersonaLoaderEdgeCases:
    """Test edge cases for PersonaLoader."""

    def test_empty_yaml_file(self):
        """Test handling empty YAML files."""
        loader = PersonaLoader()

        with patch("builtins.open", mock_open(read_data="")):
            with patch("yaml.safe_load", return_value=None):
                loader._persona_paths = {"empty": Path("empty.yaml")}
                persona = loader.load_persona("empty")

                assert persona is None

    def test_yaml_with_none_values(self):
        """Test handling YAML with None values."""
        data = {
            "identity": {"name": "Test", "id": "test", "title": None, "role": "test"},
            "behavioral_contract": None,
            "command_interface": None,
        }

        loader = PersonaLoader()
        persona = loader._parse_persona_data(data, "test")

        assert persona.identity.title == ""  # Should default to empty string
        assert persona.behavioral_contract.core_principles == []  # Should use defaults

    def test_concurrent_loading(self):
        """Test concurrent persona loading scenarios."""
        loader = PersonaLoader()

        # Simulate concurrent access to cache
        with patch("builtins.open", mock_open()):
            with patch(
                "yaml.safe_load",
                return_value={
                    "identity": {
                        "name": "Test",
                        "id": "test",
                        "title": "Test",
                        "role": "test",
                    }
                },
            ):
                loader._persona_paths = {"test": Path("test.yaml")}

                # Load same persona multiple times
                persona1 = loader.load_persona("test")
                persona2 = loader.load_persona("test")
                persona3 = loader.load_persona("test")

                # All should be the same cached instance
                assert persona1 is persona2 is persona3

    def test_large_persona_data(self):
        """Test handling large persona configurations."""
        large_data = {
            "identity": {
                "name": "Large Persona",
                "id": "large",
                "title": "Large Persona",
                "role": "large",
            },
            "behavioral_contract": {
                "core_principles": [f"Principle {i}" for i in range(100)],
                "halt_conditions": [f"Condition {i}" for i in range(50)],
            },
            "command_interface": {
                "commands": {
                    f"command_{i}": {
                        "description": f"Command {i}",
                        "execution_pattern": f"pattern_{i}",
                        "parameters": {f"param_{j}": f"value_{j}" for j in range(10)},
                    }
                    for i in range(20)
                }
            },
            "resource_dependencies": {
                "tools": [f"tool_{i}" for i in range(100)],
                "knowledge_sources": [f"source_{i}" for i in range(50)],
            },
        }

        loader = PersonaLoader()
        persona = loader._parse_persona_data(large_data, "large")

        assert len(persona.behavioral_contract.core_principles) == 100
        assert len(persona.command_interface.commands) == 20
        assert len(persona.resource_dependencies.tools) == 100

    def test_special_characters_in_paths(self):
        """Test handling special characters in file paths."""
        loader = PersonaLoader()

        # Test with special characters
        special_paths = {
            "test-with-dashes": Path("test-with-dashes.yaml"),
            "test_with_underscores": Path("test_with_underscores.yaml"),
            "test.with.dots": Path("test.with.dots.yaml"),
            "test@with@symbols": Path("test@with@symbols.yaml"),
        }

        loader._persona_paths = special_paths
        personas = loader.list_personas()

        assert len(personas) == 4
        for persona_id in special_paths.keys():
            assert persona_id in personas

    def test_unicode_content(self):
        """Test handling Unicode content in personas."""
        unicode_data = {
            "identity": {
                "name": "Développeur Français",
                "id": "dev-fr",
                "title": "Développeur Logiciel",
                "role": "développeur",
                "icon": "🇫🇷",
            },
            "behavioral_contract": {
                "core_principles": [
                    "Code propre",
                    "Tests complets",
                    "Documentation claire",
                ]
            },
        }

        loader = PersonaLoader()
        persona = loader._parse_persona_data(unicode_data, "dev-fr")

        assert persona.identity.name == "Développeur Français"
        assert persona.identity.icon == "🇫🇷"
        assert "Code propre" in persona.behavioral_contract.core_principles
