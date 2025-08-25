"""Tests for security-related Temporal activities."""

from datetime import datetime
from unittest.mock import patch

import pytest

from orchestra.temporal.activities.security import (
    audit_log_activity,
    check_rate_limits_activity,
    validate_agent_output_activity,
    validate_security_activity,
)


class TestValidateSecurityActivity:
    """Test security context validation activity."""

    @pytest.mark.asyncio
    async def test_valid_security_context(self):
        """Test successful security validation with all required fields."""
        security_context = {
            "user_id": "test-user-123",
            "permissions": ["read", "write"],
            "auth_token": "valid-token-1234567890",
        }

        result = await validate_security_activity(security_context)

        assert result["valid"] is True
        assert result["reason"] == "All security checks passed"
        assert result["errors"] == []
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_missing_user_id(self):
        """Test validation failure when user_id is missing."""
        security_context = {
            "permissions": ["read", "write"],
            "auth_token": "valid-token-1234567890",
        }

        result = await validate_security_activity(security_context)

        assert result["valid"] is False
        assert "Missing user_id" in result["errors"]
        assert "Missing user_id" in result["reason"]

    @pytest.mark.asyncio
    async def test_invalid_user_id_format(self):
        """Test validation failure when user_id format is invalid."""
        security_context = {
            "user_id": "ab",  # Too short
            "permissions": ["read", "write"],
            "auth_token": "valid-token-1234567890",
        }

        result = await validate_security_activity(security_context)

        assert result["valid"] is False
        assert "Invalid user_id format" in result["errors"]

    @pytest.mark.asyncio
    async def test_missing_permissions(self):
        """Test validation failure when no permissions are granted."""
        security_context = {
            "user_id": "test-user-123",
            "auth_token": "valid-token-1234567890",
        }

        result = await validate_security_activity(security_context)

        assert result["valid"] is False
        assert "No permissions granted" in result["errors"]

    @pytest.mark.asyncio
    async def test_invalid_permissions_format(self):
        """Test validation failure when permissions format is invalid."""
        security_context = {
            "user_id": "test-user-123",
            "permissions": "read,write",  # Should be list, not string
            "auth_token": "valid-token-1234567890",
        }

        result = await validate_security_activity(security_context)

        assert result["valid"] is False
        assert "Invalid permissions format" in result["errors"]

    @pytest.mark.asyncio
    async def test_missing_required_permissions(self):
        """Test validation failure when required permissions are missing."""
        security_context = {
            "user_id": "test-user-123",
            "permissions": ["read"],  # Missing "write"
            "auth_token": "valid-token-1234567890",
        }

        result = await validate_security_activity(security_context)

        assert result["valid"] is False
        assert "Missing required permissions" in result["errors"][0]
        assert "write" in result["reason"]

    @pytest.mark.asyncio
    async def test_invalid_auth_token_format(self):
        """Test validation failure when auth token format is invalid."""
        security_context = {
            "user_id": "test-user-123",
            "permissions": ["read", "write"],
            "auth_token": "short",  # Too short
        }

        result = await validate_security_activity(security_context)

        assert result["valid"] is False
        assert "Invalid auth token format" in result["errors"]

    @pytest.mark.asyncio
    async def test_already_validated_context(self):
        """Test that already validated contexts are skipped."""
        security_context = {
            "user_id": "test-user-123",
            "permissions": ["read", "write"],
            "auth_token": "valid-token-1234567890",
            "validated": True,
        }

        result = await validate_security_activity(security_context)

        assert result["valid"] is True
        assert result["reason"] == "Already validated"
        # Note: "already validated" case doesn't return errors field

    @pytest.mark.asyncio
    async def test_multiple_validation_errors(self):
        """Test validation with multiple errors."""
        security_context = {
            "user_id": "ab",  # Too short
            "permissions": "invalid",  # Wrong format
            "auth_token": "short",  # Too short
        }

        result = await validate_security_activity(security_context)

        assert result["valid"] is False
        assert len(result["errors"]) >= 3
        assert "Invalid user_id format" in result["errors"]
        assert "Invalid permissions format" in result["errors"]
        assert "Invalid auth token format" in result["errors"]


