"""Knowledge sharing workflow activities for Orchestra AI cross-persona knowledge sharing."""

import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from temporalio import activity

from orchestra.models.shared_knowledge import (
    SharedKnowledge,
    TargetingTag,
    ValidationMetric,
)
from orchestra.services.memory_service import MemoryService
from orchestra.services.pattern_matching_service import PatternMatchingService
from orchestra.utils.logging import get_logger

logger = get_logger(__name__)


@activity.defn
async def knowledge_sharing_activity(
    sharing_context: Dict[str, Any],
    operation: str = "export_patterns",
) -> Dict[str, Any]:
    """
    Knowledge sharing activity for cross-persona pattern export/import.

    Args:
        sharing_context: Knowledge sharing context
        operation: Operation type (export_patterns, import_shared_knowledge)

    Returns:
        Knowledge sharing result with exported/imported patterns
    """
    logger.info(
        "Executing knowledge sharing activity",
        operation=operation,
        source_persona=sharing_context.get("source_persona_id"),
        project_id=sharing_context.get("project_id"),
    )

    try:
        # Initialize services
        memory_service = MemoryService()
        pattern_service = PatternMatchingService()

        if operation == "export_patterns":
            return await _export_shareable_patterns(
                sharing_context, memory_service, pattern_service
            )
        elif operation == "import_shared_knowledge":
            return await _import_shared_knowledge(sharing_context, memory_service)
        else:
            raise ValueError(f"Unknown knowledge sharing operation: {operation}")

    except Exception as e:
        logger.error(
            "Knowledge sharing activity failed",
            error=str(e),
            operation=operation,
        )
        return {
            "success": False,
            "error": str(e),
            "operation": operation,
        }


