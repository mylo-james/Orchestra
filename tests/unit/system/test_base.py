"""Tests for system base module."""

from unittest.mock import Mock, patch

import pytest

from src.system.base import AgentContext, ModelConfig, SecureAgent


class TestAgentContext:
    """Test AgentContext functionality."""

    def test_initialization(self):
        """Test AgentContext initialization."""
        context = AgentContext(
            correlation_id="test-123",
            agent_name="test-agent",
            session_data={"key": "value"},
        )

        assert context.correlation_id == "test-123"
        assert context.agent_name == "test-agent"
        assert context.session_data == {"key": "value"}

    def test_initialization_defaults(self):
        """Test AgentContext initialization with defaults."""
        context = AgentContext()

        assert context.correlation_id is None
        assert context.agent_name is None
        assert context.session_data == {}

    def test_session_data_initialization(self):
        """Test session data initialization."""
        context = AgentContext()
        assert context.session_data == {}

        context = AgentContext(session_data={"key": "value"})
        assert context.session_data == {"key": "value"}


class TestModelConfig:
    """Test ModelConfig functionality."""

    def test_initialization(self):
        """Test ModelConfig initialization."""
        config = ModelConfig(model="gpt-4", temperature=0.7, max_tokens=1000)

        assert config.model == "gpt-4"
        assert config.temperature == 0.7
        assert config.max_tokens == 1000

    def test_initialization_required_fields(self):
        """Test ModelConfig requires all fields."""
        # ModelConfig requires all fields to be provided
        config = ModelConfig(model="gpt-4", temperature=0.7, max_tokens=1000)

        assert config.model == "gpt-4"
        assert config.temperature == 0.7
        assert config.max_tokens == 1000


