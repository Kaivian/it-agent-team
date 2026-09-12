#!/usr/bin/env python3
"""
Diagnostic utility for it-agent-team plugin.
Verifies multi-platform system dependencies, manifest validity, and agent roster completeness.
Output uses [PASS], [WARN], [FAIL] tags. English only, no icons or emojis.
Returns exit code 0 on all checks passing, 1 on any critical failure.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

EXPECTED_AGENTS = [
    "supervisor-agent.md",
    "orchestrator-agent.md",
    "pm-agent.md",
    "critic-agent.md",
    "sub-coder.md",
    "qa-agent.md",
    "security-agent.md",
    "debugger-agent.md",
    "doc-refactor-agent.md",
    "devops-infra-agent.md",
]

MANIFEST_FILES = [
    "plugin.json",
    "gemini-extension.json",
    ".claude-plugins/marketplace.json",
]


class DiagnosticReport:
    def __init__(self):
        self.passes = 0
        self.warnings = 0
        self.failures = 0

    def record_pass(self, message: str) -> None:
        self.passes += 1
        print(f"[PASS] {message}")

    def record_warn(self, message: str) -> None:
        self.warnings += 1
        print(f"[WARN] {message}")

    def record_fail(self, message: str) -> None:
        self.failures += 1
        print(f"[FAIL] {message}")


def check_python(report: DiagnosticReport) -> None:
    major = sys.version_info.major
    minor = sys.version_info.minor
    micro = sys.version_info.micro
    version_str = f"{major}.{minor}.{micro}"

    if sys.version_info >= (3, 10):
        report.record_pass(f"Python version: {version_str} (>= 3.10 required)")
    else:
        report.record_fail(f"Python version: {version_str} is below minimum requirement 3.10")


def check_sqlite(report: DiagnosticReport) -> None:
    try:
        import sqlite3

        conn = sqlite3.connect(":memory:")
        cursor = conn.cursor()
        cursor.execute("SELECT 1;")
        cursor.fetchone()
        conn.close()
        report.record_pass(f"SQLite3: Available (SQLite engine {sqlite3.sqlite_version})")
    except Exception as exc:
        report.record_fail(f"SQLite3: Failed to initialize ({exc})")


def check_git(report: DiagnosticReport) -> None:
    git_bin = shutil.which("git")
    if not git_bin:
        report.record_fail("Git CLI: git executable not found in system PATH")
        return

    try:
        result = subprocess.run(
            [git_bin, "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            version_str = result.stdout.strip()
            report.record_pass(f"Git CLI: Available ({version_str})")
        else:
            report.record_fail(f"Git CLI: Execution returned code {result.returncode}")
    except Exception as exc:
        report.record_fail(f"Git CLI: Failed to execute git command ({exc})")


def check_manifests(root_dir: Path, report: DiagnosticReport) -> None:
    for rel_path in MANIFEST_FILES:
        target_path = root_dir / rel_path
        if not target_path.exists():
            report.record_fail(f"Manifest: {rel_path} not found at {target_path}")
            continue

        try:
            content = target_path.read_text(encoding="utf-8")
            data = json.loads(content)
            if not isinstance(data, dict):
                report.record_fail(f"Manifest: {rel_path} root JSON element must be an object")
            else:
                report.record_pass(f"Manifest: {rel_path} is valid JSON")
        except json.JSONDecodeError as err:
            report.record_fail(f"Manifest: {rel_path} invalid JSON syntax: {err}")
        except Exception as exc:
            report.record_fail(f"Manifest: {rel_path} read error: {exc}")


def check_agent_roster(root_dir: Path, report: DiagnosticReport) -> None:
    agents_dir = root_dir / "agents"
    if not agents_dir.exists() or not agents_dir.is_dir():
        report.record_fail(f"Agent roster: Directory agents/ not found at {agents_dir}")
        return

    missing_agents = []
    empty_agents = []

    for agent_file in EXPECTED_AGENTS:
        agent_path = agents_dir / agent_file
        if not agent_path.exists():
            missing_agents.append(agent_file)
        elif agent_path.stat().st_size == 0:
            empty_agents.append(agent_file)

    if missing_agents:
        report.record_fail(
            f"Agent roster: Missing {len(missing_agents)}/{len(EXPECTED_AGENTS)} agent file(s): "
            f"{', '.join(missing_agents)}"
        )
    else:
        report.record_pass(
            f"Agent roster: All {len(EXPECTED_AGENTS)} agent definition files exist in agents/"
        )

    if empty_agents:
        report.record_warn(
            f"Agent roster: {len(empty_agents)} agent file(s) are 0 bytes: {', '.join(empty_agents)}"
        )


def check_config(report: DiagnosticReport) -> None:
    config_path = Path.home() / ".gemini" / "config" / "config.json"
    if not config_path.exists():
        report.record_warn(
            f"Configuration: {config_path} not found. Run installer or create configuration."
        )
        return

    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
        plugins = data.get("plugins", {})
        agent_team_plugin = plugins.get("agent-team", {})
        if agent_team_plugin.get("enabled") is True:
            report.record_pass("Configuration: Plugin agent-team is enabled in ~/.gemini/config/config.json")
        else:
            report.record_warn("Configuration: Plugin agent-team is not enabled in ~/.gemini/config/config.json")
    except Exception as exc:
        report.record_warn(f"Configuration: Could not parse {config_path}: {exc}")


def check_platform(report: DiagnosticReport) -> None:
    import platform
    os_name = platform.system()
    arch = platform.machine()
    report.record_pass(f"OS Platform: {os_name} ({arch}) - Multi-platform support active")

    detected_clis = []
    for cli_name, label in [
        ("agy", "Google Antigravity CLI (agy)"),
        ("gemini", "Gemini CLI"),
        ("claude", "Claude Code"),
        ("cursor", "Cursor IDE"),
        ("code", "VS Code"),
    ]:
        if shutil.which(cli_name):
            detected_clis.append(label)

    if detected_clis:
        report.record_pass(f"Detected Agent Environment(s): {', '.join(detected_clis)}")
    else:
        report.record_pass("Agent Runtime: Compatible with Antigravity, Claude Code, Cursor, and CLI agents")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Doctor diagnostic script for it-agent-team plugin."
    )
    parser.add_argument(
        "--root",
        type=str,
        default=None,
        help="Path to the plugin root directory (default: parent directory of scripts/)",
    )
    args = parser.parse_args()

    if args.root:
        root_dir = Path(args.root).resolve()
    else:
        root_dir = Path(__file__).resolve().parent.parent

    print("==================================================")
    print("IT Agent Team: Doctor Diagnostic")
    print(f"Plugin Root: {root_dir}")
    print("==================================================")

    report = DiagnosticReport()

    # Multi-platform and system prerequisite checks
    check_platform(report)
    check_python(report)
    check_sqlite(report)
    check_git(report)

    # Manifest and file structure checks
    check_manifests(root_dir, report)
    check_agent_roster(root_dir, report)

    # Configuration status check
    check_config(report)

    print("--------------------------------------------------")
    print(
        f"Diagnostic Summary: {report.passes} passed, "
        f"{report.warnings} warnings, {report.failures} failures"
    )
    if report.failures == 0:
        print("Status: HEALTHY (Exit Code 0)")
        print("==================================================")
        return 0
    else:
        print("Status: UNHEALTHY (Exit Code 1)")
        print("==================================================")
        return 1


if __name__ == "__main__":
    sys.exit(main())
