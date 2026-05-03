from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from derive_general_oc_core_monograph_target_structure import target_paths
from build_oc133_science_to_l10_mapping import mapping_paths
from build_oc133_science_mapping_quality_and_coverage import quality_paths
from oc_core_release_assembly_lib import (
    ASSEMBLY_ROOT,
    artifact_hash,
    assert_no_common_layer_forbidden,
    check_files,
    compact_json,
    payload_without_hash,
    read_json,
    relative,
    sha256_text,
    stable_json,
    validation_result,
)


AGGREGATOR_DIR = ASSEMBLY_ROOT / "current_release_aggregator"
AGGREGATOR_STATUS = "CURRENT_RELEASE_AGGREGATOR_READY_STRUCTURE_ONLY"


def common_text(value: Any) -> Any:
    if isinstance(value, str):
        return value.replace("OC Core 1.3.3", "OC Core").replace("1.3.3", "target release")
    if isinstance(value, list):
        return [common_text(item) for item in value]
    if isinstance(value, dict):
        return {key: common_text(item) for key, item in value.items()}
    return value


def aggregator_paths() -> dict[str, Path]:
    return {
        "aggregator_json": AGGREGATOR_DIR / "OC_CORE_CURRENT_RELEASE_AGGREGATOR.json",
        "aggregator_md": AGGREGATOR_DIR / "OC_CORE_CURRENT_RELEASE_AGGREGATOR.md",
        "audit_json": AGGREGATOR_DIR / "OC_CORE_CURRENT_RELEASE_AGGREGATOR_AUDIT.json",
        "audit_md": AGGREGATOR_DIR / "OC_CORE_CURRENT_RELEASE_AGGREGATOR_AUDIT.md",
    }


