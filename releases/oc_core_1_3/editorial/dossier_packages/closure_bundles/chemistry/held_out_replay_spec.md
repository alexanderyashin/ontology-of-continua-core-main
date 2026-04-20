# held_out_replay_spec

- Bundle: `CLOSURE_BUNDLE::CHEMISTRY`
- Claim: `CHEMISTRY`
- Phase: `PHASE_4_CHEMISTRY_CLOSURE`
- Current artifact status: `COMPLETE`
- Current transition gate: `MAINTENANCE_ONLY`
- Task id: `TASK::CHEMISTRY::HELD_OUT_REPLAY_SPEC`
- Assignee role: `REPLAY_PROTOCOL_TRACK`
- Entry gate: `ENTRY_AFTER_DATA_ROUTE_LOCKS`
- Pass transition: `MARK_COMPLETE_AND_UNLOCK_PROMOTION_AUDIT`
- Fail transition: `KEEP_FAIL_CLOSED_AND_FORBID_PROMOTION`
- Held-out case ids: CHEM_CASE_005_CH3OH_GAS_PHASE_ENTHALPY, CHEM_CASE_006_C2H5OH_GAS_PHASE_ENTHALPY, CHEM_CASE_007_CO_GAS_PHASE_ENTHALPY, CHEM_CASE_008_H2_GAS_PHASE_ENTHALPY, CHEM_CASE_009_N2_GAS_PHASE_ENTHALPY, CHEM_CASE_010_O2_GAS_PHASE_ENTHALPY, CHEM_CASE_015_CO_IR_FAMILY, CHEM_CASE_016_C2H6_IR_FAMILY, CHEM_CASE_017_C2H4_IR_FAMILY, CHEM_CASE_018_C2H2_IR_FAMILY, CHEM_CASE_019_CH3OH_IR_FAMILY, CHEM_CASE_020_C2H5OH_IR_FAMILY, CHEM_CASE_024_METHANOL_SYNTHESIS_ENVELOPE, CHEM_CASE_025_STEAM_REFORMING_ENVELOPE, CHEM_CASE_026_ELECTROCHEMICAL_CO2_REDUCTION_ENVELOPE, CHEM_CASE_027_PHOTOCATALYTIC_WATER_SPLITTING_ENVELOPE, CHEM_CASE_028_FISCHER_TROPSCH_ENVELOPE, CHEM_CASE_029_PROTON_COUPLED_ELECTRON_TRANSFER_ENVELOPE, CHEM_CASE_030_C_H_ACTIVATION_ENVELOPE

## Status

COMPLETE

## Calibration Case Ids

- CHEM_CASE_001_H2O_GAS_PHASE_ENTHALPY
- CHEM_CASE_002_CO2_GAS_PHASE_ENTHALPY
- CHEM_CASE_003_CH4_GAS_PHASE_ENTHALPY
- CHEM_CASE_004_NH3_GAS_PHASE_ENTHALPY
- CHEM_CASE_011_H2O_IR_FAMILY
- CHEM_CASE_012_CO2_IR_FAMILY
- CHEM_CASE_013_CH4_IR_FAMILY
- CHEM_CASE_014_NH3_IR_FAMILY
- CHEM_CASE_021_HABER_BOSCH_EQUILIBRIUM_ENVELOPE
- CHEM_CASE_022_WATER_GAS_SHIFT_ENVELOPE
- CHEM_CASE_023_CO_OXIDATION_ENVELOPE

## Held Out Case Ids

