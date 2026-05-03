from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

from oc133_manuscript_structure_l10_usability_auditor import run_audit as run_l10_usability_audit
from oc133_manuscript_structure_transfer_lib import (
    COMPANION_MIN_DEPTH,
    MAX_DEPTH,
    RELEASE_ID,
    STRUCTURE_DIR,
    VERSION,
    artifact_paths,
    companion_paths,
    index_paths,
    sha256_text,
    stable_json,
    standards_source_map_paths,
    write_text_if_changed,
)


ROOT = Path(__file__).resolve().parents[1]
FREEZE_VERSION = "1.0"
FREEZE_STATUS = "APPROVED_FROZEN_STRUCTURE_CASCADE_V1_0"


def freeze_paths() -> tuple[Path, Path]:
    stem = "MASTER_MANUSCRIPT_STRUCTURE_CASCADE_FREEZE_V1_0"
    return STRUCTURE_DIR / f"{stem}.json", STRUCTURE_DIR / f"{stem}.md"


def relative(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def payload_without_hash(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if key != "artifact_hash"}


def frozen_node_manifest(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "level": int(node["level"]),
            "node_id": node["node_id"],
            "order_path": node["order_path"],
            "outline_number": node["outline_number"],
            "parent_id": node["parent_id"],
            "status": node["status"],
            "title": node["title"],
        }
        for node in nodes
    ]


def build_freeze_payload() -> dict[str, Any]:
    index_json, _ = index_paths()
    standards_json, standards_md = standards_source_map_paths()
    l10_payload = read_json(artifact_paths(MAX_DEPTH)[0])
    l10_usability = run_l10_usability_audit()
    if l10_usability["state"] != "PASS":
        raise RuntimeError(f"L10 usability blocks freeze: {l10_usability}")

    structure_artifacts = []
    for depth in range(1, MAX_DEPTH + 1):
        json_path, md_path = artifact_paths(depth)
        payload = read_json(json_path)
        structure_artifacts.append(
            {
                "depth": depth,
                "json": relative(json_path),
                "markdown": relative(md_path),
                "artifact_hash": payload["artifact_hash"],
                "combined_hash": payload["combined_hash"],
                "node_counts": payload["node_counts"],
                "status": payload["status"],
            }
        )

    companion_artifacts = []
    for depth in range(COMPANION_MIN_DEPTH, MAX_DEPTH + 1):
        json_path, md_path = companion_paths(depth)
        payload = read_json(json_path)
        companion_artifacts.append(
            {
                "depth": depth,
                "json": relative(json_path),
                "markdown": relative(md_path),
                "artifact_hash": payload["artifact_hash"],
                "review_verdict": payload["review_gate_outputs"]["review_verdict"],
            }
        )

    payload: dict[str, Any] = {
        "artifact_kind": "MASTER_MANUSCRIPT_STRUCTURE_CASCADE_FREEZE",
        "body_prose_included": False,
        "freeze_version": FREEZE_VERSION,
        "status": FREEZE_STATUS,
        "release_id": RELEASE_ID,
        "source_version": VERSION,
        "owner_approval_basis": "Owner requested freeze after L10 usability has no objections.",
        "frozen_scope": "L01-L10 manuscript structure only: node IDs, titles, order, parent links, statuses, hashes, standards map, companions, and L10 usability.",
        "mutation_policy": {
            "delete_rename_reorder_collapse_forbidden": True,
            "append_only_requires_owner_override_marker": True,
            "prose_pdf_release_publication_generation_not_authorized": True,
        },
        "standards_source_map": {
            "json": relative(standards_json),
            "markdown": relative(standards_md),
            "artifact_hash": read_json(standards_json)["artifact_hash"],
        },
        "cascade_index": {
            "json": relative(index_json),
            "markdown": relative(index_paths()[1]),
            "artifact_hash": read_json(index_json)["artifact_hash"],
        },
        "structure_artifacts": structure_artifacts,
        "companion_artifacts": companion_artifacts,
        "l10_usability_audit": l10_usability,
        "frozen_node_manifest_hash": sha256_text(stable_json(frozen_node_manifest(l10_payload["combined_nodes"]))),
        "frozen_node_manifest": frozen_node_manifest(l10_payload["combined_nodes"]),
    }
    payload["artifact_hash"] = sha256_text(stable_json(payload_without_hash(payload)))
    return payload


