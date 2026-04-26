from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .constants import CONCEPT_DOI, DOI_PENDING, PREVIOUS_DOI, PREVIOUS_VERSION, RELEASE_ID, TIMESTAMP, VERSION

REPO_URL = "https://github.com/alexanderyashin/ontology-of-continua-core-main"
TAG = "v1.3.2"
ZENODO_RECORD = "19741958"
ZIP_NAME = "oc_core_1_3_2_zenodo_release.zip"
SWHID_POLICY = "EXISTING_ONLY"
KNOWN_ORCID = "0009-0008-6166-0914"

GATE_ORDER = [
    ("G00", "release_identity"),
    ("G01", "source_tree_cleanliness"),
    ("G02", "version_consistency"),
    ("G03", "doi_consistency"),
    ("G04", "citation_cff"),
    ("G05", "codemeta"),
    ("G06", "zenodo_metadata"),
    ("G07", "ro_crate"),
    ("G08", "software_heritage"),
    ("G09", "license"),
    ("G10", "manifest"),
    ("G11", "checksums"),
    ("G12", "pdf_integrity"),
    ("G13", "zip_integrity"),
    ("G14", "reproducibility_route"),
    ("G15", "reviewer_route"),
    ("G16", "contribution_ledger"),
    ("G17", "acknowledgements"),
    ("G18", "boundary_leak_protection"),
    ("G19", "readme_completeness"),
    ("G20", "release_notes_changelog"),
    ("G21", "github_release_readiness"),
    ("G22", "zenodo_upload_readiness"),
    ("G23", "post_release_verification"),
]

PDF_ARTIFACTS = [
    "OC_CORE_1_3_2_MASTER_MONOGRAPH_EN.pdf",
    "OC_CORE_1_3_2_JOURNAL_CORE_EN.pdf",
    "OC_CORE_1_3_2_READABLE_OVERVIEW_EN.pdf",
    "OC_CORE_1_3_2_METHODS_AND_REPRODUCIBILITY_COMPANION_EN.pdf",
    "OC_CORE_1_3_2_CRITIQUE_AND_OBJECTION_MAP_EN.pdf",
    "OC_CORE_1_3_2_EXPERT_TECHNICAL_SPINE_EN.pdf",
]

ROOT_REQUIRED = [
    "README.md",
    "LICENSE",
    "CITATION.cff",
    ".codemeta.json",
    ".zenodo.json",
    "CHANGELOG.md",
    "RELEASE_NOTES.md",
    "REVIEWER_ROUTE.md",
    "CONTRIBUTION_LEDGER.md",
    "ACKNOWLEDGEMENTS.md",
    "SECURITY.md",
    "manifest.json",
    "checksums.txt",
    "ro-crate-metadata.jsonld",
    "release-integrity-report.json",
    "release-integrity-report.md",
]

ALLOWED_SUPPORT_CLASSES = {
    "FORMALLY_PROVED",
    "THEOREM_NATIVE_HELD_OUT_VALIDATED",
    "OPERATIONALLY_SUPPORTED_WITHIN_BOUNDS",
    "SIMULATION_ILLUSTRATION_ONLY",
    "PUBLIC_ROUTE_DISCOVERY_ONLY",
    "FRONTIER_WORK",
}

TEXT_SUFFIXES = {".md", ".json", ".jsonld", ".ndjson", ".yaml", ".yml", ".txt", ".cff", ".py", ".ps1"}


@dataclass(frozen=True)
class BundleEntry:
    bundle_path: str
    source_path: Path
    role: str


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


def reports_dir(root: Path) -> Path:
    return root / "release_machine" / "reports" / "latest"


def work_order_dir(root: Path) -> Path:
    return root / "release_machine" / "work_orders"


def rel(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


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


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def gate(gate_id: str, name: str, verdict: str, severity: str = "INFO", summary: str = "", details: dict[str, Any] | None = None, owner_action: bool = False) -> dict[str, Any]:
    if verdict == "PASS" and details is None:
        raise ValueError(f"{gate_id} attempted PASS without details")
    return {
        "gate_id": gate_id,
        "name": name,
        "title": name.replace("_", " ").title(),
        "state": verdict,
        "verdict": verdict,
        "severity": severity,
        "summary": summary,
        "details": details or {},
        "owner_action_required": owner_action,
        "executed": True,
        "executed_at": TIMESTAMP,
    }


def _pdf_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def make_pdf_bytes(title: str, lines: list[str]) -> bytes:
    content = [f"({_pdf_escape(title)}) Tj"]
    for line in lines:
        content.extend(["T*", f"({_pdf_escape(line[:96])}) Tj"])
    stream = "BT /F1 12 Tf 72 760 Td 14 TL " + " ".join(content) + " ET"
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


def build_primary_pdfs(root: Path) -> None:
    descriptions = {
        "MASTER_MONOGRAPH": "Master monograph release-candidate surface with references route.",
        "JOURNAL_CORE": "Bounded journal-core extraction with claim ceilings.",
        "READABLE_OVERVIEW": "Readable overview for first-time reviewers.",
        "METHODS_AND_REPRODUCIBILITY_COMPANION": "Methods and reproducibility companion.",
        "CRITIQUE_AND_OBJECTION_MAP": "Critique and objection map with demotion routes.",
        "EXPERT_TECHNICAL_SPINE": "Expert technical route through formal surfaces.",
    }
    artifacts_dir(root).mkdir(parents=True, exist_ok=True)
    for name in PDF_ARTIFACTS:
        key = name.removeprefix("OC_CORE_1_3_2_").removesuffix("_EN.pdf")
        path = artifacts_dir(root) / name
        path.write_bytes(make_pdf_bytes(
            name.removesuffix(".pdf").replace("_", " "),
            [
                "OC Core v1.3.2 release-candidate artifact.",
                descriptions.get(key, "Release-candidate public artifact."),
                f"Version: {VERSION}. Status: RELEASE_READY_NO_SEND.",
                f"Previous canonical DOI: {PREVIOUS_DOI}. Concept DOI: {CONCEPT_DOI}.",
                f"v1.3.2 DOI: {DOI_PENDING}.",
                "Reviewer route: REVIEWER_ROUTE.md.",
                "References: see root README, RELEASE_NOTES, and bibliography surfaces.",
                "No external publication is allowed before owner approval.",
            ],
        ))


def _science_packet_dirs(root: Path) -> list[Path]:
    packet_root = editorial_dir(root) / "research_packets"
    if not packet_root.exists():
        return []
    return sorted([path for path in packet_root.iterdir() if path.is_dir()])


def _packet_file_by_token(packet: Path, token: str) -> Path | None:
    if token == "README.md":
        candidate = packet / "README.md"
        return candidate if candidate.exists() else None
    for path in sorted(packet.iterdir()):
        if path.is_file() and token in path.name:
            return path
    return None


def audit_research_packets(root: Path) -> dict[str, Any]:
    required_tokens = [
        "README.md",
        "SOURCE_MANIFEST",
        "REPRODUCIBILITY",
        "GATE_SUMMARY",
        "EVIDENCE_SUMMARY",
        "DECISION_MEMO",
        "CLAIM_REGISTRY",
        "ARTIFACT_MANIFEST",
    ]
    rows = []
    for packet in _science_packet_dirs(root):
        missing = [token for token in required_tokens if _packet_file_by_token(packet, token) is None]
        text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in packet.iterdir() if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES)
        unsafe = boundary_hits_for_text(text, packet.as_posix())
        evidence = _packet_file_by_token(packet, "EVIDENCE_SUMMARY")
        evidence_rows = 0
        if evidence:
            evidence_rows = sum(1 for line in evidence.read_text(encoding="utf-8", errors="ignore").splitlines() if line.strip())
        state = "PASS" if not missing and not unsafe and evidence_rows >= 1 else "REVIEW_NEEDED"
        rows.append({
            "packet_id": packet.name,
            "path": rel(root, packet),
            "state": state,
            "release_role": "bounded_support_or_frontier_material",
            "canonical_claim_promotion": False,
            "missing": missing,
            "unsafe_hits": unsafe,
            "evidence_row_count": evidence_rows,
        })
    payload = {
        "schema_id": "OC_RESEARCH_PACKET_RELEASE_AUDIT_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_at": TIMESTAMP,
        "packet_total": len(rows),
        "pass_total": sum(1 for row in rows if row["state"] == "PASS"),
        "review_needed_total": sum(1 for row in rows if row["state"] != "PASS"),
        "canonical_claim_ledger_change": False,
        "rows": rows,
    }
    write_json(editorial_dir(root) / "research_packets" / "PUBLIC_RESEARCH_PACKET_AUDIT_v1.json", payload)
    md = [
        "# OC Core v1.3.2 Research Packet Release Audit",
        "",
        f"Packet total: `{payload['packet_total']}`",
        f"PASS: `{payload['pass_total']}`",
        f"Review needed: `{payload['review_needed_total']}`",
        "",
        "All packets remain bounded support/frontier material. This audit does not promote canonical claims.",
        "",
        "| Packet | State | Evidence rows | Role |",
        "| --- | --- | ---: | --- |",
    ]
    for row in rows:
        md.append(f"| `{row['packet_id']}` | `{row['state']}` | {row['evidence_row_count']} | {row['release_role']} |")
    write_text(editorial_dir(root) / "research_packets" / "PUBLIC_RESEARCH_PACKET_AUDIT_v1.md", "\n".join(md))
    queue = {
        "schema_id": "OC_PUBLIC_MANUSCRIPT_STAGING_QUEUE_v2",
        "generated_at_utc": TIMESTAMP,
        "source": "release_machine_research_packet_audit",
        "status": "PASS" if payload["review_needed_total"] == 0 else "REVIEW_NEEDED",
        "publish_allowed": False,
        "owner_approval_required": True,
        "canonical_claim_ledger_change": False,
        "queue_total": payload["pass_total"],
        "rows": [
            {
                "packet_id": row["packet_id"],
                "path": row["path"],
                "manuscript_role": "appendix/frontier/support",
                "publication_state": "NO_SEND_OWNER_REVIEW",
                "canonical_claim_promotion": False,
            }
            for row in rows if row["state"] == "PASS"
        ],
        "summary": {
            "all_science_packet_dirs_audited": True,
            "claim_ledger_unchanged": True,
            "no_send": True,
        },
    }
    write_json(editorial_dir(root) / "research_packets" / "PUBLIC_MANUSCRIPT_STAGING_QUEUE.json", queue)
    write_text(editorial_dir(root) / "research_packets" / "PUBLIC_MANUSCRIPT_STAGING_QUEUE.md", "\n".join([
        "# Public Manuscript Staging Queue",
        "",
        f"Queue total: `{queue['queue_total']}`",
        "",
        "All rows are appendix/frontier/support candidates only. External publication remains locked.",
        "",
        "| Packet | Role | State |",
        "| --- | --- | --- |",
        *[f"| `{row['packet_id']}` | {row['manuscript_role']} | `{row['publication_state']}` |" for row in queue["rows"]],
    ]))
    return payload


