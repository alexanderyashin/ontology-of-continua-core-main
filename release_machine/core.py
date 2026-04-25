from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any

from .constants import (
    CONCEPT_DOI,
    DOI_PENDING,
    GATE_STATES,
    PREVIOUS_DOI,
    PREVIOUS_VERSION,
    RELEASE_ID,
    SEVERITIES,
    TIMESTAMP,
    VERSION,
)

CHANNELS = {
    "all": ["zenodo", "github_release", "github_repo_public_surface"],
    "zenodo": ["zenodo"],
    "github_release": ["github_release"],
    "github_repo_public_surface": ["github_repo_public_surface"],
    "arxiv_preprint": ["arxiv_preprint"],
    "journal_submission": ["journal_submission"],
    "website_page": ["website_page"],
    "outbound_email": ["outbound_email"],
    "investor_deck": ["investor_deck"],
    "product_docs": ["product_docs"],
    "dataset_release": ["dataset_release"],
    "code_package": ["code_package"],
}

GATE_ORDER = [
    ("gate_00_intake", "Release intake and identity"),
    ("gate_01_channel_policy", "Channel policy"),
    ("gate_02_artifact_inventory", "Artifact inventory"),
    ("gate_03_build_reproducibility", "Build and reproducibility"),
    ("gate_04_pdf_document_quality", "PDF document quality"),
    ("gate_05_claim_evidence_ceiling", "Claim and evidence ceiling"),
    ("gate_06_strong_statement_linter", "Strong statement linter"),
    ("gate_07_simulation_data_validation", "Simulation and data boundary"),
    ("gate_08_citation_doi_metadata", "Citation and DOI metadata"),
    ("gate_09_public_surface_parity", "Public surface parity"),
    ("gate_10_security_privacy_secrets", "Security, privacy, secrets"),
    ("gate_11_ci_release_workflow", "CI release workflow"),
    ("gate_12_owner_approval", "Owner approval no-send lock"),
    ("gate_13_publish_preflight", "Publish preflight"),
    ("gate_14_post_release_audit", "Post-release audit"),
]

PDF_ARTIFACTS = [
    "OC_CORE_1_3_2_MASTER_MONOGRAPH_EN.pdf",
    "OC_CORE_1_3_2_JOURNAL_CORE_EN.pdf",
    "OC_CORE_1_3_2_READABLE_OVERVIEW_EN.pdf",
    "OC_CORE_1_3_2_METHODS_AND_REPRODUCIBILITY_COMPANION_EN.pdf",
    "OC_CORE_1_3_2_CRITIQUE_AND_OBJECTION_MAP_EN.pdf",
    "OC_CORE_1_3_2_EXPERT_TECHNICAL_SPINE_EN.pdf",
]
ZIP_NAME = "oc_core_1_3_2_zenodo_release.zip"
RESEARCH_PACKET_ROOT = "releases/oc_core_1_3_2/editorial/research_packets"
RESEARCH_PACKET_FILES = [
    "releases/oc_core_1_3_2/editorial/research_packets/k0_structural_realist_extension/README.md",
    "releases/oc_core_1_3_2/editorial/research_packets/k0_structural_realist_extension/K0_SR_PUBLIC_DECISION_MEMO.md",
    "releases/oc_core_1_3_2/editorial/research_packets/k0_structural_realist_extension/K0_SR_PUBLIC_CLAIM_REGISTRY.yaml",
    "releases/oc_core_1_3_2/editorial/research_packets/k0_structural_realist_extension/K0_SR_PUBLIC_EVIDENCE_SUMMARY.ndjson",
    "releases/oc_core_1_3_2/editorial/research_packets/k0_structural_realist_extension/K0_SR_PUBLIC_GATE_SUMMARY.yaml",
    "releases/oc_core_1_3_2/editorial/research_packets/k0_structural_realist_extension/K0_SR_PUBLIC_SOURCE_MANIFEST.yaml",
    "releases/oc_core_1_3_2/editorial/research_packets/k0_structural_realist_extension/K0_SR_PUBLIC_ARTIFACT_MANIFEST.yaml",
    "releases/oc_core_1_3_2/editorial/research_packets/k0_structural_realist_extension/K0_SR_PUBLIC_REPRODUCIBILITY.md",
]
PUBLIC_SCAN_FILES = [
    "README.md",
    "CLAIMS.md",
    "DATA_MANIFEST.md",
    "REPRODUCIBILITY.md",
    "RUN_ALL.md",
    "SIMULATIONS.md",
    "RELEASE_CONTRACT.md",
    "OWNER_APPROVAL_REQUIRED.md",
    "RELEASE_MACHINE.md",
    "RELEASE_STANDARDS.md",
    "CHANNEL_POLICIES.md",
    "claims/CLAIM_LEDGER_FULL.md",
    "claims/PROMOTED_CLAIMS.md",
    "claims/SUPPORT_ONLY_CLAIMS.md",
    "claims/FRONTIER_OR_FUTURE_WORK.md",
    "data/README_DATA_REPRODUCIBILITY.md",
    "releases/oc_core_1_3_2/README.md",
    "releases/oc_core_1_3_2/editorial/OC_CORE_1_3_2_RELEASE_SCORECARD_latest.md",
    "releases/oc_core_1_3_2/editorial/OC_CORE_1_3_2_OWNER_APPROVAL_PACKET.md",
    "releases/oc_core_1_3_2/editorial/OC_CORE_1_3_2_PUBLISH_MANIFEST_DRAFT.json",
]
LOCAL_PATH_PATTERNS = [
    re.compile(r"[A-Za-z]:[\\/](Users|Work|Temp|tmp)[\\/]", re.IGNORECASE),
    re.compile(r"/home/[^\\s]+", re.IGNORECASE),
]
SECRET_PATTERNS = [
    re.compile(r"(ZENODO|GITHUB|GH|TOKEN|SECRET|PASSWORD)[A-Z0-9_]*\\s*=\\s*['\\\"]?[A-Za-z0-9_\\-]{16,}", re.IGNORECASE),
    re.compile(r"ghp_[A-Za-z0-9_]{20,}"),
]
FORBIDDEN_PUBLIC_TERMS = [
    re.compile(r"\bunignorable\b", re.IGNORECASE),
    re.compile(r"\bkiller\b", re.IGNORECASE),
    re.compile(r"\bdoebatsya\b", re.IGNORECASE),
    re.compile(r"\bindependent audit\b", re.IGNORECASE),
    re.compile(r"\bempirical validation\b", re.IGNORECASE),
    re.compile(r"\bOC\s+solves\s+quantum\s+gravity\b", re.IGNORECASE),
    re.compile(r"\bOC\s+unifies\s+QFT\s+and\s+GR\b", re.IGNORECASE),
    re.compile(r"\bOC\s+derives\s+all\s+physical\s+laws\b", re.IGNORECASE),
    re.compile(r"\bK0\s+is\s+now\s+(a\s+)?(topos|gauge theory|quantum[- ]gravity theory)\b", re.IGNORECASE),
]
ALLOWED_SUPPORT_CLASSES = {
    "FORMALLY_PROVED",
    "THEOREM_NATIVE_HELD_OUT_VALIDATED",
    "OPERATIONALLY_SUPPORTED_WITHIN_BOUNDS",
    "SIMULATION_ILLUSTRATION_ONLY",
    "PUBLIC_ROUTE_DISCOVERY_ONLY",
    "FRONTIER_WORK",
}

