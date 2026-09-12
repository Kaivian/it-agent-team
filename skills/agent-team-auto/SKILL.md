---
name: agent-team-auto
description: Executes the IT Agent Team engineering workflow in 100% autonomous Auto Mode, delegating all requirements decisions to user-proxy-agent without asking the human user.
argument-hint: ["[task-description] [--concurrency <N>] [--dry-run]"]
---

# /agent-team-auto

Execute software engineering tasks in 100% autonomous Auto Mode with zero human interruptions.

## Overview
`/agent-team-auto` triggers the IT Agent Team multi-agent workflow with `--auto` enabled by default. The `user-proxy-agent` acts as the human decision surrogate during Phase 0 & 1, evaluating technical trade-offs, answering requirements clarification questions, and approving specifications autonomously.

## Usage
- Run `/agent-team-auto "Build secure multi-tenant authentication with RBAC and refresh tokens"`
- Options:
  - `--concurrency <N>`: Maximum parallel sub-coders (default: 4).
  - `--dry-run`: Produce technical specifications and DAG without writing code.

## Autonomous Workflow
1. Discovery: Map codebase architecture and local conventions.
2. Auto Requirements Resolution: `pm-agent` formulates trade-offs; `user-proxy-agent` resolves them definitively without human interruption.
3. Spec Formulation & Approval: `pm-agent` creates `TECHNICAL_SPEC.md`; `critic-agent` audits and approves (`SPEC_APPROVED`).
4. Parallel Sub-Coding: Disjoint file implementation across parallel sub-coders.
5. Double-Audit Gates: `qa-agent` executes tests; `security-agent` performs SAST.
6. Code Stabilization & Release: Code freeze, README updates, git commit.
