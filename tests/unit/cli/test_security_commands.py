"""
Tests for orchestra/cli/security_commands.py

Tests security CLI commands for AI agent security monitoring and management.
"""

from unittest.mock import MagicMock, mock_open, patch

import click
import pytest
from typer.testing import CliRunner

from orchestra.cli.security_commands import (
    generate_security_report,
    list_agent_metrics,
    security_app,
    security_status,
    show_security_logs,
    test_security_monitoring,
)


class TestSecurityApp:
    """Test security CLI app configuration."""

    def test_app_exists(self):
        """Test that security app is properly configured."""
        assert security_app is not None
        # For Typer sub-apps, check if it has the info structure instead of name
        assert hasattr(security_app, "info")
        assert "AI Agent Security Monitoring Commands" in security_app.info.help


class TestSecurityStatus:
    """Test security_status command."""

    @patch("orchestra.cli.security_commands.AIAgentSecurityMonitor")
    @patch("orchestra.cli.security_commands.console")
    def test_status_normal_metrics(self, mock_console, mock_monitor_class):
        """Test status command with normal security metrics."""
        # Mock monitor instance and report
        mock_monitor = MagicMock()
        mock_monitor_class.return_value = mock_monitor

        mock_monitor.generate_security_report.return_value = {
            "overall_metrics": {
                "total_operations": 100,
                "security_violations": 2,
                "blocked_operations": 1,
                "last_updated": "2024-01-15T10:30:00",
            },
            "recent_events_24h": 15,
            "top_security_concerns": [
                {"event_type": "suspicious_api_call", "severity": "medium", "count": 2}
            ],
            "recommendations": [
                "Monitor API access patterns",
                "Review agent permissions",
            ],
        }

        # Run command
        security_status()

        # Verify monitor was created and called
        mock_monitor_class.assert_called_once()
        mock_monitor.generate_security_report.assert_called_once()

        # Verify console output
        assert mock_console.print.call_count >= 5

    @patch("orchestra.cli.security_commands.AIAgentSecurityMonitor")
    @patch("orchestra.cli.security_commands.console")
    def test_status_high_violation_rate(self, mock_console, mock_monitor_class):
        """Test status command with high violation rate (alert status)."""
        mock_monitor = MagicMock()
        mock_monitor_class.return_value = mock_monitor

        mock_monitor.generate_security_report.return_value = {
            "overall_metrics": {
                "total_operations": 100,
                "security_violations": 25,  # High violation rate (25%)
                "blocked_operations": 5,
                "last_updated": "2024-01-15T10:30:00",
            },
            "recent_events_24h": 30,
            "top_security_concerns": [
                {
                    "event_type": "unauthorized_access",
                    "severity": "critical",
                    "count": 10,
                }
            ],
            "recommendations": ["Immediate security review required"],
        }

        # Run command
        security_status()

        # Verify function calls
        mock_monitor_class.assert_called_once()
        mock_monitor.generate_security_report.assert_called_once()

    @patch("orchestra.cli.security_commands.AIAgentSecurityMonitor")
    @patch("orchestra.cli.security_commands.console")
    def test_status_no_security_concerns(self, mock_console, mock_monitor_class):
        """Test status command with no security concerns."""
        mock_monitor = MagicMock()
        mock_monitor_class.return_value = mock_monitor

        mock_monitor.generate_security_report.return_value = {
            "overall_metrics": {
                "total_operations": 50,
                "security_violations": 0,
                "blocked_operations": 0,
                "last_updated": "2024-01-15T10:30:00",
            },
            "recent_events_24h": 5,
            "top_security_concerns": [],  # No concerns
            "recommendations": ["Continue monitoring"],
        }

        # Run command
        security_status()

        # Verify no concerns message
        printed_calls = mock_console.print.call_args_list
        assert any(
            "No security concerns identified" in str(call) for call in printed_calls
        )

    @patch("orchestra.cli.security_commands.AIAgentSecurityMonitor")
    @patch("orchestra.cli.security_commands.console")
    def test_status_exception_handling(self, mock_console, mock_monitor_class):
        """Test status command exception handling."""
        # Mock exception
        mock_monitor_class.side_effect = Exception("Monitor initialization failed")

        # Run command and expect it to raise Exit
        with pytest.raises(click.exceptions.Exit):
            security_status()

        # Verify error message
        printed_calls = mock_console.print.call_args_list
        assert any(
            "Error getting security status" in str(call) for call in printed_calls
        )


