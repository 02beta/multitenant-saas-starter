# CLI Tools

Command-line utilities for development, workspace, database, and release
management in the multitenant SaaS starter. The CLI is built with Typer and
organized into command groups, all accessible from a single entrypoint.

## Requirements

- pnpm (for Node workspaces)
- uv (Python package manager and runner)
- Supabase CLI (`supabase`) for database commands
- Optional for release automation:
  - gh (GitHub CLI, authenticated)
  - jq (for parsing JSON output when using OpenAI CLI)
  - openai CLI and/or `OPENAI_API_KEY` env var (optional)
  - ollama with a local model like `llama3.2` (optional)
  - curl (optional)

## Install

From the repository root, install all workspace Python deps (including this
package):

```bash
uv sync
```

This project exposes a console script named `cli` via uv, so you can run:

```bash
uv run cli --help
```

If you prefer, you can also execute the module directly from this folder:

```bash
cd tools/cli
uv run python -m app --help
```

## Command Groups

The main entrypoint wires these groups:

- workspace: Workspace administration commands
- db: Database administration commands for Supabase
- release: Release automation (version bump, changelog, tag, GitHub release)

## Workspace Commands

Namespace: `workspace` (wired into the main `cli` entrypoint)

```bash
uv run cli workspace --help
```

### workspace clean

Clean workspace by removing build artifacts and lock files.

Removes: `.next`, `.turbo`, `.venv`, `node_modules`, `pnpm-lock.yaml`, `uv.lock`

```bash
uv run cli workspace clean
```

### workspace install

Install dependencies using pnpm and uv.

```bash
uv run cli workspace install
```

### workspace init

Initialize workspace: clean, install, initialize database, and create
`.env.development.local` in each app from `.env.local.example` if present.

```bash
uv run cli workspace init
```

### workspace set-vars

Ensure all apps have proper environment files derived from examples.

```bash
uv run cli workspace set-vars
```

### workspace dev

Start development environment with Supabase (auto-starts if not running)
and Turbo dev (`pnpm turbo dev`).

```bash
uv run cli workspace dev
```

### workspace dev-stop

Stop development environment and Supabase.

```bash
uv run cli workspace dev-stop
```

## Database (Supabase) Commands

Namespace: `db` (wired into the main `cli` entrypoint)

```bash
uv run cli db --help
```

### db init

Initialize the project for local Supabase development.

Actions:

- Creates/updates `infra/supabase/.env` with basic settings and `OPENAI_API_KEY`
  if present
- Updates `infra/supabase/config.toml` `project_id` to the monorepo folder name
- Starts Supabase locally
- Synchronizes Supabase env vars to root `.env.local` and `apps/api/.env.local`

```bash
uv run cli db init
```

### db create-new-project

Create a new Supabase project in the cloud and link it locally.

Requires `infra/supabase/.env` from `db init` and Supabase CLI auth.

```bash
uv run cli db create-new-project
```

### db set-vars

Sync required Supabase env vars into `.env.local` (root) and
`apps/api/.env.local`, adding:

- `DATABASE_URL`, `DATABASE_ASYNC_URL`
- Prefixed envs like `SUPABASE_PUBLIC_KEY`, `SUPABASE_SECRET_KEY`, `AUTH_JWT_SECRET`
- Component variables (`DATABASE_HOST`, `DATABASE_PORT`, etc.) derived from
  `DATABASE_URL`
- Ensures `SUPABASE_PRODUCTION_DB_PASSWORD` is present (generates if missing)

Requires Supabase to be running.

```bash
uv run cli db set-vars
```

### db start

Start Supabase (no-op if already running). Ensures `SUPABASE_WORKDIR=infra` in
`.env.development.local`.

```bash
uv run cli db start
```

### db stop

Stop Supabase (uses project id from `infra/supabase/config.toml` when available).

```bash
uv run cli db stop
```

### db reset-db

Reset local Supabase database (destructive), then restart.

```bash
uv run cli db reset-db
```

