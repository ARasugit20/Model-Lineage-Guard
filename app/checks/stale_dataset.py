"""Detect stale upstream datasets feeding production ML lineage paths."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.checks.base import Check, entity_properties, lineage_entities
from app.findings import Finding, Severity


class StaleDatasetCheck(Check):
    """Flag datasets that have exceeded their expected refresh cadence."""

    name = "stale_dataset"
    severity = Severity.HIGH

    def run(self, context: dict[str, Any]) -> list[Finding]:
        scan_time = _parse_time(context.get("scan_started_at")) or datetime.now(UTC)
        findings: list[Finding] = []
        for urn, entity in lineage_entities(context).items():
            props = entity_properties(entity)
            cadence = props.get("mlguard.expected_cadence_hours")
            refreshed = _parse_time(props.get("mlguard.last_refreshed_at"))
            if not cadence or not refreshed:
                continue
            age_hours = (scan_time - refreshed).total_seconds() / 3600
            cadence_hours = float(cadence)
            if age_hours <= cadence_hours:
                continue
            findings.append(
                Finding(
                    check_name=self.name,
                    severity=self.severity,
                    title="Upstream dataset is stale for its declared cadence",
                    explanation=(
                        f"{urn} was last refreshed {age_hours:.1f} hours before the scan, "
                        f"exceeding its {cadence_hours:.1f} hour cadence."
                    ),
                    evidence={
                        "entity_urn": urn,
                        "last_refreshed_at": props.get("mlguard.last_refreshed_at"),
                        "expected_cadence_hours": cadence_hours,
                        "observed_age_hours": round(age_hours, 2),
                    },
                    entity_urn=urn,
                )
            )
        return findings


def _parse_time(value: Any) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(UTC)
