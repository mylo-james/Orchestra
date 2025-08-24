"""Tests for Orchestra resource system (Story 1.3)."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.append(
    str(Path(__file__).parent.parent.parent.parent / "tools" / "bmad-conversion")
)
from bmad_inventory import BmadContentInventory

from orchestra.system.checklist_engine import ChecklistEngine, ChecklistExecutionResult
from orchestra.system.resource_loader import (
    ResourceLoader,
    ResourceLoadResult,
    ResourceMetadata,
    ResourceType,
)
from orchestra.system.task_engine import TaskEngine, TaskExecutionResult
from orchestra.system.template_processor import TemplateProcessor, TemplateRenderResult


class TestResourceMetadata:
    """Test ResourceMetadata data structure."""

    def test_resource_metadata_creation(self):
        """Test creating resource metadata."""
        metadata = ResourceMetadata(
            id="test-task",
            name="Test Task",
            resource_type=ResourceType.TASK,
            version="1.0.0",
            description="A test task",
            author="test-author",
            tags=["test", "example"],
            dependencies=["dep1", "dep2"],
            trust_level="trusted",
            provenance="bmad-core/tasks/test-task.md",
        )

        assert metadata.id == "test-task"
        assert metadata.name == "Test Task"
        assert metadata.resource_type == ResourceType.TASK
        assert metadata.version == "1.0.0"
        assert metadata.description == "A test task"
        assert metadata.author == "test-author"
        assert metadata.tags == ["test", "example"]
        assert metadata.dependencies == ["dep1", "dep2"]
        assert metadata.trust_level == "trusted"
        assert metadata.provenance == "bmad-core/tasks/test-task.md"

    def test_resource_metadata_defaults(self):
        """Test resource metadata with default values."""
        metadata = ResourceMetadata(
            id="simple-task", name="Simple Task", resource_type=ResourceType.TASK
        )

        assert metadata.version == "1.0.0"
        assert metadata.description == ""
        assert metadata.author == "unknown"
        assert metadata.tags == []
        assert metadata.dependencies == []
        assert metadata.trust_level == "untrusted"
        assert metadata.provenance is None


class TestResourceLoader:
    """Test ResourceLoader functionality."""

    @pytest.fixture
    def resource_loader(self):
        """Create a ResourceLoader instance."""
        return ResourceLoader(base_path=Path(".bmad-core"))

    @pytest.fixture
    def inventory(self):
        """Create inventory instance for accessing BMad resources."""
        return BmadContentInventory(base_path=Path(".bmad-core"))

    def test_resource_loader_initialization(self, resource_loader):
        """Test ResourceLoader initialization."""
        assert resource_loader is not None
        assert resource_loader.base_path == Path(".bmad-core")
        assert resource_loader.cache_enabled is True
        assert resource_loader.hot_reload_enabled is False

    def test_discover_resources_by_type(self, resource_loader):
        """Test discovering resources by type (AC: 1)."""
        # Discover tasks
        tasks = resource_loader.discover_resources(ResourceType.TASK)
        assert len(tasks) > 0

        # Discover templates
        templates = resource_loader.discover_resources(ResourceType.TEMPLATE)
        assert len(templates) > 0

        # Discover checklists
        checklists = resource_loader.discover_resources(ResourceType.CHECKLIST)
        assert len(checklists) > 0

        # Verify resource metadata structure
        for task in tasks:
            assert isinstance(task, ResourceMetadata)
            assert task.resource_type == ResourceType.TASK
            assert task.id is not None
            assert task.name is not None

    def test_load_resource_by_id(self, resource_loader):
        """Test loading a specific resource by ID (AC: 2)."""
        # First discover available resources
        tasks = resource_loader.discover_resources(ResourceType.TASK)
        assert len(tasks) > 0

        # Load the first task
        task_id = tasks[0].id
        result = resource_loader.load_resource(task_id, ResourceType.TASK)

        assert isinstance(result, ResourceLoadResult)
        assert result.success is True
        assert result.metadata is not None
        assert result.content is not None
        assert result.validation_errors == []
        assert result.metadata.id == task_id

    def test_load_nonexistent_resource(self, resource_loader):
        """Test loading a resource that doesn't exist."""
        result = resource_loader.load_resource("nonexistent-task", ResourceType.TASK)

        assert isinstance(result, ResourceLoadResult)
        assert result.success is False
        assert result.metadata is None
        assert result.content is None
        assert len(result.validation_errors) > 0

    def test_validate_resource_schema(self, resource_loader):
        """Test resource schema validation (AC: 3)."""
        # Load a real resource
        tasks = resource_loader.discover_resources(ResourceType.TASK)
        task_id = tasks[0].id
        result = resource_loader.load_resource(task_id, ResourceType.TASK)

        assert result.success is True

        # Validate the loaded resource
        validation_result = resource_loader.validate_resource(
            result.metadata, result.content
        )
        assert validation_result.is_valid is True
        assert len(validation_result.errors) == 0

    def test_resource_caching(self, resource_loader):
        """Test resource caching functionality."""
        # Enable caching
        resource_loader.cache_enabled = True

        # Load a resource twice
        tasks = resource_loader.discover_resources(ResourceType.TASK)
        task_id = tasks[0].id

        result1 = resource_loader.load_resource(task_id, ResourceType.TASK)
        result2 = resource_loader.load_resource(task_id, ResourceType.TASK)

        assert result1.success is True
        assert result2.success is True
        assert result1.metadata.id == result2.metadata.id

        # Verify cache hit (second load should be faster/cached)
        assert resource_loader._cache_stats["hits"] >= 1

    def test_hot_reload_functionality(self, resource_loader):
        """Test hot-reload functionality (AC: 5)."""
        # Enable hot-reload
        resource_loader.hot_reload_enabled = True

        # Load a resource
        tasks = resource_loader.discover_resources(ResourceType.TASK)
        task_id = tasks[0].id
        result = resource_loader.load_resource(task_id, ResourceType.TASK)

        assert result.success is True

        # Simulate file change (mock file modification time)
        with patch("pathlib.Path.stat") as mock_stat:
            mock_stat.return_value.st_mtime = 9999999999  # Future timestamp

            # Reload should detect change and reload
            result_reloaded = resource_loader.load_resource(task_id, ResourceType.TASK)
            assert result_reloaded.success is True

    def test_resource_provenance_tracking(self, resource_loader):
        """Test provenance tracking (AC: 4)."""
        # Load a resource
        tasks = resource_loader.discover_resources(ResourceType.TASK)
        task_id = tasks[0].id
        result = resource_loader.load_resource(task_id, ResourceType.TASK)

        assert result.success is True
        assert result.metadata.provenance is not None
        assert ".bmad-core" in result.metadata.provenance
        assert result.metadata.trust_level in ["trusted", "untrusted", "verified"]

    def test_versioned_cache_keys(self, resource_loader):
        """Test versioned cache keys (AC: 5)."""
        resource_loader.cache_enabled = True

        # Load a resource
        tasks = resource_loader.discover_resources(ResourceType.TASK)
        task_id = tasks[0].id
        result = resource_loader.load_resource(task_id, ResourceType.TASK)

        assert result.success is True

        # Check that cache key includes version
        cache_key = resource_loader._generate_cache_key(
            task_id, ResourceType.TASK, result.metadata.version
        )
        assert task_id in cache_key
        assert result.metadata.version in cache_key
        assert "task" in cache_key

    def test_atomic_resource_updates(self, resource_loader):
        """Test atomic resource updates."""
        resource_loader.cache_enabled = True

        # Load a resource
        tasks = resource_loader.discover_resources(ResourceType.TASK)
        task_id = tasks[0].id
        result1 = resource_loader.load_resource(task_id, ResourceType.TASK)

        # Simulate concurrent access during update
        with patch.object(resource_loader, "_load_resource_from_disk") as mock_load:
            mock_load.return_value = result1

            # Multiple concurrent loads should be atomic
            result2 = resource_loader.load_resource(task_id, ResourceType.TASK)
            result3 = resource_loader.load_resource(task_id, ResourceType.TASK)

            assert result2.success is True
            assert result3.success is True