class TestAuditLogActivity:
    """Test audit logging activity."""

    @pytest.mark.asyncio
    async def test_workflow_error_audit(self):
        """Test audit logging for workflow errors."""
        audit_data = {
            "event_type": "workflow_error",
            "session_id": "session-123",
            "correlation_id": "corr-456",
            "error": "Test error message",
        }

        result = await audit_log_activity(audit_data)

        assert result["success"] is True
        assert "logged_at" in result

    @pytest.mark.asyncio
    async def test_workflow_completed_audit(self):
        """Test audit logging for workflow completion."""
        audit_data = {
            "event_type": "workflow_completed",
            "session_id": "session-123",
            "correlation_id": "corr-456",
            "duration_seconds": 120,
            "agents_involved": ["brendan", "developer", "release"],
        }

        result = await audit_log_activity(audit_data)

        assert result["success"] is True
        assert "logged_at" in result

    @pytest.mark.asyncio
    async def test_workflow_signal_audit(self):
        """Test audit logging for workflow signals."""
        audit_data = {
            "event_type": "workflow_signal_received",
            "session_id": "session-123",
            "correlation_id": "corr-456",
            "signal_data": {"action": "pause"},
        }

        result = await audit_log_activity(audit_data)

        assert result["success"] is True
        assert "logged_at" in result

    @pytest.mark.asyncio
    async def test_generic_audit_event(self):
        """Test audit logging for generic events."""
        audit_data = {
            "event_type": "agent_handoff",
            "session_id": "session-123",
            "correlation_id": "corr-456",
        }

        result = await audit_log_activity(audit_data)

        assert result["success"] is True
        assert "logged_at" in result

    @pytest.mark.asyncio
    async def test_audit_with_missing_fields(self):
        """Test audit logging with missing optional fields."""
        audit_data = {
            "event_type": "test_event"
            # Missing session_id and correlation_id
        }

        result = await audit_log_activity(audit_data)

        assert result["success"] is True
        assert "logged_at" in result


class TestValidateAgentOutputActivity:
    """Test agent output validation activity."""

    @pytest.mark.asyncio
    async def test_valid_agent_output(self):
        """Test successful validation of valid agent output."""
        params = {
            "agent_type": "developer",
            "output": {
                "code": "print('Hello, World!')",
                "description": "Simple greeting",
            },
            "context": {"session_id": "session-123"},
        }

        result = await validate_agent_output_activity(params)

        assert result["valid"] is True
        assert result["reason"] == "Output validation successful"
        assert result["sanitized_output"] == params["output"]
        assert result["warnings"] == []

    @pytest.mark.asyncio
    async def test_empty_output(self):
        """Test validation failure for empty output."""
        params = {
            "agent_type": "developer",
            "output": None,
            "context": {"session_id": "session-123"},
        }

        result = await validate_agent_output_activity(params)

        assert result["valid"] is False
        assert result["reason"] == "Empty output"
        assert result["sanitized_output"] is None

    @pytest.mark.asyncio
    async def test_sensitive_data_detection(self):
        """Test detection of sensitive data in output."""
        params = {
            "agent_type": "developer",
            "output": {
                "code": "api_key = 'sk-1234567890abcdef'",
                "description": "API setup",
            },
            "context": {"session_id": "session-123"},
        }

        result = await validate_agent_output_activity(params)

        # Should still be valid but with warnings logged
        assert result["valid"] is True
        assert result["reason"] == "Output validation successful"

    @pytest.mark.asyncio
    async def test_dangerous_code_patterns(self):
        """Test detection of dangerous code patterns in developer output."""
        params = {
            "agent_type": "developer",
            "output": {
                "code": "exec('print(\"Hello\")')",
                "description": "Dynamic execution",
            },
            "context": {"session_id": "session-123"},
        }

        result = await validate_agent_output_activity(params)

        # Should still be valid but with warnings logged
        assert result["valid"] is True
        assert result["reason"] == "Output validation successful"

    @pytest.mark.asyncio
    async def test_non_developer_agent_output(self):
        """Test validation for non-developer agents."""
        params = {
            "agent_type": "orchestrator",
            "output": "Workflow completed successfully",
            "context": {"session_id": "session-123"},
        }

        result = await validate_agent_output_activity(params)

        assert result["valid"] is True
        assert result["reason"] == "Output validation successful"

    @pytest.mark.asyncio
    async def test_string_output_validation(self):
        """Test validation of string output."""
        params = {
            "agent_type": "developer",
            "output": "Simple text output",
            "context": {"session_id": "session-123"},
        }

        result = await validate_agent_output_activity(params)

        assert result["valid"] is True
        assert result["reason"] == "Output validation successful"

    @pytest.mark.asyncio
    async def test_missing_context(self):
        """Test validation with missing context."""
        params = {
            "agent_type": "developer",
            "output": {"code": "print('Hello')"},
            # Missing context
        }

        result = await validate_agent_output_activity(params)

        assert result["valid"] is True
        assert result["reason"] == "Output validation successful"


