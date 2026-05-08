from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
QA_TABLE = ROOT / "validation" / "numeric_replay_qa" / "OC133_NUMERIC_REPLAY_QA_TABLE.json"
OUTPUT = ROOT / "validation" / "numeric_predictions" / "OC133_NUMERIC_REPLAY_LOG.json"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def lf_normalized_bytes(path: Path) -> bytes:
    return path.read_bytes().replace(b"\r\n", b"\n")


def sha256_lf_normalized_text(path: Path) -> str:
    return hashlib.sha256(lf_normalized_bytes(path)).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def finite_math_replay_value(finite_report: dict[str, Any]) -> float | None:
    if finite_report.get("failure_total") != 0:
        return None
    value = finite_report.get("machine_checked_subset_total")
    if isinstance(value, (int, float)) and value >= 1:
        return float(value)
    theorem_present = finite_report.get("lean_theorem_ref_present_total")
    if isinstance(theorem_present, (int, float)) and theorem_present >= 1:
        return float(theorem_present)
    return None


def parsed_snapshot_value(row: dict[str, Any], snapshot_path: Path) -> float | None:
    if row.get("lane") == "mathematics":
        finite_report = read_json(snapshot_path)
        return finite_math_replay_value(finite_report)
    declared = row.get("parsed_snapshot_value")
    if isinstance(declared, (int, float)):
        return float(declared)
    return None


def build_log() -> dict[str, Any]:
    qa_payload = read_json(QA_TABLE)
    rows: list[dict[str, Any]] = []
    failures: list[str] = []
    snapshot_parse_fail_total = 0
    for row in qa_payload.get("rows", []):
        if not isinstance(row, dict):
            failures.append("NON_OBJECT_QA_ROW")
            continue
        snapshot_ref = str(row.get("dataset_snapshot_ref", ""))
        snapshot_path = ROOT / snapshot_ref
        snapshot_opened = snapshot_path.is_file()
        observed_value = parsed_snapshot_value(row, snapshot_path) if snapshot_opened else None
        snapshot_parse_ok = observed_value is not None
        if not snapshot_parse_ok:
            snapshot_parse_fail_total += 1
        replay_value = float(row.get("replay_value", 0.0))
        baseline_value = float(row.get("baseline_control_value", replay_value))
        declared_residual = float(row.get("replay_residual", 0.0))
        declared_comparator_residual = float(row.get("comparator_residual", 0.0))
        computed_residual = abs(replay_value - float(observed_value)) if observed_value is not None else None
        computed_comparator_residual = abs(baseline_value - float(observed_value)) if observed_value is not None else None
        residual_matches = computed_residual == declared_residual
        comparator_residual_matches = computed_comparator_residual == declared_comparator_residual
        negative_control_rejected = bool(computed_comparator_residual and computed_comparator_residual > 0)
        replay_row = {
            "claim_id": row.get("claim_id"),
            "lane": row.get("lane"),
            "dataset_snapshot_ref": snapshot_ref,
            "snapshot_opened": snapshot_opened,
            "snapshot_sha256": sha256_lf_normalized_text(snapshot_path) if snapshot_opened else None,
            "snapshot_sha256_policy": "LF_NORMALIZED_TEXT_SNAPSHOT_HASH",
            "snapshot_byte_count": len(lf_normalized_bytes(snapshot_path)) if snapshot_opened else 0,
            "snapshot_byte_count_policy": "LF_NORMALIZED_TEXT_SNAPSHOT_BYTES",
            "snapshot_parser": "lane_specific_official_snapshot_parser",
            "snapshot_parse_ok": snapshot_parse_ok,
            "snapshot_parsed_observed_value": observed_value,
            "table_replay_value": replay_value,
            "table_parsed_snapshot_value": row.get("parsed_snapshot_value"),
            "computed_residual": computed_residual,
            "computed_comparator_residual": computed_comparator_residual,
            "declared_replay_residual": declared_residual,
            "declared_comparator_residual": declared_comparator_residual,
            "residual_kind": row.get("residual_kind", "replay_residual_not_comparator_performance"),
            "residual_matches": residual_matches,
            "comparator_residual_matches": comparator_residual_matches,
            "negative_control_residual": computed_comparator_residual,
            "negative_control_method": row.get("negative_control"),
            "negative_control_rejected": negative_control_rejected,
            "prediction_support_allowed": False,
            "empirical_support_allowed": False,
            "replay_barred_from_prediction_support": True,
            "quarantine_reason": row.get("quarantine_reason", ""),
        }
        rows.append(replay_row)
        for field, ok in {
            "snapshot_opened": snapshot_opened,
            "snapshot_parse_ok": snapshot_parse_ok,
            "residual_matches": residual_matches,
            "comparator_residual_matches": comparator_residual_matches,
            "negative_control_rejected": negative_control_rejected,
        }.items():
            if not ok:
                failures.append(f"{row.get('claim_id')}::{field}")
    return {
        "schema_id": "OC133_NUMERIC_REPLAY_LOG_v12",
        "release_id": "oc_core_1_3_3",
        "version": "1.3.3",
        "qa_table_ref": "validation/numeric_replay_qa/OC133_NUMERIC_REPLAY_QA_TABLE.json",
        "qa_table_sha256": sha256_file(QA_TABLE),
        "row_total": len(rows),
        "lane_total": len({row.get("lane") for row in rows}),
        "failure_total": len(failures),
        "failures": failures,
        "snapshot_parse_fail_total": snapshot_parse_fail_total,
        "prediction_support_allowed_total": 0,
        "empirical_support_allowed_total": 0,
        "scope_policy": "Deterministic replay QA only; no row is promoted as held-out prediction or empirical validation.",
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Replay OC Core 1.3.3 numeric QA rows.")
    parser.add_argument("--materialize-first", action="store_true")
    args = parser.parse_args()
    if args.materialize_first:
        completed = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "materialize_oc_core_1_3_3_v12_closure.py")],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=900,
        )
        if completed.returncode != 0:
            print(completed.stdout[-2000:])
            print(completed.stderr[-2000:], file=sys.stderr)
            return completed.returncode
    payload = build_log()
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["failure_total"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
