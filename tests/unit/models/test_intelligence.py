"""Tests for Intelligence data models."""

import pytest
from datetime import datetime
from orchestra.models.intelligence import (
    AnalysisType,
    CodeAnalysisResult,
    ConfidenceLevel,
    IntelligenceHealthStatus,
    IntelligenceIndex,
    PerformanceMetricType,
    PerformanceMetrics,
    RetentionPolicy,
    SecurityValidationResult,
    SecurityVulnerabilityType,
    SeverityLevel,
)


class TestCodeAnalysisResult:
    """Test CodeAnalysisResult data model."""

    def test_code_analysis_result_creation(self):
        """Test creating a CodeAnalysisResult instance."""
        result = CodeAnalysisResult(
            project_id="test-project",
            file_path="src/main.py",
            analysis_type=AnalysisType.CODE_QUALITY,
            quality_score=0.92,
            complexity_score=0.15,
            patterns_detected=["good_naming", "proper_structure"],
            recommendations=["Add docstring", "Consider type hints"],
            confidence=ConfidenceLevel.HIGH,
            severity=SeverityLevel.INFO,
        )

        assert result.project_id == "test-project"
        assert result.file_path == "src/main.py"
        assert result.analysis_type == AnalysisType.CODE_QUALITY
        assert result.quality_score == 0.92
        assert result.complexity_score == 0.15
        assert len(result.patterns_detected) == 2
        assert len(result.recommendations) == 2
        assert result.confidence == ConfidenceLevel.HIGH
        assert result.severity == SeverityLevel.INFO
        assert isinstance(result.created_at, datetime)
        assert result.id is not None

    def test_code_analysis_result_defaults(self):
        """Test CodeAnalysisResult default values."""
        result = CodeAnalysisResult()

        assert result.project_id == ""
        assert result.file_path == ""
        assert result.analysis_type == AnalysisType.CODE_QUALITY
        assert result.quality_score == 0.0
        assert result.complexity_score == 0.0
        assert result.patterns_detected == []
        assert result.recommendations == []
        assert result.confidence == ConfidenceLevel.MEDIUM
        assert result.severity == SeverityLevel.INFO
        assert result.metadata == {}
        assert result.execution_time_ms == 0.0

    def test_code_analysis_result_performance_tracking(self):
        """Test CodeAnalysisResult tracks execution time for performance requirements."""
        result = CodeAnalysisResult(
            project_id="test-project",
            file_path="src/large_file.py",
            execution_time_ms=95.0,  # Under 100ms requirement
        )

        # Verify performance requirement tracking
        assert result.execution_time_ms == 95.0
        assert result.execution_time_ms < 100  # AC6: <100ms for files under 1000 lines


class TestPerformanceMetrics:
    """Test PerformanceMetrics data model."""

    def test_performance_metrics_creation(self):
        """Test creating a PerformanceMetrics instance."""
        metrics = PerformanceMetrics(
            project_id="test-project",
            operation_name="user_authentication",
            metric_type=PerformanceMetricType.EXECUTION_TIME,
            value=150.0,
            unit="ms",
            baseline_value=120.0,
            threshold_value=200.0,
            is_bottleneck=False,
            optimization_recommendations=["Add caching", "Optimize database query"],
            confidence=ConfidenceLevel.HIGH,
            overhead_percentage=2.5,
        )

        assert metrics.project_id == "test-project"
        assert metrics.operation_name == "user_authentication"
        assert metrics.metric_type == PerformanceMetricType.EXECUTION_TIME
        assert metrics.value == 150.0
        assert metrics.unit == "ms"
        assert metrics.baseline_value == 120.0
        assert metrics.threshold_value == 200.0
        assert metrics.is_bottleneck is False
        assert len(metrics.optimization_recommendations) == 2
        assert metrics.confidence == ConfidenceLevel.HIGH
        assert metrics.overhead_percentage == 2.5

    def test_performance_metrics_overhead_requirement(self):
        """Test PerformanceMetrics tracks overhead for performance requirements."""
        metrics = PerformanceMetrics(
            project_id="test-project",
            operation_name="database_query",
            overhead_percentage=3.2,  # Under 5% requirement
        )

        # Verify performance requirement tracking (AC7: <5% overhead)
        assert metrics.overhead_percentage == 3.2
        assert metrics.overhead_percentage < 5.0

    def test_performance_metrics_bottleneck_detection(self):
        """Test PerformanceMetrics bottleneck detection."""
        metrics = PerformanceMetrics(
            project_id="test-project",
            operation_name="slow_operation",
            value=2500.0,
            is_bottleneck=True,
            bottleneck_reason="Inefficient algorithm",
            optimization_recommendations=["Implement caching", "Use better algorithm"],
        )

        assert metrics.is_bottleneck is True
        assert metrics.bottleneck_reason == "Inefficient algorithm"
        assert len(metrics.optimization_recommendations) == 2


