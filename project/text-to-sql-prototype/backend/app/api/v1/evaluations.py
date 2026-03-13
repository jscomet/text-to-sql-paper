"""Evaluation API routes for managing evaluation tasks."""
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.core.logging import get_logger
from app.models.eval_result import EvalResult
from app.models.eval_task import EvalTask
from app.models.user import User
from app.schemas.evaluation import (
    EvalProgressResponse,
    EvalResultListResponse,
    EvalResultResponse,
    EvalStatsResponse,
    EvalTaskCreate,
    EvalTaskListResponse,
    EvalTaskResponse,
    EvalTaskUpdate,
    PaginationInfo,
)
from app.api.v1.api_keys import get_user_api_key_by_id
from app.services.eval_task import EvalTaskService
from app.tasks.eval_tasks import run_evaluation_task

logger = get_logger(__name__)
router = APIRouter(prefix="/eval", tags=["Evaluations"])


@router.post("/tasks", response_model=EvalTaskResponse, status_code=status.HTTP_201_CREATED)
async def create_eval_task(
    request: EvalTaskCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> EvalTaskResponse:
    """Create a new evaluation task.

    Args:
        request: Task creation request.
        background_tasks: FastAPI background tasks.
        db: Database session.
        current_user: Current authenticated user.

    Returns:
        Created task details.
    """
    # Get API key configuration
    api_key_config = await get_user_api_key_by_id(
        user_id=current_user.id,
        key_id=request.api_key_id,
        db=db,
    )

    if not api_key_config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid API key ID",
        )

    # Build model config
    model_config = {
        "model": api_key_config["model"],
        "temperature": request.temperature,
        "max_tokens": request.max_tokens,
    }

    # Build advanced inference config based on eval_mode
    inference_config = {}
    if request.eval_mode == "pass_at_k":
        inference_config = {
            "sampling_count": request.sampling_count,
            "sampling_config": request.sampling_config or {},
        }
    elif request.eval_mode == "check_correct":
        inference_config = {
            "max_iterations": request.max_iterations,
            "correction_strategy": request.correction_strategy,
            "correction_config": request.correction_config or {},
        }
    elif request.eval_mode == "majority_vote":
        inference_config = {
            "vote_count": request.vote_count,
        }

    # Merge inference config into model_config for storage
    if inference_config:
        model_config["inference"] = inference_config

    # Create task data
    task_data = EvalTaskCreate(
        name=request.name,
        dataset_type=request.dataset_type,
        dataset_path=request.dataset_path,
        connection_id=request.connection_id,
        api_key_id=request.api_key_id,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        eval_mode=request.eval_mode,
        vote_count=request.vote_count,
    )

    # Create task
    task = await EvalTaskService.create_eval_task(
        db=db,
        user_id=current_user.id,
        task_data=task_data,
    )

    # Start background evaluation
    background_tasks.add_task(
        run_evaluation_task,
        task_id=task.id,
        user_id=current_user.id,
        connection_id=request.connection_id,
        dataset_path=request.dataset_path,
        provider=api_key_config["provider"],
        model_config=model_config,
        eval_mode=request.eval_mode,
        vote_count=request.vote_count,
        api_key=api_key_config["api_key"],
        format_type=api_key_config["format_type"],
        base_url=api_key_config.get("base_url"),
        # Advanced inference parameters
        sampling_count=request.sampling_count if request.eval_mode == "pass_at_k" else None,
        max_iterations=request.max_iterations if request.eval_mode == "check_correct" else None,
        correction_strategy=request.correction_strategy if request.eval_mode == "check_correct" else None,
        sampling_config=request.sampling_config,
        correction_config=request.correction_config,
    )

    logger.info(f"Created and started eval task {task.id} for user {current_user.id}")
    return EvalTaskResponse.model_validate(task)


