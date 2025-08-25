# OpenAI Testing Best Practices

This document outlines the **proven best practices** for testing OpenAI integrations in Orchestra AI agent system, based on our implementation patterns and industry standards.

## Overview

Orchestra uses OpenAI's `AsyncOpenAI` client for AI-assisted analysis in the `AIAnalysisService`. Testing these integrations requires careful handling of:

- **API key management** in test environments
- **HTTP request mocking** to avoid real API calls
- **Cost control** by preventing accidental live API usage
- **Response consistency** for reliable test execution

## Current Implementation Analysis

### ✅ What We're Doing Well

Our current testing approach in `tests/unit/services/test_ai_analysis_service.py`:

```python
@pytest.mark.asyncio
async def test_service_initialization(self):
    """Test service initialization with API key."""
    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
        service = AIAnalysisService(openai_api_key="custom-key")

        assert service.client is not None
        assert service.model == "gpt-4"
```

**Strengths:**
✅ **Environment isolation** - Uses `patch.dict()` to avoid affecting real environment
✅ **Test API keys** - Never uses real API keys in tests
✅ **Service mocking** - Mocks internal methods like `_execute_ai_analysis`
✅ **Error handling** - Tests both success and failure scenarios
✅ **Circuit breaker testing** - Validates resilience patterns

### 🔄 Areas for Enhancement

Based on industry best practices, here are recommended improvements:

## Recommended Testing Strategy

### **Approach 1: High-Level Method Mocking (Current - GOOD)**

**Best for:** Testing business logic and service integration

```python
@pytest.mark.asyncio
async def test_analyze_patterns_success(self, sample_outcome_events):
    """Test successful pattern analysis."""
    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
        with patch.object(AIAnalysisService, "_execute_ai_analysis") as mock_execute:
            mock_execute.return_value = {
                "patterns": [{"pattern_id": "p1", "confidence": 0.87}],
                "analysis_quality": "high",
                "processing_time": 1.2
            }

            service = AIAnalysisService()
            result = await service.analyze_outcome_patterns(sample_outcome_events)

            assert result["success"] is True
            assert len(result["patterns"]) == 1
```

**Pros:**
✅ Tests business logic flow
✅ Fast execution
✅ No external dependencies
✅ Easy to maintain

### **Approach 2: HTTP Client Mocking (ENHANCED)**

**Best for:** Testing HTTP request/response handling and error scenarios

```python
import httpx
import respx

@pytest.mark.asyncio
@respx.mock
async def test_openai_api_communication():
    """Test direct OpenAI API communication patterns."""

    # Mock the actual HTTP request
    respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={
                "choices": [{
                    "message": {
                        "content": '{"patterns": [{"id": "p1", "confidence": 0.9}]}'
                    }
                }],
                "usage": {"total_tokens": 150}
            }
        )
    )

    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
        service = AIAnalysisService()
        result = await service._execute_ai_analysis("test prompt", {"context": "test"})

        assert result["patterns"][0]["confidence"] > 0.8
```

**Pros:**
✅ Tests actual HTTP communication
✅ Validates request formatting
✅ Tests response parsing
✅ Better error scenario coverage

### **Approach 3: OpenAI Client Mocking (COMPREHENSIVE)**

**Best for:** Complete control over OpenAI client behavior

```python
from unittest.mock import AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_openai_client_integration():
    """Test OpenAI client integration with full control."""

    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
        with patch("orchestra.services.ai_analysis_service.AsyncOpenAI") as mock_openai_class:
            # Mock the client instance
            mock_client = AsyncMock()
            mock_openai_class.return_value = mock_client

            # Mock the chat completion response
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = '{"analysis": "success"}'
            mock_response.usage.total_tokens = 100

            mock_client.chat.completions.create.return_value = mock_response

            service = AIAnalysisService()
            result = await service._execute_ai_analysis("test prompt", {})

            # Verify client was called correctly
            mock_client.chat.completions.create.assert_called_once()
            call_args = mock_client.chat.completions.create.call_args
            assert call_args.kwargs["model"] == "gpt-4"
            assert call_args.kwargs["temperature"] == 0.3
```

**Pros:**
✅ Complete control over client behavior
✅ Validates exact API parameters
✅ Tests client configuration
✅ Precise assertion capabilities

## Enhanced Best Practices

### 1. **API Key Management**

```python
# ✅ GOOD: Environment patching (current approach)
with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key-secure"}):
    service = AIAnalysisService()

# ✅ BETTER: Explicit test configuration
@pytest.fixture
def test_openai_service():
    """Provide AIAnalysisService with test configuration."""
    return AIAnalysisService(
        openai_api_key="test-key-fixture",
        model="gpt-3.5-turbo",  # Cheaper model for tests
        max_tokens=500,         # Smaller limit for tests
        temperature=0.0         # Deterministic responses
    )
```

### 2. **Response Consistency**

```python
@pytest.fixture
def mock_openai_responses():
    """Standard mock responses for consistent testing."""
    return {
        "pattern_analysis": {
            "choices": [{"message": {"content": '{"patterns": [{"id": "p1"}]}'}}],
            "usage": {"total_tokens": 150}
        },
        "recommendations": {
            "choices": [{"message": {"content": '{"recommendations": [{"id": "r1"}]}'}}],
            "usage": {"total_tokens": 200}
        },
        "error_response": httpx.Response(
            429,  # Rate limit
            json={"error": {"message": "Rate limit exceeded", "type": "rate_limit"}}
        )
    }
```

