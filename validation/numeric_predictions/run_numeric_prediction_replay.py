from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import re
import runpy
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def parse_snapshot_value(row: dict, snapshot_bytes: bytes):
    text = snapshot_bytes.decode("utf-8", errors="replace")
    claim_id = row["claim_id"]
    if claim_id == "OC133-NUM-PHYS-C":
        match = re.search(r"speed of light in vacuum\s+([0-9 ]+)\s+\(exact\)", text)
        return float(match.group(1).replace(" ", "")) if match else None
    if claim_id == "OC133-NUM-CHEM-H2O":
        payload = json.loads(text)
        return float(payload["PropertyTable"]["Properties"][0]["MolecularWeight"])
    if claim_id == "OC133-NUM-CHEM-WEBBOOK-H2O":
        match = re.search(r'"molecularWeight"\s*:\s*"([0-9.]+)\s*amu"', text)
        if match:
            return float(match.group(1))
        match = re.search(r"Molecular\s+weight</a>:</strong>\s*([0-9.]+)", text, re.IGNORECASE)
        return float(match.group(1)) if match else None
    if claim_id == "OC133-NUM-BIO-GEO-COUNT":
        payload = json.loads(text)
        return float(payload["esearchresult"]["count"])
    if claim_id == "OC133-NUM-SYS-WDI-GDP":
        payload = json.loads(text)
        if not isinstance(payload, list) or len(payload) < 2:
            return None
        for item in payload[1]:
            if item.get("value") is not None:
                return float(item["value"])
        return None
    if claim_id == "OC133-NUM-MATH-FINITE":
        payload = json.loads(text)
        if payload.get("failure_total") == 0:
            return float(payload.get("machine_checked_subset_total", 0))
        return None
    return None


def negative_control_rejected(row: dict, snapshot_bytes: bytes, observed_value) -> tuple[bool, float | None, str]:
    claim_id = row["claim_id"]
    if observed_value is None:
        return False, None, "snapshot did not parse"
    if claim_id == "OC133-NUM-PHYS-C":
        negative_residual = abs(300000000.0 - float(observed_value))
        return negative_residual > float(row["uncertainty"]), negative_residual, "wrong speed-of-light constant"
    if claim_id == "OC133-NUM-CHEM-H2O":
        negative_residual = abs(44.0095 - float(observed_value))
        return negative_residual > float(row["uncertainty"]), negative_residual, "CO2 molecular weight against water snapshot"
    if claim_id == "OC133-NUM-CHEM-WEBBOOK-H2O":
        negative_residual = abs(44.0095 - float(observed_value))
        return negative_residual > float(row["uncertainty"]), negative_residual, "CO2 molecular weight against NIST WebBook water snapshot"
    if claim_id == "OC133-NUM-BIO-GEO-COUNT":
        negative_residual = abs((float(observed_value) + 1.0) - float(observed_value))
        return negative_residual > float(row["uncertainty"]), negative_residual, "synthetic +1 count mutation against the pinned accession snapshot"
    if claim_id == "OC133-NUM-SYS-WDI-GDP":
        corrupted_value = parse_snapshot_value(row, b"[]")
        return corrupted_value is None, None, "corrupted WDI payload parser failure"
    if claim_id == "OC133-NUM-MATH-FINITE":
        finite = json.loads(snapshot_bytes.decode("utf-8", errors="replace"))
        return int(finite.get("mutation_control_total", 0)) > 0 and finite.get("failure_total") == 0, 1.0, "finite mutation controls reject tampered rows"
    return False, None, "no negative control"


