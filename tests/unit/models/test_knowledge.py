"""Tests for knowledge management data models."""

import uuid
from datetime import datetime, timedelta

import pytest

from orchestra.models.knowledge import (
    ConflictType,
    KnowledgeChunk,
    KnowledgeConflict,
    KnowledgeDomain,
    KnowledgeLock,
    KnowledgeMetadata,
    KnowledgeQuery,
    KnowledgeVersion,
    MergeStrategy,
    SecurityClassification,
    SeverityLevel,
)


class TestEnums:
    """Test knowledge management enums."""

    def test_conflict_type_enum(self):
        """Test ConflictType enum values."""
        assert ConflictType.CONTENT == "content"
        assert ConflictType.METADATA == "metadata"
        assert ConflictType.SEMANTIC == "semantic"
        assert ConflictType.TEMPORAL == "temporal"
        assert ConflictType.BOTH == "both"

        # Test enum is string-based
        assert isinstance(ConflictType.CONTENT, str)
        # Note: str() returns the full enum name, not just the value
        assert str(ConflictType.CONTENT) == "ConflictType.CONTENT"

    def test_severity_level_enum(self):
        """Test SeverityLevel enum values."""
        assert SeverityLevel.LOW == "low"
        assert SeverityLevel.MEDIUM == "medium"
        assert SeverityLevel.HIGH == "high"
        assert SeverityLevel.CRITICAL == "critical"

        # Test enum is string-based
        assert isinstance(SeverityLevel.LOW, str)
        assert str(SeverityLevel.LOW) == "SeverityLevel.LOW"

    def test_merge_strategy_enum(self):
        """Test MergeStrategy enum values."""
        assert MergeStrategy.APPEND == "append"
        assert MergeStrategy.VOTE == "vote"
        assert MergeStrategy.HYBRID == "hybrid"
        assert MergeStrategy.CONSERVATIVE == "conservative"
        assert MergeStrategy.AGGRESSIVE == "aggressive"

        # Test enum is string-based
        assert isinstance(MergeStrategy.APPEND, str)
        assert str(MergeStrategy.APPEND) == "MergeStrategy.APPEND"

    def test_knowledge_domain_enum(self):
        """Test KnowledgeDomain enum values."""
        assert KnowledgeDomain.GENERAL == "general"
        assert KnowledgeDomain.TECHNICAL == "technical"
        assert KnowledgeDomain.BUSINESS == "business"
        assert KnowledgeDomain.SECURITY == "security"

        # Test enum is string-based
        assert isinstance(KnowledgeDomain.TECHNICAL, str)
        assert str(KnowledgeDomain.TECHNICAL) == "KnowledgeDomain.TECHNICAL"

    def test_security_classification_enum(self):
        """Test SecurityClassification enum values."""
        assert SecurityClassification.PUBLIC == "public"
        assert SecurityClassification.INTERNAL == "internal"
        assert SecurityClassification.CONFIDENTIAL == "confidential"
        assert SecurityClassification.RESTRICTED == "restricted"

        # Test enum is string-based
        assert isinstance(SecurityClassification.PUBLIC, str)
        assert str(SecurityClassification.PUBLIC) == "SecurityClassification.PUBLIC"