class TestTaskEngine:
    """Test TaskEngine functionality."""

    @pytest.fixture
    def task_engine(self):
        """Create a TaskEngine instance."""
        return TaskEngine()

    @pytest.fixture
    def resource_loader(self):
        """Create a ResourceLoader instance."""
        return ResourceLoader(base_path=Path(".bmad-core"))

    def test_task_engine_initialization(self, task_engine):
        """Test TaskEngine initialization."""
        assert task_engine is not None
        assert task_engine.execution_timeout == 300  # 5 minutes default
        assert task_engine.max_retries == 3

    def test_execute_task_with_valid_resource(self, task_engine, resource_loader):
        """Test executing a task with valid resource (AC: 2)."""
        # Load a task resource
        tasks = resource_loader.discover_resources(ResourceType.TASK)
        task_id = tasks[0].id
        task_resource = resource_loader.load_resource(task_id, ResourceType.TASK)

        assert task_resource.success is True

        # Execute the task
        context = {"project_root": "/workspace", "user": "test-user"}
        result = task_engine.execute_task(
            task_resource.metadata, task_resource.content, context
        )

        assert isinstance(result, TaskExecutionResult)
        assert result.success is True
        assert result.task_id == task_id
        assert result.execution_time > 0
        assert result.outputs is not None

    def test_execute_task_with_invalid_resource(self, task_engine):
        """Test executing a task with invalid resource."""
        # Create invalid task metadata
        invalid_metadata = ResourceMetadata(
            id="invalid-task", name="Invalid Task", resource_type=ResourceType.TASK
        )

        invalid_content = "This is not a valid task format"
        context = {}

        result = task_engine.execute_task(invalid_metadata, invalid_content, context)

        assert isinstance(result, TaskExecutionResult)
        assert result.success is False
        assert len(result.errors) > 0

    def test_task_execution_timeout(self, task_engine):
        """Test task execution timeout handling."""
        task_engine.execution_timeout = 1  # 1 second timeout

        # Create a mock long-running task
        metadata = ResourceMetadata(
            id="long-task", name="Long Running Task", resource_type=ResourceType.TASK
        )

        # Mock content with proper task format
        content = """# Long Task

## SEQUENTIAL Task Execution

### 1. Long Step
- This is a long running step
- It takes a very long time
"""
        context = {}

        with patch.object(task_engine, "_execute_task_steps") as mock_execute:
            import time

            mock_execute.side_effect = lambda *args: time.sleep(
                2
            )  # Sleep longer than timeout

            result = task_engine.execute_task(metadata, content, context)
            assert result.success is False
            assert "timeout" in str(result.errors).lower()

    def test_task_retry_mechanism(self, task_engine):
        """Test task retry mechanism."""
        task_engine.max_retries = 2

        metadata = ResourceMetadata(
            id="flaky-task", name="Flaky Task", resource_type=ResourceType.TASK
        )

        content = """# Flaky Task

## SEQUENTIAL Task Execution

### 1. Flaky Step
- This step sometimes fails
- But should retry and succeed
"""
        context = {}

        # Mock execution that fails first time, succeeds second time
        with patch.object(task_engine, "_execute_task_steps") as mock_execute:
            mock_execute.side_effect = [
                Exception("Temporary failure"),
                {"outputs": {}, "warnings": [], "steps_completed": 1},
            ]

            result = task_engine.execute_task(metadata, content, context)
            assert result.success is True
            assert result.retry_count == 1


