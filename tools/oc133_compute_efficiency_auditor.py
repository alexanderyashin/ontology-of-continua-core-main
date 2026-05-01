from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

SCHEMA_ID = "OC133_COMPUTE_EFFICIENCY_AUDIT_v1"
MISSION_ID = "OC_CORE_1_3_3_PLATINUM_RELEASE_MISSION"
RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"
MISSION_DIR_REL = "operations/logion_release_mission/oc_core_1_3_3"

WORK_ORDERS_REL = f"{MISSION_DIR_REL}/OC133_ALL_DOMAIN_WORK_ORDERS.json"
SCORECARD_REL = f"{MISSION_DIR_REL}/OC133_ALL_DOMAIN_READINESS_SCORECARD.json"
EXECUTION_LEDGER_REL = f"{MISSION_DIR_REL}/OC133_ALL_DOMAIN_EXECUTION_LEDGER.json"
COVERAGE_QUEUE_REL = "reports/OC_CORE_1_3_3_MODERN_SCIENCE_COVERAGE_LANE_QUEUE.json"
AUDIT_REL = f"{MISSION_DIR_REL}/OC133_COMPUTE_EFFICIENCY_AUDIT.json"
COCKPIT_REL = f"{MISSION_DIR_REL}/OC133_COMPUTE_EFFICIENCY_COCKPIT.md"

TOP_WINDOW = 10
REPEAT_WARNING_THRESHOLD = 3


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not text.endswith("\n"):
        text += "\n"
    path.write_text(text, encoding="utf-8", newline="\n")


def canonical_sha256(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def file_sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def payload_rows(payload: dict[str, Any], *keys: str) -> list[dict[str, Any]]:
    for key in keys:
        rows = payload.get(key)
        if isinstance(rows, list):
            return [row for row in rows if isinstance(row, dict)]
    return []


def work_order_id(row: dict[str, Any]) -> str:
    return str(row.get("work_order_id") or row.get("id") or row.get("stable_id") or "UNKNOWN_WORK_ORDER")


def executor(row: dict[str, Any]) -> dict[str, Any]:
    value = row.get("executor")
    return value if isinstance(value, dict) else {}


def executor_mode(row: dict[str, Any]) -> str:
    value = row.get("executor_mode") or executor(row).get("mode")
    if value:
        return str(value)
    command = str(row.get("verification_command") or executor(row).get("command") or "")
    if "coverage_lane_dispatcher.py --check" in command:
        return "planning_queue_validation"
    if "oc133_capability_repair_executor.py" in command:
        return "capability_profile"
    return "unknown"


def command_text(row: dict[str, Any]) -> str:
    command = executor(row).get("command") or row.get("verification_command")
    if command:
        return str(command)
    argv = executor(row).get("argv")
    if isinstance(argv, list):
        return " ".join(str(item) for item in argv)
    return ""


def mode_bucket(mode: str) -> str:
    if mode == "planning_queue_validation":
        return "planning_only"
    if mode == "domain_local_replay":
        return "domain_local_replay"
    if mode == "capability_profile":
        return "capability_profile"
    return "unknown"


def top_row_summary(row: dict[str, Any], rank: int) -> dict[str, Any]:
    mode = executor_mode(row)
    return {
        "rank": rank,
        "work_order_id": work_order_id(row),
        "owner_capability": row.get("owner_capability") or executor(row).get("owner_capability") or "UNKNOWN",
        "executor_mode": mode,
        "mode_bucket": mode_bucket(mode),
        "command": command_text(row),
        "closure_policy": executor(row).get("closure_policy") or row.get("closure_policy"),
        "planning_only_cannot_close_science": mode == "planning_queue_validation",
    }


def repeated_execution_summary(ledger: dict[str, Any]) -> dict[str, Any]:
    rows = payload_rows(ledger, "rows")
    counts = Counter(work_order_id(row) for row in rows)
    repeated = [
        {"work_order_id": item, "execution_count": count}
        for item, count in sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))
        if count >= REPEAT_WARNING_THRESHOLD
    ]
    fail_count = sum(1 for row in rows if str(row.get("execution_state")) == "FAIL")
    blocked_count = sum(1 for row in rows if str(row.get("after_final_readiness_state")) == "SCIENTIFIC_BLOCKERS_REMAIN")
    return {
        "ledger_row_total": len(rows),
        "ledger_pass_total": ledger.get("pass_total"),
        "ledger_fail_total": ledger.get("fail_total", fail_count),
        "ledger_scientific_blocked_total": ledger.get("scientific_blocked_total", blocked_count),
        "repeated_work_order_total": len(repeated),
        "repeated_work_orders": repeated[:20],
        "latest_work_order_id": ledger.get("latest_work_order_id"),
        "latest_execution_state": ledger.get("latest_execution_state"),
    }


