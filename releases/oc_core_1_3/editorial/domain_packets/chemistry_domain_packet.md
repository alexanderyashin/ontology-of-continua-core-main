# OC Core 1.3 / Chemistry Domain Packet

## Status Snapshot

- Current state: `PACKETIZED_PENDING_QUANTITATIVE_VALIDATION`
- Target state: `EMPIRICAL_HARD_CLOSED`
- Quantitative pass result: `FAIL_CLOSED`
- Next required action: `EXECUTE_CHEMISTRY_NUMERICAL_REPLAY_PACKET`
- Replay status: `REPLAY_HARNESS_READY_PENDING_EXECUTION`

## Theorem-to-Observable Map

- K2/K3/K4 organizational thresholds are bound to thermochemical, spectroscopic, and kinetic observable families through constrained bridge maps.
- The packet is explicitly restricted to bounded chemistry benchmark families and does not claim general chemical closure.
- Only held-out thermochemical, spectral, and kinetic residual lanes are considered lawful validation targets.

## Benchmark Dataset Manifest

- {'authority_ref': 'NIST Chemistry WebBook', 'benchmark_id': 'CHEM_BENCH_001', 'dataset_url': 'https://webbook.nist.gov/chemistry/', 'held_out_policy': 'hold out one compound family from calibration', 'observable_name': 'gas_phase_enthalpy_residual'}
- {'authority_ref': 'NIST Chemistry WebBook', 'benchmark_id': 'CHEM_BENCH_002', 'dataset_url': 'https://webbook.nist.gov/chemistry/', 'held_out_policy': 'hold out one spectral family', 'observable_name': 'spectral_transition_residual'}
- {'authority_ref': 'DOE BES / EFRC challenge corpora', 'benchmark_id': 'CHEM_BENCH_003', 'dataset_url': 'https://science.osti.gov/bes/efrc/Research/Grand-Challenges', 'held_out_policy': 'hold out one reaction-class envelope', 'observable_name': 'kinetic_or_equilibrium_residual'}

## Measurable Outputs

- enthalpy_residual
- spectral_transition_residual
- kinetic_or_equilibrium_residual

## Measurement Schema

Map theorem packets to thermochemical, spectral, and kinetic observables against pinned reference tables.

## Acceptance Criterion

Declared chemistry benchmark families pass the tolerance envelope on held-out compounds or reactions.

## Falsifier

A held-out thermochemical, spectral, or kinetic family outside tolerance collapses the promoted chemistry packet.

## Replay Harness

- Replay command: `logion/k7/spe/orchestrator/science/run_oc_core_domain_hard_closure_replay_v1.py`
- Replay program status: `PROGRAM_DEFINED_PENDING_EXECUTION`

## Official / Open Source Routes

- U.S. Department of Energy Office of Science (OFFICIAL_GRAND_CHALLENGE_PAGE): https://science.osti.gov/bes/efrc/Research/Grand-Challenges

## Blocking IDs

- CHEMISTRY__NUMERICAL_PACKET_PASS_REQUIRED
- CHEMISTRY__REPLAY_PASS_REQUIRED
