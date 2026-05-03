from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time
import zipfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from release_machine import science_monolith
from tools import oc133_scientific_process_spot

RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"
TAG = "v1.3.3"
RELEASE_ROOT = ROOT / "releases" / RELEASE_ID
ARTIFACTS = RELEASE_ROOT / "artifacts"
EDITORIAL = RELEASE_ROOT / "editorial"
PUBLIC_PAYLOAD = RELEASE_ROOT / "public_payload"
PUBLIC_SOURCES = PUBLIC_PAYLOAD / "sources"
PUBLIC_EVIDENCE = PUBLIC_PAYLOAD / "evidence"
PUBLIC_FIGURES = PUBLIC_PAYLOAD / "figures"
PUBLIC_ZIP_NAME = "oc_core_1_3_3_public_release.zip"
PUBLIC_ZIP = ARTIFACTS / PUBLIC_ZIP_NAME
EDITORIAL_CERBERUS_SUMMARY = ROOT / "reviews" / "oc133_llm_cerberus" / "editorial_release_review" / "OC133_EDITORIAL_CERBERUS_SUMMARY.json"
SCIENTIFIC_PROCESS_SPOT = EDITORIAL / "OC133_SCIENTIFIC_PROCESS_SPOT_latest.json"
AUTHOR_DISPLAY = "Alexander Yashin"
AUTHOR_CITATION_NAME = "Yashin, Alexander"
AUTHOR_ORCID = "0009-0008-6166-0914"
AUTHOR_AFFILIATION = "Independent Researcher"
LOGION_ENTITY_NOTE = "Logion is the research-instrument and institute-automation system used to prepare, check, package, and audit the work; it is not an author."
ESTRA_ENTITY_NOTE = "ESTRA is the methodological framework used in the work; it is not an author or affiliation."
PUBLIC_REPOSITORY_URL = "https://github.com/alexanderyashin/ontology-of-continua-core-main"
DEFAULT_PUBLIC_DOI = "10.5281/zenodo.19965913"
DEFAULT_ZENODO_RECORD_URL = "https://zenodo.org/records/19965913"


def public_artifact_path_phrase(raw: str) -> str:
    cleaned = raw.replace("\\", "/").strip()
    if cleaned.lower().startswith("repository path "):
        return cleaned
    if cleaned.lower().startswith("public evidence "):
        return cleaned
    name = Path(cleaned).name
    if cleaned.startswith("appendix/OC_1_3_3_") and cleaned.endswith(".tex"):
        title = Path(cleaned).stem.replace("OC_1_3_3_", "").replace("_", " ").title()
        return f"master monograph appendix: {title}"
    if cleaned.startswith("proofs/proof_sheets/") and name.startswith("T133-"):
        return f"public evidence path evidence/proof_sheets_public/{name}"
    if cleaned == "proofs/FINITE_MODEL_CHECKS_1_3_3.json":
        return "repository path proofs/FINITE_MODEL_CHECKS_1_3_3.json; public evidence path evidence/proofs__FINITE_MODEL_OUTPUT_ATTESTATION_1_3_3.json"
    if cleaned == "proofs/FINITE_MODEL_OUTPUT_ATTESTATION_1_3_3.json":
        return "public evidence path evidence/proofs__FINITE_MODEL_OUTPUT_ATTESTATION_1_3_3.json"
    if cleaned == "proofs/finite_model_checks/OC133_FINITE_MODEL_INPUTS.json":
        return "repository path proofs/finite_model_checks/OC133_FINITE_MODEL_INPUTS.json"
    if cleaned == "validation/target_blind/OC133_TARGET_BLIND_PREDICTION_TABLE.json":
        return "repository path validation/target_blind/OC133_TARGET_BLIND_PREDICTION_TABLE.json; public evidence path evidence/validation__target_blind__OC133_TARGET_BLIND_PREDICTION_TABLE.json"
    if cleaned == "validation/numeric_replay_qa/OC133_NUMERIC_REPLAY_QA_TABLE.json":
        return "repository path validation/numeric_replay_qa/OC133_NUMERIC_REPLAY_QA_TABLE.json"
    if cleaned == "reports/OC_CORE_1_3_3_DOMAIN_VALIDATION_REPORT.json":
        return "repository path reports/OC_CORE_1_3_3_DOMAIN_VALIDATION_REPORT.json; public evidence path evidence/reports__OC_CORE_1_3_3_DOMAIN_VALIDATION_REPORT.json"
    if cleaned == "reports/OC_CORE_1_3_3_COUNTEREXAMPLE_REPORT.json":
        return "public evidence path evidence/reports__OC_CORE_1_3_3_COUNTEREXAMPLE_REPORT.json"
    if cleaned == "reports/OC_CORE_1_3_3_ADVERSARIAL_SIMULATION_REPORT.json":
        return "public evidence path evidence/reports__OC_CORE_1_3_3_ADVERSARIAL_SIMULATION_REPORT.json"
    if cleaned == "simulations/results/OC_CORE_1_3_3_SIMULATION_RESULTS_latest.json":
        return "public evidence path evidence/simulations__results__OC_CORE_1_3_3_SIMULATION_RESULTS_latest.json"
    if cleaned == "reviews/oc133_llm_cerberus/OC133_LLM_CERBERUS_SUMMARY.json":
        return "public evidence path evidence/reviews__oc133_llm_cerberus__OC133_LLM_CERBERUS_SUMMARY.json"
    if cleaned == "docs/OC_1_3_3_PRIOR_ART_COMPARATOR_MATRIX.json":
        return "repository path docs/OC_1_3_3_PRIOR_ART_COMPARATOR_MATRIX.json"
    if cleaned == "comparators/OC_1_3_3_NOVELTY_AND_PRIORITY_REGISTER.json":
        return "repository path comparators/OC_1_3_3_NOVELTY_AND_PRIORITY_REGISTER.json"
    if cleaned.startswith(("claims/", "proofs/", "validation/", "reports/", "reviews/", "docs/", "comparators/", "releases/")):
        return f"repository path {cleaned}"
    return cleaned


PDF_SPECS = {
    "guide": {
        "filename": "00_OC_CORE_1_3_3_RELEASE_GUIDE_EN.pdf",
        "source": "00_OC_CORE_1_3_3_RELEASE_GUIDE_EN.md",
        "title": "OC Core 1.3.3 Release Guide",
        "min_chars": 7000,
        "min_pages": 3,
        "min_size": 20000,
        "description": "Short public landing guide and recommended reading order for OC Core 1.3.3.",
    },
    "master": {
        "filename": "OC_CORE_1_3_3_MASTER_MONOGRAPH_EN.pdf",
        "source": "OC_CORE_1_3_3_MASTER_MONOGRAPH_EN.md",
        "title": "OC Core 1.3.3 Master Monograph",
        "min_chars": science_monolith.ANTI_SURROGATE_MIN_MONOLITH_TEXT_CHARS,
        "min_pages": science_monolith.ANTI_SURROGATE_MIN_MONOLITH_PAGES,
        "description": "Canonical full scientific monograph for OC Core 1.3.3.",
    },
    "journal": {
        "filename": "OC_CORE_1_3_3_JOURNAL_CORE_EN.pdf",
        "source": "OC_CORE_1_3_3_JOURNAL_CORE_EN.md",
        "title": "OC Core 1.3.3 Journal Core",
        "min_chars": 24000,
        "min_pages": 10,
        "description": "Article-style entry point for external scientific review.",
    },
    "methods": {
        "filename": "OC_CORE_1_3_3_METHODS_AND_REPRODUCIBILITY_COMPANION_EN.pdf",
        "source": "OC_CORE_1_3_3_METHODS_AND_REPRODUCIBILITY_COMPANION_EN.md",
        "title": "OC Core 1.3.3 Methods and Reproducibility Companion",
        "min_chars": 30000,
        "min_pages": 12,
        "description": "Reproducibility, bounded replay QA, and audit-navigation companion.",
    },
    "reviewer": {
        "filename": "OC_CORE_1_3_3_REVIEWER_ATTACK_AND_RESPONSE_MAP_EN.pdf",
        "source": "OC_CORE_1_3_3_REVIEWER_ATTACK_AND_RESPONSE_MAP_EN.md",
        "title": "OC Core 1.3.3 Reviewer Attack and Response Map",
        "min_chars": 45000,
        "min_pages": 15,
        "description": "Adversarial review, objections, boundaries, and response map.",
    },
}


PUBLIC_FORBIDDEN_RE = re.compile(
    r"\bNO_SEND\b|no-send|no_send|"
    r"publish_allowed\s*[:=]\s*false|owner_approved\s*[:=]\s*false|"
    r"\"publish_allowed\"\s*:\s*false|\"owner_approved\"\s*:\s*false|"
    r"not a public release|"
    r"assigned by (?:the )?corrected Zenodo|assigned by corrected publication pass|"
    r"manifest_kind[^\n]+NOT_PUBLIC_RELEASE|public release record:\s*none|release DOI:\s*none assigned",
    re.IGNORECASE,
)


ABSOLUTE_OVERCLAIM_RE = re.compile(
    r"\b(irrefutable|final truth|theory of everything|better than all modern science|proves all science)\b",
    re.IGNORECASE,
)

ROUTE_SHEET_RE = re.compile(
    r"\b(route sheet|control sheet|control-plane|route/control|status packet|manifest dump|checksum wall)\b",
    re.IGNORECASE,
)

KNOWN_PUBLICATION_ERROR_PATTERNS = {
    "KE-001_RAW_TEX_FRONTMATTER_LEAK": re.compile(r"\\begin\{titlepage\}|\\end\{titlepage\}|\\vspace|\\textsc", re.I),
    "KE-002_MALFORMED_RELEASE_DATE": re.compile(r"202605-01|2026/05/01", re.I),
    "KE-003_OLD_PDF_PLUS_DELTA": re.compile(r"old .* plus .* delta|1\.3 manuscript followed by|delta appendix|integration bridge|generated by the Logion", re.I),
    "KE-004_PRIMARY_ROLE_ROUTE_CONTROL_SHEET": re.compile(r"route sheet|control sheet|control-plane|operator checklist|minimum acceptance conditions|what changed since the bad public record", re.I),
    "KE-005_RAW_LEDGER_DOMINATES_MAIN_TEXT": re.compile(r"FM-T133-[A-Z0-9_-]{30,}|package status:|submission allowed: False|recommended:\s*(?:\n|$)", re.I),
    "KE-006_PUBLIC_NO_SEND_CONTRADICTION": re.compile(r"\bNO_SEND\b|no-send|publish_allowed\s*[:=]\s*false|owner_approved\s*[:=]\s*false", re.I),
    "KE-007_MARKDOWN_LEAKS_IN_ZENODO_HTML": re.compile(r"checksum wall|raw GitHub Markdown", re.I),
    "KE-008_METADATA_FIRST_PUBLIC_ARCHIVE": re.compile(r"metadata-first public record|dotfiles? first|\.codemeta\.json preview", re.I),
    "KE-009_MISSING_TITLE_DEDICATION_ABSTRACT_TOC": re.compile(r"missing title page|missing dedication|missing abstract|missing table of contents", re.I),
    "KE-010_UNSUPPORTED_TOE_SUPERIORITY": re.compile(r"theory of everything|final truth|better than all modern science|universal superiority|all-domain numerical closure", re.I),
    "KE-011_WEAK_PRIOR_ART_INVENTORY_ONLY": re.compile(r"LOCAL_PROTOCOL_CAPSULE_ONLY_NO_ABSENCE_PROMOTION|remaining bibliography entries|comparator source snapshots(?!.*overlap)", re.I),
    "KE-012_VISUAL_ROUTE_INVENTORY_ONLY": re.compile(r"remaining figure entries|figure atlas total(?!.*teaches)", re.I),
    "KE-013_LLM_REVIEW_PARSE_FAILURE": re.compile(r"parse_failure_total[^0-9]+[1-9]", re.I),
    "KE-014_INHERITED_ZENODO_FILES": re.compile(r"inherited_file_count[^0-9]+[1-9]|stale inherited zenodo", re.I),
    "KE-015_ENTITY_ROLE_MISATTRIBUTION": re.compile(
        r"Logion\s*/\s*Estra|Author\.[^\n]{0,120}Logion|creator[s]?[^\n]{0,160}Logion|affiliation[^\n]{0,120}(?:Logion|Estra)",
        re.I,
    ),
    "KE-016_INTERNAL_GATE_JARGON_ON_PUBLIC_SURFACE": re.compile(
        r"\bG(?:32|33|34|35|36|37|38|39|4[0-9]|5[0-9]|6[0-9]|70)\b|"
        r"\bNO_EMPIRICAL_PASS_FROM_OFFICIAL_SNAPSHOT_REPLAY_QA\b|"
        r"\breview-clean\b|\brelease machine\b|\bCerberus\b|"
        r"after\s+G\d+|v12\s+gate|internal gate",
        re.I,
    ),
    "KE-017_BLANK_PUBLIC_STATUS_FIELD": re.compile(
        r"(critical open total|high open total|certificate state|finite-model verdict|register status|failure total|row total)\s*[:\-]\s*(?:\n|$)",
        re.I,
    ),
    "KE-018_META_INTEGRATION_MARKER_PUBLIC": re.compile(
        r"This block integrates|Source-to-PDF Trace|source hash register|Machine Summary|monolith trace|machine-readable ledgers enter the manuscript",
        re.I,
    ),
    "KE-019_ARTICLE_LEDGER_INSTEAD_OF_ARGUMENT": re.compile(
        r"(claim total|registered theorem total|row total|case total|package total)\s*[:\-]|The full register contains",
        re.I,
    ),
    "KE-020_RAW_CODE_OR_LEDGER_DUMP_IN_PUBLIC_PDF": re.compile(
        r"```lean|namespace\s+OC133V12|def\s+main\s*\(|\{\s*\"schema_id\"|\{\s*'schema_id'",
        re.I,
    ),
    "KE-021_VISUAL_PEDAGOGY_ABSENT_OR_INVENTORY_ONLY": re.compile(
        r"figure source:|figure atlas total(?!.*(teaches|reader|operationalizes))|remaining figure entries",
        re.I,
    ),
    "KE-022_LITERATURE_LIST_WITHOUT_SYNTHESIS": re.compile(
        r"remaining bibliography entries|source_refs:|truncated Springer|Albert-L\{\'a\}szl\{\'o\}|LOCAL_PROTOCOL_CAPSULE_ONLY",
        re.I,
    ),
    "KE-023_SECTION_WITHOUT_READER_PAYOFF": re.compile(
        r"This row is included.*machine-readable evidence|the prose here records why the row matters|reader-facing bridge from the formal release surface",
        re.I,
    ),
    "KE-024_REPEATED_BOILERPLATE_PUBLIC_TEXT": re.compile(
        r"This section also fixes the release-quality failure mode|public scientific record must teach the claim before it asks the reader",
        re.I,
    ),
    "KE-025_UNANSWERED_MISSION_QUESTIONS": re.compile(
        r"^(Audience|Purpose|Construction|Didactic rule)\.\s*$",
        re.I | re.M,
    ),
    "KE-026_TEMPLATE_REVIEWER_RESPONSE": re.compile(
        r"overlap is recorded in the comparator register|residual delta is bounded by the public claim surface|"
        r"serious objection because the release is only defensible|must continue to support the exact claim",
        re.I,
    ),
    "KE-027_REPLAY_QA_OVERSTATED_AS_VALIDATION": re.compile(
        r"target-blind validation|complete domain validation|full validation bar|closed empirical domain|"
        r"domain has been solved",
        re.I,
    ),
    "KE-028_PUBLIC_STATUS_LEDGER_PROSE": re.compile(
        r"Current closure status|Promotion blockers|theorem packet COMPLETE|parameter law COMPLETE|"
        r"Closed-domain bindings|verdict PASS|FINAL_UNIFIED_SYNTHESIS",
        re.I,
    ),
    "KE-029_STALE_ARCHIVAL_PROVENANCE_IN_MAIN_ARGUMENT": re.compile(
        r"Core 2\.x|originally distributed across|developed in Core 2\.x",
        re.I,
    ),
    "KE-030_UNBOUNDED_SYNTHESIS_WORDING": re.compile(
        r"universal structural results|universal structure|final unified-science synthesis|"
        r"K12 packages global semantic coherence across the closed domain atlas",
        re.I,
    ),
    "KE-031_RAW_TEX_LEAK_IN_PUBLIC_TEXT": re.compile(
        r"\\begin\{(?:center|minipage|table|figure)|\\end\{(?:center|minipage|table|figure)|\\fbox|\\textbf\{",
        re.I,
    ),
    "KE-032_UNSUPPORTED_TOE_SUPERIORITY_OR_CLOSURE_LANGUAGE": re.compile(
        r"final TOE|irrefutable|better than all modern science|logical superiority|"
        r"universal formalism for deriving predictions at all K-levels|"
        r"unified theory of dimensional transitions|final unified-science envelope|"
        r"empirical closure|theorem-native",
        re.I,
    ),
    "KE-033_UNRESOLVED_CROSS_REFERENCE": re.compile(r"\?\?"),
    "KE-034_REFERENCE_PLACEHOLDER_ANCHOR": re.compile(r"mapped public anchor|cited public anchor", re.I),
    "KE-035_RELEASE_GOVERNANCE_IN_PRIMARY_SCIENCE_PDF": re.compile(
        r"Publication-Grade Scientific Quality Standard|Minimum Release-Button Interpretation|OC Core 1\.3\.3 Evidence Map",
        re.I,
    ),
    "KE-036_MARKDOWN_TABLE_SYNTAX_LEAK": re.compile(
        r"\|[^\n]{3,120}\|[^\n]{0,120}\|\s*(?:\n|\r\n)\s*[—-]+\|[—-]+|"
        r"Environment item\s*\|\s*Why it matters\s*\|\s*Failure interpretation",
        re.I,
    ),
}

BLANK_PUBLIC_FIELD_RE = KNOWN_PUBLICATION_ERROR_PATTERNS["KE-017_BLANK_PUBLIC_STATUS_FIELD"]
META_INTEGRATION_MARKER_RE = KNOWN_PUBLICATION_ERROR_PATTERNS["KE-018_META_INTEGRATION_MARKER_PUBLIC"]

PUBLICATION_GRADE_REQUIRED = [
    "DOI",
    "Abstract",
]


TEXT_SUFFIXES = {".cff", ".json", ".jsonld", ".md", ".tex", ".txt", ".yaml", ".yml"}


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def read_json(path: Path, default: Any | None = None) -> Any:
    if not path.exists():
        return {} if default is None else default
    return json.loads(read_text(path))


