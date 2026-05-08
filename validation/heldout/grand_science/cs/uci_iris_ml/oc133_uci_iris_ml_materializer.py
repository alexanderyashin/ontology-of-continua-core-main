from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen


SCRIPT_REL = "validation/heldout/grand_science/cs/uci_iris_ml/oc133_uci_iris_ml_materializer.py"
ROOT_REL = "validation/heldout/grand_science/cs/uci_iris_ml"
SOURCE_REL = f"{ROOT_REL}/OC133_UCI_IRIS_SOURCE.csv"
LOCK_REL = f"{ROOT_REL}/OC133_UCI_IRIS_SOURCE.lock.json"
TASK_TABLE_REL = f"{ROOT_REL}/OC133_UCI_IRIS_TARGET_HIDDEN_TASK_TABLE.json"
TARGET_LOCK_REL = f"{ROOT_REL}/OC133-UCI-IRIS-HIDDEN-TARGETS-0001.lock.json"
SCORING_PACK_REL = f"{ROOT_REL}/OC133_UCI_IRIS_TARGET_HIDDEN_REPLAY_SCORER_EVIDENCE_PACK.json"
REPLAY_REPORT_REL = f"{ROOT_REL}/OC133_UCI_IRIS_REPLAY_REPORT.json"

SOURCE_URL = "https://archive.ics.uci.edu/ml/machine-learning-databases/iris/iris.data"
FEATURES = ("sepal_length_cm", "sepal_width_cm", "petal_length_cm", "petal_width_cm")
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


def fetch_csv() -> str:
    request = Request(SOURCE_URL, headers={"User-Agent": "OC research pipeline-OC133-UCI-Iris-Research-Cache/1.0"})
    with urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8", errors="replace")


def parse_rows(source_csv: str) -> list[dict[str, Any]]:
    rows = []
    reader = csv.reader(io.StringIO(source_csv))
    for index, raw in enumerate(reader):
        if len(raw) != 5:
            continue
        features = [float(raw[i]) for i in range(4)]
        species = raw[4].strip()
        if not species:
            continue
        row = {
            "source_row_index": index,
            "sepal_length_cm": features[0],
            "sepal_width_cm": features[1],
            "petal_length_cm": features[2],
            "petal_width_cm": features[3],
            "species": species,
        }
        row["source_row_sha256"] = sha256_object(row)
        rows.append(row)
    return rows


def acquire(root: Path, *, write: bool) -> dict[str, Any]:
    source_csv = fetch_csv()
    rows = parse_rows(source_csv)
    snapshot = {
        "schema_id": "OC133_UCI_IRIS_SOURCE_SNAPSHOT_v1",
        "source_id": "uci_iris_machine_learning_repository_v1",
        "source_name": "UCI Machine Learning Repository Iris data set",
        "source_authority": "UC Irvine Machine Learning Repository",
        "official_endpoint_url": SOURCE_URL,
        "row_count": len(rows),
        "target_values_scored": False,
        "target_hidden_until_scoring": True,
        "coverage_closure_allowed": False,
        "rows": rows,
        "rows_sha256": sha256_object(rows),
    }
    lock = {
        "schema_id": "OC133_UCI_IRIS_SOURCE_LOCK_v1",
        "source_snapshot_ref": SOURCE_REL,
        "source_snapshot_sha256": sha256_text(source_csv),
        "parsed_rows_sha256": snapshot["rows_sha256"],
        "row_count": len(rows),
        "visible_fields": list(FEATURES),
        "target_fields_hidden": ["species"],
        "target_values_scored": False,
        "target_hidden_until_scoring": True,
        "coverage_closure_allowed": False,
    }
    if write:
        source_path = root / SOURCE_REL
        source_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.write_text(source_csv, encoding="utf-8", newline="\n")
        write_json(root / LOCK_REL, lock)
    return {"source_csv": source_csv, "snapshot": snapshot, "lock": lock}


def load_source(root: Path) -> tuple[str, dict[str, Any]]:
    source_path = root / SOURCE_REL
    lock_path = root / LOCK_REL
    if not source_path.exists() or not lock_path.exists():
        payload = acquire(root, write=True)
        return payload["source_csv"], payload["lock"]
    return source_path.read_text(encoding="utf-8"), read_json(lock_path)


