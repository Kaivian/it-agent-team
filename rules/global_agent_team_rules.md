# Agent Team project guidance

Apply this guidance only to the requested engineering workflow. Explicit user instructions and applicable project requirements determine scope, language, UI conventions and authorization.

- Use the smallest workflow that provides meaningful verification. Fixed worker counts, five-file limits, model tiers and mandatory question packets are not required.
- Identify real host capabilities. Use actual delegation when available and serial execution otherwise. A role assignment or dispatch envelope alone is not a running worker.
- Read only needed role definitions. Assign exact file ownership and dependencies before edits. Shared components may change when owned and verified against consumers.
- Obtain runtime claims and attempt tokens before implementation. Cooperative locks do not intercept arbitrary host file tools; review diffs for ownership violations.
- Record relevant checks and actual exit codes. Completed results must reference current-attempt evidence. Agent assurance is not a replacement for verification.
- Re-run checks affected by later edits. Report skipped checks, unknowns and blockers explicitly.
- Coding quality: use coherent responsibilities, domain names, clear control flow and data ownership, explicit failures and existing project patterns. Avoid speculative abstractions and unrelated rewrites; self-review the owned diff and verify meaningful behavior, boundaries and caller compatibility. Review findings must identify impact, distinguishing required fixes from optional style preferences. For UI changes, assess visual hierarchy, spacing, responsive/interactive states and accessibility against existing design references; a passing build alone is insufficient visual evidence.
- Preserve sessions under `.agent-team/sessions/<id>/`, or the configured state directory. Keep legacy `.gemini` history. Do not wipe logs between tasks.
- Confirm a worker has stopped before recovering its task or releasing ownership. Respect timeout and retry budgets; reconcile unknown external side effects before replay.
- Auto mode resolves routine choices within the user's request. A proxy cannot create authorization for external actions or expand scope.
- Maintain source, diagnostics and documentation in English. Communication defaults to English; honor explicit user preferences in their project.
- Follow the project's responsive design, component, CSS, data and migration conventions. Test data may be synthetic where appropriate; never silently represent a mock integration as a working real service.
- Frontend: inspect existing UI evidence and ask about unresolved requirements throughout the task; never invent missing design or behavior. Reuse existing components and match the site's style tokens and states. Prefer local composition or existing variants; necessary shared edits require ownership, consumer impact inspection and regression checks while preserving unrelated defaults. Use Tailwind utilities compatible with the installed version and theme, following `tailwindCSS.lint.suggestCanonicalClasses` diagnostics when available. Clarify setup scope if Tailwind is absent; report unavailable visual or canonical-diagnostic checks honestly.

The runtime contracts in `docs/RUNTIME_INVARIANTS_SPECIFICATION.md` distinguish implemented control-plane behavior from host responsibilities.

Frontend class reuse: keep call-site classes limited to necessary local differences after using existing component defaults and variants. Consolidate repeated meaningful style groups into reusable components, variants or named style helpers according to project conventions. Preserve complete detectable Tailwind strings, class precedence and shared-consumer behavior. Do not introduce global overrides or bulk `@apply` solely to shorten markup, and keep unrelated refactors outside scope.
