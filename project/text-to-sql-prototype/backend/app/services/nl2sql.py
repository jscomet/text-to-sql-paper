"""NL2SQL service for generating SQL from natural language."""
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncEngine

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
    api_key: Optional[str] = None,
    format_type: str = "openai",
    base_url: Optional[str] = None,
) -> str:
    """Generate SQL from natural language question.

    Args:
        question: Natural language question.
        schema_text: Database schema in text format.
        provider: LLM provider name for display/logging (e.g., 'openai', 'deepseek').
        model_config: Optional model configuration.
        dialect: SQL dialect (MySQL, PostgreSQL, SQLite).
        api_key: Optional API key for the provider.
        format_type: API format type (openai, anthropic, vllm).
        base_url: Optional custom base URL for the API.

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

        # Get LLM client based on format_type
        client = get_llm_client(
            provider=provider,
            api_key=api_key,
            format_type=format_type,
            base_url=base_url,
            model=model_config.get("model") if model_config else None,
        )

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
    api_key: Optional[str] = None,
    format_type: str = "openai",
    base_url: Optional[str] = None,
    max_retries: int = 2,
) -> str:
    """Generate SQL with retry on validation failure.

    Args:
        question: Natural language question.
        schema_text: Database schema in text format.
        provider: LLM provider name.
        model_config: Optional model configuration.
        dialect: SQL dialect.
        api_key: Optional API key for the provider.
        format_type: API format type (openai, anthropic, vllm).
        base_url: Optional custom base URL.
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
                api_key=api_key,
                format_type=format_type,
                base_url=base_url,
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


