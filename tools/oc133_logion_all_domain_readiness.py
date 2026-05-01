from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from release_machine import oc133_platinum  # noqa: E402


EXECUTION_LEDGER_REL = f"{oc133_platinum.MISSION_DIR_REL}/OC133_ALL_DOMAIN_EXECUTION_LEDGER.json"
EXECUTION_LEDGER = ROOT / EXECUTION_LEDGER_REL


PROFILE_BY_CAPABILITY = {
    "Research/FormalScience": "v12_grand_formal_science_research_program",
    "Research/EmpiricalScience": "v12_all_domain_empirical_readiness_repair",
    "Research/PriorArt": "v12_modern_science_comparator_research_program",
    "Review/ClaimBoundary": "v12_claim_boundary_overclaim_repair",
    "Publication/JournalPackages": "v12_journal_package_readiness_repair",
}


def command(cmd: list[str], *, timeout: int = 900) -> dict[str, Any]:
    completed = subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=timeout,
    )
    return {
        "cmd": cmd,
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


def append_ledger(row: dict[str, Any]) -> dict[str, Any]:
    ledger = read_json(EXECUTION_LEDGER)
    rows = ledger.get("rows", []) if isinstance(ledger.get("rows"), list) else []
    normalized_rows = []
    for item in rows:
        if (
            isinstance(item, dict)
            and item.get("execution_state") == "PASS"
            and item.get("after_final_readiness_state") == "SCIENTIFIC_BLOCKERS_REMAIN"
            and item.get("artifact_exists_is_not_closure") is True
        ):
            item = dict(item)
            item["execution_state"] = "SCIENTIFIC_BLOCKERS_REMAIN"
            item["legacy_execution_state_normalized_from"] = "PASS"
        normalized_rows.append(item)
    rows = normalized_rows
    rows.append(row)
    payload = {
        "schema_id": "OC133_ALL_DOMAIN_EXECUTION_LEDGER_v1",
        "mission_id": oc133_platinum.MISSION_ID,
        "release_id": oc133_platinum.RELEASE_ID,
        "version": oc133_platinum.VERSION,
        "row_total": len(rows),
        "pass_total": sum(1 for item in rows if item.get("execution_state") == "PASS"),
        "fail_total": sum(1 for item in rows if item.get("execution_state") != "PASS"),
        "scientific_blocked_total": sum(1 for item in rows if item.get("execution_state") == "SCIENTIFIC_BLOCKERS_REMAIN"),
        "latest_work_order_id": row.get("work_order_id"),
        "latest_execution_state": row.get("execution_state"),
        "no_send": True,
        "publish_allowed": False,
        "journal_submissions_allowed": False,
        "rows": rows,
    }
    oc133_platinum.write_json(EXECUTION_LEDGER, payload)
    return payload


def write_all_domain_outputs(audit: dict[str, Any] | None = None) -> dict[str, str]:
    base_audit = oc133_platinum.content_closure_audit(ROOT)
    audit = audit or oc133_platinum.all_domain_readiness_audit(ROOT, base_audit)
    base = oc133_platinum.mission_dir(ROOT)
    dispatch = {
        "schema_id": "OC133_ALL_DOMAIN_WORK_ORDERS_v1",
        "mission_id": oc133_platinum.MISSION_ID,
        "release_id": oc133_platinum.RELEASE_ID,
        "version": oc133_platinum.VERSION,
        "generated_at": oc133_platinum.TIMESTAMP,
        "queue_sha256": audit["work_order_queue_sha256"],
        "state": "ACTIVE" if audit["work_orders"] else "EMPTY_OWNER_REVIEW_NO_SEND",
        "ordering_policy": "safety/no-send, all-domain evidence blocker, claim-boundary blocker, journal-package blocker, stable work_order_id",
        "work_order_total": audit["work_order_total"],
        "rows": audit["work_orders"],
    }
    oc133_platinum.write_json(base / "OC133_ALL_DOMAIN_READINESS_SCORECARD.json", audit)
    oc133_platinum.write_json(base / "OC133_ALL_DOMAIN_WORK_ORDERS.json", dispatch)
    oc133_platinum.write_text(base / "OC133_ALL_DOMAIN_READINESS_COCKPIT.md", oc133_platinum.render_all_domain_cockpit(audit))
    return {
        "all_domain_scorecard_ref": f"{oc133_platinum.MISSION_DIR_REL}/OC133_ALL_DOMAIN_READINESS_SCORECARD.json",
        "all_domain_dispatch_ref": f"{oc133_platinum.MISSION_DIR_REL}/OC133_ALL_DOMAIN_WORK_ORDERS.json",
        "all_domain_cockpit_ref": f"{oc133_platinum.MISSION_DIR_REL}/OC133_ALL_DOMAIN_READINESS_COCKPIT.md",
    }


def execute_next() -> dict[str, Any]:
    before = oc133_platinum.all_domain_readiness_audit(ROOT, oc133_platinum.content_closure_audit(ROOT))
    work_orders = before.get("work_orders", [])
    if not work_orders:
        refs = write_all_domain_outputs(before)
        result = {
            "schema_id": "OC133_ALL_DOMAIN_EXECUTE_NEXT_RESULT_v1",
            "mission_id": oc133_platinum.MISSION_ID,
            "selected_work_order_id": "OWNER_REVIEW_NO_SEND",
            "execution_state": "NOOP",
            "after_state": before.get("state"),
            "after_final_readiness_state": before.get("final_readiness_state"),
            "refs": refs,
            "no_send": True,
            "publish_allowed": False,
            "journal_submissions_allowed": False,
        }
        append_ledger(result)
        return result

    work_order = work_orders[0]
    profile = PROFILE_BY_CAPABILITY.get(str(work_order.get("owner_capability")))
    if (
        work_order.get("owner_capability") == "Research/EmpiricalScience"
        and "grand_toe_empirical_superiority" in str(work_order.get("before_predicate", ""))
    ):
        profile = "v12_grand_empirical_superiority_research_program"
    if (
        work_order.get("owner_capability") == "Research/EmpiricalScience"
        and "strict per-domain predictive superiority" in str(work_order.get("title", "")).lower()
    ):
        profile = "v12_grand_empirical_superiority_research_program"
    if profile:
        result_cmd = command([sys.executable, "tools/oc133_capability_repair_executor.py", "--profile", profile], timeout=1500)
        after = oc133_platinum.all_domain_readiness_audit(ROOT, oc133_platinum.content_closure_audit(ROOT))
        refs = write_all_domain_outputs(after)
        after_blocker_ids = after.get("blocker_ids", [])
        if result_cmd["returncode"] != 0:
            execution_state = "FAIL"
        elif work_order.get("work_order_id") != "OWNER_REVIEW_NO_SEND" and work_order.get("before_predicate") and work_order.get("owner_capability") and work_order.get("title") and str(work_order.get("work_order_id")):
            execution_state = "SCIENTIFIC_BLOCKERS_REMAIN" if str(work_order.get("work_order_id")).startswith("OC133-PLATINUM-WO-") and any(
                str(row.get("work_order_id")) == str(work_order.get("work_order_id"))
                for row in after.get("work_orders", [])
            ) else "PASS"
        else:
            execution_state = "PASS"
        row = {
            "schema_id": "OC133_ALL_DOMAIN_EXECUTION_ROW_v1",
            "work_order_id": work_order.get("work_order_id"),
            "owner_capability": work_order.get("owner_capability"),
            "profile": profile,
            "execution_state": execution_state,
            "before_state": before.get("state"),
            "before_final_readiness_state": before.get("final_readiness_state"),
            "after_state": after.get("state"),
            "after_final_readiness_state": after.get("final_readiness_state"),
            "after_blocker_ids": after_blocker_ids,
            "command": result_cmd,
            "refs": refs,
            "artifact_exists_is_not_closure": True,
            "no_send": True,
            "publish_allowed": False,
            "journal_submissions_allowed": False,
        }
        ledger = append_ledger(row)
        return {
            "schema_id": "OC133_ALL_DOMAIN_EXECUTE_NEXT_RESULT_v1",
            "mission_id": oc133_platinum.MISSION_ID,
            "selected_work_order_id": work_order.get("work_order_id"),
            "owner_capability": work_order.get("owner_capability"),
            "profile": profile,
            "execution_state": row["execution_state"],
            "ledger_ref": EXECUTION_LEDGER_REL,
            "ledger_latest_state": ledger.get("latest_execution_state"),
            "after_state": after.get("state"),
            "after_final_readiness_state": after.get("final_readiness_state"),
            "after_blocker_ids": after.get("blocker_ids", []),
            "no_send": True,
            "publish_allowed": False,
            "journal_submissions_allowed": False,
        }

    row = {
        "schema_id": "OC133_ALL_DOMAIN_EXECUTION_ROW_v1",
        "work_order_id": work_order.get("work_order_id"),
        "owner_capability": work_order.get("owner_capability"),
        "execution_state": "BLOCKED_NO_CAPABILITY_PROFILE",
        "required_repair": "Register a Logion capability profile before direct artifact edits.",
        "no_send": True,
        "publish_allowed": False,
        "journal_submissions_allowed": False,
    }
    append_ledger(row)
    return row


def main() -> int:
    parser = argparse.ArgumentParser(description="Logion all-domain scientific readiness controller for OC Core 1.3.3.")
    parser.add_argument("--write", action="store_true", help="Write all-domain scorecard, work orders, and cockpit.")
    parser.add_argument("--execute-next", action="store_true", help="Execute the highest-priority all-domain work order via a Logion capability profile.")
    parser.add_argument(
        "--allow-blocked-exit-zero",
        action="store_true",
        help="Return zero when the controller ran correctly but scientific blockers remain.",
    )
    args = parser.parse_args()

    execute_result = execute_next() if args.execute_next else None
    audit = oc133_platinum.all_domain_readiness_audit(ROOT, oc133_platinum.content_closure_audit(ROOT))
    refs = write_all_domain_outputs(audit) if args.write else {}
    payload = {
        "schema_id": "OC133_LOGION_ALL_DOMAIN_READINESS_RUN_v1",
        "mission_id": oc133_platinum.MISSION_ID,
        "release_id": oc133_platinum.RELEASE_ID,
        "version": oc133_platinum.VERSION,
        "state": audit["state"],
        "final_readiness_state": audit["final_readiness_state"],
        "blocker_total": audit["blocker_total"],
        "blocker_ids": audit["blocker_ids"],
        "next_automatic_action": audit["next_automatic_action"],
        "execute_result": execute_result,
        "refs": refs,
        "no_send": True,
        "publish_allowed": False,
        "journal_submissions_allowed": False,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if execute_result is not None and execute_result.get("execution_state") not in {"PASS", "NOOP"}:
        if execute_result.get("execution_state") != "SCIENTIFIC_BLOCKERS_REMAIN":
            return 1
    if audit["all_domain_ready_no_send"]:
        return 0
    return 0 if args.allow_blocked_exit_zero else 2


if __name__ == "__main__":
    raise SystemExit(main())
