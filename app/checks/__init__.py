"""Risk checks for DataHub ML lineage scans."""

from typing import Any

from app.checks.deployment_config_drift import DeploymentConfigDriftCheck
from app.checks.feature_leakage_risk import FeatureLeakageRiskCheck
from app.checks.missing_owner import MissingOwnerCheck
from app.checks.model_performance_regression import ModelPerformanceRegressionCheck
from app.checks.pii_exposure import PiiExposureCheck
from app.checks.schema_drift import SchemaDriftCheck
from app.checks.stale_dataset import StaleDatasetCheck
from app.findings import Finding

DEFAULT_CHECKS = (
    SchemaDriftCheck(),
    PiiExposureCheck(),
    StaleDatasetCheck(),
    MissingOwnerCheck(),
    FeatureLeakageRiskCheck(),
    ModelPerformanceRegressionCheck(),
    DeploymentConfigDriftCheck(),
)


def run_checks(context: dict[str, Any]) -> list[Finding]:
    """Run all default risk checks against a scan context."""
    findings: list[Finding] = []
    for check in DEFAULT_CHECKS:
        findings.extend(check.run(context))
    return findings
