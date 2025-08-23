"""Tests for conflict resolution service based on PRD requirements."""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

# Import the module to ensure it's loaded for coverage
import src.services.conflict_resolution_service

from src.services.conflict_resolution_service import ConflictResolutionService
from src.models.knowledge import (
    KnowledgeChunk,
    KnowledgeConflict,
    KnowledgeVersion,
    KnowledgeMetadata,
    KnowledgeDomain,
    SecurityClassification,
    ConflictType,
    SeverityLevel,
    MergeStrategy
)


class TestConflictResolutionServiceInitialization:
    """Test conflict resolution service initialization."""

    def test_initialization_with_defaults(self):
        """Test service initialization with default parameters."""
        service = ConflictResolutionService()
        
        assert service.embedding_service is not None
        assert service.similarity_thresholds[SeverityLevel.LOW] == (0.85, 0.90)
        assert service.similarity_thresholds[SeverityLevel.MEDIUM] == (0.90, 0.95)
        assert service.similarity_thresholds[SeverityLevel.HIGH] == (0.95, 0.98)
        assert service.similarity_thresholds[SeverityLevel.CRITICAL] == (0.98, 1.0)
        
        assert service.strategy_rules[SeverityLevel.LOW] == MergeStrategy.APPEND
        assert service.strategy_rules[SeverityLevel.MEDIUM] == MergeStrategy.VOTE
        assert service.strategy_rules[SeverityLevel.HIGH] == MergeStrategy.HYBRID
        assert service.strategy_rules[SeverityLevel.CRITICAL] == MergeStrategy.HYBRID
        
        assert service.escalation_queue == []
        assert service.conflict_history == []

    def test_initialization_with_custom_embedding_service(self):
        """Test service initialization with custom embedding service."""
        mock_embedding_service = Mock()
        service = ConflictResolutionService(embedding_service=mock_embedding_service)
        
        assert service.embedding_service == mock_embedding_service


class TestConflictDetection:
    """Test conflict detection functionality."""

    @pytest.fixture
    def service(self):
        """Create a conflict resolution service with mocked embedding service."""
        mock_embedding_service = Mock()
        return ConflictResolutionService(embedding_service=mock_embedding_service)

    @pytest.fixture
    def sample_chunks(self):
        """Create sample knowledge chunks for testing."""
        base_time = datetime.utcnow()
        
        existing = KnowledgeChunk(
            id="chunk-1",
            content="Original content about authentication",
            embedding=[0.1, 0.2, 0.3, 0.4],
            metadata=KnowledgeMetadata(
                domain=KnowledgeDomain.TECHNICAL,
                document_id="doc-1",
                agent_attribution="orchestrator",
                confidence_score=0.8,
                security_classification=SecurityClassification.INTERNAL
            ),
            version=1,
            created_at=base_time,
            updated_at=base_time,
            author="orchestrator"
        )
        
        proposed = KnowledgeChunk(
            id="chunk-1",
            content="Updated content about authentication with new details",
            embedding=[0.15, 0.25, 0.35, 0.45],
            metadata=KnowledgeMetadata(
                domain=KnowledgeDomain.TECHNICAL,
                document_id="doc-1",
                agent_attribution="developer",
                confidence_score=0.9,
                security_classification=SecurityClassification.INTERNAL
            ),
            version=2,
            created_at=base_time,
            updated_at=base_time + timedelta(minutes=2),
            author="developer"
        )
        
        return existing, proposed

    @pytest.mark.asyncio
    async def test_detect_conflict_no_conflict_different_content(self, service, sample_chunks):
        """Test conflict detection when content is sufficiently different."""
        existing, proposed = sample_chunks
        
        # Make content very different (low similarity)
        proposed.content = "Completely different content about databases"
        proposed.embedding = [0.9, 0.8, 0.7, 0.6]  # Very different embedding
        
        # Mock similarity calculation to return very low similarity
        with patch.object(service, '_calculate_similarity', return_value=0.3):
            conflict = await service.detect_conflict(existing, proposed)
        
        assert conflict is None

    @pytest.mark.asyncio
    async def test_detect_conflict_high_similarity_concurrent(self, service, sample_chunks):
        """Test conflict detection with high similarity and concurrent edits."""
        existing, proposed = sample_chunks
        
        # Make edits concurrent (within 5 minutes)
        proposed.updated_at = existing.updated_at + timedelta(minutes=2)
        
        # Mock high similarity
        with patch.object(service, '_calculate_similarity', return_value=0.92):
            conflict = await service.detect_conflict(existing, proposed)
        
        assert conflict is not None
        assert conflict.chunk_id == "chunk-1"
        assert conflict.similarity_score == 0.92
        assert conflict.severity == SeverityLevel.MEDIUM

    @pytest.mark.asyncio
    async def test_detect_conflict_generates_embeddings_if_missing(self, service, sample_chunks):
        """Test that embeddings are generated if missing."""
        existing, proposed = sample_chunks
        existing.embedding = None
        proposed.embedding = None
        
        service.embedding_service.generate_embedding = AsyncMock(
            side_effect=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        )
        
        with patch.object(service, '_calculate_similarity', return_value=0.92):
            conflict = await service.detect_conflict(existing, proposed)
        
        assert service.embedding_service.generate_embedding.call_count == 2
        assert existing.embedding == [0.1, 0.2, 0.3]
        assert proposed.embedding == [0.4, 0.5, 0.6]

    def test_classify_severity_levels(self, service):
        """Test severity classification based on similarity scores."""
        assert service._classify_severity(0.87) == SeverityLevel.LOW
        assert service._classify_severity(0.92) == SeverityLevel.MEDIUM
        assert service._classify_severity(0.96) == SeverityLevel.HIGH
        assert service._classify_severity(0.99) == SeverityLevel.CRITICAL


