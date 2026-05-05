from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from assemble_oc_core_release_package import assembly_paths

RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"
ARTIFACTS = ROOT / "releases" / RELEASE_ID / "artifacts"
OUT_DIR = ROOT / "reviews" / "oc133_llm_cerberus" / "editorial_release_review"
SUMMARY = OUT_DIR / "OC133_EDITORIAL_CERBERUS_SUMMARY.json"

PDFS = {
    "guide": "00_OC_CORE_1_3_3_RELEASE_GUIDE_EN.pdf",
    "master": "OC_CORE_1_3_3_MASTER_MONOGRAPH_EN.pdf",
    "journal": "OC_CORE_1_3_3_JOURNAL_CORE_EN.pdf",
    "methods": "OC_CORE_1_3_3_METHODS_AND_REPRODUCIBILITY_COMPANION_EN.pdf",
    "reviewer": "OC_CORE_1_3_3_REVIEWER_ATTACK_AND_RESPONSE_MAP_EN.pdf",
}

ARTIFACT_KEYS = {
    "release_guide": "guide",
    "master_monograph": "master",
    "journal_core_article": "journal",
    "methods_repro_companion": "methods",
    "reviewer_attack_response_map": "reviewer",
}

ROLES = {
    "scientific_copyeditor": "Read as a senior scientific copyeditor. Ask who the target reader is, what each section teaches, whether the prose is coherent paragraph by paragraph, and whether grammar, diction, transitions, and terminology are publication-grade.",
    "technical_editor": "Read as a technical editor. Attack structure, theorem/evidence navigation, notation, formulas, cross-references, reproducibility path, and whether the science flows into the manuscript rather than being dumped as ledgers.",
    "journal_editor": "Read as a journal editor deciding whether to send for peer review. Ask what the text is about, why it exists, whether the argument is ordered correctly, whether claims are defensible, and whether the manuscript set is suitable for external review.",
    "layout_toc_page_flow_reviewer": "Read as a layout and document-design reviewer. Inspect title pages, dedication, abstracts, TOC, page flow, section hierarchy, list/table balance, figure use, visual route, and whether each PDF looks like a serious scientific document.",
    "hostile_reader": "Read as an antagonistic expert. Find places where the document feels glued, evasive, inflated, incomplete, unreadable, underexplained, insufficiently illustrated, or not publication-grade.",
    "bibliography_metadata_editor": "Read as a bibliography, literature, and metadata editor. Check whether literature coverage is adequate for the claims, whether prior-art positioning is serious, and whether DOI, version, ORCID, title, keywords, and public-record metadata are consistent.",
    "claim_evidence_prosecutor": "Read as a claim/evidence prosecutor. Find any public claim, implication, title, abstract, heading, or summary sentence that is stronger than the visible theorem/proof/data/reviewer evidence.",
}

SEVERITY_PHASES = {
    "release_blockers": {
        "allowed_severities": ["CRITICAL", "HIGH"],
        "blocking_severities": ["CRITICAL", "HIGH"],
        "instruction": (
            "Phase 1: report only defects that should block public replacement of v1.3.3. "
            "Do not report medium, low, optional, taste, wording-polish, or nice-to-have issues. "
            "A finding is CRITICAL only if it makes the release scientifically false, misleading, non-publication-grade, "
            "or structurally invalid. A finding is HIGH only if a serious journal editor or hostile expert would reasonably "
            "stop the release until repaired. If the issue can wait for post-release polish, omit it entirely in this phase."
        ),
    },
    "major_editorial": {
        "allowed_severities": ["HIGH", "MEDIUM"],
        "blocking_severities": ["HIGH"],
        "instruction": (
            "Phase 2: the CRITICAL class is already presumed clean. Report major editorial defects that still materially "
            "affect publication quality. Do not report low-level copy edits or optional preferences."
        ),
    },
    "polish_backlog": {
        "allowed_severities": ["MEDIUM", "LOW"],
        "blocking_severities": [],
        "instruction": (
            "Phase 3: collect non-blocking polish backlog only. These findings do not block release unless they reveal a "
            "new CRITICAL/HIGH class, in which case mark that row as severity_escalation_required instead of pretending it is polish."
        ),
    },
}

CHEAP_CHUNK_CHARS = 6000

