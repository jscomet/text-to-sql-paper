"""Background evaluation tasks for running model evaluations."""
import json
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.database import get_async_database_url
from app.core.logging import get_logger
from app.services.connection import ConnectionService
from app.services.eval_task import EvalTaskService
from app.services.evaluator import (
    SQLEvaluator,
    MajorityVoter,
    determine_error_type,
)
from app.services.nl2sql import (
    generate_sql,
    generate_sql_pass_at_k,
    generate_sql_with_check_correct,
)
from app.services.schema import SchemaService
from app.websocket.progress import (
    ProgressEventType,
    broadcast_progress_update,
    notify_candidate_generation_progress,
    notify_correction_iteration_progress,
    notify_question_started,
    notify_task_completed,
    notify_task_started,
)

logger = get_logger(__name__)

# Global flag for cancellation tracking
_cancelled_tasks: set = set()

# Progress callback registry for real-time updates
_progress_callbacks: Dict[int, List[Callable]] = {}


def register_progress_callback(task_id: int, callback: Callable) -> None:
    """Register a progress callback for a task.

    Args:
        task_id: Task ID.
        callback: Callback function to receive progress updates.
    """
    if task_id not in _progress_callbacks:
        _progress_callbacks[task_id] = []
    _progress_callbacks[task_id].append(callback)


def unregister_progress_callback(task_id: int, callback: Callable) -> None:
    """Unregister a progress callback.

    Args:
        task_id: Task ID.
        callback: Callback function to remove.
    """
    if task_id in _progress_callbacks:
        _progress_callbacks[task_id] = [
            cb for cb in _progress_callbacks[task_id] if cb != callback
        ]


def notify_progress(task_id: int, progress_data: Dict[str, Any]) -> None:
    """Notify all registered callbacks of progress update.

    Args:
        task_id: Task ID.
        progress_data: Progress update data.
    """
    if task_id in _progress_callbacks:
        for callback in _progress_callbacks[task_id]:
            try:
                callback(progress_data)
            except Exception as e:
                logger.warning(f"Progress callback failed for task {task_id}: {e}")


