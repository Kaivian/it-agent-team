# IT Agent Team

A plugin for coordinating software engineering tasks with scoped workers, durable session state, and recorded verification evidence. Codex is the first host targeted for end-to-end validation.

The Python runtime manages tasks and checks. The coding host performs the actual agent dispatch and source edits. Installing this plugin does not create a background service or grant permission to deploy, publish, or contact other people.

## Quick start

1. Follow [installation](docs/INSTALLATION.md) to register the plugin for your host.
2. Run `python scripts/doctor.py --host codex` from the plugin checkout.
3. Open a new Codex chat and invoke:

```text
$agent-team Fix the API pagination bug and verify its regression test.
```

The skill locates the runtime relative to its installed directory. You do not need to copy runtime files into the project.

## Skills

| Skill | Use |
| --- | --- |
| `$agent-team` | One engineering task, with clarification only when needed |
| `$agent-team-auto` | One task with routine implementation choices resolved within the user's scope |
| `$agent-team-batch` | A task list processed sequentially with preserved session history |
| `$agent-team-auto-batch` | Sequential tasks with routine decisions resolved automatically |

These are skill invocation examples for Codex. Other hosts may expose slash commands or require loading skill instructions manually. See the [support matrix](docs/SUPPORT_MATRIX.md).

## Workflow

Use the smallest workflow that provides meaningful verification:

- **Small:** scoped implementation and relevant verification.
- **Medium:** a short plan, scoped workers, integration checks, and review.
- **Large:** dependencies, explicit ownership, independent review where available, and integration verification.

Workers may run concurrently only when the host supports real delegation and their file ownership permits it. A host without delegation runs the same tasks serially. Task size and worker count are chosen from the project's needs; there is no universal five-file limit.

The runtime stores session data under `.agent-team/sessions/<session-id>/`. Existing `.gemini` history is not deleted. [Usage and recovery](docs/USAGE.md) explains task contracts, verification, and safe resume.

## What is supported

Package metadata, skill instructions, a Python control plane, and host-mediated dispatch are maintained in this repository. Host APIs, sandbox permissions, and model availability remain controlled by the coding host. Runtime evidence confirms checks that actually ran; it cannot prove that an agent's prose is true or prevent writes by tools that bypass the cooperative locks.

See [architecture](docs/ARCHITECTURE.md), [runtime contracts](docs/RUNTIME_INVARIANTS_SPECIFICATION.md), and the [implementation plan](docs/IMPLEMENTATION_PLAN.md) for boundaries and acceptance criteria. Support is marked implemented, experimental, or planned in the [support matrix](docs/SUPPORT_MATRIX.md).

## Development

Python 3.10 or newer is required for the runtime. It uses standard-library SQLite and subprocess support. Git is needed for repository installation and some diagnostics, not for every runtime operation.

```bash
python -m unittest discover -s scripts/supervisor/tests
python -m unittest discover -s tests
python scripts/doctor.py --host codex
```

CI exercises package validation and runtime behavior across its configured operating system matrix. Passing CI is distinct from a live host end-to-end run.

Rule export is optional. Inspect the target project's existing instructions before running `scripts/export_rules.py`. Existing files are preserved by default; `--replace` deliberately permits replacement. Do not replace project conventions merely to enable this plugin.

## License

[MIT](LICENSE).
