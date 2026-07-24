"""Tests for CLI validation and safety behavior."""

import importlib
import sys
from pathlib import Path
from typing import Any

from typer.testing import CliRunner

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) in sys.path:
    sys.path.remove(str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT))
sys.modules.pop("app", None)

cli_module = importlib.import_module("app.cli")
app = cli_module.app


def test_scan_rejects_malformed_urn_before_datahub_connection() -> None:
    result = CliRunner().invoke(app, ["scan", "not-a-urn"])

    assert result.exit_code != 0
    assert "Expected a DataHub URN" in result.output


def test_scan_all_caps_model_scans_before_loading_context(monkeypatch, tmp_path) -> None:
    scanned: list[str] = []

    class FakeSettings:
        gms_host = "http://example"

    class FakeClient:
        settings = FakeSettings()

        def list_ml_models(self) -> list[str]:
            return ["model-a", "model-b", "model-c"]

    def load_scan_context(
        client: FakeClient,
        urn: str,
        *,
        upstream_depth: int,
        max_breadth: int,
    ) -> dict[str, Any]:
        del client, upstream_depth, max_breadth
        scanned.append(urn)
        return {"target_urn": urn, "lineage": {}, "scan_started_at": "now"}

    def complete_scan(**kwargs: Any) -> None:
        del kwargs

    monkeypatch.setattr(cli_module, "DataHubClient", FakeClient)
    monkeypatch.setattr(cli_module, "_load_scan_context", load_scan_context)
    monkeypatch.setattr(cli_module, "_complete_scan", complete_scan)

    result = CliRunner().invoke(
        app,
        ["scan-all", "--max-downstream", "2", "--out", str(tmp_path)],
    )

    assert result.exit_code == 0
    assert "Warning: scan-all found 3 model(s); scanning first 2" in result.output
    assert scanned == ["model-a", "model-b"]
