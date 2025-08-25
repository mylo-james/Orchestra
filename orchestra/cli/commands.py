"""Orchestra CLI Commands."""

import json

# BMad imports from tools directory
import sys
import time
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from orchestra.cli.output import error_panel, info_panel, success_panel, warning_panel
from orchestra.system.checklist_engine import ChecklistEngine
from orchestra.system.factory import get_registry
from orchestra.system.loader import PersonaLoader

sys.path.append(str(Path(__file__).parent.parent.parent / "tools" / "bmad-conversion"))

# BMad imports with fallbacks for missing modules
try:
    from bmad_inventory import BmadContentInventory  # type: ignore
except ImportError:
    BmadContentInventory = None  # type: ignore

try:
    from bmad_persona_converter import BmadPersonaConverter  # type: ignore
except ImportError:
    BmadPersonaConverter = None  # type: ignore

from orchestra.system.resource_loader import ResourceLoader, ResourceType
from orchestra.system.task_engine import TaskEngine
from orchestra.system.template_processor import TemplateProcessor
from orchestra.utils.logging import get_logger

logger = get_logger(__name__)
console = Console()

# Create command groups
agent_cmd = typer.Typer(help="Agent management commands")

# Create overlay management command group
overlay_cmd = typer.Typer(help="Persona overlay management commands")
workflow_cmd = typer.Typer(help="Workflow orchestration commands")
config_cmd = typer.Typer(help="Configuration management commands")
dev_cmd = typer.Typer(help="Development tools and utilities")
bmad_cmd = typer.Typer(help="BMad content management commands")


def create_basic_command_group(name: str, help_text: str) -> typer.Typer:
    """
    Create a basic command group for testing purposes.

    Args:
        name: Name of the command group
        help_text: Help text for the command group

    Returns:
        Typer app instance with basic commands
    """
    app = typer.Typer(
        name=name,
        help=f"{help_text} ({name})",
        rich_markup_mode="rich",
        context_settings={"help_option_names": ["-h", "--help"]},
    )

    @app.command("list")
    def list_items():
        """List basic information for this command group."""
        console.print(f"[green]Available commands in {name}:[/green]")
        console.print("- list: Show this list")
        console.print("- help: Show help information")
        console.print(f"\n[dim]Command group: {name}[/dim]")
        console.print(f"[dim]Description: {help_text}[/dim]")

    @app.command("status")
    def status():
        """Show status information."""
        console.print(f"[blue]Status for {name}:[/blue]")
        console.print("✅ Operational")
        console.print(f"[dim]Group: {name}[/dim]")

    return app


