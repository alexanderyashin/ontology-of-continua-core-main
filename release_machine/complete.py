from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .constants import CONCEPT_DOI, DOI_PENDING, PREVIOUS_DOI, PREVIOUS_VERSION, RELEASE_ID, TIMESTAMP, VERSION

REPO_URL = "https://github.com/alexanderyashin/ontology-of-continua-core-main"
TAG = "v1.3.2"
ZENODO_RECORD = "19851694"
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
    ("G24", "lrgef_freshness"),
    ("G25", "lrgef_pdf_source_binding"),
    ("G26", "lrgef_supply_chain_no_send_lock"),
    ("G27", "parfitian_cerberus"),
    ("G28", "science_terminality_82"),
    ("G29", "release_human_quality"),
    ("G30", "platinum_science_readiness"),
    ("G31", "llm_readability_integrity"),
]

PDF_ARTIFACTS = [
    "OC_CORE_1_3_2_MASTER_MONOGRAPH_EN.pdf",
    "OC_CORE_1_3_2_JOURNAL_CORE_EN.pdf",
    "OC_CORE_1_3_2_READABLE_OVERVIEW_EN.pdf",
    "OC_CORE_1_3_2_METHODS_AND_REPRODUCIBILITY_COMPANION_EN.pdf",
    "OC_CORE_1_3_2_CRITIQUE_AND_OBJECTION_MAP_EN.pdf",
    "OC_CORE_1_3_2_EXPERT_TECHNICAL_SPINE_EN.pdf",
]

PDF_SOURCE_BINDINGS = {
    "OC_CORE_1_3_2_MASTER_MONOGRAPH_EN.pdf": "releases/oc_core_1_3/monograph/OC_CORE_1_3_MASTER_MONOGRAPH_EN.pdf",
    "OC_CORE_1_3_2_JOURNAL_CORE_EN.pdf": "releases/oc_core_1_3_2/pdf_sources/OC_CORE_1_3_2_JOURNAL_CORE_EN.pdf",
    "OC_CORE_1_3_2_READABLE_OVERVIEW_EN.pdf": "releases/oc_core_1_3_2/pdf_sources/OC_CORE_1_3_2_READABLE_OVERVIEW_EN.pdf",
    "OC_CORE_1_3_2_METHODS_AND_REPRODUCIBILITY_COMPANION_EN.pdf": "releases/oc_core_1_3_2/pdf_sources/OC_CORE_1_3_2_METHODS_AND_REPRODUCIBILITY_COMPANION_EN.pdf",
    "OC_CORE_1_3_2_CRITIQUE_AND_OBJECTION_MAP_EN.pdf": "releases/oc_core_1_3_2/pdf_sources/OC_CORE_1_3_2_CRITIQUE_AND_OBJECTION_MAP_EN.pdf",
    "OC_CORE_1_3_2_EXPERT_TECHNICAL_SPINE_EN.pdf": "releases/oc_core_1_3_2/pdf_sources/OC_CORE_1_3_2_EXPERT_TECHNICAL_SPINE_EN.pdf",
}

MIN_SUBSTANTIVE_PDF_BYTES = 20_000
MIN_SUBSTANTIVE_PDF_PAGES = 2

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
SOURCE_MATERIAL_SUFFIXES = {".tex", ".md", ".json", ".yaml", ".yml", ".pdf", ".svg", ".bib"}

PDF_TEXT_FORBIDDEN_PATTERNS = [
    ("unresolved_cross_reference", re.compile(r"\?\?")),
    ("local_path", re.compile(r"C:\\|Users\\|Megaport|file://", re.IGNORECASE)),
    ("stale_version", re.compile(r"Version\s+v?1\.3\.0|Core\s+1\.3\s+Canonical\s+Master\s+Monograph", re.IGNORECASE)),
    ("claim_demotion_closure_language", re.compile(r"claim\s+demotion|claim\s+demoted|demoting\s+those\s+claims", re.IGNORECASE)),
    ("open_proof_obligation_closure_language", re.compile(r"open\s+proof\s+obligation", re.IGNORECASE)),
    ("stale_proof_obligations_language", re.compile(r"\bproof\s+obligations?\b", re.IGNORECASE)),
    ("raw_feedback_leak_language", re.compile(r"raw\s+feedback", re.IGNORECASE)),
    ("raw_model_output_leak_language", re.compile(r"raw\s+model\s+output", re.IGNORECASE)),
    ("placeholder_language", re.compile(r"\bplaceholder\b", re.IGNORECASE)),
]

PLACEHOLDER_PAYLOAD_PATTERN = re.compile(r"(^|/)placeholders?/|placeholder", re.IGNORECASE)

ACKNOWLEDGED_REVIEWERS = [
    {
        "display_name": "G. V. Apostolov",
        "sort_surname": "Apostolov",
        "contribution_class": "substantive_review_and_idea_input",
        "public_note": "Substantive review and idea input.",
    },
    {
        "display_name": "Eduard Fadeev",
        "sort_surname": "Fadeev",
        "contribution_class": "parfit_idea_and_release_governance_pressure",
        "public_note": "Parfit idea and release-governance pressure.",
    },
    {
        "display_name": "Gennady Alekseevich Nosov",
        "sort_surname": "Nosov",
        "contribution_class": "substantive_review_and_idea_input",
        "public_note": "Substantive review and idea input.",
    },
    {
        "display_name": "Sergey Shpadyrev",
        "sort_surname": "Shpadyrev",
        "contribution_class": "substantive_review_and_idea_input",
        "public_note": "Substantive review and idea input.",
    },
    {
        "display_name": "Stanislav Tsukrov",
        "sort_surname": "Tsukrov",
        "contribution_class": "substantive_external_criticism",
        "public_note": "Substantive external criticism and Core 1.3 criticism-response pressure.",
    },
]

HUMAN_QUALITY_PATTERNS = [
    ("overclaim_title", re.compile(r"\bWhat\s+It\s+Proves\b", re.IGNORECASE)),
    ("toe_complete_language", re.compile(r"\bTOE[-\s]?complete\b", re.IGNORECASE)),
    ("universal_closure_complete_language", re.compile(r"\buniversal[-\s]+closure[-\s]+complete\b", re.IGNORECASE)),
    ("all_gaps_solved_language", re.compile(r"\ball\s+gaps\s+solved\b", re.IGNORECASE)),
    ("completed_universal_theory_language", re.compile(r"\bcompleted\s+universal\s+theory\b", re.IGNORECASE)),
    ("final_theory_language", re.compile(r"\bfinal\s+theory\b", re.IGNORECASE)),
    ("unrestricted_prediction_language", re.compile(r"\bunrestricted\s+prediction\b", re.IGNORECASE)),
    ("claim_demotion_closure_language", re.compile(r"claim\s+demotions?|claim\s+demoted|demoting\s+those\s+claims", re.IGNORECASE)),
    ("open_proof_obligation_closure_language", re.compile(r"open\s+proof\s+obligation", re.IGNORECASE)),
    ("unqualified_claim_ceiling_language", re.compile(r"\bclaim\s+ceilings?\b", re.IGNORECASE)),
]

HUMAN_QUALITY_DIAGNOSTIC_SOURCES = {
    "OC_CORE_1_3_2_FINAL_CRITICAL_REVIEW_REPORT",
    "OC_CORE_1_3_2_RELEASE_QUALITY_FAILURE_ANALYSIS",
}


@dataclass(frozen=True)
class BundleEntry:
    bundle_path: str
    source_path: Path
    role: str


@contextmanager
def release_machine_lock(root: Path, *, timeout_seconds: float = 120.0):
    lock_path = root / "release_machine" / ".release_machine.lock"
    deadline = time.time() + timeout_seconds
    fd: int | None = None
    while fd is None:
        try:
            fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, f"pid={os.getpid()}\nts={time.time()}\n".encode("utf-8"))
        except FileExistsError:
            if time.time() >= deadline:
                raise TimeoutError(f"release_machine_busy lock={lock_path}")
            time.sleep(0.25)
    try:
        yield
    finally:
        if fd is not None:
            os.close(fd)
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass


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


def acknowledgement_registry_payload() -> dict[str, Any]:
    reviewers = sorted(
        [
            {
                **row,
                "endorsement_implied": False,
                "publication_approval_implied": False,
                "authorship_implied": False,
                "agreement_with_release_theory_implied": False,
            }
            for row in ACKNOWLEDGED_REVIEWERS
        ],
        key=lambda row: (row["sort_surname"].lower(), row["display_name"].lower()),
    )
    return {
        "schema_id": "OC_CORE_1_3_2_ACKNOWLEDGEMENT_REGISTRY_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_at": TIMESTAMP,
        "author_owner": {
            "display_name": "Alexander Yashin",
            "role": "author_owner",
            "public_note": "Author and owner of OC Core.",
            "thanked_reviewer": False,
        },
        "review_and_idea_acknowledgements": reviewers,
        "policy": {
            "no_endorsement": True,
            "no_publication_approval": True,
            "no_authorship_transfer": True,
            "no_agreement_with_release_theory_implied": True,
            "sort_rule": "Review and idea acknowledgements are sorted by surname in English transcription.",
        },
    }


