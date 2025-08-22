"""Persona specification data structures for the Universal Agent System."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class PersonaIdentity:
    """Identity information for an agent persona."""

    name: str
    id: str
    title: str
    role: str
    icon: str = "🤖"
    when_to_use: str = ""
    style: str = ""
    focus: str = ""


@dataclass
class BehavioralContract:
    """Behavioral rules and principles for an agent persona."""

    core_principles: List[str] = field(default_factory=list)
    interaction_style: str = "conversational"
    halt_conditions: List[str] = field(default_factory=list)
    decision_framework: Optional[str] = None
    escalation_triggers: List[str] = field(default_factory=list)


@dataclass
class CommandDefinition:
    """Definition of a single command available to a persona."""

    description: str
    execution_pattern: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    requires_confirmation: bool = False
    timeout_seconds: int = 60


@dataclass
class CommandInterface:
    """Command interface configuration for a persona."""

    execution_model: str = "sequential"  # sequential, parallel, adaptive
    commands: Dict[str, CommandDefinition] = field(default_factory=dict)
    default_command: Optional[str] = None
    command_aliases: Dict[str, str] = field(default_factory=dict)


@dataclass
class ResourceDependencies:
    """Resource dependencies required by a persona."""

    knowledge_sources: List[str] = field(default_factory=list)
    tasks: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    templates: List[str] = field(default_factory=list)
    required_services: List[str] = field(default_factory=list)


@dataclass
class KnowledgeContext:
    """Knowledge context configuration for a persona."""

    domains: List[str] = field(default_factory=list)
    expertise_areas: List[str] = field(default_factory=list)
    learning_sources: List[str] = field(default_factory=list)
    context_window_size: int = 4096
    memory_retention_policy: str = "session"  # session, persistent, adaptive


@dataclass
class PersonaSpec:
    """
    Complete specification for an agent persona.

    This dataclass represents the full configuration loaded from YAML files
    that defines how an agent persona behaves, what tools it has access to,
    and how it interacts with users and other agents.
    """

    identity: PersonaIdentity
    behavioral_contract: BehavioralContract = field(default_factory=BehavioralContract)
    command_interface: CommandInterface = field(default_factory=CommandInterface)
    resource_dependencies: ResourceDependencies = field(
        default_factory=ResourceDependencies
    )
    knowledge_context: Optional[KnowledgeContext] = None

    # Metadata
    version: str = "1.0.0"
    created_by: str = "system"
    last_modified: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    # Runtime configuration
    enabled: bool = True
    experimental: bool = False
    deprecated: bool = False

    @property
    def full_id(self) -> str:
        """Get the full persona identifier."""
        return f"{self.identity.id}@{self.version}"

    @property
    def display_name(self) -> str:
        """Get the display name with icon."""
        return f"{self.identity.icon} {self.identity.name}"

    def get_command(self, command_name: str) -> Optional[CommandDefinition]:
        """
        Get a command definition by name or alias.

        Args:
            command_name: Name or alias of the command

        Returns:
            CommandDefinition if found, None otherwise
        """
        # Check direct command name
        if command_name in self.command_interface.commands:
            return self.command_interface.commands[command_name]

        # Check aliases
        if command_name in self.command_interface.command_aliases:
            actual_name = self.command_interface.command_aliases[command_name]
            return self.command_interface.commands.get(actual_name)

        return None

    def validate(self) -> List[str]:
        """
        Validate the persona specification.

        Returns:
            List of validation errors, empty if valid
        """
        errors = []

        # Validate identity
        if not self.identity.name:
            errors.append("Missing persona name")
        if not self.identity.id:
            errors.append("Missing persona ID")
        if not self.identity.role:
            errors.append("Missing persona role")

        # Validate behavioral contract
        if not self.behavioral_contract.core_principles:
            errors.append("No core principles defined")

        # Validate commands if any are defined
        for cmd_name, cmd_def in self.command_interface.commands.items():
            if not cmd_def.description:
                errors.append(f"Command '{cmd_name}' missing description")
            if not cmd_def.execution_pattern:
                errors.append(f"Command '{cmd_name}' missing execution pattern")

        # Validate resource dependencies
        for tool in self.resource_dependencies.tools:
            # In production, would validate tool exists in registry
            pass

        return errors

    def to_dict(self) -> Dict[str, Any]:
        """Convert persona spec to dictionary for serialization."""
        return {
            "identity": {
                "name": self.identity.name,
                "id": self.identity.id,
                "title": self.identity.title,
                "role": self.identity.role,
                "icon": self.identity.icon,
                "when_to_use": self.identity.when_to_use,
                "style": self.identity.style,
                "focus": self.identity.focus,
            },
            "behavioral_contract": {
                "core_principles": self.behavioral_contract.core_principles,
                "interaction_style": self.behavioral_contract.interaction_style,
                "halt_conditions": self.behavioral_contract.halt_conditions,
                "decision_framework": self.behavioral_contract.decision_framework,
                "escalation_triggers": self.behavioral_contract.escalation_triggers,
            },
            "command_interface": {
                "execution_model": self.command_interface.execution_model,
                "commands": {
                    name: {
                        "description": cmd.description,
                        "execution_pattern": cmd.execution_pattern,
                        "parameters": cmd.parameters,
                        "requires_confirmation": cmd.requires_confirmation,
                        "timeout_seconds": cmd.timeout_seconds,
                    }
                    for name, cmd in self.command_interface.commands.items()
                },
                "default_command": self.command_interface.default_command,
                "command_aliases": self.command_interface.command_aliases,
            },
            "resource_dependencies": {
                "knowledge_sources": self.resource_dependencies.knowledge_sources,
                "tasks": self.resource_dependencies.tasks,
                "tools": self.resource_dependencies.tools,
                "templates": self.resource_dependencies.templates,
                "required_services": self.resource_dependencies.required_services,
            },
            "knowledge_context": (
                {
                    "domains": self.knowledge_context.domains,
                    "expertise_areas": self.knowledge_context.expertise_areas,
                    "learning_sources": self.knowledge_context.learning_sources,
                    "context_window_size": self.knowledge_context.context_window_size,
                    "memory_retention_policy": self.knowledge_context.memory_retention_policy,
                }
                if self.knowledge_context
                else None
            ),
            "version": self.version,
            "created_by": self.created_by,
            "last_modified": self.last_modified,
            "tags": self.tags,
            "enabled": self.enabled,
            "experimental": self.experimental,
            "deprecated": self.deprecated,
        }
