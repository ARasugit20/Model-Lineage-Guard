"""Tests for the PII exposure risk check."""

from typing import Any

from app.checks.pii_exposure import PiiExposureCheck


def test_pii_exposure_fires_for_unapproved_sensitive_fields(risky_context: dict[str, Any]) -> None:
    findings = PiiExposureCheck().run(risky_context)

    assert findings
    assert any("email" in column for finding in findings for column in finding.evidence["columns"])


def test_pii_exposure_does_not_fire_without_pii(clean_context: dict[str, Any]) -> None:
    assert PiiExposureCheck().run(clean_context) == []
