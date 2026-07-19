# Changelog

## Hackathon Build-Out

- Added CI with Ruff, mypy, and pytest.
- Implemented DataHub metadata and lineage scan context collection.
- Added five production ML risk checks: schema drift, PII exposure, stale dataset, missing owner, and feature leakage risk.
- Added stable `Finding` and `RiskReport` serialization.
- Added JSON, HTML, and Markdown report renderers.
- Added a static HTML lineage graph using vis-network.
- Implemented DataHub write-back MCP construction for safe audit tags.
- Added dry-run and apply write-back modes with an explicit `--confirm` safety rail for apply.
- Added deterministic demo artifact generation.
- Added `make test`, `make demo`, and `make demo-offline` targets.
- Added generated examples and judge-facing documentation.
