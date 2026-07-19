"""Tests for CLI write-back safety flags."""

from typer.testing import CliRunner

from app.cli import app


def test_demo_report_rejects_apply_mode() -> None:
    result = CliRunner().invoke(
        app,
        ["demo-report", "--write-back", "apply"],
    )

    assert result.exit_code != 0
    assert "does not apply write-back" in result.output
