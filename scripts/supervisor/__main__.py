"""JSON command-line control plane. Set PYTHONPATH to the plugin scripts path."""
import argparse
import json
import sqlite3
import sys
from pathlib import Path
from .supervisor import Supervisor
from .recovery_manager import recover
from .reporting import generate_report


def parser():
    root = argparse.ArgumentParser(description=__doc__)
    root.add_argument("--workspace", required=True, type=Path)
    root.add_argument("--session")
    root.add_argument("--compact", action="store_true", help="Emit JSON without indentation; place before the subcommand")
    root.add_argument("--state-dir", default=".agent-team", help="Workspace-relative state directory; .gemini preserves legacy placement")
    commands = root.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init")
    init.add_argument("--objective", required=True)
    init.add_argument("--workflow", choices=("small", "medium", "large"), default="small")
    init.add_argument("--concurrency", type=int, default=1)
    init.add_argument("--timeout", type=int, default=900)
    init.add_argument("--max-retries", type=int, default=1)
    add = commands.add_parser("add")
    add.add_argument("--tasks", type=Path, required=True)
    claim = commands.add_parser("claim")
    claim.add_argument("--worker", required=True)
    for name in ("check", "submit", "heartbeat"):
        command = commands.add_parser(name)
        command.add_argument("--task", required=True)
        command.add_argument("--worker", required=True)
        command.add_argument("--token", required=True)
        if name == "check":
            command.add_argument("argv", nargs=argparse.REMAINDER)
        elif name == "submit":
            command.add_argument("--result", type=Path, required=True)
    status = commands.add_parser("status")
    status.add_argument("--summary", action="store_true", help="Omit repeated contracts and results; retain scheduling and failure signals")
    commands.add_parser("report")
    recovery = commands.add_parser("recover")
    recovery.add_argument("--task", required=True)
    recovery.add_argument("--confirm-worker-stopped", action="store_true")
    recovery.add_argument("--retry", action="store_true")
    return root


def summarize_status(status):
    """Project a status response without changing persisted state or reports."""
    tasks = []
    counts = {}
    for task in status["tasks"]:
        counts[task["status"]] = counts.get(task["status"], 0) + 1
        item = {key: task[key] for key in ("task_id", "status", "worker", "attempts", "expired", "dependencies")}
        errors = (task.get("result") or {}).get("verification_errors")
        if errors:
            item["verification_errors"] = errors
        tasks.append(item)
    return {"session": status["session"], "status": status["status"], "counts": counts, "tasks": tasks}


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.command == "init":
            manager = Supervisor.initialize(args.workspace, args.objective, args.session, workflow=args.workflow,
                                            concurrency=args.concurrency, timeout=args.timeout, max_retries=args.max_retries,
                                            state_dir=args.state_dir)
            result = {"session": manager.session_id, "state_db": str(manager.db_path), "config": manager.config}
        else:
            if not args.session:
                raise ValueError("--session is required after init")
            manager = Supervisor(args.workspace, args.session, args.state_dir)
            if args.command == "add":
                result = manager.add_tasks(json.loads(args.tasks.read_text(encoding="utf-8-sig")))
            elif args.command == "claim":
                result = manager.claim(args.worker)
            elif args.command == "check":
                command = args.argv[1:] if args.argv[:1] == ["--"] else args.argv
                result = manager.check(args.task, args.worker, args.token, command)
            elif args.command == "submit":
                result = manager.submit(args.task, args.worker, args.token, json.loads(args.result.read_text(encoding="utf-8-sig")))
            elif args.command == "heartbeat":
                result = manager.heartbeat(args.task, args.worker, args.token)
            elif args.command == "status":
                result = manager.status()
                if args.summary:
                    result = summarize_status(result)
            elif args.command == "report":
                result = generate_report(manager)
            else:
                result = recover(manager, args.task, args.confirm_worker_stopped, args.retry)
        formatting = {"separators": (",", ":")} if args.compact else {"indent": 2}
        print(json.dumps(result, **formatting))
        if args.command == "check" and result["exit_code"] != 0:
            return 1
        if args.command == "submit" and result["status"] == "FAILED":
            return 1
        return 0
    except (ValueError, OSError, sqlite3.Error) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
