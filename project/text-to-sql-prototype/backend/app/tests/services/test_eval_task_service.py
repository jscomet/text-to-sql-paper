"""Tests for eval_task service."""
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.eval_task import EvalTask
from app.schemas.evaluation import EvalTaskCreate
from app.services.eval_task import EvalTaskService


@pytest_asyncio.fixture
async def mock_db():
    """Create a mock database session."""
    db = AsyncMock(spec=AsyncSession)
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()
    return db


@pytest_asyncio.fixture
async def sample_task_create():
    """Create sample EvalTaskCreate data."""
    return EvalTaskCreate(
        name="Test Task",
        dataset_type="bird",
        dataset_path="/path/to/dataset",
        connection_id=1,
        api_key_id=1,
        temperature=0.7,
        max_tokens=2000,
        eval_mode="greedy_search",
    )


class TestCreateEvalTask:
    """Tests for create_eval_task method."""

    @pytest.mark.asyncio
    async def test_create_eval_task(self, mock_db, sample_task_create):
        """Test creating a basic evaluation task."""
        task = await EvalTaskService.create_eval_task(
            db=mock_db,
            user_id=1,
            task_data=sample_task_create,
        )

        assert task.user_id == 1
        assert task.name == "Test Task"
        assert task.dataset_type == "bird"
        assert task.status == "pending"
        assert task.progress_percent == 0
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_task_with_model_config(self, mock_db):
        """Test creating task with model configuration."""
        task_data = EvalTaskCreate(
            name="Task with Config",
            dataset_type="bird",
            dataset_path="/path",
            connection_id=1,
            api_key_id=1,
            temperature=0.5,
            max_tokens=1000,
            eval_mode="pass_at_k",
        )

        task = await EvalTaskService.create_eval_task(
            db=mock_db,
            user_id=1,
            task_data=task_data,
        )

        assert task.model_config["temperature"] == 0.5
        assert task.model_config["max_tokens"] == 1000


class TestGetEvalTask:
    """Tests for get_eval_task method."""

    @pytest.mark.asyncio
    async def test_get_existing_task(self, mock_db):
        """Test getting an existing task."""
        mock_task = MagicMock(spec=EvalTask)
        mock_task.id = 1
        mock_task.user_id = 1

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_task
        mock_db.execute = AsyncMock(return_value=mock_result)

        task = await EvalTaskService.get_eval_task(mock_db, task_id=1, user_id=1)

        assert task is not None
        assert task.id == 1

    @pytest.mark.asyncio
    async def test_get_nonexistent_task(self, mock_db):
        """Test getting a non-existent task."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        task = await EvalTaskService.get_eval_task(mock_db, task_id=999, user_id=1)

        assert task is None

    @pytest.mark.asyncio
    async def test_get_task_wrong_user(self, mock_db):
        """Test getting task belonging to different user."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        task = await EvalTaskService.get_eval_task(mock_db, task_id=1, user_id=2)

        assert task is None


class TestUpdateTaskProgress:
    """Tests for update_task_progress method."""

    @pytest.mark.asyncio
    async def test_update_progress(self, mock_db):
        """Test updating task progress."""
        task = MagicMock(spec=EvalTask)
        task.processed_questions = 0
        task.total_questions = 0
        task.progress_percent = 0

        await EvalTaskService.update_task_progress(
            db=mock_db,
            task=task,
            processed=50,
            total=100,
            correct=45,
        )

        assert task.processed_questions == 50
        assert task.total_questions == 100
        assert task.progress_percent == 50
        assert task.correct_count == 45
        assert task.accuracy == 0.45
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_progress_zero_total(self, mock_db):
        """Test updating progress with zero total questions."""
        task = MagicMock(spec=EvalTask)
        task.processed_questions = 0
        task.total_questions = 0
        task.progress_percent = 0

        await EvalTaskService.update_task_progress(
            db=mock_db,
            task=task,
            processed=0,
            total=0,
        )

        assert task.progress_percent == 0


