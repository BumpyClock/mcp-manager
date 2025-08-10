"""Settings screen for MCP Manager TUI."""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Checkbox, Input, Label, Select, Static

from mcp_manager.core.config.manager import ConfigManager


class SettingsScreen(Container):
    """Settings and preferences screen."""

    def __init__(self, config_manager: ConfigManager):
        """Initialize settings screen."""
        super().__init__()
        self.config_manager = config_manager

    def compose(self) -> ComposeResult:
        """Compose the settings screen layout."""
        yield Vertical(
            Container(
                Static("⚙️ Settings", classes="section-title"),
                classes="header-section",
            ),
            Container(
                Static("Behavior", classes="subsection-title"),
                Checkbox("Auto-sync on startup", id="auto-sync", value=True),
                Checkbox("Auto-backup before changes", id="auto-backup", value=True),
                Checkbox("Confirm destructive operations", id="confirm-destructive", value=True),
                classes="behavior-section",
            ),
            Container(
                Static("Backup", classes="subsection-title"),
                Horizontal(
                    Label("Retention days:"),
                    Input(value="30", id="retention-days", type="integer"),
                    classes="setting-row",
                ),
                classes="backup-section",
            ),
            Container(
                Static("UI Preferences", classes="subsection-title"),
                Horizontal(
                    Label("Theme:"),
                    Select(
                        [("Dark", "dark"), ("Light", "light"), ("High Contrast", "high-contrast")],
                        id="theme-select",
                    ),
                    classes="setting-row",
                ),
                Checkbox("Show hints", id="show-hints", value=True),
                Checkbox("Compact mode", id="compact-mode", value=False),
                classes="ui-section",
            ),
            Container(
                Horizontal(
                    Button("Save Settings", id="btn-save", variant="primary"),
                    Button("Reset to Defaults", id="btn-reset"),
                    classes="button-row",
                ),
                classes="actions-section",
            ),
            Container(
                Static("About", classes="subsection-title"),
                Label(
                    "MCP Manager v1.0.0\n"
                    "Centralized management of Model Context Protocol servers\n\n"
                    "Built with Python, Textual, and Pydantic\n"
                    "MIT License",
                    id="about-text",
                ),
                classes="about-section",
            ),
            classes="settings-container",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id
        
        if button_id == "btn-save":
            self.save_settings()
        elif button_id == "btn-reset":
            self.reset_settings()

    def save_settings(self) -> None:
        """Save current settings."""
        # In a real implementation, these would be saved to a config file
        # For now, just show a notification
        self.app.notify("Settings saved", severity="success")

    def reset_settings(self) -> None:
        """Reset settings to defaults."""
        # Reset UI elements to default values
        self.query_one("#auto-sync", Checkbox).value = True
        self.query_one("#auto-backup", Checkbox).value = True
        self.query_one("#confirm-destructive", Checkbox).value = True
        self.query_one("#retention-days", Input).value = "30"
        self.query_one("#theme-select", Select).value = "dark"
        self.query_one("#show-hints", Checkbox).value = True
        self.query_one("#compact-mode", Checkbox).value = False
        
        self.app.notify("Settings reset to defaults", severity="information")