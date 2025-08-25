"""Tests for learning data models based on Story 2.2 PRD requirements."""

from datetime import datetime, timedelta

import pytest

from orchestra.models.learning import (
    AdaptationRule,
    ConfidenceScore,
    LearningPattern,
    OutcomeEvent,
    PerformanceMetric,
)


class TestOutcomeEvent:
    """Test OutcomeEvent data model for success/failure tracking (AC: 1)."""

    def test_outcome_event_success_creation(self):
        """Test OutcomeEvent creation for successful persona interactions."""
        outcome = OutcomeEvent(
            outcome_id="outcome-success-1",
            persona_id="dev",
            project_id="test-project",
            session_id="session-123",
            command="implement-story",
            result={
                "success": True,
                "files_created": ["auth.py", "test_auth.py"],
                "tests_passed": 15,
                "coverage": 0.92,
                "quality_score": 0.88,
            },
            classification="success",
            confidence_score=0.95,
            timestamp=datetime.utcnow(),
            duration_seconds=45.2,
            metadata={
                "success_indicators": [
                    "high_coverage",
                    "tests_passed",
                    "quality_metrics",
                ],
                "domain": "authentication",
                "complexity": "medium",
            },
        )

        assert outcome.outcome_id == "outcome-success-1"
        assert outcome.persona_id == "dev"
        assert outcome.project_id == "test-project"
        assert outcome.classification == "success"
        assert outcome.confidence_score == 0.95
        assert outcome.result["success"] is True
        assert outcome.duration_seconds == 45.2
        assert "success_indicators" in outcome.metadata

    def test_outcome_event_failure_creation(self):
        """Test OutcomeEvent creation for failed persona interactions."""
        outcome = OutcomeEvent(
            outcome_id="outcome-failure-1",
            persona_id="dev",
            project_id="test-project",
            session_id="session-456",
            command="implement-story",
            result={
                "success": False,
                "error": "Compilation failed due to syntax errors",
                "error_type": "syntax_error",
                "failed_tests": 3,
                "error_details": {
                    "file": "auth.py",
                    "line": 42,
                    "message": "Unexpected token",
                },
            },
            classification="failure",
            confidence_score=0.92,
            timestamp=datetime.utcnow(),
            duration_seconds=120.5,
            metadata={
                "failure_indicators": ["compilation_error", "failed_tests"],
                "error_patterns": ["syntax_error"],
                "domain": "authentication",
            },
        )

        assert outcome.outcome_id == "outcome-failure-1"
        assert outcome.classification == "failure"
        assert outcome.result["success"] is False
        assert outcome.result["error_type"] == "syntax_error"
        assert "failure_indicators" in outcome.metadata

    def test_outcome_event_classification_validation(self):
        """Test OutcomeEvent validates classification values."""
        # Valid classifications
        valid_classifications = [
            "success",
            "failure",
            "partial_success",
            "timeout",
            "error",
        ]

        for classification in valid_classifications:
            outcome = OutcomeEvent(
                outcome_id=f"outcome-{classification}",
                persona_id="dev",
                project_id="test-project",
                session_id="session-test",
                command="test-command",
                result={"success": classification == "success"},
                classification=classification,
                confidence_score=0.8,
                timestamp=datetime.utcnow(),
                duration_seconds=30.0,
            )
            assert outcome.classification == classification

        # Invalid classification
        with pytest.raises(ValueError, match="Invalid classification"):
            OutcomeEvent(
                outcome_id="outcome-invalid",
                persona_id="dev",
                project_id="test-project",
                session_id="session-test",
                command="test-command",
                result={"success": False},
                classification="invalid_classification",
                confidence_score=0.8,
                timestamp=datetime.utcnow(),
                duration_seconds=30.0,
            )

    def test_outcome_event_security_integration(self):
        """Test OutcomeEvent integrates with security and audit logging."""
        outcome = OutcomeEvent(
            outcome_id="outcome-security-1",
            persona_id="dev",
            project_id="test-project",
            session_id="session-security",
            command="implement-story",
            result={"success": True},
            classification="success",
            confidence_score=0.88,
            timestamp=datetime.utcnow(),
            duration_seconds=60.0,
            security_context={
                "user_id": "user-123",
                "permissions": ["code_write", "test_execute"],
                "audit_required": True,
            },
            audit_logged=True,
        )

        assert outcome.security_context["user_id"] == "user-123"
        assert outcome.security_context["audit_required"] is True
        assert outcome.audit_logged is True