class TestCompleteEvalTask:
    """Tests for complete_eval_task method."""

    @pytest.mark.asyncio
    async def test_complete_task(self, mock_db):
        """Test completing a task."""
        task = MagicMock(spec=EvalTask)
        task.status = "running"
        task.correct_count = 0
        task.total_questions = 0
        task.accuracy = 0.0
        task.progress_percent = 0
        task.is_child.return_value = False

        await EvalTaskService.complete_eval_task(
            db=mock_db,
            task=task,
            correct_count=80,
            total_count=100,
        )

        assert task.status == "completed"
        assert task.correct_count == 80
        assert task.total_questions == 100
        assert task.accuracy == 0.8
        assert task.progress_percent == 100
        assert task.completed_at is not None

    @pytest.mark.asyncio
    async def test_complete_child_task_updates_parent(self, mock_db):
        """Test that completing child task updates parent statistics."""
        task = MagicMock(spec=EvalTask)
        task.status = "running"
        task.parent_id = 100
        task.is_child.return_value = True

        with patch.object(
            EvalTaskService, "update_parent_on_child_complete", new_callable=AsyncMock
        ) as mock_update:
            await EvalTaskService.complete_eval_task(
                db=mock_db,
                task=task,
                correct_count=50,
                total_count=50,
            )
            mock_update.assert_called_once_with(mock_db, 100)


class TestFailEvalTask:
    """Tests for fail_eval_task method."""

    @pytest.mark.asyncio
    async def test_fail_task(self, mock_db):
        """Test failing a task."""
        task = MagicMock(spec=EvalTask)
        task.status = "running"
        task.error_message = None
        task.is_child.return_value = False

        await EvalTaskService.fail_eval_task(
            db=mock_db,
            task=task,
            error_message="Connection timeout",
        )

        assert task.status == "failed"
        assert task.error_message == "Connection timeout"
        assert task.updated_at is not None

    @pytest.mark.asyncio
    async def test_fail_child_task_updates_parent(self, mock_db):
        """Test that failing child task updates parent statistics."""
        task = MagicMock(spec=EvalTask)
        task.parent_id = 100
        task.is_child.return_value = True

        with patch.object(
            EvalTaskService, "update_parent_on_child_complete", new_callable=AsyncMock
        ) as mock_update:
            await EvalTaskService.fail_eval_task(
                db=mock_db,
                task=task,
                error_message="Error occurred",
            )
            mock_update.assert_called_once_with(mock_db, 100)


class TestCancelEvalTask:
    """Tests for cancel_eval_task method."""

    @pytest.mark.asyncio
    async def test_cancel_pending_task(self, mock_db):
        """Test cancelling a pending task."""
        task = MagicMock(spec=EvalTask)
        task.status = "pending"

        result = await EvalTaskService.cancel_eval_task(mock_db, task)

        assert result is True
        assert task.status == "cancelled"
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_cancel_running_task(self, mock_db):
        """Test cancelling a running task."""
        task = MagicMock(spec=EvalTask)
        task.status = "running"

        result = await EvalTaskService.cancel_eval_task(mock_db, task)

        assert result is True
        assert task.status == "cancelled"

    @pytest.mark.asyncio
    async def test_cancel_completed_task(self, mock_db):
        """Test cancelling a completed task (should fail)."""
        task = MagicMock(spec=EvalTask)
        task.status = "completed"

        result = await EvalTaskService.cancel_eval_task(mock_db, task)

        assert result is False
        assert task.status == "completed"  # Unchanged


class TestCreateParentTask:
    """Tests for create_parent_task method."""

    @pytest.mark.asyncio
    async def test_create_parent_task(self, mock_db):
        """Test creating a parent task."""
        dataset_config = {
            "name": "BIRD Dataset Evaluation",
            "dataset_type": "bird",
            "dataset_path": "/data/bird",
            "model_config": {"temperature": 0.7, "max_tokens": 2000},
            "eval_mode": "greedy_search",
            "max_iterations": 3,
            "sampling_count": 1,
        }

        task = await EvalTaskService.create_parent_task(
            db=mock_db,
            dataset_config=dataset_config,
            user_id=1,
        )

        assert task.user_id == 1
        assert task.name == "BIRD Dataset Evaluation"
        assert task.dataset_type == "bird"
        assert task.task_type == "parent"
        assert task.status == "pending"
        assert task.child_count == 0
        assert task.completed_children == 0
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_parent_with_correction_strategy(self, mock_db):
        """Test creating parent task with correction strategy."""
        dataset_config = {
            "name": "Task with Correction",
            "dataset_type": "bird",
            "model_config": {},
            "eval_mode": "check_correct",
            "correction_strategy": {"max_attempts": 3},
        }

        task = await EvalTaskService.create_parent_task(
            db=mock_db,
            dataset_config=dataset_config,
            user_id=1,
        )

        assert task.eval_mode == "check_correct"
        assert task.correction_strategy == {"max_attempts": 3}