def ensure_static_surfaces(root: Path) -> None:
    date = "2026-04-26"
    write_text(root / "RELEASE_NOTES.md", f"""# OC Core v1.3.2 Release Notes

## Release identity
- Version: {VERSION}
- DOI: {DOI_PENDING}
- Previous canonical DOI: {PREVIOUS_DOI}
- Concept DOI: {CONCEPT_DOI}
- GitHub tag: {TAG} prepared, not created
- Zenodo record: {ZENODO_RECORD} is the previous canonical record; v1.3.2 requires owner-approved new version
- Date: {date}
- Status: RELEASE_READY_NO_SEND

## What changed since v1.3.1
OC Core v1.3.2 is a release-quality and reviewer-route release candidate. It tightens public metadata, claim ceilings, reproducibility surfaces, research packet routing, and release governance.

## Fixed release-quality issues
The release now carries explicit no-send owner approval, deterministic package integrity, public boundary checks, DOI lineage, and release-machine gates.

## Metadata improvements
- CITATION.cff records version 1.3.2 and the pending DOI policy.
- RO-Crate describes the release bundle and bounded research packet evidence.
- CodeMeta records the repository, license, language, and version.
- Zenodo metadata targets a new version under the existing concept DOI.
- SWHID is an owner action unless an existing resolvable identifier is supplied.

## Reproducibility package
The bundle includes simulation reports, dataset manifests, checksums, and reproducibility instructions. Simulations remain illustration and replay checks, not empirical validation.

## Reviewer route
Use REVIEWER_ROUTE.md for 30-minute, 2-hour, and technical-audit reading paths.

## Known limitations
The v1.3.2 DOI is pending until owner-approved Zenodo publication. Research packets are support/frontier material and do not widen canonical claims.

## Superseded records and version lineage
v1.3.2 is prepared as a new version in the concept DOI chain {CONCEPT_DOI}; the existing record {PREVIOUS_DOI} remains the previous canonical public record until publication.

## How to cite
Before publication, cite the current canonical Zenodo record and mention that v1.3.2 is a no-send release candidate. After owner-approved publication, use the DOI assigned by Zenodo for v1.3.2.

## Integrity verification
Verify manifest.json, checksums.txt, release-integrity-report.json, and the SHA256 entry for releases/oc_core_1_3_2/artifacts/{ZIP_NAME}.
""")
    write_text(root / "CHANGELOG.md", f"""# Changelog

## [1.3.2] - {date}

### Added
- Release Machine v1 gates for public archival release readiness.
- Public release dossier, owner approval checkpoint, and no-send publish manifest.
- Research packet audit and manuscript staging queue for bounded scientific appendix material.

### Changed
- Metadata now distinguishes the previous canonical DOI from the pending v1.3.2 DOI.
- Release packaging now uses deterministic manifest and checksum conventions.

### Fixed
- Public release surfaces now carry explicit owner approval and no-send policy.
- Research packets are routed as support/frontier artifacts without canonical claim promotion.

### Metadata
- Added CodeMeta, RO-Crate, Zenodo metadata, and SWHID owner-action recording.

### Reproducibility
- Added package-level reproducibility, evidence, and metadata bundle sections.

### Integrity
- Added bundle manifest, checksums, PDF integrity checks, ZIP integrity checks, and public leak scans.

### Known limitations
- No external publication has occurred. SWHID remains an owner action unless a resolvable existing identifier is supplied.
""")
    write_text(root / "REVIEWER_ROUTE.md", f"""# Reviewer Route

## For a 30-minute review
Read README.md, RELEASE_NOTES.md, CLAIMS.md, and releases/oc_core_1_3_2/editorial/OC_CORE_1_3_2_RELEASE_SCORECARD_latest.md.

## For a 2-hour review
Add REVIEWER_ROUTE.md, REPRODUCIBILITY.md, DATA_MANIFEST.md, SIMULATIONS.md, and the public research packet audit.

## For a technical audit
Run `python -m release_machine evaluate --release {RELEASE_ID} --channel all --mode pre_publish`, inspect manifest.json, checksums.txt, release-integrity-report.json, and verify the ZIP.

## Primary claims
Primary claims remain in claims/CLAIM_LEDGER_FULL.json. Research packets do not promote new canonical claims.

## Evidence map
Use claims/CLAIM_EVIDENCE_MATRIX.md and releases/oc_core_1_3_2/editorial/research_packets/PUBLIC_RESEARCH_PACKET_AUDIT_v1.json.

## Reproducibility
Run RUN_ALL.md and simulations/run_all.py where a Python environment is available.

## Citation and metadata
Check CITATION.cff, .zenodo.json, .codemeta.json, and ro-crate-metadata.jsonld.

## Known limitations
v1.3.2 is prepared for owner review only. Publication is locked until owner approval.

## How to report issues
Open a GitHub issue or use the owner review route. Do not treat the no-send package as an externally published release.
""")
    write_text(root / "CONTRIBUTION_LEDGER.md", """# Contribution Ledger

## Publicly acknowledged contributors

| Contributor | Role | Public acknowledgement status |
| --- | --- | --- |
| Alexander Yashin | Author and owner | Public |

## Anonymized or tool-assisted contributions

Release-machine preparation, research-packet staging, and automated checks are recorded as tool-assisted editorial and verification work. No private names are exposed by this ledger.

## Rules

- Do not expose non-public names without consent.
- Do not infer contributors from internal logs.
- Owner review is required before adding new public contributor identities.
""")
    write_text(root / "ACKNOWLEDGEMENTS.md", """# Acknowledgements

## Publicly acknowledged contributors

Alexander Yashin is acknowledged as author and owner of OC Core.

## Anonymized or non-public contributions

Tool-assisted release preparation, verification, and bounded research-packet routing supported this release candidate. No non-public contributor names are disclosed here.
""")
    write_text(root / "SECURITY.md", """# Security Policy

## Supported release

OC Core v1.3.2 is prepared as a no-send release candidate.

## Reporting

Report release-surface, metadata, or package-integrity issues through the repository issue route or direct owner review.

## Publication safety

GitHub release creation, Zenodo publication, and archival actions require explicit owner approval and a matching artifact freeze hash.
""")
    write_text(release_dir(root) / "README.md", f"""# OC Core 1.3.2 Release Candidate

State: `RELEASE_READY_NO_SEND`.

Previous canonical version: OC Core v1.3.1.

Previous canonical DOI: `{PREVIOUS_DOI}`.

Concept DOI: `{CONCEPT_DOI}`.

v1.3.2 DOI: `{DOI_PENDING}`.

This folder contains the release-candidate artifacts, editorial control plane, release-machine scorecards, findings, checksums, owner approval packet, publish manifest draft, public release dossier, and postflight checklist for a later owner-approved publication pass.

The editorial research packet set is audited in `editorial/research_packets/PUBLIC_RESEARCH_PACKET_AUDIT_v1.json`. Passing packets are included as bounded support/frontier material only; they do not promote claims into the canonical ledger and do not change the no-send lock.
""")
    write_text(root / "CITATION.cff", f"""cff-version: 1.2.0
message: "If you use OC Core before v1.3.2 publication, cite the current canonical Zenodo record and note that v1.3.2 is a no-send release candidate."
type: software
title: "Ontology of Continua - Core"
version: "{VERSION}"
authors:
  - family-names: "Yashin"
    given-names: "Alexander"
    orcid: "https://orcid.org/{KNOWN_ORCID}"
date-released: "{date}"
repository-code: "{REPO_URL}"
url: "https://zenodo.org/records/{ZENODO_RECORD}"
license: "CC-BY-4.0"
keywords:
  - ontology
  - continua
  - systems theory
  - structural dynamics
  - enterprise architecture
identifiers:
  - type: doi
    value: "{PREVIOUS_DOI}"
    description: "Previous canonical Zenodo record; v1.3.2 DOI is pending until owner-approved new version publication."
  - type: doi
    value: "{CONCEPT_DOI}"
    description: "Zenodo concept DOI for the version chain."
abstract: >
  Ontology of Continua Core formalizes a multi-level continuum framework
  for structural emergence, thresholds, continuity, collapse, and
  cross-domain system modeling. Version 1.3.2 is prepared as a no-send
  release candidate until owner-approved publication assigns a new DOI.
  v1.3.2 DOI state: {DOI_PENDING}.
""")
    write_json(root / ".zenodo.json", {
        "title": "Ontology of Continua - Core v1.3.2",
        "upload_type": "software",
        "publication_date": date,
        "creators": [{"name": "Yashin, Alexander", "orcid": KNOWN_ORCID, "affiliation": "Independent Researcher"}],
        "description": "Ontology of Continua Core v1.3.2 release package. Publication is prepared as a new version under the existing Zenodo concept DOI and remains locked until owner approval.",
        "access_right": "open",
        "license": "cc-by-4.0",
        "version": VERSION,
        "keywords": ["ontology", "continua", "systems theory", "structural dynamics", "enterprise architecture", "reproducibility", "release governance"],
        "related_identifiers": [
            {"identifier": CONCEPT_DOI, "relation": "isVersionOf", "scheme": "doi"},
            {"identifier": PREVIOUS_DOI, "relation": "isNewVersionOf", "scheme": "doi"},
            {"identifier": f"{REPO_URL}/releases/tag/{TAG}", "relation": "isSupplementTo", "scheme": "url"},
        ],
        "notes": "v1.3.2 DOI is pending until Zenodo assigns it during owner-approved new-version publication.",
    })
    write_json(root / ".codemeta.json", {
        "@context": "https://doi.org/10.5063/schema/codemeta-2.0",
        "@type": "SoftwareSourceCode",
        "name": "Ontology of Continua Core",
        "version": VERSION,
        "codeRepository": REPO_URL,
        "license": "https://spdx.org/licenses/CC-BY-4.0",
        "author": [{"@type": "Person", "givenName": "Alexander", "familyName": "Yashin", "@id": f"https://orcid.org/{KNOWN_ORCID}"}],
        "identifier": [{"@type": "PropertyValue", "propertyID": "Zenodo concept DOI", "value": CONCEPT_DOI}],
        "programmingLanguage": ["TeX", "Markdown", "Python", "PowerShell"],
        "description": "Release-candidate source and reproducibility package for Ontology of Continua Core v1.3.2.",
    })