def input_refs(root: Path) -> list[dict[str, Any]]:
    refs = [WORK_ORDERS_REL, SCORECARD_REL, EXECUTION_LEDGER_REL, COVERAGE_QUEUE_REL]
    return [
        {
            "ref": item,
            "exists": (root / item).exists(),
            "sha256": file_sha256(root / item),
        }
        for item in refs
    ]


def next_efficient_action(top_rows: list[dict[str, Any]], scorecard: dict[str, Any]) -> dict[str, Any]:
    if not top_rows:
        return {
            "action_id": "REFRESH_ALL_DOMAIN_WORK_ORDER_QUEUE",
            "reason": "No active work-order rows are visible.",
            "allowed": True,
        }
    top = top_rows[0]
    if top["executor_mode"] == "planning_queue_validation":
        return {
            "action_id": f"ROUTE_REAL_EXECUTOR_FOR_{top['work_order_id']}",
            "reason": "The current top work order only validates the planning queue; rerunning it cannot close a scientific blocker.",
            "allowed": True,
            "blocked_actions": [
                f"EXECUTE_{top['work_order_id']}_AS_PLANNING_ONLY",
                "FULL_CERBERUS_SUITE_BEFORE_BLOCKER_DELTA",
                "FULL_RELEASE_MACHINE_EVALUATE_BEFORE_BLOCKER_DELTA",
            ],
            "required_before_execution": [
                "executor_mode_is_domain_local_replay_or_capability_profile",
                "expected_blocker_delta_declared",
                "focused_verification_command_declared",
            ],
        }
    if top["executor_mode"] == "capability_profile":
        return {
            "action_id": f"EXECUTE_FOCUSED_CAPABILITY_PROFILE_{top['work_order_id']}",
            "reason": "The next row has a real Logion capability executor; run only its focused command and then re-audit blocker delta.",
            "allowed": True,
            "blocked_actions": ["FULL_CERBERUS_SUITE_BEFORE_BLOCKER_DELTA"],
        }
    return {
        "action_id": f"EXECUTE_FOCUSED_{top['work_order_id']}",
        "reason": "The next row is not planning-only; keep execution narrow and require blocker-delta evidence.",
        "allowed": True,
        "blocked_actions": ["BROAD_TEST_BUNDLE_WITHOUT_ARTIFACT_HASH_DELTA"],
        "current_final_state": scorecard.get("final_readiness_state"),
    }


def build_audit(root: Path = ROOT) -> dict[str, Any]:
    work_orders = read_json(root / WORK_ORDERS_REL)
    scorecard = read_json(root / SCORECARD_REL)
    ledger = read_json(root / EXECUTION_LEDGER_REL)
    coverage_queue = read_json(root / COVERAGE_QUEUE_REL)

    rows = payload_rows(work_orders, "rows", "work_orders")
    top_rows = [top_row_summary(row, idx + 1) for idx, row in enumerate(rows[:TOP_WINDOW])]
    mode_counts = Counter(row["mode_bucket"] for row in top_rows)
    repeated = repeated_execution_summary(ledger)
    blocker_ids = scorecard.get("blocker_ids")
    if not isinstance(blocker_ids, list):
        blocker_ids = []

    findings = {
        "top_window": TOP_WINDOW,
        "top_work_order_total": len(top_rows),
        "top_work_order_mode_counts": dict(sorted(mode_counts.items())),
        "planning_only_top_work_order_total": mode_counts.get("planning_only", 0),
        "capability_profile_top_work_order_total": mode_counts.get("capability_profile", 0),
        "domain_local_replay_top_work_order_total": mode_counts.get("domain_local_replay", 0),
        "unknown_executor_top_work_order_total": mode_counts.get("unknown", 0),
        "known_blocker_total": int(scorecard.get("blocker_total") or len(blocker_ids)),
        "known_blocker_ids": [str(item) for item in blocker_ids],
        "final_readiness_state": scorecard.get("final_readiness_state"),
        "coverage_queue_size": coverage_queue.get("queue_size"),
        "coverage_executable_lane_total": coverage_queue.get("executable_lane_total"),
        "execution_repetition": repeated,
    }

    policy = {
        "mode": "ECONOMY_UNTIL_DETERMINISTIC_BLOCKER_DELTA",
        "max_active_subagents": 1,
        "default_active_subagents": 0,
        "spawn_subagent_allowed_only_for": [
            "single bounded artifact family",
            "disjoint write scope",
            "declared expected blocker delta",
        ],
        "full_cerberus_allowed": False,
        "full_release_evaluate_allowed": False,
        "full_reproducibility_allowed": False,
        "focused_tests_only": True,
        "rerun_broad_checks_after": [
            "G57_G58_G59_G70 blocker delta",
            "new evidence lane closes by deterministic audit",
            "journal package/material package milestone",
        ],
        "do_not_execute": [
            "planning_queue_validation rows as if they were scientific repair",
            "same capability profile three times without input hash delta",
            "full Cerberus while known deterministic blockers remain unchanged",
        ],
    }

    audit = {
        "schema_id": SCHEMA_ID,
        "mission_id": MISSION_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "state": "COMPUTE_EFFICIENCY_GUARD_ACTIVE",
        "no_send": True,
        "publish_allowed": False,
        "journal_submissions_allowed": False,
        "user_budget_signal": {
            "weekly_compute_remaining_reported_by_owner": "48%",
            "budget_risk": "HIGH",
            "response": "narrow deterministic execution only until blocker-delta evidence exists",
        },
        "input_refs": input_refs(root),
        "input_set_sha256": canonical_sha256(input_refs(root)),
        "findings": findings,
        "top_work_orders": top_rows,
        "efficiency_policy": policy,
        "next_efficient_action": next_efficient_action(top_rows, scorecard),
        "audit_sha256": "",
    }
    audit["audit_sha256"] = canonical_sha256({key: value for key, value in audit.items() if key != "audit_sha256"})
    return audit


