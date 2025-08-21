"""Release agent built on SecureAgent."""

from __future__ import annotations

from src.agents.base.secure_agent import SecureAgent


class ReleaseAgent(SecureAgent):
    agent_name = "release"

    async def draft_notes(self, changes_summary: str) -> str:
        system = "You are a release manager. Draft clear, accurate release notes."
        return await self.ask(changes_summary, system)

