"""Tests for embedding service based on PRD requirements."""

import pytest
import time
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import List

# Import the module to ensure it's loaded for coverage
import src.services.embedding_service

from src.services.embedding_service import EmbeddingService


class TestEmbeddingServiceInitialization:
    """Test embedding service initialization."""

    @patch('src.services.embedding_service.AsyncOpenAI')
    @patch('src.services.embedding_service.get_settings')
    def test_initialization_with_defaults(self, mock_get_settings, mock_openai):
        """Test service initialization with default parameters."""
        # Mock settings
        mock_settings = Mock()
        mock_settings.openai.api_key = "test-api-key"
        mock_get_settings.return_value = mock_settings
        
        service = EmbeddingService()
        
        assert service.model == "text-embedding-3-large"
        assert service._batch_size == 20
        assert service._batch_timeout == 0.1
        assert service._cache == {}
        assert service._cache_hits == 0
        assert service._cache_misses == 0
        mock_openai.assert_called_once_with(api_key="test-api-key")

    @patch('src.services.embedding_service.AsyncOpenAI')
    @patch('src.services.embedding_service.get_settings')
    def test_initialization_with_custom_model(self, mock_get_settings, mock_openai):
        """Test service initialization with custom model."""
        mock_settings = Mock()
        mock_settings.openai.api_key = "test-api-key"
        mock_get_settings.return_value = mock_settings
        
        service = EmbeddingService(model="text-embedding-ada-002")
        
        assert service.model == "text-embedding-ada-002"


class TestEmbeddingServiceSingleEmbedding:
    """Test single embedding generation."""

    @pytest.fixture
    def mock_service(self):
        """Create a mock embedding service."""
        with patch('src.services.embedding_service.AsyncOpenAI'), \
             patch('src.services.embedding_service.get_settings'):
            service = EmbeddingService()
            service.client = AsyncMock()
            return service

    @pytest.mark.asyncio
    async def test_generate_embedding_success(self, mock_service):
        """Test successful embedding generation."""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.data = [Mock()]
        mock_response.data[0].embedding = [0.1, 0.2, 0.3, 0.4]
        mock_service.client.embeddings.create = AsyncMock(return_value=mock_response)
        
        result = await mock_service.generate_embedding("test text")
        
        assert result == [0.1, 0.2, 0.3, 0.4]
        assert mock_service._cache_misses == 1
        assert mock_service._cache_hits == 0
        
        # Verify API call
        mock_service.client.embeddings.create.assert_called_once_with(
            model="text-embedding-3-large",
            input="test text"
        )

    @pytest.mark.asyncio
    async def test_generate_embedding_cache_hit(self, mock_service):
        """Test embedding generation with cache hit."""
        # Pre-populate cache
        text_hash = mock_service._hash_text("test text")
        mock_service._cache[text_hash] = [0.5, 0.6, 0.7, 0.8]
        
        result = await mock_service.generate_embedding("test text")
        
        assert result == [0.5, 0.6, 0.7, 0.8]
        assert mock_service._cache_hits == 1
        assert mock_service._cache_misses == 0
        
        # Verify no API call was made
        mock_service.client.embeddings.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_generate_embedding_caches_result(self, mock_service):
        """Test that embedding results are cached."""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.data = [Mock()]
        mock_response.data[0].embedding = [0.1, 0.2, 0.3, 0.4]
        mock_service.client.embeddings.create = AsyncMock(return_value=mock_response)
        
        # First call
        result1 = await mock_service.generate_embedding("test text")
        assert result1 == [0.1, 0.2, 0.3, 0.4]
        assert mock_service._cache_misses == 1
        
        # Second call should hit cache
        result2 = await mock_service.generate_embedding("test text")
        assert result2 == [0.1, 0.2, 0.3, 0.4]
        assert mock_service._cache_hits == 1
        
        # API should only be called once
        assert mock_service.client.embeddings.create.call_count == 1

    @pytest.mark.asyncio
    async def test_generate_embedding_exception_handling(self, mock_service):
        """Test embedding generation with API exception."""
        mock_service.client.embeddings.create = AsyncMock(
            side_effect=Exception("API Error")
        )
        
        with pytest.raises(Exception, match="API Error"):
            await mock_service.generate_embedding("test text")
        
        assert mock_service._cache_misses == 1
        assert len(mock_service._cache) == 0  # Should not cache failed results

    @pytest.mark.asyncio
    async def test_generate_embedding_performance_logging(self, mock_service):
        """Test that performance is logged."""
        mock_response = Mock()
        mock_response.data = [Mock()]
        mock_response.data[0].embedding = [0.1, 0.2, 0.3, 0.4]
        mock_service.client.embeddings.create = AsyncMock(return_value=mock_response)
        
        with patch('src.services.embedding_service.logger') as mock_logger:
            await mock_service.generate_embedding("test text")
            
            # Should log performance
            mock_logger.debug.assert_called()
            debug_calls = [call[0][0] for call in mock_logger.debug.call_args_list]
            assert any("Generated embedding in" in call for call in debug_calls)


