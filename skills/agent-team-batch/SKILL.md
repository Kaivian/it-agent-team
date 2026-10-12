---
name: agent-team-batch
description: Process a list of engineering tasks sequentially, preserving separate session history and verification evidence.
---

# agent-team-batch

Load the shared [Agent Team workflow](../agent-team/SKILL.md) and apply batch mode. Starting in the directory containing this skill's `SKILL.md`, go up two directories to resolve the plugin root; do not assume a home-directory installation.

Read the [batch workflow](../agent-team/references/batch-workflow.md). Keep top-level tasks sequential and preserve all session histories. Do not reset or delete prior logs.

Use the same capability check, claim/check/submit evidence contract and serial fallback as the shared workflow. Default communication is English; explicit user language and project preferences take priority. A dry run inspects and proposes work without source or runtime mutation.