async def generate_sql_with_check_correct(
    question: str,
    schema_text: str,
    engine: AsyncEngine,
    provider: str = "openai",
    model_config: Optional[dict] = None,
    dialect: str = "MySQL",
    api_key: Optional[str] = None,
    format_type: str = "openai",
    base_url: Optional[str] = None,
    max_iterations: int = 3,
) -> Dict[str, Any]:
    """Generate SQL using Check-Correct iterative refinement.

    This function implements the Check-Correct pipeline:
    1. Generate initial SQL
    2. Check syntax and execution
    3. If error, use LLM to correct
    4. Repeat until success or max iterations

    Args:
        question: Natural language question.
        schema_text: Database schema in text format.
        engine: SQLAlchemy async engine for execution validation.
        provider: LLM provider name.
        model_config: Optional model configuration.
        dialect: SQL dialect.
        api_key: Optional API key for the provider.
        format_type: API format type.
        base_url: Optional custom base URL.
        max_iterations: Maximum correction iterations.

    Returns:
        Dictionary with final SQL, success status, and correction history.
    """
    from app.services.sql_checker import SQLChecker
    from app.services.sql_corrector import SQLCorrector

    checker = SQLChecker()
    corrector = SQLCorrector(
        provider=provider,
        model_config=model_config,
        api_key=api_key,
        format_type=format_type,
        base_url=base_url,
    )

    correction_history: List[Dict[str, Any]] = []
    current_sql = ""

    for iteration in range(1, max_iterations + 1):
        logger.debug(f"Check-Correct iteration {iteration}/{max_iterations}")

        try:
            # Generate or correct SQL
            if iteration == 1:
                # First iteration: generate initial SQL
                current_sql = await generate_sql(
                    question=question,
                    schema_text=schema_text,
                    provider=provider,
                    model_config=model_config,
                    dialect=dialect,
                    api_key=api_key,
                    format_type=format_type,
                    base_url=base_url,
                )
            else:
                # Subsequent iterations: use corrected SQL from previous iteration
                pass  # current_sql is already updated by correction

            # Check syntax
            syntax_result = await checker.check_syntax(current_sql, dialect.lower())
            if not syntax_result.is_valid:
                correction_history.append({
                    "iteration": iteration,
                    "sql": current_sql,
                    "success": False,
                    "error_type": syntax_result.error_type.value if syntax_result.error_type else "syntax_error",
                    "error_message": syntax_result.error_message,
                })

                # Try to correct
                if iteration < max_iterations:
                    correction_result = await corrector.correct_sql(
                        sql=current_sql,
                        error_message=syntax_result.error_message or "Syntax error",
                        error_type=syntax_result.error_type or "syntax_error",
                        schema_text=schema_text,
                        question=question,
                        dialect=dialect,
                        max_iterations=1,
                    )
                    if correction_result.success:
                        current_sql = correction_result.final_sql
                        continue
                    else:
                        return {
                            "success": False,
                            "sql": current_sql,
                            "iteration_count": iteration,
                            "correction_history": correction_history,
                            "error_message": f"Failed to correct SQL: {correction_result.error_message}",
                        }
                else:
                    return {
                        "success": False,
                        "sql": current_sql,
                        "iteration_count": iteration,
                        "correction_history": correction_history,
                        "error_message": syntax_result.error_message,
                    }

            # Check execution
            exec_result = await checker.check_execution(
                sql=current_sql,
                engine=engine,
                timeout=checker.timeout_seconds,
            )

            if exec_result.success:
                # Success!
                correction_history.append({
                    "iteration": iteration,
                    "sql": current_sql,
                    "success": True,
                    "execution_time_ms": exec_result.execution_time_ms,
                    "row_count": exec_result.row_count,
                })
                return {
                    "success": True,
                    "sql": current_sql,
                    "iteration_count": iteration,
                    "correction_history": correction_history,
                }
            else:
                correction_history.append({
                    "iteration": iteration,
                    "sql": current_sql,
                    "success": False,
                    "error_type": exec_result.error_type.value if exec_result.error_type else "execution_error",
                    "error_message": exec_result.error_message,
                })

                # Try to correct
                if iteration < max_iterations:
                    correction_result = await corrector.correct_sql(
                        sql=current_sql,
                        error_message=exec_result.error_message or "Execution error",
                        error_type=exec_result.error_type or "execution_error",
                        schema_text=schema_text,
                        question=question,
                        dialect=dialect,
                        max_iterations=1,
                    )
                    if correction_result.success:
                        current_sql = correction_result.final_sql
                        continue
                    else:
                        return {
                            "success": False,
                            "sql": current_sql,
                            "iteration_count": iteration,
                            "correction_history": correction_history,
                            "error_message": f"Failed to correct SQL: {correction_result.error_message}",
                        }
                else:
                    return {
                        "success": False,
                        "sql": current_sql,
                        "iteration_count": iteration,
                        "correction_history": correction_history,
                        "error_message": exec_result.error_message,
                    }

        except Exception as e:
            logger.error(f"Check-Correct iteration {iteration} failed: {e}")
            correction_history.append({
                "iteration": iteration,
                "sql": current_sql,
                "success": False,
                "error_type": "exception",
                "error_message": str(e),
            })

            if iteration >= max_iterations:
                return {
                    "success": False,
                    "sql": current_sql,
                    "iteration_count": iteration,
                    "correction_history": correction_history,
                    "error_message": str(e),
                }

    # Max iterations reached
    return {
        "success": False,
        "sql": current_sql,
        "iteration_count": max_iterations,
        "correction_history": correction_history,
        "error_message": "Max iterations reached without success",
    }


