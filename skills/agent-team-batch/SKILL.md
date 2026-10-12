---
name: agent-team-batch
description: Process a list of engineering tasks sequentially, preserving separate session history and verification evidence.
---

# agent-team-batch

Load the shared [Agent Team workflow](../agent-team/SKILL.md) and apply batch mode. Starting in the directory containing this skill's `SKILL.md`, go up two directories to resolve the plugin root; do not assume a home-directory installation.

Read the [batch workflow](../agent-team/references/batch-workflow.md). Keep top-level tasks sequential and preserve all session histories. Do not reset or delete prior logs.

Ask each task's own clarification questions only when that task is next, and wait for required answers before starting its session. Do not collect questions for all tasks in one upfront prompt. Reuse existing answers; tasks with sufficient information start without an extra questionnaire.

There is no fixed limit on questions or clarification rounds per task. Ask about every unresolved point needing user input, including preferences and constraints, and follow up until clear. Split questions into multiple calls when the host tool has a per-call limit; do not treat that limit as a total question budget.

Ask throughout implementation, verification and review whenever new points need user input, not only before the session starts. Wait for required answers before continuing affected work; independent authorized work may continue. Record answers in the current session and adjust its contracts and checks as needed.

Use the same capability check, claim/check/submit evidence contract and serial fallback as the shared workflow. Default communication is English; explicit user language and project preferences take priority. A dry run inspects and proposes work without source or runtime mutation.
