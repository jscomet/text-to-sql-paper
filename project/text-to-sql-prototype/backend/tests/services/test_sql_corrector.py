"""Tests for SQL corrector service."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.sql_corrector import (
    SQLCorrector,
    CorrectionResult,
    CorrectionAttempt,
)
from app.services.sql_checker import ErrorType


class TestSQLCorrectorPromptBuilding:
    """Tests for correction prompt building."""

    @pytest.fixture
    def corrector(self):
        """Create a SQLCorrector instance."""
        return SQLCorrector(
            provider="openai",
            api_key="test-key",
        )

    def test_build_prompt_basic(self, corrector):
        """Test basic prompt building."""
        prompt = corrector.build_correction_prompt(
            sql="SELECT * FORM users",
            error_message="syntax error near 'FORM'",
            error_type=ErrorType.SYNTAX_ERROR,
            dialect="MySQL",
        )

        assert "SQL Dialect" in prompt
        assert "MySQL" in prompt
        assert "SELECT * FORM users" in prompt
        assert "syntax_error" in prompt
        assert "syntax error near 'FORM'" in prompt

    def test_build_prompt_with_schema(self, corrector):
        """Test prompt building with schema."""
        schema = "Table: users\n- id (INT)\n- name (VARCHAR)"
        prompt = corrector.build_correction_prompt(
            sql="SELECT * FROM users",
            error_message="Table not found",
            error_type=ErrorType.TABLE_NOT_FOUND,
            schema_text=schema,
            dialect="MySQL",
        )

        assert "Database Schema" in prompt
        assert "Table: users" in prompt

    def test_build_prompt_with_question(self, corrector):
        """Test prompt building with original question."""
        prompt = corrector.build_correction_prompt(
            sql="SELECT * FROM users",
            error_message="Column not found",
            error_type=ErrorType.COLUMN_NOT_FOUND,
            question="Get all users",
            dialect="MySQL",
        )

        assert "Original Question" in prompt
        assert "Get all users" in prompt

    def test_build_prompt_syntax_error_guidance(self, corrector):
        """Test prompt includes syntax error guidance."""
        prompt = corrector.build_correction_prompt(
            sql="SELECT * FORM users",
            error_message="syntax error",
            error_type=ErrorType.SYNTAX_ERROR,
            dialect="MySQL",
        )

        assert "Correction Guidance" in prompt
        assert "parentheses" in prompt.lower()
        assert "quotes" in prompt.lower()

    def test_build_prompt_table_not_found_guidance(self, corrector):
        """Test prompt includes table not found guidance."""
        prompt = corrector.build_correction_prompt(
            sql="SELECT * FROM usres",
            error_message="table not found",
            error_type=ErrorType.TABLE_NOT_FOUND,
            dialect="MySQL",
        )

        assert "Correction Guidance" in prompt
        assert "table names" in prompt.lower() or "schema" in prompt.lower()

    def test_build_prompt_with_history(self, corrector):
        """Test prompt building with correction history."""
        history = [
            CorrectionAttempt(
                iteration=1,
                original_sql="SELECT * FORM users",
                corrected_sql="SELECT * FROM users",
                error_type=ErrorType.SYNTAX_ERROR,
                error_message="syntax error",
                success=True,
            )
        ]

        prompt = corrector.build_correction_prompt(
            sql="SELECT * FORM users",
            error_message="syntax error",
            error_type=ErrorType.SYNTAX_ERROR,
            dialect="MySQL",
            correction_history=history,
        )

        assert "Previous Correction Attempts" in prompt
        assert "Attempt 1" in prompt


class TestSQLCorrectorResponseParsing:
    """Tests for correction response parsing."""

    @pytest.fixture
    def corrector(self):
        """Create a SQLCorrector instance."""
        return SQLCorrector()

    def test_parse_markdown_code_block(self, corrector):
        """Test parsing SQL from markdown code block."""
        response = """
        Here's the corrected SQL:

        ```sql
        SELECT * FROM users WHERE id = 1
        ```

        This should work now.
        """
        result = corrector.parse_correction_response(response)
        assert result == "SELECT * FROM users WHERE id = 1"

    def test_parse_code_block_without_tag(self, corrector):
        """Test parsing SQL from code block without sql tag."""
        response = """
        ```
        SELECT COUNT(*) FROM orders
        ```
        """
        result = corrector.parse_correction_response(response)
        assert result == "SELECT COUNT(*) FROM orders"

    def test_parse_plain_sql(self, corrector):
        """Test parsing plain SQL response."""
        response = "SELECT * FROM users"
        result = corrector.parse_correction_response(response)
        assert result == "SELECT * FROM users"

    def test_parse_with_sql_prefix(self, corrector):
        """Test parsing SQL with 'SQL:' prefix."""
        response = "SQL: SELECT * FROM users"
        result = corrector.parse_correction_response(response)
        assert result == "SELECT * FROM users"

    def test_parse_with_corrected_sql_prefix(self, corrector):
        """Test parsing SQL with 'Corrected SQL:' prefix."""
        response = "Corrected SQL: SELECT * FROM users"
        result = corrector.parse_correction_response(response)
        assert result == "SELECT * FROM users"

    def test_parse_empty_response(self, corrector):
        """Test parsing empty response."""
        result = corrector.parse_correction_response("")
        assert result is None

    def test_parse_none_response(self, corrector):
        """Test parsing None response."""
        result = corrector.parse_correction_response(None)
        assert result is None

    def test_parse_removes_comments(self, corrector):
        """Test that SQL comments are removed."""
        response = """
        ```sql
        -- This is a comment
        SELECT * FROM users
        ```
        """
        result = corrector.parse_correction_response(response)
        assert "--" not in result
        assert "SELECT * FROM users" in result


class TestSQLCorrectorCorrectSQL:
    """Tests for SQL correction functionality."""

    @pytest.fixture
    def corrector(self):
        """Create a SQLCorrector instance."""
        return SQLCorrector(
            provider="openai",
            api_key="test-key",
        )

    @pytest.mark.asyncio
    async def test_correct_sql_success(self, corrector):
        """Test successful SQL correction."""
        mock_response = """
        ```sql
        SELECT * FROM users WHERE id = 1
        ```
        """

        with patch("app.services.sql_corrector.get_llm_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.generate = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            result = await corrector.correct_sql(
                sql="SELECT * FORM users",
                error_message="syntax error near 'FORM'",
                error_type=ErrorType.SYNTAX_ERROR,
                dialect="MySQL",
                max_iterations=3,
            )

            assert result.success is True
            assert result.final_sql == "SELECT * FROM users WHERE id = 1"
            assert len(result.attempts) == 1
            assert result.iterations == 1

    @pytest.mark.asyncio
    async def test_correct_sql_parse_failure(self, corrector):
        """Test correction when parsing fails."""
        mock_response = "No SQL found in this response"

        with patch("app.services.sql_corrector.get_llm_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.generate = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            result = await corrector.correct_sql(
                sql="SELECT * FORM users",
                error_message="syntax error",
                error_type=ErrorType.SYNTAX_ERROR,
                dialect="MySQL",
                max_iterations=3,
            )

            assert result.success is False
            assert result.error_message is not None

    @pytest.mark.asyncio
    async def test_correct_sql_llm_error(self, corrector):
        """Test correction when LLM raises error."""
        with patch("app.services.sql_corrector.get_llm_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.generate = AsyncMock(side_effect=Exception("LLM API error"))
            mock_get_client.return_value = mock_client

            result = await corrector.correct_sql(
                sql="SELECT * FORM users",
                error_message="syntax error",
                error_type=ErrorType.SYNTAX_ERROR,
                dialect="MySQL",
                max_iterations=3,
            )

            assert result.success is False
            assert "LLM API error" in result.error_message or result.attempts[0].error_message

    @pytest.mark.asyncio
    async def test_correct_sql_with_schema_and_question(self, corrector):
        """Test correction with schema and question context."""
        mock_response = """
        ```sql
        SELECT u.name, o.total FROM users u JOIN orders o ON u.id = o.user_id
        ```
        """

        with patch("app.services.sql_corrector.get_llm_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.generate = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            result = await corrector.correct_sql(
                sql="SELECT * FROM usres",
                error_message="table not found",
                error_type=ErrorType.TABLE_NOT_FOUND,
                schema_text="Table: users\n- id\n- name",
                question="Get user names with their order totals",
                dialect="MySQL",
                max_iterations=3,
            )

            assert result.success is True
            # Verify the prompt included schema and question
            call_args = mock_client.generate.call_args
            prompt = call_args[0][0]
            assert "Database Schema" in prompt
            assert "Original Question" in prompt


class TestSQLCorrectorWithFeedback:
    """Tests for correction with execution feedback loop."""

    @pytest.fixture
    def corrector(self):
        """Create a SQLCorrector instance."""
        return SQLCorrector(
            provider="openai",
            api_key="test-key",
        )

    @pytest.fixture
    def mock_checker(self):
        """Create a mock SQLChecker."""
        from app.services.sql_checker import SQLChecker, SyntaxCheckResult, ExecutionCheckResult

        checker = MagicMock(spec=SQLChecker)
        checker.check_syntax = AsyncMock(return_value=SyntaxCheckResult(is_valid=True))
        checker.check_execution = AsyncMock(
            return_value=ExecutionCheckResult(success=True, row_count=5)
        )
        return checker

    @pytest.fixture
    def mock_engine(self):
        """Create a mock database engine."""
        engine = MagicMock()
        engine.url = "sqlite+aiosqlite:///:memory:"
        return engine

    @pytest.mark.asyncio
    async def test_correct_with_feedback_success(self, corrector, mock_checker, mock_engine):
        """Test correction with feedback - success on first try."""
        mock_response = """
        ```sql
        SELECT * FROM users WHERE id = 1
        ```
        """

        with patch("app.services.sql_corrector.get_llm_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.generate = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            result = await corrector.correct_with_feedback(
                sql="SELECT * FORM users",
                checker=mock_checker,
                engine=mock_engine,
                dialect="MySQL",
                max_iterations=3,
            )

            assert result.success is True
            assert result.final_sql == "SELECT * FROM users WHERE id = 1"

    @pytest.mark.asyncio
    async def test_correct_with_feedback_syntax_error_then_success(
        self, corrector, mock_checker, mock_engine
    ):
        """Test correction with feedback - syntax error then success."""
        from app.services.sql_checker import SyntaxCheckResult, ErrorType

        # First syntax check fails, second succeeds
        mock_checker.check_syntax.side_effect = [
            SyntaxCheckResult(
                is_valid=False,
                error_type=ErrorType.SYNTAX_ERROR,
                error_message="syntax error",
            ),
            SyntaxCheckResult(is_valid=True),
        ]

        mock_response = """
        ```sql
        SELECT * FROM users
        ```
        """

        with patch("app.services.sql_corrector.get_llm_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.generate = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            result = await corrector.correct_with_feedback(
                sql="SELECT * FORM users",
                checker=mock_checker,
                engine=mock_engine,
                dialect="MySQL",
                max_iterations=3,
            )

            assert result.success is True
            assert len(result.attempts) >= 1

    @pytest.mark.asyncio
    async def test_correct_with_feedback_max_iterations(
        self, corrector, mock_checker, mock_engine
    ):
        """Test correction with feedback - max iterations reached."""
        from app.services.sql_checker import SyntaxCheckResult, ErrorType

        # Syntax check always fails
        mock_checker.check_syntax.return_value = SyntaxCheckResult(
            is_valid=False,
            error_type=ErrorType.SYNTAX_ERROR,
            error_message="syntax error",
        )

        mock_response = """
        ```sql
        SELECT * FORM users
        ```
        """

        with patch("app.services.sql_corrector.get_llm_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.generate = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            result = await corrector.correct_with_feedback(
                sql="SELECT * FORM users",
                checker=mock_checker,
                engine=mock_engine,
                dialect="MySQL",
                max_iterations=2,
            )

            assert result.success is False
            assert result.iterations <= 2

    @pytest.mark.asyncio
    async def test_correct_with_feedback_invalid_checker(self, corrector, mock_engine):
        """Test correction with invalid checker type."""
        invalid_checker = MagicMock()  # Not a SQLChecker

        with pytest.raises(ValueError, match="checker must be an instance of SQLChecker"):
            await corrector.correct_with_feedback(
                sql="SELECT * FROM users",
                checker=invalid_checker,
                engine=mock_engine,
                dialect="MySQL",
            )


class TestCorrectionResult:
    """Tests for CorrectionResult dataclass."""

    def test_correction_result_defaults(self):
        """Test CorrectionResult default values."""
        result = CorrectionResult(
            success=True,
            final_sql="SELECT * FROM users",
        )

        assert result.success is True
        assert result.final_sql == "SELECT * FROM users"
        assert result.attempts == []
        assert result.iterations == 0
        assert result.error_message is None

    def test_correction_result_with_attempts(self):
        """Test CorrectionResult with attempts."""
        attempts = [
            CorrectionAttempt(
                iteration=1,
                original_sql="SELECT * FORM users",
                corrected_sql="SELECT * FROM users",
                error_type=ErrorType.SYNTAX_ERROR,
                error_message="syntax error",
                success=True,
            )
        ]

        result = CorrectionResult(
            success=True,
            final_sql="SELECT * FROM users",
            attempts=attempts,
            iterations=1,
        )

        assert len(result.attempts) == 1
        assert result.iterations == 1


class TestCorrectionAttempt:
    """Tests for CorrectionAttempt dataclass."""

    def test_correction_attempt_creation(self):
        """Test CorrectionAttempt creation."""
        attempt = CorrectionAttempt(
            iteration=1,
            original_sql="SELECT * FORM users",
            corrected_sql="SELECT * FROM users",
            error_type=ErrorType.SYNTAX_ERROR,
            error_message="syntax error near 'FORM'",
            success=True,
        )

        assert attempt.iteration == 1
        assert attempt.original_sql == "SELECT * FORM users"
        assert attempt.corrected_sql == "SELECT * FROM users"
        assert attempt.error_type == ErrorType.SYNTAX_ERROR
        assert attempt.error_message == "syntax error near 'FORM'"
        assert attempt.success is True

    def test_correction_attempt_defaults(self):
        """Test CorrectionAttempt default values."""
        attempt = CorrectionAttempt(
            iteration=1,
            original_sql="SELECT * FROM users",
            corrected_sql="SELECT * FROM users",
        )

        assert attempt.error_type is None
        assert attempt.error_message is None
        assert attempt.success is False
