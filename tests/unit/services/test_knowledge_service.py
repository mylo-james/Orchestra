"""Tests for knowledge service based on PRD requirements."""

import pytest
import time
from typing import Any, Dict, List
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
import uuid

# Import the module to ensure it's loaded for coverage
import src.services.knowledge_service

from src.services.knowledge_service import KnowledgeService
from src.models.knowledge import (
    KnowledgeChunk,
    KnowledgeLock,
    KnowledgeQuery,
    KnowledgeVersion,
    KnowledgeDomain,
    KnowledgeMetadata,
    SecurityClassification
)
from src.services.embedding_service import EmbeddingService


def create_test_knowledge_chunk(
    chunk_id: str = "test-doc",
    content: str = "Test content",
    embedding: List[float] = None,
    metadata_dict: Dict[str, Any] = None,
    version: int = 1,
    author: str = "test-agent"
) -> KnowledgeChunk:
    """Helper to create a test knowledge chunk with proper structure."""
    if embedding is None:
        embedding = [0.1, 0.2, 0.3]
    
    if metadata_dict is None:
        metadata_dict = {}
    
    metadata = KnowledgeMetadata(
        domain=KnowledgeDomain.TECHNICAL,
        tags=["test"],
        source="test",
        confidence=0.9,
        security_classification=SecurityClassification.PUBLIC,
        document_id=chunk_id,
        agent_attribution=author,
        confidence_score=metadata_dict.get("confidence_score", 0.9),
        knowledge_domain=metadata_dict.get("knowledge_domain", "technical")
    )
    
    now = datetime.utcnow()
    return KnowledgeChunk(
        id=chunk_id,
        content=content,
        embedding=embedding,
        metadata=metadata,
        version=version,
        created_at=now,
        updated_at=now,
        author=author
    )


class TestKnowledgeServiceInitialization:
    """Test knowledge service initialization."""

    @patch('src.services.knowledge_service.QdrantClient')
    @patch('src.services.knowledge_service.EmbeddingService')
    def test_initialization_with_defaults(self, mock_embedding_service, mock_qdrant_client):
        """Test service initialization with default parameters."""
        mock_client = Mock()
        mock_qdrant_client.return_value = mock_client
        mock_client.get_collections.return_value.collections = []
        
        service = KnowledgeService()
        
        assert service.collection_name == "orchestra_knowledge"
        assert service.client == mock_client
        assert service.embedding_service == mock_embedding_service.return_value
        assert service._cache == {}
        assert service._cache_ttl == 300
        assert service._locks == {}

    @patch('src.services.knowledge_service.QdrantClient')
    @patch('src.services.knowledge_service.EmbeddingService')
    def test_initialization_with_custom_params(self, mock_embedding_service, mock_qdrant_client):
        """Test service initialization with custom parameters."""
        mock_client = Mock()
        mock_qdrant_client.return_value = mock_client
        mock_client.get_collections.return_value.collections = []
        
        custom_embedding_service = Mock()
        service = KnowledgeService(
            qdrant_host="custom-host",
            qdrant_port=9999,
            collection_name="custom_collection",
            embedding_service=custom_embedding_service
        )
        
        assert service.collection_name == "custom_collection"
        assert service.embedding_service == custom_embedding_service

    @patch('src.services.knowledge_service.QdrantClient')
    @patch('src.services.knowledge_service.EmbeddingService')
    def test_collection_initialization_existing(self, mock_embedding_service, mock_qdrant_client):
        """Test initialization when collection already exists."""
        mock_client = Mock()
        mock_qdrant_client.return_value = mock_client
        
        # Mock existing collection
        mock_collection = Mock()
        mock_collection.name = "orchestra_knowledge"
        mock_client.get_collections.return_value.collections = [mock_collection]
        
        service = KnowledgeService()
        
        # Should not create new collection
        mock_client.create_collection.assert_not_called()

    @patch('src.services.knowledge_service.QdrantClient')
    @patch('src.services.knowledge_service.EmbeddingService')
    def test_collection_initialization_new(self, mock_embedding_service, mock_qdrant_client):
        """Test initialization when creating new collection."""
        mock_client = Mock()
        mock_qdrant_client.return_value = mock_client
        mock_client.get_collections.return_value.collections = []
        
        service = KnowledgeService()
        
        # Should create new collection
        mock_client.create_collection.assert_called_once()


