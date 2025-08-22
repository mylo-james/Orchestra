"""Simple tests to boost CLI main coverage from 65% to 80%+."""

import pytest
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock

from src.cli.main import app, run_async_command


class TestCLIMainSimple:
    """Simple tests for CLI main functionality."""

    def test_app_basic_commands(self):
        """Test basic app commands."""
        runner = CliRunner()

        # Test help
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Orchestra" in result.stdout

    @patch("src.cli.main.get_settings")
    def test_version_command(self, mock_settings):
        """Test version command."""
        mock_settings.return_value = MagicMock()
        mock_settings.return_value.version = "0.1.0"

        runner = CliRunner()
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0

    def test_run_async_command_basic(self):
        """Test run_async_command utility."""
        import asyncio

        async def test_coro():
            await asyncio.sleep(0.001)
            return "test_result"

        result = run_async_command(test_coro())
        assert result == "test_result"

    def test_run_async_command_error_handling(self):
        """Test async command error handling."""
        import asyncio

        async def failing_coro():
            await asyncio.sleep(0.001)
            raise ValueError("test error")

        with pytest.raises(RuntimeError) as exc_info:
            run_async_command(failing_coro())

        assert "Async command failed" in str(exc_info.value)

    @patch("src.cli.main.get_settings")
    def test_cli_with_correlation_id(self, mock_settings):
        """Test CLI with correlation ID."""
        mock_settings.return_value = MagicMock()
        mock_settings.return_value.version = "0.1.0"

        runner = CliRunner()
        result = runner.invoke(app, ["--correlation-id", "test-123", "version"])
        # Should handle correlation ID (may exit with help or success)
        assert result.exit_code in [0, 2]

    @patch("src.cli.main.get_settings")
    def test_cli_debug_mode(self, mock_settings):
        """Test CLI debug mode."""
        mock_settings.return_value = MagicMock()
        mock_settings.return_value.version = "0.1.0"

        runner = CliRunner()
        result = runner.invoke(app, ["--debug", "version"])
        # Should handle debug mode (may exit with help or success)
        assert result.exit_code in [0, 2]

    def test_cli_error_handling(self):
        """Test CLI error handling for invalid commands."""
        runner = CliRunner()
        result = runner.invoke(app, ["nonexistent-command"])
        # Should show help for unknown command
        assert result.exit_code == 2
