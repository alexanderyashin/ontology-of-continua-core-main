from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlencode


RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"
GENERATED_ON = "2026-05-01"
SCHEMA_ID = "OC133_CS_MODERN_SCIENCE_COVERAGE_WORK_ORDERS_v1"
CAPABILITY_OWNER = "Logion CS Evidence / Verification and Evaluation Sources"

SCRIPT_REL = (
    "validation/heldout/grand_science/cs/coverage_work_orders/"
    "oc133_cs_modern_science_coverage_work_orders.py"
)
OUTPUT_REL = (
    "validation/heldout/grand_science/cs/coverage_work_orders/"
    "OC133_CS_MODERN_SCIENCE_COVERAGE_WORK_ORDERS.json"
)
COVERAGE_REGISTER_REL = "comparators/modern_science/OC133_MODERN_SCIENCE_COVERAGE_REGISTER.json"
COVERAGE_QUEUE_REF = "reports/OC_CORE_1_3_3_MODERN_SCIENCE_COVERAGE_LANE_QUEUE.json"

NO_SEND_LOCKS = {
    "no_send": True,
    "public_release_action_allowed": False,
    "publish_allowed": False,
    "push_allowed": False,
    "registry_write_allowed": False,
    "journal_submission_allowed": False,
    "email_allowed": False,
    "doi_registration_allowed": False,
    "coverage_closure_allowed": False,
    "broad_modern_science_superiority_allowed": False,
    "all_domain_scientific_closure_allowed": False,
}