def render_cockpit(audit: dict[str, Any]) -> str:
    findings = audit["findings"]
    action = audit["next_efficient_action"]
    rows = audit["top_work_orders"][:5]
    lines = [
        "# OC133 Compute Efficiency Cockpit",
        "",
        f"- State: `{audit['state']}`",
        f"- Owner budget signal: `{audit['user_budget_signal']['weekly_compute_remaining_reported_by_owner']}` remaining; risk `{audit['user_budget_signal']['budget_risk']}`",
        f"- Final readiness state: `{findings.get('final_readiness_state')}`",
        f"- Known blockers: `{findings.get('known_blocker_total')}`",
        f"- Top planning-only rows: `{findings.get('planning_only_top_work_order_total')}` / `{findings.get('top_work_order_total')}`",
        f"- Repeated work orders above threshold: `{findings['execution_repetition'].get('repeated_work_order_total')}`",
        f"- Next economical action: `{action.get('action_id')}`",
        f"- Reason: {action.get('reason')}",
        "",
        "## Guardrails",
        "",
        "- Default active subagents: `0`; maximum active subagents: `1`.",
        "- Full Cerberus/release/reproducibility runs stay blocked until deterministic blocker delta exists.",
        "- Planning-only rows must be routed to real Logion executors before they may consume execution budget.",
        "- Focused checks only after artifact edits; broad suites only at milestone boundaries.",
        "",
        "## Top Queue",
        "",
    ]
    for row in rows:
        lines.append(
            f"- `{row['rank']}` `{row['work_order_id']}` -> `{row['executor_mode']}` / `{row['owner_capability']}`"
        )
    lines.extend(["", f"Audit hash: `{audit['audit_sha256']}`", ""])
    return "\n".join(lines)


def check_stored(root: Path, audit: dict[str, Any]) -> list[str]:
    expected_md = render_cockpit(audit)
    mismatches: list[str] = []
    actual_json = read_json(root / AUDIT_REL)
    if actual_json != audit:
        mismatches.append(AUDIT_REL)
    if not (root / COCKPIT_REL).exists() or (root / COCKPIT_REL).read_text(encoding="utf-8") != expected_md:
        mismatches.append(COCKPIT_REL)
    return mismatches


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit OC133 compute efficiency before expensive Logion runs.")
    parser.add_argument("--root", default=str(ROOT), help="repository root")
    parser.add_argument("--write", action="store_true", help="write compute audit and cockpit")
    parser.add_argument("--check", action="store_true", help="check stored audit and cockpit")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    audit = build_audit(root)
    if args.write:
        write_json(root / AUDIT_REL, audit)
        write_text(root / COCKPIT_REL, render_cockpit(audit))
    if args.check:
        mismatches = check_stored(root, audit)
        if mismatches:
            print(json.dumps({"state": "FAIL", "mismatches": mismatches}, ensure_ascii=False, indent=2))
            return 1
    print(
        json.dumps(
            {
                "state": audit["state"],
                "audit_ref": AUDIT_REL,
                "cockpit_ref": COCKPIT_REL,
                "known_blocker_total": audit["findings"]["known_blocker_total"],
                "planning_only_top_work_order_total": audit["findings"]["planning_only_top_work_order_total"],
                "next_efficient_action": audit["next_efficient_action"]["action_id"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
