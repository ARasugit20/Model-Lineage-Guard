"""Tests for the deterministic demo scan context."""

from app.checks import run_checks
from app.demo_context import MODEL_URN, demo_scan_context


def test_demo_context_triggers_all_core_checks() -> None:
    findings = run_checks(demo_scan_context())

    assert {finding.check_name for finding in findings} == {
        "schema_drift",
        "pii_exposure",
        "stale_dataset",
        "missing_owner",
        "feature_leakage_risk",
        "model_performance_regression",
        "deployment_config_drift",
    }


def test_demo_context_targets_credit_risk_model() -> None:
    assert demo_scan_context()["target_urn"] == MODEL_URN
