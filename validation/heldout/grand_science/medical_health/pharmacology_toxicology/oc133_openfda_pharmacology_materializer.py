from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


SCRIPT_REL = (
    "validation/heldout/grand_science/medical_health/pharmacology_toxicology/"
    "oc133_openfda_pharmacology_materializer.py"
)
ROOT_REL = "validation/heldout/grand_science/medical_health/pharmacology_toxicology"
SNAPSHOT_REL = f"{ROOT_REL}/OC133_OPENFDA_DRUG_EVENT_SNAPSHOT.json"
LOCK_REL = f"{ROOT_REL}/OC133_OPENFDA_DRUG_EVENT_SNAPSHOT.lock.json"
TASK_TABLE_REL = f"{ROOT_REL}/OC133_OPENFDA_DRUG_EVENT_TARGET_HIDDEN_TASK_TABLE.json"
TARGET_LOCK_REL = f"{ROOT_REL}/OC133-OPENFDA-DRUG-EVENT-HIDDEN-TARGETS-0001.lock.json"
SCORING_PACK_REL = f"{ROOT_REL}/OC133_OPENFDA_DRUG_EVENT_TARGET_HIDDEN_REPLAY_SCORER_EVIDENCE_PACK.json"
REPLAY_REPORT_REL = f"{ROOT_REL}/OC133_OPENFDA_DRUG_EVENT_REPLAY_REPORT.json"

SOURCE_ENDPOINT_BASE = "https://api.fda.gov/drug/event.json"
SOURCE_QUERY = "receivedate:[20240101 TO 20241231]"
PAGE_LIMIT = 100
PAGE_SKIPS = tuple(range(0, 1000, PAGE_LIMIT))
TRAIN_ROWS = 500
MATERIAL_MARGIN = 0.05


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


def endpoint_url(skip: int) -> str:
    return SOURCE_ENDPOINT_BASE + "?" + urlencode({"search": SOURCE_QUERY, "limit": PAGE_LIMIT, "skip": skip})


