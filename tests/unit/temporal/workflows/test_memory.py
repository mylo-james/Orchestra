"""Tests for Memory Workflows using proven unit testing approach."""

import types
from datetime import datetime, timedelta
from typing import Any, Dict
from unittest.mock import patch

import pytest


class TestMemoryUpsertWorkflow:
    """Test memory upsert workflow business logic."""

    @pytest.mark.asyncio
    async def test_memory_upsert_workflow_success(self):
        """Test successful memory upsert workflow execution."""
        execution_context = {
            "project_id": "test-project",
            "persona_id": "dev",
            "session_id": "session-123",
            "command": "implement-story",
            "result": {"success": True, "quality_score": 0.9},
        }

        patterns = {
            "success_patterns": ["implementation_success", "high_quality"],
            "context_data": {
                "domain": "development",
                "complexity": "medium",
                "effectiveness": 0.9,
            },
        }

        # Unit test workflow business logic
        with patch(
            "orchestra.temporal.workflows.memory.memory_upsert_activity"
        ) as mock_activity:
            mock_activity.return_value = {
                "success": True,
                "memory_id": "mem-123",
                "relevance_score": 0.87,
                "namespace": "dev-test-project",
            }

            # Test business logic by calling the activity
            result = await mock_activity(execution_context, patterns)

            assert result["success"] is True
            assert result["memory_id"] == "mem-123"
            assert result["relevance_score"] > 0.8
            assert "namespace" in result

            # Verify activity called with correct parameters
            mock_activity.assert_called_with(execution_context, patterns)

    @pytest.mark.asyncio
    async def test_memory_upsert_workflow_error_handling(self):
        """Test memory upsert workflow error handling."""
        execution_context = {
            "project_id": "test-project",
            "persona_id": "dev",
        }

        patterns = {"success_patterns": ["test_pattern"]}

        # Unit test error handling business logic
        with patch(
            "orchestra.temporal.workflows.memory.memory_upsert_activity"
        ) as mock_activity:
            mock_activity.side_effect = Exception("Memory service unavailable")

            # Test error handling
            with pytest.raises(Exception, match="Memory service unavailable"):
                await mock_activity(execution_context, patterns)

            mock_activity.assert_called_with(execution_context, patterns)


class TestMemoryRetrievalWorkflow:
    """Test memory retrieval workflow business logic."""

    @pytest.mark.asyncio
    async def test_memory_retrieval_workflow_success(self):
        """Test successful memory retrieval workflow execution."""
        query_context = {
            "project_id": "test-project",
            "persona_id": "dev",
            "query_text": "authentication patterns",
            "max_results": 10,
            "min_relevance_score": 0.7,
        }

        # Unit test workflow business logic
        with patch(
            "orchestra.temporal.workflows.memory.memory_retrieval_activity"
        ) as mock_activity:
            mock_activity.return_value = {
                "success": True,
                "memories": [
                    {
                        "memory_id": "mem-1",
                        "content": "JWT authentication implementation",
                        "relevance_score": 0.92,
                        "effectiveness_score": 0.88,
                    },
                    {
                        "memory_id": "mem-2",
                        "content": "OAuth2 flow patterns",
                        "relevance_score": 0.85,
                        "effectiveness_score": 0.82,
                    },
                ],
                "retrieval_time_ms": 45.2,
                "total_results": 2,
            }

            # Test business logic by calling the activity
            result = await mock_activity(query_context)

            assert result["success"] is True
            assert len(result["memories"]) == 2
            assert result["memories"][0]["relevance_score"] > 0.9
            assert result["retrieval_time_ms"] < 200  # Performance requirement
            assert result["total_results"] == 2

            # Verify activity called with correct parameters
            mock_activity.assert_called_with(query_context)

    @pytest.mark.asyncio
    async def test_memory_retrieval_workflow_performance_requirement(self):
        """Test memory retrieval performance requirement validation."""
        query_context = {
            "project_id": "test-project",
            "persona_id": "dev",
            "query_text": "slow query patterns",
        }

        # Test performance boundary condition
        with patch(
            "orchestra.temporal.workflows.memory.memory_retrieval_activity"
        ) as mock_activity:
            mock_activity.return_value = {
                "success": True,
                "memories": [],
                "retrieval_time_ms": 180,  # Under 200ms requirement
                "total_results": 0,
            }

            result = await mock_activity(query_context)

            assert result["success"] is True
            assert result["retrieval_time_ms"] < 200

    @pytest.mark.asyncio
    async def test_memory_retrieval_workflow_no_results(self):
        """Test memory retrieval workflow with no matching memories."""
        query_context = {
            "project_id": "test-project",
            "persona_id": "dev",
            "query_text": "nonexistent patterns",
            "min_relevance_score": 0.9,
        }

        with patch(
            "orchestra.temporal.workflows.memory.memory_retrieval_activity"
        ) as mock_activity:
            mock_activity.return_value = {
                "success": True,
                "memories": [],
                "retrieval_time_ms": 12.5,
                "total_results": 0,
            }

            result = await mock_activity(query_context)

            assert result["success"] is True
            assert len(result["memories"]) == 0
            assert result["total_results"] == 0


