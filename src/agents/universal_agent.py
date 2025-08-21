from __future__ import annotations

from typing import List, Optional

from agents import FunctionTool

from src.agents.base.secure_agent import SecureAgent
from src.agents.tools.github import get_github_tools
from src.personas.loader import load_persona
from src.personas.specs import PersonaSpec


_TOOL_REGISTRY: dict[str, List[FunctionTool]] = {
    "github-tools": get_github_tools(),
}


def _resolve_tools(spec: PersonaSpec) -> List[FunctionTool]:
    tools: List[FunctionTool] = []
    rd = spec.resource_dependencies
    if rd:
        for key in rd.tools:
            if key in _TOOL_REGISTRY:
                tools.extend(_TOOL_REGISTRY[key])
    return tools


def _compile_instructions(spec: PersonaSpec) -> str:
    identity = spec.identity
    lines: List[str] = []
    lines.append(f"You are {identity.name} ({identity.title}). Persona id: {identity.id}.")
    if spec.behavioral_contract:
        bc = spec.behavioral_contract
        if bc.core_principles:
            lines.append("Core principles:")
            for p in bc.core_principles:
                lines.append(f"- {p}")
        if bc.interaction_style:
            lines.append(f"Interaction style: {bc.interaction_style}")
        if bc.halt_conditions:
            lines.append("Halt conditions:")
            for c in bc.halt_conditions:
                lines.append(f"- {c}")
    if spec.command_interface and spec.command_interface.commands:
        lines.append("Commands:")
        for name, cmd in spec.command_interface.commands.items():
            lines.append(f"- {name}: {cmd.description}")
            if cmd.execution_pattern:
                lines.append(f"  pattern: {cmd.execution_pattern}")
    return "\n".join(lines)


class UniversalAgent(SecureAgent):
    agent_name = "universal"

    def __init__(self, persona_id: str, settings=None, model_cfg=None):
        self.persona_id = persona_id
        spec = load_persona(persona_id)
        instructions = _compile_instructions(spec)
        tools = _resolve_tools(spec)
        super().__init__(
            settings=settings,
            model_cfg=model_cfg,
            instructions=instructions,
            tools=tools,
        )
        # Make visible for consumers
        self.persona_spec = spec