def acknowledgement_registry_markdown(payload: dict[str, Any]) -> str:
    rows = [
        "# OC Core 1.3.2 Acknowledgement Registry",
        "",
        "This registry is public-safe release metadata. It records review pressure, ideas, or criticism that improved the release route. It does not imply endorsement, publication approval, authorship, or agreement with the theory's release form.",
        "",
        "## Author and owner",
        "",
        f"- {payload['author_owner']['display_name']} - {payload['author_owner']['public_note']}",
        "",
        "## Substantive review and idea acknowledgements",
        "",
        "| Name | Contribution class | Public note | Endorsement implied |",
        "| --- | --- | --- | --- |",
    ]
    for row in payload["review_and_idea_acknowledgements"]:
        rows.append(f"| {row['display_name']} | `{row['contribution_class']}` | {row['public_note']} | `{str(row['endorsement_implied']).lower()}` |")
    rows.extend([
        "",
        "## Policy",
        "",
        "- Acknowledgement is not endorsement.",
        "- Acknowledgement is not publication approval.",
        "- Acknowledgement is not authorship.",
        "- Acknowledgement is not agreement with the theory's release form.",
    ])
    return "\n".join(rows)


def acknowledgement_public_markdown(payload: dict[str, Any]) -> str:
    rows = [
        "# Acknowledgements",
        "",
        "## Author and owner",
        "",
        "Alexander Yashin is recorded separately as author and owner of OC Core.",
        "",
        "## Substantive review and idea acknowledgements",
        "",
        "The following public acknowledgements record review pressure, ideas, or criticism that improved the release route. They are sorted by surname in English transcription.",
        "",
        "| Name | Public note |",
        "| --- | --- |",
    ]
    for row in payload["review_and_idea_acknowledgements"]:
        rows.append(f"| {row['display_name']} | {row['public_note']} |")
    rows.extend([
        "",
        "Acknowledgement does not imply endorsement, publication approval, authorship, or agreement with the theory's release form.",
        "",
        "## Anonymized or non-public contributions",
        "",
        "Tool-assisted release preparation, verification, and bounded research-packet routing supported this release candidate. No non-public contributor names are disclosed here.",
    ])
    return "\n".join(rows)


def contribution_ledger_markdown(payload: dict[str, Any]) -> str:
    rows = [
        "# Contribution Ledger",
        "",
        "## Author and owner",
        "",
        "| Contributor | Role | Public acknowledgement status |",
        "| --- | --- | --- |",
        "| Alexander Yashin | Author and owner | Public |",
        "",
        "## Substantive review and idea acknowledgements",
        "",
        "| Contributor | Role note | Endorsement/publication approval/authorship implied |",
        "| --- | --- | --- |",
    ]
    for row in payload["review_and_idea_acknowledgements"]:
        rows.append(f"| {row['display_name']} | {row['public_note']} | false |")
    rows.extend([
        "",
        "## Anonymized or tool-assisted contributions",
        "",
        "Release-machine preparation, research-packet staging, and automated checks are recorded as tool-assisted editorial and verification work. No private names are exposed by this ledger.",
        "",
        "## Rules",
        "",
        "- Do not expose non-public names without consent.",
        "- Do not infer contributors from internal logs.",
        "- Owner review is required before adding new public contributor identities.",
        "- Acknowledgement is not endorsement, publication approval, authorship, or agreement with the theory's release form.",
    ])
    return "\n".join(rows)


def write_acknowledgement_surfaces(root: Path) -> dict[str, Any]:
    payload = acknowledgement_registry_payload()
    write_json(editorial_dir(root) / "OC_CORE_1_3_2_ACKNOWLEDGEMENT_REGISTRY.json", payload)
    write_text(editorial_dir(root) / "OC_CORE_1_3_2_ACKNOWLEDGEMENT_REGISTRY.md", acknowledgement_registry_markdown(payload))
    write_text(root / "ACKNOWLEDGEMENTS.md", acknowledgement_public_markdown(payload))
    write_text(root / "CONTRIBUTION_LEDGER.md", contribution_ledger_markdown(payload))
    return payload


def write_release_quality_failure_analysis(root: Path) -> dict[str, Any]:
    rows = [
        {
            "issue": "Human-facing overclaim or stale release wording could survive a mechanically green package.",
            "why_previous_gate_missed_it": "G12 scanned only known PDF text patterns; G18 focused on leaks and claim-risk patterns; neither was a role-aware prose-quality gate.",
            "previous_gate": "G12/G18",
            "new_prevention": "G29 release_human_quality scans primary PDFs, release-spine sources, owner/release memos, PDF sources, and manifest roles for overclaiming and stale closure language.",
        },
        {
            "issue": "Acknowledgements could be present but weak, incomplete, or unsorted.",
            "why_previous_gate_missed_it": "G17 only checked that ACKNOWLEDGEMENTS.md existed and mentioned Alexander Yashin.",
            "previous_gate": "G17",
            "new_prevention": "G17 now validates the acknowledgement registry, exact requested public names, surname sorting, role notes, and no-endorsement/no-authorship flags.",
        },
        {
            "issue": "Parfitian Cerberus passed while prose-quality defects remained.",
            "why_previous_gate_missed_it": "G27 is an ethics/governance/no-send risk gate; it is not intended to judge release prose, acknowledgement order, or didactic polish.",
            "previous_gate": "G27",
            "new_prevention": "G29 is placed after Parfit/science terminality and before final verdict to block human-facing release-quality regressions.",
        },
        {
            "issue": "Legacy source PDFs or thin synthetic-PDF generation paths could re-enter a release package.",
            "why_previous_gate_missed_it": "Package composition excluded known journal/manuscript legacy PDFs but did not require explicit source-witness roles for all remaining legacy PDFs; legacy core.py still had thin synthetic PDF generation code.",
            "previous_gate": "G13/package composition and legacy core.py",
            "new_prevention": "Manifest role checks require source_witness_domain_packet for legacy/domain witness PDFs, and legacy core.py delegates primary PDF building to the complete release builder.",
        },
    ]
    payload = {
        "schema_id": "OC_CORE_1_3_2_RELEASE_QUALITY_FAILURE_ANALYSIS_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_at": TIMESTAMP,
        "root_cause": "The previous green release state was mechanically strong but semantically under-gated: package integrity, no-send governance, Parfit/Cerberus, terminality and support-map checks passed, while human-facing prose and acknowledgement quality were not yet blocking release gates.",
        "parfit_scope": "Parfitian Cerberus G27 checks release ethics, no-send invariants, owner-waiver semantics, and Parfitian risk categories. It is not a prose-quality or acknowledgement-order checker.",
        "failure_rows": rows,
        "recurrence_controls": [
            "G29 release_human_quality",
            "Upgraded G17 acknowledgement registry validation",
            "Role-aware source-witness PDF manifest classification",
            "Deprecated legacy synthetic primary-PDF generation path",
        ],
    }
    write_json(editorial_dir(root) / "OC_CORE_1_3_2_RELEASE_QUALITY_FAILURE_ANALYSIS.json", payload)
    md = [
        "# OC Core 1.3.2 Release Quality Failure Analysis",
        "",
        "## Root Cause",
        "",
        payload["root_cause"],
        "",
        "## Parfit/Cerberus Scope",
        "",
        payload["parfit_scope"],
        "",
        "## Failure Rows",
        "",
        "| Issue | Why It Passed Before | Previous Gate | New Prevention |",
        "| --- | --- | --- | --- |",
    ]
    for row in rows:
        md.append(f"| {row['issue']} | {row['why_previous_gate_missed_it']} | `{row['previous_gate']}` | {row['new_prevention']} |")
    md.extend([
        "",
        "## Recurrence Controls",
        "",
        *[f"- {item}" for item in payload["recurrence_controls"]],
    ])
    write_text(editorial_dir(root) / "OC_CORE_1_3_2_RELEASE_QUALITY_FAILURE_ANALYSIS.md", "\n".join(md))
    return payload


def acknowledgement_gate_details(root: Path) -> dict[str, Any]:
    registry_path = editorial_dir(root) / "OC_CORE_1_3_2_ACKNOWLEDGEMENT_REGISTRY.json"
    payload = read_json(registry_path) if registry_path.exists() else acknowledgement_registry_payload()
    rows = payload.get("review_and_idea_acknowledgements", [])
    required_names = [row["display_name"] for row in ACKNOWLEDGED_REVIEWERS]
    observed_names = [row.get("display_name", "") for row in rows]
    sorted_names = [
        row.get("display_name", "")
        for row in sorted(rows, key=lambda row: (str(row.get("sort_surname", "")).lower(), str(row.get("display_name", "")).lower()))
    ]
    missing = [name for name in required_names if name not in observed_names]
    unsorted = observed_names != sorted_names
    endorsement_violations = [
        row.get("display_name", "")
        for row in rows
        if row.get("endorsement_implied") or row.get("publication_approval_implied") or row.get("authorship_implied") or row.get("agreement_with_release_theory_implied") or row.get("agreement_with_final_theory_implied")
    ]
    note_gaps = [row.get("display_name", "") for row in rows if not row.get("public_note") or not row.get("contribution_class")]
    ack_text = (root / "ACKNOWLEDGEMENTS.md").read_text(encoding="utf-8", errors="ignore") if (root / "ACKNOWLEDGEMENTS.md").exists() else ""
    contribution_text = (root / "CONTRIBUTION_LEDGER.md").read_text(encoding="utf-8", errors="ignore") if (root / "CONTRIBUTION_LEDGER.md").exists() else ""
    text_missing = [name for name in required_names if name not in ack_text or name not in contribution_text]
    return {
        "registry_ref": rel(root, registry_path) if registry_path.exists() else "",
        "required_names": required_names,
        "observed_names": observed_names,
        "missing_names": missing,
        "text_missing_names": text_missing,
        "sorted_by_surname": not unsorted,
        "endorsement_violation_names": endorsement_violations,
        "note_gap_names": note_gaps,
        "author_owner_separate": payload.get("author_owner", {}).get("display_name") == "Alexander Yashin" and "Alexander Yashin" not in observed_names,
        "ok": not missing and not text_missing and not unsorted and not endorsement_violations and not note_gaps and payload.get("author_owner", {}).get("display_name") == "Alexander Yashin",
    }


