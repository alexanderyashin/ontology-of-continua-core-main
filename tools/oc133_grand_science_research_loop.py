from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MISSION_DIR_REL = "operations/logion_release_mission/oc_core_1_3_3"
MISSION_DIR = ROOT / MISSION_DIR_REL
PROGRAM_NAME = "OC133_GRAND_SCIENCE_RESEARCH_PROGRAM.json"
STATE_NAME = "OC133_GRAND_SCIENCE_LOOP_STATE.json"
REPORT_NAME = "OC133_GRAND_SCIENCE_LOOP_latest.json"
COCKPIT_NAME = "OC133_GRAND_SCIENCE_LOOP_latest.md"
SCORECARD_NAME = "OC133_ALL_DOMAIN_READINESS_SCORECARD.json"
WORK_ORDERS_NAME = "OC133_ALL_DOMAIN_WORK_ORDERS.json"

PROFILE_BY_OBLIGATION = {
    "OC133-GRAND-FORMAL-001": "v12_grand_formal_science_research_program",
    "OC133-GRAND-EMPIRICAL-001": "v12_grand_empirical_superiority_research_program",
    "OC133-GRAND-PRIORART-001": "v12_modern_science_comparator_research_program",
}

PROFILE_BY_CAPABILITY = {
    "Research/FormalScience": "v12_grand_formal_science_research_program",
    "Research/EmpiricalScience": "v12_grand_empirical_superiority_research_program",
    "Research/PriorArt": "v12_modern_science_comparator_research_program",
}

