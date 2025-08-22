"""Tests for EmbeddingService."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.embedding_service import EmbeddingService


@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client."""
    client = MagicMock()
    client.embeddings = MagicMock()
    client.embeddings.create = AsyncMock()
    return client


@pytest.fixture
def embedding_service(mock_openai_client):
    """Create an EmbeddingService instance with mocked client."""
    with patch(
        "src.services.embedding_service.AsyncOpenAI", return_value=mock_openai_client
    ):
        service = EmbeddingService()
        service.client = mock_openai_client
        return service


class TestEmbeddingService:
    """Test EmbeddingService functionality."""

    @pytest.mark.asyncio
    async def test_generate_embedding_success(
        self, embedding_service, mock_openai_client
    ):
        """Test successful embedding generation."""
        # Mock the response
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1, 0.2, 0.3])]
        mock_openai_client.embeddings.create.return_value = mock_response

        # Generate embedding
        result = await embedding_service.generate_embedding("test text")

        # Verify
        assert result == [0.1, 0.2, 0.3]
        mock_openai_client.embeddings.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_embedding_with_cache(
        self, embedding_service, mock_openai_client
    ):
        """Test embedding generation with caching."""
        # Mock the response
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1, 0.2, 0.3])]
        mock_openai_client.embeddings.create.return_value = mock_response

        # Generate embedding twice
        result1 = await embedding_service.generate_embedding("test text")
        result2 = await embedding_service.generate_embedding("test text")

        # Should use cache for second call
        assert result1 == result2
        mock_openai_client.embeddings.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_embeddings_batch(
        self, embedding_service, mock_openai_client
    ):
        """Test batch embedding generation."""
        # Mock the response
        mock_response = MagicMock()
        mock_response.data = [
            MagicMock(embedding=[0.1, 0.2, 0.3]),
            MagicMock(embedding=[0.4, 0.5, 0.6]),
        ]
        mock_openai_client.embeddings.create.return_value = mock_response

        # Generate embeddings
        texts = ["text1", "text2"]
        results = await embedding_service.generate_embeddings_batch(texts)

        # Verify
        assert len(results) == 2
        assert results[0] == [0.1, 0.2, 0.3]
        assert results[1] == [0.4, 0.5, 0.6]

    @pytest.mark.asyncio
    async def test_generate_embedding_empty_text(self, embedding_service):
        """Test embedding generation with empty text."""
        result = await embedding_service.generate_embedding("")
        assert result == []

    @pytest.mark.asyncio
    async def test_generate_embedding_error_handling(
        self, embedding_service, mock_openai_client
    ):
        """Test error handling in embedding generation."""
        # Mock an error
        mock_openai_client.embeddings.create.side_effect = Exception("API error")

        # Should raise the exception
        with pytest.raises(Exception, match="API error"):
            await embedding_service.generate_embedding("test text")

    def test_cache_stats(self, embedding_service):
        """Test cache statistics."""
        stats = embedding_service.get_cache_stats()
        assert "size" in stats
        assert "hits" in stats
        assert "misses" in stats

    def test_clear_cache(self, embedding_service):
        """Test cache clearing."""
        embedding_service.clear_cache()
        stats = embedding_service.get_cache_stats()
        assert stats["size"] == 0

    @pytest.mark.asyncio
    async def test_warmup_cache(self, embedding_service, mock_openai_client):
        """Test cache warmup."""
        # Mock the response
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1, 0.2, 0.3])]
        mock_openai_client.embeddings.create.return_value = mock_response

        # Warmup cache
        texts = ["warmup1", "warmup2"]
        await embedding_service.warmup_cache(texts)

        # Verify embeddings were generated
        assert mock_openai_client.embeddings.create.call_count >= 1

    def test_hash_text(self, embedding_service):
        """Test text hashing for cache keys."""
        # Access the private method for testing
        hash1 = embedding_service._hash_text("test")
        hash2 = embedding_service._hash_text("test")
        hash3 = embedding_service._hash_text("different")

        assert hash1 == hash2
        assert hash1 != hash3
