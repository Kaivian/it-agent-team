# Agent Team project guidance

Apply this guidance only to the requested engineering workflow. Explicit user instructions and applicable project requirements determine scope, language, UI conventions and authorization.

- Use the smallest workflow that provides meaningful verification. Fixed worker counts, five-file limits, model tiers and mandatory question packets are not required.
- Identify real host capabilities. Use actual delegation when available and serial execution otherwise. A role assignment or dispatch envelope alone is not a running worker.
- Read only needed role definitions. Assign exact file ownership and dependencies before edits. Shared components may change when owned and verified against consumers.
- Obtain runtime claims and attempt tokens before implementation. Cooperative locks do not intercept arbitrary host file tools; review diffs for ownership violations.
- Record relevant checks and actual exit codes. Completed results must reference current-attempt evidence. Agent assurance is not a replacement for verification.
- Re-run checks affected by later edits. Report skipped checks, unknowns and blockers explicitly.
- Preserve sessions under `.agent-team/sessions/<id>/`, or the configured state directory. Keep legacy `.gemini` history. Do not wipe logs between tasks.
- Confirm a worker has stopped before recovering its task or releasing ownership. Respect timeout and retry budgets; reconcile unknown external side effects before replay.
- Auto mode resolves routine choices within the user's request. A proxy cannot create authorization for external actions or expand scope.
- Maintain source, diagnostics and documentation in English. Communication defaults to English; honor explicit user preferences in their project.
- Follow the project's responsive design, component, CSS, data and migration conventions. Test data may be synthetic where appropriate; never silently represent a mock integration as a working real service.

The runtime contracts in `docs/RUNTIME_INVARIANTS_SPECIFICATION.md` distinguish implemented control-plane behavior from host responsibilities.
