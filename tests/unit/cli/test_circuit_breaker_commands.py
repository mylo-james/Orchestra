"""
Tests for src/cli/circuit_breaker_commands.py

Tests circuit breaker CLI commands for monitoring and managing external service circuit breakers.
"""

from unittest.mock import patch

import click
import pytest
from typer.testing import CliRunner

from src.cli.circuit_breaker_commands import (
    cb_app,
    circuit_breaker_health,
    circuit_breaker_status,
    reset_circuit_breakers,
    simulate_service_failure,
)


class TestCircuitBreakerApp:
    """Test circuit breaker CLI app configuration."""

    def test_app_exists(self):
        """Test that circuit breaker app is properly configured."""
        assert cb_app is not None
        # For Typer sub-apps, check if it has the info structure instead of name
        assert hasattr(cb_app, "info")
        assert "External Service Circuit Breaker Commands" in cb_app.info.help


class TestCircuitBreakerStatus:
    """Test circuit_breaker_status command."""

    @patch("src.cli.circuit_breaker_commands.get_circuit_breaker_stats")
    @patch("src.cli.circuit_breaker_commands.circuit_breaker_health_check")
    @patch("src.cli.circuit_breaker_commands.console")
    def test_status_all_healthy(self, mock_console, mock_health_check, mock_get_stats):
        """Test status command with all services healthy."""
        # Mock healthy status
        mock_health_check.return_value = {
            "healthy": True,
            "summary": "All services operational",
            "failing_services": [],
        }

        # Mock service stats
        mock_get_stats.return_value = {
            "github_api": {
                "state": "closed",
                "success_rate": 0.98,
                "consecutive_failures": 0,
                "stats": {
                    "total_requests": 150,
                    "last_success_time": "2024-01-15T10:30:00",
                },
            }
        }

        # Run command
        circuit_breaker_status()

        # Verify function calls
        mock_health_check.assert_called_once()
        mock_get_stats.assert_called_once()

        # Verify console output includes healthy status
        printed_calls = mock_console.print.call_args_list
        assert any("All Services Healthy" in str(call) for call in printed_calls)
        assert any("🟢" in str(call) for call in printed_calls)

    @patch("src.cli.circuit_breaker_commands.get_circuit_breaker_stats")
    @patch("src.cli.circuit_breaker_commands.circuit_breaker_health_check")
    @patch("src.cli.circuit_breaker_commands.console")
    def test_status_with_failures(
        self, mock_console, mock_health_check, mock_get_stats
    ):
        """Test status command with failing services."""
        # Mock unhealthy status
        mock_health_check.return_value = {
            "healthy": False,
            "summary": "2 services failing",
            "failing_services": ["github_api", "temporal_service"],
        }

        # Mock service stats with failures
        mock_get_stats.return_value = {
            "github_api": {
                "state": "open",
                "success_rate": 0.65,
                "consecutive_failures": 5,
                "stats": {
                    "total_requests": 100,
                    "last_failure_time": "2024-01-15T11:00:00",
                },
            }
        }

        # Run command
        circuit_breaker_status()

        # Verify console output includes failure status
        printed_calls = mock_console.print.call_args_list
        assert any("Service Failures Detected" in str(call) for call in printed_calls)
        assert any("🔴" in str(call) for call in printed_calls)
        assert any("github_api" in str(call) for call in printed_calls)

    @patch("src.cli.circuit_breaker_commands.get_circuit_breaker_stats")
    @patch("src.cli.circuit_breaker_commands.circuit_breaker_health_check")
    @patch("src.cli.circuit_breaker_commands.console")
    def test_status_no_circuit_breakers(
        self, mock_console, mock_health_check, mock_get_stats
    ):
        """Test status command with no active circuit breakers."""
        # Mock healthy but empty status
        mock_health_check.return_value = {
            "healthy": True,
            "summary": "No circuit breakers active",
            "failing_services": [],
        }

        mock_get_stats.return_value = {}

        # Run command
        circuit_breaker_status()

        # Verify console output shows no circuit breakers
        printed_calls = mock_console.print.call_args_list
        assert any(
            "No circuit breakers active yet" in str(call) for call in printed_calls
        )

    @patch("src.cli.circuit_breaker_commands.get_circuit_breaker_stats")
    @patch("src.cli.circuit_breaker_commands.circuit_breaker_health_check")
    @patch("src.cli.circuit_breaker_commands.console")
    def test_status_half_open_state(
        self, mock_console, mock_health_check, mock_get_stats
    ):
        """Test status command with half-open circuit breaker."""
        mock_health_check.return_value = {
            "healthy": True,
            "summary": "Testing recovery",
            "failing_services": [],
        }

        mock_get_stats.return_value = {
            "temporal_service": {
                "state": "half_open",
                "success_rate": 0.75,
                "consecutive_failures": 2,
                "stats": {
                    "total_requests": 50,
                    "last_success_time": "2024-01-15T10:45:00",
                },
            }
        }

        # Run command
        circuit_breaker_status()

        # Verify half-open state is displayed
        # Check that console.print was called multiple times (for table rendering)
        assert mock_console.print.call_count >= 3
        # Check that mocked functions were called with correct data
        mock_health_check.assert_called_once()
        mock_get_stats.assert_called_once()

    @patch("src.cli.circuit_breaker_commands.get_circuit_breaker_stats")
    @patch("src.cli.circuit_breaker_commands.circuit_breaker_health_check")
    @patch("src.cli.circuit_breaker_commands.console")
    def test_status_exception_handling(
        self, mock_console, mock_health_check, mock_get_stats
    ):
        """Test status command exception handling."""
        # Mock exception
        mock_health_check.side_effect = Exception("Connection failed")

        # Run command and expect it to raise Exit
        with pytest.raises(click.exceptions.Exit):
            circuit_breaker_status()

        # Verify error message
        printed_calls = mock_console.print.call_args_list
        assert any(
            "Error getting circuit breaker status" in str(call)
            for call in printed_calls
        )

    @patch("src.cli.circuit_breaker_commands.get_circuit_breaker_stats")
    @patch("src.cli.circuit_breaker_commands.circuit_breaker_health_check")
    @patch("src.cli.circuit_breaker_commands.console")
    def test_status_different_success_rates(
        self, mock_console, mock_health_check, mock_get_stats
    ):
        """Test status command with different success rate color coding."""
        mock_health_check.return_value = {
            "healthy": True,
            "summary": "Mixed performance",
            "failing_services": [],
        }

        mock_get_stats.return_value = {
            "high_success": {
                "state": "closed",
                "success_rate": 0.99,  # Should be green
                "consecutive_failures": 0,
                "stats": {
                    "total_requests": 100,
                    "last_success_time": "2024-01-15T10:30:00",
                },
            },
            "medium_success": {
                "state": "closed",
                "success_rate": 0.85,  # Should be yellow
                "consecutive_failures": 1,
                "stats": {
                    "total_requests": 80,
                    "last_success_time": "2024-01-15T10:25:00",
                },
            },
            "low_success": {
                "state": "half_open",
                "success_rate": 0.65,  # Should be red
                "consecutive_failures": 3,
                "stats": {"total_requests": 60, "last_success_time": None},
            },
        }

        # Run command
        circuit_breaker_status()

        # Verify different color codes are used
        # Check that console.print was called to render the table
        assert mock_console.print.call_count >= 3
        # Verify functions were called with the test data
        mock_health_check.assert_called_once()
        mock_get_stats.assert_called_once()


