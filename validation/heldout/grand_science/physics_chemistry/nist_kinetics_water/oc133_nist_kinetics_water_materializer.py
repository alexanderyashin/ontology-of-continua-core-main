from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import re
from pathlib import Path
from typing import Any
from urllib.parse import urljoin
from urllib.request import Request, urlopen


SCRIPT_REL = (
    "validation/heldout/grand_science/physics_chemistry/nist_kinetics_water/"
    "oc133_nist_kinetics_water_materializer.py"
)
ROOT_REL = "validation/heldout/grand_science/physics_chemistry/nist_kinetics_water"
SOURCE_PAGES_REL = f"{ROOT_REL}/OC133_NIST_KINETICS_WATER_SOURCE_PAGES.json"
LOCK_REL = f"{ROOT_REL}/OC133_NIST_KINETICS_WATER_SOURCE.lock.json"
TASK_TABLE_REL = f"{ROOT_REL}/OC133_NIST_KINETICS_WATER_TARGET_HIDDEN_TASK_TABLE.json"
TARGET_LOCK_REL = f"{ROOT_REL}/OC133-NIST-KINETICS-WATER-HIDDEN-TARGETS-0001.lock.json"
SCORING_PACK_REL = f"{ROOT_REL}/OC133_NIST_KINETICS_WATER_TARGET_HIDDEN_REPLAY_SCORER_EVIDENCE_PACK.json"
REPLAY_REPORT_REL = f"{ROOT_REL}/OC133_NIST_KINETICS_WATER_REPLAY_REPORT.json"

BASE_URL = "https://kinetics.nist.gov"
SEARCH_URL = "https://kinetics.nist.gov/kinetics/rpSearch?cas=7732185"
MAX_REACTION_PAGES = 40
R_GAS_CONSTANT = 8.314472
EVALUATION_TEMPERATURE_K = 298.0
MATERIAL_MARGIN = 0.05


