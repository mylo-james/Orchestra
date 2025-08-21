"""Developer agent built on SecureAgent."""

from __future__ import annotations

from src.agents.base.secure_agent import SecureAgent


class DeveloperAgent(SecureAgent):
    agent_name = "developer"

    async def implement(self, task: str) -> str:
        system = "You are a senior Python engineer. Produce robust, secure code."
        return await self.ask(task, system)