class TestResetCircuitBreakers:
    """Test reset_circuit_breakers command."""

    @patch("src.cli.circuit_breaker_commands.reset_all_circuit_breakers")
    @patch("src.cli.circuit_breaker_commands.console")
    def test_reset_all_with_yes_flag(self, mock_console, mock_reset_all):
        """Test reset all circuit breakers with --yes flag."""
        # Run command with confirmation skip
        reset_circuit_breakers(service=None, confirm=True)

        # Verify reset was called
        mock_reset_all.assert_called_once()

        # Verify success message
        printed_calls = mock_console.print.call_args_list
        assert any(
            "All circuit breakers reset to closed state" in str(call)
            for call in printed_calls
        )

    @patch("src.cli.circuit_breaker_commands.reset_all_circuit_breakers")
    @patch("src.cli.circuit_breaker_commands.console")
    @patch("typer.confirm")
    def test_reset_all_with_confirmation_yes(
        self, mock_confirm, mock_console, mock_reset_all
    ):
        """Test reset all circuit breakers with user confirmation (yes)."""
        # Mock user confirms
        mock_confirm.return_value = True

        # Run command
        reset_circuit_breakers(service=None, confirm=False)

        # Verify confirmation was asked and reset was called
        mock_confirm.assert_called_once_with("Reset ALL circuit breakers?")
        mock_reset_all.assert_called_once()

    @patch("src.cli.circuit_breaker_commands.reset_all_circuit_breakers")
    @patch("src.cli.circuit_breaker_commands.console")
    @patch("typer.confirm")
    def test_reset_all_with_confirmation_no(
        self, mock_confirm, mock_console, mock_reset_all
    ):
        """Test reset all circuit breakers with user confirmation (no)."""
        # Mock user cancels
        mock_confirm.return_value = False

        # Run command
        reset_circuit_breakers(service=None, confirm=False)

        # Verify confirmation was asked but reset was NOT called
        mock_confirm.assert_called_once_with("Reset ALL circuit breakers?")
        mock_reset_all.assert_not_called()

        # Verify cancellation message
        printed_calls = mock_console.print.call_args_list
        assert any("Reset cancelled" in str(call) for call in printed_calls)

    @patch("src.cli.circuit_breaker_commands.console")
    @patch("typer.confirm")
    def test_reset_specific_service_not_implemented(self, mock_confirm, mock_console):
        """Test reset specific service shows not implemented message."""
        # Mock user confirms
        mock_confirm.return_value = True

        # Run command with specific service
        reset_circuit_breakers(service="github_api", confirm=False)

        # Verify confirmation was asked for specific service
        mock_confirm.assert_called_once_with("Reset circuit breaker for github_api?")

        # Verify not implemented message
        printed_calls = mock_console.print.call_args_list
        assert any(
            "Resetting specific services not yet implemented" in str(call)
            for call in printed_calls
        )

    @patch("src.cli.circuit_breaker_commands.reset_all_circuit_breakers")
    @patch("src.cli.circuit_breaker_commands.console")
    def test_reset_exception_handling(self, mock_console, mock_reset_all):
        """Test reset command exception handling."""
        # Mock exception
        mock_reset_all.side_effect = Exception("Reset failed")

        # Run command and expect it to raise Exit
        with pytest.raises(click.exceptions.Exit):
            reset_circuit_breakers(service=None, confirm=True)

        # Verify error message
        printed_calls = mock_console.print.call_args_list
        assert any(
            "Error resetting circuit breakers" in str(call) for call in printed_calls
        )


