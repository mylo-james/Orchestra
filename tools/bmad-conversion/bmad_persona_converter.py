"""BMad persona converter for Orchestra integration (Story 1.2)."""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from bmad_inventory import BmadContentItem, BmadContentType
from orchestra.system.specs import (
    BehavioralContract,
    CommandDefinition,
    CommandInterface,
    KnowledgeContext,
    PersonaIdentity,
    PersonaSpec,
    ResourceDependencies,
)
from orchestra.utils.logging import get_logger

logger = get_logger(__name__)


class PersonaValidationError(Exception):
    """Exception raised when persona validation fails."""

    def __init__(
        self,
        message: str,
        persona_id: Optional[str] = None,
        field: Optional[str] = None,
    ):
        """Initialize validation error."""
        super().__init__(message)
        self.persona_id = persona_id
        self.field = field


@dataclass
class PersonaConversionResult:
    """Result of converting a BMad persona to Orchestra format."""

    success: bool
    persona_spec: Optional[PersonaSpec]
    yaml_content: Optional[str]
    validation_errors: List[str]

    @property
    def persona_id(self) -> Optional[str]:
        """Get persona ID if conversion was successful."""
        return self.persona_spec.identity.id if self.persona_spec else None


@dataclass
class ValidationResult:
    """Result of persona schema validation."""

    is_valid: bool
    errors: List[str]


