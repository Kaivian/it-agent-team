---
name: agent-team
description: Coordinate substantial software engineering tasks with scoped workers, durable session state, and recorded verification in supported coding hosts.
---

# Agent Team

Use this workflow for tasks that benefit from decomposition or durable verification. Keep small changes small.

## Bootstrap

1. Starting in the directory containing this skill's `SKILL.md`, go up two directories to resolve the plugin root (`skills/agent-team/../..`). Use its `scripts/` and `agents/`; never assume a user's home directory or a hardcoded installation location.
2. Read the target project's instructions and inspect the relevant code. Identify actual host capabilities: delegation, file editing, command execution and worker lifecycle inspection. Read only role definitions needed for this task.
3. Read [runtime workflow](references/runtime-workflow.md) for the concrete session/claim/check/submit contract. Use the actual runtime CLI help if options differ.
4. Select small, medium or large workflow from scope and risk. Respect configured concurrency, timeout and retry budgets. Missing delegation means serial execution by the host agent; never fabricate workers or audit sign-offs.
5. Create a new session or resume its existing ID. Preserve old sessions. Use `.agent-team/sessions/<id>/` by default; consult [usage](../../docs/USAGE.md) for legacy state compatibility.

## Execution

Describe measurable acceptance criteria, exact file ownership and dependencies. Claim ready tasks before edits; use actual host delegation when available. Pass workers the task contract, selected role definition, runtime access and result schema. Assign shared files to one owner or a later integration task.

Ask only for essential missing information. Existing user instructions authorize routine implementation choices within their scope. Auto mode changes how routine choices are resolved; it does not create additional permission.

Record relevant verification through the runtime, submit evidence identifiers and review the resulting state. Resolve failures within the retry budget; report unresolved blockers honestly. For medium or large workflows, register a final read-only integration task depending on every implementation task and record its relevant check before final reporting; individual worker receipts alone are insufficient. See the runtime reference for `verification_files`, shared input locks and evidence freshness.

All plugin-maintained artifacts and default communication are English. Apply an explicit user's language preference when using this plugin in their project. UI conventions, component reuse, test depth and task size follow project requirements rather than universal style mandates.

The runtime's locks are cooperative. Review diffs for ownership violations; do not represent locks as an OS sandbox. Its dispatch envelope describes work; spawning a real worker requires the host's actual API.

## Modes

- Standard: clarify only material ambiguity and continue authorized work.
- Auto: resolve routine product choices from the request and repository. Read `agents/user-proxy-agent.md` only when such a choice needs analysis.
- Batch: process top-level tasks sequentially with separate preserved sessions. Read [batch workflow](references/batch-workflow.md) when processing a list.
- Dry run: inspect and propose contracts without running mutation commands or creating a session. Do not label planned checks as performed.
