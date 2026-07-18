"""Typer command-line interface for Model Lineage Guard."""

from pathlib import Path
from typing import Annotated

import typer

from app import __version__
from app.checks import run_checks
from app.datahub_client import DataHubClient
from app.findings import RiskReport
from app.report import render_html, render_json

app = typer.Typer(
    name="mlguard",
    help="Inspect DataHub ML lineage for production risk signals.",
    no_args_is_help=True,
)


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
        bool,
        typer.Option("--write-back", help="Opt in to writing findings back to DataHub."),
    ] = False,
) -> None:
    """Scan one DataHub entity for lineage risks."""
    client = DataHubClient()
    context = client.scan_context(urn)
    findings = run_checks(context)
    report = RiskReport(
        target_urn=urn,
        findings=findings,
        lineage=context["lineage"],
        scan_started_at=context["scan_started_at"],
    )
    json_path = render_json(report, out)
    html_path = render_html(report, context["lineage"], out)
    typer.echo(f"Connected to DataHub at {client.settings.gms_host}")
    typer.echo(f"Target: {context['target_urn']}")
    typer.echo(f"Upstream edges: {len(context['lineage']['upstream'])}")
    typer.echo(f"Downstream edges: {len(context['lineage']['downstream'])}")
    typer.echo(f"Entities described: {len(context['entities'])}")
    typer.echo(f"Findings: {len(findings)}")
    for finding in findings:
        typer.echo(f"  [{finding.severity}] {finding.title} ({finding.check_name})")
    typer.echo(f"JSON report: {json_path}")
    typer.echo(f"HTML report: {html_path}")
    typer.echo(f"Write-back requested: {write_back}")


@app.command("scan-all")
def scan_all(
    out: Annotated[
        Path,
        typer.Option("--out", "-o", help="Directory where report artifacts will be written."),
    ] = Path("out"),
    write_back: Annotated[
        bool,
        typer.Option("--write-back", help="Opt in to writing findings back to DataHub."),
    ] = False,
) -> None:
    """Scan all DataHub ML models visible to the configured client."""
    client = DataHubClient()
    models = client.list_ml_models()
    typer.echo(f"Connected to DataHub at {client.settings.gms_host}")
    typer.echo(f"Found {len(models)} ML model(s).")
    for model in models:
        typer.echo(f"  {model}")
    typer.echo(f"Report output directory for Phase 3: {out}")
    typer.echo(f"Write-back requested: {write_back}")
