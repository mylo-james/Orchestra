"""Release agent built on OpenAI Agents SDK with SecureAgent base."""

from __future__ import annotations

from src.agents.base.secure_agent import SecureAgent, AgentContext
from src.agents.tools.github import get_github_tools


class ReleaseAgent(SecureAgent):
    """Release agent using OpenAI Agents SDK with release management capabilities."""

    agent_name = "release"

    def __init__(self, settings=None, model_cfg=None):
        instructions = """You are a Release Manager and Git Integration Specialist.

Your responsibilities include:
- Creating clear, accurate release notes
- Managing Git branches and pull requests
- Coordinating release processes and deployments
- Ensuring code quality gates are met
- Managing version numbers and changelogs
- Reviewing and approving changes

You work closely with:
- Developer agents for code integration
- Orchestrator for release planning
- QA processes for quality validation

You have access to GitHub tools for repository operations including PR creation,
branch management, and release coordination."""

        # Add GitHub tools to the release agent
        tools = get_github_tools()

        super().__init__(
            settings=settings,
            model_cfg=model_cfg,
            instructions=instructions,
            tools=tools
        )

    async def draft_notes(self, changes_summary: str, context: AgentContext = None) -> str:
        """Draft release notes from a changes summary (stub for tests)."""
        return f"NOTES:{changes_summary}"
