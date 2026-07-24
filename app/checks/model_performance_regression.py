"""Detect model performance regressions from evaluation metadata."""

from __future__ import annotations

from typing import Any

from app.checks.base import Check, entity_properties, lineage_entities_by_type
from app.findings import Finding, Severity


class ModelPerformanceRegressionCheck(Check):
    """Flag models whose current metric falls below their baseline."""

    name = "model_performance_regression"
    severity = Severity.HIGH

    def run(self, context: dict[str, Any]) -> list[Finding]:
        findings: list[Finding] = []
        for urn, entity in lineage_entities_by_type(context, "mlModel").items():
            props = entity_properties(entity)
            metric = props.get("mlguard.performance_metric")
            baseline = _float_or_none(props.get("mlguard.baseline_metric_value"))
            current = _float_or_none(props.get("mlguard.current_metric_value"))
            tolerance = _float_or_none(props.get("mlguard.performance_tolerance")) or 0.0
            if not metric or baseline is None or current is None:
                continue
            if current + tolerance >= baseline:
                continue
            findings.append(
                Finding(
                    check_name=self.name,
                    severity=self.severity,
                    title="Model performance regressed below baseline",
                    explanation=(
                        f"{urn} reports {metric}={current:.3f}, below baseline "
                        f"{baseline:.3f} with tolerance {tolerance:.3f}."
                    ),
                    evidence={
                        "entity_urn": urn,
                        "metric": metric,
                        "baseline": baseline,
                        "current": current,
                        "tolerance": tolerance,
                    },
                    entity_urn=urn,
                    remediation=(
                        "Review the latest evaluation slice, compare training and serving "
                        "data, and hold promotion until the metric returns to baseline."
                    ),
                )
            )
        return findings


def _float_or_none(value: str | None) -> float | None:
    if value is None:
        return None
    return float(value)
