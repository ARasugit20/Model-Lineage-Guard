"""Tests for DataHub write-back MCP construction."""

from unittest.mock import Mock

from app.findings import Finding, RiskReport, Severity
from app.writeback import apply, build_mcps


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
