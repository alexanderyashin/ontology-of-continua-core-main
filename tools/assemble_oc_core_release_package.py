from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import unicodedata
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Any

from build_oc133_science_to_l10_mapping import mapping_paths
from build_oc_core_artifact_generation_rules import CONCEPT_DOI, generation_paths
from build_oc_core_current_release_aggregator import aggregator_paths
from build_oc_core_l10_quality_projection_matrix import projection_paths
from build_oc_core_release_instance import instance_paths
from build_oc_core_release_package_cascade import package_paths
from build_oc_core_text_fill_rules import rules_paths
from oc_core_release_assembly_lib import ROOT, artifact_hash, read_json, relative, stable_json, write_text_if_changed

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from release_machine.versioning import version_from_release_id


ASSEMBLY_STATUS = "OC_CORE_RELEASE_PACKAGE_REVIEW_ARTIFACTS_ASSEMBLED"
ASSEMBLY_KIND = "OC_CORE_RELEASE_PACKAGE_ASSEMBLY"
PUBLICATION_FORBIDDEN_RE = re.compile(
    r"github release|zenodo deposit|tag movement|doi mint|journal submission|publish_allowed\s*[:=]\s*false|no_send",
    re.IGNORECASE,
)
RAW_LEDGER_RE = re.compile(r"\{\s*\"schema_id\"|route sheet|control sheet|raw ledger|checksum wall", re.IGNORECASE)
RELEASE_RECORD_DOI_RE = re.compile(r"10\.5281/zenodo\.(?!17899134)\d+", re.IGNORECASE)
CYRILLIC_RE = re.compile(r"[\u0400-\u04FF]")
RECOVERED_L10C = ROOT / "releases" / "oc_core_1_3_3" / "editorial" / "recovery" / "OC_CORE_1_3_3_TOC_L10C_RECOVERED.json"
OLD_MASTER_BASELINE_PAGES = 650


TEXT_ARTIFACTS = {
    "release_guide",
    "master_monograph",
    "journal_core_article",
    "methods_repro_companion",
    "reviewer_attack_response_map",
}


def generated_dir(release_id: str, assembly_revision: str | None = None) -> Path:
    if assembly_revision:
        return ROOT / "releases" / release_id / "editorial" / "generated_artifacts_recovered" / assembly_revision
    return ROOT / "releases" / release_id / "editorial" / "generated_artifacts"


def assembly_paths(release_id: str, version: str, assembly_revision: str | None = None) -> dict[str, Path]:
    base = generated_dir(release_id, assembly_revision)
    assembly_dir = base / "package_assembly"
    return {
        "terminal_contracts_json": base / "terminal_text" / f"OC_CORE_TERMINAL_TEXT_CONTRACTS_{version}.json",
        "terminal_contracts_md": base / "terminal_text" / f"OC_CORE_TERMINAL_TEXT_CONTRACTS_{version}.md",
        "transition_records_json": base / "transitions" / f"OC_CORE_TRANSITION_RECORDS_{version}.json",
        "transition_records_md": base / "transitions" / f"OC_CORE_TRANSITION_RECORDS_{version}.md",
        "source_bindings_json": base / "source_bindings" / f"OC_CORE_SOURCE_BINDINGS_{version}.json",
        "source_bindings_md": base / "source_bindings" / f"OC_CORE_SOURCE_BINDINGS_{version}.md",
        "manifest_json": base / "package" / f"OC_CORE_RELEASE_PACKAGE_MANIFEST_{version}.json",
        "checksums_txt": base / "package" / f"OC_CORE_RELEASE_PACKAGE_CHECKSUMS_{version}.txt",
        "assembly_json": assembly_dir / f"OC_CORE_RELEASE_PACKAGE_ASSEMBLY_{version}.json",
        "assembly_md": assembly_dir / f"OC_CORE_RELEASE_PACKAGE_ASSEMBLY_{version}.md",
        "audit_json": assembly_dir / f"OC_CORE_RELEASE_PACKAGE_ASSEMBLY_AUDIT_{version}.json",
        "audit_md": assembly_dir / f"OC_CORE_RELEASE_PACKAGE_ASSEMBLY_AUDIT_{version}.md",
        "review_zip": base / "package" / f"oc_core_release_review_package_{version}.zip",
    }


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json_if_changed(path: Path, payload: dict[str, Any]) -> bool:
    return write_text_if_changed(path, stable_json(payload))


def rel(path: Path) -> str:
    return relative(path)


def order_key(node: dict[str, Any]) -> tuple[int, ...]:
    return tuple(int(part) for part in node.get("order_path", []))


