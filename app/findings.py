"""Data structures for risk findings and reports."""

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class Severity(StrEnum):
    """Supported risk severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class Finding:
    """A single risk signal discovered in a lineage scan."""

    check_name: str
    severity: Severity
    title: str
    explanation: str
    evidence: dict[str, Any] = field(default_factory=dict)
    entity_urn: str | None = None
    remediation: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return a stable JSON-serializable finding representation."""
        return {
            "check_name": self.check_name,
            "severity": self.severity.value,
            "title": self.title,
            "explanation": self.explanation,
            "evidence": self.evidence,
            "entity_urn": self.entity_urn,
            "remediation": self.remediation,
        }


@dataclass(frozen=True)
class RiskReport:
    """Aggregated scan result rendered to human and machine-readable artifacts."""

    target_urn: str
    findings: list[Finding] = field(default_factory=list)
    lineage: dict[str, Any] = field(default_factory=dict)
    scan_started_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    writeback_applied: bool = False
    writeback_dry_run: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Return a stable JSON-serializable report representation."""
        return {
            "target_urn": self.target_urn,
            "scan_started_at": self.scan_started_at,
            "writeback": {
                "applied": self.writeback_applied,
                "dry_run": self.writeback_dry_run,
            },
            "summary": {
                severity.value: sum(1 for finding in self.findings if finding.severity == severity)
                for severity in Severity
            },
            "findings": [finding.to_dict() for finding in self.findings],
            "lineage": self.lineage,
        }

    def to_json(self) -> str:
        """Return an indented JSON document for this report."""
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)
