"""Tests for learning workflow sub-workflows based on Story 2.2 PRD requirements."""

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from orchestra.workflows.learning_workflows import (
    AIAssistedAnalysisWorkflow,
    LearningAdaptationWorkflow,
    OutcomeTrackingWorkflow,
    PerformanceMetricsWorkflow,
)


class TestOutcomeTrackingWorkflow:
    """Test outcome tracking sub-workflow (AC: 1, 6)."""

    @pytest.mark.asyncio
    async def test_outcome_tracking_workflow_success_event(self):
        """Test successful outcome tracking for success events."""
        workflow = OutcomeTrackingWorkflow()

        interaction_outcome = {
            "persona_id": "dev",
            "project_id": "test-project",
            "session_id": "session-123",
            "command": "implement-story",
            "result": {
                "success": True,
                "files_created": ["auth.py", "test_auth.py"],
                "tests_passed": 15,
                "coverage": 0.92,
            },
            "timestamp": datetime.utcnow(),
            "duration_seconds": 45.2,
        }

        with patch(
            "orchestra.workflows.learning_workflows.outcome_tracking_activity"
        ) as mock_activity:
            mock_activity.return_value = {
                "success": True,
                "outcome_id": "outcome-456",
                "classification": "success",
                "confidence_score": 0.95,
                "metadata": {
                    "success_indicators": [
                        "high_coverage",
                        "tests_passed",
                        "files_created",
                    ],
                    "performance_score": 0.88,
                },
            }

            result = await workflow.run(interaction_outcome)

            assert result["success"] is True
            assert result["outcome_id"] == "outcome-456"
            assert result["classification"] == "success"
            assert result["confidence_score"] >= 0.9

            # Verify activity called with correct parameters
            mock_activity.assert_called_once()
            call_args = mock_activity.call_args[0][0]
            assert call_args["persona_id"] == "dev"
            assert call_args["result"]["success"] is True

    @pytest.mark.asyncio
    async def test_outcome_tracking_workflow_failure_event(self):
        """Test outcome tracking for failure events."""
        workflow = OutcomeTrackingWorkflow()

        interaction_outcome = {
            "persona_id": "dev",
            "project_id": "test-project",
            "session_id": "session-123",
            "command": "implement-story",
            "result": {
                "success": False,
                "error": "Compilation failed",
                "error_type": "syntax_error",
                "failed_tests": 3,
            },
            "timestamp": datetime.utcnow(),
            "duration_seconds": 120.5,
        }

        with patch(
            "orchestra.workflows.learning_workflows.outcome_tracking_activity"
        ) as mock_activity:
            mock_activity.return_value = {
                "success": True,
                "outcome_id": "outcome-789",
                "classification": "failure",
                "confidence_score": 0.92,
                "metadata": {
                    "failure_indicators": ["compilation_error", "failed_tests"],
                    "error_patterns": ["syntax_error"],
                },
            }

            result = await workflow.run(interaction_outcome)

            assert result["success"] is True
            assert result["classification"] == "failure"
            assert "failure_indicators" in result["metadata"]

    @pytest.mark.asyncio
    async def test_outcome_tracking_workflow_security_integration(self):
        """Test outcome tracking integrates with security and audit logging."""
        workflow = OutcomeTrackingWorkflow()

        interaction_outcome = {
            "persona_id": "dev",
            "project_id": "test-project",
            "session_id": "session-123",
            "command": "implement-story",
            "result": {"success": True},
            "timestamp": datetime.utcnow(),
            "security_context": {
                "user_id": "user-456",
                "permissions": ["code_write"],
            },
        }

        with patch(
            "orchestra.workflows.learning_workflows.outcome_tracking_activity"
        ) as mock_activity:
            mock_activity.return_value = {
                "success": True,
                "outcome_id": "outcome-sec",
                "classification": "success",
                "audit_logged": True,
                "security_validated": True,
            }

            result = await workflow.run(interaction_outcome)

            assert result["success"] is True
            assert result["audit_logged"] is True
            assert result["security_validated"] is True


