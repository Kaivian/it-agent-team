---
name: agent-team-batch
description: Alias for agent-team-multi-task. Executes a batch of tasks sequentially across isolated lifecycle sessions.
argument-hint: ["[multi-task-list] [--auto] [--concurrency <N>] [--dry-run]"]
---

# /agent-team-batch

Alias for `/agent-team-multi-task`. Ingests and executes a batch of tasks sequentially with isolated session lifecycles.

## Usage
- Run `/agent-team-batch "1. Setup authentication\n2. Implement rate limiting\n3. Add unit tests"`
- Supports identical options and sequential isolation behavior as `/agent-team-multi-task`.