### 3. **Cost Control Safeguards**

```python
def test_no_real_api_calls_in_tests():
    """Ensure tests never make real API calls."""
    # This test ensures we never accidentally hit real APIs
    with patch.dict("os.environ", {}, clear=True):  # Clear all env vars
        with pytest.raises(Exception, match="api_key.*required"):
            # Should fail without API key rather than use a default
            AIAnalysisService()

@pytest.mark.integration
@pytest.mark.skipif(not os.environ.get("RUN_INTEGRATION_TESTS"),
                   reason="Integration tests require explicit enable")
async def test_real_openai_integration():
    """Integration test with real API (only when explicitly enabled)."""
    # Real API tests only when RUN_INTEGRATION_TESTS=true
    pass
```

### 4. **Error Scenario Coverage**

```python
@pytest.mark.asyncio
async def test_openai_error_scenarios():
    """Test comprehensive error handling."""
    error_scenarios = [
        (httpx.Response(429, json={"error": {"type": "rate_limit"}}), "rate_limit"),
        (httpx.Response(400, json={"error": {"type": "invalid_request"}}), "invalid_request"),
        (httpx.Response(500, json={"error": {"type": "server_error"}}), "server_error"),
        (httpx.ConnectError("Connection failed"), "connection_error")
    ]

    for error_response, expected_error_type in error_scenarios:
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            with patch.object(httpx.AsyncClient, "post", side_effect=error_response):
                service = AIAnalysisService()
                result = await service.analyze_outcome_patterns([])

                assert result["success"] is False
                assert expected_error_type in result["error"].lower()
```

## Performance Testing

### 5. **Circuit Breaker Validation**

```python
@pytest.mark.asyncio
async def test_circuit_breaker_behavior():
    """Test circuit breaker prevents cascading failures."""
    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
        service = AIAnalysisService()

        # Trigger circuit breaker with repeated failures
        with patch.object(service, "_execute_ai_analysis", side_effect=Exception("API Error")):
            for _ in range(3):  # Failure threshold
                result = await service.analyze_outcome_patterns([])
                assert result["success"] is False

        # Verify circuit breaker is open
        stats = service.circuit_breaker.get_stats()
        assert stats["state"] == "OPEN"

        # Verify subsequent calls fail fast
        with patch.object(service, "_execute_ai_analysis") as mock_execute:
            result = await service.analyze_outcome_patterns([])
            assert result["success"] is False
            mock_execute.assert_not_called()  # Should not try API when circuit is open
```

### 6. **Token Usage Monitoring**

```python
@pytest.mark.asyncio
async def test_token_usage_tracking():
    """Test token usage monitoring for cost control."""
    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
        with patch.object(AIAnalysisService, "_execute_ai_analysis") as mock_execute:
            mock_execute.return_value = {
                "patterns": [],
                "usage": {"total_tokens": 250, "prompt_tokens": 100, "completion_tokens": 150}
            }

            service = AIAnalysisService()
            await service.analyze_outcome_patterns([])

            stats = service.get_api_usage_statistics()
            assert stats["total_requests"] == 1
            assert stats["total_tokens_used"] == 250
            assert stats["estimated_cost"] > 0
```

## Implementation Roadmap

### **Phase 1: Enhance Current Approach** ✅ (Recommended)

1. Add response fixtures for consistency
2. Improve error scenario coverage
3. Add cost control safeguards
4. Enhance circuit breaker testing

### **Phase 2: Add HTTP Client Mocking** (Optional)

1. Introduce `respx` or `httpx-mock` for HTTP-level testing
2. Add request/response validation
3. Test network error scenarios

### **Phase 3: Integration Testing** (Optional)

1. Add optional real API integration tests
2. Add performance benchmarking
3. Add load testing for circuit breaker

## Dependencies

To implement enhanced testing patterns:

```bash
# Current (already have)
pytest
pytest-asyncio

# Recommended additions
pip install respx              # HTTP request mocking
pip install pytest-mock       # Enhanced mocking utilities
pip install faker             # Generate test data
```

## Comparison with Industry Standards

### ✅ **What We Match**

- **Environment isolation** - Standard practice for API key management
- **Method-level mocking** - Common pattern for business logic testing
- **Error handling** - Comprehensive failure scenario coverage
- **Circuit breaker patterns** - Industry standard for resilience

### 🔄 **What We Could Add**

- **HTTP-level mocking** - More granular request/response testing
- **Response fixtures** - Standardized mock responses for consistency
- **Integration test controls** - Explicit opt-in for real API testing
- **Performance monitoring** - Token usage and cost tracking in tests

## Conclusion

Orchestra's current OpenAI testing approach is **solid and follows industry best practices**. The main areas for enhancement are:

1. **Response standardization** through fixtures
2. **Enhanced error scenarios** with HTTP-level mocking
3. **Integration test controls** for optional real API testing
4. **Performance monitoring** for cost and usage tracking

The current approach successfully:
- ✅ **Prevents accidental API costs** through environment isolation
- ✅ **Tests business logic thoroughly** through method mocking
- ✅ **Handles errors gracefully** with circuit breaker patterns
- ✅ **Maintains fast test execution** with proper mocking

**Recommendation**: Continue with current approach while gradually adding enhanced patterns as needed for specific test scenarios.
