#!/usr/bin/env python3
"""
Create database connections for ICED BIRD datasets.

This script creates database connections in text-to-sql-prototype for each
BIRD database. It generates a mapping file (db_id_mapping.json) that maps
db_id to connection_id.

Usage:
    export JWT_TOKEN="your_token_here"
    python create_connections.py
    python create_connections.py --token "your_token" --base-url "http://localhost:8000"
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, Optional

try:
    import requests
except ImportError:
    print("Error: requests library is required. Install with: pip install requests")
    sys.exit(1)


def get_jwt_token(args_token: Optional[str]) -> str:
    """Get JWT token from args or environment variable.

    Args:
        args_token: Token from command line arguments.

    Returns:
        JWT token string.

    Raises:
        SystemExit: If token is not provided.
    """
    token = args_token or os.environ.get("JWT_TOKEN")

    if not token:
        print("Error: JWT token is required.", file=sys.stderr)
        print("Set JWT_TOKEN environment variable or use --token option.", file=sys.stderr)
        print("\nTo get a token:", file=sys.stderr)
        print('  curl -X POST http://localhost:8000/api/v1/auth/login \\', file=sys.stderr)
        print('    -H "Content-Type: application/json" \\', file=sys.stderr)
        print('    -d \'{"username": "admin", "password": "admin123"}\'', file=sys.stderr)
        sys.exit(1)

    return token


def create_connection(
    db_id: str,
    token: str,
    base_url: str,
    data_dir: Path
) -> Optional[int]:
    """Create a database connection via API.

    Args:
        db_id: Database identifier.
        token: JWT token for authentication.
        base_url: API base URL.
        data_dir: Path to data directory containing databases.

    Returns:
        Connection ID if successful, None otherwise.
    """
    # Build absolute path for SQLite database
    sqlite_path = (data_dir / "databases" / f"{db_id}.sqlite").resolve()

    if not sqlite_path.exists():
        print(f"  [ERROR] Database file not found: {sqlite_path}")
        return None

    # Convert to forward slashes for consistency
    sqlite_path_str = str(sqlite_path).replace("\\", "/")

    payload = {
        "name": f"BIRD - {db_id}",
        "db_type": "sqlite",
        "database": sqlite_path_str,
        "host": None,
        "port": None,
        "username": None,
        "password": None
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            f"{base_url}/api/v1/connections",
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code == 201:
            connection_id = response.json().get("id")
            print(f"  [OK] Created connection {connection_id} for {db_id}")
            return connection_id
        elif response.status_code == 401:
            print(f"  [ERROR] Authentication failed. Check your JWT token.")
            return None
        else:
            print(f"  [ERROR] Failed to create connection for {db_id}: {response.status_code}")
            print(f"         Response: {response.text}")
            return None

    except requests.exceptions.ConnectionError:
        print(f"  [ERROR] Cannot connect to {base_url}. Is the backend running?")
        return None
    except requests.exceptions.Timeout:
        print(f"  [ERROR] Request timeout.")
        return None
    except Exception as e:
        print(f"  [ERROR] Exception: {e}")
        return None


def refresh_connection_schema(
    connection_id: int,
    token: str,
    base_url: str
) -> bool:
    """Refresh schema for a connection.

    Args:
        connection_id: Connection ID.
        token: JWT token.
        base_url: API base URL.

    Returns:
        True if successful.
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            f"{base_url}/api/v1/connections/{connection_id}/schema/refresh",
            headers=headers,
            timeout=60
        )

        if response.status_code == 200:
            print(f"  [OK] Refreshed schema for connection {connection_id}")
            return True
        else:
            print(f"  [WARN] Failed to refresh schema: {response.status_code}")
            return False

    except Exception as e:
        print(f"  [WARN] Exception refreshing schema: {e}")
        return False


