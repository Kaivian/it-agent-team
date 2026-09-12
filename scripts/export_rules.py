#!/usr/bin/env python3
"""
Universal multi-platform rule exporter for IT Agent Team.
Exports team rules and operational invariants to any target project repository
for compatibility across Google Antigravity, Claude Code, Cursor, Windsurf, and GitHub Copilot.

Output uses [PASS], [WARN], [FAIL] tags. English only, no icons or emojis.
"""

import argparse
import shutil
import sys
from pathlib import Path


def export_rules(source_rules: Path, target_repo: Path, platforms: list[str]) -> int:
    if not source_rules.exists():
        print(f"[FAIL] Source rules not found at: {source_rules}")
        return 1

    rule_content = source_rules.read_text(encoding="utf-8")
    target_repo = target_repo.resolve()
    target_repo.mkdir(parents=True, exist_ok=True)

    print(f"Exporting IT Agent Team rules to project: {target_repo}")
    print("Platforms selected:", ", ".join(platforms))
    print("--------------------------------------------------")

    success_count = 0

    # 1. Universal AGENTS.md (Root and .agent/rules)
    if "universal" in platforms or "all" in platforms:
        dest_root = target_repo / "AGENTS.md"
        dest_agent = target_repo / ".agent" / "rules" / "AGENTS.md"
        dest_agents = target_repo / ".agents" / "rules" / "AGENTS.md"

        dest_root.write_text(rule_content, encoding="utf-8")
        dest_agent.parent.mkdir(parents=True, exist_ok=True)
        dest_agent.write_text(rule_content, encoding="utf-8")
        dest_agents.parent.mkdir(parents=True, exist_ok=True)
        dest_agents.write_text(rule_content, encoding="utf-8")
        print("  [PASS] Universal Agent standard: AGENTS.md, .agent/rules/AGENTS.md, .agents/rules/AGENTS.md")
        success_count += 1

    # 2. Claude Code (.claude/rules)
    if "claude" in platforms or "all" in platforms:
        dest_claude = target_repo / ".claude" / "rules" / "AGENTS.md"
        dest_claude.parent.mkdir(parents=True, exist_ok=True)
        dest_claude.write_text(rule_content, encoding="utf-8")
        print("  [PASS] Claude Code: .claude/rules/AGENTS.md")
        success_count += 1

    # 3. Cursor (.cursor/rules and .cursorrules)
    if "cursor" in platforms or "all" in platforms:
        cursor_dir = target_repo / ".cursor" / "rules"
        cursor_dir.mkdir(parents=True, exist_ok=True)
        cursor_file = cursor_dir / "it-agent-team.mdc"
        cursor_content = "---\ndescription: IT Agent Team Global Multi-Agent Rules and Operational Boundaries\nglobs: *\n---\n\n" + rule_content
        cursor_file.write_text(cursor_content, encoding="utf-8")

        cursorrules_root = target_repo / ".cursorrules"
        cursorrules_root.write_text(rule_content, encoding="utf-8")
        print("  [PASS] Cursor IDE: .cursor/rules/it-agent-team.mdc, .cursorrules")
        success_count += 1

    # 4. GitHub Copilot (.github/copilot-instructions.md)
    if "copilot" in platforms or "all" in platforms:
        copilot_file = target_repo / ".github" / "copilot-instructions.md"
        copilot_file.parent.mkdir(parents=True, exist_ok=True)
        copilot_file.write_text(rule_content, encoding="utf-8")
        print("  [PASS] GitHub Copilot: .github/copilot-instructions.md")
        success_count += 1

    # 5. Windsurf (.windsurfrules)
    if "windsurf" in platforms or "all" in platforms:
        windsurf_file = target_repo / ".windsurfrules"
        windsurf_file.write_text(rule_content, encoding="utf-8")
        print("  [PASS] Windsurf IDE: .windsurfrules")
        success_count += 1

    print("--------------------------------------------------")
    print(f"Export Summary: {success_count} platform integrations configured successfully.")
    print("Status: READY")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Export IT Agent Team rules to target workspace for multi-platform agent compatibility."
    )
    parser.add_argument(
        "target",
        nargs="?",
        default=".",
        help="Target project directory to install rules into (default: current directory)",
    )
    parser.add_argument(
        "--platform",
        choices=["all", "universal", "claude", "cursor", "copilot", "windsurf"],
        default="all",
        help="Target platform specification (default: all)",
    )

    args = parser.parse_args()
    root_dir = Path(__file__).resolve().parent.parent
    source_rules = root_dir / "rules" / "AGENTS.md"
    target_repo = Path(args.target).resolve()

    return export_rules(source_rules, target_repo, [args.platform])


if __name__ == "__main__":
    sys.exit(main())
