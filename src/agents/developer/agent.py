"""Developer agent built on OpenAI Agents SDK with SecureAgent base."""

from __future__ import annotations

from src.agents.base.secure_agent import SecureAgent, AgentContext
from src.agents.tools.github import get_github_tools


class DeveloperAgent(SecureAgent):
    """Developer agent using OpenAI Agents SDK with code implementation capabilities."""

    agent_name = "developer"

    def __init__(self, settings=None, model_cfg=None):
        instructions = """You are a Senior Python Engineer and Implementation Specialist.

Your expertise includes:
- Python 3.12+ development with async/await patterns
- OpenAI Agents SDK integration and patterns
- Security best practices and input validation
- Test-driven development with pytest
- Code quality standards (Black, isort, Ruff)
- Temporal workflow integration
- Pydantic for data validation and type safety

Follow the project's coding standards:
- Use async/await for all I/O operations
- Include comprehensive docstrings and type hints
- Implement proper error handling with correlation IDs
- Add security validation for all inputs
- Write tests for all new functionality

You have access to GitHub tools for repository operations and can create PRs,
manage branches, and coordinate with other agents."""

        # Add GitHub tools to the developer
        tools = get_github_tools()

        super().__init__(
            settings=settings,
            model_cfg=model_cfg,
            instructions=instructions,
            tools=tools
        )

    async def implement(self, task: str, context: AgentContext = None) -> str:
        """Implement a development task.

        Temporary stub returns a token for tests; replace with self.ask(...) in integration.
        """
        return f"IMPL:{task}"
