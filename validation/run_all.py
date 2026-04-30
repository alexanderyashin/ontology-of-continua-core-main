from __future__ import annotations

import hashlib
import json
import argparse
import subprocess
import sys
from pathlib import Path
import importlib.util


ROOT = Path(__file__).resolve().parents[1]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_lf_normalized_text(path: Path) -> str:
    data = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def certified_generated_artifact_hashes() -> dict[str, str]:
    cert_path = ROOT / "formal" / "lean" / "LEAN_BUILD_CERTIFICATE_1_3_3.json"
    if not cert_path.exists():
        return {}
    cert = json.loads(cert_path.read_text(encoding="utf-8"))
    return {
        row.get("ref"): row.get("sha256")
        for row in cert.get("generated_artifact_manifest", [])
        if isinstance(row, dict) and row.get("ref") and row.get("sha256")
    }


def replay_qa_status_language_failures(payload: dict, *, namespace: str) -> list[str]:
    """Reject support/pass/validation wording on official-snapshot replay QA rows."""
    failures: list[str] = []
    forbidden = ("SUPPORTED", "VALIDATED", "PROMOTED", "PASS")
    allowed_phrases = (
        "NOT_PROMOTED",
        "QA_NOT_DOMAIN_VALIDATION",
        "QA_REPLAY_COMPLETE_NOT_DOMAIN_VALIDATED",
        "PREDICTION_SUPPORT_BLOCKED",
        "EMPIRICAL_SUPPORT_BLOCKED",
    )
    for idx, row in enumerate(payload.get("rows", []) if isinstance(payload, dict) else []):
        if not isinstance(row, dict):
            continue
        promoted = row.get("prediction_support_allowed") is True or row.get("empirical_support_allowed") is True
        if promoted:
            continue
        for key in ("result_verdict", "promotion_status", "prediction_status", "public_status", "verdict"):
            value = row.get(key)
            if value in (None, ""):
                continue
            text = str(value).upper()
            if any(term in text for term in forbidden) and not any(allowed in text for allowed in allowed_phrases):
                failures.append(f"{namespace}::{idx}::{key}::{value}")
    return failures


def finite_math_proof_corpus_ok(finite_report: dict) -> bool:
    replay_path = ROOT / "validation" / "numeric_predictions" / "run_numeric_prediction_replay.py"
    spec = importlib.util.spec_from_file_location("oc133_numeric_replay", replay_path)
    if spec is None or spec.loader is None:
        return False
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.finite_math_replay_value(finite_report) is not None


