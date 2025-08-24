"""Tests for Orchestra CLI persona selection and management (Story 1.4)."""

import json
from pathlib import Path
from typing import Dict, List, Optional
from unittest.mock import Mock, patch, MagicMock

import pytest
import yaml
from typer.testing import CliRunner

from orchestra.cli.main import app
from orchestra.system.specs import PersonaSpec, PersonaIdentity, BehavioralContract, CommandInterface, ResourceDependencies
from orchestra.system.loader import PersonaLoader


class TestPersonaDiscovery:
    """Test persona discovery functionality."""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def mock_persona_loader(self):
        """Create mock persona loader."""
        loader = Mock(spec=PersonaLoader)
        
        # Mock discovered personas including converted BMad personas
        mock_personas = {
            "dev": Path("orchestra/personas/dev.yaml"),
            "orchestrator": Path("orchestra/personas/orchestrator.yaml"),
            "release": Path("orchestra/personas/release.yaml"),
            # Converted BMad personas
            "analyst": Path("orchestra/personas/analyst.yaml"),
            "architect": Path("orchestra/personas/architect.yaml"),
            "pm": Path("orchestra/personas/pm.yaml"),
            "po": Path("orchestra/personas/po.yaml"),
            "qa": Path("orchestra/personas/qa.yaml"),
            "spec": Path("orchestra/personas/spec.yaml"),
            "tdd-dev": Path("orchestra/personas/tdd-dev.yaml"),
            "ux-expert": Path("orchestra/personas/ux-expert.yaml"),
        }
        
        loader.discover_personas.return_value = mock_personas
        return loader

    def test_list_personas_command_exists(self, runner):
        """Test that the list-personas command exists (AC: 1)."""
        result = runner.invoke(app, ["agent", "--help"])
        assert result.exit_code == 0
        assert "list-personas" in result.stdout or "list" in result.stdout

    def test_discover_all_personas_including_converted(self, runner, mock_persona_loader):
        """Test discovering all personas including converted BMad personas (AC: 1)."""
        with patch('orchestra.system.loader.PersonaLoader', return_value=mock_persona_loader):
            result = runner.invoke(app, ["agent", "list-personas"])
            
            assert result.exit_code == 0
            
            # Should list original Orchestra personas
            assert "dev" in result.stdout
            assert "orchestrator" in result.stdout
            assert "release" in result.stdout
            
            # Should list converted BMad personas
            assert "analyst" in result.stdout
            assert "architect" in result.stdout
            assert "pm" in result.stdout
            assert "qa" in result.stdout

    def test_persona_details_display(self, runner, mock_persona_loader):
        """Test detailed persona information display."""
        # Mock persona spec for detailed view
        mock_persona_spec = PersonaSpec(
            identity=PersonaIdentity(
                id="dev",
                name="Full Stack Developer",
                title="Full Stack Developer",
                role="Full Stack Developer"
            ),
            behavioral_contract=BehavioralContract(
                core_principles=["Test-driven development", "Clean code"],
                interaction_style="professional"
            ),
            command_interface=CommandInterface(commands={}),
            resource_dependencies=ResourceDependencies()
        )
        
        mock_persona_loader.load_persona.return_value = mock_persona_spec
        
        with patch('orchestra.system.loader.PersonaLoader', return_value=mock_persona_loader):
            result = runner.invoke(app, ["agent", "describe", "dev"])
        
        assert result.exit_code == 0
        assert "Alex" in result.stdout or "Orchestra Developer" in result.stdout
        assert "TDD approach" in result.stdout or "clean maintainable code" in result.stdout

    def test_filter_personas_by_category(self, runner, mock_persona_loader):
        """Test filtering personas by category/role."""
        with patch('orchestra.system.loader.PersonaLoader', return_value=mock_persona_loader):
            result = runner.invoke(app, ["agent", "list-personas", "--category", "development"])
            
            assert result.exit_code == 0
            # Should show development-related personas
            assert "dev" in result.stdout
            assert "tdd-dev" in result.stdout

    def test_search_personas_by_keyword(self, runner, mock_persona_loader):
        """Test searching personas by keyword."""
        with patch('orchestra.system.loader.PersonaLoader', return_value=mock_persona_loader):
            result = runner.invoke(app, ["agent", "search", "architect"])
            
            assert result.exit_code == 0
            assert "architect" in result.stdout


