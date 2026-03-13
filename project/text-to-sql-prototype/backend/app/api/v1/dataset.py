"""Dataset import API routes for BIRD dataset support."""
import os
import shutil
import tempfile
import zipfile
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.core.logging import get_logger
from app.models.user import User
from app.schemas.evaluation import (
    DatasetImportResponse,
    DatasetImportProgress,
    DatasetImportItem,
    DatasetImportTaskInfo,
    DatasetImportConnectionInfo,
)
from app.services.connection import ConnectionService
from app.services.eval_task import EvalTaskService

logger = get_logger(__name__)
router = APIRouter(prefix="/datasets", tags=["Datasets"])


@router.post("/import/zip", response_model=DatasetImportResponse)
async def import_dataset_zip(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="BIRD dataset zip file"),
    dataset_type: str = Form(default="bird", description="Dataset type"),
    api_key_id: int = Form(..., description="API Key ID"),
    eval_mode: str = Form(default="greedy_search", description="Evaluation mode"),
    temperature: float = Form(default=0.7, ge=0.0, le=2.0, description="Temperature"),
    max_tokens: int = Form(default=2000, ge=100, le=8000, description="Max tokens"),
    sampling_count: Optional[int] = Form(default=None, ge=1, le=16, description="Pass@K sampling count"),
    max_iterations: Optional[int] = Form(default=None, ge=1, le=5, description="CheckCorrect max iterations"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> DatasetImportResponse:
    """Import BIRD dataset from uploaded zip file.

    Args:
        background_tasks: FastAPI background tasks.
        file: Uploaded zip file.
        dataset_type: Dataset type (default: bird).
        api_key_id: API Key ID for LLM.
        eval_mode: Evaluation mode.
        temperature: Sampling temperature.
        max_tokens: Maximum tokens.
        sampling_count: Pass@K sampling count (for pass_at_k mode).
        max_iterations: Max iterations (for check_correct mode).
        db: Database session.
        current_user: Current authenticated user.

    Returns:
        Import result with connections and tasks info.
    """
    # Validate file type
    if not file.filename or not file.filename.endswith('.zip'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only zip files are supported.",
        )

    # Generate import ID
    import_id = f"bird_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

    # Create temporary directory for extraction
    temp_dir = tempfile.mkdtemp(prefix=f"import_{import_id}_")
    extract_dir = os.path.join(temp_dir, "extracted")
    data_dir = os.path.join(temp_dir, "data")

    try:
        # Save uploaded file
        zip_path = os.path.join(temp_dir, file.filename)
        with open(zip_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Extract zip file
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        # Find dev.json
        dev_json_path = _find_dev_json(extract_dir)
        if not dev_json_path:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid dataset format. dev.json not found in zip file.",
            )

        # Find databases directory
        databases_dir = _find_databases_dir(extract_dir)
        if not databases_dir:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid dataset format. Databases directory not found.",
            )

        # Load and parse dev.json
        import json
        with open(dev_json_path, 'r', encoding='utf-8') as f:
            questions_data = json.load(f)

        # Group questions by db_id
        questions_by_db: Dict[str, List[Dict]] = {}
        for q in questions_data:
            db_id = q.get('db_id')
            if db_id:
                if db_id not in questions_by_db:
                    questions_by_db[db_id] = []
                questions_by_db[db_id].append(q)

        db_ids = list(questions_by_db.keys())
        total_questions = len(questions_data)

        # Create connections for each database
        connection_mapping = await ConnectionService.batch_create_connections(
            db=db,
            db_ids=db_ids,
            base_path=databases_dir,
            user_id=current_user.id,
            prefix="bird",
        )

        # Build connection results
        connection_items = []
        for db_id in db_ids:
            conn_id = connection_mapping.get(db_id)
            if conn_id:
                connection_items.append(
                    DatasetImportConnectionInfo(
                        db_id=db_id,
                        connection_id=conn_id,
                        status="success",
                    )
                )
            else:
                connection_items.append(
                    DatasetImportConnectionInfo(
                        db_id=db_id,
                        connection_id=None,
                        status="failed",
                        error="Failed to create connection",
                    )
                )

        # Create parent task
        dataset_config = {
            "name": f"BIRD {dataset_type.upper()} Dataset",
            "dataset_type": dataset_type,
            "dataset_path": data_dir,
            "model_config": {
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
            "eval_mode": eval_mode,
            "max_iterations": max_iterations or 3,
            "sampling_count": sampling_count or 1,
        }

        parent_task = await EvalTaskService.create_parent_task(
            db=db,
            dataset_config=dataset_config,
            user_id=current_user.id,
        )

        # Create child tasks
        child_tasks = await EvalTaskService.create_child_tasks(
            db=db,
            parent_id=parent_task.id,
            db_connections=connection_mapping,
            dataset_questions=questions_by_db,
            parent_config=dataset_config,
            user_id=current_user.id,
        )

        # Build task results
        task_items = []
        for task in child_tasks:
            task_items.append(
                DatasetImportTaskInfo(
                    db_id=task.db_id,
                    task_id=task.id,
                    connection_id=task.connection_id,
                    status="success",
                )
            )

        success = len(connection_items) == len(db_ids) and len(task_items) == len(db_ids)

        return DatasetImportResponse(
            success=success,
            message="Successfully imported BIRD dataset" if success else "Partially imported BIRD dataset",
            import_id=import_id,
            data_directory=data_dir,
            parent_task_id=parent_task.id,
            connections={
                "total": len(db_ids),
                "success": len([c for c in connection_items if c.status == "success"]),
                "failed": len([c for c in connection_items if c.status == "failed"]),
                "items": connection_items,
            },
            tasks={
                "total": len(task_items),
                "success": len([t for t in task_items if t.status == "success"]),
                "failed": len([t for t in task_items if t.status == "failed"]),
                "parent_task": {
                    "id": parent_task.id,
                    "name": parent_task.name,
                    "task_type": "parent",
                    "child_count": parent_task.child_count,
                },
                "children": task_items,
            },
            total_questions=total_questions,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to import dataset: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import dataset: {str(e)}",
        )
    finally:
        # Cleanup temp directory
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)


