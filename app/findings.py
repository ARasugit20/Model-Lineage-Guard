"""Data structures for risk findings and reports."""

from dataclasses import dataclass, field
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


@dataclass(frozen=True)
class RiskReport:
    """Aggregated scan result rendered to human and machine-readable artifacts."""

    target_urn: str
    findings: list[Finding] = field(default_factory=list)
    lineage: dict[str, Any] = field(default_factory=dict)
