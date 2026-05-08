# held_out_replay_spec

- Bundle: `CLOSURE_BUNDLE::MATHEMATICS`
- Claim: `MATHEMATICS`
- Phase: `PHASE_1_STABILIZE_CLOSED_CORE`
- Current artifact status: `COMPLETE`
- Current transition gate: `MAINTENANCE_ONLY`
- Task id: `TASK::MATHEMATICS::HELD_OUT_REPLAY_SPEC`
- Assignee role: `REPLAY_PROTOCOL_TRACK`
- Entry gate: `ENTRY_AFTER_DATA_ROUTE_LOCKS`
- Pass transition: `MARK_COMPLETE_AND_UNLOCK_PROMOTION_AUDIT`
- Fail transition: `KEEP_FAIL_CLOSED_AND_FORBID_PROMOTION`
- Held-out case ids: none

## Status

COMPLETE

## Acceptance Metrics

- `counterexample_survivor_total_max`: 0
- `policy_snapshot`: {'benchmark_residual_policy': {'critical_residual_sigma_threshold': 2.5, 'schema_id': 'LOGION_BENCHMARK_RESIDUAL_POLICY_v1', 'severe_residual_sigma_threshold': 1.5}, 'prediction_accuracy_policy': {'brier_score_max': 0.08, 'cases_total_required': 30, 'coverage_ratio_required': 1.0, 'critical_failure_f1_min': 0.87, 'critical_failure_precision_min': 0.85, 'critical_failure_recall_min': 0.9, 'expected_calibration_error_max': 0.05, 'schema_id': 'LOGION_PREDICTION_ACCURACY_POLICY_v2'}, 'prediction_sigma_policy': {'cases_total_min': 30, 'normalized_error_max_max_sigma': 5.0, 'normalized_error_mean_abs_max_sigma': 1.0, 'normalized_error_p95_max_sigma': 2.5, 'schema_id': 'LOGION_PREDICTION_SIGMA_POLICY_v1', 'tail_breach_count_max': 0}}
- `replay_divergence_total_max`: 0
- `strict_terminalized_total_min`: 31

## No Post Hoc Split Rule

HELD_OUT_SPLIT_IS_LOCKED_EX_ANTE_AND_MAY_NOT_BE_CHANGED_AFTER_REPLAY

## Acceptance Criterion

No replay divergence and no surviving counterexample against the promoted packet.

Refs:
- `simulations/run_all.py`
- `releases/oc_core_1_3/editorial/OC_CORE_1_3_SCIENCE_SPOT_latest.json`
- `OC_PUBLIC_EVIDENCE_SURFACE::OC_OPEN_QUESTION_LINKAGE_latest`
- `OC_PUBLIC_EVIDENCE_SURFACE::SCIENTIFIC_METHOD_AUTHORITY_latest`
- `OC_PUBLIC_EVIDENCE_SURFACE::OC_OPERATIONAL_FORMAL_SUBSET_latest`
- `OC_PUBLIC_EVIDENCE_SURFACE::DOMAIN_NUMERICAL_PREDICTION_REGISTRY_latest`
- `OC_PUBLIC_EVIDENCE_SURFACE::QUESTION_COMPUTATIONAL_EVIDENCE_latest`
- `OC_PUBLIC_EVIDENCE_SURFACE::OC_MATHEMATICS_STRICT_RESULT_LEDGER_latest`
- `OC_PUBLIC_EVIDENCE_SURFACE::OC_DOMAIN_HARD_CLOSURE_PACKET_SPECS_v1`
- `OC_PUBLIC_EVIDENCE_SURFACE::OC_DOMAIN_EMPIRICAL_EXECUTION_PROTOCOLS_v1`
- `releases/oc_core_1_3/editorial/DOMAIN_EXTERNAL_DATA_MANIFEST_latest.json`
- `releases/oc_core_1_3/editorial/DOMAIN_NUMERICAL_PACKET_REGISTRY_latest.json`
- `releases/oc_core_1_3/editorial/PREDICTION_REPLAY_LEDGER_latest.json`
- `releases/oc_core_1_3/editorial/DOMAIN_HARD_CLOSURE_EXECUTION_PROGRAM_latest.json`
- `OC_PUBLIC_EVIDENCE_SURFACE::BENCHMARK_RESIDUAL_POLICY_v1`
- `OC_PUBLIC_EVIDENCE_SURFACE::PREDICTION_SIGMA_POLICY_v1`
- `OC_PUBLIC_EVIDENCE_SURFACE::PREDICTION_ACCURACY_POLICY_v2`
- `releases/oc_core_1_3/editorial/DOMAIN_BENCHMARK_CASESET_latest.json`
- `releases/oc_core_1_3/editorial/DOMAIN_EXTERNAL_DATA_MANIFEST_latest.json`
- `releases/oc_core_1_3/editorial/DOMAIN_NUMERICAL_PACKET_REGISTRY_latest.json`
- `releases/oc_core_1_3/editorial/PREDICTION_REPLAY_LEDGER_latest.json`
- `releases/oc_core_1_3/editorial/science_sources/closure_bundles/mathematics/bundle.json`