class TestSimilarityCalculation:
    """Test similarity calculation functionality."""

    @pytest.fixture
    def service(self):
        """Create a conflict resolution service."""
        return ConflictResolutionService()

    def test_calculate_similarity_identical_vectors(self, service):
        """Test similarity calculation with identical vectors."""
        embedding_a = [1.0, 0.0, 0.0]
        embedding_b = [1.0, 0.0, 0.0]
        
        similarity = service._calculate_similarity(embedding_a, embedding_b)
        assert abs(similarity - 1.0) < 0.001

    def test_calculate_similarity_orthogonal_vectors(self, service):
        """Test similarity calculation with orthogonal vectors."""
        embedding_a = [1.0, 0.0, 0.0]
        embedding_b = [0.0, 1.0, 0.0]
        
        similarity = service._calculate_similarity(embedding_a, embedding_b)
        assert abs(similarity - 0.0) < 0.001

    def test_calculate_similarity_empty_vectors(self, service):
        """Test similarity calculation with empty vectors."""
        similarity = service._calculate_similarity([], [])
        assert similarity == 0.0

    def test_calculate_similarity_zero_magnitude(self, service):
        """Test similarity calculation with zero magnitude vectors."""
        embedding_a = [0.0, 0.0, 0.0]
        embedding_b = [1.0, 0.0, 0.0]
        
        similarity = service._calculate_similarity(embedding_a, embedding_b)
        assert similarity == 0.0