- CHEM_CASE_005_CH3OH_GAS_PHASE_ENTHALPY
- CHEM_CASE_006_C2H5OH_GAS_PHASE_ENTHALPY
- CHEM_CASE_007_CO_GAS_PHASE_ENTHALPY
- CHEM_CASE_008_H2_GAS_PHASE_ENTHALPY
- CHEM_CASE_009_N2_GAS_PHASE_ENTHALPY
- CHEM_CASE_010_O2_GAS_PHASE_ENTHALPY
- CHEM_CASE_015_CO_IR_FAMILY
- CHEM_CASE_016_C2H6_IR_FAMILY
- CHEM_CASE_017_C2H4_IR_FAMILY
- CHEM_CASE_018_C2H2_IR_FAMILY
- CHEM_CASE_019_CH3OH_IR_FAMILY
- CHEM_CASE_020_C2H5OH_IR_FAMILY
- CHEM_CASE_024_METHANOL_SYNTHESIS_ENVELOPE
- CHEM_CASE_025_STEAM_REFORMING_ENVELOPE
- CHEM_CASE_026_ELECTROCHEMICAL_CO2_REDUCTION_ENVELOPE
- CHEM_CASE_027_PHOTOCATALYTIC_WATER_SPLITTING_ENVELOPE
- CHEM_CASE_028_FISCHER_TROPSCH_ENVELOPE
- CHEM_CASE_029_PROTON_COUPLED_ELECTRON_TRANSFER_ENVELOPE
- CHEM_CASE_030_C_H_ACTIVATION_ENVELOPE

## Acceptance Metrics

- `coverage_ratio_required`: 1.0
- `critical_residual_sigma_threshold`: 2.5
- `normalized_error_max_max_sigma`: 5.0
- `normalized_error_mean_abs_max_sigma`: 1.0
- `normalized_error_p95_max_sigma`: 2.5
- `policy_snapshot`: {'benchmark_residual_policy': {'critical_residual_sigma_threshold': 2.5, 'schema_id': 'LOGION_BENCHMARK_RESIDUAL_POLICY_v1', 'severe_residual_sigma_threshold': 1.5}, 'prediction_accuracy_policy': {'brier_score_max': 0.08, 'cases_total_required': 30, 'coverage_ratio_required': 1.0, 'critical_failure_f1_min': 0.87, 'critical_failure_precision_min': 0.85, 'critical_failure_recall_min': 0.9, 'expected_calibration_error_max': 0.05, 'schema_id': 'LOGION_PREDICTION_ACCURACY_POLICY_v2'}, 'prediction_sigma_policy': {'cases_total_min': 30, 'normalized_error_max_max_sigma': 5.0, 'normalized_error_mean_abs_max_sigma': 1.0, 'normalized_error_p95_max_sigma': 2.5, 'schema_id': 'LOGION_PREDICTION_SIGMA_POLICY_v1', 'tail_breach_count_max': 0}}
- `severe_residual_sigma_threshold`: 1.5
- `tail_breach_count_max`: 0

## No Post Hoc Split Rule

HELD_OUT_SPLIT_IS_LOCKED_EX_ANTE_AND_MAY_NOT_BE_CHANGED_AFTER_REPLAY

## Acceptance Criterion

Declared chemistry benchmark families pass the tolerance envelope on held-out compounds or reactions.

Refs:
- `logion/k7/spe/orchestrator/science/run_oc_core_domain_hard_closure_replay_v1.py --domain-id CHEMISTRY`
- `releases/oc_core_1_3/editorial/OC_CORE_1_3_SCIENCE_SPOT_latest.json`
- `logion/k0/governance/status/OC_CORE_1_3_K_LEVEL_SYSTEM_latest.json`
- `logion/k0/governance/status/OC_DOMAIN_INCLUSION_VERDICT_LEDGER_latest.json`
- `logion/k7/spe/registry/OC_DOMAIN_HARD_CLOSURE_PACKET_SPECS_v1.json`
- `logion/k0/governance/status/LOGION_OPERATIONAL_FORMAL_SUBSET_latest.json`
- `logion/k0/governance/status/OC_K_LEVEL_PROJECTION_MATRIX_latest.json`
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
- `releases/oc_core_1_3/editorial/science_sources/closure_bundles/chemistry/bundle.json`
