from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from assemble_oc_core_release_package import (
    ACKNOWLEDGEMENT_NAMES,
    AUTHOR_DISPLAY,
    AUTHOR_ORCID,
    CONCEPT_DOI,
    DEDICATION_TEXT,
    FRONTMATTER_REQUIRED_SECTIONS,
    READER_HEADING_MAX_CHARS,
    R008_REVISION,
    R008_TRANSLATOR_STATUS,
    R009_REVISION,
    R009_TRANSLATOR_STATUS,
    R010_REVISION,
    R010_TRANSLATOR_STATUS,
    R011_REVISION,
    R011_TRANSLATOR_STATUS,
    R012_REVISION,
    R012_TRANSLATOR_STATUS,
    R013_REVISION,
    R013_TRANSLATOR_STATUS,
    TEXT_ARTIFACTS,
    assembly_paths,
    artifact_title,
)
from oc_core_release_assembly_lib import ROOT, artifact_hash, read_json, stable_json, validation_result

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from release_machine.versioning import version_from_release_id


CYRILLIC_RE = re.compile(r"[\u0400-\u04FF]")
FORBIDDEN_TEXT_RE = re.compile(
    r"("
    r"no_send|publish_allowed\s*[:=]\s*false|owner_approved\s*[:=]\s*false|"
    r"github release action|zenodo deposit action|tag movement|doi minting action|"
    r"route sheet|control sheet|raw ledger|checksum wall|"
    r"\bTODO\b|\bTBD\b|"
    r"бляд|хуй|ебан|ёбан|сука|мудак"
    r")",
    re.IGNORECASE,
)
LOCAL_PATH_RE = re.compile("|".join([r"C:" + r"\\Users\\", r"file:" + r"//", r"estra-" + r"private-work"]), re.IGNORECASE)
MISSING_CHAR_RE = re.compile(r"Missing character", re.IGNORECASE)
FRONTMATTER_BODY_LEAK_RE = re.compile(
    r"\b(Define|Bind|State limits and falsifiers for|Synthesize)\s+"
    r"(Title Page|Dedication|Abstract|Keywords|Citation, DOI|Table of Contents|List of Figures|Symbols|Author, Instrument)",
    re.IGNORECASE,
)
IDENTITY_CLUTTER_RE = re.compile(r"\b(Version DOI|Zenodo Record|Zenodo record|GitHub Release|GitHub release)\b", re.IGNORECASE)
VISIBLE_RECOVERY_REVISION_RE = re.compile(r"\brevision\s+recovery_r\d+\b|\brecovery_r\d+\b", re.IGNORECASE)
R006_INTERNAL_BLOCK_RE = re.compile(
    r"\b(This block presents|Reader Orientation|Complete Scientific Argument|Scientific Closure|"
    r"list of figures|list of tables)\b",
    re.IGNORECASE,
)
R006_READER_IMPERATIVE_RE = re.compile(
    r"(?m)(?:^|[.!?]\s+)(?:Begin with|Read the|Use the model chapters as)\b|\bshould read\b"
)
R007_INSTRUCTION_PROSE_RE = re.compile(
    r"\b("
    r"payoff|route sheet|must teach|purpose and role|construction and order|machine register|"
    r"current maturity vector|this section is included so|teaching obligation|reader should learn|"
    r"Scientific Reading Protocol|Evidence Coverage Map|Figure Route and Design Logic|"
    r"Manuscript-quality rule|Corpus coverage gate|Evidence coverage gate|Editorial adversarial-review gate|"
    r"Release payoff|Model integration payoff|Proof integration payoff|Empirical integration payoff|"
    r"Prior-art payoff|Phenomenon payoff|Editorial payoff"
    r")\b",
    re.IGNORECASE,
)
R007_PAGE17_LEAK_RE = re.compile(
    r"\b(Evidence Coverage Map|Scientific Reading Protocol|Audience\.|Purpose\.|Construction\.|Didactic rule\.|"
    r"Figure Route and Design Logic|Model integration payoff|machine register)\b",
    re.IGNORECASE,
)
READER_SURFACE_CONTROL_RE = re.compile(
    r"review-space artifact is assembled|not a GitHub or Zenodo publication action|"
    r"terminal text contracts|deterministic transition rules|generated terminal prose",
    re.IGNORECASE,
)
BODY_MARKER_RE = re.compile(r"(^|\n)#\s+Body\b", re.IGNORECASE)
MARKDOWN_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
FORBIDDEN_VISIBLE_HEADING_RE = re.compile(
    r"^(?:\d+(?:\.\d+)*\s+)?(Body\b|Block\s+\d+\b|Define\b|Bind\b|Synthesize\b|"
    r"State limits(?: and falsifiers for)?\b)",
    re.IGNORECASE,
)
TOC_MARKER_RE = re.compile(r"(?m)^\s*(?:#+\s*)?Table of Contents(?:\s+\{[^}]+\})?\s*$")
FLAT_TOC_CONTINUATION_RE = re.compile(r"Additional sections continue in document order", re.IGNORECASE)
TECHNICAL_TOC_ENTRY_RE = re.compile(r"(?m)^\s*\d+\.\s+Block\s+\d+\s*:", re.IGNORECASE)
TOC_PROSE_LEAK_RE = re.compile(r"introduced here|reader-facing obligation|evidential burden|falsifier, negative control", re.IGNORECASE)
TITLE_PAGE_BODY_MARKER_RE = re.compile(
    r"\b(Dedication|Acknowledgements|Abstract|Reader Contract|Table of Contents|Reader Orientation|The Continuum Problem|Body|Block\s+\d+)\b",
    re.IGNORECASE,
)
PUBLIC_READER_INTERNAL_RE = re.compile(r"\b(Logion|ESTRA)\b", re.IGNORECASE)
PUBLICATION_TECHNICAL_RE = re.compile(
    r"\b("
    r"L10C?|terminal text contracts?|generated terminal prose|definition_model|"
    r"introduced here as a reader-facing obligation|Additional sections continue|"
    r"Block\s+\d+"
    r")",
    re.IGNORECASE,
)
TECHNICAL_PUBLIC_HEADING_RE = re.compile(r"\b(?:T133|OC133)[-_][A-Z0-9_-]+\b", re.IGNORECASE)
TITLE_PAGE_FINDING_KINDS = {
    "pdf_title_page_missing_metadata",
    "pdf_title_page_not_primary",
    "publication_title_page_missing_dedication",
    "publication_title_page_internal_instrument_leak",
}
TOC_FORM_FINDING_KINDS = {
    "frontmatter_form_toc_count_violation",
    "frontmatter_form_flat_toc_continuation",
    "frontmatter_form_technical_toc_entry",
    "pdf_form_toc_count_violation",
    "pdf_toc_layout_line_too_long",
    "pdf_toc_layout_page_number_collision",
    "pdf_toc_layout_prose_leak",
    "pdf_toc_page_cap_violation",
    "pdf_toc_hierarchy_technical_entry",
}
HEADING_FORM_FINDING_KINDS = {
    "frontmatter_forbidden_heading_prefix",
    "frontmatter_heading_trailing_comma",
    "frontmatter_heading_too_long",
    "pdf_forbidden_heading_prefix",
    "pdf_heading_trailing_comma",
    "pdf_heading_too_long",
}
ACKNOWLEDGEMENTS_FINDING_KINDS = {
    "publication_acknowledgements_missing",
    "publication_acknowledgements_too_short",
    "publication_acknowledgements_missing_reviewers_critics",
    "publication_acknowledgements_missing_boundary",
    "publication_acknowledgements_missing_name",
}
ABSTRACT_FINDING_KINDS = {
    "publication_abstract_missing",
    "publication_abstract_too_short",
    "publication_abstract_missing_depth_anchor",
}
RELEASE_DELTA_FINDING_KINDS = {
    "publication_release_delta_missing",
    "publication_release_delta_order_violation",
    "publication_release_delta_missing_anchor",
}
READER_CONTRACT_FINDING_KINDS = {
    "publication_reader_contract_missing",
    "publication_reader_contract_too_short",
    "publication_reader_contract_missing_orientation_anchor",
    "publication_reader_routes_missing_group",
}
FRONTMATTER_IDENTITY_FINDING_KINDS = {
    "publication_frontmatter_identity_clutter",
    "publication_title_page_date_stale",
    "publication_concept_doi_occurrence_violation",
    "publication_keywords_not_backmatter",
}
LAYOUT_FINDING_KINDS = {
    "publication_toc_visual_hierarchy_missing",
    "publication_layout_standard_missing",
}
APPENDIX_FINDING_KINDS = {
    "publication_appendix_letter_only_title",
}
FIGURE_FINDING_KINDS = {
    "publication_inline_figure_distribution_too_low",
    "publication_figure_atlas_still_included",
    "publication_r012_figure_spec_missing",
    "publication_r012_geometry_failed",
    "publication_r012_rendered_bbox_failed",
    "publication_r012_label_collision_failed",
    "publication_r012_semantic_visual_failed",
    "publication_r012_k_hierarchy_visual_failed",
    "publication_r012_continuum_visual_failed",
    "publication_r012_caption_argument_failed",
    "publication_r012_visual_cockpit_failed",
}
TABLE_FINDING_KINDS = {
    "publication_r013_table_spec_missing",
    "publication_r013_compiled_table_coverage_failed",
    "publication_r013_table_layout_standard_failed",
    "publication_r013_table_geometry_failed",
    "publication_r013_rendered_table_bbox_failed",
    "publication_r013_table_text_collision_failed",
    "publication_r013_table_edge_clipping_failed",
    "publication_r013_table_caption_argument_failed",
    "publication_r013_table_semantic_anchor_failed",
    "publication_r013_table_cockpit_failed",
}
BIBLIOGRAPHY_FINDING_KINDS = {
    "publication_bibliography_depth_too_low",
    "publication_bibliography_verified_shortfall",
}
PREDICTION_FINDING_KINDS = {
    "publication_prediction_falsifiability_anchor_missing",
    "publication_tex_reference_leak",
}
CONTENT_RICHNESS_FINDING_KINDS = {
    "publication_body_source_not_corpus",
    "publication_body_source_not_curated_payload",
    "publication_master_missing_richness_anchor",
}
TECHNICAL_PROSE_FINDING_KINDS = {
    "publication_reader_internal_instrument_leak",
    "publication_technical_prose_leak",
}
R006_FINDING_KINDS = {
    "publication_visible_recovery_revision",
    "publication_title_identity_policy_violation",
    "publication_release_policy_missing_anchor",
    "publication_release_policy_too_short",
    "publication_reader_routes_tone_imperative",
    "publication_reader_orientation_duplicate",
    "publication_internal_block_metadata_leak",
    "publication_figure_table_list_visible",
    "publication_didactic_spine_order_violation",
    "publication_motivation_too_short",
    "publication_k_primer_missing",
    "publication_duplicate_structure_section",
}
R007_FINDING_KINDS = {
    "publication_instruction_prose_leak",
    "publication_page17_internal_leak",
    "publication_translation_missing",
    "publication_all_reader_pdf_translation_missing",
    "publication_v_model_trace_missing",
    "publication_ollama_governance_trace_missing",
    "publication_ollama_governance_bypass",
    "publication_k_hierarchy_figure_incomplete",
    "publication_figure_pedagogy_missing",
    "publication_diagram_label_collision_risk",
}
R008_FINDING_KINDS = {
    "publication_common_llm_service_missing",
    "publication_llm_service_governance_trace_missing",
    "publication_llm_service_cadence_trace_missing",
    "publication_llm_service_thermal_monitor_missing",
    "publication_llm_service_bypass",
    "publication_llm_service_vmodel_missing",
    "publication_local_ollama_capability_unreported",
    "publication_r008_translation_missing",
}
R009_FINDING_KINDS = {
    "publication_editorial_llm_queue_not_done",
    "publication_editorial_packet_coverage_missing",
    "publication_actual_ollama_invocation_missing",
    "publication_until_done_missing",
    "publication_cooldown_resume_missing",
    "publication_v_model_completion_missing",
    "publication_local_capability_exhaustion_invalid",
}
R011_FINDING_KINDS = {
    "publication_journal_requirements_trace_missing",
    "publication_release_spot_incomplete",
    "publication_bounded_synthesis_invalid",
    "publication_source_gap_open",
    "publication_venue_projection_missing",
    "publication_submission_component_missing",
    "publication_journal_format_compliance_missing",
    "publication_internal_leak_in_journal_projection",
    "publication_fabrication_risk_open",
    "publication_scientific_journal_readiness_missing",
}
R012_FINDING_KINDS = {
    "publication_r012_figure_spec_missing",
    "publication_r012_geometry_failed",
    "publication_r012_rendered_bbox_failed",
    "publication_r012_label_collision_failed",
    "publication_r012_semantic_visual_failed",
    "publication_r012_k_hierarchy_visual_failed",
    "publication_r012_continuum_visual_failed",
    "publication_r012_caption_argument_failed",
    "publication_r012_visual_cockpit_failed",
}
R013_FINDING_KINDS = TABLE_FINDING_KINDS
FORM_FINDING_KINDS = (
    TITLE_PAGE_FINDING_KINDS
    | TOC_FORM_FINDING_KINDS
    | HEADING_FORM_FINDING_KINDS
    | ACKNOWLEDGEMENTS_FINDING_KINDS
    | ABSTRACT_FINDING_KINDS
    | RELEASE_DELTA_FINDING_KINDS
    | READER_CONTRACT_FINDING_KINDS
    | FRONTMATTER_IDENTITY_FINDING_KINDS
    | LAYOUT_FINDING_KINDS
    | APPENDIX_FINDING_KINDS
    | FIGURE_FINDING_KINDS
    | BIBLIOGRAPHY_FINDING_KINDS
    | PREDICTION_FINDING_KINDS
    | CONTENT_RICHNESS_FINDING_KINDS
    | TECHNICAL_PROSE_FINDING_KINDS
    | R006_FINDING_KINDS
    | R007_FINDING_KINDS
    | R008_FINDING_KINDS
    | R009_FINDING_KINDS
    | R011_FINDING_KINDS
    | R012_FINDING_KINDS
    | R013_FINDING_KINDS
)


