"""
AI Agent Input/Output Validation Wrapper

This module provides a secure wrapper for AI agent operations with
comprehensive input validation and output scanning.
"""

import asyncio
import functools
import logging
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Optional, TypeVar

from .ai_agent_monitor import (
    AIAgentSecurityMonitor,
    SecurityEventType,
    SecuritySeverity,
)

logger = logging.getLogger(__name__)

# Type variables for generic decorator support
F = TypeVar("F", bound=Callable[..., Any])
AsyncF = TypeVar("AsyncF", bound=Callable[..., Awaitable[Any]])


@dataclass
class ValidationResult:
    """Result of input/output validation."""

    is_valid: bool
    violations: list
    action: str  # "allow", "warn", "block"
    severity: str


@dataclass
class SecureOperationResult:
    """Result of a secure AI agent operation."""

    success: bool
    result: Any
    operation_id: str
    input_validation: ValidationResult
    output_validation: Optional[ValidationResult] = None
    error: Optional[str] = None


class AIAgentValidationError(Exception):
    """Raised when AI agent validation fails."""

    def __init__(self, message: str, violations: list, severity: str):
        super().__init__(message)
        self.violations = violations
        self.severity = severity


class AIAgentValidator:
    """
    Secure validation wrapper for AI agent operations.

    This class provides:
    - Input validation and sanitization
    - Output scanning and filtering
    - Operation logging and audit trails
    - Rate limiting and abuse prevention
    """

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.monitor = AIAgentSecurityMonitor()
        logger.info(f"AI Agent Validator initialized for agent: {agent_id}")

    def validate_operation(
        self,
        operation_type: str,
        block_on_violations: bool = True,
        log_operations: bool = True,
    ):
        """
        Decorator to validate AI agent operations.

        Args:
            operation_type: Type of operation (e.g., "code_generation", "file_modification")
            block_on_violations: Whether to block operation on security violations
            log_operations: Whether to log operations for audit trail

        Usage:
            @validator.validate_operation("code_generation")
            def generate_code(self, prompt: str) -> str:
                # AI agent code generation logic
                return generated_code
        """

        def decorator(func: F) -> F:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return self._execute_secure_operation(
                    func,
                    operation_type,
                    block_on_violations,
                    log_operations,
                    args,
                    kwargs,
                )

            return wrapper

        return decorator

    def validate_async_operation(
        self,
        operation_type: str,
        block_on_violations: bool = True,
        log_operations: bool = True,
    ):
        """
        Decorator to validate async AI agent operations.

        Args:
            operation_type: Type of operation
            block_on_violations: Whether to block operation on security violations
            log_operations: Whether to log operations for audit trail
        """

        def decorator(func: AsyncF) -> AsyncF:
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                return await self._execute_secure_async_operation(
                    func,
                    operation_type,
                    block_on_violations,
                    log_operations,
                    args,
                    kwargs,
                )

            return wrapper

        return decorator

    def _execute_secure_operation(
        self,
        func: Callable,
        operation_type: str,
        block_on_violations: bool,
        log_operations: bool,
        args: tuple,
        kwargs: dict,
    ) -> SecureOperationResult:
        """Execute a secure operation with validation."""

        # Extract input data (assume first string arg or 'prompt'/'input' kwarg)
        input_data = self._extract_input_data(args, kwargs)

        # Validate input
        input_validation = self._validate_input(input_data, operation_type)

        if not input_validation.is_valid and block_on_violations:
            if input_validation.action == "block":
                raise AIAgentValidationError(
                    f"Input validation failed for {operation_type}",
                    input_validation.violations,
                    input_validation.severity,
                )

        # Execute the operation
        try:
            result = func(*args, **kwargs)

            # Validate output
            output_validation = None
            if isinstance(result, str):
                output_validation = self._validate_output(result, operation_type)

                if not output_validation.is_valid and block_on_violations:
                    if output_validation.action == "block":
                        raise AIAgentValidationError(
                            f"Output validation failed for {operation_type}",
                            output_validation.violations,
                            output_validation.severity,
                        )

            # Log successful operation
            operation_id = ""
            if log_operations:
                operation_id = self.monitor.log_agent_operation(
                    agent_id=self.agent_id,
                    operation_type=operation_type,
                    input_data=input_data,
                    output_data=str(result) if result else None,
                    metadata={
                        "function": func.__name__,
                        "input_validation": input_validation.__dict__,
                        "output_validation": (
                            output_validation.__dict__ if output_validation else None
                        ),
                    },
                )

            return SecureOperationResult(
                success=True,
                result=result,
                operation_id=operation_id,
                input_validation=input_validation,
                output_validation=output_validation,
            )

        except AIAgentValidationError:
            # Re-raise validation errors
            raise
        except Exception as e:
            # Log operation failure
            if log_operations:
                self.monitor.log_security_event(
                    SecurityEventType.SUSPICIOUS_BEHAVIOR,
                    self.agent_id,
                    f"Operation {operation_type} failed: {str(e)}",
                    SecuritySeverity.MEDIUM,
                    {"function": func.__name__, "error": str(e)},
                )

            return SecureOperationResult(
                success=False,
                result=None,
                operation_id="",
                input_validation=input_validation,
                error=str(e),
            )

    async def _execute_secure_async_operation(
        self,
        func: Callable,
        operation_type: str,
        block_on_violations: bool,
        log_operations: bool,
        args: tuple,
        kwargs: dict,
    ) -> SecureOperationResult:
        """Execute a secure async operation with validation."""

        # Extract input data
        input_data = self._extract_input_data(args, kwargs)

        # Validate input
        input_validation = self._validate_input(input_data, operation_type)

        if not input_validation.is_valid and block_on_violations:
            if input_validation.action == "block":
                raise AIAgentValidationError(
                    f"Input validation failed for {operation_type}",
                    input_validation.violations,
                    input_validation.severity,
                )

        # Execute the async operation
        try:
            result = await func(*args, **kwargs)

            # Validate output
            output_validation = None
            if isinstance(result, str):
                output_validation = self._validate_output(result, operation_type)

                if not output_validation.is_valid and block_on_violations:
                    if output_validation.action == "block":
                        raise AIAgentValidationError(
                            f"Output validation failed for {operation_type}",
                            output_validation.violations,
                            output_validation.severity,
                        )

            # Log successful operation
            operation_id = ""
            if log_operations:
                operation_id = self.monitor.log_agent_operation(
                    agent_id=self.agent_id,
                    operation_type=operation_type,
                    input_data=input_data,
                    output_data=str(result) if result else None,
                    metadata={
                        "function": func.__name__,
                        "async": True,
                        "input_validation": input_validation.__dict__,
                        "output_validation": (
                            output_validation.__dict__ if output_validation else None
                        ),
                    },
                )

            return SecureOperationResult(
                success=True,
                result=result,
                operation_id=operation_id,
                input_validation=input_validation,
                output_validation=output_validation,
            )

        except AIAgentValidationError:
            # Re-raise validation errors
            raise
        except Exception as e:
            # Log operation failure
            if log_operations:
                await asyncio.create_task(
                    asyncio.to_thread(
                        self.monitor.log_security_event,
                        SecurityEventType.SUSPICIOUS_BEHAVIOR,
                        self.agent_id,
                        f"Async operation {operation_type} failed: {str(e)}",
                        SecuritySeverity.MEDIUM,
                        {"function": func.__name__, "error": str(e), "async": True},
                    )
                )

            return SecureOperationResult(
                success=False,
                result=None,
                operation_id="",
                input_validation=input_validation,
                error=str(e),
            )

    def _extract_input_data(self, args: tuple, kwargs: dict) -> str:
        """Extract input data from function arguments."""
        # Try common parameter names first
        for key in ["prompt", "input", "request", "query", "data"]:
            if key in kwargs and isinstance(kwargs[key], str):
                return kwargs[key]

        # Try first string argument
        for arg in args:
            if isinstance(arg, str) and len(arg) > 0:
                return arg

        # Return string representation of all args
        return str(args) + str(kwargs)

    def _validate_input(self, input_data: str, operation_type: str) -> ValidationResult:
        """Validate input data for security issues."""
        check_result = self.monitor.check_input_security(
            self.agent_id, input_data, operation_type
        )

        return ValidationResult(
            is_valid=check_result["is_safe"],
            violations=check_result["violations"],
            action=check_result["action"],
            severity=check_result["severity"],
        )

    def _validate_output(
        self, output_data: str, operation_type: str
    ) -> ValidationResult:
        """Validate output data for security issues."""
        check_result = self.monitor.check_output_security(
            self.agent_id, output_data, operation_type
        )

        return ValidationResult(
            is_valid=check_result["is_safe"],
            violations=check_result["violations"],
            action=check_result["action"],
            severity=check_result["severity"],
        )


