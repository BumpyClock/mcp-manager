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
from mcp_manager.tui.screens.settings import SettingsScreen


class MCPManagerApp(App):
    """Main TUI application for MCP Manager."""

    CSS = """
    Screen { background: $surface; }

    #app-header { background: $primary 20%; color: $text; height: 2; }
    .compact #app-header { height: 1; }

    #main-content { width: 100%; height: 1fr; border: round $panel 20%; }

    /* Typography */
    .section-title { text-style: bold; color: $primary; padding: 0 1; }
    .subsection-title { text-style: bold; color: $secondary; padding: 0 1; }

    /* Buttons & toolbars */
    Button { height: 3; padding: 0 1; color: $text; background: $surface 10%; border: round $panel 20%; }
    .compact Button { height: 2; padding: 0 1; }
    Button:hover { background: $surface 20%; }
    Button.-primary { background: $primary 30%; color: $text; }
    Button.-error { background: $error 30%; color: $text; }
    .toolbar Button { margin-right: 1; }
    .button-row { align: right middle; }

    /* Layout sections */
    .header-section { padding: 0 1; }
    .table-section { padding: 0 1; }
    .details-section { padding: 0 1; border: round $panel 10%; }
    .actions-section { padding: 0 1; }
    .help-section { padding: 0 1; }
    .behavior-section, .backup-section, .ui-section, .about-section { padding: 0 1; }

    /* Dashboard stats */
    .stats-row { }
    .stats-row .stat-card { margin-right: 1; }
    .stat-card { width: 1fr; min-height: 5; padding: 0 1; border: round $panel 10%; background: $boost; }
    .compact .stat-card { min-height: 4; }
    .stat-label { color: $text 70%; }
    .stat-value { text-style: bold; color: $success; }

    /* Tips list */
    #tips-list Label { padding: 0 1; color: $text 70%; }

    /* General text paddings */
    Label { padding: 0 1; }

    /* Status bar */
    #status-bar { height: 1; background: $primary 10%; color: $text 90%; padding: 0 1; }
    #status-label { padding: 0 1; }
    """

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", priority=True, show=True),
        Binding("q", "quit", "Quit", show=False),
        Binding("?", "help", "Help", show=True),
        Binding("ctrl+s", "save", "Save", show=False),
        Binding("ctrl+r", "refresh", "Refresh", show=True),
        # Quick tab switching (consolidated: no Clients tab)
        Binding("f1", "switch_tab('dashboard')", "Dashboard", show=True),
        Binding("f2", "switch_tab('servers')", "Servers", show=True),
        Binding("f3", "switch_tab('deploy')", "Deploy", show=True),
        Binding("f4", "switch_tab('settings')", "Settings", show=True),
        Binding("1", "switch_tab('dashboard')", "Dashboard", show=False),
        Binding("2", "switch_tab('servers')", "Servers", show=False),
        Binding("3", "switch_tab('deploy')", "Deploy", show=False),
        Binding("4", "switch_tab('settings')", "Settings", show=False),
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
                self.dashboard_screen = DashboardScreen(self.config_manager)
                yield self.dashboard_screen
            
            with TabPane("Servers", id="servers"):
                self.servers_screen = ServersScreen(self.config_manager)
                yield self.servers_screen
            
            with TabPane("Deploy", id="deploy"):
                self.deploy_screen = DeployScreen(self.config_manager)
                yield self.deploy_screen
            
            with TabPane("Settings", id="settings"):
                self.settings_screen = SettingsScreen(self.config_manager)
                yield self.settings_screen
        
        with Horizontal(id="status-bar"):
            yield Label("Ready", id="status-label")

        yield Footer()

    def action_quit(self) -> None:
        """Quit the application with confirmation."""
        self.push_screen(ConfirmQuitModal(self))

    def action_save(self) -> None:
        """Save current changes."""
        # Route to settings screen if active, otherwise just inform
        tabbed_content = self.query_one("#main-content", TabbedContent)
        if tabbed_content.active == "settings":
            try:
                self.settings_screen.action_save_settings()  # type: ignore[attr-defined]
            except Exception:
                pass
        self.notify("Changes saved", severity="information")

    def action_help(self) -> None:
        """Show help screen."""
        from mcp_manager.tui.screens.help import HelpScreen
        self.push_screen(HelpScreen())

    def action_refresh(self) -> None:
        """Refresh current view by delegating to active screen."""
        tabbed_content = self.query_one("#main-content", TabbedContent)
        active = tabbed_content.active
        self.set_status("Refreshing…")
        try:
            if active == "dashboard":
                self.dashboard_screen.refresh_dashboard()  # type: ignore[attr-defined]
            elif active == "servers":
                self.servers_screen.refresh_table()  # type: ignore[attr-defined]
            elif active == "deploy":
                self.deploy_screen.refresh_matrix()  # type: ignore[attr-defined]
        except Exception:
            # Fallback notification on any failure
            pass
        self.notify("Refreshed", severity="information")
        self.set_status("Ready")

    def action_switch_tab(self, tab_id: str) -> None:
        """Switch to a specific tab and sync selection if possible."""
        tabbed_content = self.query_one("#main-content", TabbedContent)
        tabbed_content.active = tab_id
        # Attempt selection sync when moving to servers/deploy
        if getattr(self, "current_selected_server_id", None):
            sid = self.current_selected_server_id
            if tab_id == "servers":
                try:
                    self.servers_screen.select_server_by_id(sid)  # type: ignore[attr-defined]
                except Exception:
                    pass
            elif tab_id == "deploy":
                try:
                    self.deploy_screen.select_server_by_id(sid)  # type: ignore[attr-defined]
                except Exception:
                    pass

    def on_mount(self) -> None:
        """Called when app is mounted."""
        # Auto-sync based on setting
        self.current_selected_server_id: Optional[str] = None
        auto_sync = self.config_manager.get_setting("auto-sync", True)
        # Apply compact mode styling from settings
        if self.config_manager.get_setting("compact-mode", False):
            self.add_class("compact")
        if auto_sync:
            try:
                self.set_status("Syncing…")
                self.config_manager.sync_all()
            except Exception:
                self.notify("Initial sync encountered issues", severity="warning")
            finally:
                self.set_status("Ready")
        self.notify("MCP Manager ready", severity="information")

    # Status bar helper
    def set_status(self, text: str) -> None:
        try:
            self.query_one("#status-label", Label).update(text)
        except Exception:
            pass

    # Selection sync helper
    def set_selected_server(self, server_id) -> None:
        try:
            self.current_selected_server_id = str(server_id) if server_id else None
        except Exception:
            self.current_selected_server_id = None

    # Toggle compact mode at runtime
    def set_compact_mode(self, enabled: bool) -> None:
        if enabled:
            self.add_class("compact")
        else:
            self.remove_class("compact")


class ConfirmQuitModal(Screen):
    """Simple confirmation modal for quitting the app."""

    CSS = """
    ConfirmQuitModal { align: center middle; }
    #dialog { width: 50; height: auto; border: round $primary; padding: 1 2; background: $surface; }
    .buttons { align: center middle; margin-top: 1; }
    """

    def __init__(self, app_ref: "MCPManagerApp"):
        super().__init__()
        self._app_ref = app_ref

    def compose(self) -> ComposeResult:
        with Container(id="dialog"):
            yield Label("Quit MCP Manager? Unsaved changes may be lost.")
            with Horizontal(classes="buttons"):
                yield Label("[Y] Yes    [N/Esc] No")

    def on_key(self, event) -> None:  # type: ignore[override]
        key = getattr(event, "key", "")
        if key.lower() in ("y", "enter"):
            self._app_ref.exit()
        elif key.lower() in ("n", "escape"):
            self.app.pop_screen()


def main():
    """Entry point for the TUI application."""
    app = MCPManagerApp()
    app.run()


if __name__ == "__main__":
    main()
