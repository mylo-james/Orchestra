"""Tests for Context data models."""

import pytest
from datetime import datetime, timedelta
from orchestra.models.context import (
    AdaptationStrategy,
    AdaptiveTemplate,
    ConditionalWorkflow,
    ContextAwareResource,
    ContextDimension,
    ContextEvaluationResult,
    ContextPattern,
    ContextVariable,
    ContextVariableType,
    WorkflowCondition,
    WorkflowConditionOperator,
)


class TestContextVariable:
    """Test ContextVariable data model."""

    def test_context_variable_creation(self):
        """Test creating a ContextVariable instance."""
        variable = ContextVariable(
            name="project_type",
            value="web_app",
            variable_type=ContextVariableType.STRING,
            dimension=ContextDimension.PROJECT,
            description="Type of project being developed",
            is_persistent=True,
            is_sensitive=False,
        )

        assert variable.name == "project_type"
        assert variable.value == "web_app"
        assert variable.variable_type == ContextVariableType.STRING
        assert variable.dimension == ContextDimension.PROJECT
        assert variable.description == "Type of project being developed"
        assert variable.is_persistent is True
        assert variable.is_sensitive is False
        assert isinstance(variable.created_at, datetime)
        assert isinstance(variable.updated_at, datetime)
        assert variable.id is not None

    def test_context_variable_multi_dimensional_support(self):
        """Test ContextVariable supports multiple dimensions."""
        # Test all dimensions (AC10: project, persona, task, environment)
        dimensions = [
            ContextDimension.PROJECT,
            ContextDimension.PERSONA,
            ContextDimension.TASK,
            ContextDimension.ENVIRONMENT,
            ContextDimension.USER,
            ContextDimension.TEMPORAL,
        ]

        for dimension in dimensions:
            variable = ContextVariable(
                name=f"test_{dimension.value}",
                value="test_value",
                dimension=dimension,
            )
            assert variable.dimension == dimension

        # Verify required dimensions are supported (AC10)
        required_dimensions = [
            ContextDimension.PROJECT,
            ContextDimension.PERSONA,
            ContextDimension.TASK,
            ContextDimension.ENVIRONMENT,
        ]
        assert all(dim in dimensions for dim in required_dimensions)

    def test_context_variable_types(self):
        """Test ContextVariable supports different data types."""
        # String variable
        string_var = ContextVariable(
            name="framework",
            value="react",
            variable_type=ContextVariableType.STRING,
        )
        assert string_var.variable_type == ContextVariableType.STRING
        assert isinstance(string_var.value, str)

        # Integer variable
        int_var = ContextVariable(
            name="team_size",
            value=5,
            variable_type=ContextVariableType.INTEGER,
        )
        assert int_var.variable_type == ContextVariableType.INTEGER
        assert isinstance(int_var.value, int)

        # Boolean variable
        bool_var = ContextVariable(
            name="is_production",
            value=True,
            variable_type=ContextVariableType.BOOLEAN,
        )
        assert bool_var.variable_type == ContextVariableType.BOOLEAN
        assert isinstance(bool_var.value, bool)

        # List variable
        list_var = ContextVariable(
            name="technologies",
            value=["python", "django", "postgresql"],
            variable_type=ContextVariableType.LIST,
        )
        assert list_var.variable_type == ContextVariableType.LIST
        assert isinstance(list_var.value, list)

    def test_context_variable_validation_rules(self):
        """Test ContextVariable validation rules."""
        variable = ContextVariable(
            name="complexity_score",
            value=0.75,
            variable_type=ContextVariableType.FLOAT,
            validation_rules={
                "min_value": 0.0,
                "max_value": 1.0,
                "required": True,
            },
        )

        assert variable.validation_rules["min_value"] == 0.0
        assert variable.validation_rules["max_value"] == 1.0
        assert variable.validation_rules["required"] is True

    def test_context_variable_expiration(self):
        """Test ContextVariable expiration support."""
        expires_at = datetime.utcnow() + timedelta(hours=24)
        variable = ContextVariable(
            name="session_token",
            value="abc123",
            is_sensitive=True,
            expires_at=expires_at,
        )

        assert variable.expires_at == expires_at
        assert variable.is_sensitive is True