def load_dataset(dataset_path: str) -> List[Dict[str, Any]]:
    """Load evaluation dataset from JSON file.

    Expected format:
    [
        {
            "question_id": "1",
            "question": "What is the total sales?",
            "SQL": "SELECT SUM(sales) FROM orders",
            "db_id": "database_name"
        }
    ]

    Args:
        dataset_path: Path to dataset JSON file.

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


def is_task_cancelled(task_id: int) -> bool:
    """Check if a task has been cancelled.

    Args:
        task_id: Task ID.

    Returns:
        True if task is cancelled.
    """
    return task_id in _cancelled_tasks


def cancel_task(task_id: int) -> None:
    """Mark a task as cancelled.

    Args:
        task_id: Task ID.
    """
    _cancelled_tasks.add(task_id)


def remove_cancelled_task(task_id: int) -> None:
    """Remove task from cancelled set.

    Args:
        task_id: Task ID.
    """
    _cancelled_tasks.discard(task_id)


class InferenceExecutor(ABC):
    """Abstract base class for inference mode executors.

    Each executor handles a specific inference mode (greedy_search, sampling, check_correct).
    """

    def __init__(
        self,
        task_id: int,
        provider: str,
        model_config: Dict[str, Any],
        api_key: Optional[str] = None,
        format_type: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.task_id = task_id
        self.provider = provider
        self.model_config = model_config
        self.api_key = api_key
        self.format_type = format_type
        self.base_url = base_url

    @abstractmethod
    async def execute(
        self,
        question: str,
        schema_text: str,
        gold_sql: str,
        engine: AsyncEngine,
        dialect: str,
    ) -> Dict[str, Any]:
        """Execute inference for a single question.

        Args:
            question: Natural language question.
            schema_text: Database schema text.
            gold_sql: Gold/reference SQL.
            engine: Database engine for execution.
            dialect: SQL dialect.

        Returns:
            Dictionary containing:
            - predicted_sql: The selected/predicted SQL
            - is_correct: Whether the prediction is correct
            - error_type: Type of error if failed
            - error_message: Error message if failed
            - candidate_sqls: List of candidates (for pass_at_k)
            - iteration_count: Number of iterations (for check_correct)
            - correction_history: Correction history (for check_correct)
            - confidence_score: Confidence score
        """
        pass

    def report_progress(self, progress_data: Dict[str, Any]) -> None:
        """Report progress update.

        Args:
            progress_data: Progress data to report.
        """
        notify_progress(self.task_id, progress_data)


class GreedySearchExecutor(InferenceExecutor):
    """Executor for greedy search inference mode.

    Uses temperature=0 for deterministic single generation.
    """

    async def execute(
        self,
        question: str,
        schema_text: str,
        gold_sql: str,
        engine: AsyncEngine,
        dialect: str,
    ) -> Dict[str, Any]:
        """Execute greedy search inference.

        Args:
            question: Natural language question.
            schema_text: Database schema text.
            gold_sql: Gold/reference SQL.
            engine: Database engine for execution.
            dialect: SQL dialect.

        Returns:
            Execution result dictionary.
        """
        # Use temperature=0 for deterministic generation
        config = self.model_config.copy()
        config["temperature"] = 0.0

        predicted_sql = await generate_sql(
            question=question,
            schema_text=schema_text,
            provider=self.provider,
            model_config=config,
            dialect=dialect,
            api_key=self.api_key,
            format_type=self.format_type,
            base_url=self.base_url,
        )

        # Compare with gold SQL
        is_correct, error_msg = await SQLEvaluator.compare_sql_results_except(
            engine=engine,
            pred_sql=predicted_sql,
            gold_sql=gold_sql,
            timeout=30,
        )

        # Determine error type
        error_type = None
        if not is_correct:
            error_type = determine_error_type(
                execution_success="error" not in error_msg.lower() if error_msg else True,
                is_correct=False,
                execution_error=error_msg,
            )

        return {
            "predicted_sql": predicted_sql,
            "is_correct": is_correct,
            "error_type": error_type,
            "error_message": error_msg,
            "candidate_sqls": None,
            "iteration_count": None,
            "correction_history": None,
            "confidence_score": 0.9 if is_correct else 0.5,
        }


class SamplingExecutor(InferenceExecutor):
    """Executor for sampling inference mode (Pass@K).

    Generates K candidates using sampling (temperature > 0) and evaluates them.
    """

    def __init__(
        self,
        task_id: int,
        provider: str,
        model_config: Dict[str, Any],
        api_key: Optional[str] = None,
        format_type: Optional[str] = None,
        base_url: Optional[str] = None,
        sampling_count: int = 8,
        temperature: float = 0.7,
        use_majority_vote: bool = False,
    ):
        super().__init__(task_id, provider, model_config, api_key, format_type, base_url)
        self.sampling_count = sampling_count
        self.temperature = temperature
        self.use_majority_vote = use_majority_vote

    async def execute(
        self,
        question: str,
        schema_text: str,
        gold_sql: str,
        engine: AsyncEngine,
        dialect: str,
    ) -> Dict[str, Any]:
        """Execute sampling inference with Pass@K evaluation.

        Args:
            question: Natural language question.
            schema_text: Database schema text.
            gold_sql: Gold/reference SQL.
            engine: Database engine for execution.
            dialect: SQL dialect.

        Returns:
            Execution result dictionary with Pass@K metrics.
        """
        # Generate K candidates using Pass@K evaluator
        result = await generate_sql_pass_at_k(
            question=question,
            schema_text=schema_text,
            engine=engine,
            k=self.sampling_count,
            provider=self.provider,
            model_config=self.model_config,
            dialect=dialect,
            api_key=self.api_key,
            format_type=self.format_type,
            base_url=self.base_url,
            temperature=self.temperature,
            use_majority_vote=self.use_majority_vote,
        )

        if not result["success"]:
            return {
                "predicted_sql": None,
                "is_correct": False,
                "error_type": "generation_error",
                "error_message": result.get("error_message", "Pass@K generation failed"),
                "candidate_sqls": result.get("candidates", []),
                "iteration_count": None,
                "correction_history": None,
                "confidence_score": 0.0,
            }

        # Get the selected SQL and evaluate correctness
        predicted_sql = result["sql"]

        # Compare with gold SQL
        is_correct, error_msg = await SQLEvaluator.compare_sql_results_except(
            engine=engine,
            pred_sql=predicted_sql,
            gold_sql=gold_sql,
            timeout=30,
        )

        # Calculate Pass@K metrics
        candidates = result.get("candidates", [])
        metrics = result.get("metrics", {})

        # Build candidate SQLs list for storage
        candidate_sqls = [
            {
                "sql": c.get("sql", ""),
                "is_valid": c.get("execution_success", False),
                "is_correct": c.get("is_correct", False),
                "error_type": c.get("error_type"),
                "error_message": c.get("error_message"),
            }
            for c in candidates
        ]

        # Calculate confidence based on pass@k rate
        pass_at_k = metrics.get("pass_at_k", 0.0)
        confidence = pass_at_k

        # Determine error type
        error_type = None
        if not is_correct:
            error_type = determine_error_type(
                execution_success="error" not in error_msg.lower() if error_msg else True,
                is_correct=False,
                execution_error=error_msg,
            )

        return {
            "predicted_sql": predicted_sql,
            "is_correct": is_correct,
            "error_type": error_type,
            "error_message": error_msg,
            "candidate_sqls": candidate_sqls,
            "iteration_count": None,
            "correction_history": None,
            "confidence_score": confidence,
            "pass_at_k_metrics": metrics,
        }


class CheckCorrectExecutor(InferenceExecutor):
    """Executor for check-correct inference mode.

    Uses iterative Generator-Checker-Corrector pipeline for self-correction.
    """

    def __init__(
        self,
        task_id: int,
        provider: str,
        model_config: Dict[str, Any],
        api_key: Optional[str] = None,
        format_type: Optional[str] = None,
        base_url: Optional[str] = None,
        max_iterations: int = 3,
        correction_strategy: str = "self_correction",
    ):
        super().__init__(task_id, provider, model_config, api_key, format_type, base_url)
        self.max_iterations = max_iterations
        self.correction_strategy = correction_strategy

    async def execute(
        self,
        question: str,
        schema_text: str,
        gold_sql: str,
        engine: AsyncEngine,
        dialect: str,
    ) -> Dict[str, Any]:
        """Execute check-correct inference with iterative correction.

        Args:
            question: Natural language question.
            schema_text: Database schema text.
            gold_sql: Gold/reference SQL.
            engine: Database engine for execution.
            dialect: SQL dialect.

        Returns:
            Execution result dictionary with correction history.
        """
        # Use generate_sql_with_check_correct for iterative correction
        result = await generate_sql_with_check_correct(
            question=question,
            schema_text=schema_text,
            engine=engine,
            provider=self.provider,
            model_config=self.model_config,
            dialect=dialect,
            api_key=self.api_key,
            format_type=self.format_type,
            base_url=self.base_url,
            max_iterations=self.max_iterations,
        )

        predicted_sql = result.get("sql")
        correction_history = result.get("correction_history", [])
        iteration_count = result.get("iteration_count", 0)

        if not predicted_sql:
            return {
                "predicted_sql": None,
                "is_correct": False,
                "error_type": "generation_error",
                "error_message": result.get("error_message", "Check-Correct generation failed"),
                "candidate_sqls": None,
                "iteration_count": iteration_count,
                "correction_history": correction_history,
                "confidence_score": 0.0,
            }

        # Compare with gold SQL
        is_correct, error_msg = await SQLEvaluator.compare_sql_results_except(
            engine=engine,
            pred_sql=predicted_sql,
            gold_sql=gold_sql,
            timeout=30,
        )

        # Calculate confidence based on iteration count and success
        if is_correct:
            # Higher confidence if corrected in fewer iterations
            confidence = max(0.7, 1.0 - ((iteration_count - 1) * 0.1))
        else:
            confidence = max(0.3, 0.5 - (iteration_count * 0.1))

        # Determine error type
        error_type = None
        if not is_correct:
            error_type = determine_error_type(
                execution_success="error" not in error_msg.lower() if error_msg else True,
                is_correct=False,
                execution_error=error_msg,
            )

        return {
            "predicted_sql": predicted_sql,
            "is_correct": is_correct,
            "error_type": error_type,
            "error_message": error_msg,
            "candidate_sqls": None,
            "iteration_count": iteration_count,
            "correction_history": correction_history,
            "confidence_score": confidence,
        }


class EvalTaskRunner:
    """Evaluation task runner with mode dispatching.

    Supports multiple inference modes:
    - greedy_search: Single deterministic generation
    - sampling: Pass@K sampling with majority voting
    - check_correct: Iterative self-correction
    """

    # Registry of inference mode executors
    EXECUTORS = {
        "greedy_search": GreedySearchExecutor,
        "sampling": SamplingExecutor,
        "pass_at_k": SamplingExecutor,  # Alias for sampling
        "check_correct": CheckCorrectExecutor,
    }

    def __init__(
        self,
        task_id: int,
        user_id: int,
        connection_id: int,
        dataset_path: str,
        provider: str,
        model_config: Dict[str, Any],
        inference_mode: str = "greedy_search",
        api_key: Optional[str] = None,
        format_type: Optional[str] = None,
        base_url: Optional[str] = None,
        # Advanced inference parameters
        sampling_count: Optional[int] = None,
        max_iterations: Optional[int] = None,
        correction_strategy: Optional[str] = None,
        sampling_config: Optional[Dict[str, Any]] = None,
        correction_config: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the task runner.

        Args:
            task_id: Evaluation task ID.
            user_id: User ID.
            connection_id: Database connection ID.
            dataset_path: Path to evaluation dataset.
            provider: LLM provider.
            model_config: Model configuration.
            inference_mode: Inference mode (greedy_search/sampling/check_correct).
            api_key: API key for LLM.
            format_type: Format type for LLM client.
            base_url: Optional base URL for API.
            sampling_count: Number of samples for sampling mode.
            max_iterations: Max iterations for check_correct mode.
            correction_strategy: Correction strategy for check_correct mode.
            sampling_config: Additional sampling configuration.
            correction_config: Additional correction configuration.
        """
        self.task_id = task_id
        self.user_id = user_id
        self.connection_id = connection_id
        self.dataset_path = dataset_path
        self.provider = provider
        self.model_config = model_config
        self.inference_mode = inference_mode
        self.api_key = api_key
        self.format_type = format_type
        self.base_url = base_url
        self.sampling_count = sampling_count or 8
        self.max_iterations = max_iterations or 3
        self.correction_strategy = correction_strategy or "self_correction"
        self.sampling_config = sampling_config or {}
        self.correction_config = correction_config or {}

        # Initialize executor based on inference mode
        self.executor = self._create_executor()

    def _create_executor(self) -> InferenceExecutor:
        """Create the appropriate executor based on inference mode.

        Returns:
            Configured InferenceExecutor instance.

        Raises:
            ValueError: If inference mode is not supported.
        """
        executor_class = self.EXECUTORS.get(self.inference_mode)
        if not executor_class:
            raise ValueError(
                f"Unsupported inference mode: {self.inference_mode}. "
                f"Supported modes: {list(self.EXECUTORS.keys())}"
            )

        # Create executor with mode-specific parameters
        if self.inference_mode in ("sampling", "pass_at_k"):
            temperature = self.sampling_config.get("temperature", 0.7)
            use_majority_vote = self.sampling_config.get("use_majority_vote", False)
            return SamplingExecutor(
                task_id=self.task_id,
                provider=self.provider,
                model_config=self.model_config,
                api_key=self.api_key,
                format_type=self.format_type,
                base_url=self.base_url,
                sampling_count=self.sampling_count,
                temperature=temperature,
                use_majority_vote=use_majority_vote,
            )
        elif self.inference_mode == "check_correct":
            return CheckCorrectExecutor(
                task_id=self.task_id,
                provider=self.provider,
                model_config=self.model_config,
                api_key=self.api_key,
                format_type=self.format_type,
                base_url=self.base_url,
                max_iterations=self.max_iterations,
                correction_strategy=self.correction_strategy,
            )
        else:  # greedy_search
            return GreedySearchExecutor(
                task_id=self.task_id,
                provider=self.provider,
                model_config=self.model_config,
                api_key=self.api_key,
                format_type=self.format_type,
                base_url=self.base_url,
            )

    async def run(
        self,
        db: AsyncSession,
        progress_callback: Optional[Callable] = None,
    ) -> None:
        """Run the evaluation task.

        Args:
            db: Database session.
            progress_callback: Optional callback for progress updates.
        """
        # Register progress callback if provided
        if progress_callback:
            register_progress_callback(self.task_id, progress_callback)

        try:
            await self._run_evaluation(db)
        finally:
            if progress_callback:
                unregister_progress_callback(self.task_id, progress_callback)

    async def _run_evaluation(self, db: AsyncSession) -> None:
        """Internal evaluation runner.

        Args:
            db: Database session.
        """
        # Get task
        task = await EvalTaskService.get_eval_task(db, self.task_id, self.user_id)
        if not task:
            raise ValueError(f"Task {self.task_id} not found")

        # Load dataset
        try:
            dataset = load_dataset(self.dataset_path)
        except Exception as e:
            await EvalTaskService.fail_eval_task(db, task, f"Failed to load dataset: {e}")
            return

        total_questions = len(dataset)
        if total_questions == 0:
            await EvalTaskService.fail_eval_task(db, task, "Empty dataset")
            return

        # Get database connection
        from app.models.db_connection import DBConnection
        from sqlalchemy import select

        result = await db.execute(
            select(DBConnection).where(
                DBConnection.id == self.connection_id,
                DBConnection.user_id == self.user_id,
            )
        )
        connection = result.scalar_one_or_none()

        if not connection:
            await EvalTaskService.fail_eval_task(db, task, "Database connection not found")
            return

        # Create database engine for evaluation
        eval_engine = ConnectionService.get_async_engine(connection)

        # Get schema
        schema_service = SchemaService()
        try:
            tables = await schema_service.get_all_schemas(eval_engine)
            schema_text = SchemaService.build_schema_text(tables)
        except Exception as e:
            await EvalTaskService.fail_eval_task(db, task, f"Failed to get schema: {e}")
            return

        # Mark task as running
        await EvalTaskService.start_eval_task(db, task)

        # Track results
        correct_count = 0
        processed_count = 0

        try:
            for idx, item in enumerate(dataset):
                # Check for cancellation
                if is_task_cancelled(self.task_id):
                    logger.info(f"Task {self.task_id} cancelled")
                    await EvalTaskService.cancel_eval_task(db, task)
                    return

                # Extract question data
                question_id = str(item.get("question_id", idx + 1))
                nl_question = item.get("question", item.get("NL", ""))
                gold_sql = item.get("SQL", item.get("query", ""))
                db_id = item.get("db_id", connection.database)

                if not nl_question or not gold_sql:
                    logger.warning(f"Skipping item {question_id}: missing question or SQL")
                    continue

                # Report current question progress
                await self._report_question_progress(
                    processed_count, total_questions, correct_count,
                    question_id, nl_question
                )

                try:
                    # Execute inference using the configured executor
                    result = await self.executor.execute(
                        question=nl_question,
                        schema_text=schema_text,
                        gold_sql=gold_sql,
                        engine=eval_engine,
                        dialect=connection.db_type,
                    )

                    # Update correct count
                    if result["is_correct"]:
                        correct_count += 1

                    # Create result record
                    await EvalTaskService.create_eval_result(
                        db=db,
                        task_id=self.task_id,
                        question_id=question_id,
                        nl_question=nl_question,
                        gold_sql=gold_sql,
                        predicted_sql=result["predicted_sql"],
                        is_correct=result["is_correct"],
                        error_type=result.get("error_type"),
                        error_message=result.get("error_message"),
                        db_id=db_id,
                        candidate_sqls=result.get("candidate_sqls"),
                        iteration_count=result.get("iteration_count"),
                        correction_history=result.get("correction_history"),
                        confidence_score=result.get("confidence_score"),
                    )

                except Exception as e:
                    logger.error(f"Error processing question {question_id}: {e}")

                    # Create error result
                    await EvalTaskService.create_eval_result(
                        db=db,
                        task_id=self.task_id,
                        question_id=question_id,
                        nl_question=nl_question,
                        gold_sql=gold_sql,
                        predicted_sql=None,
                        is_correct=False,
                        error_type="generation_error",
                        error_message=str(e),
                        db_id=db_id,
                    )

                # Update progress
                processed_count += 1
                await EvalTaskService.update_task_progress(
                    db=db,
                    task=task,
                    processed=processed_count,
                    total=total_questions,
                    correct=correct_count,
                )

            # Mark task as completed
            await EvalTaskService.complete_eval_task(
                db=db,
                task=task,
                correct_count=correct_count,
                total_count=total_questions,
            )

            logger.info(
                f"Completed evaluation task {self.task_id}: "
                f"{correct_count}/{total_questions} correct "
                f"({correct_count/total_questions*100:.1f}%)"
            )

        except Exception as e:
            logger.error(f"Evaluation error: {e}")
            await EvalTaskService.fail_eval_task(db, task, str(e))

        finally:
            await eval_engine.dispose()

    async def _report_question_progress(
        self,
        processed: int,
        total: int,
        correct: int,
        question_id: str,
        question: str,
    ) -> None:
        """Report progress for current question.

        Args:
            processed: Number of processed questions.
            total: Total number of questions.
            correct: Number of correct predictions.
            question_id: Current question ID.
            question: Current question text.
        """
        progress_data = {
            "task_id": self.task_id,
            "processed": processed,
            "total": total,
            "correct": correct,
            "accuracy": correct / total if total > 0 else 0.0,
            "progress_percent": int((processed / total) * 100) if total > 0 else 0,
            "current_question_id": question_id,
            "current_question": question,
            "inference_mode": self.inference_mode,
        }
        notify_progress(self.task_id, progress_data)