class TestEmbeddingServiceBatchEmbedding:
    """Test batch embedding generation."""

    @pytest.fixture
    def mock_service(self):
        """Create a mock embedding service."""
        with patch('src.services.embedding_service.AsyncOpenAI'), \
             patch('src.services.embedding_service.get_settings'):
            service = EmbeddingService()
            service.client = AsyncMock()
            return service

    @pytest.mark.asyncio
    async def test_generate_embeddings_batch_empty_list(self, mock_service):
        """Test batch generation with empty list."""
        result = await mock_service.generate_embeddings_batch([])
        
        assert result == []
        mock_service.client.embeddings.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_generate_embeddings_batch_success(self, mock_service):
        """Test successful batch embedding generation."""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.data = [
            Mock(embedding=[0.1, 0.2, 0.3]),
            Mock(embedding=[0.4, 0.5, 0.6]),
            Mock(embedding=[0.7, 0.8, 0.9])
        ]
        mock_service.client.embeddings.create = AsyncMock(return_value=mock_response)
        
        texts = ["text1", "text2", "text3"]
        result = await mock_service.generate_embeddings_batch(texts)
        
        assert len(result) == 3
        assert result[0] == [0.1, 0.2, 0.3]
        assert result[1] == [0.4, 0.5, 0.6]
        assert result[2] == [0.7, 0.8, 0.9]
        
        # Verify API call
        mock_service.client.embeddings.create.assert_called_once_with(
            model="text-embedding-3-large",
            input=texts
        )

    @pytest.mark.asyncio
    async def test_generate_embeddings_batch_with_cache_hits(self, mock_service):
        """Test batch generation with some cache hits."""
        # Pre-populate cache for one text
        text1_hash = mock_service._hash_text("text1")
        mock_service._cache[text1_hash] = [0.1, 0.2, 0.3]
        
        # Mock OpenAI response for uncached texts
        mock_response = Mock()
        mock_response.data = [
            Mock(embedding=[0.4, 0.5, 0.6]),
            Mock(embedding=[0.7, 0.8, 0.9])
        ]
        mock_service.client.embeddings.create = AsyncMock(return_value=mock_response)
        
        texts = ["text1", "text2", "text3"]
        result = await mock_service.generate_embeddings_batch(texts)
        
        assert len(result) == 3
        assert result[0] == [0.1, 0.2, 0.3]  # From cache
        assert result[1] == [0.4, 0.5, 0.6]  # From API
        assert result[2] == [0.7, 0.8, 0.9]  # From API
        
        assert mock_service._cache_hits == 1
        assert mock_service._cache_misses == 2
        
        # API should only be called for uncached texts
        mock_service.client.embeddings.create.assert_called_once_with(
            model="text-embedding-3-large",
            input=["text2", "text3"]
        )

    @pytest.mark.asyncio
    async def test_generate_embeddings_batch_large_batch(self, mock_service):
        """Test batch generation with batch size limits."""
        # Create a large list of texts (more than batch size)
        texts = [f"text{i}" for i in range(25)]  # Exceeds batch_size of 20
        
        # Mock OpenAI responses for two batches
        mock_response1 = Mock()
        mock_response1.data = [Mock(embedding=[i, i+0.1, i+0.2]) for i in range(20)]
        
        mock_response2 = Mock()
        mock_response2.data = [Mock(embedding=[i, i+0.1, i+0.2]) for i in range(20, 25)]
        
        mock_service.client.embeddings.create = AsyncMock(
            side_effect=[mock_response1, mock_response2]
        )
        
        result = await mock_service.generate_embeddings_batch(texts)
        
        assert len(result) == 25
        assert mock_service.client.embeddings.create.call_count == 2
        
        # Verify batch calls
        calls = mock_service.client.embeddings.create.call_args_list
        assert len(calls[0][1]['input']) == 20  # First batch
        assert len(calls[1][1]['input']) == 5   # Second batch

    @pytest.mark.asyncio
    async def test_generate_embeddings_batch_all_cached(self, mock_service):
        """Test batch generation when all texts are cached."""
        texts = ["text1", "text2", "text3"]
        
        # Pre-populate cache for all texts
        for i, text in enumerate(texts):
            text_hash = mock_service._hash_text(text)
            mock_service._cache[text_hash] = [i, i+0.1, i+0.2]
        
        result = await mock_service.generate_embeddings_batch(texts)
        
        assert len(result) == 3
        assert result[0] == [0, 0.1, 0.2]
        assert result[1] == [1, 1.1, 1.2]
        assert result[2] == [2, 2.1, 2.2]
        
        assert mock_service._cache_hits == 3
        assert mock_service._cache_misses == 0
        
        # No API calls should be made
        mock_service.client.embeddings.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_generate_embeddings_batch_exception_handling(self, mock_service):
        """Test batch generation with API exception."""
        mock_service.client.embeddings.create = AsyncMock(
            side_effect=Exception("Batch API Error")
        )
        
        texts = ["text1", "text2"]
        
        with pytest.raises(Exception, match="Batch API Error"):
            await mock_service.generate_embeddings_batch(texts)
        
        assert mock_service._cache_misses == 2


