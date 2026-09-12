# IT Agent Team Runtime Invariants & Policy Plane Specification

Formal specifications for platform invariants (INVARIANT-001 through INVARIANT-010), FileGuard runtime locks, and Supervisor observability.

---

## 1. Architectural Invariants

- **INVARIANT-001**: Only the Workflow Orchestrator may mutate workflow execution states.
- **INVARIANT-002**: The Supervisor agent cannot construct DAGs or dispatch implementation tasks.
- **INVARIANT-003**: The Quality Assurance (QA) agent is strictly forbidden from directly altering product code.
- **INVARIANT-004**: The Security agent acts solely as a read-only auditor.
- **INVARIANT-005**: Dynamic sub-coding instances cannot mutate files outside their assigned disjoint allowlist.
- **INVARIANT-006**: Code changes after QA sign-off immediately invalidate QA status (QA_INVALIDATED).
- **INVARIANT-007**: A task cannot finish while unresolved blocking defects exist.
- **INVARIANT-008**: Missing or unsatisfied dependencies cannot silently transition to satisfied.
- **INVARIANT-009**: Crashed worker instances must be detected via heartbeats and transitioned to terminal states.
- **INVARIANT-010**: All execution boards and DAG transitions must be deterministically recoverable from SQLite.

---

## 2. Dynamic Sub-Coder Sizing Model

- **Trivial**:  = 1$ sub-coder.
- **Standard**:  = 2 \text{ to } 4$ sub-coders operating concurrently on disjoint file boundaries.
- **Complex**:  = 5 \text{ to } 20+$ sub-coders coordinated through lock queues and contract enclaves.