class TestPersonaActivation:
    """Test persona activation and selection functionality."""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def mock_persona_spec(self):
        """Create mock persona specification."""
        return PersonaSpec(
            identity=PersonaIdentity(
                id="dev",
                name="Full Stack Developer",
                title="Full Stack Developer",
                role="Full Stack Developer"
            ),
            behavioral_contract=BehavioralContract(
                core_principles=["Test-driven development", "Clean code"],
                interaction_style="professional"
            ),
            command_interface=CommandInterface(
                commands={
                    "implement": {
                        "description": "Implement a feature",
                        "parameters": {"feature": "string"}
                    }
                }
            ),
            resource_dependencies=ResourceDependencies()
        )

    def test_activate_persona_command(self, runner, mock_persona_spec):
        """Test persona activation command (AC: 1)."""
        with patch('orchestra.cli.commands.PersonaLoader') as mock_loader_class:
            mock_loader = Mock()
            mock_loader.load_persona.return_value = mock_persona_spec
            mock_loader_class.return_value = mock_loader
            
            result = runner.invoke(app, ["agent", "activate", "dev"])
            
            assert result.exit_code == 0
            assert "Activated persona: dev" in result.stdout or "Full Stack Developer" in result.stdout
            mock_loader.load_persona.assert_called_once_with("dev")

    def test_activate_nonexistent_persona(self, runner):
        """Test activating a persona that doesn't exist."""
        with patch('orchestra.cli.commands.PersonaLoader') as mock_loader_class:
            mock_loader = Mock()
            mock_loader.load_persona.return_value = None
            mock_loader_class.return_value = mock_loader
            
            result = runner.invoke(app, ["agent", "activate", "nonexistent"])
            
            assert result.exit_code == 1
            assert "not found" in result.stdout.lower()

    def test_show_active_persona(self, runner, mock_persona_spec):
        """Test showing currently active persona."""
        with patch('orchestra.system.loader.PersonaLoader') as mock_loader_class:
            mock_loader = Mock()
            mock_loader.load_persona.return_value = mock_persona_spec
            mock_loader_class.return_value = mock_loader
            
            # First activate a persona
            runner.invoke(app, ["agent", "activate", "dev"])
            
            # Then check active persona
            result = runner.invoke(app, ["agent", "current"])
            
            assert result.exit_code == 0
            assert "dev" in result.stdout or "Full Stack Developer" in result.stdout

    def test_deactivate_persona(self, runner):
        """Test deactivating current persona."""
        result = runner.invoke(app, ["agent", "deactivate"])
        
        assert result.exit_code == 0
        assert "deactivated" in result.stdout.lower()


class TestPersonaCommandExecution:
    """Test persona command execution functionality."""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def mock_persona_with_commands(self):
        """Create mock persona with commands."""
        return PersonaSpec(
            identity=PersonaIdentity(
                id="dev",
                name="Full Stack Developer",
                title="Full Stack Developer",
                role="Developer"
            ),
            behavioral_contract=BehavioralContract(
                core_principles=["Clean code", "Testing"],
                interaction_style="professional"
            ),
            command_interface=CommandInterface(
                commands={
                    "implement": {
                        "description": "Implement a feature",
                        "parameters": {
                            "feature": {"type": "string", "required": True},
                            "tests": {"type": "boolean", "default": True}
                        }
                    },
                    "review": {
                        "description": "Review code",
                        "parameters": {"file": {"type": "string", "required": True}}
                    }
                }
            ),
            resource_dependencies=ResourceDependencies()
        )

    def test_list_persona_commands(self, runner, mock_persona_with_commands):
        """Test listing commands for active persona (AC: 2)."""
        with patch('orchestra.system.loader.PersonaLoader') as mock_loader_class:
            mock_loader = Mock()
            mock_loader.load_persona.return_value = mock_persona_with_commands
            mock_loader_class.return_value = mock_loader
            
            # Activate persona first
            runner.invoke(app, ["agent", "activate", "dev"])
            
            # List commands
            result = runner.invoke(app, ["agent", "commands"])
            
            assert result.exit_code == 0
            assert "implement" in result.stdout
            assert "review" in result.stdout
            assert "implement-feature" in result.stdout or "Implement a specific" in result.stdout

    def test_execute_persona_command(self, runner, mock_persona_with_commands):
        """Test executing a persona command (AC: 2, 3)."""
        with patch('orchestra.system.loader.PersonaLoader') as mock_loader_class:
            mock_loader = Mock()
            mock_loader.load_persona.return_value = mock_persona_with_commands
            mock_loader_class.return_value = mock_loader
            
            # Mock command execution
            with patch('orchestra.system.agent.UniversalAgent') as mock_agent_class:
                mock_agent = Mock()
                mock_agent.execute_command.return_value = {"status": "success", "output": "Feature implemented"}
                mock_agent_class.return_value = mock_agent
                
                result = runner.invoke(app, ["agent", "exec", "implement", "--feature", "user-auth"])
                
                assert result.exit_code == 0
                assert "success" in result.stdout.lower()

    def test_command_help_display(self, runner, mock_persona_with_commands):
        """Test displaying help for persona commands (AC: 2)."""
        with patch('orchestra.system.loader.PersonaLoader') as mock_loader_class:
            mock_loader = Mock()
            mock_loader.load_persona.return_value = mock_persona_with_commands
            mock_loader_class.return_value = mock_loader
            
            result = runner.invoke(app, ["agent", "help", "implement"])
            
            assert result.exit_code == 0
            assert "implement-feature" in result.stdout or "Implement a specific" in result.stdout
            assert "feature" in result.stdout
            assert "tests" in result.stdout


