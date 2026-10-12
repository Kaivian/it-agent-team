# Support matrix

Statuses describe this repository, not a claim that every host or operating system has been tested on a real installation.

- **Implemented:** code or metadata exists with automated validation.
- **Experimental:** integration guidance or adapter exists, but live end-to-end behavior still needs host-specific validation.
- **Planned:** intended capability without a supported implementation.

| Capability | Status | Validation boundary |
| --- | --- | --- |
| Four engineering skills and scoped role definitions | Implemented | Frontmatter and references can be validated; behavioral decisions need forward evaluation |
| Codex plugin catalog | Implemented | Package checks; live install must be verified in the user's Codex version |
| Python task state, dependency scheduling, session history, checks and reports | Implemented | Runtime tests; inspect current CLI help for exact options |
| Cooperative cross-process file ownership | Implemented | Runtime contention tests; does not enforce writes made outside the runtime |
| Host-mediated Codex dispatch | Experimental | Envelope consumed by a real host agent; runtime does not spawn models itself |
| Serial execution when delegation is unavailable | Implemented | Host follows the same claim/check/submit contract |
| Recovery after worker failure | Implemented | Explicit stopped-worker confirmation; no automatic proof of host process death |
| Sequential batch workflow | Experimental | Skill coordinates sessions; not an unattended standalone model scheduler |
| Windows, Linux, macOS runtime | Experimental | CI matrix validates Python behavior; local verification may cover only one OS |
| Claude marketplace metadata | Experimental | Existing catalog retained; live installation and tool adaptation need separate validation |
| Gemini extension metadata | Experimental | Metadata retained; host-native dispatch is not yet validated |
| Cursor, Windsurf and Copilot rule export | Experimental | Instruction export, not equivalent agent orchestration |
| Automatic background watchdog and native worker lifecycle integration | Planned | Requires host APIs and lifecycle integration |
| Turnkey deployment or publishing | Planned | Would require explicit user scope, service integration, and verification |

A successful doctor run verifies the checks listed in its output. It does not confirm that a plugin is installed and enabled unless the host exposes a supported inspection mechanism and that check actually ran. A detected executable does not establish multi-agent capability.
