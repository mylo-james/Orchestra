"""
Comprehensive tests for src/security/ai_agent_validator.py

Tests the AI Agent Validation framework including:
- Input/output validation
- Security monitoring integration
- Decorator functionality
- Error handling and logging
- Example agent implementations
"""

import asyncio
from unittest.mock import Mock, patch

import pytest

# Import the module to ensure it's loaded for coverage
from src.security.ai_agent_validator import (
    AIAgentValidationError,
    AIAgentValidator,
    SecureAIAgentExample,
    SecureOperationResult,
    ValidationResult,
    create_secure_agent,
    test_ai_agent_validation,
)


class TestValidationResult:
    """Test ValidationResult dataclass."""

    def test_validation_result_creation(self):
        """Test ValidationResult creation with all fields."""
        result = ValidationResult(
            is_valid=True, violations=[], action="allow", severity="low"
        )

        assert result.is_valid is True
        assert result.violations == []
        assert result.action == "allow"
        assert result.severity == "low"

    def test_validation_result_with_violations(self):
        """Test ValidationResult with violations."""
        violations = ["prompt_injection", "suspicious_pattern"]
        result = ValidationResult(
            is_valid=False, violations=violations, action="block", severity="high"
        )

        assert result.is_valid is False
        assert result.violations == violations
        assert result.action == "block"
        assert result.severity == "high"


class TestSecureOperationResult:
    """Test SecureOperationResult dataclass."""

    def test_secure_operation_result_success(self):
        """Test successful SecureOperationResult."""
        input_validation = ValidationResult(True, [], "allow", "low")
        output_validation = ValidationResult(True, [], "allow", "low")

        result = SecureOperationResult(
            success=True,
            result="test output",
            operation_id="op-123",
            input_validation=input_validation,
            output_validation=output_validation,
        )

        assert result.success is True
        assert result.result == "test output"
        assert result.operation_id == "op-123"
        assert result.input_validation == input_validation
        assert result.output_validation == output_validation
        assert result.error is None

    def test_secure_operation_result_failure(self):
        """Test failed SecureOperationResult."""
        input_validation = ValidationResult(False, ["error"], "block", "high")

        result = SecureOperationResult(
            success=False,
            result=None,
            operation_id="",
            input_validation=input_validation,
            error="Validation failed",
        )

        assert result.success is False
        assert result.result is None
        assert result.operation_id == ""
        assert result.input_validation == input_validation
        assert result.output_validation is None
        assert result.error == "Validation failed"


class TestAIAgentValidationError:
    """Test AIAgentValidationError exception."""

    def test_validation_error_creation(self):
        """Test AIAgentValidationError creation."""
        violations = ["prompt_injection", "malicious_code"]
        error = AIAgentValidationError("Validation failed", violations, "critical")

        assert str(error) == "Validation failed"
        assert error.violations == violations
        assert error.severity == "critical"

    def test_validation_error_inheritance(self):
        """Test that AIAgentValidationError inherits from Exception."""
        error = AIAgentValidationError("test", [], "low")
        assert isinstance(error, Exception)


