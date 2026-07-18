# Model Lineage Guard

Model Lineage Guard inspects DataHub metadata and ML lineage to identify production ML risks, then prepares findings that can be written back to DataHub.

This repository is being built phase by phase for the Build with DataHub Agent Hackathon.

## Current Status

Phase 2 connectivity and risk checks are in place:

- Installable Python package with the `mlguard` Typer CLI.
- DataHub client wrapper using Agent Context Kit plus SDK graph operations.
- Synthetic demo lineage seeding script.
- Five risk checks with mocked pytest coverage:
  - schema drift
  - PII exposure
  - stale upstream dataset
  - missing owner
  - feature leakage risk
- Placeholder modules for reporting and write-back.

Later phases will add report generation, write-back, examples, and final docs.

## Phase 1 Quickstart

Start DataHub with the official quickstart:

```bash
pip install acryl-datahub
datahub docker quickstart
```

Then seed the demo graph and inspect a model:

```bash
cd model-lineage-guard
pip install -e .
python3 scripts/seed_demo_lineage.py
mlguard scan 'urn:li:mlModel:(urn:li:dataPlatform:demo,credit_risk_v3,PROD)'
```