class TestKnowledgeMetadata:
    """Test KnowledgeMetadata dataclass."""

    def test_knowledge_metadata_creation(self):
        """Test creating KnowledgeMetadata with required fields."""
        metadata = KnowledgeMetadata(domain=KnowledgeDomain.TECHNICAL)

        assert metadata.domain == KnowledgeDomain.TECHNICAL
        assert metadata.tags == []
        assert metadata.source == ""
        assert metadata.confidence == 0.0
        assert metadata.security_classification == SecurityClassification.PUBLIC
        assert metadata.document_id is None
        assert metadata.agent_attribution is None
        assert metadata.confidence_score is None
        assert metadata.knowledge_domain is None

    def test_knowledge_metadata_with_all_fields(self):
        """Test creating KnowledgeMetadata with all fields."""
        metadata = KnowledgeMetadata(
            domain=KnowledgeDomain.SECURITY,
            tags=["authentication", "oauth"],
            source="PRD-1.5",
            confidence=0.95,
            security_classification=SecurityClassification.CONFIDENTIAL,
            document_id="doc-123",
            agent_attribution="security-agent",
            confidence_score=0.9,
            knowledge_domain="security",
        )

        assert metadata.domain == KnowledgeDomain.SECURITY
        assert metadata.tags == ["authentication", "oauth"]
        assert metadata.source == "PRD-1.5"
        assert metadata.confidence == 0.95
        assert metadata.security_classification == SecurityClassification.CONFIDENTIAL
        assert metadata.document_id == "doc-123"
        assert metadata.agent_attribution == "security-agent"
        assert metadata.confidence_score == 0.9
        assert metadata.knowledge_domain == "security"

    def test_knowledge_metadata_get_method(self):
        """Test KnowledgeMetadata.get() method."""
        metadata = KnowledgeMetadata(
            domain=KnowledgeDomain.TECHNICAL, confidence_score=0.8
        )

        # Test getting existing attributes
        assert metadata.get("domain") == KnowledgeDomain.TECHNICAL
        assert metadata.get("confidence_score") == 0.8
        assert metadata.get("tags") == []

        # Test getting non-existent attributes with default
        assert metadata.get("nonexistent") is None
        assert metadata.get("nonexistent", "default") == "default"

        # Test getting None values
        assert metadata.get("document_id") is None
        # Note: get() returns the actual attribute value (None) even with default
        # because the attribute exists, it's just None
        assert metadata.get("document_id", "default") is None

    def test_knowledge_metadata_immutable_tags_default(self):
        """Test that default tags list is not shared between instances."""
        metadata1 = KnowledgeMetadata(domain=KnowledgeDomain.TECHNICAL)
        metadata2 = KnowledgeMetadata(domain=KnowledgeDomain.BUSINESS)

        metadata1.tags.append("test")

        assert metadata1.tags == ["test"]
        assert metadata2.tags == []
        assert metadata1.tags is not metadata2.tags


class TestKnowledgeChunk:
    """Test KnowledgeChunk dataclass."""

    @pytest.fixture
    def sample_metadata(self):
        """Create sample metadata for testing."""
        return KnowledgeMetadata(
            domain=KnowledgeDomain.TECHNICAL,
            confidence_score=0.8,
            agent_attribution="test-agent",
        )

    def test_knowledge_chunk_creation(self, sample_metadata):
        """Test creating KnowledgeChunk with all required fields."""
        now = datetime.utcnow()
        chunk = KnowledgeChunk(
            id="chunk-123",
            content="Test knowledge content",
            embedding=[0.1, 0.2, 0.3],
            metadata=sample_metadata,
            version=1,
            created_at=now,
            updated_at=now,
            author="test-author",
        )

        assert chunk.id == "chunk-123"
        assert chunk.content == "Test knowledge content"
        assert chunk.embedding == [0.1, 0.2, 0.3]
        assert chunk.metadata == sample_metadata
        assert chunk.version == 1
        assert chunk.created_at == now
        assert chunk.updated_at == now
        assert chunk.author == "test-author"

    def test_knowledge_chunk_with_large_embedding(self, sample_metadata):
        """Test KnowledgeChunk with realistic embedding size."""
        # OpenAI text-embedding-3-large has 3072 dimensions
        embedding = [0.1] * 3072
        now = datetime.utcnow()

        chunk = KnowledgeChunk(
            id="chunk-large",
            content="Large embedding test",
            embedding=embedding,
            metadata=sample_metadata,
            version=1,
            created_at=now,
            updated_at=now,
            author="test-author",
        )

        assert len(chunk.embedding) == 3072
        assert all(val == 0.1 for val in chunk.embedding)

    def test_knowledge_chunk_version_tracking(self, sample_metadata):
        """Test KnowledgeChunk version tracking."""
        base_time = datetime.utcnow()

        # Version 1
        chunk_v1 = KnowledgeChunk(
            id="chunk-versioned",
            content="Original content",
            embedding=[0.1, 0.2],
            metadata=sample_metadata,
            version=1,
            created_at=base_time,
            updated_at=base_time,
            author="author-1",
        )

        # Version 2 (updated)
        chunk_v2 = KnowledgeChunk(
            id="chunk-versioned",
            content="Updated content",
            embedding=[0.1, 0.2, 0.3],
            metadata=sample_metadata,
            version=2,
            created_at=base_time,
            updated_at=base_time + timedelta(minutes=5),
            author="author-2",
        )

        assert chunk_v1.version == 1
        assert chunk_v2.version == 2
        assert chunk_v1.content != chunk_v2.content
        assert chunk_v1.updated_at < chunk_v2.updated_at
        assert chunk_v1.author != chunk_v2.author


