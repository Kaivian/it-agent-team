# Coding quality

Read once per active implementation context; reuse for repairs and refactors. Apply only criteria relevant to the changed behavior. Project conventions and explicit user requirements take priority. This is a self-review guide, not a requirement for extra workers, documents or numeric quality scores.

## Readable, maintainable implementation

- Inspect nearby code, callers, contracts and existing utilities before designing the change. Use the project's architecture, formatter, type system and naming conventions. Ask about unresolved requirements rather than inventing interfaces or behavior.
- Give functions and modules coherent responsibilities. Separate domain decisions from I/O, state coordination and presentation where this clarifies ownership or enables useful tests. Avoid fragmenting straightforward code into many indirections or imposing fixed file/function lengths.
- Use names that communicate domain meaning and units. Prefer explicit control flow and named intermediate values over dense expressions or deeply nested conditionals. Use guard clauses when they make the main path clearer; preserve cleanup and error semantics.
- Reuse existing utilities. Extract repeated logic when it represents the same responsibility and would need to change together; keep unrelated similarities independent. Avoid speculative frameworks, generic base classes, flags and dependencies for imagined future requirements.
- Keep data and state ownership clear. Derive values from their authoritative source instead of maintaining synchronized copies. Use the project's types to express valid states and contracts; avoid unexplained casts, broad `any` and nullable values that hide an invalid state.
- Validate external inputs at the appropriate boundary. Propagate failures explicitly with useful context; do not silently swallow exceptions, turn failure into fake success or introduce arbitrary fallback data. Follow existing logging conventions without exposing sensitive inputs.
- For asynchronous work, account for stale results, cancellation, ordering and cleanup where relevant. Reuse existing request/resource patterns. Do not add caching, concurrency or memoization without an identified need and a check of correctness or measured impact.
- Comments explain non-obvious intent, constraints and tradeoffs. Prefer clear code over comments narrating every line. Remove dead code and temporary debugging from the changed area; document changed public behavior. Do not mix unrelated cleanup or broad formatting with the feature.

## Review before submission

1. Inspect the complete owned diff: does it implement the clarified behavior, stay in scope and preserve affected caller contracts?
2. Check responsibility boundaries, names, branching, duplication, types, error handling and resource/state ownership. Simplify concrete maintenance hazards; do not optimize for personal style or shortest code.
3. Choose relevant verification: cover the bug trigger or changed behavior and meaningful boundary/failure cases. Regression tests should fail for the original defect; avoid assertions that merely mirror implementation details. Do not add tests for reversible low-impact edits without a real verification need.
4. Run the project's relevant formatter/lint/type/build checks as appropriate. Never disable rules, weaken tests or add blanket suppressions merely to pass. Explain a necessary narrow exception and its effect.
5. Record real evidence using the runtime, rerunning affected checks after repairs. For frontend work, also apply the frontend workflow's visual and consumer checks. A passing tool check alone does not establish readability or visual quality.

Report only material tradeoffs, remaining risks and evidence paths in the existing result schema. Review findings identify a concrete location, consequence and correction; distinguish required fixes from optional suggestions. Repairs address causes and preserve compatibility rather than accumulate unexplained special cases.

Source: [Google engineering review guidance](https://google.github.io/eng-practices/review/reviewer/looking-for.html). These criteria adapt its readability and review principles to this workflow's scope and evidence rules.
