"""Evaluation task service for managing evaluation tasks."""
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.eval_result import EvalResult
from app.models.eval_task import EvalTask
from app.schemas.evaluation import EvalTaskCreate, EvalTaskStats

logger = get_logger(__name__)

logger = get_logger(__name__)


class EvalTaskService:
    """Service for managing evaluation tasks."""

    @staticmethod
    async def create_eval_task(
        db: AsyncSession,
        user_id: int,
        task_data: EvalTaskCreate,
    ) -> EvalTask:
        """Create a new evaluation task.

        Args:
            db: Database session.
            user_id: User ID who owns the task.
            task_data: Task creation data.

        Returns:
            Created EvalTask object.
        """
        # Build model_config from schema fields
        # Note: provider and model are now retrieved from APIKey in the API layer
        model_config = {
            "temperature": task_data.temperature,
            "max_tokens": task_data.max_tokens,
        }

        task = EvalTask(
            user_id=user_id,
            name=task_data.name,
            dataset_type=task_data.dataset_type,
            dataset_path=task_data.dataset_path,
            model_config=model_config,
            eval_mode=task_data.eval_mode,
            status="pending",
            progress_percent=0,
            processed_questions=0,
        )

        db.add(task)
        await db.commit()
        await db.refresh(task)

        logger.info(f"Created eval task {task.id} for user {user_id}")
        return task

    @staticmethod
    async def get_eval_task(
        db: AsyncSession,
        task_id: int,
        user_id: int,
    ) -> Optional[EvalTask]:
        """Get an evaluation task by ID.

        Args:
            db: Database session.
            task_id: Task ID.
            user_id: User ID for access control.

        Returns:
            EvalTask object or None if not found.
        """
        result = await db.execute(
            select(EvalTask).where(
                EvalTask.id == task_id,
                EvalTask.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_eval_tasks(
        db: AsyncSession,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
    ) -> List[EvalTask]:
        """List evaluation tasks for a user.

        Args:
            db: Database session.
            user_id: User ID.
            skip: Number of tasks to skip.
            limit: Maximum number of tasks to return.
            status: Optional status filter.

        Returns:
            List of EvalTask objects.
        """
        query = select(EvalTask).where(EvalTask.user_id == user_id)

        if status:
            query = query.where(EvalTask.status == status)

        query = query.order_by(EvalTask.created_at.desc())
        query = query.offset(skip).limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def update_task_progress(
        db: AsyncSession,
        task: EvalTask,
        processed: int,
        total: int,
        correct: Optional[int] = None,
    ) -> None:
        """Update task progress.

        Args:
            db: Database session.
            task: EvalTask object.
            processed: Number of processed questions.
            total: Total number of questions.
            correct: Optional number of correct predictions.
        """
        task.processed_questions = processed
        task.total_questions = total

        if total > 0:
            task.progress_percent = int((processed / total) * 100)

        if correct is not None:
            task.correct_count = correct
            task.accuracy = correct / total if total > 0 else 0.0

        task.updated_at = datetime.utcnow()
        await db.commit()

    @staticmethod
    async def start_eval_task(
        db: AsyncSession,
        task: EvalTask,
    ) -> None:
        """Mark task as started.

        Args:
            db: Database session.
            task: EvalTask object.
        """
        task.status = "running"
        task.started_at = datetime.utcnow()
        task.updated_at = datetime.utcnow()
        await db.commit()

    @staticmethod
    async def complete_eval_task(
        db: AsyncSession,
        task: EvalTask,
        correct_count: int,
        total_count: int,
    ) -> None:
        """Mark task as completed.

        Args:
            db: Database session.
            task: EvalTask object.
            correct_count: Number of correct predictions.
            total_count: Total number of questions.
        """
        task.status = "completed"
        task.correct_count = correct_count
        task.total_questions = total_count
        task.accuracy = correct_count / total_count if total_count > 0 else 0.0
        task.progress_percent = 100
        task.completed_at = datetime.utcnow()
        task.updated_at = datetime.utcnow()
        await db.commit()

        logger.info(f"Completed eval task {task.id}: {correct_count}/{total_count} = {task.accuracy:.2%}")

        # If this is a child task, update parent statistics
        if task.is_child() and task.parent_id:
            await EvalTaskService.update_parent_on_child_complete(db, task.parent_id)

    @staticmethod
    async def fail_eval_task(
        db: AsyncSession,
        task: EvalTask,
        error_message: str,
    ) -> None:
        """Mark task as failed.

        Args:
            db: Database session.
            task: EvalTask object.
            error_message: Error message.
        """
        task.status = "failed"
        task.error_message = error_message
        task.updated_at = datetime.utcnow()
        await db.commit()

        logger.error(f"Failed eval task {task.id}: {error_message}")

        # If this is a child task, update parent statistics
        if task.is_child() and task.parent_id:
            await EvalTaskService.update_parent_on_child_complete(db, task.parent_id)

    @staticmethod
    async def cancel_eval_task(
        db: AsyncSession,
        task: EvalTask,
    ) -> bool:
        """Cancel a running or pending task.

        Args:
            db: Database session.
            task: EvalTask object.

        Returns:
            True if cancelled, False if cannot cancel.
        """
        if task.status not in ("pending", "running"):
            return False

        task.status = "cancelled"
        task.updated_at = datetime.utcnow()
        await db.commit()

        logger.info(f"Cancelled eval task {task.id}")
        return True

    @staticmethod
    async def get_eval_progress(
        db: AsyncSession,
        task_id: int,
        user_id: int,
    ) -> Optional[Dict[str, Any]]:
        """Get evaluation task progress.

        Args:
            db: Database session.
            task_id: Task ID.
            user_id: User ID for access control.

        Returns:
            Progress dictionary or None if task not found.
        """
        task = await EvalTaskService.get_eval_task(db, task_id, user_id)
        if not task:
            return None

        return {
            "task_id": task.id,
            "status": task.status,
            "progress_percent": task.progress_percent,
            "processed_questions": task.processed_questions,
            "total_questions": task.total_questions,
            "correct_count": task.correct_count,
            "accuracy": task.accuracy,
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        }

    @staticmethod
    async def get_eval_results(
        db: AsyncSession,
        task_id: int,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        is_correct: Optional[bool] = None,
        error_type: Optional[str] = None,
    ) -> List[EvalResult]:
        """Get evaluation results for a task.

        Args:
            db: Database session.
            task_id: Task ID.
            user_id: User ID for access control.
            skip: Number of results to skip.
            limit: Maximum number of results to return.
            is_correct: Optional filter by correctness.
            error_type: Optional filter by error type.

        Returns:
            List of EvalResult objects.
        """
        # First verify task belongs to user
        task = await EvalTaskService.get_eval_task(db, task_id, user_id)
        if not task:
            return []

        query = select(EvalResult).where(EvalResult.task_id == task_id)

        if is_correct is not None:
            query = query.where(EvalResult.is_correct == is_correct)

        if error_type:
            query = query.where(EvalResult.error_type == error_type)

        query = query.order_by(EvalResult.id)
        query = query.offset(skip).limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_eval_stats(
        db: AsyncSession,
        task_id: int,
        user_id: int,
    ) -> Optional[EvalTaskStats]:
        """Get evaluation task statistics.

        Args:
            db: Database session.
            task_id: Task ID.
            user_id: User ID for access control.

        Returns:
            EvalTaskStats object or None if task not found.
        """
        task = await EvalTaskService.get_eval_task(db, task_id, user_id)
        if not task:
            return None

        # Get error type distribution
        error_types_query = await db.execute(
            select(EvalResult.error_type, func.count(EvalResult.id))
            .where(EvalResult.task_id == task_id)
            .where(EvalResult.error_type.isnot(None))
            .group_by(EvalResult.error_type)
        )
        error_types = {row[0]: row[1] for row in error_types_query.all()}

        # Get correctness distribution
        correct_count_query = await db.execute(
            select(func.count(EvalResult.id))
            .where(EvalResult.task_id == task_id)
            .where(EvalResult.is_correct.is_(True))
        )
        correct_count = correct_count_query.scalar() or 0

        incorrect_count_query = await db.execute(
            select(func.count(EvalResult.id))
            .where(EvalResult.task_id == task_id)
            .where(EvalResult.is_correct.is_(False))
        )
        incorrect_count = incorrect_count_query.scalar() or 0

        pending_count_query = await db.execute(
            select(func.count(EvalResult.id))
            .where(EvalTask.id == task_id)
            .where(EvalResult.is_correct.is_(None))
        )
        pending_count = pending_count_query.scalar() or 0

        total = correct_count + incorrect_count + pending_count

        return EvalTaskStats(
            task_id=task.id,
            total_questions=total,
            correct_count=correct_count,
            incorrect_count=incorrect_count,
            pending_count=pending_count,
            accuracy=correct_count / total if total > 0 else 0.0,
            error_types=error_types,
            avg_execution_time_ms=0.0,  # TODO: Calculate from results
        )

    @staticmethod
    async def create_eval_result(
        db: AsyncSession,
        task_id: int,
        question_id: str,
        nl_question: str,
        gold_sql: str,
        predicted_sql: Optional[str] = None,
        is_correct: Optional[bool] = None,
        error_type: Optional[str] = None,
        error_message: Optional[str] = None,
        execution_time_ms: Optional[float] = None,
        db_id: Optional[str] = None,
        # Advanced inference fields
        candidate_sqls: Optional[List[Dict[str, Any]]] = None,
        iteration_count: Optional[int] = None,
        correction_history: Optional[List[Dict[str, Any]]] = None,
        confidence_score: Optional[float] = None,
    ) -> EvalResult:
        """Create an evaluation result record.

        Args:
            db: Database session.
            task_id: Task ID.
            question_id: Question identifier.
            nl_question: Natural language question.
            gold_sql: Gold/reference SQL.
            predicted_sql: Predicted SQL.
            is_correct: Whether prediction is correct.
            error_type: Type of error if failed.
            error_message: Error message if failed.
            execution_time_ms: Execution time in milliseconds.
            db_id: Database ID.
            candidate_sqls: List of candidate SQLs for pass_at_k mode.
            iteration_count: Number of iterations for check_correct mode.
            correction_history: Correction history for check_correct mode.
            confidence_score: Confidence score for the prediction.

        Returns:
            Created EvalResult object.
        """
        # Serialize advanced inference fields to JSON if provided
        candidate_sqls_json = json.dumps(candidate_sqls) if candidate_sqls is not None else None
        correction_history_json = json.dumps(correction_history) if correction_history is not None else None

        result = EvalResult(
            task_id=task_id,
            question_id=question_id,
            nl_question=nl_question,
            db_id=db_id,
            gold_sql=gold_sql,
            predicted_sql=predicted_sql,
            is_correct=is_correct,
            error_type=error_type,
            error_message=error_message,
            execution_time_ms=execution_time_ms,
            # Advanced inference fields
            candidate_sqls=candidate_sqls_json,
            iteration_count=iteration_count,
            correction_history=correction_history_json,
            confidence_score=confidence_score,
        )

        db.add(result)
        await db.commit()
        await db.refresh(result)

        return result

    @staticmethod
    async def load_dataset(dataset_path: str) -> List[Dict[str, Any]]:
        """Load evaluation dataset from JSON file.

        Args:
            dataset_path: Path to dataset file.

        Returns:
            List of dataset items.
        """
        try:
            with open(dataset_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Handle both list and dict formats
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and "data" in data:
                return data["data"]
            else:
                return [data]

        except Exception as e:
            logger.error(f"Failed to load dataset from {dataset_path}: {e}")
            raise

    @staticmethod
    async def create_parent_task(
        db: AsyncSession,
        dataset_config: Dict[str, Any],
        user_id: int,
    ) -> EvalTask:
        """Create a parent task as a container for child tasks.

        This method creates a parent evaluation task that serves as a container
        for multiple child tasks, typically used when importing BIRD dataset
        with multiple databases.

        Args:
            db: Database session.
            dataset_config: Dataset configuration containing:
                - name: Task name
                - dataset_type: Type of dataset (e.g., "bird")
                - dataset_path: Path to the dataset
                - model_config: Model configuration dict
                - eval_mode: Evaluation mode
                - max_iterations: Max iterations for check_correct mode
                - sampling_count: Sampling count for pass_at_k mode
                - correction_strategy: Correction strategy config
            user_id: User ID who owns the task.

        Returns:
            Created parent EvalTask object.

        Example:
            >>> config = {
            ...     "name": "BIRD Dataset Evaluation",
            ...     "dataset_type": "bird",
            ...     "dataset_path": "/data/bird",
            ...     "model_config": {"temperature": 0.7, "max_tokens": 2000},
            ...     "eval_mode": "greedy_search"
            ... }
            >>> parent_task = await EvalTaskService.create_parent_task(db, config, user_id=1)
        """
        # Build model_config from dataset_config
        model_config = dataset_config.get("model_config", {})

        # Extract correction_strategy if present
        correction_strategy = dataset_config.get("correction_strategy")

        task = EvalTask(
            user_id=user_id,
            name=dataset_config["name"],
            dataset_type=dataset_config["dataset_type"],
            dataset_path=dataset_config.get("dataset_path"),
            model_config=model_config,
            eval_mode=dataset_config.get("eval_mode", "greedy_search"),
            max_iterations=dataset_config.get("max_iterations", 3),
            sampling_count=dataset_config.get("sampling_count", 1),
            correction_strategy=correction_strategy,
            task_type="parent",
            status="pending",
            progress_percent=0,
            processed_questions=0,
            child_count=0,
            completed_children=0,
        )

        db.add(task)
        await db.commit()
        await db.refresh(task)

        logger.info(f"Created parent task {task.id} for user {user_id}")
        return task

    @staticmethod
    async def create_child_tasks(
        db: AsyncSession,
        parent_id: int,
        db_connections: Dict[str, int],
        dataset_questions: Dict[str, List[Dict[str, Any]]],
        parent_config: Dict[str, Any],
        user_id: int,
    ) -> List[EvalTask]:
        """Batch create child tasks for a parent task.

        Each child task is associated with a specific database connection and
        contains questions from that database. Child tasks inherit configuration
        from the parent task.

        Args:
            db: Database session.
            parent_id: Parent task ID.
            db_connections: Dictionary mapping db_id to connection_id.
            dataset_questions: Dictionary mapping db_id to list of questions.
                Each question should have: question_id, nl_question, gold_sql
            parent_config: Parent task configuration to inherit.
            user_id: User ID who owns the tasks.

        Returns:
            List of created child EvalTask objects.

        Example:
            >>> db_connections = {"california_schools": 1, "financial": 2}
            >>> questions = {
            ...     "california_schools": [
            ...         {"question_id": "q1", "nl_question": "...", "gold_sql": "..."}
            ...     ]
            ... }
            >>> children = await EvalTaskService.create_child_tasks(
            ...     db, parent_id=1, db_connections=db_connections,
            ...     dataset_questions=questions, parent_config=config, user_id=1
            ... )
        """
        child_tasks: List[EvalTask] = []

        for db_id, connection_id in db_connections.items():
            questions = dataset_questions.get(db_id, [])
            if not questions:
                logger.warning(f"No questions found for database {db_id}, skipping")
                continue

            # Build model_config from parent config
            model_config = parent_config.get("model_config", {})
            correction_strategy = parent_config.get("correction_strategy")

            # Create child task name
            child_name = f"{parent_config.get('name', 'Task')} - {db_id}"

            task = EvalTask(
                user_id=user_id,
                parent_id=parent_id,
                task_type="child",
                db_id=db_id,
                connection_id=connection_id,
                name=child_name,
                dataset_type=parent_config.get("dataset_type", "bird"),
                dataset_path=parent_config.get("dataset_path"),
                model_config=model_config,
                eval_mode=parent_config.get("eval_mode", "greedy_search"),
                max_iterations=parent_config.get("max_iterations", 3),
                sampling_count=parent_config.get("sampling_count", 1),
                correction_strategy=correction_strategy,
                status="pending",
                progress_percent=0,
                total_questions=len(questions),
                processed_questions=0,
            )

            db.add(task)
            child_tasks.append(task)
            logger.info(f"Created child task for {db_id} with {len(questions)} questions")

        # Commit all child tasks
        await db.commit()

        # Refresh all tasks to get their IDs
        for task in child_tasks:
            await db.refresh(task)

        # Update parent task's child_count
        await EvalTaskService.update_parent_child_count(db, parent_id)

        logger.info(f"Created {len(child_tasks)} child tasks for parent {parent_id}")
        return child_tasks

    @staticmethod
    async def update_parent_child_count(
        db: AsyncSession,
        parent_id: int,
    ) -> None:
        """Update parent task's child count.

        Args:
            db: Database session.
            parent_id: Parent task ID.
        """
        # Get current child count
        result = await db.execute(
            select(func.count(EvalTask.id)).where(EvalTask.parent_id == parent_id)
        )
        child_count = result.scalar() or 0

        # Update parent task
        result = await db.execute(
            select(EvalTask).where(EvalTask.id == parent_id)
        )
        parent = result.scalar_one_or_none()

        if parent:
            parent.child_count = child_count
            await db.commit()
            logger.info(f"Updated parent {parent_id} child_count to {child_count}")

    @staticmethod
    async def update_parent_stats(
        db: AsyncSession,
        parent_id: int,
    ) -> None:
        """Update parent task statistics based on child tasks.

        This method aggregates statistics from all child tasks and updates
        the parent task's progress and completion status.

        Args:
            db: Database session.
            parent_id: Parent task ID.
        """
        # Get parent task
        result = await db.execute(
            select(EvalTask).where(EvalTask.id == parent_id)
        )
        parent = result.scalar_one_or_none()

        if not parent or parent.task_type != "parent":
            logger.error(f"Parent task {parent_id} not found or not a parent task")
            return

        # Get all child tasks
        result = await db.execute(
            select(EvalTask).where(EvalTask.parent_id == parent_id)
        )
        children = result.scalars().all()

        if not children:
            logger.warning(f"No child tasks found for parent {parent_id}")
            return

        # Calculate statistics
        total_children = len(children)
        completed_children = sum(1 for c in children if c.status in ("completed", "failed"))
        total_questions = sum(c.total_questions or 0 for c in children)
        processed_questions = sum(c.processed_questions or 0 for c in children)
        correct_count = sum(c.correct_count or 0 for c in children)

        # Update parent task
        parent.child_count = total_children
        parent.completed_children = completed_children
        parent.total_questions = total_questions
        parent.processed_questions = processed_questions
        parent.correct_count = correct_count

        if total_questions > 0:
            parent.accuracy = correct_count / total_questions
            parent.progress_percent = int((processed_questions / total_questions) * 100)

        # Update status
        if completed_children == total_children:
            # All children completed
            failed_children = sum(1 for c in children if c.status == "failed")
            if failed_children == total_children:
                parent.status = "failed"
            else:
                parent.status = "completed"
            parent.completed_at = datetime.utcnow()
        elif completed_children > 0:
            parent.status = "running"

        parent.updated_at = datetime.utcnow()
        await db.commit()

        logger.info(
            f"Updated parent {parent_id} stats: "
            f"{completed_children}/{total_children} children, "
            f"{processed_questions}/{total_questions} questions, "
            f"accuracy={parent.accuracy:.2%}"
        )

    @staticmethod
    async def update_parent_on_child_complete(
        db: AsyncSession,
        parent_id: int,
    ) -> None:
        """Update parent task statistics when a child task completes or fails.

        This method is called automatically when a child task's status changes
        to "completed" or "failed". It recalculates the parent task's statistics
        based on all child tasks.

        Args:
            db: Database session.
            parent_id: Parent task ID.

        Example:
            >>> # Called automatically when child task completes
            >>> await EvalTaskService.update_parent_on_child_complete(db, parent_id=100)
        """
        logger.info(f"Updating parent {parent_id} stats due to child completion")
        await EvalTaskService.update_parent_stats(db, parent_id)

    @staticmethod
    async def get_child_tasks(
        db: AsyncSession,
        parent_id: int,
        user_id: int,
    ) -> List[EvalTask]:
        """Get all child tasks for a parent task.

        Args:
            db: Database session.
            parent_id: Parent task ID.
            user_id: User ID for access control.

        Returns:
            List of child EvalTask objects.
        """
        # First verify parent belongs to user
        result = await db.execute(
            select(EvalTask).where(
                EvalTask.id == parent_id,
                EvalTask.user_id == user_id,
            )
        )
        parent = result.scalar_one_or_none()

        if not parent:
            return []

        # Get child tasks
        result = await db.execute(
            select(EvalTask).where(
                EvalTask.parent_id == parent_id,
            ).order_by(EvalTask.id)
        )
        return list(result.scalars().all())
