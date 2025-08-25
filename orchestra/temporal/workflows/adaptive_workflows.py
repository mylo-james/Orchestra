"""Adaptive workflow sub-workflows for Orchestra AI adaptive resources."""

from datetime import timedelta
from typing import Any, Dict

from temporalio import workflow
from temporalio.common import RetryPolicy

from orchestra.temporal.activities.adaptive import (
    backward_compatibility_activity,
    conditional_workflow_activity,
    context_aware_resource_activity,
    context_learning_activity,
    context_persistence_activity,
    dynamic_template_activity,
)


@workflow.defn
class DynamicTemplateWorkflow:
    """
    Dynamic template sub-workflow for context-aware template processing.

    Adapts templates based on project context and current state with
    performance requirements (<200ms for context changes).
    """

    @workflow.run
    async def run(self, template_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute dynamic template adaptation workflow.

        Args:
            template_context: Template adaptation parameters and context

        Returns:
            Adaptation result with adapted template and relevance metrics
        """
        workflow.logger.info(
            "Starting dynamic template workflow",
            project_id=template_context.get("project_id"),
            persona_id=template_context.get("persona_id"),
            template_id=template_context.get("template_id"),
            context_variables=list(template_context.get("context_variables", {}).keys()),
        )

        try:
            # Execute dynamic template adaptation activity
            result = await workflow.execute_activity(
                dynamic_template_activity,
                args=[template_context],
                start_to_close_timeout=timedelta(seconds=15),  # Fast timeout for performance
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(milliseconds=500),
                    maximum_interval=timedelta(seconds=3),
                    maximum_attempts=3,
                ),
            )

            workflow.logger.info(
                "Dynamic template workflow completed",
                success=result.get("success"),
                adaptation_id=result.get("adaptation_id"),
                relevance_score=result.get("relevance_score"),
                adaptation_time_ms=result.get("adaptation_time_ms"),
                adaptations_applied=len(result.get("adapted_template", {}).get("adaptations_applied", [])),
            )

            return result

        except Exception as e:
            workflow.logger.error(
                "Dynamic template workflow failed",
                error=str(e),
                project_id=template_context.get("project_id"),
                template_id=template_context.get("template_id"),
            )
            raise


@workflow.defn
class ConditionalWorkflowEngine:
    """
    Conditional workflow engine for context-based execution paths.

    Executes different workflow paths based on context variables with
    support for complex decision trees (>10 conditions).
    """

    @workflow.run
    async def run(self, workflow_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute conditional workflow engine.

        Args:
            workflow_context: Conditional workflow parameters and context

        Returns:
            Execution result with branch selection and evaluation metrics
        """
        workflow.logger.info(
            "Starting conditional workflow engine",
            project_id=workflow_context.get("project_id"),
            workflow_id=workflow_context.get("workflow_id"),
            conditions_count=len(workflow_context.get("conditions", [])),
            condition_logic=workflow_context.get("condition_logic"),
        )

        try:
            # Execute conditional workflow evaluation activity
            result = await workflow.execute_activity(
                conditional_workflow_activity,
                args=[workflow_context],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=1),
                    maximum_interval=timedelta(seconds=5),
                    maximum_attempts=3,
                ),
            )

            workflow.logger.info(
                "Conditional workflow engine completed",
                success=result.get("success"),
                execution_id=result.get("execution_id"),
                conditions_evaluated=result.get("conditions_evaluated"),
                conditions_met=result.get("conditions_met"),
                branch_taken=result.get("branch_taken"),
                evaluation_time_ms=result.get("evaluation_time_ms"),
            )

            return result

        except Exception as e:
            workflow.logger.error(
                "Conditional workflow engine failed",
                error=str(e),
                project_id=workflow_context.get("project_id"),
                workflow_id=workflow_context.get("workflow_id"),
            )
            raise


