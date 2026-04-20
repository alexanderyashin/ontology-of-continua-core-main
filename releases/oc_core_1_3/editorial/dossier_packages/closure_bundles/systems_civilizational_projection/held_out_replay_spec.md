# held_out_replay_spec

- Bundle: `CLOSURE_BUNDLE::SYSTEMS_CIVILIZATIONAL_PROJECTION`
- Claim: `SYSTEMS_CIVILIZATIONAL_PROJECTION`
- Phase: `PHASE_6_SYSTEMS_CLOSURE`
- Current artifact status: `COMPLETE`
- Current transition gate: `MAINTENANCE_ONLY`
- Task id: `TASK::SYSTEMS_CIVILIZATIONAL_PROJECTION::HELD_OUT_REPLAY_SPEC`
- Assignee role: `REPLAY_PROTOCOL_TRACK`
- Entry gate: `ENTRY_AFTER_DATA_ROUTE_LOCKS`
- Pass transition: `MARK_COMPLETE_AND_UNLOCK_PROMOTION_AUDIT`
- Fail transition: `KEEP_FAIL_CLOSED_AND_FORBID_PROMOTION`
- Held-out case ids: SYS_CASE_005_POP_BRA, SYS_CASE_006_POP_ZAF, SYS_CASE_007_POP_JPN, SYS_CASE_008_POP_FRA, SYS_CASE_009_POP_MEX, SYS_CASE_010_POP_IDN, SYS_CASE_015_GDPGROWTH_BRA, SYS_CASE_016_GDPGROWTH_ZAF, SYS_CASE_017_GDPGROWTH_JPN, SYS_CASE_018_GDPGROWTH_FRA, SYS_CASE_019_GDPGROWTH_MEX, SYS_CASE_020_GDPGROWTH_IDN, SYS_CASE_025_ENERGYUSE_BRA, SYS_CASE_026_ENERGYUSE_ZAF, SYS_CASE_027_ENERGYUSE_JPN, SYS_CASE_028_ENERGYUSE_FRA, SYS_CASE_029_ENERGYUSE_MEX, SYS_CASE_030_ENERGYUSE_IDN

## Status

COMPLETE

## Calibration Case Ids

- SYS_CASE_001_POP_USA
- SYS_CASE_002_POP_CHN
- SYS_CASE_003_POP_IND
- SYS_CASE_004_POP_DEU
- SYS_CASE_011_GDPGROWTH_USA
- SYS_CASE_012_GDPGROWTH_CHN
- SYS_CASE_013_GDPGROWTH_IND
- SYS_CASE_014_GDPGROWTH_DEU
- SYS_CASE_021_ENERGYUSE_USA
- SYS_CASE_022_ENERGYUSE_CHN
- SYS_CASE_023_ENERGYUSE_IND
- SYS_CASE_024_ENERGYUSE_DEU

## Held Out Case Ids

- SYS_CASE_005_POP_BRA
- SYS_CASE_006_POP_ZAF
- SYS_CASE_007_POP_JPN
- SYS_CASE_008_POP_FRA
- SYS_CASE_009_POP_MEX
- SYS_CASE_010_POP_IDN
- SYS_CASE_015_GDPGROWTH_BRA
- SYS_CASE_016_GDPGROWTH_ZAF
- SYS_CASE_017_GDPGROWTH_JPN
- SYS_CASE_018_GDPGROWTH_FRA
- SYS_CASE_019_GDPGROWTH_MEX
- SYS_CASE_020_GDPGROWTH_IDN
- SYS_CASE_025_ENERGYUSE_BRA
- SYS_CASE_026_ENERGYUSE_ZAF
- SYS_CASE_027_ENERGYUSE_JPN
- SYS_CASE_028_ENERGYUSE_FRA
- SYS_CASE_029_ENERGYUSE_MEX
- SYS_CASE_030_ENERGYUSE_IDN

## Acceptance Metrics

