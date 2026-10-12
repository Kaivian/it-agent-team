"""Supervisor facade with locally executed verification and durable receipts."""
import json
import subprocess
import time
import uuid
from pathlib import Path
from .file_guard import confined_path

from .task_manager import TaskManager, snapshot, scoped_snapshot, utc_now


class Supervisor(TaskManager):
    def check(self, task_id, worker, token, command):
        if not isinstance(command, list) or not command or not command[0] or any(not isinstance(v, str) or "\x00" in v for v in command):
            raise ValueError("Check requires a nonempty argv array")
        check_id = uuid.uuid4().hex
        with self.connect(write=True) as conn:
            row = self.active_task(conn, task_id, worker, token)
            if row["status"] == "VERIFYING":
                # VERIFYING is reserved to prevent two commands checking the same
                # attempt at once. Sequential checks restore RUNNING afterwards.
                raise ValueError("A check is already active for this task")
            self.transition(conn, row, "VERIFYING", {"check_id": check_id})
            conn.execute("UPDATE tasks SET heartbeat=? WHERE task_id=?", (time.time(), task_id))
            self.event(conn, task_id, "CHECK_STARTED", {"check_id": check_id, "command": command})
            scope = self.verification_scope(conn, json.loads(row["contract"]))
        before = scoped_snapshot(snapshot(self.workspace, self.state_dir), scope)
        started = utc_now()
        output = Path(confined_path(self.workspace, self.directory / "reports" / f"check-{check_id}.txt"))
        exit_code, timed_out = -1, False
        try:
            with output.open("wb") as stream:
                process = subprocess.run(command, cwd=self.workspace, stdout=stream, stderr=subprocess.STDOUT,
                                         timeout=self.config["timeout"], shell=False, check=False)
                exit_code = process.returncode
        except subprocess.TimeoutExpired:
            timed_out = True
            with output.open("ab") as stream:
                stream.write(b"\nCheck exceeded the configured timeout. Confirm all descendants stopped before recovery.\n")
        except OSError as exc:
            with output.open("ab") as stream:
                stream.write(f"\nUnable to start check: {exc}\n".encode("utf-8"))
        after = scoped_snapshot(snapshot(self.workspace, self.state_dir), scope)
        receipt = {"check_id": check_id, "command": command, "exit_code": exit_code, "timed_out": timed_out,
                   "started_at": started, "finished_at": utc_now(), "output_path": str(output), "before": before, "after": after,
                   "verification_files": scope, "full_workspace_scope": scope is None}
        with self.connect(write=True) as conn:
            row = conn.execute("SELECT * FROM tasks WHERE task_id=?", (task_id,)).fetchone()
            if row["token"] != token or row["status"] != "VERIFYING":
                raise ValueError("Attempt was recovered while checking; receipt discarded")
            conn.execute("INSERT INTO checks VALUES (?,?,?,?)", (check_id, task_id, token, json.dumps(receipt)))
            self.transition(conn, row, "BLOCKED" if timed_out else "RUNNING", {"check_id": check_id})
            if timed_out:
                conn.execute("UPDATE tasks SET result=? WHERE task_id=?", (json.dumps({"status": "BLOCKED", "summary": "Check timed out. Confirm worker and descendant processes stopped before recovering; locks retained."}), task_id))
            conn.execute("UPDATE tasks SET heartbeat=? WHERE task_id=?", (time.time(), task_id))
            self.event(conn, task_id, "CHECK_FINISHED", {"check_id": check_id, "exit_code": exit_code, "timed_out": timed_out})
        return {key: value for key, value in receipt.items() if key not in {"before", "after"}}
