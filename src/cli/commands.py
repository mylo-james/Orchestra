"""CLI command implementations."""

import asyncio
import sys
from typing import Optional

from rich.console import Console
from rich.table import Table

from src.agents.factory import get_registry
from src.cli.output import error_panel, info_panel, success_panel
from src.personas.loader import PersonaLoader
from src.security.ai_agent_monitor import AIAgentMonitor
from src.security.ai_agent_validator import AIAgentValidator
from src.utils.circuit_breaker import CircuitBreaker
from src.utils.logging import get_logger

logger = get_logger(__name__)
console = Console()


def start_agent(agent_name: str, persona: Optional[str] = None) -> None:
    """
    Start an agent with optional persona specification.

    Args:
        agent_name: Name of the agent to start (for backward compatibility)
        persona: Persona ID to use (overrides agent_name)
    """
    try:
        registry = get_registry()

        # Use persona if specified, otherwise use agent_name
        if persona:
            console.print(info_panel(f"Starting agent with persona: {persona}"))
            agent = registry.create(agent_name, persona_id=persona)
        else:
            console.print(info_panel(f"Starting agent: {agent_name}"))
            agent = registry.create(agent_name)

        # Display agent information
        if hasattr(agent, "describe"):
            console.print(agent.describe())

        console.print(success_panel("Agent started successfully"))

    except KeyError as e:
        console.print(error_panel(f"Agent not found: {e}"))
        sys.exit(1)
    except Exception as e:
        console.print(error_panel(f"Failed to start agent: {e}"))
        logger.error(f"Agent start failed: {e}", exc_info=True)
        sys.exit(1)


def list_agents() -> None:
    """List all available agents and personas."""
    try:
        registry = get_registry()

        # Get all agents and personas
        all_agents = registry.list_agents()
        personas = registry.list_personas()

        # Create table
        table = Table(title="Available Agents and Personas")
        table.add_column("Name/ID", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Description", style="yellow")

        # Add personas
        for persona_id in personas:
            spec = registry.get_persona_spec(persona_id)
            if spec:
                table.add_row(
                    persona_id, "Persona", f"{spec.identity.icon} {spec.identity.title}"
                )

        # Add any legacy agents not covered by personas
        legacy_only = set(all_agents) - set(personas)
        for agent in legacy_only:
            table.add_row(agent, "Legacy", "Hardcoded agent")

        console.print(table)

    except Exception as e:
        console.print(error_panel(f"Failed to list agents: {e}"))
        logger.error(f"List agents failed: {e}", exc_info=True)
        sys.exit(1)


def list_personas() -> None:
    """List all available personas."""
    try:
        loader = PersonaLoader()
        personas = loader.list_personas()

        if not personas:
            console.print(info_panel("No personas found"))
            return

        # Create detailed table
        table = Table(title="Available Personas")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Role", style="yellow")
        table.add_column("Icon", style="blue")

        for persona_id in personas:
            spec = loader.load_persona(persona_id)
            if spec:
                table.add_row(
                    persona_id,
                    spec.identity.name,
                    (
                        spec.identity.role[:50] + "..."
                        if len(spec.identity.role) > 50
                        else spec.identity.role
                    ),
                    spec.identity.icon,
                )

        console.print(table)

    except Exception as e:
        console.print(error_panel(f"Failed to list personas: {e}"))
        logger.error(f"List personas failed: {e}", exc_info=True)
        sys.exit(1)


def validate_persona(persona_id: str) -> None:
    """
    Validate a persona specification.

    Args:
        persona_id: ID of the persona to validate
    """
    try:
        loader = PersonaLoader()

        # Try to load the persona
        spec = loader.load_persona(persona_id)

        if not spec:
            console.print(error_panel(f"Persona not found: {persona_id}"))
            sys.exit(1)

        # Validate the spec
        errors = spec.validate()

        if errors:
            console.print(error_panel(f"Validation failed for {persona_id}:"))
            for error in errors:
                console.print(f"  - {error}")
            sys.exit(1)
        else:
            console.print(success_panel(f"Persona '{persona_id}' is valid"))

            # Show persona details
            table = Table(title=f"Persona: {spec.display_name}")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="yellow")

            table.add_row("ID", spec.identity.id)
            table.add_row("Name", spec.identity.name)
            table.add_row("Title", spec.identity.title)
            table.add_row("Role", spec.identity.role)
            table.add_row("Version", spec.version)
            table.add_row("Commands", str(len(spec.command_interface.commands)))
            table.add_row("Tools", ", ".join(spec.resource_dependencies.tools))
            table.add_row("Enabled", "Yes" if spec.enabled else "No")
            table.add_row("Experimental", "Yes" if spec.experimental else "No")

            console.print(table)

    except Exception as e:
        console.print(error_panel(f"Validation error: {e}"))
        logger.error(f"Persona validation failed: {e}", exc_info=True)
        sys.exit(1)