class TestAIAgentValidator:
    """Test AIAgentValidator class."""

    @patch("src.security.ai_agent_validator.AIAgentSecurityMonitor")
    def test_validator_initialization(self, mock_monitor_class):
        """Test AIAgentValidator initialization."""
        mock_monitor = Mock()
        mock_monitor_class.return_value = mock_monitor

        validator = AIAgentValidator("test-agent")

        assert validator.agent_id == "test-agent"
        assert validator.monitor == mock_monitor
        mock_monitor_class.assert_called_once()

    @patch("src.security.ai_agent_validator.AIAgentSecurityMonitor")
    def test_extract_input_data_from_kwargs(self, mock_monitor_class):
        """Test input data extraction from kwargs."""
        validator = AIAgentValidator("test-agent")

        # Test prompt parameter
        result = validator._extract_input_data((), {"prompt": "test prompt"})
        assert result == "test prompt"

        # Test input parameter
        result = validator._extract_input_data((), {"input": "test input"})
        assert result == "test input"

        # Test request parameter
        result = validator._extract_input_data((), {"request": "test request"})
        assert result == "test request"

    @patch("src.security.ai_agent_validator.AIAgentSecurityMonitor")
    def test_extract_input_data_from_args(self, mock_monitor_class):
        """Test input data extraction from args."""
        validator = AIAgentValidator("test-agent")

        # Test first string argument
        result = validator._extract_input_data(("test string", 123), {})
        assert result == "test string"

        # Test no string arguments
        result = validator._extract_input_data((123, 456), {"num": 789})
        assert result == "(123, 456){'num': 789}"

    @patch("src.security.ai_agent_validator.AIAgentSecurityMonitor")
    def test_validate_input(self, mock_monitor_class):
        """Test input validation."""
        mock_monitor = Mock()
        mock_monitor_class.return_value = mock_monitor
        mock_monitor.check_input_security.return_value = {
            "is_safe": True,
            "violations": [],
            "action": "allow",
            "severity": "low",
        }

        validator = AIAgentValidator("test-agent")
        result = validator._validate_input("test input", "code_generation")

        assert isinstance(result, ValidationResult)
        assert result.is_valid is True
        assert result.violations == []
        assert result.action == "allow"
        assert result.severity == "low"

        mock_monitor.check_input_security.assert_called_once_with(
            "test-agent", "test input", "code_generation"
        )

    @patch("src.security.ai_agent_validator.AIAgentSecurityMonitor")
    def test_validate_output(self, mock_monitor_class):
        """Test output validation."""
        mock_monitor = Mock()
        mock_monitor_class.return_value = mock_monitor
        mock_monitor.check_output_security.return_value = {
            "is_safe": False,
            "violations": ["malicious_code"],
            "action": "block",
            "severity": "high",
        }

        validator = AIAgentValidator("test-agent")
        result = validator._validate_output("malicious output", "code_generation")

        assert isinstance(result, ValidationResult)
        assert result.is_valid is False
        assert result.violations == ["malicious_code"]
        assert result.action == "block"
        assert result.severity == "high"

        mock_monitor.check_output_security.assert_called_once_with(
            "test-agent", "malicious output", "code_generation"
        )

    @patch("src.security.ai_agent_validator.AIAgentSecurityMonitor")
    def test_validate_operation_decorator_success(self, mock_monitor_class):
        """Test validate_operation decorator with successful operation."""
        mock_monitor = Mock()
        mock_monitor_class.return_value = mock_monitor
        mock_monitor.check_input_security.return_value = {
            "is_safe": True,
            "violations": [],
            "action": "allow",
            "severity": "low",
        }
        mock_monitor.check_output_security.return_value = {
            "is_safe": True,
            "violations": [],
            "action": "allow",
            "severity": "low",
        }
        mock_monitor.log_agent_operation.return_value = "op-123"

        validator = AIAgentValidator("test-agent")

        @validator.validate_operation("code_generation")
        def test_function(prompt: str) -> str:
            return f"Generated: {prompt}"

        result = test_function("test prompt")

        assert isinstance(result, SecureOperationResult)
        assert result.success is True
        assert result.result == "Generated: test prompt"
        assert result.operation_id == "op-123"
        assert result.input_validation.is_valid is True
        assert result.output_validation.is_valid is True

    @patch("src.security.ai_agent_validator.AIAgentSecurityMonitor")
    def test_validate_operation_decorator_input_blocked(self, mock_monitor_class):
        """Test validate_operation decorator with blocked input."""
        mock_monitor = Mock()
        mock_monitor_class.return_value = mock_monitor
        mock_monitor.check_input_security.return_value = {
            "is_safe": False,
            "violations": ["prompt_injection"],
            "action": "block",
            "severity": "high",
        }

        validator = AIAgentValidator("test-agent")

        @validator.validate_operation("code_generation")
        def test_function(prompt: str) -> str:
            return f"Generated: {prompt}"

        with pytest.raises(AIAgentValidationError) as exc_info:
            test_function("malicious prompt")

        assert "Input validation failed" in str(exc_info.value)
        assert exc_info.value.violations == ["prompt_injection"]
        assert exc_info.value.severity == "high"

    @patch("src.security.ai_agent_validator.AIAgentSecurityMonitor")
    def test_validate_operation_decorator_output_blocked(self, mock_monitor_class):
        """Test validate_operation decorator with blocked output."""
        mock_monitor = Mock()
        mock_monitor_class.return_value = mock_monitor
        mock_monitor.check_input_security.return_value = {
            "is_safe": True,
            "violations": [],
            "action": "allow",
            "severity": "low",
        }
        mock_monitor.check_output_security.return_value = {
            "is_safe": False,
            "violations": ["malicious_code"],
            "action": "block",
            "severity": "critical",
        }

        validator = AIAgentValidator("test-agent")

        @validator.validate_operation("code_generation")
        def test_function(prompt: str) -> str:
            return "rm -rf /"

        with pytest.raises(AIAgentValidationError) as exc_info:
            test_function("test prompt")

        assert "Output validation failed" in str(exc_info.value)
        assert exc_info.value.violations == ["malicious_code"]
        assert exc_info.value.severity == "critical"

    @patch("src.security.ai_agent_validator.AIAgentSecurityMonitor")
    def test_validate_operation_decorator_function_error(self, mock_monitor_class):
        """Test validate_operation decorator with function error."""
        mock_monitor = Mock()
        mock_monitor_class.return_value = mock_monitor
        mock_monitor.check_input_security.return_value = {
            "is_safe": True,
            "violations": [],
            "action": "allow",
            "severity": "low",
        }

        validator = AIAgentValidator("test-agent")

        @validator.validate_operation("code_generation")
        def test_function(prompt: str) -> str:
            raise ValueError("Test error")

        result = test_function("test prompt")

        assert isinstance(result, SecureOperationResult)
        assert result.success is False
        assert result.result is None
        assert result.error == "Test error"
        assert result.input_validation.is_valid is True