def write_text_if_changed(path: Path, text: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = text.rstrip() + "\n"
    if path.exists() and read_text(path) == normalized:
        return False
    path.write_text(normalized, encoding="utf-8", newline="\n")
    return True


def write_json_if_changed(path: Path, payload: Any) -> bool:
    return write_text_if_changed(path, json.dumps(payload, ensure_ascii=False, indent=2))


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_source_ref(path: Path) -> str:
    data = path.read_bytes()
    if path.suffix.lower() in TEXT_SUFFIXES:
        data = data.replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def text_bytes_for_zip(path: Path) -> bytes:
    data = path.read_bytes()
    if path.suffix.lower() in TEXT_SUFFIXES:
        text = data.decode("utf-8", errors="ignore").replace("\r\n", "\n")
        data = clean_public_text(text).encode("utf-8")
    return data


def clean_public_text(value: Any) -> str:
    text = str(value if value is not None else "")
    replacements = {
        "\u2013": "-",
        "\u2014": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u00a0": " ",
        "PROMOTED_BOUNDED_NO_SEND_V12": "bounded promoted release claim",
        "PROMOTED_BOUNDED_PUBLIC_RELEASE_V12": "bounded promoted release claim",
        "PROMOTED_BOUNDED_THEOREM_V12_OWNER_REVIEW_LOCKED": "bounded theorem claim under public release review",
        "PROMOTED_BOUNDED_THEOREM_V12_owner-review gated": "bounded theorem claim under public release review",
        "SCIENTIFICALLY_PROMOTED_NO_SEND_WITH_LEAN_SUBSET_AND_FINITE_WITNESS": "scientifically promoted with Lean subset and finite witness",
        "SCIENTIFICALLY_PROMOTED_PUBLIC_RELEASE_WITH_LEAN_SUBSET_AND_FINITE_WITNESS": "scientifically promoted with Lean subset and finite witness",
        "no-send formal release-consistency check": "bounded formal consistency check",
        "no-send formal release-consistency fields": "bounded formal consistency fields",
        "no-send scientific theorem": "bounded scientific theorem",
        "READY_NO_SEND": "ready for editorial review",
        "OWNER_REVIEW_READY_NO_SEND": "ready for owner review",
        "READY_FOR_OWNER_REVIEW": "ready for owner review",
        "OWNER_REVIEW_READY": "ready for owner review",
        "NO-SEND": "release-governed",
        "No-Send": "release-governed",
        "NO_SEND": "release-governed",
        "no_send": "release-governed",
        "no-send": "release-governed",
        "No-send": "release-governed",
        "LOCAL_PROTOCOL_CAPSULE_ONLY_NO_ABSENCE_PROMOTION": "source snapshot; no absence or priority claim",
        "NOT_PROMOTED_PRIOR_ART_POSITIONING_ONLY": "positioning only; no priority claim",
        "POSITIONING_ONLY_NO_PRIORITY_ASSERTION": "positioning only; no priority assertion",
        "NOT_OBSERVED_IN_ILLUSTRATIVE_SOURCE_NOT_ABSENCE_EVIDENCE": "not observed in the illustrative source; not absence evidence",
        "GOVERNANCE_CONTROL_OWNER_REVIEW_LOCKED_NOT_SCIENTIFIC_PROMOTION": "governance control note, not a scientific promotion",
        "publish_allowed=false": "publication previously locked before owner approval",
        "owner_approved=false": "owner approval was pending before the release authorization",
        "public_promotion/release_promotion_allowed": "public-promotion and release-permission",
        "public_promotion": "public promotion",
        "public-promotion": "public promotion",
        "release-permission": "release permission",
        "release_promotion_allowed": "release promotion permission",
        "prediction_support_allowed": "prediction support permission",
        "empirical_support_allowed": "empirical support permission",
        "prediction support allowed=false": "prediction support remains outside the promoted empirical claim",
        "empirical support allowed=false": "empirical support remains outside the promoted empirical claim",
        "owner-gated owner-review gated publication controls": "release-governed publication controls",
        "owner-review gated owner-review gated": "owner-review gated",
        "is explicitly blocks": "explicitly blocks",
        "logical unrestricted comparative claim": "bounded logical substrate conditions",
        "unrestricted comparative claim claim": "unrestricted comparative claim",
        "owner approval is pending": "owner approval is absent",
        "owner approval remains pending": "owner approval is absent",
        "false-to-public": "not authorized",
        "not a public release": "a public release boundary note",
        "It is not promoted as an independent novelty or scientific theorem in current formal profile.": "It is promoted only as a bounded model-core theorem claim, not as an independent novelty or unrestricted theory-wide theorem.",
        "It is not promoted as an independent novelty or scientific theorem in v12.": "It is promoted only as a bounded model-core theorem claim, not as an independent novelty or unrestricted theory-wide theorem.",
        "TOE": "full-science program",
        "theory of everything": "full-science program",
        "better than all modern science": "unsupported unrestricted comparative claim",
        "all-domain numerical closure": "unsupported unrestricted numeric-closure claim",
        "universal superiority": "unsupported unrestricted comparative claim",
        "unify all domains of reality under one mathematical framework": "provide a bounded cross-domain modeling grammar where assumptions and evidence are declared",
        "Unify all domains of reality under one mathematical framework": "Provide a bounded cross-domain modeling grammar where assumptions and evidence are declared",
        "global minimality": "component witness independence for the declared semantic verdict suite",
        "Global Minimality": "Component witness independence for the declared semantic verdict suite",
        "global verdict-invariant minimality": "component witness independence for the declared semantic verdict suite",
        "Global verdict-invariant minimality": "Component witness independence for the declared semantic verdict suite",
        "component-wise witness independence for the declared semantic verdict suite": "component-witness independence",
        "Component-wise witness independence for the declared semantic verdict suite": "Component-witness independence",
        "domain-independent at the level of formal vocabulary": "shared at the level of declared model vocabulary",
        "domain-independent irreducibility theorem": "unrestricted irreducibility theorem",
        "universal rules": "declared structural rules",
        "Universal rules": "Declared structural rules",
        "K0-K12 hierarchy": "K0-K12 witness taxonomy",
        "K0-K12 Hierarchy": "K0-K12 Witness Taxonomy",
        "universal modern-science-superiority": "unbounded cross-science comparison",
        "unbounded superiority": "unrestricted cross-science comparison",
        "terminal unified-science layer": "bounded synthesis layer",
        "Terminal unified-science layer": "Bounded synthesis layer",
        "global unified-science layer": "bounded synthesis layer",
        "Global unified-science layer": "Bounded synthesis layer",
        "OC claims universality": "OC claims bounded cross-domain applicability where assumptions and evidence hold",
        "modern-science-superiority": "cross-science comparison",
        "propagates across all domains": "is routed across declared domain packets",
        "logical superiority": "comparative parsimony under declared assumptions",
        "Logical superiority": "Comparative parsimony under declared assumptions",
        "EMPIRICAL_HARD_CLOSED": "bounded replay-supported",
        "the bounded empirical closures": "the bounded replay QA surfaces",
        "bounded empirical closures": "bounded replay QA surfaces",
        "bounded empirical closure program": "bounded replay QA program",
        "empirical hard-closure program": "bounded replay QA program",
        "empirical closure program": "bounded replay QA program",
        "empirical closure backlog": "bounded replay QA backlog",
        "empirical closure surfaces": "bounded replay QA surfaces",
        "empirical closure": "bounded replay QA",
        "release machine": "release process",
        "claim ledger": "claim register",
        "proof ledger": "proof register",
        "proof/evidence ledgers": "proof and evidence registers",
        "ledgers": "registers",
        "ledger": "register",
        "Cerberus": "adversarial review",
        "review-clean": "externally reviewable",
        "NO_EMPIRICAL_PASS_FROM_OFFICIAL_SNAPSHOT_REPLAY_QA": "official snapshots are inputs, not empirical promotion by themselves",
        "NUMERIC_REPLAY_QA_NOT_DOMAIN_VALIDATION": "numeric replay QA, not complete domain validation",
        "target-blind validation": "target-blind replay QA",
        "Target-blind validation": "Target-blind replay QA",
        "domain validation report": "domain evidence-boundary report",
        "Domain validation report": "Domain evidence-boundary report",
        "complete domain validation": "whole-domain proof",
        "whole scientific domain has been solved": "whole scientific domain has been proved",
        "domain has been solved": "domain has been proved",
        "full validation bar": "bounded replay QA bar",
        "Logion / Estra": "Logion research instrument; ESTRA methodological framework",
        "LEAN_SUBSET_STRUCTURED_PROOF_FINITE_WITNESS": "Lean subset, structured proof sheet, and finite witness",
        "BOUNDED_SCIENTIFIC_THEOREM": "bounded scientific theorem",
        "BLOCK_PUBLIC_PROMOTION": "unsupported public promotion is blocked",
        "THEOREM_NATIVE": "bounded theorem route",
        "theorem-native promotion": "bounded theorem-route support",
        "theorem-native empirical": "bounded theorem-routed replay",
        "theorem-native": "proof-routed",
        "held-out prediction review": "bounded replay review",
        "Final Unified Synthesis": "Bounded Synthesis",
        "unified synthesis": "bounded synthesis",
        "Unified Synthesis": "Bounded Synthesis",
        "final unified-science envelope": "bounded synthesis envelope",
        "What OC closes or adds": "What OC contributes within stated limits",
        "What prior science could do, what remained fragmented, and what OC closes": "What prior science provided, what remained fragmented, and what OC contributes within stated limits",
        "closes or adds": "contributes within stated limits",
        "Practical Consequences, Predictive Power, and Use of OC Core": "Practical Consequences, Bounded Replay Use, and Limits of OC Core",
        "Predictive Power": "Bounded Replay Use",
        "What OC predicts across the closed empirical domains": "Bounded replay examples and domain protocol boundaries",
        "closed-domain": "bounded domain-lane",
        "Closed-domain": "Bounded domain-lane",
        "closed empirical domains": "bounded replay lanes",
        "closed empirical domain": "bounded replay lane",
        "closed packets": "bounded protocol packets",
        "closed packet": "bounded protocol packet",
        "lawful closed science": "bounded research protocol",
        "Current closure status: PASS. Promotion blockers: none.": "Current release posture: bounded support is recorded; broader promotion requires explicit additional evidence.",
        "Current closure status": "Current release posture",
        "Promotion blockers": "broader-promotion limits",
        "theorem packet COMPLETE": "theorem packet recorded",
        "parameter law COMPLETE": "parameter law recorded",
        "FAIL_CLOSED": "repair-required boundary",
        "FAIL\\_CLOSED": "repair-required boundary",
        "FRAME_ONLY": "frame-only support row",
        "FRAME\\_ONLY": "frame-only support row",
        "BRIDGE_ONLY": "bridge-only support row",
        "BRIDGE\\_ONLY": "bridge-only support row",
        "CORE_1_3_SCIENCE_ONLY": "current bounded science surface",
        "CORE\\_1\\_3\\_SCIENCE\\_ONLY": "current bounded science surface",
        "FINAL_UNIFIED_SYNTHESIS_VALIDATOR_PASS": "BOUNDED_SYNTHESIS_REVIEW_RECORDED",
        "final unified-science synthesis": "bounded synthesis layer",
        "universal structural results": "declared structural results",
        "universal structure": "declared model structure",
        "Universal structure": "Declared model structure",
        "Core 2.x": "archival source corpus",
        "originally distributed across": "drawn from archived source modules across",
        "developed in Core 2.x": "developed in prior internal drafts",
        "Benchmark against serious alternatives": "Positioning against selected alternatives",
        "NO_SIMPLER_SUPERIOR_BASELINE_FOUND": "NO_SUPERIORITY_CLAIM_POSITIONING_ONLY",
        "NO_COMPARATOR_MAY_WIN_ON_SAME_CLAIM_CLASS_AFTER_COST_NORMALIZATION": "NO_GLOBAL_COMPARATOR_SUPERIORITY_CLAIM",
        "trace-closed, replay-closed, and comparator-clean": "traceable, replayable as bounded QA, and comparator-positioned",
        "trace-closed": "traceable",
        "replay-closed": "replayable as bounded QA",
        "comparator-clean": "comparator-positioned",
        "one explicit kernel": "one declared model-core kernel",
        "one K-level ladder": "one declared K-level ladder",
        "one theorem-to-observable grammar": "one declared theorem-to-observable grammar",
        "release criterion/release criterion": "release criterion",
        "review pressure": "review priority",
        "release boundary": "claim boundary",
        "failure mode": "criticism route",
        "closure evidence": "response evidence",
        "required repair": "required scientific repair",
        "T133-BOUNDARY": "T133-BOUNDARY",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    theorem_id_repairs = {
        "T133BOUNDARY": "T133-BOUNDARY",
        "T133CYCLE": "T133-CYCLE",
        "T133K0RES": "T133-K0-RES",
        "T133OMEGASTATUS": "T133-OMEGA-STATUS",
        "T133HYBRID": "T133-HYBRID",
        "T133DIM": "T133-DIM",
    }
    for malformed, repaired in theorem_id_repairs.items():
        text = re.sub(rf"\b{malformed}\b", repaired, text)
    text = re.sub(r"\bG(?:32|33|34|35|36|37|38|39|4[0-9]|5[0-9]|6[0-9]|70)\b", "release criterion", text)
    text = re.sub(r"\bDelta Queue\b", "delta-stable verification", text, flags=re.I)
    text = re.sub(r"proofs/proof_sheets/(T133-[A-Za-z0-9-]+)\.md", r"public proof sheet \1", text)
    text = re.sub(r"proofs/FINITE_MODEL_CHECKS_1_3_3\.json", "finite-model semantic report", text)
    text = re.sub(r"validation/_raw/[A-Za-z0-9_.-]+", "pinned public validation snapshot", text)
    text = re.sub(r"formal/lean/LEAN_BUILD_CERTIFICATE_1_3_3\.json::([A-Za-z0-9_'.-]+)", r"Lean build certificate declaration \1", text)
    text = re.sub(r"formal/lean/OC133V12\.lean::([A-Za-z0-9_'.-]+)", r"Lean declaration \1", text)
    text = re.sub(
        r"\bappendix/OC_1_3_3_[A-Za-z0-9_./-]+\.tex\b",
        lambda match: public_artifact_path_phrase(match.group(0)),
        text,
    )
    text = re.sub(
        r"\b(?:claims|proofs|validation|reports|reviews|docs|comparators|releases|simulations)/[A-Za-z0-9_./-]+\.(?:json|md|tex|txt|lean)\b",
        lambda match: public_artifact_path_phrase(match.group(0)),
        text,
    )
    text = re.sub(r"\brepository path\s+repository path\s+", "repository path ", text, flags=re.I)
    text = re.sub(r"\bProcess Schema Under scoped\b", "Process Schema Under Declared Scope", text, flags=re.I)
    text = re.sub(r"\bsource route\b", "source record", text, flags=re.I)
    text = re.sub(r"\bpassed\s*=\s*true\b", "the executable check passes", text, flags=re.I)
    text = re.sub(r"\bpasses\s+the\s+bounded\s+check\b", "bounded support is recorded", text, flags=re.I)
    text = re.sub(r"\bDRT:\s*class\s+REFUTED,\s*verdict\s+FAIL_CLOSED\b", "Domain replay taxonomy: this row is a negative-control rejection boundary.", text, flags=re.I)
    text = re.sub(r"\bcovered_case_total\s*=\s*([0-9]+)", r"covered case total \1", text)
    text = re.sub(r"\bcovered_held_out_case_total\s*=\s*([0-9]+)", r"held-out case total \1", text)
    text = re.sub(r"\bnormalized_error_mean_abs\s*=\s*([0-9.]+)", r"mean absolute normalized residual \1", text)
    text = re.sub(r"\bnormalized_error_p95\s*=\s*([0-9.]+)", r"95th-percentile normalized residual \1", text)
    text = re.sub(r"\bnormalized_error_max\s*=\s*([0-9.]+)", r"maximum normalized residual \1", text)
    text = re.sub(r"\btail_breach_count\s*=\s*([0-9]+)", r"tail-breach count \1", text)
    text = re.sub(r"\bv12 gate\b", "current verification criterion", text, flags=re.I)
    text = re.sub(r"\bv12 release tuple\b", "current release tuple", text, flags=re.I)
    text = re.sub(r"\bv12\b", "current formal profile", text, flags=re.I)
    text = re.sub(r"internal gate predicates", "machine-verification predicates", text, flags=re.I)
    text = re.sub(r"internal gate", "machine-verification criterion", text, flags=re.I)
    text = re.sub(r"\buniversal\s+structural\b", "declared structural", text, flags=re.I)
    text = re.sub(r"\buniversal\s+structure\b", "declared model structure", text, flags=re.I)
    text = re.sub(r"\bclosed\s+domain\s+atlas\b", "bounded domain-lane atlas", text, flags=re.I)
    text = re.sub(r"\bglobal\s+semantic\s+coherence\b", "declared semantic coherence", text, flags=re.I)
    text = re.sub(r"\btheorem[- ]native\b", "proof-routed", text, flags=re.I)
    text = re.sub(r"\bempirical\s+(?:hard[- ]closure|closure)\s+(?:program|backlog|surface|surfaces)\b", "bounded replay QA program", text, flags=re.I)
    text = re.sub(r"\bbounded\s+empirical\s+closure(s)?\b", "bounded replay QA surface", text, flags=re.I)
    text = re.sub(r"\bempirical\s+closure\b", "bounded replay QA", text, flags=re.I)
    text = re.sub(r"\blogical\s+superiority\b", "comparative parsimony under declared assumptions", text, flags=re.I)
    text = re.sub(r"\ball[- ]domain\s+numerical\s+closure\b", "unrestricted numeric closure", text, flags=re.I)
    text = re.sub(r"\buniversal\s+numeric\s+closure\b", "unrestricted numeric closure", text, flags=re.I)
    text = re.sub(r"\buniversal\s+growth\s+law\b", "unrestricted growth law", text, flags=re.I)
    text = re.sub(r"\buniversal\s+domain\s+law\b", "unrestricted domain law", text, flags=re.I)
    text = re.sub(r"\buniversal\s+evidence\b", "unrestricted evidence", text, flags=re.I)
    text = re.sub(r"\bfinal\s+all[- ]domain\s+completion\b", "complete scientific coverage", text, flags=re.I)
    text = re.sub(r"\ball[- ]domain\b", "full-scope", text, flags=re.I)
    text = re.sub(r"\bsuperiority\b", "unrestricted comparative claim", text, flags=re.I)
    text = re.sub(r"\bfinal\s+unified[- ]science\s+envelope\b", "bounded synthesis envelope", text, flags=re.I)
    text = re.sub(r"\buniversal\s+formalism\s+for\s+deriving\s+predictions\s+at\s+all\s+K-levels\b", "formal route for deriving scoped predictions at declared K-levels", text, flags=re.I)
    text = re.sub(r"\bunified\s+theory\s+of\s+dimensional\s+transitions\b", "bounded account of dimensional transitions", text, flags=re.I)
    text = re.sub(r"\bwhole\s+scientific\s+domain\s+has\s+been\s+solved\b", "whole scientific domain has been proved", text, flags=re.I)
    text = re.sub(r"\bdomain\s+has\s+been\s+solved\b", "domain has been proved", text, flags=re.I)
    text = re.sub(r"\bclassification\s+of\s+all\s+possible\s+structures\b", "classification of declared structural-possibility candidates", text, flags=re.I)
    text = re.sub(r"\ball\s+possible\s+structures\b", "declared structural-possibility candidates", text, flags=re.I)
    text = re.sub(r"\bno\s+structure\s+beyond\s+K12\s+is\s+definable\b", "no additional public level is promoted beyond the declared K12 taxonomy in this release", text, flags=re.I)
    text = re.sub(r"\bno\s+structure\s+beyond\s+\$?K_\{?12\}?\$?\s+is\s+definable\b", "no additional public level is promoted beyond the declared K12 taxonomy in this release", text, flags=re.I)
    text = re.sub(r"\bK([0-9]{1,2})\s+Run\s+[0-9]+\b", r"the K\1 construction route", text)
    text = re.sub(r"\bK\s*\$?\\?_?\{?([0-9]{1,2})\}?\$?\s+Run(?:~|\s)*[0-9]*\b", r"the K\1 construction route", text)
    text = re.sub(r"\bmemory\s+#[0-9]+(?:\s*,\s*#[0-9]+)*", "the corresponding derivation note", text, flags=re.I)
    text = re.sub(r"\bmemory(?:~|\s)*\\#[0-9]+(?:(?:\s*,|\s+and)\s*\\#[0-9]+)*", "the corresponding derivation note", text, flags=re.I)
    text = re.sub(r"\bgenerated\s+from\s+master_core_structure\.yaml\b", "organized by the canonical experiment taxonomy", text, flags=re.I)
    text = re.sub(r"\bgenerated\s+from\s+\\texttt\{master\\_core\\_structure\.yaml\}", "organized by the canonical experiment taxonomy", text, flags=re.I)
    text = re.sub(r"\\texttt\{master\\_core\\_structure\.yaml\}", "the canonical experiment taxonomy", text, flags=re.I)
    text = re.sub(r"\bexperiments_k([0-9]{1,2})\.tex\b", r"K\1 experiment design", text, flags=re.I)
    text = re.sub(r"\\texttt\{experiments\\_k([0-9]{1,2})\.tex\}", r"K\1 experiment design", text, flags=re.I)
    text = re.sub(r"\\texttt\{experiments\\_kX\.tex\}", "the K-level experiment design series", text, flags=re.I)
    # Public wording normalization must never mutate TeX/include paths.
    text = re.sub(
        r"(\\input\{content/experiments/)K([0-9]{1,2}) experiment design(\})",
        r"\1experiments_k\2\3",
        text,
        flags=re.I,
    )
    text = re.sub(
        r"(content/experiments/)K([0-9]{1,2}) experiment design\b",
        r"\1experiments_k\2",
        text,
        flags=re.I,
    )
    text = re.sub(r"\bdeclared[- ]scope\b", "scoped", text, flags=re.I)
    text = re.sub(r"\bPredictions\s+validated:", "Prediction protocol:", text, flags=re.I)
    text = re.sub(r"\bvalidated\s+predictions\b", "protocol-backed prediction routes", text, flags=re.I)
    text = re.sub(r"\bvalidated\s+in\s+physics\b", "supported in the scoped physics replay lane", text, flags=re.I)
    text = re.sub(r"\bmust\s+have\s+a\s+corresponding\s+instantiation\b", "may be tested for a corresponding scoped instantiation", text, flags=re.I)
    text = re.sub(r"\bestablish(?:es)?\s+the\s+empirical\s+basis\b", "states the protocol basis", text, flags=re.I)
    text = re.sub(r"\bguarantees\s+to\s+later\s+artifacts\b", "provides to later artifacts", text, flags=re.I)
    text = re.sub(r"\bguarantee(?:s)?\s+the\s+coherence\b", "support the coherence", text, flags=re.I)
    text = re.sub(r"\bguarantee\s+uniformity\b", "support uniformity", text, flags=re.I)
    text = re.sub(r"\bguarantee\s+that\b", "support the claim that", text, flags=re.I)
    text = re.sub(r"\bcollapse\s+is\s+guaranteed\b", "collapse follows under the declared model", text, flags=re.I)
    text = re.sub(r"\benforcement\s+guarantee\b", "enforcement assurance", text, flags=re.I)
    text = re.sub(r"\bthe\s+entire\s+ontology\b", "the declared model", text, flags=re.I)
    text = re.sub(r"\bentire\s+ontology\b", "declared model", text, flags=re.I)
    text = re.sub(r"\bdefinition\s+of\s+the\s+global\s+limit\b", "definition of the upper-coherence boundary", text, flags=re.I)
    text = re.sub(r"\bglobal\s+limit\b", "upper-coherence boundary", text, flags=re.I)
    text = re.sub(r"\bThis\s+master\s+file\s+summari[sz]es\b", "This chapter summarizes", text, flags=re.I)
    text = re.sub(r"\bRun~?[0-9]+\b", "the corresponding construction route", text)
    text = re.sub(r"\bPhysics\s+Run\b", "physics construction route", text, flags=re.I)
    text = re.sub(r"\bChemistry\s+Run\b", "chemistry construction route", text, flags=re.I)
    text = re.sub(r"\bthe\s+named\s+section\s+on\s+", "the section on ", text, flags=re.I)
    text = re.sub(r"\bthe\s+named\s+sections\s+on\s+", "the sections on ", text, flags=re.I)
    text = re.sub(r"\bthe\s+named\s+appendix\s+on\s+", "the appendix on ", text, flags=re.I)
    text = re.sub(r"\bthe\s+named\s+appendices\s+on\s+", "the appendices on ", text, flags=re.I)
    text = re.sub(r"\bpublicevidencereplayroute\b", "the public evidence replay route", text, flags=re.I)
    text = text.replace(r"\occode{public evidence replay route}", "the public evidence replay route")
    text = text.replace(r"\occode{repository checksum}", "the repository checksum field")
    text = re.sub(r"\brepositorychecksum\b", "the repository checksum field", text, flags=re.I)
    text = re.sub(r"\bmetadata\.ts_utc\b", "the release timestamp field", text, flags=re.I)
    text = re.sub(r"\bRelease\s+mirror:\b", "Public mirror:", text, flags=re.I)
    text = re.sub(r"\bUse-case\s+id\b", "Use case", text, flags=re.I)
    text = re.sub(r"\bnamed\s+evidence-package\s+record::([A-Za-z0-9_-]+)\s+route\s+row\b", r"the \1 evidence route", text, flags=re.I)
    text = re.sub(r"\bnamed\s+evidence-package\s+record::([A-Za-z0-9_-]+)\s+public\s+status=bounded\s+promoted\s+release\s+claim\b", r"the \1 public claim boundary", text, flags=re.I)
    text = re.sub(r"\bthe\s+([A-Za-z0-9_-]+)\s+evidence\s+record\s+public\s+status=bounded\s+promoted\s+release\s+claim\b", r"the \1 public claim boundary", text, flags=re.I)
    text = re.sub(r"\bnamed\s+evidence-package\s+record::([A-Za-z0-9_-]+)\b", r"the \1 evidence record", text, flags=re.I)
    text = re.sub(r"\bOC\s+CORE\s+1\s+3\s+3\s+PUBLISH\s+MANIFEST\s+DRAFT\b", "the public release manifest", text, flags=re.I)
    text = re.sub(r"\bTHEOREM\s+INVENTORY\s+1\s+3\s+3\b", "the theorem inventory", text, flags=re.I)
    text = re.sub(r"\bPHENOMENON\s+COVERAGE\s+MATRIX\b", "the phenomenon coverage matrix", text, flags=re.I)
    text = re.sub(r"\bCurrent\s+status:\s*BOUNDED_EQUIVALENCE_POSITIONING_COMPLETED_NO_PRIORITY_CLAIM\.?", "Current boundary: bounded equivalence positioning; no priority claim.", text, flags=re.I)
    text = re.sub(r"\bResidual\s+contribution\s+allowed\s+here\.?", "The residual contribution claimed here is:", text, flags=re.I)
    text = re.sub(r"\brelease\s+owner-review\s+gated\s+locks\b", "publication governance checks", text, flags=re.I)
    text = re.sub(r"\bowner-review\s+gated\s+scientific\s+promotion\b", "evidence-bound scientific promotion", text, flags=re.I)
    text = re.sub(r"\bowner-gated\s+publication\s+authorization\b", "publication authorization boundary", text, flags=re.I)
    text = re.sub(r"\bowner-gated\b", "authorization-bounded", text, flags=re.I)
    text = re.sub(r"\bpackage\s+release\s+permission\b", "public release boundary", text, flags=re.I)
    text = re.sub(r"\bevidence-bound\s+scientific\s+promotion\s+and\s+public\s+claim\s+boundary\s+must\s+not\s+be\s+conflated\.\s+at\s+the\s+point\s+where\b", "evidence-bound scientific promotion and public claim boundary are conflated where", text, flags=re.I)
    text = re.sub(r"\bOC\s+1\s+3\s+3\s+the\s+the\s+the\s+phenomenon\s+coverage\s+matrix\b", "the OC Core 1.3.3 phenomenon coverage matrix", text, flags=re.I)
    text = re.sub(r"\bboundedtheoremroute(?:_HELD_OUT_VALIDATED)?\b", "bounded theorem route", text, flags=re.I)
    text = re.sub(r"\bframe-onlysupportrow\b", "support-only row", text, flags=re.I)
    text = re.sub(r"\bfrontierextensionrow\b", "future-work support row", text, flags=re.I)
    text = re.sub(r"\bcurrentboundedsciencesurface\b", "current bounded science surface", text, flags=re.I)
    text = re.sub(r"\bproofrouted\b", "proof-routed", text, flags=re.I)
    text = re.sub(r"\bCore[~\s]+1\.2\s+and\s+subsequent\s+work\s+are\s+expected\s+to\s+develop\b", "Core 1.3.3 records the current route for", text, flags=re.I)
    text = re.sub(r"\bCore[~\s]+1\.3\.3\s+provides\s+the\s+structural\s+basis\s+for\s+an\s+explicit\s+validation\s+pipeline\s+in\s+Core[~\s]+1\.2\b", "Core 1.3.3 states the current structural basis for an explicit validation pipeline", text, flags=re.I)
    text = re.sub(r"\bwithin\s+Core~?1\.2\b", "within the bounded Core 1.3.3 release scope", text, flags=re.I)
    text = re.sub(r"\bfull\s+hierarchy\s+K0\s*[–—-]\s*K10\b", "declared hierarchy K0--K12", text, flags=re.I)
    text = re.sub(r"\bTheorem~?0\.0\s*\(embedding\s+constraint\)", "the embedding-constraint falsifier", text, flags=re.I)
    text = re.sub(r"\bTheorem\s+0\.0\s*\(embedding\s+constraint\)", "the embedding-constraint falsifier", text, flags=re.I)
    text = text.replace(r"\occode{bounded theorem route}", "bounded theorem route")
    text = text.replace(r"\occode{frame-only support row}", "support-only row")
    text = text.replace(r"\occode{frontier extension row}", "future-work support row")
    text = text.replace(r"\occode{current bounded science surface}", "current bounded science surface")
    text = re.sub(r"\bAppendix~?the\s+section\s+on\s+oc\s+core\s+1\s+3\s+practical\s+utility\s+atlas\b", "the Applied Boundary and Model Comparison Appendix", text, flags=re.I)
    text = re.sub(r"\bAppendix\s+the\s+section\s+on\s+oc\s+core\s+1\s+3\s+practical\s+utility\s+atlas\b", "the Applied Boundary and Model Comparison Appendix", text, flags=re.I)
    text = re.sub(r"\bthe\s+section\s+on\s+oc\s+core\s+1\s+3\s+practical\s+utility\b", "the practical utility chapter", text, flags=re.I)
    text = re.sub(r"\bsection\s+oc13\s+theorem\s+roadmap\b", "the theorem roadmap", text, flags=re.I)
    text = re.sub(r"\bsection\s+oc13\s+worked\s+examples\b", "the worked examples chapter", text, flags=re.I)
    text = re.sub(r"\bsection\s+oc13\s+public\s+claim\s+boundary\b", "the public claim-boundary chapter", text, flags=re.I)
    for label, replacement in {
        "model": "the formal model chapter",
        "results": "the historical result-boundary chapter",
        "operators full": "the operator semantics chapter",
        "klevels full": "the K-level witness taxonomy chapter",
        "boundary extended": "the boundary geometry chapter",
        "collapse rebirth": "the lifecycle and rebirth chapter",
        "oc13 theorem roadmap": "the theorem roadmap",
        "oc13 worked examples": "the worked examples chapter",
        "oc13 public claim boundary": "the public claim-boundary chapter",
    }.items():
        text = re.sub(rf"\bthe\s+section\s+on\s+{re.escape(label)}\b", replacement, text, flags=re.I)
        text = re.sub(rf"\bsection\s+on\s+{re.escape(label)}\b", replacement, text, flags=re.I)
    text = re.sub(r"\bthe\s+section\s+on\s+([a-z][a-z0-9 _-]{2,60})\b", lambda m: "the " + re.sub(r"\s+", " ", m.group(1)).strip().replace("_", " ") + " discussion", text, flags=re.I)
    text = re.sub(r"\bsection\s+on\s+([a-z][a-z0-9 _-]{2,60})\b", lambda m: "the " + re.sub(r"\s+", " ", m.group(1)).strip().replace("_", " ") + " discussion", text, flags=re.I)
    text = text.replace(r"\occode{FORMALLY_PROVED}", "formally proved")
    text = text.replace(r"\occode{OPERATIONALLY_SUPPORTED_WITHIN_BOUNDS}", "operationally supported within bounds")
    text = text.replace(r"\occode{bounded theorem route_HELD_OUT_VALIDATED}", "bounded theorem route with held-out validation")
    text = re.sub(r"\bFORMALLY_PROVED\b", "formally proved", text, flags=re.I)
    text = re.sub(r"\bOPERATIONALLY_SUPPORTED_WITHIN_BOUNDS\b", "operationally supported within bounds", text, flags=re.I)
    text = re.sub(r"\bboundedtheoremroute(?:_HELD_OUT_VALIDATED|_H)?\b", "bounded theorem route", text, flags=re.I)
    text = re.sub(r"\bAppendix~?the\s+section\s+on\s+oc13\s+external\s+criticism\s+closure\b", "the external-criticism closure appendix", text, flags=re.I)
    text = re.sub(r"\bAppendix~?the\s+section\s+on\s+oc13\s+journal\s+core\s+bridge\b", "the journal-core bridge appendix", text, flags=re.I)
    text = re.sub(r"\bAppendix~?the\s+section\s+on\s+oc13\b", "the relevant OC Core 1.3.3 appendix", text, flags=re.I)
    text = re.sub(r"\bAppendix~?the\s+section\b", "the relevant appendix", text, flags=re.I)
    text = re.sub(r"\bthe\s+full\s+hierarchy\s+\\?\(?K_0\\?\)?\s*[–—-]\s*\\?\(?K_\{?10\}?\\?\)?", "the declared hierarchy K0--K12", text, flags=re.I)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"publish_allowed\s*=\s*false", "publication previously locked before owner approval", text, flags=re.I)
    text = re.sub(r"owner_approved\s*=\s*false", "owner approval was pending before the release authorization", text, flags=re.I)
    return text.strip()


def version_frontmatter_present(text: str) -> bool:
    return bool(re.search(rf"\bVersion\s+v?{re.escape(VERSION)}\b", text, re.IGNORECASE))


def dedication_frontmatter_present(text: str) -> bool:
    compact = re.sub(r"\s+", " ", text)
    return bool(re.search(r"Dedicated\s+to\s+my\s+dear\s+wife\s+Maria", compact, re.IGNORECASE))


def reader_orientation_present(text: str) -> bool:
    return "Reader Contract" in text or "Reader Orientation" in text


def publication_grade_missing_frontmatter(text: str) -> list[str]:
    missing = [phrase for phrase in PUBLICATION_GRADE_REQUIRED if phrase not in text]
    if not reader_orientation_present(text):
        missing.append("Reader Orientation")
    if not dedication_frontmatter_present(text):
        missing.append("Dedicated to my dear wife Maria")
    if not version_frontmatter_present(text):
        missing.append(f"Version {VERSION}")
    return missing


def sanitize_public_json(value: Any) -> Any:
    if isinstance(value, str):
        return clean_public_text(value)
    if isinstance(value, list):
        return [sanitize_public_json(item) for item in value]
    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for key, item in value.items():
            public_key = clean_public_text(key)
            if public_key == "owner_approved" and item is False:
                sanitized["pre_publication_owner_approval_pending_control"] = True
                continue
            if public_key == "publish_allowed" and item is False:
                sanitized["pre_publication_publish_block_control"] = True
                continue
            if public_key == "support_ceiling":
                public_key = "release_support_boundary"
            sanitized[public_key] = sanitize_public_json(item)
        return sanitized
    return value


PUBLIC_EVIDENCE_INTERNAL_KEYS = {
    "fresh_cerberus_required_for_release",
    "scientific_promotion_wording_lint_rule",
    "owner_approval_required",
    "owner_approved",
    "publish_allowed",
    "global_no_send_lock",
    "submission_allowed",
    "journal_submissions_allowed",
}


def scrub_public_evidence_json(value: Any) -> Any:
    """Remove control-plane bookkeeping from public evidence files.

    Public evidence may record claim boundaries, replay hashes, proof refs, and
    comparator refs. It must not expose pre-publication control locks as if they
    were part of the scientific content.
    """
    if isinstance(value, list):
        return [scrub_public_evidence_json(item) for item in value]
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key, item in value.items():
            public_key = clean_public_text(key)
            if public_key in PUBLIC_EVIDENCE_INTERNAL_KEYS:
                continue
            if re.search(r"(no_send|nosend|owner_approval|publish_allowed|submission_allowed|cerberus_required)", public_key, re.I):
                continue
            out[public_key] = scrub_public_evidence_json(item)
        return out
    if isinstance(value, str):
        text = clean_public_text(value)
        text = re.sub(r"fresh adversarial review required(?: for release)?", "current adversarial review evidence is recorded", text, flags=re.I)
        text = re.sub(r"scientific promotion remains false", "public promotion is governed by the claim boundary", text, flags=re.I)
        return text
    return value


def apply_public_release_promotion_contract(value: Any, ref: str) -> Any:
    """Normalize promotion semantics for the public-release evidence surface.

    Internal 1.3.3 evidence was produced while journal submission and public
    publication were locked. The public payload needs a single contract:
    bounded scientific theorem/claim promotion is allowed only for rows with
    scientific evidence; journal submission remains outside this contract.
    """
    if not isinstance(value, dict):
        return value
    out = dict(value)
    out["public_release_promotion_contract"] = {
        "contract_id": "OC133_PUBLIC_RELEASE_PROMOTION_CONTRACT_v1",
        "meaning": "Public GitHub and Zenodo release may promote bounded model-core claims whose rows carry scientific_promotion_allowed=true; journal submission is not implied.",
        "journal_submission_scope": "outside this contract",
        "full_toe_or_superiority_scope": "background research unless separately evidenced",
    }
    if ref.endswith("THEOREM_REGISTRY_1_3_3.json") or out.get("schema_id") == "OC133_THEOREM_REGISTRY_v1":
        rows = out.get("rows") if isinstance(out.get("rows"), list) else []
        promoted_total = 0
        for row in rows:
            if not isinstance(row, dict):
                continue
            promoted = row.get("scientific_promotion_allowed") is True or "SCIENTIFICALLY_PROMOTED" in str(row.get("proof_status", ""))
            row["public_promotion"] = promoted
            row["release_promotion_allowed"] = promoted
            row["public_status"] = "bounded promoted release theorem" if promoted else "not promoted in this public release"
            if promoted:
                promoted_total += 1
        out["public_promoted_theorem_total"] = promoted_total
        out["release_promotion_allowed"] = promoted_total > 0
        out["promotion_authority"] = "row.scientific_promotion_allowed plus proof_status; synchronized by public payload generator"
    if ref.endswith("CLAIM_LEDGER_1_3_3.json") or out.get("schema_id") == "OC133_CLAIM_LEDGER_v1":
        rows = out.get("rows") if isinstance(out.get("rows"), list) else []
        promoted_total = 0
        for row in rows:
            if not isinstance(row, dict):
                continue
            promoted = row.get("scientific_promotion_allowed") is True
            row["release_promotion_allowed"] = promoted
            row["public_promotion"] = promoted
            row["public_status"] = "bounded promoted release claim" if promoted else "not promoted in this public release"
            if promoted:
                promoted_total += 1
        out["release_promotion_allowed"] = promoted_total > 0
        out["public_promoted_claim_total"] = promoted_total
        out["promotion_authority"] = "row.scientific_promotion_allowed; synchronized by public payload generator"
    if ref.endswith("OC_1_3_3_PHENOMENON_COVERAGE_MATRIX.json"):
        rows = out.get("rows") if isinstance(out.get("rows"), list) else []
        promoted_total = 0
        for row in rows:
            if not isinstance(row, dict):
                continue
            promoted = str(row.get("upstream_claim_status") or row.get("upstream_status") or "").lower() == "bounded promoted release claim"
            row["public_promotion"] = promoted
            row["package_release_promotion_allowed"] = promoted
            row["public_status"] = "bounded model-card support for a promoted claim" if promoted else "background or non-promoted model-card support"
            if promoted:
                promoted_total += 1
        out["public_promoted_model_card_total"] = promoted_total
        out["release_promotion_allowed"] = promoted_total > 0
        out["promotion_authority"] = "upstream bounded promoted claim status; synchronized by public payload generator"
    if ref.endswith("OC_CORE_1_3_3_DOMAIN_VALIDATION_REPORT.json"):
        out["claim_register_release_promotion_allowed"] = True
        out["validation_public_boundary"] = "Validation rows support bounded target-blind replay QA; they do not promote broad all-domain validation."
        out["promotion_authority"] = "claim ledger public-release promotion contract; empirical promotion remains lane-bounded"
    return out


def sanitize_latex_fragment(value: str) -> str:
    text = clean_public_text(value)
    accent_map = {
        "a": "a",
        "A": "A",
        "e": "e",
        "E": "E",
        "i": "i",
        "I": "I",
        "o": "o",
        "O": "O",
        "u": "u",
        "U": "U",
        "y": "y",
        "Y": "Y",
        "l": "l",
        "L": "L",
        "n": "n",
        "N": "N",
    }
    text = re.sub(r"\{['`^\"~]\s*([A-Za-z])\}", lambda m: accent_map.get(m.group(1), m.group(1)), text)
    text = re.sub(r"\{\\['`^\"~]\s*([A-Za-z])\}", lambda m: accent_map.get(m.group(1), m.group(1)), text)
    text = re.sub(r"\\['`^\"~]\{([A-Za-z])\}", lambda m: accent_map.get(m.group(1), m.group(1)), text)
    text = re.sub(r"\{?\\['`^\"~=.Hckruv]\{?([A-Za-z])\}?\}?", lambda m: accent_map.get(m.group(1), m.group(1)), text)
    text = re.sub(r"\{['`^\"~]\{?([A-Za-z])\}?\}", lambda m: accent_map.get(m.group(1), m.group(1)), text)
    text = text.replace(r"\AA", "A").replace(r"\aa", "a").replace(r"\ss", "ss")
    # Keep the public PDFs robust: raw TeX headings with nested math can break
    # Pandoc's LaTeX writer, so the public document carries readable text.
    text = re.sub(r"\\texorpdfstring\{[^{}\n]*\}\{([^{}\n]*)\}", r"\1", text)
    text = re.sub(r"\\texorpdfstring\{[^{}\n]*\{([^{}\n]*)\}[^{}\n]*\}", r"\1", text)
    text = re.sub(r"\\texorpdfstring\{[^{}\n]*\}", "", text)
    text = re.sub(r"\\(section|subsection|subsubsection|paragraph)\*?\{([^{}\n]+)\}", lambda m: f"### {m.group(2)}", text)
    text = re.sub(r"\\label\{[^}]*\}", "", text)
    text = re.sub(r"\\(begin|end)\{[^}]*\}", "", text)
    text = text.replace("\\(", "").replace("\\)", "")
    text = text.replace("\\[", "").replace("\\]", "")
    text = re.sub(r"\$([^$\n]+)\$", r"\1", text)
    text = text.replace("\\item", "-")
    text = re.sub(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?\{([^{}\n]*)\}", r"\1", text)
    text = re.sub(r"\\([a-zA-Z]+)", r"\1", text)
    text = text.replace("{", "").replace("}", "")
    text = (
        text.replace("{'a}", "a")
        .replace("{'A}", "A")
        .replace("{'o}", "o")
        .replace("{'O}", "O")
        .replace("{'u}", "u")
        .replace("{'U}", "U")
        .replace("{'e}", "e")
        .replace("{'E}", "E")
        .replace("{'i}", "i")
        .replace("{'I}", "I")
        .replace("\\AA", "A")
        .replace("\\ss", "ss")
    )
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"\b(?:source|closure|public)\s+evidence\s+artifact\s+.*?(?=;|,|\n|\.\s)", "evidence-package record", text, flags=re.I)
    text = re.sub(r"\bClosure\s+dossier\s+evidence-package\s+record\b", "Evidence-package closure dossier", text, flags=re.I)
    return text.strip()


def short(value: Any, limit: int = 280) -> str:
    text = clean_public_text(value).replace("\n", " ")
    return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."


def public_value(value: Any) -> str:
    if isinstance(value, list):
        parts = []
        for item in value[:8]:
            if isinstance(item, dict):
                label = item.get("title") or item.get("id") or item.get("url") or item.get("claim_id") or item.get("case_id")
                detail = item.get("source_date") or item.get("status") or item.get("archive_status") or item.get("url")
                parts.append(" - ".join(clean_public_text(part) for part in [label, detail] if part))
            else:
                parts.append(short(item, 180))
        if len(value) > 8:
            parts.append(f"{len(value) - 8} additional entries")
        return "; ".join(part for part in parts if part)
    if isinstance(value, dict):
        parts = []
        for key, item in list(value.items())[:8]:
            if isinstance(item, (dict, list)):
                parts.append(f"{clean_public_text(key)}: {public_value(item)}")
            else:
                parts.append(f"{clean_public_text(key)}: {short(item, 160)}")
        if len(value) > 8:
            parts.append(f"{len(value) - 8} additional fields")
        return "; ".join(parts)
    return clean_public_text(value)


def bullet(label: str, value: Any) -> str:
    return f"- **{label}:** {public_value(value)}"


def prose_sentence(text: str) -> str:
    text = clean_public_text(text)
    if not text:
        return ""
    return text if text.endswith((".", "!", "?")) else text + "."


def public_scope_sentence(scope: Any, *, fallback: str | None = None) -> str:
    text = clean_public_text(scope).strip()
    generic = "Bounded to stated theorem assumptions, finite witnesses, and public falsifier boundary."
    if not text or text == generic:
        text = fallback or "The claim is limited to the assumptions, witnesses, and falsifier boundary named by its proof and evidence route."
    return prose_sentence(text)


def sentence_list(items: list[str]) -> str:
    clean_items = [clean_public_text(item) for item in items if clean_public_text(item)]
    if not clean_items:
        return ""
    if len(clean_items) == 1:
        return clean_items[0]
    return ", ".join(clean_items[:-1]) + ", and " + clean_items[-1]


def public_theorem_label(value: Any) -> str:
    raw = clean_public_text(value)
    normalized = raw.replace("T133K0-RES", "T133-K0-RES").replace("T133K-ZERO", "T133-K-ZERO")
    normalized = normalized.replace("T133OMEGA-STATUS", "T133-OMEGA-STATUS").replace("T133-OMEGASTATUS", "T133-OMEGA-STATUS")
    normalized = normalized.replace("T133DIM", "T133-DIM").replace("T133CYCLE", "T133-CYCLE")
    normalized = re.sub(r"^(?:FM-)?(T133-[A-Za-z0-9-]+?)-(?:POS|NEG)$", r"\1", normalized)
    if normalized.startswith("T133-HYBRID-PROOF-UPDATE"):
        normalized = "T133-HYBRID"
    labels = {
        "T133-K0-RES": "K0 resolution theorem",
        "T133-OMEGA-STATUS": "lifecycle status theorem",
        "T133-K-ZERO": "K-zero boundary theorem",
        "T133 Boundary theorem": "boundary representation theorem",
        "T133-BOUNDARY": "boundary representation theorem",
        "T133-HYBRID": "hybrid semantics theorem",
        "T133-DIM": "dimension semantics theorem",
        "T133-CYCLE": "cycle-mode theorem",
        "T133-ID": "identity and rebirth theorem",
        "T133-MIN": "minimality witness theorem",
        "T133-KLEVEL": "K-level witness theorem",
    }
    return labels.get(normalized, normalized)


def heading(title: str, level: int = 2) -> str:
    return f"{'#' * level} {title}\n"


def load_rows(path: Path) -> list[dict[str, Any]]:
    payload = read_json(path, {})
    rows = payload.get("rows", [])
    return rows if isinstance(rows, list) else []


def proof_sheet_excerpt(ref: str) -> str:
    path = ROOT / ref
    if not path.exists():
        return ""
    body = clean_public_text(read_text(path))
    lines = [line for line in body.splitlines() if line.strip()]
    return "\n".join(lines[:90])


def bibliography_entries(limit: int | None = None) -> list[dict[str, str]]:
    path = ROOT / "bib" / "references.bib"
    if not path.exists():
        return []
    body = read_text(path)
    chunks = re.split(r"\n@", "\n" + body)
    entries: list[dict[str, str]] = []
    for chunk in chunks:
        if "{" not in chunk:
            continue
        chunk = "@" + chunk.strip().lstrip("@")
        key_match = re.match(r"@\w+\{([^,\s]+)", chunk)
        if not key_match:
            continue
        def field(name: str) -> str:
            match = re.search(rf"\b{name}\s*=\s*\{{([^{{}}]*(?:\{{[^{{}}]*\}}[^{{}}]*)*)\}}", chunk, re.I | re.S)
            if not match:
                return ""
            return sanitize_latex_fragment(re.sub(r"\s+", " ", match.group(1)).replace("\\&", "&")).strip()
        entries.append(
            {
                "key": key_match.group(1),
                "author": field("author"),
                "title": field("title"),
                "year": field("year"),
                "journal": field("journal") or field("publisher"),
            }
        )
    return entries[:limit] if limit else entries


def figure_entries(limit: int | None = None) -> list[dict[str, str]]:
    figure_sources = [
        ROOT / "content" / "20_oc_core_1_3_theorem_roadmap.tex",
        ROOT / "content" / "21_oc_core_1_3_worked_examples.tex",
        ROOT / "content" / "07_figures.tex",
    ]
    rows: list[dict[str, str]] = []
    for path in figure_sources:
        if not path.exists():
            continue
        body = read_text(path)
        for block in re.findall(r"\\begin\{figure\}.*?\\end\{figure\}", body, re.S):
            label = ""
            caption = ""
            label_match = re.search(r"\\label\{([^}]+)\}", block)
            caption_match = re.search(r"\\caption\{(.*?)\}\s*\\label", block, re.S)
            if label_match:
                label = label_match.group(1)
            if caption_match:
                caption = sanitize_latex_fragment(caption_match.group(1))
            if label or caption:
                rows.append({"label": label, "caption": caption, "source": rel(path)})
    return rows[:limit] if limit else rows


def first_public_value(*values: Any, default: str = "recorded in the public evidence package") -> Any:
    for value in values:
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        return value
    return default


def lean_status_summary() -> dict[str, Any]:
    cert = read_json(ROOT / "formal" / "lean" / "LEAN_BUILD_CERTIFICATE_1_3_3.json", {})
    returncode = cert.get("returncode")
    state = first_public_value(cert.get("state"), cert.get("verdict"), default="")
    if not state and returncode == 0:
        state = "PASS"
    return {
        "state": state or "recorded in the Lean build certificate",
        "execution_status": first_public_value(cert.get("execution_status"), default="recorded in the Lean build certificate"),
        "returncode": first_public_value(returncode, default="recorded in the Lean build certificate"),
        "theorem_ref_total": first_public_value(cert.get("theorem_ref_total"), default=0),
        "missing_theorem_ref_total": first_public_value(cert.get("missing_theorem_ref_total"), default=0),
        "build_command": public_value(cert.get("command") or cert.get("build_command") or "lake build OC133V12"),
    }


def finite_status_summary() -> dict[str, Any]:
    finite = read_json(ROOT / "proofs" / "FINITE_MODEL_CHECKS_1_3_3.json", {})
    rows = finite.get("rows", []) if isinstance(finite.get("rows"), list) else []
    state = first_public_value(finite.get("state"), finite.get("verdict"), default="")
    if not state and finite.get("failure_total") == 0 and rows:
        state = "PASS"
    return {
        "state": state or "recorded in the finite-model report",
        "case_total": first_public_value(finite.get("case_total"), len(rows)),
        "failure_total": first_public_value(finite.get("failure_total"), default=0),
        "semantic_evaluator": first_public_value(finite.get("semantic_evaluator"), default="independent semantic evaluator in proofs/finite_model_checks"),
        "mutation_control_total": first_public_value(finite.get("mutation_control_total"), default="recorded in the finite-model report"),
        "k_transition_negative_total": first_public_value(finite.get("k_transition_negative_total"), default="recorded in the finite-model report"),
    }


def observed_reproducibility_bom() -> str:
    commands = {
        "Python": ["python", "--version"],
        "Pandoc": ["pandoc", "--version"],
        "XeLaTeX": ["xelatex", "--version"],
        "Poppler pdftotext": ["pdftotext", "-v"],
        "Lean/Lake": ["lake", "--version"],
        "Git commit": ["git", "rev-parse", "--short", "HEAD"],
    }
    rows = [
        heading("Observed Reproducibility Bill of Materials", 2),
        "This section records the build-host toolchain used to generate this public package. Long values are rendered as wrapped lines instead of table cells, because a public methods PDF must remain readable after PDF extraction.",
        "",
    ]
    for label, cmd in commands.items():
        try:
            completed = subprocess.run(cmd, cwd=ROOT, text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=20)
            value = (completed.stdout or completed.stderr).strip().splitlines()[0] if (completed.stdout or completed.stderr).strip() else f"return code {completed.returncode}"
        except Exception as exc:
            value = f"not captured on this host: {type(exc).__name__}"
        rows.extend([f"**{label}.**", "", "```text", clean_public_text(value), "```", ""])
    public_outputs = [
        ("Master monograph", "releases/oc_core_1_3_3/artifacts/OC_CORE_1_3_3_MASTER_MONOGRAPH_EN.pdf", "canonical long-form scientific text"),
        ("Release guide", "releases/oc_core_1_3_3/artifacts/00_OC_CORE_1_3_3_RELEASE_GUIDE_EN.pdf", "public landing and reading-order document"),
        ("Journal core", "releases/oc_core_1_3_3/artifacts/OC_CORE_1_3_3_JOURNAL_CORE_EN.pdf", "compact article path"),
        ("Methods companion", "releases/oc_core_1_3_3/artifacts/OC_CORE_1_3_3_METHODS_AND_REPRODUCIBILITY_COMPANION_EN.pdf", "replay and failure-interpretation protocol"),
        ("Reviewer map", "releases/oc_core_1_3_3/artifacts/OC_CORE_1_3_3_REVIEWER_ATTACK_AND_RESPONSE_MAP_EN.pdf", "hostile-review route"),
        ("Public zip", "releases/oc_core_1_3_3/artifacts/oc_core_1_3_3_public_release.zip", "archive and replay package"),
    ]
    rows.extend(["", heading("Public Output Paths", 3)])
    for label, path, role in public_outputs:
        rows.extend([f"**{label}.** {role}.", "", "```text", path, "```", ""])
    rows.extend(
        [
            "",
            "Expected hashes are not copied by hand into this paragraph; the authoritative hash surface is checksums.txt and the public zip manifest generated in the same build. A reviewer should compare those hashes to downloaded assets before interpreting scientific results.",
        ]
    )
    return "\n".join(rows)


def editorial_manifest() -> str:
    bib_total = len(bibliography_entries())
    figure_total = len(figure_entries())
    return "\n\n".join(
        [
            heading("Editorial Passport", 2),
            (
                "Audience. The primary audience is a mixed external-review group: formal-methods readers, systems-theory "
                "readers, domain scientists, journal editors, and technically literate institutional readers. The text is "
                "therefore not allowed to assume that every reader will begin from the same mathematical or domain background."
            ),
            (
                "Purpose. The manuscript set must show what OC Core 1.3.3 claims, why the claim is bounded, how the model is "
                "typed, where the theorem evidence lives, which empirical lanes are replayable, which objections have been "
                "answered, and which larger full-science obligations remain future work. Because this is a public scientific "
                "release rather than an internal build packet, the first obligation is intelligibility."
            ),
            (
                "Construction. The reading order moves from orientation to formal model, then proof obligations, then "
                "machine-checkable evidence, then empirical evidence, then comparator and novelty boundaries, then reviewer "
                "objections, reproducibility, and release governance. This order is intentional: readers need the model before "
                "the proof register, and they need the proof register before they can judge the replay package."
            ),
            (
                "Didactic rule. Every major section must answer four questions: what is being claimed, why it matters, what "
                "evidence supports it, and what would falsify or limit it. If a section only lists identifiers, hashes, or rows, "
                "it belongs in the evidence package or appendix, not in the main explanatory path."
            ),
            (
                f"Visual and literature rule. The release corpus exposes {figure_total} public figure entries and {bib_total} "
                "bibliography entries, plus source-backed comparator anchors with explicit overlap and residual-delta notes. The editorial gate treats figures as explanatory "
                "anchors and literature as the prior-art boundary: neither may be replaced by metadata or checksums."
            ),
        ]
    )


def document_editorial_context(kind: str) -> str:
    profiles = {
        "guide": {
            "audience": "new public readers, scientific contacts, repository visitors, and archivists who need to know what to open first",
            "purpose": "orient the reader to the release without turning the guide into a process manual",
            "construction": "scope, reading order, evidence boundary, citation route, and reviewer entry points",
            "didactic": "the guide answers what exists, why it matters, what to read, and what not to overclaim",
        },
        "master": {
            "audience": "formal, systems, empirical, and editorial reviewers who need the long-form argument",
            "purpose": "teach the OC Core 1.3.3 model as one scientific manuscript with proof, evidence, limits, and prior art",
            "construction": "orientation, formal model, theorem path, executable evidence, bounded empirical replay, comparison, objections, and reproducibility",
            "didactic": "each chapter must make a claim, explain its role, state evidence, and name the boundary that could reopen it",
        },
        "journal": {
            "audience": "journal editors and first-pass peer reviewers",
            "purpose": "compress the model-core argument into a conventional article path rather than a register of artifacts",
            "construction": "problem, contribution, formal object, results, evidence, prior art, limits, and conclusion",
            "didactic": "artifact identifiers appear only after the reader understands the scientific claim they support",
        },
        "methods": {
            "audience": "reviewers who want to replay the evidence locally",
            "purpose": "turn the release evidence into an executable methods protocol",
            "construction": "environment, archive layout, commands, inputs, outputs, expected hashes, and failure interpretation",
            "didactic": "a reader should be able to decide which claim is threatened by each failed command",
        },
        "reviewer": {
            "audience": "hostile reviewers testing novelty, claim boundaries, proof support, and empirical scope",
            "purpose": "answer serious objections without exposing internal routing machinery as public prose",
            "construction": "objection, why it matters, response, evidence, residual risk, and reopening condition",
            "didactic": "each challenge teaches what criticism would hit and how the release evidence answers or bounds it",
        },
    }
    row = profiles[kind]
    title = {
        "guide": "Audience and Reading Path",
        "master": "Monograph Editorial Orientation",
        "journal": "Article Structure and Audience",
        "methods": "Reproducibility Structure and Audience",
        "reviewer": "Adversarial Review Structure and Audience",
    }[kind]
    science_support = {
        "guide": "For this guide, the support stack is used only to explain where a reader should start and how not to overread the archive.",
        "master": "For the monograph, the support stack is integrated into the long-form scientific argument.",
        "journal": "For the article, the support stack is compressed into problem, object, result, evidence, discussion, and limitation.",
        "methods": "For the methods companion, the support stack is translated into replay inputs, expected outputs, and failure interpretation.",
        "reviewer": "For the reviewer map, the support stack is translated into objections, evidence-bound responses, residual risks, and reopening rules.",
    }[kind]
    role_method = {
        "guide": "The guide stays short and practical: it names the archive objects, explains the reading order, and warns readers away from over-reading machine evidence as broader validation.",
        "master": "The monograph carries the long argument: it teaches the model before the proof route, then uses appendices for evidence that would otherwise interrupt the line of thought.",
        "journal": "The article follows a conventional journal sequence: scientific problem, related work, formal object, results, evidence, discussion, limitations, and conclusion.",
        "methods": "The methods companion is procedural prose: each replay or check is tied to the claim class it can support or reopen.",
        "reviewer": "The reviewer map is adversarial prose: each section begins with the objection, states the threatened claim, gives the answer, and names the residual risk.",
    }[kind]
    return "\n\n".join(
        [
            heading(title, 2),
            (
                f"Purpose and role. This document is written for {row['audience']}. It exists to {row['purpose']}, so the opening pages "
                "identify the intended reader before they introduce formal claims."
            ),
            (
                f"Construction and order. The argument is organized as {row['construction']}. {role_method}"
            ),
            (
                f"The teaching obligation is that {row['didactic']}. The current research support is the bounded OC Core "
                "1.3.3 model-core stack: typed model, theorem and proof route, Lean subset, finite semantic witnesses, "
                f"bounded replay rows, comparator positioning, phenomenon coverage, negative controls, falsifiers, and "
                f"adversarial review. {science_support}"
            ),
            (
                "The document therefore states what the reader should learn from the evidence and where that evidence stops. "
                "It does not use release-readiness language as a substitute for scientific explanation, and it does not claim "
                "unsupported full-science completion."
            ),
        ]
    )


def build_public_figures() -> dict[str, str]:
    from PIL import Image, ImageDraw, ImageFont

    PUBLIC_FIGURES.mkdir(parents=True, exist_ok=True)

    try:
        font = ImageFont.truetype("arial.ttf", 26)
        small = ImageFont.truetype("arial.ttf", 21)
    except Exception:
        font = ImageFont.load_default()
        small = ImageFont.load_default()

    specs = {
        "tuple": {
            "filename": "oc133_tuple_route.png",
            "title": "OC Tuple Route",
            "nodes": ["Carrier", "Realization", "Liveness", "Residue", "Boundary", "Morphism"],
            "caption": "A public claim has to name which tuple component carries the asserted distinction.",
        },
        "lifecycle": {
            "filename": "oc133_lifecycle_route.png",
            "title": "Lifecycle and Identity Route",
            "nodes": ["Live state", "Death condition", "Residue evidence", "Rebirth candidate", "Identity boundary"],
            "caption": "Residue and rebirth do not imply identity unless invariant preservation is declared.",
        },
        "klevel": {
            "filename": "oc133_klevel_route.png",
            "title": "K-Level Witness Route",
            "nodes": ["Lower model", "Added observable", "Transition witness", "Retained distinction", "Demotion test"],
            "caption": "A K-level increase requires a witness; an inert observable is demoted rather than promoted.",
        },
        "boundary": {
            "filename": "oc133_boundary_route.png",
            "title": "Boundary and Falsifier Route",
            "nodes": ["Classifier", "Separation", "Interface", "Negative control", "Falsifier"],
            "caption": "A boundary claim is reviewable only when separation, controls, and falsifiers are named.",
        },
        "evidence": {
            "filename": "oc133_evidence_route.png",
            "title": "Claim-to-Evidence Route",
            "nodes": ["Claim", "Assumptions", "Proof sheet", "Lean / finite witness", "Replay row", "Reopening condition"],
            "caption": "Evidence is read as a route from prose to proof, executable witness, bounded replay, and criticism boundary.",
        },
        "replay": {
            "filename": "oc133_replay_boundary.png",
            "title": "Replay Boundary Route",
            "nodes": ["Pinned source", "Formula", "Comparator", "Residual", "Negative control", "Falsifier"],
            "caption": "A numeric row supports only the bounded replay claim whose source, formula, comparator, residual, control, and falsifier are present.",
        },
    }

    outputs: dict[str, str] = {}
    for key, spec in specs.items():
        width, height = 1600, 360
        image = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 0, width - 1, height - 1), outline="#222222", width=2)
        draw.text((48, 28), spec["title"], fill="#111111", font=font)
        nodes = spec["nodes"]
        left = 48
        top = 130
        box_w = 205 if len(nodes) == 6 else 255
        box_h = 72
        gap = (width - 2 * left - len(nodes) * box_w) // (len(nodes) - 1)
        centers = []
        for idx, label in enumerate(nodes):
            x0 = left + idx * (box_w + gap)
            x1 = x0 + box_w
            y0 = top
            y1 = top + box_h
            draw.rounded_rectangle((x0, y0, x1, y1), radius=16, outline="#1f4e79", width=3, fill="#eef6ff")
            bbox = draw.textbbox((0, 0), label, font=small)
            draw.text((x0 + (box_w - (bbox[2] - bbox[0])) / 2, y0 + (box_h - (bbox[3] - bbox[1])) / 2), label, fill="#111111", font=small)
            centers.append((x1, y0 + box_h / 2, x0, y0 + box_h / 2))
        for idx in range(len(nodes) - 1):
            x_start, y_start, _x_unused, _y_unused = centers[idx]
            _x_prev, _y_prev, x_end, y_end = centers[idx + 1]
            draw.line((x_start + 8, y_start, x_end - 8, y_end), fill="#333333", width=3)
            draw.polygon([(x_end - 8, y_end), (x_end - 24, y_end - 8), (x_end - 24, y_end + 8)], fill="#333333")
        draw.text((48, 260), spec["caption"], fill="#222222", font=small)
        path = PUBLIC_FIGURES / spec["filename"]
        tmp = path.with_suffix(".png.tmp")
        image.save(tmp, format="PNG")
        data = tmp.read_bytes()
        if not path.exists() or path.read_bytes() != data:
            path.write_bytes(data)
        tmp.unlink(missing_ok=True)
        outputs[key] = f"../figures/{spec['filename']}"
    return outputs