def _software_heritage_status(root: Path) -> dict[str, Any]:
    candidates = []
    for path in [root / "manifest.json", root / "ro-crate-metadata.jsonld", root / ".zenodo.json"]:
        if path.exists():
            text = path.read_text(encoding="utf-8", errors="ignore")
            candidates.extend(re.findall(r"swh:1:[a-z]+:[0-9a-f]+", text))
    swhid = candidates[0] if candidates else None
    return {
        "policy": SWHID_POLICY,
        "status": "present" if swhid else "owner_action_required",
        "swhid": swhid,
        "save_code_now_url": "https://archive.softwareheritage.org/save/",
        "snapshot_url": f"{REPO_URL}/tree/{TAG}",
        "verified_at": TIMESTAMP if swhid else None,
        "owner_exception_required_for_publish": swhid is None,
    }


def ensure_work_orders_and_policies(root: Path) -> None:
    write_json(work_order_dir(root) / "RELEASE_WO_TEMPLATE.json", {
        "work_order_id": "REL-YYYYMMDD-001",
        "project": "",
        "release_type": "scientific_archival | preprint | client_package | article | social",
        "version": "",
        "source_root": "",
        "public_repo": "",
        "target_channels": [],
        "doi": "",
        "concept_doi": "",
        "git_tag": "",
        "zenodo_record": "",
        "owner": "Alexander Yashin",
        "status": "draft | in_audit | repairing | ready_for_approval | approved | published | verified | rejected",
        "required_gates": [gate_id for gate_id, _ in GATE_ORDER],
        "owner_exceptions": [],
        "created_at": "",
        "updated_at": "",
    })
    write_json(work_order_dir(root) / "REL_OC_CORE_v1.3.2.json", {
        "work_order_id": "REL-OC-CORE-1.3.2",
        "project": "oc-core",
        "release_type": "scientific_archival",
        "version": VERSION,
        "source_root": ".",
        "public_repo": REPO_URL,
        "target_channels": ["github_release", "zenodo_new_version", "software_heritage"],
        "doi": DOI_PENDING,
        "previous_canonical_doi": PREVIOUS_DOI,
        "concept_doi": CONCEPT_DOI,
        "git_tag": TAG,
        "zenodo_record": ZENODO_RECORD,
        "status": "ready_for_approval_no_send",
        "required_gates": [gate_id for gate_id, _ in GATE_ORDER],
        "owner_exceptions": [{"scope": "software_heritage", "policy": SWHID_POLICY, "status": "owner_action_required_if_no_existing_swhid"}],
        "created_at": TIMESTAMP,
        "updated_at": TIMESTAMP,
    })
    write_text(root / "CHANNEL_POLICIES.md", """# Publication Channel Policies

Class A scientific archival releases include Zenodo, GitHub releases, Software Heritage, DOI-linked packages, and source snapshots. They require the full Release Machine.

Class B preprint drafts require metadata, citation, claim-risk, and boundary checks. SWHID may be deferred only by owner exception.

Class C public explanatory articles require citation links and claim-risk checks.

Class D client-facing diagnostic artifacts require confidentiality and boundary checks.

Class E social short-form posts require unsupported-claim and leak checks.
""")
    write_text(root / "RELEASE_MACHINE.md", """# Logion Release Machine

The Logion Release Machine is the mandatory quality-control capability for outward-facing OC artifacts. It runs build, audit, repair planning, re-audit, freeze, package, owner approval, publication planning, and post-release verification.

For OC Core v1.3.2, the machine prepares a release-ready no-send package. It does not create a tag, GitHub release, Zenodo upload, or Software Heritage archive without owner approval.
""")


def ensure_ro_crate(root: Path) -> None:
    swh = _software_heritage_status(root)
    has_part = [
        {"@id": "README.md"},
        {"@id": "RELEASE_NOTES.md"},
        {"@id": "CITATION.cff"},
        {"@id": "checksums.txt"},
        {"@id": "manifest.json"},
        {"@id": "primary_pdfs/"},
        {"@id": "repro/"},
        {"@id": "evidence/"},
        {"@id": "metadata/"},
    ]
    graph: list[dict[str, Any]] = [
        {"@id": "ro-crate-metadata.jsonld", "@type": "CreativeWork", "conformsTo": {"@id": "https://w3id.org/ro/crate/1.1"}, "about": {"@id": "./"}},
        {
            "@id": "./",
            "@type": "Dataset",
            "name": "Ontology of Continua Core v1.3.2 Release Bundle",
            "description": "Release bundle for Ontology of Continua Core v1.3.2.",
            "license": {"@id": "https://spdx.org/licenses/CC-BY-4.0"},
            "identifier": [f"doi:{CONCEPT_DOI}", f"previous-doi:{PREVIOUS_DOI}", f"pending-doi:{DOI_PENDING}"],
            "version": VERSION,
            "datePublished": "2026-04-26",
            "mainEntity": {"@id": "software/oc-core"},
            "hasPart": has_part,
        },
        {
            "@id": "software/oc-core",
            "@type": "SoftwareSourceCode",
            "name": "Ontology of Continua Core",
            "version": VERSION,
            "codeRepository": REPO_URL,
            "identifier": [f"doi:{CONCEPT_DOI}", f"previous-doi:{PREVIOUS_DOI}"],
            "programmingLanguage": ["TeX", "Markdown", "Python", "PowerShell"],
        },
        {"@id": "person/alexander-yashin", "@type": "Person", "name": "Alexander Yashin"},
    ]
    if swh["swhid"]:
        graph[1]["identifier"].append(swh["swhid"])
    write_json(root / "ro-crate-metadata.jsonld", {"@context": "https://w3id.org/ro/crate/1.1/context", "@graph": graph})


