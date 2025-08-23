"""Tests for system monitoring module."""

import pytest

from src.system.monitoring import AgentMetric, AgentMonitor


class TestAgentMonitor:
    """Test AgentMonitor functionality."""

    @pytest.fixture
    def agent_monitor(self):
        """Create an AgentMonitor instance for testing."""
        return AgentMonitor("test-agent")

    def test_initialization(self, agent_monitor):
        """Test AgentMonitor initialization."""
        assert agent_monitor.agent_name == "test-agent"

    def test_emit_metric(self, agent_monitor):
        """Test emitting a metric."""
        metric = AgentMetric(
            name="test_metric",
            duration_ms=150.5,
            success=True,
            details={"test": "data"},
        )

        agent_monitor.emit(metric)
        # Note: emit just logs the metric, no return value to test

    @pytest.mark.asyncio
    async def test_time_context_manager_success(self, agent_monitor):
        """Test time context manager with successful execution."""
        async with agent_monitor.time("test_operation", {"test": "data"}):
            # Simulate some work
            pass
        # Note: time context manager logs metrics, no return value to test

    @pytest.mark.asyncio
    async def test_time_context_manager_exception(self, agent_monitor):
        """Test time context manager with exception."""
        with pytest.raises(ValueError):
            async with agent_monitor.time("test_operation", {"test": "data"}):
                raise ValueError("Test exception")
        # Note: time context manager logs metrics, no return value to test
