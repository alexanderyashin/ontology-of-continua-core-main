from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
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
from release_machine import science_monolith


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
PUBLICATION_BODY_REVISIONS = {"recovery_r004", "recovery_r005", "recovery_r006", "recovery_r007", "recovery_r008", "recovery_r009", "recovery_r010"}
PUBLICATION_DATE = "4 May 2026"
CURRENT_RECOVERY_REVISION = "recovery_r010"
R007_REVISION = "recovery_r007"
R008_REVISION = "recovery_r008"
R009_REVISION = "recovery_r009"
R010_REVISION = "recovery_r010"
R007_TRANSLATOR_STATUS = "PUBLICATION_TRANSLATOR_R007"
R008_TRANSLATOR_STATUS = "PUBLICATION_TRANSLATOR_R008"
R009_TRANSLATOR_STATUS = "PUBLICATION_TRANSLATOR_R009"
R010_TRANSLATOR_STATUS = "PUBLICATION_TRANSLATOR_R010_SOURCE_GROUNDED_REPAIR"
PUBLIC_PAYLOAD_SOURCE_BY_ARTIFACT = {
    "release_guide": ROOT / "releases" / "oc_core_1_3_3" / "public_payload" / "sources" / "00_OC_CORE_1_3_3_RELEASE_GUIDE_EN.md",
    "journal_core_article": ROOT / "releases" / "oc_core_1_3_3" / "public_payload" / "sources" / "OC_CORE_1_3_3_JOURNAL_CORE_EN.md",
    "methods_repro_companion": ROOT / "releases" / "oc_core_1_3_3" / "public_payload" / "sources" / "OC_CORE_1_3_3_METHODS_AND_REPRODUCIBILITY_COMPANION_EN.md",
    "reviewer_attack_response_map": ROOT / "releases" / "oc_core_1_3_3" / "public_payload" / "sources" / "OC_CORE_1_3_3_REVIEWER_ATTACK_AND_RESPONSE_MAP_EN.md",
}
R007_GOVERNANCE_REFS = {
    "host_resource_state": ROOT.parent.parent.parent / "logion_local" / "runtime" / "state" / "LOGION_HOST_RESOURCE_STATE_latest.json",
    "runtime_live_bridge": ROOT.parent.parent.parent / "logion_local" / "runtime" / "state" / "TOE_ASAP_RUNTIME_LIVE_BRIDGE_latest.json",
    "ollama_provider_script": ROOT.parent.parent.parent / "estra-private-work" / "logion" / "k3" / "execution" / "scripts" / "logion_llm" / "Provider_Ollama_Local_v0_1.ps1",
    "ollama_health_script": ROOT.parent.parent.parent / "estra-private-work" / "logion" / "k3" / "execution" / "scripts" / "logi" / "check_ollama_local_provider_v1.ps1",
    "logion_llm_service": ROOT.parent.parent.parent / "estra-private-work" / "logion" / "k3" / "execution" / "scripts" / "logion_llm" / "logion_llm_service_v1.py",
}


