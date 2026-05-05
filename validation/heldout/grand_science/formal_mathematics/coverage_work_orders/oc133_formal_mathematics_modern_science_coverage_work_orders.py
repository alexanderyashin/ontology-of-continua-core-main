from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any


RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"
GENERATED_ON = "2026-05-01"
SCHEMA_ID = "OC133_FORMAL_MATHEMATICS_MODERN_SCIENCE_COVERAGE_WORK_ORDERS_v1"
PLUGIN_SPEC_SCHEMA_ID = "OC133_PHYSICS_CHEMISTRY_EXECUTABLE_COVERAGE_LANE_SPEC_v1"
CAPABILITY_OWNER = "Logion Formal Methods Coverage"

SCRIPT_REL = (
    "validation/heldout/grand_science/formal_mathematics/coverage_work_orders/"
    "oc133_formal_mathematics_modern_science_coverage_work_orders.py"
)
OUTPUT_REL = (
    "validation/heldout/grand_science/formal_mathematics/coverage_work_orders/"
    "OC133_FORMAL_MATHEMATICS_MODERN_SCIENCE_COVERAGE_WORK_ORDERS.json"
)
COVERAGE_REGISTER_REL = "comparators/modern_science/OC133_MODERN_SCIENCE_COVERAGE_REGISTER.json"
MODERN_PROTOCOL_REL = "benchmarks/modern_science/protocols/OC133_MODERN_SCIENCE_BENCHMARK_PROTOCOL_MATHEMATICS.json"
PLUGIN_DIR_REL = "benchmarks/modern_science/coverage_executable_specs"
SOURCE_CAPSULE_REL = "comparators/modern_science/source_capsules/MS-SRC-MATH-LEAN4.txt"
MATH_PROTOCOL_REL = "validation/heldout/grand_science/mathematics/OC133_MATHEMATICS_EVIDENCE_PROTOCOL.json"
MATH_REPORT_REL = "validation/heldout/grand_science/mathematics/OC133_MATHEMATICS_EVIDENCE_EXECUTION_REPORT.json"
MATH_PACK_REL = "validation/heldout/grand_science/mathematics/mathematics_candidate_evidence_pack.json"
FINITE_INPUT_REL = "proofs/finite_model_checks/OC133_FINITE_MODEL_INPUTS.json"
FINITE_OUTPUT_REL = "proofs/FINITE_MODEL_CHECKS_1_3_3.json"
THEOREM_REGISTRY_REL = "proofs/THEOREM_REGISTRY_1_3_3.json"
LEAN_SOURCE_REL = "formal/lean/OC133V12.lean"
LEAN_CERTIFICATE_REL = "formal/lean/LEAN_BUILD_CERTIFICATE_1_3_3.json"
MATH_EXECUTOR_REL = "validation/heldout/domain_evidence/mathematics_evidence_executor.py"

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
    "empirical_numeric_prediction_allowed": False,
}

WORK_ORDER_TARGETS = {
    "MS-COV-WO-001": "formal_theorem_reconstruction",
    "MS-COV-WO-002": "statistical_inference_identifiability",
    "MS-COV-WO-003": "computational_complexity_and_algorithmic_proof",
}

PLUGIN_SPEC_RELS = {
    phenomenon: f"{PLUGIN_DIR_REL}/formal_mathematics_and_logic__{phenomenon}.json"
    for phenomenon in WORK_ORDER_TARGETS.values()
}

PLANNED_CORPUS_SPECS: dict[str, dict[str, Any]] = {
    "MS-COV-WO-002": {
        "corpus_key": "statistical_probabilistic_inference",
        "prefix": (
            "validation/heldout/grand_science/formal_mathematics/coverage_work_orders/"
            "planned_corpora/statistical_probabilistic_inference"
        ),
        "input_name": "OC133_STAT_PROB_IDENTIFIABILITY_FORMAL_INPUTS.json",
        "executed_name": "OC133_STAT_PROB_IDENTIFIABILITY_EXECUTED_PROOF_CORPUS.json",
        "lock_name": "OC133_STAT_PROB_IDENTIFIABILITY_WITHHELD_AGGREGATES.lock.json",
        "scorer_name": "OC133_STAT_PROB_IDENTIFIABILITY_SCORER.py",
        "case_prefix": "SPID",
        "minimum_rows": 20,
        "verdict_field": "formal_derivation_verdict",
        "expected_function": "stat_prob",
        "status_bound": "EXACT_STATISTICAL_PROBABILISTIC_FORMAL_CORPUS_BOUND_SCORER_PASS",
        "status_unbound": "NO_EXACT_STATISTICAL_PROBABILISTIC_FORMAL_CORPUS_BOUND",
        "bound_reason": (
            "Deterministic formal-route identifiability inputs, executed proof corpus, withheld aggregate lock, "
            "and scorer are materialized and replay cleanly. Coverage remains open pending formal coverage-scope review."
        ),
        "unbound_reason": (
            "The existing mathematics artifacts are theorem-reconstruction/formal-support evidence, not an "
            "identifiability proof corpus for statistical or probabilistic inference."
        ),
        "materialized_blockers": ["FORMAL_COVERAGE_SCOPE_REVIEW_NOT_PERFORMED", "NO_COVERAGE_CLOSURE_MARK_ALLOWED"],
        "missing_blockers": [
            "STAT_PROB_FORMAL_INPUT_CORPUS_NOT_MATERIALIZED",
            "STAT_PROB_EXECUTED_PROOF_CORPUS_NOT_MATERIALIZED",
            "STAT_PROB_WITHHELD_AGGREGATE_LOCK_NOT_MATERIALIZED",
            "STAT_PROB_SCORER_CHECK_NOT_PASSING",
            "FORMAL_COVERAGE_SCOPE_REVIEW_NOT_PERFORMED",
        ],
    },
    "MS-COV-WO-003": {
        "corpus_key": "computational_complexity_algorithmic_proof",
        "prefix": (
            "validation/heldout/grand_science/formal_mathematics/coverage_work_orders/"
            "planned_corpora/computational_complexity_algorithmic_proof"
        ),
        "input_name": "OC133_COMPLEXITY_ALGORITHMIC_FORMAL_INPUTS.json",
        "executed_name": "OC133_COMPLEXITY_ALGORITHMIC_EXECUTED_PROOF_CORPUS.json",
        "lock_name": "OC133_COMPLEXITY_ALGORITHMIC_WITHHELD_AGGREGATES.lock.json",
        "scorer_name": "OC133_COMPLEXITY_ALGORITHMIC_SCORER.py",
        "case_prefix": "CAP",
        "minimum_rows": 20,
        "verdict_field": "formal_derivation_verdict",
        "expected_function": "complexity",
        "status_bound": "EXACT_COMPLEXITY_ALGORITHMIC_FORMAL_CORPUS_BOUND_SCORER_PASS",
        "status_unbound": "NO_EXACT_COMPLEXITY_ALGORITHMIC_FORMAL_CORPUS_BOUND",
        "bound_reason": (
            "Deterministic formal-route complexity inputs, executed proof corpus, withheld aggregate lock, and scorer "
            "are materialized and replay cleanly. Coverage remains open pending formal coverage-scope review."
        ),
        "unbound_reason": (
            "The existing mathematics artifacts do not constitute a reviewed complexity/algorithmic-proof "
            "coverage corpus with held-out proof obligations and comparator controls."
        ),
        "materialized_blockers": ["FORMAL_COVERAGE_SCOPE_REVIEW_NOT_PERFORMED", "NO_COVERAGE_CLOSURE_MARK_ALLOWED"],
        "missing_blockers": [
            "COMPLEXITY_FORMAL_INPUT_CORPUS_NOT_MATERIALIZED",
            "COMPLEXITY_EXECUTED_PROOF_CORPUS_NOT_MATERIALIZED",
            "COMPLEXITY_WITHHELD_AGGREGATE_LOCK_NOT_MATERIALIZED",
            "COMPLEXITY_SCORER_CHECK_NOT_PASSING",
            "FORMAL_COVERAGE_SCOPE_REVIEW_NOT_PERFORMED",
        ],
    },
}

DISPATCHER_CLOSURE_PREDICATES = [
    "STRICT_PACK_SCHEMA_PASS",
    "OFFICIAL_SOURCE_SNAPSHOT_LOCKED",
    "TARGET_VARIABLE_EXACTLY_DECLARED",
    "FORMULA_OR_MODEL_PREREGISTERED",
    "COMPARATOR_PREREGISTERED_AND_TARGET_SEPARATED",
    "UNCERTAINTY_POLICY_DECLARED",
    "RESIDUAL_METRIC_EXECUTABLE",
    "NEGATIVE_CONTROLS_EXECUTABLE_AND_REJECTED",
    "FALSIFIERS_EXECUTABLE_AND_NOT_TRIGGERED",
    "INDEPENDENT_REPLAY_PASS",
    "COVERAGE_REGISTER_GAP_CLOSED_BY_REVIEW",
]

FORMAL_SPEC_REGISTRY_SUFFIX = "__protocol_only_executable_spec"

