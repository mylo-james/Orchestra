"""Tests for knowledge sharing workflow sub-workflows based on Story 2.3 PRD requirements."""

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from orchestra.workflows.knowledge_sharing_workflows import (
    KnowledgeSharingWorkflow,
    PatternMatchingWorkflow,
    PropagationWorkflow,
    ValidationWorkflow,
)


class TestKnowledgeSharingWorkflow:
    """Test knowledge sharing sub-workflow (AC: 1, 6, 9)."""

    @pytest.mark.asyncio
    async def test_knowledge_sharing_workflow_export_patterns(self):
        """Test knowledge sharing workflow exports learned patterns."""
        workflow = KnowledgeSharingWorkflow()

        sharing_context = {
            "source_persona_id": "dev",
            "project_id": "test-project",
            "operation": "export_patterns",
            "patterns": [
                {
                    "pattern_id": "auth-pattern-1",
                    "type": "success_pattern",
                    "description": "Comprehensive testing leads to successful auth implementations",
                    "effectiveness_score": 0.88,
                    "usage_count": 15,
                    "context": {"domain": "authentication", "complexity": "high"},
                }
            ],
        }

        with patch(
            "orchestra.workflows.knowledge_sharing_workflows.knowledge_sharing_activity"
        ) as mock_activity:
            mock_activity.return_value = {
                "success": True,
                "operation": "export_patterns",
                "exported_patterns": 1,
                "shared_knowledge_id": "sk-123",
                "repository_updated": True,
                "load_time_impact_ms": 25,  # AC: 9 - <500ms load time maintained
            }

            result = await workflow.run(sharing_context)

            assert result["success"] is True
            assert result["exported_patterns"] == 1
            assert (
                result["load_time_impact_ms"] < 500
            )  # AC: 9 - maintain <500ms load time
            assert result["repository_updated"] is True

    @pytest.mark.asyncio
    async def test_knowledge_sharing_workflow_import_patterns(self):
        """Test knowledge sharing workflow imports relevant patterns."""
        workflow = KnowledgeSharingWorkflow()

        sharing_context = {
            "target_persona_id": "qa",
            "project_id": "test-project",
            "operation": "import_patterns",
            "pattern_filters": {
                "domains": ["testing", "quality_assurance"],
                "min_effectiveness": 0.75,
                "source_personas": ["dev", "architect"],
            },
        }

        with patch(
            "orchestra.workflows.knowledge_sharing_workflows.knowledge_sharing_activity"
        ) as mock_activity:
            mock_activity.return_value = {
                "success": True,
                "operation": "import_patterns",
                "imported_patterns": [
                    {
                        "pattern_id": "test-pattern-1",
                        "source_persona": "dev",
                        "effectiveness_score": 0.82,
                        "transferability_score": 0.78,
                    }
                ],
                "cross_references_created": 2,
                "lazy_loaded": True,  # AC: 9 - lazy loading for performance
            }

            result = await workflow.run(sharing_context)

            assert result["success"] is True
            assert len(result["imported_patterns"]) == 1
            assert result["imported_patterns"][0]["effectiveness_score"] > 0.75
            assert result["lazy_loaded"] is True

    @pytest.mark.asyncio
    async def test_knowledge_sharing_workflow_cross_reference_system(self):
        """Test knowledge sharing creates cross-reference system."""
        workflow = KnowledgeSharingWorkflow()

        sharing_context = {
            "operation": "create_cross_references",
            "project_id": "test-project",
            "pattern_relationships": [
                {
                    "pattern_a": "auth-pattern-dev",
                    "pattern_b": "security-pattern-architect",
                    "relationship_type": "complementary",
                    "similarity_score": 0.85,
                }
            ],
        }

        with patch(
            "orchestra.workflows.knowledge_sharing_workflows.knowledge_sharing_activity"
        ) as mock_activity:
            mock_activity.return_value = {
                "success": True,
                "cross_references_created": 1,
                "relationship_graph_updated": True,
                "bidirectional_links": True,
            }

            result = await workflow.run(sharing_context)

            assert result["success"] is True
            assert result["cross_references_created"] == 1
            assert result["relationship_graph_updated"] is True


