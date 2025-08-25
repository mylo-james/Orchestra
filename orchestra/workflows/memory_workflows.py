"""Memory workflow sub-workflows for Orchestra AI memory infrastructure."""

from datetime import timedelta
from typing import Any, Dict

from temporalio import workflow
from temporalio.common import RetryPolicy

from orchestra.workflows.memory_activities import (
    memory_management_activity,
    memory_retrieval_activity,
    memory_upsert_activity,
)


@workflow.defn
class MemoryUpsertWorkflow:
    """
    Memory upsert sub-workflow for context capture and pattern storage.

    Captures context and patterns from persona executions with
    relevance scoring and namespace isolation.
    """

    @workflow.run
    async def run(
        self,
        execution_context: Dict[str, Any],
        patterns: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute memory upsert workflow.

        Args:
            execution_context: Persona execution context
            patterns: Extracted patterns and context data

        Returns:
            Upsert result with success status and memory ID
        """
        workflow.logger.info(
            "Starting memory upsert workflow",
            project_id=execution_context.get("project_id"),
            persona_id=execution_context.get("persona_id"),
        )

        try:
            # Execute memory upsert activity
            result = await workflow.execute_activity(
                memory_upsert_activity,
                args=[execution_context, patterns],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=1),
                    maximum_interval=timedelta(seconds=10),
                    maximum_attempts=3,
                ),
            )

            workflow.logger.info(
                "Memory upsert workflow completed",
                success=result.get("success"),
                memory_id=result.get("memory_id"),
                relevance_score=result.get("relevance_score"),
            )

            return result

        except Exception as e:
            workflow.logger.error(
                "Memory upsert workflow failed",
                error=str(e),
                project_id=execution_context.get("project_id"),
            )
            raise


@workflow.defn
class MemoryRetrievalWorkflow:
    """
    Memory retrieval sub-workflow for context-aware memory search.

    Provides semantic similarity search with performance requirements
    and relevance-based filtering.
    """

    @workflow.run
    async def run(self, query_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute memory retrieval workflow.

        Args:
            query_context: Query parameters and context

        Returns:
            Retrieval result with memories and performance metrics
        """
        workflow.logger.info(
            "Starting memory retrieval workflow",
            project_id=query_context.get("project_id"),
            persona_id=query_context.get("persona_id"),
        )

        start_time = workflow.now()

        try:
            # Execute memory retrieval activity
            result = await workflow.execute_activity(
                memory_retrieval_activity,
                args=[query_context],
                start_to_close_timeout=timedelta(
                    milliseconds=200
                ),  # AC: 8 - <200ms response time
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(milliseconds=50),
                    maximum_interval=timedelta(milliseconds=100),
                    maximum_attempts=2,
                ),
            )

            end_time = workflow.now()
            total_time_ms = (end_time - start_time).total_seconds() * 1000

            # Add workflow timing to result
            result["workflow_time_ms"] = total_time_ms
            result["total_time_ms"] = total_time_ms + result.get("retrieval_time_ms", 0)

            workflow.logger.info(
                "Memory retrieval workflow completed",
                success=result.get("success"),
                memories_count=len(result.get("memories", [])),
                total_time_ms=result["total_time_ms"],
            )

            # Verify performance requirement (AC: 8)
            if result["total_time_ms"] > 200:
                workflow.logger.warning(
                    "Memory retrieval exceeded 200ms requirement",
                    total_time_ms=result["total_time_ms"],
                )

            return result

        except Exception as e:
            workflow.logger.error(
                "Memory retrieval workflow failed",
                error=str(e),
                project_id=query_context.get("project_id"),
            )
            raise