class TestLearningPattern:
    """Test LearningPattern data model for identified patterns (AC: 2, 7)."""

    def test_learning_pattern_creation(self):
        """Test LearningPattern creation with AI-identified patterns."""
        pattern = LearningPattern(
            pattern_id="auth-success-pattern-1",
            project_id="test-project",
            persona_id="dev",
            pattern_type="success_pattern",
            description="High test coverage leads to successful authentication implementations",
            pattern_data={
                "conditions": [
                    {"metric": "test_coverage", "operator": ">=", "value": 0.90},
                    {"metric": "security_validation", "operator": "==", "value": True},
                ],
                "outcomes": [
                    {"metric": "success_rate", "value": 0.92},
                    {"metric": "error_rate", "value": 0.05},
                ],
            },
            confidence_score=0.89,
            effectiveness_score=0.85,
            accuracy_score=0.87,  # AC: 7 - >85% accuracy requirement
            usage_count=12,
            last_applied=datetime.utcnow(),
            created_at=datetime.utcnow(),
            ai_model="gpt-4",
            ai_confidence=0.91,
        )

        assert pattern.pattern_id == "auth-success-pattern-1"
        assert pattern.pattern_type == "success_pattern"
        assert pattern.accuracy_score > 0.85  # AC: 7 - >85% accuracy
        assert pattern.effectiveness_score == 0.85
        assert pattern.ai_model == "gpt-4"
        assert "conditions" in pattern.pattern_data

    def test_learning_pattern_types(self):
        """Test LearningPattern supports different pattern types."""
        success_pattern = LearningPattern(
            pattern_id="success-1",
            project_id="test-project",
            persona_id="dev",
            pattern_type="success_pattern",
            description="Success pattern description",
            pattern_data={"success_indicators": ["high_quality", "fast_completion"]},
            confidence_score=0.9,
            effectiveness_score=0.85,
            accuracy_score=0.88,
            usage_count=10,
            last_applied=datetime.utcnow(),
            created_at=datetime.utcnow(),
        )

        failure_pattern = LearningPattern(
            pattern_id="failure-1",
            project_id="test-project",
            persona_id="dev",
            pattern_type="failure_pattern",
            description="Common failure pattern to avoid",
            pattern_data={"failure_indicators": ["low_coverage", "missing_validation"]},
            confidence_score=0.85,
            effectiveness_score=0.80,
            accuracy_score=0.86,
            usage_count=5,
            last_applied=datetime.utcnow(),
            created_at=datetime.utcnow(),
        )

        optimization_pattern = LearningPattern(
            pattern_id="optimization-1",
            project_id="test-project",
            persona_id="dev",
            pattern_type="optimization_pattern",
            description="Performance optimization pattern",
            pattern_data={"optimization_techniques": ["caching", "lazy_loading"]},
            confidence_score=0.82,
            effectiveness_score=0.78,
            accuracy_score=0.87,
            usage_count=8,
            last_applied=datetime.utcnow(),
            created_at=datetime.utcnow(),
        )

        assert success_pattern.pattern_type == "success_pattern"
        assert failure_pattern.pattern_type == "failure_pattern"
        assert optimization_pattern.pattern_type == "optimization_pattern"

    def test_learning_pattern_accuracy_validation(self):
        """Test LearningPattern validates accuracy requirements."""
        # Test pattern meeting accuracy requirement (>85%)
        high_accuracy_pattern = LearningPattern(
            pattern_id="high-accuracy",
            project_id="test-project",
            persona_id="dev",
            pattern_type="success_pattern",
            description="High accuracy pattern",
            pattern_data={},
            confidence_score=0.9,
            effectiveness_score=0.85,
            accuracy_score=0.88,  # AC: 7 - >85% accuracy
            usage_count=5,
            last_applied=datetime.utcnow(),
            created_at=datetime.utcnow(),
        )
        assert high_accuracy_pattern.accuracy_score > 0.85

        # Test pattern below accuracy requirement
        with pytest.raises(ValueError, match="accuracy_score must be > 0.85"):
            LearningPattern(
                pattern_id="low-accuracy",
                project_id="test-project",
                persona_id="dev",
                pattern_type="success_pattern",
                description="Low accuracy pattern",
                pattern_data={},
                confidence_score=0.9,
                effectiveness_score=0.85,
                accuracy_score=0.75,  # Below 85% requirement
                usage_count=5,
                last_applied=datetime.utcnow(),
                created_at=datetime.utcnow(),
            )

    def test_learning_pattern_ai_integration(self):
        """Test LearningPattern integrates with AI analysis."""
        pattern = LearningPattern(
            pattern_id="ai-pattern",
            project_id="test-project",
            persona_id="dev",
            pattern_type="success_pattern",
            description="AI-identified success pattern",
            pattern_data={},
            confidence_score=0.9,
            effectiveness_score=0.85,
            accuracy_score=0.89,
            usage_count=3,
            last_applied=datetime.utcnow(),
            created_at=datetime.utcnow(),
            ai_model="gpt-4",
            ai_confidence=0.93,
            ai_request_id="req-abc123",
            ai_tokens_used=1250,
        )

        assert pattern.ai_model == "gpt-4"
        assert pattern.ai_confidence == 0.93
        assert pattern.ai_request_id == "req-abc123"
        assert pattern.ai_tokens_used == 1250