- `brier_score_max`: 0.08
- `coverage_ratio_required`: 1.0
- `critical_failure_f1_min`: 0.87
- `critical_failure_precision_min`: 0.85
- `critical_failure_recall_min`: 0.9
- `expected_calibration_error_max`: 0.05
- `policy_snapshot`: {'benchmark_residual_policy': {'critical_residual_sigma_threshold': 2.5, 'schema_id': 'LOGION_BENCHMARK_RESIDUAL_POLICY_v1', 'severe_residual_sigma_threshold': 1.5}, 'prediction_accuracy_policy': {'brier_score_max': 0.08, 'cases_total_required': 30, 'coverage_ratio_required': 1.0, 'critical_failure_f1_min': 0.87, 'critical_failure_precision_min': 0.85, 'critical_failure_recall_min': 0.9, 'expected_calibration_error_max': 0.05, 'schema_id': 'LOGION_PREDICTION_ACCURACY_POLICY_v2'}, 'prediction_sigma_policy': {'cases_total_min': 30, 'normalized_error_max_max_sigma': 5.0, 'normalized_error_mean_abs_max_sigma': 1.0, 'normalized_error_p95_max_sigma': 2.5, 'schema_id': 'LOGION_PREDICTION_SIGMA_POLICY_v1', 'tail_breach_count_max': 0}}
- `tail_breach_count_max`: 0

## No Post Hoc Split Rule

HELD_OUT_SPLIT_IS_LOCKED_EX_ANTE_AND_MAY_NOT_BE_CHANGED_AFTER_REPLAY

## Acceptance Criterion

Declared trajectory and regime-change observables remain inside tolerance on held-out intervals.

Refs:
- `logion/k7/spe/orchestrator/science/run_oc_core_domain_hard_closure_replay_v1.py --domain-id SYSTEMS_CIVILIZATIONAL_PROJECTION`
- `releases/oc_core_1_3/editorial/OC_CORE_1_3_SCIENCE_SPOT_latest.json`
- `logion/k0/governance/status/OC_CORE_1_3_K_LEVEL_SYSTEM_latest.json`
- `logion/k0/governance/status/OC_CORE_ROOT_REVISION_LEDGER_latest.json`
- `logion/k0/governance/status/ROOT_PRINCIPLE_THEOREM_STACK_latest.json`
- `logion/k0/governance/status/OC_DOMAIN_INCLUSION_VERDICT_LEDGER_latest.json`
- `logion/k7/spe/registry/OC_DOMAIN_HARD_CLOSURE_PACKET_SPECS_v1.json`
- `logion/k0/governance/status/DOMAIN_NUMERICAL_PREDICTION_REGISTRY_latest.json`
- `logion/k0/governance/status/QUESTION_COMPUTATIONAL_EVIDENCE_latest.json`
- `logion/k0/governance/status/OC_MATHEMATICS_STRICT_RESULT_LEDGER_latest.json`
- `logion/k7/spe/registry/OC_DOMAIN_EMPIRICAL_EXECUTION_PROTOCOLS_v1.json`
- `logion/k0/governance/status/DOMAIN_EXTERNAL_DATA_MANIFEST_latest.json`
- `logion/k0/governance/status/DOMAIN_NUMERICAL_PACKET_REGISTRY_latest.json`
- `logion/k0/governance/status/PREDICTION_REPLAY_LEDGER_latest.json`
- `logion/k0/governance/status/DOMAIN_HARD_CLOSURE_EXECUTION_PROGRAM_latest.json`
- `logion/k7/spe/registry/BENCHMARK_RESIDUAL_POLICY_v1.json`
- `logion/k7/spe/registry/PREDICTION_SIGMA_POLICY_v1.json`
- `logion/k7/spe/registry/PREDICTION_ACCURACY_POLICY_v2.json`
- `logion/k0/governance/status/DOMAIN_BENCHMARK_CASESET_latest.json`
- `releases/oc_core_1_3/editorial/DOMAIN_EXTERNAL_DATA_MANIFEST_latest.json`
- `releases/oc_core_1_3/editorial/DOMAIN_NUMERICAL_PACKET_REGISTRY_latest.json`
- `releases/oc_core_1_3/editorial/PREDICTION_REPLAY_LEDGER_latest.json`
- `releases/oc_core_1_3/editorial/science_sources/closure_bundles/systems_civilizational_projection/bundle.json`
