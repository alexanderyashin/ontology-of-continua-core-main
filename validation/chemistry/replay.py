from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LANE = "chemistry"


def main() -> int:
    log_path = ROOT / "validation" / "numeric_predictions" / "OC133_NUMERIC_REPLAY_LOG.json"
    if not log_path.exists():
        subprocess.run(
            [sys.executable, str(ROOT / "validation" / "numeric_predictions" / "run_numeric_prediction_replay.py")],
            cwd=ROOT,
            check=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
        )
    packet = json.loads((Path(__file__).with_name("VALIDATION_PACKET.json")).read_text(encoding="utf-8"))
    replay = json.loads(log_path.read_text(encoding="utf-8"))
    rows = [row for row in replay.get("rows", []) if row.get("lane") == LANE]
    failures = []
    if len(rows) < 1:
        failures.append("LANE_REPLAY_ROW_COUNT_ZERO")
    for row in rows:
        checks = {
            "snapshot_opened": row.get("snapshot_opened") is True,
            "snapshot_parse_ok": row.get("snapshot_parse_ok") is True,
            "residual_matches": row.get("residual_matches") is True,
            "comparator_residual_matches": row.get("comparator_residual_matches") is True,
            "negative_control_rejected": row.get("negative_control_rejected") is True,
            "prediction_support_blocked": row.get("prediction_support_allowed") is False,
            "empirical_support_blocked": row.get("empirical_support_allowed") is False,
            "replay_barred_from_prediction_support": row.get("replay_barred_from_prediction_support") is True,
        }
        failures.extend(name for name, ok in checks.items() if not ok)
    payload = {
        "schema_id": "OC133_LANE_REPLAY_RESULT_v12",
        "lane": LANE,
        "release_id": "oc_core_1_3_3",
        "version": "1.3.3",
        "result_verdict": "NUMERIC_REPLAY_SUPPORTED_WITHIN_BOUNDS" if not failures else "FAIL",
        "remaining_blocker": packet.get("remaining_blocker") or "NOT_EMPIRICAL_PROMOTION_NUMERIC_REPLAY_QA_ONLY",
        "failure_total": len(failures),
        "failures": failures,
        "source_log_ref": "validation/numeric_predictions/OC133_NUMERIC_REPLAY_LOG.json",
        "rows": rows,
    }
    print(json.dumps(payload, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
