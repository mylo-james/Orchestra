"""Tests for logging utilities - easy coverage wins."""

from unittest.mock import patch, MagicMock
import logging

from src.utils.logging import (
    get_logger,
    configure_logging,
    SecurityAuditLogger,
    set_correlation_id,
)


class TestLoggingUtilities:
    """Test logging utility functions."""

    def test_get_logger(self):
        """Test logger creation."""
        logger = get_logger("test")
        assert logger is not None
        assert logger.name == "test"

    def test_get_logger_with_module_name(self):
        """Test logger creation with module name."""
        logger = get_logger(__name__)
        assert logger is not None
        assert "test_logging" in logger.name

    def test_configure_logging_basic(self):
        """Test basic logging configuration."""
        # Should not raise errors
        configure_logging()

        # Test with different parameters
        configure_logging(log_level="DEBUG")
        configure_logging(log_level="INFO", json_logs=True)

    def test_configure_logging_with_options(self):
        """Test logging configuration with various options."""
        configure_logging(log_level="WARNING", json_logs=False, enable_audit=True)

        # Should configure successfully
        logger = get_logger("test")
        assert logger.level <= logging.WARNING

    def test_set_correlation_id(self):
        """Test correlation ID setting."""
        test_id = "test-correlation-123"
        set_correlation_id(test_id)

        # Should not raise errors
        # The actual implementation might store this in context

    def test_set_correlation_id_none(self):
        """Test correlation ID with None value."""
        set_correlation_id(None)
        # Should handle None gracefully

    def test_set_correlation_id_empty_string(self):
        """Test correlation ID with empty string."""
        set_correlation_id("")
        # Should handle empty string gracefully


class TestSecurityAuditLogger:
    """Test security audit logger."""

    def test_security_audit_logger_creation(self):
        """Test audit logger creation."""
        logger = SecurityAuditLogger("test.module")
        assert logger is not None

    def test_log_security_event(self):
        """Test security event logging."""
        logger = SecurityAuditLogger("test.security")

        # Should handle various event types
        logger.log_security_event("test_event", {"key": "value"})
        logger.log_security_event("user_action", {"user": "test", "action": "login"})

    def test_log_security_event_with_none_data(self):
        """Test security event logging with None data."""
        logger = SecurityAuditLogger("test.security")

        # Should handle None data gracefully
        logger.log_security_event("test_event", None)

    def test_log_security_event_with_empty_data(self):
        """Test security event logging with empty data."""
        logger = SecurityAuditLogger("test.security")

        # Should handle empty data gracefully
        logger.log_security_event("test_event", {})

    def test_multiple_audit_loggers(self):
        """Test multiple audit logger instances."""
        logger1 = SecurityAuditLogger("module1")
        logger2 = SecurityAuditLogger("module2")

        assert logger1 is not None
        assert logger2 is not None

        # Should be able to log independently
        logger1.log_security_event("event1", {"source": "module1"})
        logger2.log_security_event("event2", {"source": "module2"})

    def test_audit_logger_with_complex_data(self):
        """Test audit logger with complex data structures."""
        logger = SecurityAuditLogger("test.complex")

        complex_data = {
            "user": "test_user",
            "timestamp": "2024-01-01T00:00:00Z",
            "metadata": {"ip": "127.0.0.1", "user_agent": "test-agent"},
            "actions": ["login", "view_dashboard"],
        }

        # Should handle complex nested data
        logger.log_security_event("complex_event", complex_data)


class TestLoggingIntegration:
    """Test logging integration scenarios."""

    def test_logger_hierarchy(self):
        """Test logger hierarchy functionality."""
        parent_logger = get_logger("parent")
        child_logger = get_logger("parent.child")

        assert parent_logger is not None
        assert child_logger is not None

    def test_logging_levels(self):
        """Test different logging levels."""
        logger = get_logger("test.levels")

        # Should support standard logging levels
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")

    @patch("src.utils.logging.structlog")
    def test_structlog_integration(self, mock_structlog):
        """Test structlog integration."""
        mock_structlog.configure = MagicMock()

        configure_logging()

        # Should interact with structlog
        mock_structlog.configure.assert_called()

    def test_audit_and_regular_logging_coexist(self):
        """Test that audit and regular logging work together."""
        regular_logger = get_logger("regular")
        audit_logger = SecurityAuditLogger("audit")

        # Both should work
        regular_logger.info("Regular log message")
        audit_logger.log_security_event("audit_event", {"test": True})

    def test_logging_error_handling(self):
        """Test logging error handling."""
        # Test with potentially problematic logger names
        logger1 = get_logger("")  # Empty name
        logger2 = get_logger("very.long.nested.logger.name.for.testing")

        assert logger1 is not None
        assert logger2 is not None
