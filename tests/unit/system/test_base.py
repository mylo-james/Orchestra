"""Tests for system base module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.system.base import AgentContext, ModelConfig, SecureAgent


class TestAgentContext:
    """Test AgentContext functionality."""

    def test_initialization(self):
        """Test AgentContext initialization."""
        context = AgentContext(
            correlation_id="test-123",
            agent_name="test-agent",
            session_data={"key": "value"}
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
        config = ModelConfig(
            model="gpt-4",
            temperature=0.7,
            max_tokens=1000
        )
        
        assert config.model == "gpt-4"
        assert config.temperature == 0.7
        assert config.max_tokens == 1000

    def test_initialization_required_fields(self):
        """Test ModelConfig requires all fields."""
        # ModelConfig requires all fields to be provided
        config = ModelConfig(
            model="gpt-4",
            temperature=0.7,
            max_tokens=1000
        )
        
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
        # Test start
        await secure_agent.start()
        assert secure_agent.session is not None
        
        # Test stop
        await secure_agent.stop()
        # Note: stop doesn't clear session, just closes it
