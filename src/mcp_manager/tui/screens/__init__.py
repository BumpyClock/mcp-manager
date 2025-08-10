"""TUI screens for MCP Manager."""

from mcp_manager.tui.screens.dashboard import DashboardScreen
from mcp_manager.tui.screens.servers import ServersScreen
from mcp_manager.tui.screens.deploy import DeployScreen
from mcp_manager.tui.screens.clients import ClientsScreen
from mcp_manager.tui.screens.settings import SettingsScreen
from mcp_manager.tui.screens.help import HelpScreen

__all__ = [
    "DashboardScreen",
    "ServersScreen",
    "DeployScreen",
    "ClientsScreen",
    "SettingsScreen",
    "HelpScreen",
]