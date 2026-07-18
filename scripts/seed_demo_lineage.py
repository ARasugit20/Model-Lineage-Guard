"""Seed a local DataHub instance with synthetic ML lineage for the demo."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass

from datahub.emitter.mce_builder import (
    OwnerType,
    make_dataset_urn,
    make_ml_feature_table_urn,
    make_ml_feature_urn,
    make_ml_model_deployment_urn,
    make_ml_model_urn,
    make_owner_urn,
    make_tag_urn,
    make_term_urn,
)
from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.ingestion.graph.client import DatahubClientConfig, DataHubGraph
from datahub.metadata.schema_classes import (
    AuditStampClass,
    DatasetLineageTypeClass,
    DatasetPropertiesClass,
    GlobalTagsClass,
    GlossaryTermAssociationClass,
    GlossaryTermsClass,
    MLFeaturePropertiesClass,
    MLFeatureTablePropertiesClass,
    MLModelDeploymentPropertiesClass,
    MLModelPropertiesClass,
    NumberTypeClass,
    OtherSchemaClass,
    OwnerClass,
    OwnershipClass,
    SchemaFieldClass,
    SchemaFieldDataTypeClass,
    SchemaMetadataClass,
    StringTypeClass,
    TagAssociationClass,
    UpstreamClass,
    UpstreamLineageClass,
)

ACTOR = make_owner_urn("mlguard-demo", OwnerType.USER)
PLATFORM = "demo"


@dataclass(frozen=True)
class DemoUrns:
    """URNs used by the seeded demo lineage graph."""

    raw_transactions: str
    user_risk_features: str
    chargeback_resolved_feature: str
    credit_risk_model: str
    credit_risk_deployment: str
    risk_ops_dashboard: str


def demo_urns() -> DemoUrns:
    """Return stable URNs for the synthetic lineage graph."""
    return DemoUrns(
        raw_transactions=make_dataset_urn(PLATFORM, "raw_transactions", "PROD"),
        user_risk_features=make_ml_feature_table_urn(PLATFORM, "user_risk_features"),
        chargeback_resolved_feature=make_ml_feature_urn(
            "user_risk_features", "chargeback_resolved_at"
        ),
        credit_risk_model=make_ml_model_urn(PLATFORM, "credit_risk_v3", "PROD"),
        credit_risk_deployment=make_ml_model_deployment_urn(PLATFORM, "credit_risk_prod", "PROD"),
        risk_ops_dashboard=make_dataset_urn(PLATFORM, "dashboard.risk_ops", "PROD"),
    )


def _audit_stamp() -> AuditStampClass:
    return AuditStampClass(time=int(time.time() * 1000), actor=ACTOR)


def _emit(graph: DataHubGraph, urn: str, aspect: object) -> None:
    graph.emit_mcp(MetadataChangeProposalWrapper(entityUrn=urn, aspect=aspect))


def _ownership(*owners: str) -> OwnershipClass:
    return OwnershipClass(
        owners=[
            OwnerClass(owner=make_owner_urn(owner, OwnerType.USER), type="DATAOWNER")
            for owner in owners
        ]
    )


def _tags(*names: str) -> GlobalTagsClass:
    return GlobalTagsClass(tags=[TagAssociationClass(tag=make_tag_urn(name)) for name in names])


def _terms(*names: str) -> GlossaryTermsClass:
    return GlossaryTermsClass(
        terms=[GlossaryTermAssociationClass(urn=make_term_urn(name)) for name in names],
        auditStamp=_audit_stamp(),
    )


def _field(
    name: str,
    native_type: str,
    *,
    description: str,
    pii: bool = False,
) -> SchemaFieldClass:
    logical_type = (
        StringTypeClass()
        if native_type.lower() in {"string", "varchar"}
        else NumberTypeClass()
    )
    return SchemaFieldClass(
        fieldPath=name,
        type=SchemaFieldDataTypeClass(type=logical_type),
        nativeDataType=native_type,
        description=description,
        nullable=True,
        globalTags=_tags("pii") if pii else None,
        glossaryTerms=_terms("PII") if pii else None,
    )


def _schema(name: str, fields: list[SchemaFieldClass]) -> SchemaMetadataClass:
    return SchemaMetadataClass(
        schemaName=name,
        platform=PLATFORM,
        version=0,
        hash=f"mlguard-demo-{name}",
        platformSchema=OtherSchemaClass(
            rawSchema="Synthetic schema seeded for Model Lineage Guard."
        ),
        fields=fields,
        created=_audit_stamp(),
        lastModified=_audit_stamp(),
    )


def _upstream(*urns: str) -> UpstreamLineageClass:
    return UpstreamLineageClass(
        upstreams=[
            UpstreamClass(
                dataset=urn,
                type=DatasetLineageTypeClass.TRANSFORMED,
                auditStamp=_audit_stamp(),
            )
            for urn in urns
        ]
    )


def seed(graph: DataHubGraph) -> DemoUrns:
    """Create demo ML lineage and risk metadata in DataHub."""
    urns = demo_urns()

    _emit(
        graph,
        urns.raw_transactions,
        DatasetPropertiesClass(
            name="raw_transactions",
            description=(
                "Payment authorization and chargeback events used by the credit risk model."
            ),
            customProperties={
                "mlguard.expected_cadence_hours": "24",
                "mlguard.last_refreshed_at": "2026-07-12T02:15:00Z",
                "mlguard.schema_changed_at": "2026-07-10T08:00:00Z",
                "mlguard.schema_change": "customer_id:int->string",
            },
        ),
    )
    _emit(
        graph,
        urns.raw_transactions,
        _schema(
            "raw_transactions",
            [
                _field(
                    "customer_id",
                    "string",
                    description="Customer identifier; changed from int.",
                ),
                _field(
                    "transaction_amount",
                    "number",
                    description="Authorized transaction amount.",
                ),
                _field("email", "string", description="Customer email address.", pii=True),
                _field(
                    "chargeback_resolved_at",
                    "timestamp",
                    description="Timestamp populated after a chargeback investigation completes.",
                ),
            ],
        ),
    )
    _emit(graph, urns.raw_transactions, _ownership("payments-data-owner"))
    _emit(graph, urns.raw_transactions, _tags("mlguard-demo", "schema-drift-source"))

    _emit(
        graph,
        urns.user_risk_features,
        MLFeatureTablePropertiesClass(
            description="Feature table consumed by the credit risk model.",
            customProperties={
                "mlguard.last_recomputed_at": "2026-07-09T01:00:00Z",
                "mlguard.expected_upstream_schema": "raw_transactions.customer_id:int",
                "mlguard.contains_unapproved_pii": "true",
                "mlguard.pii_column": "raw_transactions.email",
            },
        ),
    )
    _emit(graph, urns.user_risk_features, _upstream(urns.raw_transactions))
    _emit(graph, urns.user_risk_features, _tags("mlguard-demo", "feature-table"))
    # No ownership aspect on this entity: deliberately bakes in the missing owner risk.

    _emit(
        graph,
        urns.chargeback_resolved_feature,
        MLFeaturePropertiesClass(
            description=(
                "Feature derived from chargeback_resolved_at; known only after the label event."
            ),
            dataType="TIME",
            sources=[urns.raw_transactions],
            customProperties={
                "mlguard.leakage_candidate": "true",
                "mlguard.leakage_evidence": "chargeback_resolved_at postdates label defaulted_30d",
            },
        ),
    )
    _emit(graph, urns.chargeback_resolved_feature, _upstream(urns.raw_transactions))
    _emit(graph, urns.chargeback_resolved_feature, _ownership("risk-ml-owner"))
    _emit(graph, urns.chargeback_resolved_feature, _tags("mlguard-demo", "leakage-risk"))

    _emit(
        graph,
        urns.credit_risk_model,
        MLModelPropertiesClass(
            name="credit_risk_v3",
            description=(
                "Gradient boosted credit risk model used for production authorization decisions."
            ),
            date=int(time.time() * 1000),
            type="classification",
            mlFeatures=[urns.chargeback_resolved_feature],
            deployments=[urns.credit_risk_deployment],
            customProperties={
                "mlguard.production": "true",
                "mlguard.training_data_urn": urns.raw_transactions,
                "mlguard.label_column": "defaulted_30d",
                "mlguard.last_trained_at": "2026-07-09T02:30:00Z",
            },
        ),
    )
    _emit(
        graph,
        urns.credit_risk_model,
        _upstream(urns.user_risk_features, urns.chargeback_resolved_feature),
    )
    _emit(graph, urns.credit_risk_model, _ownership("risk-ml-owner"))
    _emit(graph, urns.credit_risk_model, _tags("mlguard-demo", "production-model"))

    _emit(
        graph,
        urns.credit_risk_deployment,
        MLModelDeploymentPropertiesClass(
            description="Production deployment for real-time credit risk scoring.",
            createdAt=int(time.time() * 1000),
            status="ACTIVE",
            customProperties={"mlguard.production": "true"},
        ),
    )
    _emit(graph, urns.credit_risk_deployment, _upstream(urns.credit_risk_model))
    _emit(graph, urns.credit_risk_deployment, _ownership("risk-platform-owner"))
    _emit(graph, urns.credit_risk_deployment, _tags("mlguard-demo", "production-deployment"))

    _emit(
        graph,
        urns.risk_ops_dashboard,
        DatasetPropertiesClass(
            name="risk_ops_dashboard",
            description="Operational dashboard monitoring production credit risk decisions.",
            customProperties={"mlguard.demo_node": "true"},
        ),
    )
    _emit(graph, urns.risk_ops_dashboard, _upstream(urns.credit_risk_deployment))
    _emit(graph, urns.risk_ops_dashboard, _ownership("risk-ops-owner"))
    _emit(graph, urns.risk_ops_dashboard, _tags("mlguard-demo", "dashboard"))

    return urns


def main() -> None:
    """Seed the configured DataHub instance with demo lineage."""
    host = os.getenv("DATAHUB_GMS_HOST", "http://localhost:8080")
    token = os.getenv("DATAHUB_TOKEN") or None
    graph = DataHubGraph(DatahubClientConfig(server=host, token=token))
    graph.test_connection()
    urns = seed(graph)
    print("Seeded Model Lineage Guard demo lineage:")
    for field, urn in urns.__dict__.items():
        print(f"  {field}: {urn}")


if __name__ == "__main__":
    main()
