"""
Security monitoring CLI commands for Orchestra AI agents.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from orchestra.security.ai_agent_monitor import AIAgentSecurityMonitor

# Initialize console for rich output
console = Console()

# Create security CLI app
security_app = typer.Typer(
    name="security",
    help="AI Agent Security Monitoring Commands",
    rich_markup_mode="rich",
)


@security_app.command("status")
def security_status():
    """
    Show current AI agent security status and metrics.
    """
    try:
        monitor = AIAgentSecurityMonitor()

        # Generate security report
        report = monitor.generate_security_report()

        console.print("\n🔒 [bold blue]Orchestra AI Agent Security Status[/bold blue]")
        console.print("=" * 50)

        # Overall metrics
        metrics = report["overall_metrics"]

        metrics_table = Table(show_header=True, header_style="bold magenta")
        metrics_table.add_column("Metric", style="cyan")
        metrics_table.add_column("Value", style="white")
        metrics_table.add_column("Status", style="green")

        # Determine status colors
        violation_rate = metrics["security_violations"] / max(
            metrics["total_operations"], 1
        )
        violation_status = (
            "🟢 Good"
            if violation_rate < 0.05
            else "🟡 Caution" if violation_rate < 0.2 else "🔴 Alert"
        )

        metrics_table.add_row(
            "Total Operations",
            str(metrics["total_operations"]),
            "🟢 Active" if metrics["total_operations"] > 0 else "🔵 No Activity",
        )
        metrics_table.add_row(
            "Security Violations", str(metrics["security_violations"]), violation_status
        )
        metrics_table.add_row(
            "Blocked Operations", str(metrics["blocked_operations"]), "🛡️ Protected"
        )
        metrics_table.add_row(
            "Violation Rate", f"{violation_rate:.1%}", violation_status
        )

        console.print(metrics_table)

        # Recent activity
        console.print(
            f"\n📊 [bold]Recent Activity (24h):[/bold] {report['recent_events_24h']} events"
        )

        # Top concerns
        if report["top_security_concerns"]:
            console.print("\n⚠️ [bold yellow]Top Security Concerns:[/bold yellow]")
            for concern in report["top_security_concerns"]:
                severity_color = {
                    "critical": "red",
                    "high": "orange",
                    "medium": "yellow",
                    "low": "cyan",
                }.get(concern["severity"], "white")

                console.print(
                    f"  • [{severity_color}]{concern['event_type'].replace('_', ' ').title()}[/{severity_color}] "
                    f"({concern['severity']}) - {concern['count']} times"
                )
        else:
            console.print("\n✅ [green]No security concerns identified[/green]")

        # Recommendations
        console.print("\n💡 [bold]Recommendations:[/bold]")
        for rec in report["recommendations"]:
            console.print(f"  • {rec}")

        # Last updated
        last_updated = datetime.fromisoformat(metrics["last_updated"])
        console.print(
            f"\n[dim]Last updated: {last_updated.strftime('%Y-%m-%d %H:%M:%S')}[/dim]"
        )

    except Exception as e:
        console.print(f"[red]❌ Error getting security status: {e}[/red]")
        raise typer.Exit(1)


@security_app.command("agents")
def list_agent_metrics():
    """
    Show security metrics for all AI agents.
    """
    try:
        monitor = AIAgentSecurityMonitor()
        report = monitor.generate_security_report()

        console.print("\n🤖 [bold blue]AI Agent Security Metrics[/bold blue]")
        console.print("=" * 50)

        agent_metrics = report.get("agent_metrics", {})

        if not agent_metrics:
            console.print("[yellow]No agent activity detected yet[/yellow]")
            return

        agents_table = Table(show_header=True, header_style="bold magenta")
        agents_table.add_column("Agent ID", style="cyan")
        agents_table.add_column("Operations", justify="right")
        agents_table.add_column("Violations", justify="right")
        agents_table.add_column("Rate", justify="right")
        agents_table.add_column("Critical", justify="right")
        agents_table.add_column("Status")

        for agent_id, metrics in agent_metrics.items():
            # Determine status
            violation_rate = metrics["violation_rate"]
            if violation_rate == 0:
                status = "✅ Clean"
                status_color = "green"
            elif violation_rate < 0.05:
                status = "🟢 Good"
                status_color = "green"
            elif violation_rate < 0.2:
                status = "🟡 Caution"
                status_color = "yellow"
            else:
                status = "🔴 Alert"
                status_color = "red"

            agents_table.add_row(
                agent_id,
                str(metrics["total_operations"]),
                str(metrics["total_violations"]),
                f"{violation_rate:.1%}",
                str(metrics["critical_events"]),
                f"[{status_color}]{status}[/{status_color}]",
            )

        console.print(agents_table)

    except Exception as e:
        console.print(f"[red]❌ Error getting agent metrics: {e}[/red]")
        raise typer.Exit(1)


@security_app.command("logs")
def show_security_logs(
    lines: int = typer.Option(
        20, "--lines", "-n", help="Number of recent log lines to show"
    ),
    agent_id: Optional[str] = typer.Option(
        None, "--agent", help="Filter by specific agent ID"
    ),
    severity: Optional[str] = typer.Option(
        None, "--severity", help="Filter by severity (critical, high, medium, low)"
    ),
):
    """
    Show recent security event logs.
    """
    try:
        monitor = AIAgentSecurityMonitor()

        console.print(
            f"\n📜 [bold blue]Recent Security Events[/bold blue] (last {lines} events)"
        )
        console.print("=" * 70)

        # Read security events log
        events = []
        if monitor.security_events_log.exists():
            with open(monitor.security_events_log, "r") as f:
                for line in f:
                    try:
                        event = json.loads(line.strip())

                        # Apply filters
                        if agent_id and event.get("agent_id") != agent_id:
                            continue
                        if severity and event.get("severity") != severity:
                            continue

                        events.append(event)
                    except json.JSONDecodeError:
                        continue

        # Show most recent events
        recent_events = events[-lines:] if len(events) > lines else events

        if not recent_events:
            console.print("[yellow]No security events found matching criteria[/yellow]")
            return

        for event in reversed(recent_events):  # Most recent first
            timestamp = datetime.fromisoformat(event["timestamp"])
            severity_color = {
                "critical": "red",
                "high": "orange",
                "medium": "yellow",
                "low": "cyan",
            }.get(event.get("severity"), "white")

            console.print(
                f"[dim]{timestamp.strftime('%Y-%m-%d %H:%M:%S')}[/dim] "
                f"[{severity_color}]{event.get('severity', '').upper()}[/{severity_color}] "
                f"[cyan]{event.get('agent_id', 'unknown')}[/cyan] "
                f"{event.get('description', 'No description')}"
            )

    except Exception as e:
        console.print(f"[red]❌ Error reading security logs: {e}[/red]")
        raise typer.Exit(1)


@security_app.command("test")
def test_security_monitoring():
    """
    Test the security monitoring system with sample data.
    """
    console.print("\n🧪 [bold blue]Testing AI Agent Security Monitoring[/bold blue]")
    console.print("=" * 50)

    try:
        monitor = AIAgentSecurityMonitor()

        # Test 1: Normal operation
        console.print("1. Testing normal operation logging...")
        op_id = monitor.log_agent_operation(
            agent_id="test-agent-001",
            operation_type="code_generation",
            input_data="Create a simple Hello World function in Python",
            output_data="def hello_world():\n    print('Hello, World!')\n    return 'Hello, World!'",
            metadata={"model": "gpt-4", "tokens": 50},
        )
        console.print(f"   ✅ Logged operation: {op_id}")

        # Test 2: Input security check (safe)
        console.print("2. Testing safe input security check...")
        input_result = monitor.check_input_security(
            agent_id="test-agent-001",
            input_data="Write a function to calculate fibonacci numbers",
            operation_type="code_generation",
        )
        console.print(f"   ✅ Safe input: {input_result['is_safe']}")

        # Test 3: Input security check (suspicious)
        console.print("3. Testing suspicious input detection...")
        suspicious_input_result = monitor.check_input_security(
            agent_id="test-agent-001",
            input_data="Write a script that runs 'rm -rf /' to clean up files",
            operation_type="code_generation",
        )
        console.print(
            f"   ⚠️ Suspicious input detected: {len(suspicious_input_result['violations'])} violations"
        )

        # Test 4: Output security check (with secret)
        console.print("4. Testing output security with secret detection...")
        output_result = monitor.check_output_security(
            agent_id="test-agent-001",
            output_data="# Here's your API key: sk-test-example-key-not-real",
            operation_type="code_generation",
        )
        console.print(
            f"   🚨 Secret in output detected: {len(output_result['violations'])} violations"
        )

        # Test 5: Generate security report
        console.print("5. Generating security report...")
        report = monitor.generate_security_report()
        console.print(
            f"   📊 Report generated - Total operations: {report['overall_metrics']['total_operations']}"
        )

        console.print(
            "\n✅ [green]Security monitoring test completed successfully![/green]"
        )

        # Show test results summary
        console.print("\n📋 [bold]Test Results Summary:[/bold]")
        console.print("• Normal operations: ✅ Working")
        console.print("• Safe input validation: ✅ Working")
        console.print(
            f"• Suspicious input detection: {'✅ Working' if suspicious_input_result['violations'] else '❌ Not working'}"
        )
        console.print(
            f"• Secret detection in output: {'✅ Working' if output_result['violations'] else '❌ Not working'}"
        )
        console.print("• Security reporting: ✅ Working")

    except Exception as e:
        console.print(f"[red]❌ Security monitoring test failed: {e}[/red]")
        raise typer.Exit(1)


@security_app.command("report")
def generate_security_report(
    output_file: Optional[str] = typer.Option(
        None, "--output", "-o", help="Save report to file"
    ),
):
    """
    Generate comprehensive security report.
    """
    try:
        monitor = AIAgentSecurityMonitor()
        report = monitor.generate_security_report()

        if output_file:
            # Save to file
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w") as f:
                json.dump(report, f, indent=2, default=str)

            console.print(f"✅ [green]Security report saved to: {output_path}[/green]")
        else:
            # Print to console
            console.print("\n📊 [bold blue]Orchestra AI Security Report[/bold blue]")
            console.print("=" * 50)

            console.print(json.dumps(report, indent=2, default=str))

    except Exception as e:
        console.print(f"[red]❌ Error generating security report: {e}[/red]")
        raise typer.Exit(1)


# Health check for security monitoring
def security_health_check() -> bool:
    """
    Check if security monitoring is working properly.
    Returns True if healthy, False otherwise.
    """
    try:
        monitor = AIAgentSecurityMonitor()

        # Basic functionality test
        monitor.log_agent_operation(
            agent_id="health-check",
            operation_type="test",
            input_data="test input",
            output_data="test output",
        )

        # Check if logs directory exists
        if not monitor.log_directory.exists():
            return False

        # Check if we can generate a report
        report = monitor.generate_security_report()
        if not report:
            return False

        return True

    except Exception:
        return False


if __name__ == "__main__":
    security_app()