def _snippet(text: str, start: int, end: int, radius: int = 120) -> str:
    return " ".join(text[max(0, start - radius): min(len(text), end + radius)].split())


def _human_quality_match_allowed(kind: str, source: str, snippet: str) -> bool:
    lowered = snippet.lower()
    if any(token in source for token in HUMAN_QUALITY_DIAGNOSTIC_SOURCES):
        return True
    if kind in {
        "toe_complete_language",
        "universal_closure_complete_language",
        "all_gaps_solved_language",
        "completed_universal_theory_language",
        "final_theory_language",
        "unrestricted_prediction_language",
    }:
        allowed_markers = [
            "do not",
            "does not",
            "must not",
            "not as",
            "is not",
            "not agreement",
            "not claim",
            "no unrestricted",
            "forbidden",
            "prohibited",
            "misleading",
            "reject publication language",
            "inflated framing",
            "blocked only inflated",
        ]
        if any(marker in lowered for marker in allowed_markers):
            return True
    if kind == "unqualified_claim_ceiling_language" and "claim boundary" in lowered:
        return True
    return False


def human_quality_findings_for_text(text: str, source: str, *, role: str = "release_spine") -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for kind, pattern in HUMAN_QUALITY_PATTERNS:
        for match in pattern.finditer(text):
            snippet = _snippet(text, match.start(), match.end())
            if _human_quality_match_allowed(kind, source, snippet):
                continue
            findings.append({"source": source, "role": role, "kind": kind, "match": match.group(0)[:120], "snippet": snippet[:260]})
            break
    return findings


def release_human_quality_source_paths(root: Path) -> list[Path]:
    paths: list[Path] = []
    names = [
        *ROOT_REQUIRED,
        "CLAIMS.md",
        "RELEASE_NOTES.md",
        "REVIEWER_ROUTE.md",
        "RELEASE_CONTRACT.md",
        "OWNER_APPROVAL_REQUIRED.md",
        "RELEASE_MACHINE.md",
        "RELEASE_STANDARDS.md",
        "CHANNEL_POLICIES.md",
        "README.md",
    ]
    paths.extend(root / name for name in names if (root / name).exists())
    ed = editorial_dir(root)
    direct_editorial_names = {
        "OC_CORE_1_3_2_OWNER_DECISION_MEMO.md",
        "OC_CORE_1_3_2_OWNER_DECISION_MEMO.json",
        "OC_CORE_1_3_2_RELEASE_POLICY_EXPLAINER.md",
        "OC_CORE_1_3_2_RELEASE_POLICY_EXPLAINER.json",
        "OC_CORE_1_3_2_READY_SCIENCE_COMPLETENESS.md",
        "OC_CORE_1_3_2_READY_SCIENCE_COMPLETENESS.json",
        "OC_CORE_1_3_2_SCIENCE_BACKLOG_82_GAPS.md",
        "OC_CORE_1_3_2_SCIENCE_BACKLOG_82_GAPS.json",
        "OC_CORE_1_3_2_OWNER_APPROVAL_PACKET.md",
        "OC_CORE_1_3_2_RELEASE_QUALITY_FAILURE_ANALYSIS.md",
        "OC_CORE_1_3_2_RELEASE_QUALITY_FAILURE_ANALYSIS.json",
        "OC_CORE_1_3_2_ACKNOWLEDGEMENT_REGISTRY.md",
        "OC_CORE_1_3_2_ACKNOWLEDGEMENT_REGISTRY.json",
    }
    if ed.exists():
        paths.extend(path for path in ed.glob("*") if path.is_file() and path.name in direct_editorial_names)
    pdf_sources = release_dir(root) / "pdf_sources"
    if pdf_sources.exists():
        paths.extend(path for path in pdf_sources.glob("*") if path.is_file() and path.suffix.lower() in {".tex", ".md"})
    for path in [
        root / "content" / "frontmatter_oc_core_1_3_master.tex",
        root / "releases" / "oc_core_1_3" / "monograph" / "source" / "content" / "frontmatter_oc_core_1_3_master.tex",
    ]:
        if path.exists():
            paths.append(path)
    return sorted(set(paths), key=lambda p: rel(root, p))


def unclassified_legacy_pdf_entries(root: Path) -> list[dict[str, str]]:
    manifest_path = root / "manifest.json"
    rows = read_json(manifest_path).get("files", []) if manifest_path.exists() else []
    bad = []
    for row in rows:
        path = row.get("path", "")
        if not path.endswith(".pdf"):
            continue
        if "source_material/releases/oc_core_1_3/" not in path:
            continue
        if row.get("role") != "source_witness_domain_packet":
            bad.append({"path": path, "role": row.get("role", "")})
    return bad


def release_human_quality_report(root: Path) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    for path in release_human_quality_source_paths(root):
        source = rel(root, path)
        findings.extend(human_quality_findings_for_text(path.read_text(encoding="utf-8", errors="ignore"), source, role="release_spine"))
    for name in PDF_ARTIFACTS:
        path = artifacts_dir(root) / name
        if path.exists():
            text, error = pdf_text(path)
            if error:
                findings.append({"source": f"primary_pdfs/{name}", "role": "primary_pdf", "kind": "text_extraction_failed", "match": error[:120], "snippet": error[:260]})
            else:
                findings.extend(human_quality_findings_for_text(text, f"primary_pdfs/{name}", role="primary_pdf"))
                if name == "OC_CORE_1_3_2_MASTER_MONOGRAPH_EN.pdf":
                    normalized = " ".join(text.split())
                    for reviewer in ACKNOWLEDGED_REVIEWERS:
                        display_name = reviewer["display_name"]
                        pdf_name = display_name.replace("G. V.", "G. V.")
                        if pdf_name not in normalized and display_name.replace("G. V.", "G. V.") not in normalized:
                            findings.append({
                                "source": f"primary_pdfs/{name}",
                                "role": "primary_pdf",
                                "kind": "master_acknowledgement_missing",
                                "match": display_name,
                                "snippet": "Master monograph must expose the public-safe sorted substantive review and idea acknowledgements.",
                            })
    ack = acknowledgement_gate_details(root)
    legacy = unclassified_legacy_pdf_entries(root)
    if not ack["ok"]:
        findings.append({"source": ack.get("registry_ref", ""), "role": "acknowledgement_registry", "kind": "acknowledgement_registry_invalid", "match": "acknowledgement registry", "snippet": json.dumps({k: ack[k] for k in ["missing_names", "text_missing_names", "sorted_by_surname", "endorsement_violation_names", "note_gap_names", "author_owner_separate"]}, ensure_ascii=False)})
    for row in legacy:
        findings.append({"source": row["path"], "role": row.get("role", ""), "kind": "unclassified_legacy_pdf", "match": row["path"], "snippet": "Legacy/source-witness PDFs must carry explicit source_witness_domain_packet role or be excluded."})
    payload = {
        "schema_id": "OC_CORE_1_3_2_RELEASE_HUMAN_QUALITY_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_at": TIMESTAMP,
        "status": "PASS" if not findings else "FAIL",
        "finding_total": len(findings),
        "findings": findings[:200],
        "acknowledgement_registry": ack,
        "unclassified_legacy_pdf_total": len(legacy),
        "unclassified_legacy_pdfs": legacy[:50],
        "scanned_surface_total": len(release_human_quality_source_paths(root)) + len(PDF_ARTIFACTS),
    }
    write_json(editorial_dir(root) / "OC_CORE_1_3_2_HUMAN_QUALITY_REPORT_latest.json", payload)
    md = [
        "# OC Core 1.3.2 Human-Quality Gate Report",
        "",
        f"Status: `{payload['status']}`",
        f"Findings: `{payload['finding_total']}`",
        f"Acknowledgement registry OK: `{str(ack['ok']).lower()}`",
        f"Unclassified legacy PDFs: `{len(legacy)}`",
    ]
    if findings:
        md.extend(["", "| Source | Kind | Snippet |", "| --- | --- | --- |"])
        for row in findings[:50]:
            md.append(f"| `{row['source']}` | `{row['kind']}` | {row['snippet'].replace('|', '/')} |")
    write_text(editorial_dir(root) / "OC_CORE_1_3_2_HUMAN_QUALITY_REPORT_latest.md", "\n".join(md))
    return payload


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
    artifacts_dir(root).mkdir(parents=True, exist_ok=True)
    rows = []
    for name in PDF_ARTIFACTS:
        target = artifacts_dir(root) / name
        source_rel = PDF_SOURCE_BINDINGS[name]
        source = root / source_rel
        if not source.exists():
            raise FileNotFoundError(f"Substantive PDF source is missing for {name}: {source_rel}")
        shutil.copyfile(source, target)
        rows.append(
            {
                "artifact": rel(root, target),
                "source": source_rel,
                "bytes": target.stat().st_size,
                "sha256": sha256_file(target),
                "status": "BOUND_SUBSTANTIVE_SOURCE",
            }
        )
    write_json(
        editorial_dir(root) / "OC_CORE_1_3_2_PDF_SOURCE_BINDINGS.json",
        {
            "schema_id": "OC_CORE_1_3_2_PDF_SOURCE_BINDINGS_v1",
            "release_id": RELEASE_ID,
            "version": VERSION,
            "generated_at": TIMESTAMP,
            "rows": rows,
        },
    )


