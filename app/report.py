"""Render risk reports to HTML, JSON, and pull-request markdown."""

from app.findings import RiskReport


def render_report(report: RiskReport) -> str:
    """Render a placeholder textual report until Phase 3 adds templates."""
    return f"Model Lineage Guard report for {report.target_urn}"
