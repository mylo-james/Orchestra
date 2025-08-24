"""Unit tests for PersonaLoader."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

# Import the module to ensure it's loaded for coverage
from orchestra.system.loader import PersonaLoader
from orchestra.system.specs import PersonaSpec


@pytest.fixture
def temp_persona_dir():
    """Create a temporary directory with test persona files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        persona_dir = Path(tmpdir) / "personas"
        persona_dir.mkdir()

        # Create a test persona file
        test_persona = {
            "identity": {
                "name": "TestAgent",
                "id": "test",
                "title": "Test Agent",
                "role": "Testing persona system",
                "icon": "🧪",
            },
            "behavioral_contract": {
                "core_principles": ["Test principle 1", "Test principle 2"],
                "interaction_style": "test_style",
            },
            "command_interface": {
                "execution_model": "sequential",
                "commands": {
                    "test-command": {
                        "description": "Test command",
                        "execution_pattern": "test → validate",
                    }
                },
            },
            "resource_dependencies": {
                "tools": ["test-tool"],
            },
        }

        with open(persona_dir / "test.yaml", "w") as f:
            yaml.dump(test_persona, f)

        yield persona_dir


def test_persona_loader_init():
    """Test PersonaLoader initialization."""
    loader = PersonaLoader(cache_enabled=True)
    assert loader.cache_enabled is True
    assert len(loader._cache) == 0
    assert len(loader._persona_paths) == 0


def test_discover_personas(temp_persona_dir):
    """Test persona discovery."""
    loader = PersonaLoader()
    loader.search_paths = [temp_persona_dir]

    discovered = loader.discover_personas()
    assert "test" in discovered
    assert discovered["test"].name == "test.yaml"


def test_load_persona(temp_persona_dir):
    """Test loading a persona."""
    loader = PersonaLoader()
    loader.search_paths = [temp_persona_dir]

    spec = loader.load_persona("test")
    assert spec is not None
    assert isinstance(spec, PersonaSpec)
    assert spec.identity.name == "TestAgent"
    assert spec.identity.id == "test"
    assert len(spec.behavioral_contract.core_principles) == 2


def test_load_persona_not_found():
    """Test loading a non-existent persona."""
    loader = PersonaLoader()
    spec = loader.load_persona("nonexistent")
    assert spec is None


def test_load_persona_with_cache(temp_persona_dir):
    """Test persona caching."""
    loader = PersonaLoader(cache_enabled=True)
    loader.search_paths = [temp_persona_dir]

    # First load
    spec1 = loader.load_persona("test")
    assert spec1 is not None

    # Second load should come from cache
    with patch.object(loader, "_parse_persona_data") as mock_parse:
        spec2 = loader.load_persona("test")
        assert spec2 is spec1  # Same object from cache
        mock_parse.assert_not_called()


def test_load_persona_force_reload(temp_persona_dir):
    """Test force reload bypasses cache."""
    loader = PersonaLoader(cache_enabled=True)
    loader.search_paths = [temp_persona_dir]

    # First load
    spec1 = loader.load_persona("test")

    # Force reload
    spec2 = loader.load_persona("test", force_reload=True)
    assert spec2 is not None
    assert spec2 is not spec1  # Different object


def test_list_personas(temp_persona_dir):
    """Test listing personas."""
    loader = PersonaLoader()
    loader.search_paths = [temp_persona_dir]

    personas = loader.list_personas()
    assert "test" in personas


def test_validate_persona_file(temp_persona_dir):
    """Test validating a persona file."""
    loader = PersonaLoader()
    test_file = temp_persona_dir / "test.yaml"

    errors = loader.validate_persona_file(test_file)
    assert len(errors) == 0


def test_validate_invalid_persona_file(temp_persona_dir):
    """Test validating an invalid persona file."""
    loader = PersonaLoader()

    # Create invalid persona file
    invalid_file = temp_persona_dir / "invalid.yaml"
    with open(invalid_file, "w") as f:
        yaml.dump({"invalid": "data"}, f)

    errors = loader.validate_persona_file(invalid_file)
    assert len(errors) > 0