class TestKnowledgeServiceGrabOperation:
    """Test grab operation for atomic knowledge access."""

    @pytest.fixture
    def mock_service(self):
        """Create a mock knowledge service."""
        with patch('src.services.knowledge_service.QdrantClient'), \
             patch('src.services.knowledge_service.EmbeddingService'):
            service = KnowledgeService()
            service.client.get_collections.return_value.collections = []
            return service

    @pytest.mark.asyncio
    async def test_grab_with_cache_hit(self, mock_service):
        """Test grab operation with cache hit."""
        # Setup cached knowledge
        cached_chunk = create_test_knowledge_chunk(
            chunk_id="test-doc",
            content="Cached content"
        )
        mock_service._cache["test-doc"] = (cached_chunk, datetime.now().timestamp())
        
        # Mock lock acquisition
        mock_service._acquire_lock = AsyncMock()
        mock_service._acquire_lock.return_value = KnowledgeLock(
            document_id="test-doc",
            agent_id="test-agent",
            operation="read",
            expires_at=datetime.utcnow() + timedelta(seconds=30)
        )
        
        chunk, lock = await mock_service.grab("test-doc", "test-agent")
        
        assert chunk == cached_chunk
        assert lock is not None
        assert lock.document_id == "test-doc"

    @pytest.mark.asyncio
    async def test_grab_with_cache_miss(self, mock_service):
        """Test grab operation with cache miss."""
        # Mock lock acquisition
        mock_service._acquire_lock = AsyncMock()
        mock_service._acquire_lock.return_value = KnowledgeLock(
            document_id="test-doc",
            agent_id="test-agent",
            operation="write",
            expires_at=datetime.utcnow() + timedelta(seconds=30)
        )
        
        # Mock Qdrant fetch
        mock_service._fetch_from_qdrant = AsyncMock()
        mock_point = Mock()
        now_iso = datetime.utcnow().isoformat()
        mock_point.payload = {
            "content": "Test content",
            "metadata": {
                "document_id": "test-doc",
                "created_at": now_iso,
                "updated_at": now_iso,
                "agent_attribution": "test-agent"
            },
            "version": 1
        }
        mock_point.vector = [0.1, 0.2, 0.3]
        mock_service._fetch_from_qdrant.return_value = mock_point
        
        chunk, lock = await mock_service.grab("test-doc", "test-agent")
        
        assert chunk is not None
        assert chunk.content == "Test content"
        assert lock is not None
        assert "test-doc" in mock_service._cache

    @pytest.mark.asyncio
    async def test_grab_lock_failure(self, mock_service):
        """Test grab operation when lock acquisition fails."""
        mock_service._acquire_lock = AsyncMock()
        mock_service._acquire_lock.return_value = None
        
        chunk, lock = await mock_service.grab("test-doc", "test-agent")
        
        assert chunk is None
        assert lock is None

    @pytest.mark.asyncio
    async def test_grab_document_not_found(self, mock_service):
        """Test grab operation when document doesn't exist."""
        mock_service._acquire_lock = AsyncMock()
        mock_service._acquire_lock.return_value = KnowledgeLock(
            document_id="test-doc",
            agent_id="test-agent",
            operation="write",
            expires_at=datetime.utcnow() + timedelta(seconds=30)
        )
        
        mock_service._fetch_from_qdrant = AsyncMock()
        mock_service._fetch_from_qdrant.return_value = None
        
        mock_service._release_lock = AsyncMock()
        
        chunk, lock = await mock_service.grab("test-doc", "test-agent")
        
        assert chunk is None
        assert lock is None
        mock_service._release_lock.assert_called_once()


