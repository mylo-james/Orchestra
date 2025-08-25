"""Tests for AI Analysis Service for Epic 2 Story 2.2 adaptive learning."""

from unittest.mock import patch

import pytest

from orchestra.services.ai_analysis_service import AIAnalysisService


class TestAIAnalysisService:
    """Test AI analysis service with OpenAI integration."""

    @pytest.fixture
    def sample_outcome_events(self):
        """Sample outcome events for testing."""
        from datetime import datetime

        from orchestra.models.learning import OutcomeEvent

        return [
            OutcomeEvent(
                outcome_id="outcome-1",
                persona_id="dev",
                project_id="test-project",
                session_id="session-123",
                command="implement-story",
                result={
                    "success": True,
                    "execution_time": 45,
                    "quality_score": 0.92,
                },
                classification="success",
                confidence_score=0.92,
                timestamp=datetime.utcnow(),
                duration_seconds=45.0,
            )
        ]

    @pytest.mark.asyncio
    async def test_service_initialization(self):
        """Test service initialization with API key."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            service = AIAnalysisService(openai_api_key="custom-key")

            assert service.client is not None
            assert service.model == "gpt-4"
            assert service.circuit_breaker is not None
            assert service.circuit_breaker.name == "ai_analysis_openai"

    @pytest.mark.asyncio
    async def test_analyze_outcome_patterns_success(self, sample_outcome_events):
        """Test successful outcome pattern analysis."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            with patch.object(
                AIAnalysisService, "_execute_ai_analysis"
            ) as mock_execute:
                mock_execute.return_value = {
                    "patterns": [{"pattern_id": "p1", "confidence": 0.87}],
                    "confidence_score": 0.85,
                }

                service = AIAnalysisService()
                result = await service.analyze_outcome_patterns(
                    outcome_events=sample_outcome_events,
                    analysis_context={"project_id": "test-project"},
                )

                assert isinstance(result, dict)
                assert "patterns" in result
                mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_improvement_recommendations(self):
        """Test improvement recommendations generation."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            with patch.object(
                AIAnalysisService, "_execute_ai_analysis"
            ) as mock_execute:
                mock_execute.return_value = {
                    "recommendations": [{"rec_id": "r1", "confidence": 0.78}]
                }

                service = AIAnalysisService()

                result = await service.generate_improvement_recommendations(
                    persona_id="dev",
                    current_patterns=[],  # Pass empty list for patterns
                    performance_data={"accuracy": 0.8},
                )

                assert isinstance(result, dict)
                assert "recommendations" in result
                mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_pattern_transferability(self):
        """Test pattern transferability validation."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            with patch.object(
                AIAnalysisService, "_execute_ai_analysis"
            ) as mock_execute:
                mock_execute.return_value = {
                    "transferability_score": 0.82,
                    "confidence": 0.85,
                }

                service = AIAnalysisService()

                from datetime import datetime

                from orchestra.models.learning import LearningPattern

                mock_pattern = LearningPattern(
                    pattern_id="p1",
                    project_id="test-project",
                    persona_id="dev",
                    pattern_type="test",
                    description="test pattern",
                    pattern_data={"test": "data"},
                    confidence_score=0.85,
                    effectiveness_score=0.82,
                    accuracy_score=0.88,
                    usage_count=5,
                    last_applied=datetime.utcnow(),
                    created_at=datetime.utcnow(),
                )

                result = await service.validate_pattern_transferability(
                    source_pattern=mock_pattern,
                    target_persona_id="qa",
                    context_similarity={"similarity_score": 0.7},
                )

                assert isinstance(result, dict)
                assert "transferability_score" in result
                mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test service health check."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            service = AIAnalysisService()

            health_status = await service.health_check()

            assert isinstance(health_status, dict)
            assert "circuit_breaker_state" in health_status
            assert health_status["status"] in ["healthy", "unhealthy"]
            # For unhealthy status (invalid API key), check for error field
            if health_status["status"] == "unhealthy":
                assert "error" in health_status

    @pytest.mark.asyncio
    async def test_get_api_usage_statistics(self):
        """Test API usage statistics retrieval."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            service = AIAnalysisService()

            stats = service.get_api_usage_statistics()

            assert isinstance(stats, dict)
            assert "total_requests" in stats
            assert "failed_requests" in stats
            assert "success_rate" in stats
            assert "circuit_breaker_state" in stats
            # Check for numeric types
            assert isinstance(stats["total_requests"], int)
            assert isinstance(stats["failed_requests"], int)
            assert isinstance(stats["success_rate"], float)

    @pytest.mark.asyncio
    async def test_circuit_breaker_functionality(self):
        """Test circuit breaker functionality."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            service = AIAnalysisService()

            # Test circuit breaker stats
            stats = service.circuit_breaker.get_stats()
            assert isinstance(stats, dict)

            # Test circuit breaker name
            assert service.circuit_breaker.name == "ai_analysis_openai"

    @pytest.mark.asyncio
    async def test_error_handling(self, sample_outcome_events):
        """Test error handling in AI analysis."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            with patch.object(
                AIAnalysisService, "_execute_ai_analysis"
            ) as mock_execute:
                mock_execute.side_effect = Exception("AI Service Error")

                service = AIAnalysisService()

                result = await service.analyze_outcome_patterns(
                    outcome_events=sample_outcome_events, analysis_context={}
                )

                # Service should return error result instead of raising
                assert result["success"] is False
                assert "error" in result

    @pytest.mark.asyncio
    async def test_prompt_creation_methods(self):
        """Test internal prompt creation methods."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            service = AIAnalysisService()

            # Test pattern analysis prompt creation
            events = [{"persona_id": "dev", "result": {"success": True}}]
            context = {"project_id": "test"}

            prompt = service._create_pattern_analysis_prompt(events, context)
            assert isinstance(prompt, str)
            assert len(prompt) > 0

            from datetime import datetime

            from orchestra.models.learning import LearningPattern

            patterns = [
                LearningPattern(
                    pattern_id="p1",
                    project_id="test-project",
                    persona_id="dev",
                    pattern_type="test",
                    description="test pattern",
                    pattern_data={"test": "data"},
                    confidence_score=0.85,
                    effectiveness_score=0.82,
                    accuracy_score=0.88,
                    usage_count=5,
                    last_applied=datetime.utcnow(),
                    created_at=datetime.utcnow(),
                )
            ]

            improvement_prompt = service._create_improvement_prompt(
                persona_id="dev",
                current_patterns=patterns,
                performance_data={"accuracy": 0.85},
            )
            assert isinstance(improvement_prompt, str)
            assert len(improvement_prompt) > 0

            # Test transferability prompt creation
            from datetime import datetime

            transfer_pattern = LearningPattern(
                pattern_id="p1",
                project_id="test-project",
                persona_id="dev",
                pattern_type="test",
                description="test pattern for transferability",
                pattern_data={"test": "data"},
                confidence_score=0.85,
                effectiveness_score=0.82,
                accuracy_score=0.88,
                usage_count=5,
                last_applied=datetime.utcnow(),
                created_at=datetime.utcnow(),
            )
            target_context = {"persona_type": "qa"}
            criteria = {"min_confidence": 0.75}

            transfer_prompt = service._create_transferability_prompt(
                transfer_pattern, target_context, criteria
            )
            assert isinstance(transfer_prompt, str)
            assert len(transfer_prompt) > 0

    @pytest.mark.asyncio
    async def test_result_parsing_methods(self):
        """Test internal result parsing methods."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            service = AIAnalysisService()

            # Test pattern analysis result parsing
            analysis_result = {
                "patterns": [{"pattern_id": "p1", "confidence": 0.85}],
                "confidence_score": 0.8,
            }

            parsed = service._parse_analysis_result(analysis_result)
            assert isinstance(parsed, dict)

            # Test recommendation result parsing
            recommendation_result = {
                "recommendations": [{"rec_id": "r1", "confidence": 0.78}]
            }

            parsed_rec = service._parse_recommendation_result(recommendation_result)
            assert isinstance(parsed_rec, dict)

            # Test transferability result parsing
            transfer_result = {"transferability_score": 0.82, "confidence": 0.85}

            parsed_transfer = service._parse_transferability_result(transfer_result)
            assert isinstance(parsed_transfer, dict)


class TestAIAnalysisServiceIntegration:
    """Integration tests for AI Analysis Service."""

    @pytest.mark.asyncio
    async def test_full_analysis_pipeline(self):
        """Test complete analysis pipeline."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            with patch.object(
                AIAnalysisService, "_execute_ai_analysis"
            ) as mock_execute:
                # Mock responses for different stages
                mock_execute.side_effect = [
                    {
                        "patterns": [{"pattern_id": "p1", "confidence": 0.89}],
                        "confidence_score": 0.89,
                    },
                    {"recommendations": [{"rec_id": "r1", "confidence": 0.85}]},
                    {"transferability_score": 0.82, "confidence": 0.85},
                ]

                service = AIAnalysisService()

                from datetime import datetime

                from orchestra.models.learning import OutcomeEvent

                events = [
                    OutcomeEvent(
                        outcome_id="outcome-1",
                        persona_id="dev",
                        project_id="test-project",
                        session_id="session-123",
                        command="implement-story",
                        result={"success": True},
                        classification="success",
                        confidence_score=0.92,
                        timestamp=datetime.utcnow(),
                        duration_seconds=45.0,
                    )
                ]

                # Step 1: Analyze patterns
                analysis_result = await service.analyze_outcome_patterns(
                    outcome_events=events, analysis_context={"project_id": "test"}
                )

                # Step 2: Generate recommendations
                recommendations = await service.generate_improvement_recommendations(
                    persona_id="dev",
                    current_patterns=[],  # Pass empty patterns for mock
                    performance_data={"accuracy": 0.85},
                )

                # Step 3: Validate transferability (skip for mock test due to complexity)
                from datetime import datetime

                from orchestra.models.learning import LearningPattern

                mock_pattern = LearningPattern(
                    pattern_id="p1",
                    project_id="test-project",
                    persona_id="dev",
                    pattern_type="test",
                    description="test pattern",
                    pattern_data={"test": "data"},
                    confidence_score=0.85,
                    effectiveness_score=0.82,
                    accuracy_score=0.88,
                    usage_count=5,
                    last_applied=datetime.utcnow(),
                    created_at=datetime.utcnow(),
                )
                transferability = await service.validate_pattern_transferability(
                    source_pattern=mock_pattern,
                    target_persona_id="qa",
                    context_similarity={"similarity_score": 0.7},
                )

                # Verify full pipeline completed (mocked service returns different values)
                assert "confidence_score" in analysis_result
                assert "recommendations" in recommendations
                assert "transferability_score" in transferability

                # Verify all stages were called
                assert mock_execute.call_count == 3

    @pytest.mark.asyncio
    async def test_circuit_breaker_integration(self):
        """Test circuit breaker integration with API failures."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            with patch.object(
                AIAnalysisService, "_execute_ai_analysis"
            ) as mock_execute:
                mock_execute.side_effect = Exception("API Error")

                service = AIAnalysisService()

                # Multiple failures should engage circuit breaker
                error_results = []
                from datetime import datetime

                from orchestra.models.learning import OutcomeEvent

                test_event = OutcomeEvent(
                    outcome_id="test-1",
                    persona_id="test",
                    project_id="test-project",
                    session_id="session-123",
                    command="test",
                    result={"test": "data"},
                    classification="success",
                    confidence_score=0.5,
                    timestamp=datetime.utcnow(),
                    duration_seconds=1.0,
                )
                for _ in range(3):
                    result = await service.analyze_outcome_patterns(
                        outcome_events=[test_event], analysis_context={}
                    )
                    error_results.append(result)
                    # Service should return error result instead of raising
                    assert result["success"] is False
                    assert "error" in result

                # Circuit breaker should have recorded failures
                stats = service.circuit_breaker.get_stats()
                assert stats["stats"]["total_requests"] >= 3