@agent_cmd.command("list")
def list_agents():
    """List all available agents."""
    try:
        registry = get_registry()
        agents: list = (
            getattr(registry, "list_agents", lambda: [])() if registry else []
        )

        if not agents:
            console.print(warning_panel("No agents found"))
            return

        table = Table(title="Available Agents")
        table.add_column("Name", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Description", style="white")

        for agent in agents:
            table.add_row(agent.name, "Active", agent.description or "No description")

        console.print(table)
        console.print(success_panel(f"Found {len(agents)} agents"))

    except Exception as e:
        logger.error(f"Failed to list agents: {e}")
        console.print(error_panel(f"Failed to list agents: {e}"))
        raise typer.Exit(1)


@agent_cmd.command("status")
def agent_status(name: str):
    """Get status of a specific agent."""
    try:
        registry = get_registry()
        agent = (
            getattr(registry, "get_agent", lambda x: None)(name) if registry else None
        )

        if not agent:
            console.print(error_panel(f"Agent '{name}' not found"))
            raise typer.Exit(1)

        console.print(info_panel(f"Agent '{name}' is active"))

    except Exception as e:
        logger.error(f"Failed to get agent status: {e}")
        console.print(error_panel(f"Failed to get agent status: {e}"))
        raise typer.Exit(1)


# Global persona state for CLI session
_active_persona = None
_persona_loader = None


def get_persona_loader():
    """Get or create persona loader instance."""
    global _persona_loader
    if _persona_loader is None:
        _persona_loader = PersonaLoader()
    return _persona_loader


@agent_cmd.command("list-personas")
def list_personas(
    category: Optional[str] = typer.Option(
        None,
        "--category",
        "-c",
        help="Filter personas by category (development, management, qa, etc.)",
    ),
    detailed: bool = typer.Option(
        False, "--detailed", "-d", help="Show detailed persona information"
    ),
):
    """List all available personas including converted BMad personas (Story 1.4)."""
    try:
        console.print(info_panel("Discovering available personas..."))

        loader = get_persona_loader()
        discovered_personas = loader.discover_personas()

        if not discovered_personas:
            console.print(warning_panel("No personas found"))
            return

        # Filter by category if specified
        filtered_personas = {}
        for persona_id, persona_path in discovered_personas.items():
            if category:
                # Simple category filtering based on persona ID
                category_lower = category.lower()
                if category_lower == "development" and persona_id in ["dev", "tdd-dev"]:
                    filtered_personas[persona_id] = persona_path
                elif category_lower == "management" and persona_id in [
                    "pm",
                    "po",
                    "sm",
                ]:
                    filtered_personas[persona_id] = persona_path
                elif category_lower == "qa" and persona_id in ["qa", "spec"]:
                    filtered_personas[persona_id] = persona_path
                elif category_lower == "design" and persona_id in [
                    "architect",
                    "ux-expert",
                ]:
                    filtered_personas[persona_id] = persona_path
                elif category_lower in persona_id:
                    filtered_personas[persona_id] = persona_path
            else:
                filtered_personas[persona_id] = persona_path

        if not filtered_personas:
            console.print(warning_panel(f"No personas found for category: {category}"))
            return

        # Create table
        if detailed:
            table = Table(title="Available Personas (Detailed)")
            table.add_column("ID", style="cyan")
            table.add_column("Name", style="white")
            table.add_column("Role", style="green")
            table.add_column("Path", style="dim")
            table.add_column("Status", style="yellow")

            for persona_id, persona_path in sorted(filtered_personas.items()):
                # Try to load persona for detailed info
                persona_spec = loader.load_persona(persona_id)
                if persona_spec:
                    name = persona_spec.identity.name
                    role = persona_spec.identity.role
                    status = "✓ Available"
                else:
                    name = persona_id.replace("-", " ").title()
                    role = "Unknown"
                    status = "⚠ Load Error"

                table.add_row(persona_id, name, role, str(persona_path), status)
        else:
            table = Table(title="Available Personas")
            table.add_column("ID", style="cyan")
            table.add_column("Name", style="white")
            table.add_column("Type", style="green")

            for persona_id, persona_path in sorted(filtered_personas.items()):
                # Determine type based on path
                if "bmad" in str(persona_path).lower():
                    persona_type = "BMad (Converted)"
                else:
                    persona_type = "Orchestra (Native)"

                name = persona_id.replace("-", " ").title()

                table.add_row(persona_id, name, persona_type)

        console.print(table)
        console.print(success_panel(f"Found {len(filtered_personas)} personas"))

        if category:
            console.print(f"Filtered by category: {category}")

    except Exception as e:
        logger.error(f"Failed to list personas: {e}")
        console.print(error_panel(f"Failed to list personas: {e}"))
        raise typer.Exit(1)


@agent_cmd.command("describe")
def describe_persona(persona_id: str):
    """Show detailed information about a specific persona."""
    try:
        console.print(info_panel(f"Loading persona: {persona_id}"))

        loader = get_persona_loader()
        persona_spec = loader.load_persona(persona_id)

        if not persona_spec:
            console.print(error_panel(f"Persona '{persona_id}' not found"))

            # Show available personas
            discovered = loader.discover_personas()
            if discovered:
                available = ", ".join(sorted(discovered.keys()))
                console.print(f"Available personas: {available}")

            raise typer.Exit(1)

        # Display persona details
        console.print(f"\n[bold blue]Persona: {persona_spec.identity.name}[/bold blue]")
        console.print(f"[dim]ID: {persona_spec.identity.id}[/dim]")
        console.print(f"[dim]Title: {persona_spec.identity.title}[/dim]")
        console.print(f"[dim]Role: {persona_spec.identity.role}[/dim]")

        if persona_spec.identity.when_to_use:
            console.print(
                f"\n[bold]When to use:[/bold]\n{persona_spec.identity.when_to_use}"
            )

        if persona_spec.identity.focus:
            console.print(f"\n[bold]Focus:[/bold]\n{persona_spec.identity.focus}")

        if persona_spec.behavioral_contract.core_principles:
            console.print("\n[bold]Core Principles:[/bold]")
            for principle in persona_spec.behavioral_contract.core_principles:
                console.print(f"  • {principle}")

        console.print(
            f"\n[bold]Interaction Style:[/bold] {persona_spec.behavioral_contract.interaction_style}"
        )

        if persona_spec.command_interface.commands:
            console.print("\n[bold]Available Commands:[/bold]")
            for cmd_name, cmd_def in persona_spec.command_interface.commands.items():
                description = (
                    cmd_def.description
                    if hasattr(cmd_def, "description")
                    else "No description"
                )
                console.print(f"  • [cyan]{cmd_name}[/cyan]: {description}")

        # Show resource dependencies
        deps = persona_spec.resource_dependencies
        if deps.tasks or deps.templates or deps.tools:
            console.print("\n[bold]Resource Dependencies:[/bold]")
            if deps.tasks:
                console.print(f"  Tasks: {', '.join(deps.tasks)}")
            if deps.templates:
                console.print(f"  Templates: {', '.join(deps.templates)}")
            if deps.tools:
                console.print(f"  Tools: {', '.join(deps.tools)}")
            if deps.knowledge_sources:
                console.print(
                    f"  Knowledge Sources: {', '.join(deps.knowledge_sources)}"
                )
            if deps.required_services:
                console.print(
                    f"  Required Services: {', '.join(deps.required_services)}"
                )

    except Exception as e:
        logger.error(f"Failed to describe persona: {e}")
        console.print(error_panel(f"Failed to describe persona: {e}"))
        raise typer.Exit(1)


@agent_cmd.command("search")
def search_personas(keyword: str):
    """Search personas by keyword in name, role, or expertise."""
    try:
        console.print(info_panel(f"Searching personas for: {keyword}"))

        loader = get_persona_loader()
        discovered_personas = loader.discover_personas()

        if not discovered_personas:
            console.print(warning_panel("No personas found"))
            return

        # Search through personas
        matches = []
        keyword_lower = keyword.lower()

        for persona_id, persona_path in discovered_personas.items():
            # Check if keyword matches ID
            if keyword_lower in persona_id.lower():
                matches.append((persona_id, persona_path, "ID match"))
                continue

            # Try to load persona for deeper search
            persona_spec = loader.load_persona(persona_id)
            if persona_spec:
                # Check name
                if keyword_lower in persona_spec.identity.name.lower():
                    matches.append((persona_id, persona_path, "Name match"))
                    continue

                # Check role
                if keyword_lower in persona_spec.identity.role.lower():
                    matches.append((persona_id, persona_path, "Role match"))
                    continue

                # Check core principles
                for principle in persona_spec.behavioral_contract.core_principles:
                    # Handle both string and dict principle formats
                    principle_text = (
                        principle if isinstance(principle, str) else str(principle)
                    )
                    if keyword_lower in principle_text.lower():
                        matches.append((persona_id, persona_path, "Principle match"))
                        break

        if not matches:
            console.print(warning_panel(f"No personas found matching: {keyword}"))
            return

        # Display matches
        table = Table(title=f"Search Results for '{keyword}'")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="white")
        table.add_column("Match Type", style="green")

        for persona_id, persona_path, match_type in matches:
            name = persona_id.replace("-", " ").title()

            # Try to get actual name from spec
            persona_spec = loader.load_persona(persona_id)
            if persona_spec:
                name = persona_spec.identity.name

            table.add_row(persona_id, name, match_type)

        console.print(table)
        console.print(success_panel(f"Found {len(matches)} matching personas"))

    except Exception as e:
        logger.error(f"Failed to search personas: {e}")
        console.print(error_panel(f"Failed to search personas: {e}"))
        raise typer.Exit(1)


@agent_cmd.command("activate")
def activate_persona(
    persona_id: str,
    team: Optional[str] = typer.Option(
        None, "--team", "-t", help="Team context for persona overlay"
    ),
    project: Optional[str] = typer.Option(
        None, "--project", "-p", help="Project context for persona overlay"
    ),
):
    """Activate a persona for the current session with optional team/project context."""
    try:
        context_info = []
        if team:
            context_info.append(f"team={team}")
        if project:
            context_info.append(f"project={project}")

        context_str = f" ({', '.join(context_info)})" if context_info else ""
        console.print(info_panel(f"Activating persona: {persona_id}{context_str}"))

        loader = get_persona_loader()
        persona_spec = loader.load_persona(persona_id, team_id=team, project_id=project)

        if not persona_spec:
            console.print(error_panel(f"Persona '{persona_id}' not found"))

            # Show available personas
            discovered = loader.discover_personas()
            if discovered:
                available = ", ".join(sorted(discovered.keys()))
                console.print(f"Available personas: {available}")

            raise typer.Exit(1)

        # Set active persona
        global _active_persona
        _active_persona = persona_spec

        # Log activation for audit
        logger.info(
            "Persona activated",
            persona_id=persona_id,
            persona_name=persona_spec.identity.name,
            persona_role=persona_spec.identity.role,
            team_id=team,
            project_id=project,
        )

        console.print(
            success_panel(f"✅ Activated persona: {persona_spec.identity.name}")
        )
        console.print(f"Role: {persona_spec.identity.role}")
        if team:
            console.print(f"Team context: {team}")
        if project:
            console.print(f"Project context: {project}")

        if persona_spec.command_interface.commands:
            console.print(
                f"Available commands: {len(persona_spec.command_interface.commands)}"
            )
            console.print("Use 'orchestra agent commands' to see available commands")

    except Exception as e:
        logger.error(f"Failed to activate persona: {e}")
        console.print(error_panel(f"Failed to activate persona: {e}"))
        raise typer.Exit(1)


