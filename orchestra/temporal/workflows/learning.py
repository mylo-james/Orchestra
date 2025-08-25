"""Learning workflow sub-workflows for Orchestra AI adaptive learning system."""

from datetime import timedelta
from typing import Any, Dict, List

from temporalio import workflow
from temporalio.common import RetryPolicy

from orchestra.temporal.activities.learning import (
    ai_analysis_activity,
    confidence_scoring_activity,
    learning_adaptation_activity,
    outcome_tracking_activity,
    performance_metrics_activity,
)


@workflow.defn
class OutcomeTrackingWorkflow:
    """
    Outcome tracking sub-workflow for persona interaction outcomes.

    Captures success/failure events with security integration and
    audit logging for learning effectiveness measurement.
    """

    @workflow.run
    async def run(
        self,
        persona_execution_data: Dict[str, Any],
        outcome_classification: str = None,
    ) -> Dict[str, Any]:
        """
        Execute outcome tracking workflow.

        Args:
            persona_execution_data: Data from persona execution
            outcome_classification: Manual classification override

        Returns:
            Outcome tracking result with event ID and security validation
        """
        workflow.logger.info(
            "Starting outcome tracking workflow",
            persona_id=persona_execution_data.get("persona_id"),
            command=persona_execution_data.get("command"),
        )

        try:
            # Execute outcome tracking activity (AC: 1 - capture outcomes)
            result = await workflow.execute_activity(
                outcome_tracking_activity,
                args=[persona_execution_data, outcome_classification],
                start_to_close_timeout=timedelta(seconds=15),
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=1),
                    maximum_interval=timedelta(seconds=5),
                    maximum_attempts=3,
                ),
            )

            workflow.logger.info(
                "Outcome tracking workflow completed",
                success=result.get("success"),
                outcome_id=result.get("outcome_id"),
                classification=result.get("classification"),
            )

            return result

        except Exception as e:
            workflow.logger.error(
                "Outcome tracking workflow failed",
                error=str(e),
                persona_id=persona_execution_data.get("persona_id"),
            )
            raise


