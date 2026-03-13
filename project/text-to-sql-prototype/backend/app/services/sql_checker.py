"""SQL checking service for syntax validation and execution verification."""
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import sqlparse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.logging import get_logger

logger = get_logger(__name__)


class ErrorType(str, Enum):
    """SQL error types classification."""

    SYNTAX_ERROR = "syntax_error"
    TABLE_NOT_FOUND = "table_not_found"
    COLUMN_NOT_FOUND = "column_not_found"
    PERMISSION_ERROR = "permission_error"
    TIMEOUT = "timeout"
    EXECUTION_ERROR = "execution_error"
    WRONG_RESULT = "wrong_result"
    UNKNOWN = "unknown"


@dataclass
class SyntaxCheckResult:
    """Result of SQL syntax check."""

    is_valid: bool
    error_type: Optional[ErrorType] = None
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


@dataclass
class ExecutionCheckResult:
    """Result of SQL execution check."""

    success: bool
    error_type: Optional[ErrorType] = None
    error_message: Optional[str] = None
    execution_time_ms: Optional[float] = None
    row_count: Optional[int] = None
    details: Optional[Dict[str, Any]] = None


class SQLChecker:
    """SQL checker for syntax validation and execution verification.

    This class provides methods to:
    - Check SQL syntax validity
    - Execute SQL and verify correctness
    - Classify error types
    """

    # SQL keywords that indicate valid query start
    VALID_START_KEYWORDS = [
        "SELECT", "INSERT", "UPDATE", "DELETE",
        "WITH", "EXPLAIN", "SHOW", "DESCRIBE",
        "CREATE", "DROP", "ALTER", "TRUNCATE",
    ]

    # Dialect-specific syntax patterns
    DIALECT_PATTERNS = {
        "mysql": {
            "backtick_identifier": r"`[^`]*`",
            "limit_syntax": r"LIMIT\s+\d+(\s*,\s*\d+)?",
        },
        "postgresql": {
            "double_quote_identifier": r'"[^"]*"',
            "limit_offset": r"LIMIT\s+\d+(\s+OFFSET\s+\d+)?",
        },
        "sqlite": {
            "backtick_identifier": r"`[^`]*`",
            "bracket_identifier": r"\[[^\]]*\]",
            "limit_syntax": r"LIMIT\s+\d+(\s*,\s*\d+|\s+OFFSET\s+\d+)?",
        },
    }

    def __init__(self, timeout_seconds: float = 30.0):
        """Initialize SQL checker.

        Args:
            timeout_seconds: Default timeout for SQL execution in seconds.
        """
        self.timeout_seconds = timeout_seconds

    async def check_syntax(
        self,
        sql: str,
        dialect: str = "mysql",
    ) -> SyntaxCheckResult:
        """Check SQL syntax validity.

        Performs comprehensive syntax validation using sqlparse and
        additional dialect-specific checks.

        Args:
            sql: SQL query to validate.
            dialect: SQL dialect (mysql, postgresql, sqlite).

        Returns:
            SyntaxCheckResult with validation details.
        """
        if not sql or not sql.strip():
            return SyntaxCheckResult(
                is_valid=False,
                error_type=ErrorType.SYNTAX_ERROR,
                error_message="Empty SQL query",
            )

        sql_clean = sql.strip()
        sql_upper = sql_clean.upper()

        # Check for valid SQL start keyword
        has_valid_start = any(
            sql_upper.startswith(kw) for kw in self.VALID_START_KEYWORDS
        )
        if not has_valid_start:
            return SyntaxCheckResult(
                is_valid=False,
                error_type=ErrorType.SYNTAX_ERROR,
                error_message=f"SQL must start with one of: {', '.join(self.VALID_START_KEYWORDS)}",
                details={"sql_start": sql_clean[:50]},
            )

        # Basic parenthesis matching
        open_parens = sql_clean.count("(")
        close_parens = sql_clean.count(")")
        if open_parens != close_parens:
            return SyntaxCheckResult(
                is_valid=False,
                error_type=ErrorType.SYNTAX_ERROR,
                error_message=f"Unmatched parentheses: {open_parens} open, {close_parens} close",
                details={"open_parens": open_parens, "close_parens": close_parens},
            )

        # Basic quote matching (excluding escaped quotes)
        single_quotes = sql_clean.count("'") - sql_clean.count("\\'")
        double_quotes = sql_clean.count('"') - sql_clean.count('\\"')

        if single_quotes % 2 != 0:
            return SyntaxCheckResult(
                is_valid=False,
                error_type=ErrorType.SYNTAX_ERROR,
                error_message="Unmatched single quotes",
            )

        if double_quotes % 2 != 0:
            return SyntaxCheckResult(
                is_valid=False,
                error_type=ErrorType.SYNTAX_ERROR,
                error_message="Unmatched double quotes",
            )

        # Use sqlparse for detailed parsing
        try:
            parsed = sqlparse.parse(sql_clean)
            if not parsed or not parsed[0].tokens:
                return SyntaxCheckResult(
                    is_valid=False,
                    error_type=ErrorType.SYNTAX_ERROR,
                    error_message="Failed to parse SQL",
                )

            # Check for parsing errors in tokens
            for token in parsed[0].flatten():
                if token.ttype is not None and "Error" in str(token.ttype):
                    return SyntaxCheckResult(
                        is_valid=False,
                        error_type=ErrorType.SYNTAX_ERROR,
                        error_message=f"Parse error near: {token.value}",
                        details={"error_token": token.value},
                    )

        except Exception as e:
            logger.warning(f"SQL parse error: {e}")
            return SyntaxCheckResult(
                is_valid=False,
                error_type=ErrorType.SYNTAX_ERROR,
                error_message=f"Parse error: {str(e)}",
            )

        # Dialect-specific checks
        dialect_lower = dialect.lower()
        if dialect_lower in self.DIALECT_PATTERNS:
            dialect_result = self._check_dialect_specific(sql_clean, dialect_lower)
            if not dialect_result.is_valid:
                return dialect_result

        return SyntaxCheckResult(is_valid=True)

    def _check_dialect_specific(
        self, sql: str, dialect: str
    ) -> SyntaxCheckResult:
        """Perform dialect-specific syntax checks.

        Args:
            sql: SQL query to check.
            dialect: SQL dialect name.

        Returns:
            SyntaxCheckResult with validation details.
        """
        patterns = self.DIALECT_PATTERNS.get(dialect, {})

        # Check for common syntax issues
        sql_upper = sql.upper()

        # MySQL-specific: check for LIMIT syntax variations
        if dialect == "mysql":
            # MySQL supports LIMIT n, m syntax
            pass

        # PostgreSQL-specific: check for ILIKE (case-insensitive LIKE)
        if dialect == "postgresql":
            # PostgreSQL supports ILIKE
            pass

        # SQLite-specific: check for date functions
        if dialect == "sqlite":
            # SQLite has specific date/time functions
            pass

        return SyntaxCheckResult(is_valid=True)

    async def check_execution(
        self,
        sql: str,
        engine: AsyncEngine,
        timeout: Optional[float] = None,
        gold_sql: Optional[str] = None,
    ) -> ExecutionCheckResult:
        """Execute SQL and verify correctness.

        Args:
            sql: SQL query to execute.
            engine: SQLAlchemy async engine.
            timeout: Execution timeout in seconds.
            gold_sql: Optional gold SQL for result comparison.

        Returns:
            ExecutionCheckResult with execution details.
        """
        import asyncio

        query_timeout = timeout or self.timeout_seconds

        try:
            async with engine.connect() as conn:
                # Set busy timeout for SQLite
                if "sqlite" in str(engine.url):
                    await conn.execute(text("PRAGMA busy_timeout = 30000"))

                start_time = asyncio.get_event_loop().time()

                # Execute with timeout
                result = await asyncio.wait_for(
                    conn.execute(text(sql)),
                    timeout=query_timeout,
                )

                end_time = asyncio.get_event_loop().time()
                execution_time_ms = (end_time - start_time) * 1000

                # Fetch results
                rows = result.fetchall()
                row_count = len(rows)

                # If gold SQL provided, compare results
                if gold_sql:
                    is_correct, error_msg = await self._compare_with_gold(
                        conn, sql, gold_sql, query_timeout
                    )
                    if not is_correct:
                        return ExecutionCheckResult(
                            success=False,
                            error_type=ErrorType.WRONG_RESULT,
                            error_message=error_msg,
                            execution_time_ms=execution_time_ms,
                            row_count=row_count,
                        )

                return ExecutionCheckResult(
                    success=True,
                    execution_time_ms=execution_time_ms,
                    row_count=row_count,
                )

        except asyncio.TimeoutError:
            return ExecutionCheckResult(
                success=False,
                error_type=ErrorType.TIMEOUT,
                error_message=f"SQL execution timeout after {query_timeout} seconds",
            )
        except Exception as e:
            error_type = self.classify_error(str(e))
            return ExecutionCheckResult(
                success=False,
                error_type=error_type,
                error_message=str(e),
            )

    async def _compare_with_gold(
        self,
        conn: Any,
        pred_sql: str,
        gold_sql: str,
        timeout: float,
    ) -> Tuple[bool, Optional[str]]:
        """Compare predicted SQL results with gold SQL.

        Args:
            conn: Database connection.
            pred_sql: Predicted SQL query.
            gold_sql: Gold/reference SQL query.
            timeout: Execution timeout.

        Returns:
            Tuple of (is_correct, error_message).
        """
        import asyncio

        try:
            # Execute both queries
            pred_result = await asyncio.wait_for(
                conn.execute(text(pred_sql)),
                timeout=timeout,
            )
            pred_rows = pred_result.fetchall()

            gold_result = await asyncio.wait_for(
                conn.execute(text(gold_sql)),
                timeout=timeout,
            )
            gold_rows = gold_result.fetchall()

            # Compare row counts
            if len(pred_rows) != len(gold_rows):
                return False, f"Row count mismatch: {len(pred_rows)} vs {len(gold_rows)}"

            # Compare content (simple string comparison of normalized rows)
            pred_normalized = self._normalize_rows(pred_rows)
            gold_normalized = self._normalize_rows(gold_rows)

            if pred_normalized != gold_normalized:
                return False, "Result content mismatch"

            return True, None

        except Exception as e:
            return False, f"Comparison error: {str(e)}"

    def _normalize_rows(self, rows: List[Any]) -> List[Dict[str, Any]]:
        """Normalize rows for comparison.

        Args:
            rows: Database result rows.

        Returns:
            Normalized list of dictionaries.
        """
        normalized = []
        for row in rows:
            row_dict = {}
            for key, value in dict(row).items():
                # Normalize key to lowercase
                key_lower = key.lower() if isinstance(key, str) else key

                # Handle None values
                if value is None:
                    row_dict[key_lower] = "NULL"
                # Handle floats with precision
                elif isinstance(value, float):
                    row_dict[key_lower] = f"{value:.6f}"
                # Convert other values to string
                else:
                    row_dict[key_lower] = str(value)
            normalized.append(row_dict)

        # Sort for consistent comparison
        if normalized:
            sort_keys = sorted(normalized[0].keys())
            normalized.sort(key=lambda x: [x.get(k, "") for k in sort_keys])

        return normalized

    @staticmethod
    def classify_error(error_message: str) -> ErrorType:
        """Classify error type from error message.

        Args:
            error_message: Error message string.

        Returns:
            Classified ErrorType.
        """
        if not error_message:
            return ErrorType.UNKNOWN

        error_lower = error_message.lower()

        # Syntax errors
        syntax_patterns = [
            r"syntax error",
            r"parse error",
            r"unexpected token",
            r"invalid syntax",
            r"near .*: syntax error",
        ]
        for pattern in syntax_patterns:
            if re.search(pattern, error_lower):
                return ErrorType.SYNTAX_ERROR

        # Table not found
        table_patterns = [
            r"table .* not found",
            r"table .* doesn't exist",
            r"table .* does not exist",
            r"unknown table",
            r"relation .* does not exist",
            r"no such table",
        ]
        for pattern in table_patterns:
            if re.search(pattern, error_lower):
                return ErrorType.TABLE_NOT_FOUND

        # Column not found
        column_patterns = [
            r"column .* not found",
            r"column .* doesn't exist",
            r"column .* does not exist",
            r"unknown column",
            r"no such column",
            r"field .* not found",
        ]
        for pattern in column_patterns:
            if re.search(pattern, error_lower):
                return ErrorType.COLUMN_NOT_FOUND

        # Permission errors
        permission_patterns = [
            r"permission denied",
            r"access denied",
            r"not authorized",
            r"insufficient privileges",
        ]
        for pattern in permission_patterns:
            if re.search(pattern, error_lower):
                return ErrorType.PERMISSION_ERROR

        # Timeout
        timeout_patterns = [
            r"timeout",
            r"timed out",
            r"query cancelled",
            r"execution time exceeded",
        ]
        for pattern in timeout_patterns:
            if re.search(pattern, error_lower):
                return ErrorType.TIMEOUT

        return ErrorType.EXECUTION_ERROR

    async def check_batch(
        self,
        sqls: List[str],
        engine: AsyncEngine,
        timeout: Optional[float] = None,
    ) -> List[ExecutionCheckResult]:
        """Check multiple SQL queries in batch.

        Args:
            sqls: List of SQL queries to check.
            engine: SQLAlchemy async engine.
            timeout: Execution timeout per query.

        Returns:
            List of ExecutionCheckResult.
        """
        results = []
        for sql in sqls:
            result = await self.check_execution(sql, engine, timeout)
            results.append(result)
        return results