def repo_root() -> Path:
    return Path(__file__).resolve().parents[5]


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def sha256_object(payload: Any) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def sha256_text(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8", newline="\n")


def fetch_text(url: str) -> str:
    request = Request(url, headers={"User-Agent": "OC research pipeline-OC133-NIST-Kinetics-Research-Cache/1.0"})
    with urlopen(request, timeout=90) as response:
        return response.read().decode("utf-8", errors="replace")


def clean_cell(cell_html: str) -> str:
    text = re.sub(r"<script.*?</script>", " ", cell_html, flags=re.S | re.I)
    text = re.sub(r"<.*?>", " ", text, flags=re.S)
    text = html.unescape(text).replace("\xa0", " ")
    return re.sub(r"\s+", " ", text).strip()


def parse_float(value: str) -> float | None:
    cleaned = value.replace("\u2212", "-").replace("E ", "E").strip()
    try:
        return float(cleaned)
    except ValueError:
        return None


def reaction_links(search_html: str) -> list[str]:
    links = []
    for href in re.findall(r'href="([^"]*ReactionSearch[^"]*expandResults=true[^"]*)"', search_html):
        absolute = urljoin(BASE_URL, html.unescape(href))
        if absolute not in links:
            links.append(absolute)
    return links[:MAX_REACTION_PAGES]


def parse_records_from_page(page_url: str, page_html: str) -> list[dict[str, Any]]:
    records = []
    for row_html in re.findall(r"<tr[^>]*>.*?</tr>", page_html, flags=re.S | re.I):
        data_match = re.search(r'name="data\d+"\s+value="([^"]+)"', row_html)
        id_match = re.search(r'name="id\d+"\s+value="([^"]+)"', row_html)
        order_match = re.search(r'name="order\d+"\s+value="([^"]+)"', row_html)
        if not data_match or not id_match or not order_match:
            continue
        data_values = [parse_float(value) for value in data_match.group(1).split(",")]
        if len(data_values) != 5 or any(value is None for value in data_values):
            continue
        cells = [clean_cell(cell) for cell in re.findall(r"<td[^>]*>(.*?)</td>", row_html, flags=re.S | re.I)]
        cells = [cell for cell in cells if cell and cell != "&nbsp;"]
        numeric_cells = [cell for cell in cells if parse_float(cell) is not None]
        if len(numeric_cells) < 4:
            continue
        order = parse_float(order_match.group(1))
        if order is None:
            continue
        # The displayed target is the k(298 K) column immediately before order in NIST's result table.
        k_candidates = [parse_float(cell) for cell in numeric_cells]
        k_candidates = [value for value in k_candidates if value is not None and value > 0]
        if not k_candidates:
            continue
        k_298 = k_candidates[-2] if len(k_candidates) >= 2 else k_candidates[-1]
        if k_298 <= 0:
            continue
        temp_low, temp_high, arrhenius_a, arrhenius_n, activation_e = [float(value) for value in data_values]
        record = {
            "record_id": id_match.group(1),
            "page_url": page_url,
            "temperature_low_k": temp_low,
            "temperature_high_k": temp_high,
            "arrhenius_a": arrhenius_a,
            "arrhenius_n": arrhenius_n,
            "activation_energy_j_per_mole": activation_e,
            "reaction_order": int(order),
            "k_298_source_value": k_298,
        }
        record["source_row_sha256"] = sha256_object(record)
        records.append(record)
    return records


def acquire(root: Path, *, write: bool) -> dict[str, Any]:
    search_html = fetch_text(SEARCH_URL)
    pages = [{"url": SEARCH_URL, "html": search_html, "sha256": sha256_text(search_html)}]
    rows = []
    for link in reaction_links(search_html):
        page_html = fetch_text(link)
        pages.append({"url": link, "html": page_html, "sha256": sha256_text(page_html)})
        rows.extend(parse_records_from_page(link, page_html))
        if len(rows) >= 120:
            break
    snapshot = {
        "schema_id": "OC133_NIST_KINETICS_WATER_SOURCE_SNAPSHOT_v1",
        "source_id": "nist_chemical_kinetics_water_reaction_records_v1",
        "source_authority": "NIST Chemical Kinetics Database",
        "official_endpoint_url": SEARCH_URL,
        "page_count": len(pages),
        "row_count": len(rows),
        "target_name": "log10_k_298",
        "target_hidden_until_scoring": True,
        "coverage_closure_allowed": False,
        "pages": pages,
        "records": rows,
        "records_sha256": sha256_object(rows),
    }
    lock = {
        "schema_id": "OC133_NIST_KINETICS_WATER_SOURCE_LOCK_v1",
        "source_snapshot_ref": SOURCE_PAGES_REL,
        "source_snapshot_sha256": sha256_object(pages),
        "records_sha256": snapshot["records_sha256"],
        "row_count": len(rows),
        "target_fields_hidden": ["log10_k_298"],
        "target_hidden_until_scoring": True,
        "coverage_closure_allowed": False,
    }
    if write:
        write_json(root / SOURCE_PAGES_REL, snapshot)
        write_json(root / LOCK_REL, lock)
    return {"snapshot": snapshot, "lock": lock}


def load_snapshot(root: Path) -> dict[str, Any]:
    path = root / SOURCE_PAGES_REL
    if not path.exists():
        return acquire(root, write=True)["snapshot"]
    return read_json(path)


def build_task_table(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    snapshot = load_snapshot(root)
    visible_rows = []
    hidden_rows = []
    for index, record in enumerate(snapshot["records"]):
        task_id = f"NIST-KINETICS-WATER-{index:04d}"
        split = "hidden_score" if index % 5 == 0 else "train_visible"
        features = {
            "temperature_low_k": record["temperature_low_k"],
            "temperature_high_k": record["temperature_high_k"],
            "arrhenius_a": record["arrhenius_a"],
            "arrhenius_n": record["arrhenius_n"],
            "activation_energy_j_per_mole": record["activation_energy_j_per_mole"],
            "reaction_order": record["reaction_order"],
        }
        target = math.log10(float(record["k_298_source_value"]))
        visible_rows.append(
            {
                "task_id": task_id,
                "source_row_index": index,
                "split": split,
                "record_id": record["record_id"],
                "features": features,
                "source_row_sha256": record["source_row_sha256"],
            }
        )
        hidden_rows.append(
            {
                "task_id": task_id,
                "source_row_index": index,
                "log10_k_298": target,
                "target_sha256": sha256_object({"task_id": task_id, "log10_k_298": target}),
            }
        )
    task_table = {
        "schema_id": "OC133_NIST_KINETICS_WATER_TARGET_HIDDEN_TASK_TABLE_v1",
        "source_snapshot_ref": SOURCE_PAGES_REL,
        "source_lock_ref": LOCK_REL,
        "row_count": len(visible_rows),
        "train_visible_row_count": len([row for row in visible_rows if row["split"] == "train_visible"]),
        "hidden_score_row_count": len([row for row in visible_rows if row["split"] == "hidden_score"]),
        "target_hidden_until_scoring": True,
        "coverage_closure_allowed": False,
        "model": {
            "model_id": "NIST-KINETICS-WATER-ARRHENIUS-REPLAY-v1",
            "rule": "Use source-visible Arrhenius A,n,Ea parameters to compute log10(k(298 K)).",
        },
        "comparator": {
            "comparator_id": "NIST-KINETICS-WATER-TRAINING-MEDIAN-LOGK-v1",
            "rule": "Predict every hidden row with the median visible training log10(k(298 K)).",
        },
        "visible_rows": visible_rows,
    }
    target_lock = {
        "schema_id": "OC133_NIST_KINETICS_WATER_HIDDEN_TARGET_LOCK_v1",
        "source_snapshot_ref": SOURCE_PAGES_REL,
        "source_lock_ref": LOCK_REL,
        "visible_task_table_ref": TASK_TABLE_REL,
        "hidden_target_count": len(hidden_rows),
        "hidden_targets_sha256": sha256_object(hidden_rows),
        "target_hidden_until_scoring": True,
        "coverage_closure_allowed": False,
        "hidden_rows": hidden_rows,
    }
    return task_table, target_lock


def formula_log10_k(features: dict[str, Any]) -> float:
    arrhenius_a = float(features["arrhenius_a"])
    activation_e = float(features["activation_energy_j_per_mole"])
    if arrhenius_a <= 0:
        return float("nan")
    k = arrhenius_a * math.exp(-activation_e / (R_GAS_CONSTANT * EVALUATION_TEMPERATURE_K))
    return math.log10(k)


def median(values: list[float]) -> float:
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2


def score(root: Path, *, write: bool) -> dict[str, Any]:
    task_table, target_lock = build_task_table(root)
    target_by_task = {row["task_id"]: float(row["log10_k_298"]) for row in target_lock["hidden_rows"]}
    train_rows = [row for row in task_table["visible_rows"] if row["split"] == "train_visible"]
    hidden_rows = [row for row in task_table["visible_rows"] if row["split"] == "hidden_score"]
    comparator_prediction = median([target_by_task[row["task_id"]] for row in train_rows])
    formula_predictions = [formula_log10_k(row["features"]) for row in hidden_rows]
    negative_predictions = list(reversed(formula_predictions))
    scored_rows = []
    model_losses = []
    comparator_losses = []
    negative_losses = []
    target_hash_by_task = {row["task_id"]: row["target_sha256"] for row in target_lock["hidden_rows"]}
    for row, model_prediction, negative_prediction in zip(hidden_rows, formula_predictions, negative_predictions):
        target = target_by_task[row["task_id"]]
        model_loss = abs(model_prediction - target)
        comparator_loss = abs(comparator_prediction - target)
        negative_loss = abs(negative_prediction - target)
        model_losses.append(model_loss)
        comparator_losses.append(comparator_loss)
        negative_losses.append(negative_loss)
        scored_rows.append(
            {
                "task_id": row["task_id"],
                "record_id": row["record_id"],
                "model_log10_k_prediction": model_prediction,
                "comparator_log10_k_prediction": comparator_prediction,
                "negative_control_log10_k_prediction": negative_prediction,
                "model_loss": model_loss,
                "comparator_loss": comparator_loss,
                "negative_control_loss": negative_loss,
                "target_sha256": target_hash_by_task[row["task_id"]],
            }
        )
    model_mae = sum(model_losses) / len(model_losses)
    comparator_mae = sum(comparator_losses) / len(comparator_losses)
    negative_mae = sum(negative_losses) / len(negative_losses)
    material_margin_met = model_mae + MATERIAL_MARGIN < comparator_mae
    negative_control_rejected = negative_mae > model_mae + MATERIAL_MARGIN
    pack_status = (
        "STRICT_EVIDENCE_PASS_NO_COVERAGE_CLOSURE"
        if material_margin_met and negative_control_rejected
        else "STRICT_EVIDENCE_FAIL_CLOSED"
    )
    scoring_pack = {
        "schema_id": "OC133_NIST_KINETICS_WATER_SCORING_PACK_v1",
        "pack_status": pack_status,
        "status": pack_status,
        "domain_class_id": "chemical_sciences",
        "phenomenon_class_id": "reaction_and_kinetics_prediction",
        "source_bound": True,
        "target_hidden": True,
        "score_materialized": True,
        "scientific_pass": pack_status == "STRICT_EVIDENCE_PASS_NO_COVERAGE_CLOSURE",
        "coverage_closure_allowed": False,
        "support_allowed_for_broad_coverage": False,
        "source_snapshot_ref": SOURCE_PAGES_REL,
        "source_snapshot_sha256": sha256_object(load_snapshot(root)["pages"]),
        "source_lock_ref": LOCK_REL,
        "visible_task_table_ref": TASK_TABLE_REL,
        "hidden_target_lock_ref": TARGET_LOCK_REL,
        "row_count": len(scored_rows),
        "model": {
            "model_id": "NIST-KINETICS-WATER-ARRHENIUS-REPLAY-v1",
            "formula": "log10(A * exp(-Ea / (R * 298 K)))",
            "R_j_per_mole_k": R_GAS_CONSTANT,
        },
        "comparator": {
            "comparator_id": "NIST-KINETICS-WATER-TRAINING-MEDIAN-LOGK-v1",
            "training_median_log10_k_298": comparator_prediction,
        },
        "residuals": {
            "model": round(model_mae, 12),
            "comparator": round(comparator_mae, 12),
            "negative_control": round(negative_mae, 12),
            "material_margin_met": material_margin_met,
            "material_margin_rule": f"Arrhenius replay log10-MAE + {MATERIAL_MARGIN} must be below training-median log10-MAE",
        },
        "negative_control": {
            "control_id": "NIST-KINETICS-WATER-REVERSED-FORMULA-PREDICTIONS-v1",
            "negative_control_rejected": negative_control_rejected,
        },
        "falsifiers": [
            "source lock hash is missing or stale",
            "k(298 K) target values appear in visible rows",
            "Arrhenius replay does not beat training-median comparator",
            "reversed prediction negative control is not worse than the model",
        ],
        "scored_rows_sha256": sha256_object(scored_rows),
        "scored_rows_sample": scored_rows[:10],
    }
    replay_report = {
        "schema_id": "OC133_NIST_KINETICS_WATER_REPLAY_REPORT_v1",
        "status": "PASS" if scoring_pack["scientific_pass"] else "FAIL_CLOSED",
        "scoring_pack_ref": SCORING_PACK_REL,
        "scoring_pack_sha256": sha256_object(scoring_pack),
        "row_count": len(scored_rows),
        "material_margin_met": material_margin_met,
        "negative_control_rejected": negative_control_rejected,
        "replay_command": {
            "commands": [
                f"python {SCRIPT_REL} --score --write-scoring",
                f"python {SCRIPT_REL} --check",
            ]
        },
        "coverage_closure_allowed": False,
    }
    if write:
        write_json(root / TASK_TABLE_REL, task_table)
        write_json(root / TARGET_LOCK_REL, target_lock)
        write_json(root / SCORING_PACK_REL, scoring_pack)
        write_json(root / REPLAY_REPORT_REL, replay_report)
    return {"scoring_pack": scoring_pack, "replay_report": replay_report}


def check(root: Path) -> list[str]:
    errors: list[str] = []
    for rel_path in (SOURCE_PAGES_REL, LOCK_REL):
        if not (root / rel_path).exists():
            errors.append(f"missing {rel_path}")
    if errors:
        return errors
    snapshot = read_json(root / SOURCE_PAGES_REL)
    lock = read_json(root / LOCK_REL)
    if lock.get("source_snapshot_sha256") != sha256_object(snapshot.get("pages", [])):
        errors.append("source pages hash mismatch")
    expected_task_table, expected_target_lock = build_task_table(root)
    expected_score = score(root, write=False)
    for rel_path, expected in (
        (TASK_TABLE_REL, expected_task_table),
        (TARGET_LOCK_REL, expected_target_lock),
        (SCORING_PACK_REL, expected_score["scoring_pack"]),
        (REPLAY_REPORT_REL, expected_score["replay_report"]),
    ):
        path = root / rel_path
        if not path.exists():
            errors.append(f"missing {rel_path}")
        elif read_json(path) != expected:
            errors.append(f"stale {rel_path}")
    if expected_score["scoring_pack"].get("scientific_pass") is not True:
        errors.append("NIST kinetics scoring pack is fail-closed")
    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Materialize NIST kinetics target-hidden Arrhenius replay evidence.")
    parser.add_argument("--root", default=None)
    parser.add_argument("--acquire", action="store_true")
    parser.add_argument("--write-acquisition", action="store_true")
    parser.add_argument("--score", action="store_true")
    parser.add_argument("--write-scoring", action="store_true")
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve() if args.root else repo_root()
    if args.acquire or args.write_acquisition:
        payload = acquire(root, write=args.write_acquisition)
        print(json.dumps({"row_count": payload["snapshot"]["row_count"], "page_count": payload["snapshot"]["page_count"]}, indent=2))
    if args.score or args.write_scoring:
        payload = score(root, write=args.write_scoring)
        print(
            json.dumps(
                {
                    "status": payload["scoring_pack"]["status"],
                    "row_count": payload["scoring_pack"]["row_count"],
                    "residuals": payload["scoring_pack"]["residuals"],
                },
                indent=2,
            )
        )
    if args.check:
        errors = check(root)
        if errors:
            for error in errors:
                print(f"ERROR: {error}")
            return 1
        print("nist_kinetics_water: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
