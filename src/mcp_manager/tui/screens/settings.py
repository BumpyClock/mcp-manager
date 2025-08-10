"""Settings screen for MCP Manager TUI."""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Checkbox, Input, Label, Select, Static
from textual.binding import Binding

from mcp_manager.core.config.manager import ConfigManager


class SettingsScreen(Container):
    """Settings and preferences screen."""

    def __init__(self, config_manager: ConfigManager):
        """Initialize settings screen."""
        super().__init__()
        self.config_manager = config_manager

    BINDINGS = [
        Binding("shift+r", "reset_settings", "Reset"),
        Binding("ctrl+s", "save_settings", "Save", show=False),
    ]

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

    def on_mount(self) -> None:
        """Load existing settings from storage into controls."""
        get = self.config_manager.get_setting
        self.query_one("#auto-sync", Checkbox).value = bool(get("auto-sync", True))
        self.query_one("#auto-backup", Checkbox).value = bool(get("auto-backup", True))
        self.query_one("#confirm-destructive", Checkbox).value = bool(get("confirm-destructive", True))
        self.query_one("#retention-days", Input).value = str(get("retention-days", 30))
        self.query_one("#theme-select", Select).value = str(get("theme", "dark"))
        self.query_one("#show-hints", Checkbox).value = bool(get("show-hints", True))
        self.query_one("#compact-mode", Checkbox).value = bool(get("compact-mode", False))

    # No buttons; rely on Ctrl+S and Shift+R

    def action_save_settings(self) -> None:
        """Save current settings to persistent storage."""
        values = {
            "auto-sync": self.query_one("#auto-sync", Checkbox).value,
            "auto-backup": self.query_one("#auto-backup", Checkbox).value,
            "confirm-destructive": self.query_one("#confirm-destructive", Checkbox).value,
            "retention-days": int(self.query_one("#retention-days", Input).value or 30),
            "theme": self.query_one("#theme-select", Select).value or "dark",
            "show-hints": self.query_one("#show-hints", Checkbox).value,
            "compact-mode": self.query_one("#compact-mode", Checkbox).value,
        }
        self.config_manager.set_settings(values)
        # Apply compact mode immediately
        try:
            self.app.set_compact_mode(values["compact-mode"])  # type: ignore[attr-defined]
        except Exception:
            pass
        # Simple acknowledgment
        self.app.notify("Settings saved", severity="success")

    def action_reset_settings(self) -> None:
        """Reset settings to defaults."""
        # Reset UI elements to default values
        self.query_one("#auto-sync", Checkbox).value = True
        self.query_one("#auto-backup", Checkbox).value = True
        self.query_one("#confirm-destructive", Checkbox).value = True
        self.query_one("#retention-days", Input).value = "30"
        self.query_one("#theme-select", Select).value = "dark"
        self.query_one("#show-hints", Checkbox).value = True
        self.query_one("#compact-mode", Checkbox).value = False
        
        # Persist defaults
        self.config_manager.set_settings(
            {
                "auto-sync": True,
                "auto-backup": True,
                "confirm-destructive": True,
                "retention-days": 30,
                "theme": "dark",
                "show-hints": True,
                "compact-mode": False,
            }
        )
        try:
            self.app.set_compact_mode(False)  # type: ignore[attr-defined]
        except Exception:
            pass
        self.app.notify("Settings reset to defaults", severity="information")
