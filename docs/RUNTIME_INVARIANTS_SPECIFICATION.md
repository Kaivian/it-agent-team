# IT Agent Team Runtime Invariants & Policy Plane Specification

Formal specifications for platform invariants (INVARIANT-001 through INVARIANT-021), FileGuard runtime locks, Supervisor observability, and agent directory isolation.

---

## 1. Architectural Invariants

- **INVARIANT-001**: Only the Workflow Orchestrator may mutate workflow execution states.
- **INVARIANT-002**: The Supervisor agent cannot construct DAGs or dispatch implementation tasks.
- **INVARIANT-003**: The Quality Assurance (QA) agent is strictly forbidden from directly altering product code.
- **INVARIANT-004**: The Security agent acts solely as a read-only auditor.
- **INVARIANT-005**: Dynamic sub-coding instances cannot mutate files outside their assigned disjoint allowlist.
- **INVARIANT-006**: Code changes after QA sign-off immediately invalidate QA status (`QA_INVALIDATED`).
- **INVARIANT-007**: A task cannot finish while unresolved blocking defects exist.
- **INVARIANT-008**: Missing or unsatisfied dependencies cannot silently transition to satisfied.
- **INVARIANT-009**: Crashed worker instances must be detected via heartbeats and transitioned to terminal states.
- **INVARIANT-010**: All execution boards and DAG transitions must be deterministically recoverable from SQLite.
- **INVARIANT-011**: In `agent-team` workflow, spec approval is fulfilled autonomously by `critic-agent`. The agent MUST NOT halt for interactive planning approval or set `RequestFeedback: true`; it must dispatch sub-coders immediately upon `SPEC_APPROVED`.
- **INVARIANT-012**: Sub-coder implementation tasks MUST be dispatched concurrently in parallel using a single batch `invoke_subagent` call containing all sub-agents in the `Subagents` array.
- **INVARIANT-013**: Sub-Coders MUST write code directly to disk via file tools and return ONLY a compact implementation manifest (< 15 lines). Dumping complete source code into chat messages is strictly prohibited.
- **INVARIANT-014**: QA and Security verification audits MUST be dispatched concurrently in parallel using a single batch `invoke_subagent` tool call containing both `qa-agent` and `security-agent`.
- **INVARIANT-015**: Subagents must adhere to Model Tiering to prevent cost and latency waste: `flash` for utility/audit/status agents, and `pro` / `inherit` for reasoning and coding agents.
- **INVARIANT-016**: Sub-coder sizing MUST respect the Minimum Viable Chunk Principle: tasks touching $\le 3$ files or $< 200$ lines MUST be assigned to $N=1$ sub-coder to avoid micro-agent orchestration overhead.
- **INVARIANT-017**: For STANDARD/COMPLEX tasks with underspecified requirements, PM Agent MUST formulate 3–5 clarifying questions and pause for user confirmation (HITL Checkpoint 0) before authoring specifications.
- **INVARIANT-018**: Session-Scoped Clean Task Board (`.gemini/tasks.md`): `.gemini/tasks.md` serves strictly as the live status board for the current active session, wiped clean and recreated fresh at session start, and updated incrementally after every single agent milestone.
- **INVARIANT-019**: Mandatory Interactive Modal Q&A (`ask_question`) & Zero Pre-Decomposition: Primary agent must invoke `ask_question` and await response before drafting specs or creating downstream tasks.
- **INVARIANT-020**: Chronological Multi-Agent Timeline Log (`.gemini/LOG.md`): All inter-agent delegations, agent actions, lifecycle events, and milestone results MUST be continuously appended to `.gemini/LOG.md` in a structured timeline table format.
- **INVARIANT-021**: Agent Directory Isolation & Project Cleanliness (`.gemini/`): All agent-generated governance files, task trackers, logs, specifications, plan critiques, QA bug reports, security reports, and execution summaries MUST reside exclusively inside the `.gemini/` directory of the workspace root (e.g. `.gemini/tasks.md`, `.gemini/LOG.md`, `.gemini/TECHNICAL_SPEC.md`, `.gemini/CRITIQUE_REPORT.md`, `.gemini/QA_BUG_REPORT.md`, `.gemini/SECURITY_AUDIT_REPORT.md`, `.gemini/FINAL_EXECUTION_REPORT.md`, `.gemini/task_queue.json`). Agents are strictly forbidden from polluting the project source root.

---

## 2. Dynamic Sub-Coder Sizing Model

- **Trivial**: $N = 1$ sub-coder.
- **Standard**: $N = 2 \text{ to } 4$ sub-coders operating concurrently on disjoint file boundaries.
- **Complex**: $N = 5 \text{ to } 20+$ sub-coders coordinated through lock queues and contract enclaves.

