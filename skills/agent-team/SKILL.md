---
name: agent-team
description: Coordinates the elite multi-agent team workflow for complex or heavy software development tasks with central Supervisor control plane, dynamic sub-coding agents, QA review and testing, and debugger feedback loop.
argument-hint: ["[task-description] [--auto] [--batch] [--concurrency <N>] [--dry-run]"]
---

# /agent-team

Activate the multi-agent autonomous engineering team for end-to-end task execution.

## Usage
- Run `/agent-team "Build user authentication module"` to start a managed multi-agent session.
- Options:
  - `--auto`: Auto Mode. Bypasses all human confirmation prompts; delegates requirements clarification and trade-off decisions to the `user-proxy-agent` for 100% hands-off autonomous execution.
  - `--batch`: Batch Mode. When multiple tasks are submitted, triggers `task-dispatcher-agent` to execute each task within its own dedicated, sequential lifecycle session (Session 1 -> Session 2 -> ...).
  - `--concurrency <N>`: Maximum parallel sub-coders (default: 4).
  - `--dry-run`: Produce technical specifications and DAG without file modifications.

## Execution Flow

### Single Task Lifecycle
1. Discovery & Local Ingestion: Map codebase architecture and repository conventions.
2. Requirements Alignment: Clarify scope, edge cases, and architectural trade-offs (conducted with the human user in Standard Mode, or resolved autonomously by the `user-proxy-agent` in Auto Mode).
3. Technical Specification: Produce contract enclaves and file allowlists.
4. Critic Review: Adversarial inspection and sign-off.
5. Parallel Sub-Coding: Disjoint file execution with concurrency protection.
6. Double-Audit: QA automated test execution and Security SAST validation.
7. Post-QA Freeze: Codebase stabilization and documentation finalization.

### Multi-Task Batch Dispatch (--batch)
When multiple tasks are provided (e.g. numbered list, milestone items, or `--batch` flag), the `task-dispatcher-agent` manages queue execution:
1. Ingests and registers tasks in persistent queue (`.agent_team/task_queue.json`).
2. Sequentially provisions an isolated session (`EXEC-...-BATCH-001`) for Task 1.
3. Guides Task 1 through its complete 7-step lifecycle to verified QA/Security sign-off.
4. Resets the active task board (`tasks.md`) cleanly and launches Task 2 in a fresh session.
5. Emits a consolidated Multi-Session Batch Execution Report upon completing all queued tasks.
