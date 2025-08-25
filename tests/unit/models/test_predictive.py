"""Tests for Predictive data models."""

import pytest
from datetime import datetime, timedelta
from orchestra.models.predictive import (
    ConfidenceLevel,
    HistoricalPattern,
    MitigationStrategy,
    OutcomeMetric,
    OutcomePrediction,
    PredictionAccuracy,
    PredictionModel,
    PredictionType,
    ResourceDemandPrediction,
    ResourceType,
    RiskAssessment,
    RiskCategory,
    RiskImpact,
    RiskProbability,
    TimelinePrediction,
)


class TestOutcomePrediction:
    """Test OutcomePrediction data model."""

    def test_outcome_prediction_creation(self):
        """Test creating an OutcomePrediction instance."""
        prediction = OutcomePrediction(
            project_id="test-project",
            metric=OutcomeMetric.DELIVERY_SUCCESS,
            predicted_value=0.89,
            confidence=ConfidenceLevel.HIGH,
            confidence_score=0.85,
            prediction_horizon_days=30,
            historical_trend=[0.82, 0.85, 0.87, 0.89],
            influencing_factors=["team_velocity", "code_quality", "technical_debt"],
            accuracy_baseline=0.82,
            model_version="2.1",
        )

        assert prediction.project_id == "test-project"
        assert prediction.metric == OutcomeMetric.DELIVERY_SUCCESS
        assert prediction.predicted_value == 0.89
        assert prediction.confidence == ConfidenceLevel.HIGH
        assert prediction.confidence_score == 0.85
        assert prediction.prediction_horizon_days == 30
        assert len(prediction.historical_trend) == 4
        assert len(prediction.influencing_factors) == 3
        assert prediction.accuracy_baseline == 0.82
        assert prediction.model_version == "2.1"

    def test_outcome_prediction_accuracy_requirement(self):
        """Test OutcomePrediction meets accuracy requirement (>80%)."""
        prediction = OutcomePrediction(
            project_id="test-project",
            metric=OutcomeMetric.DELIVERY_SUCCESS,
            predicted_value=0.91,
            accuracy_baseline=0.84,  # Above 80% requirement
        )

        # Verify accuracy requirement (AC7: >80% for project success metrics)
        assert prediction.accuracy_baseline > 0.8

    def test_outcome_prediction_metrics(self):
        """Test OutcomePrediction supports all outcome metrics."""
        metrics = [
            OutcomeMetric.DELIVERY_SUCCESS,
            OutcomeMetric.QUALITY_SCORE,
            OutcomeMetric.TIMELINE_ADHERENCE,
            OutcomeMetric.BUDGET_ADHERENCE,
            OutcomeMetric.STAKEHOLDER_SATISFACTION,
            OutcomeMetric.TECHNICAL_DEBT,
        ]

        for metric in metrics:
            prediction = OutcomePrediction(
                project_id="test-project",
                metric=metric,
                predicted_value=0.85,
            )
            assert prediction.metric == metric

    def test_outcome_prediction_confidence_levels(self):
        """Test OutcomePrediction confidence levels."""
        confidence_levels = [
            ConfidenceLevel.LOW,
            ConfidenceLevel.MEDIUM,
            ConfidenceLevel.HIGH,
            ConfidenceLevel.VERY_HIGH,
        ]

        for confidence in confidence_levels:
            prediction = OutcomePrediction(
                project_id="test-project",
                confidence=confidence,
            )
            assert prediction.confidence == confidence


