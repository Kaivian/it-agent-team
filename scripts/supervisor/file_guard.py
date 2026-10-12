"""Cooperative workspace-wide SQLite locks shared by separate processes.

Locks are not OS write protection. Crashed owners are retained until an
operator confirms they stopped. Callers must participate in this protocol.
"""
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from .models import LockType

EXCLUDED_DIRS = {".git", ".agent-team", "node_modules", ".venv", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}


def confined_path(workspace, path):
    root = Path(workspace).resolve()
    target = (root / path).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"Path escapes workspace: {path}") from exc
    if target == root:
        raise ValueError("A file path is required")
    return os.path.normcase(str(target))


class FileGuard:
    def __init__(self, db_path=None, workspace=None):
        self.workspace = Path(workspace or Path.cwd()).resolve()
        default_db = confined_path(self.workspace, ".agent-team/locks.db")
        self.db_path = Path(confined_path(self.workspace, db_path or default_db))
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS file_locks (
                file_path TEXT NOT NULL, holder_agent_id TEXT NOT NULL,
                lock_type TEXT NOT NULL, PRIMARY KEY(file_path, holder_agent_id))""")

    @contextmanager
    def _connect(self):
        confined_path(self.workspace, self.db_path)
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.execute("PRAGMA busy_timeout=30000")
        try:
            yield conn
            conn.commit()
        except BaseException:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _normalize_path(self, path):
        return confined_path(self.workspace, path)

    @staticmethod
    def acquire_in(conn, path, owner, kind, table="file_locks"):
        kind = LockType(kind).value
        if not isinstance(owner, str) or not owner.strip():
            raise ValueError("Lock owner must be nonempty")
        rows = conn.execute(f"SELECT holder_agent_id, lock_type FROM {table} WHERE file_path=?", (path,)).fetchall()
        others = [(holder, mode) for holder, mode in rows if holder != owner]
        if others and (kind == "EXCLUSIVE" or any(mode == "EXCLUSIVE" for _, mode in others)):
            return False
        own = next((mode for holder, mode in rows if holder == owner), None)
        mode = "EXCLUSIVE" if own == "EXCLUSIVE" else kind
        conn.execute(f"INSERT OR REPLACE INTO {table} VALUES (?,?,?)", (path, owner, mode))
        return True

    def acquire_lock(self, file_path, agent_id, lock_type=LockType.EXCLUSIVE):
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            return self.acquire_in(conn, self._normalize_path(file_path), agent_id, lock_type)

    def release_lock(self, file_path, agent_id):
        with self._connect() as conn:
            return conn.execute("DELETE FROM file_locks WHERE file_path=? AND holder_agent_id=?",
                                (self._normalize_path(file_path), agent_id)).rowcount > 0

    def release_all_for_agent(self, agent_id):
        with self._connect() as conn:
            return conn.execute("DELETE FROM file_locks WHERE holder_agent_id=?", (agent_id,)).rowcount

    def get_lock_holders(self, file_path):
        with self._connect() as conn:
            return [row[0] for row in conn.execute("SELECT holder_agent_id FROM file_locks WHERE file_path=? ORDER BY holder_agent_id",
                                                 (self._normalize_path(file_path),))]

    def is_locked(self, file_path):
        return bool(self.get_lock_holders(file_path))

    def get_lock_holder(self, file_path):
        holders = self.get_lock_holders(file_path)
        return holders[0] if holders else None
