from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from oc_core_release_assembly_lib import ASSEMBLY_ROOT, artifact_hash, stable_json, validation_result


PACKAGE_DIR = ASSEMBLY_ROOT / "package_structure"
PACKAGE_STATUS = "OC_CORE_RELEASE_PACKAGE_CASCADE_READY"


ARTIFACT_TYPES = [
    ("release_guide", "Release guide", "Orient the reader and declare reading order, scope, boundaries, and package navigation."),
    ("master_monograph", "Master monograph", "Carry the complete scientific argument in one coherent monograph structure."),
    ("journal_core_article", "Journal core article", "Provide an article-scale scientific entry point for external review."),
    ("methods_repro_companion", "Methods and reproducibility companion", "Expose methods, replay, data, software, and traceability obligations."),
    ("reviewer_attack_response_map", "Reviewer attack and response map", "Collect adversarial objections, claim boundaries, closure evidence, and remaining caveats."),
    ("public_evidence_bundle", "Public evidence bundle", "Package source evidence, proof/data ledgers, replay material, and review summaries."),
    ("integrity_manifest", "Checksums and manifest", "Bind files, hashes, roles, and provenance without becoming the reader-facing argument."),
    ("citation_metadata", "Citation and metadata", "Provide citation, authorship, license, identifiers, and machine-readable metadata."),
    ("release_notes_changelog", "Release notes and changelog", "State what changed, why it matters, and how to use the release safely."),
]


def package_paths() -> dict[str, Path]:
    return {
        "cascade_json": PACKAGE_DIR / "OC_CORE_RELEASE_PACKAGE_CASCADE.json",
        "cascade_md": PACKAGE_DIR / "OC_CORE_RELEASE_PACKAGE_CASCADE.md",
        "audit_json": PACKAGE_DIR / "OC_CORE_RELEASE_PACKAGE_CASCADE_AUDIT.json",
        "audit_md": PACKAGE_DIR / "OC_CORE_RELEASE_PACKAGE_CASCADE_AUDIT.md",
    }


def artifact_cascade(artifact_id: str, label: str, purpose: str) -> list[dict[str, Any]]:
    return [
        {"level": 1, "node": "purpose_audience_reader_contract", "requirement": purpose},
        {"level": 2, "node": "required_sections", "requirement": "Declare mandatory sections before writing or packaging."},
        {"level": 3, "node": "source_mapping_dependencies", "requirement": "Bind each section to aggregator, release instance, mapping, and evidence sources."},
        {"level": 4, "node": "transformation_rules", "requirement": "Transform sources into readable scientific text or package inventory using text-fill rules."},
        {"level": 5, "node": "validation_gates", "requirement": "Block missing purpose, missing trace, weak claim boundary, broken links, bad encoding, or stale version."},
        {"level": 6, "node": "public_surface_constraints", "requirement": "Keep public-facing material readable and free of control-plane or raw-ledger presentation."},
    ]