@activity.defn
async def pattern_matching_activity(
    source_persona_id: str,
    target_personas: List[str],
    project_id: str,
    context_similarity: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    AI-assisted pattern matching activity for transferability assessment.

    Args:
        source_persona_id: Source persona ID
        target_personas: List of target persona IDs
        project_id: Project ID for context
        context_similarity: Context similarity data

    Returns:
        Pattern matching results with transferability scores
    """
    logger.info(
        "Executing pattern matching activity",
        source_persona=source_persona_id,
        target_personas=target_personas,
        project_id=project_id,
    )

    try:
        # Initialize pattern matching service
        pattern_service = PatternMatchingService()

        matching_results = []

        # Analyze patterns for each target persona (AC: 2, 7 - >75% accuracy)
        for target_persona in target_personas:
            try:
                result = await pattern_service.find_transferable_patterns(
                    source_persona_id,
                    target_persona,
                    project_id,
                    context_similarity,
                )

                if result.get("success"):
                    matching_results.append(
                        {
                            "target_persona": target_persona,
                            "transferable_patterns": result.get(
                                "transferable_patterns", []
                            ),
                            "pattern_mappings": result.get("pattern_mappings", []),
                            "transferable_count": result.get("transferable_count", 0),
                        }
                    )
                else:
                    matching_results.append(
                        {
                            "target_persona": target_persona,
                            "error": result.get("error", "Unknown error"),
                            "transferable_patterns": [],
                            "pattern_mappings": [],
                        }
                    )

            except Exception as e:
                logger.warning(
                    "Pattern matching failed for target persona",
                    error=str(e),
                    target_persona=target_persona,
                )
                matching_results.append(
                    {
                        "target_persona": target_persona,
                        "error": str(e),
                        "transferable_patterns": [],
                        "pattern_mappings": [],
                    }
                )

        # Calculate overall statistics
        total_transferable = sum(
            result.get("transferable_count", 0) for result in matching_results
        )
        successful_matches = sum(
            1 for result in matching_results if "error" not in result
        )

        result = {
            "success": True,
            "matching_results": matching_results,
            "total_transferable_patterns": total_transferable,
            "successful_matches": successful_matches,
            "failed_matches": len(target_personas) - successful_matches,
            "performance_metrics": pattern_service.get_performance_metrics(),
        }

        logger.info(
            "Pattern matching activity completed",
            total_transferable=total_transferable,
            successful_matches=successful_matches,
        )

        return result

    except Exception as e:
        logger.error(
            "Pattern matching activity failed",
            error=str(e),
            source_persona=source_persona_id,
        )
        return {
            "success": False,
            "error": str(e),
            "matching_results": [],
            "total_transferable_patterns": 0,
        }


@activity.defn
async def propagation_activity(
    shared_knowledge_list: List[Dict[str, Any]],
    target_personas: List[str],
    propagation_mode: str = "automatic",
) -> Dict[str, Any]:
    """
    Knowledge propagation activity for distributing patterns to target personas.

    Args:
        shared_knowledge_list: List of shared knowledge to propagate
        target_personas: Target persona IDs
        propagation_mode: Propagation mode (automatic, manual, conditional)

    Returns:
        Propagation results with distribution statistics
    """
    logger.info(
        "Executing propagation activity",
        knowledge_count=len(shared_knowledge_list),
        target_personas=target_personas,
        propagation_mode=propagation_mode,
    )

    try:
        # Initialize services
        memory_service = MemoryService()

        propagation_results = []

        # Process each shared knowledge item (AC: 3 - distribute best practices)
        for knowledge_data in shared_knowledge_list:
            try:
                # Create SharedKnowledge object
                shared_knowledge = SharedKnowledge(
                    knowledge_id=knowledge_data.get("knowledge_id", str(uuid.uuid4())),
                    source_persona_id=knowledge_data["source_persona_id"],
                    source_project_id=knowledge_data["source_project_id"],
                    pattern_id=knowledge_data.get("pattern_id", str(uuid.uuid4())),
                    knowledge_type=knowledge_data.get(
                        "knowledge_type", "success_pattern"
                    ),
                    title=knowledge_data.get("title", "Shared Pattern"),
                    description=knowledge_data.get("description", ""),
                    content=knowledge_data.get("content", {}),
                    transferability_metadata=knowledge_data.get(
                        "transferability_metadata", {}
                    ),
                    effectiveness_score=knowledge_data.get("effectiveness_score", 0.8),
                    usage_count=0,
                    success_rate=1.0,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )

                # Propagate to each target persona
                persona_results = []
                for target_persona in target_personas:
                    try:
                        propagation_result = await _propagate_to_persona(
                            shared_knowledge,
                            target_persona,
                            propagation_mode,
                            memory_service,
                        )
                        persona_results.append(propagation_result)

                    except Exception as e:
                        logger.warning(
                            "Failed to propagate to persona",
                            error=str(e),
                            target_persona=target_persona,
                            knowledge_id=shared_knowledge.knowledge_id,
                        )
                        persona_results.append(
                            {
                                "target_persona": target_persona,
                                "success": False,
                                "error": str(e),
                            }
                        )

                propagation_results.append(
                    {
                        "knowledge_id": shared_knowledge.knowledge_id,
                        "source_persona": shared_knowledge.source_persona_id,
                        "persona_results": persona_results,
                        "successful_propagations": sum(
                            1 for r in persona_results if r.get("success")
                        ),
                        "failed_propagations": sum(
                            1 for r in persona_results if not r.get("success")
                        ),
                    }
                )

            except Exception as e:
                logger.warning(
                    "Failed to process shared knowledge",
                    error=str(e),
                    knowledge_data=knowledge_data,
                )
                propagation_results.append(
                    {
                        "knowledge_id": knowledge_data.get("knowledge_id", "unknown"),
                        "error": str(e),
                        "persona_results": [],
                    }
                )

        # Calculate overall statistics
        total_successful = 0
        total_failed = 0
        for result in propagation_results:
            successful = result.get("successful_propagations", 0)
            failed = result.get("failed_propagations", 0)
            if isinstance(successful, int):
                total_successful += successful
            if isinstance(failed, int):
                total_failed += failed

        result = {
            "success": True,
            "propagation_results": propagation_results,
            "total_successful_propagations": total_successful,
            "total_failed_propagations": total_failed,
            "propagation_mode": propagation_mode,
            "knowledge_items_processed": len(shared_knowledge_list),
        }

        logger.info(
            "Propagation activity completed",
            successful_propagations=total_successful,
            failed_propagations=total_failed,
            propagation_mode=propagation_mode,
        )

        return result

    except Exception as e:
        logger.error(
            "Propagation activity failed",
            error=str(e),
            propagation_mode=propagation_mode,
        )
        return {
            "success": False,
            "error": str(e),
            "propagation_results": [],
            "total_successful_propagations": 0,
            "total_failed_propagations": 0,
        }


@activity.defn
async def validation_activity(
    shared_knowledge_ids: List[str],
    target_personas: List[str],
    validation_period_days: int = 7,
) -> Dict[str, Any]:
    """
    Pattern validation activity for effectiveness measurement and rollback.

    Args:
        shared_knowledge_ids: List of shared knowledge IDs to validate
        target_personas: Target persona IDs for validation
        validation_period_days: Validation measurement period

    Returns:
        Validation results with effectiveness metrics and rollback decisions
    """
    logger.info(
        "Executing validation activity",
        knowledge_count=len(shared_knowledge_ids),
        target_personas=target_personas,
        validation_period=validation_period_days,
    )

    try:
        # Initialize services
        pattern_service = PatternMatchingService()

        validation_results = []

        # Validate each shared knowledge item (AC: 4, 10 - ensure beneficial patterns)
        for knowledge_id in shared_knowledge_ids:
            try:
                knowledge_validation = await _validate_shared_knowledge(
                    knowledge_id,
                    target_personas,
                    validation_period_days,
                    pattern_service,
                )
                validation_results.append(knowledge_validation)

            except Exception as e:
                logger.warning(
                    "Failed to validate shared knowledge",
                    error=str(e),
                    knowledge_id=knowledge_id,
                )
                validation_results.append(
                    {
                        "knowledge_id": knowledge_id,
                        "success": False,
                        "error": str(e),
                        "validation_metrics": [],
                    }
                )

        # Analyze overall validation results
        beneficial_count = sum(
            1
            for result in validation_results
            if result.get("overall_beneficial", False)
        )
        rollback_required_count = sum(
            1 for result in validation_results if result.get("rollback_required", False)
        )

        # Generate validation summary
        validation_summary = {
            "total_validated": len(shared_knowledge_ids),
            "beneficial_patterns": beneficial_count,
            "ineffective_patterns": len(shared_knowledge_ids) - beneficial_count,
            "rollback_required": rollback_required_count,
            "validation_period_days": validation_period_days,
            "overall_success_rate": beneficial_count
            / max(1, len(shared_knowledge_ids)),
        }

        result = {
            "success": True,
            "validation_results": validation_results,
            "validation_summary": validation_summary,
        }

        logger.info(
            "Validation activity completed",
            beneficial_patterns=beneficial_count,
            rollback_required=rollback_required_count,
        )

        return result

    except Exception as e:
        logger.error(
            "Validation activity failed",
            error=str(e),
            validation_period=validation_period_days,
        )
        return {
            "success": False,
            "error": str(e),
            "validation_results": [],
            "validation_summary": {},
        }


@activity.defn
async def tag_based_targeting_activity(
    knowledge_sharing_request: Dict[str, Any],
    targeting_criteria: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Tag-based targeting activity for precise knowledge routing.

    Args:
        knowledge_sharing_request: Knowledge sharing request
        targeting_criteria: Tag-based targeting criteria

    Returns:
        Targeting results with matched personas and routing decisions
    """
    logger.info(
        "Executing tag-based targeting activity",
        request_id=knowledge_sharing_request.get("request_id"),
        targeting_criteria=targeting_criteria,
    )

    try:
        # Create targeting tags from criteria (AC: 5 - tag-based targeting)
        targeting_tags = await _create_targeting_tags(
            targeting_criteria, knowledge_sharing_request.get("project_id", "unknown")
        )

        # Match personas based on tags
        matched_personas = []
        targeting_results = []

        for tag in targeting_tags:
            try:
                # Simulate persona matching (in production, query persona registry)
                personas_for_tag = await _match_personas_by_tag(tag)

                matched_personas.extend(personas_for_tag)
                targeting_results.append(
                    {
                        "tag": tag.get_targeting_summary(),
                        "matched_personas": personas_for_tag,
                        "match_count": len(personas_for_tag),
                    }
                )

            except Exception as e:
                logger.warning(
                    "Failed to match personas for tag",
                    error=str(e),
                    tag_id=tag.tag_id,
                )
                targeting_results.append(
                    {
                        "tag": tag.get_targeting_summary(),
                        "error": str(e),
                        "matched_personas": [],
                        "match_count": 0,
                    }
                )

        # Remove duplicates while preserving order
        unique_personas = list(dict.fromkeys(matched_personas))

        # Generate routing decisions
        routing_decisions = []
        for persona_id in unique_personas:
            # Determine routing strategy based on targeting results
            applicable_tags = []
            for result in targeting_results:
                if (
                    "matched_personas" in result
                    and isinstance(result["matched_personas"], list)
                    and persona_id in result["matched_personas"]
                    and "tag" in result
                    and isinstance(result["tag"], dict)
                    and "tag_name" in result["tag"]
                ):
                    applicable_tags.append(result["tag"]["tag_name"])

            routing_decisions.append(
                {
                    "persona_id": persona_id,
                    "applicable_tags": applicable_tags,
                    "routing_strategy": (
                        "automatic" if len(applicable_tags) > 1 else "conditional"
                    ),
                    "priority": "high" if "role" in str(applicable_tags) else "medium",
                }
            )

        result = {
            "success": True,
            "targeting_tags": [tag.get_targeting_summary() for tag in targeting_tags],
            "targeting_results": targeting_results,
            "matched_personas": unique_personas,
            "routing_decisions": routing_decisions,
            "total_matches": len(unique_personas),
        }

        logger.info(
            "Tag-based targeting activity completed",
            total_matches=len(unique_personas),
            tags_processed=len(targeting_tags),
        )

        return result

    except Exception as e:
        logger.error(
            "Tag-based targeting activity failed",
            error=str(e),
            request_id=knowledge_sharing_request.get("request_id"),
        )
        return {
            "success": False,
            "error": str(e),
            "targeting_tags": [],
            "matched_personas": [],
            "routing_decisions": [],
        }


# Helper functions


async def _export_shareable_patterns(
    sharing_context: Dict[str, Any],
    memory_service: MemoryService,
    pattern_service: PatternMatchingService,
) -> Dict[str, Any]:
    """Export shareable patterns from source persona."""
    try:
        # Get shareable patterns from memory service (AC: 1 - knowledge export)
        shareable_result = await memory_service.get_shareable_patterns(sharing_context)

        if not shareable_result.get("success"):
            return {
                "success": False,
                "error": "Failed to retrieve shareable patterns",
                "shareable_patterns": [],
            }

        patterns = shareable_result.get("patterns", [])

        # Convert to SharedKnowledge objects
        shared_knowledge_list = []
        for pattern in patterns:
            try:
                shared_knowledge = SharedKnowledge(
                    knowledge_id=str(uuid.uuid4()),
                    source_persona_id=sharing_context["source_persona_id"],
                    source_project_id=sharing_context["project_id"],
                    pattern_id=pattern["pattern_id"],
                    knowledge_type="success_pattern",
                    title=f"Pattern from {sharing_context['source_persona_id']}",
                    description=pattern.get("content", ""),
                    content=pattern,
                    transferability_metadata={
                        "effectiveness_score": pattern.get("effectiveness_score", 0.8),
                        "transferability_score": pattern.get(
                            "transferability_score", 0.8
                        ),
                        "applicable_personas": [],  # Will be determined during matching
                    },
                    effectiveness_score=pattern.get("effectiveness_score", 0.8),
                    usage_count=0,
                    success_rate=1.0,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                shared_knowledge_list.append(shared_knowledge)

            except Exception as e:
                logger.warning(
                    "Failed to create SharedKnowledge object",
                    error=str(e),
                    pattern_id=pattern.get("pattern_id"),
                )
                continue

        return {
            "success": True,
            "operation": "export_patterns",
            "shareable_patterns": [sk.__dict__ for sk in shared_knowledge_list],
            "patterns_count": len(shared_knowledge_list),
            "source_persona": sharing_context["source_persona_id"],
        }

    except Exception as e:
        logger.error("Pattern export failed", error=str(e))
        return {
            "success": False,
            "error": str(e),
            "operation": "export_patterns",
            "shareable_patterns": [],
        }


async def _import_shared_knowledge(
    sharing_context: Dict[str, Any],
    memory_service: MemoryService,
) -> Dict[str, Any]:
    """Import shared knowledge to target persona."""
    try:
        shared_knowledge_list = sharing_context.get("shared_knowledge", [])
        target_persona_id = sharing_context.get("target_persona_id")

        import_results = []

        # Import each shared knowledge item (AC: 1 - knowledge import)
        for knowledge_data in shared_knowledge_list:
            try:
                # Create memory record from shared knowledge
                memory_record = (
                    await memory_service.create_memory_from_learning_outcome(
                        {
                            "outcome_id": str(uuid.uuid4()),
                            "persona_id": target_persona_id,
                            "project_id": sharing_context["project_id"],
                            "patterns_identified": [
                                knowledge_data.get("title", "Shared Pattern")
                            ],
                            "classification": "shared_knowledge_import",
                            "effectiveness_score": knowledge_data.get(
                                "effectiveness_score", 0.8
                            ),
                        }
                    )
                )

                # Store in memory
                upsert_result = await memory_service.upsert_memory(memory_record)

                import_results.append(
                    {
                        "knowledge_id": knowledge_data.get("knowledge_id"),
                        "import_success": upsert_result.get("success", False),
                        "memory_id": upsert_result.get("memory_id"),
                    }
                )

            except Exception as e:
                logger.warning(
                    "Failed to import shared knowledge",
                    error=str(e),
                    knowledge_id=knowledge_data.get("knowledge_id"),
                )
                import_results.append(
                    {
                        "knowledge_id": knowledge_data.get("knowledge_id"),
                        "import_success": False,
                        "error": str(e),
                    }
                )

        successful_imports = sum(
            1 for result in import_results if result.get("import_success")
        )

        return {
            "success": True,
            "operation": "import_shared_knowledge",
            "import_results": import_results,
            "successful_imports": successful_imports,
            "failed_imports": len(import_results) - successful_imports,
            "target_persona": target_persona_id,
        }

    except Exception as e:
        logger.error("Knowledge import failed", error=str(e))
        return {
            "success": False,
            "error": str(e),
            "operation": "import_shared_knowledge",
            "import_results": [],
        }


async def _propagate_to_persona(
    shared_knowledge: SharedKnowledge,
    target_persona_id: str,
    propagation_mode: str,
    memory_service: MemoryService,
) -> Dict[str, Any]:
    """Propagate shared knowledge to a specific target persona."""
    try:
        start_time = time.time()

        # Check transferability for target persona
        transferability = shared_knowledge.assess_transferability(target_persona_id)

        if not transferability.get("applicable", True):
            return {
                "target_persona": target_persona_id,
                "success": False,
                "reason": "Not applicable to target persona",
                "transferability": transferability,
            }

        # Create memory record for target persona
        memory_record = await memory_service.create_memory_from_learning_outcome(
            {
                "outcome_id": str(uuid.uuid4()),
                "persona_id": target_persona_id,
                "project_id": shared_knowledge.source_project_id,
                "patterns_identified": [shared_knowledge.title],
                "classification": "knowledge_sharing_propagation",
                "effectiveness_score": shared_knowledge.effectiveness_score,
                "confidence_score": transferability.get("score", 0.8),
            }
        )

        # Store in target persona's memory
        upsert_result = await memory_service.upsert_memory(memory_record)

        propagation_time_ms = (time.time() - start_time) * 1000

        # Verify performance requirement (AC: 9 - <500ms load time)
        if propagation_time_ms > 500:
            logger.warning(
                "Knowledge propagation exceeded 500ms load time requirement",
                propagation_time_ms=propagation_time_ms,
                requirement_ms=500,
            )

        return {
            "target_persona": target_persona_id,
            "success": upsert_result.get("success", False),
            "memory_id": upsert_result.get("memory_id"),
            "transferability": transferability,
            "propagation_time_ms": propagation_time_ms,
            "propagation_mode": propagation_mode,
        }

    except Exception as e:
        logger.error(
            "Failed to propagate to persona",
            error=str(e),
            target_persona=target_persona_id,
            knowledge_id=shared_knowledge.knowledge_id,
        )
        return {
            "target_persona": target_persona_id,
            "success": False,
            "error": str(e),
        }


async def _validate_shared_knowledge(
    knowledge_id: str,
    target_personas: List[str],
    validation_period_days: int,
    pattern_service: PatternMatchingService,
) -> Dict[str, Any]:
    """Validate effectiveness of shared knowledge."""
    try:
        # Simulate shared knowledge retrieval and validation
        # In production, this would retrieve actual SharedKnowledge and performance data

        validation_metrics = []

        for persona_id in target_personas:
            # Simulate validation metric creation (AC: 4 - ensure beneficial patterns)
            validation_metric = ValidationMetric(
                metric_id=str(uuid.uuid4()),
                shared_knowledge_id=knowledge_id,
                target_persona_id=persona_id,
                project_id="test-project",  # Would be retrieved from context
                validation_type="effectiveness_measurement",
                pre_sharing_metrics={"success_rate": 0.7, "quality_score": 0.6},
                post_sharing_metrics={"success_rate": 0.8, "quality_score": 0.75},
                improvement_analysis={},
                effectiveness_threshold=0.6,  # AC: 8 - >60% effectiveness improvement
                validation_status="under_review",
                measurement_period_days=validation_period_days,
            )

            # Calculate improvement metrics
            validation_metric.calculate_improvement_metrics()

            # Determine validation status
            if validation_metric.should_allow_propagation():
                validation_metric.validation_status = "beneficial"
            else:
                validation_metric.validation_status = "ineffective"

            # Check if rollback is needed (AC: 10 - prevent <50% effectiveness)
            overall_effectiveness = validation_metric.improvement_analysis.get(
                "overall_effectiveness", 0.0
            )
            if overall_effectiveness < 0.5:
                validation_metric.trigger_rollback(
                    "Pattern effectiveness below 50% threshold"
                )

            validation_metrics.append(validation_metric)

        # Determine overall validation result
        beneficial_count = sum(
            1
            for metric in validation_metrics
            if metric.validation_status == "beneficial"
        )
        rollback_count = sum(
            1 for metric in validation_metrics if metric.rollback_required
        )

        overall_beneficial = beneficial_count > len(validation_metrics) / 2
        rollback_required = rollback_count > 0

        return {
            "knowledge_id": knowledge_id,
            "success": True,
            "validation_metrics": [metric.__dict__ for metric in validation_metrics],
            "overall_beneficial": overall_beneficial,
            "rollback_required": rollback_required,
            "beneficial_personas": beneficial_count,
            "total_personas": len(target_personas),
            "validation_period_days": validation_period_days,
        }

    except Exception as e:
        logger.error(
            "Shared knowledge validation failed",
            error=str(e),
            knowledge_id=knowledge_id,
        )
        return {
            "knowledge_id": knowledge_id,
            "success": False,
            "error": str(e),
            "validation_metrics": [],
            "overall_beneficial": False,
            "rollback_required": False,
        }


async def _create_targeting_tags(
    targeting_criteria: Dict[str, Any],
    project_id: str,
) -> List[TargetingTag]:
    """Create targeting tags from criteria."""
    targeting_tags = []

    # Process different types of targeting criteria
    for criteria_type, criteria_values in targeting_criteria.items():
        if not isinstance(criteria_values, list):
            criteria_values = [criteria_values]

        for value in criteria_values:
            tag = TargetingTag(
                tag_id=str(uuid.uuid4()),
                tag_name=f"{criteria_type}_{value}",
                tag_type=criteria_type,  # technology, role, domain, specialization
                tag_value=str(value),
                project_id=project_id,
                target_criteria={criteria_type: value},
                matched_personas=[],  # Will be populated by matching
                hierarchical_tags={},
                active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            targeting_tags.append(tag)

    return targeting_tags


async def _match_personas_by_tag(tag: TargetingTag) -> List[str]:
    """Match personas based on targeting tag."""
    # Simulate persona matching based on tag
    # In production, this would query the persona registry

    if tag.tag_type == "role":
        role_personas = {
            "dev": ["dev-persona-1", "dev-persona-2", "fullstack-dev"],
            "qa": ["qa-persona-1", "test-architect"],
            "architect": ["architect-persona-1", "solution-architect"],
            "pm": ["pm-persona-1", "product-manager"],
            "po": ["po-persona-1", "product-owner"],
        }
        return role_personas.get(tag.tag_value, [])

    elif tag.tag_type == "technology":
        tech_personas = {
            "python": ["python-dev", "backend-dev", "fullstack-dev"],
            "javascript": ["js-dev", "frontend-dev", "fullstack-dev"],
            "react": ["react-dev", "frontend-dev"],
            "docker": ["devops-persona", "backend-dev"],
        }
        return tech_personas.get(tag.tag_value, [])

    elif tag.tag_type == "domain":
        domain_personas = {
            "fintech": ["fintech-dev", "security-specialist"],
            "healthcare": ["healthcare-dev", "compliance-specialist"],
            "ecommerce": ["ecommerce-dev", "payment-specialist"],
        }
        return domain_personas.get(tag.tag_value, [])

    else:
        # Default fallback
        return ["general-persona"]
