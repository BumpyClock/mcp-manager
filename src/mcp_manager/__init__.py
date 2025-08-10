"""MCP Manager - Centralized management of Model Context Protocol servers."""

__version__ = "1.0.0"
__author__ = "MCP Manager Team"

from mcp_manager.core.models import MCPServer, MCPClient, Deployment, Scope, ServerType

__all__ = ["MCPServer", "MCPClient", "Deployment", "Scope", "ServerType"]