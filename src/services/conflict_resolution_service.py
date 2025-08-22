"""Conflict resolution service for knowledge synchronization."""

import math
from datetime import datetime, timedelta
from typing import List, Optional

from src.models.knowledge import (
    KnowledgeChunk,
    KnowledgeConflict,
    KnowledgeVersion,
    MergeStrategy,
    SeverityLevel,
)
from src.services.embedding_service import EmbeddingService
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ConflictResolutionService:
    """
    Service for detecting and resolving conflicts in knowledge updates.

    This service implements intelligent merge strategies including
    append, vote, and hybrid approaches with human escalation support.
    """

    def __init__(
        self,
        embedding_service: Optional[EmbeddingService] = None,
    ):
        """
        Initialize the conflict resolution service.

        Args:
            embedding_service: Service for generating embeddings
        """
        self.embedding_service = embedding_service or EmbeddingService()

        # Conflict detection thresholds
        self.similarity_thresholds = {
            SeverityLevel.LOW: (0.85, 0.90),
            SeverityLevel.MEDIUM: (0.90, 0.95),
            SeverityLevel.HIGH: (0.95, 0.98),
            SeverityLevel.CRITICAL: (0.98, 1.0),
        }

        # Strategy selection rules
        self.strategy_rules = {
            SeverityLevel.LOW: MergeStrategy.APPEND,
            SeverityLevel.MEDIUM: MergeStrategy.VOTE,
            SeverityLevel.HIGH: MergeStrategy.HYBRID,
            SeverityLevel.CRITICAL: MergeStrategy.HYBRID,
        }

        # Default resolution strategies per severity
        self.default_strategies = self.strategy_rules

        # Human escalation queue (Phase 1 MVP)
        self.escalation_queue: List[KnowledgeConflict] = []

        # Conflict history for audit
        self.conflict_history: List[KnowledgeConflict] = []

    async def detect_conflict(
        self,
        existing: KnowledgeChunk,
        proposed: KnowledgeChunk,
    ) -> Optional[KnowledgeConflict]:
        """
        Detect if there's a conflict between existing and proposed knowledge.

        Args:
            existing: Existing knowledge chunk
            proposed: Proposed knowledge chunk

        Returns:
            KnowledgeConflict if conflict detected, None otherwise
        """
        # Generate embeddings if not present
        if not existing.embedding:
            existing.embedding = await self.embedding_service.generate_embedding(
                existing.content
            )
        if not proposed.embedding:
            proposed.embedding = await self.embedding_service.generate_embedding(
                proposed.content
            )

        # Calculate semantic similarity
        similarity = self._calculate_similarity(existing.embedding, proposed.embedding)

        # Check temporal proximity (within 5 minutes)
        time_delta = abs((proposed.updated_at - existing.updated_at).total_seconds())
        is_concurrent = time_delta < 300  # 5 minutes

        # Determine if there's a conflict
        if similarity < 0.85 and not is_concurrent:
            # Different enough and not concurrent - no conflict
            return None

        # Create conflict object
        conflict = KnowledgeConflict(
            document_id=existing.metadata.get("document_id", "unknown"),
            version_a=self._chunk_to_version(existing),
            version_b=self._chunk_to_version(proposed),
            conflict_type=self._determine_conflict_type(existing, proposed),
            similarity_score=similarity,
            detected_at=datetime.utcnow(),
        )

        # Add to history
        self.conflict_history.append(conflict)

        logger.info(
            f"Conflict detected: {conflict.conflict_type} "
            f"(similarity: {similarity:.3f}, concurrent: {is_concurrent})"
        )

        return conflict

    async def resolve_conflict(
        self,
        conflict: KnowledgeConflict,
        strategy: Optional[MergeStrategy] = None,
    ) -> KnowledgeChunk:
        """
        Resolve a knowledge conflict using the specified or auto-selected strategy.

        Args:
            conflict: The conflict to resolve
            strategy: Merge strategy to use (auto-selected if None)

        Returns:
            Merged knowledge chunk
        """
        # Auto-select strategy if not specified
        if not strategy:
            severity = self._classify_severity(conflict.similarity_score)
            strategy = self.strategy_rules[severity]
            logger.info(f"Auto-selected strategy: {strategy} for {severity} conflict")

        # Apply strategy
        if strategy == MergeStrategy.APPEND:
            return await self._merge_append(conflict)
        elif strategy == MergeStrategy.VOTE:
            return await self._merge_vote(conflict)
        elif strategy == MergeStrategy.HYBRID:
            return await self._merge_hybrid(conflict)
        elif strategy == MergeStrategy.CONSERVATIVE:
            return self._version_to_chunk(conflict.version_a)
        elif strategy == MergeStrategy.AGGRESSIVE:
            return self._version_to_chunk(conflict.version_b)
        else:
            raise ValueError(f"Unknown merge strategy: {strategy}")

    async def _merge_append(self, conflict: KnowledgeConflict) -> KnowledgeChunk:
        """
        Merge by appending both versions.

        Args:
            conflict: The conflict to resolve

        Returns:
            Merged knowledge chunk
        """
        # Combine content with clear separation
        merged_content = (
            f"{conflict.version_a.content}\n\n"
            f"--- Additional Information (Added by {conflict.version_b.agent_attribution}) ---\n"
            f"{conflict.version_b.content}"
        )

        # Merge metadata
        merged_metadata = {
            **conflict.version_a.metadata,
            "merge_strategy": "append",
            "merged_at": datetime.utcnow().isoformat(),
            "confidence_score": max(
                conflict.version_a.metadata.get("confidence_score", 0),
                conflict.version_b.metadata.get("confidence_score", 0),
            ),
        }

        return KnowledgeChunk(
            content=merged_content,
            metadata=merged_metadata,
            version=max(conflict.version_a.version, conflict.version_b.version) + 1,
        )

    async def _merge_vote(self, conflict: KnowledgeConflict) -> KnowledgeChunk:
        """
        Merge using confidence-weighted voting.

        Args:
            conflict: The conflict to resolve

        Returns:
            Merged knowledge chunk
        """
        # Get confidence scores
        conf_a = conflict.version_a.metadata.get("confidence_score", 0.5)
        conf_b = conflict.version_b.metadata.get("confidence_score", 0.5)

        # Apply exponential weighting
        weight_a = np.exp(conf_a)
        weight_b = np.exp(conf_b)

        # Select winner
        if weight_b > weight_a:
            winner = conflict.version_b
            logger.info(f"Vote strategy selected version B (confidence: {conf_b:.2f})")
        else:
            winner = conflict.version_a
            logger.info(f"Vote strategy selected version A (confidence: {conf_a:.2f})")

        # Create merged chunk
        merged_metadata = {
            **winner.metadata,
            "merge_strategy": "vote",
            "merged_at": datetime.utcnow().isoformat(),
            "vote_weights": {"version_a": weight_a, "version_b": weight_b},
        }

        return KnowledgeChunk(
            content=winner.content,
            metadata=merged_metadata,
            version=max(conflict.version_a.version, conflict.version_b.version) + 1,
        )

    async def _merge_hybrid(self, conflict: KnowledgeConflict) -> KnowledgeChunk:
        """
        Hybrid merge strategy with potential human escalation.

        Args:
            conflict: The conflict to resolve

        Returns:
            Merged knowledge chunk
        """
        # Check if human escalation is needed
        if self._needs_human_escalation(conflict):
            logger.warning(
                f"Critical conflict requires human review: {conflict.document_id}"
            )

            # Add to escalation queue
            self.escalation_queue.append(conflict)

            # For Phase 1 MVP, use conservative merge as fallback
            logger.info("Using conservative merge as fallback for human escalation")
            return await self._merge_conservative(conflict)

        # Otherwise, use intelligent merge
        # Analyze content differences
        content_a = conflict.version_a.content
        content_b = conflict.version_b.content

        # Find common and unique parts
        lines_a = set(content_a.split("\n"))
        lines_b = set(content_b.split("\n"))

        common_lines = lines_a & lines_b
        unique_a = lines_a - lines_b
        unique_b = lines_b - lines_a

        # Build merged content
        merged_lines = list(common_lines)

        if unique_a:
            merged_lines.append("\n--- From Version A ---")
            merged_lines.extend(unique_a)

        if unique_b:
            merged_lines.append("\n--- From Version B ---")
            merged_lines.extend(unique_b)

        merged_content = "\n".join(merged_lines)

        # Merge metadata
        merged_metadata = {
            **conflict.version_a.metadata,
            **conflict.version_b.metadata,
            "merge_strategy": "hybrid",
            "merged_at": datetime.utcnow().isoformat(),
            "confidence_score": (
                conflict.version_a.metadata.get("confidence_score", 0)
                + conflict.version_b.metadata.get("confidence_score", 0)
            )
            / 2,
        }

        return KnowledgeChunk(
            content=merged_content,
            metadata=merged_metadata,
            version=max(conflict.version_a.version, conflict.version_b.version) + 1,
        )

    async def _merge_conservative(self, conflict: KnowledgeConflict) -> KnowledgeChunk:
        """Conservative merge - keep existing version."""
        return self._version_to_chunk(conflict.version_a)

    def _calculate_similarity(
        self, embedding_a: List[float], embedding_b: List[float]
    ) -> float:
        """Calculate cosine similarity between two embeddings."""
        # Manual cosine similarity calculation
        if not embedding_a or not embedding_b:
            return 0.0

        # Calculate dot product
        dot_product = sum(a * b for a, b in zip(embedding_a, embedding_b))

        # Calculate magnitudes
        mag_a = math.sqrt(sum(a * a for a in embedding_a))
        mag_b = math.sqrt(sum(b * b for b in embedding_b))

        # Avoid division by zero
        if mag_a == 0 or mag_b == 0:
            return 0.0

        # Calculate cosine similarity
        similarity = dot_product / (mag_a * mag_b)

        return float(similarity)

    def _classify_severity(
        self, similarity: float, time_delta: timedelta
    ) -> SeverityLevel:
        """Classify conflict severity based on similarity score."""
        for severity, (min_sim, max_sim) in self.similarity_thresholds.items():
            if min_sim <= similarity < max_sim:
                return severity

        # Default to critical for very high similarity
        return SeverityLevel.CRITICAL

    def _determine_conflict_type(
        self, existing: KnowledgeChunk, proposed: KnowledgeChunk
    ) -> str:
        """Determine the type of conflict."""
        # Check if content differs
        content_differs = existing.content != proposed.content

        # Check if metadata differs significantly
        metadata_differs = False
        for key in ["confidence_score", "knowledge_domain", "agent_attribution"]:
            if existing.metadata.get(key) != proposed.metadata.get(key):
                metadata_differs = True
                break

        if content_differs and metadata_differs:
            return "both"
        elif content_differs:
            return "content"
        elif metadata_differs:
            return "metadata"
        else:
            return "unknown"

    def _chunk_to_version(self, chunk: KnowledgeChunk) -> KnowledgeVersion:
        """Convert a knowledge chunk to a version object."""
        return KnowledgeVersion(
            document_id=chunk.metadata.get("document_id", "unknown"),
            version=chunk.version,
            content=chunk.content,
            metadata=chunk.metadata,
            created_at=chunk.created_at,
            agent_attribution=chunk.metadata.get("agent_attribution", "system"),
        )

    def _version_to_chunk(self, version: KnowledgeVersion) -> KnowledgeChunk:
        """Convert a version object to a knowledge chunk."""
        return KnowledgeChunk(
            content=version.content,
            metadata=version.metadata,
            version=version.version,
            created_at=version.created_at,
        )

    def _needs_human_escalation(self, conflict: KnowledgeConflict) -> bool:
        """Determine if a conflict needs human escalation."""
        # Phase 1 MVP: Critical conflicts always escalate
        return conflict.severity == SeverityLevel.CRITICAL

    def get_escalation_queue(self) -> List[KnowledgeConflict]:
        """Get the current human escalation queue."""
        return self.escalation_queue.copy()

    def resolve_escalation(self, conflict_id: str, resolution: KnowledgeChunk) -> bool:
        """
        Resolve a conflict from the escalation queue.

        Args:
            conflict_id: ID of the conflict to resolve
            resolution: The resolved knowledge chunk

        Returns:
            True if resolved, False if conflict not found
        """
        for i, conflict in enumerate(self.escalation_queue):
            if conflict.document_id == conflict_id:
                # Mark as resolved
                conflict.resolved = True
                conflict.resolved_by = "human"
                conflict.resolved_at = datetime.utcnow()

                # Remove from queue
                del self.escalation_queue[i]

                logger.info(f"Human resolved conflict: {conflict_id}")
                return True

        return False

    def get_conflict_history(self, limit: int = 100) -> List[KnowledgeConflict]:
        """Get conflict history for audit purposes."""
        return self.conflict_history[-limit:]