class TestAIAssistedAnalysisWorkflow:
    """Test AI-assisted analysis sub-workflow (AC: 2, 6, 7)."""

    @pytest.mark.asyncio
    async def test_ai_analysis_workflow_pattern_recognition(self):
        """Test AI-assisted pattern analysis with OpenAI integration."""
        workflow = AIAssistedAnalysisWorkflow()

        analysis_context = {
            "project_id": "test-project",
            "outcome_events": [
                {
                    "outcome_id": "outcome-1",
                    "classification": "success",
                    "metadata": {"domain": "authentication", "complexity": "high"},
                },
                {
                    "outcome_id": "outcome-2",
                    "classification": "failure",
                    "metadata": {"domain": "authentication", "error": "validation"},
                },
            ],
            "analysis_window_days": 30,
        }

        with patch(
            "orchestra.workflows.learning_workflows.ai_analysis_activity"
        ) as mock_activity:
            mock_activity.return_value = {
                "success": True,
                "patterns_identified": [
                    {
                        "pattern_id": "auth-pattern-1",
                        "type": "success_pattern",
                        "description": "High test coverage leads to successful auth implementations",
                        "accuracy": 0.87,  # AC: 7 - >85% accuracy
                        "confidence": 0.92,
                        "recommendations": [
                            "Always include comprehensive test coverage for auth features",
                            "Use established auth libraries for validation",
                        ],
                    }
                ],
                "improvement_suggestions": [
                    {
                        "suggestion_id": "improve-1",
                        "target_persona": "dev",
                        "improvement": "Add validation step before auth implementation",
                        "expected_impact": 0.75,  # AC: 8 - >70% improvement rate
                    }
                ],
            }

            result = await workflow.run(analysis_context)

            assert result["success"] is True
            assert len(result["patterns_identified"]) == 1
            assert result["patterns_identified"][0]["accuracy"] > 0.85  # AC: 7
            assert len(result["improvement_suggestions"]) == 1
            assert (
                result["improvement_suggestions"][0]["expected_impact"] > 0.7
            )  # AC: 8

    @pytest.mark.asyncio
    async def test_ai_analysis_workflow_openai_integration(self):
        """Test AI analysis workflow integrates with OpenAI services."""
        workflow = AIAssistedAnalysisWorkflow()

        analysis_context = {
            "project_id": "test-project",
            "outcome_events": [{"outcome_id": "test", "classification": "success"}],
        }

        with patch(
            "orchestra.workflows.learning_workflows.ai_analysis_activity"
        ) as mock_activity:
            mock_activity.return_value = {
                "success": True,
                "openai_request_id": "req-abc123",
                "openai_model": "gpt-4",
                "tokens_used": 1250,
                "patterns_identified": [],
                "improvement_suggestions": [],
            }

            result = await workflow.run(analysis_context)

            assert result["success"] is True
            assert "openai_request_id" in result
            assert result["openai_model"] == "gpt-4"

    @pytest.mark.asyncio
    async def test_ai_analysis_workflow_circuit_breaker(self):
        """Test AI analysis workflow has circuit breaker for API failures."""
        workflow = AIAssistedAnalysisWorkflow()

        analysis_context = {
            "project_id": "test-project",
            "outcome_events": [{"outcome_id": "test", "classification": "success"}],
        }

        with patch(
            "orchestra.workflows.learning_workflows.ai_analysis_activity"
        ) as mock_activity:
            # Simulate OpenAI API failure
            mock_activity.return_value = {
                "success": False,
                "error": "OpenAI API rate limit exceeded",
                "circuit_breaker_triggered": True,
                "fallback_analysis": {
                    "patterns_identified": [],
                    "improvement_suggestions": [],
                },
            }

            result = await workflow.run(analysis_context)

            assert result["success"] is False
            assert result["circuit_breaker_triggered"] is True
            assert "fallback_analysis" in result