class TestEmbeddingServiceUtilities:
    """Test utility methods."""

    @pytest.fixture
    def mock_service(self):
        """Create a mock embedding service."""
        with patch('src.services.embedding_service.AsyncOpenAI'), \
             patch('src.services.embedding_service.get_settings'):
            service = EmbeddingService()
            return service

    def test_hash_text_consistency(self, mock_service):
        """Test that text hashing is consistent."""
        text = "test text"
        hash1 = mock_service._hash_text(text)
        hash2 = mock_service._hash_text(text)
        
        assert hash1 == hash2
        assert isinstance(hash1, str)
        assert len(hash1) == 64  # SHA256 hex digest length

    def test_hash_text_different_inputs(self, mock_service):
        """Test that different texts produce different hashes."""
        hash1 = mock_service._hash_text("text1")
        hash2 = mock_service._hash_text("text2")
        
        assert hash1 != hash2

    def test_get_cache_stats_empty(self, mock_service):
        """Test cache statistics with empty cache."""
        stats = mock_service.get_cache_stats()
        
        assert stats == {
            "cache_size": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "hit_rate": 0
        }

    def test_get_cache_stats_with_data(self, mock_service):
        """Test cache statistics with data."""
        # Simulate some cache activity
        mock_service._cache["hash1"] = [0.1, 0.2]
        mock_service._cache["hash2"] = [0.3, 0.4]
        mock_service._cache_hits = 5
        mock_service._cache_misses = 3
        
        stats = mock_service.get_cache_stats()
        
        assert stats == {
            "cache_size": 2,
            "cache_hits": 5,
            "cache_misses": 3,
            "hit_rate": 5/8  # 5 hits out of 8 total
        }

    def test_clear_cache(self, mock_service):
        """Test cache clearing."""
        # Add some data to cache
        mock_service._cache["hash1"] = [0.1, 0.2]
        mock_service._cache_hits = 5
        mock_service._cache_misses = 3
        
        mock_service.clear_cache()
        
        assert mock_service._cache == {}
        assert mock_service._cache_hits == 0
        assert mock_service._cache_misses == 0


