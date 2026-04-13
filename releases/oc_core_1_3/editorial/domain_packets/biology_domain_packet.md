# OC Core 1.3 / Biology Domain Packet

## Status Snapshot

- Current state: `PACKETIZED_PENDING_QUANTITATIVE_VALIDATION`
- Target state: `EMPIRICAL_HARD_CLOSED`
- Quantitative pass result: `FAIL_CLOSED`
- Next required action: `EXECUTE_BIOLOGY_NUMERICAL_REPLAY_PACKET`
- Replay status: `REPLAY_HARNESS_READY_PENDING_EXECUTION`

## Theorem-to-Observable Map

- K4/K5/K6/K7 biological organization claims are restricted to bounded state-transition and response-signature lanes.
- The packet currently targets measurable expression and cell-state trajectories rather than unrestricted biological universalization.
- Open biological assay repositories are the first-line evidence route; if insufficient, the program escalates to institute-run measurement.

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
- tail_breach_count_max: 0

## Replay Harness

- Replay command: `logion/k7/spe/orchestrator/science/run_oc_core_domain_hard_closure_replay_v1.py`
- Replay program status: `PROGRAM_DEFINED_PENDING_EXECUTION`
- Execution protocol id: `OC13::EXECUTION::BIOLOGY::STATE_TRANSITIONS_AND_RESPONSE_SIGNATURES`
- Evidence bar: `HYBRID_ESCALATION`

## Institute-run Escalation

- Current escalation status: `STAND_BY_FOR_INSTITUTE_RUN_MEASUREMENT_IF_OPEN_DATA_IS_INSUFFICIENT`
- Escalation trigger: `OPEN_DATA_COVERAGE_LT_1_0_OR_HELD_OUT_CASES_LT_30_OR_SIGNATURE_CLASS_UNDERCONSTRAINED`
- Measurement wave id: `INSTITUTE_RUN::BIOLOGY::WAVE_3A`
- Measurement plan: Run a bounded institute observation or assay campaign only for the explicitly declared biological lane; no widening of biological scope is allowed.

## Blocking IDs

- BIOLOGY__NUMERICAL_PACKET_PASS_REQUIRED
- BIOLOGY__REPLAY_PASS_REQUIRED
