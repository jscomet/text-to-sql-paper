"""NL2SQL service for generating SQL from natural language."""
from typing import Optional

from app.core.logging import get_logger
from app.services.llm import get_llm_client
from app.services.prompts import build_nl2sql_prompt

logger = get_logger(__name__)


class NL2SQLError(Exception):
    """Base exception for NL2SQL errors."""
    pass


class SQLGenerationError(NL2SQLError):
    """Error during SQL generation."""
    pass


class SQLExtractionError(NL2SQLError):
    """Error extracting SQL from LLM response."""
    pass


async def generate_sql(
    question: str,
    schema_text: str,
    provider: str = "openai",
    model_config: Optional[dict] = None,
    dialect: str = "MySQL",
) -> str:
    """Generate SQL from natural language question.

    Args:
        question: Natural language question.
        schema_text: Database schema in text format.
        provider: LLM provider ('openai' or 'dashscope').
        model_config: Optional model configuration.
        dialect: SQL dialect (MySQL, PostgreSQL, SQLite).

    Returns:
        Generated SQL query.

    Raises:
        SQLGenerationError: If SQL generation fails.
    """
    try:
        # Build prompt
        prompt = build_nl2sql_prompt(
            question=question,
            schema=schema_text,
            dialect=dialect,
        )

        # Get LLM client
        client = get_llm_client(provider)

        # Generate SQL
        logger.debug(f"Generating SQL for question: {question}")
        response = await client.generate(prompt, model_config)

        # Extract SQL from response
        sql = extract_sql_from_response(response)

        if not sql:
            raise SQLExtractionError("Could not extract SQL from LLM response")

        logger.debug(f"Generated SQL: {sql}")
        return sql

    except Exception as e:
        logger.error(f"SQL generation error: {e}")
        raise SQLGenerationError(f"Failed to generate SQL: {e}") from e


def extract_sql_from_response(response: str) -> str:
    """Extract SQL query from LLM response.

    Args:
        response: Raw LLM response.

    Returns:
        Extracted SQL query.
    """
    import re

    if not response:
        return ""

    sql = response.strip()

    # Try to extract SQL from markdown code blocks
    # Pattern matches ```sql ... ``` or ``` ... ```
    code_block_pattern = r"```(?:sql|SQL)?\s*\n?(.*?)```"
    matches = re.findall(code_block_pattern, sql, re.DOTALL)

    if matches:
        # Use the first code block found
        sql = matches[0].strip()
    else:
        # No code block found, process as plain text
        # Remove "SQL Query:" prefix if present
        if sql.upper().startswith("SQL QUERY:"):
            sql = sql[10:].strip()
        # Remove "SQL:" prefix if present
        elif sql.upper().startswith("SQL:"):
            sql = sql[4:].strip()

    return sql.strip()


def validate_sql_syntax(sql: str) -> bool:
    """Perform basic SQL syntax validation.

    Args:
        sql: SQL query to validate.

    Returns:
        True if syntax appears valid, False otherwise.
    """
    if not sql or not sql.strip():
        return False

    sql_upper = sql.upper().strip()

    # Check for basic SQL structure
    # Must start with a valid SQL keyword
    valid_starts = [
        "SELECT", "INSERT", "UPDATE", "DELETE",
        "WITH", "EXPLAIN", "SHOW", "DESCRIBE",
    ]

    has_valid_start = any(sql_upper.startswith(kw) for kw in valid_starts)

    if not has_valid_start:
        return False

    # Basic bracket/parenthesis matching
    open_parens = sql.count("(")
    close_parens = sql.count(")")
    if open_parens != close_parens:
        return False

    # Check for unclosed quotes (basic check)
    single_quotes = sql.count("'") - sql.count("\\'")
    double_quotes = sql.count('"') - sql.count('\\"')

    if single_quotes % 2 != 0:
        return False
    if double_quotes % 2 != 0:
        return False

    return True


def get_sql_dialect(db_type: str) -> str:
    """Get SQL dialect name from database type.

    Args:
        db_type: Database type (mysql, postgresql, sqlite).

    Returns:
        SQL dialect name.
    """
    dialect_map = {
        "mysql": "MySQL",
        "postgresql": "PostgreSQL",
        "sqlite": "SQLite",
    }
    return dialect_map.get(db_type.lower(), "MySQL")


async def generate_sql_with_retry(
    question: str,
    schema_text: str,
    provider: str = "openai",
    model_config: Optional[dict] = None,
    dialect: str = "MySQL",
    max_retries: int = 2,
) -> str:
    """Generate SQL with retry on validation failure.

    Args:
        question: Natural language question.
        schema_text: Database schema in text format.
        provider: LLM provider.
        model_config: Optional model configuration.
        dialect: SQL dialect.
        max_retries: Maximum number of retries.

    Returns:
        Generated SQL query.

    Raises:
        SQLGenerationError: If all retries fail.
    """
    last_error = None

    for attempt in range(max_retries + 1):
        try:
            sql = await generate_sql(
                question=question,
                schema_text=schema_text,
                provider=provider,
                model_config=model_config,
                dialect=dialect,
            )

            # Validate syntax
            if validate_sql_syntax(sql):
                return sql

            # If invalid, retry
            logger.warning(f"Generated SQL failed validation, attempt {attempt + 1}")

        except Exception as e:
            last_error = e
            logger.warning(f"SQL generation failed, attempt {attempt + 1}: {e}")

    # All retries failed
    if last_error:
        raise SQLGenerationError(f"Failed to generate valid SQL after {max_retries + 1} attempts") from last_error

    raise SQLGenerationError("Failed to generate valid SQL")