CYRILLIC_TRANSLIT = str.maketrans(
    {
        "А": "A", "Б": "B", "В": "V", "Г": "G", "Д": "D", "Е": "E", "Ё": "E", "Ж": "Zh", "З": "Z",
        "И": "I", "Й": "I", "К": "K", "Л": "L", "М": "M", "Н": "N", "О": "O", "П": "P",
        "Р": "R", "С": "S", "Т": "T", "У": "U", "Ф": "F", "Х": "Kh", "Ц": "Ts", "Ч": "Ch",
        "Ш": "Sh", "Щ": "Sch", "Ъ": "", "Ы": "Y", "Ь": "", "Э": "E", "Ю": "Yu", "Я": "Ya",
        "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e", "ж": "zh", "з": "z",
        "и": "i", "й": "i", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p",
        "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f", "х": "kh", "ц": "ts", "ч": "ch",
        "ш": "sh", "щ": "sch", "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
    }
)
PUBLIC_TEXT_REPLACEMENTS = {
    "–": "-",
    "—": "-",
    "−": "-",
    "→": "->",
    "←": "<-",
    "↔": "<->",
    "≤": "<=",
    "≥": ">=",
    "≈": "~",
    "∞": "infinity",
    "∑": "sum",
    "∏": "product",
    "∈": "in",
    "∉": "not in",
    "∅": "empty set",
    "⊂": "subset",
    "⊆": "subset or equal",
    "⊇": "superset or equal",
    "∧": "and",
    "∨": "or",
    "¬": "not",
    "∀": "for all",
    "∃": "exists",
    "α": "alpha",
    "β": "beta",
    "γ": "gamma",
    "δ": "delta",
    "θ": "theta",
    "λ": "lambda",
    "μ": "mu",
    "π": "pi",
    "σ": "sigma",
    "φ": "phi",
    "ω": "omega",
    "Α": "Alpha",
    "Β": "Beta",
    "Γ": "Gamma",
    "Δ": "Delta",
    "Θ": "Theta",
    "Λ": "Lambda",
    "Μ": "Mu",
    "Π": "Pi",
    "Σ": "Sigma",
    "Φ": "Phi",
    "Ω": "Omega",
}


def public_text(text: str) -> str:
    text = text.translate(CYRILLIC_TRANSLIT)
    for source, target in PUBLIC_TEXT_REPLACEMENTS.items():
        text = text.replace(source, target)
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def clean_title(title: str) -> str:
    text = title.replace("Paragraph Slot:", "").strip()
    text = re.sub(r"\s+", " ", text)
    text = text.replace(" and state its reader task", "")
    text = text.replace(" and hand off to the next obligation", "")
    text = public_text(text)
    return text[0].upper() + text[1:] if text else "Local obligation"


def source_inventory_by_family() -> dict[str, list[str]]:
    inventory = read_json(mapping_paths()["inventory_json"])
    rows: dict[str, list[str]] = {}
    for family in inventory.get("source_families", []):
        rows[family["id"]] = [path for path in family.get("matched_paths_sample", []) if isinstance(path, str)]
    return rows


def bind_sources(node: dict[str, Any], inventory: dict[str, list[str]]) -> list[dict[str, Any]]:
    if node.get("source_refs"):
        return [ref for ref in node["source_refs"] if isinstance(ref, dict)]
    refs: list[dict[str, Any]] = []
    seen: set[str] = set()
    for family_id in node.get("source_family_ids", []):
        for ref in inventory.get(family_id, [])[:3]:
            if ref in seen:
                continue
            seen.add(ref)
            path = ROOT / ref
            refs.append(
                {
                    "source_family_id": family_id,
                    "path": ref,
                    "exists": path.is_file(),
                    "sha256": sha256_file(path) if path.is_file() else None,
                }
            )
            if len(refs) >= 6:
                return refs
    return refs


def source_families_for_node(node: dict[str, Any]) -> list[str]:
    families = [str(item) for item in node.get("source_family_ids", []) if item]
    if families:
        return families
    return sorted({str(ref.get("source_family_id")) for ref in node.get("source_refs", []) if isinstance(ref, dict) and ref.get("source_family_id")})


def build_transition_text(current: dict[str, Any], next_node: dict[str, Any] | None) -> str:
    if next_node is None:
        return "This closes the current release-assembly route and leaves no extra unsupported claim behind."
    current_role = current.get("argument_role") or "local"
    next_role = next_node.get("argument_role") or "local"
    if current_role == "definition_model" and next_role == "proof_evidence":
        return "With the object named, the next move is to expose the support route instead of relying on assertion."
    if current_role == "proof_evidence" and next_role == "limits_falsifier":
        return "The support route only becomes reviewable when its boundary, falsifier, and negative side are visible."
    if current_role == "limits_falsifier" and next_role == "synthesis_transition":
        return "Once the boundary is explicit, the manuscript may synthesize the local consequence without inflating it."
    if current_role == "synthesis_transition" and next_role == "definition_model":
        return "The next obligation begins by defining the next object before asking the reader to accept claims about it."
    return "The next paragraph continues the same scientific route while preserving source trace and claim boundary."