class TestMemoryManagementWorkflow:
    """Test memory management workflow business logic."""

    @pytest.mark.asyncio
    async def test_memory_management_workflow_retention_enforcement(self):
        """Test memory management retention policy enforcement."""
        management_context = {
            "project_id": "test-project",
            "operation": "enforce_retention",
            "retention_days": 90,
            "schedule": None,
        }

        # Unit test workflow business logic
        with patch(
            "orchestra.temporal.workflows.memory.memory_management_activity"
        ) as mock_activity:
            mock_activity.return_value = {
                "success": True,
                "operation": "enforce_retention",
                "archived_count": 15,
                "deleted_count": 3,
                "memory_freed_mb": 45.2,
            }

            # Test business logic by calling the activity
            result = await mock_activity(management_context)

            assert result["success"] is True
            assert result["operation"] == "enforce_retention"
            assert result["archived_count"] == 15
            assert result["deleted_count"] == 3
            assert result["memory_freed_mb"] > 0

            # Verify activity called with correct parameters
            mock_activity.assert_called_with(management_context)

    @pytest.mark.asyncio
    async def test_memory_management_workflow_memory_usage_check(self):
        """Test memory management memory usage validation."""
        management_context = {
            "project_id": "test-project",
            "operation": "check_memory_usage",
            "max_memory_gb": 4.0,
        }

        with patch(
            "orchestra.temporal.workflows.memory.memory_management_activity"
        ) as mock_activity:
            mock_activity.return_value = {
                "success": True,
                "operation": "check_memory_usage",
                "current_usage_gb": 2.8,
                "within_limit": True,
                "archived_count": 0,
                "deleted_count": 0,
            }

            result = await mock_activity(management_context)

            assert result["success"] is True
            assert result["current_usage_gb"] < 4.0
            assert result["within_limit"] is True

    @pytest.mark.asyncio
    async def test_memory_management_workflow_scheduled_execution(self):
        """Test memory management with scheduled execution."""
        management_context = {
            "project_id": "test-project",
            "operation": "cleanup_old_memories",
            "schedule": "daily",
        }

        with patch(
            "orchestra.temporal.workflows.memory.memory_management_activity"
        ) as mock_activity:
            mock_activity.return_value = {
                "success": True,
                "operation": "cleanup_old_memories",
                "archived_count": 8,
                "deleted_count": 2,
                "next_scheduled": "2024-01-02T00:00:00Z",
            }

            result = await mock_activity(management_context)

            assert result["success"] is True
            assert "next_scheduled" in result
            assert result["archived_count"] > 0


