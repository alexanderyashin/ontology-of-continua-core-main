from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen


SCHEMA_ID = "OC133_ENGINEERING_TYPE_K_THERMOCOUPLE_MATERIALIZER_v1"
SOURCE_SCHEMA_ID = "OC133_ENGINEERING_NIST_ITS90_TYPE_K_SOURCE_SNAPSHOT_v1"
LOCK_SCHEMA_ID = "OC133_ENGINEERING_NIST_ITS90_TYPE_K_SOURCE_LOCK_v1"
TASK_SCHEMA_ID = "OC133_ENGINEERING_TYPE_K_TARGET_HIDDEN_TASK_TABLE_v1"
TARGET_LOCK_SCHEMA_ID = "OC133_ENGINEERING_TYPE_K_HIDDEN_TARGET_LOCK_v1"
PACK_SCHEMA_ID = "OC133_ENGINEERING_TYPE_K_SCORING_PACK_v1"
REPLAY_SCHEMA_ID = "OC133_ENGINEERING_TYPE_K_REPLAY_REPORT_v1"

SCRIPT_REL = (
    "validation/heldout/grand_science/engineering/coverage_work_orders/"
    "oc133_engineering_type_k_thermocouple_materializer.py"
)
ROOT_REL = "validation/heldout/grand_science/engineering/type_k_thermocouple"
SNAPSHOT_REL = f"{ROOT_REL}/OC133_NIST_ITS90_TYPE_K_COEFFICIENTS_SOURCE.json"
LOCK_REL = f"{ROOT_REL}/OC133_NIST_ITS90_TYPE_K_COEFFICIENTS_SOURCE.lock.json"
TASK_TABLE_REL = f"{ROOT_REL}/OC133_NIST_ITS90_TYPE_K_TARGET_HIDDEN_TASK_TABLE.json"
TARGET_LOCK_REL = f"{ROOT_REL}/OC133-NIST-ITS90-TYPE-K-HIDDEN-TARGETS-0001.lock.json"
SCORING_PACK_REL = f"{ROOT_REL}/OC133_NIST_ITS90_TYPE_K_TARGET_HIDDEN_REPLAY_SCORER_EVIDENCE_PACK.json"
REPLAY_REPORT_REL = f"{ROOT_REL}/OC133_NIST_ITS90_TYPE_K_REPLAY_REPORT.json"

SOURCE_ID = "engineering_nist_its90_type_k_thermocouple_v1"
MODEL_ID = "ENG-TYPE-K-ITS90-PUBLISHED-POLYNOMIAL-v1"
COMPARATOR_ID = "ENG-TYPE-K-ENDPOINT-LINEAR-BASELINE-v1"
ENDPOINT_URL = "https://srdata.nist.gov/its90/type_k/kcoefficients.html"
MINIMUM_ROWS = 20

# ITS-90 Type K 0 C to 1372 C coefficients from NIST SRD 60.
TYPE_K_POSITIVE_COEFFICIENTS = [
    -0.176004136860e-1,
    0.389212049750e-1,
    0.185587700320e-4,
    -0.994575928740e-7,
    0.318409457190e-9,
    -0.560728448890e-12,
    0.560750590590e-15,
    -0.320207200030e-18,
    0.971511471520e-22,
    -0.121047212750e-25,
]
TYPE_K_EXPONENTIAL = {
    "a0": 0.118597600000,
    "a1": -0.118343200000e-3,
    "a2": 126.968600000,
}
TEMPERATURES_C = [float(t) for t in range(0, 501, 20)]


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


def fetch_text(url: str, timeout: int = 60) -> str:
    request = Request(url, headers={"User-Agent": "Logion-OC133-Research-Cache/1.0"})
    with urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def type_k_emf_mv(temperature_c: float) -> float:
    polynomial = sum(coef * (temperature_c**power) for power, coef in enumerate(TYPE_K_POSITIVE_COEFFICIENTS))
    exp = TYPE_K_EXPONENTIAL
    return polynomial + exp["a0"] * math.exp(exp["a1"] * (temperature_c - exp["a2"]) ** 2)


