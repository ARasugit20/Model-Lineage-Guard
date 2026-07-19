# Live DataHub Verification

Use this checklist on a machine with Docker running:

```bash
pip install -e ".[dev]"
datahub docker quickstart
python3 scripts/seed_demo_lineage.py
mlguard scan 'urn:li:mlModel:(urn:li:dataPlatform:demo,credit_risk_v3,PROD)' --out out/live --write-back dry-run
mlguard scan 'urn:li:mlModel:(urn:li:dataPlatform:demo,credit_risk_v3,PROD)' --out out/live-apply --write-back apply --confirm
```

Expected dry-run behavior:

- Reports are written to `out/live/`.
- MCP payloads are written to `out/live/mcp_dryrun.json`.
- Human-review-only findings are excluded from write-back.

Expected apply behavior:

- Safe risk tags are emitted to DataHub one MCP at a time.