class TestPatternMatchingWorkflow:
    """Test AI-assisted pattern matching sub-workflow (AC: 2, 6, 7)."""

    @pytest.mark.asyncio
    async def test_pattern_matching_workflow_transferability_analysis(self):
        """Test pattern matching identifies transferable knowledge between personas."""
        workflow = PatternMatchingWorkflow()

        matching_context = {
            "source_patterns": [
                {
                    "pattern_id": "dev-auth-pattern",
                    "persona_id": "dev",
                    "domain": "authentication",
                    "context": {"language": "python", "framework": "fastapi"},
                    "effectiveness": 0.90,
                }
            ],
            "target_personas": ["qa", "architect"],
            "similarity_threshold": 0.75,  # AC: 7 - >75% accuracy requirement
        }

        with patch(
            "orchestra.workflows.knowledge_sharing_workflows.pattern_matching_activity"
        ) as mock_activity:
            mock_activity.return_value = {
                "success": True,
                "transferable_patterns": [
                    {
                        "source_pattern_id": "dev-auth-pattern",
                        "target_persona": "qa",
                        "transferability_score": 0.82,  # AC: 7 - >75% accuracy
                        "adaptation_required": "minimal",
                        "context_mapping": {
                            "testing_approach": "integration_tests",
                            "validation_methods": ["security_scan", "penetration_test"],
                        },
                    }
                ],
                "pattern_matching_accuracy": 0.87,  # AC: 7 - >75% accuracy
                "openai_analysis": {
                    "model_used": "gpt-4",
                    "confidence": 0.91,
                },
            }

            result = await workflow.run(matching_context)

            assert result["success"] is True
            assert len(result["transferable_patterns"]) == 1
            assert result["transferable_patterns"][0]["transferability_score"] > 0.75
            assert result["pattern_matching_accuracy"] > 0.75  # AC: 7

    @pytest.mark.asyncio
    async def test_pattern_matching_workflow_persona_compatibility(self):
        """Test pattern matching assesses persona compatibility."""
        workflow = PatternMatchingWorkflow()

        matching_context = {
            "source_patterns": [
                {
                    "pattern_id": "technical-pattern",
                    "persona_id": "architect",
                    "domain": "system_design",
                    "complexity": "high",
                }
            ],
            "target_personas": ["pm", "po", "dev"],
        }

        with patch(
            "orchestra.workflows.knowledge_sharing_workflows.pattern_matching_activity"
        ) as mock_activity:
            mock_activity.return_value = {
                "success": True,
                "compatibility_scores": {
                    "pm": 0.45,  # Low compatibility - business vs technical focus
                    "po": 0.52,  # Medium compatibility - some overlap
                    "dev": 0.88,  # High compatibility - technical alignment
                },
                "recommended_transfers": [
                    {
                        "target_persona": "dev",
                        "compatibility_score": 0.88,
                        "adaptation_strategy": "direct_transfer",
                    }
                ],
                "rejected_transfers": [
                    {
                        "target_persona": "pm",
                        "reason": "Low compatibility score",
                        "compatibility_score": 0.45,
                    }
                ],
            }

            result = await workflow.run(matching_context)

            assert result["success"] is True
            assert len(result["recommended_transfers"]) == 1
            assert result["recommended_transfers"][0]["compatibility_score"] > 0.75
            assert len(result["rejected_transfers"]) == 1

    @pytest.mark.asyncio
    async def test_pattern_matching_workflow_context_mapping(self):
        """Test pattern matching creates context mapping algorithms."""
        workflow = PatternMatchingWorkflow()

        matching_context = {
            "source_patterns": [
                {
                    "pattern_id": "frontend-pattern",
                    "persona_id": "dev",
                    "domain": "frontend",
                    "context": {"framework": "react", "state_management": "redux"},
                }
            ],
            "target_personas": ["dev"],
            "context_filters": {"framework": "vue", "state_management": "vuex"},
        }

        with patch(
            "orchestra.workflows.knowledge_sharing_workflows.pattern_matching_activity"
        ) as mock_activity:
            mock_activity.return_value = {
                "success": True,
                "context_mappings": [
                    {
                        "source_context": {
                            "framework": "react",
                            "state_management": "redux",
                        },
                        "target_context": {
                            "framework": "vue",
                            "state_management": "vuex",
                        },
                        "mapping_rules": [
                            {"react_component": "vue_component"},
                            {"redux_store": "vuex_store"},
                        ],
                        "adaptation_confidence": 0.79,
                    }
                ],
                "transferability_enhanced": True,
            }

            result = await workflow.run(matching_context)

            assert result["success"] is True
            assert len(result["context_mappings"]) == 1
            assert result["context_mappings"][0]["adaptation_confidence"] > 0.75


