#!/usr/bin/env python
"""Development server for FastAPI with monorepo support."""

import os
import sys
from pathlib import Path

import uvicorn

# Setup paths
API_DIR = Path(__file__).parent
MONOREPO_ROOT = API_DIR.parent.parent

# Add monorepo root to Python path so imports work correctly
sys.path.insert(0, str(MONOREPO_ROOT))

# Change to monorepo root for consistent imports
os.chdir(MONOREPO_ROOT)

# Now import uvicorn after setting up paths


def main():
    """Run the development server with monorepo watching."""
    # Directories to watch for changes
    watch_dirs = [
        "apps/api",
        "libs/core",
        "libs/supabase-auth-provider",
    ]

    # Convert to absolute paths
    reload_dirs = [str(MONOREPO_ROOT / d) for d in watch_dirs]

    print("🚀 Starting FastAPI development server")
    print(f"📁 Working directory: {os.getcwd()}")
    print("👀 Watching directories:")
    for d in watch_dirs:
        print(f"   - {d}")
    print()

    # Run uvicorn with the correct module path
    uvicorn.run(
        "apps.api.main:app",  # Full module path from monorepo root
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8080")),
        reload=True,
        reload_dirs=reload_dirs,
        log_level="info",
        access_log=True,
    )


if __name__ == "__main__":
    main()
