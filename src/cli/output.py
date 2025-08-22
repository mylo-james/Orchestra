"""Rich output formatting utilities for Orchestra CLI."""

from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.table import Table
from rich.tree import Tree


def error_panel(message: str) -> Panel:
    """Create an error panel."""
    return Panel(f"❌ {message}", title="Error", border_style="red")


def info_panel(message: str) -> Panel:
    """Create an info panel."""
    return Panel(f"ℹ️ {message}", title="Info", border_style="blue")


def success_panel(message: str) -> Panel:
    """Create a success panel."""
    return Panel(f"✅ {message}", title="Success", border_style="green")


def display_banner(console: Console, version: str) -> None:
    """Display the Orchestra banner."""
    banner_text = f"""
[bold blue]🎼 Orchestra[/bold blue] [dim]v{version}[/dim]
[italic]AI Agent System for Development Team Orchestration[/italic]
    """
    console.print(Panel(banner_text.strip(), border_style="blue"))


def display_success(console: Console, message: str) -> None:
    """Display a success message."""
    console.print(f"✅ [bold green]{message}[/bold green]")


def display_error(console: Console, message: str) -> None:
    """Display an error message."""
    console.print(f"❌ [bold red]{message}[/bold red]")


def display_warning(console: Console, message: str) -> None:
    """Display a warning message."""
    console.print(f"⚠️ [bold yellow]{message}[/bold yellow]")


def display_info(console: Console, message: str) -> None:
    """Display an info message."""
    console.print(f"ℹ️ [bold blue]{message}[/bold blue]")


def display_agent_status(console: Console, agents: list[dict[str, Any]]) -> None:
    """Display agent status in a formatted table."""
    table = Table(title="🤖 Agent Status", show_header=True, header_style="bold blue")

    table.add_column("Agent", style="cyan", no_wrap=True)
    table.add_column("Status", style="magenta")
    table.add_column("Last Activity", style="green")
    table.add_column("Tasks", justify="right", style="yellow")

    for agent in agents:
        status_emoji = "🟢" if agent.get("status") == "active" else "🔴"
        status_text = f"{status_emoji} {agent.get('status', 'unknown')}"

        table.add_row(
            agent.get("name", "Unknown"),
            status_text,
            agent.get("last_activity", "Never"),
            str(agent.get("task_count", 0)),
        )

    console.print(table)


def display_workflow_status(console: Console, workflows: list[dict[str, Any]]) -> None:
    """Display workflow status in a formatted table."""
    table = Table(
        title="🔄 Workflow Status", show_header=True, header_style="bold blue"
    )

    table.add_column("Workflow ID", style="cyan", no_wrap=True)
    table.add_column("Status", style="magenta")
    table.add_column("Progress", style="green")
    table.add_column("Started", style="yellow")
    table.add_column("Duration", justify="right", style="blue")

    for workflow in workflows:
        status_emoji = {
            "running": "🟡",
            "completed": "🟢",
            "failed": "🔴",
            "paused": "🟠",
        }.get(workflow.get("status", "unknown"), "⚪")

        status_text = f"{status_emoji} {workflow.get('status', 'unknown')}"
        progress = f"{workflow.get('progress', 0)}%"

        table.add_row(
            workflow.get("id", "Unknown"),
            status_text,
            progress,
            workflow.get("started", "Unknown"),
            workflow.get("duration", "Unknown"),
        )

    console.print(table)


def display_code_diff(
    console: Console, file_path: str, old_content: str, new_content: str
) -> None:
    """Display a code diff with syntax highlighting."""
    console.print(
        f"\n📝 [bold blue]Code changes for:[/bold blue] [cyan]{file_path}[/cyan]"
    )

    # Simple diff display - in a real implementation, you'd use a proper diff library
    if old_content != new_content:
        console.print("\n[bold red]- Old content:[/bold red]")
        console.print(
            Syntax(
                old_content[:500] + "..." if len(old_content) > 500 else old_content,
                "python",
                theme="monokai",
                line_numbers=True,
            )
        )

        console.print("\n[bold green]+ New content:[/bold green]")
        console.print(
            Syntax(
                new_content[:500] + "..." if len(new_content) > 500 else new_content,
                "python",
                theme="monokai",
                line_numbers=True,
            )
        )
    else:
        console.print("[dim]No changes detected[/dim]")


