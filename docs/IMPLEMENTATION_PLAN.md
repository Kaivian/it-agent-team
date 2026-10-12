# Implementation plan

All source, documentation, messages, diagnostics, and examples are maintained in English. User-requested communication preferences are respected when applying the plugin to another project.

## Milestone A: dependable installation and diagnostics

1. Document architecture and support levels; remove claims unsupported by executable code.
2. Add the Codex catalog and installation instructions while retaining other host metadata.
3. Make installation idempotent, preserve unrelated configuration, and fail on invalid configuration or failed Git operations.
4. Validate manifests, paths, skill frontmatter, nonempty runtime files, host prerequisites, and writable state.
5. Add CI for package checks and Python behavior on Windows, Linux and macOS.

Acceptance: a clean installation is reviewable, repeated installation preserves settings, and doctor catches malformed or missing package assets. Live host installation is recorded separately.

## Milestone B: a verified end-to-end task

1. Define task contracts, acceptance criteria, dependencies, allowlists, and result evidence.
2. Implement persisted state transitions and ready-task claims.
3. Connect one real Codex worker or the serial fallback to claim, check, and submit.
4. Record command output and exit codes; reject unsupported or failed completion evidence.
5. Produce a report showing changes, verified behavior and unresolved limitations.

Acceptance: a sample code change passes its relevant regression check; deliberately failing verification prevents completion. A host dispatch envelope alone does not satisfy the live-worker criterion.

## Milestone C: concurrency and recovery

1. Replace process-local file locking with cooperative cross-process ownership.
2. Validate dependency graphs and dispatch only conflict-free ready tasks.
3. Retain separate session histories and checkpoints.
4. Recover stopped workers without losing evidence or releasing a live worker's locks.
5. Bound retries and reconcile uncertain external effects before replay.

Acceptance: independent processes cannot both own the same exclusive file; recovery after an interrupted task preserves history and permits a bounded retry. Integration checks assess the combined final code.

## Experience and cost

Choose small, medium, or large workflows from actual risk and scope. Configure concurrency, timeout, retries, state directory and project conventions. Avoid mandatory full-role ceremonies, fixed file-count limits, hardcoded model tiers, compulsory desktop-first design, and mandatory questions whose answers are already known.

Auto mode resolves routine implementation decisions within existing authorization. It may stop for missing essential information, unavailable capabilities, or an action outside authorized scope.

## Reviewable changes

| Change | Scope | Dependencies |
| --- | --- | --- |
| 1 | Architecture, support matrix, honest README | None |
| 2 | Codex catalog and install docs | None |
| 3 | Safe installers, doctor, package CI | 2 |
| 4 | Task/result contracts and state transitions | 1 |
| 5 | Serial workflow, Codex dispatch envelope and end-to-end checks | 4 |
| 6 | Cross-process ownership and allowlist checks | 4 |
| 7 | Dependencies and concurrent claims | 5, 6 |
| 8 | History, recovery and bounded retry | 5, 6 |
| 9 | Configurable workflow and cost controls | 7, 8 |

These are logical review units. A local implementation may combine them; report actual validation without implying that unperformed host checks have passed.