def test_clear_cache(temp_persona_dir):
    """Test clearing the cache."""
    loader = PersonaLoader(cache_enabled=True)
    loader.search_paths = [temp_persona_dir]

    # Load a persona
    loader.load_persona("test")
    assert len(loader._cache) == 1

    # Clear cache
    loader.clear_cache()
    assert len(loader._cache) == 0


def test_reload_all(temp_persona_dir):
    """Test reloading all personas."""
    loader = PersonaLoader()
    loader.search_paths = [temp_persona_dir]

    loaded = loader.reload_all()
    assert "test" in loaded
    assert isinstance(loaded["test"], PersonaSpec)


def test_parse_persona_data():
    """Test parsing persona data."""
    loader = PersonaLoader()

    data = {
        "identity": {
            "name": "TestAgent",
            "id": "test",
            "title": "Test Agent",
            "role": "Testing",
        },
        "behavioral_contract": {
            "core_principles": ["Principle 1"],
        },
        "command_interface": {
            "commands": {
                "test": {
                    "description": "Test",
                    "execution_pattern": "test",
                }
            }
        },
        "resource_dependencies": {
            "tools": ["tool1"],
        },
        "knowledge_context": {
            "domains": ["test-domain"],
            "context_window_size": 2048,
        },
        "version": "2.0.0",
        "tags": ["test", "example"],
        "experimental": True,
    }

    spec = loader._parse_persona_data(data, "test")

    assert spec.identity.name == "TestAgent"
    assert spec.version == "2.0.0"
    assert spec.experimental is True
    assert len(spec.tags) == 2
    assert spec.knowledge_context is not None
    assert spec.knowledge_context.context_window_size == 2048


def test_yaml_error_handling(temp_persona_dir):
    """Test handling of YAML parsing errors."""
    loader = PersonaLoader()
    loader.search_paths = [temp_persona_dir]

    # Create a file with invalid YAML
    bad_file = temp_persona_dir / "bad.yaml"
    with open(bad_file, "w") as f:
        f.write("invalid: yaml: content: [")

    spec = loader.load_persona("bad")
    assert spec is None


class TestMissingCoverageLines:
    """Test specific code paths that were missing coverage."""

    def test_load_persona_validation_failure(self, temp_persona_dir):
        """Test load_persona when validation fails - covers lines 113-114."""
        loader = PersonaLoader()
        loader.search_paths = [temp_persona_dir]

        # Create a persona file with invalid structure that will fail validation
        invalid_persona = temp_persona_dir / "invalid_persona.yaml"
        invalid_data = {
            "identity": {
                "name": "Test Agent"
                # Missing required fields like role, title
            }
            # Missing other required sections
        }

        with open(invalid_persona, "w") as f:
            yaml.dump(invalid_data, f)

        result = loader.load_persona("invalid_persona")
        assert result is None  # Should return None when validation fails

    def test_load_persona_general_exception(self):
        """Test load_persona when general exception occurs - covers lines 126-128."""
        from unittest.mock import patch

        loader = PersonaLoader()

        with (
            patch.object(Path, "exists", return_value=True),
            patch.object(Path, "read_text", side_effect=Exception("File read error")),
        ):

            result = loader.load_persona("test_persona")
            assert result is None  # Should return None when exception occurs

    def test_validate_persona_file_general_exception(self, temp_persona_dir):
        """Test validate_persona_file with general exception - covers lines 257-260."""
        loader = PersonaLoader()

        # Use a non-existent file to trigger FileNotFoundError
        non_existent_file = temp_persona_dir / "does_not_exist.yaml"

        errors = loader.validate_persona_file(non_existent_file)
        assert len(errors) > 0
        assert any("Validation error" in error for error in errors)
