# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MCP Manager is a centralized management tool for Model Context Protocol (MCP) servers across multiple AI client applications (Claude Code, Claude Desktop, and VS Code). It provides both a Terminal User Interface (TUI) using Textual and a Command Line Interface (CLI) using Typer.

## Development Commands

### Setup and Installation
```bash
# Install with UV (recommended)
uv sync

# Install with pip
pip install -e .

# Install development dependencies
uv sync --all-extras
# or
pip install -e ".[dev]"
```

### Running the Application
```bash
# Run TUI
mcp-tui

# Run CLI
mcp-manager --help

# Run with UV
uv run mcp-tui
uv run mcp-manager --help
```

### Testing
```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=mcp_manager --cov-report=html

# Run specific test file
uv run pytest tests/test_specific.py

# Run with verbose output
uv run pytest -v
```

### Code Quality
```bash
# Format code
uv run black src tests

# Lint code
uv run ruff check src tests

# Type check
uv run mypy src

# Fix linting issues
uv run ruff check --fix src tests

# Run all quality checks
uv run black src tests && uv run ruff check src tests && uv run mypy src
```

### Building and Distribution
```bash
# Build package
uv build

# Build wheel only
uv build --wheel

# Install locally for testing
uv pip install dist/mcp_manager-*.whl
```

## Architecture Overview

### Clean Architecture Layers

```
┌─────────────────────────────────────┐
│         Presentation Layer          │
│     (TUI/CLI - User Interface)      │
├─────────────────────────────────────┤
│        Application Layer            │
│    (Use Cases & Orchestration)      │
├─────────────────────────────────────┤
│          Domain Layer               │
│      (Models & Business Logic)      │
├─────────────────────────────────────┤
│       Infrastructure Layer          │
│   (Storage, Adapters, External)     │
└─────────────────────────────────────┘
```

### Key Components

1. **Core Module** (`src/mcp_manager/core/`)
   - `models/` - Pydantic data models for MCPServer, MCPClient, and Deployment
   - `config/` - ConfigManager and SQLite storage backend
   - `adapters/` - Client-specific adapter implementations

2. **TUI Module** (`src/mcp_manager/tui/`)
   - `app.py` - Main Textual application with screen navigation
   - `screens/` - Individual screens for different features
   - Uses reactive bindings and message passing

3. **CLI Module** (`src/mcp_manager/cli/`)
   - `main.py` - Typer-based CLI with commands for all operations
   - Async command support with asyncio integration

### Data Flow

```
User Input → TUI/CLI → ConfigManager → Storage/Adapters → Client Configs
                            ↓
                      Domain Models
                      (Validation)
```

## Core Data Models

### MCPServer
```python
class MCPServer(BaseModel):
    name: str  # Unique identifier
    command: str  # Executable command
    args: List[str] = []
    env: Dict[str, Any] = {}
    env_file: Optional[str] = None
    tags: List[str] = []
    created_at: datetime
    updated_at: datetime
```

### MCPClient
```python
class MCPClient(BaseModel):
    name: str  # claude-code, claude-desktop, vscode
    config_path: Path
    status: str  # active, inactive, error
    deployed_servers: Dict[str, List[str]]  # scope -> server names
```

### Deployment
```python
class Deployment(BaseModel):
    server_name: str
    client_name: str
    status: str  # deployed, pending, error
    scope: str  # global, user, project
    deployed_at: datetime
```

## Technical Decisions

1. **Textual for TUI**: Provides rich, reactive terminal interfaces with CSS-like styling
2. **Pydantic Models**: Type-safe data validation and serialization
3. **SQLite Storage**: Lightweight, file-based database with async support
4. **Adapter Pattern**: Extensible client support without modifying core logic
5. **UV Package Manager**: Fast, modern Python package management
6. **Async Architecture**: Non-blocking I/O for file operations and database queries

## Common Development Workflows

### Adding a New Server
```python
# In ConfigManager
await config_manager.add_server(
    name="my-server",
    command="node",
    args=["path/to/server.js"],
    env={"API_KEY": "secret"},
    tags=["development", "ai"]
)
```