class TestListAgentMetrics:
    """Test list_agent_metrics command."""

    @patch("orchestra.cli.security_commands.AIAgentSecurityMonitor")
    @patch("orchestra.cli.security_commands.console")
    def test_agent_metrics_with_data(self, mock_console, mock_monitor_class):
        """Test agent metrics command with agent data."""
        mock_monitor = MagicMock()
        mock_monitor_class.return_value = mock_monitor

        mock_monitor.generate_security_report.return_value = {
            "agent_metrics": {
                "developer_agent": {
                    "total_operations": 50,
                    "violation_rate": 0.02,
                    "total_violations": 1,
                    "critical_events": 0,
                }
            }
        }

        # Run command
        list_agent_metrics()

        # Verify function calls
        mock_monitor_class.assert_called_once()
        mock_monitor.generate_security_report.assert_called_once()

        # Verify console output includes agent metrics
        assert mock_console.print.call_count >= 3

    @patch("orchestra.cli.security_commands.AIAgentSecurityMonitor")
    @patch("orchestra.cli.security_commands.console")
    def test_agent_metrics_no_data(self, mock_console, mock_monitor_class):
        """Test agent metrics command with no agent data."""
        mock_monitor = MagicMock()
        mock_monitor_class.return_value = mock_monitor

        mock_monitor.generate_security_report.return_value = {
            "agent_metrics": {}  # No agent data
        }

        # Run command
        list_agent_metrics()

        # Verify no activity message
        printed_calls = mock_console.print.call_args_list
        assert any(
            "No agent activity detected yet" in str(call) for call in printed_calls
        )

    @patch("orchestra.cli.security_commands.AIAgentSecurityMonitor")
    @patch("orchestra.cli.security_commands.console")
    def test_agent_metrics_different_violation_rates(
        self, mock_console, mock_monitor_class
    ):
        """Test agent metrics with different violation rate statuses."""
        mock_monitor = MagicMock()
        mock_monitor_class.return_value = mock_monitor

        mock_monitor.generate_security_report.return_value = {
            "agent_metrics": {
                "clean_agent": {
                    "total_operations": 100,
                    "violation_rate": 0.0,  # Clean
                    "total_violations": 0,
                    "critical_events": 0,
                },
                "alert_agent": {
                    "total_operations": 20,
                    "violation_rate": 0.30,  # Alert
                    "total_violations": 6,
                    "critical_events": 2,
                },
            }
        }

        # Run command
        list_agent_metrics()

        # Verify function calls and output
        mock_monitor.generate_security_report.assert_called_once()
        assert mock_console.print.call_count >= 3


