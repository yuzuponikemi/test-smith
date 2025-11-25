#!/usr/bin/env python3
"""Clean up old log and report files."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.logging_utils import cleanup_old_files

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Clean up old logs and reports")
    parser.add_argument("--days", type=int, default=30, help="Delete files older than N days")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted without deleting")

    args = parser.parse_args()

    deleted = cleanup_old_files(days=args.days, dry_run=args.dry_run)

    if args.dry_run:
        print("\nWould delete:")
    else:
        print("\nDeleted:")

    print(f"  - {deleted['logs']} log files")
    print(f"  - {deleted['reports']} report files")
