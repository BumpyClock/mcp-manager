"""CLI interface for MCP Manager using Typer."""

from pathlib import Path
from typing import List, Optional

import typer
from rich import print
from rich.console import Console
from rich.table import Table

from mcp_manager.core.config.manager import ConfigManager
from mcp_manager.core.models import MCPServer, Scope, ServerType

app = typer.Typer(
    name="mcp-manager",
    help="Centralized management of Model Context Protocol (MCP) servers",
    add_completion=False,
)
console = Console()


@app.command()
def tui():
    """Launch the TUI application."""
    from mcp_manager.tui.app import main
    main()


@app.command("add-server")
def add_server(
    name: str = typer.Option(..., "--name", "-n", help="Server name"),
    command: str = typer.Option(..., "--command", "-c", help="Server command"),
    args: Optional[List[str]] = typer.Option(None, "--arg", "-a", help="Server arguments"),
    type: str = typer.Option("stdio", "--type", "-t", help="Server type (stdio/http/sse)"),
    tags: Optional[List[str]] = typer.Option(None, "--tag", help="Server tags"),
):
    """Add a new MCP server."""
    config_manager = ConfigManager()
    
    try:
        server = MCPServer(
            name=name,
            command=command,
            args=args or [],
            type=ServerType(type),
            tags=tags or [],
        )
        
        server_id = config_manager.add_server(server)
        print(f"[green][+][/green] Server '{name}' added successfully (ID: {server_id})")
    except Exception as e:
        print(f"[red][x][/red] Failed to add server: {e}")
        raise typer.Exit(1)


@app.command("list-servers")
def list_servers(
    tag: Optional[str] = typer.Option(None, "--tag", help="Filter by tag"),
):
    """List all MCP servers."""
    config_manager = ConfigManager()
    
    filters = {"tags": tag} if tag else None
    servers = config_manager.list_servers(filters)
    
    if not servers:
        print("[yellow]No servers found[/yellow]")
        return
    
    table = Table(title="MCP Servers")
    table.add_column("Name", style="cyan")
    table.add_column("Command")
    table.add_column("Type")
    table.add_column("Tags")
    table.add_column("Deployments")
    
    for server in servers:
        deployments = config_manager.get_deployments(server.id)
        dep_count = len(deployments)
        tags_str = ", ".join(server.tags) if server.tags else "-"
        
        table.add_row(
            server.name,
            server.command,
            server.type.value,
            tags_str,
            str(dep_count),
        )
    
    console.print(table)


@app.command("delete-server")
def delete_server(
    name: str = typer.Argument(..., help="Server name to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Delete an MCP server."""
    config_manager = ConfigManager()
    
    server = config_manager.get_server_by_name(name)
    if not server:
        print(f"[red][x][/red] Server '{name}' not found")
        raise typer.Exit(1)
    
    if not force:
        confirm = typer.confirm(f"Are you sure you want to delete '{name}'?")
        if not confirm:
            print("[yellow]Cancelled[/yellow]")
            return
    
    config_manager.delete_server(server.id)
    print(f"[green][+][/green] Server '{name}' deleted successfully")


@app.command("deploy")
def deploy(
    server: str = typer.Option(..., "--server", "-s", help="Server name"),
    client: str = typer.Option(..., "--client", "-c", help="Client name"),
    scope: str = typer.Option("global", "--scope", help="Deployment scope"),
):
    """Deploy a server to a client."""
    config_manager = ConfigManager()
    
    server_obj = config_manager.get_server_by_name(server)
    if not server_obj:
        print(f"[red][x][/red] Server '{server}' not found")
        raise typer.Exit(1)
    
    try:
        config_manager.deploy_server(server_obj.id, client, Scope(scope))
        print(f"[green][+][/green] Deployed '{server}' to {client} ({scope})")
    except Exception as e:
        print(f"[red][x][/red] Deployment failed: {e}")
        raise typer.Exit(1)


@app.command("sync")
def sync(
    client: Optional[str] = typer.Option(None, "--client", "-c", help="Specific client to sync"),
    all: bool = typer.Option(False, "--all", "-a", help="Sync all clients"),
):
    """Synchronize configurations with clients."""
    config_manager = ConfigManager()
    
    if all or not client:
        print("Syncing all clients...")
        results = config_manager.sync_all()
        
        for client_name, result in results.items():
            if "error" in result:
                print(f"[red][x][/red] {client_name}: {result['error'][0]}")
            else:
                added = len(result.get("added", []))
                removed = len(result.get("removed", []))
                updated = len(result.get("updated", []))
                print(f"[green][+][/green] {client_name}: +{added} -{removed} ~{updated}")
    elif client:
        try:
            result = config_manager.sync_client(client)
            added = len(result.get("added", []))
            removed = len(result.get("removed", []))
            updated = len(result.get("updated", []))
            print(f"[green][+][/green] {client}: +{added} -{removed} ~{updated}")
        except Exception as e:
            print(f"[red][x][/red] Sync failed: {e}")
            raise typer.Exit(1)


@app.command("status")
def status():
    """Show overall system status."""
    config_manager = ConfigManager()
    
    servers = config_manager.list_servers()
    deployments = config_manager.get_deployments()
    
    print("\n[bold]MCP Manager Status[/bold]\n")
    print(f"Total Servers: {len(servers)}")
    print(f"Total Deployments: {len(deployments)}")
    print(f"Configured Clients: {len(config_manager.adapters)}")
    
    # Show client status
    print("\n[bold]Client Status:[/bold]")
    for client_name in config_manager.adapters:
        client_deps = [d for d in deployments if d.client_name == client_name]
        print(f"  - {client_name}: {len(client_deps)} servers")


@app.command("version")
def version():
    """Show version information."""
    from mcp_manager import __version__
    print(f"MCP Manager v{__version__}")


if __name__ == "__main__":
    app()