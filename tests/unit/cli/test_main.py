"""Tests for CLI main module."""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from typer.testing import CliRunner

from src.cli.main import app, main, run_async_command


class TestMainApp:
    """Test main CLI application."""

    @pytest.fixture
    def runner(self):
        """Create a CLI runner for testing."""
        return CliRunner()

    def test_app_creation(self):
        """Test that the main app is created correctly."""
        assert app.info.name == "orchestra"
        assert "Orchestra - AI Agent System" in app.info.help
        assert app.rich_markup_mode == "rich"
        # no_args_is_help is a TyperInfo property
        assert app.info.no_args_is_help is True

    def test_app_help(self, runner):
        """Test that the app shows help correctly."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Orchestra - AI Agent System" in result.stdout
        assert "agent" in result.stdout
        assert "workflow" in result.stdout
        assert "config" in result.stdout
        assert "dev" in result.stdout
        assert "security" in result.stdout
        assert "circuit-breakers" in result.stdout

    def test_app_no_args_shows_help(self, runner):
        """Test that app shows help when no arguments provided."""
        result = runner.invoke(app, [])
        assert result.exit_code == 0
        assert "Orchestra - AI Agent System" in result.stdout

    def test_agent_subcommand_help(self, runner):
        """Test agent subcommand help."""
        result = runner.invoke(app, ["agent", "--help"])
        assert result.exit_code == 0
        assert "Agent management commands" in result.stdout

    def test_workflow_subcommand_help(self, runner):
        """Test workflow subcommand help."""
        result = runner.invoke(app, ["workflow", "--help"])
        assert result.exit_code == 0
        assert "Workflow orchestration commands" in result.stdout

    def test_config_subcommand_help(self, runner):
        """Test config subcommand help."""
        result = runner.invoke(app, ["config", "--help"])
        assert result.exit_code == 0
        assert "Configuration management commands" in result.stdout

    def test_dev_subcommand_help(self, runner):
        """Test dev subcommand help."""
        result = runner.invoke(app, ["dev", "--help"])
        assert result.exit_code == 0
        assert "Development and debugging commands" in result.stdout

    def test_security_subcommand_help(self, runner):
        """Test security subcommand help."""
        result = runner.invoke(app, ["security", "--help"])
        assert result.exit_code == 0
        assert "AI Agent security monitoring commands" in result.stdout

    def test_circuit_breakers_subcommand_help(self, runner):
        """Test circuit-breakers subcommand help."""
        result = runner.invoke(app, ["circuit-breakers", "--help"])
        assert result.exit_code == 0
        assert "External service circuit breaker commands" in result.stdout


class TestMainCallback:
    """Test main callback function."""

    @pytest.fixture
    def mock_context(self):
        """Create a mock Typer context."""
        context = Mock()
        context.ensure_object = Mock()
        context.invoked_subcommand = "test"
        context.obj = {}  # Make it a real dict for assignment
        return context

    @patch('src.cli.main.set_correlation_id')
    @patch('src.cli.main.get_settings')
    @patch('src.cli.main.configure_logging')
    @patch('src.cli.main.display_banner')
    def test_main_success(self, mock_display_banner, mock_configure_logging, 
                         mock_get_settings, mock_set_correlation_id, mock_context):
        """Test successful main callback execution."""
        mock_settings = Mock()
        mock_settings.version = "1.0.0"
        mock_get_settings.return_value = mock_settings
        
        # Test with default parameters
        main(mock_context)
        
        # Verify logging was configured
        mock_configure_logging.assert_called_once_with(
            log_level="INFO", 
            json_logs=False, 
            enable_audit=True
        )
        
        # Verify correlation ID was set
        mock_set_correlation_id.assert_called_once()
        
        # Verify settings were loaded
        mock_get_settings.assert_called_once()
        
        # Verify banner was displayed
        mock_display_banner.assert_called_once()

    @patch('src.cli.main.set_correlation_id')
    @patch('src.cli.main.get_settings')
    @patch('src.cli.main.configure_logging')
    @patch('src.cli.main.display_banner')
    def test_main_verbose_logging(self, mock_display_banner, mock_configure_logging,
                                 mock_get_settings, mock_set_correlation_id, mock_context):
        """Test main callback with verbose logging."""
        mock_settings = Mock()
        mock_settings.version = "1.0.0"
        mock_get_settings.return_value = mock_settings
        
        # Test with verbose flag
        main(mock_context, verbose=True)
        
        # Verify logging was configured with DEBUG level
        mock_configure_logging.assert_called_once_with(
            log_level="DEBUG", 
            json_logs=False, 
            enable_audit=True
        )

    @patch('src.cli.main.set_correlation_id')
    @patch('src.cli.main.get_settings')
    @patch('src.cli.main.configure_logging')
    @patch('src.cli.main.display_banner')
    def test_main_quiet_mode(self, mock_display_banner, mock_configure_logging,
                            mock_get_settings, mock_set_correlation_id, mock_context):
        """Test main callback with quiet mode."""
        mock_settings = Mock()
        mock_settings.version = "1.0.0"
        mock_get_settings.return_value = mock_settings
        
        # Test with quiet flag
        main(mock_context, quiet=True)
        
        # Verify logging was configured with ERROR level
        mock_configure_logging.assert_called_once_with(
            log_level="ERROR", 
            json_logs=False, 
            enable_audit=True
        )

    @patch('src.cli.main.set_correlation_id')
    @patch('src.cli.main.get_settings')
    @patch('src.cli.main.configure_logging')
    @patch('src.cli.main.display_banner')
    def test_main_json_logs(self, mock_display_banner, mock_configure_logging,
                           mock_get_settings, mock_set_correlation_id, mock_context):
        """Test main callback with JSON logs."""
        mock_settings = Mock()
        mock_settings.version = "1.0.0"
        mock_get_settings.return_value = mock_settings
        
        # Test with JSON logs flag
        main(mock_context, json_logs=True)
        
        # Verify logging was configured with JSON logs
        mock_configure_logging.assert_called_once_with(
            log_level="INFO", 
            json_logs=True, 
            enable_audit=True
        )

    @patch('src.cli.main.set_correlation_id')
    @patch('src.cli.main.get_settings')
    @patch('src.cli.main.configure_logging')
    @patch('src.cli.main.display_banner')
    def test_main_custom_correlation_id(self, mock_display_banner, mock_configure_logging,
                                       mock_get_settings, mock_set_correlation_id, mock_context):
        """Test main callback with custom correlation ID."""
        mock_settings = Mock()
        mock_settings.version = "1.0.0"
        mock_get_settings.return_value = mock_settings
        
        # Test with custom correlation ID
        main(mock_context, correlation_id="test-correlation-123")
        
        # Verify correlation ID was set with custom value
        mock_set_correlation_id.assert_called_once_with("test-correlation-123")

    @patch('src.cli.main.set_correlation_id')
    @patch('src.cli.main.get_settings')
    @patch('src.cli.main.configure_logging')
    @patch('src.cli.main.display_banner')
    def test_main_help_mode_no_banner(self, mock_display_banner, mock_configure_logging,
                                     mock_get_settings, mock_set_correlation_id, mock_context):
        """Test main callback in help mode (no banner displayed)."""
        mock_settings = Mock()
        mock_settings.version = "1.0.0"
        mock_get_settings.return_value = mock_settings
        
        # Set context to help mode
        mock_context.invoked_subcommand = "help"
        
        # Test main callback
        main(mock_context)
        
        # Verify banner was not displayed in help mode
        mock_display_banner.assert_not_called()

    @patch('src.cli.main.set_correlation_id')
    @patch('src.cli.main.get_settings')
    @patch('src.cli.main.configure_logging')
    @patch('src.cli.main.display_banner')
    def test_main_quiet_mode_no_banner(self, mock_display_banner, mock_configure_logging,
                                      mock_get_settings, mock_set_correlation_id, mock_context):
        """Test main callback in quiet mode (no banner displayed)."""
        mock_settings = Mock()
        mock_settings.version = "1.0.0"
        mock_get_settings.return_value = mock_settings
        
        # Test with quiet flag
        main(mock_context, quiet=True)
        
        # Verify banner was not displayed in quiet mode
        mock_display_banner.assert_not_called()

    @patch('src.cli.main.set_correlation_id')
    @patch('src.cli.main.get_settings')
    @patch('src.cli.main.configure_logging')
    @patch('src.cli.main.display_banner')
    def test_main_context_object_setup(self, mock_display_banner, mock_configure_logging,
                                      mock_get_settings, mock_set_correlation_id, mock_context):
        """Test that context object is properly set up."""
        mock_settings = Mock()
        mock_settings.version = "1.0.0"
        mock_get_settings.return_value = mock_settings
        
        # Test main callback
        main(mock_context)
        
        # Verify context object was ensured
        mock_context.ensure_object.assert_called_once_with(dict)
        
        # Verify settings and console were stored in context
        assert mock_context.obj["settings"] == mock_settings
        assert "console" in mock_context.obj


class TestAppIntegration:
    """Test app integration with subcommands."""

    @pytest.fixture
    def runner(self):
        """Create a CLI runner for testing."""
        return CliRunner()

    @patch('src.cli.commands.get_registry')
    def test_agent_start_integration(self, mock_get_registry, runner):
        """Test agent start command integration."""
        mock_registry = Mock()
        mock_get_registry.return_value = mock_registry
        mock_registry.list_personas.return_value = ["test-persona"]
        
        # Mock persona spec
        mock_spec = Mock()
        mock_spec.identity.icon = "🚀"
        mock_spec.identity.name = "Test Persona"
        mock_spec.identity.title = "Test Title"
        mock_registry.get_persona_spec.return_value = mock_spec
        
        # Test agent list command
        result = runner.invoke(app, ["agent", "list"])
        assert result.exit_code == 0

    @patch('src.cli.commands.PersonaLoader')
    def test_personas_integration(self, mock_loader_class, runner):
        """Test personas command integration."""
        mock_loader = Mock()
        mock_loader_class.return_value = mock_loader
        mock_loader.list_personas.return_value = ["test-persona"]
        
        # Mock persona spec
        mock_spec = Mock()
        mock_spec.identity.name = "Test Persona"
        mock_spec.identity.role = "Test Role"
        mock_spec.identity.icon = "🚀"
        mock_loader.load_persona.return_value = mock_spec
        
        # Test personas command
        result = runner.invoke(app, ["agent", "personas"])
        assert result.exit_code == 0


class TestVersionCommand:
    """Test version command."""

    @pytest.fixture
    def runner(self):
        """Create a CLI runner for testing."""
        return CliRunner()

    @patch('src.cli.main.get_settings')
    def test_version_command(self, mock_get_settings, runner):
        """Test version command displays version information."""
        mock_settings = Mock()
        mock_settings.version = "1.2.3"
        mock_settings.environment = "test"
        mock_get_settings.return_value = mock_settings
        
        result = runner.invoke(app, ["version"])
        
        assert result.exit_code == 0
        assert "Orchestra" in result.stdout
        assert "1.2.3" in result.stdout
        assert "test" in result.stdout


class TestServeCommand:
    """Test serve command."""

    @pytest.fixture
    def runner(self):
        """Create a CLI runner for testing."""
        return CliRunner()

    @patch('time.sleep')  # Mock sleep to prevent infinite loop
    @patch('src.cli.main.display_success')
    @patch('src.cli.main.logger')
    def test_serve_command_default_params(self, mock_logger, mock_display_success, mock_sleep, runner):
        """Test serve command with default parameters."""
        # Mock sleep to raise KeyboardInterrupt immediately
        mock_sleep.side_effect = KeyboardInterrupt("Simulated Ctrl+C")
        
        result = runner.invoke(app, ["serve"])
        
        # Should start successfully but be interrupted
        assert result.exit_code == 0  # KeyboardInterrupt in serve should return 0
        mock_display_success.assert_called_once()
        mock_logger.info.assert_called()

    @patch('time.sleep')  # Mock sleep to prevent infinite loop
    @patch('src.cli.main.display_success')
    @patch('src.cli.main.logger')
    def test_serve_command_custom_params(self, mock_logger, mock_display_success, mock_sleep, runner):
        """Test serve command with custom host and port."""
        # Mock sleep to raise KeyboardInterrupt immediately
        mock_sleep.side_effect = KeyboardInterrupt("Simulated Ctrl+C")
        
        result = runner.invoke(app, ["serve", "--host", "0.0.0.0", "--port", "9000"])
        
        assert result.exit_code == 0  # KeyboardInterrupt in serve should return 0
        mock_display_success.assert_called_once()
        mock_logger.info.assert_called()

    @patch('time.sleep')  # Mock sleep to prevent infinite loop
    @patch('src.cli.main.display_success')
    @patch('src.cli.main.logger')
    def test_serve_command_with_reload(self, mock_logger, mock_display_success, mock_sleep, runner):
        """Test serve command with reload enabled."""
        # Mock sleep to raise KeyboardInterrupt immediately
        mock_sleep.side_effect = KeyboardInterrupt("Simulated Ctrl+C")
        
        result = runner.invoke(app, ["serve", "--reload"])
        
        assert result.exit_code == 0  # KeyboardInterrupt in serve should return 0
        mock_display_success.assert_called_once()
        # Verify reload logging
        assert any("auto-reload" in str(call) for call in mock_logger.info.call_args_list)


class TestHealthCommand:
    """Test health command."""

    @pytest.fixture
    def runner(self):
        """Create a CLI runner for testing."""
        return CliRunner()

    @patch('src.utils.circuit_breaker.circuit_breaker_health_check')
    @patch('src.cli.main.security_health_check')
    @patch('src.cli.main.get_settings')
    @patch('src.cli.main.display_success')
    def test_health_command_success(self, mock_display_success, mock_get_settings, 
                                   mock_security_health, mock_cb_health, runner):
        """Test successful health check."""
        # Mock settings with OpenAI API key
        mock_settings = Mock()
        mock_settings.openai.api_key = "test-key"
        mock_get_settings.return_value = mock_settings
        
        # Mock health checks
        mock_security_health.return_value = True
        mock_cb_health.return_value = {
            "healthy": True,
            "summary": "All services operational",
            "failing_services": []
        }
        
        result = runner.invoke(app, ["health"])
        
        assert result.exit_code == 0
        mock_display_success.assert_called_once()
        assert "Health Check" in result.stdout

    @patch('src.cli.main.get_settings')
    def test_health_command_missing_api_key(self, mock_get_settings, runner):
        """Test health check with missing API key."""
        # Mock settings without OpenAI API key
        mock_settings = Mock()
        mock_settings.openai.api_key = None
        mock_get_settings.return_value = mock_settings
        
        result = runner.invoke(app, ["health"])
        
        assert result.exit_code == 1
        assert "Missing required environment variable" in result.stdout

    @patch('src.utils.circuit_breaker.circuit_breaker_health_check')
    @patch('src.cli.main.security_health_check')
    @patch('src.cli.main.get_settings')
    def test_health_command_with_warnings(self, mock_get_settings, mock_security_health, 
                                         mock_cb_health, runner):
        """Test health check with warnings."""
        # Mock settings
        mock_settings = Mock()
        mock_settings.openai.api_key = "test-key"
        mock_get_settings.return_value = mock_settings
        
        # Mock health checks with issues
        mock_security_health.return_value = False
        mock_cb_health.return_value = {
            "healthy": False,
            "summary": "Some services failing",
            "failing_services": ["openai", "github"]
        }
        
        result = runner.invoke(app, ["health"])
        
        assert result.exit_code == 0  # Still passes but with warnings
        assert "may have issues" in result.stdout
        assert "issues detected" in result.stdout
        assert "openai" in result.stdout
        assert "github" in result.stdout


class TestAsyncCommandHelper:
    """Test async command helper function."""

    @patch('src.cli.main.asyncio.run')
    def test_run_async_command_success(self, mock_asyncio_run):
        """Test successful async command execution."""
        from src.cli.main import run_async_command
        
        async def test_coro():
            return "success"
        
        mock_asyncio_run.return_value = "success"
        
        result = run_async_command(test_coro())
        
        assert result == "success"
        mock_asyncio_run.assert_called_once()

    @patch('src.cli.main.asyncio.run')
    @patch('src.cli.main.console')
    def test_run_async_command_keyboard_interrupt(self, mock_console, mock_asyncio_run):
        """Test async command with keyboard interrupt."""
        from src.cli.main import run_async_command
        
        async def test_coro():
            return "success"
        
        mock_asyncio_run.side_effect = KeyboardInterrupt()
        
        with pytest.raises(SystemExit) as exc_info:
            run_async_command(test_coro())
        
        assert exc_info.value.code == 130
        mock_console.print.assert_called_once()

    @patch('src.cli.main.asyncio.run')
    @patch('src.cli.main.logger')
    def test_run_async_command_exception(self, mock_logger, mock_asyncio_run):
        """Test async command with exception."""
        from src.cli.main import run_async_command
        
        async def test_coro():
            return "success"
        
        mock_asyncio_run.side_effect = RuntimeError("Test error")
        
        with pytest.raises(RuntimeError) as exc_info:
            run_async_command(test_coro())
        
        assert "Async command failed" in str(exc_info.value)
        mock_logger.error.assert_called_once()


class TestMainCallbackErrorHandling:
    """Test main callback error handling."""

    @pytest.fixture
    def mock_context(self):
        """Create a mock Typer context."""
        context = Mock()
        context.ensure_object = Mock()
        context.invoked_subcommand = "test"
        context.obj = {}  # Make it a real dict for assignment
        return context

    @patch('src.cli.main.get_settings')
    @patch('src.cli.main.display_error')
    @patch('src.cli.main.logger')
    def test_main_callback_exception_handling(self, mock_logger, mock_display_error, 
                                             mock_get_settings, mock_context):
        """Test main callback handles exceptions properly."""
        mock_get_settings.side_effect = Exception("Settings error")
        
        with pytest.raises(SystemExit) as exc_info:
            main(mock_context)
        
        assert exc_info.value.code == 1
        mock_display_error.assert_called_once()
        mock_logger.error.assert_called_once()


class TestServeCommandErrorHandling:
    """Test serve command error handling."""

    @pytest.fixture
    def runner(self):
        """Create a CLI runner for testing."""
        return CliRunner()

    @patch('src.cli.main.display_success')
    @patch('src.cli.main.display_error')
    @patch('src.cli.main.logger')
    def test_serve_command_exception_handling(self, mock_logger, mock_display_error, 
                                             mock_display_success, runner):
        """Test serve command handles exceptions properly."""
        mock_display_success.side_effect = Exception("Service error")
        
        result = runner.invoke(app, ["serve"])
        
        assert result.exit_code == 1
        mock_display_error.assert_called_once()
        mock_logger.error.assert_called_once()


class TestHealthCommandErrorHandling:
    """Test health command error handling."""

    @pytest.fixture
    def runner(self):
        """Create a CLI runner for testing."""
        return CliRunner()

    @patch('src.cli.main.get_settings')
    @patch('src.cli.main.display_error')
    @patch('src.cli.main.logger')
    def test_health_command_exception_handling(self, mock_logger, mock_display_error, 
                                              mock_get_settings, runner):
        """Test health command handles exceptions properly."""
        mock_get_settings.side_effect = Exception("Settings error")
        
        result = runner.invoke(app, ["health"])
        
        assert result.exit_code == 1
        mock_display_error.assert_called_once()
        mock_logger.error.assert_called_once()
