"""Write risk findings back to DataHub metadata."""

from app.findings import Finding


def write_findings(findings: list[Finding]) -> None:
    """Phase 4 will emit DataHub MetadataChangeProposals for findings."""
    _ = findings
