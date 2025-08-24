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
from orchestra.system.bmad_persona_converter import BmadPersonaConverter
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


@bmad_cmd.command("convert-all-personas")
def convert_all_personas(
    output_dir: Optional[str] = typer.Option(
        "orchestra/personas/bmad", "--output-dir", "-d", help="Output directory for converted personas"
    ),
    base_path: Optional[str] = typer.Option(
        ".bmad-core", "--base-path", "-b", help="Base path to BMad content directory"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be converted without actually converting"
    ),
    force: bool = typer.Option(
        False, "--force", help="Overwrite existing files"
    )
):
    """Convert all BMad personas to Orchestra YAML format (Story 1.2)."""
    try:
        console.print(info_panel(f"Starting batch conversion of BMad personas from {base_path}"))
        
        # Create inventory and converter
        inventory = BmadContentInventory(base_path=Path(base_path))
        converter = BmadPersonaConverter(output_directory=Path(output_dir))
        
        # Scan for BMad personas
        bmad_personas = inventory.scan_agents()
        target_personas = converter.identify_target_personas(bmad_personas)
        
        console.print(success_panel(f"Found {len(target_personas)} BMad personas to convert"))
        
        # Show what will be converted
        table = Table(title="BMad Personas to Convert")
        table.add_column("Persona", style="cyan")
        table.add_column("File", style="white")
        table.add_column("Status", style="green")
        
        for persona in target_personas:
            status = "✓ Ready" if persona.path.exists() else "✗ Missing"
            table.add_row(
                persona.name.replace('.md', ''),
                str(persona.path.name),
                status
            )
        
        console.print(table)
        
        if dry_run:
            console.print(info_panel("Dry run completed - no files were converted"))
            return
        
        # Check if output directory exists and has files
        output_path = Path(output_dir)
        if output_path.exists() and list(output_path.glob("*.yaml")) and not force:
            console.print(warning_panel(f"Output directory {output_dir} contains YAML files"))
            console.print("Use --force to overwrite existing files")
            raise typer.Exit(1)
        
        # Perform conversion
        console.print(info_panel("Converting personas..."))
        results = converter.convert_and_save_all(target_personas)
        
        # Display results
        successful_results = [r for r in results if r.success]
        failed_results = [r for r in results if not r.success]
        
        console.print(success_panel(f"Conversion completed: {len(successful_results)}/{len(results)} successful"))
        
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
            console.print(success_panel("All BMad personas successfully converted to Orchestra format!"))
        else:
            console.print(warning_panel(f"{len(failed_results)} conversions failed - check errors above"))
            raise typer.Exit(1)
        
    except Exception as e:
        logger.error(f"Batch persona conversion failed: {e}")
        console.print(error_panel(f"Batch persona conversion failed: {e}"))
        raise typer.Exit(1)


@bmad_cmd.command("validate-converted-personas")
def validate_converted_personas(
    personas_dir: str = typer.Argument(..., help="Directory containing converted persona YAML files"),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed validation results"
    )
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
                with open(yaml_file, 'r') as f:
                    yaml_content = f.read()
                
                # Parse YAML to create PersonaSpec
                import yaml
                parsed_yaml = yaml.safe_load(yaml_content)
                
                # Create a minimal PersonaSpec for validation
                from orchestra.system.specs import PersonaIdentity, PersonaSpec, BehavioralContract, CommandInterface, ResourceDependencies
                
                identity = PersonaIdentity(
                    name=parsed_yaml['identity']['name'],
                    id=parsed_yaml['identity']['id'],
                    title=parsed_yaml['identity']['title'],
                    role=parsed_yaml['identity']['role'],
                    icon=parsed_yaml['identity'].get('icon', '🤖'),
                    when_to_use=parsed_yaml['identity'].get('when_to_use', ''),
                    style=parsed_yaml['identity'].get('style', ''),
                    focus=parsed_yaml['identity'].get('focus', '')
                )
                
                behavioral_contract = BehavioralContract()
                command_interface = CommandInterface()
                resource_dependencies = ResourceDependencies()
                
                persona_spec = PersonaSpec(
                    identity=identity,
                    behavioral_contract=behavioral_contract,
                    command_interface=command_interface,
                    resource_dependencies=resource_dependencies,
                    version=parsed_yaml.get('version', '1.0.0')
                )
                
                # Validate the spec
                validation_result = converter.validate_persona_schema(persona_spec)
                validation_results.append((yaml_file.name, validation_result))
                
            except Exception as e:
                validation_results.append((yaml_file.name, type('ValidationResult', (), {
                    'is_valid': False,
                    'errors': [f"Validation error: {str(e)}"]
                })()))
        
        # Display results
        valid_count = len([r for _, r in validation_results if r.is_valid])
        invalid_count = len(validation_results) - valid_count
        
        if valid_count == len(validation_results):
            console.print(success_panel(f"All {len(validation_results)} persona files are valid!"))
        else:
            console.print(warning_panel(f"Validation completed: {valid_count} valid, {invalid_count} invalid"))
        
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