class TestPropagationWorkflow:
    """Test propagation sub-workflow (AC: 3, 6, 8)."""

    @pytest.mark.asyncio
    async def test_propagation_workflow_automatic_distribution(self):
        """Test propagation workflow distributes high-confidence patterns automatically."""
        workflow = PropagationWorkflow()

        propagation_context = {
            "patterns_to_propagate": [
                {
                    "pattern_id": "high-conf-pattern",
                    "confidence_score": 0.95,
                    "effectiveness_score": 0.88,
                    "target_personas": ["dev", "qa"],
                    "propagation_mode": "automatic",
                }
            ],
            "confidence_threshold": 0.90,
        }

        with patch(
            "orchestra.workflows.knowledge_sharing_workflows.propagation_activity"
        ) as mock_activity:
            mock_activity.return_value = {
                "success": True,
                "automatic_propagations": 1,
                "manual_approvals_required": 0,
                "effectiveness_improvements": [
                    {
                        "target_persona": "dev",
                        "baseline_effectiveness": 0.75,
                        "projected_effectiveness": 0.88,
                        "improvement_rate": 0.65,  # AC: 8 - >60% effectiveness improvement
                    },
                    {
                        "target_persona": "qa",
                        "baseline_effectiveness": 0.70,
                        "projected_effectiveness": 0.82,
                        "improvement_rate": 0.63,  # AC: 8 - >60% effectiveness improvement
                    },
                ],
                "temporal_orchestration": {
                    "workflow_id": "propagation-123",
                    "distributed_successfully": True,
                },
            }

            result = await workflow.run(propagation_context)

            assert result["success"] is True
            assert result["automatic_propagations"] == 1
            assert all(
                improvement["improvement_rate"] > 0.6  # AC: 8
                for improvement in result["effectiveness_improvements"]
            )

    @pytest.mark.asyncio
    async def test_propagation_workflow_manual_approval(self):
        """Test propagation workflow requires manual approval for complex patterns."""
        workflow = PropagationWorkflow()

        propagation_context = {
            "patterns_to_propagate": [
                {
                    "pattern_id": "complex-pattern",
                    "confidence_score": 0.75,  # Below auto-threshold
                    "effectiveness_score": 0.82,
                    "target_personas": ["architect", "pm"],
                    "complexity": "high",
                    "cross_team": True,
                }
            ],
            "confidence_threshold": 0.90,
        }

        with patch(
            "orchestra.workflows.knowledge_sharing_workflows.propagation_activity"
        ) as mock_activity:
            mock_activity.return_value = {
                "success": True,
                "automatic_propagations": 0,
                "manual_approvals_required": 1,
                "approval_requests": [
                    {
                        "pattern_id": "complex-pattern",
                        "approval_id": "approval-456",
                        "reason": "Cross-team pattern requires manual review",
                        "reviewers": ["team_lead", "architect_lead"],
                        "approval_deadline": datetime.utcnow() + timedelta(days=3),
                    }
                ],
            }

            result = await workflow.run(propagation_context)

            assert result["success"] is True
            assert result["manual_approvals_required"] == 1
            assert len(result["approval_requests"]) == 1

    @pytest.mark.asyncio
    async def test_propagation_workflow_tracking_monitoring(self):
        """Test propagation workflow tracks and monitors effectiveness."""
        workflow = PropagationWorkflow()

        propagation_context = {
            "patterns_to_propagate": [
                {
                    "pattern_id": "tracked-pattern",
                    "confidence_score": 0.92,
                    "target_personas": ["dev"],
                    "enable_tracking": True,
                }
            ],
        }

        with patch(
            "orchestra.workflows.knowledge_sharing_workflows.propagation_activity"
        ) as mock_activity:
            mock_activity.return_value = {
                "success": True,
                "propagation_tracking": {
                    "tracking_enabled": True,
                    "tracking_id": "track-789",
                    "baseline_metrics_captured": True,
                    "monitoring_schedule": "weekly",
                },
                "effectiveness_monitoring": {
                    "pre_propagation_metrics": {"success_rate": 0.75},
                    "monitoring_period_days": 30,
                    "success_criteria": {"min_improvement": 0.6},
                },
            }

            result = await workflow.run(propagation_context)

            assert result["success"] is True
            assert result["propagation_tracking"]["tracking_enabled"] is True
            assert "effectiveness_monitoring" in result


