"""WebSocket routes for real-time evaluation progress updates."""
from typing import Optional

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user_from_websocket
from app.core.database import get_db
from app.core.logging import get_logger
from app.models.user import User
from app.tasks.eval_tasks import register_progress_callback, unregister_progress_callback

logger = get_logger(__name__)
router = APIRouter(prefix="/ws/eval", tags=["WebSocket Evaluations"])

# Store active WebSocket connections
_active_connections: dict[int, list[WebSocket]] = {}


async def broadcast_progress_update(task_id: int, progress_data: dict) -> None:
    """Broadcast progress update to all connected WebSocket clients for a task.

    Args:
        task_id: Task ID.
        progress_data: Progress update data.
    """
    if task_id not in _active_connections:
        return

    disconnected = []
    for websocket in _active_connections[task_id]:
        try:
            await websocket.send_json(progress_data)
        except Exception as e:
            logger.warning(f"Failed to send progress to WebSocket for task {task_id}: {e}")
            disconnected.append(websocket)

    # Remove disconnected clients
    for websocket in disconnected:
        _active_connections[task_id].remove(websocket)


@router.websocket("/tasks/{task_id}/progress")
async def eval_progress_websocket(
    websocket: WebSocket,
    task_id: int,
    token: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """WebSocket endpoint for real-time evaluation progress updates.

    Args:
        websocket: WebSocket connection.
        task_id: Task ID to monitor.
        token: Authentication token (can be passed as query parameter).
        db: Database session.
    """
    # Authenticate user
    try:
        current_user = await get_current_active_user_from_websocket(token, db)
    except Exception as e:
        logger.warning(f"WebSocket authentication failed for task {task_id}: {e}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Verify task belongs to user
    from app.services.eval_task import EvalTaskService

    task = await EvalTaskService.get_eval_task(db, task_id, current_user.id)
    if not task:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Task not found")
        return

    # Accept connection
    await websocket.accept()
    logger.debug(f"WebSocket connection accepted for task {task_id}, user {current_user.id}")

    # Register connection
    if task_id not in _active_connections:
        _active_connections[task_id] = []
    _active_connections[task_id].append(websocket)

    # Define progress callback
    async def progress_callback(progress_data: dict) -> None:
        """Send progress update via WebSocket."""
        try:
            await websocket.send_json({
                "type": "progress_update",
                "task_id": task_id,
                "data": progress_data,
            })
        except Exception as e:
            logger.warning(f"Failed to send WebSocket progress: {e}")

    # Register callback for this task
    register_progress_callback(task_id, progress_callback)

    # Send initial connection success message
    await websocket.send_json({
        "type": "connected",
        "task_id": task_id,
        "message": "Successfully connected to progress stream",
    })

    try:
        # Keep connection alive and handle client messages
        while True:
            try:
                # Wait for messages from client (ping/heartbeat)
                data = await websocket.receive_json()

                # Handle ping
                if data.get("type") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": data.get("timestamp"),
                    })

                # Handle subscription requests
                elif data.get("type") == "subscribe":
                    await websocket.send_json({
                        "type": "subscribed",
                        "task_id": task_id,
                    })

            except WebSocketDisconnect:
                logger.debug(f"WebSocket disconnected for task {task_id}")
                break
            except Exception as e:
                logger.warning(f"WebSocket message handling error for task {task_id}: {e}")
                break

    finally:
        # Cleanup
        unregister_progress_callback(task_id, progress_callback)
        if task_id in _active_connections and websocket in _active_connections[task_id]:
            _active_connections[task_id].remove(websocket)
            if not _active_connections[task_id]:
                del _active_connections[task_id]

        logger.debug(f"WebSocket connection closed for task {task_id}")


@router.websocket("/tasks/{task_id}/detailed")
async def eval_detailed_progress_websocket(
    websocket: WebSocket,
    task_id: int,
    token: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """WebSocket endpoint for detailed real-time progress with sub-task information.

    This endpoint provides more detailed progress updates including:
    - Candidate generation progress (for Pass@K mode)
    - Check-Correct iteration progress
    - Detailed intermediate states

    Args:
        websocket: WebSocket connection.
        task_id: Task ID to monitor.
        token: Authentication token.
        db: Database session.
    """
    # Authenticate user
    try:
        current_user = await get_current_active_user_from_websocket(token, db)
    except Exception as e:
        logger.warning(f"Detailed WebSocket authentication failed for task {task_id}: {e}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Verify task belongs to user
    from app.services.eval_task import EvalTaskService

    task = await EvalTaskService.get_eval_task(db, task_id, current_user.id)
    if not task:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Task not found")
        return

    # Accept connection
    await websocket.accept()
    logger.debug(f"Detailed WebSocket connection accepted for task {task_id}")

    # Register connection
    if task_id not in _active_connections:
        _active_connections[task_id] = []
    _active_connections[task_id].append(websocket)

    # Define detailed progress callback
    async def detailed_progress_callback(progress_data: dict) -> None:
        """Send detailed progress update via WebSocket."""
        try:
            # Enrich progress data with detailed information
            enriched_data = {
                "type": "detailed_progress_update",
                "task_id": task_id,
                "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
                "data": progress_data,
            }

            # Add specific handling for different progress types
            if "candidate_progress" in progress_data:
                enriched_data["progress_type"] = "candidate_generation"
            elif "check_correct_progress" in progress_data:
                enriched_data["progress_type"] = "check_correct_iteration"
            elif "sub_progress" in progress_data:
                enriched_data["progress_type"] = "sub_task"
            else:
                enriched_data["progress_type"] = "general"

            await websocket.send_json(enriched_data)
        except Exception as e:
            logger.warning(f"Failed to send detailed WebSocket progress: {e}")

    # Register callback for this task
    register_progress_callback(task_id, detailed_progress_callback)

    # Send initial connection success message
    await websocket.send_json({
        "type": "connected",
        "task_id": task_id,
        "mode": "detailed",
        "message": "Successfully connected to detailed progress stream",
    })

    try:
        while True:
            try:
                data = await websocket.receive_json()

                if data.get("type") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": data.get("timestamp"),
                    })

                elif data.get("type") == "request_status":
                    # Send current task status
                    task = await EvalTaskService.get_eval_task(db, task_id, current_user.id)
                    if task:
                        await websocket.send_json({
                            "type": "status_response",
                            "task_id": task_id,
                            "status": task.status,
                            "progress": {
                                "processed": task.processed_questions,
                                "total": task.total_questions,
                                "correct": task.correct_count,
                            },
                        })

            except WebSocketDisconnect:
                logger.debug(f"Detailed WebSocket disconnected for task {task_id}")
                break
            except Exception as e:
                logger.warning(f"Detailed WebSocket message handling error: {e}")
                break

    finally:
        # Cleanup
        unregister_progress_callback(task_id, detailed_progress_callback)
        if task_id in _active_connections and websocket in _active_connections[task_id]:
            _active_connections[task_id].remove(websocket)
            if not _active_connections[task_id]:
                del _active_connections[task_id]

        logger.debug(f"Detailed WebSocket connection closed for task {task_id}")
