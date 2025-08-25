"""Simplified tests for Knowledge Sharing Activities using proven unit testing approach."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestKnowledgeSharingActivitiesUnit:
    """Test knowledge sharing activities business logic with unit testing approach."""

    @pytest.mark.asyncio
    async def test_knowledge_sharing_activity_business_logic(self):
        """Test knowledge sharing activity core business logic."""
        from orchestra.temporal.activities.knowledge_sharing import (
            knowledge_sharing_activity,
        )

        sharing_context = {
            "source_persona_id": "dev",
            "project_id": "test-project",
            "operation": "export_patterns",
        }

        # Unit test business logic by mocking the core services
        with (
            patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test-key-123"}),
            patch(
                "orchestra.temporal.activities.knowledge_sharing.MemoryService"
            ) as mock_memory_class,
            patch(
                "orchestra.temporal.activities.knowledge_sharing.PatternMatchingService"
            ) as mock_pattern_class,
            patch(
                "orchestra.temporal.activities.knowledge_sharing._export_shareable_patterns"
            ) as mock_export,
        ):
            # Mock service initialization
            mock_memory_service = AsyncMock()
            mock_pattern_service = AsyncMock()
            mock_memory_class.return_value = mock_memory_service
            mock_pattern_class.return_value = mock_pattern_service

            # Mock the export operation
            mock_export.return_value = {
                "success": True,
                "operation": "export_patterns",
                "exported_patterns": 3,
                "shared_knowledge_id": "sk-123",
                "repository_updated": True,
            }

            # Test the business logic
            result = await knowledge_sharing_activity(
                sharing_context, "export_patterns"
            )

            # Verify business requirements
            assert result["success"] is True
            assert result["operation"] == "export_patterns"
            assert result["exported_patterns"] >= 1

            # Verify services were initialized
            mock_memory_class.assert_called_once()
            mock_pattern_class.assert_called_once()

    @pytest.mark.asyncio
    async def test_pattern_matching_activity_business_logic(self):
        """Test pattern matching activity core business logic."""
        from orchestra.temporal.activities.knowledge_sharing import (
            pattern_matching_activity,
        )

        # Unit test business logic by mocking the pattern matching service
        with (
            patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test-key-123"}),
            patch(
                "orchestra.temporal.activities.knowledge_sharing.PatternMatchingService"
            ) as mock_service_class,
        ):
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service

            # Mock successful pattern finding
            mock_service.find_transferable_patterns.return_value = {
                "success": True,
                "pattern_mappings": [
                    {"pattern_id": "p1", "transferability_score": 0.87}
                ],
                "transferable_patterns": [{"pattern_id": "p1"}],
                "transferable_count": 1,
            }

            # Test business logic
            result = await pattern_matching_activity("dev", ["qa"], "test-project")

            # Verify core business requirements
            assert result["success"] is True
            assert "matching_results" in result
            assert len(result["matching_results"]) == 1

            # Verify pattern matching was called
            mock_service.find_transferable_patterns.assert_called()

    @pytest.mark.asyncio
    async def test_propagation_activity_business_logic(self):
        """Test propagation activity core business logic."""
        from orchestra.temporal.activities.knowledge_sharing import (
            propagation_activity,
        )

        shared_knowledge_list = [
            {
                "knowledge_id": "know-1",
                "source_persona_id": "dev",
                "source_project_id": "test-project",
                "confidence_score": 0.9,
                "transferability_score": 0.85,
                "content": "Test pattern",
            }
        ]

        # Unit test business logic by mocking propagation helper
        with (
            patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test-key-123"}),
            patch(
                "orchestra.temporal.activities.knowledge_sharing._propagate_to_persona"
            ) as mock_propagate,
        ):
            mock_propagate.return_value = {
                "success": True,
                "propagated": True,
                "target_persona": "qa",
            }

            # Test business logic
            result = await propagation_activity(
                shared_knowledge_list, ["qa"], "automatic"
            )

            # Verify core business requirements
            assert result["success"] is True
            assert result["propagation_mode"] == "automatic"
            assert "propagation_results" in result
            assert result["knowledge_items_processed"] >= 1

    @pytest.mark.asyncio
    async def test_validation_activity_business_logic(self):
        """Test validation activity core business logic."""
        from orchestra.temporal.activities.knowledge_sharing import validation_activity

        shared_knowledge_ids = ["know-1", "know-2"]
        target_personas = ["qa", "dev"]

        # Unit test business logic by mocking validation helper
        with (
            patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test-key-123"}),
            patch(
                "orchestra.temporal.activities.knowledge_sharing._validate_shared_knowledge"
            ) as mock_validate,
        ):
            mock_validate.side_effect = [
                {
                    "knowledge_id": "know-1",
                    "effectiveness_score": 0.87,
                    "validation_status": "effective",
                },
                {
                    "knowledge_id": "know-2",
                    "effectiveness_score": 0.45,
                    "validation_status": "ineffective",
                },
            ]

            # Test business logic
            result = await validation_activity(shared_knowledge_ids, target_personas)

            # Verify core business requirements
            assert result["success"] is True
            assert len(result["validation_results"]) == 2
            assert mock_validate.call_count == 2

    @pytest.mark.asyncio
    async def test_tag_based_targeting_activity_business_logic(self):
        """Test tag-based targeting activity core business logic."""
        from orchestra.temporal.activities.knowledge_sharing import (
            tag_based_targeting_activity,
        )

        knowledge_sharing_request = {
            "knowledge_id": "know-123",
            "source_persona_id": "dev",
            "content": "API design patterns",
            "domain": "backend_development",
        }

        targeting_criteria = {
            "required_skills": ["python", "api_design"],
            "experience_level": "intermediate",
            "project_domains": ["web_development"],
        }

        # Unit test business logic by mocking tag creation and matching
        with (
            patch(
                "orchestra.temporal.activities.knowledge_sharing._create_targeting_tags"
            ) as mock_create_tags,
            patch(
                "orchestra.temporal.activities.knowledge_sharing._match_personas_by_tag"
            ) as mock_match,
        ):
            # Mock tag creation
            mock_tag = MagicMock()
            mock_tag.tag_id = "tag-123"
            mock_tag.tag_type = "skill_based"
            mock_create_tags.return_value = [mock_tag]

            # Mock persona matching
            mock_match.return_value = ["dev", "backend-specialist"]

            # Test business logic
            result = await tag_based_targeting_activity(
                knowledge_sharing_request, targeting_criteria
            )

            # Verify core business requirements
            assert result["success"] is True
            assert len(result["targeting_tags"]) == 1
            assert len(result["matched_personas"]) >= 1

    @pytest.mark.asyncio
    async def test_knowledge_sharing_activity_error_handling(self):
        """Test knowledge sharing activity error handling."""
        from orchestra.temporal.activities.knowledge_sharing import (
            knowledge_sharing_activity,
        )

        sharing_context = {"project_id": "test-project"}

        # Test error handling when services fail to initialize
        with patch(
            "orchestra.temporal.activities.knowledge_sharing.MemoryService",
            side_effect=Exception("Service error"),
        ):
            result = await knowledge_sharing_activity(
                sharing_context, "export_patterns"
            )

            # Verify error is handled gracefully
            assert result["success"] is False
            assert "Service error" in result["error"]
            assert result["operation"] == "export_patterns"

    @pytest.mark.asyncio
    async def test_knowledge_sharing_activity_unknown_operation(self):
        """Test knowledge sharing activity with unknown operation."""
        from orchestra.temporal.activities.knowledge_sharing import (
            knowledge_sharing_activity,
        )

        sharing_context = {"project_id": "test-project"}

        # Unit test error handling for unknown operations
        with (
            patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test-key-123"}),
            patch("orchestra.temporal.activities.knowledge_sharing.MemoryService"),
            patch(
                "orchestra.temporal.activities.knowledge_sharing.PatternMatchingService"
            ),
        ):
            result = await knowledge_sharing_activity(
                sharing_context, "unknown_operation"
            )

            # Verify unknown operation error
            assert result["success"] is False
            assert "Unknown knowledge sharing operation" in result["error"]

    @pytest.mark.asyncio
    async def test_pattern_matching_activity_error_handling(self):
        """Test pattern matching activity error handling."""
        from orchestra.temporal.activities.knowledge_sharing import (
            pattern_matching_activity,
        )

        # Test error handling when pattern service fails
        with patch(
            "orchestra.temporal.activities.knowledge_sharing.PatternMatchingService",
            side_effect=Exception("Pattern service failed"),
        ):
            result = await pattern_matching_activity("dev", ["qa"], "test-project")

            # Verify error is handled gracefully
            assert result["success"] is False
            assert "Pattern service failed" in result["error"]

    @pytest.mark.asyncio
    async def test_activities_integration_flow(self):
        """Test integration flow between knowledge sharing activities."""
        from orchestra.temporal.activities.knowledge_sharing import (
            knowledge_sharing_activity,
            propagation_activity,
        )

        # Test end-to-end business logic flow
        sharing_context = {"source_persona_id": "dev", "project_id": "test-project"}

        with (
            patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test-key-123"}),
            patch("orchestra.temporal.activities.knowledge_sharing.MemoryService"),
            patch(
                "orchestra.temporal.activities.knowledge_sharing.PatternMatchingService"
            ),
            patch(
                "orchestra.temporal.activities.knowledge_sharing._export_shareable_patterns"
            ) as mock_export,
            patch(
                "orchestra.temporal.activities.knowledge_sharing._propagate_to_persona"
            ) as mock_propagate,
        ):
            # Mock successful export
            mock_export.return_value = {"success": True, "exported_patterns": 2}
            mock_propagate.return_value = {"success": True, "propagated": True}

            # Test integration flow
            export_result = await knowledge_sharing_activity(
                sharing_context, "export_patterns"
            )

            # Verify export worked
            assert export_result["success"] is True

            # Test that subsequent activities can work with the results
            shared_knowledge = [
                {
                    "knowledge_id": "k1",
                    "source_persona_id": "dev",
                    "source_project_id": "test",
                }
            ]
            propagation_result = await propagation_activity(
                shared_knowledge, ["qa"], "automatic"
            )

            # Verify integration
            assert propagation_result["success"] is True

    @pytest.mark.asyncio
    async def test_activities_performance_requirements(self):
        """Test that activities meet basic performance requirements."""
        from orchestra.temporal.activities.knowledge_sharing import (
            knowledge_sharing_activity,
        )

        sharing_context = {"source_persona_id": "dev", "project_id": "test-project"}

        # Test that activities complete within reasonable timeframes
        with (
            patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test-key-123"}),
            patch("orchestra.temporal.activities.knowledge_sharing.MemoryService"),
            patch(
                "orchestra.temporal.activities.knowledge_sharing.PatternMatchingService"
            ),
            patch(
                "orchestra.temporal.activities.knowledge_sharing._export_shareable_patterns"
            ) as mock_export,
        ):
            mock_export.return_value = {
                "success": True,
                "exported_patterns": 5,
                "processing_time_ms": 120,  # Under performance threshold
            }

            start_time = datetime.utcnow()
            result = await knowledge_sharing_activity(
                sharing_context, "export_patterns"
            )
            end_time = datetime.utcnow()

            processing_time_ms = (end_time - start_time).total_seconds() * 1000

            # Verify performance requirements
            assert result["success"] is True
            assert processing_time_ms < 2000  # Should complete quickly with mocking

    @pytest.mark.asyncio
    async def test_knowledge_sharing_activities_business_value(self):
        """Test that activities deliver expected business value."""
        from orchestra.temporal.activities.knowledge_sharing import (
            knowledge_sharing_activity,
            pattern_matching_activity,
        )

        # Test business value: knowledge export enables sharing
        sharing_context = {"source_persona_id": "dev", "project_id": "test-project"}

        with (
            patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test-key-123"}),
            patch("orchestra.temporal.activities.knowledge_sharing.MemoryService"),
            patch(
                "orchestra.temporal.activities.knowledge_sharing.PatternMatchingService"
            ) as mock_pattern_class,
            patch(
                "orchestra.temporal.activities.knowledge_sharing._export_shareable_patterns"
            ) as mock_export,
        ):
            mock_pattern_service = AsyncMock()
            mock_pattern_class.return_value = mock_pattern_service

            # Mock high-value export
            mock_export.return_value = {
                "success": True,
                "exported_patterns": 8,
                "high_value_patterns": 3,  # Patterns with high effectiveness
                "repository_updated": True,
            }

            # Mock successful pattern matching
            mock_pattern_service.find_transferable_patterns.return_value = {
                "success": True,
                "pattern_mappings": [{"transferability_score": 0.91}],
                "transferable_patterns": [{"effectiveness": 0.89}],
                "transferable_count": 1,
            }

            # Test business value delivery
            export_result = await knowledge_sharing_activity(
                sharing_context, "export_patterns"
            )
            pattern_result = await pattern_matching_activity(
                "dev", ["qa"], "test-project"
            )

            # Verify business value
            assert export_result["success"] is True
            assert (
                export_result["exported_patterns"] > 5
            )  # Substantial knowledge shared
            assert pattern_result["success"] is True
            assert (
                len(pattern_result["matching_results"]) > 0
            )  # Patterns found for transfer


class TestKnowledgeSharingHelperFunctions:
    """Comprehensive unit tests for knowledge sharing helper functions."""

    @pytest.mark.asyncio
    async def test_export_shareable_patterns_success(self):
        """Test _export_shareable_patterns helper function success case."""
        from orchestra.temporal.activities.knowledge_sharing import (
            _export_shareable_patterns,
        )

        sharing_context = {
            "source_persona_id": "dev",
            "project_id": "test-project",
        }

        # Mock memory service
        memory_service = AsyncMock()
        memory_service.get_shareable_patterns.return_value = {
            "success": True,
            "patterns": [
                {
                    "pattern_id": "pattern-1",
                    "content": "Test pattern content",
                    "effectiveness_score": 0.85,
                    "transferability_score": 0.80,
                },
                {
                    "pattern_id": "pattern-2",
                    "content": "Another test pattern",
                    "effectiveness_score": 0.90,
                    "transferability_score": 0.85,
                },
            ],
        }

        # Mock pattern service
        pattern_service = MagicMock()

        result = await _export_shareable_patterns(
            sharing_context, memory_service, pattern_service
        )

        assert result["success"] is True
        assert result["operation"] == "export_patterns"
        assert result["patterns_count"] == 2
        assert result["source_persona"] == "dev"
        assert len(result["shareable_patterns"]) == 2

        # Verify memory service was called correctly
        memory_service.get_shareable_patterns.assert_called_once_with(sharing_context)

    @pytest.mark.asyncio
    async def test_export_shareable_patterns_memory_failure(self):
        """Test _export_shareable_patterns when memory service fails."""
        from orchestra.temporal.activities.knowledge_sharing import (
            _export_shareable_patterns,
        )

        sharing_context = {"source_persona_id": "dev", "project_id": "test-project"}

        # Mock memory service failure
        memory_service = AsyncMock()
        memory_service.get_shareable_patterns.return_value = {
            "success": False,
            "error": "Memory service failure",
        }
        pattern_service = MagicMock()

        result = await _export_shareable_patterns(
            sharing_context, memory_service, pattern_service
        )

        assert result["success"] is False
        assert result["error"] == "Failed to retrieve shareable patterns"
        assert result["shareable_patterns"] == []

    @pytest.mark.asyncio
    async def test_export_shareable_patterns_exception(self):
        """Test _export_shareable_patterns exception handling."""
        from orchestra.temporal.activities.knowledge_sharing import (
            _export_shareable_patterns,
        )

        sharing_context = {"source_persona_id": "dev", "project_id": "test-project"}

        # Mock memory service to raise exception
        memory_service = AsyncMock()
        memory_service.get_shareable_patterns.side_effect = Exception("Memory error")
        pattern_service = MagicMock()

        result = await _export_shareable_patterns(
            sharing_context, memory_service, pattern_service
        )

        assert result["success"] is False
        assert "Memory error" in result["error"]
        assert result["operation"] == "export_patterns"

    @pytest.mark.asyncio
    async def test_import_shared_knowledge_success(self):
        """Test _import_shared_knowledge helper function success case."""
        from orchestra.temporal.activities.knowledge_sharing import (
            _import_shared_knowledge,
        )

        sharing_context = {
            "target_persona_id": "qa",
            "project_id": "test-project",
            "shared_knowledge": [
                {
                    "knowledge_id": "sk-1",
                    "title": "Test Knowledge 1",
                    "effectiveness_score": 0.85,
                },
                {
                    "knowledge_id": "sk-2",
                    "title": "Test Knowledge 2",
                    "effectiveness_score": 0.90,
                },
            ],
        }

        # Mock memory service
        memory_service = AsyncMock()
        mock_memory_record = MagicMock()
        memory_service.create_memory_from_learning_outcome.return_value = (
            mock_memory_record
        )
        memory_service.upsert_memory.return_value = {
            "success": True,
            "memory_id": "mem-123",
        }

        result = await _import_shared_knowledge(sharing_context, memory_service)

        assert result["success"] is True
        assert result["operation"] == "import_shared_knowledge"
        assert result["successful_imports"] == 2
        assert result["failed_imports"] == 0
        assert result["target_persona"] == "qa"
        assert len(result["import_results"]) == 2

        # Verify memory service calls
        assert memory_service.create_memory_from_learning_outcome.call_count == 2
        assert memory_service.upsert_memory.call_count == 2

    @pytest.mark.asyncio
    async def test_import_shared_knowledge_partial_failure(self):
        """Test _import_shared_knowledge with partial failures."""
        from orchestra.temporal.activities.knowledge_sharing import (
            _import_shared_knowledge,
        )

        sharing_context = {
            "target_persona_id": "architect",
            "project_id": "test-project",
            "shared_knowledge": [
                {"knowledge_id": "sk-1", "title": "Success Knowledge"},
                {"knowledge_id": "sk-2", "title": "Failure Knowledge"},
            ],
        }

        # Mock memory service with mixed results
        memory_service = AsyncMock()
        memory_service.create_memory_from_learning_outcome.return_value = MagicMock()

        # First call succeeds, second fails
        memory_service.upsert_memory.side_effect = [
            {"success": True, "memory_id": "mem-1"},
            Exception("Upsert failed"),
        ]

        result = await _import_shared_knowledge(sharing_context, memory_service)

        assert result["success"] is True
        assert result["successful_imports"] == 1
        assert result["failed_imports"] == 1

    @pytest.mark.asyncio
    async def test_propagate_to_persona_success(self):
        """Test _propagate_to_persona helper function success case."""
        from orchestra.models.shared_knowledge import SharedKnowledge
        from orchestra.temporal.activities.knowledge_sharing import (
            _propagate_to_persona,
        )

        # Create mock shared knowledge
        shared_knowledge = SharedKnowledge(
            knowledge_id="sk-test",
            source_persona_id="dev",
            source_project_id="test-project",
            pattern_id="pattern-1",
            knowledge_type="success_pattern",
            title="Test Knowledge",
            description="Test description",
            content={},
            transferability_metadata={},
            effectiveness_score=0.85,
            usage_count=1,
            success_rate=0.9,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Mock transferability assessment
        with patch.object(shared_knowledge, "assess_transferability") as mock_assess:
            mock_assess.return_value = {"applicable": True, "score": 0.8}

            # Mock memory service
            memory_service = AsyncMock()
            mock_memory_record = MagicMock()
            memory_service.create_memory_from_learning_outcome.return_value = (
                mock_memory_record
            )
            memory_service.upsert_memory.return_value = {
                "success": True,
                "memory_id": "mem-propagated",
            }

            result = await _propagate_to_persona(
                shared_knowledge, "qa", "automatic", memory_service
            )

            assert result["target_persona"] == "qa"
            assert result["success"] is True
            assert result["memory_id"] == "mem-propagated"
            assert result["propagation_mode"] == "automatic"
            assert "propagation_time_ms" in result
            assert result["transferability"]["applicable"] is True

    @pytest.mark.asyncio
    async def test_propagate_to_persona_not_applicable(self):
        """Test _propagate_to_persona when not applicable to target persona."""
        from orchestra.models.shared_knowledge import SharedKnowledge
        from orchestra.temporal.activities.knowledge_sharing import (
            _propagate_to_persona,
        )

        shared_knowledge = SharedKnowledge(
            knowledge_id="sk-test",
            source_persona_id="dev",
            source_project_id="test-project",
            pattern_id="pattern-1",
            knowledge_type="success_pattern",
            title="Test Knowledge",
            description="Test description",
            content={},
            transferability_metadata={},
            effectiveness_score=0.85,
            usage_count=1,
            success_rate=0.9,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Mock transferability assessment - not applicable
        with patch.object(shared_knowledge, "assess_transferability") as mock_assess:
            mock_assess.return_value = {"applicable": False, "score": 0.3}

            memory_service = AsyncMock()

            result = await _propagate_to_persona(
                shared_knowledge, "pm", "manual", memory_service
            )

            assert result["target_persona"] == "pm"
            assert result["success"] is False
            assert result["reason"] == "Not applicable to target persona"
            assert result["transferability"]["applicable"] is False

    @pytest.mark.asyncio
    async def test_validate_shared_knowledge_success(self):
        """Test _validate_shared_knowledge helper function success case."""
        from orchestra.temporal.activities.knowledge_sharing import (
            _validate_shared_knowledge,
        )

        # Mock pattern service
        pattern_service = MagicMock()

        result = await _validate_shared_knowledge(
            "sk-test", ["dev", "qa"], 14, pattern_service
        )

        assert result["success"] is True
        assert result["knowledge_id"] == "sk-test"
        assert result["total_personas"] == 2
        assert result["validation_period_days"] == 14
        assert len(result["validation_metrics"]) == 2
        assert "overall_beneficial" in result
        assert "rollback_required" in result

    @pytest.mark.asyncio
    async def test_validate_shared_knowledge_with_rollback(self):
        """Test _validate_shared_knowledge when rollback is required."""
        from orchestra.temporal.activities.knowledge_sharing import (
            _validate_shared_knowledge,
        )

        # Mock pattern service
        pattern_service = MagicMock()

        # Patch ValidationMetric to simulate low effectiveness
        with patch(
            "orchestra.temporal.activities.knowledge_sharing.ValidationMetric"
        ) as MockValidationMetric:
            # Create mock instance
            mock_metric = MagicMock()
            mock_metric.validation_status = "ineffective"
            mock_metric.rollback_required = True
            mock_metric.should_allow_propagation.return_value = False
            mock_metric.improvement_analysis = {
                "overall_effectiveness": 0.3
            }  # Below 50%

            # Configure the mock constructor to return our mock instance
            MockValidationMetric.return_value = mock_metric

            result = await _validate_shared_knowledge(
                "sk-test", ["dev"], 7, pattern_service
            )

            assert result["success"] is True
            assert result["rollback_required"] is True
            assert result["overall_beneficial"] is False

    @pytest.mark.asyncio
    async def test_create_targeting_tags_success(self):
        """Test _create_targeting_tags helper function success case."""
        from orchestra.temporal.activities.knowledge_sharing import (
            _create_targeting_tags,
        )

        targeting_criteria = {
            "role": ["dev", "qa"],
            "technology": "python",
            "domain": ["fintech", "healthcare"],
        }

        result = await _create_targeting_tags(targeting_criteria, "test-project")

        assert len(result) == 5  # 2 roles + 1 tech + 2 domains

        # Check that all tags are created correctly
        role_tags = [tag for tag in result if tag.tag_type == "role"]
        tech_tags = [tag for tag in result if tag.tag_type == "technology"]
        domain_tags = [tag for tag in result if tag.tag_type == "domain"]

        assert len(role_tags) == 2
        assert len(tech_tags) == 1
        assert len(domain_tags) == 2

        # Verify tag properties
        for tag in result:
            assert tag.project_id == "test-project"
            assert tag.active is True
            assert tag.matched_personas == []

    @pytest.mark.asyncio
    async def test_create_targeting_tags_empty_criteria(self):
        """Test _create_targeting_tags with empty criteria."""
        from orchestra.temporal.activities.knowledge_sharing import (
            _create_targeting_tags,
        )

        result = await _create_targeting_tags({}, "test-project")
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_match_personas_by_tag_role(self):
        """Test _match_personas_by_tag for role-based matching."""
        from orchestra.models.shared_knowledge import TargetingTag
        from orchestra.temporal.activities.knowledge_sharing import (
            _match_personas_by_tag,
        )

        tag = TargetingTag(
            tag_id="tag-1",
            tag_name="dev_role",
            tag_type="role",
            tag_value="dev",
            project_id="test-project",
            target_criteria={"role": "dev"},
            matched_personas=[],
            hierarchical_tags={},
            active=True,
        )

        result = await _match_personas_by_tag(tag)

        assert "dev-persona-1" in result
        assert "dev-persona-2" in result
        assert "fullstack-dev" in result

    @pytest.mark.asyncio
    async def test_match_personas_by_tag_technology(self):
        """Test _match_personas_by_tag for technology-based matching."""
        from orchestra.models.shared_knowledge import TargetingTag
        from orchestra.temporal.activities.knowledge_sharing import (
            _match_personas_by_tag,
        )

        tag = TargetingTag(
            tag_id="tag-2",
            tag_name="python_tech",
            tag_type="technology",
            tag_value="python",
            project_id="test-project",
            target_criteria={"technology": "python"},
            matched_personas=[],
            hierarchical_tags={},
            active=True,
        )

        result = await _match_personas_by_tag(tag)

        assert "python-dev" in result
        assert "backend-dev" in result
        assert "fullstack-dev" in result

    @pytest.mark.asyncio
    async def test_match_personas_by_tag_domain(self):
        """Test _match_personas_by_tag for domain-based matching."""
        from orchestra.models.shared_knowledge import TargetingTag
        from orchestra.temporal.activities.knowledge_sharing import (
            _match_personas_by_tag,
        )

        tag = TargetingTag(
            tag_id="tag-3",
            tag_name="fintech_domain",
            tag_type="domain",
            tag_value="fintech",
            project_id="test-project",
            target_criteria={"domain": "fintech"},
            matched_personas=[],
            hierarchical_tags={},
            active=True,
        )

        result = await _match_personas_by_tag(tag)

        assert "fintech-dev" in result
        assert "security-specialist" in result

    @pytest.mark.asyncio
    async def test_match_personas_by_tag_unknown_type(self):
        """Test _match_personas_by_tag for unknown tag type."""
        from orchestra.models.shared_knowledge import TargetingTag
        from orchestra.temporal.activities.knowledge_sharing import (
            _match_personas_by_tag,
        )

        tag = TargetingTag(
            tag_id="tag-4",
            tag_name="unknown_type",
            tag_type="unknown",
            tag_value="test",
            project_id="test-project",
            target_criteria={"unknown": "test"},
            matched_personas=[],
            hierarchical_tags={},
            active=True,
        )

        result = await _match_personas_by_tag(tag)

        assert result == ["general-persona"]

    @pytest.mark.asyncio
    async def test_match_personas_by_tag_unknown_value(self):
        """Test _match_personas_by_tag for unknown tag value."""
        from orchestra.models.shared_knowledge import TargetingTag
        from orchestra.temporal.activities.knowledge_sharing import (
            _match_personas_by_tag,
        )

        tag = TargetingTag(
            tag_id="tag-5",
            tag_name="unknown_role",
            tag_type="role",
            tag_value="unknown_role",
            project_id="test-project",
            target_criteria={"role": "unknown_role"},
            matched_personas=[],
            hierarchical_tags={},
            active=True,
        )

        result = await _match_personas_by_tag(tag)

        assert result == []  # Unknown role returns empty list
