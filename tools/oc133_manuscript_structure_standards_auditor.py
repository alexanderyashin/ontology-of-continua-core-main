from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path
from typing import Any

from oc133_manuscript_structure_transfer_lib import (
    COMPANION_MIN_DEPTH,
    EXPECTED_L1_TOTAL,
    EXPECTED_L2_TOTAL,
    MAX_DEPTH,
    STANDARD_DERIVED_POSITIVE_CRITERIA,
    STANDARD_SOURCE_REQUIREMENTS,
    STANDARD_SOURCE_URLS,
    artifact_paths,
    companion_paths,
    validate_companion_payload,
    validate_level_payload,
    validate_standards_source_map_payload,
    standards_source_map_paths,
)


ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN_SURFACE_PATTERNS = [
    re.compile(pattern, re.I)
    for pattern in [
        r"\bNO_SEND\b",
        r"\bpublish_allowed\b",
        r"\bowner_approved\b",
        r"\bgithub\b",
        r"\bzenodo\b",
        r"\brelease[-_ ]machine\b",
        r"\bcontrol[-_ ]plane\b",
        r"\broute sheet\b",
        r"\bchecksum wall\b",
        r"\bTODO\b",
        r"\bPLACEHOLDER\b",
        r"\.pdf\b",
        r"\.zip\b",
    ]
]


