"""Adaptive activities for Epic 3: Context-Aware Adaptive Resources."""

import time
import uuid
from datetime import datetime
from typing import Any, Dict, List

from temporalio import activity

from orchestra.models.context import (
    AdaptationStrategy,
    ContextDimension,
    ContextVariable,
    ContextVariableType,
    WorkflowConditionOperator,
)
from orchestra.services.adaptive_service import AdaptiveService
from orchestra.utils.logging import get_logger

logger = get_logger(__name__)


@activity.defn
async def dynamic_template_activity(template_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute dynamic template adaptation for context-aware template processing.

    Adapts templates based on context variables with performance requirement
    (<200ms for context changes) and relevance scoring (>85%).

    Args:
        template_context: Template adaptation parameters including:
            - project_id: Project identifier
            - persona_id: Persona identifier
            - template_id: Template to adapt
            - context_variables: Context variables for adaptation

    Returns:
        Dictionary with adapted template and adaptation metrics
    """
    start_time = time.time()
    
    logger.info(
        "Starting dynamic template activity",
        project_id=template_context.get("project_id"),
        persona_id=template_context.get("persona_id"),
        template_id=template_context.get("template_id"),
        context_variables=list(template_context.get("context_variables", {}).keys()),
    )

    try:
        # Initialize adaptive service
        adaptive_service = AdaptiveService()
        
        # Perform template adaptation
        adaptation_result = await adaptive_service.adapt_template(
            project_id=template_context.get("project_id", ""),
            persona_id=template_context.get("persona_id", ""),
            template_id=template_context.get("template_id", ""),
            context_variables=template_context.get("context_variables", {}),
        )
        
        adaptation_time_ms = (time.time() - start_time) * 1000
        
        # Verify performance requirement (AC6: <200ms for context changes)
        if adaptation_time_ms > 200:
            logger.warning(
                "Template adaptation exceeded performance requirement",
                adaptation_time_ms=adaptation_time_ms,
                performance_requirement_ms=200,
            )

        # Verify relevance requirement (AC8: >85% relevance)
        relevance_score = adaptation_result.get("relevance_score", 0.0)
        if relevance_score < 0.85:
            logger.warning(
                "Template adaptation below relevance requirement",
                relevance_score=relevance_score,
                relevance_requirement=0.85,
            )

        result = {
            "success": True,
            "adaptation_id": adaptation_result.get("adaptation_id"),
            "adapted_template": {
                "name": adaptation_result.get("template_name"),
                "content": adaptation_result.get("adapted_content"),
                "adaptations_applied": adaptation_result.get("adaptations_applied", []),
            },
            "relevance_score": relevance_score,
            "adaptation_time_ms": adaptation_time_ms,
            "context_dimensions_used": adaptation_result.get("context_dimensions_used", []),
        }

        logger.info(
            "Dynamic template activity completed",
            adaptation_id=result["adaptation_id"],
            relevance_score=relevance_score,
            adaptation_time_ms=adaptation_time_ms,
            adaptations_count=len(result["adapted_template"]["adaptations_applied"]),
        )

        return result

    except Exception as e:
        adaptation_time_ms = (time.time() - start_time) * 1000
        
        logger.error(
            "Dynamic template activity failed",
            error=str(e),
            project_id=template_context.get("project_id"),
            template_id=template_context.get("template_id"),
            adaptation_time_ms=adaptation_time_ms,
        )
        
        return {
            "success": False,
            "error": str(e),
            "adaptation_time_ms": adaptation_time_ms,
        }


@activity.defn
async def conditional_workflow_activity(workflow_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute conditional workflow evaluation for context-based execution paths.

    Evaluates conditions and selects workflow branches with support for
    complex decision trees (>10 conditions).

    Args:
        workflow_context: Conditional workflow parameters including:
            - project_id: Project identifier
            - workflow_id: Workflow identifier
            - context_variables: Current context variables
            - conditions: List of conditions to evaluate
            - condition_logic: Logic for combining conditions (AND/OR)

    Returns:
        Dictionary with branch selection and evaluation metrics
    """
    start_time = time.time()
    
    logger.info(
        "Starting conditional workflow activity",
        project_id=workflow_context.get("project_id"),
        workflow_id=workflow_context.get("workflow_id"),
        conditions_count=len(workflow_context.get("conditions", [])),
        condition_logic=workflow_context.get("condition_logic"),
    )

    try:
        # Initialize adaptive service
        adaptive_service = AdaptiveService()
        
        # Evaluate conditional workflow
        evaluation_result = await adaptive_service.evaluate_conditional_workflow(
            project_id=workflow_context.get("project_id", ""),
            workflow_id=workflow_context.get("workflow_id", ""),
            context_variables=workflow_context.get("context_variables", {}),
            conditions=workflow_context.get("conditions", []),
            condition_logic=workflow_context.get("condition_logic", "AND"),
        )
        
        evaluation_time_ms = (time.time() - start_time) * 1000
        
        # Verify complex decision tree support (AC7: >10 conditions)
        conditions_count = len(workflow_context.get("conditions", []))
        if conditions_count > 10:
            logger.info(
                "Complex decision tree evaluated",
                conditions_count=conditions_count,
                complex_decision_tree_requirement=10,
            )

        result = {
            "success": True,
            "execution_id": evaluation_result.get("execution_id"),
            "conditions_evaluated": evaluation_result.get("conditions_evaluated"),
            "conditions_met": evaluation_result.get("conditions_met"),
            "branch_taken": evaluation_result.get("branch_taken"),
            "selected_workflow": evaluation_result.get("selected_workflow"),
            "logic_type": workflow_context.get("condition_logic"),
            "decision_tree_depth": evaluation_result.get("decision_tree_depth", 1),
            "evaluation_time_ms": evaluation_time_ms,
        }

        logger.info(
            "Conditional workflow activity completed",
            execution_id=result["execution_id"],
            conditions_evaluated=result["conditions_evaluated"],
            conditions_met=result["conditions_met"],
            branch_taken=result["branch_taken"],
            evaluation_time_ms=evaluation_time_ms,
        )

        return result

    except Exception as e:
        evaluation_time_ms = (time.time() - start_time) * 1000
        
        logger.error(
            "Conditional workflow activity failed",
            error=str(e),
            project_id=workflow_context.get("project_id"),
            workflow_id=workflow_context.get("workflow_id"),
            evaluation_time_ms=evaluation_time_ms,
        )
        
        return {
            "success": False,
            "error": str(e),
            "evaluation_time_ms": evaluation_time_ms,
        }


@activity.defn
async def context_aware_resource_activity(resource_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute context-aware resource loading for relevant resource selection.

    Selects resources based on context with relevance scoring and ranking
    (>85% relevance for provided resources).

    Args:
        resource_context: Resource loading parameters including:
            - project_id: Project identifier
            - persona_id: Persona identifier
            - current_task: Current task context
            - context_variables: Context variables for resource selection

    Returns:
        Dictionary with selected resources and relevance metrics
    """
    start_time = time.time()
    
    logger.info(
        "Starting context-aware resource activity",
        project_id=resource_context.get("project_id"),
        persona_id=resource_context.get("persona_id"),
        current_task=resource_context.get("current_task"),
        context_variables=list(resource_context.get("context_variables", {}).keys()),
    )

    try:
        # Initialize adaptive service
        adaptive_service = AdaptiveService()
        
        # Load context-aware resources
        loading_result = await adaptive_service.load_context_aware_resources(
            project_id=resource_context.get("project_id", ""),
            persona_id=resource_context.get("persona_id", ""),
            current_task=resource_context.get("current_task", ""),
            context_variables=resource_context.get("context_variables", {}),
        )
        
        loading_time_ms = (time.time() - start_time) * 1000
        
        # Calculate average relevance and verify requirement (AC8: >85%)
        resources = loading_result.get("resources", [])
        if resources:
            total_relevance = sum(r.get("relevance_score", 0.0) for r in resources)
            average_relevance = total_relevance / len(resources)
        else:
            average_relevance = 0.0

        if average_relevance < 0.85:
            logger.warning(
                "Resource relevance below requirement",
                average_relevance=average_relevance,
                relevance_requirement=0.85,
            )

        result = {
            "success": True,
            "loader_id": loading_result.get("loader_id"),
            "resources_found": len(resources),
            "resources": resources,
            "average_relevance": average_relevance,
            "loading_time_ms": loading_time_ms,
        }

        logger.info(
            "Context-aware resource activity completed",
            loader_id=result["loader_id"],
            resources_found=result["resources_found"],
            average_relevance=average_relevance,
            loading_time_ms=loading_time_ms,
        )

        return result

    except Exception as e:
        loading_time_ms = (time.time() - start_time) * 1000
        
        logger.error(
            "Context-aware resource activity failed",
            error=str(e),
            project_id=resource_context.get("project_id"),
            current_task=resource_context.get("current_task"),
            loading_time_ms=loading_time_ms,
        )
        
        return {
            "success": False,
            "error": str(e),
            "loading_time_ms": loading_time_ms,
        }


@activity.defn
async def context_persistence_activity(persistence_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute context persistence for memory system integration.

    Stores context variables and patterns in the memory system for
    persistent context learning and pattern recognition.

    Args:
        persistence_context: Context persistence parameters including:
            - project_id: Project identifier
            - persona_id: Persona identifier
            - context_variables: Context variables to persist
            - learning_patterns: Patterns learned from context

    Returns:
        Dictionary with persistence results and memory namespace information
    """
    start_time = time.time()
    
    logger.info(
        "Starting context persistence activity",
        project_id=persistence_context.get("project_id"),
        persona_id=persistence_context.get("persona_id"),
        context_variables=list(persistence_context.get("context_variables", {}).keys()),
        learning_patterns=len(persistence_context.get("learning_patterns", [])),
    )

    try:
        # Initialize adaptive service
        adaptive_service = AdaptiveService()
        
        # Persist context to memory system
        persistence_result = await adaptive_service.persist_context(
            project_id=persistence_context.get("project_id", ""),
            persona_id=persistence_context.get("persona_id", ""),
            context_variables=persistence_context.get("context_variables", {}),
            learning_patterns=persistence_context.get("learning_patterns", []),
        )
        
        storage_time_ms = (time.time() - start_time) * 1000
        
        # Generate memory namespace for adaptive context (AC5: Memory integration)
        project_id = persistence_context.get("project_id", "")
        memory_namespace = f"adaptive_context_{project_id}"

        result = {
            "success": True,
            "persistence_id": persistence_result.get("persistence_id"),
            "context_stored": persistence_result.get("context_stored", False),
            "patterns_learned": len(persistence_context.get("learning_patterns", [])),
            "memory_namespace": memory_namespace,
            "storage_time_ms": storage_time_ms,
        }

        logger.info(
            "Context persistence activity completed",
            persistence_id=result["persistence_id"],
            context_stored=result["context_stored"],
            patterns_learned=result["patterns_learned"],
            memory_namespace=result["memory_namespace"],
            storage_time_ms=storage_time_ms,
        )

        return result

    except Exception as e:
        storage_time_ms = (time.time() - start_time) * 1000
        
        logger.error(
            "Context persistence activity failed",
            error=str(e),
            project_id=persistence_context.get("project_id"),
            persona_id=persistence_context.get("persona_id"),
            storage_time_ms=storage_time_ms,
        )
        
        return {
            "success": False,
            "error": str(e),
            "storage_time_ms": storage_time_ms,
        }


@activity.defn
async def context_learning_activity(learning_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute context learning for pattern recognition and improvement.

    Analyzes historical contexts and outcomes to identify patterns
    for improved context-aware resource selection.

    Args:
        learning_context: Context learning parameters including:
            - project_id: Project identifier
            - historical_contexts: Historical context and outcome data

    Returns:
        Dictionary with identified patterns and confidence metrics
    """
    start_time = time.time()
    
    logger.info(
        "Starting context learning activity",
        project_id=learning_context.get("project_id"),
        historical_contexts=len(learning_context.get("historical_contexts", [])),
    )

    try:
        # Initialize adaptive service
        adaptive_service = AdaptiveService()
        
        # Perform context learning
        learning_result = await adaptive_service.learn_from_context(
            project_id=learning_context.get("project_id", ""),
            historical_contexts=learning_context.get("historical_contexts", []),
        )
        
        learning_time_ms = (time.time() - start_time) * 1000

        result = {
            "success": True,
            "learning_id": learning_result.get("learning_id"),
            "patterns_identified": learning_result.get("patterns_identified", []),
            "learning_time_ms": learning_time_ms,
        }

        logger.info(
            "Context learning activity completed",
            learning_id=result["learning_id"],
            patterns_identified=len(result["patterns_identified"]),
            learning_time_ms=learning_time_ms,
        )

        return result

    except Exception as e:
        learning_time_ms = (time.time() - start_time) * 1000
        
        logger.error(
            "Context learning activity failed",
            error=str(e),
            project_id=learning_context.get("project_id"),
            learning_time_ms=learning_time_ms,
        )
        
        return {
            "success": False,
            "error": str(e),
            "learning_time_ms": learning_time_ms,
        }


@activity.defn
async def backward_compatibility_activity(compatibility_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute backward compatibility for existing resource system integration.

    Ensures adaptive resources maintain backward compatibility with
    existing resource system while providing enhanced functionality.

    Args:
        compatibility_context: Compatibility parameters including:
            - project_id: Project identifier
            - legacy_resource_id: Legacy resource identifier
            - adaptive_features_enabled: Whether adaptive features are enabled

    Returns:
        Dictionary with compatibility results and enhancement status
    """
    start_time = time.time()
    
    logger.info(
        "Starting backward compatibility activity",
        project_id=compatibility_context.get("project_id"),
        legacy_resource_id=compatibility_context.get("legacy_resource_id"),
        adaptive_features_enabled=compatibility_context.get("adaptive_features_enabled"),
    )

    try:
        # Initialize adaptive service
        adaptive_service = AdaptiveService()
        
        # Check backward compatibility
        compatibility_result = await adaptive_service.ensure_backward_compatibility(
            project_id=compatibility_context.get("project_id", ""),
            legacy_resource_id=compatibility_context.get("legacy_resource_id", ""),
            adaptive_features_enabled=compatibility_context.get("adaptive_features_enabled", False),
        )
        
        execution_time_ms = (time.time() - start_time) * 1000

        result = {
            "success": True,
            "compatibility_id": compatibility_result.get("compatibility_id"),
            "legacy_resource_accessible": compatibility_result.get("legacy_resource_accessible", True),
            "adaptive_enhancements_applied": compatibility_result.get("adaptive_enhancements_applied", False),
            "backward_compatible": compatibility_result.get("backward_compatible", True),  # AC9
            "original_functionality_preserved": compatibility_result.get("original_functionality_preserved", True),
            "execution_time_ms": execution_time_ms,
        }

        # Verify backward compatibility requirement (AC9)
        if not result["backward_compatible"]:
            logger.warning(
                "Backward compatibility requirement not met",
                legacy_resource_id=compatibility_context.get("legacy_resource_id"),
                backward_compatible=result["backward_compatible"],
            )

        logger.info(
            "Backward compatibility activity completed",
            compatibility_id=result["compatibility_id"],
            legacy_resource_accessible=result["legacy_resource_accessible"],
            backward_compatible=result["backward_compatible"],
            execution_time_ms=execution_time_ms,
        )

        return result

    except Exception as e:
        execution_time_ms = (time.time() - start_time) * 1000
        
        logger.error(
            "Backward compatibility activity failed",
            error=str(e),
            project_id=compatibility_context.get("project_id"),
            legacy_resource_id=compatibility_context.get("legacy_resource_id"),
            execution_time_ms=execution_time_ms,
        )
        
        return {
            "success": False,
            "error": str(e),
            "execution_time_ms": execution_time_ms,
        }