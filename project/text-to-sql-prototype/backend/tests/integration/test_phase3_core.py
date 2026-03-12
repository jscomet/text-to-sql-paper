"""Phase 3 Integration Tests - Backend Core Business Logic

This module tests the core business functionality:
- Database connection management
- Text-to-SQL generation and execution
- Evaluation system
"""
import asyncio
import json
import os
import sqlite3
import tempfile
from datetime import datetime
from typing import Any, Dict, Generator

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.main import app
from app.models.eval_task import EvalTask
from app.services.connection import ConnectionService
from app.services.evaluator import MajorityVoter, SQLEvaluator
from app.services.llm import get_llm_client
from app.services import nl2sql as nl2sql_service
from app.services.prompts import build_nl2sql_prompt
from app.services.schema import SchemaService
from app.services.sql_executor import SQLExecutorService


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def temp_sqlite_db() -> Generator[str, None, None]:
    """Create a temporary SQLite database for testing."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    # Create test tables
    conn = sqlite3.connect(path)
    cursor = conn.cursor()

    # Create users table
    cursor.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            email TEXT,
            age INTEGER,
            created_at TEXT
        )
    """)

    # Create orders table
    cursor.execute("""
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            amount REAL,
            status TEXT,
            created_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Insert test data
    cursor.executemany(
        "INSERT INTO users (id, username, email, age, created_at) VALUES (?, ?, ?, ?, ?)",
        [
            (1, "alice", "alice@example.com", 25, "2024-01-01"),
            (2, "bob", "bob@example.com", 30, "2024-01-02"),
            (3, "charlie", "charlie@example.com", 35, "2024-01-03"),
        ],
    )

    cursor.executemany(
        "INSERT INTO orders (id, user_id, amount, status, created_at) VALUES (?, ?, ?, ?, ?)",
        [
            (1, 1, 100.0, "completed", "2024-01-01"),
            (2, 1, 200.0, "pending", "2024-01-02"),
            (3, 2, 150.0, "completed", "2024-01-02"),
        ],
    )

    conn.commit()
    conn.close()

    yield path

    # Cleanup
    os.unlink(path)


@pytest.fixture
async def test_db_connection(temp_sqlite_db: str) -> Dict[str, Any]:
    """Create a test database connection configuration."""
    return {
        "name": "test-sqlite",
        "db_type": "sqlite",
        "database": temp_sqlite_db,
    }


# =============================================================================
# Test 1: Database Connection Management
# =============================================================================

class TestDatabaseConnection:
    """Test database connection management functionality."""

    @pytest.mark.asyncio
    async def test_build_connection_url(self, temp_sqlite_db: str):
        """Test building connection URLs for different database types."""
        from app.models.db_connection import DBConnection

        # Test SQLite
        sqlite_conn = DBConnection(
            db_type="sqlite",
            database=temp_sqlite_db,
        )
        url = ConnectionService._build_connection_url(
            db_type=sqlite_conn.db_type,
            host=sqlite_conn.host,
            port=sqlite_conn.port,
            database=sqlite_conn.database,
            username=sqlite_conn.username,
            password=None,
        )
        assert "sqlite+aiosqlite:///" in url
        assert temp_sqlite_db in url

        # Test PostgreSQL
        pg_url = ConnectionService._build_connection_url(
            db_type="postgresql",
            host="localhost",
            port=5432,
            database="testdb",
            username="user",
            password="pass",
        )
        assert "postgresql+asyncpg://" in pg_url
        assert "user:pass@localhost:5432/testdb" in pg_url

        # Test MySQL
        mysql_url = ConnectionService._build_connection_url(
            db_type="mysql",
            host="localhost",
            port=3306,
            database="testdb",
            username="user",
            password="pass",
        )
        assert "mysql+aiomysql://" in mysql_url
        assert "user:pass@localhost:3306/testdb" in mysql_url

    @pytest.mark.asyncio
    async def test_sqlite_connection(self, temp_sqlite_db: str):
        """Test SQLite database connection."""
        from app.models.db_connection import DBConnection

        connection = DBConnection(
            db_type="sqlite",
            database=temp_sqlite_db,
        )

        success, error = await ConnectionService.test_connection_model(connection)
        assert success is True
        assert error is None

    @pytest.mark.asyncio
    async def test_schema_extraction(self, temp_sqlite_db: str):
        """Test extracting schema from database."""
        from app.models.db_connection import DBConnection

        connection = DBConnection(
            db_type="sqlite",
            database=temp_sqlite_db,
        )

        # Create engine and extract schema
        engine = ConnectionService.create_engine(connection)

        # Test get_tables
        tables = await SchemaService.get_tables(engine)
        assert "users" in tables
        assert "orders" in tables

        # Test get_table_schema
        users_schema = await SchemaService.get_table_schema(engine, "users")
        assert users_schema.name == "users"
        assert len(users_schema.columns) == 5
        assert "id" in [col.name for col in users_schema.columns]

        # Test build_schema_text
        all_schemas = await SchemaService.get_all_schemas(engine)
        schema_text = SchemaService.build_schema_text(all_schemas)
        assert "CREATE TABLE users" in schema_text
        assert "CREATE TABLE orders" in schema_text
        assert "PRIMARY KEY" in schema_text

        await engine.dispose()

    @pytest.mark.asyncio
    async def test_foreign_key_extraction(self, temp_sqlite_db: str):
        """Test extracting foreign key relationships."""
        from app.models.db_connection import DBConnection

        connection = DBConnection(
            db_type="sqlite",
            database=temp_sqlite_db,
        )

        engine = ConnectionService.create_engine(connection)
        fks = await SchemaService.get_foreign_keys(engine)

        # orders.user_id should reference users.id
        orders_fks = [fk for fk in fks if "orders" in fk.column]
        assert len(orders_fks) > 0
        assert any(fk.referenced_table == "users" for fk in orders_fks)

        await engine.dispose()


# =============================================================================
# Test 2: SQL Safety Checks
# =============================================================================

class TestSQLSafety:
    """Test SQL execution safety features."""

    def test_ddl_blocked(self):
        """Test that DDL statements are blocked."""
        unsafe_sqls = [
            "DROP TABLE users",
            "DROP TABLE IF EXISTS users",
            "ALTER TABLE users ADD COLUMN age INT",
            "CREATE TABLE test (id INT)",
            "TRUNCATE TABLE users",
        ]

        for sql in unsafe_sqls:
            result = SQLExecutorService.check_sql_safety(sql)
            assert result["safe"] is False, f"SQL should be blocked: {sql}"
            assert "DDL operations are not allowed" in result["reason"]

    def test_dml_blocked(self):
        """Test that DML statements are blocked."""
        unsafe_sqls = [
            "INSERT INTO users VALUES (1, 'test')",
            "UPDATE users SET name = 'test'",
            "DELETE FROM users",
        ]

        for sql in unsafe_sqls:
            result = SQLExecutorService.check_sql_safety(sql)
            assert result["safe"] is False, f"SQL should be blocked: {sql}"
            assert "DML operations are not allowed" in result["reason"]

    def test_safe_sql_allowed(self):
        """Test that safe SELECT statements are allowed."""
        safe_sqls = [
            "SELECT * FROM users",
            "SELECT id, name FROM users WHERE age > 18",
            "SELECT COUNT(*) FROM orders",
            "SELECT u.name, o.amount FROM users u JOIN orders o ON u.id = o.user_id",
        ]

        for sql in safe_sqls:
            result = SQLExecutorService.check_sql_safety(sql)
            assert result["safe"] is True, f"SQL should be allowed: {sql}"

    def test_case_insensitive_blocking(self):
        """Test that SQL blocking is case-insensitive."""
        sqls = [
            "drop table users",
            "DROP TABLE users",
            "Drop Table users",
            "insert into users values (1)",
            "INSERT INTO users VALUES (1)",
        ]

        for sql in sqls:
            result = SQLExecutorService.check_sql_safety(sql)
            assert result["safe"] is False, f"SQL should be blocked: {sql}"


# =============================================================================
# Test 3: SQL Execution
# =============================================================================

class TestSQLExecution:
    """Test SQL execution functionality."""

    @pytest.mark.asyncio
    async def test_execute_safe_query(self, temp_sqlite_db: str):
        """Test executing a safe SELECT query."""
        from app.models.db_connection import DBConnection

        connection = DBConnection(
            db_type="sqlite",
            database=temp_sqlite_db,
        )

        result = await SQLExecutorService.execute_sql(
            connection=connection,
            sql="SELECT * FROM users WHERE id = 1",
        )

        assert result["success"] is True
        assert len(result["columns"]) == 5
        assert len(result["rows"]) == 1
        assert result["row_count"] == 1

    @pytest.mark.asyncio
    async def test_execute_unsafe_query_blocked(self, temp_sqlite_db: str):
        """Test that unsafe queries are blocked."""
        from app.models.db_connection import DBConnection

        connection = DBConnection(
            db_type="sqlite",
            database=temp_sqlite_db,
        )

        result = await SQLExecutorService.execute_sql(
            connection=connection,
            sql="DROP TABLE users",
        )

        assert result["success"] is False
        assert "not allowed" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_execute_syntax_error(self, temp_sqlite_db: str):
        """Test handling of SQL syntax errors."""
        from app.models.db_connection import DBConnection

        connection = DBConnection(
            db_type="sqlite",
            database=temp_sqlite_db,
        )

        result = await SQLExecutorService.execute_sql(
            connection=connection,
            sql="SELECT * FROM nonexistent_table",
        )

        assert result["success"] is False
        assert "error" in result


# =============================================================================
# Test 4: SQL Generation (Mocked)
# =============================================================================

class TestSQLGeneration:
    """Test SQL generation functionality (with mocked LLM)."""

    def test_extract_sql_from_response(self):
        """Test extracting SQL from LLM responses."""
        test_cases = [
            # Code block with sql tag
            ("```sql\nSELECT * FROM users\n```", "SELECT * FROM users"),
            # Code block without tag
            ("```\nSELECT * FROM users\n```", "SELECT * FROM users"),
            # Plain SQL
            ("SELECT * FROM users", "SELECT * FROM users"),
            # With explanation
            ("Here is the SQL:\n```sql\nSELECT * FROM users\n```", "SELECT * FROM users"),
        ]

        for response, expected in test_cases:
            result = nl2sql_service.extract_sql_from_response(response)
            assert result.strip() == expected, f"Failed for: {response}"

    def test_validate_sql_syntax(self):
        """Test SQL syntax validation."""
        valid_sqls = [
            "SELECT * FROM users",
            "SELECT id, name FROM users WHERE age > 18",
            "SELECT COUNT(*) FROM orders GROUP BY status",
        ]

        for sql in valid_sqls:
            result = nl2sql_service.validate_sql_syntax(sql)
            assert result["valid"] is True, f"Should be valid: {sql}"

        invalid_sqls = [
            "SELECT * FROM",  # incomplete
            "SELET * FROM users",  # typo
        ]

        for sql in invalid_sqls:
            result = nl2sql_service.validate_sql_syntax(sql)
            assert result["valid"] is False, f"Should be invalid: {sql}"

    def test_build_prompt(self):
        """Test building NL2SQL prompts."""
        schema_text = "CREATE TABLE users (id INT, name TEXT)"
        question = "查询所有用户"

        prompt = build_nl2sql_prompt(question, schema_text)

        assert schema_text in prompt
        assert question in prompt
        assert "SQL" in prompt


# =============================================================================
# Test 5: SQL Evaluation
# =============================================================================

class TestSQLEvaluation:
    """Test SQL evaluation functionality."""

    @pytest.mark.asyncio
    async def test_compare_sql_results(self, temp_sqlite_db: str):
        """Test comparing two SQL queries with EXCEPT."""
        from app.models.db_connection import DBConnection

        connection = DBConnection(
            db_type="sqlite",
            database=temp_sqlite_db,
        )

        # Same query should match
        is_equal = await SQLEvaluator.compare_sql_results_except(
            connection,
            "SELECT * FROM users WHERE id = 1",
            "SELECT * FROM users WHERE id = 1",
        )
        assert is_equal is True

        # Different queries should not match
        is_equal = await SQLEvaluator.compare_sql_results_except(
            connection,
            "SELECT * FROM users WHERE id = 1",
            "SELECT * FROM users WHERE id = 2",
        )
        assert is_equal is False

    @pytest.mark.asyncio
    async def test_majority_voting(self, temp_sqlite_db: str):
        """Test majority voting algorithm."""
        from app.models.db_connection import DBConnection

        connection = DBConnection(
            db_type="sqlite",
            database=temp_sqlite_db,
        )

        # Test with semantically equivalent SQLs
        sqls = [
            "SELECT * FROM users WHERE id = 1",
            "SELECT * FROM users WHERE id = 1",  # Duplicate (should win)
            "SELECT * FROM users WHERE id = 2",
        ]

        winner = await MajorityVoter.majority_voting(connection, sqls)
        assert winner == "SELECT * FROM users WHERE id = 1"


# =============================================================================
# Test 6: API Integration
# =============================================================================

@pytest.mark.asyncio
async def test_api_endpoints_exist():
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
        # Check if any route starts with the endpoint
        matching = [r for r in routes if r.startswith(endpoint)]
        assert len(matching) > 0, f"Missing endpoint: {endpoint}"


# =============================================================================
# Test 7: Service Integration
# =============================================================================

class TestServiceIntegration:
    """Test integration between services."""

    @pytest.mark.asyncio
    async def test_end_to_end_query_flow(self, temp_sqlite_db: str):
        """Test complete query flow: connection -> schema -> execution."""
        from app.models.db_connection import DBConnection

        # 1. Create connection
        connection = DBConnection(
            db_type="sqlite",
            database=temp_sqlite_db,
        )

        # 2. Extract schema
        engine = ConnectionService.create_engine(connection)
        schemas = await SchemaService.get_all_schemas(engine)
        schema_text = SchemaService.build_schema_text(schemas)

        assert "users" in schema_text
        assert "orders" in schema_text

        # 3. Execute a query
        result = await SQLExecutorService.execute_sql(
            connection=connection,
            sql="SELECT COUNT(*) as total FROM users",
        )

        assert result["success"] is True
        assert result["row_count"] == 1
        assert result["rows"][0][0] == 3  # 3 users in test data

        await engine.dispose()


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