@workflow.defn
class MemoryManagementWorkflow:
    """
    Memory management sub-workflow for retention policy enforcement.

    Handles retention policies, archival, and memory footprint management
    with scheduled execution capabilities.
    """

    @workflow.run
    async def run(self, management_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute memory management workflow.

        Args:
            management_context: Management operation parameters

        Returns:
            Management result with cleanup and archival statistics
        """
        workflow.logger.info(
            "Starting memory management workflow",
            project_id=management_context.get("project_id"),
            operation=management_context.get("operation"),
        )

        try:
            # Execute memory management activity
            result = await workflow.execute_activity(
                memory_management_activity,
                args=[management_context],
                start_to_close_timeout=timedelta(
                    minutes=5
                ),  # Longer timeout for cleanup operations
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=2),
                    maximum_interval=timedelta(seconds=30),
                    maximum_attempts=3,
                ),
            )

            workflow.logger.info(
                "Memory management workflow completed",
                success=result.get("success"),
                operation=management_context.get("operation"),
                archived_count=result.get("archived_count", 0),
                deleted_count=result.get("deleted_count", 0),
            )

            # Schedule next execution if this is a scheduled operation
            if management_context.get("schedule") and result.get("success"):
                await self._schedule_next_execution(management_context, result)

            return result

        except Exception as e:
            workflow.logger.error(
                "Memory management workflow failed",
                error=str(e),
                project_id=management_context.get("project_id"),
            )
            raise

    async def _schedule_next_execution(
        self,
        management_context: Dict[str, Any],
        current_result: Dict[str, Any],
    ) -> None:
        """Schedule next execution of memory management workflow."""
        schedule = management_context.get("schedule", "daily")

        if schedule == "daily":
            next_execution = workflow.now() + timedelta(days=1)
        elif schedule == "weekly":
            next_execution = workflow.now() + timedelta(weeks=1)
        else:
            next_execution = workflow.now() + timedelta(days=1)  # Default to daily

        # Sleep until next execution time
        sleep_duration = (next_execution - workflow.now()).total_seconds()
        if sleep_duration > 0:
            await workflow.sleep(timedelta(seconds=sleep_duration))

        # Execute next scheduled run
        next_context = management_context.copy()
        next_context["scheduled_execution"] = True

        await self.run(next_context)


# Composite workflows for complex memory operations


@workflow.defn
class MemoryLearningIntegrationWorkflow:
    """
    Integration workflow between memory and learning systems.

    Coordinates memory storage of learning outcomes and retrieval
    of relevant patterns for learning enhancement.
    """

    @workflow.run
    async def run(
        self,
        learning_outcome: Dict[str, Any],
        integration_mode: str = "bidirectional",
    ) -> Dict[str, Any]:
        """
        Execute memory-learning integration workflow.

        Args:
            learning_outcome: Learning outcome data to store
            integration_mode: Integration mode (store_only, retrieve_only, bidirectional)

        Returns:
            Integration result with stored and retrieved data
        """
        workflow.logger.info(
            "Starting memory-learning integration workflow",
            outcome_id=learning_outcome.get("outcome_id"),
            integration_mode=integration_mode,
        )

        results: Dict[str, Any] = {"success": True, "operations": []}

        try:
            # Store learning outcome as memory if requested
            if integration_mode in ["store_only", "bidirectional"]:
                memory_context = {
                    "persona_id": learning_outcome.get("persona_id"),
                    "project_id": learning_outcome.get("project_id"),
                    "session_id": learning_outcome.get(
                        "session_id", "learning-integration"
                    ),
                    "command": "learning_outcome_storage",
                    "result": learning_outcome,
                    "timestamp": workflow.now(),
                }

                patterns = {
                    "success_patterns": learning_outcome.get("patterns_identified", []),
                    "context_data": {
                        "domain": "learning",
                        "outcome_type": learning_outcome.get(
                            "classification", "unknown"
                        ),
                        "effectiveness": learning_outcome.get(
                            "effectiveness_score", 0.0
                        ),
                    },
                }

                store_result = await workflow.execute_child_workflow(
                    MemoryUpsertWorkflow.run,
                    args=[memory_context, patterns],
                    id=f"memory-store-{learning_outcome.get('outcome_id')}",
                )

                results["operations"].append(
                    {
                        "operation": "store_learning_outcome",
                        "result": store_result,
                    }
                )

            # Retrieve related memories if requested
            if integration_mode in ["retrieve_only", "bidirectional"]:
                query_context = {
                    "project_id": learning_outcome.get("project_id"),
                    "persona_id": learning_outcome.get("persona_id"),
                    "query_text": f"learning patterns {learning_outcome.get('domain', '')}",
                    "max_results": 5,
                    "min_relevance_score": 0.7,
                }

                retrieve_result = await workflow.execute_child_workflow(
                    MemoryRetrievalWorkflow.run,
                    query_context,
                    id=f"memory-retrieve-{learning_outcome.get('outcome_id')}",
                )

                results["operations"].append(
                    {
                        "operation": "retrieve_related_memories",
                        "result": retrieve_result,
                    }
                )

            workflow.logger.info(
                "Memory-learning integration workflow completed",
                operations_count=len(results["operations"]),
            )

            return results

        except Exception as e:
            workflow.logger.error(
                "Memory-learning integration workflow failed",
                error=str(e),
            )
            results["success"] = False
            results["error"] = str(e)
            return results


@workflow.defn
class MemoryKnowledgeSharingWorkflow:
    """
    Integration workflow between memory and knowledge sharing systems.

    Provides memory patterns for cross-persona knowledge sharing
    and stores shared knowledge in memory for future retrieval.
    """

    @workflow.run
    async def run(
        self,
        sharing_context: Dict[str, Any],
        operation: str = "export_patterns",
    ) -> Dict[str, Any]:
        """
        Execute memory-knowledge sharing integration workflow.

        Args:
            sharing_context: Knowledge sharing context
            operation: Operation type (export_patterns, import_shared_knowledge)

        Returns:
            Integration result with shared patterns or imported knowledge
        """
        workflow.logger.info(
            "Starting memory-knowledge sharing workflow",
            operation=operation,
            project_id=sharing_context.get("project_id"),
        )

        try:
            if operation == "export_patterns":
                # Retrieve shareable patterns from memory
                query_context = {
                    "project_id": sharing_context.get("project_id"),
                    "persona_id": sharing_context.get("source_persona_id"),
                    "query_text": "successful patterns high effectiveness",
                    "max_results": 20,
                    "min_relevance_score": 0.8,
                }

                retrieve_result = await workflow.execute_child_workflow(
                    MemoryRetrievalWorkflow.run,
                    query_context,
                    id=f"export-patterns-{sharing_context.get('source_persona_id')}",
                )

                # Filter patterns for sharing based on effectiveness
                shareable_patterns = []
                for memory in retrieve_result.get("memories", []):
                    if memory.get("effectiveness_score", 0) > 0.75:
                        shareable_patterns.append(
                            {
                                "pattern_id": memory.get("memory_id"),
                                "content": memory.get("content"),
                                "effectiveness_score": memory.get(
                                    "effectiveness_score"
                                ),
                                "transferability_metadata": memory.get("metadata", {}),
                            }
                        )

                return {
                    "success": True,
                    "operation": "export_patterns",
                    "shareable_patterns": shareable_patterns,
                    "patterns_count": len(shareable_patterns),
                }

            elif operation == "import_shared_knowledge":
                # Store shared knowledge in memory for future retrieval
                shared_knowledge = sharing_context.get("shared_knowledge", [])
                import_results = []

                for knowledge in shared_knowledge:
                    memory_context = {
                        "persona_id": sharing_context.get("target_persona_id"),
                        "project_id": sharing_context.get("project_id"),
                        "session_id": f"knowledge-import-{knowledge.get('knowledge_id')}",
                        "command": "import_shared_knowledge",
                        "result": {"success": True, "imported_knowledge": knowledge},
                        "timestamp": workflow.now(),
                    }

                    patterns = {
                        "success_patterns": ["shared_knowledge_import"],
                        "context_data": {
                            "domain": "knowledge_sharing",
                            "source_persona": knowledge.get("source_persona_id"),
                            "knowledge_type": knowledge.get("knowledge_type"),
                        },
                    }

                    import_result = await workflow.execute_child_workflow(
                        MemoryUpsertWorkflow.run,
                        args=[memory_context, patterns],
                        id=f"import-knowledge-{knowledge.get('knowledge_id')}",
                    )

                    import_results.append(import_result)

                return {
                    "success": True,
                    "operation": "import_shared_knowledge",
                    "import_results": import_results,
                    "imported_count": len(import_results),
                }

            else:
                raise ValueError(f"Unknown operation: {operation}")

        except Exception as e:
            workflow.logger.error(
                "Memory-knowledge sharing workflow failed",
                error=str(e),
                operation=operation,
            )
            return {
                "success": False,
                "error": str(e),
                "operation": operation,
            }


# Scheduled memory maintenance workflows


@workflow.defn
class ScheduledMemoryMaintenanceWorkflow:
    """
    Scheduled workflow for automated memory maintenance.

    Runs retention policy enforcement, cleanup, and optimization
    on a regular schedule to maintain system performance.
    """

    @workflow.run
    async def run(
        self,
        maintenance_config: Dict[str, Any],
        schedule_interval: str = "daily",
    ) -> Dict[str, Any]:
        """
        Execute scheduled memory maintenance workflow.

        Args:
            maintenance_config: Maintenance configuration
            schedule_interval: Schedule interval (daily, weekly, monthly)

        Returns:
            Maintenance results and next execution time
        """
        workflow.logger.info(
            "Starting scheduled memory maintenance workflow",
            schedule_interval=schedule_interval,
        )

        maintenance_results = []

        try:
            while True:  # Continuous scheduled execution
                # Execute retention policy enforcement
                retention_context = {
                    "project_id": maintenance_config.get("project_id", "all"),
                    "operation": "enforce_retention",
                    "retention_days": maintenance_config.get("retention_days", 90),
                    "scheduled": True,
                }

                retention_result = await workflow.execute_child_workflow(
                    MemoryManagementWorkflow.run,
                    retention_context,
                    id=f"retention-{workflow.now().isoformat()}",
                )

                maintenance_results.append(
                    {
                        "operation": "retention_enforcement",
                        "timestamp": workflow.now().isoformat(),
                        "result": retention_result,
                    }
                )

                # Execute memory cleanup if needed
                cleanup_context = {
                    "project_id": maintenance_config.get("project_id", "all"),
                    "operation": "check_memory_usage",
                    "max_memory_gb": maintenance_config.get("max_memory_gb", 4.0),
                    "scheduled": True,
                }

                cleanup_result = await workflow.execute_child_workflow(
                    MemoryManagementWorkflow.run,
                    cleanup_context,
                    id=f"cleanup-{workflow.now().isoformat()}",
                )

                maintenance_results.append(
                    {
                        "operation": "memory_cleanup",
                        "timestamp": workflow.now().isoformat(),
                        "result": cleanup_result,
                    }
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
                        days=1
                    )  # Default to daily

                workflow.logger.info(
                    "Memory maintenance cycle completed",
                    next_execution=next_execution.isoformat(),
                    operations_completed=len(maintenance_results),
                )

                # Sleep until next execution
                sleep_duration = (next_execution - workflow.now()).total_seconds()
                if sleep_duration > 0:
                    await workflow.sleep(timedelta(seconds=sleep_duration))

        except Exception as e:
            workflow.logger.error(
                "Scheduled memory maintenance workflow failed",
                error=str(e),
            )
            return {
                "success": False,
                "error": str(e),
                "maintenance_results": maintenance_results,
            }
