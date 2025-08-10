"""Servers management screen for MCP Manager TUI."""

from typing import Optional
from uuid import UUID

from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Input, Label, Select, Static, TextArea

from mcp_manager.core.config.manager import ConfigManager
from mcp_manager.core.models import MCPServer, ServerType


class AddServerModal(ModalScreen):
    """Modal for adding/editing a server."""

    CSS = """
    AddServerModal {
        align: center middle;
    }

    #dialog {
        width: 60;
        height: auto;
        border: thick $background 80%;
        background: $surface;
        padding: 1 2;
    }

    Input, TextArea, Select {
        width: 100%;
        margin: 1 0;
    }

    .button-row {
        margin-top: 2;
        align: center middle;
    }
    """

    def __init__(self, config_manager: ConfigManager, server: Optional[MCPServer] = None):
        """Initialize the modal."""
        super().__init__()
        self.config_manager = config_manager
        self.server = server
        self.initial_type = server.type.value if server else ServerType.STDIO.value

    def compose(self) -> ComposeResult:
        """Compose the modal layout."""
        with Container(id="dialog"):
            yield Label("Add New Server" if not self.server else "Edit Server")
            
            yield Label("Name* (machine-friendly):")
            yield Input(
                placeholder="e.g., filesystem-server",
                id="input-name",
                value=self.server.name if self.server else "",
            )
            
            yield Label("Display Name:")
            yield Input(
                placeholder="e.g., File System Server",
                id="input-display-name",
                value=self.server.friendly_name if self.server else "",
            )
            
            yield Label("Command*:")
            yield Input(
                placeholder="e.g., npx",
                id="input-command",
                value=self.server.command if self.server else "",
            )
            
            yield Label("Arguments (one per line):")
            yield TextArea(
                "\n".join(self.server.args) if self.server else "",
                id="input-args",
            )
            
            yield Label("Type:")
            yield Select(
                [(t.value.upper(), t.value) for t in ServerType],
                id="select-type",
            )
            
            yield Label("Tags (comma-separated):")
            yield Input(
                placeholder="e.g., storage, local",
                id="input-tags",
                value=", ".join(self.server.tags) if self.server else "",
            )
            
            with Horizontal(classes="button-row"):
                yield Button("Save", variant="primary", id="btn-save")
                yield Button("Cancel", id="btn-cancel")

    def on_mount(self) -> None:
        """Set initial values after mounting."""
        if self.server:
            # Set the select value after mounting
            select = self.query_one("#select-type", Select)
            select.value = self.server.type.value
    
    @on(Button.Pressed, "#btn-save")
    def save_server(self) -> None:
        """Save the server."""
        name = self.query_one("#input-name", Input).value.strip()
        display_name = self.query_one("#input-display-name", Input).value.strip()
        command = self.query_one("#input-command", Input).value.strip()
        args_text = self.query_one("#input-args", TextArea).text
        type_value = self.query_one("#select-type", Select).value
        tags_text = self.query_one("#input-tags", Input).value

        if not name or not command:
            self.app.notify("Name and command are required", severity="error")
            return

        args = [arg.strip() for arg in args_text.split("\n") if arg.strip()]
        tags = [tag.strip() for tag in tags_text.split(",") if tag.strip()]

        if self.server:
            # Update existing server
            self.server.name = name
            self.server.friendly_name = display_name
            self.server.command = command
            self.server.args = args
            self.server.type = ServerType(type_value)
            self.server.tags = tags
            self.config_manager.update_server(self.server)
            self.app.notify(f"Server '{name}' updated", severity="information")
        else:
            # Create new server
            server = MCPServer(
                name=name,
                friendly_name=display_name,
                command=command,
                args=args,
                type=ServerType(type_value),
                tags=tags,
            )
            self.config_manager.add_server(server)
            self.app.notify(f"Server '{name}' added", severity="success")

        self.dismiss(True)

    @on(Button.Pressed, "#btn-cancel")
    def cancel(self) -> None:
        """Cancel the operation."""
        self.dismiss(False)


