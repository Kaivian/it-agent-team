"""Durable sessions and guarded task transitions.

This control plane dispatches envelopes. It never impersonates host agents.
SQLite is authoritative; reports are disposable exports of persisted evidence.
"""
import hashlib
import json
import os
import sqlite3
import stat
import time
import uuid
from contextlib import contextmanager, closing
from datetime import datetime, timezone
from pathlib import Path

from .file_guard import FileGuard, confined_path, EXCLUDED_DIRS
from .task_validator import identifier, validate_config, validate_tasks

ACTIVE = {"RUNNING", "VERIFYING"}
TRANSITIONS = {
    "PENDING": {"READY"}, "READY": {"RUNNING"},
    "RUNNING": {"VERIFYING", "FAILED", "BLOCKED"},
    "VERIFYING": {"RUNNING", "COMPLETED", "FAILED", "BLOCKED"},
    "FAILED": {"READY"}, "BLOCKED": {"READY"}, "COMPLETED": set(),
}
EXCLUDED = EXCLUDED_DIRS


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def snapshot(workspace, state_dir=".agent-team"):
    """Content fingerprint including untracked files and symbolic links.

    Generated dependency/cache directories are outside this evidence boundary.
    A tree scan is conservative, not attribution or OS write protection.
    """
    root = Path(workspace)
    result = {}
    for base, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = sorted(d for d in dirs if os.path.normcase(d) not in EXCLUDED and os.path.normcase(str((Path(base) / d).relative_to(root))).replace("\\", "/") != state_dir)
        for name in sorted(files + [d for d in dirs if (Path(base) / d).is_symlink()]):
            path = Path(base) / name
            relative = os.path.normcase(str(path.relative_to(root))).replace("\\", "/")
            if path.is_symlink():
                result[relative] = "link:" + os.readlink(path)
            else:
                digest = hashlib.sha256()
                with path.open("rb") as stream:
                    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                        digest.update(chunk)
                result[relative] = f"{stat.S_IMODE(path.stat().st_mode)}:" + digest.hexdigest()
    return result


def changes(before, after):
    return sorted(path for path in set(before) | set(after) if before.get(path) != after.get(path))


def scoped_snapshot(contents, allowlist):
    if allowlist is None:
        return contents
    allowed = {os.path.normcase(p).replace("\\", "/") for p in allowlist}
    return {path: digest for path, digest in contents.items() if path in allowed}


