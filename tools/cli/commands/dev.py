"""
Development environment commands for the multitenant SaaS starter project.

This module provides CLI commands to start and stop the development
environment, including Supabase and all dev servers in the apps/ directory.
"""

import subprocess
from pathlib import Path

import typer
from rich.console import Console

__all__ = [
    "app",
]

app = typer.Typer(
    name="dev",
    help="Development environment commands (start/stop dev servers)",
    add_completion=False,
)

console = Console()


def get_app_dirs():
    """Return a list of app directories in the apps/ directory."""
    apps_dir = Path(__file__).parent.parent.parent / "apps"
    if not apps_dir.exists():
        console.print("[red]apps/ directory not found.[/red]")
        raise typer.Exit(1)
    return [
        d
        for d in apps_dir.iterdir()
        if d.is_dir() and (d / "package.json").exists()
    ]


def run_pnpm_command(app_dir, command):
    """Run a pnpm command in the given app directory."""
    try:
        subprocess.run(
            ["pnpm", "run", command],
            cwd=app_dir,
            check=True,
        )
    except FileNotFoundError:
        console.print(
            "[red]Error: pnpm not found. Please install pnpm first.[/red]"
        )
        raise typer.Exit(1)
    except subprocess.CalledProcessError as e:
        console.print(
            f"[red]Error running 'pnpm run {command}' in {app_dir}: {e}[/red]"
        )
        raise typer.Exit(1)


@app.command("start")
def start():
    """Start the development environment (Supabase and all app dev servers)."""
    console.print(
        "🚀 [bold white]Starting servers in [bold blue]development mode...[/bold blue][/bold white]"
    )

    # Run 'pnpm run dev:kill' for all apps before starting
    app_dirs = get_app_dirs()
    for app_dir in app_dirs:
        console.print(
            f"🔪 [bold white]Killing dev servers in [bold blue]{app_dir.name}[/bold blue]...[/bold white]"
        )
        run_pnpm_command(app_dir, "dev:kill")

    # Start Supabase
    console.print("📊 [bold yellow]Starting Supabase...[/bold yellow]")
    try:
        subprocess.run(
            ["supabase", "start"],
            check=True,
        )
        console.print(
            "✅ [bold cyan]Supabase started successfully[/bold cyan]"
        )
    except FileNotFoundError:
        console.print(
            "[red]Error: supabase CLI not found. Please install supabase CLI first.[/red]"
        )
        raise typer.Exit(1)
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error starting Supabase: {e}[/red]")
        raise typer.Exit(1)

    # Start dev servers for all apps
    for app_dir in app_dirs:
        console.print(
            f"🔄 [bold orange]Starting dev server in [bold blue]{app_dir.name}[/bold blue]...[/bold orange]"
        )
        try:
            run_pnpm_command(app_dir, "dev")
            console.print(
                f"✅ [bold green]Dev server started in {app_dir.name}[/bold green]"
            )
        except typer.Exit:
            # Already handled error message and exit
            raise
        except Exception as e:
            console.print(
                f"[red]Error starting dev server in {app_dir.name}: {e}[/red]"
            )
            raise typer.Exit(1)


@app.command("stop")
def stop():
    """Stop the development environment (Supabase and all app dev servers)."""
    console.print(
        "🛑 [bold white]Stopping development environment...[/bold white]"
    )

    # Run 'pnpm run dev:kill' for all apps
    app_dirs = get_app_dirs()
    for app_dir in app_dirs:
        console.print(
            f"🔪 [bold white]Killing dev servers in [bold blue]{app_dir.name}[/bold blue]...[/bold white]"
        )
        run_pnpm_command(app_dir, "dev:kill")

    # Stop Supabase
    console.print("📊 [bold yellow]Stopping Supabase...[/bold yellow]")
    try:
        subprocess.run(
            ["supabase", "stop"],
            check=True,
        )
        console.print(
            "✅ [bold cyan]Supabase stopped successfully[/bold cyan]"
        )
    except FileNotFoundError:
        console.print(
            "[red]Error: supabase CLI not found. Please install supabase CLI first.[/red]"
        )
        raise typer.Exit(1)
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error stopping Supabase: {e}[/red]")
        raise typer.Exit(1)
