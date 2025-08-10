"""Deploy screen for MCP Manager TUI."""

from uuid import UUID
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Checkbox, DataTable, Label, Select, Static

from mcp_manager.core.config.manager import ConfigManager
from mcp_manager.core.models import Scope


class DeployScreen(Container):
    """Deployment matrix screen for managing server deployments."""

    BINDINGS = [
        Binding("space", "toggle", "Toggle", show=True),
        Binding("enter", "apply", "Apply", show=True),
        Binding("s", "change_scope", "Scope", show=True),
        Binding("r", "refresh", "Refresh", show=True),
        Binding("c", "open_clients", "Clients", show=False),
    ]

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
                persisted = any(
                    d.client_name == client_name and d.scope == scope
                    for d in deployments
                )
                key = f"{server.id}_{client_name}_{scope.value}"
                # Preserve any pending toggle; else use persisted
                current = self.deployment_state.get(key, persisted)
                self.deployment_state[key] = current
                row_data.append("✓" if current else "")
            
            table.add_row(*row_data, key=str(server.id))

    # No button handlers; rely on keybindings: Enter=Apply, r=Refresh, c=Clients
        
    # Key-bound actions
    def action_apply(self) -> None:
        try:
            self.app.set_status("Applying…")  # type: ignore[attr-defined]
        except Exception:
            pass
        self.apply_changes()
        try:
            self.app.set_status("Ready")  # type: ignore[attr-defined]
        except Exception:
            pass

    def action_refresh(self) -> None:
        try:
            self.app.set_status("Refreshing…")  # type: ignore[attr-defined]
        except Exception:
            pass
        self.refresh_matrix()
        try:
            self.app.set_status("Ready")  # type: ignore[attr-defined]
        except Exception:
            pass

    def action_change_scope(self) -> None:
        select = self.query_one("#scope-select", Select)
        values = [s.value for s in Scope]
        if select.value == Select.BLANK:
            current = values[0]
        else:
            current = select.value
        try:
            idx = values.index(current)  # type: ignore[arg-type]
        except ValueError:
            idx = 0
        next_val = values[(idx + 1) % len(values)]
        select.value = next_val
        self.refresh_matrix()

    def action_toggle(self) -> None:
        table = self.query_one("#deploy-table", DataTable)
        # Need a valid cell that is not the first column (server name)
        if getattr(table, "cursor_row", -1) < 0 or getattr(table, "cursor_column", 0) <= 0:
            return
        # Determine server and client from cursor position
        try:
            row_key = list(table.rows.keys())[table.cursor_row]
            server_id = UUID(str(row_key.value))
        except Exception:
            return

        client_names = list(self.config_manager.adapters.keys())
        client_col_index = table.cursor_column - 1
        if client_col_index < 0 or client_col_index >= len(client_names):
            return
        client_name = client_names[client_col_index]

        # Current scope
        select = self.query_one("#scope-select", Select)
        scope_value = select.value
        if scope_value == Select.BLANK:
            scope_value = Scope.GLOBAL.value
        scope = Scope(scope_value)

        key = f"{server_id}_{client_name}_{scope.value}"
        current = self.deployment_state.get(key, False)
        self.deployment_state[key] = not current
        # Re-render to reflect change
        self.refresh_matrix()

    def action_open_clients(self) -> None:
        # Open clients status modal
        try:
            from mcp_manager.tui.screens.clients import ClientsModal
            self.app.push_screen(ClientsModal(self.config_manager))
        except Exception:
            self.app.notify("Unable to open clients status", severity="error")

    # Selection sync from app
    def select_server_by_id(self, server_id_str: str) -> None:
        table = self.query_one("#deploy-table", DataTable)
        try:
            keys = list(table.rows.keys())
            target_index = next(i for i, k in enumerate(keys) if str(k.value) == server_id_str)
            table.cursor_row = target_index
        except StopIteration:
            pass

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle scope selection change."""
        if event.select.id == "scope-select":
            self.refresh_matrix()

    def apply_changes(self) -> None:
        """Apply deployment changes."""
        changes_made = False
        
        # Process all deployment state changes
        for key, should_deploy in self.deployment_state.items():
            parts = key.split("_")
            server_id = UUID(parts[0])
            scope_from_key = Scope(parts[-1])
            client_name = "_".join(parts[1:-1])  # Handle client names with underscores
            
            # Get current state
            deployments = self.config_manager.get_deployments(server_id)
            is_deployed = any(
                d.client_name == client_name and d.scope == scope_from_key
                for d in deployments
            )
            
            # Apply changes if needed
            if should_deploy and not is_deployed:
                self.config_manager.deploy_server(server_id, client_name, scope_from_key)
                changes_made = True
            elif not should_deploy and is_deployed:
                self.config_manager.undeploy_server(server_id, client_name, scope_from_key)
                changes_made = True
        
        if changes_made:
            self.app.notify("Deployment changes applied", severity="success")
        else:
            self.app.notify("No changes to apply", severity="information")
