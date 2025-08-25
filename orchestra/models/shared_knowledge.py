"""Shared knowledge data models for Orchestra AI cross-persona learning system."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class SharedKnowledge:
    """
    Cross-persona knowledge records with transferability metadata.

    Stores knowledge patterns that can be shared between personas
    with effectiveness tracking and usage metrics.
    """

    knowledge_id: str
    source_persona_id: str
    source_project_id: str
    pattern_id: str
    knowledge_type: str  # success_pattern, failure_pattern, optimization_pattern
    title: str
    description: str
    content: Dict[str, Any]
    transferability_metadata: Dict[str, Any]
    effectiveness_score: float
    usage_count: int
    success_rate: float
    created_at: datetime
    updated_at: datetime
    lazy_loaded: bool = False
    epic1_integration: Optional[Dict[str, Any]] = None

    def assess_transferability(self, target_persona: str) -> Dict[str, Any]:
        """Assess transferability to target persona."""
        transferability_scores = self.transferability_metadata.get(
            "transferability_scores", {}
        )
        adaptation_required = self.transferability_metadata.get(
            "adaptation_required", {}
        )

        return {
            "score": transferability_scores.get(target_persona, 0.5),
            "adaptation": adaptation_required.get(target_persona, "unknown"),
            "applicable": target_persona
            in self.transferability_metadata.get("applicable_personas", []),
        }

    def record_usage(self, success: bool) -> None:
        """Record knowledge usage and update success metrics."""
        old_success_count = int(self.usage_count * self.success_rate)
        self.usage_count += 1

        if success:
            new_success_count = old_success_count + 1
        else:
            new_success_count = old_success_count

        self.success_rate = new_success_count / self.usage_count
        self.updated_at = datetime.utcnow()

    def get_sharing_summary(self) -> Dict[str, Any]:
        """Get summary for knowledge sharing decisions."""
        return {
            "knowledge_id": self.knowledge_id,
            "source_persona": self.source_persona_id,
            "knowledge_type": self.knowledge_type,
            "title": self.title,
            "effectiveness_score": self.effectiveness_score,
            "success_rate": self.success_rate,
            "usage_count": self.usage_count,
            "applicable_personas": self.transferability_metadata.get(
                "applicable_personas", []
            ),
        }


@dataclass
class PatternMapping:
    """
    Mappings between similar patterns across different personas.

    AI-assisted pattern matching with transferability scoring
    and context mapping for cross-persona adaptation.
    """

    mapping_id: str
    source_pattern_id: str
    target_pattern_id: str
    source_persona_id: str
    target_persona_id: str
    project_id: str
    similarity_score: float
    transferability_score: float
    mapping_type: str  # complementary, equivalent, derivative
    context_mapping: Dict[str, Any]
    confidence_score: float
    ai_analysis: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    validated: bool = False

    def __post_init__(self):
        """Validate pattern mapping constraints."""
        if self.transferability_score <= 0.75:
            raise ValueError(
                "transferability_score must be > 0.75 for pattern mapping acceptance"
            )

        if not (0.0 <= self.similarity_score <= 1.0):
            raise ValueError("similarity_score must be between 0 and 1")

        if not (0.0 <= self.confidence_score <= 1.0):
            raise ValueError("confidence_score must be between 0 and 1")

    def get_adaptation_strategy(self) -> Dict[str, Any]:
        """Get adaptation strategy for pattern transfer."""
        if self.transferability_score > 0.9:
            return {"strategy": "direct_transfer", "adaptation_required": "minimal"}
        elif self.transferability_score > 0.8:
            return {"strategy": "minor_adaptation", "adaptation_required": "moderate"}
        else:
            return {
                "strategy": "significant_adaptation",
                "adaptation_required": "major",
            }

    def validate_mapping(self) -> bool:
        """Validate the pattern mapping quality."""
        # Check minimum thresholds
        if self.transferability_score <= 0.75:
            return False

        if self.confidence_score < 0.7:
            return False

        # Check AI analysis confidence if available
        if self.ai_analysis:
            ai_confidence = self.ai_analysis.get("analysis_confidence", 0.0)
            if ai_confidence < 0.8:
                return False

        self.validated = True
        return True

    def get_mapping_summary(self) -> Dict[str, Any]:
        """Get mapping summary for propagation decisions."""
        return {
            "mapping_id": self.mapping_id,
            "source_persona": self.source_persona_id,
            "target_persona": self.target_persona_id,
            "mapping_type": self.mapping_type,
            "transferability_score": self.transferability_score,
            "similarity_score": self.similarity_score,
            "adaptation_strategy": self.get_adaptation_strategy(),
            "validated": self.validated,
        }


@dataclass
class PropagationRule:
    """
    Rules governing automatic vs manual knowledge sharing.

    Defines conditions and actions for knowledge propagation
    with approval workflows and tracking mechanisms.
    """

    rule_id: str
    rule_name: str
    project_id: str
    rule_type: str  # automatic, manual, conditional
    conditions: Dict[str, Any]
    actions: Dict[str, Any]
    priority: str  # high, medium, low
    active: bool
    created_at: datetime
    updated_at: datetime

    def evaluate_knowledge(self, knowledge: SharedKnowledge) -> Dict[str, Any]:
        """Evaluate knowledge against propagation rule conditions."""
        should_propagate = True
        rejection_reasons = []

        # Check confidence score threshold
        min_confidence = self.conditions.get("min_confidence_score", 0.0)
        if knowledge.effectiveness_score < min_confidence:
            should_propagate = False
            rejection_reasons.append(
                f"effectiveness_score too low: {knowledge.effectiveness_score} < {min_confidence}"
            )

        # Check effectiveness score threshold
        min_effectiveness = self.conditions.get("min_effectiveness_score", 0.0)
        if knowledge.effectiveness_score < min_effectiveness:
            should_propagate = False
            rejection_reasons.append(
                f"effectiveness_score too low: {knowledge.effectiveness_score} < {min_effectiveness}"
            )

        # Check transferability score threshold
        min_transferability = self.conditions.get("min_transferability_score", 0.0)
        # Note: This would need to be calculated for specific target persona

        # Check source persona whitelist
        source_whitelist = self.conditions.get("source_persona_whitelist", [])
        if source_whitelist and knowledge.source_persona_id not in source_whitelist:
            should_propagate = False
            rejection_reasons.append(
                f"source persona not in whitelist: {knowledge.source_persona_id}"
            )

        # Check knowledge type allowlist
        allowed_types = self.conditions.get("allowed_knowledge_types", [])
        if allowed_types and knowledge.knowledge_type not in allowed_types:
            should_propagate = False
            rejection_reasons.append(
                f"knowledge type not allowed: {knowledge.knowledge_type}"
            )

        return {
            "should_propagate": should_propagate,
            "propagation_mode": (
                self.actions.get("propagation_mode", "manual")
                if should_propagate
                else "blocked"
            ),
            "approval_required": self.actions.get("approval_required", True),
            "rejection_reasons": rejection_reasons,
            "rule_id": self.rule_id,
        }

    def get_approval_workflow(self) -> Dict[str, Any]:
        """Get approval workflow configuration."""
        return {
            "approval_required": self.actions.get("approval_required", True),
            "approvers": self.actions.get("approvers", ["team_lead"]),
            "approval_timeout_hours": self.actions.get("approval_timeout_hours", 72),
            "auto_approve_threshold": self.conditions.get(
                "auto_approve_threshold", 0.95
            ),
        }


@dataclass
class TargetingTag:
    """
    Tag-based persona targeting with hierarchical grouping.

    Integrates with Epic 1 tag-based targeting infrastructure
    for precise knowledge routing and broadcast capabilities.
    """

    tag_id: str
    tag_name: str
    tag_type: str  # technology, role, domain, specialization
    tag_value: str
    project_id: str
    target_criteria: Dict[str, Any]
    matched_personas: List[str]
    hierarchical_tags: Dict[str, List[str]]
    active: bool
    epic1_integration: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def matches_persona(self, persona_id: str) -> bool:
        """Check if persona matches targeting criteria."""
        return persona_id in self.matched_personas

    def get_inherited_personas(self, child_tags: List["TargetingTag"]) -> List[str]:
        """Get personas inherited from child tags."""
        inherited = set(self.matched_personas)

        for child_tag in child_tags:
            if self.tag_value in child_tag.hierarchical_tags.get("parent_tags", []):
                inherited.update(child_tag.matched_personas)

        return list(inherited)

    def update_matches(self, new_personas: List[str]) -> None:
        """Update matched personas and timestamp."""
        self.matched_personas = new_personas
        self.updated_at = datetime.utcnow()

    def get_targeting_summary(self) -> Dict[str, Any]:
        """Get targeting summary for broadcast operations."""
        return {
            "tag_id": self.tag_id,
            "tag_name": self.tag_name,
            "tag_type": self.tag_type,
            "tag_value": self.tag_value,
            "matched_personas": self.matched_personas,
            "target_count": len(self.matched_personas),
            "epic1_compatible": bool(self.epic1_integration),
        }


@dataclass
class ValidationMetric:
    """
    Effectiveness and appropriateness scoring for shared patterns.

    Measures pattern quality and impact with rollback capabilities
    for unsuccessful knowledge propagation.
    """

    metric_id: str
    shared_knowledge_id: str
    target_persona_id: str
    project_id: str
    validation_type: str  # effectiveness_measurement, quality_assessment
    pre_sharing_metrics: Dict[str, float]
    post_sharing_metrics: Dict[str, float]
    improvement_analysis: Dict[str, float]
    effectiveness_threshold: float
    validation_status: str  # beneficial, harmful, neutral, under_review
    rollback_required: bool = False
    rollback_data: Optional[Dict[str, Any]] = None
    quality_assessment: Optional[Dict[str, Any]] = None
    measurement_period_days: int = 14
    measurement_start: datetime = field(default_factory=datetime.utcnow)
    measurement_end: datetime = field(default_factory=datetime.utcnow)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def should_allow_propagation(self) -> bool:
        """Determine if pattern should be allowed to propagate."""
        if self.validation_type == "effectiveness_measurement":
            overall_effectiveness = self.improvement_analysis.get(
                "overall_effectiveness", 0.0
            )
            return overall_effectiveness > self.effectiveness_threshold

        elif self.validation_type == "quality_assessment":
            if self.quality_assessment:
                quality_score = self.quality_assessment.get(
                    "overall_quality_score", 0.0
                )
                quality_threshold = self.quality_assessment.get(
                    "quality_threshold", 0.75
                )
                return quality_score > quality_threshold

        return False

    def meets_quality_threshold(self) -> bool:
        """Check if pattern meets quality threshold."""
        if not self.quality_assessment:
            return False

        quality_score = self.quality_assessment.get("overall_quality_score", 0.0)
        quality_threshold = self.quality_assessment.get("quality_threshold", 0.75)
        return quality_score > quality_threshold

    def calculate_improvement_metrics(self) -> Dict[str, float]:
        """Calculate detailed improvement metrics."""
        improvements = {}

        for metric_name in self.pre_sharing_metrics:
            if metric_name in self.post_sharing_metrics:
                pre_value = self.pre_sharing_metrics[metric_name]
                post_value = self.post_sharing_metrics[metric_name]

                if pre_value != 0:
                    improvement = (post_value - pre_value) / pre_value
                    improvements[f"{metric_name}_improvement"] = improvement
                else:
                    improvements[f"{metric_name}_improvement"] = 0.0

        # Calculate overall effectiveness
        if improvements:
            overall_effectiveness = sum(improvements.values()) / len(improvements)
            improvements["overall_effectiveness"] = overall_effectiveness

        self.improvement_analysis = improvements
        return improvements

    def trigger_rollback(self, reason: str) -> Dict[str, Any]:
        """Trigger rollback of unsuccessful pattern propagation."""
        self.rollback_required = True
        self.validation_status = "harmful"

        rollback_plan = {
            "rollback_triggered": True,
            "rollback_reason": reason,
            "rollback_timestamp": datetime.utcnow().isoformat(),
            "rollback_actions": [
                "remove_shared_pattern",
                "restore_baseline_behavior",
                "notify_stakeholders",
                "update_propagation_rules",
            ],
            "rollback_completed": False,
        }

        self.rollback_data = rollback_plan
        return rollback_plan

    def complete_rollback(self) -> None:
        """Mark rollback as completed."""
        if self.rollback_data:
            self.rollback_data["rollback_completed"] = True
            self.rollback_data["completion_timestamp"] = datetime.utcnow().isoformat()

    def get_validation_summary(self) -> Dict[str, Any]:
        """Get validation summary for reporting."""
        return {
            "metric_id": self.metric_id,
            "shared_knowledge_id": self.shared_knowledge_id,
            "target_persona": self.target_persona_id,
            "validation_status": self.validation_status,
            "effectiveness_threshold": self.effectiveness_threshold,
            "should_allow_propagation": self.should_allow_propagation(),
            "rollback_required": self.rollback_required,
            "improvement_analysis": self.improvement_analysis,
            "measurement_period_days": self.measurement_period_days,
        }


# Integration and workflow models


@dataclass
class KnowledgeSharingRequest:
    """Request for cross-persona knowledge sharing."""

    request_id: str
    source_persona_id: str
    target_personas: List[str]
    knowledge_ids: List[str]
    sharing_mode: str  # automatic, manual, conditional
    priority: str  # high, medium, low
    requester: str
    justification: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    status: str = "pending"  # pending, approved, rejected, completed

    def approve_request(self, approver: str) -> None:
        """Approve the knowledge sharing request."""
        self.status = "approved"
        self.approver = approver
        self.approved_at = datetime.utcnow()

    def reject_request(self, rejector: str, reason: str) -> None:
        """Reject the knowledge sharing request."""
        self.status = "rejected"
        self.rejector = rejector
        self.rejection_reason = reason
        self.rejected_at = datetime.utcnow()


@dataclass
class CrossPersonaLearningSession:
    """Session for cross-persona learning and knowledge transfer."""

    session_id: str
    participating_personas: List[str]
    project_id: str
    session_type: str  # knowledge_sharing, pattern_matching, collaborative_learning
    knowledge_items: List[str]
    session_data: Dict[str, Any]
    started_at: datetime
    ended_at: Optional[datetime] = None
    status: str = "active"  # active, completed, failed
    outcomes: Dict[str, Any] = field(default_factory=dict)

    def add_knowledge_item(self, knowledge_id: str) -> None:
        """Add knowledge item to the session."""
        if knowledge_id not in self.knowledge_items:
            self.knowledge_items.append(knowledge_id)

    def complete_session(self, outcomes: Dict[str, Any]) -> None:
        """Complete the learning session with outcomes."""
        self.status = "completed"
        self.ended_at = datetime.utcnow()
        self.outcomes = outcomes

    def get_session_summary(self) -> Dict[str, Any]:
        """Get session summary for reporting."""
        duration = None
        if self.ended_at:
            duration = (self.ended_at - self.started_at).total_seconds()

        return {
            "session_id": self.session_id,
            "participating_personas": self.participating_personas,
            "session_type": self.session_type,
            "knowledge_items_count": len(self.knowledge_items),
            "duration_seconds": duration,
            "status": self.status,
            "outcomes": self.outcomes,
        }
