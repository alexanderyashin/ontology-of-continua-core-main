from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen


SCHEMA_ID = "OC133_PHYSICS_JPL_HORIZONS_DYNAMICS_MATERIALIZER_v1"
SOURCE_SCHEMA_ID = "OC133_PHYSICS_JPL_HORIZONS_SOURCE_SNAPSHOT_v1"
LOCK_SCHEMA_ID = "OC133_PHYSICS_JPL_HORIZONS_SOURCE_LOCK_v1"
TASK_SCHEMA_ID = "OC133_PHYSICS_JPL_HORIZONS_TARGET_HIDDEN_TASK_TABLE_v1"
TARGET_LOCK_SCHEMA_ID = "OC133_PHYSICS_JPL_HORIZONS_HIDDEN_TARGET_LOCK_v1"
PACK_SCHEMA_ID = "OC133_PHYSICS_JPL_HORIZONS_DYNAMICS_SCORING_PACK_v1"
REPLAY_SCHEMA_ID = "OC133_PHYSICS_JPL_HORIZONS_DYNAMICS_REPLAY_REPORT_v1"

SCRIPT_REL = (
    "validation/heldout/grand_science/physics_chemistry/dynamics_jpl_horizons/"
    "oc133_physics_jpl_horizons_dynamics_materializer.py"
)
SNAPSHOT_REL = (
    "validation/heldout/grand_science/physics_chemistry/dynamics_jpl_horizons/"
    "OC133_PHYSICS_JPL_HORIZONS_EARTH_SUN_VECTORS.json"
)
LOCK_REL = (
    "validation/heldout/grand_science/physics_chemistry/dynamics_jpl_horizons/"
    "OC133_PHYSICS_JPL_HORIZONS_EARTH_SUN_VECTORS.lock.json"
)
TASK_TABLE_REL = (
    "validation/heldout/grand_science/physics_chemistry/dynamics_jpl_horizons/"
    "OC133_PHYSICS_JPL_HORIZONS_TARGET_HIDDEN_TASK_TABLE.json"
)
TARGET_LOCK_REL = (
    "validation/heldout/grand_science/physics_chemistry/dynamics_jpl_horizons/"
    "OC133-PHYSICS-JPL-HORIZONS-HIDDEN-TARGETS-0001.lock.json"
)
SCORING_PACK_REL = (
    "validation/heldout/grand_science/physics_chemistry/dynamics_jpl_horizons/"
    "OC133_PHYSICS_JPL_HORIZONS_DYNAMICS_TARGET_HIDDEN_REPLAY_SCORER_EVIDENCE_PACK.json"
)
REPLAY_REPORT_REL = (
    "validation/heldout/grand_science/physics_chemistry/dynamics_jpl_horizons/"
    "OC133_PHYSICS_JPL_HORIZONS_DYNAMICS_REPLAY_REPORT.json"
)

