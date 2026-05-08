# held_out_replay_spec

- Bundle: `CLOSURE_BUNDLE::BIOLOGY`
- Claim: `BIOLOGY`
- Phase: `PHASE_5_BIOLOGY_CLOSURE`
- Current artifact status: `COMPLETE`
- Current transition gate: `MAINTENANCE_ONLY`
- Task id: `TASK::BIOLOGY::HELD_OUT_REPLAY_SPEC`
- Assignee role: `REPLAY_PROTOCOL_TRACK`
- Entry gate: `ENTRY_AFTER_DATA_ROUTE_LOCKS`
- Pass transition: `MARK_COMPLETE_AND_UNLOCK_PROMOTION_AUDIT`
- Fail transition: `KEEP_FAIL_CLOSED_AND_FORBID_PROMOTION`
- Held-out case ids: BIO_CASE_006_GSE184558_CTRL_DAY5_3, BIO_CASE_007_GSE184558_CTRL_DAY7_1, BIO_CASE_008_GSE184558_CTRL_DAY7_2, BIO_CASE_009_GSE184558_CTRL_DAY7_3, BIO_CASE_010_GSE184558_SHRNA5_DAY3_1, BIO_CASE_016_GSE226159_NON_CPC_03, BIO_CASE_017_GSE226159_RNA_12_24, BIO_CASE_018_GSE226159_RNA_6_36, BIO_CASE_019_GSE226159_T24H_PLUSBI_1, BIO_CASE_020_GSE226159_T24H_MINUSBI_1, BIO_CASE_025_GSE69063_SEPSIS_A_T2, BIO_CASE_026_GSE69063_TRAUMA_A_T0, BIO_CASE_027_GSE69063_TRAUMA_A_T1, BIO_CASE_028_GSE69063_TRAUMA_A_T2, BIO_CASE_029_GSE69063_HEALTHY_927, BIO_CASE_030_GSE69063_HEALTHY_928

## Status

COMPLETE

## Calibration Case Ids

- BIO_CASE_001_GSE184558_CTRL_DAY3_1
- BIO_CASE_002_GSE184558_CTRL_DAY3_2
- BIO_CASE_003_GSE184558_CTRL_DAY3_3
- BIO_CASE_004_GSE184558_CTRL_DAY5_1
- BIO_CASE_005_GSE184558_CTRL_DAY5_2
- BIO_CASE_011_GSE226159_CPC_01
- BIO_CASE_012_GSE226159_CPC_02
- BIO_CASE_013_GSE226159_CPC_03
- BIO_CASE_014_GSE226159_NON_CPC_01
- BIO_CASE_015_GSE226159_NON_CPC_02
- BIO_CASE_021_GSE69063_ANAPHYLAXIS_249_T0
- BIO_CASE_022_GSE69063_ANAPHYLAXIS_249_T1
- BIO_CASE_023_GSE69063_SEPSIS_A_T0
- BIO_CASE_024_GSE69063_SEPSIS_A_T1

## Held Out Case Ids

- BIO_CASE_006_GSE184558_CTRL_DAY5_3
- BIO_CASE_007_GSE184558_CTRL_DAY7_1
- BIO_CASE_008_GSE184558_CTRL_DAY7_2
- BIO_CASE_009_GSE184558_CTRL_DAY7_3
- BIO_CASE_010_GSE184558_SHRNA5_DAY3_1
- BIO_CASE_016_GSE226159_NON_CPC_03
- BIO_CASE_017_GSE226159_RNA_12_24
- BIO_CASE_018_GSE226159_RNA_6_36
- BIO_CASE_019_GSE226159_T24H_PLUSBI_1
- BIO_CASE_020_GSE226159_T24H_MINUSBI_1
- BIO_CASE_025_GSE69063_SEPSIS_A_T2
- BIO_CASE_026_GSE69063_TRAUMA_A_T0
- BIO_CASE_027_GSE69063_TRAUMA_A_T1
- BIO_CASE_028_GSE69063_TRAUMA_A_T2
- BIO_CASE_029_GSE69063_HEALTHY_927
- BIO_CASE_030_GSE69063_HEALTHY_928

## Acceptance Metrics

- `coverage_ratio_required`: 1.0
- `expected_calibration_error_max`: 0.05
- `normalized_error_max_max_sigma`: 5.0
- `normalized_error_mean_abs_max_sigma`: 1.0
- `normalized_error_p95_max_sigma`: 2.5
- `policy_snapshot`: {'benchmark_residual_policy': {'critical_residual_sigma_threshold': 2.5, 'schema_id': 'LOGION_BENCHMARK_RESIDUAL_POLICY_v1', 'severe_residual_sigma_threshold': 1.5}, 'prediction_accuracy_policy': {'brier_score_max': 0.08, 'cases_total_required': 30, 'coverage_ratio_required': 1.0, 'critical_failure_f1_min': 0.87, 'critical_failure_precision_min': 0.85, 'critical_failure_recall_min': 0.9, 'expected_calibration_error_max': 0.05, 'schema_id': 'LOGION_PREDICTION_ACCURACY_POLICY_v2'}, 'prediction_sigma_policy': {'cases_total_min': 30, 'normalized_error_max_max_sigma': 5.0, 'normalized_error_mean_abs_max_sigma': 1.0, 'normalized_error_p95_max_sigma': 2.5, 'schema_id': 'LOGION_PREDICTION_SIGMA_POLICY_v1', 'tail_breach_count_max': 0}}
- `tail_breach_count_max`: 0

## No Post Hoc Split Rule

HELD_OUT_SPLIT_IS_LOCKED_EX_ANTE_AND_MAY_NOT_BE_CHANGED_AFTER_REPLAY

## Acceptance Criterion

The promoted biological packet reproduces the declared measurable signatures on held-out datasets without widening the claim boundary.

Refs:
- `validation/run_all.py --qa-only (public replay umbrella; domain: BIOLOGY)`
- `releases/oc_core_1_3/editorial/OC_CORE_1_3_SCIENCE_SPOT_latest.json`
- `OC_PUBLIC_EVIDENCE_SURFACE::OC_CORE_1_3_K_LEVEL_SYSTEM_latest`
- `OC_PUBLIC_EVIDENCE_SURFACE::OC_DOMAIN_INCLUSION_VERDICT_LEDGER_latest`
- `OC_PUBLIC_EVIDENCE_SURFACE::OC_DOMAIN_HARD_CLOSURE_PACKET_SPECS_v1`
- `OC_PUBLIC_EVIDENCE_SURFACE::OC_OPERATIONAL_FORMAL_SUBSET_latest`
- `OC_PUBLIC_EVIDENCE_SURFACE::OC_K_LEVEL_PROJECTION_MATRIX_latest`
- `OC_PUBLIC_EVIDENCE_SURFACE::DOMAIN_NUMERICAL_PREDICTION_REGISTRY_latest`
- `OC_PUBLIC_EVIDENCE_SURFACE::QUESTION_COMPUTATIONAL_EVIDENCE_latest`
- `OC_PUBLIC_EVIDENCE_SURFACE::OC_MATHEMATICS_STRICT_RESULT_LEDGER_latest`
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
- `releases/oc_core_1_3/editorial/science_sources/closure_bundles/biology/bundle.json`
