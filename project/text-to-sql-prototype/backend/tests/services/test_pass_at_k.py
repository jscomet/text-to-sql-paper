"""Tests for Pass@K evaluation service."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.pass_at_k import (
    PassAtKEvaluator,
    CandidateSQL,
    PassAtKMetrics,
    PassAtKResult,
)
from app.services.sql_checker import ErrorType, SQLChecker


class TestCandidateSQL:
    """Tests for CandidateSQL dataclass."""

    def test_candidate_sql_defaults(self):
        """Test CandidateSQL default values."""
        candidate = CandidateSQL(sql="SELECT * FROM users")

        assert candidate.sql == "SELECT * FROM users"
        assert candidate.confidence == 0.0
        assert candidate.execution_success is False
        assert candidate.is_correct is None
        assert candidate.error_type is None
        assert candidate.error_message is None
        assert candidate.execution_time_ms is None
        assert candidate.row_count is None

    def test_candidate_sql_with_values(self):
        """Test CandidateSQL with all values."""
        candidate = CandidateSQL(
            sql="SELECT * FROM users",
            confidence=0.95,
            execution_success=True,
            is_correct=True,
            error_type=None,
            error_message=None,
            execution_time_ms=150.5,
            row_count=10,
        )

        assert candidate.confidence == 0.95
        assert candidate.execution_success is True
        assert candidate.is_correct is True
        assert candidate.execution_time_ms == 150.5
        assert candidate.row_count == 10


class TestPassAtKMetrics:
    """Tests for PassAtKMetrics dataclass."""

    def test_metrics_defaults(self):
        """Test PassAtKMetrics default values."""
        metrics = PassAtKMetrics(
            k=8,
            pass_at_k=0.75,
            correct_count=6,
            executable_count=7,
            total_count=8,
        )

        assert metrics.k == 8
        assert metrics.pass_at_k == 0.75
        assert metrics.correct_count == 6
        assert metrics.executable_count == 7
        assert metrics.total_count == 8
        assert metrics.majority_vote_sql is None
        assert metrics.majority_vote_count == 0

    def test_metrics_with_majority_vote(self):
        """Test PassAtKMetrics with majority vote."""
        metrics = PassAtKMetrics(
            k=8,
            pass_at_k=0.75,
            correct_count=6,
            executable_count=7,
            total_count=8,
            majority_vote_sql="SELECT * FROM users",
            majority_vote_count=5,
        )

        assert metrics.majority_vote_sql == "SELECT * FROM users"
        assert metrics.majority_vote_count == 5


class TestPassAtKEvaluatorInit:
    """Tests for PassAtKEvaluator initialization."""

    def test_init_default(self):
        """Test default initialization."""
        checker = MagicMock(spec=SQLChecker)
        evaluator = PassAtKEvaluator(checker=checker)

        assert evaluator.checker == checker
        assert evaluator.max_workers == 4
        assert evaluator.timeout_seconds == 30.0

    def test_init_custom(self):
        """Test initialization with custom values."""
        checker = MagicMock(spec=SQLChecker)
        evaluator = PassAtKEvaluator(
            checker=checker,
            max_workers=8,
            timeout_seconds=60.0,
        )

        assert evaluator.max_workers == 8
        assert evaluator.timeout_seconds == 60.0


class TestPassAtKEvaluatorGenerateK:
    """Tests for generate_k method."""

    @pytest.fixture
    def evaluator(self):
        """Create a PassAtKEvaluator instance."""
        checker = MagicMock(spec=SQLChecker)
        return PassAtKEvaluator(checker=checker)

    @pytest.mark.asyncio
    async def test_generate_k_success(self, evaluator):
        """Test successful generation of K candidates."""
        mock_sqls = [
            "SELECT * FROM users WHERE id = 1",
            "SELECT * FROM users WHERE id = 2",
            "SELECT * FROM users WHERE id = 3",
        ]

        with patch("app.services.pass_at_k.generate_sql") as mock_generate:
            mock_generate.side_effect = mock_sqls

            results = await evaluator.generate_k(
                question="Get user",
                schema_text="Table: users",
                k=3,
                provider="openai",
                temperature=0.7,
            )

            assert len(results) == 3
            assert all("SELECT" in sql for sql in results)

    @pytest.mark.asyncio
    async def test_generate_k_with_failures(self, evaluator):
        """Test generation with some failures."""
        mock_sqls = [
            "SELECT * FROM users WHERE id = 1",
            Exception("Generation failed"),
            "SELECT * FROM users WHERE id = 3",
        ]

        with patch("app.services.pass_at_k.generate_sql") as mock_generate:
            mock_generate.side_effect = mock_sqls

            results = await evaluator.generate_k(
                question="Get user",
                schema_text="Table: users",
                k=3,
                provider="openai",
            )

            assert len(results) == 2  # One failed

    @pytest.mark.asyncio
    async def test_generate_k_all_fail(self, evaluator):
        """Test generation when all fail."""
        with patch("app.services.pass_at_k.generate_sql") as mock_generate:
            mock_generate.side_effect = Exception("All failed")

            results = await evaluator.generate_k(
                question="Get user",
                schema_text="Table: users",
                k=3,
                provider="openai",
            )

            assert len(results) == 0

    def test_generate_k_invalid_k(self, evaluator):
        """Test generation with invalid K."""
        with pytest.raises(ValueError, match="k must be positive"):
            evaluator.generate_k(
                question="Get user",
                schema_text="Table: users",
                k=0,
            )


class TestPassAtKEvaluatorEvaluate:
    """Tests for evaluate method."""

    @pytest.fixture
    def evaluator(self):
        """Create a PassAtKEvaluator instance."""
        checker = MagicMock(spec=SQLChecker)
        return PassAtKEvaluator(checker=checker)

    @pytest.fixture
    def mock_engine(self):
        """Create a mock database engine."""
        engine = MagicMock()
        engine.url = "sqlite+aiosqlite:///:memory:"
        return engine

    @pytest.mark.asyncio
    async def test_evaluate_empty_candidates(self, evaluator, mock_engine):
        """Test evaluation with empty candidates."""
        results = await evaluator.evaluate([], mock_engine)
        assert results == []

    @pytest.mark.asyncio
    async def test_evaluate_single_candidate_success(self, evaluator, mock_engine):
        """Test evaluation with single successful candidate."""
        from app.services.sql_checker import SyntaxCheckResult, ExecutionCheckResult

        evaluator.checker.check_syntax = AsyncMock(
            return_value=SyntaxCheckResult(is_valid=True)
        )
        evaluator.checker.check_execution = AsyncMock(
            return_value=ExecutionCheckResult(success=True, row_count=5)
        )

        results = await evaluator.evaluate(
            ["SELECT * FROM users"],
            mock_engine,
        )

        assert len(results) == 1
        assert results[0].execution_success is True
        assert results[0].row_count == 5

    @pytest.mark.asyncio
    async def test_evaluate_single_candidate_syntax_error(self, evaluator, mock_engine):
        """Test evaluation with syntax error."""
        from app.services.sql_checker import SyntaxCheckResult

        evaluator.checker.check_syntax = AsyncMock(
            return_value=SyntaxCheckResult(
                is_valid=False,
                error_type=ErrorType.SYNTAX_ERROR,
                error_message="syntax error",
            )
        )

        results = await evaluator.evaluate(
            ["SELECT * FORM users"],
            mock_engine,
        )

        assert len(results) == 1
        assert results[0].execution_success is False
        assert results[0].error_type == ErrorType.SYNTAX_ERROR

    @pytest.mark.asyncio
    async def test_evaluate_multiple_candidates(self, evaluator, mock_engine):
        """Test evaluation with multiple candidates."""
        from app.services.sql_checker import SyntaxCheckResult, ExecutionCheckResult

        # First succeeds, second fails syntax, third succeeds
        evaluator.checker.check_syntax = AsyncMock(side_effect=[
            SyntaxCheckResult(is_valid=True),
            SyntaxCheckResult(
                is_valid=False,
                error_type=ErrorType.SYNTAX_ERROR,
                error_message="syntax error",
            ),
            SyntaxCheckResult(is_valid=True),
        ])
        evaluator.checker.check_execution = AsyncMock(
            return_value=ExecutionCheckResult(success=True, row_count=5)
        )

        results = await evaluator.evaluate(
            [
                "SELECT * FROM users",
                "SELECT * FORM users",
                "SELECT COUNT(*) FROM users",
            ],
            mock_engine,
        )

        assert len(results) == 3
        assert results[0].execution_success is True
        assert results[1].execution_success is False
        assert results[2].execution_success is True


class TestPassAtKEvaluatorCalculateMetrics:
    """Tests for calculate_metrics method."""

    @pytest.fixture
    def evaluator(self):
        """Create a PassAtKEvaluator instance."""
        checker = MagicMock(spec=SQLChecker)
        return PassAtKEvaluator(checker=checker)

    def test_calculate_metrics_empty(self, evaluator):
        """Test metrics calculation with empty candidates."""
        metrics = evaluator.calculate_metrics([], k=8)

        assert metrics.k == 8
        assert metrics.pass_at_k == 0.0
        assert metrics.correct_count == 0
        assert metrics.total_count == 0

    def test_calculate_metrics_all_correct(self, evaluator):
        """Test metrics when all candidates are correct."""
        candidates = [
            CandidateSQL(sql="SELECT 1", execution_success=True, is_correct=True),
            CandidateSQL(sql="SELECT 2", execution_success=True, is_correct=True),
            CandidateSQL(sql="SELECT 3", execution_success=True, is_correct=True),
        ]

        metrics = evaluator.calculate_metrics(candidates, k=3)

        assert metrics.pass_at_k == 1.0  # 100% pass rate
        assert metrics.correct_count == 3
        assert metrics.executable_count == 3
        assert metrics.total_count == 3

    def test_calculate_metrics_none_correct(self, evaluator):
        """Test metrics when no candidates are correct."""
        candidates = [
            CandidateSQL(sql="SELECT 1", execution_success=False, is_correct=False),
            CandidateSQL(sql="SELECT 2", execution_success=False, is_correct=False),
        ]

        metrics = evaluator.calculate_metrics(candidates, k=2)

        assert metrics.pass_at_k == 0.0
        assert metrics.correct_count == 0

    def test_calculate_metrics_partial_correct(self, evaluator):
        """Test metrics with partial correct candidates."""
        candidates = [
            CandidateSQL(sql="SELECT 1", execution_success=True, is_correct=True),
            CandidateSQL(sql="SELECT 2", execution_success=True, is_correct=False),
            CandidateSQL(sql="SELECT 3", execution_success=True, is_correct=True),
            CandidateSQL(sql="SELECT 4", execution_success=False, is_correct=False),
        ]

        metrics = evaluator.calculate_metrics(candidates, k=4)

        # pass_at_k = 1 - (1 - 2/4)^4 = 1 - 0.0625 = 0.9375
        assert metrics.pass_at_k > 0.9
        assert metrics.correct_count == 2
        assert metrics.executable_count == 3
        assert metrics.total_count == 4

    def test_calculate_metrics_with_majority_vote(self, evaluator):
        """Test metrics with majority vote selection."""
        candidates = [
            CandidateSQL(sql="SELECT 1", execution_success=True, row_count=5),
            CandidateSQL(sql="SELECT 1", execution_success=True, row_count=5),
            CandidateSQL(sql="SELECT 2", execution_success=True, row_count=3),
        ]

        metrics = evaluator.calculate_metrics(candidates, k=3)

        assert metrics.majority_vote_sql == "SELECT 1"
        assert metrics.majority_vote_count == 2


class TestPassAtKEvaluatorMajorityVote:
    """Tests for majority voting."""

    @pytest.fixture
    def evaluator(self):
        """Create a PassAtKEvaluator instance."""
        checker = MagicMock(spec=SQLChecker)
        return PassAtKEvaluator(checker=checker)

    def test_majority_vote_empty(self, evaluator):
        """Test majority vote with empty candidates."""
        sql, count = evaluator._majority_vote([])
        assert sql is None
        assert count == 0

    def test_majority_vote_single(self, evaluator):
        """Test majority vote with single candidate."""
        candidates = [
            CandidateSQL(sql="SELECT * FROM users", execution_success=True),
        ]

        sql, count = evaluator._majority_vote(candidates)
        assert sql == "SELECT * FROM users"
        assert count == 1

    def test_majority_vote_clear_winner(self, evaluator):
        """Test majority vote with clear winner."""
        candidates = [
            CandidateSQL(sql="SELECT 1", execution_success=True, row_count=5),
            CandidateSQL(sql="SELECT 1", execution_success=True, row_count=5),
            CandidateSQL(sql="SELECT 1", execution_success=True, row_count=5),
            CandidateSQL(sql="SELECT 2", execution_success=True, row_count=3),
        ]

        sql, count = evaluator._majority_vote(candidates)
        assert sql == "SELECT 1"
        assert count == 3

    def test_majority_vote_with_failures(self, evaluator):
        """Test majority vote with some failures."""
        candidates = [
            CandidateSQL(
                sql="SELECT 1",
                execution_success=False,
                error_type=ErrorType.SYNTAX_ERROR,
            ),
            CandidateSQL(sql="SELECT 2", execution_success=True, row_count=5),
            CandidateSQL(sql="SELECT 2", execution_success=True, row_count=5),
        ]

        sql, count = evaluator._majority_vote(candidates)
        assert sql == "SELECT 2"
        assert count == 2

    def test_majority_vote_all_fail(self, evaluator):
        """Test majority vote when all fail."""
        candidates = [
            CandidateSQL(
                sql="SELECT 1",
                execution_success=False,
                error_type=ErrorType.SYNTAX_ERROR,
            ),
            CandidateSQL(
                sql="SELECT 2",
                execution_success=False,
                error_type=ErrorType.TABLE_NOT_FOUND,
            ),
        ]

        sql, count = evaluator._majority_vote(candidates)
        # Returns first SQL even though all failed
        assert sql in ["SELECT 1", "SELECT 2"]


class TestPassAtKEvaluatorRun:
    """Tests for the main run method."""

    @pytest.fixture
    def evaluator(self):
        """Create a PassAtKEvaluator instance."""
        checker = MagicMock(spec=SQLChecker)
        return PassAtKEvaluator(checker=checker)

    @pytest.fixture
    def mock_engine(self):
        """Create a mock database engine."""
        engine = MagicMock()
        engine.url = "sqlite+aiosqlite:///:memory:"
        return engine

    @pytest.mark.asyncio
    async def test_run_success(self, evaluator, mock_engine):
        """Test successful run."""
        from app.services.sql_checker import SyntaxCheckResult, ExecutionCheckResult

        evaluator.checker.check_syntax = AsyncMock(
            return_value=SyntaxCheckResult(is_valid=True)
        )
        evaluator.checker.check_execution = AsyncMock(
            return_value=ExecutionCheckResult(success=True, row_count=5)
        )

        mock_sqls = ["SELECT * FROM users", "SELECT COUNT(*) FROM users"]

        with patch.object(evaluator, "generate_k", AsyncMock(return_value=mock_sqls)):
            result = await evaluator.run(
                question="Get users",
                schema_text="Table: users",
                engine=mock_engine,
                k=2,
                provider="openai",
            )

            assert result.success is True
            assert len(result.candidates) == 2
            assert result.metrics is not None

    @pytest.mark.asyncio
    async def test_run_no_candidates(self, evaluator, mock_engine):
        """Test run when no candidates generated."""
        with patch.object(evaluator, "generate_k", AsyncMock(return_value=[])):
            result = await evaluator.run(
                question="Get users",
                schema_text="Table: users",
                engine=mock_engine,
                k=2,
                provider="openai",
            )

            assert result.success is False
            assert "No candidates" in result.error_message or "Failed to generate" in result.error_message

    @pytest.mark.asyncio
    async def test_run_with_gold_sql(self, evaluator, mock_engine):
        """Test run with gold SQL for comparison."""
        from app.services.sql_checker import SyntaxCheckResult, ExecutionCheckResult

        evaluator.checker.check_syntax = AsyncMock(
            return_value=SyntaxCheckResult(is_valid=True)
        )
        evaluator.checker.check_execution = AsyncMock(
            return_value=ExecutionCheckResult(success=True, row_count=5)
        )

        mock_sqls = ["SELECT * FROM users"]

        with patch.object(evaluator, "generate_k", AsyncMock(return_value=mock_sqls)):
            result = await evaluator.run(
                question="Get users",
                schema_text="Table: users",
                engine=mock_engine,
                k=1,
                gold_sql="SELECT * FROM users",
                provider="openai",
            )

            assert result.success is True
            assert result.gold_sql == "SELECT * FROM users"


class TestPassAtKResult:
    """Tests for PassAtKResult dataclass."""

    def test_result_creation(self):
        """Test PassAtKResult creation."""
        result = PassAtKResult(
            success=True,
            question="Get users",
            gold_sql="SELECT * FROM users",
            candidates=[],
        )

        assert result.success is True
        assert result.question == "Get users"
        assert result.gold_sql == "SELECT * FROM users"
        assert result.candidates == []
        assert result.metrics is None
        assert result.error_message is None

    def test_result_with_error(self):
        """Test PassAtKResult with error."""
        result = PassAtKResult(
            success=False,
            question="Get users",
            gold_sql=None,
            candidates=[],
            error_message="Generation failed",
            execution_time_ms=1000.0,
        )

        assert result.success is False
        assert result.error_message == "Generation failed"
        assert result.execution_time_ms == 1000.0