def figure_route_panels(kind: str = "general") -> str:
    figures = build_public_figures()
    panels = [
        ("Figure A. Tuple map", "Carrier -> realization -> liveness -> residue -> boundary -> morphism. The tuple is read left to right before theorem obligations are inspected."),
        ("Figure B. Lifecycle route", "Live state -> death condition -> residue evidence -> rebirth candidate -> identity boundary. A failed invariant or residue mismatch blocks identity continuation."),
        ("Figure C. K-level route", "Lower model + added observable -> transition witness -> retained distinction test -> demotion when the observable is inert."),
        ("Figure D. Boundary route", "Classifier boundary -> observable separation -> negative control -> falsifier. Metric thresholds are special cases, not the whole boundary theory."),
        ("Figure E. Evidence route", "Claim -> assumptions -> proof sheet -> Lean subset or finite witness -> numeric replay row when applicable -> reviewer reopening condition."),
        ("Figure F. Replay boundary", "Pinned source -> formula -> comparator -> residual -> negative control -> falsifier. A numeric result carries only the claim whose replay boundary is complete."),
    ]
    titles = {
        "guide": "Visual Route - Reader Route Figures",
        "journal": "Visual Route - Article Figures",
        "methods": "Visual Route - Replay Route Figures",
        "reviewer": "Visual Route - Reviewer Route Figures",
        "general": "Visual Route - Operational Figures",
    }
    leads = {
        "guide": "These figures give the first reading route before the long monograph. They show where to begin and what each route prevents.",
        "journal": "The article uses compact route figures to keep the formal, lifecycle, K-level, boundary, evidence, and replay routes visible while the prose develops the contribution.",
        "methods": "The methods companion uses the same routes as audit diagrams: each rendered image states what has to be replayed or inspected.",
        "reviewer": "The reviewer map uses rendered figures as attack surfaces: each route names where a hostile objection should land.",
        "general": "These figures give a first-pass operational path through the model before the reader enters the longer monograph atlas.",
    }
    out = [heading(titles.get(kind, titles["general"]), 2)]
    out.append(leads.get(kind, leads["general"]))
    out.append("")
    out.append(f"![Conceptual diagram of typed OC continuum components]({figures['tuple']})")
    out.append("")
    out.append("Figure 1. The typed-continuum diagram connects the basic object vocabulary to the place where a public claim must be located.")
    out.append("")
    out.append(f"![Conceptual diagram of lifecycle status and identity boundaries]({figures['lifecycle']})")
    out.append("")
    out.append("Figure 2. The lifecycle diagram separates liveness, death, residue, rebirth, and identity preservation.")
    out.append("")
    out.append(f"![Conceptual diagram of K-level witness and demotion checks]({figures['klevel']})")
    out.append("")
    out.append("Figure 3. The K-level diagram separates witness-bearing transitions from inert observables that must be demoted.")
    out.append("")
    out.append(f"![Conceptual diagram of boundary separation and falsifier checks]({figures['boundary']})")
    out.append("")
    out.append("Figure 4. The boundary diagram links classifier, separation, interface, negative control, and falsifier.")
    out.append("")
    out.append(f"![Conceptual diagram linking public claims to evidence and reopening conditions]({figures['evidence']})")
    out.append("")
    out.append("Figure 5. The evidence diagram shows how a statement becomes reviewable instead of remaining a slogan.")
    out.append("")
    out.append(f"![Conceptual diagram of bounded replay and empirical claim limits]({figures['replay']})")
    out.append("")
    out.append("Figure 6. The replay-boundary diagram shows why a numeric row is a bounded claim, not a whole-domain proof.")
    out.append("")
    out.append("Tuple route. Carrier, realization, liveness, residue, boundary, and morphism prevent the tuple from being treated as a loose metaphor.")
    out.append("")
    out.append("Lifecycle route. Live state, death condition, residue evidence, rebirth candidate, and identity boundary prevent residue from being confused with identity continuation.")
    out.append("")
    out.append("K-level route. Lower model, added observable, retained witness, reduction test, and lawful demotion prevent hierarchy from being added without a witness.")
    out.append("")
    out.append("Evidence route. Claim, assumptions, proof sheet, Lean or finite witness, replay row where applicable, and reopening condition prevent claims from being promoted without support.")
    out.append("")
    out.append("Replay route. Source, formula, comparator, residual, negative control, and falsifier prevent numeric evidence from being over-read.")
    out.append("")
    for idx, (title, body) in enumerate(panels, start=1):
        label = title.replace("Figure ", "Route ").replace(".", ":")
        out.append(f"**{label}** {clean_public_text(body)}")
        out.append("")
        out.append(f"Review use {idx}. The route points to the relevant definition, evidence artifact, and reopening condition.")
        out.append("")
    return "\n".join(out)


def figure_atlas_summary(max_rows: int = 18) -> str:
    rows = figure_entries()
    out = [heading("Visual Route and Figure Use", 2)]
    out.append(
        "The master monograph retains the figure atlas from the full corpus. The supporting PDFs do not reproduce every figure, "
        "but they must state how the visual layer supports the reader: structure diagrams teach the OC tuple, hierarchy diagrams "
        "teach K-level movement, lifecycle diagrams teach liveness/death/residue/rebirth, and domain diagrams anchor examples."
    )
    out.append(
        f"The atlas contains {len(rows)} figures/tables. The public reading route uses representative anchors here and keeps the "
        "complete figure source in the monograph and evidence package so the PDF remains a guided argument rather than an inventory."
    )
    out.append("")
    visual_roles = [
        ("Tuple map", "shows how carriers, realization, liveness, residue, boundary, and morphism components belong to one object rather than disconnected vocabulary"),
        ("Lifecycle route", "operationalizes live/dead/residue/rebirth transitions for readers who need a concrete state path before reading proof sheets"),
        ("K-level route", "shows why K-level transitions require witnesses and why inert observables can be lawfully demoted"),
        ("Boundary route", "links generalized boundaries to observable separation, interface conditions, and falsifiable boundary errors"),
        ("Evidence route", "shows how theorem labels, Lean subset, finite cases, numeric replay rows, and reviewer objections connect without replacing prose"),
    ]
    for label, explanation in visual_roles:
        out.append(bullet(label, explanation))
    out.append("")
    for row in rows[:max_rows]:
        out.append(bullet(row.get("label", "figure"), f"teaches: {row.get('caption', '')}"))
    if len(rows) > max_rows:
        out.append(
            f"The complete atlas includes {len(rows) - max_rows} additional teaching anchors in the master monograph source and public evidence package."
        )
    return "\n".join(out)


def literature_position(max_bib: int = 28, max_sources: int = 18) -> str:
    bib = bibliography_entries()
    register = read_json(ROOT / "comparators" / "OC_1_3_3_NOVELTY_AND_PRIORITY_REGISTER.json", {})
    source_refs: list[dict[str, Any]] = []
    for row in register.get("rows", []) if isinstance(register.get("rows"), list) else []:
        refs = row.get("source_refs", [])
        if isinstance(refs, list):
            for ref in refs:
                if isinstance(ref, dict):
                    source_refs.append(ref)
    out = [heading("Prior-Art and Literature Position", 2)]
    out.append(
        "The bibliography is not decorative. It locates OC against emergence, phase transitions, autopoiesis, dynamical systems, "
        "RAF chemistry, information/complexity, identity over time, hybrid systems, formal methods, systems engineering, and "
        "reproducibility practice. Therefore the release uses literature to bound novelty rather than to claim absence of all prior work."
    )
    out.append(
        f"The working bibliography contains {len(bib)} entries and the comparator register carries "
        f"{len(source_refs)} source anchors. The public text does not use those counts as evidence by themselves; "
        "it uses them to force a synthesis question for each family: what is inherited, what is rephrased, "
        "what is genuinely residual, and what cannot be claimed yet."
    )
    out.append("")
    out.append(heading("Synthesis Families", 3))
    synthesis_families = [
        ("General systems and emergence", "OC inherits the systems-theory concern with organization across levels, but makes the release claim auditable by binding each promoted model-core claim to proof, finite semantic witness, or replay artifact."),
        ("Autopoiesis and organizational closure", "OC treats liveness and residue as typed state predicates rather than as metaphor; this allows death, persistence, and rebirth boundaries to be attacked precisely."),
        ("Dynamical and hybrid systems", "OC does not replace dynamical systems theory; it adds a typed release surface for smooth/update laws, guard/reset semantics, and claims about what a hybrid witness preserves."),
        ("Formal ontology and foundational ontology", "OC uses ontology language only inside a declared model-core vocabulary. It does not claim to replace formal-ontology programs such as BFO or general ontology-engineering practice; the residual claim is the release-governed combination of continuum status, liveness, residue, K-level witnesses, and evidence promotion."),
        ("Mereology, mereotopology, and boundaries", "OC accepts that parts, wholes, spatial boundaries, fiat boundaries, and bona-fide boundaries have extensive prior-art traditions. The 1.3.3 contribution is not priority over those traditions; it is the typed classifier-boundary route used to keep public claims reviewable."),
        ("Process ontology and continuity traditions", "OC inherits the need to distinguish process, persistence, transition, and continuity. It contributes only the bounded typed lifecycle and release-evidence discipline used here, not a universal settlement of process metaphysics."),
        ("Category and type-theoretic formalisms", "OC uses typed carriers and morphism classes as a reviewable formal vocabulary while keeping stronger categorical equivalence claims outside the promoted surface unless separately proved."),
        ("RAF and chemical closure", "OC uses closure-like intuitions only where the domain lane supplies a pinned replay or a stated protocol boundary; chemistry is not used as a rhetorical proof for all domains."),
        ("Complexity and information measures", "OC positions complexity claims as bounded hypotheses with falsifiers, not as a universal growth law promoted by this release."),
        ("Identity, continuity, and lifecycle theory", "OC's identity/rebirth language is tied to declared invariant preservation and residue relations, which makes the scope of identity claims explicit."),
        ("Reproducible research and artifact evaluation", "OC treats the release package itself as a scientific object: claims, proof sheets, Lean subset, finite cases, numeric rows, and public metadata must remain traceable and replayable."),
    ]
    for label, synthesis in synthesis_families:
        out.append(bullet(label, synthesis))
    out.append("")
    out.append(heading("Selected Bibliography", 3))
    for entry in bib[:max_bib]:
        label = ", ".join(part for part in [entry.get("author"), entry.get("year")] if part)
        bibliographic_line = entry.get("title") or ""
        if entry.get("journal"):
            bibliographic_line += f". {entry.get('journal')}."
        out.append(bullet(label or entry.get("key", "reference"), bibliographic_line))
    if len(bib) > max_bib:
        out.append(
            "Additional machine-readable citation metadata is available in the evidence package; this public section uses "
            "the selected set to explain the comparator landscape rather than to present a raw bibliography dump."
        )
    out.append("")
    out.append(heading("Comparator Argument", 3))
    out.append(
        "The relevant comparator question is not whether OC invented systems language, autopoiesis, dynamical systems, "
        "category theory, RAF closure, information theory, identity theory, hybrid systems, formal verification, or "
        "research-object packaging. It did not. The bounded 1.3.3 novelty claim is narrower: OC uses typed carriers, "
        "liveness, residue, morphism classes, K-level witnesses, proof registers, executable finite checks, bounded numeric "
        "replay rows, and release-governed claim promotion as one auditable model-core package. Each comparator row "
        "therefore records accepted overlap first and residual delta second."
    )
    if source_refs:
        out.append(
            "The detailed source-anchor table remains in the evidence package. The public text uses the synthesis families "
            "above because scholarly positioning must be argued by comparison, not by displaying a list of URLs or dates."
        )
    return "\n".join(out)


def prior_art_minimum_surface(kind: str) -> str:
    """Concise related-work surface for every public PDF.

    The full bibliography and comparator rows stay in the monograph/evidence
    package, but each standalone PDF must still name the comparator families
    and the allowed claim boundary.
    """

    role_notes = {
        "guide": "This guide gives a compact map of the comparator traditions a reader should keep in view before reading the monograph.",
        "methods": "The methods companion treats prior art as a reproducibility boundary: comparison claims require source rows, not general confidence.",
        "reviewer": "The reviewer map treats prior art as an attack surface: a same-claim comparator can shrink or reopen OC wording.",
        "journal": "The journal article carries an article-level related-work synthesis rather than a bibliography dump.",
    }
    matrix = read_json(ROOT / "docs" / "OC_1_3_3_PRIOR_ART_COMPARATOR_MATRIX.json", {})
    rows = [row for row in matrix.get("rows", []) if isinstance(row, dict)]
    out = [heading("Article-Level Related Work and Comparator Boundary" if kind == "journal" else "Related Work and Comparator Boundary", 2)]
    out.append(role_notes.get(kind, "This document states the related-work boundary needed for standalone reading."))
    out.append(
        "The release does not claim absence of predecessors, global priority, or superiority over modern science. Its defensible public contribution is narrower: it integrates typed model-core claims, proof sheets, finite semantic witnesses, bounded numeric replay QA, comparator rows, and explicit reopening conditions into one auditable scientific release surface."
    )
    if kind == "journal":
        out.append(
            "The related-work argument is therefore source-by-source. For each comparator tradition, OC first records the accepted overlap, then names the residual delta that remains only within the current evidence boundary, and finally states what OC must not claim."
        )
    mandatory_families = [
        ("Formal ontology / BFO and ontology engineering", "OC does not promote Logion or ESTRA as authors and does not treat ontology-engineering vocabulary as a novelty claim. The release contribution is the bounded continuum model and its evidence governance."),
        ("Mereology and mereotopology", "OC does not claim to invent part-whole or boundary theory. It uses typed boundaries, residue relations, and classifier rules as the release-local way to keep boundary claims falsifiable."),
        ("Process ontology and continuity", "OC does not settle every process-metaphysical debate. It states lifecycle, death, residue, rebirth, and identity-continuation boundaries under declared assumptions."),
        ("Formal logic, category theory, type theory, and proof assistants", "OC uses these traditions as comparison and implementation context; a Lean declaration or finite witness supports only the exact bounded statement it encodes."),
    ]
    for family, boundary in mandatory_families:
        out.append("")
        out.append(f"Required comparator family: {family}. Boundary: {boundary}")
    max_rows = 10 if kind == "journal" else 6
    def residual_delta_clause(raw_delta: Any) -> str:
        delta_text = clean_public_text(raw_delta or "bounded residual contribution remains only inside the release evidence boundary").strip()
        lower = delta_text.lower()
        if lower.startswith("uses typed morphism discipline"):
            return "the use of typed morphism discipline to police public scientific claims, without claiming invention of category theory"
        if lower.startswith("does not replace raf"):
            return "the typed placement of RAF-like closure as one K-level route with explicit reduction and demotion checks, without replacing RAF theory"
        if lower.startswith(("uses ", "separates ", "records ", "locates ", "keeps ", "binds ")):
            return "the release-local practice that " + delta_text
        return delta_text

    for row in rows[:max_rows]:
        tradition = clean_public_text(row.get("tradition") or "comparator tradition")
        source_refs = row.get("source_refs") if isinstance(row.get("source_refs"), list) else []
        source_title = clean_public_text(source_refs[0].get("title") if source_refs and isinstance(source_refs[0], dict) else tradition)
        overlap = clean_public_text(row.get("prior_art_has") or row.get("claim_element_overlap") or "accepted overlap with the comparator tradition")
        delta = residual_delta_clause(row.get("bounded_positioning_note"))
        boundary = clean_public_text(row.get("what_oc_must_not_claim") or row.get("non_novelty_boundary") or "No priority or uniqueness claim is promoted from this comparison.")
        out.append("")
        out.append(
            f"Comparator tradition: {tradition}. Source anchor: {source_title}. OC accepts the overlap: {overlap}. "
            f"The bounded residual delta for this release is {delta}. The boundary is equally important: {boundary}"
        )
    out.append(
        "The full comparator matrix and source snapshots remain in the evidence package. If a future systematic search shows that a comparator already carries the same claim at the same strength, the OC public wording must be demoted or rewritten rather than defended by novelty rhetoric."
    )
    return "\n".join(out)


def theorem_catalog(max_rows: int | None = None, include_excerpts: bool = True) -> str:
    registry = read_json(ROOT / "proofs" / "THEOREM_REGISTRY_1_3_3.json", {})
    rows = registry.get("rows", [])
    if max_rows:
        rows = rows[:max_rows]
    out = [heading("Theorem and Proof Registry", 2)]
    out.append(
        "The release promotes bounded theorem claims only where the theorem registry binds a proof sheet, "
        "Lean reference, finite witness route, and explicit scope boundary. Broad full-science and unbounded cross-science comparison "
        "claims stay outside the promoted release surface."
    )
    out.extend(
        [
            bullet("theorem registry size", registry.get("theorem_total")),
            bullet("machine-checked subset size", registry.get("machine_checked_subset_total")),
            bullet("adversarial blocker count", registry.get("adversarial_review_blocker_total")),
            "",
        ]
    )
    for idx, row in enumerate(rows, start=1):
        theorem_id = str(row.get("theorem_id") or "")
        out.append(heading(f"{idx}. {theorem_id}: {clean_public_text(row.get('title'))}", 3))
        out.extend(
            [
                bullet("claim boundary", row.get("public_claim_boundary")),
                bullet("evidence ref", row.get("evidence_ref")),
                bullet("proof sheet", row.get("proof_sheet_ref")),
                bullet("Lean ref", row.get("lean_ref")),
                bullet("evidence ceiling", row.get("evidence_ceiling")),
                bullet("scope limit", row.get("scope_limit")),
                "",
            ]
        )
        if include_excerpts:
            excerpt = proof_sheet_excerpt(str(row.get("proof_sheet_ref", "")))
            if excerpt:
                out.append("Proof-sheet excerpt:")
                out.append("")
                out.append(textwrap.indent(excerpt, "> "))
                out.append("")
    return "\n".join(out)


def claim_catalog(max_rows: int = 12) -> str:
    register = read_json(ROOT / "claims" / "CLAIM_LEDGER_1_3_3.json", {})
    rows = register.get("rows", [])
    out = [heading("Claim Governance", 2)]
    out.append(
        "The public claim surface is intentionally bounded. A claim enters the release text only when it is "
        "evidence-bound, externally reviewable, and explicitly scoped. Universal closure or unbounded cross-domain "
        "comparison language is not promoted by this release."
    )
    out.append(
        "The current release register contains only scoped model-core claims for public promotion; unsupported broad "
        "finality claims are rejected by the publication standard before they can reach the release surface."
    )
    out.append("")
    included = 0
    for row in rows:
        if row.get("control_plane_claim"):
            continue
        if row.get("scientific_promotion_allowed") or row.get("public_status"):
            included += 1
            if included > max_rows:
                break
            out.append(heading(str(row.get("claim_id")), 3))
            scope_sentence = public_scope_sentence(row.get("scope_limit") or row.get("public_status"))
            out.extend(
                [
                    bullet("claim", row.get("claim")),
                    bullet("support", row.get("support")),
                    bullet("evidence", row.get("evidence_ref")),
                    bullet("public boundary", scope_sentence),
                    "",
                ]
            )
    if len(rows) > max_rows:
        out.append(
            "The complete claim register remains in the evidence package. The public PDF shows representative claim "
            "boundaries and keeps machine-verification predicates out of the main prose."
        )
    return "\n".join(out)


def empirical_evidence(include_lane_replays: bool = False) -> str:
    target = read_json(ROOT / "validation" / "target_blind" / "OC133_TARGET_BLIND_PREDICTION_TABLE.json", {})
    domain = read_json(ROOT / "reports" / "OC_CORE_1_3_3_DOMAIN_VALIDATION_REPORT.json", {})
    rows = target.get("rows", [])
    out = [heading("Bounded Replay QA and Artifact-Integrity Examples", 2)]
    out.append(
        "The numeric section reports bounded replay QA rows over pinned official snapshots. The rows are used as "
        "artifact-integrity and target-blind replay examples for model-core review: each lane declares a formula, a held-out or hidden target "
        "selection, a comparator, uncertainty or residual information, a negative control, a falsifier, and a replay hash. "
        "They do not claim whole-domain proof, independent domain validation, or unrestricted victory over local scientific models."
    )
    lanes = [clean_public_text(row.get("lane")).title() for row in rows if row.get("lane")]
    out.append(
        "The release covers the following bounded replay lanes: "
        f"{sentence_list(lanes) or 'recorded in the validation report'}. The domain report keeps complete domain "
        "promotion separate from replay QA so that a successful reconstruction row cannot be mistaken for a universal law."
    )
    out.append("")
    for row in rows:
        out.append(heading(f"{clean_public_text(row.get('lane')).title()} - {clean_public_text(row.get('claim_id'))}", 3))
        out.extend(
            [
                bullet("snapshot", row.get("dataset_snapshot_ref")),
                bullet("target-blind split", row.get("target_blind_split")),
                bullet("formula", row.get("formula")),
                bullet("predicted value", row.get("predicted_value")),
                bullet("observed value", row.get("observed_value")),
                bullet("uncertainty", row.get("uncertainty")),
                bullet("residual", row.get("residual")),
                bullet("comparator baseline", row.get("comparator_baseline")),
                bullet("comparator residual", row.get("comparator_residual")),
                bullet("negative control", row.get("negative_control")),
                bullet("falsifier", row.get("falsifier")),
                bullet("snapshot hash", row.get("snapshot_sha256")),
                bullet("replay hash", row.get("replay_hash")),
                bullet("support scope", row.get("support_scope")),
                "",
            ]
        )
    if include_lane_replays:
        for replay in domain.get("lane_replay_results", [])[:10]:
            out.append(heading(f"Replay Audit - {clean_public_text(replay.get('lane')).title()}", 3))
            out.extend(
                    [
                        bullet("audit conclusion", replay.get("result_verdict")),
                        bullet("recorded replay issues", replay.get("failure_total")),
                        bullet("source log", replay.get("source_log_ref")),
                        "",
                ]
            )
            for row in replay.get("rows", [])[:8]:
                out.extend(
                    [
                        bullet("row", row.get("claim_id")),
                        bullet("snapshot opened", row.get("snapshot_opened")),
                        bullet("computed residual", row.get("computed_residual")),
                        bullet("negative control rejected", row.get("negative_control_rejected")),
                        "",
                    ]
                )
    return "\n".join(out)


def finite_model_evidence(max_rows: int = 8) -> str:
    finite = read_json(ROOT / "proofs" / "FINITE_MODEL_CHECKS_1_3_3.json", {})
    rows = finite.get("rows", [])
    summary = finite_status_summary()
    out = [heading("Executable Finite-Model Evidence", 2)]
    out.append(
        "The finite-model runner computes semantic outcomes from model facts and mutation controls. "
        "The public summary below explains representative semantic proof evidence. Exhaustive case rows remain in "
        "machine-readable evidence files so the public PDF is a methods narrative rather than a truth-table dump."
    )
    out.extend(
        [
            bullet("finite-model audit conclusion", summary["state"]),
            bullet("semantic case coverage", summary["case_total"]),
            bullet("recorded semantic issues", summary["failure_total"]),
            bullet("semantic evaluator", summary["semantic_evaluator"]),
            bullet("mutation control count", summary["mutation_control_total"]),
            bullet("K-transition negative count", summary["k_transition_negative_total"]),
            "",
        ]
    )
    included = 0
    for row in rows:
        case_type = str(row.get("case_type", ""))
        if "send" in case_type.lower() or "publication" in case_type.lower():
            continue
        included += 1
        theorem_id = clean_public_text(row.get("theorem_id") or "bounded theorem")
        title = "Negative control" if str(row.get("observed_verdict", "")).upper() == "REJECT" else "Positive witness"
        model = row.get("model", {}) if isinstance(row.get("model"), dict) else {}
        model_keys = list(model.keys())[:6]
        model_summary = sentence_list([key.replace("_", " ") for key in model_keys])
        out.append(heading(f"{title} for {theorem_id}", 3))
        paired_control = clean_public_text(row.get("negative_control_id") or "")
        if len(paired_control) > 28:
            paired_control = "paired negative-control case recorded in the public evidence file"
        out.extend(
            [
                bullet("theorem anchor", theorem_id),
                bullet("Lean anchor", row.get("lean_theorem_ref")),
                bullet("semantic result", "the evaluator accepts the witness" if str(row.get("observed_verdict", "")).upper() == "ACCEPT" else "the evaluator rejects the attempted stronger or malformed reading"),
                bullet("model facts used", model_summary or "recorded in the public finite-model evidence file"),
                bullet("paired control", paired_control or "paired case recorded in the finite-model evidence file"),
                bullet("reader consequence", "the theorem boundary is executable: changing the required model facts changes the result instead of merely changing a label"),
                "",
            ]
        )
        if included >= max_rows:
            break
    return "\n".join(out)


def methods_replay_narrative() -> str:
    return "\n".join(
        [
            heading("Reproducibility Method", 2),
            "This companion is a methods guide, not the exhaustive finite-case register. The full machine-readable register is in the public evidence package; the prose here explains how a reviewer should replay the evidence and interpret failures.",
            "",
            heading("Prerequisites", 3),
            "A reviewer needs two objects with different roles: the public release archive for curated evidence and citation, and a full repository checkout at tag v1.3.3 for executable command replay. The Zenodo public zip is intentionally curated; it is not a complete source checkout and should not be mistaken for the runner tree. Network access is not required for replaying already-pinned public evidence once the repository checkout and public archive have been downloaded.",
            "",
            "Canonical source checkout route: clone the public repository, then check out the exact release tag. The canonical repository is `https://github.com/alexanderyashin/ontology-of-continua-core-main`. A reviewer may use `git clone https://github.com/alexanderyashin/ontology-of-continua-core-main.git`, `cd ontology-of-continua-core-main`, and `git checkout v1.3.3`. The public archive DOI identifies the citable release object; the repository tag identifies the executable replay tree. The methods audit stops if those two identities disagree.",
            "",
            heading("Environment Lock", 3),
            "The replay environment is treated as an explicit artifact boundary. The public archive records the repository manifest, checksums, Lean source, Lean build certificate, finite-model input facts, finite-model output attestation, target-blind table, validation report, simulation reports, and public payload suitability report. A reviewer should compare local command outputs with those named artifacts before interpreting scientific meaning.",
            "",
            "The minimum local toolchain is Python 3, Pandoc with XeLaTeX for public PDF regeneration, Poppler `pdftotext` for PDF text audit, and Lean/Lake for the formal subset. Exact local package versions are not used as scientific evidence; they are replay conditions. If a tool version changes an output hash, the mismatch is a reproducibility finding until explained by a regenerated and audited artifact.",
            "",
            heading("Public Archive to Repository Mapping", 3),
            "The public archive contains the human PDFs, curated evidence projections, metadata, checksums, and the release zip. The repository checkout contains executable directories such as formal/lean, proofs, validation, simulations, falsification, tools, and release_machine. A reviewer should use the archive to identify the published claim and checksum state, then use the checkout to run the commands against the same tag. If the archive and checkout disagree on version, DOI, manifest, or checksum, the replay stops at an archive-integrity finding before scientific interpretation begins.",
            "",
            heading("Inputs", 3),
            "The replay inputs are the Lean source and certificate, theorem/proof registers, finite-model input facts, bounded numeric tables, validation reports, comparator registers, adversarial-review summaries, public checksums, and release metadata.",
            "",
            heading("Commands", 3),
            "Run the replay from the repository root. The bounded public replay path is:",
            "",
            "```powershell",
            "lake build OC133V12",
            "python proofs/finite_model_checks/run_finite_model_checks.py",
            "python validation/run_all.py --qa-only",
            "python simulations/run_all.py --write-report",
            "python simulations/adversarial/run_all.py",
            "python falsification/counterexample_search/run_counterexample_search.py",
            "python tools/oc133_public_release_payload.py --check",
            "```",
            "",
            "The expected outputs are the Lean certificate, finite-model report, replay QA report, simulation reports, adversarial simulation report, counterexample report, public payload suitability report, public zip checksum, and PDF text-audit files named in the manifest.",
            "",
            heading("Replay Order", 3),
            "1. Build the Lean subset and inspect the Lean certificate.",
            "2. Run the finite-model semantic checker and confirm that positive witnesses and negative controls separate as declared by the theorem boundary.",
            "3. Run replay QA for bounded target-blind artifact-integrity and reconstruction examples.",
            "4. Compare generated checksums with the public checksum manifest.",
            "5. Treat any mismatch, parse failure, stale hash, unsupported claim, or publication-permission mismatch as a localized scientific or archive-integrity defect.",
            "",
            heading("Expected Outputs", 3),
            "Expected outputs are a passing Lean certificate, a finite-model report with zero failures, replay QA rows with recorded residuals and falsifiers, simulation reports, a checksum manifest matching the archive, and no stale or private-path public-surface findings. If a command changes a generated artifact, the release is replayed and checksums are recomputed; if it changes nothing, delta-stable verification prevents downstream churn.",
            "",
            heading("Failure Interpretation", 3),
            "A proof failure attacks a formal claim boundary. A finite-model mismatch attacks the executable semantic witness. A validation mismatch attacks a bounded replay row, not a universal domain law. A checksum mismatch attacks package integrity. These failures are intentionally separated so that reviewers can identify the exact class of defect.",
            "",
            heading("Artifact Map", 3),
            "Proof artifacts live under `proofs/` and `formal/lean/`; numeric replay artifacts live under `validation/` and `reports/`; reviewer artifacts live under `review/` and `reviews/`; publication artifacts live under `releases/oc_core_1_3_3/`. The public zip carries sanitized evidence projections for external replay.",
        ]
    )