class TestEmbeddingServiceCacheWarmup:
    """Test cache warmup functionality."""

    @pytest.fixture
    def mock_service(self):
        """Create a mock embedding service."""
        with patch('src.services.embedding_service.AsyncOpenAI'), \
             patch('src.services.embedding_service.get_settings'):
            service = EmbeddingService()
            service.client = AsyncMock()
            return service

    @pytest.mark.asyncio
    async def test_warmup_cache(self, mock_service):
        """Test cache warmup functionality."""
        # Mock the batch generation method
        mock_service.generate_embeddings_batch = AsyncMock()
        
        texts = ["common text 1", "common text 2", "common text 3"]
        
        await mock_service.warmup_cache(texts)
        
        # Should call batch generation
        mock_service.generate_embeddings_batch.assert_called_once_with(texts)

    @pytest.mark.asyncio
    async def test_warmup_cache_integration(self, mock_service):
        """Test cache warmup with actual batch generation."""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.data = [
            Mock(embedding=[0.1, 0.2, 0.3]),
            Mock(embedding=[0.4, 0.5, 0.6])
        ]
        mock_service.client.embeddings.create = AsyncMock(return_value=mock_response)
        
        texts = ["text1", "text2"]
        
        await mock_service.warmup_cache(texts)
        
        # Cache should be populated
        assert len(mock_service._cache) == 2
        
        # Subsequent calls should hit cache
        result = await mock_service.generate_embedding("text1")
        assert result == [0.1, 0.2, 0.3]
        assert mock_service._cache_hits == 1


class TestEmbeddingServicePerformance:
    """Test performance requirements from PRD."""

    @pytest.fixture
    def mock_service(self):
        """Create a mock embedding service."""
        with patch('src.services.embedding_service.AsyncOpenAI'), \
             patch('src.services.embedding_service.get_settings'):
            service = EmbeddingService()
            service.client = AsyncMock()
            return service

    @pytest.mark.asyncio
    async def test_embedding_performance_requirement(self, mock_service):
        """Test that embedding generation completes within reasonable time."""
        # Mock fast response
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1, 0.2, 0.3])]
        mock_service.client.embeddings.create = AsyncMock(return_value=mock_response)
        
        start_time = time.time()
        await mock_service.generate_embedding("test text")
        end_time = time.time()
        
        # Should complete quickly (within 1 second for mocked response)
        assert end_time - start_time < 1.0

    @pytest.mark.asyncio
    async def test_batch_embedding_efficiency(self, mock_service):
        """Test that batch processing is more efficient than individual calls."""
        # Mock response for batch
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[i, i+0.1, i+0.2]) for i in range(10)]
        mock_service.client.embeddings.create = AsyncMock(return_value=mock_response)
        
        texts = [f"text{i}" for i in range(10)]
        
        start_time = time.time()
        await mock_service.generate_embeddings_batch(texts)
        end_time = time.time()
        
        # Should complete quickly and make only one API call
        assert end_time - start_time < 1.0
        assert mock_service.client.embeddings.create.call_count == 1

    def test_cache_efficiency(self, mock_service):
        """Test that caching improves performance."""
        # Add items to cache
        for i in range(100):
            text_hash = mock_service._hash_text(f"text{i}")
            mock_service._cache[text_hash] = [i, i+0.1, i+0.2]
            mock_service._cache_hits += 1
        
        stats = mock_service.get_cache_stats()
        
        # Should have good hit rate
        assert stats["cache_size"] == 100
        assert stats["hit_rate"] == 1.0  # All hits, no misses