class TaskManager:
    def __init__(self, workspace, session_id, state_dir=".agent-team"):
        self.workspace = Path(workspace).resolve()
        self.session_id = identifier(session_id, "session ID")
        if Path(state_dir).is_absolute():
            raise ValueError("State directory must be workspace-relative")
        state_path = Path(confined_path(self.workspace, state_dir))
        self.state_dir = state_path.relative_to(self.workspace).as_posix()
        if any(part in EXCLUDED - {".agent-team"} for part in self.state_dir.split("/")):
            raise ValueError("State directory cannot be a reserved dependency/Git directory")
        self.directory = Path(confined_path(self.workspace, state_path / "sessions" / session_id))
        self.db_path = self.directory / "state.db"
        if not self.db_path.is_file():
            raise ValueError(f"Session does not exist: {session_id}; run init first")
        self.guard = FileGuard(workspace=self.workspace)
        with self.connect() as conn:
            schema = conn.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone()
            if not schema or schema[0] != "1":
                raise ValueError("Unsupported session schema; preserve history and create a new session")
            self.config = validate_config(json.loads(conn.execute("SELECT value FROM metadata WHERE key='config'").fetchone()[0]))
            stored_workspace = conn.execute("SELECT value FROM metadata WHERE key='workspace'").fetchone()[0]
            if os.path.normcase(stored_workspace) != os.path.normcase(str(self.workspace)):
                raise ValueError("Session belongs to a different workspace")

    @classmethod
    def initialize(cls, workspace, objective, session_id=None, state_dir=".agent-team", **options):
        root = Path(workspace).resolve()
        if Path(state_dir).is_absolute():
            raise ValueError("State directory must be workspace-relative")
        if not root.is_dir() or not isinstance(objective, str) or not objective.strip():
            raise ValueError("An existing workspace and nonempty objective are required")
        sid = identifier(session_id or uuid.uuid4().hex, "session ID")
        config = validate_config({"workflow": "small", "concurrency": 1, "timeout": 900, "max_retries": 1, **options})
        state_path = Path(confined_path(root, state_dir))
        state_relative = state_path.relative_to(root).as_posix()
        if any(part in EXCLUDED - {".agent-team"} for part in state_relative.split("/")):
            raise ValueError("State directory cannot be a reserved dependency/Git directory")
        directory = Path(confined_path(root, state_path / "sessions" / sid))
        directory.mkdir(parents=True, exist_ok=False)
        (directory / "reports").mkdir()
        with closing(sqlite3.connect(directory / "state.db")) as conn:
            conn.executescript("""
                CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE tasks(task_id TEXT PRIMARY KEY, contract TEXT NOT NULL,
                    status TEXT NOT NULL, worker TEXT, token TEXT, attempts INTEGER NOT NULL DEFAULT 0,
                    started REAL, heartbeat REAL, baseline TEXT, result TEXT);
                CREATE TABLE checks(check_id TEXT PRIMARY KEY, task_id TEXT NOT NULL,
                    token TEXT NOT NULL, receipt TEXT NOT NULL);
                CREATE TABLE events(event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL, task_id TEXT, action TEXT NOT NULL, details TEXT NOT NULL);
            """)
            for key, value in {"config": json.dumps(config), "workspace": str(root), "objective": objective,
                               "created_at": utc_now(), "schema_version": "1"}.items():
                conn.execute("INSERT INTO metadata VALUES (?,?)", (key, value))
            conn.execute("INSERT INTO events(timestamp,action,details) VALUES (?,?,?)",
                         (utc_now(), "INITIALIZED", json.dumps(config)))
            conn.commit()
        return cls(root, sid, state_relative)

    @contextmanager
    def connect(self, write=False):
        confined_path(self.workspace, self.db_path)
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout=30000")
        conn.execute("PRAGMA synchronous=FULL")
        conn.execute("ATTACH DATABASE ? AS coordination", (str(self.guard.db_path),))
        try:
            if write:
                conn.execute("BEGIN IMMEDIATE")
            yield conn
            conn.commit()
        except BaseException:
            conn.rollback()
            raise
        finally:
            conn.close()

    def owner(self, task_id):
        return f"{self.state_dir}:{self.session_id}:{task_id}"

    @staticmethod
    def event(conn, task_id, action, details):
        conn.execute("INSERT INTO events(timestamp,task_id,action,details) VALUES (?,?,?,?)",
                     (utc_now(), task_id, action, json.dumps(details)))

    def transition(self, conn, row, target, details=None):
        if target not in TRANSITIONS[row["status"]]:
            raise ValueError(f"Invalid transition: {row['status']} -> {target}")
        conn.execute("UPDATE tasks SET status=? WHERE task_id=?", (target, row["task_id"]))
        self.event(conn, row["task_id"], "TRANSITION", {"from": row["status"], "to": target, **(details or {})})

    def add_tasks(self, tasks):
        with self.connect(write=True) as conn:
            existing = [json.loads(r[0]) for r in conn.execute("SELECT contract FROM tasks")]
            normalized = validate_tasks(tasks, self.workspace, existing, self.state_dir)
            for task in normalized:
                conn.execute("INSERT INTO tasks(task_id,contract,status) VALUES (?,?,'PENDING')",
                             (task["task_id"], json.dumps(task)))
                self.event(conn, task["task_id"], "ADDED", task)
            self.refresh(conn)
        return normalized

    def refresh(self, conn):
        rows = conn.execute("SELECT * FROM tasks ORDER BY rowid").fetchall()
        states = {r["task_id"]: r["status"] for r in rows}
        for row in rows:
            dependencies = json.loads(row["contract"])["dependencies"]
            if row["status"] == "PENDING" and all(states.get(d) == "COMPLETED" for d in dependencies):
                self.transition(conn, row, "READY")

    def claim(self, worker):
        identifier(worker, "worker ID")
        with self.connect(write=True) as conn:
            self.refresh(conn)
            active = conn.execute("SELECT * FROM tasks WHERE status IN ('RUNNING','VERIFYING')").fetchall()
            if any(row["worker"] == worker for row in active):
                raise ValueError("Worker already owns an active task in this session")
            if len(active) >= self.config["concurrency"]:
                return None
            for row in conn.execute("SELECT * FROM tasks WHERE status='READY' ORDER BY rowid").fetchall():
                task = json.loads(row["contract"])
                conn.execute("SAVEPOINT claim_files")
                scope = self.verification_scope(conn, task)
                modes = {path: "SHARED" for path in (scope or [])}
                modes.update({path: "EXCLUSIVE" for path in task["file_allowlist"]})
                acquired = all(FileGuard.acquire_in(conn, confined_path(self.workspace, path), self.owner(row["task_id"]),
                                                    kind, "coordination.file_locks")
                               for path, kind in sorted(modes.items()))
                if not acquired:
                    conn.execute("ROLLBACK TO claim_files")
                    conn.execute("RELEASE claim_files")
                    continue
                conn.execute("RELEASE claim_files")
                baseline, token, now = snapshot(self.workspace, self.state_dir), uuid.uuid4().hex, time.time()
                self.transition(conn, row, "RUNNING", {"worker": worker})
                conn.execute("UPDATE tasks SET worker=?, token=?, attempts=attempts+1, started=?, heartbeat=?, baseline=?, result=NULL WHERE task_id=?",
                             (worker, token, now, now, json.dumps(baseline), row["task_id"]))
                return {"task": task, "worker": worker, "token": token, "session": self.session_id,
                        "workspace": str(self.workspace), "attempt": row["attempts"] + 1,
                        "adapter": "host-mediated", "workflow": self.config["workflow"],
                        "instructions": "Use the host's real worker API or execute serially. Read the role definition. Run checks through this runtime before submitting. No worker was spawned by this command."}
        return None

    @staticmethod
    def verification_scope(conn, task):
        """Own outputs, declared read inputs and transitive dependency outputs.

        An unscoped read-only check fingerprints the complete auditable tree.
        Hosts should declare inputs or add a final integration task depending on
        every worker to avoid stale final verification.
        """
        paths = set(task["file_allowlist"]) | set(task.get("verification_files", []))
        visited = set()
        def inputs(contract):
            paths.update(contract["file_allowlist"])
            paths.update(contract.get("verification_files", []))
            for dependency in contract["dependencies"]:
                if dependency in visited:
                    continue
                visited.add(dependency)
                row = conn.execute("SELECT contract FROM tasks WHERE task_id=?", (dependency,)).fetchone()
                inputs(json.loads(row[0]))
        inputs(task)
        return sorted(paths) if paths else None

    def active_task(self, conn, task_id, worker, token):
        row = conn.execute("SELECT * FROM tasks WHERE task_id=?", (task_id,)).fetchone()
        if not row or row["status"] not in ACTIVE:
            raise ValueError("Task must be RUNNING or VERIFYING")
        if row["worker"] != worker or row["token"] != token:
            raise ValueError("Worker or attempt token does not match")
        if time.time() - row["heartbeat"] > self.config["timeout"]:
            raise ValueError("Task lease expired; confirm worker stopped and recover explicitly")
        return row

    def heartbeat(self, task_id, worker, token):
        with self.connect(write=True) as conn:
            self.active_task(conn, task_id, worker, token)
            conn.execute("UPDATE tasks SET heartbeat=? WHERE task_id=?", (time.time(), task_id))
            self.event(conn, task_id, "HEARTBEAT", {"worker": worker})
        return {"task_id": task_id, "heartbeat": utc_now()}

    def submit(self, task_id, worker, token, result):
        if not isinstance(result, dict) or result.get("status") not in {"completed", "failed", "blocked"}:
            raise ValueError("Result status must be completed, failed or blocked")
        for field in ("changed_files", "check_ids"):
            if not isinstance(result.get(field), list) or any(not isinstance(x, str) for x in result[field]):
                raise ValueError(f"Result requires a {field} string array")
        if not isinstance(result.get("summary"), str) or not result["summary"].strip():
            raise ValueError("Result requires a nonempty summary")
        with self.connect(write=True) as conn:
            row = self.active_task(conn, task_id, worker, token)
            if row["status"] != "RUNNING":
                raise ValueError("Wait for the active check to finish before submitting")
            contract = json.loads(row["contract"])
            current = snapshot(self.workspace, self.state_dir)
            allowed = {os.path.normcase(p).replace("\\", "/") for p in contract["file_allowlist"]}
            workspace_changes = changes(json.loads(row["baseline"]), current)
            observed = sorted(set(workspace_changes) & allowed)
            # Parallel cooperative workers own disjoint files. We can detect
            # unassigned edits but cannot attribute a write into a peer's file.
            # This boundary is stated in reports; use isolated workspaces for
            # stronger attribution. Never trust submitted changed_files alone.
            peer_paths = set()
            for peer in conn.execute("SELECT contract FROM tasks WHERE task_id<>? AND attempts>0", (task_id,)):
                peer_paths.update(os.path.normcase(p).replace("\\", "/") for p in json.loads(peer[0])["file_allowlist"])
            reported = {os.path.normcase(str(Path(confined_path(self.workspace, p)).relative_to(self.workspace))).replace("\\", "/")
                        for p in result["changed_files"]}
            reasons = []
            unauthorized = set(workspace_changes) - allowed - peer_paths
            if unauthorized or reported - allowed:
                reasons.append("Workspace changes outside assigned allowlists: " + ", ".join(sorted(unauthorized | (reported - allowed))))
            if reported != set(observed):
                reasons.append("changed_files does not match observed workspace changes")
            receipts = []
            for check_id in result["check_ids"]:
                check = conn.execute("SELECT receipt FROM checks WHERE check_id=? AND task_id=? AND token=?", (check_id, task_id, token)).fetchone()
                if not check:
                    reasons.append(f"Unknown check receipt: {check_id}")
                else:
                    receipts.append(json.loads(check[0]))
            if result["status"] == "completed":
                all_receipts = [json.loads(c[0]) for c in conn.execute("SELECT receipt FROM checks WHERE task_id=? AND token=? ORDER BY rowid", (task_id, token))]
                latest_by_command = {}
                for receipt in all_receipts:
                    latest_by_command[json.dumps(receipt["command"])] = receipt
                latest = list(latest_by_command.values())
                if not receipts or any(r["exit_code"] != 0 for r in receipts):
                    reasons.append("Completion requires runtime check receipts with successful exit codes")
                if any(r["exit_code"] != 0 for r in latest):
                    reasons.append("An executed check still fails; rerun it successfully before completion")
                current_scope = scoped_snapshot(current, self.verification_scope(conn, contract))
                if any(r["after"] != current_scope or r["before"] != current_scope for r in receipts + latest):
                    reasons.append("Checks must verify current contents without mutating the workspace")
            if row["status"] == "RUNNING":
                self.transition(conn, row, "VERIFYING")
                row = conn.execute("SELECT * FROM tasks WHERE task_id=?", (task_id,)).fetchone()
            target = "FAILED" if reasons else result["status"].upper()
            final = {**result, "status": target, "observed_changed_files": observed, "verification_errors": reasons,
                     "peer_assigned_workspace_changes": sorted(set(workspace_changes) & peer_paths - allowed),
                     "completed_at": utc_now(), "evidence_source": "runtime-executed argv checks"}
            self.transition(conn, row, target, {"verification_errors": reasons})
            conn.execute("UPDATE tasks SET result=? WHERE task_id=?", (json.dumps(final), task_id))
            conn.execute("DELETE FROM coordination.file_locks WHERE holder_agent_id=?", (self.owner(task_id),))
            self.refresh(conn)
            return final

    def status(self):
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM tasks ORDER BY rowid").fetchall()
            items = []
            for row in rows:
                items.append({**json.loads(row["contract"]), "status": row["status"], "worker": row["worker"],
                              "attempts": row["attempts"], "expired": row["status"] in ACTIVE and time.time() - row["heartbeat"] > self.config["timeout"],
                              "result": json.loads(row["result"]) if row["result"] else None})
            status = "COMPLETED" if items and all(t["status"] == "COMPLETED" for t in items) else (
                     "FAILED" if any(t["status"] == "FAILED" for t in items) else "IN_PROGRESS")
            return {"session": self.session_id, "workspace": str(self.workspace), "state_dir": self.state_dir, "config": self.config,
                    "status": status, "tasks": items}