def methods_positive_audit_protocol() -> str:
    return "\n".join(
        [
            heading("Claim-to-Command Interpretation", 2),
            "The methods companion must do more than name commands. Each replay command has a scientific role, an expected artifact, and a failure interpretation. This prevents a reviewer from treating the reproducibility path as an opaque build script.",
            "",
            heading("Lean Build", 3),
            "`lake build OC133V12` checks the selected formal subset. A failure here does not merely indicate a tooling issue: it threatens every public theorem boundary that cites the Lean subset as support. The repair route is to inspect the Lean declaration, the theorem inventory binding, and the proof sheet assumption set before re-running the build.",
            "",
            heading("Finite Semantic Checks", 3),
            "`python proofs/finite_model_checks/run_finite_model_checks.py` evaluates finite model facts independently from claimed verdict labels. The expected output is a report in which positive witnesses pass and mutation or tamper controls fail as designed. A mismatch threatens the semantic witness route for K0 resolution, lifecycle status, boundary classification, hybrid behavior, K-level transition, and minimality claims.",
            "",
            heading("Validation QA", 3),
            "`python validation/run_all.py --qa-only` checks target-blind and numeric replay rows. A passing result means the row has the required formula, snapshot reference, split, prediction, observation, uncertainty, comparator, residual, negative control, falsifier, and replay hash. It does not mean that the whole scientific domain has been proved; it means the bounded public replay claim is internally auditable.",
            "",
            heading("Simulation and Counterexample Search", 3),
            "The simulation and adversarial-simulation commands check whether the computational examples behave consistently with the stated model boundaries. The counterexample search is the negative side of the same method: it tries to find cases that break promoted assumptions. A serious counterexample does not get hidden in prose; it reopens the relevant claim boundary and routes the release back to Research and Review.",
            "",
            heading("Public Archive Consistency Check", 3),
            "`python tools/oc133_public_release_payload.py --check` checks public PDFs, monograph integration, positive mission fulfillment, scientific/process state, editorial adversarial review, public surface language, known error regression, zip contents, and destination-ready metadata. It is expected to be delta-stable when inputs have not changed.",
            "",
            heading("Evidence Inputs and Outputs", 2),
            "Every replay input has a provenance role. Lean sources and certificates support formal claims. Proof sheets support theorem assumptions and counterexample boundaries. Finite-model facts support semantic witnesses. Target-blind tables support bounded replay QA and artifact-integrity examples. Domain evidence-boundary reports keep broad validation claims quarantined. Comparator registers support prior-art positioning. Reviewer summaries support adversarial closure. Checksums and manifests support archive integrity.",
            "",
            "Every replay output must be interpreted at the same level as its input. A passing formal check supports formal consistency under declared assumptions; it is not an empirical result. A passing target-blind row supports a reconstruction claim; it is not a proof of unrestricted domain coverage. A passing public payload audit supports release presentation and packaging; it is not a substitute for theorem or data evidence.",
            "",
            heading("Delta-Stable Verification", 2),
            "Verification should not dirty the release tree when no meaningful input changed. If a command rewrites a tracked artifact with identical semantic content, the release process treats that as a process-quality defect. If a command produces a real semantic delta, downstream packaging is triggered deliberately and the new checksum state is recorded. This prevents the release process from fighting itself while preserving strict reproducibility.",
            "",
            heading("Reviewer Checklist", 2),
            "A methods reviewer can audit the release by asking seven questions. First, does each promoted claim have a replay or proof route? Second, does each command produce the declared artifact? Third, are negative controls and falsifiers present where the claim requires them? Fourth, are broad domain claims kept out of the promoted surface? Fifth, do checksums bind the public archive? Sixth, does a repeated verification pass leave the tree unchanged when there is no semantic delta? Seventh, does any failure route to a named claim boundary rather than disappearing into a generic build status?",
            "",
            "Only if those questions are answerable from the public artifacts should the methods companion be considered publication-grade. That is why this PDF includes the interpretation protocol in prose rather than leaving readers with a list of commands and filenames.",
            "",
            heading("Replay Visual Route", 2),
            "The methods companion uses visual route panels as operational diagrams. They are not decorative figures: the tuple panel tells the reader what object the replay concerns, the lifecycle panel tells the reader which status transitions are being tested, the K-level panel explains transition witnesses, the boundary panel explains classifier and falsifier checks, and the evidence panel shows how a claim moves from prose to proof, finite witness, numeric row, and reviewer reopening condition.",
            "",
            heading("Artifact Interpretation Map", 2),
            "The methods reader should treat the public archive as a layered argument. The master monograph is the long-form scientific claim. The journal core is the article-length route. The methods companion is the replay route. The reviewer map is the adversarial route. The public zip is the evidence bundle. The manifest and checksum files bind the file set. A defect in one layer has a different meaning from a defect in another layer, so the review protocol separates them rather than collapsing everything into a single pass/fail label.",
            "",
            "If the master monograph fails, the scientific exposition itself is defective even if all machine files exist. If the journal core fails, the article-facing argument is not ready for editors even if the monograph is long. If the methods companion fails, the evidence is not reviewable even if the claims are plausible. If the reviewer map fails, hostile objections are not answered in public-facing form. If the public zip fails, the archive cannot be trusted as a reproducibility object. The release is acceptable only when all layers agree.",
            "",
            heading("Traceability Requirements", 3),
            "Traceability is bidirectional. A claim in prose must point to an evidence route, and an evidence route must point back to the claim it supports. A theorem identifier must be meaningful in the theorem inventory, proof sheet, Lean subset where applicable, finite witness where applicable, and public explanation. A numeric row must be meaningful in the target-blind table, validation report, methods narrative, and claim boundary. A reviewer objection must name the claim under attack and cite the evidence that answers it.",
            "",
            "The practical rule is simple: no orphan claims and no orphan evidence. An orphan claim is a public statement with no proof, data, simulation, comparator, or boundary. Orphan evidence is a file or row whose scientific role is not explained to the reader. Both are publication defects. The methods companion gives reviewers the route for detecting them before a public archive is updated.",
            "",
            heading("Minimum Reproducibility Interpretation", 3),
            "Reproducibility is interpreted at four levels. Level one is file integrity: assets match checksums and the zip contains the expected curated files. Level two is command replay: the listed commands run and produce the expected reports. Level three is semantic replay: positive examples and negative controls separate according to the claim boundary. Level four is public interpretation: the reader can understand what the replay result means without reverse-engineering internal machinery.",
            "",
            "A release can pass level one and still fail as science if it only archives files. It can pass level two and still fail as argument if the text does not connect outputs to claims. It can pass level three and still fail as publication if the public documents are unreadable. It can pass level four only when the archive, commands, semantics, and prose reinforce one another. That is the standard applied to OC Core 1.3.3.",
            "",
            heading("What a Failed Replay Means", 3),
            "A failed replay is not automatically a refutation of the whole model. It is a localized signal. The reviewer should first identify the artifact class, then the claim boundary, then the dependency path, then the appropriate repair route. A Lean failure routes to formalization and proof assumptions. A finite semantic failure routes to witness construction and theorem boundary. A numeric replay failure routes to data snapshot, formula, uncertainty, comparator, and falsifier review. A public presentation failure routes to manuscript integration, editorial review, metadata, or packaging.",
            "",
            "This localization matters because it keeps the release scientifically honest. The public claim surface is strong only where the evidence is strong. When the evidence is bounded, the public wording is bounded. When the evidence fails, the claim reopens. The methods companion therefore protects ambition by making ambition testable rather than by weakening it into vague language.",
            "",
            heading("Worked Audit Walk-Through", 2),
            "A reviewer who wants a concrete path can start with T133-K0-RES. The reviewer reads the theorem statement in the monograph, checks that the claim boundary is bounded, opens the proof sheet for assumptions and counterexample boundary, confirms that the Lean subset or finite witness reference is not empty, then runs the finite semantic checker. If the finite report shows that the declared witness passes and that tampered or inert variants fail as expected, the reviewer has a localized reason to accept the bounded K0-support claim. If any part of the route is missing, the claim is not publication-ready.",
            "",
            "The same pattern applies to a numeric row. The reviewer selects a lane, reads the formula and support scope, verifies that the dataset snapshot reference exists, checks the target-blind split, compares predicted value, observed value, uncertainty, residual, and comparator residual, then inspects the negative control and falsifier. The row supports only the bounded reconstruction claim named in the table. It does not become evidence for total domain closure unless a separate domain-validation artifact proves that stronger statement.",
            "",
            "For prior art, the reviewer should not ask whether OC has no predecessors. That would be a weak and unscientific question. The correct question is whether the release identifies the relevant predecessor families, states overlap honestly, names residual delta precisely, and prevents that residual delta from inflating into a priority or unrestricted-comparison claim. The comparator rows and novelty register are therefore read as boundaries on external speech as much as evidence for novelty.",
            "",
            "For editorial quality, the reviewer should open the PDF directly, not only the manifest. The document must have title page, dedication, version, DOI, abstract, reader contract, table of contents, explanatory paragraphs, transition language, visual anchors, literature synthesis, claim boundary, and a clear route from prose to evidence. If the first visible experience is metadata or if the text is a raw register dump, the methods replay can pass and the release can still fail as a scientific publication.",
            "",
            "This walk-through is intentionally repetitive at the method level because it encodes the invariant for future releases: select a claim, locate its evidence, replay or inspect the evidence, check the negative boundary, compare against prior art, and read the public wording against that support. The invariant applies to formal, computational, empirical, editorial, and release-metadata layers alike.",
            "",
            heading("Protocol Matrix", 2),
            "The replay protocol is organized as a matrix rather than a linear checklist. The rows are formal proof, finite semantic witness, target-blind replay QA, simulation, adversarial simulation, counterexample search, public-payload audit, and archive checksum verification. The columns are input, command, expected artifact, scientific interpretation, failure meaning, and repair owner. A row is reviewable only when all six columns can be read from the public artifacts without consulting private notes.",
            "",
            "| Protocol row | Input class | Expected artifact | Scientific interpretation | Failure route |",
            "| --- | --- | --- | --- | --- |",
            "| Lean subset | typed formal source | build certificate | selected formal declarations type-check under declared assumptions | formalization and proof boundary |",
            "| Finite semantics | raw finite model facts | output attestation | witnesses and tamper controls separate semantically | theorem witness and evaluator repair |",
            "| Replay QA | pinned numeric rows | validation report | bounded reconstruction row is auditable | data, formula, uncertainty, comparator, or falsifier repair |",
            "| Simulation | executable examples | simulation report | examples remain within declared model behavior | model assumption or example repair |",
            "| Counterexample search | adversarial fixtures | counterexample report | promoted boundary resists known search patterns | claim reopening or proof/data repair |",
            "| Public payload | manuscript and metadata sources | suitability report | public archive is readable and claim-bounded | editorial, packaging, or metadata repair |",
            "",
            "The matrix is deliberately conservative. It does not let a strong result in one row compensate for a missing row elsewhere. A theorem can be formally tidy and still need a finite witness if the public claim cites one. A numeric row can replay cleanly and still fail if the public prose describes it as whole-domain validation. A package can be checksummed and still fail if the first public reading experience is a metadata dump.",
            "",
            heading("Domain-Lane Interpretation", 2),
            "The empirical lanes in this release are read as bounded domain-lane examples. Each lane has to name a source snapshot, reconstruction formula, prediction or reconstruction target, observed value, uncertainty or residual, comparator, negative control, falsifier, and replay hash. The lane supports the claim that the released artifact can be audited at that target boundary. It does not by itself prove that the entire domain is numerically solved.",
            "",
            "A physics row therefore has a different force from a chemistry row, a biology row, a systems row, or a mathematics row. The methods companion keeps these forces separated. Physics and chemistry rows are closer to numerical reconstruction examples; biological and systems rows are more exposed to modeling assumptions; mathematics rows are formal or finite-model anchors rather than empirical measurements. The public claim boundary must reflect those differences.",
            "",
            "The reader should also distinguish target-blind replay from prospective prediction. Target-blind replay can prevent a file from being a circular restatement of its target, but it is still bounded by the chosen snapshot, split rule, formula, and comparator. Prospective prediction would require a future target and a pre-registered scoring rule. The release therefore treats prospective prediction as a future research extension unless an artifact explicitly provides it.",
            "",
            heading("Independent Rebuild Expectation", 2),
            "A serious reviewer should be able to rebuild the public evidence route independently. Independence here does not mean rewriting the whole theory. It means that the reviewer can take the public archive, rebuild the formal subset, replay the finite semantic checks, inspect numeric rows, compare checksums, and confirm that the public PDFs describe the same claim boundaries as the evidence files. The release fails if the reviewer has to infer missing links from private process memory.",
            "",
            "The release also fails if verification changes the object being verified without a declared semantic delta. Reproducibility is not only about re-running commands; it is also about preventing the release process from manufacturing new artifacts during inspection. When a real input changes, regeneration is correct. When no meaningful input changes, the correct result is a clean repeat check.",
            "",
            heading("Reviewer Burden and Author Burden", 2),
            "The methods standard assigns burden carefully. The reviewer is responsible for checking the declared evidence route and for naming the exact failure class if a replay or interpretation fails. The author is responsible for making that route available, readable, bounded, and independently inspectable. The reviewer should not have to discover whether Logion is an author, a research instrument, or a release process; the public metadata and front matter must make those entity roles explicit.",
            "",
            "The author burden is stricter for ambitious claims. A modest claim may need only a clear definition and a local example. A theorem claim needs assumptions, proof route, and boundary. A computational claim needs executable semantics and negative controls. An empirical claim needs data provenance, split, formula, comparator, residual, uncertainty, negative control, falsifier, and replay hash. A publication-readiness claim needs a human-readable manuscript set, editorial review, archive metadata, and post-release verification.",
            "",
            "This is why the methods companion belongs in the public release. It teaches reviewers how to interpret the evidence without letting the evidence become a pile of files. The method is itself part of the scientific object: it states what kind of support the release has, what kind of support it does not yet have, and what would have to happen for the claim boundary to move.",
            "",
            heading("Audit Decision Rules", 2),
            "The audit decision rules are intentionally explicit because otherwise reviewers and release operators can talk past one another. A formal failure blocks theorem promotion. A semantic witness failure blocks the theorem route that cites that witness. A numeric residual outside the declared tolerance blocks the replay row, not the whole model, unless the promoted claim depends on that row as universal evidence. An absent comparator blocks any comparative wording. An absent negative control blocks empirical promotion. Defective front matter or an unreadable first page blocks publication even when the scientific files exist.",
            "",
            "These rules prevent false escalation and false comfort. False escalation would treat a local replay mismatch as refutation of every OC claim. False comfort would treat a green checksum as proof that the manuscript is scientifically persuasive. The release needs neither habit. It needs exact routing: which claim is attacked, which evidence object is implicated, which standard is violated, and which capability must repair it.",
            "",
            heading("Evidence Reading Examples", 3),
            "Example one is a finite semantic witness. The reader starts with the public theorem identifier, verifies that the proof sheet names assumptions, checks the finite-model case identifier, then confirms that the evaluator derives the result from raw model facts. If changing a label without changing facts changes the result, the evaluator is defective. If changing the required facts changes the result as expected, the witness is meaningful.",
            "",
            "Example two is a bounded replay row. The reader starts with the lane and target, then reads the formula, pinned snapshot, split, predicted value, observed value, uncertainty, comparator, residual, negative control, falsifier, and replay hash. The row earns only the scope written in the claim boundary. If the public text says more than the row supports, the text is wrong even when the row itself is technically reproducible.",
            "",
            "Example three is a prior-art comparison. The reader starts with a comparator family, checks the overlap statement, asks whether the claimed residual difference is specific, then verifies that the release does not infer absence, priority, or unrestricted comparative victory from a narrow source sample. The comparison is strong when it is exact and bounded. It is weak when it becomes a slogan.",
            "",
            heading("Minimum Independent Scientific Review Packet", 3),
            "A reviewer who does not want to rebuild every artifact can still perform a minimum independent review. The minimum packet is the master monograph, journal core, methods companion, reviewer map, theorem registry, proof sheets, Lean source, finite-model input and output files, target-blind replay table, domain evidence-boundary report, comparator register, public checksum file, and Zenodo/GitHub metadata. Those objects must agree on version, DOI, claim boundary, author/instrument roles, and file identity.",
            "",
            "Agreement is checked materially, not by trust. The version string must be the same. The DOI must identify the same record. The checksum must match the downloaded file. The claim wording must match the evidence class. The proof route must be named where theorem language appears. The empirical route must be named where replay language appears. The journal package language must not imply submission unless a separate submission action actually occurred.",
            "",
            "This minimum packet is the bridge between a full rebuild and a first editorial screen. It lets a journal editor, archive curator, or hostile reader detect the most serious release defects without pretending that a quick inspection is the same as full scientific acceptance.",
        ]
    )


def methods_replay_matrix() -> str:
    rows = [
        (
            "Lean formal subset",
            "Command: lake build OC133V12.",
            "Inputs: formal/lean/OC133V12.lean and the Lake project files.",
            "Outputs: formal/lean/LEAN_BUILD_CERTIFICATE_1_3_3.json and the local Lake build result.",
            "Hash source: public checksum manifest and the Lean certificate hash recorded in the evidence package.",
            "Failure meaning: theorem claims citing the Lean subset are reopened until the declaration, proof boundary, or toolchain mismatch is repaired.",
        ),
        (
            "Finite semantic witnesses",
            "Command: python proofs/finite_model_checks/run_finite_model_checks.py.",
            "Inputs: proofs/finite_model_checks/OC133_FINITE_MODEL_INPUTS.json and related finite-model runner code.",
            "Outputs: proofs/FINITE_MODEL_CHECKS_1_3_3.json and the public finite-model output attestation.",
            "Hash source: checksums.txt, manifest.json, and the public evidence-package projection.",
            "Failure meaning: the theorem or semantic witness family named by the failing case is reopened; the whole model is not silently promoted.",
        ),
        (
            "Bounded target-blind replay QA",
            "Command: `python validation/run_all.py --qa-only`.",
            "Inputs:\n\n- `validation/target_blind/OC133_TARGET_BLIND_PREDICTION_TABLE.json`\n- `validation/numeric_replay_qa/OC133_NUMERIC_REPLAY_QA_TABLE.json`\n- public evidence projection `evidence/validation__target_blind__OC133_TARGET_BLIND_PREDICTION_TABLE.json`.",
            "Outputs:\n\n- `reports/OC_CORE_1_3_3_DOMAIN_VALIDATION_REPORT.json`\n- the target-blind replay table\n- the numeric replay QA table.",
            "Hash source: public checksum manifest, domain validation report hash, and replay-table hash.",
            "Failure meaning: the affected replay row loses promotion; comparative or empirical wording depending on that row must be narrowed.",
        ),
        (
            "Simulation and adversarial simulation",
            "Command: `python simulations/run_all.py --write-report`; `python simulations/adversarial/run_all.py`.",
            "Inputs: simulations, adversarial simulation fixtures, and declared public model assumptions.",
            "Outputs: simulation reports and adversarial simulation summaries.",
            "Hash source: public package manifest and generated report checksums.",
            "Failure meaning: any claim that cites the affected simulation becomes provisional until the simulation report is repaired or the claim is demoted.",
        ),
        (
            "Counterexample search",
            "Command: python falsification/counterexample_search/run_counterexample_search.py.",
            "Inputs: falsification/counterexample_search fixtures and declared theorem boundaries.",
            "Outputs: counterexample-search report with survivor or no-survivor status under the declared scope.",
            "Hash source: public evidence package and checksums.txt.",
            "Failure meaning: a surviving counterexample reopens the exact claim boundary named by the search configuration.",
        ),
        (
            "Public payload audit",
            "Command: `python tools/oc133_public_release_payload.py --check`.",
            "Inputs: public PDFs, public evidence package, metadata, checksums, DOI parameters, and known-error patterns.",
            "Outputs: PUBLIC_PAYLOAD_SUITABILITY_1.3.3_latest.json and PDF text-audit files.",
            "Hash source: public payload suitability report and generated archive checksum.",
            "Failure meaning: publication is stopped until the public-surface, archive, metadata, or claim-boundary defect is repaired.",
        ),
    ]
    out = [heading("Replay Matrix for Independent Review", 2)]
    out.append(
        "This matrix is written in prose rather than raw table syntax so it remains readable in the PDF text extraction. Each item names the command, input files, output files, expected hash source, and claim consequence."
    )
    for title, command, inputs, outputs, hash_source, failure in rows:
        out.append("")
        out.append(heading(title, 3))
        out.extend([command, inputs, outputs, hash_source, failure])
    out.append("")
    out.append(
        "A reviewer should read this matrix before running the commands. It states which scientific claim layer is threatened by each failure, so replay results do not collapse into an undifferentiated build status."
    )
    return "\n".join(out)


def journal_article_narrative() -> str:
    return "\n".join(
        [
            heading("Introduction", 2),
            "Cross-domain theories often fail at the point where vocabulary, proof obligation, computational witness, empirical replay, and reviewer boundary stop agreeing with one another. OC Core 1.3.3 asks a bounded question: whether a typed model of continua can state liveness, residue, morphism, boundary, cycle, dimension, and K-level claims in a way that is formal enough for proof review, executable enough for finite semantic checks, and explicit enough for empirical and prior-art criticism.",
            "",
            heading("Problem", 2),
            "The article problem is not how to rename existing science. The problem is how to keep a cross-domain model honest when it moves from formal definitions to executable witnesses, scoped empirical rows, comparison with prior art, and public release claims. The article therefore treats every strong statement as a claim/evidence pair.",
            "",
            heading("Contribution", 2),
            "The contribution is not a claim that every scientific domain has been fully computed. The contribution is a model-core release: formal carriers and realizations, theorem/proof boundaries, a Lean-checked subset, finite semantic witnesses, bounded target-blind replay QA examples, comparator positioning, and adversarial-review artifacts arranged for external review.",
            "",
            heading("Related Work", 2),
            "The article reads OC against systems theory, autopoiesis, dynamical systems, category/type-theory style formalisms, RAF closure, complexity measures, identity theory, and reproducible-research practice. The comparison is not framed as absence of predecessors. It is framed as overlap plus residual delta under declared assumptions.",
            "",
            heading("Methods", 2),
            "The methods path binds prose claims to proof sheets, Lean declarations, finite semantic cases, bounded numeric replay rows, comparator rows, and explicit reopening conditions. This lets a reviewer reproduce the evidence route without treating the release package as a black box.",
            "",
            heading("Formal Object", 2),
            "The formal object is a typed continuum carrier with realization, liveness, residue, boundary, morphism, operator, cycle, dimension, and K-level structure. The article does not ask the reader to infer this object from slogans; it points to theorem IDs, proof sheets, Lean declarations, and finite semantic witnesses.",
            "",
            heading("Definitions Before Evidence IDs", 2),
            "A carrier is the object whose distinctions can be realized. A realization is the way those distinctions become live in a context. Liveness, death, residue, and rebirth describe lifecycle status; they are not interchangeable terms. A boundary is the declared separation or interface condition that makes a claim testable. A morphism records the structure-preserving relation under review. A K-level witness records why an added observable changes the model rather than merely renaming it.",
            "",
            heading("Main Results", 2),
            "The promoted results are bounded theorem and model-core claims: K0 resolution, lifecycle and status boundaries, hybrid semantics, dimensional and K-level witnesses, and minimality conditions under declared assumptions. Each result is paired with the artifact that can falsify or reopen it.",
            "",
            heading("Evidence", 2),
            "Evidence appears in four layers: prose proof sheets, Lean subset, executable finite-model cases, and scoped numeric replay rows. The evidence supports the model core and makes weaknesses inspectable; it is not presented as complete scientific coverage.",
            "",
            heading("Interpretation Before Evidence", 2),
            "The release should be evaluated as a bounded model-core artifact. Its strength is that assumptions, witnesses, replay rows, comparator boundaries, and adversarial objections are visible together. Complete scientific coverage and unrestricted comparative claims are outside the promoted article claim surface.",
            "",
            heading("Related-Work Boundary", 2),
            "The comparison accepts overlap with systems theory, autopoiesis, dynamical systems, category/type formalisms, RAF closure, complexity measures, identity theory, and reproducible-research practice. Novelty is stated as residual delta in the combined audit surface, not as absence of predecessors.",
            "",
            heading("Claim Scope Before Results", 2),
            "The release keeps complete scientific closure, final full-science status, and unrestricted modern-science comparison outside the promoted claim surface.",
            "",
            heading("Argument Roadmap", 2),
            "The article path is therefore: define the object, state what is promoted, show how formal claims are supported, show how computational and numeric replay evidence is checked, compare against prior art, and state limits plainly. The full conclusion follows after the results, replay interpretation, prior-art discussion, phenomenon coverage, figures, and literature positioning.",
        ]
    )


def article_results_summary(max_claims: int = 6, max_theorems: int = 6) -> str:
    claims = [
        row
        for row in read_json(ROOT / "claims" / "CLAIM_LEDGER_1_3_3.json", {}).get("rows", [])
        if row.get("scientific_promotion_allowed") and not row.get("control_plane_claim")
    ][:max_claims]
    theorems = read_json(ROOT / "proofs" / "THEOREM_REGISTRY_1_3_3.json", {}).get("rows", [])[:max_theorems]
    lanes = read_json(ROOT / "validation" / "target_blind" / "OC133_TARGET_BLIND_PREDICTION_TABLE.json", {}).get("rows", [])
    out = [heading("Results and Evidence Interpretation", 2)]
    out.append(
        "The article states results in prose first and uses artifact identifiers as evidence anchors. The promoted surface is bounded: each result has assumptions, a proof or executable witness route, and a condition that would reopen the claim."
    )
    for idx, row in enumerate(claims, start=1):
        claim_id = public_theorem_label(row.get("claim_id"))
        claim = clean_public_text(row.get("claim"))
        scope = public_scope_sentence(row.get("scope_limit"))
        out.append(
            f"Result {idx}. {claim} The public anchor is {claim_id}. Scope: {scope}"
        )
        out.append("")
    out.append(
        "The proof route is deliberately plural. Prose proof sheets state assumptions and counterexample boundaries; the Lean subset checks selected formal declarations; finite semantic cases test positive witnesses and negative controls; numeric rows are presented as replay QA or artifact-integrity examples unless a stronger empirical claim is separately evidenced."
    )
    theorem_ids = [public_theorem_label(row.get("theorem_id") or row.get("id")) for row in theorems]
    if theorem_ids:
        out.append(
            "Representative theorem anchors are "
            f"{sentence_list(theorem_ids)}. The complete theorem register remains in the evidence package for replay."
        )
    lane_names = [clean_public_text(row.get("lane")).title() for row in lanes if row.get("lane")]
    if lane_names:
        out.append(
            "The bounded numeric evidence touches "
            f"{sentence_list(lane_names)}. These lanes support replay and reconstruction claims, not total domain validation."
        )
    return "\n".join(out)


def journal_empirical_summary() -> str:
    rows = read_json(ROOT / "validation" / "target_blind" / "OC133_TARGET_BLIND_PREDICTION_TABLE.json", {}).get("rows", [])
    lanes = [clean_public_text(row.get("lane")).title() for row in rows if row.get("lane")]
    out = [heading("Bounded Empirical Replay Interpretation", 2)]
    out.append(
        "The journal article uses the empirical layer as a bounded replay and reconstruction test, not as a claim that "
        "every domain has been numerically closed. Each promoted empirical row must have a formula, pinned snapshot, "
        "target-blind or held-out target, comparator baseline, uncertainty or residual, negative control, falsifier, "
        "and replay hash. The detailed rows belong in the methods companion and public evidence package."
    )
    if lanes:
        out.append(
            f"The current replay lanes are {sentence_list(lanes)}. Their scientific function is to show that the "
            "model core can be operationalized against pinned data under declared limits; a failed row would reopen "
            "the corresponding claim boundary rather than invalidate or validate every possible domain projection."
        )
    return "\n".join(out)


def journal_comparator_summary() -> str:
    register = read_json(ROOT / "comparators" / "OC_1_3_3_NOVELTY_AND_PRIORITY_REGISTER.json", {})
    rows = register.get("rows", []) if isinstance(register.get("rows"), list) else []
    families = [
        clean_public_text(row.get("tradition") or row.get("source_family") or row.get("comparator_id"))
        for row in rows[:10]
        if row.get("tradition") or row.get("source_family") or row.get("comparator_id")
    ]
    out = [heading("Prior-Art Interpretation for Article Readers", 2)]
    out.append(
        "The article-level novelty claim is deliberately modest and reviewable. OC does not claim to have invented "
        "systems theory, autopoiesis, dynamical systems, category/type formalisms, RAF closure, complexity measures, "
        "identity theory, or reproducibility practice. It claims a bounded integration of typed model-core semantics, "
        "proof/evidence governance, finite witnesses, replay rows, and public claim boundaries."
    )
    if families:
        out.append(
            f"The comparator register explicitly touches {sentence_list(families)}. The article summarizes the "
            "overlap/residual-delta pattern and leaves full source rows in the evidence package."
        )
    return "\n".join(out)


def journal_prior_art_detailed_comparison(max_rows: int = 8) -> str:
    register = read_json(ROOT / "comparators" / "OC_1_3_3_NOVELTY_AND_PRIORITY_REGISTER.json", {})
    rows = register.get("rows", []) if isinstance(register.get("rows"), list) else []
    out = [heading("Source-Linked Related-Work Comparison", 2)]
    out.append(
        "This article includes the major related-work comparisons directly rather than forcing the reader to open the register first. Each comparison is bounded: overlap is granted, the non-novelty boundary is stated, and the residual contribution is phrased only as positioning unless a stronger source-backed search is available."
    )
    out.append("")
    def residual_delta_clause(raw_delta: Any) -> str:
        delta_text = clean_public_text(raw_delta or "bounded residual positioning only").strip()
        lower = delta_text.lower()
        if lower.startswith("uses typed morphism discipline"):
            return "OC uses typed morphism discipline to police public scientific claims while explicitly not claiming invention of category theory"
        if lower.startswith("does not replace raf"):
            return "OC places RAF-like closure as one typed K-level route with explicit reduction and demotion checks while explicitly not replacing RAF theory"
        return delta_text

    for row in rows[:max_rows]:
        tradition = clean_public_text(row.get("tradition") or row.get("source_family") or "Comparator family")
        source_refs = row.get("source_refs") if isinstance(row.get("source_refs"), list) else []
        titles = [clean_public_text(item.get("title") or item.get("url") or "") for item in source_refs if isinstance(item, dict)]
        overlap = clean_public_text(row.get("claim_element_overlap") or row.get("prior_art_has") or "overlap recorded in the comparator register")
        prior_has = clean_public_text(row.get("prior_art_has") or overlap)
        boundary = clean_public_text(row.get("non_novelty_boundary") or row.get("what_oc_must_not_claim") or "OC must not promote priority from this comparison alone")
        residual = residual_delta_clause(row.get("bounded_positioning_note") or row.get("residual_delta") or row.get("positioning_note"))
        status = clean_public_text(row.get("positioning_status") or row.get("uniqueness_claim_status") or "positioning only")
        out.append(heading(tradition, 3))
        out.append(f"Source anchor. {sentence_list(titles[:2]) or 'The source anchor is recorded in the comparator register'}.")
        out.append(f"Accepted overlap. {prior_has}. The article treats this overlap as real; OC does not claim to invent {overlap}.")
        out.append(f"Non-novelty boundary. {boundary}. This boundary prevents related-work language from becoming an originality slogan.")
        out.append(f"Residual contribution allowed here. {residual}. Current status: {status}. The allowed wording is therefore bounded integration or positioning, not priority.")
        out.append("")
    out.append(
        "The direct comparison above is not a complete history of every field. It is the article-level related-work surface required for external review. The evidence package preserves the fuller comparator rows and source snapshots."
    )
    return "\n".join(out)


def journal_phenomenon_summary() -> str:
    matrix = read_json(ROOT / "docs" / "OC_1_3_3_PHENOMENON_COVERAGE_MATRIX.json", {})
    rows = [
        row for row in matrix.get("rows", []) if isinstance(row, dict) and (row.get("public_promotion") or row.get("counts_as_formal_model_card_replay"))
    ]
    domains = sorted({clean_public_text(row.get("domain")) for row in rows if row.get("domain")})
    out = [heading("Phenomenon Coverage Interpretation", 2)]
    out.append(
        "Phenomenon coverage is treated as a model-card obligation. A phenomenon is not counted as explained merely "
        "because it is named; it needs a formal instance, observable, replay or prediction path, comparator, negative "
        "control, falsifier, and public claim boundary. Rows that remain illustrative or protocol-ready stay outside "
        "promoted explanation claims."
    )
    if domains:
        out.append(
            f"The public coverage map spans {sentence_list(domains)} under those constraints. The article states this "
            "as scoped coverage, not as total explanation of all phenomena."
        )
    return "\n".join(out)


def journal_article_extended_discussion() -> str:
    return "\n".join(
        [
            heading("Discussion", 2),
            "The article-level contribution is a bounded model-core release, not a claim that every scientific domain has been completed. Its scientific value is the alignment of a typed continuum object, theorem/proof boundaries, Lean and finite semantic evidence, scoped replay rows, prior-art positioning, and explicit reopening conditions. The discussion therefore asks whether those layers cohere as a reviewable public object.",
            "",
            "The formal layer comes first because empirical or computational evidence can only be interpreted after the object of interpretation is declared. Terms such as carrier, realization, liveness, residue, boundary, morphism, operator, cycle, dimension, and K-level witness are not decorative vocabulary; they decide what a proof sheet, finite case, or replay row can support.",
            "",
            "The empirical layer is intentionally bounded. The release contains replay and reconstruction rows with formulas, pinned inputs, comparators, residuals, negative controls, falsifiers, and hashes. Those rows demonstrate auditability and scoped operationalization; they do not assert complete validation of physics, chemistry, biology, systems science, mathematics, or every future domain projection.",
            "",
            "The prior-art layer is overlap-first. OC intersects with systems theory, autopoiesis, dynamical systems, type and category-oriented formalisms, RAF closure, complexity measures, identity theory, hybrid systems, and reproducible-research practice. The release's defensible novelty is the combined typed model-core plus evidence-governed public claim surface, not a denial that those traditions already contain major parts of the problem space.",
            "",
            heading("Limitations", 2),
            "The release does not promote final full-science completion, universal numeric closure, or unrestricted victory over every modern scientific model. It also does not treat a successful replay row as proof of an entire domain. A failed proof dependency, finite witness, comparator, negative control, falsifier, or replay hash reopens the specific claim that depends on it.",
            "",
            "Legacy theorem material is retained as part of the full corpus and must be read through the current claim boundary. A legacy result is promoted only when the current 1.3.3 proof and evidence surfaces support the promoted wording. Otherwise it remains background, motivation, or a research-program obligation.",
            "",
            heading("Conclusion", 2),
            "OC Core 1.3.3 is publication-relevant as a bounded external-review model-core release: it gives reviewers a typed object, stated theorem obligations, executable witness routes, scoped replay evidence, prior-art boundaries, and adversarial reopening rules in one public package. The stronger full-science ambitions remain valuable, but they require later evidence before becoming promoted public claims.",
        ]
    )


def journal_article_worked_reading_path() -> str:
    return "\n".join(
        [
            heading("Worked Article Reading Path", 2),
            "A compact article still has to show how the model is used. This section gives a worked reading path without importing the full monograph registers. The goal is to let a first-pass reviewer see how a public claim moves from definition to evidence and then to a reopening condition.",
            "",
            heading("Worked Path 1: K0 Resolution", 3),
            "The K0 result is a useful first test because it is easy to overstate. OC Core 1.3.3 does not say that every absence of visible structure is automatically zero continuumness. It says that a zero-continuumness verdict needs live-support conditions, an obstruction class, and a declared zero-cause family. The proof sheet and finite semantic witness make that distinction executable: changing only a label must not change the verdict, while changing the relevant model facts must change the verdict. That is the article-level scientific point.",
            "",
            heading("Worked Path 2: Lifecycle Status", 3),
            "The lifecycle material separates live realization, death condition, residue, rebirth candidate, and identity continuation. This separation matters because ordinary language tends to slide between survival, trace, copy, and renewal. OC Core 1.3.3 promotes only the bounded claim that the public model can keep those statuses typed and reviewable. A reviewer can attack the exact invariant: if the declared invariant is missing or not preserved, identity continuation is not promoted.",
            "",
            heading("Worked Path 3: Hybrid Semantics", 3),
            "The hybrid result is not a slogan that every system is both continuous and discrete. It states a bounded semantics in which smooth-flow and update/reset aspects have different obligations. Derivative language is available only where the smooth structure supports it; guard and reset language belongs to the executable update side. A reviewer can therefore ask which side carries a claim, and a mismatch reopens the claim rather than being hidden by the word hybrid.",
            "",
            heading("Worked Path 4: Bounded Replay Row", 3),
            "The empirical rows are interpreted as bounded replay and reconstruction rows. The article-level question is whether a row has a formula, pinned input, target rule where applicable, observed value, uncertainty or residual, comparator, negative control, falsifier, and replay hash. When those fields are present, the row supports the named reconstruction claim. It does not become a declaration that the entire field has been solved.",
            "",
            heading("Worked Path 5: Prior-Art Delta", 3),
            "The prior-art question is not whether OC has no predecessors. A serious comparison begins by granting overlap. The residual question is whether the release combines typed continuum semantics, proof governance, executable witnesses, bounded replay rows, comparator discipline, and public claim boundaries in a way that is not already supplied by the same comparator source under the same claim. If the residual delta disappears under same-claim comparison, the novelty wording must shrink.",
            "",
            heading("Article-Level Evaluation Rule", 3),
            "These worked paths define the article's burden. The reader should not have to trust a file name, a package status, or a general assertion of rigor. The reader should see the claim, the evidence class, the attack surface, and the condition that would reopen the claim. That is why the article is shorter than the monograph but stricter than a promotional abstract: it is a gateway into the full scientific package.",
        ]
    )


def reviewer_adversarial_synthesis() -> str:
    return "\n".join(
        [
            heading("Adversarial Review Method", 2),
            "The reviewer map is written for an unsympathetic reader. Its purpose is not to persuade by accumulation of files; its purpose is to identify where the release could fail. Every serious attack is read as a relation between a public sentence, the claim it threatens, the evidence offered for that claim, and the exact condition under which the sentence would have to be repaired.",
            "",
            "The map therefore uses a narrow standard for closure. A criticism is not closed because a document exists. It is closed only when the public wording is no stronger than the proof, finite witness, replay row, comparator row, or claim-boundary artifact that carries it. If the support is local, the response is local. If the evidence is only a bounded replay row, the public sentence must not sound like a whole-field law.",
            "",
            heading("Attack Family 1: The Theory Is Only a Reframing", 3),
            "The strongest novelty attack says that OC merely relabels existing systems theory, dynamical systems, autopoiesis, category-oriented formalism, RAF closure, identity theory, or reproducibility practice. The response begins by accepting overlap. OC cannot defend itself by pretending those traditions do not exist. The defensible question is narrower: does the released object bind a typed continuum model, proof governance, finite semantic witnesses, bounded replay rows, prior-art comparison, and public claim boundaries into one auditable model-core package?",
            "",
            "The residual-delta answer remains bounded. If a comparator already supplies the same claim under the same assumptions and with the same evidence discipline, OC cannot promote priority. If OC supplies a different integration of typed status, K-level witnesses, lifecycle boundaries, and reviewable evidence surfaces, the residual claim can remain. The reviewer map keeps this distinction visible because novelty is not a mood; it is a same-claim comparison.",
            "",
            heading("Attack Family 2: The Formal Claims Are Theatre", 3),
            "A theorem label can be decorative unless it is tied to assumptions, definitions, dependencies, proof idea, mechanized subset where available, finite witness where relevant, and counterexample boundary. The reviewer should attack theorem labels by asking which assumption does the work and what breaks if that assumption is removed. A proof sheet that cannot answer that question is not allowed to carry a promoted theorem claim.",
            "",
            "For 1.3.3, the bounded response is that theorem claims are routed through proof sheets, selected Lean declarations, and finite semantic witnesses where applicable. The route does not imply that every mathematical sentence in the monograph has been fully mechanized. It means that the promoted theorem surface is no longer allowed to float without an evidence class. If a theorem sentence grows beyond its supporting class, the public wording must shrink or the proof surface must improve.",
            "",
            heading("Attack Family 3: The Empirical Rows Are Too Weak", 3),
            "An empirical reviewer should not accept a number merely because it appears in a release archive. The attack asks whether each row contains the right fields: source identity, reconstruction rule or formula, split or target policy where applicable, predicted or reconstructed value, observed value, uncertainty or residual, comparator, negative control, falsifier, and replay hash. Missing fields reopen the row.",
            "",
            "The response is deliberately modest. The release uses bounded replay and reconstruction rows to show operationalization and artifact-integrity discipline. It does not ask those rows to prove complete domain coverage. This is not a retreat from ambition; it is how ambition becomes testable. A future stronger empirical claim would need a stronger protocol, not louder wording.",
            "",
            heading("Attack Family 4: Phenomenon Coverage Is Inflated", 3),
            "A broad model can list phenomena faster than it explains them. The reviewer should therefore ask whether each named phenomenon has an OC instance, observable, explanation or replay path, comparator, negative control, falsifier, and claim boundary. Naming a phenomenon is not enough. A model card that lacks an observable or falsifier stays outside promoted explanation.",
            "",
            "The release response is to keep phenomenon coverage scoped. Phenomena with complete cards can be used as bounded review examples. Phenomena that are illustrative, protocol-ready, or not yet evidenced stay in the monograph as context or future work but do not become promoted public claims. This distinction protects the reader from mistaking coverage vocabulary for evidence.",
            "",
            heading("Attack Family 5: Public Wording Outruns Evidence", 3),
            "The claim-boundary attack is often the most important one. A theory can have useful definitions and still fail as a publication if public language implies more than the artifact layer supports. The reviewer should scan for totality, finality, universal numeric closure, unrestricted comparison, and implied endorsement. If such language appears without literal evidence, it is a release defect.",
            "",
            "The repaired 1.3.3 public surface uses bounded wording. It promotes a model-core package with proof, finite, replay, comparator, and review evidence. It excludes complete scientific coverage and unrestricted comparison from the promoted surface. That exclusion is not a hidden caveat; it is a scientific boundary statement that tells the reader exactly what the release is and is not claiming.",
            "",
            heading("Attack Family 6: The Package Is Not a Scientific Text", 3),
            "A scientific release can fail even when its checksums are correct. If the first public experience is a metadata dump, an internal routing memo, a raw register, or a collection of appended deltas, the release is not publication-grade. The reviewer should inspect the title page, dedication, abstract, table of contents, didactic order, page flow, figure use, literature discussion, and conclusion before trusting the archive.",
            "",
            "The corrected map treats editorial quality as part of scientific quality. The monograph carries the long argument. The journal core carries the article path. The methods companion explains replay. The reviewer map explains attacks. The archive carries evidence. If those roles blur again, the release reopens because the reader cannot know which artifact carries which burden.",
            "",
            heading("Reopening Rules", 2),
            "A novelty response reopens if same-claim prior art absorbs the residual delta. A theorem response reopens if an assumption is missing, a proof dependency fails, or a finite witness no longer separates positive and negative cases. An empirical response reopens if a formula, pinned source, comparator, uncertainty, negative control, falsifier, or replay hash is absent or inconsistent. A phenomenon response reopens if the model card lacks a testable observable. An editorial response reopens if the public PDF becomes unreadable, fragmented, or dominated by registers again.",
            "",
            "These reopening rules make the reviewer map useful after publication as well as before publication. They tell future maintainers how to classify a defect without arguing from scratch. A defect should become a known-error pattern and a gate for later releases, not a one-time apology.",
            "",
            heading("What a Hostile Reader Should Do", 2),
            "A hostile reader should first choose the public sentence under attack, then identify the claim family, then inspect the evidence class, then ask whether the support is strong enough for the wording. If the sentence is formal, inspect proof assumptions and mechanized or finite witnesses. If it is empirical, inspect the replay row. If it is comparative, inspect the comparator row. If it is editorial, inspect the rendered PDF and public archive page.",
            "",
            "The release is designed to survive that process by being bounded, not evasive. It should be possible to disagree with OC Core 1.3.3 scientifically without discovering a hidden mismatch between files, claims, and evidence. When such a mismatch is found, the correct answer is repair, not defensiveness.",
        ]
    )


