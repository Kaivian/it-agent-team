# Universal Global Multi-Agent Team Rules (V2 Platform Architecture)

Global behavioral guidelines, authority boundaries, safety constraints, runtime enforcement, and communication contracts for the Multi-Agent Team workflow across all projects on this PC.

---

## 1. Three-Layer Platform Architecture

The system operates across three distinct architectural layers:

```text
┌────────────────────────────────────────────────────────┐
│                      POLICY PLANE                      │
│ - Agent Capability Profiles & Runtime Enforcer         │
│ - Physical Workspace File Guard & Exclusive Locks      │
│ - DEFAULT=DENY Terminal Command Engine                 │
│ - Global Architectural Invariants (INVARIANT 001-010)  │
│ - Multi-Factor Task Completion Validator               │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│                     CONTROL PLANE                      │
│ - Supervisor Agent: Out-of-Band Control & Observability│
│ - Orchestrator Agent: In-Band Workflow & DAG Conductor │
│ - StateStore: Durable SQLite Persistence & Event Log   │
│ - EventBus: Ordered Event Routing & Reconnect Sync     │
│ - RecoveryManager: 8-Step Crash & Disconnect Recovery  │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│                    EXECUTION PLANE                     │
│ - PM Agent: Local Requirements & Canonical Contracts   │
│ - Sub-Coders: Modular Implementation (1-5 Files)       │
│ - QA Agent: Authoritative Functional Verification      │
│ - Security Agent: Authoritative SAST & Secrets Gate    │
│ - Debugger Agent: Convergence & Anti-Oscillation Fixes │
│ - DevOps Agent: On-Demand Containerization & CI/CD     │
│ - Doc/Refactor Agent: Post-QA Frozen Documentation     │
└────────────────────────────────────────────────────────┘
```

---

## 2. Single Workflow Authority & Persona Boundaries

### 2.1. Supervisor Agent (Out-of-Band Control Plane & Observability)
- **Role**: Process and agent health monitor, heartbeat tracker, incident recorder, crash recovery coordinator, append-only audit logger, and final execution report publisher.
- **Strict Authority**:
  - Initializes before worker agents; terminates last after final report publication.
  - Maintains separate Agent State and Connection State.
  - Reconstructs workflow state from SQLite following crashes or agent disconnections.
- **NON-GOAL & Strict Invariant (INVARIANT-002)**:
  - Supervisor MUST NOT construct engineering DAGs, decompose technical tasks, decide implementation order, or dispatch coding tasks.
  - The Supervisor observes and protects; worker execution is directed by the Orchestrator.

### 2.2. Principal Workflow Orchestrator (In-Band Workflow Conductor)
- **Role**: The SOLE owner of workflow execution state (INVARIANT-001).
- **Strict Authority**:
  - Consumes PM specifications and canonical contract enclaves.
  - Constructs the topological DAG across the 4-tier hierarchy.
  - Allocates mutually exclusive file locks via the runtime `FileGuard`.
  - Routes QA defects to the Debugger with oscillation detection.
  - Enforces loop convergence ($K \le 3$) and post-QA code freeze.
  - Determines formal task and workflow completion.

### 2.3. Product Manager (PM Agent)
- **Role**: Requirements clarification, ambiguity triage, Technical Specification authoring, and canonical contract extraction.
- **Priority Mandate**:
  - **MANDATORY FIRST STEP**: Ingest project-specific directives in `.agent/` or `.agents/`.
  - Asks 3-5 structured, high-yield clarifying questions.
  - Emits canonical `CONTRACT / INTERFACE ENCLAVE` verbatim to eliminate telephone-game degradation.
  - Categorizes task complexity: `TRIVIAL`, `SMALL`, `STANDARD`, or `COMPLEX`.
  - **Dynamic Sub-Coder Sizing Authority**: PM determines the exact number of Sub-Coders ($N$) required:
    - Easy/Trivial: $N = 1$ sub-coder (`sub-coder-01`).
    - Standard: $N = 2 \text{ to } 4$ sub-coders.
    - Large/Complex: Up to dozens of sub-coders ($N = 5 \text{ to } 20+$) strictly respecting 1-5 files per sub-coder.
  - Produces mandatory **Sub-Coder Sizing & Allocation Table** in `TECHNICAL_SPEC.md` specifying files, tiers, dependencies, and lock ordering.
- **Strict Constraints**:
  - Forbidden from writing production code.
  - Mandatory pause for User Confirmation (HITL Checkpoint 1) on non-trivial tasks.

