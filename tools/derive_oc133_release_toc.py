from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from build_oc133_science_to_l10_mapping import ALLOWED_COVERAGE_STATUSES, mapping_paths
from derive_general_oc_core_monograph_target_structure import target_paths
from oc133_manuscript_structure_transfer_lib import (
    EDITORIAL,
    sha256_text,
    stable_json,
    write_text_if_changed,
)


ROOT = Path(__file__).resolve().parents[1]
TOC_DIR = EDITORIAL / "oc_core_1_3_3_release_table_of_content"
TOC_STATUS = "DRAFT_RELEASE_ASSEMBLY_TOC_FROM_TARGET_AND_SCIENCE_MAPPING"


def toc_paths() -> dict[str, Path]:
    return {
        "toc_json": TOC_DIR / "OC_CORE_1_3_3_RELEASE_TABLE_OF_CONTENT.json",
        "toc_md": TOC_DIR / "OC_CORE_1_3_3_RELEASE_TABLE_OF_CONTENT.md",
        "audit_json": TOC_DIR / "OC_CORE_1_3_3_RELEASE_TABLE_OF_CONTENT_AUDIT.json",
        "audit_md": TOC_DIR / "OC_CORE_1_3_3_RELEASE_TABLE_OF_CONTENT_AUDIT.md",
    }


def relative(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def payload_without_hash(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if key != "artifact_hash"}


def path_is_prefix(prefix: list[int], path: list[int]) -> bool:
    return len(prefix) <= len(path) and path[: len(prefix)] == prefix


def unique_source_family_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    families = []
    for row in rows:
        for family in row.get("source_families", []):
            family_id = family["id"]
            if family_id in seen:
                continue
            seen.add(family_id)
            families.append(family)
    return families


def build_toc_payload() -> dict[str, Any]:
    target_json, _ = target_paths()
    mapping_json = mapping_paths()["mapping_json"]
    target = read_json(target_json)
    mapping = read_json(mapping_json)
    mapping_by_l10 = {row["l10_node_id"]: row for row in mapping["mapping_rows"]}

    l10_rows = mapping["mapping_rows"]
    toc_nodes = []
    for target_node in target["target_nodes"]:
        source_node_id = target_node["source_cascade_node_id"]
        order_path = target_node["order_path"]
        direct_mapping = mapping_by_l10.get(source_node_id)
        descendant_rows = [
            row
            for row in l10_rows
            if path_is_prefix(order_path, [int(part) for part in row["outline_number"].split(".")])
        ]
        source_families = direct_mapping["source_families"] if direct_mapping else unique_source_family_rows(descendant_rows)
        coverage_status = direct_mapping["coverage_status"] if direct_mapping else "not_assessed"
        toc_nodes.append(
            {
                "toc_node_id": "OC133-RELEASE-TOC-" + target_node["target_node_id"].replace("OC-GEN-MONO-", ""),
                "target_node_id": target_node["target_node_id"],
                "source_cascade_node_id": source_node_id,
                "level": target_node["level"],
                "outline_number": target_node["outline_number"],
                "title": target_node["source_title"],
                "target_obligation": f"Fulfill the monograph target obligation for: {target_node['title']}",
                "coverage_status": coverage_status,
                "source_families": source_families,
                "direct_l10_mapping_id": direct_mapping["mapping_id"] if direct_mapping else None,
                "descendant_l10_mapping_total": len(descendant_rows),
                "extraction_rule": direct_mapping["extraction_rule"] if direct_mapping else "Roll up source candidates from descendant L10 mapping rows during fill-control.",
                "integration_rule": direct_mapping["integration_rule"] if direct_mapping else "Use descendant L10 support rows to assemble this structural branch without changing frozen structure.",
                "verification_rule": direct_mapping["verification_rule"] if direct_mapping else "Verify every descendant L10 slot before marking this branch complete or partial.",
            }
        )

    payload: dict[str, Any] = {
        "artifact_kind": "OC_CORE_1_3_3_RELEASE_TABLE_OF_CONTENT",
        "body_prose_included": False,
        "status": TOC_STATUS,
        "source_target_structure": {
            "json": relative(target_json),
            "artifact_hash": target["artifact_hash"],
        },
        "source_science_to_l10_mapping": {
            "json": relative(mapping_json),
            "artifact_hash": mapping["artifact_hash"],
        },
        "allowed_coverage_statuses": ALLOWED_COVERAGE_STATUSES,
        "toc_node_total": len(toc_nodes),
        "toc_nodes": toc_nodes,
        "assembly_policy": {
            "toc_is_guidance_not_manuscript": True,
            "assembly_writes_separate_manuscript_sources_only": True,
            "frozen_structure_must_not_be_mutated_by_assembly": True,
            "coverage_statuses_are_reserved_until_fill_assessment": True,
        },
    }
    payload["artifact_hash"] = sha256_text(stable_json(payload_without_hash(payload)))
    return payload


def validate_toc_payload(payload: dict[str, Any]) -> list[str]:
    failures = []
    target = read_json(target_paths()[0])
    mapping = read_json(mapping_paths()["mapping_json"])
    if payload.get("source_target_structure", {}).get("artifact_hash") != target.get("artifact_hash"):
        failures.append("target_hash_mismatch")
    if payload.get("source_science_to_l10_mapping", {}).get("artifact_hash") != mapping.get("artifact_hash"):
        failures.append("mapping_hash_mismatch")
    if payload.get("toc_node_total") != len(target.get("target_nodes", [])):
        failures.append("toc_node_total_mismatch")
    for node in payload.get("toc_nodes", []):
        if node.get("coverage_status") not in ALLOWED_COVERAGE_STATUSES:
            failures.append(f"bad_coverage_status::{node.get('toc_node_id')}")
        for key in ["target_obligation", "extraction_rule", "integration_rule", "verification_rule"]:
            if not node.get(key):
                failures.append(f"toc_node_missing_{key}::{node.get('toc_node_id')}")
    if payload.get("artifact_hash") != sha256_text(stable_json(payload_without_hash(payload))):
        failures.append("toc_hash_mismatch")
    return failures


def build_audit_payload(toc: dict[str, Any]) -> dict[str, Any]:
    failures = validate_toc_payload(toc)
    status_counts = {}
    for node in toc["toc_nodes"]:
        status_counts[node["coverage_status"]] = status_counts.get(node["coverage_status"], 0) + 1
    payload: dict[str, Any] = {
        "artifact_kind": "OC_CORE_1_3_3_RELEASE_TABLE_OF_CONTENT_AUDIT",
        "body_prose_included": False,
        "status": "PASS" if not failures else "FAIL",
        "failure_total": len(failures),
        "failures": failures,
        "toc_hash": toc["artifact_hash"],
        "toc_node_total": toc["toc_node_total"],
        "coverage_status_counts": status_counts,
    }
    payload["artifact_hash"] = sha256_text(stable_json(payload_without_hash(payload)))
    return payload


def render_toc_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# OC Core 1.3.3 Release Table of Content",
        "",
        f"Status: {payload['status']}",
        f"Artifact hash: `{payload['artifact_hash']}`",
        f"Target structure hash: `{payload['source_target_structure']['artifact_hash']}`",
        f"Science-to-L10 mapping hash: `{payload['source_science_to_l10_mapping']['artifact_hash']}`",
        f"Node total: {payload['toc_node_total']}",
        "",
        "This is an assembly guide derived from the general target structure and science-to-L10 mapping. It is not manuscript prose.",
        "",
        "## Table of Content With Assembly Rules",
        "",
    ]
    for node in payload["toc_nodes"]:
        indent = "  " * (int(node["level"]) - 1)
        family_ids = ", ".join(family["id"] for family in node["source_families"]) or "descendant mapping pending"
        lines.append(
            f"{indent}- {node['outline_number']} {node['title']} "
            f"[coverage={node['coverage_status']}; sources={family_ids}]"
        )
    return "\n".join(lines) + "\n"