def build_terminal_paragraph(node: dict[str, Any], source_refs: list[dict[str, Any]], transition_out: str) -> str:
    topic = public_text(clean_title(str(node.get("title", ""))))
    role = str(node.get("argument_role") or "definition_model")
    reader_task = public_text(str(node.get("reader_task") or "understand the local scientific obligation"))
    claim_boundary = public_text(str(node.get("claim_boundary") or "keep the statement bounded to the named evidence route"))
    source_families = ", ".join(str(item).replace("_", " ") for item in source_families_for_node(node)[:3])
    source_phrase = source_families or "the mapped scientific source families"
    if role == "definition_model":
        body = (
            f"{topic} is introduced here as a reader-facing obligation, not as a file name or process label. "
            f"The reader task is to {reader_task}. The paragraph draws on {source_phrase} and states the local vocabulary "
            f"before any proof, replay, or comparison is allowed to carry weight. Its boundary is conservative: {claim_boundary}."
        )
    elif role == "proof_evidence":
        body = (
            f"{topic} carries the evidential burden for the surrounding claim. The release text must show how the reader moves "
            f"from prose to proof, finite semantics, replay material, comparator evidence, or source trace. The mapped route uses "
            f"{source_phrase}; exact paths and hashes stay in the source trace so the paragraph remains readable. The support is "
            f"promoted only as far as this boundary permits: {claim_boundary}."
        )
    elif role == "limits_falsifier":
        body = (
            f"{topic} states what would make the local claim weaker, false, incomplete, or research-only. The release cannot use "
            f"the presence of evidence as permission to overstate scope. It must name the falsifier, negative control, reviewer "
            f"objection, or residual risk carried by {source_phrase}. The governing boundary is: {claim_boundary}."
        )
    else:
        body = (
            f"{topic} synthesizes the local route for the reader. It states what has been established, what remains bounded, and "
            f"why the next section follows. The synthesis draws on {source_phrase} but does not add new scientific strength beyond "
            f"the evidence already named. The boundary remains: {claim_boundary}."
        )
    return body + " " + transition_out