class TestKnowledgeVersion:
    """Test KnowledgeVersion dataclass."""

    def test_knowledge_version_creation(self):
        """Test creating KnowledgeVersion."""
        now = datetime.utcnow()
        version = KnowledgeVersion(
            document_id="doc-123",
            version=1,
            content="Version content",
            metadata={"confidence_score": 0.8, "agent": "test"},
            created_at=now,
            agent_attribution="test-agent",
        )

        assert version.document_id == "doc-123"
        assert version.version == 1
        assert version.content == "Version content"
        assert version.metadata == {"confidence_score": 0.8, "agent": "test"}
        assert version.created_at == now
        assert version.agent_attribution == "test-agent"

    def test_knowledge_version_metadata_flexibility(self):
        """Test KnowledgeVersion metadata can store arbitrary data."""
        version = KnowledgeVersion(
            document_id="doc-flexible",
            version=1,
            content="Flexible metadata test",
            metadata={
                "confidence_score": 0.9,
                "tags": ["tag1", "tag2"],
                "custom_field": "custom_value",
                "nested": {"key": "value"},
            },
            created_at=datetime.utcnow(),
            agent_attribution="flexible-agent",
        )

        assert version.metadata["confidence_score"] == 0.9
        assert version.metadata["tags"] == ["tag1", "tag2"]
        assert version.metadata["custom_field"] == "custom_value"
        assert version.metadata["nested"]["key"] == "value"