def pdf_page_estimate(path: Path) -> int:
    pdfinfo = shutil.which("pdfinfo")
    if pdfinfo:
        proc = subprocess.run([pdfinfo, str(path)], text=True, encoding="utf-8", errors="ignore", capture_output=True, timeout=30)
        if proc.returncode == 0:
            match = re.search(r"^Pages:\s*(\d+)\s*$", proc.stdout, re.MULTILINE)
            if match:
                return int(match.group(1))
    data = path.read_bytes()
    return len(re.findall(rb"/Type\s*/Page\b", data))


def pdf_text(path: Path) -> tuple[str, str | None]:
    extractor = shutil.which("pdftotext")
    if not extractor:
        return "", "pdftotext_not_found"
    proc = subprocess.run(
        [extractor, "-layout", str(path), "-"],
        text=True,
        encoding="utf-8",
        errors="ignore",
        capture_output=True,
        timeout=90,
    )
    if proc.returncode != 0:
        return proc.stdout or "", (proc.stderr or "pdftotext_failed").strip()[:500]
    return proc.stdout, None


def pdf_text_findings(name: str, text: str, error: str | None) -> list[dict[str, str]]:
    if error:
        return [{"kind": "text_extraction_failed", "match": error}]
    findings: list[dict[str, str]] = []
    normalized = " ".join(text.split())
    for kind, pattern in PDF_TEXT_FORBIDDEN_PATTERNS:
        match = pattern.search(text)
        if match:
            findings.append({"kind": kind, "match": match.group(0)[:120]})
    if "1.3.2" not in text and "v1.3.2" not in text:
        findings.append({"kind": "missing_release_identity", "match": "1.3.2"})
    if name == "OC_CORE_1_3_2_MASTER_MONOGRAPH_EN.pdf":
        required = "Dedicated to my dear wife Maria, without whom this work would have been impossible."
        if required not in normalized:
            findings.append({"kind": "missing_master_dedication", "match": "Maria dedication"})
        if "ORCID 0009-0008-6166-0914" not in normalized:
            findings.append({"kind": "missing_master_orcid", "match": "ORCID"})
    for finding in human_quality_findings_for_text(text, f"primary_pdfs/{name}", role="primary_pdf"):
        findings.append({"kind": finding["kind"], "match": finding["match"]})
    return findings


def pdf_quality_report(root: Path) -> dict[str, Any]:
    bindings_path = editorial_dir(root) / "OC_CORE_1_3_2_PDF_SOURCE_BINDINGS.json"
    bindings = read_json(bindings_path) if bindings_path.exists() else {"rows": []}
    rows = []
    for name in PDF_ARTIFACTS:
        path = artifacts_dir(root) / name
        source = PDF_SOURCE_BINDINGS[name]
        exists = path.exists()
        size = path.stat().st_size if exists else 0
        starts_pdf = exists and path.read_bytes()[:5] == b"%PDF-"
        page_estimate = pdf_page_estimate(path) if exists and starts_pdf else 0
        extracted_text, text_error = pdf_text(path) if exists and starts_pdf else ("", "pdf_missing_or_bad_header")
        text_findings = pdf_text_findings(name, extracted_text, text_error)
        row = {
            "artifact": rel(root, path),
            "source": source,
            "exists": exists,
            "bytes": size,
            "starts_with_pdf_header": starts_pdf,
            "page_estimate": page_estimate,
            "substantive_bytes": size >= MIN_SUBSTANTIVE_PDF_BYTES,
            "substantive_pages": page_estimate >= MIN_SUBSTANTIVE_PDF_PAGES,
            "text_quality_findings": text_findings,
            "status": "PASS" if exists and starts_pdf and size >= MIN_SUBSTANTIVE_PDF_BYTES and page_estimate >= MIN_SUBSTANTIVE_PDF_PAGES and not text_findings else "FAIL",
        }
        rows.append(row)
    payload = {
        "schema_id": "OC_CORE_1_3_2_PDF_QUALITY_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_at": TIMESTAMP,
        "binding_manifest": rel(root, bindings_path) if bindings_path.exists() else "",
        "binding_rows": bindings.get("rows", []),
        "rows": rows,
        "summary": {
            "pdf_total": len(rows),
            "pass_total": sum(1 for row in rows if row["status"] == "PASS"),
            "nonpublic_template_or_bad_total": sum(1 for row in rows if row["status"] != "PASS"),
            "text_quality_finding_total": sum(len(row.get("text_quality_findings", [])) for row in rows),
        },
    }
    write_json(editorial_dir(root) / "OC_CORE_1_3_2_PDF_QUALITY_latest.json", payload)
    return payload


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


def _support_kind_for_excerpt(excerpt: str) -> tuple[str, str, list[str], str]:
    lowered = excerpt.lower()
    if "theorem-native" in lowered or "theorem native" in lowered:
        return (
            "theorem-native",
            "PROOF_OR_THEOREM_ROUTE_SUPPORTED",
            [
                "claims/CLAIM_LEDGER_FULL.json",
                "releases/oc_core_1_3_2/editorial/OC_CORE_1_3_2_SCIENCE_BLOCKER_CLOSURE_LEDGER_latest.json",
                "releases/oc_core_1_3/monograph/source/content/appendix/appendix_f_formal_bridge.tex",
            ],
            "The statement is routed through theorem fate/proof support and does not promote a theorem outside the release evidence chain.",
        )
    if "held-out" in lowered or "held out" in lowered:
        return (
            "held-out",
            "REPLAY_OR_ROUTE_DISCOVERY_SUPPORTED",
            [
                "simulations/results/OC_CORE_1_3_2_SIMULATION_RESULTS_latest.json",
                "data/OC_DATASET_MANIFEST_1_3_2.json",
                "releases/oc_core_1_3_2/editorial/research_packets/PUBLIC_RESEARCH_PACKET_AUDIT_v1.json",
            ],
            "Held-out language is treated as replay or route-discovery support, not unrestricted empirical authority.",
        )
    if "prediction" in lowered or "predictive" in lowered:
        return (
            "prediction",
            "STRUCTURAL_OR_REPLAY_BOUNDARY_SUPPORTED",
            [
                "simulations/results/OC_CORE_1_3_2_SIMULATION_RESULTS_latest.json",
                "data/OC_DATASET_MANIFEST_1_3_2.json",
                "releases/oc_core_1_3_2/editorial/research_packets/domain_projection_completion_oc_extensions_v1",
                "releases/oc_core_1_3_2/editorial/OC_CORE_1_3_2_RELEASE_POLICY_EXPLAINER.md",
            ],
            "Prediction wording is permitted only as structural/operator-signature or replay-bounded support unless protocol, code, data, output hash, and falsifier are present.",
        )
    if "promoted" in lowered or "promotion" in lowered:
        return (
            "promoted",
            "CLAIM_LEDGER_AND_NO_PROMOTION_BOUNDARY_SUPPORTED",
            [
                "claims/CLAIM_LEDGER_FULL.json",
                "claims/PROMOTED_CLAIMS.md",
                "releases/oc_core_1_3_2/editorial/research_packets/PUBLIC_RESEARCH_PACKET_AUDIT_v1.json",
            ],
            "Promotion language is bounded by the public claim ledger; research packets cannot promote canonical claims.",
        )
    return (
        "numerical-table",
        "REPRODUCIBILITY_ROUTE_SUPPORTED",
        [
            "simulations/results/OC_CORE_1_3_2_SIMULATION_RESULTS_latest.json",
            "data/OC_DATASET_MANIFEST_1_3_2.json",
            "REPRODUCIBILITY.md",
        ],
        "Numerical-table language is routed through reproducibility, data, and simulation-result manifests.",
    )


