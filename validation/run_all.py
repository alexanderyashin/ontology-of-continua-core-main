from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    manifest = json.loads((ROOT / "data/OC_DATASET_SNAPSHOT_MANIFEST_1_3_3.json").read_text(encoding="utf-8"))
    hash_failures = []
    for row in manifest["rows"]:
        path = ROOT / row["local_snapshot"]
        actual = sha256_file(path)
        if row["sha256"] and actual != row["sha256"]:
            hash_failures.append({"source_id": row["source_id"], "expected": row["sha256"], "actual": actual})
    lanes = []
    unsupported_promoted_total = 0
    for packet_path in sorted((ROOT / "validation").glob("*/VALIDATION_PACKET.json")):
        packet = json.loads(packet_path.read_text(encoding="utf-8"))
        if packet["result_verdict"] == "VALIDATED_OFFICIAL_SNAPSHOT" and packet.get("remaining_blocker"):
            unsupported_promoted_total += 1
        lanes.append({"lane": packet["lane"], "result_verdict": packet["result_verdict"], "remaining_blocker": packet.get("remaining_blocker")})
    numeric_payload = {}
    numeric_script = ROOT / "validation" / "numeric_predictions" / "run_numeric_prediction_replay.py"
    if numeric_script.exists():
        subprocess.run([sys.executable, str(numeric_script)], cwd=ROOT, check=True, text=True, capture_output=True)
        numeric_payload = json.loads((ROOT / "validation" / "numeric_predictions" / "OC133_NUMERIC_PREDICTION_TABLE.json").read_text(encoding="utf-8"))
        unsupported_promoted_total += int(numeric_payload.get("unsupported_promoted_total", 0))
    payload = {
        "schema_id": "OC133_DOMAIN_VALIDATION_REPORT_v1",
        "release_id": "oc_core_1_3_3",
        "hash_failure_total": len(hash_failures),
        "hash_failures": hash_failures,
        "unsupported_promoted_total": unsupported_promoted_total,
        "lane_total": len(lanes),
        "lanes": lanes,
        "official_snapshots_are_inputs_not_validation_by_themselves": True,
        "empirical_promotion_policy": "NO_EMPIRICAL_PASS_WITHOUT_NUMERIC_REPLAY",
        "numeric_prediction_table": "validation/numeric_predictions/OC133_NUMERIC_PREDICTION_TABLE.json" if numeric_payload else "",
        "numeric_replay_row_total": numeric_payload.get("row_total", 0),
        "numeric_replay_lane_total": numeric_payload.get("lane_total", 0),
        "numeric_blocked_for_promotion_total": numeric_payload.get("blocked_for_promotion_total", 0),
        "numeric_quarantined_replay_qa_total": numeric_payload.get("quarantined_replay_qa_total", 0),
        "verdict": "PASS_NO_FAKE_EMPIRICAL_PASS" if not hash_failures and unsupported_promoted_total == 0 else "FAIL",
    }
    reports = ROOT / "reports"
    reports.mkdir(exist_ok=True)
    (reports / "OC_CORE_1_3_3_DOMAIN_VALIDATION_REPORT.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# OC Core 1.3.3 Domain Validation Report",
        "",
        f"Verdict: `{payload['verdict']}`",
        f"Hash failures: `{payload['hash_failure_total']}`",
        f"Unsupported promoted empirical rows: `{payload['unsupported_promoted_total']}`",
        f"Numeric replay rows: `{payload['numeric_replay_row_total']}`",
        f"Numeric blocked-for-promotion rows: `{payload['numeric_blocked_for_promotion_total']}`",
        f"Numeric quarantined replay-QA rows: `{payload['numeric_quarantined_replay_qa_total']}`",
        "",
        "| Lane | Verdict | Blocker |",
        "| --- | --- | --- |",
    ]
    for row in lanes:
        lines.append(f"| `{row['lane']}` | `{row['result_verdict']}` | `{row.get('remaining_blocker') or ''}` |")
    (reports / "OC_CORE_1_3_3_DOMAIN_VALIDATION_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if payload["verdict"].startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
