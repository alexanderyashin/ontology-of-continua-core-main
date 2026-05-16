# OC Core 1.3 / Physics Domain Packet

## Status Snapshot

- Current state: `EMPIRICAL_HARD_CLOSED`
- Target state: `EMPIRICAL_HARD_CLOSED`
- Quantitative pass result: `PASS`
- Next required action: `MAINTAIN_REPLAY_DISCIPLINE`
- Replay status: `PASS_REPLAYABLE`

## Theorem-to-Observable Map

- K1/K2 contradiction-load and stabilization-margin operators bind to bounded physical observable families through regime-threshold maps.
- Root-law collapse boundaries are exposed as observable residual envelopes rather than as unrestricted physical universalization claims.
- The current packet is limited to benchmarked constants, spectral lines, and transport-scale residual families.

## Benchmark Dataset Manifest

- PHY_BENCH_001: fine_structure_constant_residual | NIST / CODATA constants | https://physics.nist.gov/cuu/Constants/index.html | held-out: leave-one-family-out residual verification
- PHY_BENCH_002: hydrogen_balmer_line_residual | NIST Atomic Spectra Database | https://physics.nist.gov/PhysRefData/ASD/lines_form.html | held-out: reserve transitions not used during packet fitting
- PHY_BENCH_003: transport_scaling_residual | DOE Office of Science challenge corpora | https://science.osti.gov/-/media/fes/pdf/workshop-reports/FES_Grand_Challenges_Report_final.pdf | held-out: hold out one transport regime family

## Pinned Official Route Protocol

- PHY_ROUTE_001: NIST (OFFICIAL_CONSTANTS_PORTAL) -> https://physics.nist.gov/cuu/Constants/index.html | purpose: Pinned constants and CODATA reference values
- PHY_ROUTE_002: NIST (OFFICIAL_SPECTRA_DATABASE) -> https://physics.nist.gov/PhysRefData/ASD/lines_form.html | purpose: Pinned spectral benchmark families
- PHY_ROUTE_003: U.S. Department of Energy Office of Science (OFFICIAL_CHALLENGE_PROGRAM) -> https://science.osti.gov/ascr | purpose: Transport or plasma-scale challenge framing and official program context

## Measurable Outputs

- relative_constant_error
- spectral_line_residual
- transport_scaling_residual

## Measurement Schema

Bind theorem-to-observable maps to pinned official constants and spectra, then evaluate held-out residual envelopes.

## Acceptance Criterion

Held-out residuals stay inside the declared tolerance band for every promoted benchmark family.

## Falsifier

Any benchmark family with residuals outside tolerance or with broken sign/order constraints falsifies the promoted packet.

## Quantitative Acceptance Thresholds

- coverage_ratio_required: 1.0
- critical_residual_sigma_threshold: 2.5
- normalized_error_max_max_sigma: 5.0
- normalized_error_mean_abs_max_sigma: 1.0
- normalized_error_p95_max_sigma: 2.5
- severe_residual_sigma_threshold: 1.5
- tail_breach_count_max: 0

## Replay Harness

- Replay command: `logion/k7/spe/orchestrator/science/run_oc_core_domain_hard_closure_replay_v1.py --domain-id PHYSICS`
- Replay program status: `ACTIVE_REPLAY_LANE`
- Execution protocol id: `OC13::EXECUTION::PHYSICS::CONSTANTS_SPECTRA_TRANSPORT`
- Evidence bar: `HYBRID_ESCALATION`

## Institute-run Escalation

- Current escalation status: `NOT_REQUIRED`
- Escalation trigger: `OPEN_DATA_COVERAGE_LT_1_0_OR_HELD_OUT_CASES_LT_30_OR_RESIDUAL_BREACH_PERSISTS`
- Measurement wave id: `INSTITUTE_RUN::PHYSICS::WAVE_1A`
- Measurement plan: Acquire partner or institute-run measurements for the missing observable family and rerun the held-out replay packet without widening scope.

## Blocking IDs

- None.
