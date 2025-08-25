"""Intelligence workflow sub-workflows for Orchestra AI intelligence infrastructure."""

from datetime import timedelta
from typing import Any, Dict

from temporalio import workflow
from temporalio.common import RetryPolicy

from orchestra.temporal.activities.intelligence import (
    code_analysis_activity,
    health_monitoring_activity,
    intelligence_storage_activity,
    performance_monitoring_activity,
    security_validation_activity,
)


@workflow.defn
class LiveCodeAnalysisWorkflow:
    """
    Live code analysis sub-workflow for real-time code quality assessment.

    Provides real-time code analysis with pattern detection and quality scoring
    meeting performance requirements (<100ms for files under 1000 lines).
    """

    @workflow.run
    async def run(self, analysis_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute live code analysis workflow.

        Args:
            analysis_context: Code analysis parameters and context

        Returns:
            Analysis result with quality metrics and recommendations
        """
        workflow.logger.info(
            "Starting live code analysis workflow",
            project_id=analysis_context.get("project_id"),
            file_path=analysis_context.get("file_path"),
            analysis_types=analysis_context.get("analysis_types", []),
        )

        try:
            # Execute code analysis activity with performance requirements
            result = await workflow.execute_activity(
                code_analysis_activity,
                args=[analysis_context],
                start_to_close_timeout=timedelta(seconds=10),  # Fast timeout for performance
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(milliseconds=500),
                    maximum_interval=timedelta(seconds=2),
                    maximum_attempts=3,
                ),
            )

            workflow.logger.info(
                "Live code analysis workflow completed",
                success=result.get("success"),
                analysis_id=result.get("analysis_id"),
                quality_score=result.get("quality_score"),
                execution_time_ms=result.get("execution_time_ms"),
            )

            return result

        except Exception as e:
            workflow.logger.error(
                "Live code analysis workflow failed",
                error=str(e),
                project_id=analysis_context.get("project_id"),
                file_path=analysis_context.get("file_path"),
            )
            raise


@workflow.defn
class PerformanceMonitoringWorkflow:
    """
    Performance monitoring sub-workflow for execution metric collection.

    Tracks execution metrics and identifies bottlenecks with minimal overhead
    (<5% of monitored operations).
    """

    @workflow.run
    async def run(self, monitoring_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute performance monitoring workflow.

        Args:
            monitoring_context: Performance monitoring parameters and context

        Returns:
            Monitoring result with performance metrics and bottleneck analysis
        """
        workflow.logger.info(
            "Starting performance monitoring workflow",
            project_id=monitoring_context.get("project_id"),
            operation_name=monitoring_context.get("operation_name"),
            metric_types=monitoring_context.get("metric_types", []),
        )

        try:
            # Execute performance monitoring activity with overhead limits
            result = await workflow.execute_activity(
                performance_monitoring_activity,
                args=[monitoring_context],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=1),
                    maximum_interval=timedelta(seconds=5),
                    maximum_attempts=3,
                ),
            )

            workflow.logger.info(
                "Performance monitoring workflow completed",
                success=result.get("success"),
                monitoring_id=result.get("monitoring_id"),
                metrics_count=len(result.get("metrics", [])),
                overhead_percentage=result.get("average_overhead_percentage"),
            )

            return result

        except Exception as e:
            workflow.logger.error(
                "Performance monitoring workflow failed",
                error=str(e),
                project_id=monitoring_context.get("project_id"),
                operation_name=monitoring_context.get("operation_name"),
            )
            raise


@workflow.defn
class SecurityValidationWorkflow:
    """
    Security validation sub-workflow for vulnerability scanning.

    Scans for OWASP Top 10 vulnerabilities and project-specific compliance rules
    with comprehensive security analysis.
    """

    @workflow.run
    async def run(self, validation_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute security validation workflow.

        Args:
            validation_context: Security validation parameters and context

        Returns:
            Validation result with vulnerability findings and compliance status
        """
        workflow.logger.info(
            "Starting security validation workflow",
            project_id=validation_context.get("project_id"),
            file_path=validation_context.get("file_path"),
            compliance_rules=validation_context.get("compliance_rules", []),
        )

        try:
            # Execute security validation activity with OWASP coverage
            result = await workflow.execute_activity(
                security_validation_activity,
                args=[validation_context],
                start_to_close_timeout=timedelta(seconds=60),  # Allow time for thorough scanning
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=2),
                    maximum_interval=timedelta(seconds=10),
                    maximum_attempts=3,
                ),
            )

            workflow.logger.info(
                "Security validation workflow completed",
                success=result.get("success"),
                validation_id=result.get("validation_id"),
                vulnerabilities_found=len(result.get("vulnerabilities", [])),
                compliance_status=result.get("compliance_status"),
                scan_duration_ms=result.get("scan_duration_ms"),
            )

            return result

        except Exception as e:
            workflow.logger.error(
                "Security validation workflow failed",
                error=str(e),
                project_id=validation_context.get("project_id"),
                file_path=validation_context.get("file_path"),
            )
            raise


@workflow.defn
class IntelligenceHealthMonitoringWorkflow:
    """
    Intelligence health monitoring sub-workflow for service status tracking.

    Provides real-time status reporting and alerting for all intelligence
    services with health endpoint monitoring.
    """

    @workflow.run
    async def run(self, health_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute intelligence health monitoring workflow.

        Args:
            health_context: Health monitoring parameters and context

        Returns:
            Health status result with service availability and performance metrics
        """
        workflow.logger.info(
            "Starting intelligence health monitoring workflow",
            services=health_context.get("services", []),
        )

        try:
            # Execute health monitoring activity with real-time status
            result = await workflow.execute_activity(
                health_monitoring_activity,
                args=[health_context],
                start_to_close_timeout=timedelta(seconds=15),
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(milliseconds=500),
                    maximum_interval=timedelta(seconds=3),
                    maximum_attempts=2,  # Fewer retries for health checks
                ),
            )

            workflow.logger.info(
                "Intelligence health monitoring workflow completed",
                success=result.get("success"),
                overall_health=result.get("overall_health"),
                healthy_services=sum(
                    1
                    for status in result.get("health_status", {}).values()
                    if status.get("is_healthy", False)
                ),
                total_services=len(result.get("health_status", {})),
            )

            return result

        except Exception as e:
            workflow.logger.error(
                "Intelligence health monitoring workflow failed",
                error=str(e),
                services=health_context.get("services", []),
            )
            raise


