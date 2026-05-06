from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen


SOURCE_SCHEMA_ID = "OC133_OPERATIONS_WDI_RAIL_FREIGHT_SOURCE_SNAPSHOT_v1"
LOCK_SCHEMA_ID = "OC133_OPERATIONS_WDI_RAIL_FREIGHT_SOURCE_LOCK_v1"
TASK_SCHEMA_ID = "OC133_OPERATIONS_WDI_RAIL_FREIGHT_TARGET_HIDDEN_TASK_TABLE_v1"
TARGET_LOCK_SCHEMA_ID = "OC133_OPERATIONS_WDI_RAIL_FREIGHT_HIDDEN_TARGET_LOCK_v1"
PACK_SCHEMA_ID = "OC133_OPERATIONS_WDI_RAIL_FREIGHT_SCORING_PACK_v1"
REPLAY_SCHEMA_ID = "OC133_OPERATIONS_WDI_RAIL_FREIGHT_REPLAY_REPORT_v1"

SCRIPT_REL = (
    "validation/heldout/grand_science/operations/coverage_work_orders/"
    "oc133_operations_wdi_rail_freight_materializer.py"
)
ROOT_REL = "validation/heldout/grand_science/operations/wdi_rail_freight"
SNAPSHOT_REL = f"{ROOT_REL}/OC133_WORLD_BANK_WDI_RAIL_FREIGHT_SOURCE.json"
LOCK_REL = f"{ROOT_REL}/OC133_WORLD_BANK_WDI_RAIL_FREIGHT_SOURCE.lock.json"
TASK_TABLE_REL = f"{ROOT_REL}/OC133_WORLD_BANK_WDI_RAIL_FREIGHT_TARGET_HIDDEN_TASK_TABLE.json"
TARGET_LOCK_REL = f"{ROOT_REL}/OC133-WORLD-BANK-WDI-RAIL-FREIGHT-HIDDEN-TARGETS-0001.lock.json"
SCORING_PACK_REL = f"{ROOT_REL}/OC133_WORLD_BANK_WDI_RAIL_FREIGHT_TARGET_HIDDEN_REPLAY_SCORER_EVIDENCE_PACK.json"
REPLAY_REPORT_REL = f"{ROOT_REL}/OC133_WORLD_BANK_WDI_RAIL_FREIGHT_REPLAY_REPORT.json"