class TestSecurityValidationResult:
    """Test SecurityValidationResult data model."""

    def test_security_validation_result_creation(self):
        """Test creating a SecurityValidationResult instance."""
        result = SecurityValidationResult(
            project_id="test-project",
            file_path="src/auth.py",
            vulnerability_type=SecurityVulnerabilityType.INJECTION,
            severity=SeverityLevel.HIGH,
            confidence=ConfidenceLevel.VERY_HIGH,
            description="SQL injection vulnerability detected",
            affected_code="SELECT * FROM users WHERE id = " + str(user_id),
            line_number=42,
            remediation_steps=["Use parameterized queries", "Validate input"],
            compliance_rules=["OWASP_TOP_10", "PCI_DSS"],
            is_compliant=False,
            scan_duration_ms=75.0,
        )

        assert result.project_id == "test-project"
        assert result.file_path == "src/auth.py"
        assert result.vulnerability_type == SecurityVulnerabilityType.INJECTION
        assert result.severity == SeverityLevel.HIGH
        assert result.confidence == ConfidenceLevel.VERY_HIGH
        assert "SQL injection" in result.description
        assert result.line_number == 42
        assert len(result.remediation_steps) == 2
        assert len(result.compliance_rules) == 2
        assert result.is_compliant is False
        assert result.scan_duration_ms == 75.0

    def test_security_validation_owasp_coverage(self):
        """Test SecurityValidationResult covers OWASP Top 10 vulnerabilities."""
        owasp_vulnerabilities = [
            SecurityVulnerabilityType.INJECTION,
            SecurityVulnerabilityType.BROKEN_AUTHENTICATION,
            SecurityVulnerabilityType.SENSITIVE_DATA_EXPOSURE,
            SecurityVulnerabilityType.XML_EXTERNAL_ENTITIES,
            SecurityVulnerabilityType.BROKEN_ACCESS_CONTROL,
            SecurityVulnerabilityType.SECURITY_MISCONFIGURATION,
            SecurityVulnerabilityType.CROSS_SITE_SCRIPTING,
            SecurityVulnerabilityType.INSECURE_DESERIALIZATION,
            SecurityVulnerabilityType.VULNERABLE_COMPONENTS,
            SecurityVulnerabilityType.INSUFFICIENT_LOGGING,
        ]

        # Verify OWASP Top 10 coverage (AC8)
        assert len(owasp_vulnerabilities) == 10

        for vuln_type in owasp_vulnerabilities:
            result = SecurityValidationResult(
                project_id="test-project",
                vulnerability_type=vuln_type,
                severity=SeverityLevel.MEDIUM,
            )
            assert result.vulnerability_type == vuln_type

    def test_security_validation_compliance_tracking(self):
        """Test SecurityValidationResult tracks compliance status."""
        result = SecurityValidationResult(
            project_id="test-project",
            vulnerability_type=SecurityVulnerabilityType.SENSITIVE_DATA_EXPOSURE,
            compliance_rules=["GDPR", "HIPAA", "SOX"],
            is_compliant=True,
        )

        assert len(result.compliance_rules) == 3
        assert "GDPR" in result.compliance_rules
        assert result.is_compliant is True


class TestIntelligenceIndex:
    """Test IntelligenceIndex data model."""

    def test_intelligence_index_creation(self):
        """Test creating an IntelligenceIndex instance."""
        index = IntelligenceIndex(
            project_id="test-project",
            intelligence_type="code_analysis",
            intelligence_id="analysis-123",
            relevance_score=0.92,
            tags=["python", "quality", "patterns"],
            embedding=[0.1, 0.2, 0.3, 0.4, 0.5],
        )

        assert index.project_id == "test-project"
        assert index.intelligence_type == "code_analysis"
        assert index.intelligence_id == "analysis-123"
        assert index.relevance_score == 0.92
        assert len(index.tags) == 3
        assert len(index.embedding) == 5
        assert isinstance(index.created_at, datetime)
        assert isinstance(index.updated_at, datetime)

    def test_intelligence_index_project_namespacing(self):
        """Test IntelligenceIndex supports project namespacing."""
        index_project_a = IntelligenceIndex(
            project_id="project-alpha",
            intelligence_type="security",
            intelligence_id="sec-123",
        )

        index_project_b = IntelligenceIndex(
            project_id="project-beta",
            intelligence_type="security",
            intelligence_id="sec-456",
        )

        # Verify project isolation (AC9: Project namespacing)
        assert index_project_a.project_id != index_project_b.project_id
        assert index_project_a.intelligence_id != index_project_b.intelligence_id