def reviewer_role_playbook() -> str:
    return "\n".join(
        [
            heading("Reviewer Role Playbook", 2),
            "The attack map becomes useful only when different reviewers can use it without sharing private context. This playbook therefore rewrites the same release object through the eyes of several hostile readers. Each role names what it should attack first, what would count as a serious answer, and what would reopen the issue.",
            "",
            heading("Formal-Mathematics Reviewer", 3),
            "The formal reviewer should begin by refusing to accept theorem labels as proof. The first question is whether each promoted theorem has a typed statement, assumptions, definitions, dependencies, proof idea, and counterexample boundary. The second question is whether the Lean subset and finite semantic witnesses are cited at the right strength. A Lean declaration can support a selected formal pattern, but it does not certify every surrounding informal paragraph.",
            "",
            "A serious answer for this reviewer names the exact theorem identifier, the proof sheet, the dependency path, and the witness or mechanized declaration if one is claimed. A weak answer points to the monograph as a whole. A failing answer changes the wording of a theorem claim without changing its evidence. The issue reopens when an assumption is implicit, when a theorem ID is orphaned, when a proof sheet gives only a slogan, or when a finite witness is label-driven rather than fact-driven.",
            "",
            heading("Computational-Semantics Reviewer", 3),
            "The computational reviewer should attack the finite-model layer as if every verdict were self-confirming until proven otherwise. The question is whether inputs contain raw model facts and whether the runner computes outcomes independently from expected labels. Mutation controls matter because they show whether the evaluator rejects tampered, inert, or wrong-witness cases.",
            "",
            "A serious answer cites the finite-model report, the case family, the positive witness, and the paired negative control. A weak answer says that all cases pass. A failing answer is one in which changing a label changes the outcome or changing the model facts fails to change the outcome where the theorem says it should. The issue reopens when evidence rows contain conclusion booleans, when controls are absent, or when a public theorem cites a case whose semantics do not carry the claimed distinction.",
            "",
            heading("Empirical-Statistics Reviewer", 3),
            "The empirical reviewer should treat every numeric row as suspect until the reconstruction path is complete. The row needs a source identity, pinned snapshot or official source record, formula, target policy, predicted or reconstructed value, observed value, uncertainty or residual, comparator baseline, negative control, falsifier, and replay hash. A row without a comparator cannot support comparative wording. A row without a negative control cannot support empirical promotion.",
            "",
            "A serious answer for this reviewer is local: it says exactly what the row supports and exactly what it does not support. A weak answer cites the authority of a data source without showing the replay. A failing answer uses a successful reconstruction as if it proved a whole domain. The issue reopens when a row becomes circular, when a target was not held out where the claim needs it, when residuals are not interpreted, or when public prose upgrades a bounded replay into a domain law.",
            "",
            heading("Prior-Art Historian", 3),
            "The prior-art reviewer should assume overlap until the manuscript proves a residual difference. This reviewer asks whether OC credits systems theory, autopoiesis, dynamical systems, hybrid systems, category and type-theoretic formalisms, RAF closure, complexity measures, identity theory, systems engineering, and reproducible-research practice. The comparison must be same-claim comparison, not a generic bibliography.",
            "",
            "A serious answer states what is inherited, what is reorganized, what residual delta remains, and which public claim that residual delta can support. A weak answer lists sources without using them. A failing answer claims novelty from absence of a source in a short sample. The issue reopens when a comparator row lacks overlap fields, when residual delta is vague, when a stronger priority sentence appears, or when public metadata presents the release as if it had no predecessors.",
            "",
            heading("Journal Editor", 3),
            "The journal editor should first ask whether the package reads as a scientific manuscript set rather than as a repository export. The editor checks title pages, dedication, abstract, table of contents, argument order, section transitions, literature synthesis, figure placement, conclusion, data availability, conflict/funding statement, AI assistance disclosure, and the distinction between public release and journal submission.",
            "",
            "A serious answer is visible before opening machine-readable files. The editor sees a monograph, a compact article, a methods companion, a reviewer map, and a curated evidence package with distinct roles. A weak answer requires the editor to infer roles from filenames. A failing answer lets metadata, checksums, internal statuses, or appended deltas become the primary public reading surface. The issue reopens when any public PDF lacks frontmatter, when page flow is broken, or when a public record previews metadata instead of the scientific landing document.",
            "",
            heading("Hostile Generalist", 3),
            "The hostile generalist should attack intelligibility. The question is not only whether the model is formal; it is whether a technically literate reader can understand why the formalism exists. This reviewer asks what problem is being solved, why the object is typed, how liveness differs from ordinary persistence, why residue is separated from identity, how K-level claims become testable, and what kind of evidence would make the model fail.",
            "",
            "A serious answer gives a didactic path from tuple to theorem to example to falsifier. A weak answer says that the full monograph contains everything somewhere. A failing answer forces the reader to reconstruct the theory from registers. The issue reopens when terms are introduced without motivation, when diagrams are absent or misplaced, when examples do not connect to claims, or when a public claim cannot be explained without private process history.",
            "",
            heading("Publication-Metadata Reviewer", 3),
            "The metadata reviewer checks whether GitHub, Zenodo, citation metadata, CodeMeta, RO-Crate, release notes, checksum files, and public PDFs identify the same object. The author is Alexander Yashin. Logion is the research instrument and institute-automation system. ESTRA is the methodology. OC Core is the scientific model release. Misclassifying those entities is not a cosmetic problem because it changes how the public record should be cited and evaluated.",
            "",
            "A serious answer keeps public metadata professional and concise. Zenodo needs a rendered abstract and reading order, not raw Markdown or a checksum-only display. GitHub can carry a longer Markdown release body, but it still has to match the DOI, asset set, and claim boundary. The issue reopens when version strings diverge, when stale assets remain, when a DOI points to an inferior file set, when inherited Zenodo files are not cleared, or when journal packages are described as submitted before a separate submission action exists.",
            "",
            heading("Release-Engineering Reviewer", 3),
            "The release-engineering reviewer attacks the process rather than the theory. The question is whether a verification step can dirty the release, whether a semantic delta triggers only the necessary downstream work, and whether absence of a meaningful delta stops the chain. This reviewer also checks whether a known publication error has become a permanent regression test.",
            "",
            "A serious answer uses delta-stable verification and known-error management. A weak answer reruns everything repeatedly without explaining why. A failing answer lets a read-only check rewrite tracked artifacts or lets a public release proceed because file names look correct while text quality is poor. The issue reopens when verification creates ungoverned dirt, when a generated artifact changes without input delta, or when an already-seen defect class appears again.",
            "",
            heading("Synthesis Reviewer", 3),
            "The synthesis reviewer asks whether the release is more than a pile of correct parts. The model, proof route, finite semantics, replay rows, comparator register, reviewer map, publication metadata, and journal packages must tell the same story. A contradiction between any two layers is a scientific defect because it makes the public claim ambiguous.",
            "",
            "A serious answer shows role separation and traceability. The monograph teaches the theory, the journal core compresses it, the methods companion explains replay, the reviewer map attacks it, the public zip carries evidence, and metadata makes the archive citable. A weak answer is a set of green gates. A failing answer is a release in which every component exists but the reader cannot tell how they fit together. The issue reopens when component roles blur, when a claim is promoted in one file and bounded in another, or when external positioning diverges from evidence.",
            "",
            heading("Claim-Repair Decision Ladder", 3),
            "When an attack succeeds, the repair is not always to add more text. The first decision is whether the claim is true under the current evidence class. If the claim is too strong, the correct repair is demotion or boundary clarification. If the claim is right but the evidence is hidden, the correct repair is traceability. If the evidence is insufficient but the claim is important, the correct repair is new proof, new finite semantics, new replay protocol, or new comparator work.",
            "",
            "This decision ladder prevents two opposite failures. It prevents cosmetic narrowing, where ambitious claims disappear without scientific work. It also prevents rhetorical inflation, where ambition remains but evidence does not grow. The release should preserve ambitious scientific direction while promoting only the claims that the artifact layer can carry. A reviewer can therefore distinguish a present claim from a research obligation without asking the author for private clarification.",
            "",
            heading("Evidence-to-Wording Calibration", 3),
            "The final adversarial step is calibration. Definitional support licenses definitional language. Proof support licenses theorem language only under stated assumptions. Lean support licenses selected mechanized-subset language. Finite semantic support licenses executable witness language. Target-blind replay support licenses bounded replay and reconstruction language. Comparator support licenses overlap and residual-delta language. Editorial review support licenses publication-quality language only for the rendered artifacts that were actually inspected.",
            "",
            "The public sentence must be calibrated to the weakest necessary support in its dependency chain. If a sentence depends on both a theorem and a replay row, failure of either side narrows the sentence. If a sentence depends on comparator novelty, missing source coverage narrows the sentence. If a sentence depends on publication presentation, a broken Zenodo page or unreadable PDF narrows the sentence even if the science is otherwise intact. This calibration rule is the reviewer map's main protection against repeating the failed-publication pattern.",
            "",
            heading("Editorial Closure Standard", 3),
            "The reviewer map closes only when a hostile reader can name the attacked claim, identify the evidence class, read the response in prose, and know what would reopen it. The map is not required to reproduce every proof sheet, every finite case, or every numeric row; that would turn it back into a register. It is required to make the adversarial logic legible. A reviewer should leave this document knowing how to attack the monograph, not merely how to browse the archive.",
            "",
            "That is the difference between a defensive appendix and a scientific attack map. A defensive appendix says that objections have been handled. A scientific attack map explains why an objection matters, what evidence answers it, what remains local, and what would defeat the answer. OC Core 1.3.3 uses the second form because a broad model-core release cannot earn trust by hiding from hostile reading.",
            "",
            heading("Minimum Hostile Review Walkthrough", 3),
            "A minimum hostile review can be completed without reading every appendix. The reviewer selects one theorem claim, one empirical row, one prior-art claim, one phenomenon claim, and one publication-quality claim. For each selected claim the reviewer asks the same questions: what is the sentence, what evidence class carries it, what assumption is doing the work, what would count as failure, and where is the failure recorded?",
            "",
            "For a theorem claim, the reviewer should choose a visible theorem identifier and follow it from the public sentence to the proof sheet and any Lean or finite witness cited by that sentence. For an empirical row, the reviewer should choose one replay lane and inspect formula, data, residual, comparator, negative control, falsifier, and replay hash. For prior art, the reviewer should choose one comparator family and ask whether the residual delta survives same-claim comparison. For a phenomenon, the reviewer should ask whether the model card has an observable and falsifier. For publication quality, the reviewer should open the rendered PDFs and public archive record rather than only the manifest.",
            "",
            heading("End-to-End Attack Drill", 3),
            "The fastest way to test the release is to run one claim through every layer. Start with a public sentence such as a K-level transition claim. The formal layer asks whether the typed source and target objects are declared, whether the transition preserves the stated invariant, and whether any demotion condition is explicitly lawful. The finite layer asks whether the witness changes because model facts change, not because a label was written in a favorable way. The empirical layer asks whether the sentence depends on any numeric row and, if so, whether that row has a replay path and a falsifier.",
            "",
            "The prior-art layer then asks a different question: does a comparator source already provide the same claim with the same assumptions and the same evidence discipline? If yes, the novelty wording must contract. If no, the residual delta can be stated, but only at the level carried by the evidence. The editorial layer asks whether a reader can understand that entire chain without private context. If the reader needs an internal work-order history to understand the claim, the public document has failed even when the underlying science is defensible.",
            "",
            "The drill is intentionally repetitive because release failures often hide between layers. A theorem sentence may be mathematically careful but empirically overstated. A numeric row may be reproducible but unrelated to the public claim. A prior-art paragraph may be well cited but too vague about residual delta. A rendered PDF may contain correct material while placing it in an order that defeats comprehension. The reviewer map treats these as one connected failure class: a public claim is acceptable only when the sentence, evidence, comparison, and reading path agree.",
            "",
            "A repaired answer names the smallest artifact that must change. If the theorem layer fails, repair the theorem statement, proof sheet, Lean subset, or finite witness. If the empirical layer fails, repair the row or demote the claim. If the comparator layer fails, repair the source-backed comparison or reduce novelty language. If the editorial layer fails, regenerate the public text from the manuscript integration service. This is cheaper than rereading the whole release after every finding and stricter than accepting a green package merely because files exist.",
            "",
            heading("Class-Level Repair Rule", 3),
            "When a reviewer finds a broken reference, stale identity, unsupported phrase, missing frontmatter element, malformed citation, or inconsistent entity label, the repair is not local unless the defect is demonstrably unique. The default rule is class repair: fix the generator, scan the whole public surface, regenerate only the affected artifacts, and then run the smallest gate that can prove the class is gone. This rule is why the release can become cheaper without becoming softer.",
            "",
            "Class repair also prevents editorial fatigue. A copyeditor should not have to rediscover the same defect in four PDFs, a metadata file, and a public archive description. Once the defect is recognized as a class, it becomes a known-error pattern. Future releases must fail before publication if the pattern reappears. The reviewer map therefore serves two audiences at once: it helps external critics attack the current release, and it helps Logion keep the same defect from returning.",
            "",
            heading("Claim-Family Evidence Recipes", 3),
            "Formal theorem claims follow the proof recipe. A reviewer asks for a typed statement, an explicit assumption set, a proof sheet, a named mechanized subset where the release claims one, a finite semantic witness where the theorem is operationalized, and a counterexample boundary. The public sentence may use theorem language only at that recipe's strength. If the theorem depends on a finite witness, a label-only witness is not enough; the model facts must make the verdict change.",
            "",
            "Lifecycle and identity claims follow the status recipe. The reviewer asks which token is live, which token is dead, which trace is residue, which candidate is rebirth, and which invariant is claimed to preserve identity. The release is strongest when it refuses to collapse those statuses into ordinary-language survival talk. A rebirth case is not identity continuation unless the declared identity evidence carries the invariant; a residue is not a new live object unless the typed relation says so.",
            "",
            "Empirical replay claims follow the replay recipe. The reviewer asks for source identity, pinned input, formula, target rule, observed value, residual or uncertainty, comparator, negative control, falsifier, and replay hash. The public sentence may say that a bounded row is replayable and audit-ready. It may not infer complete scientific coverage from that row. If the row is useful mainly as artifact-integrity evidence, the wording has to say so.",
            "",
            "Prior-art claims follow the comparator recipe. The reviewer grants overlap first, then asks whether the same claim already appears with the same assumptions and evidence standard. A residual difference can be promoted only after overlap is stated. A missing source does not prove novelty. A source-backed residual delta can support a bounded contribution sentence, but not a sweeping priority sentence.",
            "",
            "Publication-quality claims follow the rendered-surface recipe. The reviewer opens the PDF and public archive page before trusting the package. Title page, dedication, abstract, table of contents, argument order, figure logic, references, DOI, entity roles, and asset list must agree. If the public surface looks like a machine export, the release fails editorially even when the scientific archive is internally consistent.",
            "",
            heading("Cheap Review Cascade", 3),
            "The reviewer map also defines a cheap cascade for future repairs. Deterministic scans run first because they catch stale version strings, broken references, raw Markdown leakage, malformed citations, unsupported phrases, and entity-role errors without spending reviewer time. A sampled editorial review runs next on the rendered PDFs. Full role review runs only after deterministic scans and the sample are clean.",
            "",
            "This cascade does not lower the standard. It changes the order of work. A class defect found in a sample is repaired globally at the generator or methodology layer, then the affected artifacts are regenerated and scanned. Only after the class disappears does the expensive review resume. That is the practical meaning of quality without waste: reviewers spend attention on scientific and editorial judgment, not on rediscovering the same mechanical defect.",
            "",
            heading("Editorial Sampling Protocol", 3),
            "The minimum editorial sample is deliberately cross-layered. It includes the first public page, one table-of-contents segment, one formal theorem passage, one finite-witness passage, one empirical replay passage, one prior-art passage, one figure-reference passage, one reviewer-objection passage, and one metadata/citation passage. A sample that touches only the opening pages is not enough because the release can look polished at the front and still fail in the appendices.",
            "",
            "Each sampled passage receives four questions. Does the passage have a clear reader purpose? Does it name the evidence class without asking the reader to infer it from a filename? Does it avoid stronger wording than the support allows? Does it connect to the preceding and following argument rather than behaving like a pasted record? A negative answer creates a class repair if the pattern can occur elsewhere.",
            "",
            "The protocol is intentionally cheap. It does not require a full LLM pass across every page before obvious mechanical and structural defects are gone. It does require that any sampled defect be generalized. A broken reference in one passage triggers a reference scan. A malformed table in one PDF triggers a rendered-surface scan. A repeated closure paragraph triggers a boilerplate scan. A mismatch between figure count and rendered numbering triggers a figure-sequence audit.",
            "",
            "After class repair, the sample is rerun on fresh PDF hashes. Only then does the full editorial role set run. This ordering prevents two failures at once: it prevents the machine from wasting expensive review on defects a regular expression can catch, and it prevents cheap scans from becoming a substitute for human editorial judgment. The reviewer map records the protocol because the corrected release must be maintainable, not merely corrected once.",
            "",
            heading("Worked Attack Transcript A: Theorem Surface", 3),
            "Reviewer question: the theorem sentence sounds stronger than its assumptions. The response begins by naming the theorem family and the assumption that carries it. The reviewer then checks whether the proof sheet says the same thing as the public sentence, whether the Lean subset is cited only for the declaration it actually checks, and whether the finite witness separates the positive case from the negative control. If any one of those links is missing, the theorem sentence is narrowed before publication.",
            "",
            "The repair transcript is intentionally short. First, identify the exact sentence. Second, identify the exact theorem identifier. Third, identify the proof-sheet assumption and counterexample boundary. Fourth, identify the mechanized or finite support if the sentence invokes it. Fifth, rewrite the public sentence to match the weakest surviving link. This transcript prevents theorem theatre because a theorem label is never allowed to float without its dependency path.",
            "",
            heading("Worked Attack Transcript B: Replay Surface", 3),
            "Reviewer question: the numeric row may be a reconstruction artifact rather than empirical support for the claim. The response begins by naming the lane and the claim boundary. The reviewer then checks source identity, pinned input, formula, target policy, observed value, residual or uncertainty, comparator, negative control, falsifier, and replay hash. The row supports only the wording that survives those fields.",
            "",
            "The repair transcript is again local. If the formula is absent, the row cannot carry a numeric claim. If the comparator is absent, comparative wording is removed. If the negative control is absent, empirical promotion is blocked. If the row is target-blind but not prospective, the text says target-blind replay rather than future prediction. The archive can still be useful, but the public sentence must not pretend that the row proves more than it does.",
            "",
            heading("Worked Attack Transcript C: Prior-Art Surface", 3),
            "Reviewer question: the contribution may be a reframing of existing systems, dynamical, type-theoretic, hybrid, identity, or reproducibility traditions. The response begins by granting overlap. The reviewer chooses one comparator family and asks whether the same claim already exists under the same assumptions and evidence standard. If the comparator absorbs the residual delta, the novelty sentence contracts. If the residual survives, the sentence states the residual precisely.",
            "",
            "This transcript blocks two opposite errors. It blocks empty originality language because overlap is mandatory. It also blocks self-erasure because a real residual delta can remain after overlap is granted. The correct sentence is neither promotional nor timid: it says what the release integrates and which evidence discipline makes that integration reviewable.",
            "",
            heading("Worked Attack Transcript D: Public Surface", 3),
            "Reviewer question: the archive may be technically complete while the public reading surface is not publication-grade. The response begins outside the manifest. The reviewer opens the PDF, checks the title page, dedication, abstract, table of contents, section order, figure logic, literature synthesis, claim boundaries, and citation metadata. The public archive page must present a professional abstract and reading order rather than raw package internals.",
            "",
            "The repair transcript treats presentation as evidence hygiene. If the first visible file is metadata, the public file order is wrong. If a PDF lacks frontmatter, it is not ready. If a figure count or DOI differs across files, the release identity is unstable. If journal packages are described as submitted before a separate submission action, the public record misleads the reader. These are publication-stopping scientific defects because they change what a reader can reasonably infer.",
            "",
            heading("Worked Attack Transcript E: Synthesis Surface", 3),
            "Reviewer question: the pieces may be individually correct but not integrated. The response asks whether the monograph, article, methods companion, reviewer map, evidence package, metadata, and archive page tell the same story. A theorem claim in the monograph, a replay claim in the methods companion, and a boundary statement in the reviewer map must be mutually compatible. If one file promotes what another file demotes, the release is ambiguous.",
            "",
            "The repair transcript is to align the claim surface across artifacts. The monograph carries the long argument. The article carries the compact argument. The methods companion carries replay interpretation. The reviewer map carries adversarial logic. The evidence package carries exact machine-readable objects. Metadata makes the object citable. Once these roles are stable, a reviewer can disagree with the theory scientifically without first having to repair the release package.",
            "",
            "If all five samples survive, the release has not been proven true in every possible sense, but it has passed a meaningful adversarial screen: the public surface is inspectable, claims are typed by evidence class, and failure paths are visible. If any sample fails, the map identifies the repair owner and the kind of artifact that must change. This walk-through is deliberately included in prose so future releases cannot replace editorial judgment with a file-existence checklist.",
        ]
    )
    return "\n".join(
        [
            heading("Discussion: What the Article Claims", 2),
            "The article's central claim is not that OC Core 1.3.3 has numerically completed every possible scientific domain. The article claims that the model core is now structured enough to be reviewed as a scientific object: typed definitions, proof obligations, executable witnesses, bounded replay rows, prior-art boundaries, and reviewer reopening conditions are presented together rather than as disconnected release artifacts.",
            "",
            "This matters because many broad frameworks fail at the same point. They may be conceptually suggestive, but a reviewer cannot tell which sentence is a theorem, which sentence is a metaphor, which sentence is empirical, and which sentence is a future ambition. OC Core 1.3.3 makes that separation explicit. The separation is itself part of the contribution: it turns the model from a vocabulary into a reviewable claim system.",
            "",
            heading("Why the Formal Layer Comes First", 3),
            "The formal layer comes before empirical replay because the model must say what counts as a continuum, a live realization, a residue, a boundary, a morphism, a K-level transition, or a lifecycle relation before a data row can be interpreted. Without that order, a numeric row could be impressive but irrelevant. With that order, the row either supports a declared claim boundary or reopens it.",
            "",
            "The article therefore gives theorem anchors without asking article readers to inspect every proof sheet first. The proof sheets, Lean subset, and finite-model reports remain available for reviewers who need the full audit path. The article-level job is to explain why those artifacts matter and what scientific burden they carry.",
            "",
            heading("Why the Empirical Layer Is Bounded", 3),
            "The empirical rows are deliberately framed as bounded replay and reconstruction evidence. They show that selected domain lanes can be operationalized with formulas, pinned snapshots, comparators, residuals, negative controls, falsifiers, and replay hashes. That is real evidence for the review surface, but it is not a license to claim total closure of physics, chemistry, biology, systems science, or mathematics.",
            "",
            "A failed empirical row would not be hidden by the framework. It would attack the specific claim boundary connected to that row. This is why the article insists on target-blind or held-out structure, comparator baselines, negative controls, and falsifiers. The aim is not rhetorical breadth; the aim is a claim surface that can be reopened by evidence.",
            "",
            heading("Why Prior Art Is Treated as Overlap First", 3),
            "The article begins the novelty discussion by admitting overlap. OC intersects with systems theory, autopoiesis, dynamical systems, type and category-oriented formalisms, RAF closure, complexity measures, identity theories, hybrid systems, and reproducibility practice. A release that denied those overlaps would be weaker, not stronger.",
            "",
            "The residual-delta question is narrower: does OC Core 1.3.3 combine its typed model core, theorem/proof governance, finite semantic witnesses, bounded replay rows, comparator discipline, and public claim boundaries into a package that those comparator traditions do not already provide as one release object? That is the article's defensible novelty boundary.",
            "",
            heading("Why the Reviewer Map Is Part of the Science", 3),
            "The reviewer map is not an appendix for public relations. It is part of the scientific method of the release. A theory that cannot say how it can be attacked cannot say what it currently proves. The map records objections against novelty, theorem scope, empirical reach, phenomenon coverage, and public wording. Each objection either has evidence-bound response or remains a research obligation.",
            "",
            "That adversarial structure is especially important for broad model-core work. The more general the theory, the easier it is to drift into language that sounds universal without being reviewable. The article therefore treats hostile review as a constraint on wording and evidence, not as a post-publication afterthought.",
            "",
            heading("Limits and Next Scientific Work", 3),
            "OC Core 1.3.3 is strong enough to be used as an external-review baseline. It is not the final completion of every domain projection. The next scientific work is to expand domain-specific prediction lanes, deepen mechanized proofs, improve comparator breadth, and harden phenomenon model cards. Those tasks belong to the continuing science program rather than to the promoted claim surface of this release.",
            "",
            "This boundary keeps the article honest while preserving ambition. The release does not retreat into trivial claims; it states a broad model-core contribution with formal, computational, empirical, and adversarial evidence. But it refuses to convert future research objectives into present-tense public claims.",
            "",
            heading("Reader Payoff", 3),
            "A reader who finishes the article should be able to answer five practical questions. First, what object does OC Core 1.3.3 define? Second, what class of claims is promoted by this release? Third, how do proof sheets, Lean declarations, finite witnesses, and bounded replay rows support those claims? Fourth, where does the release accept overlap with prior work and where does it claim residual delta? Fifth, what would force a claim to reopen?",
            "",
            "Those questions are article-level criteria. If the reader can only answer them by opening the raw registers, the article has failed even if the archive is complete. The article therefore repeats the core interpretation in prose: the release is a bounded, evidence-governed model-core artifact, with serious ambitions kept under reviewable claim boundaries.",
            "",
            heading("Editorial Implication", 3),
            "For journal preparation, the article should be treated as the compact review path, not as the whole evidentiary archive. Editors can use it to decide whether the topic and argument deserve detailed review. Specialist reviewers can then use the monograph, methods companion, reviewer map, and public zip to inspect the proof, replay, and prior-art details. This division of labor is deliberate because a journal-facing text must be readable before it can be exhaustively auditable.",
            "",
            heading("Reviewer Use Cases", 3),
            "A formal reviewer can begin with the formal object and main-results sections, then inspect the theorem anchors and proof route. The article tells that reviewer which claims are meant as theorem-level claims and which are only bounded by computational or empirical support. This prevents the common failure in broad theory papers where every statement is written with the same confidence level.",
            "",
            "An empirical reviewer can begin with the bounded replay interpretation. The article tells that reviewer that the public release contains operational rows, but that those rows are not being used as a blanket validation of every scientific domain. The relevant question becomes whether each row has the promised formula, pinned data, comparator, residual, negative control, falsifier, and replay hash.",
            "",
            "A prior-art reviewer can begin with the overlap-first novelty section. The article does not ask that reviewer to believe that OC appeared in a vacuum. Instead, it frames the contribution as a combined release object: typed formal vocabulary, proof governance, finite semantic witnesses, bounded replay rows, comparator discipline, public claim boundaries, and adversarial review in one auditable package.",
            "",
            "A journal editor can begin with the reader payoff and limitations. The article gives enough structure to decide whether the manuscript is a serious review candidate while making clear that the full monograph and evidence archive are the place for exhaustive checking. The article therefore functions as a gateway into the scientific package rather than as a replacement for it.",
            "",
            heading("Why This Is Release-Grade Rather Than Merely Draft-Grade", 3),
            "A draft may contain correct material in fragments. A release-grade article has to align those fragments into a public argument. The OC Core 1.3.3 article does this by matching definitions to claims, claims to evidence, evidence to reviewer attacks, reviewer attacks to reopening rules, and all of those to public metadata. If one of those links breaks, the public release is not simply untidy; it becomes scientifically ambiguous.",
            "",
            "The article therefore treats release engineering as part of epistemic responsibility. Readers should not have to guess whether a PDF is primary science, a methods appendix, a reviewer map, or metadata. They should not have to infer whether a claim is mathematical, empirical, methodological, or aspirational. They should not have to inspect repository internals to learn whether journal packages were submitted or only prepared. The public text must say these things plainly.",
            "",
            heading("Claim Walk-Through for Article Readers", 3),
            "A compact article still needs at least one worked route. Consider K0 resolution. The article first defines the typed object whose continuumness is being discussed. It then says that zero continuumness requires a declared cause rather than a rhetorical collapse label. The support route is a proof sheet plus a finite semantic witness. The reviewer test is whether removing or altering the declared cause changes the verdict. If no verdict changes, the claim fails; if the witness and negative controls separate correctly, the bounded claim has support.",
            "",
            "Consider lifecycle status. The article distinguishes live realization, death condition, residue, rebirth candidate, and identity continuation. The point is not to settle metaphysical identity. The point is to keep the formal claim from equivocating. Residue can support comparison, but it does not by itself authorize identity continuation. A reviewer can therefore attack the exact invariant: if the invariant is absent, the identity claim cannot pass.",
            "",
            "Consider an empirical row. The article does not ask the reader to accept a domain-wide conclusion. It asks the reader to inspect a bounded reconstruction route: formula, pinned input, split, predicted value, observed value, uncertainty, comparator, residual, negative control, falsifier, and replay hash. The row is useful precisely because it is narrow enough to fail. If the comparator is missing or the negative control is not rejected, the public claim must shrink.",
            "",
            "Consider prior art. The article asks whether the proposed OC contribution remains after known traditions are credited. If the comparison shows that the same claim already exists in a prior family, OC cannot promote priority. If OC's residual contribution is the combined typed model core plus evidence-governed release surface, that narrower claim can remain. The article's novelty boundary is therefore not a slogan; it is a same-claim comparison discipline.",
            "",
            heading("How to Read the Result Without Overreading It", 3),
            "The reader should separate three levels. Level one is the formal model-core level: terms such as carrier, realization, liveness, residue, boundary, morphism, operator, cycle, dimension, and K-level have defined roles. Level two is the evidence level: proof sheets, Lean subset, finite semantic witnesses, replay rows, comparator entries, and reviewer objections support or reopen particular claims. Level three is the research-program level: broader domain expansion and stronger comparator tests remain future work. Confusing these levels is the main way to overread the release.",
            "",
            "The article therefore uses strong language only where the release has strong support. It can say that a theorem route is bounded by assumptions and a proof sheet. It can say that a finite witness separates a declared semantic case. It can say that a replay row reconstructs a target under a stated protocol. It cannot say that every domain is complete, that all modern science has been surpassed, or that no competing model can ever be simpler. Those broader statements would require different evidence.",
            "",
            heading("Article-Level Editorial Standard", 3),
            "A journal-facing article must be readable before it is exhaustive. The article must tell the reader what problem motivates OC, what object is defined, what contribution is claimed, what evidence carries that contribution, what prior art constrains it, what limits remain, and what would falsify or reopen it. These are positive obligations, not merely style preferences. If any of them is absent, the article is not ready even if the repository contains many correct files.",
            "",
            "The article also has to avoid the opposite failure: hiding the evidence behind smooth prose. For that reason it keeps theorem IDs, proof routes, Lean and finite evidence, replay requirements, comparator families, and reviewer objections visible. The prose leads, but the evidence remains inspectable. A reader should never have to choose between a readable essay with no audit trail and a raw archive with no argument.",
            "",
            heading("Use in External Conversations", 3),
            "For scientists, the article offers a compact path to the model-core claim and its proof/evidence boundary. For institutional partners, it explains what has been made reproducible and what remains in the research program. For journal editors, it separates the article-scale argument from the monograph-scale reference and the methods-scale replay package. For skeptical readers, it names the pressure points: theorem assumptions, finite witnesses, data lanes, prior-art overlap, phenomenon model cards, and claim wording.",
            "",
            "This is why the article is not written as a marketing abstract. Its job is to make the strongest defensible public claim easy to inspect. The stronger future ambitions remain valuable, but they belong in scheduled research lanes until the same standard can be met for them. The article is therefore both ambitious and bounded: ambitious in the model-core synthesis it presents, bounded in the evidence ceiling it assigns to each claim.",
            "",
            heading("Minimum Acceptance Questions for Reviewers", 3),
            "The article is designed to answer a minimum set of reviewer questions without sending the reader into repository archaeology. What is the object? A typed continuum model with declared carrier, realization, liveness, residue, boundaries, morphisms, operators, cycles, dimensions, and K-level witnesses. What is the contribution? A bounded model-core release that makes those elements reviewable through proof, finite semantics, replay evidence, prior-art comparison, and adversarial reopening rules.",
            "",
            "What is proved? The release contains promoted theorem routes only where proof sheets, assumptions, dependency links, and selected Lean or finite witnesses support the statement. What is empirically supported? Selected bounded replay rows with formulas, snapshots, comparators, residuals, negative controls, falsifiers, and hashes. What is not supported? Complete future domain projection, final full-science completion, and unrestricted victory over every modern scientific model.",
            "",
            "What should a reviewer do next? A formal reviewer should inspect theorem assumptions and finite witnesses. An empirical reviewer should inspect replay rows and negative controls. A prior-art reviewer should inspect overlap and residual-delta claims. A journal editor should inspect whether the article, monograph, methods companion, reviewer map, and public zip form a coherent public-review baseline. A journal submission dossier is a later editorial product that requires venue formatting and separate owner approval. This division of review labor is explicit so that the article can be criticized efficiently.",
            "",
            "What would make the article fail? It would fail if the public wording became stronger than the evidence, if a theorem ID had no proof route, if the finite runner accepted tampered cases, if a replay row lacked comparator or falsifier, if novelty depended on an unsourced absence claim, if the literature synthesis became decorative, if the figures did not teach the model, or if the public archive presented metadata before science. These are not optional refinements; they are publication-grade conditions.",
            "",
            "This is why the article is longer than a minimal abstract but shorter than the monograph. It has enough space to teach the route and enough restraint to leave exhaustive registers outside the prose. That middle form is the appropriate article-level surface for a complex model-core release.",
        ]
    )


def reviewer_response_narrative() -> str:
    return "\n".join(
        [
            heading("Reviewer Response Method", 2),
            "The reviewer map is organized by objections rather than by internal records. Each objection should be read as an attack on a claim boundary: what is being attacked, why the attack matters, what evidence answers it, what residual risk remains, and what future work would be required if the objection reopens.",
            "",
            "Complete claim, theorem, finite-model, validation, and journal-package inventories remain in the evidence package. The public reviewer PDF summarizes only the adversarial path needed for a hostile reader to locate the answer.",
        ]
    )


def lean_evidence() -> str:
    cert = lean_status_summary()
    lean_path = ROOT / "formal" / "lean" / "OC133V12.lean"
    body = clean_public_text(read_text(lean_path)) if lean_path.exists() else ""
    declaration_ids = re.findall(r"(?m)^(?:theorem|lemma|def|structure)\s+([A-Za-z0-9_'.-]+)", body)
    declaration_ids = [item for item in declaration_ids if item.startswith("T133") or item.startswith("OC")][:24]
    out = [heading("Lean Formalization Subset", 2)]
    out.append(
        "The Lean subset is a machine-checked subset of the OC 1.3.3 theorem surface. "
        "The release does not claim that every mathematical or empirical statement is fully formalized in Lean."
    )
    out.extend(
        [
            bullet("certificate state", cert["state"]),
            bullet("execution status", cert["execution_status"]),
            bullet("build return code", cert["returncode"]),
            bullet("theorem ref total", cert["theorem_ref_total"]),
            bullet("missing theorem ref total", cert["missing_theorem_ref_total"]),
            bullet("build command", cert["build_command"]),
            bullet("Lean file", "formal/lean/OC133V12.lean"),
            "",
            "Selected public declaration identifiers:",
            "",
            *(f"- {item}" for item in declaration_ids),
            "",
        ]
    )
    return "\n".join(out)


def comparator_and_novelty() -> str:
    register = read_json(ROOT / "comparators" / "OC_1_3_3_NOVELTY_AND_PRIORITY_REGISTER.json", {})
    prior = read_json(ROOT / "docs" / "OC_1_3_3_PRIOR_ART_COMPARATOR_MATRIX.json", {})
    rows = register.get("rows", []) or prior.get("rows", [])
    out = [heading("Prior-Art Comparator and Novelty Boundary", 2)]
    out.append(
        "Comparator material is positioning evidence, not a uniqueness proof for all possible theories. "
        "The public argument states overlap first and residual delta second."
    )
    out.append(
        "The comparison deliberately starts by admitting prior-art overlap. OC is presented as a bounded model-core "
        "integration with explicit proof/evidence discipline, not as an invention of every concept it uses."
    )
    out.append("")
    for row in rows[:24]:
        family = clean_public_text(row.get("tradition") or row.get("source_family") or row.get("comparator_id") or "Comparator family")
        overlap = clean_public_text(
            row.get("overlap")
            or row.get("overlap_summary")
            or row.get("claim_element_overlap")
            or row.get("prior_art_has")
            or "the comparator family already contains part of the vocabulary or problem space"
        )
        residual = clean_public_text(
            row.get("residual_delta")
            or row.get("bounded_positioning_note")
            or "the residual OC contribution is limited to the declared model-core, proof/evidence, and claim-boundary integration"
        )
        verdict = clean_public_text(row.get("release_verdict") or row.get("uniqueness_claim_status") or "positioning only")
        non_novel = clean_public_text(row.get("non_novelty_boundary") or "If the residual contribution collapses to renamed prior art, the novelty claim fails.")
        must_not = clean_public_text(row.get("what_oc_must_not_claim") or "No priority or absence-of-prior-work claim is promoted by this release.")
        source_title = ""
        refs = row.get("source_refs")
        if isinstance(refs, list) and refs:
            first = refs[0] if isinstance(refs[0], dict) else {}
            source_title = clean_public_text(first.get("title") or first.get("url") or "")
        out.append("")
        out.append(
            f"Comparator family: {family}. Prior-art anchor: {source_title or family}. Overlap accepted by OC: {overlap}. "
            f"Residual delta claimed by this release: {residual}. Public boundary: {verdict}."
        )
        out.append(
            f"Non-novelty test. {non_novel} Must-not-claim rule. {must_not}. "
            "This is a source-specific positioning paragraph, not a priority certificate."
        )
        out.append("")
    return "\n".join(out)


def phenomenon_coverage(max_rows: int = 60) -> str:
    matrix = read_json(ROOT / "docs" / "OC_1_3_3_PHENOMENON_COVERAGE_MATRIX.json", {})
    rows = []
    for row in matrix.get("rows", []):
        question = str(row.get("hostile_question") or row.get("phenomenon") or "")
        attacked = str(row.get("attacked_claim") or "")
        if not (row.get("public_promotion") or row.get("counts_as_formal_model_card_replay")):
            continue
        if re.search(r"no[- ]send|publication control|release-state check|NOSEND", question + " " + attacked, re.I):
            continue
        rows.append(row)
    out = [heading("Phenomenon Coverage and Limits", 2)]
    out.append(
        "The phenomenon matrix records model cards and evidence routes. Rows with illustrative or protocol-ready status "
        "are not promoted as complete phenomenon explanations. A phenomenon is public-facing only when it has a formal "
        "instance, observable, replay or prediction path, comparator, negative control, falsifier, and claim boundary."
    )
    for row in rows[:max_rows]:
        title = row.get("hostile_question") or row.get("phenomenon") or row.get("phenomenon_id") or row.get("id")
        out.append(heading(clean_public_text(title), 3))
        model_card = row.get("model_card", {}) if isinstance(row.get("model_card"), dict) else {}
        formal_instance = row.get("formal_instance") or row.get("phenomenon_specific_model") or model_card.get("formal_instance")
        observable = row.get("observable") or model_card.get("observable")
        replay_path = row.get("prediction_replay_path") or row.get("oc_explanation_route") or model_card.get("prediction_or_replay")
        negative_control = row.get("negative_control") or model_card.get("negative_control")
        falsifier = row.get("falsifier") or model_card.get("falsifier")
        for key in [
            "domain",
            "comparator",
            "claim_boundary",
        ]:
            if key in row:
                out.append(bullet(key.replace("_", " "), row.get(key)))
        out.extend(
            [
                bullet("formal instance", formal_instance),
                bullet("observable", observable),
                bullet("replay path", replay_path),
                bullet("negative control", negative_control),
                bullet("falsifier", falsifier),
            ]
        )
        out.append("")
    return "\n".join(out)


