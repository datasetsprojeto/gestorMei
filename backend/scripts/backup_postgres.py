#!/usr/bin/env python
"""Create a PostgreSQL backup using pg_dump and DATABASE_URL."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse


def parse_database_url(url: str):
    parsed = urlparse(url)
    if parsed.scheme not in {"postgresql", "postgres", "postgresql+psycopg"}:
        raise ValueError("DATABASE_URL must be a PostgreSQL URL")

    return {
        "host": parsed.hostname or "localhost",
        "port": str(parsed.port or 5432),
        "user": parsed.username or "postgres",
        "password": parsed.password or "",
        "database": (parsed.path or "/").lstrip("/") or "postgres",
    }


def build_backup_command(conn: dict, output_file: Path):
    return [
        "pg_dump",
        "--format=custom",
        "--no-owner",
        "--no-privileges",
        f"--host={conn['host']}",
        f"--port={conn['port']}",
        f"--username={conn['user']}",
        f"--file={str(output_file)}",
        conn["database"],
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a PostgreSQL backup for GestorMEI")
    parser.add_argument(
        "--output-dir",
        default="backups",
        help="Directory where backup files will be stored (default: backups)",
    )
    args = parser.parse_args()

    database_url = os.getenv("DATABASE_URL", "")
    if not database_url:
        print("DATABASE_URL is not set.")
        return 1

    try:
        conn = parse_database_url(database_url)
    except ValueError as exc:
        print(str(exc))
        return 1

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"gestormei_{timestamp}.dump"

    command = build_backup_command(conn, output_file)
    env = os.environ.copy()
    env["PGPASSWORD"] = conn["password"]

    try:
        subprocess.run(command, check=True, env=env)
    except FileNotFoundError:
        print("pg_dump not found. Install PostgreSQL client tools and try again.")
        return 1
    except subprocess.CalledProcessError as exc:
        print(f"Backup failed with exit code {exc.returncode}")
        return exc.returncode

    print(f"Backup created successfully: {output_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
