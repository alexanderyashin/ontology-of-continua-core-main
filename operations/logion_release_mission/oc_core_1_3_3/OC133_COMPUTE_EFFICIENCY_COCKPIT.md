# OC133 Compute Efficiency Cockpit

- State: `COMPUTE_EFFICIENCY_GUARD_ACTIVE`
- Owner budget signal: `48%` remaining; risk `HIGH`
- Final readiness state: `SCIENTIFIC_BLOCKERS_REMAIN`
- Known blockers: `2`
- Top planning-only rows: `6` / `10`
- Repeated work orders above threshold: `1`
- Next economical action: `ROUTE_REAL_EXECUTOR_FOR_OC133-ALLDOMAIN-COVERAGE-MS-COV-WO-003`
- Reason: The current top work order only validates the planning queue; rerunning it cannot close a scientific blocker.

## Guardrails

- Default active subagents: `0`; maximum active subagents: `1`.
- Full Cerberus/release/reproducibility runs stay blocked until deterministic blocker delta exists.
- Planning-only rows must be routed to real Logion executors before they may consume execution budget.
- Focused checks only after artifact edits; broad suites only at milestone boundaries.

## Top Queue

- `1` `OC133-ALLDOMAIN-COVERAGE-MS-COV-WO-003` -> `planning_queue_validation` / `Logion Formal Methods / Proof-Route Planning`
- `2` `OC133-ALLDOMAIN-COVERAGE-MS-COV-WO-001` -> `planning_queue_validation` / `Logion Formal Methods / Proof-Route Planning`
- `3` `OC133-ALLDOMAIN-COVERAGE-MS-COV-WO-002` -> `planning_queue_validation` / `Logion Formal Methods / Proof-Route Planning`
- `4` `OC133-ALLDOMAIN-COVERAGE-MS-COV-WO-016` -> `planning_queue_validation` / `Logion Health Evidence / Regulated Clinical and Epidemiology Sources`
- `5` `OC133-ALLDOMAIN-COVERAGE-MS-COV-WO-017` -> `planning_queue_validation` / `Logion Health Evidence / Regulated Clinical and Epidemiology Sources`

Audit hash: `46b4b76aa11be3c5faf69600b499443ca6cca515d45fbe350cb5210b27680510`