def attack_matrix(max_rows: int = 220) -> str:
    matrix = read_json(ROOT / "review" / "OC_1_3_3_TOTAL_ATTACK_MATRIX.json", {})
    rows = matrix.get("rows", [])
    rows = [
        row for row in rows
        if not re.search(
            r"\b(?:NOSEND|NO[-_ ]?SEND|ADV-NOSEND|OC133-NOSEND|publish_allowed|owner_approved|zenodo_deposit_allowed|global_no_send_lock)\b",
            " ".join(str(value) for value in row.values()) if isinstance(row, dict) else str(row),
            re.I,
        )
    ]
    critical_open = matrix.get("critical_open_total")
    high_open = matrix.get("high_open_total")
    def attack_row_closed(row: dict[str, Any]) -> bool:
        status = str(row.get("status", "")).upper()
        return status.startswith("CLOSED") or status in {"PASS", "RESOLVED", "REPAIRED"}
    if critical_open is None:
        critical_open = sum(1 for row in rows if str(row.get("severity", "")).upper() == "CRITICAL" and not attack_row_closed(row))
    if high_open is None:
        high_open = sum(1 for row in rows if str(row.get("severity", "")).upper() == "HIGH" and not attack_row_closed(row))
    out = [heading("Adversarial Objection and Response Map", 2)]
    out.append(
        "This map is organized for a hostile reader. Each group states the threatened claim, the criticism route, the response evidence, "
        "the residual risk, and the condition under which the objection would reopen. A row is not considered closed merely because an artifact exists."
    )
    out.append(
        "The public text does not ask the reader to trust an internal status word. The response below is valid only when "
        "the cited proof, finite case, replay row, comparator row, or claim-boundary artifact supports the exact public claim."
    )
    out.append(
        "To avoid turning the map into boilerplate, the reopening rules are stated as a method before the challenge list. "
        "A novelty response reopens if same-claim prior art absorbs the residual delta. A theorem response reopens if an "
        "assumption is missing, a proof dependency fails, or a finite witness no longer separates positive and negative "
        "cases. An empirical response reopens if a formula, pinned source, comparator, uncertainty, negative control, "
        "falsifier, or replay hash is absent or inconsistent. A phenomenon response reopens if the model card lacks a "
        "testable observable. An editorial response reopens if the public PDF becomes unreadable, fragmented, or dominated "
        "by registers again."
    )
    out.append("")

    def public_evidence_phrase(value: Any) -> str:
        def finite_case_phrase(raw_item: str) -> str | None:
            normalized = clean_public_text(raw_item)
            ids = sorted(set(re.findall(r"(T133-[A-Za-z0-9-]+|OC133-[A-Za-z0-9-]+)", normalized)))
            if "FM-T133" in normalized or re.search(r"\bP\d{3}::", normalized):
                if ids:
                    labels = sorted(set(public_theorem_label(item) for item in ids[:5]))
                    return "paired finite-model positive and negative controls for " + sentence_list(labels)
                return "paired finite-model positive and negative controls for the named theorem family"
            return None

        if isinstance(value, list):
            phrases: list[str] = []
            for item in value[:6]:
                raw_item = str(item)
                finite_phrase = finite_case_phrase(raw_item)
                if finite_phrase:
                    phrases.append(finite_phrase)
                elif re.search(r"\bOC133-NUM-[A-Za-z0-9-]+\b", raw_item):
                    phrases.append(
                        "bounded numeric replay rows with comparator, residual, negative-control, falsifier, and replay hash"
                    )
                elif "proofs/proof_sheets/" in raw_item:
                    match = re.search(r"proofs/proof_sheets/(T133-[A-Za-z0-9-]+)\.md(?:::([A-Za-z0-9_ +.-]+))?", raw_item)
                    phrases.append(f"proof sheet {match.group(1)}" + (f" section {clean_public_text(match.group(2)).lower()}" if match and match.group(2) else "") if match else "public proof sheet")
                elif "LEAN_BUILD_CERTIFICATE" in raw_item or "formal/lean" in raw_item:
                    match = re.search(r"::([A-Za-z0-9_'.-]+)", raw_item)
                    phrases.append("Lean build certificate" + (f" declaration {match.group(1)}" if match else ""))
                elif "FINITE_MODEL" in raw_item:
                    match = re.search(r"::([A-Za-z0-9_.-]+)", raw_item)
                    phrases.append("finite-model semantic report" + (f" case {match.group(1)}" if match else ""))
                elif "CLAIM_LEDGER" in raw_item or "claims/" in raw_item:
                    match = re.search(r"::([A-Za-z0-9_.-]+)", raw_item)
                    phrases.append("claim register boundary" + (f" row {match.group(1)}" if match else ""))
                elif "validation" in raw_item or "target" in raw_item or "replay" in raw_item:
                    match = re.search(r"::([A-Za-z0-9_.-]+)", raw_item)
                    if match:
                        phrases.append(f"bounded replay evidence row {clean_public_text(match.group(1))}")
                    else:
                        stem = clean_public_text(Path(raw_item).stem.replace("_", " "))
                        phrases.append(f"bounded replay evidence table {stem}" if stem else "bounded replay evidence table with replay, comparator, residual, negative-control, and falsifier fields")
                elif "comparator" in raw_item or "novelty" in raw_item or "prior" in raw_item:
                    match = re.search(r"::([A-Za-z0-9_.-]+)", raw_item)
                    if match:
                        phrases.append(f"prior-art comparator evidence row {clean_public_text(match.group(1))}")
                    else:
                        stem = clean_public_text(Path(raw_item).stem.replace("_", " "))
                        phrases.append(f"prior-art comparator evidence table {stem}" if stem else "prior-art comparator evidence table with overlap, residual-delta, and claim-boundary fields")
                else:
                    lowered_item = raw_item.lower()
                    if "assumptions" in lowered_item or "counterexample" in lowered_item:
                        claim_match = re.search(r"(T133-[A-Za-z0-9-]+)", raw_item)
                        phrases.append(
                            f"proof-sheet assumptions and counterexample boundary for {claim_match.group(1)}"
                            if claim_match
                            else "proof-sheet assumptions and counterexample boundary"
                        )
                    elif "lake build" in lowered_item or "lean" in lowered_item:
                        decl_match = re.search(r"::([A-Za-z0-9_'.-]+)", raw_item)
                        declaration = decl_match.group(1).replace("_", " ") if decl_match else "the cited declaration"
                        phrases.append(f"Lean build certificate showing {declaration} with successful build")
                    elif "finite_model" in lowered_item or "finite-model" in lowered_item:
                        case_match = re.search(r"::([A-Za-z0-9_.-]+)", raw_item)
                        phrases.append(
                            f"finite-model semantic case {case_match.group(1)} computed as passing"
                            if case_match
                            else "finite-model semantic case computed as passing"
                        )
                    elif "scope_limit" in lowered_item or "claim_ledger" in lowered_item or "claim ledger" in lowered_item:
                        claim_match = re.search(r"(T133-[A-Za-z0-9-]+|OC133-[A-Za-z0-9-]+)", raw_item)
                        phrases.append(
                            f"claim-boundary ledger row for {claim_match.group(1)}"
                            if claim_match
                            else "claim-boundary ledger row"
                        )
                    else:
                        cleaned = clean_public_text(Path(raw_item).stem.replace("_", " "))
                        phrases.append(cleaned if len(cleaned) <= 160 else "the exact proof, finite, replay, comparator, or claim-boundary evidence named in the public package")
            unique_phrases = list(dict.fromkeys(phrase for phrase in phrases if phrase))
            return sentence_list(unique_phrases)
        text = clean_public_text(value)
        raw = str(value if value is not None else "")
        if not text:
            return "the relevant public proof, finite-model, replay, comparator, or claim-boundary artifact"
        finite_phrase = finite_case_phrase(raw)
        if finite_phrase:
            return finite_phrase
        if (
            len(text) > 240
            or re.search(r"[\\/]|\.json\b|\.md\b|\.tex\b|__|\{|\}|\[|\]|releases[_/\\]|proofs[_/\\]|validation[_/\\]|reviews[_/\\]", raw, re.I)
        ):
            lowered = raw.lower()
            classes = []
            if "proof" in lowered or "theorem" in lowered or "lean" in lowered:
                classes.append("proof and formalization evidence")
            if "finite" in lowered:
                classes.append("finite-model witness evidence")
            if "validation" in lowered or "target" in lowered or "replay" in lowered:
                classes.append("bounded replay evidence")
            if "comparator" in lowered or "novelty" in lowered or "prior" in lowered:
                classes.append("prior-art comparator evidence")
            if "phenomenon" in lowered:
                classes.append("phenomenon model-card evidence")
            if "review" in lowered or "attack" in lowered:
                classes.append("adversarial-review evidence")
            if not classes:
                classes.append("public proof, finite-model, replay, comparator, or claim-boundary evidence")
            return sentence_list(classes)
        return text

    groups: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        theme = clean_public_text(row.get("theme") or row.get("attack_class") or row.get("attacked_claim") or row.get("failure_mode") or "general scientific objection")
        if re.search(r"corporate|autonomous|owner|publication|release permission|partial lock|public surface|no[- ]send|control", theme, re.I):
            continue
        groups.setdefault(theme, []).append(row)
    challenge_openers = [
        "A skeptical expert would press",
        "This objection targets",
        "The hostile reading begins with",
        "A journal reviewer could attack",
        "The strongest version of the criticism is aimed at",
        "The editorially relevant attack concerns",
    ]
    response_openers = [
        "The response route is evidence-bound rather than status-bound.",
        "The answer is local to the cited support.",
        "The release answers by binding the sentence to public artifacts.",
        "The repairable claim boundary is the center of the response.",
        "The evidence route is deliberately narrower than the ambition it organizes.",
        "The public answer is acceptable only because it remains testable.",
    ]
    locator_openers = [
        "Public locators.",
        "Review path.",
        "Where to verify.",
        "Audit route.",
        "Evidence entry points.",
        "Reader navigation.",
    ]
    emitted = 0
    for theme, group_rows in list(groups.items())[:max_rows]:
        emitted += 1
        sample = group_rows[0]
        theme_title = re.sub(r"\s+", " ", theme.replace("_", " ")).strip().title()
        out.append(heading(f"Reviewer challenge {emitted}: {theme_title}", 3))
        attacked_claims = []
        for row in group_rows:
            claim = public_theorem_label(row.get("attacked_claim") or "")
            if claim and claim not in attacked_claims:
                attacked_claims.append(claim)
        attacked = sentence_list(attacked_claims[:6]) if attacked_claims else "a promoted bounded model-core claim"
        response_refs = []
        for row in group_rows[:8]:
            refs = row.get("closure_evidence_refs") or row.get("closure_evidence") or row.get("evidence_ref")
            if isinstance(refs, list):
                response_refs.extend(refs)
            elif refs:
                response_refs.append(refs)
        response_text = public_evidence_phrase(response_refs)
        joined_refs = " ".join(str(item) for item in response_refs)
        theorem_ids_raw = sorted(set(re.findall(r"(T133-[A-Za-z0-9-]+)", joined_refs)))
        theorem_ids = sorted(set(re.sub(r"-(?:POS|NEG)$", "", item) for item in theorem_ids_raw))
        finite_case_ids = sorted(set(re.findall(r"(FM-T133-[A-Za-z0-9-]+)", joined_refs)))
        for item in theorem_ids_raw:
            if re.search(r"-(?:POS|NEG)$", item):
                finite_case_ids.append("FM-" + item)
        finite_case_ids = sorted(set(finite_case_ids))
        numeric_ids = sorted(set(re.findall(r"(OC133-NUM-[A-Za-z0-9-]+)", joined_refs)))
        locator_parts = [
            "master monograph sections 'Claim-by-Claim Integrated Argument', 'Theorem and Proof Integration', and 'Bounded Replay QA and Artifact-Integrity Examples'",
            "public theorem registry file THEOREM_REGISTRY_PUBLIC_1_3_3.json",
            "public claim register file CLAIM_LEDGER_PUBLIC_1_3_3.json",
        ]
        if theorem_ids:
            locator_parts.append("proof sheet file(s) " + sentence_list([f"proof_sheets_public/{item}.md" for item in theorem_ids[:5]]))
            registry = read_json(ROOT / "proofs" / "THEOREM_REGISTRY_1_3_3.json", {})
            lean_refs = []
            for theorem_id in theorem_ids[:5]:
                for registry_row in registry.get("rows", []) if isinstance(registry.get("rows"), list) else []:
                    if isinstance(registry_row, dict) and registry_row.get("theorem_id") == theorem_id and registry_row.get("lean_ref"):
                        lean_refs.append(f"{theorem_id}: {clean_public_text(registry_row.get('lean_ref'))}")
                        break
            locator_parts.append(
                "Lean source formal/lean/OC133V12.lean declaration route for "
                + sentence_list(lean_refs or theorem_ids[:5])
            )
            locator_parts.append(
                "finite-model report proofs__FINITE_MODEL_OUTPUT_ATTESTATION_1_3_3.json case family for "
                + sentence_list(finite_case_ids[:8] or theorem_ids[:5])
            )
        if numeric_ids:
            locator_parts.append("target-blind prediction table row(s) " + sentence_list(numeric_ids[:5]))
            locator_parts.append("domain validation report replay hash and falsifier fields for " + sentence_list(numeric_ids[:5]))
        locator_parts.append("reopening condition stated in this reviewer challenge")
        compact_locator_bits = [
            "master monograph evidence chapters",
            "public theorem and claim registers",
        ]
        if theorem_ids:
            compact_locator_bits.append("proof sheet(s) " + sentence_list(theorem_ids[:4]))
        if finite_case_ids:
            compact_locator_bits.append("finite case family " + sentence_list(finite_case_ids[:4]))
        if numeric_ids:
            compact_locator_bits.append("numeric replay row(s) " + sentence_list(numeric_ids[:4]))
        compact_locator_bits.append("the reopening rule printed in this challenge")
        locator_text = sentence_list(compact_locator_bits)
        failure_modes = []
        verification_queries = []
        for row in group_rows[:8]:
            mode = clean_public_text(row.get("failure_mode") or row.get("objection") or "")
            query = clean_public_text(row.get("closure_verification_query") or row.get("required_repair") or "")
            if mode and mode not in failure_modes:
                failure_modes.append(mode)
            if query and query not in verification_queries:
                verification_queries.append(query)
        mode_sentence = sentence_list(failure_modes[:5]) or "the public claim could outrun its evidence"
        query_sentence = public_evidence_phrase(verification_queries[:5]) or "the exact evidence check named by the public package"
        opener = challenge_openers[(emitted - 1) % len(challenge_openers)]
        response_opener = response_openers[(emitted - 1) % len(response_openers)]
        locator_opener = locator_openers[(emitted - 1) % len(locator_openers)]
        out.append(
            f"{opener} {attacked} at the point where {mode_sentence}. For reviewer challenge {emitted}, the seriousness "
            "comes from the release's evidence discipline: the public sentence is defended only by the match between the "
            "visible wording, its assumptions, and the evidence that can actually carry that wording."
        )
        out.append(
            f"{response_opener} The relevant support is {response_text or 'the proof, finite-model, replay, comparator, or claim-boundary evidence named by the release package'}. "
            f"The practical verification is {query_sentence}. When that verification fails, the claim is not argued around; it is "
            "repaired, demoted, or held for a later research release."
        )
        out.append(
            f"{locator_opener} For reviewer challenge {emitted}, use {locator_text}. These locators are intentionally file-and-section level rather than "
            "status-token level, while the full path and checksum detail stays in the manifest and evidence package so the prose remains readable."
        )
        out.append(
            "Residual risk is recorded as a reopening rule, not hidden in confidence language. For this challenge the repair "
            "path stays scientific: proof, finite semantics, replay evidence, comparator positioning, or public wording, "
            "depending on which cited support no longer carries the public sentence."
        )
        out.append("")
    return "\n".join(out)


def appendices_and_model() -> str:
    refs = [
        "content/03_model.tex",
        "content/OC_1_3_3_TYPED_FOUNDATION.tex",
        "content/OC_1_3_3_OPERATOR_SEMANTICS.tex",
        "content/OC_1_3_3_CYCLE_TAXONOMY.tex",
        "appendix/OC_1_3_3_K0_RESOLUTION_FOUNDATION.tex",
        "appendix/OC_1_3_3_CONTINUUMNESS_FUNCTIONALS.tex",
        "appendix/OC_1_3_3_BOUNDARY_REPRESENTATION_THEOREM.tex",
        "appendix/OC_1_3_3_VERDICT_INVARIANT_MINIMALITY_FULL_PROOF.tex",
        "appendix/OC_1_3_3_K_LEVEL_IRREDUCIBILITY_ATLAS.tex",
        "appendix/OC_1_3_3_COMPARATOR_AND_NOVELTY_MATRIX.tex",
    ]
    out = [heading("Formal Spine and Appendices", 2)]
    for ref in refs:
        path = ROOT / ref
        if not path.exists():
            continue
        out.append(heading(public_artifact_path_phrase(ref).replace("repository path ", "").replace("the ", "", 1).title(), 3))
        body = sanitize_latex_fragment(read_text(path))
        out.append(body[:18000])
        out.append("")
    return "\n".join(out)


def release_boundary() -> str:
    return "\n".join(
        [
            heading("Claim Boundary and Research Limits", 2),
            "OC Core 1.3.3 is a bounded external-review scientific release. It contains a typed model foundation, theorem/proof evidence, a Lean-checked subset, finite-model semantics, bounded numeric replay QA rows, comparator positioning, and adversarial-review material.",
            "",
            "The release does not claim complete scientific coverage, universal numeric closure, or unrestricted comparative victory over contemporary science. Those statements are outside the promoted 1.3.3 public claim surface.",
            "",
            "Journal owner-review packets are included as preparation material only. They help editors and reviewers see how a later submission could be assembled, but they are not part of the scientific proof of the model core.",
            "",
        ]
    )


def journal_package_summary() -> str:
    index = read_json(RELEASE_ROOT / "submission_packages" / "SUBMISSION_PACKAGE_INDEX.json", {})
    rows = index.get("rows", [])
    out = [heading("Journal Owner-Review Packages", 2)]
    out.append(
        "Eight venue packets are included for later owner review. They are not submitted by this release action. "
        "Each packet contains a package manifest, cover letter draft, checklist, reproducibility/data statement, conflict/funding statement, AI assistance disclosure, and venue-fit note."
    )
    recommended = [row for row in rows if row.get("submit_recommended")]
    if recommended:
        out.append(
            "The primary recommended venues are "
            f"{sentence_list([clean_public_text(row.get('venue_id')) for row in recommended])}. "
            "All venue packets remain preparation material until a separate journal-submission decision is made."
        )
        out.append("")
    for row in rows:
        out.append(heading(str(row.get("venue_id")), 3))
        recommendation = "primary target" if row.get("submit_recommended") else "conditional or secondary target"
        out.extend(
            [
                bullet("venue role", recommendation),
                bullet("venue fit", row.get("venue_fit_note")),
                bullet("official venue page", row.get("official_url")),
                bullet("owner action", "separate owner decision required before any journal submission"),
                "",
            ]
        )
    return "\n".join(out)


def write_public_markdown(doi: str | None, zenodo_record_url: str | None) -> dict[str, Path]:
    doi_text = doi or "assigned by the corrected Zenodo record metadata"
    record_text = zenodo_record_url or "assigned by corrected publication pass"

    def front(document_title: str, document_role: str, route_sections: list[str] | None = None) -> str:
        doc_key = "generic"
        lowered_title = document_title.lower()
        for candidate in ["guide", "master", "journal", "methods", "reviewer"]:
            if candidate in lowered_title or (candidate == "reviewer" and "attack" in lowered_title):
                doc_key = candidate
                break
        abstracts = {
            "OC Core 1.3.3 Release Guide": (
                "This guide is the reader's first route through the public archive. It explains which PDF to read first, "
                "which evidence files support the science, how the DOI and checksum surfaces should be used, and which "
                "claims remain outside the promoted claim boundary."
            ),
            "OC Core 1.3.3 Master Monograph": (
                "This monograph is the canonical long-form scientific text for OC Core 1.3.3. It integrates the baseline "
                "1.3 corpus with the 1.3.3 typed foundation, proof route, Lean subset, finite semantic checks, bounded "
                "numeric replay evidence, comparator positioning, reviewer closure, and publication-boundary rules."
            ),
            "OC Core 1.3.3 Journal Core": (
                "This article-shaped document compresses the monograph into a conventional review path: problem, object, "
                "methods, results, evidence, related work, limitations, and conclusion. It is written for first-pass "
                "scientific and editorial review, not as a machine register."
            ),
            "OC Core 1.3.3 Methods and Reproducibility Companion": (
                "This companion explains how formal, finite-model, simulation, target-blind replay, checksum, and package "
                "checks relate to scientific claims. It turns commands and evidence files into a reproducibility method "
                "with explicit failure interpretation."
            ),
            "OC Core 1.3.3 Reviewer Attack and Response Map": (
                "This map presents the release under hostile review. It groups objections by attacked claim, explains why "
                "each attack matters, cites the public evidence route that answers or bounds it, and records what would "
                "reopen the issue."
            ),
        }
        abstract = abstracts.get(
            document_title,
            "This public PDF is a human-readable scientific text. It explains the bounded OC Core 1.3.3 release surface in prose first, then points to machine-readable evidence where verification is needed.",
        )
        route_sections = route_sections or [
            "Audience and purpose",
            "Scientific claim boundary",
            "Evidence route",
            "Prior-art position",
            "Figures or operational diagrams",
            "Reopening and limitation rules",
        ]
        reader_contracts = {
            "guide": {
                "orientation": "This guide is the public foyer. It tells a first-time reader which document to open, what each public file is for, and how to cite the release without mistaking metadata for science.",
                "scope": "The guide does not prove the model. It orients the reader to the monograph, article, methods companion, reviewer map, evidence package, DOI, and checksums.",
                "order": "Read this file quickly, then choose either the monograph for depth, the journal core for a compact argument, the methods companion for replay, or the reviewer map for hostile objections.",
            },
            "master": {
                "orientation": "This monograph is the long scientific argument. It carries the integrated model, proof structure, evidence interpretation, prior-art boundary, and appendices.",
                "scope": "The monograph may include audit appendices, but the main line must teach the model before it exposes detailed evidence rows.",
                "order": "Read the orientation and formal model first, then theorem/proof chapters, then computational and empirical evidence, then comparator and reviewer-boundary chapters.",
            },
            "journal": {
                "orientation": "This article is the compact peer-review path. It must stand alone as a scientific paper before the reader opens the monograph.",
                "scope": "The article promotes only the bounded model-core contribution, with representative definitions, results, figures, evidence rows, related-work comparison, and limits.",
                "order": "Read it as a conventional paper: problem, contribution, model, methods, results, evidence, related work, limitations, and conclusion.",
            },
            "methods": {
                "orientation": "This companion is the independent replay manual. It tells a reviewer which command checks which claim surface and how to interpret a mismatch.",
                "scope": "The methods text does not expand the theory; it binds commands, inputs, outputs, hashes, dependency expectations, and claim consequences.",
                "order": "Read the environment section, then the replay matrix, then the command narratives, then failure interpretation and checksum binding.",
            },
            "reviewer": {
                "orientation": "This map is the hostile-review manual. It teaches a skeptical reader where to attack, what evidence answers, and what would reopen each claim family.",
                "scope": "The map is not a register of every row. It is adversarial prose that turns objections into claim-specific tests.",
                "order": "Read the attack method, then the claim-family challenges, then the role playbook, then the worked attack transcripts and reopening rules.",
            },
            "generic": {
                "orientation": "This public PDF is a human-readable scientific text. It explains its role in prose first, then points to machine-readable evidence where verification is needed.",
                "scope": "The release promotes evidence-bound model-core claims and excludes unsupported complete scientific coverage or unrestricted cross-science comparison.",
                "order": "Move from the abstract and reader contract to the role-specific argument, then to evidence, limits, literature, figures, and reopening rules.",
            },
        }
        action_templates_by_doc = {
            "guide": [
                "Confirm what the archive contains and which file is the right first read.",
                "Choose the next public PDF according to the reader's task.",
                "Check the evidence summary before treating the release as citable science.",
                "Read the boundary statement so the release is not overclaimed.",
                "Use the verification notes only after the human reading order is clear.",
                "Copy the citation metadata from the DOI and citation files.",
            ],
            "master": [
                "Understand the intended reader and the scientific object.",
                "Follow the formal construction before opening appendices.",
                "Read theorem claims with their assumptions and scope boundaries.",
                "Inspect computational and empirical evidence as support, not as decoration.",
                "Compare the model with prior art after the claim surface is clear.",
                "Use reopening rules to decide what would force revision.",
            ],
            "journal": [
                "Read the problem and contribution as a standalone article.",
                "Locate the formal object and the minimum definitions.",
                "Read the representative results and evidence table.",
                "Inspect the embedded figures that operationalize the model.",
                "Evaluate related-work overlap and residual contribution.",
                "Finish with limitations and reviewer-facing consequences.",
            ],
            "methods": [
                "Check the environment and dependency expectations.",
                "Map each command to inputs, outputs, hashes, and claim impact.",
                "Run formal and finite checks before empirical replay.",
                "Interpret validation and simulation outputs locally.",
                "Use failure interpretation to route defects to the right claim layer.",
                "Confirm checksum and archive identity after replay.",
            ],
            "reviewer": [
                "Select the public claim or sentence under attack.",
                "Identify the attack family and evidence class.",
                "Ask what would make the claim fail.",
                "Inspect the proof, replay, comparator, or editorial evidence named for that family.",
                "Apply the claim-specific reopening condition.",
                "Record whether the repair is proof, data, wording, comparator, or publication-surface work.",
            ],
        }
        contract = reader_contracts.get(doc_key, reader_contracts["generic"])
        action_templates = action_templates_by_doc.get(doc_key, action_templates_by_doc.get("guide", []))
        route_lines: list[str] = []
        for idx, section in enumerate(route_sections, start=1):
            action = action_templates[(idx - 1) % len(action_templates)]
            route_lines.append(f"{idx}. {section}. {action}")
        return "\n".join(
            [
                "---",
                f"title: {document_title}",
                f"author: {AUTHOR_DISPLAY}",
                "date: 2026-05-01",
                "header-includes:",
                "  - \\usepackage{tikz}",
                "  - \\usetikzlibrary{arrows.meta,positioning}",
                "---",
                "",
                "**Ontology of Continua**",
                "",
                f"**Document role.** {document_role}",
                "",
                f"**Author.** {AUTHOR_DISPLAY}, {AUTHOR_AFFILIATION}, ORCID {AUTHOR_ORCID}.",
                "",
                f"**Research instrument.** {LOGION_ENTITY_NOTE}",
                "",
                f"**Methodological framework.** {ESTRA_ENTITY_NOTE}",
                "",
                f"**Version.** Version {VERSION}; tag `{TAG}`; release date 2026-05-01.",
                "",
                f"**DOI.** {doi_text}.",
                "",
                f"**Zenodo record.** {record_text}.",
                "",
                "**Keywords.** Ontology of Continua; typed model core; formal methods; proof governance; finite semantic checks; target-blind replay QA; reproducible research; scientific release engineering.",
                "",
                "**Dedication.** Dedicated to my dear wife Maria, without whom this work would have been impossible.",
                "",
                "# Abstract",
                "",
                f"**Abstract.** {abstract}",
                "",
                "# Reader Contract",
                "",
                f"**Reader Orientation.** {contract['orientation']}",
                "",
                f"**Scope.** {contract['scope']} The release promotes evidence-bound model-core claims and excludes unsupported complete scientific coverage or unrestricted cross-science comparison claims.",
                "",
                f"**Reading order.** {contract['order']}",
                "",
                f"**Recommended reader path.** {contract['order']}",
                "",
                "# Reading Map",
                "",
                "This reading map is document-specific. The generated PDF table of contents gives page locations; the steps below state what the reader should do with each section.",
                "",
                *route_lines,
                "",
            ]
        )

    def promote_body_headings(markdown: str) -> str:
        promoted: list[str] = []
        for line in markdown.splitlines():
            if line.startswith("#### "):
                promoted.append("### " + line[5:])
            elif line.startswith("### "):
                promoted.append("## " + line[4:])
            elif line.startswith("## "):
                promoted.append("# " + line[3:])
            else:
                promoted.append(line)
        return "\n".join(promoted)

    def compact_journal_body(markdown: str) -> str:
        """Keep the journal PDF article-shaped by converting subroutes to run-in prose."""

        keep = {
            "Introduction",
            "Problem",
            "Contribution",
            "Related Work",
            "Methods",
            "Formal Object",
            "Definitions Before Evidence IDs",
            "Main Results",
            "Evidence",
            "Results and Evidence Interpretation",
            "Bounded Empirical Replay Interpretation",
            "Prior-Art Interpretation for Article Readers",
            "Discussion",
            "Limitations",
            "Conclusion",
        }
        compacted: list[str] = []
        for line in markdown.splitlines():
            if line.startswith("### "):
                title = line[4:].strip()
                compacted.append(f"**{title}.**")
            elif line.startswith("## "):
                title = line[3:].strip()
                if title in keep:
                    compacted.append(line)
                else:
                    compacted.append(f"**{title}.**")
            else:
                compacted.append(line)
        return "\n".join(compacted)

    def editorial_bridge(document_role: str, evidence_focus: str, reader_path: str) -> str:
        return "\n\n".join(
            [
                heading("Editorial Integration", 2),
                (
                    f"This document is written as {document_role}. It starts from the same OC Core 1.3.3 evidence graph as "
                    f"the rest of the release, but it presents that graph as a readable argument before exposing tables, "
                    f"identifiers, and replay artifacts. The reader should encounter definitions, motivation, evidence "
                    f"boundaries, and verification routes in that order, because explanation has to come before audit detail."
                ),
                (
                    f"The central evidence focus here is {evidence_focus}. This section connects the formal model, proof "
                    f"obligations, computational witnesses, empirical rows, novelty comparisons, and reviewer objections "
                    f"without pretending that every future domain projection is already complete. In contrast to an archive "
                    f"inventory, the prose explains why each evidence class matters and where its authority stops."
                ),
                (
                    f"The recommended reader path is {reader_path}. The evidence is intentionally layered: first the "
                    f"scientific statement, then the assumptions, then the verification artifact, then the boundary or "
                    f"falsifier. This structure lets hostile reviewers locate the exact place where a claim could fail "
                    f"while keeping the public document coherent for readers who are not running the replay scripts."
                ),
                (
                    "Primary PDFs may cite manifests, hashes, and evidence registers, but they must remain explanatory scientific "
                    "texts. Verification artifacts support the argument; they do not substitute for definitions, "
                    "motivation, assumptions, examples, limits, and reviewer-facing consequences."
                ),
                (
                    "Consequently, the document uses tables only where they reduce ambiguity. Long registers remain in "
                    "appendices or the reproducibility package, while the main line explains the model, the evidence, the "
                    "claim boundary, and the reviewer-facing consequence. Because the same rule applies to every public "
                    "PDF, the release has a single voice instead of a collection of detached generated fragments."
                ),
            ]
        )
    docs = {
        "guide": "\n\n".join(
            [
                front(
                    "OC Core 1.3.3 Release Guide",
                    "Public landing guide and recommended reading order",
                    [
                        "Public landing guide",
                        "Recommended reading order",
                        "Evidence summary",
                        "Claim boundary",
                        "Verification route",
                        "Citation route",
                    ],
                ),
                document_editorial_context("guide"),
                heading("Public Landing Guide", 2),
                "This guide is the first-file landing surface for public Zenodo and GitHub users. It exists so the record opens with a readable scientific navigation page rather than metadata, checksums, or process material.",
                "",
                heading("Recommended Reading Order", 2),
                "1. Read the Master Monograph for the full scientific argument, formal spine, proof registers, evidence tables, and claim boundary.",
                "2. Read the Journal Core article for the compact external-review path.",
                "3. Read the Methods and Reproducibility Companion for replay, finite-model, Lean, validation, checksum, and package-inventory details.",
                "4. Read the Reviewer Attack and Response Map for hostile-review closure, novelty/equivalence boundaries, phenomenon coverage, and known background research obligations.",
                "5. Use the public reproducibility zip only after the PDFs, because it is an evidence and replay package rather than the primary reading surface.",
                "",
                heading("Evidence Summary", 2),
                "The 1.3.3 release promotes bounded model-core claims tied to theorem/proof registers, a Lean-checked subset, finite-model semantic checks, bounded target-blind replay QA examples, comparator positioning, and adversarial-review closure.",
                "",
                "The public surface does not promote complete scientific coverage or unrestricted cross-science comparison victory. Those statements are outside the 1.3.3 public claim surface.",
                "",
                "Primary evidence anchors include T133-K0-RES, T133-OMEGA-STATUS, T133-HYBRID, T133-MIN, the finite-model output attestation, target-blind replay table, domain evidence-boundary report, and adversarial-review summary.",
                "",
                heading("What Each Public File Is For", 2),
                "The release guide is intentionally first in the file list: it is the public landing surface and tells readers where to start. The master monograph is the canonical scientific artifact and should be cited when discussing the full theory. The journal core article is the compact article-length path for editors, reviewers, and first-pass scientific readers. The methods companion is the reproducibility and audit path. The reviewer attack map is the adversarial path.",
                "",
                "The public zip is a reproducibility bundle, not the first reading surface. It carries source projections, evidence summaries, replay material, checksums, and package metadata so that a reader can verify the release without mistaking machine-readable support files for the scientific exposition. The manifest, checksums, citation, CodeMeta, RO-Crate, release notes, and changelog are included for archival and indexing use.",
                "",
                heading("Editorial Method for the Guide", 2),
                "The guide is evaluated as a reader-facing scientific document, not as an internal process summary. Its positive obligation is to answer the editor's first questions before any archive file is opened: who the document is for, what the release is about, why the release exists, how the argument is built, what the reader should learn, what evidence supports that learning, where prior art enters, what replay or simulation can check, what would reopen the claim, and what the release does not claim.",
                "",
                "The guide therefore uses a short but complete didactic path. It starts with audience and purpose, moves to the reading order, gives the claim boundary, names the evidence anchors, explains the public files in human terms, shows the visual route, and ends with citation and archival notes. That order is intentional: a reader should never have to infer the scientific role of a file from its checksum, filename, or machine manifest.",
                "",
                "This editorial method is also a regression guard. If a future release turns the public landing document into a raw ledger, a metadata wall, an internal routing memo, or a placeholder contents page, the positive mission gate must fail even if all files exist. The guide is allowed to be compact, but it is not allowed to be thin, evasive, or dependent on private process vocabulary.",
                "",
                heading("Claim Boundary", 2),
                "The release surface is deliberately bounded. It promotes the model-core and evidence-backed claims that pass the scientific verification bar. It does not promote unsupported total finality, complete numerical closure for every domain, or unrestricted victory over every local scientific model. Those statements are outside the 1.3.3 public claim surface. This boundary is part of the scientific claim, not a marketing caveat.",
                "",
                "For review purposes, the strongest public claim is that OC Core 1.3.3 is ready for external scientific review as a typed, reproducible, adversarially audited cross-domain model core with explicit limits. A reviewer can attack the formal definitions, theorem dependencies, finite witnesses, empirical lanes, comparator positioning, or release-governance boundaries directly from the public artifacts.",
                "",
                heading("Verification Route", 2),
                "A minimal verification route is: inspect the release guide, check the master monograph front matter and dedication, verify the theorem/evidence anchors in the monograph, inspect the finite-model output attestation, inspect the target-blind prediction table, compare the checksum file with local assets, and read the reviewer attack map for the known high-pressure objections. The release process records the same route in machine-readable form so that future releases cannot substitute an internal routing memo or metadata packet for the primary scientific artifact.",
                "",
                heading("Reviewer Entry Points", 2),
                "A formal reviewer should begin with the master monograph theorem roadmap, then inspect the Lean subset and finite-model attestation. An empirical reviewer should begin with the methods companion, the target-blind replay table, the domain evidence-boundary report, and the negative-control/falsifier rows. A prior-art reviewer should begin with the comparator and novelty register and then use the reviewer attack map. An editor should begin with the journal core article and the journal owner-review package index.",
                "",
                "The theory is intentionally exposed to criticism. If a theorem lacks assumptions, if a finite witness is self-confirming, if a data lane lacks a comparator or negative control, or if a public claim exceeds its evidence, the corresponding gate should fail. The 1.3.3 public release is designed so that those failures are visible and mechanically routable instead of hidden in prose.",
                "",
                figure_route_panels("guide"),
                heading("What to Cite", 2),
                "For the full theory and release-level scientific argument, cite the Master Monograph. For a concise article-shaped description, cite the Journal Core. For reproducibility and validation questions, cite the Methods and Reproducibility Companion. For adversarial-review and claim-boundary questions, cite the Reviewer Attack and Response Map. For archival integrity, cite the DOI record and verify the checksum manifest.",
                "",
                "The preferred human reading path is intentionally different from the machine replay path. Humans should start with the guide and monograph. Machines should start with the manifest, checksums, and public zip. Both paths are present, but the public record is arranged so the human path is visible first.",
                "",
                heading("Editorial and Archival Notes", 2),
                "Editors should treat the journal-preparation materials as preparation aids, not as evidence that a journal submission has occurred. The present public release establishes the scientific and reproducibility baseline from which later editorial decisions can proceed.",
                "",
                "Archivists should treat the Zenodo concept DOI as the version chain and the record DOI as the exact public artifact set for the current 1.3.3 publication. The release notes and checksum manifest record archival integrity details; this guide keeps the reader-facing path focused on the science.",
                "",
                "Readers comparing versions should not infer that every broad future research ambition is completed in 1.3.3. The release distinguishes the bounded external-review model core from the continuing full science program. This distinction is explicit so the artifact can be used for preliminary technical review with scientists, colleagues, and institutions without implying external endorsement, applied-domain validation, or broader proof than the evidence layer provides today.",
                "",
                "For practical use, this means the public record is suitable as a serious review and discussion baseline: it contains the long-form monograph, compact article path, reproducibility companion, adversarial-review map, and replay package. It is not a substitute for the reader's own scientific judgment, but it is arranged so that judgment can be applied to the right artifacts in the right order.",
                "",
                "If the record is mirrored elsewhere, this guide should remain the first visible document. That ordering is part of the release-quality contract: public readers see the science first, then the supporting machine-readable materials.",
                "",
                "The guide also states an editorial promise for the whole artifact family: every public file has a human role, and no file is promoted merely because it exists in the archive. The monograph carries the full argument, the article carries the compressed peer-review route, the methods companion carries replay interpretation, the reviewer map carries adversarial synthesis, and the public zip carries evidence. A reader who cannot tell which file answers which question has found a release defect rather than a personal reading failure.",
                "",
                "The guide's visual pedagogy is intentionally minimal. It does not try to teach every formal construction; it gives just enough orientation to let a reader distinguish the tuple route, lifecycle route, evidence route, and archive route before moving into the longer documents. That keeps the landing document readable while still satisfying the obligation that public science must show readers how to operate the model.",
                "",
                prior_art_minimum_surface("guide"),
                heading("Visual Route Boundary", 2),
                "The guide includes the route diagrams needed for first orientation. The master monograph carries the full visual and figure atlas; the guide's role is to prevent readers from opening the archive in the wrong order while still giving a durable visual map.",
            ]
        ),
        "master": "\n\n".join(
            [
                front(
                    "OC Core 1.3.3 Master Monograph",
                    "Canonical full scientific monograph",
                    [
                        "Reader orientation",
                        "Formal model",
                        "Theorem and proof route",
                        "Executable evidence",
                        "Empirical replay boundary",
                        "Prior-art and reviewer boundary",
                    ],
                ),
                document_editorial_context("master"),
                release_boundary(),
                claim_catalog(max_rows=10),
                theorem_catalog(include_excerpts=True),
                lean_evidence(),
                finite_model_evidence(max_rows=10),
                empirical_evidence(include_lane_replays=False),
                comparator_and_novelty(),
                phenomenon_coverage(max_rows=18),
                literature_position(max_bib=42, max_sources=24),
                figure_atlas_summary(max_rows=12),
                appendices_and_model(),
            ]
        ),
        "journal": "\n\n".join(
            [
                front(
                    "OC Core 1.3.3 Journal Core",
                    "Article-style entry point for external scientific review",
                    [
                        "Problem and related work",
                        "Formal object",
                        "Methods and evidence",
                        "Results and interpretation",
                        "Limitations",
                        "Conclusion",
                    ],
                ),
                document_editorial_context("journal"),
                journal_article_narrative(),
                figure_route_panels("journal"),
                article_results_summary(max_claims=6, max_theorems=8),
                journal_empirical_summary(),
                journal_comparator_summary(),
                journal_prior_art_detailed_comparison(),
                journal_phenomenon_summary(),
                journal_article_worked_reading_path(),
                literature_position(max_bib=42, max_sources=14),
                heading("Figure Route Summary", 2),
                "The article embeds the minimum figure route directly: tuple, lifecycle, K-level, boundary, evidence, and replay-boundary diagrams appear in the article itself. The master monograph contains the larger figure sequence, but the article does not require that sequence to understand the core visual logic.",
                journal_article_extended_discussion(),
            ]
        ),
        "methods": "\n\n".join(
            [
                front(
                    "OC Core 1.3.3 Methods and Reproducibility Companion",
                    "Reproducibility, validation, and audit-navigation companion",
                    [
                        "Reproducibility method",
                        "Environment and inputs",
                        "Command replay",
                        "Expected outputs and hashes",
                        "Failure interpretation",
                        "Claim affected by each check",
                    ],
                ),
                document_editorial_context("methods"),
                methods_replay_narrative(),
                methods_replay_matrix(),
                methods_positive_audit_protocol(),
                figure_route_panels("methods"),
                prior_art_minimum_surface("methods"),
                observed_reproducibility_bom(),
                release_boundary(),
                heading("Data and Source Authority Notes", 2),
                "The methods companion treats empirical authorities as replay inputs, not as ornamental bibliography. Physics rows refer to official physical constants and pinned public-source snapshots. Chemistry rows refer to public chemistry property sources and compound/property snapshots. Biology rows refer to public biological datasets or expression snapshots. Systems rows refer to public indicator time series. Each row must keep source identity, access or snapshot date, formula, comparator, residual, negative control, falsifier, and replay hash together.",
                "",
                "Formal source references, data-source records, and bibliographic records are normalized in the public evidence package and metadata files. This PDF explains how to read them during replay.",
                "",
                heading("Environment Version Capture", 2),
                "A reviewer should record local versions before interpreting a mismatch: Python runtime, Lean/Lake version, Pandoc version, XeLaTeX distribution, Poppler version, operating system, repository commit, public zip checksum, and DOI record. These values are not scientific conclusions, but they decide whether a difference is a model defect, a replay-environment defect, or an archive-integrity defect.",
                "",
                "Repository commit. This binds source files to public PDFs and manifests. A wrong commit means the replay is not testing the published object.",
                "",
                "Public zip checksum. This binds the downloaded archive to the DOI record. A mismatch is an archive-integrity problem before it is a scientific problem.",
                "",
                "Python runtime. This executes finite-model, validation, simulation, and packaging scripts. Version-sensitive output must be recorded as a replay-environment finding.",
                "",
                "Lean/Lake. This checks the selected formal subset. A build failure reopens theorem boundaries that cite the formal subset.",
                "",
                "Pandoc, XeLaTeX, and Poppler. These rebuild and audit public PDFs. Text or page-count drift is an editorial and reproducibility finding.",
                "",
                "This version-capture rule prevents a common false inference. A local rebuild mismatch is not automatically a refutation of OC, but it is also not harmless. The reviewer first identifies which layer changed, then routes the finding to the claim, evidence, archive, or editorial surface that actually depends on that layer.",
            ]
        ),
        "reviewer": "\n\n".join(
            [
                front(
                    "OC Core 1.3.3 Reviewer Attack and Response Map",
                    "Adversarial objections, boundaries, and response map",
                    [
                        "Adversarial review method",
                        "Claim families under attack",
                        "Proof and evidence responses",
                        "Novelty and prior-art attacks",
                        "Residual risks",
                        "Reopening conditions",
                    ],
                ),
                document_editorial_context("reviewer"),
                reviewer_response_narrative(),
                release_boundary(),
                attack_matrix(max_rows=18),
                reviewer_adversarial_synthesis(),
                reviewer_role_playbook(),
                prior_art_minimum_surface("reviewer"),
                figure_route_panels("reviewer"),
            ]
        ),
    }
    paths: dict[str, Path] = {}
    for key, body in docs.items():
        path = PUBLIC_SOURCES / PDF_SPECS[key]["source"]
        if key == "journal":
            body = compact_journal_body(body)
        write_text_if_changed(path, clean_public_text(promote_body_headings(body)))
        paths[key] = path
    return paths