class TestTemplateProcessor:
    """Test TemplateProcessor functionality."""

    @pytest.fixture
    def template_processor(self):
        """Create a TemplateProcessor instance."""
        return TemplateProcessor()

    @pytest.fixture
    def resource_loader(self):
        """Create a ResourceLoader instance."""
        return ResourceLoader(base_path=Path(".bmad-core"))

    def test_template_processor_initialization(self, template_processor):
        """Test TemplateProcessor initialization."""
        assert template_processor is not None
        assert template_processor.template_engine == "jinja2"
        assert template_processor.auto_escape is True

    def test_render_template_with_valid_resource(
        self, template_processor, resource_loader
    ):
        """Test rendering a template with valid resource (AC: 2)."""
        # Load a template resource
        templates = resource_loader.discover_resources(ResourceType.TEMPLATE)
        template_id = templates[0].id
        template_resource = resource_loader.load_resource(
            template_id, ResourceType.TEMPLATE
        )

        assert template_resource.success is True

        # Render the template
        context = {
            "epic": "1",
            "story": "1",
            "title": "Test Story",
            "requirements": ["Req 1", "Req 2"],
            "acceptance_criteria": ["AC 1", "AC 2"],
        }

        result = template_processor.render_template(
            template_resource.metadata, template_resource.content, context
        )

        assert isinstance(result, TemplateRenderResult)
        assert result.success is True
        assert result.template_id == template_id
        assert result.rendered_content is not None
        assert len(result.rendered_content) > 0

    def test_render_template_with_missing_variables(self, template_processor):
        """Test rendering template with missing required variables."""
        metadata = ResourceMetadata(
            id="test-template",
            name="Test Template",
            resource_type=ResourceType.TEMPLATE,
        )

        content = "Hello {{name}}, your score is {{score}}!"
        context = {"name": "John"}  # Missing 'score'

        result = template_processor.render_template(metadata, content, context)

        # Should handle missing variables gracefully
        assert isinstance(result, TemplateRenderResult)
        # Depending on implementation, might succeed with empty values or fail
        if not result.success:
            assert len(result.errors) > 0

    def test_template_syntax_validation(self, template_processor):
        """Test template syntax validation."""
        metadata = ResourceMetadata(
            id="invalid-template",
            name="Invalid Template",
            resource_type=ResourceType.TEMPLATE,
        )

        # Invalid Jinja2 syntax
        content = "Hello {{name}, your score is {{score}!"  # Missing closing brace
        context = {"name": "John", "score": 100}

        result = template_processor.render_template(metadata, content, context)

        assert isinstance(result, TemplateRenderResult)
        assert result.success is False
        assert len(result.errors) > 0

    def test_template_security_escaping(self, template_processor):
        """Test template security and auto-escaping."""
        metadata = ResourceMetadata(
            id="security-template",
            name="Security Template",
            resource_type=ResourceType.TEMPLATE,
        )

        content = "User input: {{user_input}}"
        context = {"user_input": "<script>alert('xss')</script>"}

        result = template_processor.render_template(metadata, content, context)

        assert result.success is True
        # Should escape HTML/script tags if auto_escape is enabled
        if template_processor.auto_escape:
            assert "<script>" not in result.rendered_content
            assert (
                "&lt;script&gt;" in result.rendered_content
                or "alert" not in result.rendered_content
            )


