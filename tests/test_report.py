"""Tests for report rendering."""

import json

from app.findings import Finding, RiskReport, Severity
from app.report import _build_graph, render_html, render_json, render_markdown


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
                remediation="Assign an owner.",
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

    path = render_html(
        report,
        lineage,
        tmp_path,
        mcp_payloads=[{"entityUrn": "urn:li:mlFeatureTable:(demo,user_risk_features)"}],
        datahub_base_url="http://localhost:9002",
    )
    html = path.read_text(encoding="utf-8")

    assert path.name == "report.html"
    assert "vis-network" in html
    assert "Model Lineage Guard" in html
    assert "Missing owner" in html
    assert "severity-filter" in html
    assert "Remediation" in html
    assert "Open in DataHub" in html
    assert "Write-Back MCP Preview" in html


def test_render_markdown_writes_pr_comment(tmp_path) -> None:
    report = RiskReport(
        target_urn="urn:li:mlModel:(demo,credit_risk_v3,PROD)",
        scan_started_at="2026-07-18T12:00:00+00:00",
        findings=[
            Finding(
                check_name="pii_exposure",
                severity=Severity.CRITICAL,
                title="PII exposure",
                explanation="Email flows into features.",
                entity_urn="urn:li:mlFeatureTable:(demo,user_risk_features)",
            )
        ],
    )

    path = render_markdown(report, tmp_path)
    markdown = path.read_text(encoding="utf-8")

    assert path.name == "pr_comment.md"
    assert "1 finding(s)" in markdown
    assert "| Severity | Check | Entity | Finding |" in markdown
    assert "pii_exposure" in markdown
    assert "Write-back: off" in markdown


def test_build_graph_memoizes_and_returns_mutation_safe_copy(monkeypatch) -> None:
    report = RiskReport(target_urn="urn:li:mlModel:(demo,credit_risk_v3,PROD)")
    lineage = {
        "upstream": [{"source_urn": report.target_urn, "urn": "urn:li:dataset:(demo,raw,PROD)"}],
        "downstream": [],
    }
    calls: list[str] = []

    def node_payload(urn, target, findings):
        del target, findings
        calls.append(urn)
        return {"id": urn}

    monkeypatch.setattr("app.report._node_payload", node_payload)

    first = _build_graph(report, lineage)
    first["nodes"].append({"id": "mutated"})
    second = _build_graph(report, lineage)

    assert calls == [
        "urn:li:dataset:(demo,raw,PROD)",
        "urn:li:mlModel:(demo,credit_risk_v3,PROD)",
    ]
    assert {"id": "mutated"} not in second["nodes"]
