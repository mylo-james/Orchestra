"""Tests for orchestra/system/base.py."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from orchestra.system.base import AgentContext, FunctionTool, SecureAgent


class TestAgentContext:
    """Test AgentContext data structure."""

    def test_agent_context_creation(self):
        """Test basic AgentContext creation."""
        context = AgentContext(
            correlation_id="test-123",
            agent_name="test-agent",
            session_id="session-456",
            metadata={"key": "value"},
        )

        assert context.correlation_id == "test-123"
        assert context.agent_name == "test-agent"
        assert context.session_id == "session-456"
        assert context.metadata == {"key": "value"}

    def test_agent_context_defaults(self):
        """Test AgentContext with default values."""
        context = AgentContext(correlation_id="test-123", agent_name="test-agent")

        assert context.correlation_id == "test-123"
        assert context.agent_name == "test-agent"
        assert context.session_id is None
        assert context.metadata == {}

    def test_agent_context_metadata_factory(self):
        """Test that metadata uses factory to avoid shared state."""
        context1 = AgentContext("id1", "agent1")
        context2 = AgentContext("id2", "agent2")

        context1.metadata["key1"] = "value1"
        context2.metadata["key2"] = "value2"

        assert "key1" not in context2.metadata
        assert "key2" not in context1.metadata


class TestSecureAgentInitialization:
    """Test SecureAgent initialization and setup."""

    @patch("orchestra.system.base.get_settings")
    @patch("orchestra.system.base.AgentMonitor")
    @patch("orchestra.system.base.AsyncOpenAI")
    @patch("orchestra.system.base.set_agent_context")
    def test_basic_initialization(
        self, mock_set_context, mock_openai, mock_monitor, mock_settings
    ):
        """Test basic SecureAgent initialization."""
        # Setup mocks
        mock_settings.return_value.openai.api_key = "test-key"

        agent = SecureAgent("test-agent")

        assert agent.name == "test-agent"
        assert agent.correlation_id.startswith("agent-test-agent-")
        assert agent.session_id is None

        # Verify integrations
        mock_monitor.assert_called_once_with(agent_name="test-agent")
        mock_openai.assert_called_once_with(api_key="test-key")
        mock_set_context.assert_called_once_with("test-agent")

    @patch("orchestra.system.base.get_settings")
    @patch("orchestra.system.base.AgentMonitor")
    @patch("orchestra.system.base.AsyncOpenAI")
    @patch("orchestra.system.base.set_agent_context")
    def test_initialization_with_correlation_id(
        self, mock_set_context, mock_openai, mock_monitor, mock_settings
    ):
        """Test SecureAgent initialization with explicit correlation ID."""
        mock_settings.return_value.openai.api_key = "test-key"

        agent = SecureAgent("test-agent", correlation_id="custom-correlation-123")

        assert agent.correlation_id == "custom-correlation-123"

    @patch("orchestra.system.base.get_settings")
    @patch("orchestra.system.base.AgentMonitor")
    @patch("orchestra.system.base.AsyncOpenAI")
    @patch("orchestra.system.base.set_agent_context")
    def test_initialization_with_session_id(
        self, mock_set_context, mock_openai, mock_monitor, mock_settings
    ):
        """Test SecureAgent initialization with session ID."""
        mock_settings.return_value.openai.api_key = "test-key"

        agent = SecureAgent("test-agent", session_id="session-789")

        assert agent.session_id == "session-789"

    @patch("orchestra.system.base.get_settings")
    @patch("orchestra.system.base.AgentMonitor")
    @patch("orchestra.system.base.AsyncOpenAI")
    @patch("orchestra.system.base.set_agent_context")
    @patch("orchestra.system.base.asyncio.current_task")
    def test_initialization_with_event_loop(
        self,
        mock_current_task,
        mock_set_context,
        mock_openai,
        mock_monitor,
        mock_settings,
    ):
        """Test SecureAgent initialization within event loop."""
        mock_settings.return_value.openai.api_key = "test-key"

        # Mock current task
        mock_task = Mock()
        mock_task.get_name.return_value = "test-task"
        mock_current_task.return_value = mock_task

        agent = SecureAgent("test-agent")

        assert "test-task" in agent.correlation_id

    @patch("orchestra.system.base.get_settings")
    @patch("orchestra.system.base.AgentMonitor")
    @patch("orchestra.system.base.AsyncOpenAI")
    @patch("orchestra.system.base.set_agent_context")
    @patch("orchestra.system.base.asyncio.current_task")
    def test_initialization_no_event_loop(
        self,
        mock_current_task,
        mock_set_context,
        mock_openai,
        mock_monitor,
        mock_settings,
    ):
        """Test SecureAgent initialization without event loop."""
        mock_settings.return_value.openai.api_key = "test-key"

        # Simulate no event loop
        mock_current_task.side_effect = RuntimeError("no running event loop")

        agent = SecureAgent("test-agent")

        assert "sync" in agent.correlation_id

    @patch("orchestra.system.base.get_settings")
    @patch("orchestra.system.base.AgentMonitor")
    @patch("orchestra.system.base.AsyncOpenAI")
    @patch("orchestra.system.base.set_agent_context")
    @patch("orchestra.system.base.logger")
    def test_initialization_logging(
        self, mock_logger, mock_set_context, mock_openai, mock_monitor, mock_settings
    ):
        """Test that initialization is logged."""
        mock_settings.return_value.openai.api_key = "test-key"

        SecureAgent("test-agent")

        mock_logger.info.assert_called_with("Initialized SecureAgent: test-agent")


class TestExecuteWithMonitoring:
    """Test execute_with_monitoring functionality."""

    @pytest.fixture
    def agent(self):
        """Create a SecureAgent for testing."""
        with (
            patch("orchestra.system.base.get_settings") as mock_settings,
            patch("orchestra.system.base.AgentMonitor"),
            patch("orchestra.system.base.AsyncOpenAI"),
            patch("orchestra.system.base.set_agent_context"),
        ):

            mock_settings.return_value.openai.api_key = "test-key"
            return SecureAgent("test-agent")

    @pytest.mark.asyncio
    async def test_execute_async_function(self, agent):
        """Test executing an async function with monitoring."""

        async def async_function(x, y):
            return x + y

        # Mock monitor.time to be an async context manager
        async_context_manager = AsyncMock()
        async_context_manager.__aenter__ = AsyncMock(return_value=None)
        async_context_manager.__aexit__ = AsyncMock(return_value=None)
        agent.monitor.time = Mock(return_value=async_context_manager)

        result = await agent.execute_with_monitoring("test-op", async_function, 2, 3)

        assert result == 5
        agent.monitor.time.assert_called_once_with("test-op")

    @pytest.mark.asyncio
    async def test_execute_sync_function(self, agent):
        """Test executing a sync function with monitoring."""

        def sync_function(x, y):
            return x * y

        # Mock monitor.time to be an async context manager
        async_context_manager = AsyncMock()
        async_context_manager.__aenter__ = AsyncMock(return_value=None)
        async_context_manager.__aexit__ = AsyncMock(return_value=None)
        agent.monitor.time = Mock(return_value=async_context_manager)

        result = await agent.execute_with_monitoring("test-op", sync_function, 4, 5)

        assert result == 20
        agent.monitor.time.assert_called_once_with("test-op")

    @pytest.mark.asyncio
    async def test_execute_with_kwargs(self, agent):
        """Test executing function with keyword arguments."""

        def test_function(a, b=10):
            return a + b

        # Mock monitor.time to be an async context manager
        async_context_manager = AsyncMock()
        async_context_manager.__aenter__ = AsyncMock(return_value=None)
        async_context_manager.__aexit__ = AsyncMock(return_value=None)
        agent.monitor.time = Mock(return_value=async_context_manager)

        result = await agent.execute_with_monitoring("test-op", test_function, 5, b=15)

        assert result == 20

    @pytest.mark.asyncio
    @patch("orchestra.system.base.logger")
    async def test_execute_with_logging(self, mock_logger, agent):
        """Test that execution operations are logged."""

        def simple_function():
            return "result"

        # Mock monitor.time to be an async context manager
        async_context_manager = AsyncMock()
        async_context_manager.__aenter__ = AsyncMock(return_value=None)
        async_context_manager.__aexit__ = AsyncMock(return_value=None)
        agent.monitor.time = Mock(return_value=async_context_manager)

        await agent.execute_with_monitoring("test-operation", simple_function)

        # Check logging calls
        mock_logger.info.assert_any_call("Starting operation: test-operation")
        mock_logger.info.assert_any_call("Completed operation: test-operation")


class TestValidation:
    """Test input and output validation methods."""

    @pytest.fixture
    def agent(self):
        """Create a SecureAgent for testing."""
        with (
            patch("orchestra.system.base.get_settings") as mock_settings,
            patch("orchestra.system.base.AgentMonitor"),
            patch("orchestra.system.base.AsyncOpenAI"),
            patch("orchestra.system.base.set_agent_context"),
        ):

            mock_settings.return_value.openai.api_key = "test-key"
            return SecureAgent("test-agent")

    @pytest.mark.asyncio
    async def test_validate_input_valid_data(self, agent):
        """Test input validation with valid data."""
        assert await agent.validate_input("valid string") is True
        assert await agent.validate_input({"key": "value"}) is True
        assert await agent.validate_input([1, 2, 3]) is True
        assert await agent.validate_input(42) is True

    @pytest.mark.asyncio
    async def test_validate_input_none(self, agent):
        """Test input validation with None data."""
        assert await agent.validate_input(None) is False

    @pytest.mark.asyncio
    async def test_validate_output_valid_data(self, agent):
        """Test output validation with valid data."""
        assert await agent.validate_output("valid string") is True
        assert await agent.validate_output({"key": "value"}) is True
        assert await agent.validate_output([1, 2, 3]) is True
        assert await agent.validate_output(42) is True

    @pytest.mark.asyncio
    async def test_validate_output_none(self, agent):
        """Test output validation with None data."""
        assert await agent.validate_output(None) is False


class TestContextManagement:
    """Test agent context management."""

    @pytest.fixture
    def agent(self):
        """Create a SecureAgent for testing."""
        with (
            patch("orchestra.system.base.get_settings") as mock_settings,
            patch("orchestra.system.base.AgentMonitor"),
            patch("orchestra.system.base.AsyncOpenAI"),
            patch("orchestra.system.base.set_agent_context"),
        ):

            mock_settings.return_value.openai.api_key = "test-key"
            return SecureAgent(
                "test-agent", correlation_id="test-123", session_id="session-456"
            )

    def test_get_context(self, agent):
        """Test getting agent context."""
        context = agent.get_context()

        assert isinstance(context, AgentContext)
        assert context.correlation_id == "test-123"
        assert context.agent_name == "test-agent"
        assert context.session_id == "session-456"
        assert context.metadata == {}

    def test_get_context_no_session(self):
        """Test getting context without session ID."""
        with (
            patch("orchestra.system.base.get_settings") as mock_settings,
            patch("orchestra.system.base.AgentMonitor"),
            patch("orchestra.system.base.AsyncOpenAI"),
            patch("orchestra.system.base.set_agent_context"),
        ):

            mock_settings.return_value.openai.api_key = "test-key"
            agent = SecureAgent("test-agent")

            context = agent.get_context()
            assert context.session_id is None


class TestCleanup:
    """Test agent cleanup functionality."""

    @pytest.fixture
    def agent(self):
        """Create a SecureAgent for testing."""
        with (
            patch("orchestra.system.base.get_settings") as mock_settings,
            patch("orchestra.system.base.AgentMonitor"),
            patch("orchestra.system.base.AsyncOpenAI"),
            patch("orchestra.system.base.set_agent_context"),
        ):

            mock_settings.return_value.openai.api_key = "test-key"
            return SecureAgent("test-agent")

    @pytest.mark.asyncio
    @patch("orchestra.system.base.logger")
    async def test_cleanup_logging(self, mock_logger, agent):
        """Test cleanup logs appropriately."""
        # Mock the client close method to be async
        agent.client.close = AsyncMock()

        await agent.cleanup()

        mock_logger.info.assert_any_call("Cleaning up SecureAgent: test-agent")

    @pytest.mark.asyncio
    async def test_cleanup_closes_client(self, agent):
        """Test cleanup closes OpenAI client if possible."""
        # Mock client with close method
        mock_close = AsyncMock()
        agent.client.close = mock_close

        await agent.cleanup()

        mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_no_close_method(self, agent):
        """Test cleanup handles client without close method."""
        # Remove close method if it exists
        if hasattr(agent.client, "close"):
            delattr(agent.client, "close")

        # Should not raise an exception
        await agent.cleanup()


class TestFunctionTool:
    """Test FunctionTool wrapper functionality."""

    def test_function_tool_initialization(self):
        """Test FunctionTool initialization."""

        def test_function():
            return "result"

        tool = FunctionTool("test-tool", "Test description", test_function)

        assert tool.name == "test-tool"
        assert tool.description == "Test description"
        assert tool.func == test_function

    @pytest.mark.asyncio
    async def test_execute_sync_function(self):
        """Test executing synchronous function."""

        def sync_func(x, y):
            return x + y

        tool = FunctionTool("add", "Addition tool", sync_func)
        result = await tool.execute(5, 3)

        assert result == 8

    @pytest.mark.asyncio
    async def test_execute_async_function(self):
        """Test executing asynchronous function."""

        async def async_func(x, y):
            return x * y

        tool = FunctionTool("multiply", "Multiplication tool", async_func)
        result = await tool.execute(4, 6)

        assert result == 24

    @pytest.mark.asyncio
    async def test_execute_with_kwargs(self):
        """Test executing function with keyword arguments."""

        def func_with_kwargs(a, b=10, c=5):
            return a + b + c

        tool = FunctionTool("sum", "Sum tool", func_with_kwargs)
        result = await tool.execute(1, b=2, c=3)

        assert result == 6

    @pytest.mark.asyncio
    async def test_execute_no_args(self):
        """Test executing function with no arguments."""

        def no_arg_func():
            return "no args"

        tool = FunctionTool("no-args", "No args tool", no_arg_func)
        result = await tool.execute()

        assert result == "no args"


class TestIntegrationScenarios:
    """Test end-to-end integration scenarios."""

    @pytest.fixture
    def agent(self):
        """Create a fully configured SecureAgent."""
        with (
            patch("orchestra.system.base.get_settings") as mock_settings,
            patch("orchestra.system.base.AgentMonitor"),
            patch("orchestra.system.base.AsyncOpenAI"),
            patch("orchestra.system.base.set_agent_context"),
        ):

            mock_settings.return_value.openai.api_key = "test-key"
            return SecureAgent("integration-agent", correlation_id="int-123")

    @pytest.mark.asyncio
    async def test_complete_agent_workflow(self, agent):
        """Test complete agent workflow from initialization to cleanup."""
        # Setup monitoring mock
        async_context_manager = AsyncMock()
        async_context_manager.__aenter__ = AsyncMock(return_value=None)
        async_context_manager.__aexit__ = AsyncMock(return_value=None)
        agent.monitor.time = Mock(return_value=async_context_manager)

        # Test function execution
        def test_operation(data):
            return f"processed: {data}"

        # Validate input
        input_valid = await agent.validate_input("test data")
        assert input_valid is True

        # Execute operation
        result = await agent.execute_with_monitoring(
            "process", test_operation, "test data"
        )
        assert result == "processed: test data"

        # Validate output
        output_valid = await agent.validate_output(result)
        assert output_valid is True

        # Get context
        context = agent.get_context()
        assert context.agent_name == "integration-agent"
        assert context.correlation_id == "int-123"

        # Cleanup
        # Mock the close method to be async
        agent.client.close = AsyncMock()
        await agent.cleanup()

    @pytest.mark.asyncio
    async def test_tool_integration_with_agent(self, agent):
        """Test FunctionTool integration with SecureAgent."""

        # Create a tool
        def calculation_tool(x, y, operation="add"):
            if operation == "add":
                return x + y
            elif operation == "multiply":
                return x * y
            return 0

        tool = FunctionTool("calc", "Calculation tool", calculation_tool)

        # Setup monitoring mock
        async_context_manager = AsyncMock()
        async_context_manager.__aenter__ = AsyncMock(return_value=None)
        async_context_manager.__aexit__ = AsyncMock(return_value=None)
        agent.monitor.time = Mock(return_value=async_context_manager)

        # Execute tool through agent monitoring (fix keyword argument conflict)
        async def execute_tool():
            return await tool.execute(10, 5, operation="multiply")

        result = await agent.execute_with_monitoring("tool-execution", execute_tool)

        assert result == 50
        agent.monitor.time.assert_called_once_with("tool-execution")
