# Audit evidence and ranking rubric

Use this rubric when distinguishing hypotheses from actionable findings.

## Confidence

- **Confirmed:** Reproducible evidence proves the path is unused, duplicated, or unnecessarily complex within the explicitly checked support surface; relevant dynamic/runtime/operational references have been considered.
- **Probable:** Strong static evidence, but an external caller, dynamic registration, or untested workflow could still use the code. Require additional inspection, instrumentation, or owner decision before deletion.
- **Uncertain:** Incomplete coverage or conflicting evidence. Keep as an investigation item; do not recommend removal yet.

## Benefit

- **High:** Eliminates significant maintenance burden, duplicated fragile policy, dependencies, or repeated expensive work; measured benefits where feasible.
- **Medium:** Meaningfully improves clarity, local complexity, or testability with limited blast radius.
- **Low:** Minor stylistic or local reduction; deprioritize unless nearly free.

## Risk

- **Low:** Internal-only, no persistent state/external contract, straightforward focused tests and rollback.
- **Medium:** Public/indirect callers, multi-module effects, runtime behavior, configuration, or operator workflows need checking.
- **High:** Auth/security, trust boundaries, schema/migrations, data durability, compatibility, remote side effects, deployment, or rollback. Requires explicit contract-level acceptance; keep separate from cosmetic cleanup.

## Verification patterns

| Candidate | Evidence to collect | Typical checks |
| --- | --- | --- |
| Unused function/file | Imports + dynamic references + entrypoint/config/CI scans | Static analyzer, targeted tests, smoke command |
| Duplicate logic | Compare semantics, edge cases, callers and trust boundaries | Equivalence tests, negative cases |
| Unused UI/CLI/API | Router/registration, clients, docs, telemetry if available | Endpoint/command smoke, compatibility |
| Obsolete schema or migration | Supported upgrade paths, persisted versions, rollback policy | Old-format fixtures, upgrade/rollback refusal |
| Redundant DB/API/network | Call graphs, actual traces or profiles when available | Query counts, microbenchmark, consistency tests |
| Disconnected artifact | Build manifests, CI, packaging, operator/recovery references | Package/build, docs-link/check scripts |

Do not automatically execute unknown repository code, package scripts, migrations, or networked checks during reconnaissance. Report the limitation and request appropriate authorization for execution.

## Priority suggestion

Assess each finding on **confidence, benefit, risk and effort**. Use qualitative ratings instead of manufacturing a single precision score. Work first on confirmed high-benefit low-risk items; treat high-risk findings as separate decisions even when their potential benefit is large.
