from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from build_oc_core_current_release_aggregator import aggregator_paths
from build_oc_core_release_package_cascade import package_paths
from build_oc_core_text_fill_rules import rules_paths
from oc_core_release_assembly_lib import ROOT, artifact_hash, read_json, relative, stable_json, validation_result

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from release_machine.versioning import current_release, release_id_from_version, version_from_release_id


INSTANCE_STATUS = "VERSIONED_RELEASE_INSTANCE_READY_FOR_REVIEW_ASSEMBLY"
REVIEW_PACKAGE_STATUS = "REVIEW_PACKAGE_ASSEMBLED_NO_PUBLICATION_ACTION"


def instance_dir(release_id: str) -> Path:
    return ROOT / "releases" / release_id / "editorial" / "release_assembly"


def instance_paths(release_id: str, version: str) -> dict[str, Path]:
    safe_version = version
    directory = instance_dir(release_id)
    return {
        "instance_json": directory / f"OC_CORE_RELEASE_INSTANCE_{safe_version}.json",
        "instance_md": directory / f"OC_CORE_RELEASE_INSTANCE_{safe_version}.md",
        "review_package_json": directory / f"OC_CORE_RELEASE_REVIEW_PACKAGE_{safe_version}.json",
        "review_package_md": directory / f"OC_CORE_RELEASE_REVIEW_PACKAGE_{safe_version}.md",
        "audit_json": directory / f"OC_CORE_RELEASE_INSTANCE_{safe_version}_AUDIT.json",
        "audit_md": directory / f"OC_CORE_RELEASE_INSTANCE_{safe_version}_AUDIT.md",
    }


def sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def resolve_identity(release_arg: str | None) -> tuple[str, str, str]:
    if release_arg:
        release_id = release_arg.strip()
        version = version_from_release_id(release_id)
        return release_id, version, "explicit_release_argument"
    identity = current_release(ROOT)
    return identity.release_id, identity.version, identity.source


def read_profile(release_id: str) -> dict[str, Any]:
    path = ROOT / "releases" / release_id / "editorial" / "PUBLIC_RELEASE_PROFILE.json"
    if path.exists():
        profile = read_json(path)
        profile["_profile_path"] = relative(path)
        return profile
    version = version_from_release_id(release_id)
    return {
        "_profile_path": None,
        "release_id": release_id,
        "version": version,
        "title": "Ontology of Continua Core",
        "subtitle": "Release profile was not materialized; this fallback is for assembly validation only.",
        "assets": [],
    }