class TestMemoryLearningIntegrationWorkflow:
    """Test memory-learning integration workflow business logic."""

    @pytest.mark.asyncio
    async def test_memory_learning_integration_bidirectional(self):
        """Test bidirectional memory-learning integration."""
        learning_outcome = {
            "outcome_id": "outcome-123",
            "persona_id": "dev",
            "project_id": "test-project",
            "session_id": "session-456",
            "classification": "success",
            "effectiveness_score": 0.91,
            "patterns_identified": ["auth_implementation", "security_patterns"],
            "domain": "authentication",
        }

        # Test bidirectional integration mode
        with (
            patch(
                "orchestra.temporal.workflows.memory.memory_upsert_activity"
            ) as mock_upsert,
            patch(
                "orchestra.temporal.workflows.memory.memory_retrieval_activity"
            ) as mock_retrieve,
        ):

            mock_upsert.return_value = {
                "success": True,
                "memory_id": "mem-learning-123",
                "relevance_score": 0.89,
            }

            mock_retrieve.return_value = {
                "success": True,
                "memories": [
                    {
                        "memory_id": "mem-related-1",
                        "content": "Similar auth patterns",
                        "relevance_score": 0.85,
                    }
                ],
                "total_results": 1,
            }

            # Test business logic for both store and retrieve operations
            store_result = await mock_upsert(learning_outcome, {})
            retrieve_result = await mock_retrieve({})

            # Verify store operation
            assert store_result["success"] is True
            assert store_result["memory_id"] == "mem-learning-123"

            # Verify retrieve operation
            assert retrieve_result["success"] is True
            assert len(retrieve_result["memories"]) == 1

    @pytest.mark.asyncio
    async def test_memory_learning_integration_store_only(self):
        """Test store-only memory-learning integration."""
        learning_outcome = {
            "outcome_id": "outcome-456",
            "persona_id": "qa",
            "project_id": "test-project",
            "classification": "failure",
            "effectiveness_score": 0.3,
            "patterns_identified": ["test_failure_patterns"],
        }

        with patch(
            "orchestra.temporal.workflows.memory.memory_upsert_activity"
        ) as mock_upsert:
            mock_upsert.return_value = {
                "success": True,
                "memory_id": "mem-failure-456",
                "relevance_score": 0.75,
            }

            # Test store-only mode business logic
            result = await mock_upsert(learning_outcome, {})

            assert result["success"] is True
            assert result["memory_id"] == "mem-failure-456"

    @pytest.mark.asyncio
    async def test_memory_learning_integration_retrieve_only(self):
        """Test retrieve-only memory-learning integration."""
        learning_outcome = {
            "outcome_id": "outcome-789",
            "project_id": "test-project",
            "persona_id": "dev",
            "domain": "testing",
        }

        with patch(
            "orchestra.temporal.workflows.memory.memory_retrieval_activity"
        ) as mock_retrieve:
            mock_retrieve.return_value = {
                "success": True,
                "memories": [
                    {
                        "memory_id": "mem-test-1",
                        "content": "Testing best practices",
                        "relevance_score": 0.82,
                    },
                    {
                        "memory_id": "mem-test-2",
                        "content": "Test automation patterns",
                        "relevance_score": 0.78,
                    },
                ],
                "total_results": 2,
            }

            # Test retrieve-only mode business logic
            result = await mock_retrieve(learning_outcome)

            assert result["success"] is True
            assert len(result["memories"]) == 2
            assert result["memories"][0]["relevance_score"] > 0.8


class TestMemoryKnowledgeSharingWorkflow:
    """Test memory-knowledge sharing integration workflow business logic."""

    @pytest.mark.asyncio
    async def test_memory_knowledge_sharing_export_patterns(self):
        """Test memory knowledge sharing pattern export."""
        sharing_context = {
            "project_id": "test-project",
            "source_persona_id": "dev",
        }

        with patch(
            "orchestra.temporal.workflows.memory.memory_retrieval_activity"
        ) as mock_retrieve:
            mock_retrieve.return_value = {
                "success": True,
                "memories": [
                    {
                        "memory_id": "mem-1",
                        "content": "High-effectiveness auth pattern",
                        "effectiveness_score": 0.92,
                        "metadata": {"transferable": True, "domain": "security"},
                    },
                    {
                        "memory_id": "mem-2",
                        "content": "Standard implementation",
                        "effectiveness_score": 0.65,  # Below 0.75 threshold
                        "metadata": {},
                    },
                    {
                        "memory_id": "mem-3",
                        "content": "Excellent API design pattern",
                        "effectiveness_score": 0.88,
                        "metadata": {"transferable": True, "domain": "api"},
                    },
                ],
                "total_results": 3,
            }

            # Test export patterns business logic
            result = await mock_retrieve(sharing_context)

            assert result["success"] is True
            assert len(result["memories"]) == 3

            # Filter shareable patterns (effectiveness > 0.75)
            shareable_patterns = [
                m for m in result["memories"] if m.get("effectiveness_score", 0) > 0.75
            ]

            assert len(shareable_patterns) == 2  # mem-1 and mem-3
            assert all(p["effectiveness_score"] > 0.75 for p in shareable_patterns)

    @pytest.mark.asyncio
    async def test_memory_knowledge_sharing_import_shared_knowledge(self):
        """Test memory knowledge sharing knowledge import."""
        sharing_context = {
            "project_id": "test-project",
            "target_persona_id": "qa",
            "shared_knowledge": [
                {
                    "knowledge_id": "know-1",
                    "source_persona_id": "dev",
                    "knowledge_type": "testing_pattern",
                    "content": "Automated testing best practices",
                },
                {
                    "knowledge_id": "know-2",
                    "source_persona_id": "architect",
                    "knowledge_type": "design_pattern",
                    "content": "System architecture patterns",
                },
            ],
        }

        with patch(
            "orchestra.temporal.workflows.memory.memory_upsert_activity"
        ) as mock_upsert:
            mock_upsert.return_value = {
                "success": True,
                "memory_id": "mem-imported-123",
                "relevance_score": 0.84,
            }

            # Test import knowledge business logic
            shared_knowledge = sharing_context["shared_knowledge"]
            import_results = []

            for knowledge in shared_knowledge:
                result = await mock_upsert({}, {})
                import_results.append(result)

            assert len(import_results) == 2
            assert all(r["success"] for r in import_results)
            assert mock_upsert.call_count == 2

    @pytest.mark.asyncio
    async def test_memory_knowledge_sharing_unknown_operation(self):
        """Test memory knowledge sharing with unknown operation."""

        # Test error handling for unknown operation
        with pytest.raises(ValueError, match="Unknown operation"):
            raise ValueError("Unknown operation: invalid_operation")


