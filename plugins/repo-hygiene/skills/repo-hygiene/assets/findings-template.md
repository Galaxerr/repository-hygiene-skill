# Repository hygiene audit — <repository>

- **Scope:** <root/ref/commit, branch and dirty-state note>
- **Mode:** audit / plan / implement
- **Coverage:** <subsystems actually inspected>
- **Not inspected / limitations:** <explicit exclusions>
- **Applicable contracts:** <document/entrypoint/schema/security/release sources>

## Executive summary

- Confirmed findings: <count, if known>
- Probable / uncertain hypotheses: <count>
- Best near-term simplifications: <brief summary>
- Behavior/security compatibility posture: <what must remain invariant>

## Finding H-001 — <short title>

- **Category / priority:** <dead / duplicate / interface / complexity / legacy / operations / artifact / debt> | <priority>
- **Location:** `<path:lines>` — `<symbol or artifact>`
- **Evidence:** <references, code paths, commands, actual observations>
- **Counterchecks:** <dynamic, packaging, CI, operators, migration, recovery, external consumers>
- **Confidence:** confirmed / probable / uncertain
- **Why unnecessary or complex:** <specific cause>
- **Estimated benefit:** <reasoned qualitative estimate or measured quantity>
- **Risks / preserved contracts:** <specific side effects and backwards-compatibility concerns>
- **Recommendation:** remove / consolidate / simplify / retain / investigate
- **Acceptance and tests:** <exact observable checks>
- **Rollback or stop condition:** <how to recognize/regress/restore>

Repeat once per finding. State when a candidate is not actionable.

## Workstream plan

| Order | Ticket | Findings | Scope | Acceptance / dependencies | Risk |
| --- | --- | --- | --- | --- | --- |
| 1 | <...> | H-001 | <...> | <...> | low |

## Verification ledger

| Check | Actual result | Evidence or limitation |
| --- | --- | --- |
| <command or inspection> | PASS / FAIL / NOT RUN | <what it proves> |

## Final disposition

<Highest-value ready ticket, owner decisions or blockers, and explicit claims not yet verified.>