RunCommand = Callable[[list[str], int], dict[str, Any]]


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
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def rel(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def command(root: Path, cmd: list[str], timeout: int) -> dict[str, Any]:
    completed = subprocess.run(
        cmd,
        cwd=root,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=timeout,
    )
    return {
        "cmd": cmd,
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout[-3000:],
        "stderr_tail": completed.stderr[-3000:],
    }


def _mission_dir(root: Path) -> Path:
    return root / MISSION_DIR_REL


def _obligation_rows(program: dict[str, Any]) -> list[dict[str, Any]]:
    rows = program.get("all_obligations") or program.get("obligations") or []
    return [row for row in rows if isinstance(row, dict) and row.get("obligation_id")]


def _blocker_ids(program: dict[str, Any], scorecard: dict[str, Any]) -> list[str]:
    ids = scorecard.get("blocker_ids") or program.get("blocker_ids") or []
    if not isinstance(ids, list):
        return []
    return [str(item) for item in ids]


def _round_robin(rows: list[dict[str, Any]], cursor_id: str | None, limit: int) -> tuple[list[dict[str, Any]], str | None]:
    if not rows or limit <= 0:
        return [], cursor_id
    ids = [str(row["obligation_id"]) for row in rows]
    try:
        start = ids.index(cursor_id) if cursor_id in ids else 0
    except ValueError:
        start = 0
    ordered = rows[start:] + rows[:start]
    selected = ordered[: min(limit, len(ordered))]
    next_index = (start + len(selected)) % len(rows)
    return selected, ids[next_index]


def _dispatch_ordered_rows(rows: list[dict[str, Any]], dispatch: dict[str, Any]) -> list[dict[str, Any]]:
    dispatch_rows = dispatch.get("rows", [])
    if not isinstance(dispatch_rows, list) or not dispatch_rows:
        return rows
    capability_order: dict[str, int] = {}
    for index, row in enumerate(dispatch_rows):
        if not isinstance(row, dict):
            continue
        capability = str(row.get("owner_capability", ""))
        if capability and capability not in capability_order:
            capability_order[capability] = index
    if not capability_order:
        return rows
    return sorted(
        rows,
        key=lambda row: (
            capability_order.get(str(row.get("owner_capability", "")), len(capability_order) + 100),
            str(row.get("obligation_id", "")),
        ),
    )


def _profile_for(obligation: dict[str, Any]) -> str | None:
    obligation_id = str(obligation.get("obligation_id", ""))
    capability = str(obligation.get("owner_capability", ""))
    return PROFILE_BY_OBLIGATION.get(obligation_id) or PROFILE_BY_CAPABILITY.get(capability)


def _check_state(checks: dict[str, Any], blocker_check: str) -> str:
    row = checks.get(blocker_check, {})
    if not isinstance(row, dict):
        return "UNKNOWN"
    return str(row.get("state", "UNKNOWN"))


def _run_obligation(
    root: Path,
    obligation: dict[str, Any],
    program: dict[str, Any],
    runner: RunCommand,
    timeout: int,
    execute: bool,
) -> dict[str, Any]:
    blocker_check = str(obligation.get("blocker_check", ""))
    profile = _profile_for(obligation)
    before_state = _check_state(program.get("checks", {}), blocker_check)
    if not profile:
        command_result = {
            "cmd": [],
            "returncode": 97,
            "stdout_tail": "",
            "stderr_tail": "No Logion capability profile is registered for this obligation.",
        }
        action_state = "BLOCKED_NO_CAPABILITY_PROFILE"
    else:
        mode = "execute" if execute else "check"
        command_result = runner(
            [
                sys.executable,
                "tools/oc133_capability_repair_executor.py",
                "--profile",
                profile,
            ],
            timeout,
        )
        action_state = "COMMAND_PASS" if command_result.get("returncode") == 0 else "COMMAND_FAIL"

    refreshed_program = read_json(_mission_dir(root) / PROGRAM_NAME) or program
    refreshed_scorecard = read_json(_mission_dir(root) / SCORECARD_NAME)
    blocker_ids_after = _blocker_ids(refreshed_program, refreshed_scorecard)
    after_state = _check_state(refreshed_program.get("checks", {}), blocker_check)
    obligation_closed = blocker_check not in blocker_ids_after and after_state == "PASS"
    return {
        "obligation_id": obligation.get("obligation_id"),
        "owner_capability": obligation.get("owner_capability"),
        "title": obligation.get("title"),
        "blocker_check": blocker_check,
        "profile": profile,
        "action": "execute" if execute else "check",
        "action_state": action_state,
        "execution_state": "PASS" if obligation_closed and command_result.get("returncode") == 0 else "BLOCKED",
        "before_check_state": before_state,
        "after_check_state": after_state,
        "blocker_still_present": blocker_check in blocker_ids_after,
        "closure_predicate_satisfied": obligation_closed,
        "artifact_exists_is_not_closure": bool(obligation.get("artifact_exists_is_not_closure", True)),
        "command": command_result,
        "no_send": True,
        "publish_allowed": False,
        "journal_submissions_allowed": False,
    }


def run_loop(
    root: Path = ROOT,
    *,
    max_obligations: int | None = None,
    execute: bool = False,
    timeout: int = 900,
    runner: RunCommand | None = None,
) -> dict[str, Any]:
    runner = runner or (lambda cmd, seconds: command(root, cmd, seconds))
    mission_dir = _mission_dir(root)
    program_path = mission_dir / PROGRAM_NAME
    state_path = mission_dir / STATE_NAME
    report_path = mission_dir / REPORT_NAME
    cockpit_path = mission_dir / COCKPIT_NAME
    scorecard_path = mission_dir / SCORECARD_NAME
    dispatch_path = mission_dir / WORK_ORDERS_NAME

    program = read_json(program_path)
    scorecard = read_json(scorecard_path)
    dispatch = read_json(dispatch_path)
    obligations = _obligation_rows(program)
    blocker_ids = _blocker_ids(program, scorecard)
    open_rows = [row for row in obligations if str(row.get("blocker_check", "")) in blocker_ids]
    open_rows = _dispatch_ordered_rows(open_rows, dispatch)
    state = read_json(state_path)
    dispatch_queue_sha256 = dispatch.get("queue_sha256") if isinstance(dispatch, dict) else None
    previous_dispatch_queue_sha256 = state.get("dispatch_queue_sha256")
    if dispatch_queue_sha256 and dispatch_queue_sha256 != previous_dispatch_queue_sha256:
        cursor_id = None
    else:
        cursor_id = state.get("next_cursor_obligation_id")
    limit = len(open_rows) if max_obligations is None else max_obligations
    selected, next_cursor = _round_robin(open_rows, str(cursor_id) if cursor_id else None, limit)

    rows: list[dict[str, Any]] = []
    for obligation in selected:
        rows.append(_run_obligation(root, obligation, program, runner, timeout, execute))
        program = read_json(program_path) or program

    final_program = read_json(program_path) or program
    final_scorecard = read_json(scorecard_path)
    final_blocker_ids = _blocker_ids(final_program, final_scorecard)
    command_fail_total = sum(1 for row in rows if row.get("action_state") == "COMMAND_FAIL")
    blocked_total = sum(1 for row in rows if row.get("execution_state") != "PASS")
    if final_blocker_ids:
        verdict = "SCIENTIFIC_BLOCKERS_REMAIN"
    elif command_fail_total:
        verdict = "CAPABILITY_COMMAND_FAILED"
    elif blocked_total:
        verdict = "OBLIGATION_CLOSURE_INCOMPLETE"
    else:
        verdict = "PASS_NO_SEND"

    obligation_state_by_id = {
        str(row.get("obligation_id")): {
            "latest_execution_state": row.get("execution_state"),
            "latest_action_state": row.get("action_state"),
            "latest_blocker_still_present": row.get("blocker_still_present"),
            "latest_after_check_state": row.get("after_check_state"),
            "profile": row.get("profile"),
        }
        for row in rows
    }
    previous = state.get("obligation_state_by_id", {})
    if isinstance(previous, dict):
        merged_state = {**previous, **obligation_state_by_id}
    else:
        merged_state = obligation_state_by_id

    payload = {
        "schema_id": "OC133_GRAND_SCIENCE_LOOP_RUN_v1",
        "release_id": "oc_core_1_3_3",
        "version": "1.3.3",
        "mode": "execute" if execute else "check",
        "program_ref": f"{MISSION_DIR_REL}/{PROGRAM_NAME}",
        "state_ref": f"{MISSION_DIR_REL}/{STATE_NAME}",
        "all_domain_scorecard_ref": f"{MISSION_DIR_REL}/{SCORECARD_NAME}",
        "selected_obligation_total": len(selected),
        "selected_obligation_ids": [row.get("obligation_id") for row in selected],
        "next_cursor_obligation_id": next_cursor,
        "dispatch_queue_sha256": dispatch_queue_sha256,
        "blocker_ids_before": blocker_ids,
        "blocker_ids_after": final_blocker_ids,
        "all_domain_blocker_total_after": len(final_blocker_ids),
        "command_fail_total": command_fail_total,
        "blocked_obligation_total": blocked_total,
        "rows": rows,
        "verdict": verdict,
        "no_send": True,
        "publish_allowed": False,
        "journal_submissions_allowed": False,
    }
    state_payload = {
        "schema_id": "OC133_GRAND_SCIENCE_LOOP_STATE_v1",
        "release_id": "oc_core_1_3_3",
        "version": "1.3.3",
        "next_cursor_obligation_id": next_cursor,
        "dispatch_queue_sha256": dispatch_queue_sha256,
        "latest_verdict": verdict,
        "latest_selected_obligation_ids": payload["selected_obligation_ids"],
        "obligation_state_by_id": merged_state,
        "no_send": True,
        "publish_allowed": False,
        "journal_submissions_allowed": False,
    }
    write_json(state_path, state_payload)
    write_json(report_path, payload)
    cockpit_path.write_text(render_markdown(payload), encoding="utf-8")
    return payload


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# OC133 Grand Science Loop",
        "",
        f"- Verdict: `{payload['verdict']}`",
        f"- Mode: `{payload['mode']}`",
        f"- No-send: `{payload['no_send']}`",
        f"- Publish allowed: `{payload['publish_allowed']}`",
        f"- Journal submissions allowed: `{payload['journal_submissions_allowed']}`",
        f"- All-domain blockers after: `{payload['all_domain_blocker_total_after']}`",
        f"- Next cursor: `{payload.get('next_cursor_obligation_id')}`",
        "",
        "## Obligations",
    ]
    for row in payload.get("rows", []):
        lines.extend(
            [
                "",
                f"### {row.get('obligation_id')}",
                f"- Owner: `{row.get('owner_capability')}`",
                f"- Profile: `{row.get('profile')}`",
                f"- Action state: `{row.get('action_state')}`",
                f"- Execution state: `{row.get('execution_state')}`",
                f"- Blocker check: `{row.get('blocker_check')}`",
                f"- Blocker still present: `{row.get('blocker_still_present')}`",
                f"- Artifact existence is closure: `false`",
            ]
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Round-robin Logion grand science research loop for OC Core 1.3.3.")
    parser.add_argument("--execute", action="store_true", help="Execute capability profiles instead of check-only profile audits.")
    parser.add_argument("--max-obligations", type=int, default=None, help="Maximum obligations to visit this run; default visits every open obligation once.")
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument(
        "--allow-blocked-exit-zero",
        action="store_true",
        help="Return zero when the loop ran correctly but scientific blockers remain.",
    )
    args = parser.parse_args()
    payload = run_loop(max_obligations=args.max_obligations, execute=args.execute, timeout=args.timeout)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if payload["verdict"] == "PASS_NO_SEND":
        return 0
    return 0 if args.allow_blocked_exit_zero and payload["verdict"] == "SCIENTIFIC_BLOCKERS_REMAIN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
