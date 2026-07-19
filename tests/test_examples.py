"""Tests for generated example artifacts."""

import json
from pathlib import Path


def test_sample_report_json_contains_findings() -> None:
    payload = json.loads(Path("examples/sample_report.json").read_text(encoding="utf-8"))

    assert payload["target_urn"].startswith("urn:li:mlModel")
    assert payload["findings"]


def test_sample_mcp_dryrun_contains_only_safe_tags() -> None:
    payload = json.loads(Path("examples/sample_mcp_dryrun.json").read_text(encoding="utf-8"))
    text = json.dumps(payload)

    assert "risk:schema-drift" in text
    assert "risk:missing-owner" in text
    assert "risk:stale-dataset" not in text
