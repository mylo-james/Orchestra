"""Embedding service for generating text embeddings using OpenAI."""

import hashlib
import time
from typing import Dict, List

from openai import AsyncOpenAI

from orchestra.config.settings import get_settings
from orchestra.utils.circuit_breaker import CircuitBreaker
from orchestra.utils.logging import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    """
    Service for generating text embeddings using OpenAI's text-embedding-3-large model.

    This service includes caching, batching, and circuit breaker patterns
    for optimal performance and reliability.
    """

    def __init__(self, model: str = "text-embedding-3-large"):
        """
        Initialize the embedding service.

        Args:
            model: OpenAI embedding model to use
        """
        settings = get_settings()
        self.client = AsyncOpenAI(api_key=settings.openai.api_key)
        self.model = model

        # Circuit breaker for OpenAI API calls
        from orchestra.utils.circuit_breaker import CircuitBreakerConfig

        config = CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=30.0,
        )
        self.circuit_breaker = CircuitBreaker("openai_embeddings", config)

        # Cache for embeddings (hash -> embedding)
        self._cache: Dict[str, List[float]] = {}
        self._cache_hits = 0
        self._cache_misses = 0

        # Batch processing
        self._batch_queue: List[tuple] = []
        self._batch_size = 20  # OpenAI recommended batch size
        self._batch_timeout = 0.1  # 100ms

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to generate embedding for

        Returns:
            Embedding vector
        """
        # Check cache
        text_hash = self._hash_text(text)
        if text_hash in self._cache:
            self._cache_hits += 1
            logger.debug(f"Cache hit for embedding (hits: {self._cache_hits})")
            return self._cache[text_hash]

        self._cache_misses += 1
        start_time = time.time()

        try:
            # Call OpenAI API
            response = await self.client.embeddings.create(
                model=self.model,
                input=text,
            )

            embedding = response.data[0].embedding

            # Cache the result
            self._cache[text_hash] = embedding

            # Log performance
            duration = time.time() - start_time
            logger.debug(f"Generated embedding in {duration:.2f}s")

            return embedding

        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise

    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch.

        Args:
            texts: List of texts to generate embeddings for

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        # Check cache for all texts
        embeddings = []
        uncached_texts = []
        uncached_indices = []

        for i, text in enumerate(texts):
            text_hash = self._hash_text(text)
            if text_hash in self._cache:
                self._cache_hits += 1
                cached_embedding = self._cache[text_hash]
                if cached_embedding is not None:
                    embeddings.append(cached_embedding)
                    continue
                # If cached embedding is None, fall through to uncached handling

            # Handle uncached or None cached embeddings
            self._cache_misses += 1
            embeddings.append([])  # Initialize with empty list
            uncached_texts.append(text)
            uncached_indices.append(i)

        # Generate embeddings for uncached texts
        if uncached_texts:
            start_time = time.time()

            try:
                # Process in batches if needed
                batch_embeddings = []
                for i in range(0, len(uncached_texts), self._batch_size):
                    batch = uncached_texts[i : i + self._batch_size]

                    response = await self.client.embeddings.create(
                        model=self.model,
                        input=batch,
                    )

                    batch_embeddings.extend([d.embedding for d in response.data])

                # Fill in the results and update cache
                for idx, embedding in zip(uncached_indices, batch_embeddings):
                    embeddings[idx] = embedding
                    text_hash = self._hash_text(texts[idx])
                    self._cache[text_hash] = embedding

                # Log performance
                duration = time.time() - start_time
                logger.debug(
                    f"Generated {len(uncached_texts)} embeddings in {duration:.2f}s"
                )

            except Exception as e:
                logger.error(f"Failed to generate batch embeddings: {e}")
                raise

        return embeddings

    def _hash_text(self, text: str) -> str:
        """Generate a hash for text to use as cache key."""
        return hashlib.sha256(text.encode()).hexdigest()

    def get_cache_stats(self) -> Dict[str, float | int]:
        """Get cache statistics."""
        total = self._cache_hits + self._cache_misses
        hit_rate = self._cache_hits / total if total > 0 else 0.0

        return {
            "cache_size": len(self._cache),
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "hit_rate": hit_rate,
        }

    def clear_cache(self) -> None:
        """Clear the embedding cache."""
        self._cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0
        logger.info("Embedding cache cleared")

    async def warmup_cache(self, texts: List[str]) -> None:
        """
        Warm up the cache with frequently used texts.

        Args:
            texts: List of texts to pre-generate embeddings for
        """
        logger.info(f"Warming up cache with {len(texts)} texts")
        await self.generate_embeddings_batch(texts)
        logger.info("Cache warmup complete")
