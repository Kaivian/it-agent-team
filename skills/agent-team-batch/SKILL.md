---
name: agent-team-batch
description: Coordinates execution of multiple tasks sequentially through isolated full-lifecycle sessions using task-dispatcher-agent.
argument-hint: ["[multi-task-list] [--auto] [--concurrency <N>] [--dry-run]"]
---

# /agent-team-batch

Execute multiple development tasks sequentially, each within its own isolated Agent Team lifecycle session.

## Overview
`/agent-team-batch` triggers the `task-dispatcher-agent` to manage a persistent FIFO queue (`.gemini/task_queue.json`). Rather than running tasks concurrently and colliding, each task executes sequentially through the full 7-step engineering lifecycle before the next task begins. All agent files are isolated inside `.gemini/` (INVARIANT-021).

## Usage
- Run `/agent-team-batch "1. Create Postgres schema\n2. Add REST API endpoints\n3. Write integration tests"`
- Options:
  - `--auto`: Run all queued tasks in autonomous Auto Mode without human pauses.
  - `--concurrency <N>`: Maximum parallel sub-coders per session (default: 4).
  - `--dry-run`: Generate specifications for all tasks without file modifications.

## Sequential Execution Lifecycle
1. Batch Ingestion: `task-dispatcher-agent` parses the task list into `.gemini/task_queue.json`.
2. Session N Initialization: Spawns fresh session (`EXEC-...-BATCH-00N`) with `supervisor-agent`, resetting `.gemini/tasks.md` and appending to `.gemini/LOG.md`.
3. End-to-End Delivery: Runs Discovery -> Spec (`.gemini/TECHNICAL_SPEC.md`) -> Critic (`.gemini/CRITIQUE_REPORT.md`) -> Parallel Sub-Coders -> QA (`.gemini/QA_BUG_REPORT.md`) & Security Audit (`.gemini/SECURITY_AUDIT_REPORT.md`) -> Code Freeze.
4. Clean Session Reset: Resets `.gemini/tasks.md` cleanly and marks Task N `COMPLETED`.
5. Automatic Progression: Advances to Task N+1 until queue is drained.
6. Batch Summary: Emits consolidated batch completion report to `.gemini/FINAL_EXECUTION_REPORT.md`.