@router.post("/import/local", response_model=DatasetImportResponse)
async def import_dataset_local(
    request: dict,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> DatasetImportResponse:
    """Import BIRD dataset from local directory.

    Args:
        request: Import request with local_path and config.
        background_tasks: FastAPI background tasks.
        db: Database session.
        current_user: Current authenticated user.

    Returns:
        Import result with connections and tasks info.
    """
    local_path = request.get("local_path")
    if not local_path or not os.path.exists(local_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid local path. Directory does not exist.",
        )

    # Generate import ID
    import_id = f"bird_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

    try:
        # Find dev.json
        dev_json_path = _find_dev_json(local_path)
        if not dev_json_path:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid dataset format. dev.json not found.",
            )

        # Find databases directory
        databases_dir = _find_databases_dir(local_path)
        if not databases_dir:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid dataset format. Databases directory not found.",
            )

        # Load and parse dev.json
        import json
        with open(dev_json_path, 'r', encoding='utf-8') as f:
            questions_data = json.load(f)

        # Group questions by db_id
        questions_by_db: Dict[str, List[Dict]] = {}
        for q in questions_data:
            db_id = q.get('db_id')
            if db_id:
                if db_id not in questions_by_db:
                    questions_by_db[db_id] = []
                questions_by_db[db_id].append(q)

        db_ids = list(questions_by_db.keys())
        total_questions = len(questions_data)

        # Create connections
        connection_mapping = await ConnectionService.batch_create_connections(
            db=db,
            db_ids=db_ids,
            base_path=databases_dir,
            user_id=current_user.id,
            prefix="bird",
        )

        # Build connection results
        connection_items = []
        for db_id in db_ids:
            conn_id = connection_mapping.get(db_id)
            if conn_id:
                connection_items.append(
                    DatasetImportConnectionInfo(
                        db_id=db_id,
                        connection_id=conn_id,
                        status="success",
                    )
                )
            else:
                connection_items.append(
                    DatasetImportConnectionInfo(
                        db_id=db_id,
                        connection_id=None,
                        status="failed",
                        error="Failed to create connection",
                    )
                )

        # Create parent task
        dataset_config = {
            "name": request.get("name", f"BIRD {request.get('dataset_type', 'bird').upper()} Dataset"),
            "dataset_type": request.get("dataset_type", "bird"),
            "dataset_path": local_path,
            "model_config": {
                "temperature": request.get("temperature", 0.7),
                "max_tokens": request.get("max_tokens", 2000),
            },
            "eval_mode": request.get("eval_mode", "greedy_search"),
            "max_iterations": request.get("max_iterations", 3),
            "sampling_count": request.get("sampling_count", 1),
        }

        parent_task = await EvalTaskService.create_parent_task(
            db=db,
            dataset_config=dataset_config,
            user_id=current_user.id,
        )

        # Create child tasks
        child_tasks = await EvalTaskService.create_child_tasks(
            db=db,
            parent_id=parent_task.id,
            db_connections=connection_mapping,
            dataset_questions=questions_by_db,
            parent_config=dataset_config,
            user_id=current_user.id,
        )

        # Build task results
        task_items = []
        for task in child_tasks:
            task_items.append(
                DatasetImportTaskInfo(
                    db_id=task.db_id,
                    task_id=task.id,
                    connection_id=task.connection_id,
                    status="success",
                )
            )

        success = len(connection_items) == len(db_ids) and len(task_items) == len(db_ids)

        return DatasetImportResponse(
            success=success,
            message="Successfully imported BIRD dataset" if success else "Partially imported BIRD dataset",
            import_id=import_id,
            data_directory=local_path,
            parent_task_id=parent_task.id,
            connections={
                "total": len(db_ids),
                "success": len([c for c in connection_items if c.status == "success"]),
                "failed": len([c for c in connection_items if c.status == "failed"]),
                "items": connection_items,
            },
            tasks={
                "total": len(task_items),
                "success": len([t for t in task_items if t.status == "success"]),
                "failed": len([t for t in task_items if t.status == "failed"]),
                "parent_task": {
                    "id": parent_task.id,
                    "name": parent_task.name,
                    "task_type": "parent",
                    "child_count": parent_task.child_count,
                },
                "children": task_items,
            },
            total_questions=total_questions,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to import dataset: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import dataset: {str(e)}",
        )


