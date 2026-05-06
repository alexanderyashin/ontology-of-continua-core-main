from __future__ import annotations

import argparse
import hashlib
import json
import re
import statistics
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"
GENERATED_ON = "2026-05-01"
SCHEMA_ID = "OC133_CS_MODERN_SCIENCE_COVERAGE_WORK_ORDERS_v1"
NVD_ACQUISITION_SCHEMA_ID = "OC133_CS_NVD_CVSS_READONLY_ACQUISITION_v1"
NVD_LOCK_SCHEMA_ID = "OC133_CS_NVD_CVSS_SOURCE_LOCK_v1"
NVD_TASK_TABLE_SCHEMA_ID = "OC133_CS_NVD_CVSS_TARGET_HIDDEN_TASK_TABLE_v1"
NVD_HIDDEN_TARGET_LOCK_SCHEMA_ID = "OC133_CS_NVD_CVSS_HIDDEN_TARGET_LOCK_v1"
NVD_SCORING_PACK_SCHEMA_ID = "OC133_CS_NVD_CVSS_SCORING_PACK_v1"
NVD_REPLAY_REPORT_SCHEMA_ID = "OC133_CS_NVD_CVSS_REPLAY_REPORT_v1"
CAPABILITY_OWNER = "Logion CS Evidence / Verification and Evaluation Sources"

SCRIPT_REL = (
    "validation/heldout/grand_science/cs/coverage_work_orders/"
    "oc133_cs_modern_science_coverage_work_orders.py"
)
OUTPUT_REL = (
    "validation/heldout/grand_science/cs/coverage_work_orders/"
    "OC133_CS_MODERN_SCIENCE_COVERAGE_WORK_ORDERS.json"
)
NVD_RAW_DIR_REL = "validation/heldout/grand_science/cs/coverage_work_orders/raw/security_nvd"
NVD_SNAPSHOT_REL = f"{NVD_RAW_DIR_REL}/nvd_cve_2024q1_high.compact.json"
NVD_LOCK_REL = f"{NVD_RAW_DIR_REL}/nvd_cve_2024q1_high.lock.json"
NVD_TASK_TABLE_REL = (
    "validation/heldout/grand_science/cs/coverage_work_orders/"
    "OC133_CS_NVD_CVSS_TARGET_HIDDEN_TASK_TABLE.json"
)
NVD_HIDDEN_TARGET_LOCK_REL = (
    "validation/heldout/grand_science/cs/coverage_work_orders/locks/"
    "OC133-CS-NVD-CVSS-HIDDEN-TARGETS-0001.lock.json"
)
NVD_SCORING_PACK_REL = (
    "validation/heldout/grand_science/cs/coverage_work_orders/"
    "OC133_CS_NVD_CVSS_SECURITY_TARGET_HIDDEN_REPLAY_SCORER_EVIDENCE_PACK.json"
)
NVD_REPLAY_REPORT_REL = (
    "validation/heldout/grand_science/cs/coverage_work_orders/"
    "OC133_CS_NVD_CVSS_REPLAY_REPORT.json"
)
COVERAGE_REGISTER_REL = "comparators/modern_science/OC133_MODERN_SCIENCE_COVERAGE_REGISTER.json"
COVERAGE_QUEUE_REF = "reports/OC_CORE_1_3_3_MODERN_SCIENCE_COVERAGE_LANE_QUEUE.json"

