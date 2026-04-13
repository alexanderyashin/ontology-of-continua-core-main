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

- {'authority_ref': 'World Bank Indicators API', 'benchmark_id': 'SYS_BENCH_001', 'dataset_url': 'https://api.worldbank.org/v2/en/indicator/SP.POP.TOTL?format=json', 'held_out_policy': 'leave out one interval family', 'observable_name': 'population_trajectory_residual'}
- {'authority_ref': 'World Bank Indicators API', 'benchmark_id': 'SYS_BENCH_002', 'dataset_url': 'https://api.worldbank.org/v2/en/indicator/NY.GDP.MKTP.KD.ZG?format=json', 'held_out_policy': 'reserve one held-out macro interval', 'observable_name': 'gdp_growth_turning_point_error'}
- {'authority_ref': 'DOE ASCR process-systems references', 'benchmark_id': 'SYS_BENCH_003', 'dataset_url': 'https://science.osti.gov/ascr/Community-Resources/Workshops-and-Conferences/Grand-Challenges', 'held_out_policy': 'reserve one regime-shift benchmark family', 'observable_name': 'process_system_regime_score'}

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

## Replay Harness

- Replay command: `logion/k7/spe/orchestrator/science/run_oc_core_domain_hard_closure_replay_v1.py`
- Replay program status: `PROGRAM_DEFINED_PENDING_EXECUTION`

## Official / Open Source Routes

- U.S. Department of Energy Office of Science (OFFICIAL_GRAND_CHALLENGE_HUB): https://science.osti.gov/ascr/Community-Resources/Workshops-and-Conferences/Grand-Challenges
- World Bank (OFFICIAL_OPEN_DATA_API_DOCS): https://datahelpdesk.worldbank.org/knowledgebase/articles/889392-about-the-indicators-api-documentation

## Blocking IDs

- SYSTEMS_CIVILIZATIONAL_PROJECTION__NUMERICAL_PACKET_PASS_REQUIRED
- SYSTEMS_CIVILIZATIONAL_PROJECTION__REPLAY_PASS_REQUIRED