def _find_dev_json(base_path: str) -> Optional[str]:
    """Find dev.json file in the extracted directory."""
    for root, dirs, files in os.walk(base_path):
        if "dev.json" in files:
            return os.path.join(root, "dev.json")
    return None


def _find_databases_dir(base_path: str) -> Optional[str]:
    """Find databases directory in the extracted directory."""
    for root, dirs, files in os.walk(base_path):
        if "databases" in dirs:
            return os.path.join(root, "databases")
        # Also check if current dir contains .sqlite files
        for file in files:
            if file.endswith('.sqlite') or file.endswith('.db'):
                return root
    return None


@router.get("/imports", response_model=List[DatasetImportItem])
async def list_dataset_imports(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Page size"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[DatasetImportItem]:
    """List dataset imports for the current user.

    Args:
        page: Page number (1-indexed).
        page_size: Number of items per page.
        status: Optional status filter.
        db: Database session.
        current_user: Current authenticated user.

    Returns:
        List of import records.
    """
    # TODO: Implement import history tracking
    # For now, return empty list
    return []


@router.get("/imports/{import_id}", response_model=dict)
async def get_dataset_import(
    import_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """Get dataset import details.

    Args:
        import_id: Import ID.
        db: Database session.
        current_user: Current authenticated user.

    Returns:
        Import details.
    """
    # TODO: Implement import history tracking
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Import record not found",
    )


@router.get("/imports/{import_id}/progress", response_model=DatasetImportProgress)
async def get_import_progress(
    import_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> DatasetImportProgress:
    """Get dataset import progress.

    Args:
        import_id: Import ID.
        db: Database session.
        current_user: Current authenticated user.

    Returns:
        Import progress information.
    """
    # TODO: Implement progress tracking
    return DatasetImportProgress(
        import_id=import_id,
        status="completed",
        current_step=4,
        total_steps=4,
        step_name="Import completed",
        progress_percent=100,
        connections_created=0,
        total_connections=0,
        tasks_created=0,
        total_tasks=0,
        logs=[],
    )


@router.delete("/imports/{import_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dataset_import(
    import_id: str,
    delete_data: bool = Query(default=False, description="Also delete data files"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """Delete a dataset import record.

    Args:
        import_id: Import ID.
        delete_data: Whether to also delete data files.
        db: Database session.
        current_user: Current authenticated user.
    """
    # TODO: Implement import deletion
    pass