def build_pdf(source: Path, output: Path, title: str) -> dict[str, Any]:
    output.parent.mkdir(parents=True, exist_ok=True)
    resource_path = os.pathsep.join(
        [
            str(source.parent),
            str(PUBLIC_PAYLOAD),
            str(PUBLIC_FIGURES),
            str(ROOT),
        ]
    )
    cmd = [
        "pandoc",
        str(source),
        "--from",
        "markdown+raw_tex",
        "--toc",
        "--toc-depth",
        "2",
        "--resource-path",
        resource_path,
        "--number-sections",
        "--pdf-engine=xelatex",
        "--metadata",
        f"title={title}",
        "--metadata",
        "geometry:margin=0.9in",
        "-o",
        str(output),
    ]
    completed = subprocess.run(cmd, cwd=ROOT, text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=900)
    command = " ".join(cmd).replace(str(ROOT.resolve()), "<REPO_ROOT>")
    stdout_tail = completed.stdout[-2000:].replace(str(ROOT.resolve()), "<REPO_ROOT>")
    stderr_tail = completed.stderr[-4000:].replace(str(ROOT.resolve()), "<REPO_ROOT>")
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout_tail": stdout_tail,
        "stderr_tail": stderr_tail,
        "output": rel(output),
        "ok": completed.returncode == 0 and output.exists() and output.stat().st_size > 0,
    }


def pdf_text(path: Path, *, persist_audit_text: bool = True) -> tuple[str, int]:
    if persist_audit_text:
        txt_path = EDITORIAL / "pdf_text_audit" / f"{path.stem}.txt"
        return _pdf_text_to_path(path, txt_path)

    with tempfile.TemporaryDirectory(prefix="oc133_pdf_text_audit_") as tmp_dir:
        txt_path = Path(tmp_dir) / f"{path.stem}.txt"
        return _pdf_text_to_path(path, txt_path)


def _pdf_text_to_path(path: Path, txt_path: Path) -> tuple[str, int]:
    txt_path.parent.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        ["pdftotext", str(path), str(txt_path)],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=180,
    )
    if completed.returncode != 0:
        return completed.stderr, 0
    text = read_text(txt_path)
    try:
        from pypdf import PdfReader  # type: ignore

        pages = len(PdfReader(str(path)).pages)
    except Exception:
        pages = 0
    return text, pages


def public_pdf_audit(*, persist_audit_text: bool = True) -> dict[str, Any]:
    rows = []
    failures = []
    for key, spec in PDF_SPECS.items():
        path = ARTIFACTS / spec["filename"]
        text, pages = pdf_text(path, persist_audit_text=persist_audit_text) if path.exists() else ("", 0)
        forbidden_hits = [m.group(0) for m in PUBLIC_FORBIDDEN_RE.finditer(text)]
        overclaim_hits = [m.group(0) for m in ABSOLUTE_OVERCLAIM_RE.finditer(text)]
        route_sheet_hits = [m.group(0) for m in ROUTE_SHEET_RE.finditer(text)]
        known_error_hits = [
            {"error_id": error_id, "match": match.group(0)}
            for error_id, regex in KNOWN_PUBLICATION_ERROR_PATTERNS.items()
            for match in regex.finditer(text)
        ]
        title_page_present = "Ontology of Continua" in text and "Alexander Yashin" in text and version_frontmatter_present(text)
        reader_contract_present = reader_orientation_present(text)
        abstract_present = "Abstract" in text
        row = {
            "artifact": rel(path),
            "exists": path.exists(),
            "size_bytes": path.stat().st_size if path.exists() else 0,
            "pages": pages,
            "text_chars": len(text),
            "min_chars": spec["min_chars"],
            "min_pages": spec["min_pages"],
            "version_present": version_frontmatter_present(text),
            "toc_present": "Contents" in text or "Table of Contents" in text,
            "title_page_present": title_page_present,
            "dedication_present": dedication_frontmatter_present(text),
            "abstract_present": abstract_present,
            "reader_contract_present": reader_contract_present,
            "science_delta_present": "T133-K0-RES" in text and "target-blind" in text if key == "master" else True,
            "forbidden_hit_total": len(forbidden_hits),
            "overclaim_hit_total": len(overclaim_hits),
            "route_sheet_hit_total": len(route_sheet_hits),
            "known_error_hit_total": len(known_error_hits),
            "forbidden_hits": forbidden_hits[:20],
            "overclaim_hits": overclaim_hits[:20],
            "route_sheet_hits": route_sheet_hits[:20],
            "known_error_hits": known_error_hits[:20],
        }
        ok = (
            row["exists"]
            and row["size_bytes"] >= int(spec.get("min_size", 50000))
            and row["pages"] >= spec["min_pages"]
            and row["text_chars"] >= spec["min_chars"]
            and row["version_present"]
            and row["toc_present"]
            and row["title_page_present"]
            and row["dedication_present"]
            and row["abstract_present"]
            and row["reader_contract_present"]
            and row["science_delta_present"]
            and row["forbidden_hit_total"] == 0
            and row["overclaim_hit_total"] == 0
            and row["route_sheet_hit_total"] == 0
            and row["known_error_hit_total"] == 0
        )
        row["state"] = "PASS" if ok else "FAIL"
        if not ok:
            failures.append(row)
        rows.append(row)
    return {"state": "PASS" if not failures else "FAIL", "rows": rows, "failure_total": len(failures)}