## Release Commands

Release automation is exposed under the `release` group on the main CLI.

```bash
uv run cli release --help
```

### Requirements for release automation

- gh (GitHub CLI) authenticated.
  - Non-interactive auth supported via `GITHUB_PERSONAL_ACCESS_TOKEN`.
- jq installed.
- Optional AI notes generation:
  - ollama with a local model (e.g., `llama3.2`), or
  - openai CLI with `OPENAI_API_KEY`, or
  - direct HTTP via `requests` and `OPENAI_API_KEY`, or
  - fallback to basic git log formatting.

### Behavior

- Bumps versions in all `package.json` and `pyproject.toml` files.
- Generates release notes from git history (auto AI when available).
- Updates `CHANGELOG.md` (Keep a Changelog format).
- Commits, tags (`vX.Y.Z`), pushes, and creates a GitHub release.
- Runs per-app `pnpm run precommit` under `apps/*` before release.

### Commands

```bash
# Patch release: precommit → bump patch → notes → changelog → commit → tag → push → GH release
uv run cli release release-patch

# Minor release
uv run cli release release-minor

# Major release
uv run cli release release-major

# Version bump only (no commit/push); updates package.json and pyproject.toml
uv run cli release bump-patch
uv run cli release bump-minor
uv run cli release bump-major

# Sync all versions to root version without bumping
uv run cli release sync-versions
```

### Environment variables used by release

- `GITHUB_PERSONAL_ACCESS_TOKEN`: Non-interactive GitHub CLI auth
- `OPENAI_API_KEY`: For AI-generated release notes (openai CLI or HTTP)

### Notes generation backoffs

The release notes generator tries, in order:

- ollama (`llama3.2`)
- openai CLI (`gpt-4`)
- HTTP to OpenAI API (`gpt-4`)
- Fallback: basic list from `git log`

## Examples

End-to-end local setup and dev server:

```bash
# Install deps
uv sync

# Initialize workspace and Supabase env files
uv run cli workspace init

# Start the dev environment (Supabase + Turbo)
uv run cli workspace dev
```

Create and link a new Supabase cloud project:

```bash
uv run cli db create-new-project
```

Run a patch release:

```bash
uv run cli release release-patch
```

## Getting Help

```bash
# Main CLI
uv run cli --help

# Workspace group
uv run cli workspace --help

# Database group
uv run cli db --help

# Release group
uv run cli release --help
```

## Quick aliases and local convenience

You can make CLI usage even shorter by using the helper script and/or an alias:

1. From any shell, invoke the helper script (runs from repo root):

```bash
python scripts/cli.py --help
python scripts/cli.py db init
python scripts/cli.py workspace dev
python scripts/cli.py release release-patch
```

1. Enable the alias via direnv. The provided `.envrc` defines:

```bash
alias cli="python scripts/cli.py"
```

With direnv enabled, you can run:

```bash
cli --help
cli db set-vars
cli workspace dev-stop
cli release sync-versions
```

Arguments and options work as usual with Typer, including `--option=value`.

## Troubleshooting

- Ensure Supabase CLI is installed and authenticated for cloud operations.
- Run `uv sync` after any dependency changes.
- For release automation, verify `gh` and `jq` are on PATH.
- If AI release notes are desired, set `OPENAI_API_KEY` or ensure
  `ollama list` shows an installed model.

## Real World Scenarios

### Problem: You want to synchronize all versions across the monorepo

You want every `package.json` and `pyproject.toml` to match the root version.

Solution:

```bash
# Ensure the root version is what you want (edit root package.json if needed)

# Sync all versions to the root version
uv run cli release sync-versions

# Optionally commit the changes
git add -A && git commit -m "chore: sync versions"
```

Notes:

- `sync-versions` reads the root `package.json` version; if not present,
  it defaults to `0.0.1`.
- To set a precise new version globally, first change the root version (or run
  a bump command like `uv run cli release bump-minor`), then run
  `sync-versions`.
