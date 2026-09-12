---
name: agent-team-multi-task
description: Coordinates execution of multiple tasks sequentially through isolated full-lifecycle sessions using task-dispatcher-agent.
argument-hint: ["[multi-task-list] [--auto] [--concurrency <N>] [--dry-run]"]
---

# /agent-team-multi-task

Execute multiple development tasks sequentially, each within its own isolated Agent Team lifecycle session.

## Overview
`/agent-team-multi-task` triggers the `task-dispatcher-agent` to manage a persistent FIFO queue (`.agent_team/task_queue.json`). Rather than running tasks concurrently and colliding, each task executes sequentially through the full 7-step engineering lifecycle before the next task begins.

## Usage
- Run `/agent-team-multi-task "1. Create Postgres schema\n2. Add REST API endpoints\n3. Write integration tests"`
- Options:
  - `--auto`: Run all queued tasks in autonomous Auto Mode without human pauses.
  - `--concurrency <N>`: Maximum parallel sub-coders per session.
  - `--dry-run`: Generate specifications for all tasks without file modifications.

## Sequential Execution Lifecycle
1. Batch Ingestion: `task-dispatcher-agent` parses the task list into `.agent_team/task_queue.json`.
2. Session N Initialization: Spawns fresh session (`EXEC-...-BATCH-00N`) with `supervisor-agent`.
3. End-to-End Delivery: Runs Discovery -> Spec -> Critic -> Parallel Sub-Coders -> QA & Security Audit -> Code Freeze.
4. Clean Session Reset: Resets `tasks.md` and marks Task N `COMPLETED`.
5. Automatic Progression: Advances to Task N+1 until queue is drained.
6. Batch Summary: Emits consolidated batch completion report.
