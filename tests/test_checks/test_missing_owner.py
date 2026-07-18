"""Tests for the missing owner risk check."""

from typing import Any

from app.checks.missing_owner import MissingOwnerCheck


def test_missing_owner_fires_for_unowned_lineage_entity(risky_context: dict[str, Any]) -> None:
    findings = MissingOwnerCheck().run(risky_context)

    assert len(findings) == 1
    assert findings[0].evidence["owners"] == []


def test_missing_owner_does_not_fire_when_every_entity_has_owner(
    clean_context: dict[str, Any],
) -> None:
    assert MissingOwnerCheck().run(clean_context) == []