def artifact_type_candidates(artifact_type_id: str, profile_assets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    label_needles = {
        "release_guide": ["release guide"],
        "master_monograph": ["master monograph"],
        "journal_core_article": ["journal core"],
        "methods_repro_companion": ["methods", "reproducibility"],
        "reviewer_attack_response_map": ["reviewer", "attack", "response"],
        "public_evidence_bundle": ["evidence", "reproducibility package"],
        "integrity_manifest": ["manifest", "checksums"],
        "citation_metadata": ["citation", "metadata", "codemeta", "ro-crate"],
        "release_notes_changelog": ["release notes", "changelog"],
    }[artifact_type_id]
    candidates: list[dict[str, Any]] = []
    for asset in profile_assets:
        haystack = " ".join(str(asset.get(key, "")) for key in ["path", "label", "description"]).lower()
        if any(needle in haystack for needle in label_needles):
            path = ROOT / str(asset.get("path", ""))
            candidates.append(
                {
                    "path": asset.get("path"),
                    "label": asset.get("label"),
                    "description": asset.get("description"),
                    "exists_now": path.is_file(),
                    "sha256_now": sha256_file(path),
                    "size_bytes_now": path.stat().st_size if path.is_file() else 0,
                }
            )
    return candidates


def build_instance_payload(release_arg: str | None = None) -> dict[str, Any]:
    release_id, version, identity_source = resolve_identity(release_arg)
    aggregator = read_json(aggregator_paths()["aggregator_json"])
    package = read_json(package_paths()["cascade_json"])
    rules = read_json(rules_paths()["rules_json"])
    profile = read_profile(release_id)
    nodes = aggregator.get("nodes", [])
    not_assessed = sum(1 for node in nodes if node.get("coverage_status") == "not_assessed")
    payload: dict[str, Any] = {
        "schema_id": "OC_CORE_VERSIONED_RELEASE_INSTANCE_v1",
        "artifact_kind": "OC_CORE_VERSIONED_RELEASE_INSTANCE",
        "body_prose_included": False,
        "status": INSTANCE_STATUS,
        "release_identity": {
            "release_id": release_id,
            "version": version,
            "identity_source": identity_source,
            "version_assigned_at_instance_layer": True,
        },
        "profile": {
            "profile_path": profile.get("_profile_path"),
            "title": profile.get("title"),
            "subtitle": profile.get("subtitle"),
            "asset_total": len(profile.get("assets", [])),
        },
        "source_hashes": {
            "current_release_aggregator_hash": aggregator["artifact_hash"],
            "package_cascade_hash": package["artifact_hash"],
            "text_fill_rules_hash": rules["artifact_hash"],
            **aggregator["source_hashes"],
        },
        "assembly_counts": {
            "aggregator_node_total": aggregator["node_total"],
            "l10_terminal_total": sum(1 for node in nodes if node.get("terminal_l10")),
            "artifact_type_total": package["artifact_type_total"],
            "coverage_not_assessed_total": not_assessed,
        },
        "promotion_policy": {
            "not_assessed_fill_blocks_final_publication_claims": True,
            "versioned_instance_may_be_review_ready_with_unassessed_fill": True,
            "concrete_artifacts_must_consume_instance_not_raw_l10": True,
        },
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def build_review_package_payload(instance: dict[str, Any]) -> dict[str, Any]:
    release_id = instance["release_identity"]["release_id"]
    profile = read_profile(release_id)
    package = read_json(package_paths()["cascade_json"])
    aggregator = read_json(aggregator_paths()["aggregator_json"])
    rows = []
    for artifact in package["artifact_types"]:
        candidates = artifact_type_candidates(artifact["artifact_type_id"], profile.get("assets", []))
        rows.append(
            {
                "artifact_type_id": artifact["artifact_type_id"],
                "label": artifact["label"],
                "purpose": artifact["purpose"],
                "mini_cascade_depth": len(artifact["mini_cascade"]),
                "candidate_asset_total": len(candidates),
                "existing_candidate_asset_total": sum(1 for candidate in candidates if candidate["exists_now"]),
                "candidate_assets": candidates,
                "assembly_rule": "Generate or validate this artifact from the release instance, package cascade, text fill rules, and mapped source obligations.",
                "verification_rule": "Block if role/content mismatch, missing trace, stale version, broken link, bad encoding, control-language leak, or unsupported claim appears.",
            }
        )
    payload: dict[str, Any] = {
        "schema_id": "OC_CORE_RELEASE_REVIEW_PACKAGE_v1",
        "artifact_kind": "OC_CORE_RELEASE_REVIEW_PACKAGE",
        "body_prose_included": False,
        "status": REVIEW_PACKAGE_STATUS,
        "release_identity": instance["release_identity"],
        "source_hashes": {
            "release_instance_hash": instance["artifact_hash"],
            "current_release_aggregator_hash": aggregator["artifact_hash"],
            "package_cascade_hash": package["artifact_hash"],
            "text_fill_rules_hash": read_json(rules_paths()["rules_json"])["artifact_hash"],
        },
        "review_scope": "review-space artifact assembly only; no public record update, tag movement, or publication action",
        "artifact_rows": rows,
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def validate_instance_payload(payload: dict[str, Any]) -> list[str]:
    failures = []
    if payload.get("status") != INSTANCE_STATUS:
        failures.append("bad_instance_status")
    identity = payload.get("release_identity", {})
    if release_id_from_version(identity.get("version", "")) != identity.get("release_id"):
        failures.append("release_id_version_mismatch")
    if not identity.get("version_assigned_at_instance_layer"):
        failures.append("version_not_assigned_at_instance_layer")
    if payload.get("source_hashes", {}).get("current_release_aggregator_hash") != read_json(aggregator_paths()["aggregator_json"]).get("artifact_hash"):
        failures.append("aggregator_hash_mismatch")
    if payload.get("artifact_hash") != artifact_hash(payload):
        failures.append("instance_hash_mismatch")
    return failures


def validate_review_package_payload(payload: dict[str, Any], instance: dict[str, Any]) -> list[str]:
    failures = []
    if payload.get("status") != REVIEW_PACKAGE_STATUS:
        failures.append("bad_review_package_status")
    if payload.get("source_hashes", {}).get("release_instance_hash") != instance.get("artifact_hash"):
        failures.append("review_package_instance_hash_mismatch")
    for row in payload.get("artifact_rows", []):
        if row.get("mini_cascade_depth", 0) < 3:
            failures.append(f"artifact_cascade_too_shallow::{row.get('artifact_type_id')}")
        if row.get("candidate_asset_total", 0) == 0:
            failures.append(f"artifact_has_no_profile_candidate::{row.get('artifact_type_id')}")
    if payload.get("artifact_hash") != artifact_hash(payload):
        failures.append("review_package_hash_mismatch")
    return failures


def build_audit_payload(instance: dict[str, Any], review_package: dict[str, Any]) -> dict[str, Any]:
    failures = validate_instance_payload(instance) + validate_review_package_payload(review_package, instance)
    payload: dict[str, Any] = {
        "schema_id": "OC_CORE_RELEASE_INSTANCE_AUDIT_v1",
        "artifact_kind": "OC_CORE_RELEASE_INSTANCE_AUDIT",
        "status": "PASS" if not failures else "FAIL",
        "failure_total": len(failures),
        "failures": failures,
        "release_identity": instance["release_identity"],
        "release_instance_hash": instance["artifact_hash"],
        "review_package_hash": review_package["artifact_hash"],
        "assembly_counts": instance["assembly_counts"],
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def render_instance_md(payload: dict[str, Any]) -> str:
    identity = payload["release_identity"]
    lines = [
        f"# OC Core Release Instance {identity['version']}",
        "",
        f"Status: `{payload['status']}`",
        f"Release id: `{identity['release_id']}`",
        f"Version: `{identity['version']}`",
        f"Artifact hash: `{payload['artifact_hash']}`",
        "",
        "## Source Hashes",
        "",
    ]
    for key, value in payload["source_hashes"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Assembly Counts", ""])
    for key, value in payload["assembly_counts"].items():
        lines.append(f"- {key}: {value}")
    return "\n".join(lines) + "\n"


def render_review_package_md(payload: dict[str, Any]) -> str:
    identity = payload["release_identity"]
    lines = [
        f"# OC Core Release Review Package {identity['version']}",
        "",
        f"Status: `{payload['status']}`",
        f"Artifact hash: `{payload['artifact_hash']}`",
        f"Scope: {payload['review_scope']}",
        "",
        "## Artifact Rows",
        "",
    ]
    for row in payload["artifact_rows"]:
        lines.append(
            f"- `{row['artifact_type_id']}` {row['label']}: candidates={row['candidate_asset_total']}; "
            f"existing={row['existing_candidate_asset_total']}; depth={row['mini_cascade_depth']}"
        )
    return "\n".join(lines) + "\n"


def render_audit_md(payload: dict[str, Any]) -> str:
    lines = [
        "# OC Core Release Instance Audit",
        "",
        f"Status: `{payload['status']}`",
        f"Failures: `{payload['failure_total']}`",
        f"Release instance hash: `{payload['release_instance_hash']}`",
        f"Review package hash: `{payload['review_package_hash']}`",
        "",
    ]
    for failure in payload["failures"]:
        lines.append(f"- {failure}")
    return "\n".join(lines)


def expected_files(release_arg: str | None = None) -> dict[Path, str]:
    instance = build_instance_payload(release_arg)
    review_package = build_review_package_payload(instance)
    audit = build_audit_payload(instance, review_package)
    if audit["status"] != "PASS":
        raise RuntimeError(f"Release instance audit failed: {audit['failures']}")
    release_id = instance["release_identity"]["release_id"]
    version = instance["release_identity"]["version"]
    paths = instance_paths(release_id, version)
    return {
        paths["instance_json"]: stable_json(instance),
        paths["instance_md"]: render_instance_md(instance),
        paths["review_package_json"]: stable_json(review_package),
        paths["review_package_md"]: render_review_package_md(review_package),
        paths["audit_json"]: stable_json(audit),
        paths["audit_md"]: render_audit_md(audit),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a versioned OC Core release instance from generic assembly inputs.")
    parser.add_argument("--release", default=None, help="Release id such as oc_core_1_3_3. Defaults to release_machine.versioning.current_release().")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if not args.write and not args.check:
        args.check = True
    result = validation_result(expected_files(args.release), write=args.write)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["state"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
