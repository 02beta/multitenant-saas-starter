#!/usr/bin/env python3
"""
Database administration commands for Supabase project management.

This module provides CLI commands for managing Supabase projects,
including initialization, environment variable management, and database operations.
"""

import os
import re
import secrets
import string
import subprocess
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

__all__ = [
    "app",
]

app = typer.Typer(
    name="db",
    help="Database administration commands for Supabase project management",
    add_completion=False,
)
console = Console()


def get_project_id() -> str:
    """Get project ID from Supabase config directory dynamically."""
    config_path = Path("infra/supabase/config.toml")
    if not config_path.exists():
        console.print("[red]Error: Could not find infra/supabase/config.toml[/red]")
        raise typer.Exit(1)

    try:
        with open(config_path, "r") as f:
            content = f.read()
            match = re.search(r'^project_id\s*=\s*"([^"]*)"', content, re.MULTILINE)
            if match:
                return match.group(1)
    except Exception as e:
        console.print(f"[red]Error reading config file: {e}[/red]")
        raise typer.Exit(1)

    console.print(
        "[red]Error: Could not find project_id in infra/supabase/config.toml[/red]"
    )
    raise typer.Exit(1)


def run_command(
    cmd: list[str], check: bool = True, capture_output: bool = False
) -> subprocess.CompletedProcess:
    """Run a shell command with error handling."""
    try:
        result = subprocess.run(
            cmd,
            check=check,
            capture_output=capture_output,
            text=True,
            env={**os.environ, "SUPABASE_WORKDIR": "infra"},
        )
        return result
    except subprocess.CalledProcessError as e:
        if not capture_output:
            console.print(f"[red]Command failed: {' '.join(cmd)}[/red]")
            console.print(f"[red]Error: {e}[/red]")
        raise


def ensure_supabase_workdir():
    """Ensure SUPABASE_WORKDIR is always set to 'infra' in .env.local."""
    env_file = Path(".env.local")
    key = "SUPABASE_WORKDIR"
    value = "infra"

    if not env_file.exists():
        env_file.write_text(f"{key}={value}\n")
        console.print(f"Added {key}={value} to {env_file}")
        return

    content = env_file.read_text()
    lines = content.splitlines()

    # Remove existing SUPABASE_WORKDIR lines
    lines = [line for line in lines if not line.startswith(f"{key}=")]

    # Add the correct value
    lines.append(f"{key}={value}")

    env_file.write_text("\n".join(lines) + "\n")


def is_supabase_running() -> bool:
    """Check if Supabase is running."""
    try:
        run_command(["supabase", "status"], capture_output=True)
        return True
    except subprocess.CalledProcessError:
        return False


def parse_database_url(db_url: str) -> dict[str, str]:
    """Parse DATABASE_URL to extract components."""
    # Extract components from postgresql://user:password@host:port/database
    pattern = r"postgresql://([^:]*):([^@]*)@([^:]*):(\d+)/([^?]*)"
    match = re.match(pattern, db_url)

    if not match:
        console.print(f"[red]Error: Could not parse database URL: {db_url}[/red]")
        raise typer.Exit(1)

    return {
        "user": match.group(1),
        "password": match.group(2),
        "host": match.group(3),
        "port": match.group(4),
        "name": match.group(5),
    }


def add_database_vars_to_file(env_file: Path, db_url: str):
    """Add database environment variables to a file."""
    db_components = parse_database_url(db_url)

    content = env_file.read_text() if env_file.exists() else ""
    lines = content.splitlines()

    vars_to_add = {
        "DATABASE_HOST": db_components["host"],
        "DATABASE_PORT": db_components["port"],
        "DATABASE_USER": db_components["user"],
        "DATABASE_PASSWORD": db_components["password"],
        "DATABASE_NAME": db_components["name"],
    }

    new_vars = []
    for key, value in vars_to_add.items():
        if not any(line.startswith(f"{key}=") for line in lines):
            new_vars.append(f"{key}={value}")
            console.print(f"Added: {key}={value} to {env_file}")

    if new_vars:
        with open(env_file, "a") as f:
            for var in new_vars:
                f.write(f"{var}\n")


def generate_password(length: int = 32) -> str:
    """Generate a secure random password."""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


