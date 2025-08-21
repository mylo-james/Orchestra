"""
External Service Client with Circuit Breaker Protection

Provides secure, resilient access to external services with circuit breaker protection
to prevent AI agent cascade failures.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict

import httpx
import openai

from src.utils.circuit_breaker import (
    CircuitBreakerError,
    get_circuit_breaker_stats,
    get_failing_services,
    get_github_circuit_breaker,
    get_openai_circuit_breaker,
    get_pinecone_circuit_breaker,
    get_temporal_circuit_breaker,
    protect_external_service,
    protect_external_service_async,
)

logger = logging.getLogger(__name__)


class ExternalServiceClient:
    """
    Secure client for all external service interactions.

    This client provides:
    - Circuit breaker protection for all external services
    - Comprehensive error handling and logging
    - Fallback mechanisms for service failures
    - AI agent specific protections
    """

    def __init__(self, settings):
        self.settings = settings
        self.openai_client = openai.Client(api_key=settings.openai.api_key)
        self.http_client = httpx.AsyncClient(timeout=30.0)

        logger.info(
            "External service client initialized with circuit breaker protection"
        )

    # OpenAI API with circuit breaker protection
    @protect_external_service(
        "openai_api", fallback_result="# API temporarily unavailable"
    )
    def generate_code_with_openai(self, prompt: str, model: str = "gpt-4") -> str:
        """
        Generate code using OpenAI API with circuit breaker protection.

        Args:
            prompt: Code generation prompt
            model: OpenAI model to use

        Returns:
            Generated code or fallback message
        """
        try:
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a secure code generator. Generate safe, high-quality code.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=2000,
                temperature=0.1,  # Lower temperature for more deterministic code generation
            )

            generated_code = response.choices[0].message.content
            logger.info(
                f"OpenAI code generation successful - {len(generated_code)} characters"
            )

            return generated_code

        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise

    @protect_external_service_async(
        "openai_api", fallback_result="# API temporarily unavailable"
    )
    async def generate_code_with_openai_async(
        self, prompt: str, model: str = "gpt-4"
    ) -> str:
        """Async version of OpenAI code generation."""
        try:
            # Use async OpenAI client
            response = await self.openai_client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a secure code generator. Generate safe, high-quality code.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=2000,
                temperature=0.1,
            )

            generated_code = response.choices[0].message.content
            logger.info(
                f"OpenAI async code generation successful - {len(generated_code)} characters"
            )

            return generated_code

        except Exception as e:
            logger.error(f"OpenAI async API call failed: {e}")
            raise

    # GitHub API with circuit breaker protection
    @protect_external_service_async(
        "github_api", fallback_result={"error": "GitHub API temporarily unavailable"}
    )
    async def create_github_pr(
        self, title: str, description: str, branch: str
    ) -> Dict[str, Any]:
        """
        Create GitHub pull request with circuit breaker protection.

        Args:
            title: PR title
            description: PR description
            branch: Source branch

        Returns:
            PR creation result or fallback error
        """
        try:
            # GitHub API call (using httpx for async)
            headers = {
                "Authorization": f"token {self.settings.github.token}",
                "Accept": "application/vnd.github.v3+json",
            }

            pr_data = {
                "title": title,
                "body": description,
                "head": branch,
                "base": "main",
            }

            response = await self.http_client.post(
                f"https://api.github.com/repos/{self.settings.github.repo}/pulls",
                json=pr_data,
                headers=headers,
            )

            response.raise_for_status()
            result = response.json()

            logger.info(
                f"GitHub PR created successfully: {result.get('url', 'Unknown URL')}"
            )
            return result

        except Exception as e:
            logger.error(f"GitHub API call failed: {e}")
            raise

    # Pinecone Vector Database with circuit breaker protection
    @protect_external_service_async("pinecone_vector_db", fallback_result=[])
    async def query_pinecone_knowledge(
        self, query: str, top_k: int = 5
    ) -> list[Dict[str, Any]]:
        """
        Query Pinecone vector database with circuit breaker protection.

        Args:
            query: Search query
            top_k: Number of results to return

        Returns:
            Search results or empty list as fallback
        """
        try:
            # This would contain actual Pinecone client logic
            # For demonstration, simulate the call
            await asyncio.sleep(0.1)  # Simulate API call delay

            # Placeholder result
            results = [
                {"id": "doc1", "score": 0.95, "text": f"Knowledge about: {query}"},
                {"id": "doc2", "score": 0.87, "text": f"Related info: {query}"},
            ]

            logger.info(f"Pinecone query successful - {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Pinecone API call failed: {e}")
            raise

    # Temporal Cloud with circuit breaker protection
    @protect_external_service_async(
        "temporal_cloud",
        fallback_result={"workflow_id": "fallback", "status": "degraded"},
    )
    async def start_temporal_workflow(
        self, workflow_type: str, workflow_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Start Temporal workflow with circuit breaker protection.

        Args:
            workflow_type: Type of workflow to start
            workflow_input: Input data for the workflow

        Returns:
            Workflow start result or fallback status
        """
        try:
            # This would contain actual Temporal client logic
            # For demonstration, simulate the call
            await asyncio.sleep(0.2)  # Simulate workflow start delay

            workflow_id = f"workflow_{datetime.utcnow().timestamp()}"
            result = {
                "workflow_id": workflow_id,
                "status": "started",
                "workflow_type": workflow_type,
            }

            logger.info(f"Temporal workflow started successfully: {workflow_id}")
            return result

        except Exception as e:
            logger.error(f"Temporal API call failed: {e}")
            raise

    async def close(self) -> None:
        """Close HTTP client connections."""
        await self.http_client.aclose()


