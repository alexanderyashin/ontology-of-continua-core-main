from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"
GENERATED_ON = "2026-05-01"
SCHEMA_ID = "OC133_NEUROBEHAVIORAL_MODERN_SCIENCE_COVERAGE_WORK_ORDERS_v1"
CAPABILITY_OWNER = "Logion Neurobehavioral Evidence / Public Experiment Sources"

SCRIPT_REL = (
    "validation/heldout/grand_science/neurobehavioral/coverage_work_orders/"
    "oc133_neurobehavioral_modern_science_coverage_work_orders.py"
)
OUTPUT_REL = (
    "validation/heldout/grand_science/neurobehavioral/coverage_work_orders/"
    "OC133_NEUROBEHAVIORAL_MODERN_SCIENCE_COVERAGE_WORK_ORDERS.json"
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


def openneuro_cnp_sources() -> list[dict[str, Any]]:
    return [
        {
            "source_id": "OPENNEURO_DS000030_CNP",
            "title": "UCLA Consortium for Neuropsychiatric Phenomics LA5c Study",
            "source_authority": "OpenNeuro / OpenfMRI / Center for Reproducible Neuroscience",
            "official_url": "https://openneuro.org/datasets/ds000030",
            "official_documentation_url": "https://github.com/OpenNeuroDatasets/ds000030",
            "access_mode": "read_only_openneuro_git_or_s3",
            "runner_allowlist_status": "NOT_ALLOWLISTED_FOR_THIS_SPEC",
        }
    ]


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


def cnp_acquisition_protocol(topic: str) -> dict[str, Any]:
    return {
        "mode": "bounded_protocol_only_no_network_fetch_performed",
        "steps": [
            "Acquire OpenNeuro ds000030 at a pinned version using DataLad/OpenNeuro git or the published S3 object tree.",
            "Record dataset version, git commit or object manifest hash, participants.tsv hash, and task/scan file hashes.",
            f"Materialize the {topic} target-hidden task table only after source and subject split locks exist.",
        ],
        "required_local_snapshots": [
            f"validation/heldout/grand_science/neurobehavioral/coverage_work_orders/raw/{topic}/openneuro_ds000030_dataset.lock.json",
            f"validation/heldout/grand_science/neurobehavioral/coverage_work_orders/raw/{topic}/target_projection.lock.json",
        ],
    }


def common_split() -> dict[str, Any]:
    return {
        "source_separation_mode": "subject_hash_stratified_split",
        "train": "subject_hash_mod_100 in 0..59 after diagnosis/site/task-availability strata are locked",
        "validation": "subject_hash_mod_100 in 60..79 after diagnosis/site/task-availability strata are locked",
        "holdout": "subject_hash_mod_100 in 80..99 after diagnosis/site/task-availability strata are locked",
        "target_values_visible_during_split": False,
    }


def build_work_orders() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = [
        {
            "work_order_id": "MS-COV-WO-028",
            "stable_id": "MS-COV-WO-028::cognitive_behavioral_neurosciences::neural_recording_and_brain_network_observables",
            "coverage_gap_id": "MS-COV-GAP-COGNITIVE_BEHAVIORAL_NEUROSCIENCES-NEURAL_RECORDING_AND_BRAIN_NETWORK_OBSERVABLES",
            "domain_class_id": "cognitive_behavioral_neurosciences",
            "phenomenon_class_id": "neural_recording_and_brain_network_observables",
            "phenomenon_label": "neural recording and brain network observables",
            "priority": "P0",
            "lane_status": "OPEN_FAIL_CLOSED_EXECUTABLE_SPEC_ONLY",
            "coverage_closure_allowed": False,
            "support_allowed_for_broad_coverage": False,
            "official_sources": openneuro_cnp_sources(),
            "acquisition_protocol": cnp_acquisition_protocol("neural_recording_brain_network"),
            "target_variable": {
                "name": "heldout_subject_resting_state_connectivity_edge",
                "unit": "Fisher z-transformed functional connectivity",
                "target_fields": [
                    "atlas_edge_zcorr[source_region,target_region]",
                    "subject_id",
                    "task_rest_bold_run",
                ],
                "target_field": "connectivity_matrix[heldout_subject, heldout_edge].z_corr",
                "extraction_rule": (
                    "Resting-state BOLD time series are transformed into a locked atlas connectivity matrix; "
                    "heldout subject edge values stay hidden until predictions are materialized."
                ),
                "target_hidden_until_scoring": True,
            },
            "split": common_split(),
            "formula_or_model": {
                "model_id": "NEURO-CNP-CONNECTIVITY-GRAPH-RIDGE",
                "formula_or_model": (
                    "Fit a training-only nuisance-adjusted ridge/graph prior from visible subject covariates and "
                    "training-subject connectivity structure, then predict heldout subject edge vectors once."
                ),
                "inputs_visible_before_target": [
                    "subject_id hash",
                    "site",
                    "age",
                    "sex",
                    "diagnostic group if present",
                    "training-subject connectivity covariance",
                    "motion quality metrics",
                ],
                "target_values_used_for_model_design": False,
                "target_values_used_for_selection": False,
            },
            "incumbent_comparator": {
                "name": "training-cohort mean connectivity edge comparator",
                "prediction_rule": "predict each heldout edge by the training-only mean for the same atlas edge and stratum",
                "pre_registered": True,
                "target_values_used_for_baseline_design": False,
            },
            "uncertainty_and_residual": {
                "residual_metric": "edge-wise absolute residual and subject-level RMSE over heldout edge vectors",
                "uncertainty_method": "subject bootstrap plus motion-quality stratified conformal residual envelope",
                "superiority_predicate": "model_RMSE + uncertainty_upper < comparator_RMSE",
            },
            "negative_control": {
                "control_id": "NEURO-CONNECTIVITY-SUBJECT-LABEL-SHUFFLE",
                "description": "Shuffle heldout subject labels after source lock.",
                "rejection_predicate": "shuffled-subject replay must change row hashes and remove residual advantage",
            },
            "falsifier": {
                "falsifier_id": "NEURO-CONNECTIVITY-SOURCE-LEAK-FALSIFIER",
                "trigger": (
                    "Heldout connectivity edges leak into training, dataset hashes drift, fewer than 20 subjects are scored, "
                    "or training-mean comparator ties or beats the model within uncertainty."
                ),
            },
            "falsifier_predicates": [
                "OpenNeuro dataset/tree hash changes between acquisition and replay",
                "heldout subject edge values are read before prediction materialization",
                "holdout subject count is below minimum_n",
                "subject-label shuffle is not rejected",
            ],
            "minimum_n": 80,
            "replay_command": (
                "python validation/heldout/grand_science/neurobehavioral/coverage_work_orders/"
                "oc133_neurobehavioral_modern_science_coverage_work_orders.py --check"
            ),
            "replay_protocol": {
                "commands": [
                    "python validation/heldout/grand_science/neurobehavioral/coverage_work_orders/oc133_neurobehavioral_modern_science_coverage_work_orders.py --check",
                    "python <future_openneuro_cnp_connectivity_scorer.py> --dataset-lock <ds000030_lock> --write-pack --fail-closed",
                ],
                "required_artifacts": [
                    "OpenNeuro ds000030 source lock",
                    "participants/task availability hash",
                    "target-hidden connectivity task table",
                    "strict neural network evidence pack",
                ],
                "acceptance_predicates": common_acceptance(["NEURAL_NETWORK_SCOPE_REVIEWED"]),
            },
            "current_evidence_status": common_current_status(
                "OpenNeuro ds000030 is identified, but no dataset lock, preprocessing manifest, target-hidden connectivity scorer, comparator run, or strict pack is present."
            ),
            "remaining_blockers": [
                "OPENNEURO_DS000030_SOURCE_LOCK_NOT_ACQUIRED",
                "CONNECTIVITY_PREPROCESSING_MANIFEST_NOT_LOCKED",
                "STRICT_NEURAL_NETWORK_EVIDENCE_PACK_NOT_BUILT",
                "COVERAGE_REVIEW_NOT_PERFORMED",
            ],
            "no_send_locks": no_send(),
        },
        {
            "work_order_id": "MS-COV-WO-029",
            "stable_id": "MS-COV-WO-029::cognitive_behavioral_neurosciences::behavioral_task_and_psychometric_prediction",
            "coverage_gap_id": "MS-COV-GAP-COGNITIVE_BEHAVIORAL_NEUROSCIENCES-BEHAVIORAL_TASK_AND_PSYCHOMETRIC_PREDICTION",
            "domain_class_id": "cognitive_behavioral_neurosciences",
            "phenomenon_class_id": "behavioral_task_and_psychometric_prediction",
            "phenomenon_label": "behavioral task and psychometric prediction",
            "priority": "P0",
            "lane_status": "OPEN_FAIL_CLOSED_EXECUTABLE_SPEC_ONLY",
            "coverage_closure_allowed": False,
            "support_allowed_for_broad_coverage": False,
            "official_sources": openneuro_cnp_sources(),
            "acquisition_protocol": cnp_acquisition_protocol("behavioral_task_psychometric"),
            "target_variable": {
                "name": "heldout_stop_signal_behavioral_performance",
                "unit": "milliseconds and success-rate proportion",
                "target_fields": [
                    "stop_signal_training_median_go_rt_ms",
                    "stop_signal_success_rate",
                    "phenotype_psychometric_score_if_declared",
                ],
                "target_field": "subject_behavior.stop_signal.heldout_metric",
                "extraction_rule": (
                    "BIDS behavior/event files are parsed into subject-level task metrics; heldout subject metrics "
                    "and psychometric targets remain sealed until prediction rows are written."
                ),
                "target_hidden_until_scoring": True,
            },
            "split": common_split(),
            "formula_or_model": {
                "model_id": "NEURO-BEHAVIOR-TRAINING-SUBJECT-MIXED-MODEL",
                "formula_or_model": (
                    "Fit a training-only mixed-effects behavioral model from visible trial condition, prior trial history, "
                    "age/sex/site covariates, and training-subject psychometric summaries; score heldout subject metrics once."
                ),
                "inputs_visible_before_target": [
                    "trial condition",
                    "non-heldout event timing",
                    "subject covariates",
                    "training-subject behavioral summaries",
                ],
                "target_values_used_for_model_design": False,
                "target_values_used_for_selection": False,
            },
            "incumbent_comparator": {
                "name": "condition-stratified training mean behavioral comparator",
                "prediction_rule": "predict heldout RT/success metrics by the training-only condition and covariate-stratum mean",
                "pre_registered": True,
                "target_values_used_for_baseline_design": False,
            },
            "uncertainty_and_residual": {
                "residual_metric": "absolute RT residual in ms and absolute success-rate residual per subject",
                "uncertainty_method": "subject bootstrap with trial-count weighting and preregistered missingness rules",
                "superiority_predicate": "weighted_model_residual + uncertainty_upper < weighted_comparator_residual",
            },
            "negative_control": {
                "control_id": "NEURO-BEHAVIOR-SUBJECT-METRIC-SHUFFLE",
                "description": "Shuffle heldout subject behavioral metrics after source lock.",
                "rejection_predicate": "shuffled-metric replay must change row hashes and remove residual advantage",
            },
            "falsifier": {
                "falsifier_id": "NEURO-BEHAVIOR-PSYCHOMETRIC-FALSIFIER",
                "trigger": (
                    "Heldout behavior/psychometric metrics leak into model selection, fewer than 20 subjects are scored, "
                    "dataset hashes drift, or training-mean comparator ties or beats the model within uncertainty."
                ),
            },
            "falsifier_predicates": [
                "OpenNeuro behavior/event file hash changes between acquisition and replay",
                "heldout subject target metrics are read before prediction materialization",
                "holdout subject count is below minimum_n",
                "subject-metric shuffle is not rejected",
            ],
            "minimum_n": 40,
            "replay_command": (
                "python validation/heldout/grand_science/neurobehavioral/coverage_work_orders/"
                "oc133_neurobehavioral_modern_science_coverage_work_orders.py --check"
            ),
            "replay_protocol": {
                "commands": [
                    "python validation/heldout/grand_science/neurobehavioral/coverage_work_orders/oc133_neurobehavioral_modern_science_coverage_work_orders.py --check",
                    "python <future_openneuro_cnp_behavior_scorer.py> --dataset-lock <ds000030_lock> --write-pack --fail-closed",
                ],
                "required_artifacts": [
                    "OpenNeuro ds000030 source lock",
                    "BIDS behavior/event parse manifest",
                    "target-hidden behavioral metric table",
                    "strict behavioral/psychometric evidence pack",
                ],
                "acceptance_predicates": common_acceptance(["BEHAVIORAL_PSYCHOMETRIC_SCOPE_REVIEWED"]),
            },
            "current_evidence_status": common_current_status(
                "The public experiment source is identified, but no behavior-event source lock, target-hidden metric table, comparator output, or strict pack is present."
            ),
            "remaining_blockers": [
                "OPENNEURO_BEHAVIOR_SOURCE_LOCK_NOT_ACQUIRED",
                "TARGET_HIDDEN_BEHAVIOR_TABLE_NOT_BUILT",
                "STRICT_BEHAVIORAL_EVIDENCE_PACK_NOT_BUILT",
                "COVERAGE_REVIEW_NOT_PERFORMED",
            ],
            "no_send_locks": no_send(),
        },
        {
            "work_order_id": "MS-COV-WO-030",
            "stable_id": "MS-COV-WO-030::cognitive_behavioral_neurosciences::learning_memory_and_perception_dynamics",
            "coverage_gap_id": "MS-COV-GAP-COGNITIVE_BEHAVIORAL_NEUROSCIENCES-LEARNING_MEMORY_AND_PERCEPTION_DYNAMICS",
            "domain_class_id": "cognitive_behavioral_neurosciences",
            "phenomenon_class_id": "learning_memory_and_perception_dynamics",
            "phenomenon_label": "learning memory and perception dynamics",
            "priority": "P0",
            "lane_status": "OPEN_FAIL_CLOSED_EXECUTABLE_SPEC_ONLY",
            "coverage_closure_allowed": False,
            "support_allowed_for_broad_coverage": False,
            "official_sources": openneuro_cnp_sources(),
            "acquisition_protocol": cnp_acquisition_protocol("learning_memory_perception"),
            "target_variable": {
                "name": "heldout_paired_associate_memory_performance",
                "unit": "accuracy proportion and reaction time milliseconds",
                "target_fields": [
                    "PAMenc_trial_accuracy",
                    "PAMret_trial_accuracy",
                    "PAMret_reaction_time_ms",
                ],
                "target_field": "subject_task.PAMret.heldout_accuracy_or_rt",
                "extraction_rule": (
                    "Paired-associate memory encoding/retrieval events are parsed into subject/trial target metrics; "
                    "heldout trial and subject targets remain sealed until predictions are materialized."
                ),
                "target_hidden_until_scoring": True,
            },
            "split": common_split(),
            "formula_or_model": {
                "model_id": "NEURO-PAM-TRAINING-ONLY-LEARNING-CURVE",
                "formula_or_model": (
                    "Fit a training-only learning/memory curve with trial order, stimulus condition, subject covariates, "
                    "and prior visible trials; score heldout subject/trial targets once."
                ),
                "inputs_visible_before_target": [
                    "trial order",
                    "stimulus condition",
                    "visible prior trial indicators",
                    "subject covariates",
                    "training-subject learning curves",
                ],
                "target_values_used_for_model_design": False,
                "target_values_used_for_selection": False,
            },
            "incumbent_comparator": {
                "name": "training-only task-phase mean and carry-forward learning comparator",
                "prediction_rule": "predict heldout PAM accuracy/RT from training phase mean and last visible trial metric only",
                "pre_registered": True,
                "target_values_used_for_baseline_design": False,
            },
            "uncertainty_and_residual": {
                "residual_metric": "absolute accuracy residual and RT MAE per subject/trial",
                "uncertainty_method": "blocked bootstrap by subject with trial-order conformal residual envelope",
                "superiority_predicate": "model_residual + uncertainty_upper < best_preregistered_comparator_residual",
            },
            "negative_control": {
                "control_id": "NEURO-PAM-TRIAL-ORDER-SHUFFLE",
                "description": "Shuffle heldout trial order after source lock.",
                "rejection_predicate": "shuffled-order replay must change row hashes and remove learning-curve advantage",
            },
            "falsifier": {
                "falsifier_id": "NEURO-PAM-LEARNING-MEMORY-FALSIFIER",
                "trigger": (
                    "Heldout accuracy/RT targets leak into learning-curve fitting, fewer than 20 subjects are scored, "
                    "dataset hashes drift, or carry-forward/mean comparator ties or beats the model within uncertainty."
                ),
            },
            "falsifier_predicates": [
                "OpenNeuro PAM event file hash changes between acquisition and replay",
                "heldout PAM target metrics are read before prediction materialization",
                "holdout subject count is below minimum_n",
                "trial-order shuffle is not rejected",
            ],
            "minimum_n": 40,
            "replay_command": (
                "python validation/heldout/grand_science/neurobehavioral/coverage_work_orders/"
                "oc133_neurobehavioral_modern_science_coverage_work_orders.py --check"
            ),
            "replay_protocol": {
                "commands": [
                    "python validation/heldout/grand_science/neurobehavioral/coverage_work_orders/oc133_neurobehavioral_modern_science_coverage_work_orders.py --check",
                    "python <future_openneuro_cnp_pam_learning_scorer.py> --dataset-lock <ds000030_lock> --write-pack --fail-closed",
                ],
                "required_artifacts": [
                    "OpenNeuro ds000030 source lock",
                    "BIDS PAMenc/PAMret event parse manifest",
                    "target-hidden learning/memory task table",
                    "strict learning/memory evidence pack",
                ],
                "acceptance_predicates": common_acceptance(["LEARNING_MEMORY_PERCEPTION_SCOPE_REVIEWED"]),
            },
            "current_evidence_status": common_current_status(
                "OpenNeuro ds000030 includes relevant task material, but no locked PAM event table, scorer, comparator output, or strict pack is present."
            ),
            "remaining_blockers": [
                "OPENNEURO_PAM_SOURCE_LOCK_NOT_ACQUIRED",
                "TARGET_HIDDEN_PAM_TABLE_NOT_BUILT",
                "STRICT_LEARNING_MEMORY_EVIDENCE_PACK_NOT_BUILT",
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
        "domain_class_id": "cognitive_behavioral_neurosciences",
        "target_work_order_ids": ["MS-COV-WO-028", "MS-COV-WO-029", "MS-COV-WO-030"],
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
    expected_ids = {"MS-COV-WO-028", "MS-COV-WO-029", "MS-COV-WO-030"}
    actual_ids = {str(row.get("work_order_id")) for row in rows if isinstance(row, dict)}
    if actual_ids != expected_ids:
        failures.append("NEURO_WORK_ORDER_SET_MISMATCH")
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
    parser = argparse.ArgumentParser(description="Build/check neurobehavioral modern-science coverage work orders.")
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