SOURCE_ID = "physics_jpl_horizons_state_vectors_earth_sun_v1"
MODEL_ID = "PHYS-DYNAMICS-TWO-BODY-VELOCITY-VERLET-v1"
COMPARATOR_ID = "PHYS-DYNAMICS-CONSTANT-VELOCITY-CARTESIAN-BASELINE-v1"
SUN_GM_KM3_S2 = 132712440041.93938
SECONDS_PER_DAY = 86400.0
MINIMUM_ROWS = 20
ENDPOINT_URL = (
    "https://ssd.jpl.nasa.gov/api/horizons.api?format=json&COMMAND='399'&OBJ_DATA='NO'"
    "&MAKE_EPHEM='YES'&EPHEM_TYPE='VECTORS'&CENTER='500@10'&START_TIME='2026-Jan-01'"
    "&STOP_TIME='2026-Jan-25'&STEP_SIZE='1%20d'&VEC_TABLE='3'&OUT_UNITS='KM-S'&CSV_FORMAT='YES'"
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


def fetch_json(url: str, timeout: int = 90) -> Any:
    request = Request(url, headers={"User-Agent": "OC research pipeline-OC133-Research-Cache/1.0"})
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def parse_horizons_result(result: str) -> list[dict[str, Any]]:
    if "$$SOE" not in result or "$$EOE" not in result:
        return []
    block = result[result.index("$$SOE") + len("$$SOE") : result.index("$$EOE")]
    rows: list[dict[str, Any]] = []
    for line in block.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = [part.strip() for part in line.split(",")]
        if len(parts) < 8:
            continue
        try:
            jd = float(parts[0])
            values = [float(part) for part in parts[2:8]]
        except ValueError:
            continue
        row = {
            "julian_day_tdb": jd,
            "calendar_tdb": parts[1],
            "X_km": values[0],
            "Y_km": values[1],
            "Z_km": values[2],
            "VX_km_s": values[3],
            "VY_km_s": values[4],
            "VZ_km_s": values[5],
        }
        row["row_sha256"] = sha256_object(row)
        rows.append(row)
    return rows


def acquire(root: Path, *, write: bool) -> dict[str, Any]:
    raw = fetch_json(ENDPOINT_URL)
    result = raw.get("result") if isinstance(raw, dict) else ""
    rows = parse_horizons_result(str(result))
    snapshot = {
        "schema_id": SOURCE_SCHEMA_ID,
        "source_id": SOURCE_ID,
        "source_name": "NASA/JPL Solar System Dynamics HORIZONS Earth-Sun vector ephemerides",
        "source_authority": "NASA Jet Propulsion Laboratory Solar System Dynamics",
        "official_documentation_url": "https://ssd-api.jpl.nasa.gov/doc/horizons.html",
        "official_endpoint_url": ENDPOINT_URL,
        "row_count": len(rows),
        "minimum_rows_required": MINIMUM_ROWS + 1,
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
        "visible_fields": ["prior_epoch_XYZ_VXYZ", "delta_t_seconds", "solar_GM_km3_s2"],
        "target_fields_hidden": ["next_epoch_XYZ_VXYZ"],
        "target_values_scored": False,
        "target_hidden_until_scoring": True,
        "coverage_closure_allowed": False,
    }
    if write:
        write_json(root / SNAPSHOT_REL, snapshot)
        write_json(root / LOCK_REL, lock)
    return {"snapshot": snapshot, "lock": lock}


def acceleration(r: list[float]) -> list[float]:
    radius = math.sqrt(sum(component * component for component in r))
    return [-SUN_GM_KM3_S2 * component / (radius**3) for component in r]


def velocity_verlet(r: list[float], v: list[float], dt: float) -> tuple[list[float], list[float]]:
    a0 = acceleration(r)
    r1 = [r[i] + v[i] * dt + 0.5 * a0[i] * dt * dt for i in range(3)]
    a1 = acceleration(r1)
    v1 = [v[i] + 0.5 * (a0[i] + a1[i]) * dt for i in range(3)]
    return r1, v1


def vector_rmse(predicted: list[float], observed: list[float]) -> float:
    return math.sqrt(sum((predicted[i] - observed[i]) ** 2 for i in range(len(observed))) / len(observed))


def build_task_table(snapshot: dict[str, Any], lock: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    rows = [row for row in snapshot.get("rows", []) if isinstance(row, dict)]
    visible_rows = []
    hidden_rows = []
    for index in range(len(rows) - 1):
        current = rows[index]
        target = rows[index + 1]
        task_id = f"PHYS-JPL-HORIZONS-DYNAMICS-HOLDOUT-{index + 1:04d}"
        dt = (float(target["julian_day_tdb"]) - float(current["julian_day_tdb"])) * SECONDS_PER_DAY
        visible_rows.append(
            {
                "task_id": task_id,
                "source_row_sha256": current["row_sha256"],
                "target_source_row_sha256": target["row_sha256"],
                "epoch_tdb": current["calendar_tdb"],
                "next_epoch_tdb": target["calendar_tdb"],
                "delta_t_seconds": dt,
                "solar_GM_km3_s2": SUN_GM_KM3_S2,
                "r_km": [current["X_km"], current["Y_km"], current["Z_km"]],
                "v_km_s": [current["VX_km_s"], current["VY_km_s"], current["VZ_km_s"]],
            }
        )
        hidden_rows.append(
            {
                "task_id": task_id,
                "target_r_km": [target["X_km"], target["Y_km"], target["Z_km"]],
                "target_v_km_s": [target["VX_km_s"], target["VY_km_s"], target["VZ_km_s"]],
                "target_source_row_sha256": target["row_sha256"],
            }
        )
    task_table = {
        "schema_id": TASK_SCHEMA_ID,
        "source_snapshot_ref": SNAPSHOT_REL,
        "source_lock_ref": LOCK_REL,
        "row_count": len(visible_rows),
        "target_hidden_until_scoring": True,
        "coverage_closure_allowed": False,
        "model": {
            "model_id": MODEL_ID,
            "rule": "Velocity-Verlet two-body propagation from prior heliocentric state using fixed solar GM and one-day dt.",
        },
        "comparator": {
            "comparator_id": COMPARATOR_ID,
            "rule": "Cartesian constant-velocity extrapolation from the same prior state.",
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
        hidden = hidden_by_id[row["task_id"]]
        target_vector = [*hidden["target_r_km"], *hidden["target_v_km_s"]]
        model_r, model_v = velocity_verlet(row["r_km"], row["v_km_s"], float(row["delta_t_seconds"]))
        comparator_r = [row["r_km"][i] + row["v_km_s"][i] * float(row["delta_t_seconds"]) for i in range(3)]
        comparator_v = list(row["v_km_s"])
        model_vector = [*model_r, *model_v]
        comparator_vector = [*comparator_r, *comparator_v]
        model_error = vector_rmse(model_vector, target_vector)
        comparator_error = vector_rmse(comparator_vector, target_vector)
        model_errors.append(model_error)
        comparator_errors.append(comparator_error)
        scored.append(
            {
                "task_id": row["task_id"],
                "epoch_tdb": row["epoch_tdb"],
                "next_epoch_tdb": row["next_epoch_tdb"],
                "model_vector_rmse": round(model_error, 8),
                "comparator_vector_rmse": round(comparator_error, 8),
            }
        )
    model_rmse = sum(model_errors) / len(model_errors) if model_errors else float("inf")
    comparator_rmse = sum(comparator_errors) / len(comparator_errors) if comparator_errors else float("inf")
    reversed_targets = list(reversed(target_lock["hidden_rows"]))
    shuffled_errors = []
    for index, row in enumerate(task_table["visible_rows"]):
        hidden = reversed_targets[index]
        target_vector = [*hidden["target_r_km"], *hidden["target_v_km_s"]]
        model_r, model_v = velocity_verlet(row["r_km"], row["v_km_s"], float(row["delta_t_seconds"]))
        shuffled_errors.append(vector_rmse([*model_r, *model_v], target_vector))
    shuffled_rmse = sum(shuffled_errors) / len(shuffled_errors) if shuffled_errors else 0.0
    negative_control_rejected = bool(shuffled_rmse > model_rmse * 10)
    material_margin_met = bool(model_rmse < comparator_rmse and negative_control_rejected and len(scored) >= MINIMUM_ROWS)
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
            "model": round(model_rmse, 8),
            "comparator": round(comparator_rmse, 8),
            "material_margin_met": material_margin_met,
            "material_margin_rule": "Two-body velocity-Verlet vector RMSE must beat constant-velocity extrapolation and shuffled-target control must fail.",
        },
        "negative_control": {
            "control_id": "PHYS-JPL-HORIZONS-TARGET-REVERSAL-CONTROL",
            "shuffled_model_vector_rmse": round(shuffled_rmse, 8),
            "negative_control_rejected": negative_control_rejected,
        },
        "falsifier": {
            "falsifier_id": "PHYS-DYNAMICS-HORIZONS-STATE-FALSIFIER",
            "trigger": "source hash changes, fewer than 20 hidden epochs score, next state leaks before scoring, or two-body residual does not beat constant-velocity comparator.",
        },
        "scored_rows": scored,
        "replay_command": {"commands": [f"python {SCRIPT_REL} --check"]},
        "fail_closed_reason": "" if material_margin_met else "Dynamics scorer did not satisfy materiality or control predicates.",
    }
    report = {
        "schema_id": REPLAY_SCHEMA_ID,
        "status": "PASS" if material_margin_met else "FAIL_CLOSED",
        "scoring_pack_ref": SCORING_PACK_REL,
        "source_snapshot_ref": SNAPSHOT_REL,
        "source_lock_ref": LOCK_REL,
        "row_count": len(scored),
        "model_vector_rmse": round(model_rmse, 8),
        "comparator_vector_rmse": round(comparator_rmse, 8),
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
            failures.append("JPL_HORIZONS_DYNAMICS_PACK_NOT_PASSING")
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Materialize NASA/JPL HORIZONS source-bound dynamics coverage evidence.")
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
            "model_vector_rmse": report["model_vector_rmse"],
            "comparator_vector_rmse": report["comparator_vector_rmse"],
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
