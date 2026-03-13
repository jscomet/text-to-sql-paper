#!/usr/bin/env python3
"""
Copy ICED BIRD dataset to text-to-sql-prototype.

This script copies the BIRD dev dataset files from ICED-2026-paper-code project
to the text-to-sql-prototype backend data directory.

Usage:
    python copy_bird_data.py
    python copy_bird_data.py --iced-dir "/path/to/iced/data/bird" --output-dir "/path/to/output"
"""

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import List, Set


def get_unique_db_ids(dataset_path: Path) -> Set[str]:
    """Extract unique db_ids from the dataset file.

    Args:
        dataset_path: Path to the dataset JSON file.

    Returns:
        Set of unique db_id strings.
    """
    with open(dataset_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    db_ids = set(item["db_id"] for item in dataset if "db_id" in item)
    return db_ids


def copy_bird_data(iced_dir: Path, output_dir: Path) -> List[str]:
    """Copy BIRD dataset files from ICED to prototype.

    Args:
        iced_dir: Path to ICED data directory (e.g., ICED-2026-paper-code/data/bird).
        output_dir: Path to output directory (e.g., text-to-sql-prototype/backend/data/bird).

    Returns:
        List of copied database IDs.
    """
    # Validate input directory
    if not iced_dir.exists():
        print(f"Error: ICED directory not found: {iced_dir}", file=sys.stderr)
        sys.exit(1)

    dev_json_path = iced_dir / "dev.json"
    if not dev_json_path.exists():
        print(f"Error: dev.json not found in {iced_dir}", file=sys.stderr)
        sys.exit(1)

    dev_databases_dir = iced_dir / "dev_databases"
    if not dev_databases_dir.exists():
        print(f"Error: dev_databases directory not found in {iced_dir}", file=sys.stderr)
        sys.exit(1)

    # Create output directories
    databases_dir = output_dir / "databases"
    databases_dir.mkdir(parents=True, exist_ok=True)

    print(f"Output directory: {output_dir}")
    print(f"Databases directory: {databases_dir}")

    # Copy dataset file
    output_json_path = output_dir / "bird_dev.json"
    print(f"\n[INFO] Copying dataset file...")
    shutil.copy(dev_json_path, output_json_path)
    print(f"[OK] Copied to {output_json_path}")

    # Get unique db_ids
    print(f"\n[INFO] Reading dataset to extract database list...")
    db_ids = get_unique_db_ids(dev_json_path)
    db_ids = sorted(db_ids)
    print(f"[OK] Found {len(db_ids)} unique databases: {db_ids}")

    # Copy SQLite databases
    print(f"\n[INFO] Copying SQLite databases...")
    copied_db_ids = []
    missing_dbs = []

    for db_id in db_ids:
        source_db = dev_databases_dir / db_id / f"{db_id}.sqlite"
        dest_db = databases_dir / f"{db_id}.sqlite"

        if source_db.exists():
            shutil.copy(source_db, dest_db)
            print(f"[OK] Copied {db_id}")
            copied_db_ids.append(db_id)
        else:
            print(f"[WARN] Missing database file: {source_db}")
            missing_dbs.append(db_id)

    # Summary
    print(f"\n{'='*50}")
    print(f"Summary:")
    print(f"  Total databases in dataset: {len(db_ids)}")
    print(f"  Successfully copied: {len(copied_db_ids)}")
    print(f"  Missing: {len(missing_dbs)}")

    if missing_dbs:
        print(f"\n  Missing databases: {missing_dbs}")

    print(f"\n  Dataset file: {output_json_path}")
    print(f"  Database files: {databases_dir}")
    print(f"{'='*50}")

    return copied_db_ids


def main():
    parser = argparse.ArgumentParser(
        description="Copy ICED BIRD dataset to text-to-sql-prototype",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python copy_bird_data.py
  python copy_bird_data.py --iced-dir "D:/ICED/data/bird" --output-dir "D:/prototype/backend/data/bird"
        """
    )

    # Default paths for the project structure
    default_iced_dir = "D:/Working/paper/project/ICED-2026-paper-code/data/bird"
    default_output_dir = "D:/Working/paper/project/text-to-sql-prototype/backend/data/bird"

    parser.add_argument(
        "--iced-dir",
        type=str,
        default=default_iced_dir,
        help=f"Path to ICED data directory (default: {default_iced_dir})"
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default=default_output_dir,
        help=f"Path to output directory (default: {default_output_dir})"
    )

    args = parser.parse_args()

    iced_dir = Path(args.iced_dir)
    output_dir = Path(args.output_dir)

    print("="*50)
    print("ICED BIRD Dataset Copy Tool")
    print("="*50)
    print(f"\nSource: {iced_dir}")
    print(f"Target: {output_dir}")

    copy_bird_data(iced_dir, output_dir)

    print("\n[Done] Dataset copy completed successfully!")


if __name__ == "__main__":
    main()