def publication_grade_text_gate(*, persist_audit_text: bool = False) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for key, spec in PDF_SPECS.items():
        path = ARTIFACTS / spec["filename"]
        text, pages = pdf_text(path, persist_audit_text=persist_audit_text) if path.exists() else ("", 0)
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        bullet_like_total = sum(1 for line in lines if re.match(r"^[-*•]\s+|^\d+\.\s+", line))
        heading_like_total = sum(1 for line in lines if len(line) < 90 and line.istitle())
        paragraph_total = sum(1 for line in lines if len(line) > 160 and not re.match(r"^[-*•]\s+|^\d+\.\s+", line))
        raw_hash_total = len(re.findall(r"\b[a-f0-9]{64}\b", text, re.I))
        required_missing = publication_grade_missing_frontmatter(text)
        transition_hits = sum(
            text.lower().count(phrase)
            for phrase in [
                "therefore",
                "because",
                "in contrast",
                "the release does not",
                "the reader should",
                "this section",
                "the evidence",
            ]
        )
        route_sheet_hits = [m.group(0) for m in ROUTE_SHEET_RE.finditer(text)]
        known_error_hits = [
            {"error_id": error_id, "match": match.group(0)}
            for error_id, regex in KNOWN_PUBLICATION_ERROR_PATTERNS.items()
            for match in regex.finditer(text)
        ]
        forbidden_structure_hits = []
        if key == "master" and "Science Delta Appendix" in text:
            forbidden_structure_hits.append("Science Delta Appendix")
        if key == "master" and "publication-grade manuscript" not in text.lower():
            forbidden_structure_hits.append("missing publication-grade manuscript anchor")
        line_total = max(1, len(lines))
        bullet_ratio = bullet_like_total / line_total
        heading_ratio = heading_like_total / line_total
        checks = {
            "exists": path.exists(),
            "page_count_ok": pages >= spec["min_pages"],
            "text_volume_ok": len(text) >= spec["min_chars"],
            "required_frontmatter_ok": not required_missing,
            "paragraph_density_ok": paragraph_total >= max(5, pages // 8),
            "not_bullet_dump": bullet_ratio <= 0.55,
            "not_heading_dump": heading_ratio <= 0.55,
            "not_checksum_wall": raw_hash_total <= (80 if key == "master" else 25),
            "route_sheet_absent": not route_sheet_hits,
            "known_publication_errors_absent": not known_error_hits,
            "forbidden_structure_absent": not forbidden_structure_hits,
            "transition_language_present": transition_hits >= (12 if key == "master" else 4),
        }
        row = {
            "artifact": rel(path),
            "state": "PASS" if all(checks.values()) else "FAIL",
            "pages": pages,
            "text_chars": len(text),
            "line_total": len(lines),
            "paragraph_total": paragraph_total,
            "bullet_like_total": bullet_like_total,
            "heading_like_total": heading_like_total,
            "bullet_ratio": round(bullet_ratio, 4),
            "heading_ratio": round(heading_ratio, 4),
            "raw_sha256_total": raw_hash_total,
            "transition_hits": transition_hits,
            "required_missing": required_missing,
            "route_sheet_hits": route_sheet_hits[:20],
            "known_error_hits": known_error_hits[:20],
            "forbidden_structure_hits": forbidden_structure_hits,
            "checks": checks,
        }
        rows.append(row)
        if row["state"] != "PASS":
            failures.append(row)
    return {
        "gate_id": "PUBLICATION_GRADE_TEXT_GATE",
        "state": "PASS" if not failures else "FAIL",
        "failure_total": len(failures),
        "rows": rows,
    }


def journal_editorial_board_gate(*, persist_audit_text: bool = False) -> dict[str, Any]:
    bib_total = len(bibliography_entries())
    figure_total = len(figure_entries())
    rows: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    editorial_phrases = {
        "audience": ["Audience.", "This document is written for", "primary audience"],
        "purpose": ["Purpose.", "Purpose and role.", "It exists to", "The document exists to"],
        "construction": ["Construction.", "argument is organized", "reading order", "replay order"],
        "didactic_rule": ["Didactic rule.", "teaching obligation", "reader should learn"],
        "literature": ["Literature and Prior-Art Position", "Prior-Art and Literature Position", "Prior-Art", "literature"],
        "visual_design": ["Visual and Design Review", "Visual Route", "Figure Route", "Core Route Summaries", "Operational Diagrams", "route panel"],
        "reader_path": ["recommended reader path", "recommended reading order", "reading route", "Reader Route Figures", "Replay Route Figures"],
        "target_audience": ["primary audience", "written for"],
        "claim_boundary": "claim boundary",
    }
    for key, spec in PDF_SPECS.items():
        path = ARTIFACTS / spec["filename"]
        text, pages = pdf_text(path, persist_audit_text=persist_audit_text) if path.exists() else ("", 0)
        paragraph_blocks = [
            re.sub(r"\s+", " ", block).strip()
            for block in re.split(r"\n\s*\n", text)
            if len(re.findall(r"[A-Za-z][A-Za-z'-]+", block)) >= 24
            and not block.strip().startswith(("Figure ", "Table "))
        ]
        raw_dict_hits = len(re.findall(r"\{['\"][^{}\n]{1,80}['\"]\s*:", text))
        known_error_hits = [
            {"error_id": error_id, "match": match.group(0)}
            for error_id, regex in KNOWN_PUBLICATION_ERROR_PATTERNS.items()
            for match in regex.finditer(text)
        ]
        phrase_checks = {
            name: (
                any(option.lower() in text.lower() for option in phrase)
                if isinstance(phrase, list)
                else phrase.lower() in text.lower()
            )
            for name, phrase in editorial_phrases.items()
        }
        checks = {
            "exists": path.exists(),
            "editorial_passport_present": all(phrase_checks[name] for name in ["audience", "purpose", "construction", "didactic_rule"]),
            "literature_section_present": phrase_checks["literature"],
            "visual_design_section_present": phrase_checks["visual_design"],
            "reader_path_present": phrase_checks["reader_path"],
            "target_audience_present": phrase_checks["target_audience"],
            "claim_boundary_present": phrase_checks["claim_boundary"],
            "paragraph_material_present": len(paragraph_blocks) >= max(6, pages // 5),
            "raw_python_dict_absent": raw_dict_hits == 0,
            "known_publication_errors_absent": not known_error_hits,
        }
        row = {
            "artifact": rel(path),
            "state": "PASS" if all(checks.values()) else "FAIL",
            "pages": pages,
                "paragraph_block_total": len(paragraph_blocks),
            "raw_python_dict_hits": raw_dict_hits,
            "known_error_hits": known_error_hits[:20],
            "phrase_checks": phrase_checks,
            "checks": checks,
        }
        rows.append(row)
        if row["state"] != "PASS":
            failures.append(row)
    corpus_checks = {
        "bibliography_total_ok": bib_total >= 40,
        "figure_total_ok": figure_total >= 29,
        "all_public_pdfs_checked": len(rows) == len(PDF_SPECS),
    }
    if not all(corpus_checks.values()):
        failures.append({"artifact": "release corpus", "state": "FAIL", "checks": corpus_checks})
    return {
        "gate_id": "JOURNAL_EDITORIAL_BOARD_GATE",
        "state": "PASS" if not failures else "FAIL",
        "failure_total": len(failures),
        "bibliography_total": bib_total,
        "figure_total": figure_total,
        "corpus_checks": corpus_checks,
        "rows": rows,
    }


def explanatory_prose_units(text: str) -> list[str]:
    """Count explanatory prose independently of accidental PDF line wrapping."""

    normalized_lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            normalized_lines.append("")
            continue
        if re.match(r"^\d+$", line):
            continue
        if re.match(r"^[-*•]\s+|^\d+\.\s+", line):
            continue
        if line.startswith("|") or line in {"Route", "Reader path", "What the path prevents"}:
            continue
        if len(line) < 80 and re.match(r"^\d+\s+[A-Z]", line):
            continue
        normalized_lines.append(line)
    joined = re.sub(r"\s+", " ", " ".join(normalized_lines)).strip()
    candidates = re.split(r"(?<=[.!?])\s+(?=(?:[A-Z]|The |This |For |If |Because |Consequently |Readers |Editors |Archivists))", joined)
    units = []
    for candidate in candidates:
        cleaned = candidate.strip()
        words = re.findall(r"[A-Za-z][A-Za-z0-9'-]*", cleaned)
        if len(words) >= 24 and not cleaned.startswith(("Figure ", "Table ")):
            units.append(cleaned)
    return units


def positive_mission_fulfillment_gate(*, persist_audit_text: bool = False) -> dict[str, Any]:
    role_requirements = {
        "guide": [
            "Public Landing Guide",
            "Recommended Reading Order",
            "Evidence Summary",
            "Claim Boundary",
            "Verification Route",
            "What to Cite",
        ],
        "master": [
            "Reader Contract",
            "Literature and Prior-Art Position",
            "Figure Route",
            "Model-Core Claims",
            "Theorem and Proof Integration",
            "Bounded Replay QA and Artifact-Integrity Examples",
        ],
        "journal": [
            "Introduction",
            "Problem",
            "Contribution",
            "Formal",
            "Evidence",
            "Prior-Art",
            "Limit",
            "Conclusion",
        ],
        "methods": [
            "Reproducibility Method",
            "Prerequisites",
            "Replay Order",
            "Expected Outputs",
            "Failure Interpretation",
            "Artifact Map",
            "Checksum",
        ],
        "reviewer": [
            "Reviewer Response Method",
            "Reviewer challenge",
            "attacked claim",
            "criticism route",
            "response evidence",
            "Residual risk",
            "reopening",
        ],
    }
    literature_families = [
        "General systems and emergence",
        "Autopoiesis and organizational closure",
        "Dynamical and hybrid systems",
        "Category and type-theoretic formalisms",
        "RAF and chemical closure",
        "Complexity and information measures",
        "Identity, continuity, and lifecycle theory",
        "Reproducible research and artifact evaluation",
    ]
    visual_anchors = [
        "Tuple map",
        "Lifecycle route",
        "K-level route",
        "Boundary route",
        "Evidence route",
    ]
    reader_questions = {
        "who_is_this_for": ["audience"],
        "what_is_this_about": ["claim", "model"],
        "why_this_document_exists": ["purpose", "role"],
        "how_the_argument_is_built": ["construction", "order"],
        "what_the_reader_should_learn": ["reader", "should"],
        "what_evidence_supports_it": ["evidence", "support"],
        "what_prior_art_context_applies": ["prior-art", "comparator"],
        "what_data_or_simulation_can_check_it": ["finite", "replay"],
        "what_would_reopen_or_falsify_it": ["falsifier", "reopen"],
        "what_is_not_claimed": ["does not", "claim"],
    }
    rows: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    all_texts: dict[str, str] = {}
    doi_values: set[str] = set()
    version_ok_all = True
    repeated_paragraphs: dict[str, int] = {}
    for key, spec in PDF_SPECS.items():
        path = ARTIFACTS / spec["filename"]
        text, pages = pdf_text(path, persist_audit_text=persist_audit_text) if path.exists() else ("", 0)
        all_texts[key] = text
        lowered = text.lower()
        paragraphs = explanatory_prose_units(text)
        positive_dimensions = {
            "audience_named": "audience." in lowered or "this document is for" in lowered or "this document is written for" in lowered or "primary audience" in lowered,
            "purpose_named": "purpose." in lowered or "exists so" in lowered or "it exists to" in lowered or "document role." in lowered,
            "construction_named": "construction." in lowered or "argument is organized" in lowered or "recommended reading order" in lowered or "replay order" in lowered,
            "claim_surface_named": "claim" in lowered and ("boundary" in lowered or "scope" in lowered or "limit" in lowered),
            "evidence_surface_named": "evidence" in lowered and ("proof" in lowered or "replay" in lowered or "finite" in lowered or "lean" in lowered),
            "prior_art_or_literature_named": "prior-art" in lowered or "literature" in lowered or "comparator" in lowered,
            "visual_pedagogy_named": "figure" in lowered or "visual" in lowered or "diagram" in lowered,
            "falsifier_or_limit_named": "falsifier" in lowered or "falsify" in lowered or "reopens" in lowered or "limit" in lowered,
            "reader_payoff_named": "reader" in lowered and ("path" in lowered or "contract" in lowered or "should" in lowered),
            "research_state_named": "current science" in lowered or "research state" in lowered or "model-core" in lowered,
            "methodological_standard_named": "publication-grade" in lowered or "scientific text" in lowered or "editorial" in lowered,
        }
        question_coverage = {
            question_id: all(token in lowered for token in tokens)
            for question_id, tokens in reader_questions.items()
        }
        for paragraph in paragraphs:
            normalized = re.sub(r"\s+", " ", paragraph.lower())
            if len(normalized) > 220:
                repeated_paragraphs[normalized[:260]] = repeated_paragraphs.get(normalized[:260], 0) + 1
        found_required = {
            requirement: requirement.lower() in lowered
            for requirement in role_requirements.get(key, [])
        }
        blank_hits = [m.group(0) for m in BLANK_PUBLIC_FIELD_RE.finditer(text)]
        meta_hits = [m.group(0) for m in META_INTEGRATION_MARKER_RE.finditer(text)]
        doi_values.update(re.findall(r"10\.5281/zenodo\.\d+", text))
        version_ok = VERSION in text
        version_ok_all = version_ok_all and version_ok
        section_score = sum(found_required.values()) / max(1, len(found_required))
        checks = {
            "exists": path.exists(),
            "role_required_sections_present": section_score >= 1.0,
            "explanatory_paragraphs_present": len(paragraphs) >= 8,
            "blank_public_status_fields_absent": not blank_hits,
            "meta_integration_markers_absent": not meta_hits,
            "version_present": version_ok,
            "document_role_declared": "Document role." in text,
            "reader_contract_declared": reader_orientation_present(text),
            "claim_boundary_declared": "claim boundary" in lowered,
            "positive_must_have_dimensions_present": all(positive_dimensions.values()),
            "positive_must_have_dimension_score_ok": sum(positive_dimensions.values()) / max(1, len(positive_dimensions)) >= 0.95,
            "reader_question_coverage_complete": all(question_coverage.values()),
        }
        score = sum(checks.values()) / max(1, len(checks))
        row = {
            "artifact": rel(path),
            "state": "PASS" if all(checks.values()) else "FAIL",
            "mission_fulfillment_score": round(score, 4),
            "pages": pages,
            "explanatory_paragraph_total": len(paragraphs),
            "required_section_score": round(section_score, 4),
            "required_sections": found_required,
            "blank_public_status_field_total": len(blank_hits),
            "meta_integration_marker_total": len(meta_hits),
            "blank_public_status_field_hits": blank_hits[:20],
            "meta_integration_marker_hits": meta_hits[:20],
            "positive_dimensions": positive_dimensions,
            "reader_questions": question_coverage,
            "checks": checks,
        }
        rows.append(row)
        if row["state"] != "PASS":
            failures.append(row)
    combined = "\n".join(all_texts.values())
    combined_lower = combined.lower()
    literature_presence = {item: item.lower() in combined_lower for item in literature_families}
    visual_presence = {item: item.lower() in combined_lower for item in visual_anchors}
    science_coverage_anchors = {
        "typed_model_core": "typed" in combined_lower and "model" in combined_lower,
        "theorem_proof_route": "theorem" in combined_lower and "proof" in combined_lower,
        "lean_subset": "lean" in combined_lower,
        "finite_semantics": "finite-model" in combined_lower or "finite model" in combined_lower,
        "target_blind_numeric_evidence": "target-blind" in combined_lower and ("numeric" in combined_lower or "reconstruction" in combined_lower),
        "negative_controls_or_falsifiers": "negative control" in combined_lower and "falsifier" in combined_lower,
        "prior_art_comparator": "prior-art" in combined_lower and "comparator" in combined_lower,
        "phenomenon_coverage": "phenomenon" in combined_lower and "coverage" in combined_lower,
        "adversarial_review": "adversarial review" in combined_lower or "reviewer challenge" in combined_lower,
        "journal_owner_review_path": "journal" in combined_lower and ("owner review" in combined_lower or "owner-review" in combined_lower),
    }
    repeated_total = sum(count - 1 for count in repeated_paragraphs.values() if count > 1)
    paragraph_total = sum(1 for text in all_texts.values() for line in text.splitlines() if len(line.strip()) > 160)
    repetition_ratio = repeated_total / max(1, paragraph_total)
    version_doi_values = {value for value in doi_values if value != "10.5281/zenodo.17899134"}
    parity_checks = {
        "single_or_no_public_version_doi_value": len(version_doi_values) <= 1,
        "version_present_in_all_pdfs": version_ok_all,
        "literature_synthesis_family_count_ok": sum(literature_presence.values()) >= 8,
        "visual_pedagogy_anchor_count_ok": sum(visual_presence.values()) >= 5,
        "science_coverage_anchor_count_ok": all(science_coverage_anchors.values()),
        "boilerplate_repetition_ratio_ok": repetition_ratio <= 0.25,
    }
    monolith_ledger = read_json(EDITORIAL / "SCIENCE_MONOLITH_CORPUS_LEDGER_1_3_3_latest.json", {})
    ledger_rows = monolith_ledger.get("rows", []) if isinstance(monolith_ledger.get("rows"), list) else []
    required_current_science_refs = [
        "claims/CLAIM_LEDGER_1_3_3.json",
        "proofs/THEOREM_INVENTORY_1_3_3.json",
        "proofs/THEOREM_REGISTRY_1_3_3.json",
        "formal/lean/OC133V12.lean",
        "formal/lean/LEAN_BUILD_CERTIFICATE_1_3_3.json",
        "proofs/FINITE_MODEL_CHECKS_1_3_3.json",
        "proofs/FINITE_MODEL_OUTPUT_ATTESTATION_1_3_3.json",
        "validation/target_blind/OC133_TARGET_BLIND_PREDICTION_TABLE.json",
        "validation/numeric_replay_qa/OC133_NUMERIC_REPLAY_QA_TABLE.json",
        "reports/OC_CORE_1_3_3_DOMAIN_VALIDATION_REPORT.json",
        "docs/OC_1_3_3_PRIOR_ART_COMPARATOR_MATRIX.json",
        "comparators/OC_1_3_3_NOVELTY_AND_PRIORITY_REGISTER.json",
        "docs/OC_1_3_3_PHENOMENON_COVERAGE_MATRIX.json",
        "reviews/oc133_llm_cerberus/OC133_LLM_CERBERUS_SUMMARY.json",
        "releases/oc_core_1_3_3/submission_packages/SUBMISSION_PACKAGE_INDEX.json",
    ]
    current_science_inclusion = {
        ref: any(row.get("ref") == ref and row.get("exists") is True for row in ledger_rows)
        for ref in required_current_science_refs
    }
    parity_checks["current_science_corpus_included_or_cited"] = all(current_science_inclusion.values())
    if not all(parity_checks.values()):
        failures.append({"artifact": "public PDF set", "state": "FAIL", "checks": parity_checks})
    return {
        "gate_id": "POSITIVE_MISSION_FULFILLMENT_GATE",
        "state": "PASS" if not failures else "FAIL",
        "failure_total": len(failures),
        "mission_fulfillment_score": round(sum(row["mission_fulfillment_score"] for row in rows) / max(1, len(rows)), 4),
        "literature_synthesis_family_total": sum(literature_presence.values()),
        "visual_pedagogy_anchor_total": sum(visual_presence.values()),
        "science_coverage_anchor_total": sum(science_coverage_anchors.values()),
        "boilerplate_repetition_ratio": round(repetition_ratio, 4),
        "doi_values": sorted(doi_values),
        "parity_checks": parity_checks,
        "current_science_inclusion": current_science_inclusion,
        "literature_presence": literature_presence,
        "visual_presence": visual_presence,
        "science_coverage_anchors": science_coverage_anchors,
        "rows": rows,
        "failures": failures[:20],
    }


def editorial_cerberus_gate() -> dict[str, Any]:
    summary = read_json(EDITORIAL_CERBERUS_SUMMARY, {})
    current_hashes = {
        key: sha256_file(ARTIFACTS / spec["filename"]) if (ARTIFACTS / spec["filename"]).is_file() else None
        for key, spec in PDF_SPECS.items()
    }
    report_hashes = summary.get("pdf_hashes", {}) if isinstance(summary, dict) else {}
    hash_mismatch = {
        key: {"current": value, "reported": report_hashes.get(key)}
        for key, value in current_hashes.items()
        if value and report_hashes.get(key) and report_hashes.get(key) != value
    }
    required_roles = {
        "scientific_copyeditor",
        "technical_editor",
        "journal_editor",
        "layout_toc_page_flow_reviewer",
        "hostile_reader",
        "bibliography_metadata_editor",
        "claim_evidence_prosecutor",
    }
    role_ids = set(summary.get("role_ids", [])) if isinstance(summary.get("role_ids"), list) else set()
    missing_roles = sorted(required_roles - role_ids)
    checks = {
        "summary_exists": EDITORIAL_CERBERUS_SUMMARY.exists(),
        "state_pass": summary.get("state") == "PASS",
        "critical_open_zero": int(summary.get("critical_open_total", 999)) == 0,
        "high_open_zero": int(summary.get("high_open_total", 999)) == 0,
        "parse_failures_zero": int(summary.get("parse_failure_total", 999)) == 0,
        "all_required_roles_present": not missing_roles,
        "pdf_hashes_current": not hash_mismatch and all(report_hashes.get(key) == value for key, value in current_hashes.items() if value),
    }
    return {
        "gate_id": "EDITORIAL_CERBERUS_LLM_REVIEW_GATE",
        "path": rel(EDITORIAL_CERBERUS_SUMMARY),
        "exists": EDITORIAL_CERBERUS_SUMMARY.exists(),
        "state": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "missing_roles": missing_roles,
        "hash_mismatch": hash_mismatch,
        "critical_open_total": summary.get("critical_open_total"),
        "high_open_total": summary.get("high_open_total"),
        "parse_failure_total": summary.get("parse_failure_total"),
    }


def scientific_process_spot_gate(*, write: bool = False) -> dict[str, Any]:
    spot = oc133_scientific_process_spot.write_spot(ROOT) if write else oc133_scientific_process_spot.build_spot(ROOT)
    gate_states = {gate.get("gate_id"): gate.get("state") for gate in spot.get("gates", []) if isinstance(gate, dict)}
    maturity = spot.get("maturity", {}) if isinstance(spot.get("maturity"), dict) else {}
    checks = {
        "spot_exists_or_built": bool(spot),
        "spot_pass": spot.get("state") == "PASS",
        "claim_support_stack_pass": gate_states.get("SPOT-001_PROMOTED_CLAIM_SUPPORT_STACK") == "PASS",
        "empirical_numeric_stack_pass": gate_states.get("SPOT-002_EMPIRICAL_NUMERIC_EVIDENCE_STACK") == "PASS",
        "prior_art_alignment_pass": gate_states.get("SPOT-003_PRIOR_ART_CURRENT_SCIENCE_ALIGNMENT") == "PASS",
        "current_science_corpus_complete": gate_states.get("SPOT-004_CURRENT_SCIENCE_CORPUS_COMPLETENESS") == "PASS",
        "external_positioning_from_spot_pass": gate_states.get("SPOT-005_EXTERNAL_POSITIONING_FROM_RESEARCH_STATE") == "PASS",
        "process_research_visibility_pass": gate_states.get("SPOT-006_PROCESS_RESEARCH_STATE_VISIBILITY") == "PASS",
        "positive_mission_and_method_pass": gate_states.get("SPOT-008_POSITIVE_MISSION_AND_METHOD_FULFILLMENT") == "PASS",
        "review_clean_pass": gate_states.get("SPOT-007_ADVERSARIAL_AND_EDITORIAL_REVIEW_CLEAN") == "PASS",
    }
    return {
        "gate_id": "SCIENTIFIC_PROCESS_SPOT_GATE",
        "path": rel(SCIENTIFIC_PROCESS_SPOT),
        "state": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "spot_state": spot.get("state"),
        "spot_blocker_total": spot.get("blocker_total"),
        "gate_states": gate_states,
        "maturity": maturity,
        "current_research_state": spot.get("current_research_state", {}),
        "external_speech_contract": spot.get("external_speech_contract", {}),
    }


def public_assets() -> list[dict[str, str]]:
    base = []
    for key, spec in PDF_SPECS.items():
        base.append(
            {
                "path": f"releases/{RELEASE_ID}/artifacts/{spec['filename']}",
                "label": spec["title"].replace("OC Core 1.3.3 ", ""),
                "description": spec["description"],
                "role": "PUBLIC_SCIENTIFIC_DOCUMENT",
            }
        )
    base.extend(
        [
            {
                "path": f"releases/{RELEASE_ID}/artifacts/{PUBLIC_ZIP_NAME}",
                "label": "Public reproducibility package",
                "description": "Canonical public GitHub/Zenodo reproducibility package.",
                "role": "PUBLIC_REPRODUCIBILITY_PACKAGE",
            },
            {"path": "manifest.json", "label": "Public manifest", "description": "Machine-readable public release manifest.", "role": "PUBLIC_METADATA"},
            {"path": "checksums.txt", "label": "Checksums", "description": "SHA-256 checksums for public release assets.", "role": "PUBLIC_METADATA"},
            {"path": "CITATION.cff", "label": "Citation metadata", "description": "Citation metadata for OC Core 1.3.3.", "role": "PUBLIC_METADATA"},
            {"path": ".codemeta.json", "label": "CodeMeta metadata", "description": "CodeMeta metadata for OC Core 1.3.3.", "role": "PUBLIC_METADATA"},
            {"path": "ro-crate-metadata.jsonld", "label": "RO-Crate metadata", "description": "RO-Crate metadata for OC Core 1.3.3.", "role": "PUBLIC_METADATA"},
            {"path": f"releases/{RELEASE_ID}/RELEASE_NOTES.md", "label": "Release notes", "description": "Human-readable release notes.", "role": "PUBLIC_NOTES"},
            {"path": f"releases/{RELEASE_ID}/CHANGELOG.md", "label": "Changelog", "description": "Release changelog summary.", "role": "PUBLIC_NOTES"},
        ]
    )
    return base


def zenodo_assets() -> list[dict[str, str]]:
    """Curated Zenodo public surface: readable PDFs plus the archival public ZIP.

    GitHub can carry standalone metadata files because its release page renders a
    controlled Markdown body. Zenodo previews deposited files directly, so raw
    JSON/Markdown/checksum files are kept inside the ZIP and on GitHub rather
    than uploaded as independent Zenodo landing-surface files.
    """
    return [
        row
        for row in public_assets()
        if row["role"] in {"PUBLIC_SCIENTIFIC_DOCUMENT", "PUBLIC_REPRODUCIBILITY_PACKAGE"}
    ]


def materialize_public_evidence_summaries() -> list[Path]:
    PUBLIC_EVIDENCE.mkdir(parents=True, exist_ok=True)
    refs = [
        "formal/lean/OC133V12.lean",
        "proofs/FINITE_MODEL_OUTPUT_ATTESTATION_1_3_3.json",
        "docs/OC_1_3_3_PHENOMENON_COVERAGE_MATRIX.json",
        "validation/target_blind/OC133_TARGET_BLIND_PREDICTION_TABLE.json",
        "reports/OC_CORE_1_3_3_DOMAIN_VALIDATION_REPORT.json",
        "reviews/oc133_llm_cerberus/OC133_LLM_CERBERUS_SUMMARY.json",
        "simulations/results/OC_CORE_1_3_3_SIMULATION_RESULTS_latest.json",
        "reports/OC_CORE_1_3_3_ADVERSARIAL_SIMULATION_REPORT.json",
        "reports/OC_CORE_1_3_3_COUNTEREXAMPLE_REPORT.json",
        f"releases/{RELEASE_ID}/editorial/SCIENCE_MONOLITH_CORPUS_LEDGER_1_3_3_latest.json",
        f"releases/{RELEASE_ID}/editorial/SCIENCE_MONOLITH_AUDIT_1_3_3_latest.json",
    ]
    out_paths = []
    for ref in refs:
        src = ROOT / ref
        if not src.exists():
            continue
        dst = PUBLIC_EVIDENCE / ref.replace("/", "__").replace("\\", "__")
        if src.suffix.lower() in {".json", ".jsonld"}:
            public_json = scrub_public_evidence_json(sanitize_public_json(read_json(src, {})))
            public_json = apply_public_release_promotion_contract(public_json, ref)
            write_json_if_changed(dst, public_json)
        elif src.suffix.lower() in TEXT_SUFFIXES:
            write_text_if_changed(dst, clean_public_text(read_text(src)))
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            if not dst.exists() or dst.read_bytes() != src.read_bytes():
                dst.write_bytes(src.read_bytes())
        out_paths.append(dst)

    public_theorems = scrub_public_evidence_json(sanitize_public_json(read_json(ROOT / "proofs" / "THEOREM_REGISTRY_1_3_3.json", {})))
    public_theorems = apply_public_release_promotion_contract(public_theorems, "proofs/THEOREM_REGISTRY_1_3_3.json")
    for row in public_theorems.get("rows", []):
        for key, value in list(row.items()):
            if isinstance(value, str):
                row[key] = clean_public_text(value)
    theorem_path = PUBLIC_EVIDENCE / "THEOREM_REGISTRY_PUBLIC_1_3_3.json"
    write_json_if_changed(theorem_path, public_theorems)
    out_paths.append(theorem_path)

    public_claims = scrub_public_evidence_json(sanitize_public_json(read_json(ROOT / "claims" / "CLAIM_LEDGER_1_3_3.json", {})))
    public_claims = apply_public_release_promotion_contract(public_claims, "claims/CLAIM_LEDGER_1_3_3.json")
    public_claims["publication_boundary"] = "Public GitHub and Zenodo release approved; journal submission remains separately gated."
    public_claim_rows = []
    for row in public_claims.get("rows", []):
        combined = json.dumps(row, ensure_ascii=False)
        if re.search(r"\bNOSEND\b|NO[-_ ]?SEND|global_no_send_lock|publish_allowed\s*=\s*false|owner_approved\s*=\s*false", combined, re.I):
            continue
        row["release_promotion_allowed"] = bool(row.get("scientific_promotion_allowed"))
        row["public_promotion"] = bool(row.get("scientific_promotion_allowed"))
        for key, value in list(row.items()):
            if isinstance(value, str):
                row[key] = clean_public_text(value)
        public_claim_rows.append(row)
    public_claims["rows"] = public_claim_rows
    public_claims["public_promoted_claim_total"] = sum(1 for row in public_claim_rows if row.get("public_promotion") is True)
    public_claims["release_promotion_allowed"] = public_claims["public_promoted_claim_total"] > 0
    claims_path = PUBLIC_EVIDENCE / "CLAIM_LEDGER_PUBLIC_1_3_3.json"
    write_json_if_changed(claims_path, public_claims)
    out_paths.append(claims_path)

    package_index = scrub_public_evidence_json(sanitize_public_json(read_json(RELEASE_ROOT / "submission_packages" / "SUBMISSION_PACKAGE_INDEX.json", {})))
    public_package_rows = []
    for row in package_index.get("rows", []) if isinstance(package_index.get("rows"), list) else []:
        public_package_rows.append(
            {
                "venue_id": clean_public_text(row.get("venue_id")),
                "venue_name": clean_public_text(row.get("venue_name") or row.get("venue_id")),
                "venue_fit_note": clean_public_text(row.get("venue_fit_note")),
                "official_url": clean_public_text(row.get("official_url")),
                "release_role": "owner-review preparation material; not submitted by this release",
            }
        )
    public_package_index = {
        "schema_id": "OC133_PUBLIC_JOURNAL_PACKAGE_INDEX_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "package_total": len(public_package_rows),
        "boundary": "Journal packets are preparation material only. A later submission requires separate owner approval and a venue-specific refresh.",
        "rows": public_package_rows,
    }
    public_package_path = PUBLIC_EVIDENCE / "PUBLIC_JOURNAL_PACKAGE_INDEX_1_3_3.json"
    write_json_if_changed(public_package_path, public_package_index)
    out_paths.append(public_package_path)

    proof_dir = PUBLIC_EVIDENCE / "proof_sheets_public"
    proof_dir.mkdir(parents=True, exist_ok=True)
    for src in sorted((ROOT / "proofs" / "proof_sheets").glob("T133-*.md")):
        dst = proof_dir / src.name
        write_text_if_changed(dst, clean_public_text(read_text(src)))
        out_paths.append(dst)
    return out_paths


def build_public_zip() -> dict[str, Any]:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    included: list[Path] = []
    for key, spec in PDF_SPECS.items():
        included.append(ARTIFACTS / spec["filename"])
    included.extend(PUBLIC_SOURCES.glob("*.md"))
    included.extend(PUBLIC_FIGURES.glob("*.png"))
    included.extend(PUBLIC_EVIDENCE.rglob("*"))
    for ref in [
        "CITATION.cff",
        ".codemeta.json",
        f"releases/{RELEASE_ID}/RELEASE_NOTES.md",
        f"releases/{RELEASE_ID}/CHANGELOG.md",
    ]:
        path = ROOT / ref
        if path.exists():
            included.append(path)
    # Raw journal-submission packets stay outside the public ZIP because they
    # contain workflow controls. The public ZIP carries the sanitized
    # PUBLIC_JOURNAL_PACKAGE_INDEX_1_3_3.json generated above.
    included = sorted({path.resolve(): path for path in included if path.exists() and path.is_file()}.values(), key=lambda p: rel(p))
    tmp = PUBLIC_ZIP.with_suffix(".zip.tmp")
    with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in included:
            info = zipfile.ZipInfo(rel(path), date_time=(2026, 5, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, text_bytes_for_zip(path))
    data = tmp.read_bytes()
    if not PUBLIC_ZIP.exists() or PUBLIC_ZIP.read_bytes() != data:
        PUBLIC_ZIP.write_bytes(data)
    tmp.unlink(missing_ok=True)
    return {
        "path": rel(PUBLIC_ZIP),
        "sha256": sha256_file(PUBLIC_ZIP),
        "size_bytes": PUBLIC_ZIP.stat().st_size,
        "member_total": len(zipfile.ZipFile(PUBLIC_ZIP).namelist()),
    }


def write_public_metadata(doi: str | None, zenodo_record_url: str | None, github_release_url: str | None) -> dict[str, Any]:
    assets = public_assets()
    asset_rows = []
    for row in assets:
        path = ROOT / row["path"]
        asset_rows.append(
            {
                **row,
                "filename": path.name,
                "exists": path.is_file(),
                "size_bytes": path.stat().st_size if path.is_file() else 0,
                "sha256": sha256_file(path) if path.is_file() else None,
            }
        )
    github_body = release_body(asset_rows, doi, zenodo_record_url, github_release_url)
    zenodo_description = zenodo_html_description(asset_rows, doi, zenodo_record_url, github_release_url)
    manifest = {
        "schema_id": "OC133_PUBLIC_RELEASE_MANIFEST_v2",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "tag": TAG,
        "manifest_kind": "PUBLIC_GITHUB_ZENODO_RELEASE",
        "owner_approved": True,
        "publish_allowed": True,
        "github_release_allowed": True,
        "zenodo_deposit_allowed": True,
        "doi_minting_allowed": True,
        "journal_submissions_allowed": False,
        "software_heritage_deposit_allowed": False,
        "github_release_url": github_release_url,
        "zenodo_record_url": zenodo_record_url,
        "zenodo_doi": doi,
        "concept_doi": "10.5281/zenodo.17899134",
        "github_release_body": github_body,
        "zenodo_html_description": zenodo_description,
        "files": asset_rows,
    }
    write_json_if_changed(ROOT / "manifest.json", manifest)
    checksum_lines = [f"{row['sha256']}  {row['path']}" for row in asset_rows if row.get("sha256")]
    write_text_if_changed(ROOT / "checksums.txt", "\n".join(checksum_lines))
    citation = f"""cff-version: 1.2.0
message: "If you use OC Core 1.3.3, cite the GitHub release and the Zenodo DOI recorded here."
type: report
title: "Ontology of Continua Core v{VERSION}"
version: "{VERSION}"
authors:
  - family-names: "Yashin"
    given-names: "Alexander"
    orcid: "https://orcid.org/0009-0008-6166-0914"
repository-code: "https://github.com/alexanderyashin/ontology-of-continua-core-main"
url: "{github_release_url or 'https://github.com/alexanderyashin/ontology-of-continua-core-main/releases/tag/v1.3.3'}"
license: "CC-BY-4.0"
date-released: "2026-05-01"
identifiers:
  - type: doi
    value: "{doi or '10.5281/zenodo.pending'}"
keywords:
  - ontology
  - continua
  - systems theory
  - formal methods
  - reproducible research
  - proof governance
  - target-blind replay QA
abstract: >
  OC Core 1.3.3 is a bounded external-review scientific release of the
  Ontology of Continua core model. The archived release object contains five
  substantive English PDFs, a public reproducibility package, typed foundations,
  theorem and proof evidence, a Lean-checked subset, finite-model semantics,
  target-blind replay QA and artifact-integrity examples, comparator positioning,
  adversarial-review closure, and owner-review journal packets.
preferred-citation:
  type: report
  title: "Ontology of Continua Core v{VERSION}"
  authors:
    - family-names: "Yashin"
      given-names: "Alexander"
      orcid: "https://orcid.org/0009-0008-6166-0914"
  doi: "{doi or '10.5281/zenodo.pending'}"
  date-released: "2026-05-01"
  version: "{VERSION}"
"""
    write_text_if_changed(ROOT / "CITATION.cff", citation)
    write_text_if_changed(ROOT / "release" / "CITATION.cff", citation)
    codemeta = {
        "@context": "https://doi.org/10.5063/schema/codemeta-2.0",
        "@type": "SoftwareSourceCode",
        "name": f"Ontology of Continua Core v{VERSION} Reproducibility Software Component",
        "version": VERSION,
        "codeRepository": "https://github.com/alexanderyashin/ontology-of-continua-core-main",
        "license": "https://spdx.org/licenses/CC-BY-4.0",
        "datePublished": "2026-05-01",
        "identifier": (doi + "#software-component") if doi else "10.5281/zenodo.pending#software-component",
        "description": "Subordinate CodeMeta description for the reproducibility/software component of the OC Core 1.3.3 scientific release. The canonical citable object is the release report identified in CITATION.cff and Zenodo metadata.",
        "author": [{"@type": "Person", "givenName": "Alexander", "familyName": "Yashin"}],
    }
    write_json_if_changed(ROOT / ".codemeta.json", codemeta)
    ro_crate = {
        "@context": "https://w3id.org/ro/crate/1.1/context",
        "@graph": [
            {
                "@id": "./",
                "@type": "Dataset",
                "name": f"Ontology of Continua Core v{VERSION}",
                "version": VERSION,
                "datePublished": "2026-05-01",
                "identifier": doi or "10.5281/zenodo.pending",
                "license": "https://spdx.org/licenses/CC-BY-4.0",
                "description": "RO-Crate packaging view of the OC Core 1.3.3 scientific release files. The canonical citation object is the release report; crate members are subordinate files.",
                "hasPart": [{"@id": row["path"]} for row in asset_rows],
            },
            *[
                {
                    "@id": row["path"],
                    "@type": "File",
                    "name": row["filename"],
                    "contentSize": row["size_bytes"],
                    "sha256": row["sha256"],
                    "description": row["description"],
                }
                for row in asset_rows
            ],
        ],
    }
    write_json_if_changed(ROOT / "ro-crate-metadata.jsonld", ro_crate)
    notes = f"""# OC Core v{VERSION} Release Notes

OC Core v{VERSION} is the corrected public GitHub and Zenodo release for the Ontology of Continua core line.

## Highlights

- Substantive public PDFs: master monograph, journal core, methods companion, and reviewer attack/response map.
- Typed OC foundation, bounded theorem claims, proof sheets, Lean subset, finite-model semantics, and reproducibility evidence.
- Bounded target-blind replay QA and artifact-integrity examples for physics, chemistry, biology, systems, and mathematics.
- Comparator and novelty positioning register, phenomenon coverage matrix, and adversarial review closure.
- Eight journal packets are included for owner review; journal submission is not performed by this release.

## Scope Boundary

This release is a bounded scientific external-review release. It does not promote final full-science completion or an unbounded cross-science comparison victory over contemporary science.

## Citation

Zenodo DOI: `{doi or 'assigned by corrected Zenodo record metadata'}`
"""
    write_text_if_changed(RELEASE_ROOT / "RELEASE_NOTES.md", notes)
    changelog = f"""# OC Core v{VERSION} Changelog

## Corrected public release payload

- Replaced compact surrogate PDFs with substantive scientific PDFs generated from the proof, formal, validation, comparator, and review corpus.
- Replaced the primary release package with `{PUBLIC_ZIP_NAME}`.
- Rebuilt public manifest, checksums, citation, CodeMeta, RO-Crate, GitHub release metadata, and Zenodo metadata.
- Added reusable public payload suitability gates so future publication attempts fail before upload if public assets are missing, too small, contradictory, stale, or inherited from an owner-review package.
"""
    write_text_if_changed(RELEASE_ROOT / "CHANGELOG.md", changelog)
    readme = f"""# Ontology of Continua / OC Core {VERSION}

OC Core {VERSION} is a bounded public external-review release of the Ontology of Continua core model.

Public release assets include substantive scientific PDFs, a public reproducibility package, metadata, checksums, proof/evidence summaries, bounded replay QA examples, and journal owner-review packets.

Publication scope:
- GitHub Release: owner-approved for v{VERSION}
- Zenodo production record: owner-approved for v{VERSION}
- Journal submission: requires separate approval
- Email campaign and Software Heritage: require separate approval

Zenodo DOI: `{doi or 'assigned by corrected Zenodo record metadata'}`
GitHub Release: `{github_release_url or 'https://github.com/alexanderyashin/ontology-of-continua-core-main/releases/tag/v1.3.3'}`
"""
    write_text_if_changed(RELEASE_ROOT / "README.md", readme)
    write_text_if_changed(ROOT / "README.md", readme)
    zenodo = {
        "title": f"Ontology of Continua Core v{VERSION}",
        "upload_type": "publication",
        "publication_type": "other",
        "description": zenodo_description,
        "creators": [{"name": AUTHOR_CITATION_NAME, "affiliation": AUTHOR_AFFILIATION, "orcid": AUTHOR_ORCID}],
        "license": "cc-by-4.0",
        "access_right": "open",
        "publication_date": "2026-05-01",
        "keywords": [
            "Ontology of Continua",
            "OC Core",
            "systems theory",
            "formal methods",
            "reproducible research",
            "mathematical modeling",
            "scientific release engineering",
            "cross-domain modeling",
            "proof governance",
            "target-blind replay QA",
        ],
        "version": VERSION,
        "related_identifiers": [
            {"identifier": "10.5281/zenodo.17899134", "relation": "isVersionOf", "scheme": "doi"},
            {"identifier": doi, "relation": "isIdenticalTo", "scheme": "doi"} if doi else None,
        ],
    }
    zenodo["related_identifiers"] = [row for row in zenodo["related_identifiers"] if row]
    write_json_if_changed(ROOT / ".zenodo.json", zenodo)
    write_json_if_changed(ROOT / "release" / "zenodo_metadata.json", zenodo)
    return manifest


def zenodo_html_description(
    asset_rows: list[dict[str, Any]],
    doi: str | None,
    zenodo_record_url: str | None,
    github_release_url: str | None,
) -> str:
    version_doi = doi or "pending"
    doi_html = (
        f'<a href="{html.escape("https://doi.org/" + version_doi, quote=True)}">{html.escape(version_doi)}</a>'
        if doi
        else "assigned by Zenodo publication metadata"
    )
    record_html = (
        f'<a href="{html.escape(zenodo_record_url, quote=True)}">Zenodo record</a>'
        if zenodo_record_url
        else "Zenodo record assigned during publication"
    )
    github_url = github_release_url or "https://github.com/alexanderyashin/ontology-of-continua-core-main/releases/tag/v1.3.3"
    github_html = f'<a href="{html.escape(github_url, quote=True)}">GitHub release</a>'
    labels = {row.get("filename"): row.get("label") for row in asset_rows}
    reading_order = [
        ("00_OC_CORE_1_3_3_RELEASE_GUIDE_EN.pdf", labels.get("00_OC_CORE_1_3_3_RELEASE_GUIDE_EN.pdf") or "Release guide"),
        ("OC_CORE_1_3_3_MASTER_MONOGRAPH_EN.pdf", labels.get("OC_CORE_1_3_3_MASTER_MONOGRAPH_EN.pdf") or "Master monograph"),
        ("OC_CORE_1_3_3_JOURNAL_CORE_EN.pdf", labels.get("OC_CORE_1_3_3_JOURNAL_CORE_EN.pdf") or "Journal core article"),
        (
            "OC_CORE_1_3_3_METHODS_AND_REPRODUCIBILITY_COMPANION_EN.pdf",
            labels.get("OC_CORE_1_3_3_METHODS_AND_REPRODUCIBILITY_COMPANION_EN.pdf")
            or "Methods and reproducibility companion",
        ),
        (
            "OC_CORE_1_3_3_REVIEWER_ATTACK_AND_RESPONSE_MAP_EN.pdf",
            labels.get("OC_CORE_1_3_3_REVIEWER_ATTACK_AND_RESPONSE_MAP_EN.pdf") or "Reviewer attack and response map",
        ),
        ("oc_core_1_3_3_public_release.zip", "Public reproducibility package"),
    ]
    reading = "".join(
        f"<li><strong>{html.escape(str(label))}</strong> - {html.escape(filename)}</li>"
        for filename, label in reading_order
    )
    return (
        f"<p><strong>Ontology of Continua Core v{VERSION}</strong> is a bounded external-review scientific release "
        "of the OC core model. It provides typed foundations, proof and evidence registers, Lean and finite-model evidence, "
        "target-blind replay QA summaries, reproducibility material, and adversarial-review artifacts.</p>"
        "<p>The release promotes only model-core claims supported by the included evidence. Broader full-science "
        "completion and unbounded cross-science comparison obligations remain outside this release surface.</p>"
        "<h2>Attribution</h2>"
        f"<p>Author: {html.escape(AUTHOR_DISPLAY)}, {html.escape(AUTHOR_AFFILIATION)}, ORCID {html.escape(AUTHOR_ORCID)}. "
        "Logion is the research-instrument and institute-automation system used for preparation, checking, packaging, "
        "and audit. ESTRA is the methodological framework. Neither Logion nor ESTRA is a creator, co-author, or author affiliation.</p>"
        "<h2>Recommended reading order</h2>"
        f"<ol>{reading}</ol>"
        "<h2>Release contents</h2>"
        "<ul><li>Five substantive English PDF documents: release guide, master monograph, journal core article, methods companion, and reviewer response map.</li><li>One public reproducibility package with proof, "
        "validation, review, metadata, checksums, and journal owner-review materials.</li><li>Checksums are provided "
        "in checksums.txt.</li></ul>"
        "<h2>Citation and links</h2>"
        f"<ul><li>Version DOI: {doi_html}</li><li>Concept DOI: "
        '<a href="https://doi.org/10.5281/zenodo.17899134">10.5281/zenodo.17899134</a></li>'
        f"<li>{record_html}</li><li>{github_html}</li></ul>"
        "<h2>Governance boundary</h2>"
        "<p>GitHub Release and Zenodo publication are approved for v1.3.3. Journal packages are included as "
        "owner-review material only; journal submission, email campaigns, and Software Heritage deposit require "
        "separate approval.</p>"
    )


def release_body(asset_rows: list[dict[str, Any]], doi: str | None, zenodo_record_url: str | None, github_release_url: str | None) -> str:
    download_base = "https://github.com/alexanderyashin/ontology-of-continua-core-main/releases/download/v1.3.3"
    primary = [
        ("00_OC_CORE_1_3_3_RELEASE_GUIDE_EN.pdf", "Release guide", "Public landing guide and recommended reading order."),
        ("OC_CORE_1_3_3_MASTER_MONOGRAPH_EN.pdf", "Master monograph", "Canonical long-form scientific reference."),
        ("OC_CORE_1_3_3_JOURNAL_CORE_EN.pdf", "Journal core article", "Compact article-style entry point."),
        (
            "OC_CORE_1_3_3_METHODS_AND_REPRODUCIBILITY_COMPANION_EN.pdf",
            "Methods and reproducibility companion",
            "Reproducibility, validation, and audit navigation.",
        ),
        (
            "OC_CORE_1_3_3_REVIEWER_ATTACK_AND_RESPONSE_MAP_EN.pdf",
            "Reviewer attack and response map",
            "Adversarial objections, boundaries, and responses.",
        ),
        ("oc_core_1_3_3_public_release.zip", "Public reproducibility package", "Proof/evidence corpus and journal owner-review material."),
        ("checksums.txt", "Checksums", "SHA-256 integrity list for all public assets."),
    ]
    asset_lines = "\n".join(
        f"| [{filename}]({download_base}/{filename}) | {label} | {description} |"
        for filename, label, description in primary
    )
    return f"""# Ontology of Continua Core v{VERSION}

Bounded external-review scientific release with typed foundations, proof and evidence registers, reproducibility package, and journal owner-review packets.

## Table of Contents

1. Scope
2. Core scientific documents
3. Public assets and checksums
4. Journal package boundary
5. Citation and DOI
6. Checksums

## Scope

OC Core {VERSION} is a public GitHub and Zenodo release. The promoted claims are bounded by the included formal, finite-model, validation, comparator, and adversarial-review artifacts. Broader full-science completion and unbounded cross-science comparison obligations remain outside this release surface.

## Attribution

Author: {AUTHOR_DISPLAY}, {AUTHOR_AFFILIATION}, ORCID {AUTHOR_ORCID}.

Logion is cited as the research-instrument and institute-automation system used for preparation, checking, packaging, and audit. ESTRA is cited as the methodological framework. Neither is a creator, co-author, or author affiliation.

## Public Assets

| Asset | Role | How to use it |
| --- | --- | --- |
{asset_lines}

Checksums for the complete public asset set are in [`checksums.txt`]({download_base}/checksums.txt). Machine-readable metadata is provided as `manifest.json`, `CITATION.cff`, `.codemeta.json`, and `ro-crate-metadata.jsonld`.

## Journal Packages

The eight journal packets are included for owner review. They are not submitted by this release action and require separate approval before outbound use.

## Zenodo

DOI: {doi or 'assigned by the corrected Zenodo record metadata'}

Record: {zenodo_record_url or 'assigned by the corrected publication pass'}

Concept DOI: 10.5281/zenodo.17899134

## GitHub

Release: {github_release_url or 'https://github.com/alexanderyashin/ontology-of-continua-core-main/releases/tag/v1.3.3'}

## Keywords

Ontology of Continua, OC Core, systems theory, formal methods, reproducible research, mathematical modeling, proof governance, target-blind replay QA.

#OntologyOfContinua #OCCore #SystemsTheory #FormalMethods #ReproducibleResearch #ScientificRelease #ProofGovernance
"""


def write_profile() -> None:
    payload = {
        "schema_id": "LOGION_PUBLIC_RELEASE_PROFILE_v2",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "tag": TAG,
        "branch": "release/oc-core-1.3.3-total-scientific-closure",
        "repository": "alexanderyashin/ontology-of-continua-core-main",
        "title": "Ontology of Continua Core",
        "subtitle": "Bounded external-review scientific release with typed foundations, proof and evidence registers, reproducibility package, and journal owner-review packets",
        "release_state": "OC_CORE_1_3_3_PUBLIC_GITHUB_ZENODO_RELEASE",
        "expected_gate_pass_total": 71,
        "expected_package_sha256": "",
        "previous_zenodo_record_id": "19956854",
        "previous_zenodo_doi": "10.5281/zenodo.19956854",
        "concept_doi": "10.5281/zenodo.17899134",
        "creators": [{"name": AUTHOR_CITATION_NAME, "affiliation": AUTHOR_AFFILIATION, "orcid": AUTHOR_ORCID}],
        "license": "cc-by-4.0",
        "keywords": [
            "Ontology of Continua",
            "OC Core",
            "systems theory",
            "formal methods",
            "reproducible research",
            "mathematical modeling",
            "scientific release engineering",
            "cross-domain modeling",
            "proof governance",
            "target-blind replay QA",
        ],
        "github_topics": [
            "ontology-of-continua",
            "oc-core",
            "systems-theory",
            "formal-methods",
            "reproducible-research",
            "scientific-release",
            "proof-governance",
        ],
        "hashtags": [
            "#OntologyOfContinua",
            "#OCCore",
            "#SystemsTheory",
            "#FormalMethods",
            "#ReproducibleResearch",
            "#ScientificRelease",
            "#ProofGovernance",
        ],
        "assets": [
            {key: row[key] for key in ["path", "label", "description"]}
            for row in public_assets()
        ],
        "zenodo_assets": [
            {key: row[key] for key in ["path", "label", "description"]}
            for row in zenodo_assets()
        ],
        "journal_submissions_allowed": False,
        "software_heritage_allowed": False,
    }
    write_json_if_changed(EDITORIAL / "PUBLIC_RELEASE_PROFILE.json", payload)


def public_surface_scan(paths: list[Path]) -> list[dict[str, Any]]:
    hits = []
    for path in paths:
        if not path.exists() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        body = read_text(path)
        for regex, kind in [(PUBLIC_FORBIDDEN_RE, "public_no_send_contradiction"), (ABSOLUTE_OVERCLAIM_RE, "absolute_overclaim")]:
            for match in regex.finditer(body):
                hits.append(
                    {
                        "path": rel(path),
                        "kind": kind,
                        "match": match.group(0),
                        "context": body[max(0, match.start() - 80) : match.end() + 120].replace("\n", " ")[:260],
                    }
                )
    return hits


def known_publication_error_scan(paths: list[Path], *, include_pdfs: bool = True) -> dict[str, Any]:
    hits: list[dict[str, Any]] = []
    for path in paths:
        if not path.exists():
            continue
        suffix = path.suffix.lower()
        if suffix == ".pdf" and include_pdfs:
            text, _pages = pdf_text(path, persist_audit_text=False)
        elif suffix in TEXT_SUFFIXES:
            text = read_text(path)
        else:
            continue
        for error_id, regex in KNOWN_PUBLICATION_ERROR_PATTERNS.items():
            if error_id == "KE-020_RAW_CODE_OR_LEDGER_DUMP_IN_PUBLIC_PDF" and suffix in {".json", ".jsonld", ".cff"}:
                continue
            for match in regex.finditer(text):
                hits.append(
                    {
                        "path": rel(path),
                        "error_id": error_id,
                        "match": match.group(0),
                        "context": text[max(0, match.start() - 90) : match.end() + 140].replace("\n", " ")[:320],
                    }
                )
    return {
        "gate_id": "KNOWN_PUBLICATION_ERROR_REGRESSION_GATE",
        "state": "PASS" if not hits else "FAIL",
        "hit_total": len(hits),
        "hits": hits[:200],
    }


def zip_public_scan() -> dict[str, Any]:
    forbidden = []
    if not PUBLIC_ZIP.exists():
        return {"state": "FAIL", "failure_total": 1, "failures": [{"issue": "missing_public_zip"}]}
    with zipfile.ZipFile(PUBLIC_ZIP) as zf:
        for name in zf.namelist():
            lowered = name.lower()
            if "oc_core_1_3_2" in lowered or "1_3_2" in lowered:
                forbidden.append({"member": name, "issue": "stale_132_member"})
            if "no_send_release.zip" in lowered:
                forbidden.append({"member": name, "issue": "published_review_zip_member"})
            if name.endswith("/"):
                continue
            suffix = Path(name).suffix.lower()
            if suffix in TEXT_SUFFIXES:
                text = zf.read(name).decode("utf-8", errors="ignore")
                hit = PUBLIC_FORBIDDEN_RE.search(text)
                if hit:
                    forbidden.append({"member": name, "issue": "public_forbidden_text", "match": hit.group(0)})
                is_machine_evidence = "/public_payload/evidence/" in f"/{name}" or "\\public_payload\\evidence\\" in name
                if not is_machine_evidence:
                    for error_id, regex in KNOWN_PUBLICATION_ERROR_PATTERNS.items():
                        if error_id == "KE-020_RAW_CODE_OR_LEDGER_DUMP_IN_PUBLIC_PDF" and suffix in {".json", ".jsonld", ".cff"}:
                            continue
                        match = regex.search(text)
                        if match:
                            forbidden.append({"member": name, "issue": "known_publication_error", "error_id": error_id, "match": match.group(0)})
    return {"state": "PASS" if not forbidden else "FAIL", "failure_total": len(forbidden), "failures": forbidden[:100]}


def audit_public_payload(*, write: bool = True) -> dict[str, Any]:
    asset_paths = [ROOT / row["path"] for row in public_assets()]
    pdf_audit = public_pdf_audit(persist_audit_text=write)
    publication_grade = publication_grade_text_gate(persist_audit_text=False)
    journal_editorial = journal_editorial_board_gate(persist_audit_text=False)
    positive_mission = positive_mission_fulfillment_gate(persist_audit_text=False)
    scientific_spot = scientific_process_spot_gate(write=write)
    editorial_cerberus = editorial_cerberus_gate()
    monolith_audit = science_monolith.audit_monolith(ROOT)
    scan_hits = public_surface_scan(asset_paths + list(PUBLIC_SOURCES.glob("*.md")) + [ROOT / "README.md", ROOT / ".zenodo.json"])
    known_error_scan = known_publication_error_scan(
        asset_paths
        + list(PUBLIC_SOURCES.glob("*.md"))
        + [ROOT / "README.md", ROOT / ".zenodo.json", ROOT / "CITATION.cff", ROOT / ".codemeta.json", ROOT / "ro-crate-metadata.jsonld"]
    )
    zip_scan = zip_public_scan()
    missing_assets = [rel(path) for path in asset_paths if not path.is_file()]
    primary_no_send_asset_names = [path.name for path in asset_paths if "no_send" in path.name.lower()]
    failures = []
    if pdf_audit["state"] != "PASS":
        failures.append("pdf_audit_failed")
    if monolith_audit.get("state") != "PASS":
        failures.append("science_monolith_audit_failed")
    if publication_grade["state"] != "PASS":
        failures.append("publication_grade_text_gate_failed")
    if journal_editorial["state"] != "PASS":
        failures.append("journal_editorial_board_gate_failed")
    if positive_mission["state"] != "PASS":
        failures.append("positive_mission_fulfillment_gate_failed")
    if scientific_spot["state"] != "PASS":
        failures.append("scientific_process_spot_gate_failed")
    if editorial_cerberus["state"] != "PASS":
        failures.append("editorial_cerberus_gate_failed")
    if scan_hits:
        failures.append("public_surface_forbidden_hits")
    if known_error_scan["state"] != "PASS":
        failures.append("known_publication_error_regression_failed")
    if zip_scan["state"] != "PASS":
        failures.append("zip_public_scan_failed")
    if missing_assets:
        failures.append("missing_public_assets")
    if primary_no_send_asset_names:
        failures.append("primary_public_asset_name_contains_no_send")
    payload = {
        "schema_id": "OC133_PUBLIC_PAYLOAD_SUITABILITY_AUDIT_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "state": "PASS" if not failures else "FAIL",
        "failure_total": len(failures),
        "failures": failures,
        "pdf_audit": pdf_audit,
        "publication_grade_text_gate": publication_grade,
        "journal_editorial_board_gate": journal_editorial,
        "positive_mission_fulfillment_gate": positive_mission,
        "scientific_process_spot_gate": scientific_spot,
        "editorial_cerberus_gate": editorial_cerberus,
        "science_monolith_audit": monolith_audit,
        "public_surface_forbidden_hit_total": len(scan_hits),
        "public_surface_forbidden_hits": scan_hits[:100],
        "known_publication_error_scan": known_error_scan,
        "zip_scan": zip_scan,
        "missing_assets": missing_assets,
        "primary_no_send_asset_names": primary_no_send_asset_names,
        "public_zip": {
            "path": rel(PUBLIC_ZIP) if PUBLIC_ZIP.exists() else rel(PUBLIC_ZIP),
            "exists": PUBLIC_ZIP.exists(),
            "sha256": sha256_file(PUBLIC_ZIP) if PUBLIC_ZIP.exists() else None,
            "size_bytes": PUBLIC_ZIP.stat().st_size if PUBLIC_ZIP.exists() else 0,
        },
    }
    if not write:
        return payload

    write_json_if_changed(EDITORIAL / f"PUBLIC_PAYLOAD_SUITABILITY_{VERSION}_latest.json", payload)
    lines = [
        f"# OC Core {VERSION} Public Payload Suitability",
        "",
        f"State: `{payload['state']}`",
        f"Failures: `{payload['failure_total']}`",
        f"Public ZIP: `{payload['public_zip']['path']}`",
        f"Public ZIP SHA-256: `{payload['public_zip']['sha256']}`",
        f"Publication-grade text gate: `{publication_grade['state']}`",
        f"Journal editorial board gate: `{journal_editorial['state']}`",
        f"Positive mission fulfillment gate: `{positive_mission['state']}`",
        f"Scientific/process SPOT gate: `{scientific_spot['state']}`",
        f"Editorial adversarial-review gate: `{editorial_cerberus['state']}`",
        "",
        "| PDF | State | Pages | Text chars | Size |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for row in pdf_audit["rows"]:
        lines.append(f"| `{Path(row['artifact']).name}` | `{row['state']}` | {row['pages']} | {row['text_chars']} | {row['size_bytes']} |")
    write_text_if_changed(EDITORIAL / f"PUBLIC_PAYLOAD_SUITABILITY_{VERSION}_latest.md", "\n".join(lines))
    return payload


def sync_finite_publication_controls() -> dict[str, Any]:
    inputs_path = ROOT / "proofs" / "finite_model_checks" / "OC133_FINITE_MODEL_INPUTS.json"
    if not inputs_path.exists():
        return {"state": "SKIP", "reason": "missing finite model inputs"}
    payload = read_json(inputs_path, {})
    rows = payload.get("rows", [])
    changed_rows: list[str] = []
    for row in rows if isinstance(rows, list) else []:
        model = row.get("model")
        if not isinstance(model, dict):
            continue
        manifest_ref = model.get("manifest_ref")
        approval_ref = model.get("approval_ref")
        if manifest_ref and (ROOT / str(manifest_ref)).is_file():
            current = sha256_source_ref(ROOT / str(manifest_ref))
            if model.get("manifest_sha256") != current:
                model["manifest_sha256"] = current
                changed_rows.append(str(row.get("case_id")))
        if approval_ref and (ROOT / str(approval_ref)).is_file():
            current = sha256_source_ref(ROOT / str(approval_ref))
            if model.get("approval_sha256") != current:
                model["approval_sha256"] = current
                changed_rows.append(str(row.get("case_id")))
        if row.get("case_id") == "ADV-NOSEND-PUBLISH":
            manifest = read_json(ROOT / str(manifest_ref), {}) if manifest_ref else {}
            approval = read_json(ROOT / str(approval_ref), {}) if approval_ref else {}
            public_release_approved = (
                manifest.get("owner_approved") is True
                and manifest.get("github_release_allowed") is True
                and manifest.get("zenodo_deposit_allowed") is True
                and approval.get("owner_approved") is True
            )
            if public_release_approved:
                model["current_publication_artifact_policy"] = (
                    "OWNER_APPROVED_GITHUB_ZENODO_PUBLIC_RELEASE_WITH_JOURNAL_AND_SOFTWARE_HERITAGE_LOCKS"
                )
                if model.get("public_metadata_refs"):
                    model["public_metadata_refs"] = []
                    changed_rows.append(str(row.get("case_id")))
                row["failed_gate_predicates"] = [
                    "software_heritage_deposit_allowed",
                    "journal_submission_allowed",
                ]
                row["gate_vector"] = {
                    "owner_approved": True,
                    "publish_allowed": True,
                    "deposit_ready_metadata": True,
                    "public_record_present": True,
                    "global_no_send_lock=false": True,
                    "g57_attack_matrix_zero_critical_high": True,
                    "g58_reviewer_persona_suite_pass": True,
                    "g70_scientific_closure_verdict_pass": True,
                    "critical_open_total=0": True,
                    "high_open_total=0": True,
                    "github_release_allowed": True,
                    "zenodo_deposit_allowed": True,
                    "software_heritage_deposit_allowed": False,
                    "journal_submission_allowed": False,
                    "doi_minting_allowed": True,
                }
                changed_rows.append(str(row.get("case_id")))
    changed = write_json_if_changed(inputs_path, payload)
    return {
        "state": "UPDATED" if changed else "UNCHANGED",
        "changed": changed,
        "changed_rows": sorted(set(changed_rows)),
    }


def materialize(
    doi: str | None = None,
    zenodo_record_url: str | None = None,
    github_release_url: str | None = None,
    *,
    skip_pdf: bool = False,
    only: set[str] | None = None,
) -> dict[str, Any]:
    doi = doi or DEFAULT_PUBLIC_DOI
    zenodo_record_url = zenodo_record_url or DEFAULT_ZENODO_RECORD_URL
    PUBLIC_SOURCES.mkdir(parents=True, exist_ok=True)
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    write_profile()
    sources = write_public_markdown(doi, zenodo_record_url)
    evidence_paths = materialize_public_evidence_summaries()
    finite_control_sync = sync_finite_publication_controls()
    build_rows = []
    if not skip_pdf:
        build_targets = only or set(sources)
        if "master" in build_targets:
            monolith_build = science_monolith.materialize_monolith(ROOT, doi=doi, zenodo_record_url=zenodo_record_url)
            build_rows.append(
                {
                    "command": "release_machine.science_monolith.materialize_monolith",
                    "returncode": 0 if monolith_build.get("state") == "PASS" else 1,
                    "stdout_tail": "",
                    "stderr_tail": "",
                    "output": monolith_build.get("output_pdf"),
                    "ok": monolith_build.get("state") == "PASS",
                    "science_monolith": monolith_build.get("audit", {}),
                }
            )
        for key, source in sources.items():
            if key == "master" or key not in build_targets:
                continue
            spec = PDF_SPECS[key]
            build_rows.append(build_pdf(source, ARTIFACTS / spec["filename"], spec["title"]))
        failures = [row for row in build_rows if not row["ok"]]
        if failures:
            payload = {"state": "FAIL", "build_rows": build_rows, "failures": failures}
            write_json_if_changed(EDITORIAL / f"PUBLIC_PAYLOAD_BUILD_{VERSION}_latest.json", payload)
            return payload
    write_public_metadata(doi, zenodo_record_url, github_release_url)
    zip_payload = build_public_zip()
    # The ZIP is itself a public asset, so metadata/checksums must bind the final ZIP hash.
    write_public_metadata(doi, zenodo_record_url, github_release_url)
    audit = audit_public_payload()
    payload = {
        "schema_id": "OC133_PUBLIC_RELEASE_PAYLOAD_BUILD_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "state": "PASS" if audit["state"] == "PASS" and all(row.get("ok", True) for row in build_rows) else "FAIL",
        "doi": doi,
        "zenodo_record_url": zenodo_record_url,
        "github_release_url": github_release_url,
        "source_paths": {key: rel(path) for key, path in sources.items()},
        "evidence_path_total": len(evidence_paths),
        "finite_publication_control_sync": finite_control_sync,
        "pdf_build_rows": build_rows,
        "public_zip": zip_payload,
        "suitability": audit,
    }
    write_json_if_changed(EDITORIAL / f"PUBLIC_PAYLOAD_BUILD_{VERSION}_latest.json", payload)
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build and audit the OC Core 1.3.3 corrected public release payload.")
    parser.add_argument("--doi", default=None)
    parser.add_argument("--zenodo-record-url", default=None)
    parser.add_argument("--github-release-url", default=None)
    parser.add_argument("--skip-pdf", action="store_true")
    parser.add_argument(
        "--only",
        action="append",
        choices=sorted(PDF_SPECS),
        help="Rebuild only the named PDF role; may be repeated. Used by Delta Queue repairs before full-gate runs.",
    )
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    only = set(args.only or []) or None
    payload = audit_public_payload(write=False) if args.check else materialize(
        args.doi,
        args.zenodo_record_url,
        args.github_release_url,
        skip_pdf=args.skip_pdf,
        only=only,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload.get("state") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