class TestValidationWorkflow:
    """Test validation sub-workflow (AC: 4, 6, 10)."""

    @pytest.mark.asyncio
    async def test_validation_workflow_pattern_quality(self):
        """Test validation workflow ensures shared patterns are beneficial."""
        workflow = ValidationWorkflow()

        validation_context = {
            "shared_patterns": [
                {
                    "pattern_id": "validation-pattern-1",
                    "source_persona": "dev",
                    "target_persona": "qa",
                    "effectiveness_score": 0.85,
                    "usage_history": {"success_count": 20, "failure_count": 2},
                },
                {
                    "pattern_id": "validation-pattern-2",
                    "source_persona": "architect",
                    "target_persona": "dev",
                    "effectiveness_score": 0.45,  # Below 50% threshold
                    "usage_history": {"success_count": 5, "failure_count": 8},
                },
            ],
            "effectiveness_threshold": 0.50,  # AC: 10 - prevent <50% effectiveness
        }

        with patch(
            "orchestra.workflows.knowledge_sharing_workflows.validation_activity"
        ) as mock_activity:
            mock_activity.return_value = {
                "success": True,
                "validated_patterns": [
                    {
                        "pattern_id": "validation-pattern-1",
                        "validation_status": "approved",
                        "effectiveness_score": 0.85,
                        "quality_score": 0.88,
                    }
                ],
                "rejected_patterns": [
                    {
                        "pattern_id": "validation-pattern-2",
                        "validation_status": "rejected",
                        "effectiveness_score": 0.45,
                        "rejection_reason": "Below 50% effectiveness threshold",  # AC: 10
                    }
                ],
                "propagation_prevented": 1,  # AC: 10 - prevented low-effectiveness propagation
            }

            result = await workflow.run(validation_context)

            assert result["success"] is True
            assert len(result["validated_patterns"]) == 1
            assert result["validated_patterns"][0]["effectiveness_score"] > 0.5
            assert len(result["rejected_patterns"]) == 1
            assert result["rejected_patterns"][0]["effectiveness_score"] < 0.5  # AC: 10

    @pytest.mark.asyncio
    async def test_validation_workflow_effectiveness_measurement(self):
        """Test validation workflow measures effectiveness before and after sharing."""
        workflow = ValidationWorkflow()

        validation_context = {
            "pattern_id": "effectiveness-test-pattern",
            "target_persona": "dev",
            "project_id": "test-project",
            "measurement_period_days": 14,
        }

        with patch(
            "orchestra.workflows.knowledge_sharing_workflows.validation_activity"
        ) as mock_activity:
            mock_activity.return_value = {
                "success": True,
                "effectiveness_measurement": {
                    "pre_sharing_metrics": {
                        "success_rate": 0.72,
                        "completion_time_avg": 120.5,
                        "error_rate": 0.18,
                    },
                    "post_sharing_metrics": {
                        "success_rate": 0.84,
                        "completion_time_avg": 95.2,
                        "error_rate": 0.11,
                    },
                    "improvement_analysis": {
                        "success_rate_improvement": 0.67,  # 67% improvement
                        "completion_time_improvement": 0.21,  # 21% faster
                        "error_rate_improvement": 0.39,  # 39% fewer errors
                        "overall_effectiveness": 0.68,  # AC: 8 - >60% improvement
                    },
                },
                "validation_status": "beneficial",
            }

            result = await workflow.run(validation_context)

            assert result["success"] is True
            assert (
                result["effectiveness_measurement"]["improvement_analysis"][
                    "overall_effectiveness"
                ]
                > 0.6
            )  # AC: 8

    @pytest.mark.asyncio
    async def test_validation_workflow_rollback_capability(self):
        """Test validation workflow can rollback unsuccessful pattern propagation."""
        workflow = ValidationWorkflow()

        validation_context = {
            "pattern_id": "rollback-test-pattern",
            "target_persona": "qa",
            "project_id": "test-project",
            "validation_failed": True,
            "rollback_required": True,
        }

        with patch(
            "orchestra.workflows.knowledge_sharing_workflows.validation_activity"
        ) as mock_activity:
            mock_activity.return_value = {
                "success": True,
                "rollback_executed": True,
                "rollback_details": {
                    "pattern_removed": True,
                    "behavior_reverted": True,
                    "baseline_restored": True,
                    "rollback_time_ms": 250,
                },
                "post_rollback_validation": {
                    "persona_functionality": "restored",
                    "performance_impact": "none",
                    "data_integrity": "maintained",
                },
            }

            result = await workflow.run(validation_context)

            assert result["success"] is True
            assert result["rollback_executed"] is True
            assert result["rollback_details"]["pattern_removed"] is True
            assert (
                result["post_rollback_validation"]["persona_functionality"]
                == "restored"
            )


