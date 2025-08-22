"""Tests for KnowledgeService."""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.models.knowledge import (
    KnowledgeDomain,
    KnowledgeMetadata,
    KnowledgeQuery,
    KnowledgeUpdate,
    SecurityClassification,
)
from src.services.knowledge_service import KnowledgeService


@pytest.fixture
def mock_qdrant_client():
    """Create a mock Qdrant client."""
    client = AsyncMock()
    client.get_collections = AsyncMock(return_value=MagicMock(collections=[]))
    client.create_collection = AsyncMock()
    client.retrieve = AsyncMock()
    client.upsert = AsyncMock()
    client.search = AsyncMock()
    return client


@pytest.fixture
def mock_embedding_service():
    """Create a mock EmbeddingService."""
    service = AsyncMock()
    service.generate_embedding = AsyncMock(return_value=[0.1, 0.2, 0.3])
    return service


@pytest.fixture
def knowledge_service(mock_qdrant_client, mock_embedding_service):
    """Create a KnowledgeService instance with mocked dependencies."""
    with patch(
        "src.services.knowledge_service.QdrantClient", return_value=mock_qdrant_client
    ):
        with patch(
            "src.services.knowledge_service.EmbeddingService",
            return_value=mock_embedding_service,
        ):
            service = KnowledgeService()
            service.client = mock_qdrant_client
            service.embedding_service = mock_embedding_service
            return service


class TestKnowledgeService:
    """Test KnowledgeService functionality."""

    @pytest.mark.asyncio
    async def test_grab_existing_chunk(self, knowledge_service, mock_qdrant_client):
        """Test grabbing an existing knowledge chunk."""
        chunk_id = str(uuid.uuid4())

        # Mock Qdrant response
        mock_point = MagicMock()
        mock_point.id = chunk_id
        mock_point.payload = {
            "content": "test content",
            "domain": "general",
            "security_classification": "public",
            "tags": ["test"],
            "source": "test",
            "confidence": 0.9,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "version": 1,
            "author": "test_user",
        }
        mock_point.vector = [0.1, 0.2, 0.3]
        mock_qdrant_client.retrieve.return_value = [mock_point]

        # Grab chunk
        chunk, lock_token = await knowledge_service.grab(chunk_id)

        # Verify
        assert chunk is not None
        assert chunk.id == chunk_id
        assert chunk.content == "test content"
        assert lock_token is not None

    @pytest.mark.asyncio
    async def test_grab_non_existent_chunk(self, knowledge_service, mock_qdrant_client):
        """Test grabbing a non-existent chunk."""
        chunk_id = str(uuid.uuid4())

        # Mock empty response
        mock_qdrant_client.retrieve.return_value = []

        # Grab chunk
        chunk, lock_token = await knowledge_service.grab(chunk_id)

        # Verify
        assert chunk is None
        assert lock_token is None

    @pytest.mark.asyncio
    async def test_upsert_new_chunk(
        self, knowledge_service, mock_qdrant_client, mock_embedding_service
    ):
        """Test upserting a new knowledge chunk."""
        # Create update
        update = KnowledgeUpdate(
            content="new content",
            metadata=KnowledgeMetadata(
                domain=KnowledgeDomain.GENERAL,
                tags=["new"],
                source="test",
                confidence=0.95,
                security_classification=SecurityClassification.PUBLIC,
            ),
            author="test_user",
        )

        # Mock embedding
        mock_embedding_service.generate_embedding.return_value = [0.4, 0.5, 0.6]

        # Upsert
        chunk = await knowledge_service.upsert(update, lock_token="test_token")

        # Verify
        assert chunk is not None
        assert chunk.content == "new content"
        assert chunk.metadata.confidence == 0.95
        mock_qdrant_client.upsert.assert_called_once()

    @pytest.mark.asyncio
    async def test_upsert_existing_chunk(self, knowledge_service, mock_qdrant_client):
        """Test upserting an existing chunk with lock."""
        chunk_id = str(uuid.uuid4())

        # Create update
        update = KnowledgeUpdate(
            id=chunk_id,
            content="updated content",
            metadata=KnowledgeMetadata(
                domain=KnowledgeDomain.GENERAL,
                tags=["updated"],
                source="test",
                confidence=0.98,
                security_classification=SecurityClassification.PUBLIC,
            ),
            author="test_user",
        )

        # Upsert with lock
        chunk = await knowledge_service.upsert(update, lock_token="valid_token")

        # Verify
        assert chunk is not None
        assert chunk.content == "updated content"
        mock_qdrant_client.upsert.assert_called_once()

    @pytest.mark.asyncio
    async def test_query_knowledge(
        self, knowledge_service, mock_qdrant_client, mock_embedding_service
    ):
        """Test querying knowledge base."""
        # Create query
        query = KnowledgeQuery(
            query="test query",
            domain=KnowledgeDomain.GENERAL,
            limit=5,
        )

        # Mock search results
        mock_result = MagicMock()
        mock_result.id = str(uuid.uuid4())
        mock_result.score = 0.95
        mock_result.payload = {
            "content": "result content",
            "domain": "general",
            "security_classification": "public",
            "tags": ["result"],
            "source": "test",
            "confidence": 0.9,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "version": 1,
            "author": "test_user",
        }
        mock_qdrant_client.search.return_value = [mock_result]

        # Query
        results = await knowledge_service.query(query)

        # Verify
        assert len(results) == 1
        assert results[0].content == "result content"
        mock_embedding_service.generate_embedding.assert_called_once_with("test query")

    @pytest.mark.asyncio
    async def test_get_version_history(self, knowledge_service):
        """Test getting version history."""
        chunk_id = str(uuid.uuid4())

        # Get history
        history = await knowledge_service.get_version_history(chunk_id)

        # Verify (should return empty list for now)
        assert isinstance(history, list)

    def test_acquire_lock(self, knowledge_service):
        """Test acquiring a lock."""
        chunk_id = str(uuid.uuid4())

        # Acquire lock
        token = knowledge_service._acquire_lock(chunk_id)

        # Verify
        assert token is not None
        assert chunk_id in knowledge_service.locks

    def test_release_lock(self, knowledge_service):
        """Test releasing a lock."""
        chunk_id = str(uuid.uuid4())

        # Acquire and release lock
        token = knowledge_service._acquire_lock(chunk_id)
        released = knowledge_service._release_lock(chunk_id, token)

        # Verify
        assert released is True
        assert chunk_id not in knowledge_service.locks

    def test_validate_lock(self, knowledge_service):
        """Test validating a lock."""
        chunk_id = str(uuid.uuid4())

        # Acquire lock
        token = knowledge_service._acquire_lock(chunk_id)

        # Validate with correct token
        valid = knowledge_service._validate_lock(chunk_id, token)
        assert valid is True

        # Validate with wrong token
        invalid = knowledge_service._validate_lock(chunk_id, "wrong_token")
        assert invalid is False

    def test_clear_cache(self, knowledge_service):
        """Test clearing the cache."""
        knowledge_service.clear_cache()
        assert len(knowledge_service.cache) == 0
