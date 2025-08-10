"""Clients status screen for MCP Manager TUI."""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, DataTable, Label, Static

from mcp_manager.core.config.manager import ConfigManager
from mcp_manager.core.models import Scope


class ClientsScreen(Container):
    """Clients status and management screen."""

    def __init__(self, config_manager: ConfigManager):
        """Initialize clients screen."""
        super().__init__()
        self.config_manager = config_manager

    def compose(self) -> ComposeResult:
        """Compose the clients screen layout."""
        yield Vertical(
            Container(
                Static("🔌 Client Status", classes="section-title"),
                Horizontal(
                    Button("Refresh [r]", id="btn-refresh"),
                    Button("Sync Selected [s]", id="btn-sync-selected"),
                    Button("Sync All [a]", id="btn-sync-all", variant="primary"),
                    classes="toolbar",
                ),
                classes="header-section",
            ),
            Container(
                DataTable(id="clients-table"),
                classes="table-section",
            ),
            Container(
                Static("Client Details", classes="section-title"),
                Label("Select a client to view details", id="client-details"),
                classes="details-section",
            ),
            classes="clients-container",
        )

    def on_mount(self) -> None:
        """Called when the screen is mounted."""
        self.refresh_table()

    def refresh_table(self) -> None:
        """Refresh the clients table."""
        table = self.query_one("#clients-table", DataTable)
        table.clear(columns=True)
        
        # Add columns
        table.add_column("Client", key="client")
        table.add_column("Status", key="status")
        table.add_column("Global Config", key="global_config")
        table.add_column("Project Config", key="project_config")
        
        # Add rows for each client
        for client_name, adapter in self.config_manager.adapters.items():
            display_name = client_name.replace("-", " ").title()
            
            # Check if configs exist
            global_path = adapter.get_config_path(Scope.GLOBAL)
            project_path = adapter.get_config_path(Scope.PROJECT)
            
            status = "✓ Ready"  # Simple status for now
            
            table.add_row(
                display_name,
                status,
                str(global_path) if global_path else "N/A",
                str(project_path) if project_path else "N/A",
                key=client_name,
            )

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection."""
        if event.row_key:
            self.update_details(str(event.row_key.value))

    def update_details(self, client_name: str) -> None:
        """Update the client details panel."""
        adapter = self.config_manager.adapters.get(client_name)
        if not adapter:
            return

        details = f"""Client: {client_name.replace('-', ' ').title()}

Configuration Paths:
"""
        
        for scope in [Scope.GLOBAL, Scope.PROJECT]:
            try:
                path = adapter.get_config_path(scope)
                exists = path.exists() if path else False
                details += f"  {scope.value.title()}: {path}\n"
                details += f"    Status: {'Exists' if exists else 'Not found'}\n"
                
                if exists:
                    servers = adapter.get_servers(scope)
                    details += f"    Servers: {len(servers)}\n"
            except Exception as e:
                details += f"  {scope.value.title()}: Error - {str(e)}\n"

        self.query_one("#client-details", Label).update(details)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id
        
        if button_id == "btn-refresh":
            self.refresh_table()
            self.app.notify("Client status refreshed", severity="information")
        
        elif button_id == "btn-sync-selected":
            table = self.query_one("#clients-table", DataTable)
            if table.cursor_row >= 0:
                # Get selected client
                row_key = list(table.rows.keys())[table.cursor_row]
                client_name = str(row_key.value)
                
                # Perform sync
                try:
                    results = self.config_manager.sync_client(client_name)
                    self.app.notify(f"Synced {client_name}", severity="success")
                    self.refresh_table()
                except Exception as e:
                    self.app.notify(f"Sync failed: {str(e)}", severity="error")
            else:
                self.app.notify("Please select a client to sync", severity="warning")
        
        elif button_id == "btn-sync-all":
            # Sync all clients
            try:
                results = self.config_manager.sync_all()
                self.app.notify("All clients synced", severity="success")
                self.refresh_table()
            except Exception as e:
                self.app.notify(f"Sync failed: {str(e)}", severity="error")