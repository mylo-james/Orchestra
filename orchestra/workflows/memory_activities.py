"""Memory workflow activities for Orchestra AI memory infrastructure."""

import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List

from temporalio import activity

from orchestra.models.memory import ContextPattern, MemoryRecord, RetentionPolicy
from orchestra.services.memory_service import MemoryService
from orchestra.utils.logging import get_logger

logger = get_logger(__name__)


@activity.defn
async def memory_upsert_activity(
    execution_context: Dict[str, Any],
    patterns: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Memory upsert activity for context capture and pattern storage.

    Args:
        execution_context: Persona execution context
        patterns: Extracted patterns and context data

    Returns:
        Upsert result with success status and memory ID
    """
    logger.info(
        "Executing memory upsert activity",
        project_id=execution_context.get("project_id"),
        persona_id=execution_context.get("persona_id"),
    )

    try:
        # Initialize memory service
        memory_service = MemoryService()

        # Extract context and create memory record
        memory_record = await _create_memory_record_from_context(
            execution_context, patterns
        )

        # Validate relevance score (AC: 7 - >80% relevance score)
        if memory_record.relevance_score < 0.8:
            logger.warning(
                "Memory relevance score below threshold",
                relevance_score=memory_record.relevance_score,
                threshold=0.8,
            )
            return {
                "success": False,
                "relevance_score": memory_record.relevance_score,
                "reason": "Low relevance score - below 80% threshold",
            }

        # Upsert memory record
        upsert_result = await memory_service.upsert_memory(memory_record)

        if upsert_result["success"]:
            # Create context pattern if this represents a successful pattern
            if execution_context.get("result", {}).get("success"):
                context_pattern = await _create_context_pattern(
                    execution_context, patterns, memory_record
                )
                pattern_result = await memory_service.store_context_pattern(
                    context_pattern
                )
                upsert_result["pattern_stored"] = pattern_result.get("success", False)

            logger.info(
                "Memory upsert activity completed successfully",
                memory_id=upsert_result.get("memory_id"),
                relevance_score=memory_record.relevance_score,
            )

        return upsert_result

    except Exception as e:
        logger.error(
            "Memory upsert activity failed",
            error=str(e),
            project_id=execution_context.get("project_id"),
        )
        return {
            "success": False,
            "error": str(e),
        }


@activity.defn
async def memory_retrieval_activity(query_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Memory retrieval activity for context-aware memory search.

    Args:
        query_context: Query parameters and context

    Returns:
        Retrieval result with memories and performance metrics
    """
    start_time = time.time()

    logger.info(
        "Executing memory retrieval activity",
        project_id=query_context.get("project_id"),
        persona_id=query_context.get("persona_id"),
    )

    try:
        # Initialize memory service
        memory_service = MemoryService()

        # Execute semantic search
        search_result = await memory_service.semantic_search(query_context)

        end_time = time.time()
        retrieval_time_ms = (end_time - start_time) * 1000

        # Verify performance requirement (AC: 8 - <200ms response time)
        if retrieval_time_ms > 200:
            logger.warning(
                "Memory retrieval exceeded 200ms requirement",
                retrieval_time_ms=retrieval_time_ms,
                requirement_ms=200,
            )

        result = {
            "success": search_result.get("success", False),
            "memories": search_result.get("memories", []),
            "retrieval_time_ms": retrieval_time_ms,
            "total_results": len(search_result.get("memories", [])),
        }

        # Add recommendation system results
        if query_context.get("include_recommendations", True):
            recommendations = await _generate_memory_recommendations(
                query_context, search_result.get("memories", [])
            )
            result["recommendations"] = recommendations

        logger.info(
            "Memory retrieval activity completed",
            memories_found=len(result["memories"]),
            retrieval_time_ms=retrieval_time_ms,
        )

        return result

    except Exception as e:
        logger.error(
            "Memory retrieval activity failed",
            error=str(e),
            project_id=query_context.get("project_id"),
        )
        return {
            "success": False,
            "error": str(e),
            "retrieval_time_ms": (time.time() - start_time) * 1000,
        }


@activity.defn
async def memory_management_activity(
    management_context: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Memory management activity for retention policy enforcement.

    Args:
        management_context: Management operation parameters

    Returns:
        Management result with cleanup and archival statistics
    """
    logger.info(
        "Executing memory management activity",
        project_id=management_context.get("project_id"),
        operation=management_context.get("operation"),
    )

    try:
        # Initialize memory service
        memory_service = MemoryService()

        operation = management_context.get("operation")

        if operation == "enforce_retention":
            return await _enforce_retention_policy(memory_service, management_context)

        elif operation == "check_memory_usage":
            return await _check_memory_usage(memory_service, management_context)

        elif operation == "scheduled_cleanup":
            return await _scheduled_cleanup(memory_service, management_context)

        else:
            raise ValueError(f"Unknown memory management operation: {operation}")

    except Exception as e:
        logger.error(
            "Memory management activity failed",
            error=str(e),
            operation=management_context.get("operation"),
        )
        return {
            "success": False,
            "error": str(e),
        }


# Helper functions


async def _create_memory_record_from_context(
    execution_context: Dict[str, Any],
    patterns: Dict[str, Any],
) -> MemoryRecord:
    """Create memory record from execution context and patterns."""
    memory_id = str(uuid.uuid4())

    # Extract content from execution context
    content = _extract_memory_content(execution_context, patterns)

    # Calculate relevance score based on patterns and context
    relevance_score = _calculate_relevance_score(execution_context, patterns)

    # Calculate confidence score
    confidence_score = execution_context.get("result", {}).get("confidence", 0.8)
    if isinstance(confidence_score, str):
        confidence_score = 0.8  # Default if not numeric

    # Create metadata
    metadata = {
        "domain": patterns.get("context_data", {}).get("domain", "general"),
        "complexity": patterns.get("context_data", {}).get("complexity", "medium"),
        "success_indicators": patterns.get("success_patterns", []),
        "command": execution_context.get("command"),
        "session_id": execution_context.get("session_id"),
        "duration_seconds": execution_context.get("duration_seconds", 0),
    }

    # Add result metadata if available
    result = execution_context.get("result", {})
    if result:
        metadata.update(
            {
                "success": result.get("success", False),
                "quality_score": result.get("quality_score", 0.0),
                "test_coverage": result.get("coverage", 0.0),
                "files_created": result.get("files_created", []),
            }
        )

    return MemoryRecord(
        memory_id=memory_id,
        project_id=execution_context["project_id"],
        persona_id=execution_context["persona_id"],
        content=content,
        embedding=[],  # Will be generated by memory service
        confidence_score=confidence_score,
        relevance_score=relevance_score,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        metadata=metadata,
    )


def _extract_memory_content(
    execution_context: Dict[str, Any],
    patterns: Dict[str, Any],
) -> str:
    """Extract meaningful content for memory storage."""
    content_parts = []

    # Add command and context
    command = execution_context.get("command", "unknown")
    content_parts.append(f"Command: {command}")

    # Add success patterns
    success_patterns = patterns.get("success_patterns", [])
    if success_patterns:
        content_parts.append(f"Success patterns: {', '.join(success_patterns)}")

    # Add context data
    context_data = patterns.get("context_data", {})
    if context_data:
        domain = context_data.get("domain", "general")
        complexity = context_data.get("complexity", "medium")
        content_parts.append(f"Domain: {domain}, Complexity: {complexity}")

    # Add result summary
    result = execution_context.get("result", {})
    if result.get("success"):
        content_parts.append("Execution successful")

        # Add specific success details
        if result.get("files_created"):
            content_parts.append(f"Files created: {', '.join(result['files_created'])}")

        if result.get("tests_passed"):
            content_parts.append(f"Tests passed: {result['tests_passed']}")

        if result.get("coverage"):
            content_parts.append(f"Test coverage: {result['coverage']:.2%}")

    return ". ".join(content_parts)


def _calculate_relevance_score(
    execution_context: Dict[str, Any],
    patterns: Dict[str, Any],
) -> float:
    """Calculate relevance score for memory record."""
    base_score = 0.5

    # Boost score for successful executions
    if execution_context.get("result", {}).get("success"):
        base_score += 0.2

    # Boost score for high-quality results
    quality_score = execution_context.get("result", {}).get("quality_score", 0)
    if quality_score > 0.8:
        base_score += 0.15

    # Boost score for high test coverage
    coverage = execution_context.get("result", {}).get("coverage", 0)
    if coverage > 0.8:
        base_score += 0.1

    # Boost score for security validation
    if execution_context.get("result", {}).get("security_validated"):
        base_score += 0.1

    # Boost score for complex domains
    domain = patterns.get("context_data", {}).get("domain", "general")
    if domain in ["authentication", "security", "performance"]:
        base_score += 0.1

    # Boost score for detailed patterns
    success_patterns = patterns.get("success_patterns", [])
    if len(success_patterns) > 2:
        base_score += 0.05

    return min(1.0, base_score)


async def _create_context_pattern(
    execution_context: Dict[str, Any],
    patterns: Dict[str, Any],
    memory_record: MemoryRecord,
) -> ContextPattern:
    """Create context pattern from successful execution."""
    pattern_id = f"pattern-{memory_record.memory_id}"

    # Determine pattern type
    result = execution_context.get("result", {})
    if result.get("success"):
        pattern_type = "success_pattern"
    else:
        pattern_type = "failure_pattern"

    # Create description
    domain = patterns.get("context_data", {}).get("domain", "general")
    command = execution_context.get("command", "unknown")
    description = (
        f"{pattern_type.replace('_', ' ').title()} for {command} in {domain} domain"
    )

    # Extract success metrics
    success_metrics = {}
    if result.get("success"):
        success_metrics["success_rate"] = 1.0
        success_metrics["completion_time"] = execution_context.get(
            "duration_seconds", 0
        )

        if result.get("coverage"):
            success_metrics["test_coverage"] = result["coverage"]

        if result.get("quality_score"):
            success_metrics["quality_score"] = result["quality_score"]

    return ContextPattern(
        pattern_id=pattern_id,
        project_id=execution_context["project_id"],
        persona_id=execution_context["persona_id"],
        pattern_type=pattern_type,
        description=description,
        context_data=patterns.get("context_data", {}),
        success_metrics=success_metrics,
        usage_count=1,
        last_used=datetime.utcnow(),
        created_at=datetime.utcnow(),
        effectiveness_score=memory_record.relevance_score,
    )


async def _generate_memory_recommendations(
    query_context: Dict[str, Any],
    memories: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Generate memory recommendations based on query and results."""
    recommendations = []

    # Recommend high-relevance memories
    high_relevance_memories = [
        memory for memory in memories if memory.get("relevance_score", 0) > 0.9
    ]

    if high_relevance_memories:
        recommendations.append(
            {
                "type": "high_relevance",
                "title": "Highly Relevant Patterns",
                "description": f"Found {len(high_relevance_memories)} highly relevant patterns",
                "memories": high_relevance_memories[:3],  # Top 3
            }
        )

    # Recommend similar domain patterns
    query_domain = query_context.get("domain")
    if query_domain:
        domain_memories = [
            memory
            for memory in memories
            if memory.get("metadata", {}).get("domain") == query_domain
        ]

        if domain_memories:
            recommendations.append(
                {
                    "type": "domain_specific",
                    "title": f"{query_domain.title()} Domain Patterns",
                    "description": f"Patterns specific to {query_domain} domain",
                    "memories": domain_memories[:2],
                }
            )

    # Recommend recent successful patterns
    recent_successful = [
        memory
        for memory in memories
        if (
            memory.get("metadata", {}).get("success", False)
            and memory.get("created_at")
            and (datetime.utcnow() - datetime.fromisoformat(memory["created_at"])).days
            < 30
        )
    ]

    if recent_successful:
        recommendations.append(
            {
                "type": "recent_successful",
                "title": "Recent Successful Patterns",
                "description": "Recently successful patterns from the last 30 days",
                "memories": recent_successful[:2],
            }
        )

    return recommendations


async def _enforce_retention_policy(
    memory_service: MemoryService,
    management_context: Dict[str, Any],
) -> Dict[str, Any]:
    """Enforce retention policy for memory cleanup."""
    project_id = management_context.get("project_id")
    retention_days = management_context.get("retention_days", 90)

    # Create default retention policy
    retention_policy = RetentionPolicy(
        policy_id=f"retention-{project_id}",
        project_id=project_id,
        policy_name="Standard Retention Policy",
        retention_days=retention_days,
        archive_after_days=retention_days,
        delete_after_days=365,
        rules={
            "high_value_memories": {
                "min_relevance_score": 0.85,
                "retention_days": retention_days * 2,
            },
            "low_value_memories": {
                "max_relevance_score": 0.50,
                "retention_days": retention_days // 2,
            },
        },
        active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    # Get memories for the project
    memories = await memory_service.get_project_memories(project_id)

    # Enforce retention policy
    enforcement_result = await memory_service.enforce_retention_policy(
        retention_policy, memories
    )

    return {
        "success": True,
        "operation": "enforce_retention",
        "archived_count": enforcement_result.get("memories_archived", 0),
        "deleted_count": enforcement_result.get("memories_deleted", 0),
        "retained_count": enforcement_result.get("memories_retained", 0),
        "memories_processed": enforcement_result.get("memories_processed", 0),
        "next_run": datetime.utcnow() + timedelta(days=1),
    }


async def _check_memory_usage(
    memory_service: MemoryService,
    management_context: Dict[str, Any],
) -> Dict[str, Any]:
    """Check memory usage and trigger cleanup if needed."""
    max_memory_gb = management_context.get("max_memory_gb", 4.0)

    # Get current memory usage
    usage_stats = await memory_service.get_memory_usage()
    current_memory_gb = usage_stats.get("current_memory_gb", 0.0)

    result = {
        "success": True,
        "operation": "check_memory_usage",
        "current_memory_gb": current_memory_gb,
        "max_memory_gb": max_memory_gb,
        "within_limits": current_memory_gb <= max_memory_gb,
        "cleanup_triggered": False,
    }

    # Trigger cleanup if approaching limits (AC: 9 - 4GB constraint)
    if current_memory_gb > (max_memory_gb * 0.875):  # 87.5% of limit
        cleanup_result = await memory_service.trigger_cleanup()

        result.update(
            {
                "cleanup_triggered": True,
                "cleanup_freed_gb": cleanup_result.get("memory_freed_gb", 0),
                "cleanup_details": cleanup_result,
            }
        )

        # Update memory usage after cleanup
        post_cleanup_usage = await memory_service.get_memory_usage()
        result["post_cleanup_memory_gb"] = post_cleanup_usage.get(
            "current_memory_gb", 0.0
        )

    return result


async def _scheduled_cleanup(
    memory_service: MemoryService,
    management_context: Dict[str, Any],
) -> Dict[str, Any]:
    """Execute scheduled cleanup operations."""
    project_id = management_context.get("project_id")
    schedule = management_context.get("schedule", "daily")

    # Execute comprehensive cleanup
    cleanup_operations = []

    # 1. Retention policy enforcement
    retention_result = await _enforce_retention_policy(
        memory_service, management_context
    )
    cleanup_operations.append(
        {
            "operation": "retention_enforcement",
            "result": retention_result,
        }
    )

    # 2. Memory usage check and cleanup
    usage_result = await _check_memory_usage(memory_service, management_context)
    cleanup_operations.append(
        {
            "operation": "memory_usage_check",
            "result": usage_result,
        }
    )

    # 3. Index optimization
    index_result = await memory_service.optimize_indexes(project_id)
    cleanup_operations.append(
        {
            "operation": "index_optimization",
            "result": index_result,
        }
    )

    return {
        "success": True,
        "operation": "scheduled_cleanup",
        "schedule": schedule,
        "cleanup_operations": cleanup_operations,
        "next_run": datetime.utcnow() + timedelta(days=1 if schedule == "daily" else 7),
        "timestamp": datetime.utcnow().isoformat(),
    }
