#!/usr/bin/env python3
"""
Workspace administration commands for project management.

This module provides CLI commands for managing workspace initialization,
including database setup and environment file management across all apps.
"""

import shutil
import subprocess
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .db import init as db_init
from .db import is_supabase_running
from .db import start as db_start
from .db import stop as db_stop

__all__ = [
    "app",
]

app = typer.Typer(
    name="workspace",
    help="Workspace administration commands for project management",
    add_completion=False,
)
console = Console()


def clean_workspace() -> None:
    """Clean workspace by removing build artifacts and lock files."""
    console.print("🧹 [bold blue]Cleaning workspace...[/bold blue]")

    root_path = Path(".")

    # Patterns to clean
    patterns_to_clean = [
        ".next",
        ".turbo",
        ".venv",
        "node_modules",
        "pnpm-lock.yaml",
        "uv.lock",
    ]

    cleaned_items = []

    # Clean from root and all subdirectories
    for pattern in patterns_to_clean:
        # Clean from root
        root_item = root_path / pattern
        if root_item.exists():
            if root_item.is_dir():
                shutil.rmtree(root_item)
                console.print(f"🗑️  Removed directory: {root_item}")
            else:
                root_item.unlink()
                console.print(f"🗑️  Removed file: {root_item}")
            cleaned_items.append(str(root_item))

        # Clean from all subdirectories recursively
        for item in root_path.rglob(pattern):
            if item.exists() and item != root_item:
                try:
                    if item.is_dir():
                        shutil.rmtree(item)
                        console.print(f"🗑️  Removed directory: {item}")
                    else:
                        item.unlink()
                        console.print(f"🗑️  Removed file: {item}")
                    cleaned_items.append(str(item))
                except Exception as e:
                    console.print(
                        f"⚠️  [yellow]Warning: Could not remove {item}: {e}[/yellow]"
                    )

    if not cleaned_items:
        console.print("✅ Workspace already clean")
    else:
        console.print(
            f"✅ [bold green]Cleaned {len(cleaned_items)} items[/bold green]"
        )


def install_dependencies() -> None:
    """Install dependencies using pnpm and uv."""
    console.print("📦 [bold blue]Installing dependencies...[/bold blue]")

    # Run pnpm install
    console.print("📦 Running pnpm install...")
    try:
        subprocess.run(
            ["pnpm", "install"], check=True, capture_output=True, text=True
        )
        console.print("✅ pnpm install completed successfully")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error running pnpm install: {e}[/red]")
        if e.stdout:
            console.print(f"[red]stdout: {e.stdout}[/red]")
        if e.stderr:
            console.print(f"[red]stderr: {e.stderr}[/red]")
        raise typer.Exit(1)
    except FileNotFoundError:
        console.print(
            "[red]Error: pnpm not found. Please install pnpm first.[/red]"
        )
        raise typer.Exit(1)

    # Run uv sync
    console.print("📦 Running uv sync...")
    try:
        subprocess.run(
            ["uv", "sync"], check=True, capture_output=True, text=True
        )
        console.print("✅ uv sync completed successfully")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error running uv sync: {e}[/red]")
        if e.stdout:
            console.print(f"[red]stdout: {e.stdout}[/red]")
        if e.stderr:
            console.print(f"[red]stderr: {e.stderr}[/red]")
        raise typer.Exit(1)
    except FileNotFoundError:
        console.print(
            "[red]Error: uv not found. Please install uv first.[/red]"
        )
        raise typer.Exit(1)


def copy_env_example_to_development(app_path: Path) -> bool:
    """Copy .env.local.example to .env.development.local for a specific app."""
    env_example = app_path / ".env.local.example"
    env_development = app_path / ".env.development.local"

    if not env_example.exists():
        console.print(f"⚠️  [yellow]Warning: {env_example} not found[/yellow]")
        return False

    if env_development.exists():
        console.print(f"✅ {env_development} already exists")
        return True

    try:
        shutil.copy2(env_example, env_development)
        console.print(f"✅ Created {env_development} from {env_example}")
        return True
    except Exception as e:
        console.print(
            f"[red]Error copying {env_example} to {env_development}: {e}[/red]"
        )
        return False