class ServersScreen(Container):
    """Servers management screen."""

    def __init__(self, config_manager: ConfigManager):
        """Initialize servers screen."""
        super().__init__()
        self.config_manager = config_manager
        self.selected_server_id: Optional[UUID] = None

    def compose(self) -> ComposeResult:
        """Compose the servers screen layout."""
        yield Vertical(
            Container(
                Static("🖥️ Server Management", classes="section-title"),
                Horizontal(
                    Button("Add Server [a]", id="btn-add", variant="primary"),
                    Button("Edit [e]", id="btn-edit"),
                    Button("Delete [d]", id="btn-delete", variant="error"),
                    Button("Deploy [p]", id="btn-deploy-server"),
                    classes="toolbar",
                ),
                classes="header-section",
            ),
            Container(
                DataTable(id="servers-table"),
                classes="table-section",
            ),
            Container(
                Static("Server Details", classes="section-title"),
                Label("Select a server to view details", id="server-details"),
                classes="details-section",
            ),
            classes="servers-container",
        )

    def on_mount(self) -> None:
        """Called when the screen is mounted."""
        self.refresh_table()

    def refresh_table(self) -> None:
        """Refresh the servers table."""
        table = self.query_one("#servers-table", DataTable)
        table.clear(columns=True)
        
        # Enable cursor mode for selection
        table.cursor_type = "row"
        
        # Add columns
        table.add_column("Name", key="name")
        table.add_column("Type", key="type")
        table.add_column("Tags", key="tags")
        table.add_column("Status", key="status")
        
        # Add rows
        servers = self.config_manager.list_servers()
        for server in servers:
            deployments = self.config_manager.get_deployments(server.id)
            status = "Deployed" if deployments else "Ready"
            tags = ", ".join(server.tags) if server.tags else "-"
            
            table.add_row(
                server.friendly_name or server.name,
                server.type.value,
                tags,
                status,
                key=str(server.id),
            )

    @on(DataTable.RowSelected)
    def on_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection."""
        if event.row_key:
            self.selected_server_id = UUID(str(event.row_key.value))
            self.update_details()
    
    @on(DataTable.RowHighlighted)
    def on_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        """Handle row highlighting (cursor movement)."""
        if event.row_key:
            self.selected_server_id = UUID(str(event.row_key.value))
            self.update_details()

    def update_details(self) -> None:
        """Update the server details panel."""
        if not self.selected_server_id:
            return

        server = self.config_manager.get_server(self.selected_server_id)
        if not server:
            return

        deployments = self.config_manager.get_deployments(server.id)
        
        details = f"""Name: {server.name}
Display: {server.friendly_name}
Command: {server.command}
Args: {', '.join(server.args) if server.args else 'None'}
Type: {server.type.value}
Tags: {', '.join(server.tags) if server.tags else 'None'}

Deployments:
"""
        if deployments:
            for dep in deployments:
                details += f"  • {dep.client_name} ({dep.scope.value})\n"
        else:
            details += "  • Not deployed\n"

        self.query_one("#server-details", Label).update(details)

    @on(Button.Pressed, "#btn-add")
    def add_server(self) -> None:
        """Open add server modal."""
        self.app.push_screen(AddServerModal(self.config_manager), self.on_modal_close)

    @on(Button.Pressed, "#btn-edit")
    def edit_server(self) -> None:
        """Edit selected server."""
        if not self.selected_server_id:
            self.app.notify("Please select a server to edit", severity="warning")
            return

        server = self.config_manager.get_server(self.selected_server_id)
        if server:
            self.app.push_screen(
                AddServerModal(self.config_manager, server), self.on_modal_close
            )

    @on(Button.Pressed, "#btn-delete")
    def delete_server(self) -> None:
        """Delete selected server."""
        if not self.selected_server_id:
            self.app.notify("Please select a server to delete", severity="warning")
            return

        server = self.config_manager.get_server(self.selected_server_id)
        if server:
            self.config_manager.delete_server(self.selected_server_id)
            self.app.notify(f"Server '{server.name}' deleted", severity="information")
            self.selected_server_id = None
            self.refresh_table()
            self.query_one("#server-details", Label).update("Select a server to view details")

    @on(Button.Pressed, "#btn-deploy-server")
    def deploy_server(self) -> None:
        """Deploy selected server."""
        if not self.selected_server_id:
            self.app.notify("Please select a server to deploy", severity="warning")
            return

        # Switch to deploy tab with selected server
        self.app.action_switch_tab("deploy")

    def on_modal_close(self, result: bool) -> None:
        """Handle modal close."""
        if result:
            self.refresh_table()