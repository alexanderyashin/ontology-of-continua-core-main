from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from .constants import DOI_PENDING, RELEASE_ID, TIMESTAMP, VERSION


RELEASE_CLASSES: dict[str, dict[str, Any]] = {
    "draft_internal": {"minimum_k_R": 0.70, "external_publication_allowed": False},
    "internal": {"minimum_k_R": 0.85, "external_publication_allowed": False},
    "scientific_public": {"minimum_k_R": 0.98, "external_publication_allowed": True},
    "platinum_public": {"minimum_k_R": 1.00, "external_publication_allowed": True},
    "hotfix_internal": {"minimum_k_R": 0.90, "external_publication_allowed": False},
}

LRGEF_GATES = [
    "QG-00_RELEASE_IDENTITY",
    "QG-01_POLICY_AND_CLASS",
    "QG-02_FREEZE_AND_MANIFEST",
    "QG-03_REPRODUCIBLE_BUILD_ROUTE",
    "QG-04_DOCUMENT_SUBSTANCE",
    "QG-05_CLAIM_EVIDENCE_FIREWALL",
    "QG-06_PUBLIC_BOUNDARY_LEAK_SCAN",
    "QG-07_METADATA_AND_DOI_LINEAGE",
    "QG-08_SBOM_AND_PROVENANCE",
    "QG-09_SIGNATURE_OR_NO_SEND_BLOCKER",
    "QG-10_OWNER_APPROVAL_LOCK",
    "QG-11_STALE_SOURCE_DETECTION",
    "QG-12_PUBLICATION_DRY_RUN_ONLY",
    "QG-13_K10_OBSERVER_NO_BYPASS",
    "QG-14_PARFITIAN_CERBERUS_NO_SELF_DEFEAT",
]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not text.endswith("\n"):
        text += "\n"
    path.write_text(text, encoding="utf-8")


def rel(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def sha256_text(value: str) -> str:
    import hashlib

    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def tool_location_class(path: str | None) -> str:
    if not path:
        return "MISSING"
    normalized = path.replace("\\", "/").lower()
    if "/users/" in normalized:
        return "USER_LOCAL_AVAILABLE_REDACTED"
    if "program files" in normalized or "/windows/" in normalized:
        return "SYSTEM_AVAILABLE_REDACTED"
    return "AVAILABLE_REDACTED"


def toolchain_status() -> dict[str, Any]:
    tools = {}
    for tool in ["git", "python", "cosign", "syft", "slsa-verifier", "cyclonedx-py", "pip-audit", "openssl"]:
        path = shutil.which(tool)
        tools[tool] = {
            "available": bool(path),
            "location_class": tool_location_class(path),
            "path_redacted": True,
        }
    missing_external = [name for name in ["cosign", "syft", "slsa-verifier"] if not tools[name]["available"]]
    return {
        "status": "PASS_WITH_NO_SEND_BLOCKERS" if missing_external else "PASS",
        "tools": tools,
        "missing_external_publication_tools": missing_external,
        "external_publication_blocked_until_tools_green": bool(missing_external),
    }


def compute_k_R(results: list[dict[str, Any]], *, owner_approved: bool, external_tools_green: bool) -> float:
    blocking = [
        row
        for row in results
        if row.get("state") in {"FAIL", "BLOCKED"}
        and row.get("severity") in {"CRITICAL", "HIGH"}
    ]
    if blocking:
        return 0.85
    if owner_approved and external_tools_green:
        return 1.0
    return 0.98


def freshness_report(root: Path, source_paths: list[Path], view_paths: list[Path]) -> dict[str, Any]:
    existing_sources = [path for path in source_paths if path.exists()]
    existing_views = [path for path in view_paths if path.exists()]
    newest_source = max((path.stat().st_mtime for path in existing_sources), default=0)
    oldest_view = min((path.stat().st_mtime for path in existing_views), default=0)
    stale = bool(existing_views) and newest_source > oldest_view
    return {
        "status": "STALE" if stale else "FRESH",
        "source_count": len(existing_sources),
        "view_count": len(existing_views),
        "mtime_policy": "raw filesystem mtimes are intentionally not materialized in packaged verdicts",
        "stale_inputs": [rel(root, path) for path in existing_sources if existing_views and path.stat().st_mtime > oldest_view],
    }


def build_sbom(root: Path, entries: list[Any]) -> dict[str, Any]:
    components = []
    for entry in entries:
        source = getattr(entry, "source_path", None)
        if not isinstance(source, Path) or not source.exists():
            continue
        if source.name == "LRGEF_SBOM_CYCLONEDX_latest.json":
            continue
        components.append(
            {
                "type": "file",
                "name": getattr(entry, "bundle_path", rel(root, source)),
                "version": VERSION,
                "purl": "",
                "hashes": [{"alg": "SHA-256", "content": _sha256_file(source)}],
            }
        )
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "serialNumber": f"urn:logion:lrgef:{RELEASE_ID}:{VERSION}",
        "version": 1,
        "metadata": {"timestamp": TIMESTAMP, "component": {"type": "application", "name": RELEASE_ID, "version": VERSION}},
        "components": components,
    }


