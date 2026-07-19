"""Tests for DataHub write-back MCP construction."""

from unittest.mock import Mock

from app.findings import Finding, RiskReport, Severity
from app.writeback import (
    WriteBackPolicy,
    apply,
    build_mcps,
    human_review_findings,
    render_mcp_json,
    write_audit_log,
)


def test_build_mcps_maps_findings_to_risk_tags() -> None:
    report = RiskReport(
        target_urn="urn:li:mlModel:(demo,credit_risk_v3,PROD)",
        findings=[
            Finding(
                check_name="schema_drift",
                severity=Severity.HIGH,
                title="Schema drift",
                explanation="customer_id changed.",
                entity_urn="urn:li:mlFeatureTable:(demo,user_risk_features)",
            ),
            Finding(
                check_name="pii_exposure",
                severity=Severity.CRITICAL,
                title="PII exposure",
                explanation="Email flows into features.",
            ),
        ],
    )

    mcps = build_mcps(report)

    assert len(mcps) == 2
    assert mcps[0].entityUrn == "urn:li:mlFeatureTable:(demo,user_risk_features)"
    assert mcps[1].entityUrn == report.target_urn
    assert mcps[0].aspect.tags[0].tag == "urn:li:tag:risk:schema-drift"
    assert mcps[1].aspect.tags[0].tag == "urn:li:tag:risk:pii-exposure"


def test_build_mcps_uses_policy_threshold(tmp_path) -> None:
    policy_path = tmp_path / "policy.json"
    policy_path.write_text(
        """
        {
          "minimum_severity": "critical",
          "allowed_entity_types": ["mlModel"],
          "checks": {
            "missing_owner": {"mode": "auto_apply", "tag": "risk:missing-owner"}
          }
        }
        """,
        encoding="utf-8",
    )
    report = RiskReport(
        target_urn="urn:li:mlModel:(demo,credit_risk_v3,PROD)",
        findings=[
            Finding(
                check_name="missing_owner",
                severity=Severity.MEDIUM,
                title="Missing owner",
                explanation="No owner.",
            )
        ],
    )

    assert build_mcps(report, WriteBackPolicy.load(policy_path)) == []


def test_apply_emits_every_mcp() -> None:
    client = Mock()
    report = RiskReport(
        target_urn="urn:li:mlModel:(demo,credit_risk_v3,PROD)",
        findings=[
            Finding(
                check_name="missing_owner",
                severity=Severity.MEDIUM,
                title="Missing owner",
                explanation="No owner.",
            )
        ],
    )
    mcps = build_mcps(report)

    apply(client, mcps)

    client.graph.emit_mcp.assert_called_once_with(mcps[0])


def test_human_review_findings_are_excluded_from_writeback() -> None:
    report = RiskReport(
        target_urn="urn:li:mlModel:(demo,credit_risk_v3,PROD)",
        findings=[
            Finding(
                check_name="stale_dataset",
                severity=Severity.HIGH,
                title="Stale data",
                explanation="Refresh SLA missed.",
            ),
            Finding(
                check_name="feature_leakage_risk",
                severity=Severity.HIGH,
                title="Leakage risk",
                explanation="Feature may be post-outcome.",
            ),
        ],
    )

    assert build_mcps(report) == []
    assert [finding.check_name for finding in human_review_findings(report)] == [
        "stale_dataset",
        "feature_leakage_risk",
    ]


def test_render_mcp_json_writes_dry_run_without_emitting(tmp_path) -> None:
    client = Mock()
    report = RiskReport(
        target_urn="urn:li:mlModel:(demo,credit_risk_v3,PROD)",
        findings=[
            Finding(
                check_name="missing_owner",
                severity=Severity.MEDIUM,
                title="Missing owner",
                explanation="No owner.",
            )
        ],
    )

    path = render_mcp_json(build_mcps(report), tmp_path)

    assert "risk:missing-owner" in path.read_text(encoding="utf-8")
    client.graph.emit_mcp.assert_not_called()


def test_write_audit_log_records_writeback_decisions(tmp_path) -> None:
    report = RiskReport(
        target_urn="urn:li:mlModel:(demo,credit_risk_v3,PROD)",
        findings=[
            Finding(
                check_name="missing_owner",
                severity=Severity.MEDIUM,
                title="Missing owner",
                explanation="No owner.",
            )
        ],
    )

    path = write_audit_log(
        mcps=build_mcps(report),
        out_dir=tmp_path,
        mode="dry-run",
        outcome="previewed",
    )

    text = path.read_text(encoding="utf-8")
    assert "previewed" in text
    assert "globalTags" in text
