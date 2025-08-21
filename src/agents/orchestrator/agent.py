"""Orchestrator agent built on SecureAgent."""

from __future__ import annotations

from src.agents.base.secure_agent import SecureAgent


class OrchestratorAgent(SecureAgent):
    agent_name = "orchestrator"

    async def plan(self, goal: str) -> str:
        system = (
            "You are the Orchestrator. Create concise, actionable multi-agent plans."
        )
        return await self.ask(goal, system)