def machine_audit_paths(release_id: str, version: str, assembly_revision: str | None = None) -> dict[str, Path]:
    base = assembly_paths(release_id, version, assembly_revision)["assembly_json"].parent
    return {
        "audit_json": base / f"OC_CORE_RELEASE_ASSEMBLY_MACHINE_AUDIT_{version}.json",
        "audit_md": base / f"OC_CORE_RELEASE_ASSEMBLY_MACHINE_AUDIT_{version}.md",
    }


def scan_text(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return [{"kind": "missing_file", "path": str(path)}]
    text = path.read_text(encoding="utf-8", errors="replace")
    scan_target = text
    path_text = str(path).replace("\\", "/")
    governance_metadata_path = (
        "/package_assembly/" in path_text
        or "/journal_requirements_spot/" in path_text
        or "journal_requirements_spot" in path_text
    )
    if "recovery_r011" in path_text or governance_metadata_path:
        scan_target = re.sub(
            r"SCIENTIFIC_JOURNAL_SUBMISSION_READY_NO_SEND|OWNER_REVIEW_READY_NO_SEND|REPAIR_REQUIRED_NO_SEND|owner_review_no_send|no_send_lock",
            "allowed_governance_marker",
            scan_target,
            flags=re.IGNORECASE,
        )
    findings: list[dict[str, Any]] = []
    for regex, kind in [
        (CYRILLIC_RE, "cyrillic_public_surface_leak"),
        (FORBIDDEN_TEXT_RE, "forbidden_public_surface_phrase"),
        (LOCAL_PATH_RE, "local_or_private_path_leak"),
    ]:
        for match in regex.finditer(scan_target):
            start = max(0, match.start() - 60)
            end = min(len(scan_target), match.end() + 60)
            findings.append(
                {
                    "kind": kind,
                    "path": str(path.relative_to(ROOT)),
                    "offset": match.start(),
                    "match": match.group(0),
                    "context": scan_target[start:end].replace("\n", " ")[:180],
                }
            )
            if len(findings) >= 20:
                return findings
    return findings


def pdf_text_pages(path: Path, *, first: int = 1, last: int = 16, layout: bool = False) -> str:
    if not path.exists():
        return ""
    try:
        cmd = ["pdftotext", "-f", str(first), "-l", str(last)]
        if layout:
            cmd.append("-layout")
        cmd.extend([str(path), "-"])
        completed = subprocess.run(
            cmd,
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=60,
        )
        return completed.stdout if completed.returncode == 0 else ""
    except Exception:
        return ""


def pdf_text(path: Path, *, pages: int = 16) -> str:
    return pdf_text_pages(path, first=1, last=pages)


def normalize_surface(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def text_segment(text: str, start_patterns: list[str], end_patterns: list[str]) -> str:
    start_match = None
    for pattern in start_patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.S)
        if match and (start_match is None or match.start() < start_match.start()):
            start_match = match
    if not start_match:
        return ""
    start = start_match.end()
    end = len(text)
    for pattern in end_patterns:
        match = re.search(pattern, text[start:], re.IGNORECASE | re.S)
        if match:
            end = min(end, start + match.start())
    return text[start:end]


def word_total(text: str) -> int:
    return len(re.findall(r"[A-Za-z][A-Za-z'-]*", text))


def pdf_toc_page_total(path: Path) -> int:
    text = pdf_text_pages(path, first=1, last=120)
    if not text:
        return 0
    pages = text.split("\f")
    start = None
    for index, page in enumerate(pages):
        if re.search(r"(?m)^\s*(?:Table of Contents|Contents)\s*$", page):
            start = index
            break
    if start is None:
        return 0
    for index in range(start + 1, len(pages)):
        page = pages[index]
        stripped = page.lstrip()
        dotted_line_total = sum(1 for line in page.splitlines() if re.search(r"\.\s*\.\s*\.", line))
        if re.search(r"(?m)^\s*(?:List of Figures|List of Tables|Reader Orientation|1\s+Reader Orientation|Complete Scientific Argument)\s*$", page):
            return max(1, index - start)
        if dotted_line_total < 3 and re.match(r"^\d+\s*\n\s*[A-Z][A-Za-z0-9 ,:&()/'-]{2,}\s*(?:\n|$)", stripped):
            return max(1, index - start)
        if dotted_line_total < 3 and re.match(r"^\d+\s+[A-Z][A-Za-z0-9 ,:&()/'-]{2,}", stripped):
            return max(1, index - start)
    return max(1, len(pages) - start)


def frontmatter_cut(text: str) -> str:
    match = BODY_MARKER_RE.search(text)
    return text[: match.start()] if match else text[:30000]


def expanded_frontmatter_source_text(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix.lower() != ".tex":
        return text
    expanded: list[str] = []
    for match in re.finditer(r"\\input\{([^}]*frontmatter[^}]*)\}", text, re.IGNORECASE):
        ref = match.group(1)
        candidates = [path.parent / ref]
        if not ref.endswith(".tex"):
            candidates.append(path.parent / f"{ref}.tex")
        for candidate in candidates:
            if candidate.is_file():
                expanded.append(candidate.read_text(encoding="utf-8", errors="replace"))
                break
    if expanded:
        return "\n".join(expanded + [text])
    return text


def strip_heading_attributes(text: str) -> str:
    return re.sub(r"\s+\{[^}]*\}\s*$", "", text).strip().strip("#").strip()


def artifact_title_present(text: str, artifact_type_id: str, version: str) -> bool:
    normalized = normalize_surface(text.replace("~", " "))
    normalized_lower = normalized.lower()
    title = artifact_title(artifact_type_id, version)
    if title.lower() in normalized_lower:
        return True
    if artifact_type_id == "master_monograph":
        return (
            "ontology of continua" in normalized_lower
            and f"core {version}" in normalized_lower
            and "master monograph" in normalized_lower
        )
    return False


def artifact_title_index(text: str, artifact_type_id: str, version: str) -> int:
    normalized = normalize_surface(text.replace("~", " "))
    normalized_lower = normalized.lower()
    title = artifact_title(artifact_type_id, version)
    index = normalized_lower.find(title.lower())
    if index >= 0:
        return index
    if artifact_type_id == "master_monograph":
        return normalized_lower.find("ontology of continua")
    return -1


def markdown_headings(text: str) -> list[dict[str, Any]]:
    headings: list[dict[str, Any]] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        match = MARKDOWN_HEADING_RE.match(line.strip())
        if not match:
            continue
        headings.append({"line": line_no, "level": len(match.group(1)), "title": strip_heading_attributes(match.group(2))})
    return headings


def normalized_pdf_heading_line(line: str) -> str:
    text = normalize_surface(line)
    text = re.sub(r"\s+\.{2,}\s*\d+\s*$", "", text)
    text = re.sub(r"\s{2,}\d+\s*$", "", text)
    text = re.sub(r"^\d+(?:\.\d+)*\s+", "", text)
    return text.strip()


def collect_heading_findings(
    headings: list[dict[str, Any]],
    *,
    source_kind: str,
    path: Path,
    artifact_type_id: str,
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    if source_kind == "pdf":
        forbidden_kind = "pdf_forbidden_heading_prefix"
        trailing_kind = "pdf_heading_trailing_comma"
        long_kind = "pdf_heading_too_long"
    else:
        forbidden_kind = "frontmatter_forbidden_heading_prefix"
        trailing_kind = "frontmatter_heading_trailing_comma"
        long_kind = "frontmatter_heading_too_long"
    for heading in headings:
        title = str(heading.get("title") or "").strip()
        if not title:
            continue
        if FORBIDDEN_VISIBLE_HEADING_RE.match(title):
            findings.append(
                {
                    "kind": forbidden_kind,
                    "artifact_type_id": artifact_type_id,
                    "path": str(path.relative_to(ROOT)),
                    "line": heading.get("line"),
                    "heading": title,
                }
            )
        if TECHNICAL_PUBLIC_HEADING_RE.search(title):
            findings.append(
                {
                    "kind": forbidden_kind,
                    "artifact_type_id": artifact_type_id,
                    "path": str(path.relative_to(ROOT)),
                    "line": heading.get("line"),
                    "heading": title,
                }
            )
        if title.rstrip().endswith(","):
            findings.append(
                {
                    "kind": trailing_kind,
                    "artifact_type_id": artifact_type_id,
                    "path": str(path.relative_to(ROOT)),
                    "line": heading.get("line"),
                    "heading": title,
                }
            )
        if len(title) > READER_HEADING_MAX_CHARS:
            findings.append(
                {
                    "kind": long_kind,
                    "artifact_type_id": artifact_type_id,
                    "path": str(path.relative_to(ROOT)),
                    "line": heading.get("line"),
                    "heading": title,
                    "max_chars": READER_HEADING_MAX_CHARS,
                }
            )
    return findings


def collect_source_toc_findings(text: str, path: Path, artifact_type_id: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    toc_count = len(TOC_MARKER_RE.findall(text)) + text.count("\\tableofcontents")
    if toc_count != 1:
        findings.append(
            {
                "kind": "frontmatter_form_toc_count_violation",
                "artifact_type_id": artifact_type_id,
                "path": str(path.relative_to(ROOT)),
                "toc_marker_total": toc_count,
                "expected": 1,
            }
        )
    match = FLAT_TOC_CONTINUATION_RE.search(text)
    if match:
        findings.append(
            {
                "kind": "frontmatter_form_flat_toc_continuation",
                "artifact_type_id": artifact_type_id,
                "path": str(path.relative_to(ROOT)),
                "match": match.group(0),
            }
        )
    match = TECHNICAL_TOC_ENTRY_RE.search(text)
    if match:
        findings.append(
            {
                "kind": "frontmatter_form_technical_toc_entry",
                "artifact_type_id": artifact_type_id,
                "path": str(path.relative_to(ROOT)),
                "match": match.group(0).strip(),
            }
        )
    return findings


def pdf_heading_candidates(text: str) -> list[dict[str, Any]]:
    headings: list[dict[str, Any]] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        title = normalized_pdf_heading_line(line)
        if not title or len(title) < 3:
            continue
        numbered_heading = bool(re.match(r"^\s*\d+(?:\.\d+)*\s+[A-Z][A-Za-z0-9 /&(),:-]+$", line.strip()))
        unnumbered_structural = bool(re.match(r"^(Body|Block\s+\d+)\s*$", title, re.IGNORECASE))
        if (numbered_heading and title[:1].isupper() and FORBIDDEN_VISIBLE_HEADING_RE.match(title)) or unnumbered_structural or (
            numbered_heading and title[:1].isupper() and (title.endswith(",") or len(title) > READER_HEADING_MAX_CHARS)
        ):
            headings.append({"line": line_no, "title": title})
    return headings


def collect_pdf_title_page_findings(path: Path, artifact_type_id: str, version: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    first_page = pdf_text_pages(path, first=1, last=1)
    normalized = normalize_surface(first_page)
    title = artifact_title(artifact_type_id, version)
    required = [
        ("author", AUTHOR_DISPLAY),
        ("orcid", f"ORCID {AUTHOR_ORCID}"),
        ("concept_doi", CONCEPT_DOI),
        ("revision_date", "4 May 2026"),
    ]
    missing = [label for label, needle in required if needle not in normalized]
    if not artifact_title_present(first_page, artifact_type_id, version):
        missing.append("title")
    if missing:
        findings.append(
            {
                "kind": "pdf_title_page_missing_metadata",
                "artifact_type_id": artifact_type_id,
                "path": str(path.relative_to(ROOT)),
                "missing": missing,
            }
        )
    if "1 May 2026" in normalized or "3 May 2026" in normalized or "release date:" in normalized.lower():
        findings.append(
            {
                "kind": "publication_title_page_date_stale",
                "artifact_type_id": artifact_type_id,
                "path": str(path.relative_to(ROOT)),
            }
        )
    if VISIBLE_RECOVERY_REVISION_RE.search(normalized):
        findings.append(
            {
                "kind": "publication_visible_recovery_revision",
                "artifact_type_id": artifact_type_id,
                "path": str(path.relative_to(ROOT)),
            }
        )
    clutter = IDENTITY_CLUTTER_RE.search(normalized)
    if clutter:
        findings.append(
            {
                "kind": "publication_frontmatter_identity_clutter",
                "artifact_type_id": artifact_type_id,
                "path": str(path.relative_to(ROOT)),
                "match": clutter.group(0),
            }
        )
    doi_total = normalized.count(CONCEPT_DOI)
    if doi_total != 1:
        findings.append(
            {
                "kind": "publication_concept_doi_occurrence_violation",
                "artifact_type_id": artifact_type_id,
                "path": str(path.relative_to(ROOT)),
                "concept_doi_total": doi_total,
                "expected": 1,
            }
        )
    title_index = artifact_title_index(first_page, artifact_type_id, version)
    if title_index < 0 or title_index > 240 or TITLE_PAGE_BODY_MARKER_RE.search(normalized):
        findings.append(
            {
                "kind": "pdf_title_page_not_primary",
                "artifact_type_id": artifact_type_id,
                "path": str(path.relative_to(ROOT)),
                "title_index": title_index,
                "first_page_excerpt": normalized[:400],
            }
        )
    if DEDICATION_TEXT not in normalized:
        findings.append(
            {
                "kind": "publication_title_page_missing_dedication",
                "artifact_type_id": artifact_type_id,
                "path": str(path.relative_to(ROOT)),
            }
        )
    leak = PUBLIC_READER_INTERNAL_RE.search(normalized)
    if leak:
        findings.append(
            {
                "kind": "publication_title_page_internal_instrument_leak",
                "artifact_type_id": artifact_type_id,
                "path": str(path.relative_to(ROOT)),
                "match": leak.group(0),
            }
        )
    return findings


def collect_pdf_toc_findings(path: Path, artifact_type_id: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    text = pdf_text_pages(path, first=1, last=80)
    toc_count = len(re.findall(r"(?m)^\s*(?:Table of Contents|Contents)\s*$", text))
    if toc_count != 1:
        findings.append(
            {
                "kind": "pdf_form_toc_count_violation",
                "artifact_type_id": artifact_type_id,
                "path": str(path.relative_to(ROOT)),
                "toc_marker_total": toc_count,
                "expected": 1,
            }
        )
    toc_pages = pdf_toc_page_total(path)
    cap = 20 if artifact_type_id == "master_monograph" else 4
    if toc_pages > cap:
        findings.append(
            {
                "kind": "pdf_toc_page_cap_violation",
                "artifact_type_id": artifact_type_id,
                "path": str(path.relative_to(ROOT)),
                "toc_page_total": toc_pages,
                "cap": cap,
            }
        )
    layout = pdf_text_pages(path, first=1, last=80, layout=True)
    layout_pages = layout.split("\f")
    toc_page_indexes = [
        index for index, page in enumerate(layout_pages) if re.search(r"(?m)^\s*(?:Table of Contents|Contents)\s*$", page)
    ]
    if toc_page_indexes:
        start_page = toc_page_indexes[0]
        scan_page_total = max(1, toc_pages)
        layout = "\n".join(layout_pages[start_page : start_page + scan_page_total])
    lines = layout.splitlines()
    toc_indexes = [index for index, line in enumerate(lines) if line.strip() in {"Table of Contents", "Contents"}]
    if toc_indexes:
        for line in lines[toc_indexes[0] + 1: toc_indexes[0] + 120]:
            stripped = line.strip()
            if not stripped:
                continue
            if len(stripped) > 150:
                findings.append(
                    {
                        "kind": "pdf_toc_layout_line_too_long",
                        "artifact_type_id": artifact_type_id,
                        "path": str(path.relative_to(ROOT)),
                        "line": stripped[:220],
                    }
                )
                break
            if re.search(r"[A-Za-z]\d{1,4}$", stripped):
                findings.append(
                    {
                        "kind": "pdf_toc_layout_page_number_collision",
                        "artifact_type_id": artifact_type_id,
                        "path": str(path.relative_to(ROOT)),
                        "line": stripped[:220],
                    }
                )
                break
            if re.search(r"^\s*\d+(?:\.\d+)+[A-Za-z]", stripped):
                findings.append(
                    {
                        "kind": "pdf_toc_layout_page_number_collision",
                        "artifact_type_id": artifact_type_id,
                        "path": str(path.relative_to(ROOT)),
                        "line": stripped[:220],
                    }
                )
                break
            if PUBLICATION_TECHNICAL_RE.search(stripped) or TECHNICAL_PUBLIC_HEADING_RE.search(stripped):
                findings.append(
                    {
                        "kind": "pdf_toc_hierarchy_technical_entry",
                        "artifact_type_id": artifact_type_id,
                        "path": str(path.relative_to(ROOT)),
                        "line": stripped[:220],
                    }
                )
                break
    return findings


def collect_publication_frontmatter_findings(
    text: str,
    path: Path,
    artifact_type_id: str,
    *,
    source_kind: str,
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    normalized = normalize_surface(text)
    front = frontmatter_cut(text)
    front_normalized = normalize_surface(front)
    clutter = IDENTITY_CLUTTER_RE.search(front_normalized)
    if clutter:
        findings.append(
            {
                "kind": "publication_frontmatter_identity_clutter",
                "artifact_type_id": artifact_type_id,
                "path": str(path.relative_to(ROOT)),
                "source_kind": source_kind,
                "match": clutter.group(0),
            }
        )
    if "1 May 2026" in front_normalized or "3 May 2026" in front_normalized or "release date:" in front_normalized.lower():
        findings.append(
            {
                "kind": "publication_title_page_date_stale",
                "artifact_type_id": artifact_type_id,
                "path": str(path.relative_to(ROOT)),
                "source_kind": source_kind,
            }
        )
    recovery = VISIBLE_RECOVERY_REVISION_RE.search(front_normalized)
    if recovery:
        findings.append(
            {
                "kind": "publication_visible_recovery_revision",
                "artifact_type_id": artifact_type_id,
                "path": str(path.relative_to(ROOT)),
                "source_kind": source_kind,
                "match": recovery.group(0),
            }
        )
    if source_kind == "source":
        keyword_match = re.search(r"(?im)^(?:#\s*Keywords\b|\\noindent\\textbf\{Keywords)", text)
        keyword_index = -1 if not keyword_match else keyword_match.start()
    else:
        keyword_index = normalized.lower().find("keywords")
    toc_index = normalized.lower().find("table of contents")
    if keyword_index >= 0 and (toc_index < 0 or keyword_index < toc_index):
        findings.append(
            {
                "kind": "publication_keywords_not_backmatter",
                "artifact_type_id": artifact_type_id,
                "path": str(path.relative_to(ROOT)),
                "source_kind": source_kind,
            }
        )
    if source_kind == "source" and not re.search(r"R00[567]_TOC_VISUAL_HIERARCHY", text):
        findings.append(
            {
                "kind": "publication_toc_visual_hierarchy_missing",
                "artifact_type_id": artifact_type_id,
                "path": str(path.relative_to(ROOT)),
                "source_kind": source_kind,
            }
        )
    if source_kind == "source" and "R006_TOC_VISUAL_HIERARCHY" not in text and "R007_TOC_VISUAL_HIERARCHY" not in text:
        findings.append(
            {
                "kind": "publication_didactic_spine_order_violation",
                "artifact_type_id": artifact_type_id,
                "path": str(path.relative_to(ROOT)),
                "source_kind": source_kind,
                "missing": "R006_OR_R007_TOC_VISUAL_HIERARCHY",
            }
        )
    if source_kind == "pdf":
        if re.search(r"\.tex\b", text, re.I):
            findings.append(
                {
                    "kind": "publication_tex_reference_leak",
                    "artifact_type_id": artifact_type_id,
                    "path": str(path.relative_to(ROOT)),
                    "source_kind": source_kind,
                }
            )
        lower_text = normalized.lower()
        if artifact_type_id == "master_monograph":
            prediction_anchors = ["prediction", "falsifiability", "formula", "residual", "negative control", "falsifier"]
            missing_prediction = [anchor for anchor in prediction_anchors if anchor not in lower_text]
            if len(missing_prediction) > 2:
                findings.append(
                    {
                        "kind": "publication_prediction_falsifiability_anchor_missing",
                        "artifact_type_id": artifact_type_id,
                        "path": str(path.relative_to(ROOT)),
                        "source_kind": source_kind,
                        "missing": missing_prediction,
                    }
                )
    layout_text = expanded_frontmatter_source_text(path)
    if path.suffix.lower() == ".tex" and (path.parent / "preamble.tex").is_file():
        layout_text += "\n" + (path.parent / "preamble.tex").read_text(encoding="utf-8", errors="replace")
    if path.suffix.lower() == ".tex" and "R005_LAYOUT_STANDARD" not in layout_text:
        findings.append(
            {
                "kind": "publication_layout_standard_missing",
                "artifact_type_id": artifact_type_id,
                "path": str(path.relative_to(ROOT)),
                "source_kind": source_kind,
            }
        )
    if path.suffix.lower() == ".tex" and "R006_LAYOUT_STANDARD" not in layout_text and "R007_LAYOUT_STANDARD" not in layout_text:
        findings.append(
            {
                "kind": "publication_didactic_spine_order_violation",
                "artifact_type_id": artifact_type_id,
                "path": str(path.relative_to(ROOT)),
                "source_kind": source_kind,
                "missing": "R006_OR_R007_LAYOUT_STANDARD",
            }
        )
    leak = PUBLIC_READER_INTERNAL_RE.search(text)
    if leak:
        findings.append(
            {
                "kind": "publication_reader_internal_instrument_leak",
                "artifact_type_id": artifact_type_id,
                "path": str(path.relative_to(ROOT)),
                "source_kind": source_kind,
                "match": leak.group(0),
            }
        )
    technical = PUBLICATION_TECHNICAL_RE.search(text)
    if technical:
        findings.append(
            {
                "kind": "publication_technical_prose_leak",
                "artifact_type_id": artifact_type_id,
                "path": str(path.relative_to(ROOT)),
                "source_kind": source_kind,
                "match": technical.group(0),
                "context": normalized[max(0, technical.start() - 90): technical.end() + 140],
            }
        )
    internal_block = R006_INTERNAL_BLOCK_RE.search(text)
    if internal_block:
        kind = "publication_figure_table_list_visible" if "list of" in internal_block.group(0).lower() else "publication_internal_block_metadata_leak"
        findings.append(
            {
                "kind": kind,
                "artifact_type_id": artifact_type_id,
                "path": str(path.relative_to(ROOT)),
                "source_kind": source_kind,
                "match": internal_block.group(0),
            }
        )
    instruction = R007_INSTRUCTION_PROSE_RE.search(text)
    if instruction:
        findings.append(
            {
                "kind": "publication_instruction_prose_leak",
                "artifact_type_id": artifact_type_id,
                "path": str(path.relative_to(ROOT)),
                "source_kind": source_kind,
                "match": instruction.group(0),
                "context": normalized[max(0, instruction.start() - 90): instruction.end() + 140],
            }
        )
    if artifact_type_id == "master_monograph" and source_kind == "pdf":
        page17 = R007_PAGE17_LEAK_RE.search(text)
        if page17:
            findings.append(
                {
                    "kind": "publication_page17_internal_leak",
                    "artifact_type_id": artifact_type_id,
                    "path": str(path.relative_to(ROOT)),
                    "source_kind": source_kind,
                    "match": page17.group(0),
                }
            )

    ack = text_segment(
        text,
        [r"#\s*Acknowledgements\b", r"\\textbf\{Acknowledgements\.\}", r"\\textbf\{Acknowledgements\}", r"\bAcknowledgements\b"],
        [r"#\s*Abstract\b", r"\\begin\{abstract\}", r"\bAbstract\b"],
    )
    if not ack:
        findings.append({"kind": "publication_acknowledgements_missing", "artifact_type_id": artifact_type_id, "path": str(path.relative_to(ROOT)), "source_kind": source_kind})
    else:
        if word_total(ack) < 65:
            findings.append({"kind": "publication_acknowledgements_too_short", "artifact_type_id": artifact_type_id, "path": str(path.relative_to(ROOT)), "source_kind": source_kind, "word_total": word_total(ack)})
        ack_norm = normalize_surface(ack).lower()
        if "reviewers and critics" not in ack_norm or "development of the ontology of continua" not in ack_norm:
            findings.append({"kind": "publication_acknowledgements_missing_reviewers_critics", "artifact_type_id": artifact_type_id, "path": str(path.relative_to(ROOT)), "source_kind": source_kind})
        if "does not imply authorship" not in ack_norm:
            findings.append({"kind": "publication_acknowledgements_missing_boundary", "artifact_type_id": artifact_type_id, "path": str(path.relative_to(ROOT)), "source_kind": source_kind})
        for name in ACKNOWLEDGEMENT_NAMES:
            if name.replace("G. V.", "G.").split()[0] not in normalize_surface(ack):
                findings.append({"kind": "publication_acknowledgements_missing_name", "artifact_type_id": artifact_type_id, "path": str(path.relative_to(ROOT)), "source_kind": source_kind, "name": name})

    abstract = text_segment(
        text,
        [r"#\s*Abstract\b", r"\\begin\{abstract\}", r"\bAbstract\b"],
        [r"#\s*Version\s+1\.3\.3\s+Release\s+Delta\b", r"\\section\*\{Version\s+1\.3\.3\s+Release\s+Delta\}", r"\bVersion\s+1\.3\.3\s+Release\s+Delta\b", r"\\end\{abstract\}"],
    )
    if not abstract:
        findings.append({"kind": "publication_abstract_missing", "artifact_type_id": artifact_type_id, "path": str(path.relative_to(ROOT)), "source_kind": source_kind})
    else:
        abstract_words = word_total(abstract)
        if abstract_words < 250:
            findings.append({"kind": "publication_abstract_too_short", "artifact_type_id": artifact_type_id, "path": str(path.relative_to(ROOT)), "source_kind": source_kind, "word_total": abstract_words})
        abstract_norm = normalize_surface(abstract).lower()
        anchors = ["bounded", "maturity", "stage", "evidence", "proof", "limitations", "future", "figures", "tables"]
        missing = [anchor for anchor in anchors if anchor not in abstract_norm]
        if len(missing) > 3:
            findings.append({"kind": "publication_abstract_missing_depth_anchor", "artifact_type_id": artifact_type_id, "path": str(path.relative_to(ROOT)), "source_kind": source_kind, "missing": missing})

    lower = normalized.lower()
    abstract_index = lower.find("abstract")
    delta_index = lower.find("version 1.3.3 release delta")
    reader_index = lower.find("reader contract")
    if delta_index < 0:
        findings.append({"kind": "publication_release_delta_missing", "artifact_type_id": artifact_type_id, "path": str(path.relative_to(ROOT)), "source_kind": source_kind})
    elif not (abstract_index >= 0 and abstract_index < delta_index and (reader_index < 0 or delta_index < reader_index)):
        findings.append({"kind": "publication_release_delta_order_violation", "artifact_type_id": artifact_type_id, "path": str(path.relative_to(ROOT)), "source_kind": source_kind})
    delta = text_segment(
        text,
        [r"#\s*Version\s+1\.3\.3\s+Release\s+Delta\b", r"\\section\*\{Version\s+1\.3\.3\s+Release\s+Delta\}", r"\bVersion\s+1\.3\.3\s+Release\s+Delta\b"],
        [r"#\s*Reader Routes\b", r"\\section\*\{Reader Routes\}", r"\bReader Routes\b", r"#\s*Reader Contract\b", r"\\section\*\{Reader Contract\}", r"\bReader Contract\b"],
    )
    if delta:
        delta_norm = normalize_surface(delta).lower()
        anchors = ["typed foundation", "lean", "finite", "target-blind", "prior-art", "review"]
        missing = [anchor for anchor in anchors if anchor not in delta_norm]
        if missing:
            findings.append({"kind": "publication_release_delta_missing_anchor", "artifact_type_id": artifact_type_id, "path": str(path.relative_to(ROOT)), "source_kind": source_kind, "missing": missing})
        policy_anchors = ["continuing scientific program", "meaningful scientific", "regular", "version", "1.3.3"]
        policy_missing = [anchor for anchor in policy_anchors if anchor not in delta_norm]
        if policy_missing:
            findings.append({"kind": "publication_release_policy_missing_anchor", "artifact_type_id": artifact_type_id, "path": str(path.relative_to(ROOT)), "source_kind": source_kind, "missing": policy_missing})
        if word_total(delta) < 330:
            findings.append({"kind": "publication_release_policy_too_short", "artifact_type_id": artifact_type_id, "path": str(path.relative_to(ROOT)), "source_kind": source_kind, "word_total": word_total(delta)})

    reader = text_segment(
        text,
        [r"#\s*Reader Routes\b", r"\\section\*\{Reader Routes\}", r"\bReader Routes\b", r"#\s*Reader Contract\b", r"\\section\*\{Reader Contract\}", r"\bReader Contract\b"],
        [r"\\tableofcontents", r"\bTable\s+of\s+Contents\b", r"(?m)^\s*Contents\s*$", r"\bKeywords\b", r"\\clearpage\s*\\noindent\\textbf\{Keywords"],
    )
    if not reader:
        findings.append({"kind": "publication_reader_contract_missing", "artifact_type_id": artifact_type_id, "path": str(path.relative_to(ROOT)), "source_kind": source_kind})
    else:
        reader_words = word_total(reader)
        if reader_words < 180:
            findings.append({"kind": "publication_reader_contract_too_short", "artifact_type_id": artifact_type_id, "path": str(path.relative_to(ROOT)), "source_kind": source_kind, "word_total": reader_words})
        reader_norm = normalize_surface(reader).lower()
        anchors = ["dear reader", "formulas", "proof", "figures", "numeric", "appendices", "limitations"]
        missing = [anchor for anchor in anchors if anchor not in reader_norm]
        if missing:
            findings.append({"kind": "publication_reader_contract_missing_orientation_anchor", "artifact_type_id": artifact_type_id, "path": str(path.relative_to(ROOT)), "source_kind": source_kind, "missing": missing})
        route_groups = [
            "scientific reviewers",
            "formal critics",
            "systems theorists",
            "ai builders",
            "engineers",
            "cio",
            "ceo",
            "enterprise architects",
            "reproducibility auditors",
            "benchmark readers",
        ]
        missing_groups = [group for group in route_groups if group not in reader_norm]
        if missing_groups:
            findings.append({"kind": "publication_reader_routes_missing_group", "artifact_type_id": artifact_type_id, "path": str(path.relative_to(ROOT)), "source_kind": source_kind, "missing": missing_groups})
        imperative = R006_READER_IMPERATIVE_RE.search(reader)
        if imperative:
            findings.append({"kind": "publication_reader_routes_tone_imperative", "artifact_type_id": artifact_type_id, "path": str(path.relative_to(ROOT)), "source_kind": source_kind, "match": imperative.group(0)})
    if artifact_type_id == "master_monograph":
        r006_text = text
        if source_kind == "source" and path.suffix.lower() == ".tex":
            for rel_ref in [
                "content/r006/01_why_continuum_ontology.tex",
                "content/r006/02_first_concepts_and_k_primer.tex",
                "content/r007/01_why_continuum_ontology.tex",
                "content/r007/02_first_concepts_and_k_primer.tex",
                "content/r008/01_why_continuum_ontology.tex",
                "content/r008/02_first_concepts_and_k_primer.tex",
                "content/r012/01_why_continuum_ontology.tex",
                "content/r012/02_first_concepts_and_k_primer.tex",
                "content/_auto_core_inputs_1_3_3_integrated.tex",
            ]:
                candidate = path.parent / rel_ref
                if candidate.is_file():
                    r006_text += "\n" + candidate.read_text(encoding="utf-8", errors="replace")
        lower_text = normalize_surface(r006_text).lower()
        if "reader orientation" in lower_text or "reader routes and scientific route" in lower_text or "content/17_oc_core_1_3_reader_guide" in r006_text:
            findings.append({"kind": "publication_reader_orientation_duplicate", "artifact_type_id": artifact_type_id, "path": str(path.relative_to(ROOT)), "source_kind": source_kind})
        if re.search(r"\\subsection\{(?:Relation to previous versions|Structure of the monograph)\}", r006_text, re.I) or re.search(
            r"(?m)^\s*\d+(?:\.\d+)?\s+(?:Relation to previous versions|Structure of the monograph)\s*$",
            r006_text,
            re.I,
        ):
            findings.append({"kind": "publication_duplicate_structure_section", "artifact_type_id": artifact_type_id, "path": str(path.relative_to(ROOT)), "source_kind": source_kind})
        if source_kind == "source":
            entry_lower = text.lower()
            integrated_candidate = path.parent / "content/_auto_core_inputs_1_3_3_integrated.tex"
            integrated_lower = integrated_candidate.read_text(encoding="utf-8", errors="replace").lower() if integrated_candidate.is_file() else ""
            entry_terms = [
                "content/r012/01_why_continuum_ontology.tex",
                "content/r012/02_first_concepts_and_k_primer.tex",
                "content/_auto_core_inputs_1_3_3_integrated.tex",
                "part vi -- limits, prior art, and closure",
                "appendices -- evidence, proof, and reference support",
            ]
            if any(term not in entry_lower for term in entry_terms[:2]):
                entry_terms = [
                "content/r008/01_why_continuum_ontology.tex",
                "content/r008/02_first_concepts_and_k_primer.tex",
                "content/_auto_core_inputs_1_3_3_integrated.tex",
                "part vi -- limits, prior art, and closure",
                "appendices -- evidence, proof, and reference support",
                ]
            if any(term not in entry_lower for term in entry_terms[:2]):
                entry_terms = [
                    "content/r007/01_why_continuum_ontology.tex",
                    "content/r007/02_first_concepts_and_k_primer.tex",
                    "content/_auto_core_inputs_1_3_3_integrated.tex",
                    "part vi -- limits, prior art, and closure",
                    "appendices -- evidence, proof, and reference support",
                ]
            if any(term not in entry_lower for term in entry_terms[:2]):
                entry_terms = [
                    "content/r006/01_why_continuum_ontology.tex",
                    "content/r006/02_first_concepts_and_k_primer.tex",
                    "content/_auto_core_inputs_1_3_3_integrated.tex",
                    "part vi -- limits, prior art, and closure",
                    "appendices -- evidence, proof, and reference support",
                ]
            entry_indexes = [entry_lower.find(term) for term in entry_terms]
            integrated_terms = [
                "part iii -- formal core",
                "part iv -- evidence, proof, and falsifiability",
                "part v -- domain and practical routes",
            ]
            integrated_indexes = [integrated_lower.find(term) for term in integrated_terms]
            if (
                any(index < 0 for index in entry_indexes)
                or entry_indexes != sorted(entry_indexes)
                or any(index < 0 for index in integrated_indexes)
                or integrated_indexes != sorted(integrated_indexes)
            ):
                findings.append({"kind": "publication_didactic_spine_order_violation", "artifact_type_id": artifact_type_id, "path": str(path.relative_to(ROOT)), "source_kind": source_kind, "indexes": {"entry": entry_indexes, "integrated": integrated_indexes}})
            motivation = text_segment(r006_text, [r"Motivation:\s+Why a Shared Systems Language Is Needed"], [r"Scope of OC Core 1\.3\.3"])
            if word_total(motivation) < 700:
                findings.append({"kind": "publication_motivation_too_short", "artifact_type_id": artifact_type_id, "path": str(path.relative_to(ROOT)), "source_kind": source_kind, "word_total": word_total(motivation)})
            primer = text_segment(r006_text, [r"First Concepts:\s+Continua,\s+Nesting,\s+and K-Levels"], [r"Part III -- Formal Core"])
            primer_norm = normalize_surface(primer).lower()
            primer_anchors = ["continua are composed of continua", "kontinuum", "enterprise"]
            primer_missing = [anchor for anchor in primer_anchors if anchor not in primer_norm]
            if primer_missing:
                findings.append({"kind": "publication_k_primer_missing", "artifact_type_id": artifact_type_id, "path": str(path.relative_to(ROOT)), "source_kind": source_kind, "missing": primer_missing})
            if source_kind == "source":
                r007_required = ["upward composition", "downward constraint"]
                if "fig:r012-continuum-demonstrator" in r006_text or "fig:r012-k0-k12-hierarchy" in r006_text:
                    r007_required.extend(["fig:r012-continuum-demonstrator", "fig:r012-k0-k12-hierarchy", "R012_K_LEVELS_PRESENT", "R012_VISUAL_SPEC"])
                elif "fig:r008-continuum-demonstrator" in r006_text or "fig:r008-k0-k12-hierarchy" in r006_text:
                    r007_required.extend(["fig:r008-continuum-demonstrator", "fig:r008-k0-k12-hierarchy", "R008_K_LEVELS_PRESENT"])
                else:
                    r007_required.extend(["fig:r007-continuum-demonstrator", "fig:r007-k0-k12-hierarchy"])
                missing_r007 = [anchor for anchor in r007_required if anchor not in r006_text]
                k_missing = [f"K{index}" for index in range(13) if not re.search(rf"\bK_?\{{?{index}\}}?\b", r006_text)]
                if missing_r007 or k_missing:
                    findings.append(
                        {
                            "kind": "publication_k_hierarchy_figure_incomplete",
                            "artifact_type_id": artifact_type_id,
                            "path": str(path.relative_to(ROOT)),
                            "source_kind": source_kind,
                            "missing": missing_r007 + k_missing,
                        }
                    )
                if "semantic elements" not in r006_text.lower() and "falsifier" not in r006_text.lower():
                    findings.append(
                        {
                            "kind": "publication_figure_pedagogy_missing",
                            "artifact_type_id": artifact_type_id,
                            "path": str(path.relative_to(ROOT)),
                            "source_kind": source_kind,
                        }
                    )
    return findings


def collect_publication_content_richness_findings(row: dict[str, Any]) -> list[dict[str, Any]]:
    artifact_type_id = row.get("artifact_type_id")
    findings: list[dict[str, Any]] = []
    if artifact_type_id == "master_monograph":
        if row.get("document_body_source") != "release_machine.science_monolith.integrated_tex_corpus":
            findings.append({"kind": "publication_body_source_not_corpus", "artifact_type_id": artifact_type_id, "document_body_source": row.get("document_body_source")})
        figure_total = int(row.get("figure_total") or 0)
        inline_figure_total = int(row.get("inline_figure_total") or 0)
        table_total = int(row.get("table_total") or 0)
        formula_marker_total = int(row.get("formula_marker_total") or 0)
        bibliography_entry_total = int(row.get("bibliography_entry_total") or 0)
        verified_bibliography_entry_total = int(row.get("verified_bibliography_entry_total") or 0)
        pages = int(((row.get("pdf_build") or {}).get("pages")) or 0)
        missing: list[str] = []
        if figure_total < 30:
            missing.append(f"figures:{figure_total}<30")
        if inline_figure_total < 36:
            findings.append({"kind": "publication_inline_figure_distribution_too_low", "artifact_type_id": artifact_type_id, "inline_figure_total": inline_figure_total, "expected_minimum": 36})
        if int(row.get("figure_atlas_included") or 0) != 0:
            findings.append({"kind": "publication_figure_atlas_still_included", "artifact_type_id": artifact_type_id})
        if table_total < 4:
            missing.append(f"tables:{table_total}<4")
        if formula_marker_total < 500:
            missing.append(f"formulas:{formula_marker_total}<500")
        if bibliography_entry_total < 120:
            findings.append({"kind": "publication_bibliography_depth_too_low", "artifact_type_id": artifact_type_id, "bibliography_entry_total": bibliography_entry_total, "expected_minimum": 120})
        if verified_bibliography_entry_total < 120:
            findings.append({"kind": "publication_bibliography_verified_shortfall", "artifact_type_id": artifact_type_id, "verified_bibliography_entry_total": verified_bibliography_entry_total, "expected_minimum": 120})
        if int(row.get("appendix_letter_only_total") or 0) != 0:
            findings.append({"kind": "publication_appendix_letter_only_title", "artifact_type_id": artifact_type_id, "appendix_letter_only_total": row.get("appendix_letter_only_total")})
        if pages < 650:
            missing.append(f"pages:{pages}<650")
        if missing:
            findings.append({"kind": "publication_master_missing_richness_anchor", "artifact_type_id": artifact_type_id, "missing": missing})
    elif artifact_type_id in TEXT_ARTIFACTS:
        if row.get("document_body_source") not in {
            "curated_public_payload_markdown",
            "curated_public_payload_markdown_publication_translator_r007",
            "curated_public_payload_markdown_logion_llm_service_translator_r008",
            "curated_public_payload_markdown_editorial_ollama_until_done_r009",
            "curated_public_payload_markdown_source_grounded_repair_r010",
            "curated_public_payload_markdown_journal_requirements_spot_r011",
            "curated_public_payload_markdown_figure_visual_qa_r012",
            "curated_public_payload_markdown_table_rendered_qa_r013",
        }:
            findings.append({"kind": "publication_body_source_not_curated_payload", "artifact_type_id": artifact_type_id, "document_body_source": row.get("document_body_source")})
    return findings


def collect_r007_translation_findings(row: dict[str, Any]) -> list[dict[str, Any]]:
    artifact_type_id = row.get("artifact_type_id")
    if artifact_type_id not in TEXT_ARTIFACTS:
        return []
    findings: list[dict[str, Any]] = []
    translation_status = row.get("public_translation_status")
    if translation_status not in {"PUBLICATION_TRANSLATOR_R007", R008_TRANSLATOR_STATUS, R009_TRANSLATOR_STATUS, R010_TRANSLATOR_STATUS, R011_TRANSLATOR_STATUS, R012_TRANSLATOR_STATUS, R013_TRANSLATOR_STATUS}:
        findings.append({"kind": "publication_translation_missing", "artifact_type_id": artifact_type_id, "public_translation_status": row.get("public_translation_status")})
    source = str(row.get("public_translation_source") or "")
    expected_sources = {
        "science_monolith_publication_translator_r007",
        "deterministic_publication_translator_r007",
        "science_monolith_logion_llm_service_translator_r008",
        "logion_llm_service_publication_translator_r008",
        "science_monolith_editorial_ollama_until_done_translator_r009",
        "editorial_ollama_until_done_publication_translator_r009",
        "science_monolith_source_grounded_editorial_repair_r010",
        "source_grounded_editorial_repair_publication_translator_r010",
        "science_monolith_journal_requirements_spot_r011",
        "journal_requirements_spot_publication_translator_r011",
        "science_monolith_figure_visual_qa_spot_r012",
        "figure_visual_qa_publication_translator_r012",
        "science_monolith_table_rendered_qa_spot_r013",
        "table_rendered_qa_publication_translator_r013",
    }
    if source not in expected_sources:
        findings.append({"kind": "publication_all_reader_pdf_translation_missing", "artifact_type_id": artifact_type_id, "public_translation_source": row.get("public_translation_source")})
    if row.get("v_model_lowest_checked_level") != "L10":
        findings.append({"kind": "publication_v_model_trace_missing", "artifact_type_id": artifact_type_id, "v_model_lowest_checked_level": row.get("v_model_lowest_checked_level")})
    governed_status = row.get("governed_ollama_status")
    allowed_statuses = {"OLLAMA_SKIPPED_BY_GOVERNANCE", "OLLAMA_GOVERNED_FALLBACK_DETERMINISTIC", "OLLAMA_GOVERNED_USED", "PASS", "SKIPPED_BY_GOVERNANCE", "LOCAL_OLLAMA_CAPABILITY_EXHAUSTED"}
    if governed_status not in allowed_statuses:
        findings.append({"kind": "publication_ollama_governance_trace_missing", "artifact_type_id": artifact_type_id, "governed_ollama_status": governed_status})
    if int(row.get("unmanaged_ollama_call_total") or 0) != 0:
        findings.append({"kind": "publication_ollama_governance_bypass", "artifact_type_id": artifact_type_id, "unmanaged_ollama_call_total": row.get("unmanaged_ollama_call_total")})
    if translation_status in {R008_TRANSLATOR_STATUS, R009_TRANSLATOR_STATUS, R010_TRANSLATOR_STATUS, R011_TRANSLATOR_STATUS, R012_TRANSLATOR_STATUS, R013_TRANSLATOR_STATUS}:
        if not row.get("logion_llm_service_status"):
            findings.append({"kind": "publication_common_llm_service_missing", "artifact_type_id": artifact_type_id})
        if not row.get("logion_llm_service_ledger_ref"):
            findings.append({"kind": "publication_llm_service_governance_trace_missing", "artifact_type_id": artifact_type_id})
        cadence = row.get("logion_llm_service_cadence_sequence")
        if not isinstance(cadence, list) or not cadence:
            findings.append({"kind": "publication_llm_service_cadence_trace_missing", "artifact_type_id": artifact_type_id})
    return findings


def collect_r008_service_findings(assembly: dict[str, Any]) -> list[dict[str, Any]]:
    if assembly.get("assembly_revision") == "recovery_r008":
        return [
            {"kind": "publication_editorial_llm_queue_not_done", "artifact_type_id": "assembly"},
            {"kind": "publication_actual_ollama_invocation_missing", "artifact_type_id": "assembly"},
        ]
    if assembly.get("assembly_revision") == "recovery_r007":
        return [
            {"kind": "publication_common_llm_service_missing", "artifact_type_id": "assembly"},
            {"kind": "publication_llm_service_vmodel_missing", "artifact_type_id": "assembly"},
        ]
    if assembly.get("assembly_revision") != R008_REVISION:
        return []
    trace = assembly.get("governed_ollama_trace") if isinstance(assembly.get("governed_ollama_trace"), dict) else {}
    findings: list[dict[str, Any]] = []
    if trace.get("schema_id") != "OC_CORE_R008_LOGION_LLM_SERVICE_TRACE_v1" or trace.get("common_llm_service_status") != "PASS":
        findings.append({"kind": "publication_common_llm_service_missing", "artifact_type_id": "assembly"})
    if trace.get("governance_status") not in {"ALLOW", "BLOCK"}:
        findings.append({"kind": "publication_llm_service_governance_trace_missing", "artifact_type_id": "assembly"})
    if not trace.get("gpu_thermal_band") or trace.get("gpu_thermal_band") == "UNKNOWN":
        findings.append({"kind": "publication_llm_service_thermal_monitor_missing", "artifact_type_id": "assembly"})
    if int(trace.get("unmanaged_ollama_call_total") or 0) != 0 or trace.get("direct_ollama_calls_allowed") is not False:
        findings.append({"kind": "publication_llm_service_bypass", "artifact_type_id": "assembly"})
    if trace.get("v_model_lowest_checked_level") != "L10" or trace.get("v_model_flow") != "L10_to_L9_L8_to_document":
        findings.append({"kind": "publication_llm_service_vmodel_missing", "artifact_type_id": "assembly"})
    if not trace.get("capability_status"):
        findings.append({"kind": "publication_local_ollama_capability_unreported", "artifact_type_id": "assembly"})
    cadence = trace.get("cadence_sequence")
    if not isinstance(cadence, list) or not cadence:
        findings.append({"kind": "publication_llm_service_cadence_trace_missing", "artifact_type_id": "assembly"})
    if trace.get("status") in {"SERVICE_TRACE_MISSING", "SERVICE_INVOCATION_FAILED", "SERVICE_MISSING"}:
        findings.append({"kind": "publication_common_llm_service_missing", "artifact_type_id": "assembly", "service_status": trace.get("status")})
    return findings


def collect_r009_queue_findings(assembly: dict[str, Any]) -> list[dict[str, Any]]:
    if assembly.get("assembly_revision") != R009_REVISION:
        return []
    trace = assembly.get("governed_ollama_trace") if isinstance(assembly.get("governed_ollama_trace"), dict) else {}
    findings: list[dict[str, Any]] = []
    if trace.get("schema_id") != "OC_CORE_R009_LOGION_LLM_SERVICE_UNTIL_DONE_TRACE_v1":
        findings.append({"kind": "publication_common_llm_service_missing", "artifact_type_id": "assembly"})
    if trace.get("editorial_llm_queue_status") != "PASS":
        findings.append({"kind": "publication_editorial_llm_queue_not_done", "artifact_type_id": "assembly", "queue_status": trace.get("queue_status")})
    if trace.get("editorial_packet_coverage_status") != "PASS":
        findings.append({"kind": "publication_editorial_packet_coverage_missing", "artifact_type_id": "assembly"})
    if trace.get("actual_ollama_invocation_status") != "PASS":
        findings.append({"kind": "publication_actual_ollama_invocation_missing", "artifact_type_id": "assembly", "ollama_invocation_total": trace.get("ollama_invocation_total")})
    if trace.get("until_done_status") != "PASS":
        findings.append({"kind": "publication_until_done_missing", "artifact_type_id": "assembly", "queue_status": trace.get("queue_status")})
    if trace.get("cooldown_resume_status") != "PASS":
        findings.append({"kind": "publication_cooldown_resume_missing", "artifact_type_id": "assembly"})
    if trace.get("v_model_completion_status") != "PASS":
        findings.append({"kind": "publication_v_model_completion_missing", "artifact_type_id": "assembly"})
    if trace.get("local_capability_exhaustion_status") != "PASS":
        findings.append({"kind": "publication_local_capability_exhaustion_invalid", "artifact_type_id": "assembly", "capability_status": trace.get("capability_status")})
    if int(trace.get("unmanaged_ollama_call_total") or 0) != 0:
        findings.append({"kind": "publication_llm_service_bypass", "artifact_type_id": "assembly"})
    return findings


def collect_r011_journal_spot_findings(assembly: dict[str, Any]) -> list[dict[str, Any]]:
    if assembly.get("assembly_revision") not in {R011_REVISION, R012_REVISION, R013_REVISION}:
        return []
    trace = assembly.get("governed_ollama_trace") if isinstance(assembly.get("governed_ollama_trace"), dict) else {}
    findings: list[dict[str, Any]] = []
    expected_pass = {
        "journal_requirements_trace_status": "publication_journal_requirements_trace_missing",
        "release_spot_completeness_status": "publication_release_spot_incomplete",
        "bounded_synthesis_status": "publication_bounded_synthesis_invalid",
        "source_gap_zero_status": "publication_source_gap_open",
        "all_venue_projection_status": "publication_venue_projection_missing",
        "submission_component_status": "publication_submission_component_missing",
        "journal_format_compliance_status": "publication_journal_format_compliance_missing",
        "zero_internal_leak_status": "publication_internal_leak_in_journal_projection",
        "zero_fabrication_risk_status": "publication_fabrication_risk_open",
    }
    for key, kind in expected_pass.items():
        if trace.get(key) != "PASS":
            findings.append({"kind": kind, "artifact_type_id": "assembly", key: trace.get(key)})
    if trace.get("scientific_journal_submission_ready_status") != "SCIENTIFIC_JOURNAL_SUBMISSION_READY_NO_SEND":
        findings.append(
            {
                "kind": "publication_scientific_journal_readiness_missing",
                "artifact_type_id": "assembly",
                "scientific_journal_submission_ready_status": trace.get("scientific_journal_submission_ready_status"),
            }
        )
    if int(trace.get("venue_total") or 0) != 8 or int(trace.get("requirements_source_total") or 0) != 8 or int(trace.get("requirements_matrix_total") or 0) != 8:
        findings.append(
            {
                "kind": "publication_journal_requirements_trace_missing",
                "artifact_type_id": "assembly",
                "venue_total": trace.get("venue_total"),
                "requirements_source_total": trace.get("requirements_source_total"),
                "requirements_matrix_total": trace.get("requirements_matrix_total"),
            }
        )
    if int(trace.get("unresolved_repair_record_total") or 0) != 0:
        findings.append({"kind": "publication_source_gap_open", "artifact_type_id": "assembly", "unresolved_repair_record_total": trace.get("unresolved_repair_record_total")})
    if int(trace.get("fabrication_risk_total") or 0) != 0:
        findings.append({"kind": "publication_fabrication_risk_open", "artifact_type_id": "assembly", "fabrication_risk_total": trace.get("fabrication_risk_total")})
    if int(trace.get("unmanaged_ollama_call_total") or 0) != 0:
        findings.append({"kind": "publication_llm_service_bypass", "artifact_type_id": "assembly"})
    if trace.get("editorial_llm_queue_status") != "PASS" or trace.get("actual_ollama_invocation_status") != "PASS":
        findings.append(
            {
                "kind": "publication_editorial_llm_queue_not_done",
                "artifact_type_id": "assembly",
                "editorial_llm_queue_status": trace.get("editorial_llm_queue_status"),
                "actual_ollama_invocation_status": trace.get("actual_ollama_invocation_status"),
            }
        )
    version = assembly.get("release_identity", {}).get("version") or "1.3.3"
    base = assembly_paths("oc_core_1_3_3", str(version), str(assembly.get("assembly_revision") or R011_REVISION))["assembly_json"].parents[1]
    root = base / "journal_requirements_spot"
    if not (root / f"OC133_R011_JOURNAL_REQUIREMENTS_INDEX_{version}.json").is_file():
        findings.append({"kind": "publication_journal_requirements_trace_missing", "artifact_type_id": "assembly", "missing": "requirements_index"})
    for venue_id in [
        "FOUNDATIONS_OF_SCIENCE",
        "SYNTHESE",
        "FOUNDATIONS_OF_PHYSICS",
        "ACTA_BIOTHEORETICA",
        "GLOBAL_JOURNAL_OF_FLEXIBLE_SYSTEMS_MANAGEMENT",
        "PHYSICAL_REVIEW_RESEARCH",
        "ACS_OMEGA",
        "PLOS_COMPUTATIONAL_BIOLOGY",
    ]:
        venue_dir_id = {"GLOBAL_JOURNAL_OF_FLEXIBLE_SYSTEMS_MANAGEMENT": "GJFSM"}.get(venue_id, venue_id)
        source = root / "venues" / venue_dir_id / "JOURNAL_REQUIREMENTS_SOURCE.json"
        matrix = root / "venues" / venue_dir_id / "JOURNAL_REQUIREMENTS_MATRIX.json"
        package = root / "journal_packages" / venue_dir_id / "SUBMISSION_PACKAGE.json"
        for path, kind in [
            (source, "publication_journal_requirements_trace_missing"),
            (matrix, "publication_journal_requirements_trace_missing"),
            (package, "publication_venue_projection_missing"),
        ]:
            if not path.is_file():
                findings.append({"kind": kind, "artifact_type_id": venue_id, "missing_path": str(path.relative_to(ROOT))})
        if package.is_file():
            package_payload = read_json(package)
            if package_payload.get("status") != "OWNER_REVIEW_READY_NO_SEND" or package_payload.get("external_action_performed") is not False or package_payload.get("no_send_lock") is not True:
                findings.append({"kind": "publication_submission_component_missing", "artifact_type_id": venue_id})
    return findings


def collect_r012_visual_findings(assembly: dict[str, Any]) -> list[dict[str, Any]]:
    if assembly.get("assembly_revision") == R011_REVISION:
        return [
            {"kind": "publication_r012_figure_spec_missing", "artifact_type_id": "assembly", "reason": "r011 has no figure registry"},
            {"kind": "publication_r012_geometry_failed", "artifact_type_id": "assembly", "reason": "r011 has no geometry ledger"},
            {"kind": "publication_r012_rendered_bbox_failed", "artifact_type_id": "assembly", "reason": "r011 has no rendered bbox ledger"},
            {"kind": "publication_r012_visual_cockpit_failed", "artifact_type_id": "assembly", "reason": "r011 has no visual QA cockpit"},
        ]
    if assembly.get("assembly_revision") not in {R012_REVISION, R013_REVISION}:
        return []
    trace = assembly.get("visual_quality_trace") if isinstance(assembly.get("visual_quality_trace"), dict) else {}
    findings: list[dict[str, Any]] = []
    expected = {
        "figure_spec_coverage_status": "publication_r012_figure_spec_missing",
        "diagram_geometry_status": "publication_r012_geometry_failed",
        "rendered_figure_bbox_status": "publication_r012_rendered_bbox_failed",
        "label_collision_status": "publication_r012_label_collision_failed",
        "figure_semantic_completeness_status": "publication_r012_semantic_visual_failed",
        "k_hierarchy_visual_status": "publication_r012_k_hierarchy_visual_failed",
        "continuum_visual_status": "publication_r012_continuum_visual_failed",
        "caption_argument_status": "publication_r012_caption_argument_failed",
        "visual_cockpit_status": "publication_r012_visual_cockpit_failed",
    }
    for key, kind in expected.items():
        if trace.get(key) != "PASS":
            findings.append({"kind": kind, "artifact_type_id": "assembly", key: trace.get(key)})
    version = assembly.get("release_identity", {}).get("version") or "1.3.3"
    base = assembly_paths("oc_core_1_3_3", str(version), str(assembly.get("assembly_revision") or R012_REVISION))["assembly_json"].parents[1]
    visual_root = base / "visual_quality"
    required_files = [
        visual_root / f"OC133_R012_FIGURE_REGISTRY_{version}.json",
        visual_root / f"OC133_R012_FIGURE_GEOMETRY_LEDGER_{version}.json",
        visual_root / f"OC133_R012_RENDERED_FIGURE_BBOX_LEDGER_{version}.json",
        visual_root / f"OC133_R012_VISUAL_QA_COCKPIT_{version}.json",
    ]
    for path in required_files:
        if not path.is_file():
            findings.append({"kind": "publication_r012_visual_cockpit_failed", "artifact_type_id": "assembly", "missing": str(path.relative_to(ROOT))})
    if (visual_root / "probe").exists():
        findings.append({"kind": "publication_r012_rendered_bbox_failed", "artifact_type_id": "assembly", "reason": "technical probe PDF directory leaked into release tree"})
    return findings


def collect_r013_table_findings(assembly: dict[str, Any]) -> list[dict[str, Any]]:
    if assembly.get("assembly_revision") == R012_REVISION:
        return [
            {"kind": "publication_r013_table_spec_missing", "artifact_type_id": "assembly", "reason": "r012 has no table registry"},
            {"kind": "publication_r013_table_geometry_failed", "artifact_type_id": "assembly", "reason": "r012 has no table geometry ledger"},
            {"kind": "publication_r013_rendered_table_bbox_failed", "artifact_type_id": "assembly", "reason": "r012 has no rendered table bbox ledger"},
            {"kind": "publication_r013_table_cockpit_failed", "artifact_type_id": "assembly", "reason": "r012 has no table QA cockpit"},
        ]
    if assembly.get("assembly_revision") != R013_REVISION:
        return []
    trace = assembly.get("table_quality_trace") if isinstance(assembly.get("table_quality_trace"), dict) else {}
    findings: list[dict[str, Any]] = []
    expected = {
        "table_spec_coverage_status": "publication_r013_table_spec_missing",
        "compiled_table_coverage_status": "publication_r013_compiled_table_coverage_failed",
        "table_layout_standard_status": "publication_r013_table_layout_standard_failed",
        "table_geometry_status": "publication_r013_table_geometry_failed",
        "rendered_table_bbox_status": "publication_r013_rendered_table_bbox_failed",
        "table_text_collision_status": "publication_r013_table_text_collision_failed",
        "table_edge_clipping_status": "publication_r013_table_edge_clipping_failed",
        "table_caption_argument_status": "publication_r013_table_caption_argument_failed",
        "table_semantic_anchor_status": "publication_r013_table_semantic_anchor_failed",
        "table_cockpit_status": "publication_r013_table_cockpit_failed",
    }
    for key, kind in expected.items():
        if trace.get(key) != "PASS":
            findings.append({"kind": kind, "artifact_type_id": "assembly", key: trace.get(key)})
    version = assembly.get("release_identity", {}).get("version") or "1.3.3"
    base = assembly_paths("oc_core_1_3_3", str(version), R013_REVISION)["assembly_json"].parents[1]
    table_root = base / "table_quality"
    required_files = [
        table_root / f"OC133_R013_TABLE_REGISTRY_{version}.json",
        table_root / f"OC133_R013_TABLE_GEOMETRY_LEDGER_{version}.json",
        table_root / f"OC133_R013_RENDERED_TABLE_BBOX_LEDGER_{version}.json",
        table_root / f"OC133_R013_TABLE_QA_COCKPIT_{version}.json",
    ]
    for path in required_files:
        if not path.is_file():
            findings.append({"kind": "publication_r013_table_cockpit_failed", "artifact_type_id": "assembly", "missing": str(path.relative_to(ROOT))})
    if (table_root / "probe").exists():
        findings.append({"kind": "publication_r013_rendered_table_bbox_failed", "artifact_type_id": "assembly", "reason": "technical table probe directory leaked into release tree"})
    if int(trace.get("registered_table_total") or 0) != int(trace.get("compiled_reader_table_total") or -1):
        findings.append(
            {
                "kind": "publication_r013_compiled_table_coverage_failed",
                "artifact_type_id": "assembly",
                "registered_table_total": trace.get("registered_table_total"),
                "compiled_reader_table_total": trace.get("compiled_reader_table_total"),
            }
        )
    return findings


def form_statuses(findings: list[dict[str, Any]]) -> dict[str, str | int]:
    kinds = {finding.get("kind") for finding in findings}
    title_status = "FAIL" if kinds & TITLE_PAGE_FINDING_KINDS else "PASS"
    toc_status = "FAIL" if kinds & TOC_FORM_FINDING_KINDS else "PASS"
    heading_status = "FAIL" if kinds & HEADING_FORM_FINDING_KINDS else "PASS"
    ack_status = "FAIL" if kinds & ACKNOWLEDGEMENTS_FINDING_KINDS else "PASS"
    abstract_status = "FAIL" if kinds & ABSTRACT_FINDING_KINDS else "PASS"
    delta_status = "FAIL" if kinds & RELEASE_DELTA_FINDING_KINDS else "PASS"
    reader_status = "FAIL" if kinds & READER_CONTRACT_FINDING_KINDS else "PASS"
    identity_status = "FAIL" if kinds & FRONTMATTER_IDENTITY_FINDING_KINDS else "PASS"
    layout_status = "FAIL" if kinds & LAYOUT_FINDING_KINDS else "PASS"
    appendix_status = "FAIL" if kinds & APPENDIX_FINDING_KINDS else "PASS"
    figure_status = "FAIL" if kinds & FIGURE_FINDING_KINDS else "PASS"
    bibliography_status = "FAIL" if kinds & BIBLIOGRAPHY_FINDING_KINDS else "PASS"
    prediction_status = "FAIL" if kinds & PREDICTION_FINDING_KINDS else "PASS"
    content_status = "FAIL" if kinds & CONTENT_RICHNESS_FINDING_KINDS else "PASS"
    technical_status = "FAIL" if kinds & TECHNICAL_PROSE_FINDING_KINDS else "PASS"
    title_identity_public_status = "FAIL" if kinds & (TITLE_PAGE_FINDING_KINDS | {"publication_visible_recovery_revision", "publication_title_identity_policy_violation"}) else "PASS"
    frontmatter_depth_status = "FAIL" if kinds & (ABSTRACT_FINDING_KINDS | RELEASE_DELTA_FINDING_KINDS | READER_CONTRACT_FINDING_KINDS | {"publication_release_policy_missing_anchor", "publication_release_policy_too_short"}) else "PASS"
    release_policy_status = "FAIL" if kinds & {"publication_release_policy_missing_anchor", "publication_release_policy_too_short"} else "PASS"
    reader_routes_tone_status = "FAIL" if kinds & {"publication_reader_routes_tone_imperative"} else "PASS"
    single_reader_orientation_status = "FAIL" if kinds & {"publication_reader_orientation_duplicate"} else "PASS"
    no_internal_block_metadata_status = "FAIL" if kinds & {"publication_internal_block_metadata_leak"} else "PASS"
    no_fig_table_lists_status = "FAIL" if kinds & {"publication_figure_table_list_visible"} else "PASS"
    didactic_spine_order_status = "FAIL" if kinds & {"publication_didactic_spine_order_violation"} else "PASS"
    motivation_depth_status = "FAIL" if kinds & {"publication_motivation_too_short"} else "PASS"
    k_primer_status = "FAIL" if kinds & {"publication_k_primer_missing"} else "PASS"
    duplicate_structure_status = "FAIL" if kinds & {"publication_duplicate_structure_section"} else "PASS"
    publication_translation_status = "FAIL" if kinds & {"publication_translation_missing", "publication_all_reader_pdf_translation_missing"} else "PASS"
    instruction_prose_leak_status = "FAIL" if kinds & {"publication_instruction_prose_leak"} else "PASS"
    page17_internal_leak_status = "FAIL" if kinds & {"publication_page17_internal_leak"} else "PASS"
    figure_pedagogy_status = "FAIL" if kinds & {"publication_figure_pedagogy_missing", "publication_diagram_label_collision_risk"} else "PASS"
    k_hierarchy_figure_status = "FAIL" if kinds & {"publication_k_hierarchy_figure_incomplete"} else "PASS"
    all_reader_pdf_translation_status = "FAIL" if kinds & {"publication_all_reader_pdf_translation_missing"} else "PASS"
    governed_ollama_status = "FAIL" if kinds & {"publication_ollama_governance_trace_missing", "publication_ollama_governance_bypass"} else "PASS"
    v_model_audit_status = "FAIL" if kinds & {"publication_v_model_trace_missing"} else "PASS"
    common_llm_service_status = "FAIL" if kinds & {"publication_common_llm_service_missing"} else "PASS"
    llm_service_governance_status = "FAIL" if kinds & {"publication_llm_service_governance_trace_missing"} else "PASS"
    llm_service_cadence_status = "FAIL" if kinds & {"publication_llm_service_cadence_trace_missing"} else "PASS"
    llm_service_thermal_monitor_status = "FAIL" if kinds & {"publication_llm_service_thermal_monitor_missing"} else "PASS"
    llm_service_no_bypass_status = "FAIL" if kinds & {"publication_llm_service_bypass"} else "PASS"
    llm_service_vmodel_status = "FAIL" if kinds & {"publication_llm_service_vmodel_missing"} else "PASS"
    local_ollama_capability_status = "FAIL" if kinds & {"publication_local_ollama_capability_unreported"} else "PASS"
    editorial_llm_queue_status = "FAIL" if kinds & {"publication_editorial_llm_queue_not_done"} else "PASS"
    editorial_packet_coverage_status = "FAIL" if kinds & {"publication_editorial_packet_coverage_missing"} else "PASS"
    actual_ollama_invocation_status = "FAIL" if kinds & {"publication_actual_ollama_invocation_missing"} else "PASS"
    until_done_status = "FAIL" if kinds & {"publication_until_done_missing"} else "PASS"
    cooldown_resume_status = "FAIL" if kinds & {"publication_cooldown_resume_missing"} else "PASS"
    v_model_completion_status = "FAIL" if kinds & {"publication_v_model_completion_missing"} else "PASS"
    local_capability_exhaustion_status = "FAIL" if kinds & {"publication_local_capability_exhaustion_invalid"} else "PASS"
    journal_requirements_trace_status = "FAIL" if kinds & {"publication_journal_requirements_trace_missing"} else "PASS"
    release_spot_completeness_status = "FAIL" if kinds & {"publication_release_spot_incomplete"} else "PASS"
    bounded_synthesis_status = "FAIL" if kinds & {"publication_bounded_synthesis_invalid"} else "PASS"
    source_gap_zero_status = "FAIL" if kinds & {"publication_source_gap_open"} else "PASS"
    all_venue_projection_status = "FAIL" if kinds & {"publication_venue_projection_missing"} else "PASS"
    submission_component_status = "FAIL" if kinds & {"publication_submission_component_missing"} else "PASS"
    journal_format_compliance_status = "FAIL" if kinds & {"publication_journal_format_compliance_missing"} else "PASS"
    zero_internal_leak_status = "FAIL" if kinds & {"publication_internal_leak_in_journal_projection"} else "PASS"
    zero_fabrication_risk_status = "FAIL" if kinds & {"publication_fabrication_risk_open"} else "PASS"
    scientific_journal_submission_ready_status = "FAIL" if kinds & {"publication_scientific_journal_readiness_missing"} else "PASS"
    figure_spec_coverage_status = "FAIL" if kinds & {"publication_r012_figure_spec_missing"} else "PASS"
    diagram_geometry_status = "FAIL" if kinds & {"publication_r012_geometry_failed"} else "PASS"
    rendered_figure_bbox_status = "FAIL" if kinds & {"publication_r012_rendered_bbox_failed"} else "PASS"
    label_collision_status = "FAIL" if kinds & {"publication_r012_label_collision_failed"} else "PASS"
    figure_semantic_completeness_status = "FAIL" if kinds & {"publication_r012_semantic_visual_failed"} else "PASS"
    k_hierarchy_visual_status = "FAIL" if kinds & {"publication_r012_k_hierarchy_visual_failed"} else "PASS"
    continuum_visual_status = "FAIL" if kinds & {"publication_r012_continuum_visual_failed"} else "PASS"
    caption_argument_status = "FAIL" if kinds & {"publication_r012_caption_argument_failed"} else "PASS"
    visual_cockpit_status = "FAIL" if kinds & {"publication_r012_visual_cockpit_failed"} else "PASS"
    table_spec_coverage_status = "FAIL" if kinds & {"publication_r013_table_spec_missing"} else "PASS"
    compiled_table_coverage_status = "FAIL" if kinds & {"publication_r013_compiled_table_coverage_failed"} else "PASS"
    table_layout_standard_status = "FAIL" if kinds & {"publication_r013_table_layout_standard_failed"} else "PASS"
    table_geometry_status = "FAIL" if kinds & {"publication_r013_table_geometry_failed"} else "PASS"
    rendered_table_bbox_status = "FAIL" if kinds & {"publication_r013_rendered_table_bbox_failed"} else "PASS"
    table_text_collision_status = "FAIL" if kinds & {"publication_r013_table_text_collision_failed"} else "PASS"
    table_edge_clipping_status = "FAIL" if kinds & {"publication_r013_table_edge_clipping_failed"} else "PASS"
    table_caption_argument_status = "FAIL" if kinds & {"publication_r013_table_caption_argument_failed"} else "PASS"
    table_semantic_anchor_status = "FAIL" if kinds & {"publication_r013_table_semantic_anchor_failed"} else "PASS"
    table_cockpit_status = "FAIL" if kinds & {"publication_r013_table_cockpit_failed"} else "PASS"
    form_status = "PASS" if all(
        status == "PASS"
        for status in [
            title_status,
            toc_status,
            heading_status,
            ack_status,
            abstract_status,
            delta_status,
            reader_status,
            identity_status,
            layout_status,
            appendix_status,
            figure_status,
            bibliography_status,
            prediction_status,
            content_status,
            technical_status,
            title_identity_public_status,
            frontmatter_depth_status,
            release_policy_status,
            reader_routes_tone_status,
            single_reader_orientation_status,
            no_internal_block_metadata_status,
            no_fig_table_lists_status,
            didactic_spine_order_status,
            motivation_depth_status,
            k_primer_status,
            duplicate_structure_status,
            publication_translation_status,
            instruction_prose_leak_status,
            page17_internal_leak_status,
            figure_pedagogy_status,
            k_hierarchy_figure_status,
            all_reader_pdf_translation_status,
            governed_ollama_status,
            v_model_audit_status,
            common_llm_service_status,
            llm_service_governance_status,
            llm_service_cadence_status,
            llm_service_thermal_monitor_status,
            llm_service_no_bypass_status,
            llm_service_vmodel_status,
            local_ollama_capability_status,
            editorial_llm_queue_status,
            editorial_packet_coverage_status,
            actual_ollama_invocation_status,
            until_done_status,
            cooldown_resume_status,
            v_model_completion_status,
            local_capability_exhaustion_status,
            journal_requirements_trace_status,
            release_spot_completeness_status,
            bounded_synthesis_status,
            source_gap_zero_status,
            all_venue_projection_status,
            submission_component_status,
            journal_format_compliance_status,
            zero_internal_leak_status,
            zero_fabrication_risk_status,
            scientific_journal_submission_ready_status,
            figure_spec_coverage_status,
            diagram_geometry_status,
            rendered_figure_bbox_status,
            label_collision_status,
            figure_semantic_completeness_status,
            k_hierarchy_visual_status,
            continuum_visual_status,
            caption_argument_status,
            visual_cockpit_status,
            table_spec_coverage_status,
            compiled_table_coverage_status,
            table_layout_standard_status,
            table_geometry_status,
            rendered_table_bbox_status,
            table_text_collision_status,
            table_edge_clipping_status,
            table_caption_argument_status,
            table_semantic_anchor_status,
            table_cockpit_status,
        ]
    ) else "FAIL"
    return {
        "title_page_status": title_status,
        "toc_semantic_status": toc_status,
        "heading_hygiene_status": heading_status,
        "title_page_publication_status": title_status,
        "acknowledgements_status": ack_status,
        "abstract_depth_status": abstract_status,
        "release_delta_status": delta_status,
        "reader_contract_status": reader_status,
        "frontmatter_identity_status": identity_status,
        "reader_routes_status": reader_status,
        "toc_visual_hierarchy_status": layout_status,
        "uniform_document_hierarchy_status": "PASS" if appendix_status == "PASS" and heading_status == "PASS" else "FAIL",
        "appendix_naming_status": appendix_status,
        "layout_quality_status": layout_status,
        "table_readability_status": "PASS" if content_status == "PASS" and table_cockpit_status == "PASS" else "FAIL",
        "inline_figure_distribution_status": figure_status,
        "caption_quality_status": figure_status,
        "bibliography_depth_status": bibliography_status,
        "prediction_falsifiability_status": prediction_status,
        "reader_facing_reference_status": identity_status,
        "toc_hierarchy_status": toc_status,
        "content_richness_status": content_status,
        "technical_prose_leak_status": technical_status,
        "didactic_density_status": "PASS" if content_status == "PASS" and figure_status == "PASS" else "FAIL",
        "title_identity_public_status": title_identity_public_status,
        "frontmatter_depth_status": frontmatter_depth_status,
        "release_policy_status": release_policy_status,
        "reader_routes_tone_status": reader_routes_tone_status,
        "single_reader_orientation_status": single_reader_orientation_status,
        "no_internal_block_metadata_status": no_internal_block_metadata_status,
        "no_fig_table_lists_status": no_fig_table_lists_status,
        "didactic_spine_order_status": didactic_spine_order_status,
        "motivation_depth_status": motivation_depth_status,
        "k_primer_status": k_primer_status,
        "duplicate_structure_status": duplicate_structure_status,
        "publication_translation_status": publication_translation_status,
        "instruction_prose_leak_status": instruction_prose_leak_status,
        "page17_internal_leak_status": page17_internal_leak_status,
        "figure_pedagogy_status": figure_pedagogy_status,
        "k_hierarchy_figure_status": k_hierarchy_figure_status,
        "all_reader_pdf_translation_status": all_reader_pdf_translation_status,
        "governed_ollama_status": governed_ollama_status,
        "v_model_audit_status": v_model_audit_status,
        "common_llm_service_status": common_llm_service_status,
        "llm_service_governance_status": llm_service_governance_status,
        "llm_service_cadence_status": llm_service_cadence_status,
        "llm_service_thermal_monitor_status": llm_service_thermal_monitor_status,
        "llm_service_no_bypass_status": llm_service_no_bypass_status,
        "llm_service_vmodel_status": llm_service_vmodel_status,
        "local_ollama_capability_status": local_ollama_capability_status,
        "editorial_llm_queue_status": editorial_llm_queue_status,
        "editorial_packet_coverage_status": editorial_packet_coverage_status,
        "actual_ollama_invocation_status": actual_ollama_invocation_status,
        "until_done_status": until_done_status,
        "cooldown_resume_status": cooldown_resume_status,
        "v_model_completion_status": v_model_completion_status,
        "local_capability_exhaustion_status": local_capability_exhaustion_status,
        "journal_requirements_trace_status": journal_requirements_trace_status,
        "release_spot_completeness_status": release_spot_completeness_status,
        "bounded_synthesis_status": bounded_synthesis_status,
        "source_gap_zero_status": source_gap_zero_status,
        "all_venue_projection_status": all_venue_projection_status,
        "submission_component_status": submission_component_status,
        "journal_format_compliance_status": journal_format_compliance_status,
        "zero_internal_leak_status": zero_internal_leak_status,
        "zero_fabrication_risk_status": zero_fabrication_risk_status,
        "scientific_journal_submission_ready_status": scientific_journal_submission_ready_status,
        "figure_spec_coverage_status": figure_spec_coverage_status,
        "diagram_geometry_status": diagram_geometry_status,
        "rendered_figure_bbox_status": rendered_figure_bbox_status,
        "label_collision_status": label_collision_status,
        "figure_semantic_completeness_status": figure_semantic_completeness_status,
        "k_hierarchy_visual_status": k_hierarchy_visual_status,
        "continuum_visual_status": continuum_visual_status,
        "caption_argument_status": caption_argument_status,
        "visual_cockpit_status": visual_cockpit_status,
        "table_spec_coverage_status": table_spec_coverage_status,
        "compiled_table_coverage_status": compiled_table_coverage_status,
        "table_layout_standard_status": table_layout_standard_status,
        "table_geometry_status": table_geometry_status,
        "rendered_table_bbox_status": rendered_table_bbox_status,
        "table_text_collision_status": table_text_collision_status,
        "table_edge_clipping_status": table_edge_clipping_status,
        "table_caption_argument_status": table_caption_argument_status,
        "table_semantic_anchor_status": table_semantic_anchor_status,
        "table_cockpit_status": table_cockpit_status,
        "form_quality_status": form_status,
        "form_finding_total": sum(1 for finding in findings if finding.get("kind") in FORM_FINDING_KINDS),
    }


def frontmatter_findings_for_source(path: Path, artifact_type_id: str, version: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    if not path.exists():
        return [{"kind": "reader_source_missing", "path": str(path.relative_to(ROOT)), "artifact_type_id": artifact_type_id}]
    text = expanded_frontmatter_source_text(path)
    front = frontmatter_cut(text)
    normalized_front = normalize_surface(front.replace("~", " "))
    title = artifact_title(artifact_type_id, version)
    required_pairs = [
        ("dedication", DEDICATION_TEXT),
        ("acknowledgements", "reviewers and critics whose questions"),
        ("acknowledgement_boundary", "does not imply authorship"),
        ("abstract", "Abstract"),
        ("release_delta", "Version 1.3.3 Release Delta"),
        ("reader_routes", "Reader Routes"),
        ("table_of_contents", "\\tableofcontents"),
        ("author_orcid", "ORCID 0009-0008-6166-0914"),
    ]
    if not artifact_title_present(front, artifact_type_id, version):
        findings.append(
            {
                "kind": "frontmatter_governance_missing_source_section",
                "artifact_type_id": artifact_type_id,
                "path": str(path.relative_to(ROOT)),
                "section_id": "title_page",
                "needle": title,
            }
        )
    for section_id, needle in required_pairs:
        if normalize_surface(needle).lower() not in normalized_front.lower():
            findings.append(
                {
                    "kind": "frontmatter_governance_missing_source_section",
                    "artifact_type_id": artifact_type_id,
                    "path": str(path.relative_to(ROOT)),
                    "section_id": section_id,
                    "needle": needle,
                }
            )
    for name in ACKNOWLEDGEMENT_NAMES:
        name_variants = {name, name.replace("G. V.", "G.~V.")}
        if not any(normalize_surface(variant.replace("~", " ")) in normalized_front for variant in name_variants):
            findings.append(
                {
                    "kind": "frontmatter_governance_missing_acknowledgement_name",
                    "artifact_type_id": artifact_type_id,
                    "path": str(path.relative_to(ROOT)),
                    "name": name,
                }
            )
    previous_index = -1
    for label_group in [
        ["\\begin{titlepage}"],
        [DEDICATION_TEXT],
        ["# Acknowledgements", r"\textbf{Acknowledgements", "Acknowledgements"],
        ["# Abstract", r"\begin{abstract}", "Abstract"],
        ["# Version 1.3.3 Release Delta", r"\section*{Version 1.3.3 Release Delta}", "Version 1.3.3 Release Delta"],
        ["# Reader Routes", r"\section*{Reader Routes}", "Reader Routes", "# Reader Contract", r"\section*{Reader Contract}", "Reader Contract"],
        ["\\tableofcontents"],
    ]:
        label_index = min([index for index in (text.find(label) for label in label_group) if index >= 0] or [-1])
        if label_index < 0 or label_index <= previous_index:
            findings.append(
                {
                    "kind": "frontmatter_governance_source_order_violation",
                    "artifact_type_id": artifact_type_id,
                    "path": str(path.relative_to(ROOT)),
                    "label": " | ".join(label_group),
                }
            )
        else:
            previous_index = label_index
    findings.extend(collect_heading_findings(markdown_headings(text), source_kind="source", path=path, artifact_type_id=artifact_type_id))
    findings.extend(collect_source_toc_findings(text, path, artifact_type_id))
    for regex, kind in [
        (FRONTMATTER_BODY_LEAK_RE, "frontmatter_l10_rendered_as_body_prose"),
        (READER_SURFACE_CONTROL_RE, "reader_surface_control_plane_leak"),
    ]:
        match = regex.search(text)
        if match:
            findings.append(
                {
                    "kind": kind,
                    "artifact_type_id": artifact_type_id,
                    "path": str(path.relative_to(ROOT)),
                    "match": match.group(0),
                    "context": normalized_front[max(0, match.start() - 80): match.end() + 120],
                }
            )
    findings.extend(collect_publication_frontmatter_findings(text, path, artifact_type_id, source_kind="source"))
    return findings


def frontmatter_findings_for_pdf(path: Path, artifact_type_id: str, version: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    if not path.exists():
        return [{"kind": "reader_pdf_missing", "path": str(path.relative_to(ROOT)), "artifact_type_id": artifact_type_id}]
    text = pdf_text(path, pages=120)
    normalized = normalize_surface(text)
    title = artifact_title(artifact_type_id, version)
    findings.extend(collect_pdf_title_page_findings(path, artifact_type_id, version))
    findings.extend(collect_pdf_toc_findings(path, artifact_type_id))
    findings.extend(collect_heading_findings(pdf_heading_candidates(text), source_kind="pdf", path=path, artifact_type_id=artifact_type_id))
    required = [
        ("dedication", DEDICATION_TEXT),
        ("acknowledgements", "reviewers and critics whose questions"),
        ("abstract", "Abstract"),
        ("release_delta", "Version 1.3.3 Release Delta"),
        ("reader_routes", "Reader Routes"),
        ("table_of_contents", "Table of Contents"),
        ("author_orcid", "ORCID 0009-0008-6166-0914"),
    ]
    if not artifact_title_present(text, artifact_type_id, version):
        findings.append(
            {
                "kind": "frontmatter_governance_missing_pdf_section",
                "artifact_type_id": artifact_type_id,
                "path": str(path.relative_to(ROOT)),
                "section_id": "title_page",
                "needle": title,
            }
        )
    for section_id, needle in required:
        if normalize_surface(needle) not in normalized:
            findings.append(
                {
                    "kind": "frontmatter_governance_missing_pdf_section",
                    "artifact_type_id": artifact_type_id,
                    "path": str(path.relative_to(ROOT)),
                    "section_id": section_id,
                    "needle": needle,
                }
            )
    findings.extend(collect_publication_frontmatter_findings(text, path, artifact_type_id, source_kind="pdf"))
    for regex, kind in [
        (FRONTMATTER_BODY_LEAK_RE, "frontmatter_l10_rendered_as_pdf_body_prose"),
        (READER_SURFACE_CONTROL_RE, "reader_pdf_control_plane_leak"),
    ]:
        match = regex.search(text)
        if match:
            findings.append(
                {
                    "kind": kind,
                    "artifact_type_id": artifact_type_id,
                    "path": str(path.relative_to(ROOT)),
                    "match": match.group(0),
                    "context": normalized[max(0, match.start() - 80): match.end() + 120],
                }
            )
    return findings


def build_audit(release_id: str, assembly_revision: str | None = None) -> dict[str, Any]:
    version = version_from_release_id(release_id)
    paths = assembly_paths(release_id, version, assembly_revision)
    assembly = read_json(paths["assembly_json"])
    assembly_audit = read_json(paths["audit_json"])
    terminal_contracts = read_json(paths["terminal_contracts_json"])
    transitions = read_json(paths["transition_records_json"])
    findings: list[dict[str, Any]] = []

    if assembly.get("status") != "OC_CORE_RELEASE_PACKAGE_REVIEW_ARTIFACTS_ASSEMBLED":
        findings.append({"kind": "assembly_status_not_ready", "value": assembly.get("status")})
    if assembly_audit.get("status") != "PASS":
        findings.append({"kind": "assembly_audit_not_pass", "value": assembly_audit.get("status")})
    if assembly.get("publication_actions_performed") is not False:
        findings.append({"kind": "publication_action_flag_not_false", "value": assembly.get("publication_actions_performed")})
    if terminal_contracts.get("blocked_terminal_total", 0) != 0:
        findings.append({"kind": "blocked_terminal_contracts", "value": terminal_contracts.get("blocked_terminal_total")})
    if transitions.get("transition_record_total") != max(terminal_contracts.get("terminal_node_total", 0) - 1, 0):
        findings.append(
            {
                "kind": "transition_count_mismatch",
                "transition_record_total": transitions.get("transition_record_total"),
                "terminal_node_total": terminal_contracts.get("terminal_node_total"),
            }
        )
    findings.extend(collect_r008_service_findings(assembly))
    findings.extend(collect_r009_queue_findings(assembly))
    findings.extend(collect_r011_journal_spot_findings(assembly))
    findings.extend(collect_r012_visual_findings(assembly))
    findings.extend(collect_r013_table_findings(assembly))

    scan_paths = [
        paths["terminal_contracts_json"],
        paths["terminal_contracts_md"],
        paths["transition_records_json"],
        paths["transition_records_md"],
        paths["assembly_json"],
        paths["assembly_md"],
        paths["manifest_json"],
        paths["checksums_txt"],
    ]
    for row in assembly.get("artifact_rows", []):
        if row.get("artifact_type_id") in TEXT_ARTIFACTS:
            source_path = ROOT / str(row.get("source_path"))
            pdf_path = ROOT / str(row.get("pdf_path"))
            findings.extend(collect_publication_content_richness_findings(row))
            findings.extend(collect_r007_translation_findings(row))
            findings.extend(frontmatter_findings_for_source(source_path, row["artifact_type_id"], version))
            findings.extend(frontmatter_findings_for_pdf(pdf_path, row["artifact_type_id"], version))
            if "frontmatter_body_excluded_total" not in row:
                findings.append(
                    {
                        "kind": "frontmatter_body_exclusion_metric_missing",
                        "artifact_type_id": row.get("artifact_type_id"),
                        "required_sections": FRONTMATTER_REQUIRED_SECTIONS,
                    }
                )
        for output in row.get("output_paths", []):
            path = ROOT / output
            if path.suffix.lower() in {".md", ".json", ".txt"}:
                scan_paths.append(path)
        pdf_build = row.get("pdf_build")
        if pdf_build:
            stderr_tail = str(pdf_build.get("stderr_tail") or "")
            stdout_tail = str(pdf_build.get("stdout_tail") or "")
            if MISSING_CHAR_RE.search(stderr_tail) or MISSING_CHAR_RE.search(stdout_tail):
                findings.append(
                    {
                        "kind": "pdf_engine_missing_character_warning",
                        "artifact_type_id": row.get("artifact_type_id"),
                        "stderr_tail": stderr_tail[-1000:],
                    }
                )
            if not pdf_build.get("ok"):
                findings.append({"kind": "pdf_build_not_ok", "artifact_type_id": row.get("artifact_type_id")})

    for path in sorted(set(scan_paths), key=lambda item: str(item)):
        findings.extend(scan_text(path))

    severity_counts: dict[str, int] = {}
    for finding in findings:
        severity = "CRITICAL" if finding["kind"] in {
            "cyrillic_public_surface_leak",
            "forbidden_public_surface_phrase",
            "local_or_private_path_leak",
            "pdf_engine_missing_character_warning",
            "frontmatter_governance_missing_source_section",
            "frontmatter_governance_missing_pdf_section",
            "frontmatter_l10_rendered_as_body_prose",
            "frontmatter_l10_rendered_as_pdf_body_prose",
            "reader_surface_control_plane_leak",
            "reader_pdf_control_plane_leak",
            *FORM_FINDING_KINDS,
        } else "HIGH"
        finding["severity"] = severity
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
    form_summary = form_statuses(findings)
    trace = assembly.get("governed_ollama_trace") if isinstance(assembly.get("governed_ollama_trace"), dict) else {}

    payload: dict[str, Any] = {
        "schema_id": "OC_CORE_RELEASE_ASSEMBLY_MACHINE_AUDIT_v1",
        "artifact_kind": "OC_CORE_RELEASE_ASSEMBLY_MACHINE_AUDIT",
        "status": "PASS" if not findings else "FAIL",
        "release_id": release_id,
        "version": version,
        "assembly_revision": assembly_revision,
        "structure_source": assembly.get("structure_source"),
        "source_hashes": {
            "release_package_assembly_hash": assembly.get("artifact_hash"),
            "release_package_assembly_audit_hash": assembly_audit.get("artifact_hash"),
            "terminal_contracts_hash": terminal_contracts.get("artifact_hash"),
            "transition_records_hash": transitions.get("artifact_hash"),
        },
        "summary": {
            "terminal_node_total": terminal_contracts.get("terminal_node_total"),
            "blocked_terminal_total": terminal_contracts.get("blocked_terminal_total"),
            "transition_record_total": transitions.get("transition_record_total"),
            "artifact_type_total": len(assembly.get("artifact_rows", [])),
            "finding_total": len(findings),
            "severity_counts": severity_counts,
            "source_grounded_repair_status": trace.get("source_grounded_repair_status"),
            "local_editorial_capability_boundary_status": trace.get("local_editorial_capability_boundary_status"),
            "unresolved_repair_record_total": trace.get("unresolved_repair_record_total"),
            "accepted_candidate_promoted_total": trace.get("accepted_candidate_promoted_total"),
            "journal_requirements_trace_status": trace.get("journal_requirements_trace_status"),
            "release_spot_completeness_status": trace.get("release_spot_completeness_status"),
            "bounded_synthesis_status": trace.get("bounded_synthesis_status"),
            "source_gap_zero_status": trace.get("source_gap_zero_status"),
            "all_venue_projection_status": trace.get("all_venue_projection_status"),
            "submission_component_status": trace.get("submission_component_status"),
            "journal_format_compliance_status": trace.get("journal_format_compliance_status"),
            "zero_internal_leak_status": trace.get("zero_internal_leak_status"),
            "zero_fabrication_risk_status": trace.get("zero_fabrication_risk_status"),
            "scientific_journal_submission_ready_status": trace.get("scientific_journal_submission_ready_status"),
            "scientific_journal_terminal_state": trace.get("scientific_journal_submission_ready_status"),
            "venue_total": trace.get("venue_total"),
            "requirements_source_total": trace.get("requirements_source_total"),
            "requirements_matrix_total": trace.get("requirements_matrix_total"),
            "journal_package_total": trace.get("journal_package_total"),
            **form_summary,
        },
        "findings": findings,
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def render_md(payload: dict[str, Any]) -> str:
    lines = [
        f"# OC Core Release Assembly Machine Audit {payload['version']}",
        "",
        f"Status: `{payload['status']}`",
        f"Assembly revision: `{payload.get('assembly_revision') or 'default'}`",
        f"Structure source: `{payload.get('structure_source')}`",
        f"Artifact hash: `{payload['artifact_hash']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Findings", ""])
    if not payload["findings"]:
        lines.append("- none")
    for finding in payload["findings"][:200]:
        lines.append(f"- `{finding['severity']}` `{finding['kind']}`: `{finding.get('path') or finding.get('artifact_type_id') or 'assembly'}`")
    return "\n".join(lines).rstrip() + "\n"


def expected_files(release_id: str, assembly_revision: str | None = None) -> dict[Path, str]:
    version = version_from_release_id(release_id)
    audit = build_audit(release_id, assembly_revision)
    paths = machine_audit_paths(release_id, version, assembly_revision)
    return {
        paths["audit_json"]: stable_json(audit),
        paths["audit_md"]: render_md(audit),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit OC Core release assembly machine output for surface and process leaks.")
    parser.add_argument("--release", required=True)
    parser.add_argument("--assembly-revision")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if not args.write and not args.check:
        args.check = True
    result = validation_result(expected_files(args.release, args.assembly_revision), write=args.write)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    audit = build_audit(args.release, args.assembly_revision)
    return 0 if result["state"] == "PASS" and audit["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
