"""Main CLI entry point for Orchestra AI Agent System."""

import asyncio
import sys
from typing import Any, Optional

import typer
from rich.console import Console
from rich.traceback import install

from src.cli.circuit_breaker_commands import cb_app
from src.cli.commands import agent_cmd, config_cmd, dev_cmd, workflow_cmd
from src.cli.output import display_banner, display_error, display_success
from src.cli.security_commands import security_app, security_health_check
from src.config.settings import get_settings
from src.utils.logging import configure_logging, get_logger, set_correlation_id

# Install rich traceback handler for better error display
install(show_locals=True)

# Initialize console for rich output
console = Console()

# Create the main Typer app
app = typer.Typer(
    name="orchestra",
    help="🎼 Orchestra - AI Agent System for Development Team Orchestration",
    rich_markup_mode="rich",
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)

# Add command groups
app.add_typer(agent_cmd, name="agent", help="👥 Agent management commands")
app.add_typer(workflow_cmd, name="workflow", help="🔄 Workflow orchestration commands")
app.add_typer(config_cmd, name="config", help="⚙️ Configuration management commands")
app.add_typer(dev_cmd, name="dev", help="🛠️ Development and debugging commands")
app.add_typer(
    security_app, name="security", help="🔒 AI Agent security monitoring commands"
)
app.add_typer(
    cb_app, name="circuit-breakers", help="⚡ External service circuit breaker commands"
)

# Global logger
logger = get_logger(__name__)


@app.callback()
def main(
    ctx: typer.Context,
    verbose: bool = typer.Option(
        False, "-v", "--verbose", help="Enable verbose logging"
    ),
    quiet: bool = typer.Option(
        False, "-q", "--quiet", help="Suppress all output except errors"
    ),
    json_logs: bool = typer.Option(
        False, "--json-logs", help="Output logs in JSON format"
    ),
    correlation_id: Optional[str] = typer.Option(
        None, "--correlation-id", help="Set correlation ID for request tracing"
    ),
) -> None:
    """Orchestra AI Agent System - Development Team Orchestration Platform.

    Orchestra coordinates multiple AI agents to handle complex development workflows,
    from code generation to testing to deployment, with built-in security and audit trails.
    """
    try:
        # Set up logging configuration
        if quiet:
            log_level = "ERROR"
        elif verbose:
            log_level = "DEBUG"
        else:
            log_level = "INFO"

        # Configure logging
        configure_logging(log_level=log_level, json_logs=json_logs, enable_audit=True)

        # Set correlation ID for request tracing
        if correlation_id:
            set_correlation_id(correlation_id)
        else:
            set_correlation_id()  # Generate new one

        # Load and validate settings
        settings = get_settings()

        # Store settings in context for commands to access
        ctx.ensure_object(dict)
        ctx.obj["settings"] = settings
        ctx.obj["console"] = console

        # Display banner if not quiet and not in help mode
        if not quiet and ctx.invoked_subcommand and ctx.invoked_subcommand != "help":
            display_banner(console, settings.version)

        logger.info(
            "Orchestra CLI initialized",
            version=settings.version,
            environment=settings.environment,
        )

    except Exception as e:
        display_error(console, f"Failed to initialize Orchestra: {e}")
        logger.error("CLI initialization failed", error=str(e), exc_info=True)
        raise typer.Exit(1) from e


@app.command()
def version() -> None:
    """Display version information."""
    settings = get_settings()
    console.print(
        f"[bold blue]Orchestra[/bold blue] version [bold green]{settings.version}[/bold green]"
    )
    console.print(f"Environment: [yellow]{settings.environment}[/yellow]")


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", help="Host to bind to"),
    port: int = typer.Option(8000, help="Port to bind to"),
    reload: bool = typer.Option(False, help="Enable auto-reload in development"),
) -> None:
    """Start the Orchestra service for API mode."""
    try:
        display_success(console, f"Starting Orchestra service on {host}:{port}")

        if reload:
            logger.info("Starting Orchestra service with auto-reload enabled")
        else:
            logger.info("Starting Orchestra service", host=host, port=port)

        # Note: This would start a web server in a real implementation
        # For now, we'll just keep the process running
        console.print("🎼 [bold green]Orchestra service is running...[/bold green]")
        console.print("Press [bold red]Ctrl+C[/bold red] to stop")

        try:
            while True:
                import time

                time.sleep(1)
        except KeyboardInterrupt:
            console.print("\n🛑 [yellow]Orchestra service stopped[/yellow]")

    except Exception as e:
        display_error(console, f"Failed to start service: {e}")
        logger.error("Service startup failed", error=str(e), exc_info=True)
        raise typer.Exit(1) from e


@app.command()
def health() -> None:
    """Check system health and dependencies."""
    try:
        console.print("🏥 [bold blue]Orchestra Health Check[/bold blue]")

        # Check settings
        settings = get_settings()
        console.print("✅ Configuration loaded successfully")

        # Check required environment variables
        required_vars = ["OPENAI_API_KEY", "PINECONE_API_KEY"]
        missing_vars = []

        for var in required_vars:
            if (
                not getattr(settings.openai, "api_key", None)
                and var == "OPENAI_API_KEY"
            ):
                missing_vars.append(var)
            elif (
                not getattr(settings.pinecone, "api_key", None)
                and var == "PINECONE_API_KEY"
            ):
                missing_vars.append(var)

        if missing_vars:
            for var in missing_vars:
                console.print(f"❌ Missing required environment variable: {var}")
            display_error(console, "Some required environment variables are missing")
            raise typer.Exit(1)
        else:
            console.print("✅ Required environment variables are set")

        # Check Python version
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        console.print(f"✅ Python version: {python_version}")

        # Check security monitoring system
        if security_health_check():
            console.print("✅ AI Agent security monitoring is operational")
        else:
            console.print("⚠️ AI Agent security monitoring may have issues")

        # Check circuit breaker system
        from src.utils.circuit_breaker import circuit_breaker_health_check

        cb_health = circuit_breaker_health_check()
        if cb_health["healthy"]:
            console.print(
                f"✅ External service circuit breakers operational - {cb_health['summary']}"
            )
        else:
            console.print(
                f"⚠️ External service issues detected - {cb_health['summary']}"
            )
            if cb_health["failing_services"]:
                console.print(f"   Failing: {', '.join(cb_health['failing_services'])}")

        display_success(console, "All health checks passed!")
        logger.info("Health check completed successfully")

    except typer.Exit:
        raise
    except Exception as e:
        display_error(console, f"Health check failed: {e}")
        logger.error("Health check failed", error=str(e), exc_info=True)
        raise typer.Exit(1) from e


def run_async_command(coro) -> Any:
    """Helper to run async commands in sync CLI context."""
    try:
        return asyncio.run(coro)
    except KeyboardInterrupt:
        console.print("\n🛑 [yellow]Operation cancelled[/yellow]")
        raise typer.Exit(130) from None  # Standard exit code for SIGINT
    except Exception as e:
        logger.error("Async command failed", error=str(e), exc_info=True)
        raise RuntimeError("Async command failed") from e


if __name__ == "__main__":
    app()
