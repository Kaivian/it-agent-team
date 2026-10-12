"""Readable exports from authoritative session state, including check evidence."""
import json
import os
import uuid
from pathlib import Path
from .file_guard import confined_path
from .task_manager import EXCLUDED


def atomic_write(path, content):
    temporary = path.with_name(path.name + f".{uuid.uuid4().hex}.tmp")
    try:
        temporary.write_text(content, encoding="utf-8")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def generate_report(manager):
    report = manager.status()
    report["snapshot_excluded_directories"] = sorted(EXCLUDED | {manager.state_dir})
    with manager.connect() as conn:
        report["checks"] = [{key: value for key, value in json.loads(row[0]).items() if key not in {"before", "after"}}
                            for row in conn.execute("SELECT receipt FROM checks ORDER BY rowid")]
        events = [dict(row) for row in conn.execute("SELECT * FROM events ORDER BY event_id")]
    report["verification_boundary"] = "Runtime-executed argv checks and task-scoped content fingerprints, plus workspace snapshots detecting changes outside assigned task allowlists. Parallel peer-file changes are cooperatively attributed by ownership, not independently to a process. Locks do not enforce OS permissions; excluded dependency/cache/Git/runtime directories are not audited."
    json_path = Path(confined_path(manager.workspace, manager.directory / "reports" / "summary.json"))
    md_path = Path(confined_path(manager.workspace, manager.directory / "reports" / "summary.md"))
    atomic_write(json_path, json.dumps(report, indent=2) + "\n")
    lines = [f"# Session {manager.session_id}", "", f"Status: {report['status']}", "", report["verification_boundary"], ""]
    for task in report["tasks"]:
        lines.extend([f"## {task['task_id']}: {task['name']}", "", f"Status: {task['status']}; attempts: {task['attempts']}", ""])
        if task["result"]:
            lines.extend([task["result"]["summary"], ""])
            lines.extend(f"- {error}" for error in task["result"].get("verification_errors", []))
            lines.append("")
    lines.extend(["## Check receipts", ""])
    for receipt in report["checks"]:
        lines.append(f"- `{receipt['check_id']}`: exit {receipt['exit_code']}; output: `{receipt['output_path']}`")
    atomic_write(md_path, "\n".join(lines) + "\n")
    event_path = Path(confined_path(manager.workspace, manager.directory / "events.jsonl"))
    atomic_write(event_path, "".join(json.dumps(event) + "\n" for event in events))
    return {"session": manager.session_id, "status": report["status"], "json_report": str(json_path), "markdown_report": str(md_path)}
