"""Tests for BMad content inventory and conversion strategy."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from bmad_inventory import (
    BmadContentInventory,
    BmadContentItem,
    BmadContentType,
    ConversionStrategy,
    ResourceSchema,
)


class TestBmadContentInventory:
    """Test BMad content inventory functionality."""

    @pytest.fixture
    def inventory(self):
        """Create a BMad content inventory instance."""
        return BmadContentInventory(base_path=Path(".bmad-core"))

    @pytest.fixture
    def mock_bmad_structure(self):
        """Mock BMad directory structure for testing."""
        return {
            "agents": [
                "analyst.md",
                "architect.md",
                "bmad-master.md",
                "bmad-orchestrator.md",
                "dev.md",
                "pm.md",
                "po.md",
                "qa.md",
                "sm.md",
                "spec.md",
                "tdd-dev.md",
                "ux-expert.md",
            ],
            "tasks": [
                "create-doc.md",
                "review-story.md",
                "implement-from-specs.md",
                "validate-test-coverage.md",
                "qa-gate.md",
            ],
            "templates": [
                "prd-tmpl.yaml",
                "story-tmpl.yaml",
                "architecture-tmpl.yaml",
                "test-spec-tmpl.md",
            ],
            "checklists": [
                "story-dod-checklist.md",
                "architect-checklist.md",
                "pm-checklist.md",
                "tdd-dev-dod-checklist.md",
            ],
        }

    def test_inventory_initialization(self, inventory):
        """Test that inventory initializes with correct base path."""
        assert inventory.base_path == Path(".bmad-core")
        assert inventory.content_items == []
        assert inventory.conversion_strategy is not None

    def test_scan_agents_directory(self, inventory, mock_bmad_structure):
        """Test scanning agents directory and identifying personas."""
        with patch.object(inventory, "_scan_directory") as mock_scan:
            mock_scan.return_value = [
                BmadContentItem(
                    name="dev.md",
                    path=Path(".bmad-core/agents/dev.md"),
                    content_type=BmadContentType.PERSONA,
                    version="1.0",
                    metadata={"role": "developer", "commands": ["implement", "test"]},
                )
            ]

            items = inventory.scan_agents()

            assert len(items) == 1
            assert items[0].content_type == BmadContentType.PERSONA
            assert items[0].name == "dev.md"
            mock_scan.assert_called_once_with(
                Path(".bmad-core/agents"), BmadContentType.PERSONA
            )

    def test_scan_tasks_directory(self, inventory):
        """Test scanning tasks directory and identifying task resources."""
        with patch.object(inventory, "_scan_directory") as mock_scan:
            mock_scan.return_value = [
                BmadContentItem(
                    name="create-doc.md",
                    path=Path(".bmad-core/tasks/create-doc.md"),
                    content_type=BmadContentType.TASK,
                    version="1.0",
                    metadata={"dependencies": [], "outputs": ["document"]},
                )
            ]

            items = inventory.scan_tasks()

            assert len(items) == 1
            assert items[0].content_type == BmadContentType.TASK
            assert items[0].name == "create-doc.md"

    def test_scan_templates_directory(self, inventory):
        """Test scanning templates directory and identifying template resources."""
        with patch.object(inventory, "_scan_directory") as mock_scan:
            mock_scan.return_value = [
                BmadContentItem(
                    name="prd-tmpl.yaml",
                    path=Path(".bmad-core/templates/prd-tmpl.yaml"),
                    content_type=BmadContentType.TEMPLATE,
                    version="1.0",
                    metadata={
                        "format": "yaml",
                        "variables": ["project_name", "description"],
                    },
                )
            ]

            items = inventory.scan_templates()

            assert len(items) == 1
            assert items[0].content_type == BmadContentType.TEMPLATE
            assert items[0].name == "prd-tmpl.yaml"

    def test_scan_checklists_directory(self, inventory):
        """Test scanning checklists directory and identifying checklist resources."""
        with patch.object(inventory, "_scan_directory") as mock_scan:
            mock_scan.return_value = [
                BmadContentItem(
                    name="story-dod-checklist.md",
                    path=Path(".bmad-core/checklists/story-dod-checklist.md"),
                    content_type=BmadContentType.CHECKLIST,
                    version="1.0",
                    metadata={"items": 5, "categories": ["implementation", "testing"]},
                )
            ]

            items = inventory.scan_checklists()

            assert len(items) == 1
            assert items[0].content_type == BmadContentType.CHECKLIST
            assert items[0].name == "story-dod-checklist.md"

    def test_full_inventory_scan(self, inventory):
        """Test complete inventory scan of all BMad content."""
        with (
            patch.object(inventory, "scan_agents") as mock_agents,
            patch.object(inventory, "scan_tasks") as mock_tasks,
            patch.object(inventory, "scan_templates") as mock_templates,
            patch.object(inventory, "scan_checklists") as mock_checklists,
        ):

            mock_agents.return_value = [Mock(content_type=BmadContentType.PERSONA)]
            mock_tasks.return_value = [Mock(content_type=BmadContentType.TASK)]
            mock_templates.return_value = [Mock(content_type=BmadContentType.TEMPLATE)]
            mock_checklists.return_value = [
                Mock(content_type=BmadContentType.CHECKLIST)
            ]

            inventory.scan_all()

            assert len(inventory.content_items) == 4
            mock_agents.assert_called_once()
            mock_tasks.assert_called_once()
            mock_templates.assert_called_once()
            mock_checklists.assert_called_once()

    def test_generate_inventory_report(self, inventory):
        """Test generating inventory report with categorized content."""
        # Setup mock content items
        inventory.content_items = [
            BmadContentItem(
                name="dev.md",
                path=Path(".bmad-core/agents/dev.md"),
                content_type=BmadContentType.PERSONA,
                version="1.0",
                metadata={},
            ),
            BmadContentItem(
                name="create-doc.md",
                path=Path(".bmad-core/tasks/create-doc.md"),
                content_type=BmadContentType.TASK,
                version="1.0",
                metadata={},
            ),
        ]

        report = inventory.generate_report()

        assert "personas" in report
        assert "tasks" in report
        assert "templates" in report
        assert "checklists" in report
        assert len(report["personas"]) == 1
        assert len(report["tasks"]) == 1
        assert report["personas"][0]["name"] == "dev.md"


class TestConversionStrategy:
    """Test BMad to Orchestra conversion strategy."""

    @pytest.fixture
    def strategy(self):
        """Create a conversion strategy instance."""
        return ConversionStrategy()

    def test_persona_conversion_mapping(self, strategy):
        """Test mapping BMad persona to Orchestra YAML schema."""
        bmad_persona = BmadContentItem(
            name="dev.md",
            path=Path(".bmad-core/agents/dev.md"),
            content_type=BmadContentType.PERSONA,
            version="1.0",
            metadata={
                "name": "Alex",
                "role": "Developer",
                "commands": ["implement", "test", "debug"],
                "dependencies": ["github-tools", "test-runner"],
            },
        )

        orchestra_schema = strategy.convert_persona(bmad_persona)

        assert orchestra_schema.schema_type == "persona"
        assert "identity" in orchestra_schema.schema_definition
        assert "behavioral_contract" in orchestra_schema.schema_definition
        assert "command_interface" in orchestra_schema.schema_definition
        assert "resource_dependencies" in orchestra_schema.schema_definition

    def test_task_conversion_mapping(self, strategy):
        """Test mapping BMad task to Orchestra resource schema."""
        bmad_task = BmadContentItem(
            name="create-doc.md",
            path=Path(".bmad-core/tasks/create-doc.md"),
            content_type=BmadContentType.TASK,
            version="1.0",
            metadata={
                "description": "Create documentation",
                "inputs": ["template", "data"],
                "outputs": ["document"],
                "dependencies": [],
            },
        )

        orchestra_schema = strategy.convert_task(bmad_task)

        assert orchestra_schema.schema_type == "task"
        assert "metadata" in orchestra_schema.schema_definition
        assert "execution" in orchestra_schema.schema_definition
        assert "validation" in orchestra_schema.schema_definition

    def test_template_conversion_mapping(self, strategy):
        """Test mapping BMad template to Orchestra resource schema."""
        bmad_template = BmadContentItem(
            name="prd-tmpl.yaml",
            path=Path(".bmad-core/templates/prd-tmpl.yaml"),
            content_type=BmadContentType.TEMPLATE,
            version="1.0",
            metadata={
                "format": "yaml",
                "variables": ["project_name", "description"],
                "sections": ["overview", "requirements"],
            },
        )

        orchestra_schema = strategy.convert_template(bmad_template)

        assert orchestra_schema.schema_type == "template"
        assert "metadata" in orchestra_schema.schema_definition
        assert "variables" in orchestra_schema.schema_definition
        assert "content" in orchestra_schema.schema_definition

    def test_checklist_conversion_mapping(self, strategy):
        """Test mapping BMad checklist to Orchestra resource schema."""
        bmad_checklist = BmadContentItem(
            name="story-dod-checklist.md",
            path=Path(".bmad-core/checklists/story-dod-checklist.md"),
            content_type=BmadContentType.CHECKLIST,
            version="1.0",
            metadata={
                "items": 5,
                "categories": ["implementation", "testing"],
                "required": True,
            },
        )

        orchestra_schema = strategy.convert_checklist(bmad_checklist)

        assert orchestra_schema.schema_type == "checklist"
        assert "metadata" in orchestra_schema.schema_definition
        assert "items" in orchestra_schema.schema_definition
        assert "validation" in orchestra_schema.schema_definition

    def test_conversion_validation_rules(self, strategy):
        """Test that conversion includes validation rules and CI checks."""
        validation_rules = strategy.get_validation_rules()

        assert "json_schemas" in validation_rules
        assert "ci_checks" in validation_rules
        assert "required_fields" in validation_rules
        assert len(validation_rules["json_schemas"]) > 0

    def test_directory_structure_planning(self, strategy):
        """Test planning of Orchestra resource directory structure."""
        structure_plan = strategy.plan_directory_structure()

        assert "orchestra/resources/personas" in structure_plan
        assert "orchestra/resources/tasks" in structure_plan
        assert "orchestra/resources/templates" in structure_plan
        assert "orchestra/resources/checklists" in structure_plan
        assert "schemas" in structure_plan
        assert "validation" in structure_plan


class TestResourceSchema:
    """Test resource schema definitions and validation."""

    def test_persona_schema_structure(self):
        """Test persona schema has required Orchestra fields."""
        schema = ResourceSchema(
            schema_type="persona",
            schema_definition={
                "identity": {"name": "Alex", "role": "Developer"},
                "behavioral_contract": {"core_principles": []},
                "command_interface": {"commands": {}},
                "resource_dependencies": {"tools": []},
            },
        )

        assert schema.schema_type == "persona"
        assert schema.is_valid()
        assert "identity" in schema.schema_definition

    def test_task_schema_structure(self):
        """Test task schema has required Orchestra fields."""
        schema = ResourceSchema(
            schema_type="task",
            schema_definition={
                "metadata": {"name": "create-doc", "version": "1.0"},
                "execution": {"steps": [], "timeout": 300},
                "validation": {"required_outputs": []},
            },
        )

        assert schema.schema_type == "task"
        assert schema.is_valid()
        assert "execution" in schema.schema_definition

    def test_schema_validation_with_missing_fields(self):
        """Test schema validation fails with missing required fields."""
        schema = ResourceSchema(
            schema_type="persona",
            schema_definition={"identity": {"name": "Alex"}},  # Missing required fields
        )

        assert not schema.is_valid()
        validation_errors = schema.get_validation_errors()
        assert len(validation_errors) > 0
        assert "behavioral_contract" in str(validation_errors)

    def test_schema_json_export(self):
        """Test exporting schema as JSON for CI validation."""
        schema = ResourceSchema(
            schema_type="persona",
            schema_definition={
                "identity": {"name": "Alex", "role": "Developer"},
                "behavioral_contract": {"core_principles": []},
                "command_interface": {"commands": {}},
                "resource_dependencies": {"tools": []},
            },
        )

        json_schema = schema.to_json_schema()

        assert "type" in json_schema
        assert "properties" in json_schema
        assert "required" in json_schema
        assert json_schema["type"] == "object"


class TestBmadContentItem:
    """Test BMad content item data structure."""

    def test_content_item_creation(self):
        """Test creating BMad content item with metadata."""
        item = BmadContentItem(
            name="dev.md",
            path=Path(".bmad-core/agents/dev.md"),
            content_type=BmadContentType.PERSONA,
            version="1.0",
            metadata={"role": "developer", "commands": ["implement"]},
        )

        assert item.name == "dev.md"
        assert item.content_type == BmadContentType.PERSONA
        assert item.version == "1.0"
        assert item.metadata["role"] == "developer"

    def test_content_item_serialization(self):
        """Test serializing content item for reporting."""
        item = BmadContentItem(
            name="dev.md",
            path=Path(".bmad-core/agents/dev.md"),
            content_type=BmadContentType.PERSONA,
            version="1.0",
            metadata={"role": "developer"},
        )

        serialized = item.to_dict()

        assert serialized["name"] == "dev.md"
        assert serialized["content_type"] == "persona"
        assert serialized["version"] == "1.0"
        assert serialized["metadata"]["role"] == "developer"