class TestAdaptationRule:
    """Test AdaptationRule data model for behavior modification (AC: 3, 8)."""

    def test_adaptation_rule_creation(self):
        """Test AdaptationRule creation for persona behavior modification."""
        rule = AdaptationRule(
            rule_id="auth-validation-rule",
            persona_id="dev",
            project_id="test-project",
            rule_type="behavior_modification",
            description="Add validation step before authentication implementation",
            condition="command == 'implement-story' AND domain == 'authentication'",
            action="run_validation_checks_first",
            priority="high",
            confidence_score=0.88,
            expected_improvement=0.75,  # AC: 8 - >70% improvement rate
            active=True,
            created_at=datetime.utcnow(),
            applied_at=None,
            source_pattern_id="auth-success-pattern-1",
        )

        assert rule.rule_id == "auth-validation-rule"
        assert rule.persona_id == "dev"
        assert rule.rule_type == "behavior_modification"
        assert rule.expected_improvement > 0.7  # AC: 8 - >70% improvement rate
        assert rule.active is True
        assert rule.priority == "high"

    def test_adaptation_rule_types(self):
        """Test AdaptationRule supports different rule types."""
        behavior_rule = AdaptationRule(
            rule_id="behavior-rule",
            persona_id="dev",
            project_id="test-project",
            rule_type="behavior_modification",
            description="Modify behavior pattern",
            condition="command == 'implement'",
            action="add_extra_validation",
            priority="medium",
            confidence_score=0.85,
            expected_improvement=0.72,
            active=True,
            created_at=datetime.utcnow(),
        )

        workflow_rule = AdaptationRule(
            rule_id="workflow-rule",
            persona_id="dev",
            project_id="test-project",
            rule_type="workflow_modification",
            description="Modify workflow sequence",
            condition="task_complexity == 'high'",
            action="enable_peer_review_step",
            priority="high",
            confidence_score=0.90,
            expected_improvement=0.80,
            active=True,
            created_at=datetime.utcnow(),
        )

        parameter_rule = AdaptationRule(
            rule_id="parameter-rule",
            persona_id="dev",
            project_id="test-project",
            rule_type="parameter_adjustment",
            description="Adjust parameter values",
            condition="domain == 'performance'",
            action="increase_timeout_threshold",
            priority="low",
            confidence_score=0.75,
            expected_improvement=0.72,
            active=True,
            created_at=datetime.utcnow(),
        )

        assert behavior_rule.rule_type == "behavior_modification"
        assert workflow_rule.rule_type == "workflow_modification"
        assert parameter_rule.rule_type == "parameter_adjustment"

    def test_adaptation_rule_improvement_validation(self):
        """Test AdaptationRule validates improvement rate requirements."""
        # Test rule meeting improvement requirement (>70%)
        high_improvement_rule = AdaptationRule(
            rule_id="high-improvement",
            persona_id="dev",
            project_id="test-project",
            rule_type="behavior_modification",
            description="High improvement rule",
            condition="test_condition",
            action="test_action",
            priority="medium",
            confidence_score=0.85,
            expected_improvement=0.75,  # AC: 8 - >70% improvement rate
            active=True,
            created_at=datetime.utcnow(),
        )
        assert high_improvement_rule.expected_improvement > 0.7

        # Test rule below improvement requirement
        with pytest.raises(ValueError, match="expected_improvement must be > 0.7"):
            AdaptationRule(
                rule_id="low-improvement",
                persona_id="dev",
                project_id="test-project",
                rule_type="behavior_modification",
                description="Low improvement rule",
                condition="test_condition",
                action="test_action",
                priority="medium",
                confidence_score=0.85,
                expected_improvement=0.65,  # Below 70% requirement
                active=True,
                created_at=datetime.utcnow(),
            )

    def test_adaptation_rule_rollback_support(self):
        """Test AdaptationRule supports rollback mechanisms."""
        rule = AdaptationRule(
            rule_id="rollback-rule",
            persona_id="dev",
            project_id="test-project",
            rule_type="behavior_modification",
            description="Rule with rollback support",
            condition="test_condition",
            action="test_action",
            priority="medium",
            confidence_score=0.85,
            expected_improvement=0.75,
            active=True,
            created_at=datetime.utcnow(),
            rollback_data={
                "original_behavior": "original_action",
                "rollback_condition": "performance_degradation > 0.1",
                "rollback_enabled": True,
            },
        )

        assert rule.rollback_data["rollback_enabled"] is True
        assert "original_behavior" in rule.rollback_data

        # Test rollback execution
        rule.execute_rollback()
        assert rule.active is False
        assert rule.rollback_executed is True


