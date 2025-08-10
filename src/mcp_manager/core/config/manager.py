"""Configuration manager for MCP Manager."""

from pathlib import Path
from typing import Dict, List, Optional
from uuid import UUID

from mcp_manager.core.adapters import (
    BaseAdapter,
    ClaudeCodeAdapter,
    ClaudeDesktopAdapter,
    VSCodeAdapter,
)
from mcp_manager.core.config.storage import Storage
from mcp_manager.core.models import Deployment, MCPServer, Scope


class ConfigManager:
    """Manages application configuration and state."""

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize configuration manager."""
        if db_path is None:
            db_path = Path.home() / ".mcp-manager" / "mcp-manager.db"

        self.storage = Storage(db_path)
        self.adapters: Dict[str, BaseAdapter] = {
            "claude-code": ClaudeCodeAdapter(),
            "claude-desktop": ClaudeDesktopAdapter(),
            "vscode": VSCodeAdapter(),
        }

    # Server operations
    def add_server(self, server: MCPServer) -> UUID:
        """Add a new server."""
        self.storage.add_server(server)
        return server.id

    def update_server(self, server: MCPServer) -> None:
        """Update an existing server."""
        self.storage.update_server(server)

    def delete_server(self, server_id: UUID) -> None:
        """Delete a server and its deployments."""
        self.storage.delete_server(server_id)

    def get_server(self, server_id: UUID) -> Optional[MCPServer]:
        """Get a server by ID."""
        return self.storage.get_server(server_id)

    def get_server_by_name(self, name: str) -> Optional[MCPServer]:
        """Get a server by name."""
        return self.storage.get_server_by_name(name)

    def list_servers(self, filters: Optional[Dict] = None) -> List[MCPServer]:
        """List all servers with optional filters."""
        return self.storage.list_servers(filters)

    # Deployment operations
    def deploy_server(
        self, server_id: UUID, client_name: str, scope: Scope
    ) -> None:
        """Deploy a server to a client."""
        server = self.get_server(server_id)
        if not server:
            raise ValueError(f"Server with ID {server_id} not found")

        if client_name not in self.adapters:
            raise ValueError(f"Unknown client: {client_name}")

        # Add server to client configuration
        adapter = self.adapters[client_name]
        adapter.add_server(server, scope)

        # Record deployment
        from uuid import uuid4

        deployment = Deployment(
            id=uuid4(),
            server_id=server_id,
            client_name=client_name,
            scope=scope,
        )
        self.storage.add_deployment(deployment)

    def undeploy_server(
        self, server_id: UUID, client_name: str, scope: Scope
    ) -> None:
        """Remove a server deployment from a client."""
        server = self.get_server(server_id)
        if not server:
            raise ValueError(f"Server with ID {server_id} not found")

        if client_name not in self.adapters:
            raise ValueError(f"Unknown client: {client_name}")

        # Remove server from client configuration
        adapter = self.adapters[client_name]
        adapter.remove_server(server.name, scope)

        # Remove deployment record
        deployments = self.storage.get_deployments(server_id, client_name)
        for deployment in deployments:
            if deployment.scope == scope:
                self.storage.delete_deployment(deployment.id)

    def get_deployments(
        self, server_id: Optional[UUID] = None
    ) -> List[Deployment]:
        """Get deployments for a server or all deployments."""
        return self.storage.get_deployments(server_id)

    # Bulk operations
    def deploy_servers(
        self, server_ids: List[UUID], clients: List[str], scope: Scope
    ) -> Dict[str, List[str]]:
        """Deploy multiple servers to multiple clients."""
        results = {"success": [], "failed": []}

        for server_id in server_ids:
            server = self.get_server(server_id)
            if not server:
                results["failed"].append(f"Server {server_id} not found")
                continue

            for client in clients:
                try:
                    self.deploy_server(server_id, client, scope)
                    results["success"].append(f"{server.name} -> {client}")
                except Exception as e:
                    results["failed"].append(f"{server.name} -> {client}: {str(e)}")

        return results

    # Sync operations
    def sync_client(self, client_name: str) -> Dict[str, List[str]]:
        """Sync configuration with a specific client."""
        if client_name not in self.adapters:
            raise ValueError(f"Unknown client: {client_name}")

        adapter = self.adapters[client_name]
        results = {"added": [], "removed": [], "updated": [], "deployments_created": []}

        # Get servers from client for all scopes
        for scope in [Scope.GLOBAL, Scope.PROJECT]:
            try:
                client_servers = adapter.get_servers(scope)
                
                for client_server in client_servers:
                    # Check if server exists in our database
                    db_server = self.get_server_by_name(client_server.name)
                    
                    if not db_server:
                        # New server found in client, add to database
                        server_id = self.add_server(client_server)
                        results["added"].append(client_server.name)
                        
                        # Create deployment record since it's deployed in the client
                        from uuid import uuid4
                        deployment = Deployment(
                            id=uuid4(),
                            server_id=server_id,
                            client_name=client_name,
                            scope=scope,
                        )
                        self.storage.add_deployment(deployment)
                        results["deployments_created"].append(f"{client_server.name} ({scope.value})")
                    else:
                        # Server exists, check if deployment record exists
                        existing_deployments = self.get_deployments(db_server.id)
                        has_deployment = any(
                            d.client_name == client_name and d.scope == scope
                            for d in existing_deployments
                        )
                        
                        if not has_deployment:
                            # Server is deployed but we don't have a record, create one
                            from uuid import uuid4
                            deployment = Deployment(
                                id=uuid4(),
                                server_id=db_server.id,
                                client_name=client_name,
                                scope=scope,
                            )
                            self.storage.add_deployment(deployment)
                            results["deployments_created"].append(f"{client_server.name} ({scope.value})")
            except Exception:
                # Scope might not be available for this client
                pass

        return results

    def sync_all(self) -> Dict[str, Dict[str, List[str]]]:
        """Sync configuration with all clients."""
        results = {}
        
        for client_name in self.adapters:
            try:
                results[client_name] = self.sync_client(client_name)
            except Exception as e:
                results[client_name] = {"error": [str(e)]}

        return results

    # Settings operations
    def set_setting(self, key: str, value):
        self.storage.set_setting(key, value)

    def get_setting(self, key: str, default=None):
        return self.storage.get_setting(key, default)

    def set_settings(self, values: Dict[str, object]) -> None:
        for k, v in values.items():
            self.set_setting(k, v)

    def get_settings(self) -> Dict[str, object]:
        return self.storage.get_all_settings()
