"""Release agent built on OpenAI Agents SDK with SecureAgent base."""

from __future__ import annotations

from typing import Optional

from src.agents.base.secure_agent import AgentContext, SecureAgent
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
            tools=tools,
        )

    async def draft_notes(
        self, changes_summary: str, context: Optional[AgentContext] = None
    ) -> str:
        """Draft release notes from a changes summary."""
        if context is None:
            context = AgentContext(
                agent_name=self.agent_name,
                correlation_id=f"notes_{changes_summary[:20]}",
            )

        notes_prompt = f"""
        Draft clear, professional release notes for these changes: {changes_summary}

        Structure the release notes with:
        - Version and date
        - Summary of key changes
        - New features (if any)
        - Bug fixes (if any)
        - Breaking changes (if any)
        - Migration notes (if needed)

        Use clear, user-focused language that explains the impact of changes.
        """

        return await self.ask(notes_prompt, context)
