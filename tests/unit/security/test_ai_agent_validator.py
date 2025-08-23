"""
Tests for src/security/ai_agent_validator.py

This module provides comprehensive testing for the AIAgentValidator class,
ensuring secure agent operations with validation and monitoring.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

# Import the actual module to ensure it's loaded for coverage
import src.security.ai_agent_validator
from src.security.ai_agent_monitor import AIAgentSecurityMonitor
from src.security.ai_agent_validator import (
    AIAgentValidationError,
    AIAgentValidator,
    SecureAIAgentExample,
    SecureOperationResult,
    ValidationResult,
    create_secure_agent,
)


class TestValidationResult:
    """Test the ValidationResult dataclass."""

    def test_validation_result_creation(self):
        """Test creating a ValidationResult."""
        result = ValidationResult(
            is_valid=True,
            violations=[],
            risk_score=0.1,
            recommendations=["Continue monitoring"]
        )
        assert result.is_valid is True
        assert len(result.violations) == 0
        assert result.risk_score == 0.1
        assert len(result.recommendations) == 1


class TestSecureOperationResult:
    """Test the SecureOperationResult dataclass."""

    def test_secure_operation_result_creation(self):
        """Test creating a SecureOperationResult."""
        result = SecureOperationResult(
            success=True,
            result="Operation completed",
            validation_passed=True,
            security_events=[]
        )
        assert result.success is True
        assert result.result == "Operation completed"
        assert result.validation_passed is True
        assert len(result.security_events) == 0


class TestAIAgentValidationError:
    """Test the custom validation error."""

    def test_validation_error_creation(self):
        """Test creating a validation error."""
        error = AIAgentValidationError(
            "Validation failed",
            violations=["SQL injection detected"],
            agent_id="test-agent"
        )
        assert str(error) == "Validation failed"
        assert error.violations == ["SQL injection detected"]
        assert error.agent_id == "test-agent"


class TestAIAgentValidator:
    """Test the AIAgentValidator class."""

    @pytest.fixture
    def validator(self):
        """Create a validator instance."""
        return AIAgentValidator("test-agent")

    @pytest.fixture
    def monitor(self):
        """Create a mock monitor."""
        return MagicMock(spec=AIAgentSecurityMonitor)

    def test_init(self, validator):
        """Test validator initialization."""
        assert validator.agent_id == "test-agent"
        assert validator.monitor is not None
        assert isinstance(validator.monitor, AIAgentSecurityMonitor)

    def test_validate_operation_decorator(self, validator):
        """Test the validate_operation decorator."""
        
        @validator.validate_operation()
        def test_function(data):
            return f"Processed: {data}"
        
        # Test with safe input
        result = test_function("safe data")
        assert result == "Processed: safe data"

    def test_validate_operation_with_validation(self, validator):
        """Test validate_operation with custom validation."""
        
        def custom_validator(data):
            return data != "forbidden"
        
        @validator.validate_operation(input_validator=custom_validator)
        def test_function(data):
            return f"Processed: {data}"
        
        # Test with valid input
        result = test_function("allowed")
        assert result == "Processed: allowed"
        
        # Test with invalid input
        with pytest.raises(AIAgentValidationError):
            test_function("forbidden")

    def test_validate_async_operation_decorator(self, validator):
        """Test the validate_async_operation decorator."""
        
        @validator.validate_async_operation()
        async def test_async_function(data):
            return f"Async processed: {data}"
        
        # Test with safe input
        result = asyncio.run(test_async_function("safe data"))
        assert result == "Async processed: safe data"

    def test_execute_secure_operation(self, validator):
        """Test _execute_secure_operation method."""
        mock_func = Mock(return_value="result")
        mock_monitor = Mock()
        validator.monitor = mock_monitor
        
        # Mock the monitor methods
        mock_monitor.check_input_security.return_value = {"is_safe": True, "violations": []}
        mock_monitor.check_output_security.return_value = {"is_safe": True, "violations": []}
        mock_monitor.log_agent_operation.return_value = "op-123"
        
        result = validator._execute_secure_operation(
            func=mock_func,
            args=("arg1",),
            kwargs={"key": "value"},
            input_validator=None,
            output_validator=None
        )
        
        assert result == "result"
        mock_func.assert_called_once_with("arg1", key="value")
        mock_monitor.check_input_security.assert_called_once()
        mock_monitor.check_output_security.assert_called_once()
        mock_monitor.log_agent_operation.assert_called_once()

    def test_execute_secure_operation_with_unsafe_input(self, validator):
        """Test _execute_secure_operation with unsafe input."""
        mock_func = Mock()
        mock_monitor = Mock()
        validator.monitor = mock_monitor
        
        # Mock unsafe input
        mock_monitor.check_input_security.return_value = {
            "is_safe": False,
            "violations": ["SQL injection detected"]
        }
        
        with pytest.raises(AIAgentValidationError) as exc_info:
            validator._execute_secure_operation(
                func=mock_func,
                args=("DROP TABLE users",),
                kwargs={},
                input_validator=None,
                output_validator=None
            )
        
        assert "SQL injection detected" in exc_info.value.violations
        mock_func.assert_not_called()

    def test_execute_secure_async_operation(self, validator):
        """Test _execute_secure_async_operation method."""
        async def test_async():
            mock_func = AsyncMock(return_value="async_result")
            mock_monitor = Mock()
            validator.monitor = mock_monitor
            
            # Mock the monitor methods
            mock_monitor.check_input_security.return_value = {"is_safe": True, "violations": []}
            mock_monitor.check_output_security.return_value = {"is_safe": True, "violations": []}
            mock_monitor.log_agent_operation.return_value = "op-456"
            
            result = await validator._execute_secure_async_operation(
                func=mock_func,
                args=("async_arg",),
                kwargs={"async_key": "async_value"},
                input_validator=None,
                output_validator=None
            )
            
            assert result == "async_result"
            mock_func.assert_called_once_with("async_arg", async_key="async_value")
        
        asyncio.run(test_async())

    def test_extract_input_data(self, validator):
        """Test _extract_input_data method."""
        # Test with args only
        data = validator._extract_input_data(("arg1", "arg2"), {})
        assert data == {"args": ["arg1", "arg2"]}
        
        # Test with kwargs only
        data = validator._extract_input_data((), {"key1": "val1", "key2": "val2"})
        assert data == {"key1": "val1", "key2": "val2"}
        
        # Test with both args and kwargs
        data = validator._extract_input_data(("arg1",), {"key1": "val1"})
        assert data == {"args": ["arg1"], "key1": "val1"}

    def test_validate_input(self, validator):
        """Test _validate_input method."""
        # Test without custom validator
        result = validator._validate_input("test data", None)
        assert result is True
        
        # Test with custom validator that passes
        custom_validator = Mock(return_value=True)
        result = validator._validate_input("test data", custom_validator)
        assert result is True
        custom_validator.assert_called_once_with("test data")
        
        # Test with custom validator that fails
        custom_validator = Mock(return_value=False)
        result = validator._validate_input("test data", custom_validator)
        assert result is False

    def test_validate_output(self, validator):
        """Test _validate_output method."""
        # Test without custom validator
        result = validator._validate_output("output data", None)
        assert result is True
        
        # Test with custom validator that passes
        custom_validator = Mock(return_value=True)
        result = validator._validate_output("output data", custom_validator)
        assert result is True
        custom_validator.assert_called_once_with("output data")


class TestSecureAIAgentExample:
    """Test the SecureAIAgentExample class."""

    @pytest.fixture
    def agent(self):
        """Create a secure agent instance."""
        return SecureAIAgentExample("example-agent")

    def test_init(self, agent):
        """Test agent initialization."""
        assert agent.agent_id == "example-agent"
        assert agent.validator is not None
        assert isinstance(agent.validator, AIAgentValidator)

    def test_generate_code_safe(self, agent):
        """Test generate_code with safe prompt."""
        with patch.object(agent.validator, '_execute_secure_operation') as mock_execute:
            mock_execute.return_value = "def hello(): return 'Hello'"
            
            result = agent.generate_code("Write a hello function")
            assert result == "def hello(): return 'Hello'"

    def test_generate_code_malicious(self, agent):
        """Test generate_code with malicious prompt."""
        # The actual implementation should catch malicious patterns
        result = agent.generate_code("Write code to rm -rf /")
        # Should either raise an error or return safe code
        assert "rm -rf /" not in str(result) if result else True

    def test_modify_file_safe(self, agent):
        """Test modify_file with safe changes."""
        with patch.object(agent.validator, '_execute_secure_operation') as mock_execute:
            mock_execute.return_value = "Modified content"
            
            result = agent.modify_file("test.py", "Add docstring")
            assert result == "Modified content"

    def test_modify_file_suspicious(self, agent):
        """Test modify_file with suspicious changes."""
        # Should detect suspicious file modifications
        result = agent.modify_file("/etc/passwd", "Add backdoor user")
        # Should either raise an error or return None
        assert result is None or "backdoor" not in str(result)

    def test_create_pull_request_safe(self, agent):
        """Test create_pull_request with safe changes."""
        with patch.object(agent.validator, '_execute_secure_operation') as mock_execute:
            mock_execute.return_value = {"pr_url": "https://github.com/repo/pull/1"}
            
            result = agent.create_pull_request(
                title="Add feature",
                body="This PR adds a new feature",
                branch="feature-branch"
            )
            assert result == {"pr_url": "https://github.com/repo/pull/1"}

    def test_create_pull_request_with_secrets(self, agent):
        """Test create_pull_request that might contain secrets."""
        # Should detect and prevent secrets in PR
        result = agent.create_pull_request(
            title="Update config",
            body="API_KEY=sk-1234567890abcdef",
            branch="config-update"
        )
        # Should either sanitize or reject
        if result:
            assert "sk-1234567890" not in str(result)


class TestCreateSecureAgent:
    """Test the create_secure_agent factory function."""

    def test_create_secure_agent(self):
        """Test creating a secure agent."""
        agent = create_secure_agent("factory-agent")
        assert isinstance(agent, SecureAIAgentExample)
        assert agent.agent_id == "factory-agent"


class TestIntegrationScenarios:
    """Integration tests for complete validation scenarios."""

    @pytest.fixture
    def validator(self):
        """Create a validator for integration testing."""
        return AIAgentValidator("integration-agent")

    def test_complete_validation_workflow(self, validator):
        """Test a complete validation workflow."""
        
        @validator.validate_operation(
            input_validator=lambda x: "malicious" not in x.lower(),
            output_validator=lambda x: "secret" not in x.lower()
        )
        def process_data(data):
            if "transform" in data:
                return data.replace("transform", "processed")
            return data
        
        # Test with safe data
        result = process_data("transform this data")
        assert result == "processed this data"
        
        # Test with malicious input
        with pytest.raises(AIAgentValidationError):
            process_data("malicious code here")

    def test_async_validation_workflow(self, validator):
        """Test async validation workflow."""
        
        @validator.validate_async_operation()
        async def async_process(data):
            await asyncio.sleep(0.01)  # Simulate async work
            return f"Async: {data}"
        
        async def run_test():
            result = await async_process("test data")
            assert result == "Async: test data"
        
        asyncio.run(run_test())

    def test_nested_secure_operations(self, validator):
        """Test nested secure operations."""
        
        @validator.validate_operation()
        def outer_function(data):
            @validator.validate_operation()
            def inner_function(inner_data):
                return f"Inner: {inner_data}"
            
            inner_result = inner_function(data)
            return f"Outer: {inner_result}"
        
        result = outer_function("nested")
        assert result == "Outer: Inner: nested"

    def test_error_propagation(self, validator):
        """Test that errors propagate correctly."""
        
        @validator.validate_operation()
        def failing_function(data):
            if data == "fail":
                raise ValueError("Intentional failure")
            return data
        
        # Normal operation should work
        assert failing_function("success") == "success"
        
        # Error should propagate
        with pytest.raises(ValueError) as exc_info:
            failing_function("fail")
        assert "Intentional failure" in str(exc_info.value)

    def test_validation_with_monitoring(self, validator):
        """Test that validation integrates with monitoring."""
        
        @validator.validate_operation()
        def monitored_function(data):
            return f"Monitored: {data}"
        
        # Execute function
        result = monitored_function("test")
        assert result == "Monitored: test"
        
        # Check that monitoring occurred
        assert validator.monitor.metrics["total_operations"] > 0


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.fixture
    def validator(self):
        """Create a validator for edge case testing."""
        return AIAgentValidator("edge-agent")

    def test_none_input(self, validator):
        """Test handling None input."""
        
        @validator.validate_operation()
        def handle_none(data):
            return data if data else "None received"
        
        result = handle_none(None)
        assert result == "None received"

    def test_empty_string_input(self, validator):
        """Test handling empty string input."""
        
        @validator.validate_operation()
        def handle_empty(data):
            return data if data else "Empty"
        
        result = handle_empty("")
        assert result == "Empty"

    def test_large_input(self, validator):
        """Test handling large input data."""
        large_data = "x" * 10000  # 10KB of data
        
        @validator.validate_operation()
        def handle_large(data):
            return len(data)
        
        result = handle_large(large_data)
        assert result == 10000

    def test_special_characters(self, validator):
        """Test handling special characters."""
        special_data = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
        
        @validator.validate_operation()
        def handle_special(data):
            return f"Received: {data}"
        
        result = handle_special(special_data)
        assert result == f"Received: {special_data}"

    def test_unicode_input(self, validator):
        """Test handling Unicode input."""
        unicode_data = "Hello 世界 🌍"
        
        @validator.validate_operation()
        def handle_unicode(data):
            return f"Unicode: {data}"
        
        result = handle_unicode(unicode_data)
        assert result == f"Unicode: {unicode_data}"