def relative(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def scan_forbidden_text(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    failures: list[str] = []
    for pattern in FORBIDDEN_SURFACE_PATTERNS:
        if pattern.search(text):
            failures.append(f"forbidden_surface_text::{relative(path)}::{pattern.pattern}")
    return failures


def companion_positive_gate_failures(companion: dict[str, Any], structure_payload: dict[str, Any]) -> list[str]:
    failures = validate_companion_payload(companion, structure_payload)
    source_map = companion.get("standards_source_map", {})
    if not source_map.get("json") or not source_map.get("markdown") or not source_map.get("artifact_hash"):
        failures.append("companion_missing_standards_source_map_reference")

    source_ids = set(STANDARD_SOURCE_URLS)
    companion_source_ids = {anchor.get("id") for anchor in companion.get("standard_anchors", [])}
    if companion_source_ids != source_ids:
        failures.append("companion_standard_anchor_set_mismatch")

    requirements_by_id = {item["id"]: item for item in STANDARD_SOURCE_REQUIREMENTS}
    criteria = companion.get("standard_derived_positive_criteria", [])
    if len(criteria) != len(STANDARD_DERIVED_POSITIVE_CRITERIA):
        failures.append("companion_standard_criteria_total_mismatch")
    for criterion in criteria:
        criterion_id = criterion.get("criterion_id", "UNKNOWN")
        if criterion.get("status") != "PLANNED_IN_STRUCTURE":
            failures.append(f"criterion_not_planned::{criterion_id}")
        if not criterion.get("criterion"):
            failures.append(f"criterion_missing_text::{criterion_id}")
        refs = criterion.get("exact_standard_source_refs", [])
        if not refs:
            failures.append(f"criterion_missing_exact_source_refs::{criterion_id}")
        for requirement_id in criterion.get("source_requirement_ids", []):
            if requirement_id not in requirements_by_id:
                failures.append(f"criterion_unknown_source_requirement::{criterion_id}::{requirement_id}")
        for ref in refs:
            if not ref.get("source_url") or ref.get("id") not in requirements_by_id:
                failures.append(f"criterion_bad_source_ref::{criterion_id}")
        if not criterion.get("matched_keywords"):
            failures.append(f"criterion_keyword_only_or_unmatched::{criterion_id}")

    gate = companion.get("review_gate_outputs", {})
    if int(gate.get("standards_criterion_coverage_score", 0)) != 100:
        failures.append("standards_criterion_coverage_score_not_100")
    if int(gate.get("sequence_order_score", 0)) != 100:
        failures.append("sequence_order_score_not_100")
    if gate.get("review_verdict") == "PASS" and not criteria:
        failures.append("pass_without_criteria_objects")

    contract = companion.get("next_level_contract", {})
    for key in ["must_preserve", "must_add", "must_not_change", "verification_commands"]:
        if not contract.get(key):
            failures.append(f"next_level_contract_missing::{key}")
    if not companion.get("level_specific_rationale"):
        failures.append("missing_level_specific_rationale")
    if not companion.get("rejected_alternatives"):
        failures.append("missing_rejected_alternatives")
    if not companion.get("node_expectation_index"):
        failures.append("missing_node_expectation_index")
    for item in companion.get("node_expectation_index", []):
        hook = item.get("future_fill_control_hook", {})
        if "not_assessed_this_phase" != hook.get("current_fill_maturity_status"):
            failures.append(f"bad_fill_hook_status::{item.get('node_id')}")
        if set(hook.get("allowed_maturity_values", [])) != {"complete", "partial", "planned", "missing"}:
            failures.append(f"bad_fill_hook_values::{item.get('node_id')}")
    return failures


def audit_existing_package() -> dict[str, Any]:
    failures: list[str] = []
    standards_json, standards_md = standards_source_map_paths()
    if not standards_json.exists() or not standards_md.exists():
        failures.append("missing_standards_source_map_artifacts")
    else:
        standards_payload = read_json(standards_json)
        failures.extend(validate_standards_source_map_payload(standards_payload))
        standards_text = standards_md.read_text(encoding="utf-8", errors="replace")
        for source_id, url in STANDARD_SOURCE_URLS.items():
            if source_id not in standards_text or url not in standards_text:
                failures.append(f"standards_markdown_missing_source::{source_id}")
        failures.extend(scan_forbidden_text(standards_md))

    structure_payloads: list[dict[str, Any]] = []
    companion_count = 0
    for depth in range(1, MAX_DEPTH + 1):
        json_path, md_path = artifact_paths(depth)
        if not json_path.exists() or not md_path.exists():
            failures.append(f"missing_structure_artifact::L{depth:02d}")
            continue
        payload = read_json(json_path)
        structure_payloads.append(payload)
        parent = structure_payloads[depth - 2] if depth > 1 and len(structure_payloads) >= depth - 1 else None
        failures.extend(f"L{depth:02d}::{failure}" for failure in validate_level_payload(payload, parent))
        failures.extend(scan_forbidden_text(md_path))
        if depth >= COMPANION_MIN_DEPTH:
            companion_json, companion_md = companion_paths(depth)
            if not companion_json.exists() or not companion_md.exists():
                failures.append(f"missing_companion_artifact::L{depth:02d}")
                continue
            companion_count += 1
            companion = read_json(companion_json)
            failures.extend(
                f"L{depth:02d}_COMPANION::{failure}"
                for failure in companion_positive_gate_failures(companion, payload)
            )
            companion_text = companion_md.read_text(encoding="utf-8", errors="replace")
            for source_id, url in STANDARD_SOURCE_URLS.items():
                if source_id not in companion_text or url not in companion_text:
                    failures.append(f"L{depth:02d}_COMPANION::markdown_missing_source::{source_id}")
            for criterion in STANDARD_DERIVED_POSITIVE_CRITERIA:
                if criterion["id"] not in companion_text:
                    failures.append(f"L{depth:02d}_COMPANION::markdown_missing_criterion::{criterion['id']}")
            failures.extend(scan_forbidden_text(companion_md))

    if structure_payloads:
        if structure_payloads[0]["node_counts"]["own_expansion"] != EXPECTED_L1_TOTAL:
            failures.append("l1_total_mismatch")
        if len(structure_payloads) >= 2 and structure_payloads[1]["node_counts"]["own_expansion"] != EXPECTED_L2_TOTAL:
            failures.append("l2_total_mismatch")
    if companion_count != MAX_DEPTH - COMPANION_MIN_DEPTH + 1:
        failures.append("companion_count_mismatch")

    return {
        "state": "PASS" if not failures else "FAIL",
        "failure_total": len(failures),
        "failures": failures,
        "checked_depth_total": len(structure_payloads),
        "companion_checked_total": companion_count,
    }


def run_self_tests() -> dict[str, Any]:
    failures: list[str] = []
    standards_json, _ = standards_source_map_paths()
    source_map = read_json(standards_json)
    bad_source_map = copy.deepcopy(source_map)
    bad_source_map["sources"] = bad_source_map["sources"][1:]
    if not validate_standards_source_map_payload(bad_source_map):
        failures.append("self_test_missing_standard_source_did_not_fail")

    l1 = read_json(artifact_paths(1)[0])
    l2 = read_json(artifact_paths(2)[0])
    l2_bad_inherited = copy.deepcopy(l2)
    l2_bad_inherited["inherited_locked_nodes"] = l2_bad_inherited["inherited_locked_nodes"][1:]
    if not validate_level_payload(l2_bad_inherited, l1):
        failures.append("self_test_inherited_deletion_did_not_fail")

    l2_bad_reorder = copy.deepcopy(l2)
    l2_bad_reorder["inherited_locked_nodes"] = list(reversed(l2_bad_reorder["inherited_locked_nodes"]))
    if not validate_level_payload(l2_bad_reorder, l1):
        failures.append("self_test_inherited_reorder_did_not_fail")

    l2_bad_count = copy.deepcopy(l2)
    l2_bad_count["own_expansion_nodes"] = l2_bad_count["own_expansion_nodes"][1:]
    l2_bad_count["node_counts"]["own_expansion"] -= 1
    if not validate_level_payload(l2_bad_count, l1):
        failures.append("self_test_l2_count_drift_did_not_fail")

    companion = read_json(companion_paths(2)[0])
    bad_companion = copy.deepcopy(companion)
    bad_companion["standard_derived_positive_criteria"] = []
    if not companion_positive_gate_failures(bad_companion, l2):
        failures.append("self_test_generic_companion_did_not_fail")

    fake_text = ROOT / "NUL"
    forbidden_samples = [
        "TODO",
        "NO_SEND",
        "release-machine",
        "route sheet",
        "artifact.pdf",
        "payload.zip",
    ]
    for sample in forbidden_samples:
        if not any(pattern.search(sample) for pattern in FORBIDDEN_SURFACE_PATTERNS):
            failures.append(f"self_test_forbidden_pattern_not_detected::{sample}")
    _ = fake_text  # keeps the self-test read-only; samples are checked in memory.

    return {
        "state": "PASS" if not failures else "FAIL",
        "failure_total": len(failures),
        "failures": failures,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only standards auditor for OC133 manuscript structure companions.")
    parser.add_argument("--check", action="store_true", help="Audit existing structure/companion artifacts.")
    parser.add_argument("--self-test", action="store_true", help="Run in-memory negative tests without writing files.")
    args = parser.parse_args(argv)
    if not args.check and not args.self_test:
        args.check = True

    result: dict[str, Any] = {}
    states: list[str] = []
    if args.check:
        result["package_audit"] = audit_existing_package()
        states.append(result["package_audit"]["state"])
    if args.self_test:
        result["self_tests"] = run_self_tests()
        states.append(result["self_tests"]["state"])
    result["state"] = "PASS" if states and all(state == "PASS" for state in states) else "FAIL"
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["state"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
