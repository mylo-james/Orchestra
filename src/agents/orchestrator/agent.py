"""Orchestrator agent built on OpenAI Agents SDK with SecureAgent base."""

from __future__ import annotations

from src.agents.base.secure_agent import SecureAgent, AgentContext
from src.agents.tools.github import get_github_tools


class OrchestratorAgent(SecureAgent):
    """Orchestrator agent using OpenAI Agents SDK with planning capabilities."""

    agent_name = "orchestrator"

    def __init__(self, settings=None, model_cfg=None):
        instructions = """You are the Orchestrator, a master planning and coordination agent.

Your primary responsibilities:
- Create concise, actionable multi-agent plans
- Coordinate workflow execution and agent handoffs
- Analyze user requests and break them into manageable tasks
- Assign appropriate agents to specific tasks
- Monitor progress and adapt plans as needed

You have access to GitHub tools for repository operations and can coordinate
with Developer and Release agents for implementation tasks."""

        # Add GitHub tools to the orchestrator
        tools = get_github_tools()

        super().__init__(
            settings=settings,
            model_cfg=model_cfg,
            instructions=instructions,
            tools=tools,
        )

    async def plan(self, goal: str, context: AgentContext = None) -> str:
        """Create a multi-agent plan for the given goal."""
        if context is None:
            context = AgentContext(
                agent_name=self.agent_name, correlation_id=f"plan_{goal[:20]}"
            )

        planning_prompt = f"""
        Create a detailed multi-agent plan for this goal: {goal}

        Consider:
        - What agents are needed (Developer, Release, others)
        - What tasks can be done in parallel vs sequential
        - What GitHub operations might be required
        - Success criteria and validation steps

        Provide a structured plan with numbered steps.
        """

        return await self.ask(planning_prompt, context)
