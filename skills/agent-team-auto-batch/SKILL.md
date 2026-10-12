---
name: agent-team-auto-batch
description: Process engineering tasks sequentially with routine decisions resolved automatically within existing user authorization.
---

# agent-team-auto-batch

Load the shared [Agent Team workflow](../agent-team/SKILL.md) and apply auto batch mode. Starting in the directory containing this skill's `SKILL.md`, go up two directories to resolve the plugin root; do not assume a home-directory installation.

Resolve routine implementation choices from the user's request and repository. The user proxy is advisory; it cannot create authorization or promise zero interruptions when essential input is missing.

Read the [batch workflow](../agent-team/references/batch-workflow.md). Keep top-level tasks sequential and preserve all session histories. Do not reset or delete prior logs.

Resolve routine choices automatically. When essential human input is needed, ask only for the task whose turn has arrived and wait for required answers before starting its session. Never combine several tasks' question sets into an upfront prompt; reuse existing answers.

Essential questions may also arise during implementation, verification or review. Ask as they arise in the current session, with no fixed question or round limit, and wait for required answers before continuing affected work. Independent authorized work may continue; record answers and adjust the current contracts and checks as needed.

Use the same capability check, claim/check/submit evidence contract and serial fallback as the shared workflow. Default communication is English; explicit user language and project preferences take priority. A dry run inspects and proposes work without source or runtime mutation.
