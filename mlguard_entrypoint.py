"""Console-script shim that resolves this repository's app package first."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# The path shim above must run before importing the local app package.
from app.cli import app  # noqa: E402

__all__ = ["app"]
