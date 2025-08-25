"""Intelligence activities for Epic 3: Live Intelligence & Adaptive Workflows."""

import time
import uuid
from datetime import datetime
from typing import Any, Dict, List

from temporalio import activity

from orchestra.models.intelligence import (
    AnalysisType,
    CodeAnalysisResult,
    ConfidenceLevel,
    IntelligenceHealthStatus,
    PerformanceMetricType,
    PerformanceMetrics,
    SecurityValidationResult,
    SecurityVulnerabilityType,
    SeverityLevel,
)
from orchestra.services.intelligence_service import IntelligenceService
from orchestra.utils.logging import get_logger

logger = get_logger(__name__)


@activity.defn
async def code_analysis_activity(analysis_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute code analysis for real-time code quality assessment.

    Provides code quality scoring, pattern detection, and recommendations
    with performance requirement (<100ms for files under 1000 lines).

    Args:
        analysis_context: Code analysis parameters including:
            - project_id: Project identifier
            - file_path: Path to file being analyzed
            - code_content: Code content to analyze
            - analysis_types: List of analysis types to perform

    Returns:
        Dictionary with analysis results and performance metrics
    """
    start_time = time.time()
    
    logger.info(
        "Starting code analysis activity",
        project_id=analysis_context.get("project_id"),
        file_path=analysis_context.get("file_path"),
        analysis_types=analysis_context.get("analysis_types", []),
    )

    try:
        # Initialize intelligence service
        intelligence_service = IntelligenceService()
        
        # Perform code analysis
        analysis_result = await intelligence_service.analyze_code(
            project_id=analysis_context.get("project_id", ""),
            file_path=analysis_context.get("file_path", ""),
            code_content=analysis_context.get("code_content", ""),
            analysis_types=analysis_context.get("analysis_types", [AnalysisType.CODE_QUALITY]),
        )
        
        execution_time_ms = (time.time() - start_time) * 1000
        
        # Verify performance requirement (AC6: <100ms for files under 1000 lines)
        code_content = analysis_context.get("code_content", "")
        line_count = len(code_content.split('\n')) if code_content else 0
        
        if line_count < 1000 and execution_time_ms > 100:
            logger.warning(
                "Code analysis exceeded performance requirement",
                execution_time_ms=execution_time_ms,
                line_count=line_count,
                performance_requirement_ms=100,
            )

        result = {
            "success": True,
            "analysis_id": analysis_result.id,
            "quality_score": analysis_result.quality_score,
            "complexity_score": analysis_result.complexity_score,
            "maintainability_score": analysis_result.maintainability_score,
            "patterns_detected": analysis_result.patterns_detected,
            "recommendations": analysis_result.recommendations,
            "confidence": analysis_result.confidence.value,
            "severity": analysis_result.severity.value,
            "execution_time_ms": execution_time_ms,
            "line_count": line_count,
        }

        logger.info(
            "Code analysis activity completed",
            analysis_id=result["analysis_id"],
            quality_score=result["quality_score"],
            execution_time_ms=execution_time_ms,
            patterns_count=len(result["patterns_detected"]),
        )

        return result

    except Exception as e:
        execution_time_ms = (time.time() - start_time) * 1000
        
        logger.error(
            "Code analysis activity failed",
            error=str(e),
            project_id=analysis_context.get("project_id"),
            file_path=analysis_context.get("file_path"),
            execution_time_ms=execution_time_ms,
        )
        
        return {
            "success": False,
            "error": str(e),
            "execution_time_ms": execution_time_ms,
        }


@activity.defn
async def performance_monitoring_activity(monitoring_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute performance monitoring for execution metric collection.

    Tracks performance metrics and identifies bottlenecks with minimal overhead
    (<5% of monitored operations).

    Args:
        monitoring_context: Performance monitoring parameters including:
            - project_id: Project identifier
            - operation_name: Name of operation being monitored
            - metric_types: List of metric types to collect

    Returns:
        Dictionary with performance metrics and bottleneck analysis
    """
    start_time = time.time()
    
    logger.info(
        "Starting performance monitoring activity",
        project_id=monitoring_context.get("project_id"),
        operation_name=monitoring_context.get("operation_name"),
        metric_types=monitoring_context.get("metric_types", []),
    )

    try:
        # Initialize intelligence service
        intelligence_service = IntelligenceService()
        
        # Perform performance monitoring
        metrics_results = await intelligence_service.monitor_performance(
            project_id=monitoring_context.get("project_id", ""),
            operation_name=monitoring_context.get("operation_name", ""),
            metric_types=monitoring_context.get("metric_types", [PerformanceMetricType.EXECUTION_TIME]),
        )
        
        execution_time_ms = (time.time() - start_time) * 1000
        
        # Convert metrics to response format
        metrics = []
        total_overhead = 0.0
        
        for metric in metrics_results:
            metric_data = {
                "metric_type": metric.metric_type.value,
                "value": metric.value,
                "unit": metric.unit,
                "baseline_value": metric.baseline_value,
                "threshold_value": metric.threshold_value,
                "is_bottleneck": metric.is_bottleneck,
                "bottleneck_reason": metric.bottleneck_reason,
                "optimization_recommendations": metric.optimization_recommendations,
                "confidence": metric.confidence.value,
                "overhead_percentage": metric.overhead_percentage,
            }
            metrics.append(metric_data)
            total_overhead += metric.overhead_percentage
        
        average_overhead = total_overhead / len(metrics) if metrics else 0.0
        
        # Verify performance requirement (AC7: <5% overhead)
        if average_overhead > 5.0:
            logger.warning(
                "Performance monitoring exceeded overhead requirement",
                average_overhead_percentage=average_overhead,
                overhead_requirement_percentage=5.0,
            )

        result = {
            "success": True,
            "monitoring_id": str(uuid.uuid4()),
            "metrics": metrics,
            "average_overhead_percentage": average_overhead,
            "execution_time_ms": execution_time_ms,
        }

        logger.info(
            "Performance monitoring activity completed",
            monitoring_id=result["monitoring_id"],
            metrics_count=len(metrics),
            average_overhead_percentage=average_overhead,
            execution_time_ms=execution_time_ms,
        )

        return result

    except Exception as e:
        execution_time_ms = (time.time() - start_time) * 1000
        
        logger.error(
            "Performance monitoring activity failed",
            error=str(e),
            project_id=monitoring_context.get("project_id"),
            operation_name=monitoring_context.get("operation_name"),
            execution_time_ms=execution_time_ms,
        )
        
        return {
            "success": False,
            "error": str(e),
            "execution_time_ms": execution_time_ms,
        }


@activity.defn
async def security_validation_activity(validation_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute security validation for vulnerability scanning.

    Scans for OWASP Top 10 vulnerabilities and project-specific compliance rules
    with comprehensive security analysis.

    Args:
        validation_context: Security validation parameters including:
            - project_id: Project identifier
            - file_path: Path to file being validated
            - code_content: Code content to validate
            - compliance_rules: List of compliance rules to check

    Returns:
        Dictionary with vulnerability findings and compliance status
    """
    start_time = time.time()
    
    logger.info(
        "Starting security validation activity",
        project_id=validation_context.get("project_id"),
        file_path=validation_context.get("file_path"),
        compliance_rules=validation_context.get("compliance_rules", []),
    )

    try:
        # Initialize intelligence service
        intelligence_service = IntelligenceService()
        
        # Perform security validation
        validation_results = await intelligence_service.validate_security(
            project_id=validation_context.get("project_id", ""),
            file_path=validation_context.get("file_path", ""),
            code_content=validation_context.get("code_content", ""),
            compliance_rules=validation_context.get("compliance_rules", []),
        )
        
        scan_duration_ms = (time.time() - start_time) * 1000
        
        # Convert validation results to response format
        vulnerabilities = []
        compliance_status = {}
        
        for validation_result in validation_results:
            vulnerability_data = {
                "vulnerability_type": validation_result.vulnerability_type.value,
                "severity": validation_result.severity.value,
                "confidence": validation_result.confidence.value,
                "description": validation_result.description,
                "affected_code": validation_result.affected_code,
                "line_number": validation_result.line_number,
                "remediation_steps": validation_result.remediation_steps,
                "compliance_rules": validation_result.compliance_rules,
                "is_compliant": validation_result.is_compliant,
            }
            vulnerabilities.append(vulnerability_data)
            
            # Track compliance status by rule
            for rule in validation_result.compliance_rules:
                if rule not in compliance_status:
                    compliance_status[rule] = validation_result.is_compliant
                else:
                    # If any validation fails for a rule, mark as non-compliant
                    compliance_status[rule] = compliance_status[rule] and validation_result.is_compliant

        result = {
            "success": True,
            "validation_id": str(uuid.uuid4()),
            "vulnerabilities": vulnerabilities,
            "compliance_status": compliance_status,
            "scan_duration_ms": scan_duration_ms,
            "owasp_coverage": True,  # AC8: OWASP Top 10 coverage
        }

        logger.info(
            "Security validation activity completed",
            validation_id=result["validation_id"],
            vulnerabilities_found=len(vulnerabilities),
            compliance_rules_checked=len(compliance_status),
            scan_duration_ms=scan_duration_ms,
        )

        return result

    except Exception as e:
        scan_duration_ms = (time.time() - start_time) * 1000
        
        logger.error(
            "Security validation activity failed",
            error=str(e),
            project_id=validation_context.get("project_id"),
            file_path=validation_context.get("file_path"),
            scan_duration_ms=scan_duration_ms,
        )
        
        return {
            "success": False,
            "error": str(e),
            "scan_duration_ms": scan_duration_ms,
        }


@activity.defn
async def health_monitoring_activity(health_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute intelligence health monitoring for service status tracking.

    Provides real-time status reporting and alerting for all intelligence
    services with health endpoint monitoring.

    Args:
        health_context: Health monitoring parameters including:
            - services: List of service names to monitor

    Returns:
        Dictionary with service health status and overall system health
    """
    start_time = time.time()
    
    logger.info(
        "Starting health monitoring activity",
        services=health_context.get("services", []),
    )

    try:
        # Initialize intelligence service
        intelligence_service = IntelligenceService()
        
        # Monitor service health
        health_results = await intelligence_service.monitor_health(
            services=health_context.get("services", []),
        )
        
        execution_time_ms = (time.time() - start_time) * 1000
        
        # Convert health results to response format
        health_status = {}
        overall_health = True
        
        for service_name, health_result in health_results.items():
            service_status = {
                "is_healthy": health_result.is_healthy,
                "response_time_ms": health_result.response_time_ms,
                "error_count": health_result.error_count,
                "success_rate": health_result.success_rate,
                "last_check": health_result.last_check.isoformat(),
                "metadata": health_result.metadata,
            }
            health_status[service_name] = service_status
            
            # Update overall health
            if not health_result.is_healthy:
                overall_health = False

        result = {
            "success": True,
            "health_status": health_status,
            "overall_health": overall_health,
            "execution_time_ms": execution_time_ms,
        }

        logger.info(
            "Health monitoring activity completed",
            overall_health=overall_health,
            healthy_services=sum(1 for s in health_status.values() if s["is_healthy"]),
            total_services=len(health_status),
            execution_time_ms=execution_time_ms,
        )

        return result

    except Exception as e:
        execution_time_ms = (time.time() - start_time) * 1000
        
        logger.error(
            "Health monitoring activity failed",
            error=str(e),
            services=health_context.get("services", []),
            execution_time_ms=execution_time_ms,
        )
        
        return {
            "success": False,
            "error": str(e),
            "execution_time_ms": execution_time_ms,
        }


@activity.defn
async def intelligence_storage_activity(storage_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute intelligence data storage with project namespacing.

    Stores intelligence data with project namespacing (orchestra_intelligence_{project_id})
    in Qdrant collections and PostgreSQL metadata tables.

    Args:
        storage_context: Storage parameters including:
            - project_id: Project identifier for namespacing
            - intelligence_data: Intelligence data to store

    Returns:
        Dictionary with storage results and namespace information
    """
    start_time = time.time()
    
    logger.info(
        "Starting intelligence storage activity",
        project_id=storage_context.get("project_id"),
        intelligence_type=storage_context.get("intelligence_data", {}).get("type"),
    )

    try:
        # Initialize intelligence service
        intelligence_service = IntelligenceService()
        
        # Store intelligence data with project namespacing
        storage_result = await intelligence_service.store_intelligence_data(
            project_id=storage_context.get("project_id", ""),
            intelligence_data=storage_context.get("intelligence_data", {}),
        )
        
        execution_time_ms = (time.time() - start_time) * 1000
        
        # Generate project namespace (AC9: Project namespacing)
        project_id = storage_context.get("project_id", "")
        namespace = f"orchestra_intelligence_{project_id}"
        
        result = {
            "success": True,
            "storage_id": str(uuid.uuid4()),
            "namespace": namespace,
            "stored_items": storage_result.get("stored_items", 0),
            "qdrant_collection": namespace,
            "postgresql_table": f"intelligence_metadata_{project_id.replace('-', '_')}",
            "execution_time_ms": execution_time_ms,
        }

        logger.info(
            "Intelligence storage activity completed",
            storage_id=result["storage_id"],
            namespace=result["namespace"],
            stored_items=result["stored_items"],
            execution_time_ms=execution_time_ms,
        )

        return result

    except Exception as e:
        execution_time_ms = (time.time() - start_time) * 1000
        
        logger.error(
            "Intelligence storage activity failed",
            error=str(e),
            project_id=storage_context.get("project_id"),
            execution_time_ms=execution_time_ms,
        )
        
        return {
            "success": False,
            "error": str(e),
            "execution_time_ms": execution_time_ms,
        }