def validate_freeze_payload(payload: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if payload.get("status") != FREEZE_STATUS:
        failures.append("freeze_status_mismatch")
    if payload.get("body_prose_included") is not False:
        failures.append("body_prose_flag_mismatch")
    l10_payload = read_json(artifact_paths(MAX_DEPTH)[0])
    current_manifest = frozen_node_manifest(l10_payload["combined_nodes"])
    if payload.get("frozen_node_manifest") != current_manifest:
        failures.append("frozen_node_manifest_mismatch")
    if payload.get("frozen_node_manifest_hash") != sha256_text(stable_json(current_manifest)):
        failures.append("frozen_node_manifest_hash_mismatch")
    if payload.get("l10_usability_audit", {}).get("state") != "PASS":
        failures.append("l10_usability_not_pass")
    if payload.get("artifact_hash") != sha256_text(stable_json(payload_without_hash(payload))):
        failures.append("freeze_artifact_hash_mismatch")
    companion_rows = payload.get("companion_artifacts", [])
    if len(companion_rows) != MAX_DEPTH - COMPANION_MIN_DEPTH + 1:
        failures.append("companion_artifact_total_mismatch")
    if any(row.get("review_verdict") != "PASS" for row in companion_rows):
        failures.append("companion_review_not_pass")
    return failures


def render_freeze_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Master Manuscript Structure Cascade Freeze v1.0",
        "",
        f"Status: {payload['status']}",
        f"Artifact hash: `{payload['artifact_hash']}`",
        f"Frozen node manifest hash: `{payload['frozen_node_manifest_hash']}`",
        "",
        "This is a structure-only freeze certificate. It freezes headings, node IDs, order, parent links, statuses, hashes, standards references, companion reviews, and L10 usability.",
        "",
        "## Mutation Policy",
        "",
    ]
    for key, value in payload["mutation_policy"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## L10 Usability", ""])
    audit = payload["l10_usability_audit"]
    for key in ["state", "terminal_node_total", "unique_terminal_title_total", "max_shared_terminal_title_ratio", "l2_chapter_total"]:
        lines.append(f"- {key}: {audit[key]}")
    lines.extend(["", "## Structure Artifacts", ""])
    for row in payload["structure_artifacts"]:
        lines.append(
            f"- L{row['depth']:02d}: {row['status']} combined={row['node_counts']['combined']} hash=`{row['artifact_hash']}`"
        )
    lines.extend(["", "## Companion Artifacts", ""])
    for row in payload["companion_artifacts"]:
        lines.append(f"- L{row['depth']:02d}: {row['review_verdict']} hash=`{row['artifact_hash']}`")
    return "\n".join(lines) + "\n"


def expected_files() -> dict[Path, str]:
    payload = build_freeze_payload()
    failures = validate_freeze_payload(payload)
    if failures:
        raise RuntimeError(f"Freeze validation failed: {failures}")
    json_path, md_path = freeze_paths()
    return {json_path: stable_json(payload), md_path: render_freeze_markdown(payload)}


def check_files(files: dict[Path, str]) -> dict[str, Any]:
    changed = []
    missing = []
    for path, text in files.items():
        if not path.exists():
            missing.append(relative(path))
        elif path.read_text(encoding="utf-8", errors="replace") != text:
            changed.append(relative(path))
    return {"state": "PASS" if not changed and not missing else "FAIL", "changed": changed, "missing": missing}


def write_files(files: dict[Path, str]) -> list[str]:
    changed = []
    for path, text in files.items():
        if write_text_if_changed(path, text):
            changed.append(relative(path))
    return changed


def run_self_tests() -> dict[str, Any]:
    failures = []
    payload = build_freeze_payload()

    deleted = copy.deepcopy(payload)
    deleted["frozen_node_manifest"] = deleted["frozen_node_manifest"][1:]
    if not validate_freeze_payload(deleted):
        failures.append("self_test_deleted_node_did_not_fail")

    renamed = copy.deepcopy(payload)
    renamed["frozen_node_manifest"][0]["title"] = renamed["frozen_node_manifest"][0]["title"] + " changed"
    if not validate_freeze_payload(renamed):
        failures.append("self_test_renamed_node_did_not_fail")

    reordered = copy.deepcopy(payload)
    reordered["frozen_node_manifest"] = list(reversed(reordered["frozen_node_manifest"]))
    if not validate_freeze_payload(reordered):
        failures.append("self_test_reordered_node_did_not_fail")

    appended = copy.deepcopy(payload)
    appended["frozen_node_manifest"].append(copy.deepcopy(appended["frozen_node_manifest"][-1]))
    appended["frozen_node_manifest"][-1]["node_id"] = "UNAPPROVED_APPEND_ONLY_TEST"
    if not validate_freeze_payload(appended):
        failures.append("self_test_unapproved_append_did_not_fail")

    return {"state": "PASS" if not failures else "FAIL", "failure_total": len(failures), "failures": failures}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Freeze OC Core manuscript structure cascade as v1.0.")
    parser.add_argument("--write", action="store_true", help="Write freeze artifacts if changed.")
    parser.add_argument("--check", action="store_true", help="Check freeze artifacts without writing.")
    parser.add_argument("--self-test", action="store_true", help="Run in-memory negative freeze tests.")
    args = parser.parse_args(argv)
    if not args.write and not args.check and not args.self_test:
        args.check = True

    result: dict[str, Any] = {}
    states = []
    if args.write or args.check:
        files = expected_files()
        action_result = {"changed": write_files(files), "missing": [], "state": "PASS"} if args.write else check_files(files)
        result["freeze_artifacts"] = action_result
        states.append(action_result["state"])
    if args.self_test:
        result["self_tests"] = run_self_tests()
        states.append(result["self_tests"]["state"])
    result["state"] = "PASS" if states and all(state == "PASS" for state in states) else "FAIL"
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["state"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
