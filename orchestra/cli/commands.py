"""Orchestra CLI Commands."""

import asyncio
import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from orchestra.cli.output import (
    error_panel,
    info_panel,
    success_panel,
    warning_panel,
)
from orchestra.system.bmad_inventory import BmadContentInventory
from orchestra.system.factory import get_registry
from orchestra.utils.logging import get_logger

logger = get_logger(__name__)
console = Console()

# Create command groups
agent_cmd = typer.Typer(help="Agent management commands")
workflow_cmd = typer.Typer(help="Workflow orchestration commands")
config_cmd = typer.Typer(help="Configuration management commands")
dev_cmd = typer.Typer(help="Development tools and utilities")
bmad_cmd = typer.Typer(help="BMad content management commands")


@agent_cmd.command("list")
def list_agents():
    """List all available agents."""
    try:
        registry = get_registry()
        agents = registry.list_agents()
        
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
        agent = registry.get_agent(name)
        
        if not agent:
            console.print(error_panel(f"Agent '{name}' not found"))
            raise typer.Exit(1)
        
        console.print(info_panel(f"Agent '{name}' is active"))
        
    except Exception as e:
        logger.error(f"Failed to get agent status: {e}")
        console.print(error_panel(f"Failed to get agent status: {e}"))
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
    )
):
    """Generate BMad content inventory and conversion strategy report."""
    try:
        console.print(info_panel(f"Starting BMad content inventory scan from {base_path}"))
        
        # Create inventory instance
        inventory = BmadContentInventory(base_path=Path(base_path))
        
        # Perform full scan
        inventory.scan_all()
        
        # Generate report
        report = inventory.generate_report()
        
        # Display summary
        summary = report["summary"]
        console.print(success_panel(f"Inventory scan completed: {summary['total_items']} items found"))
        
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
    persona_name: str = typer.Argument(..., help="Name of the BMad persona to convert (e.g., 'dev.md')"),
    output_file: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output file for converted persona YAML"
    ),
    base_path: Optional[str] = typer.Option(
        ".bmad-core", "--base-path", "-b", help="Base path to BMad content directory"
    )
):
    """Convert a specific BMad persona to Orchestra YAML format."""
    try:
        console.print(info_panel(f"Converting BMad persona: {persona_name}"))
        
        # Create inventory and scan agents
        inventory = BmadContentInventory(base_path=Path(base_path))
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
            yaml_content = yaml.dump(orchestra_schema.schema_definition, default_flow_style=False, sort_keys=False)
            
            with open(output_path, 'w', encoding='utf-8') as f:
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
