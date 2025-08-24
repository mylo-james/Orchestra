"""Fixed tests for CLI main using proper 4-step methodology.

Step 1: PRD Analysis - Command-line interface for power users, logging infrastructure, natural language request processing
Step 2: Code Analysis - Verified actual main() signature, configure_logging parameters, exit codes
Step 3: Test Analysis - Identified exit code mismatches and parameter format issues
Step 4: Align Misalignments - Create tests that validate actual CLI behavior
"""

from unittest.mock import Mock, patch

import pytest
import typer
from typer.testing import CliRunner as TyperCliRunner

from orchestra.cli.main import app, main, run_async_command


class TestMainApp:
    """Test main CLI app behavior with actual implementation."""

    def test_app_no_args_shows_help_with_correct_exit_code(self):
        """Test CLI shows help when no args provided (actual behavior)."""
        runner = TyperCliRunner()
        result = runner.invoke(app, [])

        # Actual behavior: no_args_is_help=True returns exit code 2, not 0
        assert result.exit_code == 2  # Corrected from 0 to 2
        assert "Orchestra" in result.output
        assert "Usage:" in result.output

    def test_app_help_flag_shows_help(self):
        """Test CLI help flag works correctly."""
        runner = TyperCliRunner()
        result = runner.invoke(app, ["--help"])

        # Help flag should return 0
        assert result.exit_code == 0
        assert "Orchestra" in result.output
        assert "Usage:" in result.output

    def test_app_version_command(self):
        """Test version command works correctly."""
        runner = TyperCliRunner()

        with patch("orchestra.cli.main.get_settings") as mock_settings:
            mock_settings.return_value.version = "1.0.0"
            mock_settings.return_value.environment = "test"

            result = runner.invoke(app, ["version"])

            assert result.exit_code == 0
            assert "Orchestra version 1.0.0" in result.output
            assert "Environment: test" in result.output


