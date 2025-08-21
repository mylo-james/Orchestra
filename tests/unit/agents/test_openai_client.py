from unittest.mock import AsyncMock, Mock, patch
import pytest

from src.agents.base.secure_agent import SecureAgent, ModelConfig, AgentContext


@pytest.mark.asyncio
async def test_secure_agent_initialization():
    """Test SecureAgent initialization with OpenAI Agents SDK."""
    with patch("src.agents.base.secure_agent.OpenAIChatCompletionsModel") as mock_model_cls:
        with patch("src.agents.base.secure_agent.Agent") as mock_agent_cls:
            mock_model = Mock()
            mock_model_cls.return_value = mock_model
            
            mock_agent = Mock()
            mock_agent.tools = []
            
            # Handle the generic Agent[AgentContext] call
            mock_agent_generic = Mock()
            mock_agent_generic.return_value = mock_agent
            mock_agent_cls.__getitem__ = Mock(return_value=mock_agent_generic)

            agent = SecureAgent(instructions="Test instructions")

            # Verify model was created with correct parameters
            mock_model_cls.assert_called_once()
            call_args = mock_model_cls.call_args
            assert call_args[1]["model_name"] == "gpt-4o"  # Default model
            assert call_args[1]["api_key"] == "sk-test-key"  # Default API key

            # Verify Agent[AgentContext] was created
            mock_agent_cls.__getitem__.assert_called_once()
            mock_agent_generic.assert_called_once()
            agent_args = mock_agent_generic.call_args[1]
            assert agent_args["name"] == "secure_agent"
            assert agent_args["model"] == mock_model
            assert "Test instructions" in agent_args["instructions"]


@pytest.mark.asyncio
async def test_secure_agent_ask():
    """Test SecureAgent ask method with OpenAI Agents SDK Runner."""
    with patch("src.agents.base.secure_agent.OpenAIChatCompletionsModel"):
        with patch("src.agents.base.secure_agent.Agent"):
            with patch("src.agents.base.secure_agent.Runner") as mock_runner_cls:
                with patch("src.agents.base.secure_agent.SQLiteSession") as mock_session_cls:
                    mock_runner = Mock()
                    mock_runner_cls.return_value = mock_runner

                    mock_result = Mock()
                    mock_result.final_output = "Test response"
                    mock_runner.run_sync.return_value = mock_result

                    mock_session = Mock()
                    mock_session_cls.return_value = mock_session

                    agent = SecureAgent()
                    result = await agent.ask("Test message")

                    assert result == "Test response"
                    mock_runner.run_sync.assert_called_once()


@pytest.mark.asyncio
async def test_secure_agent_with_custom_model_config():
    """Test SecureAgent with custom model configuration."""
    custom_config = ModelConfig(
        model="gpt-3.5-turbo",
        temperature=0.5,
        max_tokens=2048
    )

    with patch("src.agents.base.secure_agent.OpenAIChatCompletionsModel") as mock_model_cls:
        with patch("src.agents.base.secure_agent.Agent"):
            agent = SecureAgent(model_cfg=custom_config)

            # Verify custom config was used
            call_args = mock_model_cls.call_args[1]
            assert call_args["model_name"] == "gpt-3.5-turbo"
            assert call_args["temperature"] == 0.5
            assert call_args["max_tokens"] == 2048


@pytest.mark.asyncio
async def test_agent_context_creation():
    """Test AgentContext creation and initialization."""
    context = AgentContext(
        agent_name="test_agent",
        correlation_id="test_123"
    )

    assert context.agent_name == "test_agent"
    assert context.correlation_id == "test_123"
    assert context.session_data == {}

    # Test default initialization
    context2 = AgentContext()
    assert context2.session_data is not None