class TestCreateChildTasks:
    """Tests for create_child_tasks method."""

    @pytest.mark.asyncio
    async def test_create_child_tasks(self, mock_db):
        """Test creating child tasks for a parent."""
        db_connections = {"db1": 101, "db2": 102}
        dataset_questions = {
            "db1": [
                {"question_id": "q1", "nl_question": "Q1", "gold_sql": "S1"},
                {"question_id": "q2", "nl_question": "Q2", "gold_sql": "S2"},
            ],
            "db2": [
                {"question_id": "q3", "nl_question": "Q3", "gold_sql": "S3"},
            ],
        }
        parent_config = {
            "name": "Parent Task",
            "dataset_type": "bird",
            "model_config": {},
            "eval_mode": "greedy_search",
        }

        with patch.object(
            EvalTaskService, "update_parent_child_count", new_callable=AsyncMock
        ) as mock_update:
            child_tasks = await EvalTaskService.create_child_tasks(
                db=mock_db,
                parent_id=100,
                db_connections=db_connections,
                dataset_questions=dataset_questions,
                parent_config=parent_config,
                user_id=1,
            )

            assert len(child_tasks) == 2
            assert child_tasks[0].parent_id == 100
            assert child_tasks[0].task_type == "child"
            assert child_tasks[0].db_id in ["db1", "db2"]
            mock_update.assert_called_once_with(mock_db, 100)

    @pytest.mark.asyncio
    async def test_skip_empty_question_databases(self, mock_db):
        """Test skipping databases with no questions."""
        db_connections = {"db1": 101, "db2": 102}
        dataset_questions = {
            "db1": [{"question_id": "q1", "nl_question": "Q1", "gold_sql": "S1"}],
            "db2": [],  # Empty
        }
        parent_config = {"name": "Parent", "dataset_type": "bird", "model_config": {}}

        with patch.object(
            EvalTaskService, "update_parent_child_count", new_callable=AsyncMock
        ):
            child_tasks = await EvalTaskService.create_child_tasks(
                db=mock_db,
                parent_id=100,
                db_connections=db_connections,
                dataset_questions=dataset_questions,
                parent_config=parent_config,
                user_id=1,
            )

            assert len(child_tasks) == 1
            assert child_tasks[0].db_id == "db1"