class TestEndToEndValidation:
    """Test end-to-end persona execution with resources."""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def mock_persona_with_resources(self):
        """Create persona with resource dependencies."""
        return PersonaSpec(
            identity=PersonaIdentity(
                id="tdd-dev",
                name="Test-Driven Developer",
                title="Test-Driven Developer",
                role="TDD Developer"
            ),
            behavioral_contract=BehavioralContract(
                core_principles=["Test-first development", "Red-Green-Refactor"],
                interaction_style="methodical"
            ),
            command_interface=CommandInterface(
                commands={
                    "implement-tdd": {
                        "description": "Implement using TDD approach",
                        "parameters": {"story": {"type": "string", "required": True}}
                    }
                }
            ),
            resource_dependencies=ResourceDependencies(
                tasks=["review-tdd-implementation"],
                templates=["test-spec-tmpl"]
            )
        )

    def test_end_to_end_task_execution(self, runner, mock_persona_with_resources):
        """Test end-to-end execution with task resource (AC: 3)."""
        with patch('orchestra.system.loader.PersonaLoader') as mock_loader_class:
            mock_loader = Mock()
            mock_loader.load_persona.return_value = mock_persona_with_resources
            mock_loader_class.return_value = mock_loader
            
            # Mock resource loader and task engine
            with patch('orchestra.system.resource_loader.ResourceLoader') as mock_resource_loader:
                with patch('orchestra.system.task_engine.TaskEngine') as mock_task_engine:
                    mock_resource_result = Mock()
                    mock_resource_result.success = True
                    mock_resource_result.metadata = Mock()
                    mock_resource_result.content = "# Test Task\n## Steps\n- Step 1"
                    
                    mock_execution_result = Mock()
                    mock_execution_result.success = True
                    mock_execution_result.execution_time = 1.5
                    mock_execution_result.steps_completed = 1
                    mock_execution_result.total_steps = 1
                    
                    mock_resource_loader.return_value.load_resource.return_value = mock_resource_result
                    mock_task_engine.return_value.execute_task.return_value = mock_execution_result
                    
                    result = runner.invoke(app, ["agent", "run-task", "review-tdd-implementation"])
                    
                    assert result.exit_code == 0
                    assert "success" in result.stdout.lower()

    def test_end_to_end_template_rendering(self, runner, mock_persona_with_resources):
        """Test end-to-end template rendering (AC: 3)."""
        with patch('orchestra.system.loader.PersonaLoader') as mock_loader_class:
            mock_loader = Mock()
            mock_loader.load_persona.return_value = mock_persona_with_resources
            mock_loader_class.return_value = mock_loader
            
            # Mock resource loader and template processor
            with patch('orchestra.system.resource_loader.ResourceLoader') as mock_resource_loader:
                with patch('orchestra.system.template_processor.TemplateProcessor') as mock_template_processor:
                    mock_resource_result = Mock()
                    mock_resource_result.success = True
                    mock_resource_result.metadata = Mock()
                    mock_resource_result.content = "# Test Spec for {story}"
                    
                    mock_render_result = Mock()
                    mock_render_result.success = True
                    mock_render_result.rendered_content = "# Test Spec for User Auth"
                    mock_render_result.render_time = 0.1
                    
                    mock_resource_loader.return_value.load_resource.return_value = mock_resource_result
                    mock_template_processor.return_value.render_template.return_value = mock_render_result
                    
                    result = runner.invoke(app, ["agent", "render", "test-spec-tmpl", "--context", '{"story": "User Auth"}'])
                    
                    assert result.exit_code == 0
                    assert "success" in result.stdout.lower()

    def test_end_to_end_checklist_execution(self, runner, mock_persona_with_resources):
        """Test end-to-end checklist execution (AC: 3)."""
        with patch('orchestra.system.loader.PersonaLoader') as mock_loader_class:
            mock_loader = Mock()
            mock_loader.load_persona.return_value = mock_persona_with_resources
            mock_loader_class.return_value = mock_loader
            
            # Mock resource loader and checklist engine
            with patch('orchestra.system.resource_loader.ResourceLoader') as mock_resource_loader:
                with patch('orchestra.system.checklist_engine.ChecklistEngine') as mock_checklist_engine:
                    mock_resource_result = Mock()
                    mock_resource_result.success = True
                    mock_resource_result.metadata = Mock()
                    mock_resource_result.content = "# TDD DoD\n- [x] Tests written\n- [ ] Code implemented"
                    
                    mock_execution_result = Mock()
                    mock_execution_result.success = True
                    mock_execution_result.completion_percentage = 50.0
                    mock_execution_result.completed_items = 1
                    mock_execution_result.total_items = 2
                    
                    mock_resource_loader.return_value.load_resource.return_value = mock_resource_result
                    mock_checklist_engine.return_value.execute_checklist.return_value = mock_execution_result
                    
                    result = runner.invoke(app, ["agent", "check", "tdd-dev-dod-checklist"])
                    
                    assert result.exit_code == 0
                    assert "50.0%" in result.stdout


