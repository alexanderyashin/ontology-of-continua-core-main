from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

import numpy as np


SCRIPT_REL = (
    "validation/heldout/grand_science/cs/codexglue_defect/"
    "oc133_codexglue_defect_materializer.py"
)
ROOT_REL = "validation/heldout/grand_science/cs/codexglue_defect"
FUNCTIONS_REL = f"{ROOT_REL}/OC133_CODEXGLUE_DEFECT_FUNCTIONS.json"
TRAIN_IDS_REL = f"{ROOT_REL}/OC133_CODEXGLUE_DEFECT_TRAIN_IDS.txt"
TEST_IDS_REL = f"{ROOT_REL}/OC133_CODEXGLUE_DEFECT_TEST_IDS.txt"
LOCK_REL = f"{ROOT_REL}/OC133_CODEXGLUE_DEFECT_SOURCE.lock.json"
TASK_TABLE_REL = f"{ROOT_REL}/OC133_CODEXGLUE_DEFECT_TARGET_HIDDEN_TASK_TABLE.json"
TARGET_LOCK_REL = f"{ROOT_REL}/OC133-CODEXGLUE-DEFECT-HIDDEN-TARGETS-0001.lock.json"
SCORING_PACK_REL = f"{ROOT_REL}/OC133_CODEXGLUE_DEFECT_TARGET_HIDDEN_REPLAY_SCORER_EVIDENCE_PACK.json"
REPLAY_REPORT_REL = f"{ROOT_REL}/OC133_CODEXGLUE_DEFECT_REPLAY_REPORT.json"

BASE_URL = "https://raw.githubusercontent.com/madlag/CodeXGLUE/main/Code-Code/Defect-detection/dataset"
FUNCTIONS_URL = f"{BASE_URL}/function.json"
TRAIN_IDS_URL = f"{BASE_URL}/train.txt"
TEST_IDS_URL = f"{BASE_URL}/test.txt"
MATERIAL_MARGIN = 0.005
TOKENS = (
    "malloc",
    "free",
    "memcpy",
    "strcpy",
    "sprintf",
    "scanf",
    "while",
    "for",
    "if",
    "return",
    "NULL",
    "goto",
    "sizeof",
    "->",
    "[",
    "*",
    "error",
    "len",
    "size",
    "ptr",
    "alloc",
    "copy",
    "break",
    "continue",
    "case",
    "switch",
    "assert",
    "BUG",
    "EINVAL",
)


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
    request = Request(url, headers={"User-Agent": "OC research pipeline-OC133-CodeXGLUE-Research-Cache/1.0"})
    with urlopen(request, timeout=180) as response:
        return response.read().decode("utf-8", errors="replace")


def acquire(root: Path, *, write: bool) -> dict[str, Any]:
    functions_text = fetch_text(FUNCTIONS_URL)
    train_ids_text = fetch_text(TRAIN_IDS_URL)
    test_ids_text = fetch_text(TEST_IDS_URL)
    functions = json.loads(functions_text)
    train_ids = [int(value) for value in train_ids_text.split()]
    test_ids = [int(value) for value in test_ids_text.split()]
    lock = {
        "schema_id": "OC133_CODEXGLUE_DEFECT_SOURCE_LOCK_v1",
        "source_authority": "CodeXGLUE / Devign defect-detection corpus",
        "source_urls": {
            "function_json": FUNCTIONS_URL,
            "train_ids": TRAIN_IDS_URL,
            "test_ids": TEST_IDS_URL,
        },
        "source_refs": {
            "function_json": FUNCTIONS_REL,
            "train_ids": TRAIN_IDS_REL,
            "test_ids": TEST_IDS_REL,
        },
        "source_hashes": {
            "function_json_sha256": sha256_text(functions_text),
            "train_ids_sha256": sha256_text(train_ids_text),
            "test_ids_sha256": sha256_text(test_ids_text),
        },
        "function_total": len(functions),
        "train_id_total": len(train_ids),
        "test_id_total": len(test_ids),
        "target_fields_hidden": ["defect_target"],
        "target_hidden_until_scoring": True,
        "coverage_closure_allowed": False,
    }
    if write:
        (root / FUNCTIONS_REL).parent.mkdir(parents=True, exist_ok=True)
        (root / FUNCTIONS_REL).write_text(functions_text, encoding="utf-8", newline="\n")
        (root / TRAIN_IDS_REL).write_text(train_ids_text, encoding="utf-8", newline="\n")
        (root / TEST_IDS_REL).write_text(test_ids_text, encoding="utf-8", newline="\n")
        write_json(root / LOCK_REL, lock)
    return {"functions": functions, "train_ids": train_ids, "test_ids": test_ids, "lock": lock}


