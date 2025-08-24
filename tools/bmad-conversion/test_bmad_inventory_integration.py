"""Integration tests for BMad content inventory with real files."""

import json
from pathlib import Path

import pytest

from bmad_inventory import (
    BmadContentInventory,
    BmadContentType,
    ConversionStrategy,
)


class TestBmadInventoryIntegration:
    """Integration tests using actual BMad content files."""

    @pytest.fixture
    def inventory(self):
        """Create inventory instance pointing to actual BMad directory."""
        # Path relative to workspace root, not tools/bmad-conversion
        workspace_root = Path(__file__).parent.parent.parent
        return BmadContentInventory(base_path=workspace_root / ".bmad-core")

    @pytest.fixture
    def conversion_strategy(self):
        """Create conversion strategy instance."""
        return ConversionStrategy()

    def test_scan_real_bmad_agents(self, inventory):
        """Test scanning actual BMad agent files."""
        agents = inventory.scan_agents()

        # Should find the 12 agent files we saw in the directory listing
        assert len(agents) >= 12

        # Check that we have expected agents
        agent_names = [agent.name for agent in agents]
        expected_agents = [
            "dev.md",
            "analyst.md",
            "architect.md",
            "bmad-master.md",
            "bmad-orchestrator.md",
            "pm.md",
            "po.md",
            "qa.md",
            "sm.md",
            "spec.md",
            "tdd-dev.md",
            "ux-expert.md",
        ]

        for expected in expected_agents:
            assert expected in agent_names, f"Expected agent {expected} not found"

        # Verify all items are personas
        for agent in agents:
            assert agent.content_type == BmadContentType.PERSONA
            assert agent.path.exists()

    def test_scan_real_bmad_tasks(self, inventory):
        """Test scanning actual BMad task files."""
        tasks = inventory.scan_tasks()

        # Should find multiple task files
        assert len(tasks) >= 20  # We saw many task files

        # Check for some expected tasks
        task_names = [task.name for task in tasks]
        expected_tasks = [
            "create-doc.md",
            "review-story.md",
            "implement-from-specs.md",
            "validate-test-coverage.md",
            "qa-gate.md",
        ]

        for expected in expected_tasks:
            assert expected in task_names, f"Expected task {expected} not found"

        # Verify all items are tasks
        for task in tasks:
            assert task.content_type == BmadContentType.TASK
            assert task.path.exists()

    def test_scan_real_bmad_templates(self, inventory):
        """Test scanning actual BMad template files."""
        templates = inventory.scan_templates()

        # Should find multiple template files (both .md and .yaml)
        assert len(templates) >= 10

        # Check for some expected templates
        template_names = [template.name for template in templates]
        expected_templates = [
            "prd-tmpl.yaml",
            "story-tmpl.yaml",
            "architecture-tmpl.yaml",
        ]

        for expected in expected_templates:
            assert expected in template_names, f"Expected template {expected} not found"

        # Verify all items are templates
        for template in templates:
            assert template.content_type == BmadContentType.TEMPLATE
            assert template.path.exists()

    def test_scan_real_bmad_checklists(self, inventory):
        """Test scanning actual BMad checklist files."""
        checklists = inventory.scan_checklists()

        # Should find multiple checklist files
        assert len(checklists) >= 5

        # Check for some expected checklists
        checklist_names = [checklist.name for checklist in checklists]
        expected_checklists = [
            "story-dod-checklist.md",
            "architect-checklist.md",
            "pm-checklist.md",
            "tdd-dev-dod-checklist.md",
        ]

        for expected in expected_checklists:
            assert (
                expected in checklist_names
            ), f"Expected checklist {expected} not found"

        # Verify all items are checklists
        for checklist in checklists:
            assert checklist.content_type == BmadContentType.CHECKLIST
            assert checklist.path.exists()

    def test_full_inventory_scan_real_files(self, inventory):
        """Test complete inventory scan with real BMad files."""
        inventory.scan_all()

        # Should have found content in all categories
        assert len(inventory.content_items) >= 50  # Conservative estimate

        # Verify we have items of each type
        content_types = {item.content_type for item in inventory.content_items}
        assert BmadContentType.PERSONA in content_types
        assert BmadContentType.TASK in content_types
        assert BmadContentType.TEMPLATE in content_types
        assert BmadContentType.CHECKLIST in content_types

    def test_generate_real_inventory_report(self, inventory):
        """Test generating inventory report with real BMad content."""
        inventory.scan_all()
        report = inventory.generate_report()

        # Verify report structure
        assert "personas" in report
        assert "tasks" in report
        assert "templates" in report
        assert "checklists" in report
        assert "summary" in report

        # Verify summary data
        summary = report["summary"]
        assert summary["total_items"] > 0
        assert "by_type" in summary

        # Verify each category has items
        assert len(report["personas"]) >= 12
        assert len(report["tasks"]) >= 20
        assert len(report["templates"]) >= 10
        assert len(report["checklists"]) >= 5

    def test_save_inventory_report(self, inventory, tmp_path):
        """Test saving inventory report to file."""
        inventory.scan_all()

        output_file = tmp_path / "bmad_inventory_report.json"
        inventory.save_report(output_file)

        # Verify file was created
        assert output_file.exists()

        # Verify file content
        with open(output_file, "r") as f:
            saved_report = json.load(f)

        assert "personas" in saved_report
        assert "summary" in saved_report
        assert saved_report["summary"]["total_items"] > 0

    def test_convert_real_persona_to_orchestra_schema(
        self, inventory, conversion_strategy
    ):
        """Test converting a real BMad persona to Orchestra schema."""
        agents = inventory.scan_agents()

        # Find the dev.md persona
        dev_persona = None
        for agent in agents:
            if agent.name == "dev.md":
                dev_persona = agent
                break

        assert dev_persona is not None, "dev.md persona not found"

        # Convert to Orchestra schema
        orchestra_schema = conversion_strategy.convert_persona(dev_persona)

        # Verify schema structure
        assert orchestra_schema.schema_type == "persona"
        assert orchestra_schema.is_valid()

        schema_def = orchestra_schema.schema_definition
        assert "identity" in schema_def
        assert "behavioral_contract" in schema_def
        assert "command_interface" in schema_def
        assert "resource_dependencies" in schema_def

        # Verify identity section
        identity = schema_def["identity"]
        assert "name" in identity
        assert "role" in identity
        assert "id" in identity
        assert identity["id"] == "dev"

    def test_convert_real_task_to_orchestra_schema(
        self, inventory, conversion_strategy
    ):
        """Test converting a real BMad task to Orchestra schema."""
        tasks = inventory.scan_tasks()

        # Find a task to convert
        create_doc_task = None
        for task in tasks:
            if task.name == "create-doc.md":
                create_doc_task = task
                break

        assert create_doc_task is not None, "create-doc.md task not found"

        # Convert to Orchestra schema
        orchestra_schema = conversion_strategy.convert_task(create_doc_task)

        # Verify schema structure
        assert orchestra_schema.schema_type == "task"
        assert orchestra_schema.is_valid()

        schema_def = orchestra_schema.schema_definition
        assert "metadata" in schema_def
        assert "execution" in schema_def
        assert "validation" in schema_def

    def test_metadata_extraction_from_real_files(self, inventory):
        """Test that metadata is properly extracted from real BMad files."""
        inventory.scan_all()

        # Check that some items have extracted metadata
        items_with_metadata = [
            item
            for item in inventory.content_items
            if item.metadata and len(item.metadata) > 0
        ]

        # Should have extracted some metadata from files
        assert len(items_with_metadata) > 0

        # Check specific metadata extraction for templates
        templates = [
            item
            for item in inventory.content_items
            if item.content_type == BmadContentType.TEMPLATE
        ]
        yaml_templates = [t for t in templates if t.name.endswith(".yaml")]

        if yaml_templates:
            # YAML templates should have format metadata
            yaml_template = yaml_templates[0]
            assert yaml_template.metadata.get("format") == "yaml"

    def test_directory_structure_planning(self, conversion_strategy):
        """Test directory structure planning for Orchestra resources."""
        structure_plan = conversion_strategy.plan_directory_structure()

        # Verify all expected directories are planned
        expected_dirs = [
            "orchestra/resources/personas",
            "orchestra/resources/tasks",
            "orchestra/resources/templates",
            "orchestra/resources/checklists",
            "schemas",
            "validation",
        ]

        for expected_dir in expected_dirs:
            assert expected_dir in structure_plan
            assert isinstance(structure_plan[expected_dir], list)
            assert len(structure_plan[expected_dir]) > 0

    def test_validation_rules_generation(self, conversion_strategy):
        """Test validation rules generation for CI checks."""
        validation_rules = conversion_strategy.get_validation_rules()

        # Verify validation rules structure
        assert "json_schemas" in validation_rules
        assert "ci_checks" in validation_rules
        assert "required_fields" in validation_rules

        # Verify schema paths
        schemas = validation_rules["json_schemas"]
        assert "persona" in schemas
        assert "task" in schemas
        assert "template" in schemas
        assert "checklist" in schemas

        # Verify CI checks
        ci_checks = validation_rules["ci_checks"]
        assert "schema_validation" in ci_checks
        assert "required_fields_check" in ci_checks