@workflow.defn
class AIAnalysisWorkflow:
    """
    AI-assisted analysis sub-workflow using OpenAI integration.

    Processes outcome patterns and generates improvement suggestions
    with circuit breaker protection and accuracy validation.
    """

    @workflow.run
    async def run(
        self,
        outcome_events: List[Dict[str, Any]],
        analysis_context: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Execute AI analysis workflow.

        Args:
            outcome_events: List of outcome events to analyze
            analysis_context: Additional context for analysis

        Returns:
            AI analysis result with patterns and recommendations
        """
        workflow.logger.info(
            "Starting AI analysis workflow",
            outcome_events_count=len(outcome_events),
            context_provided=bool(analysis_context),
        )

        try:
            # Execute AI analysis activity (AC: 2, 7 - AI analysis with >85% accuracy)
            result = await workflow.execute_activity(
                ai_analysis_activity,
                args=[outcome_events, analysis_context],
                start_to_close_timeout=timedelta(
                    minutes=2
                ),  # Allow time for OpenAI API
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=5),
                    maximum_interval=timedelta(seconds=30),
                    maximum_attempts=3,
                ),
            )

            # Validate accuracy requirement (AC: 7)
            accuracy_score = result.get("confidence_score", 0.0)
            if accuracy_score < 0.85:
                workflow.logger.warning(
                    "AI analysis accuracy below 85% requirement",
                    accuracy_score=accuracy_score,
                    requirement=0.85,
                )

            workflow.logger.info(
                "AI analysis workflow completed",
                success=result.get("success"),
                patterns_count=len(result.get("patterns", [])),
                accuracy_score=accuracy_score,
            )

            return result

        except Exception as e:
            workflow.logger.error(
                "AI analysis workflow failed",
                error=str(e),
                outcome_events_count=len(outcome_events),
            )
            raise


@workflow.defn
class LearningAdaptationWorkflow:
    """
    Learning adaptation sub-workflow for applying AI recommendations.

    Applies behavior modifications with rollback support and
    performance monitoring to maintain system constraints.
    """

    @workflow.run
    async def run(
        self,
        ai_recommendations: List[Dict[str, Any]],
        persona_context: Dict[str, Any],
        confidence_threshold: float = 0.7,
    ) -> Dict[str, Any]:
        """
        Execute learning adaptation workflow.

        Args:
            ai_recommendations: AI-generated improvement recommendations
            persona_context: Context about target persona
            confidence_threshold: Minimum confidence for application

        Returns:
            Adaptation result with applied rules and rollback info
        """
        workflow.logger.info(
            "Starting learning adaptation workflow",
            persona_id=persona_context.get("persona_id"),
            recommendations_count=len(ai_recommendations),
            confidence_threshold=confidence_threshold,
        )

        try:
            # Step 1: Calculate confidence scores (AC: 5 - confidence scoring)
            confidence_result = await workflow.execute_activity(
                confidence_scoring_activity,
                args=[ai_recommendations, persona_context],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=2),
                    maximum_interval=timedelta(seconds=10),
                    maximum_attempts=3,
                ),
            )

            if not confidence_result.get("success"):
                workflow.logger.error(
                    "Confidence scoring failed",
                    error=confidence_result.get("error"),
                )
                return {
                    "success": False,
                    "error": "Confidence scoring failed",
                    "step_failed": "confidence_scoring",
                }

            # Filter recommendations by confidence threshold
            high_confidence_recommendations = []
            for i, recommendation in enumerate(ai_recommendations):
                confidence_scores = confidence_result.get("confidence_scores", [])
                if i < len(confidence_scores):
                    confidence_score = confidence_scores[i]
                    if confidence_score.get("threshold_met", False):
                        high_confidence_recommendations.append(recommendation)

            workflow.logger.info(
                "Filtered recommendations by confidence",
                original_count=len(ai_recommendations),
                high_confidence_count=len(high_confidence_recommendations),
                threshold=confidence_threshold,
            )

            # Step 2: Apply adaptations (AC: 3, 8, 9 - apply with >70% improvement, maintain <500ms)
            if high_confidence_recommendations:
                adaptation_result = await workflow.execute_activity(
                    learning_adaptation_activity,
                    args=[high_confidence_recommendations, persona_context],
                    start_to_close_timeout=timedelta(minutes=1),
                    retry_policy=RetryPolicy(
                        initial_interval=timedelta(seconds=2),
                        maximum_interval=timedelta(seconds=15),
                        maximum_attempts=2,  # Limited retries for adaptation
                    ),
                )

                # Check for circuit breaker triggers (AC: 10)
                success_rate = adaptation_result.get("success_rate", 0.0)
                if success_rate < 0.5:  # Less than 50% success triggers concern
                    workflow.logger.warning(
                        "Low adaptation success rate detected",
                        success_rate=success_rate,
                        threshold=0.5,
                    )

                combined_result = {
                    "success": adaptation_result.get("success", False),
                    "confidence_scoring": confidence_result,
                    "adaptation_results": adaptation_result,
                    "recommendations_processed": len(ai_recommendations),
                    "high_confidence_count": len(high_confidence_recommendations),
                    "adaptations_applied": adaptation_result.get(
                        "successful_applications", 0
                    ),
                }

            else:
                # No high-confidence recommendations
                combined_result = {
                    "success": True,
                    "confidence_scoring": confidence_result,
                    "adaptation_results": {
                        "applied_adaptations": [],
                        "failed_adaptations": [],
                        "success_rate": 0.0,
                        "message": "No recommendations met confidence threshold",
                    },
                    "recommendations_processed": len(ai_recommendations),
                    "high_confidence_count": 0,
                    "adaptations_applied": 0,
                }

            workflow.logger.info(
                "Learning adaptation workflow completed",
                success=combined_result.get("success"),
                adaptations_applied=combined_result.get("adaptations_applied"),
                high_confidence_count=combined_result.get("high_confidence_count"),
            )

            return combined_result

        except Exception as e:
            workflow.logger.error(
                "Learning adaptation workflow failed",
                error=str(e),
                persona_id=persona_context.get("persona_id"),
            )
            raise


@workflow.defn
class PerformanceMetricsWorkflow:
    """
    Performance metrics sub-workflow for learning effectiveness tracking.

    Measures persona performance trends and effectiveness of learning
    adaptations over configurable time periods.
    """

    @workflow.run
    async def run(
        self,
        persona_id: str,
        project_id: str,
        measurement_period_days: int = 14,
    ) -> Dict[str, Any]:
        """
        Execute performance metrics workflow.

        Args:
            persona_id: ID of persona to measure
            project_id: Project ID for context
            measurement_period_days: Period to measure over

        Returns:
            Performance metrics with trends and effectiveness analysis
        """
        workflow.logger.info(
            "Starting performance metrics workflow",
            persona_id=persona_id,
            project_id=project_id,
            measurement_period_days=measurement_period_days,
        )

        try:
            # Execute performance metrics activity (AC: 4 - track effectiveness over time)
            result = await workflow.execute_activity(
                performance_metrics_activity,
                args=[persona_id, project_id, measurement_period_days],
                start_to_close_timeout=timedelta(minutes=1),
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=2),
                    maximum_interval=timedelta(seconds=15),
                    maximum_attempts=3,
                ),
            )

            workflow.logger.info(
                "Performance metrics workflow completed",
                success=result.get("success"),
                metrics_count=result.get("metrics_count"),
                overall_effectiveness=result.get("overall_effectiveness"),
            )

            return result

        except Exception as e:
            workflow.logger.error(
                "Performance metrics workflow failed",
                error=str(e),
                persona_id=persona_id,
            )
            raise


# Composite workflows for complex learning operations


@workflow.defn
class ComprehensiveLearningWorkflow:
    """
    Comprehensive learning workflow combining all learning sub-workflows.

    Orchestrates the complete learning cycle from outcome tracking
    through AI analysis, adaptation, and performance measurement.
    """

    @workflow.run
    async def run(
        self,
        persona_execution_data: Dict[str, Any],
        learning_context: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Execute comprehensive learning workflow.

        Args:
            persona_execution_data: Data from persona execution
            learning_context: Additional learning context

        Returns:
            Complete learning cycle results
        """
        workflow.logger.info(
            "Starting comprehensive learning workflow",
            persona_id=persona_execution_data.get("persona_id"),
            has_context=bool(learning_context),
        )

        results: Dict[str, Any] = {"success": True, "phases": []}

        try:
            # Phase 1: Track outcome
            outcome_result = await workflow.execute_child_workflow(
                OutcomeTrackingWorkflow.run,
                args=[persona_execution_data],
                id=f"outcome-{persona_execution_data.get('session_id', 'unknown')}",
            )

            results["phases"].append(
                {
                    "phase": "outcome_tracking",
                    "result": outcome_result,
                    "success": outcome_result.get("success", False),
                }
            )

            if not outcome_result.get("success"):
                workflow.logger.error("Outcome tracking phase failed")
                results["success"] = False
                return results

            # Phase 2: AI analysis (if we have multiple outcomes to analyze)
            # For now, use single outcome for analysis
            outcome_events = [
                {
                    "outcome_id": outcome_result.get("outcome_id"),
                    "persona_id": persona_execution_data.get("persona_id"),
                    "project_id": persona_execution_data.get("project_id"),
                    "session_id": persona_execution_data.get("session_id"),
                    "command": persona_execution_data.get("command"),
                    "result": persona_execution_data.get("result", {}),
                    "classification": outcome_result.get("classification"),
                    "confidence_score": outcome_result.get("confidence_score"),
                    "timestamp": workflow.now().isoformat(),
                    "duration_seconds": persona_execution_data.get(
                        "duration_seconds", 0.0
                    ),
                    "metadata": persona_execution_data.get("metadata", {}),
                }
            ]

            analysis_result = await workflow.execute_child_workflow(
                AIAnalysisWorkflow.run,
                args=[outcome_events, learning_context],
                id=f"analysis-{outcome_result.get('outcome_id')}",
            )

            results["phases"].append(
                {
                    "phase": "ai_analysis",
                    "result": analysis_result,
                    "success": analysis_result.get("success", False),
                }
            )

            # Phase 3: Learning adaptation (if we have recommendations)
            recommendations = analysis_result.get("recommendations", [])
            if recommendations and analysis_result.get("success"):
                persona_context = {
                    "persona_id": persona_execution_data.get("persona_id"),
                    "project_id": persona_execution_data.get("project_id"),
                    "current_behavior": persona_execution_data.get(
                        "current_behavior", {}
                    ),
                }

                adaptation_result = await workflow.execute_child_workflow(
                    LearningAdaptationWorkflow.run,
                    args=[recommendations, persona_context],
                    id=f"adaptation-{outcome_result.get('outcome_id')}",
                )

                results["phases"].append(
                    {
                        "phase": "learning_adaptation",
                        "result": adaptation_result,
                        "success": adaptation_result.get("success", False),
                    }
                )

            # Phase 4: Performance metrics
            metrics_result = await workflow.execute_child_workflow(
                PerformanceMetricsWorkflow.run,
                args=[
                    persona_execution_data.get("persona_id"),
                    persona_execution_data.get("project_id"),
                    14,  # 14-day measurement period
                ],
                id=f"metrics-{outcome_result.get('outcome_id')}",
            )

            results["phases"].append(
                {
                    "phase": "performance_metrics",
                    "result": metrics_result,
                    "success": metrics_result.get("success", False),
                }
            )

            # Determine overall success
            successful_phases = sum(
                1 for phase in results["phases"] if phase["success"]
            )
            results["successful_phases"] = successful_phases
            results["total_phases"] = len(results["phases"])
            results["success"] = successful_phases >= 3  # At least 3 out of 4 phases

            workflow.logger.info(
                "Comprehensive learning workflow completed",
                success=results["success"],
                successful_phases=successful_phases,
                total_phases=results["total_phases"],
            )

            return results

        except Exception as e:
            workflow.logger.error(
                "Comprehensive learning workflow failed",
                error=str(e),
                persona_id=persona_execution_data.get("persona_id"),
            )
            results["success"] = False
            results["error"] = str(e)
            return results


@workflow.defn
class PeriodicLearningAnalysisWorkflow:
    """
    Periodic learning analysis workflow for scheduled pattern analysis.

    Runs on schedule to analyze accumulated outcomes and update
    learning patterns for continuous improvement.
    """

    @workflow.run
    async def run(
        self,
        analysis_config: Dict[str, Any],
        schedule_interval: str = "daily",
    ) -> Dict[str, Any]:
        """
        Execute periodic learning analysis workflow.

        Args:
            analysis_config: Analysis configuration
            schedule_interval: Schedule interval (daily, weekly)

        Returns:
            Periodic analysis results with next execution time
        """
        workflow.logger.info(
            "Starting periodic learning analysis workflow",
            schedule_interval=schedule_interval,
        )

        try:
            while True:  # Continuous scheduled execution
                # In production, fetch accumulated outcome events from storage
                # For now, simulate with configuration data
                outcome_events = analysis_config.get("sample_outcomes", [])

                if outcome_events:
                    # Execute AI analysis on accumulated outcomes
                    analysis_result = await workflow.execute_child_workflow(
                        AIAnalysisWorkflow.run,
                        outcome_events,
                        id=f"periodic-analysis-{workflow.now().isoformat()}",
                    )

                    workflow.logger.info(
                        "Periodic analysis completed",
                        success=analysis_result.get("success"),
                        patterns_identified=len(analysis_result.get("patterns", [])),
                    )
                else:
                    workflow.logger.info(
                        "No outcome events for periodic analysis",
                        schedule_interval=schedule_interval,
                    )

                # Calculate next execution time
                if schedule_interval == "daily":
                    next_execution = workflow.now() + timedelta(days=1)
                elif schedule_interval == "weekly":
                    next_execution = workflow.now() + timedelta(weeks=1)
                else:
                    next_execution = workflow.now() + timedelta(
                        days=1
                    )  # Default to daily

                workflow.logger.info(
                    "Next periodic analysis scheduled",
                    next_execution=next_execution.isoformat(),
                )

                # Sleep until next execution
                sleep_duration = (next_execution - workflow.now()).total_seconds()
                if sleep_duration > 0:
                    await workflow.sleep(timedelta(seconds=sleep_duration))

        except Exception as e:
            workflow.logger.error(
                "Periodic learning analysis workflow failed",
                error=str(e),
                schedule_interval=schedule_interval,
            )
            return {
                "success": False,
                "error": str(e),
                "schedule_interval": schedule_interval,
            }
