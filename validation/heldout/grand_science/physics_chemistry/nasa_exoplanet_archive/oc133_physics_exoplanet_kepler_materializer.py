from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
from pathlib import Path
from typing import Any
from urllib.parse import quote
from urllib.request import Request, urlopen


SCHEMA_ID = "OC133_PHYSICS_EXOPLANET_KEPLER_MATERIALIZER_v1"
SOURCE_SCHEMA_ID = "OC133_PHYSICS_EXOPLANET_PS_COMPOSITE_SOURCE_SNAPSHOT_v1"
LOCK_SCHEMA_ID = "OC133_PHYSICS_EXOPLANET_PS_COMPOSITE_SOURCE_LOCK_v1"
TASK_SCHEMA_ID = "OC133_PHYSICS_EXOPLANET_KEPLER_TARGET_HIDDEN_TASK_TABLE_v1"
TARGET_LOCK_SCHEMA_ID = "OC133_PHYSICS_EXOPLANET_KEPLER_HIDDEN_TARGET_LOCK_v1"
PACK_SCHEMA_ID = "OC133_PHYSICS_EXOPLANET_KEPLER_SCORING_PACK_v1"
REPLAY_SCHEMA_ID = "OC133_PHYSICS_EXOPLANET_KEPLER_REPLAY_REPORT_v1"

SCRIPT_REL = (
    "validation/heldout/grand_science/physics_chemistry/nasa_exoplanet_archive/"
    "oc133_physics_exoplanet_kepler_materializer.py"
)
SNAPSHOT_REL = (
    "validation/heldout/grand_science/physics_chemistry/nasa_exoplanet_archive/"
    "OC133_NASA_EXOPLANET_PS_COMPOSITE_KEPLER.json"
)
LOCK_REL = (
    "validation/heldout/grand_science/physics_chemistry/nasa_exoplanet_archive/"
    "OC133_NASA_EXOPLANET_PS_COMPOSITE_KEPLER.lock.json"
)
TASK_TABLE_REL = (
    "validation/heldout/grand_science/physics_chemistry/nasa_exoplanet_archive/"
    "OC133_NASA_EXOPLANET_KEPLER_TARGET_HIDDEN_TASK_TABLE.json"
)
TARGET_LOCK_REL = (
    "validation/heldout/grand_science/physics_chemistry/nasa_exoplanet_archive/"
    "OC133-NASA-EXOPLANET-KEPLER-HIDDEN-TARGETS-0001.lock.json"
)
SCORING_PACK_REL = (
    "validation/heldout/grand_science/physics_chemistry/nasa_exoplanet_archive/"
    "OC133_NASA_EXOPLANET_KEPLER_TARGET_HIDDEN_REPLAY_SCORER_EVIDENCE_PACK.json"
)
REPLAY_REPORT_REL = (
    "validation/heldout/grand_science/physics_chemistry/nasa_exoplanet_archive/"
    "OC133_NASA_EXOPLANET_KEPLER_REPLAY_REPORT.json"
)

SOURCE_ID = "physics_nasa_exoplanet_archive_pscomppars_kepler_v1"
MODEL_ID = "PHYS-EXOPLANET-KEPLER-THIRD-LAW-SMA-v1"
COMPARATOR_ID = "PHYS-EXOPLANET-MEDIAN-STELLAR-MASS-KEPLER-BASELINE-v1"
EARTH_YEAR_DAYS = 365.2568983
MINIMUM_ROWS = 100
QUERY = (
    "select top 1000 pl_name,pl_orbper,st_mass,pl_orbsmax,pl_orbsmaxerr1,pl_orbsmaxerr2 "
    "from pscomppars where pl_orbper is not null and st_mass is not null and pl_orbsmax is not null "
    "order by pl_name"
)
ENDPOINT_URL = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query=" + quote(QUERY) + "&format=json"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[5]


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def sha256_object(payload: Any) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8", newline="\n")


def fetch_json(url: str, timeout: int = 90) -> Any:
    request = Request(url, headers={"User-Agent": "Logion-OC133-Research-Cache/1.0"})
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def as_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