def load_db_ids(data_dir: Path) -> list:
    """Load db_id list from dataset file.

    Args:
        data_dir: Path to data directory.

    Returns:
        List of db_id strings.
    """
    dataset_path = data_dir / "bird_dev.json"

    if not dataset_path.exists():
        print(f"Error: Dataset file not found: {dataset_path}", file=sys.stderr)
        print("Run copy_bird_data.py first.", file=sys.stderr)
        sys.exit(1)

    with open(dataset_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    db_ids = sorted(set(item["db_id"] for item in dataset if "db_id" in item))
    return db_ids


def create_connections(
    token: str,
    base_url: str,
    data_dir: Path,
    refresh_schema: bool = True
) -> Dict[str, int]:
    """Create connections for all BIRD databases.

    Args:
        token: JWT token.
        base_url: API base URL.
        data_dir: Path to data directory.
        refresh_schema: Whether to refresh schema after creation.

    Returns:
        Dictionary mapping db_id to connection_id.
    """
    db_ids = load_db_ids(data_dir)
    print(f"[INFO] Found {len(db_ids)} databases to process")

    mapping = {}
    failed = []

    for i, db_id in enumerate(db_ids, 1):
        print(f"\n[{i}/{len(db_ids)}] Creating connection for {db_id}...")

        connection_id = create_connection(db_id, token, base_url, data_dir)

        if connection_id:
            mapping[db_id] = connection_id

            # Refresh schema if requested
            if refresh_schema:
                refresh_connection_schema(connection_id, token, base_url)
        else:
            failed.append(db_id)

    return mapping, failed


def save_mapping(mapping: Dict[str, int], output_path: Path) -> None:
    """Save db_id to connection_id mapping to file.

    Args:
        mapping: Dictionary mapping db_id to connection_id.
        output_path: Path to output file.
    """
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Mapping saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Create database connections for ICED BIRD datasets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment Variables:
  JWT_TOKEN    JWT token for API authentication (alternative to --token)

Examples:
  export JWT_TOKEN="eyJ0eXAiOiJKV1QiLCJhbGc..."
  python create_connections.py

  python create_connections.py --token "eyJ0eXAiOiJKV1QiLCJhbGc..." --base-url "http://localhost:8000"
        """
    )

    default_data_dir = "D:/Working/paper/project/text-to-sql-prototype/backend/data/bird"

    parser.add_argument(
        "--token",
        type=str,
        default=None,
        help="JWT token for API authentication (or set JWT_TOKEN env var)"
    )

    parser.add_argument(
        "--base-url",
        type=str,
        default="http://localhost:8000",
        help="API base URL (default: http://localhost:8000)"
    )

    parser.add_argument(
        "--data-dir",
        type=str,
        default=default_data_dir,
        help=f"Path to data directory (default: {default_data_dir})"
    )

    parser.add_argument(
        "--no-refresh-schema",
        action="store_true",
        help="Skip schema refresh after creating connections"
    )

    args = parser.parse_args()

    # Get JWT token
    token = get_jwt_token(args.token)

    data_dir = Path(args.data_dir)

    print("="*50)
    print("ICED BIRD Connection Creation Tool")
    print("="*50)
    print(f"\nAPI URL: {args.base_url}")
    print(f"Data directory: {data_dir}")

    # Create connections
    mapping, failed = create_connections(
        token=token,
        base_url=args.base_url,
        data_dir=data_dir,
        refresh_schema=not args.no_refresh_schema
    )

    # Save mapping
    if mapping:
        mapping_path = data_dir / "db_id_mapping.json"
        save_mapping(mapping, mapping_path)

    # Summary
    print(f"\n{'='*50}")
    print("Summary:")
    print(f"  Total databases: {len(load_db_ids(data_dir))}")
    print(f"  Successfully created: {len(mapping)}")
    print(f"  Failed: {len(failed)}")

    if failed:
        print(f"\n  Failed databases: {failed}")

    print(f"{'='*50}")

    if failed:
        print("\n[WARNING] Some connections failed. Check errors above.")
        sys.exit(1)
    else:
        print("\n[Done] All connections created successfully!")


if __name__ == "__main__":
    main()
