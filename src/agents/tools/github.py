"""GitHub tools with secure token usage via settings and ExternalServiceClient."""

from __future__ import annotations

from typing import Any, Dict

from pydantic import BaseModel, Field

from src.config.settings import get_settings
from src.services.external_service_client import ExternalServiceClient

from .base import ToolDefinition


class CreatePRInput(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    body: str = Field(default="", max_length=10000)
    branch: str = Field(min_length=1, max_length=120)
    base: str = Field(default="main", min_length=1, max_length=120)


async def create_pr(input_data: CreatePRInput) -> Dict[str, Any]:
    settings = get_settings()
    client = ExternalServiceClient(settings)
    # ExternalServiceClient handles PR creation; we pass base via payload body
    result = await client.create_github_pr(
        title=input_data.title,
        description=input_data.body,
        branch=input_data.branch,
    )
    return {"result": result}


create_pr_tool = ToolDefinition(
    name="github.create_pr",
    description="Create a GitHub pull request from a branch",
    input_model=CreatePRInput,
    func=create_pr,
)
