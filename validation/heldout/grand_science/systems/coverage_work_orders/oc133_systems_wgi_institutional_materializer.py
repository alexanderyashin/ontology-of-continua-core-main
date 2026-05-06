from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen


SOURCE_SCHEMA_ID = "OC133_SYSTEMS_WGI_INSTITUTIONAL_SOURCE_SNAPSHOT_v1"
LOCK_SCHEMA_ID = "OC133_SYSTEMS_WGI_INSTITUTIONAL_SOURCE_LOCK_v1"
TASK_SCHEMA_ID = "OC133_SYSTEMS_WGI_INSTITUTIONAL_TARGET_HIDDEN_TASK_TABLE_v1"
TARGET_LOCK_SCHEMA_ID = "OC133_SYSTEMS_WGI_INSTITUTIONAL_HIDDEN_TARGET_LOCK_v1"
PACK_SCHEMA_ID = "OC133_SYSTEMS_WGI_INSTITUTIONAL_SCORING_PACK_v1"
REPLAY_SCHEMA_ID = "OC133_SYSTEMS_WGI_INSTITUTIONAL_REPLAY_REPORT_v1"

SCRIPT_REL = (
    "validation/heldout/grand_science/systems/coverage_work_orders/"
    "oc133_systems_wgi_institutional_materializer.py"
)
ROOT_REL = "validation/heldout/grand_science/systems/wgi_institutional"
SNAPSHOT_REL = f"{ROOT_REL}/OC133_WORLD_BANK_WGI_INSTITUTIONAL_SOURCE.json"
LOCK_REL = f"{ROOT_REL}/OC133_WORLD_BANK_WGI_INSTITUTIONAL_SOURCE.lock.json"
TASK_TABLE_REL = f"{ROOT_REL}/OC133_WORLD_BANK_WGI_INSTITUTIONAL_TARGET_HIDDEN_TASK_TABLE.json"
TARGET_LOCK_REL = f"{ROOT_REL}/OC133-WORLD-BANK-WGI-INSTITUTIONAL-HIDDEN-TARGETS-0001.lock.json"
SCORING_PACK_REL = f"{ROOT_REL}/OC133_WORLD_BANK_WGI_INSTITUTIONAL_TARGET_HIDDEN_REPLAY_SCORER_EVIDENCE_PACK.json"
REPLAY_REPORT_REL = f"{ROOT_REL}/OC133_WORLD_BANK_WGI_INSTITUTIONAL_REPLAY_REPORT.json"

SOURCE_ID = "world_bank_wgi_government_effectiveness_rule_of_law_v1"
MODEL_ID = "SYS-WGI-INSTITUTIONAL-STATE-PERSISTENCE-v1"
COMPARATOR_ID = "SYS-WGI-INSTITUTIONAL-FIVE_YEAR_TREND_BASELINE-v1"
NEGATIVE_CONTROL_ID = "SYS-WGI-INSTITUTIONAL-FIVE_YEAR_MEAN_NEGATIVE_CONTROL-v1"
INDICATORS = {
    "GOV_WGI_GE.EST": "Government Effectiveness - Governance estimate (approx. -2.5 to +2.5)",
    "GOV_WGI_RL.EST": "Rule of Law - Governance estimate (approx. -2.5 to +2.5)",
}
SOURCE_API_TEMPLATE = "https://api.worldbank.org/v2/sources/3/country/all/series/{indicator}/time/all?format=json&per_page=20000"
HOLDOUT_YEARS = tuple(range(2010, 2023))
HISTORY_YEARS = 5
MINIMUM_ROWS = 400
MATERIAL_MARGIN_ABS_MAE = 0.01


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


def parse_wgi_row(item: dict[str, Any], indicator: str) -> dict[str, Any] | None:
    variables = {str(var.get("concept")): var for var in item.get("variable", []) if isinstance(var, dict)}
    country = variables.get("Country", {})
    time = variables.get("Time", {})
    value = item.get("value")
    if value in (None, ""):
        return None
    try:
        year = int(str(time.get("id") or "").replace("YR", ""))
        estimate = float(value)
    except (TypeError, ValueError):
        return None
    country_code = str(country.get("id") or "")
    if len(country_code) != 3:
        return None
    row = {
        "countryiso3code": country_code,
        "country_name": str(country.get("value") or ""),
        "indicator": indicator,
        "indicator_label": INDICATORS[indicator],
        "year": year,
        "governance_estimate": estimate,
        "row_sha256": "",
    }
    row["row_sha256"] = sha256_object({key: value for key, value in row.items() if key != "row_sha256"})
    return row