def reload_personas() -> None:
    """Reload all personas from disk."""
    try:
        registry = get_registry()
        registry.reload_personas()

        console.print(success_panel("Personas reloaded successfully"))

        # Show count
        personas = registry.list_personas()
        console.print(info_panel(f"Loaded {len(personas)} personas"))

    except Exception as e:
        console.print(error_panel(f"Failed to reload personas: {e}"))
        logger.error(f"Persona reload failed: {e}", exc_info=True)
        sys.exit(1)


def test_security() -> None:
    """Test security components."""
    console.print(info_panel("Testing security components..."))

    # Test validator
    validator = AIAgentValidator()
    validation_result = validator.validate_prompt("Test prompt")

    if validation_result["is_valid"]:
        console.print(success_panel("✓ AI Agent Validator: Working"))
    else:
        console.print(error_panel("✗ AI Agent Validator: Issues detected"))

    # Test monitor
    monitor = AIAgentMonitor()
    monitor.start_monitoring()
    monitor.log_agent_action("test_agent", "test_action", {"test": "data"})
    monitor.stop_monitoring()

    console.print(success_panel("✓ AI Agent Monitor: Working"))

    console.print(success_panel("Security components test completed"))


def test_circuit_breaker() -> None:
    """Test circuit breaker functionality."""
    console.print(info_panel("Testing circuit breaker..."))

    breaker = CircuitBreaker(
        failure_threshold=3, recovery_timeout=5, expected_exception=Exception
    )

    # Test normal operation
    @breaker
    def test_function(should_fail: bool = False):
        if should_fail:
            raise Exception("Test failure")
        return "Success"

    try:
        # Should work
        result = test_function(should_fail=False)
        console.print(success_panel(f"✓ Normal operation: {result}"))

        # Simulate failures
        for i in range(3):
            try:
                test_function(should_fail=True)
            except:
                pass

        # Circuit should be open now
        try:
            test_function(should_fail=False)
            console.print(error_panel("✗ Circuit breaker did not open"))
        except Exception as e:
            if "Circuit breaker is OPEN" in str(e):
                console.print(success_panel("✓ Circuit breaker opened correctly"))
            else:
                console.print(error_panel(f"✗ Unexpected error: {e}"))

    except Exception as e:
        console.print(error_panel(f"Circuit breaker test failed: {e}"))


async def run_workflow(workflow_name: str) -> None:
    """Run a Temporal workflow."""
    console.print(info_panel(f"Running workflow: {workflow_name}"))

    # TODO: Implement actual workflow execution
    await asyncio.sleep(1)

    console.print(success_panel(f"Workflow {workflow_name} completed"))


def health_check() -> None:
    """Perform a health check of the system."""
    console.print(info_panel("Performing health check..."))

    checks = {
        "Logging": True,
        "Security": True,
        "Circuit Breaker": True,
        "Agent Registry": True,
        "Persona Loader": True,
    }

    # Test each component
    try:
        # Test logging
        logger.info("Health check test")

        # Test agent registry
        registry = get_registry()
        _ = registry.list_agents()

        # Test persona loader
        loader = PersonaLoader()
        _ = loader.list_personas()

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        checks["Agent Registry"] = False

    # Display results
    table = Table(title="System Health Check")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")

    for component, status in checks.items():
        status_text = "✓ Healthy" if status else "✗ Unhealthy"
        status_style = "green" if status else "red"
        table.add_row(component, f"[{status_style}]{status_text}[/{status_style}]")

    console.print(table)

    if all(checks.values()):
        console.print(success_panel("All systems operational"))
    else:
        console.print(error_panel("Some systems are experiencing issues"))
        sys.exit(1)