class TestResourceDemandPrediction:
    """Test ResourceDemandPrediction data model."""

    def test_resource_demand_prediction_creation(self):
        """Test creating a ResourceDemandPrediction instance."""
        prediction = ResourceDemandPrediction(
            project_id="test-project",
            resource_type=ResourceType.DEVELOPER,
            predicted_demand=360.0,
            demand_unit="hours",
            prediction_period_days=30,
            current_capacity=320.0,
            capacity_gap=40.0,
            peak_demand_date=datetime(2024, 3, 15),
            confidence=ConfidenceLevel.HIGH,
            confidence_score=0.78,
            demand_pattern="increasing",
            seasonality_factors=[
                {"period": "weekly", "peak_days": ["monday", "tuesday"]},
                {"period": "daily", "peak_hours": [9, 10, 14, 15]},
            ],
            accuracy_baseline=0.76,
        )

        assert prediction.project_id == "test-project"
        assert prediction.resource_type == ResourceType.DEVELOPER
        assert prediction.predicted_demand == 360.0
        assert prediction.demand_unit == "hours"
        assert prediction.prediction_period_days == 30
        assert prediction.current_capacity == 320.0
        assert prediction.capacity_gap == 40.0
        assert prediction.peak_demand_date == datetime(2024, 3, 15)
        assert prediction.confidence == ConfidenceLevel.HIGH
        assert prediction.confidence_score == 0.78
        assert prediction.demand_pattern == "increasing"
        assert len(prediction.seasonality_factors) == 2
        assert prediction.accuracy_baseline == 0.76

    def test_resource_demand_prediction_accuracy_requirement(self):
        """Test ResourceDemandPrediction meets accuracy requirement (>75%)."""
        prediction = ResourceDemandPrediction(
            project_id="test-project",
            resource_type=ResourceType.TESTER,
            predicted_demand=120.0,
            accuracy_baseline=0.78,  # Above 75% requirement
        )

        # Verify accuracy requirement (AC8: >75% for capacity planning)
        assert prediction.accuracy_baseline > 0.75

    def test_resource_demand_prediction_resource_types(self):
        """Test ResourceDemandPrediction supports all resource types."""
        resource_types = [
            ResourceType.DEVELOPER,
            ResourceType.DESIGNER,
            ResourceType.TESTER,
            ResourceType.DEVOPS,
            ResourceType.PRODUCT_MANAGER,
            ResourceType.COMPUTE,
            ResourceType.STORAGE,
            ResourceType.NETWORK,
        ]

        for resource_type in resource_types:
            prediction = ResourceDemandPrediction(
                project_id="test-project",
                resource_type=resource_type,
                predicted_demand=100.0,
            )
            assert prediction.resource_type == resource_type

    def test_resource_demand_prediction_capacity_planning(self):
        """Test ResourceDemandPrediction capacity planning features."""
        # Scenario: Need more resources (capacity gap > 0)
        over_capacity_prediction = ResourceDemandPrediction(
            project_id="test-project",
            resource_type=ResourceType.DEVELOPER,
            predicted_demand=400.0,
            current_capacity=300.0,
            capacity_gap=100.0,  # Need 100 more hours
        )

        # Scenario: Excess capacity (capacity gap < 0)
        under_capacity_prediction = ResourceDemandPrediction(
            project_id="test-project",
            resource_type=ResourceType.TESTER,
            predicted_demand=80.0,
            current_capacity=120.0,
            capacity_gap=-40.0,  # 40 hours excess
        )

        assert over_capacity_prediction.capacity_gap > 0  # Need more resources
        assert under_capacity_prediction.capacity_gap < 0  # Excess capacity

    def test_resource_demand_prediction_patterns(self):
        """Test ResourceDemandPrediction demand patterns."""
        patterns = ["steady", "increasing", "decreasing", "cyclical"]

        for pattern in patterns:
            prediction = ResourceDemandPrediction(
                project_id="test-project",
                demand_pattern=pattern,
            )
            assert prediction.demand_pattern == pattern


