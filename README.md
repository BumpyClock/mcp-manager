# MCP Manager

A powerful TUI/CLI application for centralized management of Model Context Protocol (MCP) servers across multiple AI client applications.

## Features

- 🎯 **Unified Management**: Manage MCP servers for Claude Code, Claude Desktop, and VS Code from one place
- 🖥️ **Rich TUI**: Beautiful terminal interface built with Textual
- ⚡ **CLI Support**: Full command-line interface for automation
- 🔄 **Bidirectional Sync**: Keep configurations synchronized across all clients
- 💾 **Automatic Backups**: Never lose configurations with automatic backup before changes
- 🏷️ **Tagging System**: Organize servers with tags
- 🌍 **Cross-Platform**: Works on Windows, macOS, and Linux
- 🔐 **Secure**: Environment variables and secrets handled safely

## Installation

### Using UV (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/mcp-manager.git
cd mcp-manager

# Install with UV
uv sync

# Run the TUI
uv run mcp-tui

# Or use the CLI
uv run mcp-manager --help
```

### Using pip

```bash
# Clone the repository
git clone https://github.com/yourusername/mcp-manager.git
cd mcp-manager

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the package
pip install -e .

# Run the TUI
mcp-tui

# Or use the CLI
mcp-manager --help
```

## Quick Start

### Launch the TUI

```bash
mcp-tui
```

Navigate with:
- **Tab**: Switch between panels
- **1-5**: Quick jump to tabs
- **↑↓**: Navigate lists
- **Enter**: Select/Confirm
- **Esc**: Cancel/Back
- **?** or **F1**: Help

### CLI Usage

#### Add a server
```bash
mcp-manager add-server --name filesystem --command npx --arg "-y" --arg "@modelcontextprotocol/server-filesystem"
```

#### List servers
```bash
mcp-manager list-servers
```

#### Deploy to a client
```bash
mcp-manager deploy --server filesystem --client claude-code --scope global
```

#### Sync configurations
```bash
mcp-manager sync --all
```

## Supported Clients

### Claude Code
- **Global**: `~/.claude/settings.json`
- **Project**: `./.claude/settings.json`
- Supports all scopes (global, user, project)

### Claude Desktop
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

### VS Code
- **Global**: `~/.vscode/mcp.json`
- **Project**: `./.vscode/mcp.json`
- Supports stdio, http, and sse transport types

## Project Structure

```
mcp-manager/
├── src/
│   └── mcp_manager/
│       ├── core/           # Core library (no UI dependencies)
│       │   ├── models/     # Pydantic data models
│       │   ├── adapters/   # Client-specific adapters
│       │   ├── config/     # Configuration management
│       │   └── sync/       # Synchronization engine
│       ├── tui/           # Textual TUI application
│       │   ├── screens/   # TUI screens
│       │   └── widgets/   # Custom widgets
│       └── cli/           # Typer CLI interface
├── tests/                 # Test suite
├── ai_docs/              # Architecture and PRD documents
└── pyproject.toml        # Project configuration
```

## Development

### Prerequisites

- Python 3.12+
- UV package manager (recommended) or pip

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/yourusername/mcp-manager.git
cd mcp-manager

# Install with development dependencies
uv sync --dev

# Run tests
uv run pytest

# Format code
uv run black src/ tests/

# Lint code
uv run ruff src/ tests/

# Type check
uv run mypy src/
```

### Architecture

The project follows a clean architecture pattern:

1. **Core Library**: Business logic with no UI dependencies
2. **Adapters**: Client-specific implementations
3. **TUI Layer**: Textual-based terminal interface
4. **CLI Layer**: Typer-based command-line interface

See `ai_docs/arch.md` for detailed architecture documentation.

## Configuration

MCP Manager stores its data in:
- **Database**: `~/.mcp-manager/mcp-manager.db`
- **Backups**: `~/.mcp-manager/backups/`
- **Logs**: `~/.mcp-manager/logs/`

## Keyboard Shortcuts

### Global
- `Ctrl+Q`: Quit
- `Ctrl+S`: Save
- `F1` or `?`: Help
- `Ctrl+R`: Refresh

### Navigation
- `Tab`: Switch panels
- `1-5`: Quick jump to tabs
- `↑↓`: Move selection
- `Enter`: Confirm
- `Esc`: Cancel

### Server Management
- `a`: Add server
- `e`: Edit server
- `d`: Delete server
- `p`: Deploy server

## Contributing

Contributions are welcome! Please read the contributing guidelines before submitting PRs.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Acknowledgments

Built with:
- [Textual](https://github.com/Textualize/textual) - TUI framework
- [Typer](https://github.com/tiangolo/typer) - CLI framework
- [Pydantic](https://github.com/pydantic/pydantic) - Data validation
- [Rich](https://github.com/Textualize/rich) - Terminal formatting

## Support

For issues, questions, or suggestions, please open an issue on GitHub.