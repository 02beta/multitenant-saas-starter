"""
Release management commands for the multitenant SaaS starter project.

This module provides CLI commands for managing releases, version bumps,
changelog updates, and GitHub releases.

Available commands:
- bump-patch:    Bump patch version only (no commit)
- bump-minor:    Bump minor version only (no commit)
- bump-major:    Bump major version only (no commit)
- sync-versions: Sync all package.json and pyproject.toml versions to root version
- release-patch: Run precommit, bump patch version, generate release notes, commit, push, and create GitHub release
- release-minor: Run precommit, bump minor version, generate release notes, commit, push, and create GitHub release
- release-major: Run precommit, bump major version, generate release notes, commit, push, and create GitHub release
"""

import datetime
import json
import logging
import os
import re
import subprocess
import tempfile
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

__all__ = [
    "app",
]

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)

app = typer.Typer(
    name="release",
    help="Release management commands for the SaaS starter project",
    add_completion=False,
)
console = Console()


def run(cmd, check=True, capture_output=False, text=True, env=None, cwd=None):
    """Run a shell command with error handling and logging."""
    logging.info(f"Running command: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            check=check,
            capture_output=capture_output,
            text=text,
            env=env or os.environ,
            cwd=cwd,
        )
        if capture_output and result.stdout:
            logging.debug(f"Command output: {result.stdout.strip()}")
        return result
    except subprocess.CalledProcessError as e:
        error_text = Text(f"Command failed: {' '.join(cmd)}", style="bold red")
        error_panel = Panel(error_text, title="Error", style="red")
        console.print(error_panel)
        logging.error(f"Command failed: {' '.join(cmd)}")
        logging.error(f"Error: {e}")
        raise


def command_exists(cmd):
    """Check if a command exists in PATH."""
    exists = (
        run(["which", cmd], check=False, capture_output=True).returncode == 0
    )
    logging.info(f"Command '{cmd}' exists: {exists}")
    return exists


def get_current_version():
    """Get current version from root package.json."""
    pkg_path = Path("package.json")
    if pkg_path.exists():
        try:
            with open(pkg_path) as f:
                pkg = json.load(f)
            version = pkg.get("version", "0.0.0")
            logging.info(f"Current version from package.json: {version}")
            return version
        except Exception as e:
            logging.warning(f"Failed to read package.json: {e}")
            return "0.0.0"
    logging.warning("package.json not found, defaulting version to 0.0.0")
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
                logging.info(f"Last release tag found: {tag}")
                return tag
        logging.info("No release tag found.")
        return ""
    except Exception as e:
        logging.warning(f"Failed to get last release tag: {e}")
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
        logging.error(f"Invalid version type: {version_type}")
        raise typer.Exit(f"Invalid version type: {version_type}")
    new_version = f"{major}.{minor}.{patch}"
    logging.info(
        f"Bumped {version_type} version: {current_version} -> {new_version}"
    )
    return new_version


def update_pyproject_toml_files(new_version: str):
    """Update version in all pyproject.toml files."""
    logging.info("Updating pyproject.toml files...")
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
            msg = Text(f"Updated version in {file}", style="green")
            console.print(Panel(msg, title="pyproject.toml", style="green"))
            logging.info(f"Updated version in {file}")
        except Exception as e:
            msg = Text(f"Error updating {file}: {e}", style="bold red")
            console.print(Panel(msg, title="Error", style="red"))
            logging.error(f"Error updating {file}: {e}")


def update_package_json_files(new_version: str):
    """Update version in all package.json files."""
    logging.info("Updating package.json files...")
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
            msg = Text(f"Updated version in {file}", style="green")
            console.print(Panel(msg, title="package.json", style="green"))
            logging.info(f"Updated version in {file}")
        except Exception as e:
            msg = Text(f"Error updating {file}: {e}", style="bold red")
            console.print(Panel(msg, title="Error", style="red"))
            logging.error(f"Error updating {file}: {e}")


def install_dependencies():
    """Check and install required dependencies."""
    logging.info("Checking for required dependencies...")
    # Check for gh CLI
    if not command_exists("gh"):
        msg = Text(
            "GitHub CLI (gh) not found. Please install it manually.",
            style="yellow",
        )
        console.print(Panel(msg, title="Dependency Missing", style="yellow"))
        logging.error("GitHub CLI (gh) not found.")
        raise typer.Exit(1)
    # Check for jq
    if not command_exists("jq"):
        msg = Text("jq not found. Please install it manually.", style="yellow")
        console.print(Panel(msg, title="Dependency Missing", style="yellow"))
        logging.error("jq not found.")
        raise typer.Exit(1)
    msg = Text("All required dependencies are installed.", style="green")
    console.print(Panel(msg, title="Dependencies", style="green"))
    logging.info("All required dependencies are installed.")


