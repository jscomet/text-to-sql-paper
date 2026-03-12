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
        model_config = {
            "provider": task_data.provider,
            "model": task_data.model,
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

        Returns:
            Created EvalResult object.
        """
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