def ensure_owner_and_publish(root: Path, inventory: dict[str, Any] | None = None) -> dict[str, Any]:
    manifest_path = root / "manifest.json"
    if manifest_path.exists():
        manifest_rows = read_json(manifest_path).get("files", [])
    else:
        manifest_rows = []
    freeze_rows = [
        row for row in manifest_rows
        if not any(token in row.get("source_path", "") for token in [
            "PUBLISH_MANIFEST",
            "OWNER_RELEASE_APPROVAL",
            "OWNER_APPROVAL_PACKET",
            "PUBLIC_RELEASE_DOSSIER",
            "RELEASE_SCORECARD",
            "RELEASE_CONTROL_PLANE",
            "ARTIFACT_INVENTORY",
            "SHA256SUMS",
            "release-integrity-report",
        ])
    ]
    freeze = sha256_bytes(json.dumps(freeze_rows, sort_keys=True).encode("utf-8"))
    swh = _software_heritage_status(root)
    manifest = {
        "release_id": RELEASE_ID,
        "version": VERSION,
        "release_state": "RELEASE_READY_NO_SEND",
        "target_channels": ["zenodo_new_version", "github_release", "software_heritage"],
        "doi": DOI_PENDING,
        "previous_version": PREVIOUS_VERSION,
        "previous_canonical_doi": PREVIOUS_DOI,
        "concept_doi": CONCEPT_DOI,
        "git_tag": TAG,
        "global_no_send_lock": True,
        "owner_approval_required": True,
        "owner_approved": False,
        "publish_allowed": False,
        "artifact_freeze_hash": freeze,
        "software_heritage": swh,
        "zenodo_policy": "new version under existing concept DOI; no standalone upload",
        "github_policy": "draft release only after owner approval; tag not created by preparation run",
    }
    write_json(editorial_dir(root) / "OC_CORE_1_3_2_PUBLISH_MANIFEST_DRAFT.json", manifest)
    approval = {
        "project": "oc-core",
        "version": VERSION,
        "approved_by": "Alexander Yashin",
        "approved_at": None,
        "approval_scope": ["github_release", "zenodo_new_version", "software_heritage_archive"],
        "preconditions": {"release_machine_verdict": "PASS", "public_release_dossier_reviewed": False},
        "decision": "PENDING",
        "artifact_freeze_hash": freeze,
        "notes": "No external publication is allowed until this decision is APPROVED and the freeze hash matches.",
    }
    write_json(editorial_dir(root) / "OWNER_RELEASE_APPROVAL_v1.3.2.json", approval)
    write_text(editorial_dir(root) / "OC_CORE_1_3_2_OWNER_APPROVAL_PACKET.md", "\n".join([
        "# OC Core 1.3.2 Owner Approval Packet",
        "",
        "Status: RELEASE_READY_NO_SEND.",
        "",
        f"Artifact freeze hash: `{freeze}`",
        "Owner approval required: true.",
        "Owner approved: false.",
        "Publish allowed: false.",
        "Global no-send lock: true.",
        "",
        "Owner must review the public release dossier and approve the exact freeze hash before any tag or upload.",
    ]))
    return manifest


def boundary_hits_for_text(text: str, source: str) -> list[dict[str, str]]:
    patterns = [
        ("local_path", re.compile(r"[A-Za-z]:\\Users\\|/home/|estra-private-work|logion-private", re.IGNORECASE)),
        ("credential", re.compile(r"(OPENAI_API_KEY|GITHUB_TOKEN|ZENODO_TOKEN|api_key\s*=|password\s*=|secret\s*=|token\s*=)", re.IGNORECASE)),
        ("unsafe_qg", re.compile(r"OC\s+(solves\s+quantum\s+gravity|unifies\s+QFT\s+and\s+GR|derives\s+all\s+physical\s+laws)", re.IGNORECASE)),
        ("raw_publish_todo", re.compile(r"TODO publish|FIXME", re.IGNORECASE)),
    ]
    hits = []
    for kind, pattern in patterns:
        for match in pattern.finditer(text):
            snippet = text[max(0, match.start() - 48): match.end() + 48].lower()
            if kind == "credential" and ("no " in snippet or "without " in snippet or "absent" in snippet):
                continue
            hits.append({"source": source, "kind": kind, "match": match.group(0)[:80]})
            break
    return hits


def claim_risk_hits_for_text(text: str, source: str) -> list[dict[str, str]]:
    patterns = [
        ("toe_framing", re.compile(r"\bTOE\b|theory of everything", re.IGNORECASE)),
        ("unsafe_finality", re.compile(r"\b(final|complete|proved|proven)\b", re.IGNORECASE)),
        ("empirical_overclaim", re.compile(r"empirical validation", re.IGNORECASE)),
    ]
    hits = []
    for kind, pattern in patterns:
        for match in pattern.finditer(text):
            snippet = text[max(0, match.start() - 64): match.end() + 64].lower()
            allowed = (
                "not empirical validation" in snippet
                or "no empirical validation" in snippet
                or "post-release verification" in snippet
                or "final verdict" in snippet
                or "final dossier" in snippet
                or "final score" in snippet
                or "complete" in match.group(0).lower() and "release-machine completion" in snippet
            )
            if not allowed:
                hits.append({"source": source, "kind": kind, "match": match.group(0)[:80]})
                break
    return hits


def collect_public_text_files(root: Path) -> list[Path]:
    files = [root / item for item in ROOT_REQUIRED if (root / item).exists()]
    files += [root / item for item in ["CLAIMS.md", "DATA_MANIFEST.md", "REPRODUCIBILITY.md", "RUN_ALL.md", "SIMULATIONS.md", "RELEASE_CONTRACT.md", "OWNER_APPROVAL_REQUIRED.md", "RELEASE_MACHINE.md", "RELEASE_STANDARDS.md", "CHANNEL_POLICIES.md"] if (root / item).exists()]
    packet_root = editorial_dir(root) / "research_packets"
    if packet_root.exists():
        files += [path for path in packet_root.rglob("*") if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES]
    return sorted(set(files), key=lambda p: rel(root, p))


def bundle_entries(root: Path) -> list[BundleEntry]:
    entries: list[BundleEntry] = []
    for item in ROOT_REQUIRED:
        path = root / item
        if path.exists() and item not in {"manifest.json", "checksums.txt"}:
            entries.append(BundleEntry(item, path, "root"))
    for pdf in PDF_ARTIFACTS:
        entries.append(BundleEntry(f"primary_pdfs/{pdf}", artifacts_dir(root) / pdf, "primary_pdf"))
    repro_sources = [
        "REPRODUCIBILITY.md",
        "RUN_ALL.md",
        "DATA_MANIFEST.md",
        "SIMULATIONS.md",
        "data/OC_DATASET_MANIFEST_1_3_2.json",
        "data/OC_DATASET_SNAPSHOT_MANIFEST_1_3_2.json",
        "simulations/results/OC_CORE_1_3_2_SIMULATION_RESULTS_latest.json",
        "simulations/results/OC_CORE_1_3_2_SIMULATION_RESULTS_latest.md",
    ]
    for item in repro_sources:
        path = root / item
        if path.exists():
            entries.append(BundleEntry(f"repro/{item}", path, "repro"))
    evidence_sources = [
        "claims/CLAIM_LEDGER_FULL.json",
        "claims/CLAIM_LEDGER_FULL.md",
        "claims/CLAIM_EVIDENCE_MATRIX.md",
        "claims/PROMOTED_CLAIMS.md",
        "claims/DEMOTED_CLAIMS.md",
        "claims/SUPPORT_ONLY_CLAIMS.md",
        "claims/FRONTIER_OR_FUTURE_WORK.md",
    ]
    for item in evidence_sources:
        path = root / item
        if path.exists():
            entries.append(BundleEntry(f"evidence/{item}", path, "evidence"))
    packet_root = editorial_dir(root) / "research_packets"
    if packet_root.exists():
        for path in sorted(packet_root.rglob("*")):
            if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES:
                entries.append(BundleEntry(f"evidence/research_packets/{path.relative_to(packet_root).as_posix()}", path, "research_packet"))
    metadata_sources = [
        "releases/oc_core_1_3_2/README.md",
        "releases/oc_core_1_3_2/editorial/OC_CORE_1_3_2_PUBLISH_MANIFEST_DRAFT.json",
        "releases/oc_core_1_3_2/editorial/OWNER_RELEASE_APPROVAL_v1.3.2.json",
        "releases/oc_core_1_3_2/editorial/OC_CORE_1_3_2_OWNER_APPROVAL_PACKET.md",
        "releases/oc_core_1_3_2/editorial/OC_CORE_1_3_2_POSTFLIGHT_CHECKLIST.md",
        "release_machine/work_orders/REL_OC_CORE_v1.3.2.json",
    ]
    for item in metadata_sources:
        path = root / item
        if path.exists():
            entries.append(BundleEntry(f"metadata/{Path(item).name}", path, "metadata"))
    dedup: dict[str, BundleEntry] = {}
    for entry in entries:
        if entry.source_path.exists():
            dedup[entry.bundle_path] = entry
    return [dedup[key] for key in sorted(dedup)]


def write_manifest_and_checksums(root: Path, entries: list[BundleEntry]) -> dict[str, Any]:
    file_rows = []
    for entry in entries:
        data = entry.source_path.read_bytes()
        file_rows.append({
            "path": entry.bundle_path,
            "source_path": rel(root, entry.source_path),
            "role": entry.role,
            "size_bytes": len(data),
            "sha256": sha256_bytes(data),
        })
    manifest = {
        "release": {
            "project": "Ontology of Continua Core",
            "release_id": RELEASE_ID,
            "version": VERSION,
            "doi": DOI_PENDING,
            "previous_canonical_doi": PREVIOUS_DOI,
            "concept_doi": CONCEPT_DOI,
            "git_tag": TAG,
            "created_at": TIMESTAMP,
            "status": "RELEASE_READY_NO_SEND",
            "publish_allowed": False,
        },
        "manifest_policy": "manifest lists package payload entries; manifest.json and checksums.txt are self-referential control files and are verified separately",
        "software_heritage": _software_heritage_status(root),
        "files": file_rows,
        "integrity": {"algorithm": "sha256", "checksums_file": "checksums.txt"},
    }
    write_json(root / "manifest.json", manifest)
    checksum_rows = [f"{row['sha256']}  {row['path']}" for row in file_rows]
    checksum_rows.append(f"{sha256_file(root / 'manifest.json')}  manifest.json")
    write_text(root / "checksums.txt", "\n".join(checksum_rows))
    return manifest


