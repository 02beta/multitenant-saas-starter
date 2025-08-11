#!/usr/bin/env python3
"""
CLI tools for the multitenant SaaS starter project.

This package provides command-line utilities to help with development and project management tasks.
"""

import typer
from commands import db, release, workspace
from rich.console import Console

app = typer.Typer(
    name="cli",
    help="CLI tools for the multitenant SaaS starter project",
    add_completion=False,
)

console = Console()

# Add command groups
app.add_typer(db, name="db", help="Database administration commands")
app.add_typer(
    workspace,
    name="workspace",
    help="Workspace administration commands",
)
app.add_typer(
    release,
    name="release",
    help="Create releases which run precommit, bump version, ai generated release "
    "notes, commit, push, and create GitHub release",
)


def main():
    """Main CLI entry point."""
    app()


if __name__ == "__main__":
    main()
