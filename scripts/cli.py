#!/usr/bin/env python3
"""
Convenience script to run the CLI from the project root.

This script allows you to run the CLI commands directly from the project root
using uv run to ensure the correct environment.
"""

import subprocess
import sys
from pathlib import Path


def main():
    """Run the CLI using uv run."""
    # Get the project root directory
    project_root = Path(__file__).parent.parent

    # Build the command to run the CLI
    cmd = ["uv", "run", "cli"] + sys.argv[1:]

    # Run the command
    try:
        subprocess.run(cmd, cwd=project_root, check=True)
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        sys.exit(1)


if __name__ == "__main__":
    main()