def build_task_table(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    source_csv, lock = load_source(root)
    rows = parse_rows(source_csv)
    visible_rows = []
    hidden_rows = []
    for index, row in enumerate(rows):
        task_id = f"UCI-IRIS-{index:03d}"
        split = "hidden_score" if index % 5 == 0 else "train_visible"
        visible_rows.append(
            {
                "task_id": task_id,
                "source_row_index": index,
                "split": split,
                **{feature: row[feature] for feature in FEATURES},
                "source_row_sha256": row["source_row_sha256"],
            }
        )
        hidden_rows.append(
            {
                "task_id": task_id,
                "source_row_index": index,
                "species": row["species"],
                "target_sha256": sha256_object({"task_id": task_id, "species": row["species"]}),
            }
        )
    task_table = {
        "schema_id": "OC133_UCI_IRIS_TARGET_HIDDEN_TASK_TABLE_v1",
        "source_snapshot_ref": SOURCE_REL,
        "source_lock_ref": LOCK_REL,
        "row_count": len(visible_rows),
        "train_visible_row_count": len([row for row in visible_rows if row["split"] == "train_visible"]),
        "hidden_score_row_count": len([row for row in visible_rows if row["split"] == "hidden_score"]),
        "target_hidden_until_scoring": True,
        "coverage_closure_allowed": False,
        "model": {
            "model_id": "CS-UCI-IRIS-NEAREST-CENTROID-v1",
            "rule": "Fit class centroids on train_visible rows and classify hidden rows by Euclidean distance.",
        },
        "comparator": {
            "comparator_id": "CS-UCI-IRIS-MAJORITY-CLASS-v1",
            "rule": "Predict the training majority class for every hidden row.",
        },
        "visible_rows": visible_rows,
    }
    target_lock = {
        "schema_id": "OC133_UCI_IRIS_HIDDEN_TARGET_LOCK_v1",
        "source_snapshot_ref": SOURCE_REL,
        "source_lock_ref": LOCK_REL,
        "visible_task_table_ref": TASK_TABLE_REL,
        "hidden_target_count": len(hidden_rows),
        "hidden_targets_sha256": sha256_object(hidden_rows),
        "target_hidden_until_scoring": True,
        "coverage_closure_allowed": False,
        "hidden_rows": hidden_rows,
    }
    return task_table, target_lock


def centroid(rows: list[dict[str, Any]]) -> dict[str, float]:
    return {feature: sum(float(row[feature]) for row in rows) / len(rows) for feature in FEATURES}


def train_centroids(train_rows: list[dict[str, Any]], target_by_task: dict[str, str]) -> dict[str, dict[str, float]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in train_rows:
        grouped[target_by_task[row["task_id"]]].append(row)
    return {label: centroid(rows) for label, rows in grouped.items() if rows}


def predict_centroid(row: dict[str, Any], centroids: dict[str, dict[str, float]]) -> str:
    best_label = ""
    best_distance = float("inf")
    for label, center in sorted(centroids.items()):
        distance = math.sqrt(sum((float(row[feature]) - center[feature]) ** 2 for feature in FEATURES))
        if distance < best_distance:
            best_label = label
            best_distance = distance
    return best_label


def permuted_training_targets(train_rows: list[dict[str, Any]], target_by_task: dict[str, str]) -> dict[str, str]:
    task_ids = sorted(row["task_id"] for row in train_rows)
    values = [target_by_task[task_id] for task_id in task_ids]
    return {**target_by_task, **dict(zip(task_ids, reversed(values)))}


def score(root: Path, *, write: bool) -> dict[str, Any]:
    task_table, target_lock = build_task_table(root)
    target_by_task = {row["task_id"]: row["species"] for row in target_lock["hidden_rows"]}
    train_rows = [row for row in task_table["visible_rows"] if row["split"] == "train_visible"]
    hidden_rows = [row for row in task_table["visible_rows"] if row["split"] == "hidden_score"]
    centroids = train_centroids(train_rows, target_by_task)
    majority_label = Counter(target_by_task[row["task_id"]] for row in train_rows).most_common(1)[0][0]
    negative_centroids = train_centroids(train_rows, permuted_training_targets(train_rows, target_by_task))
    model_losses = []
    comparator_losses = []
    negative_losses = []
    scored_rows = []
    for row in hidden_rows:
        target = target_by_task[row["task_id"]]
        model_prediction = predict_centroid(row, centroids)
        comparator_prediction = majority_label
        negative_prediction = predict_centroid(row, negative_centroids)
        model_loss = 0.0 if model_prediction == target else 1.0
        comparator_loss = 0.0 if comparator_prediction == target else 1.0
        negative_loss = 0.0 if negative_prediction == target else 1.0
        model_losses.append(model_loss)
        comparator_losses.append(comparator_loss)
        negative_losses.append(negative_loss)
        scored_rows.append(
            {
                "task_id": row["task_id"],
                "model_prediction_species": model_prediction,
                "comparator_prediction_species": comparator_prediction,
                "negative_control_prediction_species": negative_prediction,
                "model_0_1_loss": model_loss,
                "comparator_0_1_loss": comparator_loss,
                "negative_control_0_1_loss": negative_loss,
                "target_sha256": next(item["target_sha256"] for item in target_lock["hidden_rows"] if item["task_id"] == row["task_id"]),
            }
        )
    model_loss = sum(model_losses) / len(model_losses)
    comparator_loss = sum(comparator_losses) / len(comparator_losses)
    negative_loss = sum(negative_losses) / len(negative_losses)
    material_margin_met = model_loss + MATERIAL_MARGIN < comparator_loss
    negative_control_rejected = negative_loss > model_loss + MATERIAL_MARGIN
    pack_status = (
        "STRICT_EVIDENCE_PASS_NO_COVERAGE_CLOSURE"
        if material_margin_met and negative_control_rejected
        else "STRICT_EVIDENCE_FAIL_CLOSED"
    )
    scoring_pack = {
        "schema_id": "OC133_UCI_IRIS_ML_SCORING_PACK_v1",
        "pack_status": pack_status,
        "status": pack_status,
        "domain_class_id": "computer_information_sciences",
        "phenomenon_class_id": "machine_learning_generalization_and_evaluation",
        "source_bound": True,
        "target_hidden": True,
        "score_materialized": True,
        "scientific_pass": pack_status == "STRICT_EVIDENCE_PASS_NO_COVERAGE_CLOSURE",
        "coverage_closure_allowed": False,
        "support_allowed_for_broad_coverage": False,
        "source_snapshot_ref": SOURCE_REL,
        "source_snapshot_sha256": sha256_text(load_source(root)[0]),
        "source_lock_ref": LOCK_REL,
        "visible_task_table_ref": TASK_TABLE_REL,
        "hidden_target_lock_ref": TARGET_LOCK_REL,
        "row_count": len(scored_rows),
        "model": {"model_id": "CS-UCI-IRIS-NEAREST-CENTROID-v1", "centroids": centroids},
        "comparator": {"comparator_id": "CS-UCI-IRIS-MAJORITY-CLASS-v1", "majority_label": majority_label},
        "residuals": {
            "model": round(model_loss, 12),
            "comparator": round(comparator_loss, 12),
            "negative_control": round(negative_loss, 12),
            "material_margin_met": material_margin_met,
            "material_margin_rule": f"nearest-centroid loss + {MATERIAL_MARGIN} must be below majority-class comparator loss",
        },
        "negative_control": {
            "control_id": "CS-UCI-IRIS-REVERSED-TRAINING-LABEL-CONTROL-v1",
            "negative_control_rejected": negative_control_rejected,
        },
        "falsifiers": [
            "source lock hash is missing or stale",
            "hidden species labels appear in visible task rows",
            "nearest-centroid generalization does not beat majority baseline",
            "label-permutation negative control is not worse than the model",
        ],
        "scored_rows_sha256": sha256_object(scored_rows),
        "scored_rows_sample": scored_rows[:10],
    }
    replay_report = {
        "schema_id": "OC133_UCI_IRIS_REPLAY_REPORT_v1",
        "status": "PASS" if scoring_pack["scientific_pass"] else "FAIL_CLOSED",
        "scoring_pack_ref": SCORING_PACK_REL,
        "scoring_pack_sha256": sha256_object(scoring_pack),
        "row_count": len(scored_rows),
        "material_margin_met": material_margin_met,
        "negative_control_rejected": negative_control_rejected,
        "replay_command": {
            "commands": [f"python {SCRIPT_REL} --score --write-scoring", f"python {SCRIPT_REL} --check"]
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
    for rel_path in (SOURCE_REL, LOCK_REL):
        if not (root / rel_path).exists():
            errors.append(f"missing {rel_path}")
    if errors:
        return errors
    source_csv, lock = load_source(root)
    if lock.get("source_snapshot_sha256") != sha256_text(source_csv):
        errors.append("source csv hash mismatch")
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
        errors.append("UCI Iris ML scoring pack is fail-closed")
    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Materialize target-hidden UCI Iris ML generalization evidence.")
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
        print(json.dumps({"row_count": payload["snapshot"]["row_count"]}, indent=2))
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
        print("UCI Iris ML generalization: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
