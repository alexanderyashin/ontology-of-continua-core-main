# OC Core 1.3 / Chemistry Domain Packet

## Status Snapshot

- Current state: `EMPIRICAL_HARD_CLOSED`
- Target state: `EMPIRICAL_HARD_CLOSED`
- Quantitative pass result: `PASS`
- Next required action: `MAINTAIN_REPLAY_DISCIPLINE`
- Replay status: `PASS_REPLAYABLE`

## Theorem-to-Observable Map

- K2/K3/K4 organizational thresholds are bound to thermochemical, spectroscopic, and kinetic observable families through constrained bridge maps.
- The packet is explicitly restricted to bounded chemistry benchmark families and does not claim general chemical closure.
- Only held-out thermochemical, spectral, and kinetic residual lanes are considered lawful validation targets.

## Benchmark Dataset Manifest

- CHEM_BENCH_001: gas_phase_enthalpy_residual | NIST Chemistry WebBook | https://webbook.nist.gov/chemistry/ | held-out: hold out one compound family from calibration
- CHEM_BENCH_002: spectral_transition_residual | NIST Chemistry WebBook | https://webbook.nist.gov/chemistry/ | held-out: hold out one spectral family
- CHEM_BENCH_003: kinetic_or_equilibrium_residual | DOE BES / EFRC challenge corpora | https://science.osti.gov/bes/efrc/Research/Grand-Challenges | held-out: hold out one reaction-class envelope

## Pinned Official Route Protocol

- CHEM_ROUTE_001: NIST (OFFICIAL_CHEMISTRY_REFERENCE) -> https://webbook.nist.gov/chemistry/ | purpose: Thermochemistry and spectroscopy reference tables
- CHEM_ROUTE_002: U.S. Department of Energy Office of Science (OFFICIAL_CHALLENGE_PROGRAM) -> https://science.osti.gov/bes/efrc/Research/Grand-Challenges | purpose: Grand-challenge chemistry benchmark framing

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

## Quantitative Acceptance Thresholds

- coverage_ratio_required: 1.0
- critical_residual_sigma_threshold: 2.5
- normalized_error_max_max_sigma: 5.0
- normalized_error_mean_abs_max_sigma: 1.0
- normalized_error_p95_max_sigma: 2.5
- severe_residual_sigma_threshold: 1.5
- tail_breach_count_max: 0

## Replay Harness

- Replay command: `logion/k7/spe/orchestrator/science/run_oc_core_domain_hard_closure_replay_v1.py --domain-id CHEMISTRY`
- Replay program status: `ACTIVE_REPLAY_LANE`
- Execution protocol id: `OC13::EXECUTION::CHEMISTRY::THERMOCHEMISTRY_SPECTRA_KINETICS`
- Evidence bar: `HYBRID_ESCALATION`

## Institute-run Escalation

- Current escalation status: `NOT_REQUIRED`
- Escalation trigger: `OPEN_DATA_COVERAGE_LT_1_0_OR_HELD_OUT_CASES_LT_30_OR_RESIDUAL_BREACH_PERSISTS`
- Measurement wave id: `INSTITUTE_RUN::CHEMISTRY::WAVE_2A`
- Measurement plan: Acquire targeted laboratory or partner measurements for unsupported thermochemical, spectral, or kinetic families before any positive promotion.

## Blocking IDs

- None.