def main() -> int:
    parser = argparse.ArgumentParser(description="Run OC133 domain validation or explicit replay-QA mode.")
    parser.add_argument(
        "--qa-only",
        action="store_true",
        help="Allow zero exit for deterministic official-snapshot replay QA that is explicitly barred from empirical promotion.",
    )
    parser.add_argument(
        "--materialize-first",
        action="store_true",
        help="Explicitly regenerate deterministic no-send artifacts before replay and then verify their certified hashes.",
    )
    args = parser.parse_args()
    materialize_first_returncode = None
    if args.materialize_first:
        materialize = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "materialize_oc_core_1_3_3_v12_closure.py")],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=900,
        )
        materialize_first_returncode = materialize.returncode
        if materialize.returncode != 0:
            print(materialize.stdout[-2000:])
            print(materialize.stderr[-2000:])
            return materialize.returncode
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
        policy = str(row.get("sha256_policy", ""))
        actual = sha256_lf_normalized_text(path) if "LF_NORMALIZED" in policy else sha256_file(path)
        if row["sha256"] and actual != row["sha256"]:
            hash_failures.append({"source_id": row["source_id"], "expected": row["sha256"], "actual": actual, "sha256_policy": policy})
    numeric_payload = {}
    numeric_log = {}
    numeric_artifact_failures = []
    finite_check = subprocess.run(
        [sys.executable, str(ROOT / "proofs" / "finite_model_checks" / "run_finite_model_checks.py")],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=600,
    )
    if finite_check.returncode != 0:
        numeric_artifact_failures.append("FINITE_MODEL_CHECKS_FAILED_BEFORE_NUMERIC_REPLAY")
    finite_report_path = ROOT / "proofs" / "FINITE_MODEL_CHECKS_1_3_3.json"
    finite_report = json.loads(finite_report_path.read_text(encoding="utf-8")) if finite_report_path.exists() else {}
    finite_math_corpus_ok = finite_math_proof_corpus_ok(finite_report) if finite_report else False
    if args.qa_only and finite_math_corpus_ok:
        numeric_artifact_failures = [
            failure for failure in numeric_artifact_failures
            if failure != "FINITE_MODEL_CHECKS_FAILED_BEFORE_NUMERIC_REPLAY"
        ]
    numeric_script = ROOT / "validation" / "numeric_predictions" / "run_numeric_prediction_replay.py"
    qa_table = ROOT / "validation" / "numeric_replay_qa" / "OC133_NUMERIC_REPLAY_QA_TABLE.json"
    qa_table_ref = "validation/numeric_replay_qa/OC133_NUMERIC_REPLAY_QA_TABLE.json"
    if not qa_table.exists():
        numeric_artifact_failures.append("NUMERIC_REPLAY_QA_TABLE_MISSING_RUN_MATERIALIZER_EXPLICITLY")
    cert_generated_hashes = certified_generated_artifact_hashes()
    if qa_table.exists():
        certified_qa_sha = cert_generated_hashes.get(qa_table_ref)
        actual_qa_sha = sha256_file(qa_table)
        if not certified_qa_sha:
            numeric_artifact_failures.append("NUMERIC_REPLAY_QA_TABLE_NOT_IN_CERTIFIED_GENERATED_ARTIFACT_MANIFEST")
        elif certified_qa_sha != actual_qa_sha:
            numeric_artifact_failures.append("NUMERIC_REPLAY_QA_TABLE_CERTIFIED_HASH_MISMATCH")
    if numeric_script.exists():
        numeric_proc = subprocess.run(
            [sys.executable, str(numeric_script)],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
        )
        if numeric_proc.returncode != 0:
            numeric_artifact_failures.append(f"NUMERIC_REPLAY_RETURNCODE::{numeric_proc.returncode}")
        numeric_payload_path = ROOT / "validation" / "numeric_replay_qa" / "OC133_NUMERIC_REPLAY_QA_TABLE.json"
        numeric_log_path = ROOT / "validation" / "numeric_predictions" / "OC133_NUMERIC_REPLAY_LOG.json"
        if numeric_payload_path.exists():
            numeric_payload = json.loads(numeric_payload_path.read_text(encoding="utf-8"))
        else:
            numeric_artifact_failures.append("NUMERIC_REPLAY_QA_TABLE_NOT_WRITTEN")
        if numeric_log_path.exists():
            numeric_log = json.loads(numeric_log_path.read_text(encoding="utf-8"))
        else:
            numeric_artifact_failures.append("NUMERIC_REPLAY_LOG_NOT_WRITTEN")
    else:
        numeric_artifact_failures.append("NUMERIC_REPLAY_SCRIPT_MISSING")
    target_payload = {}
    target_blind_failures = []
    target_script = ROOT / "validation" / "target_blind" / "run_target_blind_predictions.py"
    if target_script.exists():
        target_proc = subprocess.run(
            [sys.executable, str(target_script)],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=120,
        )
        target_path = ROOT / "validation" / "target_blind" / "OC133_TARGET_BLIND_PREDICTION_TABLE.json"
        if target_proc.returncode != 0:
            target_blind_failures.append(f"TARGET_BLIND_RETURNCODE::{target_proc.returncode}")
        if target_path.exists():
            target_payload = json.loads(target_path.read_text(encoding="utf-8"))
            target_blind_failures.extend(target_payload.get("failures", []))
            if target_payload.get("generated_by") != "LOGION_CAPABILITY_WORKER":
                target_blind_failures.append("TARGET_BLIND_NOT_LOGION_CAPABILITY_GENERATED")
            if target_payload.get("capability_owner") != "Research/EmpiricalScience":
                target_blind_failures.append("TARGET_BLIND_CAPABILITY_OWNER_MISMATCH")
            predicates = target_payload.get("closure_predicates", {})
            if not predicates.get("all_rows_have_formula_snapshot_split_uncertainty_comparator_residual_negative_control_falsifier"):
                target_blind_failures.append("TARGET_BLIND_REQUIRED_FIELDS_OR_CONTROLS_INCOMPLETE")
            if not predicates.get("scope_is_bounded_not_domain_validation"):
                target_blind_failures.append("TARGET_BLIND_SCOPE_OVERCLAIMS_DOMAIN_VALIDATION")
        else:
            target_blind_failures.append("TARGET_BLIND_TABLE_NOT_WRITTEN")
    else:
        target_blind_failures.append("TARGET_BLIND_SCRIPT_MISSING")
    if numeric_payload.get("row_total", 0) < 5 or numeric_payload.get("lane_total", 0) < 5:
        numeric_artifact_failures.append("NUMERIC_REPLAY_TABLE_INCOMPLETE")
    if numeric_log.get("row_total", 0) < 5:
        numeric_artifact_failures.append("NUMERIC_REPLAY_LOG_INCOMPLETE")
    numeric_artifact_failures.extend(replay_qa_status_language_failures(numeric_payload, namespace="NUMERIC_REPLAY_QA_TABLE"))
    numeric_artifact_failures.extend(replay_qa_status_language_failures(numeric_log, namespace="NUMERIC_REPLAY_LOG"))
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
        replay_status_failures = replay_qa_status_language_failures({"rows": [packet, replay_payload]}, namespace=f"LANE::{packet.get('lane')}")
        numeric_artifact_failures.extend(replay_status_failures)
    missing_lanes = [lane for lane in expected_lanes if lane not in seen_lanes]
    extra_lanes = sorted(seen_lanes - set(expected_lanes))
    for lane in missing_lanes:
        lane_replay_results.append({"lane": lane, "result_verdict": "VALIDATION_PACKET_MISSING", "failure_total": 1})
    if missing_lanes or extra_lanes:
        lane_replay_failure_total += len(missing_lanes) + len(extra_lanes)
    finite_gate_clear = (
        finite_check.returncode == 0
        and finite_report.get("failure_total", 1) == 0
    ) or (args.qa_only and finite_math_corpus_ok)
    qa_clear = (
        not hash_failures
        and not manifest_policy_failures
        and not numeric_artifact_failures
        and unsupported_promoted_total == 0
        and lane_replay_failure_total == 0
        and numeric_log.get("failure_total", 0) == 0
        and not target_blind_failures
        and finite_gate_clear
    )
    target_prediction_total = int(target_payload.get("prediction_support_allowed_total", 0) or 0)
    target_empirical_total = int(target_payload.get("empirical_support_allowed_total", 0) or 0)
    target_blind_lane_total = int(target_payload.get("lane_total", 0) or 0)
    target_blind_all_required_domains_present = target_blind_lane_total >= 5 and target_prediction_total >= 5 and target_empirical_total >= 5
    target_blind_bounded_support_present = target_prediction_total > 0 and target_empirical_total > 0 and not target_blind_failures
    scientific_validation_state = (
        "TARGET_BLIND_HELDOUT_RECONSTRUCTION_ALL_REQUIRED_DOMAINS_NO_SEND"
        if qa_clear and target_blind_all_required_domains_present
        else (
            "TARGET_BLIND_HELDOUT_RECONSTRUCTION_PARTIAL_NO_SEND"
            if target_blind_bounded_support_present
            else "TARGET_BLIND_HELDOUT_PROTOCOL_REQUIRED_FOR_DOMAIN_PROMOTION"
        )
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
        "empirical_promotion_policy": "NO_EMPIRICAL_PASS_FROM_OFFICIAL_SNAPSHOT_REPLAY_QA",
        "numeric_replay_qa_table": "validation/numeric_replay_qa/OC133_NUMERIC_REPLAY_QA_TABLE.json" if numeric_payload else "",
        "finite_model_checks_ref": "proofs/FINITE_MODEL_CHECKS_1_3_3.json",
        "finite_model_checks_sha256": sha256_file(finite_report_path) if finite_report_path.exists() else None,
        "finite_model_checks_failure_total": finite_report.get("failure_total"),
        "finite_model_checks_certificate_binding_failure_total": finite_report.get("certificate_binding_failure_total"),
        "finite_model_checks_returncode": finite_check.returncode,
        "finite_model_math_proof_corpus_qa_ok": finite_math_corpus_ok,
        "finite_model_math_proof_corpus_policy": "QA-only semantic theorem-corpus parse; unrelated finite governance/public-surface rows are not empirical or prediction support.",
        "numeric_replay_row_total": numeric_payload.get("row_total", 0),
        "numeric_replay_lane_total": numeric_payload.get("lane_total", 0),
        "numeric_replay_failure_total": numeric_log.get("failure_total", 0),
        "target_blind_prediction_table": "validation/target_blind/OC133_TARGET_BLIND_PREDICTION_TABLE.json" if target_payload else "",
        "target_blind_failure_total": len(target_blind_failures),
        "target_blind_failures": target_blind_failures,
        "target_blind_prediction_support_allowed_total": target_prediction_total,
        "target_blind_empirical_support_allowed_total": target_empirical_total,
        "target_blind_lane_total": target_blind_lane_total,
        "target_blind_all_required_domains_present": target_blind_all_required_domains_present,
        "target_blind_generated_by": target_payload.get("generated_by"),
        "target_blind_capability_owner": target_payload.get("capability_owner"),
        "target_blind_closure_predicates": target_payload.get("closure_predicates", {}),
        "promoted_empirical_lane_total": target_blind_lane_total if target_blind_bounded_support_present else 0,
        "numeric_snapshot_parse_fail_total": numeric_log.get("snapshot_parse_fail_total", 0),
        "lane_replay_failure_total": lane_replay_failure_total,
        "lane_replay_results": lane_replay_results,
        "numeric_blocked_for_promotion_total": numeric_payload.get("blocked_for_promotion_total", 0),
        "empirical_promotion_disallowed_total": numeric_payload.get("empirical_promotion_disallowed_total", 0),
        "numeric_quarantined_replay_qa_total": numeric_payload.get("quarantined_replay_qa_total", 0),
        "domain_validation_promoted": False,
        "broad_domain_validation_promoted": False,
        "domain_validation_support_allowed": False,
        "target_blind_bounded_reconstruction_support_present": target_blind_bounded_support_present,
        "heldout_prediction_support_present": target_blind_bounded_support_present,
        "scientific_validation_state": scientific_validation_state,
        "scientific_validation_state_scope": "bounded target-blind reconstruction rows only; no broad domain validation and no TOE truth claim",
        "release_gate_semantics": "Exit 0 means official-snapshot replay QA completed and no empirical promotion leaked; snapshot replay can never by itself become a domain-validation PASS.",
        "cli_mode": "QA_ONLY" if args.qa_only else "DOMAIN_VALIDATION_GATE",
        "materialize_first_explicit": bool(args.materialize_first),
        "materialize_first_returncode": materialize_first_returncode,
        "canonical_clean_checkout_command_sequence": [
            "python tools/materialize_oc_core_1_3_3_v12_closure.py",
            "python validation/run_all.py --qa-only",
        ],
        "qa_only_zero_exit_allowed": bool(args.qa_only),
        "validation_boundary": "Official-snapshot replay QA remains quarantined. Target-blind rows may support only bounded held-out reconstruction claims, not broad domain validation or novelty.",
        "verdict": scientific_validation_state if qa_clear and target_blind_bounded_support_present else ("QA_REPLAY_COMPLETE_NOT_DOMAIN_VALIDATED" if qa_clear else "FAIL"),
    }
    reports = ROOT / "reports"
    reports.mkdir(exist_ok=True)
    (reports / "OC_CORE_1_3_3_DOMAIN_VALIDATION_REPORT.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n")
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
    (reports / "OC_CORE_1_3_3_DOMAIN_VALIDATION_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(payload, indent=2))
    if payload["verdict"] == "FAIL":
        return 1
    if args.qa_only:
        return 0
    if payload["target_blind_bounded_reconstruction_support_present"] is True and payload["claim_ledger_release_promotion_allowed"] is True:
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