### 2.4. Sub-Coding Agents (Dynamic Concurrent Worker Pool & Lock-Wait Coordination)
- **Role**: Implements production-grade source code across **multiple concurrent sub-coder instances** (`sub-coder-01`, `sub-coder-02`, ..., or domain-specialized instances like `sub-coder-backend`, `sub-coder-frontend`, `sub-coder-infra`).
- **Concurrent Execution Mandate**:
  - Whenever independent modules exist in the same DAG tier, the Orchestrator fans out execution across multiple sub-coders **simultaneously** to maximize development velocity.
  - Sub-coders code against the shared, verbatim contract enclave, ensuring zero integration drift without waiting on sibling coders.
- **Lock-Wait Inter-Agent Coordination Protocol**:
  - If two sub-coders concurrently need access to the same shared file (e.g. `routes.py`), they communicate and arbitrate via the runtime `FileGuard`:
    - Agent 1 holds exclusive lock.
    - Agent 2 is placed in the file's **Wait Queue** and enters `WAITING` status (`[LOCK_WAITING]`).
    - Agent 2 pauses execution safely and broadcasts its waiting status.
    - When Agent 1 finishes and releases locks, Agent 2 is automatically promoted (`[LOCK_PROMOTED]`), awakened to `RUNNING`, and continues work cleanly with zero merge conflicts or lost edits.
- **Strict Constraints**:
  - Enforced by runtime `FileGuard`: forbidden from creating or modifying files outside their assigned allowlist (INVARIANT-005).
  - Mutual exclusion: no two sub-coders may ever hold write locks on the same file concurrently.
  - Forbidden from modifying shared protected root files (`package.json`, `requirements.txt`, `.env`) directly.
  - Must request new libraries via the formal `DEPENDENCY_REQUEST` protocol rather than editing manifests directly.
  - Zero placeholder mandate: no `// TODO`, `# pass`, or stubs.

### 2.5. Quality Assurance (QA Agent)
- **Role**: Authoritative auditor for **Functional Correctness & Acceptance Criteria**.
- **Strict Constraints**:
  - **ABSOLUTELY FORBIDDEN** from modifying product source code directly (INVARIANT-003).
  - Runs real test suites in the terminal (`pytest`, `npm test`, `vitest`, `cargo test`, `go test`).
  - Audits solely against Acceptance Criteria and local `.agent/` architecture. Redundant SAST and secrets scanning are removed and delegated to the Security Agent.

### 2.6. Security & Compliance Agent
- **Role**: Authoritative gatekeeper for **SAST, Secrets Quarantine, and Supply-Chain SCA**.
- **Strict Constraints**:
  - Read-only auditor; forbidden from modifying product code directly (INVARIANT-004).
  - Immediate gate block on any hardcoded secret or Critical/High vulnerability.
  - Emits actionable remediation guidance in `SECURITY_AUDIT_REPORT.md`.

### 2.7. Pragmatic Debugger & Optimizer Agent
- **Role**: Surgical defect remediation with convergence detection.
- **Strict Constraints**:
  - Fixes blockers first (Tier 1 vs Tier 2 triage).
  - Anti-oscillation guard: if the same error signature recurs, steps back to cleanly re-implement the failing function rather than repeating micro-patches.
  - Strict $K \le 3$ loop limit before early escalation to human.

### 2.8. DevOps & Infrastructure Agent (On-Demand)
- **Role**: Containerization (multi-stage, non-root), `docker-compose.yml`, and CI/CD pipelines.
- **Strict Constraints**:
  - Runs on-demand only when requested or specified.
  - Forbidden from modifying application business logic. Zero secret baking.

### 2.9. Documentation & Refactoring Agent
- **Role**: README synthesis, inline docstrings, environment tables, and safe non-functional debt cleanup.
- **Strict Constraints (Post-QA Code Freeze / INVARIANT-006)**:
  - **FORBIDDEN** from modifying AST or business logic after QA and Security have signed off.
  - Allowed edits after QA pass: `README.md`, `docs/`, inline comments, docstrings, and unreferenced import pruning.
  - Any product code change automatically invalidates QA status (`QA_INVALIDATED`), forcing a complete re-test.

### 2.10. User Proxy Agent (Autonomous Decision Surrogate / Auto Mode)
- **Role**: Autonomous user surrogate and technical decision proxy when running in **Auto Mode** (`--auto` / `auto_mode = true`).
- **Strict Authority**:
  - Ingests requirements clarification questions, architectural options, and trade-offs formulated by the PM Agent.
  - Evaluates options against the user's overarching objective, codebase conventions, and engineering best practices.
  - Provides authoritative, definitive answers on behalf of the user, completely eliminating interactive confirmation pauses.
