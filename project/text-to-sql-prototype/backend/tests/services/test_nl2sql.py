"""Tests for NL2SQL service."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.nl2sql import (
    extract_sql_from_response,
    validate_sql_syntax,
    get_sql_dialect,
    generate_sql,
    generate_sql_with_retry,
    SQLGenerationError,
    SQLExtractionError,
)


class TestExtractSQLFromResponse:
    """Tests for SQL extraction from LLM responses."""

    def test_extract_from_markdown_code_block(self):
        """Test extracting SQL from markdown code block."""
        response = """
        Here's the query:
        ```sql
        SELECT * FROM users WHERE id = 1
        ```
        """
        result = extract_sql_from_response(response)
        assert result == "SELECT * FROM users WHERE id = 1"

    def test_extract_from_code_block_without_sql_tag(self):
        """Test extracting SQL from code block without sql tag."""
        response = """
        ```
        SELECT * FROM orders
        ```
        """
        result = extract_sql_from_response(response)
        assert result == "SELECT * FROM orders"

    def test_extract_plain_sql(self):
        """Test extracting plain SQL without code block."""
        response = "SELECT * FROM users"
        result = extract_sql_from_response(response)
        assert result == "SELECT * FROM users"

    def test_extract_sql_with_prefix(self):
        """Test extracting SQL with 'SQL Query:' prefix."""
        response = "SQL Query: SELECT * FROM users"
        result = extract_sql_from_response(response)
        assert result == "SELECT * FROM users"

    def test_extract_sql_with_short_prefix(self):
        """Test extracting SQL with 'SQL:' prefix."""
        response = "SQL: SELECT * FROM users"
        result = extract_sql_from_response(response)
        assert result == "SELECT * FROM users"

    def test_extract_empty_response(self):
        """Test extracting from empty response."""
        result = extract_sql_from_response("")
        assert result == ""

    def test_extract_none_response(self):
        """Test extracting from None response."""
        result = extract_sql_from_response(None)
        assert result == ""

    def test_extract_multiple_code_blocks(self):
        """Test that first code block is used when multiple exist."""
        response = """
        ```sql
        SELECT first FROM table1
        ```
        Some text
        ```sql
        SELECT second FROM table2
        ```
        """
        result = extract_sql_from_response(response)
        assert result == "SELECT first FROM table1"


class TestValidateSQLSyntax:
    """Tests for SQL syntax validation."""

    def test_valid_select(self):
        """Test valid SELECT statement."""
        sql = "SELECT * FROM users"
        assert validate_sql_syntax(sql) is True

    def test_valid_select_with_where(self):
        """Test valid SELECT with WHERE clause."""
        sql = "SELECT * FROM users WHERE id = 1"
        assert validate_sql_syntax(sql) is True

    def test_valid_select_with_join(self):
        """Test valid SELECT with JOIN."""
        sql = "SELECT u.*, o.id FROM users u JOIN orders o ON u.id = o.user_id"
        assert validate_sql_syntax(sql) is True

    def test_valid_insert(self):
        """Test valid INSERT statement."""
        sql = "INSERT INTO users (name) VALUES ('test')"
        assert validate_sql_syntax(sql) is True

    def test_valid_update(self):
        """Test valid UPDATE statement."""
        sql = "UPDATE users SET name = 'test' WHERE id = 1"
        assert validate_sql_syntax(sql) is True

    def test_valid_delete(self):
        """Test valid DELETE statement."""
        sql = "DELETE FROM users WHERE id = 1"
        assert validate_sql_syntax(sql) is True

    def test_valid_with_clause(self):
        """Test valid WITH clause."""
        sql = "WITH cte AS (SELECT * FROM users) SELECT * FROM cte"
        assert validate_sql_syntax(sql) is True

    def test_empty_sql(self):
        """Test empty SQL."""
        assert validate_sql_syntax("") is False
        assert validate_sql_syntax("   ") is False

    def test_invalid_start_keyword(self):
        """Test SQL with invalid start keyword."""
        sql = "TRUNCATE TABLE users"
        assert validate_sql_syntax(sql) is False

    def test_mismatched_parentheses(self):
        """Test SQL with mismatched parentheses."""
        sql = "SELECT * FROM users WHERE id = (1"
        assert validate_sql_syntax(sql) is False

    def test_unclosed_single_quote(self):
        """Test SQL with unclosed single quote."""
        sql = "SELECT * FROM users WHERE name = 'test"
        assert validate_sql_syntax(sql) is False

    def test_unclosed_double_quote(self):
        """Test SQL with unclosed double quote."""
        sql = 'SELECT * FROM users WHERE name = "test'
        assert validate_sql_syntax(sql) is False

    def test_escaped_quotes(self):
        """Test SQL with escaped quotes."""
        sql = "SELECT * FROM users WHERE name = 'it\\'s'"
        assert validate_sql_syntax(sql) is True


class TestGetSQLDialect:
    """Tests for SQL dialect mapping."""

    def test_mysql_dialect(self):
        """Test MySQL dialect mapping."""
        assert get_sql_dialect("mysql") == "MySQL"
        assert get_sql_dialect("MySQL") == "MySQL"
        assert get_sql_dialect("MYSQL") == "MySQL"

    def test_postgresql_dialect(self):
        """Test PostgreSQL dialect mapping."""
        assert get_sql_dialect("postgresql") == "PostgreSQL"
        assert get_sql_dialect("PostgreSQL") == "PostgreSQL"

    def test_sqlite_dialect(self):
        """Test SQLite dialect mapping."""
        assert get_sql_dialect("sqlite") == "SQLite"
        assert get_sql_dialect("SQLite") == "SQLite"

    def test_unknown_dialect_defaults_to_mysql(self):
        """Test that unknown dialect defaults to MySQL."""
        assert get_sql_dialect("oracle") == "MySQL"
        assert get_sql_dialect("unknown") == "MySQL"


class TestGenerateSQL:
    """Tests for SQL generation with mocked LLM."""

    @pytest.mark.asyncio
    async def test_generate_sql_success(self, mock_schema_text):
        """Test successful SQL generation."""
        mock_response = "```sql\nSELECT * FROM users WHERE id = 1\n```"

        with patch("app.services.nl2sql.get_llm_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.generate = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            result = await generate_sql(
                question="Get user with id 1",
                schema_text=mock_schema_text,
                provider="openai",
            )

            assert "SELECT" in result.upper()
            mock_client.generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_sql_empty_response(self, mock_schema_text):
        """Test SQL generation with empty response."""
        with patch("app.services.nl2sql.get_llm_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.generate = AsyncMock(return_value="")
            mock_get_client.return_value = mock_client

            # Empty response causes SQLExtractionError which is wrapped in SQLGenerationError
            with pytest.raises(SQLGenerationError):
                await generate_sql(
                    question="Get all users",
                    schema_text=mock_schema_text,
                    provider="openai",
                )

    @pytest.mark.asyncio
    async def test_generate_sql_llm_error(self, mock_schema_text):
        """Test SQL generation when LLM raises error."""
        with patch("app.services.nl2sql.get_llm_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.generate = AsyncMock(side_effect=Exception("LLM API error"))
            mock_get_client.return_value = mock_client

            with pytest.raises(SQLGenerationError):
                await generate_sql(
                    question="Get all users",
                    schema_text=mock_schema_text,
                    provider="openai",
                )

    @pytest.mark.asyncio
    async def test_generate_sql_with_different_provider(self, mock_schema_text):
        """Test SQL generation with different provider."""
        mock_response = "```sql\nSELECT COUNT(*) FROM users\n```"

        with patch("app.services.nl2sql.get_llm_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.generate = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            result = await generate_sql(
                question="Count users",
                schema_text=mock_schema_text,
                provider="dashscope",
                dialect="MySQL",
            )

            assert "COUNT" in result.upper()
            mock_get_client.assert_called_once_with("dashscope")


class TestGenerateSQLWithRetry:
    """Tests for SQL generation with retry logic."""

    @pytest.mark.asyncio
    async def test_generate_sql_with_retry_success(self, mock_schema_text):
        """Test successful SQL generation with retry."""
        mock_response = "```sql\nSELECT * FROM users\n```"

        with patch("app.services.nl2sql.get_llm_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.generate = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            result = await generate_sql_with_retry(
                question="Get all users",
                schema_text=mock_schema_text,
                provider="openai",
                max_retries=2,
            )

            assert "SELECT" in result.upper()

    @pytest.mark.asyncio
    async def test_generate_sql_with_retry_eventual_success(self, mock_schema_text):
        """Test retry succeeds after initial failures."""
        responses = [
            "invalid sql without select",  # First attempt - invalid
            "```sql\nSELECT * FROM users\n```",  # Second attempt - valid
        ]

        with patch("app.services.nl2sql.get_llm_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.generate = AsyncMock(side_effect=responses)
            mock_get_client.return_value = mock_client

            result = await generate_sql_with_retry(
                question="Get all users",
                schema_text=mock_schema_text,
                provider="openai",
                max_retries=2,
            )

            assert "SELECT" in result.upper()
            assert mock_client.generate.call_count == 2

    @pytest.mark.asyncio
    async def test_generate_sql_with_retry_all_fail(self, mock_schema_text):
        """Test retry when all attempts fail."""
        with patch("app.services.nl2sql.get_llm_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.generate = AsyncMock(return_value="invalid sql")
            mock_get_client.return_value = mock_client

            with pytest.raises(SQLGenerationError):
                await generate_sql_with_retry(
                    question="Get all users",
                    schema_text=mock_schema_text,
                    provider="openai",
                    max_retries=1,
                )

            assert mock_client.generate.call_count == 2  # Initial + 1 retry
