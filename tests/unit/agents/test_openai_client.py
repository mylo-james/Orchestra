from unittest.mock import AsyncMock, patch

import pytest

from src.agents.base.secure_agent import ModelConfig, OpenAIClient


@pytest.mark.asyncio
async def test_openai_client_retries_and_returns_content():
    cfg = ModelConfig(model="gpt-4o", temperature=0.0, max_tokens=10)
    client = OpenAIClient(api_key="sk-test-key", model_cfg=cfg)

    fake_resp = AsyncMock()
    fake_resp.choices = [AsyncMock()]
    fake_resp.choices[0].message.content = "ok"

    async def create_mock(**kwargs):  # noqa: ARG001
        return fake_resp

    with patch("src.agents.base.secure_agent.AsyncOpenAI") as mock_cls:
        mock_instance = mock_cls.return_value
        mock_instance.chat.completions.create = AsyncMock(
            side_effect=[Exception("boom"), create_mock()]
        )

        # Recreate client so it uses patched class
        client = OpenAIClient(api_key="sk-test-key", model_cfg=cfg)

        result = await client.chat([{"role": "user", "content": "hi"}], retries=1)
        assert result == "ok"