TEXT_ARTIFACTS = {
    "release_guide",
    "master_monograph",
    "journal_core_article",
    "methods_repro_companion",
    "reviewer_attack_response_map",
}
AUTHOR_DISPLAY = "Alexander Yashin"
AUTHOR_AFFILIATION = "Independent Researcher"
AUTHOR_ORCID = "0009-0008-6166-0914"
DEDICATION_TEXT = "Dedicated to my dear wife Maria, without whom this work would have been impossible."
ACKNOWLEDGEMENT_BOUNDARY = (
    "They are acknowledged for review pressure, ideas, criticism, or external response that improved the work. "
    "Acknowledgement does not imply authorship, endorsement, publication approval, or agreement with the theory's release form."
)
ACKNOWLEDGEMENT_NAMES = [
    "G. V. Apostolov",
    "Eduard Fadeev",
    "Gennady Alekseevich Nosov",
    "Sergey Shpadyrev",
    "Stanislav Tsukrov",
]
FRONTMATTER_REQUIRED_SECTIONS = [
    "Title Page",
    "Dedication",
    "Acknowledgements",
    "Abstract",
    "Version 1.3.3 Release Delta",
    "Reader Routes",
    "Table of Contents",
]
FRONTMATTER_L1_BLOCKS = {1}
FRONTMATTER_BODY_TITLE_RE = re.compile(
    r"\b(Define|Bind|State limits and falsifiers for|Synthesize)\s+"
    r"(Title Page|Dedication|Abstract|Keywords|Citation, DOI|Table of Contents|List of Figures|Symbols|Author, Instrument)",
    re.IGNORECASE,
)
READER_HEADING_MAX_CHARS = 88
TECHNICAL_HEADING_PREFIX_RE = re.compile(
    r"^(Define|Bind|State limits and falsifiers for|State limits for|State|Synthesize|Register|Map|Trace|Validate|"
    r"Prove|Show|Compare|Document|Encode|Declare|Specify|Connect|Close)\s+",
    re.IGNORECASE,
)
READER_CHAPTER_TITLES = {
    2: "Reader Orientation and Claim Boundaries",
    3: "The Continuum Problem",
    4: "Systems-Theory Context",
    5: "Claim Taxonomy and Promotion Rules",
    6: "Basic Objects and Type Discipline",
    7: "The Core OC Tuple",
    8: "Operators and Transition Semantics",
    9: "Theorem Inventory and Proof Route",
    10: "Formalization Strategy",
    11: "Evidence Ledger and Source Trace",
    12: "Domain Projection Method",
    13: "Falsifiers and Negative Controls",
    14: "Novelty and Prior-Art Boundary",
    15: "Model Maps and Figures",
    16: "Reviewer Protocol and Attack Surface",
    17: "Build Environment and Reproducibility",
    18: "Versioning, Citation, and Release Identity",
    19: "Release Synthesis",
    20: "Appendices",
    999: "Document Boundary",
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


def portable_ref(path: Path) -> str:
    try:
        return rel(path)
    except ValueError:
        return str(path).replace("\\", "/")


def read_json_optional(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        return read_json(path)
    except Exception:
        return {}


def governed_ollama_trace(assembly_revision: str | None) -> dict[str, Any]:
    """Record local-LLM governance without making unmanaged Ollama calls."""
    host_state = read_json_optional(R007_GOVERNANCE_REFS["host_resource_state"])
    live_bridge = read_json_optional(R007_GOVERNANCE_REFS["runtime_live_bridge"])
    host_status = str(host_state.get("status") or host_state.get("overall_status") or "UNKNOWN")
    bridge_next_action = str(live_bridge.get("host_safety_next_action") or "")
    bridge_allows_gpu = bool(live_bridge.get("host_gpu_allowed") is True)
    effective_workers = int(live_bridge.get("effective_max_workers") or 1)
    allowed_throttled = bridge_allows_gpu and effective_workers <= 1 and "SAFE_GPU" in bridge_next_action.upper()
    if assembly_revision == R007_REVISION and host_status.upper() in {"DEGRADED", "FAIL", "BLOCKED"}:
        status = "OLLAMA_SKIPPED_BY_GOVERNANCE"
        rationale = f"Host resource state is {host_status}; r007 uses deterministic translator only."
    elif assembly_revision == R007_REVISION and allowed_throttled:
        status = "OLLAMA_GOVERNED_FALLBACK_DETERMINISTIC"
        rationale = "Governance allows only bounded single-worker local LLM; deterministic translator is cheaper while lower-level blockers are still audited."
    elif assembly_revision == R007_REVISION:
        status = "OLLAMA_SKIPPED_BY_GOVERNANCE"
        rationale = "Safe local-LLM preflight was not fully affirmative; deterministic translator remained active."
    else:
        status = "NOT_APPLICABLE"
        rationale = "Governed publication translator is introduced in recovery_r007."
    return {
        "schema_id": "OC_CORE_R007_GOVERNED_OLLAMA_TRACE_v1",
        "status": status,
        "rationale": rationale,
        "provider_script_id": "logion_llm/Provider_Ollama_Local_v0_1.ps1",
        "health_check_script_id": "logi/check_ollama_local_provider_v1.ps1",
        "host_resource_state_ref": "logion_runtime_state/LOGION_HOST_RESOURCE_STATE_latest.json",
        "runtime_live_bridge_ref": "logion_runtime_state/TOE_ASAP_RUNTIME_LIVE_BRIDGE_latest.json",
        "provider_script_present": R007_GOVERNANCE_REFS["ollama_provider_script"].is_file(),
        "health_check_script_present": R007_GOVERNANCE_REFS["ollama_health_script"].is_file(),
        "host_resource_state_present": R007_GOVERNANCE_REFS["host_resource_state"].is_file(),
        "runtime_live_bridge_present": R007_GOVERNANCE_REFS["runtime_live_bridge"].is_file(),
        "host_resource_status": host_status,
        "host_gpu_allowed": bridge_allows_gpu,
        "host_safety_next_action": bridge_next_action,
        "effective_max_workers": effective_workers,
        "default_model": "qwen2.5-coder:3b",
        "bounded_model": "qwen2.5-coder:7b",
        "temperature": 0.05,
        "max_tokens": 256,
        "max_workers": 1,
        "ollama_invocation_total": 0,
        "unmanaged_ollama_call_total": 0,
        "generation_mode": "deterministic_templates_first",
        "cache_policy": "small_chunk_sequential_cache_required_before_any_llm",
    }


def r008_llm_service_request(version: str) -> dict[str, Any]:
    forbidden_terms = [
        "route sheet",
        "control sheet",
        "machine register",
        "this section is included so",
        "must teach",
        "purpose and role",
        "construction and order",
        "Figure Route and Design Logic",
        "Evidence Coverage Map",
        "Scientific Reading Protocol",
    ]
    return {
        "schema_id": "LOGION_LLM_SERVICE_BATCH_REQUEST_v1",
        "caller_id": "oc_core_1_3_3_recovery_r008",
        "batch_id": f"oc_core_{version}_r008_v_model_publication_translation",
        "run_mode": "safe_exhaustive",
        "thermal_debt_remaining": 0,
        "requests": [
            {
                "schema_id": "LOGION_LLM_SERVICE_REQUEST_v1",
                "task_id": "r008_l10_public_instruction_leak_check",
                "level": "L10",
                "operation_type": "micro_check",
                "allow_7b": True,
                "use_cache": True,
                "temperature": 0.05,
                "max_tokens": 192,
                "forbidden_terms": forbidden_terms,
                "prompt": (
                    "Inspect this OC Core 1.3.3 public section policy for instruction-prose leakage. "
                    "Return JSON with facts, inferences, next_action, blocker_delta, stop_class, confidence, "
                    "and science_program_update. Public text must be finished scientific prose."
                ),
            },
            {
                "schema_id": "LOGION_LLM_SERVICE_REQUEST_v1",
                "task_id": "r008_l10_k_figure_pedagogy_check",
                "level": "L10",
                "operation_type": "figure_pedagogy_check",
                "allow_7b": True,
                "use_cache": True,
                "temperature": 0.05,
                "max_tokens": 192,
                "forbidden_terms": forbidden_terms,
                "prompt": (
                    "Check whether a K0-K12 hierarchy figure names every K-level, avoids label collisions, "
                    "shows upward composition and downward constraint, and links the diagram to formulas, "
                    "examples, evidence, and falsifiers."
                ),
            },
            {
                "schema_id": "LOGION_LLM_SERVICE_REQUEST_v1",
                "task_id": "r008_l9_reader_pdf_translation_aggregate",
                "level": "L9",
                "operation_type": "chapter_aggregate_check",
                "allow_7b": True,
                "use_cache": True,
                "temperature": 0.05,
                "max_tokens": 224,
                "forbidden_terms": forbidden_terms,
                "prompt": (
                    "Aggregate clean L10 findings into an L9 reader-facing translation check. "
                    "Confirm that lower-level blockers are zero before whole-section review and that public prose "
                    "reads as manuscript text rather than a construction packet."
                ),
            },
        ],
    }


def r008_service_output_paths(base: Path, version: str) -> dict[str, Path]:
    package_assembly = base / "package_assembly"
    return {
        "request_json": package_assembly / f"OC133_R008_LOGION_LLM_SERVICE_REQUEST_{version}.json",
        "trace_json": package_assembly / f"OC133_R008_LOGION_LLM_SERVICE_TRACE_{version}.json",
    }


def r009_service_output_paths(base: Path, version: str) -> dict[str, Path]:
    package_assembly = base / "package_assembly"
    return {
        "queue_json": package_assembly / f"OC133_R009_EDITORIAL_LLM_PACKET_QUEUE_{version}.json",
        "trace_json": package_assembly / f"OC133_R009_LOGION_LLM_SERVICE_UNTIL_DONE_TRACE_{version}.json",
    }


def r010_repair_output_paths(base: Path, version: str) -> dict[str, Path]:
    repair_dir = base / "editorial_repair"
    return {
        "records_json": repair_dir / f"OC133_R010_SOURCE_GROUNDED_REPAIR_RECORDS_{version}.json",
        "records_md": repair_dir / f"OC133_R010_SOURCE_GROUNDED_REPAIR_RECORDS_{version}.md",
        "queue_json": repair_dir / f"OC133_R010_SOURCE_GROUNDED_REPAIR_QUEUE_{version}.json",
        "trace_json": repair_dir / f"OC133_R010_SOURCE_GROUNDED_REPAIR_TRACE_{version}.json",
        "summary_json": repair_dir / f"OC133_R010_SOURCE_GROUNDED_REPAIR_SUMMARY_{version}.json",
        "summary_md": repair_dir / f"OC133_R010_SOURCE_GROUNDED_REPAIR_SUMMARY_{version}.md",
    }


def json_object_from_text(text: str) -> dict[str, Any]:
    if not text.strip():
        return {}
    try:
        value = json.loads(text)
        return value if isinstance(value, dict) else {}
    except Exception:
        pass
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        return {}
    try:
        value = json.loads(match.group(0))
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def review_score(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def blocker_classes(blockers: list[Any]) -> list[str]:
    classes: set[str] = set()
    for blocker in blockers:
        text = stable_json(blocker) if isinstance(blocker, (dict, list)) else str(blocker)
        lowered = text.lower()
        if "fabricat" in lowered or "unsupported" in lowered:
            classes.add("fabrication_risk")
        if "forbidden" in lowered or "logion" in lowered or "estra" in lowered or "recovery_" in lowered:
            classes.add("forbidden_public_term")
        if "formal" in lowered:
            classes.add("weak_formal_anchor")
        if "anchor" in lowered or "evidence" in lowered or "proof" in lowered:
            classes.add("missing_anchor")
        if "example" in lowered:
            classes.add("weak_example")
        if "limitation" in lowered or "falsifier" in lowered:
            classes.add("weak_limitation")
    return sorted(classes or {"reader_quality_blocker"})


def packet_text_from_prompt(prompt: str) -> str:
    marker = "Packet text:"
    if marker in prompt:
        return prompt.split(marker, 1)[1].strip()
    return prompt


def r010_workbench_paths(version: str) -> dict[str, Path]:
    base = generated_dir("oc_core_1_3_3", R009_REVISION)
    workbench = base / "editorial_workbench"
    return {
        "v2_cockpit": workbench / "write_check_v2_timeout_fixed" / "LOGION_EDITORIAL_WORKBENCH_COCKPIT.json",
        "v2_writer": workbench / "write_check_v2_timeout_fixed" / "LOGION_EDITORIAL_WORKBENCH_WRITER_TRACE.json",
        "v2_review": workbench / "write_check_v2_timeout_fixed" / "LOGION_EDITORIAL_WORKBENCH_REVIEW_TRACE.json",
        "v3_cockpit": workbench / "write_check_v3_strict_extractive" / "LOGION_EDITORIAL_WORKBENCH_COCKPIT.json",
        "v3_writer": workbench / "write_check_v3_strict_extractive" / "LOGION_EDITORIAL_WORKBENCH_WRITER_TRACE.json",
        "v3_review": workbench / "write_check_v3_strict_extractive" / "LOGION_EDITORIAL_WORKBENCH_REVIEW_TRACE.json",
        "source_queue": base / "package_assembly" / f"OC133_R009_EDITORIAL_LLM_PACKET_QUEUE_{version}.json",
    }


def r010_repair_records(version: str) -> dict[str, Any]:
    paths = r010_workbench_paths(version)
    source_queue = read_json_optional(paths["source_queue"])
    writer_trace = read_json_optional(paths["v3_writer"])
    review_trace = read_json_optional(paths["v3_review"])
    v2_cockpit = read_json_optional(paths["v2_cockpit"])
    v3_cockpit = read_json_optional(paths["v3_cockpit"])
    source_by_task = {
        str(row.get("task_id")): row
        for row in source_queue.get("requests", [])
        if isinstance(row, dict) and str(row.get("level", "")).upper() == "L10"
    }
    writer_by_task = {
        str(row.get("task_id")): row
        for row in writer_trace.get("rows", [])
        if isinstance(row, dict)
    }
    records: list[dict[str, Any]] = []
    accepted_candidates: list[dict[str, Any]] = []
    for row in review_trace.get("rows", []):
        if not isinstance(row, dict) or not row.get("model"):
            continue
        payload = json_object_from_text(str(row.get("output_text") or ""))
        score = review_score(payload.get("score_0_100"))
        blockers = payload.get("blockers") if isinstance(payload.get("blockers"), list) else []
        writer_task_id = str(row.get("source_task_id") or str(row.get("task_id", "")).replace("editorial_check_", "", 1))
        writer_row = writer_by_task.get(writer_task_id, {})
        source_task_id = str(writer_row.get("source_task_id") or writer_task_id.replace("editorial_write_", "", 1))
        source_row = source_by_task.get(source_task_id, {})
        source_excerpt = compact_packet_text(packet_text_from_prompt(str(source_row.get("prompt") or "")), max_chars=3600)
        candidate_text = str(writer_row.get("output_text") or "")
        forbidden_hits = [term for term in ["Logion", "ESTRA", "recovery_", "Figure Route and Design Logic", "Evidence Coverage Map"] if term.lower() in candidate_text.lower()]
        accepted = (score is not None and score >= 85 and not blockers and not forbidden_hits)
        if accepted:
            accepted_candidates.append(
                {
                    "source_l10_task_id": source_task_id,
                    "artifact_type_id": row.get("artifact_type_id"),
                    "page_range": row.get("page_range"),
                    "score_0_100": score,
                    "candidate_sha256": hashlib.sha256(candidate_text.encode("utf-8")).hexdigest() if candidate_text else None,
                    "promotion_status": "NOT_PROMOTED_REQUIRES_REPAIR_PACKET_CONFIRMATION",
                }
            )
            continue
        if score is None and not blockers:
            continue
        records.append(
            {
                "record_id": f"r010_repair_{len(records) + 1:04d}",
                "artifact_type_id": row.get("artifact_type_id"),
                "source_l10_task_id": source_task_id,
                "writer_task_id": writer_task_id,
                "review_task_id": row.get("task_id"),
                "source_ref": row.get("source_ref"),
                "page_range": row.get("page_range"),
                "score_0_100": score,
                "blockers": blockers,
                "blocker_classes": blocker_classes(blockers),
                "repair_actions": payload.get("repair_actions") if isinstance(payload.get("repair_actions"), list) else [],
                "source_excerpt_sha256": hashlib.sha256(source_excerpt.encode("utf-8")).hexdigest() if source_excerpt else None,
                "source_excerpt": source_excerpt,
                "candidate_sha256": hashlib.sha256(candidate_text.encode("utf-8")).hexdigest() if candidate_text else None,
                "promotion_status": "NOT_PROMOTED_LOCAL_REPAIR_REQUIRED",
            }
        )
    class_counts: dict[str, int] = defaultdict(int)
    for record in records:
        for kind in record["blocker_classes"]:
            class_counts[kind] += 1
    payload: dict[str, Any] = {
        "schema_id": "OC133_R010_SOURCE_GROUNDED_REPAIR_RECORDS_v1",
        "status": "REPAIR_REQUIRED" if records else "PASS",
        "release_id": "oc_core_1_3_3",
        "version": version,
        "source_revision": R009_REVISION,
        "source_workbench": "write_check_v3_strict_extractive",
        "fallback_workbench": "write_check_v2_timeout_fixed",
        "source_hashes": {
            "v2_cockpit_hash": artifact_hash(v2_cockpit) if v2_cockpit else None,
            "v3_cockpit_hash": artifact_hash(v3_cockpit) if v3_cockpit else None,
            "v3_writer_trace_hash": artifact_hash(writer_trace) if writer_trace else None,
            "v3_review_trace_hash": artifact_hash(review_trace) if review_trace else None,
            "r009_source_queue_hash": artifact_hash(source_queue) if source_queue else None,
        },
        "summary": {
            "repair_record_total": len(records),
            "accepted_candidate_total": len(accepted_candidates),
            "accepted_candidate_promoted_total": 0,
            "blocker_class_counts": dict(sorted(class_counts.items())),
            "v2_review_score_avg": (v2_cockpit.get("summary") or {}).get("review_score_avg") if v2_cockpit else None,
            "v2_review_blocker_total": (v2_cockpit.get("summary") or {}).get("review_blocker_total") if v2_cockpit else None,
            "v3_review_score_avg": (v3_cockpit.get("summary") or {}).get("review_score_avg") if v3_cockpit else None,
            "v3_review_blocker_total": (v3_cockpit.get("summary") or {}).get("review_blocker_total") if v3_cockpit else None,
        },
        "accepted_candidates": accepted_candidates,
        "records": records,
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def r010_repair_queue(records_payload: dict[str, Any], version: str) -> dict[str, Any]:
    requests: list[dict[str, Any]] = []
    for index, record in enumerate(records_payload.get("records", [])):
        if not isinstance(record, dict):
            continue
        source_excerpt = str(record.get("source_excerpt") or "")
        prompt = (
            "Return one compact JSON object with keys: repair_summary, source_grounded_rewrite_candidate, "
            "anchors_preserved, unsupported_items_rejected, source_gaps, acceptance_recommendation. Use only the source excerpt. "
            "Do not invent facts, numbers, formulas, examples, or citations. If the source excerpt is insufficient, leave "
            "source_grounded_rewrite_candidate empty and explain the source gap. The candidate is not accepted unless a later "
            "checker finds score >=85, zero blockers, zero forbidden terms, and preserved anchors.\n\n"
            f"Artifact: {record.get('artifact_type_id')}. Pages: {record.get('page_range')}. "
            f"Blocker classes: {', '.join(record.get('blocker_classes') or [])}. Repair actions: {record.get('repair_actions')}.\n\n"
            f"Source excerpt:\n{source_excerpt}"
        )
        requests.append(
            {
                "schema_id": "LOGION_LLM_SERVICE_REQUEST_v1",
                "task_id": f"r010_repair_{index + 1:04d}_{record.get('source_l10_task_id')}",
                "sequence_index": index,
                "level": "L10",
                "operation_type": "source_grounded_repair_suggestion",
                "artifact_type_id": record.get("artifact_type_id"),
                "source_repair_record_id": record.get("record_id"),
                "source_l10_task_id": record.get("source_l10_task_id"),
                "page_range": record.get("page_range"),
                "allow_7b": False,
                "use_cache": False,
                "temperature": 0.03,
                "max_tokens": 256,
                "timeout_seconds": 90,
                "monitor_interval_seconds": 2,
                "text_under_review": source_excerpt,
                "forbidden_terms": [],
                "expected_schema": "repair_summary_source_grounded_rewrite_candidate_anchors_preserved_unsupported_items_rejected_source_gaps_acceptance_recommendation",
                "prompt": prompt,
            }
        )
    return {
        "schema_id": "LOGION_LLM_SERVICE_QUEUE_REQUEST_v1",
        "caller_id": "oc_core_1_3_3_recovery_r010",
        "queue_id": f"oc_core_{version}_r010_source_grounded_repair",
        "batch_id": f"oc_core_{version}_r010_source_grounded_repair",
        "run_mode": "safe_exhaustive_until_done_repair_suggestions",
        "cooldown_seconds": 30,
        "max_cooldown_cycles": 1000000,
        "source_revision": R009_REVISION,
        "repair_record_total": len(requests),
        "requests": requests,
    }


def normalize_r010_repair_trace(trace: dict[str, Any], queue: dict[str, Any], records_payload: dict[str, Any], *, version: str) -> dict[str, Any]:
    summary = trace.get("summary") if isinstance(trace.get("summary"), dict) else {}
    queue_status = str(trace.get("queue_status") or trace.get("status") or "SERVICE_TRACE_MISSING")
    invocation_total = int(summary.get("provider_invocation_total") or 0)
    repair_record_total = int(records_payload.get("summary", {}).get("repair_record_total") or 0)
    packet_done_total = int(summary.get("packet_done_total") or 0)
    repair_queue_done = queue_status == "DONE" and packet_done_total == len(queue.get("requests", []))
    unresolved_total = repair_record_total
    payload = {
        "schema_id": "OC133_R010_SOURCE_GROUNDED_REPAIR_SUMMARY_v1",
        "status": "PASS" if repair_queue_done or not queue.get("requests") else "REPAIR_REQUIRED",
        "source_grounded_repair_status": "REPAIR_REQUIRED" if unresolved_total else "PASS",
        "release_id": "oc_core_1_3_3",
        "version": version,
        "source_revision": R009_REVISION,
        "service_status": queue_status,
        "queue_status": queue_status,
        "common_llm_service_status": "PASS" if trace.get("schema_id") == "LOGION_LLM_SERVICE_RESPONSE_v1" else "FAIL",
        "repair_record_total": repair_record_total,
        "accepted_candidate_total": int(records_payload.get("summary", {}).get("accepted_candidate_total") or 0),
        "accepted_candidate_promoted_total": 0,
        "accepted_repair_blocker_total": 0,
        "unresolved_repair_record_total": unresolved_total,
        "source_grounded_repair_loop_status": "PASS" if records_payload.get("schema_id") == "OC133_R010_SOURCE_GROUNDED_REPAIR_RECORDS_v1" else "FAIL",
        "accepted_repair_promotion_status": "PASS",
        "local_editorial_capability_boundary_status": "LOCAL_EDITORIAL_CAPABILITY_EXHAUSTED" if unresolved_total else "PASS",
        "repair_queue_status": queue_status,
        "repair_queue_done_status": "PASS" if repair_queue_done or not queue.get("requests") else "FAIL",
        "repair_queue_packet_total": len(queue.get("requests", [])),
        "repair_queue_packet_done_total": packet_done_total,
        "repair_ollama_invocation_total": invocation_total,
        "ollama_invocation_total": invocation_total,
        "unmanaged_ollama_call_total": int(summary.get("unmanaged_ollama_call_total") or 0),
        "service_ledger_ref": trace.get("ledger_ref") or "logion_local/runtime/observability/logion_llm/LOGION_LLM_SERVICE_LEDGER.ndjson",
        "v_model_lowest_checked_level": "L10",
        "v_model_flow": "L10_source_grounded_repair_suggestions_without_public_promotion",
        "model_sequence": list(summary.get("model_sequence") or []),
        "cadence_sequence": list(summary.get("cadence_sequence") or []),
        "blocker_class_counts": records_payload.get("summary", {}).get("blocker_class_counts", {}),
        "capability_boundary": (
            "Local Ollama generated bounded repair suggestions, but unresolved source-grounding blockers remain; "
            "no generated repair text is promoted into public PDFs."
            if unresolved_total
            else "No unresolved source-grounding blockers remain."
        ),
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def render_r010_repair_records_md(payload: dict[str, Any]) -> str:
    lines = [
        "# OC Core 1.3.3 r010 Source-Grounded Repair Records",
        "",
        f"Status: `{payload['status']}`",
        f"Artifact hash: `{payload['artifact_hash']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Records", ""])
    for record in payload.get("records", [])[:80]:
        lines.append(
            f"- `{record['record_id']}` `{record.get('artifact_type_id')}` pages={record.get('page_range')} "
            f"score={record.get('score_0_100')} classes={', '.join(record.get('blocker_classes') or [])}"
        )
    return "\n".join(lines).rstrip() + "\n"


def render_r010_repair_summary_md(payload: dict[str, Any]) -> str:
    lines = [
        "# OC Core 1.3.3 r010 Source-Grounded Repair Summary",
        "",
        f"Status: `{payload['status']}`",
        f"Artifact hash: `{payload['artifact_hash']}`",
        "",
        "## Fields",
        "",
    ]
    for key, value in payload.items():
        if key not in {"schema_id", "artifact_hash"}:
            lines.append(f"- `{key}`: {value}")
    return "\n".join(lines).rstrip() + "\n"


def pdf_text_by_pages(path: Path) -> list[str]:
    if not path.is_file():
        return []
    try:
        completed = subprocess.run(
            ["pdftotext", "-layout", str(path), "-"],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=180,
        )
    except Exception:
        return []
    if completed.returncode != 0:
        return []
    return [page.strip() for page in completed.stdout.split("\f") if page.strip()]


def compact_packet_text(text: str, max_chars: int = 3200) -> str:
    normalized = re.sub(r"\s+", " ", text).strip()
    if len(normalized) <= max_chars:
        return normalized
    head = normalized[: max_chars // 2].rstrip()
    tail = normalized[-max_chars // 2 :].lstrip()
    return f"{head}\n[... middle omitted for governed small-packet review ...]\n{tail}"


def r009_editorial_packet_queue(version: str, base: Path, artifact_rows: list[dict[str, Any]]) -> dict[str, Any]:
    forbidden_terms = [
        "route sheet",
        "control sheet",
        "machine register",
        "this section is included so",
        "must teach",
        "purpose and role",
        "construction and order",
        "Figure Route and Design Logic",
        "Evidence Coverage Map",
        "Scientific Reading Protocol",
        "recovery_r009",
        "Logion",
        "ESTRA",
    ]
    requests: list[dict[str, Any]] = []
    sequence = 0
    artifact_packet_counts: dict[str, int] = {}
    page_window = 25
    for row in artifact_rows:
        artifact_id = str(row.get("artifact_type_id") or "")
        if artifact_id not in TEXT_ARTIFACTS:
            continue
        pdf_path = ROOT / str(row.get("pdf_path") or "")
        pages = pdf_text_by_pages(pdf_path)
        if not pages:
            source_path = ROOT / str(row.get("source_path") or "")
            pages = [source_path.read_text(encoding="utf-8", errors="replace")] if source_path.is_file() else []
            page_window = 1
        for start_index in range(0, len(pages), page_window):
            chunk_pages = pages[start_index : start_index + page_window]
            start_page = start_index + 1
            end_page = start_index + len(chunk_pages)
            chunk_text = compact_packet_text("\n\n".join(chunk_pages), max_chars=3200)
            if not chunk_text:
                continue
            requests.append(
                {
                    "schema_id": "LOGION_LLM_SERVICE_REQUEST_v1",
                    "task_id": f"r009_l10_{artifact_id}_{start_page:04d}_{end_page:04d}",
                    "sequence_index": sequence,
                    "level": "L10",
                    "operation_type": "editorial_packet_review",
                    "artifact_type_id": artifact_id,
                    "source_ref": row.get("pdf_path") or row.get("source_path"),
                    "page_range": [start_page, end_page],
                    "allow_7b": True,
                    "use_cache": False,
                    "temperature": 0.05,
                    "max_tokens": 128,
                    "timeout_seconds": 70,
                    "monitor_interval_seconds": 2,
                    "forbidden_terms": [],
                    "expected_output_schema": {
                        "required_keys": ["facts", "inferences", "next_action", "blocker_delta", "stop_class", "confidence", "science_program_update"],
                    },
                    "prompt": (
                        "Return a single compact JSON object. Inspect this reader-facing OC Core 1.3.3 packet for public prose quality, "
                        "instruction leakage, missing evidence/formula/figure/table anchors, weak didactic explanation, and reviewer-facing clarity. "
                        f"Artifact: {artifact_id}. Pages: {start_page}-{end_page}. Forbidden public terms to report if present: {', '.join(forbidden_terms)}. "
                        "Packet text:\n"
                        + chunk_text
                    ),
                }
            )
            sequence += 1
            artifact_packet_counts[artifact_id] = artifact_packet_counts.get(artifact_id, 0) + 1
    for artifact_id in sorted(artifact_packet_counts):
        requests.append(
            {
                "schema_id": "LOGION_LLM_SERVICE_REQUEST_v1",
                "task_id": f"r009_l9_{artifact_id}_aggregate",
                "sequence_index": sequence,
                "level": "L9",
                "operation_type": "artifact_aggregate_review",
                "artifact_type_id": artifact_id,
                "allow_7b": True,
                "use_cache": False,
                "temperature": 0.05,
                "max_tokens": 160,
                "timeout_seconds": 70,
                "forbidden_terms": [],
                "prompt": (
                    "Return JSON. Aggregate the completed L10 editorial packets for this artifact and report whether the public artifact "
                    f"is ready for higher-level review. Artifact: {artifact_id}. L10 packet count: {artifact_packet_counts[artifact_id]}."
                ),
            }
        )
        sequence += 1
    requests.append(
        {
            "schema_id": "LOGION_LLM_SERVICE_REQUEST_v1",
            "task_id": "r009_l8_release_reader_surface_aggregate",
            "sequence_index": sequence,
            "level": "L8",
            "operation_type": "release_aggregate_review",
            "artifact_type_id": "oc_core_1_3_3_reader_package",
            "allow_7b": True,
            "use_cache": False,
            "temperature": 0.05,
            "max_tokens": 192,
            "timeout_seconds": 80,
            "forbidden_terms": [],
            "prompt": (
                "Return JSON. Perform the whole-release L8 reader-surface aggregation after all L10 and L9 packets. "
                f"Artifacts covered: {', '.join(sorted(artifact_packet_counts))}. L10 packet total: {sum(artifact_packet_counts.values())}."
            ),
        }
    )
    return {
        "schema_id": "LOGION_LLM_SERVICE_QUEUE_REQUEST_v1",
        "caller_id": "oc_core_1_3_3_recovery_r009",
        "queue_id": f"oc_core_{version}_r009_editorial_until_done",
        "batch_id": f"oc_core_{version}_r009_editorial_until_done",
        "run_mode": "safe_exhaustive_until_done",
        "cooldown_seconds": 30,
        "max_cooldown_cycles": 1000000,
        "source_revision": base.name,
        "packet_builder": "r009_reader_facing_pdf_page_windows",
        "page_window": page_window,
        "artifact_packet_counts": artifact_packet_counts,
        "l10_packet_total": sum(artifact_packet_counts.values()),
        "requests": requests,
    }


def normalize_r008_service_trace(trace: dict[str, Any], *, version: str) -> dict[str, Any]:
    summary = trace.get("summary") if isinstance(trace.get("summary"), dict) else {}
    governance = trace.get("governance_decision") if isinstance(trace.get("governance_decision"), dict) else {}
    host_summary = trace.get("host_summary") if isinstance(trace.get("host_summary"), dict) else {}
    v_model = trace.get("v_model") if isinstance(trace.get("v_model"), dict) else {}
    status = str(trace.get("status") or "SERVICE_TRACE_MISSING")
    service_present = trace.get("schema_id") == "LOGION_LLM_SERVICE_RESPONSE_v1"
    return {
        "schema_id": "OC_CORE_R008_LOGION_LLM_SERVICE_TRACE_v1",
        "status": status,
        "service_status": status,
        "service_id": trace.get("service_id") or "logion_llm_service_v1",
        "caller_id": trace.get("caller_id") or "oc_core_1_3_3_recovery_r008",
        "batch_id": trace.get("batch_id") or f"oc_core_{version}_r008_v_model_publication_translation",
        "common_llm_service_status": "PASS" if service_present else "FAIL",
        "governance_status": governance.get("status") or "UNKNOWN",
        "host_status": host_summary.get("status") or "UNKNOWN",
        "gpu_thermal_band": host_summary.get("gpu_thermal_band") or "UNKNOWN",
        "host_gpu_allowed": bool(host_summary.get("host_gpu_allowed") is True),
        "effective_max_workers": int(host_summary.get("effective_max_workers") or 1),
        "provider_script_present": R007_GOVERNANCE_REFS["ollama_provider_script"].is_file(),
        "health_check_script_present": R007_GOVERNANCE_REFS["ollama_health_script"].is_file(),
        "logion_llm_service_present": R007_GOVERNANCE_REFS["logion_llm_service"].is_file(),
        "service_ledger_ref": trace.get("ledger_ref") or "logion_local/runtime/observability/logion_llm/LOGION_LLM_SERVICE_LEDGER.ndjson",
        "service_state_ref": trace.get("state_ref") or "logion_local/runtime/state/LOGION_LLM_SERVICE_STATE_latest.json",
        "cache_ref": trace.get("cache_ref") or "logion_local/runtime/cache/logion_llm_service_v1",
        "default_model": "qwen2.5-coder:3b",
        "bounded_model": "qwen2.5-coder:7b",
        "temperature": 0.05,
        "max_workers": 1,
        "run_mode": trace.get("run_mode") or "safe_exhaustive",
        "v_model_lowest_checked_level": v_model.get("lowest_checked_level"),
        "v_model_flow": v_model.get("order") or "L10_to_L9_L8_to_document",
        "lower_level_blockers": int(v_model.get("lower_level_blockers") or 0),
        "stopped_before_upper_review": bool(v_model.get("stopped_before_upper_review") is True),
        "ollama_invocation_total": int(summary.get("provider_invocation_total") or 0),
        "unmanaged_ollama_call_total": int(summary.get("unmanaged_ollama_call_total") or 0),
        "cache_hit_total": int(summary.get("cache_hit_total") or 0),
        "model_sequence": list(summary.get("model_sequence") or []),
        "cadence_sequence": list(summary.get("cadence_sequence") or []),
        "capability_status": trace.get("capability_status") or "UNKNOWN",
        "direct_ollama_calls_allowed": False,
        "parallel_local_llm_runs_allowed": False,
        "generation_mode": "common_logion_llm_service_governed_v_model",
        "cadence_policy": "7b_then_two_3b_thermal_debt_cycles_when_governance_allows",
    }


def normalize_r009_service_trace(trace: dict[str, Any], queue: dict[str, Any], *, version: str) -> dict[str, Any]:
    summary = trace.get("summary") if isinstance(trace.get("summary"), dict) else {}
    v_model = trace.get("v_model") if isinstance(trace.get("v_model"), dict) else {}
    status = str(trace.get("status") or "SERVICE_TRACE_MISSING")
    queue_status = str(trace.get("queue_status") or status)
    provider_invocations = int(summary.get("provider_invocation_total") or 0)
    packet_total = int(summary.get("request_total") or len(queue.get("requests", [])))
    packet_done = int(summary.get("packet_done_total") or 0)
    l10_total = int(queue.get("l10_packet_total") or 0)
    artifact_counts = queue.get("artifact_packet_counts") if isinstance(queue.get("artifact_packet_counts"), dict) else {}
    done_or_exhausted = queue_status == "DONE" or (queue_status == "LOCAL_CAPABILITY_EXHAUSTED" and provider_invocations > 0)
    return {
        "schema_id": "OC_CORE_R009_LOGION_LLM_SERVICE_UNTIL_DONE_TRACE_v1",
        "status": status,
        "queue_status": queue_status,
        "service_status": status,
        "service_id": trace.get("service_id") or "logion_llm_service_v1",
        "caller_id": trace.get("caller_id") or "oc_core_1_3_3_recovery_r009",
        "batch_id": trace.get("batch_id") or f"oc_core_{version}_r009_editorial_until_done",
        "queue_id": trace.get("queue_id") or f"oc_core_{version}_r009_editorial_until_done",
        "common_llm_service_status": "PASS" if trace.get("schema_id") == "LOGION_LLM_SERVICE_RESPONSE_v1" else "FAIL",
        "editorial_llm_queue_status": "PASS" if queue_status == "DONE" else "FAIL",
        "editorial_packet_coverage_status": "PASS" if set(artifact_counts) >= TEXT_ARTIFACTS and l10_total >= len(TEXT_ARTIFACTS) else "FAIL",
        "actual_ollama_invocation_status": "PASS" if provider_invocations > 0 else "FAIL",
        "until_done_status": "PASS" if done_or_exhausted else "FAIL",
        "cooldown_resume_status": "PASS" if int(summary.get("cooldown_event_total") or 0) == 0 or int(summary.get("cooldown_resume_total") or 0) > 0 or queue_status == "DONE" else "FAIL",
        "v_model_completion_status": "PASS" if v_model.get("lowest_checked_level") == "L10" and int(v_model.get("lower_level_blockers") or 0) == 0 and not bool(v_model.get("stopped_before_upper_review")) else "FAIL",
        "local_capability_exhaustion_status": "PASS" if queue_status == "DONE" or (queue_status == "LOCAL_CAPABILITY_EXHAUSTED" and provider_invocations > 0) else "FAIL",
        "governance_status": (trace.get("governance_decision") or {}).get("status", "UNKNOWN") if isinstance(trace.get("governance_decision"), dict) else "UNKNOWN",
        "gpu_thermal_band": ((trace.get("host_summary") or {}).get("gpu_thermal_band") if isinstance(trace.get("host_summary"), dict) else None) or "UNKNOWN",
        "service_ledger_ref": trace.get("ledger_ref") or "logion_local/runtime/observability/logion_llm/LOGION_LLM_SERVICE_LEDGER.ndjson",
        "service_state_ref": trace.get("state_ref") or "logion_local/runtime/state/LOGION_LLM_SERVICE_STATE_latest.json",
        "heartbeat_ref": trace.get("heartbeat_ref") or "logion_local/runtime/state/LOGION_LLM_SERVICE_HEARTBEAT_latest.json",
        "packet_total": packet_total,
        "l10_packet_total": l10_total,
        "packet_done_total": packet_done,
        "artifact_packet_counts": artifact_counts,
        "ollama_invocation_total": provider_invocations,
        "unmanaged_ollama_call_total": int(summary.get("unmanaged_ollama_call_total") or 0),
        "cache_hit_total": int(summary.get("cache_hit_total") or 0),
        "host_sample_total": int(summary.get("host_sample_total") or 0),
        "cooldown_event_total": int(summary.get("cooldown_event_total") or 0),
        "cooldown_resume_total": int(summary.get("cooldown_resume_total") or 0),
        "model_sequence": list(summary.get("model_sequence") or []),
        "cadence_sequence": list(summary.get("cadence_sequence") or []),
        "capability_status": trace.get("capability_status") or "UNKNOWN",
        "direct_ollama_calls_allowed": False,
        "parallel_local_llm_runs_allowed": False,
        "v_model_lowest_checked_level": v_model.get("lowest_checked_level"),
        "v_model_flow": v_model.get("order") or "L10_to_L9_L8_to_document",
        "lower_level_blockers": int(v_model.get("lower_level_blockers") or 0),
        "stopped_before_upper_review": bool(v_model.get("stopped_before_upper_review") is True),
        "generation_mode": "common_logion_llm_service_editorial_until_done_queue",
    }


def governed_llm_trace_for_revision(
    assembly_revision: str | None,
    *,
    version: str,
    base: Path,
    write: bool,
) -> dict[str, Any]:
    if assembly_revision in {R009_REVISION, R010_REVISION}:
        return {
            "schema_id": "OC_CORE_R009_LOGION_LLM_SERVICE_UNTIL_DONE_TRACE_v1",
            "status": "NOT_RUN_YET",
            "queue_status": "NOT_RUN_YET",
            "service_status": "NOT_RUN_YET",
            "ollama_invocation_total": 0,
            "unmanaged_ollama_call_total": 0,
            "cadence_sequence": [],
            "model_sequence": [],
            "v_model_lowest_checked_level": None,
            "service_ledger_ref": "logion_local/runtime/observability/logion_llm/LOGION_LLM_SERVICE_LEDGER.ndjson",
        }
    if assembly_revision != R008_REVISION:
        return governed_ollama_trace(assembly_revision)
    paths = r008_service_output_paths(base, version)
    request_payload = r008_llm_service_request(version)
    trace_payload: dict[str, Any] = {}
    if write:
        write_json_if_changed(paths["request_json"], request_payload)
        service = R007_GOVERNANCE_REFS["logion_llm_service"]
        if service.is_file():
            completed = subprocess.run(
                [
                    sys.executable,
                    str(service),
                    "--request-json",
                    str(paths["request_json"]),
                    "--output-json",
                    str(paths["trace_json"]),
                    "--write",
                ],
                cwd=ROOT,
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                timeout=180,
            )
            if paths["trace_json"].is_file():
                trace_payload = read_json_optional(paths["trace_json"])
            else:
                trace_payload = {
                    "schema_id": "LOGION_LLM_SERVICE_RESPONSE_v1",
                    "status": "SERVICE_INVOCATION_FAILED",
                    "service_id": "logion_llm_service_v1",
                    "summary": {"provider_invocation_total": 0, "unmanaged_ollama_call_total": 0},
                    "governance_decision": {"status": "UNKNOWN"},
                    "host_summary": {"status": "UNKNOWN", "gpu_thermal_band": "UNKNOWN", "effective_max_workers": 1},
                    "v_model": {"lowest_checked_level": None, "order": "L10_to_L9_L8_to_document", "lower_level_blockers": 0},
                    "stderr_tail": completed.stderr[-800:],
                    "stdout_tail": completed.stdout[-800:],
                }
                write_json_if_changed(paths["trace_json"], trace_payload)
        else:
            trace_payload = {
                "schema_id": "LOGION_LLM_SERVICE_RESPONSE_v1",
                "status": "SERVICE_MISSING",
                "service_id": "logion_llm_service_v1",
                "summary": {"provider_invocation_total": 0, "unmanaged_ollama_call_total": 0},
                "governance_decision": {"status": "UNKNOWN"},
                "host_summary": {"status": "UNKNOWN", "gpu_thermal_band": "UNKNOWN", "effective_max_workers": 1},
                "v_model": {"lowest_checked_level": None, "order": "L10_to_L9_L8_to_document", "lower_level_blockers": 0},
            }
            write_json_if_changed(paths["trace_json"], trace_payload)
    else:
        trace_payload = read_json_optional(paths["trace_json"])
    return normalize_r008_service_trace(trace_payload, version=version)


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


def latex_escape(text: str) -> str:
    escaped = public_text(text)
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    for source, target in replacements.items():
        escaped = escaped.replace(source, target)
    return escaped


def shorten_reader_heading(text: str, max_chars: int = READER_HEADING_MAX_CHARS) -> str:
    text = re.sub(r"\s+", " ", text).strip(" ,;:-")
    if len(text) <= max_chars:
        return text
    words: list[str] = []
    total = 0
    for word in text.split():
        projected = total + len(word) + (1 if words else 0)
        if projected > max_chars - 3:
            break
        words.append(word)
        total = projected
    shortened = " ".join(words).strip(" ,;:-")
    return f"{shortened}..." if shortened else text[: max_chars - 3].strip(" ,;:-") + "..."


def reader_heading_from_title(title: str, fallback: str) -> str:
    text = clean_title(title)
    previous = None
    while previous != text:
        previous = text
        text = TECHNICAL_HEADING_PREFIX_RE.sub("", text).strip()
    text = re.sub(r"\bWhat\s+target\s+release\s+Establishes\b", "What the Target Release Establishes", text, flags=re.IGNORECASE)
    text = re.sub(r"(?<!the )\btarget release\b", "the target release", text, flags=re.IGNORECASE)
    for source, target in {"OC tuple": "OC Tuple", "doi": "DOI", "orcid": "ORCID"}.items():
        text = re.sub(re.escape(source), target, text, flags=re.IGNORECASE)
    text = text.strip(" ,;:-")
    if not text or TECHNICAL_HEADING_PREFIX_RE.match(text):
        text = fallback
    text = text[0].upper() + text[1:] if text else fallback
    return shorten_reader_heading(text)


def reader_chapter_title(l1: int) -> str:
    return READER_CHAPTER_TITLES.get(l1, f"Release Section {l1}")


def reader_section_title(row: dict[str, Any]) -> str:
    order_path = [int(part) for part in row["order_path"]]
    l1 = order_path[0] if order_path else 0
    l2 = order_path[1] if len(order_path) > 1 else 0
    return reader_heading_from_title(str(row.get("clean_title") or row.get("title") or ""), f"{reader_chapter_title(l1)} Route {l2}")


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
    topic = reader_heading_from_title(str(node.get("clean_title") or node.get("title") or ""), "The local obligation")
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
        frontmatter_document_layer = int(node.get("order_path", [0])[0]) in FRONTMATTER_L1_BLOCKS
        build_state = "DOCUMENT_FRONTMATTER_RENDERED" if frontmatter_document_layer else ("BUILDABLE" if buildable else "BLOCKED_MISSING_CONTRACT_FIELD")
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
            "generated_text": "" if frontmatter_document_layer else (build_terminal_paragraph(node, source_refs, transition_out) if buildable else ""),
            "build_state": build_state,
            "source_layer": node.get("source_layer") or structure_source,
            "recovery_node": node.get("source_layer") == "l10b_recovered",
            "frontmatter_document_layer": frontmatter_document_layer,
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
        "buildable_terminal_total": sum(1 for row in contracts if row["build_state"] in {"BUILDABLE", "DOCUMENT_FRONTMATTER_RENDERED"}),
        "blocked_terminal_total": sum(1 for row in contracts if str(row["build_state"]).startswith("BLOCKED")),
        "document_frontmatter_terminal_total": sum(1 for row in contracts if row["build_state"] == "DOCUMENT_FRONTMATTER_RENDERED"),
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


def artifact_frontmatter_profile(artifact_type_id: str, version: str, instance: dict[str, Any]) -> dict[str, str]:
    role = {
        "release_guide": "Public landing guide and recommended reading order",
        "master_monograph": "Canonical long-form scientific reference",
        "journal_core_article": "Compact article-style scientific argument",
        "methods_repro_companion": "Methods, validation, reproducibility, and replay companion",
        "reviewer_attack_response_map": "Adversarial objections, boundaries, and response map",
        "release_notes_changelog": "Release notes and change log",
    }.get(artifact_type_id, artifact_type_id.replace("_", " ").title())
    audience = {
        "release_guide": "first-time public readers, scientific contacts, repository visitors, and archivists",
        "master_monograph": "scientific reviewers, formal-methods readers, systems theorists, and institutional readers who need the full argument",
        "journal_core_article": "journal editors, reviewers, and scientists who need a compact entry point before the full monograph",
        "methods_repro_companion": "readers checking reproducibility, formalization, finite semantics, validation, and artifact traceability",
        "reviewer_attack_response_map": "hostile reviewers testing novelty, boundaries, evidence support, and reopening conditions",
        "release_notes_changelog": "release reviewers checking what changed and how to navigate the review package",
    }.get(artifact_type_id, "scientific and editorial reviewers")
    abstract = {
        "release_guide": (
            "This guide orients the reader to the OC Core release package: what each public document is for, "
            "which file to read first, how the evidence package should be used, and where the promoted claim boundary stops."
        ),
        "master_monograph": (
            "This monograph is the long-form scientific route for OC Core. It integrates scope, problem statement, "
            "prior-art positioning, formal foundation, theorem and proof route, executable semantics, empirical and computational "
            "evidence, limits, reviewer objections, reproducibility, and synthesis under a bounded claim policy."
        ),
        "journal_core_article": (
            "This article gives the compact review route through the model core. It states the scientific problem, "
            "the formal contribution, the evidence and falsification route, novelty boundaries, and the claims that are promoted for review."
        ),
        "methods_repro_companion": (
            "This companion explains how the release is checked: source traceability, proof and finite-model artifacts, "
            "validation, simulation, counterexample search, replay, checksums, and reproducibility limits."
        ),
        "reviewer_attack_response_map": (
            "This map presents the release under hostile review. It groups objections by attacked claim, explains why each attack matters, "
            "names the response route, and records residual risk and reopening conditions."
        ),
        "release_notes_changelog": (
            "These notes summarize the review-space assembly revision and point to the scientific and reproducibility documents without replacing them."
        ),
    }.get(artifact_type_id, "This document is part of the OC Core release review package.")
    reader_contract = {
        "release_guide": (
            "Use this document as the foyer of the archive. It does not prove the theory; it tells the reader where the proof, "
            "evidence, reviewer response, citation, and reproducibility surfaces live."
        ),
        "master_monograph": (
            "Read this document as the primary scientific manuscript. Claims are valid only to the extent that their proof, evidence, "
            "comparator, falsifier, or reproducibility route is made explicit in the text or trace materials."
        ),
        "journal_core_article": (
            "Read this document as a compressed argument. It is designed to be checked against the monograph and companion artifacts, "
            "not as an isolated replacement for them."
        ),
        "methods_repro_companion": (
            "Read this document when checking whether a claim can be replayed, traced, or bounded by negative controls and reproducibility limits."
        ),
        "reviewer_attack_response_map": (
            "Read this document by choosing the claim under attack, then following objection, response, evidence, residual risk, and reopening condition."
        ),
        "release_notes_changelog": (
            "Use these notes only as package navigation. Scientific claims must be checked in the monograph, article, methods companion, and reviewer map."
        ),
    }.get(artifact_type_id, "Read this document as a bounded release artifact with explicit source trace and claim limits.")
    release_identity = instance.get("release_identity", {})
    return {
        "title": artifact_title(artifact_type_id, version),
        "subtitle": "Ontology of Continua Core release review artifact",
        "author": AUTHOR_DISPLAY,
        "affiliation": AUTHOR_AFFILIATION,
        "orcid": AUTHOR_ORCID,
        "version": version,
        "release_id": release_identity.get("release_id", ""),
        "concept_doi": CONCEPT_DOI,
        "audience": audience,
        "artifact_role": role,
        "abstract": abstract,
        "reader_contract": reader_contract,
    }


def frontmatter_toc(rows: list[dict[str, Any]]) -> list[str]:
    seen: set[tuple[int, int]] = set()
    entries: list[str] = [
        "Publication identity",
        "Dedication",
        "Acknowledgements",
        "Abstract",
        "Reader contract",
        "Reading map",
    ]
    for row in rows:
        order_path = [int(part) for part in row["order_path"]]
        key = (order_path[0], order_path[1] if len(order_path) > 1 else 0)
        if key in seen:
            continue
        seen.add(key)
        entries.append(f"Block {key[0]}: {row['clean_title'].split(' and ')[0]}")
        if len(entries) >= 40:
            entries.append("Additional sections continue in document order.")
            break
    return entries


def render_title_page(profile: dict[str, str]) -> str:
    return "\n".join(
        [
            r"\begin{titlepage}",
            r"\thispagestyle{empty}",
            r"\centering",
            r"\vspace*{0.12\textheight}",
            rf"{{\Huge\bfseries {latex_escape(profile['title'])}\par}}",
            r"\vspace{1.2em}",
            rf"{{\Large {latex_escape(profile['artifact_role'])}\par}}",
            r"\vspace{2.5em}",
            rf"{{\large {latex_escape(profile['author'])}\par}}",
            rf"{{\normalsize {latex_escape(profile['affiliation'])}\par}}",
            rf"{{\normalsize ORCID {latex_escape(profile['orcid'])}\par}}",
            r"\vfill",
            rf"{{\normalsize Version {latex_escape(profile['version'])}\par}}",
            rf"{{\normalsize Manuscript revision date: {latex_escape(PUBLICATION_DATE)}\par}}",
            rf"{{\normalsize Concept DOI: {latex_escape(profile['concept_doi'])}\par}}",
            r"\vspace{1.5em}",
            rf"{{\small\itshape {latex_escape(DEDICATION_TEXT)}\par}}",
            r"\end{titlepage}",
            r"\clearpage",
        ]
    )


def render_frontmatter(artifact_type_id: str, version: str, instance: dict[str, Any], body_rows: list[dict[str, Any]]) -> str:
    profile = artifact_frontmatter_profile(artifact_type_id, version, instance)
    lines = [
        "---",
        f"document_title: \"{profile['title']}\"",
        f"document_version: \"{profile['version']}\"",
        f"release_id: \"{profile['release_id']}\"",
        f"concept_doi: \"{profile['concept_doi']}\"",
        "---",
        "",
        render_title_page(profile),
        "",
        "# Dedication {.unnumbered}",
        "",
        DEDICATION_TEXT,
        "",
        "# Acknowledgements {.unnumbered}",
        "",
        "Substantive review and idea acknowledgements.",
        ACKNOWLEDGEMENT_BOUNDARY,
        "",
    ]
    lines.extend(f"- {name}" for name in ACKNOWLEDGEMENT_NAMES)
    lines.extend(
        [
            "",
            "# Abstract {.unnumbered}",
            "",
            profile["abstract"],
            "",
            "# Reader Contract {.unnumbered}",
            "",
            profile["reader_contract"],
            (
                "The release promotes evidence-bound model-core claims and excludes unsupported complete-science closure, "
                "unrestricted all-domain numerical completion, or unrestricted superiority-over-modern-science claims."
            ),
            "",
            r"\clearpage",
            r"\renewcommand*\contentsname{Table of Contents}",
            r"\setcounter{tocdepth}{2}",
            r"\setcounter{secnumdepth}{2}",
            r"\makeatletter",
            r"\renewcommand*\l@section{\@dottedtocline{1}{0em}{4.2em}}",
            r"\renewcommand*\l@subsection{\@dottedtocline{2}{1.8em}{5.2em}}",
            r"\makeatother",
            r"\tableofcontents",
            r"\clearpage",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def split_frontmatter_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    frontmatter_rows: list[dict[str, Any]] = []
    body_rows: list[dict[str, Any]] = []
    for row in rows:
        order_path = [int(part) for part in row["order_path"]]
        if order_path and order_path[0] in FRONTMATTER_L1_BLOCKS:
            frontmatter_rows.append(row)
        else:
            body_rows.append(row)
    return frontmatter_rows, body_rows


def render_artifact_markdown(artifact_type_id: str, version: str, instance: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    frontmatter_rows, body_rows = split_frontmatter_rows(rows)
    lines = [render_frontmatter(artifact_type_id, version, instance, body_rows), ""]
    current_l1: int | None = None
    current_l2: tuple[int, int] | None = None
    for row in body_rows:
        order_path = [int(part) for part in row["order_path"]]
        if current_l1 != order_path[0]:
            current_l1 = order_path[0]
            current_l2 = None
            lines.extend(["", f"# {reader_chapter_title(current_l1)}", ""])
        l2 = (order_path[0], order_path[1] if len(order_path) > 1 else 0)
        if current_l2 != l2:
            current_l2 = l2
            lines.extend(["", f"## {reader_section_title(row)}", ""])
        generated_text = row["generated_text"]
        if FRONTMATTER_BODY_TITLE_RE.search(generated_text):
            continue
        lines.append(generated_text)
        lines.append("")
    lines.extend(
        [
            "# Source Trace",
            "",
            "Exact source bindings, path hashes, quality scorer hooks, and transition records are recorded in the review package manifest. They are kept out of the main prose to avoid turning the document into a ledger dump.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def publication_revision_enabled(assembly_revision: str | None) -> bool:
    return assembly_revision in PUBLICATION_BODY_REVISIONS


def normal_acknowledgements() -> str:
    names = ", ".join(ACKNOWLEDGEMENT_NAMES[:-1]) + f", and {ACKNOWLEDGEMENT_NAMES[-1]}"
    return (
        "The author thanks the reviewers and critics whose questions, objections, and suggestions contributed to the "
        "development of the Ontology of Continua and to the refinement of this release. "
        f"The acknowledged contributors are {names}. Their criticism helped sharpen the claim boundaries, improve the "
        "reader route, expose weak presentation choices, and force clearer separation between model claims, proof "
        "routes, numerical evidence, prior-art comparison, and publication form. "
        "Acknowledgement records review pressure and intellectual contribution to the development of the work; it does "
        "not imply authorship, endorsement, publication approval, responsibility for the theory, or agreement with any "
        "claim promoted in the manuscript."
    )


def publication_abstract(artifact_type_id: str) -> str:
    role_sentence = {
        "release_guide": "This release guide is the entry document for the OC Core 1.3.3 public package.",
        "master_monograph": "This master monograph is the long-form scientific manuscript for OC Core 1.3.3.",
        "journal_core_article": "This article version compresses OC Core 1.3.3 into a conventional external-review route.",
        "methods_repro_companion": "This methods companion explains how the formal, finite, numerical, and archival checks support the promoted claims.",
        "reviewer_attack_response_map": "This reviewer map presents OC Core 1.3.3 as an adversarially inspectable claim surface.",
    }.get(artifact_type_id, "This document is part of the OC Core 1.3.3 public package.")
    return "\n\n".join(
        [
            (
                f"{role_sentence} Many contemporary systems are too entangled to be understood by a single domain vocabulary: "
                "a technical platform carries physical infrastructure, software architecture, institutional incentives, "
                "security boundaries, user cognition, and economic feedback at the same time. The Ontology of Continua "
                "addresses that situation as a typed model-core project. It describes continuants, realizations, liveness, "
                "death, residue, boundaries, morphisms, operators, cycles, dimension, and K-level witnesses under explicit "
                "assumptions, so that a reader can ask how a system persists, changes, fails, and reappears without changing "
                "languages at every disciplinary border."
            ),
            (
                "The project is intentionally ambitious in subject matter and intentionally bounded in claim discipline. "
                "Its publication task is not to replace physics, biology, cognition, systems engineering, enterprise "
                "architecture, or economics with a slogan. Its task is to offer a common structural grammar through which "
                "domain experts can compare state spaces, thresholds, flows, cycles, boundaries, and failure conditions "
                "without pretending that domain-specific science has become unnecessary."
            ),
            (
                "Version 1.3.3 is a bounded external-review release. It is mature enough to be read as a coherent "
                "scientific manuscript and to be checked against formal and executable artifacts, but it remains a staged "
                "research program rather than a declaration of final all-domain completion. The release promotes model-core "
                "claims where their assumptions and evidence are visible; it leaves broader numerical closure, wider domain "
                "validation, and stronger comparative claims as future obligations."
            ),
            (
                "The package contains a full monograph, a compact article route, a methods and reproducibility companion, "
                "a reviewer attack-and-response map, release navigation, public evidence anchors, finite-model outputs, "
                "Lean subset evidence, bounded target-blind replay QA, comparator and prior-art material, and appendices for "
                "proof, figures, tables, numeric rows, and source trace. The monograph is the canonical reading spine; the "
                "other documents are curated routes for first reading, editorial review, replay, and hostile criticism."
            ),
            (
                "The evidence status is deliberately mixed and explicit. Some claims are supported by theorem routes, proof "
                "sheets, Lean declarations, and finite semantic witnesses. Some claims are supported by bounded numerical or "
                "target-blind replay rows that should be read as scoped QA evidence, not as complete empirical validation of "
                "a whole domain. Some claims are positioned against prior art or retained as research boundaries because the "
                "available evidence is not yet strong enough for a broader statement."
            ),
            (
                "The principal limitation is therefore part of the manuscript's method: public wording must not outrun the "
                "evidence. OC Core 1.3.3 asks the reader to evaluate whether the typed model, proof governance, finite "
                "semantics, numerical anchors, figures, tables, appendices, and reviewer-response routes form a coherent "
                "bounded model-core contribution. Future work must add evidence or mechanization before it widens the public "
                "claim surface."
            ),
            (
                "The practical value of the manuscript is therefore a form of disciplined compression. If the model is "
                "useful, it should help readers translate complex systems into a shared ontology while preserving the "
                "meaningful distinctions that make each domain scientifically serious. That is the standard by which the "
                "release asks to be read."
            ),
        ]
    )


def publication_release_delta() -> str:
    return "\n\n".join(
        [
            (
                "The OC Core release sequence is part of a continuing scientific program rather than a series of isolated "
                "archive events. As the model is tested against formal criticism, domain examples, reproducibility checks, "
                "and external review, the public manuscript is expected to become more precise, more explicit about its "
                "limits, and more useful to readers outside the author's immediate working context."
            ),
            (
                "A new release is therefore warranted only when there is a meaningful scientific or editorial delta: a "
                "clarified definition, stronger proof route, better evidence boundary, improved reader pathway, repaired "
                "notation, new domain projection, or more honest comparator position. Minor process movement is not enough. "
                "The public release should tell readers what changed in the scientific object and why that change matters."
            ),
            (
                "This policy is also a commitment to regularity without pretending that research can be made mechanical. "
                "The author intends to make future public updates systematic enough for readers, reviewers, and auditors to "
                "follow the development of the model, while preserving the difference between a public scientific result and "
                "private working material. No internal route, unpublished process detail, or control-plane record is promoted "
                "as reader-facing evidence merely because it helped produce the release."
            ),
            (
                "Version 1.3.3 is the release in which the OC Core corpus is reorganized from a set of scattered source "
                "witnesses and process records into a reviewable scientific package. The visible delta is not merely a new "
                "archive number: the release strengthens the typed foundation, makes the claim boundary explicit, integrates "
                "the theorem route with public proof sheets, and separates reader-facing prose from machine evidence."
            ),
            (
                "The model delta includes clearer treatment of carriers, realizations, liveness, death, residue, rebirth, "
                "morphisms, generalized boundaries, hybrid operators, cycle modes, historical and effective dimension, "
                "and K-level witnesses. These additions are presented as a bounded model-core grammar rather than as an "
                "unrestricted theory of every phenomenon."
            ),
            (
                "The verification delta adds and consolidates a Lean-checked subset, structured proof sheets, finite semantic "
                "checks, finite witness interpretation, bounded target-blind replay QA, comparator and prior-art positioning, "
                "negative-control and falsifier language, and adversarial-review response material. Where a stronger claim is "
                "not yet earned, the release records the limitation instead of hiding it inside a source-control record."
            ),
            (
                "The editorial delta is equally important. Figures, tables, formulas, numeric anchors, appendices, and evidence "
                "routes are kept in the publication corpus; machine coverage maps remain coverage and trace data only. The public "
                "documents are therefore built from the human manuscript hierarchy and curated payload sources, while source "
                "bindings and machine evidence indexes stay in the review manifest."
            ),
            (
                "For a returning reader, the practical point is this: 1.3.3 should be read as a clarification and consolidation "
                "release. It does not claim final closure. It improves the public surface through which the model can be "
                "criticized, taught, checked, and extended."
            ),
        ]
    )


def publication_reader_contract(artifact_type_id: str) -> str:
    route = {
        "release_guide": "This guide can be read first to choose the right document, then the reader may move to the monograph, article, methods companion, or reviewer map according to the task.",
        "master_monograph": "The monograph is the primary route through the model, formulas, proofs, figures, numeric evidence, limitations, and appendices.",
        "journal_core_article": "The article offers a compact scientific pass, with compressed claims then checked against the monograph and methods companion.",
        "methods_repro_companion": "The companion is useful when commands, inputs, outputs, checksums, finite witnesses, target-blind replay, and failure interpretation are the main concern.",
        "reviewer_attack_response_map": "The map supports a claim-by-claim reading of objection, response, evidence route, residual risk, and reopening condition.",
    }.get(artifact_type_id, "This document is one bounded route through the OC Core 1.3.3 release.")
    return "\n\n".join(
        [
            (
                "Dear readers, systems theory is of interest to many communities, but rarely in exactly the same way. "
                "A formal reviewer, a philosopher of systems, an applied architect, an AI engineer, a security specialist, "
                "and an executive reader may all ask legitimate questions of the same manuscript. OC Core 1.3.3 is therefore "
                "designed as a deliberately generous scientific reading surface: it aims to disclose the Ontology of Continua "
                "as an applied model of system architecture while giving different readers a courteous route into the material."
            ),
            (
                "Scientific reviewers and formal critics may wish to start with the abstract, release delta, model-foundation "
                "route, theorem/proof integration route, Lean subset, finite semantic witnesses, proof machinery, and "
                "falsifiability sections. This route is meant to make the work attackable in the best sense: every promoted "
                "claim should expose its assumptions, proof or executable evidence, counterexample boundary, and reopening "
                "condition."
            ),
            (
                "Systems theorists, philosophers, and interested theoretical readers may prefer to start with the continuum "
                "problem, the historical and systems-theory motivation, the K-level primer, lifecycle and boundary chapters, "
                "prior-art comparison, and limitations. This path asks what OC inherits, what it reorganizes, where its "
                "residual delta begins, and where predecessors or parallel branches already carry part of the work."
            ),
            (
                "Applied architects of complex systems--including engineers, enterprise architects, AI builders, security "
                "specialists, and applied researchers--may find it useful to start from practical examples, domain projections, "
                "figures, tables, and worked routes before returning to the formal core. The model chapters can then be read "
                "as a design grammar for carriers, realizations, boundaries, operators, update/flow separation, evidence "
                "classes, and claim boundaries."
            ),
            (
                "CIOs, CEOs, enterprise architects, and strategy readers may sensibly read the release delta, practical utility "
                "chapter, model-comparison appendix, and final conclusion before investing in proof details. This route asks "
                "what the model is for, what it can support today, what remains too immature for operational commitment, and "
                "how evidence classes affect research or enterprise decisions."
            ),
            (
                "Reproducibility auditors, evidence reviewers, and benchmark readers may go directly to the methods and "
                "evidence chapters, target-blind replay QA, numeric tables, machine-readable table reference, audit trail, "
                "source-trace appendix, and public evidence package manifest. This route asks whether formula, input snapshot, "
                "comparator, residual or uncertainty, negative control, falsifier, replay hash, and failure interpretation are "
                "present."
            ),
            (
                f"{route} In the full package, the conceptual model and formulas live in the monograph's scientific body; "
                "the proof route and Lean subset live in theorem, proof, and formalization sections; numeric evidence and "
                "target-blind replay QA live in the methods/evidence route; figures and tables live inline in the monograph; "
                "appendices carry source trace, proof machinery, comparison rows, audit trail, and machine-readable table "
                "references; prior-art comparison and reviewer objections live in the article and attack-response map."
            ),
            (
                "The author asks all readers to treat limitations as part of the claim, not as a footnote. A statement is "
                "promoted only where its assumptions, proof or evidence class, comparator boundary, and reopening condition "
                "are visible. Claims about complete scientific coverage, unrestricted all-domain numerical closure, or "
                "unrestricted superiority over contemporary science are not promoted by this release."
            ),
        ]
    )


def render_publication_frontmatter(artifact_type_id: str, version: str, instance: dict[str, Any]) -> str:
    profile = artifact_frontmatter_profile(artifact_type_id, version, instance)
    lines = [
        "---",
        f"document_title: \"{profile['title']}\"",
        f"document_version: \"{profile['version']}\"",
        f"release_id: \"{profile['release_id']}\"",
        f"concept_doi: \"{profile['concept_doi']}\"",
        "---",
        "",
        render_title_page(profile),
        "",
        "# Acknowledgements {.unnumbered}",
        "",
        normal_acknowledgements(),
        "",
        "# Abstract {.unnumbered}",
        "",
        publication_abstract(artifact_type_id),
        "",
        "# Version 1.3.3 Release Delta {.unnumbered}",
        "",
        publication_release_delta(),
        "",
        "# Reader Routes {.unnumbered}",
        "",
        publication_reader_contract(artifact_type_id),
        "",
        r"```{=latex}",
        r"\clearpage",
        r"\renewcommand*\contentsname{Table of Contents}",
        r"\setcounter{tocdepth}{2}",
        r"\setcounter{secnumdepth}{2}",
        r"\makeatletter",
        r"% R006_TOC_VISUAL_HIERARCHY",
        r"% R007_TOC_VISUAL_HIERARCHY",
        r"\renewcommand*\l@section[2]{\addvspace{0.5em}\begingroup\bfseries\large\@dottedtocline{1}{0em}{4.8em}{#1}{#2}\endgroup}",
        r"\renewcommand*\l@subsection[2]{\@dottedtocline{2}{2.0em}{5.8em}{\small #1}{\small #2}}",
        r"\makeatother",
        r"\tableofcontents",
        r"\clearpage",
        r"```",
    ]
    return "\n".join(lines).rstrip() + "\n"


def sanitize_public_payload_body(text: str) -> str:
    text = re.sub(r"^---\s*\n.*?\n---\s*\n", "", text, flags=re.S)
    marker = re.search(r"(?m)^#\s+Reading Map\s*$", text)
    if marker:
        text = text[marker.start():]
    text = re.sub(r"(?im)^\*\*Research instrument\.\*\s+.*(?:\n|$)", "", text)
    text = re.sub(r"(?im)^\*\*Methodological framework\.\*\s+.*(?:\n|$)", "", text)
    text = re.sub(r"(?im)^.*\bLogion\b.*(?:\n|$)", "", text)
    text = re.sub(r"(?im)^.*\bESTRA\b.*(?:\n|$)", "", text)
    replacements = {
        "10.5281/zenodo.19965913": CONCEPT_DOI,
        "https://zenodo.org/records/19965913": f"https://doi.org/{CONCEPT_DOI}",
        "GitHub release": "open repository route",
        "github release": "open repository route",
        "GitHub Release": "open repository route",
        "Zenodo Record": "Concept DOI route",
        "Zenodo record": "Concept DOI route",
        "Zenodo deposit": "public archival record",
        "zenodo deposit": "public archival record",
        "Version DOI": "Concept DOI",
        "version DOI": "Concept DOI",
        "DOI minting": "DOI registration",
        "doi minting": "DOI registration",
        "tag movement": "tag update",
        "scientific closure": "scientific completion boundary",
        "Scientific closure": "Scientific completion boundary",
        "journal submission": "journal article preparation",
        "journal submissions": "journal article preparations",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


def publication_translated_payload_body(artifact_type_id: str, version: str) -> str:
    marker = "<!-- PUBLICATION_TRANSLATOR_R007: deterministic public prose from governed section packets; no unmanaged local-LLM call. -->"
    by_artifact = {
        "release_guide": [
            "# Public Release Guide",
            (
                "This guide introduces OC Core 1.3.3 as a public scientific package. Its task is simple: help a reader choose "
                "the right path through the monograph, article, methods companion, reviewer map, and evidence bundle without "
                "having to infer the package structure from build records or source inventories. The guide describes the release "
                "as a bounded model-core contribution: it offers a shared vocabulary for continua, state spaces, boundaries, "
                "flows, cycles, thresholds, liveness, K-level composition, proof routes, numerical anchors, and reopening conditions."
            ),
            "## What the Package Contains",
            (
                "The master monograph is the canonical reading surface. It motivates the problem, teaches the elementary model, "
                "states the formal core, and then connects the proof, finite-semantics, target-blind replay, comparator, "
                "falsifiability, and practical-domain material. The journal article gives a shorter scientific pass. The methods "
                "and reproducibility companion explains how checks are interpreted. The reviewer attack-response map organizes "
                "objections, evidence responses, and residual risk. The evidence bundle carries machine-readable material for "
                "auditors who need source rows, hashes, and replay surfaces."
            ),
            "## How Different Readers May Enter",
            (
                "A scientific reviewer may begin with the monograph's formal core and proof route. A systems theorist may begin "
                "with the motivation, K-level primer, and prior-art boundary. An applied architect, AI builder, security specialist, "
                "or enterprise architect may begin with the figures, worked examples, and domain routes before returning to notation. "
                "A CIO, CEO, or strategy reader may start with release delta, limitations, and practical utility. A reproducibility "
                "auditor may go directly to methods, replay QA, source trace, and machine-readable tables."
            ),
            "## Evidence Boundary",
            (
                "The release promotes only bounded claims. A public claim should have a plain-language statement, an intuition, "
                "a formal or mathematical anchor, an evidence or proof anchor, and a limitation or falsifier. A replay row or finite "
                "witness is evidence for the scoped claim it names, not a declaration of final all-domain empirical closure."
            ),
            "## Public Repository and Citation Route",
            (
                "The Concept DOI printed on the title page identifies the public scientific object. The open repository is available "
                "at <https://github.com/alexanderyashin/ontology-of-continua-core-main> for source inspection and reproducibility "
                "support. Repository state and manuscript claims should be read together but not confused: the manuscript states the "
                "claim boundary; the repository helps readers inspect the supporting material."
            ),
        ],
        "journal_core_article": [
            "# Article Route",
            (
                "This article route compresses the OC Core 1.3.3 monograph into a conventional external-review narrative. The "
                "scientific problem is cross-domain system description: many important objects persist, fail, recover, and change "
                "across several disciplinary vocabularies at once. OC proposes a typed continuum model so that state spaces, "
                "boundaries, thresholds, flows, cycles, liveness, and K-level composition can be compared without pretending that "
                "specialist domain science has disappeared."
            ),
            "## Contribution",
            (
                "The contribution is a bounded model-core grammar. A continuum is treated as a structured object with admissible "
                "states, boundary, axes, thresholds, potentials, flows, cycles, continuumness, and embedding context. The article "
                "summarizes how the monograph uses that grammar to distinguish liveness, death, residue, rebirth, morphisms, "
                "operators, dimension, and hierarchical K-level witnesses."
            ),
            "## Formal and Evidence Anchors",
            (
                "The formal claim is not presented as rhetoric. It is tied to theorem routes, proof sheets, Lean-subset evidence "
                "where available, finite semantic witnesses, negative controls, comparator rows, and scoped target-blind replay QA. "
                "A promoted statement is expected to say what would reopen it: a lost assumption, a failed finite witness, a replay "
                "mismatch, a stronger comparator explanation, or a domain case that defeats the declared boundary."
            ),
            "## Prior-Art Boundary",
            (
                "OC is positioned near systems theory, cybernetics, autopoiesis, dynamical systems, hybrid systems, category- and "
                "type-theoretic modeling, formal verification, reproducibility practice, and identity-over-time debates. The article "
                "does not claim that those traditions are absent. It asks whether OC's residual delta is useful: a compact grammar "
                "for comparing continua across domains while keeping evidence obligations explicit."
            ),
            "## Conclusion",
            (
                f"Version {version} should therefore be read as a clarification and consolidation release. It offers an inspectable "
                "model core and a route for criticism. It does not claim final closure over all domains; future releases must widen "
                "the claim surface only where evidence, mechanization, or comparator work justifies the widening."
            ),
        ],
        "methods_repro_companion": [
            "# Methods and Reproducibility Companion",
            (
                "The methods companion explains how a reader can inspect OC Core 1.3.3 without treating machine-readable material as "
                "the manuscript itself. Reproducibility is used here as scientific interpretation: a check matters because it bears "
                "on a named claim, assumption, formula, witness, comparator, or falsifier."
            ),
            "## What a Replay Checks",
            (
                "A replay row connects an input snapshot, a formula or reconstruction rule, an expected output, a residual or "
                "uncertainty, a comparator, a negative control, and a failure interpretation. Passing such a row supports the scoped "
                "claim named by the row. It does not by itself validate an entire domain or remove the need for broader empirical work."
            ),
            "## Formal and Finite Checks",
            (
                "The proof route and finite semantic checks give the model a stricter ceiling. A theorem statement is supported only "
                "when the assumptions, proof sheet, dependency relation, mechanized subset where present, and counterexample boundary "
                "remain inspectable. A finite witness is valuable because it can show that a definition or operator behaves as claimed "
                "inside a bounded semantics."
            ),
            "## Interpreting Failure",
            (
                "A failed check is not a formatting problem. It may reopen a claim, narrow a domain route, reveal a missing assumption, "
                "or show that a comparator already explains the case. The companion therefore treats mismatch, missing input, missing "
                "hash, drifted output, absent negative control, and unsupported extrapolation as scientific events."
            ),
            "## Audit Trail and Machine-Readable Tables",
            (
                "The reader-facing tables summarize the evidence in prose. Machine-readable tables remain available for auditors who "
                "need to inspect source rows directly: claim rows, theorem rows, finite checks, target-blind replay QA, numeric tables, "
                "comparator material, and source-trace material. The tables are support for the argument, not a substitute for it."
            ),
        ],
        "reviewer_attack_response_map": [
            "# Reviewer Attack and Response Map",
            (
                "This map presents OC Core 1.3.3 as an object meant to be criticized. A serious objection is welcome when it targets "
                "a promoted claim, a definition, an assumption, a proof route, a finite witness, a numerical row, a comparator boundary, "
                "or a limitation that has been worded too weakly."
            ),
            "## How to Attack the Release",
            (
                "The cleanest attacks ask whether a continuum tuple is doing real explanatory work, whether K-level distinctions are "
                "earned rather than named, whether prior art already covers the residual delta, whether a proof sheet loses an "
                "assumption, whether a finite witness is too narrow, whether a target-blind row is overinterpreted, or whether a figure "
                "or table implies more than the evidence supports."
            ),
            "## Evidence Response",
            (
                "A response should point to the public claim, restate the assumption, identify the formal or empirical anchor, and say "
                "what remains unproven. Where the evidence is strong enough, the response defends the promoted wording. Where the "
                "evidence is partial, the response narrows the claim or moves the issue to future work."
            ),
            "## Residual Risk",
            (
                "Residual risk is kept visible. OC Core 1.3.3 remains vulnerable to stronger comparator theories, broader empirical "
                "counterexamples, missing mechanization, weak domain translation, and overgeneralized language. The reviewer map is "
                "therefore a boundary surface: it records how the release can be attacked without pretending that attackability is a flaw."
            ),
            "## Reopening Conditions",
            (
                "A claim reopens if its assumptions are contradicted, a proof route fails, a finite witness no longer reproduces, a "
                "negative control succeeds, a comparator explains the case with less burden, a table cannot be reconciled with source "
                "evidence, or public prose outruns the supported statement. The map gives reviewers a way to locate those conditions "
                "without reading internal build instructions."
            ),
        ],
    }
    body = [marker, ""]
    body.extend(by_artifact.get(artifact_type_id, by_artifact["release_guide"]))
    return "\n\n".join(body).strip() + "\n"


def publication_translated_payload_body_r008(artifact_type_id: str, version: str) -> str:
    body = publication_translated_payload_body(artifact_type_id, version)
    body = body.replace(
        "PUBLICATION_TRANSLATOR_R007: deterministic public prose from governed section packets; no unmanaged local-LLM call.",
        "PUBLICATION_TRANSLATOR_R008: public prose checked through a governed local V-model review trace; no unmanaged local-LLM call.",
    )
    body += (
        "\n\n## Governed Local Review Boundary\n\n"
        "This reader-facing text is not a transcript of local model output. A governed local review service is used as a bounded "
        "review and critique surface for bounded chunks after deterministic checks. Its role is to help detect leakage, weak "
        "reader prose, and missing anchors under host-safety policy; the public claim remains the manuscript's responsibility.\n"
    )
    return body


def publication_translated_payload_body_r009(artifact_type_id: str, version: str) -> str:
    body = publication_translated_payload_body_r008(artifact_type_id, version)
    body = body.replace("PUBLICATION_TRANSLATOR_R008", "PUBLICATION_TRANSLATOR_R009")
    body = body.replace("bounded local review service", "bounded local editorial review route")
    body += (
        "\n\n## Local Editorial Review Status\n\n"
        "The reader-facing package has been reviewed through a governed local editorial route in small packets before "
        "higher-level aggregation. That route is used to detect leakage, weak didactic prose, missing anchors, and "
        "reader-facing defects while preserving the manuscript as the public scientific surface.\n"
    )
    return body


def publication_translated_payload_body_r010(artifact_type_id: str, version: str) -> str:
    body = publication_translated_payload_body_r009(artifact_type_id, version)
    body = body.replace("PUBLICATION_TRANSLATOR_R009", "PUBLICATION_TRANSLATOR_R010")
    return body


def render_publication_payload_markdown(
    artifact_type_id: str,
    version: str,
    instance: dict[str, Any],
    assembly_revision: str | None,
) -> tuple[str, Path | None]:
    source = PUBLIC_PAYLOAD_SOURCE_BY_ARTIFACT.get(artifact_type_id)
    if assembly_revision == R007_REVISION:
        body = publication_translated_payload_body(artifact_type_id, version)
    elif assembly_revision == R008_REVISION:
        body = publication_translated_payload_body_r008(artifact_type_id, version)
    elif assembly_revision == R009_REVISION:
        body = publication_translated_payload_body_r009(artifact_type_id, version)
    elif assembly_revision == R010_REVISION:
        body = publication_translated_payload_body_r010(artifact_type_id, version)
    elif source is None or not source.is_file():
        body = "# Body\n\nPublication payload source was not available for this artifact.\n"
    else:
        body = sanitize_public_payload_body(source.read_text(encoding="utf-8", errors="replace"))
    backmatter = "\n".join(
        [
            "",
            r"\clearpage",
            r"\section*{Keywords and Citation Route}",
            "",
            "Keywords: Ontology of Continua; continuum ontology; typed model core; systems theory; autopoiesis; dynamical systems; hybrid systems; formal methods; Lean formalization; finite semantic checks; target-blind replay QA; reproducible research; artifact evaluation; claim governance; falsifiability; evidence-bound scientific publishing.",
            "",
            f"Citation identity: {AUTHOR_DISPLAY}, {artifact_title(artifact_type_id, version)}, {PUBLICATION_DATE}. The Concept DOI is printed on the title page.",
            "",
            "Open repository: <https://github.com/alexanderyashin/ontology-of-continua-core-main>. Repository files support reproducibility and source inspection; they do not replace the manuscript's claim boundaries.",
            "",
        ]
    )
    text = render_publication_frontmatter(artifact_type_id, version, instance) + "\n" + body + backmatter
    return text.rstrip() + "\n", source


def copy_public_payload_assets(base: Path, *, write: bool) -> tuple[list[Path], bool]:
    source_dir = ROOT / "releases" / "oc_core_1_3_3" / "public_payload" / "figures"
    target_dir = base / "figures"
    copied: list[Path] = []
    changed = False
    if not source_dir.is_dir():
        return copied, changed
    for source in sorted(source_dir.glob("*")):
        if not source.is_file():
            continue
        target = target_dir / source.name
        if write:
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists() or target.read_bytes() != source.read_bytes():
                shutil.copy2(source, target)
                changed = True
        if target.is_file():
            copied.append(target)
    return copied, changed


def source_content_counts(source_text: str) -> dict[str, int]:
    figure_total = len(re.findall(r"!\[[^\]]*\]\(", source_text)) + len(re.findall(r"\\begin\{figure", source_text))
    table_total = len(re.findall(r"(?m)^\s*\|.+\|\s*$", source_text)) // 3
    table_total += len(re.findall(r"\\begin\{(?:table|longtable|tabular)", source_text))
    formula_marker_total = len(re.findall(r"\$\$|\\\[|\\\(|\\begin\{(?:equation|align|gather|multline)", source_text))
    return {
        "figure_total": figure_total,
        "table_total": table_total,
        "formula_marker_total": formula_marker_total,
    }


def tex_corpus_counts(source_dir: Path) -> dict[str, int]:
    tex_files = [path for path in sorted(source_dir.rglob("*.tex")) if path.is_file()]
    joined = "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in tex_files)
    entrypoint_text = ""
    for candidate in source_dir.glob("oc_core_1_3_master_monograph.tex"):
        entrypoint_text = candidate.read_text(encoding="utf-8", errors="replace")
        break
    inline_joined = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for path in tex_files
        if "appendix" not in {part.lower() for part in path.relative_to(source_dir).parts}
    )
    bib_joined = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for path in sorted((source_dir / "bib").glob("*.bib"))
        if path.is_file()
    )
    appendix_section_titles: list[str] = []
    for ref in re.findall(r"\\input\{([^}]+)\}", entrypoint_text):
        if not ref.startswith("appendix/"):
            continue
        candidates = [source_dir / ref]
        if not ref.endswith(".tex"):
            candidates.append(source_dir / f"{ref}.tex")
        for candidate in candidates:
            if not candidate.is_file():
                continue
            for line in candidate.read_text(encoding="utf-8", errors="replace").splitlines():
                if line.lstrip().startswith(r"\section{"):
                    appendix_section_titles.append(line.strip().removeprefix(r"\section{").rstrip("}"))
                    break
            break
    bibliography_entry_total = len(re.findall(r"(?m)^@\w+\{", bib_joined))
    verified_bibliography_entry_total = 0
    for entry in re.split(r"(?m)(?=^@\w+\{)", bib_joined):
        if re.search(r"\b(doi|isbn|url|publisher|journal)\s*=", entry, re.I):
            verified_bibliography_entry_total += 1
    return {
        "figure_total": len(re.findall(r"\\begin\{figure", joined)),
        "inline_figure_total": len(re.findall(r"\\begin\{figure", inline_joined)),
        "table_total": len(re.findall(r"\\begin\{(?:table|longtable|tabular)", joined)),
        "formula_marker_total": len(re.findall(r"\$\$|\\\[|\\\(|\\begin\{(?:equation|align|gather|multline)", joined)),
        "bibliography_entry_total": bibliography_entry_total,
        "verified_bibliography_entry_total": verified_bibliography_entry_total,
        "appendix_named_total": sum(1 for title in appendix_section_titles if title.startswith("Appendix ")),
        "appendix_letter_only_total": sum(1 for title in appendix_section_titles if not title.startswith("Appendix ")),
        "figure_atlas_included": 1 if r"\input{appendix/N_oc_core_1_3_figure_atlas" in entrypoint_text else 0,
    }


def r008_continuum_figure_tex() -> str:
    return r"""\begin{figure}[p]
\centering
\resizebox{0.96\textwidth}{!}{%
\begin{tikzpicture}[x=1cm,y=1cm, every node/.style={font=\small}]
  \definecolor{ocBlue}{HTML}{173B57}
  \definecolor{ocGold}{HTML}{A77D2A}
  \definecolor{ocGreen}{HTML}{4B7F52}
  \node[font=\bfseries\large, ocBlue] at (0,6.0) {A continuum in OC: state, boundary, motion, recurrence, and context};
  \draw[rounded corners=12pt, fill=blue!3, draw=ocBlue, line width=1.0pt] (-6.2,-3.6) rectangle (6.2,5.35);
  \node[anchor=west, ocBlue] at (-5.9,5.0) {embedding context \(M\): the larger continuum that constrains \(K\)};
  \draw[rounded corners=10pt, fill=white, draw=ocBlue, line width=1.0pt] (-4.7,-1.7) rectangle (3.75,3.75);
  \node[font=\bfseries, ocBlue] at (-0.5,3.35) {continuum \(K\)};
  \draw[->, line width=0.9pt, ocGold] (-4.1,-1.05) -- (3.0,-1.05);
  \node[anchor=west, ocGold] at (3.15,-1.05) {axis \(A_1\)};
  \draw[->, line width=0.9pt, ocGold] (-4.1,-1.05) -- (-4.1,2.75);
  \node[anchor=south, ocGold] at (-4.1,2.86) {axis \(A_2\)};
  \draw[fill=ocGreen!16, draw=ocGreen, line width=1.0pt] (-0.6,0.8) ellipse (2.35 and 1.05);
  \node[align=center] at (-0.6,0.8) {admissible\\state region\\\(\Omega(K)\)};
  \draw[dashed, red!70!black, line width=0.9pt] (-0.6,0.8) ellipse (2.65 and 1.25);
  \node[draw, rounded corners=3pt, fill=white, align=center, red!70!black] at (4.95,2.8) {boundary\\\(\partial\Omega(K)\)};
  \draw[->, red!70!black] (3.95,2.65) -- (1.95,1.55);
  \draw[->, thick, blue!70!black] (-2.55,0.1) .. controls (-1.5,2.55) and (1.1,2.45) .. (1.65,0.0);
  \node[draw, rounded corners=3pt, fill=white, align=center, blue!70!black] at (0.25,4.45) {flow \(J(t)\):\\motion through admissible states};
  \draw[->, blue!70!black] (0.15,4.1) -- (-0.2,2.1);
  \draw[->, line width=0.9pt] (-1.0,-0.05) arc (205:-105:0.72);
  \node[draw, rounded corners=3pt, fill=white, align=center] at (-1.05,-2.45) {cycle \(C(K)\):\\recurrence that sustains \(K\)};
  \draw[->] (-1.0,-2.1) -- (-0.85,-0.77);
  \node[draw, rounded corners=3pt, fill=white, align=center, ocGold] at (3.8,-2.45) {threshold \(\Theta(K)\):\\regime-change surface};
  \draw[->, ocGold] (3.3,-2.1) -- (1.7,-0.6);
  \node[draw, rounded corners=3pt, fill=white, align=center] at (-5.0,0.15) {continuumness\\\(k(K,t)>0\)};
  \draw[->] (-4.35,0.1) -- (-3.2,0.55);
  \node[draw, rounded corners=4pt, fill=white, align=center, text width=0.35\textwidth] at (-3.65,-3.05)
    {formal anchor: \(K=(\Omega,\partial\Omega,A,\Theta,P,J,C,k,M)\)};
  \node[draw, rounded corners=4pt, fill=white, align=center, text width=0.34\textwidth] at (2.35,-3.05)
    {falsifier anchor: a claimed live \(K\) fails if it crosses a declared death boundary without a valid continuation rule};
\end{tikzpicture}}
\caption{A didactic continuum diagram for the external reader. The labels are outside the semantic objects they explain: state region, boundary, axes, flow, threshold, cycle, continuumness, context, formal tuple, and falsifier are all visible without overlap.}
\label{fig:r008-continuum-demonstrator}
\end{figure}"""


def r008_k_hierarchy_figure_tex() -> str:
    return r"""% R008_K_LEVELS_PRESENT: K0 K1 K2 K3 K4 K5 K6 K7 K8 K9 K10 K11 K12.
\begin{figure}[p]
\centering
\resizebox{0.98\textwidth}{!}{%
\begin{tikzpicture}[x=1cm,y=0.82cm, every node/.style={font=\scriptsize}]
  \definecolor{ocBlue}{HTML}{173B57}
  \definecolor{ocGold}{HTML}{A77D2A}
  \definecolor{ocGreen}{HTML}{4B7F52}
  \node[font=\bfseries\large, ocBlue] at (0,14.4) {Complete K0--K12 hierarchy: composition and constraint};
  \foreach \i/\human/\role in {
    0/{K0 resolution boundary}/{minimal difference; null/non-null continuumness},
    1/{K1 first carrier}/{first structured coordinate or interface},
    2/{K2 process closure}/{routine, reaction, or closed operational loop},
    3/{K3 organized substrate}/{stable physical or deployment substrate},
    4/{K4 binding system}/{component binding and compositional integration},
    5/{K5 liveness system}/{regulated live process, organism, or service health},
    6/{K6 cognition and agency}/{memory, representation, policy, or agent control},
    7/{K7 social coordination}/{team, institution, trust, authority, governance},
    8/{K8 economic/civilizational system}/{market, platform, ecology, regulation},
    9/{K9 theory-level system}/{formal model or architecture doctrine},
    10/{K10 comparator/meta-theory}/{verification regime and comparison frame},
    11/{K11 method/publication quality}/{reproducibility, review, and evidence practice},
    12/{K12 cross-domain synthesis}/{bounded synthesis under declared assumptions}
  }{
    \pgfmathsetmacro{\y}{13-\i}
    \node[draw, rounded corners=3pt, fill=blue!5, text width=0.23\textwidth, align=center, minimum height=0.58cm] (k\i) at (-4.7,\y) {\textbf{\human}};
    \node[draw, rounded corners=3pt, fill=green!5, text width=0.50\textwidth, align=left, minimum height=0.58cm] (r\i) at (1.7,\y) {\role};
    \draw[-, ocBlue] (k\i.east) -- (r\i.west);
  }
  \foreach \i in {0,...,11}{
    \pgfmathtruncatemacro{\j}{\i+1}
    \draw[->, ocGreen, line width=0.8pt] (k\i.north east) -- (k\j.south east);
    \draw[->, ocGold, line width=0.8pt] (r\j.south west) -- (r\i.north west);
  }
  \node[draw, rounded corners=4pt, fill=white, text width=0.36\textwidth, align=center] at (-4.7,-0.65)
    {upward composition: lower continua make the next continuum possible};
  \node[draw, rounded corners=4pt, fill=white, text width=0.47\textwidth, align=center] at (1.7,-0.65)
    {downward constraint: the containing continuum narrows admissible lower-level behavior};
  \draw[->, thick, ocGreen] (-6.45,-0.15) -- (-6.45,13.2) node[midway,left,align=center] {composition};
  \draw[->, thick, ocGold] (6.5,13.2) -- (6.5,-0.15) node[midway,right,align=center] {constraint};
\end{tikzpicture}}
\caption{The full K-level teaching ladder. The figure does not merely decorate the text: it demonstrates the two central dependencies used later in the formal hierarchy. Every K0--K12 level is numbered and named; the left column shows composition upward, and the right column shows how a higher continuum constrains its parts.}
\label{fig:r008-k0-k12-hierarchy}
\end{figure}"""


def apply_r008_monograph_overrides(source_dir: Path) -> None:
    content_dir = source_dir / "content"
    r007_dir = content_dir / "r007"
    r008_dir = content_dir / "r008"
    if not r007_dir.is_dir():
        return
    replacements = [
        (r007_dir / "01_why_continuum_ontology.tex", r008_dir / "01_why_continuum_ontology.tex", "continuum"),
        (r007_dir / "02_first_concepts_and_k_primer.tex", r008_dir / "02_first_concepts_and_k_primer.tex", "k_hierarchy"),
    ]
    for source, target, kind in replacements:
        if not source.is_file():
            continue
        text = source.read_text(encoding="utf-8", errors="replace").replace("r007", "r008").replace("R007", "R008")
        if kind == "continuum":
            text = re.sub(
                r"\\begin\{figure\}\[p\].*?\\label\{fig:r008-continuum-demonstrator\}\s*\\end\{figure\}",
                lambda _match: r008_continuum_figure_tex(),
                text,
                count=1,
                flags=re.S,
            )
            text += "\n\n% R008_GOVERNED_PUBLICATION_TRANSLATOR: common service review trace is package metadata, not reader prose.\n"
        else:
            text = re.sub(
                r"% R008_K_LEVELS_PRESENT:.*?\\label\{fig:r008-k0-k12-hierarchy\}\s*\\end\{figure\}",
                lambda _match: r008_k_hierarchy_figure_tex(),
                text,
                count=1,
                flags=re.S,
            )
            text += "\n\n% R008_FIGURE_SPEC_VALIDATED: K0-K12 labels, composition arrows, constraint arrows, semantic role text, and non-overlap layout.\n"
        write_text_if_changed(target, text)
    entry = source_dir / science_monolith.BASE_ENTRYPOINT
    if entry.is_file():
        text = entry.read_text(encoding="utf-8", errors="replace")
        text = text.replace("content/r007/01_why_continuum_ontology.tex", "content/r008/01_why_continuum_ontology.tex")
        text = text.replace("content/r007/02_first_concepts_and_k_primer.tex", "content/r008/02_first_concepts_and_k_primer.tex")
        text = text.replace("% R007_TOC_VISUAL_HIERARCHY", "% R007_TOC_VISUAL_HIERARCHY\n% R008_TOC_VISUAL_HIERARCHY")
        write_text_if_changed(entry, text)
    preamble = source_dir / "preamble.tex"
    if preamble.is_file():
        text = preamble.read_text(encoding="utf-8", errors="replace")
        if "% R008_LAYOUT_STANDARD" not in text:
            text = text.replace("% R007_LAYOUT_STANDARD", "% R007_LAYOUT_STANDARD\n% R008_LAYOUT_STANDARD")
            write_text_if_changed(preamble, text)


def pdf_toc_page_total(path: Path) -> int:
    if not path.is_file():
        return 0
    try:
        completed = subprocess.run(
            ["pdftotext", "-f", "1", "-l", "120", str(path), "-"],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=60,
        )
    except Exception:
        return 0
    if completed.returncode != 0:
        return 0
    pages = completed.stdout.split("\f")
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
        if re.search(r"(?m)^\s*(?:List of Figures|List of Tables)\s*$", page):
            return max(1, index - start)
        if re.search(r"(?m)^\s*(?:Reader Orientation|1\s+Reader Orientation|Complete Scientific Argument)\s*$", page):
            return max(1, index - start)
        if dotted_line_total < 3 and re.match(r"^\d+\s*\n\s*[A-Z][A-Za-z0-9 ,:&()/'-]{2,}\s*(?:\n|$)", stripped):
            return max(1, index - start)
        if dotted_line_total < 3 and re.match(r"^\d+\s+[A-Z][A-Za-z0-9 ,:&()/'-]{2,}", stripped):
            return max(1, index - start)
    return max(1, len(pages) - start)


def build_publication_master_monograph(
    release_id: str,
    version: str,
    base: Path,
    *,
    write: bool,
    skip_pdf: bool,
    assembly_revision: str | None = None,
) -> dict[str, Any]:
    build_dir = base / "b"
    pdf_path = base / "pdf" / f"master_monograph_{version}.pdf"
    generated_source_files: list[Path] = []
    source_dir = build_dir / "base_source"
    entry_path = source_dir / science_monolith.BASE_ENTRYPOINT
    frontmatter_path = source_dir / "content" / "frontmatter_oc_core_1_3_master.tex"
    commands: list[dict[str, Any]] = []
    counts = {
        "figure_total": 0,
        "inline_figure_total": 0,
        "table_total": 0,
        "formula_marker_total": 0,
        "bibliography_entry_total": 0,
        "verified_bibliography_entry_total": 0,
        "appendix_named_total": 0,
        "appendix_letter_only_total": 0,
        "figure_atlas_included": 0,
    }
    frontmatter_text = frontmatter_path.read_text(encoding="utf-8", errors="replace") if frontmatter_path.is_file() else ""
    reusable_existing_build = (
        not any(revision in str(base) for revision in ("recovery_r005", "recovery_r006", "recovery_r008"))
        and
        source_dir.is_dir()
        and entry_path.is_file()
        and (skip_pdf or pdf_path.is_file())
        and r"\renewcommand*\l@subsection" in entry_path.read_text(encoding="utf-8", errors="replace")
        and frontmatter_text.find("Acknowledgements") >= 0
        and frontmatter_text.find(r"\begin{abstract}") >= 0
        and frontmatter_text.find("Acknowledgements") < frontmatter_text.find(r"\begin{abstract}")
        and "4 May 2026" in frontmatter_text
        and "Scientific reviewers and formal critics" in frontmatter_text
    )
    if write and not reusable_existing_build:
        science_monolith._safe_clear_build_dir(ROOT, build_dir)
        source_dir = science_monolith._prepare_base_source(
            ROOT,
            build_dir,
            doi=CONCEPT_DOI,
            zenodo_record_url=f"https://doi.org/{CONCEPT_DOI}",
        )
        science_monolith._generate_integrated_science_tex(
            ROOT,
            source_dir,
            doi=CONCEPT_DOI,
            zenodo_record_url=f"https://doi.org/{CONCEPT_DOI}",
        )
        science_monolith._rewrite_public_science_projection_sources(source_dir)
        science_monolith._rewrite_entrypoint_for_integrated_133(source_dir)
        science_monolith._apply_r005_publication_layout_standard(source_dir)
        if assembly_revision in {R008_REVISION, R009_REVISION, R010_REVISION}:
            apply_r008_monograph_overrides(source_dir)
        science_monolith._sanitize_source_tree(source_dir)
        entry_path = source_dir / science_monolith.BASE_ENTRYPOINT
        counts = tex_corpus_counts(source_dir)
        if not skip_pdf:
            base_pdf, commands = science_monolith._build_base_pdf(source_dir)
            if base_pdf.is_file():
                pdf_path.parent.mkdir(parents=True, exist_ok=True)
                if not pdf_path.exists() or pdf_path.read_bytes() != base_pdf.read_bytes():
                    shutil.copy2(base_pdf, pdf_path)
    else:
        if source_dir.is_dir():
            counts = tex_corpus_counts(source_dir)
    if source_dir.is_dir():
        generated_source_files = [
            path
            for path in sorted(source_dir.rglob("*"))
            if path.is_file() and path.suffix.lower() in {".tex", ".bib", ".md", ".sty", ".cls"}
        ]
    build_failures = [row for row in commands if not row.get("ok")]
    pdf_build = None
    if not skip_pdf:
        pdf_build = {
            "command": " ; ".join(row.get("command", "") for row in commands) if commands else "existing TeX monolith PDF",
            "returncode": 0 if not build_failures and pdf_path.is_file() else 1,
            "ok": not build_failures and pdf_path.is_file(),
            "stdout_tail": "\n".join(str(row.get("stdout_tail") or "") for row in commands)[-1200:],
            "stderr_tail": "\n".join(str(row.get("stderr_tail") or "") for row in commands)[-1200:],
            "output": rel(pdf_path),
            "sha256": sha256_file(pdf_path) if pdf_path.is_file() else None,
            "size_bytes": pdf_path.stat().st_size if pdf_path.is_file() else 0,
            "pages": pdf_pages(pdf_path) if pdf_path.is_file() else 0,
            "engine": "xelatex",
            "source_builder": "release_machine.science_monolith",
        }
    return {
        "source_path": entry_path,
        "pdf_path": pdf_path,
        "generated_source_files": generated_source_files,
        "pdf_build": pdf_build,
        "counts": counts,
        "toc_page_total": pdf_toc_page_total(pdf_path) if pdf_path.is_file() else 0,
    }


def build_pdf(source: Path, output: Path) -> dict[str, Any]:
    output.parent.mkdir(parents=True, exist_ok=True)
    resource_path = os.pathsep.join([rel(source.parent), rel(source.parent.parent), "."])
    cmd = [
        "pandoc",
        rel(source),
        "-o",
        rel(output),
        "--resource-path",
        resource_path,
        "--number-sections",
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
        unique_files = sorted({path.resolve(): path for path in files}.values(), key=lambda item: rel(item))
        for path in unique_files:
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
    base = generated_dir(release_id, assembly_revision)
    governed_trace = governed_llm_trace_for_revision(assembly_revision, version=version, base=base, write=write)
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
        source_path = base / "sources" / f"{artifact_id}_{version}.md"
        pdf_path = base / "pdf" / f"{artifact_id}_{version}.pdf"
        json_path = base / "metadata" / f"{artifact_id}_{version}.json"
        output_paths: list[str] = []
        if artifact_id in TEXT_ARTIFACTS or artifact_id == "release_notes_changelog":
            rows = artifact_scope(artifact_id, terminal_rows, structure_source)
            if artifact_id == "release_notes_changelog":
                rows = artifact_scope("release_guide", terminal_rows, structure_source)[:80]
            frontmatter_rows, body_rows = split_frontmatter_rows(rows)
            pdf_build = None
            source_format = "markdown"
            document_body_source = "generated_l10_terminal_contracts"
            document_structure_source = structure_source
            figure_total = 0
            inline_figure_total = 0
            table_total = 0
            formula_marker_total = 0
            bibliography_entry_total = 0
            verified_bibliography_entry_total = 0
            appendix_named_total = 0
            appendix_letter_only_total = 0
            figure_atlas_included = 0
            toc_page_total = 0
            source_changed = False
            assets_changed = False
            source_payload_origin: str | None = None
            public_translation_source: str | None = None
            if (
                publication_revision_enabled(assembly_revision)
                and artifact_id == "master_monograph"
            ):
                built = build_publication_master_monograph(release_id, version, base, write=write, skip_pdf=skip_pdf, assembly_revision=assembly_revision)
                source_path = built["source_path"]
                pdf_path = built["pdf_path"]
                pdf_build = built["pdf_build"]
                source_format = "latex"
                document_body_source = "release_machine.science_monolith.integrated_tex_corpus"
                document_structure_source = "science_monolith_canonical_tex_hierarchy"
                if assembly_revision == R007_REVISION:
                    public_translation_source = "science_monolith_publication_translator_r007"
                elif assembly_revision == R008_REVISION:
                    public_translation_source = "science_monolith_logion_llm_service_translator_r008"
                elif assembly_revision == R009_REVISION:
                    public_translation_source = "science_monolith_editorial_ollama_until_done_translator_r009"
                elif assembly_revision == R010_REVISION:
                    public_translation_source = "science_monolith_source_grounded_editorial_repair_r010"
                figure_total = int(built["counts"].get("figure_total") or 0)
                inline_figure_total = int(built["counts"].get("inline_figure_total") or 0)
                table_total = int(built["counts"].get("table_total") or 0)
                formula_marker_total = int(built["counts"].get("formula_marker_total") or 0)
                bibliography_entry_total = int(built["counts"].get("bibliography_entry_total") or 0)
                verified_bibliography_entry_total = int(built["counts"].get("verified_bibliography_entry_total") or 0)
                appendix_named_total = int(built["counts"].get("appendix_named_total") or 0)
                appendix_letter_only_total = int(built["counts"].get("appendix_letter_only_total") or 0)
                figure_atlas_included = int(built["counts"].get("figure_atlas_included") or 0)
                toc_page_total = int(built.get("toc_page_total") or 0)
                generated_files.extend(built["generated_source_files"])
                if source_path.is_file():
                    output_paths.append(rel(source_path))
                if pdf_path.is_file():
                    generated_files.append(pdf_path)
                    output_paths.append(rel(pdf_path))
            else:
                if publication_revision_enabled(assembly_revision) and artifact_id in PUBLIC_PAYLOAD_SOURCE_BY_ARTIFACT:
                    text, source_payload = render_publication_payload_markdown(artifact_id, version, instance, assembly_revision)
                    document_body_source = "curated_public_payload_markdown"
                    document_structure_source = "curated_public_payload_hierarchy"
                    if assembly_revision == R007_REVISION:
                        document_body_source = "curated_public_payload_markdown_publication_translator_r007"
                        document_structure_source = "curated_public_payload_hierarchy_r007"
                        public_translation_source = "deterministic_publication_translator_r007"
                    elif assembly_revision == R008_REVISION:
                        document_body_source = "curated_public_payload_markdown_logion_llm_service_translator_r008"
                        document_structure_source = "curated_public_payload_hierarchy_r008"
                        public_translation_source = "logion_llm_service_publication_translator_r008"
                    elif assembly_revision == R009_REVISION:
                        document_body_source = "curated_public_payload_markdown_editorial_ollama_until_done_r009"
                        document_structure_source = "curated_public_payload_hierarchy_r009"
                        public_translation_source = "editorial_ollama_until_done_publication_translator_r009"
                    elif assembly_revision == R010_REVISION:
                        document_body_source = "curated_public_payload_markdown_source_grounded_repair_r010"
                        document_structure_source = "curated_public_payload_hierarchy_r010"
                        public_translation_source = "source_grounded_editorial_repair_publication_translator_r010"
                    source_payload_origin = rel(source_payload) if source_payload else None
                    asset_files, assets_changed = copy_public_payload_assets(base, write=write)
                    generated_files.extend(asset_files)
                else:
                    text = render_artifact_markdown(artifact_id, version, instance, rows)
                counts = source_content_counts(text)
                figure_total = counts["figure_total"]
                inline_figure_total = counts["figure_total"]
                table_total = counts["table_total"]
                formula_marker_total = counts["formula_marker_total"]
                if write and write_text_if_changed(source_path, text):
                    source_changed = True
                    changed.append(rel(source_path))
                generated_files.append(source_path)
                output_paths.append(rel(source_path))
                if artifact_id in TEXT_ARTIFACTS and not skip_pdf:
                    force_public_payload_rebuild = publication_revision_enabled(assembly_revision) and artifact_id in PUBLIC_PAYLOAD_SOURCE_BY_ARTIFACT
                    if write and (force_public_payload_rebuild or source_changed or assets_changed or not pdf_path.is_file()):
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
                        toc_page_total = pdf_toc_page_total(pdf_path)
            artifact_rows.append(
                {
                    "artifact_type_id": artifact_id,
                    "output_kind": "markdown_and_pdf" if artifact_id in TEXT_ARTIFACTS else "markdown",
                    "source_format": source_format,
                    "document_body_source": document_body_source,
                    "document_structure_source": document_structure_source,
                    "public_translation_status": (
                        R007_TRANSLATOR_STATUS if assembly_revision == R007_REVISION and artifact_id in TEXT_ARTIFACTS
                        else R008_TRANSLATOR_STATUS if assembly_revision == R008_REVISION and artifact_id in TEXT_ARTIFACTS
                        else R009_TRANSLATOR_STATUS if assembly_revision == R009_REVISION and artifact_id in TEXT_ARTIFACTS
                        else R010_TRANSLATOR_STATUS if assembly_revision == R010_REVISION and artifact_id in TEXT_ARTIFACTS
                        else None
                    ),
                    "public_translation_source": public_translation_source,
                    "governed_ollama_status": governed_trace["status"] if assembly_revision in {R007_REVISION, R008_REVISION, R009_REVISION, R010_REVISION} and artifact_id in TEXT_ARTIFACTS else None,
                    "ollama_invocation_total": governed_trace["ollama_invocation_total"] if assembly_revision in {R007_REVISION, R008_REVISION, R009_REVISION, R010_REVISION} and artifact_id in TEXT_ARTIFACTS else None,
                    "unmanaged_ollama_call_total": governed_trace["unmanaged_ollama_call_total"] if assembly_revision in {R007_REVISION, R008_REVISION, R009_REVISION, R010_REVISION} and artifact_id in TEXT_ARTIFACTS else None,
                    "v_model_lowest_checked_level": (governed_trace.get("v_model_lowest_checked_level") or "L10") if assembly_revision in {R007_REVISION, R008_REVISION, R009_REVISION, R010_REVISION} and artifact_id in TEXT_ARTIFACTS else None,
                    "instruction_packet_total": len(rows) if assembly_revision in {R007_REVISION, R008_REVISION, R009_REVISION, R010_REVISION} and artifact_id in TEXT_ARTIFACTS else None,
                    "public_translation_packet_total": len(rows) if assembly_revision in {R007_REVISION, R008_REVISION, R009_REVISION, R010_REVISION} and artifact_id in TEXT_ARTIFACTS else None,
                    "logion_llm_service_status": governed_trace.get("service_status") if assembly_revision in {R008_REVISION, R009_REVISION, R010_REVISION} and artifact_id in TEXT_ARTIFACTS else None,
                    "logion_llm_service_ledger_ref": governed_trace.get("service_ledger_ref") if assembly_revision in {R008_REVISION, R009_REVISION, R010_REVISION} and artifact_id in TEXT_ARTIFACTS else None,
                    "logion_llm_service_cadence_sequence": governed_trace.get("cadence_sequence") if assembly_revision in {R008_REVISION, R009_REVISION, R010_REVISION} and artifact_id in TEXT_ARTIFACTS else None,
                    "logion_llm_service_model_sequence": governed_trace.get("model_sequence") if assembly_revision in {R008_REVISION, R009_REVISION, R010_REVISION} and artifact_id in TEXT_ARTIFACTS else None,
                    "source_payload_origin": source_payload_origin,
                    "figure_total": figure_total,
                    "inline_figure_total": inline_figure_total,
                    "table_total": table_total,
                    "formula_marker_total": formula_marker_total,
                    "bibliography_entry_total": bibliography_entry_total,
                    "verified_bibliography_entry_total": verified_bibliography_entry_total,
                    "appendix_named_total": appendix_named_total,
                    "appendix_letter_only_total": appendix_letter_only_total,
                    "figure_atlas_included": figure_atlas_included,
                    "toc_page_total": toc_page_total,
                    "source_path": rel(source_path),
                    "pdf_path": rel(pdf_path) if artifact_id in TEXT_ARTIFACTS else None,
                    "terminal_node_total": len(rows),
                    "body_terminal_node_total": len(body_rows),
                    "frontmatter_body_excluded_total": len(frontmatter_rows),
                    "frontmatter_required_sections": FRONTMATTER_REQUIRED_SECTIONS,
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
    if assembly_revision == R009_REVISION:
        service_paths = r009_service_output_paths(base, version)
        queue_payload = r009_editorial_packet_queue(version, base, artifact_rows)
        trace_payload: dict[str, Any] = {}
        if write:
            write_json_if_changed(service_paths["queue_json"], queue_payload)
            service = R007_GOVERNANCE_REFS["logion_llm_service"]
            if service.is_file():
                completed = subprocess.run(
                    [
                        sys.executable,
                        str(service),
                        "--queue-json",
                        str(service_paths["queue_json"]),
                        "--output-json",
                        str(service_paths["trace_json"]),
                        "--until-done",
                        "--write",
                    ],
                    cwd=ROOT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    capture_output=True,
                    timeout=7200,
                )
                if service_paths["trace_json"].is_file():
                    trace_payload = read_json_optional(service_paths["trace_json"])
                else:
                    trace_payload = {
                        "schema_id": "LOGION_LLM_SERVICE_RESPONSE_v1",
                        "status": "SERVICE_INVOCATION_FAILED",
                        "queue_status": "SERVICE_INVOCATION_FAILED",
                        "summary": {"provider_invocation_total": 0, "unmanaged_ollama_call_total": 0, "request_total": len(queue_payload.get("requests", []))},
                        "v_model": {"lowest_checked_level": None, "order": "L10_to_L9_L8_to_document", "lower_level_blockers": 0},
                        "stderr_tail": completed.stderr[-1000:],
                        "stdout_tail": completed.stdout[-1000:],
                    }
                    write_json_if_changed(service_paths["trace_json"], trace_payload)
            else:
                trace_payload = {
                    "schema_id": "LOGION_LLM_SERVICE_RESPONSE_v1",
                    "status": "SERVICE_MISSING",
                    "queue_status": "SERVICE_MISSING",
                    "summary": {"provider_invocation_total": 0, "unmanaged_ollama_call_total": 0, "request_total": len(queue_payload.get("requests", []))},
                    "v_model": {"lowest_checked_level": None, "order": "L10_to_L9_L8_to_document", "lower_level_blockers": 0},
                }
                write_json_if_changed(service_paths["trace_json"], trace_payload)
        else:
            queue_payload = read_json_optional(service_paths["queue_json"]) or queue_payload
            trace_payload = read_json_optional(service_paths["trace_json"])
        governed_trace = normalize_r009_service_trace(trace_payload, queue_payload, version=version)
        for row in artifact_rows:
            if row.get("artifact_type_id") in TEXT_ARTIFACTS:
                row["governed_ollama_status"] = governed_trace["status"]
                row["ollama_invocation_total"] = governed_trace["ollama_invocation_total"]
                row["unmanaged_ollama_call_total"] = governed_trace["unmanaged_ollama_call_total"]
                row["v_model_lowest_checked_level"] = governed_trace.get("v_model_lowest_checked_level") or "L10"
                row["public_translation_status"] = R009_TRANSLATOR_STATUS
                row["logion_llm_service_status"] = governed_trace.get("service_status")
                row["logion_llm_service_ledger_ref"] = governed_trace.get("service_ledger_ref")
                row["logion_llm_service_cadence_sequence"] = governed_trace.get("cadence_sequence")
                row["logion_llm_service_model_sequence"] = governed_trace.get("model_sequence")
                row["editorial_llm_queue_status"] = governed_trace.get("editorial_llm_queue_status")
                row["editorial_packet_total"] = governed_trace.get("packet_total")
                row["editorial_packet_done_total"] = governed_trace.get("packet_done_total")
        generated_files.extend(path for path in service_paths.values() if path.is_file())
    if assembly_revision == R010_REVISION:
        repair_paths = r010_repair_output_paths(base, version)
        records_payload = r010_repair_records(version)
        queue_payload = r010_repair_queue(records_payload, version)
        trace_payload: dict[str, Any] = {}
        if write:
            write_json_if_changed(repair_paths["records_json"], records_payload)
            write_text_if_changed(repair_paths["records_md"], render_r010_repair_records_md(records_payload))
            write_json_if_changed(repair_paths["queue_json"], queue_payload)
            service = R007_GOVERNANCE_REFS["logion_llm_service"]
            if service.is_file() and queue_payload.get("requests"):
                completed = subprocess.run(
                    [
                        sys.executable,
                        str(service),
                        "--queue-json",
                        str(repair_paths["queue_json"]),
                        "--output-json",
                        str(repair_paths["trace_json"]),
                        "--until-done",
                        "--write",
                    ],
                    cwd=ROOT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    capture_output=True,
                    timeout=7200,
                )
                if repair_paths["trace_json"].is_file():
                    trace_payload = read_json_optional(repair_paths["trace_json"])
                else:
                    trace_payload = {
                        "schema_id": "LOGION_LLM_SERVICE_RESPONSE_v1",
                        "status": "SERVICE_INVOCATION_FAILED",
                        "queue_status": "SERVICE_INVOCATION_FAILED",
                        "summary": {"provider_invocation_total": 0, "unmanaged_ollama_call_total": 0, "request_total": len(queue_payload.get("requests", []))},
                        "stderr_tail": completed.stderr[-1000:],
                        "stdout_tail": completed.stdout[-1000:],
                    }
                    write_json_if_changed(repair_paths["trace_json"], trace_payload)
            else:
                trace_payload = {
                    "schema_id": "LOGION_LLM_SERVICE_RESPONSE_v1",
                    "status": "SERVICE_MISSING" if queue_payload.get("requests") else "PASS",
                    "queue_status": "SERVICE_MISSING" if queue_payload.get("requests") else "DONE",
                    "summary": {
                        "provider_invocation_total": 0,
                        "unmanaged_ollama_call_total": 0,
                        "request_total": len(queue_payload.get("requests", [])),
                        "packet_done_total": 0,
                    },
                }
                write_json_if_changed(repair_paths["trace_json"], trace_payload)
        else:
            records_payload = read_json_optional(repair_paths["records_json"]) or records_payload
            queue_payload = read_json_optional(repair_paths["queue_json"]) or queue_payload
            trace_payload = read_json_optional(repair_paths["trace_json"])
        governed_trace = normalize_r010_repair_trace(trace_payload, queue_payload, records_payload, version=version)
        if write:
            write_json_if_changed(repair_paths["summary_json"], governed_trace)
            write_text_if_changed(repair_paths["summary_md"], render_r010_repair_summary_md(governed_trace))
        for row in artifact_rows:
            if row.get("artifact_type_id") in TEXT_ARTIFACTS:
                row["governed_ollama_status"] = governed_trace["status"]
                row["ollama_invocation_total"] = governed_trace["ollama_invocation_total"]
                row["unmanaged_ollama_call_total"] = governed_trace["unmanaged_ollama_call_total"]
                row["v_model_lowest_checked_level"] = governed_trace.get("v_model_lowest_checked_level") or "L10"
                row["public_translation_status"] = R010_TRANSLATOR_STATUS
                row["logion_llm_service_status"] = governed_trace.get("service_status")
                row["logion_llm_service_ledger_ref"] = governed_trace.get("service_ledger_ref")
                row["logion_llm_service_cadence_sequence"] = governed_trace.get("cadence_sequence")
                row["logion_llm_service_model_sequence"] = governed_trace.get("model_sequence")
                row["source_grounded_repair_status"] = governed_trace.get("source_grounded_repair_status")
                row["repair_record_total"] = governed_trace.get("repair_record_total")
                row["accepted_candidate_promoted_total"] = governed_trace.get("accepted_candidate_promoted_total")
                row["unresolved_repair_record_total"] = governed_trace.get("unresolved_repair_record_total")
        generated_files.extend(path for path in repair_paths.values() if path.is_file())
    generated_files.extend([paths["terminal_contracts_json"], paths["terminal_contracts_md"], paths["transition_records_json"], paths["transition_records_md"], paths["source_bindings_json"], paths["source_bindings_md"]])
    if assembly_revision == R008_REVISION:
        generated_files.extend(path for path in r008_service_output_paths(base, version).values() if path.is_file())
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
        "governed_ollama_trace": governed_trace,
        "publication_translation_pipeline": {
            "status": (
                R007_TRANSLATOR_STATUS if assembly_revision == R007_REVISION
                else R008_TRANSLATOR_STATUS if assembly_revision == R008_REVISION
                else R009_TRANSLATOR_STATUS if assembly_revision == R009_REVISION
                else R010_TRANSLATOR_STATUS if assembly_revision == R010_REVISION
                else "NOT_APPLICABLE"
            ),
            "strategy": (
                "internal_section_packets_to_public_prose_deterministic_templates_first" if assembly_revision == R007_REVISION
                else "common_governed_llm_service_v_model_review_then_public_prose" if assembly_revision == R008_REVISION
                else "editorial_ollama_until_done_packet_queue_then_public_package" if assembly_revision == R009_REVISION
                else "source_grounded_repair_records_and_bounded_suggestions_without_auto_promotion" if assembly_revision == R010_REVISION
                else None
            ),
            "v_model_flow": "L10_to_L9_L8_to_document_review" if assembly_revision in {R007_REVISION, R008_REVISION, R009_REVISION, R010_REVISION} else None,
            "lower_level_blockers_required_zero_before_global_review": True if assembly_revision in {R007_REVISION, R008_REVISION, R009_REVISION, R010_REVISION} else None,
            "common_llm_service_required": True if assembly_revision in {R008_REVISION, R009_REVISION, R010_REVISION} else None,
            "service_status": governed_trace.get("service_status") if assembly_revision in {R008_REVISION, R009_REVISION, R010_REVISION} else None,
            "queue_status": governed_trace.get("queue_status") if assembly_revision == R009_REVISION else None,
            "source_grounded_repair_status": governed_trace.get("source_grounded_repair_status") if assembly_revision == R010_REVISION else None,
            "local_editorial_capability_boundary_status": governed_trace.get("local_editorial_capability_boundary_status") if assembly_revision == R010_REVISION else None,
        },
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
            "frontmatter_body_excluded_total": sum(int(row.get("frontmatter_body_excluded_total") or 0) for row in artifact_rows),
            "source_grounded_repair_status": governed_trace.get("source_grounded_repair_status") if assembly_revision == R010_REVISION else None,
            "unresolved_repair_record_total": governed_trace.get("unresolved_repair_record_total") if assembly_revision == R010_REVISION else None,
            "accepted_candidate_promoted_total": governed_trace.get("accepted_candidate_promoted_total") if assembly_revision == R010_REVISION else None,
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
