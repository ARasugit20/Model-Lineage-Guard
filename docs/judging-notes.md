# Judging Notes

Model Lineage Guard is designed around the hackathon scoring points:

- Reads real DataHub metadata through the SDK and Agent Context Kit path.
- Does practical ML platform work: lineage risk detection.
- Writes findings back to DataHub through MCPs when explicitly confirmed.
- Produces artifacts judges can inspect quickly: JSON, Markdown, and a static HTML lineage graph.

The strongest demo path is:

```bash
make demo
```

When Docker is unavailable, use:

```bash
make demo-offline
```
