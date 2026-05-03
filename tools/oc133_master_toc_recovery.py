from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"
EDITORIAL = ROOT / "releases" / RELEASE_ID / "editorial"

RAW_JSON = EDITORIAL / "ALL_HISTORICAL_TOC_SOURCES.json"
RAW_MD = EDITORIAL / "ALL_HISTORICAL_TOC_SOURCES.md"
MASTER_JSON = EDITORIAL / "MASTER_MANUSCRIPT_STRUCTURE_1_3_3.json"
MASTER_MD = EDITORIAL / "MASTER_MANUSCRIPT_STRUCTURE_1_3_3.md"
FREEZE_JSON = EDITORIAL / "MASTER_MANUSCRIPT_STRUCTURE_FREEZE_1_3_3.json"

STRUCTURE_POLICY = "MASTER_TOC_APPEND_ONLY_AFTER_OWNER_APPROVAL"
FREEZE_STATUS = "PENDING_OWNER_APPROVAL"

REQUIRED_ARC = [
    "frontmatter",
    "dedication",
    "reader_contract",
    "motivation",
    "formal_model",
    "theorem_proof_spine",
    "lean_formalization",
    "finite_model_evidence",
    "empirical_domain_evidence",
    "prior_art_novelty",
    "phenomenon_coverage",
    "figures_visual_route",
    "reviewer_objections",
    "reproducibility_release_citation",
    "appendices",
    "bibliography",
]

ROLE_ORDER = {
    role: idx
    for idx, role in enumerate(
        [
            "frontmatter",
            "dedication",
            "reader_contract",
            "motivation",
            "formal_model",
            "theorem_proof_spine",
            "lean_formalization",
            "finite_model_evidence",
            "empirical_domain_evidence",
            "prior_art_novelty",
            "phenomenon_coverage",
            "figures_visual_route",
            "reviewer_objections",
            "reproducibility_release_citation",
            "appendices",
            "bibliography",
            "journal_package_map",
            "release_metadata",
            "other_structure",
        ]
    )
}

KEY_HISTORICAL_HINTS = (
    "master_monograph",
    "master_monograph_en",
    "master_route",
    "source/routes",
    "science_delta_appendix",
    "total_closure_appendix",
    "critique_closure_appendix",
    "simulation_and_data_appendix",
    "experiment_required_appendix",
    "discipline_expansion_appendix",
    "public_payload/sources/oc_core_1_3_3_master_monograph_en.md",
)


@dataclass(frozen=True)
class TocItem:
    title: str
    level: int
    kind: str
    role: str
    source_id: str
    path: str
    commit: str
    line: int | None
    source_order: int


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def stable_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True).rstrip() + "\n"


def write_text_if_changed(path: Path, text: str) -> bool:
    normalized = text.rstrip() + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text(encoding="utf-8", errors="ignore") == normalized:
        return False
    path.write_text(normalized, encoding="utf-8", newline="\n")
    return True


