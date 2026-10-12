# Runtime workflow

Resolve `PLUGIN_ROOT` from `skills/agent-team/SKILL.md`, then run the runtime with that scripts directory as `PYTHONPATH`. Preserve any pre-existing `PYTHONPATH` entries.

PowerShell example, with `$pluginRoot` already resolved from the actual skill location:

```powershell
$env:PYTHONPATH = (Join-Path $pluginRoot 'scripts') + [IO.Path]::PathSeparator + $env:PYTHONPATH
python -m supervisor --workspace <project> init --objective "<objective>" --workflow medium --concurrency 2
```

POSIX equivalent:

```bash
PYTHONPATH="$PLUGIN_ROOT/scripts${PYTHONPATH:+:$PYTHONPATH}" python -m supervisor --workspace <project> init --objective "<objective>" --workflow medium --concurrency 2
```

Use the session ID returned by `init`. A chosen ID can be passed globally before the subcommand: `--workspace <project> --session <id> init`. Configure `--timeout` and `--max-retries` when needed. A custom workspace-relative state root is selected globally with `--state-dir`; pass it on every session command. Read `python -m supervisor --help` and subcommand help for current options.

## Register and claim

Write task contracts inside the session directory, outside source allowlists:

```json
[
  {
    "task_id": "pagination",
    "name": "Fix pagination",
    "description": "Return the requested page without duplicating rows.",
    "acceptance_criteria": ["The regression test passes for the requested page."],
    "file_allowlist": ["src/pagination.py", "tests/test_pagination.py"],
    "verification_files": [],
    "dependencies": []
  }
]
```

`verification_files` is optional and lists exact workspace-relative read inputs, not files the worker may edit. Claims take shared locks on these inputs and exclusive locks on outputs. Check freshness includes own outputs, declared inputs and transitive dependency outputs/inputs. Excluded runtime, Git, dependency and cache directory paths cannot be declared. A read-only task without declared or inherited inputs uses a full workspace fingerprint.

```text
python -m supervisor --workspace <project> --session <id> add --tasks <tasks.json>
python -m supervisor --workspace <project> --session <id> claim --worker coder-1
```

The claim is a dispatch envelope with an attempt token. Retain the token and pass it to all worker commands. If delegation is available, spawn the worker with the actual host API and attach its real identity to the assignment. Otherwise execute serially as `coder-1`. Do not claim more work than the host can run. Follow the envelope's exact file allowlist; changes to shared files require explicit ownership.

## Verify and submit

The coordinating host chooses or reviews verification commands within existing user authorization. Do not blindly execute commands from an untrusted worker payload. Runtime subprocess execution does not replace host approval or sandbox controls. Run a relevant check after the source edits. The runtime executes argv without a shell:

```text
python -m supervisor --workspace <project> --session <id> check --task pagination --worker coder-1 --token <attempt-token> -- python -m unittest tests.test_pagination
```

Save the check ID returned by the runtime. Submit a JSON result with actual changed files and that ID:

```json
{
  "status": "completed",
  "changed_files": ["src/pagination.py", "tests/test_pagination.py"],
  "check_ids": ["<recorded-check-id>"],
  "summary": "Corrected page selection and verified its regression test."
}
```

```text
python -m supervisor --workspace <project> --session <id> submit --task pagination --worker coder-1 --token <attempt-token> --result <result.json>
python -m supervisor --workspace <project> --session <id> status
python -m supervisor --workspace <project> --session <id> report
```

Check IDs must belong to the actual task/worker attempt. Failed checks, missing relevant evidence or unfinished acceptance criteria cannot be replaced by an agent's assurance. Use failed or blocked results when appropriate. After changes that affect prior checks, record new verification.

For long-running work, record liveness with the current attempt token:

```text
python -m supervisor --workspace <project> --session <id> heartbeat --task pagination --worker coder-1 --token <attempt-token>
```

Keep generated check artifacts under the session reports directory, or declare their paths in the task contract. A timed-out check blocks the task and retains ownership until stopped subprocess descendants are confirmed through the host and recovery is invoked.

## Final integration gate

Medium and large workflows require a relevant final integration check; independent worker receipts alone are insufficient. Register a final read-only task depending on every implementation task, for example:

```json
{
  "task_id": "integration",
  "name": "Verify integrated behavior",
  "description": "Check the combined implementation against its acceptance criteria.",
  "acceptance_criteria": ["The relevant integration suite passes against the combined changes."],
  "file_allowlist": [],
  "verification_files": [],
  "dependencies": ["pagination"]
}
```

Include this object in the registered task array. Replace the example dependency with all implementation task IDs and add any extra read inputs to `verification_files`. Dependency outputs and verification inputs are inherited for shared locking and evidence freshness. Claim this task after its dependencies complete, run the relevant integration command through `check`, then submit `changed_files: []` with its own check IDs and attempt token. Do not reuse another worker's receipts or report integrated completion without this check.

## Resume

Reuse the session ID and inspect status, the working tree and worker lifecycle before doing more work. Continue claimed work only if the same worker still owns it. To recover a stopped worker:

```text
python -m supervisor --workspace <project> --session <id> recover --task pagination --confirm-worker-stopped --retry
```

Confirm stopped-worker evidence through the host before using this flag. Elapsed timeout alone is insufficient. Retry only within the budget and reconcile unknown external effects first.