NVD_WORK_ORDER_ID = "MS-COV-WO-027"
NVD_QUERY_PARAMS = {
    "pubStartDate": "2024-01-01T00:00:00.000",
    "pubEndDate": "2024-03-31T23:59:59.999",
    "cvssV3Severity": "HIGH",
    "resultsPerPage": "2000",
}
NVD_MODEL_ID = "CS-NVD-CVSS-TEXT-CWE-CPE-METADATA-MEDIAN-ENSEMBLE-v1"
NVD_MODEL_RULE = (
    "predict heldout CVSS v3.x base score from training-only medians over CWE, CPE-count bin, "
    "reference-count bin, and visible description/reference/source tokens; baseScore, severity, "
    "CVSS vector metrics, exploitabilityScore, and impactScore remain hidden until scoring"
)
NVD_COMPARATOR_ID = "CS-NVD-PRIOR-CWE-MEDIAN-COMPARATOR-v1"
NVD_COMPARATOR_RULE = "predict heldout CVSS score from the training-only median score for the same CWE, otherwise the global training median"
NVD_STOP_TOKENS = {
    "the",
    "and",
    "for",
    "with",
    "this",
    "that",
    "which",
    "from",
    "when",
    "allow",
    "allows",
    "could",
    "vulnerability",
    "vulnerabilities",
    "attacker",
    "remote",
    "local",
    "user",
    "users",
}

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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rounded(value: float, digits: int = 6) -> float:
    return round(float(value), digits)


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def median(values: list[float]) -> float:
    return float(statistics.median(values)) if values else 0.0


def nvd_official_url() -> str:
    return nvd_url(NVD_QUERY_PARAMS)


def fetch_json(url: str, *, timeout: int = 90) -> dict[str, Any]:
    request = Request(url, headers={"User-Agent": "Logion-OC133-Research-Cache/1.0"})
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def cve_cvss_metric(cve: dict[str, Any]) -> dict[str, Any] | None:
    metrics = cve.get("metrics", {}) if isinstance(cve.get("metrics"), dict) else {}
    for key in ("cvssMetricV31", "cvssMetricV30"):
        rows = metrics.get(key)
        if isinstance(rows, list) and rows:
            metric = rows[0]
            if isinstance(metric, dict) and isinstance(metric.get("cvssData"), dict):
                return metric
    return None


