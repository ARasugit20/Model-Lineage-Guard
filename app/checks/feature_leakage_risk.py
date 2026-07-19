"""Detect heuristic feature leakage risks from post-outcome fields or timestamps."""

from __future__ import annotations

from typing import Any

from app.checks.base import Check, contains_token, entity_properties, lineage_entities
from app.findings import Finding, Severity

POST_OUTCOME_TOKENS = (
    "chargeback_resolved",
    "resolved_at",
    "settled_at",
    "defaulted",
    "outcome",
    "label",
    "postdate",
)


class FeatureLeakageRiskCheck(Check):
    """Flag features that appear to use fields only known after the label event."""

    name = "feature_leakage_risk"
    severity = Severity.HIGH

    def run(self, context: dict[str, Any]) -> list[Finding]:
        findings: list[Finding] = []
        for urn, entity in lineage_entities(context).items():
            props = entity_properties(entity)
            explicit = props.get("mlguard.leakage_candidate", "").lower() == "true"
            evidence = props.get("mlguard.leakage_evidence")
            suspicious_fields = _suspicious_fields(entity)

            if not explicit and not suspicious_fields:
                continue

            findings.append(
                Finding(
                    check_name=self.name,
                    severity=self.severity,
                    title="Feature may use post-outcome information",
                    explanation=(
                        f"{urn} contains feature evidence that may be known only after the "
                        "prediction label is determined."
                    ),
                    evidence={
                        "entity_urn": urn,
                        "leakage_evidence": evidence,
                        "suspicious_fields": suspicious_fields,
                    },
                    entity_urn=urn,
                    remediation=(
                        "Human review required: confirm the feature is available at "
                        "prediction time or remove it from model training."
                    ),
                )
            )
        return findings


def _suspicious_fields(entity: dict[str, Any]) -> list[str]:
    fields: list[str] = []
    for field in entity.get("schema", []) or []:
        field_text = f"{field.get('fieldPath', '')} {field.get('description', '')}"
        if contains_token(field_text, *POST_OUTCOME_TOKENS):
            fields.append(str(field.get("fieldPath")))
    for aspect_name in ("model", "dataset", "deployment"):
        aspect = entity.get(aspect_name) or {}
        if contains_token(aspect.get("description", ""), *POST_OUTCOME_TOKENS):
            fields.append("description")
    return sorted(set(fields))