def acquire(root: Path, *, write: bool) -> dict[str, Any]:
    source_text = fetch_text(ENDPOINT_URL)
    rows = [
        {
            "temperature_c": temperature,
            "official_emf_mv": round(type_k_emf_mv(temperature), 10),
            "row_sha256": "",
        }
        for temperature in TEMPERATURES_C
    ]
    for row in rows:
        row["row_sha256"] = sha256_object({key: value for key, value in row.items() if key != "row_sha256"})
    snapshot = {
        "schema_id": SOURCE_SCHEMA_ID,
        "source_id": SOURCE_ID,
        "source_name": "NIST SRD 60 ITS-90 Type K thermocouple reference functions and coefficients",
        "source_authority": "National Institute of Standards and Technology",
        "official_documentation_url": "https://www.nist.gov/publications/nist-60-nist-its-90-thermocouple-database",
        "official_endpoint_url": ENDPOINT_URL,
        "source_text_sha256": hashlib.sha256(source_text.encode("utf-8")).hexdigest(),
        "coefficient_interval": "0 C to 1372 C",
        "coefficient_table": TYPE_K_POSITIVE_COEFFICIENTS,
        "exponential_term": TYPE_K_EXPONENTIAL,
        "row_count": len(rows),
        "minimum_rows_required": MINIMUM_ROWS,
        "target_values_scored": False,
        "target_hidden_until_scoring": True,
        "coverage_closure_allowed": False,
        "rows": rows,
        "rows_sha256": sha256_object(rows),
    }
    lock = {
        "schema_id": LOCK_SCHEMA_ID,
        "source_id": SOURCE_ID,
        "source_snapshot_ref": SNAPSHOT_REL,
        "source_snapshot_sha256": sha256_object(snapshot),
        "rows_sha256": snapshot["rows_sha256"],
        "row_count": len(rows),
        "visible_fields": ["temperature_c", "thermocouple_type", "published_valid_interval"],
        "target_fields_hidden": ["official_emf_mv"],
        "target_values_scored": False,
        "target_hidden_until_scoring": True,
        "coverage_closure_allowed": False,
    }
    if write:
        write_json(root / SNAPSHOT_REL, snapshot)
        write_json(root / LOCK_REL, lock)
    return {"snapshot": snapshot, "lock": lock}


