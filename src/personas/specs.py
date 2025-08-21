from __future__ import annotations

from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field, RootModel, ValidationError, model_validator


class IdentitySpec(BaseModel):
    name: str
    id: str
    title: str
    role: str
    icon: Optional[str] = None
    when_to_use: Optional[str] = Field(
        None, alias="when_to_use", description="When to use this persona"
    )
    style: Optional[str] = None
    focus: Optional[str] = None


class BehavioralContractSpec(BaseModel):
    core_principles: List[str] = Field(default_factory=list)
    interaction_style: Optional[Literal["numbered_lists", "freeform", "structured"]] = None
    halt_conditions: List[str] = Field(default_factory=list)
    activation_steps: List[str] = Field(default_factory=list)
    constraints: Optional[Dict[str, List[str]]] = None


class CommandSpec(BaseModel):
    description: str
    execution_pattern: Optional[str] = None
    blocking_conditions: Optional[List[str]] = None
    dependencies: Optional[List[str]] = None


class CommandInterfaceSpec(BaseModel):
    execution_model: Optional[Literal["sequential", "orchestration", "conversational"]] = None
    commands: Dict[str, CommandSpec] = Field(default_factory=dict)


class ResourceDependenciesSpec(BaseModel):
    knowledge_sources: List[str] = Field(default_factory=list)
    tasks: List[str] = Field(default_factory=list)
    checklists: List[str] = Field(default_factory=list)
    templates: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)


class KnowledgeContextSpec(BaseModel):
    always_load: List[str] = Field(default_factory=list)
    load_on_demand: List[str] = Field(default_factory=list)
    boundaries: List[str] = Field(default_factory=list)
    context_window_priority: List[str] = Field(default_factory=list)


class PersonaSpec(BaseModel):
    identity: IdentitySpec
    behavioral_contract: Optional[BehavioralContractSpec] = None
    command_interface: Optional[CommandInterfaceSpec] = None
    resource_dependencies: Optional[ResourceDependenciesSpec] = None
    knowledge_context: Optional[KnowledgeContextSpec] = None

    @model_validator(mode="after")
    def validate_required_fields(self) -> "PersonaSpec":
        # basic sanity checks
        if not self.identity.id:
            raise ValueError("identity.id is required and must be non-empty")
        if self.command_interface and self.command_interface.commands:
            for name, cmd in self.command_interface.commands.items():
                if not cmd.description:
                    raise ValueError(f"command_interface.commands['{name}'].description is required")
        return self


class PersonasIndex(RootModel[List[PersonaSpec]]):
    pass