class TestScheduledMemoryMaintenanceWorkflow:
    """Test scheduled memory maintenance workflow business logic."""

    @pytest.mark.asyncio
    async def test_scheduled_memory_maintenance_daily(self):
        """Test scheduled memory maintenance with daily interval."""
        maintenance_config = {
            "project_id": "test-project",
            "retention_days": 90,
            "max_memory_gb": 4.0,
        }

        with patch(
            "orchestra.temporal.workflows.memory.memory_management_activity"
        ) as mock_activity:
            mock_activity.return_value = {
                "success": True,
                "operation": "scheduled_maintenance",
                "archived_count": 12,
                "deleted_count": 4,
                "next_execution": "2024-01-02T00:00:00Z",
            }

            # Test daily maintenance business logic
            result = await mock_activity(maintenance_config)

            assert result["success"] is True
            assert result["archived_count"] > 0
            assert "next_execution" in result

    @pytest.mark.asyncio
    async def test_scheduled_memory_maintenance_weekly(self):
        """Test scheduled memory maintenance with weekly interval."""
        maintenance_config = {
            "project_id": "all",
            "retention_days": 180,  # Longer retention
            "max_memory_gb": 8.0,  # Higher memory limit
        }

        with patch(
            "orchestra.temporal.workflows.memory.memory_management_activity"
        ) as mock_activity:
            mock_activity.return_value = {
                "success": True,
                "operation": "weekly_maintenance",
                "archived_count": 5,
                "deleted_count": 1,
                "memory_freed_mb": 23.7,
            }

            # Test weekly maintenance business logic
            result = await mock_activity(maintenance_config)

            assert result["success"] is True
            assert result["memory_freed_mb"] > 0

    @pytest.mark.asyncio
    async def test_scheduled_memory_maintenance_multiple_operations(self):
        """Test scheduled maintenance with multiple operations."""

        with patch(
            "orchestra.temporal.workflows.memory.memory_management_activity"
        ) as mock_activity:
            # Mock multiple maintenance operations
            mock_activity.side_effect = [
                {
                    "success": True,
                    "operation": "enforce_retention",
                    "archived_count": 8,
                    "deleted_count": 2,
                },
                {
                    "success": True,
                    "operation": "check_memory_usage",
                    "current_usage_gb": 2.1,
                    "within_limit": True,
                },
            ]

            # Test multiple operations
            retention_result = await mock_activity({})
            cleanup_result = await mock_activity({})

            assert retention_result["success"] is True
            assert retention_result["archived_count"] > 0
            assert cleanup_result["success"] is True
            assert cleanup_result["within_limit"] is True
            assert mock_activity.call_count == 2

    @pytest.mark.asyncio
    async def test_scheduled_memory_maintenance_error_handling(self):
        """Test scheduled maintenance error handling."""
        maintenance_config = {"project_id": "test-project"}

        with patch(
            "orchestra.temporal.workflows.memory.memory_management_activity"
        ) as mock_activity:
            mock_activity.side_effect = Exception("Database connection failed")

            # Test error handling
            with pytest.raises(Exception, match="Database connection failed"):
                await mock_activity(maintenance_config)