def build_package_payload() -> dict[str, Any]:
    artifacts = []
    for index, (artifact_id, label, purpose) in enumerate(ARTIFACT_TYPES, start=1):
        artifacts.append(
            {
                "order": index,
                "artifact_type_id": artifact_id,
                "label": label,
                "purpose": purpose,
                "standard_package_member": True,
                "why_included": "Required to make an OC Core release scientifically readable, reproducible, citable, and reviewable.",
                "known_error_classes_prevented": [
                    "route_sheet_as_primary_artifact",
                    "metadata_first_public_package",
                    "raw_ledger_as_reader_facing_text",
                    "missing_traceability_or_claim_boundary",
                    "stale_version_or_role_mismatch",
                ],
                "mini_cascade": artifact_cascade(artifact_id, label, purpose),
            }
        )
    payload: dict[str, Any] = {
        "schema_id": "OC_CORE_RELEASE_PACKAGE_CASCADE_v1",
        "artifact_kind": "OC_CORE_RELEASE_PACKAGE_CASCADE",
        "body_prose_included": False,
        "status": PACKAGE_STATUS,
        "l0_policy": "L0 is the standard package artifact set; each member has a separate mini-cascade.",
        "artifact_type_total": len(artifacts),
        "artifact_types": artifacts,
        "assembly_policy": {
            "concrete_version_assigned_downstream": True,
            "package_manifest_is_not_reader_facing_argument": True,
            "artifact_role_must_match_content": True,
        },
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def validate_package_payload(payload: dict[str, Any]) -> list[str]:
    failures = []
    if payload.get("status") != PACKAGE_STATUS:
        failures.append("bad_status")
    artifacts = payload.get("artifact_types", [])
    if payload.get("artifact_type_total") != len(artifacts) or len(artifacts) != len(ARTIFACT_TYPES):
        failures.append("artifact_type_total_mismatch")
    for artifact in artifacts:
        if len(artifact.get("mini_cascade", [])) < 3:
            failures.append(f"mini_cascade_too_shallow::{artifact.get('artifact_type_id')}")
        for key in ["purpose", "why_included", "known_error_classes_prevented"]:
            if not artifact.get(key):
                failures.append(f"artifact_missing_{key}::{artifact.get('artifact_type_id')}")
    if payload.get("artifact_hash") != artifact_hash(payload):
        failures.append("artifact_hash_mismatch")
    return failures


def build_audit_payload(cascade: dict[str, Any]) -> dict[str, Any]:
    failures = validate_package_payload(cascade)
    payload: dict[str, Any] = {
        "schema_id": "OC_CORE_RELEASE_PACKAGE_CASCADE_AUDIT_v1",
        "artifact_kind": "OC_CORE_RELEASE_PACKAGE_CASCADE_AUDIT",
        "status": "PASS" if not failures else "FAIL",
        "failure_total": len(failures),
        "failures": failures,
        "cascade_hash": cascade["artifact_hash"],
        "artifact_type_total": cascade["artifact_type_total"],
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def render_cascade_md(payload: dict[str, Any]) -> str:
    lines = [
        "# OC Core Release Package Cascade",
        "",
        f"Status: `{payload['status']}`",
        f"Artifact hash: `{payload['artifact_hash']}`",
        "",
        "## L0 Standard Artifact Set",
        "",
    ]
    for artifact in payload["artifact_types"]:
        lines.append(f"### {artifact['order']}. {artifact['label']} `{artifact['artifact_type_id']}`")
        lines.append("")
        lines.append(f"Purpose: {artifact['purpose']}")
        lines.append("")
        lines.append(f"Why included: {artifact['why_included']}")
        lines.append("")
        lines.append("Mini-cascade:")
        for node in artifact["mini_cascade"]:
            lines.append(f"- L{node['level']} `{node['node']}`: {node['requirement']}")
        lines.append("")
    return "\n".join(lines)


def render_audit_md(payload: dict[str, Any]) -> str:
    lines = [
        "# OC Core Release Package Cascade Audit",
        "",
        f"Status: `{payload['status']}`",
        f"Failures: `{payload['failure_total']}`",
        f"Cascade hash: `{payload['cascade_hash']}`",
        "",
    ]
    for failure in payload["failures"]:
        lines.append(f"- {failure}")
    return "\n".join(lines)


def expected_files() -> dict[Path, str]:
    cascade = build_package_payload()
    failures = validate_package_payload(cascade)
    if failures:
        raise RuntimeError(f"Package cascade validation failed: {failures}")
    audit = build_audit_payload(cascade)
    paths = package_paths()
    return {
        paths["cascade_json"]: stable_json(cascade),
        paths["cascade_md"]: render_cascade_md(cascade),
        paths["audit_json"]: stable_json(audit),
        paths["audit_md"]: render_audit_md(audit),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the generic OC Core release package artifact cascade.")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if not args.write and not args.check:
        args.check = True
    result = validation_result(expected_files(), write=args.write)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["state"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
