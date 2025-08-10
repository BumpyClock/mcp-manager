"""Main TUI application using Textual."""

from pathlib import Path
from typing import Optional

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Label, TabbedContent, TabPane

from mcp_manager.core.config.manager import ConfigManager
from mcp_manager.tui.screens.dashboard import DashboardScreen
from mcp_manager.tui.screens.servers import ServersScreen
from mcp_manager.tui.screens.deploy import DeployScreen
from mcp_manager.tui.screens.clients import ClientsScreen
from mcp_manager.tui.screens.settings import SettingsScreen


class MCPManagerApp(App):
    """Main TUI application for MCP Manager."""

    CSS = """
    Screen {
        background: $surface;
    }

    #app-header {
        background: $primary;
        color: $text;
        height: 3;
    }

    #main-content {
        width: 100%;
        height: 1fr;
    }

    .tab-content {
        padding: 1;
    }

    Label {
        padding: 1;
    }
    """

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", priority=True),
        Binding("ctrl+s", "save", "Save"),
        Binding("f1", "help", "Help"),
        Binding("ctrl+r", "refresh", "Refresh"),
        Binding("1", "switch_tab('dashboard')", "Dashboard", show=False),
        Binding("2", "switch_tab('servers')", "Servers", show=False),
        Binding("3", "switch_tab('deploy')", "Deploy", show=False),
        Binding("4", "switch_tab('clients')", "Clients", show=False),
        Binding("5", "switch_tab('settings')", "Settings", show=False),
    ]

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize the TUI application."""
        super().__init__()
        self.config_manager = ConfigManager(config_path)
        self.title = "MCP Manager v1.0.0"

    def compose(self) -> ComposeResult:
        """Compose the application layout."""
        yield Header(id="app-header")
        
        with TabbedContent(initial="dashboard", id="main-content"):
            with TabPane("Dashboard", id="dashboard"):
                yield DashboardScreen(self.config_manager)
            
            with TabPane("Servers", id="servers"):
                yield ServersScreen(self.config_manager)
            
            with TabPane("Deploy", id="deploy"):
                yield DeployScreen(self.config_manager)
            
            with TabPane("Clients", id="clients"):
                yield ClientsScreen(self.config_manager)
            
            with TabPane("Settings", id="settings"):
                yield SettingsScreen(self.config_manager)
        
        yield Footer()

    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()

    def action_save(self) -> None:
        """Save current changes."""
        # Trigger save in the active screen
        self.notify("Changes saved", severity="information")

    def action_help(self) -> None:
        """Show help screen."""
        from mcp_manager.tui.screens.help import HelpScreen
        self.push_screen(HelpScreen())

    def action_refresh(self) -> None:
        """Refresh current view."""
        # Trigger refresh in the active screen
        self.notify("Refreshed", severity="information")

    def action_switch_tab(self, tab_id: str) -> None:
        """Switch to a specific tab."""
        tabbed_content = self.query_one("#main-content", TabbedContent)
        tabbed_content.active = tab_id

    def on_mount(self) -> None:
        """Called when app is mounted."""
        # Perform initial sync check
        self.config_manager.sync_all()
        self.notify("MCP Manager ready", severity="information")


def main():
    """Entry point for the TUI application."""
    app = MCPManagerApp()
    app.run()


if __name__ == "__main__":
    main()