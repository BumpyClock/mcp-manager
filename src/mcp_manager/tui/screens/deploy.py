"""Deploy screen for MCP Manager TUI."""

from uuid import UUID
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Checkbox, DataTable, Label, Select, Static

from mcp_manager.core.config.manager import ConfigManager
from mcp_manager.core.models import Scope


class DeployScreen(Container):
    """Deployment matrix screen for managing server deployments."""

    def __init__(self, config_manager: ConfigManager):
        """Initialize deploy screen."""
        super().__init__()
        self.config_manager = config_manager
        self.deployment_state = {}  # Track checkbox states

    def compose(self) -> ComposeResult:
        """Compose the deploy screen layout."""
        yield Vertical(
            Container(
                Static("🚀 Deployment Matrix", classes="section-title"),
                Horizontal(
                    Label("Scope:"),
                    Select(
                        [(s.value.title(), s.value) for s in Scope],
                        id="scope-select",
                    ),
                    Button("Apply Changes", id="btn-apply", variant="primary"),
                    Button("Refresh", id="btn-refresh"),
                    classes="toolbar",
                ),
                classes="header-section",
            ),
            Container(
                DataTable(id="deploy-table"),
                classes="table-section",
            ),
            Container(
                Static("Instructions", classes="section-title"),
                Label(
                    "• Use arrow keys to navigate\n"
                    "• Press Space to toggle deployment\n"
                    "• Select scope from dropdown\n"
                    "• Click Apply to save changes",
                    id="instructions",
                ),
                classes="help-section",
            ),
            classes="deploy-container",
        )

    def on_mount(self) -> None:
        """Called when the screen is mounted."""
        self.refresh_matrix()

    def refresh_matrix(self) -> None:
        """Refresh the deployment matrix."""
        table = self.query_one("#deploy-table", DataTable)
        table.clear(columns=True)
        
        # Get current scope
        select = self.query_one("#scope-select", Select)
        scope_value = select.value
        if scope_value == Select.BLANK:
            scope_value = Scope.GLOBAL.value
        scope = Scope(scope_value)
        
        # Add columns
        table.add_column("Server", key="server")
        for client_name in self.config_manager.adapters.keys():
            display_name = client_name.replace("-", " ").title()
            table.add_column(display_name, key=client_name)
        
        # Add rows
        servers = self.config_manager.list_servers()
        for server in servers:
            deployments = self.config_manager.get_deployments(server.id)
            
            # Build row data
            row_data = [server.friendly_name or server.name]
            
            for client_name in self.config_manager.adapters.keys():
                # Check if deployed to this client with this scope
                is_deployed = any(
                    d.client_name == client_name and d.scope == scope
                    for d in deployments
                )
                row_data.append("✓" if is_deployed else "")
                
                # Track state
                key = f"{server.id}_{client_name}_{scope.value}"
                self.deployment_state[key] = is_deployed
            
            table.add_row(*row_data, key=str(server.id))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id
        
        if button_id == "btn-apply":
            self.apply_changes()
        elif button_id == "btn-refresh":
            self.refresh_matrix()

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle scope selection change."""
        if event.select.id == "scope-select":
            self.refresh_matrix()

    def apply_changes(self) -> None:
        """Apply deployment changes."""
        select = self.query_one("#scope-select", Select)
        scope_value = select.value
        if scope_value == Select.BLANK:
            scope_value = Scope.GLOBAL.value
        scope = Scope(scope_value)
        changes_made = False
        
        # Process all deployment state changes
        for key, should_deploy in self.deployment_state.items():
            parts = key.split("_")
            server_id = UUID(parts[0])
            client_name = "_".join(parts[1:-1])  # Handle client names with underscores
            
            # Get current state
            deployments = self.config_manager.get_deployments(server_id)
            is_deployed = any(
                d.client_name == client_name and d.scope == scope
                for d in deployments
            )
            
            # Apply changes if needed
            if should_deploy and not is_deployed:
                self.config_manager.deploy_server(server_id, client_name, scope)
                changes_made = True
            elif not should_deploy and is_deployed:
                self.config_manager.undeploy_server(server_id, client_name, scope)
                changes_made = True
        
        if changes_made:
            self.app.notify("Deployment changes applied", severity="success")
        else:
            self.app.notify("No changes to apply", severity="information")