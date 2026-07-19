"""Tests for the model performance regression risk check."""

from typing import Any

from app.checks.model_performance_regression import ModelPerformanceRegressionCheck


def test_model_performance_regression_fires_for_metric_drop(
    risky_context: dict[str, Any],
) -> None:
    model = risky_context["entities"][risky_context["target_urn"]]["model"]
    model["customProperties"].update(
        {
            "mlguard.performance_metric": "auc",
            "mlguard.baseline_metric_value": "0.89",
            "mlguard.current_metric_value": "0.84",
            "mlguard.performance_tolerance": "0.01",
        }
    )

    findings = ModelPerformanceRegressionCheck().run(risky_context)

    assert len(findings) == 1
    assert findings[0].evidence["metric"] == "auc"


def test_model_performance_regression_ignores_healthy_metric(
    clean_context: dict[str, Any],
) -> None:
    model = clean_context["entities"][clean_context["target_urn"]]["model"]
    model["customProperties"].update(
        {
            "mlguard.performance_metric": "auc",
            "mlguard.baseline_metric_value": "0.89",
            "mlguard.current_metric_value": "0.885",
            "mlguard.performance_tolerance": "0.01",
        }
    )

    assert ModelPerformanceRegressionCheck().run(clean_context) == []
