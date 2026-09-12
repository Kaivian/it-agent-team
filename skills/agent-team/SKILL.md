---
name: agent-team
description: Coordinates the elite multi-agent team workflow for complex or heavy software development tasks with central Supervisor control plane, dynamic sub-coding agents, QA review and testing, and debugger feedback loop.
argument-hint: ["[task-description] [--auto] [--concurrency <N>] [--dry-run]"]
---

# /agent-team

Activate the multi-agent autonomous engineering team for end-to-end task execution.

## Usage
- Run `/agent-team "Build user authentication module"` to start a managed multi-agent session.
- Options:
  - `--auto`: Auto Mode. Bypasses all human confirmation prompts; delegates requirements clarification and trade-off decisions to the `user-proxy-agent` for 100% hands-off autonomous execution.
  - `--concurrency <N>`: Maximum parallel sub-coders (default: 4).
  - `--dry-run`: Produce technical specifications and DAG without file modifications.

## Execution Flow
1. Discovery & Local Ingestion: Map codebase architecture and repository conventions.
2. Requirements Alignment: Clarify scope, edge cases, and architectural trade-offs (conducted with the human user in Standard Mode, or resolved autonomously by the `user-proxy-agent` in Auto Mode).
3. Technical Specification: Produce contract enclaves and file allowlists.
4. Critic Review: Adversarial inspection and sign-off.
5. Parallel Sub-Coding: Disjoint file execution with concurrency protection.
6. Double-Audit: QA automated test execution and Security SAST validation.
7. Post-QA Freeze: Codebase stabilization and documentation finalization.