def compact_rows(raw_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw in raw_rows:
        period = as_float(raw.get("pl_orbper"))
        mass = as_float(raw.get("st_mass"))
        sma = as_float(raw.get("pl_orbsmax"))
        if period is None or mass is None or sma is None or period <= 0 or mass <= 0 or sma <= 0:
            continue
        row = {
            "pl_name": str(raw.get("pl_name") or "").strip(),
            "pl_orbper_days": round(period, 10),
            "st_mass_solar": round(mass, 8),
            "pl_orbsmax_au": round(sma, 10),
            "pl_orbsmaxerr1_au": as_float(raw.get("pl_orbsmaxerr1")),
            "pl_orbsmaxerr2_au": as_float(raw.get("pl_orbsmaxerr2")),
        }
        row["row_sha256"] = sha256_object(row)
        rows.append(row)
    return sorted(rows, key=lambda row: (row["pl_name"], row["pl_orbper_days"], row["pl_orbsmax_au"]))


def acquire(root: Path, *, write: bool) -> dict[str, Any]:
    raw = fetch_json(ENDPOINT_URL)
    raw_rows = raw if isinstance(raw, list) else []
    rows = compact_rows([row for row in raw_rows if isinstance(row, dict)])
    snapshot = {
        "schema_id": SOURCE_SCHEMA_ID,
        "source_id": SOURCE_ID,
        "source_name": "NASA Exoplanet Archive TAP Planetary Systems Composite Parameters",
        "source_authority": "NASA Exoplanet Archive / IPAC",
        "official_documentation_url": "https://exoplanetarchive.ipac.caltech.edu/docs/TAP/usingTAP.html",
        "official_endpoint_url": ENDPOINT_URL,
        "query": QUERY,
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
        "target_fields_hidden": ["pl_orbsmax_au"],
        "visible_fields": ["pl_name", "pl_orbper_days", "st_mass_solar"],
        "target_values_scored": False,
        "target_hidden_until_scoring": True,
        "coverage_closure_allowed": False,
    }
    if write:
        write_json(root / SNAPSHOT_REL, snapshot)
        write_json(root / LOCK_REL, lock)
    return {"snapshot": snapshot, "lock": lock}


def kepler_semimajor_axis_au(period_days: float, mass_solar: float) -> float:
    return (mass_solar * (period_days / EARTH_YEAR_DAYS) ** 2) ** (1.0 / 3.0)


def split_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if len(rows) < MINIMUM_ROWS:
        return rows, []
    cut = max(MINIMUM_ROWS // 2, int(len(rows) * 0.7))
    return rows[:cut], rows[cut:]


def build_task_table(snapshot: dict[str, Any], lock: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    rows = [row for row in snapshot.get("rows", []) if isinstance(row, dict)]
    train, holdout = split_rows(rows)
    training_masses = [float(row["st_mass_solar"]) for row in train]
    comparator_mass = float(statistics.median(training_masses)) if training_masses else 1.0
    visible_rows = []
    hidden_rows = []
    for index, row in enumerate(holdout, start=1):
        task_id = f"PHYS-EXOPLANET-KEPLER-HOLDOUT-{index:04d}"
        visible_rows.append(
            {
                "task_id": task_id,
                "pl_name": row["pl_name"],
                "pl_orbper_days": row["pl_orbper_days"],
                "st_mass_solar": row["st_mass_solar"],
                "source_row_sha256": row["row_sha256"],
            }
        )
        hidden_rows.append(
            {
                "task_id": task_id,
                "target_pl_orbsmax_au": row["pl_orbsmax_au"],
                "target_pl_orbsmaxerr1_au": row["pl_orbsmaxerr1_au"],
                "target_pl_orbsmaxerr2_au": row["pl_orbsmaxerr2_au"],
                "source_row_sha256": row["row_sha256"],
            }
        )
    task_table = {
        "schema_id": TASK_SCHEMA_ID,
        "source_snapshot_ref": SNAPSHOT_REL,
        "source_lock_ref": LOCK_REL,
        "row_count": len(visible_rows),
        "training_row_count": len(train),
        "target_hidden_until_scoring": True,
        "coverage_closure_allowed": False,
        "model": {"model_id": MODEL_ID, "rule": "a_AU = (M_solar * (P_days / 365.2568983)^2)^(1/3)"},
        "comparator": {
            "comparator_id": COMPARATOR_ID,
            "rule": "Kepler third-law replay using the training-panel median stellar mass instead of each row's stellar mass",
            "training_median_stellar_mass_solar": round(comparator_mass, 8),
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
    comparator_mass = float(task_table["comparator"]["training_median_stellar_mass_solar"])
    scored = []
    model_abs = []
    comparator_abs = []
    for row in task_table["visible_rows"]:
        target = float(hidden_by_id[row["task_id"]]["target_pl_orbsmax_au"])
        model = kepler_semimajor_axis_au(float(row["pl_orbper_days"]), float(row["st_mass_solar"]))
        comparator = kepler_semimajor_axis_au(float(row["pl_orbper_days"]), comparator_mass)
        model_error = abs(model - target)
        comparator_error = abs(comparator - target)
        model_abs.append(model_error)
        comparator_abs.append(comparator_error)
        scored.append(
            {
                "task_id": row["task_id"],
                "pl_name": row["pl_name"],
                "model_prediction_au": round(model, 10),
                "comparator_prediction_au": round(comparator, 10),
                "target_au_opened_after_scoring": round(target, 10),
                "model_abs_error_au": round(model_error, 10),
                "comparator_abs_error_au": round(comparator_error, 10),
            }
        )
    model_mae = sum(model_abs) / len(model_abs) if model_abs else float("inf")
    comparator_mae = sum(comparator_abs) / len(comparator_abs) if comparator_abs else float("inf")
    shuffled_targets = list(reversed([float(row["target_pl_orbsmax_au"]) for row in target_lock["hidden_rows"]]))
    shuffled_model_abs = [
        abs(kepler_semimajor_axis_au(float(row["pl_orbper_days"]), float(row["st_mass_solar"])) - shuffled_targets[index])
        for index, row in enumerate(task_table["visible_rows"])
    ]
    shuffled_mae = sum(shuffled_model_abs) / len(shuffled_model_abs) if shuffled_model_abs else 0.0
    negative_control_rejected = bool(shuffled_mae > model_mae * 5)
    material_margin_met = bool(model_mae < comparator_mae and negative_control_rejected and len(scored) >= MINIMUM_ROWS)
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
            "model": round(model_mae, 8),
            "comparator": round(comparator_mae, 8),
            "material_margin_met": material_margin_met,
            "material_margin_rule": "Kepler-law semi-major-axis MAE must be below the preregistered median-stellar-mass Kepler comparator and the shuffled-target control must fail.",
        },
        "negative_control": {
            "control_id": "PHYS-EXOPLANET-TARGET-REVERSAL-CONTROL",
            "shuffled_model_mae_au": round(shuffled_mae, 8),
            "negative_control_rejected": negative_control_rejected,
        },
        "falsifier": {
            "falsifier_id": "PHYS-EXOPLANET-KEPLER-NO-MATERIAL-ADVANTAGE",
            "trigger": "source hash changes, fewer than 100 rows score, semi-major-axis leaks before scoring, or Kepler-law residual does not beat the preregistered median-mass comparator.",
        },
        "scored_rows": scored,
        "replay_command": {
            "commands": [
                "python validation/heldout/grand_science/physics_chemistry/nasa_exoplanet_archive/oc133_physics_exoplanet_kepler_materializer.py --check"
            ]
        },
        "fail_closed_reason": "" if material_margin_met else "Kepler scorer did not satisfy materiality or control predicates.",
    }
    report = {
        "schema_id": REPLAY_SCHEMA_ID,
        "status": "PASS" if material_margin_met else "FAIL_CLOSED",
        "scoring_pack_ref": SCORING_PACK_REL,
        "source_snapshot_ref": SNAPSHOT_REL,
        "source_lock_ref": LOCK_REL,
        "row_count": len(scored),
        "model_mae_au": round(model_mae, 8),
        "comparator_mae_au": round(comparator_mae, 8),
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
    for rel in [SNAPSHOT_REL, LOCK_REL, TASK_TABLE_REL, TARGET_LOCK_REL, SCORING_PACK_REL, REPLAY_REPORT_REL]:
        path = root / rel
        if not path.exists():
            failures.append(f"missing::{rel}")
            continue
        payload = read_json(path)
        if not isinstance(payload, dict):
            failures.append(f"not_object::{rel}")
        if payload.get("coverage_closure_allowed") is not False:
            failures.append(f"closure_allowed::{rel}")
    if not failures:
        expected = score(root, write=False)
        stored_pack = read_json(root / SCORING_PACK_REL)
        if sha256_object(stored_pack) != sha256_object(expected["pack"]):
            failures.append(f"mismatch::{SCORING_PACK_REL}")
        if stored_pack.get("scientific_pass") is not True:
            failures.append("EXOPLANET_KEPLER_PACK_NOT_PASSING")
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Materialize NASA Exoplanet Archive Kepler-law source-bound coverage evidence.")
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
            "model_mae_au": report["model_mae_au"],
            "comparator_mae_au": report["comparator_mae_au"],
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