def cve_cwes(cve: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for weakness in cve.get("weaknesses", []) or []:
        if not isinstance(weakness, dict):
            continue
        for desc in weakness.get("description", []) or []:
            if isinstance(desc, dict) and desc.get("value"):
                values.append(str(desc["value"]))
    return values or ["UNKNOWN"]


def cve_cpe_tokens(cve: dict[str, Any]) -> list[str]:
    tokens: list[str] = []
    for config in cve.get("configurations", []) or []:
        if not isinstance(config, dict):
            continue
        for node in config.get("nodes", []) or []:
            if not isinstance(node, dict):
                continue
            for match in node.get("cpeMatch", []) or []:
                if not isinstance(match, dict):
                    continue
                criteria = str(match.get("criteria") or "")
                parts = criteria.split(":")
                tokens.extend(part for part in parts[3:6] if part and part != "*")
    return tokens


def cve_reference_tags(cve: dict[str, Any]) -> list[str]:
    tags: list[str] = []
    for ref in cve.get("references", []) or []:
        if isinstance(ref, dict):
            tags.extend(str(tag) for tag in ref.get("tags", []) or [] if tag)
    return tags


def cve_description(cve: dict[str, Any]) -> str:
    return " ".join(
        str(desc.get("value") or "")
        for desc in cve.get("descriptions", []) or []
        if isinstance(desc, dict) and desc.get("lang") == "en"
    )


def nvd_visible_tokens(row: dict[str, Any]) -> set[str]:
    text = " ".join(
        [
            str(row.get("description", "")),
            " ".join(str(item) for item in row.get("cwe_ids", [])),
            " ".join(str(item) for item in row.get("cpe_tokens", [])),
            " ".join(str(item) for item in row.get("reference_tags", [])),
            str(row.get("source_identifier", "")),
        ]
    ).lower()
    return {
        token
        for token in re.findall(r"[a-z][a-z0-9_]{2,}", text)
        if token not in NVD_STOP_TOKENS
    }


def compact_nvd_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in payload.get("vulnerabilities", []) or []:
        if not isinstance(item, dict):
            continue
        cve = item.get("cve", {})
        if not isinstance(cve, dict):
            continue
        metric = cve_cvss_metric(cve)
        if not metric:
            continue
        cvss = metric.get("cvssData", {})
        score = cvss.get("baseScore")
        if not isinstance(score, (int, float)):
            continue
        rows.append(
            {
                "cve_id": cve.get("id"),
                "published": cve.get("published"),
                "last_modified": cve.get("lastModified"),
                "source_identifier": cve.get("sourceIdentifier"),
                "description": cve_description(cve),
                "cwe_ids": cve_cwes(cve),
                "cpe_tokens": cve_cpe_tokens(cve),
                "cpe_match_count": len(cve_cpe_tokens(cve)),
                "reference_tags": cve_reference_tags(cve),
                "reference_count": len(cve.get("references", []) or []),
                "hidden_cvss_base_score": float(score),
                "hidden_cvss_base_severity": cvss.get("baseSeverity"),
                "hidden_cvss_metric_version": cvss.get("version"),
            }
        )
    return sorted(rows, key=lambda row: (str(row.get("published") or ""), str(row.get("cve_id") or "")))


def acquire_nvd(root: Path, *, write: bool) -> dict[str, Any]:
    url = nvd_official_url()
    payload = fetch_json(url)
    rows = compact_nvd_rows(payload)
    snapshot = {
        "schema_id": NVD_ACQUISITION_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_on": GENERATED_ON,
        "capability_owner": CAPABILITY_OWNER,
        "target_work_order_id": NVD_WORK_ORDER_ID,
        "official_url": url,
        "official_documentation_url": "https://nvd.nist.gov/developers/vulnerabilities",
        "source_authority": "National Institute of Standards and Technology",
        "source_id": "NIST_NVD_CVE_API_2_0",
        "query_params": dict(NVD_QUERY_PARAMS),
        "nvd_total_results": payload.get("totalResults"),
        "row_count": len(rows),
        "minimum_n_required": 100,
        "target_hidden_fields": [
            "hidden_cvss_base_score",
            "hidden_cvss_base_severity",
            "hidden_cvss_metric_version",
        ],
        "visible_fields": [
            "cve_id",
            "published",
            "source_identifier",
            "description",
            "cwe_ids",
            "cpe_tokens",
            "cpe_match_count",
            "reference_tags",
            "reference_count",
        ],
        "target_hidden_until_scoring": True,
        "target_values_used_for_selection": False,
        "target_values_used_for_model_design": False,
        "rows": rows,
    }
    snapshot["snapshot_sha256"] = sha256_object(snapshot)
    lock = {
        "schema_id": NVD_LOCK_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_on": GENERATED_ON,
        "source_snapshot_ref": NVD_SNAPSHOT_REL,
        "official_url": url,
        "source_snapshot_sha256": snapshot["snapshot_sha256"],
        "row_count": len(rows),
        "minimum_n_required": 100,
        "target_hidden_until_scoring": True,
        "source_separation_mode": "prospective_publication_date_split",
        "train_fraction": 0.6,
        "validation_fraction": 0.2,
        "holdout_fraction": 0.2,
        "no_send_locks": no_send(),
    }
    lock["lock_sha256"] = sha256_object(lock)
    if write:
        write_json(root / NVD_SNAPSHOT_REL, snapshot)
        write_json(root / NVD_LOCK_REL, lock)
    return {
        "status": "ok" if len(rows) >= 100 else "blocked",
        "source_snapshot_ref": NVD_SNAPSHOT_REL,
        "source_lock_ref": NVD_LOCK_REL,
        "source_snapshot_sha256": snapshot["snapshot_sha256"],
        "row_count": len(rows),
        "minimum_n_required": 100,
        "snapshot": snapshot,
        "lock": lock,
    }


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


def load_or_acquire_nvd(root: Path, *, write: bool) -> tuple[dict[str, Any], dict[str, Any]]:
    snapshot_path = root / NVD_SNAPSHOT_REL
    lock_path = root / NVD_LOCK_REL
    if snapshot_path.exists() and lock_path.exists():
        return read_json(snapshot_path), read_json(lock_path)
    acquired = acquire_nvd(root, write=write)
    return acquired["snapshot"], acquired["lock"]


def nvd_train_validation_holdout(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    total = len(rows)
    train_end = int(total * 0.6)
    validation_end = int(total * 0.8)
    return rows[:train_end], rows[train_end:validation_end], rows[validation_end:]


def nvd_feature_key_rows(row: dict[str, Any]) -> list[tuple[str, str]]:
    cwe = str((row.get("cwe_ids") or ["UNKNOWN"])[0])
    cpe_bin = str(min(int(row.get("cpe_match_count") or 0) // 5, 8))
    ref_bin = str(min(int(row.get("reference_count") or 0) // 5, 8))
    keys = [("cwe", cwe), ("cpe_bin", cpe_bin), ("ref_bin", ref_bin)]
    keys.extend(("tag", str(tag).lower()) for tag in row.get("reference_tags", []) or [])
    keys.extend(("tok", token) for token in nvd_visible_tokens(row))
    return keys


def nvd_train_model(train_rows: list[dict[str, Any]]) -> dict[str, Any]:
    scores = [float(row["hidden_cvss_base_score"]) for row in train_rows]
    values_by_key: dict[tuple[str, str], list[float]] = {}
    for row in train_rows:
        score = float(row["hidden_cvss_base_score"])
        for key in nvd_feature_key_rows(row):
            values_by_key.setdefault(key, []).append(score)
    medians = {
        f"{kind}::{value}": median(rows)
        for (kind, value), rows in values_by_key.items()
        if len(rows) >= (3 if kind != "tok" else 5)
    }
    return {
        "model_id": NVD_MODEL_ID,
        "model_rule": NVD_MODEL_RULE,
        "training_row_count": len(train_rows),
        "global_training_median": median(scores),
        "feature_medians": medians,
        "token_weight": 3,
        "target_values_used_for_model_design": False,
        "target_values_used_for_selection": False,
        "forbidden_inputs": [
            "hidden_cvss_base_score",
            "hidden_cvss_base_severity",
            "cvss vectorString",
            "exploitabilityScore",
            "impactScore",
        ],
    }


def nvd_predict_model(row: dict[str, Any], model: dict[str, Any]) -> float:
    medians = model.get("feature_medians", {})
    values: list[float] = []
    cwe = str((row.get("cwe_ids") or ["UNKNOWN"])[0])
    cwe_key = f"cwe::{cwe}"
    if cwe_key in medians:
        values.append(float(medians[cwe_key]))
    cpe_key = f"cpe_bin::{min(int(row.get('cpe_match_count') or 0) // 5, 8)}"
    ref_key = f"ref_bin::{min(int(row.get('reference_count') or 0) // 5, 8)}"
    for key in (cpe_key, ref_key):
        if key in medians:
            values.append(float(medians[key]))
    token_values = [
        float(medians[f"tok::{token}"])
        for token in nvd_visible_tokens(row)
        if f"tok::{token}" in medians
    ]
    if token_values:
        values.extend([median(token_values)] * int(model.get("token_weight") or 1))
    return rounded(mean(values) if values else float(model["global_training_median"]))


def nvd_predict_comparator(row: dict[str, Any], model: dict[str, Any]) -> float:
    cwe = str((row.get("cwe_ids") or ["UNKNOWN"])[0])
    return rounded(float(model.get("feature_medians", {}).get(f"cwe::{cwe}", model["global_training_median"])))


def nvd_summary(values: list[float]) -> dict[str, float]:
    return {
        "mean_absolute_error": rounded(mean(values)),
        "median_absolute_error": rounded(median(values)),
        "max_absolute_error": rounded(max(values) if values else 0.0),
    }


def nvd_jackknife_interval(values: list[float]) -> dict[str, float]:
    if len(values) <= 1:
        value = rounded(mean(values))
        return {"lower_mean_absolute_error": value, "upper_mean_absolute_error": value}
    estimates = [mean([value for idx, value in enumerate(values) if idx != index]) for index in range(len(values))]
    return {
        "lower_mean_absolute_error": rounded(min(estimates)),
        "upper_mean_absolute_error": rounded(max(estimates)),
    }


def build_nvd_task_table(snapshot: dict[str, Any], lock: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    rows = list(snapshot.get("rows", []) or [])
    train_rows, validation_rows, holdout_rows = nvd_train_validation_holdout(rows)
    model = nvd_train_model(train_rows)
    visible_rows = []
    hidden_targets = []
    for index, row in enumerate(holdout_rows):
        visible = {
            "task_id": f"NVD-CVSS-HOLDOUT-{index + 1:04d}",
            "cve_id": row.get("cve_id"),
            "published": row.get("published"),
            "source_identifier": row.get("source_identifier"),
            "description_sha256": sha256_object(row.get("description", "")),
            "description_token_total": len(nvd_visible_tokens(row)),
            "cwe_ids": row.get("cwe_ids"),
            "cpe_match_count": row.get("cpe_match_count"),
            "reference_tags": row.get("reference_tags"),
            "reference_count": row.get("reference_count"),
            "model_prediction_cvss": nvd_predict_model(row, model),
            "comparator_prediction_cvss": nvd_predict_comparator(row, model),
        }
        visible["visible_row_sha256"] = sha256_object(visible)
        target = {
            "task_id": visible["task_id"],
            "cve_id": row.get("cve_id"),
            "cvss_base_score": row.get("hidden_cvss_base_score"),
            "cvss_base_severity": row.get("hidden_cvss_base_severity"),
            "cvss_metric_version": row.get("hidden_cvss_metric_version"),
        }
        target["target_row_sha256"] = sha256_object(target)
        visible_rows.append(visible)
        hidden_targets.append(target)
    task_table = {
        "schema_id": NVD_TASK_TABLE_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_on": GENERATED_ON,
        "target_work_order_id": NVD_WORK_ORDER_ID,
        "source_snapshot_ref": NVD_SNAPSHOT_REL,
        "source_lock_ref": NVD_LOCK_REL,
        "source_snapshot_sha256": snapshot.get("snapshot_sha256"),
        "source_lock_sha256": lock.get("lock_sha256"),
        "train_row_count": len(train_rows),
        "validation_row_count": len(validation_rows),
        "holdout_row_count": len(holdout_rows),
        "target_hidden_until_scoring": True,
        "target_values_used_for_selection": False,
        "target_values_used_for_model_design": False,
        "model_manifest": model,
        "comparator_baseline": {
            "comparator_id": NVD_COMPARATOR_ID,
            "baseline_name": "NVD prior-CWE median comparator",
            "prediction_rule": NVD_COMPARATOR_RULE,
            "pre_registered": True,
            "target_values_used_for_baseline_design": False,
        },
        "hidden_target_fields": ["cvss_base_score", "cvss_base_severity", "cvss_metric_version"],
        "rows": visible_rows,
    }
    task_table["task_table_sha256"] = sha256_object(task_table)
    hidden_lock = {
        "schema_id": NVD_HIDDEN_TARGET_LOCK_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_on": GENERATED_ON,
        "target_work_order_id": NVD_WORK_ORDER_ID,
        "source_snapshot_ref": NVD_SNAPSHOT_REL,
        "visible_task_table_ref": NVD_TASK_TABLE_REL,
        "source_snapshot_sha256": snapshot.get("snapshot_sha256"),
        "task_table_sha256": task_table["task_table_sha256"],
        "target_hidden_until_scoring": True,
        "target_values_used_for_model_design": False,
        "target_fields": task_table["hidden_target_fields"],
        "rows": hidden_targets,
    }
    hidden_lock["target_map_sha256"] = sha256_object(
        [{"task_id": row["task_id"], "cvss_base_score": row["cvss_base_score"]} for row in hidden_targets]
    )
    hidden_lock["hidden_target_lock_sha256"] = sha256_object(hidden_lock)
    return task_table, hidden_lock, model


def build_nvd_scoring_pack(
    snapshot: dict[str, Any],
    lock: dict[str, Any],
    task_table: dict[str, Any],
    hidden_target_lock: dict[str, Any],
) -> dict[str, Any]:
    targets = {row["task_id"]: row for row in hidden_target_lock.get("rows", [])}
    row_results: list[dict[str, Any]] = []
    model_residuals: list[float] = []
    comparator_residuals: list[float] = []
    for task_row in task_table.get("rows", []):
        target = targets[task_row["task_id"]]
        observed = float(target["cvss_base_score"])
        model_prediction = float(task_row["model_prediction_cvss"])
        comparator_prediction = float(task_row["comparator_prediction_cvss"])
        model_residual = abs(model_prediction - observed)
        comparator_residual = abs(comparator_prediction - observed)
        result = {
            "task_id": task_row["task_id"],
            "cve_id": task_row["cve_id"],
            "visible_row_sha256": task_row["visible_row_sha256"],
            "hidden_target_row_sha256": target["target_row_sha256"],
            "model_prediction_cvss": rounded(model_prediction),
            "comparator_prediction_cvss": rounded(comparator_prediction),
            "observed_cvss_base_score": rounded(observed),
            "model_absolute_residual_cvss": rounded(model_residual),
            "comparator_absolute_residual_cvss": rounded(comparator_residual),
        }
        result["row_result_sha256"] = sha256_object(result)
        row_results.append(result)
        model_residuals.append(model_residual)
        comparator_residuals.append(comparator_residual)
    model_summary = nvd_summary(model_residuals)
    comparator_summary = nvd_summary(comparator_residuals)
    shuffled_targets = [row["cvss_base_score"] for row in hidden_target_lock.get("rows", [])]
    shuffled_targets = shuffled_targets[1:] + shuffled_targets[:1]
    control_residuals = [
        abs(float(task_row["model_prediction_cvss"]) - float(shuffled_target))
        for task_row, shuffled_target in zip(task_table.get("rows", []), shuffled_targets)
    ]
    control_summary = nvd_summary(control_residuals)
    control_target_hash = sha256_object(
        [{"task_id": row["task_id"], "cvss_base_score": score} for row, score in zip(hidden_target_lock.get("rows", []), shuffled_targets)]
    )
    negative_control_rejected = (
        control_target_hash != hidden_target_lock.get("target_map_sha256")
        and control_summary["mean_absolute_error"] > model_summary["mean_absolute_error"]
    )
    superiority_margin = rounded(comparator_summary["mean_absolute_error"] - model_summary["mean_absolute_error"])
    material_margin_required = 0.0
    material_margin_met = superiority_margin > material_margin_required and negative_control_rejected
    pack_status = (
        "STRICT_EVIDENCE_PASS_NO_COVERAGE_CLOSURE"
        if material_margin_met
        else "FAIL_CLOSED_SOURCE_BOUND_SCORING_MATERIALIZED_NEGATIVE_RESULT"
    )
    pack = {
        "schema_id": NVD_SCORING_PACK_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_on": GENERATED_ON,
        "capability_owner": CAPABILITY_OWNER,
        "target_work_order_id": NVD_WORK_ORDER_ID,
        "status": pack_status,
        "pack_status": pack_status,
        "scientific_pass": material_margin_met,
        "source_snapshot_ref": NVD_SNAPSHOT_REL,
        "source_lock_ref": NVD_LOCK_REL,
        "visible_task_table_ref": NVD_TASK_TABLE_REL,
        "hidden_target_lock_ref": NVD_HIDDEN_TARGET_LOCK_REL,
        "source_snapshot_sha256": snapshot.get("snapshot_sha256"),
        "source_lock_sha256": lock.get("lock_sha256"),
        "visible_task_table_sha256": task_table.get("task_table_sha256"),
        "hidden_target_lock_sha256": hidden_target_lock.get("hidden_target_lock_sha256"),
        "source": {
            "source_id": "NIST_NVD_CVE_API_2_0",
            "source_authority": "National Institute of Standards and Technology",
            "official_endpoint_url": nvd_official_url(),
            "official_documentation_url": "https://nvd.nist.gov/developers/vulnerabilities",
            "source_snapshot_ref": NVD_SNAPSHOT_REL,
            "source_snapshot_sha256": snapshot.get("snapshot_sha256"),
            "row_count": len(snapshot.get("rows", []) or []),
        },
        "source_separation": {
            "mode": "target_hidden_prospective_publication_date_split",
            "target_hidden_until_scoring": True,
            "target_values_used_for_selection": False,
            "target_values_used_for_model_design": False,
            "predictions_materialized_before_target_unseal": True,
            "visible_fields": snapshot.get("visible_fields"),
            "hidden_target_fields": task_table["hidden_target_fields"],
        },
        "formula_model": task_table["model_manifest"],
        "comparator_baseline": task_table["comparator_baseline"],
        "aggregate": {
            "model_mae": model_summary["mean_absolute_error"],
            "comparator_mae": comparator_summary["mean_absolute_error"],
            "superiority_margin_cvss": superiority_margin,
            "material_margin_met": material_margin_met,
            "material_margin_rule": "model mean absolute CVSS residual must be strictly below the preregistered prior-CWE median comparator and the shuffled-target control must be rejected",
        },
        "residuals": {
            "model": model_summary,
            "comparator": comparator_summary,
            "model_jackknife_interval": nvd_jackknife_interval(model_residuals),
            "comparator_jackknife_interval": nvd_jackknife_interval(comparator_residuals),
            "material_margin_met": material_margin_met,
        },
        "negative_control": {
            "control_id": "CS-NVD-CVSS-WITHIN-HOLDOUT-ROTATION",
            "description": "rotate heldout CVSS scores by one row after visible predictions are materialized",
            "locked_target_map_sha256": hidden_target_lock.get("target_map_sha256"),
            "control_target_map_sha256": control_target_hash,
            "model_control_residual": control_summary,
            "rejection_predicate": "control target map hash differs from locked target map and control model MAE exceeds locked-target model MAE",
            "rejected": negative_control_rejected,
        },
        "falsifier": {
            "falsifier_id": "CS-NVD-CVSS-SECURITY-FALSIFIER",
            "triggered": [] if material_margin_met else ["model did not beat comparator or negative control was not rejected"],
        },
        "row_count": len(row_results),
        "minimum_n_required": 100,
        "row_results_sha256": sha256_object(row_results),
        "row_results": row_results,
        "replay_command": {
            "commands": [
                f"python {SCRIPT_REL} --score-nvd --write-scoring",
                f"python {SCRIPT_REL} --check",
            ]
        },
        "coverage_closure_allowed": False,
        "support_allowed_for_broad_coverage": False,
        "broad_modern_science_superiority_allowed": False,
        "exact_blocker": None if material_margin_met else "COMPARATOR_BASELINE_NOT_BEATEN_OR_NEGATIVE_CONTROL_NOT_REJECTED",
        "no_send_locks": no_send(),
    }
    pack["scoring_pack_sha256"] = sha256_object(pack)
    return pack


def score_nvd(root: Path, *, write: bool) -> dict[str, Any]:
    snapshot, lock = load_or_acquire_nvd(root, write=write)
    task_table, hidden_target_lock, _model = build_nvd_task_table(snapshot, lock)
    scoring_pack = build_nvd_scoring_pack(snapshot, lock, task_table, hidden_target_lock)
    report = {
        "schema_id": NVD_REPLAY_REPORT_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_on": GENERATED_ON,
        "capability_owner": CAPABILITY_OWNER,
        "target_work_order_id": NVD_WORK_ORDER_ID,
        "status": "ok" if scoring_pack.get("row_count", 0) >= 100 else "blocked",
        "source_snapshot_ref": NVD_SNAPSHOT_REL,
        "source_lock_ref": NVD_LOCK_REL,
        "target_hidden_task_table_ref": NVD_TASK_TABLE_REL,
        "hidden_target_lock_ref": NVD_HIDDEN_TARGET_LOCK_REL,
        "scoring_pack_ref": NVD_SCORING_PACK_REL,
        "row_count": scoring_pack.get("row_count"),
        "minimum_n_required": scoring_pack.get("minimum_n_required"),
        "pack_status": scoring_pack.get("pack_status"),
        "model_mae": scoring_pack.get("aggregate", {}).get("model_mae"),
        "comparator_mae": scoring_pack.get("aggregate", {}).get("comparator_mae"),
        "material_margin_met": scoring_pack.get("aggregate", {}).get("material_margin_met"),
        "negative_control_rejected": scoring_pack.get("negative_control", {}).get("rejected"),
        "coverage_closure_allowed": False,
        "support_allowed_for_broad_coverage": False,
        "no_send_locks": no_send(),
    }
    report["report_sha256"] = sha256_object(report)
    if write:
        write_json(root / NVD_TASK_TABLE_REL, task_table)
        write_json(root / NVD_HIDDEN_TARGET_LOCK_REL, hidden_target_lock)
        write_json(root / NVD_SCORING_PACK_REL, scoring_pack)
        write_json(root / NVD_REPLAY_REPORT_REL, report)
    return {
        "status": "ok" if report["status"] == "ok" else "blocked",
        "pack_status": scoring_pack.get("pack_status"),
        "scoring_pack_ref": NVD_SCORING_PACK_REL,
        "report_ref": NVD_REPLAY_REPORT_REL,
        "row_count": scoring_pack.get("row_count"),
        "model_mae": report["model_mae"],
        "comparator_mae": report["comparator_mae"],
        "material_margin_met": report["material_margin_met"],
        "negative_control_rejected": report["negative_control_rejected"],
        "errors": [] if report["status"] == "ok" else ["NVD_ROW_COUNT_BELOW_MINIMUM"],
    }


def validate_nvd_stored(root: Path) -> list[str]:
    failures: list[str] = []
    for rel_path in (NVD_SNAPSHOT_REL, NVD_LOCK_REL, NVD_TASK_TABLE_REL, NVD_HIDDEN_TARGET_LOCK_REL, NVD_SCORING_PACK_REL):
        if not (root / rel_path).exists():
            continue
        payload = read_json(root / rel_path)
        if not isinstance(payload, dict):
            failures.append(f"NVD_PAYLOAD_NOT_OBJECT::{rel_path}")
            continue
        if payload.get("coverage_closure_allowed") not in {None, False}:
            failures.append(f"NVD_COVERAGE_CLOSURE_ALLOWED::{rel_path}")
    pack_path = root / NVD_SCORING_PACK_REL
    if pack_path.exists():
        pack = read_json(pack_path)
        snapshot = read_json(root / NVD_SNAPSHOT_REL)
        if pack.get("source_snapshot_sha256") != snapshot.get("snapshot_sha256"):
            failures.append("NVD_SOURCE_SNAPSHOT_HASH_MISMATCH")
        if pack.get("source_separation", {}).get("target_hidden_until_scoring") is not True:
            failures.append("NVD_TARGET_NOT_HIDDEN")
        if pack.get("row_count", 0) < 100:
            failures.append("NVD_ROW_COUNT_BELOW_MINIMUM")
        if pack.get("negative_control", {}).get("rejected") is not True:
            failures.append("NVD_NEGATIVE_CONTROL_NOT_REJECTED")
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
    failures.extend(validate_nvd_stored(root))
    return sorted(set(failures))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build/check CS modern-science coverage work orders.")
    parser.add_argument("--root", default=str(repo_root()), help="repository root")
    parser.add_argument("--write", action="store_true", help="write the deterministic work-order artifact")
    parser.add_argument("--check", action="store_true", help="check stored artifact synchronization")
    parser.add_argument("--refresh-nvd-source", action="store_true", help="fetch and lock the official NVD CVE source snapshot")
    parser.add_argument("--write-acquisition", action="store_true", help="write NVD acquisition/cache artifacts")
    parser.add_argument("--score-nvd", action="store_true", help="materialize target-hidden NVD CVSS scorer evidence")
    parser.add_argument("--write-scoring", action="store_true", help="write NVD scoring artifacts")
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
    if args.refresh_nvd_source:
        report = acquire_nvd(root, write=args.write_acquisition)
        print(
            json.dumps(
                {
                    "status": report["status"],
                    "source_snapshot_ref": NVD_SNAPSHOT_REL if args.write_acquisition else None,
                    "source_lock_ref": NVD_LOCK_REL if args.write_acquisition else None,
                    "row_count": report["row_count"],
                    "minimum_n_required": report["minimum_n_required"],
                },
                indent=2,
            )
        )
        return 0 if report["status"] == "ok" else 1
    if args.score_nvd:
        report = score_nvd(root, write=args.write_scoring)
        print(json.dumps(report, indent=2))
        return 0 if report["status"] == "ok" and not report["errors"] else 1
    payload = build_payload()
    failures = validate_payload(payload)
    if args.write:
        write_json(root / OUTPUT_REL, payload)
    print(json.dumps({"status": "ok" if not failures else "failed", "output_ref": OUTPUT_REL, "failures": failures}, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