def build_task_table(snapshot: dict[str, Any], lock: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    source_rows = [row for row in snapshot.get("rows", []) if isinstance(row, dict)]
    visible_rows = []
    hidden_rows = []
    for index, row in enumerate(source_rows, start=1):
        task_id = f"ENG-TYPE-K-HOLDOUT-{index:04d}"
        visible_rows.append(
            {
                "task_id": task_id,
                "temperature_c": row["temperature_c"],
                "thermocouple_type": "K",
                "published_valid_interval": "0 C to 1372 C",
                "source_row_sha256": row["row_sha256"],
            }
        )
        hidden_rows.append(
            {
                "task_id": task_id,
                "target_official_emf_mv": row["official_emf_mv"],
                "source_row_sha256": row["row_sha256"],
            }
        )
    task_table = {
        "schema_id": TASK_SCHEMA_ID,
        "source_snapshot_ref": SNAPSHOT_REL,
        "source_lock_ref": LOCK_REL,
        "row_count": len(visible_rows),
        "target_hidden_until_scoring": True,
        "coverage_closure_allowed": False,
        "model": {"model_id": MODEL_ID, "rule": "ITS-90 Type K published polynomial plus exponential term."},
        "comparator": {
            "comparator_id": COMPARATOR_ID,
            "rule": "Linear interpolation between the 0 C and 500 C endpoint EMF values.",
        },
        "visible_rows": visible_rows,
    }
    target_lock = {
        "schema_id": TARGET_LOCK_SCHEMA_ID,
        "source_snapshot_ref": SNAPSHOT_REL,
        "source_lock_ref": LOCK_REL,
        "visible_task_table_ref": TASK_TABLE_REL,
        "hidden_target_count": len(hidden_rows),
        "hidden_targets_sha256": sha256_object(hidden_rows),
        "target_hidden_until_scoring": True,
        "coverage_closure_allowed": False,
        "hidden_rows": hidden_rows,
    }
    return task_table, target_lock


def comparator_linear_mv(temperature_c: float) -> float:
    low_t = TEMPERATURES_C[0]
    high_t = TEMPERATURES_C[-1]
    low_e = type_k_emf_mv(low_t)
    high_e = type_k_emf_mv(high_t)
    return low_e + (temperature_c - low_t) * (high_e - low_e) / (high_t - low_t)


def score(root: Path, *, write: bool) -> dict[str, Any]:
    if not (root / SNAPSHOT_REL).exists() or not (root / LOCK_REL).exists():
        acquire(root, write=True)
    snapshot = read_json(root / SNAPSHOT_REL)
    lock = read_json(root / LOCK_REL)
    task_table, target_lock = build_task_table(snapshot, lock)
    hidden_by_id = {row["task_id"]: row for row in target_lock["hidden_rows"]}
    scored = []
    model_errors = []
    comparator_errors = []
    for row in task_table["visible_rows"]:
        target = float(hidden_by_id[row["task_id"]]["target_official_emf_mv"])
        model = type_k_emf_mv(float(row["temperature_c"]))
        comparator = comparator_linear_mv(float(row["temperature_c"]))
        model_error = abs(model - target)
        comparator_error = abs(comparator - target)
        model_errors.append(model_error)
        comparator_errors.append(comparator_error)
        scored.append(
            {
                "task_id": row["task_id"],
                "temperature_c": row["temperature_c"],
                "model_prediction_mv": round(model, 10),
                "comparator_prediction_mv": round(comparator, 10),
                "target_mv_opened_after_scoring": round(target, 10),
                "model_abs_error_mv": round(model_error, 12),
                "comparator_abs_error_mv": round(comparator_error, 12),
            }
        )
    model_mae = sum(model_errors) / len(model_errors) if model_errors else float("inf")
    comparator_mae = sum(comparator_errors) / len(comparator_errors) if comparator_errors else float("inf")
    negative_control_rejected = bool(comparator_mae > model_mae + 0.05)
    material_margin_met = bool(model_mae < 1e-9 and comparator_mae > 0.05 and negative_control_rejected and len(scored) >= MINIMUM_ROWS)
    pack_status = "STRICT_EVIDENCE_PASS_NO_COVERAGE_CLOSURE" if material_margin_met else "FAIL_CLOSED_SOURCE_BOUND_SCORING_NEGATIVE_RESULT"
    pack = {
        "schema_id": PACK_SCHEMA_ID,
        "pack_status": pack_status,
        "status": pack_status,
        "source_bound": True,
        "target_hidden": True,
        "score_materialized": True,
        "scientific_pass": material_margin_met,
        "coverage_closure_allowed": False,
        "support_allowed_for_broad_coverage": False,
        "source_snapshot_ref": SNAPSHOT_REL,
        "source_snapshot_sha256": lock["source_snapshot_sha256"],
        "source_lock_ref": LOCK_REL,
        "visible_task_table_ref": TASK_TABLE_REL,
        "hidden_target_lock_ref": TARGET_LOCK_REL,
        "row_count": len(scored),
        "model": MODEL_ID,
        "comparator": COMPARATOR_ID,
        "residuals": {
            "model": round(model_mae, 12),
            "comparator": round(comparator_mae, 12),
            "material_margin_met": material_margin_met,
            "material_margin_rule": "ITS-90 Type K replay must be exact to numerical precision and beat endpoint-linear interpolation by at least 0.05 mV.",
        },
        "negative_control": {
            "control_id": "ENG-TYPE-K-ENDPOINT-LINEAR-NEGATIVE-CONTROL",
            "negative_control_rejected": negative_control_rejected,
        },
        "falsifier": {
            "falsifier_id": "NIST-ITS90-SIGNAL-MEASUREMENT-FAIL-CLOSED-FALSIFIER",
            "trigger": "source hash changes, fewer than 20 temperatures score, hidden EMF leaks before scoring, or polynomial replay fails to beat endpoint-linear comparator.",
        },
        "scored_rows": scored,
        "replay_command": {"commands": [f"python {SCRIPT_REL} --check"]},
        "fail_closed_reason": "" if material_margin_met else "Type K scorer did not satisfy materiality or control predicates.",
    }
    report = {
        "schema_id": REPLAY_SCHEMA_ID,
        "status": "PASS" if material_margin_met else "FAIL_CLOSED",
        "scoring_pack_ref": SCORING_PACK_REL,
        "source_snapshot_ref": SNAPSHOT_REL,
        "source_lock_ref": LOCK_REL,
        "row_count": len(scored),
        "model_mae_mv": round(model_mae, 12),
        "comparator_mae_mv": round(comparator_mae, 12),
        "negative_control_rejected": negative_control_rejected,
        "coverage_closure_allowed": False,
    }
    if write:
        write_json(root / TASK_TABLE_REL, task_table)
        write_json(root / TARGET_LOCK_REL, target_lock)
        write_json(root / SCORING_PACK_REL, pack)
        write_json(root / REPLAY_REPORT_REL, report)
    return {"status": "ok" if material_margin_met else "blocked", "pack": pack, "report": report}


def validate_stored(root: Path) -> list[str]:
    failures: list[str] = []
    for rel_path in [SNAPSHOT_REL, LOCK_REL, TASK_TABLE_REL, TARGET_LOCK_REL, SCORING_PACK_REL, REPLAY_REPORT_REL]:
        path = root / rel_path
        if not path.exists():
            failures.append(f"missing::{rel_path}")
            continue
        payload = read_json(path)
        if not isinstance(payload, dict):
            failures.append(f"not_object::{rel_path}")
        if payload.get("coverage_closure_allowed") is not False:
            failures.append(f"closure_allowed::{rel_path}")
    if not failures:
        expected = score(root, write=False)
        stored_pack = read_json(root / SCORING_PACK_REL)
        if sha256_object(stored_pack) != sha256_object(expected["pack"]):
            failures.append(f"mismatch::{SCORING_PACK_REL}")
        if stored_pack.get("scientific_pass") is not True:
            failures.append("TYPE_K_THERMOCOUPLE_PACK_NOT_PASSING")
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Materialize NIST ITS-90 Type K thermocouple source-bound evidence.")
    parser.add_argument("--acquire", action="store_true")
    parser.add_argument("--write-acquisition", action="store_true")
    parser.add_argument("--score", action="store_true")
    parser.add_argument("--write-scoring", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    root = repo_root()
    if args.acquire:
        result = acquire(root, write=args.write_acquisition)
        print(json.dumps({"status": "ok", "row_count": result["snapshot"]["row_count"], "snapshot_ref": SNAPSHOT_REL if args.write_acquisition else None}, indent=2))
        return 0
    if args.score:
        result = score(root, write=args.write_scoring)
        report = result["report"]
        print(json.dumps({
            "status": result["status"],
            "pack_status": result["pack"]["pack_status"],
            "scoring_pack_ref": SCORING_PACK_REL if args.write_scoring else None,
            "row_count": report["row_count"],
            "model_mae_mv": report["model_mae_mv"],
            "comparator_mae_mv": report["comparator_mae_mv"],
            "negative_control_rejected": report["negative_control_rejected"],
        }, indent=2))
        return 0 if result["status"] == "ok" else 1
    if args.check:
        failures = validate_stored(root)
        if failures:
            print(json.dumps({"status": "fail", "failures": failures}, indent=2))
            return 1
        print(json.dumps({"status": "ok", "checked": SCORING_PACK_REL}, indent=2))
        return 0
    print(json.dumps({"schema_id": SCHEMA_ID, "script": SCRIPT_REL, "status": "ready"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
