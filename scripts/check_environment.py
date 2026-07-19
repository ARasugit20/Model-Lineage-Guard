"""Check whether the local machine can run the full live demo."""

from __future__ import annotations

import shutil
import subprocess


def main() -> None:
    """Print local environment readiness for Model Lineage Guard."""
    tools = ["python3", "datahub", "docker"]
    for tool in tools:
        path = shutil.which(tool)
        status = path or "not found"
        print(f"{tool}: {status}")
    if shutil.which("docker"):
        result = subprocess.run(
            ["docker", "info"],
            check=False,
            capture_output=True,
            text=True,
        )
        print(f"docker running: {result.returncode == 0}")


if __name__ == "__main__":
    main()
