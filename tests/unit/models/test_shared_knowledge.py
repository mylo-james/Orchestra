"""Tests for shared knowledge data models based on Story 2.3 PRD requirements."""

from datetime import datetime, timedelta

import pytest

from orchestra.models.shared_knowledge import (
    PatternMapping,
    PropagationRule,
    SharedKnowledge,
    TargetingTag,
    ValidationMetric,
)


class TestSharedKnowledge:
    """Test SharedKnowledge data model for cross-persona knowledge records (AC: 1)."""

    def test_shared_knowledge_creation(self):
        """Test SharedKnowledge creation for cross-persona knowledge sharing."""
        shared_knowledge = SharedKnowledge(
            knowledge_id="sk-auth-pattern-1",
            source_persona_id="dev",
            source_project_id="project-a",
            pattern_id="auth-success-pattern",
            knowledge_type="success_pattern",
            title="Authentication Implementation Best Practices",
            description="Comprehensive testing and validation leads to successful auth implementations",
            content={
                "pattern_data": {
                    "conditions": [
                        {"metric": "test_coverage", "operator": ">=", "value": 0.90},
                        {
                            "metric": "security_validation",
                            "operator": "==",
                            "value": True,
                        },
                    ],
                    "outcomes": [
                        {"metric": "success_rate", "value": 0.92},
                        {"metric": "error_rate", "value": 0.05},
                    ],
                },
                "implementation_guide": {
                    "steps": [
                        "design_tests",
                        "implement_validation",
                        "run_security_scan",
                    ],
                    "best_practices": ["use_established_libraries", "validate_inputs"],
                },
            },
            transferability_metadata={
                "applicable_domains": ["authentication", "security", "user_management"],
                "applicable_personas": ["dev", "qa", "architect"],
                "complexity_level": "medium",
                "technology_agnostic": True,
            },
            effectiveness_score=0.88,
            usage_count=15,
            success_rate=0.92,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        assert shared_knowledge.knowledge_id == "sk-auth-pattern-1"
        assert shared_knowledge.source_persona_id == "dev"
        assert shared_knowledge.knowledge_type == "success_pattern"
        assert shared_knowledge.effectiveness_score == 0.88
        assert shared_knowledge.success_rate == 0.92
        assert "applicable_personas" in shared_knowledge.transferability_metadata
        assert "pattern_data" in shared_knowledge.content

    def test_shared_knowledge_types(self):
        """Test SharedKnowledge supports different knowledge types."""
        success_knowledge = SharedKnowledge(
            knowledge_id="sk-success-1",
            source_persona_id="dev",
            source_project_id="project-a",
            pattern_id="success-pattern-1",
            knowledge_type="success_pattern",
            title="Success Pattern Knowledge",
            description="Knowledge about successful patterns",
            content={"success_indicators": ["high_quality", "fast_completion"]},
            transferability_metadata={"applicable_personas": ["dev", "qa"]},
            effectiveness_score=0.85,
            usage_count=10,
            success_rate=0.90,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        failure_knowledge = SharedKnowledge(
            knowledge_id="sk-failure-1",
            source_persona_id="dev",
            source_project_id="project-a",
            pattern_id="failure-pattern-1",
            knowledge_type="failure_pattern",
            title="Common Failure Pattern",
            description="Knowledge about patterns to avoid",
            content={"failure_indicators": ["low_coverage", "missing_validation"]},
            transferability_metadata={
                "applicable_personas": ["dev", "qa", "architect"]
            },
            effectiveness_score=0.78,
            usage_count=8,
            success_rate=0.85,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        optimization_knowledge = SharedKnowledge(
            knowledge_id="sk-optimization-1",
            source_persona_id="architect",
            source_project_id="project-a",
            pattern_id="optimization-pattern-1",
            knowledge_type="optimization_pattern",
            title="Performance Optimization Techniques",
            description="Knowledge about performance improvements",
            content={
                "optimization_techniques": ["caching", "lazy_loading", "indexing"]
            },
            transferability_metadata={"applicable_personas": ["dev", "architect"]},
            effectiveness_score=0.82,
            usage_count=12,
            success_rate=0.88,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        assert success_knowledge.knowledge_type == "success_pattern"
        assert failure_knowledge.knowledge_type == "failure_pattern"
        assert optimization_knowledge.knowledge_type == "optimization_pattern"

    def test_shared_knowledge_transferability_assessment(self):
        """Test SharedKnowledge assesses transferability between personas."""
        knowledge = SharedKnowledge(
            knowledge_id="sk-transferable",
            source_persona_id="dev",
            source_project_id="project-a",
            pattern_id="transferable-pattern",
            knowledge_type="success_pattern",
            title="Highly Transferable Pattern",
            description="Pattern with high cross-persona applicability",
            content={
                "universal_principles": ["thorough_testing", "clear_documentation"]
            },
            transferability_metadata={
                "applicable_personas": ["dev", "qa", "architect", "pm"],
                "transferability_scores": {
                    "dev": 0.95,
                    "qa": 0.88,
                    "architect": 0.82,
                    "pm": 0.65,
                },
                "adaptation_required": {
                    "dev": "minimal",
                    "qa": "moderate",
                    "architect": "moderate",
                    "pm": "significant",
                },
            },
            effectiveness_score=0.90,
            usage_count=20,
            success_rate=0.93,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Test transferability assessment
        dev_transferability = knowledge.assess_transferability("dev")
        qa_transferability = knowledge.assess_transferability("qa")
        pm_transferability = knowledge.assess_transferability("pm")

        assert dev_transferability["score"] == 0.95
        assert dev_transferability["adaptation"] == "minimal"
        assert qa_transferability["score"] == 0.88
        assert pm_transferability["score"] == 0.65
        assert pm_transferability["adaptation"] == "significant"

    def test_shared_knowledge_usage_tracking(self):
        """Test SharedKnowledge tracks usage and success metrics."""
        knowledge = SharedKnowledge(
            knowledge_id="sk-usage-tracking",
            source_persona_id="dev",
            source_project_id="project-a",
            pattern_id="usage-pattern",
            knowledge_type="success_pattern",
            title="Usage Tracking Pattern",
            description="Pattern with usage tracking",
            content={},
            transferability_metadata={"applicable_personas": ["dev", "qa"]},
            effectiveness_score=0.85,
            usage_count=5,
            success_rate=0.80,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Simulate successful usage
        old_usage_count = knowledge.usage_count
        old_success_rate = knowledge.success_rate

        knowledge.record_usage(success=True)

        assert knowledge.usage_count == old_usage_count + 1
        # Success rate should improve or stay the same
        assert knowledge.success_rate >= old_success_rate

        # Simulate failed usage
        knowledge.record_usage(success=False)

        # Usage count increases but success rate may decrease
        assert knowledge.usage_count == old_usage_count + 2


class TestPatternMapping:
    """Test PatternMapping data model for cross-persona pattern relationships (AC: 2, 7)."""

    def test_pattern_mapping_creation(self):
        """Test PatternMapping creation for similar patterns across personas."""
        mapping = PatternMapping(
            mapping_id="pm-auth-mapping-1",
            source_pattern_id="dev-auth-pattern",
            target_pattern_id="qa-auth-pattern",
            source_persona_id="dev",
            target_persona_id="qa",
            project_id="test-project",
            similarity_score=0.85,
            transferability_score=0.78,  # AC: 7 - >75% accuracy requirement
            mapping_type="complementary",
            context_mapping={
                "dev_context": {
                    "focus": "implementation",
                    "tools": ["IDE", "debugger", "unit_tests"],
                    "metrics": ["code_quality", "performance"],
                },
                "qa_context": {
                    "focus": "validation",
                    "tools": ["test_framework", "automation", "security_scanner"],
                    "metrics": ["test_coverage", "defect_rate"],
                },
                "mapping_rules": [
                    {"dev_implementation": "qa_test_cases"},
                    {"dev_unit_tests": "qa_integration_tests"},
                    {"dev_performance_check": "qa_load_testing"},
                ],
            },
            confidence_score=0.82,
            ai_analysis={
                "model_used": "gpt-4",
                "analysis_confidence": 0.89,
                "pattern_similarity_factors": [
                    "domain_alignment",
                    "outcome_similarity",
                    "context_compatibility",
                ],
            },
            created_at=datetime.utcnow(),
            validated=True,
        )

        assert mapping.mapping_id == "pm-auth-mapping-1"
        assert mapping.source_persona_id == "dev"
        assert mapping.target_persona_id == "qa"
        assert mapping.similarity_score == 0.85
        assert mapping.transferability_score > 0.75  # AC: 7 - >75% accuracy
        assert mapping.mapping_type == "complementary"
        assert "mapping_rules" in mapping.context_mapping

    def test_pattern_mapping_types(self):
        """Test PatternMapping supports different mapping types."""
        complementary_mapping = PatternMapping(
            mapping_id="complementary-1",
            source_pattern_id="dev-pattern",
            target_pattern_id="qa-pattern",
            source_persona_id="dev",
            target_persona_id="qa",
            project_id="test-project",
            similarity_score=0.80,
            transferability_score=0.78,
            mapping_type="complementary",
            context_mapping={"relationship": "complementary_workflow"},
            confidence_score=0.85,
            created_at=datetime.utcnow(),
            validated=True,
        )

        equivalent_mapping = PatternMapping(
            mapping_id="equivalent-1",
            source_pattern_id="dev-pattern-a",
            target_pattern_id="dev-pattern-b",
            source_persona_id="dev",
            target_persona_id="dev",
            project_id="test-project",
            similarity_score=0.95,
            transferability_score=0.92,
            mapping_type="equivalent",
            context_mapping={"relationship": "same_outcome_different_approach"},
            confidence_score=0.90,
            created_at=datetime.utcnow(),
            validated=True,
        )

        derivative_mapping = PatternMapping(
            mapping_id="derivative-1",
            source_pattern_id="architect-pattern",
            target_pattern_id="dev-implementation-pattern",
            source_persona_id="architect",
            target_persona_id="dev",
            project_id="test-project",
            similarity_score=0.75,
            transferability_score=0.80,
            mapping_type="derivative",
            context_mapping={"relationship": "high_level_to_implementation"},
            confidence_score=0.78,
            created_at=datetime.utcnow(),
            validated=True,
        )

        assert complementary_mapping.mapping_type == "complementary"
        assert equivalent_mapping.mapping_type == "equivalent"
        assert derivative_mapping.mapping_type == "derivative"

    def test_pattern_mapping_accuracy_validation(self):
        """Test PatternMapping validates accuracy requirements."""
        # Test mapping meeting accuracy requirement (>75%)
        high_accuracy_mapping = PatternMapping(
            mapping_id="high-accuracy",
            source_pattern_id="source-pattern",
            target_pattern_id="target-pattern",
            source_persona_id="dev",
            target_persona_id="qa",
            project_id="test-project",
            similarity_score=0.88,
            transferability_score=0.82,  # AC: 7 - >75% accuracy
            mapping_type="complementary",
            context_mapping={},
            confidence_score=0.85,
            created_at=datetime.utcnow(),
            validated=True,
        )
        assert high_accuracy_mapping.transferability_score > 0.75

        # Test mapping below accuracy requirement
        with pytest.raises(ValueError, match="transferability_score must be > 0.75"):
            PatternMapping(
                mapping_id="low-accuracy",
                source_pattern_id="source-pattern",
                target_pattern_id="target-pattern",
                source_persona_id="dev",
                target_persona_id="qa",
                project_id="test-project",
                similarity_score=0.70,
                transferability_score=0.65,  # Below 75% requirement
                mapping_type="complementary",
                context_mapping={},
                confidence_score=0.70,
                created_at=datetime.utcnow(),
                validated=False,
            )

    def test_pattern_mapping_ai_integration(self):
        """Test PatternMapping integrates with AI analysis."""
        mapping = PatternMapping(
            mapping_id="ai-mapping",
            source_pattern_id="ai-source-pattern",
            target_pattern_id="ai-target-pattern",
            source_persona_id="dev",
            target_persona_id="architect",
            project_id="test-project",
            similarity_score=0.87,
            transferability_score=0.83,
            mapping_type="derivative",
            context_mapping={},
            confidence_score=0.85,
            ai_analysis={
                "model_used": "gpt-4",
                "request_id": "req-mapping-123",
                "analysis_confidence": 0.91,
                "tokens_used": 2150,
                "analysis_factors": [
                    "semantic_similarity",
                    "outcome_alignment",
                    "context_compatibility",
                    "persona_role_analysis",
                ],
                "recommendations": [
                    "Direct transfer with minimal adaptation",
                    "Focus on implementation details for dev persona",
                ],
            },
            created_at=datetime.utcnow(),
            validated=True,
        )

        assert mapping.ai_analysis["model_used"] == "gpt-4"
        assert mapping.ai_analysis["analysis_confidence"] == 0.91
        assert "semantic_similarity" in mapping.ai_analysis["analysis_factors"]


class TestPropagationRule:
    """Test PropagationRule data model for knowledge distribution governance (AC: 3)."""

    def test_propagation_rule_creation(self):
        """Test PropagationRule creation for automatic vs manual sharing decisions."""
        rule = PropagationRule(
            rule_id="prop-rule-1",
            rule_name="High Confidence Auto-Propagation",
            project_id="test-project",
            rule_type="automatic",
            conditions={
                "min_confidence_score": 0.90,
                "min_effectiveness_score": 0.85,
                "min_transferability_score": 0.80,
                "source_persona_whitelist": ["dev", "architect", "qa"],
                "target_persona_whitelist": ["dev", "qa"],
            },
            actions={
                "propagation_mode": "automatic",
                "approval_required": False,
                "notification_required": True,
                "tracking_enabled": True,
            },
            priority="high",
            active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        assert rule.rule_id == "prop-rule-1"
        assert rule.rule_type == "automatic"
        assert rule.conditions["min_confidence_score"] == 0.90
        assert rule.actions["approval_required"] is False
        assert rule.priority == "high"
        assert rule.active is True

    def test_propagation_rule_types(self):
        """Test PropagationRule supports different rule types."""
        automatic_rule = PropagationRule(
            rule_id="auto-rule",
            rule_name="Automatic High-Confidence Propagation",
            project_id="test-project",
            rule_type="automatic",
            conditions={"min_confidence_score": 0.95},
            actions={"propagation_mode": "automatic", "approval_required": False},
            priority="high",
            active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        manual_rule = PropagationRule(
            rule_id="manual-rule",
            rule_name="Manual Review for Cross-Team Sharing",
            project_id="test-project",
            rule_type="manual",
            conditions={"cross_team": True, "complexity": "high"},
            actions={"propagation_mode": "manual", "approval_required": True},
            priority="medium",
            active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        conditional_rule = PropagationRule(
            rule_id="conditional-rule",
            rule_name="Conditional Propagation Based on Domain",
            project_id="test-project",
            rule_type="conditional",
            conditions={"domain": "security", "min_effectiveness_score": 0.80},
            actions={"propagation_mode": "conditional", "approval_required": True},
            priority="high",
            active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        assert automatic_rule.rule_type == "automatic"
        assert manual_rule.rule_type == "manual"
        assert conditional_rule.rule_type == "conditional"

    def test_propagation_rule_evaluation(self):
        """Test PropagationRule can evaluate knowledge for propagation decisions."""
        rule = PropagationRule(
            rule_id="eval-rule",
            rule_name="Evaluation Test Rule",
            project_id="test-project",
            rule_type="automatic",
            conditions={
                "min_confidence_score": 0.85,
                "min_effectiveness_score": 0.80,
                "allowed_knowledge_types": ["success_pattern", "optimization_pattern"],
                "source_persona_whitelist": ["dev", "architect"],
            },
            actions={"propagation_mode": "automatic", "approval_required": False},
            priority="medium",
            active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Knowledge that meets criteria
        qualifying_knowledge = SharedKnowledge(
            knowledge_id="qualifying-knowledge",
            source_persona_id="dev",
            source_project_id="test-project",
            pattern_id="qualifying-pattern",
            knowledge_type="success_pattern",
            title="Qualifying Knowledge",
            description="Knowledge that meets propagation criteria",
            content={},
            transferability_metadata={},
            effectiveness_score=0.88,  # Above 0.80 threshold
            usage_count=10,
            success_rate=0.90,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Knowledge that doesn't meet criteria
        non_qualifying_knowledge = SharedKnowledge(
            knowledge_id="non-qualifying-knowledge",
            source_persona_id="pm",  # Not in whitelist
            source_project_id="test-project",
            pattern_id="non-qualifying-pattern",
            knowledge_type="failure_pattern",  # Not in allowed types
            title="Non-Qualifying Knowledge",
            description="Knowledge that doesn't meet criteria",
            content={},
            transferability_metadata={},
            effectiveness_score=0.75,  # Below 0.80 threshold
            usage_count=3,
            success_rate=0.70,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Test rule evaluation
        qualifying_result = rule.evaluate_knowledge(qualifying_knowledge)
        non_qualifying_result = rule.evaluate_knowledge(non_qualifying_knowledge)

        assert qualifying_result["should_propagate"] is True
        assert qualifying_result["propagation_mode"] == "automatic"
        assert non_qualifying_result["should_propagate"] is False
        assert any(
            "effectiveness_score too low" in reason
            for reason in non_qualifying_result["rejection_reasons"]
        )


class TestTargetingTag:
    """Test TargetingTag data model for Epic 1 integration (AC: 5)."""

    def test_targeting_tag_creation(self):
        """Test TargetingTag creation for tag-based persona targeting."""
        tag = TargetingTag(
            tag_id="tag-python-dev",
            tag_name="Python Developers",
            tag_type="technology",
            tag_value="python",
            project_id="test-project",
            target_criteria={
                "persona_roles": ["dev"],
                "technology_stack": ["python"],
                "experience_level": ["intermediate", "senior"],
                "domains": ["backend", "api", "data"],
            },
            matched_personas=[
                "dev-python-1",
                "dev-python-2",
                "backend-dev-1",
                "fullstack-dev-python",
            ],
            hierarchical_tags={
                "parent_tags": ["technology", "programming_language"],
                "child_tags": ["python3", "django", "fastapi", "flask"],
            },
            active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        assert tag.tag_id == "tag-python-dev"
        assert tag.tag_type == "technology"
        assert tag.tag_value == "python"
        assert len(tag.matched_personas) == 4
        assert "backend" in tag.target_criteria["domains"]
        assert "python3" in tag.hierarchical_tags["child_tags"]

    def test_targeting_tag_types(self):
        """Test TargetingTag supports different tag types."""
        technology_tag = TargetingTag(
            tag_id="tech-react",
            tag_name="React Developers",
            tag_type="technology",
            tag_value="react",
            project_id="test-project",
            target_criteria={"technology_stack": ["react", "javascript"]},
            matched_personas=["frontend-dev-1", "fullstack-dev-2"],
            hierarchical_tags={},
            active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        role_tag = TargetingTag(
            tag_id="role-qa",
            tag_name="Quality Assurance Engineers",
            tag_type="role",
            tag_value="qa",
            project_id="test-project",
            target_criteria={"persona_roles": ["qa", "test_engineer"]},
            matched_personas=["qa-1", "qa-automation-1", "test-lead-1"],
            hierarchical_tags={},
            active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        domain_tag = TargetingTag(
            tag_id="domain-fintech",
            tag_name="Financial Technology Domain",
            tag_type="domain",
            tag_value="fintech",
            project_id="test-project",
            target_criteria={"domains": ["fintech", "payments", "banking"]},
            matched_personas=["fintech-dev-1", "payments-architect-1"],
            hierarchical_tags={},
            active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        assert technology_tag.tag_type == "technology"
        assert role_tag.tag_type == "role"
        assert domain_tag.tag_type == "domain"

    def test_targeting_tag_hierarchical_structure(self):
        """Test TargetingTag supports hierarchical grouping."""
        parent_tag = TargetingTag(
            tag_id="parent-backend",
            tag_name="Backend Development",
            tag_type="domain",
            tag_value="backend",
            project_id="test-project",
            target_criteria={"domains": ["backend", "api", "database"]},
            matched_personas=["backend-dev-1", "api-dev-1", "db-admin-1"],
            hierarchical_tags={
                "parent_tags": ["development"],
                "child_tags": ["api_development", "database_design", "microservices"],
            },
            active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        child_tag = TargetingTag(
            tag_id="child-api",
            tag_name="API Development",
            tag_type="specialization",
            tag_value="api_development",
            project_id="test-project",
            target_criteria={"specializations": ["rest_api", "graphql", "grpc"]},
            matched_personas=["api-dev-1", "api-architect-1"],
            hierarchical_tags={
                "parent_tags": ["backend", "development"],
                "child_tags": ["rest_api", "graphql_api", "grpc_api"],
            },
            active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Test hierarchical relationships
        assert "api_development" in parent_tag.hierarchical_tags["child_tags"]
        assert "backend" in child_tag.hierarchical_tags["parent_tags"]

        # Test tag inheritance
        inherited_personas = parent_tag.get_inherited_personas([child_tag])
        assert "api-dev-1" in inherited_personas  # Should be in both parent and child

    def test_targeting_tag_epic1_integration(self):
        """Test TargetingTag integrates with Epic 1 tag-based targeting."""
        tag = TargetingTag(
            tag_id="epic1-integration-tag",
            tag_name="Epic 1 Integration Test",
            tag_type="technology",
            tag_value="python",
            project_id="test-project",
            target_criteria={"technology_stack": ["python"]},
            matched_personas=["dev-python-1"],
            hierarchical_tags={},
            active=True,
            epic1_integration={
                "broadcast_compatible": True,
                "policy_cascade_enabled": True,
                "targeting_service_id": "epic1-targeting-service",
            },
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        assert tag.epic1_integration["broadcast_compatible"] is True
        assert tag.epic1_integration["policy_cascade_enabled"] is True
        assert "targeting_service_id" in tag.epic1_integration


class TestValidationMetric:
    """Test ValidationMetric data model for shared pattern quality control (AC: 4, 10)."""

    def test_validation_metric_creation(self):
        """Test ValidationMetric creation for effectiveness measurement."""
        metric = ValidationMetric(
            metric_id="vm-auth-pattern-validation",
            shared_knowledge_id="sk-auth-pattern-1",
            target_persona_id="qa",
            project_id="test-project",
            validation_type="effectiveness_measurement",
            pre_sharing_metrics={
                "success_rate": 0.72,
                "completion_time_avg": 120.5,
                "error_rate": 0.18,
                "quality_score": 0.75,
            },
            post_sharing_metrics={
                "success_rate": 0.84,
                "completion_time_avg": 95.2,
                "error_rate": 0.11,
                "quality_score": 0.88,
            },
            improvement_analysis={
                "success_rate_improvement": 0.67,  # 67% improvement
                "completion_time_improvement": 0.21,  # 21% faster
                "error_rate_improvement": 0.39,  # 39% fewer errors
                "quality_improvement": 0.17,  # 17% higher quality
                "overall_effectiveness": 0.68,  # AC: 8 - >60% improvement
            },
            effectiveness_threshold=0.50,  # AC: 10 - prevent <50% effectiveness
            validation_status="beneficial",
            measurement_period_days=14,
            measurement_start=datetime.utcnow() - timedelta(days=14),
            measurement_end=datetime.utcnow(),
            created_at=datetime.utcnow(),
        )

        assert metric.metric_id == "vm-auth-pattern-validation"
        assert metric.validation_type == "effectiveness_measurement"
        assert metric.improvement_analysis["overall_effectiveness"] > 0.6  # AC: 8
        assert (
            metric.improvement_analysis["overall_effectiveness"]
            > metric.effectiveness_threshold
        )  # AC: 10
        assert metric.validation_status == "beneficial"

    def test_validation_metric_effectiveness_threshold(self):
        """Test ValidationMetric enforces effectiveness threshold."""
        # Test metric above effectiveness threshold
        beneficial_metric = ValidationMetric(
            metric_id="beneficial-metric",
            shared_knowledge_id="sk-beneficial",
            target_persona_id="dev",
            project_id="test-project",
            validation_type="effectiveness_measurement",
            pre_sharing_metrics={"success_rate": 0.70},
            post_sharing_metrics={"success_rate": 0.85},
            improvement_analysis={"overall_effectiveness": 0.65},  # Above 50% threshold
            effectiveness_threshold=0.50,
            validation_status="beneficial",
            measurement_period_days=14,
            measurement_start=datetime.utcnow() - timedelta(days=14),
            measurement_end=datetime.utcnow(),
            created_at=datetime.utcnow(),
        )

        # Test metric below effectiveness threshold
        harmful_metric = ValidationMetric(
            metric_id="harmful-metric",
            shared_knowledge_id="sk-harmful",
            target_persona_id="dev",
            project_id="test-project",
            validation_type="effectiveness_measurement",
            pre_sharing_metrics={"success_rate": 0.80},
            post_sharing_metrics={"success_rate": 0.65},
            improvement_analysis={"overall_effectiveness": 0.35},  # Below 50% threshold
            effectiveness_threshold=0.50,
            validation_status="harmful",  # AC: 10 - prevent propagation
            measurement_period_days=14,
            measurement_start=datetime.utcnow() - timedelta(days=14),
            measurement_end=datetime.utcnow(),
            created_at=datetime.utcnow(),
        )

        assert beneficial_metric.should_allow_propagation() is True
        assert harmful_metric.should_allow_propagation() is False  # AC: 10
        assert beneficial_metric.improvement_analysis["overall_effectiveness"] > 0.5
        assert harmful_metric.improvement_analysis["overall_effectiveness"] < 0.5

    def test_validation_metric_rollback_capability(self):
        """Test ValidationMetric supports rollback for unsuccessful propagation."""
        metric = ValidationMetric(
            metric_id="rollback-metric",
            shared_knowledge_id="sk-rollback-test",
            target_persona_id="qa",
            project_id="test-project",
            validation_type="effectiveness_measurement",
            pre_sharing_metrics={"success_rate": 0.85, "error_rate": 0.10},
            post_sharing_metrics={"success_rate": 0.70, "error_rate": 0.25},
            improvement_analysis={"overall_effectiveness": 0.30},  # Poor effectiveness
            effectiveness_threshold=0.50,
            validation_status="harmful",
            rollback_required=True,
            rollback_data={
                "rollback_triggered": True,
                "rollback_reason": "Effectiveness below 50% threshold",
                "rollback_actions": [
                    "remove_shared_pattern",
                    "restore_baseline_behavior",
                    "notify_stakeholders",
                ],
                "rollback_completed": True,
            },
            measurement_period_days=7,
            measurement_start=datetime.utcnow() - timedelta(days=7),
            measurement_end=datetime.utcnow(),
            created_at=datetime.utcnow(),
        )

        assert metric.rollback_required is True
        assert metric.rollback_data["rollback_triggered"] is True
        assert "remove_shared_pattern" in metric.rollback_data["rollback_actions"]
        assert metric.rollback_data["rollback_completed"] is True

    def test_validation_metric_quality_assessment(self):
        """Test ValidationMetric assesses pattern quality and relevance."""
        metric = ValidationMetric(
            metric_id="quality-metric",
            shared_knowledge_id="sk-quality-test",
            target_persona_id="dev",
            project_id="test-project",
            validation_type="quality_assessment",
            pre_sharing_metrics={},
            post_sharing_metrics={},
            improvement_analysis={},
            effectiveness_threshold=0.50,
            validation_status="under_review",
            quality_assessment={
                "relevance_score": 0.88,
                "applicability_score": 0.82,
                "clarity_score": 0.90,
                "completeness_score": 0.85,
                "overall_quality_score": 0.86,
                "quality_threshold": 0.75,
            },
            measurement_period_days=0,  # Quality assessment doesn't require measurement period
            measurement_start=datetime.utcnow(),
            measurement_end=datetime.utcnow(),
            created_at=datetime.utcnow(),
        )

        assert metric.validation_type == "quality_assessment"
        assert metric.quality_assessment["overall_quality_score"] > 0.75
        assert metric.quality_assessment["relevance_score"] == 0.88
        assert metric.meets_quality_threshold() is True


class TestSharedKnowledgeModelIntegration:
    """Test integration between shared knowledge data models."""

    def test_shared_knowledge_models_complete_workflow(self):
        """Test shared knowledge models work together in complete sharing workflow."""
        # Step 1: Shared Knowledge
        knowledge = SharedKnowledge(
            knowledge_id="workflow-knowledge",
            source_persona_id="dev",
            source_project_id="workflow-project",
            pattern_id="workflow-pattern",
            knowledge_type="success_pattern",
            title="Workflow Integration Test",
            description="Complete workflow test knowledge",
            content={"workflow_steps": ["analyze", "implement", "validate"]},
            transferability_metadata={"applicable_personas": ["dev", "qa"]},
            effectiveness_score=0.88,
            usage_count=10,
            success_rate=0.90,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Step 2: Pattern Mapping
        mapping = PatternMapping(
            mapping_id="workflow-mapping",
            source_pattern_id="workflow-pattern",
            target_pattern_id="qa-workflow-pattern",
            source_persona_id="dev",
            target_persona_id="qa",
            project_id="workflow-project",
            similarity_score=0.85,
            transferability_score=0.80,
            mapping_type="complementary",
            context_mapping={"dev_to_qa_mapping": True},
            confidence_score=0.82,
            created_at=datetime.utcnow(),
            validated=True,
        )

        # Step 3: Propagation Rule
        rule = PropagationRule(
            rule_id="workflow-rule",
            rule_name="Workflow Test Rule",
            project_id="workflow-project",
            rule_type="automatic",
            conditions={"min_effectiveness_score": 0.80},
            actions={"propagation_mode": "automatic"},
            priority="medium",
            active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Step 4: Targeting Tag
        tag = TargetingTag(
            tag_id="workflow-tag",
            tag_name="Workflow Test Tag",
            tag_type="role",
            tag_value="qa",
            project_id="workflow-project",
            target_criteria={"persona_roles": ["qa"]},
            matched_personas=["qa-1"],
            hierarchical_tags={},
            active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Step 5: Validation Metric
        metric = ValidationMetric(
            metric_id="workflow-metric",
            shared_knowledge_id="workflow-knowledge",
            target_persona_id="qa",
            project_id="workflow-project",
            validation_type="effectiveness_measurement",
            pre_sharing_metrics={"success_rate": 0.75},
            post_sharing_metrics={"success_rate": 0.88},
            improvement_analysis={"overall_effectiveness": 0.65},
            effectiveness_threshold=0.50,
            validation_status="beneficial",
            measurement_period_days=14,
            measurement_start=datetime.utcnow() - timedelta(days=14),
            measurement_end=datetime.utcnow(),
            created_at=datetime.utcnow(),
        )

        # Test workflow integration
        assert knowledge.knowledge_id == metric.shared_knowledge_id
        assert mapping.source_pattern_id == knowledge.pattern_id
        assert mapping.target_persona_id == metric.target_persona_id
        assert rule.project_id == knowledge.source_project_id
        assert tag.project_id == knowledge.source_project_id

        # Test workflow decisions
        rule_evaluation = rule.evaluate_knowledge(knowledge)
        assert (
            rule_evaluation["should_propagate"] is True
        )  # Meets effectiveness threshold

        tag_match = tag.matches_persona("qa-1")
        assert tag_match is True  # QA persona matches tag

        metric_validation = metric.should_allow_propagation()
        assert metric_validation is True  # Above effectiveness threshold

    def test_shared_knowledge_models_performance_requirements(self):
        """Test shared knowledge models meet performance requirements."""
        # Test lazy loading and performance constraints (AC: 9)
        start_time = datetime.utcnow()

        # Create multiple shared knowledge objects (simulating lazy loading)
        knowledge_objects = []
        for i in range(50):  # Simulate batch processing
            knowledge = SharedKnowledge(
                knowledge_id=f"perf-knowledge-{i}",
                source_persona_id="dev",
                source_project_id="perf-project",
                pattern_id=f"perf-pattern-{i}",
                knowledge_type="success_pattern",
                title=f"Performance Test Knowledge {i}",
                description=f"Performance test {i}",
                content={"test_data": f"data_{i}"},
                transferability_metadata={"applicable_personas": ["dev"]},
                effectiveness_score=0.80,
                usage_count=1,
                success_rate=0.85,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                lazy_loaded=True,  # AC: 9 - lazy loading for performance
            )
            knowledge_objects.append(knowledge)

        end_time = datetime.utcnow()
        processing_time_ms = (end_time - start_time).total_seconds() * 1000

        # Should complete quickly to maintain <500ms load time (AC: 9)
        assert processing_time_ms < 200  # Model creation should be very fast
        assert len(knowledge_objects) == 50
        assert all(k.lazy_loaded for k in knowledge_objects)

    def test_shared_knowledge_models_epic1_integration(self):
        """Test shared knowledge models integrate with Epic 1 infrastructure."""
        # Test integration with Epic 1 tag-based targeting and broadcast systems
        knowledge = SharedKnowledge(
            knowledge_id="epic1-integration-knowledge",
            source_persona_id="dev",
            source_project_id="epic1-project",
            pattern_id="epic1-pattern",
            knowledge_type="success_pattern",
            title="Epic 1 Integration Knowledge",
            description="Knowledge with Epic 1 integration",
            content={},
            transferability_metadata={"applicable_personas": ["dev", "qa"]},
            effectiveness_score=0.85,
            usage_count=5,
            success_rate=0.88,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            epic1_integration={
                "tag_based_targeting": True,
                "broadcast_compatible": True,
                "policy_cascade_enabled": True,
            },
        )

        tag = TargetingTag(
            tag_id="epic1-tag",
            tag_name="Epic 1 Integration Tag",
            tag_type="technology",
            tag_value="python",
            project_id="epic1-project",
            target_criteria={"technology_stack": ["python"]},
            matched_personas=["dev-python-1", "qa-python-1"],
            hierarchical_tags={},
            active=True,
            epic1_integration={
                "broadcast_service_id": "epic1-broadcast",
                "targeting_service_id": "epic1-targeting",
            },
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Test Epic 1 integration
        assert knowledge.epic1_integration["tag_based_targeting"] is True
        assert knowledge.epic1_integration["broadcast_compatible"] is True
        assert tag.epic1_integration["broadcast_service_id"] == "epic1-broadcast"

        # Test cross-system compatibility
        assert knowledge.source_project_id == tag.project_id
        assert len(tag.matched_personas) == 2  # Multiple personas targeted
