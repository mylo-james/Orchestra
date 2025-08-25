"""Context data models for Epic 3: Context-Aware Adaptive Resources."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ContextDimension(str, Enum):
    """Dimensions of context variables."""
    PROJECT = "project"
    PERSONA = "persona"
    TASK = "task"
    ENVIRONMENT = "environment"
    USER = "user"
    TEMPORAL = "temporal"


class ContextVariableType(str, Enum):
    """Types of context variables."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    LIST = "list"
    DICT = "dict"
    DATETIME = "datetime"


class AdaptationStrategy(str, Enum):
    """Strategies for adaptive resource selection."""
    RELEVANCE_BASED = "relevance_based"
    PATTERN_MATCHING = "pattern_matching"
    MACHINE_LEARNING = "machine_learning"
    RULE_BASED = "rule_based"
    HYBRID = "hybrid"


class WorkflowConditionOperator(str, Enum):
    """Operators for workflow conditions."""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_EQUAL = "greater_equal"
    LESS_EQUAL = "less_equal"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    IN = "in"
    NOT_IN = "not_in"
    REGEX_MATCH = "regex_match"


@dataclass
class ContextVariable:
    """Multi-dimensional context data with validation and persistence."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    value: Any = None
    variable_type: ContextVariableType = ContextVariableType.STRING
    dimension: ContextDimension = ContextDimension.PROJECT
    description: str = ""
    is_persistent: bool = True
    is_sensitive: bool = False
    validation_rules: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None


@dataclass
class AdaptiveTemplate:
    """Dynamic template with context-aware adaptation rules."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    template_content: str = ""
    adaptation_rules: List[Dict[str, Any]] = field(default_factory=list)
    required_context: List[str] = field(default_factory=list)
    adaptation_strategy: AdaptationStrategy = AdaptationStrategy.RELEVANCE_BASED
    relevance_threshold: float = 0.7
    version: int = 1
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class WorkflowCondition:
    """Individual condition for conditional workflow branching."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    context_variable: str = ""
    operator: WorkflowConditionOperator = WorkflowConditionOperator.EQUALS
    expected_value: Any = None
    description: str = ""
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConditionalWorkflow:
    """Workflow with conditional branching based on context."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    conditions: List[WorkflowCondition] = field(default_factory=list)
    condition_logic: str = "AND"  # "AND", "OR", or custom expression
    true_branch_workflow: str = ""
    false_branch_workflow: str = ""
    default_workflow: Optional[str] = None
    max_condition_depth: int = 10
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ContextAwareResource:
    """Resource with relevance scoring and context matching."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    resource_type: str = ""  # "template", "checklist", "workflow", "tool"
    resource_content: Dict[str, Any] = field(default_factory=dict)
    context_requirements: List[str] = field(default_factory=list)
    relevance_score: float = 0.0
    adaptation_rules: List[Dict[str, Any]] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ContextPattern:
    """Learned patterns for context-aware resource selection."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    pattern_name: str = ""
    context_signature: Dict[str, Any] = field(default_factory=dict)
    resource_preferences: List[str] = field(default_factory=list)
    success_rate: float = 0.0
    usage_count: int = 0
    confidence_score: float = 0.0
    learning_source: str = ""  # "user_feedback", "outcome_analysis", "usage_patterns"
    is_validated: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ContextEvaluationResult:
    """Result of context evaluation for adaptive resources."""
    context_variables: Dict[str, Any] = field(default_factory=dict)
    matched_patterns: List[str] = field(default_factory=list)
    recommended_resources: List[str] = field(default_factory=list)
    relevance_scores: Dict[str, float] = field(default_factory=dict)
    adaptation_applied: bool = False
    evaluation_time_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)