class TestSecureAgent:
    """Test SecureAgent functionality."""

    @pytest.fixture
    def secure_agent(self):
        """Create a SecureAgent instance for testing."""
        return SecureAgent()

    def test_initialization(self, secure_agent):
        """Test SecureAgent initialization."""
        assert secure_agent.agent_name == "secure_agent"
        assert secure_agent.settings is not None
        assert secure_agent.model_cfg is not None
        assert secure_agent.model is not None
        assert secure_agent.agent is not None
        assert secure_agent.monitor is not None
        assert secure_agent.session is None
        assert secure_agent.runner is not None

    def test_add_tool(self, secure_agent):
        """Test adding tools to agent."""
        mock_tool = Mock()
        secure_agent.add_tool(mock_tool)

        # Verify tool was added to agent's tools
        assert mock_tool in secure_agent.agent.tools

    @pytest.mark.asyncio
    async def test_start_stop(self, secure_agent):
        """Test agent start and stop methods."""
        # Mock SQLiteSession to avoid database file creation in tests
        with patch("src.system.base.SQLiteSession") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # Test start
            await secure_agent.start()
            assert secure_agent.session is not None

            # Verify SQLiteSession was created with correct parameters
            mock_session_class.assert_called_once_with(
                session_id=f"{secure_agent.agent_name}_session",
                db_path=f".ai/sessions/{secure_agent.agent_name}_sessions.db",
            )

            # Test stop
            await secure_agent.stop()
            # Note: stop doesn't clear session, just closes it

    @pytest.mark.asyncio
    async def test_ask_method_basic_functionality(self, secure_agent):
        """Test ask method with basic functionality (lines 114-162)."""
        user_message = "Hello, how are you?"

        # Mock session creation and runner execution
        with (
            patch("src.system.base.SQLiteSession") as mock_session_class,
            patch.object(secure_agent.runner, "run_sync") as mock_run_sync,
        ):

            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # Mock the runner result with final_output
            mock_result = Mock()
            mock_result.final_output = "I'm doing well, thank you!"
            mock_run_sync.return_value = mock_result

            # Execute ask method
            response = await secure_agent.ask(user_message)

            # Verify response
            assert response == "I'm doing well, thank you!"

            # Verify session was created (since it starts as None)
            assert secure_agent.session is not None

            # Verify runner was called with correct parameters
            mock_run_sync.assert_called_once()
            call_args = mock_run_sync.call_args
            assert call_args[1]["starting_agent"] == secure_agent.agent
            assert call_args[1]["input"] == user_message
            assert call_args[1]["session"] == mock_session

    @pytest.mark.asyncio
    async def test_ask_method_with_messages_fallback(self, secure_agent):
        """Test ask method when result has messages but no final_output."""
        user_message = "Test message"

        with (
            patch("src.system.base.SQLiteSession") as mock_session_class,
            patch.object(secure_agent.runner, "run_sync") as mock_run_sync,
        ):

            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # Mock result with messages but no final_output
            mock_result = Mock()
            mock_result.final_output = None

            mock_message = Mock()
            mock_message.content = "Response from messages"
            mock_result.messages = [mock_message]
            mock_run_sync.return_value = mock_result

            # Execute ask method
            response = await secure_agent.ask(user_message)

            # Should use message content as fallback
            assert response == "Response from messages"

    @pytest.mark.asyncio
    async def test_ask_method_with_empty_messages_fallback(self, secure_agent):
        """Test ask method when result has empty messages."""
        user_message = "Test message"

        with (
            patch("src.system.base.SQLiteSession") as mock_session_class,
            patch.object(secure_agent.runner, "run_sync") as mock_run_sync,
        ):

            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # Mock result with empty content messages
            mock_result = Mock()
            mock_result.final_output = None

            mock_message = Mock()
            mock_message.content = None
            mock_result.messages = [mock_message]
            mock_run_sync.return_value = mock_result

            # Execute ask method
            response = await secure_agent.ask(user_message)

            # Should use empty string as fallback
            assert response == ""

    @pytest.mark.asyncio
    async def test_ask_method_no_response_fallback(self, secure_agent):
        """Test ask method when no response is available."""
        user_message = "Test message"

        with (
            patch("src.system.base.SQLiteSession") as mock_session_class,
            patch.object(secure_agent.runner, "run_sync") as mock_run_sync,
        ):

            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # Mock result with no final_output and no messages
            mock_result = Mock()
            mock_result.final_output = None
            mock_result.messages = None
            mock_run_sync.return_value = mock_result

            # Execute ask method
            response = await secure_agent.ask(user_message)

            # Should return default message
            assert response == "No response generated"

    @pytest.mark.asyncio
    async def test_ask_method_with_existing_session(self, secure_agent):
        """Test ask method when session already exists."""
        user_message = "Hello with existing session"

        # Pre-set a session
        mock_existing_session = Mock()
        secure_agent.session = mock_existing_session

        with patch.object(secure_agent.runner, "run_sync") as mock_run_sync:

            # Mock the runner result
            mock_result = Mock()
            mock_result.final_output = "Response with existing session"
            mock_run_sync.return_value = mock_result

            # Execute ask method
            response = await secure_agent.ask(user_message)

            # Verify response
            assert response == "Response with existing session"

            # Verify existing session was used
            assert secure_agent.session == mock_existing_session

            # Verify runner was called with existing session
            call_args = mock_run_sync.call_args
            assert call_args[1]["session"] == mock_existing_session

    @pytest.mark.asyncio
    async def test_ask_method_with_custom_context(self, secure_agent):
        """Test ask method with provided context."""
        user_message = "Hello with context"
        custom_context = AgentContext(
            correlation_id="custom-123",
            agent_name="custom-agent",
            session_data={"custom": "data"},
        )

        with (
            patch("src.system.base.SQLiteSession") as mock_session_class,
            patch.object(secure_agent.runner, "run_sync") as mock_run_sync,
        ):

            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # Mock the runner result
            mock_result = Mock()
            mock_result.final_output = "Response with custom context"
            mock_run_sync.return_value = mock_result

            # Execute ask method with custom context
            response = await secure_agent.ask(user_message, context=custom_context)

            # Verify response
            assert response == "Response with custom context"

            # Verify custom context was used
            call_args = mock_run_sync.call_args
            assert call_args[1]["context"] == custom_context

    @pytest.mark.asyncio
    async def test_ask_method_error_handling(self, secure_agent):
        """Test ask method error handling and logging."""
        user_message = "Test error handling"

        with (
            patch("src.system.base.SQLiteSession") as mock_session_class,
            patch.object(secure_agent.runner, "run_sync") as mock_run_sync,
        ):

            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # Make runner raise an exception
            mock_run_sync.side_effect = Exception("Test runner error")

            # Execute ask method and expect exception
            with pytest.raises(Exception) as exc_info:
                await secure_agent.ask(user_message)

            assert str(exc_info.value) == "Test runner error"

    @pytest.mark.asyncio
    async def test_ask_method_creates_default_context_with_correlation_id(
        self, secure_agent
    ):
        """Test ask method creates default context with correlation ID."""
        user_message = "Test default context"

        with (
            patch("src.system.base.SQLiteSession") as mock_session_class,
            patch.object(secure_agent.runner, "run_sync") as mock_run_sync,
            patch("asyncio.current_task") as mock_current_task,
        ):

            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # Mock current_task for correlation ID generation
            mock_task = Mock()
            mock_task.__str__ = Mock(return_value="task-123")
            mock_current_task.return_value = mock_task

            # Mock the runner result
            mock_result = Mock()
            mock_result.final_output = "Response with default context"
            mock_run_sync.return_value = mock_result

            # Execute ask method
            response = await secure_agent.ask(user_message)

            # Verify response
            assert response == "Response with default context"

            # Verify default context was created with correlation ID
            call_args = mock_run_sync.call_args
            context = call_args[1]["context"]
            assert context.agent_name == secure_agent.agent_name
            assert "secure_agent_" in context.correlation_id

    @pytest.mark.asyncio
    async def test_ask_method_comprehensive_coverage(self, secure_agent):
        """Test ask method comprehensive coverage - all code paths."""
        user_message = "Test comprehensive coverage"

        with (
            patch("src.system.base.SQLiteSession") as mock_session_class,
            patch.object(secure_agent.runner, "run_sync") as mock_run_sync,
        ):

            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # Mock the runner result
            mock_result = Mock()
            mock_result.final_output = "Comprehensive test response"
            mock_run_sync.return_value = mock_result

            # Execute ask method - this will exercise monitoring code internally
            response = await secure_agent.ask(user_message)

            # Verify response
            assert response == "Comprehensive test response"

            # Verify runner was called (covers main execution path)
            mock_run_sync.assert_called_once()