def authenticate_github_cli():
    """Authenticate GitHub CLI if needed."""
    logging.info("Authenticating GitHub CLI...")
    try:
        run(["gh", "auth", "status"], check=True, capture_output=True)
        msg = Text("GitHub CLI is already authenticated", style="green")
        console.print(Panel(msg, title="GitHub Auth", style="green"))
        logging.info("GitHub CLI is already authenticated.")
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
                msg = Text(
                    "GitHub CLI authenticated successfully", style="green"
                )
                console.print(Panel(msg, title="GitHub Auth", style="green"))
                logging.info("GitHub CLI authenticated successfully.")
                return True
            else:
                msg = Text(
                    "Failed to authenticate GitHub CLI with provided token",
                    style="bold red",
                )
                console.print(Panel(msg, title="GitHub Auth", style="red"))
                logging.error(
                    "Failed to authenticate GitHub CLI with provided token."
                )
                return False
        else:
            msg = Text(
                "GitHub CLI is not authenticated and GITHUB_PERSONAL_ACCESS_TOKEN "
                "is not set.",
                style="bold red",
            )
            console.print(Panel(msg, title="GitHub Auth", style="red"))
            logging.error(
                "GitHub CLI is not authenticated and GITHUB_PERSONAL_ACCESS_TOKEN "
                "is not set."
            )
            return False


def generate_release_notes(from_tag, to_ref, version):
    """Generate release notes using AI or fallback to git log."""
    msg = Text(
        f"Generating release notes for v{version}...", style="bold blue"
    )
    console.print(Panel(msg, title="Release Notes", style="blue"))
    logging.info(f"Generating release notes for v{version}...")
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
                    logging.info("Release notes generated using ollama.")
        except Exception as e:
            logging.warning(f"Ollama failed: {e}")
    # Try openai cli
    if (
        not release_notes
        and command_exists("openai")
        and os.environ.get("OPENAI_API_KEY")
    ):
        try:
            import json as pyjson

            openai_prompt = prompt.replace('"', '\\"')
            openai_prompt = pyjson.dumps([
                {"role": "user", "content": openai_prompt}
            ])
            logging.info("Generating release notes using OpenAI CLI...")
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
            import jq

            content = (
                jq.compile(".choices[0].message.content")
                .input(text=result.stdout)
                .first()
            )
            release_notes = content.strip()
            logging.info("Release notes generated using OpenAI CLI.")
        except Exception as e:
            logging.warning(f"OpenAI CLI failed: {e}")
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
            logging.info(
                "Generating release notes using OpenAI API via requests..."
            )
            resp = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30,
            )
            if resp.ok:
                content = resp.json()["choices"][0]["message"]["content"]
                release_notes = content.strip()
                logging.info("Release notes generated using OpenAI API.")
        except Exception as e:
            logging.warning(f"OpenAI API via requests failed: {e}")
    # Fallback
    if not release_notes:
        msg = Text(
            "AI tools not available, generating basic release notes...",
            style="yellow",
        )
        console.print(Panel(msg, title="Release Notes", style="yellow"))
        logging.warning(
            "AI tools not available, generating basic release notes."
        )
        release_notes = f"## [{version}] - {datetime.date.today().isoformat()}\n\n### Changes\n{git_diff}"
    return release_notes


def update_changelog(version, release_notes):
    """Update CHANGELOG.md with new release notes."""
    logging.info("Updating CHANGELOG.md...")
    changelog_file = Path("CHANGELOG.md")
    header = (
        "# Changelog\n\n"
        "All notable changes to this project will be documented in this file.\n\n"
        "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),\n"
        "and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).\n\n"
    )
    if not changelog_file.exists():
        changelog_file.write_text(header)
        logging.info("Created new CHANGELOG.md with header.")
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
    msg = Text("Updated CHANGELOG.md", style="green")
    console.print(Panel(msg, title="Changelog", style="green"))
    logging.info("CHANGELOG.md updated.")


def create_github_release(version, release_notes):
    """Create a GitHub release using gh CLI."""
    logging.info(f"Creating GitHub release v{version}...")
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
    msg = Text(f"GitHub release created: v{version}", style="green")
    console.print(Panel(msg, title="GitHub Release", style="green"))
    logging.info(f"GitHub release created: v{version}")


def run_precommit():
    """Run precommit tasks for all apps."""
    logging.info("Running precommit tasks for all apps...")
    apps_dir = Path("apps")
    if not apps_dir.exists():
        logging.info("No 'apps' directory found, skipping precommit.")
        return
    for app_dir in apps_dir.iterdir():
        if app_dir.is_dir() and (app_dir / "package.json").exists():
            msg = Text(f"Running precommit for {app_dir}", style="blue")
            console.print(Panel(msg, title="Precommit", style="blue"))
            logging.info(f"Running precommit for {app_dir}")
            try:
                run(
                    ["pnpm", "run", "precommit"], check=False, cwd=str(app_dir)
                )
            except Exception as e:
                logging.warning(f"Precommit failed for {app_dir}: {e}")
    msg = Text("Precommit tasks completed", style="green")
    console.print(Panel(msg, title="Precommit", style="green"))
    logging.info("Precommit tasks completed.")


