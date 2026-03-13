"""Tests for eval task parent-child functionality."""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.eval_task import EvalTaskService
from app.models.eval_task import EvalTask


class TestCreateParentTask:
    """Test cases for create_parent_task method."""

    @pytest.mark.asyncio
    async def test_create_parent_task_success(self):
        """Test successful creation of parent task."""
        mock_db = AsyncMock()

        dataset_config = {
            "name": "BIRD Dataset Evaluation",
            "dataset_type": "bird",
            "dataset_path": "/data/bird",
            "model_config": {"temperature": 0.7, "max_tokens": 2000},
            "eval_mode": "greedy_search",
            "max_iterations": 3,
            "sampling_count": 1,
        }
        user_id = 1

        result = await EvalTaskService.create_parent_task(
            db=mock_db,
            dataset_config=dataset_config,
            user_id=user_id
        )

        assert result is not None
        assert result.task_type == "parent"
        assert result.name == "BIRD Dataset Evaluation"
        assert result.dataset_type == "bird"
        assert result.status == "pending"
        assert result.child_count == 0
        assert result.completed_children == 0

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_parent_task_with_correction_strategy(self):
        """Test parent task creation with correction strategy."""
        mock_db = AsyncMock()

        dataset_config = {
            "name": "BIRD CheckCorrect Evaluation",
            "dataset_type": "bird",
            "dataset_path": "/data/bird",
            "model_config": {"temperature": 0.5},
            "eval_mode": "check_correct",
            "max_iterations": 5,
            "correction_strategy": {"strategy": "self_correction"},
        }
        user_id = 1

        result = await EvalTaskService.create_parent_task(
            db=mock_db,
            dataset_config=dataset_config,
            user_id=user_id
        )

        assert result.task_type == "parent"
        assert result.max_iterations == 5
        assert result.correction_strategy == {"strategy": "self_correction"}


class TestCreateChildTasks:
    """Test cases for create_child_tasks method."""

    @pytest.mark.asyncio
    async def test_create_child_tasks_success(self):
        """Test successful creation of child tasks."""
        mock_db = AsyncMock()

        parent_id = 1
        db_connections = {"california_schools": 10, "financial": 11}
        dataset_questions = {
            "california_schools": [
                {"question_id": "q1", "nl_question": "What is...", "gold_sql": "SELECT..."},
                {"question_id": "q2", "nl_question": "How many...", "gold_sql": "SELECT..."},
            ],
            "financial": [
                {"question_id": "q3", "nl_question": "List all...", "gold_sql": "SELECT..."},
            ]
        }
        parent_config = {
            "name": "BIRD Evaluation",
            "dataset_type": "bird",
            "model_config": {"temperature": 0.7},
            "eval_mode": "greedy_search",
        }
        user_id = 1

        with patch.object(
            EvalTaskService,
            'update_parent_child_count',
            return_value=None
        ):
            result = await EvalTaskService.create_child_tasks(
                db=mock_db,
                parent_id=parent_id,
                db_connections=db_connections,
                dataset_questions=dataset_questions,
                parent_config=parent_config,
                user_id=user_id
            )

            assert len(result) == 2

            # Verify child tasks have correct properties
            california_task = next(t for t in result if t.db_id == "california_schools")
            assert california_task.task_type == "child"
            assert california_task.parent_id == parent_id
            assert california_task.connection_id == 10
            assert california_task.total_questions == 2

            financial_task = next(t for t in result if t.db_id == "financial")
            assert financial_task.connection_id == 11
            assert financial_task.total_questions == 1

    @pytest.mark.asyncio
    async def test_create_child_tasks_skip_empty_questions(self):
        """Test that child tasks are not created for databases without questions."""
        mock_db = AsyncMock()

        parent_id = 1
        db_connections = {"california_schools": 10, "empty_db": 11}
        dataset_questions = {
            "california_schools": [
                {"question_id": "q1", "nl_question": "What is...", "gold_sql": "SELECT..."},
            ],
            "empty_db": []
        }
        parent_config = {
            "name": "BIRD Evaluation",
            "dataset_type": "bird",
            "model_config": {},
            "eval_mode": "greedy_search",
        }
        user_id = 1

        with patch.object(
            EvalTaskService,
            'update_parent_child_count',
            return_value=None
        ):
            result = await EvalTaskService.create_child_tasks(
                db=mock_db,
                parent_id=parent_id,
                db_connections=db_connections,
                dataset_questions=dataset_questions,
                parent_config=parent_config,
                user_id=user_id
            )

            assert len(result) == 1
            assert result[0].db_id == "california_schools"