class TestKnowledgeServiceUpsertOperation:
    """Test upsert operation for atomic knowledge updates."""

    @pytest.fixture
    def mock_service(self):
        """Create a mock knowledge service."""
        with patch('src.services.knowledge_service.QdrantClient'), \
             patch('src.services.knowledge_service.EmbeddingService'):
            service = KnowledgeService()
            service.client.get_collections.return_value.collections = []
            return service

    @pytest.mark.asyncio
    async def test_upsert_success(self, mock_service):
        """Test successful upsert operation."""
        # Mock embedding service
        mock_service.embedding_service.generate_embedding = AsyncMock()
        mock_service.embedding_service.generate_embedding.return_value = [0.1, 0.2, 0.3]
        
        # Mock lock validation
        mock_service._validate_lock = AsyncMock()
        mock_service._validate_lock.return_value = True
        
        # Mock lock release
        mock_service._release_lock = AsyncMock()
        
        chunk = create_test_knowledge_chunk(
            chunk_id="test-doc",
            content="Test content",
            metadata_dict={"confidence_score": 0.9},
            version=2
        )
        
        lock = KnowledgeLock(
            document_id="test-doc",
            agent_id="test-agent",
            operation="write",
            expires_at=datetime.utcnow() + timedelta(seconds=30)
        )
        
        result = await mock_service.upsert(chunk, lock, "test-agent")
        
        assert result is True
        mock_service.client.upsert.assert_called_once()
        mock_service._release_lock.assert_called_once_with(lock)
        assert "test-doc" in mock_service._cache

    @pytest.mark.asyncio
    async def test_upsert_without_lock(self, mock_service):
        """Test upsert operation without lock."""
        mock_service.embedding_service.generate_embedding = AsyncMock()
        mock_service.embedding_service.generate_embedding.return_value = [0.1, 0.2, 0.3]
        
        chunk = create_test_knowledge_chunk(
            chunk_id="test-doc",
            content="Test content"
        )
        
        result = await mock_service.upsert(chunk, None, "test-agent")
        
        assert result is True
        mock_service.client.upsert.assert_called_once()

    @pytest.mark.asyncio
    async def test_upsert_invalid_lock(self, mock_service):
        """Test upsert operation with invalid lock."""
        mock_service._validate_lock = AsyncMock()
        mock_service._validate_lock.return_value = False
        
        chunk = create_test_knowledge_chunk(
            chunk_id="test-doc",
            content="Test content"
        )
        
        lock = KnowledgeLock(
            document_id="test-doc",
            agent_id="test-agent",
            operation="write",
            expires_at=datetime.utcnow() + timedelta(seconds=30)
        )
        
        result = await mock_service.upsert(chunk, lock, "test-agent")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_upsert_exception_handling(self, mock_service):
        """Test upsert operation with exception handling."""
        # Mock lock validation to pass
        mock_service._validate_lock = AsyncMock()
        mock_service._validate_lock.return_value = True
        
        mock_service.embedding_service.generate_embedding = AsyncMock()
        mock_service.embedding_service.generate_embedding.side_effect = Exception("Embedding failed")
        
        mock_service._release_lock = AsyncMock()
        
        chunk = create_test_knowledge_chunk(
            chunk_id="test-doc",
            content="Test content"
        )
        
        lock = KnowledgeLock(
            document_id="test-doc",
            agent_id="test-agent",
            operation="write",
            expires_at=datetime.utcnow() + timedelta(seconds=30)
        )
        
        result = await mock_service.upsert(chunk, lock, "test-agent")
        
        assert result is False
        mock_service._release_lock.assert_called_once_with(lock)


class TestKnowledgeServiceQueryOperation:
    """Test query operation for semantic search."""

    @pytest.fixture
    def mock_service(self):
        """Create a mock knowledge service."""
        with patch('src.services.knowledge_service.QdrantClient'), \
             patch('src.services.knowledge_service.EmbeddingService'):
            service = KnowledgeService()
            service.client.get_collections.return_value.collections = []
            return service

    @pytest.mark.asyncio
    async def test_query_basic(self, mock_service):
        """Test basic query operation."""
        # Mock embedding service
        mock_service.embedding_service.generate_embedding = AsyncMock()
        mock_service.embedding_service.generate_embedding.return_value = [0.1, 0.2, 0.3]
        
        # Mock Qdrant search results
        mock_result = Mock()
        mock_result.payload = {
            "content": "Test content",
            "metadata": {"document_id": "test-doc", "confidence_score": 0.9},
            "version": 1
        }
        mock_result.vector = [0.1, 0.2, 0.3]
        mock_service.client.search.return_value = [mock_result]
        
        query = KnowledgeQuery(
            query_text="test query",
            max_results=10
        )
        
        results = await mock_service.query(query)
        
        assert len(results) == 1
        assert results[0].content == "Test content"
        mock_service.client.search.assert_called_once()

    @pytest.mark.asyncio
    async def test_query_with_filters(self, mock_service):
        """Test query operation with filters."""
        mock_service.embedding_service.generate_embedding = AsyncMock()
        mock_service.embedding_service.generate_embedding.return_value = [0.1, 0.2, 0.3]
        
        mock_service.client.search.return_value = []
        
        query = KnowledgeQuery(
            query_text="test query",
            knowledge_domains=[KnowledgeDomain.TECHNICAL],
            agent_id="test-agent",
            min_confidence=0.8,
            max_results=5
        )
        
        results = await mock_service.query(query)
        
        assert len(results) == 0
        # Verify filter was applied
        call_args = mock_service.client.search.call_args
        assert call_args[1]['query_filter'] is not None

    @pytest.mark.asyncio
    async def test_query_exception_handling(self, mock_service):
        """Test query operation with exception handling."""
        mock_service.embedding_service.generate_embedding = AsyncMock()
        mock_service.embedding_service.generate_embedding.side_effect = Exception("Query failed")
        
        query = KnowledgeQuery(query_text="test query")
        
        with pytest.raises(Exception):
            await mock_service.query(query)


