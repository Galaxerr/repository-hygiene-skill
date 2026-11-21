<div align="center">

# Repository Hygiene

**Make codebases smaller, clearer, and easier to maintain — without guessing what is safe to delete.**

A repository-wide cleanup skill for **Claude Code** and **OpenAI Codex**.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude_Code-plugin-6B4FBB)](#claude-code)
[![Codex](https://img.shields.io/badge/OpenAI_Codex-plugin-24292F)](#openai-codex)
[![Validation](https://github.com/Galaxerr/repository-hygiene-skill/actions/workflows/validate.yml/badge.svg)](https://github.com/Galaxerr/repository-hygiene-skill/actions/workflows/validate.yml)

[Installation](#installation) · [How it works](#how-it-works) · [Examples](#usage-examples) · [Safety](#safety-by-design) · [Contributing](#contributing) · [Security](SECURITY.md)

</div>

> [!IMPORTANT]
> **Audit first, change later.** Running Repository Hygiene does **not** automatically delete code, modify dependencies, run untrusted scripts, or publish changes. Implementation requires an explicit request.

## Why Repository Hygiene?

Codebases accumulate unused paths, duplicate validation, legacy compatibility layers, and disconnected scripts. A broad “delete dead code” prompt can find candidates — but it can also misidentify dynamically loaded modules, migration readers, recovery routines, and security checks as unused.

**Repository Hygiene turns cleanup into an evidence-based engineering workflow.** It maps the repository, checks candidates against actual entrypoints and contracts, ranks findings by confidence and risk, and proposes small, testable changes.

| Typical cleanup prompt | Repository Hygiene |
| --- | --- |
| Flags unreferenced code | Checks runtime registration, dynamic imports, scripts, CI, and operational paths |
| Suggests broad deletions | Separates **confirmed**, **probable**, and **uncertain** findings |
| Optimizes for fewer lines | Prioritizes maintainability and proven value over line count |
| Treats tests as disposable | Preserves tests that establish contracts, refusal behavior, and recovery |
| Mixes analysis and editing | Separates **Audit**, **Plan**, and **Implement** |

## What it audits

| Area | Examples |
| --- | --- |
| **Dead code** | Unused functions, imports, files, routes, dependencies, and entrypoints |
| **Duplication** | Repeated validation, serialization, business rules, and error handling |
| **Unused interfaces** | UI components, CLI commands, API endpoints, callbacks, and handlers |
| **Complexity** | Unnecessary indirection, oversized abstractions, avoidable state |
| **Legacy paths** | Superseded code, obsolete compatibility logic **when safe to retire** |
| **Redundant work** | Repeated database queries, filesystem reads, and network calls |
| **Disconnected artifacts** | Abandoned scripts, stale fixtures, unused configuration |
| **Technical debt** | Inconsistent conventions, maintenance hotspots, unnecessary dependencies |

Works across Python, JavaScript/TypeScript, Go, Rust, and mixed-language repositories. It adapts to projects without a frontend, database, or standard build system.

## Installation

The same skill is packaged for Claude Code and Codex marketplaces. Public installation commands target `Galaxerr/repository-hygiene-skill` and are pending release qualification.

### Claude Code

Run inside Claude Code:

```text
/plugin marketplace add Galaxerr/repository-hygiene-skill
/plugin install repo-hygiene@repo-hygiene-marketplace
```

Invoke:

```text
/repo-hygiene:repo-hygiene Audit this repository. Do not modify code.
```

### OpenAI Codex

In your terminal, with a marketplace-capable Codex installation:

```bash
codex plugin marketplace add Galaxerr/repository-hygiene-skill --ref main
codex plugin add repo-hygiene@repo-hygiene-marketplace
```

After a local marketplace install, Codex CLI 0.158.0 listed `repo-hygiene:repo-hygiene`. Model-backed invocation and public installation are pending qualification. Use this prompt with the skill selected:

```text
Audit this repository. Produce an evidence-backed cleanup plan.
```

> [!NOTE]
> Choose one Codex install route. For native discovery, copy the entire `plugins/repo-hygiene/skills/repo-hygiene` directory into `.agents/skills/` in the repository you want to audit. This includes the rubric, findings template, and MIT notice. Remove the copied directory to uninstall the native skill. [Codex skill discovery](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills)

### Local validation before publishing

From a clean Git checkout, use Git and Python 3.12 with `venv` and pip available.

```bash
validation_env=$(mktemp -d)
python3 -m venv "$validation_env"
source "$validation_env/bin/activate"
python3 -m pip install --only-binary=:all: -r tests/requirements.txt
python3 tests/validate_package.py
python3 tests/test_validate_package.py
```

GitHub Actions runs the same checks on pull requests and pushes to `main`. Both commands run offline after installing the validation dependencies. Use relative Markdown links to tracked files within the skill directory. Resource symlink targets must be tracked and use a relative path without parent traversal.

During release qualification, run the vendor checks and test installation in both clients.

```bash
claude plugin validate --strict ./plugins/repo-hygiene
claude plugin validate --strict .
```

## How it works

```text
Inspect repository
       │
       ▼
Map entrypoints, dependencies, contracts
       │
       ▼
Find cleanup candidates
       │
       ▼
Trace references + counterexamples
       │
       ▼
Rank confidence, impact, and risk
       │
       ├── Audit (default): findings + recommendations
       │
       ├── Plan: scoped, dependency-ordered tickets
       │
       └── Implement (explicitly requested):
                    small changes → focused tests → review
```

| Mode | Output | Changes application code? |
| --- | --- | --- |
| **Audit** (default) | Repository map, findings, evidence, risk, priorities | No |
| **Plan** | Cleanup workstreams, acceptance criteria, implementation order | No |
| **Implement** | Approved changes, verification results, remaining risks | Yes, only when explicitly requested |

The skill follows repository-local instructions such as `AGENTS.md` and `CLAUDE.md` where applicable. It can cooperate with existing planning and review skills but does not require them.

## Usage examples

**Audit a repository**

```text
/repo-hygiene:repo-hygiene Audit the entire codebase for dead code,
duplicate logic, obsolete modules, and unnecessary complexity.
Report confirmed findings separately from uncertain candidates.
Do not edit files.
```

**Focus on a subsystem**

```text
/repo-hygiene:repo-hygiene Audit the authentication and persistence
modules. Prioritize repeated validation and unnecessary database work.
Preserve all security and migration contracts.
```

**Build a cleanup plan**

```text
/repo-hygiene:repo-hygiene Plan the confirmed cleanup findings as
small, dependency-ordered tickets with acceptance tests and rollback risks.
```

**Implement a reviewed scope**

```text
/repo-hygiene:repo-hygiene Implement only the approved low-risk
cleanup ticket. Run targeted tests and report the exact diff and results.
Do not commit or push.
```

In Codex, select `repo-hygiene:repo-hygiene` for the marketplace skill or `repo-hygiene` for the native copy, then enter the remainder of the prompt.

### Example finding

> **RH-014 · Confirmed duplication · Medium priority**
>
> **Candidate:** Two internal validators independently normalize the same request fields.
>
> **Evidence:** Both call paths and their consumers were traced; no differing authorization policy was found.
>
> **Impact:** One shared normalization rule and fewer divergent edge cases. Performance improvement not claimed.
>
> **Risk:** Error messages or validation order could change.
>
> **Recommended action:** Consolidate the shared pure normalization logic, retain distinct authorization checks, and add contract tests before deleting either implementation.

*Illustrative example, not a finding from a real repository.*

## Safety by design

Repository Hygiene does not treat “zero static references” as proof of dead code. Before recommending removal, it checks relevant dynamic and operational use, including:

- Framework registration, dependency injection, reflection, and runtime imports.
- CLI commands, scheduled jobs, plugins, callbacks, and build entrypoints.
- CI workflows, deployment scripts, test fixtures, and operator runbooks.
- Database migrations, old-format readers, rollback paths, and persisted-state compatibility.
- Authentication, authorization, audit logs, idempotency, retries, and recovery semantics.

Unproven candidates remain **uncertain** rather than being silently removed. Performance improvements must be measured, not invented. Existing tests and release evidence are not deleted merely because they describe historical behavior.

**Default boundaries:** no live credentials or production data, no dependency installation, no execution of untrusted project scripts, and no commits, pushes, merges, or releases without explicit authorization.

## Output and prioritization

Every actionable finding should include its location, supporting evidence, confidence, expected benefit, deletion/refactor risks, affected contracts, and the smallest recommended verification path.

The included [audit rubric](plugins/repo-hygiene/skills/repo-hygiene/references/audit-rubric.md) guides confidence and priority. The [findings template](plugins/repo-hygiene/skills/repo-hygiene/assets/findings-template.md) provides a consistent report format.

A successful cleanup is **not** defined by lines deleted. It is defined by reduced unnecessary complexity with preserved behavior and demonstrated regression safety.

## Repository layout

```text
.claude-plugin/marketplace.json          Claude marketplace catalog
.agents/plugins/marketplace.json         Codex marketplace catalog
plugins/repo-hygiene/
  .claude-plugin/plugin.json             Claude plugin metadata
  plugin.json                            Codex plugin metadata
  skills/repo-hygiene/
    SKILL.md                             Portable Agent Skill
    LICENSE                              Bundled MIT notice
    agents/openai.yaml                   Codex presentation metadata
    references/audit-rubric.md           Evidence and risk rubric
    assets/findings-template.md          Report template
    tests/eval-cases.md                  Behavioral evaluation scenarios
tests/validate_package.py                Package structural checks
tests/test_validate_package.py           Validator regression tests
tests/requirements.txt                   Validation dependencies
.github/workflows/validate.yml           CI package validation
```

## Validation and limitations

The package includes structural checks and evaluation scenarios. **It is not a deterministic static analyzer:** the agent's findings depend on available repository context, tools, and runtime evidence.

A clean structural validation does not mean every suggested deletion is safe. For high-risk changes, use independent review, relevant integration tests, and owner approval. Some dynamic usages cannot be proven without executing the application in an appropriate test environment.

Use the [repeatable behavioral fixtures](tests/behavioral/README.md) to collect evidence from installed clients. The [manual evaluation matrix](plugins/repo-hygiene/skills/repo-hygiene/tests/eval-cases.md) covers additional scenarios involving dynamic references, historical schemas, security boundaries, and false positives.

## Contributing

Open public issues for ordinary bugs and proposals. Maintainers review issues and focused pull requests. Contributions use the project's MIT terms, without a separate contributor agreement or required sign-off. Use the [security policy](SECURITY.md) for vulnerability reporting.

For behavior changes, include a minimal, sanitized reproduction, the expected outcome, and verification evidence. Keep the skill portable and avoid mandatory runtime dependencies. Run the same package checks as CI. [Local validation commands](#local-validation-before-publishing)

## Releasing

1. Qualify the exact candidate commit locally. Require passing structural checks, CI and vendor validation, clean-profile installs from the local candidate, the native fallback, and the owner-approved behavioral evaluation policy. Check the README commands and inspect the candidate tree and installed payloads for sensitive or unintended files.
2. Confirm the private reporting entry is visible to a non-maintainer and that the repository owner has configured notifications before publishing the reporting instructions.
3. Match both manifest versions to the reviewed tag, starting with `v1.0.0`. After separate owner authorization for public exposure and any required tag creation, verify clean-profile marketplace installs and the native fallback from the advertised public source and ref. Confirm the release ref resolves to the qualified commit. Prefer a versioned install source where the host supports it and the exact flow passes testing.
4. With the qualification checks passed and private reporting verified, the repository owner explicitly approves the exact revision and manually publishes the reviewed tag's release. Record the tested and public commits, source and ref, CI run, evaluator, results, known limits, and owner approval. Include changes, tested client versions, limitations, and update or recovery steps in the release notes. Material changes require rerunning the affected checks.

## License

Keep the copyright and permission notices with distributed copies. The shared skill bundles a copy of the root notice for both marketplace installs and the native install. [MIT License](LICENSE)

---

<div align="center">

**Less unnecessary code. More confidence in what remains.**

Built for deliberate maintenance, not indiscriminate deletion.

</div>
