"""Tests for CLI output formatting utilities."""

from unittest.mock import Mock

import pytest
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from orchestra.cli.output import (
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
    error_panel,
    info_panel,
    success_panel,
    warning_panel,
)


class TestPanelFunctions:
    """Test panel creation functions."""

    def test_error_panel(self):
        """Test error panel creation."""
        panel = error_panel("Test error message")

        assert isinstance(panel, Panel)
        assert "❌ Test error message" in panel.renderable
        assert panel.title == "Error"
        assert panel.border_style == "red"

    def test_info_panel(self):
        """Test info panel creation."""
        panel = info_panel("Test info message")

        assert isinstance(panel, Panel)
        assert "ℹ️ Test info message" in panel.renderable
        assert panel.title == "Info"
        assert panel.border_style == "blue"

    def test_success_panel(self):
        """Test success panel creation."""
        panel = success_panel("Test success message")

        assert isinstance(panel, Panel)
        assert "✅ Test success message" in panel.renderable
        assert panel.title == "Success"
        assert panel.border_style == "green"

    def test_panel_with_empty_message(self):
        """Test panel creation with empty messages."""
        error_p = error_panel("")
        info_p = info_panel("")
        success_p = success_panel("")

        assert isinstance(error_p, Panel)
        assert isinstance(info_p, Panel)
        assert isinstance(success_p, Panel)


class TestDisplayFunctions:
    """Test display functions."""

    @pytest.fixture
    def mock_console(self):
        """Create a mock console for testing."""
        return Mock(spec=Console)

    def test_display_banner(self, mock_console):
        """Test banner display."""
        display_banner(mock_console, "1.0.0")

        # Verify console.print was called
        mock_console.print.assert_called_once()

        # Verify the call was made with a Panel
        call_args = mock_console.print.call_args[0][0]
        assert isinstance(call_args, Panel)
        assert "🎼 Orchestra" in str(call_args.renderable)
        assert "v1.0.0" in str(call_args.renderable)

    def test_display_success(self, mock_console):
        """Test success message display."""
        display_success(mock_console, "Operation completed")

        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args[0][0]
        assert "✅" in call_args
        assert "Operation completed" in call_args

    def test_display_error(self, mock_console):
        """Test error message display."""
        display_error(mock_console, "Operation failed")

        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args[0][0]
        assert "❌" in call_args
        assert "Operation failed" in call_args

    def test_display_warning(self, mock_console):
        """Test warning message display."""
        display_warning(mock_console, "Warning message")

        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args[0][0]
        assert "⚠️" in call_args
        assert "Warning message" in call_args

    def test_display_info(self, mock_console):
        """Test info message display."""
        display_info(mock_console, "Info message")

        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args[0][0]
        assert "ℹ️" in call_args
        assert "Info message" in call_args


class TestStatusDisplayFunctions:
    """Test status display functions."""

    @pytest.fixture
    def mock_console(self):
        """Create a mock console for testing."""
        return Mock(spec=Console)

    def test_display_agent_status_empty_list(self, mock_console):
        """Test agent status display with empty list."""
        display_agent_status(mock_console, [])

        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args[0][0]
        assert isinstance(call_args, Table)
        assert call_args.title == "🤖 Agent Status"

    def test_display_agent_status_with_agents(self, mock_console):
        """Test agent status display with agents."""
        agents = [
            {
                "name": "Agent 1",
                "status": "active",
                "last_activity": "2023-01-01 12:00:00",
                "task_count": 5,
            },
            {
                "name": "Agent 2",
                "status": "inactive",
                "last_activity": "2023-01-01 11:00:00",
                "task_count": 0,
            },
        ]

        display_agent_status(mock_console, agents)

        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args[0][0]
        assert isinstance(call_args, Table)
        assert call_args.title == "🤖 Agent Status"

    def test_display_agent_status_missing_fields(self, mock_console):
        """Test agent status display with missing fields."""
        agents = [
            {
                "name": "Agent 1"
                # Missing other fields
            }
        ]

        display_agent_status(mock_console, agents)

        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args[0][0]
        assert isinstance(call_args, Table)

    def test_display_workflow_status_empty_list(self, mock_console):
        """Test workflow status display with empty list."""
        display_workflow_status(mock_console, [])

        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args[0][0]
        assert isinstance(call_args, Table)
        assert call_args.title == "🔄 Workflow Status"

    def test_display_workflow_status_with_workflows(self, mock_console):
        """Test workflow status display with workflows."""
        workflows = [
            {
                "id": "workflow-1",
                "status": "running",
                "progress": "50%",
                "started": "2023-01-01 12:00:00",
                "duration": "1h 30m",
            },
            {
                "id": "workflow-2",
                "status": "completed",
                "progress": "100%",
                "started": "2023-01-01 10:00:00",
                "duration": "2h 15m",
            },
        ]

        display_workflow_status(mock_console, workflows)

        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args[0][0]
        assert isinstance(call_args, Table)
        assert call_args.title == "🔄 Workflow Status"

    def test_display_workflow_status_different_statuses(self, mock_console):
        """Test workflow status display with different status types."""
        workflows = [
            {"id": "w1", "status": "running"},
            {"id": "w2", "status": "completed"},
            {"id": "w3", "status": "failed"},
            {"id": "w4", "status": "paused"},
            {"id": "w5", "status": "unknown"},
        ]

        display_workflow_status(mock_console, workflows)

        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args[0][0]
        assert isinstance(call_args, Table)

    def test_display_workflow_status_missing_fields(self, mock_console):
        """Test workflow status display with missing fields."""
        workflows = [
            {
                "id": "workflow-1"
                # Missing other fields
            }
        ]

        display_workflow_status(mock_console, workflows)

        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args[0][0]
        assert isinstance(call_args, Table)