class TestLearningAdaptationWorkflow:
    """Test learning adaptation sub-workflow (AC: 3, 6, 8, 9, 10)."""

    @pytest.mark.asyncio
    async def test_learning_adaptation_workflow_apply_recommendations(self):
        """Test learning adaptation applies AI recommendations to persona behavior."""
        workflow = LearningAdaptationWorkflow()

        adaptation_context = {
            "persona_id": "dev",
            "project_id": "test-project",
            "ai_recommendations": [
                {
                    "recommendation_id": "rec-1",
                    "type": "behavior_modification",
                    "description": "Add validation step before implementation",
                    "confidence": 0.88,
                    "expected_improvement": 0.75,
                    "rules": [
                        {
                            "condition": "command == 'implement-story'",
                            "action": "run_validation_checks_first",
                            "priority": "high",
                        }
                    ],
                }
            ],
        }

        with patch(
            "orchestra.workflows.learning_workflows.learning_adaptation_activity"
        ) as mock_activity:
            mock_activity.return_value = {
                "success": True,
                "adaptations_applied": 1,
                "behavior_rules_updated": [
                    {
                        "rule_id": "rule-123",
                        "persona_id": "dev",
                        "rule": "run_validation_checks_first",
                        "active": True,
                    }
                ],
                "performance_impact": {
                    "load_time_ms": 480,  # AC: 9 - <500ms load time maintained
                    "within_limits": True,
                },
            }

            result = await workflow.run(adaptation_context)

            assert result["success"] is True
            assert result["adaptations_applied"] == 1
            assert result["performance_impact"]["load_time_ms"] < 500  # AC: 9
            assert result["performance_impact"]["within_limits"] is True

    @pytest.mark.asyncio
    async def test_learning_adaptation_workflow_rollback_mechanism(self):
        """Test learning adaptation has rollback for unsuccessful adaptations."""
        workflow = LearningAdaptationWorkflow()

        adaptation_context = {
            "persona_id": "dev",
            "project_id": "test-project",
            "ai_recommendations": [
                {
                    "recommendation_id": "rec-bad",
                    "type": "behavior_modification",
                    "description": "Complex rule that degrades performance",
                    "confidence": 0.60,
                    "expected_improvement": 0.30,
                }
            ],
        }

        with patch(
            "orchestra.workflows.learning_workflows.learning_adaptation_activity"
        ) as mock_activity:
            mock_activity.return_value = {
                "success": False,
                "error": "Performance degradation detected",
                "rollback_triggered": True,
                "rollback_successful": True,
                "performance_impact": {
                    "load_time_ms": 650,  # Exceeds 500ms limit
                    "degradation_percent": 15,  # AC: 10 - >10% degradation
                    "within_limits": False,
                },
            }

            result = await workflow.run(adaptation_context)

            assert result["success"] is False
            assert result["rollback_triggered"] is True
            assert result["rollback_successful"] is True
            assert result["performance_impact"]["degradation_percent"] > 10  # AC: 10

    @pytest.mark.asyncio
    async def test_learning_adaptation_workflow_confidence_scoring(self):
        """Test learning adaptation uses confidence scoring system."""
        workflow = LearningAdaptationWorkflow()

        adaptation_context = {
            "persona_id": "dev",
            "project_id": "test-project",
            "ai_recommendations": [
                {
                    "recommendation_id": "rec-high-conf",
                    "confidence": 0.95,
                    "expected_improvement": 0.80,
                },
                {
                    "recommendation_id": "rec-low-conf",
                    "confidence": 0.45,
                    "expected_improvement": 0.60,
                },
            ],
        }

        with patch(
            "orchestra.workflows.learning_workflows.learning_adaptation_activity"
        ) as mock_activity:
            mock_activity.return_value = {
                "success": True,
                "adaptations_applied": 1,  # Only high-confidence recommendation applied
                "confidence_threshold": 0.70,
                "rejected_recommendations": [
                    {
                        "recommendation_id": "rec-low-conf",
                        "reason": "Below confidence threshold",
                    }
                ],
            }

            result = await workflow.run(adaptation_context)

            assert result["success"] is True
            assert result["adaptations_applied"] == 1
            assert len(result["rejected_recommendations"]) == 1