class TestKnowledgeConflict:
    """Test KnowledgeConflict dataclass."""

    @pytest.fixture
    def sample_chunks(self):
        """Create sample knowledge chunks for conflict testing."""
        base_time = datetime.utcnow()
        metadata = KnowledgeMetadata(
            domain=KnowledgeDomain.TECHNICAL, confidence_score=0.8
        )

        existing = KnowledgeChunk(
            id="chunk-1",
            content="Original content",
            embedding=[0.1, 0.2],
            metadata=metadata,
            version=1,
            created_at=base_time,
            updated_at=base_time,
            author="author-1",
        )

        incoming = KnowledgeChunk(
            id="chunk-1",
            content="Modified content",
            embedding=[0.15, 0.25],
            metadata=metadata,
            version=2,
            created_at=base_time,
            updated_at=base_time + timedelta(minutes=2),
            author="author-2",
        )

        return existing, incoming

    def test_knowledge_conflict_creation(self, sample_chunks):
        """Test creating KnowledgeConflict."""
        existing, incoming = sample_chunks
        detected_at = datetime.utcnow()

        conflict = KnowledgeConflict(
            id="conflict-123",
            chunk_id="chunk-1",
            existing_version=existing,
            incoming_version=incoming,
            conflict_type=ConflictType.CONTENT,
            severity=SeverityLevel.MEDIUM,
            detected_at=detected_at,
        )

        assert conflict.id == "conflict-123"
        assert conflict.chunk_id == "chunk-1"
        assert conflict.existing_version == existing
        assert conflict.incoming_version == incoming
        assert conflict.conflict_type == ConflictType.CONTENT
        assert conflict.severity == SeverityLevel.MEDIUM
        assert conflict.detected_at == detected_at
        assert conflict.resolved is False
        assert conflict.resolved_by is None
        assert conflict.resolved_at is None

    def test_knowledge_conflict_with_optional_fields(self, sample_chunks):
        """Test KnowledgeConflict with all optional fields."""
        existing, incoming = sample_chunks
        detected_at = datetime.utcnow()
        resolved_at = detected_at + timedelta(minutes=5)

        version_a = KnowledgeVersion(
            document_id="doc-1",
            version=1,
            content="Version A",
            metadata={"confidence": 0.8},
            created_at=detected_at,
            agent_attribution="agent-a",
        )

        version_b = KnowledgeVersion(
            document_id="doc-1",
            version=2,
            content="Version B",
            metadata={"confidence": 0.9},
            created_at=detected_at,
            agent_attribution="agent-b",
        )

        conflict = KnowledgeConflict(
            id="conflict-full",
            chunk_id="chunk-1",
            existing_version=existing,
            incoming_version=incoming,
            conflict_type=ConflictType.BOTH,
            severity=SeverityLevel.HIGH,
            detected_at=detected_at,
            document_id="doc-1",
            version_a=version_a,
            version_b=version_b,
            similarity_score=0.92,
            resolved=True,
            resolved_by="human",
            resolved_at=resolved_at,
        )

        assert conflict.document_id == "doc-1"
        assert conflict.version_a == version_a
        assert conflict.version_b == version_b
        assert conflict.similarity_score == 0.92
        assert conflict.resolved is True
        assert conflict.resolved_by == "human"
        assert conflict.resolved_at == resolved_at

    def test_knowledge_conflict_resolution_workflow(self, sample_chunks):
        """Test knowledge conflict resolution workflow."""
        existing, incoming = sample_chunks

        # Create unresolved conflict
        conflict = KnowledgeConflict(
            id="conflict-workflow",
            chunk_id="chunk-1",
            existing_version=existing,
            incoming_version=incoming,
            conflict_type=ConflictType.SEMANTIC,
            severity=SeverityLevel.CRITICAL,
            detected_at=datetime.utcnow(),
            similarity_score=0.96,
        )

        assert conflict.resolved is False
        assert conflict.resolved_by is None
        assert conflict.resolved_at is None

        # Simulate resolution
        resolution_time = datetime.utcnow()
        resolved_conflict = KnowledgeConflict(
            id=conflict.id,
            chunk_id=conflict.chunk_id,
            existing_version=conflict.existing_version,
            incoming_version=conflict.incoming_version,
            conflict_type=conflict.conflict_type,
            severity=conflict.severity,
            detected_at=conflict.detected_at,
            similarity_score=conflict.similarity_score,
            resolved=True,
            resolved_by="hybrid-strategy",
            resolved_at=resolution_time,
        )

        assert resolved_conflict.resolved is True
        assert resolved_conflict.resolved_by == "hybrid-strategy"
        assert resolved_conflict.resolved_at == resolution_time


class TestKnowledgeLock:
    """Test KnowledgeLock dataclass."""

    def test_knowledge_lock_creation(self):
        """Test creating KnowledgeLock."""
        expires_at = datetime.utcnow() + timedelta(minutes=5)

        lock = KnowledgeLock(
            document_id="doc-123",
            agent_id="agent-456",
            operation="edit",
            expires_at=expires_at,
        )

        assert lock.document_id == "doc-123"
        assert lock.agent_id == "agent-456"
        assert lock.operation == "edit"
        assert lock.expires_at == expires_at
        assert lock.released is False

        # Test auto-generated lock_id
        assert lock.lock_id is not None
        assert isinstance(lock.lock_id, str)
        assert len(lock.lock_id) > 0

    def test_knowledge_lock_with_custom_id(self):
        """Test KnowledgeLock with custom lock_id."""
        custom_id = str(uuid.uuid4())

        lock = KnowledgeLock(
            document_id="doc-custom",
            agent_id="agent-custom",
            operation="read",
            expires_at=datetime.utcnow() + timedelta(minutes=1),
            lock_id=custom_id,
        )

        assert lock.lock_id == custom_id

    def test_knowledge_lock_unique_ids(self):
        """Test that KnowledgeLock generates unique IDs."""
        lock1 = KnowledgeLock(
            document_id="doc-1",
            agent_id="agent-1",
            operation="edit",
            expires_at=datetime.utcnow() + timedelta(minutes=5),
        )

        lock2 = KnowledgeLock(
            document_id="doc-2",
            agent_id="agent-2",
            operation="edit",
            expires_at=datetime.utcnow() + timedelta(minutes=5),
        )

        assert lock1.lock_id != lock2.lock_id

    def test_knowledge_lock_expiration_workflow(self):
        """Test knowledge lock expiration workflow."""
        now = datetime.utcnow()
        expires_soon = now + timedelta(seconds=30)
        expires_later = now + timedelta(minutes=10)

        # Lock that expires soon
        lock_expiring = KnowledgeLock(
            document_id="doc-expiring",
            agent_id="agent-1",
            operation="edit",
            expires_at=expires_soon,
        )

        # Lock that expires later
        lock_valid = KnowledgeLock(
            document_id="doc-valid",
            agent_id="agent-2",
            operation="read",
            expires_at=expires_later,
        )

        # Test expiration logic (would be implemented in service layer)
        current_time = now + timedelta(minutes=1)
        assert lock_expiring.expires_at < current_time  # Expired
        assert lock_valid.expires_at > current_time  # Still valid

    def test_knowledge_lock_release_workflow(self):
        """Test knowledge lock release workflow."""
        lock = KnowledgeLock(
            document_id="doc-release",
            agent_id="agent-release",
            operation="edit",
            expires_at=datetime.utcnow() + timedelta(minutes=5),
        )

        assert lock.released is False

        # Simulate release (would be done by service layer)
        released_lock = KnowledgeLock(
            document_id=lock.document_id,
            agent_id=lock.agent_id,
            operation=lock.operation,
            expires_at=lock.expires_at,
            lock_id=lock.lock_id,
            released=True,
        )

        assert released_lock.released is True


