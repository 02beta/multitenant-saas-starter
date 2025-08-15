#!/usr/bin/env python3
"""
CLI tools for the multitenant SaaS starter project.

This package provides command-line utilities to help with development and project management tasks.
"""

import typer
from commands import db, release, serve, workspace
from rich.console import Console

app = typer.Typer(
    name="cli",
    help="Workspace CLI for managing the development, database, and release of the 02Beta Multi-Tenant SaaS Starter.",
    add_completion=False,
    no_args_is_help=True,
    rich_markup_mode="rich",
)

console = Console()

# Typer Command Groups
app.add_typer(db, name="db", help="Database administration commands")
app.add_typer(serve, name="serve", help="Development environment commands")
app.add_typer(release, name="release", help="Release automation commands")
app.add_typer(
    workspace, name="workspace", help="Workspace administration commands"
)


def main():
    """Main CLI entry point."""
    app()


if __name__ == "__main__":
    main()
