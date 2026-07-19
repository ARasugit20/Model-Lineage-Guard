# Model Lineage Guard

[![CI](https://github.com/ARasugit20/Model-Lineage-Guard/actions/workflows/ci.yml/badge.svg)](https://github.com/ARasugit20/Model-Lineage-Guard/actions/workflows/ci.yml)

Model Lineage Guard is a DataHub-aware CLI agent that scans ML lineage for production risks that usually hide between datasets, feature tables, models, and deployments: schema drift, PII exposure, stale upstream data, missing ownership, and feature leakage. It reads DataHub metadata, produces JSON/HTML/Markdown reports, and can write safe audit tags back to DataHub through MetadataChangeProposals.

License: Apache-2.0. Hackathon: Build with DataHub Agent Hackathon, Agents That Do Real Work / Production ML Agents track. Current phase: Phase 3/4 build-out with reports, dry-run write-back, tests, and examples.

Demo video: [DEMO VIDEO LINK]

Tech stack: Python 3.11+, Typer, acryl-datahub, datahub-agent-context, Jinja2, vis-network, pytest, ruff, mypy.

## Quickstart

One-command live demo on a machine with Docker available:

```bash
make demo
```

## How To Demo In 3 Minutes

1. Run `make demo-offline` if Docker is unavailable, or `make demo` with Docker running.
2. Open `examples/sample_report.html` and point at the lineage graph first.
3. Filter findings by severity and check type.
4. Open `examples/sample_mcp_dryrun.json` to show safe write-back payloads.
5. Open `examples/sample_writeback_audit.jsonl` to show the audit trail.
6. Explain that live apply mode requires `--write-back apply --confirm`.

Manual live DataHub path:

```bash
pip install acryl-datahub
datahub docker quickstart
pip install -e ".[dev]"
python3 scripts/seed_demo_lineage.py
mlguard scan 'urn:li:mlModel:(urn:li:dataPlatform:demo,credit_risk_v3,PROD)' --out out/credit_risk_v3 --write-back dry-run
```

Offline artifact preview, useful when Docker is not available:

```bash
make demo-offline
```

## Environment

Create `.env` from `.env.example` when scanning live DataHub:

```bash
DATAHUB_GMS_HOST=http://localhost:8080
DATAHUB_TOKEN=
```

`DATAHUB_GMS_HOST` points to DataHub GMS. `DATAHUB_TOKEN` is optional for local quickstart and required for authenticated DataHub instances.

## Commands

Scan one entity and write reports:

```bash
mlguard scan 'urn:li:mlModel:(urn:li:dataPlatform:demo,credit_risk_v3,PROD)' --out out/credit_risk_v3 --write-back dry-run
```

Scan all visible ML models:

```bash
mlguard scan-all --out out/all-models --write-back dry-run
```

Generate deterministic demo reports without connecting to DataHub:

```bash
mlguard demo-report --out examples --write-back dry-run
```

Real stdout from `mlguard demo-report --out examples --write-back dry-run`:

```text
Target: urn:li:mlModel:(urn:li:dataPlatform:demo,credit_risk_v3,PROD)
Upstream edges: 3
Downstream edges: 2
Findings: 9
  [high] Upstream schema changed after feature computation (schema_drift)
  [critical] PII flows into model lineage without an approved exception (pii_exposure)
  [critical] PII flows into model lineage without an approved exception (pii_exposure)
  [high] Upstream dataset is stale for its declared cadence (stale_dataset)
  [medium] Lineage entity has no registered owner (missing_owner)
  [high] Feature may use post-outcome information (feature_leakage_risk)
  [high] Feature may use post-outcome information (feature_leakage_risk)
  [high] Model performance regressed below baseline (model_performance_regression)
  [medium] Deployment config drift detected (deployment_config_drift)
JSON report: examples/report.json
HTML report: examples/report.html
PR comment: examples/pr_comment.md
Write-back dry-run MCP JSON: examples/mcp_dryrun.json
Write-back audit log: examples/writeback_audit.jsonl
Human-review-only findings excluded from write-back:
  stale_dataset: Upstream dataset is stale for its declared cadence
  feature_leakage_risk: Feature may use post-outcome information
  feature_leakage_risk: Feature may use post-outcome information
  model_performance_regression: Model performance regressed below baseline
  deployment_config_drift: Deployment config drift detected
```

## Write-Back

Write-back is explicit and safe by default:

```bash
mlguard scan '<urn>' --write-back dry-run
mlguard scan '<urn>' --write-back apply --confirm
```

Dry-run builds MCP payloads and writes them to `mcp_dryrun.json` without sending anything to DataHub. Apply mode requires `--confirm` and emits one MCP at a time through the DataHub SDK.

Safe write-back currently adds risk tags for schema drift, PII exposure, and missing owner findings. Stale dataset and feature leakage findings are flagged for human review only and excluded from automated write-back.

See [examples/sample_mcp_dryrun.json](examples/sample_mcp_dryrun.json).
Dry-run/apply decisions are logged to `writeback_audit.jsonl`; see [examples/sample_writeback_audit.jsonl](examples/sample_writeback_audit.jsonl).

Policy lives in [config/writeback_policy.json](config/writeback_policy.json). Edit it to change severity thresholds, eligible checks, allowed entity types, and tag names.

## Reports

Every scan writes:

- `report.json`: machine-readable report
- `report.html`: static visual report with a vis-network lineage graph
- `pr_comment.md`: GitHub PR-comment-ready Markdown summary

Generated samples:

- [examples/sample_report.json](examples/sample_report.json)
- [examples/sample_report.html](examples/sample_report.html)
- [examples/sample_report.md](examples/sample_report.md)

## Testing

Run all local checks:

```bash
make test
```

This runs:

```bash
ruff check .
mypy app/
pytest -q
```

Unit tests mock DataHub metadata and do not require a live DataHub instance. Live DataHub verification requires Docker and the official `datahub docker quickstart` runtime.

## Packaging

Build and install a wheel:

```bash
python -m pip install build
python -m build
pip install dist/*.whl
mlguard --help
```

## Roadmap

- Phase 2 complete: DataHub client wrapper, five risk checks, mocked tests.
- Phase 3 in progress: JSON/HTML/Markdown reporting, generated examples.
- Phase 4 in progress: safe write-back dry-run/apply flow.
- Next: live DataHub integration test, configuration file for check thresholds, extra governance/model-eval checks, lineage caching and pagination.

Out of scope: multi-tenant auth, raw warehouse connectors, and a persistent database. DataHub is the source of truth.

Additional docs:

- [Architecture](docs/architecture.md)
- [Write-back safety](docs/writeback-safety.md)
- [Write-back policy](docs/writeback-policy.md)
- [Live DataHub verification](docs/live-datahub-verification.md)
- [Submission checklist](docs/submission-checklist.md)
