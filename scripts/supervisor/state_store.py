"""Durable SQLite State Store for IT Agent Team supervisor."""

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional

from .models import AgentRecord, AgentState, ConnectionState, IncidentRecord, TaskRecord, TaskStatus


class StateStore:
    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            self.db_path = (
                Path.home()
                / ".gemini"
                / "config"
                / "plugins"
                / "agent-team"
                / ".agent_team"
                / "state.db"
            )
        else:
            self.db_path = Path(db_path)

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _connect(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    objective TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    status TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS agents (
                    agent_id TEXT PRIMARY KEY,
                    role TEXT NOT NULL,
                    model_tier TEXT NOT NULL,
                    state TEXT NOT NULL,
                    connection_state TEXT NOT NULL,
                    assigned_files TEXT,
                    last_heartbeat TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    assigned_agent TEXT,
                    tier INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    file_allowlist TEXT,
                    dependencies TEXT,
                    created_at TEXT NOT NULL,
                    completed_at TEXT
                );

                CREATE TABLE IF NOT EXISTS locks (
                    file_path TEXT PRIMARY KEY,
                    holder_agent_id TEXT NOT NULL,
                    lock_type TEXT NOT NULL,
                    acquired_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    source_agent TEXT NOT NULL,
                    target_agent TEXT NOT NULL,
                    action TEXT NOT NULL,
                    details TEXT,
                    status TEXT NOT NULL
                );
                """
            )

    def register_agent(self, agent: AgentRecord) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO agents (agent_id, role, model_tier, state, connection_state, assigned_files, last_heartbeat)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    agent.agent_id,
                    agent.role,
                    agent.model_tier,
                    agent.state.value,
                    agent.connection_state.value,
                    json.dumps(agent.assigned_files),
                    agent.last_heartbeat,
                ),
            )

    def get_agent(self, agent_id: str) -> Optional[AgentRecord]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM agents WHERE agent_id = ?", (agent_id,)
            ).fetchone()
            if not row:
                return None
            return AgentRecord(
                agent_id=row["agent_id"],
                role=row["role"],
                model_tier=row["model_tier"],
                state=AgentState(row["state"]),
                connection_state=ConnectionState(row["connection_state"]),
                assigned_files=json.loads(row["assigned_files"] or "[]"),
                last_heartbeat=row["last_heartbeat"],
            )

    def log_event(
        self,
        timestamp: str,
        source_agent: str,
        target_agent: str,
        action: str,
        details: str,
        status: str,
    ) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO events (timestamp, source_agent, target_agent, action, details, status)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (timestamp, source_agent, target_agent, action, details, status),
            )
            return cursor.lastrowid
