# Repository hygiene report

- **Snapshot and mode:** <revision or snapshot, working-tree state, audit / plan / implement>
- **Scope and coverage:** <requested scope, areas inspected, relevant contracts and exclusions>
- **Summary:** <highest-value supported outcome and any consequential decisions to retain live paths>

## Confirmed cleanup findings

For each finding:

- **ID, category, location:** <stable ID, category, path and symbol or line>
- **Claim and evidence:** <what is unnecessary, observations or reproducible checks, supported paths ruled out, and evidence that would overturn the claim>
- **Benefit, risk, effort:** <low / medium / high for each, with reasons and affected contracts>
- **Recommendation and checks:** <change, observable acceptance checks, and stop or rollback condition>

## Hypotheses

<Give each hypothesis an ID and location. Label it probable or uncertain and give the missing evidence and next check.>

## Cleanup order

<List actionable IDs by priority and note prerequisites. Include scope, acceptance checks, and rollback for each task in plan mode. Give a no-change disposition if nothing qualifies.>

## Verification

<Record inspection, test, or measurement and its actual result. Identify relevant checks not run and why. In implement mode, include the changes made and unresolved failures.>
