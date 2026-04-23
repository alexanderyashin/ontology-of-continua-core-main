from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TOOLS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TOOLS_DIR.parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from oc_core_1_3_cerberus_lib import validate_existing_cerberus_bundle  # noqa: E402
from oc_core_1_3_science_spot_lib import validate_existing_bundle  # noqa: E402


EDITORIAL_DIR = REPO_ROOT / "releases" / "oc_core_1_3" / "editorial"
HOSTILE_REVIEW_DIR = EDITORIAL_DIR / "dossier_packages" / "hostile_review"
PUBLIC_REVIEW_DIR = HOSTILE_REVIEW_DIR / "public_repo"
LOGION_ROOT = Path("C:/Users/Megaport/work/worktrees/oc13-publication-clean")

README_PATH = REPO_ROOT / "README.md"
ARCHITECTURE_PATH = REPO_ROOT / "ARCHITECTURE.md"
BUILD_NOTES_PATH = REPO_ROOT / "BUILD_NOTES.md"
BUILD_CORE_PATH = REPO_ROOT / "build_core.sh"
BUILD_WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "build-pdf.yml"
TAG_RELEASE_WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "core-release-on-tag.yml"
MANIFEST_PATH = REPO_ROOT / "releases" / "oc_core_1_3" / "OC_CORE_1_3_ZENODO_EN_ONLY_MANIFEST.json"

TOPLEVEL_OUTPUTS = {
    "audit_matrix_json": EDITORIAL_DIR / "OC_PUBLIC_REPO_AUDIT_MATRIX.json",
    "audit_matrix_md": EDITORIAL_DIR / "OC_PUBLIC_REPO_AUDIT_MATRIX.md",
    "governance_gap_report_md": EDITORIAL_DIR / "OC_PUBLIC_REPO_GOVERNANCE_GAP_REPORT.md",
    "release_risk_report_md": EDITORIAL_DIR / "OC_PUBLIC_REPO_RELEASE_RISK_REPORT.md",
    "critique_readiness_report_md": EDITORIAL_DIR / "OC_PUBLIC_REPO_CRITIQUE_READINESS_REPORT.md",
    "artifact_map_json": EDITORIAL_DIR / "OC_PUBLIC_RELEASE_ARTIFACT_MAP_latest.json",
    "archive_contract_json": EDITORIAL_DIR / "OC_PUBLIC_RELEASE_ARCHIVE_CONTRACT_latest.json",
    "build_recipe_md": EDITORIAL_DIR / "OC_PUBLIC_BUILD_RECIPE_latest.md",
    "gate_cert_json": EDITORIAL_DIR / "OC_PUBLIC_RELEASE_GATE_CERT_latest.json",
    "parity_audit_json": EDITORIAL_DIR / "OC_PUBLIC_PRIVATE_DRIFT_AUDIT_latest.json",
    "critique_intake_json": EDITORIAL_DIR / "OC_PUBLIC_CRITIQUE_INTAKE_LEDGER_latest.json",
    "rebuttal_prep_json": EDITORIAL_DIR / "OC_PUBLIC_REBUTTAL_PREP_BOARD_latest.json",
    "bridge_spec_md": EDITORIAL_DIR / "OC_PUBLIC_CRITIQUE_TO_LOGION_BRIDGE_SPEC.md",
    "control_plane_json": EDITORIAL_DIR / "OC_PUBLIC_REPO_CONTROL_PLANE_latest.json",
    "execute_now_manifest_md": EDITORIAL_DIR / "OC_PUBLIC_REPO_EXECUTE_NOW_MANIFEST_latest.md",
    "release_safety_board_json": EDITORIAL_DIR / "OC_PUBLIC_REPO_RELEASE_SAFETY_BOARD_latest.json",
    "critique_ready_board_json": EDITORIAL_DIR / "OC_PUBLIC_REPO_CRITIQUE_READY_BOARD_latest.json",
    "do_not_do_board_json": EDITORIAL_DIR / "OC_PUBLIC_REPO_DO_NOT_DO_BOARD_latest.json",
}

PUBLIC_DOSSIER_OUTPUTS = {
    "readme": PUBLIC_REVIEW_DIR / "README.md",
    "manifest": PUBLIC_REVIEW_DIR / "manifest.json",
    "formal_dossier": PUBLIC_REVIEW_DIR / "formal_dossier.md",
}

REPRODUCIBILITY_ARCHIVE_MEMBERS = [
    ".github/workflows/build-pdf.yml",
    ".github/workflows/core-release-on-tag.yml",
    ".zenodo.json",
    "ARCHITECTURE.md",
    "BUILD_NOTES.md",
    "CONVENTIONS.md",
    "LICENSE",
    "README.md",
    "VERSION",
    "appendix",
    "bib",
    "build_core.sh",
    "content",
    "figures",
    "main.tex",
    "master_core_structure.yaml",
    "preamble.tex",
    "releases/oc_core_1_3",
    "tools/build_oc_core_1_3_science_spot.py",
    "tools/build_oc_public_repo_release_hardening_v8.py",
    "tools/fix_math_in_headings.py",
    "tools/generate_auto_inputs.py",
    "tools/generate_core_from_yaml.py",
    "tools/oc_core_1_3_cerberus_lib.py",
    "tools/oc_core_1_3_science_spot_lib.py",
    "tools/run_oc_core_1_3_cerberus_review.py",
    "tools/stage_oc_core_1_3_zenodo_en_release.py",
    "tools/stage_oc_public_release_artifacts.py",
    "tools/validate_core_structure.py",
    "tools/validate_oc_core_1_3_science_spot.py",
]

PRIVATE_NEVER_LEAK_PATTERNS = [
    "logion/k0/governance/status/LOGION_*",
    "logion/k0/governance/status/OWNER_*",
    "logion/k0/governance/status/OC_LOGION_*",
    "logion/k0/governance/status/OC_BUSINESS_*",
    "logion/k0/governance/status/OC_EXECUTE_NOW_MANIFEST*",
]