class TestKnowledgeServiceLocking:
    """Test distributed locking functionality."""

    @pytest.fixture
    def mock_service(self):
        """Create a mock knowledge service."""
        with patch('src.services.knowledge_service.QdrantClient'), \
             patch('src.services.knowledge_service.EmbeddingService'):
            service = KnowledgeService()
            service.client.get_collections.return_value.collections = []
            return service

    @pytest.mark.asyncio
    async def test_acquire_lock_success(self, mock_service):
        """Test successful lock acquisition."""
        lock = await mock_service._acquire_lock("test-doc", "test-agent", "write", 30)
        
        assert lock is not None
        assert lock.document_id == "test-doc"
        assert lock.agent_id == "test-agent"
        assert lock.operation == "write"
        assert lock.expires_at > datetime.utcnow()
        assert "test-doc" in mock_service._locks

    @pytest.mark.asyncio
    async def test_acquire_lock_already_locked(self, mock_service):
        """Test lock acquisition when document is already locked."""
        # Create existing lock
        existing_lock = KnowledgeLock(
            document_id="test-doc",
            agent_id="other-agent",
            operation="write",
            expires_at=datetime.utcnow() + timedelta(seconds=60)
        )
        mock_service._locks["test-doc"] = existing_lock
        
        lock = await mock_service._acquire_lock("test-doc", "test-agent", "write", 30)
        
        assert lock is None

    @pytest.mark.asyncio
    async def test_acquire_lock_expired(self, mock_service):
        """Test lock acquisition when existing lock is expired."""
        # Create expired lock
        expired_lock = KnowledgeLock(
            document_id="test-doc",
            agent_id="other-agent",
            operation="write",
            expires_at=datetime.utcnow() - timedelta(seconds=10)
        )
        mock_service._locks["test-doc"] = expired_lock
        
        lock = await mock_service._acquire_lock("test-doc", "test-agent", "write", 30)
        
        assert lock is not None
        assert lock.agent_id == "test-agent"

    @pytest.mark.asyncio
    async def test_release_lock(self, mock_service):
        """Test lock release."""
        lock = KnowledgeLock(
            document_id="test-doc",
            agent_id="test-agent",
            operation="write",
            expires_at=datetime.utcnow() + timedelta(seconds=30)
        )
        mock_service._locks["test-doc"] = lock
        
        await mock_service._release_lock(lock)
        
        assert "test-doc" not in mock_service._locks
        assert lock.released is True

    @pytest.mark.asyncio
    async def test_validate_lock_valid(self, mock_service):
        """Test lock validation with valid lock."""
        lock = KnowledgeLock(
            document_id="test-doc",
            agent_id="test-agent",
            operation="write",
            expires_at=datetime.utcnow() + timedelta(seconds=30)
        )
        mock_service._locks["test-doc"] = lock
        
        is_valid = await mock_service._validate_lock(lock)
        
        assert is_valid is True

    @pytest.mark.asyncio
    async def test_validate_lock_released(self, mock_service):
        """Test lock validation with released lock."""
        lock = KnowledgeLock(
            document_id="test-doc",
            agent_id="test-agent",
            operation="write",
            expires_at=datetime.utcnow() + timedelta(seconds=30)
        )
        lock.released = True
        
        is_valid = await mock_service._validate_lock(lock)
        
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_validate_lock_expired(self, mock_service):
        """Test lock validation with expired lock."""
        lock = KnowledgeLock(
            document_id="test-doc",
            agent_id="test-agent",
            operation="write",
            expires_at=datetime.utcnow() - timedelta(seconds=10)
        )
        mock_service._locks["test-doc"] = lock
        
        is_valid = await mock_service._validate_lock(lock)
        
        assert is_valid is False