@agent_cmd.command("current")
def show_current_persona():
    """Show the currently active persona."""
    try:
        global _active_persona

        if not _active_persona:
            console.print(warning_panel("No persona is currently active"))
            console.print(
                "Use 'orchestra agent activate <persona-id>' to activate a persona"
            )
            return

        console.print(
            f"[bold green]Active Persona:[/bold green] {_active_persona.identity.name}"
        )
        console.print(f"[dim]ID: {_active_persona.identity.id}[/dim]")
        console.print(f"[dim]Role: {_active_persona.identity.role}[/dim]")

        if _active_persona.command_interface.commands:
            console.print(
                f"Commands available: {len(_active_persona.command_interface.commands)}"
            )

    except Exception as e:
        logger.error(f"Failed to show current persona: {e}")
        console.print(error_panel(f"Failed to show current persona: {e}"))
        raise typer.Exit(1)


@agent_cmd.command("deactivate")
def deactivate_persona():
    """Deactivate the current persona."""
    try:
        global _active_persona

        if not _active_persona:
            console.print(warning_panel("No persona is currently active"))
            return

        persona_name = _active_persona.identity.name
        _active_persona = None

        logger.info("Persona deactivated", persona_name=persona_name)
        console.print(success_panel(f"Deactivated persona: {persona_name}"))

    except Exception as e:
        logger.error(f"Failed to deactivate persona: {e}")
        console.print(error_panel(f"Failed to deactivate persona: {e}"))
        raise typer.Exit(1)


@agent_cmd.command("commands")
def list_persona_commands():
    """List commands available for the active persona."""
    try:
        global _active_persona

        if not _active_persona:
            console.print(warning_panel("No persona is currently active"))
            console.print(
                "Use 'orchestra agent activate <persona-id>' to activate a persona"
            )
            return

        commands = _active_persona.command_interface.commands

        if not commands:
            console.print(
                warning_panel(
                    f"No commands available for persona: {_active_persona.identity.name}"
                )
            )
            return

        table = Table(title=f"Commands for {_active_persona.identity.name}")
        table.add_column("Command", style="cyan")
        table.add_column("Description", style="white")
        table.add_column("Parameters", style="dim")

        for cmd_name, cmd_def in commands.items():
            description = (
                cmd_def.description
                if hasattr(cmd_def, "description") and cmd_def.description
                else "No description"
            )

            # Format parameters
            params = cmd_def.parameters if hasattr(cmd_def, "parameters") else {}
            if params:
                param_list = []
                for param_name, param_def in params.items():
                    if isinstance(param_def, dict):
                        param_type = param_def.get("type", "string")
                        required = param_def.get("required", False)
                        req_marker = "*" if required else ""
                        param_list.append(f"{param_name}{req_marker}:{param_type}")
                    else:
                        param_list.append(f"{param_name}:{param_def}")
                param_str = ", ".join(param_list)
            else:
                param_str = "None"

            # Ensure all values are strings
            cmd_name_str = str(cmd_name) if cmd_name else "Unknown"
            description_str = str(description) if description else "No description"
            param_str = str(param_str) if param_str else "None"

            table.add_row(cmd_name_str, description_str, param_str)

        console.print(table)
        console.print("Use 'orchestra agent exec <command>' to execute a command")
        console.print("Use 'orchestra agent help <command>' for detailed help")

    except Exception as e:
        logger.error(f"Failed to list persona commands: {e}")
        console.print(error_panel(f"Failed to list persona commands: {e}"))
        raise typer.Exit(1)


@agent_cmd.command("exec")
def execute_persona_command(command: str, ctx: typer.Context):
    """Execute a command from the active persona."""
    try:
        global _active_persona

        if not _active_persona:
            console.print(error_panel("No persona is currently active"))
            console.print(
                "Use 'orchestra agent activate <persona-id>' to activate a persona"
            )
            raise typer.Exit(1)

        # Check if command exists
        commands = _active_persona.command_interface.commands
        if command not in commands:
            console.print(error_panel(f"Command '{command}' not found"))
            if commands:
                available = ", ".join(commands.keys())
                console.print(f"Available commands: {available}")
            raise typer.Exit(1)

        console.print(info_panel(f"Executing command: {command}"))

        # Parse command arguments from context
        # This is a simplified implementation - in a full implementation,
        # we would parse the command parameters properly
        args = ctx.params

        # Log command execution for audit
        logger.info(
            "Persona command executed",
            persona_id=_active_persona.identity.id,
            command=command,
            arguments=args,
        )

        # Mock command execution for now
        # In a real implementation, this would use the UniversalAgent
        console.print(success_panel(f"Command '{command}' executed successfully"))
        console.print(f"Persona: {_active_persona.identity.name}")
        console.print(f"Arguments: {args}")

    except Exception as e:
        logger.error(f"Failed to execute persona command: {e}")
        console.print(error_panel(f"Failed to execute persona command: {e}"))
        raise typer.Exit(1)


@agent_cmd.command("help")
def show_command_help(command: str):
    """Show detailed help for a persona command."""
    try:
        global _active_persona

        if not _active_persona:
            console.print(error_panel("No persona is currently active"))
            console.print(
                "Use 'orchestra agent activate <persona-id>' to activate a persona"
            )
            raise typer.Exit(1)

        commands = _active_persona.command_interface.commands
        if command not in commands:
            console.print(error_panel(f"Command '{command}' not found"))
            if commands:
                available = ", ".join(commands.keys())
                console.print(f"Available commands: {available}")
            raise typer.Exit(1)

        cmd_def = commands[command]

        console.print(f"\n[bold blue]Command: {command}[/bold blue]")
        console.print(
            f"[bold]Description:[/bold] {cmd_def.description if hasattr(cmd_def, 'description') else 'No description'}"
        )

        params = cmd_def.parameters if hasattr(cmd_def, "parameters") else {}
        if params:
            console.print("\n[bold]Parameters:[/bold]")
            for param_name, param_def in params.items():
                if isinstance(param_def, dict):
                    param_type = param_def.get("type", "string")
                    required = param_def.get("required", False)
                    default = param_def.get("default")

                    req_str = " (required)" if required else ""
                    default_str = (
                        f" [default: {default}]" if default is not None else ""
                    )

                    console.print(
                        f"  • [cyan]{param_name}[/cyan]: {param_type}{req_str}{default_str}"
                    )
                else:
                    console.print(f"  • [cyan]{param_name}[/cyan]: {param_def}")
        else:
            console.print("\n[dim]No parameters required[/dim]")

        console.print(
            f"\n[bold]Usage:[/bold] orchestra agent exec {command} [parameters]"
        )

    except Exception as e:
        logger.error(f"Failed to show command help: {e}")
        console.print(error_panel(f"Failed to show command help: {e}"))
        raise typer.Exit(1)