@router.get("/tasks", response_model=EvalTaskListResponse)
async def list_eval_tasks(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=1000, description="Page size"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> EvalTaskListResponse:
    """List evaluation tasks for the current user.

    Args:
        page: Page number (1-indexed).
        page_size: Number of items per page.
        status: Optional status filter.
        db: Database session.
        current_user: Current authenticated user.

    Returns:
        List of evaluation tasks.
    """
    skip = (page - 1) * page_size

    # Get tasks
    tasks = await EvalTaskService.list_eval_tasks(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=page_size,
        status=status,
    )

    # Get total count
    count_query = select(func.count(EvalTask.id)).where(EvalTask.user_id == current_user.id)
    if status:
        count_query = count_query.where(EvalTask.status == status)

    result = await db.execute(count_query)
    total = result.scalar() or 0

    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

    return EvalTaskListResponse(
        list=[EvalTaskResponse.model_validate(t) for t in tasks],
        pagination=PaginationInfo(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
        ),
    )


@router.get("/tasks/{task_id}", response_model=EvalTaskResponse)
async def get_eval_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> EvalTaskResponse:
    """Get evaluation task details.

    Args:
        task_id: Task ID.
        db: Database session.
        current_user: Current authenticated user.

    Returns:
        Task details.
    """
    task = await EvalTaskService.get_eval_task(db, task_id, current_user.id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation task not found",
        )

    return EvalTaskResponse.model_validate(task)


@router.get("/tasks/{task_id}/progress", response_model=EvalProgressResponse)
async def get_eval_progress(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> EvalProgressResponse:
    """Get evaluation task progress.

    Args:
        task_id: Task ID.
        db: Database session.
        current_user: Current authenticated user.

    Returns:
        Task progress information.
    """
    progress = await EvalTaskService.get_eval_progress(db, task_id, current_user.id)

    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation task not found",
        )

    # Calculate estimated time remaining
    estimated_time = None
    if progress["status"] == "running" and progress["processed_questions"] > 0:
        elapsed_per_question = (
            (progress.get("completed_at") or __import__("datetime").datetime.utcnow()) -
            progress.get("started_at", __import__("datetime").datetime.utcnow())
        ).total_seconds() / progress["processed_questions"]
        remaining = progress["total_questions"] - progress["processed_questions"]
        estimated_time = int(elapsed_per_question * remaining)

    return EvalProgressResponse(
        task_id=progress["task_id"],
        status=progress["status"],
        progress_percent=progress["progress_percent"],
        total_questions=progress["total_questions"] or 0,
        processed_questions=progress["processed_questions"],
        correct_count=progress["correct_count"] or 0,
        accuracy=progress["accuracy"] or 0.0,
        estimated_time_remaining=estimated_time,
    )


@router.get("/tasks/{task_id}/results", response_model=EvalResultListResponse)
async def get_eval_results(
    task_id: int,
    skip: int = Query(0, ge=0, description="Number of results to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    is_correct: Optional[bool] = Query(None, description="Filter by correctness"),
    error_type: Optional[str] = Query(None, description="Filter by error type"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> EvalResultListResponse:
    """Get evaluation results for a task.

    Args:
        task_id: Task ID.
        skip: Number of results to skip.
        limit: Maximum number of results to return.
        is_correct: Filter by correctness.
        error_type: Filter by error type.
        db: Database session.
        current_user: Current authenticated user.

    Returns:
        List of evaluation results.
    """
    # Verify task belongs to user
    task = await EvalTaskService.get_eval_task(db, task_id, current_user.id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation task not found",
        )

    # Get results
    results = await EvalTaskService.get_eval_results(
        db=db,
        task_id=task_id,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        is_correct=is_correct,
        error_type=error_type,
    )

    # Get total count
    count_query = select(func.count(EvalResult.id)).where(EvalResult.task_id == task_id)
    if is_correct is not None:
        count_query = count_query.where(EvalResult.is_correct == is_correct)
    if error_type:
        count_query = count_query.where(EvalResult.error_type == error_type)

    result = await db.execute(count_query)
    total = result.scalar() or 0

    return EvalResultListResponse(
        items=[EvalResultResponse.model_validate(r) for r in results],
        total=total,
        limit=limit,
        offset=skip,
    )


@router.get("/tasks/{task_id}/stats", response_model=EvalStatsResponse)
async def get_eval_stats(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> EvalStatsResponse:
    """Get evaluation task statistics.

    Args:
        task_id: Task ID.
        db: Database session.
        current_user: Current authenticated user.

    Returns:
        Task statistics.
    """
    stats = await EvalTaskService.get_eval_stats(db, task_id, current_user.id)

    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation task not found",
        )

    return EvalStatsResponse(
        task_id=stats.task_id,
        total_questions=stats.total_questions,
        correct_count=stats.correct_count,
        accuracy=stats.accuracy,
        error_breakdown=stats.error_types,
        avg_execution_time_ms=stats.avg_execution_time_ms,
    )


@router.post("/tasks/{task_id}/cancel", response_model=EvalTaskResponse)
async def cancel_eval_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> EvalTaskResponse:
    """Cancel an evaluation task.

    Args:
        task_id: Task ID.
        db: Database session.
        current_user: Current authenticated user.

    Returns:
        Updated task details.
    """
    task = await EvalTaskService.get_eval_task(db, task_id, current_user.id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation task not found",
        )

    cancelled = await EvalTaskService.cancel_eval_task(db, task)

    if not cancelled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel task with status '{task.status}'",
        )

    logger.info(f"Cancelled eval task {task_id}")
    return EvalTaskResponse.model_validate(task)


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_eval_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """Delete an evaluation task and all its results.

    Args:
        task_id: Task ID.
        db: Database session.
        current_user: Current authenticated user.
    """
    task = await EvalTaskService.get_eval_task(db, task_id, current_user.id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation task not found",
        )

    # Don't allow deletion of running tasks
    if task.status == "running":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete a running task. Cancel it first.",
        )

    await db.delete(task)
    await db.commit()

    logger.info(f"Deleted eval task {task_id}")
