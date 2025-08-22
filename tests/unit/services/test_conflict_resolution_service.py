"""Tests for ConflictResolutionService."""

import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from src.models.knowledge import (
    ConflictType,
    KnowledgeChunk,
    KnowledgeConflict,
    KnowledgeDomain,
    KnowledgeMetadata,
    MergeStrategy,
    SecurityClassification,
    SeverityLevel,
)
from src.services.conflict_resolution_service import ConflictResolutionService


@pytest.fixture
def mock_embedding_service():
    """Create a mock EmbeddingService."""
    service = AsyncMock()
    service.generate_embedding = AsyncMock(return_value=[0.1, 0.2, 0.3])
    return service


@pytest.fixture
def conflict_service(mock_embedding_service):
    """Create a ConflictResolutionService instance."""
    with patch(
        "src.services.conflict_resolution_service.EmbeddingService",
        return_value=mock_embedding_service,
    ):
        service = ConflictResolutionService()
        service.embedding_service = mock_embedding_service
        return service


def create_test_chunk(content="test content", author="user1", confidence=0.9):
    """Helper to create a test knowledge chunk."""
    return KnowledgeChunk(
        id=str(uuid.uuid4()),
        content=content,
        embedding=[0.1, 0.2, 0.3],
        metadata=KnowledgeMetadata(
            domain=KnowledgeDomain.GENERAL,
            tags=["test"],
            source="test",
            confidence=confidence,
            security_classification=SecurityClassification.PUBLIC,
        ),
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        author=author,
    )


