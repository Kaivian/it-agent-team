#!/usr/bin/env python3
"""Validate the supported package contract without third-party dependencies.

This validates the fields used by this package; it is not a general JSON Schema
validator. Host parsing is separately verified with the native Codex CLI.
"""
import argparse
import json
import re
from pathlib import Path

SKILLS = ("agent-team", "agent-team-auto", "agent-team-batch", "agent-team-auto-batch")
AGENTS = ("supervisor-agent", "orchestrator-agent", "pm-agent", "critic-agent",
          "sub-coder", "qa-agent", "security-agent", "debugger-agent",
          "doc-refactor-agent", "devops-infra-agent", "user-proxy-agent",
          "task-dispatcher-agent")


def load_object(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError(f"{path.name}: JSON root must be an object")
    return data


def package_path(root: Path, value: str) -> Path:
    if not isinstance(value, str) or not value.startswith("./"):
        raise ValueError("Package paths must start with ./")
    path = (root / value).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("Package path escapes the package root")
    if not path.exists():
        raise ValueError(f"Missing package path: {value}")
    return path


def validate(root: Path) -> list[dict]:
    checks = []

    def run(name, action):
        try:
            action()
            checks.append({"status": "PASS", "check": name, "message": "Valid"})
        except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
            checks.append({"status": "FAIL", "check": name, "message": str(exc)})

    def manifest():
        data = load_object(root / "plugin.json")
        if data.get("name") != "agent-team":
            raise ValueError("Expected name agent-team")
        if not re.fullmatch(r"\d+\.\d+\.\d+(?:[-+][A-Za-z0-9.-]+)?", str(data.get("version", ""))):
            raise ValueError("version must be a semantic version")
        if data.get("$schema") != "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json":
            raise ValueError("Expected portable Agent Plugins schema")
        for field in ("description", "repository", "license"):
            if not isinstance(data.get(field), str) or not data[field].strip():
                raise ValueError(f"{field} must be a nonempty string")
        if not isinstance(data.get("author"), dict) or not data["author"].get("name"):
            raise ValueError("author.name is required")
        if any(key in data for key in ("agents", "skills", "scripts")):
            raise ValueError("Use portable component discovery, not unsupported top-level component fields")
        interface = data["extensions"]["com.openai"]["interface"]
        if not interface.get("displayName") or interface.get("category") != "Productivity":
            raise ValueError("OpenAI interface requires displayName and Productivity category")

    def gemini():
        data = load_object(root / "gemini-extension.json")
        canonical = load_object(root / "plugin.json")
        for key in ("name", "version", "description"):
            if data.get(key) != canonical.get(key):
                raise ValueError(f"Gemini {key} differs from plugin.json")
        package_path(root, "./" + data["entrypoint"])

    def catalog(codex):
        path = ".agents/plugins/marketplace.json" if codex else ".claude-plugins/marketplace.json"
        data = load_object(root / path)
        canonical = load_object(root / "plugin.json")
        if data.get("name") != "it-agent-team":
            raise ValueError("Expected marketplace name it-agent-team")
        entries = data.get("plugins")
        if not isinstance(entries, list) or len(entries) != 1:
            raise ValueError("Expected exactly one plugin")
        entry = entries[0]
        if entry.get("name") != canonical["name"]:
            raise ValueError("Plugin name differs from plugin.json")
        if codex:
            if entry.get("source", {}).get("source") != "local":
                raise ValueError("Expected local marketplace source")
            if package_path(root, entry["source"]["path"]) != root.resolve():
                raise ValueError("Expected repository-root plugin source")
            if entry.get("policy") != {"installation": "AVAILABLE", "authentication": "ON_USE"}:
                raise ValueError("Expected AVAILABLE / ON_USE policy")
            if entry.get("category") != "Productivity":
                raise ValueError("Expected Productivity category")
        else:
            for key in ("version", "description"):
                if entry.get(key) != canonical[key]:
                    raise ValueError(f"Legacy marketplace {key} differs from plugin.json")
            package_path(root, entry["source"])

    def skill(name):
        text = (root / "skills" / name / "SKILL.md").read_text(encoding="utf-8-sig")
        lines = text.splitlines()
        if not lines or lines[0] != "---" or "---" not in lines[1:]:
            raise ValueError("Missing skill frontmatter")
        end = lines.index("---", 1)
        fields = {}
        for line in lines[1:end]:
            if ":" in line and not line.startswith(" "):
                key, value = line.split(":", 1)
                fields[key] = value.strip().strip('"\'')
        if fields.get("name") != name:
            raise ValueError("Skill frontmatter name differs from its directory")
        if not fields.get("description") or fields["description"] in ("|", ">"):
            raise ValueError("A nonempty scalar description is required")
        if not "\n".join(lines[end + 1:]).strip():
            raise ValueError("Skill body is empty")

    run("plugin.json", manifest)
    run("gemini-extension.json", gemini)
    run("Codex marketplace", lambda: catalog(True))
    run("Legacy marketplace", lambda: catalog(False))
    for name in SKILLS:
        run(f"Skill {name}", lambda name=name: skill(name))
    for name in AGENTS:
        def role(name=name):
            if not (root / "agents" / f"{name}.md").read_text(encoding="utf-8").strip():
                raise ValueError("Agent definition is empty")
        run(f"Role {name}", role)
    run("License", lambda: package_path(root, "./LICENSE"))
    return checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    checks = validate(args.root.resolve())
    if args.json:
        print(json.dumps({"checks": checks}, indent=2))
    else:
        for check in checks:
            print(f"[{check['status']}] {check['check']}: {check['message']}")
    return int(any(check["status"] == "FAIL" for check in checks))


if __name__ == "__main__":
    raise SystemExit(main())
