# OC Core 1.3 / Mathematics Domain Packet

## Status Snapshot

- Current state: `VALIDATED_ANCHOR_ACTIVE`
- Target state: `VALIDATED_ANCHOR_ACTIVE`
- Scientific class: `THEOREM_NATIVE`
- Trace status: `TRACE_COMPLETE`
- Closure verdict: `PASS`
- Quantitative pass result: `PASS_TERMINALIZED_NUMERICAL_REPLAY`
- Next required action: `MAINTAIN_REPLAY_DISCIPLINE`
- Replay status: `PASS_REPLAYABLE`

## Theorem-to-Observable Map


## Benchmark Dataset Manifest


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
- policy_snapshot: {'benchmark_residual_policy': {'critical_residual_sigma_threshold': 2.5, 'schema_id': 'LOGION_BENCHMARK_RESIDUAL_POLICY_v1', 'severe_residual_sigma_threshold': 1.5}, 'prediction_accuracy_policy': {'brier_score_max': 0.08, 'cases_total_required': 30, 'coverage_ratio_required': 1.0, 'critical_failure_f1_min': 0.87, 'critical_failure_precision_min': 0.85, 'critical_failure_recall_min': 0.9, 'expected_calibration_error_max': 0.05, 'schema_id': 'LOGION_PREDICTION_ACCURACY_POLICY_v2'}, 'prediction_sigma_policy': {'cases_total_min': 30, 'normalized_error_max_max_sigma': 5.0, 'normalized_error_mean_abs_max_sigma': 1.0, 'normalized_error_p95_max_sigma': 2.5, 'schema_id': 'LOGION_PREDICTION_SIGMA_POLICY_v1', 'tail_breach_count_max': 0}}
- replay_divergence_total_max: 0
- strict_terminalized_total_min: 31

## Replay Harness

- Replay command: `simulations/run_all.py`
- Evidence bar: `HYBRID_ESCALATION`
- Protocol id: `OC13::EXECUTION::MATHEMATICS::ANCHOR_REPLAY`

## Institute-run Escalation

- Current escalation status: `NOT_REQUIRED`
- Escalation trigger: `ONLY_IF_DETERMINISTIC_REPLAY_BREAKS`
- Measurement wave id: ``
- Measurement plan: Expand the exact-question corpus instead of broadening claims.

## Blocking IDs

- None.