async def report_detailed_progress(
    task_id: int,
    db: AsyncSession,
    task: Any,
    processed: int,
    total: int,
    correct: int,
    current_question: Optional[str] = None,
    current_mode: Optional[str] = None,
    sub_progress: Optional[Dict[str, Any]] = None,
) -> None:
    """Report detailed progress with sub-task information.

    Args:
        task_id: Task ID.
        db: Database session.
        task: EvalTask object.
        processed: Number of processed questions.
        total: Total number of questions.
        correct: Number of correct predictions.
        current_question: Current question being processed.
        current_mode: Current evaluation mode.
        sub_progress: Sub-task progress information.
    """
    # Update database progress
    await EvalTaskService.update_task_progress(
        db=db,
        task=task,
        processed=processed,
        total=total,
        correct=correct,
    )

    # Build detailed progress data
    progress_data = {
        "task_id": task_id,
        "processed": processed,
        "total": total,
        "correct": correct,
        "accuracy": correct / total if total > 0 else 0.0,
        "progress_percent": int((processed / total) * 100) if total > 0 else 0,
        "current_question": current_question,
        "current_mode": current_mode,
        "sub_progress": sub_progress,
    }

    # Notify registered callbacks
    notify_progress(task_id, progress_data)

    logger.debug(
        f"Task {task_id} progress: {processed}/{total} "
        f"({progress_data['progress_percent']}%), "
        f"correct: {correct}, "
        f"mode: {current_mode}"
    )


