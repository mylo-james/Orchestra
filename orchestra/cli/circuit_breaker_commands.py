"""
Circuit Breaker monitoring CLI commands for Orchestra.
"""

from datetime import datetime
from typing import Optional

import typer
from rich.console import Console
from rich.progress import BarColumn, Progress, TextColumn
from rich.table import Table

from orchestra.utils.circuit_breaker import (
    circuit_breaker_health_check,
    get_circuit_breaker_stats,
    reset_all_circuit_breakers,
)

# Initialize console for rich output
console = Console()

# Create circuit breaker CLI app
cb_app = typer.Typer(
    name="circuit-breakers",
    help="External Service Circuit Breaker Commands",
    rich_markup_mode="rich",
)


@cb_app.command("status")
def circuit_breaker_status():
    """
    Show status of all external service circuit breakers.
    """
    try:
        health = circuit_breaker_health_check()
        stats = get_circuit_breaker_stats()

        console.print(
            "\n⚡ [bold blue]External Service Circuit Breaker Status[/bold blue]"
        )
        console.print("=" * 60)

        # Overall health summary
        if health["healthy"]:
            console.print(
                f"🟢 [bold green]All Services Healthy[/bold green] - {health['summary']}"
            )
        else:
            console.print(
                f"🔴 [bold red]Service Failures Detected[/bold red] - {health['summary']}"
            )
            console.print(
                f"   [red]Failing services: {', '.join(health['failing_services'])}[/red]"
            )

        console.print()

        # Individual service status
        if stats:
            services_table = Table(show_header=True, header_style="bold magenta")
            services_table.add_column("Service", style="cyan")
            services_table.add_column("State", justify="center")
            services_table.add_column("Requests", justify="right")
            services_table.add_column("Success Rate", justify="right")
            services_table.add_column("Failures", justify="right")
            services_table.add_column("Last Activity")

            for service_name, service_stats in stats.items():
                # Determine state color and icon
                state = service_stats["state"]
                if state == "closed":
                    state_display = "[green]🟢 CLOSED[/green]"
                elif state == "open":
                    state_display = "[red]🔴 OPEN[/red]"
                elif state == "half_open":
                    state_display = "[yellow]🟡 HALF-OPEN[/yellow]"
                else:
                    state_display = f"[white]{state.upper()}[/white]"

                # Success rate with color coding
                success_rate = service_stats["success_rate"]
                if success_rate >= 0.95:
                    success_display = f"[green]{success_rate:.1%}[/green]"
                elif success_rate >= 0.80:
                    success_display = f"[yellow]{success_rate:.1%}[/yellow]"
                else:
                    success_display = f"[red]{success_rate:.1%}[/red]"

                # Last activity
                last_success = service_stats["stats"].get("last_success_time")
                if last_success:
                    last_activity = datetime.fromisoformat(last_success).strftime(
                        "%H:%M:%S"
                    )
                else:
                    last_activity = "Never"

                services_table.add_row(
                    service_name.replace("_", " ").title(),
                    state_display,
                    str(service_stats["stats"]["total_requests"]),
                    success_display,
                    str(service_stats["consecutive_failures"]),
                    last_activity,
                )

            console.print(services_table)
        else:
            console.print("[yellow]No circuit breakers active yet[/yellow]")

        # Show failing services details
        if health["failing_services"]:
            console.print("\n🚨 [bold red]Failing Services Details:[/bold red]")
            for service in health["failing_services"]:
                service_stats = stats.get(service, {})
                failures = service_stats.get("consecutive_failures", 0)
                last_failure = service_stats.get("stats", {}).get(
                    "last_failure_time", "Unknown"
                )

                console.print(
                    f"  • [red]{service}[/red]: {failures} consecutive failures"
                )
                if last_failure != "Unknown":
                    failure_time = datetime.fromisoformat(last_failure).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    console.print(f"    Last failure: {failure_time}")

    except Exception as e:
        console.print(f"[red]❌ Error getting circuit breaker status: {e}[/red]")
        raise typer.Exit(1)


@cb_app.command("reset")
def reset_circuit_breakers(
    service: Optional[str] = typer.Option(
        None, "--service", "-s", help="Reset specific service (or all if not specified)"
    ),
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
):
    """
    Reset circuit breakers to closed state.
    """
    try:
        if not confirm:
            if service:
                user_confirm = typer.confirm(f"Reset circuit breaker for {service}?")
            else:
                user_confirm = typer.confirm("Reset ALL circuit breakers?")

            if not user_confirm:
                console.print("Reset cancelled")
                return

        if service:
            # Reset specific service (not implemented in current version)
            console.print(
                "[yellow]Resetting specific services not yet implemented[/yellow]"
            )
            console.print(
                "Use --service option when available, or reset all with no --service"
            )
        else:
            # Reset all
            reset_all_circuit_breakers()
            console.print(
                "✅ [green]All circuit breakers reset to closed state[/green]"
            )

    except Exception as e:
        console.print(f"[red]❌ Error resetting circuit breakers: {e}[/red]")
        raise typer.Exit(1)


@cb_app.command("health")
def circuit_breaker_health():
    """
    Check health of external service circuit breakers.
    """
    try:
        health = circuit_breaker_health_check()

        console.print("\n🏥 [bold blue]Circuit Breaker Health Check[/bold blue]")
        console.print("=" * 50)

        if health["healthy"]:
            console.print("✅ [green]All external services are healthy[/green]")
        else:
            console.print("❌ [red]Some external services are failing[/red]")

        console.print(f"Status: {health['summary']}")
        console.print(f"Total circuit breakers: {health['total_circuit_breakers']}")
        console.print(f"Open (failing) breakers: {health['open_circuit_breakers']}")

        if health["failing_services"]:
            console.print(
                f"Failing services: [red]{', '.join(health['failing_services'])}[/red]"
            )

        # Service availability visualization
        if health["total_circuit_breakers"] > 0:
            console.print("\n📊 Service Availability:")

            healthy_count = (
                health["total_circuit_breakers"] - health["open_circuit_breakers"]
            )

            with Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                expand=True,
                console=console,
            ) as progress:
                progress.add_task(
                    f"Healthy Services ({healthy_count}/{health['total_circuit_breakers']})",
                    total=health["total_circuit_breakers"],
                    completed=healthy_count,
                )

    except Exception as e:
        console.print(f"[red]❌ Error checking circuit breaker health: {e}[/red]")
        raise typer.Exit(1)


@cb_app.command("simulate-failure")
def simulate_service_failure(
    service: str = typer.Argument(help="Service name to simulate failure for"),
    failure_count: int = typer.Option(
        5, "--failures", "-f", help="Number of failures to simulate"
    ),
):
    """
    Simulate service failures for testing circuit breaker behavior.
    """
    try:
        console.print(
            f"\n🧪 [bold yellow]Simulating {failure_count} failures for {service}[/bold yellow]"
        )

        # This would need to be implemented to actually trigger failures
        # For now, just show what would happen
        console.print("[yellow]Failure simulation not yet implemented[/yellow]")
        console.print(f"Would simulate {failure_count} failures for {service}")
        console.print("Use this for testing circuit breaker behavior in development")

    except Exception as e:
        console.print(f"[red]❌ Error simulating failures: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    cb_app()
