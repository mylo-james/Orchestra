"""Tests for memory service based on Story 2.1 PRD requirements."""

import time
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest

from orchestra.models.memory import (
    MemoryRecord,
    RetentionPolicy,
)
from orchestra.services.memory_service import MemoryService


class TestMemoryService:
    """Test MemoryService for memory storage and retrieval (AC: 1, 6, 8, 9)."""

    @pytest.fixture
    def mock_qdrant_client(self):
        """Mock Qdrant client for testing."""
        with patch("orchestra.services.memory_service.QdrantClient") as mock_client:
            mock_instance = Mock()
            mock_client.return_value = mock_instance

            # Mock collection operations
            mock_instance.get_collections.return_value = Mock(collections=[])
            mock_instance.create_collection = Mock()
            mock_instance.upsert = Mock()
            mock_instance.search = Mock()
            mock_instance.retrieve = Mock()

            yield mock_instance

    @pytest.fixture
    def mock_embedding_service(self):
        """Mock embedding service for testing."""
        with patch(
            "orchestra.services.memory_service.EmbeddingService"
        ) as mock_service:
            mock_instance = Mock()
            mock_service.return_value = mock_instance

            # Mock embedding generation
            mock_instance.generate_embedding = AsyncMock(
                return_value=[0.1] * 3072  # text-embedding-3-large dimension
            )

            yield mock_instance

    @pytest.fixture
    def memory_service(self, mock_qdrant_client, mock_embedding_service):
        """Create MemoryService instance for testing."""
        return MemoryService(
            qdrant_host="localhost",
            qdrant_port=6333,
            collection_name="test_orchestra_memory",
            embedding_service=mock_embedding_service,
        )

    @pytest.mark.asyncio
    async def test_memory_service_initialization(
        self, memory_service, mock_qdrant_client
    ):
        """Test MemoryService initializes with proper configuration."""
        assert memory_service.collection_name == "test_orchestra_memory"
        assert memory_service.client == mock_qdrant_client
        assert memory_service._cache_ttl == 300  # 5 minutes

        # Verify collection initialization was attempted
        mock_qdrant_client.get_collections.assert_called_once()

    @pytest.mark.asyncio
    async def test_memory_upsert_success(
        self, memory_service, mock_qdrant_client, mock_embedding_service
    ):
        """Test successful memory upsert with namespace isolation."""
        memory_record = MemoryRecord(
            memory_id="test-memory-1",
            project_id="test-project",
            persona_id="dev",
            content="Test authentication implementation pattern",
            embedding=[0.1] * 3072,
            confidence_score=0.88,
            relevance_score=0.92,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            metadata={
                "domain": "authentication",
                "complexity": "medium",
                "success_indicators": ["high_coverage", "security_validated"],
            },
        )

        # Mock successful upsert
        mock_qdrant_client.upsert = Mock()

        result = await memory_service.upsert_memory(memory_record)

        assert result["success"] is True
        assert result["memory_id"] == "test-memory-1"
        assert result["namespace"] == "orchestra_memory_test-project"

        # Verify Qdrant upsert was called
        mock_qdrant_client.upsert.assert_called_once()

        # Verify embedding generation was called
        mock_embedding_service.generate_embedding.assert_called_once_with(
            "Test authentication implementation pattern"
        )

    @pytest.mark.asyncio
    async def test_memory_upsert_relevance_scoring(self, memory_service):
        """Test memory upsert with relevance scoring (AC: 7 - >80% relevance)."""
        high_relevance_memory = MemoryRecord(
            memory_id="high-relevance",
            project_id="test-project",
            persona_id="dev",
            content="Comprehensive authentication pattern with detailed implementation guide",
            embedding=[0.1] * 3072,
            confidence_score=0.95,
            relevance_score=0.92,  # AC: 7 - >80% relevance score
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            metadata={"domain": "authentication", "detail_level": "comprehensive"},
        )

        low_relevance_memory = MemoryRecord(
            memory_id="low-relevance",
            project_id="test-project",
            persona_id="dev",
            content="Simple task completion",
            embedding=[0.1] * 3072,
            confidence_score=0.60,
            relevance_score=0.65,  # Below 80% threshold
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            metadata={"domain": "general", "detail_level": "minimal"},
        )

        # High relevance should be accepted
        high_result = await memory_service.upsert_memory(high_relevance_memory)
        assert high_result["success"] is True
        assert high_result["relevance_score"] > 0.8  # AC: 7

        # Low relevance should be rejected or flagged
        low_result = await memory_service.upsert_memory(low_relevance_memory)
        if not low_result["success"]:
            assert "relevance score too low" in low_result.get("reason", "")
        else:
            assert low_result["relevance_score"] < 0.8

    @pytest.mark.asyncio
    async def test_memory_retrieval_performance(
        self, memory_service, mock_qdrant_client
    ):
        """Test memory retrieval meets performance requirements (AC: 8 - <200ms)."""
        # Mock Qdrant search results
        mock_search_results = [
            Mock(
                payload={
                    "content": "Retrieved memory content",
                    "metadata": {
                        "memory_id": "retrieved-memory",
                        "project_id": "test-project",
                        "confidence_score": 0.88,
                        "created_at": datetime.utcnow().isoformat(),
                        "updated_at": datetime.utcnow().isoformat(),
                    },
                    "version": 1,
                },
                vector=[0.1] * 3072,
                score=0.92,
            )
        ]
        mock_qdrant_client.search.return_value = mock_search_results

        query_context = {
            "project_id": "test-project",
            "persona_id": "dev",
            "query_text": "authentication implementation patterns",
            "max_results": 10,
        }

        start_time = time.time()
        result = await memory_service.retrieve_memories(query_context)
        end_time = time.time()

        retrieval_time_ms = (end_time - start_time) * 1000

        assert result["success"] is True
        assert len(result["memories"]) == 1
        assert retrieval_time_ms < 200  # AC: 8 - <200ms response time
        assert result["retrieval_time_ms"] < 200

    @pytest.mark.asyncio
    async def test_memory_namespace_isolation(self, memory_service, mock_qdrant_client):
        """Test memory service respects project namespace isolation."""
        project_a_memory = MemoryRecord(
            memory_id="project-a-memory",
            project_id="project-a",
            persona_id="dev",
            content="Project A specific memory",
            embedding=[0.1] * 3072,
            confidence_score=0.85,
            relevance_score=0.90,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        project_b_memory = MemoryRecord(
            memory_id="project-b-memory",
            project_id="project-b",
            persona_id="dev",
            content="Project B specific memory",
            embedding=[0.2] * 3072,
            confidence_score=0.85,
            relevance_score=0.90,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Upsert memories for different projects
        result_a = await memory_service.upsert_memory(project_a_memory)
        result_b = await memory_service.upsert_memory(project_b_memory)

        assert result_a["namespace"] == "orchestra_memory_project-a"
        assert result_b["namespace"] == "orchestra_memory_project-b"
        assert result_a["namespace"] != result_b["namespace"]

        # Verify search respects namespace isolation
        query_a = {"project_id": "project-a", "query_text": "memory"}
        query_b = {"project_id": "project-b", "query_text": "memory"}

        # Mock different search results for different namespaces
        mock_qdrant_client.search.side_effect = [
            [Mock(payload={"content": "Project A memory"}, vector=[0.1] * 3072)],
            [Mock(payload={"content": "Project B memory"}, vector=[0.2] * 3072)],
        ]

        result_a_search = await memory_service.retrieve_memories(query_a)
        result_b_search = await memory_service.retrieve_memories(query_b)

        # Each project should only see its own memories
        assert result_a_search["success"] is True
        assert result_b_search["success"] is True

    @pytest.mark.asyncio
    async def test_memory_footprint_management(self, memory_service):
        """Test memory service manages 4GB footprint constraint (AC: 9)."""
        # Test memory usage monitoring
        current_usage = await memory_service.get_memory_usage()

        assert "current_memory_gb" in current_usage
        assert "within_limits" in current_usage
        assert current_usage["memory_limit_gb"] == 4.0  # AC: 9 - 4GB constraint

        # Test cleanup trigger when approaching limits
        if current_usage["current_memory_gb"] > 3.5:  # Approaching 4GB limit
            cleanup_result = await memory_service.trigger_cleanup()

            assert cleanup_result["cleanup_triggered"] is True
            assert cleanup_result["memory_freed_gb"] > 0

            # Verify memory usage is reduced
            post_cleanup_usage = await memory_service.get_memory_usage()
            assert (
                post_cleanup_usage["current_memory_gb"]
                < current_usage["current_memory_gb"]
            )

    @pytest.mark.asyncio
    async def test_memory_retention_policy_enforcement(self, memory_service):
        """Test memory service enforces retention policies (AC: 10 - 90 days)."""
        retention_policy = RetentionPolicy(
            policy_id="test-retention-policy",
            project_id="test-project",
            policy_name="90-day retention",
            retention_days=90,  # AC: 10 - 90 days retention
            archive_after_days=90,
            delete_after_days=365,
            rules={
                "standard_retention": {"min_relevance_score": 0.70},
                "extended_retention": {
                    "min_relevance_score": 0.90,
                    "retention_days": 180,
                },
            },
            active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Test old memory (>90 days) should be archived
        old_memory = MemoryRecord(
            memory_id="old-memory",
            project_id="test-project",
            persona_id="dev",
            content="Old memory content",
            embedding=[0.1] * 3072,
            confidence_score=0.75,
            relevance_score=0.80,
            created_at=datetime.utcnow() - timedelta(days=95),  # 95 days old
            updated_at=datetime.utcnow() - timedelta(days=95),
        )

        # Test recent memory should be retained
        recent_memory = MemoryRecord(
            memory_id="recent-memory",
            project_id="test-project",
            persona_id="dev",
            content="Recent memory content",
            embedding=[0.1] * 3072,
            confidence_score=0.85,
            relevance_score=0.90,
            created_at=datetime.utcnow() - timedelta(days=30),  # 30 days old
            updated_at=datetime.utcnow() - timedelta(days=30),
        )

        enforcement_result = await memory_service.enforce_retention_policy(
            retention_policy, [old_memory, recent_memory]
        )

        assert enforcement_result["memories_processed"] == 2
        assert (
            enforcement_result["memories_archived"] >= 1
        )  # Old memory should be archived
        assert (
            enforcement_result["memories_retained"] >= 1
        )  # Recent memory should be retained

    @pytest.mark.asyncio
    async def test_memory_service_caching(self, memory_service):
        """Test memory service caching for performance optimization."""
        memory_record = MemoryRecord(
            memory_id="cached-memory",
            project_id="test-project",
            persona_id="dev",
            content="Cached memory content",
            embedding=[0.1] * 3072,
            confidence_score=0.85,
            relevance_score=0.90,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # First upsert - should cache the memory
        await memory_service.upsert_memory(memory_record)

        # Verify memory is in cache
        cache_key = "test-project:cached-memory"
        assert cache_key in memory_service._memory_cache

        # Second retrieval - should use cache
        start_time = time.time()
        cached_result = await memory_service.get_memory("cached-memory", "test-project")
        end_time = time.time()

        cache_retrieval_time = (end_time - start_time) * 1000

        assert cached_result["success"] is True
        assert cached_result["from_cache"] is True
        assert cache_retrieval_time < 10  # Cache retrieval should be very fast

    @pytest.mark.asyncio
    async def test_memory_service_temporal_integration(self, memory_service):
        """Test memory service integrates with Temporal workflow orchestration."""
        # Test memory operations can be called from Temporal workflows
        temporal_context = {
            "workflow_id": "memory-workflow-123",
            "run_id": "run-456",
            "activity_id": "memory-upsert-activity",
        }

        memory_record = MemoryRecord(
            memory_id="temporal-memory",
            project_id="temporal-project",
            persona_id="dev",
            content="Memory from Temporal workflow",
            embedding=[0.1] * 3072,
            confidence_score=0.85,
            relevance_score=0.90,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            metadata={"temporal_context": temporal_context},
        )

        result = await memory_service.upsert_memory(memory_record, temporal_context)

        assert result["success"] is True
        assert result["temporal_context"]["workflow_id"] == "memory-workflow-123"
        assert result["temporal_context"]["run_id"] == "run-456"

    @pytest.mark.asyncio
    async def test_memory_service_error_handling(
        self, memory_service, mock_qdrant_client
    ):
        """Test memory service error handling and circuit breaker patterns."""
        # Test Qdrant connection failure
        mock_qdrant_client.upsert.side_effect = Exception("Qdrant connection failed")

        memory_record = MemoryRecord(
            memory_id="error-memory",
            project_id="test-project",
            persona_id="dev",
            content="Memory that will fail",
            embedding=[0.1] * 3072,
            confidence_score=0.85,
            relevance_score=0.90,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        result = await memory_service.upsert_memory(memory_record)

        assert result["success"] is False
        assert "error" in result
        assert "Qdrant connection failed" in result["error"]

        # Test circuit breaker activation after multiple failures
        for _ in range(5):  # Trigger circuit breaker threshold
            await memory_service.upsert_memory(memory_record)

        circuit_breaker_status = memory_service.get_circuit_breaker_status()
        assert circuit_breaker_status["state"] in ["open", "half_open"]

    @pytest.mark.asyncio
    async def test_memory_service_context_extraction(self, memory_service):
        """Test memory service context extraction algorithms (AC: 7)."""
        # Test context extraction from persona execution results
        execution_context = {
            "persona_id": "dev",
            "project_id": "test-project",
            "command": "implement-story",
            "result": {
                "success": True,
                "files_created": ["auth.py", "test_auth.py"],
                "tests_passed": 15,
                "coverage": 0.92,
                "security_validated": True,
            },
            "timestamp": datetime.utcnow(),
            "duration_seconds": 45.2,
        }

        extracted_context = await memory_service.extract_context_patterns(
            execution_context
        )

        assert extracted_context["success"] is True
        assert extracted_context["relevance_score"] > 0.8  # AC: 7 - >80% relevance
        assert "success_patterns" in extracted_context
        assert "context_data" in extracted_context

        # Verify extracted patterns contain meaningful information
        patterns = extracted_context["success_patterns"]
        assert "high_test_coverage" in patterns or "security_validation" in patterns

        context_data = extracted_context["context_data"]
        assert context_data["domain"] in ["authentication", "security"]
        assert context_data["success_indicators"] is not None

    @pytest.mark.asyncio
    async def test_memory_service_semantic_search(
        self, memory_service, mock_qdrant_client
    ):
        """Test memory service semantic similarity search."""
        # Mock Qdrant search with semantic similarity results
        mock_search_results = [
            Mock(
                payload={
                    "content": "Authentication implementation with JWT tokens",
                    "metadata": {
                        "memory_id": "auth-jwt-memory",
                        "domain": "authentication",
                        "confidence_score": 0.92,
                        "created_at": datetime.utcnow().isoformat(),
                        "updated_at": datetime.utcnow().isoformat(),
                    },
                },
                vector=[0.1] * 3072,
                score=0.95,  # High semantic similarity
            ),
            Mock(
                payload={
                    "content": "User authentication with OAuth2 flow",
                    "metadata": {
                        "memory_id": "auth-oauth-memory",
                        "domain": "authentication",
                        "confidence_score": 0.88,
                        "created_at": datetime.utcnow().isoformat(),
                        "updated_at": datetime.utcnow().isoformat(),
                    },
                },
                vector=[0.2] * 3072,
                score=0.87,  # Good semantic similarity
            ),
        ]
        mock_qdrant_client.search.return_value = mock_search_results

        query_context = {
            "project_id": "test-project",
            "persona_id": "dev",
            "query_text": "authentication implementation patterns",
            "semantic_search": True,
            "min_similarity": 0.80,
        }

        result = await memory_service.semantic_search(query_context)

        assert result["success"] is True
        assert len(result["memories"]) == 2
        assert all(memory["similarity_score"] > 0.80 for memory in result["memories"])
        assert (
            result["memories"][0]["similarity_score"]
            > result["memories"][1]["similarity_score"]
        )  # Sorted by similarity


class TestMemoryServiceIntegration:
    """Test MemoryService integration with other Epic 2 components."""

    @pytest.mark.asyncio
    async def test_memory_service_learning_integration(self):
        """Test MemoryService integrates with learning workflows."""
        memory_service = MemoryService()

        # Test memory service can store learning outcomes
        learning_outcome = {
            "outcome_id": "learning-outcome-1",
            "persona_id": "dev",
            "project_id": "integration-project",
            "success": True,
            "patterns_identified": ["high_test_coverage", "security_validation"],
            "effectiveness_score": 0.88,
        }

        memory_record = await memory_service.create_memory_from_learning_outcome(
            learning_outcome
        )

        assert memory_record.memory_id is not None
        assert memory_record.project_id == "integration-project"
        assert memory_record.persona_id == "dev"
        assert memory_record.relevance_score > 0.8
        assert "learning_outcome" in memory_record.metadata

    @pytest.mark.asyncio
    async def test_memory_service_knowledge_sharing_integration(self):
        """Test MemoryService integrates with knowledge sharing workflows."""
        memory_service = MemoryService()

        # Test memory service can provide patterns for knowledge sharing
        sharing_context = {
            "source_persona_id": "dev",
            "project_id": "sharing-project",
            "target_personas": ["qa", "architect"],
            "pattern_types": ["success_pattern", "optimization_pattern"],
        }

        shareable_patterns = await memory_service.get_shareable_patterns(
            sharing_context
        )

        assert shareable_patterns["success"] is True
        assert "patterns" in shareable_patterns
        assert all(
            pattern["transferability_score"] > 0.75
            for pattern in shareable_patterns["patterns"]
        )

    @pytest.mark.asyncio
    async def test_memory_service_performance_monitoring(self):
        """Test MemoryService provides performance monitoring capabilities."""
        memory_service = MemoryService()

        # Test memory service tracks performance metrics
        performance_metrics = await memory_service.get_performance_metrics()

        assert "memory_usage_gb" in performance_metrics
        assert "retrieval_latency_ms" in performance_metrics
        assert "cache_hit_rate" in performance_metrics
        assert "retention_policy_compliance" in performance_metrics

        # Verify metrics meet requirements
        assert performance_metrics["memory_usage_gb"] <= 4.0  # AC: 9 - 4GB constraint
        assert (
            performance_metrics["retrieval_latency_ms"] < 200
        )  # AC: 8 - <200ms response
        assert performance_metrics["cache_hit_rate"] > 0.0  # Cache should be used

    @pytest.mark.asyncio
    async def test_memory_service_health_monitoring(self):
        """Test MemoryService provides health monitoring endpoints."""
        memory_service = MemoryService()

        # Test health check endpoint
        health_status = await memory_service.health_check()

        assert "status" in health_status
        assert health_status["status"] in ["healthy", "degraded", "unhealthy"]
        assert "qdrant_connection" in health_status
        assert "memory_usage" in health_status
        assert "cache_status" in health_status
        assert "circuit_breaker_status" in health_status

        # Test detailed health metrics
        if health_status["status"] == "healthy":
            assert health_status["qdrant_connection"] == "connected"
            assert health_status["memory_usage"]["within_limits"] is True
            assert health_status["cache_status"] == "active"