def _sha256_file(path: Path) -> str:
    import hashlib

    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def emit_lrgef_outputs(
    root: Path,
    *,
    summary: dict[str, Any],
    results: list[dict[str, Any]],
    entries: list[Any],
    package_sha256: str,
    pdf_quality: dict[str, Any],
) -> dict[str, Any]:
    ed = root / "releases" / RELEASE_ID / "editorial"
    toolchain = toolchain_status()
    external_tools_green = not toolchain["missing_external_publication_tools"]
    owner_approved = False
    k_R = compute_k_R(results, owner_approved=owner_approved, external_tools_green=external_tools_green)
    hard_green_external = bool(k_R >= 1.0 and owner_approved and external_tools_green)
    science_terminality_blocked = any(
        row.get("gate_id") == "G28" and row.get("state") in {"FAIL", "BLOCKED"}
        for row in results
    )
    lrgef_state = {
        "schema_id": "LRGEF_RELEASE_STATE_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_at": TIMESTAMP,
        "git_head": None,
        "git_head_policy": "recorded outside the packaged release after checkpoint to avoid self-referential commit drift",
        "release_class": "scientific_public_no_send_rc",
        "k_R": k_R,
        "required_public_threshold": RELEASE_CLASSES["scientific_public"]["minimum_k_R"],
        "release_machine_state": summary.get("release_state"),
        "master_verdict": summary.get("master_verdict"),
        "gate_counts": summary.get("gate_counts", {}),
        "hard_green_external": hard_green_external,
        "publish_allowed": False,
        "doi": DOI_PENDING,
        "owner_approval_required": True,
        "owner_approved": False,
        "external_publication_blockers": [
            *toolchain["missing_external_publication_tools"],
            *(["SCIENCE_TERMINALITY_82_OPEN"] if science_terminality_blocked else []),
            "OWNER_APPROVAL_REQUIRED",
            "ZENODO_DOI_PENDING_UNTIL_PUBLICATION",
        ],
        "toolchain": toolchain,
        "pdf_quality": pdf_quality,
        "package_sha256": None,
        "package_sha256_policy": "recorded externally in OC_CORE_1_3_2_ZIP_INTEGRITY_latest.json to avoid self-referential ZIP drift",
        "lrgef_gate_ids": LRGEF_GATES,
    }
    policy = {
        "schema_id": "LRGEF_RELEASE_POLICY_v1",
        "version": "1.0",
        "release_classes": RELEASE_CLASSES,
        "hard_rules": [
            "NO_SIGNED_PASS_NO_PUBLICATION",
            "NO_MANIFEST_NO_RELEASE",
            "NO_EVIDENCE_NO_SCIENTIFIC_RELEASE",
            "NO_REPRODUCIBILITY_NO_SCIENTIFIC_OR_PLATINUM_RELEASE",
            "NO_HARD_GREEN_NO_EXTERNAL_TRANSITION",
            "NO_SILENT_REPAIR",
            "NO_OVERWRITE_PUBLISHED_ARTIFACTS",
            "NO_MANUAL_BYPASS_WITHOUT_BLACK_INCIDENT",
            "NO_GATE_WEAKENING_WITHOUT_K0_AND_K10_PASS",
            "NO_PARFITIAN_HIGH_PLUS_FINDINGS_FOR_RELEASE_READY_NO_SEND",
            "NO_WAIVER_FOR_PARFITIAN_BLOCKER_OR_NO_SEND_VIOLATION",
        ],
        "qg_gate_ids": LRGEF_GATES,
    }
    provenance = {
        "schema_id": "LRGEF_PROVENANCE_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_at": TIMESTAMP,
        "git_head": None,
        "git_head_policy": lrgef_state["git_head_policy"],
        "builder": "release_machine.complete + release_machine.lrgef",
        "source_date_epoch": "2026-04-26T00:00:00Z",
        "package_sha256": None,
        "package_sha256_policy": "external_zip_integrity_report",
        "slsa_status": "LOCAL_NO_SEND_PROVENANCE",
        "in_toto_status": "LOCAL_NO_SEND_PROVENANCE",
    }
    sbom = build_sbom(root, entries)
    signature_payload = {
        "schema_id": "LRGEF_MANIFEST_SIGNATURE_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_at": TIMESTAMP,
        "signature_status": "TOOLING_BLOCKED_NO_SEND" if not external_tools_green else "LOCAL_HASH_ATTESTATION",
        "cosign_available": toolchain["tools"]["cosign"]["available"],
        "signed_manifest_sha256": sha256_text(json.dumps(lrgef_state, ensure_ascii=False, sort_keys=True)),
        "external_publication_allowed": False,
        "reason": "Owner approval and external signing/archive toolchain are required before public publication.",
    }
    portfolio = build_release_portfolio(root, lrgef_state)
    write_json(ed / "LRGEF_RELEASE_STATE_latest.json", lrgef_state)
    write_json(ed / "LRGEF_RELEASE_POLICY_v1.json", policy)
    write_json(ed / "LRGEF_PROVENANCE_latest.json", provenance)
    write_json(ed / "LRGEF_SBOM_CYCLONEDX_latest.json", sbom)
    write_json(ed / "LRGEF_MANIFEST_SIGNATURE_latest.json", signature_payload)
    write_json(ed / "LRGEF_RELEASE_PORTFOLIO_latest.json", portfolio)
    write_text(
        ed / "LRGEF_RELEASE_STATE_latest.md",
        "\n".join(
            [
                "# LRGEF Release State: OC Core 1.3.2",
                "",
                f"- release_class: `{lrgef_state['release_class']}`",
                f"- k_R: `{lrgef_state['k_R']}`",
                f"- release_machine_state: `{lrgef_state['release_machine_state']}`",
                f"- master_verdict: `{lrgef_state['master_verdict']}`",
                f"- hard_green_external: `{str(hard_green_external).lower()}`",
                f"- publish_allowed: `false`",
                "- package_sha256: `external_zip_integrity_report`",
                "",
                "## External Publication Blockers",
                *[f"- `{item}`" for item in lrgef_state["external_publication_blockers"]],
            ]
        ),
    )
    return lrgef_state