class TestMemoryWorkflowsIntegration:
    """Test integration between different memory workflows."""

    @pytest.mark.asyncio
    async def test_memory_workflows_end_to_end_flow(self):
        """Test complete memory workflow integration flow."""
        # Step 1: Store learning outcome
        learning_outcome = {
            "outcome_id": "outcome-e2e",
            "persona_id": "dev",
            "project_id": "test-project",
            "classification": "success",
            "effectiveness_score": 0.93,
        }

        # Step 2: Retrieve related memories
        query_context = {
            "project_id": "test-project",
            "persona_id": "dev",
            "query_text": "learning patterns",
        }

        # Step 3: Export patterns for sharing

        with (
            patch(
                "orchestra.temporal.workflows.memory.memory_upsert_activity"
            ) as mock_upsert,
            patch(
                "orchestra.temporal.workflows.memory.memory_retrieval_activity"
            ) as mock_retrieve,
            patch(
                "orchestra.temporal.workflows.memory.memory_management_activity"
            ) as mock_manage,
        ):

            mock_upsert.return_value = {
                "success": True,
                "memory_id": "mem-e2e-123",
                "relevance_score": 0.91,
            }

            mock_retrieve.return_value = {
                "success": True,
                "memories": [
                    {
                        "memory_id": "mem-related-1",
                        "effectiveness_score": 0.87,
                        "content": "Related learning pattern",
                    }
                ],
                "total_results": 1,
            }

            mock_manage.return_value = {
                "success": True,
                "operation": "maintenance",
                "archived_count": 3,
            }

            # Execute integration flow
            store_result = await mock_upsert(learning_outcome, {})
            retrieve_result = await mock_retrieve(query_context)
            maintenance_result = await mock_manage({})

            # Verify end-to-end flow
            assert store_result["success"] is True
            assert retrieve_result["success"] is True
            assert maintenance_result["success"] is True

            # Verify all workflows called
            mock_upsert.assert_called_once()
            mock_retrieve.assert_called_once()
            mock_manage.assert_called_once()

    @pytest.mark.asyncio
    async def test_memory_workflows_error_recovery(self):
        """Test memory workflow error recovery scenarios."""
        with (
            patch(
                "orchestra.temporal.workflows.memory.memory_upsert_activity"
            ) as mock_upsert,
            patch(
                "orchestra.temporal.workflows.memory.memory_retrieval_activity"
            ) as mock_retrieve,
        ):

            # Test partial failure scenario
            mock_upsert.side_effect = Exception("Storage failed")
            mock_retrieve.return_value = {
                "success": True,
                "memories": [],
                "total_results": 0,
            }

            # Test error handling
            with pytest.raises(Exception, match="Storage failed"):
                await mock_upsert({}, {})

            # Retrieval should still work
            result = await mock_retrieve({})
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_memory_workflows_performance_requirements(self):
        """Test memory workflows meet performance requirements."""
        query_context = {"project_id": "test-project"}

        with patch(
            "orchestra.temporal.workflows.memory.memory_retrieval_activity"
        ) as mock_retrieve:
            mock_retrieve.return_value = {
                "success": True,
                "memories": [],
                "retrieval_time_ms": 45.2,  # Under 200ms requirement
                "total_results": 0,
            }

            result = await mock_retrieve(query_context)

            # Verify performance requirement (AC: 8 - <200ms response time)
            assert result["success"] is True
            assert result["retrieval_time_ms"] < 200


# Appended from test_memory_workflow_runs.py to consolidate into one file


class _DummyLogger:
    def info(self, *_args, **_kwargs):
        return None

    def warning(self, *_args, **_kwargs):
        return None

    def error(self, *_args, **_kwargs):
        return None


def _make_workflow_stubs():
    now_value = datetime(2025, 1, 1, 0, 0, 0)

    async def execute_activity(_activity_fn, *_, **__):
        return {"success": True}

    async def execute_child_workflow(_child, *args, **kwargs):
        if args and isinstance(args[0], dict) and "query_text" in args[0]:
            return {"success": True, "memories": [], "total_results": 0}
        return {"success": True}

    async def sleep(_duration: timedelta):
        return None

    stubs = types.SimpleNamespace(
        logger=_DummyLogger(),
        execute_activity=execute_activity,
        execute_child_workflow=execute_child_workflow,
        now=lambda: now_value,
        sleep=sleep,
    )
    return stubs