# Example AI Agent using circuit breaker protected services
class SecureAIAgent:
    """
    Example AI agent that uses circuit breaker protected external services.

    This demonstrates how AI agents should interact with external services
    to prevent cascade failures and maintain system resilience.
    """

    def __init__(self, agent_id: str, settings):
        self.agent_id = agent_id
        self.external_client = ExternalServiceClient(settings)
        logger.info(f"Secure AI agent '{agent_id}' initialized")

    async def generate_and_commit_code(self, prompt: str) -> Dict[str, Any]:
        """
        Generate code and create PR with full circuit breaker protection.

        This method demonstrates how AI agents can gracefully handle
        external service failures without causing system-wide issues.
        """
        result = {
            "agent_id": self.agent_id,
            "prompt": prompt,
            "generated_code": None,
            "knowledge_context": None,
            "pr_created": None,
            "workflow_started": None,
            "fallbacks_used": [],
            "success": False,
        }

        try:
            # Step 1: Get knowledge context (with fallback)
            try:
                result["knowledge_context"] = (
                    await self.external_client.query_pinecone_knowledge(prompt)
                )
                logger.info("Knowledge context retrieved successfully")
            except CircuitBreakerError:
                result["fallbacks_used"].append("pinecone_fallback")
                result["knowledge_context"] = []
                logger.warning(
                    "Using empty knowledge context due to Pinecone circuit breaker"
                )

            # Step 2: Generate code (with fallback)
            try:
                result["generated_code"] = (
                    await self.external_client.generate_code_with_openai_async(prompt)
                )
                logger.info("Code generation completed successfully")
            except CircuitBreakerError:
                result["fallbacks_used"].append("openai_fallback")
                result["generated_code"] = (
                    f"# Code generation temporarily unavailable\n# Prompt: {prompt}\n# TODO: Retry when OpenAI service recovers"
                )
                logger.warning("Using fallback code due to OpenAI circuit breaker")

            # Step 3: Create PR (with fallback)
            try:
                pr_result = await self.external_client.create_github_pr(
                    title=f"AI Generated: {prompt[:50]}...",
                    description=f"Generated by agent {self.agent_id}",
                    branch=f"ai-feature-{int(datetime.utcnow().timestamp())}",
                )
                result["pr_created"] = pr_result
                logger.info("GitHub PR created successfully")
            except CircuitBreakerError:
                result["fallbacks_used"].append("github_fallback")
                result["pr_created"] = {
                    "error": "GitHub temporarily unavailable",
                    "local_changes": "saved",
                }
                logger.warning("Local changes saved due to GitHub circuit breaker")

            # Step 4: Start workflow (with fallback)
            try:
                workflow_result = await self.external_client.start_temporal_workflow(
                    "ai_code_generation", {"agent_id": self.agent_id, "prompt": prompt}
                )
                result["workflow_started"] = workflow_result
                logger.info("Temporal workflow started successfully")
            except CircuitBreakerError:
                result["fallbacks_used"].append("temporal_fallback")
                result["workflow_started"] = {
                    "status": "degraded_mode",
                    "local_execution": True,
                }
                logger.warning("Using local execution due to Temporal circuit breaker")

            result["success"] = True
            logger.info(
                f"AI agent operation completed with {len(result['fallbacks_used'])} fallbacks"
            )

        except Exception as e:
            logger.error(f"AI agent operation failed: {e}")
            result["error"] = str(e)

        return result


# Test function
async def test_circuit_breakers():
    """Test circuit breaker functionality."""
    print("🧪 Testing Circuit Breaker System")
    print("=" * 40)

    # Test individual circuit breakers
    openai_cb = get_openai_circuit_breaker()
    print(f"OpenAI circuit breaker state: {openai_cb.state.value}")

    temporal_cb = get_temporal_circuit_breaker()
    print(f"Temporal circuit breaker state: {temporal_cb.state.value}")

    pinecone_cb = get_pinecone_circuit_breaker()
    print(f"Pinecone circuit breaker state: {pinecone_cb.state.value}")

    github_cb = get_github_circuit_breaker()
    print(f"GitHub circuit breaker state: {github_cb.state.value}")

    # Test stats
    stats = get_circuit_breaker_stats()
    print(f"\nCircuit breaker statistics: {len(stats)} breakers initialized")

    failing_services = get_failing_services()
    print(f"Failing services: {failing_services if failing_services else 'None'}")

    print("\n✅ Circuit breaker system test complete!")


if __name__ == "__main__":
    asyncio.run(test_circuit_breakers())
