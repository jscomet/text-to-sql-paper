"""SQL execution service with safety checks and timeout."""
import asyncio
import re
from typing import Any, Dict, List, Optional

import sqlparse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger

logger = get_logger(__name__)

# Dangerous SQL keywords to block
DANGEROUS_KEYWORDS = [
    "INSERT", "UPDATE", "DELETE", "DROP", "CREATE",
    "ALTER", "TRUNCATE", "GRANT", "REVOKE", "EXEC",
    "EXECUTE", "MERGE", "UPSERT", "REPLACE",
]

# Read-only allowed keywords
ALLOWED_KEYWORDS = ["SELECT", "SHOW", "DESCRIBE", "EXPLAIN"]


class SQLExecutorService:
    """Service for executing SQL queries with safety checks."""

    def __init__(self, timeout_seconds: float = 30.0):
        """Initialize SQL executor.

        Args:
            timeout_seconds: Query timeout in seconds.
        """
        self.timeout_seconds = timeout_seconds

    async def execute_sql(
        self,
        sql: str,
        db_session: AsyncSession,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Execute SQL query with safety checks and timeout.

        Args:
            sql: SQL query to execute.
            db_session: Database session.
            timeout: Optional timeout override in seconds.

        Returns:
            Dictionary with execution results.
        """
        # Check SQL safety
        is_safe, error = self.check_sql_safety(sql)
        if not is_safe:
            return {
                "success": False,
                "error": error,
                "rows": [],
                "columns": [],
                "row_count": 0,
                "execution_time_ms": 0,
            }

        # Set timeout
        query_timeout = timeout or self.timeout_seconds

        try:
            start_time = asyncio.get_event_loop().time()

            # Execute with timeout
            result = await asyncio.wait_for(
                self._execute_query(sql, db_session),
                timeout=query_timeout,
            )

            end_time = asyncio.get_event_loop().time()
            execution_time_ms = (end_time - start_time) * 1000

            return {
                "success": True,
                "error": None,
                **result,
                "execution_time_ms": round(execution_time_ms, 2),
            }

        except asyncio.TimeoutError:
            logger.warning(f"SQL execution timed out after {query_timeout}s")
            return {
                "success": False,
                "error": f"Query timed out after {query_timeout} seconds",
                "rows": [],
                "columns": [],
                "row_count": 0,
                "execution_time_ms": query_timeout * 1000,
            }

        except Exception as e:
            logger.error(f"SQL execution failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "rows": [],
                "columns": [],
                "row_count": 0,
                "execution_time_ms": 0,
            }

    async def _execute_query(
        self,
        sql: str,
        db_session: AsyncSession,
    ) -> Dict[str, Any]:
        """Execute the actual SQL query.

        Args:
            sql: SQL query.
            db_session: Database session.

        Returns:
            Dictionary with query results.
        """
        # Execute query
        result = await db_session.execute(text(sql))

        # Fetch results
        rows = result.fetchall()

        # Get column names
        columns = list(result.keys()) if result.keys() else []

        # Format rows
        formatted_rows = []
        for row in rows:
            row_dict = {}
            for i, col in enumerate(columns):
                value = row[i]
                # Convert non-serializable types
                if hasattr(value, "isoformat"):  # datetime
                    row_dict[col] = value.isoformat()
                else:
                    row_dict[col] = value
            formatted_rows.append(row_dict)

        return {
            "rows": formatted_rows,
            "columns": columns,
            "row_count": len(formatted_rows),
        }

    def check_sql_safety(self, sql: str) -> tuple[bool, Optional[str]]:
        """Check if SQL is safe to execute.

        Args:
            sql: SQL query to check.

        Returns:
            Tuple of (is_safe, error_message).
        """
        if not sql or not sql.strip():
            return False, "Empty SQL query"

        # Normalize SQL for checking
        sql_upper = sql.upper().strip()

        # Check for dangerous keywords
        for keyword in DANGEROUS_KEYWORDS:
            pattern = r"\b" + keyword + r"\b"
            if re.search(pattern, sql_upper):
                return False, f"SQL contains forbidden keyword: {keyword}"

        # Must start with allowed keyword
        starts_with_allowed = any(
            sql_upper.startswith(kw) for kw in ALLOWED_KEYWORDS
        )
        if not starts_with_allowed:
            return False, f"SQL must start with one of: {', '.join(ALLOWED_KEYWORDS)}"

        # Parse and validate
        try:
            parsed = sqlparse.parse(sql)
            if not parsed:
                return False, "Failed to parse SQL"
        except Exception as e:
            return False, f"SQL parse error: {str(e)}"

        return True, None

    def format_results(
        self,
        rows: List[Dict[str, Any]],
        columns: List[str],
        max_rows: int = 100,
    ) -> Dict[str, Any]:
        """Format query results for display.

        Args:
            rows: Query result rows.
            columns: Column names.
            max_rows: Maximum rows to include.

        Returns:
            Formatted results dictionary.
        """
        total_rows = len(rows)
        truncated = total_rows > max_rows
        display_rows = rows[:max_rows]

        return {
            "columns": columns,
            "rows": display_rows,
            "total_rows": total_rows,
            "truncated": truncated,
            "displayed_rows": len(display_rows),
        }