def build_release_portfolio(root: Path, current_state: dict[str, Any]) -> dict[str, Any]:
    releases_root = root / "releases"
    rows = []
    if releases_root.exists():
        for path in sorted(item for item in releases_root.iterdir() if item.is_dir()):
            release_id = path.name
            if release_id == RELEASE_ID:
                classification = "SCIENTIFIC_NO_SEND_RC"
                state = current_state.get("release_machine_state", "UNKNOWN")
            elif release_id == "oc_core_1_3_1":
                classification = "HISTORICAL_CANONICAL_PREVIOUS"
                state = "HISTORICAL"
            elif release_id == "oc_core_1_3":
                classification = "INTEGRATED_SOURCE_LINE_FOR_1_3_2"
                state = "SOURCE_LINE"
            else:
                classification = "DRAFT_OR_UNCLASSIFIED"
                state = "REVIEW_REQUIRED"
            rows.append(
                {
                    "release_id": release_id,
                    "path": rel(root, path),
                    "classification": classification,
                    "state": state,
                    "publication_allowed": False,
                }
            )
    return {
        "schema_id": "LRGEF_RELEASE_PORTFOLIO_v1",
        "generated_at": TIMESTAMP,
        "active_release_id": RELEASE_ID,
        "rows": rows,
        "summary": {
            "release_unit_total": len(rows),
            "scientific_no_send_rc_total": sum(1 for row in rows if row["classification"] == "SCIENTIFIC_NO_SEND_RC"),
            "publication_allowed_total": 0,
        },
    }