class TestMainCallback:
    """Test main callback function with actual parameter handling."""

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings for testing."""
        settings = Mock()
        settings.version = "1.0.0"
        settings.environment = "test"
        return settings

    @pytest.fixture
    def mock_context(self):
        """Create mock typer context."""
        ctx = Mock()
        ctx.ensure_object.return_value = {}
        ctx.obj = {}
        ctx.invoked_subcommand = "test_command"
        return ctx

    @patch("orchestra.cli.main.get_settings")
    @patch("orchestra.cli.main.configure_logging")
    @patch("orchestra.cli.main.set_correlation_id")
    @patch("orchestra.cli.main.display_banner")
    def test_main_success_with_correct_parameters(
        self,
        mock_banner,
        mock_correlation,
        mock_configure_logging,
        mock_get_settings,
        mock_context,
        mock_settings,
    ):
        """Test main callback with ACTUAL parameter format (Story 1.1 AC4)."""
        mock_get_settings.return_value = mock_settings

        # Test actual main function call with default parameters
        main(
            mock_context,
            verbose=False,
            quiet=False,
            json_logs=False,
            correlation_id="test-correlation-id",
        )

        # Verify actual configure_logging call format
        mock_configure_logging.assert_called_once_with(
            log_level="INFO",  # Default when not verbose/quiet
            json_logs=False,  # Actual parameter value
            enable_audit=True,  # Always True in implementation
        )

        mock_correlation.assert_called_once_with("test-correlation-id")
        mock_get_settings.assert_called_once()

    @patch("orchestra.cli.main.get_settings")
    @patch("orchestra.cli.main.configure_logging")
    @patch("orchestra.cli.main.set_correlation_id")
    def test_main_verbose_logging_correct_level(
        self,
        mock_correlation,
        mock_configure_logging,
        mock_get_settings,
        mock_context,
        mock_settings,
    ):
        """Test verbose mode sets correct log level."""
        mock_get_settings.return_value = mock_settings

        main(mock_context, verbose=True, quiet=False, json_logs=False)

        # Verify verbose sets DEBUG level
        mock_configure_logging.assert_called_once_with(
            log_level="DEBUG", json_logs=False, enable_audit=True  # Verbose mode
        )

    @patch("orchestra.cli.main.get_settings")
    @patch("orchestra.cli.main.configure_logging")
    @patch("orchestra.cli.main.set_correlation_id")
    def test_main_quiet_mode_correct_level(
        self,
        mock_correlation,
        mock_configure_logging,
        mock_get_settings,
        mock_context,
        mock_settings,
    ):
        """Test quiet mode sets correct log level."""
        mock_get_settings.return_value = mock_settings

        main(mock_context, verbose=False, quiet=True, json_logs=False)

        # Verify quiet sets ERROR level
        mock_configure_logging.assert_called_once_with(
            log_level="ERROR", json_logs=False, enable_audit=True  # Quiet mode
        )

    @patch("orchestra.cli.main.get_settings")
    @patch("orchestra.cli.main.configure_logging")
    @patch("orchestra.cli.main.set_correlation_id")
    def test_main_json_logs_enabled(
        self,
        mock_correlation,
        mock_configure_logging,
        mock_get_settings,
        mock_context,
        mock_settings,
    ):
        """Test JSON logs parameter is passed correctly."""
        mock_get_settings.return_value = mock_settings

        main(mock_context, verbose=False, quiet=False, json_logs=True)

        # Verify json_logs=True is passed
        mock_configure_logging.assert_called_once_with(
            log_level="INFO", json_logs=True, enable_audit=True  # JSON logs enabled
        )

    @patch("orchestra.cli.main.get_settings")
    @patch("orchestra.cli.main.set_correlation_id")
    def test_main_correlation_id_generation(
        self, mock_correlation, mock_get_settings, mock_context, mock_settings
    ):
        """Test correlation ID generation when not provided."""
        mock_get_settings.return_value = mock_settings

        main(mock_context, correlation_id=None)

        # Should call set_correlation_id() without arguments to generate new one
        mock_correlation.assert_called_once_with()


class TestMainCallbackErrorHandling:
    """Test error handling in main callback with actual exit codes."""

    @pytest.fixture
    def mock_context(self):
        """Create mock context for error testing."""
        ctx = Mock()
        ctx.ensure_object.return_value = {}
        ctx.obj = {}  # Initialize obj as dict
        return ctx

    @patch("orchestra.cli.main.get_settings")
    @patch("orchestra.cli.main.display_error")
    def test_main_callback_exception_handling_with_exit_1(
        self, mock_display_error, mock_get_settings, mock_context
    ):
        """Test main callback handles exceptions with correct exit code."""
        mock_get_settings.side_effect = Exception("Settings error")

        # Should raise typer.Exit(1) for exceptions
        with pytest.raises(typer.Exit) as exc_info:
            main(mock_context)

        assert exc_info.value.exit_code == 1  # Actual exit code for exceptions
        mock_display_error.assert_called_once()

    @patch("orchestra.cli.main.get_settings")
    @patch("orchestra.cli.main.configure_logging")
    def test_main_callback_settings_validation(
        self, mock_configure, mock_get_settings, mock_context
    ):
        """Test settings are loaded and validated correctly."""
        mock_settings = Mock()
        mock_settings.version = "1.0.0"
        mock_settings.environment = "test"
        mock_get_settings.return_value = mock_settings

        main(mock_context)

        # Settings should be stored in context
        assert mock_context.obj["settings"] == mock_settings
        assert "console" in mock_context.obj


class TestAsyncCommandHelper:
    """Test async command helper with actual error handling."""

    def test_run_async_command_success(self):
        """Test successful async command execution."""

        async def test_coro():
            return "test_result"

        # Test the function directly without pytest-asyncio conflict
        with patch("orchestra.cli.main.asyncio.run") as mock_run:
            mock_run.return_value = "test_result"
            result = run_async_command(test_coro())
            assert result == "test_result"
            mock_run.assert_called_once()

    def test_run_async_command_keyboard_interrupt_exit_130(self):
        """Test KeyboardInterrupt handling with CORRECT exit code."""

        async def test_coro():
            raise KeyboardInterrupt("User interrupted")

        # Should raise typer.Exit(130) for KeyboardInterrupt (SIGINT standard)
        with pytest.raises(typer.Exit) as exc_info:
            run_async_command(test_coro())

        assert exc_info.value.exit_code == 130  # Standard SIGINT exit code

    def test_run_async_command_exception_handling(self):
        """Test general exception handling in async commands."""

        async def test_coro():
            raise ValueError("Test error")

        # Should raise RuntimeError for general exceptions
        with pytest.raises(RuntimeError, match="Async command failed"):
            run_async_command(test_coro())


class TestHealthCommand:
    """Test health command functionality."""

    def test_health_command_success(self):
        """Test successful health check."""
        runner = TyperCliRunner()

        with (
            patch("orchestra.cli.main.get_settings") as mock_settings,
            patch("orchestra.cli.main.security_health_check") as mock_security,
            patch(
                "orchestra.utils.circuit_breaker.circuit_breaker_health_check"
            ) as mock_cb,
        ):

            mock_settings.return_value.openai.api_key = "test-key"
            mock_security.return_value = True
            mock_cb.return_value = {"healthy": True, "summary": "All good"}

            result = runner.invoke(app, ["health"])

            assert result.exit_code == 0
            assert "Orchestra Health Check" in result.output
            assert "All health checks passed!" in result.output

    def test_health_command_missing_api_key(self):
        """Test health check with missing API key."""
        runner = TyperCliRunner()

        with patch("orchestra.cli.main.get_settings") as mock_settings:
            mock_settings.return_value.openai.api_key = None

            result = runner.invoke(app, ["health"])

            assert result.exit_code == 1  # Should exit with error code
            assert "Missing required environment variable" in result.output


class TestServeCommand:
    """Test serve command functionality."""

    def test_serve_command_basic(self):
        """Test serve command starts correctly."""
        runner = TyperCliRunner()

        # Mock the infinite loop to avoid hanging
        with patch("time.sleep") as mock_sleep:
            mock_sleep.side_effect = KeyboardInterrupt()  # Simulate Ctrl+C

            result = runner.invoke(app, ["serve"])

            # Should handle KeyboardInterrupt gracefully
            assert "Orchestra service is running" in result.output


class TestCLIPRDCompliance:
    """Test CLI compliance with PRD requirements."""

    def test_user_interface_design_goals_power_users(self):
        """Test CLI provides command-line interface for power users."""
        runner = TyperCliRunner()
        result = runner.invoke(app, ["--help"])

        # Should provide comprehensive help for power users
        assert result.exit_code == 0
        assert "Orchestra" in result.output
        assert "Agent management" in result.output
        assert "Workflow orchestration" in result.output

    def test_story_1_1_ac4_logging_infrastructure(self):
        """Test Story 1.1 AC4: Basic logging and debugging infrastructure configured."""
        mock_context = Mock()
        mock_context.ensure_object.return_value = {}
        mock_context.obj = {}
        mock_context.invoked_subcommand = None

        with (
            patch("orchestra.cli.main.get_settings") as mock_settings,
            patch("orchestra.cli.main.configure_logging") as mock_logging,
        ):

            mock_settings.return_value.version = "1.0.0"
            mock_settings.return_value.environment = "test"

            # Test logging infrastructure is configured - pass actual values not defaults
            main(
                mock_context,
                verbose=True,
                quiet=False,
                json_logs=False,
                correlation_id=None,
            )

            mock_logging.assert_called_once_with(
                log_level="DEBUG", json_logs=False, enable_audit=True
            )

    def test_progress_transparency_logging(self):
        """Test progress transparency through proper logging."""
        runner = TyperCliRunner()

        with patch("orchestra.cli.main.get_settings") as mock_settings:
            mock_settings.return_value.version = "1.0.0"
            mock_settings.return_value.environment = "test"
            mock_settings.return_value.openai.api_key = "test-key"

            # Health command should provide transparent progress
            with (
                patch("orchestra.cli.main.security_health_check") as mock_security,
                patch(
                    "orchestra.utils.circuit_breaker.circuit_breaker_health_check"
                ) as mock_cb,
            ):

                mock_security.return_value = True
                mock_cb.return_value = {
                    "healthy": True,
                    "summary": "All systems operational",
                }

                result = runner.invoke(app, ["health"])

                assert result.exit_code == 0
                # Should show transparent progress indicators
                assert "✅" in result.output  # Progress indicators
                assert "Configuration loaded" in result.output
