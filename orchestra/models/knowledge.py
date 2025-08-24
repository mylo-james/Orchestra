"""Knowledge management data models for orchestra layout."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ConflictType(str, Enum):
    CONTENT = "content"
    METADATA = "metadata"
    SEMANTIC = "semantic"
    TEMPORAL = "temporal"
    BOTH = "both"


class SeverityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MergeStrategy(str, Enum):
    APPEND = "append"
    VOTE = "vote"
    HYBRID = "hybrid"
    CONSERVATIVE = "conservative"
    AGGRESSIVE = "aggressive"


class KnowledgeDomain(str, Enum):
    GENERAL = "general"
    TECHNICAL = "technical"
    BUSINESS = "business"
    SECURITY = "security"


class SecurityClassification(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


@dataclass
class KnowledgeMetadata:
    domain: KnowledgeDomain
    tags: List[str] = field(default_factory=list)
    source: str = ""
    confidence: float = 0.0
    security_classification: SecurityClassification = SecurityClassification.PUBLIC
    document_id: Optional[str] = None
    agent_attribution: Optional[str] = None
    confidence_score: Optional[float] = None
    knowledge_domain: Optional[str] = None

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)


@dataclass
class KnowledgeChunk:
    id: str
    content: str
    embedding: List[float]
    metadata: KnowledgeMetadata
    version: int
    created_at: datetime
    updated_at: datetime
    author: str


@dataclass
class KnowledgeVersion:
    document_id: str
    version: int
    content: str
    metadata: Dict[str, Any]
    created_at: datetime
    agent_attribution: str


@dataclass
class KnowledgeConflict:
    id: str
    chunk_id: str
    existing_version: KnowledgeChunk
    incoming_version: KnowledgeChunk
    conflict_type: ConflictType
    severity: SeverityLevel
    detected_at: datetime
    document_id: Optional[str] = None
    version_a: Optional[KnowledgeVersion] = None
    version_b: Optional[KnowledgeVersion] = None
    similarity_score: Optional[float] = None
    resolved: bool = False
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None


@dataclass
class KnowledgeLock:
    document_id: str
    agent_id: str
    operation: str
    expires_at: datetime
    lock_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    released: bool = False


@dataclass
class KnowledgeQuery:
    query_text: str
    max_results: int = 10
    min_confidence: float = 0.0
    knowledge_domains: List[KnowledgeDomain] = field(default_factory=list)
    agent_id: Optional[str] = None