def render_audit_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# OC Core 1.3.3 Release Table of Content Audit",
        "",
        f"Status: {payload['status']}",
        f"Artifact hash: `{payload['artifact_hash']}`",
        f"TOC hash: `{payload['toc_hash']}`",
        f"Node total: {payload['toc_node_total']}",
        f"Failures: {payload['failure_total']}",
        "",
        "## Coverage Status Counts",
        "",
    ]
    for status, total in sorted(payload["coverage_status_counts"].items()):
        lines.append(f"- {status}: {total}")
    if payload["failures"]:
        lines.extend(["", "## Failures", ""])
        for failure in payload["failures"]:
            lines.append(f"- {failure}")
    return "\n".join(lines) + "\n"


def expected_files() -> dict[Path, str]:
    toc = build_toc_payload()
    failures = validate_toc_payload(toc)
    if failures:
        raise RuntimeError(f"Release TOC validation failed: {failures}")
    audit = build_audit_payload(toc)
    if audit["status"] != "PASS":
        raise RuntimeError(f"Release TOC audit failed: {audit['failures']}")
    paths = toc_paths()
    return {
        paths["toc_json"]: stable_json(toc),
        paths["toc_md"]: render_toc_markdown(toc),
        paths["audit_json"]: stable_json(audit),
        paths["audit_md"]: render_audit_markdown(audit),
    }


def check_files(files: dict[Path, str]) -> dict[str, Any]:
    missing = []
    changed = []
    for path, text in files.items():
        if not path.exists():
            missing.append(relative(path))
        elif path.read_text(encoding="utf-8", errors="replace") != text:
            changed.append(relative(path))
    return {"state": "PASS" if not missing and not changed else "FAIL", "missing": missing, "changed": changed}


def write_files(files: dict[Path, str]) -> list[str]:
    changed = []
    for path, text in files.items():
        if write_text_if_changed(path, text):
            changed.append(relative(path))
    return changed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Derive OC Core 1.3.3 release table of content.")
    parser.add_argument("--write", action="store_true", help="Write release TOC artifacts if changed.")
    parser.add_argument("--check", action="store_true", help="Check release TOC artifacts without writing.")
    args = parser.parse_args(argv)
    if not args.write and not args.check:
        args.check = True
    files = expected_files()
    result = {"changed": write_files(files), "missing": [], "state": "PASS"} if args.write else check_files(files)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["state"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
