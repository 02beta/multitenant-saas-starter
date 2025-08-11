"""
Release management commands for the multitenant SaaS starter project.

This module provides CLI commands for managing releases, version bumps,
changelog updates, and GitHub releases.
"""

import datetime
import json
import os
import re
import subprocess

# import sys
import tempfile
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

app = typer.Typer(
    name="release",
    help="Release management commands for the SaaS starter project",
    add_completion=False,
)
console = Console()


def run(cmd, check=True, capture_output=False, text=True, env=None):
    """Run a shell command with error handling."""
    try:
        result = subprocess.run(
            cmd,
            check=check,
            capture_output=capture_output,
            text=text,
            env=env or os.environ,
        )
        return result
    except subprocess.CalledProcessError as e:
        if not capture_output:
            console.print(f"[red]Command failed: {' '.join(cmd)}[/red]")
            console.print(f"[red]Error: {e}[/red]")
        raise


def command_exists(cmd):
    """Check if a command exists in PATH."""
    return (
        run(["which", cmd], check=False, capture_output=True).returncode == 0
    )


def get_current_version():
    """Get current version from root package.json."""
    pkg_path = Path("package.json")
    if pkg_path.exists():
        try:
            with open(pkg_path) as f:
                pkg = json.load(f)
            return pkg.get("version", "0.0.0")
        except Exception:
            return "0.0.0"
    return "0.0.0"


def get_last_release_tag():
    """Get last release tag in the form vX.Y.Z."""
    try:
        result = run(
            ["git", "tag", "--sort=-version:refname"],
            capture_output=True,
        )
        tags = result.stdout.splitlines()
        for tag in tags:
            if re.match(r"^v\d+\.\d+\.\d+$", tag):
                return tag
        return ""
    except Exception:
        return ""


def bump_version(version_type: str, current_version: str = None):
    """Bump version based on type."""
    if not current_version:
        current_version = get_current_version()
    parts = current_version.split(".")
    major, minor, patch = [int(x) for x in parts[:3]]
    if version_type == "patch":
        patch += 1
    elif version_type == "minor":
        minor += 1
        patch = 0
    elif version_type == "major":
        major += 1
        minor = 0
        patch = 0
    else:
        raise typer.Exit(f"Invalid version type: {version_type}")
    return f"{major}.{minor}.{patch}"


def update_pyproject_toml_files(new_version: str):
    """Update version in all pyproject.toml files."""
    result = run(["git", "ls-files", "*.toml"], capture_output=True)
    files = [
        f for f in result.stdout.splitlines() if f.endswith("pyproject.toml")
    ]
    for file in files:
        try:
            with open(file, "r") as f:
                content = f.read()
            # Replace version in [project] section
            content = re.sub(
                r"(version\s*=\s*[\"\']).+?([\"\']\s*)",
                r"\g<1>" + new_version + r"\2",
                content,
            )
            with open(file, "w") as f:
                f.write(content)
            console.print(f"[green]Updated version in {file}[/green]")
        except Exception as e:
            console.print(f"[red]Error updating {file}: {e}[/red]")


def update_package_json_files(new_version: str):
    """Update version in all package.json files."""
    result = run(["git", "ls-files", "*.json"], capture_output=True)
    files = [
        f for f in result.stdout.splitlines() if f.endswith("package.json")
    ]
    for file in files:
        try:
            with open(file, "r") as f:
                pkg = json.load(f)
            pkg["version"] = new_version
            with open(file, "w") as f:
                json.dump(pkg, f, indent=2)
                f.write("\n")
            console.print(f"[green]Updated version in {file}[/green]")
        except Exception as e:
            console.print(f"[red]Error updating {file}: {e}[/red]")


def install_dependencies():
    """Check and install required dependencies."""
    # Check for gh CLI
    if not command_exists("gh"):
        console.print(
            "[yellow]GitHub CLI (gh) not found. Please install it manually.[/yellow]"
        )
        raise typer.Exit(1)
    # Check for jq
    if not command_exists("jq"):
        console.print(
            "[yellow]jq not found. Please install it manually.[/yellow]"
        )
        raise typer.Exit(1)


