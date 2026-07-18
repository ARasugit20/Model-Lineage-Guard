"""Tests for report rendering."""

import json

from app.findings import Finding, RiskReport, Severity
from app.report import render_html, render_json


def test_render_json_writes_report_file(tmp_path) -> None:
    report = RiskReport(
        target_urn="urn:li:mlModel:(demo,credit_risk_v3,PROD)",
        scan_started_at="2026-07-18T12:00:00+00:00",
        findings=[
            Finding(
                check_name="schema_drift",
                severity=Severity.HIGH,
                title="Schema drift",
                explanation="customer_id changed type.",
            )
        ],
    )

    path = render_json(report, tmp_path)
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert path.name == "report.json"
    assert payload["target_urn"] == report.target_urn
    assert payload["findings"][0]["check_name"] == "schema_drift"


def test_render_html_writes_graph_report(tmp_path) -> None:
    report = RiskReport(
        target_urn="urn:li:mlModel:(demo,credit_risk_v3,PROD)",
        scan_started_at="2026-07-18T12:00:00+00:00",
        findings=[
            Finding(
                check_name="missing_owner",
                severity=Severity.MEDIUM,
                title="Missing owner",
                explanation="Feature table has no owner.",
                entity_urn="urn:li:mlFeatureTable:(demo,user_risk_features)",
            )
        ],
    )
    lineage = {
        "upstream": [
            {
                "source_urn": report.target_urn,
                "urn": "urn:li:mlFeatureTable:(demo,user_risk_features)",
            }
        ],
        "downstream": [],
    }

    path = render_html(report, lineage, tmp_path)
    html = path.read_text(encoding="utf-8")

    assert path.name == "report.html"
    assert "vis-network" in html
    assert "Model Lineage Guard" in html
    assert "Missing owner" in html
