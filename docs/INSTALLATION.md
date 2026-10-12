# Installation

## Codex

Python 3.10 or newer and a Codex CLI with native plugin commands are required by the installer. Git is needed to clone or update the repository. Runtime commands operate locally and do not require Git for every task.

After the repository changes are published, use the Codex CLI:

```bash
codex plugin marketplace add Kaivian/it-agent-team
codex plugin add agent-team@it-agent-team
codex plugin list --json
```

Before publication, register an existing local checkout:

```bash
codex plugin marketplace add /absolute/path/to/it-agent-team
codex plugin add agent-team@it-agent-team
codex plugin list --json
```

The catalog is `.agents/plugins/marketplace.json`. Skill discovery uses the package's `skills/` directory. If the installed Codex version lacks these commands, use the app's supported plugin installation interface rather than editing its configuration by hand.

The wrapper performs validation and native Codex registration from the checkout:

```powershell
./install.ps1 -HostName codex
```

```bash
bash install.sh --host codex
```

By default, the target is the installer's own package. To install from another existing checkout or clone into an absent directory, use `-TargetDir <path>` or `--target-dir <path>`. An update requires `-Update` or `--update`; it fast-forwards a clean checkout with the expected origin and fails on Git errors.

For isolated installation testing, use `-CodexHome <directory>` or `--codex-home <directory>`. This scopes native Codex configuration/cache writes to that directory. The installer preserves unrelated configuration rather than rebuilding it.

Verify from the checkout:

```bash
python scripts/validate_package.py
python scripts/doctor.py --host codex --json
```

Open a new chat to load revised skill instructions. The installer can register a source, but the exact installed/enabled state is confirmed only by successful native inspection. For update or removal commands, consult `codex plugin --help` in the installed version.

## State directory check

To probe an existing project's state directory:

```bash
python scripts/doctor.py --host codex --state-dir /absolute/path/to/project/.agent-team --json
```

The directory must already exist. This probe verifies writability, not task completion or host delegation.

## Legacy Gemini registry

`--host gemini` is a compatibility path for the legacy registry used by earlier versions of this plugin. It preserves JSON configuration and refuses malformed data. Forwarding skill wrappers point to the canonical package files so plugin-relative resources remain resolvable; keep that package available. This does not establish that the current Gemini CLI's native extension installation or agent tools are compatible.

```powershell
./install.ps1 -HostName gemini -ConfigFile <config.json> -SkillsDir <skills-directory>
```

```bash
bash install.sh --host gemini --config-file <config.json> --skills-dir <skills-directory>
```

Use `python scripts/doctor.py --host gemini --config-file <config.json>` to inspect that registry. Native Gemini extension support requires separate validation.

## Other hosts and optional rule export

Claude marketplace metadata and Gemini extension metadata are retained as experimental integrations. Rule export for Cursor, Windsurf and Copilot installs instructions, not a model scheduler.

```bash
python scripts/export_rules.py /path/to/project --platform universal
```

Existing instruction files are preserved by default. Inspect them and use `--replace` only when replacement is intended. Exporting rules does not override the project's requirements or grant permission for external actions.