@app.command()
def init():
    """Initialize project with env files, start Supabase, and set vars."""
    console.print("🚀 [bold blue]Initializing project...[/bold blue]")

    # Get the parent directory name (monorepo name)
    monorepo_name = Path.cwd().name

    # Create infra/supabase directory if it doesn't exist
    supabase_dir = Path("infra/supabase")
    supabase_dir.mkdir(parents=True, exist_ok=True)

    # Create or replace .env file in infra/supabase directory
    supabase_env_file = supabase_dir / ".env"
    console.print(f"Creating {supabase_env_file}...")

    env_content = f"""# Supabase Environment Configuration
# Generated by cli db init
SUPABASE_PROJECT_ID={monorepo_name}
SUPABASE_CLOUD_REGION=us-west-1
"""

    # Add OPENAI_API_KEY if it exists in environment
    if openai_key := os.getenv("OPENAI_API_KEY"):
        env_content += f"OPENAI_API_KEY={openai_key}\n"
        console.print("Added OPENAI_API_KEY from environment")
    else:
        console.print(
            "⚠️  [yellow]Warning: OPENAI_API_KEY not found in environment[/yellow]"
        )

    supabase_env_file.write_text(env_content)
    console.print(f"✅ Created {supabase_env_file}")

    # Update config.toml to use the dynamic project_id
    config_file = Path("infra/supabase/config.toml")
    if config_file.exists():
        content = config_file.read_text()
        updated_content = re.sub(
            r"^project_id\s*=.*",
            f'project_id = "{monorepo_name}"',
            content,
            flags=re.MULTILINE,
        )
        config_file.write_text(updated_content)
        console.print(f"✅ Updated project_id in {config_file} to: {monorepo_name}")
    else:
        console.print(f"⚠️  [yellow]Warning: {config_file} not found[/yellow]")

    console.print("🔄 [bold blue]Starting Supabase...[/bold blue]")
    start()

    console.print("⚙️  [bold blue]Setting environment variables...[/bold blue]")
    set_vars()

    console.print("✅ [bold green]Project initialization complete![/bold green]")
    console.print(
        Panel(
            Text.from_markup(
                f"📁 Files created/updated:\n"
                f"   - {supabase_env_file}\n"
                f"   - .env.local (root)\n"
                f"   - apps/api/.env.local\n"
                + (f"   - {config_file}\n" if config_file.exists() else "")
            ),
            title="Summary",
            border_style="green",
        )
    )


