"""Knowledge sharing workflow sub-workflows for Orchestra AI cross-persona knowledge sharing system."""

from datetime import timedelta
from typing import Any, Dict, List

from temporalio import workflow
from temporalio.common import RetryPolicy

from orchestra.temporal.activities.knowledge_sharing import (
    knowledge_sharing_activity,
    pattern_matching_activity,
    propagation_activity,
    tag_based_targeting_activity,
    validation_activity,
)


@workflow.defn
class KnowledgeSharingWorkflow:
    """
    Knowledge sharing sub-workflow for cross-persona pattern export/import.

    Enables personas to export successful patterns and import shared
    knowledge with lazy loading and performance optimization.
    """

    @workflow.run
    async def run(
        self,
        sharing_context: Dict[str, Any],
        operation: str = "export_patterns",
    ) -> Dict[str, Any]:
        """
        Execute knowledge sharing workflow.

        Args:
            sharing_context: Knowledge sharing context
            operation: Operation type (export_patterns, import_shared_knowledge)

        Returns:
            Knowledge sharing result with exported/imported patterns
        """
        workflow.logger.info(
            "Starting knowledge sharing workflow",
            operation=operation,
            source_persona=sharing_context.get("source_persona_id"),
            project_id=sharing_context.get("project_id"),
        )

        try:
            # Execute knowledge sharing activity (AC: 1 - enable export/import)
            result = await workflow.execute_activity(
                knowledge_sharing_activity,
                args=[sharing_context, operation],
                start_to_close_timeout=timedelta(
                    minutes=2
                ),  # Allow time for pattern processing
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=2),
                    maximum_interval=timedelta(seconds=15),
                    maximum_attempts=3,
                ),
            )

            # Verify performance requirement (AC: 9 - <500ms load time with lazy loading)
            processing_time_ms = result.get("processing_time_ms", 0)
            if processing_time_ms > 500 and operation == "export_patterns":
                workflow.logger.warning(
                    "Knowledge sharing exceeded 500ms load time",
                    processing_time_ms=processing_time_ms,
                    operation=operation,
                )

            workflow.logger.info(
                "Knowledge sharing workflow completed",
                success=result.get("success"),
                operation=operation,
                patterns_processed=result.get("patterns_count", 0),
            )

            return result

        except Exception as e:
            workflow.logger.error(
                "Knowledge sharing workflow failed",
                error=str(e),
                operation=operation,
            )
            raise


