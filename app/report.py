"""Render risk reports to HTML, JSON, and pull-request markdown."""

from pathlib import Path

from app.findings import RiskReport


def render_report(report: RiskReport) -> str:
    """Render a placeholder textual report until Phase 3 adds templates."""
    return f"Model Lineage Guard report for {report.target_urn}"


def render_json(report: RiskReport, out_dir: Path) -> Path:
    """Write a machine-readable JSON risk report."""
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "report.json"
    path.write_text(report.to_json(), encoding="utf-8")
    return path
