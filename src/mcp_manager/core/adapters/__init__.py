"""Client adapters for different AI applications."""

from mcp_manager.core.adapters.base import BaseAdapter
from mcp_manager.core.adapters.claude_code import ClaudeCodeAdapter
from mcp_manager.core.adapters.claude_desktop import ClaudeDesktopAdapter
from mcp_manager.core.adapters.vscode import VSCodeAdapter

__all__ = [
    "BaseAdapter",
    "ClaudeCodeAdapter",
    "ClaudeDesktopAdapter",
    "VSCodeAdapter",
]