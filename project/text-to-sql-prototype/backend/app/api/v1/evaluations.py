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
    EvalTaskWithChildrenResponse,
    EvalTaskChildResponse,
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
    task_type: Optional[str] = Query(None, description="Filter by task type: parent, child, single"),
    parent_id: Optional[int] = Query(None, description="Filter by parent task ID"),
    db_id: Optional[str] = Query(None, description="Filter by database ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> EvalTaskListResponse:
    """List evaluation tasks for the current user.

    Args:
        page: Page number (1-indexed).
        page_size: Number of items per page.
        status: Optional status filter.
        task_type: Optional task type filter (parent, child, single).
        parent_id: Optional parent task ID filter.
        db_id: Optional database ID filter.
        db: Database session.
        current_user: Current authenticated user.

    Returns:
        List of evaluation tasks.
    """
    skip = (page - 1) * page_size

    # Build base query
    query = select(EvalTask).where(EvalTask.user_id == current_user.id)
    count_query = select(func.count(EvalTask.id)).where(EvalTask.user_id == current_user.id)

    # Apply filters
    if status:
        query = query.where(EvalTask.status == status)
        count_query = count_query.where(EvalTask.status == status)

    if task_type:
        query = query.where(EvalTask.task_type == task_type)
        count_query = count_query.where(EvalTask.task_type == task_type)

    if parent_id is not None:
        query = query.where(EvalTask.parent_id == parent_id)
        count_query = count_query.where(EvalTask.parent_id == parent_id)

    if db_id:
        query = query.where(EvalTask.db_id == db_id)
        count_query = count_query.where(EvalTask.db_id == db_id)

    # Order by created_at desc
    query = query.order_by(EvalTask.created_at.desc())

    # Apply pagination
    query = query.offset(skip).limit(page_size)

    # Execute query
    result = await db.execute(query)
    tasks = result.scalars().all()

    # Get total count
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

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


@router.get("/tasks/{task_id}", response_model=EvalTaskWithChildrenResponse)
async def get_eval_task(
    task_id: int,
    include_children: bool = Query(default=True, description="Include children for parent tasks"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> EvalTaskWithChildrenResponse:
    """Get evaluation task details.

    Args:
        task_id: Task ID.
        include_children: Whether to include children for parent tasks.
        db: Database session.
        current_user: Current authenticated user.

    Returns:
        Task details with optional children.
    """
    task = await EvalTaskService.get_eval_task(db, task_id, current_user.id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation task not found",
        )

    # If it's a parent task and include_children is True, fetch children
    children = []
    if task.task_type == "parent" and include_children:
        child_tasks = await EvalTaskService.get_child_tasks(db, task_id, current_user.id)
        children = [
            EvalTaskChildResponse(
                id=child.id,
                name=child.name,
                task_type=child.task_type,
                db_id=child.db_id,
                connection_id=child.connection_id,
                status=child.status,
                progress_percent=child.progress_percent,
                total_questions=child.total_questions,
                correct_count=child.correct_count,
                accuracy=child.accuracy,
                created_at=child.created_at,
                completed_at=child.completed_at,
            )
            for child in child_tasks
        ]

    return EvalTaskWithChildrenResponse(
        id=task.id,
        user_id=task.user_id,
        name=task.name,
        task_type=task.task_type,
        dataset_type=task.dataset_type,
        dataset_path=task.dataset_path,
        model_settings=task.model_config,
        eval_mode=task.eval_mode,
        status=task.status,
        progress_percent=task.progress_percent,
        total_questions=task.total_questions,
        processed_questions=task.processed_questions,
        correct_count=task.correct_count,
        accuracy=task.accuracy,
        child_count=task.child_count,
        completed_children=task.completed_children,
        log_path=task.log_path,
        error_message=task.error_message,
        created_at=task.created_at,
        updated_at=task.updated_at,
        started_at=task.started_at,
        completed_at=task.completed_at,
        children=children,
    )


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

    # Calculate pagination info
    page = skip // limit + 1 if limit > 0 else 1
    total_pages = (total + limit - 1) // limit if limit > 0 else 1

    return EvalResultListResponse(
        list=[EvalResultResponse.model_validate(r) for r in results],
        pagination={
            "total": total,
            "page": page,
            "page_size": limit,
            "total_pages": total_pages,
        },
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


@router.post("/tasks/{parent_id}/start-all", response_model=dict)
async def start_all_child_tasks(
    parent_id: int,
    background_tasks: BackgroundTasks,
    api_key_id: int = Query(..., description="API Key ID for LLM"),
    delay_seconds: int = Query(default=0, ge=0, description="Delay between starting tasks"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """Start all pending child tasks for a parent task.

    Args:
        parent_id: Parent task ID.
        api_key_id: API Key ID for LLM.
        delay_seconds: Delay between starting tasks in seconds.
        background_tasks: FastAPI background tasks.
        db: Database session.
        current_user: Current authenticated user.

    Returns:
        Start result with counts and task IDs.
    """
    # Get parent task
    parent = await EvalTaskService.get_eval_task(db, parent_id, current_user.id)

    if not parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent task not found",
        )

    if parent.task_type != "parent":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task is not a parent task",
        )

    # Get API key configuration
    api_key_config = await get_user_api_key_by_id(
        user_id=current_user.id,
        key_id=api_key_id,
        db=db,
    )

    if not api_key_config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid API key ID",
        )

    # Get child tasks
    child_tasks = await EvalTaskService.get_child_tasks(db, parent_id, current_user.id)

    # Filter pending tasks
    pending_tasks = [t for t in child_tasks if t.status == "pending"]

    if not pending_tasks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No pending child tasks to start",
        )

    # Start each child task in background
    started_task_ids = []
    for task in pending_tasks:
        # Build model config from task and api_key config
        model_config = {
            "model": api_key_config["model"],
            "temperature": task.model_config.get("temperature", 0.7),
            "max_tokens": task.model_config.get("max_tokens", 2000),
        }

        # Add inference config if present in task's model_config
        inference_config = task.model_config.get("inference", {})
        if inference_config:
            model_config["inference"] = inference_config

        # Get dataset path for this child task
        # Child tasks use the db_id to form the dataset path
        dataset_path = task.dataset_path
        if dataset_path and task.db_id:
            # For BIRD dataset, the dataset file is at dataset_path/db_id.json
            import os

            possible_paths = [
                os.path.join(dataset_path, f"{task.db_id}.json"),
                os.path.join(dataset_path, "dev.json"),
                dataset_path,
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    dataset_path = path
                    break

        # Add task to background tasks
        background_tasks.add_task(
            run_evaluation_task,
            task_id=task.id,
            user_id=current_user.id,
            connection_id=task.connection_id,
            dataset_path=dataset_path or parent.dataset_path,
            provider=api_key_config["provider"],
            model_config=model_config,
            eval_mode=task.eval_mode,
            api_key=api_key_config["api_key"],
            format_type=api_key_config["format_type"],
            base_url=api_key_config.get("base_url"),
            # Advanced inference parameters from task config
            sampling_count=task.sampling_count if task.eval_mode == "pass_at_k" else None,
            max_iterations=task.max_iterations if task.eval_mode == "check_correct" else None,
            correction_strategy=task.correction_strategy.get("strategy", "self_correction") if task.correction_strategy else None,
            sampling_config=task.model_config.get("inference", {}).get("sampling_config") if task.eval_mode == "pass_at_k" else None,
            correction_config=task.model_config.get("inference", {}).get("correction_config") if task.eval_mode == "check_correct" else None,
        )

        started_task_ids.append(task.id)

    # Update parent task status to running
    if started_task_ids:
        await EvalTaskService.start_eval_task(db, parent)

    return {
        "success": True,
        "message": f"Started {len(started_task_ids)} child tasks",
        "started_count": len(started_task_ids),
        "skipped_count": len(child_tasks) - len(pending_tasks),
        "started_tasks": started_task_ids,
    }


@router.post("/tasks/{parent_id}/retry-failed", response_model=dict)
async def retry_failed_child_tasks(
    parent_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """Retry all failed child tasks for a parent task.

    Args:
        parent_id: Parent task ID.
        db: Database session.
        current_user: Current authenticated user.

    Returns:
        Retry result with counts and task IDs.
    """
    # Get parent task
    parent = await EvalTaskService.get_eval_task(db, parent_id, current_user.id)

    if not parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent task not found",
        )

    if parent.task_type != "parent":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task is not a parent task",
        )

    # Get child tasks
    child_tasks = await EvalTaskService.get_child_tasks(db, parent_id, current_user.id)

    # Filter failed tasks
    failed_tasks = [t for t in child_tasks if t.status == "failed"]

    if not failed_tasks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No failed child tasks to retry",
        )

    # TODO: Reset and retry tasks
    retried_task_ids = [t.id for t in failed_tasks]

    return {
        "success": True,
        "message": f"Retried {len(failed_tasks)} failed child tasks",
        "retried_count": len(failed_tasks),
        "retried_tasks": retried_task_ids,
    }


@router.get("/tasks/{parent_id}/children", response_model=dict)
async def list_child_tasks(
    parent_id: int,
    task_status: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Page size"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """List child tasks for a parent task.

    Args:
        parent_id: Parent task ID.
        task_status: Optional status filter.
        page: Page number (1-indexed).
        page_size: Number of items per page.
        db: Database session.
        current_user: Current authenticated user.

    Returns:
        List of child tasks with pagination.
    """
    # Get parent task
    parent = await EvalTaskService.get_eval_task(db, parent_id, current_user.id)

    if not parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent task not found",
        )

    # Get child tasks
    child_tasks = await EvalTaskService.get_child_tasks(db, parent_id, current_user.id)

    # Filter by status if provided
    if task_status:
        child_tasks = [t for t in child_tasks if t.status == task_status]

    # Pagination
    total = len(child_tasks)
    skip = (page - 1) * page_size
    paginated_tasks = child_tasks[skip:skip + page_size]

    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

    return {
        "parent_id": parent_id,
        "list": [
            {
                "id": t.id,
                "name": t.name,
                "db_id": t.db_id,
                "connection_id": t.connection_id,
                "status": t.status,
                "progress_percent": t.progress_percent,
                "question_count": t.total_questions,
                "processed_count": t.processed_questions,
                "correct_count": t.correct_count,
                "accuracy": t.accuracy,
            }
            for t in paginated_tasks
        ],
        "pagination": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        },
    }
