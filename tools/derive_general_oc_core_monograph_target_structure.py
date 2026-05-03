from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from freeze_oc_core_manuscript_structure_cascade_v1_0 import FREEZE_STATUS, freeze_paths
from oc133_manuscript_structure_transfer_lib import (
    EDITORIAL,
    sha256_text,
    stable_json,
    write_text_if_changed,
)


ROOT = Path(__file__).resolve().parents[1]
TARGET_DIR = EDITORIAL / "general_oc_core_monograph_target_structure"
TARGET_STATUS = "APPROVED_FROZEN_GENERAL_OC_CORE_MONOGRAPH_TARGET_STRUCTURE_V1_0"
TARGET_VERSION = "1.0"


def target_paths() -> tuple[Path, Path]:
    stem = "GENERAL_OC_CORE_MONOGRAPH_TARGET_STRUCTURE_V1_0"
    return TARGET_DIR / f"{stem}.json", TARGET_DIR / f"{stem}.md"


def target_freeze_paths() -> tuple[Path, Path]:
    stem = "GENERAL_OC_CORE_MONOGRAPH_TARGET_STRUCTURE_FREEZE_V1_0"
    return TARGET_DIR / f"{stem}.json", TARGET_DIR / f"{stem}.md"


def relative(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def payload_without_hash(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if key != "artifact_hash"}


def generalize_text(text: str) -> str:
    replacements = [
        (r"\bOC Core 1\.3\.3\b", "OC Core"),
        (r"\bOC 1\.3\.3\b", "OC Core"),
        (r"\b1\.3\.3\b", "target release"),
    ]
    result = text
    for pattern, replacement in replacements:
        result = re.sub(pattern, replacement, result)
    return result


def generalize_value(value: Any) -> Any:
    if isinstance(value, str):
        return generalize_text(value)
    if isinstance(value, list):
        return [generalize_value(item) for item in value]
    if isinstance(value, dict):
        return {key: generalize_value(item) for key, item in value.items()}
    return value


def build_target_payload() -> dict[str, Any]:
    freeze_json, _ = freeze_paths()
    freeze = read_json(freeze_json)
    if freeze.get("status") != FREEZE_STATUS:
        raise RuntimeError(f"Cascade freeze not approved: {freeze.get('status')}")

    target_nodes = []
    for node in freeze["frozen_node_manifest"]:
        target_nodes.append(
            {
                "target_node_id": "OC-GEN-MONO-" + node["node_id"].replace("OC133-MS-", ""),
                "source_cascade_node_id": node["node_id"],
                "level": node["level"],
                "order_path": node["order_path"],
                "outline_number": node["outline_number"],
                "parent_source_node_id": node["parent_id"],
                "title": generalize_text(node["title"]),
                "source_title": node["title"],
                "structure_status": "FROZEN_TARGET_STRUCTURE",
            }
        )

    payload: dict[str, Any] = {
        "artifact_kind": "GENERAL_OC_CORE_MONOGRAPH_TARGET_STRUCTURE",
        "body_prose_included": False,
        "status": TARGET_STATUS,
        "target_structure_version": TARGET_VERSION,
        "source_cascade_freeze": {
            "json": relative(freeze_json),
            "artifact_hash": freeze["artifact_hash"],
            "frozen_node_manifest_hash": freeze["frozen_node_manifest_hash"],
        },
        "mutation_policy": {
            "derived_from_cascade_freeze_only": True,
            "delete_rename_reorder_collapse_forbidden": True,
            "release_specific_wording_removed_where_appropriate": True,
            "prose_generation_not_authorized": True,
        },
        "node_total": len(target_nodes),
        "target_nodes": target_nodes,
    }
    payload["artifact_hash"] = sha256_text(stable_json(payload_without_hash(payload)))
    return payload


def build_target_freeze_payload(target: dict[str, Any]) -> dict[str, Any]:
    target_json, target_md = target_paths()
    payload: dict[str, Any] = {
        "artifact_kind": "GENERAL_OC_CORE_MONOGRAPH_TARGET_STRUCTURE_FREEZE",
        "body_prose_included": False,
        "status": TARGET_STATUS,
        "target_structure_version": TARGET_VERSION,
        "target_structure": {
            "json": relative(target_json),
            "markdown": relative(target_md),
            "artifact_hash": target["artifact_hash"],
            "node_total": target["node_total"],
        },
        "source_cascade_freeze": target["source_cascade_freeze"],
        "mutation_policy": target["mutation_policy"],
    }
    payload["artifact_hash"] = sha256_text(stable_json(payload_without_hash(payload)))
    return payload


def validate_target_payload(payload: dict[str, Any]) -> list[str]:
    failures = []
    if payload.get("status") != TARGET_STATUS:
        failures.append("target_status_mismatch")
    if payload.get("body_prose_included") is not False:
        failures.append("body_prose_flag_mismatch")
    if payload.get("node_total") != len(payload.get("target_nodes", [])):
        failures.append("node_total_mismatch")
    titles = [node["title"] for node in payload.get("target_nodes", [])]
    if any("1.3.3" in title for title in titles):
        failures.append("release_specific_title_not_generalized")
    if payload.get("artifact_hash") != sha256_text(stable_json(payload_without_hash(payload))):
        failures.append("target_hash_mismatch")
    return failures


def validate_target_freeze_payload(payload: dict[str, Any], target: dict[str, Any]) -> list[str]:
    failures = []
    if payload.get("status") != TARGET_STATUS:
        failures.append("target_freeze_status_mismatch")
    if payload.get("target_structure", {}).get("artifact_hash") != target.get("artifact_hash"):
        failures.append("target_freeze_hash_mismatch")
    if payload.get("artifact_hash") != sha256_text(stable_json(payload_without_hash(payload))):
        failures.append("target_freeze_artifact_hash_mismatch")
    return failures


def render_target_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# General OC Core Monograph Target Structure v1.0",
        "",
        f"Status: {payload['status']}",
        f"Artifact hash: `{payload['artifact_hash']}`",
        f"Source cascade freeze: `{payload['source_cascade_freeze']['artifact_hash']}`",
        f"Node total: {payload['node_total']}",
        "",
        "This is a structure-only target standard derived from the frozen cascade. It is not manuscript prose.",
        "",
        "## Target Outline",
        "",
    ]
    for node in payload["target_nodes"]:
        indent = "  " * (int(node["level"]) - 1)
        lines.append(f"{indent}- {node['outline_number']} {node['title']} [{node['target_node_id']}]")
    return "\n".join(lines) + "\n"


