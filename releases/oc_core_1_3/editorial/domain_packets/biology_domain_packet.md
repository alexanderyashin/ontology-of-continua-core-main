# OC Core 1.3 / Biology Domain Packet

## Status Snapshot

- Current state: `VALIDATED_ANCHOR_ACTIVE`
- Target state: `VALIDATED_ANCHOR_ACTIVE`
- Scientific class: `THEOREM_NATIVE`
- Trace status: `TRACE_COMPLETE`
- Closure verdict: `PASS`
- Quantitative pass result: `PASS`
- Next required action: `MAINTENANCE_ONLY`
- Replay status: `PASS_REPLAYABLE`

## Theorem-to-Observable Map

- K4/K5/K6/K7 organizational thresholds lawfully generate the bounded biology packet over expression, state-transition, and response-onset observable families.
- The promoted biology packet binds source-native biological organization claims to pinned assay observables without expanding to unrestricted biological universalization.
- Every promoted biological benchmark family is traced through the locked K4/K5/K6/K7 route, open assay datasets, and held-out replay.

## Benchmark Dataset Manifest

- BIO_BENCH_001: expression_signature_residual | NCBI GEO | https://www.ncbi.nlm.nih.gov/geo/ | held-out: reserve one time-series family for held-out replay
- BIO_BENCH_002: state_transition_order_error | NCBI GEO | https://www.ncbi.nlm.nih.gov/geo/ | held-out: reserve one cell-state transition family
- BIO_BENCH_003: response_onset_residual | official open biological assay repositories | https://www.ncbi.nlm.nih.gov/geo/ | held-out: reserve one response-signature family

## Pinned Official Route Protocol

- BIO_ROUTE_001: NCBI GEO (OFFICIAL_OPEN_DATA_HUB) -> https://www.ncbi.nlm.nih.gov/geo/ | purpose: Open assay and expression benchmark families

## Measurable Outputs

- expression_signature_residual
- state_transition_order_error
- response_onset_residual

## Measurement Schema

Choose one bounded biological lane and evaluate predicted state transitions or response signatures against open assay data.

## Acceptance Criterion

The promoted biological packet reproduces the declared measurable signatures on held-out datasets without widening the claim boundary.

## Falsifier

If the bounded signature family fails on held-out datasets, the biological packet remains frontier-bound.

## Quantitative Acceptance Thresholds

- coverage_ratio_required: 1.0
- expected_calibration_error_max: 0.05
- normalized_error_max_max_sigma: 5.0
- normalized_error_mean_abs_max_sigma: 1.0
- normalized_error_p95_max_sigma: 2.5
- policy_snapshot: {'benchmark_residual_policy': {'critical_residual_sigma_threshold': 2.5, 'schema_id': 'LOGION_BENCHMARK_RESIDUAL_POLICY_v1', 'severe_residual_sigma_threshold': 1.5}, 'prediction_accuracy_policy': {'brier_score_max': 0.08, 'cases_total_required': 30, 'coverage_ratio_required': 1.0, 'critical_failure_f1_min': 0.87, 'critical_failure_precision_min': 0.85, 'critical_failure_recall_min': 0.9, 'expected_calibration_error_max': 0.05, 'schema_id': 'LOGION_PREDICTION_ACCURACY_POLICY_v2'}, 'prediction_sigma_policy': {'cases_total_min': 30, 'normalized_error_max_max_sigma': 5.0, 'normalized_error_mean_abs_max_sigma': 1.0, 'normalized_error_p95_max_sigma': 2.5, 'schema_id': 'LOGION_PREDICTION_SIGMA_POLICY_v1', 'tail_breach_count_max': 0}}
- tail_breach_count_max: 0

## Replay Harness

- Replay command: `logion/k7/spe/orchestrator/science/run_oc_core_domain_hard_closure_replay_v1.py --domain-id BIOLOGY`
- Evidence bar: `HYBRID_ESCALATION`
- Protocol id: `OC13::EXECUTION::BIOLOGY::STATE_TRANSITIONS_AND_RESPONSE_SIGNATURES`

## Institute-run Escalation

- Current escalation status: `NOT_REQUIRED_UNLESS_NEW_OBSERVABLE_FAMILY_ENTERS`
- Escalation trigger: `OPEN_DATA_COVERAGE_LT_1_0_OR_HELD_OUT_CASES_LT_30_OR_SIGNATURE_CLASS_UNDERCONSTRAINED`
- Measurement wave id: `INSTITUTE_RUN::BIOLOGY::WAVE_3A`
- Measurement plan: Run a bounded institute observation or assay campaign only for the explicitly declared biological lane; no widening of biological scope is allowed.

## Blocking IDs

- None.