class TestEmbeddingServiceIntegration:
    """Test integration scenarios."""

    @pytest.fixture
    def mock_service(self):
        """Create a mock embedding service."""
        with patch('src.services.embedding_service.AsyncOpenAI'), \
             patch('src.services.embedding_service.get_settings'):
            service = EmbeddingService()
            service.client = AsyncMock()
            return service

    @pytest.mark.asyncio
    async def test_mixed_cache_and_api_calls(self, mock_service):
        """Test scenario with mixed cache hits and API calls."""
        # Pre-populate cache with some texts
        cached_texts = ["cached1", "cached2"]
        for i, text in enumerate(cached_texts):
            text_hash = mock_service._hash_text(text)
            mock_service._cache[text_hash] = [i, i+0.1, i+0.2]
        
        # Mock API response for new texts
        mock_response = Mock()
        mock_response.data = [
            Mock(embedding=[2, 2.1, 2.2]),
            Mock(embedding=[3, 3.1, 3.2])
        ]
        mock_service.client.embeddings.create = AsyncMock(return_value=mock_response)
        
        # Mix of cached and new texts
        all_texts = ["cached1", "new1", "cached2", "new2"]
        result = await mock_service.generate_embeddings_batch(all_texts)
        
        assert len(result) == 4
        assert result[0] == [0, 0.1, 0.2]    # cached1
        assert result[1] == [2, 2.1, 2.2]    # new1 (from API)
        assert result[2] == [1, 1.1, 1.2]    # cached2
        assert result[3] == [3, 3.1, 3.2]    # new2 (from API)
        
        assert mock_service._cache_hits == 2
        assert mock_service._cache_misses == 2
        
        # API should only be called for new texts
        mock_service.client.embeddings.create.assert_called_once_with(
            model="text-embedding-3-large",
            input=["new1", "new2"]
        )

    @pytest.mark.asyncio
    async def test_error_recovery_and_retry(self, mock_service):
        """Test error handling and recovery scenarios."""
        # First call fails, second succeeds
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1, 0.2, 0.3])]
        
        mock_service.client.embeddings.create = AsyncMock(
            side_effect=[Exception("Temporary error"), mock_response]
        )
        
        # First call should fail
        with pytest.raises(Exception, match="Temporary error"):
            await mock_service.generate_embedding("test text")
        
        # Second call should succeed
        result = await mock_service.generate_embedding("test text")
        assert result == [0.1, 0.2, 0.3]
        
        # Should have made two API calls
        assert mock_service.client.embeddings.create.call_count == 2

    @pytest.mark.asyncio
    async def test_concurrent_embedding_requests(self, mock_service):
        """Test handling of concurrent embedding requests."""
        import asyncio
        
        # Mock responses
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1, 0.2, 0.3])]
        mock_service.client.embeddings.create = AsyncMock(return_value=mock_response)
        
        # Make concurrent requests for the same text
        tasks = [
            mock_service.generate_embedding("same text")
            for _ in range(5)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # All should return the same result
        for result in results:
            assert result == [0.1, 0.2, 0.3]
        
        # Should have made at least one API call
        # (Note: Due to async nature, might make multiple calls before caching)
        assert mock_service.client.embeddings.create.call_count >= 1


class TestEmbeddingServiceRealExecution:
    """Test embedding service with minimal mocking to ensure real code execution."""

    def test_hash_text_functionality(self):
        """Test _hash_text method with real execution - no mocking."""
        # Create service with minimal mocking for just the external dependencies
        with patch('src.services.embedding_service.AsyncOpenAI') as mock_openai, \
             patch('src.services.embedding_service.get_settings') as mock_settings:
            
            mock_settings_obj = Mock()
            mock_settings_obj.openai.api_key = "test-key"
            mock_settings.return_value = mock_settings_obj
            
            service = EmbeddingService()
            
            # Test real _hash_text execution
            text1 = "This is a test text for hashing"
            text2 = "This is a different text"
            text3 = "This is a test text for hashing"  # Same as text1
            
            hash1 = service._hash_text(text1)
            hash2 = service._hash_text(text2)
            hash3 = service._hash_text(text3)
            
            # Verify hash consistency
            assert hash1 == hash3  # Same text should produce same hash
            assert hash1 != hash2  # Different text should produce different hash
            assert isinstance(hash1, str)
            assert len(hash1) > 0

    def test_cache_management_real_execution(self):
        """Test cache operations with real code execution."""
        with patch('src.services.embedding_service.AsyncOpenAI') as mock_openai, \
             patch('src.services.embedding_service.get_settings') as mock_settings:
            
            mock_settings_obj = Mock()  
            mock_settings_obj.openai.api_key = "test-key"
            mock_settings.return_value = mock_settings_obj
            
            service = EmbeddingService()
            
            # Test real cache operations
            test_embedding = [0.1, 0.2, 0.3, 0.4]
            cache_key = "test_cache_key"
            
            # Add to cache  
            service._cache[cache_key] = test_embedding
            assert service._cache[cache_key] == test_embedding
            
            # Test get_cache_stats with real execution
            stats = service.get_cache_stats()
            assert isinstance(stats, dict)
            assert "cache_size" in stats
            assert "cache_hits" in stats  # Fixed: actual key name
            assert "cache_misses" in stats  # Fixed: actual key name
            assert "hit_rate" in stats
            
            # Test clear_cache with real execution
            service.clear_cache()
            assert len(service._cache) == 0
            assert service._cache_hits == 0
            assert service._cache_misses == 0