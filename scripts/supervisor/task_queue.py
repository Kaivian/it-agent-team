"""Task Queue and sequential multi-session lifecycle coordinator for IT Agent Team."""

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .models import QueueTaskItem, TaskQueueBatch, TaskStatus


class TaskQueue:
    def __init__(self, queue_file: Optional[Path] = None):
        if queue_file is None:
            self.queue_file = (
                Path.home()
                / ".gemini"
                / "config"
                / "plugins"
                / "agent-team"
                / ".agent_team"
                / "task_queue.json"
            )
        else:
            self.queue_file = Path(queue_file)

        self.queue_file.parent.mkdir(parents=True, exist_ok=True)
        self.batch: Optional[TaskQueueBatch] = None
        self._load()

    def _load(self) -> None:
        if self.queue_file.exists():
            try:
                data = json.loads(self.queue_file.read_text(encoding="utf-8"))
                tasks = [
                    QueueTaskItem(
                        item_id=t["item_id"],
                        title=t["title"],
                        description=t["description"],
                        status=TaskStatus(t.get("status", TaskStatus.PENDING.value)),
                        session_id=t.get("session_id"),
                        started_at=t.get("started_at"),
                        completed_at=t.get("completed_at"),
                    )
                    for t in data.get("tasks", [])
                ]
                self.batch = TaskQueueBatch(
                    batch_id=data["batch_id"],
                    tasks=tasks,
                    current_index=data.get("current_index", 0),
                    status=data.get("status", "IN_PROGRESS"),
                    created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
                )
            except Exception:
                self.batch = None

    def save(self) -> None:
        if not self.batch:
            return
        data = {
            "batch_id": self.batch.batch_id,
            "current_index": self.batch.current_index,
            "status": self.batch.status,
            "created_at": self.batch.created_at,
            "tasks": [
                {
                    "item_id": t.item_id,
                    "title": t.title,
                    "description": t.description,
                    "status": t.status.value,
                    "session_id": t.session_id,
                    "started_at": t.started_at,
                    "completed_at": t.completed_at,
                }
                for t in self.batch.tasks
            ],
        }
        self.queue_file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    @classmethod
    def parse_tasks_from_text(cls, text: str) -> list[tuple[str, str]]:
        """Parses numbered or bulleted list of tasks from text input."""
        results: list[tuple[str, str]] = []
        lines = [line.strip() for line in text.strip().splitlines() if line.strip()]

        pattern = re.compile(r"^(?:\d+[\.\)]|[-*])\s+(.+)$")
        current_title = ""
        current_desc: list[str] = []

        for line in lines:
            match = pattern.match(line)
            if match:
                if current_title:
                    results.append((current_title, " ".join(current_desc).strip() or current_title))
                    current_desc = []
                current_title = match.group(1).strip()
            elif current_title:
                current_desc.append(line)

        if current_title:
            results.append((current_title, " ".join(current_desc).strip() or current_title))

        # Fallback if no list pattern detected
        if not results and lines:
            results.append((lines[0], " ".join(lines[1:]).strip() or lines[0]))

        return results

    def initialize_batch(self, batch_id: str, raw_tasks: list[tuple[str, str]]) -> TaskQueueBatch:
        items = []
        for idx, (title, desc) in enumerate(raw_tasks, start=1):
            items.append(
                QueueTaskItem(
                    item_id=f"TASK-ITEM-{idx:03d}",
                    title=title,
                    description=desc,
                    status=TaskStatus.PENDING,
                )
            )
        self.batch = TaskQueueBatch(
            batch_id=batch_id,
            tasks=items,
            current_index=0,
            status="IN_PROGRESS",
        )
        self.save()
        return self.batch

    def get_current_task(self) -> Optional[QueueTaskItem]:
        if not self.batch or self.batch.current_index >= len(self.batch.tasks):
            return None
        return self.batch.tasks[self.batch.current_index]

    def start_current_task(self, session_id: str) -> Optional[QueueTaskItem]:
        task = self.get_current_task()
        if task:
            task.status = TaskStatus.IN_PROGRESS
            task.session_id = session_id
            task.started_at = datetime.now(timezone.utc).isoformat()
            self.save()
        return task

    def complete_current_task(self, success: bool = True) -> Optional[QueueTaskItem]:
        task = self.get_current_task()
        if task:
            task.status = TaskStatus.COMPLETED if success else TaskStatus.FAILED
            task.completed_at = datetime.now(timezone.utc).isoformat()
            self.batch.current_index += 1
            if self.batch.current_index >= len(self.batch.tasks):
                self.batch.status = "COMPLETED"
            self.save()
        return task

    def is_all_completed(self) -> bool:
        if not self.batch:
            return True
        return self.batch.current_index >= len(self.batch.tasks)

    def get_progress_summary(self) -> str:
        if not self.batch:
            return "No active task queue batch."
        total = len(self.batch.tasks)
        completed = sum(1 for t in self.batch.tasks if t.status == TaskStatus.COMPLETED)
        return (
            f"Batch [{self.batch.batch_id}]: {completed}/{total} tasks completed "
            f"(Current Task index: {self.batch.current_index + 1}/{total})"
        )
