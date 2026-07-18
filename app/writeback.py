"""Write risk findings back to DataHub metadata."""

from collections.abc import Iterable

from datahub.emitter.mce_builder import make_tag_urn
from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.metadata.schema_classes import GlobalTagsClass, TagAssociationClass

from app.datahub_client import DataHubClient
from app.findings import RiskReport

_RISK_TAGS = {
    "schema_drift": "risk:schema-drift",
    "pii_exposure": "risk:pii-exposure",
    "stale_dataset": "risk:stale-dataset",
    "missing_owner": "risk:missing-owner",
    "feature_leakage_risk": "risk:feature-leakage",
}


def build_mcps(report: RiskReport) -> list[MetadataChangeProposalWrapper]:
    """Build DataHub tag MCPs for every finding in a report."""
    mcps: list[MetadataChangeProposalWrapper] = []
    for finding in report.findings:
        entity_urn = finding.entity_urn or report.target_urn
        tag_name = _RISK_TAGS.get(finding.check_name, f"risk:{finding.check_name}")
        aspect = GlobalTagsClass(tags=[TagAssociationClass(tag=make_tag_urn(tag_name))])
        mcps.append(MetadataChangeProposalWrapper(entityUrn=entity_urn, aspect=aspect))
    return mcps


def apply(client: DataHubClient, mcps: Iterable[MetadataChangeProposalWrapper]) -> None:
    """Emit DataHub MetadataChangeProposals through the configured SDK graph."""
    for mcp in mcps:
        client.graph.emit_mcp(mcp)