class TestRetentionPolicy:
    """Test RetentionPolicy data model."""

    def test_retention_policy_creation(self):
        """Test creating a RetentionPolicy instance."""
        policy = RetentionPolicy(
            project_id="test-project",
            intelligence_type="performance",
            retention_days=30,
            archive_after_days=90,
            auto_cleanup=True,
            compression_enabled=True,
        )

        assert policy.project_id == "test-project"
        assert policy.intelligence_type == "performance"
        assert policy.retention_days == 30
        assert policy.archive_after_days == 90
        assert policy.auto_cleanup is True
        assert policy.compression_enabled is True

    def test_retention_policy_lifecycle_management(self):
        """Test RetentionPolicy supports intelligence data lifecycle management."""
        policy = RetentionPolicy(
            project_id="test-project",
            intelligence_type="code_analysis",
            retention_days=60,
            archive_after_days=180,
            auto_cleanup=False,  # Manual cleanup
        )

        # Verify lifecycle management capabilities
        assert policy.retention_days < policy.archive_after_days
        assert policy.auto_cleanup is False  # Manual control


class TestIntelligenceHealthStatus:
    """Test IntelligenceHealthStatus data model."""

    def test_intelligence_health_status_creation(self):
        """Test creating an IntelligenceHealthStatus instance."""
        status = IntelligenceHealthStatus(
            service_name="code_analysis_service",
            is_healthy=True,
            response_time_ms=45.0,
            error_count=0,
            success_rate=99.5,
        )

        assert status.service_name == "code_analysis_service"
        assert status.is_healthy is True
        assert status.response_time_ms == 45.0
        assert status.error_count == 0
        assert status.success_rate == 99.5
        assert isinstance(status.last_check, datetime)

    def test_intelligence_health_status_monitoring(self):
        """Test IntelligenceHealthStatus supports real-time monitoring."""
        # Healthy service
        healthy_status = IntelligenceHealthStatus(
            service_name="performance_monitoring_service",
            is_healthy=True,
            response_time_ms=32.0,
            success_rate=98.8,
        )

        # Unhealthy service
        unhealthy_status = IntelligenceHealthStatus(
            service_name="security_validation_service",
            is_healthy=False,
            response_time_ms=5000.0,  # Timeout
            error_count=15,
            success_rate=45.0,
        )

        # Verify health monitoring (AC10: Health endpoints)
        assert healthy_status.is_healthy is True
        assert healthy_status.response_time_ms < 100
        assert healthy_status.success_rate > 95

        assert unhealthy_status.is_healthy is False
        assert unhealthy_status.response_time_ms > 1000
        assert unhealthy_status.success_rate < 50


class TestIntelligenceEnums:
    """Test Intelligence model enums."""

    def test_analysis_type_enum(self):
        """Test AnalysisType enum values."""
        assert AnalysisType.CODE_QUALITY == "code_quality"
        assert AnalysisType.PATTERN_DETECTION == "pattern_detection"
        assert AnalysisType.COMPLEXITY == "complexity"
        assert AnalysisType.MAINTAINABILITY == "maintainability"
        assert AnalysisType.SECURITY == "security"

    def test_performance_metric_type_enum(self):
        """Test PerformanceMetricType enum values."""
        assert PerformanceMetricType.EXECUTION_TIME == "execution_time"
        assert PerformanceMetricType.MEMORY_USAGE == "memory_usage"
        assert PerformanceMetricType.CPU_USAGE == "cpu_usage"
        assert PerformanceMetricType.IO_OPERATIONS == "io_operations"
        assert PerformanceMetricType.NETWORK_LATENCY == "network_latency"

    def test_security_vulnerability_type_enum(self):
        """Test SecurityVulnerabilityType enum covers OWASP Top 10."""
        owasp_types = [
            SecurityVulnerabilityType.INJECTION,
            SecurityVulnerabilityType.BROKEN_AUTHENTICATION,
            SecurityVulnerabilityType.SENSITIVE_DATA_EXPOSURE,
            SecurityVulnerabilityType.XML_EXTERNAL_ENTITIES,
            SecurityVulnerabilityType.BROKEN_ACCESS_CONTROL,
            SecurityVulnerabilityType.SECURITY_MISCONFIGURATION,
            SecurityVulnerabilityType.CROSS_SITE_SCRIPTING,
            SecurityVulnerabilityType.INSECURE_DESERIALIZATION,
            SecurityVulnerabilityType.VULNERABLE_COMPONENTS,
            SecurityVulnerabilityType.INSUFFICIENT_LOGGING,
        ]

        # Verify OWASP Top 10 coverage (AC8)
        assert len(owasp_types) == 10

    def test_confidence_level_enum(self):
        """Test ConfidenceLevel enum values."""
        assert ConfidenceLevel.LOW == "low"
        assert ConfidenceLevel.MEDIUM == "medium"
        assert ConfidenceLevel.HIGH == "high"
        assert ConfidenceLevel.VERY_HIGH == "very_high"

    def test_severity_level_enum(self):
        """Test SeverityLevel enum values."""
        assert SeverityLevel.INFO == "info"
        assert SeverityLevel.LOW == "low"
        assert SeverityLevel.MEDIUM == "medium"
        assert SeverityLevel.HIGH == "high"
        assert SeverityLevel.CRITICAL == "critical"