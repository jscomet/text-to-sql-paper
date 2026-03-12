"""Tests for evaluator service."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from app.services.evaluator import (
    SQLEvaluator,
    MajorityVoter,
    determine_error_type,
)


class TestSQLEvaluatorExecuteSafely:
    """Tests for SQL execution with safety."""

    @pytest.fixture
    def mock_engine(self):
        """Create a mock async engine."""
        engine = MagicMock()
        return engine

    @pytest.mark.asyncio
    async def test_execute_sql_safely_success(self, mock_engine):
        """Test successful SQL execution."""
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_result.mappings.return_value.all.return_value = [
            {"id": 1, "name": "alice"},
            {"id": 2, "name": "bob"},
        ]
        mock_conn.execute = AsyncMock(return_value=mock_result)

        mock_context = MagicMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        mock_engine.connect.return_value = mock_context
        mock_engine.url = "sqlite:///test.db"

        success, results, error = await SQLEvaluator.execute_sql_safely(
            mock_engine, "SELECT * FROM users"
        )

        assert success is True
        assert results == [{"id": 1, "name": "alice"}, {"id": 2, "name": "bob"}]
        assert error is None

    @pytest.mark.asyncio
    async def test_execute_sql_safely_timeout(self, mock_engine):
        """Test SQL execution timeout."""
        mock_conn = MagicMock()

        async def slow_execute(*args, **kwargs):
            await asyncio.sleep(1)
            return MagicMock()

        mock_conn.execute = slow_execute

        mock_context = MagicMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        mock_engine.connect.return_value = mock_context
        mock_engine.url = "sqlite:///test.db"

        success, results, error = await SQLEvaluator.execute_sql_safely(
            mock_engine, "SELECT * FROM users", timeout=0.01
        )

        assert success is False
        assert results is None
        assert "timeout" in error.lower()

    @pytest.mark.asyncio
    async def test_execute_sql_safely_error(self, mock_engine):
        """Test SQL execution error handling."""
        mock_conn = MagicMock()
        mock_conn.execute = AsyncMock(side_effect=Exception("Syntax error"))

        mock_context = MagicMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        mock_engine.connect.return_value = mock_context
        mock_engine.url = "sqlite:///test.db"

        success, results, error = await SQLEvaluator.execute_sql_safely(
            mock_engine, "INVALID SQL"
        )

        assert success is False
        assert results is None
        assert "Syntax error" in error


class TestNormalizeResults:
    """Tests for result normalization."""

    def test_normalize_empty_results(self):
        """Test normalizing empty results."""
        result = SQLEvaluator.normalize_results([])
        assert result == []

    def test_normalize_simple_results(self):
        """Test normalizing simple results."""
        results = [
            {"id": 1, "name": "alice"},
            {"id": 2, "name": "bob"},
        ]
        normalized = SQLEvaluator.normalize_results(results)

        assert len(normalized) == 2
        assert normalized[0]["id"] == "1"
        assert normalized[0]["name"] == "alice"

    def test_normalize_with_none_values(self):
        """Test normalizing results with None values."""
        results = [
            {"id": 1, "name": None},
            {"id": 2, "name": "bob"},
        ]
        normalized = SQLEvaluator.normalize_results(results)

        assert normalized[0]["name"] == "NULL"
        assert normalized[1]["name"] == "bob"

    def test_normalize_with_float_values(self):
        """Test normalizing results with float values."""
        results = [
            {"id": 1, "value": 3.14159},
        ]
        normalized = SQLEvaluator.normalize_results(results)

        assert "3.141590" in normalized[0]["value"]

    def test_normalize_sorts_consistently(self):
        """Test that normalization sorts results consistently."""
        results = [
            {"b": 2, "a": 1},
            {"b": 1, "a": 2},
        ]
        normalized = SQLEvaluator.normalize_results(results)

        # Should be sorted by 'a' then 'b'
        assert normalized[0]["a"] == "1"
        assert normalized[1]["a"] == "2"

    def test_normalize_case_insensitive_keys(self):
        """Test that keys are lowercased."""
        results = [
            {"ID": 1, "NAME": "alice"},
        ]
        normalized = SQLEvaluator.normalize_results(results)

        assert "id" in normalized[0]
        assert "name" in normalized[0]


class TestCompareSQLResults:
    """Tests for SQL result comparison."""

    @pytest.fixture
    def mock_engine(self):
        """Create a mock async engine."""
        engine = MagicMock()
        return engine

    @pytest.mark.asyncio
    async def test_compare_identical_results(self, mock_engine):
        """Test comparing identical results."""
        results = [{"id": 1, "name": "alice"}]

        with patch.object(
            SQLEvaluator, "execute_sql_safely",
            side_effect=[
                (True, results, None),  # pred_sql result
                (True, results, None),  # gold_sql result
            ]
        ) as mock_execute:
            is_correct, error = await SQLEvaluator.compare_sql_results(
                mock_engine, "SELECT * FROM users", "SELECT * FROM users"
            )

            assert is_correct is True
            assert error is None

    @pytest.mark.asyncio
    async def test_compare_different_row_count(self, mock_engine):
        """Test comparing results with different row counts."""
        pred_results = [{"id": 1}]
        gold_results = [{"id": 1}, {"id": 2}]

        with patch.object(
            SQLEvaluator, "execute_sql_safely",
            side_effect=[
                (True, pred_results, None),
                (True, gold_results, None),
            ]
        ):
            is_correct, error = await SQLEvaluator.compare_sql_results(
                mock_engine, "SELECT * FROM pred", "SELECT * FROM gold"
            )

            assert is_correct is False
            assert "Row count mismatch" in error

    @pytest.mark.asyncio
    async def test_compare_different_content(self, mock_engine):
        """Test comparing results with different content."""
        pred_results = [{"id": 1, "name": "alice"}]
        gold_results = [{"id": 1, "name": "bob"}]

        with patch.object(
            SQLEvaluator, "execute_sql_safely",
            side_effect=[
                (True, pred_results, None),
                (True, gold_results, None),
            ]
        ):
            is_correct, error = await SQLEvaluator.compare_sql_results(
                mock_engine, "SELECT * FROM pred", "SELECT * FROM gold"
            )

            assert is_correct is False
            assert "Result content mismatch" in error

    @pytest.mark.asyncio
    async def test_compare_pred_sql_error(self, mock_engine):
        """Test when predicted SQL fails."""
        with patch.object(
            SQLEvaluator, "execute_sql_safely",
            return_value=(False, None, "Syntax error")
        ):
            is_correct, error = await SQLEvaluator.compare_sql_results(
                mock_engine, "INVALID SQL", "SELECT * FROM users"
            )

            assert is_correct is False
            assert "Predicted SQL error" in error

    @pytest.mark.asyncio
    async def test_compare_gold_sql_error(self, mock_engine):
        """Test when gold SQL fails."""
        with patch.object(
            SQLEvaluator, "execute_sql_safely",
            side_effect=[
                (True, [{"id": 1}], None),
                (False, None, "Syntax error"),
            ]
        ):
            is_correct, error = await SQLEvaluator.compare_sql_results(
                mock_engine, "SELECT * FROM users", "INVALID SQL"
            )

            assert is_correct is False
            assert "Gold SQL error" in error


class TestDetermineErrorType:
    """Tests for error type determination."""

    def test_no_error_success(self):
        """Test successful execution with no error."""
        error_type = determine_error_type(
            execution_success=True,
            is_correct=True,
            execution_error=None
        )
        assert error_type is None

    def test_syntax_error(self):
        """Test syntax error detection."""
        error_type = determine_error_type(
            execution_success=False,
            is_correct=None,
            execution_error="near 'SELEC': syntax error"
        )
        assert error_type == "syntax_error"

    def test_timeout_error(self):
        """Test timeout error detection."""
        error_type = determine_error_type(
            execution_success=False,
            is_correct=None,
            execution_error="Query timed out after 30 seconds"
        )
        assert error_type == "timeout"

    def test_permission_error(self):
        """Test permission error detection."""
        error_type = determine_error_type(
            execution_success=False,
            is_correct=None,
            execution_error="permission denied for table users"
        )
        assert error_type == "permission_error"

    def test_table_not_found(self):
        """Test table not found error."""
        error_type = determine_error_type(
            execution_success=False,
            is_correct=None,
            execution_error="table 'users' does not exist"
        )
        assert error_type == "table_not_found"

    def test_column_not_found(self):
        """Test column not found error."""
        error_type = determine_error_type(
            execution_success=False,
            is_correct=None,
            execution_error="column 'name' does not exist"
        )
        assert error_type == "column_not_found"

    def test_generic_execution_error(self):
        """Test generic execution error."""
        error_type = determine_error_type(
            execution_success=False,
            is_correct=None,
            execution_error="Some unknown error"
        )
        assert error_type == "execution_error"

    def test_wrong_result_error(self):
        """Test wrong result error."""
        error_type = determine_error_type(
            execution_success=True,
            is_correct=False,
            execution_error=None
        )
        assert error_type == "wrong_result"


class TestMajorityVoter:
    """Tests for majority voting."""

    @pytest.fixture
    def mock_engine(self):
        """Create a mock async engine."""
        engine = MagicMock()
        return engine

    @pytest.mark.asyncio
    async def test_majority_voting_single_sql(self, mock_engine):
        """Test majority voting with single SQL."""
        selected_sql, vote_count, details = await MajorityVoter.majority_voting(
            mock_engine, ["SELECT * FROM users"]
        )

        assert selected_sql == "SELECT * FROM users"
        assert vote_count == 1

    @pytest.mark.asyncio
    async def test_majority_voting_empty_list(self, mock_engine):
        """Test majority voting with empty list."""
        with pytest.raises(ValueError, match="Empty SQL list"):
            await MajorityVoter.majority_voting(mock_engine, [])

    @pytest.mark.asyncio
    async def test_majority_voting_with_tie(self, mock_engine):
        """Test majority voting with tied results."""
        # Mock execute_and_hash to return different hashes for different SQLs
        with patch.object(
            MajorityVoter, "execute_and_hash",
            side_effect=[
                ("hash1", None),  # SQL 1
                ("hash2", None),  # SQL 2
            ]
        ):
            selected_sql, vote_count, details = await MajorityVoter.majority_voting(
                mock_engine, ["SELECT 1", "SELECT 2"]
            )

            # One of them should be selected (first with most votes)
            assert selected_sql in ["SELECT 1", "SELECT 2"]
            assert vote_count == 1

    @pytest.mark.asyncio
    async def test_majority_voting_all_fail(self, mock_engine):
        """Test majority voting when all SQLs fail."""
        with patch.object(
            MajorityVoter, "execute_and_hash",
            return_value=(None, "Execution error")
        ):
            selected_sql, vote_count, details = await MajorityVoter.majority_voting(
                mock_engine, ["SELECT 1", "SELECT 2"]
            )

            assert selected_sql == "SELECT 1"  # First one returned
            assert vote_count == 0
            assert details["errors"] is not None

    @pytest.mark.asyncio
    async def test_majority_voting_with_confidence(self, mock_engine):
        """Test weighted majority voting."""
        with patch.object(
            MajorityVoter, "execute_and_hash",
            side_effect=[
                ("hash1", None),  # SQL 1
                ("hash1", None),  # SQL 2 - same result
            ]
        ):
            selected_sql, confidence, details = await MajorityVoter.majority_voting_with_confidence(
                mock_engine,
                ["SELECT 1", "SELECT 2"],
                confidence_scores=[0.8, 0.6]
            )

            assert confidence > 0
            assert details["total"] == 2

    @pytest.mark.asyncio
    async def test_majority_voting_confidence_mismatch(self, mock_engine):
        """Test error when confidence scores don't match SQL count."""
        with pytest.raises(ValueError, match="Confidence scores length must match"):
            await MajorityVoter.majority_voting_with_confidence(
                mock_engine,
                ["SELECT 1", "SELECT 2"],
                confidence_scores=[0.8]  # Only one score for two SQLs
            )