async def run_evaluation_task(
    task_id: int,
    user_id: int,
    connection_id: int,
    dataset_path: str,
    provider: str,
    model_config: Dict[str, Any],
    eval_mode: str = "greedy_search",
    vote_count: int = 5,
    api_key: str = None,
    format_type: str = None,
    base_url: Optional[str] = None,
    # Advanced inference parameters
    sampling_count: Optional[int] = None,
    max_iterations: Optional[int] = None,
    correction_strategy: Optional[str] = None,
    sampling_config: Optional[Dict[str, Any]] = None,
    correction_config: Optional[Dict[str, Any]] = None,
) -> None:
    """Run evaluation task in background.

    This is the main entry point for running evaluation tasks.
    It creates an EvalTaskRunner and executes the evaluation.

    Args:
        task_id: Evaluation task ID.
        user_id: User ID.
        connection_id: Database connection ID.
        dataset_path: Path to evaluation dataset.
        provider: LLM provider.
        model_config: Model configuration.
        eval_mode: Evaluation mode (greedy_search/sampling/check_correct).
        vote_count: Number of votes for majority voting (deprecated, use sampling_config).
        api_key: The decrypted API key.
        format_type: The format type for LLM client selection.
        base_url: Optional base URL for API.
        sampling_count: Number of samples for sampling mode.
        max_iterations: Max iterations for check_correct mode.
        correction_strategy: Correction strategy for check_correct mode.
        sampling_config: Additional sampling configuration.
        correction_config: Additional correction configuration.
    """
    # Create async database engine and session
    engine = create_async_engine(
        get_async_database_url(settings.database_url),
        echo=False,
        future=True,
    )

    AsyncSessionLocal = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )

    async with AsyncSessionLocal() as db:
        try:
            # Create task runner with new architecture
            runner = EvalTaskRunner(
                task_id=task_id,
                user_id=user_id,
                connection_id=connection_id,
                dataset_path=dataset_path,
                provider=provider,
                model_config=model_config,
                inference_mode=eval_mode,
                api_key=api_key,
                format_type=format_type,
                base_url=base_url,
                sampling_count=sampling_count,
                max_iterations=max_iterations,
                correction_strategy=correction_strategy,
                sampling_config=sampling_config,
                correction_config=correction_config,
            )

            # Run evaluation
            await runner.run(db)

        except Exception as e:
            logger.error(f"Evaluation task {task_id} failed: {e}")
            task = await EvalTaskService.get_eval_task(db, task_id, user_id)
            if task:
                await EvalTaskService.fail_eval_task(db, task, str(e))
        finally:
            remove_cancelled_task(task_id)
            await engine.dispose()