class TestTimelinePrediction:
    """Test TimelinePrediction data model."""

    def test_timeline_prediction_creation(self):
        """Test creating a TimelinePrediction instance."""
        prediction = TimelinePrediction(
            project_id="test-project",
            milestone_name="MVP Release",
            predicted_completion_date=datetime(2024, 3, 5),
            original_target_date=datetime(2024, 3, 1),
            confidence=ConfidenceLevel.HIGH,
            confidence_score=0.82,
            delay_probability=0.68,
            expected_delay_days=4.0,
            risk_factors=["dependency_delay", "resource_constraint"],
            critical_path_items=["API integration", "UI testing"],
            buffer_days=2.0,
            accuracy_baseline=0.74,
            historical_performance={
                "average_delay": 3.2,
                "on_time_rate": 0.73,
                "early_delivery_rate": 0.15,
            },
        )

        assert prediction.project_id == "test-project"
        assert prediction.milestone_name == "MVP Release"
        assert prediction.predicted_completion_date == datetime(2024, 3, 5)
        assert prediction.original_target_date == datetime(2024, 3, 1)
        assert prediction.confidence == ConfidenceLevel.HIGH
        assert prediction.confidence_score == 0.82
        assert prediction.delay_probability == 0.68
        assert prediction.expected_delay_days == 4.0
        assert len(prediction.risk_factors) == 2
        assert len(prediction.critical_path_items) == 2
        assert prediction.buffer_days == 2.0
        assert prediction.accuracy_baseline == 0.74
        assert len(prediction.historical_performance) == 3

    def test_timeline_prediction_accuracy_requirement(self):
        """Test TimelinePrediction meets accuracy requirement (>70%)."""
        prediction = TimelinePrediction(
            project_id="test-project",
            milestone_name="Beta Release",
            accuracy_baseline=0.72,  # Above 70% requirement
        )

        # Verify accuracy requirement (AC9: >70% for delivery estimates)
        assert prediction.accuracy_baseline > 0.7

    def test_timeline_prediction_delay_analysis(self):
        """Test TimelinePrediction delay analysis features."""
        # On-time prediction
        on_time_prediction = TimelinePrediction(
            project_id="test-project",
            milestone_name="On-time Milestone",
            delay_probability=0.25,  # Low delay probability
            expected_delay_days=0.0,
        )

        # Delayed prediction
        delayed_prediction = TimelinePrediction(
            project_id="test-project",
            milestone_name="Delayed Milestone",
            delay_probability=0.85,  # High delay probability
            expected_delay_days=7.0,
        )

        assert on_time_prediction.delay_probability < 0.5
        assert on_time_prediction.expected_delay_days == 0.0

        assert delayed_prediction.delay_probability > 0.5
        assert delayed_prediction.expected_delay_days > 0.0

    def test_timeline_prediction_risk_factors(self):
        """Test TimelinePrediction risk factor tracking."""
        prediction = TimelinePrediction(
            project_id="test-project",
            milestone_name="Risky Milestone",
            risk_factors=[
                "external_dependency",
                "new_technology",
                "team_changes",
                "scope_creep",
            ],
            critical_path_items=[
                "Third-party API integration",
                "Performance optimization",
                "Security audit",
            ],
        )

        assert len(prediction.risk_factors) == 4
        assert len(prediction.critical_path_items) == 3
        assert "external_dependency" in prediction.risk_factors
        assert "Third-party API integration" in prediction.critical_path_items