# Convenience function for quick validation
def create_secure_agent(agent_id: str) -> AIAgentValidator:
    """
    Create a secure AI agent validator.

    Args:
        agent_id: Unique identifier for the AI agent

    Returns:
        Configured validator for the agent

    Example:
        # In your AI agent class
        validator = create_secure_agent("orchestrator-001")

        @validator.validate_operation("code_generation")
        def generate_code(self, prompt: str) -> str:
            # Your AI agent code here
            return generated_code
    """
    return AIAgentValidator(agent_id)


# Example usage for AI agent implementation
class SecureAIAgentExample:
    """Example of how to use the validation framework in an AI agent."""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.validator = create_secure_agent(agent_id)

    def generate_code(self, prompt: str) -> str:
        """Generate code with security validation."""
        # Manually validate input and output
        input_validation = self.validator._validate_input(prompt, "code_generation")

        if not input_validation.is_valid and input_validation.action == "block":
            raise AIAgentValidationError(
                "Input validation failed for code generation",
                input_validation.violations,
                input_validation.severity,
            )

        # This would contain actual AI agent logic
        # For demonstration, return a simple response
        if "hello" in prompt.lower():
            result = "def hello_world():\n    print('Hello, World!')\n    return 'Hello, World!'"
        else:
            # Placeholder for actual code generation implementation
            result = f"# Generated code for: {prompt}\n# Implementation pending - using placeholder"
            result += "\ndef placeholder_function():\n    print('Code generation not yet implemented')\n    return None"

        # Validate output
        output_validation = self.validator._validate_output(result, "code_generation")

        if not output_validation.is_valid and output_validation.action == "block":
            raise AIAgentValidationError(
                "Output validation failed for code generation",
                output_validation.violations,
                output_validation.severity,
            )

        # Log the operation
        self.validator.monitor.log_agent_operation(
            agent_id=self.agent_id,
            operation_type="code_generation",
            input_data=prompt,
            output_data=result,
            metadata={"function": "generate_code"},
        )

        return result

    def modify_file(self, file_path: str, new_content: str) -> str:
        """Modify file with security validation."""
        # Validate input
        input_data = f"file_path: {file_path}, content: {new_content}"
        input_validation = self.validator._validate_input(
            input_data, "file_modification"
        )

        if not input_validation.is_valid and input_validation.action == "block":
            raise AIAgentValidationError(
                "Input validation failed for file modification",
                input_validation.violations,
                input_validation.severity,
            )

        # This would contain actual file modification logic
        result = f"Modified {file_path} with {len(new_content)} characters"

        # Validate output
        output_validation = self.validator._validate_output(result, "file_modification")

        if not output_validation.is_valid and output_validation.action == "block":
            raise AIAgentValidationError(
                "Output validation failed for file modification",
                output_validation.violations,
                output_validation.severity,
            )

        # Log the operation
        self.validator.monitor.log_agent_operation(
            agent_id=self.agent_id,
            operation_type="file_modification",
            input_data=input_data,
            output_data=result,
            metadata={"function": "modify_file", "file_path": file_path},
        )

        return result

    def create_pull_request(self, title: str, description: str) -> str:
        """Create pull request with security validation."""
        # Validate input
        input_data = f"title: {title}, description: {description}"
        input_validation = self.validator._validate_input(input_data, "git_operations")

        if not input_validation.is_valid and input_validation.action == "block":
            raise AIAgentValidationError(
                "Input validation failed for git operations",
                input_validation.violations,
                input_validation.severity,
            )

        # This would contain actual GitHub API logic
        result = f"Created PR: {title}"

        # Log the operation (git operations typically don't need output validation)
        self.validator.monitor.log_agent_operation(
            agent_id=self.agent_id,
            operation_type="git_operations",
            input_data=input_data,
            output_data=result,
            metadata={"function": "create_pull_request", "title": title},
        )

        return result


