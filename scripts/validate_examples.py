"""Validate generated example artifacts."""

from __future__ import annotations

import json
from pathlib import Path

REQUIRED_FILES = (
    "sample_report.json",
    "sample_report.html",
    "sample_report.md",
    "sample_mcp_dryrun.json",
)


def main() -> None:
    """Validate generated examples are present and parseable."""
    examples_dir = Path("examples")
    missing = [name for name in REQUIRED_FILES if not (examples_dir / name).exists()]
    if missing:
        raise SystemExit(f"Missing example files: {', '.join(missing)}")

    json.loads((examples_dir / "sample_report.json").read_text(encoding="utf-8"))
    json.loads((examples_dir / "sample_mcp_dryrun.json").read_text(encoding="utf-8"))

    html = (examples_dir / "sample_report.html").read_text(encoding="utf-8")
    markdown = (examples_dir / "sample_report.md").read_text(encoding="utf-8")
    if "Model Lineage Guard" not in html or "Model Lineage Guard" not in markdown:
        raise SystemExit("Example reports do not contain the expected title.")
    print("Example artifacts validated.")


if __name__ == "__main__":
    main()