class TestPerformanceMetric:
    """Test PerformanceMetric data model for effectiveness tracking (AC: 4)."""

    def test_performance_metric_creation(self):
        """Test PerformanceMetric creation for learning effectiveness tracking."""
        metric = PerformanceMetric(
            metric_id="perf-metric-1",
            persona_id="dev",
            project_id="test-project",
            metric_type="learning_effectiveness",
            metric_name="Success Rate Improvement",
            baseline_value=0.75,
            current_value=0.85,
            improvement_percentage=13.33,
            measurement_period_days=30,
            measurement_start=datetime.utcnow() - timedelta(days=30),
            measurement_end=datetime.utcnow(),
            trend="improving",
            confidence_interval=[0.82, 0.88],
            created_at=datetime.utcnow(),
        )

        assert metric.metric_id == "perf-metric-1"
        assert metric.persona_id == "dev"
        assert metric.metric_type == "learning_effectiveness"
        assert metric.baseline_value == 0.75
        assert metric.current_value == 0.85
        assert metric.improvement_percentage == 13.33
        assert metric.trend == "improving"

    def test_performance_metric_types(self):
        """Test PerformanceMetric supports different metric types."""
        effectiveness_metric = PerformanceMetric(
            metric_id="effectiveness-1",
            persona_id="dev",
            project_id="test-project",
            metric_type="learning_effectiveness",
            metric_name="Overall Learning Effectiveness",
            baseline_value=0.70,
            current_value=0.82,
            improvement_percentage=17.14,
            measurement_period_days=30,
            measurement_start=datetime.utcnow() - timedelta(days=30),
            measurement_end=datetime.utcnow(),
            trend="improving",
            created_at=datetime.utcnow(),
        )

        performance_metric = PerformanceMetric(
            metric_id="performance-1",
            persona_id="dev",
            project_id="test-project",
            metric_type="task_performance",
            metric_name="Average Completion Time",
            baseline_value=120.0,
            current_value=95.0,
            improvement_percentage=20.83,
            measurement_period_days=30,
            measurement_start=datetime.utcnow() - timedelta(days=30),
            measurement_end=datetime.utcnow(),
            trend="improving",
            created_at=datetime.utcnow(),
        )

        quality_metric = PerformanceMetric(
            metric_id="quality-1",
            persona_id="dev",
            project_id="test-project",
            metric_type="output_quality",
            metric_name="Code Quality Score",
            baseline_value=0.78,
            current_value=0.88,
            improvement_percentage=12.82,
            measurement_period_days=30,
            measurement_start=datetime.utcnow() - timedelta(days=30),
            measurement_end=datetime.utcnow(),
            trend="improving",
            created_at=datetime.utcnow(),
        )

        assert effectiveness_metric.metric_type == "learning_effectiveness"
        assert performance_metric.metric_type == "task_performance"
        assert quality_metric.metric_type == "output_quality"

    def test_performance_metric_trend_analysis(self):
        """Test PerformanceMetric provides trending analysis."""
        # Improving trend
        improving_metric = PerformanceMetric(
            metric_id="improving-1",
            persona_id="dev",
            project_id="test-project",
            metric_type="learning_effectiveness",
            metric_name="Success Rate",
            baseline_value=0.70,
            current_value=0.85,
            improvement_percentage=21.43,
            measurement_period_days=30,
            measurement_start=datetime.utcnow() - timedelta(days=30),
            measurement_end=datetime.utcnow(),
            trend="improving",
            trend_confidence=0.88,
            created_at=datetime.utcnow(),
        )

        # Stable trend
        stable_metric = PerformanceMetric(
            metric_id="stable-1",
            persona_id="dev",
            project_id="test-project",
            metric_type="learning_effectiveness",
            metric_name="Error Rate",
            baseline_value=0.15,
            current_value=0.14,
            improvement_percentage=6.67,
            measurement_period_days=30,
            measurement_start=datetime.utcnow() - timedelta(days=30),
            measurement_end=datetime.utcnow(),
            trend="stable",
            trend_confidence=0.75,
            created_at=datetime.utcnow(),
        )

        # Declining trend
        declining_metric = PerformanceMetric(
            metric_id="declining-1",
            persona_id="dev",
            project_id="test-project",
            metric_type="learning_effectiveness",
            metric_name="Response Time",
            baseline_value=50.0,
            current_value=65.0,
            improvement_percentage=-30.0,  # Negative improvement (degradation)
            measurement_period_days=30,
            measurement_start=datetime.utcnow() - timedelta(days=30),
            measurement_end=datetime.utcnow(),
            trend="declining",
            trend_confidence=0.82,
            created_at=datetime.utcnow(),
        )

        assert improving_metric.trend == "improving"
        assert improving_metric.improvement_percentage > 0
        assert stable_metric.trend == "stable"
        assert declining_metric.trend == "declining"
        assert declining_metric.improvement_percentage < 0

    def test_performance_metric_forecasting(self):
        """Test PerformanceMetric supports performance forecasting."""
        metric = PerformanceMetric(
            metric_id="forecast-1",
            persona_id="dev",
            project_id="test-project",
            metric_type="learning_effectiveness",
            metric_name="Success Rate with Forecasting",
            baseline_value=0.75,
            current_value=0.85,
            improvement_percentage=13.33,
            measurement_period_days=30,
            measurement_start=datetime.utcnow() - timedelta(days=30),
            measurement_end=datetime.utcnow(),
            trend="improving",
            forecast_data={
                "next_30_days": {
                    "predicted_value": 0.87,
                    "confidence_interval": [0.82, 0.92],
                    "prediction_confidence": 0.85,
                },
                "next_60_days": {
                    "predicted_value": 0.89,
                    "confidence_interval": [0.80, 0.95],
                    "prediction_confidence": 0.78,
                },
            },
            created_at=datetime.utcnow(),
        )

        assert "next_30_days" in metric.forecast_data
        assert metric.forecast_data["next_30_days"]["predicted_value"] == 0.87
        assert metric.forecast_data["next_30_days"]["prediction_confidence"] == 0.85