def commit_and_push(version_type, new_version):
    """Commit and push changes, create tag."""
    logging.info("Committing and pushing changes...")
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
    msg = Text(
        f"Changes committed and pushed with tag v{new_version}", style="green"
    )
    console.print(Panel(msg, title="Git", style="green"))
    logging.info(f"Changes committed and pushed with tag v{new_version}")


def sync_versions():
    """Sync all versions to root version."""
    logging.info("Syncing all versions to root version...")
    current_version = get_current_version()
    if current_version == "0.0.0":
        msg = Text(
            "No root package.json found or version not set. Using 0.0.1 as default.",
            style="yellow",
        )
        console.print(Panel(msg, title="Sync Versions", style="yellow"))
        logging.warning(
            "No root package.json found or version not set. Using 0.0.1 as default."
        )
        current_version = "0.0.1"
    msg = Text(f"Syncing all versions to: {current_version}", style="blue")
    console.print(Panel(msg, title="Sync Versions", style="blue"))
    update_package_json_files(current_version)
    update_pyproject_toml_files(current_version)
    msg = Text("All versions synced", style="green")
    console.print(Panel(msg, title="Sync Versions", style="green"))
    logging.info("All versions synced.")


@app.command("bump-patch")
def bump_patch():
    """Bump patch version only (no commit)."""
    logging.info("Bumping patch version (no commit)...")
    new_version = bump_version("patch")
    update_package_json_files(new_version)
    update_pyproject_toml_files(new_version)
    msg = Text(f"Bumped patch version to {new_version}", style="green")
    console.print(Panel(msg, title="Bump Patch", style="green"))
    logging.info(f"Bumped patch version to {new_version}")


@app.command("bump-minor")
def bump_minor():
    """Bump minor version only (no commit)."""
    logging.info("Bumping minor version (no commit)...")
    new_version = bump_version("minor")
    update_package_json_files(new_version)
    update_pyproject_toml_files(new_version)
    msg = Text(f"Bumped minor version to {new_version}", style="green")
    console.print(Panel(msg, title="Bump Minor", style="green"))
    logging.info(f"Bumped minor version to {new_version}")


@app.command("bump-major")
def bump_major():
    """Bump major version only (no commit)."""
    logging.info("Bumping major version (no commit)...")
    new_version = bump_version("major")
    update_package_json_files(new_version)
    update_pyproject_toml_files(new_version)
    msg = Text(f"Bumped major version to {new_version}", style="green")
    console.print(Panel(msg, title="Bump Major", style="green"))
    logging.info(f"Bumped major version to {new_version}")


@app.command("sync-versions")
def sync_versions_cmd():
    """Sync all package.json and pyproject.toml versions to root version."""
    logging.info(
        "Syncing all package.json and pyproject.toml versions to root version..."
    )
    sync_versions()


def _release(version_type: str):
    """Run the release process for the specified version type.

    This function ensures all versions are synchronized before and after
    bumping, runs precommit checks, generates release notes, updates
    changelogs, commits, pushes, and creates a GitHub release.
    """
    msg = Text(
        f"Starting {version_type} release process...", style="bold blue"
    )
    console.print(Panel(msg, title="Release", style="blue"))
    logging.info(f"Starting {version_type} release process...")

    # Ensure all versions are synchronized before bumping
    logging.info("Synchronizing versions before version bump...")
    sync_versions()

    install_dependencies()
    run_precommit()

    new_version = bump_version(version_type)

    # Ensure all versions are synchronized after bumping
    logging.info("Synchronizing versions after version bump...")
    sync_versions()

    last_tag = get_last_release_tag()
    release_notes = generate_release_notes(last_tag, "HEAD", new_version)
    update_package_json_files(new_version)
    update_pyproject_toml_files(new_version)
    update_changelog(new_version, release_notes)
    commit_and_push(version_type, new_version)
    create_github_release(new_version, release_notes)

    msg = Text(
        f"{version_type.capitalize()} release completed: v{new_version}",
        style="bold green",
    )
    console.print(Panel(msg, title="Release Complete", style="green"))
    logging.info(
        f"{version_type.capitalize()} release completed: v{new_version}"
    )


@app.command("release-patch")
def release_patch():
    """Run precommit, bump patch version, generate release notes, commit, push,
    and create GitHub release."""
    logging.info("Running release-patch command...")
    _release("patch")


@app.command("release-minor")
def release_minor():
    """Run precommit, bump minor version, generate release notes, commit, push,
    and create GitHub release."""
    logging.info("Running release-minor command...")
    _release("minor")


@app.command("release-major")
def release_major():
    """Run precommit, bump major version, generate release notes, commit, push,
    and create GitHub release."""
    logging.info("Running release-major command...")
    _release("major")


if __name__ == "__main__":
    app()