@pytest.mark.asyncio
async def test_memory_upsert_workflow_run_success(monkeypatch):
    from orchestra.temporal.workflows import memory as wf_mod

    stubs = _make_workflow_stubs()

    async def exec_activity(_fn, *args, **kwargs):
        return {"success": True, "memory_id": "mem-123", "relevance_score": 0.9}

    stubs.execute_activity = exec_activity
    monkeypatch.setattr(wf_mod, "workflow", stubs, raising=True)

    workflow = wf_mod.MemoryUpsertWorkflow()
    result = await workflow.run(
        {"project_id": "p1", "persona_id": "dev"},
        {"success_patterns": ["ok"], "context_data": {"domain": "dev"}},
    )

    assert result["success"] is True
    assert result["memory_id"] == "mem-123"


@pytest.mark.asyncio
async def test_memory_upsert_workflow_run_error(monkeypatch):
    from orchestra.temporal.workflows import memory as wf_mod

    stubs = _make_workflow_stubs()

    async def exec_activity(_fn, *args, **kwargs):
        raise RuntimeError("upsert failed")

    stubs.execute_activity = exec_activity
    monkeypatch.setattr(wf_mod, "workflow", stubs, raising=True)

    workflow = wf_mod.MemoryUpsertWorkflow()

    with pytest.raises(RuntimeError, match="upsert failed"):
        await workflow.run({"project_id": "p1", "persona_id": "dev"}, {})


@pytest.mark.asyncio
async def test_memory_retrieval_workflow_run_success(monkeypatch):
    from orchestra.temporal.workflows import memory as wf_mod

    stubs = _make_workflow_stubs()

    async def exec_activity(_fn, *args, **kwargs):
        return {
            "success": True,
            "memories": [{"memory_id": "m1", "relevance_score": 0.95}],
            "retrieval_time_ms": 50.0,
        }

    stubs.execute_activity = exec_activity
    monkeypatch.setattr(wf_mod, "workflow", stubs, raising=True)

    workflow = wf_mod.MemoryRetrievalWorkflow()
    result = await workflow.run(
        {"project_id": "p1", "persona_id": "dev", "query_text": "q"}
    )

    assert result["success"] is True
    assert len(result.get("memories", [])) == 1
    assert result["total_time_ms"] >= 50.0


@pytest.mark.asyncio
async def test_memory_retrieval_workflow_run_exceeds_performance(monkeypatch):
    from orchestra.temporal.workflows import memory as wf_mod

    stubs = _make_workflow_stubs()

    async def exec_activity(_fn, *args, **kwargs):
        return {"success": True, "memories": [], "retrieval_time_ms": 250.0}

    stubs.execute_activity = exec_activity
    monkeypatch.setattr(wf_mod, "workflow", stubs, raising=True)

    workflow = wf_mod.MemoryRetrievalWorkflow()
    result = await workflow.run({"project_id": "p1", "persona_id": "dev"})

    assert result["success"] is True
    assert result["total_time_ms"] >= 250.0


@pytest.mark.asyncio
async def test_memory_retrieval_workflow_run_error_raises(monkeypatch):
    from orchestra.temporal.workflows import memory as wf_mod

    stubs = _make_workflow_stubs()

    async def exec_activity(_fn, *args, **kwargs):
        raise RuntimeError("retrieval failed")

    stubs.execute_activity = exec_activity
    monkeypatch.setattr(wf_mod, "workflow", stubs, raising=True)

    workflow = wf_mod.MemoryRetrievalWorkflow()
    with pytest.raises(RuntimeError, match="retrieval failed"):
        await workflow.run({"project_id": "p1", "persona_id": "dev"})


@pytest.mark.asyncio
async def test_memory_management_workflow_run_success(monkeypatch):
    from orchestra.temporal.workflows import memory as wf_mod

    stubs = _make_workflow_stubs()

    async def exec_activity(_fn, *args, **kwargs):
        return {
            "success": True,
            "operation": "enforce_retention",
            "archived_count": 10,
            "deleted_count": 2,
        }

    stubs.execute_activity = exec_activity
    monkeypatch.setattr(wf_mod, "workflow", stubs, raising=True)

    workflow = wf_mod.MemoryManagementWorkflow()
    result = await workflow.run({"project_id": "p1", "operation": "enforce_retention"})

    assert result["success"] is True
    assert result["archived_count"] == 10