class TestConflictResolution:
    """Test conflict resolution strategies."""

    @pytest.fixture
    def service(self):
        """Create a conflict resolution service."""
        mock_embedding_service = Mock()
        return ConflictResolutionService(embedding_service=mock_embedding_service)

    @pytest.fixture
    def sample_conflict(self):
        """Create a sample conflict for testing."""
        base_time = datetime.utcnow()
        
        # Create proper KnowledgeChunk objects
        existing_chunk = KnowledgeChunk(
            id="chunk-1",
            content="Original authentication implementation",
            embedding=[0.1, 0.2, 0.3],
            metadata=KnowledgeMetadata(
                domain=KnowledgeDomain.TECHNICAL,
                confidence_score=0.8,
                agent_attribution="orchestrator"
            ),
            version=1,
            created_at=base_time,
            updated_at=base_time,
            author="orchestrator"
        )
        
        incoming_chunk = KnowledgeChunk(
            id="chunk-1",
            content="Enhanced authentication with OAuth support",
            embedding=[0.15, 0.25, 0.35],
            metadata=KnowledgeMetadata(
                domain=KnowledgeDomain.TECHNICAL,
                confidence_score=0.9,
                agent_attribution="developer"
            ),
            version=2,
            created_at=base_time + timedelta(minutes=2),
            updated_at=base_time + timedelta(minutes=2),
            author="developer"
        )
        
        version_a = KnowledgeVersion(
            document_id="doc-1",
            version=1,
            content="Original authentication implementation",
            metadata={
                "confidence_score": 0.8,
                "agent_attribution": "orchestrator",
                "knowledge_domain": "technical"
            },
            created_at=base_time,
            agent_attribution="orchestrator"
        )
        
        version_b = KnowledgeVersion(
            document_id="doc-1",
            version=2,
            content="Enhanced authentication with OAuth support",
            metadata={
                "confidence_score": 0.9,
                "agent_attribution": "developer",
                "knowledge_domain": "technical"
            },
            created_at=base_time + timedelta(minutes=2),
            agent_attribution="developer"
        )
        
        return KnowledgeConflict(
            id="conflict-1",
            chunk_id="chunk-1",
            existing_version=existing_chunk,
            incoming_version=incoming_chunk,
            conflict_type=ConflictType.CONTENT,
            severity=SeverityLevel.MEDIUM,
            detected_at=base_time,
            similarity_score=0.92,
            version_a=version_a,
            version_b=version_b
        )

    @pytest.mark.asyncio
    async def test_resolve_conflict_auto_strategy_selection(self, service, sample_conflict):
        """Test automatic strategy selection based on severity."""
        sample_conflict.similarity_score = 0.87  # LOW severity
        
        with patch.object(service, '_merge_append', return_value=Mock()) as mock_append:
            await service.resolve_conflict(sample_conflict)
            mock_append.assert_called_once_with(sample_conflict)

    @pytest.mark.asyncio
    async def test_merge_append_strategy(self, service, sample_conflict):
        """Test append merge strategy."""
        result = await service._merge_append(sample_conflict)
        
        assert "Original authentication implementation" in result.content
        assert "Enhanced authentication with OAuth support" in result.content
        assert "Additional Information" in result.content
        # Note: merge_strategy is not stored in KnowledgeMetadata, just verify content
        assert "Original authentication implementation" in result.content
        assert "Enhanced authentication with OAuth support" in result.content
        assert result.version == 3  # max(1, 2) + 1

    @pytest.mark.asyncio
    async def test_merge_vote_strategy_higher_confidence_wins(self, service, sample_conflict):
        """Test vote strategy selects higher confidence version."""
        # Version B has higher confidence (0.9 vs 0.8)
        result = await service._merge_vote(sample_conflict)
        
        assert result.content == "Enhanced authentication with OAuth support"
        # Note: merge_strategy is not stored in KnowledgeMetadata, just verify content and version
        assert result.version == 3
        assert result.author == "developer"  # Should be the winner's author

    @pytest.mark.asyncio
    async def test_merge_hybrid_strategy_with_escalation(self, service, sample_conflict):
        """Test hybrid strategy with human escalation."""
        sample_conflict.severity = SeverityLevel.CRITICAL
        
        with patch.object(service, '_needs_human_escalation', return_value=True), \
             patch.object(service, '_merge_conservative', return_value=Mock()) as mock_conservative:
            
            result = await service._merge_hybrid(sample_conflict)
            
            # Should add to escalation queue and use conservative fallback
            assert len(service.escalation_queue) == 1
            assert service.escalation_queue[0] == sample_conflict
            mock_conservative.assert_called_once_with(sample_conflict)

    def test_needs_human_escalation(self, service, sample_conflict):
        """Test human escalation decision logic."""
        sample_conflict.severity = SeverityLevel.CRITICAL
        assert service._needs_human_escalation(sample_conflict) is True
        
        sample_conflict.severity = SeverityLevel.HIGH
        assert service._needs_human_escalation(sample_conflict) is False


class TestHumanEscalation:
    """Test human escalation functionality."""

    @pytest.fixture
    def service(self):
        """Create a conflict resolution service."""
        return ConflictResolutionService()

    @pytest.fixture
    def sample_conflict(self):
        """Create a sample conflict for testing."""
        existing_chunk = KnowledgeChunk(
            id="chunk-1",
            content="Original content",
            embedding=[0.1, 0.2, 0.3],
            metadata=KnowledgeMetadata(
                domain=KnowledgeDomain.TECHNICAL,
                confidence_score=0.8,
                agent_attribution="orchestrator"
            ),
            version=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            author="orchestrator"
        )
        
        return KnowledgeConflict(
            id="conflict-1",
            chunk_id="chunk-1",
            existing_version=existing_chunk,
            incoming_version=existing_chunk,  # Same for simplicity
            conflict_type=ConflictType.CONTENT,
            severity=SeverityLevel.CRITICAL,
            detected_at=datetime.utcnow(),
            similarity_score=0.99
        )

    def test_get_escalation_queue_empty(self, service):
        """Test getting empty escalation queue."""
        queue = service.get_escalation_queue()
        assert queue == []

    @pytest.mark.asyncio
    async def test_resolve_escalation_success(self, service, sample_conflict):
        """Test successful escalation resolution."""
        service.escalation_queue.append(sample_conflict)
        
        resolved_chunk = await service.resolve_escalation(
            "conflict-1", 
            "Human-resolved content"
        )
        
        assert resolved_chunk is not None
        assert resolved_chunk.content == "Human-resolved content"
        assert resolved_chunk.author == "human"
        assert len(service.escalation_queue) == 0  # Removed from queue

    @pytest.mark.asyncio
    async def test_resolve_escalation_not_found(self, service):
        """Test escalation resolution with non-existent conflict."""
        resolved_chunk = await service.resolve_escalation(
            "non-existent", 
            "Some content"
        )
        
        assert resolved_chunk is None