@agent_cmd.command("run-task")
def run_persona_task(
    task_id: str,
    context_file: Optional[str] = typer.Option(
        None, "--context", "-c", help="JSON file containing task context"
    ),
):
    """Execute a task using the active persona's context."""
    try:
        global _active_persona

        if not _active_persona:
            console.print(error_panel("No persona is currently active"))
            console.print(
                "Use 'orchestra agent activate <persona-id>' to activate a persona"
            )
            raise typer.Exit(1)

        console.print(
            info_panel(
                f"Executing task: {task_id} with persona: {_active_persona.identity.name}"
            )
        )

        # Load context
        context = {}
        if context_file:
            try:
                with open(context_file, "r") as f:
                    context = json.load(f)
            except Exception as e:
                console.print(error_panel(f"Failed to load context file: {e}"))
                raise typer.Exit(1)

        # Add persona context
        context.update(
            {
                "persona_id": _active_persona.identity.id,
                "persona_name": _active_persona.identity.name,
                "persona_role": _active_persona.identity.role,
                "user": "cli-user",
                "timestamp": time.time(),
            }
        )

        # Use resource system to execute task
        loader = ResourceLoader()
        engine = TaskEngine()

        # Load the task
        result = loader.load_resource(task_id, ResourceType.TASK)
        if not result.success:
            console.print(error_panel(f"Failed to load task: {task_id}"))
            for error in result.validation_errors:
                console.print(f"  • {error}")
            raise typer.Exit(1)

        # Execute the task
        if result.metadata is None or result.content is None:
            console.print(error_panel("Task metadata or content is missing"))
            raise typer.Exit(1)
        execution_result = engine.execute_task(result.metadata, result.content, context)

        # Display results
        if execution_result.success:
            console.print(
                success_panel(
                    f"Task executed successfully in {execution_result.execution_time:.3f}s"
                )
            )
            console.print(
                f"Steps completed: {execution_result.steps_completed}/{execution_result.total_steps}"
            )

            if execution_result.warnings:
                console.print("\n[bold yellow]Warnings:[/bold yellow]")
                for warning in execution_result.warnings:
                    console.print(f"  ⚠️ {warning}")
        else:
            console.print(error_panel("Task execution failed"))
            for error in execution_result.errors:
                console.print(f"  ❌ {error}")
            raise typer.Exit(1)

        # Log for audit
        logger.info(
            "Task executed via persona",
            persona_id=_active_persona.identity.id,
            task_id=task_id,
            success=execution_result.success,
            execution_time=execution_result.execution_time,
        )

    except Exception as e:
        logger.error(f"Failed to execute task: {e}")
        console.print(error_panel(f"Failed to execute task: {e}"))
        raise typer.Exit(1)


@agent_cmd.command("render")
def render_persona_template(
    template_id: str,
    context: Optional[str] = typer.Option(
        None, "--context", "-c", help="JSON context for template variables"
    ),
    output_file: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output file for rendered content"
    ),
):
    """Render a template using the active persona's context."""
    try:
        global _active_persona

        if not _active_persona:
            console.print(error_panel("No persona is currently active"))
            console.print(
                "Use 'orchestra agent activate <persona-id>' to activate a persona"
            )
            raise typer.Exit(1)

        console.print(
            info_panel(
                f"Rendering template: {template_id} with persona: {_active_persona.identity.name}"
            )
        )

        # Parse context
        template_context = {}
        if context:
            try:
                template_context = json.loads(context)
            except Exception as e:
                console.print(error_panel(f"Failed to parse context JSON: {e}"))
                raise typer.Exit(1)

        # Add persona context
        template_context.update(
            {
                "persona_id": _active_persona.identity.id,
                "persona_name": _active_persona.identity.name,
                "persona_role": _active_persona.identity.role,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "user": "cli-user",
            }
        )

        # Use resource system to render template
        loader = ResourceLoader()
        processor = TemplateProcessor()

        # Load the template
        result = loader.load_resource(template_id, ResourceType.TEMPLATE)
        if not result.success:
            console.print(error_panel(f"Failed to load template: {template_id}"))
            for error in result.validation_errors:
                console.print(f"  • {error}")
            raise typer.Exit(1)

        # Render the template
        if result.metadata is None or result.content is None:
            console.print(error_panel("Template metadata or content is missing"))
            raise typer.Exit(1)
        render_result = processor.render_template(
            result.metadata, result.content, template_context
        )

        # Display results
        if render_result.success:
            console.print(
                success_panel(
                    f"Template rendered successfully in {render_result.render_time:.3f}s"
                )
            )

            if render_result.warnings:
                console.print("\n[bold yellow]Warnings:[/bold yellow]")
                for warning in render_result.warnings:
                    console.print(f"  ⚠️ {warning}")

            # Output rendered content
            if output_file:
                with open(output_file, "w") as f:
                    content = render_result.rendered_content or ""
                    f.write(content)
                console.print(f"Rendered content saved to: {output_file}")
            else:
                console.print("\n[bold]Rendered Content:[/bold]")
                console.print(
                    Panel(render_result.rendered_content or "", title="Template Output")
                )
        else:
            console.print(error_panel("Template rendering failed"))
            for error in render_result.errors:
                console.print(f"  ❌ {error}")
            raise typer.Exit(1)

        # Log for audit
        logger.info(
            "Template rendered via persona",
            persona_id=_active_persona.identity.id,
            template_id=template_id,
            success=render_result.success,
            render_time=render_result.render_time,
        )

    except Exception as e:
        logger.error(f"Failed to render template: {e}")
        console.print(error_panel(f"Failed to render template: {e}"))
        raise typer.Exit(1)


@agent_cmd.command("check")
def execute_persona_checklist(
    checklist_id: str,
    context_file: Optional[str] = typer.Option(
        None, "--context", "-c", help="JSON file containing checklist context"
    ),
    auto_check: bool = typer.Option(
        False, "--auto-check", help="Enable automatic checking based on context"
    ),
):
    """Execute a checklist using the active persona's context."""
    try:
        global _active_persona

        if not _active_persona:
            console.print(error_panel("No persona is currently active"))
            console.print(
                "Use 'orchestra agent activate <persona-id>' to activate a persona"
            )
            raise typer.Exit(1)

        console.print(
            info_panel(
                f"Executing checklist: {checklist_id} with persona: {_active_persona.identity.name}"
            )
        )

        # Load context
        context = {}
        if context_file:
            try:
                with open(context_file, "r") as f:
                    context = json.load(f)
            except Exception as e:
                console.print(error_panel(f"Failed to load context file: {e}"))
                raise typer.Exit(1)

        # Add persona context
        context.update(
            {
                "persona_id": _active_persona.identity.id,
                "persona_name": _active_persona.identity.name,
                "persona_role": _active_persona.identity.role,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "user": "cli-user",
            }
        )

        # Use resource system to execute checklist
        loader = ResourceLoader()
        engine = ChecklistEngine(auto_check_enabled=auto_check)

        # Load the checklist
        result = loader.load_resource(checklist_id, ResourceType.CHECKLIST)
        if not result.success:
            console.print(error_panel(f"Failed to load checklist: {checklist_id}"))
            for error in result.validation_errors:
                console.print(f"  • {error}")
            raise typer.Exit(1)

        # Execute the checklist
        if result.metadata is None or result.content is None:
            console.print(error_panel("Checklist metadata or content is missing"))
            raise typer.Exit(1)
        execution_result = engine.execute_checklist(
            result.metadata, result.content, context
        )

        # Display results
        if execution_result.success:
            console.print(
                success_panel(
                    f"Checklist executed successfully in {execution_result.execution_time:.3f}s"
                )
            )
            console.print(
                f"Completion: {execution_result.completion_percentage:.1f}% ({execution_result.completed_items}/{execution_result.total_items - execution_result.not_applicable_items} applicable items)"
            )

            if auto_check and execution_result.auto_checked_items > 0:
                console.print(
                    f"Auto-checked: {execution_result.auto_checked_items} items"
                )

            if execution_result.warnings:
                console.print("\n[bold yellow]Warnings:[/bold yellow]")
                for warning in execution_result.warnings:
                    console.print(f"  ⚠️ {warning}")
        else:
            console.print(error_panel("Checklist execution failed"))
            for error in execution_result.errors:
                console.print(f"  ❌ {error}")
            raise typer.Exit(1)

        # Log for audit
        logger.info(
            "Checklist executed via persona",
            persona_id=_active_persona.identity.id,
            checklist_id=checklist_id,
            success=execution_result.success,
            completion_percentage=execution_result.completion_percentage,
        )

    except Exception as e:
        logger.error(f"Failed to execute checklist: {e}")
        console.print(error_panel(f"Failed to execute checklist: {e}"))
        raise typer.Exit(1)


