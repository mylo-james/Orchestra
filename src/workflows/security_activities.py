"""Security activities for workflow state validation and context sanitization."""

from __future__ import annotations

from typing import Any, Dict

from src.utils.logging import SecurityAuditLogger


audit = SecurityAuditLogger()


def sanitize_agent_context(context: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize agent context before handoff (remove secrets, PII, etc.)."""
    sanitized = {**context}
    for key in list(sanitized.keys()):
        if key.lower() in {"token", "api_key", "password", "secret"}:
            sanitized[key] = "[REDACTED]"
    audit.log_security_event("context_sanitized", {"keys": list(sanitized.keys())})
    return sanitized


def validate_state_integrity(state: Dict[str, Any]) -> None:
    """Validate minimal fields exist for integrity across handoffs."""
    required = ["session_id", "correlation_id", "current_agent"]
    missing = [k for k in required if k not in state or not state[k]]
    if missing:
        raise ValueError(f"Invalid workflow state, missing: {missing}")
    audit.log_security_event("state_validated", {"ok": True})