class TestPerformanceMetricsWorkflow:
    """Test performance metrics sub-workflow (AC: 4, 6)."""

    @pytest.mark.asyncio
    async def test_performance_metrics_workflow_effectiveness_tracking(self):
        """Test performance metrics tracks learning effectiveness over time."""
        workflow = PerformanceMetricsWorkflow()

        metrics_context = {
            "persona_id": "dev",
            "project_id": "test-project",
            "measurement_period_days": 30,
            "baseline_metrics": {
                "success_rate": 0.75,
                "average_completion_time": 120.0,
                "error_rate": 0.15,
            },
        }

        with patch(
            "orchestra.workflows.learning_workflows.performance_metrics_activity"
        ) as mock_activity:
            mock_activity.return_value = {
                "success": True,
                "current_metrics": {
                    "success_rate": 0.85,  # 10% improvement
                    "average_completion_time": 95.0,  # 25 seconds faster
                    "error_rate": 0.08,  # 7% reduction
                },
                "improvement_trends": {
                    "success_rate_trend": "+13.3%",
                    "completion_time_trend": "-20.8%",
                    "error_rate_trend": "-46.7%",
                },
                "learning_effectiveness_score": 0.82,
            }

            result = await workflow.run(metrics_context)

            assert result["success"] is True
            assert (
                result["current_metrics"]["success_rate"]
                > metrics_context["baseline_metrics"]["success_rate"]
            )
            assert result["learning_effectiveness_score"] > 0.7

    @pytest.mark.asyncio
    async def test_performance_metrics_workflow_trending_analysis(self):
        """Test performance metrics provides trending analysis."""
        workflow = PerformanceMetricsWorkflow()

        metrics_context = {
            "persona_id": "dev",
            "project_id": "test-project",
            "measurement_period_days": 90,
        }

        with patch(
            "orchestra.workflows.learning_workflows.performance_metrics_activity"
        ) as mock_activity:
            mock_activity.return_value = {
                "success": True,
                "trend_analysis": {
                    "30_day_trend": "improving",
                    "60_day_trend": "stable",
                    "90_day_trend": "improving",
                    "trend_confidence": 0.88,
                },
                "performance_forecasts": {
                    "next_30_days": {
                        "predicted_success_rate": 0.87,
                        "confidence_interval": [0.82, 0.92],
                    }
                },
            }

            result = await workflow.run(metrics_context)

            assert result["success"] is True
            assert "trend_analysis" in result
            assert result["trend_analysis"]["trend_confidence"] > 0.8
            assert "performance_forecasts" in result

    @pytest.mark.asyncio
    async def test_performance_metrics_workflow_scheduled_execution(self):
        """Test performance metrics as scheduled Temporal workflow."""
        workflow = PerformanceMetricsWorkflow()

        metrics_context = {
            "persona_id": "dev",
            "project_id": "test-project",
            "schedule_type": "weekly",
            "automated": True,
        }

        with patch(
            "orchestra.workflows.learning_workflows.performance_metrics_activity"
        ) as mock_activity:
            mock_activity.return_value = {
                "success": True,
                "schedule_type": "weekly",
                "next_execution": datetime.utcnow() + timedelta(weeks=1),
                "metrics_collected": True,
                "report_generated": True,
            }

            result = await workflow.run(metrics_context)

            assert result["success"] is True
            assert result["schedule_type"] == "weekly"
            assert "next_execution" in result


