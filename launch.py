#!/usr/bin/env python3
"""Convenience script to run docker compose and open a status page."""

import subprocess



def main() -> None:
    subprocess.run(["docker", "compose", "up", "-d", "--wait"], check=True)


if __name__ == "__main__":
    main()
