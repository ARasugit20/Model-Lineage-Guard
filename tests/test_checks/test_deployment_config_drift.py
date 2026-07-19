"""Tests for the deployment config drift risk check."""

from typing import Any

from app.checks.deployment_config_drift import DeploymentConfigDriftCheck


def test_deployment_config_drift_fires_for_changed_instance(
    risky_context: dict[str, Any],
) -> None:
    deployment_urn = "urn:li:mlModelDeployment:(urn:li:dataPlatform:demo,credit_risk_prod,PROD)"
    risky_context["entities"][deployment_urn] = {
        "urn": deployment_urn,
        "dataset": {},
        "model": {},
        "deployment": {
            "customProperties": {
                "mlguard.expected_instance_type": "ml.m5.large",
                "mlguard.actual_instance_type": "ml.t3.medium",
            }
        },
        "owners": ["urn:li:corpuser:risk-platform-owner"],
        "schema": [],
    }

    findings = DeploymentConfigDriftCheck().run(risky_context)

    assert len(findings) == 1
    assert findings[0].evidence["actual_instance_type"] == "ml.t3.medium"


def test_deployment_config_drift_ignores_matching_instance(
    clean_context: dict[str, Any],
) -> None:
    deployment_urn = "urn:li:mlModelDeployment:(urn:li:dataPlatform:demo,credit_risk_prod,PROD)"
    clean_context["entities"][deployment_urn] = {
        "urn": deployment_urn,
        "dataset": {},
        "model": {},
        "deployment": {
            "customProperties": {
                "mlguard.expected_instance_type": "ml.m5.large",
                "mlguard.actual_instance_type": "ml.m5.large",
            }
        },
        "owners": ["urn:li:corpuser:risk-platform-owner"],
        "schema": [],
    }

    assert DeploymentConfigDriftCheck().run(clean_context) == []