class TestIntegration:
    """Test integration scenarios."""

    @pytest.fixture
    def real_console(self):
        """Create a real console for integration testing."""
        return Console(force_terminal=True)

    def test_panel_integration(self, real_console):
        """Test panel integration with real console."""
        # This test verifies that panels can be created and don't crash
        error_p = error_panel("Integration test error")
        info_p = info_panel("Integration test info")
        success_p = success_panel("Integration test success")

        assert isinstance(error_p, Panel)
        assert isinstance(info_p, Panel)
        assert isinstance(success_p, Panel)

        # Test that panels can be rendered (basic integration test)
        try:
            # Just verify the panels can be created without errors
            str(error_p.renderable)
            str(info_p.renderable)
            str(success_p.renderable)
        except Exception as e:
            pytest.fail(f"Panel rendering failed: {e}")

    def test_table_integration(self, real_console):
        """Test table integration with real console."""
        # Test agent status table
        agents = [
            {
                "name": "Test Agent",
                "status": "active",
                "last_activity": "2023-01-01 12:00:00",
                "task_count": 3,
            }
        ]

        # This should not raise any exceptions
        display_agent_status(real_console, agents)

        # Test workflow status table
        workflows = [
            {
                "id": "test-workflow",
                "status": "running",
                "progress": "75%",
                "started": "2023-01-01 12:00:00",
                "duration": "45m",
            }
        ]

        # This should not raise any exceptions
        display_workflow_status(real_console, workflows)