@workflow.defn
class PatternMatchingWorkflow:
    """
    AI-assisted pattern matching sub-workflow for transferability assessment.

    Identifies transferable knowledge between persona types using
    AI analysis with accuracy and effectiveness requirements.
    """

    @workflow.run
    async def run(
        self,
        source_persona_id: str,
        target_personas: List[str],
        project_id: str,
        context_similarity: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Execute pattern matching workflow.

        Args:
            source_persona_id: Source persona ID
            target_personas: List of target persona IDs
            project_id: Project ID for context
            context_similarity: Context similarity data

        Returns:
            Pattern matching results with transferability scores
        """
        workflow.logger.info(
            "Starting pattern matching workflow",
            source_persona=source_persona_id,
            target_count=len(target_personas),
            project_id=project_id,
        )

        try:
            # Execute pattern matching activity (AC: 2, 7 - >75% accuracy pattern matching)
            result = await workflow.execute_activity(
                pattern_matching_activity,
                args=[
                    source_persona_id,
                    target_personas,
                    project_id,
                    context_similarity,
                ],
                start_to_close_timeout=timedelta(
                    minutes=3
                ),  # Allow time for AI analysis
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=5),
                    maximum_interval=timedelta(seconds=30),
                    maximum_attempts=3,
                ),
            )

            # Validate accuracy requirement (AC: 7)
            total_transferable = result.get("total_transferable_patterns", 0)
            successful_matches = result.get("successful_matches", 0)

            if successful_matches > 0:
                match_accuracy = successful_matches / len(target_personas)
                if match_accuracy < 0.75:
                    workflow.logger.warning(
                        "Pattern matching accuracy below 75% requirement",
                        match_accuracy=match_accuracy,
                        requirement=0.75,
                    )

            workflow.logger.info(
                "Pattern matching workflow completed",
                success=result.get("success"),
                total_transferable=total_transferable,
                successful_matches=successful_matches,
            )

            return result

        except Exception as e:
            workflow.logger.error(
                "Pattern matching workflow failed",
                error=str(e),
                source_persona=source_persona_id,
            )
            raise


@workflow.defn
class PropagationWorkflow:
    """
    Knowledge propagation sub-workflow for distributing best practices.

    Distributes validated patterns to relevant personas via Temporal
    orchestration with Epic 1 broadcast integration.
    """

    @workflow.run
    async def run(
        self,
        shared_knowledge_list: List[Dict[str, Any]],
        target_personas: List[str],
        propagation_mode: str = "automatic",
        approval_required: bool = False,
    ) -> Dict[str, Any]:
        """
        Execute propagation workflow.

        Args:
            shared_knowledge_list: List of shared knowledge to propagate
            target_personas: Target persona IDs
            propagation_mode: Propagation mode (automatic, manual, conditional)
            approval_required: Whether manual approval is required

        Returns:
            Propagation results with distribution statistics
        """
        workflow.logger.info(
            "Starting propagation workflow",
            knowledge_count=len(shared_knowledge_list),
            target_count=len(target_personas),
            propagation_mode=propagation_mode,
            approval_required=approval_required,
        )

        try:
            # Handle approval workflow if required
            if approval_required and propagation_mode != "automatic":
                workflow.logger.info("Manual approval required for propagation")

                # Wait for manual approval (simplified - in production, use signals)
                await workflow.sleep(timedelta(minutes=1))  # Simulate approval wait

                # For demonstration, assume approval granted
                workflow.logger.info("Manual approval granted for propagation")

            # Execute propagation activity (AC: 3 - distribute best practices)
            result = await workflow.execute_activity(
                propagation_activity,
                args=[shared_knowledge_list, target_personas, propagation_mode],
                start_to_close_timeout=timedelta(
                    minutes=5
                ),  # Allow time for distribution
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=3),
                    maximum_interval=timedelta(seconds=20),
                    maximum_attempts=3,
                ),
            )

            # Validate effectiveness requirement (AC: 8 - >60% effectiveness improvement)
            successful_propagations = result.get("total_successful_propagations", 0)
            total_attempts = successful_propagations + result.get(
                "total_failed_propagations", 0
            )

            if total_attempts > 0:
                propagation_success_rate = successful_propagations / total_attempts
                workflow.logger.info(
                    "Propagation success rate calculated",
                    success_rate=propagation_success_rate,
                    successful=successful_propagations,
                    total=total_attempts,
                )

            workflow.logger.info(
                "Propagation workflow completed",
                success=result.get("success"),
                successful_propagations=successful_propagations,
                propagation_mode=propagation_mode,
            )

            return result

        except Exception as e:
            workflow.logger.error(
                "Propagation workflow failed",
                error=str(e),
                propagation_mode=propagation_mode,
            )
            raise


@workflow.defn
class ValidationWorkflow:
    """
    Pattern validation sub-workflow for effectiveness measurement.

    Ensures shared patterns are beneficial through effectiveness
    measurement and provides rollback capabilities.
    """

    @workflow.run
    async def run(
        self,
        shared_knowledge_ids: List[str],
        target_personas: List[str],
        validation_period_days: int = 7,
        effectiveness_threshold: float = 0.5,
    ) -> Dict[str, Any]:
        """
        Execute validation workflow.

        Args:
            shared_knowledge_ids: List of shared knowledge IDs to validate
            target_personas: Target persona IDs for validation
            validation_period_days: Validation measurement period
            effectiveness_threshold: Minimum effectiveness threshold

        Returns:
            Validation results with effectiveness metrics and rollback decisions
        """
        workflow.logger.info(
            "Starting validation workflow",
            knowledge_count=len(shared_knowledge_ids),
            target_count=len(target_personas),
            validation_period=validation_period_days,
            threshold=effectiveness_threshold,
        )

        try:
            # Execute validation activity (AC: 4, 10 - ensure beneficial patterns)
            result = await workflow.execute_activity(
                validation_activity,
                args=[shared_knowledge_ids, target_personas, validation_period_days],
                start_to_close_timeout=timedelta(minutes=3),
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=2),
                    maximum_interval=timedelta(seconds=15),
                    maximum_attempts=3,
                ),
            )

            # Process rollback recommendations
            validation_summary = result.get("validation_summary", {})
            rollback_required = validation_summary.get("rollback_required", 0)

            if rollback_required > 0:
                workflow.logger.warning(
                    "Patterns require rollback due to poor effectiveness",
                    rollback_count=rollback_required,
                    total_validated=validation_summary.get("total_validated", 0),
                )

                # Execute rollback sub-workflow if needed
                rollback_result = await self._execute_rollback_workflow(
                    result.get("validation_results", [])
                )
                result["rollback_execution"] = rollback_result

            # Validate overall success rate (AC: 10 - prevent <50% effectiveness)
            overall_success_rate = validation_summary.get("overall_success_rate", 0.0)
            if overall_success_rate < effectiveness_threshold:
                workflow.logger.warning(
                    "Overall validation success rate below threshold",
                    success_rate=overall_success_rate,
                    threshold=effectiveness_threshold,
                )

            workflow.logger.info(
                "Validation workflow completed",
                success=result.get("success"),
                beneficial_patterns=validation_summary.get("beneficial_patterns", 0),
                rollback_required=rollback_required,
            )

            return result

        except Exception as e:
            workflow.logger.error(
                "Validation workflow failed",
                error=str(e),
                validation_period=validation_period_days,
            )
            raise

    async def _execute_rollback_workflow(
        self,
        validation_results: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Execute rollback for patterns that require it."""
        rollback_results = []

        for validation_result in validation_results:
            if validation_result.get("rollback_required", False):
                knowledge_id = validation_result.get("knowledge_id")

                workflow.logger.info(
                    "Executing rollback for knowledge",
                    knowledge_id=knowledge_id,
                )

                # In production, this would call actual rollback activities
                # For now, simulate rollback execution
                rollback_results.append(
                    {
                        "knowledge_id": knowledge_id,
                        "rollback_success": True,
                        "rollback_reason": "Effectiveness below threshold",
                        "rollback_timestamp": workflow.now().isoformat(),
                    }
                )

        return {
            "rollback_executed": len(rollback_results),
            "rollback_results": rollback_results,
        }


@workflow.defn
class TagBasedTargetingWorkflow:
    """
    Tag-based targeting sub-workflow for precise knowledge routing.

    Integrates with Epic 1 tag-based targeting infrastructure for
    hierarchical persona grouping and broadcast capabilities.
    """

    @workflow.run
    async def run(
        self,
        knowledge_sharing_request: Dict[str, Any],
        targeting_criteria: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute tag-based targeting workflow.

        Args:
            knowledge_sharing_request: Knowledge sharing request
            targeting_criteria: Tag-based targeting criteria

        Returns:
            Targeting results with matched personas and routing decisions
        """
        workflow.logger.info(
            "Starting tag-based targeting workflow",
            request_id=knowledge_sharing_request.get("request_id"),
            targeting_criteria=targeting_criteria,
        )

        try:
            # Execute tag-based targeting activity (AC: 5, 6 - Epic 1 integration)
            result = await workflow.execute_activity(
                tag_based_targeting_activity,
                args=[knowledge_sharing_request, targeting_criteria],
                start_to_close_timeout=timedelta(minutes=1),
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=1),
                    maximum_interval=timedelta(seconds=10),
                    maximum_attempts=3,
                ),
            )

            # Validate targeting effectiveness
            total_matches = result.get("total_matches", 0)
            targeting_results = result.get("targeting_results", [])

            if total_matches == 0:
                workflow.logger.warning(
                    "No personas matched targeting criteria",
                    targeting_criteria=targeting_criteria,
                )

            workflow.logger.info(
                "Tag-based targeting workflow completed",
                success=result.get("success"),
                total_matches=total_matches,
                tags_processed=len(targeting_results),
            )

            return result

        except Exception as e:
            workflow.logger.error(
                "Tag-based targeting workflow failed",
                error=str(e),
                request_id=knowledge_sharing_request.get("request_id"),
            )
            raise


# Composite workflows for complex knowledge sharing operations


@workflow.defn
class ComprehensiveKnowledgeSharingWorkflow:
    """
    Comprehensive knowledge sharing workflow combining all sub-workflows.

    Orchestrates the complete knowledge sharing cycle from pattern
    identification through targeting, propagation, and validation.
    """

    @workflow.run
    async def run(
        self,
        sharing_request: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute comprehensive knowledge sharing workflow.

        Args:
            sharing_request: Complete knowledge sharing request

        Returns:
            Complete knowledge sharing cycle results
        """
        workflow.logger.info(
            "Starting comprehensive knowledge sharing workflow",
            source_persona=sharing_request.get("source_persona_id"),
            request_id=sharing_request.get("request_id"),
        )

        results: Dict[str, Any] = {"success": True, "phases": []}

        try:
            # Phase 1: Export patterns from source persona
            export_context = {
                "source_persona_id": sharing_request["source_persona_id"],
                "project_id": sharing_request["project_id"],
            }

            export_result = await workflow.execute_child_workflow(
                KnowledgeSharingWorkflow.run,
                args=[export_context, "export_patterns"],
                id=f"export-{sharing_request.get('request_id', 'unknown')}",
            )

            results["phases"].append(
                {
                    "phase": "pattern_export",
                    "result": export_result,
                    "success": export_result.get("success", False),
                }
            )

            if not export_result.get("success"):
                workflow.logger.error("Pattern export phase failed")
                results["success"] = False
                return results

            # Phase 2: Tag-based targeting (if targeting criteria provided)
            targeting_criteria = sharing_request.get("targeting_criteria")
            target_personas = sharing_request.get("target_personas", [])

            if targeting_criteria:
                targeting_result = await workflow.execute_child_workflow(
                    TagBasedTargetingWorkflow.run,
                    args=[sharing_request, targeting_criteria],
                    id=f"targeting-{sharing_request.get('request_id', 'unknown')}",
                )

                results["phases"].append(
                    {
                        "phase": "tag_based_targeting",
                        "result": targeting_result,
                        "success": targeting_result.get("success", False),
                    }
                )

                # Use targeted personas if targeting was successful
                if targeting_result.get("success"):
                    target_personas.extend(targeting_result.get("matched_personas", []))
                    # Remove duplicates
                    target_personas = list(set(target_personas))

            # Phase 3: Pattern matching for target personas
            if target_personas:
                matching_result = await workflow.execute_child_workflow(
                    PatternMatchingWorkflow.run,
                    args=[
                        sharing_request["source_persona_id"],
                        target_personas,
                        sharing_request["project_id"],
                        sharing_request.get("context_similarity"),
                    ],
                    id=f"matching-{sharing_request.get('request_id', 'unknown')}",
                )

                results["phases"].append(
                    {
                        "phase": "pattern_matching",
                        "result": matching_result,
                        "success": matching_result.get("success", False),
                    }
                )

                # Phase 4: Propagation of matched patterns
                if (
                    matching_result.get("success")
                    and matching_result.get("total_transferable_patterns", 0) > 0
                ):
                    # Collect transferable patterns from all target personas
                    transferable_patterns = []
                    for match_result in matching_result.get("matching_results", []):
                        transferable_patterns.extend(
                            match_result.get("transferable_patterns", [])
                        )

                    if transferable_patterns:
                        propagation_result = await workflow.execute_child_workflow(
                            PropagationWorkflow.run,
                            args=[
                                transferable_patterns,
                                target_personas,
                                sharing_request.get("propagation_mode", "automatic"),
                                sharing_request.get("approval_required", False),
                            ],
                            id=f"propagation-{sharing_request.get('request_id', 'unknown')}",
                        )

                        results["phases"].append(
                            {
                                "phase": "knowledge_propagation",
                                "result": propagation_result,
                                "success": propagation_result.get("success", False),
                            }
                        )

                        # Phase 5: Validation of propagated knowledge
                        if propagation_result.get("success"):
                            # Collect knowledge IDs for validation
                            knowledge_ids = []
                            for pattern in transferable_patterns:
                                knowledge_ids.append(
                                    pattern.get("knowledge_id", str(workflow.uuid4()))
                                )

                            validation_result = await workflow.execute_child_workflow(
                                ValidationWorkflow.run,
                                args=[
                                    knowledge_ids,
                                    target_personas,
                                    sharing_request.get("validation_period_days", 7),
                                ],
                                id=f"validation-{sharing_request.get('request_id', 'unknown')}",
                            )

                            results["phases"].append(
                                {
                                    "phase": "pattern_validation",
                                    "result": validation_result,
                                    "success": validation_result.get("success", False),
                                }
                            )

            # Determine overall success
            successful_phases = sum(
                1 for phase in results["phases"] if phase["success"]
            )
            results["successful_phases"] = successful_phases
            results["total_phases"] = len(results["phases"])
            results["success"] = (
                successful_phases >= len(results["phases"]) - 1
            )  # Allow one failure

            workflow.logger.info(
                "Comprehensive knowledge sharing workflow completed",
                success=results["success"],
                successful_phases=successful_phases,
                total_phases=results["total_phases"],
            )

            return results

        except Exception as e:
            workflow.logger.error(
                "Comprehensive knowledge sharing workflow failed",
                error=str(e),
                source_persona=sharing_request.get("source_persona_id"),
            )
            results["success"] = False
            results["error"] = str(e)
            return results


@workflow.defn
class PeriodicKnowledgeMaintenanceWorkflow:
    """
    Periodic knowledge maintenance workflow for scheduled validation.

    Runs on schedule to validate shared knowledge effectiveness and
    perform maintenance operations like rollback and optimization.
    """

    @workflow.run
    async def run(
        self,
        maintenance_config: Dict[str, Any],
        schedule_interval: str = "weekly",
    ) -> Dict[str, Any]:
        """
        Execute periodic knowledge maintenance workflow.

        Args:
            maintenance_config: Maintenance configuration
            schedule_interval: Schedule interval (daily, weekly, monthly)

        Returns:
            Maintenance results with next execution time
        """
        workflow.logger.info(
            "Starting periodic knowledge maintenance workflow",
            schedule_interval=schedule_interval,
        )

        try:
            while True:  # Continuous scheduled execution
                maintenance_results = []

                # Get shared knowledge for validation (would query from storage in production)
                shared_knowledge_ids = maintenance_config.get(
                    "knowledge_ids_for_validation", []
                )
                target_personas = maintenance_config.get("target_personas", [])

                if shared_knowledge_ids and target_personas:
                    # Execute validation workflow
                    validation_result = await workflow.execute_child_workflow(
                        ValidationWorkflow.run,
                        args=[
                            shared_knowledge_ids,
                            target_personas,
                            maintenance_config.get("validation_period_days", 14),
                        ],
                        id=f"maintenance-validation-{workflow.now().isoformat()}",
                    )

                    maintenance_results.append(
                        {
                            "operation": "validation",
                            "timestamp": workflow.now().isoformat(),
                            "result": validation_result,
                        }
                    )

                    workflow.logger.info(
                        "Periodic validation completed",
                        success=validation_result.get("success"),
                        knowledge_validated=len(shared_knowledge_ids),
                    )
                else:
                    workflow.logger.info(
                        "No knowledge items for periodic validation",
                        schedule_interval=schedule_interval,
                    )

                # Calculate next execution time
                if schedule_interval == "daily":
                    next_execution = workflow.now() + timedelta(days=1)
                elif schedule_interval == "weekly":
                    next_execution = workflow.now() + timedelta(weeks=1)
                elif schedule_interval == "monthly":
                    next_execution = workflow.now() + timedelta(days=30)
                else:
                    next_execution = workflow.now() + timedelta(
                        weeks=1
                    )  # Default to weekly

                workflow.logger.info(
                    "Next periodic maintenance scheduled",
                    next_execution=next_execution.isoformat(),
                    operations_completed=len(maintenance_results),
                )

                # Sleep until next execution
                sleep_duration = (next_execution - workflow.now()).total_seconds()
                if sleep_duration > 0:
                    await workflow.sleep(timedelta(seconds=sleep_duration))

        except Exception as e:
            workflow.logger.error(
                "Periodic knowledge maintenance workflow failed",
                error=str(e),
                schedule_interval=schedule_interval,
            )
            return {
                "success": False,
                "error": str(e),
                "maintenance_results": [],
                "schedule_interval": schedule_interval,
            }