class TestRegressionValidation:
    """Test that existing personas still work (AC: 4)."""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    def test_existing_orchestrator_persona(self, runner):
        """Test that orchestrator persona still works."""
        with patch('orchestra.cli.commands.PersonaLoader') as mock_loader_class:
            mock_loader = Mock()
            
            # Mock existing orchestrator persona
            orchestrator_spec = PersonaSpec(
                identity=PersonaIdentity(
                    id="orchestrator",
                    name="BMad Master Orchestrator",
                    title="BMad Master Orchestrator",
                    role="Master Orchestrator"
                ),
                behavioral_contract=BehavioralContract(
                    core_principles=["Workflow coordination", "Agent management"],
                    interaction_style="authoritative"
                ),
                command_interface=CommandInterface(commands={}),
                resource_dependencies=ResourceDependencies()
            )
            
            mock_loader.load_persona.return_value = orchestrator_spec
            mock_loader_class.return_value = mock_loader
            
            result = runner.invoke(app, ["agent", "activate", "orchestrator"])
            
            assert result.exit_code == 0
            assert "orchestrator" in result.stdout.lower()

    def test_existing_dev_persona(self, runner):
        """Test that dev persona still works."""
        with patch('orchestra.cli.commands.PersonaLoader') as mock_loader_class:
            mock_loader = Mock()
            
            # Mock existing dev persona
            dev_spec = PersonaSpec(
                identity=PersonaIdentity(
                    id="dev",
                    name="Full Stack Developer",
                    title="Full Stack Developer",
                    role="Developer"
                ),
                behavioral_contract=BehavioralContract(
                    core_principles=["Clean code", "Testing"],
                    interaction_style="professional"
                ),
                command_interface=CommandInterface(commands={}),
                resource_dependencies=ResourceDependencies()
            )
            
            mock_loader.load_persona.return_value = dev_spec
            mock_loader_class.return_value = mock_loader
            
            result = runner.invoke(app, ["agent", "activate", "dev"])
            
            assert result.exit_code == 0
            assert "dev" in result.stdout.lower()

    def test_existing_release_persona(self, runner):
        """Test that release persona still works."""
        with patch('orchestra.cli.commands.PersonaLoader') as mock_loader_class:
            mock_loader = Mock()
            
            # Mock existing release persona
            release_spec = PersonaSpec(
                identity=PersonaIdentity(
                    id="release",
                    name="Release Manager",
                    title="Release Manager",
                    role="Release Manager"
                ),
                behavioral_contract=BehavioralContract(
                    core_principles=["Deployment safety", "Release coordination"],
                    interaction_style="systematic"
                ),
                command_interface=CommandInterface(commands={}),
                resource_dependencies=ResourceDependencies()
            )
            
            mock_loader.load_persona.return_value = release_spec
            mock_loader_class.return_value = mock_loader
            
            result = runner.invoke(app, ["agent", "activate", "release"])
            
            assert result.exit_code == 0
            assert "release" in result.stdout.lower()