def acquire(root: Path, *, write: bool) -> dict[str, Any]:
    rows = []
    source_hashes = {}
    for indicator in INDICATORS:
        url = SOURCE_API_TEMPLATE.format(indicator=indicator)
        raw = fetch_json(url)
        source_hashes[indicator] = sha256_object(raw)
        for item in raw.get("source", {}).get("data", []):
            if isinstance(item, dict):
                row = parse_wgi_row(item, indicator)
                if row:
                    rows.append(row)
    rows.sort(key=lambda row: (row["indicator"], row["countryiso3code"], row["year"]))
    snapshot = {
        "schema_id": SOURCE_SCHEMA_ID,
        "source_id": SOURCE_ID,
        "source_name": "World Bank Worldwide Governance Indicators API",
        "source_authority": "World Bank",
        "official_documentation_url": "https://www.worldbank.org/en/publication/worldwide-governance-indicators",
        "official_endpoint_templates": [SOURCE_API_TEMPLATE.format(indicator=indicator) for indicator in INDICATORS],
        "indicators": INDICATORS,
        "source_payload_sha256_by_indicator": source_hashes,
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
        "visible_fields": ["countryiso3code", "country_name", "indicator", "indicator_label", "year"],
        "target_fields_hidden": ["governance_estimate"],
        "target_values_scored": False,
        "target_hidden_until_scoring": True,
        "coverage_closure_allowed": False,
    }
    if write:
        write_json(root / SNAPSHOT_REL, snapshot)
        write_json(root / LOCK_REL, lock)
    return {"snapshot": snapshot, "lock": lock}


def rows_by_series(snapshot: dict[str, Any]) -> dict[tuple[str, str], dict[int, float]]:
    grouped: dict[tuple[str, str], dict[int, float]] = {}
    for row in snapshot.get("rows", []):
        if not isinstance(row, dict):
            continue
        try:
            year = int(row.get("year"))
            value = float(row.get("governance_estimate"))
        except (TypeError, ValueError):
            continue
        key = (str(row.get("indicator") or ""), str(row.get("countryiso3code") or ""))
        if key[0] and key[1]:
            grouped.setdefault(key, {})[year] = value
    return grouped


