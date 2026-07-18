"""Tests for the schema drift risk check."""

from typing import Any

from app.checks.schema_drift import SchemaDriftCheck


def test_schema_drift_fires_when_source_changed_after_recompute(
    risky_context: dict[str, Any],
) -> None:
    findings = SchemaDriftCheck().run(risky_context)

    assert len(findings) == 1
    assert findings[0].evidence["schema_change"] == "customer_id:int->string"


def test_schema_drift_does_not_fire_without_schema_change(clean_context: dict[str, Any]) -> None:
    assert SchemaDriftCheck().run(clean_context) == []