class TestMergeStrategies:
    """Test comprehensive merge strategy functionality."""

    @pytest.fixture
    def service(self):
        """Create a conflict resolution service."""
        mock_embedding_service = Mock()
        return ConflictResolutionService(embedding_service=mock_embedding_service)

    @pytest.fixture
    def complex_conflict(self):
        """Create a more complex conflict for testing merge strategies."""
        base_time = datetime.utcnow()
        
        version_a = KnowledgeVersion(
            document_id="doc-complex",
            version=1,
            content="Authentication system:\n- JWT tokens\n- Basic validation\n- User roles",
            metadata={
                "confidence_score": 0.85,
                "agent_attribution": "orchestrator",
                "knowledge_domain": "security"
            },
            created_at=base_time,
            agent_attribution="orchestrator"
        )
        
        version_b = KnowledgeVersion(
            document_id="doc-complex",
            version=2,
            content="Authentication system:\n- OAuth2 support\n- Advanced validation\n- Role-based access control\n- Session management",
            metadata={
                "confidence_score": 0.75,
                "agent_attribution": "developer",
                "knowledge_domain": "security"
            },
            created_at=base_time + timedelta(minutes=3),
            agent_attribution="developer"
        )
        
        return KnowledgeConflict(
            id="complex-conflict",
            chunk_id="chunk-complex",
            existing_version=Mock(),  # Not used in these specific merge tests
            incoming_version=Mock(),  # Not used in these specific merge tests
            conflict_type=ConflictType.CONTENT,
            severity=SeverityLevel.HIGH,
            detected_at=base_time,
            similarity_score=0.96,
            version_a=version_a,
            version_b=version_b
        )

    @pytest.mark.asyncio
    async def test_merge_hybrid_strategy_intelligent_merge(self, service, complex_conflict):
        """Test hybrid strategy with intelligent line-by-line merging."""
        complex_conflict.severity = SeverityLevel.HIGH  # Won't escalate
        
        with patch.object(service, '_needs_human_escalation', return_value=False):
            result = await service._merge_hybrid(complex_conflict)
        
        assert result is not None
        assert "Authentication system:" in result.content
        assert "JWT tokens" in result.content or "OAuth2 support" in result.content
        assert "From Version" in result.content  # Should show merged sections
        assert result.version == 3  # max(1, 2) + 1

    @pytest.mark.asyncio
    async def test_merge_vote_strategy_lower_confidence_wins(self, service, complex_conflict):
        """Test vote strategy when version A has higher confidence."""
        # Swap confidence so version A wins
        complex_conflict.version_a.metadata["confidence_score"] = 0.95
        complex_conflict.version_b.metadata["confidence_score"] = 0.70
        
        result = await service._merge_vote(complex_conflict)
        
        # Should select version A (higher confidence)
        assert "JWT tokens" in result.content
        assert result.author == "orchestrator"
        assert result.version == 3

    @pytest.mark.asyncio
    async def test_merge_conservative_strategy(self, service, complex_conflict):
        """Test conservative merge strategy."""
        result = await service._merge_conservative(complex_conflict)
        
        # Should return version A unchanged
        assert result.content == complex_conflict.version_a.content
        assert result.version == complex_conflict.version_a.version

    def test_strategy_selection_for_all_severities(self, service):
        """Test automatic strategy selection for all severity levels."""
        # Test LOW severity -> APPEND
        assert service.strategy_rules[SeverityLevel.LOW] == MergeStrategy.APPEND
        
        # Test MEDIUM severity -> VOTE
        assert service.strategy_rules[SeverityLevel.MEDIUM] == MergeStrategy.VOTE
        
        # Test HIGH severity -> HYBRID
        assert service.strategy_rules[SeverityLevel.HIGH] == MergeStrategy.HYBRID
        
        # Test CRITICAL severity -> HYBRID
        assert service.strategy_rules[SeverityLevel.CRITICAL] == MergeStrategy.HYBRID

    @pytest.mark.asyncio
    async def test_resolve_conflict_with_explicit_strategies(self, service, complex_conflict):
        """Test conflict resolution with explicitly specified strategies."""
        # Test CONSERVATIVE strategy
        result = await service.resolve_conflict(complex_conflict, MergeStrategy.CONSERVATIVE)
        assert result.content == complex_conflict.version_a.content
        
        # Test AGGRESSIVE strategy
        result = await service.resolve_conflict(complex_conflict, MergeStrategy.AGGRESSIVE)
        assert result.content == complex_conflict.version_b.content

    @pytest.mark.asyncio
    async def test_resolve_conflict_unknown_strategy(self, service, complex_conflict):
        """Test conflict resolution with unknown strategy raises error."""
        with pytest.raises(ValueError, match="Unknown merge strategy"):
            await service.resolve_conflict(complex_conflict, "unknown_strategy")


