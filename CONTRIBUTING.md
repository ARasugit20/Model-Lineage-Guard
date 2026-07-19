# Contributing

Thanks for improving Model Lineage Guard.

## Local Setup

```bash
pip install -e ".[dev]"
make test
```

## Development Rules

- Keep DataHub calls behind `app/datahub_client.py`.
- Unit tests must mock DataHub; live DataHub tests should be clearly opt-in.
- Run `make test` before opening a pull request.
- Keep generated examples in `examples/` reproducible with `python3 scripts/generate_examples.py`.

## Commit Style

Use short imperative summaries, for example:

```text
Add JSON report renderer
Fix write-back dry-run serialization
```