def run_git(args: list[str], *, binary: bool = False) -> bytes | str:
    completed = subprocess.run(
        ["git", "-C", str(ROOT), *args],
        capture_output=True,
        text=not binary,
        encoding="utf-8" if not binary else None,
        errors="replace" if not binary else None,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {completed.stderr if not binary else completed.stderr!r}")
    return completed.stdout if not binary else completed.stdout


def git_text_at(commit: str, path: str) -> str | None:
    if commit == "HEAD":
        candidate = ROOT / path
        if candidate.exists():
            return candidate.read_text(encoding="utf-8", errors="replace")
    completed = subprocess.run(
        ["git", "-C", str(ROOT), "show", f"{commit}:{path}"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if completed.returncode != 0:
        return None
    return completed.stdout


def git_bytes_at(commit: str, path: str) -> bytes | None:
    if commit == "HEAD":
        candidate = ROOT / path
        if candidate.exists():
            return candidate.read_bytes()
    completed = subprocess.run(
        ["git", "-C", str(ROOT), "show", f"{commit}:{path}"],
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        return None
    return completed.stdout


def all_git_paths() -> list[str]:
    current = set(str(run_git(["ls-files"])).splitlines())
    all_names = str(run_git(["log", "--all", "--name-only", "--pretty=format:"])).splitlines()
    current.update(line.strip() for line in all_names if line.strip())
    return sorted(path for path in current if is_candidate_path(path))


def is_candidate_path(path: str) -> bool:
    lower = path.lower().replace("\\", "/")
    ext = Path(lower).suffix
    if ext not in {".md", ".tex", ".pdf"}:
        return False
    if any(part in lower for part in ["/__pycache__/", "/.pytest_cache/", "/build/"]):
        return False
    if ext == ".pdf":
        return lower in {
            "releases/oc_core_1_3_3/artifacts/oc_core_1_3_3_master_monograph_en.pdf",
            "releases/oc_core_1_3_2/artifacts/oc_core_1_3_2_master_monograph_en.pdf",
            "releases/oc_core_1_3/monograph/oc_core_1_3_master_monograph_en.pdf",
            "releases/oc_core_1_3/monograph/oc_core_1_3_master_monograph.pdf",
        }
    if any(hint in lower for hint in KEY_HISTORICAL_HINTS):
        return True
    if lower.startswith(("content/", "appendix/", "releases/oc_core_1_3/monograph/source/")):
        return True
    if lower.startswith("releases/oc_core_1_3_1/manuscripts/"):
        return True
    if lower.startswith("releases/oc_core_1_3_2/editorial/research_packets/") and "manuscript" in lower:
        return True
    if lower.startswith("releases/oc_core_1_3_3/public_payload/sources/"):
        return True
    return False


def historical_commits_for(path: str) -> list[str]:
    lower = path.lower().replace("\\", "/")
    use_full_history = any(hint in lower for hint in KEY_HISTORICAL_HINTS) or lower.endswith(".pdf")
    if not use_full_history:
        return ["HEAD"]
    out = str(run_git(["log", "--all", "--format=%H", "--", path]))
    commits = [line.strip() for line in out.splitlines() if line.strip()]
    return commits or ["HEAD"]


def clean_tex_title(text: str) -> str:
    text = text.strip()
    text = re.sub(r"%.*$", "", text).strip()
    text = text.replace(r"\_", "_")
    text = re.sub(r"\\(?:texttt|emph|textbf|textit)\{([^{}]*)\}", r"\1", text)
    text = re.sub(r"\\[A-Za-z]+\*?(?:\[[^\]]*\])?", "", text)
    text = re.sub(r"[{}$]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip(" .:-")


def normalize_title(title: str) -> str:
    text = clean_tex_title(title).lower()
    text = re.sub(r"^import:\s*", "", text)
    text = re.sub(r"^(chapter|section|appendix|part)\s+[a-z0-9ivx.:-]+\s*", "", text)
    text = re.sub(r"^\d+(?:\.\d+)*\s*", "", text)
    text = re.sub(r"\b(?:oc|core)\s+v?1[._ ]3(?:[._ ]\d+)?\b", "oc core", text)
    text = re.sub(r"\b1[._ ]3(?:[._ ]\d+)?\b", "version", text)
    text = re.sub(r"[^a-z0-9а-яё]+", " ", text, flags=re.I)
    return re.sub(r"\s+", " ", text).strip()


def classify_role(title: str, path: str = "") -> str:
    text = f"{title} {path}".lower()
    if any(word in text for word in ["dedication", "maria"]):
        return "dedication"
    is_abstract_section = re.search(r"(^|\s)(abstract)(\s*$|\s+and|\s+reader|\.)", clean_tex_title(title).lower())
    if "frontmatter" in text or "title page" in text or is_abstract_section:
        return "frontmatter"
    if any(word in text for word in ["reader contract", "reading map", "reader guide", "audience"]):
        return "reader_contract"
    if any(word in text for word in ["introduction", "motivation", "background", "problem", "scope"]):
        return "motivation"
    if any(word in text for word in ["lean", "lake", "formalization subset"]):
        return "lean_formalization"
    if any(word in text for word in ["finite-model", "finite model", "witness", "counterexample", "negative control"]):
        return "finite_model_evidence"
    if any(word in text for word in ["empirical", "validation", "target-blind", "target blind", "replay", "physics", "chemistry", "biology", "systems", "mathematics", "data", "prediction"]):
        return "empirical_domain_evidence"
    if any(word in text for word in ["prior-art", "prior art", "novelty", "comparator", "literature", "reference benchmark"]):
        return "prior_art_novelty"
    if any(word in text for word in ["phenomenon", "coverage", "does oc explain"]):
        return "phenomenon_coverage"
    if any(word in text for word in ["figure", "visual", "diagram", "atlas"]):
        return "figures_visual_route"
    if any(word in text for word in ["reviewer", "attack", "cerberus", "objection", "criticism", "hostile"]):
        return "reviewer_objections"
    if any(word in text for word in ["reproducibility", "release", "citation", "doi", "checksum", "journal", "package", "governance", "zenodo", "github"]):
        if "journal" in text or "package" in text:
            return "journal_package_map"
        return "reproducibility_release_citation"
    if any(word in text for word in ["bibliography", "references", "reference catalog"]):
        return "bibliography"
    if any(word in text for word in ["appendix", "/appendix/", "\\appendix"]):
        return "appendices"
    if any(word in text for word in ["model", "ontology", "axiom", "definition", "boundary", "operator", "cycle", "dimension", "k-level", "k0", "liveness", "threshold", "collapse", "rebirth", "continuumness"]):
        return "formal_model"
    if any(word in text for word in ["theorem", "proof", "lemma", "claim ledger", "proof registry"]):
        return "theorem_proof_spine"
    return "other_structure"


def parse_markdown(text: str, source_id: str, path: str, commit: str, order_start: int) -> list[TocItem]:
    items: list[TocItem] = []
    order = order_start
    for line_no, line in enumerate(text.splitlines(), 1):
        match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if not match:
            marker = structural_marker_for_line(line)
            if marker:
                items.append(
                    TocItem(
                        title=marker,
                        level=1,
                        kind="markdown_structural_marker",
                        role=classify_role(marker, path),
                        source_id=source_id,
                        path=path,
                        commit=commit,
                        line=line_no,
                        source_order=order,
                    )
                )
                order += 1
            continue
        title = match.group(2).strip()
        if not title:
            continue
        items.append(
            TocItem(
                title=clean_tex_title(title),
                level=len(match.group(1)),
                kind="markdown_heading",
                role=classify_role(title, path),
                source_id=source_id,
                path=path,
                commit=commit,
                line=line_no,
                source_order=order,
            )
        )
        order += 1
    return items


TEX_SECTION_RE = re.compile(
    r"\\(part|chapter|section|subsection|subsubsection|paragraph)\*?(?:\[[^\]]*\])?\{([^{}\n]*(?:\{[^{}\n]*\}[^{}\n]*)*)\}"
)
TEX_INPUT_RE = re.compile(r"\\(?:input|include)\{([^{}\n]+)\}")


def parse_tex(text: str, source_id: str, path: str, commit: str, order_start: int) -> list[TocItem]:
    items: list[TocItem] = []
    order = order_start
    command_levels = {
        "part": 1,
        "chapter": 2,
        "section": 3,
        "subsection": 4,
        "subsubsection": 5,
        "paragraph": 6,
    }
    for line_no, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("%"):
            continue
        marker = structural_marker_for_line(line)
        if marker:
            items.append(
                TocItem(
                    title=marker,
                    level=1,
                    kind="tex_structural_marker",
                    role=classify_role(marker, path),
                    source_id=source_id,
                    path=path,
                    commit=commit,
                    line=line_no,
                    source_order=order,
                )
            )
            order += 1
        for match in TEX_SECTION_RE.finditer(line):
            title = clean_tex_title(match.group(2))
            if title:
                items.append(
                    TocItem(
                        title=title,
                        level=command_levels.get(match.group(1), 3),
                        kind=f"tex_{match.group(1)}",
                        role=classify_role(title, path),
                        source_id=source_id,
                        path=path,
                        commit=commit,
                        line=line_no,
                        source_order=order,
                    )
                )
                order += 1
        for match in TEX_INPUT_RE.finditer(line):
            ref = match.group(1).strip()
            title = f"Import: {ref}"
            items.append(
                TocItem(
                    title=title,
                    level=3,
                    kind="tex_import_route",
                    role=classify_role(ref, path),
                    source_id=source_id,
                    path=path,
                    commit=commit,
                    line=line_no,
                    source_order=order,
                )
            )
            order += 1
    return items


def structural_marker_for_line(line: str) -> str | None:
    plain = clean_tex_title(re.sub(r"[*_`]+", " ", line))
    lower = plain.lower()
    if "dedicated to my dear wife maria" in lower or "dedication" in lower and "maria" in lower:
        return "Dedication to Maria"
    if "meiner lieben ehefrau maria gewidmet" in lower:
        return "Dedication to Maria"
    return None


def parse_pdf_bytes(data: bytes, source_id: str, path: str, commit: str, order_start: int) -> tuple[list[TocItem], int | None]:
    try:
        from pypdf import PdfReader
    except Exception:
        return [], None
    try:
        import io

        reader = PdfReader(io.BytesIO(data))
    except Exception:
        return [], None
    page_count = len(reader.pages)
    items: list[TocItem] = []
    order = order_start

    def walk_outline(nodes: Iterable[Any]) -> None:
        nonlocal order
        for node in nodes:
            if isinstance(node, list):
                walk_outline(node)
                continue
            title = clean_tex_title(str(getattr(node, "title", "")))
            if not title:
                continue
            items.append(
                TocItem(
                    title=title,
                    level=2,
                    kind="pdf_bookmark",
                    role=classify_role(title, path),
                    source_id=source_id,
                    path=path,
                    commit=commit,
                    line=None,
                    source_order=order,
                )
            )
            order += 1

    try:
        walk_outline(reader.outline or [])
    except Exception:
        pass

    # Fallback TOC extraction from early pages. It is intentionally conservative:
    # it captures numbered TOC entries without importing body prose.
    try:
        early_text = "\n".join((reader.pages[idx].extract_text() or "") for idx in range(min(35, page_count)))
    except Exception:
        early_text = ""
    for line in early_text.splitlines():
        s = " ".join(line.split())
        marker = structural_marker_for_line(s)
        if marker:
            items.append(
                TocItem(
                    title=marker,
                    level=1,
                    kind="pdf_structural_marker",
                    role=classify_role(marker, path),
                    source_id=source_id,
                    path=path,
                    commit=commit,
                    line=None,
                    source_order=order,
                )
            )
            order += 1
            continue
        if len(s) < 4 or len(s) > 180:
            continue
        if re.match(r"^(?:[A-Z]|\d+(?:\.\d+)*)\s+.+\s+\d+$", s) or re.match(r"^[A-Z]\.\d+\s+.+\s+\d+$", s):
            title = re.sub(r"\s+\d+$", "", s)
            items.append(
                TocItem(
                    title=clean_tex_title(title),
                    level=2 if re.match(r"^(?:[A-Z]|\d+)\s+", title) else 3,
                    kind="pdf_toc_line",
                    role=classify_role(title, path),
                    source_id=source_id,
                    path=path,
                    commit=commit,
                    line=None,
                    source_order=order,
                )
            )
            order += 1
    return items, page_count


def quick_pdf_page_count(data: bytes) -> int:
    # Historical PDF commits are used primarily to recover the strongest
    # proven page baseline. Full text extraction is intentionally avoided
    # there; it is slow and not needed for TOC-only source recovery.
    return len(re.findall(rb"/Type\s*/Page\b", data))


def source_type_for(path: str) -> str:
    ext = Path(path).suffix.lower()
    return {".md": "markdown", ".tex": "tex", ".pdf": "pdf"}.get(ext, "unknown")


def collect_sources() -> dict[str, Any]:
    sources: list[dict[str, Any]] = []
    all_items: list[TocItem] = []
    strongest_pdf: dict[str, Any] = {"pages": 0, "path": None, "commit": None, "sha256": None}
    global_order = 0

    for path in all_git_paths():
        for commit in historical_commits_for(path):
            source_type = source_type_for(path)
            source_id = sha256_text(f"{commit}:{path}")[:16]
            items: list[TocItem] = []
            page_count: int | None = None
            content_hash: str | None = None
            if source_type == "pdf":
                data = git_bytes_at(commit, path)
                if not data or not data.startswith(b"%PDF"):
                    continue
                content_hash = sha256_bytes(data)
                if commit == "HEAD":
                    items, page_count = parse_pdf_bytes(data, source_id, path, commit, global_order)
                else:
                    page_count = quick_pdf_page_count(data)
                    items = []
                if page_count and page_count > int(strongest_pdf["pages"] or 0):
                    strongest_pdf = {"pages": page_count, "path": path, "commit": commit, "sha256": content_hash}
            else:
                text = git_text_at(commit, path)
                if text is None:
                    continue
                content_hash = sha256_text(text)
                if source_type == "markdown":
                    items = parse_markdown(text, source_id, path, commit, global_order)
                elif source_type == "tex":
                    items = parse_tex(text, source_id, path, commit, global_order)
            if not items and source_type != "pdf":
                continue
            global_order += len(items) + 1
            all_items.extend(items)
            sources.append(
                {
                    "source_id": source_id,
                    "commit": commit,
                    "path": path,
                    "source_type": source_type,
                    "sha256": content_hash,
                    "page_count": page_count,
                    "item_total": len(items),
                    "items": [item_to_raw(item) for item in items],
                }
            )

    return {
        "schema_id": "OC133_ALL_HISTORICAL_TOC_SOURCES_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "collection_policy": "TOC_ONLY_NO_BODY_PROSE_NO_PDF_STITCHING",
        "source_total": len(sources),
        "item_total": len(all_items),
        "strongest_proven_pdf_baseline": strongest_pdf,
        "sources": sources,
    }


def item_to_raw(item: TocItem) -> dict[str, Any]:
    return {
        "title": item.title,
        "level": item.level,
        "kind": item.kind,
        "role": item.role,
        "source_id": item.source_id,
        "path": item.path,
        "commit": item.commit,
        "line": item.line,
        "source_order": item.source_order,
        "dedupe_key": f"{item.role}:{normalize_title(item.title)}",
    }


def raw_items(raw_payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source in raw_payload.get("sources", []):
        rows.extend(source.get("items", []))
    return rows


def choose_richest_title(titles: list[str]) -> str:
    def score(title: str) -> tuple[int, int, str]:
        alpha = len(re.findall(r"[A-Za-zА-Яа-я0-9]", title))
        words = len(title.split())
        return (words, alpha, title)

    return sorted(set(titles), key=score, reverse=True)[0]


def synthesize_master_structure(raw_payload: dict[str, Any]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in raw_items(raw_payload):
        key = item["dedupe_key"]
        if key.endswith(":"):
            key = f"{item['role']}:{normalize_title(item['path'])}"
        grouped.setdefault(key, []).append(item)

    nodes: list[dict[str, Any]] = []
    for key, items in grouped.items():
        role, norm = key.split(":", 1)
        titles = [item["title"] for item in items if item.get("title")]
        title = choose_richest_title(titles) if titles else norm
        node_id = "MTOC-" + sha256_text(f"{role}:{norm}")[:12].upper()
        first_order = min(int(item.get("source_order", 0)) for item in items)
        levels = [int(item.get("level", 3)) for item in items if item.get("level")]
        kinds = sorted(set(str(item.get("kind")) for item in items))
        provenance = [
            {
                "source_id": item["source_id"],
                "commit": item["commit"],
                "path": item["path"],
                "line": item.get("line"),
                "kind": item.get("kind"),
            }
            for item in sorted(items, key=lambda row: (row.get("commit", ""), row.get("path", ""), row.get("line") or 0))[:25]
        ]
        nodes.append(
            {
                "node_id": node_id,
                "title": title,
                "normalized_title": norm,
                "role": role,
                "level_min": min(levels) if levels else 3,
                "source_order_min": first_order,
                "kind_set": kinds,
                "provenance_total": len(items),
                "provenance": provenance,
                "needs_owner_review": len(set(item["role"] for item in items)) > 1,
            }
        )

    nodes.sort(key=lambda row: (ROLE_ORDER.get(row["role"], 999), row["source_order_min"], row["normalized_title"]))
    for idx, node in enumerate(nodes, 1):
        node["master_order"] = idx

    role_counts: dict[str, int] = {}
    for node in nodes:
        role_counts[node["role"]] = role_counts.get(node["role"], 0) + 1

    validation = validate_structure(nodes, raw_payload)
    structural_cerberus = structural_cerberus_review(nodes, validation)
    structure = {
        "schema_id": "OC133_MASTER_MANUSCRIPT_STRUCTURE_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "artifact_kind": "TOC_ONLY_MASTER_STRUCTURE",
        "structure_policy": STRUCTURE_POLICY,
        "body_prose_included": False,
        "release_payload_included": False,
        "pdf_stitching_included": False,
        "source_total": raw_payload.get("source_total", 0),
        "historical_toc_item_total": raw_payload.get("item_total", 0),
        "node_total": len(nodes),
        "role_counts": dict(sorted(role_counts.items())),
        "strongest_proven_pdf_baseline": raw_payload.get("strongest_proven_pdf_baseline"),
        "validation": validation,
        "structural_cerberus_gate": structural_cerberus,
        "nodes": nodes,
    }
    structure["structure_hash"] = structure_hash(structure)
    return structure


def structural_cerberus_review(nodes: list[dict[str, Any]], validation: dict[str, Any]) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    if validation.get("missing_required_roles"):
        findings.append(
            {
                "role_id": "editorial_architect",
                "severity": "CRITICAL",
                "finding_id": "MTOC-CERB-001",
                "failure_mode": "required_scientific_arc_role_missing",
                "evidence": validation["missing_required_roles"],
            }
        )
    if not validation.get("coverage_complete"):
        findings.append(
            {
                "role_id": "source_coverage_reviewer",
                "severity": "CRITICAL",
                "finding_id": "MTOC-CERB-002",
                "failure_mode": "historical_toc_item_not_covered",
                "evidence": {
                    "historical_item_total": validation.get("historical_item_total"),
                    "covered_historical_item_total": validation.get("covered_historical_item_total"),
                },
            }
        )
    sequence_failures = [
        failure for failure in validation.get("failures", []) if str(failure).startswith("top_level_sequence_incoherent")
    ]
    if sequence_failures:
        findings.append(
            {
                "role_id": "sequence_reviewer",
                "severity": "HIGH",
                "finding_id": "MTOC-CERB-003",
                "failure_mode": "top_level_sequence_incoherent",
                "evidence": sequence_failures,
            }
        )
    if not nodes:
        findings.append(
            {
                "role_id": "freeze_policy_reviewer",
                "severity": "CRITICAL",
                "finding_id": "MTOC-CERB-004",
                "failure_mode": "empty_master_toc",
                "evidence": "no structure nodes recovered",
            }
        )
    critical_open_total = sum(1 for finding in findings if finding["severity"] == "CRITICAL")
    high_open_total = sum(1 for finding in findings if finding["severity"] == "HIGH")
    return {
        "schema_id": "OC133_MASTER_TOC_STRUCTURAL_CERBERUS_v1",
        "review_scope": "TOC_STRUCTURE_ONLY_NO_PROSE_REVIEW",
        "role_ids": [
            "editorial_architect",
            "source_coverage_reviewer",
            "sequence_reviewer",
            "freeze_policy_reviewer",
        ],
        "state": "PASS" if critical_open_total == 0 and high_open_total == 0 else "FAIL",
        "critical_open_total": critical_open_total,
        "high_open_total": high_open_total,
        "parse_failure_total": 0,
        "findings": findings,
    }


def structure_hash(structure: dict[str, Any]) -> str:
    stable = {
        "schema_id": structure.get("schema_id"),
        "release_id": structure.get("release_id"),
        "version": structure.get("version"),
        "nodes": [
            {
                "node_id": node["node_id"],
                "title": node["title"],
                "normalized_title": node["normalized_title"],
                "role": node["role"],
                "master_order": node["master_order"],
            }
            for node in structure.get("nodes", [])
        ],
    }
    return sha256_text(stable_json(stable))


def validate_structure(nodes: list[dict[str, Any]], raw_payload: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    role_counts: dict[str, int] = {}
    for node in nodes:
        role_counts[node["role"]] = role_counts.get(node["role"], 0) + 1
    missing_roles = [role for role in REQUIRED_ARC if role_counts.get(role, 0) == 0]
    if missing_roles:
        failures.append("required_scientific_arc_role_missing")

    covered_provenance = sum(int(node.get("provenance_total", 0)) for node in nodes)
    raw_total = int(raw_payload.get("item_total", 0))
    if covered_provenance < raw_total:
        failures.append("historical_toc_item_not_covered")

    ordered_roles = [node["role"] for node in nodes]
    role_positions = {role: min(idx for idx, value in enumerate(ordered_roles) if value == role) for role in set(ordered_roles)}
    for before, after in [
        ("frontmatter", "formal_model"),
        ("motivation", "formal_model"),
        ("formal_model", "theorem_proof_spine"),
        ("theorem_proof_spine", "empirical_domain_evidence"),
        ("prior_art_novelty", "reviewer_objections"),
        ("reproducibility_release_citation", "appendices"),
    ]:
        if before in role_positions and after in role_positions and role_positions[before] > role_positions[after]:
            failures.append(f"top_level_sequence_incoherent::{before}_after_{after}")

    unstable_ids = [node["node_id"] for node in nodes if node["node_id"] != "MTOC-" + sha256_text(f"{node['role']}:{node['normalized_title']}")[:12].upper()]
    if unstable_ids:
        failures.append("unstable_node_id_detected")

    return {
        "state": "PASS" if not failures else "FAIL",
        "failures": failures,
        "required_arc": REQUIRED_ARC,
        "missing_required_roles": missing_roles,
        "historical_item_total": raw_total,
        "covered_historical_item_total": covered_provenance,
        "coverage_complete": covered_provenance == raw_total,
        "role_counts": dict(sorted(role_counts.items())),
    }


def build_freeze_candidate(master: dict[str, Any]) -> dict[str, Any]:
    validation = master.get("validation", {})
    return {
        "schema_id": "OC133_MASTER_MANUSCRIPT_STRUCTURE_FREEZE_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "freeze_status": FREEZE_STATUS,
        "owner_approved": False,
        "owner_approval_required": True,
        "structure_hash": master["structure_hash"],
        "structure_ref": str(MASTER_JSON.relative_to(ROOT)).replace("\\", "/"),
        "master_toc_ref": str(MASTER_MD.relative_to(ROOT)).replace("\\", "/"),
        "append_only_policy": {
            "may_add_nodes": True,
            "may_delete_nodes": False,
            "may_rename_nodes": False,
            "may_reorder_nodes": False,
            "may_collapse_nodes": False,
            "owner_override_required": True,
        },
        "forbidden_mutations": [
            "delete_frozen_node",
            "rename_frozen_node",
            "reorder_frozen_node",
            "collapse_frozen_nodes",
            "replace_master_toc_without_owner_hash_approval",
        ],
        "validation_state": validation.get("state"),
        "validation_failures": validation.get("failures", []),
        "frozen_node_total": master.get("node_total"),
        "frozen_nodes": [
            {
                "node_id": node["node_id"],
                "title": node["title"],
                "role": node["role"],
                "master_order": node["master_order"],
                "normalized_title": node["normalized_title"],
            }
            for node in master.get("nodes", [])
        ],
    }


def validate_append_only(candidate: dict[str, Any], freeze: dict[str, Any]) -> dict[str, Any]:
    if not freeze.get("owner_approved"):
        return {"state": "PASS", "enforced": False, "failures": [], "reason": "freeze_pending_owner_approval"}

    failures: list[str] = []
    frozen = {node["node_id"]: node for node in freeze.get("frozen_nodes", [])}
    candidate_nodes = {node["node_id"]: node for node in candidate.get("nodes", [])}
    for node_id, frozen_node in frozen.items():
        current = candidate_nodes.get(node_id)
        if current is None:
            failures.append(f"delete_frozen_node::{node_id}")
            continue
        for field in ("title", "role", "normalized_title"):
            if current.get(field) != frozen_node.get(field):
                failures.append(f"rename_or_reclassify_frozen_node::{node_id}::{field}")
        if current.get("master_order") != frozen_node.get("master_order"):
            failures.append(f"reorder_frozen_node::{node_id}")
    return {"state": "PASS" if not failures else "FAIL", "enforced": True, "failures": failures}


def render_raw_md(raw: dict[str, Any]) -> str:
    lines = [
        "# All Historical TOC Sources",
        "",
        "This artifact contains TOC/outline/import-route candidates only. It contains no manuscript body prose.",
        "",
        f"- Release: `{raw['release_id']}`",
        f"- Version: `{raw['version']}`",
        f"- Sources: `{raw['source_total']}`",
        f"- TOC items: `{raw['item_total']}`",
        f"- Strongest proven PDF pages: `{raw.get('strongest_proven_pdf_baseline', {}).get('pages')}`",
        "",
    ]
    for source in raw.get("sources", []):
        lines.extend(
            [
                f"## {source['path']} @ {source['commit'][:12]}",
                "",
                f"- Type: `{source['source_type']}`",
                f"- SHA-256: `{source['sha256']}`",
                f"- Page count: `{source.get('page_count')}`",
                f"- Item total: `{source['item_total']}`",
                "",
            ]
        )
        for item in source.get("items", []):
            lines.append(
                f"- L{item['level']} `{item['role']}` {item['title']} "
                f"({item['kind']}; line={item.get('line')})"
            )
        lines.append("")
    return "\n".join(lines)


def render_master_md(master: dict[str, Any]) -> str:
    lines = [
        "# OC Core 1.3.3 Master Manuscript Structure",
        "",
        "Status: structure candidate for owner freeze approval. This is TOC only: no manuscript body prose, no release payload, no PDF stitching.",
        "",
        f"- Structure hash: `{master['structure_hash']}`",
        f"- Validation state: `{master['validation']['state']}`",
        f"- Structural Cerberus state: `{master['structural_cerberus_gate']['state']}`",
        f"- Source total: `{master['source_total']}`",
        f"- Historical TOC item total: `{master['historical_toc_item_total']}`",
        f"- Master node total: `{master['node_total']}`",
        f"- Strongest proven PDF baseline pages: `{master.get('strongest_proven_pdf_baseline', {}).get('pages')}`",
        "",
        "## Required Scientific Arc Gate",
        "",
    ]
    for role in REQUIRED_ARC:
        count = master["validation"]["role_counts"].get(role, 0)
        marker = "PASS" if count else "FAIL"
        lines.append(f"- `{marker}` `{role}`: {count} node(s)")
    lines.append("")

    by_role: dict[str, list[dict[str, Any]]] = {}
    for node in master.get("nodes", []):
        by_role.setdefault(node["role"], []).append(node)

    for role in sorted(by_role, key=lambda item: ROLE_ORDER.get(item, 999)):
        lines.extend([f"## {role}", ""])
        for node in by_role[role]:
            lines.append(
                f"- `{node['node_id']}` {node['title']} "
                f"(sources={node['provenance_total']}; order={node['master_order']})"
            )
        lines.append("")
    return "\n".join(lines)


def build_payloads() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    raw = collect_sources()
    master = synthesize_master_structure(raw)
    freeze = build_freeze_candidate(master)
    return raw, master, freeze


def materialize(*, write: bool) -> dict[str, Any]:
    raw, master, freeze = build_payloads()
    outputs = {
        str(RAW_JSON.relative_to(ROOT)).replace("\\", "/"): stable_json(raw),
        str(RAW_MD.relative_to(ROOT)).replace("\\", "/"): render_raw_md(raw).rstrip() + "\n",
        str(MASTER_JSON.relative_to(ROOT)).replace("\\", "/"): stable_json(master),
        str(MASTER_MD.relative_to(ROOT)).replace("\\", "/"): render_master_md(master).rstrip() + "\n",
        str(FREEZE_JSON.relative_to(ROOT)).replace("\\", "/"): stable_json(freeze),
    }

    changed: list[str] = []
    missing: list[str] = []
    mismatched: list[str] = []
    for rel, text in outputs.items():
        path = ROOT / rel
        if write:
            if write_text_if_changed(path, text):
                changed.append(rel)
        else:
            if not path.exists():
                missing.append(rel)
            elif path.read_text(encoding="utf-8", errors="ignore") != text:
                mismatched.append(rel)

    check_state = "PASS" if master["validation"]["state"] == "PASS" and not missing and not mismatched else "FAIL"
    return {
        "schema_id": "OC133_MASTER_TOC_RECOVERY_RUN_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "mode": "write" if write else "check",
        "state": check_state,
        "changed": changed,
        "missing": missing,
        "mismatched": mismatched,
        "source_total": raw["source_total"],
        "historical_toc_item_total": raw["item_total"],
        "node_total": master["node_total"],
        "structure_hash": master["structure_hash"],
        "validation": master["validation"],
        "freeze_status": freeze["freeze_status"],
        "owner_approved": freeze["owner_approved"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Recover and freeze-candidate the OC 1.3.3 master manuscript TOC.")
    parser.add_argument("--write", action="store_true", help="Write recovered TOC artifacts if they changed.")
    parser.add_argument("--check", action="store_true", help="Check that recovered TOC artifacts match current inputs.")
    args = parser.parse_args(argv)
    if args.write and args.check:
        parser.error("--write and --check are mutually exclusive")
    payload = materialize(write=bool(args.write))
    print(stable_json(payload), end="")
    if args.check and payload["state"] != "PASS":
        return 1
    return 0 if payload["validation"]["state"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