class TestConflictTypeDetection:
    """Test conflict type detection functionality."""

    @pytest.fixture
    def service(self):
        """Create a conflict resolution service."""
        return ConflictResolutionService()

    def test_determine_conflict_type_content_only(self, service):
        """Test conflict type detection for content-only changes."""
        existing = KnowledgeChunk(
            id="chunk-1",
            content="Original content",
            embedding=[],
            metadata=KnowledgeMetadata(
                domain=KnowledgeDomain.TECHNICAL,
                confidence_score=0.8,
                agent_attribution="orchestrator",
                knowledge_domain="technical"
            ),
            version=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            author="orchestrator"
        )
        
        proposed = KnowledgeChunk(
            id="chunk-1",
            content="Updated content",  # Content changed
            embedding=[],
            metadata=KnowledgeMetadata(
                domain=KnowledgeDomain.TECHNICAL,
                confidence_score=0.8,  # Same metadata
                agent_attribution="orchestrator",
                knowledge_domain="technical"
            ),
            version=2,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            author="orchestrator"
        )
        
        conflict_type = service._determine_conflict_type(existing, proposed)
        assert conflict_type == "content"

    def test_determine_conflict_type_metadata_only(self, service):
        """Test conflict type detection for metadata-only changes."""
        existing = KnowledgeChunk(
            id="chunk-1",
            content="Same content",
            embedding=[],
            metadata=KnowledgeMetadata(
                domain=KnowledgeDomain.TECHNICAL,
                confidence_score=0.8,
                agent_attribution="orchestrator",
                knowledge_domain="technical"
            ),
            version=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            author="orchestrator"
        )
        
        proposed = KnowledgeChunk(
            id="chunk-1",
            content="Same content",  # Content same
            embedding=[],
            metadata=KnowledgeMetadata(
                domain=KnowledgeDomain.TECHNICAL,
                confidence_score=0.9,  # Confidence changed
                agent_attribution="orchestrator",
                knowledge_domain="technical"
            ),
            version=2,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            author="orchestrator"
        )
        
        conflict_type = service._determine_conflict_type(existing, proposed)
        assert conflict_type == "metadata"

    def test_determine_conflict_type_both(self, service):
        """Test conflict type detection for both content and metadata changes."""
        existing = KnowledgeChunk(
            id="chunk-1",
            content="Original content",
            embedding=[],
            metadata=KnowledgeMetadata(
                domain=KnowledgeDomain.TECHNICAL,
                confidence_score=0.8,
                agent_attribution="orchestrator",
                knowledge_domain="technical"
            ),
            version=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            author="orchestrator"
        )
        
        proposed = KnowledgeChunk(
            id="chunk-1",
            content="Updated content",  # Content changed
            embedding=[],
            metadata=KnowledgeMetadata(
                domain=KnowledgeDomain.TECHNICAL,
                confidence_score=0.9,  # Confidence changed
                agent_attribution="developer",  # Agent changed
                knowledge_domain="security"  # Domain changed
            ),
            version=2,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            author="developer"
        )
        
        conflict_type = service._determine_conflict_type(existing, proposed)
        assert conflict_type == "both"

    def test_determine_conflict_type_unknown(self, service):
        """Test conflict type detection when no changes detected."""
        chunk = KnowledgeChunk(
            id="chunk-1",
            content="Same content",
            embedding=[],
            metadata=KnowledgeMetadata(
                domain=KnowledgeDomain.TECHNICAL,
                confidence_score=0.8,
                agent_attribution="orchestrator",
                knowledge_domain="technical"
            ),
            version=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            author="orchestrator"
        )
        
        conflict_type = service._determine_conflict_type(chunk, chunk)
        assert conflict_type == "unknown"


