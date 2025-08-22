"""Structured logging configuration with correlation IDs and security audit trails."""

import logging
import logging.config
import sys
import uuid
from contextvars import ContextVar
from typing import Any

import structlog
from structlog.types import EventDict, Processor

# Context variables for correlation tracking
correlation_id: ContextVar[str | None] = ContextVar("correlation_id", default=None)
agent_context: ContextVar[str | None] = ContextVar("agent_context", default=None)
workflow_context: ContextVar[str | None] = ContextVar("workflow_context", default=None)


def add_correlation_id(
    logger: Any, method_name: str, event_dict: EventDict
) -> EventDict:
    """Add correlation ID to all log entries for tracing across agent handoffs."""
    cid = correlation_id.get()
    if cid:
        event_dict["correlation_id"] = cid

    agent_ctx = agent_context.get()
    if agent_ctx:
        event_dict["agent"] = agent_ctx

    workflow_ctx = workflow_context.get()
    if workflow_ctx:
        event_dict["workflow_id"] = workflow_ctx

    return event_dict


def add_security_context(
    logger: Any, method_name: str, event_dict: EventDict
) -> EventDict:
    """Add security context for audit trails."""
    # Mark security-sensitive events
    if any(key in event_dict for key in ["error", "exception", "security", "auth"]):
        event_dict["security_audit"] = True

    # Add timestamp for audit trails
    event_dict["audit_timestamp"] = structlog.stdlib.add_log_level(
        logger, method_name, event_dict
    ).get("timestamp")

    return event_dict


def configure_logging(
    log_level: str = "INFO", json_logs: bool = False, enable_audit: bool = True
) -> None:
    """Configure structured logging for the Orchestra system.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_logs: Whether to output logs in JSON format
        enable_audit: Whether to enable security audit logging
    """
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )

    # Build processor chain
    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        add_correlation_id,
    ]

    if enable_audit:
        processors.append(add_security_context)

    if json_logs:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        context_class=dict,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a configured logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)


def set_correlation_id(cid: str | None = None) -> str:
    """Set correlation ID for request tracing.

    Args:
        cid: Correlation ID to set, or None to generate a new one

    Returns:
        The correlation ID that was set
    """
    if cid is None:
        cid = str(uuid.uuid4())
    correlation_id.set(cid)
    return cid


def set_agent_context(agent_name: str) -> None:
    """Set agent context for logging.

    Args:
        agent_name: Name of the current agent
    """
    agent_context.set(agent_name)


def set_workflow_context(workflow_id: str) -> None:
    """Set workflow context for logging.

    Args:
        workflow_id: ID of the current workflow
    """
    workflow_context.set(workflow_id)


def clear_context() -> None:
    """Clear all logging context variables."""
    correlation_id.set(None)
    agent_context.set(None)
    workflow_context.set(None)


class SecurityAuditLogger:
    """Specialized logger for security audit events."""

    def __init__(self, logger_name: str = "orchestra.security"):
        self.logger = get_logger(logger_name)

    def log_security_event(
        self, event_type: str, details: dict[str, Any], severity: str = "INFO"
    ) -> None:
        """Log a security audit event.

        Args:
            event_type: Type of security event (auth, validation, scan, etc.)
            details: Event details dictionary
            severity: Log severity level
        """
        log_method = getattr(self.logger, severity.lower())
        log_method(
            "Security audit event",
            event_type=event_type,
            security=True,
            audit=True,
            **(details or {}),  # Handle None gracefully
        )

    def log_agent_handoff(
        self, from_agent: str, to_agent: str, context: dict[str, Any]
    ) -> None:
        """Log agent handoff for audit trail.

        Args:
            from_agent: Source agent name
            to_agent: Target agent name
            context: Handoff context data
        """
        self.log_security_event(
            event_type="agent_handoff",
            details={
                "from_agent": from_agent,
                "to_agent": to_agent,
                "handoff_context": context,
            },
        )

    def log_code_generation(
        self, agent: str, file_path: str, operation: str, validated: bool = False
    ) -> None:
        """Log code generation events.

        Args:
            agent: Agent performing the operation
            file_path: Path of file being modified
            operation: Type of operation (create, modify, delete)
            validated: Whether code was security validated
        """
        self.log_security_event(
            event_type="code_generation",
            details={
                "agent": agent,
                "file_path": file_path,
                "operation": operation,
                "security_validated": validated,
            },
        )

    def log_external_api_call(
        self,
        service: str,
        endpoint: str,
        success: bool,
        response_code: int | None = None,
    ) -> None:
        """Log external API calls for audit.

        Args:
            service: External service name (openai, github, pinecone)
            endpoint: API endpoint called
            success: Whether the call was successful
            response_code: HTTP response code if applicable
        """
        self.log_security_event(
            event_type="external_api_call",
            details={
                "service": service,
                "endpoint": endpoint,
                "success": success,
                "response_code": response_code,
            },
        )