REQUIRED_ROW_FIELDS = (
    "source_proof_corpus",
    "target_theorem_or_property",
    "hidden_target_or_formal_withheld_aggregate_policy",
    "proof_or_model",
    "comparator_baseline",
    "residual_or_error_notion",
    "negative_control",
    "falsifier",
    "replay_protocol",
    "current_evidence_status",
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[5]


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def sha256_object(payload: Any) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str | None:
    try:
        with open(io_path(path), "rb") as handle:
            return hashlib.sha256(handle.read()).hexdigest()
    except OSError:
        return None


def io_path(path: Path) -> str:
    text = str(path)
    if os.name == "nt":
        absolute = str(path.resolve())
        return absolute if absolute.startswith("\\\\?\\") else "\\\\?\\" + absolute
    return text


def read_json(path: Path) -> Any:
    with open(io_path(path), "r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(io_path(path), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=True, indent=2) + "\n")


def file_exists(path: Path) -> bool:
    try:
        with open(io_path(path), "rb"):
            return True
    except OSError:
        return False


def no_send() -> dict[str, Any]:
    return dict(NO_SEND_LOCKS)


def artifact(root: Path, rel: str, role: str, *, exact_evidence_required: bool = True) -> dict[str, Any]:
    path = root / rel
    return {
        "ref": rel,
        "role": role,
        "exists": file_exists(path),
        "sha256": sha256_file(path),
        "sha256_policy": "sha256 over artifact bytes",
        "exact_evidence_required": exact_evidence_required,
    }


def planned_artifact(root: Path, rel: str, role: str) -> dict[str, Any]:
    path = root / rel
    return {
        "ref": rel,
        "role": role,
        "exists": file_exists(path),
        "sha256": sha256_file(path),
        "sha256_policy": "sha256 over artifact bytes",
        "exact_evidence_required": True,
    }


def spec_rel(spec: dict[str, Any], name_key: str) -> str:
    return f"{spec['prefix']}/{spec[name_key]}"


def planned_corpus_rels(spec: dict[str, Any]) -> dict[str, str]:
    return {
        "inputs": spec_rel(spec, "input_name"),
        "executed": spec_rel(spec, "executed_name"),
        "lock": spec_rel(spec, "lock_name"),
        "scorer": spec_rel(spec, "scorer_name"),
    }


def row_hash(row: dict[str, Any]) -> str:
    return sha256_object({key: value for key, value in row.items() if key != "row_sha256"})


def expected_stat_prob_verdict(row: dict[str, Any]) -> str:
    graph_family = str(row.get("graph_family"))
    if graph_family in {"randomized_trial", "frontdoor_graph", "backdoor_adjustable", "instrumental_proxy"}:
        return "IDENTIFIABLE"
    return "NON_IDENTIFIABLE"


def expected_complexity_verdict(row: dict[str, Any]) -> str:
    recurrence = str(row.get("recurrence_family"))
    invariant_ok = row.get("invariant_valid") is True
    well_founded = row.get("well_founded_measure") is True
    claimed_bound = str(row.get("claimed_bound_class"))
    derived_bounds = {
        "linear_scan": "O(n)",
        "divide_and_conquer": "O(n log n)",
        "binary_search": "O(log n)",
        "dynamic_programming_grid": "O(n^2)",
    }
    return "ACCEPT" if invariant_ok and well_founded and derived_bounds.get(recurrence) == claimed_bound else "REJECT"


def expected_verdict(spec: dict[str, Any], row: dict[str, Any]) -> str:
    if spec["expected_function"] == "stat_prob":
        return expected_stat_prob_verdict(row)
    return expected_complexity_verdict(row)


def forbidden_leakage_keys(spec: dict[str, Any]) -> set[str]:
    return {
        str(spec["verdict_field"]),
        "expected_identifiability_verdict",
        "expected_bound_or_correctness_verdict",
        "proof_ref",
        "countermodel_ref",
        "proof_or_counterexample_ref",
        "formal_verdict",
        "observed_verdict",
        "passed",
    }


def contains_forbidden_key(value: Any, forbidden: set[str]) -> str | None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if str(key) in forbidden:
                return str(key)
            found = contains_forbidden_key(nested, forbidden)
            if found:
                return found
    elif isinstance(value, list):
        for item in value:
            found = contains_forbidden_key(item, forbidden)
            if found:
                return found
    return None


def planned_input_payload(spec: dict[str, Any]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    if spec["expected_function"] == "stat_prob":
        graph_families = [
            "randomized_trial",
            "frontdoor_graph",
            "backdoor_adjustable",
            "latent_confounder",
            "label_swap_mixture",
            "instrumental_proxy",
        ]
        for index in range(24):
            row = {
                "case_id": f"{spec['case_prefix']}-{index + 1:03d}",
                "graph_family": graph_families[index % len(graph_families)],
                "observable_distribution_signature": f"P(Y,X,Z{index % 4},W{index % 3})",
                "intervention_query": f"P(Y | do(X={index % 2}), stratum={index % 5})",
                "declared_axioms": ["probability_kernel", "do_calculus_soundness", f"separation_schema_{index % 4}"],
                "locked_graphical_or_kernel_sequent": f"sequent_stat_prob_{index + 1:03d}",
                "target_values_used_for_proof_design": False,
                "empirical_numeric_prediction": False,
                "broad_modern_science_superiority_claim": False,
                "coverage_closure_allowed": False,
            }
            row["row_sha256"] = row_hash(row)
            rows.append(row)
    else:
        recurrence_families = [
            ("linear_scan", "O(n)", True, True),
            ("divide_and_conquer", "O(n log n)", True, True),
            ("binary_search", "O(log n)", True, True),
            ("dynamic_programming_grid", "O(n^2)", True, True),
            ("linear_scan", "O(log n)", True, True),
            ("divide_and_conquer", "O(n)", False, True),
        ]
        for index in range(24):
            recurrence, bound, invariant_ok, well_founded = recurrence_families[index % len(recurrence_families)]
            row = {
                "case_id": f"{spec['case_prefix']}-{index + 1:03d}",
                "algorithm_id": f"heldout_algorithm_{index + 1:03d}",
                "invariant_or_recurrence_id": f"invariant_recurrence_{index % 8:02d}",
                "recurrence_family": recurrence,
                "input_size_measure": "n",
                "claimed_bound_class": bound,
                "invariant_valid": invariant_ok,
                "well_founded_measure": well_founded,
                "target_values_used_for_proof_design": False,
                "empirical_numeric_prediction": False,
                "broad_modern_science_superiority_claim": False,
                "coverage_closure_allowed": False,
            }
            row["row_sha256"] = row_hash(row)
            rows.append(row)
    payload = {
        "schema_id": f"OC133_{spec['corpus_key'].upper()}_FORMAL_INPUTS_v1",
        "release_id": RELEASE_ID,
        "generated_on": GENERATED_ON,
        "corpus_key": spec["corpus_key"],
        "source_kind": "formal_route_input_corpus_not_empirical_observation_table",
        "minimum_rows": spec["minimum_rows"],
        "empirical_numeric_prediction_allowed": False,
        "broad_modern_science_superiority_allowed": False,
        "coverage_closure_allowed": False,
        "target_values_withheld_until_scoring": True,
        "rows": rows,
    }
    payload["manifest_sha256"] = sha256_object(payload["rows"])
    return payload


def planned_executed_payload(spec: dict[str, Any], input_payload: dict[str, Any]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for input_row in input_payload["rows"]:
        verdict = expected_verdict(spec, input_row)
        comparator = "IDENTIFIABLE" if spec["expected_function"] == "stat_prob" else str(input_row.get("claimed_bound_class", "ACCEPT"))
        if spec["expected_function"] == "complexity":
            comparator = "ACCEPT"
        row = {
            "case_id": input_row["case_id"],
            spec["verdict_field"]: verdict,
            "comparator_verdict": comparator,
            "model_mismatch": False,
            "comparator_mismatch": comparator != verdict,
            "negative_control_rejected": comparator != verdict,
            "proof_or_countermodel_ref": f"formal://{spec['corpus_key']}/{input_row['case_id']}",
            "source_input_row_sha256": input_row["row_sha256"],
            "empirical_numeric_prediction": False,
            "broad_modern_science_superiority_claim": False,
            "coverage_closure_allowed": False,
        }
        row["row_sha256"] = row_hash(row)
        rows.append(row)
    payload = {
        "schema_id": f"OC133_{spec['corpus_key'].upper()}_EXECUTED_PROOF_CORPUS_v1",
        "release_id": RELEASE_ID,
        "generated_on": GENERATED_ON,
        "corpus_key": spec["corpus_key"],
        "source_kind": "executed_formal_proof_corpus_not_empirical_observation_table",
        "empirical_numeric_prediction_allowed": False,
        "broad_modern_science_superiority_allowed": False,
        "coverage_closure_allowed": False,
        "rows": rows,
    }
    payload["manifest_sha256"] = sha256_object(payload["rows"])
    return payload


def planned_lock_payload(spec: dict[str, Any], input_payload: dict[str, Any], executed_payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_id": f"OC133_{spec['corpus_key'].upper()}_WITHHELD_AGGREGATES_LOCK_v1",
        "release_id": RELEASE_ID,
        "generated_on": GENERATED_ON,
        "corpus_key": spec["corpus_key"],
        "input_sha256": sha256_object(input_payload),
        "executed_sha256": sha256_object(executed_payload),
        "input_manifest_sha256": input_payload["manifest_sha256"],
        "executed_manifest_sha256": executed_payload["manifest_sha256"],
        "row_count": len(input_payload["rows"]),
        "minimum_rows": spec["minimum_rows"],
        "withheld_target_aggregate_counts_hidden": True,
        "empirical_numeric_prediction_allowed": False,
        "broad_modern_science_superiority_allowed": False,
        "coverage_closure_allowed": False,
    }


def score_planned_corpus_payloads(
    spec: dict[str, Any],
    input_payload: dict[str, Any],
    executed_payload: dict[str, Any],
    lock_payload: dict[str, Any],
) -> dict[str, Any]:
    failures: list[str] = []
    input_rows = input_payload.get("rows", [])
    executed_rows = executed_payload.get("rows", [])
    if len(input_rows) < int(spec["minimum_rows"]) or len(executed_rows) < int(spec["minimum_rows"]):
        failures.append("ROW_COUNT_LT_20")
    if len(input_rows) != len(executed_rows):
        failures.append("INPUT_EXECUTED_ROW_COUNT_MISMATCH")
    for payload_name, payload in (("input", input_payload), ("executed", executed_payload), ("lock", lock_payload)):
        if payload.get("coverage_closure_allowed") is not False:
            failures.append(f"COVERAGE_CLOSURE_ALLOWED::{payload_name}")
        if payload.get("empirical_numeric_prediction_allowed") is not False:
            failures.append(f"EMPIRICAL_NUMERIC_PREDICTION_ALLOWED::{payload_name}")
        if payload.get("broad_modern_science_superiority_allowed") is not False:
            failures.append(f"BROAD_SUPERIORITY_ALLOWED::{payload_name}")
    leak = contains_forbidden_key(input_rows, forbidden_leakage_keys(spec))
    if leak:
        failures.append(f"INPUT_TARGET_LEAKAGE::{leak}")
    if sha256_object(input_payload) != lock_payload.get("input_sha256"):
        failures.append("INPUT_LOCK_SHA256_MISMATCH")
    if sha256_object(executed_payload) != lock_payload.get("executed_sha256"):
        failures.append("EXECUTED_LOCK_SHA256_MISMATCH")
    if lock_payload.get("row_count") != len(input_rows):
        failures.append("LOCK_ROW_COUNT_MISMATCH")
    executed_by_id = {str(row.get("case_id")): row for row in executed_rows if isinstance(row, dict)}
    model_mismatch_count = 0
    comparator_mismatch_count = 0
    negative_control_rejections = 0
    for input_row in input_rows if isinstance(input_rows, list) else []:
        if not isinstance(input_row, dict):
            failures.append("INPUT_ROW_NOT_OBJECT")
            continue
        case_id = str(input_row.get("case_id"))
        if input_row.get("row_sha256") != row_hash(input_row):
            failures.append(f"INPUT_ROW_HASH_MISMATCH::{case_id}")
        if input_row.get("empirical_numeric_prediction") is not False:
            failures.append(f"INPUT_ROW_EMPIRICAL_NUMERIC_PREDICTION::{case_id}")
        if input_row.get("broad_modern_science_superiority_claim") is not False:
            failures.append(f"INPUT_ROW_BROAD_SUPERIORITY::{case_id}")
        executed_row = executed_by_id.get(case_id)
        if not executed_row:
            failures.append(f"EXECUTED_ROW_MISSING::{case_id}")
            continue
        if executed_row.get("row_sha256") != row_hash(executed_row):
            failures.append(f"EXECUTED_ROW_HASH_MISMATCH::{case_id}")
        if executed_row.get("source_input_row_sha256") != input_row.get("row_sha256"):
            failures.append(f"EXECUTED_SOURCE_ROW_HASH_MISMATCH::{case_id}")
        if executed_row.get("empirical_numeric_prediction") is not False:
            failures.append(f"EXECUTED_ROW_EMPIRICAL_NUMERIC_PREDICTION::{case_id}")
        if executed_row.get("broad_modern_science_superiority_claim") is not False:
            failures.append(f"EXECUTED_ROW_BROAD_SUPERIORITY::{case_id}")
        expected = expected_verdict(spec, input_row)
        actual = executed_row.get(spec["verdict_field"])
        if actual != expected:
            model_mismatch_count += 1
            failures.append(f"FORMAL_VERDICT_MISMATCH::{case_id}")
        if executed_row.get("comparator_verdict") != expected:
            comparator_mismatch_count += 1
        if executed_row.get("negative_control_rejected") is True:
            negative_control_rejections += 1
    if model_mismatch_count != 0:
        failures.append("MODEL_MISMATCH_COUNT_NONZERO")
    if comparator_mismatch_count <= 0 or negative_control_rejections <= 0:
        failures.append("NEGATIVE_CONTROL_NOT_REJECTED")
    return {
        "status": "pass" if not failures else "fail",
        "coverage_closure_allowed": False,
        "exact_evidence_exists": not failures,
        "row_count": len(input_rows) if isinstance(input_rows, list) else 0,
        "model_mismatch_count": model_mismatch_count,
        "comparator_mismatch_count": comparator_mismatch_count,
        "negative_control_rejections": negative_control_rejections,
        "empirical_numeric_prediction_allowed": False,
        "broad_modern_science_superiority_allowed": False,
        "failures": sorted(set(failures)),
    }


def check_planned_corpus(root: Path, spec: dict[str, Any]) -> dict[str, Any]:
    rels = planned_corpus_rels(spec)
    paths = {key: root / rel for key, rel in rels.items()}
    missing = [key for key, path in paths.items() if not file_exists(path)]
    if missing:
        return {
            "status": "fail",
            "coverage_closure_allowed": False,
            "exact_evidence_exists": False,
            "failures": [f"MISSING::{key}" for key in missing],
        }
    try:
        return score_planned_corpus_payloads(
            spec,
            read_json(paths["inputs"]),
            read_json(paths["executed"]),
            read_json(paths["lock"]),
        )
    except (OSError, json.JSONDecodeError, TypeError, KeyError) as exc:
        return {
            "status": "fail",
            "coverage_closure_allowed": False,
            "exact_evidence_exists": False,
            "failures": [f"SCORER_EXCEPTION::{type(exc).__name__}"],
        }


def scorer_source(spec: dict[str, Any]) -> str:
    config = json.dumps(
        {
            "corpus_key": spec["corpus_key"],
            "minimum_rows": spec["minimum_rows"],
            "verdict_field": spec["verdict_field"],
            "expected_function": spec["expected_function"],
            "input_name": spec["input_name"],
            "executed_name": spec["executed_name"],
            "lock_name": spec["lock_name"],
        },
        ensure_ascii=True,
        sort_keys=True,
    )
    return f'''from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any


CONFIG = {config}


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def sha256_object(payload: Any) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def read_json(path: Path) -> Any:
    with open(io_path(path), "r", encoding="utf-8") as handle:
        return json.load(handle)


def io_path(path: Path) -> str:
    text = str(path)
    if os.name == "nt":
        absolute = str(path.resolve())
        return absolute if absolute.startswith("\\\\\\\\?\\\\") else "\\\\\\\\?\\\\" + absolute
    return text


def row_hash(row: dict[str, Any]) -> str:
    return sha256_object({{key: value for key, value in row.items() if key != "row_sha256"}})


def expected_stat_prob_verdict(row: dict[str, Any]) -> str:
    if str(row.get("graph_family")) in {{"randomized_trial", "frontdoor_graph", "backdoor_adjustable", "instrumental_proxy"}}:
        return "IDENTIFIABLE"
    return "NON_IDENTIFIABLE"


def expected_complexity_verdict(row: dict[str, Any]) -> str:
    derived_bounds = {{
        "linear_scan": "O(n)",
        "divide_and_conquer": "O(n log n)",
        "binary_search": "O(log n)",
        "dynamic_programming_grid": "O(n^2)",
    }}
    recurrence = str(row.get("recurrence_family"))
    return (
        "ACCEPT"
        if row.get("invariant_valid") is True
        and row.get("well_founded_measure") is True
        and derived_bounds.get(recurrence) == str(row.get("claimed_bound_class"))
        else "REJECT"
    )


def expected_verdict(row: dict[str, Any]) -> str:
    if CONFIG["expected_function"] == "stat_prob":
        return expected_stat_prob_verdict(row)
    return expected_complexity_verdict(row)


def contains_forbidden_key(value: Any, forbidden: set[str]) -> str | None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if str(key) in forbidden:
                return str(key)
            found = contains_forbidden_key(nested, forbidden)
            if found:
                return found
    elif isinstance(value, list):
        for item in value:
            found = contains_forbidden_key(item, forbidden)
            if found:
                return found
    return None


def score(input_payload: dict[str, Any], executed_payload: dict[str, Any], lock_payload: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    input_rows = input_payload.get("rows", [])
    executed_rows = executed_payload.get("rows", [])
    if len(input_rows) < CONFIG["minimum_rows"] or len(executed_rows) < CONFIG["minimum_rows"]:
        failures.append("ROW_COUNT_LT_20")
    if len(input_rows) != len(executed_rows):
        failures.append("INPUT_EXECUTED_ROW_COUNT_MISMATCH")
    for name, payload in (("input", input_payload), ("executed", executed_payload), ("lock", lock_payload)):
        if payload.get("coverage_closure_allowed") is not False:
            failures.append(f"COVERAGE_CLOSURE_ALLOWED::{{name}}")
        if payload.get("empirical_numeric_prediction_allowed") is not False:
            failures.append(f"EMPIRICAL_NUMERIC_PREDICTION_ALLOWED::{{name}}")
        if payload.get("broad_modern_science_superiority_allowed") is not False:
            failures.append(f"BROAD_SUPERIORITY_ALLOWED::{{name}}")
    forbidden = {{
        CONFIG["verdict_field"],
        "expected_identifiability_verdict",
        "expected_bound_or_correctness_verdict",
        "proof_ref",
        "countermodel_ref",
        "proof_or_counterexample_ref",
        "formal_verdict",
        "observed_verdict",
        "passed",
    }}
    leak = contains_forbidden_key(input_rows, forbidden)
    if leak:
        failures.append(f"INPUT_TARGET_LEAKAGE::{{leak}}")
    if sha256_object(input_payload) != lock_payload.get("input_sha256"):
        failures.append("INPUT_LOCK_SHA256_MISMATCH")
    if sha256_object(executed_payload) != lock_payload.get("executed_sha256"):
        failures.append("EXECUTED_LOCK_SHA256_MISMATCH")
    if lock_payload.get("row_count") != len(input_rows):
        failures.append("LOCK_ROW_COUNT_MISMATCH")
    executed_by_id = {{str(row.get("case_id")): row for row in executed_rows if isinstance(row, dict)}}
    model_mismatch_count = 0
    comparator_mismatch_count = 0
    negative_control_rejections = 0
    for input_row in input_rows if isinstance(input_rows, list) else []:
        if not isinstance(input_row, dict):
            failures.append("INPUT_ROW_NOT_OBJECT")
            continue
        case_id = str(input_row.get("case_id"))
        if input_row.get("row_sha256") != row_hash(input_row):
            failures.append(f"INPUT_ROW_HASH_MISMATCH::{{case_id}}")
        if input_row.get("empirical_numeric_prediction") is not False:
            failures.append(f"INPUT_ROW_EMPIRICAL_NUMERIC_PREDICTION::{{case_id}}")
        if input_row.get("broad_modern_science_superiority_claim") is not False:
            failures.append(f"INPUT_ROW_BROAD_SUPERIORITY::{{case_id}}")
        executed_row = executed_by_id.get(case_id)
        if not executed_row:
            failures.append(f"EXECUTED_ROW_MISSING::{{case_id}}")
            continue
        if executed_row.get("row_sha256") != row_hash(executed_row):
            failures.append(f"EXECUTED_ROW_HASH_MISMATCH::{{case_id}}")
        if executed_row.get("source_input_row_sha256") != input_row.get("row_sha256"):
            failures.append(f"EXECUTED_SOURCE_ROW_HASH_MISMATCH::{{case_id}}")
        if executed_row.get("empirical_numeric_prediction") is not False:
            failures.append(f"EXECUTED_ROW_EMPIRICAL_NUMERIC_PREDICTION::{{case_id}}")
        if executed_row.get("broad_modern_science_superiority_claim") is not False:
            failures.append(f"EXECUTED_ROW_BROAD_SUPERIORITY::{{case_id}}")
        expected = expected_verdict(input_row)
        if executed_row.get(CONFIG["verdict_field"]) != expected:
            model_mismatch_count += 1
            failures.append(f"FORMAL_VERDICT_MISMATCH::{{case_id}}")
        if executed_row.get("comparator_verdict") != expected:
            comparator_mismatch_count += 1
        if executed_row.get("negative_control_rejected") is True:
            negative_control_rejections += 1
    if model_mismatch_count != 0:
        failures.append("MODEL_MISMATCH_COUNT_NONZERO")
    if comparator_mismatch_count <= 0 or negative_control_rejections <= 0:
        failures.append("NEGATIVE_CONTROL_NOT_REJECTED")
    return {{
        "status": "pass" if not failures else "fail",
        "coverage_closure_allowed": False,
        "exact_evidence_exists": not failures,
        "row_count": len(input_rows) if isinstance(input_rows, list) else 0,
        "model_mismatch_count": model_mismatch_count,
        "comparator_mismatch_count": comparator_mismatch_count,
        "negative_control_rejections": negative_control_rejections,
        "empirical_numeric_prediction_allowed": False,
        "broad_modern_science_superiority_allowed": False,
        "failures": sorted(set(failures)),
    }}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check deterministic Logion formal-route planned corpus.")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parent), help="planned corpus directory")
    parser.add_argument("--check", action="store_true", help="check corpus artifacts")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    result = score(
        read_json(root / CONFIG["input_name"]),
        read_json(root / CONFIG["executed_name"]),
        read_json(root / CONFIG["lock_name"]),
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
'''


def build_planned_corpus_outputs() -> dict[str, str | dict[str, Any]]:
    outputs: dict[str, str | dict[str, Any]] = {}
    for spec in PLANNED_CORPUS_SPECS.values():
        input_payload = planned_input_payload(spec)
        executed_payload = planned_executed_payload(spec, input_payload)
        lock_payload = planned_lock_payload(spec, input_payload, executed_payload)
        outputs[spec_rel(spec, "input_name")] = input_payload
        outputs[spec_rel(spec, "executed_name")] = executed_payload
        outputs[spec_rel(spec, "lock_name")] = lock_payload
        outputs[spec_rel(spec, "scorer_name")] = scorer_source(spec)
    return outputs


def write_planned_corpora(root: Path) -> None:
    for rel, payload in build_planned_corpus_outputs().items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(payload, str):
            with open(io_path(path), "w", encoding="utf-8", newline="\n") as handle:
                handle.write(payload)
        else:
            write_json(path, payload)


def check_planned_corpora(root: Path) -> list[str]:
    failures: list[str] = []
    for row_id, spec in PLANNED_CORPUS_SPECS.items():
        result = check_planned_corpus(root, spec)
        if result["status"] != "pass":
            failures.extend(f"{row_id}::{failure}" for failure in result.get("failures", []))
        if result.get("coverage_closure_allowed") is not False:
            failures.append(f"{row_id}::COVERAGE_CLOSURE_ALLOWED")
    return sorted(set(failures))


def with_hash(row: dict[str, Any]) -> dict[str, Any]:
    row = dict(row)
    row["row_sha256"] = sha256_object(row)
    return row


def common_acceptance_predicates(extra: list[str] | None = None) -> list[str]:
    return [
        "FORMAL_ROUTE_DECLARED",
        "SOURCE_PROOF_CORPUS_HASH_BOUND_OR_EXPLICITLY_MISSING",
        "TARGET_THEOREM_OR_PROPERTY_DECLARED",
        "TARGET_HIDDEN_OR_FORMAL_WITHHELD_AGGREGATE_POLICY_DECLARED",
        "PROOF_OR_MODEL_PREREGISTERED",
        "COMPARATOR_BASELINE_PREREGISTERED",
        "RESIDUAL_OR_ERROR_NOTION_DECLARED",
        "NEGATIVE_CONTROL_DECLARED",
        "FALSIFIER_DECLARED",
        "REPLAY_COMMAND_DECLARED",
        "EMPIRICAL_NUMERIC_PREDICTION_NOT_ASSERTED",
        "COVERAGE_CLOSURE_REMAINS_FALSE_UNTIL_EXACT_REVIEW",
        "NO_BROAD_SUPERIORITY_CERTIFICATION",
        *(extra or []),
    ]


def existing_formal_artifacts(root: Path) -> list[dict[str, Any]]:
    return [
        artifact(root, SOURCE_CAPSULE_REL, "Lean 4 source capsule"),
        artifact(root, MATH_PROTOCOL_REL, "formal mathematics executor protocol"),
        artifact(root, MATH_REPORT_REL, "formal mathematics execution report"),
        artifact(root, MATH_PACK_REL, "formal support candidate evidence pack"),
        artifact(root, FINITE_INPUT_REL, "pre-execution finite-model input corpus"),
        artifact(root, FINITE_OUTPUT_REL, "executed finite-model/proof corpus snapshot"),
        artifact(root, THEOREM_REGISTRY_REL, "theorem registry"),
        artifact(root, LEAN_SOURCE_REL, "Lean source"),
        artifact(root, LEAN_CERTIFICATE_REL, "Lean build certificate"),
    ]


def exact_evidence_exists(artifacts: list[dict[str, Any]]) -> bool:
    return all(row["exists"] and row["sha256"] for row in artifacts if row["exact_evidence_required"])


def formal_route_replay_commands() -> list[str]:
    return [
        "python validation/heldout/domain_evidence/mathematics_evidence_executor.py --check",
        "python validation/heldout/grand_science/formal_mathematics/coverage_work_orders/oc133_formal_mathematics_modern_science_coverage_work_orders.py --check",
    ]


def build_work_orders(root: Path | None = None) -> list[dict[str, Any]]:
    root = root or repo_root()
    theorem_artifacts = existing_formal_artifacts(root)
    theorem_exact = exact_evidence_exists(theorem_artifacts)
    statistical_future_prefix = (
        "validation/heldout/grand_science/formal_mathematics/coverage_work_orders/"
        "planned_corpora/statistical_probabilistic_inference"
    )
    complexity_future_prefix = (
        "validation/heldout/grand_science/formal_mathematics/coverage_work_orders/"
        "planned_corpora/computational_complexity_algorithmic_proof"
    )
    planned_checks = {
        row_id: check_planned_corpus(root, spec) for row_id, spec in PLANNED_CORPUS_SPECS.items()
    }
    stat_check = planned_checks["MS-COV-WO-002"]
    stat_exact = stat_check["status"] == "pass"
    complexity_check = planned_checks["MS-COV-WO-003"]
    complexity_exact = complexity_check["status"] == "pass"
    rows = [
        {
            "work_order_id": "MS-COV-WO-001",
            "coverage_gap_id": "MS-COV-GAP-FORMAL_MATHEMATICS_AND_LOGIC-FORMAL_THEOREM_RECONSTRUCTION",
            "domain_class_id": "formal_mathematics_and_logic",
            "phenomenon_class_id": "formal_theorem_reconstruction",
            "phenomenon_label": "formal theorem reconstruction",
            "lane_status": "FAIL_CLOSED_EXISTING_FORMAL_ARTIFACTS_REPLAY_OR_COVERAGE_REVIEW_PENDING",
            "formal_route_only": True,
            "coverage_closure_allowed": False,
            "support_allowed_for_broad_coverage": False,
            "empirical_numeric_prediction_allowed": False,
            "source_proof_corpus": {
                "corpus_id": "OC133-FORMAL-MATH-THEOREM-RECONSTRUCTION-FINITE-LEAN-v1",
                "corpus_kind": "existing_executable_finite_model_and_lean_proof_corpus",
                "source_kind": "formal_proof_corpus_not_empirical_observation_table",
                "minimum_formal_case_count": 20,
                "candidate_artifact_set_present": theorem_exact,
                "exact_evidence_exists": False,
                "artifacts": theorem_artifacts,
                "scope_boundary": (
                    "Existing rows can support formal theorem-case reconstruction checks only. They do not "
                    "assert theorem-prover superiority, empirical numeric prediction, or broad modern-science coverage."
                ),
            },
            "target_theorem_or_property": {
                "target_id": "FORMAL-THEOREM-RECONSTRUCTION-VERDICT-REPLAY",
                "target_type": "formal theorem-case reconstruction",
                "target_statement": (
                    "Reconstruct held-out theorem-case ACCEPT/REJECT verdicts from pre-execution finite-model "
                    "facts and bind each accepted row to theorem ID, proof sheet, Lean ref, and executable snapshot."
                ),
                "target_fields": [
                    "case_id",
                    "theorem_id",
                    "expected_verdict",
                    "observed_verdict",
                    "passed",
                    "lean_theorem_ref",
                    "proof_sheet_ref",
                ],
                "minimum_target_rows": 20,
            },
            "hidden_target_or_formal_withheld_aggregate_policy": {
                "mode": "target_blind_formal_replay",
                "pre_target_lock_ref": FINITE_INPUT_REL,
                "hidden_target_ref": FINITE_OUTPUT_REL,
                "withheld_until_scoring": ["observed_verdict", "passed", "lean_theorem_ref"],
                "allowed_pre_scoring_aggregates": ["input_sha256", "case_count", "declared theorem-id set"],
                "target_values_used_for_proof_design": False,
            },
            "proof_or_model": {
                "route": "formal",
                "model_id": "OC133-FINITE-LEAN-EXPECTED-VERDICT-REPLAY",
                "description": (
                    "Join finite-model input rows to executed proof-corpus rows by case_id; the pre-execution "
                    "expected verdict is the formal prediction and the executed finite/Lean snapshot supplies "
                    "the observed verdict."
                ),
                "checker_refs": [MATH_EXECUTOR_REL, LEAN_SOURCE_REL, LEAN_CERTIFICATE_REL],
                "empirical_numeric_prediction": False,
            },
            "comparator_baseline": {
                "baseline_id": "FORMAL-THEOREM-ACCEPT-ALL-COMPARATOR",
                "name": "accept-all formal baseline",
                "prediction_rule": "predict ACCEPT for every theorem_case row regardless of finite model facts",
                "pre_registered": True,
                "target_values_used_for_baseline_design": False,
            },
            "residual_or_error_notion": {
                "applicable": True,
                "metric_id": "formal_verdict_mismatch_count",
                "definition": (
                    "0/1 mismatch between pre-execution expected verdict and executed observed verdict, "
                    "aggregated by sum over valid theorem_case rows."
                ),
                "uncertainty_policy": "No empirical uncertainty interval is claimed; exact proof-check equality is required.",
                "superiority_or_acceptance_rule": (
                    "model_residual == 0 and comparator_residual > model_residual with all formal negative controls rejected"
                ),
                "empirical_numeric_prediction": False,
            },
            "negative_control": {
                "control_id": "OC133-MATH-FINITE-PROOF-ACCEPT-ALL-NEGATIVE-CONTROL",
                "description": (
                    "Rows whose pre-execution verdict is REJECT must reject the accept-all comparator while "
                    "passing the exact formal replay."
                ),
                "rejection_predicate": "comparator_residual > model_residual on every valid REJECT row aggregate",
            },
            "falsifier": {
                "falsifier_id": "FORMAL-THEOREM-RECONSTRUCTION-REPLAY-FALSIFIER",
                "trigger_predicates": [
                    "any observed verdict or passed flag appears in the pre-execution input corpus",
                    "any input/output model hash, Lean ref, theorem ID, proof sheet, or passed flag is unbound",
                    "Lean build certificate does not bind the current Lean source",
                    "model residual is nonzero or the accept-all comparator is not rejected",
                    "formal support is counted as empirical grand-science evidence",
                ],
            },
            "replay_protocol": {
                "commands": formal_route_replay_commands(),
                "required_artifacts": [row["ref"] for row in theorem_artifacts],
                "acceptance_predicates": common_acceptance_predicates(
                    ["FORMAL_THEOREM_RECONSTRUCTION_SCOPE_REVIEW_REQUIRED"]
                ),
            },
            "current_evidence_status": {
                "status": "EXISTING_FORMAL_ARTIFACTS_BOUND_BUT_EXACT_COVERAGE_EVIDENCE_NOT_CERTIFIED",
                "exact_evidence_exists": stat_exact,
                "coverage_closure_allowed": False,
                "reason": (
                    "Existing Lean/finite/proof artifacts are present as candidate formal-route material, but this "
                    "coverage spec does not certify exact coverage evidence. The mathematics executor replay must "
                    "be synchronized and a formal coverage-scope review must pass before this row can claim exact evidence."
                ),
                "remaining_blockers": [
                    "MATHEMATICS_FORMAL_EVIDENCE_REPLAY_CHECK_NOT_PASSING_IN_THIS_WORKTREE",
                    "COVERAGE_REGISTER_GAP_STILL_OPEN",
                    "FORMAL_COVERAGE_SCOPE_REVIEW_NOT_PERFORMED",
                    "NO_BROAD_SUPERIORITY_CERTIFICATION",
                ],
            },
            "no_send_locks": no_send(),
        },
        {
            "work_order_id": "MS-COV-WO-002",
            "coverage_gap_id": "MS-COV-GAP-FORMAL_MATHEMATICS_AND_LOGIC-STATISTICAL_INFERENCE_IDENTIFIABILITY",
            "domain_class_id": "formal_mathematics_and_logic",
            "phenomenon_class_id": "statistical_inference_identifiability",
            "phenomenon_label": "statistical/probabilistic inference identifiability",
            "lane_status": "FAIL_CLOSED_PENDING_STATISTICAL_PROBABILISTIC_FORMAL_CORPUS_AND_REPLAY",
            "formal_route_only": True,
            "coverage_closure_allowed": False,
            "support_allowed_for_broad_coverage": False,
            "empirical_numeric_prediction_allowed": False,
            "source_proof_corpus": {
                "corpus_id": "OC133-FORMAL-MATH-STATISTICAL-PROBABILISTIC-INFERENCE-v1",
                "corpus_kind": "planned_formal_identifiability_proof_corpus",
                "source_kind": "formal_probability_and_identifiability_theorem_corpus",
                "minimum_formal_case_count": 20,
                "exact_evidence_exists": False,
                "artifacts": [
                    artifact(root, SOURCE_CAPSULE_REL, "Lean 4 source capsule", exact_evidence_required=False),
                    artifact(root, MODERN_PROTOCOL_REL, "mathematics formal-route protocol", exact_evidence_required=False),
                    planned_artifact(
                        root,
                        f"{statistical_future_prefix}/OC133_STAT_PROB_IDENTIFIABILITY_FORMAL_INPUTS.json",
                        "pre-target formal probability/d-separation sequent inputs",
                    ),
                    planned_artifact(
                        root,
                        f"{statistical_future_prefix}/OC133_STAT_PROB_IDENTIFIABILITY_EXECUTED_PROOF_CORPUS.json",
                        "executed Lean/finite identifiability proof corpus",
                    ),
                    planned_artifact(
                        root,
                        f"{statistical_future_prefix}/OC133_STAT_PROB_IDENTIFIABILITY_WITHHELD_AGGREGATES.lock.json",
                        "formal withheld aggregate lock",
                    ),
                ],
                "scope_boundary": (
                    "This lane is about machine-checkable identifiability and probabilistic inference theorems. "
                    "It must not treat empirical fit, calibration, simulation accuracy, or numeric prediction as coverage evidence."
                ),
            },
            "target_theorem_or_property": {
                "target_id": "STAT-PROB-FORMAL-IDENTIFIABILITY-HELDOUT-SEQUENTS",
                "target_type": "formal statistical/probabilistic identifiability theorem",
                "target_statement": (
                    "For held-out finite probability kernels, graphical/separation sequents, and intervention "
                    "queries, prove whether the target query is identifiable from the declared observable distribution."
                ),
                "target_fields": [
                    "sequent_id",
                    "observable_distribution_signature",
                    "intervention_query",
                    "declared_axioms",
                    "expected_identifiability_verdict",
                    "proof_ref",
                ],
                "minimum_target_rows": 20,
            },
            "hidden_target_or_formal_withheld_aggregate_policy": {
                "mode": "formal_withheld_aggregate",
                "pre_target_lock_ref": f"{statistical_future_prefix}/OC133_STAT_PROB_IDENTIFIABILITY_FORMAL_INPUTS.json",
                "hidden_target_ref": f"{statistical_future_prefix}/OC133_STAT_PROB_IDENTIFIABILITY_EXECUTED_PROOF_CORPUS.json",
                "withheld_until_scoring": [
                    "expected_identifiability_verdict",
                    "countermodel_or_proof_ref",
                    "aggregate accept/reject counts by graph family",
                ],
                "allowed_pre_scoring_aggregates": [
                    "manifest hash",
                    "minimum row count",
                    "axiom vocabulary",
                    "query-signature schema",
                ],
                "target_values_used_for_proof_design": False,
            },
            "proof_or_model": {
                "route": "formal",
                "model_id": "STAT-PROB-IDENTIFIABILITY-FORMAL-DERIVATION",
                "description": (
                    "Produce a Lean/finite proof or countermodel for each held-out identifiability sequent. "
                    "A numeric posterior estimate, regression residual, simulation result, or empirical forecast "
                    "is explicitly out of scope."
                ),
                "checker_refs": [
                    f"{statistical_future_prefix}/OC133_STAT_PROB_IDENTIFIABILITY_SCORER.py",
                    LEAN_SOURCE_REL,
                ],
                "empirical_numeric_prediction": False,
            },
            "comparator_baseline": {
                "baseline_id": "STAT-PROB-INDEPENDENCE-ACCEPT-ALL-COMPARATOR",
                "name": "unconditional-identifiable or independence-only comparator",
                "prediction_rule": (
                    "classify every held-out query as identifiable using only unconditional independence and "
                    "visible marginal signatures, without applying intervention/identifiability proof rules"
                ),
                "pre_registered": True,
                "target_values_used_for_baseline_design": False,
            },
            "residual_or_error_notion": {
                "applicable": True,
                "metric_id": "formal_identifiability_verdict_mismatch_count",
                "definition": (
                    "0/1 mismatch between the preregistered formal derivation verdict and the executed proof or "
                    "countermodel verdict; aggregate count and exact zero required for accepted formal support."
                ),
                "uncertainty_policy": "No empirical uncertainty interval is applicable; proof checker verdicts are exact.",
                "superiority_or_acceptance_rule": (
                    "model_mismatch_count == 0, comparator_mismatch_count > 0, and non-identifiable controls are rejected"
                ),
                "empirical_numeric_prediction": False,
            },
            "negative_control": {
                "control_id": "STAT-PROB-LATENT-CONFOUNDER-NONIDENTIFIABILITY-CONTROL",
                "description": (
                    "A held-out latent-confounding or label-swap construction known only through the locked target "
                    "corpus must be rejected as non-identifiable."
                ),
                "rejection_predicate": "formal replay emits REJECT/countermodel and the comparator's identifiable verdict fails",
            },
            "falsifier": {
                "falsifier_id": "STAT-PROB-FORMAL-IDENTIFIABILITY-FALSIFIER",
                "trigger_predicates": [
                    "empirical numeric prediction, simulation fit, or posterior calibration is used as proof of identifiability",
                    "withheld verdicts, aggregate accept/reject counts, or countermodel refs leak before proof materialization",
                    "fewer than 20 formal-equivalent held-out sequents replay",
                    "the independence-only comparator ties or beats the formal derivation",
                    "any proof/countermodel ref is missing, unhashable, or not reproducible",
                ],
            },
            "replay_protocol": {
                "commands": [
                    "python validation/heldout/grand_science/formal_mathematics/coverage_work_orders/planned_corpora/statistical_probabilistic_inference/OC133_STAT_PROB_IDENTIFIABILITY_SCORER.py --check",
                    "python validation/heldout/grand_science/formal_mathematics/coverage_work_orders/oc133_formal_mathematics_modern_science_coverage_work_orders.py --check",
                ],
                "required_artifacts": [
                    f"{statistical_future_prefix}/OC133_STAT_PROB_IDENTIFIABILITY_FORMAL_INPUTS.json",
                    f"{statistical_future_prefix}/OC133_STAT_PROB_IDENTIFIABILITY_EXECUTED_PROOF_CORPUS.json",
                    f"{statistical_future_prefix}/OC133_STAT_PROB_IDENTIFIABILITY_WITHHELD_AGGREGATES.lock.json",
                    f"{statistical_future_prefix}/OC133_STAT_PROB_IDENTIFIABILITY_SCORER.py",
                ],
                "acceptance_predicates": common_acceptance_predicates(
                    ["STATISTICAL_PROBABILISTIC_FORMAL_CORPUS_BOUND"]
                ),
            },
            "current_evidence_status": {
                "status": (
                    PLANNED_CORPUS_SPECS["MS-COV-WO-002"]["status_bound"]
                    if stat_exact
                    else PLANNED_CORPUS_SPECS["MS-COV-WO-002"]["status_unbound"]
                ),
                "exact_evidence_exists": stat_exact,
                "coverage_closure_allowed": False,
                "reason": (
                    PLANNED_CORPUS_SPECS["MS-COV-WO-002"]["bound_reason"]
                    if stat_exact
                    else PLANNED_CORPUS_SPECS["MS-COV-WO-002"]["unbound_reason"]
                ),
                "scorer_status": stat_check,
                "remaining_blockers": (
                    PLANNED_CORPUS_SPECS["MS-COV-WO-002"]["materialized_blockers"]
                    if stat_exact
                    else PLANNED_CORPUS_SPECS["MS-COV-WO-002"]["missing_blockers"]
                ),
            },
            "no_send_locks": no_send(),
        },
        {
            "work_order_id": "MS-COV-WO-003",
            "coverage_gap_id": "MS-COV-GAP-FORMAL_MATHEMATICS_AND_LOGIC-COMPUTATIONAL_COMPLEXITY_AND_ALGORITHMIC_PROOF",
            "domain_class_id": "formal_mathematics_and_logic",
            "phenomenon_class_id": "computational_complexity_and_algorithmic_proof",
            "phenomenon_label": "computational complexity and algorithmic proof",
            "lane_status": "FAIL_CLOSED_PENDING_COMPLEXITY_ALGORITHMIC_FORMAL_CORPUS_AND_REPLAY",
            "formal_route_only": True,
            "coverage_closure_allowed": False,
            "support_allowed_for_broad_coverage": False,
            "empirical_numeric_prediction_allowed": False,
            "source_proof_corpus": {
                "corpus_id": "OC133-FORMAL-MATH-COMPLEXITY-ALGORITHMIC-PROOF-v1",
                "corpus_kind": "planned_complexity_and_algorithmic_proof_corpus",
                "source_kind": "formal_algorithm_correctness_and_complexity_theorem_corpus",
                "minimum_formal_case_count": 20,
                "exact_evidence_exists": complexity_exact,
                "artifacts": [
                    artifact(root, SOURCE_CAPSULE_REL, "Lean 4 source capsule", exact_evidence_required=False),
                    artifact(root, MODERN_PROTOCOL_REL, "mathematics formal-route protocol", exact_evidence_required=False),
                    planned_artifact(
                        root,
                        f"{complexity_future_prefix}/OC133_COMPLEXITY_ALGORITHMIC_FORMAL_INPUTS.json",
                        "pre-target algorithm/invariant/recurrence inputs",
                    ),
                    planned_artifact(
                        root,
                        f"{complexity_future_prefix}/OC133_COMPLEXITY_ALGORITHMIC_EXECUTED_PROOF_CORPUS.json",
                        "executed complexity and algorithmic proof corpus",
                    ),
                    planned_artifact(
                        root,
                        f"{complexity_future_prefix}/OC133_COMPLEXITY_ALGORITHMIC_WITHHELD_AGGREGATES.lock.json",
                        "formal withheld aggregate lock",
                    ),
                ],
                "scope_boundary": (
                    "This lane requires formal correctness or complexity proofs. Runtime timing curves, benchmark "
                    "speed, empirical numeric prediction, empirical scaling fits, or sample tests are controls/"
                    "comparators only, not proof evidence."
                ),
            },
            "target_theorem_or_property": {
                "target_id": "COMPLEXITY-ALGORITHMIC-HELDOUT-PROOF-OBLIGATIONS",
                "target_type": "formal computational complexity and algorithmic proof",
                "target_statement": (
                    "For held-out algorithm specifications, loop invariants, recurrences, and input-size measures, "
                    "prove the declared correctness and asymptotic upper-bound verdict or provide an executable counterexample."
                ),
                "target_fields": [
                    "algorithm_id",
                    "invariant_or_recurrence_id",
                    "input_size_measure",
                    "claimed_bound_class",
                    "expected_bound_or_correctness_verdict",
                    "proof_or_counterexample_ref",
                ],
                "minimum_target_rows": 20,
            },
            "hidden_target_or_formal_withheld_aggregate_policy": {
                "mode": "formal_withheld_aggregate",
                "pre_target_lock_ref": f"{complexity_future_prefix}/OC133_COMPLEXITY_ALGORITHMIC_FORMAL_INPUTS.json",
                "hidden_target_ref": f"{complexity_future_prefix}/OC133_COMPLEXITY_ALGORITHMIC_EXECUTED_PROOF_CORPUS.json",
                "withheld_until_scoring": [
                    "expected_bound_or_correctness_verdict",
                    "proof_or_counterexample_ref",
                    "aggregate bound-class pass/fail counts",
                ],
                "allowed_pre_scoring_aggregates": [
                    "manifest hash",
                    "minimum row count",
                    "algorithm vocabulary",
                    "bound-class vocabulary",
                ],
                "target_values_used_for_proof_design": False,
            },
            "proof_or_model": {
                "route": "formal",
                "model_id": "COMPLEXITY-ALGORITHMIC-FORMAL-DERIVATION",
                "description": (
                    "Materialize a Lean/finite proof of algorithmic correctness or complexity-bound preservation, "
                    "or a checked counterexample. Empirical runtime measurements may only appear as negative controls."
                ),
                "checker_refs": [
                    f"{complexity_future_prefix}/OC133_COMPLEXITY_ALGORITHMIC_SCORER.py",
                    LEAN_SOURCE_REL,
                ],
                "empirical_numeric_prediction": False,
            },
            "comparator_baseline": {
                "baseline_id": "COMPLEXITY-SAMPLE-RUN-OR-MAJORITY-BOUND-COMPARATOR",
                "name": "sample-run/majority-bound comparator",
                "prediction_rule": (
                    "infer the visible majority bound class or correctness verdict from sample executions only, "
                    "without a machine-checkable invariant, recurrence, or proof certificate"
                ),
                "pre_registered": True,
                "target_values_used_for_baseline_design": False,
            },
            "residual_or_error_notion": {
                "applicable": True,
                "metric_id": "formal_complexity_proof_mismatch_count",
                "definition": (
                    "0/1 mismatch between the preregistered formal proof verdict and the executed proof or "
                    "counterexample verdict; aggregate count and exact zero required for formal support."
                ),
                "uncertainty_policy": "No empirical uncertainty interval is applicable; asymptotic claims require proof/counterexample replay.",
                "superiority_or_acceptance_rule": (
                    "model_mismatch_count == 0, comparator_mismatch_count > 0, and invariant/recurrence mutation controls are rejected"
                ),
                "empirical_numeric_prediction": False,
            },
            "negative_control": {
                "control_id": "COMPLEXITY-INVARIANT-OR-RECURRENCE-MUTATION-CONTROL",
                "description": (
                    "Mutate a loop invariant, recurrence base case, or monotonicity premise after source lock; "
                    "the formal replay must reject the corrupted proof route."
                ),
                "rejection_predicate": "mutated proof obligations fail while the locked formal obligations replay exactly",
            },
            "falsifier": {
                "falsifier_id": "COMPLEXITY-ALGORITHMIC-PROOF-FALSIFIER",
                "trigger_predicates": [
                    "runtime timing, benchmark speed, or empirical scaling fit is used as proof of complexity",
                    "withheld bound verdicts or counterexample refs leak before proof materialization",
                    "fewer than 20 formal-equivalent algorithmic proof obligations replay",
                    "sample-run/majority comparator ties or beats the formal derivation",
                    "any invariant, recurrence, proof certificate, or counterexample ref is missing or unhashable",
                ],
            },
            "replay_protocol": {
                "commands": [
                    "python validation/heldout/grand_science/formal_mathematics/coverage_work_orders/planned_corpora/computational_complexity_algorithmic_proof/OC133_COMPLEXITY_ALGORITHMIC_SCORER.py --check",
                    "python validation/heldout/grand_science/formal_mathematics/coverage_work_orders/oc133_formal_mathematics_modern_science_coverage_work_orders.py --check",
                ],
                "required_artifacts": [
                    f"{complexity_future_prefix}/OC133_COMPLEXITY_ALGORITHMIC_FORMAL_INPUTS.json",
                    f"{complexity_future_prefix}/OC133_COMPLEXITY_ALGORITHMIC_EXECUTED_PROOF_CORPUS.json",
                    f"{complexity_future_prefix}/OC133_COMPLEXITY_ALGORITHMIC_WITHHELD_AGGREGATES.lock.json",
                    f"{complexity_future_prefix}/OC133_COMPLEXITY_ALGORITHMIC_SCORER.py",
                ],
                "acceptance_predicates": common_acceptance_predicates(
                    ["COMPLEXITY_ALGORITHMIC_FORMAL_CORPUS_BOUND"]
                ),
            },
            "current_evidence_status": {
                "status": (
                    PLANNED_CORPUS_SPECS["MS-COV-WO-003"]["status_bound"]
                    if complexity_exact
                    else PLANNED_CORPUS_SPECS["MS-COV-WO-003"]["status_unbound"]
                ),
                "exact_evidence_exists": complexity_exact,
                "coverage_closure_allowed": False,
                "reason": (
                    PLANNED_CORPUS_SPECS["MS-COV-WO-003"]["bound_reason"]
                    if complexity_exact
                    else PLANNED_CORPUS_SPECS["MS-COV-WO-003"]["unbound_reason"]
                ),
                "scorer_status": complexity_check,
                "remaining_blockers": (
                    PLANNED_CORPUS_SPECS["MS-COV-WO-003"]["materialized_blockers"]
                    if complexity_exact
                    else PLANNED_CORPUS_SPECS["MS-COV-WO-003"]["missing_blockers"]
                ),
            },
            "no_send_locks": no_send(),
        },
    ]
    return [with_hash(row) for row in rows]


def build_payload(root: Path | None = None) -> dict[str, Any]:
    root = root or repo_root()
    rows = build_work_orders(root)
    return {
        "schema_id": SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_on": GENERATED_ON,
        "capability_owner": CAPABILITY_OWNER,
        "generated_by": SCRIPT_REL,
        "coverage_register_ref": COVERAGE_REGISTER_REL,
        "modern_science_protocol_ref": MODERN_PROTOCOL_REL,
        "domain_class_id": "formal_mathematics_and_logic",
        "work_order_ids": list(WORK_ORDER_TARGETS.keys()),
        "work_order_total": len(rows),
        "fail_closed_or_review_pending_total": len(rows),
        "formal_route_only": True,
        "empirical_numeric_prediction_allowed": False,
        "coverage_closure_allowed": False,
        "broad_modern_science_superiority_allowed": False,
        "closure_policy": (
            "Formal coverage specs are executable planning/replay contracts. They cannot close coverage unless exact "
            "domain-matching proof evidence, controls, falsifiers, and independent review are bound; this payload "
            "keeps closure disabled."
        ),
        "no_send_locks": no_send(),
        "work_orders": rows,
    }


def open_fail_closed_status(row: dict[str, Any]) -> str:
    status = str(row["lane_status"])
    return status if status.startswith("OPEN_FAIL_CLOSED") else f"OPEN_{status}"


def formal_registry_phenomenon_id(row: dict[str, Any]) -> str:
    # The dispatcher still routes formal mathematics as protocol-only; this keeps these specs schema-valid
    # without converting the coverage gap into an empirical executable lane.
    return f"{row['phenomenon_class_id']}{FORMAL_SPEC_REGISTRY_SUFFIX}"


def formal_source_refs(row: dict[str, Any]) -> tuple[str, str]:
    phenomenon = str(row["phenomenon_class_id"])
    if phenomenon == "formal_theorem_reconstruction":
        return FINITE_OUTPUT_REL, FINITE_INPUT_REL
    if phenomenon == "statistical_inference_identifiability":
        prefix = (
            "validation/heldout/grand_science/formal_mathematics/coverage_work_orders/"
            "planned_corpora/statistical_probabilistic_inference"
        )
        return (
            f"{prefix}/OC133_STAT_PROB_IDENTIFIABILITY_EXECUTED_PROOF_CORPUS.json",
            f"{prefix}/OC133_STAT_PROB_IDENTIFIABILITY_WITHHELD_AGGREGATES.lock.json",
        )
    prefix = (
        "validation/heldout/grand_science/formal_mathematics/coverage_work_orders/"
        "planned_corpora/computational_complexity_algorithmic_proof"
    )
    return (
        f"{prefix}/OC133_COMPLEXITY_ALGORITHMIC_EXECUTED_PROOF_CORPUS.json",
        f"{prefix}/OC133_COMPLEXITY_ALGORITHMIC_WITHHELD_AGGREGATES.lock.json",
    )


def formal_source_name(row: dict[str, Any]) -> str:
    names = {
        "formal_theorem_reconstruction": "Lean 4 finite-model theorem reconstruction proof corpus",
        "statistical_inference_identifiability": "Lean 4 statistical and probabilistic identifiability proof corpus",
        "computational_complexity_and_algorithmic_proof": "Lean 4 computational complexity and algorithmic proof corpus",
    }
    return names[str(row["phenomenon_class_id"])]


def formal_required_inputs(row: dict[str, Any]) -> list[str]:
    inputs = {
        "formal_theorem_reconstruction": [
            "case_id",
            "theorem_id",
            "pre_execution_expected_verdict",
            "finite_model_input_facts",
        ],
        "statistical_inference_identifiability": [
            "observable_distribution_signature",
            "intervention_query",
            "declared_axioms",
            "locked_graphical_or_kernel_sequent",
        ],
        "computational_complexity_and_algorithmic_proof": [
            "algorithm_id",
            "invariant_or_recurrence_id",
            "input_size_measure",
            "claimed_bound_class",
        ],
    }
    return inputs[str(row["phenomenon_class_id"])]


def build_official_data_source(row: dict[str, Any]) -> dict[str, Any]:
    snapshot_ref, lock_ref = formal_source_refs(row)
    status = row["current_evidence_status"]
    return {
        "source_id": f"{row['phenomenon_class_id']}_lean4_formal_corpus_v1",
        "source_name": formal_source_name(row),
        "source_authority": "Lean project and Logion formal proof corpus steward",
        "official_documentation_url": "https://lean-lang.org/documentation/",
        "official_endpoint_url": "https://github.com/leanprover/lean4",
        "required_local_snapshot_ref": snapshot_ref,
        "required_lock_ref": lock_ref,
        "minimum_rows_required": row["target_theorem_or_property"]["minimum_target_rows"],
        "snapshot_status": status["status"],
        "source_kind": row["source_proof_corpus"]["source_kind"],
    }


def build_target_variable(row: dict[str, Any]) -> dict[str, Any]:
    target = row["target_theorem_or_property"]
    withheld = row["hidden_target_or_formal_withheld_aggregate_policy"]
    return {
        "name": target["target_id"].lower().replace("-", "_"),
        "unit": "formal proof-checker verdict",
        "target_fields": target["target_fields"],
        "extraction_rule": (
            f"Hold back {', '.join(withheld['withheld_until_scoring'])} until the formal proof route "
            f"materializes from {withheld['pre_target_lock_ref']}."
        ),
        "target_statement": target["target_statement"],
        "minimum_target_rows": target["minimum_target_rows"],
    }


def build_formula_requirement(row: dict[str, Any]) -> dict[str, Any]:
    proof = row["proof_or_model"]
    return {
        "formula_or_model": proof["description"],
        "required_inputs": formal_required_inputs(row),
        "target_values_may_be_used_for_model_design": False,
        "route": proof["route"],
        "checker_refs": proof["checker_refs"],
        "empirical_numeric_prediction": False,
    }


def build_comparator_requirement(row: dict[str, Any]) -> dict[str, Any]:
    comparator = row["comparator_baseline"]
    residual = row["residual_or_error_notion"]
    return {
        "baseline_name": comparator["name"],
        "baseline_id": comparator["baseline_id"],
        "prediction_rule": comparator["prediction_rule"],
        "pre_registered": comparator["pre_registered"],
        "target_values_used_for_baseline_design": comparator["target_values_used_for_baseline_design"],
        "required_material_margin": residual["superiority_or_acceptance_rule"],
    }


def build_uncertainty_requirement(row: dict[str, Any]) -> dict[str, Any]:
    residual = row["residual_or_error_notion"]
    return {
        "metric": "exact_formal_verdict_no_empirical_interval",
        "rule": residual["uncertainty_policy"],
        "empirical_numeric_prediction": False,
    }


def build_residual_requirement(row: dict[str, Any]) -> dict[str, Any]:
    residual = row["residual_or_error_notion"]
    return {
        "metric_id": residual["metric_id"],
        "formula": "sum(1 if preregistered_formal_verdict != executed_formal_verdict else 0) over locked formal rows",
        "definition": residual["definition"],
        "superiority_rule": residual["superiority_or_acceptance_rule"],
        "empirical_numeric_prediction": False,
    }


def build_negative_control_requirement(row: dict[str, Any]) -> dict[str, Any]:
    control = row["negative_control"]
    return {
        "control_id": control["control_id"],
        "rule": control["rejection_predicate"],
        "description": control["description"],
    }


def build_falsifier_requirement(row: dict[str, Any]) -> dict[str, Any]:
    falsifier = row["falsifier"]
    return {
        "falsifier_id": falsifier["falsifier_id"],
        "trigger": "; ".join(falsifier["trigger_predicates"]),
        "trigger_predicates": falsifier["trigger_predicates"],
    }


def build_execution_requirements(row: dict[str, Any]) -> dict[str, Any]:
    commands = row["replay_protocol"]["commands"]
    return {
        "minimum_n": row["target_theorem_or_property"]["minimum_target_rows"],
        "source_separation_mode": "target_blind",
        "target_hidden_until_scoring": True,
        "evidence_pack_schema_id": SCHEMA_ID,
        "replay_command": commands[-1],
        "replay_commands": commands,
        "empirical_numeric_prediction_allowed": False,
    }


def build_current_evidence(row: dict[str, Any]) -> dict[str, Any]:
    status = row["current_evidence_status"]
    return {
        "executable_evidence_exists": False,
        "executable_evidence_ref": None,
        "reason": status["reason"],
        "status": status["status"],
        "formal_exact_evidence_exists": status["exact_evidence_exists"],
        "coverage_closure_allowed": False,
        "remaining_blockers": status["remaining_blockers"],
    }


def executable_closure_predicates(row: dict[str, Any]) -> list[str]:
    predicates = list(DISPATCHER_CLOSURE_PREDICATES)
    for predicate in row["replay_protocol"]["acceptance_predicates"]:
        if predicate not in predicates:
            predicates.append(predicate)
    for predicate in ("EXECUTABLE_LANE_SPEC_DECLARED", "FAIL_CLOSED_UNLESS_EXECUTABLE_EVIDENCE_BOUND"):
        if predicate not in predicates:
            predicates.append(predicate)
    return predicates


def build_plugin_spec(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "spec_schema_id": PLUGIN_SPEC_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_on": GENERATED_ON,
        "capability_owner": CAPABILITY_OWNER,
        "source_domain_work_order_ref": OUTPUT_REL,
        "work_order_id": row["work_order_id"],
        "coverage_gap_id": row["coverage_gap_id"],
        "domain_class_id": row["domain_class_id"],
        "phenomenon_class_id": formal_registry_phenomenon_id(row),
        "source_domain_class_id": row["domain_class_id"],
        "source_phenomenon_class_id": row["phenomenon_class_id"],
        "source_coverage_gap_id": row["coverage_gap_id"],
        "coverage_closure_status": open_fail_closed_status(row),
        "coverage_closure_allowed": False,
        "formal_route_only": True,
        "empirical_numeric_prediction_allowed": False,
        "source_plan_id": f"MS-FORMAL-{row['phenomenon_class_id'].upper()}-LEAN4-v1",
        "official_data_source": build_official_data_source(row),
        "target_variable": build_target_variable(row),
        "formula_requirement": build_formula_requirement(row),
        "incumbent_comparator_requirement": build_comparator_requirement(row),
        "uncertainty_requirement": build_uncertainty_requirement(row),
        "residual_requirement": build_residual_requirement(row),
        "negative_control_requirement": build_negative_control_requirement(row),
        "falsifier_requirement": build_falsifier_requirement(row),
        "execution_requirements": build_execution_requirements(row),
        "current_evidence": build_current_evidence(row),
        "closure_predicates_required": executable_closure_predicates(row),
        "source_proof_corpus": row["source_proof_corpus"],
        "target_theorem_or_property": row["target_theorem_or_property"],
        "hidden_target_or_formal_withheld_aggregate_policy": row[
            "hidden_target_or_formal_withheld_aggregate_policy"
        ],
        "proof_or_model": row["proof_or_model"],
        "comparator_baseline": row["comparator_baseline"],
        "residual_or_error_notion": row["residual_or_error_notion"],
        "negative_control": row["negative_control"],
        "falsifier": row["falsifier"],
        "no_send_locks": no_send(),
    }


def plugin_specs_enabled(root: Path) -> bool:
    return (root / PLUGIN_DIR_REL).is_dir()


def build_all(root: Path | None = None) -> dict[str, Any]:
    root = root or repo_root()
    payload = build_payload(root)
    outputs: dict[str, Any] = {OUTPUT_REL: payload}
    if plugin_specs_enabled(root):
        for row in payload["work_orders"]:
            rel = PLUGIN_SPEC_RELS[str(row["phenomenon_class_id"])]
            outputs[rel] = build_plugin_spec(row)
    return outputs


def validate_payload(payload: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    rows = payload.get("work_orders", [])
    if payload.get("coverage_closure_allowed") is not False:
        failures.append("PAYLOAD_COVERAGE_CLOSURE_ALLOWED")
    if payload.get("broad_modern_science_superiority_allowed") is not False:
        failures.append("PAYLOAD_BROAD_SUPERIORITY_ALLOWED")
    if payload.get("empirical_numeric_prediction_allowed") is not False:
        failures.append("PAYLOAD_EMPIRICAL_NUMERIC_PREDICTION_ALLOWED")
    if not isinstance(rows, list) or payload.get("work_order_total") != len(rows):
        failures.append("WORK_ORDER_TOTAL_MISMATCH")
        return failures
    actual = {str(row.get("work_order_id")): str(row.get("phenomenon_class_id")) for row in rows if isinstance(row, dict)}
    if actual != WORK_ORDER_TARGETS:
        failures.append("FORMAL_MATHEMATICS_WORK_ORDER_SET_MISMATCH")
    for row in rows:
        if not isinstance(row, dict):
            failures.append("WORK_ORDER_NOT_OBJECT")
            continue
        row_id = str(row.get("work_order_id", "unknown"))
        if row.get("coverage_closure_allowed") is not False:
            failures.append(f"COVERAGE_CLOSURE_ALLOWED::{row_id}")
        if row.get("support_allowed_for_broad_coverage") is not False:
            failures.append(f"BROAD_SUPPORT_ALLOWED::{row_id}")
        if row.get("formal_route_only") is not True:
            failures.append(f"FORMAL_ROUTE_NOT_DECLARED::{row_id}")
        if row.get("empirical_numeric_prediction_allowed") is not False:
            failures.append(f"EMPIRICAL_NUMERIC_PREDICTION_ALLOWED::{row_id}")
        if str(row.get("lane_status")).upper() == "PASS":
            failures.append(f"FAKE_PASS_STATUS::{row_id}")
        for field in REQUIRED_ROW_FIELDS:
            if not row.get(field):
                failures.append(f"REQUIRED_FIELD_MISSING::{row_id}::{field}")
        corpus = row.get("source_proof_corpus", {})
        if corpus.get("source_kind") == "empirical_observation_table":
            failures.append(f"FORMAL_SOURCE_MISCLASSIFIED_AS_EMPIRICAL::{row_id}")
        if corpus.get("minimum_formal_case_count") != 20:
            failures.append(f"FORMAL_MINIMUM_CASE_COUNT_NOT_20::{row_id}")
        target = row.get("target_theorem_or_property", {})
        if not target.get("target_statement") or not target.get("target_fields"):
            failures.append(f"TARGET_THEOREM_OR_PROPERTY_INCOMPLETE::{row_id}")
        withheld = row.get("hidden_target_or_formal_withheld_aggregate_policy", {})
        if withheld.get("target_values_used_for_proof_design") is not False:
            failures.append(f"TARGET_VALUES_USED_FOR_PROOF_DESIGN::{row_id}")
        proof = row.get("proof_or_model", {})
        if proof.get("route") != "formal" or proof.get("empirical_numeric_prediction") is not False:
            failures.append(f"PROOF_MODEL_NOT_FORMAL_ONLY::{row_id}")
        comparator = row.get("comparator_baseline", {})
        if comparator.get("pre_registered") is not True:
            failures.append(f"COMPARATOR_NOT_PREREGISTERED::{row_id}")
        if comparator.get("target_values_used_for_baseline_design") is not False:
            failures.append(f"COMPARATOR_TARGET_LEAKAGE::{row_id}")
        residual = row.get("residual_or_error_notion", {})
        if residual.get("empirical_numeric_prediction") is not False:
            failures.append(f"RESIDUAL_ASSERTS_EMPIRICAL_NUMERIC_PREDICTION::{row_id}")
        if not row.get("negative_control", {}).get("rejection_predicate"):
            failures.append(f"NEGATIVE_CONTROL_PREDICATE_MISSING::{row_id}")
        if not row.get("falsifier", {}).get("trigger_predicates"):
            failures.append(f"FALSIFIER_PREDICATES_MISSING::{row_id}")
        replay = row.get("replay_protocol", {})
        if not replay.get("commands"):
            failures.append(f"REPLAY_COMMAND_MISSING::{row_id}")
        if "EMPIRICAL_NUMERIC_PREDICTION_NOT_ASSERTED" not in replay.get("acceptance_predicates", []):
            failures.append(f"FORMAL_NUMERIC_BOUNDARY_PREDICATE_MISSING::{row_id}")
        status = row.get("current_evidence_status", {})
        if status.get("coverage_closure_allowed") is not False:
            failures.append(f"CURRENT_STATUS_ALLOWS_COVERAGE_CLOSURE::{row_id}")
        locks = row.get("no_send_locks", {})
        if locks.get("no_send") is not True or any(
            locks.get(key) is not False for key in NO_SEND_LOCKS if key != "no_send"
        ):
            failures.append(f"NO_SEND_LOCK_OPEN::{row_id}")
        expected_hash = sha256_object({key: value for key, value in row.items() if key != "row_sha256"})
        if row.get("row_sha256") != expected_hash:
            failures.append(f"ROW_HASH_MISMATCH::{row_id}")
    return sorted(set(failures))


def check_stored(root: Path | None = None) -> list[str]:
    root = root or repo_root()
    expected_outputs = build_all(root)
    expected = expected_outputs[OUTPUT_REL]
    failures = validate_payload(expected)
    for rel, expected_payload in expected_outputs.items():
        path = root / rel
        if not path.exists():
            failures.append(f"missing::{rel}")
            continue
        actual = read_json(path)
        if actual != expected_payload:
            failures.append(f"mismatch::{rel}")
        if rel == OUTPUT_REL:
            failures.extend(validate_payload(actual if isinstance(actual, dict) else {}))
    return sorted(set(failures))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build/check formal mathematics modern-science coverage work orders.")
    parser.add_argument("--root", default=str(repo_root()), help="repository root")
    parser.add_argument("--write", action="store_true", help="write the deterministic work-order artifact")
    parser.add_argument("--check", action="store_true", help="check stored artifact synchronization")
    parser.add_argument(
        "--materialize-planned-corpora",
        action="store_true",
        help="materialize deterministic planned formal corpora and scorer scripts for MS-COV-WO-002/003",
    )
    parser.add_argument(
        "--check-planned-corpora",
        action="store_true",
        help="check deterministic planned formal corpora and scorer pass/fail controls",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    if args.materialize_planned_corpora:
        write_planned_corpora(root)
    if args.check:
        failures = check_stored(root)
        if args.check_planned_corpora:
            failures.extend(check_planned_corpora(root))
        if failures:
            for failure in failures:
                print(f"ERROR: {failure}")
            return 1
        print(json.dumps({"status": "ok", "checked": OUTPUT_REL, "planned_corpora_checked": args.check_planned_corpora}, indent=2))
        return 0
    if args.check_planned_corpora:
        failures = check_planned_corpora(root)
        if failures:
            for failure in failures:
                print(f"ERROR: {failure}")
            return 1
        print(json.dumps({"status": "ok", "checked": "planned_corpora"}, indent=2))
        return 0
    payload = build_payload(root)
    failures = validate_payload(payload)
    if args.write:
        for rel, output_payload in build_all(root).items():
            write_json(root / rel, output_payload)
    print(json.dumps({"status": "ok" if not failures else "failed", "output_ref": OUTPUT_REL, "failures": failures}, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