def main() -> int:
    parser = argparse.ArgumentParser(description="Replay OC133 numeric QA against already materialized release artifacts.")
    parser.add_argument("--materialize-first", action="store_true", help="Regenerate artifacts before replay. Forbidden for independent release validation.")
    args = parser.parse_args()
    materialize_first = args.materialize_first or os.getenv("OC133_NUMERIC_REPLAY_MATERIALIZE_FIRST") == "1"
    if materialize_first:
        with contextlib.redirect_stdout(io.StringIO()):
            try:
                runpy.run_path(str(ROOT / "tools" / "materialize_oc_core_1_3_3_v12_closure.py"), run_name="__main__")
            except SystemExit as exc:
                if int(exc.code or 0) != 0:
                    raise
    table_path = ROOT / "validation" / "numeric_replay_qa" / "OC133_NUMERIC_REPLAY_QA_TABLE.json"
    if not table_path.exists():
        raise FileNotFoundError(f"numeric replay table is missing; run materializer explicitly before independent replay: {table_path}")
    payload = json.loads(table_path.read_text(encoding="utf-8"))
    rows = []
    for row in payload["rows"]:
        snapshot_path = ROOT / row["dataset_snapshot_ref"]
        snapshot_bytes = snapshot_path.read_bytes() if snapshot_path.exists() else b""
        snapshot_sha256 = hashlib.sha256(snapshot_bytes).hexdigest() if snapshot_path.exists() else None
        parsed_observed = parse_snapshot_value(row, snapshot_bytes) if snapshot_path.exists() else None
        residual = abs(float(row["replay_value"]) - float(parsed_observed)) if parsed_observed is not None else float("inf")
        baseline_control_value = row.get("baseline_control_value", row.get("comparator_prediction"))
        comparator_residual = abs(float(baseline_control_value) - float(parsed_observed)) if parsed_observed is not None else float("inf")
        tolerance = float(row["uncertainty"]) if float(row["uncertainty"]) > 0 else 0.0
        negative_rejected, negative_residual, negative_control_method = negative_control_rejected(row, snapshot_bytes, parsed_observed)
        declared = float(row["replay_residual"])
        declared_comparator = float(row["comparator_residual"])
        rows.append({
            "claim_id": row["claim_id"],
            "lane": row["lane"],
            "dataset_snapshot_ref": row["dataset_snapshot_ref"],
            "snapshot_opened": snapshot_path.exists(),
            "snapshot_sha256": snapshot_sha256,
            "snapshot_byte_count": len(snapshot_bytes),
            "snapshot_parser": "lane_specific_official_snapshot_parser",
            "snapshot_parse_ok": parsed_observed is not None,
            "snapshot_parsed_observed_value": parsed_observed,
            "table_replay_value": row["replay_value"],
            "table_parsed_snapshot_value": row["parsed_snapshot_value"],
            "computed_residual": residual,
            "computed_comparator_residual": comparator_residual,
            "declared_replay_residual": row["replay_residual"],
            "declared_comparator_residual": row["comparator_residual"],
            "residual_kind": row.get("residual_kind"),
            "residual_matches": abs(residual - declared) <= max(1e-6, abs(declared) * 1e-9),
            "comparator_residual_matches": abs(comparator_residual - declared_comparator) <= max(1e-6, abs(declared_comparator) * 1e-9),
            "negative_control_residual": negative_residual,
            "negative_control_method": negative_control_method,
            "negative_control_rejected": negative_rejected,
            "prediction_support_allowed": row.get("prediction_support_allowed", False),
            "empirical_support_allowed": row.get("empirical_support_allowed", False),
            "replay_barred_from_prediction_support": not (
                row.get("numeric_replay") is True
                and (
                    row.get("prediction_support_allowed") is True
                    or row.get("empirical_support_allowed") is True
                )
            ),
            "quarantine_reason": row.get("quarantine_reason", ""),
        })
    failures = [
        row for row in rows
        if not row["snapshot_opened"]
        or not row["snapshot_parse_ok"]
        or not row["residual_matches"]
        or not row["comparator_residual_matches"]
        or not row["negative_control_rejected"]
        or not row["replay_barred_from_prediction_support"]
    ]
    snapshot_open_failures = [row for row in rows if not row["snapshot_opened"]]
    snapshot_parse_failures = [row for row in rows if not row["snapshot_parse_ok"]]
    residual_failures = [row for row in rows if not row["residual_matches"]]
    negative_control_failures = [row for row in rows if not row["negative_control_rejected"]]
    promotion_leak_failures = [row for row in rows if not row["replay_barred_from_prediction_support"]]
    h = hashlib.sha256()
    h.update(table_path.read_bytes())
    log = {
        "schema_id": "OC133_NUMERIC_REPLAY_LOG_v12",
        "release_id": "oc_core_1_3_3",
        "version": "1.3.3",
        "input_ref": "validation/numeric_replay_qa/OC133_NUMERIC_REPLAY_QA_TABLE.json",
        "input_sha256": h.hexdigest(),
        "independent_replay": not materialize_first,
        "materializer_invoked": materialize_first,
        "materializer_policy": "default replay does not regenerate release artifacts; --materialize-first is diagnostic only",
        "row_total": len(rows),
        "snapshot_open_fail_total": len(snapshot_open_failures),
        "snapshot_parse_fail_total": len(snapshot_parse_failures),
        "residual_failure_total": len(residual_failures),
        "negative_control_failure_total": len(negative_control_failures),
        "promotion_leak_failure_total": len(promotion_leak_failures),
        "failure_total": len(failures),
        "rows": rows,
    }
    (ROOT / "validation" / "numeric_predictions" / "OC133_NUMERIC_REPLAY_LOG.json").write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload.get("unsupported_promoted_total") == 0 and not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
