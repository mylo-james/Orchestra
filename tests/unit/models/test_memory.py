"""Tests for memory data models based on Story 2.1 PRD requirements."""

import uuid
from datetime import datetime, timedelta

import pytest

from orchestra.models.memory import (
    ContextPattern,
    MemoryIndex,
    MemoryRecord,
    RetentionPolicy,
)


class TestMemoryRecord:
    """Test MemoryRecord data model (AC: 1, 6)."""

    def test_memory_record_creation(self):
        """Test MemoryRecord can be created with required fields."""
        memory_id = str(uuid.uuid4())
        project_id = "test-project"
        content = "Test memory content about authentication implementation"
        embedding = [0.1, 0.2, 0.3] * 1024  # Simulate 3072-dim embedding

        memory_record = MemoryRecord(
            memory_id=memory_id,
            project_id=project_id,
            persona_id="dev",
            content=content,
            embedding=embedding,
            confidence_score=0.85,
            relevance_score=0.92,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            metadata={
                "domain": "authentication",
                "complexity": "medium",
                "success_indicators": ["high_test_coverage", "security_validated"],
            },
        )

        assert memory_record.memory_id == memory_id
        assert memory_record.project_id == project_id
        assert memory_record.persona_id == "dev"
        assert memory_record.content == content
        assert len(memory_record.embedding) == 3072
        assert memory_record.confidence_score == 0.85
        assert memory_record.relevance_score == 0.92
        assert isinstance(memory_record.created_at, datetime)
        assert "domain" in memory_record.metadata

    def test_memory_record_namespace_isolation(self):
        """Test MemoryRecord supports project namespace isolation."""
        project_a_record = MemoryRecord(
            memory_id="mem-1",
            project_id="project-a",
            persona_id="dev",
            content="Project A specific memory",
            embedding=[0.1] * 3072,
            confidence_score=0.8,
            relevance_score=0.9,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        project_b_record = MemoryRecord(
            memory_id="mem-2",
            project_id="project-b",
            persona_id="dev",
            content="Project B specific memory",
            embedding=[0.2] * 3072,
            confidence_score=0.8,
            relevance_score=0.9,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Records should be isolated by project_id
        assert project_a_record.project_id != project_b_record.project_id
        assert project_a_record.get_namespace() == "orchestra_memory_project-a"
        assert project_b_record.get_namespace() == "orchestra_memory_project-b"

    def test_memory_record_validation(self):
        """Test MemoryRecord validates required fields and constraints."""
        # Test missing required fields
        with pytest.raises(ValueError, match="memory_id is required"):
            MemoryRecord(
                memory_id="",
                project_id="test-project",
                persona_id="dev",
                content="test",
                embedding=[0.1] * 3072,
                confidence_score=0.8,
                relevance_score=0.9,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

        # Test confidence score range validation
        with pytest.raises(
            ValueError, match="confidence_score must be between 0 and 1"
        ):
            MemoryRecord(
                memory_id="mem-1",
                project_id="test-project",
                persona_id="dev",
                content="test",
                embedding=[0.1] * 3072,
                confidence_score=1.5,  # Invalid: > 1.0
                relevance_score=0.9,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

        # Test relevance score range validation
        with pytest.raises(ValueError, match="relevance_score must be between 0 and 1"):
            MemoryRecord(
                memory_id="mem-1",
                project_id="test-project",
                persona_id="dev",
                content="test",
                embedding=[0.1] * 3072,
                confidence_score=0.8,
                relevance_score=-0.1,  # Invalid: < 0.0
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

    def test_memory_record_embedding_dimension(self):
        """Test MemoryRecord validates embedding dimensions for text-embedding-3-large."""
        # Test correct embedding dimension (3072 for text-embedding-3-large)
        memory_record = MemoryRecord(
            memory_id="mem-1",
            project_id="test-project",
            persona_id="dev",
            content="test",
            embedding=[0.1] * 3072,  # Correct dimension
            confidence_score=0.8,
            relevance_score=0.9,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        assert len(memory_record.embedding) == 3072

        # Test incorrect embedding dimension
        with pytest.raises(ValueError, match="embedding must have 3072 dimensions"):
            MemoryRecord(
                memory_id="mem-1",
                project_id="test-project",
                persona_id="dev",
                content="test",
                embedding=[0.1] * 1536,  # Wrong dimension
                confidence_score=0.8,
                relevance_score=0.9,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )


class TestContextPattern:
    """Test ContextPattern data model for project-specific interaction patterns."""

    def test_context_pattern_creation(self):
        """Test ContextPattern creation with success metrics."""
        pattern = ContextPattern(
            pattern_id="auth-success-pattern",
            project_id="test-project",
            persona_id="dev",
            pattern_type="success_pattern",
            description="High test coverage leads to successful auth implementations",
            context_data={
                "domain": "authentication",
                "test_coverage_threshold": 0.90,
                "security_validations": ["input_sanitization", "encryption"],
            },
            success_metrics={
                "success_rate": 0.92,
                "average_completion_time": 85.5,
                "error_rate": 0.05,
            },
            usage_count=15,
            last_used=datetime.utcnow(),
            created_at=datetime.utcnow(),
        )

        assert pattern.pattern_id == "auth-success-pattern"
        assert pattern.project_id == "test-project"
        assert pattern.persona_id == "dev"
        assert pattern.pattern_type == "success_pattern"
        assert pattern.success_metrics["success_rate"] == 0.92
        assert pattern.usage_count == 15
        assert "domain" in pattern.context_data

    def test_context_pattern_types(self):
        """Test ContextPattern supports different pattern types."""
        success_pattern = ContextPattern(
            pattern_id="success-1",
            project_id="test-project",
            persona_id="dev",
            pattern_type="success_pattern",
            description="Successful implementation pattern",
            context_data={},
            success_metrics={"success_rate": 0.9},
            usage_count=10,
            last_used=datetime.utcnow(),
            created_at=datetime.utcnow(),
        )

        failure_pattern = ContextPattern(
            pattern_id="failure-1",
            project_id="test-project",
            persona_id="dev",
            pattern_type="failure_pattern",
            description="Common failure pattern to avoid",
            context_data={},
            success_metrics={"success_rate": 0.2},
            usage_count=5,
            last_used=datetime.utcnow(),
            created_at=datetime.utcnow(),
        )

        optimization_pattern = ContextPattern(
            pattern_id="optimization-1",
            project_id="test-project",
            persona_id="dev",
            pattern_type="optimization_pattern",
            description="Performance optimization pattern",
            context_data={},
            success_metrics={"performance_improvement": 0.35},
            usage_count=8,
            last_used=datetime.utcnow(),
            created_at=datetime.utcnow(),
        )

        assert success_pattern.pattern_type == "success_pattern"
        assert failure_pattern.pattern_type == "failure_pattern"
        assert optimization_pattern.pattern_type == "optimization_pattern"

    def test_context_pattern_usage_tracking(self):
        """Test ContextPattern tracks usage and updates metrics."""
        pattern = ContextPattern(
            pattern_id="usage-pattern",
            project_id="test-project",
            persona_id="dev",
            pattern_type="success_pattern",
            description="Pattern with usage tracking",
            context_data={},
            success_metrics={"success_rate": 0.8},
            usage_count=5,
            last_used=datetime.utcnow() - timedelta(days=1),
            created_at=datetime.utcnow() - timedelta(days=30),
        )

        # Simulate pattern usage
        old_usage_count = pattern.usage_count
        old_last_used = pattern.last_used

        pattern.record_usage()

        assert pattern.usage_count == old_usage_count + 1
        assert pattern.last_used > old_last_used


class TestMemoryIndex:
    """Test MemoryIndex data model for fast retrieval indexing."""

    def test_memory_index_creation(self):
        """Test MemoryIndex creation with relevance scoring."""
        index = MemoryIndex(
            index_id="idx-1",
            project_id="test-project",
            memory_id="mem-1",
            index_type="semantic",
            index_data={
                "keywords": ["authentication", "security", "validation"],
                "domain": "backend",
                "complexity": "medium",
            },
            relevance_score=0.88,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        assert index.index_id == "idx-1"
        assert index.project_id == "test-project"
        assert index.memory_id == "mem-1"
        assert index.index_type == "semantic"
        assert index.relevance_score == 0.88
        assert "keywords" in index.index_data

    def test_memory_index_types(self):
        """Test MemoryIndex supports different index types."""
        semantic_index = MemoryIndex(
            index_id="semantic-idx",
            project_id="test-project",
            memory_id="mem-1",
            index_type="semantic",
            index_data={"embedding_cluster": "auth_cluster_1"},
            relevance_score=0.9,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        keyword_index = MemoryIndex(
            index_id="keyword-idx",
            project_id="test-project",
            memory_id="mem-1",
            index_type="keyword",
            index_data={"keywords": ["auth", "login", "security"]},
            relevance_score=0.85,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        temporal_index = MemoryIndex(
            index_id="temporal-idx",
            project_id="test-project",
            memory_id="mem-1",
            index_type="temporal",
            index_data={"time_bucket": "2024-01-week-4"},
            relevance_score=0.75,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        assert semantic_index.index_type == "semantic"
        assert keyword_index.index_type == "keyword"
        assert temporal_index.index_type == "temporal"

    def test_memory_index_relevance_scoring(self):
        """Test MemoryIndex relevance scoring validation and updates."""
        # Test valid relevance score
        index = MemoryIndex(
            index_id="relevance-idx",
            project_id="test-project",
            memory_id="mem-1",
            index_type="semantic",
            index_data={},
            relevance_score=0.75,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        assert index.relevance_score == 0.75

        # Test relevance score validation
        with pytest.raises(ValueError, match="relevance_score must be between 0 and 1"):
            MemoryIndex(
                index_id="invalid-idx",
                project_id="test-project",
                memory_id="mem-1",
                index_type="semantic",
                index_data={},
                relevance_score=1.5,  # Invalid: > 1.0
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )


class TestRetentionPolicy:
    """Test RetentionPolicy data model for memory lifecycle management."""

    def test_retention_policy_creation(self):
        """Test RetentionPolicy creation with configurable rules."""
        policy = RetentionPolicy(
            policy_id="retention-policy-1",
            project_id="test-project",
            policy_name="Standard 90-day retention",
            retention_days=90,  # AC: 10 - 90 days retention
            archive_after_days=90,
            delete_after_days=365,
            rules={
                "high_value_memories": {
                    "min_relevance_score": 0.85,
                    "extended_retention_days": 180,
                },
                "low_value_memories": {
                    "max_relevance_score": 0.50,
                    "accelerated_deletion_days": 30,
                },
            },
            active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        assert policy.policy_id == "retention-policy-1"
        assert policy.project_id == "test-project"
        assert policy.retention_days == 90
        assert policy.archive_after_days == 90
        assert policy.delete_after_days == 365
        assert policy.active is True
        assert "high_value_memories" in policy.rules

    def test_retention_policy_memory_classification(self):
        """Test RetentionPolicy can classify memories for different retention."""
        policy = RetentionPolicy(
            policy_id="classification-policy",
            project_id="test-project",
            policy_name="Value-based retention",
            retention_days=90,
            archive_after_days=90,
            delete_after_days=365,
            rules={
                "critical_memories": {
                    "min_relevance_score": 0.90,
                    "min_usage_count": 10,
                    "retention_days": 365,
                },
                "standard_memories": {
                    "min_relevance_score": 0.70,
                    "retention_days": 90,
                },
                "low_value_memories": {
                    "max_relevance_score": 0.50,
                    "retention_days": 30,
                },
            },
            active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Test high-value memory classification
        high_value_memory = MemoryRecord(
            memory_id="high-value-mem",
            project_id="test-project",
            persona_id="dev",
            content="Critical authentication pattern",
            embedding=[0.1] * 3072,
            confidence_score=0.95,
            relevance_score=0.92,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            metadata={"usage_count": 15},
        )

        classification = policy.classify_memory(high_value_memory)
        assert classification["category"] == "critical_memories"
        assert classification["retention_days"] == 365

        # Test low-value memory classification
        low_value_memory = MemoryRecord(
            memory_id="low-value-mem",
            project_id="test-project",
            persona_id="dev",
            content="Trivial task memory",
            embedding=[0.1] * 3072,
            confidence_score=0.60,
            relevance_score=0.45,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            metadata={"usage_count": 1},
        )

        classification = policy.classify_memory(low_value_memory)
        assert classification["category"] == "low_value_memories"
        assert classification["retention_days"] == 30

    def test_retention_policy_memory_footprint_management(self):
        """Test RetentionPolicy helps manage 4GB memory footprint constraint."""
        policy = RetentionPolicy(
            policy_id="footprint-policy",
            project_id="test-project",
            policy_name="Memory footprint management",
            retention_days=90,
            archive_after_days=90,
            delete_after_days=365,
            rules={
                "memory_pressure_cleanup": {
                    "trigger_memory_gb": 3.5,  # Trigger cleanup at 3.5GB
                    "target_memory_gb": 3.0,  # Clean down to 3.0GB
                    "cleanup_strategy": "least_recently_used",
                },
            },
            active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Test memory pressure detection
        current_memory_gb = 3.7  # Above trigger threshold
        cleanup_needed = policy.should_trigger_cleanup(current_memory_gb)
        assert cleanup_needed is True

        # Test cleanup target
        cleanup_target = policy.get_cleanup_target()
        assert cleanup_target["target_memory_gb"] == 3.0
        assert cleanup_target["cleanup_strategy"] == "least_recently_used"

    def test_retention_policy_scheduled_execution(self):
        """Test RetentionPolicy supports scheduled execution patterns."""
        policy = RetentionPolicy(
            policy_id="scheduled-policy",
            project_id="test-project",
            policy_name="Daily scheduled cleanup",
            retention_days=90,
            archive_after_days=90,
            delete_after_days=365,
            rules={
                "schedule": {
                    "frequency": "daily",
                    "time": "02:00",
                    "timezone": "UTC",
                },
            },
            active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Test schedule configuration
        schedule = policy.get_schedule()
        assert schedule["frequency"] == "daily"
        assert schedule["time"] == "02:00"
        assert schedule["timezone"] == "UTC"

        # Test next execution calculation
        next_execution = policy.calculate_next_execution()
        assert isinstance(next_execution, datetime)
        assert next_execution > datetime.utcnow()


class TestMemoryModelIntegration:
    """Test integration between memory data models."""

    def test_memory_models_work_together(self):
        """Test memory models can work together in a complete memory system."""
        # Create a memory record
        memory_record = MemoryRecord(
            memory_id="integration-mem",
            project_id="integration-project",
            persona_id="dev",
            content="Integration test memory for authentication patterns",
            embedding=[0.1] * 3072,
            confidence_score=0.88,
            relevance_score=0.92,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            metadata={"domain": "authentication", "complexity": "medium"},
        )

        # Create associated context pattern
        context_pattern = ContextPattern(
            pattern_id="integration-pattern",
            project_id="integration-project",
            persona_id="dev",
            pattern_type="success_pattern",
            description="Authentication implementation success pattern",
            context_data={"domain": "authentication", "test_coverage": 0.95},
            success_metrics={"success_rate": 0.92, "completion_time": 75.5},
            usage_count=12,
            last_used=datetime.utcnow(),
            created_at=datetime.utcnow(),
        )

        # Create memory index for fast retrieval
        memory_index = MemoryIndex(
            index_id="integration-idx",
            project_id="integration-project",
            memory_id="integration-mem",
            index_type="semantic",
            index_data={
                "keywords": ["authentication", "security"],
                "pattern_id": "integration-pattern",
            },
            relevance_score=0.90,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Create retention policy
        retention_policy = RetentionPolicy(
            policy_id="integration-policy",
            project_id="integration-project",
            policy_name="Integration test retention",
            retention_days=90,
            archive_after_days=90,
            delete_after_days=365,
            rules={"standard_retention": {"min_relevance_score": 0.70}},
            active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Test relationships
        assert memory_record.project_id == context_pattern.project_id
        assert memory_record.memory_id == memory_index.memory_id
        assert memory_record.project_id == retention_policy.project_id

        # Test policy application
        classification = retention_policy.classify_memory(memory_record)
        assert classification["retention_days"] == 90  # Standard retention

        # Test index relevance
        assert memory_index.relevance_score >= 0.90
        assert memory_record.relevance_score >= 0.90

    def test_memory_models_namespace_consistency(self):
        """Test all memory models respect project namespace isolation."""
        project_id = "namespace-test-project"

        memory_record = MemoryRecord(
            memory_id="ns-mem",
            project_id=project_id,
            persona_id="dev",
            content="Namespace test",
            embedding=[0.1] * 3072,
            confidence_score=0.8,
            relevance_score=0.9,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        context_pattern = ContextPattern(
            pattern_id="ns-pattern",
            project_id=project_id,
            persona_id="dev",
            pattern_type="success_pattern",
            description="Namespace test pattern",
            context_data={},
            success_metrics={"success_rate": 0.8},
            usage_count=5,
            last_used=datetime.utcnow(),
            created_at=datetime.utcnow(),
        )

        memory_index = MemoryIndex(
            index_id="ns-idx",
            project_id=project_id,
            memory_id="ns-mem",
            index_type="semantic",
            index_data={},
            relevance_score=0.85,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        retention_policy = RetentionPolicy(
            policy_id="ns-policy",
            project_id=project_id,
            policy_name="Namespace test policy",
            retention_days=90,
            archive_after_days=90,
            delete_after_days=365,
            rules={},
            active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # All models should have the same project_id for namespace isolation
        assert memory_record.project_id == project_id
        assert context_pattern.project_id == project_id
        assert memory_index.project_id == project_id
        assert retention_policy.project_id == project_id

        # Memory record should generate correct namespace
        expected_namespace = f"orchestra_memory_{project_id}"
        assert memory_record.get_namespace() == expected_namespace