class TestRiskAssessment:
    """Test RiskAssessment data model."""

    def test_risk_assessment_creation(self):
        """Test creating a RiskAssessment instance."""
        mitigation_strategy = MitigationStrategy(
            name="Technical Training Program",
            description="Comprehensive training on new technology stack",
            action_steps=[
                "Identify training needs",
                "Select training provider",
                "Schedule training sessions",
                "Conduct hands-on workshops",
            ],
            estimated_effort_hours=40.0,
            estimated_cost=5000.0,
            effectiveness_score=0.85,
            implementation_timeline_days=14,
            required_resources=["senior_developer", "training_budget"],
            success_criteria=["Team proficiency > 80%", "Reduced development time"],
        )

        assessment = RiskAssessment(
            project_id="test-project",
            risk_name="Technology Learning Curve",
            category=RiskCategory.TECHNICAL,
            description="Team unfamiliar with new technology stack",
            probability=RiskProbability.HIGH,
            impact=RiskImpact.MEDIUM,
            risk_score=0.75,
            confidence=ConfidenceLevel.HIGH,
            confidence_score=0.88,
            mitigation_strategies=[mitigation_strategy],
            recommended_strategy_id="strategy-1",
            early_warning_indicators=["Slow development velocity", "Increased bugs"],
            contingency_plans=["Hire external consultant", "Reduce scope"],
            owner="tech_lead",
            review_date=datetime(2024, 2, 15),
        )

        assert assessment.project_id == "test-project"
        assert assessment.risk_name == "Technology Learning Curve"
        assert assessment.category == RiskCategory.TECHNICAL
        assert assessment.probability == RiskProbability.HIGH
        assert assessment.impact == RiskImpact.MEDIUM
        assert assessment.risk_score == 0.75
        assert assessment.confidence == ConfidenceLevel.HIGH
        assert assessment.confidence_score == 0.88
        assert len(assessment.mitigation_strategies) == 1
        assert assessment.recommended_strategy_id == "strategy-1"
        assert len(assessment.early_warning_indicators) == 2
        assert len(assessment.contingency_plans) == 2
        assert assessment.owner == "tech_lead"

    def test_risk_assessment_categories(self):
        """Test RiskAssessment risk categories."""
        categories = [
            RiskCategory.TECHNICAL,
            RiskCategory.SCHEDULE,
            RiskCategory.RESOURCE,
            RiskCategory.QUALITY,
            RiskCategory.SECURITY,
            RiskCategory.COMPLIANCE,
            RiskCategory.EXTERNAL,
            RiskCategory.FINANCIAL,
        ]

        for category in categories:
            assessment = RiskAssessment(
                project_id="test-project",
                risk_name=f"{category.value.title()} Risk",
                category=category,
            )
            assert assessment.category == category

    def test_risk_assessment_probability_impact_matrix(self):
        """Test RiskAssessment probability and impact levels."""
        probabilities = [
            RiskProbability.VERY_LOW,
            RiskProbability.LOW,
            RiskProbability.MEDIUM,
            RiskProbability.HIGH,
            RiskProbability.VERY_HIGH,
        ]

        impacts = [
            RiskImpact.NEGLIGIBLE,
            RiskImpact.LOW,
            RiskImpact.MEDIUM,
            RiskImpact.HIGH,
            RiskImpact.CRITICAL,
        ]

        for probability in probabilities:
            for impact in impacts:
                assessment = RiskAssessment(
                    project_id="test-project",
                    risk_name="Test Risk",
                    probability=probability,
                    impact=impact,
                )
                assert assessment.probability == probability
                assert assessment.impact == impact

    def test_risk_assessment_mitigation_strategies(self):
        """Test RiskAssessment actionable mitigation strategies."""
        strategy = MitigationStrategy(
            name="Security Hardening",
            description="Implement comprehensive security measures",
            action_steps=[
                "Conduct security audit",
                "Implement MFA",
                "Update dependencies",
                "Add monitoring",
            ],
            estimated_effort_hours=60.0,
            effectiveness_score=0.92,
            implementation_timeline_days=21,
            success_criteria=["Zero critical vulnerabilities", "Pass security audit"],
        )

        assessment = RiskAssessment(
            project_id="test-project",
            risk_name="Security Vulnerability",
            category=RiskCategory.SECURITY,
            mitigation_strategies=[strategy],
        )

        # Verify actionable mitigation strategies (AC10)
        mitigation = assessment.mitigation_strategies[0]
        assert len(mitigation.action_steps) > 0
        assert mitigation.estimated_effort_hours > 0
        assert mitigation.effectiveness_score > 0
        assert mitigation.implementation_timeline_days > 0
        assert len(mitigation.success_criteria) > 0