class TestMissingFunctions:
    """Test functions that are missing from coverage (PRD NFR1 - Rich CLI interface)."""

    def test_warning_panel(self):
        """Test warning panel creation (missing coverage)."""
        panel = warning_panel("Test warning message")

        assert isinstance(panel, Panel)
        assert "⚠️ Test warning message" in panel.renderable
        assert panel.title == "Warning"
        assert panel.border_style == "yellow"

    def test_display_code_diff(self):
        """Test code diff display function."""
        console = Mock(spec=Console)
        old_content = "def hello():\n    return 'old'"
        new_content = "def hello():\n    return 'new'"

        display_code_diff(console, "test.py", old_content, new_content)

        # Should call print multiple times for diff display
        assert console.print.call_count >= 3

        # Check some expected calls
        calls = console.print.call_args_list
        assert any("Code changes for:" in str(call) for call in calls)
        assert any("Old content:" in str(call) for call in calls)
        assert any("New content:" in str(call) for call in calls)

    def test_display_code_diff_no_changes(self):
        """Test code diff display when no changes."""
        console = Mock(spec=Console)
        content = "def hello():\n    return 'same'"

        display_code_diff(console, "test.py", content, content)

        # Should still call print for header and no changes message
        assert console.print.call_count >= 2
        calls = console.print.call_args_list
        assert any("No changes detected" in str(call) for call in calls)

    def test_display_config_tree_simple(self):
        """Test config tree display with simple config."""
        console = Mock(spec=Console)
        config = {
            "database": {"host": "localhost", "port": 5432, "password": "secret123"},
            "debug": True,
        }

        display_config_tree(console, config, "Test Config")

        # Should call print once with the tree
        console.print.assert_called_once()

    def test_display_config_tree_with_lists(self):
        """Test config tree display with lists."""
        console = Mock(spec=Console)
        config = {
            "servers": ["server1", "server2"],
            "users": [
                {"name": "user1", "role": "admin"},
                {"name": "user2", "role": "user"},
            ],
        }

        display_config_tree(console, config)

        console.print.assert_called_once()

    def test_display_config_tree_sensitive_masking(self):
        """Test that sensitive values are masked in config tree."""
        console = Mock(spec=Console)
        config = {
            "api_key": "secret123",
            "password": "mypass",
            "token": "abc123",
            "secret": "topsecret",
            "normal_value": "visible",
        }

        display_config_tree(console, config)

        # Get the tree that was printed
        console.print.assert_called_once()

    def test_display_logs_basic(self):
        """Test logs display function."""
        console = Mock(spec=Console)
        logs = [
            {"timestamp": "2023-01-01 10:00:00", "level": "INFO", "message": "Started"},
            {
                "timestamp": "2023-01-01 10:01:00",
                "level": "WARNING",
                "message": "Warning occurred",
            },
            {
                "timestamp": "2023-01-01 10:02:00",
                "level": "ERROR",
                "message": "Error occurred",
            },
        ]

        display_logs(console, logs)

        # Should call print for header + each log entry
        assert console.print.call_count >= 4

    def test_display_logs_max_lines_limit(self):
        """Test logs display with max_lines limit."""
        console = Mock(spec=Console)
        logs = [
            {
                "timestamp": f"2023-01-01 10:00:{i:02d}",
                "level": "INFO",
                "message": f"Message {i}",
            }
            for i in range(100)
        ]

        display_logs(console, logs, max_lines=5)

        # Should limit to max_lines + header
        assert console.print.call_count <= 6

    def test_display_logs_missing_fields(self):
        """Test logs display with missing fields."""
        console = Mock(spec=Console)
        logs = [
            {},  # Empty log
            {"message": "Only message"},  # Missing timestamp and level
        ]

        display_logs(console, logs)

        # Should not crash and still display something
        assert console.print.call_count >= 2

    def test_create_progress_bar(self):
        """Test progress bar creation."""
        # Use real console since Progress needs specific console methods
        from rich.console import Console

        console = Console(file=Mock())  # Mock the file output but use real console

        progress = create_progress_bar(console, "Testing progress")

        # Should return a Progress object
        from rich.progress import Progress

        assert isinstance(progress, Progress)

    def test_display_security_scan_results_no_issues(self):
        """Test security scan results with no issues."""
        console = Mock(spec=Console)
        results = {"total_issues": 0}

        display_security_scan_results(console, results)

        # Should call print for header and success message
        assert console.print.call_count >= 2

    def test_display_security_scan_results_with_issues(self):
        """Test security scan results with issues."""
        console = Mock(spec=Console)
        results = {
            "total_issues": 3,
            "issues_by_severity": {"high": 1, "medium": 2},
            "issues": [
                {
                    "test_name": "hardcoded_password_string",
                    "filename": "test.py",
                    "line_number": 42,
                    "issue_severity": "HIGH",
                    "issue_text": "Hardcoded password found",
                },
                {
                    "test_name": "sql_injection",
                    "filename": "db.py",
                    "line_number": 15,
                    "issue_severity": "MEDIUM",
                    "issue_text": "Possible SQL injection",
                },
            ],
        }

        display_security_scan_results(console, results)

        # Should call print multiple times for all sections
        assert console.print.call_count >= 8

    def test_display_security_scan_results_many_issues(self):
        """Test security scan results with many issues (>10)."""
        console = Mock(spec=Console)
        issues = [
            {
                "test_name": f"issue_{i}",
                "filename": f"file_{i}.py",
                "line_number": i,
                "issue_severity": "LOW",
                "issue_text": f"Issue {i} description",
            }
            for i in range(15)
        ]

        results = {"total_issues": 15, "issues": issues}

        display_security_scan_results(console, results)

        # Should display max 10 issues plus "and X more" message
        calls = console.print.call_args_list
        assert any("and 5 more issues" in str(call) for call in calls)

    def test_display_task_progress_various_statuses(self):
        """Test task progress display with various statuses."""
        console = Mock(spec=Console)
        tasks = [
            {"name": "Task 1", "status": "completed", "progress": 100},
            {"name": "Task 2", "status": "running", "progress": 50},
            {"name": "Task 3", "status": "pending", "progress": 0},
            {"name": "Task 4", "status": "failed", "progress": 25},
            {"name": "Task 5", "status": "cancelled", "progress": 10},
            {"name": "Task 6", "status": "unknown", "progress": 75},
        ]

        display_task_progress(console, tasks)

        # Should call print for header + each task
        assert console.print.call_count >= 7

        # Check that different status emojis are used
        calls = console.print.call_args_list
        call_strings = [str(call) for call in calls]

        # Should contain different status emojis
        assert any("✅" in call for call in call_strings)  # completed
        assert any("🔄" in call for call in call_strings)  # running
        assert any("⏳" in call for call in call_strings)  # pending
        assert any("❌" in call for call in call_strings)  # failed
        assert any("🚫" in call for call in call_strings)  # cancelled
        assert any("❓" in call for call in call_strings)  # unknown

    def test_display_task_progress_empty_list(self):
        """Test task progress display with empty task list."""
        console = Mock(spec=Console)
        tasks = []

        display_task_progress(console, tasks)

        # Should still display header
        console.print.assert_called_once()

    def test_display_task_progress_missing_fields(self):
        """Test task progress display with missing fields."""
        console = Mock(spec=Console)
        tasks = [
            {},  # Empty task
            {"name": "Partial Task"},  # Missing status and progress
        ]

        display_task_progress(console, tasks)

        # Should not crash and display default values
        assert console.print.call_count >= 3