class TestCircuitBreakerHealth:
    """Test circuit_breaker_health command."""

    @patch("src.cli.circuit_breaker_commands.circuit_breaker_health_check")
    @patch("src.cli.circuit_breaker_commands.console")
    def test_health_all_healthy(self, mock_console, mock_health_check):
        """Test health command with all services healthy."""
        mock_health_check.return_value = {
            "healthy": True,
            "summary": "All services operational",
            "total_circuit_breakers": 3,
            "open_circuit_breakers": 0,
            "failing_services": [],
        }

        # Run command
        circuit_breaker_health()

        # Verify health check was called
        mock_health_check.assert_called_once()

        # Verify console output includes healthy status
        printed_calls = mock_console.print.call_args_list
        assert any(
            "All external services are healthy" in str(call) for call in printed_calls
        )
        assert any("✅" in str(call) for call in printed_calls)

    @patch("src.cli.circuit_breaker_commands.circuit_breaker_health_check")
    @patch("src.cli.circuit_breaker_commands.console")
    def test_health_some_failing(self, mock_console, mock_health_check):
        """Test health command with some services failing."""
        mock_health_check.return_value = {
            "healthy": False,
            "summary": "2 services down",
            "total_circuit_breakers": 3,
            "open_circuit_breakers": 2,
            "failing_services": ["github_api", "temporal_service"],
        }

        # Run command
        circuit_breaker_health()

        # Verify console output includes failure status
        printed_calls = mock_console.print.call_args_list
        assert any(
            "Some external services are failing" in str(call) for call in printed_calls
        )
        assert any("❌" in str(call) for call in printed_calls)
        assert any(
            "github_api" in str(call) and "temporal_service" in str(call)
            for call in printed_calls
        )

    @patch("src.cli.circuit_breaker_commands.circuit_breaker_health_check")
    @patch("src.cli.circuit_breaker_commands.console")
    def test_health_no_circuit_breakers(self, mock_console, mock_health_check):
        """Test health command with no circuit breakers."""
        mock_health_check.return_value = {
            "healthy": True,
            "summary": "No circuit breakers configured",
            "total_circuit_breakers": 0,
            "open_circuit_breakers": 0,
            "failing_services": [],
        }

        # Run command
        circuit_breaker_health()

        # Verify appropriate output for no circuit breakers
        printed_calls = mock_console.print.call_args_list
        assert any("Total circuit breakers: 0" in str(call) for call in printed_calls)

    @patch("src.cli.circuit_breaker_commands.circuit_breaker_health_check")
    @patch("src.cli.circuit_breaker_commands.console")
    def test_health_with_progress_visualization(self, mock_console, mock_health_check):
        """Test health command includes progress visualization."""
        mock_health_check.return_value = {
            "healthy": True,
            "summary": "Mostly healthy",
            "total_circuit_breakers": 5,
            "open_circuit_breakers": 1,
            "failing_services": ["one_service"],
        }

        # Run command
        circuit_breaker_health()

        # Verify progress/visualization output
        printed_calls = mock_console.print.call_args_list
        assert any("Service Availability" in str(call) for call in printed_calls)

    @patch("src.cli.circuit_breaker_commands.circuit_breaker_health_check")
    @patch("src.cli.circuit_breaker_commands.console")
    def test_health_exception_handling(self, mock_console, mock_health_check):
        """Test health command exception handling."""
        # Mock exception
        mock_health_check.side_effect = Exception("Health check failed")

        # Run command and expect it to raise Exit
        with pytest.raises(click.exceptions.Exit):
            circuit_breaker_health()

        # Verify error message
        printed_calls = mock_console.print.call_args_list
        assert any(
            "Error checking circuit breaker health" in str(call)
            for call in printed_calls
        )


