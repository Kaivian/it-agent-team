"""Data models for IT Agent Team supervisor and orchestration runtime."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class AgentState(str, Enum):
    INITIALIZING = "INITIALIZING"
    READY = "READY"
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    PAUSED = "PAUSED"
    BLOCKED = "BLOCKED"
    DISCONNECTED = "DISCONNECTED"
    RECONNECTING = "RECONNECTING"
    FAILED = "FAILED"
    COMPLETED = "COMPLETED"
    TERMINATED = "TERMINATED"


class ConnectionState(str, Enum):
    CONNECTED = "CONNECTED"
    UNSTABLE = "UNSTABLE"
    DISCONNECTED = "DISCONNECTED"
    RECONNECTING = "RECONNECTING"


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"


class LockType(str, Enum):
    EXCLUSIVE = "EXCLUSIVE"
    SHARED = "SHARED"


@dataclass
class AgentRecord:
    agent_id: str
    role: str
    model_tier: str
    state: AgentState = AgentState.READY
    connection_state: ConnectionState = ConnectionState.CONNECTED
    assigned_files: list[str] = field(default_factory=list)
    last_heartbeat: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class TaskRecord:
    task_id: str
    name: str
    description: str
    assigned_agent: Optional[str] = None
    tier: int = 1
    status: TaskStatus = TaskStatus.PENDING
    file_allowlist: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    completed_at: Optional[str] = None


@dataclass
class FileLock:
    file_path: str
    holder_agent_id: str
    lock_type: LockType = LockType.EXCLUSIVE
    acquired_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class IncidentRecord:
    incident_id: str
    session_id: str
    incident_type: str
    severity: str
    details: str
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    resolved_at: Optional[str] = None


@dataclass
class QueueTaskItem:
    item_id: str
    title: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    session_id: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


@dataclass
class TaskQueueBatch:
    batch_id: str
    tasks: list[QueueTaskItem] = field(default_factory=list)
    current_index: int = 0
    status: str = "IN_PROGRESS"
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
