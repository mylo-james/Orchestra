"""Learning data models for Orchestra AI adaptive learning system."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class OutcomeEvent:
    """
    Records success/failure events from persona interactions.

    Captures detailed outcome data for AI-assisted pattern analysis
    and learning effectiveness measurement.
    """

    outcome_id: str
    persona_id: str
    project_id: str
    session_id: str
    command: str
    result: Dict[str, Any]
    classification: str  # success, failure, partial_success, timeout, error
    confidence_score: float
    timestamp: datetime
    duration_seconds: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    security_context: Optional[Dict[str, Any]] = None
    audit_logged: bool = False

    def __post_init__(self):
        """Validate outcome event constraints."""
        valid_classifications = [
            "success",
            "failure",
            "partial_success",
            "timeout",
            "error",
        ]
        if self.classification not in valid_classifications:
            raise ValueError(f"Invalid classification: {self.classification}")

        if not (0.0 <= self.confidence_score <= 1.0):
            raise ValueError("confidence_score must be between 0 and 1")

    def get_success_indicators(self) -> List[str]:
        """Extract success indicators from result data."""
        indicators = []

        if self.result.get("success"):
            if self.result.get("tests_passed", 0) > 0:
                indicators.append("tests_passed")
            if self.result.get("coverage", 0) > 0.8:
                indicators.append("high_coverage")
            if self.result.get("quality_score", 0) > 0.8:
                indicators.append("high_quality")
            if self.result.get("security_validated"):
                indicators.append("security_validated")

        return indicators

    def get_failure_indicators(self) -> List[str]:
        """Extract failure indicators from result data."""
        indicators = []

        if not self.result.get("success"):
            if "error" in self.result:
                indicators.append("error_occurred")
            if self.result.get("failed_tests", 0) > 0:
                indicators.append("failed_tests")
            if self.result.get("coverage", 1.0) < 0.5:
                indicators.append("low_coverage")
            if "compilation" in self.result.get("error", "").lower():
                indicators.append("compilation_error")

        return indicators

    def to_analysis_data(self) -> Dict[str, Any]:
        """Convert to data structure for AI analysis."""
        return {
            "outcome_id": self.outcome_id,
            "persona_id": self.persona_id,
            "command": self.command,
            "classification": self.classification,
            "success_indicators": self.get_success_indicators(),
            "failure_indicators": self.get_failure_indicators(),
            "duration_seconds": self.duration_seconds,
            "confidence_score": self.confidence_score,
            "context": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class LearningPattern:
    """
    AI-identified patterns with confidence and effectiveness scores.

    Stores patterns identified through AI analysis with accuracy
    requirements and usage tracking.
    """

    pattern_id: str
    project_id: str
    persona_id: str
    pattern_type: str  # success_pattern, failure_pattern, optimization_pattern
    description: str
    pattern_data: Dict[str, Any]
    confidence_score: float
    effectiveness_score: float
    accuracy_score: float
    usage_count: int
    last_applied: datetime
    created_at: datetime
    ai_model: Optional[str] = None
    ai_confidence: Optional[float] = None
    ai_request_id: Optional[str] = None
    ai_tokens_used: Optional[int] = None
    source_outcome_id: Optional[str] = None

    def __post_init__(self):
        """Validate learning pattern constraints."""
        if self.accuracy_score <= 0.85:
            raise ValueError("accuracy_score must be > 0.85 for pattern acceptance")

        if not (0.0 <= self.confidence_score <= 1.0):
            raise ValueError("confidence_score must be between 0 and 1")

        if not (0.0 <= self.effectiveness_score <= 1.0):
            raise ValueError("effectiveness_score must be between 0 and 1")

    def apply_pattern(self) -> None:
        """Record pattern application and update usage."""
        self.usage_count += 1
        self.last_applied = datetime.utcnow()

    def get_transferability_score(self, target_persona: str) -> float:
        """Calculate transferability score for target persona."""
        # Base transferability on pattern type and persona compatibility
        base_score = self.effectiveness_score

        # Adjust based on persona similarity
        persona_compatibility = {
            ("dev", "qa"): 0.8,
            ("dev", "architect"): 0.7,
            ("qa", "dev"): 0.75,
            ("architect", "dev"): 0.8,
            ("pm", "po"): 0.9,
        }

        compatibility = persona_compatibility.get(
            (self.persona_id, target_persona), 0.5
        )
        return min(1.0, base_score * compatibility)

    def to_recommendation(self) -> Dict[str, Any]:
        """Convert pattern to AI recommendation format."""
        return {
            "recommendation_id": f"rec-{self.pattern_id}",
            "pattern_id": self.pattern_id,
            "type": "behavior_modification",
            "description": self.description,
            "confidence": self.confidence_score,
            "expected_improvement": self.effectiveness_score,
            "pattern_data": self.pattern_data,
            "ai_analysis": {
                "model": self.ai_model,
                "confidence": self.ai_confidence,
                "accuracy": self.accuracy_score,
            },
        }


@dataclass
class AdaptationRule:
    """
    Rules for behavior modification based on learned patterns.

    Defines conditions and actions for persona behavior adaptation
    with rollback support and improvement tracking.
    """

    rule_id: str
    persona_id: str
    project_id: str
    rule_type: str  # behavior_modification, workflow_modification, parameter_adjustment
    description: str
    condition: str
    action: str
    priority: str  # high, medium, low
    confidence_score: float
    expected_improvement: float
    active: bool
    created_at: datetime
    applied_at: Optional[datetime] = None
    source_pattern_id: Optional[str] = None
    rollback_data: Optional[Dict[str, Any]] = None
    rollback_executed: bool = False

    def __post_init__(self):
        """Validate adaptation rule constraints."""
        if self.expected_improvement <= 0.7:
            raise ValueError("expected_improvement must be > 0.7 for rule acceptance")

        if not (0.0 <= self.confidence_score <= 1.0):
            raise ValueError("confidence_score must be between 0 and 1")

    def apply_rule(self) -> None:
        """Apply the adaptation rule and record application."""
        self.active = True
        self.applied_at = datetime.utcnow()

    def execute_rollback(self) -> None:
        """Execute rollback of the adaptation rule."""
        self.active = False
        self.rollback_executed = True

        if self.rollback_data:
            self.rollback_data["rollback_timestamp"] = datetime.utcnow().isoformat()

    def evaluate_condition(self, context: Dict[str, Any]) -> bool:
        """Evaluate if rule condition is met in given context."""
        # Simple condition evaluation (in production, use proper expression parser)
        try:
            # Replace context variables in condition
            condition = self.condition
            for key, value in context.items():
                condition = condition.replace(key, str(value))

            # Basic evaluation (extend for complex conditions)
            if "==" in condition:
                left, right = condition.split("==")
                return left.strip().strip("'\"") == right.strip().strip("'\"")
            elif ">=" in condition:
                left, right = condition.split(">=")
                return float(left.strip()) >= float(right.strip())

            return False
        except Exception:
            return False

    def get_rollback_plan(self) -> Dict[str, Any]:
        """Get rollback plan for the adaptation rule."""
        return {
            "rule_id": self.rule_id,
            "original_behavior": (
                self.rollback_data.get("original_behavior")
                if self.rollback_data
                else None
            ),
            "rollback_actions": [
                "deactivate_rule",
                "restore_original_behavior",
                "notify_stakeholders",
                "update_learning_metrics",
            ],
            "rollback_conditions": [
                "performance_degradation > 0.1",
                "error_rate_increase > 0.05",
                "user_satisfaction_drop > 0.2",
            ],
        }


@dataclass
class PerformanceMetric:
    """
    Tracks learning effectiveness and improvement trends over time.

    Measures persona performance before and after learning adaptations
    with trend analysis and forecasting capabilities.
    """

    metric_id: str
    persona_id: str
    project_id: str
    metric_type: str  # learning_effectiveness, task_performance, output_quality
    metric_name: str
    baseline_value: float
    current_value: float
    improvement_percentage: float
    measurement_period_days: int
    measurement_start: datetime
    measurement_end: datetime
    trend: str  # improving, stable, declining
    confidence_interval: Optional[List[float]] = None
    trend_confidence: Optional[float] = None
    forecast_data: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    source_rule_id: Optional[str] = None

    def calculate_improvement(self) -> float:
        """Calculate improvement percentage from baseline."""
        if self.baseline_value == 0:
            return 0.0

        improvement = (
            (self.current_value - self.baseline_value) / self.baseline_value
        ) * 100
        self.improvement_percentage = improvement
        return improvement

    def update_trend(self, historical_values: List[float]) -> None:
        """Update trend analysis based on historical values."""
        if len(historical_values) < 3:
            self.trend = "stable"
            return

        # Simple trend analysis (extend with proper statistical methods)
        recent_avg = sum(historical_values[-3:]) / 3
        older_avg = sum(historical_values[:-3]) / max(1, len(historical_values) - 3)

        if recent_avg > older_avg * 1.05:
            self.trend = "improving"
        elif recent_avg < older_avg * 0.95:
            self.trend = "declining"
        else:
            self.trend = "stable"

    def generate_forecast(self, forecast_days: int = 30) -> Dict[str, Any]:
        """Generate performance forecast for specified period."""
        # Simple linear projection (extend with proper forecasting models)
        daily_change = self.improvement_percentage / self.measurement_period_days
        projected_change = daily_change * forecast_days
        projected_value = self.current_value * (1 + projected_change / 100)

        # Calculate confidence interval (simplified)
        confidence_range = abs(projected_value - self.current_value) * 0.2

        forecast = {
            "forecast_period_days": forecast_days,
            "projected_value": projected_value,
            "confidence_interval": [
                projected_value - confidence_range,
                projected_value + confidence_range,
            ],
            "projection_confidence": max(
                0.5, 1.0 - (forecast_days / 90)
            ),  # Decreases with time
        }

        self.forecast_data = forecast
        return forecast

    def is_improving(self) -> bool:
        """Check if metric shows improvement."""
        return self.improvement_percentage > 5.0 and self.trend == "improving"

    def meets_effectiveness_threshold(self, threshold: float = 0.6) -> bool:
        """Check if improvement meets effectiveness threshold."""
        return (self.improvement_percentage / 100) > threshold


@dataclass
class ConfidenceScore:
    """
    Confidence scoring system for AI recommendation weighting.

    Manages confidence weighting between AI recommendations and
    base behavior with threshold-based decision making.
    """

    score_id: str
    persona_id: str
    project_id: str
    recommendation_id: str
    ai_confidence: float
    base_behavior_confidence: float
    weighted_confidence: float
    weighting_algorithm: str
    factors: Dict[str, float]
    threshold_met: bool
    confidence_threshold: float
    dynamic_threshold_data: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Validate confidence score constraints."""
        if not (0.0 <= self.ai_confidence <= 1.0):
            raise ValueError("ai_confidence must be between 0 and 1")

        if not (0.0 <= self.base_behavior_confidence <= 1.0):
            raise ValueError("base_behavior_confidence must be between 0 and 1")

        if not (0.0 <= self.weighted_confidence <= 1.0):
            raise ValueError("weighted_confidence must be between 0 and 1")

    def calculate_weighted_confidence(self) -> float:
        """Calculate weighted confidence based on algorithm."""
        if self.weighting_algorithm == "simple_average":
            self.weighted_confidence = (
                self.ai_confidence + self.base_behavior_confidence
            ) / 2

        elif self.weighting_algorithm == "ai_weighted_average":
            ai_weight = self.factors.get("ai_weight", 0.7)
            base_weight = self.factors.get("base_weight", 0.3)
            self.weighted_confidence = (
                self.ai_confidence * ai_weight
                + self.base_behavior_confidence * base_weight
            )

        elif self.weighting_algorithm == "conservative_minimum":
            self.weighted_confidence = min(
                self.ai_confidence, self.base_behavior_confidence
            )

        elif self.weighting_algorithm == "adaptive_weighted_average":
            # Adaptive weighting based on factors
            ai_accuracy = self.factors.get("ai_model_accuracy", 0.85)
            historical_success = self.factors.get("historical_success_rate", 0.8)
            context_similarity = self.factors.get("context_similarity", 0.75)

            # Weight AI confidence by its accuracy and context
            ai_weight = (ai_accuracy + context_similarity) / 2
            base_weight = historical_success

            total_weight = ai_weight + base_weight
            self.weighted_confidence = (
                self.ai_confidence * ai_weight
                + self.base_behavior_confidence * base_weight
            ) / total_weight

        # Update threshold status
        effective_threshold = self.get_effective_threshold()
        self.threshold_met = self.weighted_confidence >= effective_threshold

        return self.weighted_confidence

    def get_effective_threshold(self) -> float:
        """Get effective threshold considering dynamic adjustments."""
        if not self.dynamic_threshold_data:
            return self.confidence_threshold

        return self.dynamic_threshold_data.get(
            "final_threshold", self.confidence_threshold
        )

    def should_apply_recommendation(self) -> bool:
        """Determine if recommendation should be applied based on confidence."""
        return self.threshold_met

    def update_factors(self, new_factors: Dict[str, float]) -> None:
        """Update confidence factors and recalculate weighted confidence."""
        self.factors.update(new_factors)
        self.calculate_weighted_confidence()

    def get_confidence_breakdown(self) -> Dict[str, Any]:
        """Get detailed confidence score breakdown."""
        return {
            "ai_confidence": self.ai_confidence,
            "base_behavior_confidence": self.base_behavior_confidence,
            "weighted_confidence": self.weighted_confidence,
            "weighting_algorithm": self.weighting_algorithm,
            "factors": self.factors,
            "threshold": self.get_effective_threshold(),
            "threshold_met": self.threshold_met,
            "recommendation": (
                "apply" if self.should_apply_recommendation() else "reject"
            ),
        }
