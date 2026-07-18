"""Render risk reports to HTML, JSON, and pull-request markdown."""

import json
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.findings import Finding, RiskReport, Severity


def render_report(report: RiskReport) -> str:
    """Render a placeholder textual report until Phase 3 adds templates."""
    return f"Model Lineage Guard report for {report.target_urn}"


def render_json(report: RiskReport, out_dir: Path) -> Path:
    """Write a machine-readable JSON risk report."""
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "report.json"
    path.write_text(report.to_json(), encoding="utf-8")
    return path


def render_html(report: RiskReport, lineage_graph: dict[str, Any], out_dir: Path) -> Path:
    """Write a self-contained judge-facing HTML risk report."""
    out_dir.mkdir(parents=True, exist_ok=True)
    template_dir = Path(__file__).parent / "templates"
    environment = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(("html", "j2")),
    )
    template = environment.get_template("report.html.j2")
    graph = _build_graph(report, lineage_graph)
    html = template.render(
        report=report.to_dict(),
        findings_by_severity=_group_findings(report.findings),
        graph_json=json.dumps(graph),
        severity_order=[severity.value for severity in _SEVERITY_ORDER],
    )
    path = out_dir / "report.html"
    path.write_text(html, encoding="utf-8")
    return path


def render_markdown(report: RiskReport, out_dir: Path) -> Path:
    """Write a GitHub PR-comment-friendly markdown summary."""
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = report.to_dict()
    summary = payload["summary"]
    writeback_status = (
        "applied" if report.writeback_applied else "dry-run" if report.writeback_dry_run else "off"
    )
    lines = [
        "## Model Lineage Guard",
        "",
        (
            f"Scanned `{report.target_urn}` with "
            f"{len(report.findings)} finding(s): "
            f"{summary['critical']} critical, {summary['high']} high, "
            f"{summary['medium']} medium, {summary['low']} low."
        ),
        "",
        "Full report: `report.html`",
        f"Write-back: {writeback_status}",
        "",
    ]
    if report.findings:
        lines.extend(
            [
                "| Severity | Check | Entity | Finding |",
                "| --- | --- | --- | --- |",
            ]
        )
        for finding in sorted(
            report.findings,
            key=lambda item: _SEVERITY_RANK[item.severity],
            reverse=True,
        ):
            lines.append(
                "| "
                f"{finding.severity.value} | "
                f"{finding.check_name} | "
                f"`{finding.entity_urn or report.target_urn}` | "
                f"{finding.title} |"
            )
    else:
        lines.append("No risks detected across the scanned lineage neighborhood.")
    path = out_dir / "pr_comment.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


_SEVERITY_ORDER = (Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW)
_SEVERITY_RANK = {severity: index for index, severity in enumerate(reversed(_SEVERITY_ORDER))}
_NODE_COLORS = {
    "critical": "#ef4444",
    "high": "#f97316",
    "medium": "#f59e0b",
    "low": "#38bdf8",
    "none": "#64748b",
}


def _group_findings(findings: list[Finding]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {severity.value: [] for severity in _SEVERITY_ORDER}
    for finding in sorted(findings, key=lambda item: _SEVERITY_RANK[item.severity], reverse=True):
        grouped[finding.severity.value].append(finding.to_dict())
    return grouped


def _build_graph(report: RiskReport, lineage_graph: dict[str, Any]) -> dict[str, Any]:
    target = report.target_urn
    node_urns = {target}
    edges: list[dict[str, str]] = []
    for direction in ("upstream", "downstream"):
        for edge in lineage_graph.get(direction, []) or []:
            source = str(edge.get("source_urn") or target)
            related = str(edge.get("urn"))
            if not related:
                continue
            node_urns.update({source, related})
            if direction == "upstream":
                edges.append({"from": related, "to": source, "arrows": "to"})
            else:
                edges.append({"from": source, "to": related, "arrows": "to"})

    findings_by_entity: dict[str, list[Finding]] = {}
    for finding in report.findings:
        if finding.entity_urn:
            findings_by_entity.setdefault(finding.entity_urn, []).append(finding)

    nodes = [
        _node_payload(urn, urn == target, findings_by_entity.get(urn, []))
        for urn in sorted(node_urns)
    ]
    return {"nodes": nodes, "edges": edges}


def _node_payload(urn: str, target: bool, findings: list[Finding]) -> dict[str, Any]:
    severity = _highest_severity(findings)
    finding_lines = "<br>".join(
        f"{finding.severity.value.upper()}: {finding.title}" for finding in findings
    )
    title = f"<strong>{urn}</strong>"
    if finding_lines:
        title = f"{title}<br>{finding_lines}"
    return {
        "id": urn,
        "label": _short_label(urn),
        "title": title,
        "color": {
            "background": _NODE_COLORS[severity],
            "border": "#f8fafc" if target else "#0f172a",
        },
        "font": {"color": "#f8fafc", "face": "Inter"},
        "borderWidth": 4 if target else 1,
        "shape": "box" if target else "ellipse",
    }


def _highest_severity(findings: list[Finding]) -> str:
    if not findings:
        return "none"
    return max(findings, key=lambda finding: _SEVERITY_RANK[finding.severity]).severity.value


def _short_label(urn: str) -> str:
    if "," in urn:
        return urn.rstrip(")").split(",")[-2]
    return urn.rsplit(":", maxsplit=1)[-1]
