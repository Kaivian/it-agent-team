"""Explicit recovery; never replay commands or free a live worker's locks."""
import json
from .task_manager import ACTIVE, utc_now


def recover(manager, task_id, confirm_worker_stopped=False, retry=False):
    if not confirm_worker_stopped:
        raise ValueError("Recovery requires explicit confirmation that the worker and its check processes stopped")
    with manager.connect(write=True) as conn:
        row = conn.execute("SELECT * FROM tasks WHERE task_id=?", (task_id,)).fetchone()
        if not row or row["status"] not in ACTIVE | {"FAILED", "BLOCKED"}:
            raise ValueError("Only active, failed or blocked tasks can be recovered")
        if retry and row["attempts"] >= 1 + manager.config["max_retries"]:
            raise ValueError("Retry limit exhausted")
        prior = row["status"]
        if prior in ACTIVE:
            manager.transition(conn, row, "BLOCKED", {"reason": "Operator confirmed worker stopped"})
            interruption = {"status": "BLOCKED", "summary": "Interrupted attempt; inspect workspace before retry",
                            "completed_at": utc_now(), "attempt": row["attempts"]}
            conn.execute("UPDATE tasks SET result=? WHERE task_id=?", (json.dumps(interruption), task_id))
        manager.event(conn, task_id, "RECOVERED", {"prior_status": prior, "previous_worker": row["worker"],
                                                  "previous_token": row["token"], "attempt": row["attempts"],
                                                  "previous_result": json.loads(row["result"]) if row["result"] else None,
                                                  "retry_requested": retry})
        conn.execute("DELETE FROM coordination.file_locks WHERE holder_agent_id=?", (manager.owner(task_id),))
        conn.execute("UPDATE tasks SET worker=NULL, token=NULL WHERE task_id=?", (task_id,))
        if retry:
            row = conn.execute("SELECT * FROM tasks WHERE task_id=?", (task_id,)).fetchone()
            manager.transition(conn, row, "READY", {"reason": "Explicit retry; no commands replayed"})
    return {"task_id": task_id, "status": "READY" if retry else ("BLOCKED" if prior in ACTIVE else prior), "automatic_replay": False}
