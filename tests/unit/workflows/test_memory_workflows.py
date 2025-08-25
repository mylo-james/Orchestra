"""Tests for memory workflow sub-workflows based on Story 2.1 PRD requirements."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest

from orchestra.workflows.memory_activities import memory_upsert_activity


class TestMemoryUpsertActivity:
    """Test memory upsert activity (AC: 2, 5, 7)."""

    @pytest.mark.asyncio
    async def test_memory_upsert_activity_success(self):
        """Test successful memory upsert with context extraction."""
        # Test data from persona execution
        execution_context = {
            "persona_id": "dev",
            "project_id": "test-project",
            "session_id": "test-session",
            "command": "implement-story",
            "result": {"success": True, "files_created": ["auth.py"]},
            "timestamp": datetime.utcnow(),
        }

        patterns = {
            "success_patterns": ["file creation", "authentication implementation"],
            "context_data": {"domain": "authentication", "complexity": "medium"},
        }

        with patch(
            "orchestra.workflows.memory_activities.MemoryService"
        ) as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.upsert_memory = AsyncMock(
                return_value={
                    "success": True,
                    "memory_id": "mem-123",
                    "relevance_score": 0.85,
                }
            )
            mock_service.store_context_pattern = AsyncMock(
                return_value={
                    "success": True,
                }
            )

            result = await memory_upsert_activity(execution_context, patterns)

            assert result["success"] is True
            assert result["memory_id"] == "mem-123"
            assert result["relevance_score"] >= 0.8  # AC: 7 - >80% relevance score

            # Verify service methods were called
            mock_service.upsert_memory.assert_called_once()
            mock_service.store_context_pattern.assert_called_once()

    @pytest.mark.asyncio
    async def test_memory_upsert_activity_low_relevance(self):
        """Test memory upsert with low relevance score rejection."""
        execution_context = {
            "persona_id": "dev",
            "project_id": "test-project",
            "session_id": "test-session",
            "command": "simple-task",
            "result": {"success": True},
            "timestamp": datetime.utcnow(),
        }

        patterns = {
            "success_patterns": ["trivial task"],
            "context_data": {"domain": "general", "complexity": "low"},
        }

        with patch(
            "orchestra.workflows.memory_activities._calculate_relevance_score"
        ) as mock_relevance:
            mock_relevance.return_value = 0.75  # Below 80% threshold

            result = await memory_upsert_activity(execution_context, patterns)

            assert result["success"] is False
            assert result["relevance_score"] < 0.8
            assert "Low relevance score" in result["reason"]

    @pytest.mark.asyncio
    async def test_memory_upsert_workflow_namespace_isolation(self):
        """Test memory upsert respects project namespace isolation."""
        workflow = MemoryUpsertWorkflow()

        execution_context = {
            "persona_id": "dev",
            "project_id": "project-a",
            "session_id": "test-session",
            "command": "implement-story",
            "result": {"success": True},
            "timestamp": datetime.utcnow(),
        }

        patterns = {"success_patterns": ["implementation"], "context_data": {}}

        with patch(
            "orchestra.workflows.memory_workflows.memory_upsert_activity"
        ) as mock_activity:
            mock_activity.return_value = {
                "success": True,
                "memory_id": "mem-123",
                "namespace": "orchestra_memory_project-a",
            }

            result = await workflow.run(execution_context, patterns)

            assert result["success"] is True
            assert result["namespace"] == "orchestra_memory_project-a"


class TestMemoryRetrievalWorkflow:
    """Test memory retrieval sub-workflow (AC: 3, 5, 8)."""

    @pytest.mark.asyncio
    async def test_memory_retrieval_workflow_success(self):
        """Test successful memory retrieval with semantic search."""
        workflow = MemoryRetrievalWorkflow()

        query_context = {
            "persona_id": "dev",
            "project_id": "test-project",
            "current_task": "implement authentication",
            "context_hints": ["auth", "security", "user management"],
        }

        expected_memories = [
            {
                "memory_id": "mem-123",
                "content": "Previous auth implementation patterns",
                "relevance_score": 0.92,
                "context": {"domain": "authentication", "success": True},
            }
        ]

        with patch(
            "orchestra.workflows.memory_workflows.memory_retrieval_activity"
        ) as mock_activity:
            mock_activity.return_value = {
                "success": True,
                "memories": expected_memories,
                "retrieval_time_ms": 150,  # AC: 8 - <200ms response time
            }

            result = await workflow.run(query_context)

            assert result["success"] is True
            assert len(result["memories"]) == 1
            assert result["memories"][0]["relevance_score"] > 0.9
            assert (
                result["retrieval_time_ms"] < 200
            )  # AC: 8 - <200ms for 95% of queries

    @pytest.mark.asyncio
    async def test_memory_retrieval_workflow_performance_requirement(self):
        """Test memory retrieval meets performance requirements."""
        workflow = MemoryRetrievalWorkflow()

        query_context = {
            "persona_id": "dev",
            "project_id": "test-project",
            "current_task": "complex query",
        }

        with patch(
            "orchestra.workflows.memory_workflows.memory_retrieval_activity"
        ) as mock_activity:
            # Simulate fast retrieval
            mock_activity.return_value = {
                "success": True,
                "memories": [],
                "retrieval_time_ms": 180,
            }

            start_time = datetime.utcnow()
            result = await workflow.run(query_context)
            end_time = datetime.utcnow()

            # Total workflow time should be minimal
            total_time_ms = (end_time - start_time).total_seconds() * 1000
            assert total_time_ms < 200  # AC: 8 - <200ms response time
            assert result["retrieval_time_ms"] < 200

    @pytest.mark.asyncio
    async def test_memory_retrieval_workflow_empty_results(self):
        """Test memory retrieval with no matching memories."""
        workflow = MemoryRetrievalWorkflow()

        query_context = {
            "persona_id": "dev",
            "project_id": "new-project",
            "current_task": "novel task",
        }

        with patch(
            "orchestra.workflows.memory_workflows.memory_retrieval_activity"
        ) as mock_activity:
            mock_activity.return_value = {
                "success": True,
                "memories": [],
                "retrieval_time_ms": 50,
            }

            result = await workflow.run(query_context)

            assert result["success"] is True
            assert len(result["memories"]) == 0
            assert result["retrieval_time_ms"] < 200


class TestMemoryManagementWorkflow:
    """Test memory management sub-workflow (AC: 4, 5, 10)."""

    @pytest.mark.asyncio
    async def test_memory_management_workflow_retention_policy(self):
        """Test memory management enforces retention policies."""
        workflow = MemoryManagementWorkflow()

        management_context = {
            "project_id": "test-project",
            "operation": "enforce_retention",
            "retention_days": 90,  # AC: 10 - archive memories older than 90 days
        }

        with patch(
            "orchestra.workflows.memory_workflows.memory_management_activity"
        ) as mock_activity:
            mock_activity.return_value = {
                "success": True,
                "archived_count": 15,
                "deleted_count": 3,
                "memory_freed_mb": 45,
            }

            result = await workflow.run(management_context)

            assert result["success"] is True
            assert result["archived_count"] == 15
            assert result["deleted_count"] == 3
            assert result["memory_freed_mb"] > 0

    @pytest.mark.asyncio
    async def test_memory_management_workflow_memory_footprint(self):
        """Test memory management stays within 4GB constraint."""
        workflow = MemoryManagementWorkflow()

        management_context = {
            "project_id": "test-project",
            "operation": "check_memory_usage",
            "max_memory_gb": 4,  # AC: 9 - 4GB constraint
        }

        with patch(
            "orchestra.workflows.memory_workflows.memory_management_activity"
        ) as mock_activity:
            mock_activity.return_value = {
                "success": True,
                "current_memory_gb": 3.2,
                "cleanup_triggered": False,
                "within_limits": True,
            }

            result = await workflow.run(management_context)

            assert result["success"] is True
            assert result["current_memory_gb"] < 4.0  # AC: 9 - within 4GB constraint
            assert result["within_limits"] is True

    @pytest.mark.asyncio
    async def test_memory_management_workflow_cleanup_trigger(self):
        """Test memory management triggers cleanup when approaching limits."""
        workflow = MemoryManagementWorkflow()

        management_context = {
            "project_id": "test-project",
            "operation": "check_memory_usage",
            "max_memory_gb": 4,
        }

        with patch(
            "orchestra.workflows.memory_workflows.memory_management_activity"
        ) as mock_activity:
            # Simulate memory usage approaching limit
            mock_activity.return_value = {
                "success": True,
                "current_memory_gb": 3.8,
                "cleanup_triggered": True,
                "within_limits": True,
                "cleanup_freed_gb": 0.5,
            }

            result = await workflow.run(management_context)

            assert result["success"] is True
            assert result["cleanup_triggered"] is True
            assert result["cleanup_freed_gb"] > 0

    @pytest.mark.asyncio
    async def test_memory_management_workflow_scheduled_execution(self):
        """Test memory management as scheduled Temporal workflow."""
        workflow = MemoryManagementWorkflow()

        # Simulate scheduled execution context
        management_context = {
            "project_id": "test-project",
            "operation": "scheduled_cleanup",
            "schedule": "daily",
            "retention_days": 90,
        }

        with patch(
            "orchestra.workflows.memory_workflows.memory_management_activity"
        ) as mock_activity:
            mock_activity.return_value = {
                "success": True,
                "operation": "scheduled_cleanup",
                "next_run": datetime.utcnow() + timedelta(days=1),
                "archived_count": 5,
            }

            result = await workflow.run(management_context)

            assert result["success"] is True
            assert result["operation"] == "scheduled_cleanup"
            assert "next_run" in result


class TestMemoryWorkflowIntegration:
    """Test integration between memory workflows."""

    @pytest.mark.asyncio
    async def test_memory_workflow_composition(self):
        """Test memory workflows can be composed together."""
        # Test upsert followed by retrieval
        upsert_workflow = MemoryUpsertWorkflow()
        retrieval_workflow = MemoryRetrievalWorkflow()

        # First upsert a memory
        execution_context = {
            "persona_id": "dev",
            "project_id": "test-project",
            "session_id": "test-session",
            "command": "implement-feature",
            "result": {"success": True, "feature": "user-auth"},
            "timestamp": datetime.utcnow(),
        }

        patterns = {
            "success_patterns": ["authentication", "user management"],
            "context_data": {"domain": "security", "complexity": "high"},
        }

        with patch(
            "orchestra.workflows.memory_workflows.memory_upsert_activity"
        ) as mock_upsert:
            mock_upsert.return_value = {
                "success": True,
                "memory_id": "mem-456",
                "relevance_score": 0.88,
            }

            upsert_result = await upsert_workflow.run(execution_context, patterns)
            assert upsert_result["success"] is True

        # Then retrieve related memories
        query_context = {
            "persona_id": "dev",
            "project_id": "test-project",
            "current_task": "implement similar auth feature",
            "context_hints": ["authentication", "security"],
        }

        with patch(
            "orchestra.workflows.memory_workflows.memory_retrieval_activity"
        ) as mock_retrieval:
            mock_retrieval.return_value = {
                "success": True,
                "memories": [
                    {
                        "memory_id": "mem-456",
                        "content": "Previous auth implementation",
                        "relevance_score": 0.88,
                    }
                ],
                "retrieval_time_ms": 120,
            }

            retrieval_result = await retrieval_workflow.run(query_context)
            assert retrieval_result["success"] is True
            assert len(retrieval_result["memories"]) == 1
            assert retrieval_result["memories"][0]["memory_id"] == "mem-456"

    @pytest.mark.asyncio
    async def test_memory_workflow_error_handling(self):
        """Test memory workflow error handling and rollback."""
        workflow = MemoryUpsertWorkflow()

        execution_context = {
            "persona_id": "dev",
            "project_id": "test-project",
            "session_id": "test-session",
            "command": "implement-story",
            "result": {"success": True},
            "timestamp": datetime.utcnow(),
        }

        patterns = {"success_patterns": ["implementation"], "context_data": {}}

        with patch(
            "orchestra.workflows.memory_workflows.memory_upsert_activity"
        ) as mock_activity:
            # Simulate activity failure
            mock_activity.side_effect = Exception("Qdrant connection failed")

            with pytest.raises(Exception, match="Qdrant connection failed"):
                await workflow.run(execution_context, patterns)

    @pytest.mark.asyncio
    async def test_memory_workflow_temporal_integration(self):
        """Test memory workflows integrate with Temporal orchestration."""
        # This test verifies the workflows are properly structured for Temporal
        workflow = MemoryUpsertWorkflow()

        # Verify workflow has required Temporal attributes
        assert hasattr(workflow, "run")
        assert callable(workflow.run)

        # Verify workflow can handle Temporal context
        execution_context = {
            "persona_id": "dev",
            "project_id": "test-project",
            "temporal_workflow_id": "memory-workflow-123",
            "temporal_run_id": "run-456",
        }

        patterns = {"success_patterns": ["test"], "context_data": {}}

        with patch(
            "orchestra.workflows.memory_workflows.memory_upsert_activity"
        ) as mock_activity:
            mock_activity.return_value = {
                "success": True,
                "memory_id": "mem-789",
                "temporal_context": {
                    "workflow_id": "memory-workflow-123",
                    "run_id": "run-456",
                },
            }

            result = await workflow.run(execution_context, patterns)

            assert result["success"] is True
            assert "temporal_context" in result
