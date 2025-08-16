"""
Script to launch FastAPI in production mode using Gunicorn with Uvicorn workers.

Usage:
    uv run python apps/api/start.py
    -or-
    pnpm run start

This script will start the FastAPI application using Gunicorn with 4 Uvicorn
workers, binding to 0.0.0.0:8080.
"""

import os
import subprocess
import sys


class GunicornConfig:
    """Gunicorn configuration for running FastAPI with Uvicorn workers."""

    # dynamically calculate the number of workers
    workers = os.cpu_count() * 2 + 1

    # Worker class to use (Uvicorn worker for ASGI) required for FastAPI
    worker_class = "uvicorn.workers.UvicornWorker"

    # Bind address and port
    bind = "0.0.0.0:8080"

    # Application entrypoint
    app_module = "api.main:app"

    @classmethod
    def to_cmd(cls):
        """Return the Gunicorn command as a list suitable for subprocess."""
        return [
            "gunicorn",
            cls.app_module,
            "--workers",
            str(cls.workers),
            "--worker-class",
            cls.worker_class,
            "--bind",
            cls.bind,
        ]


def main():
    """Launch FastAPI app in production mode with Gunicorn and Uvicorn workers."""
    cmd = GunicornConfig.to_cmd()
    sys.exit(subprocess.call(cmd))


if __name__ == "__main__":
    main()
