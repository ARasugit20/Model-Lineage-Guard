"""Write risk findings back to DataHub metadata."""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from datahub.emitter.mce_builder import make_tag_urn
from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.metadata.schema_classes import GlobalTagsClass, TagAssociationClass

from app.datahub_client import DataHubClient
from app.findings import Finding, RiskReport

_RISK_TAGS = {
    "schema_drift": "risk:schema-drift",
    "pii_exposure": "risk:pii-exposure",
    "missing_owner": "risk:missing-owner",
}
_HUMAN_REVIEW_ONLY = {"stale_dataset", "feature_leakage_risk"}


def is_writeback_safe(finding: Finding) -> bool:
    """Return whether a finding has a safe audit tag write-back."""
    return finding.check_name in _RISK_TAGS and finding.check_name not in _HUMAN_REVIEW_ONLY


def human_review_findings(report: RiskReport) -> list[Finding]:
    """Return findings intentionally excluded from automated write-back."""
    return [finding for finding in report.findings if not is_writeback_safe(finding)]


def build_mcps(report: RiskReport) -> list[MetadataChangeProposalWrapper]:
    """Build DataHub tag MCPs for findings with safe, well-defined write-back."""
    mcps: list[MetadataChangeProposalWrapper] = []
    for finding in report.findings:
        if not is_writeback_safe(finding):
            continue
        entity_urn = finding.entity_urn or report.target_urn
        tag_name = _RISK_TAGS[finding.check_name]
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


def apply(client: DataHubClient, mcps: Iterable[MetadataChangeProposalWrapper]) -> list[str]:
    """Emit DataHub MetadataChangeProposals through the configured SDK graph."""
    emitted: list[str] = []
    for mcp in mcps:
        client.graph.emit_mcp(mcp)
        emitted.append(str(mcp.entityUrn))
    return emitted