class TestConfidenceScore:
    """Test ConfidenceScore data model for weighting decisions (AC: 5)."""

    def test_confidence_score_creation(self):
        """Test ConfidenceScore creation for AI recommendation weighting."""
        confidence = ConfidenceScore(
            score_id="conf-score-1",
            persona_id="dev",
            project_id="test-project",
            recommendation_id="rec-123",
            ai_confidence=0.92,
            base_behavior_confidence=0.85,
            weighted_confidence=0.88,
            weighting_algorithm="adaptive_weighted_average",
            factors={
                "ai_model_accuracy": 0.91,
                "historical_success_rate": 0.87,
                "pattern_match_strength": 0.89,
                "context_similarity": 0.85,
            },
            threshold_met=True,
            confidence_threshold=0.80,
            created_at=datetime.utcnow(),
        )

        assert confidence.score_id == "conf-score-1"
        assert confidence.ai_confidence == 0.92
        assert confidence.base_behavior_confidence == 0.85
        assert confidence.weighted_confidence == 0.88
        assert confidence.threshold_met is True
        assert "ai_model_accuracy" in confidence.factors

    def test_confidence_score_weighting_algorithms(self):
        """Test ConfidenceScore supports different weighting algorithms."""
        # Simple average weighting
        simple_confidence = ConfidenceScore(
            score_id="simple-conf",
            persona_id="dev",
            project_id="test-project",
            recommendation_id="rec-simple",
            ai_confidence=0.90,
            base_behavior_confidence=0.80,
            weighted_confidence=0.85,  # (0.90 + 0.80) / 2
            weighting_algorithm="simple_average",
            factors={},
            threshold_met=True,
            confidence_threshold=0.75,
            created_at=datetime.utcnow(),
        )

        # Weighted average with AI bias
        ai_biased_confidence = ConfidenceScore(
            score_id="ai-biased-conf",
            persona_id="dev",
            project_id="test-project",
            recommendation_id="rec-ai-biased",
            ai_confidence=0.95,
            base_behavior_confidence=0.75,
            weighted_confidence=0.89,  # AI weighted higher
            weighting_algorithm="ai_weighted_average",
            factors={"ai_weight": 0.7, "base_weight": 0.3},
            threshold_met=True,
            confidence_threshold=0.80,
            created_at=datetime.utcnow(),
        )

        # Conservative weighting (lower of the two)
        conservative_confidence = ConfidenceScore(
            score_id="conservative-conf",
            persona_id="dev",
            project_id="test-project",
            recommendation_id="rec-conservative",
            ai_confidence=0.92,
            base_behavior_confidence=0.78,
            weighted_confidence=0.78,  # Conservative: min(ai, base)
            weighting_algorithm="conservative_minimum",
            factors={},
            threshold_met=False,  # Below threshold
            confidence_threshold=0.80,
            created_at=datetime.utcnow(),
        )

        assert simple_confidence.weighting_algorithm == "simple_average"
        assert ai_biased_confidence.weighting_algorithm == "ai_weighted_average"
        assert conservative_confidence.weighting_algorithm == "conservative_minimum"
        assert conservative_confidence.threshold_met is False

    def test_confidence_score_threshold_management(self):
        """Test ConfidenceScore manages thresholds for adaptation decisions."""
        # Above threshold - should be applied
        high_confidence = ConfidenceScore(
            score_id="high-conf",
            persona_id="dev",
            project_id="test-project",
            recommendation_id="rec-high",
            ai_confidence=0.95,
            base_behavior_confidence=0.88,
            weighted_confidence=0.91,
            weighting_algorithm="adaptive_weighted_average",
            factors={},
            threshold_met=True,
            confidence_threshold=0.85,
            created_at=datetime.utcnow(),
        )

        # Below threshold - should be rejected
        low_confidence = ConfidenceScore(
            score_id="low-conf",
            persona_id="dev",
            project_id="test-project",
            recommendation_id="rec-low",
            ai_confidence=0.75,
            base_behavior_confidence=0.70,
            weighted_confidence=0.72,
            weighting_algorithm="simple_average",
            factors={},
            threshold_met=False,
            confidence_threshold=0.85,
            created_at=datetime.utcnow(),
        )

        assert high_confidence.should_apply_recommendation() is True
        assert low_confidence.should_apply_recommendation() is False
        assert (
            high_confidence.weighted_confidence > high_confidence.confidence_threshold
        )
        assert low_confidence.weighted_confidence < low_confidence.confidence_threshold

    def test_confidence_score_dynamic_thresholds(self):
        """Test ConfidenceScore supports dynamic threshold adjustment."""
        confidence = ConfidenceScore(
            score_id="dynamic-conf",
            persona_id="dev",
            project_id="test-project",
            recommendation_id="rec-dynamic",
            ai_confidence=0.88,
            base_behavior_confidence=0.82,
            weighted_confidence=0.85,
            weighting_algorithm="adaptive_weighted_average",
            factors={},
            threshold_met=True,
            confidence_threshold=0.80,
            dynamic_threshold_data={
                "base_threshold": 0.80,
                "risk_adjustment": -0.05,  # Lower threshold for low-risk changes
                "context_adjustment": 0.02,  # Higher threshold for critical context
                "final_threshold": 0.77,
            },
            created_at=datetime.utcnow(),
        )

        assert "dynamic_threshold_data" in confidence.__dict__
        assert confidence.dynamic_threshold_data["final_threshold"] == 0.77
        assert (
            confidence.weighted_confidence
            > confidence.dynamic_threshold_data["final_threshold"]
        )


