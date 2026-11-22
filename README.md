<div align="center">

# Repository Hygiene

**Make codebases smaller, clearer, and easier to maintain.**

A shared Agent Skill for evidence-backed cleanup audits in **Claude Code** and **Codex CLI**.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude_Code-plugin-6B4FBB)](#claude-code)
[![Codex](https://img.shields.io/badge/OpenAI_Codex-plugin-24292F)](#openai-codex)
[![Validation](https://github.com/Galaxerr/repository-hygiene-skill/actions/workflows/validate.yml/badge.svg)](https://github.com/Galaxerr/repository-hygiene-skill/actions/workflows/validate.yml)

[Installation](#installation) · [How it works](#how-it-works) · [Examples](#usage-examples) · [Safety](#safety-by-design) · [Validation](#validation-and-limitations) · [Contributing](#contributing)

[Repository layout](#repository-layout) · [Release qualification](#release-qualification) · [Security](SECURITY.md) · [License](#license)

</div>

> [!IMPORTANT]
> **Audit first, change later.** Audits and plans are read-only by default. Implementation requires explicit authorization for the changes.

## Installation

Install from the published `v1.0.0` tag. Local installation checks used Claude Code 2.1.148 and Codex CLI 0.158.0 on Linux. The four desktop behavior cases used Codex CLI 0.171.0.

### Prerequisites

Have Git and the chosen client installed. For the audit, sign in to the client and open it from the root of the repository you want to audit. Choose one Codex route to avoid duplicate skill entries.

### Claude Code

Run in your shell:

```bash
claude plugin marketplace add 'https://github.com/Galaxerr/repository-hygiene-skill.git#v1.0.0'
claude plugin install repo-hygiene@repo-hygiene-marketplace
claude plugin list
```

Start a new session with `claude` in the target repository. Look for `/repo-hygiene:repo-hygiene` in slash-command completion and enter:

```text
/repo-hygiene:repo-hygiene Audit this repository for dead code and duplication. Report evidence, confidence, risk, and coverage gaps. Do not edit files or run project code.
```

To remove the user-scope install and its catalog, exit the session and run in your shell:

```bash
claude plugin uninstall repo-hygiene@repo-hygiene-marketplace
claude plugin marketplace remove repo-hygiene-marketplace
```

[Claude Code marketplace documentation](https://code.claude.com/docs/en/plugins/host-marketplace)

### OpenAI Codex

Run in your shell:

```bash
codex plugin marketplace add https://github.com/Galaxerr/repository-hygiene-skill.git --ref v1.0.0
codex plugin add repo-hygiene@repo-hygiene-marketplace
```

Start a new session with `codex` in the target repository. In the client, type `$repo-hygiene` to filter the skill picker and select **Repository Hygiene** with Enter. The installed skill ID is `repo-hygiene:repo-hygiene`. Append this prompt to the selected mention:

```text
Audit this repository for dead code and duplication. Report evidence, confidence, risk, and coverage gaps. Do not edit files or run project code.
```

To remove the plugin and its catalog, exit the session and run in your shell:

```bash
codex plugin remove repo-hygiene@repo-hygiene-marketplace
codex plugin marketplace remove repo-hygiene-marketplace
```

[OpenAI marketplace documentation](https://developers.openai.com/plugins/build/plugins#add-a-marketplace-from-the-cli)

### Native Codex fallback

From the target repository root, use a shell with `mktemp` and `cp`. Make sure `.agents/skills/repo-hygiene` does not exist before copying. Copy the complete skill directory so its rubric, template, and MIT notice travel with it.

```bash
(
  set -e
  test ! -e .agents/skills/repo-hygiene
  test ! -L .agents/skills/repo-hygiene
  checkout=$(mktemp -d)
  git clone --branch v1.0.0 --single-branch https://github.com/Galaxerr/repository-hygiene-skill.git "$checkout"
  mkdir -p .agents/skills
  cp -R "$checkout/plugins/repo-hygiene/skills/repo-hygiene" .agents/skills/
  printf 'Temporary source checkout: %s\n' "$checkout"
)
```

Start Codex in the target repository, type `$repo-hygiene`, select **Repository Hygiene**, and use the same audit prompt. The native skill ID is `repo-hygiene`. To uninstall, exit Codex and remove the `.agents/skills/repo-hygiene` directory you copied. The temporary source checkout can also be removed. Keep the copied skill out of commits unless you intend to share it with the repository.

[Codex skill discovery](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills)

### Upgrading and recovering

Each route pins the source to a release tag. The tag stays fixed while the default branch can advance. To upgrade, remove the current copy and repeat the installation with the newer qualified tag. To recover, remove the problematic copy and reinstall from a previously qualified tag. The first release has no earlier stable tag. Catalog refreshes are unnecessary for switching tags.

## How it works

Repository Hygiene traces dead-code and duplication candidates through entrypoints, runtime loading, and supported contracts before recommending changes.

| Mode | Behavior |
| --- | --- |
| **Audit** (default) | Maps the repository and reports cleanup candidates with evidence, confidence, risk, and any checks left unrun. |
| **Plan** | Produces ordered cleanup tasks with prerequisites, acceptance checks, and rollback risks. |
| **Implement** | Makes only explicitly authorized changes and reports the actual verification results. |

## Usage examples

### Try the ledger fixture

Follow the [behavioral fixture setup](tests/behavioral/README.md#prepare-each-case) to try the audit on a disposable ledger repository. Prepare a fresh dirty fixture and client session for the implementation prompt. Setup needs Bash, Git, tar, and Python 3. For native Codex, copy the skill into each fresh fixture before taking its baseline snapshot. Enter the prompts in the fixture repository with the skill selected as shown above.

### Example audit finding

The private `_obsolete_label` in [ledger/service.py](tests/behavioral/fixture/ledger/service.py#L4) has a definition and no callers in the fixture. The [operator runbook](tests/behavioral/fixture/README.md) identifies `public_export` as the library API and underscore-prefixed names as private. Confidence is high within this fixture. External consumers were outside the inspected scope. Removing the helper reduces unused code. An undiscovered caller would lose its formatter. Verify with the local contract suite and both CLI profiles.

### Example implementation approval

```text
I approve removing only the private formatter _obsolete_label in ledger/service.py
after verifying it is unused. Keep the v1 reader, restore path, and existing
staged, unstaged, and untracked changes. Run python3 -B -m unittest -v,
python3 -B -m ledger, and python3 -B -m ledger --profile extended.
Report the exact change and observed results. Do not stage, commit, or push.
```

Use the shipped [audit rubric](plugins/repo-hygiene/skills/repo-hygiene/references/audit-rubric.md) and [findings template](plugins/repo-hygiene/skills/repo-hygiene/assets/findings-template.md) to review the report.

## Safety by design

Check runtime registration, scripts, CI, and operational entrypoints before recommending deletion. Preserve supported migrations, authorization checks, and recovery paths. Mark uncertain candidates and missing coverage. Findings depend on the repository context, available tools, and runtime evidence.

Running untrusted project code, installing dependencies, accessing live systems, and committing or publishing changes require separate authorization.

## Repository layout

```text
.claude-plugin/marketplace.json          Claude Code catalog
.agents/plugins/marketplace.json         Codex catalog
plugins/repo-hygiene/
  .claude-plugin/plugin.json             Claude Code plugin manifest
  plugin.json                            Portable plugin manifest
  skills/repo-hygiene/
    SKILL.md                             Shared skill instructions
    LICENSE                              Bundled MIT notice
    agents/openai.yaml                   Codex presentation metadata
    references/audit-rubric.md           Evidence and risk rubric
    assets/findings-template.md          Report template
    tests/eval-cases.md                  Extended evaluation matrix
```

## Validation and limitations

Use the [repeatable behavioral evaluations](tests/behavioral/README.md) to verify installed-client behavior. The [extended evaluation matrix](plugins/repo-hygiene/skills/repo-hygiene/tests/eval-cases.md) covers additional scenarios. Package validation checks structure and file references. Test and review each proposed cleanup against the contracts it affects.

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

## Contributing

Open public issues for ordinary bugs and proposals. Maintainers review issues and focused pull requests. Contributions use the project's MIT terms, without a separate contributor agreement or required sign-off. Use the [security policy](SECURITY.md) for vulnerability reporting.

For behavior changes, include a minimal, sanitized reproduction, the expected outcome, and verification evidence. Keep the skill portable and avoid mandatory runtime dependencies. Run the same package checks as CI. [Local validation commands](#local-validation-before-publishing) · [Package validation workflow](.github/workflows/validate.yml)

## Release qualification

1. Qualify the exact candidate commit locally. Require passing structural checks, CI and vendor validation, clean-profile installs from the local candidate, the native fallback, and the owner-approved behavioral evaluation policy. Check the README commands and inspect the candidate tree and installed payloads for sensitive or unintended files.
2. Verify private reporting is enabled and the public Advisories page links to the private form. Confirm the owner has configured report notifications. Record signed-in reporter access and notification delivery as unverified when they cannot be tested, and require an explicit owner decision on that evidence gap before publishing.
3. Match both manifest versions to the reviewed tag, starting with `v1.0.0`. After separate owner authorization for public exposure and any required tag creation, verify clean-profile marketplace installs and the native fallback from the advertised public source and ref. Confirm the release ref resolves to the qualified commit. Prefer a versioned install source where the host supports it and the exact flow passes testing.
4. With the qualification checks passed and private reporting verified, the repository owner explicitly approves the exact revision and manually publishes the reviewed tag's release. Record the tested and public commits, source and ref, CI run, evaluator, results, known limits, and owner approval. Include changes, tested client versions, limitations, and update or recovery steps in the release notes. Material changes require rerunning the affected checks.

## License

Keep the copyright and permission notices with distributed copies. The shared skill bundles a copy of the root notice for both marketplace installs and the native install. [MIT License](LICENSE)

---

<div align="center">

**Evidence-backed cleanup for Claude Code and Codex.**

</div>
