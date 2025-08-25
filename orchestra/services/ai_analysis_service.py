"""AI analysis service for Orchestra AI adaptive learning system."""

import json
import time
from typing import Any, Dict, List, Optional

from openai import AsyncOpenAI

from orchestra.models.learning import LearningPattern, OutcomeEvent
from orchestra.utils.circuit_breaker import CircuitBreaker
from orchestra.utils.logging import get_logger

logger = get_logger(__name__)


class AIAnalysisService:
    """
    Service for AI-assisted pattern analysis using OpenAI.

    Provides sophisticated pattern recognition and improvement suggestions
    for persona learning and adaptation with circuit breaker protection.
    """

    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        model: str = "gpt-4",
        max_tokens: int = 2048,
        temperature: float = 0.3,
    ):
        """
        Initialize the AI analysis service.

        Args:
            openai_api_key: OpenAI API key (if None, uses environment variable)
            model: OpenAI model to use for analysis
            max_tokens: Maximum tokens for responses
            temperature: Temperature for response generation
        """
        self.client = AsyncOpenAI(api_key=openai_api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

        # Circuit breaker for OpenAI operations
        from orchestra.utils.circuit_breaker import CircuitBreakerConfig

        config = CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=60.0,
        )
        self.circuit_breaker = CircuitBreaker("ai_analysis_openai", config)

        # Track API usage for cost monitoring
        self._api_usage = {
            "total_requests": 0,
            "total_tokens": 0,
            "failed_requests": 0,
        }

    async def analyze_outcome_patterns(
        self,
        outcome_events: List[OutcomeEvent],
        analysis_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze outcome events to identify patterns and improvement opportunities.

        Args:
            outcome_events: List of outcome events to analyze
            analysis_context: Additional context for analysis

        Returns:
            Analysis result with identified patterns and recommendations
        """
        logger.info(
            "Starting AI pattern analysis",
            outcome_count=len(outcome_events),
            context_provided=bool(analysis_context),
        )

        try:
            # Convert outcome events to analysis format
            analysis_data = [event.to_analysis_data() for event in outcome_events]

            # Create analysis prompt
            analysis_prompt = self._create_pattern_analysis_prompt(
                analysis_data, analysis_context
            )

            # Execute AI analysis with circuit breaker
            analysis_result = await self.circuit_breaker.call(
                self._execute_ai_analysis, analysis_prompt
            )

            # Parse and validate results
            parsed_result = self._parse_analysis_result(analysis_result)

            # Validate accuracy requirement (AC: 7 - >85% accuracy)
            if parsed_result.get("confidence_score", 0.0) < 0.85:
                logger.warning(
                    "AI analysis confidence below 85% threshold",
                    confidence=parsed_result.get("confidence_score"),
                )

            # Update usage tracking
            self._api_usage["total_requests"] += 1
            self._api_usage["total_tokens"] += analysis_result.get("tokens_used", 0)

            logger.info(
                "AI pattern analysis completed",
                patterns_identified=len(parsed_result.get("patterns", [])),
                confidence_score=parsed_result.get("confidence_score"),
            )

            return parsed_result

        except Exception as e:
            logger.error("AI pattern analysis failed", error=str(e))
            self._api_usage["failed_requests"] += 1
            return {
                "success": False,
                "error": str(e),
                "patterns": [],
                "recommendations": [],
                "confidence_score": 0.0,
            }

    async def generate_improvement_recommendations(
        self,
        persona_id: str,
        current_patterns: List[LearningPattern],
        performance_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate AI-assisted improvement recommendations for persona behavior.

        Args:
            persona_id: ID of persona to generate recommendations for
            current_patterns: Current learning patterns for the persona
            performance_data: Performance metrics and trends

        Returns:
            Improvement recommendations with confidence scores
        """
        logger.info(
            "Generating AI improvement recommendations",
            persona_id=persona_id,
            patterns_count=len(current_patterns),
        )

        try:
            # Create improvement prompt
            improvement_prompt = self._create_improvement_prompt(
                persona_id, current_patterns, performance_data
            )

            # Execute AI recommendation generation
            recommendation_result = await self.circuit_breaker.call(
                self._execute_ai_analysis, improvement_prompt
            )

            # Parse recommendations
            parsed_recommendations = self._parse_recommendation_result(
                recommendation_result
            )

            # Validate improvement rate requirement (AC: 8 - >70% improvement rate)
            expected_improvement = parsed_recommendations.get(
                "expected_improvement_rate", 0.0
            )
            if expected_improvement < 0.7:
                logger.warning(
                    "AI recommendations below 70% improvement threshold",
                    expected_improvement=expected_improvement,
                )

            # Update usage tracking
            self._api_usage["total_requests"] += 1
            self._api_usage["total_tokens"] += recommendation_result.get(
                "tokens_used", 0
            )

            logger.info(
                "AI improvement recommendations completed",
                recommendations_count=len(
                    parsed_recommendations.get("recommendations", [])
                ),
                expected_improvement=expected_improvement,
            )

            return parsed_recommendations

        except Exception as e:
            logger.error("AI recommendation generation failed", error=str(e))
            self._api_usage["failed_requests"] += 1
            return {
                "success": False,
                "error": str(e),
                "recommendations": [],
                "expected_improvement_rate": 0.0,
                "confidence_score": 0.0,
            }

    async def validate_pattern_transferability(
        self,
        source_pattern: LearningPattern,
        target_persona_id: str,
        context_similarity: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Validate if a learning pattern can be transferred to another persona.

        Args:
            source_pattern: Pattern to evaluate for transfer
            target_persona_id: Target persona ID
            context_similarity: Context similarity data

        Returns:
            Transferability assessment with confidence scores
        """
        logger.info(
            "Validating pattern transferability",
            pattern_id=source_pattern.pattern_id,
            source_persona=source_pattern.persona_id,
            target_persona=target_persona_id,
        )

        try:
            # Create transferability prompt
            transferability_prompt = self._create_transferability_prompt(
                source_pattern, target_persona_id, context_similarity
            )

            # Execute AI transferability analysis
            transferability_result = await self.circuit_breaker.call(
                self._execute_ai_analysis, transferability_prompt
            )

            # Parse transferability result
            parsed_result = self._parse_transferability_result(transferability_result)

            # Update usage tracking
            self._api_usage["total_requests"] += 1
            self._api_usage["total_tokens"] += transferability_result.get(
                "tokens_used", 0
            )

            logger.info(
                "Pattern transferability validation completed",
                transferable=parsed_result.get("transferable", False),
                transferability_score=parsed_result.get("transferability_score", 0.0),
            )

            return parsed_result

        except Exception as e:
            logger.error("Pattern transferability validation failed", error=str(e))
            self._api_usage["failed_requests"] += 1
            return {
                "success": False,
                "error": str(e),
                "transferable": False,
                "transferability_score": 0.0,
                "adaptation_requirements": [],
            }

    def get_api_usage_statistics(self) -> Dict[str, Any]:
        """Get API usage statistics for monitoring and cost tracking."""
        return {
            "total_requests": self._api_usage["total_requests"],
            "total_tokens": self._api_usage["total_tokens"],
            "failed_requests": self._api_usage["failed_requests"],
            "success_rate": (
                (self._api_usage["total_requests"] - self._api_usage["failed_requests"])
                / max(1, self._api_usage["total_requests"])
            ),
            "circuit_breaker_state": self.circuit_breaker.state.name,
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on AI analysis service."""
        try:
            # Simple health check query
            test_prompt = "Respond with 'healthy' if you can process this request."

            start_time = time.time()
            response = await self.circuit_breaker.call(
                self._execute_simple_query, test_prompt
            )
            response_time_ms = (time.time() - start_time) * 1000

            is_healthy = "healthy" in response.get("response", "").lower()

            return {
                "status": "healthy" if is_healthy else "unhealthy",
                "response_time_ms": response_time_ms,
                "circuit_breaker_state": self.circuit_breaker.state.name,
                "api_usage": self.get_api_usage_statistics(),
            }

        except Exception as e:
            logger.error("AI analysis service health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e),
                "circuit_breaker_state": self.circuit_breaker.state.name,
            }

    # Private methods

    async def _execute_ai_analysis(self, prompt: str) -> Dict[str, Any]:
        """Execute AI analysis with OpenAI API."""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an AI assistant specialized in analyzing software development patterns and providing improvement recommendations. Always respond in valid JSON format.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else 0

            return {
                "response": content,
                "tokens_used": tokens_used,
                "model": self.model,
                "request_id": response.id if hasattr(response, "id") else None,
            }

        except Exception as e:
            logger.error("OpenAI API call failed", error=str(e))
            raise

    async def _execute_simple_query(self, prompt: str) -> Dict[str, Any]:
        """Execute simple query for health checks."""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.1,
            )

            return {
                "response": response.choices[0].message.content,
                "tokens_used": response.usage.total_tokens if response.usage else 0,
            }

        except Exception as e:
            logger.error("Simple OpenAI query failed", error=str(e))
            raise

    def _create_pattern_analysis_prompt(
        self,
        analysis_data: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create prompt for pattern analysis."""
        prompt = """
Analyze the following software development outcome events to identify patterns and improvement opportunities.

Outcome Events:
{}

{}

Please provide analysis in JSON format with:
1. "patterns": Array of identified patterns with type, description, confidence
2. "recommendations": Array of improvement recommendations
3. "confidence_score": Overall confidence in analysis (0.0-1.0)
4. "success_indicators": Key success factors identified
5. "failure_indicators": Key failure factors identified
6. "improvement_opportunities": Specific areas for improvement

Ensure patterns have >85% accuracy confidence score and recommendations target >70% improvement rate.
        """.strip()

        events_json = json.dumps(analysis_data, indent=2, default=str)
        context_str = (
            f"Additional Context:\n{json.dumps(context, indent=2, default=str)}\n"
            if context
            else ""
        )

        return prompt.format(events_json, context_str)

    def _create_improvement_prompt(
        self,
        persona_id: str,
        current_patterns: List[LearningPattern],
        performance_data: Dict[str, Any],
    ) -> str:
        """Create prompt for improvement recommendations."""
        patterns_data = [
            {
                "pattern_id": pattern.pattern_id,
                "type": pattern.pattern_type,
                "description": pattern.description,
                "effectiveness_score": pattern.effectiveness_score,
                "usage_count": pattern.usage_count,
            }
            for pattern in current_patterns
        ]

        prompt = """
Generate improvement recommendations for persona "{}".

Current Learning Patterns:
{}

Performance Data:
{}

Provide recommendations in JSON format with:
1. "recommendations": Array of behavior modifications with type, description, expected_improvement
2. "expected_improvement_rate": Overall expected improvement percentage (target >70%)
3. "confidence_score": Confidence in recommendations (0.0-1.0)
4. "priority_actions": Top 3 priority improvements
5. "risk_assessment": Potential risks and mitigation strategies
6. "implementation_plan": Step-by-step implementation guidance

Focus on actionable recommendations that maintain system performance within 500ms load time constraint.
        """.strip()

        return prompt.format(
            persona_id,
            json.dumps(patterns_data, indent=2, default=str),
            json.dumps(performance_data, indent=2, default=str),
        )

    def _create_transferability_prompt(
        self,
        source_pattern: LearningPattern,
        target_persona_id: str,
        context_similarity: Dict[str, Any],
    ) -> str:
        """Create prompt for transferability analysis."""
        pattern_data = {
            "pattern_id": source_pattern.pattern_id,
            "source_persona": source_pattern.persona_id,
            "type": source_pattern.pattern_type,
            "description": source_pattern.description,
            "effectiveness_score": source_pattern.effectiveness_score,
            "pattern_data": source_pattern.pattern_data,
        }

        prompt = """
Analyze if the following learning pattern can be transferred from "{}" to "{}".

Source Pattern:
{}

Context Similarity Data:
{}

Provide analysis in JSON format with:
1. "transferable": Boolean indicating if pattern can be transferred
2. "transferability_score": Score from 0.0 to 1.0 (target >75%)
3. "adaptation_requirements": List of required adaptations
4. "risk_factors": Potential risks in transfer
5. "success_probability": Estimated success probability
6. "implementation_strategy": How to implement the transfer

Consider persona role differences, domain compatibility, and potential adaptation needs.
        """.strip()

        return prompt.format(
            source_pattern.persona_id,
            target_persona_id,
            json.dumps(pattern_data, indent=2, default=str),
            json.dumps(context_similarity, indent=2, default=str),
        )

    def _parse_analysis_result(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and validate analysis result from OpenAI."""
        try:
            response_content = analysis_result.get("response", "{}")
            parsed_data = json.loads(response_content)

            # Validate required fields
            patterns = parsed_data.get("patterns", [])
            recommendations = parsed_data.get("recommendations", [])
            confidence_score = parsed_data.get("confidence_score", 0.0)

            return {
                "success": True,
                "patterns": patterns,
                "recommendations": recommendations,
                "confidence_score": confidence_score,
                "success_indicators": parsed_data.get("success_indicators", []),
                "failure_indicators": parsed_data.get("failure_indicators", []),
                "improvement_opportunities": parsed_data.get(
                    "improvement_opportunities", []
                ),
                "ai_metadata": {
                    "model": analysis_result.get("model"),
                    "tokens_used": analysis_result.get("tokens_used"),
                    "request_id": analysis_result.get("request_id"),
                },
            }

        except json.JSONDecodeError as e:
            logger.error("Failed to parse AI analysis result", error=str(e))
            return {
                "success": False,
                "error": f"JSON parsing failed: {str(e)}",
                "patterns": [],
                "recommendations": [],
                "confidence_score": 0.0,
            }

    def _parse_recommendation_result(
        self, recommendation_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse and validate recommendation result from OpenAI."""
        try:
            response_content = recommendation_result.get("response", "{}")
            parsed_data = json.loads(response_content)

            return {
                "success": True,
                "recommendations": parsed_data.get("recommendations", []),
                "expected_improvement_rate": parsed_data.get(
                    "expected_improvement_rate", 0.0
                ),
                "confidence_score": parsed_data.get("confidence_score", 0.0),
                "priority_actions": parsed_data.get("priority_actions", []),
                "risk_assessment": parsed_data.get("risk_assessment", {}),
                "implementation_plan": parsed_data.get("implementation_plan", []),
                "ai_metadata": {
                    "model": recommendation_result.get("model"),
                    "tokens_used": recommendation_result.get("tokens_used"),
                    "request_id": recommendation_result.get("request_id"),
                },
            }

        except json.JSONDecodeError as e:
            logger.error("Failed to parse AI recommendation result", error=str(e))
            return {
                "success": False,
                "error": f"JSON parsing failed: {str(e)}",
                "recommendations": [],
                "expected_improvement_rate": 0.0,
                "confidence_score": 0.0,
            }

    def _parse_transferability_result(
        self, transferability_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse and validate transferability result from OpenAI."""
        try:
            response_content = transferability_result.get("response", "{}")
            parsed_data = json.loads(response_content)

            return {
                "success": True,
                "transferable": parsed_data.get("transferable", False),
                "transferability_score": parsed_data.get("transferability_score", 0.0),
                "adaptation_requirements": parsed_data.get(
                    "adaptation_requirements", []
                ),
                "risk_factors": parsed_data.get("risk_factors", []),
                "success_probability": parsed_data.get("success_probability", 0.0),
                "implementation_strategy": parsed_data.get(
                    "implementation_strategy", []
                ),
                "ai_metadata": {
                    "model": transferability_result.get("model"),
                    "tokens_used": transferability_result.get("tokens_used"),
                    "request_id": transferability_result.get("request_id"),
                },
            }

        except json.JSONDecodeError as e:
            logger.error("Failed to parse AI transferability result", error=str(e))
            return {
                "success": False,
                "error": f"JSON parsing failed: {str(e)}",
                "transferable": False,
                "transferability_score": 0.0,
                "adaptation_requirements": [],
            }