SOURCE_ID = "world_bank_wdi_rail_freight_ton_km_v1"
MODEL_ID = "OPS-WDI-RAIL-FREIGHT-LOG-LINEAR-FLOW-CONTINUATION-v1"
COMPARATOR_ID = "OPS-WDI-RAIL-FREIGHT-LAST-OBSERVATION-BASELINE-v1"
NEGATIVE_CONTROL_ID = "OPS-WDI-RAIL-FREIGHT-FIVE_YEAR_STALE_BASELINE_NEGATIVE_CONTROL-v1"
INDICATOR = "IS.RRS.GOOD.MT.K6"
INDICATOR_LABEL = "Railways, goods transported (million ton-km)"
API_URL = (
    "https://api.worldbank.org/v2/country/all/indicator/"
    f"{INDICATOR}?format=json&per_page=20000&date=2000:2019"
)
HOLDOUT_YEARS = tuple(range(2010, 2020))
HISTORY_YEARS = 5
MINIMUM_ROWS = 200
MATERIAL_MARGIN_RELATIVE_MAE = 0.05


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
    request = Request(url, headers={"User-Agent": "Logion-OC133-Research-Cache/1.0"})
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def acquire(root: Path, *, write: bool) -> dict[str, Any]:
    raw = fetch_json(API_URL)
    if not isinstance(raw, list) or len(raw) < 2 or not isinstance(raw[1], list):
        raise RuntimeError("World Bank WDI API returned an unexpected payload shape")
    source_rows = []
    for item in raw[1]:
        if not isinstance(item, dict):
            continue
        country_code = str(item.get("countryiso3code") or "")
        value = item.get("value")
        if len(country_code) != 3 or value is None:
            continue
        try:
            year = int(item.get("date"))
            freight_million_ton_km = float(value)
        except (TypeError, ValueError):
            continue
        if freight_million_ton_km <= 0:
            continue
        row = {
            "countryiso3code": country_code,
            "country_name": str((item.get("country") or {}).get("value") or ""),
            "indicator": INDICATOR,
            "indicator_label": INDICATOR_LABEL,
            "year": year,
            "rail_freight_million_ton_km": freight_million_ton_km,
            "row_sha256": "",
        }
        row["row_sha256"] = sha256_object({key: value for key, value in row.items() if key != "row_sha256"})
        source_rows.append(row)
    source_rows.sort(key=lambda row: (row["countryiso3code"], row["year"]))
    snapshot = {
        "schema_id": SOURCE_SCHEMA_ID,
        "source_id": SOURCE_ID,
        "source_name": "World Bank World Development Indicators API",
        "source_authority": "World Bank",
        "official_documentation_url": "https://datahelpdesk.worldbank.org/knowledgebase/topics/125589-developer-information",
        "official_endpoint_url": API_URL,
        "indicator": INDICATOR,
        "indicator_label": INDICATOR_LABEL,
        "year_range": "2000:2019",
        "row_count": len(source_rows),
        "minimum_rows_required": MINIMUM_ROWS,
        "target_values_scored": False,
        "target_hidden_until_scoring": True,
        "coverage_closure_allowed": False,
        "rows": source_rows,
        "rows_sha256": sha256_object(source_rows),
    }
    lock = {
        "schema_id": LOCK_SCHEMA_ID,
        "source_id": SOURCE_ID,
        "source_snapshot_ref": SNAPSHOT_REL,
        "source_snapshot_sha256": sha256_object(snapshot),
        "rows_sha256": snapshot["rows_sha256"],
        "row_count": len(source_rows),
        "visible_fields": ["countryiso3code", "country_name", "indicator", "indicator_label", "year"],
        "target_fields_hidden": ["rail_freight_million_ton_km"],
        "target_values_scored": False,
        "target_hidden_until_scoring": True,
        "coverage_closure_allowed": False,
    }
    if write:
        write_json(root / SNAPSHOT_REL, snapshot)
        write_json(root / LOCK_REL, lock)
    return {"snapshot": snapshot, "lock": lock}


def rows_by_country(snapshot: dict[str, Any]) -> dict[str, dict[int, float]]:
    grouped: dict[str, dict[int, float]] = {}
    for row in snapshot.get("rows", []):
        if not isinstance(row, dict):
            continue
        country = str(row.get("countryiso3code") or "")
        try:
            year = int(row.get("year"))
            value = float(row.get("rail_freight_million_ton_km"))
        except (TypeError, ValueError):
            continue
        if country and value > 0:
            grouped.setdefault(country, {})[year] = value
    return grouped