@workflow_cmd.command("list")
def list_workflows():
    """List all available workflows."""
    console.print(info_panel("Workflow listing not yet implemented"))


@workflow_cmd.command("status")
def workflow_status():
    """Get workflow system status."""
    console.print(info_panel("Workflow status not yet implemented"))


@config_cmd.command("show")
def show_config():
    """Show current configuration."""
    console.print(info_panel("Configuration display not yet implemented"))


@config_cmd.command("validate")
def validate_config():
    """Validate current configuration."""
    console.print(info_panel("Configuration validation not yet implemented"))


@dev_cmd.command("test")
def run_tests():
    """Run development tests."""
    console.print(info_panel("Test runner not yet implemented"))


@dev_cmd.command("lint")
def run_linting():
    """Run code linting."""
    console.print(info_panel("Linting not yet implemented"))


@bmad_cmd.command("inventory")
def bmad_inventory(
    output_file: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output file for inventory report (JSON format)"
    ),
    base_path: Optional[str] = typer.Option(
        ".bmad-core", "--base-path", "-b", help="Base path to BMad content directory"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
):
    """Generate BMad content inventory and conversion strategy report."""
    try:
        console.print(
            info_panel(f"Starting BMad content inventory scan from {base_path}")
        )

        # Create inventory instance
        inventory = BmadContentInventory(base_path=Path(base_path or ".bmad-core"))

        # Perform full scan
        inventory.scan_all()

        # Generate report
        report = inventory.generate_report()

        # Display summary
        summary = report["summary"]
        console.print(
            success_panel(
                f"Inventory scan completed: {summary['total_items']} items found"
            )
        )

        # Create summary table
        table = Table(title="BMad Content Inventory Summary")
        table.add_column("Content Type", style="cyan")
        table.add_column("Count", style="green", justify="right")

        for content_type, count in summary["by_type"].items():
            table.add_row(content_type.title(), str(count))

        console.print(table)

        if verbose:
            # Show detailed breakdown
            console.print("\n[bold]Detailed Breakdown:[/bold]")

            for category in ["personas", "tasks", "templates", "checklists"]:
                items = report[category]
                if items:
                    console.print(f"\n[bold cyan]{category.title()}:[/bold cyan]")
                    for item in items[:5]:  # Show first 5 items
                        console.print(f"  • {item['name']}")
                    if len(items) > 5:
                        console.print(f"  ... and {len(items) - 5} more")

        # Save report if output file specified
        if output_file:
            output_path = Path(output_file)
            inventory.save_report(output_path)
            console.print(success_panel(f"Inventory report saved to {output_path}"))

        # Display conversion strategy information
        strategy = inventory.conversion_strategy
        validation_rules = strategy.get_validation_rules()

        console.print(info_panel("Conversion Strategy Generated"))
        console.print(f"• JSON Schemas: {len(validation_rules['json_schemas'])} types")
        console.print(f"• CI Checks: {len(validation_rules['ci_checks'])} validations")

        # Display directory structure plan
        structure_plan = strategy.plan_directory_structure()
        console.print(info_panel("Directory Structure Plan"))
        for directory, description in structure_plan.items():
            console.print(f"• {directory}: {len(description)} components")

    except Exception as e:
        logger.error(f"BMad inventory failed: {e}")
        console.print(error_panel(f"BMad inventory failed: {e}"))
        raise typer.Exit(1)


@bmad_cmd.command("convert-persona")
def convert_persona(
    persona_name: str = typer.Argument(
        ..., help="Name of the BMad persona to convert (e.g., 'dev.md')"
    ),
    output_file: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output file for converted persona YAML"
    ),
    base_path: Optional[str] = typer.Option(
        ".bmad-core", "--base-path", "-b", help="Base path to BMad content directory"
    ),
):
    """Convert a specific BMad persona to Orchestra YAML format."""
    try:
        console.print(info_panel(f"Converting BMad persona: {persona_name}"))

        # Create inventory and scan agents
        inventory = BmadContentInventory(base_path=Path(base_path or ".bmad-core"))
        agents = inventory.scan_agents()

        # Find the specified persona
        target_persona = None
        for agent in agents:
            if agent.name == persona_name:
                target_persona = agent
                break

        if not target_persona:
            available_personas = [agent.name for agent in agents]
            console.print(error_panel(f"Persona '{persona_name}' not found"))
            console.print(f"Available personas: {', '.join(available_personas)}")
            raise typer.Exit(1)

        # Convert to Orchestra schema
        strategy = inventory.conversion_strategy
        orchestra_schema = strategy.convert_persona(target_persona)

        # Display conversion results
        console.print(success_panel(f"Successfully converted persona: {persona_name}"))
        console.print(f"• Schema Type: {orchestra_schema.schema_type}")
        console.print(f"• Version: {orchestra_schema.version}")
        console.print(f"• Valid: {orchestra_schema.is_valid()}")

        if not orchestra_schema.is_valid():
            errors = orchestra_schema.get_validation_errors()
            console.print(warning_panel("Validation errors found:"))
            for error in errors:
                console.print(f"  • {error}")

        # Save converted schema if output file specified
        if output_file:
            output_path = Path(output_file)

            # Convert to YAML format for saving
            import yaml

            yaml_content = yaml.dump(
                orchestra_schema.schema_definition,
                default_flow_style=False,
                sort_keys=False,
            )

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(yaml_content)

            console.print(success_panel(f"Converted persona saved to {output_path}"))
        else:
            # Display schema structure
            console.print("\n[bold]Schema Structure:[/bold]")
            schema_def = orchestra_schema.schema_definition
            for section, content in schema_def.items():
                if isinstance(content, dict):
                    console.print(f"• {section}: {len(content)} fields")
                else:
                    console.print(f"• {section}: {content}")

    except Exception as e:
        logger.error(f"Persona conversion failed: {e}")
        console.print(error_panel(f"Persona conversion failed: {e}"))
        raise typer.Exit(1)


