from __future__ import annotations

import hashlib
import json
import argparse
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
    parser = argparse.ArgumentParser(description="Run OC133 domain validation or explicit replay-QA mode.")
    parser.add_argument(
        "--qa-only",
        action="store_true",
        help="Allow zero exit for deterministic official-snapshot replay QA that is explicitly barred from empirical promotion.",
    )
    args = parser.parse_args()
    manifest = json.loads((ROOT / "data/OC_DATASET_SNAPSHOT_MANIFEST_1_3_3.json").read_text(encoding="utf-8"))
    claim_ledger_path = ROOT / "claims" / "CLAIM_LEDGER_1_3_3.json"
    claim_ledger = json.loads(claim_ledger_path.read_text(encoding="utf-8")) if claim_ledger_path.exists() else {}
    hash_failures = []
    manifest_policy_failures = []
    if manifest.get("validation_claim_allowed") is not False:
        manifest_policy_failures.append("MANIFEST_VALIDATION_CLAIM_ALLOWED_NOT_FALSE")
    for lane_row in manifest.get("lanes", []):
        if lane_row.get("result_verdict") == "VALIDATED_OFFICIAL_SNAPSHOT" or not lane_row.get("remaining_blocker"):
            manifest_policy_failures.append(f"MANIFEST_LANE_PROMOTES_VALIDATION::{lane_row.get('lane')}")
    for row in manifest["rows"]:
        path = ROOT / row["local_snapshot"]
        actual = sha256_file(path)
        if row["sha256"] and actual != row["sha256"]:
            hash_failures.append({"source_id": row["source_id"], "expected": row["sha256"], "actual": actual})
    numeric_payload = {}
    numeric_log = {}
    numeric_artifact_failures = []
    numeric_script = ROOT / "validation" / "numeric_predictions" / "run_numeric_prediction_replay.py"
    if numeric_script.exists():
        subprocess.run(
            [sys.executable, str(numeric_script)],
            cwd=ROOT,
            check=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
        )
        numeric_payload = json.loads((ROOT / "validation" / "numeric_replay_qa" / "OC133_NUMERIC_REPLAY_QA_TABLE.json").read_text(encoding="utf-8"))
        numeric_log = json.loads((ROOT / "validation" / "numeric_predictions" / "OC133_NUMERIC_REPLAY_LOG.json").read_text(encoding="utf-8"))
    else:
        numeric_artifact_failures.append("NUMERIC_REPLAY_SCRIPT_MISSING")
    if numeric_payload.get("row_total", 0) < 5 or numeric_payload.get("lane_total", 0) < 5:
        numeric_artifact_failures.append("NUMERIC_REPLAY_TABLE_INCOMPLETE")
    if numeric_log.get("row_total", 0) < 5:
        numeric_artifact_failures.append("NUMERIC_REPLAY_LOG_INCOMPLETE")
    lanes = []
    lane_replay_results = []
    lane_replay_failure_total = 0
    unsupported_promoted_total = int(numeric_payload.get("unsupported_promoted_total", 0)) if numeric_payload else 0
    expected_lanes = sorted(
        {row.get("lane") for row in manifest.get("lanes", []) if row.get("lane")}
        | {row.get("lane") for row in manifest.get("rows", []) if row.get("lane")}
    )
    seen_lanes = set()
    for packet_path in sorted((ROOT / "validation").glob("*/VALIDATION_PACKET.json")):
        packet = json.loads(packet_path.read_text(encoding="utf-8"))
        seen_lanes.add(packet.get("lane"))
        if packet["result_verdict"] == "VALIDATED_OFFICIAL_SNAPSHOT":
            unsupported_promoted_total += 1
        replay_script = packet_path.with_name("replay.py")
        replay_payload = {}
        if replay_script.exists():
            completed = subprocess.run(
                [sys.executable, str(replay_script)],
                cwd=ROOT,
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                timeout=120,
            )
            try:
                replay_payload = json.loads(completed.stdout)
            except Exception:
                replay_payload = {
                    "lane": packet.get("lane"),
                    "result_verdict": "REPLAY_PARSE_FAILED",
                    "failure_total": 1,
                    "stderr_tail": completed.stderr[-1000:],
                    "stdout_tail": completed.stdout[-1000:],
                }
            if completed.returncode != 0:
                replay_payload["returncode"] = completed.returncode
                replay_payload["failure_total"] = max(1, int(replay_payload.get("failure_total", 0)))
        else:
            replay_payload = {"lane": packet.get("lane"), "result_verdict": "REPLAY_SCRIPT_MISSING", "failure_total": 1}
        lane_replay_failure_total += int(replay_payload.get("failure_total", 0))
        lane_replay_results.append(replay_payload)
        remaining = replay_payload.get("remaining_blocker", packet.get("remaining_blocker"))
        if packet.get("prediction_support_allowed") is False or packet.get("empirical_support_allowed") is False:
            remaining = remaining or "NOT_EMPIRICAL_PROMOTION_NUMERIC_REPLAY_QA_ONLY"
        lanes.append({"lane": packet["lane"], "result_verdict": replay_payload.get("result_verdict", packet["result_verdict"]), "remaining_blocker": remaining})
    missing_lanes = [lane for lane in expected_lanes if lane not in seen_lanes]
    extra_lanes = sorted(seen_lanes - set(expected_lanes))
    for lane in missing_lanes:
        lane_replay_results.append({"lane": lane, "result_verdict": "VALIDATION_PACKET_MISSING", "failure_total": 1})
    if missing_lanes or extra_lanes:
        lane_replay_failure_total += len(missing_lanes) + len(extra_lanes)
    qa_clear = (
        not hash_failures
        and not manifest_policy_failures
        and not numeric_artifact_failures
        and unsupported_promoted_total == 0
        and lane_replay_failure_total == 0
        and numeric_log.get("failure_total", 0) == 0
    )
    payload = {
        "schema_id": "OC133_DOMAIN_VALIDATION_REPORT_v12",
        "release_id": "oc_core_1_3_3",
        "version": "1.3.3",
        "hash_failure_total": len(hash_failures),
        "hash_failures": hash_failures,
        "manifest_policy_failure_total": len(manifest_policy_failures),
        "manifest_policy_failures": manifest_policy_failures,
        "numeric_artifact_failure_total": len(numeric_artifact_failures),
        "numeric_artifact_failures": numeric_artifact_failures,
        "unsupported_promoted_total": unsupported_promoted_total,
        "claim_ledger_adversarial_review_blocker_total": claim_ledger.get("adversarial_review_blocker_total"),
        "claim_ledger_release_promotion_allowed": claim_ledger.get("release_promotion_allowed"),
        "lane_total": len(lanes),
        "expected_lanes": expected_lanes,
        "missing_lane_total": len(missing_lanes),
        "missing_lanes": missing_lanes,
        "extra_lane_total": len(extra_lanes),
        "extra_lanes": extra_lanes,
        "lanes": lanes,
        "official_snapshots_are_inputs_not_validation_by_themselves": True,
        "empirical_promotion_policy": "NO_EMPIRICAL_PASS_WITHOUT_NUMERIC_REPLAY",
        "numeric_replay_qa_table": "validation/numeric_replay_qa/OC133_NUMERIC_REPLAY_QA_TABLE.json" if numeric_payload else "",
        "numeric_replay_row_total": numeric_payload.get("row_total", 0),
        "numeric_replay_lane_total": numeric_payload.get("lane_total", 0),
        "numeric_replay_failure_total": numeric_log.get("failure_total", 0),
        "numeric_snapshot_parse_fail_total": numeric_log.get("snapshot_parse_fail_total", 0),
        "lane_replay_failure_total": lane_replay_failure_total,
        "lane_replay_results": lane_replay_results,
        "numeric_blocked_for_promotion_total": numeric_payload.get("blocked_for_promotion_total", 0),
        "empirical_promotion_disallowed_total": numeric_payload.get("empirical_promotion_disallowed_total", 0),
        "numeric_quarantined_replay_qa_total": numeric_payload.get("quarantined_replay_qa_total", 0),
        "domain_validation_promoted": False,
        "heldout_prediction_support_present": False,
        "scientific_validation_state": "EMPIRICAL_REPLAY_REQUIRED_FOR_DOMAIN_PROMOTION",
        "release_gate_semantics": "Exit 0 means replay QA completed and no empirical promotion leaked; it is not a domain-validation PASS.",
        "cli_mode": "QA_ONLY" if args.qa_only else "DOMAIN_VALIDATION_GATE",
        "qa_only_zero_exit_allowed": bool(args.qa_only),
        "validation_boundary": "Deterministic numeric replay QA only; no held-out empirical prediction support is promoted.",
        "verdict": "QA_REPLAY_COMPLETE_NOT_DOMAIN_VALIDATED" if qa_clear else "FAIL",
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
        f"Empirical promotion disallowed rows: `{payload['empirical_promotion_disallowed_total']}`",
        f"Numeric quarantined replay-QA rows: `{payload['numeric_quarantined_replay_qa_total']}`",
        "",
        payload["validation_boundary"],
        "",
        "| Lane | Verdict | Blocker |",
        "| --- | --- | --- |",
    ]
    for row in lanes:
        lines.append(f"| `{row['lane']}` | `{row['result_verdict']}` | `{row.get('remaining_blocker') or ''}` |")
    (reports / "OC_CORE_1_3_3_DOMAIN_VALIDATION_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    if payload["verdict"] == "FAIL":
        return 1
    if args.qa_only:
        return 0
    if payload["domain_validation_promoted"] is True and payload["heldout_prediction_support_present"] is True and payload["claim_ledger_release_promotion_allowed"] is True:
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
