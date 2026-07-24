"""Tests for scan-local entity type indexing used by checks."""

from typing import Any

from app.checks.base import entity_type_index, lineage_entities_by_type


def test_entity_type_index_is_built_once_and_reused(risky_context: dict[str, Any]) -> None:
    first = entity_type_index(risky_context)
    second = entity_type_index(risky_context)

    assert first is second
    assert first["dataset"] == ["urn:li:dataset:(urn:li:dataPlatform:demo,raw_transactions,PROD)"]
    assert set(first) >= {"dataset", "mlFeatureTable", "mlFeature", "mlModel"}


def test_lineage_entities_by_type_uses_indexed_subset(risky_context: dict[str, Any]) -> None:
    indexed = lineage_entities_by_type(risky_context, "dataset", "mlModel")

    assert sorted(indexed) == [
        "urn:li:dataset:(urn:li:dataPlatform:demo,raw_transactions,PROD)",
        "urn:li:mlModel:(urn:li:dataPlatform:demo,credit_risk_v3,PROD)",
    ]