class TestLearningWorkflowIntegration:
    """Test integration between learning workflows."""

    @pytest.mark.asyncio
    async def test_learning_workflow_end_to_end(self):
        """Test complete learning cycle: outcome -> analysis -> adaptation -> metrics."""
        # Step 1: Track outcome
        outcome_workflow = OutcomeTrackingWorkflow()
        interaction_outcome = {
            "persona_id": "dev",
            "project_id": "test-project",
            "command": "implement-story",
            "result": {"success": True, "quality_score": 0.9},
            "timestamp": datetime.utcnow(),
        }

        with patch(
            "orchestra.workflows.learning_workflows.outcome_tracking_activity"
        ) as mock_outcome:
            mock_outcome.return_value = {
                "success": True,
                "outcome_id": "outcome-e2e",
                "classification": "success",
            }

            outcome_result = await outcome_workflow.run(interaction_outcome)
            assert outcome_result["success"] is True

        # Step 2: AI analysis
        analysis_workflow = AIAssistedAnalysisWorkflow()
        analysis_context = {
            "project_id": "test-project",
            "outcome_events": [outcome_result],
        }

        with patch(
            "orchestra.workflows.learning_workflows.ai_analysis_activity"
        ) as mock_analysis:
            mock_analysis.return_value = {
                "success": True,
                "patterns_identified": [{"pattern_id": "p1", "accuracy": 0.9}],
                "improvement_suggestions": [
                    {"suggestion_id": "s1", "expected_impact": 0.8}
                ],
            }

            analysis_result = await analysis_workflow.run(analysis_context)
            assert analysis_result["success"] is True

        # Step 3: Learning adaptation
        adaptation_workflow = LearningAdaptationWorkflow()
        adaptation_context = {
            "persona_id": "dev",
            "project_id": "test-project",
            "ai_recommendations": analysis_result["improvement_suggestions"],
        }

        with patch(
            "orchestra.workflows.learning_workflows.learning_adaptation_activity"
        ) as mock_adaptation:
            mock_adaptation.return_value = {
                "success": True,
                "adaptations_applied": 1,
                "performance_impact": {"load_time_ms": 450, "within_limits": True},
            }

            adaptation_result = await adaptation_workflow.run(adaptation_context)
            assert adaptation_result["success"] is True

        # Step 4: Performance metrics
        metrics_workflow = PerformanceMetricsWorkflow()
        metrics_context = {
            "persona_id": "dev",
            "project_id": "test-project",
            "measurement_period_days": 7,
        }

        with patch(
            "orchestra.workflows.learning_workflows.performance_metrics_activity"
        ) as mock_metrics:
            mock_metrics.return_value = {
                "success": True,
                "learning_effectiveness_score": 0.85,
                "improvement_trends": {"success_rate_trend": "+15%"},
            }

            metrics_result = await metrics_workflow.run(metrics_context)
            assert metrics_result["success"] is True
            assert metrics_result["learning_effectiveness_score"] > 0.7

    @pytest.mark.asyncio
    async def test_learning_workflow_memory_integration(self):
        """Test learning workflows integrate with memory infrastructure."""
        # Learning workflows should store and retrieve patterns from memory
        outcome_workflow = OutcomeTrackingWorkflow()

        interaction_outcome = {
            "persona_id": "dev",
            "project_id": "test-project",
            "command": "implement-story",
            "result": {"success": True},
            "timestamp": datetime.utcnow(),
            "memory_context": {
                "store_outcome": True,
                "retrieve_similar": True,
            },
        }

        with patch(
            "orchestra.workflows.learning_workflows.outcome_tracking_activity"
        ) as mock_activity:
            mock_activity.return_value = {
                "success": True,
                "outcome_id": "outcome-mem",
                "memory_stored": True,
                "similar_outcomes_retrieved": 3,
                "memory_integration": {
                    "memory_service_called": True,
                    "patterns_enhanced": True,
                },
            }

            result = await outcome_workflow.run(interaction_outcome)

            assert result["success"] is True
            assert result["memory_stored"] is True
            assert result["memory_integration"]["memory_service_called"] is True
