"""
Tests for src/cli/output.py

Tests rich output formatting utilities for Orchestra CLI.
"""

from io import StringIO
from unittest.mock import MagicMock

from rich.console import Console

from src.cli.output import (
    create_progress_bar,
    display_agent_status,
    display_banner,
    display_code_diff,
    display_config_tree,
    display_error,
    display_info,
    display_logs,
    display_security_scan_results,
    display_success,
    display_task_progress,
    display_warning,
    display_workflow_status,
)


class TestBasicDisplayFunctions:
    """Test basic display functions."""

    def test_display_banner(self):
        """Test banner display function."""
        output = StringIO()
        console = Console(file=output, width=80)

        display_banner(console, "1.0.0")

        result = output.getvalue()
        assert "Orchestra" in result
        assert "1.0.0" in result
        assert "🎼" in result

    def test_display_success(self):
        """Test success message display."""
        output = StringIO()
        console = Console(file=output, width=80)

        display_success(console, "Operation completed")

        result = output.getvalue()
        assert "Operation completed" in result
        assert "✅" in result

    def test_display_error(self):
        """Test error message display."""
        output = StringIO()
        console = Console(file=output, width=80)

        display_error(console, "Something went wrong")

        result = output.getvalue()
        assert "Something went wrong" in result
        assert "❌" in result

    def test_display_warning(self):
        """Test warning message display."""
        output = StringIO()
        console = Console(file=output, width=80)

        display_warning(console, "This is a warning")

        result = output.getvalue()
        assert "This is a warning" in result
        assert "⚠️" in result

    def test_display_info(self):
        """Test info message display."""
        output = StringIO()
        console = Console(file=output, width=80)

        display_info(console, "Here's some info")

        result = output.getvalue()
        assert "Here's some info" in result
        assert "ℹ️" in result


class TestComplexDisplayFunctions:
    """Test complex display functions."""

    def test_display_agent_status(self):
        """Test agent status display."""
        output = StringIO()
        console = Console(file=output, width=120)

        agents = [
            {
                "name": "Developer Agent",
                "status": "active",
                "last_activity": "2024-01-15 10:30:00",
                "task_count": 5,
            },
            {"name": "Orchestrator Agent", "status": "inactive"},
        ]

        display_agent_status(console, agents)

        result = output.getvalue()
        assert "Agent Status" in result
        assert "Developer Agent" in result

    def test_display_workflow_status(self):
        """Test workflow status display."""
        output = StringIO()
        console = Console(file=output, width=120)

        workflows = [
            {
                "id": "CI/CD Pipeline",
                "status": "running",
                "progress": 75,
                "started": "10:30:00",
                "duration": "2m 15s",
            }
        ]

        display_workflow_status(console, workflows)

        result = output.getvalue()
        assert "Workflow Status" in result
        assert "CI/CD Pipeline" in result

    def test_display_code_diff(self):
        """Test code diff display."""
        output = StringIO()
        console = Console(file=output, width=120)

        display_code_diff(
            console=console,
            file_path="test.py",
            old_content="def hello():\n    print('Hello')",
            new_content="def hello():\n    print('Hello, World!')",
        )

        result = output.getvalue()
        assert "Code changes" in result

    def test_display_config_tree(self):
        """Test config tree display."""
        output = StringIO()
        console = Console(file=output, width=120)

        config = {"database": {"host": "localhost", "port": 5432}, "debug": True}

        display_config_tree(console, config, "Test Configuration")

        result = output.getvalue()
        assert "Test Configuration" in result

    def test_display_logs(self):
        """Test logs display."""
        output = StringIO()
        console = Console(file=output, width=120)

        log_entries = [
            {
                "timestamp": "2024-01-15T10:30:00",
                "level": "INFO",
                "message": "Application started",
            }
        ]

        display_logs(console, log_entries, max_lines=10)

        result = output.getvalue()
        assert "Recent Logs" in result

    def test_create_progress_bar(self):
        """Test progress bar creation."""
        output = StringIO()
        console = Console(file=output, width=80)

        progress = create_progress_bar(console, "Processing files")

        assert progress is not None
        assert hasattr(progress, "add_task")

    def test_display_security_scan_results(self):
        """Test security scan results display."""
        output = StringIO()
        console = Console(file=output, width=120)

        results = {
            "status": "clean",
            "total_files": 50,
            "issues_found": 0,
            "scan_time": "2.5s",
        }

        display_security_scan_results(console, results)

        result = output.getvalue()
        assert "Security Scan Results" in result

    def test_display_task_progress(self):
        """Test task progress display."""
        output = StringIO()
        console = Console(file=output, width=120)

        tasks = [{"name": "Setup Environment", "status": "completed", "progress": 100}]

        display_task_progress(console, tasks)

        result = output.getvalue()
        assert "Task Progress" in result


