"""Tests for the stale dataset risk check."""

from typing import Any

from app.checks.stale_dataset import StaleDatasetCheck


def test_stale_dataset_fires_when_refresh_exceeds_cadence(risky_context: dict[str, Any]) -> None:
    findings = StaleDatasetCheck().run(risky_context)

    assert len(findings) == 1
    assert findings[0].evidence["observed_age_hours"] > 24


def test_stale_dataset_does_not_fire_when_fresh(clean_context: dict[str, Any]) -> None:
    assert StaleDatasetCheck().run(clean_context) == []
