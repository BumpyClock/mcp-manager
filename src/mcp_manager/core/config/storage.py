"""Storage layer for MCP Manager."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

from mcp_manager.core.models import Deployment, MCPServer, Scope


class Storage:
    """SQLite storage implementation."""

    def __init__(self, db_path: Path):
        """Initialize storage with database path."""
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS servers (
                    id TEXT PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    friendly_name TEXT,
                    command TEXT NOT NULL,
                    args TEXT,
                    env TEXT,
                    type TEXT NOT NULL,
                    tags TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS deployments (
                    id TEXT PRIMARY KEY,
                    server_id TEXT NOT NULL,
                    client_name TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    enabled BOOLEAN DEFAULT 1,
                    deployed_at TIMESTAMP,
                    last_sync TIMESTAMP,
                    FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE,
                    UNIQUE(server_id, client_name, scope)
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sync_state (
                    client_name TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    config_hash TEXT,
                    last_sync TIMESTAMP,
                    PRIMARY KEY (client_name, scope)
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP
                )
            """
            )

    def add_server(self, server: MCPServer) -> None:
        """Add a new server to storage."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO servers (
                    id, name, friendly_name, command, args, env, type, 
                    tags, metadata, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    str(server.id),
                    server.name,
                    server.friendly_name,
                    server.command,
                    json.dumps(server.args),
                    json.dumps(server.env),
                    server.type.value,
                    json.dumps(server.tags),
                    json.dumps(server.metadata),
                    server.created_at.isoformat(),
                    server.updated_at.isoformat(),
                ),
            )

    def update_server(self, server: MCPServer) -> None:
        """Update an existing server."""
        server.updated_at = datetime.now()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                UPDATE servers SET 
                    name = ?, friendly_name = ?, command = ?, args = ?, 
                    env = ?, type = ?, tags = ?, metadata = ?, updated_at = ?
                WHERE id = ?
            """,
                (
                    server.name,
                    server.friendly_name,
                    server.command,
                    json.dumps(server.args),
                    json.dumps(server.env),
                    server.type.value,
                    json.dumps(server.tags),
                    json.dumps(server.metadata),
                    server.updated_at.isoformat(),
                    str(server.id),
                ),
            )

    def delete_server(self, server_id: UUID) -> None:
        """Delete a server from storage."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM servers WHERE id = ?", (str(server_id),))

    def get_server(self, server_id: UUID) -> Optional[MCPServer]:
        """Get a server by ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM servers WHERE id = ?", (str(server_id),))
            row = cursor.fetchone()

            if row:
                return self._row_to_server(row)
            return None

    def get_server_by_name(self, name: str) -> Optional[MCPServer]:
        """Get a server by name."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM servers WHERE name = ?", (name,))
            row = cursor.fetchone()

            if row:
                return self._row_to_server(row)
            return None

    def list_servers(self, filters: Optional[Dict[str, Any]] = None) -> List[MCPServer]:
        """List all servers with optional filters."""
        query = "SELECT * FROM servers"
        params = []

        if filters:
            conditions = []
            if "tags" in filters:
                # For tag filtering, we need to check JSON array
                conditions.append("tags LIKE ?")
                params.append(f'%"{filters["tags"]}"%')

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY name"

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            return [self._row_to_server(row) for row in cursor.fetchall()]

    def add_deployment(self, deployment: Deployment) -> None:
        """Add a new deployment."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO deployments (
                    id, server_id, client_name, scope, enabled, deployed_at, last_sync
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    str(deployment.id),
                    str(deployment.server_id),
                    deployment.client_name,
                    deployment.scope.value,
                    deployment.enabled,
                    deployment.deployed_at.isoformat(),
                    deployment.last_sync.isoformat() if deployment.last_sync else None,
                ),
            )

    def get_deployments(
        self, server_id: Optional[UUID] = None, client_name: Optional[str] = None
    ) -> List[Deployment]:
        """Get deployments with optional filters."""
        query = "SELECT * FROM deployments WHERE 1=1"
        params = []

        if server_id:
            query += " AND server_id = ?"
            params.append(str(server_id))

        if client_name:
            query += " AND client_name = ?"
            params.append(client_name)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            return [self._row_to_deployment(row) for row in cursor.fetchall()]

    def delete_deployment(self, deployment_id: UUID) -> None:
        """Delete a deployment."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM deployments WHERE id = ?", (str(deployment_id),))

    def _row_to_server(self, row: sqlite3.Row) -> MCPServer:
        """Convert database row to MCPServer object."""
        from mcp_manager.core.models import ServerType

        return MCPServer(
            id=UUID(row["id"]),
            name=row["name"],
            friendly_name=row["friendly_name"] or "",
            command=row["command"],
            args=json.loads(row["args"]),
            env=json.loads(row["env"]),
            type=ServerType(row["type"]),
            tags=json.loads(row["tags"]),
            metadata=json.loads(row["metadata"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def _row_to_deployment(self, row: sqlite3.Row) -> Deployment:
        """Convert database row to Deployment object."""
        return Deployment(
            id=UUID(row["id"]),
            server_id=UUID(row["server_id"]),
            client_name=row["client_name"],
            scope=Scope(row["scope"]),
            enabled=bool(row["enabled"]),
            deployed_at=datetime.fromisoformat(row["deployed_at"]),
            last_sync=datetime.fromisoformat(row["last_sync"]) if row["last_sync"] else None,
        )