REQUIRED_ROW_FIELDS = (
    "official_sources",
    "acquisition_protocol",
    "target_variable",
    "split",
    "formula_or_model",
    "incumbent_comparator",
    "uncertainty_and_residual",
    "negative_control",
    "falsifier",
    "minimum_n",
    "replay_command",
    "current_evidence_status",
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[5]


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def sha256_object(payload: Any) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8", newline="\n")


def no_send() -> dict[str, Any]:
    return dict(NO_SEND_LOCKS)


def with_hash(row: dict[str, Any]) -> dict[str, Any]:
    row = dict(row)
    if "minimum_n" in row and "N" not in row:
        row["N"] = {
            "minimum_required": row["minimum_n"],
            "observed": None,
            "status": "NOT_ACQUIRED_PROTOCOL_ONLY",
        }
    row["row_sha256"] = sha256_object(row)
    return row


def nvd_url(params: dict[str, str]) -> str:
    return "https://services.nvd.nist.gov/rest/json/cves/2.0?" + urlencode(params)


def common_acceptance(extra: list[str] | None = None) -> list[str]:
    return [
        "STRICT_PACK_SCHEMA_PASS",
        "MINIMUM_N_GE_20_OR_FORMAL_EQUIVALENT_JUSTIFIED",
        "OFFICIAL_SOURCE_SNAPSHOT_LOCKED",
        "SOURCE_SEPARATION_PASS",
        "TARGET_VARIABLE_EXACTLY_DECLARED",
        "FORMULA_OR_MODEL_PREREGISTERED",
        "COMPARATOR_PREREGISTERED_AND_TARGET_SEPARATED",
        "UNCERTAINTY_POLICY_DECLARED",
        "RESIDUAL_METRIC_EXECUTABLE",
        "NEGATIVE_CONTROLS_EXECUTABLE_AND_REJECTED",
        "FALSIFIERS_EXECUTABLE_AND_NOT_TRIGGERED",
        "INDEPENDENT_REPLAY_PASS",
        "COVERAGE_REVIEW_REQUIRED",
        "NO_BROAD_SUPERIORITY_CERTIFICATION",
        "FAIL_CLOSED_UNLESS_EXECUTABLE_EVIDENCE_BOUND",
        *(extra or []),
    ]


def common_current_status(reason: str) -> dict[str, Any]:
    return {
        "status": "OPEN_FAIL_CLOSED_SPEC_DECLARED_NO_SOURCE_LOCK_NO_STRICT_PACK",
        "executable_evidence_exists": False,
        "coverage_closure_allowed": False,
        "broad_support_allowed": False,
        "reason": reason,
    }


def build_work_orders() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = [
        {
            "work_order_id": "MS-COV-WO-025",
            "stable_id": "MS-COV-WO-025::computer_information_sciences::program_semantics_and_verification",
            "coverage_gap_id": "MS-COV-GAP-COMPUTER_INFORMATION_SCIENCES-PROGRAM_SEMANTICS_AND_VERIFICATION",
            "domain_class_id": "computer_information_sciences",
            "phenomenon_class_id": "program_semantics_and_verification",
            "phenomenon_label": "program semantics and verification",
            "priority": "P0",
            "lane_status": "OPEN_FAIL_CLOSED_EXECUTABLE_SPEC_ONLY",
            "coverage_closure_allowed": False,
            "support_allowed_for_broad_coverage": False,
            "official_sources": [
                {
                    "source_id": "NIST_SAMATE_SARD",
                    "title": "NIST SAMATE Software Assurance Reference Dataset",
                    "source_authority": "National Institute of Standards and Technology",
                    "official_url": "https://samate.nist.gov/SARD/",
                    "official_documentation_url": (
                        "https://www.nist.gov/itl/ssd/software-quality-group/"
                        "samate/software-assurance-reference-dataset-sard"
                    ),
                    "access_mode": "read_only_https_or_export",
                    "runner_allowlist_status": "NOT_ALLOWLISTED_FOR_THIS_SPEC",
                },
                {
                    "source_id": "SV_COMP_SV_BENCHMARKS",
                    "title": "SV-COMP sv-benchmarks public verification benchmark corpus",
                    "source_authority": "SV-COMP benchmark maintainers",
                    "official_url": "https://gitlab.com/sosy-lab/benchmarking/sv-benchmarks",
                    "access_mode": "read_only_git_clone",
                    "runner_allowlist_status": "NOT_ALLOWLISTED_FOR_THIS_SPEC",
                },
            ],
            "acquisition_protocol": {
                "mode": "bounded_protocol_only_no_network_fetch_performed",
                "steps": [
                    "Clone sv-benchmarks at a pinned commit with --depth 1 and record HEAD plus tree hash.",
                    "Export SARD testcase metadata for the selected CWE families and hash the raw export.",
                    "Materialize a target-hidden table only after the source lock exists.",
                ],
                "required_local_snapshots": [
                    "validation/heldout/grand_science/cs/coverage_work_orders/raw/program_semantics/sv_benchmarks_tree.lock.json",
                    "validation/heldout/grand_science/cs/coverage_work_orders/raw/program_semantics/nist_sard_cases.lock.json",
                ],
            },
            "target_variable": {
                "name": "heldout_program_verification_verdict",
                "unit": "boolean or categorical verification verdict",
                "target_fields": [
                    "sv_comp_expected_verdict",
                    "sard_weakness_presence",
                    "sard_cwe_id",
                ],
                "target_field": "locked_case.expected_verdict",
                "extraction_rule": (
                    "Expected verdict and CWE/weakness labels remain hidden until predictions are materialized from "
                    "source text, property file, and training-only metadata."
                ),
                "target_hidden_until_scoring": True,
            },
            "split": {
                "source_separation_mode": "hash_locked_benchmark_family_split",
                "train": "case_hash_mod_100 in 0..59 within each benchmark family/CWE stratum",
                "validation": "case_hash_mod_100 in 60..79 within each benchmark family/CWE stratum",
                "holdout": "case_hash_mod_100 in 80..99 within each benchmark family/CWE stratum",
                "target_values_visible_during_split": False,
            },
            "formula_or_model": {
                "model_id": "CS-SEMANTICS-LOCKED-SOURCE-FEATURE-VERDICT-MODEL",
                "formula_or_model": (
                    "Predeclare static source and property features, then fit a training-only calibrated classifier "
                    "for expected verification verdict; score each holdout program exactly once."
                ),
                "inputs_visible_before_target": [
                    "source text hash",
                    "language",
                    "property filename",
                    "control-flow feature counts",
                    "visible benchmark family",
                    "training-only verdict frequencies",
                ],
                "target_values_used_for_model_design": False,
                "target_values_used_for_selection": False,
            },
            "incumbent_comparator": {
                "name": "property-family majority and public verifier-result comparator",
                "prediction_rule": (
                    "Use the better preregistered comparator between training-stratum majority verdict and a pinned "
                    "public SV-COMP result table for an incumbent verifier, scored on the same hidden cases."
                ),
                "pre_registered": True,
                "target_values_used_for_baseline_design": False,
            },
            "uncertainty_and_residual": {
                "residual_metric": "0/1 verdict error per program; macro error by benchmark family",
                "uncertainty_method": "Wilson interval for error rate plus family-stratified bootstrap",
                "superiority_predicate": (
                    "model_macro_error + uncertainty_upper < best_preregistered_comparator_macro_error"
                ),
            },
            "negative_control": {
                "control_id": "CS-SEMANTICS-VERDICT-LABEL-PERMUTATION",
                "description": "Permute holdout expected verdicts within family after lock.",
                "rejection_predicate": "permuted-label replay must break row hashes and lose any claimed residual advantage",
            },
            "falsifier": {
                "falsifier_id": "CS-SEMANTICS-VERIFICATION-FALSIFIER",
                "trigger": (
                    "Any expected verdict appears in visible inputs, source hashes drift, fewer than 20 holdout cases "
                    "are scored, or the incumbent comparator ties or beats the model within uncertainty."
                ),
            },
            "falsifier_predicates": [
                "source snapshot hash changes between acquisition and replay",
                "target verdict or CWE label is read before prediction materialization",
                "holdout N is below minimum_n",
                "comparator residual is less than or equal to model residual after uncertainty",
            ],
            "minimum_n": 20,
            "replay_command": (
                "python validation/heldout/grand_science/cs/coverage_work_orders/"
                "oc133_cs_modern_science_coverage_work_orders.py --check"
            ),
            "replay_protocol": {
                "commands": [
                    "python validation/heldout/grand_science/cs/coverage_work_orders/oc133_cs_modern_science_coverage_work_orders.py --check",
                    "python <future_cs_program_semantics_scorer.py> --source-lock <sv_benchmarks_lock> --sard-lock <sard_lock> --write-pack --fail-closed",
                ],
                "required_artifacts": [
                    "pinned sv-benchmarks tree hash",
                    "NIST SARD metadata export hash",
                    "target-hidden case table",
                    "strict evidence candidate pack",
                ],
                "acceptance_predicates": common_acceptance(["PROGRAM_SEMANTICS_SCOPE_REVIEWED"]),
            },
            "current_evidence_status": common_current_status(
                "No pinned SV-COMP/SARD source lock, target-hidden task table, scorer, comparator run, or strict evidence pack is present."
            ),
            "remaining_blockers": [
                "SV_BENCHMARKS_SOURCE_LOCK_NOT_ACQUIRED",
                "NIST_SARD_SOURCE_LOCK_NOT_ACQUIRED",
                "STRICT_VERIFICATION_EVIDENCE_PACK_NOT_BUILT",
                "COVERAGE_REVIEW_NOT_PERFORMED",
            ],
            "no_send_locks": no_send(),
        },
        {
            "work_order_id": "MS-COV-WO-026",
            "stable_id": "MS-COV-WO-026::computer_information_sciences::machine_learning_generalization_and_evaluation",
            "coverage_gap_id": "MS-COV-GAP-COMPUTER_INFORMATION_SCIENCES-MACHINE_LEARNING_GENERALIZATION_AND_EVALUATION",
            "domain_class_id": "computer_information_sciences",
            "phenomenon_class_id": "machine_learning_generalization_and_evaluation",
            "phenomenon_label": "machine learning generalization and evaluation",
            "priority": "P0",
            "lane_status": "OPEN_FAIL_CLOSED_EXECUTABLE_SPEC_ONLY",
            "coverage_closure_allowed": False,
            "support_allowed_for_broad_coverage": False,
            "official_sources": [
                {
                    "source_id": "OPENML_CC18_BENCHMARK_SUITE",
                    "title": "OpenML Curated Classification benchmark suite 2018",
                    "source_authority": "OpenML",
                    "official_url": "https://www.openml.org/api/v1/json/study/99",
                    "official_documentation_url": "https://docs.openml.org/benchmark/",
                    "access_mode": "read_only_https_get",
                    "runner_allowlist_status": "NOT_ALLOWLISTED_FOR_THIS_SPEC",
                }
            ],
            "acquisition_protocol": {
                "mode": "bounded_protocol_only_no_network_fetch_performed",
                "steps": [
                    "Fetch OpenML study 99 task list and each task split manifest with immutable IDs.",
                    "Record dataset/task/version hashes before model selection.",
                    "Use official OpenML task folds where available; otherwise materialize deterministic folds from row IDs.",
                ],
                "required_local_snapshots": [
                    "validation/heldout/grand_science/cs/coverage_work_orders/raw/ml_generalization/openml_cc18_study_99.lock.json",
                    "validation/heldout/grand_science/cs/coverage_work_orders/raw/ml_generalization/openml_task_folds.lock.json",
                ],
            },
            "target_variable": {
                "name": "heldout_openml_task_generalization_score",
                "unit": "balanced accuracy error or multiclass log-loss on official holdout fold",
                "target_fields": [
                    "fold_test_labels",
                    "fold_balanced_accuracy",
                    "fold_log_loss",
                ],
                "target_field": "openml_task.fold[target_fold].test_metric",
                "extraction_rule": "Test labels and final fold metrics are sealed until all candidate model outputs are written.",
                "target_hidden_until_scoring": True,
            },
            "split": {
                "source_separation_mode": "official_openml_task_fold_or_hash_locked_fallback",
                "train": "official OpenML train folds or row_hash_mod_100 in 0..59",
                "validation": "official OpenML validation fold or row_hash_mod_100 in 60..79",
                "holdout": "official OpenML test fold or row_hash_mod_100 in 80..99",
                "target_values_visible_during_split": False,
            },
            "formula_or_model": {
                "model_id": "CS-ML-TRAINING-ONLY-GENERALIZATION-EVALUATOR",
                "formula_or_model": (
                    "Select the model family and hyperparameters using only training/validation folds from a fixed "
                    "manifest of logistic regression, random forest, and gradient boosting candidates, then score the heldout fold once."
                ),
                "inputs_visible_before_target": [
                    "training features",
                    "training labels",
                    "validation labels",
                    "OpenML task metadata",
                    "fixed hyperparameter manifest",
                ],
                "target_values_used_for_model_design": False,
                "target_values_used_for_selection": False,
            },
            "incumbent_comparator": {
                "name": "OpenML dummy, majority, logistic-regression, and random-forest baselines",
                "prediction_rule": (
                    "Score preregistered DummyClassifier, majority-class, logistic-regression, and random-forest baselines "
                    "on the same task folds; compare against the strongest admissible baseline."
                ),
                "pre_registered": True,
                "target_values_used_for_baseline_design": False,
            },
            "uncertainty_and_residual": {
                "residual_metric": "per-task generalization residual: 1 - balanced_accuracy, with log-loss as secondary metric",
                "uncertainty_method": "paired bootstrap over tasks/folds plus binomial label uncertainty for accuracy",
                "superiority_predicate": "paired residual margin over best comparator is positive after uncertainty",
            },
            "negative_control": {
                "control_id": "CS-ML-LABEL-PERMUTATION-CONTROL",
                "description": "Permute holdout labels inside each task after source lock.",
                "rejection_predicate": "permuted-label replay must destroy generalization advantage and change row hashes",
            },
            "falsifier": {
                "falsifier_id": "CS-ML-GENERALIZATION-FALSIFIER",
                "trigger": (
                    "Holdout labels leak into model selection, fewer than 20 tasks/folds are scored, comparator ties or beats "
                    "within uncertainty, or any OpenML task/version hash changes."
                ),
            },
            "falsifier_predicates": [
                "OpenML task or fold hash changes between acquisition and replay",
                "holdout labels are loaded before model output materialization",
                "best preregistered comparator residual is less than or equal to model residual after uncertainty",
                "label permutation is not rejected",
            ],
            "minimum_n": 20,
            "replay_command": (
                "python validation/heldout/grand_science/cs/coverage_work_orders/"
                "oc133_cs_modern_science_coverage_work_orders.py --check"
            ),
            "replay_protocol": {
                "commands": [
                    "python validation/heldout/grand_science/cs/coverage_work_orders/oc133_cs_modern_science_coverage_work_orders.py --check",
                    "python <future_openml_cc18_generalization_scorer.py> --study 99 --write-pack --fail-closed",
                ],
                "required_artifacts": [
                    "OpenML CC18 study/task locks",
                    "target-hidden fold table",
                    "baseline run manifest",
                    "strict ML generalization candidate pack",
                ],
                "acceptance_predicates": common_acceptance(["OPENML_CC18_SCOPE_REVIEWED"]),
            },
            "current_evidence_status": common_current_status(
                "OpenML CC18 is identified as the public benchmark source, but no source lock, scorer, comparator result, or strict pack is present."
            ),
            "remaining_blockers": [
                "OPENML_CC18_SOURCE_LOCK_NOT_ACQUIRED",
                "OPENML_TASK_FOLD_LOCK_NOT_ACQUIRED",
                "STRICT_ML_GENERALIZATION_EVIDENCE_PACK_NOT_BUILT",
                "COVERAGE_REVIEW_NOT_PERFORMED",
            ],
            "no_send_locks": no_send(),
        },
        {
            "work_order_id": "MS-COV-WO-027",
            "stable_id": "MS-COV-WO-027::computer_information_sciences::information_network_and_security_observables",
            "coverage_gap_id": "MS-COV-GAP-COMPUTER_INFORMATION_SCIENCES-INFORMATION_NETWORK_AND_SECURITY_OBSERVABLES",
            "domain_class_id": "computer_information_sciences",
            "phenomenon_class_id": "information_network_and_security_observables",
            "phenomenon_label": "information network and security observables",
            "priority": "P0",
            "lane_status": "OPEN_FAIL_CLOSED_EXECUTABLE_SPEC_ONLY",
            "coverage_closure_allowed": False,
            "support_allowed_for_broad_coverage": False,
            "official_sources": [
                {
                    "source_id": "NIST_NVD_CVE_API_2_0",
                    "title": "NIST National Vulnerability Database CVE API 2.0",
                    "source_authority": "National Institute of Standards and Technology",
                    "official_url": "https://services.nvd.nist.gov/rest/json/cves/2.0",
                    "official_documentation_url": "https://nvd.nist.gov/developers/vulnerabilities",
                    "access_mode": "read_only_https_get",
                    "runner_allowlist_status": "ALLOWLIST_CANDIDATE_OFFICIAL_NIST_SOURCE",
                }
            ],
            "acquisition_protocol": {
                "mode": "bounded_protocol_only_no_network_fetch_performed",
                "steps": [
                    "Fetch CVE rows for a pinned historical publication interval with cvssMetricV31 present.",
                    "Record raw NVD response, request URL, response timestamp, totalResults, and SHA-256.",
                    "Build target-hidden CVSS score/severity rows from the locked snapshot only after source hashing.",
                ],
                "example_official_endpoint_url": nvd_url(
                    {
                        "pubStartDate": "2024-01-01T00:00:00.000",
                        "pubEndDate": "2024-03-31T23:59:59.999",
                        "cvssV3Severity": "HIGH",
                        "resultsPerPage": "2000",
                    }
                ),
                "required_local_snapshots": [
                    "validation/heldout/grand_science/cs/coverage_work_orders/raw/security_nvd/nvd_cve_2024q1_high.lock.json",
                ],
            },
            "target_variable": {
                "name": "heldout_nvd_cvss_v31_base_score",
                "unit": "CVSS v3.1 points",
                "target_fields": [
                    "metrics.cvssMetricV31[].cvssData.baseScore",
                    "metrics.cvssMetricV31[].cvssData.baseSeverity",
                ],
                "target_field": "nvd_cve.metrics.cvssMetricV31[primary].cvssData.baseScore",
                "extraction_rule": (
                    "CVSS score/severity are hidden until the prediction row is materialized from CVE text, CWE IDs, "
                    "CPE counts, dates, and reference metadata."
                ),
                "target_hidden_until_scoring": True,
            },
            "split": {
                "source_separation_mode": "prospective_publication_date_split",
                "train": "CVE publishedDate before the locked holdout interval",
                "validation": "last complete month before the holdout interval",
                "holdout": "pinned historical quarter requested from NVD after model manifest is locked",
                "target_values_visible_during_split": False,
            },
            "formula_or_model": {
                "model_id": "CS-NVD-CVSS-TEXT-METADATA-REGRESSOR",
                "formula_or_model": (
                    "Fit a training-only calibrated score regressor/classifier from CVE description tokens, CWE, CPE count, "
                    "reference tags, and publication metadata; predict heldout CVSS base score and severity once."
                ),
                "inputs_visible_before_target": [
                    "CVE ID",
                    "publishedDate",
                    "description text",
                    "CWE IDs",
                    "CPE match counts",
                    "reference tags",
                ],
                "target_values_used_for_model_design": False,
                "target_values_used_for_selection": False,
            },
            "incumbent_comparator": {
                "name": "NVD prior-CWE median and prior-severity-frequency comparator",
                "prediction_rule": (
                    "Predict heldout CVSS score from the training-only median score for the same CWE when present, otherwise "
                    "the global prior median; severity comparator uses prior class frequencies."
                ),
                "pre_registered": True,
                "target_values_used_for_baseline_design": False,
            },
            "uncertainty_and_residual": {
                "residual_metric": "absolute CVSS-point residual per CVE; macro MAE by CWE stratum",
                "uncertainty_method": "pre-holdout conformal residual interval stratified by CWE availability",
                "superiority_predicate": "model_MAE + conformal_upper < comparator_MAE",
            },
            "negative_control": {
                "control_id": "CS-NVD-CVSS-WITHIN-CWE-SHUFFLE",
                "description": "Shuffle heldout CVSS scores within CWE strata after source lock.",
                "rejection_predicate": "shuffled-score replay must change row hashes and remove residual advantage",
            },
            "falsifier": {
                "falsifier_id": "CS-NVD-CVSS-SECURITY-FALSIFIER",
                "trigger": (
                    "CVSS fields leak into visible inputs, fewer than 20 CVEs are scored, NVD source hash changes, "
                    "or prior-CWE comparator ties or beats the model within uncertainty."
                ),
            },
            "falsifier_predicates": [
                "NVD response hash changes between acquisition and replay",
                "CVSS baseScore/baseSeverity is read before prediction materialization",
                "holdout CVE count is below minimum_n",
                "within-CWE shuffled negative control is not rejected",
            ],
            "minimum_n": 100,
            "replay_command": (
                "python validation/heldout/grand_science/cs/coverage_work_orders/"
                "oc133_cs_modern_science_coverage_work_orders.py --check"
            ),
            "replay_protocol": {
                "commands": [
                    "python validation/heldout/grand_science/cs/coverage_work_orders/oc133_cs_modern_science_coverage_work_orders.py --check",
                    "python <future_nvd_cvss_security_scorer.py> --source-lock <nvd_lock> --write-pack --fail-closed",
                ],
                "required_artifacts": [
                    "NVD CVE API source lock",
                    "target-hidden CVSS task table",
                    "prior-CWE comparator manifest",
                    "strict security observables evidence pack",
                ],
                "acceptance_predicates": common_acceptance(["NIST_NVD_SECURITY_SCOPE_REVIEWED"]),
            },
            "current_evidence_status": common_current_status(
                "NIST NVD is identified as the official source, but no locked NVD snapshot, target-hidden scorer, comparator output, or strict pack is present."
            ),
            "remaining_blockers": [
                "NVD_CVE_SOURCE_LOCK_NOT_ACQUIRED",
                "TARGET_HIDDEN_CVSS_TASK_TABLE_NOT_BUILT",
                "STRICT_SECURITY_OBSERVABLES_EVIDENCE_PACK_NOT_BUILT",
                "COVERAGE_REVIEW_NOT_PERFORMED",
            ],
            "no_send_locks": no_send(),
        },
    ]
    return [with_hash(row) for row in rows]


def build_payload() -> dict[str, Any]:
    rows = build_work_orders()
    return {
        "schema_id": SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_on": GENERATED_ON,
        "capability_owner": CAPABILITY_OWNER,
        "generated_by": SCRIPT_REL,
        "coverage_register_ref": COVERAGE_REGISTER_REL,
        "coverage_queue_ref": COVERAGE_QUEUE_REF,
        "domain_class_id": "computer_information_sciences",
        "target_work_order_ids": ["MS-COV-WO-025", "MS-COV-WO-026", "MS-COV-WO-027"],
        "work_order_total": len(rows),
        "fail_closed_spec_total": len(rows),
        "coverage_closure_allowed": False,
        "broad_modern_science_superiority_allowed": False,
        "small_deterministic_replay_implemented": "SPEC_GENERATION_AND_SYNC_CHECK_ONLY",
        "official_data_acquired": False,
        "no_fake_pass": True,
        "no_send_locks": no_send(),
        "work_orders": rows,
    }


def validate_payload(payload: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    rows = payload.get("work_orders", [])
    if payload.get("coverage_closure_allowed") is not False:
        failures.append("PAYLOAD_COVERAGE_CLOSURE_ALLOWED")
    if payload.get("broad_modern_science_superiority_allowed") is not False:
        failures.append("PAYLOAD_BROAD_SUPERIORITY_ALLOWED")
    if payload.get("official_data_acquired") is not False:
        failures.append("PAYLOAD_FALSE_DATA_ACQUISITION_CLAIM")
    if payload.get("no_fake_pass") is not True:
        failures.append("NO_FAKE_PASS_FLAG_MISSING")
    if not isinstance(rows, list) or payload.get("work_order_total") != len(rows):
        failures.append("WORK_ORDER_TOTAL_MISMATCH")
        return failures
    expected_ids = {"MS-COV-WO-025", "MS-COV-WO-026", "MS-COV-WO-027"}
    actual_ids = {str(row.get("work_order_id")) for row in rows if isinstance(row, dict)}
    if actual_ids != expected_ids:
        failures.append("CS_WORK_ORDER_SET_MISMATCH")
    for row in rows:
        if not isinstance(row, dict):
            failures.append("WORK_ORDER_NOT_OBJECT")
            continue
        row_id = str(row.get("work_order_id", "unknown"))
        if row.get("coverage_closure_allowed") is not False:
            failures.append(f"COVERAGE_CLOSURE_ALLOWED::{row_id}")
        if row.get("support_allowed_for_broad_coverage") is not False:
            failures.append(f"BROAD_SUPPORT_ALLOWED::{row_id}")
        if "PASS" in str(row.get("lane_status", "")).upper():
            failures.append(f"FAKE_PASS_STATUS::{row_id}")
        for field in REQUIRED_ROW_FIELDS:
            if not row.get(field):
                failures.append(f"REQUIRED_FIELD_MISSING::{row_id}::{field}")
        if row.get("minimum_n", 0) < 20:
            failures.append(f"MINIMUM_N_TOO_SMALL::{row_id}")
        if not row.get("target_variable", {}).get("target_hidden_until_scoring"):
            failures.append(f"TARGET_NOT_HIDDEN::{row_id}")
        if row.get("split", {}).get("target_values_visible_during_split") is not False:
            failures.append(f"SPLIT_LEAKS_TARGET::{row_id}")
        if row.get("formula_or_model", {}).get("target_values_used_for_selection") is not False:
            failures.append(f"MODEL_SELECTION_USES_TARGET::{row_id}")
        if row.get("incumbent_comparator", {}).get("pre_registered") is not True:
            failures.append(f"COMPARATOR_NOT_PREREGISTERED::{row_id}")
        if not row.get("uncertainty_and_residual", {}).get("residual_metric"):
            failures.append(f"RESIDUAL_METRIC_MISSING::{row_id}")
        if not row.get("negative_control", {}).get("rejection_predicate"):
            failures.append(f"NEGATIVE_CONTROL_PREDICATE_MISSING::{row_id}")
        if not row.get("falsifier", {}).get("trigger"):
            failures.append(f"FALSIFIER_TRIGGER_MISSING::{row_id}")
        if not row.get("replay_protocol", {}).get("commands"):
            failures.append(f"REPLAY_COMMANDS_MISSING::{row_id}")
        if "NO_BROAD_SUPERIORITY_CERTIFICATION" not in row.get("replay_protocol", {}).get("acceptance_predicates", []):
            failures.append(f"NO_BROAD_SUPERIORITY_PREDICATE_MISSING::{row_id}")
        status = row.get("current_evidence_status", {})
        if status.get("executable_evidence_exists") is not False or status.get("coverage_closure_allowed") is not False:
            failures.append(f"CURRENT_STATUS_NOT_FAIL_CLOSED::{row_id}")
        if not all(str(source.get("official_url", "")).startswith("https://") for source in row.get("official_sources", [])):
            failures.append(f"OFFICIAL_SOURCE_URL_NOT_HTTPS::{row_id}")
        expected_hash = sha256_object({key: value for key, value in row.items() if key != "row_sha256"})
        if row.get("row_sha256") != expected_hash:
            failures.append(f"ROW_HASH_MISMATCH::{row_id}")
    return failures


def check_stored(root: Path | None = None) -> list[str]:
    root = root or repo_root()
    path = root / OUTPUT_REL
    expected = build_payload()
    failures = validate_payload(expected)
    if not path.exists():
        return [*failures, f"missing::{OUTPUT_REL}"]
    actual = read_json(path)
    if actual != expected:
        failures.append(f"mismatch::{OUTPUT_REL}")
    failures.extend(validate_payload(actual if isinstance(actual, dict) else {}))
    return sorted(set(failures))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build/check CS modern-science coverage work orders.")
    parser.add_argument("--root", default=str(repo_root()), help="repository root")
    parser.add_argument("--write", action="store_true", help="write the deterministic work-order artifact")
    parser.add_argument("--check", action="store_true", help="check stored artifact synchronization")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    if args.check:
        failures = check_stored(root)
        if failures:
            for failure in failures:
                print(f"ERROR: {failure}")
            return 1
        print(json.dumps({"status": "ok", "checked": OUTPUT_REL}, indent=2))
        return 0
    payload = build_payload()
    failures = validate_payload(payload)
    if args.write:
        write_json(root / OUTPUT_REL, payload)
    print(json.dumps({"status": "ok" if not failures else "failed", "output_ref": OUTPUT_REL, "failures": failures}, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