def _quality_by_outline(quality: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for row in quality.get("l10_quality_rows", []):
        rows[str(row["outline_number"])] = row
    for row in quality.get("aggregate_quality_rows", []):
        rows.setdefault(str(row["outline_number"]), row)
    return rows


def _mapping_by_outline(mapping: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(row["outline_number"]): row for row in mapping.get("mapping_rows", [])}


def build_aggregator_payload() -> dict[str, Any]:
    target_json, _ = target_paths()
    mapping_json = mapping_paths()["mapping_json"]
    quality_json = quality_paths()["quality_json"]
    quality_audit_json = quality_paths()["audit_json"]
    target = read_json(target_json)
    mapping = read_json(mapping_json)
    quality = read_json(quality_json)
    quality_audit = read_json(quality_audit_json)
    quality_by_outline = _quality_by_outline(quality)
    mapping_by_outline = _mapping_by_outline(mapping)

    coverage_counter: Counter[str] = Counter()
    nodes: list[dict[str, Any]] = []
    for target_node in target.get("target_nodes", []):
        outline = str(target_node["outline_number"])
        quality_row = quality_by_outline.get(outline, {})
        mapping_row = mapping_by_outline.get(outline)
        coverage_status = str(quality_row.get("coverage_status") or (mapping_row or {}).get("coverage_status") or "not_assessed")
        coverage_counter[coverage_status] += 1
        terminal = target_node["level"] == 10
        nodes.append(
            {
                "aggregator_node_id": "OC-CURRENT-AGG-" + target_node["target_node_id"].replace("OC-GEN-MONO-", ""),
                "target_node_id": target_node["target_node_id"],
                "level": target_node["level"],
                "order_path": target_node["order_path"],
                "order_label": "/".join(str(part) for part in target_node["order_path"]),
                "title": target_node["title"],
                "terminal_l10": terminal,
                "coverage_status": coverage_status,
                "auto_quality_index": quality_row.get("auto_quality_index") or quality_row.get("auto_quality_index_mean"),
                "argument_role": (mapping_row or {}).get("argument_role"),
                "source_family_ids": [family["id"] for family in (mapping_row or {}).get("source_families", [])],
                "reader_task": common_text((mapping_row or {}).get("reader_task")),
                "claim_boundary": common_text((mapping_row or {}).get("claim_boundary")),
                "extraction_rule": common_text((mapping_row or {}).get("extraction_rule"))
                or "Aggregate descendant source obligations without changing the frozen target structure.",
                "integration_rule": common_text((mapping_row or {}).get("integration_rule"))
                or "Integrate descendant terminal obligations only through the versioned release instance.",
                "verification_rule": common_text((mapping_row or {}).get("verification_rule"))
                or "Verify all descendant terminal obligations before promoting this branch.",
            }
        )

    payload: dict[str, Any] = {
        "schema_id": "OC_CORE_CURRENT_RELEASE_AGGREGATOR_v1",
        "artifact_kind": "OC_CORE_CURRENT_RELEASE_AGGREGATOR",
        "body_prose_included": False,
        "status": AGGREGATOR_STATUS,
        "canonical_scope": "common current-release assembly input, not a concrete release table of contents",
        "source_hashes": {
            "general_target_structure_hash": target["artifact_hash"],
            "science_to_l10_mapping_hash": mapping["artifact_hash"],
            "mapping_quality_hash": quality["artifact_hash"],
            "mapping_quality_audit_hash": quality_audit["artifact_hash"],
        },
        "coverage_status_counts": dict(sorted(coverage_counter.items())),
        "quality_summary": {
            "status": quality_audit.get("status"),
            "l10_quality_row_total": quality_audit.get("l10_quality_row_total"),
            "auto_quality_index_mean": quality_audit.get("auto_quality_index_mean"),
            "auto_quality_index_min": quality_audit.get("auto_quality_index_min"),
            "auto_quality_index_max": quality_audit.get("auto_quality_index_max"),
            "flag_counts": quality_audit.get("flag_counts", {}),
        },
        "node_total": len(nodes),
        "nodes": nodes,
        "assembly_contract": {
            "concrete_release_number_assigned_only_by_release_instance_builder": True,
            "package_artifact_materialization_is_downstream": True,
            "prose_generation_is_downstream": True,
            "public_record_metadata_is_downstream": True,
        },
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def validate_aggregator(payload: dict[str, Any]) -> list[str]:
    failures = []
    if payload.get("status") != AGGREGATOR_STATUS:
        failures.append("bad_status")
    if payload.get("body_prose_included") is not False:
        failures.append("body_prose_flag_mismatch")
    if payload.get("node_total") != len(payload.get("nodes", [])):
        failures.append("node_total_mismatch")
    failures.extend(assert_no_common_layer_forbidden(payload))
    if payload.get("artifact_hash") != sha256_text(compact_json(payload_without_hash(payload))):
        failures.append("artifact_hash_mismatch")
    return failures


def build_audit_payload(aggregator: dict[str, Any]) -> dict[str, Any]:
    failures = validate_aggregator(aggregator)
    payload: dict[str, Any] = {
        "schema_id": "OC_CORE_CURRENT_RELEASE_AGGREGATOR_AUDIT_v1",
        "artifact_kind": "OC_CORE_CURRENT_RELEASE_AGGREGATOR_AUDIT",
        "status": "PASS" if not failures else "FAIL",
        "failure_total": len(failures),
        "failures": failures,
        "aggregator_hash": aggregator["artifact_hash"],
        "node_total": aggregator["node_total"],
        "coverage_status_counts": aggregator["coverage_status_counts"],
        "quality_summary": aggregator["quality_summary"],
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def render_aggregator_md(payload: dict[str, Any]) -> str:
    lines = [
        "# OC Core Current Release Aggregator",
        "",
        f"Status: `{payload['status']}`",
        f"Artifact hash: `{payload['artifact_hash']}`",
        f"Node total: `{payload['node_total']}`",
        "",
        "This is a common current-release assembly input. It is not a concrete release table of contents.",
        "",
        "## Source Hashes",
        "",
    ]
    for key, value in payload["source_hashes"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Coverage Status Counts", ""])
    for key, value in payload["coverage_status_counts"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Node Map", ""])
    for node in payload["nodes"]:
        indent = "  " * (int(node["level"]) - 1)
        quality = node["auto_quality_index"]
        quality_text = "n/a" if quality is None else str(quality)
        lines.append(f"{indent}- {node['order_label']} {node['title']} :: {node['coverage_status']} :: quality={quality_text}")
    return "\n".join(lines) + "\n"


def render_audit_md(payload: dict[str, Any]) -> str:
    lines = [
        "# OC Core Current Release Aggregator Audit",
        "",
        f"Status: `{payload['status']}`",
        f"Artifact hash: `{payload['artifact_hash']}`",
        f"Aggregator hash: `{payload['aggregator_hash']}`",
        f"Failures: `{payload['failure_total']}`",
        "",
    ]
    if payload["failures"]:
        lines.extend(["## Failures", ""])
        lines.extend(f"- {failure}" for failure in payload["failures"])
    return "\n".join(lines) + "\n"


def expected_files() -> dict[Path, str]:
    aggregator = build_aggregator_payload()
    failures = validate_aggregator(aggregator)
    if failures:
        raise RuntimeError(f"Aggregator validation failed: {failures}")
    audit = build_audit_payload(aggregator)
    if audit["status"] != "PASS":
        raise RuntimeError(f"Aggregator audit failed: {audit['failures']}")
    paths = aggregator_paths()
    return {
        paths["aggregator_json"]: stable_json(aggregator),
        paths["aggregator_md"]: render_aggregator_md(aggregator),
        paths["audit_json"]: stable_json(audit),
        paths["audit_md"]: render_audit_md(audit),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the generic OC Core current release aggregator.")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if not args.write and not args.check:
        args.check = True
    files = expected_files()
    result = validation_result(files, write=args.write)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["state"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