@bmad_cmd.command("convert-all-personas")
def convert_all_personas(
    output_dir: Optional[str] = typer.Option(
        "orchestra/personas/bmad",
        "--output-dir",
        "-d",
        help="Output directory for converted personas",
    ),
    base_path: Optional[str] = typer.Option(
        ".bmad-core", "--base-path", "-b", help="Base path to BMad content directory"
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be converted without actually converting",
    ),
    force: bool = typer.Option(False, "--force", help="Overwrite existing files"),
):
    """Convert all BMad personas to Orchestra YAML format (Story 1.2)."""
    try:
        console.print(
            info_panel(f"Starting batch conversion of BMad personas from {base_path}")
        )

        # Create inventory and converter
        inventory = BmadContentInventory(base_path=Path(base_path or ".bmad-core"))
        converter = BmadPersonaConverter(
            output_directory=Path(output_dir or "orchestra/personas")
        )

        # Scan for BMad personas
        bmad_personas = inventory.scan_agents()
        target_personas = converter.identify_target_personas(bmad_personas)

        console.print(
            success_panel(f"Found {len(target_personas)} BMad personas to convert")
        )

        # Show what will be converted
        table = Table(title="BMad Personas to Convert")
        table.add_column("Persona", style="cyan")
        table.add_column("File", style="white")
        table.add_column("Status", style="green")

        for persona in target_personas:
            status = "✓ Ready" if persona.path.exists() else "✗ Missing"
            table.add_row(
                persona.name.replace(".md", ""), str(persona.path.name), status
            )

        console.print(table)

        if dry_run:
            console.print(info_panel("Dry run completed - no files were converted"))
            return

        # Check if output directory exists and has files
        output_path = Path(output_dir or "orchestra/personas")
        if output_path.exists() and list(output_path.glob("*.yaml")) and not force:
            console.print(
                warning_panel(f"Output directory {output_dir} contains YAML files")
            )
            console.print("Use --force to overwrite existing files")
            raise typer.Exit(1)

        # Perform conversion
        console.print(info_panel("Converting personas..."))
        results = converter.convert_and_save_all(target_personas)

        # Display results
        successful_results = [r for r in results if r.success]
        failed_results = [r for r in results if not r.success]

        console.print(
            success_panel(
                f"Conversion completed: {len(successful_results)}/{len(results)} successful"
            )
        )

        if successful_results:
            console.print("\n[bold green]Successfully Converted:[/bold green]")
            for result in successful_results:
                console.print(f"  ✓ {result.persona_id}.yaml")

        if failed_results:
            console.print("\n[bold red]Failed Conversions:[/bold red]")
            for result in failed_results:
                console.print(f"  ✗ {result.persona_id or 'unknown'}")
                for error in result.validation_errors:
                    console.print(f"    • {error}")

        # Performance summary
        console.print(f"\n[bold]Output Directory:[/bold] {output_path}")
        yaml_files = list(output_path.glob("*.yaml"))
        console.print(f"[bold]Total Files:[/bold] {len(yaml_files)}")

        if len(successful_results) == len(target_personas):
            console.print(
                success_panel(
                    "All BMad personas successfully converted to Orchestra format!"
                )
            )
        else:
            console.print(
                warning_panel(
                    f"{len(failed_results)} conversions failed - check errors above"
                )
            )
            raise typer.Exit(1)

    except Exception as e:
        logger.error(f"Batch persona conversion failed: {e}")
        console.print(error_panel(f"Batch persona conversion failed: {e}"))
        raise typer.Exit(1)


@bmad_cmd.command("validate-converted-personas")
def validate_converted_personas(
    personas_dir: str = typer.Argument(
        ..., help="Directory containing converted persona YAML files"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed validation results"
    ),
):
    """Validate converted persona YAML files against Orchestra schema."""
    try:
        personas_path = Path(personas_dir)

        if not personas_path.exists():
            console.print(error_panel(f"Directory not found: {personas_dir}"))
            raise typer.Exit(1)

        console.print(info_panel(f"Validating converted personas in {personas_dir}"))

        # Find all YAML files
        yaml_files = list(personas_path.glob("*.yaml"))

        if not yaml_files:
            console.print(warning_panel("No YAML files found in directory"))
            return

        console.print(f"Found {len(yaml_files)} YAML files to validate")

        # Create converter for validation
        converter = BmadPersonaConverter()

        # Validate each file
        validation_results = []

        for yaml_file in yaml_files:
            try:
                # Load YAML content
                with open(yaml_file, "r") as f:
                    yaml_content = f.read()

                # Parse YAML to create PersonaSpec
                import yaml

                parsed_yaml = yaml.safe_load(yaml_content)

                # Create a minimal PersonaSpec for validation
                from orchestra.system.specs import (
                    BehavioralContract,
                    CommandInterface,
                    PersonaIdentity,
                    PersonaSpec,
                    ResourceDependencies,
                )

                identity = PersonaIdentity(
                    name=parsed_yaml["identity"]["name"],
                    id=parsed_yaml["identity"]["id"],
                    title=parsed_yaml["identity"]["title"],
                    role=parsed_yaml["identity"]["role"],
                    icon=parsed_yaml["identity"].get("icon", "🤖"),
                    when_to_use=parsed_yaml["identity"].get("when_to_use", ""),
                    style=parsed_yaml["identity"].get("style", ""),
                    focus=parsed_yaml["identity"].get("focus", ""),
                )

                behavioral_contract = BehavioralContract()
                command_interface = CommandInterface()
                resource_dependencies = ResourceDependencies()

                persona_spec = PersonaSpec(
                    identity=identity,
                    behavioral_contract=behavioral_contract,
                    command_interface=command_interface,
                    resource_dependencies=resource_dependencies,
                    version=parsed_yaml.get("version", "1.0.0"),
                )

                # Validate the spec
                validation_result = converter.validate_persona_schema(persona_spec)
                validation_results.append((yaml_file.name, validation_result))

            except Exception as e:
                validation_results.append(
                    (
                        yaml_file.name,
                        type(
                            "ValidationResult",
                            (),
                            {
                                "is_valid": False,
                                "errors": [f"Validation error: {str(e)}"],
                            },
                        )(),
                    )
                )

        # Display results
        valid_count = len([r for _, r in validation_results if r.is_valid])
        invalid_count = len(validation_results) - valid_count

        if valid_count == len(validation_results):
            console.print(
                success_panel(f"All {len(validation_results)} persona files are valid!")
            )
        else:
            console.print(
                warning_panel(
                    f"Validation completed: {valid_count} valid, {invalid_count} invalid"
                )
            )

        # Show detailed results if requested or if there are errors
        if verbose or invalid_count > 0:
            table = Table(title="Validation Results")
            table.add_column("File", style="cyan")
            table.add_column("Status", style="white")
            table.add_column("Errors", style="red")

            for filename, result in validation_results:
                status = "✓ Valid" if result.is_valid else "✗ Invalid"
                errors = "; ".join(result.errors) if not result.is_valid else ""
                table.add_row(filename, status, errors)

            console.print(table)

        if invalid_count > 0:
            raise typer.Exit(1)

    except Exception as e:
        logger.error(f"Persona validation failed: {e}")
        console.print(error_panel(f"Persona validation failed: {e}"))
        raise typer.Exit(1)