class BmadPersonaConverter:
    """Converter for BMad personas to Orchestra YAML format."""

    def __init__(
        self,
        output_directory: Path = Path("orchestra/personas"),
        validation_enabled: bool = True,
    ):
        """
        Initialize the BMad persona converter.

        Args:
            output_directory: Directory to save converted personas
            validation_enabled: Whether to enable schema validation
        """
        self.output_directory = output_directory
        self.validation_enabled = validation_enabled
        self._bmad_content_cache: Dict[str, str] = {}

        logger.info(
            f"Initialized BMad persona converter with output directory: {output_directory}"
        )

    def identify_target_personas(
        self, bmad_personas: List[BmadContentItem]
    ) -> List[BmadContentItem]:
        """
        Identify target BMad personas for conversion.

        Args:
            bmad_personas: List of BMad persona items

        Returns:
            List of target personas to convert
        """
        # Filter to only persona content types
        persona_items = [
            item
            for item in bmad_personas
            if item.content_type == BmadContentType.PERSONA
        ]

        # Sort by name for consistent ordering
        persona_items.sort(key=lambda x: x.name)

        logger.info(f"Identified {len(persona_items)} target personas for conversion")
        return persona_items

    def convert_persona(self, bmad_persona: BmadContentItem) -> PersonaConversionResult:
        """
        Convert a single BMad persona to Orchestra YAML format.

        Args:
            bmad_persona: BMad persona item to convert

        Returns:
            PersonaConversionResult with conversion details
        """
        try:
            logger.info(f"Converting BMad persona: {bmad_persona.name}")

            # Extract detailed metadata from BMad content
            detailed_metadata = self._extract_detailed_metadata(bmad_persona)

            # Create Orchestra persona spec
            persona_spec = self._create_persona_spec(bmad_persona, detailed_metadata)

            # Validate the persona spec if validation is enabled
            if self.validation_enabled:
                validation_result = self.validate_persona_schema(persona_spec)
                if not validation_result.is_valid:
                    return PersonaConversionResult(
                        success=False,
                        persona_spec=None,
                        yaml_content=None,
                        validation_errors=validation_result.errors,
                    )

            # Generate YAML content
            yaml_content = self._generate_yaml_content(persona_spec)

            logger.info(f"Successfully converted persona: {bmad_persona.name}")

            return PersonaConversionResult(
                success=True,
                persona_spec=persona_spec,
                yaml_content=yaml_content,
                validation_errors=[],
            )

        except Exception as e:
            logger.error(f"Failed to convert persona {bmad_persona.name}: {e}")
            return PersonaConversionResult(
                success=False,
                persona_spec=None,
                yaml_content=None,
                validation_errors=[str(e)],
            )

    def convert_all_personas(
        self, target_personas: List[BmadContentItem]
    ) -> List[PersonaConversionResult]:
        """
        Convert all target personas to Orchestra format.

        Args:
            target_personas: List of BMad personas to convert

        Returns:
            List of conversion results
        """
        logger.info(f"Starting batch conversion of {len(target_personas)} personas")

        results = []
        for persona in target_personas:
            result = self.convert_persona(persona)
            results.append(result)

            if result.success:
                logger.debug(f"✓ Converted: {persona.name}")
            else:
                logger.warning(f"✗ Failed: {persona.name} - {result.validation_errors}")

        successful_count = len([r for r in results if r.success])
        logger.info(
            f"Batch conversion completed: {successful_count}/{len(target_personas)} successful"
        )

        return results

    def convert_and_save_all(
        self, target_personas: List[BmadContentItem]
    ) -> List[PersonaConversionResult]:
        """
        Convert all personas and save to output directory.

        Args:
            target_personas: List of BMad personas to convert

        Returns:
            List of conversion results
        """
        # Ensure output directory exists
        self.output_directory.mkdir(parents=True, exist_ok=True)

        # Convert all personas
        results = self.convert_all_personas(target_personas)

        # Save successful conversions
        for result in results:
            if result.success and result.yaml_content:
                output_file = self.output_directory / f"{result.persona_id}.yaml"
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(result.yaml_content)
                logger.info(f"Saved converted persona to: {output_file}")

        return results

    def validate_persona_schema(self, persona_spec: PersonaSpec) -> ValidationResult:
        """
        Validate a persona spec against Orchestra schema requirements.

        Args:
            persona_spec: PersonaSpec to validate

        Returns:
            ValidationResult with validation status and errors
        """
        errors = []

        try:
            # Validate identity section
            identity = persona_spec.identity
            if not identity.name or not identity.name.strip():
                errors.append("Identity name is required and cannot be empty")
            if not identity.id or not identity.id.strip():
                errors.append("Identity id is required and cannot be empty")
            if not identity.title or not identity.title.strip():
                errors.append("Identity title is required and cannot be empty")
            if not identity.role or not identity.role.strip():
                errors.append("Identity role is required and cannot be empty")

            # Validate behavioral contract exists
            if not persona_spec.behavioral_contract:
                errors.append("Behavioral contract is required")

            # Validate command interface exists
            if not persona_spec.command_interface:
                errors.append("Command interface is required")

            # Validate resource dependencies exist
            if not persona_spec.resource_dependencies:
                errors.append("Resource dependencies are required")

            # Validate version format
            if not persona_spec.version or not re.match(
                r"^\d+\.\d+(\.\d+)?$", persona_spec.version
            ):
                errors.append("Version must be in format X.Y or X.Y.Z")

        except Exception as e:
            errors.append(f"Validation error: {str(e)}")

        return ValidationResult(is_valid=len(errors) == 0, errors=errors)

    def _extract_detailed_metadata(
        self, bmad_persona: BmadContentItem
    ) -> Dict[str, any]:
        """Extract detailed metadata from BMad persona content."""
        metadata = bmad_persona.metadata.copy()

        try:
            # Read the actual BMad file content for more detailed extraction
            if bmad_persona.path.exists():
                content = bmad_persona.path.read_text(encoding="utf-8")
                self._bmad_content_cache[bmad_persona.name] = content

                # Extract additional metadata from content
                additional_metadata = self._parse_bmad_content(content)
                metadata.update(additional_metadata)
            else:
                # File doesn't exist - this should be treated as an error for conversion
                raise FileNotFoundError(
                    f"BMad persona file not found: {bmad_persona.path}"
                )

        except Exception as e:
            logger.warning(f"Could not read BMad content for {bmad_persona.name}: {e}")
            # Re-raise the exception to be caught by convert_persona
            raise

        return metadata

    def _parse_bmad_content(self, content: str) -> Dict[str, any]:
        """Parse BMad content to extract structured metadata."""
        metadata = {}

        # Extract YAML frontmatter if present
        yaml_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        if yaml_match:
            try:
                yaml_metadata = yaml.safe_load(yaml_match.group(1))
                if yaml_metadata:
                    metadata.update(yaml_metadata)
            except yaml.YAMLError:
                pass

        # Extract YAML blocks from markdown code fences (BMad format)
        yaml_block_match = re.search(r"```yaml\n(.*?)\n```", content, re.DOTALL)
        if yaml_block_match:
            try:
                yaml_content = yaml_block_match.group(1)
                yaml_metadata = yaml.safe_load(yaml_content)
                if yaml_metadata:
                    metadata.update(yaml_metadata)
            except yaml.YAMLError as e:
                logger.warning(f"Failed to parse YAML block: {e}")

        # Extract persona information from content structure
        lines = content.split("\n")

        for line in lines:
            line = line.strip()

            # Detect sections
            if line.startswith("# ") or line.startswith("## "):
                line.lstrip("# ").lower()  # Parse section but don't store
                continue

            # Extract key-value pairs
            if ":" in line and not line.startswith("http"):
                key, value = line.split(":", 1)
                key = key.strip().lower().replace(" ", "_")
                value = value.strip()

                if value and key not in metadata:
                    metadata[key] = value

        # Extract commands from content
        commands = re.findall(r"(?:command|cmd):\s*(.+)", content, re.IGNORECASE)
        if commands:
            metadata["commands"] = [cmd.strip() for cmd in commands]

        # Extract tools/dependencies
        tools = re.findall(
            r"(?:tool|dependency|depends):\s*(.+)", content, re.IGNORECASE
        )
        if tools:
            metadata["tools"] = [tool.strip() for tool in tools]

        return metadata

    def _create_persona_spec(
        self, bmad_persona: BmadContentItem, metadata: Dict[str, any]
    ) -> PersonaSpec:
        """Create Orchestra PersonaSpec from BMad persona data."""
        persona_id = bmad_persona.name.replace(".md", "").lower()

        # Extract agent and persona sections from BMad YAML
        agent_data = metadata.get("agent", {})
        persona_data = metadata.get("persona", {})

        # Create identity from BMad agent section
        identity = PersonaIdentity(
            name=agent_data.get("name", persona_id.replace("-", " ").title()),
            id=agent_data.get("id", persona_id),
            title=agent_data.get("title", f"{persona_id.title()} Specialist"),
            role=persona_data.get(
                "role", f"Expert {persona_id.replace('-', ' ').title()}"
            ),
            icon=agent_data.get("icon", "🤖"),
            when_to_use=agent_data.get(
                "whenToUse", f"Use for {persona_id.replace('-', ' ')} related tasks"
            ),
            style=persona_data.get("style", "Professional and helpful"),
            focus=persona_data.get("focus", "Task execution and problem solving"),
        )

        # Create behavioral contract from BMad persona section
        # Core principles can be at root level or in persona section
        core_principles = metadata.get(
            "core_principles", persona_data.get("core_principles", [])
        )
        behavioral_contract = BehavioralContract(
            core_principles=core_principles,
            interaction_style=persona_data.get("interaction_style", "professional"),
            halt_conditions=persona_data.get("halt_conditions", []),
            decision_framework=persona_data.get("decision_framework", "analytical"),
            escalation_triggers=persona_data.get("escalation_triggers", []),
        )

        # Create command interface from BMad commands
        commands = {}
        bmad_commands = metadata.get("commands", [])

        if bmad_commands:
            for cmd_entry in bmad_commands:
                if isinstance(cmd_entry, dict):
                    # BMad format: {command_name: description}
                    for cmd_name, cmd_desc in cmd_entry.items():
                        # Clean up command name
                        clean_cmd_name = (
                            cmd_name.strip()
                            .replace(" ", "-")
                            .replace("{", "")
                            .replace("}", "")
                        )

                        # Extract parameters from command name if present
                        params = {}
                        if "{" in cmd_name and "}" in cmd_name:
                            param_matches = re.findall(r"\{(\w+)\}", cmd_name)
                            for param in param_matches:
                                params[param] = {
                                    "type": "string",
                                    "description": f"{param.replace('_', ' ').title()} parameter",
                                    "required": True,
                                }

                        commands[clean_cmd_name] = CommandDefinition(
                            description=cmd_desc,
                            execution_pattern="analyze → execute → validate",
                            parameters=params,
                            requires_confirmation=False,
                            timeout_seconds=120,
                        )
                elif isinstance(cmd_entry, str):
                    # Parse command string format: "command-name: description"
                    if ":" in cmd_entry:
                        cmd_name, cmd_desc = cmd_entry.split(":", 1)
                        cmd_name = cmd_name.strip().replace(" ", "-")
                        cmd_desc = cmd_desc.strip()
                    else:
                        cmd_name = cmd_entry.strip().replace(" ", "-")
                        cmd_desc = f"Execute {cmd_entry} command"

                    # Extract parameters from command description if present
                    params = {}
                    if "{" in cmd_desc and "}" in cmd_desc:
                        param_matches = re.findall(r"\{(\w+)\}", cmd_desc)
                        for param in param_matches:
                            params[param] = {
                                "type": "string",
                                "description": f"{param.replace('_', ' ').title()} parameter",
                                "required": True,
                            }

                    commands[cmd_name] = CommandDefinition(
                        description=cmd_desc,
                        execution_pattern="analyze → execute → validate",
                        parameters=params,
                        requires_confirmation=False,
                        timeout_seconds=120,
                    )

        # Add default help command if no commands defined
        if not commands:
            commands["help"] = CommandDefinition(
                description="Show available commands and usage information",
                execution_pattern="display → explain",
                parameters={},
                requires_confirmation=False,
                timeout_seconds=30,
            )

        command_interface = CommandInterface(
            execution_model="sequential",
            commands=commands,
            default_command="help",
            command_aliases={},
        )

        # Create resource dependencies from BMad dependencies
        bmad_dependencies = metadata.get("dependencies", {})
        resource_dependencies = ResourceDependencies(
            knowledge_sources=bmad_dependencies.get("data", []),
            tasks=bmad_dependencies.get("tasks", []),
            tools=bmad_dependencies.get("tools", []),
            templates=bmad_dependencies.get("templates", []),
            required_services=metadata.get("required_services", []),
        )

        # Create knowledge context if domain information is available
        knowledge_context = None
        if "domains" in metadata or "expertise_areas" in metadata:
            knowledge_context = KnowledgeContext(
                domains=metadata.get("domains", []),
                expertise_areas=metadata.get("expertise_areas", []),
                learning_sources=metadata.get("learning_sources", []),
                context_window_size=metadata.get("context_window_size", 4096),
                memory_retention_policy=metadata.get(
                    "memory_retention_policy", "session"
                ),
            )

        # Create persona spec
        persona_spec = PersonaSpec(
            identity=identity,
            behavioral_contract=behavioral_contract,
            command_interface=command_interface,
            resource_dependencies=resource_dependencies,
            knowledge_context=knowledge_context,
            version=metadata.get("version", "1.0.0"),
            created_by=metadata.get("created_by", "bmad-converter"),
            tags=metadata.get("tags", [persona_id]),
            enabled=True,
            experimental=False,
            deprecated=False,
        )

        return persona_spec

    def _generate_yaml_content(self, persona_spec: PersonaSpec) -> str:
        """Generate YAML content from PersonaSpec."""
        # Convert PersonaSpec to dictionary
        spec_dict = self._persona_spec_to_dict(persona_spec)

        # Generate YAML with proper formatting
        yaml_content = yaml.dump(
            spec_dict,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
            width=100,
            indent=2,
        )

        return yaml_content

    def _persona_spec_to_dict(self, spec: PersonaSpec) -> Dict[str, any]:
        """Convert PersonaSpec to dictionary for YAML serialization."""
        result = {
            "identity": {
                "name": spec.identity.name,
                "id": spec.identity.id,
                "title": spec.identity.title,
                "role": spec.identity.role,
                "icon": spec.identity.icon,
                "when_to_use": spec.identity.when_to_use,
                "style": spec.identity.style,
                "focus": spec.identity.focus,
            },
            "behavioral_contract": {
                "core_principles": spec.behavioral_contract.core_principles,
                "interaction_style": spec.behavioral_contract.interaction_style,
                "halt_conditions": spec.behavioral_contract.halt_conditions,
                "decision_framework": spec.behavioral_contract.decision_framework,
                "escalation_triggers": spec.behavioral_contract.escalation_triggers,
            },
            "command_interface": {
                "execution_model": spec.command_interface.execution_model,
                "commands": {},
                "default_command": spec.command_interface.default_command,
                "command_aliases": spec.command_interface.command_aliases,
            },
            "resource_dependencies": {
                "knowledge_sources": spec.resource_dependencies.knowledge_sources,
                "tasks": spec.resource_dependencies.tasks,
                "tools": spec.resource_dependencies.tools,
                "templates": spec.resource_dependencies.templates,
                "required_services": spec.resource_dependencies.required_services,
            },
            "version": spec.version,
            "created_by": spec.created_by,
            "tags": spec.tags,
            "enabled": spec.enabled,
            "experimental": spec.experimental,
            "deprecated": spec.deprecated,
        }

        # Convert commands
        for cmd_name, cmd_def in spec.command_interface.commands.items():
            result["command_interface"]["commands"][cmd_name] = {
                "description": cmd_def.description,
                "execution_pattern": cmd_def.execution_pattern,
                "parameters": cmd_def.parameters,
                "requires_confirmation": cmd_def.requires_confirmation,
                "timeout_seconds": cmd_def.timeout_seconds,
            }

        # Add knowledge context if present
        if spec.knowledge_context:
            result["knowledge_context"] = {
                "domains": spec.knowledge_context.domains,
                "expertise_areas": spec.knowledge_context.expertise_areas,
                "learning_sources": spec.knowledge_context.learning_sources,
                "context_window_size": spec.knowledge_context.context_window_size,
                "memory_retention_policy": spec.knowledge_context.memory_retention_policy,
            }

        return result
