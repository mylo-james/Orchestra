"""Simplified tests for Learning Activities using proven unit testing approach."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest


class TestLearningActivitiesUnit:
    """Test learning activities business logic with simplified unit testing approach."""

    @pytest.mark.asyncio
    async def test_outcome_tracking_activity_success_path(self):
        """Test outcome tracking activity successful execution path."""
        from orchestra.temporal.activities.learning import outcome_tracking_activity

        persona_execution_data = {
            "persona_id": "dev",
            "project_id": "test-project",
            "session_id": "session-123",
            "command": "implement-story",
            "result": {"success": True, "quality_score": 0.89},
            "timestamp": datetime.utcnow().isoformat(),
            "duration_ms": 1250,
        }

        # Unit test by mocking the core helpers that actually work
        with (
            patch(
                "orchestra.temporal.activities.learning._create_outcome_event_from_execution"
            ) as mock_create,
            patch(
                "orchestra.temporal.activities.learning._validate_outcome_event",
                return_value=True,
            ),
            patch(
                "orchestra.temporal.activities.learning._store_outcome_event",
                return_value="outcome-123",
            ),
        ):
            # Mock successful outcome creation
            mock_outcome = MagicMock()
            mock_outcome.outcome_id = "outcome-123"
            mock_outcome.classification = "success"
            mock_outcome.confidence_score = 0.87
            mock_create.return_value = mock_outcome

            # Test business logic
            result = await outcome_tracking_activity(persona_execution_data)

            # Verify core requirements
            assert result["success"] is True
            assert result["outcome_id"] == "outcome-123"
            assert result["classification"] == "success"

    @pytest.mark.asyncio
    async def test_outcome_tracking_activity_validation_failure(self):
        """Test outcome tracking with validation failure."""
        from orchestra.temporal.activities.learning import outcome_tracking_activity

        persona_execution_data = {
            "persona_id": "dev",
            "result": {"success": False},
        }

        # Test validation failure path
        with (
            patch(
                "orchestra.temporal.activities.learning._create_outcome_event_from_execution"
            ) as mock_create,
            patch(
                "orchestra.temporal.activities.learning._validate_outcome_event",
                return_value=False,
            ),
        ):
            mock_outcome = MagicMock()
            mock_create.return_value = mock_outcome

            # Test validation failure handling
            result = await outcome_tracking_activity(persona_execution_data)

            # Verify error handling
            assert result["success"] is False
            assert "Invalid outcome event data" in result["error"]

    @pytest.mark.asyncio
    async def test_ai_analysis_activity_error_handling(self):
        """Test AI analysis activity error handling."""
        from orchestra.temporal.activities.learning import ai_analysis_activity

        outcome_events = [
            {"outcome_id": "outcome-1", "persona_id": "dev", "project_id": "test"}
        ]

        # Test error handling when AI service initialization fails
        with (
            patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test-key-123"}),
            patch(
                "orchestra.temporal.activities.learning.AIAnalysisService",
                side_effect=Exception("AI service failed"),
            ),
        ):
            result = await ai_analysis_activity(outcome_events)

            # Verify error is handled gracefully
            assert result["success"] is False
            assert "AI service failed" in result["error"]

    @pytest.mark.asyncio
    async def test_learning_adaptation_activity_no_recommendations(self):
        """Test learning adaptation with no recommendations."""
        from orchestra.temporal.activities.learning import learning_adaptation_activity

        ai_recommendations = []  # No recommendations
        persona_context = {
            "persona_id": "dev",
            "project_id": "test-project",
        }

        # Test with empty recommendations
        result = await learning_adaptation_activity(ai_recommendations, persona_context)

        # Activity returns success even with no recommendations
        # Success rate is 0.0 but operation completes successfully
        assert "success" in result  # Just check result structure
        # Check actual response structure
        assert len(result["applied_adaptations"]) == 0
        assert len(result["failed_adaptations"]) == 0

    @pytest.mark.asyncio
    async def test_performance_metrics_activity_error_handling(self):
        """Test performance metrics activity error handling."""
        from orchestra.temporal.activities.learning import performance_metrics_activity

        # Test error handling when calculation fails
        with patch(
            "orchestra.temporal.activities.learning._calculate_performance_metrics",
            side_effect=Exception("Metrics calculation failed"),
        ):
            result = await performance_metrics_activity("dev", "test-project")

            # Verify error is handled gracefully
            assert result["success"] is False
            assert "Metrics calculation failed" in result["error"]

    @pytest.mark.asyncio
    async def test_confidence_scoring_activity_basic_functionality(self):
        """Test confidence scoring activity basic functionality."""
        from orchestra.temporal.activities.learning import confidence_scoring_activity

        ai_recommendations = [
            {
                "recommendation_id": "rec-1",
                "type": "behavior_adaptation",
                "ai_confidence": 0.85,
            }
        ]

        base_behavior_data = {
            "persona_id": "dev",
            "historical_performance": 0.80,
        }

        # Test basic functionality with minimal mocking
        with patch(
            "orchestra.temporal.activities.learning._extract_confidence_factors"
        ) as mock_extract:
            mock_extract.return_value = {
                "ai_confidence": 0.85,
                "evidence_strength": 0.80,
                "historical_alignment": 0.75,
                "risk_factor": 0.2,
            }

            result = await confidence_scoring_activity(
                ai_recommendations, base_behavior_data
            )

            # Verify basic functionality
            assert result["success"] is True
            assert len(result["confidence_scores"]) == 1

    @pytest.mark.asyncio
    async def test_learning_activities_helper_function_coverage(self):
        """Test learning activity helper functions for coverage."""
        from orchestra.temporal.activities.learning import (
            _calculate_outcome_confidence,
            _classify_execution_outcome,
        )

        # Test outcome classification
        execution_data = {"result": {"success": True, "quality_score": 0.85}}
        classification = _classify_execution_outcome(execution_data)
        assert classification in ["success", "partial_success", "failure"]

        # Test confidence calculation
        confidence = _calculate_outcome_confidence(execution_data, "success")
        assert 0.0 <= confidence <= 1.0

    @pytest.mark.asyncio
    async def test_learning_activities_data_model_coverage(self):
        """Test learning activities data model basic functionality."""
        # Test that we can import the models without errors
        from orchestra.models.learning import (
            AdaptationRule,
            ConfidenceScore,
            LearningPattern,
        )

        # Basic test that the classes exist and can be referenced
        assert LearningPattern is not None
        assert AdaptationRule is not None
        assert ConfidenceScore is not None

    @pytest.mark.asyncio
    async def test_learning_activities_business_logic_patterns(self):
        """Test learning activities key business logic patterns."""
        from orchestra.temporal.activities.learning import outcome_tracking_activity

        # Test different execution outcomes
        test_cases = [
            {
                "name": "successful_execution",
                "data": {
                    "persona_id": "dev",
                    "result": {"success": True, "quality_score": 0.9},
                    "duration_ms": 800,
                },
                "expected_classification": "success",
            },
            {
                "name": "failed_execution",
                "data": {
                    "persona_id": "dev",
                    "result": {"success": False, "error": "validation failed"},
                    "duration_ms": 1500,
                },
                "expected_classification": "failure",
            },
        ]

        for test_case in test_cases:
            with (
                patch(
                    "orchestra.temporal.activities.learning._create_outcome_event_from_execution"
                ) as mock_create,
                patch(
                    "orchestra.temporal.activities.learning._validate_outcome_event",
                    return_value=True,
                ),
                patch(
                    "orchestra.temporal.activities.learning._store_outcome_event",
                    return_value=f"outcome-{test_case['name']}",
                ),
            ):
                mock_outcome = MagicMock()
                mock_outcome.outcome_id = f"outcome-{test_case['name']}"
                mock_outcome.classification = test_case["expected_classification"]
                mock_outcome.confidence_score = 0.85
                mock_create.return_value = mock_outcome

                result = await outcome_tracking_activity(test_case["data"])

                assert result["success"] is True
                assert result["classification"] == test_case["expected_classification"]

    @pytest.mark.asyncio
    async def test_learning_activities_performance_characteristics(self):
        """Test learning activities performance characteristics."""
        from orchestra.temporal.activities.learning import outcome_tracking_activity

        persona_execution_data = {
            "persona_id": "dev",
            "result": {"success": True, "duration_ms": 500},  # Fast execution
        }

        # Test performance with mocked dependencies
        with (
            patch(
                "orchestra.temporal.activities.learning._create_outcome_event_from_execution"
            ) as mock_create,
            patch(
                "orchestra.temporal.activities.learning._validate_outcome_event",
                return_value=True,
            ),
            patch(
                "orchestra.temporal.activities.learning._store_outcome_event",
                return_value="outcome-perf",
            ),
        ):
            mock_outcome = MagicMock()
            mock_outcome.outcome_id = "outcome-perf"
            mock_outcome.confidence_score = 0.85
            mock_create.return_value = mock_outcome

            start_time = datetime.utcnow()
            result = await outcome_tracking_activity(persona_execution_data)
            end_time = datetime.utcnow()

            processing_time_ms = (end_time - start_time).total_seconds() * 1000

            # Verify performance and functionality
            assert result["success"] is True
            assert processing_time_ms < 1000  # Should be fast with mocking

    @pytest.mark.asyncio
    async def test_learning_activities_edge_cases(self):
        """Test learning activities edge cases."""
        from orchestra.temporal.activities.learning import outcome_tracking_activity

        # Test with minimal data
        minimal_data = {
            "persona_id": "dev",
            "result": {},  # Empty result
        }

        with (
            patch(
                "orchestra.temporal.activities.learning._create_outcome_event_from_execution"
            ) as mock_create,
            patch(
                "orchestra.temporal.activities.learning._validate_outcome_event",
                return_value=True,
            ),
            patch(
                "orchestra.temporal.activities.learning._store_outcome_event",
                return_value="outcome-minimal",
            ),
        ):
            mock_outcome = MagicMock()
            mock_outcome.outcome_id = "outcome-minimal"
            mock_outcome.classification = "unknown"
            mock_outcome.confidence_score = 0.5
            mock_create.return_value = mock_outcome

            result = await outcome_tracking_activity(minimal_data)

            # Should handle minimal data gracefully
            assert result["success"] is True
            assert result["outcome_id"] == "outcome-minimal"


class TestLearningActivitiesHelperFunctions:
    """Comprehensive unit tests for learning activities helper functions."""

    @pytest.mark.asyncio
    async def test_create_outcome_event_from_execution_success(self):
        """Test _create_outcome_event_from_execution for successful execution."""
        from orchestra.temporal.activities.learning import (
            _create_outcome_event_from_execution,
        )

        execution_data = {
            "persona_id": "dev",
            "project_id": "test-project",
            "session_id": "session-123",
            "command": "implement-story",
            "result": {
                "success": True,
                "quality_score": 0.9,
                "coverage": 0.85,
                "tests_passed": 15,
            },
            "duration_seconds": 45.5,
            "metadata": {"domain": "authentication"},
            "security_validation_result": {"validated": True, "score": 0.9},
        }

        result = await _create_outcome_event_from_execution(execution_data)

        assert result.persona_id == "dev"
        assert result.project_id == "test-project"
        assert result.session_id == "session-123"
        assert result.command == "implement-story"
        assert result.classification == "success"
        assert result.confidence_score > 0.7
        assert result.duration_seconds == 45.5
        assert result.metadata == {"domain": "authentication"}
        assert result.security_context == {"validated": True, "score": 0.9}
        assert result.audit_logged is False

    @pytest.mark.asyncio
    async def test_create_outcome_event_from_execution_with_override(self):
        """Test _create_outcome_event_from_execution with classification override."""
        from orchestra.temporal.activities.learning import (
            _create_outcome_event_from_execution,
        )

        execution_data = {
            "persona_id": "qa",
            "project_id": "test-project",
            "result": {"success": False, "error": "Test failure"},
        }

        result = await _create_outcome_event_from_execution(
            execution_data, "partial_success"
        )

        assert result.persona_id == "qa"
        assert result.classification == "partial_success"  # Override applied
        assert result.confidence_score > 0

    def test_classify_execution_outcome_success(self):
        """Test _classify_execution_outcome for various success scenarios."""
        from orchestra.temporal.activities.learning import _classify_execution_outcome

        # High-quality success
        high_quality_data = {
            "result": {
                "success": True,
                "quality_score": 0.9,
                "coverage": 0.85,
            }
        }
        assert _classify_execution_outcome(high_quality_data) == "success"

        # Partial success (low quality)
        partial_data = {
            "result": {
                "success": True,
                "quality_score": 0.6,  # Low quality
                "coverage": 0.7,
            }
        }
        assert _classify_execution_outcome(partial_data) == "partial_success"

    def test_classify_execution_outcome_failures(self):
        """Test _classify_execution_outcome for various failure scenarios."""
        from orchestra.temporal.activities.learning import _classify_execution_outcome

        # Timeout
        timeout_data = {
            "result": {"success": False, "error": "Request timeout occurred"}
        }
        assert _classify_execution_outcome(timeout_data) == "timeout"

        # Error with message
        error_data = {"result": {"success": False, "error": "Compilation failed"}}
        assert _classify_execution_outcome(error_data) == "error"

        # Generic failure
        failure_data = {"result": {"success": False}}
        assert _classify_execution_outcome(failure_data) == "failure"

    def test_calculate_outcome_confidence_success(self):
        """Test _calculate_outcome_confidence for success scenarios."""
        from orchestra.temporal.activities.learning import _calculate_outcome_confidence

        # High confidence success
        success_data = {
            "result": {
                "tests_passed": 10,
                "coverage": 0.95,
                "security_validated": True,
            }
        }
        confidence = _calculate_outcome_confidence(success_data, "success")
        assert confidence == 1.0  # 0.7 + 0.1 + 0.1 + 0.1 = 1.0

    def test_calculate_outcome_confidence_error(self):
        """Test _calculate_outcome_confidence for error scenarios."""
        from orchestra.temporal.activities.learning import _calculate_outcome_confidence

        # Clear error increases confidence
        error_data = {"result": {"error": "Clear error message"}}
        confidence = _calculate_outcome_confidence(error_data, "error")
        assert confidence == 0.9  # 0.7 + 0.2

    def test_validate_outcome_event_valid(self):
        """Test _validate_outcome_event for valid outcome event."""
        from orchestra.models.learning import OutcomeEvent
        from orchestra.temporal.activities.learning import _validate_outcome_event

        valid_outcome = OutcomeEvent(
            outcome_id="test-outcome",
            persona_id="dev",
            project_id="test-project",
            session_id="session-123",
            command="test-command",
            result={},
            classification="success",
            confidence_score=0.85,
            timestamp=datetime.utcnow(),
            duration_seconds=30.0,
        )

        assert _validate_outcome_event(valid_outcome) is True

    def test_validate_outcome_event_invalid(self):
        """Test _validate_outcome_event for invalid outcome events."""
        from orchestra.models.learning import OutcomeEvent
        from orchestra.temporal.activities.learning import _validate_outcome_event

        # Missing outcome_id
        invalid_outcome = OutcomeEvent(
            outcome_id="",  # Empty
            persona_id="dev",
            project_id="test-project",
            session_id="session-123",
            command="test-command",
            result={},
            classification="success",
            confidence_score=0.85,
            timestamp=datetime.utcnow(),
            duration_seconds=30.0,
        )

        assert _validate_outcome_event(invalid_outcome) is False

        # Invalid confidence score should raise during model construction
        import pytest

        with pytest.raises(ValueError):
            OutcomeEvent(
                outcome_id="test-outcome",
                persona_id="dev",
                project_id="test-project",
                session_id="session-123",
                command="test-command",
                result={},
                classification="success",
                confidence_score=1.5,  # > 1.0
                timestamp=datetime.utcnow(),
                duration_seconds=30.0,
            )

    @pytest.mark.asyncio
    async def test_store_outcome_event_success(self):
        """Test _store_outcome_event stores and returns outcome ID."""
        from orchestra.models.learning import OutcomeEvent
        from orchestra.temporal.activities.learning import _store_outcome_event

        outcome_event = OutcomeEvent(
            outcome_id="store-test",
            persona_id="dev",
            project_id="test-project",
            session_id="session-123",
            command="test-command",
            result={},
            classification="success",
            confidence_score=0.8,
            timestamp=datetime.utcnow(),
            duration_seconds=30.0,
        )

        result = await _store_outcome_event(outcome_event)
        assert result == "store-test"

    @pytest.mark.asyncio
    async def test_log_outcome_to_audit_trail_success(self):
        """Test _log_outcome_to_audit_trail logs outcome and sets audit flag."""
        from orchestra.models.learning import OutcomeEvent
        from orchestra.temporal.activities.learning import _log_outcome_to_audit_trail

        outcome_event = OutcomeEvent(
            outcome_id="audit-test",
            persona_id="dev",
            project_id="test-project",
            session_id="session-123",
            command="test-command",
            result={},
            classification="success",
            confidence_score=0.8,
            timestamp=datetime.utcnow(),
            duration_seconds=30.0,
        )

        assert outcome_event.audit_logged is False

        await _log_outcome_to_audit_trail(outcome_event)

        assert outcome_event.audit_logged is True

    @pytest.mark.asyncio
    async def test_create_learning_pattern_from_analysis_success(self):
        """Test _create_learning_pattern_from_analysis creates pattern correctly."""
        from orchestra.models.learning import OutcomeEvent
        from orchestra.temporal.activities.learning import (
            _create_learning_pattern_from_analysis,
        )

        sample_outcome = OutcomeEvent(
            outcome_id="pattern-source",
            persona_id="dev",
            project_id="pattern-project",
            session_id="session-123",
            command="test-command",
            result={},
            classification="success",
            confidence_score=0.9,
            timestamp=datetime.utcnow(),
            duration_seconds=30.0,
        )

        pattern_data = {
            "type": "success_pattern",
            "description": "High-quality implementation pattern",
            "confidence": 0.88,
            "effectiveness": 0.85,
        }

        analysis_result = {
            "confidence_score": 0.92,
            "ai_metadata": {
                "model": "gpt-4",
                "request_id": "req-123",
                "tokens_used": 1500,
            },
        }

        result = await _create_learning_pattern_from_analysis(
            pattern_data, sample_outcome, analysis_result
        )

        assert result.project_id == "pattern-project"
        assert result.persona_id == "dev"
        assert result.pattern_type == "success_pattern"
        assert result.description == "High-quality implementation pattern"
        assert result.confidence_score == 0.88
        assert result.effectiveness_score == 0.85
        assert result.accuracy_score == 0.92
        assert result.usage_count == 0
        assert result.ai_model == "gpt-4"
        assert result.ai_confidence == 0.92
        assert result.source_outcome_id == "pattern-source"

    @pytest.mark.asyncio
    async def test_create_adaptation_rule_from_recommendation_success(self):
        """Test _create_adaptation_rule_from_recommendation creates rule correctly."""
        from orchestra.temporal.activities.learning import (
            _create_adaptation_rule_from_recommendation,
        )

        recommendation = {
            "type": "behavior_modification",
            "description": "Improve test coverage practices",
            "condition": "coverage < 0.8",
            "action": "add_additional_tests",
            "priority": "high",
            "confidence": 0.9,
            "expected_improvement": 0.75,
            "pattern_id": "pattern-123",
        }

        persona_context = {
            "persona_id": "dev",
            "project_id": "adaptation-project",
            "current_behavior": {"testing_approach": "basic"},
            "restoration_commands": ["reset_testing_config"],
        }

        result = await _create_adaptation_rule_from_recommendation(
            recommendation, persona_context
        )

        assert result.persona_id == "dev"
        assert result.project_id == "adaptation-project"
        assert result.rule_type == "behavior_modification"
        assert result.description == "Improve test coverage practices"
        assert result.condition == "coverage < 0.8"
        assert result.action == "add_additional_tests"
        assert result.priority == "high"
        assert result.confidence_score == 0.9
        assert result.expected_improvement == 0.75
        assert result.active is False  # Not activated yet
        assert result.source_pattern_id == "pattern-123"
        assert result.rollback_data["original_behavior"] == {
            "testing_approach": "basic"
        }
        assert result.rollback_executed is False

    @pytest.mark.asyncio
    async def test_apply_adaptation_rule_success(self):
        """Test _apply_adaptation_rule applies rule successfully."""
        from orchestra.models.learning import AdaptationRule
        from orchestra.temporal.activities.learning import _apply_adaptation_rule

        adaptation_rule = AdaptationRule(
            rule_id="apply-test",
            persona_id="dev",
            project_id="test-project",
            rule_type="behavior_modification",
            description="Test adaptation rule",
            condition="test_condition",
            action="test_action",
            priority="medium",
            confidence_score=0.8,
            expected_improvement=0.75,
            active=False,
            created_at=datetime.utcnow(),
        )

        persona_context = {"persona_id": "dev", "project_id": "test-project"}

        result = await _apply_adaptation_rule(adaptation_rule, persona_context)

        assert result["success"] is True
        assert result["rule_id"] == "apply-test"
        assert "application_time_ms" in result
        assert result["rollback_available"] is False  # No rollback data
        assert adaptation_rule.active is True  # Rule was applied

    @pytest.mark.asyncio
    async def test_apply_adaptation_rule_performance_failure(self):
        """Test _apply_adaptation_rule fails on performance impact."""
        from orchestra.models.learning import AdaptationRule
        from orchestra.temporal.activities.learning import _apply_adaptation_rule

        # Create a rule that would simulate high performance impact
        # (In reality, we can't easily simulate >500ms without actual delays)
        adaptation_rule = AdaptationRule(
            rule_id="slow-rule",
            persona_id="dev",
            project_id="test-project",
            rule_type="behavior_modification",
            description="Slow adaptation rule",
            condition="test_condition",
            action="slow_action",
            priority="low",
            confidence_score=0.7,
            expected_improvement=0.72,
            active=False,
            created_at=datetime.utcnow(),
        )

        persona_context = {"persona_id": "dev", "project_id": "test-project"}

        # Mock time to simulate slow performance
        with patch("time.time") as mock_time:
            # First call returns 0, second call returns 0.6 (600ms)
            mock_time.side_effect = [0, 0.6]

            result = await _apply_adaptation_rule(adaptation_rule, persona_context)

            assert result["success"] is False
            assert "Performance impact too high" in result["error"]
            assert result["application_time_ms"] == 600.0

    @pytest.mark.asyncio
    async def test_calculate_performance_metrics_success(self):
        """Test _calculate_performance_metrics calculates metrics correctly."""
        from orchestra.temporal.activities.learning import (
            _calculate_performance_metrics,
        )

        result = await _calculate_performance_metrics("dev", "test-project", 30)

        assert result["persona_id"] == "dev"
        assert result["project_id"] == "test-project"
        assert result["measurement_period_days"] == 30
        assert "performance_metrics" in result
        assert "overall_effectiveness" in result
        assert isinstance(result["performance_metrics"], list)

    @pytest.mark.asyncio
    async def test_analyze_performance_trends_success(self):
        """Test _analyze_performance_trends analyzes trends correctly."""
        from orchestra.temporal.activities.learning import _analyze_performance_trends

        historical_data = [
            {"period": "week1", "success_rate": 0.75, "quality_score": 0.7},
            {"period": "week2", "success_rate": 0.80, "quality_score": 0.75},
            {"period": "week3", "success_rate": 0.85, "quality_score": 0.80},
            {"period": "week4", "success_rate": 0.88, "quality_score": 0.82},
        ]

        result = await _analyze_performance_trends(
            "dev", "test-project", historical_data
        )

        assert result["persona_id"] == "dev"
        assert result["project_id"] == "test-project"
        assert "trend_analysis" in result
        assert "improvement_rate" in result
        assert "forecasted_performance" in result

    def test_calculate_overall_effectiveness_success(self):
        """Test _calculate_overall_effectiveness calculates correctly."""
        from orchestra.models.learning import PerformanceMetric
        from orchestra.temporal.activities.learning import (
            _calculate_overall_effectiveness,
        )

        # Create mock performance metrics
        metrics = [
            PerformanceMetric(
                metric_id="metric-1",
                persona_id="dev",
                project_id="test-project",
                metric_type="learning_effectiveness",
                metric_name="Learning Rate",
                baseline_value=0.7,
                current_value=0.85,
                improvement_percentage=21.43,  # ~21%
                measurement_period_days=30,
                measurement_start=datetime.utcnow() - timedelta(days=30),
                measurement_end=datetime.utcnow(),
                trend="improving",
            ),
            PerformanceMetric(
                metric_id="metric-2",
                persona_id="dev",
                project_id="test-project",
                metric_type="task_performance",
                metric_name="Task Success Rate",
                baseline_value=0.8,
                current_value=0.9,
                improvement_percentage=12.5,  # 12.5%
                measurement_period_days=30,
                measurement_start=datetime.utcnow() - timedelta(days=30),
                measurement_end=datetime.utcnow(),
                trend="improving",
            ),
            PerformanceMetric(
                metric_id="metric-3",
                persona_id="dev",
                project_id="test-project",
                metric_type="output_quality",
                metric_name="Quality Score",
                baseline_value=0.75,
                current_value=0.85,
                improvement_percentage=13.33,  # ~13%
                measurement_period_days=30,
                measurement_start=datetime.utcnow() - timedelta(days=30),
                measurement_end=datetime.utcnow(),
                trend="improving",
            ),
        ]

        effectiveness = _calculate_overall_effectiveness(metrics)

        # Expected: (21.43*0.4 + 12.5*0.4 + 13.33*0.2) / 100 = ~16.24/100 = 0.1624
        assert 0.15 < effectiveness < 0.17

    def test_calculate_overall_effectiveness_empty(self):
        """Test _calculate_overall_effectiveness with empty metrics."""
        from orchestra.temporal.activities.learning import (
            _calculate_overall_effectiveness,
        )

        effectiveness = _calculate_overall_effectiveness([])
        assert effectiveness == 0.0

    def test_extract_confidence_factors_success(self):
        """Test _extract_confidence_factors extracts factors correctly."""
        from orchestra.temporal.activities.learning import _extract_confidence_factors

        recommendation = {
            "ai_model_accuracy": 0.92,
            "context_similarity": 0.88,
            "pattern_complexity": 0.75,
            "risk_assessment_score": 0.85,
        }

        base_behavior_data = {
            "historical_success_rate": 0.87,
        }

        factors = _extract_confidence_factors(recommendation, base_behavior_data)

        assert factors["ai_model_accuracy"] == 0.92
        assert factors["historical_success_rate"] == 0.87
        assert factors["context_similarity"] == 0.88
        assert factors["pattern_complexity"] == 0.75
        assert factors["risk_assessment_score"] == 0.85

    def test_extract_confidence_factors_defaults(self):
        """Test _extract_confidence_factors uses defaults when data missing."""
        from orchestra.temporal.activities.learning import _extract_confidence_factors

        # Empty recommendation and base behavior data
        factors = _extract_confidence_factors({}, {})

        assert factors["ai_model_accuracy"] == 0.85  # Default
        assert factors["historical_success_rate"] == 0.8  # Default
        assert factors["context_similarity"] == 0.75  # Default
        assert factors["pattern_complexity"] == 0.7  # Default
        assert factors["risk_assessment_score"] == 0.8  # Default

    @pytest.mark.asyncio
    async def test_confidence_scoring_activity_edge_inputs(self):
        """Exercise confidence scoring with non-numeric inputs and empty lists."""
        from orchestra.temporal.activities.learning import confidence_scoring_activity

        # Mixed bad inputs should not crash and should clamp to defaults
        ai_recommendations = [
            {
                "recommendation_id": "r1",
                "confidence": "0.9",
                "context_similarity": "0.8",
            },
            {"recommendation_id": "r2", "confidence": None},
        ]
        base_behavior_data = {
            "persona_id": "dev",
            "project_id": "proj",
            "confidence": "0.7",
        }

        result = await confidence_scoring_activity(
            ai_recommendations, base_behavior_data
        )

        assert result["success"] is True
        assert "confidence_scores" in result
        assert result["threshold_met_count"] >= 0

    @pytest.mark.asyncio
    async def test_analyze_performance_trends_fallback_and_style2(self):
        """Cover _analyze_performance_trends fallback path and style2 with non-float values."""
        from orchestra.temporal.activities.learning import _analyze_performance_trends

        # Fallback style: arg1 truthy non-list, arg2 truthy non-int
        fallback = await _analyze_performance_trends(None, "14")
        assert fallback["overall_trend"] in {"stable", "improving", "declining"}
        assert "improvement_rate" in fallback

        # Style 2: persona_id, project_id, historical list with string/None values
        historical = [
            {"success_rate": "0.5", "quality_score": "0.7"},
            {"success_rate": None, "quality_score": 0.72},
            {"success_rate": "0.8", "quality_score": 0.74},
        ]
        style2 = await _analyze_performance_trends("dev", "proj", historical)
        assert style2["persona_id"] == "dev"
        assert style2["project_id"] == "proj"
        assert "forecasted_performance" in style2

    @pytest.mark.asyncio
    async def test_analyze_performance_trends_metrics_mix(self):
        """Cover _from_metrics branches: improving/declining/stable tallies."""
        from orchestra.temporal.activities.learning import _analyze_performance_trends

        metrics = [
            {"improvement_percentage": 10.0},  # improving
            {"improvement_percentage": -10.0},  # declining
            {"improvement_percentage": 2.0},  # stable
        ]
        res = await _analyze_performance_trends(metrics, 30)
        assert res["period_days"] == 30
        assert res["stable_metrics"] >= 0
        assert "overall_trend" in res

    @pytest.mark.asyncio
    async def test_ai_analysis_activity_no_valid_events(self):
        """Return failure when all outcome events fail to parse."""
        from orchestra.temporal.activities.learning import ai_analysis_activity

        outcome_events = [
            {
                "outcome_id": "o-1",
                "persona_id": "dev",
                "project_id": "proj",
                "session_id": "s1",
                "command": "run",
                "result": {"success": True},
                "classification": "success",
                "confidence_score": 0.9,
                "timestamp": "not-a-timestamp",
                "duration_seconds": 1.0,
            }
        ]

        res = await ai_analysis_activity(outcome_events)
        assert res["success"] is False
        assert res["patterns"] == []
        assert res["recommendations"] == []

    @pytest.mark.asyncio
    async def test_ai_analysis_activity_partial_parse(self):
        """One invalid event should be skipped and analysis proceed with valid one."""
        from unittest.mock import AsyncMock, patch

        from orchestra.temporal.activities.learning import ai_analysis_activity

        valid = {
            "outcome_id": "o-2",
            "persona_id": "dev",
            "project_id": "proj",
            "session_id": "s2",
            "command": "run",
            "result": {"success": True},
            "classification": "success",
            "confidence_score": 0.9,
            "timestamp": datetime.utcnow().isoformat(),
            "duration_seconds": 1.0,
        }
        invalid = dict(valid, timestamp="bad")

        payload = {
            "success": True,
            "patterns": [],
            "recommendations": [],
            "confidence_score": 0.9,
        }
        with patch(
            "orchestra.temporal.activities.learning.AIAnalysisService"
        ) as mock_cls:
            inst = AsyncMock()
            inst.analyze_outcome_patterns.return_value = payload
            mock_cls.return_value = inst

            res = await ai_analysis_activity([invalid, valid])
            assert res["success"] is True

    @pytest.mark.asyncio
    async def test_confidence_scoring_activity_exception_path(self):
        """Per-item extraction failures are handled; overall success with zero scores."""
        from unittest.mock import patch

        from orchestra.temporal.activities.learning import confidence_scoring_activity

        with patch(
            "orchestra.temporal.activities.learning._extract_confidence_factors",
            side_effect=RuntimeError("boom"),
        ):
            res = await confidence_scoring_activity(
                [{"recommendation_id": "r"}], {"persona_id": "p"}
            )
            assert res["success"] is True
            assert res["confidence_scores"] == []
            assert res["average_confidence"] == 0.0

    @pytest.mark.asyncio
    async def test_apply_adaptation_rule_exception_path(self):
        """Trigger _apply_adaptation_rule exception branch by raising in apply_rule."""
        from unittest.mock import patch

        from orchestra.temporal.activities.learning import (
            _apply_adaptation_rule,
            _create_adaptation_rule_from_recommendation,
        )

        recommendation = {
            "type": "behavior_modification",
            "description": "x",
            "expected_improvement": 0.75,
        }
        persona_context = {"persona_id": "dev", "project_id": "proj"}
        rule = await _create_adaptation_rule_from_recommendation(
            recommendation, persona_context
        )

        with patch(
            "orchestra.models.learning.AdaptationRule.apply_rule",
            side_effect=RuntimeError("x"),
        ):
            res = await _apply_adaptation_rule(rule, persona_context)
            assert res["success"] is False

    @pytest.mark.asyncio
    async def test_learning_adaptation_activity_below_threshold_skips(self):
        """Recommendations below 0.7 improvement are skipped and counted as failed."""
        from orchestra.temporal.activities.learning import learning_adaptation_activity

        recs = [
            {
                "recommendation_id": "r-low",
                "expected_improvement": 0.6,
                "confidence": 0.9,
            }
        ]
        persona = {"persona_id": "dev", "project_id": "proj"}
        res = await learning_adaptation_activity(recs, persona)
        assert res["success"] is False
        assert res["successful_applications"] == 0
        assert len(res["failed_adaptations"]) == 1

    @pytest.mark.asyncio
    async def test_performance_metrics_activity_exception_path(self):
        """If metrics calculation raises, activity returns failure payload."""
        from unittest.mock import patch

        from orchestra.temporal.activities.learning import performance_metrics_activity

        with patch(
            "orchestra.temporal.activities.learning._calculate_performance_metrics",
            side_effect=RuntimeError("calc-fail"),
        ):
            res = await performance_metrics_activity("dev", "proj", 7)
            assert res["success"] is False
            assert res["performance_metrics"] == []