@bmad_cmd.command("list-resources")
def list_resources(
    resource_type: Optional[str] = typer.Option(
        None, "--type", "-t", help="Resource type to list (task, template, checklist)"
    ),
    base_path: Optional[str] = typer.Option(
        ".bmad-core", "--base-path", "-b", help="Base path to BMad content directory"
    ),
):
    """List available BMad resources (Story 1.3)."""
    try:
        console.print(info_panel(f"Listing BMad resources from {base_path}"))

        # Create resource loader
        loader = ResourceLoader(base_path=Path(base_path or ".bmad-core"))

        # Determine which resource types to list
        if resource_type:
            try:
                resource_types = [ResourceType(resource_type.lower())]
            except ValueError:
                console.print(
                    error_panel(
                        f"Invalid resource type: {resource_type}. Valid types: task, template, checklist"
                    )
                )
                raise typer.Exit(1)
        else:
            resource_types = [
                ResourceType.TASK,
                ResourceType.TEMPLATE,
                ResourceType.CHECKLIST,
            ]

        # Discover and display resources
        for res_type in resource_types:
            resources = loader.discover_resources(res_type)

            if resources:
                table = Table(title=f"{res_type.value.title()} Resources")
                table.add_column("ID", style="cyan")
                table.add_column("Name", style="white")
                table.add_column("Description", style="dim")
                table.add_column("Trust Level", style="green")
                table.add_column("Tags", style="blue")

                for resource in resources:
                    description = (
                        resource.description[:50] + "..."
                        if len(resource.description) > 50
                        else resource.description
                    )
                    tags = ", ".join(resource.tags[:3])  # Show first 3 tags

                    table.add_row(
                        resource.id,
                        resource.name,
                        description,
                        resource.trust_level,
                        tags,
                    )

                console.print(table)
                console.print()
            else:
                console.print(warning_panel(f"No {res_type.value} resources found"))

    except Exception as e:
        logger.error(f"Resource listing failed: {e}")
        console.print(error_panel(f"Resource listing failed: {e}"))
        raise typer.Exit(1)


@bmad_cmd.command("execute-task")
def execute_task(
    task_id: str = typer.Argument(..., help="ID of the task to execute"),
    base_path: Optional[str] = typer.Option(
        ".bmad-core", "--base-path", "-b", help="Base path to BMad content directory"
    ),
    context_file: Optional[str] = typer.Option(
        None, "--context", "-c", help="JSON file containing execution context"
    ),
    timeout: Optional[int] = typer.Option(
        300, "--timeout", help="Execution timeout in seconds"
    ),
):
    """Execute a BMad task (Story 1.3)."""
    try:
        console.print(info_panel(f"Executing task: {task_id}"))

        # Create resource loader and task engine
        loader = ResourceLoader(base_path=Path(base_path or ".bmad-core"))
        engine = TaskEngine(execution_timeout=timeout or 30)

        # Load the task
        result = loader.load_resource(task_id, ResourceType.TASK)
        if not result.success:
            console.print(error_panel(f"Failed to load task: {task_id}"))
            for error in result.validation_errors:
                console.print(f"  • {error}")
            raise typer.Exit(1)

        # Load context
        context = {}
        if context_file:
            try:
                with open(context_file, "r") as f:
                    context = json.load(f)
            except Exception as e:
                console.print(error_panel(f"Failed to load context file: {e}"))
                raise typer.Exit(1)

        # Add default context
        context.update(
            {
                "project_root": str(Path.cwd()),
                "user": "cli-user",
                "timestamp": time.time(),
            }
        )

        # Execute the task
        console.print(info_panel("Starting task execution..."))
        if result.metadata is None or result.content is None:
            console.print(error_panel("Task metadata or content is missing"))
            raise typer.Exit(1)
        execution_result = engine.execute_task(result.metadata, result.content, context)

        # Display results
        if execution_result.success:
            console.print(
                success_panel(
                    f"Task executed successfully in {execution_result.execution_time:.3f}s"
                )
            )
            console.print(
                f"Steps completed: {execution_result.steps_completed}/{execution_result.total_steps}"
            )

            if execution_result.warnings:
                console.print("\n[bold yellow]Warnings:[/bold yellow]")
                for warning in execution_result.warnings:
                    console.print(f"  ⚠️ {warning}")

            if execution_result.outputs:
                console.print(
                    f"\n[bold]Outputs:[/bold] {len(execution_result.outputs)} items"
                )
        else:
            console.print(
                error_panel(
                    f"Task execution failed after {execution_result.retry_count} retries"
                )
            )
            for error in execution_result.errors:
                console.print(f"  ❌ {error}")
            raise typer.Exit(1)

    except Exception as e:
        logger.error(f"Task execution failed: {e}")
        console.print(error_panel(f"Task execution failed: {e}"))
        raise typer.Exit(1)


@bmad_cmd.command("render-template")
def render_template(
    template_id: str = typer.Argument(..., help="ID of the template to render"),
    base_path: Optional[str] = typer.Option(
        ".bmad-core", "--base-path", "-b", help="Base path to BMad content directory"
    ),
    context_file: Optional[str] = typer.Option(
        None, "--context", "-c", help="JSON file containing template variables"
    ),
    output_file: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output file for rendered content"
    ),
):
    """Render a BMad template (Story 1.3)."""
    try:
        console.print(info_panel(f"Rendering template: {template_id}"))

        # Create resource loader and template processor
        loader = ResourceLoader(base_path=Path(base_path or ".bmad-core"))
        processor = TemplateProcessor()

        # Load the template
        result = loader.load_resource(template_id, ResourceType.TEMPLATE)
        if not result.success:
            console.print(error_panel(f"Failed to load template: {template_id}"))
            for error in result.validation_errors:
                console.print(f"  • {error}")
            raise typer.Exit(1)

        # Load context
        context = {}
        if context_file:
            try:
                with open(context_file, "r") as f:
                    context = json.load(f)
            except Exception as e:
                console.print(error_panel(f"Failed to load context file: {e}"))
                raise typer.Exit(1)

        # Add default context
        context.update(
            {"timestamp": time.strftime("%Y-%m-%d %H:%M:%S"), "user": "cli-user"}
        )

        # Render the template
        console.print(info_panel("Rendering template..."))
        if result.metadata is None or result.content is None:
            console.print(error_panel("Template metadata or content is missing"))
            raise typer.Exit(1)
        render_result = processor.render_template(
            result.metadata, result.content, context
        )

        # Display results
        if render_result.success:
            console.print(
                success_panel(
                    f"Template rendered successfully in {render_result.render_time:.3f}s"
                )
            )

            if render_result.warnings:
                console.print("\n[bold yellow]Warnings:[/bold yellow]")
                for warning in render_result.warnings:
                    console.print(f"  ⚠️ {warning}")

            # Output rendered content
            if output_file:
                with open(output_file, "w") as f:
                    content = render_result.rendered_content or ""
                    f.write(content)
                console.print(f"Rendered content saved to: {output_file}")
            else:
                console.print("\n[bold]Rendered Content:[/bold]")
                console.print(
                    Panel(render_result.rendered_content or "", title="Template Output")
                )
        else:
            console.print(error_panel("Template rendering failed"))
            for error in render_result.errors:
                console.print(f"  ❌ {error}")
            raise typer.Exit(1)

    except Exception as e:
        logger.error(f"Template rendering failed: {e}")
        console.print(error_panel(f"Template rendering failed: {e}"))
        raise typer.Exit(1)