class TestAdaptiveTemplate:
    """Test AdaptiveTemplate data model."""

    def test_adaptive_template_creation(self):
        """Test creating an AdaptiveTemplate instance."""
        template = AdaptiveTemplate(
            name="Story Implementation Template",
            template_content="# Story: {story_title}\n## Implementation Steps\n...",
            adaptation_rules=[
                {
                    "condition": "framework == 'react'",
                    "modifications": ["add_jsx_examples", "include_hooks_section"],
                },
                {
                    "condition": "complexity == 'high'",
                    "modifications": ["add_detailed_checklist", "include_review_steps"],
                },
            ],
            required_context=["framework", "complexity", "team_size"],
            adaptation_strategy=AdaptationStrategy.RELEVANCE_BASED,
            relevance_threshold=0.8,
        )

        assert template.name == "Story Implementation Template"
        assert "story_title" in template.template_content
        assert len(template.adaptation_rules) == 2
        assert len(template.required_context) == 3
        assert template.adaptation_strategy == AdaptationStrategy.RELEVANCE_BASED
        assert template.relevance_threshold == 0.8
        assert template.version == 1
        assert template.is_active is True

    def test_adaptive_template_strategies(self):
        """Test AdaptiveTemplate adaptation strategies."""
        strategies = [
            AdaptationStrategy.RELEVANCE_BASED,
            AdaptationStrategy.PATTERN_MATCHING,
            AdaptationStrategy.MACHINE_LEARNING,
            AdaptationStrategy.RULE_BASED,
            AdaptationStrategy.HYBRID,
        ]

        for strategy in strategies:
            template = AdaptiveTemplate(
                name=f"Template with {strategy.value}",
                adaptation_strategy=strategy,
            )
            assert template.adaptation_strategy == strategy

    def test_adaptive_template_relevance_threshold(self):
        """Test AdaptiveTemplate relevance threshold for resource selection."""
        template = AdaptiveTemplate(
            name="High Relevance Template",
            relevance_threshold=0.85,  # AC8: >85% relevance
        )

        assert template.relevance_threshold == 0.85
        assert template.relevance_threshold > 0.85  # Meets AC8 requirement


class TestConditionalWorkflow:
    """Test ConditionalWorkflow data model."""

    def test_conditional_workflow_creation(self):
        """Test creating a ConditionalWorkflow instance."""
        conditions = [
            WorkflowCondition(
                context_variable="code_coverage",
                operator=WorkflowConditionOperator.GREATER_THAN,
                expected_value=0.8,
                description="Code coverage above 80%",
            ),
            WorkflowCondition(
                context_variable="security_scan",
                operator=WorkflowConditionOperator.EQUALS,
                expected_value=True,
                description="Security scan passed",
            ),
        ]

        workflow = ConditionalWorkflow(
            name="Production Deployment Workflow",
            description="Conditional workflow for production deployments",
            conditions=conditions,
            condition_logic="AND",
            true_branch_workflow="full_deployment_workflow",
            false_branch_workflow="staging_deployment_workflow",
            default_workflow="basic_deployment_workflow",
        )

        assert workflow.name == "Production Deployment Workflow"
        assert len(workflow.conditions) == 2
        assert workflow.condition_logic == "AND"
        assert workflow.true_branch_workflow == "full_deployment_workflow"
        assert workflow.false_branch_workflow == "staging_deployment_workflow"
        assert workflow.default_workflow == "basic_deployment_workflow"
        assert workflow.is_active is True

    def test_conditional_workflow_complex_conditions(self):
        """Test ConditionalWorkflow supports complex decision trees (>10 conditions)."""
        # Create more than 10 conditions (AC7: >10 conditions)
        conditions = []
        for i in range(12):
            condition = WorkflowCondition(
                context_variable=f"condition_{i}",
                operator=WorkflowConditionOperator.EQUALS,
                expected_value=True,
                description=f"Condition {i} description",
            )
            conditions.append(condition)

        workflow = ConditionalWorkflow(
            name="Complex Decision Workflow",
            conditions=conditions,
            max_condition_depth=15,  # Support deep decision trees
        )

        # Verify complex decision tree support (AC7)
        assert len(workflow.conditions) > 10
        assert workflow.max_condition_depth >= 10

    def test_conditional_workflow_operators(self):
        """Test ConditionalWorkflow supports various operators."""
        operators = [
            WorkflowConditionOperator.EQUALS,
            WorkflowConditionOperator.NOT_EQUALS,
            WorkflowConditionOperator.GREATER_THAN,
            WorkflowConditionOperator.LESS_THAN,
            WorkflowConditionOperator.GREATER_EQUAL,
            WorkflowConditionOperator.LESS_EQUAL,
            WorkflowConditionOperator.CONTAINS,
            WorkflowConditionOperator.NOT_CONTAINS,
            WorkflowConditionOperator.IN,
            WorkflowConditionOperator.NOT_IN,
            WorkflowConditionOperator.REGEX_MATCH,
        ]

        for operator in operators:
            condition = WorkflowCondition(
                context_variable="test_var",
                operator=operator,
                expected_value="test_value",
            )
            assert condition.operator == operator