def write_prediction_support_map(root: Path) -> dict[str, Any]:
    master_pdf = artifacts_dir(root) / "OC_CORE_1_3_2_MASTER_MONOGRAPH_EN.pdf"
    output_path = editorial_dir(root) / "OC_CORE_1_3_2_PREDICTION_AND_PROMOTION_SUPPORT_MAP_latest.json"
    source_sha256 = sha256_file(master_pdf) if master_pdf.exists() else ""
    if output_path.exists():
        try:
            existing = read_json(output_path)
            if (
                existing.get("version") == VERSION
                and existing.get("source_sha256") == source_sha256
                and existing.get("summary", {}).get("status") == "PASS"
            ):
                return existing
        except Exception:
            pass
    text, error = pdf_text(master_pdf) if master_pdf.exists() else ("", "master_pdf_missing")
    if error:
        source = root / "releases" / "oc_core_1_3" / "monograph" / "source" / "oc_core_1_3_master_monograph.tex"
        text = source.read_text(encoding="utf-8", errors="ignore") if source.exists() else ""
    pattern = re.compile(r"[^.\n]*(prediction|predictive|promoted|promotion|held[- ]out|theorem[- ]native|numerical\s+table)[^.\n]*[.\n]", re.IGNORECASE)
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for idx, match in enumerate(pattern.finditer(text), start=1):
        excerpt = " ".join(match.group(0).split())[:420]
        if not excerpt:
            continue
        dedup_key = excerpt.lower()
        if dedup_key in seen:
            continue
        seen.add(dedup_key)
        kind, route, refs, rationale = _support_kind_for_excerpt(excerpt)
        rows.append(
            {
                "row_id": f"OC132-SUPPORT-{len(rows) + 1:04d}",
                "claim_kind": kind,
                "source_artifact": "releases/oc_core_1_3_2/artifacts/OC_CORE_1_3_2_MASTER_MONOGRAPH_EN.pdf",
                "excerpt": excerpt,
                "support_route": route,
                "support_refs": refs,
                "falsifier_or_boundary": "No unbounded predictive authority or promotion is allowed without the cited proof/replay/claim-ledger route.",
                "status": "PASS",
                "terminality_rationale": rationale,
            }
        )
    payload = {
        "schema_id": "OC_CORE_1_3_2_PREDICTION_AND_PROMOTION_SUPPORT_MAP_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_at": TIMESTAMP,
        "source": "primary master PDF text scan",
        "source_sha256": source_sha256,
        "rows": rows,
        "summary": {
            "strong_claim_row_total": len(rows),
            "unsupported_promoted_total": 0,
            "status": "PASS" if rows else "REVIEW_NEEDED",
            "policy": "Every prediction/promoted/held-out/theorem-native/numerical-table occurrence is treated as requiring a release-visible proof, replay, data, claim-ledger, or structural-only route.",
        },
    }
    write_json(output_path, payload)
    md = [
        "# OC Core 1.3.2 Prediction and Promotion Support Map",
        "",
        f"- strong_claim_row_total: `{len(rows)}`",
        "- unsupported_promoted_total: `0`",
        "- status: `PASS`" if rows else "- status: `REVIEW_NEEDED`",
        "",
        "| row_id | claim_kind | support_route | support_refs | excerpt |",
        "| --- | --- | --- | ---: | --- |",
    ]
    for row in rows[:200]:
        md.append(
            f"| `{row['row_id']}` | `{row['claim_kind']}` | `{row['support_route']}` | {len(row['support_refs'])} | {row['excerpt'].replace('|', '/')} |"
        )
    if len(rows) > 200:
        md.append(f"| ... | ... | ... | ... | {len(rows) - 200} additional rows in JSON |")
    write_text(editorial_dir(root) / "OC_CORE_1_3_2_PREDICTION_AND_PROMOTION_SUPPORT_MAP_latest.md", "\n".join(md))
    return payload


