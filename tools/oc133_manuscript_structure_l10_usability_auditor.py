from __future__ import annotations

import argparse
import copy
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from oc133_manuscript_structure_transfer_lib import (
    EXPECTED_L2_TOTAL,
    MAX_DEPTH,
    artifact_paths,
)


ROOT = Path(__file__).resolve().parents[1]
MAX_SHARED_TERMINAL_TITLE_RATIO = 0.05
REQUIRED_ARGUMENT_ROLES = {
    "definition_model",
    "proof_evidence",
    "limits_falsifier",
    "synthesis_transition",
}
REQUIRED_TERMINAL_METADATA = [
    "reader_task",
    "argument_role",
    "evidence_proof_source_route",
    "claim_boundary",
    "future_fill_control_hook",
]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def l2_chapter_key(node: dict[str, Any]) -> tuple[int, int]:
    path = node.get("order_path", [])
    if len(path) < 2:
        raise ValueError(f"Node lacks L2 order path: {node.get('node_id')}")
    return int(path[0]), int(path[1])


def audit_l10_payload(l10_payload: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    terminal_nodes = [
        node
        for node in l10_payload.get("own_expansion_nodes", [])
        if int(node.get("level", 0)) == MAX_DEPTH
    ]
    if not terminal_nodes:
        failures.append("l10_terminal_nodes_missing")

    title_counts = Counter(str(node.get("title", "")) for node in terminal_nodes)
    most_common_title, most_common_count = title_counts.most_common(1)[0] if title_counts else ("", 0)
    duplicate_ratio = most_common_count / len(terminal_nodes) if terminal_nodes else 1.0
    if duplicate_ratio > MAX_SHARED_TERMINAL_TITLE_RATIO:
        failures.append(
            f"terminal_title_duplicate_ratio_too_high::{most_common_title}::{duplicate_ratio:.4f}"
        )

    roles_by_chapter: dict[tuple[int, int], set[str]] = defaultdict(set)
    terminal_failures: list[str] = []
    for node in terminal_nodes:
        metadata = node.get("metadata") or {}
        for key in REQUIRED_TERMINAL_METADATA:
            if not metadata.get(key):
                terminal_failures.append(f"{node.get('node_id')}::missing_{key}")
        hook = metadata.get("future_fill_control_hook") or {}
        if hook.get("current_fill_maturity_status") != "not_assessed_this_phase":
            terminal_failures.append(f"{node.get('node_id')}::bad_fill_status")
        if set(hook.get("allowed_maturity_values", [])) != {"complete", "partial", "planned", "missing"}:
            terminal_failures.append(f"{node.get('node_id')}::bad_fill_values")
        argument_role = metadata.get("argument_role")
        if argument_role not in REQUIRED_ARGUMENT_ROLES:
            terminal_failures.append(f"{node.get('node_id')}::unknown_argument_role::{argument_role}")
        else:
            roles_by_chapter[l2_chapter_key(node)].add(argument_role)
        if str(node.get("title", "")).strip() in {"Paragraph Draft Slot", "Paragraph Slot"}:
            terminal_failures.append(f"{node.get('node_id')}::generic_terminal_title")
    failures.extend(terminal_failures[:50])
    if len(terminal_failures) > 50:
        failures.append(f"terminal_metadata_failure_overflow::{len(terminal_failures)}")

    if len(roles_by_chapter) != EXPECTED_L2_TOTAL:
        failures.append(f"l2_chapter_coverage_total_mismatch::{len(roles_by_chapter)}")
    missing_role_rows = []
    for chapter_key, roles in sorted(roles_by_chapter.items()):
        missing = sorted(REQUIRED_ARGUMENT_ROLES - roles)
        if missing:
            missing_role_rows.append({"chapter_key": chapter_key, "missing_roles": missing})
    if missing_role_rows:
        failures.append(f"l2_chapter_missing_semantic_paths::{missing_role_rows[:10]}")

    return {
        "state": "PASS" if not failures else "FAIL",
        "failure_total": len(failures),
        "failures": failures,
        "terminal_node_total": len(terminal_nodes),
        "unique_terminal_title_total": len(title_counts),
        "max_shared_terminal_title_ratio": round(duplicate_ratio, 6),
        "most_common_terminal_title": most_common_title,
        "l2_chapter_total": len(roles_by_chapter),
        "required_argument_roles": sorted(REQUIRED_ARGUMENT_ROLES),
    }


def run_audit() -> dict[str, Any]:
    l10_payload = read_json(artifact_paths(MAX_DEPTH)[0])
    return audit_l10_payload(l10_payload)


def run_self_tests() -> dict[str, Any]:
    failures: list[str] = []
    l10_payload = read_json(artifact_paths(MAX_DEPTH)[0])

    bad_duplicate = copy.deepcopy(l10_payload)
    for node in bad_duplicate["own_expansion_nodes"]:
        node["title"] = "Paragraph Draft Slot"
    if audit_l10_payload(bad_duplicate)["state"] != "FAIL":
        failures.append("self_test_duplicate_titles_did_not_fail")

    bad_metadata = copy.deepcopy(l10_payload)
    bad_metadata["own_expansion_nodes"][0]["metadata"].pop("reader_task", None)
    if audit_l10_payload(bad_metadata)["state"] != "FAIL":
        failures.append("self_test_missing_metadata_did_not_fail")

    bad_role = copy.deepcopy(l10_payload)
    first_chapter = l2_chapter_key(bad_role["own_expansion_nodes"][0])
    bad_role["own_expansion_nodes"] = [
        node
        for node in bad_role["own_expansion_nodes"]
        if not (
            l2_chapter_key(node) == first_chapter
            and (node.get("metadata") or {}).get("argument_role") == "limits_falsifier"
        )
    ]
    if audit_l10_payload(bad_role)["state"] != "FAIL":
        failures.append("self_test_missing_l2_role_path_did_not_fail")

    return {
        "state": "PASS" if not failures else "FAIL",
        "failure_total": len(failures),
        "failures": failures,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit L10 usability for OC133 manuscript structure.")
    parser.add_argument("--check", action="store_true", help="Audit current L10 structure.")
    parser.add_argument("--self-test", action="store_true", help="Run in-memory negative tests.")
    args = parser.parse_args(argv)
    if not args.check and not args.self_test:
        args.check = True

    result: dict[str, Any] = {}
    states: list[str] = []
    if args.check:
        result["l10_usability_audit"] = run_audit()
        states.append(result["l10_usability_audit"]["state"])
    if args.self_test:
        result["self_tests"] = run_self_tests()
        states.append(result["self_tests"]["state"])
    result["state"] = "PASS" if states and all(state == "PASS" for state in states) else "FAIL"
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["state"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
