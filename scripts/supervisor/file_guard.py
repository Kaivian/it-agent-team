"""File Guard and physical concurrency lock manager for IT Agent Team."""

from pathlib import Path
from typing import Optional

from .models import FileLock, LockType


class FileGuard:
    def __init__(self):
        self._locks: dict[str, FileLock] = {}

    def _normalize_path(self, path: str) -> str:
        return str(Path(path).resolve().as_posix().lower())

    def acquire_lock(
        self,
        file_path: str,
        agent_id: str,
        lock_type: LockType = LockType.EXCLUSIVE,
    ) -> bool:
        normalized = self._normalize_path(file_path)
        existing = self._locks.get(normalized)

        if existing is None:
            self._locks[normalized] = FileLock(
                file_path=normalized,
                holder_agent_id=agent_id,
                lock_type=lock_type,
            )
            return True

        if existing.holder_agent_id == agent_id:
            return True

        if lock_type == LockType.SHARED and existing.lock_type == LockType.SHARED:
            return True

        return False

    def release_lock(self, file_path: str, agent_id: str) -> bool:
        normalized = self._normalize_path(file_path)
        existing = self._locks.get(normalized)
        if existing and existing.holder_agent_id == agent_id:
            del self._locks[normalized]
            return True
        return False

    def release_all_for_agent(self, agent_id: str) -> int:
        released = 0
        to_delete = [
            path
            for path, lock in self._locks.items()
            if lock.holder_agent_id == agent_id
        ]
        for path in to_delete:
            del self._locks[path]
            released += 1
        return released

    def is_locked(self, file_path: str) -> bool:
        return self._normalize_path(file_path) in self._locks

    def get_lock_holder(self, file_path: str) -> Optional[str]:
        lock = self._locks.get(self._normalize_path(file_path))
        return lock.holder_agent_id if lock else None