class TestEdgeCases:
    """Test edge cases."""

    def test_empty_lists(self):
        """Test functions with empty lists."""
        output = StringIO()
        console = Console(file=output, width=80)

        display_agent_status(console, [])
        display_workflow_status(console, [])
        display_logs(console, [], max_lines=10)
        display_task_progress(console, [])

        result = output.getvalue()
        assert len(result) > 0

    def test_missing_fields(self):
        """Test functions with missing fields."""
        output = StringIO()
        console = Console(file=output, width=120)

        # Test with minimal/missing data
        display_agent_status(console, [{}])
        display_workflow_status(console, [{"name": "Test"}])
        display_logs(console, [{"message": "test"}], max_lines=5)
        display_task_progress(console, [{"name": "test"}])

        result = output.getvalue()
        assert len(result) > 0

    def test_various_data_types(self):
        """Test config tree with various data types."""
        output = StringIO()
        console = Console(file=output, width=120)

        config = {
            "string": "test",
            "number": 42,
            "boolean": True,
            "list": [1, 2, 3],
            "nested": {"key": "value"},
        }

        display_config_tree(console, config, "Mixed Config")

        result = output.getvalue()
        assert "Mixed Config" in result


class TestFunctionCallCounts:
    """Test that functions make expected console calls."""

    def test_console_print_call_counts(self):
        """Test console.print call counts for verification."""
        mock_console = MagicMock()

        # Test each function makes at least one console call
        functions_and_args = [
            (display_banner, ["1.0.0"]),
            (display_success, ["Success"]),
            (display_error, ["Error"]),
            (display_warning, ["Warning"]),
            (display_info, ["Info"]),
            (display_agent_status, [[{"name": "Agent"}]]),
            (display_workflow_status, [[{"name": "Workflow"}]]),
            (display_code_diff, ["file.py", "old", "new"]),
            (display_config_tree, [{"key": "value"}, "Config"]),
            (display_logs, [[{"message": "log"}], 10]),
            (display_security_scan_results, [{"status": "clean"}]),
            (display_task_progress, [[{"name": "Task"}]]),
        ]

        total_calls = 0
        for func, args in functions_and_args:
            mock_console.reset_mock()
            func(mock_console, *args)
            assert mock_console.print.call_count >= 1
            total_calls += mock_console.print.call_count

        # All functions should have made console calls
        assert total_calls >= len(functions_and_args)

    def test_progress_bar_creation(self):
        """Test progress bar creation and attributes."""
        output = StringIO()
        console = Console(file=output, width=80)

        # Test progress bar creation
        progress = create_progress_bar(console, "Test progress")

        assert progress is not None
        assert hasattr(progress, "add_task")
        assert hasattr(progress, "update")
        assert hasattr(progress, "refresh")

    def test_all_functions_handle_unicode(self):
        """Test that all functions handle unicode characters."""
        output = StringIO()
        console = Console(file=output, width=120)

        # Test with unicode content
        display_success(console, "Success! ✨🎉")
        display_error(console, "Error! ❌💥")
        display_warning(console, "Warning! ⚠️🚨")
        display_info(console, "Info! ℹ️📝")

        result = output.getvalue()
        assert len(result) > 0  # Should handle unicode without crashing
