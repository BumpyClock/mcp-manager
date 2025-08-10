"""Base adapter class for client integrations."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp_manager.core.models import MCPServer, Scope


class BaseAdapter(ABC):
    """Abstract base class for client adapters."""

    def __init__(self, client_name: str):
        """Initialize adapter with client name."""
        self.client_name = client_name

    @abstractmethod
    def get_config_path(self, scope: Scope) -> Path:
        """Get configuration file path for given scope."""
        pass

    @abstractmethod
    def read_config(self, scope: Scope) -> Dict[str, Any]:
        """Read configuration from file."""
        pass

    @abstractmethod
    def write_config(self, config: Dict[str, Any], scope: Scope) -> None:
        """Write configuration to file."""
        pass

    @abstractmethod
    def get_servers(self, scope: Scope) -> List[MCPServer]:
        """Get list of servers from configuration."""
        pass

    @abstractmethod
    def add_server(self, server: MCPServer, scope: Scope) -> None:
        """Add server to configuration."""
        pass

    @abstractmethod
    def remove_server(self, server_name: str, scope: Scope) -> None:
        """Remove server from configuration."""
        pass

    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate configuration structure."""
        pass

    def backup_config(self, scope: Scope) -> Optional[Path]:
        """Create backup of current configuration."""
        config_path = self.get_config_path(scope)
        if not config_path.exists():
            return None

        backup_dir = config_path.parent / ".mcp-manager-backups"
        backup_dir.mkdir(exist_ok=True)

        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"{config_path.name}.{timestamp}"

        import shutil

        shutil.copy2(config_path, backup_path)
        return backup_path

    def restore_config(self, backup_path: Path, scope: Scope) -> None:
        """Restore configuration from backup."""
        import shutil

        config_path = self.get_config_path(scope)
        shutil.copy2(backup_path, config_path)