"""Claude Desktop adapter implementation."""

import json
import platform
from pathlib import Path
from typing import Any, Dict, List

from mcp_manager.core.adapters.base import BaseAdapter
from mcp_manager.core.models import MCPServer, Scope, ServerType


class ClaudeDesktopAdapter(BaseAdapter):
    """Adapter for Claude Desktop client."""

    def __init__(self):
        """Initialize Claude Desktop adapter."""
        super().__init__("claude-desktop")

    def get_config_path(self, scope: Scope) -> Path:
        """Get Claude Desktop configuration file path."""
        # Claude Desktop only has global scope
        system = platform.system()

        if system == "Darwin":  # macOS
            return (
                Path.home()
                / "Library"
                / "Application Support"
                / "Claude"
                / "claude_desktop_config.json"
            )
        elif system == "Windows":
            import os

            appdata = os.environ.get("APPDATA", "")
            if appdata:
                return Path(appdata) / "Claude" / "claude_desktop_config.json"
            return Path.home() / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json"
        else:  # Linux
            return Path.home() / ".config" / "Claude" / "claude_desktop_config.json"

    def read_config(self, scope: Scope) -> Dict[str, Any]:
        """Read Claude Desktop configuration."""
        config_path = self.get_config_path(scope)
        if not config_path.exists():
            return {"mcpServers": {}}

        with open(config_path, "r") as f:
            return json.load(f)

    def write_config(self, config: Dict[str, Any], scope: Scope) -> None:
        """Write Claude Desktop configuration."""
        config_path = self.get_config_path(scope)
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

    def get_servers(self, scope: Scope) -> List[MCPServer]:
        """Get servers from Claude Desktop configuration."""
        config = self.read_config(scope)
        servers = []

        for name, server_config in config.get("mcpServers", {}).items():
            server = MCPServer(
                name=name,
                command=server_config.get("command", ""),
                args=server_config.get("args", []),
                env=server_config.get("env", {}),
                type=ServerType.STDIO,  # Claude Desktop primarily uses stdio
            )
            servers.append(server)

        return servers

    def add_server(self, server: MCPServer, scope: Scope) -> None:
        """Add server to Claude Desktop configuration."""
        self.backup_config(scope)
        config = self.read_config(scope)

        if "mcpServers" not in config:
            config["mcpServers"] = {}

        config["mcpServers"][server.name] = {
            "command": server.command,
            "args": server.args,
        }

        if server.env:
            config["mcpServers"][server.name]["env"] = server.env

        self.write_config(config, scope)

    def remove_server(self, server_name: str, scope: Scope) -> None:
        """Remove server from Claude Desktop configuration."""
        self.backup_config(scope)
        config = self.read_config(scope)

        if "mcpServers" in config and server_name in config["mcpServers"]:
            del config["mcpServers"][server_name]
            self.write_config(config, scope)

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate Claude Desktop configuration structure."""
        if not isinstance(config, dict):
            return False

        if "mcpServers" in config:
            if not isinstance(config["mcpServers"], dict):
                return False

            for name, server in config["mcpServers"].items():
                if not isinstance(server, dict):
                    return False
                if "command" not in server:
                    return False
                if "args" in server and not isinstance(server["args"], list):
                    return False

        return True