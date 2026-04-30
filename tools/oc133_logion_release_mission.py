from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
WORK_ROOT = ROOT.parents[2]
PRIVATE_K7 = WORK_ROOT / "estra-private-work" / "logion" / "k7"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from release_machine import oc133_platinum, publication  # noqa: E402


EXECUTION_LEDGER_REL = f"{oc133_platinum.MISSION_DIR_REL}/OC133_LOGION_CAPABILITY_EXECUTION_LEDGER.json"
EXECUTION_LEDGER = ROOT / EXECUTION_LEDGER_REL


def command(cmd: list[str], *, cwd: Path = ROOT, timeout: int = 300) -> dict[str, Any]:
    completed = subprocess.run(
        cmd,
        cwd=cwd,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=timeout,
    )
    return {
        "cmd": cmd,
        "cwd": str(cwd),
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout[-4000:],
        "stderr_tail": completed.stderr[-4000:],
    }


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def append_execution_ledger(row: dict[str, Any]) -> dict[str, Any]:
    ledger = read_json(EXECUTION_LEDGER)
    rows = ledger.get("rows", []) if isinstance(ledger.get("rows"), list) else []
    rows.append(row)
    payload = {
        "schema_id": "OC133_LOGION_CAPABILITY_EXECUTION_LEDGER_v1",
        "mission_id": oc133_platinum.MISSION_ID,
        "release_id": oc133_platinum.RELEASE_ID,
        "version": oc133_platinum.VERSION,
        "row_total": len(rows),
        "pass_total": sum(1 for item in rows if item.get("execution_state") == "PASS"),
        "fail_total": sum(1 for item in rows if item.get("execution_state") != "PASS"),
        "latest_work_order_id": row.get("work_order_id"),
        "latest_execution_state": row.get("execution_state"),
        "no_send": True,
        "publish_allowed": False,
        "journal_submissions_allowed": False,
        "rows": rows,
    }
    oc133_platinum.write_json(EXECUTION_LEDGER, payload)
    return payload


def execute_empirical_prediction_work_order(work_order: dict[str, Any], before_audit: dict[str, Any]) -> dict[str, Any]:
    profile_cmd = command(
        [sys.executable, "tools/oc133_capability_repair_executor.py", "--profile", "v12_target_blind_empirical_repair"],
        timeout=1500,
    )
    after_audit = oc133_platinum.content_closure_audit(ROOT)
    mission_refs = oc133_platinum.write_mission_outputs(ROOT, after_audit)
    target_table = read_json(ROOT / "validation" / "target_blind" / "OC133_TARGET_BLIND_PREDICTION_TABLE.json")
    validation_report = read_json(ROOT / "reports" / "OC_CORE_1_3_3_DOMAIN_VALIDATION_REPORT.json")
    empirical_check = after_audit.get("checks", {}).get("empirical_prediction_promotion", {})
    predicate_checks = {
        "capability_profile_returncode_zero": profile_cmd["returncode"] == 0,
        "target_blind_generated_by_logion_worker": target_table.get("generated_by") == "LOGION_CAPABILITY_WORKER",
        "target_blind_capability_owner_ok": target_table.get("capability_owner") == "Research/EmpiricalScience",
        "target_blind_required_fields_and_controls_ok": target_table.get("closure_predicates", {}).get("all_rows_have_formula_snapshot_split_uncertainty_comparator_residual_negative_control_falsifier") is True,
        "target_blind_scope_bounded_not_domain_validation": target_table.get("closure_predicates", {}).get("scope_is_bounded_not_domain_validation") is True,
        "validation_holds_bounded_target_blind_support": validation_report.get("target_blind_bounded_reconstruction_support_present") is True,
        "validation_rejects_broad_domain_promotion": validation_report.get("broad_domain_validation_promoted") is False,
        "empirical_content_check_pass": empirical_check.get("state") == "PASS",
    }
    execution_state = "PASS" if all(predicate_checks.values()) else "FAIL"
    row = {
        "work_order_id": work_order.get("work_order_id"),
        "owner_capability": work_order.get("owner_capability"),
        "title": work_order.get("title"),
        "before_state": before_audit.get("checks", {}).get("empirical_prediction_promotion", {}).get("state"),
        "after_state": empirical_check.get("state"),
        "execution_state": execution_state,
        "artifact_exists_is_not_closure": True,
        "predicate_checks": predicate_checks,
        "closure_evidence_refs": [
            "validation/target_blind/OC133_TARGET_BLIND_PREDICTION_TABLE.json",
            "reports/OC_CORE_1_3_3_DOMAIN_VALIDATION_REPORT.json",
            "reviews/oc133_llm_cerberus/repair/OC133_CAPABILITY_REPAIR_EXECUTION_LEDGER.json",
            "operations/logion_release_mission/oc_core_1_3_3/OC133_CONTENT_CLOSURE_SCORECARD.json",
        ],
        "commands": [profile_cmd],
        "mission_refs": mission_refs,
        "no_send": True,
        "publish_allowed": False,
        "journal_submissions_allowed": False,
    }
    ledger = append_execution_ledger(row)
    return {
        "schema_id": "OC133_LOGION_EXECUTE_NEXT_RESULT_v1",
        "mission_id": oc133_platinum.MISSION_ID,
        "selected_work_order_id": work_order.get("work_order_id"),
        "owner_capability": work_order.get("owner_capability"),
        "execution_state": execution_state,
        "predicate_checks": predicate_checks,
        "ledger_ref": EXECUTION_LEDGER_REL,
        "ledger_latest_state": ledger.get("latest_execution_state"),
        "after_mission_state": after_audit.get("state"),
        "after_blocker_total": after_audit.get("blocker_total"),
        "after_blocker_ids": after_audit.get("blocker_ids", []),
        "no_send": True,
        "publish_allowed": False,
        "journal_submissions_allowed": False,
    }


