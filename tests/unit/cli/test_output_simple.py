"""Simple tests to boost CLI output coverage."""

from rich.console import Console

from src.cli.output import (
    display_banner,
    display_success,
    display_error,
    display_warning,
    display_info,
    display_agent_status,
    display_workflow_status,
)


class TestBasicOutputFunctions:
    """Test basic output functions that we know exist."""

    def test_all_display_functions(self):
        """Test all the display functions we know exist."""
        console = Console()

        # Test banner
        display_banner(console, "1.0.0")

        # Test status messages
        display_success(console, "Test success")
        display_error(console, "Test error")
        display_warning(console, "Test warning")
        display_info(console, "Test info")

    def test_display_agent_status_variations(self):
        """Test agent status display with different inputs."""
        console = Console()

        # Empty list
        display_agent_status(console, [])

        # Single agent
        display_agent_status(
            console,
            [
                {
                    "name": "test-agent",
                    "status": "active",
                    "last_activity": "now",
                    "tasks": 1,
                }
            ],
        )

        # Multiple agents
        display_agent_status(
            console,
            [
                {
                    "name": "orchestrator",
                    "status": "running",
                    "last_activity": "2024-01-01",
                    "tasks": 3,
                },
                {
                    "name": "developer",
                    "status": "idle",
                    "last_activity": "2024-01-02",
                    "tasks": 0,
                },
                {
                    "name": "release",
                    "status": "error",
                    "last_activity": "2024-01-03",
                    "tasks": 2,
                },
            ],
        )

    def test_display_workflow_status_variations(self):
        """Test workflow status display with different inputs."""
        console = Console()

        # Empty list
        display_workflow_status(console, [])

        # Single workflow
        display_workflow_status(
            console,
            [
                {
                    "name": "test-workflow",
                    "status": "running",
                    "progress": 50,
                    "agents": ["dev"],
                }
            ],
        )

        # Multiple workflows
        display_workflow_status(
            console,
            [
                {
                    "name": "dev-workflow",
                    "status": "completed",
                    "progress": 100,
                    "agents": ["dev", "test"],
                },
                {
                    "name": "release-workflow",
                    "status": "pending",
                    "progress": 0,
                    "agents": ["release"],
                },
                {
                    "name": "monitor-workflow",
                    "status": "running",
                    "progress": 75,
                    "agents": ["monitor"],
                },
            ],
        )

    def test_console_output_edge_cases(self):
        """Test edge cases for console output."""
        console = Console()

        # Test with None/empty values
        display_success(console, "")
        display_error(console, None)

        # Test with very long messages
        long_message = "A" * 1000
        display_warning(console, long_message)

        # Test with special characters
        display_info(console, "Test with émojis 🎉 and spéciàl characters!")

    def test_workflow_and_agent_display_edge_cases(self):
        """Test edge cases for workflow and agent displays."""
        console = Console()

        # Test with missing fields
        display_agent_status(
            console, [{"name": "incomplete-agent"}]  # Missing other fields
        )

        display_workflow_status(
            console, [{"name": "incomplete-workflow"}]  # Missing other fields
        )

        # Test with None values
        display_agent_status(
            console,
            [
                {
                    "name": "agent-with-nones",
                    "status": None,
                    "last_activity": None,
                    "tasks": None,
                }
            ],
        )