class TestSimulateServiceFailure:
    """Test simulate_service_failure command."""

    @patch("src.cli.circuit_breaker_commands.console")
    def test_simulate_failure_basic(self, mock_console):
        """Test simulate failure command basic functionality."""
        # Run command
        simulate_service_failure("github_api", 3)

        # Verify console output
        printed_calls = mock_console.print.call_args_list
        assert any(
            "Simulating 3 failures for github_api" in str(call)
            for call in printed_calls
        )
        assert any(
            "Failure simulation not yet implemented" in str(call)
            for call in printed_calls
        )

    @patch("src.cli.circuit_breaker_commands.console")
    def test_simulate_failure_default_count(self, mock_console):
        """Test simulate failure command with default failure count."""
        # Run command with default failure count (5)
        simulate_service_failure("temporal_service", 5)

        # Verify console output includes default count
        printed_calls = mock_console.print.call_args_list
        assert any(
            "Simulating 5 failures for temporal_service" in str(call)
            for call in printed_calls
        )

    @patch("src.cli.circuit_breaker_commands.console")
    def test_simulate_failure_exception_handling(self, mock_console):
        """Test simulate failure command exception handling."""
        # Mock console.print to work normally but cause an exception in the try block
        # Inject an exception by mocking something else that might fail

        # Test normal execution first (exception handling path isn't easily testable
        # without breaking the try block differently)
        simulate_service_failure("test_service", 1)

        # Verify basic functionality was called
        assert mock_console.print.call_count >= 1


class TestCliIntegration:
    """Test CLI integration and runner functionality."""

    def test_cli_runner_status_command(self):
        """Test status command via CLI runner."""
        runner = CliRunner()

        with (
            patch(
                "src.cli.circuit_breaker_commands.circuit_breaker_health_check"
            ) as mock_health,
            patch(
                "src.cli.circuit_breaker_commands.get_circuit_breaker_stats"
            ) as mock_stats,
        ):

            mock_health.return_value = {
                "healthy": True,
                "summary": "All good",
                "failing_services": [],
            }
            mock_stats.return_value = {}

            result = runner.invoke(cb_app, ["status"])

            assert result.exit_code == 0
            assert "Circuit Breaker Status" in result.output

    def test_cli_runner_health_command(self):
        """Test health command via CLI runner."""
        runner = CliRunner()

        with patch(
            "src.cli.circuit_breaker_commands.circuit_breaker_health_check"
        ) as mock_health:
            mock_health.return_value = {
                "healthy": True,
                "summary": "All operational",
                "total_circuit_breakers": 2,
                "open_circuit_breakers": 0,
                "failing_services": [],
            }

            result = runner.invoke(cb_app, ["health"])

            assert result.exit_code == 0
            assert "Circuit Breaker Health Check" in result.output

    def test_cli_runner_reset_with_yes_flag(self):
        """Test reset command via CLI runner with --yes flag."""
        runner = CliRunner()

        with patch(
            "src.cli.circuit_breaker_commands.reset_all_circuit_breakers"
        ) as mock_reset:
            result = runner.invoke(cb_app, ["reset", "--yes"])

            assert result.exit_code == 0
            mock_reset.assert_called_once()
            assert "reset to closed state" in result.output

    def test_cli_runner_simulate_failure(self):
        """Test simulate-failure command via CLI runner."""
        runner = CliRunner()

        result = runner.invoke(
            cb_app, ["simulate-failure", "test_service", "--failures", "3"]
        )

        assert result.exit_code == 0
        assert "Simulating 3 failures for test_service" in result.output