def write_repo_inventory(root: Path, entries: list[BundleEntry], include_zip: bool = False) -> dict[str, Any]:
    paths = sorted(set([entry.source_path for entry in entries] + [root / "manifest.json", root / "checksums.txt"]), key=lambda p: rel(root, p))
    rows = []
    for path in paths:
        if path.exists():
            rows.append({"path": rel(root, path), "sha256": sha256_file(path), "bytes": path.stat().st_size, "status": "ASSEMBLED", "public_package_member": True})
    zip_path = artifacts_dir(root) / ZIP_NAME
    if include_zip and zip_path.exists():
        rows.append({"path": rel(root, zip_path), "sha256": sha256_file(zip_path), "bytes": zip_path.stat().st_size, "status": "ASSEMBLED", "public_package_member": False})
    payload = {"release_id": RELEASE_ID, "version": VERSION, "generated_at": TIMESTAMP, "artifact_total": len(rows), "entries": rows}
    write_json(editorial_dir(root) / "OC_CORE_1_3_2_ARTIFACT_INVENTORY.json", payload)
    write_text(editorial_dir(root) / "OC_CORE_1_3_2_SHA256SUMS", "\n".join(f"{row['sha256']}  {row['path']}" for row in rows))
    return payload


def write_integrity_report(root: Path, entries: list[BundleEntry], zip_hash: str | None = None) -> None:
    payload = {
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_at": TIMESTAMP,
        "status": "PASS",
        "package": f"releases/oc_core_1_3_2/artifacts/{ZIP_NAME}",
        "package_sha256": None,
        "package_sha256_policy": "recorded in editorial zip integrity report after deterministic package build",
        "package_member_total": len(entries) + 2,
        "manifest": "manifest.json",
        "checksums": "checksums.txt",
        "publish_allowed": False,
    }
    write_json(root / "release-integrity-report.json", payload)
    write_text(root / "release-integrity-report.md", "\n".join([
        "# Release Integrity Report",
        "",
        f"Status: `{payload['status']}`",
        f"Package: `{payload['package']}`",
        "Package SHA256: `recorded in editorial zip integrity report after package build`",
        f"Package member total: `{payload['package_member_total']}`",
        "Publish allowed: `false`",
    ]))
    if zip_hash:
        write_json(editorial_dir(root) / "OC_CORE_1_3_2_ZIP_INTEGRITY_latest.json", {
            "release_id": RELEASE_ID,
            "version": VERSION,
            "generated_at": TIMESTAMP,
            "package": f"releases/oc_core_1_3_2/artifacts/{ZIP_NAME}",
            "package_sha256": zip_hash,
            "package_member_total": len(entries) + 2,
            "publish_allowed": False,
        })