def load_source(root: Path) -> tuple[list[dict[str, Any]], list[int], list[int], dict[str, Any]]:
    if not (root / FUNCTIONS_REL).exists() or not (root / TRAIN_IDS_REL).exists() or not (root / TEST_IDS_REL).exists():
        payload = acquire(root, write=True)
        return payload["functions"], payload["train_ids"], payload["test_ids"], payload["lock"]
    functions = read_json(root / FUNCTIONS_REL)
    train_ids = [int(value) for value in (root / TRAIN_IDS_REL).read_text(encoding="utf-8").split()]
    test_ids = [int(value) for value in (root / TEST_IDS_REL).read_text(encoding="utf-8").split()]
    lock = read_json(root / LOCK_REL)
    return functions, train_ids, test_ids, lock


def feature_vector(source_code: str) -> list[float]:
    return [float(source_code.count(token)) for token in TOKENS] + [
        float(len(source_code)),
        float(source_code.count("\n")),
        float(sum(char.isdigit() for char in source_code)),
    ]


def build_task_table(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    functions, train_ids, test_ids, _lock = load_source(root)
    visible_rows = []
    hidden_rows = []
    for split, ids in (("train_visible", train_ids), ("hidden_score", test_ids)):
        for function_id in ids:
            record = functions[function_id]
            task_id = f"CODEXGLUE-DEFECT-{function_id:05d}"
            features = {f"feature_{index:02d}": value for index, value in enumerate(feature_vector(record["func"]))}
            visible_rows.append(
                {
                    "task_id": task_id,
                    "function_id": function_id,
                    "split": split,
                    "project": record.get("project", ""),
                    "commit_id_sha256": sha256_text(str(record.get("commit_id", ""))),
                    "features": features,
                    "source_row_sha256": sha256_object(
                        {
                            "function_id": function_id,
                            "project": record.get("project", ""),
                            "func_sha256": sha256_text(record["func"]),
                        }
                    ),
                }
            )
            hidden_rows.append(
                {
                    "task_id": task_id,
                    "function_id": function_id,
                    "defect_target": int(record["target"]),
                    "target_sha256": sha256_object({"task_id": task_id, "defect_target": int(record["target"])}),
                }
            )
    task_table = {
        "schema_id": "OC133_CODEXGLUE_DEFECT_TARGET_HIDDEN_TASK_TABLE_v1",
        "source_lock_ref": LOCK_REL,
        "row_count": len(visible_rows),
        "train_visible_row_count": len(train_ids),
        "hidden_score_row_count": len(test_ids),
        "target_hidden_until_scoring": True,
        "coverage_closure_allowed": False,
        "model": {
            "model_id": "CODEXGLUE-DEFECT-RIDGE-TOKEN-SEMANTICS-v1",
            "rule": "Ridge linear probability scorer over source-code lexical/control-flow token counts.",
        },
        "comparator": {
            "comparator_id": "CODEXGLUE-DEFECT-TRAINING-MAJORITY-v1",
            "rule": "Predict every hidden function with the training majority defect label.",
        },
        "visible_rows": visible_rows,
    }
    target_lock = {
        "schema_id": "OC133_CODEXGLUE_DEFECT_HIDDEN_TARGET_LOCK_v1",
        "source_lock_ref": LOCK_REL,
        "visible_task_table_ref": TASK_TABLE_REL,
        "hidden_target_count": len(hidden_rows),
        "hidden_targets_sha256": sha256_object(hidden_rows),
        "target_hidden_until_scoring": True,
        "coverage_closure_allowed": False,
        "hidden_rows": hidden_rows,
    }
    return task_table, target_lock


def train_ridge(train_rows: list[dict[str, Any]], target_by_task: dict[str, int]) -> dict[str, Any]:
    feature_names = list(train_rows[0]["features"].keys())
    matrix = np.array([[float(row["features"][feature]) for feature in feature_names] for row in train_rows], dtype=float)
    targets = np.array([float(target_by_task[row["task_id"]]) for row in train_rows], dtype=float)
    means = matrix.mean(axis=0)
    stds = matrix.std(axis=0)
    stds[stds == 0] = 1.0
    normalized = (matrix - means) / stds
    augmented = np.c_[np.ones(len(normalized)), normalized]
    ridge_lambda = 1.0
    normal = augmented.T @ augmented + ridge_lambda * np.eye(augmented.shape[1])
    normal[0, 0] -= ridge_lambda
    coefficients = np.linalg.solve(normal, augmented.T @ targets)
    return {
        "feature_names": feature_names,
        "feature_means": {feature: float(value) for feature, value in zip(feature_names, means)},
        "feature_stds": {feature: float(value) for feature, value in zip(feature_names, stds)},
        "intercept": float(coefficients[0]),
        "coefficients": {feature: float(value) for feature, value in zip(feature_names, coefficients[1:])},
        "ridge_lambda": ridge_lambda,
    }


def predict(row: dict[str, Any], model: dict[str, Any]) -> int:
    score = float(model["intercept"])
    for feature in model["feature_names"]:
        value = (float(row["features"][feature]) - float(model["feature_means"][feature])) / float(model["feature_stds"][feature])
        score += float(model["coefficients"][feature]) * value
    return int(score >= 0.5)


def score(root: Path, *, write: bool) -> dict[str, Any]:
    task_table, target_lock = build_task_table(root)
    target_by_task = {row["task_id"]: int(row["defect_target"]) for row in target_lock["hidden_rows"]}
    train_rows = [row for row in task_table["visible_rows"] if row["split"] == "train_visible"]
    hidden_rows = [row for row in task_table["visible_rows"] if row["split"] == "hidden_score"]
    model = train_ridge(train_rows, target_by_task)
    majority = int(sum(target_by_task[row["task_id"]] for row in train_rows) >= (len(train_rows) / 2))
    target_hash_by_task = {row["task_id"]: row["target_sha256"] for row in target_lock["hidden_rows"]}
    model_losses = []
    comparator_losses = []
    negative_losses = []
    scored_rows = []
    for row in hidden_rows:
        target = target_by_task[row["task_id"]]
        model_prediction = predict(row, model)
        comparator_prediction = majority
        negative_prediction = 1 - model_prediction
        model_loss = 0.0 if model_prediction == target else 1.0
        comparator_loss = 0.0 if comparator_prediction == target else 1.0
        negative_loss = 0.0 if negative_prediction == target else 1.0
        model_losses.append(model_loss)
        comparator_losses.append(comparator_loss)
        negative_losses.append(negative_loss)
        scored_rows.append(
            {
                "task_id": row["task_id"],
                "function_id": row["function_id"],
                "model_prediction": model_prediction,
                "comparator_prediction": comparator_prediction,
                "negative_control_prediction": negative_prediction,
                "model_loss": model_loss,
                "comparator_loss": comparator_loss,
                "negative_control_loss": negative_loss,
                "target_sha256": target_hash_by_task[row["task_id"]],
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
        "schema_id": "OC133_CODEXGLUE_DEFECT_SCORING_PACK_v1",
        "pack_status": pack_status,
        "status": pack_status,
        "domain_class_id": "computer_information_sciences",
        "phenomenon_class_id": "program_semantics_and_verification",
        "source_bound": True,
        "target_hidden": True,
        "score_materialized": True,
        "scientific_pass": pack_status == "STRICT_EVIDENCE_PASS_NO_COVERAGE_CLOSURE",
        "coverage_closure_allowed": False,
        "support_allowed_for_broad_coverage": False,
        "source_snapshot_ref": FUNCTIONS_REL,
        "source_snapshot_sha256": sha256_text((root / FUNCTIONS_REL).read_text(encoding="utf-8")),
        "source_lock_ref": LOCK_REL,
        "source_lock_sha256": sha256_object(read_json(root / LOCK_REL)),
        "visible_task_table_ref": TASK_TABLE_REL,
        "hidden_target_lock_ref": TARGET_LOCK_REL,
        "row_count": len(scored_rows),
        "model": {"model_id": "CODEXGLUE-DEFECT-RIDGE-TOKEN-SEMANTICS-v1", "model": model},
        "comparator": {"comparator_id": "CODEXGLUE-DEFECT-TRAINING-MAJORITY-v1", "majority_label": majority},
        "residuals": {
            "model": round(model_loss, 12),
            "comparator": round(comparator_loss, 12),
            "negative_control": round(negative_loss, 12),
            "material_margin_met": material_margin_met,
            "material_margin_rule": f"0/1 loss + {MATERIAL_MARGIN} must be below training-majority comparator loss",
        },
        "negative_control": {
            "control_id": "CODEXGLUE-DEFECT-OPPOSITE-PREDICTION-CONTROL-v1",
            "negative_control_rejected": negative_control_rejected,
        },
        "falsifiers": [
            "source lock hash is missing or stale",
            "hidden defect targets appear in visible task rows",
            "token semantics scorer does not beat training majority comparator",
            "opposite-prediction negative control is not worse than the model",
        ],
        "replay_command": {
            "commands": [
                f"python {SCRIPT_REL} --score --write-scoring",
                f"python {SCRIPT_REL} --check",
            ]
        },
        "scored_rows_sha256": sha256_object(scored_rows),
        "scored_rows_sample": scored_rows[:10],
    }
    replay_report = {
        "schema_id": "OC133_CODEXGLUE_DEFECT_REPLAY_REPORT_v1",
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
    for rel_path in (FUNCTIONS_REL, TRAIN_IDS_REL, TEST_IDS_REL, LOCK_REL):
        if not (root / rel_path).exists():
            errors.append(f"missing {rel_path}")
    if errors:
        return errors
    lock = read_json(root / LOCK_REL)
    if lock.get("source_hashes", {}).get("function_json_sha256") != sha256_text((root / FUNCTIONS_REL).read_text(encoding="utf-8")):
        errors.append("function.json hash mismatch")
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
        errors.append("CodeXGLUE defect scoring pack is fail-closed")
    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Materialize CodeXGLUE defect target-hidden program-semantics evidence.")
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
        print(json.dumps({"function_total": len(payload["functions"]), "train_id_total": len(payload["train_ids"]), "test_id_total": len(payload["test_ids"])}, indent=2))
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
        print("codexglue_defect: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