### Deploying to Clients
```python
# Deploy to specific client with scope
await config_manager.deploy_to_client(
    server_names=["my-server"],
    client_name="claude-code",
    scope="user"  # or "global", "project"
)
```

### Syncing Changes
```python
# Sync all changes from clients to storage
changes = await config_manager.sync_all()
# Returns: {"claude-code": {"added": [...], "updated": [...], "removed": [...]}}
```

## TUI Navigation

### Global Keybindings
- `F1-F6`: Navigate between screens
- `q`: Quit application (with confirmation)
- `ctrl+c`: Force quit
- `?`: Show help/keybindings
- `Tab`/`Shift+Tab`: Navigate between widgets

### Screen-Specific Keys
- **Servers Screen**: `a` (add), `e` (edit), `d` (delete), `t` (tag filter)
- **Deploy Screen**: `Space` (toggle), `Enter` (deploy), `s` (select scope)
- **Dashboard**: Auto-refreshes every 5 seconds

## Client Configuration Paths

### Claude Code
- **macOS/Linux**: `~/.config/claude-code/applications.json`
- **Windows**: `%APPDATA%\claude-code\applications.json`

### Claude Desktop  
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

### VS Code
- Settings path varies by platform, uses VS Code's settings.json

## Development Guidelines

### Code Style
- Black formatter with 100 char line length
- Ruff linter with Python 3.12 target
- Type hints required (mypy strict mode)
- Async functions for I/O operations

### Testing Strategy
- Unit tests for models and core logic
- Integration tests for adapters
- Mock external dependencies (file system, VS Code)
- Use pytest fixtures for test data

### Error Handling
- Use custom exceptions in `core/exceptions.py`
- Graceful degradation for client errors
- User-friendly error messages in TUI/CLI
- Automatic backups before destructive operations

### Performance Targets
- TUI startup < 100ms
- Screen transitions < 50ms
- Sync operations < 1s for typical configs
- Support 100+ servers without degradation

## Important Architecture Patterns

### 1. Adapter Interface
All client adapters must implement:
```python
async def read_config() -> Dict[str, Any]
async def write_config(config: Dict[str, Any]) -> None
async def deploy_server(server: MCPServer, scope: str) -> None
async def remove_server(server_name: str, scope: str) -> None
```

### 2. Reactive Bindings (TUI)
Textual's reactive attributes automatically update UI:
```python
selected_servers = reactive(set())  # UI updates when modified
filter_text = reactive("")  # Triggers re-filtering on change
```

### 3. Message Passing (TUI)
Screens communicate via messages:
```python
class ServerSelected(Message):
    def __init__(self, server_name: str): ...

# Post from any widget
self.post_message(ServerSelected("my-server"))
```

### 4. Scope Management
Deploy servers at different levels:
- **Global**: All users on the system
- **User**: Current user only (default)
- **Project**: VS Code workspace-specific

### 5. Conflict Resolution
When syncing, local state takes precedence:
1. Import new servers from clients
2. Update existing servers
3. Preserve local tags and metadata
4. Skip servers marked for deletion

## Database Schema

Located at `~/.mcp-manager/mcp-manager.db`:
- **servers** table: All registered MCP servers
- **clients** table: Client application configurations  
- **deployments** table: Server-client relationships
- **tags** table: Server categorization
- Automatic backups in `~/.mcp-manager/backups/`

## Environment Variable Handling

Servers can use environment variables via:
1. Direct `env` dict in server config
2. `.env` file path in `env_file` field
3. System environment variables (inherited)

Priority: env dict > env_file > system env

## Debugging Tips

1. Enable debug logging: `TEXTUAL_DEBUG=1 mcp-tui`
2. Check logs in `~/.mcp-manager/logs/`
3. Use `--dry-run` flag for CLI operations
4. Inspect SQLite directly: `sqlite3 ~/.mcp-manager/mcp-manager.db`
5. VS Code adapter issues: Check VS Code's output panel