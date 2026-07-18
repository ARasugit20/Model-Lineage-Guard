"""Tests for the feature leakage risk check."""

from typing import Any

from app.checks.feature_leakage_risk import FeatureLeakageRiskCheck


def test_feature_leakage_fires_for_post_outcome_feature(risky_context: dict[str, Any]) -> None:
    findings = FeatureLeakageRiskCheck().run(risky_context)

    assert findings
    assert any("chargeback_resolved_at" in str(finding.evidence) for finding in findings)


def test_feature_leakage_does_not_fire_for_clean_features(clean_context: dict[str, Any]) -> None:
    assert FeatureLeakageRiskCheck().run(clean_context) == []