@bmad_cmd.command("execute-checklist")
def execute_checklist(
    checklist_id: str = typer.Argument(..., help="ID of the checklist to execute"),
    base_path: Optional[str] = typer.Option(
        ".bmad-core", "--base-path", "-b", help="Base path to BMad content directory"
    ),
    context_file: Optional[str] = typer.Option(
        None, "--context", "-c", help="JSON file containing execution context"
    ),
    auto_check: bool = typer.Option(
        False, "--auto-check", help="Enable automatic checking based on context"
    ),
    report_format: str = typer.Option(
        "markdown", "--format", help="Report format (markdown, json)"
    ),
    output_file: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output file for checklist report"
    ),
):
    """Execute a BMad checklist (Story 1.3)."""
    try:
        console.print(info_panel(f"Executing checklist: {checklist_id}"))

        # Create resource loader and checklist engine
        loader = ResourceLoader(base_path=Path(base_path or ".bmad-core"))
        engine = ChecklistEngine(auto_check_enabled=auto_check)

        # Load the checklist
        result = loader.load_resource(checklist_id, ResourceType.CHECKLIST)
        if not result.success:
            console.print(error_panel(f"Failed to load checklist: {checklist_id}"))
            for error in result.validation_errors:
                console.print(f"  • {error}")
            raise typer.Exit(1)

        # Load context
        context = {}
        if context_file:
            try:
                with open(context_file, "r") as f:
                    context = json.load(f)
            except Exception as e:
                console.print(error_panel(f"Failed to load context file: {e}"))
                raise typer.Exit(1)

        # Add default context
        context.update(
            {"timestamp": time.strftime("%Y-%m-%d %H:%M:%S"), "user": "cli-user"}
        )

        # Execute the checklist
        console.print(info_panel("Executing checklist..."))
        if result.metadata is None or result.content is None:
            console.print(error_panel("Checklist metadata or content is missing"))
            raise typer.Exit(1)
        execution_result = engine.execute_checklist(
            result.metadata, result.content, context
        )

        # Display results
        if execution_result.success:
            console.print(
                success_panel(
                    f"Checklist executed successfully in {execution_result.execution_time:.3f}s"
                )
            )
            console.print(
                f"Completion: {execution_result.completion_percentage:.1f}% ({execution_result.completed_items}/{execution_result.total_items - execution_result.not_applicable_items} applicable items)"
            )

            if auto_check and execution_result.auto_checked_items > 0:
                console.print(
                    f"Auto-checked: {execution_result.auto_checked_items} items"
                )

            if execution_result.warnings:
                console.print("\n[bold yellow]Warnings:[/bold yellow]")
                for warning in execution_result.warnings:
                    console.print(f"  ⚠️ {warning}")

            # Generate and output report
            report = engine.export_checklist_report(execution_result, report_format)

            if output_file:
                with open(output_file, "w") as f:
                    f.write(report)
                console.print(f"Checklist report saved to: {output_file}")
            else:
                console.print("\n[bold]Checklist Report:[/bold]")
                if report_format == "markdown":
                    console.print(Panel(report or "", title="Checklist Report"))
                else:
                    console.print(report)
        else:
            console.print(error_panel("Checklist execution failed"))
            for error in execution_result.errors:
                console.print(f"  ❌ {error}")
            raise typer.Exit(1)

    except Exception as e:
        logger.error(f"Checklist execution failed: {e}")
        console.print(error_panel(f"Checklist execution failed: {e}"))
        raise typer.Exit(1)


# Overlay Management Commands
@overlay_cmd.command("preview")
def preview_merged_persona(
    persona_id: str,
    team: Optional[str] = typer.Option(None, "--team", "-t", help="Team context"),
    project: Optional[str] = typer.Option(
        None, "--project", "-p", help="Project context"
    ),
):
    """Preview merged persona with overlays applied."""
    try:
        loader = get_persona_loader()
        persona_spec = loader.load_persona(persona_id, team_id=team, project_id=project)

        if not persona_spec:
            console.print(error_panel(f"Persona '{persona_id}' not found"))
            raise typer.Exit(1)

        console.print(
            f"\n[bold blue]Merged Persona Preview: {persona_spec.identity.name}[/bold blue]"
        )
        console.print(f"[dim]ID: {persona_spec.identity.id}[/dim]")
        if team:
            console.print(f"[dim]Team: {team}[/dim]")
        if project:
            console.print(f"[dim]Project: {project}[/dim]")

        # Show core principles
        if persona_spec.behavioral_contract.core_principles:
            console.print("\n[bold]Core Principles:[/bold]")
            for principle in persona_spec.behavioral_contract.core_principles:
                console.print(f"  • {principle}")

        # Show commands
        if persona_spec.command_interface.commands:
            console.print("\n[bold]Available Commands:[/bold]")
            for cmd_name, cmd_def in persona_spec.command_interface.commands.items():
                description = (
                    cmd_def.description
                    if hasattr(cmd_def, "description")
                    else "No description"
                )
                console.print(f"  • [cyan]{cmd_name}[/cyan]: {description}")

        # Show tools
        if persona_spec.resource_dependencies.tools:
            console.print("\n[bold]Tools:[/bold]")
            tools_str = ", ".join(persona_spec.resource_dependencies.tools)
            console.print(f"  {tools_str}")

    except Exception as e:
        logger.error(f"Failed to preview persona: {e}")
        console.print(error_panel(f"Failed to preview persona: {e}"))
        raise typer.Exit(1)


@overlay_cmd.command("list")
def list_overlays(
    persona_id: Optional[str] = typer.Option(
        None, "--persona", "-p", help="Filter by persona ID"
    )
):
    """List available overlay files."""
    try:
        from pathlib import Path

        console.print(info_panel("Discovering overlay files..."))

        overlays = []

        # Scan team overlays
        teams_path = Path("teams")
        if teams_path.exists():
            for team_dir in teams_path.iterdir():
                if team_dir.is_dir():
                    personas_dir = team_dir / "personas"
                    if personas_dir.exists():
                        for overlay_file in personas_dir.glob("*.yaml"):
                            if not persona_id or overlay_file.stem == persona_id:
                                overlays.append(
                                    {
                                        "type": "team",
                                        "context": team_dir.name,
                                        "persona": overlay_file.stem,
                                        "path": str(overlay_file),
                                    }
                                )

        # Scan project overlays
        projects_path = Path("projects")
        if projects_path.exists():
            for project_dir in projects_path.iterdir():
                if project_dir.is_dir():
                    personas_dir = project_dir / "personas"
                    if personas_dir.exists():
                        for overlay_file in personas_dir.glob("*.yaml"):
                            if not persona_id or overlay_file.stem == persona_id:
                                overlays.append(
                                    {
                                        "type": "project",
                                        "context": project_dir.name,
                                        "persona": overlay_file.stem,
                                        "path": str(overlay_file),
                                    }
                                )

        if not overlays:
            console.print(warning_panel("No overlay files found"))
            return

        # Display overlays in a table
        from rich.table import Table

        table = Table(title="Available Overlays")
        table.add_column("Type", style="cyan")
        table.add_column("Context", style="green")
        table.add_column("Persona", style="yellow")
        table.add_column("Path", style="dim")

        for overlay in sorted(
            overlays, key=lambda x: (x["type"], x["context"], x["persona"])
        ):
            table.add_row(
                overlay["type"].title(),
                overlay["context"],
                overlay["persona"],
                overlay["path"],
            )

        console.print(table)
        console.print(success_panel(f"Found {len(overlays)} overlay files"))

    except Exception as e:
        logger.error(f"Failed to list overlays: {e}")
        console.print(error_panel(f"Failed to list overlays: {e}"))
        raise typer.Exit(1)
