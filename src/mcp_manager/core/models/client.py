"""MCP Client model definition."""

from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class Platform(str, Enum):
    """Supported platforms."""

    WINDOWS = "windows"
    MACOS = "macos"
    LINUX = "linux"


class ConfigFormat(str, Enum):
    """Configuration file format."""

    JSON = "json"
    TOML = "toml"


class MCPClient(BaseModel):
    """Represents a client application that can consume MCP servers."""

    name: str = Field(..., description="Client identifier")
    display_name: str = Field(..., description="UI display name")
    supported_scopes: List[str] = Field(..., description="Available deployment scopes")
    config_paths: Dict[Platform, Dict[str, Path]] = Field(
        ..., description="Platform-specific config paths by scope"
    )
    config_format: ConfigFormat = Field(ConfigFormat.JSON, description="Config file format")
    supports_env_vars: bool = Field(True, description="Supports environment variables")
    supports_inputs: bool = Field(False, description="Supports VSCode-style inputs")
    installed: bool = Field(False, description="Whether client is installed")
    version: Optional[str] = Field(None, description="Detected client version")

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True