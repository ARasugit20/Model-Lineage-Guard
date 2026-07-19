"""Write risk findings back to DataHub metadata."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from datahub.emitter.mce_builder import make_tag_urn
from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.metadata.schema_classes import GlobalTagsClass, TagAssociationClass

from app.datahub_client import DataHubClient
from app.findings import Finding, RiskReport, Severity

DEFAULT_POLICY_PATH = Path(__file__).resolve().parents[1] / "config" / "writeback_policy.json"
DEFAULT_POLICY: dict[str, Any] = {
    "minimum_severity": "medium",
    "allowed_entity_types": ["dataset", "mlFeatureTable", "mlModel", "mlModelDeployment"],
    "checks": {
        "schema_drift": {"mode": "auto_apply", "tag": "risk:schema-drift"},
        "pii_exposure": {"mode": "auto_apply", "tag": "risk:pii-exposure"},
        "missing_owner": {"mode": "auto_apply", "tag": "risk:missing-owner"},
        "stale_dataset": {"mode": "human_review_only", "tag": "risk:stale-dataset"},
        "feature_leakage_risk": {
            "mode": "human_review_only",
            "tag": "risk:feature-leakage",
        },
        "model_performance_regression": {
            "mode": "human_review_only",
            "tag": "risk:model-performance-regression",
        },
        "deployment_config_drift": {
            "mode": "human_review_only",
            "tag": "risk:deployment-config-drift",
        },
    },
}
_SEVERITY_ORDER = {
    Severity.LOW: 0,
    Severity.MEDIUM: 1,
    Severity.HIGH: 2,
    Severity.CRITICAL: 3,
}


@dataclass(frozen=True)
class CheckPolicy:
    """Write-back behavior for one check."""

    mode: str
    tag: str


@dataclass(frozen=True)
class WriteBackPolicy:
    """Policy controlling which findings produce DataHub MCPs."""

    minimum_severity: Severity
    allowed_entity_types: set[str]
    checks: dict[str, CheckPolicy]

    @classmethod
    def load(cls, path: Path = DEFAULT_POLICY_PATH) -> WriteBackPolicy:
        payload = json.loads(path.read_text(encoding="utf-8")) if path.exists() else DEFAULT_POLICY
        return cls(
            minimum_severity=Severity(payload.get("minimum_severity", Severity.MEDIUM.value)),
            allowed_entity_types=set(payload.get("allowed_entity_types", [])),
            checks={
                name: CheckPolicy(mode=str(value["mode"]), tag=str(value["tag"]))
                for name, value in payload.get("checks", {}).items()
            },
        )


def is_writeback_safe(finding: Finding, policy: WriteBackPolicy | None = None) -> bool:
    """Return whether a finding has a safe audit tag write-back."""
    active_policy = policy or WriteBackPolicy.load()
    check_policy = active_policy.checks.get(finding.check_name)
    if not check_policy or check_policy.mode != "auto_apply":
        return False
    return _SEVERITY_ORDER[finding.severity] >= _SEVERITY_ORDER[active_policy.minimum_severity]


def human_review_findings(
    report: RiskReport, policy: WriteBackPolicy | None = None
) -> list[Finding]:
    """Return findings intentionally excluded from automated write-back."""
    active_policy = policy or WriteBackPolicy.load()
    return [finding for finding in report.findings if not is_writeback_safe(finding, active_policy)]


def build_mcps(
    report: RiskReport, policy: WriteBackPolicy | None = None
) -> list[MetadataChangeProposalWrapper]:
    """Build DataHub tag MCPs for findings with safe, well-defined write-back."""
    active_policy = policy or WriteBackPolicy.load()
    mcps: list[MetadataChangeProposalWrapper] = []
    for finding in report.findings:
        if not is_writeback_safe(finding, active_policy):
            continue
        entity_urn = finding.entity_urn or report.target_urn
        entity_type = _entity_type(entity_urn)
        if entity_type not in active_policy.allowed_entity_types:
            continue
        tag_name = active_policy.checks[finding.check_name].tag
        aspect = GlobalTagsClass(tags=[TagAssociationClass(tag=make_tag_urn(tag_name))])
        mcps.append(MetadataChangeProposalWrapper(entityUrn=entity_urn, aspect=aspect))
    return mcps


def mcps_to_dicts(mcps: Iterable[MetadataChangeProposalWrapper]) -> list[dict[str, Any]]:
    """Return JSON-serializable DataHub MCP payloads."""
    return [dict(mcp.to_obj()) for mcp in mcps]


def render_mcp_json(mcps: Iterable[MetadataChangeProposalWrapper], out_dir: Path) -> Path:
    """Write dry-run MCP JSON for inspection."""
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "mcp_dryrun.json"
    path.write_text(json.dumps(mcps_to_dicts(mcps), indent=2, default=str), encoding="utf-8")
    return path


def write_audit_log(
    *,
    mcps: Iterable[MetadataChangeProposalWrapper],
    out_dir: Path,
    mode: str,
    outcome: str,
) -> Path:
    """Append JSONL audit records for write-back decisions."""
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "writeback_audit.jsonl"
    timestamp = datetime.now(UTC).isoformat()
    with path.open("a", encoding="utf-8") as audit_file:
        for mcp in mcps:
            audit_file.write(
                json.dumps(
                    {
                        "timestamp": timestamp,
                        "entity_urn": mcp.entityUrn,
                        "aspect": mcp.aspectName,
                        "mode": mode,
                        "outcome": outcome,
                    },
                    sort_keys=True,
                )
                + "\n"
            )
    return path


def apply(
    client: DataHubClient,
    mcps: Iterable[MetadataChangeProposalWrapper],
    *,
    audit_dir: Path | None = None,
) -> list[str]:
    """Emit DataHub MetadataChangeProposals through the configured SDK graph."""
    emitted: list[str] = []
    for mcp in mcps:
        try:
            client.graph.emit_mcp(mcp)
        except Exception:
            if audit_dir:
                write_audit_log(mcps=[mcp], out_dir=audit_dir, mode="apply", outcome="failed")
            raise
        else:
            emitted.append(str(mcp.entityUrn))
            if audit_dir:
                write_audit_log(mcps=[mcp], out_dir=audit_dir, mode="apply", outcome="sent")
    return emitted


def _entity_type(urn: str) -> str:
    parts = urn.split(":")
    return parts[2] if len(parts) > 2 else ""
