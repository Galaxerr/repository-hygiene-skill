# Audit rubric

## Evidence and confidence

Record the candidate, exact location, checked support surface, and observations that establish the claim. For negative evidence, record what was searched and where. Check relevant:

| Surface | Evidence to trace |
| --- | --- |
| Runtime and build | Direct callers, reflection, computed names, registration by convention, plugins, generated inputs and outputs, build targets, packaging and import or startup side effects |
| Configuration and operations | Supported flags, profiles and platforms, CI, scheduled tasks, operator runbooks, maintenance commands, fallback, restore and rollback paths |
| Contracts and state | Published interfaces and downstream consumers, supported upgrade paths, persisted formats, retention requirements, and trust boundaries |

- **Confirmed:** Reproducible evidence establishes the claim across the relevant supported paths. For dead code, show why the candidate is unreachable or unconsumed. For example, trace all entrypoints that can reach a private symbol and rule out applicable indirect routes. Bound the claim to the checked support surface. A relevant inaccessible consumer, configuration, or workflow prevents confirmation.
- **Probable:** Strong evidence supports the claim, but a specific plausible path or obligation remains unchecked. Name the check or owner evidence needed.
- **Uncertain:** Evidence is sparse, conflicting, or too incomplete to bound the claim. State the gap.

A positive reference is evidence of use when its caller or workflow is supported. Verify that a reference can be reached before counting it. Historical references alone establish neither current use nor retirement. If a supported path reaches the candidate, retain it as a live path and report it only when it explains a decision or supports a separate finding.

## Benefit, risk, and effort

Assess each independently of confidence. Use high, medium, or low with a short reason.

- **Benefit:** High for substantial maintenance burden or repeated expensive work removed. Medium for meaningful local simplification. Low for minor or stylistic gains. Label estimates and give numbers only when measured.
- **Risk:** Low for isolated internals with straightforward verification and reversal. Medium for cross-module or runtime effects with bounded consumers. High for possible effects on public or external contracts, security, persistent data, compatibility, deployment, or recovery. Name the concrete failure and affected consumers or state. Consider whether reverting code can undo the effects. Keep high-risk changes separate with contract checks and any required owner decision.
- **Effort:** Include evidence gathering, implementation, verification, and coordination.

## Checks matched to the claim

- **Unused code or artifacts:** Verify reachability from entrypoints, build outputs, packages, and operational workflows. Use targeted build or smoke checks where relevant.
- **Duplicate logic:** Compare outcomes, errors, side effects, and ordering. Preserve enforcement at each independent trust boundary. Verify negative as well as successful cases.
- **Compatibility and recovery:** Identify supported versions, failure modes, and retirement policy. Verify old data, upgrade and rollback paths, or recovery with representative fixtures.
- **Redundant operations:** Verify whether retries, freshness, consistency, or observability require the work. Use measurements for runtime claims.