class TestShowSecurityLogs:
    """Test show_security_logs command."""

    @patch("orchestra.cli.security_commands.AIAgentSecurityMonitor")
    @patch("orchestra.cli.security_commands.console")
    @patch("builtins.open", new_callable=mock_open)
    def test_show_logs_default_options(
        self, mock_file, mock_console, mock_monitor_class
    ):
        """Test show logs command with default options."""
        mock_monitor = MagicMock()
        mock_monitor_class.return_value = mock_monitor

        # Mock log file exists and has content
        mock_monitor.security_events_log.exists.return_value = True
        mock_file.return_value.__iter__.return_value = [
            '{"timestamp": "2024-01-15T10:30:00", "agent_id": "developer_agent", "event_type": "operation_completed", "severity": "info", "message": "Test event"}\n'
        ]

        # Run command with defaults
        show_security_logs(lines=20, agent_id=None, severity=None)

        # Verify function calls
        mock_monitor_class.assert_called_once()
        mock_monitor.security_events_log.exists.assert_called_once()

    @patch("orchestra.cli.security_commands.AIAgentSecurityMonitor")
    @patch("orchestra.cli.security_commands.console")
    @patch("builtins.open", new_callable=mock_open)
    def test_show_logs_with_filters(self, mock_file, mock_console, mock_monitor_class):
        """Test show logs command with filters."""
        mock_monitor = MagicMock()
        mock_monitor_class.return_value = mock_monitor

        # Mock log file exists and has content
        mock_monitor.security_events_log.exists.return_value = True
        mock_file.return_value.__iter__.return_value = [
            '{"timestamp": "2024-01-15T10:30:00", "agent_id": "orchestrator_agent", "event_type": "security_violation", "severity": "high", "message": "Test event"}\n',
            '{"timestamp": "2024-01-15T10:29:00", "agent_id": "other_agent", "event_type": "normal_op", "severity": "info", "message": "Should be filtered out"}\n',
        ]

        # Run command with filters
        show_security_logs(lines=10, agent_id="orchestrator_agent", severity="high")

        # Verify function calls
        mock_monitor_class.assert_called_once()
        mock_monitor.security_events_log.exists.assert_called_once()

    @patch("orchestra.cli.security_commands.AIAgentSecurityMonitor")
    @patch("orchestra.cli.security_commands.console")
    def test_show_logs_no_events(self, mock_console, mock_monitor_class):
        """Test show logs command with no events."""
        mock_monitor = MagicMock()
        mock_monitor_class.return_value = mock_monitor

        # Mock log file doesn't exist or is empty
        mock_monitor.security_events_log.exists.return_value = False

        # Run command
        show_security_logs(lines=20, agent_id=None, severity=None)

        # Verify no events message
        printed_calls = mock_console.print.call_args_list
        assert any(
            "No security events found matching criteria" in str(call)
            for call in printed_calls
        )

    @patch("orchestra.cli.security_commands.AIAgentSecurityMonitor")
    @patch("orchestra.cli.security_commands.console")
    def test_show_logs_exception_handling(self, mock_console, mock_monitor_class):
        """Test show logs command exception handling."""
        # Mock exception during monitor creation
        mock_monitor_class.side_effect = Exception("Log access failed")

        # Run command and expect it to raise Exit
        with pytest.raises(click.exceptions.Exit):
            show_security_logs(lines=20, agent_id=None, severity=None)

        # Verify error message
        printed_calls = mock_console.print.call_args_list
        assert any("Error reading security logs" in str(call) for call in printed_calls)


class TestTestSecurityMonitoring:
    """Test test_security_monitoring command."""

    @patch("orchestra.cli.security_commands.AIAgentSecurityMonitor")
    @patch("orchestra.cli.security_commands.console")
    def test_security_monitoring_test(self, mock_console, mock_monitor_class):
        """Test security monitoring test command."""
        mock_monitor = MagicMock()
        mock_monitor_class.return_value = mock_monitor

        # Mock the test operations that the command actually uses
        mock_monitor.log_agent_operation.return_value = "op-123"
        mock_monitor.check_input_security.side_effect = [
            {"is_safe": True, "violations": []},
            {"is_safe": False, "violations": ["suspicious_content"]},
        ]
        mock_monitor.check_output_security.return_value = {
            "is_safe": False,
            "violations": ["secret_detected"],
        }

        # Run command
        test_security_monitoring()

        # Verify monitor was created
        mock_monitor_class.assert_called_once()

        # Verify test operations were called
        assert mock_monitor.log_agent_operation.call_count >= 1
        assert mock_monitor.check_input_security.call_count >= 2
        assert mock_monitor.check_output_security.call_count >= 1

    @patch("orchestra.cli.security_commands.AIAgentSecurityMonitor")
    @patch("orchestra.cli.security_commands.console")
    def test_security_monitoring_test_exception_handling(
        self, mock_console, mock_monitor_class
    ):
        """Test security monitoring test exception handling."""
        # Mock exception
        mock_monitor_class.side_effect = Exception("Test failed")

        # Run command and expect it to raise Exit
        with pytest.raises(click.exceptions.Exit):
            test_security_monitoring()

        # Verify error message - should be logged and printed
        printed_calls = mock_console.print.call_args_list
        assert any(
            "Unexpected error in security monitoring test" in str(call)
            for call in printed_calls
        )


