# Security Policy

Model Lineage Guard reads metadata from DataHub and can optionally emit audit tags back to DataHub.

## Supported Versions

This hackathon project currently supports the latest `main` branch only.

## Reporting Issues

Do not publish credentials, DataHub tokens, or private lineage details in public issues. Report sensitive security concerns privately to the repository owner.

## Token Handling

- Store DataHub credentials in `.env`, not in source control.
- `DATAHUB_TOKEN` is optional for local quickstart and required for authenticated instances.
- Write-back apply mode requires `--confirm` to reduce accidental metadata changes.
