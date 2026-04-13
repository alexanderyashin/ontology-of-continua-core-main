# OC Core 1.3 / Mathematics Domain Packet

## Status Snapshot

- Current state: `VALIDATED_ANCHOR_ACTIVE`
- Target state: `VALIDATED_ANCHOR_ACTIVE`
- Quantitative pass result: `PASS`
- Next required action: `MAINTAIN_REPLAY_DISCIPLINE`
- Replay status: `PASS_REPLAYABLE`

## Theorem-to-Observable Map

- Pending explicit theorem-to-observable rows in the packet specification.

## Benchmark Dataset Manifest

- Pending explicit benchmark dataset rows.

## Pinned Official Route Protocol

- MATH_ROUTE_001: Clay Mathematics Institute (OFFICIAL_PROBLEM_CATALOG) -> https://www.claymath.org/millennium-problems/ | purpose: Exact benchmark anchor catalog
- MATH_ROUTE_002: American Institute of Mathematics (OFFICIAL_PROBLEM_CATALOG) -> https://aimath.org/problemlists/ | purpose: Supplementary exact-question corpus

## Measurable Outputs

- epsilon_star
- minimal_denominator
- minimal_augmentation_rank
- component_fiber_count
- move_connectivity_or_degree_bound
- strict_terminalized_total
- counterexample_executed_total
- python_evidence_executed_total

## Measurement Schema

Replay declared mathematical packets deterministically against the strict closure ledger and counterexample traces.

## Acceptance Criterion

No replay divergence and no surviving counterexample against the promoted packet.

## Falsifier

A single replay divergence or surviving counterexample collapses promotion for the affected packet.

## Quantitative Acceptance Thresholds

- counterexample_survivor_total_max: 0
- replay_divergence_total_max: 0
- strict_terminalized_total_min: 31

## Replay Harness

- Replay command: `logion/k7/spe/orchestrator/science/run_claim_simulations_v1.py`
- Replay program status: `ACTIVE_REPLAY_LANE`
- Execution protocol id: `OC13::EXECUTION::MATHEMATICS::ANCHOR_REPLAY`
- Evidence bar: `HYBRID_ESCALATION`

## Institute-run Escalation

- Current escalation status: `NOT_REQUIRED`
- Escalation trigger: `ONLY_IF_DETERMINISTIC_REPLAY_BREAKS`
- Measurement wave id: `NONE`
- Measurement plan: Expand the exact-question corpus instead of broadening claims.

## Blocking IDs

- None.
