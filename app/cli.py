"""Typer command-line interface for Model Lineage Guard."""

from enum import StrEnum
from pathlib import Path
from typing import Annotated

import typer
from click import ClickException

from app import __version__
from app.checks import run_checks
from app.datahub_client import DataHubClient
from app.demo_context import demo_scan_context
from app.findings import RiskReport
from app.report import render_html, render_json, render_markdown
from app.writeback import apply as apply_writeback
from app.writeback import build_mcps, human_review_findings, render_mcp_json

app = typer.Typer(
    name="mlguard",
    help="Inspect DataHub ML lineage for production risk signals.",
    no_args_is_help=True,
)


class WriteBackMode(StrEnum):
    """Supported DataHub write-back modes."""

    OFF = "off"
    DRY_RUN = "dry-run"
    APPLY = "apply"


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"mlguard {__version__}")
        raise typer.Exit


@app.callback()
def main(
    version: Annotated[
        bool | None,
        typer.Option("--version", callback=_version_callback, help="Show the installed version."),
    ] = None,
) -> None:
    """Run Model Lineage Guard commands."""


@app.command()
def scan(
    urn: Annotated[str, typer.Argument(help="DataHub URN of the dataset, model, or deployment.")],
    out: Annotated[
        Path,
        typer.Option("--out", "-o", help="Directory where report artifacts will be written."),
    ] = Path("out"),
    write_back: Annotated[
        WriteBackMode,
        typer.Option("--write-back", help="DataHub write-back mode: off, dry-run, or apply."),
    ] = WriteBackMode.OFF,
    confirm: Annotated[
        bool,
        typer.Option("--confirm", help="Required with --write-back apply."),
    ] = False,
) -> None:
    """Scan one DataHub entity for lineage risks."""
    _validate_urn(urn)
    client = DataHubClient()
    context = _load_scan_context(client, urn)
    _complete_scan(
        client=client,
        context=context,
        out=out,
        write_back=write_back,
        confirm=confirm,
    )


@app.command("scan-all")
def scan_all(
    out: Annotated[
        Path,
        typer.Option("--out", "-o", help="Directory where report artifacts will be written."),
    ] = Path("out"),
    write_back: Annotated[
        WriteBackMode,
        typer.Option("--write-back", help="DataHub write-back mode: off, dry-run, or apply."),
    ] = WriteBackMode.OFF,
    confirm: Annotated[
        bool,
        typer.Option("--confirm", help="Required with --write-back apply."),
    ] = False,
) -> None:
    """Scan all DataHub ML models visible to the configured client."""
    client = DataHubClient()
    models = client.list_ml_models()
    typer.echo(f"Connected to DataHub at {client.settings.gms_host}")
    typer.echo(f"Found {len(models)} ML model(s).")
    for model in models:
        typer.echo(f"  {model}")
        model_out = out / _safe_dir_name(model)
        context = _load_scan_context(client, model)
        _complete_scan(
            client=client,
            context=context,
            out=model_out,
            write_back=write_back,
            confirm=confirm,
        )


@app.command("demo-report")
def demo_report(
    out: Annotated[
        Path,
        typer.Option("--out", "-o", help="Directory where demo artifacts will be written."),
    ] = Path("examples"),
    write_back: Annotated[
        WriteBackMode,
        typer.Option("--write-back", help="Demo write-back mode: off or dry-run."),
    ] = WriteBackMode.DRY_RUN,
) -> None:
    """Generate report artifacts from the built-in seeded demo context."""
    if write_back == WriteBackMode.APPLY:
        raise typer.BadParameter("demo-report does not apply write-back to DataHub.")
    context = demo_scan_context()
    _complete_scan(
        client=None,
        context=context,
        out=out,
        write_back=write_back,
        confirm=False,
    )


def _complete_scan(
    *,
    client: DataHubClient | None,
    context: dict[str, object],
    out: Path,
    write_back: WriteBackMode,
    confirm: bool,
) -> RiskReport:
    if write_back == WriteBackMode.APPLY and not confirm:
        raise typer.BadParameter("--write-back apply requires --confirm.")

    findings = run_checks(context)
    target_urn = str(context["target_urn"])
    lineage = context["lineage"]
    if not isinstance(lineage, dict):
        raise typer.BadParameter("Scan context is missing lineage metadata.")
    report = RiskReport(
        target_urn=target_urn,
        findings=findings,
        lineage=lineage,
        scan_started_at=str(context["scan_started_at"]),
        writeback_applied=write_back == WriteBackMode.APPLY,
        writeback_dry_run=write_back == WriteBackMode.DRY_RUN,
    )
    mcps = build_mcps(report) if write_back != WriteBackMode.OFF else []
    mcp_path = render_mcp_json(mcps, out) if write_back == WriteBackMode.DRY_RUN else None
    emitted = []
    if write_back == WriteBackMode.APPLY:
        if client is None:
            raise typer.BadParameter("A live DataHub client is required for write-back apply.")
        emitted = apply_writeback(client, mcps)

    json_path = render_json(report, out)
    html_path = render_html(report, lineage, out)
    markdown_path = render_markdown(report, out)

    typer.echo(f"Target: {target_urn}")
    typer.echo(f"Upstream edges: {len(lineage.get('upstream', []))}")
    typer.echo(f"Downstream edges: {len(lineage.get('downstream', []))}")
    typer.echo(f"Findings: {len(findings)}")
    for finding in findings:
        typer.echo(f"  [{finding.severity}] {finding.title} ({finding.check_name})")
    typer.echo(f"JSON report: {json_path}")
    typer.echo(f"HTML report: {html_path}")
    typer.echo(f"PR comment: {markdown_path}")
    if mcp_path:
        typer.echo(f"Write-back dry-run MCP JSON: {mcp_path}")
    if human_review_findings(report):
        typer.echo("Human-review-only findings excluded from write-back:")
        for finding in human_review_findings(report):
            typer.echo(f"  {finding.check_name}: {finding.title}")
    if emitted:
        typer.echo(f"Write-back applied MCPs: {len(emitted)}")
        for entity_urn in emitted:
            typer.echo(f"  emitted: {entity_urn}")
    return report


def _safe_dir_name(urn: str) -> str:
    return "".join(character if character.isalnum() else "-" for character in urn).strip("-")


def _validate_urn(urn: str) -> None:
    if not urn.startswith("urn:li:"):
        raise typer.BadParameter("Expected a DataHub URN starting with 'urn:li:'.")


def _load_scan_context(client: DataHubClient, urn: str) -> dict[str, object]:
    try:
        return client.scan_context(urn)
    except Exception as exc:
        raise ClickException(
            f"Could not read DataHub lineage for {urn} at {client.settings.gms_host}. "
            "Is DataHub running, and are DATAHUB_GMS_HOST/DATAHUB_TOKEN correct?"
        ) from exc