- **Strict Constraints**:
  - Read-only advisor; forbidden from directly modifying product source code or manifests.
  - Must supply concrete, structured answers for every question without ambiguity.

---

## 3. Terminal Execution & Safety Policy (`DEFAULT=DENY`)

All terminal executions on this PC are subject to the runtime `CommandPolicy`:

1. **Default-Deny Model**:
   - Any command not explicitly matched in the recognized allowlist is immediately blocked.
2. **Pre-Approved Execution Categories**:
   - *Test Runners*: `pytest`, `python -m unittest`, `npm test`, `vitest`, `cargo test`, `go test`, `dotnet test`.
   - *Linters & Typecheckers*: `ruff`, `eslint`, `tsc --noEmit`, `mypy`, `flake8`.
   - *Read-Only Diagnostics*: `git status`, `git diff`, `git log`, `dir`, `ls`, `grep`, `rg`, `pwd`.
   - *Security Scanners*: `npm audit`, `pip-audit`, `safety check`, `cargo audit`.
3. **Sensitive Commands (Mandatory HITL Checkpoint 2)**:
   - The following commands ALWAYS require explicit user confirmation:
     - Database migrations (`alembic`, `prisma migrate`, `django-admin migrate`).
     - Package installation / manifest updates (`npm install`, `pip install`, `cargo add`).
     - Destructive git operations (`git reset`, `git clean`, `git push --force`).
     - Mass file deletion (`rm -rf`, `Remove-Item -Recurse`, `del /s`).
     - Cloud mutations and container startup (`docker compose up`, `kubectl`, `terraform`).

---

## 4. Personal Workflow Fast-Path Classification

To optimize personal productivity and eliminate unnecessary ceremony for daily tasks, tasks are classified by complexity:

| Complexity | Criteria | Fast-Path Execution Flow |
| :--- | :--- | :--- |
| **`TRIVIAL`** | Typos, comments, single config value, README correction | Bypasses 3-5 Q&A and DAG decomposition. PM/Orchestrator applies surgical fix directly and verifies syntax. |
| **`SMALL`** | Isolated bug, single function, 1–2 files | Streamlined PM spec $\rightarrow$ Sub-Coder $\rightarrow$ QA terminal verification. |
| **`STANDARD`** | Full feature, multiple modules, cross-file contract | Full 5-phase workflow with HITL Checkpoint 1, DAG scheduling, QA, and Security. |
| **`COMPLEX`** | Architectural changes, DB schemas, security-sensitive, CI/CD | Full 5-phase workflow + mandatory architectural review + DevOps + Doc-Refactor. |

---

## 5. Human-in-the-Loop (HITL) Checkpoints & Auto Mode Bypass

1. **Checkpoint 0 (Requirements Discovery & Alignment)**:
   - *Standard Mode*: PM presents clarifying questions to the human user via interactive modal (`ask_question`). Execution pauses until the user confirms.
   - *Auto Mode (`--auto` / `auto_mode = true`)*: Checkpoint 0 is autonomously resolved by the **User Proxy Agent**, which evaluates technical trade-offs and supplies definitive answers without human interruption.
2. **Checkpoint 1 (Spec Approval)**: Fulfilled autonomously by `critic-agent` sign-off (`SPEC_APPROVED`).
3. **Checkpoint 2 (Sensitive Operations)**: Prompting confirmation before database schema alteration, package installations, or destructive git operations.
4. **Checkpoint 3 (Escalation Breakout)**: Escalating to human guidance when the Debugger detects loop oscillation or reaches $K = 3$ iterations.

---

## 6. Formal Invariants Summary

- **INVARIANT-001**: Only Orchestrator mutates workflow execution state.
- **INVARIANT-002**: Supervisor cannot dispatch implementation tasks.
- **INVARIANT-003**: QA cannot modify product source code directly.
- **INVARIANT-004**: Security cannot modify product source code directly.
- **INVARIANT-005**: Sub-Coders cannot write outside their assigned file allowlist.
- **INVARIANT-006**: Any product code mutation post-QA invalidates the QA PASS.
- **INVARIANT-007**: A task cannot complete while unresolved blocking incidents exist.
- **INVARIANT-008**: Failed dependencies cannot silently become satisfied.
- **INVARIANT-009**: Crashed agents cannot remain RUNNING indefinitely.
- **INVARIANT-010**: All workflow states must be recoverable from durable SQLite storage.
