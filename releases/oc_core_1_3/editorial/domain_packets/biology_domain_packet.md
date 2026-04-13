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

- {'authority_ref': 'NCBI GEO', 'benchmark_id': 'BIO_BENCH_001', 'dataset_url': 'https://www.ncbi.nlm.nih.gov/geo/', 'held_out_policy': 'reserve one time-series family for held-out replay', 'observable_name': 'expression_signature_residual'}
- {'authority_ref': 'NCBI GEO', 'benchmark_id': 'BIO_BENCH_002', 'dataset_url': 'https://www.ncbi.nlm.nih.gov/geo/', 'held_out_policy': 'reserve one cell-state transition family', 'observable_name': 'state_transition_order_error'}
- {'authority_ref': 'official open biological assay repositories', 'benchmark_id': 'BIO_BENCH_003', 'dataset_url': 'https://www.ncbi.nlm.nih.gov/geo/', 'held_out_policy': 'reserve one response-signature family', 'observable_name': 'response_onset_residual'}

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

## Replay Harness

- Replay command: `logion/k7/spe/orchestrator/science/run_oc_core_domain_hard_closure_replay_v1.py`
- Replay program status: `PROGRAM_DEFINED_PENDING_EXECUTION`

## Official / Open Source Routes

- U.S. National Center for Biotechnology Information (OFFICIAL_OPEN_DATA_HUB): https://www.ncbi.nlm.nih.gov/geo/

## Blocking IDs

- BIOLOGY__NUMERICAL_PACKET_PASS_REQUIRED
- BIOLOGY__REPLAY_PASS_REQUIRED