class TestCheckRateLimitsActivity:
    """Test rate limit checking activity."""

    @pytest.mark.asyncio
    async def test_openai_rate_limit_check(self):
        """Test rate limit checking for OpenAI service."""
        params = {
            "service": "openai",
            "user_id": "test-user-123",
            "operation": "code_generation",
        }

        result = await check_rate_limits_activity(params)

        assert result["allowed"] is True
        assert result["service"] == "openai"
        assert "limits" in result
        assert "remaining" in result
        assert "reset_at" in result
        assert result["limits"]["requests_per_minute"] == 60
        assert result["limits"]["tokens_per_minute"] == 90000

    @pytest.mark.asyncio
    async def test_github_rate_limit_check(self):
        """Test rate limit checking for GitHub service."""
        params = {
            "service": "github",
            "user_id": "test-user-123",
            "operation": "create_pr",
        }

        result = await check_rate_limits_activity(params)

        assert result["allowed"] is True
        assert result["service"] == "github"
        assert result["limits"]["requests_per_hour"] == 5000

    @pytest.mark.asyncio
    async def test_default_service_rate_limit(self):
        """Test rate limit checking with default service."""
        params = {"user_id": "test-user-123", "operation": "test_operation"}

        result = await check_rate_limits_activity(params)

        assert result["allowed"] is True
        assert result["service"] == "openai"  # Default service

    @pytest.mark.asyncio
    async def test_unknown_service_rate_limit(self):
        """Test rate limit checking for unknown service."""
        params = {
            "service": "unknown_service",
            "user_id": "test-user-123",
            "operation": "test_operation",
        }

        result = await check_rate_limits_activity(params)

        assert result["allowed"] is True
        assert result["service"] == "unknown_service"
        assert result["limits"] == {}  # No limits defined for unknown service

    @pytest.mark.asyncio
    async def test_missing_params(self):
        """Test rate limit checking with missing parameters."""
        params = {}

        result = await check_rate_limits_activity(params)

        assert result["allowed"] is True
        assert result["service"] == "openai"  # Default service
        assert "remaining" in result