class TestGenerateSecurityReport:
    """Test generate_security_report command."""

    @patch("orchestra.cli.security_commands.AIAgentSecurityMonitor")
    @patch("orchestra.cli.security_commands.console")
    def test_generate_report_no_output_file(self, mock_console, mock_monitor_class):
        """Test generate report command without output file."""
        mock_monitor = MagicMock()
        mock_monitor_class.return_value = mock_monitor

        mock_report = {
            "timestamp": "2024-01-15T10:30:00",
            "overall_metrics": {"total_operations": 100},
            "agent_metrics": {"test_agent": {"total_operations": 50}},
            "recommendations": ["Keep monitoring"],
        }
        mock_monitor.generate_security_report.return_value = mock_report

        # Run command without output file
        generate_security_report(output_file=None)

        # Verify monitor calls
        mock_monitor_class.assert_called_once()
        mock_monitor.generate_security_report.assert_called_once()

        # Verify console output (report should be printed)
        assert mock_console.print.call_count >= 3

    @patch("orchestra.cli.security_commands.AIAgentSecurityMonitor")
    @patch("orchestra.cli.security_commands.console")
    @patch("builtins.open", new_callable=mock_open)
    def test_generate_report_with_output_file(
        self, mock_file, mock_console, mock_monitor_class
    ):
        """Test generate report command with output file."""
        mock_monitor = MagicMock()
        mock_monitor_class.return_value = mock_monitor

        mock_report = {
            "timestamp": "2024-01-15T10:30:00",
            "overall_metrics": {"total_operations": 100},
            "recommendations": ["Keep monitoring"],
        }
        mock_monitor.generate_security_report.return_value = mock_report

        # Run command with output file
        generate_security_report(output_file="security_report.json")

        # Verify file was written (Path object is converted from string)
        mock_file.assert_called_once()
        call_args = mock_file.call_args[0]
        assert str(call_args[0]) == "security_report.json"
        assert call_args[1] == "w"

    @patch("orchestra.cli.security_commands.AIAgentSecurityMonitor")
    @patch("orchestra.cli.security_commands.console")
    def test_generate_report_exception_handling(self, mock_console, mock_monitor_class):
        """Test generate report command exception handling."""
        # Mock exception
        mock_monitor_class.side_effect = Exception("Report generation failed")

        # Run command and expect it to raise Exit
        with pytest.raises(click.exceptions.Exit):
            generate_security_report(output_file=None)

        # Verify error message - should be logged and printed
        printed_calls = mock_console.print.call_args_list
        assert any(
            "Unexpected error generating security report" in str(call)
            for call in printed_calls
        )


class TestCliIntegration:
    """Test CLI integration and runner functionality."""

    def test_cli_runner_status_command(self):
        """Test status command via CLI runner."""
        runner = CliRunner()

        with patch(
            "orchestra.cli.security_commands.AIAgentSecurityMonitor"
        ) as mock_monitor_class:
            mock_monitor = MagicMock()
            mock_monitor_class.return_value = mock_monitor

            mock_monitor.generate_security_report.return_value = {
                "overall_metrics": {
                    "total_operations": 10,
                    "security_violations": 0,
                    "blocked_operations": 0,
                    "last_updated": "2024-01-15T10:30:00",
                },
                "recent_events_24h": 2,
                "top_security_concerns": [],
                "recommendations": ["All good"],
            }

            result = runner.invoke(security_app, ["status"])

            assert result.exit_code == 0
            assert "Orchestra AI Agent Security Status" in result.output

    def test_cli_runner_agents_command(self):
        """Test agents command via CLI runner."""
        runner = CliRunner()

        with patch(
            "orchestra.cli.security_commands.AIAgentSecurityMonitor"
        ) as mock_monitor_class:
            mock_monitor = MagicMock()
            mock_monitor_class.return_value = mock_monitor

            mock_monitor.generate_security_report.return_value = {"agent_metrics": {}}

            result = runner.invoke(security_app, ["agents"])

            assert result.exit_code == 0
            assert "AI Agent Security Metrics" in result.output

    def test_cli_runner_logs_command(self):
        """Test logs command via CLI runner."""
        runner = CliRunner()

        with patch(
            "orchestra.cli.security_commands.AIAgentSecurityMonitor"
        ) as mock_monitor_class:
            mock_monitor = MagicMock()
            mock_monitor_class.return_value = mock_monitor

            mock_monitor.get_recent_events.return_value = []

            result = runner.invoke(security_app, ["logs", "--lines", "10"])

            assert result.exit_code == 0
            assert "Recent Security Events" in result.output

    def test_cli_runner_test_command(self):
        """Test test command via CLI runner."""
        runner = CliRunner()

        with patch(
            "orchestra.cli.security_commands.AIAgentSecurityMonitor"
        ) as mock_monitor_class:
            mock_monitor = MagicMock()
            mock_monitor_class.return_value = mock_monitor

            # Mock validation results
            mock_monitor.validate_operation.side_effect = [True, False, True]

            result = runner.invoke(security_app, ["test"])

            assert result.exit_code == 0
            assert "Testing AI Agent Security Monitoring" in result.output

    def test_cli_runner_report_command(self):
        """Test report command via CLI runner."""
        runner = CliRunner()

        with patch(
            "orchestra.cli.security_commands.AIAgentSecurityMonitor"
        ) as mock_monitor_class:
            mock_monitor = MagicMock()
            mock_monitor_class.return_value = mock_monitor

            mock_monitor.generate_security_report.return_value = {
                "timestamp": "2024-01-15T10:30:00",
                "overall_metrics": {"total_operations": 50},
            }

            result = runner.invoke(security_app, ["report"])

            assert result.exit_code == 0
            assert "Orchestra AI Security Report" in result.output