def display_config_tree(
    console: Console, config: dict[str, Any], title: str = "Configuration"
) -> None:
    """Display configuration in a tree format."""
    tree = Tree(f"🔧 {title}")

    def add_dict_to_tree(
        parent_tree: Tree, data: dict[str, Any], prefix: str = ""
    ) -> None:
        for key, value in data.items():
            if isinstance(value, dict):
                branch = parent_tree.add(f"[bold blue]{key}[/bold blue]")
                add_dict_to_tree(branch, value, f"{prefix}.{key}")
            elif isinstance(value, list):
                branch = parent_tree.add(
                    f"[bold blue]{key}[/bold blue] [dim](list)[/dim]"
                )
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        item_branch = branch.add(f"[yellow]Item {i}[/yellow]")
                        add_dict_to_tree(item_branch, item, f"{prefix}.{key}[{i}]")
                    else:
                        branch.add(f"[green]{item}[/green]")
            else:
                # Mask sensitive values
                if any(
                    sensitive in key.lower()
                    for sensitive in ["password", "key", "token", "secret"]
                ):
                    display_value = "[dim]***[/dim]"
                else:
                    display_value = f"[green]{value}[/green]"
                parent_tree.add(f"[blue]{key}[/blue]: {display_value}")

    add_dict_to_tree(tree, config)
    console.print(tree)


def display_logs(
    console: Console, logs: list[dict[str, Any]], max_lines: int = 50
) -> None:
    """Display recent logs in a formatted way."""
    console.print(
        f"📋 [bold blue]Recent Logs[/bold blue] (last {min(len(logs), max_lines)} entries)"
    )

    for log in logs[-max_lines:]:
        timestamp = log.get("timestamp", "Unknown")
        level = log.get("level", "INFO")
        message = log.get("message", "")

        level_colors = {
            "DEBUG": "dim",
            "INFO": "blue",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold red",
        }

        level_color = level_colors.get(level, "white")
        console.print(
            f"[dim]{timestamp}[/dim] [{level_color}]{level:8}[/{level_color}] {message}"
        )


def create_progress_bar(console: Console, description: str) -> Progress:
    """Create a progress bar for long-running operations."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    )


def display_security_scan_results(console: Console, results: dict[str, Any]) -> None:
    """Display security scan results."""
    console.print("\n🔒 [bold blue]Security Scan Results[/bold blue]")

    # Summary
    total_issues = results.get("total_issues", 0)
    if total_issues == 0:
        display_success(console, "No security issues found!")
    else:
        display_warning(console, f"Found {total_issues} security issues")

    # Issues by severity
    issues_by_severity = results.get("issues_by_severity", {})
    if issues_by_severity:
        table = Table(
            title="Issues by Severity", show_header=True, header_style="bold red"
        )
        table.add_column("Severity", style="red")
        table.add_column("Count", justify="right", style="yellow")

        for severity, count in issues_by_severity.items():
            table.add_row(severity.upper(), str(count))

        console.print(table)

    # Detailed issues
    issues = results.get("issues", [])
    if issues:
        console.print("\n[bold red]Detailed Issues:[/bold red]")
        for i, issue in enumerate(issues[:10], 1):  # Show first 10 issues
            console.print(
                f"\n[bold red]{i}.[/bold red] [yellow]{issue.get('test_name', 'Unknown')}[/yellow]"
            )
            console.print(f"   File: [cyan]{issue.get('filename', 'Unknown')}[/cyan]")
            console.print(
                f"   Line: [blue]{issue.get('line_number', 'Unknown')}[/blue]"
            )
            console.print(
                f"   Severity: [red]{issue.get('issue_severity', 'Unknown')}[/red]"
            )
            console.print(f"   Message: {issue.get('issue_text', 'No message')}")

        if len(issues) > 10:
            console.print(f"\n[dim]... and {len(issues) - 10} more issues[/dim]")


def display_task_progress(console: Console, tasks: list[dict[str, Any]]) -> None:
    """Display task progress in a formatted way."""
    console.print("\n📋 [bold blue]Task Progress[/bold blue]")

    for task in tasks:
        status = task.get("status", "unknown")
        name = task.get("name", "Unknown Task")
        progress = task.get("progress", 0)

        status_emoji = {
            "pending": "⏳",
            "running": "🔄",
            "completed": "✅",
            "failed": "❌",
            "cancelled": "🚫",
        }.get(status, "❓")

        progress_bar = "█" * (progress // 10) + "░" * (10 - progress // 10)
        console.print(f"{status_emoji} {name}: [{progress_bar}] {progress}%")
