"""Tests for SQL executor service."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from app.services.sql_executor import SQLExecutorService


class TestSQLExecutorServiceInit:
    """Tests for SQLExecutorService initialization."""

    def test_default_timeout(self):
        """Test default timeout value."""
        service = SQLExecutorService()
        assert service.timeout_seconds == 30.0

    def test_custom_timeout(self):
        """Test custom timeout value."""
        service = SQLExecutorService(timeout_seconds=60.0)
        assert service.timeout_seconds == 60.0


class TestCheckSQLSafety:
    """Tests for SQL safety checking."""

    @pytest.fixture
    def service(self):
        return SQLExecutorService()

    def test_safe_select(self, service):
        """Test that SELECT is allowed."""
        is_safe, error = service.check_sql_safety("SELECT * FROM users")
        assert is_safe is True
        assert error is None

    def test_safe_select_with_where(self, service):
        """Test SELECT with WHERE clause."""
        is_safe, error = service.check_sql_safety("SELECT * FROM users WHERE id = 1")
        assert is_safe is True
        assert error is None

    def test_safe_show(self, service):
        """Test that SHOW is allowed."""
        is_safe, error = service.check_sql_safety("SHOW TABLES")
        assert is_safe is True
        assert error is None

    def test_safe_describe(self, service):
        """Test that DESCRIBE is allowed."""
        is_safe, error = service.check_sql_safety("DESCRIBE users")
        assert is_safe is True
        assert error is None

    def test_safe_explain(self, service):
        """Test that EXPLAIN is allowed."""
        is_safe, error = service.check_sql_safety("EXPLAIN SELECT * FROM users")
        assert is_safe is True
        assert error is None

    def test_blocked_insert(self, service):
        """Test that INSERT is blocked."""
        is_safe, error = service.check_sql_safety("INSERT INTO users VALUES (1)")
        assert is_safe is False
        assert "INSERT" in error

    def test_blocked_update(self, service):
        """Test that UPDATE is blocked."""
        is_safe, error = service.check_sql_safety("UPDATE users SET name = 'test'")
        assert is_safe is False
        assert "UPDATE" in error

    def test_blocked_delete(self, service):
        """Test that DELETE is blocked."""
        is_safe, error = service.check_sql_safety("DELETE FROM users")
        assert is_safe is False
        assert "DELETE" in error

    def test_blocked_drop(self, service):
        """Test that DROP is blocked."""
        is_safe, error = service.check_sql_safety("DROP TABLE users")
        assert is_safe is False
        assert "DROP" in error

    def test_blocked_create(self, service):
        """Test that CREATE is blocked."""
        is_safe, error = service.check_sql_safety("CREATE TABLE test (id INT)")
        assert is_safe is False
        assert "CREATE" in error

    def test_blocked_alter(self, service):
        """Test that ALTER is blocked."""
        is_safe, error = service.check_sql_safety("ALTER TABLE users ADD COLUMN name")
        assert is_safe is False
        assert "ALTER" in error

    def test_blocked_truncate(self, service):
        """Test that TRUNCATE is blocked."""
        is_safe, error = service.check_sql_safety("TRUNCATE TABLE users")
        assert is_safe is False
        assert "TRUNCATE" in error

    def test_case_insensitive_blocking(self, service):
        """Test that blocking is case insensitive."""
        is_safe, error = service.check_sql_safety("insert INTO users VALUES (1)")
        assert is_safe is False

    def test_empty_sql(self, service):
        """Test empty SQL."""
        is_safe, error = service.check_sql_safety("")
        assert is_safe is False
        assert "Empty" in error

    def test_whitespace_only_sql(self, service):
        """Test whitespace-only SQL."""
        is_safe, error = service.check_sql_safety("   ")
        assert is_safe is False

    def test_blocked_in_subquery(self, service):
        """Test that dangerous keywords in subqueries are blocked."""
        is_safe, error = service.check_sql_safety("SELECT * FROM (DELETE FROM users)")
        assert is_safe is False
        assert "DELETE" in error


class TestExecuteSQL:
    """Tests for SQL execution."""

    @pytest.fixture
    def service(self):
        return SQLExecutorService()

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        session = MagicMock()
        session.execute = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_execute_safe_query_success(self, service, mock_db_session):
        """Test successful execution of safe query."""
        # Mock the result
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            (1, "alice", "alice@example.com"),
            (2, "bob", "bob@example.com"),
        ]
        mock_result.keys.return_value = ["id", "username", "email"]
        mock_db_session.execute.return_value = mock_result

        result = await service.execute_sql(
            "SELECT * FROM users",
            mock_db_session,
        )

        assert result["success"] is True
        assert result["error"] is None
        assert result["row_count"] == 2
        assert len(result["columns"]) == 3
        assert len(result["rows"]) == 2

    @pytest.mark.asyncio
    async def test_execute_unsafe_query_blocked(self, service, mock_db_session):
        """Test that unsafe queries are blocked."""
        result = await service.execute_sql(
            "DELETE FROM users",
            mock_db_session,
        )

        assert result["success"] is False
        assert "DELETE" in result["error"]
        assert result["row_count"] == 0
        mock_db_session.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_empty_query(self, service, mock_db_session):
        """Test execution of empty query."""
        result = await service.execute_sql(
            "",
            mock_db_session,
        )

        assert result["success"] is False
        assert result["row_count"] == 0

    @pytest.mark.asyncio
    async def test_execute_query_with_error(self, service, mock_db_session):
        """Test handling of database error."""
        mock_db_session.execute.side_effect = Exception("Database error")

        result = await service.execute_sql(
            "SELECT * FROM users",
            mock_db_session,
        )

        assert result["success"] is False
        assert "Database error" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_query_timeout(self, service, mock_db_session):
        """Test query timeout handling."""
        async def slow_execute(*args, **kwargs):
            await asyncio.sleep(1)
            return MagicMock()

        mock_db_session.execute.side_effect = slow_execute

        result = await service.execute_sql(
            "SELECT * FROM users",
            mock_db_session,
            timeout=0.01,  # Very short timeout
        )

        assert result["success"] is False
        assert "timeout" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_execute_query_datetime_serialization(self, service, mock_db_session):
        """Test datetime serialization in results."""
        from datetime import datetime

        mock_result = MagicMock()
        now = datetime.now()
        mock_result.fetchall.return_value = [(1, now)]
        mock_result.keys.return_value = ["id", "created_at"]
        mock_db_session.execute.return_value = mock_result

        result = await service.execute_sql(
            "SELECT * FROM users",
            mock_db_session,
        )

        assert result["success"] is True
        assert result["rows"][0]["created_at"] == now.isoformat()


class TestFormatResults:
    """Tests for result formatting."""

    @pytest.fixture
    def service(self):
        return SQLExecutorService()

    def test_format_results_within_limit(self, service):
        """Test formatting results within row limit."""
        rows = [{"id": i, "name": f"user{i}"} for i in range(10)]
        columns = ["id", "name"]

        result = service.format_results(rows, columns, max_rows=100)

        assert result["total_rows"] == 10
        assert result["displayed_rows"] == 10
        assert result["truncated"] is False
        assert len(result["rows"]) == 10

    def test_format_results_truncate(self, service):
        """Test formatting results that exceed limit."""
        rows = [{"id": i, "name": f"user{i}"} for i in range(150)]
        columns = ["id", "name"]

        result = service.format_results(rows, columns, max_rows=100)

        assert result["total_rows"] == 150
        assert result["displayed_rows"] == 100
        assert result["truncated"] is True
        assert len(result["rows"]) == 100

    def test_format_empty_results(self, service):
        """Test formatting empty results."""
        result = service.format_results([], ["id", "name"])

        assert result["total_rows"] == 0
        assert result["displayed_rows"] == 0
        assert result["truncated"] is False
        assert result["rows"] == []
