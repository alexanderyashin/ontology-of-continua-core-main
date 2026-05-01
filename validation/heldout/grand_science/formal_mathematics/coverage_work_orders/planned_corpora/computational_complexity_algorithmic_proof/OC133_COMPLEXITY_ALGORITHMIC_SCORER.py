from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


CONFIG = {"corpus_key": "computational_complexity_algorithmic_proof", "executed_name": "OC133_COMPLEXITY_ALGORITHMIC_EXECUTED_PROOF_CORPUS.json", "expected_function": "complexity", "input_name": "OC133_COMPLEXITY_ALGORITHMIC_FORMAL_INPUTS.json", "lock_name": "OC133_COMPLEXITY_ALGORITHMIC_WITHHELD_AGGREGATES.lock.json", "minimum_rows": 20, "verdict_field": "formal_derivation_verdict"}


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def sha256_object(payload: Any) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def row_hash(row: dict[str, Any]) -> str:
    return sha256_object({key: value for key, value in row.items() if key != "row_sha256"})


def expected_stat_prob_verdict(row: dict[str, Any]) -> str:
    if str(row.get("graph_family")) in {"randomized_trial", "frontdoor_graph", "backdoor_adjustable", "instrumental_proxy"}:
        return "IDENTIFIABLE"
    return "NON_IDENTIFIABLE"


def expected_complexity_verdict(row: dict[str, Any]) -> str:
    derived_bounds = {
        "linear_scan": "O(n)",
        "divide_and_conquer": "O(n log n)",
        "binary_search": "O(log n)",
        "dynamic_programming_grid": "O(n^2)",
    }
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
            failures.append(f"COVERAGE_CLOSURE_ALLOWED::{name}")
        if payload.get("empirical_numeric_prediction_allowed") is not False:
            failures.append(f"EMPIRICAL_NUMERIC_PREDICTION_ALLOWED::{name}")
        if payload.get("broad_modern_science_superiority_allowed") is not False:
            failures.append(f"BROAD_SUPERIORITY_ALLOWED::{name}")
    forbidden = {
        CONFIG["verdict_field"],
        "expected_identifiability_verdict",
        "expected_bound_or_correctness_verdict",
        "proof_ref",
        "countermodel_ref",
        "proof_or_counterexample_ref",
        "formal_verdict",
        "observed_verdict",
        "passed",
    }
    leak = contains_forbidden_key(input_rows, forbidden)
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
        expected = expected_verdict(input_row)
        if executed_row.get(CONFIG["verdict_field"]) != expected:
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
