"""Tests for SQL checker service."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.sql_checker import (
    SQLChecker,
    ErrorType,
    SyntaxCheckResult,
    ExecutionCheckResult,
)


class TestSQLCheckerSyntax:
    """Tests for SQL syntax checking."""

    @pytest.fixture
    def checker(self):
        """Create a SQLChecker instance."""
        return SQLChecker()

    @pytest.mark.asyncio
    async def test_valid_select_syntax(self, checker):
        """Test valid SELECT statement."""
        result = await checker.check_syntax("SELECT * FROM users")
        assert result.is_valid is True
        assert result.error_type is None
        assert result.error_message is None

    @pytest.mark.asyncio
    async def test_valid_select_with_where(self, checker):
        """Test valid SELECT with WHERE clause."""
        result = await checker.check_syntax(
            "SELECT * FROM users WHERE id = 1 AND name = 'test'"
        )
        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_valid_select_with_join(self, checker):
        """Test valid SELECT with JOIN."""
        result = await checker.check_syntax(
            "SELECT u.*, o.id FROM users u JOIN orders o ON u.id = o.user_id"
        )
        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_valid_insert_syntax(self, checker):
        """Test valid INSERT statement."""
        result = await checker.check_syntax(
            "INSERT INTO users (name, email) VALUES ('test', 'test@example.com')"
        )
        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_valid_update_syntax(self, checker):
        """Test valid UPDATE statement."""
        result = await checker.check_syntax(
            "UPDATE users SET name = 'test' WHERE id = 1"
        )
        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_valid_delete_syntax(self, checker):
        """Test valid DELETE statement."""
        result = await checker.check_syntax("DELETE FROM users WHERE id = 1")
        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_valid_with_clause(self, checker):
        """Test valid WITH clause."""
        result = await checker.check_syntax(
            "WITH cte AS (SELECT * FROM users) SELECT * FROM cte"
        )
        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_empty_sql(self, checker):
        """Test empty SQL."""
        result = await checker.check_syntax("")
        assert result.is_valid is False
        assert result.error_type == ErrorType.SYNTAX_ERROR
        assert "Empty SQL" in result.error_message

    @pytest.mark.asyncio
    async def test_whitespace_only_sql(self, checker):
        """Test SQL with only whitespace."""
        result = await checker.check_syntax("   ")
        assert result.is_valid is False
        assert result.error_type == ErrorType.SYNTAX_ERROR

    @pytest.mark.asyncio
    async def test_invalid_start_keyword(self, checker):
        """Test SQL with invalid start keyword."""
        result = await checker.check_syntax("TRUNCATE TABLE users")
        assert result.is_valid is False
        assert result.error_type == ErrorType.SYNTAX_ERROR
        assert "must start with" in result.error_message

    @pytest.mark.asyncio
    async def test_mismatched_parentheses(self, checker):
        """Test SQL with mismatched parentheses."""
        result = await checker.check_syntax("SELECT * FROM users WHERE id = (1")
        assert result.is_valid is False
        assert result.error_type == ErrorType.SYNTAX_ERROR
        assert "parentheses" in result.error_message

    @pytest.mark.asyncio
    async def test_unclosed_single_quote(self, checker):
        """Test SQL with unclosed single quote."""
        result = await checker.check_syntax("SELECT * FROM users WHERE name = 'test")
        assert result.is_valid is False
        assert result.error_type == ErrorType.SYNTAX_ERROR
        assert "single quotes" in result.error_message

    @pytest.mark.asyncio
    async def test_unclosed_double_quote(self, checker):
        """Test SQL with unclosed double quote."""
        result = await checker.check_syntax('SELECT * FROM users WHERE name = "test')
        assert result.is_valid is False
        assert result.error_type == ErrorType.SYNTAX_ERROR
        assert "double quotes" in result.error_message

    @pytest.mark.asyncio
    async def test_escaped_quotes_valid(self, checker):
        """Test SQL with escaped quotes is valid."""
        result = await checker.check_syntax("SELECT * FROM users WHERE name = 'it''s'")
        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_dialect_mysql(self, checker):
        """Test MySQL dialect checking."""
        result = await checker.check_syntax("SELECT * FROM users", dialect="mysql")
        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_dialect_postgresql(self, checker):
        """Test PostgreSQL dialect checking."""
        result = await checker.check_syntax("SELECT * FROM users", dialect="postgresql")
        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_dialect_sqlite(self, checker):
        """Test SQLite dialect checking."""
        result = await checker.check_syntax("SELECT * FROM users", dialect="sqlite")
        assert result.is_valid is True


class TestSQLCheckerClassifyError:
    """Tests for error classification."""

    def test_classify_syntax_error(self):
        """Test classifying syntax errors."""
        assert (
            SQLChecker.classify_error("syntax error near 'SELECT'")
            == ErrorType.SYNTAX_ERROR
        )
        assert (
            SQLChecker.classify_error("parse error: unexpected token")
            == ErrorType.SYNTAX_ERROR
        )
        assert (
            SQLChecker.classify_error("invalid syntax at line 1")
            == ErrorType.SYNTAX_ERROR
        )

    def test_classify_table_not_found(self):
        """Test classifying table not found errors."""
        assert (
            SQLChecker.classify_error("table 'users' not found")
            == ErrorType.TABLE_NOT_FOUND
        )
        assert (
            SQLChecker.classify_error("table 'orders' doesn't exist")
            == ErrorType.TABLE_NOT_FOUND
        )
        assert (
            SQLChecker.classify_error("no such table: products")
            == ErrorType.TABLE_NOT_FOUND
        )

    def test_classify_column_not_found(self):
        """Test classifying column not found errors."""
        assert (
            SQLChecker.classify_error("column 'name' not found")
            == ErrorType.COLUMN_NOT_FOUND
        )
        assert (
            SQLChecker.classify_error("no such column: email")
            == ErrorType.COLUMN_NOT_FOUND
        )

    def test_classify_permission_error(self):
        """Test classifying permission errors."""
        assert (
            SQLChecker.classify_error("permission denied for table users")
            == ErrorType.PERMISSION_ERROR
        )
        assert (
            SQLChecker.classify_error("access denied")
            == ErrorType.PERMISSION_ERROR
        )

    def test_classify_timeout(self):
        """Test classifying timeout errors."""
        assert SQLChecker.classify_error("query timeout") == ErrorType.TIMEOUT
        assert (
            SQLChecker.classify_error("execution timed out after 30s")
            == ErrorType.TIMEOUT
        )

    def test_classify_execution_error(self):
        """Test classifying generic execution errors."""
        assert (
            SQLChecker.classify_error("division by zero")
            == ErrorType.EXECUTION_ERROR
        )
        assert (
            SQLChecker.classify_error("data type mismatch")
            == ErrorType.EXECUTION_ERROR
        )

    def test_classify_unknown_error(self):
        """Test classifying unknown errors."""
        assert SQLChecker.classify_error("") == ErrorType.UNKNOWN
        assert SQLChecker.classify_error(None) == ErrorType.UNKNOWN


class TestSQLCheckerExecution:
    """Tests for SQL execution checking."""

    @pytest.fixture
    def checker(self):
        """Create a SQLChecker instance."""
        return SQLChecker(timeout_seconds=5.0)

    @pytest.fixture
    def mock_engine(self):
        """Create a mock database engine."""
        engine = MagicMock()
        engine.url = "sqlite+aiosqlite:///:memory:"
        return engine

    @pytest.mark.asyncio
    async def test_successful_execution(self, checker, mock_engine):
        """Test successful SQL execution."""
        # Mock the connection and execution
        mock_conn = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [{"id": 1, "name": "test"}]
        mock_result.keys.return_value = ["id", "name"]

        mock_conn.execute.return_value = mock_result
        mock_engine.connect.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_engine.connect.return_value.__aexit__ = AsyncMock(return_value=None)

        result = await checker.check_execution(
            "SELECT * FROM users", mock_engine, timeout=5.0
        )

        assert result.success is True
        assert result.error_type is None
        assert result.error_message is None
        assert result.row_count == 1

    @pytest.mark.asyncio
    async def test_execution_timeout(self, checker, mock_engine):
        """Test SQL execution timeout."""
        import asyncio

        # Mock the connection to raise timeout
        mock_conn = AsyncMock()
        mock_conn.execute.side_effect = asyncio.TimeoutError()

        mock_engine.connect.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_engine.connect.return_value.__aexit__ = AsyncMock(return_value=None)

        result = await checker.check_execution(
            "SELECT * FROM users", mock_engine, timeout=1.0
        )

        assert result.success is False
        assert result.error_type == ErrorType.TIMEOUT
        assert "timeout" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_execution_syntax_error(self, checker, mock_engine):
        """Test SQL execution with syntax error."""
        # Mock the connection to raise syntax error
        mock_conn = AsyncMock()
        mock_conn.execute.side_effect = Exception("syntax error near 'FROM'")

        mock_engine.connect.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_engine.connect.return_value.__aexit__ = AsyncMock(return_value=None)

        result = await checker.check_execution(
            "SELECT * FORM users", mock_engine, timeout=5.0
        )

        assert result.success is False
        assert result.error_type == ErrorType.SYNTAX_ERROR

    @pytest.mark.asyncio
    async def test_execution_table_not_found(self, checker, mock_engine):
        """Test SQL execution with table not found error."""
        # Mock the connection to raise table not found error
        mock_conn = AsyncMock()
        mock_conn.execute.side_effect = Exception("no such table: nonexistent")

        mock_engine.connect.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_engine.connect.return_value.__aexit__ = AsyncMock(return_value=None)

        result = await checker.check_execution(
            "SELECT * FROM nonexistent", mock_engine, timeout=5.0
        )

        assert result.success is False
        assert result.error_type == ErrorType.TABLE_NOT_FOUND

    @pytest.mark.asyncio
    async def test_execution_with_gold_sql_comparison(self, checker, mock_engine):
        """Test SQL execution with gold SQL comparison."""
        # Mock the connection and execution
        mock_conn = AsyncMock()

        # First call for pred_sql, second for gold_sql
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [{"count": 5}]
        mock_result.keys.return_value = ["count"]

        mock_conn.execute.return_value = mock_result
        mock_engine.connect.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_engine.connect.return_value.__aexit__ = AsyncMock(return_value=None)

        result = await checker.check_execution(
            "SELECT COUNT(*) FROM users",
            mock_engine,
            timeout=5.0,
            gold_sql="SELECT COUNT(*) FROM users",
        )

        assert result.success is True


class TestSQLCheckerBatch:
    """Tests for batch SQL checking."""

    @pytest.fixture
    def checker(self):
        """Create a SQLChecker instance."""
        return SQLChecker()

    @pytest.fixture
    def mock_engine(self):
        """Create a mock database engine."""
        engine = MagicMock()
        engine.url = "sqlite+aiosqlite:///:memory:"
        return engine

    @pytest.mark.asyncio
    async def test_check_batch_empty(self, checker, mock_engine):
        """Test batch checking with empty list."""
        results = await checker.check_batch([], mock_engine)
        assert results == []

    @pytest.mark.asyncio
    async def test_check_batch_single_sql(self, checker, mock_engine):
        """Test batch checking with single SQL."""
        # Mock the connection and execution
        mock_conn = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [{"id": 1}]
        mock_result.keys.return_value = ["id"]

        mock_conn.execute.return_value = mock_result
        mock_engine.connect.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_engine.connect.return_value.__aexit__ = AsyncMock(return_value=None)

        results = await checker.check_batch(
            ["SELECT * FROM users"], mock_engine, timeout=5.0
        )

        assert len(results) == 1
        assert results[0].success is True

    @pytest.mark.asyncio
    async def test_check_batch_multiple_sqls(self, checker, mock_engine):
        """Test batch checking with multiple SQLs."""
        # Mock the connection and execution
        mock_conn = AsyncMock()

        # Different results for different calls
        mock_results = [
            MagicMock(fetchall=lambda: [{"id": 1}], keys=lambda: ["id"]),
            MagicMock(fetchall=lambda: [{"count": 10}], keys=lambda: ["count"]),
        ]

        mock_conn.execute.side_effect = mock_results
        mock_engine.connect.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_engine.connect.return_value.__aexit__ = AsyncMock(return_value=None)

        results = await checker.check_batch(
            ["SELECT * FROM users", "SELECT COUNT(*) FROM orders"],
            mock_engine,
            timeout=5.0,
        )

        assert len(results) == 2
        assert all(r.success for r in results)