class TestKnowledgeServiceVersioning:
    """Test versioning functionality."""

    @pytest.fixture
    def mock_service(self):
        """Create a mock knowledge service."""
        with patch('src.services.knowledge_service.QdrantClient'), \
             patch('src.services.knowledge_service.EmbeddingService'):
            service = KnowledgeService()
            service.client.get_collections.return_value.collections = []
            return service

    @pytest.mark.asyncio
    async def test_get_version_history(self, mock_service):
        """Test getting version history."""
        # Mock Qdrant fetch
        mock_service._fetch_from_qdrant = AsyncMock()
        mock_point = Mock()
        now_iso = datetime.utcnow().isoformat()
        mock_point.payload = {
            "content": "Test content",
            "metadata": {
                "document_id": "test-doc",
                "agent_attribution": "test-agent",
                "created_at": now_iso,
                "updated_at": now_iso
            },
            "version": 2
        }
        mock_point.vector = [0.1, 0.2, 0.3]
        mock_service._fetch_from_qdrant.return_value = mock_point
        
        versions = await mock_service.get_version_history("test-doc", limit=5)
        
        assert len(versions) == 1
        assert versions[0].document_id == "test-doc"
        assert versions[0].version == 2
        assert versions[0].content == "Test content"
        assert versions[0].agent_attribution == "test-agent"

    @pytest.mark.asyncio
    async def test_get_version_history_not_found(self, mock_service):
        """Test getting version history for non-existent document."""
        mock_service._fetch_from_qdrant = AsyncMock()
        mock_service._fetch_from_qdrant.return_value = None
        
        versions = await mock_service.get_version_history("test-doc")
        
        assert len(versions) == 0


class TestKnowledgeServicePerformance:
    """Test performance requirements from PRD."""

    @pytest.fixture
    def mock_service(self):
        """Create a mock knowledge service."""
        with patch('src.services.knowledge_service.QdrantClient'), \
             patch('src.services.knowledge_service.EmbeddingService'):
            service = KnowledgeService()
            service.client.get_collections.return_value.collections = []
            return service

    @pytest.mark.asyncio
    async def test_upsert_performance_requirement(self, mock_service):
        """Test that upsert completes within 1 second (NFR10)."""
        import time
        
        # Mock all dependencies
        mock_service.embedding_service.generate_embedding = AsyncMock()
        mock_service.embedding_service.generate_embedding.return_value = [0.1, 0.2, 0.3]
        
        chunk = create_test_knowledge_chunk(
            chunk_id="test-doc",
            content="Test content"
        )
        
        start_time = time.time()
        result = await mock_service.upsert(chunk, None, "test-agent")
        end_time = time.time()
        
        assert result is True
        assert end_time - start_time < 1.0  # NFR10 requirement

    @pytest.mark.asyncio
    async def test_query_performance_requirement(self, mock_service):
        """Test that query completes within 500ms (NFR9)."""
        import time
        
        mock_service.embedding_service.generate_embedding = AsyncMock()
        mock_service.embedding_service.generate_embedding.return_value = [0.1, 0.2, 0.3]
        mock_service.client.search.return_value = []
        
        query = KnowledgeQuery(query_text="test query")
        
        start_time = time.time()
        results = await mock_service.query(query)
        end_time = time.time()
        
        assert len(results) == 0
        assert end_time - start_time < 0.5  # NFR9 requirement


