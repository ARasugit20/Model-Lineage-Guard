"""Tests for report and finding serialization."""

import json

from app.findings import Finding, RiskReport, Severity


def test_finding_serializes_severity_as_string() -> None:
    finding = Finding(
        check_name="schema_drift",
        severity=Severity.HIGH,
        title="Schema changed",
        explanation="A source column changed type.",
        evidence={"column": "customer_id"},
        entity_urn="urn:li:dataset:(demo,raw,PROD)",
        remediation="Recompute downstream features.",
    )

    assert finding.to_dict() == {
        "check_name": "schema_drift",
        "severity": "high",
        "title": "Schema changed",
        "explanation": "A source column changed type.",
        "evidence": {"column": "customer_id"},
        "entity_urn": "urn:li:dataset:(demo,raw,PROD)",
        "remediation": "Recompute downstream features.",
    }


def test_risk_report_json_round_trip() -> None:
    report = RiskReport(
        target_urn="urn:li:mlModel:(demo,credit_risk_v3,PROD)",
        scan_started_at="2026-07-18T12:00:00+00:00",
        findings=[
            Finding(
                check_name="missing_owner",
                severity=Severity.MEDIUM,
                title="Missing owner",
                explanation="A feature table has no owner.",
                entity_urn="urn:li:mlFeatureTable:(demo,user_risk_features)",
            )
        ],
        lineage={"upstream": [{"urn": "urn:li:dataset:(demo,raw,PROD)"}]},
    )

    payload = json.loads(report.to_json())

    assert payload["target_urn"] == "urn:li:mlModel:(demo,credit_risk_v3,PROD)"
    assert payload["summary"]["medium"] == 1
    assert payload["findings"][0]["severity"] == "medium"
    assert payload["lineage"]["upstream"][0]["urn"] == "urn:li:dataset:(demo,raw,PROD)"