# Legacy function for backward compatibility
async def _run_evaluation(
    db: AsyncSession,
    task_id: int,
    user_id: int,
    connection_id: int,
    dataset_path: str,
    provider: str,
    model_config: Dict[str, Any],
    eval_mode: str,
    vote_count: int,
    api_key: str = None,
    format_type: str = None,
    base_url: Optional[str] = None,
    sampling_count: Optional[int] = None,
    max_iterations: Optional[int] = None,
    correction_strategy: Optional[str] = None,
    sampling_config: Optional[Dict[str, Any]] = None,
    correction_config: Optional[Dict[str, Any]] = None,
) -> None:
    """Legacy internal evaluation runner.

    This function is kept for backward compatibility.
    New code should use EvalTaskRunner directly.

    Args:
        db: Database session.
        task_id: Task ID.
        user_id: User ID.
        connection_id: Connection ID.
        dataset_path: Dataset path.
        provider: LLM provider.
        model_config: Model configuration.
        eval_mode: Evaluation mode.
        vote_count: Vote count for majority voting.
        api_key: The decrypted API key.
        format_type: The format type for LLM client selection.
        base_url: Optional base URL for API.
        sampling_count: Number of samples for pass_at_k mode.
        max_iterations: Max iterations for check_correct mode.
        correction_strategy: Correction strategy for check_correct mode.
        sampling_config: Additional sampling configuration.
        correction_config: Additional correction configuration.
    """
    # Create runner and run
    runner = EvalTaskRunner(
        task_id=task_id,
        user_id=user_id,
        connection_id=connection_id,
        dataset_path=dataset_path,
        provider=provider,
        model_config=model_config,
        inference_mode=eval_mode,
        api_key=api_key,
        format_type=format_type,
        base_url=base_url,
        sampling_count=sampling_count,
        max_iterations=max_iterations,
        correction_strategy=correction_strategy,
        sampling_config=sampling_config,
        correction_config=correction_config,
    )
    await runner.run(db)