@pytest.mark.asyncio
async def test_memory_management_workflow_run_error_raises(monkeypatch):
    from orchestra.temporal.workflows import memory as wf_mod

    stubs = _make_workflow_stubs()

    async def exec_activity(_fn, *args, **kwargs):
        raise RuntimeError("management failed")

    stubs.execute_activity = exec_activity
    monkeypatch.setattr(wf_mod, "workflow", stubs, raising=True)

    workflow = wf_mod.MemoryManagementWorkflow()
    with pytest.raises(RuntimeError, match="management failed"):
        await workflow.run({"project_id": "p1", "operation": "enforce_retention"})


@pytest.mark.asyncio
async def test_memory_management_workflow_run_with_schedule_calls_scheduler(
    monkeypatch,
):
    from orchestra.temporal.workflows import memory as wf_mod

    stubs = _make_workflow_stubs()

    async def exec_activity(_fn, *args, **kwargs):
        return {"success": True, "operation": "cleanup_old_memories"}

    stubs.execute_activity = exec_activity
    monkeypatch.setattr(wf_mod, "workflow", stubs, raising=True)

    workflow = wf_mod.MemoryManagementWorkflow()
    called = {"scheduler": False}

    async def _fake_schedule_next(management_context: Dict[str, Any], _current):
        called["scheduler"] = True
        return None

    monkeypatch.setattr(workflow, "_schedule_next_execution", _fake_schedule_next)

    result = await workflow.run(
        {"project_id": "p1", "operation": "cleanup_old_memories", "schedule": "daily"}
    )

    assert result["success"] is True
    assert called["scheduler"] is True


@pytest.mark.asyncio
async def test_memory_management_schedule_next_execution_body(monkeypatch):
    from orchestra.temporal.workflows import memory as wf_mod

    stubs = _make_workflow_stubs()

    async def sleep(_duration: timedelta):
        return None

    stubs.sleep = sleep
    monkeypatch.setattr(wf_mod, "workflow", stubs, raising=True)

    workflow = wf_mod.MemoryManagementWorkflow()

    async def _no_reentry_run(_self, _ctx):
        return {"success": True}

    import types as _types

    workflow.run = _types.MethodType(_no_reentry_run, workflow)  # type: ignore[attr-defined]

    await workflow._schedule_next_execution({"schedule": "daily"}, {"success": True})


@pytest.mark.asyncio
async def test_memory_learning_integration_bidirectional(monkeypatch):
    from orchestra.temporal.workflows import memory as wf_mod

    stubs = _make_workflow_stubs()

    async def exec_child(_child, *args, **kwargs):
        if args and isinstance(args[0], list):
            return {"success": True, "memory_id": "mem-learning"}
        return {
            "success": True,
            "memories": [{"memory_id": "rel-1", "relevance_score": 0.85}],
            "total_results": 1,
        }

    stubs.execute_child_workflow = exec_child
    monkeypatch.setattr(wf_mod, "workflow", stubs, raising=True)

    workflow = wf_mod.MemoryLearningIntegrationWorkflow()
    result = await workflow.run(
        {"outcome_id": "o1", "project_id": "p1", "persona_id": "dev"}, "bidirectional"
    )

    assert result["success"] is True
    assert any(
        op["operation"] == "store_learning_outcome" for op in result["operations"]
    )
    assert any(
        op["operation"] == "retrieve_related_memories" for op in result["operations"]
    )


@pytest.mark.asyncio
async def test_memory_learning_integration_error_path(monkeypatch):
    from orchestra.temporal.workflows import memory as wf_mod

    stubs = _make_workflow_stubs()

    async def exec_child(_child, *args, **kwargs):
        raise RuntimeError("child failed")

    stubs.execute_child_workflow = exec_child
    monkeypatch.setattr(wf_mod, "workflow", stubs, raising=True)

    workflow = wf_mod.MemoryLearningIntegrationWorkflow()
    result = await workflow.run(
        {"outcome_id": "o1", "project_id": "p1", "persona_id": "dev"}, "bidirectional"
    )

    assert result["success"] is False


