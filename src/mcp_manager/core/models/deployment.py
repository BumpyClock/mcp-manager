"""Deployment model definition."""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Scope(str, Enum):
    """Deployment scope enumeration."""

    GLOBAL = "global"
    USER = "user"
    PROJECT = "project"


class Deployment(BaseModel):
    """Represents the relationship between servers and clients."""

    id: UUID = Field(default_factory=uuid4)
    server_id: UUID = Field(..., description="Reference to MCPServer")
    client_name: str = Field(..., description="Client identifier")
    scope: Scope = Field(..., description="Deployment scope")
    enabled: bool = Field(True, description="Whether deployment is active")
    deployed_at: datetime = Field(default_factory=datetime.now)
    last_sync: Optional[datetime] = Field(None, description="Last synchronization time")

    class Config:
        """Pydantic config."""

        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat(),
        }