# Task #31: Check-Correct Evaluation Implementation
async def _run_check_correct_evaluation(
    task_id: int,
    question: str,
    schema_text: str,
    gold_sql: str,
    engine: AsyncEngine,
    dialect: str,
    provider: str,
    model_config: Dict[str, Any],
    api_key: Optional[str] = None,
    format_type: Optional[str] = None,
    base_url: Optional[str] = None,
    max_iterations: int = 3,
    correction_strategy: str = "self_correction",
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
) -> Dict[str, Any]:
    """Run Check-Correct evaluation for a single question.

    This function implements Task #31: Check-Correct evaluation task execution.
    It iteratively generates SQL, checks for errors, corrects them, and returns
    detailed results including correction history.

    Args:
        task_id: Task ID for progress reporting.
        question: Natural language question.
        schema_text: Database schema text.
        gold_sql: Gold/reference SQL.
        engine: Database engine for execution.
        dialect: SQL dialect.
        provider: LLM provider.
        model_config: Model configuration.
        api_key: API key for LLM.
        format_type: Format type for LLM client.
        base_url: Optional base URL for API.
        max_iterations: Maximum correction iterations.
        correction_strategy: Correction strategy (self_correction, etc.).
        progress_callback: Callback(current_iteration, max_iterations, status) for progress.

    Returns:
        Dictionary containing:
        - predicted_sql: The final SQL (corrected or last attempt)
        - is_correct: Whether the final SQL is correct
        - iteration_count: Number of iterations performed
        - correction_history: List of correction attempts with details
        - confidence_score: Confidence based on iteration success
        - error_message: Error message if failed
    """
    logger.debug(f"Task {task_id}: Starting Check-Correct evaluation with max_iterations={max_iterations}")

    try:
        # Report initial progress
        if progress_callback:
            progress_callback(0, max_iterations, "starting")

        # Use generate_sql_with_check_correct for iterative correction
        result = await generate_sql_with_check_correct(
            question=question,
            schema_text=schema_text,
            engine=engine,
            provider=provider,
            model_config=model_config,
            dialect=dialect,
            api_key=api_key,
            format_type=format_type,
            base_url=base_url,
            max_iterations=max_iterations,
        )

        predicted_sql = result.get("sql")
        correction_history = result.get("correction_history", [])
        iteration_count = result.get("iteration_count", 0)
        success = result.get("success", False)

        # Report generation progress
        for i, history_item in enumerate(correction_history):
            if progress_callback:
                status = "corrected" if history_item.get("success") else "correcting"
                progress_callback(i + 1, max_iterations, status)

            # Report sub-progress for WebSocket
            notify_progress(task_id, {
                "task_id": task_id,
                "check_correct_progress": {
                    "current_iteration": i + 1,
                    "max_iterations": max_iterations,
                    "current_sql": history_item.get("sql", "")[:100] + "..." if len(history_item.get("sql", "")) > 100 else history_item.get("sql", ""),
                    "error_type": history_item.get("error_type"),
                    "error_message": history_item.get("error_message"),
                    "success": history_item.get("success", False),
                },
            })

        if not predicted_sql:
            logger.warning(f"Task {task_id}: Check-Correct evaluation failed - no SQL generated")
            return {
                "predicted_sql": None,
                "is_correct": False,
                "iteration_count": iteration_count,
                "correction_history": correction_history,
                "confidence_score": 0.0,
                "error_message": result.get("error_message", "Check-Correct generation failed"),
            }

        # Compare with gold SQL
        is_correct, error_msg = await SQLEvaluator.compare_sql_results_except(
            engine=engine,
            pred_sql=predicted_sql,
            gold_sql=gold_sql,
            timeout=30,
        )

        # Calculate confidence based on iteration count and success
        if is_correct:
            # Higher confidence if corrected in fewer iterations
            confidence = max(0.7, 1.0 - ((iteration_count - 1) * 0.1))
        else:
            confidence = max(0.3, 0.5 - (iteration_count * 0.1))

        # Determine error type
        error_type = None
        if not is_correct:
            error_type = determine_error_type(
                execution_success="error" not in error_msg.lower() if error_msg else True,
                is_correct=False,
                execution_error=error_msg,
            )

        logger.debug(
            f"Task {task_id}: Check-Correct evaluation complete - "
            f"iterations={iteration_count}, is_correct={is_correct}, confidence={confidence:.2f}"
        )

        return {
            "predicted_sql": predicted_sql,
            "is_correct": is_correct,
            "iteration_count": iteration_count,
            "correction_history": correction_history,
            "confidence_score": confidence,
            "error_type": error_type,
            "error_message": error_msg if not is_correct else None,
            "correction_strategy": correction_strategy,
        }

    except Exception as e:
        logger.error(f"Task {task_id}: Check-Correct evaluation error - {e}")
        return {
            "predicted_sql": None,
            "is_correct": False,
            "iteration_count": 0,
            "correction_history": [],
            "confidence_score": 0.0,
            "error_message": str(e),
        }