class TestKnowledgeServiceIntegration:
    """Test integration scenarios."""

    @pytest.fixture
    def mock_service(self):
        """Create a mock knowledge service."""
        with patch('src.services.knowledge_service.QdrantClient'), \
             patch('src.services.knowledge_service.EmbeddingService'):
            service = KnowledgeService()
            service.client.get_collections.return_value.collections = []
            return service

    @pytest.mark.asyncio
    async def test_grab_edit_upsert_workflow(self, mock_service):
        """Test complete grab-edit-upsert workflow."""
        # Mock dependencies
        mock_service.embedding_service.generate_embedding = AsyncMock()
        mock_service.embedding_service.generate_embedding.return_value = [0.1, 0.2, 0.3]
        
        # 1. Grab knowledge
        mock_service._acquire_lock = AsyncMock()
        mock_service._acquire_lock.return_value = KnowledgeLock(
            document_id="test-doc",
            agent_id="brendan",
            operation="write",
            expires_at=datetime.utcnow() + timedelta(seconds=30)
        )
        
        mock_service._fetch_from_qdrant = AsyncMock()
        mock_point = Mock()
        now_iso = datetime.utcnow().isoformat()
        mock_point.payload = {
            "content": "Original content",
            "metadata": {
                "document_id": "test-doc",
                "created_at": now_iso,
                "updated_at": now_iso,
                "agent_attribution": "brendan"
            },
            "version": 1
        }
        mock_point.vector = [0.1, 0.2, 0.3]
        mock_service._fetch_from_qdrant.return_value = mock_point
        
        chunk, lock = await mock_service.grab("test-doc", "brendan")
        assert chunk is not None
        assert lock is not None
        
        # 2. Edit knowledge
        chunk.content = "Updated content"
        chunk.version = 2
        
        # 3. Upsert knowledge
        mock_service._validate_lock = AsyncMock()
        mock_service._validate_lock.return_value = True
        mock_service._release_lock = AsyncMock()
        
        result = await mock_service.upsert(chunk, lock, "brendan")
        assert result is True

    @pytest.mark.asyncio
    async def test_concurrent_access_handling(self, mock_service):
        """Test handling of concurrent access (FR12)."""
        # Mock the fetch method to return proper data
        mock_service._fetch_from_qdrant = AsyncMock()
        mock_point = Mock()
        now_iso = datetime.utcnow().isoformat()
        mock_point.payload = {
            "content": "Test content",
            "metadata": {
                "document_id": "test-doc",
                "created_at": now_iso,
                "updated_at": now_iso,
                "agent_attribution": "brendan"
            },
            "version": 1
        }
        mock_point.vector = [0.1, 0.2, 0.3]
        mock_service._fetch_from_qdrant.return_value = mock_point
        
        # Simulate two agents trying to grab the same document
        mock_service._acquire_lock = AsyncMock()
        
        # First agent gets the lock
        mock_service._acquire_lock.return_value = KnowledgeLock(
            document_id="test-doc",
            agent_id="brendan",
            operation="write",
            expires_at=datetime.utcnow() + timedelta(seconds=30)
        )
        
        chunk1, lock1 = await mock_service.grab("test-doc", "brendan")
        assert chunk1 is not None
        assert lock1 is not None
        
        # Clear cache to avoid cache hit on second grab
        mock_service.clear_cache()
        
        # Second agent should fail to get lock
        mock_service._acquire_lock.return_value = None
        
        chunk2, lock2 = await mock_service.grab("test-doc", "developer")
        assert chunk2 is None
        assert lock2 is None

    def test_cache_management(self, mock_service):
        """Test cache management functionality."""
        # Add items to cache
        chunk1 = create_test_knowledge_chunk(chunk_id="doc1", content="Content 1")
        chunk2 = create_test_knowledge_chunk(chunk_id="doc2", content="Content 2")
        
        mock_service._cache["doc1"] = (chunk1, time.time())
        mock_service._cache["doc2"] = (chunk2, time.time())
        
        assert len(mock_service._cache) == 2