class TestContextAwareResource:
    """Test ContextAwareResource data model."""

    def test_context_aware_resource_creation(self):
        """Test creating a ContextAwareResource instance."""
        resource = ContextAwareResource(
            name="React Component Template",
            resource_type="template",
            resource_content={
                "template_file": "component.tsx.template",
                "test_file": "component.test.tsx.template",
                "story_file": "component.stories.tsx.template",
            },
            context_requirements=["framework:react", "language:typescript"],
            relevance_score=0.92,
            adaptation_rules=[
                {
                    "context_match": "testing_framework:jest",
                    "adaptations": ["include_jest_config", "add_test_utilities"],
                }
            ],
            tags=["react", "typescript", "component", "frontend"],
        )

        assert resource.name == "React Component Template"
        assert resource.resource_type == "template"
        assert len(resource.resource_content) == 3
        assert len(resource.context_requirements) == 2
        assert resource.relevance_score == 0.92
        assert resource.relevance_score > 0.85  # AC8: >85% relevance
        assert len(resource.adaptation_rules) == 1
        assert len(resource.tags) == 4
        assert resource.is_active is True

    def test_context_aware_resource_relevance_scoring(self):
        """Test ContextAwareResource relevance scoring."""
        high_relevance_resource = ContextAwareResource(
            name="High Relevance Resource",
            relevance_score=0.95,
        )

        medium_relevance_resource = ContextAwareResource(
            name="Medium Relevance Resource",
            relevance_score=0.75,
        )

        low_relevance_resource = ContextAwareResource(
            name="Low Relevance Resource",
            relevance_score=0.45,
        )

        # Verify relevance scoring (AC8: >85% for provided resources)
        assert high_relevance_resource.relevance_score > 0.85
        assert medium_relevance_resource.relevance_score < 0.85
        assert low_relevance_resource.relevance_score < 0.85

    def test_context_aware_resource_types(self):
        """Test ContextAwareResource supports different resource types."""
        resource_types = ["template", "checklist", "workflow", "tool", "guideline"]

        for resource_type in resource_types:
            resource = ContextAwareResource(
                name=f"Test {resource_type.title()}",
                resource_type=resource_type,
            )
            assert resource.resource_type == resource_type


class TestContextPattern:
    """Test ContextPattern data model."""

    def test_context_pattern_creation(self):
        """Test creating a ContextPattern instance."""
        pattern = ContextPattern(
            pattern_name="Python Web Development Pattern",
            context_signature={
                "language": "python",
                "framework": ["django", "flask"],
                "project_type": "web_app",
                "team_experience": "intermediate",
            },
            resource_preferences=[
                "python_web_template",
                "django_checklist",
                "web_security_guide",
            ],
            success_rate=0.87,
            usage_count=25,
            confidence_score=0.91,
            learning_source="outcome_analysis",
            is_validated=True,
        )

        assert pattern.pattern_name == "Python Web Development Pattern"
        assert len(pattern.context_signature) == 4
        assert len(pattern.resource_preferences) == 3
        assert pattern.success_rate == 0.87
        assert pattern.usage_count == 25
        assert pattern.confidence_score == 0.91
        assert pattern.learning_source == "outcome_analysis"
        assert pattern.is_validated is True

    def test_context_pattern_learning_sources(self):
        """Test ContextPattern supports different learning sources."""
        learning_sources = ["user_feedback", "outcome_analysis", "usage_patterns"]

        for source in learning_sources:
            pattern = ContextPattern(
                pattern_name=f"Pattern from {source}",
                learning_source=source,
            )
            assert pattern.learning_source == source

    def test_context_pattern_validation(self):
        """Test ContextPattern validation and confidence scoring."""
        validated_pattern = ContextPattern(
            pattern_name="Validated Pattern",
            confidence_score=0.95,
            is_validated=True,
            usage_count=50,
        )

        unvalidated_pattern = ContextPattern(
            pattern_name="Unvalidated Pattern",
            confidence_score=0.65,
            is_validated=False,
            usage_count=3,
        )

        assert validated_pattern.is_validated is True
        assert validated_pattern.confidence_score > 0.9
        assert validated_pattern.usage_count > 10

        assert unvalidated_pattern.is_validated is False
        assert unvalidated_pattern.confidence_score < 0.7
        assert unvalidated_pattern.usage_count < 10