def execute_next_work_order() -> dict[str, Any]:
    before_audit = oc133_platinum.content_closure_audit(ROOT)
    work_orders = before_audit.get("work_orders", [])
    if not work_orders:
        refs = oc133_platinum.write_mission_outputs(ROOT, before_audit)
        result = {
            "schema_id": "OC133_LOGION_EXECUTE_NEXT_RESULT_v1",
            "mission_id": oc133_platinum.MISSION_ID,
            "selected_work_order_id": "OWNER_REVIEW_NO_SEND",
            "execution_state": "NOOP",
            "mission_refs": refs,
            "after_mission_state": before_audit.get("state"),
            "after_blocker_total": before_audit.get("blocker_total"),
            "no_send": True,
            "publish_allowed": False,
            "journal_submissions_allowed": False,
        }
        append_execution_ledger(result)
        return result
    work_order = work_orders[0]
    if work_order.get("owner_capability") == "Research/EmpiricalScience":
        return execute_empirical_prediction_work_order(work_order, before_audit)
    result = {
        "schema_id": "OC133_LOGION_EXECUTE_NEXT_RESULT_v1",
        "mission_id": oc133_platinum.MISSION_ID,
        "selected_work_order_id": work_order.get("work_order_id"),
        "owner_capability": work_order.get("owner_capability"),
        "execution_state": "BLOCKED_NO_CAPABILITY_EXECUTOR",
        "blocker": "No registered Logion capability executor for this work-order class.",
        "required_repair": "Add a capability-owned executor before attempting direct artifact edits.",
        "no_send": True,
        "publish_allowed": False,
        "journal_submissions_allowed": False,
    }
    append_execution_ledger(result)
    return result


def run_historical_intent_preflight(output_ref: str) -> dict[str, Any]:
    script = PRIVATE_K7 / "spe" / "orchestrator" / "k6" / "query_logion_historical_intent_preflight_v1.py"
    if not script.exists():
        return {"state": "BLOCKED", "reason": "historical intent preflight script missing", "script": str(script)}
    request = (
        "OC Core 1.3.3 platinum release mission must reuse existing Logion Strategy HQ, "
        "institute director, research, IT, publication, review, LLM bridge, and factory/factory-of-factories "
        "capabilities instead of creating duplicate standalone supervisors."
    )
    result = command(
        [
            sys.executable,
            str(script),
            "--request-text",
            request,
            "--reuse-decision",
            "REPAIR_EXISTING",
            "--run-id",
            "OC_CORE_1_3_3_PLATINUM_RELEASE_MISSION_PREFLIGHT",
            "--output",
            output_ref,
        ],
        cwd=PRIVATE_K7,
        timeout=180,
    )
    state = "PASS" if result["returncode"] == 0 else "BLOCKED"
    return {"state": state, "command": result, "output_ref": output_ref}


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap and audit the Logion-owned OC Core 1.3.3 platinum release mission.")
    parser.add_argument("--write", action="store_true", help="Write mission packet, dispatch queue, cockpit, and trajectory certificate.")
    parser.add_argument("--run-preflight", action="store_true", help="Run private K6 historical-intent preflight and store the public evidence packet.")
    parser.add_argument("--run-publication", action="store_true", help="Run Publication capability to generate 1.3.3 no-send journal packages.")
    parser.add_argument("--execute-next", action="store_true", help="Execute the highest-priority Logion mission work order through its registered capability worker.")
    args = parser.parse_args()

    preflight = None
    if args.run_preflight:
        preflight_output = ROOT / oc133_platinum.MISSION_DIR_REL / "OC133_HISTORICAL_INTENT_PREFLIGHT.json"
        preflight = run_historical_intent_preflight(str(preflight_output))

    publication_index = None
    if args.run_publication:
        publication_index = publication.generate_submission_packages(ROOT, release_id=oc133_platinum.RELEASE_ID)

    execute_result = execute_next_work_order() if args.execute_next else None

    audit = oc133_platinum.content_closure_audit(ROOT)
    refs = oc133_platinum.write_mission_outputs(ROOT, audit) if args.write else {}
    payload = {
        "schema_id": "OC133_LOGION_RELEASE_MISSION_RUN_v1",
        "mission_id": oc133_platinum.MISSION_ID,
        "release_id": oc133_platinum.RELEASE_ID,
        "version": oc133_platinum.VERSION,
        "state": audit["state"],
        "blocker_total": audit["blocker_total"],
        "next_automatic_action": audit["next_automatic_action"],
        "preflight": preflight,
        "publication_index": publication_index,
        "execute_result": execute_result,
        "mission_refs": refs,
        "no_send": True,
        "publish_allowed": False,
        "journal_submissions_allowed": False,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if preflight is not None and preflight.get("state") != "PASS":
        return 2
    if execute_result is not None and execute_result.get("execution_state") not in {"PASS", "NOOP"}:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