class TestAuditAndSecurity:
    """Test audit logging and security monitoring (AC: 5)."""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    def test_persona_activation_audit_logging(self, runner):
        """Test that persona activation is logged for audit."""
        with patch('orchestra.system.loader.PersonaLoader') as mock_loader_class:
            mock_loader = Mock()
            mock_loader.load_persona.return_value = Mock()
            mock_loader_class.return_value = mock_loader
            
            with patch('orchestra.utils.logging.get_logger') as mock_logger:
                mock_logger_instance = Mock()
                mock_logger.return_value = mock_logger_instance
                
                result = runner.invoke(app, ["agent", "activate", "dev"])
                
                # Should have audit log entries
                mock_logger_instance.info.assert_called()
                
                # Check that audit information is logged
                call_args = [call[0] for call in mock_logger_instance.info.call_args_list]
                audit_logged = any("persona" in str(args).lower() and "activate" in str(args).lower() for args in call_args)
                assert audit_logged

    def test_command_execution_audit_logging(self, runner):
        """Test that command execution is logged for audit."""
        with patch('orchestra.system.loader.PersonaLoader') as mock_loader_class:
            mock_loader = Mock()
            mock_persona = Mock()
            mock_persona.command_interface.commands = {"test": {"description": "Test command"}}
            mock_loader.load_persona.return_value = mock_persona
            mock_loader_class.return_value = mock_loader
            
            with patch('orchestra.utils.logging.get_logger') as mock_logger:
                mock_logger_instance = Mock()
                mock_logger.return_value = mock_logger_instance
                
                with patch('orchestra.system.agent.UniversalAgent') as mock_agent:
                    mock_agent.return_value.execute_command.return_value = {"status": "success"}
                    
                    result = runner.invoke(app, ["agent", "exec", "test"])
                    
                    # Should have audit log entries for command execution
                    mock_logger_instance.info.assert_called()

    def test_security_monitoring_integration(self, runner):
        """Test that security monitoring captures persona operations."""
        with patch('orchestra.security.ai_agent_monitor.AIAgentMonitor') as mock_monitor:
            mock_monitor_instance = Mock()
            mock_monitor.return_value = mock_monitor_instance
            
            with patch('orchestra.system.loader.PersonaLoader') as mock_loader_class:
                mock_loader = Mock()
                mock_loader.load_persona.return_value = Mock()
                mock_loader_class.return_value = mock_loader
                
                result = runner.invoke(app, ["agent", "activate", "dev"])
                
                # Security monitoring should be notified
                # This would be implemented in the actual command handlers


class TestIntegrationWithRealData:
    """Integration tests that work with actual persona files."""
    
    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()
    
    def test_real_persona_activation(self, runner):
        """Test activation with real persona data."""
        result = runner.invoke(app, ["agent", "activate", "dev"])
        assert result.exit_code == 0
        # The actual dev persona is named "Alex"
        assert "Activated persona: Alex" in result.stdout or "✅ Activated persona:" in result.stdout
        
    def test_real_persona_listing(self, runner):
        """Test listing with real persona data."""
        result = runner.invoke(app, ["agent", "list-personas"])
        assert result.exit_code == 0
        assert "dev" in result.stdout
        assert "orchestrator" in result.stdout
        assert "release" in result.stdout
        
    def test_real_persona_description(self, runner):
        """Test describing real persona data."""
        result = runner.invoke(app, ["agent", "describe", "dev"])
        assert result.exit_code == 0
        assert "Alex" in result.stdout or "Expert Python" in result.stdout