# Task #14: Pass@K Evaluation Implementation
async def _run_pass_at_k_evaluation(
    task_id: int,
    question: str,
    schema_text: str,
    gold_sql: str,
    engine: AsyncEngine,
    dialect: str,
    provider: str,
    model_config: Dict[str, Any],
    api_key: Optional[str] = None,
    format_type: Optional[str] = None,
    base_url: Optional[str] = None,
    k: int = 8,
    temperature: float = 0.7,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> Dict[str, Any]:
    """Run Pass@K evaluation for a single question.

    This function implements Task #14: Pass@K evaluation task execution.
    It generates K candidates, evaluates each against gold SQL, and returns
    detailed results including Pass@K metrics.

    Args:
        task_id: Task ID for progress reporting.
        question: Natural language question.
        schema_text: Database schema text.
        gold_sql: Gold/reference SQL.
        engine: Database engine for execution.
        dialect: SQL dialect.
        provider: LLM provider.
        model_config: Model configuration.
        api_key: API key for LLM.
        format_type: Format type for LLM client.
        base_url: Optional base URL for API.
        k: Number of candidate SQLs to generate.
        temperature: Sampling temperature.
        progress_callback: Callback(current, total) for candidate generation progress.

    Returns:
        Dictionary containing:
        - predicted_sql: The selected SQL (first correct or best candidate)
        - is_correct: Whether any candidate was correct
        - candidate_results: List of candidate evaluation results
        - pass_at_k: Pass@K metric (1 if any correct, 0 otherwise)
        - correct_count: Number of correct candidates
        - confidence_score: Confidence based on correct ratio
    """
    from app.services.pass_at_k import PassAtKEvaluator
    from app.services.sql_checker import SQLChecker

    logger.debug(f"Task {task_id}: Starting Pass@K evaluation with k={k}")

    checker = SQLChecker()
    evaluator = PassAtKEvaluator(
        checker=checker,
        max_workers=4,
        timeout_seconds=30.0,
    )

    candidate_results = []
    correct_count = 0

    try:
        # Run Pass@K evaluation to generate candidates
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
            logger.warning(f"Task {task_id}: Pass@K evaluation failed - {result.error_message}")
            return {
                "predicted_sql": None,
                "is_correct": False,
                "candidate_results": [],
                "pass_at_k": 0.0,
                "correct_count": 0,
                "confidence_score": 0.0,
                "error_message": result.error_message or "Pass@K evaluation failed",
            }

        # Evaluate each candidate against gold SQL
        selected_sql = None
        first_correct_sql = None

        for i, candidate in enumerate(result.candidates):
            # Report progress: (i+1)/K
            if progress_callback:
                progress_callback(i + 1, k)

            # Compare with gold SQL
            is_correct, error_msg = await SQLEvaluator.compare_sql_results_except(
                engine=engine,
                pred_sql=candidate.sql,
                gold_sql=gold_sql,
                timeout=30,
            )

            # Track first correct SQL
            if is_correct and first_correct_sql is None:
                first_correct_sql = candidate.sql

            if is_correct:
                correct_count += 1

            # Build candidate result
            candidate_result = {
                "index": i,
                "sql": candidate.sql,
                "execution_success": candidate.execution_success,
                "is_correct": is_correct,
                "error_type": candidate.error_type.value if candidate.error_type else None,
                "error_message": error_msg if not is_correct else None,
                "execution_time_ms": candidate.execution_time_ms,
                "row_count": candidate.row_count,
            }
            candidate_results.append(candidate_result)

            # Report sub-progress for WebSocket
            notify_progress(task_id, {
                "task_id": task_id,
                "candidate_progress": {
                    "current": i + 1,
                    "total": k,
                    "current_sql": candidate.sql[:100] + "..." if len(candidate.sql) > 100 else candidate.sql,
                    "is_correct": is_correct,
                },
            })

        # Select predicted SQL: first correct or use majority vote
        if first_correct_sql:
            selected_sql = first_correct_sql
            is_correct = True
        elif result.metrics and result.metrics.majority_vote_sql:
            selected_sql = result.metrics.majority_vote_sql
            is_correct = False  # No candidate was actually correct
        elif result.candidates:
            selected_sql = result.candidates[0].sql
            is_correct = False
        else:
            selected_sql = None
            is_correct = False

        # Calculate Pass@K metric
        pass_at_k = 1.0 if correct_count > 0 else 0.0

        # Calculate confidence based on correct ratio
        confidence = correct_count / k if k > 0 else 0.0

        logger.debug(
            f"Task {task_id}: Pass@K evaluation complete - "
            f"correct={correct_count}/{k}, pass@k={pass_at_k:.2f}"
        )

        return {
            "predicted_sql": selected_sql,
            "is_correct": is_correct,
            "candidate_results": candidate_results,
            "pass_at_k": pass_at_k,
            "correct_count": correct_count,
            "confidence_score": confidence,
            "metrics": {
                "k": k,
                "pass_at_k": pass_at_k,
                "correct_count": correct_count,
                "executable_count": result.metrics.executable_count if result.metrics else 0,
                "total_count": result.metrics.total_count if result.metrics else k,
            },
        }

    except Exception as e:
        logger.error(f"Task {task_id}: Pass@K evaluation error - {e}")
        return {
            "predicted_sql": None,
            "is_correct": False,
            "candidate_results": candidate_results,
            "pass_at_k": 0.0,
            "correct_count": correct_count,
            "confidence_score": 0.0,
            "error_message": str(e),
        }
