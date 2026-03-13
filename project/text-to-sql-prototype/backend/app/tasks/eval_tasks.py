"""Background evaluation tasks for running model evaluations."""
import json
from typing import Any, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
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
from app.services.nl2sql import generate_sql
from app.services.schema import SchemaService

logger = get_logger(__name__)

# Global flag for cancellation tracking
_cancelled_tasks: set = set()


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
) -> None:
    """Run evaluation task in background.

    Args:
        task_id: Evaluation task ID.
        user_id: User ID.
        connection_id: Database connection ID.
        dataset_path: Path to evaluation dataset.
        provider: LLM provider.
        model_config: Model configuration.
        eval_mode: Evaluation mode (greedy_search or majority_vote).
        vote_count: Number of votes for majority voting.
        api_key: The decrypted API key.
        format_type: The format type for LLM client selection.
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
            await _run_evaluation(
                db=db,
                task_id=task_id,
                user_id=user_id,
                connection_id=connection_id,
                dataset_path=dataset_path,
                provider=provider,
                model_config=model_config,
                eval_mode=eval_mode,
                vote_count=vote_count,
                api_key=api_key,
                format_type=format_type,
            )
        except Exception as e:
            logger.error(f"Evaluation task {task_id} failed: {e}")
            task = await EvalTaskService.get_eval_task(db, task_id, user_id)
            if task:
                await EvalTaskService.fail_eval_task(db, task, str(e))
        finally:
            remove_cancelled_task(task_id)
            await engine.dispose()


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
) -> None:
    """Internal evaluation runner.

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
    """
    # Get task
    task = await EvalTaskService.get_eval_task(db, task_id, user_id)
    if not task:
        raise ValueError(f"Task {task_id} not found")

    # Load dataset
    try:
        dataset = load_dataset(dataset_path)
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
            DBConnection.id == connection_id,
            DBConnection.user_id == user_id,
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
            if is_task_cancelled(task_id):
                logger.info(f"Task {task_id} cancelled")
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

            try:
                # Generate SQL based on eval mode
                if eval_mode == "majority_vote":
                    # Generate multiple SQLs and vote
                    pred_sqls = []
                    for _ in range(vote_count):
                        sql = await generate_sql(
                            question=nl_question,
                            schema_text=schema_text,
                            provider=provider,
                            model_config=model_config,
                            dialect=connection.db_type,
                            api_key=api_key,
                            format_type=format_type,
            
                        )
                        pred_sqls.append(sql)

                    # Perform majority voting
                    predicted_sql, voting_info = await MajorityVoter.majority_voting(
                        engine=eval_engine,
                        pred_sqls=pred_sqls,
                        timeout=30,
                    )
                else:
                    # Greedy search: single generation
                    predicted_sql = await generate_sql(
                        question=nl_question,
                        schema_text=schema_text,
                        provider=provider,
                        model_config=model_config,
                        dialect=connection.db_type,
                        api_key=api_key,
                        format_type=format_type,
        
                    )

                # Compare results using EXCEPT
                is_correct, compare_error = await SQLEvaluator.compare_sql_results_except(
                    engine=eval_engine,
                    pred_sql=predicted_sql,
                    gold_sql=gold_sql,
                    timeout=30,
                )

                # Determine error type
                error_type = None
                error_message = None

                if not is_correct:
                    if compare_error:
                        error_message = compare_error
                        error_type = determine_error_type(
                            execution_success="error" not in compare_error.lower(),
                            is_correct=False,
                            execution_error=compare_error,
                        )
                    else:
                        error_type = "wrong_result"
                        error_message = "Results do not match"

                if is_correct:
                    correct_count += 1

                # Create result record
                await EvalTaskService.create_eval_result(
                    db=db,
                    task_id=task_id,
                    question_id=question_id,
                    nl_question=nl_question,
                    gold_sql=gold_sql,
                    predicted_sql=predicted_sql,
                    is_correct=is_correct,
                    error_type=error_type,
                    error_message=error_message,
                    db_id=db_id,
                )

            except Exception as e:
                logger.error(f"Error processing question {question_id}: {e}")

                # Create error result
                await EvalTaskService.create_eval_result(
                    db=db,
                    task_id=task_id,
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
            f"Completed evaluation task {task_id}: "
            f"{correct_count}/{total_questions} correct "
            f"({correct_count/total_questions*100:.1f}%)"
        )

    except Exception as e:
        logger.error(f"Evaluation error: {e}")
        await EvalTaskService.fail_eval_task(db, task, str(e))

    finally:
        await eval_engine.dispose()