def build_task_table(snapshot: dict[str, Any], lock: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    grouped = rows_by_series(snapshot)
    source_hash_by_key = {
        (str(row.get("indicator")), str(row.get("countryiso3code")), int(row.get("year"))): row.get("row_sha256")
        for row in snapshot.get("rows", [])
        if isinstance(row, dict) and row.get("year") is not None
    }
    visible_rows = []
    hidden_rows = []
    for (indicator, country), yearly in sorted(grouped.items()):
        for target_year in HOLDOUT_YEARS:
            history = [
                {"year": year, "governance_estimate": yearly[year]}
                for year in range(target_year - HISTORY_YEARS, target_year)
                if yearly.get(year) is not None
            ]
            target = yearly.get(target_year)
            if len(history) != HISTORY_YEARS or target is None:
                continue
            task_id = f"SYS-WGI-{indicator}-{country}-{target_year}".replace(".", "-")
            visible_rows.append(
                {
                    "task_id": task_id,
                    "countryiso3code": country,
                    "indicator": indicator,
                    "indicator_label": INDICATORS[indicator],
                    "target_year": target_year,
                    "history_window_years": HISTORY_YEARS,
                    "history_rows": history,
                    "source_row_sha256": source_hash_by_key.get((indicator, country, target_year)),
                }
            )
            hidden_rows.append(
                {
                    "task_id": task_id,
                    "target_governance_estimate": target,
                    "source_row_sha256": source_hash_by_key.get((indicator, country, target_year)),
                }
            )
    task_table = {
        "schema_id": TASK_SCHEMA_ID,
        "source_snapshot_ref": SNAPSHOT_REL,
        "source_lock_ref": LOCK_REL,
        "row_count": len(visible_rows),
        "target_hidden_until_scoring": True,
        "coverage_closure_allowed": False,
        "model": {"model_id": MODEL_ID, "rule": "Predict the next institutional estimate as the last visible pre-target estimate."},
        "comparator": {"comparator_id": COMPARATOR_ID, "rule": "Fit a five-year linear trend and extrapolate one year."},
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


def trend_predict(history_rows: list[dict[str, Any]], target_year: int) -> float:
    xs = [float(row["year"]) for row in history_rows]
    ys = [float(row["governance_estimate"]) for row in history_rows]
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    denominator = sum((x - mean_x) ** 2 for x in xs)
    slope = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys)) / denominator if denominator else 0.0
    return mean_y + slope * (float(target_year) - mean_x)


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
        target = float(hidden_by_id[row["task_id"]]["target_governance_estimate"])
        model_prediction = float(history[-1]["governance_estimate"])
        comparator_prediction = trend_predict(history, int(row["target_year"]))
        negative_control_prediction = sum(float(item["governance_estimate"]) for item in history) / len(history)
        model_error = abs(model_prediction - target)
        comparator_error = abs(comparator_prediction - target)
        negative_control_error = abs(negative_control_prediction - target)
        model_errors.append(model_error)
        comparator_errors.append(comparator_error)
        negative_control_errors.append(negative_control_error)
        scored.append(
            {
                "task_id": row["task_id"],
                "countryiso3code": row["countryiso3code"],
                "indicator": row["indicator"],
                "target_year": row["target_year"],
                "model_prediction": round(model_prediction, 8),
                "comparator_prediction": round(comparator_prediction, 8),
                "target_opened_after_scoring": round(target, 8),
                "model_abs_error": round(model_error, 12),
                "comparator_abs_error": round(comparator_error, 12),
                "negative_control_abs_error": round(negative_control_error, 12),
            }
        )
    model_mae = sum(model_errors) / len(model_errors) if model_errors else float("inf")
    comparator_mae = sum(comparator_errors) / len(comparator_errors) if comparator_errors else float("inf")
    negative_control_mae = sum(negative_control_errors) / len(negative_control_errors) if negative_control_errors else float("inf")
    negative_control_rejected = bool(negative_control_mae > model_mae)
    material_margin_met = bool(
        len(scored) >= MINIMUM_ROWS
        and model_mae + MATERIAL_MARGIN_ABS_MAE < comparator_mae
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
            "model_abs_mae": round(model_mae, 12),
            "comparator_abs_mae": round(comparator_mae, 12),
            "negative_control_abs_mae": round(negative_control_mae, 12),
            "material_margin_met": material_margin_met,
            "material_margin_rule": "model_abs_mae + 0.01 must be below the five-year trend comparator MAE",
        },
        "negative_control": {
            "control_id": NEGATIVE_CONTROL_ID,
            "negative_control_rejected": negative_control_rejected,
            "rule": "Five-year historical mean must be worse than the institutional-state persistence model.",
        },
        "falsifiers": [
            "World Bank WGI source hash cannot be reproduced",
            "held-out governance estimate leaks into model selection",
            "five-year trend comparator ties or beats the persistence model within the material margin",
            "historical-mean negative control is not rejected",
        ],
        "scored_rows_sha256": sha256_object(scored),
        "scored_rows_sample": scored[:50],
    }
    replay = {
        "schema_id": REPLAY_SCHEMA_ID,
        "status": "PASS" if material_margin_met else "FAIL",
        "scoring_pack_ref": SCORING_PACK_REL,
        "row_count": len(scored),
        "model_abs_mae": pack["residuals"]["model_abs_mae"],
        "comparator_abs_mae": pack["residuals"]["comparator_abs_mae"],
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
    parser = argparse.ArgumentParser(description="Materialize World Bank WGI institutional target-hidden replay evidence.")
    parser.add_argument("--root", default=str(repo_root()), help="repository root")
    parser.add_argument("--acquire", action="store_true", help="fetch and lock the WGI source snapshot")
    parser.add_argument("--write-acquisition", action="store_true", help="write acquisition artifacts")
    parser.add_argument("--score", action="store_true", help="score the target-hidden WGI replay")
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
                    "model_abs_mae": result["pack"]["residuals"]["model_abs_mae"],
                    "comparator_abs_mae": result["pack"]["residuals"]["comparator_abs_mae"],
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