@workflow.defn
class ContextAwareResourceLoader:
    """
    Context-aware resource loader for relevant resource selection.

    Provides context-based resource selection with relevance scoring
    and resource ranking (>85% relevance for provided resources).
    """

    @workflow.run
    async def run(self, resource_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute context-aware resource loading.

        Args:
            resource_context: Resource loading parameters and context

        Returns:
            Loading result with selected resources and relevance metrics
        """
        workflow.logger.info(
            "Starting context-aware resource loader",
            project_id=resource_context.get("project_id"),
            persona_id=resource_context.get("persona_id"),
            current_task=resource_context.get("current_task"),
            context_variables=list(resource_context.get("context_variables", {}).keys()),
        )

        try:
            # Execute context-aware resource loading activity
            result = await workflow.execute_activity(
                context_aware_resource_activity,
                args=[resource_context],
                start_to_close_timeout=timedelta(seconds=20),
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=1),
                    maximum_interval=timedelta(seconds=4),
                    maximum_attempts=3,
                ),
            )

            workflow.logger.info(
                "Context-aware resource loader completed",
                success=result.get("success"),
                loader_id=result.get("loader_id"),
                resources_found=result.get("resources_found"),
                average_relevance=result.get("average_relevance"),
                loading_time_ms=result.get("loading_time_ms"),
            )

            return result

        except Exception as e:
            workflow.logger.error(
                "Context-aware resource loader failed",
                error=str(e),
                project_id=resource_context.get("project_id"),
                current_task=resource_context.get("current_task"),
            )
            raise


@workflow.defn
class ContextPersistenceWorkflow:
    """
    Context persistence workflow for memory system integration.

    Stores context variables and patterns in the memory system for
    persistent context learning and pattern recognition.
    """

    @workflow.run
    async def run(self, persistence_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute context persistence workflow.

        Args:
            persistence_context: Context persistence parameters and data

        Returns:
            Persistence result with storage information and learning metrics
        """
        workflow.logger.info(
            "Starting context persistence workflow",
            project_id=persistence_context.get("project_id"),
            persona_id=persistence_context.get("persona_id"),
            context_variables=list(persistence_context.get("context_variables", {}).keys()),
            learning_patterns=len(persistence_context.get("learning_patterns", [])),
        )

        try:
            # Execute context persistence activity
            result = await workflow.execute_activity(
                context_persistence_activity,
                args=[persistence_context],
                start_to_close_timeout=timedelta(seconds=25),
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=1),
                    maximum_interval=timedelta(seconds=6),
                    maximum_attempts=3,
                ),
            )

            workflow.logger.info(
                "Context persistence workflow completed",
                success=result.get("success"),
                persistence_id=result.get("persistence_id"),
                context_stored=result.get("context_stored"),
                patterns_learned=result.get("patterns_learned"),
                memory_namespace=result.get("memory_namespace"),
            )

            return result

        except Exception as e:
            workflow.logger.error(
                "Context persistence workflow failed",
                error=str(e),
                project_id=persistence_context.get("project_id"),
                persona_id=persistence_context.get("persona_id"),
            )
            raise


@workflow.defn
class ContextLearningWorkflow:
    """
    Context learning workflow for pattern recognition and improvement.

    Analyzes historical contexts and outcomes to identify patterns
    for improved context-aware resource selection.
    """

    @workflow.run
    async def run(self, learning_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute context learning workflow.

        Args:
            learning_context: Context learning parameters and historical data

        Returns:
            Learning result with identified patterns and confidence metrics
        """
        workflow.logger.info(
            "Starting context learning workflow",
            project_id=learning_context.get("project_id"),
            historical_contexts=len(learning_context.get("historical_contexts", [])),
        )

        try:
            # Execute context learning activity
            result = await workflow.execute_activity(
                context_learning_activity,
                args=[learning_context],
                start_to_close_timeout=timedelta(seconds=45),  # Allow time for pattern analysis
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=2),
                    maximum_interval=timedelta(seconds=8),
                    maximum_attempts=3,
                ),
            )

            workflow.logger.info(
                "Context learning workflow completed",
                success=result.get("success"),
                learning_id=result.get("learning_id"),
                patterns_identified=len(result.get("patterns_identified", [])),
                learning_time_ms=result.get("learning_time_ms"),
            )

            return result

        except Exception as e:
            workflow.logger.error(
                "Context learning workflow failed",
                error=str(e),
                project_id=learning_context.get("project_id"),
            )
            raise


@workflow.defn
class BackwardCompatibilityWorkflow:
    """
    Backward compatibility workflow for existing resource system integration.

    Ensures adaptive resources maintain backward compatibility with
    existing resource system while providing enhanced functionality.
    """

    @workflow.run
    async def run(self, compatibility_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute backward compatibility workflow.

        Args:
            compatibility_context: Compatibility parameters and legacy resource info

        Returns:
            Compatibility result with legacy access and enhancement status
        """
        workflow.logger.info(
            "Starting backward compatibility workflow",
            project_id=compatibility_context.get("project_id"),
            legacy_resource_id=compatibility_context.get("legacy_resource_id"),
            adaptive_features_enabled=compatibility_context.get("adaptive_features_enabled"),
        )

        try:
            # Execute backward compatibility activity
            result = await workflow.execute_activity(
                backward_compatibility_activity,
                args=[compatibility_context],
                start_to_close_timeout=timedelta(seconds=20),
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=1),
                    maximum_interval=timedelta(seconds=4),
                    maximum_attempts=3,
                ),
            )

            workflow.logger.info(
                "Backward compatibility workflow completed",
                success=result.get("success"),
                compatibility_id=result.get("compatibility_id"),
                legacy_resource_accessible=result.get("legacy_resource_accessible"),
                backward_compatible=result.get("backward_compatible"),
                adaptive_enhancements_applied=result.get("adaptive_enhancements_applied"),
            )

            return result

        except Exception as e:
            workflow.logger.error(
                "Backward compatibility workflow failed",
                error=str(e),
                project_id=compatibility_context.get("project_id"),
                legacy_resource_id=compatibility_context.get("legacy_resource_id"),
            )
            raise


