#!/usr/bin/env python3
"""Convenience script to run docker compose and open a status page."""

import subprocess
import webbrowser
from pathlib import Path


def main() -> None:
    subprocess.run(["docker", "compose", "up", "-d", "--build"], check=True)
    status_file = Path(__file__).parent / "status.html"
    webbrowser.open(status_file.resolve().as_uri())


if __name__ == "__main__":
    main()