def build_task_table(snapshot: dict[str, Any], lock: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    by_country = rows_by_country(snapshot)
    source_hash_by_key = {
        (str(row.get("countryiso3code")), int(row.get("year"))): row.get("row_sha256")
        for row in snapshot.get("rows", [])
        if isinstance(row, dict) and row.get("year") is not None
    }
    visible_rows = []
    hidden_rows = []
    for country, yearly in sorted(by_country.items()):
        for target_year in HOLDOUT_YEARS:
            history = [
                {"year": year, "rail_freight_million_ton_km": yearly[year]}
                for year in range(target_year - HISTORY_YEARS, target_year)
                if yearly.get(year) is not None
            ]
            target = yearly.get(target_year)
            if len(history) != HISTORY_YEARS or target is None:
                continue
            task_id = f"OPS-WDI-RAIL-HOLDOUT-{country}-{target_year}"
            visible_rows.append(
                {
                    "task_id": task_id,
                    "countryiso3code": country,
                    "indicator": INDICATOR,
                    "target_year": target_year,
                    "history_window_years": HISTORY_YEARS,
                    "history_rows": history,
                    "source_row_sha256": source_hash_by_key.get((country, target_year)),
                }
            )
            hidden_rows.append(
                {
                    "task_id": task_id,
                    "target_rail_freight_million_ton_km": target,
                    "source_row_sha256": source_hash_by_key.get((country, target_year)),
                }
            )
    task_table = {
        "schema_id": TASK_SCHEMA_ID,
        "source_snapshot_ref": SNAPSHOT_REL,
        "source_lock_ref": LOCK_REL,
        "row_count": len(visible_rows),
        "target_hidden_until_scoring": True,
        "coverage_closure_allowed": False,
        "model": {"model_id": MODEL_ID, "rule": "Fit a five-year log-linear rail-freight flow and extrapolate one year."},
        "comparator": {"comparator_id": COMPARATOR_ID, "rule": "Predict held-out rail freight as the last visible value."},
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


def log_linear_predict(history_rows: list[dict[str, Any]], target_year: int) -> float:
    xs = [float(row["year"]) for row in history_rows]
    ys = [math.log(float(row["rail_freight_million_ton_km"])) for row in history_rows]
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    denominator = sum((x - mean_x) ** 2 for x in xs)
    slope = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys)) / denominator if denominator else 0.0
    return math.exp(mean_y + slope * (float(target_year) - mean_x))


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
    negative_control_errors = []
    for row in task_table["visible_rows"]:
        history = row["history_rows"]
        target = float(hidden_by_id[row["task_id"]]["target_rail_freight_million_ton_km"])
        model_prediction = log_linear_predict(history, int(row["target_year"]))
        comparator_prediction = float(history[-1]["rail_freight_million_ton_km"])
        negative_control_prediction = float(history[0]["rail_freight_million_ton_km"])
        model_error = abs(model_prediction - target) / target
        comparator_error = abs(comparator_prediction - target) / target
        negative_control_error = abs(negative_control_prediction - target) / target
        model_errors.append(model_error)
        comparator_errors.append(comparator_error)
        negative_control_errors.append(negative_control_error)
        scored.append(
            {
                "task_id": row["task_id"],
                "countryiso3code": row["countryiso3code"],
                "target_year": row["target_year"],
                "model_prediction_million_ton_km": round(model_prediction, 6),
                "comparator_prediction_million_ton_km": round(comparator_prediction, 6),
                "target_million_ton_km_opened_after_scoring": round(target, 6),
                "model_relative_abs_error": round(model_error, 12),
                "comparator_relative_abs_error": round(comparator_error, 12),
                "negative_control_relative_abs_error": round(negative_control_error, 12),
            }
        )
    model_mae = sum(model_errors) / len(model_errors) if model_errors else float("inf")
    comparator_mae = sum(comparator_errors) / len(comparator_errors) if comparator_errors else float("inf")
    negative_control_mae = sum(negative_control_errors) / len(negative_control_errors) if negative_control_errors else float("inf")
    negative_control_rejected = bool(negative_control_mae > comparator_mae and negative_control_mae > model_mae)
    material_margin_met = bool(
        len(scored) >= MINIMUM_ROWS
        and model_mae + MATERIAL_MARGIN_RELATIVE_MAE < comparator_mae
        and negative_control_rejected
    )
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
            "model_relative_mae": round(model_mae, 12),
            "comparator_relative_mae": round(comparator_mae, 12),
            "negative_control_relative_mae": round(negative_control_mae, 12),
            "material_margin_met": material_margin_met,
            "material_margin_rule": "model_relative_mae + 0.05 must be below last-observation comparator relative MAE",
        },
        "negative_control": {
            "control_id": NEGATIVE_CONTROL_ID,
            "negative_control_rejected": negative_control_rejected,
            "rule": "Five-year stale rail-freight baseline must be materially worse than model and comparator.",
        },
        "falsifiers": [
            "World Bank WDI source hash cannot be reproduced",
            "held-out rail freight target leaks into model fitting",
            "last-observation comparator ties or beats the log-linear flow model within the material margin",
            "five-year stale negative control is not rejected",
        ],
        "scored_rows_sha256": sha256_object(scored),
        "scored_rows_sample": scored[:50],
    }
    replay = {
        "schema_id": REPLAY_SCHEMA_ID,
        "status": "PASS" if material_margin_met else "FAIL",
        "scoring_pack_ref": SCORING_PACK_REL,
        "row_count": len(scored),
        "model_relative_mae": pack["residuals"]["model_relative_mae"],
        "comparator_relative_mae": pack["residuals"]["comparator_relative_mae"],
        "negative_control_rejected": negative_control_rejected,
        "replay_command": f"python {SCRIPT_REL} --score --write-scoring && python {SCRIPT_REL} --check",
    }
    if write:
        write_json(root / TASK_TABLE_REL, task_table)
        write_json(root / TARGET_LOCK_REL, target_lock)
        write_json(root / SCORING_PACK_REL, pack)
        write_json(root / REPLAY_REPORT_REL, replay)
    return {"task_table": task_table, "target_lock": target_lock, "pack": pack, "replay": replay}


