"""MCP Server model definition."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class ServerType(str, Enum):
    """Transport type for MCP servers."""

    STDIO = "stdio"
    HTTP = "http"
    SSE = "sse"


class MCPServer(BaseModel):
    """Represents an MCP server configuration."""

    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1, max_length=100, description="Unique machine name")
    friendly_name: str = Field("", max_length=200, description="Human-readable display name")
    command: str = Field(..., min_length=1, description="Executable command")
    args: List[str] = Field(default_factory=list, description="Command arguments")
    env: Dict[str, str] = Field(default_factory=dict, description="Environment variables")
    type: ServerType = Field(ServerType.STDIO, description="Transport type")
    tags: List[str] = Field(default_factory=list, description="Organizational tags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional properties")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate server name contains only allowed characters."""
        import re

        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("Name must contain only letters, numbers, hyphens, and underscores")
        return v

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        """Validate and normalize tags."""
        return [tag.lower().strip() for tag in v if tag.strip()]

    def model_post_init(self, __context: Any) -> None:
        """Set friendly_name to name if not provided."""
        if not self.friendly_name:
            self.friendly_name = self.name.replace("_", " ").replace("-", " ").title()

    class Config:
        """Pydantic config."""

        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat(),
        }