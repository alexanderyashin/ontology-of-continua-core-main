from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import zipfile
from pathlib import Path
from typing import Any

from oc_core_release_assembly_lib import ROOT, artifact_hash, read_json, relative, stable_json, validation_result


RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"
RECOVERY_DIR = ROOT / "releases" / RELEASE_ID / "editorial" / "recovery"
OLD_MASTER = ROOT / "releases" / RELEASE_ID / "artifacts" / "OC_CORE_1_3_3_MASTER_MONOGRAPH_EN.pdf"
NEW_MASTER = ROOT / "releases" / RELEASE_ID / "editorial" / "generated_artifacts" / "pdf" / "master_monograph_1.3.3.pdf"
HISTORICAL_TOC = ROOT / "releases" / RELEASE_ID / "editorial" / "MASTER_MANUSCRIPT_STRUCTURE_1_3_3.json"
HISTORICAL_SOURCES = ROOT / "releases" / RELEASE_ID / "editorial" / "ALL_HISTORICAL_TOC_SOURCES.json"
CURRENT_TERMINAL_CONTRACTS = (
    ROOT
    / "releases"
    / RELEASE_ID
    / "editorial"
    / "generated_artifacts"
    / "terminal_text"
    / "OC_CORE_TERMINAL_TEXT_CONTRACTS_1.3.3.json"
)
CURRENT_PACKAGE_ASSEMBLY = (
    ROOT
    / "releases"
    / RELEASE_ID
    / "editorial"
    / "generated_artifacts"
    / "package_assembly"
    / "OC_CORE_RELEASE_PACKAGE_ASSEMBLY_1.3.3.json"
)
CYRILLIC_RE = re.compile(r"[\u0400-\u04FF]")
IMPORT_OR_INCLUDE_RE = re.compile(r"\bimport\b|\\(?:input|include)\{|include\{", re.IGNORECASE)
PLACEHOLDER_TITLE_RE = re.compile(r"\b(TITLE|TODO|TBD|placeholder|draft slot)\b", re.IGNORECASE)
STRUCTURAL_ONLY_KINDS = {"tex_import_route", "markdown_structural_marker", "tex_structural_marker"}


def recovery_paths() -> dict[str, Path]:
    return {
        "comparison_json": RECOVERY_DIR / "OC_CORE_1_3_3_PACKAGE_COMPARISON_OLD_VS_NEW.json",
        "comparison_md": RECOVERY_DIR / "OC_CORE_1_3_3_PACKAGE_COMPARISON_OLD_VS_NEW.md",
        "l10b_json": RECOVERY_DIR / "OC_CORE_1_3_3_TOC_L10B_RECOVERY_DELTA.json",
        "l10b_md": RECOVERY_DIR / "OC_CORE_1_3_3_TOC_L10B_RECOVERY_DELTA.md",
        "artifact_lb_json": RECOVERY_DIR / "OC_CORE_1_3_3_ARTIFACT_STRUCTURE_LB_RECOVERY_DELTA.json",
        "artifact_lb_md": RECOVERY_DIR / "OC_CORE_1_3_3_ARTIFACT_STRUCTURE_LB_RECOVERY_DELTA.md",
        "source_intake_json": RECOVERY_DIR / "OC_CORE_1_3_3_SOURCE_INTAKE_AUDIT.json",
        "source_intake_md": RECOVERY_DIR / "OC_CORE_1_3_3_SOURCE_INTAKE_AUDIT.md",
        "l10c_json": RECOVERY_DIR / "OC_CORE_1_3_3_TOC_L10C_RECOVERED.json",
        "l10c_md": RECOVERY_DIR / "OC_CORE_1_3_3_TOC_L10C_RECOVERED.md",
        "audit_json": RECOVERY_DIR / "OC_CORE_1_3_3_RECOVERY_STRUCTURE_AUDIT.json",
        "audit_md": RECOVERY_DIR / "OC_CORE_1_3_3_RECOVERY_STRUCTURE_AUDIT.md",
    }


def sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def normalize_title(value: str) -> str:
    text = value.lower()
    text = text.replace("paragraph slot:", "")
    text = re.sub(r"\b(define|bind|state|synthesize|and|the|a|an|to|its|reader|task|proof|evidence|replay)\b", " ", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def is_non_english_source_path(path: Any) -> bool:
    text = str(path or "").lower().replace("\\", "/")
    return bool(re.search(r"(^|[_/.-])(ru|de)([_/.-]|$)", text))


def source_intake_rejections(row: dict[str, Any]) -> list[str]:
    title = str(row.get("title") or "")
    provenance = row.get("provenance", [])
    reasons: list[str] = []
    if CYRILLIC_RE.search(title):
        reasons.append("non_english_cyrillic_title")
    if IMPORT_OR_INCLUDE_RE.search(title):
        reasons.append("import_route_not_science_node")
    if PLACEHOLDER_TITLE_RE.search(title):
        reasons.append("placeholder_or_template_title")
    if provenance and all(is_non_english_source_path(item.get("path")) for item in provenance):
        reasons.append("only_non_english_source_paths")
    if provenance and all(item.get("kind") in STRUCTURAL_ONLY_KINDS for item in provenance):
        reasons.append("structural_route_only_no_science_heading")
    return reasons


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


def pdf_text_chars(path: Path) -> int:
    if not path.is_file():
        return 0
    try:
        completed = subprocess.run(
            ["pdftotext", "-layout", str(path), "-"],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=120,
        )
        return len(completed.stdout or "")
    except Exception:
        return 0


def file_profile(path: Path) -> dict[str, Any]:
    return {
        "path": relative(path) if path.exists() else relative(path),
        "exists": path.is_file(),
        "size_bytes": path.stat().st_size if path.is_file() else 0,
        "sha256": sha256_file(path),
        "pages": pdf_pages(path) if path.suffix.lower() == ".pdf" else None,
        "text_chars": pdf_text_chars(path) if path.suffix.lower() == ".pdf" else (len(path.read_text(encoding="utf-8", errors="replace")) if path.is_file() and path.suffix.lower() in {".md", ".txt"} else None),
    }


def zip_profile(path: Path) -> dict[str, Any]:
    profile = file_profile(path)
    names: list[str] = []
    if path.is_file():
        try:
            with zipfile.ZipFile(path) as archive:
                names = sorted(archive.namelist())
        except Exception:
            names = []
    profile.update({"zip_entry_total": len(names), "zip_entries_sample": names[:80]})
    return profile


def build_package_comparison() -> dict[str, Any]:
    old_sources = ROOT / "releases" / RELEASE_ID / "public_payload" / "sources"
    new_sources = ROOT / "releases" / RELEASE_ID / "editorial" / "generated_artifacts" / "sources"
    old_artifacts = ROOT / "releases" / RELEASE_ID / "artifacts"
    new_pdf = ROOT / "releases" / RELEASE_ID / "editorial" / "generated_artifacts" / "pdf"
    artifact_pairs = [
        ("release_guide", old_artifacts / "00_OC_CORE_1_3_3_RELEASE_GUIDE_EN.pdf", new_pdf / "release_guide_1.3.3.pdf", old_sources / "00_OC_CORE_1_3_3_RELEASE_GUIDE_EN.md", new_sources / "release_guide_1.3.3.md"),
        ("master_monograph", OLD_MASTER, NEW_MASTER, old_sources / "OC_CORE_1_3_3_MASTER_MONOGRAPH_EN.md", new_sources / "master_monograph_1.3.3.md"),
        ("journal_core_article", old_artifacts / "OC_CORE_1_3_3_JOURNAL_CORE_EN.pdf", new_pdf / "journal_core_article_1.3.3.pdf", old_sources / "OC_CORE_1_3_3_JOURNAL_CORE_EN.md", new_sources / "journal_core_article_1.3.3.md"),
        ("methods_repro_companion", old_artifacts / "OC_CORE_1_3_3_METHODS_AND_REPRODUCIBILITY_COMPANION_EN.pdf", new_pdf / "methods_repro_companion_1.3.3.pdf", old_sources / "OC_CORE_1_3_3_METHODS_AND_REPRODUCIBILITY_COMPANION_EN.md", new_sources / "methods_repro_companion_1.3.3.md"),
        ("reviewer_attack_response_map", old_artifacts / "OC_CORE_1_3_3_REVIEWER_ATTACK_AND_RESPONSE_MAP_EN.pdf", new_pdf / "reviewer_attack_response_map_1.3.3.pdf", old_sources / "OC_CORE_1_3_3_REVIEWER_ATTACK_AND_RESPONSE_MAP_EN.md", new_sources / "reviewer_attack_response_map_1.3.3.md"),
    ]
    rows = []
    for artifact_id, old_pdf, new_pdf_path, old_source, new_source in artifact_pairs:
        old_pdf_profile = file_profile(old_pdf)
        new_pdf_profile = file_profile(new_pdf_path)
        old_source_profile = file_profile(old_source)
        new_source_profile = file_profile(new_source)
        rows.append(
            {
                "artifact_type_id": artifact_id,
                "old_pdf": old_pdf_profile,
                "new_pdf": new_pdf_profile,
                "old_source": old_source_profile,
                "new_source": new_source_profile,
                "page_delta_new_minus_old": (new_pdf_profile.get("pages") or 0) - (old_pdf_profile.get("pages") or 0),
                "text_char_delta_new_minus_old": (new_pdf_profile.get("text_chars") or 0) - (old_pdf_profile.get("text_chars") or 0),
                "loss_class": "new_package_below_old_page_baseline" if (new_pdf_profile.get("pages") or 0) < (old_pdf_profile.get("pages") or 0) else "new_package_not_below_old_page_baseline",
            }
        )
    historical = read_json(HISTORICAL_TOC)
    historical_sources = read_json(HISTORICAL_SOURCES)
    current_contracts = read_json(CURRENT_TERMINAL_CONTRACTS)
    payload: dict[str, Any] = {
        "schema_id": "OC_CORE_1_3_3_PACKAGE_COMPARISON_OLD_VS_NEW_v1",
        "artifact_kind": "OC_CORE_1_3_3_PACKAGE_COMPARISON_OLD_VS_NEW",
        "status": "PACKAGE_COMPARISON_READY",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "baseline_policy": {
            "old_public_master_pages": rows[1]["old_pdf"]["pages"],
            "new_generated_master_pages": rows[1]["new_pdf"]["pages"],
            "minimum_proven_public_baseline_pages": 650,
            "strongest_committed_historical_baseline_pages": historical.get("strongest_proven_pdf_baseline", {}).get("pages"),
            "uncommitted_1100_plus_claim_status": "UNTRUSTED_UNTIL_ARTIFACT_HASH_OR_SOURCE_IS_FOUND",
        },
        "historical_toc_summary": {
            "node_total": historical.get("node_total"),
            "source_total": historical.get("source_total"),
            "historical_toc_item_total": historical.get("historical_toc_item_total"),
            "historical_source_total": historical_sources.get("source_total"),
            "historical_source_item_total": historical_sources.get("item_total"),
        },
        "current_new_assembly_summary": {
            "terminal_contract_total": current_contracts.get("terminal_node_total"),
            "current_package_assembly_hash": read_json(CURRENT_PACKAGE_ASSEMBLY).get("artifact_hash"),
        },
        "artifact_rows": rows,
        "zip_rows": [
            {"zip_role": "old_public_zip", **zip_profile(ROOT / "releases" / RELEASE_ID / "artifacts" / "oc_core_1_3_3_public_release.zip")},
            {"zip_role": "new_review_zip", **zip_profile(ROOT / "releases" / RELEASE_ID / "editorial" / "generated_artifacts" / "package" / "oc_core_release_review_package_1.3.3.zip")},
        ],
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def historical_node_key(node: dict[str, Any]) -> str:
    return str(node.get("normalized_title") or normalize_title(str(node.get("title", ""))))


def build_l10b_delta(comparison: dict[str, Any]) -> dict[str, Any]:
    historical = read_json(HISTORICAL_TOC)
    current = read_json(CURRENT_TERMINAL_CONTRACTS)
    current_keys = {
        normalize_title(str(row.get("title", ""))) for row in current.get("terminal_contracts", [])
    } | {
        normalize_title(str(row.get("clean_title", ""))) for row in current.get("terminal_contracts", [])
    }
    rows = []
    raw_recovered_total = 0
    accepted_recovered_total = 0
    rejected_recovered_total = 0
    for node in historical.get("nodes", []):
        key = historical_node_key(node)
        covered = key in current_keys
        relation = "covered_by_current_l10" if covered else "old_or_historical_only"
        source_row = {
            "title": node.get("title"),
            "provenance": node.get("provenance", []),
        }
        intake_reasons = [] if covered else source_intake_rejections(source_row)
        accepted_for_l10c = (not covered) and not intake_reasons
        if not covered:
            raw_recovered_total += 1
            if accepted_for_l10c:
                accepted_recovered_total += 1
            else:
                rejected_recovered_total += 1
        rows.append(
            {
                "l10b_node_id": "OC133-L10B-" + str(node.get("node_id", "")),
                "historical_node_id": node.get("node_id"),
                "title": node.get("title"),
                "normalized_title": key,
                "role": node.get("role"),
                "historical_master_order": node.get("master_order"),
                "relation_to_current_l10": relation,
                "source_intake_decision": "accepted_for_l10c" if accepted_for_l10c else ("current_l10_already_covers" if covered else "rejected_from_l10c"),
                "source_intake_reasons": intake_reasons,
                "accepted_for_l10c_recovery": accepted_for_l10c,
                "recovery_action": (
                    "append_to_l10c_recovered_as_historical_content_node"
                    if accepted_for_l10c
                    else ("keep_current_l10_binding" if covered else "reject_from_l10c_source_intake")
                ),
                "reason_for_loss": "not_represented_in_current_656_terminal_contracts" if (not covered and accepted_for_l10c) else None,
                "needs_owner_review": bool(node.get("needs_owner_review")),
                "provenance_total": node.get("provenance_total"),
                "provenance": node.get("provenance", [])[:12],
            }
        )
    payload: dict[str, Any] = {
        "schema_id": "OC_CORE_1_3_3_TOC_L10B_RECOVERY_DELTA_v1",
        "artifact_kind": "OC_CORE_1_3_3_TOC_L10B_RECOVERY_DELTA",
        "status": "L10B_RECOVERY_DELTA_READY",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "source_hashes": {
            "package_comparison_hash": comparison["artifact_hash"],
            "historical_master_structure_hash": historical.get("structure_hash"),
            "current_terminal_contracts_hash": current.get("artifact_hash"),
        },
        "current_terminal_node_total": current.get("terminal_node_total"),
        "historical_node_total": len(historical.get("nodes", [])),
        "raw_recovered_candidate_total": raw_recovered_total,
        "accepted_recovered_candidate_total": accepted_recovered_total,
        "rejected_recovered_candidate_total": rejected_recovered_total,
        "recovered_candidate_total": accepted_recovered_total,
        "covered_by_current_total": len(rows) - raw_recovered_total,
        "delta_rows": rows,
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def build_artifact_lb_delta(comparison: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for row in comparison["artifact_rows"]:
        artifact_id = row["artifact_type_id"]
        old_pages = row["old_pdf"].get("pages") or 0
        new_pages = row["new_pdf"].get("pages") or 0
        old_chars = row["old_pdf"].get("text_chars") or 0
        new_chars = row["new_pdf"].get("text_chars") or 0
        rows.append(
            {
                "artifact_type_id": artifact_id,
                "old_pages": old_pages,
                "new_pages": new_pages,
                "old_text_chars": old_chars,
                "new_text_chars": new_chars,
                "page_delta_new_minus_old": new_pages - old_pages,
                "text_char_delta_new_minus_old": new_chars - old_chars,
                "recovery_requirement": "recover_to_old_or_historical_baseline" if new_pages < old_pages else "preserve_new_plus_verify_no_loss",
                "source_strategy": "merge old public source, historical TOC provenance, and current terminal contracts through L10c; do not overwrite current package",
            }
        )
    payload: dict[str, Any] = {
        "schema_id": "OC_CORE_1_3_3_ARTIFACT_STRUCTURE_LB_RECOVERY_DELTA_v1",
        "artifact_kind": "OC_CORE_1_3_3_ARTIFACT_STRUCTURE_LB_RECOVERY_DELTA",
        "status": "ARTIFACT_LB_RECOVERY_DELTA_READY",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "source_hashes": {"package_comparison_hash": comparison["artifact_hash"]},
        "artifact_delta_rows": rows,
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def build_source_intake_audit(l10b: dict[str, Any]) -> dict[str, Any]:
    decision_counts: dict[str, int] = {}
    reason_counts: dict[str, int] = {}
    provenance_kind_counts: dict[str, int] = {}
    accepted_bad_rows: list[str] = []
    for row in l10b["delta_rows"]:
        decision = str(row.get("source_intake_decision"))
        decision_counts[decision] = decision_counts.get(decision, 0) + 1
        for reason in row.get("source_intake_reasons", []):
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
        for provenance in row.get("provenance", []):
            kind = str(provenance.get("kind"))
            provenance_kind_counts[kind] = provenance_kind_counts.get(kind, 0) + 1
        if row.get("accepted_for_l10c_recovery") and source_intake_rejections(row):
            accepted_bad_rows.append(str(row.get("l10b_node_id")))
    payload: dict[str, Any] = {
        "schema_id": "OC_CORE_1_3_3_SOURCE_INTAKE_AUDIT_v1",
        "artifact_kind": "OC_CORE_1_3_3_SOURCE_INTAKE_AUDIT",
        "status": "PASS" if not accepted_bad_rows else "FAIL",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "source_hashes": {"l10b_recovery_delta_hash": l10b["artifact_hash"]},
        "policy": {
            "accepted_language": "English/public-release-safe source routes only",
            "reject_non_english_titles": True,
            "reject_only_non_english_source_paths": True,
            "reject_import_routes_as_science_nodes": True,
            "reject_placeholders": True,
            "reject_structural_route_only_nodes": True,
            "note": "Rejected rows remain in L10b forensic evidence but are not allowed into L10c assembly.",
        },
        "summary": {
            "total_l10b_rows": len(l10b["delta_rows"]),
            "covered_by_current_total": l10b["covered_by_current_total"],
            "raw_recovered_candidate_total": l10b["raw_recovered_candidate_total"],
            "accepted_recovered_candidate_total": l10b["accepted_recovered_candidate_total"],
            "rejected_recovered_candidate_total": l10b["rejected_recovered_candidate_total"],
            "accepted_bad_row_total": len(accepted_bad_rows),
        },
        "decision_counts": dict(sorted(decision_counts.items())),
        "rejection_reason_counts": dict(sorted(reason_counts.items())),
        "provenance_kind_counts": dict(sorted(provenance_kind_counts.items())),
        "accepted_bad_row_ids": accepted_bad_rows,
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def current_l10c_rows() -> list[dict[str, Any]]:
    current = read_json(CURRENT_TERMINAL_CONTRACTS)
    rows = []
    for index, row in enumerate(current.get("terminal_contracts", []), start=1):
        rows.append(
            {
                "l10c_node_id": "OC133-L10C-CURRENT-" + row["aggregator_node_id"],
                "aggregator_node_id": row["aggregator_node_id"],
                "source_layer": "current_l10",
                "order_index": index,
                "title": row["title"],
                "clean_title": row["clean_title"],
                "argument_role": row["argument_role"],
                "reader_task": row["reader_task"],
                "claim_boundary": row["claim_boundary"],
                "order_path": row["order_path"],
                "source_refs": row.get("source_refs", []),
                "parent_current_node_id": row["aggregator_node_id"],
                "mutation_policy": "inherited_current_node_not_deleted_not_renamed_not_reordered",
            }
        )
    return rows


def recovered_l10c_rows(l10b: dict[str, Any], start_order: int) -> list[dict[str, Any]]:
    rows = []
    accepted = [
        item for item in l10b["delta_rows"]
        if item["relation_to_current_l10"] == "old_or_historical_only" and item.get("accepted_for_l10c_recovery")
    ]
    for offset, row in enumerate(accepted, start=1):
        provenance = row.get("provenance", [])
        source_refs = []
        for source in provenance[:6]:
            path_text = source.get("path")
            path = ROOT / str(path_text) if path_text else None
            source_refs.append(
                {
                    "source_family_id": "historical_toc_recovery",
                    "path": path_text,
                    "commit": source.get("commit"),
                    "line": source.get("line"),
                    "exists": bool(path and path.is_file()),
                    "sha256": sha256_file(path) if path and path.is_file() else None,
                }
            )
        title = str(row.get("title") or "Recovered historical obligation")
        rows.append(
            {
                "l10c_node_id": "OC133-L10C-RECOVERED-" + str(row.get("historical_node_id")),
                "aggregator_node_id": "OC133-L10C-RECOVERED-" + str(row.get("historical_node_id")),
                "source_layer": "l10b_recovered",
                "order_index": start_order + offset,
                "title": title,
                "clean_title": title.replace("Import:", "Recovered source route:").strip(),
                "argument_role": role_to_argument(row.get("role"), title),
                "reader_task": f"recover the historical scientific content route for {title}",
                "claim_boundary": "historical recovery restores structure and source route; it does not promote stronger claims without current evidence",
                "order_path": [999, int(row.get("historical_master_order") or offset)],
                "source_refs": source_refs,
                "parent_l10b_node_id": row["l10b_node_id"],
                "historical_node_id": row.get("historical_node_id"),
                "conflict_resolution": "parallel_node_keep",
                "needs_owner_review": row.get("needs_owner_review", False),
                "mutation_policy": "recovered_append_node_may_not_delete_current_l10",
            }
        )
    return rows


def role_to_argument(role: Any, title: str) -> str:
    text = f"{role or ''} {title}".lower()
    if any(word in text for word in ["proof", "theorem", "evidence", "validation", "lean", "finite", "simulation"]):
        return "proof_evidence"
    if any(word in text for word in ["limit", "fals", "review", "attack", "risk", "counterexample"]):
        return "limits_falsifier"
    if any(word in text for word in ["synthesis", "conclusion", "roadmap", "release", "governance"]):
        return "synthesis_transition"
    return "definition_model"


def build_l10c(l10b: dict[str, Any]) -> dict[str, Any]:
    current_rows = current_l10c_rows()
    recovered_rows = recovered_l10c_rows(l10b, len(current_rows))
    nodes = current_rows + recovered_rows
    payload: dict[str, Any] = {
        "schema_id": "OC_CORE_1_3_3_TOC_L10C_RECOVERED_v1",
        "artifact_kind": "OC_CORE_1_3_3_TOC_L10C_RECOVERED",
        "status": "L10C_RECOVERED_READY_FOR_RECOVERY_ASSEMBLY",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "source_hashes": {
            "l10b_recovery_delta_hash": l10b["artifact_hash"],
            "current_terminal_contracts_hash": read_json(CURRENT_TERMINAL_CONTRACTS)["artifact_hash"],
        },
        "current_l10_node_total": len(current_rows),
        "recovered_l10b_node_total": len(recovered_rows),
        "node_total": len(nodes),
        "merge_policy": {
            "current_l10_nodes_preserved_first": True,
            "recovered_nodes_appended": True,
            "source_intake_filter_required": True,
            "rejected_l10b_rows_forensic_only": True,
            "silent_collapse_forbidden": True,
            "allowed_conflict_resolutions": ["same_role_merge", "parallel_node_keep", "needs_owner_review"],
        },
        "nodes": nodes,
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def validate_payloads(
    comparison: dict[str, Any],
    l10b: dict[str, Any],
    artifact_lb: dict[str, Any],
    source_intake: dict[str, Any],
    l10c: dict[str, Any],
) -> list[str]:
    failures: list[str] = []
    if comparison["baseline_policy"]["old_public_master_pages"] < 650:
        failures.append("old_public_master_baseline_below_expected_650")
    if comparison["baseline_policy"]["new_generated_master_pages"] >= comparison["baseline_policy"]["old_public_master_pages"]:
        failures.append("comparison_did_not_detect_new_master_page_regression")
    if l10b["recovered_candidate_total"] <= 0:
        failures.append("l10b_has_no_recovered_candidates")
    if l10c["current_l10_node_total"] != read_json(CURRENT_TERMINAL_CONTRACTS).get("terminal_node_total"):
        failures.append("l10c_current_l10_count_mismatch")
    if l10c["node_total"] != l10c["current_l10_node_total"] + l10c["recovered_l10b_node_total"]:
        failures.append("l10c_node_total_mismatch")
    if l10c["recovered_l10b_node_total"] != l10b["recovered_candidate_total"]:
        failures.append("l10c_missing_l10b_recovered_nodes")
    if source_intake["status"] != "PASS":
        failures.append("source_intake_audit_failed")
    if source_intake["summary"]["accepted_recovered_candidate_total"] != l10c["recovered_l10b_node_total"]:
        failures.append("source_intake_l10c_count_mismatch")
    for row in l10c["nodes"]:
        if row.get("source_layer") == "l10b_recovered" and source_intake_rejections(row):
            failures.append(f"rejected_source_reached_l10c::{row.get('l10c_node_id')}")
            break
    for name, payload in {"comparison": comparison, "l10b": l10b, "artifact_lb": artifact_lb, "source_intake": source_intake, "l10c": l10c}.items():
        if payload.get("artifact_hash") != artifact_hash(payload):
            failures.append(f"{name}_hash_mismatch")
    return sorted(set(failures))


def build_audit(
    comparison: dict[str, Any],
    l10b: dict[str, Any],
    artifact_lb: dict[str, Any],
    source_intake: dict[str, Any],
    l10c: dict[str, Any],
) -> dict[str, Any]:
    failures = validate_payloads(comparison, l10b, artifact_lb, source_intake, l10c)
    payload: dict[str, Any] = {
        "schema_id": "OC_CORE_1_3_3_RECOVERY_STRUCTURE_AUDIT_v1",
        "artifact_kind": "OC_CORE_1_3_3_RECOVERY_STRUCTURE_AUDIT",
        "status": "PASS" if not failures else "FAIL",
        "failure_total": len(failures),
        "failures": failures,
        "source_hashes": {
            "package_comparison_hash": comparison["artifact_hash"],
            "l10b_recovery_delta_hash": l10b["artifact_hash"],
            "artifact_lb_recovery_delta_hash": artifact_lb["artifact_hash"],
            "source_intake_audit_hash": source_intake["artifact_hash"],
            "l10c_recovered_hash": l10c["artifact_hash"],
        },
        "summary": {
            "old_public_master_pages": comparison["baseline_policy"]["old_public_master_pages"],
            "new_generated_master_pages": comparison["baseline_policy"]["new_generated_master_pages"],
            "current_l10_node_total": l10c["current_l10_node_total"],
            "raw_recovered_candidate_total": l10b["raw_recovered_candidate_total"],
            "accepted_recovered_candidate_total": l10b["accepted_recovered_candidate_total"],
            "rejected_recovered_candidate_total": l10b["rejected_recovered_candidate_total"],
            "recovered_l10b_node_total": l10c["recovered_l10b_node_total"],
            "l10c_node_total": l10c["node_total"],
        },
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def render_comparison_md(payload: dict[str, Any]) -> str:
    lines = ["# OC Core 1.3.3 Package Comparison: Old vs New", "", f"Status: `{payload['status']}`", f"Artifact hash: `{payload['artifact_hash']}`", ""]
    lines.extend(["## Baselines", ""])
    for key, value in payload["baseline_policy"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Artifact Deltas", "", "| Artifact | Old pages | New pages | Page delta | Old text chars | New text chars |", "|---|---:|---:|---:|---:|---:|"])
    for row in payload["artifact_rows"]:
        lines.append(
            f"| `{row['artifact_type_id']}` | {row['old_pdf'].get('pages')} | {row['new_pdf'].get('pages')} | "
            f"{row['page_delta_new_minus_old']} | {row['old_pdf'].get('text_chars')} | {row['new_pdf'].get('text_chars')} |"
        )
    return "\n".join(lines) + "\n"


def render_l10b_md(payload: dict[str, Any]) -> str:
    lines = [
        "# OC Core 1.3.3 TOC L10b Recovery Delta",
        "",
        f"Status: `{payload['status']}`",
        f"Raw recovered candidates: `{payload['raw_recovered_candidate_total']}`",
        f"Accepted recovered candidates: `{payload['accepted_recovered_candidate_total']}`",
        f"Rejected recovered candidates: `{payload['rejected_recovered_candidate_total']}`",
        f"Covered by current: `{payload['covered_by_current_total']}`",
        "",
    ]
    lines.extend(["## Sample Accepted Recovered Rows", ""])
    accepted = [item for item in payload["delta_rows"] if item.get("accepted_for_l10c_recovery")]
    for row in accepted[:300]:
        lines.append(f"- `{row['l10b_node_id']}` {row['title']} / role={row.get('role')} / provenance={row.get('provenance_total')}")
    if payload["recovered_candidate_total"] > 300:
        lines.append(f"- ... {payload['recovered_candidate_total'] - 300} additional recovered rows in JSON.")
    return "\n".join(lines) + "\n"


def render_artifact_lb_md(payload: dict[str, Any]) -> str:
    lines = ["# OC Core 1.3.3 Artifact Structure LB Recovery Delta", "", f"Status: `{payload['status']}`", ""]
    for row in payload["artifact_delta_rows"]:
        lines.append(f"- `{row['artifact_type_id']}` old_pages={row['old_pages']} new_pages={row['new_pages']} requirement=`{row['recovery_requirement']}`")
    return "\n".join(lines) + "\n"


def render_source_intake_md(payload: dict[str, Any]) -> str:
    lines = [
        "# OC Core 1.3.3 Source Intake Audit",
        "",
        f"Status: `{payload['status']}`",
        f"Artifact hash: `{payload['artifact_hash']}`",
        "",
        "## Policy",
        "",
    ]
    for key, value in payload["policy"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Summary", ""])
    for key, value in payload["summary"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Rejection Reasons", ""])
    for key, value in payload["rejection_reason_counts"].items():
        lines.append(f"- `{key}`: {value}")
    return "\n".join(lines) + "\n"


def render_l10c_md(payload: dict[str, Any]) -> str:
    lines = ["# OC Core 1.3.3 TOC L10c Recovered", "", f"Status: `{payload['status']}`", f"Node total: `{payload['node_total']}`", f"Current L10 nodes: `{payload['current_l10_node_total']}`", f"Recovered nodes: `{payload['recovered_l10b_node_total']}`", ""]
    lines.extend(["## First Current Nodes", ""])
    for row in payload["nodes"][:40]:
        lines.append(f"- `{row['l10c_node_id']}` {row['clean_title']}")
    lines.extend(["", "## First Recovered Nodes", ""])
    for row in [item for item in payload["nodes"] if item["source_layer"] == "l10b_recovered"][:300]:
        lines.append(f"- `{row['l10c_node_id']}` {row['clean_title']}")
    if payload["recovered_l10b_node_total"] > 300:
        lines.append(f"- ... {payload['recovered_l10b_node_total'] - 300} additional recovered rows in JSON.")
    return "\n".join(lines) + "\n"


def render_audit_md(payload: dict[str, Any]) -> str:
    lines = ["# OC Core 1.3.3 Recovery Structure Audit", "", f"Status: `{payload['status']}`", f"Failures: `{payload['failure_total']}`", ""]
    for key, value in payload["summary"].items():
        lines.append(f"- {key}: `{value}`")
    if payload["failures"]:
        lines.extend(["", "## Failures", ""])
        lines.extend(f"- {failure}" for failure in payload["failures"])
    return "\n".join(lines) + "\n"


def expected_files() -> dict[Path, str]:
    comparison = build_package_comparison()
    l10b = build_l10b_delta(comparison)
    artifact_lb = build_artifact_lb_delta(comparison)
    source_intake = build_source_intake_audit(l10b)
    l10c = build_l10c(l10b)
    audit = build_audit(comparison, l10b, artifact_lb, source_intake, l10c)
    if audit["status"] != "PASS":
        raise RuntimeError(f"Recovery structure audit failed: {audit['failures']}")
    paths = recovery_paths()
    return {
        paths["comparison_json"]: stable_json(comparison),
        paths["comparison_md"]: render_comparison_md(comparison),
        paths["l10b_json"]: stable_json(l10b),
        paths["l10b_md"]: render_l10b_md(l10b),
        paths["artifact_lb_json"]: stable_json(artifact_lb),
        paths["artifact_lb_md"]: render_artifact_lb_md(artifact_lb),
        paths["source_intake_json"]: stable_json(source_intake),
        paths["source_intake_md"]: render_source_intake_md(source_intake),
        paths["l10c_json"]: stable_json(l10c),
        paths["l10c_md"]: render_l10c_md(l10c),
        paths["audit_json"]: stable_json(audit),
        paths["audit_md"]: render_audit_md(audit),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build OC Core 1.3.3 package forensic comparison and L10b/L10c recovery structures.")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if not args.write and not args.check:
        args.check = True
    result = validation_result(expected_files(), write=args.write)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["state"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