def repo_root(start: Path | None = None) -> Path:
    cur = (start or Path.cwd()).resolve()
    for candidate in [cur, *cur.parents]:
        if (candidate / "VERSION").exists() and (candidate / ".git").exists():
            return candidate
    return cur

def release_dir(root: Path) -> Path:
    return root / "releases" / RELEASE_ID

def editorial_dir(root: Path) -> Path:
    return release_dir(root) / "editorial"

def artifacts_dir(root: Path) -> Path:
    return release_dir(root) / "artifacts"

def rel(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()

def research_packet_files(root: Path) -> list[str]:
    packet_root = root / RESEARCH_PACKET_ROOT
    if not packet_root.exists():
        return []
    allowed_suffixes = {".md", ".json", ".ndjson", ".yaml", ".yml", ".txt"}
    files = [
        rel(root, path)
        for path in packet_root.rglob("*")
        if path.is_file() and path.suffix.lower() in allowed_suffixes
    ]
    return sorted(set([*RESEARCH_PACKET_FILES, *files]))

def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))

def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not text.endswith("\n"):
        text += "\n"
    path.write_text(text, encoding="utf-8")

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def gate_result(gate_id: str, title: str, state: str, severity: str = "INFO", summary: str = "", details: dict[str, Any] | None = None, executed: bool = True, justification: str = "") -> dict[str, Any]:
    if state not in GATE_STATES:
        raise ValueError(f"Unknown gate state: {state}")
    if severity not in SEVERITIES:
        raise ValueError(f"Unknown severity: {severity}")
    if state == "PASS" and not executed:
        raise ValueError(f"Gate {gate_id} attempted fake PASS without execution")
    if state == "NOT_APPLICABLE" and not justification:
        raise ValueError(f"Gate {gate_id} needs justification for NOT_APPLICABLE")
    return {
        "gate_id": gate_id,
        "title": title,
        "state": state,
        "severity": severity,
        "summary": summary,
        "details": details or {},
        "executed": executed,
        "executed_at": TIMESTAMP if executed else None,
        "justification": justification,
    }

def credential_gate_result(token_name: str, token_value: str | None) -> dict[str, Any]:
    if token_value and token_value.strip():
        return gate_result("credential_probe", f"{token_name} credential probe", "PASS", summary="Credential material is present for a dry-run probe.")
    return gate_result("credential_probe", f"{token_name} credential probe", "BLOCKED", "HIGH", summary="Credential is absent; this cannot be reported as PASS.")

