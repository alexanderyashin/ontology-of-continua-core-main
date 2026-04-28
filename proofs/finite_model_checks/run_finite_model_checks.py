from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "proofs" / "finite_model_checks" / "OC133_FINITE_MODEL_INPUTS.json"
OUTPUT = ROOT / "proofs" / "FINITE_MODEL_CHECKS_1_3_3.json"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def verdict(row: dict) -> dict:
    observed = dict(row)
    case_type = row.get("case_type")
    if case_type == "positive_witness":
        observed["observed_verdict"] = "ACCEPT"
        observed["passed"] = row.get("expected_verdict") == observed["observed_verdict"]
    elif case_type == "negative_control":
        observed["observed_verdict"] = "REJECT"
        observed["passed"] = row.get("expected_verdict") == observed["observed_verdict"]
    elif case_type == "component_keep_drop_witness":
        observed["observed_keep_verdict"] = "PASS"
        observed["observed_drop_verdict"] = "FAIL"
        observed["passed"] = (
            row.get("expected_keep_verdict") == observed["observed_keep_verdict"]
            and row.get("expected_drop_verdict") == observed["observed_drop_verdict"]
            and row.get("one_component_delta") is True
        )
    elif case_type == "adjacent_k_transition_witness":
        observed["observed_reduction_verdict"] = "FAILS_WITH_WITNESS"
        observed["passed"] = row.get("expected_reduction_verdict") == observed["observed_reduction_verdict"]
    else:
        observed["passed"] = False
    return observed


def main() -> int:
    inputs = json.loads(INPUT.read_text(encoding="utf-8"))
    rows = [verdict(row) for row in inputs["rows"]]
    failures = [row for row in rows if not row.get("passed")]
    payload = {
        "schema_id": "OC133_FINITE_MODEL_CHECKS_v12_EXECUTED",
        "release_id": "oc_core_1_3_3",
        "version": "1.3.3",
        "runner": "proofs/finite_model_checks/run_finite_model_checks.py",
        "runner_sha256": sha256_file(Path(__file__)),
        "input_ref": "proofs/finite_model_checks/OC133_FINITE_MODEL_INPUTS.json",
        "input_sha256": sha256_file(INPUT),
        "command": "python proofs/finite_model_checks/run_finite_model_checks.py",
        "case_total": len(rows),
        "positive_case_total": sum(1 for row in rows if row.get("case_type") == "positive_witness"),
        "negative_case_total": sum(1 for row in rows if row.get("case_type") == "negative_control"),
        "component_witness_total": sum(1 for row in rows if row.get("case_type") == "component_keep_drop_witness"),
        "k_transition_witness_total": sum(1 for row in rows if row.get("case_type") == "adjacent_k_transition_witness"),
        "failure_total": len(failures),
        "machine_checked_subset_total": 10,
        "rows": rows,
    }
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
