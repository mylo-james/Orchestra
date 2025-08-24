"""Temporal activities for agent execution and workflow operations."""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict

from temporalio import activity

from orchestra.system.agent import UniversalAgent
from orchestra.system.factory import get_registry
from orchestra.utils.logging import get_logger

logger = get_logger(__name__)


@activity.defn
async def execute_agent_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute an agent with the given context.

    This activity wraps agent execution in a Temporal activity for durability
    and fault tolerance. All external API calls (OpenAI, GitHub) happen within
    this activity boundary.

    Args:
        params: Dictionary containing:
            - agent_type: Type of agent to execute (maps to persona)
            - context: Workflow context for the agent
            - operation: Operation to perform (plan, implement, release)

    Returns:
        Dictionary with agent execution results
    """
    agent_type = params["agent_type"]
    context = params["context"]
    operation = params["operation"]

    logger.info(
        "Executing agent activity",
        agent_type=agent_type,
        operation=operation,
        session_id=context.get("session_id"),
        correlation_id=context.get("correlation_id"),
    )

    try:
        # Create agent instance using persona
        registry = get_registry()
        # Map agent_type to persona_id if needed
        persona_map = {
            "orchestrator": "orchestrator",
            "developer": "dev",
            "release": "release",
        }
        persona_id = persona_map.get(agent_type, agent_type)
        agent = registry.create(persona_id)

        # All agents must be UniversalAgent instances
        if not isinstance(agent, UniversalAgent):
            raise ValueError(
                f"Agent must be a UniversalAgent instance, got {type(agent)}"
            )

        result = await _execute_with_universal_agent(agent, operation, context)

        logger.info(
            "Agent activity completed successfully",
            agent_type=agent_type,
            operation=operation,
            confidence=result.get("confidence"),
        )

        return result

    except Exception as e:
        logger.error(
            "Agent activity failed",
            agent_type=agent_type,
            operation=operation,
            error=str(e),
            exc_info=True,
        )
        raise


async def _execute_with_universal_agent(
    agent: UniversalAgent, operation: str, context: Dict[str, Any]
) -> Dict[str, Any]:
    """Execute operation using UniversalAgent with persona-based commands."""

    # Map operations to persona commands
    operation_to_command = {
        "plan": "plan",
        "implement": "implement-story",
        "release": "create-pr",
    }

    command = operation_to_command.get(operation)
    if not command:
        # Try using operation directly as command
        command = operation

    # Prepare parameters from context
    params = {
        "context": context,
        "working_memory": context.get("working_memory", {}),
        "request": context.get("working_memory", {}).get("request", ""),
    }

    # Execute the command
    result = await agent.execute_command(command, params)

    if result["success"]:
        # Format result for workflow consumption
        return {
            "conversation": {
                "role": agent.persona_id,
                "content": f"Executed {command}: {json.dumps(result.get('result', {}), indent=2)}",
                "timestamp": datetime.utcnow().isoformat(),
            },
            "confidence": 0.85,
            "memory_updates": result.get("result", {}),
            "next_action": _determine_next_action(agent.persona_id, operation),
        }
    else:
        raise Exception(f"Command execution failed: {result.get('error')}")


def _determine_next_action(persona_id: str, operation: str) -> str:
    """Determine the next action based on persona and operation."""
    if persona_id == "orchestrator" and operation == "plan":
        return "implement"
    elif persona_id == "dev" and operation == "implement":
        return "release"
    elif persona_id == "release":
        return "complete"
    return "continue"


@activity.defn
async def validate_context_activity(context: Dict[str, Any]) -> Dict[str, bool]:
    """
    Validate workflow context integrity.

    Args:
        context: Workflow context to validate

    Returns:
        Validation result with details
    """
    logger.info(
        "Validating workflow context",
        session_id=context.get("session_id"),
        correlation_id=context.get("correlation_id"),
    )

    validation_errors = []

    # Check required fields
    if not context.get("session_id"):
        validation_errors.append("Missing session_id")

    if not context.get("correlation_id"):
        validation_errors.append("Missing correlation_id")

    if not context.get("security_context"):
        validation_errors.append("Missing security_context")

    # Check schema version
    schema_version = context.get("schema_version", "")
    if not schema_version.startswith("1."):
        validation_errors.append(f"Unsupported schema version: {schema_version}")

    # Check for data corruption
    if context.get("task_state") not in [
        "planning",
        "implementing",
        "reviewing",
        "releasing",
        "completed",
        "failed",
        None,
    ]:
        validation_errors.append(f"Invalid task_state: {context.get('task_state')}")

    valid = len(validation_errors) == 0

    if not valid:
        logger.warning(
            "Context validation failed",
            errors=validation_errors,
            session_id=context.get("session_id"),
        )

    return {
        "valid": valid,
        "errors": validation_errors,
    }


@activity.defn
async def create_github_pr_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a GitHub pull request.

    This activity wraps GitHub API operations in a Temporal activity
    for durability and retry handling.

    Args:
        params: PR creation parameters including title, body, branch

    Returns:
        PR creation result with URL
    """
    title = params["title"]
    _ = params["body"]  # Will be used in actual implementation
    branch = params["branch"]
    context = params["context"]

    logger.info(
        "Creating GitHub PR",
        title=title,
        branch=branch,
        session_id=context.get("session_id"),
    )

    try:
        # Simulate GitHub API call (would use actual GitHub client)
        await asyncio.sleep(0.5)

        # In real implementation, this would call GitHub API
        pr_url = f"https://github.com/org/repo/pull/{datetime.now().microsecond}"

        logger.info(
            "GitHub PR created successfully",
            pr_url=pr_url,
            branch=branch,
        )

        return {
            "success": True,
            "url": pr_url,
            "pr_number": datetime.now().microsecond,
            "branch": branch,
        }

    except Exception as e:
        logger.error(
            "Failed to create GitHub PR",
            error=str(e),
            title=title,
            exc_info=True,
        )
        raise
