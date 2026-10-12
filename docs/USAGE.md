# Usage and recovery

## Host workflow

In Codex, invoke `$agent-team <objective>`. The skill resolves its installed package directory, reads project instructions, checks real host capabilities and connects the host to the Python runtime.

Use small workflow for localized changes, medium for multiple interfaces, and large for substantial dependencies or risk. Independent QA or security reviews should serve a real need. No workflow requires a fixed number of workers or a universal full-role sequence.

The runtime returns dispatch envelopes, not live agents. Host delegation must actually be invoked. When unavailable, run serially and report that execution mode honestly.

## Runtime entrypoint

Resolve the plugin root from the actual `skills/<name>/SKILL.md` location. The scripts directory is two levels above the skill directory. Add `<plugin-root>/scripts` to `PYTHONPATH`, preserving existing entries, then use:

```text
python -m supervisor --workspace <project> init --objective "<objective>" --workflow small --concurrency 1
```

The detailed task/result examples and concrete claim/check/submit commands are maintained in the [runtime workflow reference](../skills/agent-team/references/runtime-workflow.md). Consult CLI help for current options:

```text
python -m supervisor --help
python -m supervisor --workspace <project> init --help
```

Run every command with the same workspace and session ID. Claim commands return an attempt token; heartbeat, check and submit commands use that token to reject stale workers after recovery.

## Token-efficient operation

The workflow reuses loaded instructions, reads focused source sections and carries concise session notes across batch tasks. Worker context includes the assigned contract and relevant decisions, with paths to full artifacts. Questions can still be asked throughout each task with no fixed limit; evidence and integration requirements remain in force.

Use global `--compact` before any subcommand to remove JSON indentation. For routine monitoring, `--compact status --summary` additionally omits repeated task contracts and results while retaining scheduling, expiry and verification-error signals. Regular `status` provides full details for diagnosis, and persisted reports retain complete evidence. Neither option changes runtime verification or exit codes.

## Configuration

| Setting | Default | Runtime bounds |
| --- | --- | --- |
| Workflow | `small` | `small`, `medium`, `large` |
| Concurrency | 1 | 1–32 |
| Worker timeout | 900 seconds | 1–86400 seconds |
| Maximum retries | 1 | 0–10 |
| State directory | `.agent-team` | Confined workspace-relative directory, passed globally as `--state-dir` |

These are maximum scheduling budgets, not a promise that the host has the corresponding number of slots. Project instructions can specify communication language, UI priorities, shared-component policy and verification requirements. Plugin communication defaults to English; explicit user choices take priority.

## Durable session layout

```text
.agent-team/
  locks.db
  sessions/<id>/
    state.db
    events.jsonl
    reports/
      summary.json
      summary.md
```

SQLite is the authoritative state store. Reports and event JSON exports are generated views. Keep contract and result JSON artifacts in the relevant session directory. Ignore local state in the project's Git settings when appropriate; do not ignore the plugin's distributable `.agents/plugins/` catalog.

The runtime excludes its state directory and common generated directories from source snapshots; the report identifies those exclusions. Verification fingerprints are scoped to owned files; the workspace snapshot also detects edits outside declared ownership. Peer-file edits are attributed cooperatively to their declared owners, not independently to an OS process. Unregistered concurrent edits may cause a submission to fail. Use isolated working trees when stronger attribution is needed. An accepted allowlist check is not an OS sandbox. Put check artifacts such as coverage output under session reports, or include their paths in the task contract.

## Verification and completion

The coordinating host chooses or reviews verification commands within existing user authorization. Do not execute untrusted worker-provided commands blindly. The runtime's subprocess runner does not replace host sandbox controls or approval checks.

Commands run as argument lists without a shell. Keep checks relevant to acceptance criteria and record output/exit code through the runtime. A worker result lists changed files and check IDs; it must not invent evidence or reuse stale attempt IDs. Report failed, blocked and skipped checks accurately.

Task contracts may declare optional `verification_files`: exact workspace-relative files read by verification but not owned for edits. The runtime claims shared locks for these inputs and exclusive locks for `file_allowlist` outputs. Evidence freshness covers the task's outputs, its declared verification inputs, and outputs/verification inputs inherited from transitive dependencies. Excluded runtime, Git, dependency and cache directories cannot be declared in either list. A read-only task with no declared or inherited inputs uses a full workspace fingerprint.

A passing worker unit check may not assess combined behavior. Medium and large workflows require a relevant final integration check after all implementation outputs are combined. Register a final task with `file_allowlist: []` and dependencies on every implementation worker task; declare additional read-only inputs in `verification_files` when needed. Its dependency inputs receive shared locks and are included in evidence freshness. Claim, check and submit this task using its own attempt token and check receipts. Individual worker receipts alone do not satisfy the final integration gate. After new edits, rerun checks affected by the change before final sign-off.

## Resume and recovery

1. Reuse the existing session ID and inspect runtime status.
2. Inspect the working tree, outstanding ownership and actual host worker state.
3. Continue with the owning worker if it is still active.
4. If stopped, confirm that fact through the host before invoking recovery.
5. Retry within the budget; retain previous checks, failures and decisions.

Use `--confirm-worker-stopped` only after checking actual worker lifecycle evidence. Timeout alone does not establish death. A check timeout blocks the task and retains ownership, since subprocess descendants may still be active. For an external operation with an unknown outcome, reconcile that outcome before replaying it.

## Legacy state

To retain a legacy location, select it explicitly through the global `--state-dir` option on every session command. For example, use `--state-dir .gemini/agent-team` so existing Gemini files are untouched. This creates the new session layout at that location; it does not migrate old queues, schemas or task boards automatically. Lock coordination remains shared in `.agent-team/locks.db` across configured session roots. Preserve existing `.gemini` logs and reports for reference.

## Batch and auto modes

Batch skills run top-level tasks sequentially with separate session IDs and a combined outcome report. Failed tasks are not silently skipped or counted as complete.

Clarification happens separately at each task's turn. The host asks only the current task's essential questions, waits for the answers, then starts that session. After it finishes, the host asks the next task's questions using any relevant earlier results. Questions for every task are never collected in one upfront prompt. Existing answers are reused, including on resume; tasks with enough information proceed directly. Auto batch follows the same timing for essential human input while resolving routine choices automatically. See the [batch workflow](../skills/agent-team/references/batch-workflow.md).

Auto skills choose routine implementation details within the user's request. A user-proxy role cannot provide new permission, impersonate the user, or guarantee that essential human input will never be needed.

Standard batch does not cap the number of questions or clarification rounds for a task. Unresolved requirements, preferences and constraints can all be clarified, with follow-up rounds until clear. A host tool's per-call question limit only affects how questions are split across calls. Auto batch still resolves routine choices automatically, with no fixed round limit for essential human input.

Questions may be asked at any point during the current session, including implementation, verification and review. When new points need user input, the host asks immediately and waits for required answers before continuing affected work. Independent authorized work may continue while waiting. Answers and resulting changes to the task's scope or checks are recorded in that session; clarification is not limited to the opening questions.