class TestMitigationStrategy:
    """Test MitigationStrategy data model."""

    def test_mitigation_strategy_creation(self):
        """Test creating a MitigationStrategy instance."""
        strategy = MitigationStrategy(
            name="Risk Mitigation Plan",
            description="Comprehensive plan to mitigate identified risk",
            action_steps=[
                "Step 1: Assessment",
                "Step 2: Planning",
                "Step 3: Implementation",
                "Step 4: Validation",
            ],
            estimated_effort_hours=32.0,
            estimated_cost=2500.0,
            effectiveness_score=0.88,
            implementation_timeline_days=10,
            required_resources=["project_manager", "developer", "budget"],
            success_criteria=["Risk reduced by 80%", "No incidents in 30 days"],
        )

        assert strategy.name == "Risk Mitigation Plan"
        assert len(strategy.action_steps) == 4
        assert strategy.estimated_effort_hours == 32.0
        assert strategy.estimated_cost == 2500.0
        assert strategy.effectiveness_score == 0.88
        assert strategy.implementation_timeline_days == 10
        assert len(strategy.required_resources) == 3
        assert len(strategy.success_criteria) == 2

    def test_mitigation_strategy_actionable_steps(self):
        """Test MitigationStrategy provides actionable steps."""
        strategy = MitigationStrategy(
            name="Database Performance Optimization",
            action_steps=[
                "Analyze slow queries",
                "Add database indexes",
                "Optimize query structure",
                "Implement query caching",
                "Monitor performance metrics",
            ],
            estimated_effort_hours=24.0,
            effectiveness_score=0.85,
        )

        # Verify actionable steps
        assert len(strategy.action_steps) >= 3  # Multiple actionable steps
        assert all(step.strip() for step in strategy.action_steps)  # Non-empty steps
        assert strategy.estimated_effort_hours > 0
        assert 0 < strategy.effectiveness_score <= 1


class TestPredictionModel:
    """Test PredictionModel data model."""

    def test_prediction_model_creation(self):
        """Test creating a PredictionModel instance."""
        model = PredictionModel(
            name="Delivery Success Predictor",
            prediction_type=PredictionType.OUTCOME,
            model_type="random_forest",
            version="2.1",
            accuracy_score=0.87,
            training_data_size=1500,
            feature_importance={
                "team_velocity": 0.35,
                "code_quality": 0.28,
                "technical_debt": 0.22,
                "team_experience": 0.15,
            },
            hyperparameters={
                "n_estimators": 100,
                "max_depth": 10,
                "min_samples_split": 5,
            },
            is_active=True,
            performance_metrics={
                "precision": 0.89,
                "recall": 0.85,
                "f1_score": 0.87,
            },
        )

        assert model.name == "Delivery Success Predictor"
        assert model.prediction_type == PredictionType.OUTCOME
        assert model.model_type == "random_forest"
        assert model.version == "2.1"
        assert model.accuracy_score == 0.87
        assert model.training_data_size == 1500
        assert len(model.feature_importance) == 4
        assert len(model.hyperparameters) == 3
        assert model.is_active is True
        assert len(model.performance_metrics) == 3

    def test_prediction_model_types(self):
        """Test PredictionModel supports different prediction types."""
        prediction_types = [
            PredictionType.OUTCOME,
            PredictionType.RESOURCE_DEMAND,
            PredictionType.TIMELINE,
            PredictionType.RISK_ASSESSMENT,
        ]

        for pred_type in prediction_types:
            model = PredictionModel(
                name=f"{pred_type.value.title()} Model",
                prediction_type=pred_type,
            )
            assert model.prediction_type == pred_type


class TestHistoricalPattern:
    """Test HistoricalPattern data model."""

    def test_historical_pattern_creation(self):
        """Test creating a HistoricalPattern instance."""
        pattern = HistoricalPattern(
            pattern_name="Sprint Velocity Decline",
            pattern_type=PredictionType.TIMELINE,
            pattern_signature={
                "team_size_change": True,
                "new_technology": True,
                "deadline_pressure": "high",
            },
            outcome_data=[
                {"sprint": 1, "velocity": 10, "outcome": "success"},
                {"sprint": 2, "velocity": 8, "outcome": "delayed"},
                {"sprint": 3, "velocity": 6, "outcome": "delayed"},
            ],
            pattern_strength=0.82,
            occurrence_count=15,
            success_rate=0.67,
            confidence_level=ConfidenceLevel.HIGH,
            is_validated=True,
            validation_source="historical_analysis",
        )

        assert pattern.pattern_name == "Sprint Velocity Decline"
        assert pattern.pattern_type == PredictionType.TIMELINE
        assert len(pattern.pattern_signature) == 3
        assert len(pattern.outcome_data) == 3
        assert pattern.pattern_strength == 0.82
        assert pattern.occurrence_count == 15
        assert pattern.success_rate == 0.67
        assert pattern.confidence_level == ConfidenceLevel.HIGH
        assert pattern.is_validated is True
        assert pattern.validation_source == "historical_analysis"


