"""Detect upstream schema changes that downstream ML assets have not consumed."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.checks.base import Check, entity_properties, lineage_entities_by_type
from app.findings import Finding, Severity


class SchemaDriftCheck(Check):
    """Flag upstream schema changes that downstream features have not consumed."""

    name = "schema_drift"
    severity = Severity.HIGH

    def run(self, context: dict[str, Any]) -> list[Finding]:
        changed_sources = [
            (urn, entity, entity_properties(entity))
            for urn, entity in lineage_entities_by_type(context, "dataset").items()
            if entity_properties(entity).get("mlguard.schema_change")
        ]
        consumers = [
            (urn, entity, entity_properties(entity))
            for urn, entity in lineage_entities_by_type(
                context,
                "mlFeatureTable",
                "mlFeature",
                "mlModel",
            ).items()
            if entity_properties(entity).get("mlguard.expected_upstream_schema")
        ]

        consumers_with_recompute_time = [
            (
                consumer_urn,
                consumer_props,
                _parse_time(consumer_props.get("mlguard.last_recomputed_at")),
            )
            for consumer_urn, _consumer, consumer_props in consumers
        ]

        findings: list[Finding] = []
        for source_urn, _source, source_props in changed_sources:
            changed_at = _parse_time(source_props.get("mlguard.schema_changed_at"))
            for consumer_urn, consumer_props, recomputed_at in consumers_with_recompute_time:
                if changed_at and recomputed_at and recomputed_at >= changed_at:
                    continue
                findings.append(
                    Finding(
                        check_name=self.name,
                        severity=self.severity,
                        title="Upstream schema changed after feature computation",
                        explanation=(
                            f"Upstream {source_urn} changed schema "
                            f"({source_props['mlguard.schema_change']}); {consumer_urn} "
                            "has not recorded a recomputation after that change."
                        ),
                        evidence={
                            "upstream_urn": source_urn,
                            "downstream_urn": consumer_urn,
                            "schema_change": source_props["mlguard.schema_change"],
                            "schema_changed_at": source_props.get("mlguard.schema_changed_at"),
                            "last_recomputed_at": consumer_props.get("mlguard.last_recomputed_at"),
                        },
                        entity_urn=consumer_urn,
                        remediation=(
                            "Recompute the downstream feature table after validating the upstream "
                            "schema change, then update the expected schema metadata."
                        ),
                    )
                )
        return findings


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
