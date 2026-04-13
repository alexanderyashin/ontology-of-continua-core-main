# OC Core 1.3 / Physics Domain Packet

## Status Snapshot

- Current state: `PACKETIZED_PENDING_QUANTITATIVE_VALIDATION`
- Target state: `EMPIRICAL_HARD_CLOSED`
- Quantitative pass result: `FAIL_CLOSED`
- Next required action: `EXECUTE_PHYSICS_NUMERICAL_REPLAY_PACKET`
- Replay status: `REPLAY_HARNESS_READY_PENDING_EXECUTION`

## Theorem-to-Observable Map

- K1/K2 contradiction-load and stabilization-margin operators bind to bounded physical observable families through regime-threshold maps.
- Root-law collapse boundaries are exposed as observable residual envelopes rather than as unrestricted physical universalization claims.
- The current packet is limited to benchmarked constants, spectral lines, and transport-scale residual families.

## Benchmark Dataset Manifest

- {'authority_ref': 'NIST / CODATA constants', 'benchmark_id': 'PHY_BENCH_001', 'dataset_url': 'https://physics.nist.gov/cuu/Constants/index.html', 'held_out_policy': 'leave-one-family-out residual verification', 'observable_name': 'fine_structure_constant_residual'}
- {'authority_ref': 'NIST Atomic Spectra Database', 'benchmark_id': 'PHY_BENCH_002', 'dataset_url': 'https://physics.nist.gov/PhysRefData/ASD/lines_form.html', 'held_out_policy': 'reserve transitions not used during packet fitting', 'observable_name': 'hydrogen_balmer_line_residual'}
- {'authority_ref': 'DOE Office of Science challenge corpora', 'benchmark_id': 'PHY_BENCH_003', 'dataset_url': 'https://science.osti.gov/-/media/fes/pdf/workshop-reports/FES_Grand_Challenges_Report_final.pdf', 'held_out_policy': 'hold out one transport regime family', 'observable_name': 'transport_scaling_residual'}

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

## Replay Harness

- Replay command: `logion/k7/spe/orchestrator/science/run_oc_core_domain_hard_closure_replay_v1.py`
- Replay program status: `PROGRAM_DEFINED_PENDING_EXECUTION`

## Official / Open Source Routes

- U.S. Department of Energy Office of Science (OFFICIAL_GRAND_CHALLENGE_REPORT): https://science.osti.gov/-/media/hep/pdf/files/Banner-PDFs/QIS_Study_Group_Report.pdf
- U.S. Department of Energy Office of Science (OFFICIAL_GRAND_CHALLENGE_REPORT): https://science.osti.gov/-/media/fes/pdf/workshop-reports/FES_Grand_Challenges_Report_final.pdf

## Blocking IDs

- PHYSICS__NUMERICAL_PACKET_PASS_REQUIRED
- PHYSICS__REPLAY_PASS_REQUIRED