def setup_app_env_files() -> list[Path]:
    """Setup .env.development.local files for all apps."""
    apps_dir = Path("apps")
    created_files = []

    if not apps_dir.exists():
        console.print(
            f"⚠️  [yellow]Warning: {apps_dir} directory not found[/yellow]"
        )
        return created_files

    # Find all app directories
    app_dirs = [
        d
        for d in apps_dir.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    ]

    if not app_dirs:
        console.print(
            f"⚠️  [yellow]Warning: No app directories found in {apps_dir}[/yellow]"
        )
        return created_files

    console.print(
        f"🔍 Found {len(app_dirs)} app(s): {', '.join(d.name for d in app_dirs)}"
    )

    for app_dir in app_dirs:
        console.print(f"📁 Processing app: {app_dir.name}")
        if copy_env_example_to_development(app_dir):
            created_files.append(app_dir / ".env.development.local")

    return created_files


@app.command()
def clean():
    """Clean workspace by removing build artifacts and lock files."""
    clean_workspace()


@app.command()
def install():
    """Install dependencies using pnpm and uv."""
    install_dependencies()


@app.command()
def init():
    """Initialize workspace with database setup and environment files for all apps."""
    console.print("🚀 [bold blue]Initializing workspace...[/bold blue]")

    # First, clean the workspace
    clean_workspace()

    # Install dependencies
    install_dependencies()

    # Run database initialization
    console.print("📊 [bold blue]Setting up database...[/bold blue]")
    try:
        db_init()
        console.print(
            "✅ [bold green]Database initialization completed[/bold green]"
        )
    except Exception as e:
        console.print(f"[red]Error during database initialization: {e}[/red]")
        raise typer.Exit(1)

    # Setup environment files for all apps
    console.print(
        "📄 [bold blue]Setting up app environment files...[/bold blue]"
    )
    created_files = setup_app_env_files()

    # Summary
    console.print(
        "✅ [bold green]Workspace initialization complete![/bold green]"
    )

    summary_text = "📁 Files created/updated:\n"
    summary_text += "   - Cleaned workspace artifacts\n"
    summary_text += "   - Installed dependencies (pnpm + uv)\n"
    summary_text += "   - Database files (see db init output above)\n"

    if created_files:
        for file_path in created_files:
            summary_text += f"   - {file_path}\n"
    else:
        summary_text += "   - No new app environment files created\n"

    console.print(
        Panel(
            Text.from_markup(summary_text.rstrip()),
            title="Workspace Setup Summary",
            border_style="green",
        )
    )


@app.command()
def set_vars():
    """Ensure all apps have proper environment files derived from examples."""
    console.print(
        "📄 [bold blue]Setting up app environment files...[/bold blue]"
    )

    created_files = setup_app_env_files()

    if created_files:
        console.print(
            f"✅ [bold green]Created {len(created_files)} environment file(s)[/bold green]"
        )
        for file_path in created_files:
            console.print(f"   - {file_path}")
    else:
        console.print(
            "✅ [bold green]All app environment files are already set up[/bold green]"
        )


@app.command()
def dev():
    """Start development environment with Supabase and Turbo dev."""
    console.print(
        "🚀 [bold blue]Starting development environment...[/bold blue]"
    )

    # Check if Supabase is running, start if not
    if not is_supabase_running():
        console.print(
            "📊 [bold blue]Supabase is not running. Starting it...[/bold blue]"
        )
        try:
            db_start()
            console.print(
                "✅ [bold green]Supabase started successfully[/bold green]"
            )
        except Exception as e:
            console.print(f"[red]Error starting Supabase: {e}[/red]")
            raise typer.Exit(1)
    else:
        console.print("✅ Supabase is already running")

    # Start Turbo dev
    console.print(
        "🔄 [bold blue]Starting Turbo development server...[/bold blue]"
    )
    try:
        subprocess.run(["pnpm", "turbo", "dev"], check=True)
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error running turbo dev: {e}[/red]")
        raise typer.Exit(1)
    except FileNotFoundError:
        console.print(
            "[red]Error: pnpm not found. Please install pnpm first.[/red]"
        )
        raise typer.Exit(1)
    except KeyboardInterrupt:
        console.print(
            "\n🛑 [yellow]Development server stopped by user[/yellow]"
        )
        raise typer.Exit(0)


@app.command()
def dev_stop():
    """Stop development environment and Supabase."""
    console.print(
        "🛑 [bold blue]Stopping development environment...[/bold blue]"
    )

    # Stop Supabase if running
    if is_supabase_running():
        console.print("📊 [bold blue]Stopping Supabase...[/bold blue]")
        try:
            db_stop()
            console.print(
                "✅ [bold green]Supabase stopped successfully[/bold green]"
            )
        except Exception as e:
            console.print(f"[red]Error stopping Supabase: {e}[/red]")
            raise typer.Exit(1)
    else:
        console.print("✅ Supabase is not running")

    console.print(
        "✅ [bold green]Development environment stopped[/bold green]"
    )


if __name__ == "__main__":
    app()
