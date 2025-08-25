"""Pattern matching service for Orchestra AI cross-persona knowledge sharing."""

import time
from typing import Any, Dict, List, Optional

from orchestra.models.shared_knowledge import PatternMapping, SharedKnowledge
from orchestra.services.ai_analysis_service import AIAnalysisService
from orchestra.services.memory_service import MemoryService
from orchestra.utils.circuit_breaker import CircuitBreaker
from orchestra.utils.logging import get_logger

logger = get_logger(__name__)


class PatternMatchingService:
    """
    Service for AI-assisted pattern matching across personas.

    Identifies transferable knowledge between persona types using
    AI analysis with transferability scoring and context mapping.
    """

    def __init__(
        self,
        ai_analysis_service: Optional[AIAnalysisService] = None,
        memory_service: Optional[MemoryService] = None,
        similarity_threshold: float = 0.75,
        transferability_threshold: float = 0.75,
    ):
        """
        Initialize pattern matching service.

        Args:
            ai_analysis_service: AI analysis service for pattern comparison
            memory_service: Memory service for pattern storage and retrieval
            similarity_threshold: Minimum similarity score for pattern matching
            transferability_threshold: Minimum transferability score (AC: 7 - >75%)
        """
        self.ai_service = ai_analysis_service or AIAnalysisService()
        self.memory_service = memory_service or MemoryService()
        self.similarity_threshold = similarity_threshold
        self.transferability_threshold = transferability_threshold

        # Circuit breaker for AI operations
        from orchestra.utils.circuit_breaker import CircuitBreakerConfig

        config = CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=60.0,
        )
        self.circuit_breaker = CircuitBreaker("pattern_matching_ai", config)

        # Performance metrics
        self._performance_metrics = {
            "total_matches": 0,
            "successful_transfers": 0,
            "failed_transfers": 0,
            "average_similarity_score": 0.0,
            "average_transferability_score": 0.0,
        }

    async def find_transferable_patterns(
        self,
        source_persona_id: str,
        target_persona_id: str,
        project_id: str,
        context_similarity: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Find patterns that can be transferred between personas.

        Args:
            source_persona_id: Source persona ID
            target_persona_id: Target persona ID
            project_id: Project ID for context
            context_similarity: Context similarity data

        Returns:
            Transferable patterns with mapping and confidence scores
        """
        logger.info(
            "Finding transferable patterns",
            source_persona=source_persona_id,
            target_persona=target_persona_id,
            project_id=project_id,
        )

        try:
            start_time = time.time()

            # Step 1: Get source patterns from memory
            source_patterns = await self._get_persona_patterns(
                source_persona_id, project_id
            )

            if not source_patterns:
                return {
                    "success": True,
                    "transferable_patterns": [],
                    "pattern_mappings": [],
                    "message": "No source patterns found",
                }

            # Step 2: Analyze pattern compatibility (AC: 2 - pattern matching with AI analysis)
            compatibility_results = []

            for pattern in source_patterns:
                try:
                    compatibility_result = await self.circuit_breaker.call(
                        self._analyze_pattern_compatibility,
                        pattern,
                        target_persona_id,
                        context_similarity or {},
                    )

                    if compatibility_result.get("success"):
                        compatibility_results.append(compatibility_result)

                except Exception as e:
                    logger.warning(
                        "Pattern compatibility analysis failed",
                        error=str(e),
                        pattern_id=pattern.get("pattern_id"),
                    )
                    continue

            # Step 3: Filter by transferability threshold (AC: 7 - >75% accuracy)
            transferable_patterns = []
            pattern_mappings = []

            for result in compatibility_results:
                transferability_score = result.get("transferability_score", 0.0)

                if transferability_score >= self.transferability_threshold:
                    transferable_patterns.append(result["pattern"])

                    # Create pattern mapping
                    pattern_mapping = await self._create_pattern_mapping(
                        result, source_persona_id, target_persona_id, project_id
                    )
                    pattern_mappings.append(pattern_mapping)

            # Update performance metrics
            self._update_performance_metrics(compatibility_results)

            processing_time_ms = (time.time() - start_time) * 1000

            result = {
                "success": True,
                "transferable_patterns": transferable_patterns,
                "pattern_mappings": [mapping.__dict__ for mapping in pattern_mappings],
                "total_patterns_analyzed": len(source_patterns),
                "transferable_count": len(transferable_patterns),
                "processing_time_ms": processing_time_ms,
                "performance_metrics": self._performance_metrics.copy(),
            }

            logger.info(
                "Pattern matching completed",
                transferable_count=len(transferable_patterns),
                total_analyzed=len(source_patterns),
                processing_time_ms=processing_time_ms,
            )

            return result

        except Exception as e:
            logger.error(
                "Pattern matching failed",
                error=str(e),
                source_persona=source_persona_id,
                target_persona=target_persona_id,
            )
            return {
                "success": False,
                "error": str(e),
                "transferable_patterns": [],
                "pattern_mappings": [],
            }

    async def assess_cross_persona_similarity(
        self,
        pattern_a: Dict[str, Any],
        pattern_b: Dict[str, Any],
        context_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Assess similarity between patterns from different personas.

        Args:
            pattern_a: First pattern for comparison
            pattern_b: Second pattern for comparison
            context_data: Additional context for comparison

        Returns:
            Similarity assessment with scores and analysis
        """
        logger.info(
            "Assessing cross-persona similarity",
            pattern_a_id=pattern_a.get("pattern_id"),
            pattern_b_id=pattern_b.get("pattern_id"),
        )

        try:
            # Use AI analysis for sophisticated pattern comparison
            similarity_result = await self.circuit_breaker.call(
                self._ai_similarity_analysis,
                pattern_a,
                pattern_b,
                context_data or {},
            )

            # Validate similarity score threshold
            similarity_score = similarity_result.get("similarity_score", 0.0)
            meets_threshold = similarity_score >= self.similarity_threshold

            return {
                "success": True,
                "similarity_score": similarity_score,
                "meets_threshold": meets_threshold,
                "similarity_analysis": similarity_result.get("analysis", {}),
                "context_alignment": similarity_result.get("context_alignment", {}),
                "transferability_assessment": similarity_result.get(
                    "transferability", {}
                ),
            }

        except Exception as e:
            logger.error(
                "Similarity assessment failed",
                error=str(e),
                pattern_a_id=pattern_a.get("pattern_id"),
                pattern_b_id=pattern_b.get("pattern_id"),
            )
            return {
                "success": False,
                "error": str(e),
                "similarity_score": 0.0,
                "meets_threshold": False,
            }

    async def generate_adaptation_strategy(
        self,
        pattern_mapping: PatternMapping,
        target_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate adaptation strategy for pattern transfer.

        Args:
            pattern_mapping: Pattern mapping with transferability data
            target_context: Target persona context

        Returns:
            Adaptation strategy with implementation steps
        """
        logger.info(
            "Generating adaptation strategy",
            mapping_id=pattern_mapping.mapping_id,
            target_persona=pattern_mapping.target_persona_id,
        )

        try:
            # Determine adaptation complexity based on transferability score
            base_strategy = pattern_mapping.get_adaptation_strategy()

            # Use AI for detailed adaptation planning
            ai_strategy = await self.circuit_breaker.call(
                self._ai_adaptation_planning,
                pattern_mapping,
                target_context,
                base_strategy,
            )

            adaptation_steps = []

            # Generate step-by-step adaptation plan
            if base_strategy["strategy"] == "direct_transfer":
                adaptation_steps = [
                    {
                        "step": "validate_context",
                        "description": "Validate target context compatibility",
                        "effort": "minimal",
                        "risk": "low",
                    },
                    {
                        "step": "apply_pattern",
                        "description": "Apply pattern with minimal modifications",
                        "effort": "low",
                        "risk": "low",
                    },
                ]
            elif base_strategy["strategy"] == "minor_adaptation":
                adaptation_steps = [
                    {
                        "step": "analyze_differences",
                        "description": "Analyze context differences between personas",
                        "effort": "moderate",
                        "risk": "low",
                    },
                    {
                        "step": "adapt_parameters",
                        "description": "Adapt pattern parameters for target context",
                        "effort": "moderate",
                        "risk": "medium",
                    },
                    {
                        "step": "test_adaptation",
                        "description": "Test adapted pattern in target environment",
                        "effort": "moderate",
                        "risk": "medium",
                    },
                ]
            else:  # significant_adaptation
                adaptation_steps = [
                    {
                        "step": "deep_analysis",
                        "description": "Deep analysis of pattern applicability",
                        "effort": "high",
                        "risk": "high",
                    },
                    {
                        "step": "redesign_pattern",
                        "description": "Significant redesign for target persona",
                        "effort": "high",
                        "risk": "high",
                    },
                    {
                        "step": "validation_testing",
                        "description": "Extensive validation and testing",
                        "effort": "high",
                        "risk": "medium",
                    },
                ]

            # Enhance with AI-generated insights
            if ai_strategy.get("success"):
                ai_insights = ai_strategy.get("insights", {})
                for step in adaptation_steps:
                    step_insights = ai_insights.get(step["step"], {})
                    if step_insights:
                        step["ai_recommendations"] = step_insights

            return {
                "success": True,
                "adaptation_strategy": base_strategy["strategy"],
                "adaptation_required": base_strategy["adaptation_required"],
                "adaptation_steps": adaptation_steps,
                "estimated_effort": ai_strategy.get("estimated_effort", "unknown"),
                "success_probability": ai_strategy.get("success_probability", 0.5),
                "risk_factors": ai_strategy.get("risk_factors", []),
                "ai_insights": ai_strategy.get("insights", {}),
            }

        except Exception as e:
            logger.error(
                "Adaptation strategy generation failed",
                error=str(e),
                mapping_id=pattern_mapping.mapping_id,
            )
            return {
                "success": False,
                "error": str(e),
                "adaptation_strategy": "unknown",
                "adaptation_steps": [],
            }

    async def validate_pattern_effectiveness(
        self,
        shared_knowledge: SharedKnowledge,
        target_persona_results: Dict[str, Any],
        baseline_metrics: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Validate effectiveness of shared pattern in target persona.

        Args:
            shared_knowledge: Shared knowledge pattern
            target_persona_results: Results from target persona execution
            baseline_metrics: Baseline performance metrics

        Returns:
            Effectiveness validation with improvement metrics
        """
        logger.info(
            "Validating pattern effectiveness",
            knowledge_id=shared_knowledge.knowledge_id,
            target_persona=target_persona_results.get("persona_id"),
        )

        try:
            # Calculate effectiveness metrics (AC: 8 - >60% effectiveness improvement)
            effectiveness_analysis = await self._analyze_effectiveness(
                target_persona_results, baseline_metrics
            )

            improvement_score = effectiveness_analysis.get("improvement_score", 0.0)
            meets_threshold = improvement_score >= 0.6  # AC: 8 - >60% effectiveness

            # Update shared knowledge usage statistics
            if meets_threshold:
                shared_knowledge.record_usage(success=True)
                validation_status = "beneficial"
            else:
                shared_knowledge.record_usage(success=False)
                validation_status = "ineffective"

            # Generate validation report
            validation_report = {
                "knowledge_id": shared_knowledge.knowledge_id,
                "target_persona": target_persona_results.get("persona_id"),
                "validation_status": validation_status,
                "improvement_score": improvement_score,
                "meets_threshold": meets_threshold,
                "threshold_required": 0.6,
                "effectiveness_analysis": effectiveness_analysis,
                "usage_statistics": {
                    "total_usage_count": shared_knowledge.usage_count,
                    "success_rate": shared_knowledge.success_rate,
                    "updated_at": shared_knowledge.updated_at.isoformat(),
                },
            }

            # Determine if rollback is needed (AC: 10 - prevent <50% effectiveness)
            if improvement_score < 0.5:  # Below 50% effectiveness
                validation_report["rollback_recommended"] = True
                validation_report["rollback_reason"] = (
                    f"Pattern effectiveness too low: {improvement_score:.2%} < 50%"
                )

            logger.info(
                "Pattern effectiveness validation completed",
                knowledge_id=shared_knowledge.knowledge_id,
                validation_status=validation_status,
                improvement_score=improvement_score,
            )

            return {
                "success": True,
                "validation_report": validation_report,
            }

        except Exception as e:
            logger.error(
                "Pattern effectiveness validation failed",
                error=str(e),
                knowledge_id=shared_knowledge.knowledge_id,
            )
            return {
                "success": False,
                "error": str(e),
                "validation_report": {},
            }

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get pattern matching service performance metrics."""
        return {
            "total_matches": self._performance_metrics["total_matches"],
            "successful_transfers": self._performance_metrics["successful_transfers"],
            "failed_transfers": self._performance_metrics["failed_transfers"],
            "success_rate": (
                self._performance_metrics["successful_transfers"]
                / max(1, self._performance_metrics["total_matches"])
            ),
            "average_similarity_score": self._performance_metrics[
                "average_similarity_score"
            ],
            "average_transferability_score": self._performance_metrics[
                "average_transferability_score"
            ],
            "circuit_breaker_state": self.circuit_breaker.state.name,
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on pattern matching service."""
        try:
            # Test AI service connectivity
            ai_health = await self.ai_service.health_check()

            # Test memory service connectivity
            memory_health = await self.memory_service.health_check()

            overall_healthy = (
                ai_health.get("status") == "healthy"
                and memory_health.get("status") == "healthy"
            )

            return {
                "status": "healthy" if overall_healthy else "unhealthy",
                "ai_service_health": ai_health,
                "memory_service_health": memory_health,
                "circuit_breaker_state": self.circuit_breaker.state.name,
                "performance_metrics": self.get_performance_metrics(),
            }

        except Exception as e:
            logger.error("Pattern matching service health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e),
            }

    # Private methods

    async def _get_persona_patterns(
        self,
        persona_id: str,
        project_id: str,
    ) -> List[Dict[str, Any]]:
        """Get patterns for a specific persona from memory."""
        try:
            # Query memory service for persona patterns
            query_context = {
                "project_id": project_id,
                "persona_id": persona_id,
                "query_text": "successful patterns high effectiveness",
                "min_relevance_score": 0.8,
                "max_results": 50,
            }

            memory_result = await self.memory_service.retrieve_memories(query_context)

            if memory_result.get("success"):
                patterns = []
                for memory in memory_result.get("memories", []):
                    # Convert memory to pattern format
                    pattern = {
                        "pattern_id": memory.get("memory_id"),
                        "persona_id": persona_id,
                        "project_id": project_id,
                        "content": memory.get("content"),
                        "effectiveness_score": memory.get("relevance_score", 0.0),
                        "metadata": memory.get("metadata", {}),
                        "created_at": memory.get("created_at"),
                    }
                    patterns.append(pattern)

                return patterns

            return []

        except Exception as e:
            logger.error(
                "Failed to get persona patterns",
                error=str(e),
                persona_id=persona_id,
            )
            return []

    async def _analyze_pattern_compatibility(
        self,
        pattern: Dict[str, Any],
        target_persona_id: str,
        context_similarity: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Analyze pattern compatibility using AI."""
        try:
            # Create a mock LearningPattern for AI analysis
            from datetime import datetime

            from orchestra.models.learning import LearningPattern

            learning_pattern = LearningPattern(
                pattern_id=pattern["pattern_id"],
                project_id=pattern["project_id"],
                persona_id=pattern["persona_id"],
                pattern_type="success_pattern",
                description=pattern.get("content", "Pattern content"),
                pattern_data=pattern.get("metadata", {}),
                confidence_score=0.8,
                effectiveness_score=pattern.get("effectiveness_score", 0.8),
                accuracy_score=0.85,
                usage_count=1,
                last_applied=datetime.utcnow(),
                created_at=datetime.utcnow(),
            )

            # Use AI service for transferability analysis
            transferability_result = (
                await self.ai_service.validate_pattern_transferability(
                    learning_pattern, target_persona_id, context_similarity
                )
            )

            if transferability_result.get("success"):
                return {
                    "success": True,
                    "pattern": pattern,
                    "transferability_score": transferability_result.get(
                        "transferability_score", 0.0
                    ),
                    "transferable": transferability_result.get("transferable", False),
                    "adaptation_requirements": transferability_result.get(
                        "adaptation_requirements", []
                    ),
                    "ai_analysis": transferability_result.get("ai_metadata", {}),
                }
            else:
                return {
                    "success": False,
                    "pattern": pattern,
                    "error": transferability_result.get("error", "AI analysis failed"),
                }

        except Exception as e:
            logger.error(
                "Pattern compatibility analysis failed",
                error=str(e),
                pattern_id=pattern.get("pattern_id"),
            )
            return {
                "success": False,
                "pattern": pattern,
                "error": str(e),
            }

    async def _create_pattern_mapping(
        self,
        compatibility_result: Dict[str, Any],
        source_persona_id: str,
        target_persona_id: str,
        project_id: str,
    ) -> PatternMapping:
        """Create PatternMapping from compatibility analysis result."""
        import uuid
        from datetime import datetime

        mapping_id = str(uuid.uuid4())
        pattern = compatibility_result["pattern"]

        return PatternMapping(
            mapping_id=mapping_id,
            source_pattern_id=pattern["pattern_id"],
            target_pattern_id=f"target-{pattern['pattern_id']}",  # Will be generated on transfer
            source_persona_id=source_persona_id,
            target_persona_id=target_persona_id,
            project_id=project_id,
            similarity_score=compatibility_result.get(
                "transferability_score", 0.0
            ),  # Using transferability as similarity
            transferability_score=compatibility_result.get(
                "transferability_score", 0.0
            ),
            mapping_type="equivalent",  # Default mapping type
            context_mapping={
                "adaptation_requirements": compatibility_result.get(
                    "adaptation_requirements", []
                ),
                "source_context": pattern.get("metadata", {}),
            },
            confidence_score=0.8,  # Default confidence
            ai_analysis=compatibility_result.get("ai_analysis", {}),
            created_at=datetime.utcnow(),
            validated=compatibility_result.get("transferable", False),
        )

    async def _ai_similarity_analysis(
        self,
        pattern_a: Dict[str, Any],
        pattern_b: Dict[str, Any],
        context_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Use AI for sophisticated pattern similarity analysis."""
        # This would use the AI service for detailed pattern comparison
        # For now, implement basic similarity scoring

        # Compare content similarity (simplified)
        content_a = pattern_a.get("content", "").lower()
        content_b = pattern_b.get("content", "").lower()

        # Basic text similarity (would use proper NLP similarity in production)
        common_words = set(content_a.split()) & set(content_b.split())
        total_words = set(content_a.split()) | set(content_b.split())

        content_similarity = len(common_words) / max(1, len(total_words))

        # Compare effectiveness scores
        effectiveness_a = pattern_a.get("effectiveness_score", 0.0)
        effectiveness_b = pattern_b.get("effectiveness_score", 0.0)
        effectiveness_similarity = 1.0 - abs(effectiveness_a - effectiveness_b)

        # Calculate overall similarity
        similarity_score = content_similarity * 0.6 + effectiveness_similarity * 0.4

        return {
            "success": True,
            "similarity_score": similarity_score,
            "analysis": {
                "content_similarity": content_similarity,
                "effectiveness_similarity": effectiveness_similarity,
                "common_elements": list(common_words)[:5],  # Top 5 common elements
            },
            "context_alignment": context_data,
            "transferability": {
                "estimated_score": similarity_score
                * 0.9,  # Slightly lower than similarity
                "factors": ["content_overlap", "effectiveness_alignment"],
            },
        }

    async def _ai_adaptation_planning(
        self,
        pattern_mapping: PatternMapping,
        target_context: Dict[str, Any],
        base_strategy: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Use AI for detailed adaptation planning."""
        # This would use the AI service for adaptation planning
        # For now, implement basic adaptation insights

        transferability_score = pattern_mapping.transferability_score

        if transferability_score > 0.9:
            effort = "minimal"
            success_probability = 0.9
            risk_factors = ["context_mismatch"]
        elif transferability_score > 0.8:
            effort = "moderate"
            success_probability = 0.75
            risk_factors = ["parameter_adaptation", "context_differences"]
        else:
            effort = "high"
            success_probability = 0.6
            risk_factors = [
                "significant_redesign",
                "context_incompatibility",
                "effectiveness_uncertainty",
            ]

        return {
            "success": True,
            "estimated_effort": effort,
            "success_probability": success_probability,
            "risk_factors": risk_factors,
            "insights": {
                "validate_context": {
                    "priority": "high",
                    "description": "Ensure target context compatibility",
                },
                "test_adaptation": {
                    "priority": "medium",
                    "description": "Thorough testing in target environment",
                },
            },
        }

    async def _analyze_effectiveness(
        self,
        target_results: Dict[str, Any],
        baseline_metrics: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Analyze effectiveness of pattern transfer."""
        try:
            # Compare target results with baseline
            improvement_metrics = {}

            # Compare success rates
            target_success_rate = target_results.get("success_rate", 0.0)
            baseline_success_rate = baseline_metrics.get("success_rate", 0.0)

            if baseline_success_rate > 0:
                success_improvement = (
                    target_success_rate - baseline_success_rate
                ) / baseline_success_rate
            else:
                success_improvement = target_success_rate

            improvement_metrics["success_rate_improvement"] = success_improvement

            # Compare quality scores
            target_quality = target_results.get("quality_score", 0.0)
            baseline_quality = baseline_metrics.get("quality_score", 0.0)

            if baseline_quality > 0:
                quality_improvement = (
                    target_quality - baseline_quality
                ) / baseline_quality
            else:
                quality_improvement = target_quality

            improvement_metrics["quality_improvement"] = quality_improvement

            # Calculate overall improvement score
            improvement_score = success_improvement * 0.6 + quality_improvement * 0.4

            return {
                "improvement_score": improvement_score,
                "improvement_metrics": improvement_metrics,
                "target_metrics": {
                    "success_rate": target_success_rate,
                    "quality_score": target_quality,
                },
                "baseline_metrics": {
                    "success_rate": baseline_success_rate,
                    "quality_score": baseline_quality,
                },
            }

        except Exception as e:
            logger.error("Effectiveness analysis failed", error=str(e))
            return {
                "improvement_score": 0.0,
                "improvement_metrics": {},
                "error": str(e),
            }

    def _update_performance_metrics(self, results: List[Dict[str, Any]]) -> None:
        """Update performance metrics from analysis results."""
        if not results:
            return

        self._performance_metrics["total_matches"] += len(results)

        similarity_scores = []
        transferability_scores = []

        for result in results:
            if result.get("success"):
                transferability_score = result.get("transferability_score", 0.0)
                transferability_scores.append(transferability_score)

                # Use transferability score as similarity for metrics
                similarity_scores.append(transferability_score)

                if transferability_score >= self.transferability_threshold:
                    self._performance_metrics["successful_transfers"] += 1
                else:
                    self._performance_metrics["failed_transfers"] += 1
            else:
                self._performance_metrics["failed_transfers"] += 1

        # Update averages
        if similarity_scores:
            current_avg_similarity = self._performance_metrics[
                "average_similarity_score"
            ]
            current_count = self._performance_metrics["total_matches"] - len(results)

            if current_count > 0:
                new_avg_similarity = (
                    current_avg_similarity * current_count + sum(similarity_scores)
                ) / self._performance_metrics["total_matches"]
            else:
                new_avg_similarity = sum(similarity_scores) / len(similarity_scores)

            self._performance_metrics["average_similarity_score"] = new_avg_similarity

        if transferability_scores:
            current_avg_transferability = self._performance_metrics[
                "average_transferability_score"
            ]
            current_count = self._performance_metrics["total_matches"] - len(results)

            if current_count > 0:
                new_avg_transferability = (
                    current_avg_transferability * current_count
                    + sum(transferability_scores)
                ) / self._performance_metrics["total_matches"]
            else:
                new_avg_transferability = sum(transferability_scores) / len(
                    transferability_scores
                )

            self._performance_metrics["average_transferability_score"] = (
                new_avg_transferability
            )