@app.command()
def create_new_project():
    """Create new Supabase project in cloud and link it."""
    console.print("🚀 [bold blue]Creating new Supabase project in cloud...[/bold blue]")

    # Check if Supabase CLI is installed
    try:
        run_command(["supabase", "--version"], capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        console.print("[red]Error: Supabase CLI is not installed[/red]")
        raise typer.Exit(1)

    supabase_env_file = Path("infra/supabase/.env")

    if not supabase_env_file.exists():
        console.print(
            f"[red]Error: {supabase_env_file} not found. Please run 'init' command first.[/red]"
        )
        raise typer.Exit(1)

    # Load environment variables from the Supabase env file
    env_vars = {}
    for line in supabase_env_file.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            key, value = line.split("=", 1)
            env_vars[key] = value

    project_id = env_vars.get("SUPABASE_PROJECT_ID")
    region = env_vars.get("SUPABASE_CLOUD_REGION")

    if not project_id or not region:
        console.print(
            "[red]Error: SUPABASE_PROJECT_ID or SUPABASE_CLOUD_REGION not found[/red]"
        )
        raise typer.Exit(1)

    # Generate production DB password if not set
    db_password = env_vars.get("SUPABASE_PRODUCTION_DB_PASSWORD")
    if not db_password:
        db_password = generate_password()
        with open(supabase_env_file, "a") as f:
            f.write(f"SUPABASE_PRODUCTION_DB_PASSWORD={db_password}\n")
        console.print("Generated and added SUPABASE_PRODUCTION_DB_PASSWORD")

    console.print("Creating Supabase project with:")
    console.print(f"  Name: {project_id}")
    console.print(f"  Region: {region}")
    console.print("  Password: [HIDDEN]")

    # Create the project
    try:
        result = run_command(
            [
                "supabase",
                "projects",
                "create",
                project_id,
                "--region",
                region,
                "--db-password",
                db_password,
            ],
            capture_output=True,
        )

        # Extract project reference from output
        project_ref_match = re.search(r"[a-z0-9]{20}", result.stdout)
        if not project_ref_match:
            console.print(
                "[red]Error: Could not extract project reference from output[/red]"
            )
            raise typer.Exit(1)

        project_ref = project_ref_match.group(0)
        console.print(f"✅ Project created successfully with reference: {project_ref}")

        # Add project reference to env file
        with open(supabase_env_file, "a") as f:
            f.write(f"SUPABASE_PROJECT_REF={project_ref}\n")
        console.print(f"Added SUPABASE_PROJECT_REF to {supabase_env_file}")

        # Link the project
        console.print("🔗 [bold blue]Linking project...[/bold blue]")
        run_command(
            ["supabase", "link", "--project-ref", project_ref, "-p", db_password]
        )

        console.print("✅ [bold green]Project linked successfully![/bold green]")
        console.print(
            Panel(
                Text.from_markup(
                    f"📁 Project details:\n"
                    f"   - Project ID: {project_id}\n"
                    f"   - Project Reference: {project_ref}\n"
                    f"   - Region: {region}\n"
                    f"   - Environment file: {supabase_env_file}"
                ),
                title="Project Created",
                border_style="green",
            )
        )

    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error creating project: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def set_vars():
    """Ensure all required Supabase env vars are present in .env.local without duplicates."""
    env_file = Path(".env.local")
    api_env_file = Path("apps/api/.env.local")

    # Check if Supabase CLI is installed
    try:
        run_command(["supabase", "--version"], capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        console.print("[red]Error: Supabase CLI is not installed[/red]")
        raise typer.Exit(1)

    # Check if Supabase is running
    if not is_supabase_running():
        console.print(
            "[red]Supabase is not running. Please run 'db start' first.[/red]"
        )
        raise typer.Exit(1)

    # Create .env.local if it doesn't exist
    if not env_file.exists():
        env_file.touch()
        console.print(f"Created {env_file}")

    # Get Supabase environment variables
    try:
        result = run_command(["supabase", "status", "-o", "env"], capture_output=True)
        env_output = result.stdout
    except subprocess.CalledProcessError:
        console.print("[red]Error getting Supabase status[/red]")
        raise typer.Exit(1)

    # Parse environment variables
    existing_content = env_file.read_text() if env_file.exists() else ""
    existing_lines = existing_content.splitlines()

    new_vars = []
    database_url_value = ""

    for line in env_output.splitlines():
        if line.startswith("#") or "=" not in line:
            continue

        var, value = line.split("=", 1)

        # Handle special case for DB_URL
        if var == "DB_URL":
            # Add DATABASE_URL (sync version)
            if not any(
                existing_line.startswith("DATABASE_URL=")
                for existing_line in existing_lines
            ):
                new_vars.append(f"DATABASE_URL={value}")
                console.print(f"Added: DATABASE_URL={value}")

            # Add DATABASE_ASYNC_URL (async version)
            async_url = value.replace("postgresql:", "postgresql+asyncpg:")
            if not any(
                existing_line.startswith("DATABASE_ASYNC_URL=")
                for existing_line in existing_lines
            ):
                new_vars.append(f"DATABASE_ASYNC_URL={async_url}")
                console.print(f"Added: DATABASE_ASYNC_URL={async_url}")

            database_url_value = value
            continue

        # Prefix variable with SUPABASE_ if not already present
        if not var.startswith("SUPABASE_"):
            prefixed_var = f"SUPABASE_{var}"
            line = f"SUPABASE_{line}"
        else:
            prefixed_var = var

        # Add if not already present
        if not any(
            existing_line.startswith(f"{prefixed_var}=")
            for existing_line in existing_lines
        ):
            new_vars.append(line)
            console.print(f"Added: {line}")

    # Add new variables to .env.local
    if new_vars:
        with open(env_file, "a") as f:
            f.write("\n# Supabase DO NOT EDIT (added by cli db set-vars)\n")
            f.write("# ------------------------------------------------------------\n")
            for var in new_vars:
                f.write(f"{var}\n")

        ensure_supabase_workdir()
        console.print(f"✅ All missing Supabase env vars have been added to {env_file}")
    else:
        console.print(
            f"All required Supabase env vars are already present in {env_file}"
        )

    # Add database component vars to root .env.local
    if database_url_value:
        add_database_vars_to_file(env_file, database_url_value)

    # Create apps/api directory and .env.local file
    api_env_file.parent.mkdir(parents=True, exist_ok=True)
    if not api_env_file.exists():
        api_env_file.touch()
        console.print(f"Created {api_env_file}")

    # Add database vars to API env file
    if database_url_value:
        api_content = api_env_file.read_text() if api_env_file.exists() else ""
        api_lines = api_content.splitlines()

        api_vars_to_add = []

        if not any(
            existing_line.startswith("DATABASE_URL=") for existing_line in api_lines
        ):
            api_vars_to_add.append(f"DATABASE_URL={database_url_value}")
            console.print(f"Added: DATABASE_URL to {api_env_file}")

        async_url = database_url_value.replace("postgresql:", "postgresql+asyncpg:")
        if not any(
            existing_line.startswith("DATABASE_ASYNC_URL=")
            for existing_line in api_lines
        ):
            api_vars_to_add.append(f"DATABASE_ASYNC_URL={async_url}")
            console.print(f"Added: DATABASE_ASYNC_URL to {api_env_file}")

        if api_vars_to_add:
            with open(api_env_file, "a") as f:
                for var in api_vars_to_add:
                    f.write(f"{var}\n")

        add_database_vars_to_file(api_env_file, database_url_value)

    # Handle SUPABASE_PRODUCTION_DB_PASSWORD
    prod_db_password = ""
    if any(
        existing_line.startswith("SUPABASE_PRODUCTION_DB_PASSWORD=")
        for existing_line in existing_lines
    ):
        for line in existing_lines:
            if line.startswith("SUPABASE_PRODUCTION_DB_PASSWORD="):
                prod_db_password = line.split("=", 1)[1]
                break
    else:
        prod_db_password = generate_password()
        with open(env_file, "a") as f:
            f.write(f"SUPABASE_PRODUCTION_DB_PASSWORD={prod_db_password}\n")
        console.print(
            f"Added: SUPABASE_PRODUCTION_DB_PASSWORD (generated) to {env_file}"
        )

    # Add SUPABASE_PRODUCTION_DB_PASSWORD to API env file
    api_content = api_env_file.read_text()
    if not any(
        existing_line.startswith("SUPABASE_PRODUCTION_DB_PASSWORD=")
        for existing_line in api_content.splitlines()
    ):
        with open(api_env_file, "a") as f:
            f.write(f"SUPABASE_PRODUCTION_DB_PASSWORD={prod_db_password}\n")
        console.print(f"Added: SUPABASE_PRODUCTION_DB_PASSWORD to {api_env_file}")

    console.print(
        "✅ [bold green]Database environment variables have been synchronized across all files.[/bold green]"
    )


@app.command()
def start():
    """Start Supabase (restarts if already running)."""
    # Check if Supabase CLI is installed
    try:
        run_command(["supabase", "--version"], capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        console.print("[red]Error: Supabase CLI is not installed[/red]")
        raise typer.Exit(1)

    # Ensure SUPABASE_WORKDIR is set
    ensure_supabase_workdir()

    if is_supabase_running():
        console.print("Supabase is already running. Restarting...")
        try:
            project_id = get_project_id()
            run_command(["supabase", "stop", "--project-id", project_id])
            console.print("Supabase stopped.")
        except Exception:
            # If we can't get project ID, just stop without it
            run_command(["supabase", "stop"])
            console.print("Supabase stopped.")

    console.print("🔄 [bold blue]Starting Supabase...[/bold blue]")
    run_command(["supabase", "start"])
    console.print("✅ [bold green]Supabase started.[/bold green]")


@app.command()
def stop():
    """Stop Supabase."""
    # Check if Supabase CLI is installed
    try:
        run_command(["supabase", "--version"], capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        console.print("[red]Error: Supabase CLI is not installed[/red]")
        raise typer.Exit(1)

    if is_supabase_running():
        console.print("🛑 [bold blue]Stopping Supabase...[/bold blue]")
        try:
            project_id = get_project_id()
            run_command(["supabase", "stop", "--project-id", project_id])
        except Exception:
            # If we can't get project ID, just stop without it
            run_command(["supabase", "stop"])
        console.print("✅ [bold green]Supabase stopped.[/bold green]")
    else:
        console.print("Supabase is not running.")


@app.command()
def reset_db():
    """Reset Supabase database (stops with reset and restarts)."""
    # Check if Supabase CLI is installed
    try:
        run_command(["supabase", "--version"], capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        console.print("[red]Error: Supabase CLI is not installed[/red]")
        raise typer.Exit(1)

    # Ensure SUPABASE_WORKDIR is set
    ensure_supabase_workdir()

    console.print("🔄 [bold blue]Resetting Supabase database...[/bold blue]")
    console.print(
        "⚠️  [yellow]This will delete all data in your local database![/yellow]"
    )

    try:
        project_id = get_project_id()

        if is_supabase_running():
            console.print("Stopping Supabase with reset...")
            run_command(["supabase", "stop", "--project-id", project_id, "--reset"])
        else:
            console.print("Supabase is not running. Running reset anyway...")
            run_command(["supabase", "stop", "--project-id", project_id, "--reset"])

        console.print("Supabase stopped and reset.")

    except Exception:
        # If we can't get project ID, just reset without it
        if is_supabase_running():
            run_command(["supabase", "stop", "--reset"])
        else:
            run_command(["supabase", "stop", "--reset"])
        console.print("Supabase stopped and reset.")

    console.print("🔄 [bold blue]Starting Supabase...[/bold blue]")
    run_command(["supabase", "start"])
    console.print(
        "✅ [bold green]Supabase database has been reset and restarted.[/bold green]"
    )


if __name__ == "__main__":
    app()