def terminal_nodes_for_source(structure_source: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if structure_source == "current":
        aggregator = read_json(aggregator_paths()["aggregator_json"])
        nodes = sorted([node for node in aggregator["nodes"] if node.get("terminal_l10") is True], key=order_key)
        return nodes, {
            "structure_source": "current",
            "current_release_aggregator_hash": aggregator["artifact_hash"],
        }
    if structure_source == "recovered_l10c":
        l10c = read_json(RECOVERED_L10C)
        nodes = sorted(l10c["nodes"], key=lambda row: int(row.get("order_index", 0)))
        return nodes, {
            "structure_source": "recovered_l10c",
            "l10c_recovered_hash": l10c["artifact_hash"],
        }
    raise ValueError(f"Unsupported structure source: {structure_source}")


def build_terminal_contracts(structure_source: str = "current") -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    terminal_nodes, structure_hashes = terminal_nodes_for_source(structure_source)
    inventory = source_inventory_by_family()
    contracts: list[dict[str, Any]] = []
    transition_records: list[dict[str, Any]] = []
    for index, node in enumerate(terminal_nodes):
        next_node = terminal_nodes[index + 1] if index + 1 < len(terminal_nodes) else None
        transition_out = build_transition_text(node, next_node)
        source_refs = bind_sources(node, inventory)
        buildable = bool(node.get("reader_task") and node.get("claim_boundary") and source_refs and node.get("argument_role"))
        title_raw = str(node["title"])
        title_public = public_text(title_raw)
        contract = {
            "aggregator_node_id": node["aggregator_node_id"],
            "target_node_id": node.get("target_node_id") or node.get("l10c_node_id"),
            "order_label": node.get("order_label") or "/".join(str(part) for part in node.get("order_path", [])),
            "order_path": node["order_path"],
            "title": title_public,
            "source_title_requires_translation": bool(CYRILLIC_RE.search(title_raw)),
            "clean_title": public_text(str(node.get("clean_title") or clean_title(str(node["title"])))),
            "argument_role": node.get("argument_role"),
            "reader_task": public_text(str(node.get("reader_task") or "")),
            "claim_boundary": public_text(str(node.get("claim_boundary") or "")),
            "source_refs": source_refs,
            "transformation_rule": public_text(str(node.get("integration_rule") or node.get("extraction_rule") or "")),
            "transition_in": "Continue the inherited top-down manuscript route without modifying frozen parent structure.",
            "transition_out": transition_out,
            "quality_scorer_hooks": [
                "coverage.target_obligation",
                "trace.exact_source_binding",
                "claim.boundary_discipline",
                "didactic.reader_task_payoff",
                "structure.sequence_transition",
                "public.no_overclaim_surface",
            ],
            "generated_text": build_terminal_paragraph(node, source_refs, transition_out) if buildable else "",
            "build_state": "BUILDABLE" if buildable else "BLOCKED_MISSING_CONTRACT_FIELD",
            "source_layer": node.get("source_layer") or structure_source,
            "recovery_node": node.get("source_layer") == "l10b_recovered",
        }
        contracts.append(contract)
        if next_node is not None:
            transition_records.append(
                {
                    "transition_id": f"TRANS-{node['aggregator_node_id']}-TO-{next_node['aggregator_node_id']}",
                    "from_node_id": node["aggregator_node_id"],
                    "to_node_id": next_node["aggregator_node_id"],
                    "from_role": node.get("argument_role"),
                    "to_role": next_node.get("argument_role"),
                    "transition_text": transition_out,
                    "transition_scope": "terminal",
                }
            )
    contracts_payload: dict[str, Any] = {
        "schema_id": "OC_CORE_TERMINAL_TEXT_CONTRACTS_v1",
        "artifact_kind": "OC_CORE_TERMINAL_TEXT_CONTRACTS",
        "status": "TERMINAL_TEXT_CONTRACTS_READY",
        "source_hashes": {
            **structure_hashes,
            "terminal_text_rules_hash": read_json(generation_paths()["terminal_rules_json"])["artifact_hash"],
        },
        "structure_source": structure_source,
        "terminal_node_total": len(terminal_nodes),
        "buildable_terminal_total": sum(1 for row in contracts if row["build_state"] == "BUILDABLE"),
        "blocked_terminal_total": sum(1 for row in contracts if row["build_state"] != "BUILDABLE"),
        "terminal_contracts": contracts,
    }
    contracts_payload["artifact_hash"] = artifact_hash(contracts_payload)
    transitions_payload: dict[str, Any] = {
        "schema_id": "OC_CORE_TRANSITION_RECORDS_v1",
        "artifact_kind": "OC_CORE_TRANSITION_RECORDS",
        "status": "TRANSITION_RECORDS_READY",
        "source_hashes": {
            "terminal_text_contracts_hash": contracts_payload["artifact_hash"],
            "transition_rules_hash": read_json(generation_paths()["transition_rules_json"])["artifact_hash"],
        },
        "terminal_node_total": len(terminal_nodes),
        "transition_record_total": len(transition_records),
        "transition_records": transition_records,
    }
    transitions_payload["artifact_hash"] = artifact_hash(transitions_payload)
    source_payload: dict[str, Any] = {
        "schema_id": "OC_CORE_SOURCE_BINDINGS_v1",
        "artifact_kind": "OC_CORE_SOURCE_BINDINGS",
        "status": "SOURCE_BINDINGS_READY",
        "source_family_total": len(inventory),
        "source_families": [
            {"source_family_id": key, "candidate_path_total": len(value), "candidate_paths": value[:20]}
            for key, value in sorted(inventory.items())
        ],
        "terminal_source_binding_total": sum(len(row["source_refs"]) for row in contracts),
    }
    source_payload["artifact_hash"] = artifact_hash(source_payload)
    return contracts_payload, transitions_payload, [source_payload]


def render_contracts_md(payload: dict[str, Any]) -> str:
    lines = [
        "# OC Core Terminal Text Contracts",
        "",
        f"Status: `{payload['status']}`",
        f"Artifact hash: `{payload['artifact_hash']}`",
        f"Terminal nodes: `{payload['terminal_node_total']}`",
        f"Buildable terminals: `{payload['buildable_terminal_total']}`",
        "",
    ]
    for row in payload["terminal_contracts"]:
        lines.append(f"## {row['order_label']} {row['clean_title']}")
        lines.append(f"- Node: `{row['aggregator_node_id']}`")
        lines.append(f"- Role: `{row['argument_role']}`")
        lines.append(f"- Build state: `{row['build_state']}`")
        lines.append(f"- Reader task: {row['reader_task']}")
        lines.append(f"- Claim boundary: {row['claim_boundary']}")
        lines.append(f"- Source refs: {len(row['source_refs'])}")
        lines.append("")
    return "\n".join(lines)


def render_transitions_md(payload: dict[str, Any]) -> str:
    lines = [
        "# OC Core Transition Records",
        "",
        f"Status: `{payload['status']}`",
        f"Artifact hash: `{payload['artifact_hash']}`",
        f"Transition records: `{payload['transition_record_total']}`",
        "",
    ]
    for row in payload["transition_records"][:120]:
        lines.append(f"- `{row['from_node_id']}` -> `{row['to_node_id']}`: {row['transition_text']}")
    if payload["transition_record_total"] > 120:
        lines.append(f"- ... {payload['transition_record_total'] - 120} additional terminal transitions recorded in JSON.")
    return "\n".join(lines)


def render_source_bindings_md(payload: dict[str, Any]) -> str:
    lines = ["# OC Core Source Bindings", "", f"Status: `{payload['status']}`", f"Artifact hash: `{payload['artifact_hash']}`", ""]
    for family in payload["source_families"]:
        lines.append(f"## `{family['source_family_id']}`")
        lines.append(f"Candidate paths: `{family['candidate_path_total']}`")
        lines.append("")
        for path in family["candidate_paths"][:10]:
            lines.append(f"- `{path}`")
        lines.append("")
    return "\n".join(lines)


def artifact_scope(artifact_type_id: str, contracts: list[dict[str, Any]], structure_source: str = "current") -> list[dict[str, Any]]:
    if artifact_type_id == "master_monograph":
        return contracts
    l1_scopes = {
        "release_guide": {1, 2, 18, 19},
        "journal_core_article": {2, 3, 4, 5, 7, 9, 10, 11, 13, 14, 19},
        "methods_repro_companion": {5, 10, 11, 17, 18},
        "reviewer_attack_response_map": {2, 13, 14, 16, 18},
    }.get(artifact_type_id)
    if not l1_scopes:
        return []
    scoped = [row for row in contracts if int(row["order_path"][0]) in l1_scopes]
    if structure_source == "recovered_l10c":
        recovered = [row for row in contracts if row.get("recovery_node")]
        if artifact_type_id == "release_guide":
            keywords = ["frontmatter", "release", "citation", "governance", "synthesis"]
            extra_limit = 500
        elif artifact_type_id == "journal_core_article":
            keywords = ["model", "theorem", "proof", "evidence", "prior", "novelty"]
            extra_limit = 1500
        elif artifact_type_id == "methods_repro_companion":
            keywords = ["method", "lean", "finite", "validation", "reproduc", "simulation"]
            extra_limit = 1400
        else:
            keywords = ["review", "attack", "limit", "fals", "counterexample", "risk"]
            extra_limit = 1200
        selected = [
            row for row in recovered
            if any(keyword in (row.get("clean_title", "") + " " + row.get("title", "")).lower() for keyword in keywords)
        ][:extra_limit]
        return scoped + selected
    return scoped[: min(len(scoped), 160)]


def artifact_title(artifact_type_id: str, version: str) -> str:
    titles = {
        "release_guide": "OC Core Release Guide",
        "master_monograph": "OC Core Master Monograph",
        "journal_core_article": "OC Core Journal Core Article",
        "methods_repro_companion": "OC Core Methods and Reproducibility Companion",
        "reviewer_attack_response_map": "OC Core Reviewer Attack and Response Map",
        "release_notes_changelog": "OC Core Release Notes and Changelog",
    }
    return f"{titles.get(artifact_type_id, artifact_type_id.replace('_', ' ').title())} v{version}"


def render_artifact_markdown(artifact_type_id: str, version: str, instance: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    title = artifact_title(artifact_type_id, version)
    lines = [
        f"# {title}",
        "",
        f"Version: `{version}`",
        f"Concept DOI for PDF citation: `{CONCEPT_DOI}`",
        "Author: Alexander Yashin",
        "",
        "## Abstract",
        "",
        "This review-space artifact is assembled from the current OC Core release aggregator, science-to-structure mapping, package cascade, terminal text contracts, and deterministic transition rules. It is not a GitHub or Zenodo publication action.",
        "",
        "## Reader Contract",
        "",
        "Read this document as an assembled scientific route. Claims are bounded by their proof, evidence, replay, comparator, or falsifier route; unsupported all-domain or superiority claims are not promoted by package assembly.",
        "",
    ]
    current_l1: int | None = None
    current_l2: tuple[int, int] | None = None
    for row in rows:
        order_path = [int(part) for part in row["order_path"]]
        if current_l1 != order_path[0]:
            current_l1 = order_path[0]
            lines.extend(["", f"## Block {current_l1}", ""])
        l2 = (order_path[0], order_path[1] if len(order_path) > 1 else 0)
        if current_l2 != l2:
            current_l2 = l2
            lines.extend(["", f"### {row['clean_title'].split(' and ')[0]}", ""])
        lines.append(row["generated_text"])
        lines.append("")
    lines.extend(
        [
            "## Source Trace",
            "",
            "Exact source bindings, path hashes, quality scorer hooks, and transition records are recorded in the generated artifact package manifest. They are kept out of the main prose to avoid turning the document into a ledger dump.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def build_pdf(source: Path, output: Path) -> dict[str, Any]:
    output.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "pandoc",
        str(source),
        "-o",
        str(output),
        "--pdf-engine=xelatex",
        "-V",
        "geometry:margin=1in",
        "-V",
        "fontsize=11pt",
    ]
    completed = subprocess.run(cmd, cwd=ROOT, text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=240)
    return {
        "command": " ".join(cmd),
        "returncode": completed.returncode,
        "ok": completed.returncode == 0 and output.is_file(),
        "stdout_tail": completed.stdout[-1200:],
        "stderr_tail": completed.stderr[-1200:],
        "output": rel(output) if output.exists() else rel(output),
        "sha256": sha256_file(output) if output.is_file() else None,
        "size_bytes": output.stat().st_size if output.is_file() else 0,
        "pages": pdf_pages(output) if output.is_file() else 0,
    }


def pdf_pages(path: Path) -> int:
    if not path.is_file():
        return 0
    try:
        completed = subprocess.run(
            ["pdfinfo", str(path)],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=30,
        )
        match = re.search(r"^Pages:\s*(\d+)\s*$", completed.stdout, re.M)
        if match:
            return int(match.group(1))
    except Exception:
        return 0
    return 0


def write_review_zip(zip_path: Path, files: list[Path]) -> dict[str, Any]:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(files, key=lambda item: rel(item)):
            if not path.is_file() or path.resolve() == zip_path.resolve():
                continue
            info = zipfile.ZipInfo(rel(path), date_time=(2026, 5, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, path.read_bytes())
    return {"path": rel(zip_path), "sha256": sha256_file(zip_path), "size_bytes": zip_path.stat().st_size}


def assemble_release(
    release_id: str,
    *,
    write: bool,
    skip_pdf: bool = False,
    structure_source: str = "current",
    assembly_revision: str | None = None,
) -> dict[str, Any]:
    version = version_from_release_id(release_id)
    paths = assembly_paths(release_id, version, assembly_revision)
    instance = read_json(instance_paths(release_id, version)["instance_json"])
    package = read_json(package_paths()["cascade_json"])
    profile = read_json(generation_paths()["profile_json"])
    terminal_contracts, transitions, source_payloads = build_terminal_contracts(structure_source)
    source_bindings = source_payloads[0]
    generated_files: list[Path] = []
    changed: list[str] = []
    if write:
        changed.extend(
            [
                rel(path)
                for path, payload in [
                    (paths["terminal_contracts_json"], terminal_contracts),
                    (paths["transition_records_json"], transitions),
                    (paths["source_bindings_json"], source_bindings),
                ]
                if write_json_if_changed(path, payload)
            ]
        )
        for path, text in [
            (paths["terminal_contracts_md"], render_contracts_md(terminal_contracts)),
            (paths["transition_records_md"], render_transitions_md(transitions)),
            (paths["source_bindings_md"], render_source_bindings_md(source_bindings)),
        ]:
            if write_text_if_changed(path, text):
                changed.append(rel(path))
    terminal_rows = terminal_contracts["terminal_contracts"]
    artifact_rows: list[dict[str, Any]] = []
    for artifact in package["artifact_types"]:
        artifact_id = artifact["artifact_type_id"]
        base = generated_dir(release_id, assembly_revision)
        source_path = base / "sources" / f"{artifact_id}_{version}.md"
        pdf_path = base / "pdf" / f"{artifact_id}_{version}.pdf"
        json_path = base / "metadata" / f"{artifact_id}_{version}.json"
        output_paths: list[str] = []
        if artifact_id in TEXT_ARTIFACTS or artifact_id == "release_notes_changelog":
            rows = artifact_scope(artifact_id, terminal_rows, structure_source)
            if artifact_id == "release_notes_changelog":
                rows = artifact_scope("release_guide", terminal_rows, structure_source)[:80]
            text = render_artifact_markdown(artifact_id, version, instance, rows)
            source_changed = False
            if write and write_text_if_changed(source_path, text):
                source_changed = True
                changed.append(rel(source_path))
            generated_files.append(source_path)
            output_paths.append(rel(source_path))
            pdf_build = None
            if artifact_id in TEXT_ARTIFACTS and not skip_pdf:
                if write and (source_changed or not pdf_path.is_file()):
                    pdf_build = build_pdf(source_path, pdf_path)
                else:
                    pdf_build = {
                        "ok": pdf_path.is_file(),
                        "output": rel(pdf_path),
                        "sha256": sha256_file(pdf_path) if pdf_path.is_file() else None,
                        "size_bytes": pdf_path.stat().st_size if pdf_path.is_file() else 0,
                        "pages": pdf_pages(pdf_path) if pdf_path.is_file() else 0,
                    }
                if pdf_path.is_file():
                    generated_files.append(pdf_path)
                    output_paths.append(rel(pdf_path))
            artifact_rows.append(
                {
                    "artifact_type_id": artifact_id,
                    "output_kind": "markdown_and_pdf" if artifact_id in TEXT_ARTIFACTS else "markdown",
                    "source_path": rel(source_path),
                    "pdf_path": rel(pdf_path) if artifact_id in TEXT_ARTIFACTS else None,
                    "terminal_node_total": len(rows),
                    "output_paths": output_paths,
                    "pdf_build": pdf_build,
                }
            )
        elif artifact_id == "public_evidence_bundle":
            payload = {
                "schema_id": "OC_CORE_PUBLIC_EVIDENCE_BUNDLE_REVIEW_v1",
                "release_id": release_id,
                "version": version,
                "terminal_text_contracts_hash": terminal_contracts["artifact_hash"],
                "transition_records_hash": transitions["artifact_hash"],
                "source_bindings_hash": source_bindings["artifact_hash"],
                "concept_doi": CONCEPT_DOI,
            }
            payload["artifact_hash"] = artifact_hash(payload)
            if write and write_json_if_changed(json_path, payload):
                changed.append(rel(json_path))
            generated_files.append(json_path)
            artifact_rows.append({"artifact_type_id": artifact_id, "output_kind": "json_bundle_seed", "output_paths": [rel(json_path)], "terminal_node_total": terminal_contracts["terminal_node_total"]})
        elif artifact_id in {"integrity_manifest", "citation_metadata"}:
            payload = {
                "schema_id": f"OC_CORE_{artifact_id.upper()}_REVIEW_v1",
                "release_id": release_id,
                "version": version,
                "concept_doi": CONCEPT_DOI,
                "release_record_doi": None,
                "source_hashes": {
                    "release_instance_hash": instance["artifact_hash"],
                    "package_cascade_hash": package["artifact_hash"],
                    "artifact_generation_profile_hash": profile["artifact_hash"],
                },
            }
            payload["artifact_hash"] = artifact_hash(payload)
            if write and write_json_if_changed(json_path, payload):
                changed.append(rel(json_path))
            generated_files.append(json_path)
            artifact_rows.append({"artifact_type_id": artifact_id, "output_kind": "metadata_json", "output_paths": [rel(json_path)], "terminal_node_total": 0})
    generated_files.extend([paths["terminal_contracts_json"], paths["terminal_contracts_md"], paths["transition_records_json"], paths["transition_records_md"], paths["source_bindings_json"], paths["source_bindings_md"]])
    manifest_rows = []
    for path in sorted({path for path in generated_files if path.is_file()}, key=lambda item: rel(item)):
        manifest_rows.append({"path": rel(path), "sha256": sha256_file(path), "size_bytes": path.stat().st_size})
    manifest: dict[str, Any] = {
        "schema_id": "OC_CORE_RELEASE_PACKAGE_MANIFEST_v1",
        "artifact_kind": "OC_CORE_RELEASE_PACKAGE_MANIFEST",
        "status": "REVIEW_SPACE_MANIFEST_READY",
        "release_id": release_id,
        "version": version,
        "concept_doi": CONCEPT_DOI,
        "release_record_doi": None,
        "source_hashes": {
            "release_instance_hash": instance["artifact_hash"],
            "terminal_text_contracts_hash": terminal_contracts["artifact_hash"],
            "transition_records_hash": transitions["artifact_hash"],
            "source_bindings_hash": source_bindings["artifact_hash"],
            "artifact_generation_profile_hash": profile["artifact_hash"],
            "quality_projection_matrix_hash": read_json(projection_paths()["matrix_json"])["artifact_hash"],
            "text_fill_rules_hash": read_json(rules_paths()["rules_json"])["artifact_hash"],
        },
        "file_total": len(manifest_rows),
        "files": manifest_rows,
    }
    manifest["artifact_hash"] = artifact_hash(manifest)
    checksums = "\n".join(f"{row['sha256']}  {row['path']}" for row in manifest_rows) + "\n"
    if write:
        if write_json_if_changed(paths["manifest_json"], manifest):
            changed.append(rel(paths["manifest_json"]))
        if write_text_if_changed(paths["checksums_txt"], checksums):
            changed.append(rel(paths["checksums_txt"]))
        generated_files.extend([paths["manifest_json"], paths["checksums_txt"]])
    zip_payload = write_review_zip(paths["review_zip"], generated_files) if write else {
        "path": rel(paths["review_zip"]),
        "sha256": sha256_file(paths["review_zip"]) if paths["review_zip"].is_file() else None,
        "size_bytes": paths["review_zip"].stat().st_size if paths["review_zip"].is_file() else 0,
    }
    assembly: dict[str, Any] = {
        "schema_id": "OC_CORE_RELEASE_PACKAGE_ASSEMBLY_v1",
        "artifact_kind": ASSEMBLY_KIND,
        "status": ASSEMBLY_STATUS,
        "release_identity": instance["release_identity"],
        "concept_doi": CONCEPT_DOI,
        "release_record_doi": None,
        "publication_actions_performed": False,
        "structure_source": structure_source,
        "assembly_revision": assembly_revision,
        "source_hashes": {
            "release_instance_hash": instance["artifact_hash"],
            "current_release_aggregator_hash": read_json(aggregator_paths()["aggregator_json"])["artifact_hash"],
            "package_cascade_hash": package["artifact_hash"],
            "artifact_generation_profile_hash": profile["artifact_hash"],
            "terminal_text_contracts_hash": terminal_contracts["artifact_hash"],
            "transition_records_hash": transitions["artifact_hash"],
            "source_bindings_hash": source_bindings["artifact_hash"],
            "manifest_hash": manifest["artifact_hash"],
            "l10c_recovered_hash": read_json(RECOVERED_L10C)["artifact_hash"] if structure_source == "recovered_l10c" else None,
        },
        "summary": {
            "terminal_node_total": terminal_contracts["terminal_node_total"],
            "buildable_terminal_total": terminal_contracts["buildable_terminal_total"],
            "blocked_terminal_total": terminal_contracts["blocked_terminal_total"],
            "transition_record_total": transitions["transition_record_total"],
            "artifact_type_total": len(artifact_rows),
            "manifest_file_total": manifest["file_total"],
        },
        "artifact_rows": artifact_rows,
        "review_zip": zip_payload,
    }
    assembly["artifact_hash"] = artifact_hash(assembly)
    audit = build_audit_payload(assembly)
    if write:
        if write_json_if_changed(paths["assembly_json"], assembly):
            changed.append(rel(paths["assembly_json"]))
        if write_text_if_changed(paths["assembly_md"], render_assembly_md(assembly)):
            changed.append(rel(paths["assembly_md"]))
        if write_json_if_changed(paths["audit_json"], audit):
            changed.append(rel(paths["audit_json"]))
        if write_text_if_changed(paths["audit_md"], render_audit_md(audit)):
            changed.append(rel(paths["audit_md"]))
    state = "PASS" if audit["status"] == "PASS" else "FAIL"
    return {"state": state, "changed": sorted(set(changed)), "assembly": assembly, "audit": audit}


def scan_text(path: Path) -> list[str]:
    if not path.is_file() or path.suffix.lower() not in {".md", ".json", ".txt"}:
        return []
    text = path.read_text(encoding="utf-8", errors="replace")
    failures = []
    if PUBLICATION_FORBIDDEN_RE.search(text):
        failures.append(f"publication_control_language::{rel(path)}")
    if RAW_LEDGER_RE.search(text):
        failures.append(f"raw_ledger_or_control_sheet_language::{rel(path)}")
    if RELEASE_RECORD_DOI_RE.search(text):
        failures.append(f"release_record_doi_in_package_build::{rel(path)}")
    return failures


def build_audit_payload(assembly: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    summary = assembly["summary"]
    if summary["blocked_terminal_total"] != 0:
        failures.append("terminal_contracts_blocked")
    if summary["transition_record_total"] != max(summary["terminal_node_total"] - 1, 0):
        failures.append("transition_record_total_mismatch")
    if assembly.get("concept_doi") != CONCEPT_DOI:
        failures.append("concept_doi_mismatch")
    if assembly.get("release_record_doi") is not None:
        failures.append("release_record_doi_present_in_package_build")
    if assembly.get("publication_actions_performed") is not False:
        failures.append("publication_action_flag_mismatch")
    for row in assembly.get("artifact_rows", []):
        if not row.get("output_paths"):
            failures.append(f"artifact_has_no_output::{row.get('artifact_type_id')}")
        for output in row.get("output_paths", []):
            path = ROOT / output
            if not path.is_file():
                failures.append(f"artifact_output_missing::{output}")
            failures.extend(scan_text(path))
        pdf_build = row.get("pdf_build")
        if row.get("output_kind") == "markdown_and_pdf" and (not pdf_build or not pdf_build.get("ok")):
            failures.append(f"pdf_build_failed::{row.get('artifact_type_id')}")
        if (
            assembly.get("structure_source") == "recovered_l10c"
            and row.get("artifact_type_id") == "master_monograph"
            and row.get("output_kind") == "markdown_and_pdf"
            and int((pdf_build or {}).get("pages") or 0) < OLD_MASTER_BASELINE_PAGES
        ):
            failures.append("recovered_master_pages_below_old_650_page_baseline")
    payload: dict[str, Any] = {
        "schema_id": "OC_CORE_RELEASE_PACKAGE_ASSEMBLY_AUDIT_v1",
        "artifact_kind": "OC_CORE_RELEASE_PACKAGE_ASSEMBLY_AUDIT",
        "status": "PASS" if not failures else "FAIL",
        "failure_total": len(failures),
        "failures": sorted(set(failures)),
        "release_identity": assembly["release_identity"],
        "release_package_assembly_hash": assembly["artifact_hash"],
        "structure_source": assembly.get("structure_source", "current"),
        "assembly_revision": assembly.get("assembly_revision"),
        "summary": summary,
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def render_assembly_md(payload: dict[str, Any]) -> str:
    lines = [
        f"# OC Core Release Package Assembly {payload['release_identity']['version']}",
        "",
        f"Status: `{payload['status']}`",
        f"Artifact hash: `{payload['artifact_hash']}`",
        f"Concept DOI for generated PDFs: `{payload['concept_doi']}`",
        f"Structure source: `{payload.get('structure_source', 'current')}`",
        f"Assembly revision: `{payload.get('assembly_revision')}`",
        "Publication actions performed: `false`",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Artifacts", ""])
    for row in payload["artifact_rows"]:
        lines.append(f"- `{row['artifact_type_id']}`: {', '.join(row.get('output_paths', []))}")
    lines.extend(["", "## Review Zip", "", f"- `{payload['review_zip']['path']}`"])
    return "\n".join(lines).rstrip() + "\n"


def render_audit_md(payload: dict[str, Any]) -> str:
    lines = [
        "# OC Core Release Package Assembly Audit",
        "",
        f"Status: `{payload['status']}`",
        f"Failures: `{payload['failure_total']}`",
        f"Assembly hash: `{payload['release_package_assembly_hash']}`",
        "",
    ]
    for failure in payload["failures"]:
        lines.append(f"- {failure}")
    return "\n".join(lines).rstrip() + "\n"


def check_release(release_id: str, *, assembly_revision: str | None = None) -> dict[str, Any]:
    version = version_from_release_id(release_id)
    paths = assembly_paths(release_id, version, assembly_revision)
    missing = [rel(path) for path in paths.values() if not path.is_file()]
    if missing:
        return {"state": "FAIL", "missing": missing, "changed": []}
    assembly = read_json(paths["assembly_json"])
    audit = build_audit_payload(assembly)
    recorded_audit = read_json(paths["audit_json"])
    changed = []
    expected_audit = stable_json(audit)
    if paths["audit_json"].read_text(encoding="utf-8", errors="replace") != expected_audit:
        changed.append(rel(paths["audit_json"]))
    expected_audit_md = render_audit_md(audit)
    if paths["audit_md"].read_text(encoding="utf-8", errors="replace") != expected_audit_md:
        changed.append(rel(paths["audit_md"]))
    if recorded_audit.get("artifact_hash") != audit.get("artifact_hash"):
        changed.append("audit_hash_mismatch")
    return {"state": "PASS" if audit["status"] == "PASS" and not changed else "FAIL", "missing": [], "changed": changed, "audit": audit}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Assemble a review-space OC Core release package from generic assembly inputs.")
    parser.add_argument("--release", required=True)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--skip-pdf", action="store_true")
    parser.add_argument("--structure-source", default="current", choices=["current", "recovered_l10c"])
    parser.add_argument("--assembly-revision", default=None)
    args = parser.parse_args(argv)
    if not args.write and not args.check:
        args.check = True
    payload = check_release(args.release, assembly_revision=args.assembly_revision) if args.check else assemble_release(
        args.release,
        write=True,
        skip_pdf=args.skip_pdf,
        structure_source=args.structure_source,
        assembly_revision=args.assembly_revision,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if payload.get("state") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
