#!/usr/bin/env python3
"""Shared fail-fast installer for Codex and the legacy Gemini plugin registry."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from validate_package import SKILLS, load_object, validate


def run(command, *, env=None, capture=False):
    result = subprocess.run(command, env=env, text=True, capture_output=capture, check=False)
    if result.returncode:
        raise RuntimeError(f"{Path(command[0]).name} command failed (exit {result.returncode})")
    return result.stdout if capture else None


def read_gemini_config(path):
    data = load_object(path) if path.exists() else {}
    plugins = data.get("plugins", {})
    if not isinstance(plugins, dict):
        raise ValueError("Existing plugins configuration must be an object; no changes made")
    if not isinstance(plugins.get("agent-team", {}), dict):
        raise ValueError("Existing agent-team configuration must be an object; no changes made")
    return data


def enable_gemini(path):
    data = read_gemini_config(path)
    data.setdefault("plugins", {}).setdefault("agent-team", {})["enabled"] = True
    content = json.dumps(data, indent=2) + "\n"
    if path.exists() and path.read_text(encoding="utf-8-sig") == content:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=".agent-team-", delete=False) as handle:
            handle.write(content)
            temporary = Path(handle.name)
        if path.exists():
            shutil.copymode(path, temporary)
        os.replace(temporary, path)
    finally:
        if temporary and temporary.exists():
            temporary.unlink()


def deploy(target, source, update, repo_url):
    if target == source:
        if update:
            raise ValueError("--update requires a separate --target-dir; installer working tree is preserved")
        return
    if target.exists():
        if update:
            if not (target / ".git").exists():
                raise ValueError("--update requires an existing Git checkout")
            git = shutil.which("git")
            if not git:
                raise ValueError("Git is required to update a checkout")
            if run([git, "-C", str(target), "status", "--porcelain"], capture=True).strip():
                raise ValueError("Refusing to update a checkout with local changes")
            origin = run([git, "-C", str(target), "remote", "get-url", "origin"], capture=True).strip()
            if origin.rstrip("/") != repo_url.rstrip("/"):
                raise ValueError("Checkout origin differs from requested repository")
            run([git, "-C", str(target), "pull", "--ff-only"])
        return
    git = shutil.which("git")
    if not git:
        raise ValueError("Git is required to clone a checkout")
    target.parent.mkdir(parents=True, exist_ok=True)
    run([git, "clone", repo_url, str(target)])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", choices=("codex", "gemini"), default="codex")
    parser.add_argument("--target-dir", type=Path, help="Use/clone a checkout here; defaults to this package")
    parser.add_argument("--update", action="store_true", help="Fast-forward a clean separate checkout")
    parser.add_argument("--repo-url", default="https://github.com/Kaivian/it-agent-team.git")
    parser.add_argument("--config-file", type=Path, help="Legacy Gemini JSON config override")
    parser.add_argument("--skills-dir", type=Path, help="Legacy Gemini skills directory override")
    parser.add_argument("--codex-home", type=Path, help="Isolate native Codex configuration/cache")
    parser.add_argument("--skip-doctor", action="store_true")
    args = parser.parse_args(argv)
    source = Path(__file__).resolve().parent.parent
    target = (args.target_dir or source).resolve()
    env = os.environ.copy()
    if sys.version_info < (3, 10):
        parser.error("Python 3.10 or newer is required")
    try:
        if args.host == "gemini":
            if args.codex_home:
                raise ValueError("--codex-home requires --host codex")
            config = args.config_file or Path.home() / ".gemini/config/config.json"
            skills = args.skills_dir or Path.home() / ".gemini/config/skills"
            read_gemini_config(config)
        else:
            if args.config_file or args.skills_dir:
                raise ValueError("--config-file and --skills-dir require --host gemini")
            cli = shutil.which("codex")
            if not cli:
                raise ValueError("Codex CLI with plugin support is required")
            if args.codex_home:
                env["CODEX_HOME"] = str(args.codex_home.resolve())
                args.codex_home.mkdir(parents=True, exist_ok=True)
            run([cli, "plugin", "list", "--json"], env=env, capture=True)
        deploy(target, source, args.update, args.repo_url)
        failures = [item for item in validate(target) if item["status"] == "FAIL"]
        if failures:
            raise ValueError("Invalid package: " + "; ".join(item["check"] for item in failures))
        if args.host == "codex":
            run([cli, "plugin", "marketplace", "add", str(target)], env=env)
            run([cli, "plugin", "add", "agent-team@it-agent-team"], env=env)
        else:
            skills.mkdir(parents=True, exist_ok=True)
            for name in SKILLS:
                # Forward to the package instead of copying instructions with broken
                # relative runtime/role paths into a different directory tree.
                destination = skills / name
                destination.mkdir(parents=True, exist_ok=True)
                canonical = (target / "skills" / name / "SKILL.md").resolve().as_posix()
                wrapper = (f"---\nname: {name}\ndescription: Load the IT Agent Team {name} workflow from its canonical package.\n---\n\n"
                           f"Read and follow the canonical skill at `{canonical}`. Resolve its referenced files relative to that canonical file.\n")
                (destination / "SKILL.md").write_text(wrapper, encoding="utf-8")
            enable_gemini(config)
            print("[WARN] Legacy Gemini registry configured; native extension loading is unverified.")
        if not args.skip_doctor:
            command = [sys.executable, str(target / "scripts/doctor.py"), "--host", args.host]
            if args.host == "gemini":
                command += ["--config-file", str(config)]
            run(command, env=env)
        print(f"Installed agent-team for {args.host} from {target}. Open a new chat to load the skills.")
        return 0
    except (OSError, ValueError, RuntimeError) as exc:
        message = "Existing configuration contains invalid JSON; no changes made" if isinstance(exc, json.JSONDecodeError) else str(exc)
        print(f"[FAIL] {message}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