class TestKnowledgeQuery:
    """Test KnowledgeQuery dataclass."""

    def test_knowledge_query_minimal(self):
        """Test creating KnowledgeQuery with minimal fields."""
        query = KnowledgeQuery(query_text="test query")

        assert query.query_text == "test query"
        assert query.max_results == 10
        assert query.min_confidence == 0.0
        assert query.knowledge_domains == []
        assert query.agent_id is None

    def test_knowledge_query_full(self):
        """Test creating KnowledgeQuery with all fields."""
        domains = [KnowledgeDomain.TECHNICAL, KnowledgeDomain.SECURITY]

        query = KnowledgeQuery(
            query_text="authentication implementation",
            max_results=25,
            min_confidence=0.8,
            knowledge_domains=domains,
            agent_id="security-agent",
        )

        assert query.query_text == "authentication implementation"
        assert query.max_results == 25
        assert query.min_confidence == 0.8
        assert query.knowledge_domains == domains
        assert query.agent_id == "security-agent"

    def test_knowledge_query_immutable_domains_default(self):
        """Test that default knowledge_domains list is not shared."""
        query1 = KnowledgeQuery(query_text="query 1")
        query2 = KnowledgeQuery(query_text="query 2")

        query1.knowledge_domains.append(KnowledgeDomain.TECHNICAL)

        assert query1.knowledge_domains == [KnowledgeDomain.TECHNICAL]
        assert query2.knowledge_domains == []
        assert query1.knowledge_domains is not query2.knowledge_domains

    def test_knowledge_query_validation_scenarios(self):
        """Test KnowledgeQuery with various validation scenarios."""
        # Empty query text
        empty_query = KnowledgeQuery(query_text="")
        assert empty_query.query_text == ""

        # Zero max results
        zero_results = KnowledgeQuery(query_text="test", max_results=0)
        assert zero_results.max_results == 0

        # High confidence threshold
        high_confidence = KnowledgeQuery(query_text="test", min_confidence=0.95)
        assert high_confidence.min_confidence == 0.95

        # Multiple domains
        multi_domain = KnowledgeQuery(
            query_text="test",
            knowledge_domains=[
                KnowledgeDomain.TECHNICAL,
                KnowledgeDomain.BUSINESS,
                KnowledgeDomain.SECURITY,
            ],
        )
        assert len(multi_domain.knowledge_domains) == 3


