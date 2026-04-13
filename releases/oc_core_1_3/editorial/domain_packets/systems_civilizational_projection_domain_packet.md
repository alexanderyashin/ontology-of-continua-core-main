# OC Core 1.3 / Systems / Civilizational projection Domain Packet

## Status Snapshot

- Current state: `PACKETIZED_PENDING_QUANTITATIVE_VALIDATION`
- Target state: `EMPIRICAL_HARD_CLOSED`
- Quantitative pass result: `FAIL_CLOSED`
- Next required action: `EXECUTE_SYSTEMS_NUMERICAL_REPLAY_PACKET`
- Replay status: `REPLAY_HARNESS_READY_PENDING_EXECUTION`

## Theorem-to-Observable Map

- K8 projection claims are restricted to measurable macro-process trajectories and regime-shift signatures on pinned official series.
- The packet is source-native only at the bounded projection level and does not authorize unrestricted civilizational prediction.
- Validation is lawful only through held-out interval replay against official macro/process data.

## Benchmark Dataset Manifest

- SYS_BENCH_001: population_trajectory_residual | World Bank Indicators API | https://api.worldbank.org/v2/en/indicator/SP.POP.TOTL?format=json | held-out: leave out one interval family
- SYS_BENCH_002: gdp_growth_turning_point_error | World Bank Indicators API | https://api.worldbank.org/v2/en/indicator/NY.GDP.MKTP.KD.ZG?format=json | held-out: reserve one held-out macro interval
- SYS_BENCH_003: process_system_regime_score | DOE ASCR process-systems references | https://science.osti.gov/ascr/Community-Resources/Workshops-and-Conferences/Grand-Challenges | held-out: reserve one regime-shift benchmark family

## Pinned Official Route Protocol

- SYS_ROUTE_001: World Bank (OFFICIAL_OPEN_DATA_API_DOCS) -> https://datahelpdesk.worldbank.org/knowledgebase/articles/889392-about-the-indicators-api-documentation | purpose: Pinned macro indicator route and API semantics
- SYS_ROUTE_002: U.S. Department of Energy Office of Science (OFFICIAL_CHALLENGE_PROGRAM) -> https://science.osti.gov/ascr | purpose: Process-systems and high-performance systems benchmark framing

## Measurable Outputs

- trajectory_residual
- turning_point_error
- held_out_interval_regime_score

## Measurement Schema

Evaluate K8 projection packets against pinned official macro-process series with held-out interval tests.

## Acceptance Criterion

Declared trajectory and regime-change observables remain inside tolerance on held-out intervals.

## Falsifier

A missed turning point or out-of-band held-out trajectory falsifies the promoted systems packet.

## Quantitative Acceptance Thresholds

- brier_score_max: 0.08
- coverage_ratio_required: 1.0
- critical_failure_f1_min: 0.87
- critical_failure_precision_min: 0.85
- critical_failure_recall_min: 0.9
- expected_calibration_error_max: 0.05
- tail_breach_count_max: 0

## Replay Harness

- Replay command: `logion/k7/spe/orchestrator/science/run_oc_core_domain_hard_closure_replay_v1.py`
- Replay program status: `PROGRAM_DEFINED_PENDING_EXECUTION`
- Execution protocol id: `OC13::EXECUTION::SYSTEMS::MACRO_TRAJECTORIES_AND_REGIME_SHIFTS`
- Evidence bar: `HYBRID_ESCALATION`

## Institute-run Escalation

- Current escalation status: `STAND_BY_FOR_INSTITUTE_RUN_MEASUREMENT_IF_OPEN_DATA_IS_INSUFFICIENT`
- Escalation trigger: `OPEN_DATA_COVERAGE_LT_1_0_OR_HELD_OUT_INTERVAL_COUNT_LT_30_OR_TURNING_POINT_BREACH_PERSISTS`
- Measurement wave id: `INSTITUTE_RUN::SYSTEMS::WAVE_4A`
- Measurement plan: Acquire partner or institute-run observation programs for the missing macro-process lane and rerun the held-out interval evaluation without broadening civilizational claims.

## Blocking IDs

- SYSTEMS_CIVILIZATIONAL_PROJECTION__NUMERICAL_PACKET_PASS_REQUIRED
- SYSTEMS_CIVILIZATIONAL_PROJECTION__REPLAY_PASS_REQUIRED
