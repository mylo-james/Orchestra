"""Memory management data models for Orchestra AI system."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


@dataclass
class MemoryRecord:
    """
    Core memory storage record with embeddings and metadata.

    Supports project namespace isolation and Qdrant vector storage
    with text-embedding-3-large dimensions (3072).
    """

    memory_id: str
    project_id: str
    persona_id: str
    content: str
    embedding: List[float]
    confidence_score: float
    relevance_score: float
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    version: int = 1

    def __post_init__(self):
        """Validate memory record constraints."""
        if not self.memory_id:
            raise ValueError("memory_id is required")

        if not (0.0 <= self.confidence_score <= 1.0):
            raise ValueError("confidence_score must be between 0 and 1")

        if not (0.0 <= self.relevance_score <= 1.0):
            raise ValueError("relevance_score must be between 0 and 1")

        if len(self.embedding) != 3072:
            raise ValueError(
                "embedding must have 3072 dimensions for text-embedding-3-large"
            )

    def get_namespace(self) -> str:
        """Get Qdrant collection namespace for project isolation."""
        return f"orchestra_memory_{self.project_id}"

    def to_qdrant_point(self) -> Dict[str, Any]:
        """Convert to Qdrant point structure."""
        return {
            "id": self.memory_id,
            "vector": self.embedding,
            "payload": {
                "content": self.content,
                "metadata": {
                    "memory_id": self.memory_id,
                    "project_id": self.project_id,
                    "persona_id": self.persona_id,
                    "confidence_score": self.confidence_score,
                    "relevance_score": self.relevance_score,
                    "created_at": self.created_at.isoformat(),
                    "updated_at": self.updated_at.isoformat(),
                    "version": self.version,
                    **self.metadata,
                },
            },
        }


@dataclass
class ContextPattern:
    """
    Project-specific interaction patterns with success metrics.

    Captures successful and failed patterns for persona learning
    and improvement recommendations.
    """

    pattern_id: str
    project_id: str
    persona_id: str
    pattern_type: str  # success_pattern, failure_pattern, optimization_pattern
    description: str
    context_data: Dict[str, Any]
    success_metrics: Dict[str, float]
    usage_count: int
    last_used: datetime
    created_at: datetime
    effectiveness_score: float = 0.0

    def record_usage(self, success: bool = True) -> None:
        """Record pattern usage and update metrics."""
        self.usage_count += 1
        self.last_used = datetime.utcnow()

        if success and self.usage_count > 1:
            # Update effectiveness score based on success rate
            current_success_rate = self.success_metrics.get("success_rate", 0.8)
            # Weighted average with new success
            self.effectiveness_score = (current_success_rate * 0.9) + (1.0 * 0.1)
        elif not success:
            # Decrease effectiveness on failure
            self.effectiveness_score = max(0.0, self.effectiveness_score - 0.1)

    def get_pattern_summary(self) -> Dict[str, Any]:
        """Get pattern summary for sharing and analysis."""
        return {
            "pattern_id": self.pattern_id,
            "pattern_type": self.pattern_type,
            "description": self.description,
            "effectiveness_score": self.effectiveness_score,
            "usage_count": self.usage_count,
            "success_metrics": self.success_metrics,
            "context_data": self.context_data,
        }


@dataclass
class MemoryIndex:
    """
    Fast retrieval indexing with relevance scoring.

    Supports semantic, keyword, and temporal indexing for
    efficient memory search and retrieval.
    """

    index_id: str
    project_id: str
    memory_id: str
    index_type: str  # semantic, keyword, temporal
    index_data: Dict[str, Any]
    relevance_score: float
    created_at: datetime
    updated_at: datetime

    def __post_init__(self):
        """Validate index constraints."""
        if not (0.0 <= self.relevance_score <= 1.0):
            raise ValueError("relevance_score must be between 0 and 1")

    def update_relevance(self, new_score: float) -> None:
        """Update relevance score and timestamp."""
        if not (0.0 <= new_score <= 1.0):
            raise ValueError("relevance_score must be between 0 and 1")

        self.relevance_score = new_score
        self.updated_at = datetime.utcnow()

    def matches_query(self, query_data: Dict[str, Any]) -> bool:
        """Check if index matches query criteria."""
        if self.index_type == "semantic":
            return query_data.get("semantic_search", False)
        elif self.index_type == "keyword":
            query_keywords = query_data.get("keywords", [])
            index_keywords = self.index_data.get("keywords", [])
            return bool(set(query_keywords) & set(index_keywords))
        elif self.index_type == "temporal":
            query_time_range = query_data.get("time_range")
            if query_time_range:
                index_time = self.index_data.get("time_bucket")
                return index_time in query_time_range

        return False


@dataclass
class RetentionPolicy:
    """
    Configurable memory lifecycle management.

    Manages memory retention, archival, and deletion based on
    relevance scores, usage patterns, and time-based rules.
    """

    policy_id: str
    project_id: str
    policy_name: str
    retention_days: int
    archive_after_days: int
    delete_after_days: int
    rules: Dict[str, Any]
    active: bool
    created_at: datetime
    updated_at: datetime

    def classify_memory(self, memory_record: MemoryRecord) -> Dict[str, Any]:
        """Classify memory for retention decision."""
        age_days = (datetime.utcnow() - memory_record.created_at).days

        # Check rules for classification
        for rule_name, rule_config in self.rules.items():
            if self._memory_matches_rule(memory_record, rule_config):
                return {
                    "category": rule_name,
                    "retention_days": rule_config.get(
                        "retention_days", self.retention_days
                    ),
                    "action": self._determine_action(age_days, rule_config),
                }

        # Default classification
        return {
            "category": "standard",
            "retention_days": self.retention_days,
            "action": self._determine_action(age_days, {}),
        }

    def _memory_matches_rule(
        self, memory_record: MemoryRecord, rule_config: Dict[str, Any]
    ) -> bool:
        """Check if memory matches rule criteria."""
        # Check relevance score criteria
        min_relevance = rule_config.get("min_relevance_score")
        if min_relevance and memory_record.relevance_score < min_relevance:
            return False

        max_relevance = rule_config.get("max_relevance_score")
        if max_relevance and memory_record.relevance_score > max_relevance:
            return False

        # Check usage count criteria
        min_usage = rule_config.get("min_usage_count")
        usage_count = memory_record.metadata.get("usage_count", 0)
        if min_usage and usage_count < min_usage:
            return False

        return True

    def _determine_action(self, age_days: int, rule_config: Dict[str, Any]) -> str:
        """Determine action based on age and rules."""
        retention_days = rule_config.get("retention_days", self.retention_days)

        if age_days > self.delete_after_days:
            return "delete"
        elif age_days > max(retention_days, self.archive_after_days):
            return "archive"
        elif age_days > retention_days:
            return "review"
        else:
            return "retain"

    def should_trigger_cleanup(self, current_memory_gb: float) -> bool:
        """Check if cleanup should be triggered based on memory usage."""
        trigger_threshold = self.rules.get("memory_pressure_cleanup", {}).get(
            "trigger_memory_gb", 3.5
        )
        return current_memory_gb > trigger_threshold

    def get_cleanup_target(self) -> Dict[str, Any]:
        """Get cleanup target configuration."""
        cleanup_config = self.rules.get("memory_pressure_cleanup", {})
        return {
            "target_memory_gb": cleanup_config.get("target_memory_gb", 3.0),
            "cleanup_strategy": cleanup_config.get(
                "cleanup_strategy", "least_recently_used"
            ),
        }

    def get_schedule(self) -> Dict[str, Any]:
        """Get retention policy schedule configuration."""
        return self.rules.get(
            "schedule",
            {
                "frequency": "daily",
                "time": "02:00",
                "timezone": "UTC",
            },
        )

    def calculate_next_execution(self) -> datetime:
        """Calculate next scheduled execution time."""
        schedule = self.get_schedule()
        frequency = schedule.get("frequency", "daily")

        now = datetime.utcnow()

        if frequency == "daily":
            # Next execution at 2 AM UTC tomorrow
            next_execution = now.replace(hour=2, minute=0, second=0, microsecond=0)
            if next_execution <= now:
                next_execution += timedelta(days=1)
            return next_execution
        elif frequency == "weekly":
            # Next execution next Monday at 2 AM UTC
            days_ahead = 7 - now.weekday()  # Monday is 0
            next_execution = now + timedelta(days=days_ahead)
            return next_execution.replace(hour=2, minute=0, second=0, microsecond=0)
        else:
            # Default to daily
            return now + timedelta(days=1)


# Query and search models


@dataclass
class MemoryQuery:
    """Memory query parameters for search and retrieval."""

    project_id: str
    persona_id: Optional[str] = None
    query_text: str = ""
    max_results: int = 10
    min_relevance_score: float = 0.0
    semantic_search: bool = True
    keywords: List[str] = field(default_factory=list)
    time_range: Optional[List[str]] = None
    domains: List[str] = field(default_factory=list)
    pattern_types: List[str] = field(default_factory=list)


@dataclass
class MemorySearchResult:
    """Memory search result with relevance and similarity scores."""

    memory_record: MemoryRecord
    relevance_score: float
    similarity_score: float
    match_type: str  # semantic, keyword, exact
    context_snippet: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "memory_id": self.memory_record.memory_id,
            "content": self.memory_record.content,
            "relevance_score": self.relevance_score,
            "similarity_score": self.similarity_score,
            "match_type": self.match_type,
            "context_snippet": self.context_snippet,
            "metadata": self.memory_record.metadata,
            "created_at": self.memory_record.created_at.isoformat(),
        }
