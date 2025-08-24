"""Knowledge service for managing vector database operations."""

import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    Range,
    VectorParams,
)

from orchestra.models.knowledge import (
    KnowledgeChunk,
    KnowledgeLock,
    KnowledgeMetadata,
    KnowledgeQuery,
    KnowledgeVersion,
)
from orchestra.services.embedding_service import EmbeddingService
from orchestra.utils.circuit_breaker import CircuitBreaker
from orchestra.utils.logging import get_logger

logger = get_logger(__name__)


class KnowledgeService:
    """
    Service for managing knowledge in the vector database.

    This service provides atomic grab-edit-upsert operations with
    versioning, conflict detection, and performance optimization.
    """

    def __init__(
        self,
        qdrant_host: str = "localhost",
        qdrant_port: int = 6333,
        collection_name: str = "orchestra_knowledge",
        embedding_service: Optional[EmbeddingService] = None,
    ):
        """
        Initialize the knowledge service.

        Args:
            qdrant_host: Qdrant server host
            qdrant_port: Qdrant server port
            collection_name: Name of the Qdrant collection
            embedding_service: Service for generating embeddings
        """
        self.client = QdrantClient(host=qdrant_host, port=qdrant_port)
        self.collection_name = collection_name
        self.embedding_service = embedding_service or EmbeddingService()

        # Circuit breaker for Qdrant operations
        from orchestra.utils.circuit_breaker import CircuitBreakerConfig

        config = CircuitBreakerConfig(
            failure_threshold=5,
            recovery_timeout=30.0,
        )
        self.circuit_breaker = CircuitBreaker("qdrant_operations", config)

        # In-memory cache for frequently accessed knowledge
        self._cache: Dict[str, Tuple[KnowledgeChunk, float]] = {}
        self._cache_ttl = 300  # 5 minutes

        # Distributed locks (in production, use Redis)
        self._locks: Dict[str, KnowledgeLock] = {}

        # Initialize collection if it doesn't exist
        self._initialize_collection()

    def _initialize_collection(self) -> None:
        """Initialize the Qdrant collection if it doesn't exist."""
        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]

            if self.collection_name not in collection_names:
                # Create collection with vector size for text-embedding-3-large
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=3072,  # text-embedding-3-large dimension
                        distance=Distance.COSINE,
                    ),
                )
                logger.info(f"Created Qdrant collection: {self.collection_name}")
            else:
                logger.info(f"Using existing Qdrant collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant collection: {e}")
            raise

    async def grab(
        self,
        document_id: str,
        agent_id: str,
        lock_timeout: int = 30,
    ) -> Tuple[Optional[KnowledgeChunk], Optional[KnowledgeLock]]:
        """
        Grab a knowledge chunk with distributed locking.

        Args:
            document_id: ID of the document to grab
            agent_id: ID of the agent grabbing the document
            lock_timeout: Lock timeout in seconds

        Returns:
            Tuple of (knowledge chunk, lock) if successful, (None, None) otherwise
        """
        # Check cache first
        if document_id in self._cache:
            chunk, cached_at = self._cache[document_id]
            if time.time() - cached_at < self._cache_ttl:
                logger.debug(f"Returning cached knowledge: {document_id}")
                # Still need to acquire lock for write operations
                lock = await self._acquire_lock(
                    document_id, agent_id, "read", lock_timeout
                )
                return chunk, lock

        # Acquire lock
        lock = await self._acquire_lock(document_id, agent_id, "write", lock_timeout)
        if not lock:
            logger.warning(f"Failed to acquire lock for document: {document_id}")
            return None, None

        try:
            # Fetch from Qdrant
            result = await self._fetch_from_qdrant(document_id)
            if result:
                chunk = self._point_to_chunk(result)
                # Update cache
                self._cache[document_id] = (chunk, time.time())
                return chunk, lock

            logger.warning(f"Document not found: {document_id}")
            await self._release_lock(lock)
            return None, None

        except Exception as e:
            logger.error(f"Failed to grab document {document_id}: {e}")
            await self._release_lock(lock)
            raise

    async def upsert(
        self,
        chunk: KnowledgeChunk,
        lock: Optional[KnowledgeLock] = None,
        agent_id: str = "system",
    ) -> bool:
        """
        Upsert a knowledge chunk with versioning.

        Args:
            chunk: Knowledge chunk to upsert
            lock: Lock acquired during grab operation
            agent_id: ID of the agent performing the upsert

        Returns:
            True if successful, False otherwise
        """
        start_time = time.time()

        try:
            # Validate lock if provided
            if lock and not await self._validate_lock(lock):
                logger.error("Invalid or expired lock")
                return False

            # Generate embedding
            embedding = await self.embedding_service.generate_embedding(chunk.content)
            chunk.embedding = embedding

            # Update metadata
            document_id = getattr(chunk.metadata, "document_id", None) or str(
                uuid.uuid4()
            )
            metadata_dict = {
                "document_id": document_id,
                "version": chunk.version,
                "agent_attribution": agent_id,
                "updated_at": datetime.utcnow().isoformat(),
                "created_at": chunk.created_at.isoformat(),
                "confidence_score": getattr(chunk.metadata, "confidence_score", 1.0),
                "knowledge_domain": getattr(
                    chunk.metadata, "knowledge_domain", "general"
                ),
            }

            # Create Qdrant point
            point = PointStruct(
                id=document_id,
                vector=embedding,
                payload={
                    "content": chunk.content,
                    "metadata": metadata_dict,
                    "version": chunk.version,
                },
            )

            # Upsert to Qdrant
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point],
            )

            # Update cache
            self._cache[metadata_dict["document_id"]] = (chunk, time.time())

            # Release lock if held
            if lock:
                await self._release_lock(lock)

            # Log performance
            duration = time.time() - start_time
            if duration > 1.0:
                logger.warning(f"Slow upsert operation: {duration:.2f}s")
            else:
                logger.info(f"Upsert completed in {duration:.2f}s")

            return True

        except Exception as e:
            logger.error(f"Failed to upsert knowledge: {e}")
            if lock:
                await self._release_lock(lock)
            return False

    async def query(
        self,
        query: KnowledgeQuery,
    ) -> List[KnowledgeChunk]:
        """
        Query the knowledge base with semantic search.

        Args:
            query: Query parameters

        Returns:
            List of matching knowledge chunks
        """
        start_time = time.time()

        try:
            # Generate query embedding
            query_embedding = await self.embedding_service.generate_embedding(
                query.query_text
            )

            # Build filter conditions
            filter_conditions = []

            if query.knowledge_domains:
                domain_values = [d.value for d in query.knowledge_domains]
                filter_conditions.append(
                    FieldCondition(
                        key="metadata.knowledge_domain",
                        match=MatchValue(
                            value=domain_values[0]
                        ),  # Use first domain for now
                    )
                )

            if query.agent_id:
                filter_conditions.append(
                    FieldCondition(
                        key="metadata.agent_attribution",
                        match=MatchValue(value=query.agent_id),
                    )
                )

            if query.min_confidence > 0:
                filter_conditions.append(
                    FieldCondition(
                        key="metadata.confidence_score",
                        range=Range(gte=query.min_confidence),
                    )
                )

            # Create filter
            search_filter = (
                Filter(must=filter_conditions) if filter_conditions else None
            )

            # Search in Qdrant
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                query_filter=search_filter,
                limit=query.max_results,
            )

            # Convert results to knowledge chunks
            chunks = [self._point_to_chunk(result) for result in results]

            # Log performance
            duration = time.time() - start_time
            if duration > 0.5:
                logger.warning(f"Slow query operation: {duration:.2f}s")

            return chunks

        except Exception as e:
            logger.error(f"Failed to query knowledge base: {e}")
            raise

    async def get_version_history(
        self,
        document_id: str,
        limit: int = 10,
    ) -> List[KnowledgeVersion]:
        """
        Get version history for a document.

        Args:
            document_id: Document ID
            limit: Maximum number of versions to return

        Returns:
            List of knowledge versions
        """
        # In production, this would query a separate version history table
        # For now, return current version only
        result = await self._fetch_from_qdrant(document_id)
        if result:
            chunk = self._point_to_chunk(result)
            version = KnowledgeVersion(
                document_id=document_id,
                version=chunk.version,
                content=chunk.content,
                metadata=chunk.metadata,
                created_at=chunk.created_at,
                agent_attribution=chunk.metadata.get("agent_attribution", "system"),
            )
            return [version]
        return []

    async def _acquire_lock(
        self,
        document_id: str,
        agent_id: str,
        operation: str,
        timeout: int,
    ) -> Optional[KnowledgeLock]:
        """Acquire a distributed lock for a document."""
        # Check if already locked
        if document_id in self._locks:
            existing_lock = self._locks[document_id]
            if existing_lock.expires_at > datetime.utcnow():
                logger.debug(f"Document {document_id} is already locked")
                return None

        # Create new lock
        lock = KnowledgeLock(
            document_id=document_id,
            agent_id=agent_id,
            operation=operation,
            expires_at=datetime.utcnow() + timedelta(seconds=timeout),
        )

        self._locks[document_id] = lock
        logger.debug(f"Acquired lock for document {document_id}")
        return lock

    async def _release_lock(self, lock: KnowledgeLock) -> None:
        """Release a distributed lock."""
        if lock.document_id in self._locks:
            del self._locks[lock.document_id]
            lock.released = True
            logger.debug(f"Released lock for document {lock.document_id}")

    async def _validate_lock(self, lock: KnowledgeLock) -> bool:
        """Validate that a lock is still valid."""
        if lock.released:
            return False
        if lock.expires_at <= datetime.utcnow():
            return False
        if lock.document_id not in self._locks:
            return False
        return self._locks[lock.document_id].lock_id == lock.lock_id

    async def _fetch_from_qdrant(self, document_id: str) -> Optional[Any]:
        """Fetch a document from Qdrant by ID."""
        try:
            results = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[document_id],
            )
            return results[0] if results else None
        except Exception as e:
            logger.error(f"Failed to fetch from Qdrant: {e}")
            return None

    def _point_to_chunk(self, point: Any) -> KnowledgeChunk:
        """Convert a Qdrant point to a KnowledgeChunk."""
        from orchestra.models.knowledge import KnowledgeDomain, SecurityClassification

        payload = point.payload if hasattr(point, "payload") else point
        metadata_dict = payload.get("metadata", {})

        # Create proper KnowledgeMetadata object
        metadata = KnowledgeMetadata(
            domain=KnowledgeDomain.GENERAL,  # Default domain
            tags=[],
            source="qdrant",
            confidence=metadata_dict.get("confidence_score", 0.0),
            security_classification=SecurityClassification.PUBLIC,
            document_id=metadata_dict.get("document_id"),
            agent_attribution=metadata_dict.get("agent_attribution"),
            confidence_score=metadata_dict.get("confidence_score"),
            knowledge_domain=metadata_dict.get("knowledge_domain"),
        )

        return KnowledgeChunk(
            id=metadata_dict.get("document_id", str(uuid.uuid4())),
            content=payload.get("content", ""),
            metadata=metadata,
            embedding=point.vector if hasattr(point, "vector") else None,
            version=payload.get("version", 1),
            created_at=datetime.fromisoformat(
                str(metadata_dict.get("created_at", datetime.utcnow().isoformat()))
            ),
            updated_at=datetime.fromisoformat(
                str(metadata_dict.get("updated_at", datetime.utcnow().isoformat()))
            ),
            author=metadata_dict.get("agent_attribution", "system"),
        )

    def clear_cache(self) -> None:
        """Clear the knowledge cache."""
        self._cache.clear()
        logger.info("Knowledge cache cleared")