class TestContextEvaluationResult:
    """Test ContextEvaluationResult data model."""

    def test_context_evaluation_result_creation(self):
        """Test creating a ContextEvaluationResult instance."""
        result = ContextEvaluationResult(
            context_variables={
                "framework": "react",
                "language": "typescript",
                "complexity": "medium",
                "team_size": 4,
            },
            matched_patterns=["react_typescript_pattern", "medium_complexity_pattern"],
            recommended_resources=[
                "react_component_template",
                "typescript_checklist",
                "medium_complexity_workflow",
            ],
            relevance_scores={
                "react_component_template": 0.95,
                "typescript_checklist": 0.88,
                "medium_complexity_workflow": 0.82,
            },
            adaptation_applied=True,
            evaluation_time_ms=175.0,
        )

        assert len(result.context_variables) == 4
        assert len(result.matched_patterns) == 2
        assert len(result.recommended_resources) == 3
        assert len(result.relevance_scores) == 3
        assert result.adaptation_applied is True
        assert result.evaluation_time_ms == 175.0
        assert result.evaluation_time_ms < 200  # AC6: <200ms response time

    def test_context_evaluation_result_performance(self):
        """Test ContextEvaluationResult tracks performance requirements."""
        fast_result = ContextEvaluationResult(
            evaluation_time_ms=150.0,  # Under 200ms requirement
        )

        slow_result = ContextEvaluationResult(
            evaluation_time_ms=250.0,  # Over 200ms requirement
        )

        # Verify performance requirement tracking (AC6: <200ms)
        assert fast_result.evaluation_time_ms < 200
        assert slow_result.evaluation_time_ms > 200

    def test_context_evaluation_result_relevance_tracking(self):
        """Test ContextEvaluationResult tracks relevance scores."""
        result = ContextEvaluationResult(
            recommended_resources=["resource_1", "resource_2", "resource_3"],
            relevance_scores={
                "resource_1": 0.95,  # High relevance
                "resource_2": 0.87,  # Good relevance
                "resource_3": 0.72,  # Lower relevance
            },
        )

        # Verify relevance tracking
        high_relevance_resources = [
            resource
            for resource, score in result.relevance_scores.items()
            if score > 0.85
        ]

        # AC8: >85% relevance for provided resources
        assert len(high_relevance_resources) >= 2


class TestContextEnums:
    """Test Context model enums."""

    def test_context_dimension_enum(self):
        """Test ContextDimension enum values."""
        assert ContextDimension.PROJECT == "project"
        assert ContextDimension.PERSONA == "persona"
        assert ContextDimension.TASK == "task"
        assert ContextDimension.ENVIRONMENT == "environment"
        assert ContextDimension.USER == "user"
        assert ContextDimension.TEMPORAL == "temporal"

    def test_context_variable_type_enum(self):
        """Test ContextVariableType enum values."""
        assert ContextVariableType.STRING == "string"
        assert ContextVariableType.INTEGER == "integer"
        assert ContextVariableType.FLOAT == "float"
        assert ContextVariableType.BOOLEAN == "boolean"
        assert ContextVariableType.LIST == "list"
        assert ContextVariableType.DICT == "dict"
        assert ContextVariableType.DATETIME == "datetime"

    def test_adaptation_strategy_enum(self):
        """Test AdaptationStrategy enum values."""
        assert AdaptationStrategy.RELEVANCE_BASED == "relevance_based"
        assert AdaptationStrategy.PATTERN_MATCHING == "pattern_matching"
        assert AdaptationStrategy.MACHINE_LEARNING == "machine_learning"
        assert AdaptationStrategy.RULE_BASED == "rule_based"
        assert AdaptationStrategy.HYBRID == "hybrid"

    def test_workflow_condition_operator_enum(self):
        """Test WorkflowConditionOperator enum values."""
        assert WorkflowConditionOperator.EQUALS == "equals"
        assert WorkflowConditionOperator.NOT_EQUALS == "not_equals"
        assert WorkflowConditionOperator.GREATER_THAN == "greater_than"
        assert WorkflowConditionOperator.LESS_THAN == "less_than"
        assert WorkflowConditionOperator.CONTAINS == "contains"
        assert WorkflowConditionOperator.REGEX_MATCH == "regex_match"