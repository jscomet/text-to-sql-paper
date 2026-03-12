"""Phase 3 Simplified Integration Tests

Quick verification of core functionality without database dependencies.
"""
import pytest


class TestSQLSafety:
    """Test SQL execution safety features."""

    def test_ddl_blocked(self):
        """Test that DDL statements are blocked."""
        from app.services.sql_executor import SQLExecutorService

        executor = SQLExecutorService()
        unsafe_sqls = [
            "DROP TABLE users",
            "DROP TABLE IF EXISTS users",
            "ALTER TABLE users ADD COLUMN age INT",
            "CREATE TABLE test (id INT)",
            "TRUNCATE TABLE users",
        ]

        for sql in unsafe_sqls:
            is_safe, error = executor.check_sql_safety(sql)
            assert is_safe is False, f"SQL should be blocked: {sql}"

    def test_dml_blocked(self):
        """Test that DML statements are blocked."""
        from app.services.sql_executor import SQLExecutorService

        executor = SQLExecutorService()
        unsafe_sqls = [
            "INSERT INTO users VALUES (1, 'test')",
            "UPDATE users SET name = 'test'",
            "DELETE FROM users",
        ]

        for sql in unsafe_sqls:
            is_safe, error = executor.check_sql_safety(sql)
            assert is_safe is False, f"SQL should be blocked: {sql}"

    def test_safe_sql_allowed(self):
        """Test that safe SELECT statements are allowed."""
        from app.services.sql_executor import SQLExecutorService

        executor = SQLExecutorService()
        safe_sqls = [
            "SELECT * FROM users",
            "SELECT id, name FROM users WHERE age > 18",
            "SELECT COUNT(*) FROM orders",
            "SELECT u.name, o.amount FROM users u JOIN orders o ON u.id = o.user_id",
        ]

        for sql in safe_sqls:
            is_safe, error = executor.check_sql_safety(sql)
            assert is_safe is True, f"SQL should be allowed: {sql}"


class TestSQLGeneration:
    """Test SQL generation functionality."""

    def test_extract_sql_from_response(self):
        """Test extracting SQL from LLM responses."""
        from app.services import nl2sql as nl2sql_service

        test_cases = [
            ("```sql\nSELECT * FROM users\n```", "SELECT * FROM users"),
            ("```\nSELECT * FROM users\n```", "SELECT * FROM users"),
            ("SELECT * FROM users", "SELECT * FROM users"),
        ]

        for response, expected in test_cases:
            result = nl2sql_service.extract_sql_from_response(response)
            assert result.strip() == expected, f"Failed for: {response}"

    def test_validate_sql_syntax(self):
        """Test SQL syntax validation."""
        from app.services import nl2sql as nl2sql_service

        valid_sqls = [
            "SELECT * FROM users",
            "SELECT id, name FROM users WHERE age > 18",
        ]

        for sql in valid_sqls:
            is_valid = nl2sql_service.validate_sql_syntax(sql)
            assert is_valid is True, f"Should be valid: {sql}"

    def test_build_prompt(self):
        """Test building NL2SQL prompts."""
        from app.services.prompts import build_nl2sql_prompt

        schema_text = "CREATE TABLE users (id INT, name TEXT)"
        question = "查询所有用户"

        prompt = build_nl2sql_prompt(question, schema_text)

        assert schema_text in prompt
        assert question in prompt


class TestConnectionService:
    """Test connection service functionality."""

    def test_build_connection_url_sqlite(self):
        """Test building SQLite connection URL."""
        from app.services.connection import ConnectionService

        url = ConnectionService._build_connection_url(
            db_type="sqlite",
            host=None,
            port=None,
            database="test.db",
            username=None,
            password=None,
        )
        assert "sqlite+aiosqlite:///" in url
        assert "test.db" in url

    def test_build_connection_url_postgresql(self):
        """Test building PostgreSQL connection URL."""
        from app.services.connection import ConnectionService

        url = ConnectionService._build_connection_url(
            db_type="postgresql",
            host="localhost",
            port=5432,
            database="testdb",
            username="user",
            password="pass",
        )
        assert "postgresql+asyncpg://" in url
        assert "user:pass@localhost:5432/testdb" in url

    def test_build_connection_url_mysql(self):
        """Test building MySQL connection URL."""
        from app.services.connection import ConnectionService

        url = ConnectionService._build_connection_url(
            db_type="mysql",
            host="localhost",
            port=3306,
            database="testdb",
            username="user",
            password="pass",
        )
        assert "mysql+aiomysql://" in url
        assert "user:pass@localhost:3306/testdb" in url


class TestAPIEndpoints:
    """Test API endpoint registration."""

    def test_api_endpoints_exist(self):
        """Test that all expected API endpoints are registered."""
        from app.main import app

        routes = [route.path for route in app.routes if hasattr(route, "path")]

        expected_endpoints = [
            "/api/v1/connections",
            "/api/v1/queries/generate",
            "/api/v1/queries/execute",
            "/api/v1/queries/run",
            "/api/v1/eval/tasks",
            "/api/v1/keys",
        ]

        for endpoint in expected_endpoints:
            matching = [r for r in routes if r.startswith(endpoint)]
            assert len(matching) > 0, f"Missing endpoint: {endpoint}"


class TestSchemaService:
    """Test schema service functionality."""

    def test_build_schema_text(self):
        """Test building CREATE TABLE statements from schemas."""
        from app.schemas.connection import ColumnSchema, TableSchema
        from app.services.schema import SchemaService

        tables = [
            TableSchema(
                name="users",
                columns=[
                    ColumnSchema(name="id", type="INTEGER", nullable=False),
                    ColumnSchema(name="name", type="TEXT", nullable=True),
                ],
                primary_keys=["id"],
            )
        ]

        schema_text = SchemaService.build_schema_text(tables)

        assert "CREATE TABLE users" in schema_text
        assert "id INTEGER NOT NULL" in schema_text
        assert "PRIMARY KEY (id)" in schema_text


class TestEvaluatorService:
    """Test evaluator service functionality."""

    def test_error_type_detection(self):
        """Test error type detection."""
        from app.services.evaluator import determine_error_type

        # Test syntax error detection
        assert determine_error_type(False, None, "syntax error near SELECT") == "syntax_error"
        # Test timeout detection
        assert determine_error_type(False, None, "Query timed out") == "timeout"
        # Test execution error
        assert determine_error_type(False, None, "Database connection failed") == "execution_error"
        # Test correct result
        assert determine_error_type(True, True, None) is None
        # Test wrong result
        assert determine_error_type(True, False, None) == "wrong_result"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