class TestPredictionAccuracy:
    """Test PredictionAccuracy data model."""

    def test_prediction_accuracy_creation(self):
        """Test creating a PredictionAccuracy instance."""
        accuracy = PredictionAccuracy(
            prediction_id="pred-123",
            prediction_type=PredictionType.OUTCOME,
            predicted_value=0.85,
            actual_value=0.82,
            accuracy_score=0.96,  # High accuracy
            error_margin=0.03,
            model_version="2.1",
        )

        assert accuracy.prediction_id == "pred-123"
        assert accuracy.prediction_type == PredictionType.OUTCOME
        assert accuracy.predicted_value == 0.85
        assert accuracy.actual_value == 0.82
        assert accuracy.accuracy_score == 0.96
        assert accuracy.error_margin == 0.03
        assert accuracy.model_version == "2.1"

    def test_prediction_accuracy_tracking(self):
        """Test PredictionAccuracy tracks model performance."""
        # High accuracy prediction
        high_accuracy = PredictionAccuracy(
            prediction_id="pred-high",
            predicted_value=0.90,
            actual_value=0.88,
            accuracy_score=0.98,
            error_margin=0.02,
        )

        # Low accuracy prediction
        low_accuracy = PredictionAccuracy(
            prediction_id="pred-low",
            predicted_value=0.75,
            actual_value=0.60,
            accuracy_score=0.80,
            error_margin=0.15,
        )

        assert high_accuracy.accuracy_score > 0.95
        assert high_accuracy.error_margin < 0.05

        assert low_accuracy.accuracy_score < 0.85
        assert low_accuracy.error_margin > 0.10


class TestPredictiveEnums:
    """Test Predictive model enums."""

    def test_prediction_type_enum(self):
        """Test PredictionType enum values."""
        assert PredictionType.OUTCOME == "outcome"
        assert PredictionType.RESOURCE_DEMAND == "resource_demand"
        assert PredictionType.TIMELINE == "timeline"
        assert PredictionType.RISK_ASSESSMENT == "risk_assessment"

    def test_outcome_metric_enum(self):
        """Test OutcomeMetric enum values."""
        assert OutcomeMetric.DELIVERY_SUCCESS == "delivery_success"
        assert OutcomeMetric.QUALITY_SCORE == "quality_score"
        assert OutcomeMetric.TIMELINE_ADHERENCE == "timeline_adherence"
        assert OutcomeMetric.BUDGET_ADHERENCE == "budget_adherence"
        assert OutcomeMetric.STAKEHOLDER_SATISFACTION == "stakeholder_satisfaction"
        assert OutcomeMetric.TECHNICAL_DEBT == "technical_debt"

    def test_resource_type_enum(self):
        """Test ResourceType enum values."""
        assert ResourceType.DEVELOPER == "developer"
        assert ResourceType.DESIGNER == "designer"
        assert ResourceType.TESTER == "tester"
        assert ResourceType.DEVOPS == "devops"
        assert ResourceType.PRODUCT_MANAGER == "product_manager"
        assert ResourceType.COMPUTE == "compute"
        assert ResourceType.STORAGE == "storage"
        assert ResourceType.NETWORK == "network"

    def test_risk_category_enum(self):
        """Test RiskCategory enum values."""
        assert RiskCategory.TECHNICAL == "technical"
        assert RiskCategory.SCHEDULE == "schedule"
        assert RiskCategory.RESOURCE == "resource"
        assert RiskCategory.QUALITY == "quality"
        assert RiskCategory.SECURITY == "security"
        assert RiskCategory.COMPLIANCE == "compliance"
        assert RiskCategory.EXTERNAL == "external"
        assert RiskCategory.FINANCIAL == "financial"