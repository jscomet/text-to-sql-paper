"""WebSocket progress manager for real-time evaluation updates."""
import asyncio
import json
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Callable

from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger

logger = get_logger(__name__)


class ProgressEventType(str, Enum):
    """Types of progress events."""
    # Connection events
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    PING = "ping"
    PONG = "pong"

    # Task progress events
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_CANCELLED = "task_cancelled"

    # Question progress events
    QUESTION_STARTED = "question_started"
    QUESTION_COMPLETED = "question_completed"

    # Candidate generation events (Pass@K mode)
    CANDIDATE_GENERATION_STARTED = "candidate_generation_started"
    CANDIDATE_GENERATION_PROGRESS = "candidate_generation_progress"
    CANDIDATE_GENERATION_COMPLETED = "candidate_generation_completed"

    # Check-Correct iteration events
    CORRECTION_ITERATION_STARTED = "correction_iteration_started"
    CORRECTION_ITERATION_PROGRESS = "correction_iteration_progress"
    CORRECTION_ITERATION_COMPLETED = "correction_iteration_completed"

    # SQL execution events
    SQL_EXECUTION_STARTED = "sql_execution_started"
    SQL_EXECUTION_COMPLETED = "sql_execution_completed"
    SQL_EXECUTION_FAILED = "sql_execution_failed"

    # Evaluation result events
    EVALUATION_RESULT = "evaluation_result"
    ERROR_OCCURRED = "error_occurred"


@dataclass
class ProgressEvent:
    """Progress event data structure."""
    event_type: ProgressEventType
    task_id: int
    timestamp: str
    data: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "event_type": self.event_type.value,
            "task_id": self.task_id,
            "timestamp": self.timestamp,
            "data": self.data,
        }

    def to_json(self) -> str:
        """Convert event to JSON string."""
        return json.dumps(self.to_dict(), default=str)

    @classmethod
    def create(
        cls,
        event_type: ProgressEventType,
        task_id: int,
        data: Dict[str, Any],
    ) -> "ProgressEvent":
        """Create a new progress event."""
        return cls(
            event_type=event_type,
            task_id=task_id,
            timestamp=datetime.utcnow().isoformat(),
            data=data,
        )


class WebSocketProgressManager:
    """Manager for WebSocket progress connections."""

    def __init__(self):
        """Initialize the progress manager."""
        # task_id -> list of WebSocket connections
        self._connections: Dict[int, List[WebSocket]] = {}
        # task_id -> list of callback functions
        self._callbacks: Dict[int, List[Callable[[ProgressEvent], None]]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, task_id: int, websocket: WebSocket) -> None:
        """Register a new WebSocket connection for a task.

        Args:
            task_id: Task ID.
            websocket: WebSocket connection.
        """
        async with self._lock:
            if task_id not in self._connections:
                self._connections[task_id] = []
            self._connections[task_id].append(websocket)

        logger.debug(f"WebSocket connected for task {task_id}")

        # Send connected event
        event = ProgressEvent.create(
            event_type=ProgressEventType.CONNECTED,
            task_id=task_id,
            data={"message": "Successfully connected to progress stream"},
        )
        await self._send_to_websocket(websocket, event)

    async def disconnect(self, task_id: int, websocket: WebSocket) -> None:
        """Unregister a WebSocket connection for a task.

        Args:
            task_id: Task ID.
            websocket: WebSocket connection.
        """
        async with self._lock:
            if task_id in self._connections:
                if websocket in self._connections[task_id]:
                    self._connections[task_id].remove(websocket)
                if not self._connections[task_id]:
                    del self._connections[task_id]

        logger.debug(f"WebSocket disconnected for task {task_id}")

    async def broadcast(self, event: ProgressEvent) -> None:
        """Broadcast a progress event to all connected clients for a task.

        Args:
            event: Progress event to broadcast.
        """
        task_id = event.task_id

        async with self._lock:
            connections = self._connections.get(task_id, []).copy()

        if not connections:
            return

        # Send to all connected WebSockets
        disconnected = []
        for websocket in connections:
            try:
                await self._send_to_websocket(websocket, event)
            except Exception as e:
                logger.warning(f"Failed to send progress to WebSocket for task {task_id}: {e}")
                disconnected.append(websocket)

        # Clean up disconnected clients
        async with self._lock:
            for websocket in disconnected:
                if task_id in self._connections and websocket in self._connections[task_id]:
                    self._connections[task_id].remove(websocket)
            if task_id in self._connections and not self._connections[task_id]:
                del self._connections[task_id]

    async def _send_to_websocket(self, websocket: WebSocket, event: ProgressEvent) -> None:
        """Send an event to a specific WebSocket.

        Args:
            websocket: WebSocket connection.
            event: Progress event.
        """
        try:
            await websocket.send_json(event.to_dict())
        except Exception as e:
            raise WebSocketDisconnect() from e

    def register_callback(
        self,
        task_id: int,
        callback: Callable[[ProgressEvent], None],
    ) -> None:
        """Register a callback function for progress events.

        Args:
            task_id: Task ID.
            callback: Callback function to receive progress events.
        """
        if task_id not in self._callbacks:
            self._callbacks[task_id] = []
        self._callbacks[task_id].append(callback)

    def unregister_callback(
        self,
        task_id: int,
        callback: Callable[[ProgressEvent], None],
    ) -> None:
        """Unregister a callback function.

        Args:
            task_id: Task ID.
            callback: Callback function to remove.
        """
        if task_id in self._callbacks:
            self._callbacks[task_id] = [
                cb for cb in self._callbacks[task_id] if cb != callback
            ]

    async def notify_callbacks(self, event: ProgressEvent) -> None:
        """Notify all registered callbacks of a progress event.

        Args:
            event: Progress event.
        """
        callbacks = self._callbacks.get(event.task_id, [])
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.warning(f"Progress callback failed for task {event.task_id}: {e}")

    def get_connection_count(self, task_id: int) -> int:
        """Get the number of active connections for a task.

        Args:
            task_id: Task ID.

        Returns:
            Number of active connections.
        """
        return len(self._connections.get(task_id, []))


