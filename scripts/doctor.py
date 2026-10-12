#!/usr/bin/env python3
"""Check package, core runtime, and selected host without modifying user config."""
import argparse
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
from validate_package import load_object, validate

CORE = ("models", "state_store", "task_queue", "file_guard", "invariants",
        "task_manager", "task_validator", "orchestrator", "supervisor",
        "reporting", "recovery_manager")


def diagnose(root, host, config_file=None, state_dir=None):
    checks = validate(root)
    def record(status, name, message):
        checks.append({"status": status, "check": name, "message": message})
    record("PASS" if sys.version_info >= (3, 10) else "FAIL", "Python", platform.python_version())
    record("PASS", "Platform", f"{platform.system()} {platform.machine()} (observed platform only)")
    try:
        import sqlite3
        with sqlite3.connect(":memory:") as db:
            db.execute("SELECT 1").fetchone()
        record("PASS", "SQLite", sqlite3.sqlite_version)
    except Exception:
        record("FAIL", "SQLite", "Could not initialize SQLite")
    record("PASS" if shutil.which("git") else "WARN", "Git", "Required only for clone/update")
    runtime = root / "scripts/supervisor"
    for name in CORE:
        path = runtime / f"{name}.py"
        if not path.exists() or not path.read_text(encoding="utf-8").strip():
            record("FAIL", f"Runtime {name}", "Required module is missing or empty")
        else:
            try:
                compile(path.read_text(encoding="utf-8"), str(path), "exec")
                record("PASS", f"Runtime {name}", "Nonempty and syntactically valid; behavior requires runtime tests")
            except SyntaxError:
                record("FAIL", f"Runtime {name}", "Invalid Python syntax")
    for path in sorted(runtime.glob("*.py")):
        if path.stem not in CORE and path.name != "__init__.py" and not path.read_text(encoding="utf-8").strip():
            record("WARN", f"Optional runtime {path.stem}", "Placeholder module; feature is not implemented")
    if state_dir:
        try:
            with tempfile.TemporaryFile(dir=state_dir) as probe:
                probe.write(b"probe")
            record("PASS", "State directory", "Writable")
        except OSError:
            record("FAIL", "State directory", "Missing or not writable")
    else:
        record("WARN", "State directory", "Not probed; use --state-dir to check an existing directory")
    if host == "codex":
        cli = shutil.which("codex")
        if not cli:
            record("FAIL", "Codex CLI", "Not found; native plugin commands are required for installation")
        else:
            try:
                result = subprocess.run([cli, "plugin", "list", "--json"], capture_output=True,
                                        text=True, timeout=30, check=False)
                if result.returncode:
                    record("FAIL", "Codex plugins", f"Native plugin list failed (exit {result.returncode}); config was not changed")
                else:
                    data = json.loads(result.stdout)
                    entries = data if isinstance(data, list) else data.get("installed", data.get("plugins", []))
                    entry = next((p for p in entries if p.get("name") == "agent-team" and p.get("marketplaceName", p.get("marketplace")) == "it-agent-team"), None)
                    confirmed = entry and entry.get("installed") is True and entry.get("enabled") is True
                    record("PASS" if confirmed else "WARN", "Codex installation", "Installed and enabled" if confirmed else "Could not confirm installed and enabled")
            except (OSError, ValueError, TypeError, AttributeError, subprocess.TimeoutExpired):
                record("FAIL", "Codex plugins", "Query failed or returned an unsupported response")
    else:
        path = config_file or Path.home() / ".gemini/config/config.json"
        try:
            data = load_object(path)
            enabled = data.get("plugins", {}).get("agent-team", {}).get("enabled") is True
            record("PASS" if enabled else "WARN", "Legacy Gemini registry", "Enabled" if enabled else "Not enabled")
        except FileNotFoundError:
            record("WARN", "Legacy Gemini registry", "Not found")
        except (OSError, ValueError, TypeError, AttributeError):
            record("FAIL", "Legacy Gemini registry", "Malformed or unreadable; no changes made")
        record("WARN", "Gemini host support", "Legacy registry only; native extension loading is unverified")
    return checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--host", choices=("codex", "gemini"), default="codex")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--config-file", type=Path, help="Legacy Gemini config override")
    parser.add_argument("--state-dir", type=Path, help="Probe an existing state directory")
    args = parser.parse_args()
    checks = diagnose(args.root.resolve(), args.host, args.config_file, args.state_dir)
    counts = {status.lower(): sum(c["status"] == status for c in checks) for status in ("PASS", "WARN", "FAIL")}
    status = "FAILED" if counts["fail"] else "WARNINGS" if counts["warn"] else "PASSED"
    if args.json:
        print(json.dumps({"host": args.host, "root": str(args.root.resolve()), "status": status,
                          "summary": counts, "checks": checks}, indent=2))
    else:
        for check in checks:
            print(f"[{check['status']}] {check['check']}: {check['message']}")
        print(f"Status: {status}; {counts['pass']} passed, {counts['warn']} warnings, {counts['fail']} failures")
    return int(bool(counts["fail"]))


if __name__ == "__main__":
    raise SystemExit(main())
