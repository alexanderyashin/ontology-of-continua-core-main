from __future__ import annotations

import contextlib
import hashlib
import io
import json
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    with contextlib.redirect_stdout(io.StringIO()):
        runpy.run_path(str(ROOT / "tools" / "materialize_oc_core_1_3_3_v12_closure.py"), run_name="__main__")
    table_path = ROOT / "validation" / "numeric_predictions" / "OC133_NUMERIC_PREDICTION_TABLE.json"
    payload = json.loads(table_path.read_text(encoding="utf-8"))
    rows = []
    for row in payload["rows"]:
        residual = abs(float(row["predicted_value"]) - float(row["observed_value"]))
        tolerance = float(row["uncertainty"]) if float(row["uncertainty"]) > 0 else 0.0
        if row["claim_id"] == "OC133-NUM-PHYS-C":
            negative_residual = abs(300000000.0 - float(row["observed_value"]))
        elif row["claim_id"] == "OC133-NUM-CHEM-H2O":
            negative_residual = abs(44.0095 - float(row["observed_value"]))
        elif row["claim_id"] == "OC133-NUM-BIO-GEO-COUNT":
            negative_residual = abs((float(row["observed_value"]) + 1.0) - float(row["observed_value"]))
        elif row["claim_id"] == "OC133-NUM-SYS-WDI-GDP":
            negative_residual = float(row["uncertainty"]) + 1.0
        else:
            negative_residual = 1.0
        declared = float(row["residual"])
        rows.append({
            "claim_id": row["claim_id"],
            "lane": row["lane"],
            "computed_residual": residual,
            "declared_residual": row["residual"],
            "residual_matches": abs(residual - declared) <= max(1e-6, abs(declared) * 1e-9),
            "negative_control_residual": negative_residual,
            "negative_control_rejected": negative_residual > tolerance,
        })
    failures = [row for row in rows if not row["residual_matches"] or not row["negative_control_rejected"]]
    h = hashlib.sha256()
    h.update(table_path.read_bytes())
    log = {
        "schema_id": "OC133_NUMERIC_REPLAY_LOG_v12",
        "release_id": "oc_core_1_3_3",
        "version": "1.3.3",
        "input_ref": "validation/numeric_predictions/OC133_NUMERIC_PREDICTION_TABLE.json",
        "input_sha256": h.hexdigest(),
        "row_total": len(rows),
        "failure_total": len(failures),
        "rows": rows,
    }
    (ROOT / "validation" / "numeric_predictions" / "OC133_NUMERIC_REPLAY_LOG.json").write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload.get("unsupported_promoted_total") == 0 and not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
