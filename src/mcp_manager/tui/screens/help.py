"""Help screen for MCP Manager TUI."""

from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static


class HelpScreen(ModalScreen):
    """Help screen showing keyboard shortcuts and usage."""

    CSS = """
    HelpScreen {
        align: center middle;
    }

    #help-dialog {
        width: 70;
        height: 80%;
        border: thick $background 80%;
        background: $surface;
        padding: 1 2;
        overflow-y: auto;
    }

    .help-section {
        margin: 1 0;
    }

    .help-title {
        text-style: bold;
        color: $primary;
    }

    .help-key {
        color: $success;
        text-style: bold;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the help screen layout."""
        with Container(id="help-dialog"):
            yield Vertical(
                Static("📚 MCP Manager Help", classes="help-title"),
                
                Container(
                    Static("Global Shortcuts", classes="subsection-title"),
                    Label("Ctrl+Q - Quit application"),
                    Label("Ctrl+S - Save changes"),
                    Label("F1 or ? - Show this help"),
                    Label("Ctrl+R - Refresh current view"),
                    Label("Tab - Navigate between panels"),
                    Label("1-5 - Quick jump to tabs"),
                    classes="help-section",
                ),
                
                Container(
                    Static("Navigation", classes="subsection-title"),
                    Label("↑/↓ - Move selection up/down"),
                    Label("←/→ - Move between columns"),
                    Label("Page Up/Down - Scroll pages"),
                    Label("Home/End - Jump to first/last item"),
                    Label("Enter - Select/Confirm"),
                    Label("Esc - Cancel/Back"),
                    classes="help-section",
                ),
                
                Container(
                    Static("Server Management", classes="subsection-title"),
                    Label("a - Add new server"),
                    Label("e - Edit selected server"),
                    Label("d - Delete selected server"),
                    Label("p - Deploy selected server"),
                    Label("Space - Toggle selection"),
                    classes="help-section",
                ),
                
                Container(
                    Static("Deployment", classes="subsection-title"),
                    Label("Use arrow keys to navigate the matrix"),
                    Label("Space - Toggle deployment"),
                    Label("s - Change scope"),
                    Label("Enter - Apply changes"),
                    classes="help-section",
                ),
                
                Container(
                    Static("Client Management", classes="subsection-title"),
                    Label("r - Refresh client status"),
                    Label("s - Sync selected client"),
                    Label("a - Sync all clients"),
                    Label("v - View client details"),
                    classes="help-section",
                ),
                
                Container(
                    Static("Tips", classes="subsection-title"),
                    Label("• MCP servers are stored locally in a SQLite database"),
                    Label("• Configurations are automatically backed up before changes"),
                    Label("• Use tags to organize your servers"),
                    Label("• Different scopes (global/project) allow flexible deployment"),
                    Label("• Sync regularly to keep configurations in sync"),
                    classes="help-section",
                ),
                
                Button("Close [Esc]", id="btn-close"),
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "btn-close":
            self.dismiss()

    def on_key(self, event) -> None:
        """Handle key press."""
        if event.key == "escape":
            self.dismiss()