"""Detect sensitive or PII columns flowing into model feature sets without approval."""

from __future__ import annotations

from typing import Any

from app.checks.base import Check, contains_token, entity_properties, lineage_entities
from app.findings import Finding, Severity


class PiiExposureCheck(Check):
    """Flag sensitive columns flowing into model lineage without an approved exception."""

    name = "pii_exposure"
    severity = Severity.CRITICAL

    def run(self, context: dict[str, Any]) -> list[Finding]:
        findings: list[Finding] = []
        for urn, entity in lineage_entities(context).items():
            props = entity_properties(entity)
            if props.get("mlguard.pii_exception_approved", "").lower() == "true":
                continue

            pii_columns = _pii_columns(entity)
            configured_column = props.get("mlguard.pii_column")
            if configured_column:
                pii_columns.append(configured_column)

            if props.get("mlguard.contains_unapproved_pii", "").lower() == "true" or pii_columns:
                findings.append(
                    Finding(
                        check_name=self.name,
                        severity=self.severity,
                        title="PII flows into model lineage without an approved exception",
                        explanation=(
                            f"{urn} exposes sensitive field evidence in the scanned model lineage "
                            "and no approved exception was found."
                        ),
                        evidence={
                            "entity_urn": urn,
                            "columns": sorted(set(pii_columns)),
                            "approved_exception": False,
                        },
                        entity_urn=urn,
                        remediation=(
                            "Remove the sensitive field from the feature set or attach an approved "
                            "PII exception in DataHub before production use."
                        ),
                    )
                )
        return findings


def _pii_columns(entity: dict[str, Any]) -> list[str]:
    columns: list[str] = []
    for field in entity.get("schema", []) or []:
        haystack = {
            "name": field.get("fieldPath"),
            "description": field.get("description"),
            "tags": field.get("globalTags"),
            "terms": field.get("glossaryTerms"),
        }
        if any(contains_token(value, "pii", "sensitive") for value in haystack.values()):
            columns.append(str(field.get("fieldPath")))
    return columns
