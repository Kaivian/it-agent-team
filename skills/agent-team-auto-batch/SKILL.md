---
name: agent-team-auto-batch
description: Executes a batch of tasks sequentially in 100% autonomous Auto Mode with zero human interruptions across all sessions.
argument-hint: ["[multi-task-list] [--concurrency <N>] [--dry-run]"]
---

# /agent-team-auto-batch

Execute multiple development tasks sequentially in 100% autonomous Auto Mode without human intervention.

## Overview
`/agent-team-auto-batch` combines the sequential session isolation of `task-dispatcher-agent` with the autonomous decision proxy of `user-proxy-agent`. It drains an entire task list from start to finish without pausing for interactive human confirmation at any stage.

## Usage
- Run `/agent-team-auto-batch "1. Setup database models\n2. Create CRUD controllers\n3. Add end-to-end tests"`
- Options:
  - `--concurrency <N>`: Maximum parallel sub-coders per session (default: 4).
  - `--dry-run`: Generate specifications for all tasks without modifying files.

## Workflow
- Task 1: Autonomous spec (`.gemini/TECHNICAL_SPEC.md`) -> Critic approval (`.gemini/CRITIQUE_REPORT.md`) -> Sub-coders -> QA/Security audit -> Sign-off.
- Task 2: Fresh session reset (`.gemini/tasks.md`) -> Autonomous spec -> Coding -> Testing -> Sign-off.
- ...
- Queue Complete: Publishes final consolidated batch execution report (`.gemini/FINAL_EXECUTION_REPORT.md`). All governance files reside strictly in `.gemini/` (INVARIANT-021).