class TestConflictResolutionService:
    """Test ConflictResolutionService functionality."""

    @pytest.mark.asyncio
    async def test_detect_no_conflict(self, conflict_service):
        """Test detecting no conflict between similar chunks."""
        existing = create_test_chunk("test content", "user1")
        incoming = create_test_chunk("test content", "user1")

        # Detect conflict
        conflict = await conflict_service.detect_conflict(existing, incoming)

        # Should detect no significant conflict
        assert conflict is None or conflict.severity == SeverityLevel.LOW

    @pytest.mark.asyncio
    async def test_detect_content_conflict(self, conflict_service):
        """Test detecting content conflict."""
        existing = create_test_chunk("original content", "user1")
        incoming = create_test_chunk("completely different content", "user2")

        # Detect conflict
        conflict = await conflict_service.detect_conflict(existing, incoming)

        # Should detect conflict
        assert conflict is not None
        assert conflict.conflict_type in [ConflictType.CONTENT, ConflictType.SEMANTIC]

    @pytest.mark.asyncio
    async def test_detect_temporal_conflict(self, conflict_service):
        """Test detecting temporal conflict."""
        # Create chunks with time difference
        existing = create_test_chunk("content A", "user1")
        existing.updated_at = datetime.utcnow() - timedelta(seconds=1)

        incoming = create_test_chunk("content B", "user2")
        incoming.created_at = datetime.utcnow()

        # Detect conflict
        conflict = await conflict_service.detect_conflict(existing, incoming)

        # Should detect some conflict
        assert conflict is not None

    @pytest.mark.asyncio
    async def test_resolve_conflict_append_strategy(self, conflict_service):
        """Test resolving conflict with append strategy."""
        existing = create_test_chunk("original content", "user1")
        incoming = create_test_chunk("new content", "user2")

        conflict = KnowledgeConflict(
            id=str(uuid.uuid4()),
            chunk_id=existing.id,
            existing_version=existing,
            incoming_version=incoming,
            conflict_type=ConflictType.CONTENT,
            severity=SeverityLevel.MEDIUM,
            detected_at=datetime.utcnow(),
        )

        # Resolve with append strategy
        resolved = await conflict_service.resolve_conflict(
            conflict, strategy=MergeStrategy.APPEND
        )

        # Verify
        assert resolved is not None
        assert "original content" in resolved.content
        assert "new content" in resolved.content

    @pytest.mark.asyncio
    async def test_resolve_conflict_vote_strategy(self, conflict_service):
        """Test resolving conflict with vote strategy."""
        existing = create_test_chunk("content", "user1", confidence=0.7)
        incoming = create_test_chunk("better content", "user2", confidence=0.95)

        conflict = KnowledgeConflict(
            id=str(uuid.uuid4()),
            chunk_id=existing.id,
            existing_version=existing,
            incoming_version=incoming,
            conflict_type=ConflictType.CONTENT,
            severity=SeverityLevel.MEDIUM,
            detected_at=datetime.utcnow(),
        )

        # Resolve with vote strategy (should pick higher confidence)
        resolved = await conflict_service.resolve_conflict(
            conflict, strategy=MergeStrategy.VOTE
        )

        # Verify - should pick incoming due to higher confidence
        assert resolved is not None
        assert resolved.content == "better content"

    @pytest.mark.asyncio
    async def test_resolve_conflict_conservative_strategy(self, conflict_service):
        """Test resolving conflict with conservative strategy."""
        existing = create_test_chunk("original", "user1")
        incoming = create_test_chunk("new", "user2")

        conflict = KnowledgeConflict(
            id=str(uuid.uuid4()),
            chunk_id=existing.id,
            existing_version=existing,
            incoming_version=incoming,
            conflict_type=ConflictType.CONTENT,
            severity=SeverityLevel.LOW,
            detected_at=datetime.utcnow(),
        )

        # Resolve with conservative strategy (keeps existing)
        resolved = await conflict_service.resolve_conflict(
            conflict, strategy=MergeStrategy.CONSERVATIVE
        )

        # Verify - should keep existing
        assert resolved is not None
        assert resolved.content == "original"

    @pytest.mark.asyncio
    async def test_resolve_conflict_aggressive_strategy(self, conflict_service):
        """Test resolving conflict with aggressive strategy."""
        existing = create_test_chunk("old", "user1")
        incoming = create_test_chunk("new", "user2")

        conflict = KnowledgeConflict(
            id=str(uuid.uuid4()),
            chunk_id=existing.id,
            existing_version=existing,
            incoming_version=incoming,
            conflict_type=ConflictType.CONTENT,
            severity=SeverityLevel.LOW,
            detected_at=datetime.utcnow(),
        )

        # Resolve with aggressive strategy (takes incoming)
        resolved = await conflict_service.resolve_conflict(
            conflict, strategy=MergeStrategy.AGGRESSIVE
        )

        # Verify - should take incoming
        assert resolved is not None
        assert resolved.content == "new"

    @pytest.mark.asyncio
    async def test_resolve_conflict_hybrid_strategy(self, conflict_service):
        """Test resolving conflict with hybrid strategy."""
        existing = create_test_chunk("original", "user1", confidence=0.8)
        incoming = create_test_chunk("updated", "user2", confidence=0.9)

        conflict = KnowledgeConflict(
            id=str(uuid.uuid4()),
            chunk_id=existing.id,
            existing_version=existing,
            incoming_version=incoming,
            conflict_type=ConflictType.CONTENT,
            severity=SeverityLevel.MEDIUM,
            detected_at=datetime.utcnow(),
        )

        # Resolve with hybrid strategy
        resolved = await conflict_service.resolve_conflict(
            conflict, strategy=MergeStrategy.HYBRID
        )

        # Verify
        assert resolved is not None
        # Hybrid should consider both confidence and content

    def test_calculate_similarity(self, conflict_service):
        """Test similarity calculation."""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        vec3 = [1.0, 0.0, 0.0]

        # Perpendicular vectors
        sim1 = conflict_service._calculate_similarity(vec1, vec2)
        assert sim1 < 0.5

        # Identical vectors
        sim2 = conflict_service._calculate_similarity(vec1, vec3)
        assert sim2 > 0.99

    def test_classify_severity(self, conflict_service):
        """Test severity classification."""
        # Low similarity = high severity
        severity1 = conflict_service._classify_severity(0.2, timedelta(hours=1))
        assert severity1 in [SeverityLevel.HIGH, SeverityLevel.CRITICAL]

        # High similarity = low severity
        severity2 = conflict_service._classify_severity(0.95, timedelta(hours=1))
        assert severity2 == SeverityLevel.LOW

    def test_needs_human_escalation(self, conflict_service):
        """Test human escalation detection."""
        conflict_critical = KnowledgeConflict(
            id=str(uuid.uuid4()),
            chunk_id="test",
            existing_version=create_test_chunk(),
            incoming_version=create_test_chunk(),
            conflict_type=ConflictType.CONTENT,
            severity=SeverityLevel.CRITICAL,
            detected_at=datetime.utcnow(),
        )

        # Critical severity should need escalation
        assert conflict_service._needs_human_escalation(conflict_critical) is True

        conflict_low = KnowledgeConflict(
            id=str(uuid.uuid4()),
            chunk_id="test",
            existing_version=create_test_chunk(),
            incoming_version=create_test_chunk(),
            conflict_type=ConflictType.CONTENT,
            severity=SeverityLevel.LOW,
            detected_at=datetime.utcnow(),
        )

        # Low severity should not need escalation
        assert conflict_service._needs_human_escalation(conflict_low) is False

    def test_get_escalation_queue(self, conflict_service):
        """Test getting escalation queue."""
        queue = conflict_service.get_escalation_queue()
        assert isinstance(queue, list)

    @pytest.mark.asyncio
    async def test_resolve_escalation(self, conflict_service):
        """Test resolving an escalated conflict."""
        conflict = KnowledgeConflict(
            id=str(uuid.uuid4()),
            chunk_id="test",
            existing_version=create_test_chunk(),
            incoming_version=create_test_chunk("human approved content"),
            conflict_type=ConflictType.CONTENT,
            severity=SeverityLevel.CRITICAL,
            detected_at=datetime.utcnow(),
        )

        # Add to escalation queue
        conflict_service.escalation_queue.append(conflict)

        # Resolve escalation
        resolved = await conflict_service.resolve_escalation(
            conflict.id, "human approved content"
        )

        # Verify
        assert resolved is not None
        assert resolved.content == "human approved content"
        assert len(conflict_service.escalation_queue) == 0

    def test_get_conflict_history(self, conflict_service):
        """Test getting conflict history."""
        chunk_id = str(uuid.uuid4())
        history = conflict_service.get_conflict_history(chunk_id)
        assert isinstance(history, list)
