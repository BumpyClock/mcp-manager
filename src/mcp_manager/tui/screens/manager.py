"""Unified Manager screen with a single table for overview + management + deployment."""

from textual.app import ComposeResult
from uuid import UUID
from textual import on
from textual.binding import Binding
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import DataTable, Label, Select, Static

from mcp_manager.core.config.manager import ConfigManager
from mcp_manager.tui.screens.servers import AddServerModal
from mcp_manager.tui.screens.clients import ClientsModal
from mcp_manager.core.models import Scope, MCPServer, ServerType


class ManagerScreen(Container):
    """Single table view combining overview, server management, and deployment matrix."""

    BINDINGS = [
        Binding("a", "add", "Add", show=True),
        Binding("e", "edit", "Edit", show=True),
        Binding("x", "delete", "Delete", show=True),
        Binding("space", "toggle", "Toggle", show=True),
        Binding("s", "change_scope", "Scope", show=True),
        Binding("enter", "apply", "Apply", show=True),
        Binding("r", "refresh", "Refresh", show=True),
        Binding("c", "open_clients", "Clients", show=False),
        Binding("t", "toggle_meta", "Cols", show=True),
    ]

    def __init__(self, config_manager: ConfigManager):
        super().__init__()
        self.config_manager = config_manager
        self.deployment_state: dict[str, bool] = {}
        self.selected_server_id: UUID | None = None
        self.show_meta_columns: bool = True

    def compose(self) -> ComposeResult:
        with Vertical(id="manager-root"):
            # Compact, one-line filter bar
            with Horizontal(id="filter-bar"):
                yield Label("Scope")
                yield Select([(s.value.title(), s.value) for s in Scope], id="scope-select")
                yield Label("Type")
                yield Select([("All", "all")] + [(t.value.upper(), t.value) for t in ServerType], id="type-filter")
                yield Label("Tag")
                # Tag options are populated on mount (can be empty initially)
                yield Select([("All", "all")], id="tag-filter")
                # Stats at the end of the row
                yield Label("", id="stats-label")
            # Unified table
            yield DataTable(id="manager-table")

    def on_mount(self) -> None:
        # Populate tag filter options based on current servers
        tags = sorted({tag for s in self.config_manager.list_servers() for tag in s.tags})
        try:
            tag_select = self.query_one("#tag-filter", Select)
            tag_select.set_options([("All", "all")] + [(t, t) for t in tags])
        except Exception:
            pass
        self.refresh_table()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id in {"scope-select", "type-filter", "tag-filter"}:
            self.refresh_table()

    def refresh_active(self) -> None:
        self.refresh_table()

    # External selection sync
    def select_server_by_id(self, server_id_str: str, target_inner: str | None = None) -> None:
        # In unified table, selection sync just focuses row
        table = self.query_one("#manager-table", DataTable)
        try:
            keys = list(table.rows.keys())
            target_index = next(i for i, k in enumerate(keys) if str(k.value) == server_id_str)
            table.cursor_row = target_index
        except StopIteration:
            pass

    def _current_scope(self) -> Scope:
        select = self.query_one("#scope-select", Select)
        val = select.value
        if val == Select.BLANK or val is None:
            val = Scope.GLOBAL.value
        return Scope(val)

    def _current_type_filter(self) -> str:
        try:
            sel = self.query_one("#type-filter", Select)
            val = sel.value
            if val == Select.BLANK or val is None:
                return "all"
            return str(val)
        except Exception:
            return "all"

    def _current_tag_filter(self) -> str:
        try:
            sel = self.query_one("#tag-filter", Select)
            val = sel.value
            if val == Select.BLANK or val is None:
                return "all"
            return str(val)
        except Exception:
            return "all"

    def refresh_table(self) -> None:
        table = self.query_one("#manager-table", DataTable)
        table.clear(columns=True)
        table.cursor_type = "row"  # Changed from "cell" to "row" for better selection
        scope = self._current_scope()

        # Columns: Server, Type, [clients...], Tags
        table.add_column("Server", key="server", width=24)
        if self.show_meta_columns:
            table.add_column("Type", key="type", width=8)
        client_names = list(self.config_manager.adapters.keys())
        for client in client_names:
            table.add_column(client.replace("-", " ").title(), key=client, width=14)
        if self.show_meta_columns:
            table.add_column("Tags", key="tags", width=20)

        servers = self.config_manager.list_servers()
        # Apply filters
        type_filter = self._current_type_filter()
        tag_filter = self._current_tag_filter()
        if type_filter != "all":
            servers = [s for s in servers if s.type.value == type_filter]
        if tag_filter != "all":
            servers = [s for s in servers if tag_filter in s.tags]
        total_deployments = 0
        deployed_clients: set[str] = set()
        self.deployment_state = {}
        pending_count = 0

        for server in servers:
            deployments = self.config_manager.get_deployments(server.id)
            row = [server.friendly_name or server.name]
            if self.show_meta_columns:
                row.append(server.type.value)
            for client in client_names:
                persisted = any(d.client_name == client and d.scope == scope for d in deployments)
                key = f"{server.id}_{client}_{scope.value}"
                current = self.deployment_state.get(key, persisted)
                self.deployment_state[key] = current
                if current:
                    total_deployments += 1
                    deployed_clients.add(client)
                # Pending marker if toggled differs from persisted
                if current != persisted:
                    pending_count += 1
                    cell = "✓•" if current else "•"
                else:
                    cell = "✓" if current else ""
                row.append(cell)
            if self.show_meta_columns:
                tags = ", ".join(server.tags[:2]) if server.tags else "-"
                if server.tags and len(server.tags) > 2:
                    tags += f" (+{len(server.tags)-2})"
                row.append(tags)
            table.add_row(*row, key=str(server.id))

        # Update stats label
        stats = f"Servers: {len(servers)} | Deployments: {total_deployments} | Clients Active: {len(deployed_clients)}"
        if pending_count:
            stats += f" | Pending: {pending_count}"
        self.query_one("#stats-label", Label).update(stats)
        
        # Restore selection if possible, or select first row if we have servers
        if servers:
            if self.selected_server_id:
                try:
                    keys = list(table.rows.keys())
                    idx = next(i for i, k in enumerate(keys) if str(k.value) == str(self.selected_server_id))
                    table.cursor_row = idx
                    # Ensure selected_server_id is still valid after restore
                    self.selected_server_id = UUID(str(keys[idx].value))
                except (StopIteration, IndexError):
                    # If previous selection not found, select first row
                    if table.row_count > 0:
                        table.cursor_row = 0
                        keys = list(table.rows.keys())
                        if keys:
                            self.selected_server_id = UUID(str(keys[0].value))
            else:
                # No previous selection, select first row if available
                if table.row_count > 0:
                    table.cursor_row = 0
                    keys = list(table.rows.keys())
                    if keys:
                        self.selected_server_id = UUID(str(keys[0].value))

    # Key-bound actions
    def action_add(self) -> None:
        self.app.push_screen(AddServerModal(self.config_manager), self._on_modal_close)

    def action_edit(self) -> None:
        if not self._ensure_selected():
            return
        server = self.config_manager.get_server(self.selected_server_id)  # type: ignore[arg-type]
        if server:
            self.app.push_screen(AddServerModal(self.config_manager, server), self._on_modal_close)

    def action_delete(self) -> None:
        if not self._ensure_selected():
            return
        srv = self.config_manager.get_server(self.selected_server_id)  # type: ignore[arg-type]
        if srv:
            self.config_manager.delete_server(self.selected_server_id)  # type: ignore[arg-type]
            self.app.notify(f"Server '{srv.name}' deleted", severity="information")
            self.refresh_table()

    def action_toggle(self) -> None:
        table = self.query_one("#manager-table", DataTable)
        # For row cursor mode, we need to handle toggling differently
        # You might want to prompt which client to toggle or cycle through them
        if not self._ensure_selected():
            return
        
        # Since we're in row mode, let's toggle the first client as default
        # Or you could show a modal to select which client to toggle
        client_names = list(self.config_manager.adapters.keys())
        if not client_names:
            return
            
        # For now, toggle the first client (you may want to enhance this)
        client_name = client_names[0]
        scope = self._current_scope()
        key = f"{self.selected_server_id}_{client_name}_{scope.value}"
        self.deployment_state[key] = not self.deployment_state.get(key, False)
        self.refresh_table()
        self.app.notify(f"Toggled {client_name} deployment", severity="information")

    def action_change_scope(self) -> None:
        select = self.query_one("#scope-select", Select)
        values = [s.value for s in Scope]
        current = select.value if select.value != Select.BLANK else values[0]
        try:
            idx = values.index(current)  # type: ignore[arg-type]
        except ValueError:
            idx = 0
        select.value = values[(idx + 1) % len(values)]
        self.refresh_table()

    def action_apply(self) -> None:
        scope = self._current_scope()
        changes = False
        for key, should in self.deployment_state.items():
            parts = key.split("_")
            server_id = UUID(parts[0])
            client_name = "_".join(parts[1:-1])
            scope_from_key = Scope(parts[-1])
            if scope_from_key != scope:
                continue
            deployments = self.config_manager.get_deployments(server_id)
            is_deployed = any(d.client_name == client_name and d.scope == scope for d in deployments)
            if should and not is_deployed:
                self.config_manager.deploy_server(server_id, client_name, scope)
                changes = True
            elif not should and is_deployed:
                self.config_manager.undeploy_server(server_id, client_name, scope)
                changes = True
        if changes:
            self.app.notify("Deployment changes applied", severity="success")
        else:
            self.app.notify("No changes to apply", severity="information")
        self.refresh_table()

    def action_refresh(self) -> None:
        self.refresh_table()

    def action_toggle_meta(self) -> None:
        """Toggle visibility of Type/Tags columns."""
        self.show_meta_columns = not self.show_meta_columns
        self.refresh_table()

    def action_open_clients(self) -> None:
        self.app.push_screen(ClientsModal(self.config_manager))

    # Row selection tracking
    @on(DataTable.RowHighlighted)
    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        if event.row_key:
            try:
                self.selected_server_id = UUID(str(event.row_key.value))
                self.app.set_selected_server(self.selected_server_id)  # type: ignore[attr-defined]
            except Exception:
                pass

    @on(DataTable.RowSelected)
    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        if event.row_key:
            try:
                self.selected_server_id = UUID(str(event.row_key.value))
                self.app.set_selected_server(self.selected_server_id)  # type: ignore[attr-defined]
            except Exception:
                pass

    def _ensure_selected(self) -> bool:
        if not self.selected_server_id:
            self.app.notify("Please select a server first", severity="warning")
            return False
        return True

    def _on_modal_close(self, result: bool) -> None:
        if result:
            self.refresh_table()
