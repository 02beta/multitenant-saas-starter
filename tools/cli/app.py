#!/usr/bin/env python3
"""
CLI tools for the multitenant SaaS starter project.

This package provides command-line utilities to help with development and project management tasks.
"""

import typer
from commands import db, workspace
from rich.console import Console

app = typer.Typer(
    name="cli",
    help="CLI tools for the multitenant SaaS starter project",
    add_completion=False,
)

console = Console()

# Add command groups
app.add_typer(db, name="db", help="Database administration commands")
app.add_typer(workspace, name="workspace", help="Workspace administration commands")


def main():
    """Main CLI entry point."""
    app()


if __name__ == "__main__":
    main()
