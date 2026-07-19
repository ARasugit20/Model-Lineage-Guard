# Write-Back Policy

Write-back behavior is controlled by `config/writeback_policy.json`.

Fields:

- `minimum_severity`: findings below this severity are not written back.
- `allowed_entity_types`: DataHub entity types allowed to receive write-back MCPs.
- `checks`: per-check policy.
- `mode`: `auto_apply` means the finding may produce an MCP; `human_review_only` means it is documented but excluded from write-back.
- `tag`: DataHub tag name to attach for eligible findings.

Default policy:

```json
{
  "minimum_severity": "medium",
  "checks": {
    "schema_drift": {"mode": "auto_apply", "tag": "risk:schema-drift"},
    "pii_exposure": {"mode": "auto_apply", "tag": "risk:pii-exposure"},
    "missing_owner": {"mode": "auto_apply", "tag": "risk:missing-owner"}
  }
}
```

Use dry-run before apply:

```bash
mlguard scan '<urn>' --write-back dry-run
mlguard scan '<urn>' --write-back apply --confirm
```