def authenticate_github_cli():
    """Authenticate GitHub CLI if needed."""
    try:
        run(["gh", "auth", "status"], check=True, capture_output=True)
        console.print("[green]GitHub CLI is already authenticated[/green]")
        return True
    except Exception:
        token = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN")
        if token:
            p = subprocess.Popen(
                ["gh", "auth", "login", "--with-token"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            p.communicate(input=token)
            if p.returncode == 0:
                console.print(
                    "[green]GitHub CLI authenticated successfully[/green]"
                )
                return True
            else:
                console.print(
                    "[red]Failed to authenticate GitHub CLI with provided token[/red]"
                )
                return False
        else:
            console.print(
                "[red]GitHub CLI is not authenticated and GITHUB_PERSONAL_ACCESS_TOKEN is not set.[/red]"
            )
            return False


def generate_release_notes(from_tag, to_ref, version):
    """Generate release notes using AI or fallback to git log."""
    console.print(f"[blue]Generating release notes for v{version}...[/blue]")
    if from_tag:
        result = run(
            [
                "git",
                "log",
                "--oneline",
                "--pretty=format:- %s",
                f"{from_tag}..{to_ref}",
            ],
            capture_output=True,
        )
    else:
        result = run(
            ["git", "log", "--oneline", "--pretty=format:- %s"],
            capture_output=True,
        )
    git_diff = result.stdout.strip() or "- Initial release"
    prompt = f"""
Please format the following git commit messages into a professional
changelog entry for version {version}.

Git commits since last release:
{git_diff}

Please format this as a markdown changelog entry with the following structure:
- Start with "## [{version}] - {datetime.date.today().isoformat()}"
- Group changes into categories like "### Added", "### Changed", "### Fixed",
  "### Removed" as appropriate
- Make the descriptions more user-friendly and professional
- Remove any internal/technical commit prefixes like "chore:", "feat:",
  "fix:" etc.
- Focus on user-facing changes and improvements

Return only the markdown changelog entry, nothing else.
"""
    release_notes = ""
    # Try ollama
    if command_exists("ollama"):
        try:
            ollama_list = run(["ollama", "list"], capture_output=True)
            if "llama" in ollama_list.stdout:
                with tempfile.NamedTemporaryFile("w+", delete=False) as tf:
                    tf.write(prompt)
                    tf.flush()
                    result = run(
                        ["ollama", "run", "llama3.2", prompt],
                        capture_output=True,
                    )
                    release_notes = result.stdout.strip()
        except Exception:
            pass
    # Try openai cli
    if (
        not release_notes
        and command_exists("openai")
        and os.environ.get("OPENAI_API_KEY")
    ):
        try:
            import json as pyjson
            # import shlex

            openai_prompt = prompt.replace('"', '\\"')
            openai_prompt = pyjson.dumps([
                {"role": "user", "content": openai_prompt}
            ])
            print(f"openai_prompt: {openai_prompt.center(79, '=')}")
            result = run(
                [
                    "openai",
                    "api",
                    "chat.completions.create",
                    "-m",
                    "gpt-4",
                    "--messages",
                    openai_prompt,
                    "--max-tokens",
                    "1000",
                ],
                capture_output=True,
            )
            # Parse output for .choices[0].message.content
            import jq

            content = (
                jq.compile(".choices[0].message.content")
                .input(text=result.stdout)
                .first()
            )
            release_notes = content.strip()
        except Exception:
            pass
    # Try curl to OpenAI API
    if (
        not release_notes
        and command_exists("curl")
        and os.environ.get("OPENAI_API_KEY")
    ):
        try:
            import requests

            headers = {
                "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}",
                "Content-Type": "application/json",
            }
            data = {
                "model": "gpt-4",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1000,
            }
            resp = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30,
            )
            if resp.ok:
                content = resp.json()["choices"][0]["message"]["content"]
                release_notes = content.strip()
        except Exception:
            pass
    # Fallback
    if not release_notes:
        console.print(
            "[yellow]AI tools not available, generating basic release notes...[/yellow]"
        )
        release_notes = f"## [{version}] - {datetime.date.today().isoformat()}\n\n### Changes\n{git_diff}"
    return release_notes


def update_changelog(version, release_notes):
    """Update CHANGELOG.md with new release notes."""
    changelog_file = Path("CHANGELOG.md")
    header = (
        "# Changelog\n\n"
        "All notable changes to this project will be documented in this file.\n\n"
        "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),\n"
        "and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).\n\n"
    )
    if not changelog_file.exists():
        changelog_file.write_text(header)
    with open(changelog_file, "r") as f:
        lines = f.readlines()
    # Find where header ends (after 6 lines)
    header_lines = 6
    new_content = lines[:header_lines] if len(lines) >= header_lines else lines
    new_content.append(f"{release_notes}\n\n")
    if len(lines) > header_lines:
        new_content.extend(lines[header_lines:])
    with tempfile.NamedTemporaryFile("w", delete=False) as tf:
        tf.writelines(new_content)
        tf.flush()
        changelog_file.write_text("".join(new_content))
    console.print("[green]Updated CHANGELOG.md[/green]")


def create_github_release(version, release_notes):
    """Create a GitHub release using gh CLI."""
    if not authenticate_github_cli():
        raise typer.Exit(1)
    with tempfile.NamedTemporaryFile("w", delete=False) as tf:
        tf.write(release_notes)
        tf.flush()
        run([
            "gh",
            "release",
            "create",
            f"v{version}",
            "--title",
            f"Release v{version}",
            "--notes-file",
            tf.name,
            "--latest",
        ])
    console.print(f"[green]GitHub release created: v{version}[/green]")


def run_precommit():
    """Run precommit tasks for all apps."""
    apps_dir = Path("apps")
    if not apps_dir.exists():
        return
    for app_dir in apps_dir.iterdir():
        if app_dir.is_dir() and (app_dir / "package.json").exists():
            console.print(f"[blue]Running precommit for {app_dir}[/blue]")
            try:
                run(
                    ["pnpm", "run", "precommit"], check=False, cwd=str(app_dir)
                )
            except Exception:
                pass
    console.print("[green]Precommit tasks completed[/green]")


def commit_and_push(version_type, new_version):
    """Commit and push changes, create tag."""
    run(["git", "add", "."])
    run([
        "git",
        "commit",
        "-m",
        f"chore: release:{version_type} - bump to v{new_version}",
    ])
    run(["git", "tag", f"v{new_version}"])
    run(["git", "push"])
    run(["git", "push", "--tags"])
    console.print(
        f"[green]Changes committed and pushed with tag v{new_version}[/green]"
    )


def sync_versions():
    """Sync all versions to root version."""
    current_version = get_current_version()
    if current_version == "0.0.0":
        console.print(
            "[yellow]No root package.json found or version not set. Using 0.0.1 as default.[/yellow]"
        )
        current_version = "0.0.1"
    console.print(f"[blue]Syncing all versions to: {current_version}[/blue]")
    update_package_json_files(current_version)
    update_pyproject_toml_files(current_version)
    console.print("[green]All versions synced[/green]")


@app.command("bump-patch")
def bump_patch():
    """Bump patch version only (no commit)."""
    new_version = bump_version("patch")
    update_package_json_files(new_version)
    update_pyproject_toml_files(new_version)
    console.print(f"[green]Bumped patch version to {new_version}[/green]")


@app.command("bump-minor")
def bump_minor():
    """Bump minor version only (no commit)."""
    new_version = bump_version("minor")
    update_package_json_files(new_version)
    update_pyproject_toml_files(new_version)
    console.print(f"[green]Bumped minor version to {new_version}[/green]")


@app.command("bump-major")
def bump_major():
    """Bump major version only (no commit)."""
    new_version = bump_version("major")
    update_package_json_files(new_version)
    update_pyproject_toml_files(new_version)
    console.print(f"[green]Bumped major version to {new_version}[/green]")


@app.command("sync-versions")
def sync_versions_cmd():
    """Sync all package.json and pyproject.toml versions to root version."""
    sync_versions()


def _release(version_type: str):
    install_dependencies()
    run_precommit()
    new_version = bump_version(version_type)
    last_tag = get_last_release_tag()
    release_notes = generate_release_notes(last_tag, "HEAD", new_version)
    update_package_json_files(new_version)
    update_pyproject_toml_files(new_version)
    update_changelog(new_version, release_notes)
    commit_and_push(version_type, new_version)
    create_github_release(new_version, release_notes)
    console.print(
        f"[green]{version_type.capitalize()} release completed: v{new_version}[/green]"
    )


@app.command("release-patch")
def release_patch():
    """Run precommit, bump patch version, generate release notes, commit, push, and create GitHub release."""
    _release("patch")


@app.command("release-minor")
def release_minor():
    """Run precommit, bump minor version, generate release notes, commit, push, and create GitHub release."""
    _release("minor")


@app.command("release-major")
def release_major():
    """Run precommit, bump major version, generate release notes, commit, push, and create GitHub release."""
    _release("major")