def render_target_freeze_markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# General OC Core Monograph Target Structure Freeze v1.0",
            "",
            f"Status: {payload['status']}",
            f"Artifact hash: `{payload['artifact_hash']}`",
            f"Target structure hash: `{payload['target_structure']['artifact_hash']}`",
            f"Source cascade freeze hash: `{payload['source_cascade_freeze']['artifact_hash']}`",
            "",
            "This freeze is derived from the cascade freeze and remains structure-only.",
            "",
        ]
    )


def expected_files() -> dict[Path, str]:
    target = build_target_payload()
    failures = validate_target_payload(target)
    if failures:
        raise RuntimeError(f"Target validation failed: {failures}")
    target_freeze = build_target_freeze_payload(target)
    freeze_failures = validate_target_freeze_payload(target_freeze, target)
    if freeze_failures:
        raise RuntimeError(f"Target freeze validation failed: {freeze_failures}")
    target_json, target_md = target_paths()
    freeze_json, freeze_md = target_freeze_paths()
    return {
        target_json: stable_json(target),
        target_md: render_target_markdown(target),
        freeze_json: stable_json(target_freeze),
        freeze_md: render_target_freeze_markdown(target_freeze),
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
    parser = argparse.ArgumentParser(description="Derive General OC Core Monograph Target Structure from cascade freeze.")
    parser.add_argument("--write", action="store_true", help="Write derived target artifacts if changed.")
    parser.add_argument("--check", action="store_true", help="Check derived target artifacts without writing.")
    args = parser.parse_args(argv)
    if not args.write and not args.check:
        args.check = True
    files = expected_files()
    result = {"changed": write_files(files), "missing": [], "state": "PASS"} if args.write else check_files(files)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["state"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