def fetch_json(url: str, timeout: int = 90) -> dict[str, Any]:
    last_error: Exception | None = None
    for attempt in range(1, 4):
        try:
            request = Request(url, headers={"User-Agent": "OC research pipeline-OC133-openFDA-Research-Cache/1.0"})
            with urlopen(request, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as error:
            last_error = error
            if attempt < 3:
                time.sleep(float(attempt))
    assert last_error is not None
    raise last_error


def numeric(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def first_drug_route(drugs: list[dict[str, Any]]) -> str:
    for drug in drugs:
        route = drug.get("drugadministrationroute")
        if route:
            return str(route)
    return ""


def max_structured_dose(drugs: list[dict[str, Any]]) -> float:
    values = []
    for drug in drugs:
        value = numeric(drug.get("drugstructuredosagenumb"))
        if value > 0:
            values.append(value)
    return max(values) if values else 0.0


def parse_event(event: dict[str, Any]) -> dict[str, Any] | None:
    report_id = str(event.get("safetyreportid") or "")
    patient = event.get("patient", {}) if isinstance(event.get("patient"), dict) else {}
    drugs = patient.get("drug", []) if isinstance(patient.get("drug"), list) else []
    reactions = patient.get("reaction", []) if isinstance(patient.get("reaction"), list) else []
    if not report_id or not drugs or not reactions:
        return None
    serious_raw = str(event.get("serious") or "")
    if serious_raw not in {"1", "2"}:
        return None
    visible = {
        "safetyreportid": report_id,
        "receivedate": str(event.get("receivedate") or ""),
        "patientonsetage": numeric(patient.get("patientonsetage")),
        "patientsex": str(patient.get("patientsex") or ""),
        "patientagegroup": str(patient.get("patientagegroup") or ""),
        "drug_count": len(drugs),
        "reaction_count": len(reactions),
        "max_structured_dose": max_structured_dose(drugs),
        "first_administration_route": first_drug_route(drugs),
        "primary_drug_characterization": str(drugs[0].get("drugcharacterization") or ""),
        "primary_drug_indication_present": bool(drugs[0].get("drugindication")),
    }
    target = {
        "safetyreportid": report_id,
        "serious": 1 if serious_raw == "1" else 0,
    }
    return {
        "visible": visible,
        "target": target,
        "source_row_sha256": sha256_object({"visible": visible, "target": target}),
    }


def acquire(root: Path, *, write: bool) -> dict[str, Any]:
    events: dict[str, dict[str, Any]] = {}
    endpoint_refs = []
    for skip in PAGE_SKIPS:
        url = endpoint_url(skip)
        payload = fetch_json(url)
        endpoint_refs.append({"skip": skip, "endpoint_url": url, "result_count": len(payload.get("results", []))})
        for event in payload.get("results", []):
            if not isinstance(event, dict):
                continue
            parsed = parse_event(event)
            if not parsed:
                continue
            events[parsed["visible"]["safetyreportid"]] = parsed
        time.sleep(0.2)
    rows = [events[key] for key in sorted(events)]
    source_rows = []
    for row in rows:
        item = {
            **row["visible"],
            "source_row_sha256": row["source_row_sha256"],
        }
        item["row_sha256"] = sha256_object(item)
        source_rows.append(item)
    hidden_targets = [row["target"] for row in rows]
    snapshot = {
        "schema_id": "OC133_OPENFDA_DRUG_EVENT_SOURCE_SNAPSHOT_v1",
        "source_id": "openfda_faers_drug_event_v1",
        "source_name": "openFDA drug adverse event endpoint",
        "source_authority": "U.S. Food and Drug Administration openFDA",
        "official_documentation_url": "https://open.fda.gov/apis/drug/event/how-to-use-the-endpoint/",
        "endpoint_pages": endpoint_refs,
        "row_count": len(source_rows),
        "target_values_scored": False,
        "target_hidden_until_scoring": True,
        "coverage_closure_allowed": False,
        "rows": source_rows,
        "rows_sha256": sha256_object(source_rows),
    }
    lock = {
        "schema_id": "OC133_OPENFDA_DRUG_EVENT_SOURCE_LOCK_v1",
        "source_snapshot_ref": SNAPSHOT_REL,
        "source_snapshot_sha256": sha256_object(snapshot),
        "row_count": len(source_rows),
        "visible_fields": [
            "safetyreportid",
            "receivedate",
            "patientonsetage",
            "patientsex",
            "patientagegroup",
            "drug_count",
            "reaction_count",
            "max_structured_dose",
            "first_administration_route",
            "primary_drug_characterization",
            "primary_drug_indication_present",
        ],
        "target_fields_hidden": ["serious"],
        "hidden_targets_sha256": sha256_object(hidden_targets),
        "target_values_scored": False,
        "target_hidden_until_scoring": True,
        "coverage_closure_allowed": False,
    }
    if write:
        write_json(root / SNAPSHOT_REL, snapshot)
        write_json(root / LOCK_REL, lock)
    return {"snapshot": snapshot, "lock": lock, "hidden_targets": hidden_targets}


def load_source(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    if not (root / SNAPSHOT_REL).exists() or not (root / LOCK_REL).exists():
        acquire(root, write=True)
    return read_json(root / SNAPSHOT_REL), read_json(root / LOCK_REL)


def build_task_table(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    snapshot, lock = load_source(root)
    rows = snapshot.get("rows", [])
    if len(rows) < TRAIN_ROWS + 100:
        raise RuntimeError(f"openFDA snapshot has too few scoreable rows: {len(rows)}")
    visible_rows = []
    hidden_rows = []
    for index, row in enumerate(rows):
        task_id = f"OPENFDA-DRUG-EVENT-{row['safetyreportid']}"
        visible = {key: value for key, value in row.items() if key not in {"row_sha256"}}
        visible["task_id"] = task_id
        visible["split"] = "train_visible" if index < TRAIN_ROWS else "hidden_score"
        visible_rows.append(visible)
        hidden_rows.append(
            {
                "task_id": task_id,
                "safetyreportid": row["safetyreportid"],
                "serious": None,
                "source_row_sha256": row["source_row_sha256"],
            }
        )
    existing_target_lock_path = root / TARGET_LOCK_REL
    if existing_target_lock_path.exists():
        existing_target_lock = read_json(existing_target_lock_path)
        existing_hidden_rows = existing_target_lock.get("hidden_rows", [])
        existing_by_report = {
            str(row.get("safetyreportid")): row
            for row in existing_hidden_rows
            if isinstance(row, dict) and row.get("safetyreportid")
        }
        expected_reports = {str(row["safetyreportid"]) for row in rows}
        if expected_reports.issubset(set(existing_by_report)):
            target_by_report = {
                report_id: int(existing_by_report[report_id]["serious"])
                for report_id in expected_reports
            }
        else:
            target_by_report = {}
    else:
        target_by_report = {}
    if not target_by_report:
        source_targets = acquire(root, write=False)["hidden_targets"]
        target_by_report = {row["safetyreportid"]: row["serious"] for row in source_targets}
    target_lock_rows = []
    for row in rows:
        task_id = f"OPENFDA-DRUG-EVENT-{row['safetyreportid']}"
        target_lock_rows.append(
            {
                "task_id": task_id,
                "safetyreportid": row["safetyreportid"],
                "serious": target_by_report.get(row["safetyreportid"]),
                "source_row_sha256": row["source_row_sha256"],
            }
        )
    task_table = {
        "schema_id": "OC133_OPENFDA_DRUG_EVENT_TARGET_HIDDEN_TASK_TABLE_v1",
        "source_snapshot_ref": SNAPSHOT_REL,
        "source_lock_ref": LOCK_REL,
        "row_count": len(visible_rows),
        "train_visible_row_count": TRAIN_ROWS,
        "hidden_score_row_count": len(visible_rows) - TRAIN_ROWS,
        "target_hidden_until_scoring": True,
        "coverage_closure_allowed": False,
        "model": {
            "model_id": "MED-OPENFDA-TRAINED-RISK-SCORE-v1",
            "rule": "Fit a low-dimensional risk-score threshold on the first locked visible rows; score later hidden rows without reading hidden seriousness labels.",
        },
        "comparator": {
            "comparator_id": "MED-OPENFDA-TRAIN-MAJORITY-CLASS-v1",
            "rule": "Predict every hidden row as the majority serious/non-serious class in the visible training rows.",
        },
        "visible_rows": visible_rows,
    }
    target_lock = {
        "schema_id": "OC133_OPENFDA_DRUG_EVENT_HIDDEN_TARGET_LOCK_v1",
        "source_snapshot_ref": SNAPSHOT_REL,
        "source_lock_ref": LOCK_REL,
        "visible_task_table_ref": TASK_TABLE_REL,
        "hidden_target_count": len(target_lock_rows),
        "hidden_targets_sha256": sha256_object(target_lock_rows),
        "target_hidden_until_scoring": True,
        "coverage_closure_allowed": False,
        "hidden_rows": target_lock_rows,
    }
    return task_table, target_lock


def feature_score(row: dict[str, Any], weights: dict[str, float]) -> float:
    return (
        weights["age"] * numeric(row.get("patientonsetage"))
        + weights["drug_count"] * numeric(row.get("drug_count"))
        + weights["reaction_count"] * numeric(row.get("reaction_count"))
        + weights["dose"] * numeric(row.get("max_structured_dose"))
    )


def train_model(train_rows: list[dict[str, Any]], target_by_task: dict[str, int]) -> dict[str, Any]:
    candidates = []
    for age in (0.0, 0.005, 0.01, 0.02, 0.03):
        for drug_count in (0.0, 0.05, 0.1, 0.2, 0.4):
            for reaction_count in (0.0, 0.05, 0.1, 0.2, 0.4):
                for dose in (0.0, 0.0001, 0.001, 0.01):
                    weights = {
                        "age": age,
                        "drug_count": drug_count,
                        "reaction_count": reaction_count,
                        "dose": dose,
                    }
                    scores = [feature_score(row, weights) for row in train_rows]
                    ordered = sorted(scores)
                    for quantile in (0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8):
                        threshold = ordered[int(quantile * (len(ordered) - 1))]
                        predictions = [1 if score >= threshold else 0 for score in scores]
                        errors = [
                            1.0 if pred != int(target_by_task[row["task_id"]]) else 0.0
                            for pred, row in zip(predictions, train_rows)
                        ]
                        candidates.append(
                            {
                                "train_error": sum(errors) / len(errors),
                                "weights": weights,
                                "threshold_quantile": quantile,
                                "threshold": threshold,
                            }
                        )
    candidates.sort(key=lambda row: (row["train_error"], row["threshold_quantile"], canonical_json(row["weights"])))
    return candidates[0]


def reverse_permuted_training_targets(train_rows: list[dict[str, Any]], target_by_task: dict[str, int]) -> dict[str, int]:
    task_ids = sorted(str(row["task_id"]) for row in train_rows)
    target_values = [int(target_by_task[task_id]) for task_id in task_ids]
    permuted = dict(zip(task_ids, reversed(target_values)))
    return {**target_by_task, **permuted}


def score(root: Path, *, write: bool) -> dict[str, Any]:
    snapshot, lock = load_source(root)
    task_table, target_lock = build_task_table(root)
    target_by_task = {row["task_id"]: int(row["serious"]) for row in target_lock["hidden_rows"]}
    train_rows = [row for row in task_table["visible_rows"] if row["split"] == "train_visible"]
    hidden_rows = [row for row in task_table["visible_rows"] if row["split"] == "hidden_score"]
    model = train_model(train_rows, target_by_task)
    train_serious_rate = sum(target_by_task[row["task_id"]] for row in train_rows) / len(train_rows)
    comparator_prediction = 1 if train_serious_rate >= 0.5 else 0
    negative_control_targets = reverse_permuted_training_targets(train_rows, target_by_task)
    negative_control_model = train_model(train_rows, negative_control_targets)
    scored_rows = []
    model_errors = []
    comparator_errors = []
    negative_control_errors = []
    for row in hidden_rows:
        target = target_by_task[row["task_id"]]
        model_prediction = 1 if feature_score(row, model["weights"]) >= float(model["threshold"]) else 0
        negative_control_prediction = (
            1
            if feature_score(row, negative_control_model["weights"])
            >= float(negative_control_model["threshold"])
            else 0
        )
        model_error = 1.0 if model_prediction != target else 0.0
        comparator_error = 1.0 if comparator_prediction != target else 0.0
        negative_control_error = 1.0 if negative_control_prediction != target else 0.0
        model_errors.append(model_error)
        comparator_errors.append(comparator_error)
        negative_control_errors.append(negative_control_error)
        scored_rows.append(
            {
                "task_id": row["task_id"],
                "safetyreportid": row["safetyreportid"],
                "model_prediction_serious": model_prediction,
                "comparator_prediction_serious": comparator_prediction,
                "negative_control_prediction_serious": negative_control_prediction,
                "target_sha256": sha256_object(
                    {
                        "task_id": row["task_id"],
                        "safetyreportid": row["safetyreportid"],
                        "serious": target,
                    }
                ),
                "model_0_1_loss": model_error,
                "comparator_0_1_loss": comparator_error,
                "negative_control_0_1_loss": negative_control_error,
            }
        )
    row_count = len(scored_rows)
    model_loss = sum(model_errors) / row_count
    comparator_loss = sum(comparator_errors) / row_count
    negative_control_loss = sum(negative_control_errors) / row_count
    material_margin_met = model_loss + MATERIAL_MARGIN < comparator_loss
    negative_control_rejected = negative_control_loss > model_loss
    pack_status = "STRICT_EVIDENCE_PASS_NO_COVERAGE_CLOSURE" if material_margin_met and negative_control_rejected else "STRICT_EVIDENCE_FAIL_CLOSED"
    scoring_pack = {
        "schema_id": "OC133_OPENFDA_DRUG_EVENT_SCORING_PACK_v1",
        "pack_status": pack_status,
        "status": pack_status,
        "domain_class_id": "medical_health_sciences",
        "phenomenon_class_id": "pharmacology_toxicology_and_dose_response",
        "source_bound": True,
        "target_hidden": True,
        "score_materialized": True,
        "scientific_pass": pack_status == "STRICT_EVIDENCE_PASS_NO_COVERAGE_CLOSURE",
        "coverage_closure_allowed": False,
        "support_allowed_for_broad_coverage": False,
        "source_snapshot_ref": SNAPSHOT_REL,
        "source_snapshot_sha256": lock["source_snapshot_sha256"],
        "source_lock_ref": LOCK_REL,
        "visible_task_table_ref": TASK_TABLE_REL,
        "hidden_target_lock_ref": TARGET_LOCK_REL,
        "row_count": row_count,
        "train_visible_row_count": len(train_rows),
        "model": {
            "model_id": "MED-OPENFDA-TRAINED-RISK-SCORE-v1",
            "training_only_parameters": model,
        },
        "comparator": {
            "comparator_id": "MED-OPENFDA-TRAIN-MAJORITY-CLASS-v1",
            "train_serious_rate": round(train_serious_rate, 12),
            "prediction": comparator_prediction,
        },
        "residuals": {
            "model": round(model_loss, 12),
            "comparator": round(comparator_loss, 12),
            "negative_control": round(negative_control_loss, 12),
            "material_margin_met": material_margin_met,
            "material_margin_rule": (
                f"model_0_1_loss + {MATERIAL_MARGIN} must be below the train-majority comparator loss"
            ),
        },
        "negative_control": {
            "control_id": "MED-OPENFDA-REVERSED-TRAINING-TARGET-CONTROL-v1",
            "control_model": negative_control_model,
            "negative_control_rejected": negative_control_rejected,
        },
        "falsifiers": [
            "hidden serious labels appear in visible task table",
            "source lock hash is missing or stale",
            "model 0/1 loss plus material margin is not below comparator loss",
            "negative control is not worse than the model",
        ],
        "scored_rows_sha256": sha256_object(scored_rows),
        "scored_rows_sample": scored_rows[:10],
    }
    replay_report = {
        "schema_id": "OC133_OPENFDA_DRUG_EVENT_REPLAY_REPORT_v1",
        "status": "PASS" if scoring_pack["scientific_pass"] else "FAIL_CLOSED",
        "scoring_pack_ref": SCORING_PACK_REL,
        "scoring_pack_sha256": sha256_object(scoring_pack),
        "row_count": row_count,
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
    for rel_path in (SNAPSHOT_REL, LOCK_REL):
        if not (root / rel_path).exists():
            errors.append(f"missing {rel_path}")
    if errors:
        return errors
    snapshot, lock = load_source(root)
    if lock.get("source_snapshot_sha256") != sha256_object(snapshot):
        errors.append("source snapshot hash mismatch")
    score_payload = score(root, write=False)
    expected_task_table, expected_target_lock = build_task_table(root)
    for rel_path, expected in (
        (TASK_TABLE_REL, expected_task_table),
        (TARGET_LOCK_REL, expected_target_lock),
        (SCORING_PACK_REL, score_payload["scoring_pack"]),
        (REPLAY_REPORT_REL, score_payload["replay_report"]),
    ):
        path = root / rel_path
        if not path.exists():
            errors.append(f"missing {rel_path}")
        elif read_json(path) != expected:
            errors.append(f"stale {rel_path}")
    if score_payload["scoring_pack"].get("scientific_pass") is not True:
        errors.append("openFDA pharmacology scoring pack is fail-closed")
    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Materialize target-hidden openFDA pharmacology evidence.")
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
        print(json.dumps({"snapshot_rows": payload["snapshot"]["row_count"]}, indent=2))
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
        print("openFDA pharmacology: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
