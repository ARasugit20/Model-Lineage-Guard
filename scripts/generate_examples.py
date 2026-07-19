"""Generate sample artifacts from the built-in demo scan context."""

from __future__ import annotations

from pathlib import Path

from app.checks import run_checks
from app.demo_context import demo_scan_context
from app.findings import RiskReport
from app.report import render_html, render_json, render_markdown
from app.writeback import build_mcps, render_mcp_json, write_audit_log


def main() -> None:
    """Generate examples without requiring a live DataHub instance."""
    context = demo_scan_context()
    report = RiskReport(
        target_urn=str(context["target_urn"]),
        findings=run_checks(context),
        lineage=context["lineage"],
        scan_started_at=str(context["scan_started_at"]),
        writeback_dry_run=True,
    )
    out_dir = Path("examples")
    json_path = render_json(report, out_dir)
    html_path = render_html(report, context["lineage"], out_dir)
    markdown_path = render_markdown(report, out_dir)
    mcps = build_mcps(report)
    mcp_path = render_mcp_json(mcps, out_dir)
    audit_path = write_audit_log(
        mcps=mcps,
        out_dir=out_dir,
        mode="dry-run",
        outcome="previewed",
    )

    (out_dir / "sample_report.json").write_text(json_path.read_text(encoding="utf-8"))
    (out_dir / "sample_report.html").write_text(html_path.read_text(encoding="utf-8"))
    (out_dir / "sample_report.md").write_text(markdown_path.read_text(encoding="utf-8"))
    (out_dir / "sample_mcp_dryrun.json").write_text(mcp_path.read_text(encoding="utf-8"))
    (out_dir / "sample_writeback_audit.jsonl").write_text(
        audit_path.read_text(encoding="utf-8")
    )
    (out_dir / "sample_lineage_report.json").write_text(json_path.read_text(encoding="utf-8"))
    (out_dir / "sample_lineage_report.html").write_text(html_path.read_text(encoding="utf-8"))
    (out_dir / "generated_pr_comment.md").write_text(markdown_path.read_text(encoding="utf-8"))

    print(f"Generated {out_dir / 'sample_report.json'}")
    print(f"Generated {out_dir / 'sample_report.html'}")
    print(f"Generated {out_dir / 'sample_report.md'}")
    print(f"Generated {out_dir / 'sample_mcp_dryrun.json'}")
    print(f"Generated {out_dir / 'sample_writeback_audit.jsonl'}")


if __name__ == "__main__":
    main()
