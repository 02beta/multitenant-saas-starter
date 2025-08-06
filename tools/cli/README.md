# CLI Tools

A collection of command-line interface tools for the multitenant SaaS starter project.

## Overview

This package provides CLI utilities to help with development and project management tasks, including database administration for Supabase projects.

## Installation

From the project root, run the following command to install the dependencies:

```bash
uv sync
```

Note, this will install the dependencies for the CLI tools, as well as all other python packages in the workspace.

## Usage

Make sure you have activated the virtual environment created by `uv` by running `uv venv`.

Enter the following command to see a list of available commands:

```bash
uv run cli --help
```

## Available Commands

### Database Commands

The CLI provides comprehensive database administration commands for Supabase projects:

```bash
# Initialize project with env files, start Supabase, and set vars
uv run cli db init

# Create new Supabase project in cloud and link it
uv run cli db create-new-project

# Ensure all required Supabase env vars are present in .env.local
uv run cli db set-vars

# Start Supabase (restarts if already running)
uv run cli db start

# Stop Supabase
uv run cli db stop

# Reset Supabase database (stops with reset and restarts)
uv run cli db reset-db
```

### Getting Help

To see help for any command:

```bash
# Main CLI help
uv run cli --help

# Database commands help
uv run cli db --help

# Specific command help
uv run cli db init --help
```

## Features

- **Project Initialization**: Set up Supabase environment files and configuration
- **Cloud Project Management**: Create and link Supabase cloud projects
- **Environment Variable Management**: Automatically sync database environment variables
- **Database Operations**: Start, stop, and reset local Supabase instances
- **Rich Output**: Beautiful console output with colors and formatting
