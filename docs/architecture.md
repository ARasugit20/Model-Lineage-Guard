# Architecture

Model Lineage Guard has four layers:

1. DataHub access: `app/datahub_client.py` gathers lineage and metadata.
2. Risk checks: `app/checks/` turns metadata into structured findings.
3. Reporting: `app/report.py` renders JSON, HTML, and Markdown artifacts.
4. Write-back: `app/writeback.py` builds DataHub MCPs for safe audit tags.

```mermaid
flowchart LR
  DataHub[DataHub metadata graph] --> Client[DataHubClient]
  Client --> Context[Scan context]
  Context --> Checks[Risk checks]
  Checks --> Report[RiskReport]
  Report --> JSON[report.json]
  Report --> HTML[report.html]
  Report --> MD[pr_comment.md]
  Report --> MCP[write-back MCPs]
  MCP --> DataHub
```