# Global progress manager instance
_progress_manager: Optional[WebSocketProgressManager] = None


def get_progress_manager() -> WebSocketProgressManager:
    """Get the global progress manager instance.

    Returns:
        WebSocketProgressManager instance.
    """
    global _progress_manager
    if _progress_manager is None:
        _progress_manager = WebSocketProgressManager()
    return _progress_manager


async def broadcast_progress_update(
    task_id: int,
    event_type: ProgressEventType,
    data: Dict[str, Any],
) -> None:
    """Broadcast a progress update to all connected clients.

    Args:
        task_id: Task ID.
        event_type: Type of progress event.
        data: Event data.
    """
    manager = get_progress_manager()
    event = ProgressEvent.create(
        event_type=event_type,
        task_id=task_id,
        data=data,
    )
    await manager.broadcast(event)
    await manager.notify_callbacks(event)


# Helper functions for common progress events

async def notify_task_started(task_id: int, total_questions: int) -> None:
    """Notify that a task has started.

    Args:
        task_id: Task ID.
        total_questions: Total number of questions.
    """
    await broadcast_progress_update(
        task_id=task_id,
        event_type=ProgressEventType.TASK_STARTED,
        data={"total_questions": total_questions},
    )


async def notify_task_completed(
    task_id: int,
    correct_count: int,
    total_count: int,
) -> None:
    """Notify that a task has completed.

    Args:
        task_id: Task ID.
        correct_count: Number of correct predictions.
        total_count: Total number of questions.
    """
    await broadcast_progress_update(
        task_id=task_id,
        event_type=ProgressEventType.TASK_COMPLETED,
        data={
            "correct_count": correct_count,
            "total_count": total_count,
            "accuracy": correct_count / total_count if total_count > 0 else 0.0,
        },
    )


async def notify_question_started(
    task_id: int,
    question_id: str,
    question: str,
    current: int,
    total: int,
) -> None:
    """Notify that processing of a question has started.

    Args:
        task_id: Task ID.
        question_id: Question ID.
        question: Question text.
        current: Current question index.
        total: Total number of questions.
    """
    await broadcast_progress_update(
        task_id=task_id,
        event_type=ProgressEventType.QUESTION_STARTED,
        data={
            "question_id": question_id,
            "question": question,
            "progress": {"current": current, "total": total},
        },
    )


async def notify_candidate_generation_progress(
    task_id: int,
    question_id: str,
    current: int,
    total: int,
    sql_preview: Optional[str] = None,
) -> None:
    """Notify progress of candidate SQL generation (Pass@K mode).

    Args:
        task_id: Task ID.
        question_id: Question ID.
        current: Current candidate index.
        total: Total number of candidates.
        sql_preview: Preview of generated SQL.
    """
    await broadcast_progress_update(
        task_id=task_id,
        event_type=ProgressEventType.CANDIDATE_GENERATION_PROGRESS,
        data={
            "question_id": question_id,
            "progress": {"current": current, "total": total},
            "sql_preview": sql_preview,
        },
    )


async def notify_correction_iteration_progress(
    task_id: int,
    question_id: str,
    iteration: int,
    max_iterations: int,
    error_type: Optional[str] = None,
    error_message: Optional[str] = None,
) -> None:
    """Notify progress of correction iteration (Check-Correct mode).

    Args:
        task_id: Task ID.
        question_id: Question ID.
        iteration: Current iteration number.
        max_iterations: Maximum number of iterations.
        error_type: Type of error being corrected.
        error_message: Error message.
    """
    await broadcast_progress_update(
        task_id=task_id,
        event_type=ProgressEventType.CORRECTION_ITERATION_PROGRESS,
        data={
            "question_id": question_id,
            "iteration": iteration,
            "max_iterations": max_iterations,
            "error_type": error_type,
            "error_message": error_message,
        },
    )