async def generate_sql_pass_at_k(
    question: str,
    schema_text: str,
    engine: AsyncEngine,
    k: int = 8,
    provider: str = "openai",
    model_config: Optional[dict] = None,
    dialect: str = "MySQL",
    api_key: Optional[str] = None,
    format_type: str = "openai",
    base_url: Optional[str] = None,
    temperature: float = 0.7,
    use_majority_vote: bool = True,
) -> Dict[str, Any]:
    """Generate SQL using Pass@K sampling with majority voting.

    This function implements the Pass@K pipeline:
    1. Generate K candidate SQLs using sampling (temperature > 0)
    2. Execute and evaluate all candidates
    3. Select best SQL using majority voting or pass@k metrics

    Args:
        question: Natural language question.
        schema_text: Database schema in text format.
        engine: SQLAlchemy async engine for execution validation.
        k: Number of candidate SQLs to generate.
        provider: LLM provider name.
        model_config: Optional model configuration.
        dialect: SQL dialect.
        api_key: Optional API key for the provider.
        format_type: API format type.
        base_url: Optional custom base URL.
        temperature: Sampling temperature for diversity (should be > 0).
        use_majority_vote: If True, use majority voting to select best SQL.
                          If False, return the first successful SQL.

    Returns:
        Dictionary with selected SQL, metrics, and candidate details.
    """
    from app.services.pass_at_k import PassAtKEvaluator
    from app.services.sql_checker import SQLChecker

    checker = SQLChecker()
    evaluator = PassAtKEvaluator(
        checker=checker,
        max_workers=4,
        timeout_seconds=30.0,
    )

    try:
        # Run Pass@K evaluation
        result = await evaluator.run(
            question=question,
            schema_text=schema_text,
            engine=engine,
            k=k,
            provider=provider,
            model_config=model_config,
            dialect=dialect,
            api_key=api_key,
            format_type=format_type,
            base_url=base_url,
            temperature=temperature,
        )

        if not result.success:
            return {
                "success": False,
                "sql": None,
                "error_message": result.error_message or "Pass@K evaluation failed",
                "candidates": [],
                "metrics": None,
            }

        # Select best SQL based on mode
        selected_sql = None
        selection_method = ""

        if use_majority_vote and result.metrics and result.metrics.majority_vote_sql:
            # Use majority voting result
            selected_sql = result.metrics.majority_vote_sql
            selection_method = "majority_vote"
        else:
            # Find first successful candidate
            for candidate in result.candidates:
                if candidate.execution_success:
                    selected_sql = candidate.sql
                    selection_method = "first_success"
                    break

        if not selected_sql:
            # No successful candidate found
            return {
                "success": False,
                "sql": None,
                "error_message": "No successful SQL candidate found",
                "candidates": [
                    {
                        "sql": c.sql,
                        "execution_success": c.execution_success,
                        "error_type": c.error_type.value if c.error_type else None,
                        "error_message": c.error_message,
                    }
                    for c in result.candidates
                ],
                "metrics": {
                    "k": result.metrics.k if result.metrics else k,
                    "pass_at_k": result.metrics.pass_at_k if result.metrics else 0.0,
                    "correct_count": result.metrics.correct_count if result.metrics else 0,
                    "executable_count": result.metrics.executable_count if result.metrics else 0,
                } if result.metrics else None,
            }

        # Build candidate details
        candidate_details = [
            {
                "sql": c.sql,
                "execution_success": c.execution_success,
                "is_correct": c.is_correct,
                "error_type": c.error_type.value if c.error_type else None,
                "error_message": c.error_message,
                "execution_time_ms": c.execution_time_ms,
                "row_count": c.row_count,
            }
            for c in result.candidates
        ]

        return {
            "success": True,
            "sql": selected_sql,
            "selection_method": selection_method,
            "k": k,
            "metrics": {
                "pass_at_k": result.metrics.pass_at_k,
                "correct_count": result.metrics.correct_count,
                "executable_count": result.metrics.executable_count,
                "total_count": result.metrics.total_count,
                "majority_vote_count": result.metrics.majority_vote_count,
            } if result.metrics else None,
            "candidates": candidate_details,
            "execution_time_ms": result.execution_time_ms,
        }

    except Exception as e:
        logger.error(f"Pass@K generation failed: {e}")
        return {
            "success": False,
            "sql": None,
            "error_message": str(e),
            "candidates": [],
            "metrics": None,
        }