class TestDataModelIntegration:
    """Test integration between different data models."""

    def test_conflict_with_versions_integration(self):
        """Test KnowledgeConflict integration with KnowledgeVersion."""
        base_time = datetime.utcnow()

        # Create versions
        version_a = KnowledgeVersion(
            document_id="doc-integration",
            version=1,
            content="Original content",
            metadata={"confidence_score": 0.8, "agent": "agent-a"},
            created_at=base_time,
            agent_attribution="agent-a",
        )

        version_b = KnowledgeVersion(
            document_id="doc-integration",
            version=2,
            content="Modified content",
            metadata={"confidence_score": 0.9, "agent": "agent-b"},
            created_at=base_time + timedelta(minutes=2),
            agent_attribution="agent-b",
        )

        # Create chunks
        metadata = KnowledgeMetadata(
            domain=KnowledgeDomain.TECHNICAL, confidence_score=0.8
        )

        existing_chunk = KnowledgeChunk(
            id="chunk-integration",
            content=version_a.content,
            embedding=[0.1, 0.2],
            metadata=metadata,
            version=version_a.version,
            created_at=version_a.created_at,
            updated_at=version_a.created_at,
            author=version_a.agent_attribution,
        )

        incoming_chunk = KnowledgeChunk(
            id="chunk-integration",
            content=version_b.content,
            embedding=[0.15, 0.25],
            metadata=metadata,
            version=version_b.version,
            created_at=version_b.created_at,
            updated_at=version_b.created_at,
            author=version_b.agent_attribution,
        )

        # Create conflict linking everything
        conflict = KnowledgeConflict(
            id="conflict-integration",
            chunk_id="chunk-integration",
            existing_version=existing_chunk,
            incoming_version=incoming_chunk,
            conflict_type=ConflictType.CONTENT,
            severity=SeverityLevel.MEDIUM,
            detected_at=base_time + timedelta(minutes=3),
            document_id="doc-integration",
            version_a=version_a,
            version_b=version_b,
            similarity_score=0.87,
        )

        # Verify integration
        assert conflict.document_id == version_a.document_id == version_b.document_id
        assert conflict.existing_version.content == version_a.content
        assert conflict.incoming_version.content == version_b.content
        assert conflict.version_a.agent_attribution == existing_chunk.author
        assert conflict.version_b.agent_attribution == incoming_chunk.author

    def test_lock_and_query_integration(self):
        """Test KnowledgeLock and KnowledgeQuery integration scenario."""
        # Agent wants to query and then lock for editing
        agent_id = "integration-agent"
        document_id = "doc-to-edit"

        # First, create a query
        query = KnowledgeQuery(
            query_text="find document to edit",
            max_results=1,
            min_confidence=0.9,
            knowledge_domains=[KnowledgeDomain.TECHNICAL],
            agent_id=agent_id,
        )

        # Then create a lock for the found document
        lock = KnowledgeLock(
            document_id=document_id,
            agent_id=agent_id,
            operation="edit",
            expires_at=datetime.utcnow() + timedelta(minutes=10),
        )

        # Verify integration
        assert query.agent_id == lock.agent_id
        assert query.max_results == 1  # Only need one document to edit
        assert lock.operation == "edit"
        assert not lock.released

    def test_metadata_consistency_across_models(self):
        """Test metadata consistency between KnowledgeMetadata and KnowledgeVersion."""
        # Create structured metadata
        structured_metadata = KnowledgeMetadata(
            domain=KnowledgeDomain.SECURITY,
            tags=["auth", "oauth"],
            confidence_score=0.95,
            agent_attribution="security-agent",
            document_id="doc-security",
        )

        # Create version with equivalent dict metadata
        dict_metadata = {
            "domain": "security",
            "tags": ["auth", "oauth"],
            "confidence_score": 0.95,
            "agent_attribution": "security-agent",
            "document_id": "doc-security",
        }

        version = KnowledgeVersion(
            document_id="doc-security",
            version=1,
            content="Security content",
            metadata=dict_metadata,
            created_at=datetime.utcnow(),
            agent_attribution="security-agent",
        )

        # Verify consistency
        assert (
            structured_metadata.confidence_score == version.metadata["confidence_score"]
        )
        assert (
            structured_metadata.agent_attribution
            == version.metadata["agent_attribution"]
        )
        assert structured_metadata.agent_attribution == version.agent_attribution
        assert structured_metadata.document_id == version.document_id