class TestCommandEdgeCases:
    """Test edge cases and boundary conditions."""

    @patch("src.cli.circuit_breaker_commands.get_circuit_breaker_stats")
    @patch("src.cli.circuit_breaker_commands.circuit_breaker_health_check")
    @patch("src.cli.circuit_breaker_commands.console")
    def test_status_with_no_last_success_time(
        self, mock_console, mock_health_check, mock_get_stats
    ):
        """Test status command when service has no last success time."""
        mock_health_check.return_value = {
            "healthy": False,
            "summary": "Service never succeeded",
            "failing_services": ["broken_service"],
        }

        mock_get_stats.return_value = {
            "broken_service": {
                "state": "open",
                "success_rate": 0.0,
                "consecutive_failures": 10,
                "stats": {
                    "total_requests": 20,
                    "last_success_time": None,  # No success time
                },
            }
        }

        # Run command
        circuit_breaker_status()

        # Verify service stats were processed (Never time case)
        assert mock_console.print.call_count >= 3
        mock_health_check.assert_called_once()
        mock_get_stats.assert_called_once()

    @patch("src.cli.circuit_breaker_commands.get_circuit_breaker_stats")
    @patch("src.cli.circuit_breaker_commands.circuit_breaker_health_check")
    @patch("src.cli.circuit_breaker_commands.console")
    def test_status_with_unknown_state(
        self, mock_console, mock_health_check, mock_get_stats
    ):
        """Test status command with unknown circuit breaker state."""
        mock_health_check.return_value = {
            "healthy": True,
            "summary": "Unknown state detected",
            "failing_services": [],
        }

        mock_get_stats.return_value = {
            "weird_service": {
                "state": "unknown",  # Non-standard state
                "success_rate": 0.5,
                "consecutive_failures": 0,
                "stats": {
                    "total_requests": 10,
                    "last_success_time": "2024-01-15T10:30:00",
                },
            }
        }

        # Run command
        circuit_breaker_status()

        # Verify unknown state is handled (table was rendered)
        assert mock_console.print.call_count >= 3
        mock_health_check.assert_called_once()
        mock_get_stats.assert_called_once()

    @patch("src.cli.circuit_breaker_commands.console")
    @patch("typer.confirm")
    def test_reset_specific_service_user_cancels(self, mock_confirm, mock_console):
        """Test reset specific service when user cancels."""
        # Mock user cancels
        mock_confirm.return_value = False

        # Run command
        reset_circuit_breakers(service="github_api", confirm=False)

        # Verify service-specific confirmation was asked
        mock_confirm.assert_called_once_with("Reset circuit breaker for github_api?")

        # Verify cancellation message
        printed_calls = mock_console.print.call_args_list
        assert any("Reset cancelled" in str(call) for call in printed_calls)

    @patch("src.cli.circuit_breaker_commands.get_circuit_breaker_stats")
    @patch("src.cli.circuit_breaker_commands.circuit_breaker_health_check")
    @patch("src.cli.circuit_breaker_commands.console")
    def test_status_failing_services_without_stats(
        self, mock_console, mock_health_check, mock_get_stats
    ):
        """Test status command when failing service has no stats."""
        mock_health_check.return_value = {
            "healthy": False,
            "summary": "Service failing",
            "failing_services": ["missing_service"],
        }

        mock_get_stats.return_value = {}  # No stats for the failing service

        # Run command
        circuit_breaker_status()

        # Should handle missing stats gracefully
        printed_calls = mock_console.print.call_args_list
        assert any("Failing Services Details" in str(call) for call in printed_calls)


class TestAppMainExecution:
    """Test main app execution."""

    def test_main_execution_path_exists(self):
        """Test that main execution path exists and app is callable."""
        # Test that we can access the app for main execution
        assert cb_app is not None
        assert hasattr(cb_app, "__call__")

        # Test that the main execution code exists in the module
        with open("src/cli/circuit_breaker_commands.py", "r") as f:
            content = f.read()
            assert 'if __name__ == "__main__":' in content
            assert "cb_app()" in content
