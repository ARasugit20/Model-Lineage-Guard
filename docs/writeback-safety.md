# Write-Back Safety

Write-back uses DataHub MetadataChangeProposals to add audit tags.

Safe automated write-back:

- `schema_drift`
- `pii_exposure`
- `missing_owner`

Human-review-only findings:

- `stale_dataset`
- `feature_leakage_risk`

Apply mode requires:

```bash
mlguard scan '<urn>' --write-back apply --confirm
```

Dry-run mode writes JSON payloads without emitting to DataHub:

```bash
mlguard scan '<urn>' --write-back dry-run
```
