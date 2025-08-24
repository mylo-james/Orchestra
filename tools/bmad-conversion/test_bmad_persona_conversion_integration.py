"""Integration tests for BMad persona conversion with real files."""

from pathlib import Path

import pytest
import yaml

from bmad_inventory import BmadContentInventory
from bmad_persona_converter import BmadPersonaConverter
from orchestra.system.loader import PersonaLoader


class TestBmadPersonaConversionIntegration:
    """Integration tests using actual BMad persona files."""

    @pytest.fixture
    def inventory(self):
        """Create inventory instance pointing to actual BMad directory."""
        return BmadContentInventory(base_path=Path(".bmad-core"))

    @pytest.fixture
    def converter(self):
        """Create converter instance."""
        return BmadPersonaConverter()

    @pytest.fixture
    def persona_loader(self):
        """Create persona loader instance."""
        return PersonaLoader()

    def test_convert_all_real_bmad_personas(self, inventory, converter):
        """Test converting all real BMad personas to Orchestra format."""
        # Get all BMad personas
        bmad_personas = inventory.scan_agents()
        target_personas = converter.identify_target_personas(bmad_personas)

        # Should have found the expected personas
        assert len(target_personas) == 12  # We have 12 BMad personas

        # Convert all personas
        results = converter.convert_all_personas(target_personas)

        # All conversions should succeed
        successful_results = [r for r in results if r.success]
        assert len(successful_results) == len(target_personas)

        # Verify each result
        for result in successful_results:
            assert result.persona_spec is not None
            assert result.yaml_content is not None
            assert len(result.validation_errors) == 0

            # Verify YAML is valid
            parsed_yaml = yaml.safe_load(result.yaml_content)
            assert isinstance(parsed_yaml, dict)
            assert "identity" in parsed_yaml
            assert "behavioral_contract" in parsed_yaml
            assert "command_interface" in parsed_yaml
            assert "resource_dependencies" in parsed_yaml

    def test_convert_specific_bmad_personas(self, inventory, converter):
        """Test converting specific BMad personas with detailed validation."""
        # Get specific personas to test
        bmad_personas = inventory.scan_agents()
        test_personas = {}

        for persona in bmad_personas:
            if persona.name in ["dev.md", "analyst.md", "architect.md"]:
                test_personas[persona.name] = persona

        assert len(test_personas) >= 3, "Should find at least 3 test personas"

        # Convert each test persona
        for name, persona in test_personas.items():
            result = converter.convert_persona(persona)

            assert (
                result.success is True
            ), f"Failed to convert {name}: {result.validation_errors}"
            assert result.persona_spec is not None
            assert result.yaml_content is not None

            # Verify persona-specific details
            spec = result.persona_spec
            assert spec.identity.id == persona.name.replace(".md", "").lower()
            assert spec.identity.name is not None
            assert spec.identity.role is not None
            assert spec.version is not None

    def test_converted_personas_load_correctly(self, inventory, converter, tmp_path):
        """Test that converted personas can be loaded by PersonaLoader."""
        # Convert a few personas
        bmad_personas = inventory.scan_agents()
        target_personas = converter.identify_target_personas(bmad_personas)[:3]

        # Set output directory to temp path
        converter.output_directory = tmp_path / "converted_personas"

        # Convert and save personas
        converter.convert_and_save_all(target_personas)

        # Verify files were created
        yaml_files = list(converter.output_directory.glob("*.yaml"))
        assert len(yaml_files) == len(target_personas)

        # Test loading with PersonaLoader
        loader = PersonaLoader()

        for yaml_file in yaml_files:
            # Load persona from file
            loaded_spec = loader.load_persona_from_file(yaml_file)
            assert loaded_spec is not None, f"Failed to load {yaml_file}"

            # Verify loaded spec structure
            assert loaded_spec.identity is not None
            assert loaded_spec.behavioral_contract is not None
            assert loaded_spec.command_interface is not None
            assert loaded_spec.resource_dependencies is not None

    def test_performance_with_all_personas(self, inventory, converter):
        """Test conversion performance with all BMad personas."""
        import time

        # Get all personas
        bmad_personas = inventory.scan_agents()
        target_personas = converter.identify_target_personas(bmad_personas)

        # Measure conversion time
        start_time = time.time()
        results = converter.convert_all_personas(target_personas)
        end_time = time.time()

        conversion_time = end_time - start_time

        # Should convert all personas quickly (under 5 seconds)
        assert conversion_time < 5.0, f"Conversion took {conversion_time}s, too slow"

        # All conversions should succeed
        successful_count = len([r for r in results if r.success])
        assert successful_count == len(target_personas)

    def test_yaml_output_quality(self, inventory, converter):
        """Test the quality and completeness of YAML output."""
        # Convert dev persona as a detailed test case
        bmad_personas = inventory.scan_agents()
        dev_persona = next((p for p in bmad_personas if p.name == "dev.md"), None)
        assert dev_persona is not None

        result = converter.convert_persona(dev_persona)
        assert result.success is True

        # Parse and validate YAML structure
        parsed = yaml.safe_load(result.yaml_content)

        # Verify identity section completeness
        identity = parsed["identity"]
        required_identity_fields = [
            "name",
            "id",
            "title",
            "role",
            "icon",
            "when_to_use",
            "style",
            "focus",
        ]
        for field in required_identity_fields:
            assert field in identity, f"Missing identity field: {field}"
            assert (
                identity[field] is not None and identity[field] != ""
            ), f"Empty identity field: {field}"

        # Verify behavioral contract
        behavioral_contract = parsed["behavioral_contract"]
        assert "core_principles" in behavioral_contract
        assert "interaction_style" in behavioral_contract
        assert "halt_conditions" in behavioral_contract
        assert "decision_framework" in behavioral_contract

        # Verify command interface
        command_interface = parsed["command_interface"]
        assert "execution_model" in command_interface
        assert "commands" in command_interface
        assert "default_command" in command_interface
        assert isinstance(command_interface["commands"], dict)

        # Should have at least a help command
        assert len(command_interface["commands"]) >= 1

        # Verify resource dependencies
        resource_deps = parsed["resource_dependencies"]
        required_dep_fields = [
            "knowledge_sources",
            "tasks",
            "tools",
            "templates",
            "required_services",
        ]
        for field in required_dep_fields:
            assert field in resource_deps, f"Missing resource dependency field: {field}"
            assert isinstance(
                resource_deps[field], list
            ), f"Resource dependency {field} should be a list"

    def test_metadata_extraction_from_real_files(self, inventory, converter):
        """Test that metadata is properly extracted from real BMad files."""
        # Get all personas and convert them
        bmad_personas = inventory.scan_agents()
        target_personas = converter.identify_target_personas(bmad_personas)

        results = converter.convert_all_personas(target_personas)
        successful_results = [r for r in results if r.success]

        # Check that personas have meaningful extracted data
        personas_with_rich_data = 0

        for result in successful_results:
            spec = result.persona_spec

            # Count personas with rich metadata
            if (
                len(spec.behavioral_contract.core_principles) > 0
                or len(spec.resource_dependencies.tools) > 0
                or len(spec.command_interface.commands) > 1
            ):  # More than just help command
                personas_with_rich_data += 1

        # At least some personas should have rich metadata extracted
        # Note: BMad files may have minimal structured metadata, so we check for at least 1
        assert (
            personas_with_rich_data >= 1
        ), "Should extract rich metadata from at least 1 persona"

    def test_backward_compatibility_validation(
        self, inventory, converter, persona_loader
    ):
        """Test that converted personas don't break existing persona loading."""
        # Load existing Orchestra personas first
        existing_personas = ["orchestrator", "dev", "release"]
        existing_specs = {}

        for persona_id in existing_personas:
            try:
                spec = persona_loader.load_persona(persona_id)
                if spec:
                    existing_specs[persona_id] = spec
            except Exception:
                # Skip if persona doesn't exist
                pass

        # Convert BMad personas
        bmad_personas = inventory.scan_agents()
        target_personas = converter.identify_target_personas(bmad_personas)[
            :5
        ]  # Test with 5

        results = converter.convert_all_personas(target_personas)

        # Verify all conversions succeeded
        successful_results = [r for r in results if r.success]
        assert len(successful_results) == len(target_personas)

        # Verify existing personas still work (if they existed)
        for persona_id, original_spec in existing_specs.items():
            current_spec = persona_loader.load_persona(persona_id)
            assert (
                current_spec is not None
            ), f"Existing persona {persona_id} no longer loads"

            # Basic structure should be the same
            assert current_spec.identity.id == original_spec.identity.id
            assert current_spec.identity.name == original_spec.identity.name

    def test_schema_validation_with_real_data(self, inventory, converter):
        """Test schema validation with real converted data."""
        # Convert all personas
        bmad_personas = inventory.scan_agents()
        target_personas = converter.identify_target_personas(bmad_personas)

        results = converter.convert_all_personas(target_personas)

        # All results should pass validation
        for result in results:
            assert (
                result.success is True
            ), f"Validation failed: {result.validation_errors}"

            # Double-check with explicit validation
            validation_result = converter.validate_persona_schema(result.persona_spec)
            assert (
                validation_result.is_valid is True
            ), f"Schema validation failed: {validation_result.errors}"

    def test_conversion_preserves_essential_information(self, inventory, converter):
        """Test that conversion preserves essential BMad persona information."""
        # Get personas with known characteristics
        bmad_personas = inventory.scan_agents()

        # Test specific personas we know should have certain characteristics
        test_cases = {
            "dev.md": {
                "expected_role_keywords": [
                    "developer",
                    "development",
                    "code",
                    "implementation",
                ],
                "should_have_commands": True,
            },
            "qa.md": {
                "expected_role_keywords": ["quality", "test", "qa", "assurance"],
                "should_have_commands": True,
            },
            "architect.md": {
                "expected_role_keywords": ["architect", "architecture", "design"],
                "should_have_commands": True,
            },
        }

        for persona in bmad_personas:
            if persona.name in test_cases:
                test_case = test_cases[persona.name]

                result = converter.convert_persona(persona)
                assert result.success is True

                spec = result.persona_spec

                # Check role contains expected keywords
                role_text = spec.identity.role.lower()
                title_text = spec.identity.title.lower()
                combined_text = f"{role_text} {title_text}"

                found_keywords = [
                    kw
                    for kw in test_case["expected_role_keywords"]
                    if kw in combined_text
                ]
                assert (
                    len(found_keywords) > 0
                ), f"No expected keywords found in {persona.name} role/title"

                # Check commands if expected
                if test_case["should_have_commands"]:
                    assert (
                        len(spec.command_interface.commands) >= 1
                    ), f"No commands found for {persona.name}"

    def test_batch_conversion_file_output(self, inventory, converter, tmp_path):
        """Test batch conversion with file output."""
        # Set up output directory
        output_dir = tmp_path / "batch_converted_personas"
        converter.output_directory = output_dir

        # Get all personas
        bmad_personas = inventory.scan_agents()
        target_personas = converter.identify_target_personas(bmad_personas)

        # Perform batch conversion with file output
        results = converter.convert_and_save_all(target_personas)

        # Verify output directory was created
        assert output_dir.exists()

        # Verify all personas were saved
        yaml_files = list(output_dir.glob("*.yaml"))
        successful_results = [r for r in results if r.success]
        assert len(yaml_files) == len(successful_results)

        # Verify each file is valid YAML and contains expected structure
        for yaml_file in yaml_files:
            with open(yaml_file, "r") as f:
                content = f.read()
                parsed = yaml.safe_load(content)

            assert isinstance(parsed, dict)
            assert "identity" in parsed
            assert "behavioral_contract" in parsed
            assert "command_interface" in parsed
            assert "resource_dependencies" in parsed

            # Verify the persona ID matches the filename
            expected_id = yaml_file.stem
            assert parsed["identity"]["id"] == expected_id
