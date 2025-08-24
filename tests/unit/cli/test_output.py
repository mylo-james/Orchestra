"""Tests for CLI output formatting utilities."""

from unittest.mock import Mock

import pytest
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from orchestra.cli.output import (
    display_agent_status,
    display_banner,
    display_error,
    display_info,
    display_success,
    display_warning,
    display_workflow_status,
    error_panel,
    info_panel,
    success_panel,
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
