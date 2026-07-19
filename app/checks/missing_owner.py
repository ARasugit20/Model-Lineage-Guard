"""Detect datasets and ML assets in the lineage path with no registered owner."""

from __future__ import annotations

from typing import Any

from app.checks.base import Check, lineage_entities
from app.findings import Finding, Severity


class MissingOwnerCheck(Check):
    """Flag lineage entities with no registered owner in DataHub."""

    name = "missing_owner"
    severity = Severity.MEDIUM

    def run(self, context: dict[str, Any]) -> list[Finding]:
        findings: list[Finding] = []
        for urn, entity in lineage_entities(context).items():
            owners = entity.get("owners") or []
            if owners:
                continue
            findings.append(
                Finding(
                    check_name=self.name,
                    severity=self.severity,
                    title="Lineage entity has no registered owner",
                    explanation=(
                        f"{urn} appears in the scanned lineage path but has no DataHub owner."
                    ),
                    evidence={"entity_urn": urn, "owners": []},
                    entity_urn=urn,
                    remediation="Assign a DataHub owner for this lineage entity.",
                )
            )
        return findings
