"""Tests for CLI validation and safety behavior."""

import sys
from pathlib import Path

from typer.testing import CliRunner

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) in sys.path:
    sys.path.remove(str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT))
sys.modules.pop("app", None)

from app.cli import app  # noqa: E402


def test_scan_rejects_malformed_urn_before_datahub_connection() -> None:
    result = CliRunner().invoke(app, ["scan", "not-a-urn"])

    assert result.exit_code != 0
    assert "Expected a DataHub URN" in result.output