# Test function to demonstrate the validation system
def test_ai_agent_validation():
    """Test the AI agent validation framework."""
    print("🧪 Testing AI Agent Validation Framework")
    print("=" * 50)

    # Create test agent
    test_agent = SecureAIAgentExample("test-orchestrator-001")

    # Test 1: Safe code generation
    print("1. Testing safe code generation...")
    try:
        result = test_agent.generate_code("Create a hello world function")
        print("   ✅ Safe operation succeeded")
        print(f"   Result: {result[:50]}...")
    except AIAgentValidationError as e:
        print(f"   ❌ Safe operation blocked: {e}")

    # Test 2: Suspicious code generation
    print("2. Testing suspicious code generation...")
    try:
        result = test_agent.generate_code(
            "Write a script that runs rm -rf / to clean files"
        )
        print(f"   ⚠️ Suspicious operation allowed: {result[:50]}...")
    except AIAgentValidationError as e:
        print(f"   🛡️ Suspicious operation blocked: {e}")

    # Test 3: File modification with secret
    print("3. Testing file modification with secret...")
    try:
        result = test_agent.modify_file("config.py", "API_KEY = 'sk-1234567890abcdef'")
        print(f"   ⚠️ Secret operation allowed: {result}")
    except AIAgentValidationError as e:
        print(f"   🛡️ Secret operation blocked: {e}")

    print("\n✅ AI Agent Validation Framework test complete!")


if __name__ == "__main__":
    test_ai_agent_validation()