class TestKnowledgeServiceErrorHandling:
    """Test error handling and exception scenarios for missing coverage."""

    @patch('src.services.knowledge_service.QdrantClient')
    @patch('src.services.knowledge_service.EmbeddingService') 
    def test_collection_initialization_exception(self, mock_embedding_service, mock_qdrant_client):
        """Test collection initialization with exception - covers lines 97-99."""
        mock_client = Mock()
        mock_qdrant_client.return_value = mock_client
        
        # Make get_collections raise an exception
        mock_client.get_collections.side_effect = Exception("Qdrant connection failed")
        
        with pytest.raises(Exception, match="Qdrant connection failed"):
            KnowledgeService()

    @pytest.fixture
    def error_test_service(self):
        """Create service for error testing."""
        with patch('src.services.knowledge_service.QdrantClient'), \
             patch('src.services.knowledge_service.EmbeddingService'):
            service = KnowledgeService()
            service.client.get_collections.return_value.collections = []
            return service

    @pytest.mark.asyncio
    async def test_grab_with_fetch_exception(self, error_test_service):
        """Test grab operation with Qdrant fetch exception - covers lines 148-151."""
        # Mock lock acquisition to succeed
        mock_lock = KnowledgeLock(
            document_id="test-doc",
            agent_id="test-agent", 
            operation="write",
            expires_at=datetime.utcnow() + timedelta(minutes=5),
            lock_id="test-lock"
        )
        error_test_service._acquire_lock = AsyncMock(return_value=mock_lock)
        error_test_service._fetch_from_qdrant = AsyncMock(side_effect=Exception("Qdrant fetch failed"))
        error_test_service._release_lock = AsyncMock()
        
        with pytest.raises(Exception, match="Qdrant fetch failed"):
            await error_test_service.grab("test-doc", "test-agent")
            
        # Verify lock was released
        error_test_service._release_lock.assert_called_once_with(mock_lock)

    @pytest.mark.asyncio  
    async def test_fetch_from_qdrant_exception(self, error_test_service):
        """Test _fetch_from_qdrant with exception - covers lines 386-394."""
        # Make client.retrieve raise exception
        error_test_service.client.retrieve.side_effect = Exception("Qdrant retrieve failed")
        
        result = await error_test_service._fetch_from_qdrant("test-doc")
        assert result is None

    @pytest.mark.asyncio
    async def test_validate_lock_edge_cases(self, error_test_service):
        """Test lock validation edge cases - covers line 381."""
        # Test with missing document in locks
        lock = KnowledgeLock(
            document_id="missing-doc",
            agent_id="test-agent",
            operation="write", 
            expires_at=datetime.utcnow() + timedelta(minutes=5),
            lock_id="test-lock"
        )
        
        # Document not in _locks dict - should return False
        result = await error_test_service._validate_lock(lock)
        assert result is False


class TestKnowledgeServicePerformanceWarnings:
    """Test performance warning scenarios for missing coverage."""

    @pytest.fixture
    def perf_test_service(self):
        """Create service for performance testing."""
        with patch('src.services.knowledge_service.QdrantClient'), \
             patch('src.services.knowledge_service.EmbeddingService'):
            service = KnowledgeService()
            service.client.get_collections.return_value.collections = []
            return service

    @pytest.mark.asyncio
    async def test_slow_upsert_warning(self, perf_test_service):
        """Test slow upsert operation warning - covers line 221.""" 
        chunk = create_test_knowledge_chunk()
        
        # Mock embedding service to return quickly
        perf_test_service.embedding_service.generate_embedding = AsyncMock(return_value=[0.1, 0.2, 0.3])
        
        # Mock time.time to simulate slow operation
        original_time = time.time
        call_count = 0
        def mock_time():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return original_time()  # Start time
            else:
                return original_time() + 2.0  # End time (2 seconds later, > 1s threshold)
        
        with patch('time.time', side_effect=mock_time):
            with patch('src.services.knowledge_service.logger') as mock_logger:
                result = await perf_test_service.upsert(chunk)
                
                assert result is True
                mock_logger.warning.assert_called_once()
                args = mock_logger.warning.call_args[0] 
                assert "Slow upsert operation" in args[0]

    @pytest.mark.asyncio
    async def test_slow_query_warning(self, perf_test_service):
        """Test slow query operation warning - covers line 301."""
        query = KnowledgeQuery(
            query_text="test query",
            max_results=5,
            knowledge_domains=[]
        )
        
        # Mock embedding generation
        perf_test_service.embedding_service.generate_embedding = AsyncMock(return_value=[0.1, 0.2, 0.3])
        
        # Mock Qdrant search to return results
        mock_result = Mock()
        mock_result.id = "test-doc"
        mock_result.score = 0.9
        mock_result.payload = {
            "content": "Test content",
            "metadata": {
                "document_id": "test-doc",
                "version": 1,
                "agent_attribution": "test",
                "updated_at": datetime.utcnow().isoformat(),
                "created_at": datetime.utcnow().isoformat(),
                "confidence_score": 0.9,
                "knowledge_domain": "technical"
            },
            "version": 1
        }
        perf_test_service.client.search.return_value = [mock_result]
        
        # Mock time.time to simulate slow operation  
        original_time = time.time
        call_count = 0
        def mock_time():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return original_time()  # Start time
            else:
                return original_time() + 0.8  # End time (0.8 seconds later, > 0.5s threshold)
        
        with patch('time.time', side_effect=mock_time):
            with patch('src.services.knowledge_service.logger') as mock_logger:
                result = await perf_test_service.query(query)
                
                assert len(result) == 1
                mock_logger.warning.assert_called_once()
                args = mock_logger.warning.call_args[0]
                assert "Slow query operation" in args[0]