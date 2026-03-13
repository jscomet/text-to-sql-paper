"""SQL correction service for fixing SQL errors using LLM."""
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.core.logging import get_logger
from app.services.llm import get_llm_client
from app.services.sql_checker import ErrorType

logger = get_logger(__name__)


@dataclass
class CorrectionAttempt:
    """Record of a single correction attempt."""

    iteration: int
    original_sql: str
    corrected_sql: str
    error_type: Optional[ErrorType] = None
    error_message: Optional[str] = None
    success: bool = False


@dataclass
class CorrectionResult:
    """Result of SQL correction process."""

    success: bool
    final_sql: str
    attempts: List[CorrectionAttempt] = field(default_factory=list)
    iterations: int = 0
    error_message: Optional[str] = None


class SQLCorrector:
    """SQL corrector for fixing SQL errors using LLM.

    This class provides methods to:
    - Build correction prompts based on error types
    - Parse LLM correction responses
    - Iteratively correct SQL errors
    """

    def __init__(
        self,
        provider: str = "openai",
        model_config: Optional[Dict[str, Any]] = None,
        api_key: Optional[str] = None,
        format_type: str = "openai",
        base_url: Optional[str] = None,
    ):
        """Initialize SQL corrector.

        Args:
            provider: LLM provider name.
            model_config: Model configuration dictionary.
            api_key: API key for the provider.
            format_type: API format type (openai, anthropic, vllm).
            base_url: Optional custom base URL.
        """
        self.provider = provider
        self.model_config = model_config or {}
        self.api_key = api_key
        self.format_type = format_type
        self.base_url = base_url

    def build_correction_prompt(
        self,
        sql: str,
        error_message: str,
        error_type: ErrorType,
        schema_text: Optional[str] = None,
        question: Optional[str] = None,
        dialect: str = "MySQL",
        correction_history: Optional[List[CorrectionAttempt]] = None,
    ) -> str:
        """Build correction prompt based on error type.

        Args:
            sql: Original SQL with errors.
            error_message: Error message from execution.
            error_type: Classified error type.
            schema_text: Database schema information.
            question: Original natural language question.
            dialect: SQL dialect.
            correction_history: Previous correction attempts.

        Returns:
            Formatted correction prompt.
        """
        # Base prompt components
        prompt_parts = [
            f"You are an expert SQL debugger. Fix the following SQL query that has errors.",
            "",
            f"**SQL Dialect**: {dialect}",
        ]

        # Add schema if available
        if schema_text:
            prompt_parts.extend([
                "",
                "**Database Schema**:",
                "```",
                schema_text,
                "```",
            ])

        # Add original question if available
        if question:
            prompt_parts.extend([
                "",
                f"**Original Question**: {question}",
            ])

        # Add the problematic SQL
        prompt_parts.extend([
            "",
            "**SQL with Errors**:",
            "```sql",
            sql,
            "```",
        ])

        # Add error information with specific guidance based on error type
        prompt_parts.extend([
            "",
            f"**Error Type**: {error_type.value}",
            f"**Error Message**: {error_message}",
        ])

        # Add error-specific guidance
        guidance = self._get_error_guidance(error_type, sql)
        if guidance:
            prompt_parts.extend([
                "",
                "**Correction Guidance**:",
                guidance,
            ])

        # Add correction history if available
        if correction_history:
            prompt_parts.extend([
                "",
                "**Previous Correction Attempts**:",
            ])
            for attempt in correction_history[-3:]:  # Show last 3 attempts
                prompt_parts.extend([
                    f"\nAttempt {attempt.iteration}:",
                    f"- Error: {attempt.error_message}",
                    f"- Tried: {attempt.corrected_sql[:100]}...",
                ])

        # Add output format instructions
        prompt_parts.extend([
            "",
            "**Instructions**:",
            "1. Analyze the error carefully",
            "2. Fix the SQL query to resolve the error",
            "3. Ensure the corrected SQL is syntactically correct",
            "4. Maintain the original query's intent",
            "5. Output ONLY the corrected SQL in a code block",
            "",
            "**Output Format**:",
            "```sql",
            "-- Your corrected SQL here",
            "```",
        ])

        return "\n".join(prompt_parts)

    def _get_error_guidance(self, error_type: ErrorType, sql: str) -> str:
        """Get specific guidance for error type.

        Args:
            error_type: Type of error.
            sql: The SQL query.

        Returns:
            Guidance string for the error type.
        """
        guidance_map = {
            ErrorType.SYNTAX_ERROR: (
                "- Check for missing or extra parentheses, quotes, or commas\n"
                "- Verify SQL keywords are spelled correctly\n"
                "- Ensure proper clause ordering (SELECT, FROM, WHERE, etc.)\n"
                "- Check for unclosed string literals"
            ),
            ErrorType.TABLE_NOT_FOUND: (
                "- Verify table names are spelled correctly\n"
                "- Check if table exists in the schema\n"
                "- Ensure proper schema/database prefix if needed\n"
                "- Check for case sensitivity issues"
            ),
            ErrorType.COLUMN_NOT_FOUND: (
                "- Verify column names are spelled correctly\n"
                "- Check if column exists in the referenced table\n"
                "- Ensure table aliases match the FROM clause\n"
                "- Check for proper table-column qualification (table.column)"
            ),
            ErrorType.PERMISSION_ERROR: (
                "- The query may require elevated permissions\n"
                "- Consider using SELECT with appropriate table permissions\n"
                "- Avoid DDL operations (CREATE, DROP, ALTER) if not authorized"
            ),
            ErrorType.TIMEOUT: (
                "- Optimize the query for better performance\n"
                "- Add appropriate WHERE clauses to limit results\n"
                "- Consider adding indexes or query hints\n"
                "- Break complex queries into simpler parts"
            ),
            ErrorType.WRONG_RESULT: (
                "- Verify the query logic matches the intended question\n"
                "- Check JOIN conditions and types (INNER, LEFT, etc.)\n"
                "- Review WHERE clause conditions\n"
                "- Ensure aggregation functions (COUNT, SUM, etc.) are used correctly"
            ),
            ErrorType.EXECUTION_ERROR: (
                "- Check for data type mismatches\n"
                "- Verify function usage and arguments\n"
                "- Ensure subqueries return expected results\n"
                "- Check for division by zero or other runtime errors"
            ),
        }

        return guidance_map.get(error_type, "- Review the SQL carefully and fix any issues")

    def parse_correction_response(self, response: str) -> Optional[str]:
        """Parse corrected SQL from LLM response.

        Args:
            response: Raw LLM response.

        Returns:
            Extracted SQL query or None if extraction fails.
        """
        if not response:
            return None

        response = response.strip()

        # Try to extract SQL from markdown code blocks
        # Pattern matches ```sql ... ``` or ``` ... ```
        code_block_pattern = r"```(?:sql|SQL)?\s*\n?(.*?)```"
        matches = re.findall(code_block_pattern, response, re.DOTALL)

        if matches:
            # Use the first code block found
            sql = matches[0].strip()
        else:
            # No code block found, process as plain text
            sql = response

            # Remove common prefixes
            prefixes_to_remove = [
                "SQL Query:",
                "SQL:",
                "Corrected SQL:",
                "Fixed SQL:",
                "Answer:",
            ]

            for prefix in prefixes_to_remove:
                if sql.upper().startswith(prefix.upper()):
                    sql = sql[len(prefix):].strip()

        # Clean up the SQL
        sql = sql.strip()

        # Remove SQL comments at the beginning
        sql = re.sub(r"^\s*--.*?\n", "", sql, flags=re.MULTILINE)
        sql = re.sub(r"^\s*/\*.*?\*/", "", sql, flags=re.DOTALL)

        return sql.strip() if sql else None

    async def correct_sql(
        self,
        sql: str,
        error_message: str,
        error_type: ErrorType,
        schema_text: Optional[str] = None,
        question: Optional[str] = None,
        dialect: str = "MySQL",
        max_iterations: int = 3,
    ) -> CorrectionResult:
        """Correct SQL error using LLM.

        Args:
            sql: Original SQL with errors.
            error_message: Error message from execution.
            error_type: Classified error type.
            schema_text: Database schema information.
            question: Original natural language question.
            dialect: SQL dialect.
            max_iterations: Maximum correction iterations.

        Returns:
            CorrectionResult with correction details.
        """
        attempts: List[CorrectionAttempt] = []
        current_sql = sql

        for iteration in range(1, max_iterations + 1):
            logger.debug(f"Correction attempt {iteration}/{max_iterations}")

            # Build correction prompt
            prompt = self.build_correction_prompt(
                sql=current_sql,
                error_message=error_message,
                error_type=error_type,
                schema_text=schema_text,
                question=question,
                dialect=dialect,
                correction_history=attempts,
            )

            try:
                # Get LLM client
                client = get_llm_client(
                    provider=self.provider,
                    api_key=self.api_key,
                    format_type=self.format_type,
                    base_url=self.base_url,
                    model=self.model_config.get("model") if self.model_config else None,
                )

                # Generate correction
                response = await client.generate(prompt, self.model_config)

                # Parse corrected SQL
                corrected_sql = self.parse_correction_response(response)

                if not corrected_sql:
                    logger.warning(f"Failed to extract SQL from correction response")
                    attempts.append(CorrectionAttempt(
                        iteration=iteration,
                        original_sql=current_sql,
                        corrected_sql="",
                        error_type=error_type,
                        error_message="Failed to parse correction response",
                        success=False,
                    ))
                    continue

                # Record attempt
                attempt = CorrectionAttempt(
                    iteration=iteration,
                    original_sql=current_sql,
                    corrected_sql=corrected_sql,
                    error_type=error_type,
                    error_message=error_message,
                    success=True,
                )
                attempts.append(attempt)

                # Update current SQL for next iteration if needed
                current_sql = corrected_sql

                # Return successful correction
                return CorrectionResult(
                    success=True,
                    final_sql=corrected_sql,
                    attempts=attempts,
                    iterations=iteration,
                )

            except Exception as e:
                logger.error(f"Correction attempt {iteration} failed: {e}")
                attempts.append(CorrectionAttempt(
                    iteration=iteration,
                    original_sql=current_sql,
                    corrected_sql="",
                    error_type=error_type,
                    error_message=str(e),
                    success=False,
                ))

        # All iterations failed
        return CorrectionResult(
            success=False,
            final_sql=sql,
            attempts=attempts,
            iterations=len(attempts),
            error_message="Failed to correct SQL after maximum iterations",
        )

    async def correct_with_feedback(
        self,
        sql: str,
        checker: Any,  # SQLChecker instance
        engine: Any,  # AsyncEngine
        schema_text: Optional[str] = None,
        question: Optional[str] = None,
        dialect: str = "MySQL",
        max_iterations: int = 3,
    ) -> CorrectionResult:
        """Correct SQL with execution feedback loop.

        Iteratively correct SQL until it executes successfully or max iterations reached.

        Args:
            sql: Original SQL.
            checker: SQLChecker instance for validation.
            engine: Database engine for execution testing.
            schema_text: Database schema information.
            question: Original natural language question.
            dialect: SQL dialect.
            max_iterations: Maximum correction iterations.

        Returns:
            CorrectionResult with correction details.
        """
        from app.services.sql_checker import SQLChecker

        if not isinstance(checker, SQLChecker):
            raise ValueError("checker must be an instance of SQLChecker")

        attempts: List[CorrectionAttempt] = []
        current_sql = sql

        for iteration in range(1, max_iterations + 1):
            # Check syntax first
            syntax_result = await checker.check_syntax(current_sql, dialect.lower())
            if not syntax_result.is_valid:
                # Try to correct syntax error
                correction = await self.correct_sql(
                    sql=current_sql,
                    error_message=syntax_result.error_message or "Syntax error",
                    error_type=syntax_result.error_type or ErrorType.SYNTAX_ERROR,
                    schema_text=schema_text,
                    question=question,
                    dialect=dialect,
                    max_iterations=1,
                )

                if correction.success:
                    current_sql = correction.final_sql
                    attempts.extend(correction.attempts)
                else:
                    attempts.extend(correction.attempts)
                    break

                continue

            # Try execution
            exec_result = await checker.check_execution(current_sql, engine)

            if exec_result.success:
                # Success!
                return CorrectionResult(
                    success=True,
                    final_sql=current_sql,
                    attempts=attempts,
                    iterations=iteration,
                )

            # Execution failed, try to correct
            correction = await self.correct_sql(
                sql=current_sql,
                error_message=exec_result.error_message or "Execution error",
                error_type=exec_result.error_type or ErrorType.EXECUTION_ERROR,
                schema_text=schema_text,
                question=question,
                dialect=dialect,
                max_iterations=1,
            )

            if correction.success:
                current_sql = correction.final_sql
                attempts.extend(correction.attempts)
            else:
                attempts.extend(correction.attempts)
                break

        # Max iterations reached or correction failed
        return CorrectionResult(
            success=False,
            final_sql=current_sql,
            attempts=attempts,
            iterations=len(attempts),
            error_message="Failed to correct SQL after maximum iterations",
        )