class TestUpdateParentStats:
    """Test cases for update_parent_stats method."""

    @pytest.mark.asyncio
    async def test_update_parent_stats_all_completed(self):
        """Test updating parent stats when all children completed."""
        mock_db = AsyncMock()

        # Mock parent task
        parent = MagicMock()
        parent.task_type = "parent"
        parent.status = "running"

        # Mock children
        child1 = MagicMock()
        child1.status = "completed"
        child1.total_questions = 10
        child1.processed_questions = 10
        child1.correct_count = 8

        child2 = MagicMock()
        child2.status = "completed"
        child2.total_questions = 5
        child2.processed_questions = 5
        child2.correct_count = 3

        # Setup mock results
        parent_result = MagicMock()
        parent_result.scalar_one_or_none.return_value = parent

        children_result = MagicMock()
        children_result.scalars.return_value.all.return_value = [child1, child2]

        mock_db.execute.side_effect = [parent_result, children_result]

        await EvalTaskService.update_parent_stats(mock_db, parent_id=1)

        assert parent.child_count == 2
        assert parent.completed_children == 2
        assert parent.total_questions == 15
        assert parent.processed_questions == 15
        assert parent.correct_count == 11
        assert parent.accuracy == 11 / 15
        assert parent.progress_percent == 100
        assert parent.status == "completed"
        assert parent.completed_at is not None

        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_parent_stats_partial_completion(self):
        """Test updating parent stats when some children are still running."""
        mock_db = AsyncMock()

        parent = MagicMock()
        parent.task_type = "parent"

        child1 = MagicMock()
        child1.status = "completed"
        child1.total_questions = 10
        child1.processed_questions = 10
        child1.correct_count = 8

        child2 = MagicMock()
        child2.status = "running"
        child2.total_questions = 5
        child2.processed_questions = 2
        child2.correct_count = 1

        parent_result = MagicMock()
        parent_result.scalar_one_or_none.return_value = parent

        children_result = MagicMock()
        children_result.scalars.return_value.all.return_value = [child1, child2]

        mock_db.execute.side_effect = [parent_result, children_result]

        await EvalTaskService.update_parent_stats(mock_db, parent_id=1)

        assert parent.completed_children == 1
        assert parent.total_questions == 15
        assert parent.processed_questions == 12
        assert parent.status == "running"

    @pytest.mark.asyncio
    async def test_update_parent_stats_all_failed(self):
        """Test updating parent stats when all children failed."""
        mock_db = AsyncMock()

        parent = MagicMock()
        parent.task_type = "parent"

        child1 = MagicMock()
        child1.status = "failed"
        child1.total_questions = 10
        child1.processed_questions = 0
        child1.correct_count = 0

        child2 = MagicMock()
        child2.status = "failed"
        child2.total_questions = 5
        child2.processed_questions = 0
        child2.correct_count = 0

        parent_result = MagicMock()
        parent_result.scalar_one_or_none.return_value = parent

        children_result = MagicMock()
        children_result.scalars.return_value.all.return_value = [child1, child2]

        mock_db.execute.side_effect = [parent_result, children_result]

        await EvalTaskService.update_parent_stats(mock_db, parent_id=1)

        assert parent.status == "failed"


class TestGetChildTasks:
    """Test cases for get_child_tasks method."""

    @pytest.mark.asyncio
    async def test_get_child_tasks_success(self):
        """Test retrieving child tasks."""
        mock_db = AsyncMock()

        # Mock parent verification
        parent = MagicMock()
        parent.id = 1
        parent.user_id = 1

        parent_result = MagicMock()
        parent_result.scalar_one_or_none.return_value = parent

        # Mock children
        child1 = MagicMock()
        child1.id = 2
        child1.parent_id = 1

        child2 = MagicMock()
        child2.id = 3
        child2.parent_id = 1

        children_result = MagicMock()
        children_result.scalars.return_value.all.return_value = [child1, child2]

        mock_db.execute.side_effect = [parent_result, children_result]

        result = await EvalTaskService.get_child_tasks(
            db=mock_db,
            parent_id=1,
            user_id=1
        )

        assert len(result) == 2
        assert result[0].id == 2
        assert result[1].id == 3

    @pytest.mark.asyncio
    async def test_get_child_tasks_unauthorized(self):
        """Test retrieving child tasks with wrong user."""
        mock_db = AsyncMock()

        # Mock parent not found (different user)
        parent_result = MagicMock()
        parent_result.scalar_one_or_none.return_value = None

        mock_db.execute.return_value = parent_result

        result = await EvalTaskService.get_child_tasks(
            db=mock_db,
            parent_id=1,
            user_id=999
        )

        assert result == []


class TestUpdateParentChildCount:
    """Test cases for update_parent_child_count method."""

    @pytest.mark.asyncio
    async def test_update_parent_child_count(self):
        """Test updating parent child count."""
        mock_db = AsyncMock()

        # Mock count query
        count_result = MagicMock()
        count_result.scalar.return_value = 5

        # Mock parent query
        parent = MagicMock()
        parent.child_count = 0

        parent_result = MagicMock()
        parent_result.scalar_one_or_none.return_value = parent

        mock_db.execute.side_effect = [count_result, parent_result]

        await EvalTaskService.update_parent_child_count(mock_db, parent_id=1)

        assert parent.child_count == 5
        mock_db.commit.assert_called_once()
