from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen


SCRIPT_REL = "validation/heldout/grand_science/uci/coverage_work_orders/oc133_uci_tabular_classifier_materializer.py"
ROOT_REL = "validation/heldout/grand_science/uci"
MATERIAL_MARGIN_DEFAULT = 0.05

LANES: dict[str, dict[str, Any]] = {
    "cognitive_student_psychometric_performance": {
        "domain_class_id": "cognitive_behavioral_neurosciences",
        "phenomenon_class_id": "behavioral_task_and_psychometric_prediction",
        "source_url": "https://archive.ics.uci.edu/ml/machine-learning-databases/00320/student.zip",
        "source_kind": "zip_csv",
        "zip_member": "student-mat.csv",
        "delimiter": ";",
        "feature_names": [
            "age",
            "Medu",
            "Fedu",
            "traveltime",
            "studytime",
            "failures",
            "famrel",
            "freetime",
            "goout",
            "Dalc",
            "Walc",
            "health",
            "absences",
            "G1",
            "G2",
        ],
        "target_name": "G3_pass_fail",
        "target_from_row": "student_g3_pass_fail",
        "model_type": "decision_stump_binary",
        "material_margin": 0.05,
        "source_name": "UCI Student Performance data set",
        "source_authority": "UC Irvine Machine Learning Repository",
    },
    "cognitive_letter_perception": {
        "domain_class_id": "cognitive_behavioral_neurosciences",
        "phenomenon_class_id": "learning_memory_and_perception_dynamics",
        "source_url": "https://archive.ics.uci.edu/ml/machine-learning-databases/letter-recognition/letter-recognition.data",
        "source_kind": "csv_no_header",
        "feature_names": [f"letter_shape_feature_{index:02d}" for index in range(1, 17)],
        "target_name": "letter_class",
        "target_column_index": 0,
        "feature_column_start": 1,
        "model_type": "nearest_centroid_multiclass",
        "material_margin": 0.1,
        "source_name": "UCI Letter Recognition data set",
        "source_authority": "UC Irvine Machine Learning Repository",
    },
    "neuro_eeg_eye_state": {
        "domain_class_id": "cognitive_behavioral_neurosciences",
        "phenomenon_class_id": "neural_recording_and_brain_network_observables",
        "source_url": "https://archive.ics.uci.edu/ml/machine-learning-databases/00264/EEG%20Eye%20State.arff",
        "source_kind": "arff",
        "target_name": "eyeDetection",
        "model_type": "decision_stump_binary",
        "material_margin": 0.02,
        "source_name": "UCI EEG Eye State data set",
        "source_authority": "UC Irvine Machine Learning Repository",
    },
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[5]


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def sha256_object(payload: Any) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8", newline="\n")


def lane_paths(lane_id: str) -> dict[str, str]:
    stem = lane_id.upper()
    base = f"{ROOT_REL}/{lane_id}"
    return {
        "source": f"{base}/OC133_UCI_{stem}_SOURCE.dat",
        "lock": f"{base}/OC133_UCI_{stem}_SOURCE.lock.json",
        "task_table": f"{base}/OC133_UCI_{stem}_TARGET_HIDDEN_TASK_TABLE.json",
        "target_lock": f"{base}/OC133-UCI-{stem}-HIDDEN-TARGETS-0001.lock.json",
        "scoring_pack": f"{base}/OC133_UCI_{stem}_TARGET_HIDDEN_REPLAY_SCORER_EVIDENCE_PACK.json",
        "replay_report": f"{base}/OC133_UCI_{stem}_REPLAY_REPORT.json",
    }


def fetch_source(config: dict[str, Any]) -> bytes:
    request = Request(str(config["source_url"]), headers={"User-Agent": "Logion-OC133-UCI-Research-Cache/1.0"})
    with urlopen(request, timeout=90) as response:
        return response.read()


def parse_student_rows(payload: bytes, config: dict[str, Any]) -> list[dict[str, Any]]:
    archive = zipfile.ZipFile(io.BytesIO(payload))
    text = archive.read(str(config["zip_member"])).decode("utf-8", errors="replace")
    rows = []
    for index, row in enumerate(csv.DictReader(io.StringIO(text), delimiter=str(config["delimiter"]))):
        features = {name: float(row[name]) for name in config["feature_names"]}
        target = "pass" if int(row["G3"]) >= 10 else "fail"
        item = {
            "source_row_index": index,
            "features": features,
            "target": target,
        }
        item["source_row_sha256"] = sha256_object(item)
        rows.append(item)
    return rows


def parse_csv_no_header_rows(payload: bytes, config: dict[str, Any]) -> list[dict[str, Any]]:
    text = payload.decode("utf-8", errors="replace")
    rows = []
    for index, raw in enumerate(csv.reader(io.StringIO(text))):
        if len(raw) < int(config["feature_column_start"]) + len(config["feature_names"]):
            continue
        target = raw[int(config["target_column_index"])].strip()
        values = raw[int(config["feature_column_start"]) : int(config["feature_column_start"]) + len(config["feature_names"])]
        features = {name: float(value) for name, value in zip(config["feature_names"], values)}
        item = {"source_row_index": index, "features": features, "target": target}
        item["source_row_sha256"] = sha256_object(item)
        rows.append(item)
    return rows


def parse_arff_rows(payload: bytes, config: dict[str, Any]) -> list[dict[str, Any]]:
    text = payload.decode("utf-8", errors="replace")
    attributes = []
    data = False
    rows = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("%"):
            continue
        lowered = stripped.lower()
        if lowered.startswith("@attribute"):
            parts = stripped.split()
            if len(parts) >= 2:
                attributes.append(parts[1])
        elif lowered.startswith("@data"):
            data = True
        elif data:
            values = [part.strip() for part in stripped.split(",")]
            if len(values) != len(attributes):
                continue
            feature_names = attributes[:-1]
            features = {name: float(value) for name, value in zip(feature_names, values[:-1])}
            item = {"source_row_index": len(rows), "features": features, "target": values[-1]}
            item["source_row_sha256"] = sha256_object(item)
            rows.append(item)
    config.setdefault("feature_names", attributes[:-1])
    return rows


def parse_rows(payload: bytes, config: dict[str, Any]) -> list[dict[str, Any]]:
    kind = str(config["source_kind"])
    if kind == "zip_csv":
        return parse_student_rows(payload, config)
    if kind == "csv_no_header":
        return parse_csv_no_header_rows(payload, config)
    if kind == "arff":
        return parse_arff_rows(payload, config)
    raise RuntimeError(f"unsupported UCI source kind: {kind}")


def acquire(root: Path, lane_id: str, *, write: bool) -> dict[str, Any]:
    config = dict(LANES[lane_id])
    paths = lane_paths(lane_id)
    payload = fetch_source(config)
    rows = parse_rows(payload, config)
    snapshot = {
        "schema_id": "OC133_UCI_TABULAR_SOURCE_SNAPSHOT_v1",
        "lane_id": lane_id,
        "source_id": f"uci_{lane_id}_v1",
        "source_name": config["source_name"],
        "source_authority": config["source_authority"],
        "official_endpoint_url": config["source_url"],
        "row_count": len(rows),
        "target_name": config["target_name"],
        "target_values_scored": False,
        "target_hidden_until_scoring": True,
        "coverage_closure_allowed": False,
        "rows": rows,
        "rows_sha256": sha256_object(rows),
    }
    lock = {
        "schema_id": "OC133_UCI_TABULAR_SOURCE_LOCK_v1",
        "lane_id": lane_id,
        "source_snapshot_ref": paths["source"],
        "source_snapshot_sha256": sha256_bytes(payload),
        "parsed_rows_sha256": snapshot["rows_sha256"],
        "row_count": len(rows),
        "target_fields_hidden": [config["target_name"]],
        "target_values_scored": False,
        "target_hidden_until_scoring": True,
        "coverage_closure_allowed": False,
    }
    if write:
        source_path = root / paths["source"]
        source_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.write_bytes(payload)
        write_json(root / paths["lock"], lock)
    return {"payload": payload, "snapshot": snapshot, "lock": lock, "config": config}


def load_source(root: Path, lane_id: str) -> tuple[bytes, dict[str, Any], dict[str, Any]]:
    paths = lane_paths(lane_id)
    source_path = root / paths["source"]
    lock_path = root / paths["lock"]
    if not source_path.exists() or not lock_path.exists():
        payload = acquire(root, lane_id, write=True)
        return payload["payload"], payload["lock"], payload["config"]
    return source_path.read_bytes(), read_json(lock_path), dict(LANES[lane_id])


def build_task_table(root: Path, lane_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    payload, _lock, config = load_source(root, lane_id)
    paths = lane_paths(lane_id)
    rows = parse_rows(payload, config)
    visible_rows = []
    hidden_rows = []
    for index, row in enumerate(rows):
        task_id = f"UCI-{lane_id.upper()}-{index:05d}"
        split = "hidden_score" if index % 5 == 0 else "train_visible"
        visible_rows.append(
            {
                "task_id": task_id,
                "source_row_index": row["source_row_index"],
                "split": split,
                "features": row["features"],
                "source_row_sha256": row["source_row_sha256"],
            }
        )
        hidden_rows.append(
            {
                "task_id": task_id,
                "source_row_index": row["source_row_index"],
                str(config["target_name"]): row["target"],
                "target_sha256": sha256_object({"task_id": task_id, "target": row["target"]}),
            }
        )
    task_table = {
        "schema_id": "OC133_UCI_TABULAR_TARGET_HIDDEN_TASK_TABLE_v1",
        "lane_id": lane_id,
        "source_snapshot_ref": paths["source"],
        "source_lock_ref": paths["lock"],
        "row_count": len(visible_rows),
        "train_visible_row_count": len([row for row in visible_rows if row["split"] == "train_visible"]),
        "hidden_score_row_count": len([row for row in visible_rows if row["split"] == "hidden_score"]),
        "target_hidden_until_scoring": True,
        "coverage_closure_allowed": False,
        "model": {"model_id": f"UCI-{lane_id.upper()}-{config['model_type']}-v1"},
        "comparator": {"comparator_id": f"UCI-{lane_id.upper()}-MAJORITY-CLASS-v1"},
        "visible_rows": visible_rows,
    }
    target_lock = {
        "schema_id": "OC133_UCI_TABULAR_HIDDEN_TARGET_LOCK_v1",
        "lane_id": lane_id,
        "source_snapshot_ref": paths["source"],
        "source_lock_ref": paths["lock"],
        "visible_task_table_ref": paths["task_table"],
        "hidden_target_count": len(hidden_rows),
        "hidden_targets_sha256": sha256_object(hidden_rows),
        "target_hidden_until_scoring": True,
        "coverage_closure_allowed": False,
        "hidden_rows": hidden_rows,
    }
    return task_table, target_lock


def normalize_features(rows: list[dict[str, Any]]) -> tuple[dict[str, tuple[float, float]], list[dict[str, Any]]]:
    feature_names = list(rows[0]["features"].keys())
    bounds = {
        feature: (
            min(float(row["features"][feature]) for row in rows),
            max(float(row["features"][feature]) for row in rows),
        )
        for feature in feature_names
    }
    normalized = []
    for row in rows:
        features = {}
        for feature in feature_names:
            lo, hi = bounds[feature]
            features[feature] = (float(row["features"][feature]) - lo) / (hi - lo or 1.0)
        normalized.append({**row, "features": features})
    return bounds, normalized


def train_decision_stump(train_rows: list[dict[str, Any]], target_by_task: dict[str, str]) -> dict[str, Any]:
    labels = sorted(set(target_by_task[row["task_id"]] for row in train_rows))
    if len(labels) != 2:
        raise RuntimeError("decision_stump_binary requires exactly two labels")
    best: tuple[float, str, float, str] | None = None
    feature_names = list(train_rows[0]["features"].keys())
    for feature in feature_names:
        values = sorted(set(float(row["features"][feature]) for row in train_rows))
        if len(values) > 80:
            thresholds = [values[int(q * (len(values) - 1) / 20)] for q in range(1, 20)]
        else:
            thresholds = values
        for threshold in thresholds:
            for low_label in labels:
                high_label = labels[1] if low_label == labels[0] else labels[0]
                error = sum(
                    (low_label if float(row["features"][feature]) <= threshold else high_label)
                    != target_by_task[row["task_id"]]
                    for row in train_rows
                ) / len(train_rows)
                candidate = (error, feature, float(threshold), low_label)
                if best is None or candidate < best:
                    best = candidate
    assert best is not None
    return {"train_error": best[0], "feature": best[1], "threshold": best[2], "low_label": best[3], "labels": labels}


def predict_decision_stump(row: dict[str, Any], model: dict[str, Any]) -> str:
    low_label = str(model["low_label"])
    labels = list(model["labels"])
    high_label = labels[1] if low_label == labels[0] else labels[0]
    return low_label if float(row["features"][model["feature"]]) <= float(model["threshold"]) else high_label


def train_centroids(train_rows: list[dict[str, Any]], target_by_task: dict[str, str]) -> dict[str, dict[str, float]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in train_rows:
        grouped[target_by_task[row["task_id"]]].append(row)
    return {
        label: {
            feature: sum(float(row["features"][feature]) for row in rows) / len(rows)
            for feature in rows[0]["features"].keys()
        }
        for label, rows in grouped.items()
        if rows
    }


def predict_centroid(row: dict[str, Any], model: dict[str, dict[str, float]]) -> str:
    best_label = ""
    best_distance = float("inf")
    for label, center in sorted(model.items()):
        distance = math.sqrt(
            sum((float(row["features"][feature]) - center[feature]) ** 2 for feature in center.keys())
        )
        if distance < best_distance:
            best_label = label
            best_distance = distance
    return best_label


def permute_targets(train_rows: list[dict[str, Any]], target_by_task: dict[str, str]) -> dict[str, str]:
    task_ids = sorted(row["task_id"] for row in train_rows)
    return {**target_by_task, **dict(zip(task_ids, reversed([target_by_task[task_id] for task_id in task_ids])))}


def score(root: Path, lane_id: str, *, write: bool) -> dict[str, Any]:
    config = dict(LANES[lane_id])
    paths = lane_paths(lane_id)
    task_table, target_lock = build_task_table(root, lane_id)
    target_by_task = {row["task_id"]: str(row[config["target_name"]]) for row in target_lock["hidden_rows"]}
    train_rows = [row for row in task_table["visible_rows"] if row["split"] == "train_visible"]
    hidden_rows = [row for row in task_table["visible_rows"] if row["split"] == "hidden_score"]
    _bounds, normalized_rows = normalize_features(train_rows + hidden_rows)
    normalized_by_task = {row["task_id"]: row for row in normalized_rows}
    train_rows = [normalized_by_task[row["task_id"]] for row in train_rows]
    hidden_rows = [normalized_by_task[row["task_id"]] for row in hidden_rows]
    model_type = str(config["model_type"])
    if model_type == "decision_stump_binary":
        model = train_decision_stump(train_rows, target_by_task)
        negative_model = {"opposite_of": model}
        predict = lambda row: predict_decision_stump(row, model)
        negative_predict = lambda row: (
            model["labels"][1]
            if predict_decision_stump(row, model) == model["labels"][0]
            else model["labels"][0]
        )
    elif model_type == "nearest_centroid_multiclass":
        model = train_centroids(train_rows, target_by_task)
        negative_model = train_centroids(train_rows, permute_targets(train_rows, target_by_task))
        predict = lambda row: predict_centroid(row, model)
        negative_predict = lambda row: predict_centroid(row, negative_model)
    else:
        raise RuntimeError(f"unsupported UCI model type: {model_type}")
    majority_label = Counter(target_by_task[row["task_id"]] for row in train_rows).most_common(1)[0][0]
    model_losses = []
    comparator_losses = []
    negative_losses = []
    scored_rows = []
    target_hash_by_task = {row["task_id"]: row["target_sha256"] for row in target_lock["hidden_rows"]}
    for row in hidden_rows:
        target = target_by_task[row["task_id"]]
        model_prediction = predict(row)
        comparator_prediction = majority_label
        negative_prediction = negative_predict(row)
        model_loss = 0.0 if model_prediction == target else 1.0
        comparator_loss = 0.0 if comparator_prediction == target else 1.0
        negative_loss = 0.0 if negative_prediction == target else 1.0
        model_losses.append(model_loss)
        comparator_losses.append(comparator_loss)
        negative_losses.append(negative_loss)
        scored_rows.append(
            {
                "task_id": row["task_id"],
                "model_prediction": model_prediction,
                "comparator_prediction": comparator_prediction,
                "negative_control_prediction": negative_prediction,
                "model_0_1_loss": model_loss,
                "comparator_0_1_loss": comparator_loss,
                "negative_control_0_1_loss": negative_loss,
                "target_sha256": target_hash_by_task[row["task_id"]],
            }
        )
    model_loss = sum(model_losses) / len(model_losses)
    comparator_loss = sum(comparator_losses) / len(comparator_losses)
    negative_loss = sum(negative_losses) / len(negative_losses)
    margin = float(config.get("material_margin", MATERIAL_MARGIN_DEFAULT))
    material_margin_met = model_loss + margin < comparator_loss
    negative_control_rejected = negative_loss > model_loss + margin
    pack_status = (
        "STRICT_EVIDENCE_PASS_NO_COVERAGE_CLOSURE"
        if material_margin_met and negative_control_rejected
        else "STRICT_EVIDENCE_FAIL_CLOSED"
    )
    scoring_pack = {
        "schema_id": "OC133_UCI_TABULAR_CLASSIFIER_SCORING_PACK_v1",
        "pack_status": pack_status,
        "status": pack_status,
        "lane_id": lane_id,
        "domain_class_id": config["domain_class_id"],
        "phenomenon_class_id": config["phenomenon_class_id"],
        "source_bound": True,
        "target_hidden": True,
        "score_materialized": True,
        "scientific_pass": pack_status == "STRICT_EVIDENCE_PASS_NO_COVERAGE_CLOSURE",
        "coverage_closure_allowed": False,
        "support_allowed_for_broad_coverage": False,
        "source_snapshot_ref": paths["source"],
        "source_snapshot_sha256": sha256_bytes(load_source(root, lane_id)[0]),
        "source_lock_ref": paths["lock"],
        "visible_task_table_ref": paths["task_table"],
        "hidden_target_lock_ref": paths["target_lock"],
        "row_count": len(scored_rows),
        "model": {"model_id": f"UCI-{lane_id.upper()}-{model_type}-v1", "model": model},
        "comparator": {"comparator_id": f"UCI-{lane_id.upper()}-MAJORITY-CLASS-v1", "majority_label": majority_label},
        "residuals": {
            "model": round(model_loss, 12),
            "comparator": round(comparator_loss, 12),
            "negative_control": round(negative_loss, 12),
            "material_margin_met": material_margin_met,
            "material_margin_rule": f"classifier loss + {margin} must be below majority-class comparator loss",
        },
        "negative_control": {
            "control_id": f"UCI-{lane_id.upper()}-NEGATIVE-CONTROL-v1",
            "negative_model": negative_model,
            "negative_control_rejected": negative_control_rejected,
        },
        "falsifiers": [
            "source lock hash is missing or stale",
            "hidden target labels appear in visible task rows",
            "classifier does not beat majority-class comparator",
            "negative control is not worse than the model",
        ],
        "scored_rows_sha256": sha256_object(scored_rows),
        "scored_rows_sample": scored_rows[:10],
    }
    replay_report = {
        "schema_id": "OC133_UCI_TABULAR_CLASSIFIER_REPLAY_REPORT_v1",
        "status": "PASS" if scoring_pack["scientific_pass"] else "FAIL_CLOSED",
        "lane_id": lane_id,
        "scoring_pack_ref": paths["scoring_pack"],
        "scoring_pack_sha256": sha256_object(scoring_pack),
        "row_count": len(scored_rows),
        "material_margin_met": material_margin_met,
        "negative_control_rejected": negative_control_rejected,
        "replay_command": {
            "commands": [
                f"python {SCRIPT_REL} --lane {lane_id} --score --write-scoring",
                f"python {SCRIPT_REL} --lane {lane_id} --check",
            ]
        },
        "coverage_closure_allowed": False,
    }
    if write:
        write_json(root / paths["task_table"], task_table)
        write_json(root / paths["target_lock"], target_lock)
        write_json(root / paths["scoring_pack"], scoring_pack)
        write_json(root / paths["replay_report"], replay_report)
    return {"scoring_pack": scoring_pack, "replay_report": replay_report}


def check(root: Path, lane_id: str) -> list[str]:
    paths = lane_paths(lane_id)
    errors: list[str] = []
    for key in ("source", "lock"):
        if not (root / paths[key]).exists():
            errors.append(f"missing {paths[key]}")
    if errors:
        return errors
    payload, lock, _config = load_source(root, lane_id)
    if lock.get("source_snapshot_sha256") != sha256_bytes(payload):
        errors.append("source hash mismatch")
    expected_task_table, expected_target_lock = build_task_table(root, lane_id)
    expected_score = score(root, lane_id, write=False)
    for key, expected in (
        ("task_table", expected_task_table),
        ("target_lock", expected_target_lock),
        ("scoring_pack", expected_score["scoring_pack"]),
        ("replay_report", expected_score["replay_report"]),
    ):
        path = root / paths[key]
        if not path.exists():
            errors.append(f"missing {paths[key]}")
        elif read_json(path) != expected:
            errors.append(f"stale {paths[key]}")
    if expected_score["scoring_pack"].get("scientific_pass") is not True:
        errors.append(f"{lane_id} scoring pack is fail-closed")
    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Materialize target-hidden UCI tabular classifier evidence.")
    parser.add_argument("--lane", choices=sorted(LANES), required=True)
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
        payload = acquire(root, args.lane, write=args.write_acquisition)
        print(json.dumps({"lane": args.lane, "row_count": payload["snapshot"]["row_count"]}, indent=2))
    if args.score or args.write_scoring:
        payload = score(root, args.lane, write=args.write_scoring)
        print(
            json.dumps(
                {
                    "lane": args.lane,
                    "status": payload["scoring_pack"]["status"],
                    "row_count": payload["scoring_pack"]["row_count"],
                    "residuals": payload["scoring_pack"]["residuals"],
                },
                indent=2,
            )
        )
    if args.check:
        errors = check(root, args.lane)
        if errors:
            for error in errors:
                print(f"ERROR: {error}")
            return 1
        print(f"{args.lane}: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