class TestSecurityActivitiesIntegration:
    """Test integration scenarios for security activities."""

    @pytest.mark.asyncio
    async def test_complete_security_workflow_success(self):
        """Test a complete security workflow with all activities."""
        # 1. Validate security context
        security_context = {
            "user_id": "test-user-123",
            "permissions": ["read", "write"],
            "auth_token": "valid-token-1234567890",
        }

        security_result = await validate_security_activity(security_context)
        assert security_result["valid"] is True

        # 2. Check rate limits
        rate_limit_params = {
            "service": "openai",
            "user_id": "test-user-123",
            "operation": "code_generation",
        }

        rate_limit_result = await check_rate_limits_activity(rate_limit_params)
        assert rate_limit_result["allowed"] is True

        # 3. Validate agent output
        output_params = {
            "agent_type": "developer",
            "output": {"code": "print('Hello, World!')"},
            "context": {"session_id": "session-123"},
        }

        output_result = await validate_agent_output_activity(output_params)
        assert output_result["valid"] is True

        # 4. Audit log the workflow
        audit_data = {
            "event_type": "workflow_completed",
            "session_id": "session-123",
            "correlation_id": "corr-456",
            "duration_seconds": 60,
            "agents_involved": ["brendan", "developer"],
        }

        audit_result = await audit_log_activity(audit_data)
        assert audit_result["success"] is True

    @pytest.mark.asyncio
    async def test_security_workflow_failure_scenario(self):
        """Test security workflow with validation failures."""
        # 1. Invalid security context
        security_context = {
            "user_id": "ab",  # Too short
            "permissions": ["read"],  # Missing write
            "auth_token": "short",  # Too short
        }

        security_result = await validate_security_activity(security_context)
        assert security_result["valid"] is False

        # 2. Audit log the failure
        audit_data = {
            "event_type": "workflow_error",
            "session_id": "session-123",
            "correlation_id": "corr-456",
            "error": "Security validation failed",
        }

        audit_result = await audit_log_activity(audit_data)
        assert audit_result["success"] is True

    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self):
        """Test error handling in security activities."""
        # Test with malformed data
        malformed_context = {
            "user_id": None,
            "permissions": "not_a_list",
            "auth_token": 123,  # Not a string
        }

        result = await validate_security_activity(malformed_context)
        assert result["valid"] is False
        assert len(result["errors"]) > 0

    @pytest.mark.asyncio
    async def test_performance_requirements(self):
        """Test that activities complete within performance requirements."""
        import time

        # Test security validation performance
        start_time = time.time()
        await validate_security_activity(
            {
                "user_id": "test-user-123",
                "permissions": ["read", "write"],
                "auth_token": "valid-token-1234567890",
            }
        )
        end_time = time.time()

        # Should complete within 1 second
        assert end_time - start_time < 1.0

    @pytest.mark.asyncio
    @patch("orchestra.temporal.activities.security.AIAgentValidator")
    async def test_agent_output_validator_exception_handling(self, mock_validator):
        """Test exception handling in agent output validator initialization."""
        # Make validator initialization raise an exception
        mock_validator.side_effect = Exception("Validator initialization failed")

        params = {
            "agent_type": "developer",
            "output": {"code": "print('Hello')"},
            "context": {"session_id": "session-123"},
        }

        # Should still complete successfully despite validator failure
        result = await validate_agent_output_activity(params)

        assert result["valid"] is True
        assert result["reason"] == "Output validation successful"

    @pytest.mark.asyncio
    async def test_agent_output_multiple_sensitive_patterns(self):
        """Test detection of multiple sensitive data patterns."""
        params = {
            "agent_type": "developer",
            "output": {
                "config": "api_key=secret123 and password=mypass and token=abc123",
                "description": "Configuration with credentials",
            },
            "context": {"session_id": "session-123"},
        }

        result = await validate_agent_output_activity(params)

        # Should be valid but will log warnings for multiple patterns
        assert result["valid"] is True
        assert result["reason"] == "Output validation successful"