class TestUtilityMethods:
    """Test utility methods and edge cases."""

    @pytest.fixture
    def service(self):
        """Create a conflict resolution service."""
        return ConflictResolutionService()

    def test_classify_severity_edge_cases(self, service):
        """Test severity classification edge cases."""
        # Test boundary conditions - values outside thresholds default to CRITICAL
        assert service._classify_severity(0.849) == SeverityLevel.CRITICAL  # Below all thresholds -> CRITICAL
        assert service._classify_severity(0.851) == SeverityLevel.LOW  # Within LOW threshold
        assert service._classify_severity(0.999) == SeverityLevel.CRITICAL  # Very high similarity
        assert service._classify_severity(1.0) == SeverityLevel.CRITICAL  # Perfect similarity
        
        # Test edge of ranges
        assert service._classify_severity(0.85) == SeverityLevel.LOW  # LOW threshold start
        assert service._classify_severity(0.90) == SeverityLevel.MEDIUM  # MEDIUM threshold start
        assert service._classify_severity(0.95) == SeverityLevel.HIGH  # HIGH threshold start
        assert service._classify_severity(0.98) == SeverityLevel.CRITICAL  # CRITICAL threshold start

    def test_chunk_to_version_conversion(self, service):
        """Test conversion from knowledge chunk to version."""
        chunk = KnowledgeChunk(
            id="chunk-1",
            content="Test content",
            embedding=[0.1, 0.2, 0.3],
            metadata=KnowledgeMetadata(
                domain=KnowledgeDomain.TECHNICAL,
                document_id="doc-1",
                confidence_score=0.8,
                agent_attribution="test-agent",
                knowledge_domain="technical"
            ),
            version=5,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            author="test-agent"
        )
        
        version = service._chunk_to_version(chunk)
        
        assert version.document_id == "doc-1"
        assert version.version == 5
        assert version.content == "Test content"
        assert version.agent_attribution == "test-agent"

    def test_version_to_chunk_conversion(self, service):
        """Test conversion from version to knowledge chunk."""
        version = KnowledgeVersion(
            document_id="doc-1",
            version=5,
            content="Test content",
            metadata={
                "confidence_score": 0.8,
                "agent_attribution": "test-agent",
                "knowledge_domain": "technical"
            },
            created_at=datetime.utcnow(),
            agent_attribution="test-agent"
        )
        
        chunk = service._version_to_chunk(version)
        
        assert chunk.id == "doc-1"
        assert chunk.version == 5
        assert chunk.content == "Test content"
        assert chunk.author == "test-agent"


class TestConflictHistory:
    """Test conflict history and audit trail functionality."""

    @pytest.fixture
    def service(self):
        """Create a conflict resolution service."""
        return ConflictResolutionService()

    @pytest.fixture
    def sample_conflicts(self, service):
        """Create sample conflicts for history testing."""
        conflicts = []
        base_time = datetime.utcnow()
        
        for i in range(5):
            conflict = KnowledgeConflict(
                id=f"conflict-{i}",
                chunk_id=f"chunk-{i}",
                existing_version=Mock(),
                incoming_version=Mock(),
                conflict_type=ConflictType.CONTENT,
                severity=SeverityLevel.MEDIUM,
                detected_at=base_time + timedelta(minutes=i),
                similarity_score=0.90 + (i * 0.01)
            )
            conflicts.append(conflict)
            service.conflict_history.append(conflict)
        
        return conflicts

    def test_get_conflict_history_default_limit(self, service, sample_conflicts):
        """Test getting conflict history with default limit."""
        history = service.get_conflict_history()
        
        assert len(history) == 5  # All conflicts within default limit
        # Should return most recent conflicts (LIFO order maintained)
        assert history[-1].id == "conflict-4"

    def test_get_conflict_history_custom_limit(self, service, sample_conflicts):
        """Test getting conflict history with custom limit."""
        history = service.get_conflict_history(limit=3)
        
        assert len(history) == 3  # Limited to 3
        # Should return last 3 conflicts
        assert history[-1].id == "conflict-4"
        assert history[-2].id == "conflict-3"
        assert history[-3].id == "conflict-2"

    def test_get_conflict_history_exceeds_available(self, service, sample_conflicts):
        """Test getting conflict history when limit exceeds available."""
        history = service.get_conflict_history(limit=10)
        
        assert len(history) == 5  # Only 5 available
        assert history[-1].id == "conflict-4"

    def test_get_conflict_history_empty(self, service):
        """Test getting conflict history when empty."""
        history = service.get_conflict_history()
        assert history == []