def check(root: Path) -> list[str]:
    failures: list[str] = []
    for rel_path in (SNAPSHOT_REL, LOCK_REL, TASK_TABLE_REL, TARGET_LOCK_REL, SCORING_PACK_REL, REPLAY_REPORT_REL):
        if not (root / rel_path).exists():
            failures.append(f"missing::{rel_path}")
    if failures:
        return failures
    pack = read_json(root / SCORING_PACK_REL)
    replay = read_json(root / REPLAY_REPORT_REL)
    if pack.get("pack_status") != "STRICT_EVIDENCE_PASS_NO_COVERAGE_CLOSURE":
        failures.append("SCORING_PACK_NOT_STRICT_PASS")
    if replay.get("status") != "PASS":
        failures.append("REPLAY_NOT_PASS")
    if pack.get("coverage_closure_allowed") is not False or pack.get("support_allowed_for_broad_coverage") is not False:
        failures.append("NO_SEND_OR_BROAD_COVERAGE_LOCK_MISSING")
    if int(pack.get("row_count") or 0) < MINIMUM_ROWS:
        failures.append("ROW_COUNT_BELOW_MINIMUM")
    if not pack.get("residuals", {}).get("material_margin_met"):
        failures.append("MATERIAL_MARGIN_NOT_MET")
    if not pack.get("negative_control", {}).get("negative_control_rejected"):
        failures.append("NEGATIVE_CONTROL_NOT_REJECTED")
    return failures


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Materialize World Bank WDI rail-freight target-hidden replay evidence.")
    parser.add_argument("--root", default=str(repo_root()), help="repository root")
    parser.add_argument("--acquire", action="store_true", help="fetch and lock the WDI rail-freight source snapshot")
    parser.add_argument("--write-acquisition", action="store_true", help="write acquisition artifacts")
    parser.add_argument("--score", action="store_true", help="score the target-hidden rail-freight replay")
    parser.add_argument("--write-scoring", action="store_true", help="write scoring artifacts")
    parser.add_argument("--check", action="store_true", help="check stored artifacts")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    if args.check:
        failures = check(root)
        if failures:
            print(json.dumps({"status": "failed", "failures": failures}, indent=2))
            return 1
        print(json.dumps({"status": "ok", "checked": SCORING_PACK_REL}, indent=2))
        return 0
    if args.acquire or args.write_acquisition:
        result = acquire(root, write=args.write_acquisition)
        print(json.dumps({"status": "ok", "snapshot_rows": result["snapshot"]["row_count"]}, indent=2))
    if args.score or args.write_scoring:
        result = score(root, write=args.write_scoring)
        print(
            json.dumps(
                {
                    "status": result["pack"]["pack_status"],
                    "row_count": result["pack"]["row_count"],
                    "model_relative_mae": result["pack"]["residuals"]["model_relative_mae"],
                    "comparator_relative_mae": result["pack"]["residuals"]["comparator_relative_mae"],
                },
                indent=2,
            )
        )
    if not (args.acquire or args.write_acquisition or args.score or args.write_scoring):
        result = score(root, write=False)
        print(json.dumps({"status": result["pack"]["pack_status"], "row_count": result["pack"]["row_count"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
