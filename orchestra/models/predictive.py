"""Predictive data models for Epic 3: Predictive Intelligence Engine."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class PredictionType(str, Enum):
    """Types of predictions."""
    OUTCOME = "outcome"
    RESOURCE_DEMAND = "resource_demand"
    TIMELINE = "timeline"
    RISK_ASSESSMENT = "risk_assessment"


class OutcomeMetric(str, Enum):
    """Project success metrics for outcome prediction."""
    DELIVERY_SUCCESS = "delivery_success"
    QUALITY_SCORE = "quality_score"
    TIMELINE_ADHERENCE = "timeline_adherence"
    BUDGET_ADHERENCE = "budget_adherence"
    STAKEHOLDER_SATISFACTION = "stakeholder_satisfaction"
    TECHNICAL_DEBT = "technical_debt"


class ResourceType(str, Enum):
    """Types of resources for demand prediction."""
    DEVELOPER = "developer"
    DESIGNER = "designer"
    TESTER = "tester"
    DEVOPS = "devops"
    PRODUCT_MANAGER = "product_manager"
    COMPUTE = "compute"
    STORAGE = "storage"
    NETWORK = "network"


class RiskCategory(str, Enum):
    """Categories of project risks."""
    TECHNICAL = "technical"
    SCHEDULE = "schedule"
    RESOURCE = "resource"
    QUALITY = "quality"
    SECURITY = "security"
    COMPLIANCE = "compliance"
    EXTERNAL = "external"
    FINANCIAL = "financial"


class RiskImpact(str, Enum):
    """Impact levels for risks."""
    NEGLIGIBLE = "negligible"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskProbability(str, Enum):
    """Probability levels for risks."""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class ConfidenceLevel(str, Enum):
    """Confidence levels for predictions."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class OutcomePrediction:
    """Project success metrics with confidence scores and trends."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str = ""
    metric: OutcomeMetric = OutcomeMetric.DELIVERY_SUCCESS
    predicted_value: float = 0.0
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    confidence_score: float = 0.0
    prediction_horizon_days: int = 30
    historical_trend: List[float] = field(default_factory=list)
    influencing_factors: List[str] = field(default_factory=list)
    accuracy_baseline: Optional[float] = None
    model_version: str = "1.0"
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    prediction_date: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ResourceDemandPrediction:
    """Future resource requirements with capacity planning."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str = ""
    resource_type: ResourceType = ResourceType.DEVELOPER
    predicted_demand: float = 0.0
    demand_unit: str = "hours"  # "hours", "FTE", "GB", "CPU cores", etc.
    prediction_period_days: int = 30
    current_capacity: Optional[float] = None
    capacity_gap: Optional[float] = None
    peak_demand_date: Optional[datetime] = None
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    confidence_score: float = 0.0
    demand_pattern: str = "steady"  # "steady", "increasing", "decreasing", "cyclical"
    seasonality_factors: List[Dict[str, Any]] = field(default_factory=list)
    accuracy_baseline: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    prediction_date: datetime = field(default_factory=datetime.utcnow)


@dataclass
class TimelinePrediction:
    """Delivery estimates with milestone forecasting and risk factors."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str = ""
    milestone_name: str = ""
    predicted_completion_date: datetime = field(default_factory=datetime.utcnow)
    original_target_date: Optional[datetime] = None
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    confidence_score: float = 0.0
    delay_probability: float = 0.0
    expected_delay_days: float = 0.0
    risk_factors: List[str] = field(default_factory=list)
    critical_path_items: List[str] = field(default_factory=list)
    buffer_days: float = 0.0
    accuracy_baseline: Optional[float] = None
    historical_performance: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    prediction_date: datetime = field(default_factory=datetime.utcnow)


@dataclass
class MitigationStrategy:
    """Risk mitigation strategy with actionable steps."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    action_steps: List[str] = field(default_factory=list)
    estimated_effort_hours: float = 0.0
    estimated_cost: Optional[float] = None
    effectiveness_score: float = 0.0
    implementation_timeline_days: int = 0
    required_resources: List[str] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RiskAssessment:
    """Risk identification with mitigation strategies and confidence scores."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str = ""
    risk_name: str = ""
    category: RiskCategory = RiskCategory.TECHNICAL
    description: str = ""
    probability: RiskProbability = RiskProbability.MEDIUM
    impact: RiskImpact = RiskImpact.MEDIUM
    risk_score: float = 0.0  # Calculated from probability * impact
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    confidence_score: float = 0.0
    mitigation_strategies: List[MitigationStrategy] = field(default_factory=list)
    recommended_strategy_id: Optional[str] = None
    early_warning_indicators: List[str] = field(default_factory=list)
    contingency_plans: List[str] = field(default_factory=list)
    owner: Optional[str] = None
    review_date: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PredictionModel:
    """Machine learning models for various prediction types."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    prediction_type: PredictionType = PredictionType.OUTCOME
    model_type: str = ""  # "linear_regression", "random_forest", "neural_network", etc.
    version: str = "1.0"
    accuracy_score: float = 0.0
    training_data_size: int = 0
    feature_importance: Dict[str, float] = field(default_factory=dict)
    hyperparameters: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    last_trained: datetime = field(default_factory=datetime.utcnow)
    next_training_due: Optional[datetime] = None
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class HistoricalPattern:
    """Learned patterns from past outcomes for prediction improvement."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    pattern_name: str = ""
    pattern_type: PredictionType = PredictionType.OUTCOME
    pattern_signature: Dict[str, Any] = field(default_factory=dict)
    outcome_data: List[Dict[str, Any]] = field(default_factory=list)
    pattern_strength: float = 0.0
    occurrence_count: int = 0
    success_rate: float = 0.0
    confidence_level: ConfidenceLevel = ConfidenceLevel.MEDIUM
    is_validated: bool = False
    validation_source: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PredictionAccuracy:
    """Tracking prediction accuracy for model improvement."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    prediction_id: str = ""
    prediction_type: PredictionType = PredictionType.OUTCOME
    predicted_value: Any = None
    actual_value: Any = None
    accuracy_score: float = 0.0
    error_margin: float = 0.0
    model_version: str = "1.0"
    evaluation_date: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)