"""VS Code adapter implementation."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp_manager.core.adapters.base import BaseAdapter
from mcp_manager.core.models import MCPServer, Scope, ServerType


class VSCodeAdapter(BaseAdapter):
    """Adapter for VS Code with GitHub Copilot."""

    def __init__(self):
        """Initialize VS Code adapter."""
        super().__init__("vscode")

    def get_config_path(self, scope: Scope) -> Path:
        """Get VS Code MCP configuration file path."""
        if scope == Scope.PROJECT:
            return Path.cwd() / ".vscode" / "mcp.json"
        else:
            # VS Code global settings would be in user settings.json
            # For MCP servers, we'll use a dedicated file
            return Path.home() / ".vscode" / "mcp.json"

    def read_config(self, scope: Scope) -> Dict[str, Any]:
        """Read VS Code MCP configuration."""
        config_path = self.get_config_path(scope)
        if not config_path.exists():
            return {"inputs": [], "servers": {}}

        with open(config_path, "r") as f:
            return json.load(f)

    def write_config(self, config: Dict[str, Any], scope: Scope) -> None:
        """Write VS Code MCP configuration."""
        config_path = self.get_config_path(scope)
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

    def get_servers(self, scope: Scope) -> List[MCPServer]:
        """Get servers from VS Code configuration."""
        config = self.read_config(scope)
        servers = []

        for name, server_config in config.get("servers", {}).items():
            # Extract environment variables from inputs if present
            env = server_config.get("env", {})
            processed_env = self._process_env_variables(env, config.get("inputs", []))

            server = MCPServer(
                name=name,
                command=server_config.get("command", ""),
                args=server_config.get("args", []),
                env=processed_env,
                type=ServerType(server_config.get("type", "stdio")),
            )
            servers.append(server)

        return servers

    def add_server(self, server: MCPServer, scope: Scope) -> None:
        """Add server to VS Code configuration."""
        self.backup_config(scope)
        config = self.read_config(scope)

        if "servers" not in config:
            config["servers"] = {}

        server_config = {
            "type": server.type.value,
            "command": server.command,
            "args": server.args,
        }

        if server.env:
            server_config["env"] = server.env
            # Add inputs for sensitive environment variables
            self._update_inputs_for_env(config, server.env)

        config["servers"][server.name] = server_config
        self.write_config(config, scope)

    def remove_server(self, server_name: str, scope: Scope) -> None:
        """Remove server from VS Code configuration."""
        self.backup_config(scope)
        config = self.read_config(scope)

        if "servers" in config and server_name in config["servers"]:
            del config["servers"][server_name]
            self.write_config(config, scope)

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate VS Code MCP configuration structure."""
        if not isinstance(config, dict):
            return False

        # Validate inputs section
        if "inputs" in config:
            if not isinstance(config["inputs"], list):
                return False
            for input_item in config["inputs"]:
                if not isinstance(input_item, dict):
                    return False
                if "id" not in input_item or "type" not in input_item:
                    return False

        # Validate servers section
        if "servers" in config:
            if not isinstance(config["servers"], dict):
                return False
            for name, server in config["servers"].items():
                if not isinstance(server, dict):
                    return False
                if "type" not in server or "command" not in server:
                    return False
                if server["type"] not in ["stdio", "http", "sse"]:
                    return False

        return True

    def _process_env_variables(
        self, env: Dict[str, str], inputs: List[Dict[str, Any]]
    ) -> Dict[str, str]:
        """Process environment variables, resolving input references."""
        processed = {}
        input_map = {inp["id"]: inp for inp in inputs}

        for key, value in env.items():
            # Check if value references an input (e.g., "${input:api-key}")
            if value.startswith("${input:") and value.endswith("}"):
                input_id = value[8:-1]
                if input_id in input_map:
                    # For now, we'll keep the reference
                    processed[key] = value
                else:
                    processed[key] = value
            else:
                processed[key] = value

        return processed

    def _update_inputs_for_env(self, config: Dict[str, Any], env: Dict[str, str]) -> None:
        """Update inputs section for environment variables that might be sensitive."""
        if "inputs" not in config:
            config["inputs"] = []

        existing_ids = {inp["id"] for inp in config["inputs"]}

        for key, value in env.items():
            # Check if this looks like a sensitive variable
            if any(
                sensitive in key.lower()
                for sensitive in ["key", "token", "secret", "password", "api"]
            ):
                input_id = f"{key.lower().replace('_', '-')}"
                if input_id not in existing_ids:
                    config["inputs"].append(
                        {
                            "type": "promptString",
                            "id": input_id,
                            "description": f"{key} for MCP server",
                            "password": True,
                        }
                    )