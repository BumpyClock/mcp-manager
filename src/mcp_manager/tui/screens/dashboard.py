"""Dashboard screen for MCP Manager TUI."""

from textual import on, events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, ScrollableContainer, Vertical
from textual.widgets import Button, DataTable, Label, Static

from mcp_manager.core.config.manager import ConfigManager


class DashboardScreen(Container):
    """Dashboard screen showing overview and quick actions."""

    BINDINGS = [
        Binding("a", "add_server", "Add", show=True),
        Binding("e", "edit_server", "Edit", show=True),
        Binding("d", "deploy_server", "Deploy", show=True),
        Binding("x", "delete_server", "Delete", show=True),
        Binding("r", "refresh", "Refresh", show=True),
    ]

    def __init__(self, config_manager: ConfigManager):
        """Initialize dashboard screen."""
        super().__init__()
        self.config_manager = config_manager
        self.selected_server_id = None
        self.can_focus = True

    def compose(self) -> ComposeResult:
        """Compose the dashboard layout."""
        yield ScrollableContainer(
            Container(
                Static("📊 Quick Stats", classes="section-title"),
                Horizontal(
                    self._create_stat_card("Total Servers", "0"),
                    self._create_stat_card("Total Deployments", "0"),
                    self._create_stat_card("Active Clients", "0"),
                    id="stats-container",
                    classes="stats-row",
                ),
                classes="stats-section",
            ),
            Container(
                Static("🖥️ Server Overview", classes="section-title"),
                DataTable(id="dashboard-table", show_cursor=True),
                classes="servers-overview-section",
            ),
            Container(
                Static("💡 Tips", classes="section-title"),
                Vertical(
                    Label("- Use arrow keys to navigate servers"),
                    Label("- Press Tab to switch between sections"),
                    Label("- Press 2 for full Server Management"),
                    Label("- Press 3 for Deployment Matrix"),
                    id="tips-list",
                ),
                classes="tips-section",
            ),
            classes="dashboard-container",
        )

    def _create_stat_card(self, label: str, value: str) -> Container:
        """Create a statistics card."""
        return Container(
            Label(label, classes="stat-label"),
            Label(value, classes="stat-value", id=f"stat-{label.lower().replace(' ', '-')}"),
            classes="stat-card",
        )

    def on_mount(self) -> None:
        """Called when the screen is mounted."""
        self.refresh_dashboard()

    def refresh_dashboard(self) -> None:
        """Refresh the dashboard data."""
        # Update stats
        servers = self.config_manager.list_servers()
        deployments = self.config_manager.get_deployments()
        
        # Count unique clients with deployments
        deployed_clients = set()
        for dep in deployments:
            deployed_clients.add(dep.client_name)
        
        # Update stat cards
        stats_container = self.query_one("#stats-container", Horizontal)
        stats_container.remove_children()
        stats_container.mount(
            self._create_stat_card("Total Servers", str(len(servers))),
            self._create_stat_card("Total Deployments", str(len(deployments))),
            self._create_stat_card("Active Clients", str(len(deployed_clients))),
        )
        
        # Update server table
        table = self.query_one("#dashboard-table", DataTable)
        table.clear(columns=True)
        table.cursor_type = "row"
        
        # Add columns
        table.add_column("Server Name", key="name", width=20)
        table.add_column("Type", key="type", width=8)
        table.add_column("Claude Code", key="claude-code", width=12)
        table.add_column("Claude Desktop", key="claude-desktop", width=14)
        table.add_column("VS Code", key="vscode", width=12)
        table.add_column("Tags", key="tags", width=20)
        
        # Add rows
        for server in servers:
            server_deployments = self.config_manager.get_deployments(server.id)
            
            # Check deployment status for each client
            claude_code = self._get_deployment_status(server_deployments, "claude-code")
            claude_desktop = self._get_deployment_status(server_deployments, "claude-desktop")
            vscode = self._get_deployment_status(server_deployments, "vscode")
            
            tags = ", ".join(server.tags[:2]) if server.tags else "-"
            if len(server.tags) > 2:
                tags += f" (+{len(server.tags)-2})"
            
            table.add_row(
                server.friendly_name or server.name,
                server.type.value,
                claude_code,
                claude_desktop,
                vscode,
                tags,
                key=str(server.id),
            )

    def _get_deployment_status(self, deployments, client_name: str) -> str:
        """Get deployment status for a specific client."""
        for dep in deployments:
            if dep.client_name == client_name:
                return f"[+] {dep.scope.value}"
        return "-"

    @on(DataTable.RowHighlighted)
    def on_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        """Handle row highlighting."""
        from uuid import UUID
        if event.row_key:
            self.selected_server_id = UUID(str(event.row_key.value))
            try:
                self.app.set_selected_server(self.selected_server_id)  # type: ignore[attr-defined]
            except Exception:
                pass

    @on(DataTable.RowSelected)
    def on_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection (Enter key)."""
        from uuid import UUID
        if event.row_key:
            self.selected_server_id = UUID(str(event.row_key.value))
            try:
                self.app.set_selected_server(self.selected_server_id)  # type: ignore[attr-defined]
            except Exception:
                pass
            # Go to servers tab for detailed view
            self.app.action_switch_tab("servers")

    # No on_button_pressed: rely on keybindings shown in footer

    # Key-bound actions
    def action_add_server(self) -> None:
        """Add a new server."""
        self.app.action_switch_tab("servers")

    def action_edit_server(self) -> None:
        """Edit selected server."""
        if not self.selected_server_id:
            self.app.notify("Please select a server first", severity="warning")
            return
        self.app.action_switch_tab("servers")

    def action_deploy_server(self) -> None:
        """Deploy selected server."""
        if not self.selected_server_id:
            self.app.notify("Please select a server first", severity="warning")
            return
        self.app.action_switch_tab("deploy")

    def action_delete_server(self) -> None:
        """Delete selected server."""
        if not self.selected_server_id:
            self.app.notify("Please select a server first", severity="warning")
            return
        server = self.config_manager.get_server(self.selected_server_id)
        if server:
            # Could add confirmation dialog here
            self.config_manager.delete_server(self.selected_server_id)
            self.app.notify(f"Server '{server.name}' deleted", severity="information")
            self.refresh_dashboard()

    def action_refresh(self) -> None:
        """Refresh the dashboard."""
        self.refresh_dashboard()
        self.app.notify("Dashboard refreshed", severity="information")

    def action_edit_server(self) -> None:
        """Edit selected server."""
        if not self.selected_server_id:
            self.app.notify("Please select a server first", severity="warning")
            return
        self.app.action_switch_tab("servers")

    def action_deploy_server(self) -> None:
        """Deploy selected server."""
        if not self.selected_server_id:
            self.app.notify("Please select a server first", severity="warning")
            return
        self.app.action_switch_tab("deploy")

    def action_delete_server(self) -> None:
        """Delete selected server."""
        if not self.selected_server_id:
            self.app.notify("Please select a server first", severity="warning")
            return
        server = self.config_manager.get_server(self.selected_server_id)
        if server:
            # Could add confirmation dialog here
            self.config_manager.delete_server(self.selected_server_id)
            self.app.notify(f"Server '{server.name}' deleted", severity="information")
            self.refresh_dashboard()

    def action_refresh(self) -> None:
        """Refresh the dashboard."""
        self.refresh_dashboard()
        self.app.notify("Dashboard refreshed", severity="information")
