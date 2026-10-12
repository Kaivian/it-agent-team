# Batch workflow

Parse the requested top-level tasks in order. Create a separate session for each and retain its ID, outcome and report location in a batch summary under the state directory.

Run each session using the shared runtime workflow. Do not wipe task boards, logs or past reports between tasks. Later tasks may use verified outputs from earlier tasks; document those dependencies.

If a task fails or is blocked, continue only with independent work that remains meaningful and authorized. Report the blocked task, its evidence and the effect on dependent tasks. A completed batch means every required top-level task was actually completed; skipped or failed tasks remain visible.

Auto batch resolves routine choices within the original request. It cannot grant permission to publish, deploy, delete data, send messages or expand scope. Preserve the host's authority checks, and request essential human input when needed.