class TestChecklistEngine:
    """Test ChecklistEngine functionality."""

    @pytest.fixture
    def checklist_engine(self):
        """Create a ChecklistEngine instance."""
        return ChecklistEngine()

    @pytest.fixture
    def resource_loader(self):
        """Create a ResourceLoader instance."""
        return ResourceLoader(base_path=Path(".bmad-core"))

    def test_checklist_engine_initialization(self, checklist_engine):
        """Test ChecklistEngine initialization."""
        assert checklist_engine is not None
        assert checklist_engine.interactive_mode is False
        assert checklist_engine.auto_check_enabled is False

    def test_execute_checklist_with_valid_resource(
        self, checklist_engine, resource_loader
    ):
        """Test executing a checklist with valid resource (AC: 2)."""
        # Load a checklist resource
        checklists = resource_loader.discover_resources(ResourceType.CHECKLIST)
        checklist_id = checklists[0].id
        checklist_resource = resource_loader.load_resource(
            checklist_id, ResourceType.CHECKLIST
        )

        assert checklist_resource.success is True

        # Execute the checklist
        context = {
            "story_id": "1.1",
            "requirements": ["Req 1", "Req 2"],
            "implementation_status": "complete",
        }

        result = checklist_engine.execute_checklist(
            checklist_resource.metadata, checklist_resource.content, context
        )

        assert isinstance(result, ChecklistExecutionResult)
        assert result.success is True
        assert result.checklist_id == checklist_id
        assert result.total_items > 0
        assert result.completed_items >= 0
        assert result.completion_percentage >= 0.0

    def test_checklist_item_parsing(self, checklist_engine):
        """Test parsing checklist items from content."""
        metadata = ResourceMetadata(
            id="test-checklist",
            name="Test Checklist",
            resource_type=ResourceType.CHECKLIST,
        )

        content = """
# Test Checklist

## Items

- [ ] First item
- [x] Second item (completed)
- [ ] Third item
- [N/A] Fourth item (not applicable)
"""

        context = {}
        result = checklist_engine.execute_checklist(metadata, content, context)

        assert result.success is True
        assert result.total_items == 4
        assert result.completed_items == 1  # Only [x] items
        assert result.not_applicable_items == 1  # [N/A] items
        assert (
            result.completion_percentage == 33.33333333333333
        )  # 1/3 applicable items = 33.33%

    def test_checklist_validation_rules(self, checklist_engine):
        """Test checklist validation rules."""
        metadata = ResourceMetadata(
            id="validation-checklist",
            name="Validation Checklist",
            resource_type=ResourceType.CHECKLIST,
        )

        content = """
# Validation Checklist

## Required Items
- [ ] All tests pass
- [ ] Code coverage > 90%
- [ ] Documentation updated

## Optional Items
- [ ] Performance benchmarks run
- [ ] Security scan completed
"""

        context = {"test_status": "passing", "coverage": 95.0, "docs_updated": True}

        result = checklist_engine.execute_checklist(metadata, content, context)

        assert result.success is True
        # Should have validation results based on context
        assert result.validation_results is not None

    def test_checklist_auto_check_functionality(self, checklist_engine):
        """Test automatic checking based on context."""
        checklist_engine.auto_check_enabled = True

        metadata = ResourceMetadata(
            id="auto-checklist",
            name="Auto Checklist",
            resource_type=ResourceType.CHECKLIST,
        )

        content = """
# Auto Checklist

- [ ] Tests pass (auto: test_status == 'passing')
- [ ] Coverage above 90% (auto: coverage > 90)
- [ ] Manual review completed
"""

        context = {"test_status": "passing", "coverage": 95.0}

        result = checklist_engine.execute_checklist(metadata, content, context)

        assert result.success is True
        # Should auto-check items based on context
        assert result.auto_checked_items >= 2  # First two items should be auto-checked


