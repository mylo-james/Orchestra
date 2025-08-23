"""Simple focused tests for CLI main module to contribute to repo-wide 80% coverage."""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from typer.testing import CliRunner

from src.cli.main import app, main, run_async_command


class TestMainAppBasic:
    """Test basic CLI app functionality."""

    @pytest.fixture
    def runner(self):
        """Create a CLI runner for testing."""
        return CliRunner()

    def test_app_help(self, runner):
        """Test that the app shows help correctly."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Orchestra - AI Agent System" in result.stdout

    def test_version_command(self, runner):
        """Test version command."""
        with patch('src.cli.main.get_settings') as mock_settings:
            mock_settings.return_value.version = "1.0.0"
            mock_settings.return_value.environment = "test"
            
            result = runner.invoke(app, ["version"])
            assert result.exit_code == 0
            assert "Orchestra" in result.stdout
            assert "1.0.0" in result.stdout

    @patch('src.cli.main.display_success')
    @patch('src.cli.main.logger')
    def test_serve_command_basic(self, mock_logger, mock_display_success, runner):
        """Test serve command basic functionality."""
        # Simulate Ctrl+C to stop the server
        result = runner.invoke(app, ["serve"], input="\x03")
        mock_display_success.assert_called_once()

    @patch('src.utils.circuit_breaker.circuit_breaker_health_check')
    @patch('src.cli.main.security_health_check')
    @patch('src.cli.main.get_settings')
    def test_health_command_success(self, mock_get_settings, mock_security_health, mock_cb_health, runner):
        """Test health command success."""
        # Mock settings with API key
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
        assert "Health Check" in result.stdout

    @patch('src.cli.main.get_settings')
    def test_health_command_missing_api_key(self, mock_get_settings, runner):
        """Test health command with missing API key."""
        mock_settings = Mock()
        mock_settings.openai.api_key = None
        mock_get_settings.return_value = mock_settings
        
        result = runner.invoke(app, ["health"])
        assert result.exit_code == 1
        assert "Missing required environment variable" in result.stdout


class TestAsyncHelper:
    """Test async command helper."""

    @patch('src.cli.main.asyncio.run')
    def test_run_async_command_success(self, mock_asyncio_run):
        """Test successful async command execution."""
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
        async def test_coro():
            return "success"
        
        mock_asyncio_run.side_effect = KeyboardInterrupt()
        
        # The function raises typer.Exit, which becomes click.exceptions.Exit
        with pytest.raises(Exception) as exc_info:
            run_async_command(test_coro())
        
        # Should be a click.exceptions.Exit with code 130
        assert hasattr(exc_info.value, 'exit_code') and exc_info.value.exit_code == 130
        mock_console.print.assert_called_once()

    @patch('src.cli.main.asyncio.run')
    @patch('src.cli.main.logger')
    def test_run_async_command_exception(self, mock_logger, mock_asyncio_run):
        """Test async command with exception."""
        async def test_coro():
            return "success"
        
        mock_asyncio_run.side_effect = RuntimeError("Test error")
        
        with pytest.raises(RuntimeError):
            run_async_command(test_coro())
        
        mock_logger.error.assert_called_once()


class TestMainCallback:
    """Test main callback function."""

    @patch('src.cli.main.set_correlation_id')
    @patch('src.cli.main.get_settings')
    @patch('src.cli.main.configure_logging')
    @patch('src.cli.main.display_banner')
    @patch('src.cli.main.logger')
    def test_main_callback_success(self, mock_logger, mock_display_banner, 
                                  mock_configure_logging, mock_get_settings, 
                                  mock_set_correlation_id):
        """Test successful main callback execution."""
        # Create a proper mock context
        mock_context = Mock()
        mock_context.ensure_object = Mock()
        mock_context.invoked_subcommand = "test"
        mock_context.obj = {}
        
        # Mock settings
        mock_settings = Mock()
        mock_settings.version = "1.0.0"
        mock_settings.environment = "test"
        mock_get_settings.return_value = mock_settings
        
        # Test main callback
        main(mock_context, verbose=False, quiet=False, json_logs=False, correlation_id=None)
        
        # Verify calls
        mock_configure_logging.assert_called_once()
        mock_set_correlation_id.assert_called_once()
        mock_get_settings.assert_called_once()
        mock_display_banner.assert_called_once()
        mock_logger.info.assert_called_once()

    @patch('src.cli.main.set_correlation_id')
    @patch('src.cli.main.get_settings')
    @patch('src.cli.main.configure_logging')
    @patch('src.cli.main.display_banner')
    @patch('src.cli.main.logger')
    def test_main_callback_verbose(self, mock_logger, mock_display_banner, 
                                  mock_configure_logging, mock_get_settings, 
                                  mock_set_correlation_id):
        """Test main callback with verbose logging."""
        mock_context = Mock()
        mock_context.ensure_object = Mock()
        mock_context.invoked_subcommand = "test"
        mock_context.obj = {}
        
        mock_settings = Mock()
        mock_settings.version = "1.0.0"
        mock_get_settings.return_value = mock_settings
        
        # Test with verbose flag
        main(mock_context, verbose=True, quiet=False, json_logs=False, correlation_id=None)
        
        # Verify DEBUG logging was configured
        mock_configure_logging.assert_called_once_with(
            log_level="DEBUG", json_logs=False, enable_audit=True
        )

    @patch('src.cli.main.set_correlation_id')
    @patch('src.cli.main.get_settings')
    @patch('src.cli.main.configure_logging')
    @patch('src.cli.main.display_banner')
    @patch('src.cli.main.logger')
    def test_main_callback_quiet(self, mock_logger, mock_display_banner, 
                                mock_configure_logging, mock_get_settings, 
                                mock_set_correlation_id):
        """Test main callback with quiet mode."""
        mock_context = Mock()
        mock_context.ensure_object = Mock()
        mock_context.invoked_subcommand = "test"
        mock_context.obj = {}
        
        mock_settings = Mock()
        mock_settings.version = "1.0.0"
        mock_get_settings.return_value = mock_settings
        
        # Test with quiet flag
        main(mock_context, verbose=False, quiet=True, json_logs=False, correlation_id=None)
        
        # Verify ERROR logging was configured and no banner
        mock_configure_logging.assert_called_once_with(
            log_level="ERROR", json_logs=False, enable_audit=True
        )
        mock_display_banner.assert_not_called()

    @patch('src.cli.main.set_correlation_id')
    @patch('src.cli.main.get_settings')
    @patch('src.cli.main.configure_logging')
    @patch('src.cli.main.display_banner')
    @patch('src.cli.main.logger')
    def test_main_callback_json_logs(self, mock_logger, mock_display_banner, 
                                    mock_configure_logging, mock_get_settings, 
                                    mock_set_correlation_id):
        """Test main callback with JSON logs."""
        mock_context = Mock()
        mock_context.ensure_object = Mock()
        mock_context.invoked_subcommand = "test"
        mock_context.obj = {}
        
        mock_settings = Mock()
        mock_settings.version = "1.0.0"
        mock_get_settings.return_value = mock_settings
        
        # Test with JSON logs
        main(mock_context, verbose=False, quiet=False, json_logs=True, correlation_id=None)
        
        # Verify JSON logging was configured
        mock_configure_logging.assert_called_once_with(
            log_level="INFO", json_logs=True, enable_audit=True
        )

    @patch('src.cli.main.set_correlation_id')
    @patch('src.cli.main.get_settings')
    @patch('src.cli.main.configure_logging')
    @patch('src.cli.main.display_banner')
    @patch('src.cli.main.logger')
    def test_main_callback_custom_correlation_id(self, mock_logger, mock_display_banner, 
                                                 mock_configure_logging, mock_get_settings, 
                                                 mock_set_correlation_id):
        """Test main callback with custom correlation ID."""
        mock_context = Mock()
        mock_context.ensure_object = Mock()
        mock_context.invoked_subcommand = "test"
        mock_context.obj = {}
        
        mock_settings = Mock()
        mock_settings.version = "1.0.0"
        mock_get_settings.return_value = mock_settings
        
        # Test with custom correlation ID
        main(mock_context, correlation_id="test-123")
        
        # Verify correlation ID was set
        mock_set_correlation_id.assert_called_once_with("test-123")

    @patch('src.cli.main.get_settings')
    @patch('src.cli.main.display_error')
    @patch('src.cli.main.logger')
    def test_main_callback_exception(self, mock_logger, mock_display_error, mock_get_settings):
        """Test main callback exception handling."""
        mock_context = Mock()
        mock_context.ensure_object = Mock()
        mock_context.invoked_subcommand = "test"
        mock_context.obj = {}
        
        # Mock exception
        mock_get_settings.side_effect = Exception("Settings error")
        
        with pytest.raises(SystemExit) as exc_info:
            main(mock_context, verbose=False, quiet=False, json_logs=False, correlation_id=None)
        
        assert exc_info.value.code == 1
        mock_display_error.assert_called_once()
        mock_logger.error.assert_called_once()


class TestServeCommand:
    """Test serve command functionality."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @patch('src.cli.main.display_success')
    @patch('src.cli.main.display_error')
    @patch('src.cli.main.logger')
    def test_serve_command_exception(self, mock_logger, mock_display_error, 
                                    mock_display_success, runner):
        """Test serve command exception handling."""
        mock_display_success.side_effect = Exception("Service error")
        
        result = runner.invoke(app, ["serve"])
        
        assert result.exit_code == 1
        mock_display_error.assert_called_once()
        mock_logger.error.assert_called_once()

    @patch('src.cli.main.display_success')
    @patch('src.cli.main.logger')
    def test_serve_command_with_params(self, mock_logger, mock_display_success, runner):
        """Test serve command with custom parameters."""
        result = runner.invoke(app, ["serve", "--host", "0.0.0.0", "--port", "9000", "--reload"], input="\x03")
        
        mock_display_success.assert_called_once()
        # Check that reload logging was called
        assert any("auto-reload" in str(call) for call in mock_logger.info.call_args_list)


class TestHealthCommand:
    """Test health command functionality."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @patch('src.utils.circuit_breaker.circuit_breaker_health_check')
    @patch('src.cli.main.security_health_check')
    @patch('src.cli.main.get_settings')
    def test_health_command_with_warnings(self, mock_get_settings, mock_security_health, 
                                         mock_cb_health, runner):
        """Test health command with warnings."""
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

    @patch('src.cli.main.get_settings')
    @patch('src.cli.main.display_error')
    @patch('src.cli.main.logger')
    def test_health_command_exception(self, mock_logger, mock_display_error, 
                                     mock_get_settings, runner):
        """Test health command exception handling."""
        mock_get_settings.side_effect = Exception("Settings error")
        
        result = runner.invoke(app, ["health"])
        
        assert result.exit_code == 1
        mock_display_error.assert_called_once()
        mock_logger.error.assert_called_once()