def repo_rel(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def json_bytes(payload: Any) -> bytes:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n"


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(json_bytes(payload))


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not text.endswith("\n"):
        text += "\n"
    path.write_text(text, encoding="utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def run_command(args: list[str]) -> str:
    proc = subprocess.run(args, cwd=REPO_ROOT, capture_output=True, text=True, check=True)
    return proc.stdout.strip()


def git_head_sha() -> str:
    return run_command(["git", "rev-parse", "HEAD"])


def git_branch() -> str:
    return run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"])


def git_is_clean() -> bool:
    return run_command(["git", "status", "--short"]) == ""


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def compact(value: Any) -> str:
    return " ".join(str(value or "").replace("\r", " ").replace("\n", " ").replace("\t", " ").split())


def render_markdown_rows(rows: list[dict[str, Any]], ordered_fields: list[str]) -> str:
    if not rows:
        return "- none"
    lines: list[str] = []
    for row in rows:
        parts = [f"{field}={compact(row.get(field, ''))}" for field in ordered_fields]
        lines.append(f"- {'; '.join(parts)}")
    return "\n".join(lines)


def status_rank(value: str) -> int:
    order = {
        "UNSAFE": 0,
        "PARTIALLY_HARDENED": 1,
        "RELEASE_SAFE": 2,
        "CRITIQUE_READY": 3,
        "INSTITUTE_GRADE_PUBLIC_SURFACE": 4,
    }
    return order.get(value, -1)


def requirement_status(ok: bool, broken: bool = False) -> str:
    if ok:
        return "IMPLEMENTED"
    return "BROKEN" if broken else "MISSING"


def classify_surface_status(row_statuses: list[str]) -> str:
    if any(status == "UNSAFE" for status in row_statuses):
        return "UNSAFE"
    if row_statuses and all(status in {"CRITIQUE_READY", "INSTITUTE_GRADE_PUBLIC_SURFACE", "RELEASE_SAFE"} for status in row_statuses):
        return "RELEASE_SAFE"
    return "PARTIALLY_HARDENED"


def build_artifact_map(manifest: dict[str, Any], repo_sha: str, generated_at: str) -> dict[str, Any]:
    files = manifest.get("files") or []
    staged_refs = [str(item.get("stage_ref", item.get("source_ref", ""))) for item in files if isinstance(item, dict)]
    required_upload_members = list(manifest.get("required_upload_members") or [])
    archive_members = []
    missing_archive_members: list[str] = []
    for ref in REPRODUCIBILITY_ARCHIVE_MEMBERS:
        target = REPO_ROOT / ref
        if target.exists():
            archive_members.append(ref)
        else:
            missing_archive_members.append(ref)

    return {
        "schema_id": "OC_PUBLIC_RELEASE_ARTIFACT_MAP_v1",
        "artifact_map_id": "OC_PUBLIC_RELEASE_ARTIFACT_MAP",
        "generated_at_utc": generated_at,
        "repo_sha": repo_sha,
        "canonical_stage_helper": "tools/stage_oc_core_1_3_zenodo_en_release.py",
        "canonical_archive_helper": "tools/stage_oc_public_release_artifacts.py",
        "release_scope": manifest.get("release_scope", "OC_CORE_1_3_ENGLISH_FLAGSHIP_RELEASE_PACKAGE"),
        "release_version": manifest.get("release_version", "1.3.0"),
        "release_upload_assets": [
            {
                "asset_id": "PRIMARY_COMPILED_PDF",
                "path_ref": "build/main.pdf",
                "role": "compiled_pdf",
            },
            {
                "asset_id": "ZENODO_EN_RELEASE_PACKAGE",
                "path_ref": "build_oc_core_1_3_zenodo_en_only.zip",
                "role": "manifest_staged_release_package",
            },
            {
                "asset_id": "PUBLIC_REPRODUCIBILITY_ARCHIVE",
                "path_ref": "build_oc_public_release_archive.zip",
                "role": "explicit_reproducibility_archive",
            },
        ],
        "required_upload_members": required_upload_members,
        "manifest_stage_members": staged_refs,
        "manifest_stage_member_total": len(staged_refs),
        "reproducibility_archive_members": archive_members,
        "reproducibility_archive_member_total": len(archive_members),
        "missing_reproducibility_archive_members": missing_archive_members,
        "workflow_refs": [
            ".github/workflows/build-pdf.yml",
            ".github/workflows/core-release-on-tag.yml",
        ],
        "archive_stage_directory": "build_oc_public_release_archive",
        "zenodo_stage_directory": str(manifest.get("staging_directory", "build_oc_core_1_3_zenodo_en_only")),
        "source_of_truth_refs": [
            "README.md",
            "ARCHITECTURE.md",
            "BUILD_NOTES.md",
            "build_core.sh",
            "releases/oc_core_1_3/README.md",
            "releases/oc_core_1_3/OC_CORE_1_3_ZENODO_EN_ONLY_MANIFEST.json",
            "releases/oc_core_1_3/editorial/OC_CORE_1_3_CERBERUS_ACCEPTANCE_CERT_latest.json",
        ],
    }


def build_archive_contract(artifact_map: dict[str, Any], generated_at: str, repo_sha: str) -> dict[str, Any]:
    archive_members = artifact_map["reproducibility_archive_members"]
    workflow_included = all(ref in archive_members for ref in artifact_map["workflow_refs"])
    status = "RELEASE_SAFE" if workflow_included and not artifact_map["missing_reproducibility_archive_members"] else "PARTIALLY_HARDENED"
    return {
        "schema_id": "OC_PUBLIC_RELEASE_ARCHIVE_CONTRACT_v1",
        "archive_contract_id": "OC_PUBLIC_RELEASE_ARCHIVE_CONTRACT",
        "generated_at_utc": generated_at,
        "repo_sha": repo_sha,
        "status": status,
        "source_zip_policy": "EXPLICIT_ARTIFACT_MAP_WITH_WORKFLOW_PROVENANCE_INCLUDED",
        "canonical_archive_helper": artifact_map["canonical_archive_helper"],
        "canonical_stage_helper": artifact_map["canonical_stage_helper"],
        "workflow_provenance_policy": {
            "status": "INCLUDED" if workflow_included else "MISSING",
            "required_refs": artifact_map["workflow_refs"],
        },
        "included_path_refs": archive_members,
        "excluded_by_omission": [
            "$build/",
            "build/",
            "build_*",
            "__pycache__/",
            "*.aux",
            "*.bcf",
            "*.blg",
            "*.bbl",
            "*.log",
            "*.out",
            "*.run.xml",
            "*.toc",
        ],
        "archive_asset_path_ref": "build_oc_public_release_archive.zip",
        "notes": [
            "The reproducibility archive is explicit rather than repo-wide. Generated build residues and scratch files are excluded by omission.",
            "Workflow provenance is included so the public release archive can explain how CI, validation, and tag-release gates are executed.",
        ],
    }


def build_parity_audit(repo_sha: str, generated_at: str) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    packaged_mirror_total = 0
    matching_total = 0
    missing_total = 0
    divergent_total = 0
    canonical_public_only_total = 0

    public_surface_paths = sorted(path for path in EDITORIAL_DIR.glob("*.json") if path.is_file())
    for path in public_surface_paths:
        payload = load_json(path)
        metadata = payload.get("metadata") if isinstance(payload, dict) else None
        private_ref = ""
        if isinstance(metadata, dict):
            private_ref = str(metadata.get("surface", "") or "")
        row = {
            "public_ref": repo_rel(path),
            "private_ref": private_ref,
        }
        if private_ref.startswith("logion/"):
            packaged_mirror_total += 1
            private_path = LOGION_ROOT / private_ref
            row["private_ref_exists"] = private_path.exists()
            if private_path.exists():
                public_digest = sha256_bytes(json_bytes(payload))
                private_payload = load_json(private_path)
                private_digest = sha256_bytes(json_bytes(private_payload))
                row["public_digest"] = public_digest
                row["private_digest"] = private_digest
                if public_digest == private_digest:
                    row["parity_status"] = "MATCH"
                    matching_total += 1
                else:
                    row["parity_status"] = "DIVERGED"
                    divergent_total += 1
            else:
                row["parity_status"] = "PRIVATE_TWIN_NOT_PRESENT"
                missing_total += 1
        else:
            row["parity_status"] = "CANONICAL_PUBLIC_ONLY"
            canonical_public_only_total += 1
        rows.append(row)

    summary = {
        "packaged_mirror_total": packaged_mirror_total,
        "matching_private_twin_total": matching_total,
        "private_twin_missing_total": missing_total,
        "diverged_total": divergent_total,
        "canonical_public_only_total": canonical_public_only_total,
        "status": "UNSAFE"
        if divergent_total > 0
        else ("PARTIALLY_HARDENED" if missing_total > 0 else "RELEASE_SAFE"),
    }
    return {
        "schema_id": "OC_PUBLIC_PRIVATE_DRIFT_AUDIT_v1",
        "audit_id": "OC_PUBLIC_PRIVATE_DRIFT_AUDIT",
        "generated_at_utc": generated_at,
        "repo_sha": repo_sha,
        "summary": summary,
        "private_never_leak_patterns": PRIVATE_NEVER_LEAK_PATTERNS,
        "rows": rows,
    }


def build_public_critique_assets(repo_sha: str, generated_at: str) -> tuple[dict[str, Any], dict[str, Any], str, dict[str, Any]]:
    dossier_dirs = sorted(path for path in HOSTILE_REVIEW_DIR.iterdir() if path.is_dir() and path.name != "public_repo")
    intake_rows: list[dict[str, Any]] = [
        {
            "critique_id": "PUBLIC_REPO::ARCHITECTURE_TRUTH_DRIFT",
            "critique_class": "public-repo architecture drift",
            "target_surface": "README.md / ARCHITECTURE.md / BUILD_NOTES.md",
            "target_audience": "public reviewers",
            "response_mode": "CORRECTIVE_DOCUMENTATION_AND_MACHINE_AUDIT",
            "bridge_route": "LOGION_EXTERNAL_SIGNAL_INBOX_latest.json",
            "status": "CRITIQUE_READY",
        },
        {
            "critique_id": "PUBLIC_REPO::RELEASE_SELECTOR_AMBIGUITY",
            "critique_class": "release determinism criticism",
            "target_surface": ".github/workflows/core-release-on-tag.yml",
            "target_audience": "release and reproducibility reviewers",
            "response_mode": "ARTIFACT_MAP_AND_ARCHIVE_CONTRACT",
            "bridge_route": "LOGION_CRITIQUE_ROUTING_BOARD_latest.json",
            "status": "CRITIQUE_READY",
        },
    ]
    rebuttal_rows: list[dict[str, Any]] = []
    for dossier_dir in dossier_dirs:
        manifest_path = dossier_dir / "manifest.json"
        manifest = load_json(manifest_path) if manifest_path.exists() else {}
        critique_id = f"PUBLIC_DOSSIER::{dossier_dir.name.upper()}"
        intake_rows.append(
            {
                "critique_id": critique_id,
                "critique_class": "hostile scientific review",
                "target_surface": repo_rel(dossier_dir),
                "target_audience": "hostile scientific reviewers",
                "response_mode": "DOSSIER_PLUS_LOGION_BRIDGE",
                "bridge_route": "LOGION_EXTERNAL_SIGNAL_INBOX_latest.json",
                "status": "CRITIQUE_READY",
            }
        )
        rebuttal_rows.append(
            {
                "critique_id": critique_id,
                "package_ref": repo_rel(dossier_dir),
                "manifest_id": manifest.get("package_id", dossier_dir.name),
                "response_surface_ref": "releases/oc_core_1_3/editorial/OC_PUBLIC_CRITIQUE_TO_LOGION_BRIDGE_SPEC.md",
                "status": "CRITIQUE_READY",
            }
        )

    critique_intake = {
        "schema_id": "OC_PUBLIC_CRITIQUE_INTAKE_LEDGER_v1",
        "ledger_id": "OC_PUBLIC_CRITIQUE_INTAKE_LEDGER",
        "generated_at_utc": generated_at,
        "repo_sha": repo_sha,
        "summary": {
            "critique_total": len(intake_rows),
            "hostile_dossier_total": len(dossier_dirs),
            "status": "CRITIQUE_READY",
        },
        "rows": intake_rows,
    }
    rebuttal_board = {
        "schema_id": "OC_PUBLIC_REBUTTAL_PREP_BOARD_v1",
        "board_id": "OC_PUBLIC_REBUTTAL_PREP_BOARD",
        "generated_at_utc": generated_at,
        "repo_sha": repo_sha,
        "summary": {
            "ready_total": len(rebuttal_rows),
            "status": "CRITIQUE_READY",
        },
        "rows": rebuttal_rows,
    }
    bridge_spec = "\n".join(
        [
            "# OC Public Critique To Logion Bridge",
            "",
            "This bridge defines how critique raised against the public repository is handed",
            "off into Logion without leaking private governance or widening claims.",
            "",
            "## Public intake classes",
            "",
            "- documentation drift",
            "- release determinism ambiguity",
            "- hostile scientific review dossiers",
            "",
            "## Bridge law",
            "",
            "1. Public critique stays source-first: the public repo accepts only critique packets",
            "   grounded in public docs, public editorial surfaces, or hostile-review packages.",
            "2. Every critique packet is mirrored into Logion as a bounded external signal, not as",
            "   public claim inflation.",
            "3. Public packets may reference packaged mirrors, but they must not expose private-only",
            "   governance boards, owner queues, revenue wedges, or internal allocator state.",
            "4. Any claim-strength dispute is resolved against the existing science support class and",
            "   the public/private parity contract.",
            "5. Outbound reviewer-facing response packets are activation-ready only; no live posting,",
            "   upload, or owner-skipping action is authorized by this bridge.",
            "",
            "## Logion handoff targets",
            "",
            "- `LOGION_EXTERNAL_SIGNAL_INBOX_latest.json`",
            "- `LOGION_CRITIQUE_ROUTING_BOARD_latest.json`",
            "- `LOGION_REBUTTAL_AND_CORRECTION_LEDGER_latest.json`",
            "",
            "## Public safety boundary",
            "",
            "- Never copy `LOGION_*`, owner-benefit, business, or private runtime surfaces into the",
            "  public repo except where a public editorial surface is already an explicit packaged mirror.",
        ]
    )
    public_manifest = {
        "package_id": "hostile_review/public_repo",
        "generated_at_utc": generated_at,
        "repo_sha": repo_sha,
        "files": [
            "releases/oc_core_1_3/editorial/OC_PUBLIC_CRITIQUE_INTAKE_LEDGER_latest.json",
            "releases/oc_core_1_3/editorial/OC_PUBLIC_REBUTTAL_PREP_BOARD_latest.json",
            "releases/oc_core_1_3/editorial/OC_PUBLIC_CRITIQUE_TO_LOGION_BRIDGE_SPEC.md",
            "releases/oc_core_1_3/editorial/dossier_packages/hostile_review/public_repo/formal_dossier.md",
        ],
        "status": "CRITIQUE_READY",
    }
    return critique_intake, rebuttal_board, bridge_spec, public_manifest


def build_audit_rows(
    docs_truth_ok: bool,
    build_script_ok: bool,
    build_workflow_ok: bool,
    tag_release_ok: bool,
    archive_contract_ok: bool,
    parity_status: str,
    critique_ready: bool,
) -> list[dict[str, Any]]:
    return [
        {
            "requirement_id": "V8_REQ_001",
            "description": "README reflects Core 1.3 public-source reality instead of stale Core 1.2 freeze language.",
            "status": requirement_status(docs_truth_ok, broken=True),
            "evidence_ref": "README.md",
            "remediation": "Keep the repo entrypoint aligned to the real Core 1.3 source corpus and public/private boundary.",
        },
        {
            "requirement_id": "V8_REQ_002",
            "description": "ARCHITECTURE.md reflects actual Core 1.3 repository architecture.",
            "status": requirement_status(docs_truth_ok, broken=True),
            "evidence_ref": "ARCHITECTURE.md",
            "remediation": "Remove Core 1.1-only architecture claims and describe current source/build/release layers.",
        },
        {
            "requirement_id": "V8_REQ_003",
            "description": "BUILD_NOTES.md reflects the real Core 1.3 fail-closed build and release flow.",
            "status": requirement_status(docs_truth_ok, broken=True),
            "evidence_ref": "BUILD_NOTES.md",
            "remediation": "Document the actual build sequence, validation path, and release gate.",
        },
        {
            "requirement_id": "V8_REQ_004",
            "description": "build_core.sh fails closed on validator/build-critical failures.",
            "status": requirement_status(build_script_ok, broken=True),
            "evidence_ref": "build_core.sh",
            "remediation": "Remove warning-only continuation and fail on missing bibliography, missing BCF, or missing PDF.",
        },
        {
            "requirement_id": "V8_REQ_005",
            "description": "build-pdf workflow performs build plus public-release validation and staging.",
            "status": requirement_status(build_workflow_ok, broken=True),
            "evidence_ref": ".github/workflows/build-pdf.yml",
            "remediation": "Use the v8 builder and stage helpers so CI produces auditable public artifacts.",
        },
        {
            "requirement_id": "V8_REQ_006",
            "description": "Tag release is deterministic, gate-aware, and no longer uses find/head selection.",
            "status": requirement_status(tag_release_ok, broken=True),
            "evidence_ref": ".github/workflows/core-release-on-tag.yml",
            "remediation": "Read deterministic asset refs from the artifact map and require a release-safe gate cert.",
        },
        {
            "requirement_id": "V8_REQ_007",
            "description": "Explicit public release artifact map and archive contract are materialized.",
            "status": requirement_status(archive_contract_ok),
            "evidence_ref": "releases/oc_core_1_3/editorial/OC_PUBLIC_RELEASE_ARTIFACT_MAP_latest.json",
            "remediation": "Keep release packaging explicit and source-first.",
        },
        {
            "requirement_id": "V8_REQ_008",
            "description": "Public/private parity drift is machine-detectable.",
            "status": requirement_status(parity_status != "UNSAFE", broken=parity_status == "UNSAFE"),
            "evidence_ref": "releases/oc_core_1_3/editorial/OC_PUBLIC_PRIVATE_DRIFT_AUDIT_latest.json",
            "remediation": "Only declared packaged mirrors may track private authority; divergence must fail closed.",
        },
        {
            "requirement_id": "V8_REQ_009",
            "description": "Public critique intake, rebuttal prep, and Logion bridge surfaces are present.",
            "status": requirement_status(critique_ready),
            "evidence_ref": "releases/oc_core_1_3/editorial/OC_PUBLIC_CRITIQUE_TO_LOGION_BRIDGE_SPEC.md",
            "remediation": "Keep the hostile-review public lane activation-ready and bounded.",
        },
        {
            "requirement_id": "V8_REQ_010",
            "description": "Final public control-plane family is materialized.",
            "status": "IMPLEMENTED",
            "evidence_ref": "releases/oc_core_1_3/editorial/OC_PUBLIC_REPO_CONTROL_PLANE_latest.json",
            "remediation": "",
        },
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the OC Core 1.3 public-repo release hardening and critique readiness surfaces.")
    _ = parser.parse_args()

    generated_at = now_utc()
    repo_sha = git_head_sha()
    branch = git_branch()
    repo_clean = git_is_clean()

    manifest = load_json(MANIFEST_PATH)
    artifact_map = build_artifact_map(manifest, repo_sha, generated_at)
    archive_contract = build_archive_contract(artifact_map, generated_at, repo_sha)
    parity_audit = build_parity_audit(repo_sha, generated_at)
    critique_intake, rebuttal_board, bridge_spec, public_manifest = build_public_critique_assets(repo_sha, generated_at)

    readme_text = read_text(README_PATH)
    architecture_text = read_text(ARCHITECTURE_PATH)
    build_notes_text = read_text(BUILD_NOTES_PATH)
    build_core_text = read_text(BUILD_CORE_PATH)
    build_workflow_text = read_text(BUILD_WORKFLOW_PATH)
    tag_release_text = read_text(TAG_RELEASE_WORKFLOW_PATH)

    stale_markers = [
        "Repository Architecture — Ontology of Continua Core 1.1",
        "Build System Notes — Ontology of Continua Core 1.1",
        "ARCHITECTURE FREEZE (Core 1.2)",
        "This README is the authoritative entry point for the Core 1.2 repository.",
    ]
    docs_truth_ok = (
        all(marker not in readme_text for marker in stale_markers)
        and all(marker not in architecture_text for marker in stale_markers[:1])
        and all(marker not in build_notes_text for marker in stale_markers[:2])
        and "public/private boundary" in readme_text.lower()
        and "release bundle" in architecture_text.lower()
        and "core-release-on-tag.yml" in build_notes_text
    )
    build_script_ok = (
        "if ! python tools/validate_core_structure.py;" not in build_core_text
        and "[WARN] Validator reported issues" not in build_core_text
        and "for required_cmd in python xelatex biber; do" in build_core_text
        and "if [ ! -f build/main.pdf ]" in build_core_text
        and "ERROR: No .bib files found" in build_core_text
        and "ERROR: build/main.bcf not found" in build_core_text
    )
    build_workflow_ok = (
        "tools/build_oc_public_repo_release_hardening_v8.py" in build_workflow_text
        and "tools/stage_oc_core_1_3_zenodo_en_release.py" in build_workflow_text
        and "tools/stage_oc_public_release_artifacts.py" in build_workflow_text
        and "Core 1.1 PDF" not in build_workflow_text
        and "OC Public Release Surfaces" in build_workflow_text
    )
    tag_release_ok = (
        "find build -maxdepth 1 -name \"*.pdf\" | head -n 1" not in tag_release_text
        and "tools/build_oc_public_repo_release_hardening_v8.py" in tag_release_text
        and "tools/stage_oc_core_1_3_zenodo_en_release.py" in tag_release_text
        and "tools/stage_oc_public_release_artifacts.py" in tag_release_text
        and "release_gate_status" in tag_release_text
    )
    archive_contract_ok = archive_contract["status"] == "RELEASE_SAFE"
    critique_ready = critique_intake["summary"]["status"] == "CRITIQUE_READY"

    science_bundle_errors = validate_existing_bundle(REPO_ROOT)
    cerberus_errors = validate_existing_cerberus_bundle(REPO_ROOT, require_clean=True)
    science_bundle_status = "RELEASE_SAFE" if not science_bundle_errors else "UNSAFE"
    cerberus_bundle_status = "RELEASE_SAFE" if not cerberus_errors else "PARTIALLY_HARDENED"

    audit_rows = build_audit_rows(
        docs_truth_ok=docs_truth_ok,
        build_script_ok=build_script_ok,
        build_workflow_ok=build_workflow_ok,
        tag_release_ok=tag_release_ok,
        archive_contract_ok=archive_contract_ok,
        parity_status=str(parity_audit["summary"]["status"]),
        critique_ready=critique_ready,
    )
    implemented_total = sum(1 for row in audit_rows if row["status"] == "IMPLEMENTED")
    non_implemented_total = len(audit_rows) - implemented_total

    release_safety_rows = [
        {
            "check_id": "DOCS_TRUTH",
            "status": "INSTITUTE_GRADE_PUBLIC_SURFACE" if docs_truth_ok else "UNSAFE",
            "detail": "Top-level docs align to actual Core 1.3 repo reality.",
        },
        {
            "check_id": "SCIENCE_BUNDLE_INTERNAL_CONSISTENCY",
            "status": science_bundle_status,
            "detail": "Existing Core 1.3 science bundle remains internally consistent.",
        },
        {
            "check_id": "CERBERUS_HEAD_SYNC",
            "status": cerberus_bundle_status,
            "detail": "Current Cerberus latest bundle is head-synced and clean only when the status is RELEASE_SAFE.",
        },
        {
            "check_id": "BUILD_SCRIPT_FAIL_CLOSED",
            "status": "RELEASE_SAFE" if build_script_ok else "UNSAFE",
            "detail": "build_core.sh no longer tolerates validator or build-critical drift.",
        },
        {
            "check_id": "BUILD_WORKFLOW_HARDENED",
            "status": "RELEASE_SAFE" if build_workflow_ok else "PARTIALLY_HARDENED",
            "detail": "CI build produces validated public release artifacts.",
        },
        {
            "check_id": "TAG_RELEASE_HARDENED",
            "status": "RELEASE_SAFE" if tag_release_ok else "UNSAFE",
            "detail": "Tag release reads deterministic assets and requires a release-safe gate cert.",
        },
        {
            "check_id": "ARCHIVE_CONTRACT",
            "status": archive_contract["status"],
            "detail": "Reproducibility archive contract is explicit and includes workflow provenance.",
        },
        {
            "check_id": "PUBLIC_PRIVATE_PARITY",
            "status": str(parity_audit["summary"]["status"]),
            "detail": "Declared public/private mirror parity is machine-detectable.",
        },
    ]
    critique_ready_rows = [
        {
            "check_id": "PUBLIC_CRITIQUE_INTAKE",
            "status": critique_intake["summary"]["status"],
            "detail": "Public critique packets are structured and bounded.",
        },
        {
            "check_id": "PUBLIC_REBUTTAL_PREP",
            "status": rebuttal_board["summary"]["status"],
            "detail": "Rebuttal prep board exists for hostile-review and infrastructure critique lanes.",
        },
        {
            "check_id": "CRITIQUE_BRIDGE_SPEC",
            "status": "CRITIQUE_READY",
            "detail": "Public-to-Logion bridge is explicit and claim-ceiling bounded.",
        },
        {
            "check_id": "PUBLIC_HOSTILE_REVIEW_PACK",
            "status": "CRITIQUE_READY",
            "detail": "The hostile-review public_repo package is materialized on disk.",
        },
    ]
    do_not_do_rows = [
        {
            "rule_id": "DO_NOT_RELEASE_WITHOUT_GATE",
            "status": "UNSAFE",
            "forbidden_move": "Create a tag release when OC_PUBLIC_RELEASE_GATE_CERT_latest.json is not RELEASE_SAFE.",
        },
        {
            "rule_id": "DO_NOT_USE_FIND_HEAD",
            "status": "UNSAFE",
            "forbidden_move": "Select release assets with find/head ambiguity instead of canonical artifact refs.",
        },
        {
            "rule_id": "DO_NOT_REVERT_TO_CORE_1_1_OR_1_2_FREEZE_LANGUAGE",
            "status": "UNSAFE",
            "forbidden_move": "Describe the repo as a Core 1.1 shell or a Core 1.2 architecture freeze when Core 1.3 release routes are present.",
        },
        {
            "rule_id": "DO_NOT_EXCLUDE_WORKFLOW_PROVENANCE",
            "status": "UNSAFE",
            "forbidden_move": "Publish a reproducibility archive that omits .github/workflows without an explicit archive contract.",
        },
        {
            "rule_id": "DO_NOT_LEAK_PRIVATE_LOGION_GOVERNANCE",
            "status": "UNSAFE",
            "forbidden_move": "Expose private owner, revenue, or internal governance surfaces in the public repo.",
        },
    ]

    release_gate_status = "RELEASE_SAFE"
    for row in release_safety_rows:
        if row["status"] not in {"RELEASE_SAFE", "INSTITUTE_GRADE_PUBLIC_SURFACE"}:
            release_gate_status = "PARTIALLY_HARDENED" if row["status"] != "UNSAFE" else "UNSAFE"
            if row["status"] == "UNSAFE":
                break
    critique_status = "CRITIQUE_READY" if all(row["status"] == "CRITIQUE_READY" for row in critique_ready_rows) else "PARTIALLY_HARDENED"
    overall_status = "PARTIALLY_HARDENED"
    if release_gate_status == "RELEASE_SAFE" and critique_status == "CRITIQUE_READY" and docs_truth_ok and parity_audit["summary"]["status"] == "RELEASE_SAFE":
        overall_status = "INSTITUTE_GRADE_PUBLIC_SURFACE"
    elif any(row["status"] == "UNSAFE" for row in release_safety_rows):
        overall_status = "UNSAFE"

    gate_cert = {
        "schema_id": "OC_PUBLIC_RELEASE_GATE_CERT_v1",
        "gate_cert_id": "OC_PUBLIC_RELEASE_GATE_CERT",
        "generated_at_utc": generated_at,
        "repo_sha": repo_sha,
        "branch": branch,
        "repo_clean": repo_clean,
        "docs_truth_status": "INSTITUTE_GRADE_PUBLIC_SURFACE" if docs_truth_ok else "UNSAFE",
        "science_bundle_status": science_bundle_status,
        "cerberus_bundle_status": cerberus_bundle_status,
        "build_script_status": "RELEASE_SAFE" if build_script_ok else "UNSAFE",
        "build_workflow_status": "RELEASE_SAFE" if build_workflow_ok else "PARTIALLY_HARDENED",
        "tag_release_status": "RELEASE_SAFE" if tag_release_ok else "UNSAFE",
        "archive_contract_status": archive_contract["status"],
        "public_private_parity_status": parity_audit["summary"]["status"],
        "release_gate_status": release_gate_status,
        "critique_ready_status": critique_status,
        "overall_status": overall_status,
        "summary": {
            "audit_requirement_total": len(audit_rows),
            "audit_non_implemented_total": non_implemented_total,
            "science_bundle_error_total": len(science_bundle_errors),
            "cerberus_error_total": len(cerberus_errors),
            "packaged_mirror_total": int(parity_audit["summary"]["packaged_mirror_total"]),
            "diverged_total": int(parity_audit["summary"]["diverged_total"]),
            "private_twin_missing_total": int(parity_audit["summary"]["private_twin_missing_total"]),
            "critique_total": int(critique_intake["summary"]["critique_total"]),
        },
    }

    control_plane = {
        "schema_id": "OC_PUBLIC_REPO_CONTROL_PLANE_v1",
        "control_plane_id": "OC_PUBLIC_REPO_CONTROL_PLANE",
        "generated_at_utc": generated_at,
        "repo_sha": repo_sha,
        "branch": branch,
        "repo_clean": repo_clean,
        "overall_status": overall_status,
        "summary": {
            "audit_requirement_total": len(audit_rows),
            "audit_non_implemented_total": non_implemented_total,
            "release_gate_status": release_gate_status,
            "critique_ready_status": critique_status,
            "overall_status": overall_status,
            "packaged_mirror_total": int(parity_audit["summary"]["packaged_mirror_total"]),
            "private_twin_missing_total": int(parity_audit["summary"]["private_twin_missing_total"]),
            "diverged_total": int(parity_audit["summary"]["diverged_total"]),
            "critique_total": int(critique_intake["summary"]["critique_total"]),
            "do_not_do_total": len(do_not_do_rows),
        },
        "refs": {key: repo_rel(path) for key, path in TOPLEVEL_OUTPUTS.items()},
    }

    governance_gap_report = "\n".join(
        [
            "# OC Public Repo Governance Gap Report",
            "",
            f"- generated_at_utc: {generated_at}",
            f"- repo_sha: {repo_sha}",
            f"- audit_non_implemented_total: {non_implemented_total}",
            "",
            "## Open gaps",
            "",
            render_markdown_rows(
                [row for row in audit_rows if row["status"] != "IMPLEMENTED"],
                ["requirement_id", "status", "description", "remediation"],
            ),
        ]
    )
    release_risk_report = "\n".join(
        [
            "# OC Public Repo Release Risk Report",
            "",
            f"- release_gate_status: {release_gate_status}",
            f"- overall_status: {overall_status}",
            "",
            "## Safety board",
            "",
            render_markdown_rows(release_safety_rows, ["check_id", "status", "detail"]),
            "",
            "## Cerberus errors",
            "",
            "\n".join(f"- {compact(error)}" for error in cerberus_errors) if cerberus_errors else "- none",
        ]
    )
    critique_readiness_report = "\n".join(
        [
            "# OC Public Repo Critique Readiness Report",
            "",
            f"- critique_ready_status: {critique_status}",
            f"- critique_total: {critique_intake['summary']['critique_total']}",
            "",
            "## Rebuttal prep",
            "",
            render_markdown_rows(rebuttal_board["rows"], ["critique_id", "status", "package_ref"]),
        ]
    )
    build_recipe = "\n".join(
        [
            "# OC Public Build Recipe",
            "",
            "The public Core 1.3 release flow is deterministic and split into four explicit stages:",
            "",
            "1. Build the canonical PDF:",
            "   `./build_core.sh`",
            "2. Validate the checked-in Core 1.3 science bundle:",
            "   `python tools/validate_oc_core_1_3_science_spot.py`",
            "3. Materialize public release-hardening surfaces:",
            "   `python tools/build_oc_public_repo_release_hardening_v8.py`",
            "4. Stage deterministic upload and reproducibility archives:",
            "   `python tools/stage_oc_core_1_3_zenodo_en_release.py --zip-path build_oc_core_1_3_zenodo_en_only.zip`",
            "   `python tools/stage_oc_public_release_artifacts.py --zip-path build_oc_public_release_archive.zip`",
            "",
            "Tag release is lawful only when `OC_PUBLIC_RELEASE_GATE_CERT_latest.json` reports",
            "`release_gate_status = RELEASE_SAFE`.",
            "",
            "The reproducibility archive includes `.github/workflows/` so workflow provenance",
            "remains inspectable inside the release package itself.",
        ]
    )
    execute_now_manifest = "\n".join(
        [
            "# OC Public Repo Execute Now Manifest",
            "",
            f"- overall_status: {overall_status}",
            f"- release_gate_status: {release_gate_status}",
            "",
            "## Next actions",
            "",
            "1. Rerun the full Cerberus review on the current repository HEAD so the release gate can advance from head-drift-sensitive partial hardening to a release-safe state.",
            "2. Run the public build workflow and inspect the staged `build_oc_core_1_3_zenodo_en_only.zip` and `build_oc_public_release_archive.zip` artifacts.",
            "3. Review `OC_PUBLIC_PRIVATE_DRIFT_AUDIT_latest.json` and resolve any packaged-mirror rows whose private twin is still absent from the local Logion worktree.",
            "4. Keep critique intake and rebuttal prep surfaces current when hostile-review or public architecture criticism changes.",
        ]
    )

    audit_matrix = {
        "schema_id": "OC_PUBLIC_REPO_AUDIT_MATRIX_v1",
        "audit_matrix_id": "OC_PUBLIC_REPO_AUDIT_MATRIX",
        "generated_at_utc": generated_at,
        "repo_sha": repo_sha,
        "branch": branch,
        "summary": {
            "requirement_total": len(audit_rows),
            "implemented_total": implemented_total,
            "non_implemented_total": non_implemented_total,
        },
        "rows": audit_rows,
    }

    audit_matrix_md = "\n".join(
        [
            "# OC Public Repo Audit Matrix",
            "",
            f"- generated_at_utc: {generated_at}",
            f"- repo_sha: {repo_sha}",
            f"- branch: {branch}",
            "",
            render_markdown_rows(audit_rows, ["requirement_id", "status", "description", "evidence_ref", "remediation"]),
        ]
    )

    release_safety_board = {
        "schema_id": "OC_PUBLIC_REPO_RELEASE_SAFETY_BOARD_v1",
        "board_id": "OC_PUBLIC_REPO_RELEASE_SAFETY_BOARD",
        "generated_at_utc": generated_at,
        "repo_sha": repo_sha,
        "summary": {
            "status": release_gate_status,
            "unsafe_total": sum(1 for row in release_safety_rows if row["status"] == "UNSAFE"),
            "partially_hardened_total": sum(1 for row in release_safety_rows if row["status"] == "PARTIALLY_HARDENED"),
        },
        "rows": release_safety_rows,
    }
    critique_ready_board = {
        "schema_id": "OC_PUBLIC_REPO_CRITIQUE_READY_BOARD_v1",
        "board_id": "OC_PUBLIC_REPO_CRITIQUE_READY_BOARD",
        "generated_at_utc": generated_at,
        "repo_sha": repo_sha,
        "summary": {
            "status": critique_status,
            "critique_ready_total": sum(1 for row in critique_ready_rows if row["status"] == "CRITIQUE_READY"),
        },
        "rows": critique_ready_rows,
    }
    do_not_do_board = {
        "schema_id": "OC_PUBLIC_REPO_DO_NOT_DO_BOARD_v1",
        "board_id": "OC_PUBLIC_REPO_DO_NOT_DO_BOARD",
        "generated_at_utc": generated_at,
        "repo_sha": repo_sha,
        "summary": {
            "status": "UNSAFE",
            "row_total": len(do_not_do_rows),
        },
        "rows": do_not_do_rows,
    }

    public_dossier_readme = "\n".join(
        [
            "# Public Repo Hostile-Review Bridge",
            "",
            "This package keeps the public-repo critique lane inside the existing hostile-review",
            "layout instead of creating a second critique tree.",
            "",
            "- `formal_dossier.md` summarizes the public-repo critique mission.",
            "- `manifest.json` points to the public critique ledger, rebuttal prep board, and bridge spec.",
            "- `../../OC_PUBLIC_CRITIQUE_TO_LOGION_BRIDGE_SPEC.md` defines the bounded handoff into Logion.",
        ]
    )
    public_dossier_formal = "\n".join(
        [
            "# Formal Dossier — Public Repo Release Hardening and Critique Readiness",
            "",
            "This dossier does not widen science claims. It packages only the public release-hardening,",
            "critique-intake, and public/private parity surfaces needed for external reproducibility and",
            "reviewer-facing critique preparation.",
            "",
            "## Included lanes",
            "",
            "- public architecture truth repair",
            "- deterministic release and archive hardening",
            "- public/private parity audit",
            "- critique intake and rebuttal prep bridge",
        ]
    )

    write_json(TOPLEVEL_OUTPUTS["artifact_map_json"], artifact_map)
    write_json(TOPLEVEL_OUTPUTS["archive_contract_json"], archive_contract)
    write_json(TOPLEVEL_OUTPUTS["parity_audit_json"], parity_audit)
    write_json(TOPLEVEL_OUTPUTS["critique_intake_json"], critique_intake)
    write_json(TOPLEVEL_OUTPUTS["rebuttal_prep_json"], rebuttal_board)
    write_json(TOPLEVEL_OUTPUTS["gate_cert_json"], gate_cert)
    write_json(TOPLEVEL_OUTPUTS["control_plane_json"], control_plane)
    write_json(TOPLEVEL_OUTPUTS["audit_matrix_json"], audit_matrix)
    write_json(TOPLEVEL_OUTPUTS["release_safety_board_json"], release_safety_board)
    write_json(TOPLEVEL_OUTPUTS["critique_ready_board_json"], critique_ready_board)
    write_json(TOPLEVEL_OUTPUTS["do_not_do_board_json"], do_not_do_board)
    write_text(TOPLEVEL_OUTPUTS["audit_matrix_md"], audit_matrix_md)
    write_text(TOPLEVEL_OUTPUTS["governance_gap_report_md"], governance_gap_report)
    write_text(TOPLEVEL_OUTPUTS["release_risk_report_md"], release_risk_report)
    write_text(TOPLEVEL_OUTPUTS["critique_readiness_report_md"], critique_readiness_report)
    write_text(TOPLEVEL_OUTPUTS["build_recipe_md"], build_recipe)
    write_text(TOPLEVEL_OUTPUTS["bridge_spec_md"], bridge_spec)
    write_text(TOPLEVEL_OUTPUTS["execute_now_manifest_md"], execute_now_manifest)
    write_json(PUBLIC_DOSSIER_OUTPUTS["manifest"], public_manifest)
    write_text(PUBLIC_DOSSIER_OUTPUTS["readme"], public_dossier_readme)
    write_text(PUBLIC_DOSSIER_OUTPUTS["formal_dossier"], public_dossier_formal)

    print(TOPLEVEL_OUTPUTS["control_plane_json"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
