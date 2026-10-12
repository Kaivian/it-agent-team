# Runtime contracts

This document replaces the earlier aspirational invariant list. Runtime guarantees apply to its own registered state and cooperative callers. Host instructions and actual available tools govern execution.

1. Task contracts contain an ID, objective, acceptance criteria, exact file allowlist and dependencies. Optional `verification_files` declare exact read-only verification inputs; excluded runtime, Git, dependency and cache paths cannot appear in either file list.
2. Dependencies are valid and acyclic. A dependent task becomes ready only after accepted completion of its dependencies.
3. A worker claims a ready task before editing. Claims obey configured concurrency and cooperative ownership: exclusive locks cover outputs; shared locks cover verification inputs and transitive dependency inputs.
4. Workers edit only assigned files. Shared-component edits are permitted when included in the task and verified against consumers.
5. Task transitions are persisted and validated. A failed, blocked or interrupted task is not presented as completed.
6. Completion references actual recorded checks from the task's current worker attempt. Relevant failed verification blocks completion.
7. Evidence freshness covers owned outputs, declared verification inputs and transitive dependency outputs/verification inputs. A read-only task without declared or inherited inputs uses a full workspace fingerprint. Changed inputs invalidate affected prior verification; recheck relevant criteria before final sign-off.
8. Session history is preserved. Starting a new task does not wipe previous task boards or logs.
9. Ownership is released after accepted results or explicit recovery of a stopped worker.
10. Recovery never infers worker death solely from elapsed time. Unknown side effects are reconciled before replay.
11. Routine clarification is proportional to missing information. Neither mandatory question packets nor automatic proxy approval expand user authority.
12. Agent delegation uses actual host APIs when available. Serial execution is explicit when delegation is absent.
13. Concurrency, workflow size and model selection follow the host and project. There are no universal five-file or fixed-model-tier requirements.
14. Final reports distinguish verified behavior, skipped checks, limitations and unresolved blockers.
15. Medium and large workflows require relevant final integration verification. Use a read-only final task with an empty `file_allowlist` depending on all implementation tasks, and submit its own recorded check evidence. Independent worker receipts alone are insufficient to verify integrated behavior.

## Historical specification

The previous INVARIANT-001 through INVARIANT-023 rules mixed planned guarantees with host-specific tool names, required parallel calls, compulsory user questions, history deletion, and fixed UI preferences. They are superseded by this document and must not be used as active execution policy.