CHEAP_FIRST_LADDER = [
    {
        "tier": "L10_static_public_surface",
        "engine": "deterministic_regex_and_path_checks",
        "role": "Reject metadata leaks, malformed paths, raw generator labels, TeX filename leaks, and already-known bad wording classes before any expensive review.",
    },
    {
        "tier": "L10_governed_ollama_chunks",
        "engine": "Logion governed local LLM service",
        "role": "Inspect small reader-facing chunks for cheap prose defects, forbidden public terms, weak local readability, and local leakage under host safety policy.",
    },
    {
        "tier": "L9_chapter_aggregation",
        "engine": "deterministic aggregation plus governed local checker",
        "role": "Aggregate only clean L10 chunks into chapter/document-local findings; repeated cheap defects become static regression tests.",
    },
    {
        "tier": "L8_document_projection",
        "engine": "release assembly machine",
        "role": "Check document-level form, layout, figure/table gates, journal package projections, and source-grounding before external reasoning.",
    },
    {
        "tier": "external_cerberus_reasoning",
        "engine": "Codex/external high-reasoning review",
        "role": "Spend expensive reasoning only on conceptual vulnerabilities, scientific adequacy, argument order, claim/evidence fit, and journal-readiness.",
    },
]

CHEAP_LOCAL_PATTERNS = [
    (
        "internal_source_route_leak",
        re.compile(r"\bsource route\b|\broute sheet\b|\bcontrol sheet\b|\bcontrol-plane\b", re.I),
        "Internal route/control language belongs in ledgers, not public prose.",
    ),
    (
        "raw_generator_label_leak",
        re.compile(r"\bSynthesis checkpoint\b|\bContent:\s*Oc133\b|\bRecorded content:\b|\bPublication-grade text gate\b|\bManuscriptIntegration\b", re.I),
        "Generated labels and checkpoint prose must be translated into public scientific prose.",
    ),
    (
        "source_digest_leak",
        re.compile(r"\bsource[- ]digest\b|\bsource digest\b", re.I),
        "Source-digest wording is a construction note and must remain non-public.",
    ),
    (
        "internal_revision_leak",
        re.compile(r"\brecovery_r0\d+\b|\bR0\d{2}_VISUAL_SPEC\b|\bR0\d{2}_TABLE\b", re.I),
        "Reader-facing PDFs may not expose internal recovery or QA revision labels.",
    ),
    (
        "tex_source_reference_leak",
        re.compile(r"\b(?:content|appendix|bib|source|sources)/[A-Za-z0-9_./-]+\.tex\b", re.I),
        "Public prose may cite claims, figures, tables, and evidence rows, but not internal TeX source filenames.",
    ),
    (
        "known_malformed_visual_text",
        re.compile(r"\bR_\s+t\b|\browi\s+d\b|model_A\\?\{\}Delta", re.I),
        "Known rendered visual/formula text corruption must be repaired before global review.",
    ),
    (
        "pdf_replacement_character",
        re.compile("\ufffd"),
        "PDF text extraction contains replacement characters, so the public text layer is not reliable.",
    ),
    (
        "pdf_control_character_or_formula_corruption",
        re.compile(r"\x0f|\x16|\browId\b|\browi\s+d\b", re.I),
        "PDF text extraction contains control characters or corrupted figure/formula text.",
    ),
    (
        "clipped_public_command",
        re.compile(r"--assembly-revis\b|<pack\b", re.I),
        "A public command appears clipped in the PDF text layer and must be wrapped or reformatted.",
    ),
    (
        "clipped_public_path",
        re.compile(r"TARGET_BLIND_PR\b|COMPARATOR_MATRIX\.jso\b|FINITE_MODEL_CHECKS_1_3_\b", re.I),
        "A public evidence path appears clipped in the PDF text layer and must be reflowed into extractable prose.",
    ),
    (
        "raw_execution_protocol_id",
        re.compile(r"\bOC13::EXECUTION::|OPEN_DATA_COVERAGE_LT_1_0_OR_", re.I),
        "Long internal execution or trigger identifiers must be translated into public labels or moved to manifests.",
    ),
    (
        "closed_synthesis_or_validator_leak",
        re.compile(r"closed synthesis stack|BOUNDED_SYNTHESIS_REVIEW_RECORDED|release gate now reports|hostile-review blockers|science-state register|broader-promotion limits:\s*none remain|Core v2\.6", re.I),
        "Legacy synthesis/register/validator language must be demoted or removed before external review.",
    ),
    (
        "internal_recovery_shorthand_leak",
        re.compile(r"\br014\b", re.I),
        "Internal recovery shorthand must not appear in reader-facing prose.",
    ),
    (
        "control_placeholder_reference_leak",
        re.compile(r"corresponding evidence-package record|Appendix~?the Synthesis Support Appendix|Appendix the Synthesis Support Appendix", re.I),
        "Generated placeholder references must become concrete public citations or appendix labels.",
    ),
    (
        "domain_validation_overpromotion",
        re.compile(
            r"TRACE_COMPLETE|EVIDENCE_COMPLETE|PASS_31_OF_31_TERMINALIZED|proof-routed\s*\+\s*empirical\s*/\s*held-out validated|"
            r"held-out validated|lawfully generates?|usable now|usable-now|already cleared|bounded theorem-route|bounded theorem route|"
            r"Open gaps:\s*none|unified-synthesis naming",
            re.I,
        ),
        "Domain replay rows must be bounded review examples unless the exact support stack is visible and clean.",
    ),
    (
        "practical_utility_or_math_replay_overpromotion",
        re.compile(
            r"closed practical value|formally proved|active and replayable|blocks 0 of 5|proved Core kernel|"
            r"All live continua maintain supporting flows|Complexity grows monotonically|"
            r"(?:proof-routed|theorem-native) domain lanes are usable|operationally supported within bounds|"
            r"held-out case total|promoted (?:physics|chemistry|biological|systems|domain|systems)?\s*packet",
            re.I,
        ),
        "Practical-utility and mathematics replay language must not promote demoted rows as operational proof.",
    ),
    (
        "structural_experiment_or_legacy_law_overpromotion",
        re.compile(
            r"direct empirical grounding|foundation for all physical continua|"
            r"theorem packet is recorded|parameter law is recorded|\d+\s+covered cases;\s+\d+\s+held-out cases|"
            r"dimensional monotonicity for live continua|monotonic growth of structural complexity|"
            r"stops evolving structurally does so only at the moment of collapse",
            re.I,
        ),
        "Experiment, domain-packet, and legacy-law wording must stay scoped to proposed protocols or named proof routes.",
    ),
    (
        "unbounded_validation_wording",
        re.compile(r"empirical foundation for|civilisational-scale validation|tests cross-level invariants that hold across", re.I),
        "Experiment chapters must not promote domain validation without row-level support.",
    ),
    (
        "legacy_discussion_theorem_repromotion",
        re.compile(r"Theorem\s+\d+\s+means|Theorems\s+\d+\s+and\s+\d+\s+allow|all these domains can be analysed with a single structural toolkit", re.I),
        "Discussion chapters may interpret the theorem route, but must not re-promote historical theorem numbers as current unrestricted results.",
    ),
    (
        "experiment_validation_results_overpromotion",
        re.compile(r"empirical and computational foundation|empirically validate|experiments? (?:for\s+K\d+\s+)?validate|Predictions validated|empirical results anchor", re.I),
        "K-level experiment chapters must read as proposed protocols unless row-level source/evidence support is visible.",
    ),
    (
        "prospective_blind_replay_overclaim",
        re.compile(r"\btarget-blind replay\b|\btarget-blind table\b|\btarget-blind split\b|\btarget-blind row\b", re.I),
        "Replay wording must not imply an independently auditable prospective-blind study unless split locks, raw snapshots, timestamps, and runner records are packaged.",
    ),
    (
        "unbound_public_proof_path",
        re.compile(r"proof_sheets_public", re.I),
        "Public proof anchors must use the actual bound proof-sheet namespace.",
    ),
    (
        "legacy_k12_overclaim",
        re.compile(
            r"limit continuum|global structural fixed point|all operators\s+.*act as symmetries|entire ladder\s+K0.*K11\s+becomes representable inside one invariant continuum",
            re.I | re.S,
        ),
        "Legacy K12 wording must be demoted to bounded taxonomy/proof obligations before external review.",
    ),
    (
        "k12_m12_terminal_overclaim",
        re.compile(
            r"maximum possible value among all K-levels|most energy-stable admissible continuum|Operator algebra becomes Abelian|"
            r"Any admissible recursive meta-hierarchy eventually converges|No new axes or potentials can emerge|terminal environment for Core|terminal meta-space for the Core|necessary and sufficient for the existence of K12|"
            r"branching reaches closure|all flows are symmetry flows|no new time directions can arise|all branches close",
            re.I,
        ),
        "K12/M12 terminality, maximality, convergence, and symmetry claims must be hypothetical or proof-bounded.",
    ),
    (
        "escaped_tex_leak",
        re.compile(r"textbackslash", re.I),
        "Escaped TeX control text leaked into the public PDF text layer.",
    ),
    (
        "instruction_prose_leak",
        re.compile(r"\bthis section is included so\b|\bmust teach\b|\bpurpose and role\b|\bmachine register\b|\bcurrent maturity vector\b", re.I),
        "Instruction-to-writer prose must be translated into finished public text.",
    ),
    (
        "internal_org_boundary_leak",
        re.compile(r"\bLogion\b|\bESTRA\b", re.I),
        "Reader-facing r014 PDFs must not expose internal organization/boundary prose.",
    ),
    (
        "internal_release_process_jargon",
        re.compile(r"\brelease\s+SPOT\b|\bSPOT\s+source\b|\bquality\s+ledger\b|\bquality\s+ledgers\b|\brequirements\s+matrices\b", re.I),
        "Internal release-process jargon must be translated into public scientific or venue-facing language before external review.",
    ),
    (
        "unqualified_lean_support_wording",
        re.compile(r"\bLean-checked\s+subset\b|\bLean\s+subset\b", re.I),
        "Lean support wording must be demoted to formalization inventory unless certificate binding is clean for the cited revision.",
    ),
    (
        "unbounded_prediction_wording",
        re.compile(r"\bAll\s+phenomena\s+must\b|\bmust\s+hold\s+in\s+any\s+admissible\s+real\b|\bactive\s+bounded\s+numeric\s+packet\b", re.I),
        "Prediction and numeric-packet wording must stay bounded, not universal or promotion-like.",
    ),
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def write_text_if_changed(path: Path, text: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = text.rstrip() + "\n"
    if path.exists() and read_text(path) == normalized:
        return False
    path.write_text(normalized, encoding="utf-8", newline="\n")
    return True


def write_json_if_changed(path: Path, payload: Any) -> bool:
    return write_text_if_changed(path, json.dumps(payload, ensure_ascii=False, indent=2))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def output_dir(assembly_revision: str | None = None) -> Path:
    if assembly_revision:
        return ROOT / "releases" / RELEASE_ID / "editorial" / "quality_validation" / assembly_revision / "cerberus"
    return OUT_DIR


def summary_path(assembly_revision: str | None = None) -> Path:
    return output_dir(assembly_revision) / "OC133_EDITORIAL_CERBERUS_SUMMARY.json"


def pdf_paths(assembly_revision: str | None = None) -> dict[str, Path]:
    if not assembly_revision:
        return {key: ARTIFACTS / filename for key, filename in PDFS.items()}
    assembly_path = assembly_paths(RELEASE_ID, VERSION, assembly_revision)["assembly_json"]
    if not assembly_path.exists():
        raise FileNotFoundError(assembly_path)
    assembly = json.loads(read_text(assembly_path))
    paths: dict[str, Path] = {}
    for row in assembly.get("artifact_rows", []):
        key = ARTIFACT_KEYS.get(str(row.get("artifact_type_id")))
        if key and row.get("pdf_path"):
            paths[key] = ROOT / str(row["pdf_path"])
    return paths


def assembly_record(assembly_revision: str | None = None) -> dict[str, Any]:
    if not assembly_revision:
        return {}
    assembly_path = assembly_paths(RELEASE_ID, VERSION, assembly_revision)["assembly_json"]
    if not assembly_path.exists():
        return {}
    return json.loads(read_text(assembly_path))


def pdf_text(path: Path) -> str:
    with tempfile.TemporaryDirectory(prefix="oc133_editorial_pdf_text_") as tmp:
        txt = Path(tmp) / f"{path.stem}.txt"
        completed = subprocess.run(
            ["pdftotext", str(path), str(txt)],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=240,
        )
        if completed.returncode != 0:
            return completed.stderr
        return read_text(txt)


def short_evidence(text: str, start: int, end: int, radius: int = 160) -> str:
    excerpt = text[max(0, start - radius) : min(len(text), end + radius)]
    return re.sub(r"\s+", " ", excerpt).strip()


def cheap_public_surface_findings(artifact_key: str, filename: str, text: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for kind, pattern, description in CHEAP_LOCAL_PATTERNS:
        for match in pattern.finditer(text):
            findings.append(
                {
                    "finding_id": f"LOCAL-L10-{artifact_key}-{kind}-{len(findings)+1:03d}",
                    "severity": "HIGH",
                    "status": "OPEN",
                    "artifact": filename,
                    "role_id": "local_governed_l10_preflight",
                    "severity_phase": "release_blockers",
                    "issue": description,
                    "evidence": short_evidence(text, match.start(), match.end()),
                    "required_repair": "Repair the source-level public prose or generated figure/table text, rebuild the PDF, and rerun the cheap-first preflight before external Cerberus.",
                    "routing_tier": "L10_static_public_surface",
                    "pattern_kind": kind,
                }
            )
    return findings


def chunk_total(text: str) -> int:
    return max(1, (len(text) + CHEAP_CHUNK_CHARS - 1) // CHEAP_CHUNK_CHARS) if text.strip() else 0


def build_local_first_review(
    *,
    assembly_revision: str | None,
    assembly: dict[str, Any],
    static_findings: list[dict[str, Any]],
    packet_total: int,
) -> dict[str, Any]:
    trace = assembly.get("governed_ollama_trace") if isinstance(assembly.get("governed_ollama_trace"), dict) else {}
    service_status = str(trace.get("service_status") or trace.get("status") or "NOT_SCOPED")
    queue_status = str(trace.get("queue_status") or "NOT_SCOPED")
    ollama_invocations = int(trace.get("ollama_invocation_total") or 0)
    local_queue_pass = bool(
        assembly_revision
        and service_status == "PASS"
        and queue_status == "DONE"
        and ollama_invocations > 0
        and trace.get("unmanaged_ollama_call_total", 0) == 0
    )
    blocker_total = len(static_findings)
    status = "PASS" if blocker_total == 0 and local_queue_pass else "FAIL"
    return {
        "schema_id": "OC133_CERBERUS_CHEAP_FIRST_LOCAL_REVIEW_v1",
        "state": status,
        "assembly_revision": assembly_revision,
        "cheap_first_ladder": CHEAP_FIRST_LADDER,
        "l10_static_packet_total": packet_total,
        "l10_static_blocker_total": blocker_total,
        "local_ollama_queue_status": "PASS" if local_queue_pass else "FAIL",
        "governed_service_status": service_status,
        "governed_queue_status": queue_status,
        "ollama_invocation_total": ollama_invocations,
        "unmanaged_ollama_call_total": int(trace.get("unmanaged_ollama_call_total") or 0),
        "external_reasoning_gate_status": "PASS" if blocker_total == 0 and local_queue_pass else "BLOCKED_BY_CHEAP_FIRST_PRECHECK",
        "external_reasoning_scope": [
            "scientific adequacy and claim/evidence fit",
            "conceptual vulnerabilities and logical inconsistencies",
            "argument order, didactic completeness, and reader confidence",
            "journal-readiness and venue-facing package completeness",
        ],
        "findings": static_findings[:200],
    }


def window(text: str, needle: str, radius: int = 3500) -> str:
    idx = text.lower().find(needle.lower())
    if idx < 0:
        return ""
    return text[max(0, idx - radius) : min(len(text), idx + len(needle) + radius)]


def compact_bundle(assembly_revision: str | None = None) -> dict[str, Any]:
    docs: dict[str, Any] = {}
    paths = pdf_paths(assembly_revision)
    assembly = assembly_record(assembly_revision)
    local_findings: list[dict[str, Any]] = []
    local_packet_total = 0
    for key, filename in PDFS.items():
        path = paths.get(key, ARTIFACTS / filename)
        text = pdf_text(path) if path.exists() else ""
        local_findings.extend(cheap_public_surface_findings(key, path.name if path.exists() else filename, text))
        local_packet_total += chunk_total(text)
        excerpts = [text[:18000]]
        for needle in [
            "Abstract and Reader Contract",
            "Dedicated to my dear wife Maria",
            "ManuscriptIntegration",
            "Publication-grade text gate",
            "T133-K0-RES",
            "T133-OMEGA-STATUS",
            "target-blind",
            "Cerberus",
            "Journal Owner-Review",
            "Release Boundary",
            "Editorial Passport",
            "Literature and Prior-Art Position",
            "Visual and Design Review",
            "Audience.",
            "Purpose.",
        ]:
            item = window(text, needle)
            if item:
                excerpts.append(item)
        excerpts.append(text[-12000:])
        deduped: list[str] = []
        seen = set()
        for item in excerpts:
            digest = hashlib.sha256(item.encode("utf-8", errors="ignore")).hexdigest()
            if item and digest not in seen:
                seen.add(digest)
                deduped.append(item)
        docs[key] = {
            "filename": path.name,
            "path": str(path.relative_to(ROOT)) if path.exists() else str(path),
            "exists": path.exists(),
            "sha256": sha256_file(path) if path.exists() else None,
            "text_chars": len(text),
            "line_total": len([line for line in text.splitlines() if line.strip()]),
            "excerpt_total": len(deduped),
            "excerpts": deduped,
        }
    local_first_review = build_local_first_review(
        assembly_revision=assembly_revision,
        assembly=assembly,
        static_findings=local_findings,
        packet_total=local_packet_total,
    )
    return {
        "release_id": RELEASE_ID,
        "version": VERSION,
        "assembly_revision": assembly_revision,
        "review_scope": "publication-grade public PDF manuscript set; cheap-first local L10/L9 hygiene before external high-reasoning Cerberus review",
        "canonical_scope_policy": {
            "scoped_to": "the exact PDFs and hashes listed in this bundle plus the matching recovery package assembly record",
            "out_of_scope": "older generated_artifacts, public/postflight presentation drafts, prior release assets, publish drafts, and unrelated repository surfaces",
            "doi_policy": "reader-facing r014 PDFs intentionally print the Concept DOI only; release_record_doi remains null because no Zenodo/publication action is performed in this repair pass",
            "no_send_policy": "no GitHub, Zenodo, journal, DOI minting, or public-promotion action is part of this validation run",
        },
        "cerberus_priority_routing": {
            "schema_id": "OC133_CERBERUS_PRIORITY_ROUTING_v1",
            "policy": "cheap_local_first_then_expensive_external_reasoning",
            "cheap_first_ladder": CHEAP_FIRST_LADDER,
            "external_review_enabled": local_first_review["external_reasoning_gate_status"] == "PASS",
            "external_review_instruction": "Do not spend external reasoning on simple metadata leaks, malformed paths, raw generator labels, TeX filename leaks, or known wording classes; those are local L10/L9 obligations. External Cerberus reviews conceptual, scientific, structural, evidence, and journal-readiness risks.",
        },
        "local_first_review": local_first_review,
        "pdfs": docs,
    }


def extract_json(text: str) -> dict[str, Any]:
    stripped = text.strip()
    stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
    stripped = re.sub(r"\s*```$", "", stripped)
    decoder = json.JSONDecoder()
    errors: list[str] = []
    for match in re.finditer(r"\{", stripped):
        candidate = stripped[match.start() :]
        try:
            parsed, _end = decoder.raw_decode(candidate)
        except Exception as exc:
            errors.append(str(exc))
            continue
        if isinstance(parsed, dict):
            if parsed.get("role_id") or parsed.get("verdict") or parsed.get("findings") is not None:
                return parsed
    raise ValueError("no valid editorial JSON object in Codex output; parse attempts=" + "; ".join(errors[:5]))


def run_role(role_id: str, role_prompt: str, bundle: dict[str, Any], *, timeout: int, phase: str, out_dir: Path) -> dict[str, Any]:
    phase_policy = SEVERITY_PHASES[phase]
    prompt = {
        "task": "You are an Editorial Cerberus reviewer for OC Core 1.3.3. Review the supplied public-release manuscript bundle adversarially.",
        "role_id": role_id,
        "role_prompt": role_prompt,
        "severity_phase": phase,
        "severity_phase_policy": phase_policy,
        "cerberus_priority_routing": bundle.get("cerberus_priority_routing"),
        "local_first_review": bundle.get("local_first_review"),
        "canonical_scope_policy": bundle.get("canonical_scope_policy"),
        "routing_instruction": (
            "Respect the cheap-first hierarchy. L10/L9 metadata leaks, malformed paths, raw generator labels, forbidden public terms, "
            "and routine wording defects are handled by the governed local Ollama/static preflight. Use this external review for "
            "higher-level scientific, conceptual, structural, evidence, and journal-readiness reasoning. If a cheap class is still visible, "
            "report the class once as a blocking routing failure rather than spending the review budget on many small copies."
        ),
        "scope_instruction": (
            "Review only the scoped bundle PDFs, their hashes, and the matching recovery package assembly record supplied in the prompt. "
            "Do not turn older public-release drafts, postflight files, previous generated_artifacts, stale Zenodo/GitHub presentation files, "
            "or unrelated repository surfaces into findings. In this r014 repair pass the canonical DOI policy is Concept DOI only and "
            "release_record_doi is intentionally null because no publication action is performed."
        ),
        "acceptance_standard": [
            "Every public PDF must read as coherent scientific prose, not a route/control sheet or raw ledger dump.",
            "Every public PDF must answer: audience, topic, purpose, structure, didactic path, evidence boundary, and intended reviewer use.",
            "Every public PDF must have title/frontmatter, version, DOI, dedication to Maria, abstract/reader contract, and readable flow.",
            "The master monograph must be one integrated manuscript, not old PDF plus delta appendix.",
            "The manuscript set must contain explicit literature/prior-art positioning and a visual/figure route; inadequate references or inadequate figures are HIGH or CRITICAL if they affect publication readiness.",
            "Unsupported TOE/all-domain/superiority claims are critical findings.",
            "Follow severity_phase_policy exactly. Do not use severities outside allowed_severities for this phase.",
        ],
        "return_json_schema": {
            "role_id": role_id,
            "verdict": "PASS or FAIL",
            "severity_phase": phase,
            "critical_open_total": 0,
            "high_open_total": 0,
            "findings": [
                {
                    "finding_id": "string",
                    "severity": "|".join(phase_policy["allowed_severities"]),
                    "status": "OPEN|CLOSED",
                    "artifact": "filename",
                    "issue": "specific issue",
                    "evidence": "short evidence",
                    "required_repair": "specific repair",
                }
            ],
            "notes": "brief",
        },
        "bundle": bundle,
    }
    started = time.time()
    with tempfile.TemporaryDirectory(prefix="oc133_editorial_last_message_") as tmp:
        last_message = Path(tmp) / f"{role_id}_last_message.json"
        command = [
            "codex",
            "exec",
            "--sandbox",
            "read-only",
            "--skip-git-repo-check",
            "--output-last-message",
            str(last_message),
            "-",
        ]
        completed = subprocess.run(
            command,
            cwd=ROOT,
            input=json.dumps(prompt, ensure_ascii=False),
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=timeout,
        )
        last_text = read_text(last_message) if last_message.exists() else ""
    raw = last_text.strip() or ((completed.stdout or "") + "\n" + (completed.stderr or ""))
    parsed: dict[str, Any] | None = None
    parse_error = None
    try:
        parsed = extract_json(raw)
    except Exception as exc:
        parse_error = str(exc)
    payload = {
        "role_id": role_id,
        "severity_phase": phase,
        "command": "codex exec --sandbox read-only --skip-git-repo-check - <editorial-review-json-prompt>",
        "returncode": completed.returncode,
        "elapsed_seconds": round(time.time() - started, 3),
        "raw_output_tail": raw[-6000:],
        "transport_stdout_tail": (completed.stdout or "")[-2000:],
        "transport_stderr_tail": (completed.stderr or "")[-2000:],
        "parsed": parsed,
        "parse_error": parse_error,
        "parse_ok": parsed is not None and parse_error is None,
    }
    write_json_if_changed(out_dir / f"{role_id}.json", payload)
    return payload


def summarize(rows: list[dict[str, Any]], bundle: dict[str, Any], *, out_dir: Path) -> dict[str, Any]:
    critical = 0
    high = 0
    parse_failures = 0
    role_ids: list[str] = []
    findings: list[dict[str, Any]] = []
    omitted_out_of_phase: list[dict[str, Any]] = []
    local_first_review = bundle.get("local_first_review") if isinstance(bundle.get("local_first_review"), dict) else {}
    local_findings = local_first_review.get("findings") if isinstance(local_first_review.get("findings"), list) else []
    if local_first_review and local_first_review.get("state") != "PASS":
        findings.extend(local_findings)
        high += len(local_findings) or 1
        if not local_findings:
            findings.append(
                {
                    "finding_id": "LOCAL-L10-CHEAP-FIRST-GATE-001",
                    "severity": "HIGH",
                    "status": "OPEN",
                    "artifact": "cerberus_priority_router",
                    "role_id": "local_governed_l10_preflight",
                    "severity_phase": "release_blockers",
                    "issue": "Cheap-first local review did not clear before external Cerberus.",
                    "evidence": json.dumps(local_first_review, ensure_ascii=False)[:1000],
                    "required_repair": "Complete governed local Ollama/static L10/L9 preflight before external high-reasoning Cerberus can certify the package.",
                }
            )
    phases = sorted({str(row.get("severity_phase", "release_blockers")) for row in rows})
    for row in rows:
        row_phase = str(row.get("severity_phase", "release_blockers"))
        allowed_severities = {
            item.upper()
            for item in SEVERITY_PHASES.get(row_phase, SEVERITY_PHASES["release_blockers"])["allowed_severities"]
        }
        parsed = row.get("parsed") if isinstance(row.get("parsed"), dict) else {}
        if not row.get("parse_ok"):
            parse_failures += 1
        role_id = str(row.get("role_id"))
        role_ids.append(role_id)
        for finding in parsed.get("findings", []) if isinstance(parsed.get("findings"), list) else []:
            severity = str(finding.get("severity", "")).upper()
            status = str(finding.get("status", "OPEN")).upper()
            finding["role_id"] = role_id
            finding["severity_phase"] = row_phase
            if severity not in allowed_severities:
                omitted_out_of_phase.append(
                    {
                        "role_id": role_id,
                        "severity_phase": row_phase,
                        "severity": severity,
                        "issue": finding.get("issue"),
                        "omission_reason": "outside_current_severity_phase",
                    }
                )
                continue
            findings.append(finding)
            if status == "OPEN" and severity == "CRITICAL":
                critical += 1
            if status == "OPEN" and severity == "HIGH":
                high += 1
    pdf_hashes = {key: doc.get("sha256") for key, doc in bundle["pdfs"].items()}
    summary = {
        "schema_id": "OC133_EDITORIAL_CERBERUS_SUMMARY_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "assembly_revision": bundle.get("assembly_revision"),
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "state": "PASS" if critical == 0 and high == 0 and parse_failures == 0 else "FAIL",
        "severity_phases": phases,
        "severity_policy": {phase: SEVERITY_PHASES.get(phase) for phase in phases},
        "cerberus_priority_routing": bundle.get("cerberus_priority_routing"),
        "local_first_review": local_first_review,
        "external_reasoning_run_status": (
            "RUN"
            if local_first_review.get("external_reasoning_gate_status") == "PASS" and rows
            else "SKIPPED_BY_CHEAP_FIRST_PRECHECK"
            if local_first_review.get("external_reasoning_gate_status") != "PASS"
            else "NOT_RUN"
        ),
        "role_ids": sorted(role_ids),
        "role_total": len(role_ids),
        "critical_open_total": critical,
        "high_open_total": high,
        "parse_failure_total": parse_failures,
        "finding_total": len(findings),
        "findings": findings,
        "omitted_out_of_phase_total": len(omitted_out_of_phase),
        "omitted_out_of_phase": omitted_out_of_phase[:50],
        "waterfall_policy": {
            "active_phases": phases,
            "current_release_blocker_rule": "CRITICAL/HIGH first; no MEDIUM/LOW or taste-polish may enter the release-blocking queue.",
            "next_phase_allowed": critical == 0 and high == 0 and parse_failures == 0,
        },
        "pdf_hashes": pdf_hashes,
        "pdf_text_chars": {key: doc.get("text_chars") for key, doc in bundle["pdfs"].items()},
        "coverage_note": bundle["review_scope"],
    }
    write_json_if_changed(out_dir / "OC133_EDITORIAL_CERBERUS_SUMMARY.json", summary)
    write_text_if_changed(
        out_dir / "OC133_EDITORIAL_CERBERUS_SUMMARY.md",
        "\n".join(
            [
                "# OC Core 1.3.3 Editorial Cerberus",
                "",
                f"State: `{summary['state']}`",
                f"Roles: `{summary['role_total']}`",
                f"Critical open: `{critical}`",
                f"High open: `{high}`",
                f"Parse failures: `{parse_failures}`",
            ]
        ),
    )
    return summary


def aggregate_existing(assembly_revision: str | None = None) -> dict[str, Any]:
    out_dir = output_dir(assembly_revision)
    out_dir.mkdir(parents=True, exist_ok=True)
    bundle = compact_bundle(assembly_revision)
    write_json_if_changed(out_dir / "OC133_EDITORIAL_CERBERUS_CONTEXT_BUNDLE.json", bundle)
    rows: list[dict[str, Any]] = []
    for role_id in ROLES:
        path = out_dir / f"{role_id}.json"
        if not path.exists():
            rows.append(
                {
                    "role_id": role_id,
                    "parse_ok": False,
                    "parsed": None,
                    "parse_error": "missing role review file",
                }
            )
            continue
        rows.append(json.loads(read_text(path)))
    return summarize(rows, bundle, out_dir=out_dir)


def run(*, roles: list[str] | None = None, timeout: int = 900, phase: str = "release_blockers", assembly_revision: str | None = None) -> dict[str, Any]:
    if phase not in SEVERITY_PHASES:
        raise ValueError(f"Unknown editorial Cerberus severity phase: {phase}")
    selected = roles or list(ROLES)
    unknown = sorted(set(selected) - set(ROLES))
    if unknown:
        raise ValueError(f"Unknown editorial Cerberus roles: {', '.join(unknown)}")
    out_dir = output_dir(assembly_revision)
    out_dir.mkdir(parents=True, exist_ok=True)
    bundle = compact_bundle(assembly_revision)
    write_json_if_changed(out_dir / "OC133_EDITORIAL_CERBERUS_CONTEXT_BUNDLE.json", bundle)
    local_first_review = bundle.get("local_first_review") if isinstance(bundle.get("local_first_review"), dict) else {}
    if local_first_review.get("external_reasoning_gate_status") != "PASS":
        return summarize([], bundle, out_dir=out_dir)
    rows = [run_role(role_id, ROLES[role_id], bundle, timeout=timeout, phase=phase, out_dir=out_dir) for role_id in selected]
    return summarize(rows, bundle, out_dir=out_dir)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run OC Core 1.3.3 editorial Cerberus LLM review.")
    parser.add_argument("--role", action="append", default=[])
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--phase", choices=sorted(SEVERITY_PHASES), default="release_blockers")
    parser.add_argument("--assembly-revision")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--aggregate-existing", action="store_true")
    args = parser.parse_args(argv)
    if args.check:
        path = summary_path(args.assembly_revision)
        payload = json.loads(read_text(path)) if path.exists() else {"state": "FAIL", "reason": "missing summary", "path": str(path)}
    elif args.aggregate_existing:
        payload = aggregate_existing(args.assembly_revision)
    else:
        payload = run(roles=args.role or None, timeout=args.timeout, phase=args.phase, assembly_revision=args.assembly_revision)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload.get("state") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
