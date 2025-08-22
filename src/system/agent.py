"""Universal Agent that can embody any persona through YAML configuration."""

import asyncio
from typing import Any, Dict, List, Optional

from agents.tools import FunctionTool

from src.system.base import SecureAgent
from src.system.loader import PersonaLoader
from src.system.specs import CommandDefinition, PersonaSpec
from src.system.tools import create_github_pr_tool, list_repositories_tool
from src.utils.logging import get_logger

logger = get_logger(__name__)


class UniversalAgent(SecureAgent):
    """
    Universal agent that can embody any persona defined in YAML.

    This agent dynamically loads persona specifications and configures
    itself based on the loaded persona's behavioral contract, tools,
    and command interface.
    """

    def __init__(
        self,
        persona_id: str = "orchestrator",
        persona_spec: Optional[PersonaSpec] = None,
    ):
        """
        Initialize the UniversalAgent with a specific persona.

        Args:
            persona_id: ID of the persona to load
            persona_spec: Pre-loaded PersonaSpec (optional, will load from file if not provided)
        """
        # Load persona if not provided
        if persona_spec is None:
            loader = PersonaLoader()
            persona_spec = loader.load_persona(persona_id)
            if not persona_spec:
                raise ValueError(f"Failed to load persona: {persona_id}")

        self.persona_spec = persona_spec
        self.persona_id = persona_id

        # Initialize base agent with persona name
        super().__init__()
        self.agent_name = f"universal_{persona_id}"

        # Configure agent based on persona
        self._configure_from_persona()

        logger.info(f"UniversalAgent initialized as: {self.persona_spec.display_name}")

    def _configure_from_persona(self) -> None:
        """Configure the agent based on the loaded persona specification."""
        # Set agent identity
        self.agent_role = self.persona_spec.identity.role
        self.agent_style = self.persona_spec.identity.style
        self.agent_focus = self.persona_spec.identity.focus

        # Set behavioral parameters
        self.core_principles = self.persona_spec.behavioral_contract.core_principles
        self.halt_conditions = self.persona_spec.behavioral_contract.halt_conditions
        self.interaction_style = self.persona_spec.behavioral_contract.interaction_style

        # Configure execution model
        self.execution_model = self.persona_spec.command_interface.execution_model

        # Load and configure tools
        self._load_persona_tools()

    def _load_persona_tools(self) -> None:
        """Load tools specified in the persona's resource dependencies."""
        self.tools = []

        for tool_name in self.persona_spec.resource_dependencies.tools:
            tool = self._resolve_tool(tool_name)
            if tool:
                self.tools.append(tool)
                logger.debug(f"Loaded tool for persona: {tool_name}")
            else:
                logger.warning(f"Tool not found for persona: {tool_name}")

    def _resolve_tool(self, tool_name: str) -> Optional[FunctionTool]:
        """
        Resolve a tool name to an actual tool instance.

        Args:
            tool_name: Name of the tool to resolve

        Returns:
            FunctionTool instance if found, None otherwise
        """
        # Map tool names to actual tool functions
        tool_registry = {
            "github-tools": [create_github_pr_tool(), list_repositories_tool()],
            "create-pr": [create_github_pr_tool()],
            "list-repos": [list_repositories_tool()],
        }

        # Return tools if found in registry
        if tool_name in tool_registry:
            tools = tool_registry[tool_name]
            return tools[0] if len(tools) == 1 else tools

        # Log unknown tool
        logger.warning(f"Unknown tool requested: {tool_name}")
        return None

    async def execute_command(
        self, command_name: str, params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Execute a command defined in the persona's command interface.

        Args:
            command_name: Name of the command to execute
            params: Parameters for the command

        Returns:
            Command execution result
        """
        # Get command definition
        command = self.persona_spec.get_command(command_name)
        if not command:
            return {
                "success": False,
                "error": f"Command not found: {command_name}",
                "available_commands": list(
                    self.persona_spec.command_interface.commands.keys()
                ),
            }

        logger.info(
            f"Executing command: {command_name}",
            persona=self.persona_id,
            pattern=command.execution_pattern,
        )

        # Check if confirmation is required
        if command.requires_confirmation:
            logger.info(f"Command {command_name} requires confirmation")
            # In production, would implement confirmation logic

        # Execute based on pattern
        try:
            result = await self._execute_pattern(command, params or {})

            return {
                "success": True,
                "command": command_name,
                "result": result,
                "persona": self.persona_id,
            }

        except asyncio.TimeoutError:
            logger.error(
                f"Command {command_name} timed out after {command.timeout_seconds}s"
            )
            return {
                "success": False,
                "error": f"Command timed out after {command.timeout_seconds} seconds",
            }
        except Exception as e:
            logger.error(f"Command {command_name} failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
            }

    async def _execute_pattern(
        self, command: CommandDefinition, params: Dict[str, Any]
    ) -> Any:
        """
        Execute a command pattern.

        Args:
            command: Command definition to execute
            params: Parameters for execution

        Returns:
            Execution result
        """
        pattern = command.execution_pattern

        # Parse execution pattern (simplified for MVP)
        steps = [step.strip() for step in pattern.split("→")]

        results = []
        for step in steps:
            # Execute each step based on execution model
            if self.execution_model == "parallel" and len(steps) > 1:
                # Would implement parallel execution
                pass

            # Sequential execution (default)
            result = await self._execute_step(step, params)
            results.append(result)

            # Check halt conditions
            if self._should_halt(result):
                logger.warning(f"Halting execution due to condition: {result}")
                break

        return results

    async def _execute_step(self, step: str, params: Dict[str, Any]) -> Any:
        """
        Execute a single step in a command pattern.

        Args:
            step: Step name to execute
            params: Parameters for the step

        Returns:
            Step execution result
        """
        # Map step names to actual operations
        step_handlers = {
            "read_story": self._read_story,
            "implement": self._implement_code,
            "test": self._run_tests,
            "validate": self._validate_output,
            "plan": self._create_plan,
            "analyze": self._analyze_request,
        }

        handler = step_handlers.get(step)
        if handler:
            return await handler(params)

        # Default: log and return placeholder
        logger.info(f"Executing step: {step} with params: {params}")
        return {"step": step, "status": "completed", "params": params}

    def _should_halt(self, result: Any) -> bool:
        """
        Check if execution should halt based on conditions.

        Args:
            result: Result to check against halt conditions

        Returns:
            True if should halt, False otherwise
        """
        if not self.halt_conditions:
            return False

        # Check each halt condition
        for condition in self.halt_conditions:
            if condition == "Security validation failures" and isinstance(result, dict):
                if result.get("security_failed"):
                    return True
            elif condition == "Ambiguous requirements" and isinstance(result, dict):
                if result.get("ambiguous"):
                    return True

        return False

    # Placeholder methods for step execution
    async def _read_story(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Read a story file."""
        return {"action": "read_story", "status": "completed"}

    async def _implement_code(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Implement code based on requirements."""
        return {"action": "implement", "status": "completed"}

    async def _run_tests(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run tests on implemented code."""
        return {"action": "test", "status": "completed"}

    async def _validate_output(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate output against requirements."""
        return {"action": "validate", "status": "completed"}

    async def _create_plan(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create an execution plan."""
        return {"action": "plan", "status": "completed"}

    async def _analyze_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a user request."""
        return {"action": "analyze", "status": "completed"}

    def get_system_prompt(self) -> str:
        """
        Generate system prompt based on persona specification.

        Returns:
            System prompt for the agent
        """
        prompt_parts = [
            f"You are {self.persona_spec.identity.name}, {self.persona_spec.identity.title}.",
            f"Your role: {self.persona_spec.identity.role}",
            f"Your style: {self.persona_spec.identity.style}",
            f"Your focus: {self.persona_spec.identity.focus}",
            "",
            "Core Principles:",
        ]

        for principle in self.persona_spec.behavioral_contract.core_principles:
            prompt_parts.append(f"- {principle}")

        if self.persona_spec.identity.when_to_use:
            prompt_parts.append(
                f"\nYou are best suited for: {self.persona_spec.identity.when_to_use}"
            )

        return "\n".join(prompt_parts)

    def get_available_commands(self) -> List[str]:
        """
        Get list of available commands for this persona.

        Returns:
            List of command names
        """
        return list(self.persona_spec.command_interface.commands.keys())

    def describe(self) -> str:
        """
        Get a human-readable description of the agent's current persona.

        Returns:
            Description string
        """
        return (
            f"{self.persona_spec.display_name}\n"
            f"Role: {self.persona_spec.identity.role}\n"
            f"Commands: {', '.join(self.get_available_commands())}\n"
            f"Tools: {', '.join(self.persona_spec.resource_dependencies.tools)}\n"
            f"Execution Model: {self.persona_spec.command_interface.execution_model}"
        )