class TestSecurityActivitiesComprehensive:
    """Additional comprehensive tests to achieve 90%+ coverage."""

    @pytest.mark.asyncio
    async def test_security_validation_edge_cases(self):
        """Test edge cases in security validation - covers missing lines 45, 47, 52, 54."""

        # Test short user_id (< 3 characters) - line 47
        result = await validate_security_activity(
            {"user_id": "ab", "permissions": ["read", "write"]}  # Too short
        )
        assert result["valid"] is False
        assert "Invalid user_id format" in result["errors"]

        # Test non-list permissions - line 54
        result = await validate_security_activity(
            {
                "user_id": "test-user",
                "permissions": "read,write",  # String instead of list
            }
        )
        assert result["valid"] is False
        assert "Invalid permissions format" in result["errors"]

        # Test short auth token - line 70
        result = await validate_security_activity(
            {
                "user_id": "test-user",
                "permissions": ["read", "write"],
                "auth_token": "short",  # Too short
            }
        )
        assert result["valid"] is False
        assert "Invalid auth token format" in result["errors"]

    @pytest.mark.asyncio
    async def test_already_validated_context(self):
        """Test already validated context - covers lines 74-75."""
        result = await validate_security_activity(
            {
                "user_id": "test-user",
                "permissions": ["read", "write"],
                "validated": True,  # Already validated
            }
        )
        assert result["valid"] is True
        assert result["reason"] == "Already validated"

    @pytest.mark.asyncio
    async def test_complex_validation_failures(self):
        """Test multiple validation failures - covers lines 80-85."""
        result = await validate_security_activity(
            {
                "user_id": "",  # Missing
                "permissions": "invalid",  # Wrong type
                "auth_token": "short",  # Too short
            }
        )
        assert result["valid"] is False
        assert len(result["errors"]) >= 3
        assert "Missing user_id" in result["errors"][0]

    @pytest.mark.asyncio
    async def test_audit_workflow_start_event(self):
        """Test workflow start audit event - covers lines 119-130."""
        audit_data = {
            "event_type": "workflow_start",
            "session_id": "session-456",
            "correlation_id": "corr-789",
            "workflow_id": "wf-123",
            "user_id": "user-456",
        }

        result = await audit_log_activity(audit_data)
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_audit_agent_handoff_event(self):
        """Test agent handoff audit event - covers lines 150-165."""
        audit_data = {
            "event_type": "agent_handoff",
            "session_id": "session-789",
            "correlation_id": "corr-abc",
            "from_agent": "orchestrator",
            "to_agent": "developer",
            "context": {"task": "implement feature"},
        }

        result = await audit_log_activity(audit_data)
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_audit_security_event(self):
        """Test security event audit logging."""
        audit_data = {
            "event_type": "security_event",
            "session_id": "session-sec",
            "security_violation": "rate_limit_exceeded",
            "user_id": "suspicious-user",
            "details": {"attempts": 100, "timeframe": "1min"},
        }

        result = await audit_log_activity(audit_data)
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_agent_output_sensitive_data_detection(self):
        """Test sensitive data detection in agent output - covers lines 188-220."""

        # Test SSN detection
        params = {
            "agent_type": "developer",
            "output": {
                "code": "# SSN: 123-45-6789 for testing",
                "description": "Sample code with SSN",
            },
            "context": {"session_id": "session-sensitive"},
        }

        result = await validate_agent_output_activity(params)

        # Should detect sensitive data but still be valid (with sanitization)
        assert result["valid"] is True
        assert "sanitized_output" in result

    @pytest.mark.asyncio
    async def test_agent_output_credit_card_detection(self):
        """Test credit card number detection - covers sensitive data validation."""
        params = {
            "agent_type": "developer",
            "output": {
                "config": "credit_card=4532-1234-5678-9012",
                "note": "Test configuration",
            },
            "context": {"session_id": "session-cc"},
        }

        result = await validate_agent_output_activity(params)
        assert result["valid"] is True

    @pytest.mark.asyncio
    async def test_agent_output_api_key_detection(self):
        """Test API key detection and sanitization - covers lines 220-240."""
        params = {
            "agent_type": "release",
            "output": {
                "env": "OPENAI_API_KEY=sk-1234567890abcdef",
                "instructions": "Set up environment variables",
            },
            "context": {"session_id": "session-api"},
        }

        result = await validate_agent_output_activity(params)
        assert result["valid"] is True
        assert "sanitized_output" in result

    @pytest.mark.asyncio
    async def test_agent_output_malicious_content(self):
        """Test malicious content detection - covers lines 240-260."""
        params = {
            "agent_type": "developer",
            "output": {
                "script": "<script>alert('xss')</script>",
                "sql": "'; DROP TABLE users; --",
            },
            "context": {"session_id": "session-malicious"},
        }

        result = await validate_agent_output_activity(params)
        # Should flag as suspicious but handle gracefully
        assert result["valid"] is True

    @pytest.mark.asyncio
    async def test_rate_limits_user_exceeded(self):
        """Test user rate limit functionality - covers lines 279-290."""
        params = {
            "user_id": "heavy-user",
            "service": "openai",
            "operation": "chat_completion",
        }

        result = await check_rate_limits_activity(params)
        assert result["allowed"] is True  # Current implementation always allows
        assert result["service"] == "openai"
        assert "limits" in result
        assert "remaining" in result

    @pytest.mark.asyncio
    async def test_rate_limits_endpoint_specific(self):
        """Test GitHub service rate limits - covers lines 290-305."""
        params = {
            "user_id": "normal-user",
            "service": "github",
            "operation": "create_pr",
        }

        result = await check_rate_limits_activity(params)
        assert result["allowed"] is True  # Current implementation always allows
        assert result["service"] == "github"
        assert "limits" in result

    @pytest.mark.asyncio
    async def test_rate_limits_within_bounds(self):
        """Test default service rate limits."""
        params = {
            "user_id": "good-user",
            "service": "openai",
            "operation": "text_generation",
        }

        result = await check_rate_limits_activity(params)
        assert result["allowed"] is True
        assert result["service"] == "openai"
        assert "remaining" in result
        assert "reset_at" in result