@workflow.defn
class CompositeAdaptiveWorkflow:
    """
    Composite adaptive workflow that orchestrates multiple adaptive sub-workflows.

    Coordinates template adaptation, conditional workflows, and resource loading
    for comprehensive adaptive resource management.
    """

    @workflow.run
    async def run(self, composite_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute composite adaptive workflow.

        Args:
            composite_context: Composite adaptive parameters and context

        Returns:
            Composite result with all adaptive workflow results
        """
        workflow.logger.info(
            "Starting composite adaptive workflow",
            project_id=composite_context.get("project_id"),
            adaptive_types=composite_context.get("adaptive_types", []),
        )

        results = {}

        try:
            # Execute adaptive workflows based on requested types
            adaptive_types = composite_context.get("adaptive_types", [])

            if "template_adaptation" in adaptive_types:
                template_future = workflow.execute_child_workflow(
                    DynamicTemplateWorkflow.run,
                    args=[composite_context.get("template_context", {})],
                    id=f"template-{composite_context.get('project_id')}-{workflow.info().workflow_id}",
                )
                results["template_adaptation"] = await template_future

            if "conditional_workflow" in adaptive_types:
                conditional_future = workflow.execute_child_workflow(
                    ConditionalWorkflowEngine.run,
                    args=[composite_context.get("workflow_context", {})],
                    id=f"conditional-{composite_context.get('project_id')}-{workflow.info().workflow_id}",
                )
                results["conditional_workflow"] = await conditional_future

            if "resource_loading" in adaptive_types:
                resource_future = workflow.execute_child_workflow(
                    ContextAwareResourceLoader.run,
                    args=[composite_context.get("resource_context", {})],
                    id=f"resource-{composite_context.get('project_id')}-{workflow.info().workflow_id}",
                )
                results["resource_loading"] = await resource_future

            # Store context and patterns for learning
            if results and composite_context.get("enable_learning", True):
                persistence_context = {
                    "project_id": composite_context.get("project_id"),
                    "persona_id": composite_context.get("persona_id"),
                    "context_variables": composite_context.get("context_variables", {}),
                    "learning_patterns": self._extract_learning_patterns(results),
                }

                persistence_future = workflow.execute_child_workflow(
                    ContextPersistenceWorkflow.run,
                    args=[persistence_context],
                    id=f"persistence-{composite_context.get('project_id')}-{workflow.info().workflow_id}",
                )
                results["context_persistence"] = await persistence_future

            workflow.logger.info(
                "Composite adaptive workflow completed",
                project_id=composite_context.get("project_id"),
                completed_adaptations=list(results.keys()),
                success_count=sum(1 for r in results.values() if r.get("success", False)),
            )

            return {
                "success": True,
                "composite_id": f"adaptive-{workflow.info().workflow_id}",
                "results": results,
                "completed_adaptations": list(results.keys()),
            }

        except Exception as e:
            workflow.logger.error(
                "Composite adaptive workflow failed",
                error=str(e),
                project_id=composite_context.get("project_id"),
            )
            raise

    def _extract_learning_patterns(self, results: Dict[str, Any]) -> List[str]:
        """Extract learning patterns from adaptive workflow results."""
        patterns = []

        # Extract patterns from template adaptation
        if "template_adaptation" in results:
            template_result = results["template_adaptation"]
            if template_result.get("success") and template_result.get("relevance_score", 0) > 0.8:
                patterns.append("high_relevance_template_adaptation")

        # Extract patterns from conditional workflow
        if "conditional_workflow" in results:
            workflow_result = results["conditional_workflow"]
            if workflow_result.get("success") and workflow_result.get("conditions_met", 0) > 0:
                patterns.append("successful_conditional_execution")

        # Extract patterns from resource loading
        if "resource_loading" in results:
            resource_result = results["resource_loading"]
            if resource_result.get("success") and resource_result.get("average_relevance", 0) > 0.85:
                patterns.append("high_relevance_resource_selection")

        return patterns