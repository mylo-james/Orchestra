"""Intelligence data models for Epic 3: Live Intelligence & Adaptive Workflows."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class AnalysisType(str, Enum):
    """Types of code analysis."""
    CODE_QUALITY = "code_quality"
    PATTERN_DETECTION = "pattern_detection"
    COMPLEXITY = "complexity"
    MAINTAINABILITY = "maintainability"
    SECURITY = "security"


class PerformanceMetricType(str, Enum):
    """Types of performance metrics."""
    EXECUTION_TIME = "execution_time"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"
    IO_OPERATIONS = "io_operations"
    NETWORK_LATENCY = "network_latency"


class SecurityVulnerabilityType(str, Enum):
    """Types of security vulnerabilities based on OWASP Top 10."""
    INJECTION = "injection"
    BROKEN_AUTHENTICATION = "broken_authentication"
    SENSITIVE_DATA_EXPOSURE = "sensitive_data_exposure"
    XML_EXTERNAL_ENTITIES = "xml_external_entities"
    BROKEN_ACCESS_CONTROL = "broken_access_control"
    SECURITY_MISCONFIGURATION = "security_misconfiguration"
    CROSS_SITE_SCRIPTING = "cross_site_scripting"
    INSECURE_DESERIALIZATION = "insecure_deserialization"
    VULNERABLE_COMPONENTS = "vulnerable_components"
    INSUFFICIENT_LOGGING = "insufficient_logging"


class ConfidenceLevel(str, Enum):
    """Confidence levels for intelligence results."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class SeverityLevel(str, Enum):
    """Severity levels for issues and recommendations."""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class CodeAnalysisResult:
    """Result of code analysis intelligence."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str = ""
    file_path: str = ""
    analysis_type: AnalysisType = AnalysisType.CODE_QUALITY
    quality_score: float = 0.0
    complexity_score: float = 0.0
    maintainability_score: float = 0.0
    patterns_detected: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    severity: SeverityLevel = SeverityLevel.INFO
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    execution_time_ms: float = 0.0


@dataclass
class PerformanceMetrics:
    """Performance monitoring metrics."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str = ""
    operation_name: str = ""
    metric_type: PerformanceMetricType = PerformanceMetricType.EXECUTION_TIME
    value: float = 0.0
    unit: str = ""
    baseline_value: Optional[float] = None
    threshold_value: Optional[float] = None
    is_bottleneck: bool = False
    bottleneck_reason: Optional[str] = None
    optimization_recommendations: List[str] = field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    overhead_percentage: float = 0.0


@dataclass
class SecurityValidationResult:
    """Security validation and vulnerability scan result."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str = ""
    file_path: str = ""
    vulnerability_type: SecurityVulnerabilityType = SecurityVulnerabilityType.INJECTION
    severity: SeverityLevel = SeverityLevel.INFO
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    description: str = ""
    affected_code: Optional[str] = None
    line_number: Optional[int] = None
    remediation_steps: List[str] = field(default_factory=list)
    compliance_rules: List[str] = field(default_factory=list)
    is_compliant: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    scan_duration_ms: float = 0.0


@dataclass
class IntelligenceIndex:
    """Fast retrieval indexing for intelligence data."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str = ""
    intelligence_type: str = ""  # "code_analysis", "performance", "security"
    intelligence_id: str = ""
    relevance_score: float = 0.0
    tags: List[str] = field(default_factory=list)
    embedding: List[float] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class RetentionPolicy:
    """Intelligence data lifecycle management policy."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str = ""
    intelligence_type: str = ""
    retention_days: int = 30
    archive_after_days: int = 90
    auto_cleanup: bool = True
    compression_enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class IntelligenceHealthStatus:
    """Health status for intelligence services."""
    service_name: str = ""
    is_healthy: bool = True
    last_check: datetime = field(default_factory=datetime.utcnow)
    response_time_ms: float = 0.0
    error_count: int = 0
    success_rate: float = 100.0
    metadata: Dict[str, Any] = field(default_factory=dict)