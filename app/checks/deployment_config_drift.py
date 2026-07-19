"""Detect production deployment config drift from last known-good metadata."""

from __future__ import annotations

from typing import Any

from app.checks.base import Check, entity_properties, lineage_entities
from app.findings import Finding, Severity


class DeploymentConfigDriftCheck(Check):
    """Flag deployment metadata that differs from last known-good config."""

    name = "deployment_config_drift"
    severity = Severity.MEDIUM

    def run(self, context: dict[str, Any]) -> list[Finding]:
        findings: list[Finding] = []
        for urn, entity in lineage_entities(context).items():
            props = entity_properties(entity)
            expected = props.get("mlguard.expected_instance_type")
            actual = props.get("mlguard.actual_instance_type")
            if not expected or not actual or expected == actual:
                continue
            findings.append(
                Finding(
                    check_name=self.name,
                    severity=self.severity,
                    title="Deployment config drift detected",
                    explanation=(
                        f"{urn} is running on {actual}, but last known-good config "
                        f"expects {expected}."
                    ),
                    evidence={
                        "entity_urn": urn,
                        "expected_instance_type": expected,
                        "actual_instance_type": actual,
                    },
                    entity_urn=urn,
                    remediation=(
                        "Compare the deployment change history, confirm the instance "
                        "change was approved, or roll back to the last known-good config."
                    ),
                )
            )
        return findings