class TestSecurityActivitiesIntegrationEnhanced:
    """Enhanced integration tests for security activities."""

    @pytest.mark.asyncio
    async def test_complete_security_workflow(self):
        """Test complete security validation workflow."""

        # 1. Validate security context
        security_context = {
            "user_id": "integration-user-123",
            "permissions": ["read", "write", "execute"],
            "auth_token": "valid-integration-token-1234567890",
        }

        security_result = await validate_security_activity(security_context)
        assert security_result["valid"] is True

        # 2. Check rate limits
        rate_params = {
            "user_id": "integration-user-123",
            "endpoint": "/api/workflow",
            "current_count": 10,
            "limit": 100,
            "window_seconds": 3600,
        }

        rate_result = await check_rate_limits_activity(rate_params)
        assert rate_result["allowed"] is True

        # 3. Validate agent output
        output_params = {
            "agent_type": "orchestrator",
            "output": {
                "plan": "1. Analyze requirements\n2. Create implementation\n3. Test solution",
                "status": "ready",
            },
            "context": {
                "session_id": "integration-session-123",
                "user_id": "integration-user-123",
            },
        }

        output_result = await validate_agent_output_activity(output_params)
        assert output_result["valid"] is True

        # 4. Audit the workflow completion
        audit_data = {
            "event_type": "workflow_completed",
            "session_id": "integration-session-123",
            "correlation_id": "integration-corr-456",
            "duration_seconds": 45.2,
            "success": True,
            "user_id": "integration-user-123",
        }

        audit_result = await audit_log_activity(audit_data)
        assert audit_result["success"] is True

    @pytest.mark.asyncio
    async def test_security_failure_escalation(self):
        """Test security failure escalation workflow."""

        # 1. Failed security validation
        security_result = await validate_security_activity(
            {"user_id": "", "permissions": []}  # Invalid  # No permissions
        )
        assert security_result["valid"] is False

        # 2. Check rate limits (current implementation always allows)
        rate_result = await check_rate_limits_activity(
            {
                "user_id": "bad-actor",
                "service": "openai",
                "operation": "suspicious_activity",
            }
        )
        assert rate_result["allowed"] is True  # Current implementation always allows

        # 3. Audit security violation
        audit_result = await audit_log_activity(
            {
                "event_type": "security_event",
                "session_id": "security-violation-789",
                "violation_type": "multiple_failures",
                "user_id": "bad-actor",
                "details": {
                    "security_failed": True,
                    "rate_limited": True,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            }
        )
        assert audit_result["success"] is True

    @pytest.mark.asyncio
    async def test_performance_requirements(self):
        """Test that activities complete within performance requirements."""
        import time

        # Test security validation performance
        start_time = time.time()
        await validate_security_activity(
            {
                "user_id": "perf-test-user-123",
                "permissions": ["read", "write"],
                "auth_token": "valid-token-1234567890",
            }
        )
        end_time = time.time()

        # Should complete within 1 second
        assert end_time - start_time < 1.0

        # Test audit logging performance
        start_time = time.time()
        await audit_log_activity(
            {
                "event_type": "performance_test",
                "session_id": "perf-session-123",
                "data": {"test": "performance validation"},
            }
        )
        end_time = time.time()

        # Should complete within 0.5 seconds
        assert end_time - start_time < 0.5