class TestConvenienceFunction:
    """Test convenience functions."""

    @patch("src.security.ai_agent_validator.AIAgentValidator")
    def test_create_secure_agent(self, mock_validator_class):
        """Test create_secure_agent convenience function."""
        mock_validator = Mock()
        mock_validator_class.return_value = mock_validator

        result = create_secure_agent("test-agent-123")

        assert result == mock_validator
        mock_validator_class.assert_called_once_with("test-agent-123")


class TestSecureAIAgentExample:
    """Test SecureAIAgentExample class."""

    @patch("src.security.ai_agent_validator.create_secure_agent")
    def test_secure_agent_example_initialization(self, mock_create_secure_agent):
        """Test SecureAIAgentExample initialization."""
        mock_validator = Mock()
        mock_create_secure_agent.return_value = mock_validator

        agent = SecureAIAgentExample("example-agent")

        assert agent.agent_id == "example-agent"
        assert agent.validator == mock_validator
        mock_create_secure_agent.assert_called_once_with("example-agent")

    @patch("src.security.ai_agent_validator.create_secure_agent")
    def test_generate_code_success(self, mock_create_secure_agent):
        """Test generate_code method with successful validation."""
        mock_validator = Mock()
        mock_create_secure_agent.return_value = mock_validator

        # Mock successful validation
        mock_validator._validate_input.return_value = ValidationResult(
            True, [], "allow", "low"
        )
        mock_validator._validate_output.return_value = ValidationResult(
            True, [], "allow", "low"
        )
        mock_validator.monitor.log_agent_operation.return_value = "op-123"

        agent = SecureAIAgentExample("example-agent")
        result = agent.generate_code("hello world function")

        assert "def hello_world():" in result
        assert "Hello, World!" in result
        mock_validator._validate_input.assert_called_once()
        mock_validator._validate_output.assert_called_once()
        mock_validator.monitor.log_agent_operation.assert_called_once()

    @patch("src.security.ai_agent_validator.create_secure_agent")
    def test_generate_code_input_blocked(self, mock_create_secure_agent):
        """Test generate_code method with blocked input."""
        mock_validator = Mock()
        mock_create_secure_agent.return_value = mock_validator

        # Mock blocked input validation
        mock_validator._validate_input.return_value = ValidationResult(
            False, ["malicious_pattern"], "block", "high"
        )

        agent = SecureAIAgentExample("example-agent")

        with pytest.raises(AIAgentValidationError) as exc_info:
            agent.generate_code("malicious prompt")

        assert "Input validation failed" in str(exc_info.value)
        assert exc_info.value.violations == ["malicious_pattern"]

    @patch("src.security.ai_agent_validator.create_secure_agent")
    def test_modify_file_success(self, mock_create_secure_agent):
        """Test modify_file method with successful validation."""
        mock_validator = Mock()
        mock_create_secure_agent.return_value = mock_validator

        # Mock successful validation
        mock_validator._validate_input.return_value = ValidationResult(
            True, [], "allow", "low"
        )
        mock_validator._validate_output.return_value = ValidationResult(
            True, [], "allow", "low"
        )
        mock_validator.monitor.log_agent_operation.return_value = "op-456"

        agent = SecureAIAgentExample("example-agent")
        result = agent.modify_file("test.py", "print('hello')")

        assert "Modified test.py with 14 characters" == result
        mock_validator._validate_input.assert_called_once()
        mock_validator._validate_output.assert_called_once()
        mock_validator.monitor.log_agent_operation.assert_called_once()

    @patch("src.security.ai_agent_validator.create_secure_agent")
    def test_create_pull_request_success(self, mock_create_secure_agent):
        """Test create_pull_request method with successful validation."""
        mock_validator = Mock()
        mock_create_secure_agent.return_value = mock_validator

        # Mock successful validation (no output validation for git operations)
        mock_validator._validate_input.return_value = ValidationResult(
            True, [], "allow", "low"
        )
        mock_validator.monitor.log_agent_operation.return_value = "op-789"

        agent = SecureAIAgentExample("example-agent")
        result = agent.create_pull_request("Fix bug", "This fixes the bug")

        assert result == "Created PR: Fix bug"
        mock_validator._validate_input.assert_called_once()
        mock_validator.monitor.log_agent_operation.assert_called_once()