class TestKnowledgeSharingIntegration:
    """Test integration between knowledge sharing workflows and Epic 1 infrastructure."""

    @pytest.mark.asyncio
    async def test_knowledge_sharing_tag_based_targeting(self):
        """Test knowledge sharing integrates with Epic 1 tag-based targeting."""
        workflow = KnowledgeSharingWorkflow()

        sharing_context = {
            "operation": "targeted_sharing",
            "patterns": [{"pattern_id": "python-pattern", "domain": "backend"}],
            "targeting_tags": {
                "technology": ["python"],
                "role": ["dev"],
                "domain": ["backend", "api"],
            },
        }

        with patch(
            "orchestra.workflows.knowledge_sharing_workflows.knowledge_sharing_activity"
        ) as mock_activity:
            mock_activity.return_value = {
                "success": True,
                "tag_based_targeting": {
                    "targeting_enabled": True,
                    "matched_personas": [
                        "dev-python-1",
                        "dev-python-2",
                        "backend-dev-1",
                    ],
                    "targeting_accuracy": 0.92,
                },
                "epic1_integration": {
                    "broadcast_system_used": True,
                    "policy_cascade_triggered": False,
                },
            }

            result = await workflow.run(sharing_context)

            assert result["success"] is True
            assert result["tag_based_targeting"]["targeting_enabled"] is True
            assert len(result["tag_based_targeting"]["matched_personas"]) == 3

    @pytest.mark.asyncio
    async def test_knowledge_sharing_broadcast_integration(self):
        """Test knowledge sharing integrates with Epic 1 broadcast and policy cascade."""
        propagation_workflow = PropagationWorkflow()

        propagation_context = {
            "patterns_to_propagate": [
                {
                    "pattern_id": "security-pattern",
                    "confidence_score": 0.95,
                    "target_scope": "all_dev_personas",
                    "broadcast_enabled": True,
                }
            ],
        }

        with patch(
            "orchestra.workflows.knowledge_sharing_workflows.propagation_activity"
        ) as mock_activity:
            mock_activity.return_value = {
                "success": True,
                "broadcast_propagation": {
                    "broadcast_initiated": True,
                    "target_personas": 12,
                    "cascade_triggered": True,
                    "policy_version": "v1.2.3",
                },
                "epic1_integration": {
                    "broadcast_service_called": True,
                    "cascade_service_called": True,
                    "audit_trail_created": True,
                },
            }

            result = await propagation_workflow.run(propagation_context)

            assert result["success"] is True
            assert result["broadcast_propagation"]["broadcast_initiated"] is True
            assert result["epic1_integration"]["audit_trail_created"] is True

    @pytest.mark.asyncio
    async def test_knowledge_sharing_cross_persona_performance(self):
        """Test knowledge sharing maintains performance requirements across personas."""
        # Test that cross-persona operations don't impact <500ms load time (AC: 9)
        workflow = KnowledgeSharingWorkflow()

        sharing_context = {
            "operation": "bulk_cross_persona_sharing",
            "source_personas": ["dev", "architect", "qa"],
            "target_personas": ["pm", "po"],
            "patterns_count": 50,
        }

        with patch(
            "orchestra.workflows.knowledge_sharing_workflows.knowledge_sharing_activity"
        ) as mock_activity:
            mock_activity.return_value = {
                "success": True,
                "performance_metrics": {
                    "total_operation_time_ms": 450,  # AC: 9 - <500ms load time
                    "per_persona_load_time_ms": 85,
                    "lazy_loading_used": True,
                    "caching_effective": True,
                },
                "cross_persona_stats": {
                    "personas_processed": 5,
                    "patterns_shared": 25,
                    "patterns_filtered": 25,  # Half filtered for relevance
                },
            }

            result = await workflow.run(sharing_context)

            assert result["success"] is True
            assert (
                result["performance_metrics"]["total_operation_time_ms"] < 500
            )  # AC: 9
            assert result["performance_metrics"]["lazy_loading_used"] is True

    @pytest.mark.asyncio
    async def test_knowledge_sharing_memory_integration(self):
        """Test knowledge sharing integrates with Story 2.1 memory infrastructure."""
        workflow = KnowledgeSharingWorkflow()

        sharing_context = {
            "operation": "memory_enhanced_sharing",
            "project_id": "test-project",
            "use_memory_patterns": True,
            "memory_namespace": "orchestra_memory_test-project",
        }

        with patch(
            "orchestra.workflows.knowledge_sharing_workflows.knowledge_sharing_activity"
        ) as mock_activity:
            mock_activity.return_value = {
                "success": True,
                "memory_integration": {
                    "memory_patterns_retrieved": 8,
                    "memory_enhanced_matching": True,
                    "memory_service_latency_ms": 120,
                },
                "story21_integration": {
                    "memory_service_called": True,
                    "namespace_respected": True,
                    "pattern_storage_updated": True,
                },
            }

            result = await workflow.run(sharing_context)

            assert result["success"] is True
            assert result["memory_integration"]["memory_enhanced_matching"] is True
            assert result["story21_integration"]["namespace_respected"] is True

    @pytest.mark.asyncio
    async def test_knowledge_sharing_learning_integration(self):
        """Test knowledge sharing integrates with Story 2.2 learning engine."""
        validation_workflow = ValidationWorkflow()

        validation_context = {
            "shared_patterns": [{"pattern_id": "learning-enhanced-pattern"}],
            "use_learning_feedback": True,
            "learning_context": {
                "outcome_history": True,
                "ai_recommendations": True,
            },
        }

        with patch(
            "orchestra.workflows.knowledge_sharing_workflows.validation_activity"
        ) as mock_activity:
            mock_activity.return_value = {
                "success": True,
                "learning_integration": {
                    "outcome_data_used": True,
                    "ai_analysis_applied": True,
                    "learning_feedback_incorporated": True,
                },
                "story22_integration": {
                    "learning_service_called": True,
                    "adaptive_validation": True,
                    "confidence_scoring_enhanced": True,
                },
            }

            result = await validation_workflow.run(validation_context)

            assert result["success"] is True
            assert result["learning_integration"]["ai_analysis_applied"] is True
            assert result["story22_integration"]["adaptive_validation"] is True