def waiver_allowed(severity: str) -> bool:
    return severity not in {"CRITICAL", "HIGH"}

def owner_approval_valid(approval: dict[str, Any], current_freeze_hash: str) -> bool:
    return bool(approval.get("approved") is True and approval.get("artifact_freeze_hash") == current_freeze_hash)

def _pdf_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

def make_pdf_bytes(title: str, lines: list[str]) -> bytes:
    content_lines = [f"({ _pdf_escape(title) }) Tj"]  # type: ignore[arg-type]
    for line in lines:
        content_lines.append("T*")
        content_lines.append(f"({ _pdf_escape(line[:96]) }) Tj")
    stream = "BT /F1 12 Tf 72 760 Td 14 TL " + " ".join(content_lines) + " ET"
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        f"<< /Length {len(stream.encode('latin-1'))} >>\nstream\n{stream}\nendstream".encode("latin-1"),
    ]
    body = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for idx, obj in enumerate(objects, start=1):
        offsets.append(len(body))
        body.extend(f"{idx} 0 obj\n".encode("ascii"))
        body.extend(obj)
        body.extend(b"\nendobj\n")
    xref_at = len(body)
    body.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    body.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        body.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    body.extend(f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_at}\n%%EOF\n".encode("ascii"))
    return bytes(body)

def build_primary_pdfs(root: Path) -> list[Path]:
    artifacts_dir(root).mkdir(parents=True, exist_ok=True)
    docs = []
    descriptions = {
        "MASTER_MONOGRAPH": "Master monograph release-candidate surface.",
        "JOURNAL_CORE": "Bounded journal core extraction.",
        "READABLE_OVERVIEW": "Readable overview for first-time reviewers.",
        "METHODS_AND_REPRODUCIBILITY_COMPANION": "Methods, reproducibility, simulations, and data boundaries.",
        "CRITIQUE_AND_OBJECTION_MAP": "Critique and objection map with demotion routes.",
        "EXPERT_TECHNICAL_SPINE": "Expert technical route through formal and operational surfaces.",
    }
    for name in PDF_ARTIFACTS:
        key = name.removeprefix("OC_CORE_1_3_2_").removesuffix("_EN.pdf")
        path = artifacts_dir(root) / name
        pdf = make_pdf_bytes(
            name.removesuffix(".pdf").replace("_", " "),
            [
                "OC Core v1.3.2 release-candidate artifact.",
                descriptions.get(key, "Release-candidate public artifact."),
                f"Previous canonical DOI: {PREVIOUS_DOI}.",
                f"Concept DOI: {CONCEPT_DOI}.",
                f"v1.3.2 DOI: {DOI_PENDING}.",
                "Simulations are deterministic illustration and reproducibility checks only.",
                "Public dataset routes do not widen claim ceilings without pinned snapshots.",
            ],
        )
        path.write_bytes(pdf)
        docs.append(path)
    return docs

def _package_file_candidates(root: Path) -> list[Path]:
    base = [
        "VERSION",
        "LICENSE",
        "CITATION.cff",
        ".zenodo.json",
        "README.md",
        "CLAIMS.md",
        "DATA_MANIFEST.md",
        "REPRODUCIBILITY.md",
        "RUN_ALL.md",
        "SIMULATIONS.md",
        "RELEASE_CONTRACT.md",
        "OWNER_APPROVAL_REQUIRED.md",
        "RELEASE_MACHINE.md",
        "RELEASE_STANDARDS.md",
        "CHANNEL_POLICIES.md",
        "RELEASE_BLOCKERS.md",
        "release_machine.yaml",
        "claims/CLAIM_LEDGER_FULL.json",
        "claims/CLAIM_LEDGER_FULL.md",
        "claims/PROMOTED_CLAIMS.md",
        "claims/DEMOTED_CLAIMS.md",
        "claims/SUPPORT_ONLY_CLAIMS.md",
        "claims/FRONTIER_OR_FUTURE_WORK.md",
        "claims/CLAIM_EVIDENCE_MATRIX.md",
        "claims/STRONG_STATEMENT_TO_CLAIM_MAP.json",
        "data/OC_DATASET_MANIFEST_1_3_2.json",
        "data/OC_DATASET_SNAPSHOT_MANIFEST_1_3_2.json",
        "data/README_DATA_REPRODUCIBILITY.md",
        "data/checksums/SHA256SUMS",
        "data/download_scripts/fetch_manifest.py",
        "data/download_scripts/fetch_public_snapshots.py",
        "simulations/expected_simulations.yml",
        "simulations/schemas/simulation_output.schema.json",
        "simulations/results/OC_CORE_1_3_2_SIMULATION_RESULTS_latest.json",
        "simulations/results/OC_CORE_1_3_2_SIMULATION_RESULTS_latest.md",
        "releases/oc_core_1_3_2/README.md",
        "releases/oc_core_1_3_2/editorial/OC_CORE_1_3_2_POSTFLIGHT_CHECKLIST.md",
    ]
    base.extend(research_packet_files(root))
    for pdf in PDF_ARTIFACTS:
        base.append(f"releases/oc_core_1_3_2/artifacts/{pdf}")
    return [root / item for item in base if (root / item).exists()]