class TestMainFunction:
    """Test main test function."""

    @patch("src.security.ai_agent_validator.SecureAIAgentExample")
    @patch("builtins.print")
    def test_ai_agent_validation_test_function(self, mock_print, mock_agent_class):
        """Test test_ai_agent_validation function."""
        mock_agent = Mock()
        mock_agent_class.return_value = mock_agent

        # Mock successful operations
        mock_agent.generate_code.return_value = "def hello_world(): pass"
        mock_agent.modify_file.return_value = "Modified config.py"

        # Test that function runs without error
        test_ai_agent_validation()

        # Verify agent was created and methods called
        mock_agent_class.assert_called_once_with("test-orchestrator-001")
        assert mock_agent.generate_code.call_count >= 2  # At least 2 calls in test
        mock_agent.modify_file.assert_called_once()

        # Verify print statements were made
        assert mock_print.call_count > 0


class TestAsyncValidatorMissingCoverage:
    """Test async validation functionality to cover missing lines 126-140 and 243-316."""

    @pytest.fixture
    def validator(self):
        """Create AIAgentValidator instance."""
        return AIAgentValidator("async-test-agent")

    @pytest.mark.asyncio
    async def test_validate_async_operation_decorator_success(self, validator):
        """Test validate_async_operation decorator - covers lines 126-140."""

        # Mock the monitoring system
        with (
            patch.object(
                validator.monitor, "log_agent_operation", return_value="async-op-123"
            ),
            patch.object(
                validator,
                "_validate_input",
                return_value=ValidationResult(True, [], "allow", "low"),
            ),
            patch.object(
                validator,
                "_validate_output",
                return_value=ValidationResult(True, [], "allow", "low"),
            ),
        ):

            @validator.validate_async_operation("async_code_generation")
            async def async_generate_code(prompt: str) -> str:
                await asyncio.sleep(0.001)  # Simulate async work
                return f"Generated code for: {prompt}"

            result = await async_generate_code("Create async function")

            # Verify successful execution through decorator
            assert result.success is True
            assert "Generated code for: Create async function" in str(result.result)
            assert result.input_validation.is_valid is True

    @pytest.mark.asyncio
    async def test_validate_async_operation_input_validation_failure(self, validator):
        """Test async operation with input validation failure - covers lines 243-316."""

        # Mock validation to fail
        with patch.object(
            validator,
            "_validate_input",
            return_value=ValidationResult(False, ["Malicious input"], "block", "high"),
        ):

            @validator.validate_async_operation(
                "async_code_generation", block_on_violations=True
            )
            async def async_generate_malicious_code(prompt: str) -> str:
                await asyncio.sleep(0.001)
                return "This should not execute"

            # Should raise validation error
            with pytest.raises(AIAgentValidationError) as exc_info:
                await async_generate_malicious_code("malicious prompt")

            assert "Input validation failed" in str(exc_info.value)
            assert exc_info.value.violations == ["Malicious input"]

    @pytest.mark.asyncio
    async def test_validate_async_operation_output_validation_failure(self, validator):
        """Test async operation with output validation failure - covers error handling."""

        with (
            patch.object(
                validator.monitor, "log_agent_operation", return_value="async-op-456"
            ),
            patch.object(
                validator,
                "_validate_input",
                return_value=ValidationResult(True, [], "allow", "low"),
            ),
            patch.object(
                validator,
                "_validate_output",
                return_value=ValidationResult(
                    False, ["Dangerous output"], "block", "high"
                ),
            ),
        ):

            @validator.validate_async_operation(
                "async_code_generation", block_on_violations=True
            )
            async def async_generate_dangerous_output(prompt: str) -> str:
                await asyncio.sleep(0.001)
                return "import os; os.system('rm -rf /')"  # Dangerous code

            # Should raise validation error for output
            with pytest.raises(AIAgentValidationError) as exc_info:
                await async_generate_dangerous_output("safe prompt")

            assert "Output validation failed" in str(exc_info.value)
            assert exc_info.value.violations == ["Dangerous output"]

    @pytest.mark.asyncio
    async def test_async_operation_with_logging_disabled(self, validator):
        """Test async operation with logging disabled."""

        with (
            patch.object(validator.monitor, "log_agent_operation") as mock_log,
            patch.object(
                validator,
                "_validate_input",
                return_value=ValidationResult(True, [], "allow", "low"),
            ),
            patch.object(
                validator,
                "_validate_output",
                return_value=ValidationResult(True, [], "allow", "low"),
            ),
        ):

            @validator.validate_async_operation("async_test", log_operations=False)
            async def async_no_log_operation(data: str) -> str:
                await asyncio.sleep(0.001)
                return f"Processed: {data}"

            result = await async_no_log_operation("test data")

            # Verify logging was not called when disabled
            mock_log.assert_not_called()
            assert result.success is True
