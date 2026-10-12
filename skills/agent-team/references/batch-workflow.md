# Batch workflow

Parse the requested top-level tasks in order. Keep later tasks queued; clarify and start only the next eligible task. Create a separate session for each when its turn arrives and retain its ID, outcome and report location in a batch summary under the state directory.

## Per-task clarification

Standard batch has no fixed limit on the number of questions or clarification rounds per task. Ask about every unresolved point that needs the user's input, including useful preferences and constraints, rather than restricting clarification to blockers alone. After each answer, reassess the current task and ask follow-up questions until those points are clear. Do not stop because a question quota or round count has been reached, and do not repeat questions already answered. If the host's question tool limits questions per call, split the current task's questions across as many calls as needed; a per-call limit is not a per-task limit. Auto batch retains its routine-choice policy and has no fixed limit on rounds for essential human input.

For each top-level task, use this sequence:

1. Review the current task against the user's request, existing answers and verified outputs from earlier sessions. Identify unresolved requirements, preferences and constraints that need the user's input for this task.
2. If clarification is needed, present a question set labeled with the current task's name or position (for example, "Task 2 of 3: Pagination"). Include only questions needed for this task. Never combine question sets for several tasks into one prompt or ask later tasks' questions upfront.
3. Wait for the user's required answers and complete any follow-up clarification rounds before initializing the current session, registering its implementation contracts or dispatching its work. An asynchronous question remains pending until answered; elapsed time is not an answer. If there are no unresolved questions, proceed without a mandatory questionnaire or additional confirmation.
4. Initialize and run the current session using the clarified scope. Record its relevant answers and decisions in that session. On resume, reuse recorded answers and ask only about unresolved or newly material issues.
5. Complete the session and record its outcome before moving to the next eligible task. Only then review and ask that task's own questions, incorporating earlier results as needed.

A shared decision needed by the current task may be asked at its turn and reused later. Batch-wide questions are limited to information required to identify or order the tasks; they must not become an upfront requirements interview for every session.

Clarification is continuous throughout the current session, not restricted to its opening. During implementation, verification or review, ask whenever a new requirement, preference, constraint or other unresolved point needs user input. Do not defer these questions until session completion or assume the opening answers settle newly discovered issues. Keep the questions scoped to the current task and reuse existing answers. Wait for required answers before continuing affected work; independent authorized work may continue while an asynchronous question is pending. Record the answers and update the current task's scope, acceptance criteria and checks as needed. These follow-up rounds have no fixed limit. Auto batch follows the same timing for essential human input while continuing to resolve routine choices automatically.

For example, a batch containing tasks A, B and C follows: questions for A (if needed) → answers → session A → questions for B (if needed) → answers → session B → questions for C (if needed) → answers → session C.

Run each session using the shared runtime workflow. Do not wipe task boards, logs or past reports between tasks. Later tasks may use verified outputs from earlier tasks; document those dependencies.

Reuse the shared workflow and applicable role instructions already loaded in the active context. Carry forward a concise batch summary of task order, session IDs, outcomes, reusable decisions and evidence/report paths. At each task's turn, load only its relevant source and dependency outputs; do not replay every earlier session's chat, reports or logs. Recheck earlier evidence when its inputs changed. Keep all session histories on disk and preserve unanswered questions; reducing repeated context must not limit clarification before or during a session.

If a task fails or is blocked, continue only with independent work that remains meaningful and authorized. Report the blocked task, its evidence and the effect on dependent tasks. A completed batch means every required top-level task was actually completed; skipped or failed tasks remain visible.

Auto batch uses the same per-task timing, but resolves routine choices within the original request instead of asking the user. It cannot grant permission to publish, deploy, delete data, send messages or expand scope. Preserve the host's authority checks, and request essential human input only for the current task when needed.
