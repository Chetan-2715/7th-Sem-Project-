"""
backend/services/task_manager.py
Thread-safe in-memory task tracker for asynchronous audit jobs.
Allows the frontend to poll progress (0-100%) and view real-time stage updates.
"""

import threading
import uuid
from typing import Dict, Optional
from datetime import datetime

from backend.schemas import TaskStatusResponse, AuditStatus, AuditResult


class TaskManager:
    """Stores and updates background audit task states."""

    def __init__(self):
        self._tasks: Dict[str, TaskStatusResponse] = {}
        self._lock = threading.Lock()

    def create_task(self, initial_stage: str = "Task initialized") -> str:
        """Creates a new audit task and returns unique task_id."""
        task_id = str(uuid.uuid4())
        with self._lock:
            self._tasks[task_id] = TaskStatusResponse(
                task_id=task_id,
                status=AuditStatus.PENDING,
                progress=0,
                current_stage=initial_stage,
                message="Audit scheduled in background"
            )
        return task_id

    def update_progress(self, task_id: str, progress: int, stage: str, message: Optional[str] = None):
        """Updates progress percentage and current stage."""
        with self._lock:
            if task_id in self._tasks:
                task = self._tasks[task_id]
                task.status = AuditStatus.IN_PROGRESS
                task.progress = min(max(progress, 0), 100)
                task.current_stage = stage
                if message:
                    task.message = message

    def complete_task(self, task_id: str, result: AuditResult):
        """Marks task as successfully completed with final AuditResult."""
        with self._lock:
            if task_id in self._tasks:
                task = self._tasks[task_id]
                task.status = AuditStatus.COMPLETED
                task.progress = 100
                task.current_stage = "Audit Complete"
                task.message = f"Audit completed successfully. Security Health Score: {result.health_score}/100"
                task.result = result

    def fail_task(self, task_id: str, error_message: str):
        """Marks task as failed with error details."""
        with self._lock:
            if task_id in self._tasks:
                task = self._tasks[task_id]
                task.status = AuditStatus.FAILED
                task.current_stage = "Failed"
                task.message = error_message

    def get_task(self, task_id: str) -> Optional[TaskStatusResponse]:
        """Retrieves current state of a task."""
        with self._lock:
            return self._tasks.get(task_id)


# Global singleton task manager instance
audit_task_manager = TaskManager()