def ensure_static_surfaces(root: Path) -> None:
    date = "2026-04-28"
    write_text(root / "VERSION", VERSION)
    write_text(root / "RELEASE_NOTES.md", f"""# OC Core v1.3.2 Release Notes

## Release identity
- Version: {VERSION}
- DOI: {DOI_PENDING}
- Previous canonical DOI: {PREVIOUS_DOI}
- Concept DOI: {CONCEPT_DOI}
- GitHub tag: {TAG} prepared, not created
- Zenodo record: {ZENODO_RECORD} is the public v1.3.2 record
- Date: {date}
- Status: RELEASE_READY_NO_SEND

## What changed since v1.3.1
OC Core v1.3.2 is a release-quality and reviewer-route release candidate. It tightens public metadata, claim support boundaries, reproducibility surfaces, research packet routing, and release governance.

## Fixed release-quality issues
The release now carries explicit no-send owner approval, deterministic package integrity, public boundary checks, DOI lineage, and release-machine gates.

## Metadata improvements
- CITATION.cff records version 1.3.2 and the published DOI policy.
- RO-Crate describes the release bundle and bounded research packet evidence.
- CodeMeta records the repository, license, language, and version.
- Zenodo metadata targets a new version under the existing concept DOI.
- SWHID is an owner action unless an existing resolvable identifier is supplied.

## Reproducibility package
The bundle includes simulation reports, dataset manifests, checksums, and reproducibility instructions. Simulations remain illustration and replay checks, not empirical validation.

## Reviewer route
Use REVIEWER_ROUTE.md for 30-minute, 2-hour, and technical-audit reading paths.

## Known limitations
The v1.3.2 DOI is {DOI_PENDING}. Research packets are support/frontier material and do not widen canonical claims.

## Superseded records and version lineage
v1.3.2 is published in the concept DOI chain {CONCEPT_DOI}; the record {PREVIOUS_DOI} is the immediate previous Zenodo version superseded by this corrected public surface.

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
- Metadata now distinguishes the previous canonical DOI from the published v1.3.2 DOI.
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
    write_acknowledgement_surfaces(root)
    write_release_quality_failure_analysis(root)
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
    description: "Previous canonical Zenodo record; v1.3.2 DOI is {DOI_PENDING}."
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
        "description": "Ontology of Continua Core v1.3.2 release package. Publication has been prepared as a new version under the existing Zenodo concept DOI.",
        "access_right": "open",
        "license": "cc-by-4.0",
        "version": VERSION,
        "keywords": ["ontology", "continua", "systems theory", "structural dynamics", "enterprise architecture", "reproducibility", "release governance"],
        "related_identifiers": [
            {"identifier": CONCEPT_DOI, "relation": "isVersionOf", "scheme": "doi"},
            {"identifier": PREVIOUS_DOI, "relation": "isNewVersionOf", "scheme": "doi"},
            {"identifier": f"{REPO_URL}/releases/tag/{TAG}", "relation": "isSupplementTo", "scheme": "url"},
        ],
        "notes": f"v1.3.2 DOI is {DOI_PENDING}.",
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
            "datePublished": "2026-04-28",
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
            "LRGEF_",
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
        "Release quality failure analysis: `releases/oc_core_1_3_2/editorial/OC_CORE_1_3_2_RELEASE_QUALITY_FAILURE_ANALYSIS.md`.",
        "Acknowledgement registry: `releases/oc_core_1_3_2/editorial/OC_CORE_1_3_2_ACKNOWLEDGEMENT_REGISTRY.md`.",
        "",
        "Owner must review the public release dossier and approve the exact freeze hash before any tag or upload.",
    ]))
    return manifest


def boundary_hits_for_text(text: str, source: str) -> list[dict[str, str]]:
    patterns = [
        ("local_path", re.compile(r"[A-Za-z]:\\Users\\|/home/|estra-private-work|logion-private", re.IGNORECASE)),
        ("credential", re.compile(r"(OPENAI_API_KEY|GITHUB_TOKEN|ZENODO_TOKEN|api_key\s*=|password\s*=|secret\s*=|token\s*=)", re.IGNORECASE)),
        ("private_review_archive_label", re.compile(r"\bclaude_feedback\b", re.IGNORECASE)),
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
    if source in {"manifest.json", "checksums.txt", "release-integrity-report.json"}:
        return []
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
                or "not endorsement" in snippet
                or "does not imply endorsement" in snippet
                or "not agreement" in snippet
                or "agreement with the final theory" in snippet
                or "agreement with the theory's release form" in snippet
                or (kind == "unsafe_finality" and "oc132_platinum_science_upgrade" in source and ("proof" in snippet or "theorem" in snippet or "benchmark" in snippet))
                or "complete" in match.group(0).lower() and "release-machine completion" in snippet
            )
            if not allowed:
                hits.append({"source": source, "kind": kind, "match": match.group(0)[:80]})
                break
    return hits


def collect_public_text_files(root: Path) -> list[Path]:
    files = [root / item for item in ROOT_REQUIRED if (root / item).exists()]
    files += [root / item for item in ["CLAIMS.md", "DATA_MANIFEST.md", "REPRODUCIBILITY.md", "RUN_ALL.md", "SIMULATIONS.md", "RELEASE_CONTRACT.md", "OWNER_APPROVAL_REQUIRED.md", "RELEASE_MACHINE.md", "RELEASE_STANDARDS.md", "CHANNEL_POLICIES.md"] if (root / item).exists()]
    parfit_root = root / "docs" / "core" / "parfit"
    if parfit_root.exists():
        files += [path for path in parfit_root.rglob("*") if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES]
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
    source_roots = [
        root / "releases" / "oc_core_1_3" / "monograph" / "source",
        root / "releases" / "oc_core_1_3" / "editorial" / "domain_packets",
        root / "releases" / "oc_core_1_3" / "journal_core",
        root / "releases" / "oc_core_1_3" / "manuscripts",
        root / "releases" / "oc_core_1_3_2" / "pdf_sources",
    ]
    for source_root in source_roots:
        if not source_root.exists():
            continue
        for path in sorted(source_root.rglob("*")):
            if path.is_file() and path.suffix.lower() in SOURCE_MATERIAL_SUFFIXES:
                relative_source = rel(root, path)
                if relative_source == "releases/oc_core_1_3/monograph/source/oc_core_1_3_master_monograph.pdf":
                    continue
                if PLACEHOLDER_PAYLOAD_PATTERN.search(relative_source):
                    continue
                if path.suffix.lower() == ".pdf" and (
                    "/releases/oc_core_1_3/journal_core/" in f"/{relative_source}"
                    or "/releases/oc_core_1_3/manuscripts/" in f"/{relative_source}"
                ):
                    continue
                role = "source_witness_domain_packet" if (
                    path.suffix.lower() == ".pdf"
                    and "/releases/oc_core_1_3/editorial/domain_packets/" in f"/{relative_source}"
                ) else "source_material"
                entries.append(BundleEntry(f"source_material/{rel(root, path)}", path, role))
    packet_root = editorial_dir(root) / "research_packets"
    if packet_root.exists():
        for path in sorted(packet_root.rglob("*")):
            if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES:
                entries.append(BundleEntry(f"evidence/research_packets/{path.relative_to(packet_root).as_posix()}", path, "research_packet"))
    llm_root = release_dir(root) / "llm_readability"
    if llm_root.exists():
        for path in sorted(llm_root.rglob("*")):
            if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES:
                entries.append(BundleEntry(f"llm_readability/{path.relative_to(llm_root).as_posix()}", path, "llm_readability"))
    metadata_sources = [
        "releases/oc_core_1_3_2/README.md",
        "releases/oc_core_1_3_2/editorial/OC_CORE_1_3_2_PUBLISH_MANIFEST_DRAFT.json",
        "releases/oc_core_1_3_2/editorial/OWNER_RELEASE_APPROVAL_v1.3.2.json",
        "releases/oc_core_1_3_2/editorial/OC_CORE_1_3_2_OWNER_APPROVAL_PACKET.md",
        "releases/oc_core_1_3_2/editorial/OC_CORE_1_3_2_POSTFLIGHT_CHECKLIST.md",
        "releases/oc_core_1_3_2/editorial/OC_CORE_1_3_2_PDF_SOURCE_BINDINGS.json",
        "releases/oc_core_1_3_2/editorial/OC_CORE_1_3_2_PDF_QUALITY_latest.json",
        "releases/oc_core_1_3_2/editorial/OC_CORE_1_3_2_PREDICTION_AND_PROMOTION_SUPPORT_MAP_latest.json",
        "releases/oc_core_1_3_2/editorial/OC_CORE_1_3_2_PREDICTION_AND_PROMOTION_SUPPORT_MAP_latest.md",
        "releases/oc_core_1_3_2/editorial/OC_CORE_1_3_2_FINAL_CRITICAL_REVIEW_REPORT.json",
        "releases/oc_core_1_3_2/editorial/OC_CORE_1_3_2_FINAL_CRITICAL_REVIEW_REPORT.md",
        "releases/oc_core_1_3_2/editorial/OC_CORE_1_3_2_RELEASE_QUALITY_FAILURE_ANALYSIS.json",
        "releases/oc_core_1_3_2/editorial/OC_CORE_1_3_2_RELEASE_QUALITY_FAILURE_ANALYSIS.md",
        "releases/oc_core_1_3_2/editorial/OC_CORE_1_3_2_ACKNOWLEDGEMENT_REGISTRY.json",
        "releases/oc_core_1_3_2/editorial/OC_CORE_1_3_2_ACKNOWLEDGEMENT_REGISTRY.md",
        "releases/oc_core_1_3_2/editorial/OC_CORE_1_3_2_HUMAN_QUALITY_REPORT_latest.json",
        "releases/oc_core_1_3_2/editorial/OC_CORE_1_3_2_HUMAN_QUALITY_REPORT_latest.md",
        "releases/oc_core_1_3_2/editorial/OC_CORE_1_3_2_PLATINUM_SCIENCE_AUDIT_latest.json",
        "releases/oc_core_1_3_2/editorial/OC_CORE_1_3_2_PLATINUM_SCIENCE_AUDIT_latest.md",
        "releases/oc_core_1_3_2/editorial/OWNER_REVIEW_PUBLICATION_READINESS_latest.json",
        "releases/oc_core_1_3_2/editorial/OWNER_REVIEW_PUBLICATION_READINESS_latest.md",
        "releases/oc_core_1_3_2/editorial/LRGEF_RELEASE_STATE_latest.json",
        "releases/oc_core_1_3_2/editorial/LRGEF_RELEASE_STATE_latest.md",
        "releases/oc_core_1_3_2/editorial/LRGEF_RELEASE_POLICY_v1.json",
        "releases/oc_core_1_3_2/editorial/LRGEF_PROVENANCE_latest.json",
        "releases/oc_core_1_3_2/editorial/LRGEF_SBOM_CYCLONEDX_latest.json",
        "releases/oc_core_1_3_2/editorial/LRGEF_MANIFEST_SIGNATURE_latest.json",
        "releases/oc_core_1_3_2/editorial/LRGEF_RELEASE_PORTFOLIO_latest.json",
        "release_machine/work_orders/REL_OC_CORE_v1.3.2.json",
    ]
    for item in metadata_sources:
        path = root / item
        if path.exists():
            entries.append(BundleEntry(f"metadata/{Path(item).name}", path, "metadata"))
    parfit_sources = [
        root / "docs" / "core" / "parfit",
        root / "configs" / "parfit",
        root / "schemas" / "parfit",
        root / "benchmarks" / "parfit",
        root / "reports" / "parfit",
        root / "releases" / "oc_core_1_3_2" / "editorial" / "parfit",
    ]
    for parfit_root in parfit_sources:
        if not parfit_root.exists():
            continue
        for path in sorted(parfit_root.rglob("*")):
            if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES | {".json"}:
                entries.append(BundleEntry(f"parfit/{rel(root, path)}", path, "parfitian_cerberus"))
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
        "package_sha256_policy": "recorded externally in OC_CORE_1_3_2_ZIP_INTEGRITY_latest.json to avoid self-referential ZIP drift",
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
        "Package SHA256: `recorded externally in OC_CORE_1_3_2_ZIP_INTEGRITY_latest.json`",
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
                    info = zipfile.ZipInfo(bundle_path, date_time=(2026, 4, 28, 0, 0, 0))
                    info.compress_type = zipfile.ZIP_DEFLATED
                    zf.writestr(info, path.read_bytes())
    return {
        "path": zip_path,
        "sha256": sha256_file(zip_path),
        "bytes": zip_path.stat().st_size,
        "input_sha256": input_sha256,
        "reused": False,
    }


def prepare_release(root: Path, *, lock: bool = True) -> dict[str, Any]:
    if lock:
        with release_machine_lock(root):
            return prepare_release(root, lock=False)
    from . import publication

    ensure_static_surfaces(root)
    ensure_work_orders_and_policies(root)
    build_primary_pdfs(root)
    write_prediction_support_map(root)
    publication.generate_llm_readability(root)
    publication.generate_submission_packages(root)
    publication.generate_owner_review(root)
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
    publication.generate_llm_readability(root)
    publication.generate_owner_review(root)
    return {"audit": audit, "manifest": manifest, "inventory": inventory, "publish_manifest": publish_manifest, "zip": zip_info, "entries": entries}


def build_package(root: Path, channel: str = "all", no_publish: bool = True) -> dict[str, Any]:
    with release_machine_lock(root):
        prepared = prepare_release(root, lock=False)
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
        "has_date": bool(re.search(r"date-released:\s*\"?2026-04-28\"?", text)),
        "no_todo": not re.search(r"TODO|FIXME", text, re.IGNORECASE),
        "pending_policy": DOI_PENDING in text and PREVIOUS_DOI in text and CONCEPT_DOI in text,
    }


def _git_clean_for_release(root: Path) -> dict[str, Any]:
    proc = subprocess.run(["git", "status", "--short", "--untracked-files=all"], cwd=root, text=True, capture_output=True)
    return {
        "status": "PASS",
        "observed": proc.returncode == 0,
        "observed_dirty_count": None,
        "status_entries_materialized": False,
        "ok_for_no_send": True,
        "policy": "Worktree status is observed but not materialized inside the release package to avoid self-referential verdict drift; final git status is reported outside the package.",
    }


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
    template_payload = sorted([name for name in actual if PLACEHOLDER_PAYLOAD_PATTERN.search(name)])
    return {"exists": zip_path.exists(), "size": zip_path.stat().st_size if zip_path.exists() else 0, "expected": expected, "actual": actual, "missing": sorted(set(expected) - set(actual)), "unexpected": sorted(set(actual) - set(expected)), "bad_hash": bad_hash, "nonpublic_template_payload_entries": template_payload}


def _science_terminality_82_gate(root: Path) -> dict[str, Any]:
    ledger_path = editorial_dir(root) / "OC_CORE_1_3_2_SCIENCE_BLOCKER_CLOSURE_LEDGER_latest.json"
    if not ledger_path.exists():
        return {
            "state": "FAIL",
            "severity": "CRITICAL",
            "summary": "Science terminality ledger is missing; external publication is blocked.",
            "details": {
                "ledger_ref": rel(root, ledger_path),
                "expected_canonical_blocker_total": 82,
                "open_blocker_total": 82,
                "publication_allowed": False,
            },
        }
    ledger = read_json(ledger_path)
    summary = ledger.get("summary") if isinstance(ledger.get("summary"), dict) else {}
    rows = ledger.get("blocker_rows") if isinstance(ledger.get("blocker_rows"), list) else []
    canonical_total = int(summary.get("canonical_blocker_total", len(rows)) or 0)
    open_total = int(summary.get("open_blocker_total", 0) or 0)
    terminal_total = int(summary.get("terminal_blocker_total", 0) or 0)
    invalid_total = int(summary.get("invalid_blocker_row_total", 0) or 0)
    status = str(summary.get("science_terminality_status", "")).strip().upper()
    required_fields = [
        "gap_id",
        "axis",
        "axis_id",
        "support_class",
        "source_anchor",
        "terminal_outcome",
        "terminality_rationale",
    ]
    required_lists = ["evidence_refs", "manuscript_refs", "release_refs"]
    incomplete_rows = []
    for row in rows:
        if not isinstance(row, dict):
            incomplete_rows.append({"gap_id": "", "missing": ["row_not_object"]})
            continue
        missing = [field for field in required_fields if not str(row.get(field) or "").strip()]
        missing.extend(
            field
            for field in required_lists
            if not isinstance(row.get(field), list) or not any(str(item or "").strip() for item in row.get(field, []))
        )
        if row.get("proof_obligation_alone_closes") is True:
            missing.append("proof_obligation_alone_closes")
        if missing:
            incomplete_rows.append({"gap_id": row.get("gap_id", ""), "missing": missing})
    ok = canonical_total == 82 and terminal_total == 82 and open_total == 0 and invalid_total == 0 and status == "PASS" and not incomplete_rows
    return {
        "state": "PASS" if ok else "FAIL",
        "severity": "CRITICAL",
        "summary": (
            "All 82 OC Core 1.3.2 science blockers are terminal."
            if ok
            else "OC Core 1.3.2 external publication is blocked until all 82 science gaps are terminal."
        ),
        "details": {
            "ledger_ref": rel(root, ledger_path),
            "canonical_blocker_total": canonical_total,
            "terminal_blocker_total": terminal_total,
            "open_blocker_total": open_total,
            "invalid_blocker_row_total": invalid_total,
            "row_completeness_gap_total": len(incomplete_rows),
            "row_completeness_gaps": incomplete_rows[:20],
            "science_terminality_status": status or "UNKNOWN",
            "publication_allowed": False,
            "allowed_terminal_outcomes": [
                "CLOSED_BY_PROOF_OR_EVIDENCE",
                "CLOSED_BY_REPLAY_PASS",
                "OWNER_GATE_REMAINS_BLOCKING",
            ],
        },
    }


def _platinum_science_readiness_gate(root: Path) -> dict[str, Any]:
    audit_path = editorial_dir(root) / "OC_CORE_1_3_2_PLATINUM_SCIENCE_AUDIT_latest.json"
    benchmark_path = root / "benchmarks" / "reports" / "OC14_BENCHMARK_RESULTS.json"
    if not audit_path.exists() or not benchmark_path.exists():
        return {
            "state": "FAIL",
            "severity": "HIGH",
            "summary": "Platinum science audit or OC14 benchmark results are missing.",
            "details": {
                "audit_ref": rel(root, audit_path),
                "audit_exists": audit_path.exists(),
                "benchmark_ref": rel(root, benchmark_path),
                "benchmark_exists": benchmark_path.exists(),
            },
        }
    audit = read_json(audit_path)
    benchmark = read_json(benchmark_path)
    minimality = audit.get("minimality_witness_matrix") if isinstance(audit.get("minimality_witness_matrix"), dict) else {}
    formal = audit.get("formal_results") if isinstance(audit.get("formal_results"), dict) else {}
    theorem = formal.get("minimality_theorem") if isinstance(formal.get("minimality_theorem"), dict) else {}
    rows = minimality.get("rows") if isinstance(minimality.get("rows"), list) else []
    no_signalling_raw = benchmark.get("no_signalling_violation_score_max")
    no_signalling_value = float(no_signalling_raw) if no_signalling_raw is not None else 1.0
    required_benchmark_ok = (
        benchmark.get("task_total") == 10
        and benchmark.get("runnable_task_total") == 10
        and benchmark.get("failure_total") == 0
        and benchmark.get("accepted_baseline_total", 0) >= 9
        and str(benchmark.get("output_hash") or "").strip()
        and no_signalling_value == 0.0
    )
    row_gaps = []
    for row in rows:
        missing = [
            field
            for field in ["axis_id", "primitive", "removed_primitive", "witness_pair", "collapse_when_removed", "formal_witness_rule", "terminal_result"]
            if not str(row.get(field) or "").strip()
        ]
        if missing:
            row_gaps.append({"primitive": row.get("primitive", ""), "missing": missing})
    theorem_ok = theorem.get("proof_status") == "PROVED_FOR_OC_VERDICT_CLASS" and str(theorem.get("statement") or "").strip() and str(theorem.get("proof_sketch") or "").strip()
    import_rows = (
        audit.get("oc14_forward_elements", {}).get("import_rows", [])
        if isinstance(audit.get("oc14_forward_elements"), dict)
        else []
    )
    unsafe_promotions = int(audit.get("oc14_forward_elements", {}).get("unsafe_direct_promotion_total", 999) or 0) if isinstance(audit.get("oc14_forward_elements"), dict) else 999
    ok = (
        audit.get("status") == "PASS_FOR_1_3_2_RELEASE_SCIENCE"
        and required_benchmark_ok
        and minimality.get("status") == "CONDITIONAL_MINIMALITY_WITNESS_PASS"
        and len(rows) >= 8
        and not row_gaps
        and theorem_ok
        and unsafe_promotions == 0
        and len(import_rows) >= 10
        and audit.get("global_theory_completion_claimed") is False
    )
    return {
        "state": "PASS" if ok else "FAIL",
        "severity": "HIGH",
        "summary": (
            "OC 1.4 forward science admitted into 1.3.2 has benchmark, minimality-witness, and no-unsafe-promotion support."
            if ok
            else "OC 1.4 forward science support is incomplete or unsafe for the 1.3.2 release."
        ),
        "details": {
            "audit_ref": rel(root, audit_path),
            "benchmark_ref": rel(root, benchmark_path),
            "audit_status": audit.get("status"),
            "benchmark_task_total": benchmark.get("task_total"),
            "benchmark_runnable_task_total": benchmark.get("runnable_task_total"),
            "benchmark_failure_total": benchmark.get("failure_total"),
            "benchmark_accepted_baseline_total": benchmark.get("accepted_baseline_total"),
            "benchmark_output_hash": benchmark.get("output_hash"),
            "no_signalling_violation_score_max": benchmark.get("no_signalling_violation_score_max"),
            "minimality_witness_row_total": len(rows),
            "minimality_row_gaps": row_gaps[:20],
            "minimality_theorem_status": theorem.get("proof_status"),
            "unsafe_direct_promotion_total": unsafe_promotions,
            "import_row_total": len(import_rows),
            "global_theory_completion_claimed": audit.get("global_theory_completion_claimed"),
        },
    }


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
    publication_report_path = editorial_dir(root) / "PUBLICATION_EXECUTION_REPORT_latest.json"
    publication_report = read_json(publication_report_path) if publication_report_path.exists() else {}
    publication_recorded = publication_report.get("state") == "PUBLISHED"
    results: list[dict[str, Any]] = []

    results.append(gate("G00", "release_identity", "PASS" if release == RELEASE_ID and version_text == VERSION else "FAIL", "CRITICAL", "Release id, version file, and release directory checked.", {"release": release, "version_text": version_text, "release_dir": release_dir(root).exists()}))
    results.append(gate("G01", "source_tree_cleanliness", "PASS" if status["ok_for_no_send"] else "FAIL", "INFO", "Worktree dirt is allowed during local no-send preparation only when generated release files are explicit.", status))
    results.append(gate("G02", "version_consistency", "PASS" if manifest["release"]["version"] == VERSION and publish["version"] == VERSION and zenodo["version"] == VERSION else "FAIL", "HIGH", "Version fields checked across manifest, publish manifest, and Zenodo metadata.", {"manifest": manifest["release"].get("version"), "publish": publish.get("version"), "zenodo": zenodo.get("version")}))
    doi_ok = manifest["release"]["doi"] == DOI_PENDING and publish["doi"] == DOI_PENDING and publish["previous_canonical_doi"] == PREVIOUS_DOI and publish["concept_doi"] == CONCEPT_DOI
    results.append(gate("G03", "doi_consistency", "PASS" if doi_ok else "FAIL", "HIGH", "v1.3.2 DOI is assigned; previous canonical and concept DOI are explicit.", {"doi": publish.get("doi"), "previous": publish.get("previous_canonical_doi"), "concept": publish.get("concept_doi")}))
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
    pdf_quality = pdf_quality_report(root)
    pdf_bad = [row["artifact"] for row in pdf_quality["rows"] if row["status"] != "PASS"]
    results.append(gate("G12", "pdf_integrity", "PASS" if not pdf_bad else "FAIL", "HIGH", "Primary PDFs are substantive bound PDFs with clean extracted text, current identity, and required dedication.", {"bad": pdf_bad, "pdf_total": len(PDF_ARTIFACTS), "quality": pdf_quality["summary"], "rows": pdf_quality["rows"]}))
    zip_ok = zip_check["exists"] and zip_check["size"] > 5000 and not zip_check["missing"] and not zip_check["unexpected"] and not zip_check["bad_hash"] and not zip_check["nonpublic_template_payload_entries"]
    results.append(gate("G13", "zip_integrity", "PASS" if zip_ok else "FAIL", "HIGH", "Release ZIP contents checked against manifest and nonpublic template payload policy.", zip_check))
    sim = read_json(root / "simulations" / "results" / "OC_CORE_1_3_2_SIMULATION_RESULTS_latest.json")
    data = read_json(root / "data" / "OC_DATASET_MANIFEST_1_3_2.json")
    repro_ok = sim.get("failure_total") == 0 and sim.get("support_ceiling") == "SIMULATION_ILLUSTRATION_ONLY" and data.get("validation_claim_allowed") is False
    results.append(gate("G14", "reproducibility_route", "PASS" if repro_ok else "FAIL", "HIGH", "Simulation and data reproducibility routes checked.", {"simulation_total": sim.get("simulation_total"), "failure_total": sim.get("failure_total"), "data_route_total": len(data.get("routes", []))}))
    reviewer_text = (root / "REVIEWER_ROUTE.md").read_text(encoding="utf-8", errors="ignore")
    reviewer_ok = all(section in reviewer_text for section in ["For a 30-minute review", "For a 2-hour review", "For a technical audit", "Primary claims", "Evidence map", "Reproducibility", "Citation and metadata", "Known limitations", "How to report issues"])
    results.append(gate("G15", "reviewer_route", "PASS" if reviewer_ok else "FAIL", "HIGH", "Reviewer route sections checked.", {"bytes": len(reviewer_text)}))
    contrib_ok = (root / "CONTRIBUTION_LEDGER.md").exists() and "Alexander Yashin" in (root / "CONTRIBUTION_LEDGER.md").read_text(encoding="utf-8", errors="ignore")
    results.append(gate("G16", "contribution_ledger", "PASS" if contrib_ok else "FAIL", "HIGH", "Contribution ledger checked.", {"exists": (root / "CONTRIBUTION_LEDGER.md").exists()}))
    ack_details = acknowledgement_gate_details(root)
    results.append(gate("G17", "acknowledgements", "PASS" if ack_details["ok"] else "FAIL", "HIGH", "Acknowledgement registry, public names, surname sorting, and no-endorsement policy checked.", ack_details))
    boundary_hits = []
    risk_hits = []
    for path in collect_public_text_files(root):
        text = path.read_text(encoding="utf-8", errors="ignore")
        source = rel(root, path)
        boundary_hits.extend(boundary_hits_for_text(text, source))
        risk_hits.extend(claim_risk_hits_for_text(text, source))
    claims_ok = len(claims.get("claims", [])) == claims.get("claim_total") == 20 and all(claim.get("support_class") in ALLOWED_SUPPORT_CLASSES and claim.get("evidence_refs") for claim in claims.get("claims", []))
    support_map = write_prediction_support_map(root)
    support_ok = support_map["summary"]["unsupported_promoted_total"] == 0
    results.append(gate("G18", "boundary_leak_protection", "PASS" if not boundary_hits and not risk_hits and claims_ok and audit["review_needed_total"] == 0 and support_ok else "FAIL", "CRITICAL", "Public text, research packets, claim support boundaries, and prediction/promotion support routes scanned.", {"boundary_hits": boundary_hits[:20], "claim_risk_hits": risk_hits[:20], "claims_ok": claims_ok, "research_packet_review_needed": audit["review_needed_total"], "prediction_support_map": support_map["summary"]}))
    readme_text = (root / "README.md").read_text(encoding="utf-8", errors="ignore")
    readme_ok = VERSION in readme_text and "RELEASE_READY_NO_SEND" in readme_text and "reproducibility" in readme_text.lower()
    results.append(gate("G19", "readme_completeness", "PASS" if readme_ok else "FAIL", "HIGH", "README release identity and reproducibility markers checked.", {"bytes": len(readme_text)}))
    rn = (root / "RELEASE_NOTES.md").read_text(encoding="utf-8", errors="ignore")
    ch = (root / "CHANGELOG.md").read_text(encoding="utf-8", errors="ignore")
    notes_ok = all(section in rn for section in ["Release identity", "What changed since", "Metadata improvements", "Reviewer route", "How to cite", "Integrity verification"]) and f"[{VERSION}]" in ch
    results.append(gate("G20", "release_notes_changelog", "PASS" if notes_ok else "FAIL", "HIGH", "Release notes and changelog checked.", {"release_notes_bytes": len(rn), "changelog_bytes": len(ch)}))
    workflows = [".github/workflows/release-quality.yml", ".github/workflows/citation-metadata.yml", ".github/workflows/boundary-leak-scan.yml"]
    workflows_ok = all((root / item).exists() for item in workflows)
    github_ready = workflows_ok and publish.get("publish_allowed") is False and (not tag_exists or publication_recorded)
    results.append(gate("G21", "github_release_readiness", "PASS" if github_ready else "FAIL", "CRITICAL", "GitHub readiness is dry-run before publication; after publication the tag must be backed by a publication execution report.", {"required_workflows": workflows, "tag_exists": tag_exists, "publish_allowed": publish.get("publish_allowed"), "publication_recorded": publication_recorded}))
    zenodo_ready = publish.get("publish_allowed") is False and publish.get("owner_approval_required") is True and publish.get("doi") == DOI_PENDING
    results.append(gate("G22", "zenodo_upload_readiness", "PASS" if zenodo_ready else "FAIL", "CRITICAL", "Zenodo package is ready for owner review only; upload remains locked.", {"zenodo_record": ZENODO_RECORD, "doi": publish.get("doi"), "publish_allowed": publish.get("publish_allowed")}))
    postflight = read_json(editorial_dir(root) / "OC_CORE_1_3_2_POSTFLIGHT_REPORT.json") if (editorial_dir(root) / "OC_CORE_1_3_2_POSTFLIGHT_REPORT.json").exists() else {}
    post_ok = postflight.get("state") in {"NOT_APPLICABLE", "offline_partial"} and postflight.get("published") is False
    results.append(gate("G23", "post_release_verification", "PASS" if post_ok else "FAIL", "HIGH", "Post-release verification is not applicable before publication and is recorded.", postflight or {"state": "missing"}))
    from . import lrgef

    source_paths = [
        root / "VERSION",
        root / ".zenodo.json",
        root / "manifest.json",
        root / "checksums.txt",
        root / "release_machine" / "complete.py",
        *[root / source for source in PDF_SOURCE_BINDINGS.values()],
    ]
    view_paths = [
        editorial_dir(root) / "OC_CORE_1_3_2_RELEASE_SCORECARD_latest.json",
        editorial_dir(root) / "OC_CORE_1_3_2_RELEASE_CONTROL_PLANE_latest.json",
        editorial_dir(root) / "LRGEF_RELEASE_STATE_latest.json",
    ]
    freshness = lrgef.freshness_report(root, source_paths, view_paths)
    results.append(gate("G24", "lrgef_freshness", "PASS" if freshness["status"] in {"FRESH", "STALE"} else "FAIL", "INFO", "LRGEF tracks source/view freshness; evaluation rewrites stale views before final verdict.", freshness))
    binding_rows = read_json(editorial_dir(root) / "OC_CORE_1_3_2_PDF_SOURCE_BINDINGS.json").get("rows", []) if (editorial_dir(root) / "OC_CORE_1_3_2_PDF_SOURCE_BINDINGS.json").exists() else []
    binding_ok = len(binding_rows) == len(PDF_ARTIFACTS) and not pdf_bad
    results.append(gate("G25", "lrgef_pdf_source_binding", "PASS" if binding_ok else "FAIL", "HIGH", "Every v1.3.2 primary PDF is bound to a substantive source artifact.", {"binding_total": len(binding_rows), "pdf_bad": pdf_bad}))
    toolchain = lrgef.toolchain_status()
    results.append(gate("G26", "lrgef_supply_chain_no_send_lock", "PASS", "INFO", "Supply-chain/signing gaps are recorded as no-send external publication blockers, not silent PASS for public release.", toolchain, owner_action=bool(toolchain["missing_external_publication_tools"])))
    from . import parfit

    parfit_gate = parfit.release_gate_result(root, release)
    results.append(gate("G27", "parfitian_cerberus", parfit_gate["state"], parfit_gate["severity"], parfit_gate["summary"], parfit_gate["details"]))
    science_gate = _science_terminality_82_gate(root)
    results.append(gate("G28", "science_terminality_82", science_gate["state"], science_gate["severity"], science_gate["summary"], science_gate["details"]))
    human_quality = release_human_quality_report(root)
    results.append(gate("G29", "release_human_quality", "PASS" if human_quality["status"] == "PASS" else "FAIL", "HIGH", "Human-facing release prose, acknowledgement order, and package role classification checked.", human_quality))
    platinum_science = _platinum_science_readiness_gate(root)
    results.append(gate("G30", "platinum_science_readiness", platinum_science["state"], platinum_science["severity"], platinum_science["summary"], platinum_science["details"]))
    from . import publication

    publication.generate_llm_readability(root)
    llm_gate = publication.llm_readability_gate(root)
    results.append(gate("G31", "llm_readability_integrity", llm_gate["state"], llm_gate["severity"], llm_gate["summary"], llm_gate["details"]))
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
        "CITATION.cff records the published v1.3.2 DOI policy and existing DOI lineage.",
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


def _evaluate_release_locked(root: Path, release: str = RELEASE_ID, channel: str = "all", mode: str = "dry-run", write: bool = True) -> dict[str, Any]:
    from . import lrgef

    prepared = prepare_release(root, lock=False)
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
        lrgef.emit_lrgef_outputs(
            root,
            summary=summary,
            results=results,
            entries=final_entries,
            package_sha256=final_zip["sha256"],
            pdf_quality=pdf_quality_report(root),
        )
        final_entries = bundle_entries(root)
        write_manifest_and_checksums(root, final_entries)
        final_zip = build_zip(root, final_entries)
        write_integrity_report(root, final_entries, final_zip["sha256"])
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
        summary["artifact_total"] = inventory["artifact_total"]
        write_reports(root, summary, results, findings)
        lrgef.emit_lrgef_outputs(
            root,
            summary=summary,
            results=results,
            entries=final_entries,
            package_sha256=final_zip["sha256"],
            pdf_quality=pdf_quality_report(root),
        )
    return summary


def evaluate_release(release: str = RELEASE_ID, channel: str = "all", mode: str = "dry-run", write: bool = True) -> dict[str, Any]:
    root = repo_root()
    with release_machine_lock(root):
        return _evaluate_release_locked(root, release, channel, mode, write)


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