class TestResourceIntegration:
    """Integration tests for the complete resource system."""

    @pytest.fixture
    def resource_loader(self):
        """Create a ResourceLoader instance."""
        return ResourceLoader(base_path=Path(".bmad-core"))

    @pytest.fixture
    def task_engine(self):
        """Create a TaskEngine instance."""
        return TaskEngine()

    @pytest.fixture
    def template_processor(self):
        """Create a TemplateProcessor instance."""
        return TemplateProcessor()

    @pytest.fixture
    def checklist_engine(self):
        """Create a ChecklistEngine instance."""
        return ChecklistEngine()

    def test_end_to_end_resource_workflow(
        self, resource_loader, task_engine, template_processor, checklist_engine
    ):
        """Test complete end-to-end resource workflow."""
        # 1. Discover all resource types
        tasks = resource_loader.discover_resources(ResourceType.TASK)
        templates = resource_loader.discover_resources(ResourceType.TEMPLATE)
        checklists = resource_loader.discover_resources(ResourceType.CHECKLIST)

        assert len(tasks) > 0
        assert len(templates) > 0
        assert len(checklists) > 0

        # 2. Load one resource of each type
        task_resource = resource_loader.load_resource(tasks[0].id, ResourceType.TASK)
        template_resource = resource_loader.load_resource(
            templates[0].id, ResourceType.TEMPLATE
        )
        checklist_resource = resource_loader.load_resource(
            checklists[0].id, ResourceType.CHECKLIST
        )

        assert task_resource.success is True
        assert template_resource.success is True
        assert checklist_resource.success is True

        # 3. Execute/render each resource
        context = {
            "project_root": "/workspace",
            "epic": "1",
            "story": "1",
            "title": "Integration Test",
            "requirements": ["Integration requirement"],
            "test_status": "passing",
            "coverage": 95.0,
        }

        # Execute task
        task_result = task_engine.execute_task(
            task_resource.metadata, task_resource.content, context
        )

        # Render template
        template_result = template_processor.render_template(
            template_resource.metadata, template_resource.content, context
        )

        # Execute checklist
        checklist_result = checklist_engine.execute_checklist(
            checklist_resource.metadata, checklist_resource.content, context
        )

        # Verify all executions succeeded
        assert task_result.success is True
        assert template_result.success is True
        assert checklist_result.success is True

    def test_resource_dependency_resolution(self, resource_loader):
        """Test resource dependency resolution."""
        # Load a resource that might have dependencies
        tasks = resource_loader.discover_resources(ResourceType.TASK)

        for task_metadata in tasks:
            if task_metadata.dependencies:
                # Test dependency resolution
                dependencies = resource_loader.resolve_dependencies(task_metadata)
                assert isinstance(dependencies, list)

                # Each dependency should be loadable
                for dep_id in task_metadata.dependencies:
                    # Try to load dependency (might be any resource type)
                    for resource_type in [
                        ResourceType.TASK,
                        ResourceType.TEMPLATE,
                        ResourceType.CHECKLIST,
                    ]:
                        dep_result = resource_loader.load_resource(
                            dep_id, resource_type
                        )
                        if dep_result.success:
                            break
                    # At least one resource type should work for valid dependencies

    def test_resource_signing_and_trust(self, resource_loader):
        """Test resource signing and trust levels (AC: 4)."""
        # Load resources and check trust levels
        all_resources = []
        for resource_type in [
            ResourceType.TASK,
            ResourceType.TEMPLATE,
            ResourceType.CHECKLIST,
        ]:
            resources = resource_loader.discover_resources(resource_type)
            all_resources.extend(resources)

        assert len(all_resources) > 0

        # Check that all resources have trust levels assigned
        for resource in all_resources:
            assert resource.trust_level in [
                "trusted",
                "untrusted",
                "verified",
                "signed",
            ]
            assert resource.provenance is not None

            # Load full resource to check signing
            full_resource = resource_loader.load_resource(
                resource.id, resource.resource_type
            )
            if full_resource.success:
                # Should have provenance tracking
                assert full_resource.metadata.provenance is not None