class TestLearningModelIntegration:
    """Test integration between learning data models."""

    def test_learning_models_complete_cycle(self):
        """Test learning models work together in a complete learning cycle."""
        # Step 1: Outcome Event
        outcome = OutcomeEvent(
            outcome_id="cycle-outcome",
            persona_id="dev",
            project_id="integration-project",
            session_id="integration-session",
            command="implement-story",
            result={"success": True, "quality_score": 0.9},
            classification="success",
            confidence_score=0.92,
            timestamp=datetime.utcnow(),
            duration_seconds=75.0,
        )

        # Step 2: Learning Pattern (derived from outcome)
        pattern = LearningPattern(
            pattern_id="cycle-pattern",
            project_id="integration-project",
            persona_id="dev",
            pattern_type="success_pattern",
            description="High quality implementations lead to success",
            pattern_data={"quality_threshold": 0.85},
            confidence_score=0.89,
            effectiveness_score=0.87,
            accuracy_score=0.88,
            usage_count=1,
            last_applied=datetime.utcnow(),
            created_at=datetime.utcnow(),
            source_outcome_id="cycle-outcome",
        )

        # Step 3: Adaptation Rule (derived from pattern)
        rule = AdaptationRule(
            rule_id="cycle-rule",
            persona_id="dev",
            project_id="integration-project",
            rule_type="behavior_modification",
            description="Ensure quality checks before implementation",
            condition="command == 'implement-story'",
            action="run_quality_checks_first",
            priority="medium",
            confidence_score=0.85,
            expected_improvement=0.75,
            active=True,
            created_at=datetime.utcnow(),
            source_pattern_id="cycle-pattern",
        )

        # Step 4: Performance Metric (tracking rule effectiveness)
        metric = PerformanceMetric(
            metric_id="cycle-metric",
            persona_id="dev",
            project_id="integration-project",
            metric_type="learning_effectiveness",
            metric_name="Quality-driven Success Rate",
            baseline_value=0.75,
            current_value=0.87,
            improvement_percentage=16.0,
            measurement_period_days=14,
            measurement_start=datetime.utcnow() - timedelta(days=14),
            measurement_end=datetime.utcnow(),
            trend="improving",
            created_at=datetime.utcnow(),
            source_rule_id="cycle-rule",
        )

        # Step 5: Confidence Score (for future decisions)
        confidence = ConfidenceScore(
            score_id="cycle-confidence",
            persona_id="dev",
            project_id="integration-project",
            recommendation_id="future-rec",
            ai_confidence=0.90,
            base_behavior_confidence=0.82,
            weighted_confidence=0.86,
            weighting_algorithm="adaptive_weighted_average",
            factors={"historical_effectiveness": 0.87},
            threshold_met=True,
            confidence_threshold=0.80,
            created_at=datetime.utcnow(),
        )

        # Test relationships and consistency
        assert outcome.project_id == pattern.project_id == rule.project_id
        assert outcome.persona_id == pattern.persona_id == rule.persona_id
        assert pattern.source_outcome_id == outcome.outcome_id
        assert rule.source_pattern_id == pattern.pattern_id
        assert metric.source_rule_id == rule.rule_id

        # Test learning effectiveness
        assert pattern.accuracy_score > 0.85  # AC: 7
        assert rule.expected_improvement > 0.7  # AC: 8
        assert metric.improvement_percentage > 0  # Positive improvement
        assert confidence.threshold_met is True  # Confidence threshold met

    def test_learning_models_performance_constraints(self):
        """Test learning models respect performance constraints."""
        # Test that learning operations don't impact persona load times
        start_time = datetime.utcnow()

        # Create multiple learning objects (simulating learning processing)
        outcomes = []
        patterns = []
        rules = []

        for i in range(10):  # Simulate batch processing
            outcome = OutcomeEvent(
                outcome_id=f"perf-outcome-{i}",
                persona_id="dev",
                project_id="perf-project",
                session_id=f"perf-session-{i}",
                command="implement-story",
                result={"success": True},
                classification="success",
                confidence_score=0.85,
                timestamp=datetime.utcnow(),
                duration_seconds=30.0,
            )
            outcomes.append(outcome)

            pattern = LearningPattern(
                pattern_id=f"perf-pattern-{i}",
                project_id="perf-project",
                persona_id="dev",
                pattern_type="success_pattern",
                description=f"Performance test pattern {i}",
                pattern_data={},
                confidence_score=0.85,
                effectiveness_score=0.80,
                accuracy_score=0.87,
                usage_count=1,
                last_applied=datetime.utcnow(),
                created_at=datetime.utcnow(),
            )
            patterns.append(pattern)

            rule = AdaptationRule(
                rule_id=f"perf-rule-{i}",
                persona_id="dev",
                project_id="perf-project",
                rule_type="behavior_modification",
                description=f"Performance test rule {i}",
                condition="test_condition",
                action="test_action",
                priority="low",
                confidence_score=0.80,
                expected_improvement=0.72,
                active=True,
                created_at=datetime.utcnow(),
            )
            rules.append(rule)

        end_time = datetime.utcnow()
        processing_time_ms = (end_time - start_time).total_seconds() * 1000

        # Learning model creation should be fast (not impact persona load times)
        assert processing_time_ms < 100  # Should be very fast for model creation
        assert len(outcomes) == 10
        assert len(patterns) == 10
        assert len(rules) == 10