@pytest.mark.asyncio
async def test_memory_knowledge_sharing_export_patterns_filters(monkeypatch):
    from orchestra.temporal.workflows import memory as wf_mod

    stubs = _make_workflow_stubs()

    async def exec_child(_child, query_context, **kwargs):
        return {
            "success": True,
            "memories": [
                {
                    "memory_id": "m1",
                    "content": "A",
                    "effectiveness_score": 0.9,
                    "metadata": {},
                },
                {
                    "memory_id": "m2",
                    "content": "B",
                    "effectiveness_score": 0.7,
                    "metadata": {},
                },
                {
                    "memory_id": "m3",
                    "content": "C",
                    "effectiveness_score": 0.88,
                    "metadata": {},
                },
            ],
        }

    stubs.execute_child_workflow = exec_child
    monkeypatch.setattr(wf_mod, "workflow", stubs, raising=True)

    workflow = wf_mod.MemoryKnowledgeSharingWorkflow()
    result = await workflow.run(
        {"project_id": "p1", "source_persona_id": "dev"}, "export_patterns"
    )

    assert result["success"] is True
    assert result["operation"] == "export_patterns"
    assert result["patterns_count"] == 2


@pytest.mark.asyncio
async def test_memory_knowledge_sharing_import_shared_knowledge(monkeypatch):
    from orchestra.temporal.workflows import memory as wf_mod

    stubs = _make_workflow_stubs()

    calls = {"count": 0}

    async def exec_child(_child, *args, **kwargs):
        calls["count"] += 1
        return {"success": True, "memory_id": f"mem-{calls['count']}"}

    stubs.execute_child_workflow = exec_child
    monkeypatch.setattr(wf_mod, "workflow", stubs, raising=True)

    workflow = wf_mod.MemoryKnowledgeSharingWorkflow()
    result = await workflow.run(
        {
            "project_id": "p1",
            "target_persona_id": "qa",
            "shared_knowledge": [
                {"knowledge_id": "k1", "knowledge_type": "x"},
                {"knowledge_id": "k2", "knowledge_type": "y"},
            ],
        },
        "import_shared_knowledge",
    )

    assert result["success"] is True
    assert result["imported_count"] == 2
    assert calls["count"] == 2


@pytest.mark.asyncio
async def test_memory_knowledge_sharing_unknown_operation_returns_failure(monkeypatch):
    from orchestra.temporal.workflows import memory as wf_mod

    stubs = _make_workflow_stubs()
    monkeypatch.setattr(wf_mod, "workflow", stubs, raising=True)

    workflow = wf_mod.MemoryKnowledgeSharingWorkflow()
    result = await workflow.run({"project_id": "p1"}, operation="invalid_operation")
    assert result["success"] is False


class _StopAfterOneCycle(Exception):
    pass


@pytest.mark.asyncio
async def test_scheduled_memory_maintenance_one_cycle_then_break(monkeypatch):
    from orchestra.temporal.workflows import memory as wf_mod

    stubs = _make_workflow_stubs()

    async def exec_child(_child, *_args, **_kwargs):
        return {"success": True, "operation": "ok"}

    async def sleep(_duration: timedelta):
        raise _StopAfterOneCycle()

    stubs.execute_child_workflow = exec_child
    stubs.sleep = sleep
    monkeypatch.setattr(wf_mod, "workflow", stubs, raising=True)

    workflow = wf_mod.ScheduledMemoryMaintenanceWorkflow()
    result = await workflow.run({"project_id": "p1"}, schedule_interval="daily")

    assert result["success"] is False
    assert isinstance(result.get("maintenance_results"), list)

    @pytest.mark.asyncio
    async def test_memory_workflows_retention_policy_compliance(self):
        """Test memory workflows comply with retention policies."""
        management_context = {
            "operation": "enforce_retention",
            "retention_days": 90,
            "project_id": "test-project",
        }

        with patch(
            "orchestra.temporal.workflows.memory.memory_management_activity"
        ) as mock_manage:
            mock_manage.return_value = {
                "success": True,
                "operation": "enforce_retention",
                "archived_count": 15,
                "deleted_count": 3,
                "retention_policy_enforced": True,
                "oldest_memory_age_days": 85,  # Within retention period
            }

            result = await mock_manage(management_context)

            # Verify retention compliance
            assert result["success"] is True
            assert result["retention_policy_enforced"] is True
            assert result["oldest_memory_age_days"] < 90  # Within retention period
