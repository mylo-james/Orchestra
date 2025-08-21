import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from src.agents.developer.tools import developer_tool_registry


@pytest.mark.asyncio
async def test_github_create_pr_tool_invokes_external_client():
    registry = developer_tool_registry()

    async def fake_create_pr(title: str, description: str, branch: str):  # noqa: ARG001
        return {"html_url": "https://example/pr/1", "number": 1}

    with patch(
        "src.services.external_service_client.ExternalServiceClient.create_github_pr",
        new=AsyncMock(side_effect=fake_create_pr),
    ):
        with patch("src.agents.tools.github.get_settings") as mock_settings:
            mock_settings.return_value.github.token = "test_token"

            result = await registry.call(
                "github.create_pr",
                {"title": "T", "body": "B", "branch": "feat/x"},
            )
            assert result["result"]["url"].endswith("/1")


def test_tool_validation_errors():
    registry = developer_tool_registry()
    with patch("src.agents.tools.github.get_settings") as mock_settings:
        mock_settings.return_value.github.token = "test_token"

        with pytest.raises(ValueError):
            asyncio.run(
                registry.call(
                    "github.create_pr", {"title": "", "body": "", "branch": ""}
                )
            )