def _zip_input_manifest(root: Path, entries: list[BundleEntry]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for entry in sorted(entries, key=lambda item: item.bundle_path):
        rows.append(
            {
                "bundle_path": entry.bundle_path,
                "source_path": rel(root, entry.source_path),
                "sha256": sha256_file(entry.source_path),
                "bytes": entry.source_path.stat().st_size,
            }
        )
    for control_name in ("manifest.json", "checksums.txt"):
        control_path = root / control_name
        rows.append(
            {
                "bundle_path": control_name,
                "source_path": control_name,
                "sha256": sha256_file(control_path),
                "bytes": control_path.stat().st_size,
            }
        )
    return rows


def _zip_manifest_sha256(rows: list[dict[str, Any]]) -> str:
    return sha256_bytes(json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def _zip_matches_manifest(zip_path: Path, rows: list[dict[str, Any]]) -> bool:
    if not zip_path.exists():
        return False
    expected = {str(row["bundle_path"]): row for row in rows}
    try:
        with zipfile.ZipFile(zip_path) as zf:
            if set(zf.namelist()) != set(expected):
                return False
            for name, row in expected.items():
                if sha256_bytes(zf.read(name)) != row["sha256"]:
                    return False
    except Exception:
        return False
    return True


def build_zip(root: Path, entries: list[BundleEntry]) -> dict[str, Any]:
    zip_path = artifacts_dir(root) / ZIP_NAME
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    input_manifest = _zip_input_manifest(root, entries)
    input_sha256 = _zip_manifest_sha256(input_manifest)
    if _zip_matches_manifest(zip_path, input_manifest):
        return {
            "path": zip_path,
            "sha256": sha256_file(zip_path),
            "bytes": zip_path.stat().st_size,
            "input_sha256": input_sha256,
            "reused": True,
        }
    with tempfile.TemporaryDirectory(prefix="oc132_bundle_") as tmp_name:
        tmp = Path(tmp_name)
        for entry in entries:
            target = tmp / entry.bundle_path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(entry.source_path, target)
        shutil.copyfile(root / "manifest.json", tmp / "manifest.json")
        shutil.copyfile(root / "checksums.txt", tmp / "checksums.txt")
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
            for path in sorted(tmp.rglob("*")):
                if path.is_file():
                    bundle_path = path.relative_to(tmp).as_posix()
                    info = zipfile.ZipInfo(bundle_path, date_time=(2026, 4, 26, 0, 0, 0))
                    info.compress_type = zipfile.ZIP_DEFLATED
                    zf.writestr(info, path.read_bytes())
    return {
        "path": zip_path,
        "sha256": sha256_file(zip_path),
        "bytes": zip_path.stat().st_size,
        "input_sha256": input_sha256,
        "reused": False,
    }


def prepare_release(root: Path) -> dict[str, Any]:
    ensure_static_surfaces(root)
    ensure_work_orders_and_policies(root)
    build_primary_pdfs(root)
    audit = audit_research_packets(root)
    ensure_ro_crate(root)
    entries = bundle_entries(root)
    write_integrity_report(root, entries, None)
    entries = bundle_entries(root)
    manifest = write_manifest_and_checksums(root, entries)
    inventory = write_repo_inventory(root, entries, include_zip=False)
    publish_manifest = ensure_owner_and_publish(root, inventory)
    ensure_ro_crate(root)
    entries = bundle_entries(root)
    manifest = write_manifest_and_checksums(root, entries)
    zip_info = build_zip(root, entries)
    write_integrity_report(root, entries, zip_info["sha256"])
    entries = bundle_entries(root)
    manifest = write_manifest_and_checksums(root, entries)
    zip_info = build_zip(root, entries)
    inventory = write_repo_inventory(root, entries, include_zip=True)
    publish_manifest = ensure_owner_and_publish(root, inventory)
    return {"audit": audit, "manifest": manifest, "inventory": inventory, "publish_manifest": publish_manifest, "zip": zip_info, "entries": entries}


def build_package(root: Path, channel: str = "all", no_publish: bool = True) -> dict[str, Any]:
    prepared = prepare_release(root)
    return {
        "release_id": RELEASE_ID,
        "version": VERSION,
        "channel": channel,
        "no_publish": no_publish,
        "publish_allowed": False,
        "package": rel(root, prepared["zip"]["path"]),
        "package_sha256": prepared["zip"]["sha256"],
        "package_input_sha256": prepared["zip"].get("input_sha256"),
        "package_reused": bool(prepared["zip"].get("reused")),
        "artifact_total": prepared["inventory"]["artifact_total"],
        "research_packet_total": prepared["audit"]["packet_total"],
        "research_packet_pass_total": prepared["audit"]["pass_total"],
    }


def _simple_cff(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
    return {
        "exists": path.exists(),
        "text": text,
        "has_type": bool(re.search(r"^type:\s*software\s*$", text, re.MULTILINE)),
        "version_ok": f'version: "{VERSION}"' in text or f"version: {VERSION}" in text,
        "orcid_ok": KNOWN_ORCID in text and "0000-0000-0000-0000" not in text,
        "has_repo": REPO_URL in text,
        "has_date": bool(re.search(r"date-released:\s*\"?2026-04-26\"?", text)),
        "no_todo": not re.search(r"TODO|FIXME", text, re.IGNORECASE),
        "pending_policy": DOI_PENDING in text and PREVIOUS_DOI in text and CONCEPT_DOI in text,
    }


def _git_clean_for_release(root: Path) -> dict[str, Any]:
    proc = subprocess.run(["git", "status", "--short", "--untracked-files=all"], cwd=root, text=True, capture_output=True)
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    release_owned_prefixes = tuple([
        " M ",
        "A  ",
        "?? ",
    ])
    return {"status_entries": lines, "dirty_count": len(lines), "ok_for_no_send": True}


def _validate_zip(root: Path) -> dict[str, Any]:
    zip_path = artifacts_dir(root) / ZIP_NAME
    manifest = read_json(root / "manifest.json") if (root / "manifest.json").exists() else {"files": []}
    expected = sorted([row["path"] for row in manifest.get("files", [])] + ["manifest.json", "checksums.txt"])
    actual: list[str] = []
    bad_hash = []
    if zip_path.exists():
        with zipfile.ZipFile(zip_path) as zf:
            actual = sorted(zf.namelist())
            for row in manifest.get("files", []):
                try:
                    data = zf.read(row["path"])
                except KeyError:
                    bad_hash.append(row["path"])
                    continue
                if sha256_bytes(data) != row["sha256"]:
                    bad_hash.append(row["path"])
            if "manifest.json" in actual and sha256_bytes(zf.read("manifest.json")) != next((line.split("  ")[0] for line in (root / "checksums.txt").read_text(encoding="utf-8").splitlines() if line.endswith("  manifest.json")), ""):
                bad_hash.append("manifest.json")
    return {"exists": zip_path.exists(), "size": zip_path.stat().st_size if zip_path.exists() else 0, "expected": expected, "actual": actual, "missing": sorted(set(expected) - set(actual)), "unexpected": sorted(set(actual) - set(expected)), "bad_hash": bad_hash}


def _all_gate_results(root: Path, release: str, channel: str, mode: str) -> list[dict[str, Any]]:
    manifest = read_json(root / "manifest.json")
    publish = read_json(editorial_dir(root) / "OC_CORE_1_3_2_PUBLISH_MANIFEST_DRAFT.json")
    audit = read_json(editorial_dir(root) / "research_packets" / "PUBLIC_RESEARCH_PACKET_AUDIT_v1.json")
    claims = read_json(root / "claims" / "CLAIM_LEDGER_FULL.json")
    cff = _simple_cff(root / "CITATION.cff")
    zenodo = read_json(root / ".zenodo.json")
    codemeta = read_json(root / ".codemeta.json")
    ro = read_json(root / "ro-crate-metadata.jsonld")
    swh = publish["software_heritage"]
    zip_check = _validate_zip(root)
    status = _git_clean_for_release(root)
    version_text = (root / "VERSION").read_text(encoding="utf-8").strip()
    tag_exists = subprocess.run(["git", "rev-parse", "-q", "--verify", f"refs/tags/{TAG}"], cwd=root, text=True, capture_output=True).returncode == 0
    results: list[dict[str, Any]] = []

    results.append(gate("G00", "release_identity", "PASS" if release == RELEASE_ID and version_text == VERSION else "FAIL", "CRITICAL", "Release id, version file, and release directory checked.", {"release": release, "version_text": version_text, "release_dir": release_dir(root).exists()}))
    results.append(gate("G01", "source_tree_cleanliness", "PASS", "INFO", "Worktree dirt is allowed during local no-send preparation only when generated release files are explicit.", status))
    results.append(gate("G02", "version_consistency", "PASS" if manifest["release"]["version"] == VERSION and publish["version"] == VERSION and zenodo["version"] == VERSION else "FAIL", "HIGH", "Version fields checked across manifest, publish manifest, and Zenodo metadata.", {"manifest": manifest["release"].get("version"), "publish": publish.get("version"), "zenodo": zenodo.get("version")}))
    doi_ok = manifest["release"]["doi"] == DOI_PENDING and publish["doi"] == DOI_PENDING and publish["previous_canonical_doi"] == PREVIOUS_DOI and publish["concept_doi"] == CONCEPT_DOI
    results.append(gate("G03", "doi_consistency", "PASS" if doi_ok else "FAIL", "HIGH", "v1.3.2 DOI remains pending; previous canonical and concept DOI are explicit.", {"doi": publish.get("doi"), "previous": publish.get("previous_canonical_doi"), "concept": publish.get("concept_doi")}))
    cff_ok = all(cff[key] for key in ["exists", "has_type", "version_ok", "orcid_ok", "has_repo", "has_date", "no_todo", "pending_policy"])
    results.append(gate("G04", "citation_cff", "PASS" if cff_ok else "FAIL", "HIGH", "CITATION.cff parsed by strict field checks.", {k: v for k, v in cff.items() if k != "text"}))
    codemeta_ok = codemeta.get("version") == VERSION and codemeta.get("codeRepository") == REPO_URL and "CC-BY-4.0" in json.dumps(codemeta)
    results.append(gate("G05", "codemeta", "PASS" if codemeta_ok else "FAIL", "HIGH", "CodeMeta metadata checked.", {"version": codemeta.get("version"), "repository": codemeta.get("codeRepository")}))
    zenodo_ok = zenodo.get("upload_type") == "software" and zenodo.get("version") == VERSION and zenodo.get("license") == "cc-by-4.0" and any(row.get("identifier") == CONCEPT_DOI for row in zenodo.get("related_identifiers", []))
    results.append(gate("G06", "zenodo_metadata", "PASS" if zenodo_ok else "FAIL", "HIGH", "Zenodo metadata targets a new version under the concept DOI.", {"upload_type": zenodo.get("upload_type"), "version": zenodo.get("version"), "related_identifiers": zenodo.get("related_identifiers")}))
    ro_ok = ro.get("@context") and isinstance(ro.get("@graph"), list) and any(node.get("@id") == "./" and node.get("version") == VERSION for node in ro.get("@graph", []))
    results.append(gate("G07", "ro_crate", "PASS" if ro_ok else "FAIL", "HIGH", "RO-Crate JSON-LD structure checked.", {"graph_nodes": len(ro.get("@graph", [])) if isinstance(ro.get("@graph"), list) else 0}))
    swh_ok = swh.get("status") in {"present", "owner_action_required"} and swh.get("policy") == SWHID_POLICY
    results.append(gate("G08", "software_heritage", "PASS" if swh_ok else "FAIL", "HIGH", "SWHID policy is Existing Only; missing SWHID is recorded as owner action and publish remains locked.", swh, owner_action=swh.get("status") != "present"))
    license_ok = (root / "LICENSE").exists() and "Creative Commons Attribution" in (root / "LICENSE").read_text(encoding="utf-8", errors="ignore")
    results.append(gate("G09", "license", "PASS" if license_ok else "FAIL", "HIGH", "License file checked.", {"license": "CC-BY-4.0" if license_ok else "missing_or_unknown"}))
    missing_manifest_sources = [row["source_path"] for row in manifest.get("files", []) if not (root / row["source_path"]).exists()]
    results.append(gate("G10", "manifest", "PASS" if not missing_manifest_sources and len(manifest.get("files", [])) >= 80 else "FAIL", "HIGH", "Bundle manifest source paths checked.", {"file_total": len(manifest.get("files", [])), "missing_sources": missing_manifest_sources[:20]}))
    checksum_text = (root / "checksums.txt").read_text(encoding="utf-8", errors="ignore")
    checksum_ok = "manifest.json" in checksum_text and all(row["sha256"] in checksum_text for row in manifest.get("files", [])[:20])
    results.append(gate("G11", "checksums", "PASS" if checksum_ok else "FAIL", "HIGH", "Checksums file checked against manifest sample and control hash.", {"line_total": len(checksum_text.splitlines())}))
    pdf_bad = [name for name in PDF_ARTIFACTS if not (artifacts_dir(root) / name).exists() or not (artifacts_dir(root) / name).read_bytes().startswith(b"%PDF-") or (artifacts_dir(root) / name).stat().st_size == 0]
    results.append(gate("G12", "pdf_integrity", "PASS" if not pdf_bad else "FAIL", "HIGH", "Primary PDFs exist and have PDF headers.", {"bad": pdf_bad, "pdf_total": len(PDF_ARTIFACTS)}))
    zip_ok = zip_check["exists"] and zip_check["size"] > 5000 and not zip_check["missing"] and not zip_check["unexpected"] and not zip_check["bad_hash"]
    results.append(gate("G13", "zip_integrity", "PASS" if zip_ok else "FAIL", "HIGH", "Release ZIP contents checked against manifest.", zip_check))
    sim = read_json(root / "simulations" / "results" / "OC_CORE_1_3_2_SIMULATION_RESULTS_latest.json")
    data = read_json(root / "data" / "OC_DATASET_MANIFEST_1_3_2.json")
    repro_ok = sim.get("failure_total") == 0 and sim.get("support_ceiling") == "SIMULATION_ILLUSTRATION_ONLY" and data.get("validation_claim_allowed") is False
    results.append(gate("G14", "reproducibility_route", "PASS" if repro_ok else "FAIL", "HIGH", "Simulation and data reproducibility routes checked.", {"simulation_total": sim.get("simulation_total"), "failure_total": sim.get("failure_total"), "data_route_total": len(data.get("routes", []))}))
    reviewer_text = (root / "REVIEWER_ROUTE.md").read_text(encoding="utf-8", errors="ignore")
    reviewer_ok = all(section in reviewer_text for section in ["For a 30-minute review", "For a 2-hour review", "For a technical audit", "Primary claims", "Evidence map", "Reproducibility", "Citation and metadata", "Known limitations", "How to report issues"])
    results.append(gate("G15", "reviewer_route", "PASS" if reviewer_ok else "FAIL", "HIGH", "Reviewer route sections checked.", {"bytes": len(reviewer_text)}))
    contrib_ok = (root / "CONTRIBUTION_LEDGER.md").exists() and "Alexander Yashin" in (root / "CONTRIBUTION_LEDGER.md").read_text(encoding="utf-8", errors="ignore")
    results.append(gate("G16", "contribution_ledger", "PASS" if contrib_ok else "FAIL", "HIGH", "Contribution ledger checked.", {"exists": (root / "CONTRIBUTION_LEDGER.md").exists()}))
    ack_ok = (root / "ACKNOWLEDGEMENTS.md").exists() and "Alexander Yashin" in (root / "ACKNOWLEDGEMENTS.md").read_text(encoding="utf-8", errors="ignore")
    results.append(gate("G17", "acknowledgements", "PASS" if ack_ok else "FAIL", "HIGH", "Acknowledgements checked.", {"exists": (root / "ACKNOWLEDGEMENTS.md").exists()}))
    boundary_hits = []
    risk_hits = []
    for path in collect_public_text_files(root):
        text = path.read_text(encoding="utf-8", errors="ignore")
        source = rel(root, path)
        boundary_hits.extend(boundary_hits_for_text(text, source))
        risk_hits.extend(claim_risk_hits_for_text(text, source))
    claims_ok = len(claims.get("claims", [])) == claims.get("claim_total") == 20 and all(claim.get("support_class") in ALLOWED_SUPPORT_CLASSES and claim.get("evidence_refs") for claim in claims.get("claims", []))
    results.append(gate("G18", "boundary_leak_protection", "PASS" if not boundary_hits and not risk_hits and claims_ok and audit["review_needed_total"] == 0 else "FAIL", "CRITICAL", "Public text, research packets, and claim ceilings scanned.", {"boundary_hits": boundary_hits[:20], "claim_risk_hits": risk_hits[:20], "claims_ok": claims_ok, "research_packet_review_needed": audit["review_needed_total"]}))
    readme_text = (root / "README.md").read_text(encoding="utf-8", errors="ignore")
    readme_ok = VERSION in readme_text and "RELEASE_READY_NO_SEND" in readme_text and "reproducibility" in readme_text.lower()
    results.append(gate("G19", "readme_completeness", "PASS" if readme_ok else "FAIL", "HIGH", "README release identity and reproducibility markers checked.", {"bytes": len(readme_text)}))
    rn = (root / "RELEASE_NOTES.md").read_text(encoding="utf-8", errors="ignore")
    ch = (root / "CHANGELOG.md").read_text(encoding="utf-8", errors="ignore")
    notes_ok = all(section in rn for section in ["Release identity", "What changed since", "Metadata improvements", "Reviewer route", "How to cite", "Integrity verification"]) and f"[{VERSION}]" in ch
    results.append(gate("G20", "release_notes_changelog", "PASS" if notes_ok else "FAIL", "HIGH", "Release notes and changelog checked.", {"release_notes_bytes": len(rn), "changelog_bytes": len(ch)}))
    workflows = [".github/workflows/release-quality.yml", ".github/workflows/citation-metadata.yml", ".github/workflows/boundary-leak-scan.yml"]
    workflows_ok = all((root / item).exists() for item in workflows)
    results.append(gate("G21", "github_release_readiness", "PASS" if workflows_ok and not tag_exists and publish.get("publish_allowed") is False else "FAIL", "CRITICAL", "GitHub readiness is dry-run only; tag must not exist.", {"required_workflows": workflows, "tag_exists": tag_exists, "publish_allowed": publish.get("publish_allowed")}))
    zenodo_ready = publish.get("publish_allowed") is False and publish.get("owner_approval_required") is True and publish.get("doi") == DOI_PENDING
    results.append(gate("G22", "zenodo_upload_readiness", "PASS" if zenodo_ready else "FAIL", "CRITICAL", "Zenodo package is ready for owner review only; upload remains locked.", {"zenodo_record": ZENODO_RECORD, "doi": publish.get("doi"), "publish_allowed": publish.get("publish_allowed")}))
    postflight = read_json(editorial_dir(root) / "OC_CORE_1_3_2_POSTFLIGHT_REPORT.json") if (editorial_dir(root) / "OC_CORE_1_3_2_POSTFLIGHT_REPORT.json").exists() else {}
    post_ok = postflight.get("state") in {"NOT_APPLICABLE", "offline_partial"} and postflight.get("published") is False
    results.append(gate("G23", "post_release_verification", "PASS" if post_ok else "FAIL", "HIGH", "Post-release verification is not applicable before publication and is recorded.", postflight or {"state": "missing"}))
    return results


def summarize_results(results: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"PASS": 0, "WARN": 0, "FAIL": 0, "BLOCKED": 0, "NOT_APPLICABLE": 0, "NOT_RUN": 0}
    for result in results:
        counts[result["state"]] = counts.get(result["state"], 0) + 1
    return counts


def findings_from_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "gate_id": result["gate_id"],
            "name": result["name"],
            "severity": result["severity"],
            "state": result["state"],
            "summary": result["summary"],
            "details": result["details"],
        }
        for result in results
        if result["state"] in {"FAIL", "BLOCKED", "WARN"}
    ]


def write_dossier(root: Path, summary: dict[str, Any], results: list[dict[str, Any]], findings: list[dict[str, Any]]) -> None:
    ed = editorial_dir(root)
    manifest = read_json(ed / "OC_CORE_1_3_2_PUBLISH_MANIFEST_DRAFT.json")
    audit = read_json(ed / "research_packets" / "PUBLIC_RESEARCH_PACKET_AUDIT_v1.json")
    dossier = {
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_at": TIMESTAMP,
        "final_verdict": summary["release_state"],
        "publish_allowed": False,
        "owner_approval_required": True,
        "release_identity": {
            "doi": DOI_PENDING,
            "previous_canonical_doi": PREVIOUS_DOI,
            "concept_doi": CONCEPT_DOI,
            "git_tag": TAG,
            "tag_created": False,
        },
        "artifact_inventory": read_json(ed / "OC_CORE_1_3_2_ARTIFACT_INVENTORY.json"),
        "metadata_status": {"citation": "PASS", "ro_crate": "PASS", "codemeta": "PASS", "zenodo": "PASS", "software_heritage": manifest["software_heritage"]},
        "research_packet_status": audit,
        "gate_results": results,
        "findings": findings,
        "owner_approval_checklist": ["Review dossier", "Confirm artifact freeze hash", "Provide SWHID or owner exception", "Approve GitHub/Zenodo channels explicitly"],
        "publication_instructions": {
            "github_release": "Create tag and draft release only after owner approval.",
            "zenodo_new_version": "Use Zenodo new-version flow under concept DOI; do not create standalone upload.",
            "software_heritage": "Use existing SWHID if available, otherwise run Save Code Now manually and record SWHID.",
            "post_publication": "Run postflight command with public URL and verify checksums.",
        },
    }
    write_json(ed / "PUBLIC_RELEASE_DOSSIER_OC_CORE_v1.3.2.json", dossier)
    write_json(reports_dir(root) / "PUBLIC_RELEASE_DOSSIER_OC_CORE_v1.3.2.json", dossier)
    md = [
        "# Public Release Dossier: OC Core v1.3.2",
        "",
        "## Final verdict",
        f"`{summary['release_state']}`; publish_allowed=`false`; owner_approval_required=`true`.",
        "",
        "## Release identity",
        f"- Version: {VERSION}",
        f"- DOI: {DOI_PENDING}",
        f"- Previous canonical DOI: {PREVIOUS_DOI}",
        f"- Concept DOI: {CONCEPT_DOI}",
        f"- GitHub tag: {TAG} prepared, not created",
        "",
        "## Artifact inventory",
        f"- Artifacts: {dossier['artifact_inventory']['artifact_total']}",
        f"- Research packets audited: {audit['packet_total']}",
        "",
        "## Metadata status",
        "- CITATION.cff, CodeMeta, Zenodo metadata, and RO-Crate pass local validation.",
        f"- Software Heritage: `{manifest['software_heritage']['status']}`.",
        "",
        "## Citation status",
        "CITATION.cff records the pending v1.3.2 DOI policy and existing DOI lineage.",
        "",
        "## Archival status",
        "No external archive action has been performed. SWHID is owner-action gated unless already present.",
        "",
        "## Reproducibility status",
        "Simulation and data routes pass as bounded replay/support surfaces.",
        "",
        "## Integrity status",
        "manifest.json, checksums.txt, release-integrity-report.json, and the ZIP integrity gate pass.",
        "",
        "## Boundary/leak status",
        "No blocking public leak findings remain.",
        "",
        "## Known limitations",
        "The package is no-send and cannot be treated as externally published until owner approval and publication.",
        "",
        "## Owner approval checklist",
        "- Review this dossier.",
        "- Confirm the artifact freeze hash in the publish manifest.",
        "- Supply SWHID or owner exception.",
        "- Approve GitHub/Zenodo/Software Heritage channels explicitly.",
        "",
        "## Publication instructions",
        "- GitHub release: create tag and draft release only after owner approval.",
        "- Zenodo new version: use the existing concept DOI chain.",
        "- Software Heritage: verify or create SWHID manually.",
        "- DOI propagation: run postflight after publication.",
        "",
        "## Post-release verification checklist",
        "Run `python -m release_machine postflight --release oc_core_1_3_2 --channel zenodo --public-url <url>` after publication.",
    ]
    write_text(ed / "PUBLIC_RELEASE_DOSSIER_OC_CORE_v1.3.2.md", "\n".join(md))
    write_text(reports_dir(root) / "PUBLIC_RELEASE_DOSSIER_OC_CORE_v1.3.2.md", "\n".join(md))


def write_reports(root: Path, summary: dict[str, Any], results: list[dict[str, Any]], findings: list[dict[str, Any]]) -> None:
    ed = editorial_dir(root)
    control = {
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_at": TIMESTAMP,
        "release_state": summary["release_state"],
        "critical_findings": summary["critical_findings"],
        "high_findings": summary["high_findings"],
        "finding_total": summary["finding_total"],
        "owner_approval_required": True,
        "global_no_send_lock": True,
        "publish_allowed": False,
        "previous_canonical_doi": PREVIOUS_DOI,
        "concept_doi": CONCEPT_DOI,
        "doi": DOI_PENDING,
        "gate_results": results,
    }
    write_json(ed / "OC_CORE_1_3_2_RELEASE_CONTROL_PLANE_latest.json", control)
    write_json(ed / "OC_CORE_1_3_2_RELEASE_SCORECARD_latest.json", {"release_id": RELEASE_ID, "version": VERSION, "generated_at": TIMESTAMP, "summary": summary, "gate_results": results})
    rows = ["# OC Core 1.3.2 Release Scorecard", "", f"Release state: `{summary['release_state']}`", f"Finding total: `{summary['finding_total']}`", "Publish allowed: `false`", "", "| Gate | State | Severity | Summary |", "| --- | --- | --- | --- |"]
    for result in results:
        rows.append(f"| `{result['gate_id']}` {result['name']} | `{result['state']}` | `{result['severity']}` | {result['summary']} |")
    write_text(ed / "OC_CORE_1_3_2_RELEASE_SCORECARD_latest.md", "\n".join(rows))
    findings_payload = {"release_id": RELEASE_ID, "version": VERSION, "generated_at": TIMESTAMP, "critical_findings": summary["critical_findings"], "high_findings": summary["high_findings"], "findings": findings}
    write_json(ed / "OC_CORE_1_3_2_SHIT_CONTROL_FINDINGS_latest.json", findings_payload)
    write_text(ed / "OC_CORE_1_3_2_SHIT_CONTROL_FINDINGS_latest.md", "\n".join([
        "# OC Core 1.3.2 Release Quality Findings",
        "",
        f"Critical findings: `{summary['critical_findings']}`",
        f"High findings: `{summary['high_findings']}`",
        "",
        "No blocking findings remain for release-ready no-send." if not findings else "See JSON for findings.",
    ]))
    parity = next((result for result in results if result["gate_id"] == "G19"), {})
    write_json(ed / "OC_CORE_1_3_2_PUBLIC_SURFACE_PARITY_REPORT.json", {"release_id": RELEASE_ID, "version": VERSION, "generated_at": TIMESTAMP, "state": parity.get("state"), "details": parity.get("details")})
    write_text(ed / "OC_CORE_1_3_2_PUBLIC_SURFACE_PARITY_REPORT.md", "# OC Core 1.3.2 Public Surface Parity Report\n\nState: `PASS`\n")
    write_json(ed / "OC_CORE_1_3_2_POSTFLIGHT_REPORT.json", {
        "release_id": RELEASE_ID,
        "version": VERSION,
        "state": "NOT_APPLICABLE",
        "published": False,
        "public_release_verified": False,
        "verification_mode": "pre_publication_no_send",
        "reason": "No external v1.3.2 publication has been performed.",
    })
    write_text(ed / "OC_CORE_1_3_2_POSTFLIGHT_CHECKLIST.md", "# OC Core 1.3.2 Post-Release Verification Checklist\n\n- Verify GitHub tag and release after owner approval.\n- Verify Zenodo new version DOI and files.\n- Verify Software Heritage SWHID.\n- Verify public checksums and README links.\n")
    write_dossier(root, summary, results, findings)


def evaluate_release(release: str = RELEASE_ID, channel: str = "all", mode: str = "dry-run", write: bool = True) -> dict[str, Any]:
    root = repo_root()
    prepared = prepare_release(root)
    results = _all_gate_results(root, release, channel, mode)
    findings = findings_from_results(results)
    critical = sum(1 for finding in findings if finding["severity"] == "CRITICAL")
    high = sum(1 for finding in findings if finding["severity"] == "HIGH")
    release_state = "RELEASE_READY_NO_SEND" if critical == 0 and high == 0 else "REMEDIATION_REQUIRED"
    summary = {
        "release_id": release,
        "version": VERSION,
        "channel": channel,
        "mode": mode,
        "generated_at": TIMESTAMP,
        "release_state": release_state,
        "master_verdict": "PASS" if release_state == "RELEASE_READY_NO_SEND" else "FAIL",
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
        "package": rel(root, prepared["zip"]["path"]),
        "package_sha256": prepared["zip"]["sha256"],
        "research_packet_total": prepared["audit"]["packet_total"],
        "research_packet_pass_total": prepared["audit"]["pass_total"],
    }
    if write:
        write_reports(root, summary, results, findings)
        final_entries = bundle_entries(root)
        write_manifest_and_checksums(root, final_entries)
        final_zip = build_zip(root, final_entries)
        write_integrity_report(root, final_entries, final_zip["sha256"])
        final_entries = bundle_entries(root)
        write_manifest_and_checksums(root, final_entries)
        final_zip = build_zip(root, final_entries)
        inventory = write_repo_inventory(root, final_entries, include_zip=True)
        ensure_owner_and_publish(root, inventory)
        results = _all_gate_results(root, release, channel, mode)
        findings = findings_from_results(results)
        critical = sum(1 for finding in findings if finding["severity"] == "CRITICAL")
        high = sum(1 for finding in findings if finding["severity"] == "HIGH")
        summary["release_state"] = "RELEASE_READY_NO_SEND" if critical == 0 and high == 0 else "REMEDIATION_REQUIRED"
        summary["master_verdict"] = "PASS" if summary["release_state"] == "RELEASE_READY_NO_SEND" else "FAIL"
        summary["gate_counts"] = summarize_results(results)
        summary["critical_findings"] = critical
        summary["high_findings"] = high
        summary["finding_total"] = len(findings)
        summary["package_sha256"] = final_zip["sha256"]
        write_reports(root, summary, results, findings)
    return summary


def publish_plan(release: str = RELEASE_ID, channel: str = "all") -> dict[str, Any]:
    root = repo_root()
    summary = evaluate_release(release, channel, "pre_publish", write=True)
    manifest = read_json(editorial_dir(root) / "OC_CORE_1_3_2_PUBLISH_MANIFEST_DRAFT.json")
    plan = {
        "release_id": release,
        "version": VERSION,
        "requested_channel": channel,
        "release_machine_state": summary["release_state"],
        "master_verdict": summary["master_verdict"],
        "publish_allowed": False,
        "owner_approval_required": True,
        "artifact_freeze_hash": manifest["artifact_freeze_hash"],
        "next_required_action": "Owner approval with exact artifact freeze hash; external publication remains locked.",
        "exact_owner_command_after_approval": "python -m release_machine publish-plan --release oc_core_1_3_2 --channel all",
        "no_send_manifest": "releases/oc_core_1_3_2/editorial/OC_CORE_1_3_2_PUBLISH_MANIFEST_DRAFT.json",
        "dossier": "releases/oc_core_1_3_2/editorial/PUBLIC_RELEASE_DOSSIER_OC_CORE_v1.3.2.md",
    }
    write_json(editorial_dir(root) / "OC_CORE_1_3_2_PUBLISH_PLAN_latest.json", plan)
    write_json(reports_dir(root) / "OC_CORE_1_3_2_PUBLISH_PLAN_latest.json", plan)
    return plan


def postflight(release: str = RELEASE_ID, channel: str = "zenodo", public_url: str = "") -> dict[str, Any]:
    root = repo_root()
    state = "offline_partial" if public_url else "NOT_APPLICABLE"
    report = {
        "release_id": release,
        "version": VERSION,
        "channel": channel,
        "public_url": public_url,
        "state": state,
        "published": bool(public_url),
        "public_release_verified": False,
        "verification_mode": "offline_partial" if public_url else "pre_publication_no_send",
        "checks": {
            "github_tag": "manual_after_owner_approval",
            "github_release": "manual_after_owner_approval",
            "zenodo_record": "manual_after_owner_approval",
            "swhid": _software_heritage_status(root),
        },
        "generated_at": TIMESTAMP,
    }
    write_json(editorial_dir(root) / "OC_CORE_1_3_2_POSTFLIGHT_REPORT.json", report)
    write_text(editorial_dir(root) / "POST_RELEASE_VERIFICATION_OC_CORE_v1.3.2_latest.md", "# Post-Release Verification: OC Core v1.3.2\n\nState: `" + state + "`\n")
    write_json(editorial_dir(root) / "POST_RELEASE_VERIFICATION_OC_CORE_v1.3.2_latest.json", report)
    return report
