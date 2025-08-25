"""Targeted coverage boost tests for MemoryService.

These tests exercise error paths and rarely hit branches to raise
per-file coverage to 90%+ while aligning with Story 2.1 ACs.
"""

from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

from orchestra.models.memory import MemoryRecord, RetentionPolicy
from orchestra.services.memory_service import MemoryService


@pytest.fixture
def mock_qdrant_client():
    with patch("orchestra.services.memory_service.QdrantClient") as mock_client:
        instance = Mock()
        # Default: no collections
        instance.get_collections.return_value = Mock(collections=[])
        # Common ops
        instance.create_collection = Mock()
        instance.upsert = Mock()
        instance.search = Mock()
        instance.retrieve = Mock()
        instance.scroll = Mock(return_value=([], None))
        instance.delete = Mock()
        mock_client.return_value = instance
        yield instance


@pytest.fixture
def memory_service(mock_qdrant_client):
    svc = MemoryService(collection_name="test_memory")
    # Avoid real embeddings
    svc.embedding_service.generate_embedding = AsyncMock(return_value=[0.0] * 3072)
    return svc


@pytest.mark.asyncio
async def test_initialize_collections_creates_new(memory_service, mock_qdrant_client):
    await memory_service._initialize_collections()
    mock_qdrant_client.create_collection.assert_called_once()


@pytest.mark.asyncio
async def test_retrieve_memories_with_filters(memory_service, mock_qdrant_client):
    memory_service._collection_exists = AsyncMock(return_value=True)

    # Simulate two results
    mock_qdrant_client.search.return_value = [
        Mock(
            payload={
                "content": "A",
                "metadata": {
                    "memory_id": "m1",
                    "relevance_score": 0.9,
                    "created_at": datetime.utcnow().isoformat(),
                },
            },
            score=0.93,
        ),
        Mock(
            payload={
                "content": "B",
                "metadata": {
                    "memory_id": "m2",
                    "relevance_score": 0.85,
                    "created_at": datetime.utcnow().isoformat(),
                },
            },
            score=0.88,
        ),
    ]

    result = await memory_service.retrieve_memories(
        {
            "project_id": "p1",
            "persona_id": "dev",
            "query_text": "auth",
            "min_relevance_score": 0.8,
            "max_results": 5,
        }
    )

    assert result["success"] is True
    assert result["total_results"] == 2


@pytest.mark.asyncio
async def test_retrieve_memories_exception_path(memory_service):
    memory_service._collection_exists = AsyncMock(return_value=True)

    # Force exception during search
    def _boom(*_a, **_kw):
        raise RuntimeError("boom")

    memory_service.circuit_breaker.call = _boom  # type: ignore[assignment]

    result = await memory_service.retrieve_memories(
        {"project_id": "p1", "query_text": "x"}
    )

    assert result["success"] is False
    assert "boom" in result["error"]


@pytest.mark.asyncio
async def test_trigger_cleanup_removes_low_relevance(
    memory_service, mock_qdrant_client
):
    # One memory collection present
    coll = SimpleNamespace(name="test_memory_projA")
    mock_qdrant_client.get_collections.return_value = Mock(collections=[coll])

    # Low relevance results with ids
    low_items = [
        SimpleNamespace(id=f"id-{i}", payload=None, score=0.0) for i in range(3)
    ]
    mock_qdrant_client.search.return_value = low_items

    result = await memory_service.trigger_cleanup()

    assert result["success"] is True
    assert result["removed_memories"] == 3
    mock_qdrant_client.delete.assert_called_once()


@pytest.mark.asyncio
async def test_trigger_cleanup_exception(memory_service, mock_qdrant_client):
    mock_qdrant_client.get_collections.side_effect = Exception("listing error")
    result = await memory_service.trigger_cleanup()
    assert result["success"] is False
    assert "listing error" in result["error"]


@pytest.mark.asyncio
async def test_get_project_memories_nonempty(memory_service, mock_qdrant_client):
    memory_service._collection_exists = AsyncMock(return_value=True)

    # First batch non-empty, second empty
    first_point = SimpleNamespace(
        payload={
            "content": "hello",
            "metadata": {
                "memory_id": "mid",
                "project_id": "p1",
                "persona_id": "dev",
                "confidence_score": 0.9,
                "relevance_score": 0.9,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            },
        },
        vector=[0.0] * 3072,
    )
    mock_qdrant_client.scroll.side_effect = [([first_point], None), ([], None)]

    records = await memory_service.get_project_memories("p1")
    assert len(records) == 1
    assert isinstance(records[0], MemoryRecord)


@pytest.mark.asyncio
async def test_enforce_retention_policy_delete_and_error(
    memory_service, mock_qdrant_client
):
    # Memory old enough to delete
    old_mem = MemoryRecord(
        memory_id="d1",
        project_id="p1",
        persona_id="dev",
        content="old",
        embedding=[0.0] * 3072,
        confidence_score=0.5,
        relevance_score=0.5,
        created_at=datetime.utcnow() - timedelta(days=400),
        updated_at=datetime.utcnow() - timedelta(days=400),
    )
    policy = RetentionPolicy(
        policy_id="rp",
        project_id="p1",
        policy_name="90 day",
        retention_days=90,
        archive_after_days=90,
        delete_after_days=365,
        rules={},
        active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    ok = await memory_service.enforce_retention_policy(policy, [old_mem])
    assert ok["success"] is True
    assert ok["memories_deleted"] == 1
    mock_qdrant_client.delete.assert_called()

    # Now force delete exception
    mock_qdrant_client.delete.side_effect = Exception("delete fail")
    fail = await memory_service.enforce_retention_policy(policy, [old_mem])
    assert fail["success"] is False
    assert "delete fail" in fail["error"]


@pytest.mark.asyncio
async def test_optimize_indexes_exception(memory_service):
    async def _boom(_name):
        raise RuntimeError("exists check failed")

    memory_service._collection_exists = _boom  # type: ignore[assignment]
    res = await memory_service.optimize_indexes("p1")
    assert res["success"] is False


@pytest.mark.asyncio
async def test_health_check_unhealthy_path(memory_service, mock_qdrant_client):
    mock_qdrant_client.get_collections.side_effect = Exception("down")
    # Force within_limits False to ensure unhealthy
    memory_service.get_memory_usage = AsyncMock(return_value={"within_limits": False})
    health = await memory_service.health_check()
    assert health["status"] == "unhealthy"
    assert health["qdrant_connection"] == "disconnected"


def test_update_average_retrieval_time_running_avg(memory_service):
    # Simulate multiple ops to hit running average branch
    memory_service._performance_metrics["total_operations"] = 2
    memory_service._performance_metrics["average_retrieval_time_ms"] = 100.0
    memory_service._update_average_retrieval_time(200.0)
    assert memory_service._performance_metrics["average_retrieval_time_ms"] != 100.0


@pytest.mark.asyncio
async def test_get_shareable_patterns_success(memory_service):
    async def _fake_retrieve(_ctx):
        return {
            "success": True,
            "memories": [
                {
                    "memory_id": "m1",
                    "content": "pattern A",
                    "relevance_score": 0.9,
                    "metadata": {"confidence_score": 0.9},
                },
                {
                    "memory_id": "m2",
                    "content": "pattern B",
                    "relevance_score": 0.8,
                    "metadata": {"confidence_score": 0.85},
                },
            ],
        }

    memory_service.retrieve_memories = _fake_retrieve  # type: ignore[assignment]
    out = await memory_service.get_shareable_patterns(
        {"project_id": "p1", "source_persona_id": "dev"}
    )
    assert out["success"] is True
    assert out["total_patterns"] == 2
