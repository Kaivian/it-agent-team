"""Strict task and session contracts; paths are exact relative files."""
import re
import os
from pathlib import Path
from .file_guard import confined_path, EXCLUDED_DIRS

IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")


def identifier(value, label="identifier"):
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
        raise ValueError(f"Invalid {label}; use 1-64 letters, digits, dots, underscores or hyphens")
    return value


def validate_config(config):
    if not isinstance(config, dict) or set(config) != {"workflow", "concurrency", "timeout", "max_retries"}:
        raise ValueError("Configuration requires workflow, concurrency, timeout and max_retries")
    if config.get("workflow") not in {"small", "medium", "large"}:
        raise ValueError("workflow must be small, medium or large")
    for key, low, high in (("concurrency", 1, 32), ("timeout", 1, 86400), ("max_retries", 0, 10)):
        value = config.get(key)
        if type(value) is not int or not low <= value <= high:
            raise ValueError(f"{key} must be an integer in {low}..{high}")
    return config


def validate_tasks(tasks, workspace, existing=(), state_dir=".agent-team"):
    if not isinstance(tasks, list) or not tasks:
        raise ValueError("Tasks must be a nonempty JSON array")
    all_tasks = {t["task_id"]: t for t in existing}
    normalized = []
    for raw in tasks:
        if not isinstance(raw, dict):
            raise ValueError("Each task must be an object")
        task = dict(raw)
        tid = identifier(task.get("task_id"), "task ID")
        if tid in all_tasks:
            raise ValueError(f"Duplicate task ID: {tid}")
        for key in ("name", "description"):
            if not isinstance(task.get(key), str) or not task[key].strip():
                raise ValueError(f"Task {tid} requires {key}")
        for key in ("acceptance_criteria", "file_allowlist", "dependencies", "verification_files"):
            value = task.get(key, [] if key in {"dependencies", "verification_files"} else None)
            if not isinstance(value, list) or any(not isinstance(v, str) or not v.strip() for v in value):
                raise ValueError(f"Task {tid}: {key} must be a string array")
            if key == "acceptance_criteria" and not value:
                raise ValueError(f"Task {tid} requires acceptance criteria")
            if len(value) != len(set(value)):
                raise ValueError(f"Task {tid}: duplicate {key}")
            task[key] = value
        for field in ("file_allowlist", "verification_files"):
            paths = []
            for value in task[field]:
                if Path(value).is_absolute() or any(c in value for c in "*?["):
                    raise ValueError("Allowlists require exact workspace-relative paths")
                if os.name == "nt":
                    for part in value.replace("\\", "/").split("/"):
                        if ":" in part or part.endswith((".", " ")) or part.split(".")[0].upper() in {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}:
                            raise ValueError("Windows paths cannot use streams, reserved devices or trailing dots/spaces")
                absolute = Path(confined_path(workspace, value))
                relative = absolute.relative_to(Path(workspace).resolve()).as_posix()
                if any(part in EXCLUDED_DIRS for part in relative.split("/")[:-1]):
                    raise ValueError("Allowlist cannot include excluded runtime, Git, dependency or cache directories")
                if any(part in {".git", ".agent-team"} for part in relative.split("/")):
                    raise ValueError("Allowlist cannot include runtime state or Git metadata")
                if absolute.is_dir():
                    raise ValueError("Allowlists require files, not directories")
                state_relative = Path(state_dir).as_posix().strip("/")
                if relative == state_relative or relative.startswith(state_relative + "/"):
                    raise ValueError("Allowlist cannot include configured runtime state")
                paths.append(relative)
            if len(paths) != len(set(paths)):
                raise ValueError("Allowlist contains equivalent paths")
            task[field] = paths
        task = {key: task[key] for key in ("task_id", "name", "description", "acceptance_criteria", "file_allowlist", "dependencies", "verification_files")}
        all_tasks[tid] = task
        normalized.append(task)
    visiting, visited = set(), set()
    def visit(tid):
        if tid in visiting:
            raise ValueError("Dependency graph contains a cycle")
        if tid in visited:
            return
        if tid not in all_tasks:
            raise ValueError(f"Missing dependency: {tid}")
        visiting.add(tid)
        for dep in all_tasks[tid]["dependencies"]:
            visit(dep)
        visiting.remove(tid)
        visited.add(tid)
    for tid in all_tasks:
        visit(tid)
    return normalized