@workflow.defn
class IntelligenceDataStorageWorkflow:
    """
    Intelligence data storage sub-workflow for project-namespaced data persistence.

    Stores intelligence data with project namespacing (orchestra_intelligence_{project_id})
    in Qdrant collections and PostgreSQL metadata tables.
    """

    @workflow.run
    async def run(self, storage_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute intelligence data storage workflow.

        Args:
            storage_context: Storage parameters and intelligence data

        Returns:
            Storage result with namespace information and stored item count
        """
        workflow.logger.info(
            "Starting intelligence data storage workflow",
            project_id=storage_context.get("project_id"),
            intelligence_type=storage_context.get("intelligence_data", {}).get("type"),
        )

        try:
            # Execute intelligence storage activity with project namespacing
            result = await workflow.execute_activity(
                intelligence_storage_activity,
                args=[storage_context],
                start_to_close_timeout=timedelta(seconds=45),
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=1),
                    maximum_interval=timedelta(seconds=8),
                    maximum_attempts=3,
                ),
            )

            workflow.logger.info(
                "Intelligence data storage workflow completed",
                success=result.get("success"),
                storage_id=result.get("storage_id"),
                namespace=result.get("namespace"),
                stored_items=result.get("stored_items"),
            )

            return result

        except Exception as e:
            workflow.logger.error(
                "Intelligence data storage workflow failed",
                error=str(e),
                project_id=storage_context.get("project_id"),
            )
            raise


@workflow.defn
class CompositeIntelligenceWorkflow:
    """
    Composite intelligence workflow that orchestrates multiple intelligence sub-workflows.

    Coordinates code analysis, performance monitoring, and security validation
    for comprehensive project intelligence gathering.
    """

    @workflow.run
    async def run(self, composite_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute composite intelligence workflow.

        Args:
            composite_context: Composite intelligence parameters and context

        Returns:
            Composite result with all intelligence analysis results
        """
        workflow.logger.info(
            "Starting composite intelligence workflow",
            project_id=composite_context.get("project_id"),
            intelligence_types=composite_context.get("intelligence_types", []),
        )

        results = {}
        
        try:
            # Execute intelligence workflows in parallel for efficiency
            intelligence_types = composite_context.get("intelligence_types", [])
            
            if "code_analysis" in intelligence_types:
                code_analysis_future = workflow.execute_child_workflow(
                    LiveCodeAnalysisWorkflow.run,
                    args=[composite_context.get("code_analysis_context", {})],
                    id=f"code-analysis-{composite_context.get('project_id')}-{workflow.info().workflow_id}",
                )
                results["code_analysis"] = await code_analysis_future
            
            if "performance_monitoring" in intelligence_types:
                performance_future = workflow.execute_child_workflow(
                    PerformanceMonitoringWorkflow.run,
                    args=[composite_context.get("performance_context", {})],
                    id=f"performance-{composite_context.get('project_id')}-{workflow.info().workflow_id}",
                )
                results["performance_monitoring"] = await performance_future
            
            if "security_validation" in intelligence_types:
                security_future = workflow.execute_child_workflow(
                    SecurityValidationWorkflow.run,
                    args=[composite_context.get("security_context", {})],
                    id=f"security-{composite_context.get('project_id')}-{workflow.info().workflow_id}",
                )
                results["security_validation"] = await security_future

            # Store composite intelligence data
            if results:
                storage_context = {
                    "project_id": composite_context.get("project_id"),
                    "intelligence_data": {
                        "type": "composite",
                        "results": results,
                    },
                }
                
                storage_result = await workflow.execute_child_workflow(
                    IntelligenceDataStorageWorkflow.run,
                    args=[storage_context],
                    id=f"storage-{composite_context.get('project_id')}-{workflow.info().workflow_id}",
                )
                results["storage"] = storage_result

            workflow.logger.info(
                "Composite intelligence workflow completed",
                project_id=composite_context.get("project_id"),
                completed_analyses=list(results.keys()),
                success_count=sum(1 for r in results.values() if r.get("success", False)),
            )

            return {
                "success": True,
                "composite_id": f"composite-{workflow.info().workflow_id}",
                "results": results,
                "completed_analyses": list(results.keys()),
            }

        except Exception as e:
            workflow.logger.error(
                "Composite intelligence workflow failed",
                error=str(e),
                project_id=composite_context.get("project_id"),
            )
            raise