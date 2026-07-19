"""Deterministic demo scan context mirroring the seeded DataHub lineage."""

from __future__ import annotations

from typing import Any

RAW_URN = "urn:li:dataset:(urn:li:dataPlatform:demo,raw_transactions,PROD)"
FEATURE_TABLE_URN = "urn:li:mlFeatureTable:(urn:li:dataPlatform:demo,user_risk_features)"
FEATURE_URN = "urn:li:mlFeature:(user_risk_features,chargeback_resolved_at)"
MODEL_URN = "urn:li:mlModel:(urn:li:dataPlatform:demo,credit_risk_v3,PROD)"
DEPLOYMENT_URN = "urn:li:mlModelDeployment:(urn:li:dataPlatform:demo,credit_risk_prod,PROD)"
DASHBOARD_URN = "urn:li:dataset:(urn:li:dataPlatform:demo,dashboard.risk_ops,PROD)"


def demo_scan_context() -> dict[str, Any]:
    """Return a generated scan context with one instance of every core risk."""
    return {
        "target_urn": MODEL_URN,
        "scan_started_at": "2026-07-17T12:00:00+00:00",
        "lineage": {
            "upstream": [
                {"urn": FEATURE_TABLE_URN, "source_urn": MODEL_URN, "depth": 1},
                {"urn": FEATURE_URN, "source_urn": MODEL_URN, "depth": 1},
                {"urn": RAW_URN, "source_urn": FEATURE_TABLE_URN, "depth": 2},
            ],
            "downstream": [
                {"urn": DEPLOYMENT_URN, "source_urn": MODEL_URN, "depth": 1},
                {"urn": DASHBOARD_URN, "source_urn": DEPLOYMENT_URN, "depth": 2},
            ],
        },
        "entities": {
            RAW_URN: {
                "urn": RAW_URN,
                "dataset": {
                    "name": "raw_transactions",
                    "customProperties": {
                        "mlguard.expected_cadence_hours": "24",
                        "mlguard.last_refreshed_at": "2026-07-12T02:15:00Z",
                        "mlguard.schema_changed_at": "2026-07-10T08:00:00Z",
                        "mlguard.schema_change": "customer_id:int->string",
                    },
                },
                "model": {},
                "deployment": {},
                "owners": ["urn:li:corpuser:payments-data-owner"],
                "schema": [
                    {
                        "fieldPath": "customer_id",
                        "nativeDataType": "string",
                        "description": "Customer identifier; changed from int.",
                    },
                    {
                        "fieldPath": "email",
                        "nativeDataType": "string",
                        "description": "Customer email address.",
                        "globalTags": {"tags": [{"tag": "urn:li:tag:pii"}]},
                        "glossaryTerms": {"terms": [{"urn": "urn:li:glossaryTerm:PII"}]},
                    },
                    {
                        "fieldPath": "chargeback_resolved_at",
                        "nativeDataType": "timestamp",
                        "description": "Timestamp populated after chargeback outcome is resolved.",
                    },
                ],
            },
            FEATURE_TABLE_URN: {
                "urn": FEATURE_TABLE_URN,
                "dataset": {},
                "model": {
                    "customProperties": {
                        "mlguard.last_recomputed_at": "2026-07-09T01:00:00Z",
                        "mlguard.expected_upstream_schema": "raw_transactions.customer_id:int",
                        "mlguard.contains_unapproved_pii": "true",
                        "mlguard.pii_column": "raw_transactions.email",
                    }
                },
                "deployment": {},
                "owners": [],
                "schema": [],
            },
            FEATURE_URN: {
                "urn": FEATURE_URN,
                "dataset": {},
                "model": {
                    "description": "Feature derived from chargeback_resolved_at.",
                    "customProperties": {
                        "mlguard.leakage_candidate": "true",
                        "mlguard.leakage_evidence": (
                            "chargeback_resolved_at postdates label defaulted_30d"
                        ),
                    },
                },
                "deployment": {},
                "owners": ["urn:li:corpuser:risk-ml-owner"],
                "schema": [],
            },
            MODEL_URN: {
                "urn": MODEL_URN,
                "dataset": {},
                "model": {
                    "name": "credit_risk_v3",
                    "customProperties": {
                        "mlguard.production": "true",
                        "mlguard.performance_metric": "auc",
                        "mlguard.baseline_metric_value": "0.890",
                        "mlguard.current_metric_value": "0.841",
                        "mlguard.performance_tolerance": "0.010",
                    },
                },
                "deployment": {},
                "owners": ["urn:li:corpuser:risk-ml-owner"],
                "schema": [],
            },
            DEPLOYMENT_URN: {
                "urn": DEPLOYMENT_URN,
                "dataset": {},
                "model": {},
                "deployment": {
                    "customProperties": {
                        "mlguard.production": "true",
                        "mlguard.expected_instance_type": "ml.m5.large",
                        "mlguard.actual_instance_type": "ml.t3.medium",
                    }
                },
                "owners": ["urn:li:corpuser:risk-platform-owner"],
                "schema": [],
            },
            DASHBOARD_URN: {
                "urn": DASHBOARD_URN,
                "dataset": {"customProperties": {"mlguard.demo_node": "true"}},
                "model": {},
                "deployment": {},
                "owners": ["urn:li:corpuser:risk-ops-owner"],
                "schema": [],
            },
        },
    }