class TestPRDRequirementsIntegration:
    """Test integration with PRD Story 1.5 requirements."""

    @pytest.fixture
    def service(self):
        """Create a conflict resolution service."""
        mock_embedding_service = Mock()
        return ConflictResolutionService(embedding_service=mock_embedding_service)

    @pytest.mark.asyncio
    async def test_concurrent_access_control(self, service):
        """Test concurrent access control (PRD requirement 1)."""
        base_time = datetime.utcnow()
        
        # Create two versions updated within 5 minutes (concurrent)
        existing = KnowledgeChunk(
            id="chunk-1",
            content="Original implementation",
            embedding=[0.1, 0.2, 0.3],
            metadata=KnowledgeMetadata(
                domain=KnowledgeDomain.TECHNICAL,
                confidence_score=0.8,
                agent_attribution="orchestrator"
            ),
            version=1,
            created_at=base_time,
            updated_at=base_time,
            author="orchestrator"
        )
        
        proposed = KnowledgeChunk(
            id="chunk-1",
            content="Concurrent implementation update",
            embedding=[0.15, 0.25, 0.35],
            metadata=KnowledgeMetadata(
                domain=KnowledgeDomain.TECHNICAL,
                confidence_score=0.9,
                agent_attribution="developer"
            ),
            version=2,
            created_at=base_time,
            updated_at=base_time + timedelta(minutes=3),  # Within 5 minutes
            author="developer"
        )
        
        # Mock high similarity
        with patch.object(service, '_calculate_similarity', return_value=0.88):
            conflict = await service.detect_conflict(existing, proposed)
        
        # Should detect conflict for concurrent access
        assert conflict is not None
        assert conflict.similarity_score == 0.88

    def test_edit_tracking_agent_attribution(self, service):
        """Test edit tracking with agent attribution (PRD requirement 2)."""
        base_time = datetime.utcnow()
        
        version_a = KnowledgeVersion(
            document_id="doc-1",
            version=1,
            content="Original content",
            metadata={"agent_attribution": "orchestrator"},
            created_at=base_time,
            agent_attribution="orchestrator"
        )
        
        version_b = KnowledgeVersion(
            document_id="doc-1", 
            version=2,
            content="Modified content",
            metadata={"agent_attribution": "developer"},
            created_at=base_time + timedelta(minutes=2),
            agent_attribution="developer"
        )
        
        conflict = KnowledgeConflict(
            id="conflict-1",
            chunk_id="chunk-1",
            existing_version=Mock(),
            incoming_version=Mock(),
            conflict_type=ConflictType.CONTENT,
            severity=SeverityLevel.MEDIUM,
            detected_at=base_time,
            similarity_score=0.92,
            version_a=version_a,
            version_b=version_b
        )
        
        # Should track which agents made which modifications
        assert conflict.version_a.agent_attribution == "orchestrator"
        assert conflict.version_b.agent_attribution == "developer"

    def test_audit_trail_timestamps(self, service):
        """Test complete audit trail with timestamps (PRD requirement 6)."""
        base_time = datetime.utcnow()
        
        conflict = KnowledgeConflict(
            id="audit-conflict",
            chunk_id="chunk-audit",
            existing_version=Mock(),
            incoming_version=Mock(),
            conflict_type=ConflictType.CONTENT,
            severity=SeverityLevel.HIGH,
            detected_at=base_time,
            similarity_score=0.96
        )
        
        # Add to history (simulating detection)
        service.conflict_history.append(conflict)
        
        # Verify audit trail
        history = service.get_conflict_history()
        assert len(history) == 1
        assert history[0].detected_at == base_time
        assert history[0].id == "audit-conflict"
        assert history[0].similarity_score == 0.96

    @pytest.mark.asyncio
    async def test_rollback_capability_via_conservative_merge(self, service):
        """Test rollback capability via conservative merge (PRD requirement 5)."""
        version_a = KnowledgeVersion(
            document_id="doc-1",
            version=1,
            content="Stable version",
            metadata={"confidence_score": 0.9},
            created_at=datetime.utcnow(),
            agent_attribution="orchestrator"
        )
        
        version_b = KnowledgeVersion(
            document_id="doc-1",
            version=2,
            content="Unstable version",
            metadata={"confidence_score": 0.6},
            created_at=datetime.utcnow(),
            agent_attribution="developer"
        )
        
        conflict = KnowledgeConflict(
            id="rollback-conflict",
            chunk_id="chunk-rollback",
            existing_version=Mock(),
            incoming_version=Mock(),
            conflict_type=ConflictType.CONTENT,
            severity=SeverityLevel.MEDIUM,
            detected_at=datetime.utcnow(),
            similarity_score=0.92,
            version_a=version_a,
            version_b=version_b
        )
        
        # Use conservative strategy (rollback to version A)
        result = await service.resolve_conflict(conflict, MergeStrategy.CONSERVATIVE)
        
        # Should rollback to stable version
        assert result.content == "Stable version"
        assert result.version == version_a.version


