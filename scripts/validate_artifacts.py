"""Validate scan output artifacts in a supplied directory."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> None:
    """Validate report and write-back preview artifacts."""
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python scripts/validate_artifacts.py <artifact-dir>")
    artifact_dir = Path(sys.argv[1])
    required = ("report.json", "report.html", "mcp_dryrun.json")
    missing = [name for name in required if not (artifact_dir / name).exists()]
    if missing:
        raise SystemExit(f"Missing artifacts in {artifact_dir}: {', '.join(missing)}")
    for name in required:
        if (artifact_dir / name).stat().st_size == 0:
            raise SystemExit(f"Artifact is empty: {artifact_dir / name}")
    json.loads((artifact_dir / "report.json").read_text(encoding="utf-8"))
    json.loads((artifact_dir / "mcp_dryrun.json").read_text(encoding="utf-8"))
    print(f"Validated artifacts in {artifact_dir}")


if __name__ == "__main__":
    main()