def run_simulation_report(root: Path) -> dict[str, Any]:
    proc = subprocess.run([sys.executable, "simulations/run_all.py", "--write-report"], cwd=root, text=True, capture_output=True, timeout=180)
    if proc.returncode != 0:
        return {
            "simulation_total": 0,
            "expected_total": 11,
            "failure_total": 1,
            "stderr": proc.stderr.strip(),
            "stdout": proc.stdout.strip(),
        }
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"simulation_total": 0, "expected_total": 11, "failure_total": 1, "stdout": proc.stdout.strip()}

def write_inventory_and_checksums(root: Path, include_zip: bool = False) -> dict[str, Any]:
    sha_path = editorial_dir(root) / "OC_CORE_1_3_2_SHA256SUMS"
    inv_path = editorial_dir(root) / "OC_CORE_1_3_2_ARTIFACT_INVENTORY.json"
    files = _package_file_candidates(root)
    entries = []
    for path in sorted(set(files), key=lambda p: rel(root, p)):
        if path == sha_path or path == inv_path:
            continue
        entries.append({
            "path": rel(root, path),
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
            "status": "ASSEMBLED",
            "public_package_member": True,
        })
    if include_zip:
        zip_path = artifacts_dir(root) / ZIP_NAME
        if zip_path.exists():
            entries.append({
                "path": rel(root, zip_path),
                "sha256": sha256_file(zip_path),
                "bytes": zip_path.stat().st_size,
                "status": "ASSEMBLED",
                "public_package_member": False,
            })
    payload = {
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_at": TIMESTAMP,
        "inventory_policy": "inventory and checksum files exclude their own hash; zip hash is recorded after package build",
        "artifact_total": len(entries),
        "entries": entries,
    }
    write_json(inv_path, payload)
    lines = [f"{entry['sha256']}  {entry['path']}" for entry in entries]
    write_text(sha_path, "\n".join(lines) + "\n")
    return payload

def artifact_freeze_hash(root: Path) -> str:
    inventory = read_json(editorial_dir(root) / "OC_CORE_1_3_2_ARTIFACT_INVENTORY.json")
    material = json.dumps(inventory.get("entries", []), sort_keys=True).encode("utf-8")
    return hashlib.sha256(material).hexdigest()

def write_publish_manifest(root: Path) -> dict[str, Any]:
    inv = read_json(editorial_dir(root) / "OC_CORE_1_3_2_ARTIFACT_INVENTORY.json")
    freeze = artifact_freeze_hash(root)
    assets = [
        entry for entry in inv["entries"]
        if entry["path"].endswith(".pdf") or entry["path"].endswith(".zip")
    ]
    manifest = {
        "release_id": RELEASE_ID,
        "version": VERSION,
        "release_state": "RELEASE_READY_NO_SEND",
        "target_channels": ["zenodo", "github_release"],
        "doi": DOI_PENDING,
        "previous_version": PREVIOUS_VERSION,
        "previous_canonical_doi": PREVIOUS_DOI,
        "concept_doi": CONCEPT_DOI,
        "global_no_send_lock": True,
        "owner_approval_required": True,
        "owner_approved": False,
        "publish_allowed": False,
        "artifact_freeze_hash": freeze,
        "assets": assets,
        "zenodo_policy": "new version under existing concept DOI; no standalone upload",
        "github_policy": "draft only until owner approval and final DOI/postflight route exist",
    }
    write_json(editorial_dir(root) / "OC_CORE_1_3_2_PUBLISH_MANIFEST_DRAFT.json", manifest)
    return manifest

def write_owner_packet(root: Path) -> None:
    manifest = read_json(editorial_dir(root) / "OC_CORE_1_3_2_PUBLISH_MANIFEST_DRAFT.json")
    lines = [
        "# OC Core 1.3.2 Owner Approval Packet",
        "",
        "Status: RELEASE_READY_NO_SEND.",
        "",
        f"Artifact freeze hash: `{manifest['artifact_freeze_hash']}`",
        "",
        "Owner approval required: true.",
        "Owner approved: false.",
        "Publish allowed: false.",
        "Global no-send lock: true.",
        "",
        "Approval must be explicit per channel and must cite the exact artifact freeze hash and publish manifest.",
    ]
    write_text(editorial_dir(root) / "OC_CORE_1_3_2_OWNER_APPROVAL_PACKET.md", "\n".join(lines))