class TestMissingCoverageLines:
    """Test specific code paths that were missing coverage."""

    @pytest.fixture
    def service(self):
        """Create a conflict resolution service with real embedding service."""
        # Use real embedding service to avoid over-mocking
        return ConflictResolutionService()

    @pytest.mark.asyncio
    async def test_detect_conflict_no_conflict_low_similarity(self, service):
        """Test no conflict detection with very low similarity - covers line 104."""
        base_time = datetime.utcnow()
        
        # Create chunks with very different content/embeddings  
        existing = KnowledgeChunk(
            id="chunk-1",
            content="Authentication system using JWT tokens",
            embedding=[0.1, 0.2, 0.3, 0.4],
            metadata=KnowledgeMetadata(
                domain=KnowledgeDomain.TECHNICAL,
                document_id="doc-1", 
                agent_attribution="orchestrator",
                confidence_score=0.8,
                security_classification=SecurityClassification.INTERNAL
            ),
            version=1,
            created_at=base_time,
            updated_at=base_time,
            author="orchestrator"
        )
        
        proposed = KnowledgeChunk(
            id="chunk-1", 
            content="Database migration scripts for PostgreSQL",  # Very different content
            embedding=[0.9, 0.8, 0.7, 0.6],  # Very different embedding
            metadata=KnowledgeMetadata(
                domain=KnowledgeDomain.TECHNICAL,
                document_id="doc-1",
                agent_attribution="developer", 
                confidence_score=0.9,
                security_classification=SecurityClassification.INTERNAL
            ),
            version=2,
            created_at=base_time + timedelta(hours=2),  # Not concurrent  
            updated_at=base_time + timedelta(hours=2),
            author="developer"
        )
        
        # This should trigger line 104: return None (no conflict due to low similarity + not concurrent)
        conflict = await service.detect_conflict(existing, proposed)
        assert conflict is None

    @pytest.mark.asyncio
    async def test_resolve_conflict_vote_strategy_execution(self, service):
        """Test resolve_conflict calling _merge_vote - covers line 157."""
        base_time = datetime.utcnow()
        
        # Create a conflict that will use VOTE strategy (medium severity)
        version_a = KnowledgeVersion(
            document_id="doc-1",
            version=1,
            content="Original authentication docs",
            metadata={"confidence_score": 0.7, "agent_attribution": "orchestrator"},
            created_at=base_time,
            agent_attribution="orchestrator"
        )
        
        version_b = KnowledgeVersion(
            document_id="doc-1", 
            version=2,
            content="Updated authentication with OAuth",
            metadata={"confidence_score": 0.9, "agent_attribution": "developer"},
            created_at=base_time + timedelta(minutes=2), 
            agent_attribution="developer"
        )
        
        conflict = KnowledgeConflict(
            id=str(uuid.uuid4()),
            chunk_id="doc-1",
            existing_version=None,
            incoming_version=version_b,
            version_a=version_a,
            version_b=version_b,
            similarity_score=0.92,
            severity=SeverityLevel.MEDIUM,
            conflict_type="content",
            detected_at=base_time,
            resolved=False
        )
        
        # This should trigger line 157: return await self._merge_vote(conflict)
        result = await service.resolve_conflict(conflict)
        assert result is not None
        assert result.content == "Updated authentication with OAuth"  # Higher confidence wins
        
    @pytest.mark.asyncio
    async def test_resolve_conflict_hybrid_strategy_execution(self, service):
        """Test resolve_conflict calling _merge_hybrid - covers line 159."""
        base_time = datetime.utcnow()
        
        # Create a conflict that will use HYBRID strategy (high severity)
        version_a = KnowledgeVersion(
            document_id="doc-1",
            version=1, 
            content="Security implementation v1",
            metadata={"confidence_score": 0.85, "agent_attribution": "security-dev"},
            created_at=base_time,
            agent_attribution="security-dev"
        )
        
        version_b = KnowledgeVersion(
            document_id="doc-1",
            version=2,
            content="Enhanced security implementation v2", 
            metadata={"confidence_score": 0.88, "agent_attribution": "lead-dev"},
            created_at=base_time + timedelta(minutes=1),
            agent_attribution="lead-dev"
        )
        
        conflict = KnowledgeConflict(
            id=str(uuid.uuid4()),
            chunk_id="doc-1",
            existing_version=None,
            incoming_version=version_b,
            version_a=version_a,
            version_b=version_b,
            similarity_score=0.96,
            severity=SeverityLevel.HIGH,
            conflict_type="content",
            detected_at=base_time,
            resolved=False
        )
        
        # This should trigger line 159: return await self._merge_hybrid(conflict)  
        result = await service.resolve_conflict(conflict)
        assert result is not None
        # Hybrid merge should intelligently combine content
        assert "security" in result.content.lower()