class TestSecurityCommandsEdgeCases:
    """Test edge cases and boundary conditions."""

    @patch("orchestra.cli.security_commands.AIAgentSecurityMonitor")
    @patch("orchestra.cli.security_commands.console")
    def test_status_division_by_zero_protection(self, mock_console, mock_monitor_class):
        """Test status command handles zero operations gracefully."""
        mock_monitor = MagicMock()
        mock_monitor_class.return_value = mock_monitor

        mock_monitor.generate_security_report.return_value = {
            "overall_metrics": {
                "total_operations": 0,  # Zero operations
                "security_violations": 0,
                "blocked_operations": 0,
                "last_updated": "2024-01-15T10:30:00",
            },
            "recent_events_24h": 0,
            "top_security_concerns": [],
            "recommendations": ["Start monitoring"],
        }

        # Run command (should handle division by zero)
        security_status()

        # Should not raise exception and should call functions
        mock_monitor.generate_security_report.assert_called_once()
        assert mock_console.print.call_count >= 3

    @patch("orchestra.cli.security_commands.AIAgentSecurityMonitor")
    @patch("orchestra.cli.security_commands.console")
    def test_status_all_severity_levels(self, mock_console, mock_monitor_class):
        """Test status command with all severity levels."""
        mock_monitor = MagicMock()
        mock_monitor_class.return_value = mock_monitor

        mock_monitor.generate_security_report.return_value = {
            "overall_metrics": {
                "total_operations": 100,
                "security_violations": 10,
                "blocked_operations": 2,
                "last_updated": "2024-01-15T10:30:00",
            },
            "recent_events_24h": 15,
            "top_security_concerns": [
                {"event_type": "critical_issue", "severity": "critical", "count": 1},
                {"event_type": "high_issue", "severity": "high", "count": 2},
                {"event_type": "medium_issue", "severity": "medium", "count": 3},
                {"event_type": "low_issue", "severity": "low", "count": 4},
                {"event_type": "unknown_issue", "severity": "unknown", "count": 1},
            ],
            "recommendations": ["Review all issues"],
        }

        # Run command
        security_status()

        # Verify all severity levels are handled
        mock_monitor.generate_security_report.assert_called_once()
        assert mock_console.print.call_count >= 8


class TestSecurityAppMainExecution:
    """Test main app execution."""

    def test_main_execution_path_exists(self):
        """Test that main execution path exists and app is callable."""
        # Test that we can access the app for main execution
        assert security_app is not None
        assert hasattr(security_app, "__call__")

        # Test that the main execution code exists in the module
        with open("orchestra/cli/security_commands.py", "r") as f:
            content = f.read()
            assert 'if __name__ == "__main__":' in content
            assert "security_app()" in content