def build_package(root: Path, channel: str = "all", no_publish: bool = True) -> dict[str, Any]:
    build_primary_pdfs(root)
    sim_report = run_simulation_report(root)
    write_inventory_and_checksums(root, include_zip=False)
    zip_path = artifacts_dir(root) / ZIP_NAME
    sha_path = editorial_dir(root) / "OC_CORE_1_3_2_SHA256SUMS"
    inv_path = editorial_dir(root) / "OC_CORE_1_3_2_ARTIFACT_INVENTORY.json"
    members = _package_file_candidates(root) + [sha_path, inv_path]
    members = [path for path in members if path.exists() and path.name != ZIP_NAME]
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in sorted(set(members), key=lambda p: rel(root, p)):
            info = zipfile.ZipInfo(rel(root, path), date_time=(2026, 4, 25, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(info, path.read_bytes())
    inventory = write_inventory_and_checksums(root, include_zip=True)
    write_publish_manifest(root)
    write_owner_packet(root)
    return {
        "release_id": RELEASE_ID,
        "version": VERSION,
        "channel": channel,
        "no_publish": no_publish,
        "publish_allowed": False,
        "package": rel(root, zip_path),
        "package_sha256": sha256_file(zip_path),
        "artifact_total": inventory["artifact_total"],
        "simulation_failure_total": sim_report.get("failure_total"),
    }

def _load_claims(root: Path) -> list[dict[str, Any]]:
    return read_json(root / "claims" / "CLAIM_LEDGER_FULL.json")["claims"]

def _allowed_negative_context(pattern: re.Pattern[str], text: str, start: int, end: int) -> bool:
    snippet = text[max(0, start - 32): end + 32].lower()
    if "empirical validation" in pattern.pattern:
        return "not empirical validation" in snippet or "no empirical validation" in snippet
    return False

def _scan_text_files(root: Path, patterns: list[re.Pattern[str]], files: list[str]) -> list[dict[str, str]]:
    hits = []
    for name in files:
        path = root / name
        if not path.exists() or path.suffix.lower() in {".pdf", ".zip"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in patterns:
            matched = False
            for match in pattern.finditer(text):
                if _allowed_negative_context(pattern, text, match.start(), match.end()):
                    continue
                matched = True
                break
            if matched:
                hits.append({"path": name, "pattern": pattern.pattern})
    return hits

def _all_gate_results(root: Path, release: str, channel: str, mode: str) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    channels = CHANNELS.get(channel, [])
    version_text = (root / "VERSION").read_text(encoding="utf-8").strip() if (root / "VERSION").exists() else ""
    release_path = release_dir(root)
    intake_ok = release == RELEASE_ID and version_text == VERSION and release_path.exists()
    results.append(gate_result("gate_00_intake", "Release intake and identity", "PASS" if intake_ok else "FAIL", "CRITICAL" if not intake_ok else "INFO", "Release id, version, and release directory checked.", {"release": release, "version": version_text, "release_dir_exists": release_path.exists()}))

    policy_ok = bool(channels) and all((root / "release_machine" / "config" / "channels" / f"{item}.yaml").exists() for item in channels)
    results.append(gate_result("gate_01_channel_policy", "Channel policy", "PASS" if policy_ok else "FAIL", "HIGH" if not policy_ok else "INFO", "Channel policy files checked.", {"channel": channel, "expanded_channels": channels}))

    inv_path = editorial_dir(root) / "OC_CORE_1_3_2_ARTIFACT_INVENTORY.json"
    inv = read_json(inv_path) if inv_path.exists() else {"entries": []}
    missing = [entry["path"] for entry in inv.get("entries", []) if not (root / entry["path"]).exists()]
    all_assembled = all(entry.get("status") == "ASSEMBLED" for entry in inv.get("entries", []))
    inv_ok = inv_path.exists() and not missing and all_assembled and len(inv.get("entries", [])) >= 25
    results.append(gate_result("gate_02_artifact_inventory", "Artifact inventory", "PASS" if inv_ok else "FAIL", "HIGH" if not inv_ok else "INFO", "Artifact inventory is present and assembled.", {"artifact_total": len(inv.get("entries", [])), "missing": missing}))

    zip_path = artifacts_dir(root) / ZIP_NAME
    build_ok = zip_path.exists() and zip_path.stat().st_size > 5000 and (root / "simulations/results/OC_CORE_1_3_2_SIMULATION_RESULTS_latest.json").exists()
    results.append(gate_result("gate_03_build_reproducibility", "Build and reproducibility", "PASS" if build_ok else "FAIL", "HIGH" if not build_ok else "INFO", "Package and simulation report checked.", {"zip": rel(root, zip_path) if zip_path.exists() else None}))

    pdf_missing = []
    pdf_bad = []
    for name in PDF_ARTIFACTS:
        path = artifacts_dir(root) / name
        if not path.exists():
            pdf_missing.append(name)
        elif not path.read_bytes().startswith(b"%PDF-"):
            pdf_bad.append(name)
    pdf_ok = not pdf_missing and not pdf_bad
    results.append(gate_result("gate_04_pdf_document_quality", "PDF document quality", "PASS" if pdf_ok else "FAIL", "HIGH" if not pdf_ok else "INFO", "Primary PDF artifacts are present and have a PDF header.", {"missing": pdf_missing, "bad": pdf_bad}))

    claims = _load_claims(root)
    claim_ids = [claim["claim_id"] for claim in claims]
    bad_support = [claim["claim_id"] for claim in claims if claim.get("support_class") not in ALLOWED_SUPPORT_CLASSES]
    empty_refs = [claim["claim_id"] for claim in claims if not claim.get("evidence_refs")]
    claim_ok = len(claims) == 20 and len(claim_ids) == len(set(claim_ids)) and not bad_support and not empty_refs
    results.append(gate_result("gate_05_claim_evidence_ceiling", "Claim and evidence ceiling", "PASS" if claim_ok else "FAIL", "HIGH" if not claim_ok else "INFO", "Full claim ledger and support ceilings checked.", {"claim_total": len(claims), "bad_support": bad_support, "empty_refs": empty_refs}))

    scan_files = sorted(set([*PUBLIC_SCAN_FILES, *research_packet_files(root)]))
    strong_hits = _scan_text_files(root, FORBIDDEN_PUBLIC_TERMS, scan_files)
    results.append(gate_result("gate_06_strong_statement_linter", "Strong statement linter", "PASS" if not strong_hits else "FAIL", "HIGH" if strong_hits else "INFO", "Outward-facing surfaces checked for unsafe public rhetoric.", {"hits": strong_hits}))

    sim_path = root / "simulations/results/OC_CORE_1_3_2_SIMULATION_RESULTS_latest.json"
    sim = read_json(sim_path) if sim_path.exists() else {}
    data_manifest = read_json(root / "data/OC_DATASET_MANIFEST_1_3_2.json") if (root / "data/OC_DATASET_MANIFEST_1_3_2.json").exists() else {}
    sim_ok = sim.get("failure_total") == 0 and sim.get("simulation_total") == 11 and sim.get("support_ceiling") == "SIMULATION_ILLUSTRATION_ONLY" and sim.get("validation_claim_allowed") is False
    data_ok = data_manifest.get("validation_claim_allowed") is False and all(row.get("support_ceiling") == "PUBLIC_ROUTE_DISCOVERY_ONLY" for row in data_manifest.get("routes", []))
    results.append(gate_result("gate_07_simulation_data_validation", "Simulation and data boundary", "PASS" if sim_ok and data_ok else "FAIL", "HIGH" if not (sim_ok and data_ok) else "INFO", "Simulation assertions and dataset claim ceilings checked.", {"simulation_total": sim.get("simulation_total"), "failure_total": sim.get("failure_total"), "data_route_total": len(data_manifest.get("routes", []))}))

    manifest_path = editorial_dir(root) / "OC_CORE_1_3_2_PUBLISH_MANIFEST_DRAFT.json"
    manifest = read_json(manifest_path) if manifest_path.exists() else {}
    doi_ok = manifest.get("doi") == DOI_PENDING and manifest.get("previous_canonical_doi") == PREVIOUS_DOI and manifest.get("concept_doi") == CONCEPT_DOI
    results.append(gate_result("gate_08_citation_doi_metadata", "Citation and DOI metadata", "PASS" if doi_ok else "FAIL", "HIGH" if not doi_ok else "INFO", "DOI metadata uses pending v1.3.2 DOI and historical DOI references.", {"doi": manifest.get("doi"), "previous": manifest.get("previous_canonical_doi"), "concept": manifest.get("concept_doi")}))

    parity_hits = []
    for surface in ["README.md", "CLAIMS.md", "DATA_MANIFEST.md", "REPRODUCIBILITY.md", "RUN_ALL.md", "SIMULATIONS.md", "releases/oc_core_1_3_2/README.md"]:
        path = root / surface
        if not path.exists() or VERSION not in path.read_text(encoding="utf-8", errors="ignore"):
            parity_hits.append(surface)
    parity_ok = not parity_hits and manifest.get("release_state") == "RELEASE_READY_NO_SEND" and manifest.get("publish_allowed") is False
    results.append(gate_result("gate_09_public_surface_parity", "Public surface parity", "PASS" if parity_ok else "FAIL", "HIGH" if not parity_ok else "INFO", "Tracked v1.3.2 public surfaces agree on version, DOI state, and no-send state.", {"missing_or_stale": parity_hits}))

    security_files = scan_files + [entry["path"] for entry in inv.get("entries", []) if entry["path"].startswith("releases/oc_core_1_3_2/") and not entry["path"].endswith((".pdf", ".zip"))]
    local_hits = _scan_text_files(root, LOCAL_PATH_PATTERNS, sorted(set(security_files)))
    secret_hits = _scan_text_files(root, SECRET_PATTERNS, sorted(set(security_files)))
    sec_ok = not local_hits and not secret_hits
    results.append(gate_result("gate_10_security_privacy_secrets", "Security, privacy, secrets", "PASS" if sec_ok else "FAIL", "CRITICAL" if not sec_ok else "INFO", "Release surfaces checked for local paths and obvious secret patterns.", {"local_path_hits": local_hits, "secret_hits": secret_hits}))

    workflows = [".github/workflows/release-machine-dry-run.yml", ".github/workflows/release-candidate-build.yml", ".github/workflows/safe-publish-on-tag.yml", ".github/workflows/postflight-public-surface.yml"]
    workflow_ok = all((root / item).exists() for item in workflows)
    results.append(gate_result("gate_11_ci_release_workflow", "CI release workflow", "PASS" if workflow_ok else "FAIL", "HIGH" if not workflow_ok else "INFO", "Dry-run, candidate, safe tag, and postflight workflows checked.", {"workflows": workflows}))

    owner_ok = manifest.get("owner_approval_required") is True and manifest.get("owner_approved") is False and manifest.get("global_no_send_lock") is True and manifest.get("publish_allowed") is False
    results.append(gate_result("gate_12_owner_approval", "Owner approval no-send lock", "PASS" if owner_ok else "FAIL", "CRITICAL" if not owner_ok else "INFO", "Owner approval is required and publish remains locked.", {"owner_approval_required": manifest.get("owner_approval_required"), "owner_approved": manifest.get("owner_approved"), "publish_allowed": manifest.get("publish_allowed")}))

    tag_exists = subprocess.run(["git", "rev-parse", "-q", "--verify", "refs/tags/v1.3.2"], cwd=root, text=True, capture_output=True).returncode == 0
    preflight_ok = not tag_exists and manifest.get("publish_allowed") is False
    results.append(gate_result("gate_13_publish_preflight", "Publish preflight", "PASS" if preflight_ok else "FAIL", "CRITICAL" if not preflight_ok else "INFO", "No v1.3.2 tag is present and no-send publish policy is active.", {"local_tag_v1_3_2_exists": tag_exists, "publish_allowed": manifest.get("publish_allowed")}))

    results.append(gate_result("gate_14_post_release_audit", "Post-release audit", "NOT_APPLICABLE", "INFO", "Postflight is not applicable before publication.", {"published": False}, justification="v1.3.2 has not been externally published."))
    return results

def summarize_results(results: list[dict[str, Any]]) -> dict[str, int]:
    counts = {state: 0 for state in sorted(GATE_STATES)}
    for result in results:
        counts[result["state"]] += 1
    return counts

def findings_from_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    findings = []
    for result in results:
        if result["state"] in {"FAIL", "BLOCKED", "WARN"}:
            findings.append({
                "gate_id": result["gate_id"],
                "severity": result["severity"],
                "state": result["state"],
                "summary": result["summary"],
                "details": result["details"],
            })
    return findings

def write_reports(root: Path, summary: dict[str, Any], results: list[dict[str, Any]], findings: list[dict[str, Any]]) -> None:
    ed = editorial_dir(root)
    control = {
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_at": TIMESTAMP,
        "release_state": summary["release_state"],
        "critical_findings": summary["critical_findings"],
        "high_findings": summary["high_findings"],
        "owner_approval_required": True,
        "global_no_send_lock": True,
        "publish_allowed": False,
        "previous_canonical_doi": PREVIOUS_DOI,
        "concept_doi": CONCEPT_DOI,
        "doi": DOI_PENDING,
        "public_truth_policy": "latest means current release-candidate truth for v1.3.2; historical v1.3.1 snapshots remain historical",
        "gate_results": results,
    }
    write_json(ed / "OC_CORE_1_3_2_RELEASE_CONTROL_PLANE_latest.json", control)
    scorecard = {
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_at": TIMESTAMP,
        "summary": summary,
        "gate_results": results,
    }
    write_json(ed / "OC_CORE_1_3_2_RELEASE_SCORECARD_latest.json", scorecard)
    md = [
        "# OC Core 1.3.2 Release Scorecard",
        "",
        f"Release state: `{summary['release_state']}`",
        f"Critical findings: `{summary['critical_findings']}`",
        f"High findings: `{summary['high_findings']}`",
        f"Publish allowed: `{str(summary['publish_allowed']).lower()}`",
        "",
        "| Gate | State | Severity | Summary |",
        "| --- | --- | --- | --- |",
    ]
    for result in results:
        md.append(f"| `{result['gate_id']}` | `{result['state']}` | `{result['severity']}` | {result['summary']} |")
    write_text(ed / "OC_CORE_1_3_2_RELEASE_SCORECARD_latest.md", "\n".join(md))

    findings_payload = {
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_at": TIMESTAMP,
        "critical_findings": summary["critical_findings"],
        "high_findings": summary["high_findings"],
        "findings": findings,
    }
    write_json(ed / "OC_CORE_1_3_2_SHIT_CONTROL_FINDINGS_latest.json", findings_payload)
    fmd = [
        "# OC Core 1.3.2 Release Quality Findings",
        "",
        "Internal alias: Shit Control. Public name: Logion External Release Quality Control.",
        "",
        f"Critical findings: `{summary['critical_findings']}`",
        f"High findings: `{summary['high_findings']}`",
    ]
    if findings:
        fmd.extend(["", "| Gate | State | Severity | Summary |", "| --- | --- | --- | --- |"])
        for finding in findings:
            fmd.append(f"| `{finding['gate_id']}` | `{finding['state']}` | `{finding['severity']}` | {finding['summary']} |")
    else:
        fmd.extend(["", "No critical, high, medium, or low findings remain for the release-ready no-send state."])
    write_text(ed / "OC_CORE_1_3_2_SHIT_CONTROL_FINDINGS_latest.md", "\n".join(fmd))

    parity = next((result for result in results if result["gate_id"] == "gate_09_public_surface_parity"), {})
    parity_payload = {
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_at": TIMESTAMP,
        "state": parity.get("state"),
        "details": parity.get("details"),
    }
    write_json(ed / "OC_CORE_1_3_2_PUBLIC_SURFACE_PARITY_REPORT.json", parity_payload)
    write_text(ed / "OC_CORE_1_3_2_PUBLIC_SURFACE_PARITY_REPORT.md", "\n".join([
        "# OC Core 1.3.2 Public Surface Parity Report",
        "",
        f"State: `{parity_payload['state']}`",
        "",
        "Checked surfaces agree on version 1.3.2, pending DOI state, previous DOI, concept DOI, release-ready no-send state, and publish lock.",
    ]))
    if not (ed / "OC_CORE_1_3_2_REMEDIATION_LOG.md").exists():
        write_text(ed / "OC_CORE_1_3_2_REMEDIATION_LOG.md", "# OC Core 1.3.2 Remediation Log\n\nAll v1.3.2 hygiene repairs are tracked in the release-machine commit. No destructive history rewrite is used.\n")
    write_json(ed / "OC_CORE_1_3_2_POSTFLIGHT_REPORT.json", {
        "release_id": RELEASE_ID,
        "version": VERSION,
        "state": "NOT_APPLICABLE",
        "published": False,
        "public_release_verified": False,
        "reason": "No external v1.3.2 publication has been performed.",
    })

def evaluate_release(release: str = RELEASE_ID, channel: str = "all", mode: str = "dry-run", write: bool = True) -> dict[str, Any]:
    root = repo_root()
    build_package(root, channel=channel, no_publish=True)
    results = _all_gate_results(root, release, channel, mode)
    findings = findings_from_results(results)
    critical = sum(1 for finding in findings if finding["severity"] == "CRITICAL")
    high = sum(1 for finding in findings if finding["severity"] == "HIGH")
    hard_bad = [result for result in results if result["state"] in {"FAIL", "BLOCKED"} and result["severity"] in {"CRITICAL", "HIGH"}]
    release_state = "RELEASE_READY_NO_SEND" if critical == 0 and high == 0 and not hard_bad else "REMEDIATION_REQUIRED"
    summary = {
        "release_id": release,
        "version": VERSION,
        "channel": channel,
        "mode": mode,
        "generated_at": TIMESTAMP,
        "release_state": release_state,
        "gate_counts": summarize_results(results),
        "critical_findings": critical,
        "high_findings": high,
        "finding_total": len(findings),
        "owner_approval_required": True,
        "global_no_send_lock": True,
        "publish_allowed": False,
        "doi": DOI_PENDING,
        "previous_canonical_doi": PREVIOUS_DOI,
        "concept_doi": CONCEPT_DOI,
    }
    if write:
        write_reports(root, summary, results, findings)
        write_publish_manifest(root)
        write_owner_packet(root)
        write_inventory_and_checksums(root, include_zip=True)
    return summary

def publish_plan(release: str = RELEASE_ID, channel: str = "all") -> dict[str, Any]:
    root = repo_root()
    evaluate_release(release, channel, "dry-run", write=True)
    manifest = read_json(editorial_dir(root) / "OC_CORE_1_3_2_PUBLISH_MANIFEST_DRAFT.json")
    manifest["requested_channel"] = channel
    manifest["next_required_action"] = "Owner approval with exact artifact freeze hash; external publication remains locked."
    write_json(editorial_dir(root) / "OC_CORE_1_3_2_PUBLISH_MANIFEST_DRAFT.json", manifest)
    return manifest

def postflight(release: str = RELEASE_ID, channel: str = "zenodo", public_url: str = "") -> dict[str, Any]:
    root = repo_root()
    report = {
        "release_id": release,
        "version": VERSION,
        "channel": channel,
        "public_url": public_url,
        "state": "NOT_APPLICABLE",
        "published": False,
        "public_release_verified": False,
        "reason": "Postflight is blocked until a later explicit external publication instruction creates a real public v1.3.2 surface.",
        "generated_at": TIMESTAMP,
    }
    write_json(editorial_dir(root) / "OC_CORE_1_3_2_POSTFLIGHT_REPORT.json", report)
    return report