class TestUpdateParentStats:
    """Tests for update_parent_stats method."""

    @pytest.mark.asyncio
    async def test_update_parent_with_completed_children(self, mock_db):
        """Test updating parent when all children are completed."""
        parent = MagicMock(spec=EvalTask)
        parent.task_type = "parent"
        parent.child_count = 0
        parent.completed_children = 0
        parent.total_questions = 0
        parent.processed_questions = 0
        parent.correct_count = 0
        parent.accuracy = 0.0
        parent.progress_percent = 0
        parent.status = "pending"

        child1 = MagicMock(spec=EvalTask)
        child1.status = "completed"
        child1.total_questions = 50
        child1.processed_questions = 50
        child1.correct_count = 45

        child2 = MagicMock(spec=EvalTask)
        child2.status = "completed"
        child2.total_questions = 50
        child2.processed_questions = 50
        child2.correct_count = 40

        # Mock the execute calls
        mock_parent_result = MagicMock()
        mock_parent_result.scalar_one_or_none.return_value = parent

        mock_children_result = MagicMock()
        mock_children_result.scalars.return_value.all.return_value = [child1, child2]

        mock_db.execute = AsyncMock(side_effect=[mock_parent_result, mock_children_result])

        await EvalTaskService.update_parent_stats(mock_db, parent_id=100)

        assert parent.child_count == 2
        assert parent.completed_children == 2
        assert parent.total_questions == 100
        assert parent.processed_questions == 100
        assert parent.correct_count == 85
        assert parent.accuracy == 0.85
        assert parent.progress_percent == 100
        assert parent.status == "completed"

    @pytest.mark.asyncio
    async def test_update_parent_with_failed_children(self, mock_db):
        """Test updating parent when some children failed."""
        parent = MagicMock(spec=EvalTask)
        parent.task_type = "parent"
        parent.status = "pending"

        child1 = MagicMock(spec=EvalTask)
        child1.status = "completed"
        child1.total_questions = 50
        child1.processed_questions = 50
        child1.correct_count = 45

        child2 = MagicMock(spec=EvalTask)
        child2.status = "failed"
        child2.total_questions = 50
        child2.processed_questions = 0
        child2.correct_count = 0

        mock_parent_result = MagicMock()
        mock_parent_result.scalar_one_or_none.return_value = parent

        mock_children_result = MagicMock()
        mock_children_result.scalars.return_value.all.return_value = [child1, child2]

        mock_db.execute = AsyncMock(side_effect=[mock_parent_result, mock_children_result])

        await EvalTaskService.update_parent_stats(mock_db, parent_id=100)

        assert parent.completed_children == 2
        assert parent.status == "completed"  # Not all failed

    @pytest.mark.asyncio
    async def test_update_parent_all_failed(self, mock_db):
        """Test updating parent when all children failed."""
        parent = MagicMock(spec=EvalTask)
        parent.task_type = "parent"
        parent.status = "pending"

        child1 = MagicMock(spec=EvalTask)
        child1.status = "failed"
        child1.total_questions = 50
        child1.processed_questions = 0
        child1.correct_count = 0

        child2 = MagicMock(spec=EvalTask)
        child2.status = "failed"
        child2.total_questions = 50
        child2.processed_questions = 0
        child2.correct_count = 0

        mock_parent_result = MagicMock()
        mock_parent_result.scalar_one_or_none.return_value = parent

        mock_children_result = MagicMock()
        mock_children_result.scalars.return_value.all.return_value = [child1, child2]

        mock_db.execute = AsyncMock(side_effect=[mock_parent_result, mock_children_result])

        await EvalTaskService.update_parent_stats(mock_db, parent_id=100)

        assert parent.status == "failed"

    @pytest.mark.asyncio
    async def test_update_nonexistent_parent(self, mock_db):
        """Test updating non-existent parent."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Should not raise exception
        await EvalTaskService.update_parent_stats(mock_db, parent_id=999)

    @pytest.mark.asyncio
    async def test_update_non_parent_task(self, mock_db):
        """Test updating a task that is not a parent."""
        task = MagicMock(spec=EvalTask)
        task.task_type = "child"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = task
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Should not raise exception
        await EvalTaskService.update_parent_stats(mock_db, parent_id=100)


class TestGetChildTasks:
    """Tests for get_child_tasks method."""

    @pytest.mark.asyncio
    async def test_get_child_tasks(self, mock_db):
        """Test getting child tasks for a parent."""
        parent = MagicMock(spec=EvalTask)
        parent.user_id = 1

        child1 = MagicMock(spec=EvalTask)
        child1.id = 1
        child2 = MagicMock(spec=EvalTask)
        child2.id = 2

        mock_parent_result = MagicMock()
        mock_parent_result.scalar_one_or_none.return_value = parent

        mock_children_result = MagicMock()
        mock_children_result.scalars.return_value.all.return_value = [child1, child2]

        mock_db.execute = AsyncMock(side_effect=[mock_parent_result, mock_children_result])

        children = await EvalTaskService.get_child_tasks(mock_db, parent_id=100, user_id=1)

        assert len(children) == 2
        assert children[0].id == 1
        assert children[1].id == 2

    @pytest.mark.asyncio
    async def test_get_children_wrong_user(self, mock_db):
        """Test getting children for parent belonging to different user."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        children = await EvalTaskService.get_child_tasks(mock_db, parent_id=100, user_id=2)

        assert children == []


class TestLoadDataset:
    """Tests for load_dataset method."""

    @pytest.mark.asyncio
    async def test_load_list_format(self, temp_dir):
        """Test loading dataset in list format."""
        data = [{"question_id": "q1"}, {"question_id": "q2"}]
        json_path = temp_dir + "/data.json"
        with open(json_path, "w") as f:
            json.dump(data, f)

        result = await EvalTaskService.load_dataset(json_path)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_load_dict_with_data_key(self, temp_dir):
        """Test loading dataset with data key."""
        data = {"data": [{"question_id": "q1"}, {"question_id": "q2"}]}
        json_path = temp_dir + "/data.json"
        with open(json_path, "w") as f:
            json.dump(data, f)

        result = await EvalTaskService.load_dataset(json_path)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_load_single_object(self, temp_dir):
        """Test loading single object as dataset."""
        data = {"question_id": "q1"}
        json_path = temp_dir + "/data.json"
        with open(json_path, "w") as f:
            json.dump(data, f)

        result = await EvalTaskService.load_dataset(json_path)
        assert len(result) == 1
        assert result[0]["question_id"] == "q1"

    @pytest.mark.asyncio
    async def test_load_nonexistent_file(self):
        """Test loading non-existent file raises exception."""
        with pytest.raises(Exception):
            await EvalTaskService.load_dataset("/nonexistent/file.json")
