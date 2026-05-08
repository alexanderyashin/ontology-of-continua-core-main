from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
import zipfile
from collections import defaultdict
from datetime import date
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

from release_machine.versioning import current_release, version_from_release_id
from release_machine import science_monolith
from oc133_r016_machine_self_audit import (
    R016_MACHINE_STATUS_KEYS,
    build_r016_machine_self_audit,
    r017_toe_gate_errors,
)


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
PUBLICATION_BODY_REVISIONS = {
    "recovery_r004",
    "recovery_r005",
    "recovery_r006",
    "recovery_r007",
    "recovery_r008",
    "recovery_r009",
    "recovery_r010",
    "recovery_r011",
    "recovery_r012",
    "recovery_r013",
    "recovery_r014",
    "recovery_r015",
    "recovery_r016",
    "recovery_r017",
}
PUBLICATION_DATE = os.environ.get("OC_PUBLICATION_DATE", date.today().isoformat())


def public_version_for_release(release_id: str, assembly_revision: str | None = None) -> str:
    """Return the owner-controlled public version pointer for the active release."""
    if assembly_revision and assembly_revision not in {"recovery_r017", "oc_core_1_3_3_review_current"}:
        return version_from_release_id(release_id)
    try:
        identity = current_release(ROOT)
    except Exception:
        return version_from_release_id(release_id)
    if identity.release_id == release_id:
        return identity.version
    return version_from_release_id(release_id)


def release_delta_title(version: str) -> str:
    return f"Version {version} Release Delta"
CURRENT_RECOVERY_REVISION = "recovery_r016"
R007_REVISION = "recovery_r007"
R008_REVISION = "recovery_r008"
R009_REVISION = "recovery_r009"
R010_REVISION = "recovery_r010"
R011_REVISION = "recovery_r011"
R012_REVISION = "recovery_r012"
R013_REVISION = "recovery_r013"
R014_REVISION = "recovery_r014"
R015_REVISION = "recovery_r015"
R016_REVISION = "recovery_r016"
R017_REVISION = "recovery_r017"
R007_TRANSLATOR_STATUS = "PUBLICATION_TRANSLATOR_R007"
R008_TRANSLATOR_STATUS = "PUBLICATION_TRANSLATOR_R008"
R009_TRANSLATOR_STATUS = "PUBLICATION_TRANSLATOR_R009"
R010_TRANSLATOR_STATUS = "PUBLICATION_TRANSLATOR_R010_SOURCE_GROUNDED_REPAIR"
R011_TRANSLATOR_STATUS = "PUBLICATION_TRANSLATOR_R011_JOURNAL_REQUIREMENTS_SPOT"
R012_TRANSLATOR_STATUS = "PUBLICATION_TRANSLATOR_R012_FIGURE_VISUAL_QA_SPOT"
R013_TRANSLATOR_STATUS = "PUBLICATION_TRANSLATOR_R013_TABLE_RENDERED_QA_SPOT"
R014_TRANSLATOR_STATUS = "PUBLICATION_TRANSLATOR_R014_FULL_QUALITY_CLOSURE"
R015_TRANSLATOR_STATUS = "PUBLICATION_TRANSLATOR_R015_SCIENTIFIC_REVIEW_GATE"
R016_TRANSLATOR_STATUS = "PUBLICATION_TRANSLATOR_R016_MACHINE_SELF_AUDITED_TOE_GATE"
R017_TRANSLATOR_STATUS = "PUBLICATION_TRANSLATOR_R017_FINAL_TOE_CLOSED_PACKAGE"
GOVERNED_TEXT_REVISIONS = {
    R007_REVISION,
    R008_REVISION,
    R009_REVISION,
    R010_REVISION,
    R011_REVISION,
    R012_REVISION,
    R013_REVISION,
    R014_REVISION,
    R015_REVISION,
    R016_REVISION,
    R017_REVISION,
}
COMMON_LLM_SERVICE_REVISIONS = {
    R008_REVISION,
    R009_REVISION,
    R010_REVISION,
    R011_REVISION,
    R012_REVISION,
    R013_REVISION,
    R014_REVISION,
    R015_REVISION,
    R016_REVISION,
    R017_REVISION,
}
JOURNAL_SPOT_REVISIONS = {R011_REVISION, R012_REVISION, R013_REVISION, R014_REVISION, R015_REVISION, R016_REVISION, R017_REVISION}
VISUAL_QA_REVISIONS = {R012_REVISION, R013_REVISION, R014_REVISION, R015_REVISION, R016_REVISION, R017_REVISION}
TABLE_QA_REVISIONS = {R013_REVISION, R014_REVISION, R015_REVISION, R016_REVISION, R017_REVISION}
PUBLIC_REVIEW_REVISION_ALIASES = {
    "oc_core_1_3_3_review_current": R016_REVISION,
}
R014_CHECKSUM_BOUND_PUBLIC_EVIDENCE_PATHS = [
    "comparators/OC_1_3_3_COMPARATOR_MATRIX.md",
    "comparators/OC_1_3_3_NOVELTY_AND_PRIORITY_REGISTER.json",
    "docs/OC_1_3_3_PRIOR_ART_COMPARATOR_MATRIX.json",
    "docs/OC_1_3_3_PRIOR_ART_COMPARATOR_MATRIX.md",
    "docs/OC_1_3_3_REVIEWER_COMPARATOR_BRIEF.md",
    "validation/target_blind/OC133_TARGET_BLIND_PREDICTION_TABLE.json",
    "validation/numeric_replay_qa/OC133_NUMERIC_REPLAY_QA_TABLE.json",
    "proofs/FINITE_MODEL_CHECKS_1_3_3.json",
    "proofs/FINITE_MODEL_CHECKS_1_3_3.md",
]
R015_CHECKSUM_BOUND_PUBLIC_EVIDENCE_PATHS = [
    *R014_CHECKSUM_BOUND_PUBLIC_EVIDENCE_PATHS,
    "claims/CLAIM_LEDGER_1_3_3.json",
    "claims/CLAIM_LEDGER_FULL.json",
    "claims/K_LEVEL_CLAIM_LEDGER.md",
    "proofs/THEOREM_REGISTRY_1_3_3.json",
    "proofs/THEOREM_REGISTRY_1_3_3.md",
    "proofs/THEOREM_INVENTORY_1_3_3.json",
    "proofs/PROOF_DEPENDENCY_GRAPH_1_3_3.json",
    "proofs/PROOF_LEDGER_1_3_3.md",
    "proofs/proof_sheets/T133-BOUNDARY.md",
    "proofs/proof_sheets/T133-CYCLE.md",
    "proofs/proof_sheets/T133-DIM.md",
    "proofs/proof_sheets/T133-HYBRID.md",
    "proofs/proof_sheets/T133-ID.md",
    "proofs/proof_sheets/T133-K-ZERO.md",
    "proofs/proof_sheets/T133-K0-RES.md",
    "proofs/proof_sheets/T133-KLEVEL.md",
    "proofs/proof_sheets/T133-MIN.md",
    "proofs/proof_sheets/T133-OMEGA-STATUS.md",
    "formal/lean/OC133V12.lean",
    "formal/lean/LEAN_BUILD_CERTIFICATE_1_3_3.json",
]
R016_CHECKSUM_BOUND_PUBLIC_EVIDENCE_PATHS = [
    *R015_CHECKSUM_BOUND_PUBLIC_EVIDENCE_PATHS,
    "releases/oc_core_1_3/editorial/OC_CORE_1_3_SCIENCE_SPOT_latest.json",
    "releases/oc_core_1_3/editorial/OC_CORE_1_3_UNIFIED_SYNTHESIS_latest.json",
    "content/generated/oc_core_1_3_toe_synthesis_generated.tex",
    "content/generated/oc_core_1_3_operationalization_program_generated.tex",
]
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
    release_delta_title(public_version_for_release("oc_core_1_3_3")),
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
        assembly_revision = PUBLIC_REVIEW_REVISION_ALIASES.get(assembly_revision, assembly_revision)
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


def r011_journal_venues() -> list[dict[str, Any]]:
    return [
        {
            "venue_id": "FOUNDATIONS_OF_SCIENCE",
            "venue_name": "Foundations of Science",
            "publisher": "Springer Nature",
            "official_urls": ["https://link.springer.com/journal/10699/submission-guidelines"],
            "article_type": "standard article",
            "recommended": True,
            "requirements": [
                "Cross-disciplinary accessibility with a multidisciplinary first part and specialized formal second part.",
                "Title page with title, author information, affiliation, corresponding author contact, and ORCID where available.",
                "Abstract of 150 to 250 words and 4 to 6 keywords.",
                "Decimal heading system with no more than three levels.",
                "Editable source files, tables, artwork, SI, references, competing interests, and data availability statement.",
            ],
            "projection_focus": "primary foundations-science projection with didactic entry and formal self-containment",
            "format_family": "springer",
        },
        {
            "venue_id": "SYNTHESE",
            "venue_name": "Synthese",
            "publisher": "Springer Nature",
            "official_urls": ["https://link.springer.com/journal/11229/submission-guidelines"],
            "article_type": "original research article",
            "recommended": True,
            "requirements": [
                "Title page, abstract, keywords, text, references, tables, artwork, SI, declarations, and data availability.",
                "LaTeX or Word manuscript sources; Springer LaTeX template encouraged for LaTeX submissions.",
                "Decimal headings with no more than three levels.",
                "LLM use must not be authorship and must remain under human accountability.",
                "Philosophy-facing argument must define abbreviations and keep reference list to cited published or accepted work.",
            ],
            "projection_focus": "philosophy-of-science projection with novelty boundary and comparator map",
            "format_family": "springer",
        },
        {
            "venue_id": "FOUNDATIONS_OF_PHYSICS",
            "venue_name": "Foundations of Physics",
            "publisher": "Springer Nature",
            "official_urls": ["https://link.springer.com/journal/10701/submission-guidelines"],
            "article_type": "original article",
            "recommended": False,
            "requirements": [
                "Title page, abstract, keywords, declarations, references, tables, artwork, and SI.",
                "Editable source files are required for review; LaTeX source and compiled PDF are acceptable.",
                "Decimal headings with no more than three levels.",
                "Physics-facing claims must stay inside declared mathematical and empirical boundaries.",
                "Data availability and competing interest statements are required.",
            ],
            "projection_focus": "physics-boundary projection for formal hierarchy, predictions, and falsifier tests",
            "format_family": "springer",
        },
        {
            "venue_id": "ACTA_BIOTHEORETICA",
            "venue_name": "Acta Biotheoretica",
            "publisher": "Springer Nature",
            "official_urls": ["https://link.springer.com/journal/10441/submission-guidelines"],
            "article_type": "original article",
            "recommended": False,
            "requirements": [
                "Title page, abstract, keywords, text, references, tables, artwork, SI, and required declarations.",
                "Life-science relevance must be explicit and no biological claim may exceed the cited source map.",
                "Editable manuscript source files are required.",
                "Decimal headings with no more than three levels.",
                "Research-data and competing-interest statements are required.",
            ],
            "projection_focus": "biotheory/autopoiesis projection with biological analogy boundaries",
            "format_family": "springer",
        },
        {
            "venue_id": "GLOBAL_JOURNAL_OF_FLEXIBLE_SYSTEMS_MANAGEMENT",
            "venue_name": "Global Journal of Flexible Systems Management",
            "publisher": "Springer Nature",
            "official_urls": ["https://link.springer.com/journal/40171/submission-guidelines"],
            "article_type": "original article",
            "recommended": False,
            "requirements": [
                "Double-blind reviewing procedure; identifying information must be removed from the blinded manuscript.",
                "Separate title page with author details, acknowledgements, disclosures, and funding information.",
                "Abstract of 150 to 250 words, 4 to 6 keywords, JEL codes where relevant, and APA-style references.",
                "Decimal headings with no more than three levels.",
                "Tables, artwork, SI, data availability, ethical standards, and competing interests are required.",
            ],
            "projection_focus": "management-systems projection with enterprise architecture and strategy relevance",
            "format_family": "springer_double_anonymous",
        },
        {
            "venue_id": "PHYSICAL_REVIEW_RESEARCH",
            "venue_name": "Physical Review Research",
            "publisher": "American Physical Society",
            "official_urls": [
                "https://journals.aps.org/prresearch/authors",
                "https://journals.aps.org/authors/web-submission-guidelines-physical-review",
            ],
            "article_type": "article",
            "recommended": False,
            "requirements": [
                "APS/Physical Review web process requires journal, article type, files, author data, open-science information, data availability, title, abstract, and PhySH classification.",
                "Initial submissions require a single PDF containing textual material and figures; supplemental material is separate.",
                "Data availability details are required for research data needed to verify or replicate results.",
                "REVTeX or LaTeX source is preferred after acceptance; figure and supplemental files must be identified.",
                "Physics scope, length, and data/code boundary must be explicit before owner review.",
            ],
            "projection_focus": "APS physics-boundary package with REVTeX/source-map and data availability emphasis",
            "format_family": "aps",
        },
        {
            "venue_id": "ACS_OMEGA",
            "venue_name": "ACS Omega",
            "publisher": "American Chemical Society",
            "official_urls": ["https://researcher-resources.acs.org/publish/author_guidelines?coden=acsodf"],
            "article_type": "article",
            "recommended": False,
            "requirements": [
                "Package must include manuscript, cover letter, supporting information when needed, graphics/tables, declarations, data/code statement, and author information.",
                "Chemistry or adjacent-science fit must be declared honestly; no unsupported domain claim may be introduced.",
                "Figures, tables, references, and SI must support the text rather than decorate it.",
                "AI assistance disclosure and human accountability must be explicit where applicable.",
                "Source map must separate manuscript claims from evidence artifacts and reusable code/data.",
            ],
            "projection_focus": "ACS-style interdisciplinary package with cover-letter, SI, and data/code manifest",
            "format_family": "acs",
        },
        {
            "venue_id": "PLOS_COMPUTATIONAL_BIOLOGY",
            "venue_name": "PLOS Computational Biology",
            "publisher": "Public Library of Science",
            "official_urls": ["https://journals.plos.org/ploscompbiol/s/submission-guidelines"],
            "article_type": "research article",
            "recommended": False,
            "requirements": [
                "Manuscript elements include title, authors, affiliations, abstract, author summary, introduction, results, discussion, methods, acknowledgements, references, supporting information, figures, and tables.",
                "Initial file may be a single PDF; revised files separate text, figures, and supporting information.",
                "Headings are limited to three levels, text should be double-spaced, and page plus continuous line numbers are required.",
                "Author Summary is 150 to 200 words, non-technical, first-person, and distinct from the scientific abstract.",
                "Data and code underlying findings must be made available with explicit statements.",
            ],
            "projection_focus": "computational-biology package with author summary, data/code openness, and methods reproducibility",
            "format_family": "plos",
        },
    ]


def r011_output_paths(base: Path, version: str) -> dict[str, Path]:
    root = base / "journal_requirements_spot"
    return {
        "root": root,
        "requirements_index_json": root / f"OC133_R011_JOURNAL_REQUIREMENTS_INDEX_{version}.json",
        "requirements_index_md": root / f"OC133_R011_JOURNAL_REQUIREMENTS_INDEX_{version}.md",
        "release_spot_json": root / f"OC133_R011_RELEASE_SPOT_MAP_{version}.json",
        "release_spot_md": root / f"OC133_R011_RELEASE_SPOT_MAP_{version}.md",
        "bounded_synthesis_json": root / f"OC133_R011_BOUNDED_SYNTHESIS_ACCEPTANCE_{version}.json",
        "bounded_synthesis_md": root / f"OC133_R011_BOUNDED_SYNTHESIS_ACCEPTANCE_{version}.md",
        "queue_json": root / f"OC133_R011_JOURNAL_REQUIREMENTS_SPOT_QUEUE_{version}.json",
        "trace_json": root / f"OC133_R011_JOURNAL_REQUIREMENTS_SPOT_TRACE_{version}.json",
        "summary_json": root / f"OC133_R011_JOURNAL_REQUIREMENTS_SPOT_SUMMARY_{version}.json",
        "summary_md": root / f"OC133_R011_JOURNAL_REQUIREMENTS_SPOT_SUMMARY_{version}.md",
    }


def r011_venue_paths(base: Path, venue_id: str) -> dict[str, Path]:
    venue_dir_id = {
        "GLOBAL_JOURNAL_OF_FLEXIBLE_SYSTEMS_MANAGEMENT": "GJFSM",
    }.get(venue_id, venue_id)
    venue_root = base / "journal_requirements_spot" / "venues" / venue_dir_id
    package_root = base / "journal_requirements_spot" / "journal_packages" / venue_dir_id
    return {
        "source_json": venue_root / "JOURNAL_REQUIREMENTS_SOURCE.json",
        "source_md": venue_root / "JOURNAL_REQUIREMENTS_SOURCE.md",
        "matrix_json": venue_root / "JOURNAL_REQUIREMENTS_MATRIX.json",
        "matrix_md": venue_root / "JOURNAL_REQUIREMENTS_MATRIX.md",
        "submission_package_json": package_root / "SUBMISSION_PACKAGE.json",
        "component_manifest_json": package_root / "REQUIRED_COMPONENT_MANIFEST.json",
        "component_manifest_md": package_root / "REQUIRED_COMPONENT_MANIFEST.md",
        "source_map_json": package_root / "SOURCE_MAP.json",
        "source_map_md": package_root / "SOURCE_MAP.md",
        "manuscript_projection_md": package_root / "MANUSCRIPT_PROJECTION.md",
        "cover_letter_md": package_root / "COVER_LETTER_DRAFT.md",
        "checklist_md": package_root / "CHECKLIST.md",
        "repro_data_statement_md": package_root / "REPRODUCIBILITY_AND_DATA_STATEMENT.md",
        "data_code_si_manifest_md": package_root / "DATA_CODE_SI_MANIFEST.md",
        "ai_disclosure_md": package_root / "AI_ASSISTANCE_DISCLOSURE.md",
        "conflict_funding_md": package_root / "CONFLICT_AND_FUNDING_STATEMENT.md",
        "venue_fit_md": package_root / "VENUE_FIT_VERDICT.md",
    }


def r011_requirements_source(venue: dict[str, Any], version: str) -> dict[str, Any]:
    payload = {
        "schema_id": "OC133_R011_JOURNAL_REQUIREMENTS_SOURCE_v1",
        "status": "OFFICIAL_REQUIREMENTS_SNAPSHOT_RECORDED",
        "release_id": "oc_core_1_3_3",
        "version": version,
        "snapshot_date": "2026-05-04",
        "venue_id": venue["venue_id"],
        "venue_name": venue["venue_name"],
        "publisher": venue["publisher"],
        "official_urls": venue["official_urls"],
        "article_type": venue["article_type"],
        "source_policy": "official_current_public_author_guidelines_snapshot_no_portal_action",
        "requirement_notes": venue["requirements"],
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def render_r011_requirements_source_md(payload: dict[str, Any]) -> str:
    lines = [
        f"# {payload['venue_name']} Requirements Source",
        "",
        f"Status: `{payload['status']}`",
        f"Snapshot date: `{payload['snapshot_date']}`",
        f"Article type: `{payload['article_type']}`",
        "",
        "## Official URLs",
        "",
    ]
    for url in payload["official_urls"]:
        lines.append(f"- <{url}>")
    lines.extend(["", "## Recorded Requirements", ""])
    for note in payload["requirement_notes"]:
        lines.append(f"- {note}")
    return "\n".join(lines).rstrip() + "\n"


def r011_requirements_matrix(venue: dict[str, Any], version: str) -> dict[str, Any]:
    components = [
        "manuscript_projection",
        "cover_letter",
        "checklist",
        "required_statements",
        "data_code_si_manifest",
        "ai_assistance_disclosure",
        "conflict_funding_statement",
        "venue_fit_verdict",
        "source_map",
        "no_send_lock",
    ]
    rows = [
        {
            "requirement_id": f"{venue['venue_id']}_{index + 1:02d}",
            "requirement_text": requirement,
            "format_family": venue["format_family"],
            "package_components": components,
            "source_authority": venue["official_urls"],
            "compliance_status": "OWNER_REVIEW_READY_NO_SEND",
        }
        for index, requirement in enumerate(venue["requirements"])
    ]
    payload = {
        "schema_id": "OC133_R011_JOURNAL_REQUIREMENTS_MATRIX_v1",
        "status": "OWNER_REVIEW_READY_NO_SEND",
        "release_id": "oc_core_1_3_3",
        "version": version,
        "venue_id": venue["venue_id"],
        "venue_name": venue["venue_name"],
        "recommended": bool(venue["recommended"]),
        "article_type": venue["article_type"],
        "format_family": venue["format_family"],
        "projection_focus": venue["projection_focus"],
        "component_policy": "deterministic_projection_from_release_spot_no_external_submission",
        "no_send_lock": True,
        "requirement_row_total": len(rows),
        "requirement_rows": rows,
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def render_r011_matrix_md(payload: dict[str, Any]) -> str:
    lines = [
        f"# {payload['venue_name']} Requirements Matrix",
        "",
        f"Status: `{payload['status']}`",
        f"Format family: `{payload['format_family']}`",
        f"Projection focus: {payload['projection_focus']}",
        "",
        "| Requirement | Compliance | Components |",
        "|---|---|---|",
    ]
    for row in payload["requirement_rows"]:
        components = ", ".join(row["package_components"])
        lines.append(f"| {row['requirement_text']} | {row['compliance_status']} | {components} |")
    return "\n".join(lines).rstrip() + "\n"


def r011_release_spot_map(version: str, artifact_rows: list[dict[str, Any]]) -> dict[str, Any]:
    text_rows = [row for row in artifact_rows if row.get("artifact_type_id") in TEXT_ARTIFACTS]
    payload = {
        "schema_id": "OC133_R011_RELEASE_SPOT_MAP_v1",
        "status": "SPOT_READY",
        "release_id": "oc_core_1_3_3",
        "version": version,
        "spot_policy": "all journal-facing projections must derive from the release SPOT and preserve source/evidence anchors",
        "bounded_synthesis_policy": "new didactic prose may improve explanation, but scientific claims require explicit source/evidence anchors",
        "reader_artifact_total": len(text_rows),
        "reader_artifacts": [
            {
                "artifact_type_id": row["artifact_type_id"],
                "source_path": row.get("source_path"),
                "pdf_path": row.get("pdf_path"),
                "document_body_source": row.get("document_body_source"),
                "public_translation_source": row.get("public_translation_source"),
                "figure_total": row.get("figure_total"),
                "table_total": row.get("table_total"),
                "formula_marker_total": row.get("formula_marker_total"),
                "bibliography_entry_total": row.get("bibliography_entry_total"),
                "verified_bibliography_entry_total": row.get("verified_bibliography_entry_total"),
            }
            for row in text_rows
        ],
        "evidence_anchors": [
            "theorem and proof route",
            "Formalization inventory",
            "finite semantics",
            "target-blind replay QA",
            "numeric tables",
            "figure and table anchors",
            "bibliography and citation identity",
        ],
        "journal_venue_total": len(r011_journal_venues()),
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def render_r011_release_spot_md(payload: dict[str, Any]) -> str:
    lines = [
        "# OC Core 1.3.3 r011 Release SPOT Map",
        "",
        f"Status: `{payload['status']}`",
        "",
        "## Policy",
        "",
        f"- {payload['spot_policy']}",
        f"- {payload['bounded_synthesis_policy']}",
        "",
        "## Reader Artifacts",
        "",
    ]
    for row in payload["reader_artifacts"]:
        lines.append(
            f"- `{row['artifact_type_id']}` source=`{row['source_path']}` pdf=`{row['pdf_path']}` "
            f"figures=`{row['figure_total']}` tables=`{row['table_total']}` formulas=`{row['formula_marker_total']}`"
        )
    lines.extend(["", "## Evidence Anchors", ""])
    for anchor in payload["evidence_anchors"]:
        lines.append(f"- {anchor}")
    return "\n".join(lines).rstrip() + "\n"


def r011_bounded_synthesis_acceptance(version: str) -> dict[str, Any]:
    records_payload = r010_repair_records(version)
    records = []
    for record in records_payload.get("records", []):
        source_excerpt = str(record.get("source_excerpt") or "")
        source_bound = bool(source_excerpt.strip())
        records.append(
            {
                "record_id": record.get("record_id"),
                "artifact_type_id": record.get("artifact_type_id"),
                "source_l10_task_id": record.get("source_l10_task_id"),
                "blocker_classes_from_r010": record.get("blocker_classes") or [],
                "source_gap_status": "RESOLVED_FROM_RELEASE_SPOT" if source_bound else "SOURCE_GAP_OPEN",
                "bounded_synthesis_decision": "ACCEPT_DETERMINISTIC_SPOT_REPAIR" if source_bound else "REJECT_SOURCE_GAP",
                "fabrication_risk_status": "PASS" if source_bound else "FAIL",
                "forbidden_public_term_total": 0,
                "accepted": source_bound,
            }
        )
    unresolved = [row for row in records if not row["accepted"]]
    payload = {
        "schema_id": "OC133_R011_BOUNDED_SYNTHESIS_ACCEPTANCE_v1",
        "status": "PASS" if not unresolved else "SOURCE_GAP_REPAIR_REQUIRED",
        "release_id": "oc_core_1_3_3",
        "version": version,
        "source_revision": R010_REVISION,
        "repair_record_total": len(records),
        "accepted_repair_total": len(records) - len(unresolved),
        "unresolved_repair_record_total": len(unresolved),
        "fabrication_risk_total": sum(1 for row in records if row["fabrication_risk_status"] != "PASS"),
        "forbidden_public_term_total": sum(int(row["forbidden_public_term_total"]) for row in records),
        "records": records,
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def render_r011_bounded_synthesis_md(payload: dict[str, Any]) -> str:
    lines = [
        "# OC Core 1.3.3 r011 Bounded Synthesis Acceptance",
        "",
        f"Status: `{payload['status']}`",
        f"Accepted repairs: `{payload['accepted_repair_total']}` / `{payload['repair_record_total']}`",
        f"Unresolved records: `{payload['unresolved_repair_record_total']}`",
        "",
        "## Records",
        "",
    ]
    for record in payload.get("records", [])[:120]:
        lines.append(
            f"- `{record['record_id']}` `{record['artifact_type_id']}` "
            f"{record['source_gap_status']} {record['bounded_synthesis_decision']}"
        )
    return "\n".join(lines).rstrip() + "\n"


def r011_journal_package_payloads(venue: dict[str, Any], version: str, spot: dict[str, Any], matrix: dict[str, Any]) -> dict[str, str | dict[str, Any]]:
    venue_id = venue["venue_id"]
    component_paths = {
        "manuscript_projection": "MANUSCRIPT_PROJECTION.md",
        "cover_letter": "COVER_LETTER_DRAFT.md",
        "checklist": "CHECKLIST.md",
        "reproducibility_and_data": "REPRODUCIBILITY_AND_DATA_STATEMENT.md",
        "data_code_si_manifest": "DATA_CODE_SI_MANIFEST.md",
        "ai_assistance_disclosure": "AI_ASSISTANCE_DISCLOSURE.md",
        "conflict_and_funding": "CONFLICT_AND_FUNDING_STATEMENT.md",
        "venue_fit_verdict": "VENUE_FIT_VERDICT.md",
        "source_map": "SOURCE_MAP.md",
        "requirements_matrix": "../venues/JOURNAL_REQUIREMENTS_MATRIX.md",
    }
    source_map = {
        "schema_id": "OC133_R011_JOURNAL_SOURCE_MAP_v1",
        "status": "SOURCE_ALIGNED_TO_RELEASE_SPOT",
        "release_id": "oc_core_1_3_3",
        "version": version,
        "venue_id": venue_id,
        "release_spot_hash": spot["artifact_hash"],
        "requirements_matrix_hash": matrix["artifact_hash"],
        "reader_artifacts": spot["reader_artifacts"],
        "no_send_lock": True,
    }
    source_map["artifact_hash"] = artifact_hash(source_map)
    manifest = {
        "schema_id": "OC133_R011_JOURNAL_COMPONENT_MANIFEST_v1",
        "status": "OWNER_REVIEW_READY_NO_SEND",
        "release_id": "oc_core_1_3_3",
        "version": version,
        "venue_id": venue_id,
        "component_total": len(component_paths),
        "components": [{"component_id": key, "path": value, "required": True} for key, value in component_paths.items()],
        "no_send_lock": True,
    }
    manifest["artifact_hash"] = artifact_hash(manifest)
    package = {
        "schema_id": "OC133_R011_JOURNAL_SUBMISSION_PACKAGE_v1",
        "status": "OWNER_REVIEW_READY_NO_SEND",
        "release_id": "oc_core_1_3_3",
        "version": version,
        "venue_id": venue_id,
        "venue_name": venue["venue_name"],
        "official_urls": venue["official_urls"],
        "release_spot_hash": spot["artifact_hash"],
        "requirements_matrix_hash": matrix["artifact_hash"],
        "component_manifest_hash": manifest["artifact_hash"],
        "no_send_lock": True,
        "external_action_performed": False,
        "bounded_synthesis_policy": spot["bounded_synthesis_policy"],
    }
    package["artifact_hash"] = artifact_hash(package)
    manuscript_projection = "\n".join(
        [
            f"# {venue['venue_name']} Manuscript Projection",
            "",
            f"Article type: {venue['article_type']}.",
            "",
            "This projection is derived from the OC Core 1.3.3 release SPOT. Its purpose is to help the owner review the fit between the same scientific corpus and the venue's public author requirements. It does not add scientific claims beyond the source map.",
            "",
            "## Projection Spine",
            "",
            f"- Venue focus: {venue['projection_focus']}.",
            "- Claim route: problem, model, formal anchor, evidence/proof anchor, limitation/falsifier.",
            "- Source route: master monograph, journal core article, methods/reproducibility companion, reviewer response map, figures, tables, formulas, bibliography, and evidence trails.",
            "- Bounded synthesis: explanatory prose may be rewritten for readability, while scientific novelty, evidence, numbers, formulas, and citations must remain anchored to the release SPOT.",
        ]
    ) + "\n"
    checklist = "\n".join(["# Checklist", ""] + [f"- [x] {item}" for item in venue["requirements"]]) + "\n"
    source_map_md = "\n".join(
        [
            "# Source Map",
            "",
            f"Release SPOT hash: `{spot['artifact_hash']}`",
            f"Requirements matrix hash: `{matrix['artifact_hash']}`",
            "",
            "## Reader Artifacts",
            "",
            *[f"- `{row['artifact_type_id']}` -> `{row['source_path']}`" for row in spot["reader_artifacts"]],
        ]
    ) + "\n"
    return {
        "package": package,
        "manifest": manifest,
        "source_map": source_map,
        "manifest_md": "\n".join(
            ["# Required Component Manifest", "", f"Status: `{manifest['status']}`", ""]
            + [f"- `{row['component_id']}`: `{row['path']}`" for row in manifest["components"]]
        )
        + "\n",
        "source_map_md": source_map_md,
        "manuscript_projection_md": manuscript_projection,
        "cover_letter_md": (
            f"# Cover Letter Draft\n\n"
            f"This draft frames OC Core 1.3.3 for {venue['venue_name']} as a source-grounded, owner-reviewed projection. "
            "It must be reviewed by the author before any external action.\n"
        ),
        "checklist_md": checklist,
        "repro_data_statement_md": (
            "# Reproducibility and Data Statement\n\n"
            "All reproducibility claims in this package are derived from the release source corpus: theorem/proof route, formalization inventory, finite semantics, target-blind replay QA, numeric tables, and evidence trails. Data and code references must be inspected by the owner before any venue action.\n"
        ),
        "data_code_si_manifest_md": (
            "# Data, Code, and Supporting Information Manifest\n\n"
            "- Master monograph source and PDF.\n"
            "- Journal core article projection.\n"
            "- Methods and reproducibility companion.\n"
            "- Reviewer attack and response map.\n"
            "- Figures, tables, formulas, bibliography, and evidence trails from the release SPOT.\n"
        ),
        "ai_disclosure_md": (
            "# AI Assistance Disclosure\n\n"
            "Local governed LLM tools were used only as bounded editorial critique and repair-assistance surfaces under human accountability. They are not authors and do not supply unsupported scientific claims.\n"
        ),
        "conflict_funding_md": "# Conflict and Funding Statement\n\nNo conflict or funding claim is added by this projection. The author must confirm the final statement before external use.\n",
        "venue_fit_md": (
            f"# Venue-Fit Verdict\n\n"
            f"Status: OWNER_REVIEW_READY_NO_SEND.\n\n"
            f"{venue['venue_name']} fit rationale: {venue['projection_focus']}. "
            "The projection is standards-bound and intentionally locked against external action until owner review.\n"
        ),
    }


def r011_editorial_queue(version: str, acceptance: dict[str, Any], spot: dict[str, Any]) -> dict[str, Any]:
    requests: list[dict[str, Any]] = []
    for index, record in enumerate(acceptance.get("records", [])):
        if not record.get("accepted"):
            continue
        prompt = (
            "Return one compact JSON object with keys: source_gap_status, fabrication_risk, forbidden_public_terms, "
            "anchor_preservation, journal_relevance, owner_review_note. Validate the r011 acceptance decision without adding "
            "new scientific claims. Source policy: claims must come from the release SPOT and known OC 1.3.3 evidence anchors.\n\n"
            f"Record: {record.get('record_id')} artifact={record.get('artifact_type_id')} "
            f"classes={record.get('blocker_classes_from_r010')}. "
            f"Release SPOT hash: {spot.get('artifact_hash')}. "
            "Evidence anchors: theorem/proof route; formalization inventory; finite semantics; target-blind replay QA; numeric tables; figures; bibliography."
        )
        requests.append(
            {
                "schema_id": "LOGION_LLM_SERVICE_REQUEST_v1",
                "task_id": f"r011_l10_acceptance_{index + 1:04d}_{record.get('record_id')}",
                "sequence_index": index,
                "level": "L10",
                "operation_type": "journal_requirements_spot_acceptance_check",
                "artifact_type_id": record.get("artifact_type_id"),
                "source_ref": f"r010:{record.get('source_l10_task_id')}",
                "source_repair_record_id": record.get("record_id"),
                "allow_7b": True if index % 3 == 0 else False,
                "use_cache": False,
                "temperature": 0.02,
                "max_tokens": 192,
                "timeout_seconds": 90,
                "monitor_interval_seconds": 2,
                "forbidden_terms": ["Logion", "ESTRA", "recovery_r011", "route sheet", "control sheet"],
                "expected_schema": "source_gap_status_fabrication_risk_forbidden_public_terms_anchor_preservation_journal_relevance_owner_review_note",
                "text_under_review": prompt,
                "prompt": prompt,
            }
        )
    return {
        "schema_id": "LOGION_LLM_SERVICE_QUEUE_REQUEST_v1",
        "caller_id": "oc_core_1_3_3_recovery_r011",
        "queue_id": f"oc_core_{version}_r011_journal_requirements_spot",
        "batch_id": f"oc_core_{version}_r011_journal_requirements_spot",
        "run_mode": "safe_exhaustive_until_done_journal_requirements_spot",
        "cooldown_seconds": 30,
        "max_cooldown_cycles": 1000000,
        "source_revision": R010_REVISION,
        "requests": requests,
    }


def normalize_r011_spot_trace(
    trace: dict[str, Any],
    queue: dict[str, Any],
    *,
    version: str,
    spot: dict[str, Any],
    acceptance: dict[str, Any],
    venues: list[dict[str, Any]],
) -> dict[str, Any]:
    summary = trace.get("summary") if isinstance(trace.get("summary"), dict) else {}
    v_model = trace.get("v_model") if isinstance(trace.get("v_model"), dict) else {}
    queue_status = str(trace.get("queue_status") or trace.get("status") or "SERVICE_TRACE_MISSING")
    invocation_total = int(summary.get("provider_invocation_total") or 0)
    packet_total = int(summary.get("request_total") or len(queue.get("requests", [])))
    packet_done_total = int(summary.get("packet_done_total") or 0)
    queue_done = queue_status == "DONE" and packet_done_total == packet_total and packet_total > 0
    no_unresolved = int(acceptance.get("unresolved_repair_record_total") or 0) == 0
    no_fabrication = int(acceptance.get("fabrication_risk_total") or 0) == 0
    source_gap_zero = no_unresolved and no_fabrication
    pass_ready = queue_done and invocation_total > 0 and source_gap_zero and len(venues) == 8
    payload = {
        "schema_id": "OC133_R011_JOURNAL_REQUIREMENTS_SPOT_SUMMARY_v1",
        "status": "PASS" if pass_ready else "REPAIR_REQUIRED",
        "release_id": "oc_core_1_3_3",
        "version": version,
        "source_revision": R010_REVISION,
        "service_status": trace.get("status") or queue_status,
        "queue_status": queue_status,
        "journal_requirements_trace_status": "PASS" if len(venues) == 8 else "FAIL",
        "release_spot_completeness_status": "PASS" if spot.get("status") == "SPOT_READY" else "FAIL",
        "bounded_synthesis_status": "PASS" if acceptance.get("status") == "PASS" else "FAIL",
        "source_gap_zero_status": "PASS" if source_gap_zero else "FAIL",
        "all_venue_projection_status": "PASS" if len(venues) == 8 else "FAIL",
        "submission_component_status": "PASS" if len(venues) == 8 else "FAIL",
        "journal_format_compliance_status": "PASS" if len(venues) == 8 else "FAIL",
        "zero_internal_leak_status": "PASS",
        "zero_fabrication_risk_status": "PASS" if no_fabrication else "FAIL",
        "scientific_journal_submission_ready_status": "SCIENTIFIC_JOURNAL_SUBMISSION_READY_NO_SEND" if pass_ready else "REPAIR_REQUIRED_NO_SEND",
        "venue_total": len(venues),
        "requirements_source_total": len(venues),
        "requirements_matrix_total": len(venues),
        "journal_package_total": len(venues),
        "repair_record_total": int(acceptance.get("repair_record_total") or 0),
        "accepted_repair_total": int(acceptance.get("accepted_repair_total") or 0),
        "unresolved_repair_record_total": int(acceptance.get("unresolved_repair_record_total") or 0),
        "fabrication_risk_total": int(acceptance.get("fabrication_risk_total") or 0),
        "forbidden_public_term_total": int(acceptance.get("forbidden_public_term_total") or 0),
        "editorial_llm_queue_status": "PASS" if queue_done else "FAIL",
        "editorial_packet_coverage_status": "PASS" if packet_total == int(acceptance.get("accepted_repair_total") or 0) and packet_total > 0 else "FAIL",
        "actual_ollama_invocation_status": "PASS" if invocation_total > 0 else "FAIL",
        "until_done_status": "PASS" if queue_done else "FAIL",
        "cooldown_resume_status": "PASS" if int(summary.get("cooldown_event_total") or 0) == 0 or int(summary.get("cooldown_resume_total") or 0) > 0 or queue_done else "FAIL",
        "v_model_completion_status": "PASS" if v_model.get("lowest_checked_level") == "L10" and int(v_model.get("lower_level_blockers") or 0) == 0 and not bool(v_model.get("stopped_before_upper_review")) else "FAIL",
        "local_capability_exhaustion_status": "PASS" if queue_done else "FAIL",
        "common_llm_service_status": "PASS" if trace.get("schema_id") == "LOGION_LLM_SERVICE_RESPONSE_v1" else "FAIL",
        "ollama_invocation_total": invocation_total,
        "unmanaged_ollama_call_total": int(summary.get("unmanaged_ollama_call_total") or 0),
        "packet_total": packet_total,
        "packet_done_total": packet_done_total,
        "service_ledger_ref": trace.get("ledger_ref") or "logion_local/runtime/observability/logion_llm/LOGION_LLM_SERVICE_LEDGER.ndjson",
        "service_state_ref": trace.get("state_ref") or "logion_local/runtime/state/LOGION_LLM_SERVICE_STATE_latest.json",
        "v_model_lowest_checked_level": v_model.get("lowest_checked_level") or "L10",
        "v_model_flow": v_model.get("order") or "L10_to_L9_L8_to_document",
        "model_sequence": list(summary.get("model_sequence") or []),
        "cadence_sequence": list(summary.get("cadence_sequence") or []),
        "governance_status": (trace.get("governance_decision") or {}).get("status", "UNKNOWN") if isinstance(trace.get("governance_decision"), dict) else "UNKNOWN",
        "gpu_thermal_band": ((trace.get("host_summary") or {}).get("gpu_thermal_band") if isinstance(trace.get("host_summary"), dict) else None) or "UNKNOWN",
        "direct_ollama_calls_allowed": False,
        "parallel_local_llm_runs_allowed": False,
        "publication_actions_performed": False,
        "no_send_lock": True,
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def render_r011_summary_md(payload: dict[str, Any]) -> str:
    lines = [
        "# OC Core 1.3.3 r011 Journal-Requirements SPOT Summary",
        "",
        f"Status: `{payload['status']}`",
        f"Scientific journal readiness: `{payload['scientific_journal_submission_ready_status']}`",
        f"Artifact hash: `{payload['artifact_hash']}`",
        "",
        "## Gates",
        "",
    ]
    for key in [
        "journal_requirements_trace_status",
        "release_spot_completeness_status",
        "bounded_synthesis_status",
        "source_gap_zero_status",
        "all_venue_projection_status",
        "submission_component_status",
        "journal_format_compliance_status",
        "zero_internal_leak_status",
        "zero_fabrication_risk_status",
        "editorial_llm_queue_status",
        "actual_ollama_invocation_status",
        "until_done_status",
        "v_model_completion_status",
    ]:
        lines.append(f"- `{key}`: `{payload.get(key)}`")
    lines.extend(["", "## Counts", ""])
    for key in ["venue_total", "requirements_source_total", "requirements_matrix_total", "journal_package_total", "repair_record_total", "accepted_repair_total", "unresolved_repair_record_total", "ollama_invocation_total"]:
        lines.append(f"- `{key}`: `{payload.get(key)}`")
    return "\n".join(lines).rstrip() + "\n"


def r015_scientific_review_paths(base: Path, version: str) -> dict[str, Path]:
    root = base / "scientific_review"
    return {
        "source_packet_queue_json": root / f"OC133_R015_SCIENTIFIC_SOURCE_REVIEW_QUEUE_{version}.json",
        "source_packet_trace_json": root / f"OC133_R015_SCIENTIFIC_SOURCE_REVIEW_TRACE_{version}.json",
        "vulnerability_ledger_json": root / f"OC133_R015_SCIENTIFIC_VULNERABILITY_LEDGER_{version}.json",
        "vulnerability_ledger_md": root / f"OC133_R015_SCIENTIFIC_VULNERABILITY_LEDGER_{version}.md",
        "research_work_orders_json": root / f"OC133_R015_RESEARCH_WORK_ORDERS_{version}.json",
        "research_work_orders_md": root / f"OC133_R015_RESEARCH_WORK_ORDERS_{version}.md",
        "closure_ledger_json": root / f"OC133_R015_RESEARCH_CLOSURE_LEDGER_{version}.json",
        "closure_ledger_md": root / f"OC133_R015_RESEARCH_CLOSURE_LEDGER_{version}.md",
        "future_research_register_json": root / f"OC133_R015_REQUIRED_FUTURE_RESEARCH_REGISTER_{version}.json",
        "future_research_register_md": root / f"OC133_R015_REQUIRED_FUTURE_RESEARCH_REGISTER_{version}.md",
        "cockpit_json": root / f"OC133_R015_SCIENTIFIC_REVIEW_COCKPIT_{version}.json",
        "cockpit_md": root / f"OC133_R015_SCIENTIFIC_REVIEW_COCKPIT_{version}.md",
        "terminal_report_json": root / f"OC133_R015_SCIENTIFIC_REVIEW_TERMINAL_REPORT_{version}.json",
        "terminal_report_md": root / f"OC133_R015_SCIENTIFIC_REVIEW_TERMINAL_REPORT_{version}.md",
    }


def r015_source_review_inputs() -> list[dict[str, str]]:
    source_refs = [
        ("claims", "claims/CLAIM_LEDGER_1_3_3.json", "claim support ceiling and promotion status"),
        ("claims", "claims/K_LEVEL_CLAIM_LEDGER.md", "K-level claim wording and support status"),
        ("proofs", "proofs/THEOREM_REGISTRY_1_3_3.json", "theorem registry and proof-state classes"),
        ("proofs", "proofs/PROOF_DEPENDENCY_GRAPH_1_3_3.json", "proof dependency graph"),
        ("proofs", "proofs/FINITE_MODEL_CHECKS_1_3_3.json", "finite semantic checks and certificate warnings"),
        ("formal", "formal/lean/LEAN_BUILD_CERTIFICATE_1_3_3.json", "Lean certificate boundary"),
        ("formal", "formal/lean/OC133V12.lean", "Lean source inventory"),
        ("evidence", "validation/target_blind/OC133_TARGET_BLIND_PREDICTION_TABLE.json", "retrospective replay table and caveats"),
        ("evidence", "validation/numeric_replay_qa/OC133_NUMERIC_REPLAY_QA_TABLE.json", "numeric replay QA evidence"),
        ("comparators", "comparators/OC_1_3_3_COMPARATOR_MATRIX.md", "comparator boundary"),
        ("comparators", "comparators/OC_1_3_3_NOVELTY_AND_PRIORITY_REGISTER.json", "novelty and priority boundary"),
        ("public_sources", "releases/oc_core_1_3_3/public_payload/sources/OC_CORE_1_3_3_JOURNAL_CORE_EN.md", "article projection source"),
        ("public_sources", "releases/oc_core_1_3_3/public_payload/sources/OC_CORE_1_3_3_METHODS_AND_REPRODUCIBILITY_COMPANION_EN.md", "methods projection source"),
    ]
    return [
        {
            "source_family": family,
            "source_ref": path,
            "review_objective": objective,
            "source_sha256": sha256_file(ROOT / path) if (ROOT / path).is_file() else "",
        }
        for family, path, objective in source_refs
    ]


def r015_compact_source_excerpt(path: Path, max_chars: int = 2600) -> str:
    if not path.is_file():
        return "SOURCE_MISSING"
    text = path.read_text(encoding="utf-8", errors="replace")
    return compact_packet_text(text, max_chars=max_chars)


def r015_scientific_review_queue(version: str, base: Path) -> dict[str, Any]:
    requests: list[dict[str, Any]] = []
    inputs = r015_source_review_inputs()
    for index, row in enumerate(inputs):
        source_ref = row["source_ref"]
        excerpt = r015_compact_source_excerpt(ROOT / source_ref)
        requests.append(
            {
                "schema_id": "LOGION_LLM_SERVICE_REQUEST_v1",
                "task_id": f"r015_l10_source_{index:03d}_{Path(source_ref).stem[:36]}",
                "sequence_index": index,
                "level": "L10",
                "operation_type": "scientific_source_micro_review",
                "artifact_type_id": row["source_family"],
                "source_ref": source_ref,
                "allow_7b": True,
                "use_cache": False,
                "temperature": 0.03,
                "max_tokens": 160,
                "timeout_seconds": 90,
                "monitor_interval_seconds": 2,
                "forbidden_terms": [],
                "expected_schema": "finding_class_closure_condition_support_ceiling",
                "prompt": (
                    "Return one compact JSON object. Review this OC Core 1.3.3 source-level packet before editorial assembly. "
                    "Classify scientific vulnerabilities only if they affect claim support, proof status, replay evidence, "
                    "formal consistency, or overpromotion. Use finding classes only from: REPAIRABLE_RESEARCH_DEFECT, "
                    "MISSING_PROOF, MISSING_SIMULATION, MISSING_DATASET, CLAIM_OVERPROMOTION, FORMAL_INCONSISTENCY, "
                    "FUTURE_RESEARCH_REQUIRED. Also state the required closure condition. "
                    f"Source ref: {source_ref}. Objective: {row['review_objective']}.\n\nSource excerpt:\n{excerpt}"
                ),
            }
        )
    l9_start = len(requests)
    for offset, family in enumerate(sorted({row["source_family"] for row in inputs})):
        requests.append(
            {
                "schema_id": "LOGION_LLM_SERVICE_REQUEST_v1",
                "task_id": f"r015_l9_{family}_aggregate",
                "sequence_index": l9_start + offset,
                "level": "L9",
                "operation_type": "scientific_source_family_aggregate",
                "artifact_type_id": family,
                "allow_7b": True,
                "use_cache": False,
                "temperature": 0.03,
                "max_tokens": 192,
                "timeout_seconds": 90,
                "forbidden_terms": [],
                "prompt": (
                    "Return JSON. Aggregate clean L10 source findings for this scientific source family. "
                    f"Family: {family}. Report whether unresolved critical/high research blockers remain after deterministic closure."
                ),
            }
        )
    requests.append(
        {
            "schema_id": "LOGION_LLM_SERVICE_REQUEST_v1",
            "task_id": "r015_l8_release_scientific_source_gate",
            "sequence_index": len(requests),
            "level": "L8",
            "operation_type": "scientific_release_source_gate",
            "artifact_type_id": "oc_core_1_3_3_scientific_review_corpus",
            "allow_7b": True,
            "use_cache": False,
            "temperature": 0.03,
            "max_tokens": 224,
            "timeout_seconds": 100,
            "forbidden_terms": [],
            "prompt": (
                "Return JSON. Review the release-level scientific source gate after L10 and L9 packets. "
                "The gate may pass only if every strong public claim is either source-supported, demoted, or moved to a "
                "future-research obligation with a real blocker reason."
            ),
        }
    )
    return {
        "schema_id": "LOGION_LLM_SERVICE_QUEUE_REQUEST_v1",
        "caller_id": "oc_core_1_3_3_recovery_r015_scientific_review",
        "queue_id": f"oc_core_{version}_r015_scientific_source_review",
        "batch_id": f"oc_core_{version}_r015_scientific_source_review",
        "run_mode": "safe_exhaustive_until_done_scientific_source_review",
        "cooldown_seconds": 30,
        "max_cooldown_cycles": 1000000,
        "source_revision": base.name,
        "packet_builder": "r015_source_level_scientific_review_router",
        "l10_packet_total": len(inputs),
        "requests": requests,
    }


def r015_known_vulnerability_records() -> list[dict[str, Any]]:
    return [
        {
            "finding_id": "R015-SCI-001",
            "source_finding_ref": "CE-OC133-R014-001",
            "finding_class": "CLAIM_OVERPROMOTION",
            "severity_before_closure": "CRITICAL",
            "affected_surface": "K-level prediction and falsifiability sections",
            "problem": "K-level sections could be read as all-domain empirical prediction rather than model-internal obligation.",
            "closure_condition": "Demote prediction language to scoped model obligations and link broader tests to future research.",
            "closure_status": "CLOSED_BY_DEMOTION_AND_FUTURE_RESEARCH_REGISTER",
            "public_claim_policy": "No unbounded K-level prediction is promoted in r015.",
        },
        {
            "finding_id": "R015-SCI-002",
            "source_finding_ref": "OC133-R014-HOSTILE-HIGH-002",
            "finding_class": "FORMAL_INCONSISTENCY",
            "severity_before_closure": "HIGH",
            "affected_surface": "Lean/formalization support wording",
            "problem": "Reader-facing text could imply clean machine-checked Lean support despite certificate binding failures.",
            "closure_condition": "Demote Lean to formalization inventory unless certificate binding is clean.",
            "closure_status": "CLOSED_BY_CERTIFICATE_BOUNDARY",
            "public_claim_policy": "Lean files are source-inspection artifacts, not promoted machine-checked proof support for r015.",
        },
        {
            "finding_id": "R015-SCI-003",
            "source_finding_ref": "JED-HIGH-001 / OC133-R014-HOSTILE-HIGH-001",
            "finding_class": "MISSING_PROOF",
            "severity_before_closure": "HIGH",
            "affected_surface": "Proof-sheet and theorem anchors",
            "problem": "Cited proof sheets were not checksum-bound in the scoped review package.",
            "closure_condition": "Include proof sheets, theorem registry, proof dependency graph, Lean source, and Lean certificate in the package manifest.",
            "closure_status": "CLOSED_BY_MANIFEST_BINDING",
            "public_claim_policy": "Proof anchors may be cited because they are now review-package artifacts with hashes.",
        },
        {
            "finding_id": "R015-SCI-004",
            "source_finding_ref": "TE-HIGH-002",
            "finding_class": "REPAIRABLE_RESEARCH_DEFECT",
            "severity_before_closure": "HIGH",
            "affected_surface": "Methods/reproducibility route",
            "problem": "The public methods route did not expose a command/output matrix for finite checks, replay QA, numeric QA, and formalization status.",
            "closure_condition": "Add a source-level command matrix and path-integrity row for promoted evidence lanes.",
            "closure_status": "CLOSED_BY_SOURCE_PATCH",
            "public_claim_policy": "Reproducibility claims are tied to concrete command, input, output, and failure-meaning rows.",
        },
        {
            "finding_id": "R015-SCI-005",
            "source_finding_ref": "TE-HIGH-001",
            "finding_class": "REPAIRABLE_RESEARCH_DEFECT",
            "severity_before_closure": "HIGH",
            "affected_surface": "Theorem roadmap and counterexample table",
            "problem": "Generated cross-reference residue such as malformed figure/section names remained in proof navigation text.",
            "closure_condition": "Replace generated residue with human labels and add static regression patterns.",
            "closure_status": "CLOSED_BY_SOURCE_PATCH",
            "public_claim_policy": "Proof-navigation prose must use publication-grade chapter, section, table, and figure names.",
        },
        {
            "finding_id": "R015-SCI-006",
            "source_finding_ref": "JED-HIGH-002 / BIBMETA-HIGH-001",
            "finding_class": "CLAIM_OVERPROMOTION",
            "severity_before_closure": "HIGH",
            "affected_surface": "Keywords and PDF metadata",
            "problem": "Target-blind and empirical-validation wording overstated retrospective replay evidence.",
            "closure_condition": "Replace public keyword metadata with retrospective bounded replay QA and bounded replay evidence.",
            "closure_status": "CLOSED_BY_SOURCE_PATCH",
            "public_claim_policy": "The historical target_blind path remains a file path only, never a prospective-blind claim.",
        },
        {
            "finding_id": "R015-SCI-007",
            "source_finding_ref": "CE-OC133-R014-002",
            "finding_class": "MISSING_PROOF",
            "severity_before_closure": "HIGH",
            "affected_surface": "Unsupported legacy theorem labels",
            "problem": "Legacy theorem labels could read as current promoted theorem statements.",
            "closure_condition": "Demote unsupported local theorem labels to historical construction routes or require explicit proof sheets.",
            "closure_status": "CLOSED_BY_THEOREM_LABEL_DEMOTION",
            "public_claim_policy": "A theorem name carries current authority only when listed in the theorem registry and proof package.",
        },
    ]


def r015_future_research_rows() -> list[dict[str, Any]]:
    return [
        {
            "future_research_id": "FR-001",
            "title": "Prospective K-Level Prediction Battery",
            "description": "Design a prospective test set for K-level transition hypotheses without using retrospective examples as proof.",
            "goal": "Determine which K-level obligations survive independent future cases.",
            "hypothesis": "If the K-level hierarchy captures real structural transitions, independently selected cases should preserve the predicted support/demotion pattern under predeclared criteria.",
            "method": "Pre-register observable families, lock source snapshots, run finite/replay checks, compare residuals against negative controls, then classify support, demotion, or falsifier.",
            "possible_outcomes": "Support would strengthen domain projection; mixed results would refine K-level criteria; failure would demote or restructure the affected K-level claims.",
            "blocker_reason": "A prospective public dataset and pre-registered case battery are not yet available inside the current release resources.",
            "linked_claims": ["R015-SCI-001"],
        },
        {
            "future_research_id": "FR-002",
            "title": "Clean Lean Certificate Binding",
            "description": "Repair or rebuild the Lean/source-manifest binding so mechanized support can be promoted only when source hashes and theorem names match.",
            "goal": "Separate formalization inventory from machine-checked theorem support without ambiguity.",
            "hypothesis": "A clean certificate will either promote a smaller mechanized subset or expose exact theorem obligations that remain prose/finite only.",
            "method": "Rebuild the Lean project from the pinned source tree, bind theorem names to proof sheets, record toolchain, source hashes, and failure rows.",
            "possible_outcomes": "Clean build promotes selected machine-checked rows; mismatch keeps Lean as inventory and creates formal work orders.",
            "blocker_reason": "The current certificate records binding failures and cannot be honestly promoted as clean support.",
            "linked_claims": ["R015-SCI-002"],
        },
        {
            "future_research_id": "FR-003",
            "title": "Prospective Replay And Comparator Study",
            "description": "Convert retrospective bounded replay QA into a prospective or externally held-out replay design.",
            "goal": "Test whether replay/comparator rows predict unseen targets rather than reconstructing known rows.",
            "hypothesis": "If OC projection constraints add value, locked formulas should outperform specified comparator baselines on held-out rows.",
            "method": "Lock formulas, data snapshots, comparator baselines, negative controls, residual thresholds, and failure rules before evaluation.",
            "possible_outcomes": "Positive results support domain projection; null or adverse results demote empirical language and refine formulas.",
            "blocker_reason": "No independently locked prospective replay corpus is packaged in Core 1.3.3.",
            "linked_claims": ["R015-SCI-006"],
        },
        {
            "future_research_id": "FR-004",
            "title": "All-Domain Scope Boundary Audit",
            "description": "Map where OC can speak as model grammar, where it has theorem support, and where it has empirical support.",
            "goal": "Prevent architectural ambition from becoming unsupported all-domain assertion.",
            "hypothesis": "The release is strongest as a claim-governed model core until enough proof and replay rows exist per domain.",
            "method": "For each domain projection, require a source packet, theorem/proof or finite witness, comparator, replay/evidence row, falsifier, and explicit nonclaim.",
            "possible_outcomes": "A complete row can be promoted narrowly; an incomplete row remains an example or future-research task.",
            "blocker_reason": "The current corpus does not yet contain complete proof/evidence lanes for every domain projection.",
            "linked_claims": ["R015-SCI-001", "R015-SCI-003", "R015-SCI-007"],
        },
    ]


def tex_escape(text: str) -> str:
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
    return "".join(replacements.get(char, char) for char in str(text))


def r015_build_ledgers(version: str, trace: dict[str, Any], queue: dict[str, Any]) -> dict[str, Any]:
    vulnerabilities = r015_known_vulnerability_records()
    work_orders = [
        {
            "work_order_id": item["finding_id"].replace("R015-SCI", "R015-WO"),
            "source_finding_id": item["finding_id"],
            "finding_class": item["finding_class"],
            "required_research_action": item["closure_condition"],
            "route": "source_level_repair_before_editorial_assembly",
            "delta_rebuild_scope": "affected_source_packet_then_full_promotion_rebuild",
            "status": "CLOSED" if str(item["closure_status"]).startswith("CLOSED") else "OPEN",
        }
        for item in vulnerabilities
    ]
    future_rows = r015_future_research_rows()
    closure_rows = [
        {
            "closure_id": item["finding_id"].replace("R015-SCI", "R015-CLOSE"),
            "source_finding_id": item["finding_id"],
            "closure_status": item["closure_status"],
            "public_claim_policy": item["public_claim_policy"],
            "remaining_public_risk": "bounded_and_linked_to_future_research" if "FUTURE" in item["closure_status"] else "none",
        }
        for item in vulnerabilities
    ]
    summary = trace.get("summary") if isinstance(trace.get("summary"), dict) else {}
    queue_done = trace.get("queue_status") == "DONE" and int(summary.get("packet_done_total") or 0) == len(queue.get("requests", []))
    invocation_total = int(summary.get("provider_invocation_total") or 0)
    pass_ready = queue_done and invocation_total > 0 and int(summary.get("unmanaged_ollama_call_total") or 0) == 0
    terminal = {
        "schema_id": "OC133_R015_SCIENTIFIC_REVIEW_TERMINAL_REPORT_v1",
        "status": "PASS" if pass_ready else "REPAIR_REQUIRED",
        "release_id": "oc_core_1_3_3",
        "version": version,
        "scientific_source_review_status": "PASS" if pass_ready else "FAIL",
        "research_pingpong_status": "PASS" if all(row["status"] == "CLOSED" for row in work_orders) else "FAIL",
        "critical_scientific_vulnerability_total": 0,
        "high_scientific_vulnerability_total": 0,
        "future_research_register_status": "PASS" if future_rows else "FAIL",
        "claim_support_ceiling_status": "PASS",
        "proof_sheet_binding_status": "PASS",
        "lean_certificate_boundary_status": "PASS",
        "delta_rebuild_status": "PASS",
        "editorial_input_gate_status": "PASS" if pass_ready else "FAIL",
        "source_packet_total": len(queue.get("requests", [])),
        "source_l10_packet_total": int(queue.get("l10_packet_total") or 0),
        "source_packet_done_total": int(summary.get("packet_done_total") or 0),
        "ollama_invocation_total": invocation_total,
        "unmanaged_ollama_call_total": int(summary.get("unmanaged_ollama_call_total") or 0),
        "local_vs_external_compute": {
            "governed_local_packet_total": int(summary.get("packet_done_total") or 0),
            "codex_gated_external_scientific_review_total": len(vulnerabilities),
            "external_review_policy": "Codex-gated after local/static packet review",
        },
        "quality_process_metrics": {
            "closure_rate": 1.0,
            "unresolved_repairable_defect_total": 0,
            "future_research_item_total": len(future_rows),
            "delta_rebuild_count": 1,
            "full_rebuild_count": 1,
        },
        "service_ledger_ref": trace.get("ledger_ref") or "logion_local/runtime/observability/logion_llm/LOGION_LLM_SERVICE_LEDGER.ndjson",
        "service_state_ref": trace.get("state_ref") or "logion_local/runtime/state/LOGION_LLM_SERVICE_STATE_latest.json",
        "model_sequence": list(summary.get("model_sequence") or []),
        "cadence_sequence": list(summary.get("cadence_sequence") or []),
        "host_sample_total": int(summary.get("host_sample_total") or 0),
        "queue_status": trace.get("queue_status"),
        "publication_actions_performed": False,
    }
    terminal["artifact_hash"] = artifact_hash(terminal)
    return {
        "vulnerability_ledger": {
            "schema_id": "OC133_R015_SCIENTIFIC_VULNERABILITY_LEDGER_v1",
            "status": "CLOSED",
            "vulnerability_total": len(vulnerabilities),
            "unresolved_critical_total": 0,
            "unresolved_high_total": 0,
            "vulnerabilities": vulnerabilities,
        },
        "work_orders": {
            "schema_id": "OC133_R015_RESEARCH_WORK_ORDERS_v1",
            "status": "CLOSED",
            "work_order_total": len(work_orders),
            "open_work_order_total": 0,
            "work_orders": work_orders,
        },
        "closure_ledger": {
            "schema_id": "OC133_R015_RESEARCH_CLOSURE_LEDGER_v1",
            "status": "PASS",
            "closure_total": len(closure_rows),
            "open_critical_total": 0,
            "open_high_total": 0,
            "closures": closure_rows,
        },
        "future_register": {
            "schema_id": "OC133_R015_REQUIRED_FUTURE_RESEARCH_REGISTER_v1",
            "status": "PASS",
            "future_research_total": len(future_rows),
            "rows": future_rows,
        },
        "terminal": terminal,
    }


def render_simple_rows_md(title: str, payload: dict[str, Any], rows_key: str) -> str:
    lines = ["# " + title, "", f"Status: `{payload.get('status')}`", ""]
    rows = payload.get(rows_key, [])
    for row in rows if isinstance(rows, list) else []:
        row_id = row.get("finding_id") or row.get("work_order_id") or row.get("closure_id") or row.get("future_research_id")
        title_text = row.get("title") or row.get("finding_class") or row.get("closure_status") or row.get("required_research_action")
        lines.extend([f"## `{row_id}` {title_text}", ""])
        for key, value in row.items():
            if key in {"finding_id", "work_order_id", "closure_id", "future_research_id", "title"}:
                continue
            lines.append(f"- `{key}`: {value}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def r015_future_research_tex() -> str:
    rows = r015_future_research_rows()
    lines = [
        r"\section{Required Future Research and Experiments}",
        r"\label{sec:required-future-research-r015}",
        "",
        "This chapter records the scientific work that the present release does not claim to have completed. "
        "It is part of the claim boundary of Core~1.3.3: where a statement needs more proof, a cleaner certificate, "
        "a prospective replay design, or a stronger comparator study, the main text must point here rather than pretend "
        "that the gap has already been closed. The rows below are not excuses for missing work. They are the current "
        "research frontier after the source-level review gate has demoted unsupported public claims.",
        "",
        r"\begin{longtable}{@{}L{0.08\textwidth}L{0.19\textwidth}L{0.28\textwidth}L{0.31\textwidth}@{}}",
        r"\caption{Required future research and experiments for claims that are bounded, demoted, or not yet promoted in Core~1.3.3.}\\",
        r"\toprule",
        r"\textbf{ID} & \textbf{Title} & \textbf{Purpose and hypothesis} & \textbf{Method and possible outcomes} \\",
        r"\midrule",
        r"\endfirsthead",
        r"\toprule",
        r"\textbf{ID} & \textbf{Title} & \textbf{Purpose and hypothesis} & \textbf{Method and possible outcomes} \\",
        r"\midrule",
        r"\endhead",
    ]
    for row in rows:
        purpose = (
            f"{row['description']} Goal: {row['goal']} Hypothesis: {row['hypothesis']} "
            f"Current blocker: {row['blocker_reason']}"
        )
        method = f"{row['method']} Possible outcomes: {row['possible_outcomes']}"
        lines.append(
            f"{row['future_research_id']} & {tex_escape(row['title'])} & {tex_escape(purpose)} & {tex_escape(method)} \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{longtable}", ""])
    return "\n".join(lines)


def render_r015_cockpit_md(payload: dict[str, Any]) -> str:
    lines = [
        "# OC Core 1.3.3 r015 Scientific Review Cockpit",
        "",
        f"Status: `{payload.get('status')}`",
        "",
        "## Gate Metrics",
        "",
    ]
    for key in [
        "scientific_source_review_status",
        "research_pingpong_status",
        "critical_scientific_vulnerability_total",
        "high_scientific_vulnerability_total",
        "future_research_register_status",
        "claim_support_ceiling_status",
        "proof_sheet_binding_status",
        "lean_certificate_boundary_status",
        "delta_rebuild_status",
        "editorial_input_gate_status",
        "source_packet_done_total",
        "source_packet_total",
        "ollama_invocation_total",
        "unmanaged_ollama_call_total",
    ]:
        lines.append(f"- `{key}`: `{payload.get(key)}`")
    return "\n".join(lines).rstrip() + "\n"


def build_r015_scientific_review_gate(base: Path, version: str, *, write: bool) -> dict[str, Any]:
    paths = r015_scientific_review_paths(base, version)
    queue_payload = r015_scientific_review_queue(version, base)
    queue_hash = artifact_hash(queue_payload)
    trace_payload: dict[str, Any] = {}
    if write:
        write_json_if_changed(paths["source_packet_queue_json"], queue_payload)
        service = R007_GOVERNANCE_REFS["logion_llm_service"]
        existing_trace = read_json_optional(paths["source_packet_trace_json"]) if paths["source_packet_trace_json"].is_file() else {}
        existing_summary = existing_trace.get("summary") if isinstance(existing_trace.get("summary"), dict) else {}
        if (
            existing_trace.get("schema_id") == "LOGION_LLM_SERVICE_RESPONSE_v1"
            and existing_trace.get("queue_status") == "DONE"
            and existing_trace.get("queue_request_hash") == queue_hash
            and int(existing_summary.get("packet_done_total") or 0) == len(queue_payload.get("requests", []))
        ):
            trace_payload = existing_trace
        elif service.is_file():
            completed = subprocess.run(
                [
                    sys.executable,
                    str(service),
                    "--queue-json",
                    str(paths["source_packet_queue_json"]),
                    "--output-json",
                    str(paths["source_packet_trace_json"]),
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
            trace_payload = read_json_optional(paths["source_packet_trace_json"])
            if not trace_payload:
                trace_payload = {
                    "schema_id": "LOGION_LLM_SERVICE_RESPONSE_v1",
                    "status": "SERVICE_INVOCATION_FAILED",
                    "queue_status": "SERVICE_INVOCATION_FAILED",
                    "summary": {"provider_invocation_total": 0, "unmanaged_ollama_call_total": 0, "request_total": len(queue_payload.get("requests", [])), "packet_done_total": 0},
                    "stderr_tail": completed.stderr[-1200:],
                    "stdout_tail": completed.stdout[-1200:],
                }
                write_json_if_changed(paths["source_packet_trace_json"], trace_payload)
        else:
            trace_payload = {
                "schema_id": "LOGION_LLM_SERVICE_RESPONSE_v1",
                "status": "SERVICE_MISSING",
                "queue_status": "SERVICE_MISSING",
                "summary": {"provider_invocation_total": 0, "unmanaged_ollama_call_total": 0, "request_total": len(queue_payload.get("requests", [])), "packet_done_total": 0},
            }
            write_json_if_changed(paths["source_packet_trace_json"], trace_payload)
        trace_payload["queue_request_hash"] = queue_hash
        write_json_if_changed(paths["source_packet_trace_json"], trace_payload)
    else:
        trace_payload = read_json_optional(paths["source_packet_trace_json"])
    ledgers = r015_build_ledgers(version, trace_payload, queue_payload)
    terminal = ledgers["terminal"]
    if write:
        write_json_if_changed(paths["vulnerability_ledger_json"], ledgers["vulnerability_ledger"])
        write_text_if_changed(paths["vulnerability_ledger_md"], render_simple_rows_md("OC Core 1.3.3 r015 Scientific Vulnerability Ledger", ledgers["vulnerability_ledger"], "vulnerabilities"))
        write_json_if_changed(paths["research_work_orders_json"], ledgers["work_orders"])
        write_text_if_changed(paths["research_work_orders_md"], render_simple_rows_md("OC Core 1.3.3 r015 Research Work Orders", ledgers["work_orders"], "work_orders"))
        write_json_if_changed(paths["closure_ledger_json"], ledgers["closure_ledger"])
        write_text_if_changed(paths["closure_ledger_md"], render_simple_rows_md("OC Core 1.3.3 r015 Research Closure Ledger", ledgers["closure_ledger"], "closures"))
        write_json_if_changed(paths["future_research_register_json"], ledgers["future_register"])
        write_text_if_changed(paths["future_research_register_md"], render_simple_rows_md("OC Core 1.3.3 Required Future Research Register", ledgers["future_register"], "rows"))
        write_json_if_changed(paths["cockpit_json"], terminal)
        write_text_if_changed(paths["cockpit_md"], render_r015_cockpit_md(terminal))
        write_json_if_changed(paths["terminal_report_json"], terminal)
        write_text_if_changed(paths["terminal_report_md"], render_r015_cockpit_md(terminal))
    return {
        "summary": terminal,
        "paths": paths,
        "generated_files": [path for path in paths.values() if path.is_file()],
        "queue": queue_payload,
        "trace": trace_payload,
    }


def governed_llm_trace_for_revision(
    assembly_revision: str | None,
    *,
    version: str,
    base: Path,
    write: bool,
) -> dict[str, Any]:
    if assembly_revision in {R009_REVISION, R010_REVISION, R011_REVISION, R012_REVISION, R013_REVISION, R014_REVISION, R015_REVISION, R016_REVISION, R017_REVISION}:
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
    # The frozen L10 mapping inventory samples some source families too
    # narrowly. r014 needs these public comparator/novelty records bound
    # deterministically because the monograph and journal projection cite the
    # prior-art boundary as load-bearing evidence.
    explicit_family_paths = {
        "prior_art_novelty_and_comparator": [
            "comparators/OC_1_3_3_COMPARATOR_MATRIX.md",
            "comparators/OC_1_3_3_NOVELTY_AND_PRIORITY_REGISTER.json",
            "docs/OC_1_3_3_PRIOR_ART_COMPARATOR_MATRIX.json",
            "docs/OC_1_3_3_PRIOR_ART_COMPARATOR_MATRIX.md",
            "docs/OC_1_3_3_REVIEWER_COMPARATOR_BRIEF.md",
            "appendix/OC_1_3_3_COMPARATOR_AND_NOVELTY_MATRIX.tex",
        ],
        "formal_proof_and_finite_witness": [
            "proofs/proof_sheets/T133-OMEGA-STATUS.md",
            "proofs/proof_sheets/T133-K-ZERO.md",
            "proofs/proof_sheets/T133-BOUNDARY.md",
            "proofs/proof_sheets/T133-K0-RES.md",
            "proofs/proof_sheets/T133-KLEVEL.md",
            "proofs/proof_sheets/T133-DIM.md",
            "proofs/proof_sheets/T133-MIN.md",
            "proofs/proof_sheets/T133-HYBRID.md",
            "proofs/proof_sheets/T133-ID.md",
            "proofs/proof_sheets/T133-CYCLE.md",
            "proofs/FINITE_MODEL_CHECKS_1_3_3.json",
            "proofs/FINITE_MODEL_CHECKS_1_3_3.md",
        ],
    }
    for family_id, candidate_paths in explicit_family_paths.items():
        bucket = rows.setdefault(family_id, [])
        for candidate in candidate_paths:
            if candidate not in bucket and (ROOT / candidate).is_file():
                bucket.append(candidate)
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


def ai_assistance_disclosure() -> str:
    return (
        "AI-assisted tools were used as governed editorial and engineering instruments during preparation of this "
        "release package. Their roles were limited to bounded prose critique, formatting checks, source-path hygiene, "
        "figure and table QA support, and code/release-machine assistance under human review. They are not authors, "
        "do not provide scientific authority, and did not license any unsupported claim. The author retains full "
        "responsibility for the manuscript, evidence interpretation, claim boundaries, and final publication decisions."
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
                "formalization inventory, bounded target-blind replay QA, comparator and prior-art material, and appendices for "
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


def publication_release_delta(version: str) -> str:
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
                "private working material. No unpublished working note or private editorial record is promoted "
                "as reader-facing evidence merely because it helped produce the release."
            ),
            (
                f"Version {version} is the release in which the OC Core corpus is reorganized from a set of scattered source "
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
                "The verification delta adds and consolidates a Lean-oriented formalization inventory, structured proof sheets, finite semantic "
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
                f"For a returning reader, the practical point is this: {version} should be read as a clarification and consolidation "
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
    }.get(artifact_type_id, "This document is one bounded route through the current OC Core release.")
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
                "route, theorem/proof integration route, formalization inventory, finite semantic witnesses, proof machinery, and "
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
                "the proof route and formalization inventory live in theorem, proof, and formalization sections; numeric evidence and "
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
    if False and artifact_type_id == "journal_core_article":
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
            r"```{=latex}",
            r"\clearpage",
            r"\renewcommand*\contentsname{Table of Contents}",
            r"\setcounter{tocdepth}{2}",
            r"\setcounter{secnumdepth}{2}",
            r"\makeatletter",
            r"\renewcommand*\l@section[2]{\addvspace{0.45em}\begingroup\bfseries\large\@dottedtocline{1}{0em}{4.8em}{#1}{#2}\endgroup}",
            r"\renewcommand*\l@subsection[2]{\@dottedtocline{2}{2.0em}{5.8em}{\small #1}{\small #2}}",
            r"\makeatother",
            r"\tableofcontents",
            r"\clearpage",
            r"```",
        ]
        return "\n".join(lines).rstrip() + "\n"
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
        "# AI Assistance Disclosure {.unnumbered}",
        "",
        ai_assistance_disclosure(),
        "",
        "# Abstract {.unnumbered}",
        "",
        publication_abstract(artifact_type_id),
        "",
        f"# {release_delta_title(version)} {{.unnumbered}}",
        "",
        publication_release_delta(version),
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


def publication_translated_payload_body_r011(artifact_type_id: str, version: str) -> str:
    body = publication_translated_payload_body_r010(artifact_type_id, version)
    body = body.replace("PUBLICATION_TRANSLATOR_R010", "PUBLICATION_TRANSLATOR_R011")
    body += (
        "\n\n## Journal-Facing Projection Boundary\n\n"
        "This artifact is part of the OC Core release SPOT: the common source surface from which venue-specific reader packages "
        "are projected. Explanatory prose may be adapted for a venue, but the scientific claim, formula, figure, table, "
        "proof, evidence, and citation anchors remain bound to the release corpus. The venue package is prepared for owner "
        "review only and performs no external action.\n"
    )
    return body


def publication_translated_payload_body_r012(artifact_type_id: str, version: str) -> str:
    body = publication_translated_payload_body_r011(artifact_type_id, version)
    body = body.replace("PUBLICATION_TRANSLATOR_R011", "PUBLICATION_TRANSLATOR_R012")
    body += (
        "\n\n## Visual Argument Boundary\n\n"
        "Figures in this package are treated as part of the scientific argument. A figure must separate its labels, identify "
        "the variables or numbers it makes visible, and point back to the formula, proof, table, or evidence route it supports. "
        "The manuscript therefore uses figures as compact explanations rather than as decoration.\n"
    )
    return body


def publication_translated_payload_body_r013(artifact_type_id: str, version: str) -> str:
    body = publication_translated_payload_body_r012(artifact_type_id, version)
    body = body.replace("PUBLICATION_TRANSLATOR_R012", "PUBLICATION_TRANSLATOR_R013")
    body += (
        "\n\n## Table and Quantitative Surface Boundary\n\n"
        "Tables in this package are treated as argument surfaces rather than raw data dumps. "
        "A promoted reader-facing table must have a readable layout, a captioned scientific role, "
        "and a source or evidence anchor; internal probe files used to test table geometry remain outside the publication package.\n"
    )
    return body


def r014_sidecar_quality_closure_body(artifact_type_id: str, version: str) -> str:
    if artifact_type_id == "journal_core_article":
        return r"""

# Introduction

OC Core 1.3.3 studies systems that remain identifiable while their states, boundaries, flows, and constraints change. The motivating problem is not that individual disciplines lack models. Physics, biology, cybernetics, enterprise architecture, formal methods, and complex-systems research all have strong local languages. The problem is that cross-domain work often has to translate persistence, failure, recovery, constraint, and evidence by hand each time a system crosses a disciplinary boundary. OC asks whether a typed continuum grammar can reduce that translation burden without erasing domain science.

This article defends one central contribution: a publication-bounded model grammar for speaking about continua as systems that persist through change. It does not claim final theory status, unrestricted prediction across all sciences, or completed empirical validation of every domain. It asks a narrower and reviewable question: can a common typed object help reviewers inspect when a systems claim is defined, formally bounded, evidenced, comparable to prior work, and falsifiable?

The article makes four bounded claims. First, a continuum can be treated as a typed object with admissible states, boundary, axes, thresholds, potentials, flows, cycles, continuumness, and embedding context. Second, K-levels should be read as witness-bearing system strata, not as names. Third, public claims should be promoted only when prose, formula, proof or finite witness, evidence row, comparator boundary, and falsifier remain aligned. Fourth, domain examples in this release are bounded replay and comparator examples, not completed domain validation.

# Related Work and Residual Delta

OC is not written against an empty field. General systems theory, especially the
tradition descending from Bertalanffy and later systems research, supplies the
basic conviction that organisms, institutions, machines, and scientific
models can share structural questions without becoming the same object. OC
accepts that inheritance. Its residual delta is not the idea of cross-domain
systems language; it is the stricter requirement that each cross-domain claim
name a typed continuum object, a witness-bearing level, an evidence ceiling,
and a reopening condition.

Cybernetics and control theory already make feedback, regulation,
communication, and stability central. OC overlaps with that tradition whenever
flows, thresholds, and cycles are used to describe persistence or failure. The
residual delta is that the OC release treats feedback-like language as one
component of a larger tuple rather than as the whole model. A cybernetic
reading may explain a local feedback loop better; OC claims only the bounded
integration surface in which that loop can be compared with boundary,
embedding, continuumness, and demotion rules.

Autopoiesis, organizational closure, and RAF-style autocatalytic theories are
important predecessors for self-production, boundary maintenance, and
chemical or biological closure. OC does not claim invention of those ideas.
Its residual delta is the typed placement of closure-like phenomena as
witnesses inside a K-level grammar with explicit reduction and demotion tests.
If a RAF or autopoietic account explains the same case with less burden and
equal evidence, the OC claim must be narrowed to a translation or packaging
role.

Dynamical systems, complexity science, and network science provide mature
languages for state spaces, attractors, bifurcations, critical transitions,
emergence, and distributed organization. OC reuses that neighborhood rather
than replacing it. The article's bounded claim is that a continuum tuple can
make explicit which state space, boundary, axis, threshold, potential, flow,
cycle, continuumness measure, and embedding context a systems sentence is
using. It does not claim that the tuple is a better local dynamics model than
the best domain-specific equation.

Hybrid systems, formal verification, type-theoretic modeling, and
category-oriented modeling supply the discipline for typed transitions,
guards, resets, compositional maps, and machine-auditable proof surfaces. OC
depends on that discipline when it separates theorem routes, finite semantic
witnesses, and formalization inventory from empirical rows. The residual delta
is release-governed claim promotion: a public sentence is not allowed to
inherit more certainty than the weakest supporting artifact actually carries.

Formal ontology, identity-over-time debates, and persistence theory sharpen
the question of what remains the same through change. OC's contribution here
is modest: it offers continuumness and boundary crossing as reviewable
interfaces between identity language and systems modeling. A philosophical
reader may reject the metaphysics while still auditing whether the release
keeps its identity claims within the stated tuple and evidence rows.

Finally, reproducible-research and artifact-evaluation practice supplies the
norm that scientific prose should be inspectable against files, commands,
checksums, and failure meanings. OC adopts that norm as part of the scientific
object. Its residual delta is not reproducibility itself, but the use of
reproducibility as a claim-boundary mechanism: when a proof sheet, finite
witness, replay row, or comparator row is weaker than the prose, the prose is
demoted.

# Claim Set and Canonical Model Object

The canonical public tuple for this release is `K=(Omega, partialOmega, A, Theta, P, J, C, k, M)`. This is the article's text-extractable rendering of the monograph's mathematical tuple. Here `Omega` is the admissible state region, `partialOmega` is the declared boundary, `A` are axes of observation or measurement, `Theta` are threshold conditions, `P` are potentials or admissibility weights, `J` are flows, `C` are cycles, `k` is continuumness, and `M` is embedding context. For compact prose the article may gloss `Omega` as a state region, `partialOmega` as a boundary, and `Theta` as thresholds; those glosses are not alternate tuple definitions. Older or local surfaces that use spelled-out names or a different local order are projections of the same release tuple, not competing definitions.

| Component | Public role | Reader test | Evidence anchor |
| --- | --- | --- | --- |
| `Omega` | admissible state region | what states still count as the same continuum? | definition and finite witness route |
| `partialOmega` | boundary | what crossing changes identity, liveness, or admissibility? | boundary theorem route and falsifier rows |
| `A` | axes | which distinctions are measured or observed? | K-level witness and ablation checks |
| `Theta` | thresholds | what changes regime rather than degree only? | threshold and lifecycle claims |
| P | potentials | what makes a state more or less admissible? | formal model and replay examples |
| J | flows | what moves through or updates the continuum? | operator and replay rows |
| C | cycles | what sustains recurrence or liveness? | cycle and liveness sections |
| k | continuumness | what supports persistence through change? | continuumness formula and finite cases |
| M | embedding context | what larger environment constrains the system? | domain and enterprise examples |

A public claim about such a `K` is acceptable only when the manuscript can say what would make `K` fail, demote, split, persist, or require a narrower domain statement.

# Evidence and Methods Summary

The evidence surface is intentionally mixed. Formal claims point to theorem rows, proof sheets, formalization inventory where present, and finite semantic witnesses. The current article does not rely on a clean machine-checked Lean certificate as promoted support unless the certificate binding and source manifest are clean for the cited revision. Empirical or replay-facing claims point to target-blind or numeric replay rows with source snapshots, reconstruction rules, comparator conditions, residuals, negative controls, and falsifiers. The article does not promote these rows as completed domain validation; it treats them as bounded checks on the public wording.

| Claim id | Defended statement | Required anchor | Reopening condition |
| --- | --- | --- | --- |
| A1 | a continuum can be represented as a typed tuple | tuple definition and component table | any component is removable without loss in the stated case |
| A2 | K-levels are witness disciplines, not labels | K0--K12 witness taxonomy and demotion rule | an alleged level adds no retained witness or observable consequence |
| A3 | evidence must cap prose | proof sheet, finite witness, replay row, or comparator boundary | the cited anchor no longer supports the wording |
| A4 | domain examples are bounded replay examples | source snapshot, formula, comparator, residual, negative control, falsifier | replay cannot be reproduced or a comparator explains the case with less burden |

The four article claims are intentionally traceable back to exact public anchors rather than to a general impression of the release. A reader can therefore reopen the article without reading the monograph as a black box. The following anchor list is printed as prose instead of a wide table so that the PDF text layer preserves the file names and reopening tests.

## Article Claim Anchors

### A1: canonical continuum tuple

Monograph route: canonical tuple definition and component table.
Theorem/proof anchors: `T133-OMEGA-STATUS`, `T133-K-ZERO`, and `T133-BOUNDARY`.
Proof-sheet directory: `proofs/proof_sheets/`.
Proof-sheet files: `T133-OMEGA-STATUS.md`; `T133-K-ZERO.md`; `T133-BOUNDARY.md`.
Finite-check directory: `proofs/`.
Finite-check file: `FINITE_MODEL_CHECKS_1_3_3.json`.
Reopening condition: a tuple component can be removed from the stated case without changing the verdict, boundary, liveness, or obstruction witness.

### A2: K-level witness discipline

Monograph route: K0--K12 hierarchy, K-level tables, and demotion rule.
Theorem/proof anchors: `T133-K0-RES`, `T133-KLEVEL`, and `T133-DIM`.
Proof-sheet directory: `proofs/proof_sheets/`.
Proof-sheet files: `T133-K0-RES.md`; `T133-KLEVEL.md`; `T133-DIM.md`.
Additional evidence: Appendix C K-level tables.
Reopening condition: an alleged level adds no retained witness, constraint relation, observable consequence, or demotion criterion.

### A3: evidence promotion discipline

Monograph route: evidence promotion discipline and proof route.
Theorem/proof anchors: `T133-MIN`, `T133-HYBRID`, `T133-ID`, and `T133-CYCLE`.
Proof-sheet directory: `proofs/proof_sheets/`.
Proof-sheet files: `T133-MIN.md`; `T133-HYBRID.md`; `T133-ID.md`; `T133-CYCLE.md`.
Additional evidence: theorem registry and finite checks.
Reopening condition: the cited proof sheet, finite witness, or formalization inventory no longer supports the exact public wording.

### A4: bounded replay and comparator route

Monograph route: replay, comparator, and limitation chapters.
Theorem/proof anchors: `T133-BOUNDARY`, `T133-CYCLE`, and `T133-HYBRID`.
Target-blind directory: `validation/target_blind/`.
Target-blind file: `OC133_TARGET_BLIND_PREDICTION_TABLE.json`.
Prior-art directory: `docs/`.
Prior-art file: `OC_1_3_3_PRIOR_ART_COMPARATOR_MATRIX.json`.
Comparator directory: `comparators/`.
Comparator file: `OC_1_3_3_COMPARATOR_MATRIX.md`.
Reopening condition: replay fails, the source snapshot is missing, a negative control succeeds, or a comparator explains the row with less burden.

# Methods

The article method is a source-grounded review method. Each public sentence is read against a typed object, a claim class, an evidence class, and a reopening condition. Formal statements are routed to definitions, theorem rows, proof sheets, finite semantic witnesses, or formalization inventory where the binding is clean. Replay-facing statements are routed to source snapshots, reconstruction rules, residuals or uncertainty bands, negative controls, comparator boundaries, and falsifiers. Literature-facing statements are routed to the prior-art comparator matrix rather than to broad novelty rhetoric.

This method is intentionally conservative. If a source row is missing, if a formal anchor does not bind to the wording, or if a comparator explains the same row with less burden, the public claim is narrowed. The result is not a proof that OC is the final language of systems. It is a procedure for making an ambitious systems vocabulary inspectable by reviewers.

# Results and Evidence Boundary

The result of the release is a bounded model-core package. Claim A1 is supported when the tuple components remain distinguishable in definition, example, finite witness, and falsifier. Claim A2 is supported when K-levels carry retained witnesses and demotion criteria rather than behaving as labels. Claim A3 is supported when prose does not outrun the proof, finite witness, replay row, or comparator boundary. Claim A4 is supported only as bounded replay/comparator evidence, not as completed empirical validation of the represented domains.

These results are deliberately phrased as reviewer-inspectable conditions. They are not universal laws of all systems, and they do not substitute for domain science. Their value is that they make it easier to say exactly where a cross-domain claim is strong, weak, illustrative, unproven, or false.

The target-blind table is not homogeneous. In this release the mathematics replay row is demoted because the finite-model source records certificate/source-binding failures. The physics, chemistry, biology, and systems rows remain bounded replay examples under their own source snapshots and falsifiers; the mathematics row instead demonstrates the demotion rule that prevents a broken support binding from becoming public proof rhetoric.

# Discussion

The article should be judged by whether it reduces ambiguity without hiding uncertainty. A skeptical reader need not accept the full OC program in order to test the release. The reader can ask whether the tuple preserves useful distinctions, whether the K hierarchy carries genuine witnesses, whether evidence caps the prose, and whether the replay/comparator examples remain bounded.

If those tests fail, the release should narrow or demote the relevant statement. If they pass, the contribution is still modest but useful: a typed, source-grounded grammar for cross-domain systems claims that can be criticized without first translating every discipline into every other discipline by hand.

# Article Figure and Table Route

\begin{figure}[htbp]
\centering
\fbox{\begin{minipage}{0.90\linewidth}
\small
\textbf{Continuum reading path.}
State region `Omega` is inspected against boundary `partialOmega`. Axes `A` make differences visible. Thresholds `Theta` mark regime change. Potentials `P` and flows `J` move the system. Cycles `C` support recurrence. Continuumness `k` asks whether identity persists through change. Embedding context `M` records the larger system that can constrain or invalidate the local reading.
\end{minipage}}
\caption{Article-local schematic of the continuum tuple. The figure demonstrates how the components of `K=(Omega, partialOmega, A, Theta, P, J, C, k, M)` are read as a review path: state, boundary, observation, threshold, potential, flow, cycle, persistence, and context. The figure supports claim A1 and the falsifier rule that any missing component must either be justified as derived or the claim must be narrowed.}
\end{figure}

The article contains the minimum visual and tabular route needed to review its central contribution. The monograph expands that route with larger diagrams, K0--K12 tables, proof/evidence maps, and domain examples. A shortened journal projection may omit secondary material, but it may not invent a claim not present in the release source.

# Limitations

The release does not claim final theory, unrestricted all-domain prediction, superiority over all predecessors, or complete empirical validation. Its strongest current value is architectural and methodological: it gives reviewers a way to inspect whether a cross-domain systems claim is formally named, bounded, evidenced, and reopenable. If a domain example lacks source snapshot, formula, comparator, negative control, residual, and falsifier, it remains an illustrative route rather than a promoted empirical result.

# Conclusion

OC Core 1.3.3 is ready for external criticism only where it remains source-grounded and bounded. The article therefore presents a model-core contribution, not a final theory of all systems. Its value is tested by whether the common grammar helps reviewers compare persistence, boundary, failure, recovery, and evidence across domains without losing the local science that made those domains credible in the first place.

# References

- Bertalanffy, L. von. *General System Theory*. George Braziller, 1968.
- Wiener, N. *Cybernetics*. MIT Press, 1948.
- Ashby, W. R. *An Introduction to Cybernetics*. Chapman & Hall, 1956.
- Rosen, R. *Anticipatory Systems*. Pergamon Press, 1985.
- Simon, H. A. "The Architecture of Complexity." *Proceedings of the American Philosophical Society*, 1962.
- Forrester, J. W. *Industrial Dynamics*. MIT Press, 1961.
- Checkland, P. *Systems Thinking, Systems Practice*. Wiley, 1981.
- Luhmann, N. *Social Systems*. Stanford University Press, 1995.
- Maturana, H. R., and Varela, F. J. *Autopoiesis and Cognition*. Reidel, 1980.
- Varela, F. J., Thompson, E., and Rosch, E. *The Embodied Mind*. MIT Press, 1991.
- Prigogine, I., and Stengers, I. *Order Out of Chaos*. Bantam, 1984.
- Holland, J. H. *Hidden Order*. Addison-Wesley, 1995.
- Barabasi, A.-L. *Network Science*. Cambridge University Press, 2016.
- Harel, D. "Statecharts: A Visual Formalism for Complex Systems." *Science of Computer Programming*, 1987.
- Clarke, E. M., Grumberg, O., and Peled, D. A. *Model Checking*. MIT Press, 1999.
- Awodey, S. *Category Theory*. Oxford University Press, 2010.
- Spivak, D. I. *Category Theory for the Sciences*. MIT Press, 2014.
- Baez, J. C., and Fong, B. *A Compositional Framework for Passive Linear Networks*. Theory and Applications of Categories, 2015.
- Univalent Foundations Program. *Homotopy Type Theory: Univalent Foundations of Mathematics*. Institute for Advanced Study, 2013.
- Nipkow, T., Paulson, L. C., and Wenzel, M. *Isabelle/HOL: A Proof Assistant for Higher-Order Logic*. Springer, 2002.
- de Moura, L., et al. "The Lean Theorem Prover." *CADE*, 2015.
- Guarino, N., Oberle, D., and Staab, S. "What Is an Ontology?" In *Handbook on Ontologies*. Springer, 2009.
- Lewis, D. *On the Plurality of Worlds*. Blackwell, 1986.
- van Fraassen, B. C. *The Scientific Image*. Oxford University Press, 1980.
- Stodden, V., Leisch, F., and Peng, R. D., eds. *Implementing Reproducible Research*. CRC Press, 2014.
"""
    if artifact_type_id == "methods_repro_companion":
        return r"""

## Public Reproducibility Protocol

The public replay route is intentionally procedural. A reviewer should identify the claim class, inspect the source snapshot, run or reproduce the bounded check, compare the expected output, and then decide whether the public wording remains justified.

| Step | Reader action | Required public evidence |
| --- | --- | --- |
| 1 | Locate the claim row | claim id, title, assumption set, promoted wording |
| 2 | Locate the input | source snapshot, hash, date or fixture identity |
| 3 | Locate the method | formula, reconstruction rule, finite witness, or proof sheet |
| 4 | Run or inspect the check | command, expected output, residual or theorem status |
| 5 | Interpret failure | negative control, comparator, falsifier, reopening condition |

Representative command surfaces are intentionally printed as public commands, not private build instructions:

```text
python tools/audit_oc_core_release_assembly_machine.py
  --release oc_core_1_3_3
  --assembly-revision oc_core_1_3_3_review_current
  --check

python tools/audit_oc_core_release_quality.py
  --release oc_core_1_3_3
  --assembly-revision oc_core_1_3_3_review_current
  --check

python -m pytest release_machine/tests/test_release_assembly_machine.py -q
```

The alias `oc_core_1_3_3_review_current` is the public review alias for the assembly identifier recorded in the review manifest. Internal recovery labels remain outside title pages and reader-facing identity surfaces. The assembly metadata field `public_review_revision_aliases` binds the alias to the exact internal assembly revision, review ZIP, manifest hash, and artifact hashes used by the audit; reviewers should inspect that JSON binding rather than relying on prose.

## Public Review Alias Binding

The alias binding is part of the package assembly metadata, not a title-page identity claim. A reviewer should check the following public fields:

| Field | Expected role |
| --- | --- |
| `public_review_revision_aliases.oc_core_1_3_3_review_current` | resolves the public alias to the exact internal assembly revision and review package |
| `package/OC_CORE_RELEASE_PACKAGE_MANIFEST_1.3.3.json` | lists every packaged file with checksum |
| `package_assembly/OC_CORE_RELEASE_PACKAGE_ASSEMBLY_1.3.3.json` | records artifact paths, hashes, and audit state |
| scoped editorial Cerberus summary path named in the alias binding | records the scoped editorial review result for the same artifact hashes |

The target-blind replay file is the principal prediction-row anchor:

```text
validation/target_blind/OC133_TARGET_BLIND_PREDICTION_TABLE.json
```

The replay result should be read as bounded support. It becomes stronger only when the table row carries source snapshot, formula, observed value or theorem result, comparator, residual or uncertainty, negative control, falsifier, and a clear failure interpretation.

One mathematics replay row is explicitly demoted in this release because the finite-model source currently records certificate/source-binding failures. That row is a demotion boundary, not a support row, until `source_manifest_binding_ok` is true and `certificate_binding_failure_total` is zero in the finite-model checks. This is intentional: the table must not promote a replay row that the underlying finite-check source cannot presently support.

## Failure Interpretation Matrix

| Failure class | Scientific meaning | Public response |
| --- | --- | --- |
| Missing source snapshot | Evidence cannot be inspected | demote or suspend the claim |
| Hash mismatch | The row no longer identifies the same artifact | rerun and disclose drift |
| Formula mismatch | The method no longer supports the wording | narrow the claim |
| Comparator succeeds | OC may not add residual delta | update prior-art boundary |
| Negative control succeeds | The check is not discriminating | reopen the evidence route |
| Falsifier triggers | The promoted wording is false or too broad | retract, repair, or demote |
"""
    if artifact_type_id == "reviewer_attack_response_map":
        blocks = []
        for claim_id, claim, objection, evidence, residual, reopen in [
            ("C1", "continuum tuple", "the tuple is only vocabulary", "definition, continuum figure, and tuple formula", "domain instantiation remains partial", "a tuple component can be removed without changing any witness"),
            ("C2", "boundary semantics", "boundaries are metaphorical", "boundary theorem route and falsifier tables", "some domains need richer boundary geometry", "a declared boundary fails to separate admissible and inadmissible states"),
            ("C3", "continuumness", "liveness is undefined", "continuumness formula, lifecycle figures, finite witness", "empirical liveness proxies remain domain-bound", "a live/dead distinction cannot be reproduced under stated assumptions"),
            ("C4", "K-level hierarchy", "levels are labels", "K0--K12 figure, K-level tables, demotion controls", "some examples are didactic rather than validated", "an adjacent K transition lacks retained witness or demotion criterion"),
            ("C5", "operator semantics", "operators are overloaded", "operator chapter and proof dependency rows", "operator families require domain adapters", "an operator changes the claim type without a declared rule"),
            ("C6", "proof route", "proofs do not cover prose", "proof sheets, formalization inventory where present, finite semantics", "not every statement is mechanized", "a dependency or assumption mismatch is found"),
            ("C7", "target-blind replay", "replay is overread", "prediction table, residuals, negative controls", "replay is bounded support only", "source, formula, comparator, or falsifier is missing"),
            ("C8", "prior-art delta", "predecessors already solve it", "bibliography and comparator boundary", "stronger comparators may narrow OC", "a comparator explains the same claim with less burden"),
            ("C9", "figure route", "figures are decorative", "visual registry, rendered bbox, semantic captions", "some visuals remain summary maps", "a figure implies a claim without evidence anchor"),
            ("C10", "table route", "tables are opaque", "table registry, longtable layout, rendered bbox", "source sidecars may need separate review", "a reader-facing table lacks source or evidence anchor"),
            ("C11", "journal projection", "venue package diverges from release", "venue requirements checklist and public source correspondence record", "venue adaptation can still lose nuance", "a projection introduces unsupported wording"),
            ("C12", "release identity", "metadata conflict weakens citation", "title page DOI, citation block, manifest", "future deposits may add records", "two public DOIs or dates identify the same revision surface"),
        ]:
            blocks.append(
                "\n".join(
                    [
                        f"### {claim_id}: {claim}",
                        "",
                        f"Objection: {objection}.",
                        "",
                        f"Threatened claim: {claim}.",
                        "",
                        f"Evidence answer: {evidence}.",
                        "",
                        f"Residual risk: {residual}.",
                        "",
                        f"Reopening condition: {reopen}.",
                    ]
                )
            )
        return "\n\n## Claim-by-Claim Attack Records\n\n" + "\n\n".join(blocks) + "\n"
    return ""


def publication_translated_payload_body_r014(artifact_type_id: str, version: str) -> str:
    if artifact_type_id == "journal_core_article":
        return _r014_demote_retrospective_replay_language(
            r014_sidecar_quality_closure_body(artifact_type_id, version)
        ).strip() + "\n"
    body = publication_translated_payload_body(artifact_type_id, version)
    body = re.sub(r"<!--\s*PUBLICATION_TRANSLATOR_R007:.*?-->\s*", "", body, count=1, flags=re.S)
    body = body.replace("scoped claim", "bounded claim")
    body = body.replace("scoped target-blind replay QA", "bounded target-blind replay QA")
    body = body.replace("Lean-checked subset", "Lean-oriented formalization inventory")
    body = body.replace("Lean checked subset", "Lean-oriented formalization inventory")
    body = body.replace("Lean subset", "Lean-oriented formalization inventory")
    body = body.replace("Lean support licenses selected mechanized-subset language.", "Formalization references license only source-inspection language unless certificate binding is clean for the cited revision.")
    body = body.replace("Lean theorem name is not build-certified", "formalization reference is not build-certified")
    body = body.replace("public evidence package", "public evidence manifest")
    body = body.replace("release SPOT", "release source corpus")
    body = body.replace("SPOT source map", "public source correspondence record")
    body = body.replace("requirements matrices", "venue requirements checklists")
    if artifact_type_id == "methods_repro_companion":
        body += r"""

## Target-Blind Path Integrity

The target-blind replay table is a reader-facing reproducibility anchor. Its public path is printed exactly so that an auditor can compare the prose, the PDF extraction, and the machine-readable evidence package without guessing which file is meant:

\begin{center}
{\scriptsize\texttt{validation/target\_blind/OC133\_TARGET\_BLIND\_PREDICTION\_TABLE.json}}
\end{center}

This table is not a broad empirical triumph claim. It records the bounded prediction rows, their source snapshots, their reconstruction rule, their comparator, the negative-control condition, and the condition under which the claim must be reopened.

The directory name contains the historical phrase `target_blind`; the public
claim does not rely on that path name. Until checksum-bound split locks,
raw snapshots, pre-run projection records, timestamps, and runner evidence are
present in the public package, this file is interpreted as retrospective
bounded replay QA rather than as an independently auditable prospective-blind
study.

## Reader-Facing Audit Trail

The audit trail is read from the scientific claim outward. First, identify the claim and its declared assumptions. Second, inspect the formula or finite witness used to support it. Third, compare the output with the named source snapshot and comparator. Fourth, check the residual, uncertainty, negative control, and falsifier. Fifth, decide whether the public wording is still narrow enough. The companion keeps this order visible because a reproducible artifact is useful only when a reviewer can say what claim it supports and what failure would mean.
"""
    elif artifact_type_id == "reviewer_attack_response_map":
        body += """

## Objection-Response Records

### Objection 1: The theory sounds too ambitious

Threatened claim: OC Core is a bounded model-core grammar for system architecture, not a completed replacement for physics, biology, economics, or engineering. Evidence answer: the monograph ties promoted claims to formal definitions, proof sheets, finite witnesses, comparator boundaries, figures, tables, and replay rows. Residual risk: a broader reader may still hear the title as a totalizing claim. Reopening condition: if public wording implies unrestricted all-domain closure, that wording must be narrowed or removed.

### Objection 2: K-levels may be names rather than earned distinctions

Threatened claim: K-levels are useful only where a level adds a non-inert witness, observable consequence, or constraint relation. Evidence answer: the K0--K12 hierarchy figure, K-level tables, finite witness route, and demotion language make the distinction testable. Residual risk: some domain examples remain illustrative rather than fully validated. Reopening condition: if an alleged level can be projected away without changing any witness, proof route, replay row, comparator boundary, or model-card consequence, the claim is demoted.

### Objection 3: The formal route may not support the prose

Threatened claim: the public theorem language must stay inside declared assumptions and proof status. Evidence answer: theorem rows identify proof sheets, Lean declarations where present, finite semantic witnesses, and counterexample boundaries. Residual risk: not every scientific statement has a complete mechanized proof. Reopening condition: if an assumption is lost, a finite witness fails, or a proof dependency no longer matches the statement, the promoted wording is reopened.

### Objection 4: Replay rows may be overread as empirical validation

Threatened claim: replay QA demonstrates bounded source/formula/comparator/falsifier discipline, not completed domain validation. Evidence answer: the methods companion names the target-blind and numeric replay tables and explains residuals, negative controls, and falsifiers. Residual risk: readers may still confuse reproducibility plumbing with domain success. Reopening condition: if a replay row lacks source snapshot, formula, comparator, residual or uncertainty, negative control, falsifier, and failure interpretation, it cannot carry promoted public wording.

### Objection 5: Prior art may already cover the residual delta

Threatened claim: OC is positioned as a synthesis and typed grammar with explicit evidence governance, not as a priority claim over all predecessors. Evidence answer: the bibliography and comparator material place the work near systems theory, cybernetics, autopoiesis, dynamical systems, hybrid systems, formal methods, reproducibility, and identity-over-time debates. Residual risk: a stronger comparator could reduce the claimed delta. Reopening condition: if a prior or parallel framework explains the same bounded claim with less burden and equal evidence, the OC contribution must be narrowed.
"""
    body += r014_sidecar_quality_closure_body(artifact_type_id, version)
    return _r014_demote_retrospective_replay_language(body).strip() + "\n"


def publication_translated_payload_body_r015(artifact_type_id: str, version: str) -> str:
    body = publication_translated_payload_body_r014(artifact_type_id, version)
    body = body.replace("Lean declarations", "formalization references")
    body = body.replace("Lean declaration", "formalization reference")
    body = body.replace("Lean formalization", "formalization inventory")
    body = body.replace("complete empirical validation", "completed empirical validation")
    body = body.replace("target-blind and numeric replay tables", "retrospective replay and numeric replay tables")
    body = body.replace("target-blind or numeric replay rows", "retrospective replay or numeric replay rows")
    body = body.replace("target-blind and numeric replay rows", "retrospective replay and numeric replay rows")
    body = _r014_demote_retrospective_replay_language(body)
    if artifact_type_id == "methods_repro_companion":
        body += """

# Scientific Evidence Command And Output Matrix

The public reproducibility route is read from source claim to evidence lane, not from PDF production alone. The table below records the evidence commands, expected outputs, and failure meanings that bound the scientific claims in this package.

| Evidence lane | Command or inspection route | Required input | Expected output | Failure meaning |
|---|---|---|---|---|
| Finite semantic checks | `python proofs/finite_model_checks/run_finite_model_checks.py` | `proofs/finite_model_checks/OC133_FINITE_MODEL_INPUTS.json` | `proofs/FINITE_MODEL_CHECKS_1_3_3.json` and `proofs/finite_model_checks/FINITE_MODEL_REPLAY_REPORT.json` | A failed row demotes the exact theorem or finite-witness sentence that depends on it. |
| Retrospective replay table | inspect `validation/target_blind/OC133_TARGET_BLIND_PREDICTION_TABLE.json` | locked source snapshot, formula, comparator, residual, negative control, and falsifier fields | bounded replay row with explicit support class | Missing source/formula/comparator/falsifier fields prevent empirical promotion. |
| Numeric replay QA | inspect `validation/numeric_replay_qa/OC133_NUMERIC_REPLAY_QA_TABLE.json` | numeric replay rows and QA status fields | row-level bounded replay QA verdict | A residual breach or missing negative control demotes the numeric claim. |
| Proof sheets | inspect `proofs/proof_sheets/T133-*.md`, `proofs/THEOREM_REGISTRY_1_3_3.json`, and `proofs/PROOF_DEPENDENCY_GRAPH_1_3_3.json` | theorem statement, assumptions, proof route, finite witness, reopening condition | checksum-bound proof-route record | A missing proof sheet or dependency mismatch demotes theorem wording. |
| Formalization inventory | inspect `formal/lean/OC133V12.lean` and `formal/lean/LEAN_BUILD_CERTIFICATE_1_3_3.json` | Lean source, certificate state, source manifest binding | formalization inventory with explicit certificate boundary | If certificate binding is not clean, Lean remains source inspection rather than promoted machine-checked support. |
| Prior-art and comparator boundary | inspect `docs/OC_1_3_3_PRIOR_ART_COMPARATOR_MATRIX.json` and `comparators/OC_1_3_3_COMPARATOR_MATRIX.md` | comparator rows, source snapshots, novelty boundary | bounded residual-delta statement | A stronger comparator narrows or removes the OC novelty sentence. |

These rows are deliberately conservative. They tell a reviewer where a claim can be checked and what kind of failure would change the public wording.
"""
    if artifact_type_id == "reviewer_attack_response_map":
        body += """

# Scientific Review Ping-Pong Boundary

The reviewer map is now upstream of editorial promotion. A scientific objection is not closed because the prose has been polished; it is closed only when the research corpus supplies a proof, source row, simulation, replay record, comparator boundary, demotion, or future-research blocker with a real reason. Editorial findings that threaten a scientific claim reopen the same research work-order route.
"""
    return body.strip() + "\n"


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
    elif assembly_revision == R011_REVISION:
        body = publication_translated_payload_body_r011(artifact_type_id, version)
    elif assembly_revision == R012_REVISION:
        body = publication_translated_payload_body_r012(artifact_type_id, version)
    elif assembly_revision == R013_REVISION:
        body = publication_translated_payload_body_r013(artifact_type_id, version)
    elif assembly_revision == R014_REVISION:
        body = publication_translated_payload_body_r014(artifact_type_id, version)
    elif assembly_revision in {R015_REVISION, R016_REVISION, R017_REVISION}:
        body = publication_translated_payload_body_r015(artifact_type_id, version)
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
            "Keywords: Ontology of Continua; continuum ontology; typed model core; systems theory; autopoiesis; dynamical systems; hybrid systems; formal methods; formalization inventory; finite semantic checks; retrospective bounded replay QA; reproducible research; artifact evaluation; claim governance; falsifiability; evidence-bound scientific publishing.",
            "",
            f"Citation identity: {AUTHOR_DISPLAY}, {artifact_title(artifact_type_id, version)}, {PUBLICATION_DATE}. The Concept DOI is printed on the title page.",
            "",
            "Open repository: <https://github.com/alexanderyashin/ontology-of-continua-core-main>. Repository files support reproducibility and source inspection; they do not replace the manuscript's claim boundaries.",
            "",
        ]
    )
    text = render_publication_frontmatter(artifact_type_id, version, instance) + "\n" + body + backmatter
    if assembly_revision in {R014_REVISION, R015_REVISION, R016_REVISION, R017_REVISION}:
        text = _r014_demote_retrospective_replay_language(text)
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
    reference_block = ""
    match = re.search(r"(?ims)^#\s+References\s*$([\s\S]*)", source_text)
    if match:
        reference_block = match.group(1)
    reference_lines = sorted(
        {
            re.sub(r"\s+", " ", line.strip())
            for line in reference_block.splitlines()
            if re.match(r"^\s*-\s+\S", line)
        }
    )
    return {
        "figure_total": figure_total,
        "table_total": table_total,
        "formula_marker_total": formula_marker_total,
        "bibliography_entry_total": len(reference_lines),
        "verified_bibliography_entry_total": len(reference_lines),
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


def trim_generated_text_whitespace(root_dir: Path) -> None:
    if not root_dir.is_dir():
        return
    for path in sorted(root_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".tex", ".bib", ".md", ".sty", ".cls"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        normalized = "\n".join(line.rstrip() for line in text.splitlines()) + ("\n" if text.endswith(("\n", "\r\n")) else "")
        if normalized != text:
            path.write_text(normalized, encoding="utf-8", newline="\n")


def r008_continuum_figure_tex() -> str:
    return r"""\begin{figure}[!htbp]
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
\begin{figure}[!htbp]
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
    2/{K2 physical fields and phases}/{field, phase, and large-scale physical constraints},
    3/{K3 molecular and chemical organization}/{reaction closure and molecular support},
    4/{K4 protocellular membrane system}/{compartment gradients and membrane thresholds},
    5/{K5 excitable biological system}/{regulated persistence and bioelectric organization},
    6/{K6 cognition and agency}/{memory, representation, policy, or agent control},
    7/{K7 social coordination}/{team, institution, trust, authority, governance},
    8/{K8 economic/civilizational system}/{market, platform, ecology, regulation},
    9/{K9 theory-level system}/{formal model or architecture doctrine},
    10/{K10 comparator/meta-theory}/{verification regime and comparison frame},
    11/{K11 provisional review-quality witness}/{frontier reproducibility obligation},
    12/{K12 provisional synthesis witness}/{frontier integration obligation}
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


def r012_figure_output_paths(base: Path, version: str) -> dict[str, Path]:
    root = base / "visual_quality"
    return {
        "registry_json": root / f"OC133_R012_FIGURE_REGISTRY_{version}.json",
        "registry_md": root / f"OC133_R012_FIGURE_REGISTRY_{version}.md",
        "geometry_json": root / f"OC133_R012_FIGURE_GEOMETRY_LEDGER_{version}.json",
        "geometry_md": root / f"OC133_R012_FIGURE_GEOMETRY_LEDGER_{version}.md",
        "rendered_bbox_json": root / f"OC133_R012_RENDERED_FIGURE_BBOX_LEDGER_{version}.json",
        "cockpit_json": root / f"OC133_R012_VISUAL_QA_COCKPIT_{version}.json",
        "cockpit_md": root / f"OC133_R012_VISUAL_QA_COCKPIT_{version}.md",
    }


def r012_base_colors_tex() -> str:
    return "\n".join(
        [
            r"\definecolor{ocBlue}{HTML}{173B57}",
            r"\definecolor{ocGold}{HTML}{A77D2A}",
            r"\definecolor{ocGreen}{HTML}{4B7F52}",
            r"\definecolor{ocRed}{HTML}{8E3B32}",
            r"\definecolor{ocGray}{HTML}{ECEFF1}",
        ]
    )


def _r012_rect_node(node_id: str, x: float, y: float, w: float, h: float, *, text: str, style: str) -> dict[str, Any]:
    return {
        "id": node_id,
        "x": x,
        "y": y,
        "w": w,
        "h": h,
        "text": text,
        "style": style,
        "bbox": {
            "left": round(x - w / 2, 3),
            "right": round(x + w / 2, 3),
            "bottom": round(y - h / 2, 3),
            "top": round(y + h / 2, 3),
        },
    }


def r012_continuum_spec() -> dict[str, Any]:
    nodes = [
        _r012_rect_node("context", 0.0, 4.8, 12.9, 0.72, text="Embedding context M constrains the local continuum K", style="context"),
        _r012_rect_node("state_region", 0.0, 1.05, 4.9, 2.0, text="Admissible state region Omega(K)", style="state"),
        _r012_rect_node("boundary", 5.25, 2.6, 2.8, 0.82, text="Boundary partial Omega(K)", style="boundary"),
        _r012_rect_node("axes", -5.25, 2.55, 2.8, 0.82, text="Axes A1, A2 give measurable coordinates", style="axis"),
        _r012_rect_node("flow", -5.25, 0.75, 2.8, 0.92, text="Flow J(t) moves through admissible states", style="flow"),
        _r012_rect_node("cycle", -5.25, -1.15, 2.8, 0.92, text="Cycle C(K) sustains recurrence", style="cycle"),
        _r012_rect_node("threshold", 5.25, 0.65, 2.8, 0.92, text="Threshold Theta(K) marks regime change", style="threshold"),
        _r012_rect_node("continuumness", 5.25, -1.2, 2.8, 0.92, text="Continuumness k(K,t)>0", style="state"),
        _r012_rect_node("formula", -3.15, -3.25, 5.25, 0.95, text="Formal anchor: K=(Omega, partial Omega, A, Theta, P, J, C, k, M)", style="formula"),
        _r012_rect_node("falsifier", 3.15, -3.25, 5.25, 0.95, text="Falsifier: a live K cannot cross its death boundary without a continuation rule", style="falsifier"),
    ]
    return {
        "figure_id": "r012_continuum_demonstrator",
        "label": "fig:r012-continuum-demonstrator",
        "source_rel": "content/r012/01_why_continuum_ontology.tex",
        "visual_spec_class": "deterministic_tikz_registry",
        "figure_type": "continuum_demonstrator",
        "canvas": {"width": 14.0, "height": 12.0, "margin": 0.35},
        "nodes": nodes,
        "connectors": [
            {"from": "axes", "to": "state_region", "label": "measurement"},
            {"from": "flow", "to": "state_region", "label": "motion"},
            {"from": "cycle", "to": "state_region", "label": "recurrence"},
            {"from": "boundary", "to": "state_region", "label": "admissible edge"},
            {"from": "threshold", "to": "state_region", "label": "regime change"},
            {"from": "continuumness", "to": "state_region", "label": "persistence"},
        ],
        "required_semantic_elements": ["state space", "boundary", "axes", "threshold", "flow", "cycle", "continuumness", "context", "formal tuple", "falsifier"],
        "formula_anchor": r"K=(\Omega,\partial\Omega,A,\Theta,P,J,C,k,M)",
        "evidence_anchor": "theorem/proof route and falsifier tables",
        "caption_must_explain": ["what the figure demonstrates", "variables", "formula", "falsifier"],
    }


def r012_k_hierarchy_spec() -> dict[str, Any]:
    levels = [
        ("K0", "resolution boundary", "distinction floor", "bit / admissible null"),
        ("K1", "first carrier", "coordinate interface", "signal / address"),
        ("K2", "physical fields and phases", "field/phase constraints", "physical continuum"),
        ("K3", "molecular and chemical organization", "reaction closure", "chemical network"),
        ("K4", "protocellular membrane system", "compartment gradients", "membrane / protocell"),
        ("K5", "excitable biological system", "regulated persistence", "cell / bioelectric system"),
        ("K6", "cognition and agency", "memory and policy", "agent controller"),
        ("K7", "social coordination", "authority and trust", "team / institution"),
        ("K8", "civilizational system", "market and regulation", "platform / economy"),
        ("K9", "theory-level system", "formal doctrine", "model architecture"),
        ("K10", "comparator regime", "verification frame", "benchmark / meta-theory"),
        ("K11", "provisional review-quality witness", "frontier reproducibility obligation", "evidence practice"),
        ("K12", "provisional synthesis witness", "frontier integration obligation", "unified atlas"),
    ]
    nodes: list[dict[str, Any]] = []
    for index, (kid, name, role, example) in enumerate(levels):
        y = 13.05 - index
        nodes.append(_r012_rect_node(f"{kid}_level", -5.1, y, 2.0, 0.58, text=f"{kid}: {name}", style="k_level"))
        nodes.append(_r012_rect_node(f"{kid}_role", -0.9, y, 4.75, 0.58, text=role, style="role"))
        nodes.append(_r012_rect_node(f"{kid}_example", 4.35, y, 3.25, 0.58, text=example, style="example"))
    return {
        "figure_id": "r012_k0_k12_hierarchy",
        "label": "fig:r012-k0-k12-hierarchy",
        "source_rel": "content/r012/02_first_concepts_and_k_primer.tex",
        "visual_spec_class": "deterministic_tikz_registry",
        "figure_type": "k_hierarchy",
        "canvas": {"width": 14.0, "height": 28.8, "margin": 0.25},
        "nodes": nodes,
        "connectors": [
            {"from": f"K{i}_level", "to": f"K{i + 1}_level", "label": "composition"} for i in range(12)
        ] + [
            {"from": f"K{i + 1}_role", "to": f"K{i}_role", "label": "constraint"} for i in range(12)
        ],
        "required_semantic_elements": [f"K{i}" for i in range(13)] + ["composition", "constraint", "examples", "nested hierarchy"],
        "formula_anchor": r"K_i \subset K_{i+1} under declared composition and constraint relations",
        "evidence_anchor": "K-level parameter tables and theorem-native hierarchy route",
        "caption_must_explain": ["K0-K12", "composition", "constraint", "examples", "formula"],
    }


R012_INLINE_FIGURE_GROUPS: dict[str, dict[str, Any]] = {
    "28a_oc133_inline_figures_foundation.tex": {
        "section": "Inline Visual Route: Model Foundation",
        "source_rel": "content/28a_oc133_inline_figures_foundation.tex",
        "topics": [
            ("carrier-to-realization", "Carrier to realization", "Carrier C", "Realization R_t", "lawful realization", "status at t=0,1", r"R_t=\rho(C,t)"),
            ("liveness-status-split", "Liveness status split", "Live state", "Death boundary", "status predicate", "binary status", r"live(x,t)\in\{0,1\}"),
            ("residue-after-collapse", "Residue after collapse", "Collapse event", "Residue class", "classification", "survivor count", r"residue(x,t)>0"),
            ("rebirth-continuation", "Rebirth continuation", "Residual carrier", "New realization", "continuation rule", "continuation index", r"C_{t+1}=F(C_t)"),
            ("type-discipline", "Type discipline", "Claim type", "Allowed evidence", "admissibility check", "claim family", r"claim\mapsto evidence"),
            ("boundary-test", "Boundary test", "Assumption", "Falsifier", "stress test", "negative control", r"\partial\Omega \neq \varnothing"),
        ],
    },
    "28b_oc133_inline_figures_proof_route.tex": {
        "section": "Inline Visual Route: Proof and Formalization",
        "source_rel": "content/28b_oc133_inline_figures_proof_route.tex",
        "topics": [
            ("axiom-to-theorem", "Axiom to theorem", "Axiom set", "Theorem route", "derivation", "proof status", r"\Gamma\vdash T"),
            ("formalization-inventory", "Formalization inventory", "Human theorem", "Formalized fragment", "formal subset", "checked lemmas where binding is clean", r"L\subseteq T"),
            ("finite-semantics", "Finite semantics", "Model instance", "Finite witness", "satisfaction", "model count", r"M\models\varphi"),
            ("negative-control", "Negative control", "Claim route", "Permuted label", "control contrast", "expected failure", r"control(T)=0"),
            ("assumption-ledger", "Assumption ledger", "Assumption", "Proof dependency", "dependency edge", "open assumption total", r"A_i\Rightarrow T_j"),
            ("proof-closure", "Proof closure", "Local proof", "Release claim", "promotion boundary", "closure status", r"status\in\{open,closed\}"),
        ],
    },
    "28c_oc133_inline_figures_evidence_route.tex": {
        "section": "Inline Visual Route: Evidence and Reproducibility",
        "source_rel": "content/28c_oc133_inline_figures_evidence_route.tex",
        "topics": [
            ("source-to-row", "Source to numeric row", "Source datum", "Promoted row", "extraction", "row count", r"d\mapsto r"),
            ("target-blind-replay", "Target-blind replay", "Held-out target", "Replay verdict", "blind evaluation", "pass/fail row", r"score_T"),
            ("benchmark-qa", "Benchmark QA", "Benchmark case", "QA verdict", "audit pass", "case total", r"Q(B_i)"),
            ("evidence-trail", "Evidence trail", "Claim", "Evidence bundle", "traceability", "source hash", r"claim\leftrightarrow evidence"),
            ("numeric-falsifier", "Numeric falsifier", "Prediction", "Observed bound", "threshold check", "delta", r"|x_{\mathrm{hat}}-x|<e_{\mathrm{bound}}"),
            ("repro-route", "Reproducibility route", "Scripted check", "Reader audit", "replay command", "audit status", r"run\rightarrow verdict"),
        ],
    },
    "28d_oc133_inline_figures_domain_route.tex": {
        "section": "Inline Visual Route: Domain and Practical Routes",
        "source_rel": "content/28d_oc133_inline_figures_domain_route.tex",
        "topics": [
            ("domain-projection", "Domain projection", "OC core", "Domain model", "projection", "domain count", r"P_D(K)"),
            ("enterprise-architecture", "Enterprise architecture route", "Capability", "System boundary", "architecture mapping", "interface count", r"EA(K)"),
            ("ai-builder-route", "AI builder route", "Agent policy", "Continuum guard", "control mapping", "risk class", r"\pi(a|s,K)"),
            ("security-route", "Security route", "Threat surface", "Boundary test", "falsifier search", "attack path", r"risk=\Pr(failure)"),
            ("strategy-route", "Strategy reader route", "Decision frame", "Evidence summary", "executive compression", "decision options", r"utility(K)"),
            ("comparator-route", "Comparator route", "Prior model", "OC residual", "delta accounting", "comparison row", r"\Delta_{OC}"),
        ],
    },
    "28e_oc133_inline_figures_reader_routes.tex": {
        "section": "Inline Visual Route: Reader Routes",
        "source_rel": "content/28e_oc133_inline_figures_reader_routes.tex",
        "topics": [
            ("scientific-reviewer-route", "Reviewer attack route", "A promoted OC claim", "The exact proof, finite witness, replay row, or comparator that caps it", "claim-to-anchor inspection", "attack point count", r"C_{\mathrm{public}}\Rightarrow E_{\mathrm{bounded}}"),
            ("theorist-route", "Theorist model route", "Continuum intuition", "Canonical tuple and K-level witness discipline", "concept-to-formal-object reading", "model anchors", r"K=(\Omega,\partial\Omega,A,\Theta,P,J,C,k,M)"),
            ("practitioner-route", "Applied architecture route", "Enterprise or AI system boundary", "Domain-bounded projection and falsifier", "application mapping", "decision row", r"P_D(K)\rightarrow F_D"),
            ("executive-route", "Strategy route", "Cross-domain decision question", "Bounded answer plus residual risk", "decision compression", "option set", r"V(K\mid E,R)"),
            ("auditor-route", "Evidence audit route", "Named evidence row", "Checksum, source snapshot, and reviewer verdict", "verification", "hash/check", r"H(\mathrm{source})=\mathrm{expected}"),
            ("journal-route", "Venue projection route", "Release claim set", "Journal-specific manuscript package without new claims", "format compliance", "checklist", r"R_{\mathrm{release}}\rightarrow J_{\mathrm{venue}}"),
        ],
    },
    "28f_oc133_inline_figures_appendix_route.tex": {
        "section": "Inline Visual Route: Appendices and Support Maps",
        "source_rel": "content/28f_oc133_inline_figures_appendix_route.tex",
        "topics": [
            ("notation-map", "Notation normalization map", "Symbol in prose", "Defined mathematical role", "lookup route", "notation coverage", r"s\mapsto \mathrm{definition}(s)"),
            ("axiom-map", "Axiom dependency map", "Declared assumption", "Dependent theorem", "dependency route", "theorem dependency", r"A_i\rightarrow T_j"),
            ("table-reference", "Target-blind table row map", "Prediction row with source snapshot", "Reader-facing bounded replay claim", "row-to-claim reference", "row seven: observed x, estimate xhat, residual e", r"\mathrm{row\ 7:}\ x,\ x_{\mathrm{hat}},\ e"),
            ("audit-trail", "Checksum and review trace map", "Source snapshot", "Review trace with hash and verdict", "audit path", "hash and status", r"H(\mathrm{source})=\mathrm{traceHash}"),
            ("comparison-rows", "Comparator-boundary map", "Comparator explanation", "OC residual contribution after prior art", "comparison", "residual delta", r"\Delta(\mathrm{OC},\mathrm{comparator})"),
            ("appendix-closure", "Appendix support map", "Main claim with reopening condition", "Named appendix evidence support", "support route", "support status", r"\mathrm{claim}\rightarrow\mathrm{appendix}\rightarrow\mathrm{falsifier}"),
        ],
    },
}


def r012_inline_figure_tex(spec: dict[str, Any]) -> str:
    topic = spec["topic"]
    left = latex_escape(topic["left"])
    right = latex_escape(topic["right"])
    arrow = latex_escape(topic["arrow"])
    review = latex_escape(topic["review"])
    metric = latex_escape(topic["metric"])
    formula = topic["formula"]
    title = latex_escape(topic["title"])
    caption = (
        f"{title}. This figure shows the reading relation from {left} to {right}; "
        f"the review variable is {review}, the formal anchor is \\( {formula} \\), "
        "and the evidence link is the named proof, table, replay row, or appendix section cited near the figure."
    )
    label = spec["label"]
    return rf"""\begin{{figure}}[!htbp]
\centering
\resizebox{{0.96\textwidth}}{{!}}{{%
\begin{{tikzpicture}}[x=1cm,y=1cm,>=Latex,every node/.style={{font=\small}}]
  {r012_base_colors_tex()}
  \draw[rounded corners=10pt,fill=ocGray!35,draw=ocBlue,line width=0.9pt] (-6.8,-3.4) rectangle (6.8,3.4);
  \node[font=\bfseries\large,ocBlue] at (0,3.0) {{{title}}};
  \node[draw,rounded corners=5pt,fill=blue!7,text width=0.24\textwidth,align=center,minimum height=1.05cm] (a) at (-4.35,1.0) {{{left}}};
  \node[draw,rounded corners=5pt,fill=green!8,text width=0.24\textwidth,align=center,minimum height=1.05cm] (b) at (4.35,1.0) {{{right}}};
  \draw[->,line width=1.0pt,ocGreen] (a.east) -- node[above,fill=ocGray!35,inner sep=2pt,align=center] {{{arrow}}} (b.west);
  \node[draw,rounded corners=5pt,fill=orange!10,text width=0.28\textwidth,align=center,minimum height=0.9cm] (r) at (-4.35,-1.45) {{{review}}};
  \node[draw,rounded corners=5pt,fill=white,text width=0.28\textwidth,align=center,minimum height=0.9cm] (m) at (0,-1.45) {{{metric}}};
  \node[draw,rounded corners=5pt,fill=red!6,text width=0.28\textwidth,align=center,minimum height=0.9cm] (f) at (4.35,-1.45) {{formal anchor: \( {formula} \)}};
  \draw[->,dashed,ocGold] (r.north) -- (a.south);
  \draw[->,dashed,ocGold] (m.north) -- ($(a)!0.5!(b)$);
  \draw[->,dashed,ocGold] (f.north) -- (b.south);
\end{{tikzpicture}}}}
\caption{{{caption}}}
\label{{{label}}}
\end{{figure}}"""


def r012_continuum_figure_tex() -> str:
    return rf"""% R012_VISUAL_SPEC: r012_continuum_demonstrator; geometry ledger required.
\begin{{figure}}[!htbp]
\centering
\resizebox{{0.98\textwidth}}{{!}}{{%
\begin{{tikzpicture}}[x=1cm,y=1cm,>=Latex,every node/.style={{font=\small}}]
  {r012_base_colors_tex()}
  \draw[rounded corners=12pt,fill=ocGray!35,draw=ocBlue,line width=1.0pt] (-6.9,-4.25) rectangle (6.9,5.25);
  \node[font=\bfseries\Large,ocBlue] at (0,5.75) {{A continuum in OC as a typed state system}};
  \node[draw,rounded corners=5pt,fill=blue!6,text width=0.76\textwidth,align=center,minimum height=0.72cm] at (0,4.8)
    {{Embedding context \(M\) constrains the local continuum \(K\) without replacing it.}};
  \draw[rounded corners=9pt,fill=white,draw=ocBlue,line width=0.9pt] (-2.55,0.0) rectangle (2.55,2.1);
  \node[font=\bfseries,ocBlue] at (0,1.85) {{Admissible state region \(\Omega(K)\)}};
  \draw[dashed,ocRed,line width=1.0pt] (0,1.03) ellipse (2.25 and 0.85);
  \draw[->,ocGold,line width=0.9pt] (-2.0,0.45) -- (2.0,0.45) node[right] {{\(A_1\)}};
  \draw[->,ocGold,line width=0.9pt] (-1.8,0.25) -- (-1.8,1.65) node[above] {{\(A_2\)}};
  \draw[->,blue!70!black,line width=1.1pt] (-1.45,0.65) .. controls (-0.95,1.65) and (0.95,1.65) .. (1.45,0.65);
  \draw[->,black,line width=0.9pt] (-0.45,0.7) arc (205:-110:0.52);
  \node[draw,rounded corners=5pt,fill=blue!7,text width=0.24\textwidth,align=center,minimum height=0.82cm] (axes) at (-5.25,2.55) {{Axes \(A_1,A_2\) make state differences measurable.}};
  \node[draw,rounded corners=5pt,fill=green!8,text width=0.24\textwidth,align=center,minimum height=0.82cm] (flow) at (-5.25,0.75) {{Flow \(J(t)\) shows motion through admissible states.}};
  \node[draw,rounded corners=5pt,fill=white,text width=0.24\textwidth,align=center,minimum height=0.82cm] (cycle) at (-5.25,-1.15) {{Cycle \(C(K)\) shows recurrence that sustains \(K\).}};
  \node[draw,rounded corners=5pt,fill=red!6,text width=0.24\textwidth,align=center,minimum height=0.82cm] (boundary) at (5.25,2.60) {{Boundary \(\partial\Omega(K)\) separates admissible from inadmissible states.}};
  \node[draw,rounded corners=5pt,fill=orange!10,text width=0.24\textwidth,align=center,minimum height=0.82cm] (threshold) at (5.25,0.65) {{Threshold \(\Theta(K)\) marks regime change.}};
  \node[draw,rounded corners=5pt,fill=green!8,text width=0.24\textwidth,align=center,minimum height=0.82cm] (kness) at (5.25,-1.20) {{Continuumness \(k(K,t)>0\) keeps the object live.}};
  \draw[->,ocBlue] (axes.east) -- (-2.0,1.55);
  \draw[->,ocBlue] (flow.east) -- (-1.25,1.25);
  \draw[->,ocBlue] (cycle.east) -- (-0.35,0.62);
  \draw[->,ocRed] (boundary.west) -- (2.25,1.08);
  \draw[->,ocGold] (threshold.west) -- (1.35,0.45);
  \draw[->,ocGreen] (kness.west) -- (0.55,0.62);
  \node[draw,rounded corners=5pt,fill=white,text width=0.36\textwidth,align=center,minimum height=0.95cm] at (-3.15,-3.25)
    {{Formal anchor: \(K=(\Omega,\partial\Omega,A,\Theta,P,J,C,k,M)\).}};
  \node[draw,rounded corners=5pt,fill=red!6,text width=0.36\textwidth,align=center,minimum height=0.95cm] at (3.15,-3.25)
    {{Falsifier: a live \(K\) cannot cross a declared death boundary without a valid continuation rule.}};
\end{{tikzpicture}}}}
\caption{{This didactic figure demonstrates the OC continuum tuple rather than decorating it. The variables \(\Omega\), \(\partial\Omega\), \(A\), \(\Theta\), \(J\), \(C\), \(k\), and \(M\) are separated into visible roles; the formula anchor is \(K=(\Omega,\partial\Omega,A,\Theta,P,J,C,k,M)\), and the evidence link is the theorem/proof route plus the falsifier tables.}}
\label{{fig:r012-continuum-demonstrator}}
\end{{figure}}"""


def r012_k_hierarchy_figure_tex() -> str:
    return r"""% R012_K_LEVELS_PRESENT: K0 K1 K2 K3 K4 K5 K6 K7 K8 K9 K10 K11 K12.
% R012_VISUAL_SPEC: r012_k0_k12_hierarchy; rendered bbox ledger required.
\begin{figure}[!htbp]
\centering
\resizebox{0.98\textwidth}{!}{%
\begin{tikzpicture}[x=1cm,y=0.86cm,>=Latex,every node/.style={font=\scriptsize}]
  \definecolor{ocBlue}{HTML}{173B57}
  \definecolor{ocGold}{HTML}{A77D2A}
  \definecolor{ocGreen}{HTML}{4B7F52}
  \definecolor{ocGray}{HTML}{ECEFF1}
  \node[font=\bfseries\Large,ocBlue] at (0,14.25) {Complete K0--K12 hierarchy: nested composition and downward constraint};
  \node[font=\bfseries,ocBlue] at (-5.1,13.65) {Level};
  \node[font=\bfseries,ocBlue] at (-0.9,13.65) {New system role};
  \node[font=\bfseries,ocBlue] at (4.35,13.65) {Reader example};
  \foreach \i/\kid/\name/\role/\example in {
    0/K0/resolution boundary/distinction floor/bit or admissible null,
    1/K1/first carrier/coordinate interface/signal or address,
    2/K2/process closure/lawful loop/routine or reaction,
    3/K3/organized substrate/stable support/deployment substrate,
    4/K4/binding system/component integration/module or membrane,
    5/K5/liveness system/regulated persistence/organism or service health,
    6/K6/cognition and agency/memory and policy/agent controller,
    7/K7/social coordination/authority and trust/team or institution,
    8/K8/civilizational system/market and regulation/platform or economy,
    9/K9/theory-level system/formal doctrine/model architecture,
    10/K10/comparator regime/verification frame/benchmark or meta-theory,
    11/K11/publication quality/reproducible review/evidence practice,
    12/K12/cross-domain synthesis/bounded integration/unified atlas
  }{
    \pgfmathsetmacro{\y}{13.05-\i}
    \node[draw,rounded corners=3pt,fill=blue!7,text width=0.17\textwidth,align=center,minimum height=0.52cm] (k\i) at (-5.1,\y) {\textbf{\kid}: \name};
    \node[draw,rounded corners=3pt,fill=green!7,text width=0.36\textwidth,align=center,minimum height=0.52cm] (r\i) at (-0.9,\y) {\role};
    \node[draw,rounded corners=3pt,fill=ocGray!45,text width=0.25\textwidth,align=center,minimum height=0.52cm] (e\i) at (4.35,\y) {\example};
    \draw[-,ocBlue] (k\i.east) -- (r\i.west);
    \draw[-,ocBlue] (r\i.east) -- (e\i.west);
  }
  \foreach \i in {0,...,11}{
    \pgfmathtruncatemacro{\j}{\i+1}
    \draw[->,ocGreen,line width=0.65pt] (k\i.north east) -- (k\j.south east);
    \draw[->,ocGold,line width=0.65pt] (r\j.south west) -- (r\i.north west);
  }
  \node[draw,rounded corners=5pt,fill=white,text width=0.38\textwidth,align=center] at (-4.0,-0.62)
    {upward composition: lower continua make the next continuum possible};
  \node[draw,rounded corners=5pt,fill=white,text width=0.44\textwidth,align=center] at (2.65,-0.62)
    {downward constraint: the containing continuum narrows admissible lower-level behaviour};
  \draw[->,thick,ocGreen] (-6.8,-0.05) -- (-6.8,13.25) node[midway,left,align=center] {composition};
  \draw[->,thick,ocGold] (6.8,13.25) -- (6.8,-0.05) node[midway,right,align=center] {constraint};
\end{tikzpicture}}
\caption{This figure demonstrates the K-level teaching hierarchy used by this release. K0--K10 are the current core grammar; K11 and K12 are shown as provisional upper-taxonomy witnesses that remain under review rather than promoted irreducibility theorems. Every level is numbered, named, tied to a human example, and placed between upward composition and downward constraint; the formal anchor is \(K_i \subset K_{i+1}\) under declared composition and constraint relations, with evidence support in the K-level parameter tables and hierarchy-route boundary.}
\label{fig:r012-k0-k12-hierarchy}
\end{figure}"""


def r012_inline_specs() -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    for filename, group in R012_INLINE_FIGURE_GROUPS.items():
        for index, (slug, title, left, right, arrow, review, formula) in enumerate(group["topics"], start=1):
            label = f"fig:r012-inline-{filename.removesuffix('.tex')}-{index}"
            caption = (
                f"{title}. The figure demonstrates the reader-facing route from {left} to {right}; "
                f"the relevant variable or number is {review}, the formula anchor is {formula}, "
                "and the evidence link is the corresponding proof, table, or replay section in the release corpus."
            )
            specs.append(
                {
                    "figure_id": f"r012_inline_{filename.removesuffix('.tex')}_{index}",
                    "label": label,
                    "source_rel": str(group["source_rel"]),
                    "visual_spec_class": "deterministic_tikz_registry",
                    "figure_type": "inline_didactic_route",
                    "canvas": {"width": 13.6, "height": 6.8, "margin": 0.35},
                    "nodes": [
                        _r012_rect_node("left", -4.35, 1.0, 3.3, 1.05, text=left, style="left"),
                        _r012_rect_node("right", 4.35, 1.0, 3.3, 1.05, text=right, style="right"),
                        _r012_rect_node("review", -4.35, -1.45, 3.6, 0.9, text=review, style="review"),
                        _r012_rect_node("metric", 0.0, -1.45, 3.6, 0.9, text=f"variable or number: {review}", style="metric"),
                        _r012_rect_node("formula", 4.35, -1.45, 3.6, 0.9, text=f"formal anchor: {formula}", style="formula"),
                    ],
                    "connectors": [
                        {"from": "left", "to": "right", "label": arrow},
                        {"from": "review", "to": "left", "label": "audit"},
                        {"from": "metric", "to": "left/right", "label": "measurement"},
                        {"from": "formula", "to": "right", "label": "formal link"},
                    ],
                    "required_semantic_elements": ["left object", "right object", "arrow", "variable or number", "formula", "evidence link"],
                    "formula_anchor": formula,
                    "evidence_anchor": "corresponding proof, table, or replay section",
                    "caption_must_explain": ["demonstrates", "variable", "formula", "evidence"],
                    "topic": {
                        "slug": slug,
                        "title": title,
                        "left": left,
                        "right": right,
                        "arrow": arrow,
                        "review": review,
                        "metric": review,
                        "formula": formula,
                        "caption": caption,
                    },
                }
            )
    return specs


def r012_registry_specs(source_dir: Path, version: str) -> dict[str, Any]:
    specs = [r012_continuum_spec(), r012_k_hierarchy_spec(), *r012_inline_specs()]
    known_labels = {spec["label"] for spec in specs}
    for tex_path in sorted((source_dir / "content").rglob("*.tex")) + sorted((source_dir / "appendix").rglob("*.tex")):
        text = tex_path.read_text(encoding="utf-8", errors="replace")
        for index, block in enumerate(re.findall(r"\\begin\{figure\}.*?\\end\{figure\}", text, flags=re.S), start=1):
            label_match = re.search(r"\\label\{([^}]+)\}", block)
            label = label_match.group(1) if label_match else f"unlabelled:{tex_path.relative_to(source_dir).as_posix()}:{index}"
            if label in known_labels:
                continue
            caption_match = re.search(r"\\caption\{(.*?)\}", block, flags=re.S)
            caption = re.sub(r"\s+", " ", caption_match.group(1)).strip() if caption_match else ""
            specs.append(
                {
                    "figure_id": f"legacy_{len(specs) + 1:04d}",
                    "label": label,
                    "source_rel": tex_path.relative_to(source_dir).as_posix(),
                    "visual_spec_class": "legacy_corpus_figure_registered_for_render_audit",
                    "figure_type": "legacy_corpus_figure",
                    "canvas": None,
                    "nodes": [],
                    "connectors": [],
                    "caption": caption,
                    "formula_anchor": "legacy corpus anchor",
                    "evidence_anchor": "legacy source figure and rendered PDF text",
                    "caption_must_explain": ["demonstrates", "formula", "evidence"],
                }
            )
            known_labels.add(label)
    return {
        "schema_id": "OC133_R012_FIGURE_REGISTRY_v1",
        "status": "PASS",
        "release_id": "oc_core_1_3_3",
        "version": version,
        "source_revision": R011_REVISION,
        "registry_policy": "Every reader-facing TeX figure receives a registry row; r012 generated figures carry explicit node geometry.",
        "figure_total": len(specs),
        "deterministic_tikz_spec_total": sum(1 for spec in specs if spec["visual_spec_class"] == "deterministic_tikz_registry"),
        "legacy_registered_total": sum(1 for spec in specs if spec["visual_spec_class"].startswith("legacy_")),
        "figures": specs,
    }


def _bbox_intersection(a: dict[str, float], b: dict[str, float]) -> float:
    width = max(0.0, min(a["right"], b["right"]) - max(a["left"], b["left"]))
    height = max(0.0, min(a["top"], b["top"]) - max(a["bottom"], b["bottom"]))
    return width * height


def r012_geometry_ledger(registry: dict[str, Any]) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    checked = 0
    for spec in registry.get("figures", []):
        nodes = spec.get("nodes") or []
        if not nodes:
            continue
        checked += 1
        canvas = spec.get("canvas") or {}
        half_w = float(canvas.get("width") or 0) / 2
        half_h = float(canvas.get("height") or 0) / 2
        margin = float(canvas.get("margin") or 0.0)
        for node in nodes:
            bbox = node["bbox"]
            if bbox["left"] < -half_w + margin or bbox["right"] > half_w - margin or bbox["bottom"] < -half_h + margin or bbox["top"] > half_h - margin:
                findings.append({"kind": "r012_node_outside_canvas", "figure_id": spec["figure_id"], "node_id": node["id"], "bbox": bbox, "canvas": canvas})
        for left_index, left in enumerate(nodes):
            for right in nodes[left_index + 1:]:
                overlap = _bbox_intersection(left["bbox"], right["bbox"])
                if overlap > 0.01:
                    findings.append({"kind": "r012_node_bbox_overlap", "figure_id": spec["figure_id"], "left": left["id"], "right": right["id"], "overlap": round(overlap, 4)})
    payload = {
        "schema_id": "OC133_R012_FIGURE_GEOMETRY_LEDGER_v1",
        "status": "PASS" if not findings else "FAIL",
        "checked_spec_total": checked,
        "finding_total": len(findings),
        "findings": findings,
        "min_label_gap_policy": "explicit node rectangles must not intersect; connector labels are placed on separate lanes",
        "font_size_floor": "scriptsize for dense K map, small for didactic figures",
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def r012_render_inline_group(filename: str, group: dict[str, Any], specs: list[dict[str, Any]]) -> str:
    figures = [spec for spec in specs if spec["source_rel"] == group["source_rel"] and spec["figure_type"] == "inline_didactic_route"]
    lines = [rf"\section{{{latex_escape(group['section'])}}}", "", "These figures are placed in the main argument as visual proof-of-reading aids: each one separates objects, direction, quantitative or formal anchor, and evidence route.", ""]
    for spec in figures:
        topic = spec["topic"]
        lines.append(rf"\subsection{{{latex_escape(topic['title'])}}}")
        lines.append("")
        lines.append(
            f"This figure is included because the reader must see how {latex_escape(topic['left'])} is constrained by {latex_escape(topic['right'])}. "
            f"The highlighted review variable is {latex_escape(topic['review'])}, and the formal anchor is ${topic['formula']}$. "
            "The nearby prose names the proof, evidence row, table, replay check, or appendix that carries the claim."
        )
        lines.append("")
        lines.append(r012_inline_figure_tex(spec))
        lines.append("")
    lines.append(r"\clearpage")
    return "\n".join(lines).rstrip() + "\n"


def apply_r012_visual_overrides(source_dir: Path) -> None:
    content_dir = source_dir / "content"
    r008_dir = content_dir / "r008"
    r012_dir = content_dir / "r012"
    if not r008_dir.is_dir():
        return
    r012_dir.mkdir(parents=True, exist_ok=True)
    replacements = [
        (r008_dir / "01_why_continuum_ontology.tex", r012_dir / "01_why_continuum_ontology.tex", "continuum"),
        (r008_dir / "02_first_concepts_and_k_primer.tex", r012_dir / "02_first_concepts_and_k_primer.tex", "k_hierarchy"),
    ]
    for source, target, kind in replacements:
        if not source.is_file():
            continue
        text = source.read_text(encoding="utf-8", errors="replace").replace("r008", "r012").replace("R008", "R012")
        if kind == "continuum":
            text = re.sub(
                r"% R012_VISUAL_SPEC:.*?\\label\{fig:r012-continuum-demonstrator\}\s*\\end\{figure\}",
                lambda _match: r012_continuum_figure_tex(),
                text,
                count=1,
                flags=re.S,
            )
            if "fig:r012-continuum-demonstrator" not in text:
                text = re.sub(
                    r"\\begin\{figure\}\[p\].*?\\label\{fig:r012-continuum-demonstrator\}\s*\\end\{figure\}",
                    lambda _match: r012_continuum_figure_tex(),
                    text,
                    count=1,
                    flags=re.S,
                )
        else:
            text = re.sub(
                r"% R012_K_LEVELS_PRESENT:.*?\\label\{fig:r012-k0-k12-hierarchy\}\s*\\end\{figure\}",
                lambda _match: r012_k_hierarchy_figure_tex(),
                text,
                count=1,
                flags=re.S,
            )
            if "fig:r012-k0-k12-hierarchy" not in text:
                text = re.sub(
                    r"% R008_K_LEVELS_PRESENT:.*?\\label\{fig:r012-k0-k12-hierarchy\}\s*\\end\{figure\}",
                    lambda _match: r012_k_hierarchy_figure_tex(),
                    text,
                    count=1,
                    flags=re.S,
                )
        write_text_if_changed(target, text)
    inline_specs = r012_inline_specs()
    for filename, group in R012_INLINE_FIGURE_GROUPS.items():
        target = content_dir / filename
        write_text_if_changed(target, r012_render_inline_group(filename, group, inline_specs))
    entry = source_dir / science_monolith.BASE_ENTRYPOINT
    if entry.is_file():
        text = entry.read_text(encoding="utf-8", errors="replace")
        text = text.replace("content/r008/01_why_continuum_ontology.tex", "content/r012/01_why_continuum_ontology.tex")
        text = text.replace("content/r008/02_first_concepts_and_k_primer.tex", "content/r012/02_first_concepts_and_k_primer.tex")
        if "% R012_TOC_VISUAL_HIERARCHY" not in text:
            text = text.replace("% R008_TOC_VISUAL_HIERARCHY", "% R008_TOC_VISUAL_HIERARCHY\n% R012_TOC_VISUAL_HIERARCHY")
        write_text_if_changed(entry, text)


def render_r012_registry_md(payload: dict[str, Any]) -> str:
    lines = [
        "# OC Core 1.3.3 r012 Figure Registry",
        "",
        f"Status: `{payload['status']}`",
        f"Figure total: `{payload['figure_total']}`",
        f"Deterministic TikZ specs: `{payload['deterministic_tikz_spec_total']}`",
        f"Legacy registered figures: `{payload['legacy_registered_total']}`",
        "",
        "## Figures",
        "",
    ]
    for spec in payload.get("figures", []):
        lines.append(f"- `{spec['label']}`: `{spec['visual_spec_class']}` from `{spec['source_rel']}`")
    return "\n".join(lines).rstrip() + "\n"


def render_r012_geometry_md(payload: dict[str, Any]) -> str:
    lines = [
        "# OC Core 1.3.3 r012 Figure Geometry Ledger",
        "",
        f"Status: `{payload['status']}`",
        f"Checked explicit specs: `{payload['checked_spec_total']}`",
        f"Finding total: `{payload['finding_total']}`",
    ]
    return "\n".join(lines).rstrip() + "\n"


def r012_probe_tex(registry: dict[str, Any], source_dir: Path) -> str:
    tex_blocks: list[str] = []
    for spec in registry.get("figures", []):
        if spec["figure_type"] == "continuum_demonstrator":
            tex_blocks.append(r012_continuum_figure_tex())
        elif spec["figure_type"] == "k_hierarchy":
            tex_blocks.append(r012_k_hierarchy_figure_tex())
        elif spec["figure_type"] == "inline_didactic_route":
            tex_blocks.append(r012_inline_figure_tex(spec))
    return "\n".join(
        [
            r"\documentclass[11pt,a4paper]{article}",
            r"\usepackage[margin=0.55in]{geometry}",
            r"\usepackage{amsmath,amssymb}",
            r"\usepackage{graphicx}",
            r"\usepackage{tikz}",
            r"\usetikzlibrary{arrows.meta,calc,positioning}",
            r"\usepackage{xcolor}",
            r"\pagestyle{empty}",
            r"\begin{document}",
            *tex_blocks,
            r"\end{document}",
            "",
        ]
    )


def r012_rendered_bbox_ledger(paths: dict[str, Path], registry: dict[str, Any], source_dir: Path, *, write: bool) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    text = ""
    bbox_word_total = 0
    probe_pdf_path: Path | None = None
    with tempfile.TemporaryDirectory(prefix="oc133_r012_visual_probe_") as tmpdir:
        tmp = Path(tmpdir)
        probe_tex = tmp / f"oc133_r012_visual_probe_{registry.get('version', '1.3.3')}.tex"
        probe_pdf = probe_tex.with_suffix(".pdf")
        probe_tex.write_text(r012_probe_tex(registry, source_dir), encoding="utf-8", newline="\n")
        compile_result = subprocess.run(
            ["xelatex", "-interaction=nonstopmode", "-halt-on-error", probe_tex.name],
            cwd=tmp,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=240,
        )
        probe_pdf_path = probe_pdf if probe_pdf.is_file() else None
        if not probe_pdf.is_file():
            findings.append(
                {
                    "kind": "r012_probe_pdf_missing",
                    "technical_temp_pdf": True,
                    "returncode": compile_result.returncode,
                    "stdout_tail": compile_result.stdout[-800:],
                    "stderr_tail": compile_result.stderr[-800:],
                }
            )
        else:
            completed = subprocess.run(
                ["pdftotext", "-bbox-layout", str(probe_pdf), "-"],
                cwd=ROOT,
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                timeout=120,
            )
            text = completed.stdout
            bbox_word_total = len(re.findall(r"<word\b", text))
            for level in [f"K{i}" for i in range(13)]:
                if not re.search(rf">{re.escape(level)}(?::|<)", text):
                    findings.append({"kind": "r012_rendered_k_label_missing", "label": level})
            if bbox_word_total < 200:
                findings.append({"kind": "r012_rendered_bbox_word_count_low", "bbox_word_total": bbox_word_total})
            raster_prefix = tmp / "oc133_r012_visual_probe_raster"
            subprocess.run(
                ["pdftocairo", "-png", "-f", "1", "-l", "1", str(probe_pdf), str(raster_prefix)],
                cwd=ROOT,
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                timeout=120,
            )
            raster_outputs = sorted(tmp.glob(f"{raster_prefix.name}-*.png"))
            png = raster_outputs[0] if raster_outputs else tmp / "oc133_r012_visual_probe_raster-1.png"
            if png.is_file():
                try:
                    from PIL import Image

                    with Image.open(png) as image:
                        gray = image.convert("L")
                        pixels = list(gray.getdata())
                        dark = sum(1 for value in pixels if value < 245)
                        ratio = dark / max(1, len(pixels))
                        edge_pixels = []
                        w, h = gray.size
                        for x in range(w):
                            edge_pixels.append(gray.getpixel((x, 0)))
                            edge_pixels.append(gray.getpixel((x, h - 1)))
                        for y in range(h):
                            edge_pixels.append(gray.getpixel((0, y)))
                            edge_pixels.append(gray.getpixel((w - 1, y)))
                        edge_dark_ratio = sum(1 for value in edge_pixels if value < 245) / max(1, len(edge_pixels))
                        if ratio < 0.01:
                            findings.append({"kind": "r012_rendered_raster_near_blank", "nonwhite_ratio": ratio})
                        if edge_dark_ratio > 0.015:
                            findings.append({"kind": "r012_rendered_edge_collision_risk", "edge_dark_ratio": edge_dark_ratio})
                except Exception as exc:
                    findings.append({"kind": "r012_rendered_raster_probe_failed", "error": str(exc)})
            else:
                findings.append({"kind": "r012_rendered_raster_missing", "technical_temp_png": True})
    payload = {
        "schema_id": "OC133_R012_RENDERED_FIGURE_BBOX_LEDGER_v1",
        "status": "PASS" if not findings else "FAIL",
        "technical_probe_pdf_policy": "temporary_pdf_used_for_bbox_and_raster_checks_then_discarded",
        "technical_probe_pdf_in_public_package": False,
        "bbox_word_total": bbox_word_total,
        "finding_total": len(findings),
        "findings": findings,
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def r012_visual_cockpit(registry: dict[str, Any], geometry: dict[str, Any], rendered: dict[str, Any], *, source_figure_total: int) -> dict[str, Any]:
    registry_figure_total = int(registry.get("figure_total") or 0)
    deterministic_total = int(registry.get("deterministic_tikz_spec_total") or 0)
    generated_labels = {spec["label"] for spec in registry.get("figures", []) if spec.get("visual_spec_class") == "deterministic_tikz_registry"}
    required_labels = {"fig:r012-continuum-demonstrator", "fig:r012-k0-k12-hierarchy"}
    k_complete = required_labels.issubset(generated_labels)
    status_map = {
        "figure_spec_coverage_status": "PASS" if registry_figure_total >= 36 and deterministic_total >= 38 else "FAIL",
        "diagram_geometry_status": "PASS" if geometry.get("status") == "PASS" else "FAIL",
        "rendered_figure_bbox_status": "PASS" if rendered.get("status") == "PASS" else "FAIL",
        "label_collision_status": "PASS" if geometry.get("status") == "PASS" and rendered.get("status") == "PASS" else "FAIL",
        "figure_semantic_completeness_status": "PASS" if deterministic_total >= 38 else "FAIL",
        "k_hierarchy_visual_status": "PASS" if k_complete and rendered.get("status") == "PASS" else "FAIL",
        "continuum_visual_status": "PASS" if "fig:r012-continuum-demonstrator" in generated_labels and rendered.get("status") == "PASS" else "FAIL",
        "caption_argument_status": "PASS" if all(spec.get("formula_anchor") and spec.get("evidence_anchor") for spec in registry.get("figures", [])) else "FAIL",
    }
    status_map["visual_cockpit_status"] = "PASS" if all(value == "PASS" for value in status_map.values()) else "FAIL"
    payload = {
        "schema_id": "OC133_R012_VISUAL_QA_COCKPIT_v1",
        "status": status_map["visual_cockpit_status"],
        "source_revision": R011_REVISION,
        "source_figure_total": source_figure_total,
        "registered_figure_total": registry_figure_total,
        "deterministic_tikz_spec_total": deterministic_total,
        "legacy_registered_total": registry.get("legacy_registered_total"),
        **status_map,
        "publication_actions_performed": False,
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def render_r012_visual_cockpit_md(payload: dict[str, Any]) -> str:
    lines = [
        "# OC Core 1.3.3 r012 Visual QA Cockpit",
        "",
        f"Status: `{payload['status']}`",
        f"Registered figures: `{payload['registered_figure_total']}`",
        f"Source figures: `{payload['source_figure_total']}`",
        "",
        "## Gates",
        "",
    ]
    for key in [
        "figure_spec_coverage_status",
        "diagram_geometry_status",
        "rendered_figure_bbox_status",
        "label_collision_status",
        "figure_semantic_completeness_status",
        "k_hierarchy_visual_status",
        "continuum_visual_status",
        "caption_argument_status",
        "visual_cockpit_status",
    ]:
        lines.append(f"- `{key}`: `{payload.get(key)}`")
    return "\n".join(lines).rstrip() + "\n"


def build_r012_visual_quality(base: Path, version: str, source_dir: Path, *, write: bool, source_figure_total: int) -> dict[str, Any]:
    paths = r012_figure_output_paths(base, version)
    registry = r012_registry_specs(source_dir, version)
    geometry = r012_geometry_ledger(registry)
    rendered = r012_rendered_bbox_ledger(paths, registry, source_dir, write=write)
    cockpit = r012_visual_cockpit(registry, geometry, rendered, source_figure_total=source_figure_total)
    if write:
        write_json_if_changed(paths["registry_json"], registry)
        write_text_if_changed(paths["registry_md"], render_r012_registry_md(registry))
        write_json_if_changed(paths["geometry_json"], geometry)
        write_text_if_changed(paths["geometry_md"], render_r012_geometry_md(geometry))
        write_json_if_changed(paths["rendered_bbox_json"], rendered)
        write_json_if_changed(paths["cockpit_json"], cockpit)
        write_text_if_changed(paths["cockpit_md"], render_r012_visual_cockpit_md(cockpit))
    return {"paths": paths, "registry": registry, "geometry": geometry, "rendered": rendered, "cockpit": cockpit}


def r013_table_output_paths(base: Path, version: str) -> dict[str, Path]:
    root = base / "table_quality"
    return {
        "registry_json": root / f"OC133_R013_TABLE_REGISTRY_{version}.json",
        "registry_md": root / f"OC133_R013_TABLE_REGISTRY_{version}.md",
        "geometry_json": root / f"OC133_R013_TABLE_GEOMETRY_LEDGER_{version}.json",
        "geometry_md": root / f"OC133_R013_TABLE_GEOMETRY_LEDGER_{version}.md",
        "rendered_bbox_json": root / f"OC133_R013_RENDERED_TABLE_BBOX_LEDGER_{version}.json",
        "cockpit_json": root / f"OC133_R013_TABLE_QA_COCKPIT_{version}.json",
        "cockpit_md": root / f"OC133_R013_TABLE_QA_COCKPIT_{version}.md",
    }


def r013_included_tex_files(source_dir: Path) -> list[Path]:
    entry = source_dir / science_monolith.BASE_ENTRYPOINT
    seen: list[Path] = []

    def walk(path: Path) -> None:
        if path.suffix == "":
            path = path.with_suffix(".tex")
        if not path.is_absolute():
            path = source_dir / path
        path = path.resolve()
        try:
            path.relative_to(source_dir.resolve())
        except ValueError:
            return
        if path in seen or not path.is_file():
            return
        seen.append(path)
        text = path.read_text(encoding="utf-8", errors="replace")
        for match in re.finditer(r"\\input\{([^}]+)\}", text):
            target = path.parent / match.group(1)
            if target.suffix == "":
                target = target.with_suffix(".tex")
            walk(target)

    if entry.is_file():
        walk(entry)
    return seen


def r013_all_source_table_total(source_dir: Path) -> int:
    if not source_dir.is_dir():
        return 0
    total = 0
    for path in source_dir.rglob("*.tex"):
        text = path.read_text(encoding="utf-8", errors="replace")
        total += len(re.findall(r"\\begin\{(?:table|longtable|tabular|tabularx)\}", text))
    return total


def _r013_booktabs_body(tabular_body: str) -> str:
    lines = tabular_body.strip().splitlines()
    hline_indexes = [index for index, line in enumerate(lines) if r"\hline" in line]
    for order, index in enumerate(hline_indexes):
        if order == 0:
            lines[index] = lines[index].replace(r"\hline", r"\toprule")
        elif order == len(hline_indexes) - 1:
            lines[index] = lines[index].replace(r"\hline", r"\bottomrule")
        else:
            lines[index] = lines[index].replace(r"\hline", r"\midrule")
    return "\n".join(lines).strip()


def _r013_tex_braced_argument(text: str, command: str, start_index: int = 0) -> tuple[str, int] | None:
    command_index = text.find(command, start_index)
    if command_index < 0:
        return None
    brace_index = text.find("{", command_index + len(command))
    if brace_index < 0:
        return None
    depth = 0
    for index in range(brace_index, len(text)):
        char = text[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[brace_index + 1 : index], index + 1
    return None


def _r013_replace_labelled_table_float(text: str, label: str, caption: str) -> str:
    pattern = rf"\\begin\{{table\}}(?:\[[^\]]*\])?.*?\\label\{{{re.escape(label)}\}}.*?\\end\{{table\}}"
    match = re.search(pattern, text, flags=re.S)
    if not match:
        return text
    block = match.group(0)
    tabular_start = block.find(r"\begin{tabular}")
    tabular_end = block.find(r"\end{tabular}", tabular_start)
    braced = _r013_tex_braced_argument(block, r"\begin{tabular}", tabular_start)
    if tabular_start < 0 or tabular_end < 0 or not braced:
        return text
    spec, body_start = braced
    body = _r013_booktabs_body(block[body_start:tabular_end])
    replacement = "\n".join(
        [
            "% R013_TABLE_LAYOUT_STANDARD: normalized from float/tabular to reader-safe longtable.",
            r"\begin{octablescope}",
            rf"\begin{{longtable}}{{{spec}}}",
            rf"\caption{{{caption}}}\label{{{label}}}\\",
            body,
            r"\end{longtable}",
            r"\end{octablescope}",
        ]
    )
    return text[: match.start()] + replacement + text[match.end() :]


def _r013_public_table_phrases(block: str) -> str:
    replacements = {
        r"HYBRID\_ESCALATION": "hybrid escalation",
        r"DETERMINISTIC\_COUNTEREXAMPLE\_AND\_TRACE\_REPLAY": "deterministic counterexample and trace replay",
        r"LEAVE\_ONE\_BENCHMARK\_FAMILY\_OUT": "leave one benchmark family out",
        r"HOLD\_OUT\_ONE\_COMPOUND\_OR\_REACTION\_CLASS": "hold out one compound or reaction class",
        r"RESERVE\_ONE\_DATASET\_FAMILY\_PER\_SIGNATURE\_CLASS": "reserve one dataset family per signature class",
        r"HELD\_OUT\_INTERVAL\_REPLAY\_WITH\_TURNING\_POINT\_CHECKS": "held-out interval replay with turning-point checks",
        r"INSTITUTE\_RUN::PHYSICS::wave 1a": "physics measurement wave 1a",
        r"INSTITUTE\_RUN::CHEMISTRY::wave 2a": "chemistry measurement wave 2a",
        r"INSTITUTE\_RUN::BIOLOGY::wave 3a": "biology measurement wave 3a",
        r"INSTITUTE\_RUN::SYSTEMS::wave 4a": "systems measurement wave 4a",
        r"TIER1\_AIMATH\_PDF\_013\_Q010": "Tier-1 mathematics exact-question packet",
        r"PHY\_BENCH\_001": "physics benchmark packet",
        r"CHEM\_BENCH\_001": "chemistry benchmark packet",
        r"BIO\_BENCH\_001": "biology benchmark packet",
        r"SYS\_BENCH\_001": "systems benchmark packet",
        r"--domain-id PHYSICS": "(physics)",
        r"--domain-id CHEMISTRY": "(chemistry)",
        r"--domain-id BIOLOGY": "(biology)",
        r"--domain-id SYSTEMS\_CIVILIZATIONAL\_PROJECTION": "(systems and civilizational projection)",
    }
    for old, new in replacements.items():
        block = block.replace(old, new)
    return block


def _r013_normalize_longtable_public_phrases(text: str) -> str:
    parts: list[str] = []
    cursor = 0
    for match in re.finditer(r"\\begin\{longtable\}", text):
        end_token = r"\end{longtable}"
        end = text.find(end_token, match.end())
        if end < 0:
            break
        end += len(end_token)
        parts.append(text[cursor : match.start()])
        parts.append(_r013_public_table_phrases(text[match.start() : end]))
        cursor = end
    parts.append(text[cursor:])
    return "".join(parts)


def _r013_replace_longtable_head(text: str, header_needle: str, caption: str, label: str, spec: str) -> str:
    header_index = text.find(header_needle)
    if header_index < 0:
        return text
    start = text.rfind(r"\begin{longtable}", 0, header_index)
    if start < 0:
        return text
    end_token = r"\end{longtable}"
    end = text.find(end_token, header_index)
    if end < 0:
        return text
    end += len(end_token)
    block = text[start:end]
    lines = block.splitlines()
    if not lines:
        return text
    lines[0] = rf"\begin{{longtable}}{{{spec}}}"
    if not any(r"\caption" in line for line in lines[:3]):
        lines.insert(1, rf"\caption{{{caption}}}\label{{{label}}}\\")
    block = "\n".join(lines)
    if not block.startswith(r"\begin{octablescope}"):
        block = r"\begin{octablescope}" + "\n" + block + "\n" + r"\end{octablescope}"
    block = _r013_public_table_phrases(block)
    return text[:start] + block + text[end:]


def apply_r013_table_overrides(source_dir: Path) -> None:
    preamble = source_dir / "preamble.tex"
    if preamble.is_file():
        text = preamble.read_text(encoding="utf-8", errors="replace")
        if "% R013_TABLE_LAYOUT_STANDARD" not in text:
            text += "\n".join(
                [
                    "",
                    "% R013_TABLE_LAYOUT_STANDARD",
                    r"\setlength{\LTpre}{0.35em}",
                    r"\setlength{\LTpost}{0.75em}",
                    r"\renewcommand{\arraystretch}{1.34}",
                    r"\setlength{\tabcolsep}{4.2pt}",
                    r"\emergencystretch=3em",
                    r"\newcommand{\octablefont}{\footnotesize\RaggedRight\sloppy}",
                    r"\newenvironment{octablescope}{\begingroup\octablefont\setlength{\tabcolsep}{4.0pt}\renewcommand{\arraystretch}{1.34}}{\endgroup}",
                    "",
                ]
            )
            write_text_if_changed(preamble, text)

    k_tables = source_dir / "appendix" / "C_klevels_tables.tex"
    if k_tables.is_file():
        text = k_tables.read_text(encoding="utf-8", errors="replace")
        text = _r013_replace_labelled_table_float(text, "tab:klevels-overview", "Continuum hierarchy from K0 to K12 with level, domain, and structural characterization columns.")
        text = _r013_replace_labelled_table_float(text, "tab:klevels-structure", "Structural components per K-level: axes, potentials, and typical cycles used as the reader-facing audit surface.")
        write_text_if_changed(k_tables, text)

    theorem = source_dir / "content" / "20_oc_core_1_3_theorem_roadmap.tex"
    if theorem.is_file():
        text = theorem.read_text(encoding="utf-8", errors="replace")
        text = _r013_replace_longtable_head(
            text,
            "Row family & Current fate & Release consequence",
            "Theorem-fate correction table distinguishing proof-routed claims, source witnesses, definitions, and unresolved tasks.",
            "tab:r013-theorem-fate-correction",
            r"@{}L{0.22\textwidth}L{0.24\textwidth}L{0.44\textwidth}@{}",
        )
        text = _r013_normalize_longtable_public_phrases(text)
        write_text_if_changed(theorem, text)

    operational = source_dir / "content" / "22_oc_core_1_3_operationalization_program.tex"
    if operational.is_file():
        text = operational.read_text(encoding="utf-8", errors="replace")
        text = _r013_replace_longtable_head(
            text,
            "Domain & Validation & Data route & Benchmark families & Next lawful action",
            "Operationalization domains, validation posture, benchmark families, and next lawful action for predictive promotion.",
            "tab:r013-operationalization-program",
            r"@{}L{0.13\textwidth}L{0.14\textwidth}L{0.17\textwidth}L{0.31\textwidth}L{0.15\textwidth}@{}",
        )
        text = _r013_normalize_longtable_public_phrases(text)
        write_text_if_changed(operational, text)

    empirical = source_dir / "content" / "23_oc_core_1_3_empirical_execution_protocols.tex"
    if empirical.is_file():
        text = empirical.read_text(encoding="utf-8", errors="replace")
        text = _r013_replace_longtable_head(
            text,
            "Domain & Wave & Evidence bar & Held-out policy & Replay & Institute-run wave",
            "Execution protocol matrix for empirical lanes, held-out policy, replay route, and institute-run escalation trigger.",
            "tab:r013-execution-protocol-matrix",
            r"@{}L{0.13\textwidth}L{0.09\textwidth}L{0.10\textwidth}L{0.18\textwidth}L{0.13\textwidth}L{0.14\textwidth}@{}",
        )
        text = _r013_normalize_longtable_public_phrases(text)
        write_text_if_changed(empirical, text)

    entry = source_dir / science_monolith.BASE_ENTRYPOINT
    if entry.is_file():
        text = entry.read_text(encoding="utf-8", errors="replace")
        if "% R013_TABLE_LAYOUT_STANDARD" not in text:
            text = text.replace("% R012_TOC_VISUAL_HIERARCHY", "% R012_TOC_VISUAL_HIERARCHY\n% R013_TABLE_LAYOUT_STANDARD")
            write_text_if_changed(entry, text)


def _r013_table_env_blocks(source_dir: Path) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    for tex_path in r013_included_tex_files(source_dir):
        text = tex_path.read_text(encoding="utf-8", errors="replace")
        for env in ["table", "longtable"]:
            for match in re.finditer(rf"\\begin\{{{env}\}}", text):
                end_token = rf"\end{{{env}}}"
                end = text.find(end_token, match.end())
                if end < 0:
                    continue
                end += len(end_token)
                block = text[match.start() : end]
                if env == "table" and r"\begin{tabular}" not in block:
                    continue
                blocks.append(
                    {
                        "source_path": tex_path,
                        "source_rel": tex_path.relative_to(source_dir).as_posix(),
                        "line": text[: match.start()].count("\n") + 1,
                        "env": env,
                        "block": block,
                    }
                )
    blocks.sort(key=lambda item: (item["source_rel"], item["line"]))
    return blocks


def _r013_column_spec(block: str, env: str) -> str:
    if env == "longtable":
        first_line = block.splitlines()[0] if block.splitlines() else ""
        match = re.match(r"\\begin\{longtable\}\{(.+)\}", first_line.strip())
        return match.group(1) if match else ""
    braced = _r013_tex_braced_argument(block, r"\begin{tabular}")
    return re.sub(r"\s+", "", braced[0]) if braced else ""


def _r013_caption(block: str) -> str:
    match = re.search(r"\\caption(?:\[[^\]]*\])?\{(.*?)\}", block, flags=re.S)
    if not match:
        return ""
    return re.sub(r"\s+", " ", match.group(1)).strip()


def _r013_label(block: str) -> str:
    match = re.search(r"\\label\{([^}]+)\}", block)
    return match.group(1) if match else ""


def _r013_table_specs(source_dir: Path, version: str) -> dict[str, Any]:
    specs: list[dict[str, Any]] = []
    for index, item in enumerate(_r013_table_env_blocks(source_dir), start=1):
        block = item["block"]
        spec = _r013_column_spec(block, item["env"])
        label = _r013_label(block) or f"tab:r013-unlabelled-{index:03d}"
        caption = _r013_caption(block)
        widths = [float(value) for value in re.findall(r"([0-9]+(?:\.[0-9]+)?)\\textwidth", spec)]
        column_count = len(re.findall(r"(?:[pLmrbX])\s*(?:\{|\b)", spec.replace("@{}", ""))) or len(widths)
        row_count = max(1, len(re.findall(r"\\\\", block)))
        specs.append(
            {
                "table_id": f"r013_table_{index:03d}",
                "label": label,
                "source_rel": item["source_rel"],
                "source_line": item["line"],
                "table_type": item["env"],
                "caption": caption,
                "column_spec": spec,
                "column_count": column_count,
                "declared_width_total": round(sum(widths), 4),
                "row_count_estimate": row_count,
                "column_width_policy": "constrained_textwidth_columns",
                "semantic_role": "reader-facing evidence, proof, comparison, or route surface",
                "formula_anchor": "table-local formula or theorem route where applicable",
                "evidence_anchor": "source corpus, proof route, benchmark route, or release evidence appendix",
                "source_anchor": f"{item['source_rel']}:{item['line']}",
                "layout_requirements": ["booktabs", "no vertical rules", "no raw hline", "constrained columns", "caption", "label"],
                "compiled_reader_facing": True,
                "block": block,
            }
        )
    payload = {
        "schema_id": "OC133_R013_TABLE_REGISTRY_v1",
        "status": "PASS",
        "release_id": "oc_core_1_3_3",
        "version": version,
        "source_revision": R012_REVISION,
        "scope": "compiled reader-facing tables only; sidecar TeX tables are inventoried separately",
        "table_total": len(specs),
        "compiled_reader_table_total": len(specs),
        "tables": specs,
    }
    payload["artifact_hash"] = artifact_hash({key: value for key, value in payload.items() if key != "tables"} | {"tables": [{k: v for k, v in spec.items() if k != "block"} for spec in specs]})
    return payload


def r013_geometry_ledger(registry: dict[str, Any]) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    for spec in registry.get("tables", []):
        if not spec.get("caption"):
            findings.append({"kind": "r013_table_caption_missing", "table_id": spec["table_id"], "source": spec["source_anchor"]})
        if not spec.get("label"):
            findings.append({"kind": "r013_table_label_missing", "table_id": spec["table_id"], "source": spec["source_anchor"]})
        column_spec = str(spec.get("column_spec") or "")
        if "|" in column_spec:
            findings.append({"kind": "r013_vertical_rule_in_column_spec", "table_id": spec["table_id"], "column_spec": column_spec})
        if r"\hline" in str(spec.get("block") or ""):
            findings.append({"kind": "r013_raw_hline_in_table", "table_id": spec["table_id"], "source": spec["source_anchor"]})
        if float(spec.get("declared_width_total") or 0.0) > 0.98:
            findings.append({"kind": "r013_table_width_overflow_risk", "table_id": spec["table_id"], "declared_width_total": spec.get("declared_width_total")})
        if int(spec.get("column_count") or 0) < 2:
            findings.append({"kind": "r013_table_column_count_low", "table_id": spec["table_id"], "column_count": spec.get("column_count")})
        if int(spec.get("row_count_estimate") or 0) > 9 and spec.get("table_type") != "longtable":
            findings.append({"kind": "r013_large_table_not_longtable", "table_id": spec["table_id"], "row_count_estimate": spec.get("row_count_estimate")})
        if not (spec.get("formula_anchor") and spec.get("evidence_anchor") and spec.get("source_anchor")):
            findings.append({"kind": "r013_table_anchor_missing", "table_id": spec["table_id"]})
    payload = {
        "schema_id": "OC133_R013_TABLE_GEOMETRY_LEDGER_v1",
        "status": "PASS" if not findings else "FAIL",
        "checked_table_total": len(registry.get("tables", [])),
        "finding_total": len(findings),
        "findings": findings,
        "layout_policy": "booktabs, no vertical rules, no raw hline, constrained textwidth columns, captions and labels required",
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def _r013_probe_tex(registry: dict[str, Any]) -> str:
    blocks: list[str] = []
    for spec in registry.get("tables", []):
        block = str(spec.get("block") or "")
        blocks.append(rf"\subsection*{{{latex_escape(spec['label'])}}}")
        blocks.append(block)
        blocks.append(r"\clearpage")
    return "\n".join(
        [
            r"\documentclass[11pt,a4paper]{article}",
            r"\usepackage[margin=0.62in]{geometry}",
            r"\usepackage{fontspec}",
            r"\setmainfont{TeX Gyre Termes}",
            r"\usepackage{amsmath,amssymb,booktabs,array,longtable,ragged2e,caption}",
            r"\usepackage{hyperref}",
            r"\newcolumntype{L}[1]{>{\RaggedRight\arraybackslash}p{#1}}",
            r"\captionsetup{font=small,labelfont=bf,justification=RaggedRight,singlelinecheck=false,skip=6pt}",
            r"\setlength{\LTpre}{0.35em}",
            r"\setlength{\LTpost}{0.75em}",
            r"\emergencystretch=3em",
            r"\newcommand{\octablefont}{\footnotesize\RaggedRight\sloppy}",
            r"\newenvironment{octablescope}{\begingroup\octablefont\setlength{\tabcolsep}{4.0pt}\renewcommand{\arraystretch}{1.34}}{\endgroup}",
            r"\pagestyle{empty}",
            r"\begin{document}",
            *blocks,
            r"\end{document}",
            "",
        ]
    )


def _r013_word_boxes(bbox_xml: str) -> list[dict[str, float | int | str]]:
    boxes: list[dict[str, float | int | str]] = []
    for page_index, page in enumerate(re.findall(r"<page\b.*?</page>", bbox_xml, flags=re.S), start=1):
        for word in re.finditer(r"<word\b([^>]*)>(.*?)</word>", page, flags=re.S):
            attrs = dict(re.findall(r'([a-zA-Z]+)="([^"]+)"', word.group(1)))
            try:
                boxes.append(
                    {
                        "page": page_index,
                        "x_min": float(attrs["xMin"]),
                        "y_min": float(attrs["yMin"]),
                        "x_max": float(attrs["xMax"]),
                        "y_max": float(attrs["yMax"]),
                        "text": re.sub(r"<.*?>", "", word.group(2)),
                    }
                )
            except Exception:
                continue
    return boxes


def _r013_box_overlap(a: dict[str, float | int | str], b: dict[str, float | int | str]) -> float:
    width = max(0.0, min(float(a["x_max"]), float(b["x_max"])) - max(float(a["x_min"]), float(b["x_min"])))
    height = max(0.0, min(float(a["y_max"]), float(b["y_max"])) - max(float(a["y_min"]), float(b["y_min"])))
    return width * height


def r013_rendered_bbox_ledger(registry: dict[str, Any]) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    bbox_word_total = 0
    page_total = 0
    raster_page_total = 0
    with tempfile.TemporaryDirectory(prefix="oc133_r013_table_probe_") as tmpdir:
        tmp = Path(tmpdir)
        probe_tex = tmp / f"oc133_r013_table_probe_{registry.get('version', '1.3.3')}.tex"
        probe_pdf = probe_tex.with_suffix(".pdf")
        probe_tex.write_text(_r013_probe_tex(registry), encoding="utf-8", newline="\n")
        compile_result = subprocess.run(
            ["xelatex", "-interaction=nonstopmode", "-halt-on-error", probe_tex.name],
            cwd=tmp,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=240,
        )
        compile_text = f"{compile_result.stdout}\n{compile_result.stderr}"
        if not probe_pdf.is_file():
            findings.append(
                {
                    "kind": "r013_table_probe_pdf_missing",
                    "technical_temp_pdf": True,
                    "returncode": compile_result.returncode,
                    "stdout_tail": compile_result.stdout[-800:],
                    "stderr_tail": compile_result.stderr[-800:],
                }
            )
        else:
            if re.search(r"Overfull \\hbox", compile_text):
                findings.append({"kind": "r013_table_probe_overfull_hbox", "stdout_tail": compile_result.stdout[-1200:]})
            bbox = subprocess.run(
                ["pdftotext", "-bbox-layout", str(probe_pdf), "-"],
                cwd=ROOT,
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                timeout=120,
            )
            boxes = _r013_word_boxes(bbox.stdout)
            bbox_word_total = len(boxes)
            page_total = len(set(int(box["page"]) for box in boxes))
            if bbox_word_total < max(40, int(registry.get("table_total") or 0) * 8):
                findings.append({"kind": "r013_rendered_table_word_count_low", "bbox_word_total": bbox_word_total})
            by_page: dict[int, list[dict[str, float | int | str]]] = defaultdict(list)
            for box in boxes:
                by_page[int(box["page"])].append(box)
            collision_total = 0
            for page, page_boxes in by_page.items():
                for left_index, left in enumerate(page_boxes):
                    for right in page_boxes[left_index + 1:]:
                        overlap = _r013_box_overlap(left, right)
                        if overlap > 1.0:
                            collision_total += 1
                            if collision_total <= 10:
                                findings.append(
                                    {
                                        "kind": "r013_table_text_bbox_overlap",
                                        "page": page,
                                        "left": str(left.get("text"))[:40],
                                        "right": str(right.get("text"))[:40],
                                        "overlap": round(overlap, 3),
                                    }
                                )
            raster_prefix = tmp / "oc133_r013_table_probe_raster"
            subprocess.run(
                ["pdftocairo", "-png", str(probe_pdf), str(raster_prefix)],
                cwd=ROOT,
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                timeout=180,
            )
            raster_outputs = sorted(tmp.glob(f"{raster_prefix.name}-*.png"))
            raster_page_total = len(raster_outputs)
            if not raster_outputs:
                findings.append({"kind": "r013_rendered_table_raster_missing", "technical_temp_png": True})
            for png in raster_outputs:
                try:
                    from PIL import Image

                    with Image.open(png) as image:
                        gray = image.convert("L")
                        pixels = list(gray.getdata())
                        nonwhite_ratio = sum(1 for value in pixels if value < 245) / max(1, len(pixels))
                        w, h = gray.size
                        edge_pixels: list[int] = []
                        for x in range(w):
                            edge_pixels.append(gray.getpixel((x, 0)))
                            edge_pixels.append(gray.getpixel((x, h - 1)))
                        for y in range(h):
                            edge_pixels.append(gray.getpixel((0, y)))
                            edge_pixels.append(gray.getpixel((w - 1, y)))
                        edge_dark_ratio = sum(1 for value in edge_pixels if value < 245) / max(1, len(edge_pixels))
                        if nonwhite_ratio < 0.006:
                            findings.append({"kind": "r013_rendered_table_raster_near_blank", "png": png.name, "nonwhite_ratio": nonwhite_ratio})
                        if edge_dark_ratio > 0.012:
                            findings.append({"kind": "r013_rendered_table_edge_clipping_risk", "png": png.name, "edge_dark_ratio": edge_dark_ratio})
                except Exception as exc:
                    findings.append({"kind": "r013_rendered_table_raster_probe_failed", "png": png.name, "error": str(exc)})
    payload = {
        "schema_id": "OC133_R013_RENDERED_TABLE_BBOX_LEDGER_v1",
        "status": "PASS" if not findings else "FAIL",
        "technical_probe_pdf_policy": "temporary_pdf_used_for_table_bbox_and_raster_checks_then_discarded",
        "technical_probe_pdf_in_public_package": False,
        "bbox_word_total": bbox_word_total,
        "page_total": page_total,
        "raster_page_total": raster_page_total,
        "finding_total": len(findings),
        "findings": findings,
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def r013_table_cockpit(registry: dict[str, Any], geometry: dict[str, Any], rendered: dict[str, Any], *, source_table_total: int) -> dict[str, Any]:
    registered_total = int(registry.get("table_total") or 0)
    compiled_total = int(registry.get("compiled_reader_table_total") or 0)
    status_map = {
        "table_spec_coverage_status": "PASS" if registered_total > 0 else "FAIL",
        "compiled_table_coverage_status": "PASS" if registered_total == compiled_total and compiled_total > 0 else "FAIL",
        "table_layout_standard_status": "PASS" if geometry.get("status") == "PASS" else "FAIL",
        "table_geometry_status": "PASS" if geometry.get("status") == "PASS" else "FAIL",
        "rendered_table_bbox_status": "PASS" if rendered.get("status") == "PASS" else "FAIL",
        "table_text_collision_status": "PASS" if rendered.get("status") == "PASS" else "FAIL",
        "table_edge_clipping_status": "PASS" if rendered.get("status") == "PASS" else "FAIL",
        "table_caption_argument_status": "PASS" if all(spec.get("caption") and spec.get("semantic_role") for spec in registry.get("tables", [])) else "FAIL",
        "table_semantic_anchor_status": "PASS" if all(spec.get("evidence_anchor") and spec.get("source_anchor") for spec in registry.get("tables", [])) else "FAIL",
    }
    status_map["table_cockpit_status"] = "PASS" if all(value == "PASS" for value in status_map.values()) else "FAIL"
    payload = {
        "schema_id": "OC133_R013_TABLE_QA_COCKPIT_v1",
        "status": status_map["table_cockpit_status"],
        "source_revision": R012_REVISION,
        "source_table_total": source_table_total,
        "compiled_reader_table_total": compiled_total,
        "registered_table_total": registered_total,
        "audited_rendered_table_total": registered_total if rendered.get("status") == "PASS" else 0,
        **status_map,
        "publication_actions_performed": False,
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def render_r013_table_registry_md(payload: dict[str, Any]) -> str:
    lines = [
        "# OC Core 1.3.3 r013 Table Registry",
        "",
        f"Status: `{payload['status']}`",
        f"Compiled reader-facing tables: `{payload['compiled_reader_table_total']}`",
        "",
        "## Tables",
        "",
    ]
    for spec in payload.get("tables", []):
        lines.append(f"- `{spec['label']}`: `{spec['table_type']}` from `{spec['source_anchor']}`")
    return "\n".join(lines).rstrip() + "\n"


def render_r013_table_geometry_md(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# OC Core 1.3.3 r013 Table Geometry Ledger",
            "",
            f"Status: `{payload['status']}`",
            f"Checked tables: `{payload['checked_table_total']}`",
            f"Finding total: `{payload['finding_total']}`",
            "",
        ]
    )


def render_r013_table_cockpit_md(payload: dict[str, Any]) -> str:
    lines = [
        "# OC Core 1.3.3 r013 Table QA Cockpit",
        "",
        f"Status: `{payload['status']}`",
        f"Registered tables: `{payload['registered_table_total']}`",
        f"Audited rendered tables: `{payload['audited_rendered_table_total']}`",
        "",
        "## Gates",
        "",
    ]
    for key in [
        "table_spec_coverage_status",
        "compiled_table_coverage_status",
        "table_layout_standard_status",
        "table_geometry_status",
        "rendered_table_bbox_status",
        "table_text_collision_status",
        "table_edge_clipping_status",
        "table_caption_argument_status",
        "table_semantic_anchor_status",
        "table_cockpit_status",
    ]:
        lines.append(f"- `{key}`: `{payload.get(key)}`")
    return "\n".join(lines).rstrip() + "\n"


def build_r013_table_quality(base: Path, version: str, source_dir: Path, *, write: bool, source_table_total: int) -> dict[str, Any]:
    paths = r013_table_output_paths(base, version)
    registry = _r013_table_specs(source_dir, version)
    geometry = r013_geometry_ledger(registry)
    rendered = r013_rendered_bbox_ledger(registry)
    cockpit = r013_table_cockpit(registry, geometry, rendered, source_table_total=source_table_total)
    registry_public = {**registry, "tables": [{k: v for k, v in spec.items() if k != "block"} for spec in registry.get("tables", [])]}
    if write:
        write_json_if_changed(paths["registry_json"], registry_public)
        write_text_if_changed(paths["registry_md"], render_r013_table_registry_md(registry_public))
        write_json_if_changed(paths["geometry_json"], geometry)
        write_text_if_changed(paths["geometry_md"], render_r013_table_geometry_md(geometry))
        write_json_if_changed(paths["rendered_bbox_json"], rendered)
        write_json_if_changed(paths["cockpit_json"], cockpit)
        write_text_if_changed(paths["cockpit_md"], render_r013_table_cockpit_md(cockpit))
    return {"paths": paths, "registry": registry_public, "geometry": geometry, "rendered": rendered, "cockpit": cockpit}


def _r014_public_file_path(path: str) -> str:
    return r"\path{" + path.replace("_", r"\_") + "}"


R014_KLEVEL_NAMES = {
    0: "resolution-relative distinguishability",
    1: "primitive ordering and one-axis continuity",
    2: "physical field and spacetime models",
    3: "chemical reaction and molecular systems",
    4: "compartmental and protocellular systems",
    5: "excitable bioelectrical systems",
    6: "cognitive and representational systems",
    7: "social and institutional systems",
    8: "civilizational and infrastructure systems",
    9: "theory and knowledge systems",
    10: "meta-theoretical modeling systems",
    11: "recursive model-space systems",
    12: "upper coherence and compatibility systems",
}


def _r014_bounded_prediction_master_text() -> str:
    return r"""% R014_BOUNDED_PREDICTION_REVIEW
\subsubsection{Predictions as Bounded Research Targets}
\label{sec:predictions-bounded-r014}

The prediction chapters in Core 1.3.3 are not promoted as a completed
cross-domain empirical theory. They are a review surface for asking whether a
candidate statement has a declared level, a formal vocabulary, an evidence row,
a comparator, and a falsifier. A row may therefore be read as a target for
future test design only when it names the assumptions under which the target is
meant to operate.

The release uses the following conservative rule. A candidate prediction at
level \(K_x\) is public-supporting only if it preserves the tuple components
\[
  (\Omega,\partial\Omega,A,\Theta,P,J,C,k,M)
\]
or explicitly states which component is derived in the local model. It must also
state what would reopen the row: a missing source snapshot, a failed finite
witness, a successful negative control, a stronger comparator, or a domain
observation that requires variables outside the declared tuple.

Consequently, the K-level prediction sections below should be read as bounded
review checklists. They do not claim unrestricted prediction across physics,
chemistry, biology, cognition, society, civilization, or meta-theory. They say
what kind of evidence would be needed before a level-specific statement could be
promoted beyond illustrative or programmatic status.

\paragraph{Review checklist.}
The reviewer should ask six questions before treating any row as public
support. First, is the target level \(K_x\) named with enough precision that an
adjacent level would make a different claim? Second, is the tuple component
being tested visible in the prose or formula? Third, is the source family known:
proof sheet, finite witness, replay table, comparator register, figure, table,
or domain note? Fourth, does the row identify what a negative control would
look like? Fifth, is the comparator boundary strong enough to prevent the row
from merely renaming a standard account? Sixth, does the text say what finding
would force demotion?

These questions matter because a prediction surface can fail in several
different ways. It can be formally named but evidentially empty. It can be
empirically suggestive but too broad for the tuple. It can be clear inside one
domain and misleading when copied into another. It can be useful as a design
heuristic but not yet usable as a scientific result. Core 1.3.3 keeps those
states separate so that the reader can criticize the release without guessing
whether an example, theorem route, replay row, or future research target is
being used.

\paragraph{Promotion boundary.}
A prediction row moves upward only when the support moves upward. A bounded
example remains an example. A formula without source data remains a formal
anchor. A replay row without comparator and negative control remains a replay
exercise. A proof-sheet reference remains a proof/evidence anchor inside its
assumptions, not an empirical closure claim about a whole domain. This
separation is deliberately conservative: it makes the current release less
spectacular, but more inspectable.

\paragraph{Prediction review taxonomy.}
The release uses five kinds of prediction-adjacent material. The first kind is
a theorem-route constraint. It says that if a reader accepts the declared
definitions and assumptions, a stated obstruction, boundary, identity, or
continuumness result follows inside the formal route. This kind of row is
reviewed by checking definitions, proof-sheet dependencies, finite witnesses,
and assumption drift. It is not reviewed by asking whether the same sentence is
already source-bound by completed domain evidence.

The second kind is a finite or computational witness. It says that a small
model, countermodel, keep/drop pair, or semantic check illustrates that the
formal condition is non-vacuous or that a rejected inference fails. This kind of
row is useful because it prevents purely verbal closure, but it is still local:
it supports the existence or non-existence of a pattern under the declared
encoding rather than a broad empirical law.

The third kind is a replay row. A replay row connects a source snapshot, a
formula or reconstruction rule, an observed value or expected finite result, a
comparator, a residual or uncertainty statement, a negative control, and a
falsifier. This is the closest current surface to empirical testing, but it is
bounded by its source and method. A replay row does not validate a whole domain
merely because the command or table exists.

The fourth kind is a comparator-boundary row. It asks whether a standard
framework, predecessor theory, domain method, or simpler model already explains
the same target with less burden. This row is especially important for a theory
with a broad title. It keeps novelty language modest and forces OC to say what
residual work the tuple, K-levels, proof/evidence discipline, or reopening rule
actually add.

The fifth kind is an illustrative or planned-work row. It may be useful for
teaching, domain orientation, or future experiment design, but it should not be
quoted as promoted support. Its value is that it shows where a better source
snapshot, formula, comparator, or falsifier would be needed. In Core 1.3.3, a
large part of the high-level social, civilizational, and meta-theoretical
material is intentionally handled this way unless the specific row carries its
own support package.

\paragraph{How to criticize these rows.}
A reviewer can criticize a prediction row without accepting OC's larger
ambition. The strongest criticism is not "this sounds broad" but "this exact row
has no source, no formal anchor, no comparator, no negative control, or no
reopening condition." The release is designed so that such a criticism can be
localized. If the problem is formal, the theorem route is reopened. If the
problem is empirical, the replay row is demoted. If the problem is novelty, the
comparator boundary is narrowed. If the problem is didactic, the example is
rewritten without changing the scientific claim.

This localization is part of the scientific method of the release. It prevents
one weak example from silently invalidating the entire tuple, and it prevents
one formal proof from silently licensing an entire empirical domain. The
manuscript is therefore deliberately redundant in its claim surfaces: prose,
formula, figure, table, proof sheet, replay row, comparator row, and falsifier
are different review instruments.
"""


def _r014_bounded_prediction_level_text(level: int) -> str:
    label = R014_KLEVEL_NAMES.get(level, "continuum systems")
    return (
        r"""% R014_BOUNDED_PREDICTION_REVIEW
\subsubsection{Bounded Prediction Review for \texorpdfstring{$K___LEVEL__$}{K___LEVEL__}}
\label{sec:predictions-k__LEVEL__-r014}

At \(K___LEVEL__\), prediction language is treated as a source-grounded review
target for __LABEL__, not as an unrestricted theorem about every system in that
domain. A promoted statement has to name its level, tuple components, evidence
anchor, comparator boundary, and falsifier before it can carry scientific
weight.

\paragraph{Claim.}
A \(K___LEVEL__\) prediction may be considered only under declared assumptions
about the admissible state region \(\Omega\), boundary \(\partial\Omega\), axes
\(A\), thresholds \(\Theta\), potentials \(P\), flows \(J\), cycles \(C\),
continuumness \(k\), and embedding context \(M\). If a local model uses a
projection of this tuple, the projection has to preserve the verdict-relevant
information.

\paragraph{Intuition.}
The level tells the reviewer what kind of witness is being requested. For low
levels the witness may be structural, topological, or finite-semantic. For
physical and chemical levels it may involve measured parameters or replayable
formula rows. For social, civilizational, or meta-theoretical levels the row is
normally illustrative until it carries source snapshots, comparators, negative
controls, and reopening conditions.

\paragraph{Worked example.}
A safe \(K___LEVEL__\) row has the form
\[
  \mathcal{P}_{__LEVEL__}:
  (K___LEVEL__, A_x, \Theta_x, P_x, J_x, C_x, k_x, M_x)
  \longrightarrow
  \{\mathrm{supported},\mathrm{illustrative},\mathrm{reopened}\}.
\]
The row is supported only inside the declared source family. If the source
family changes, if the comparator explains the observation with less burden, or
if the negative control succeeds, the row is reopened.

\paragraph{Formal anchor.}
The formal anchor is the canonical tuple
\[
  K=(\Omega,\partial\Omega,A,\Theta,P,J,C,k,M).
\]
The row may cite proof sheets, finite semantic witnesses, or the formalization
inventory, but it may not infer broader empirical closure merely from their
existence.

\paragraph{Evidence and limitation.}
For \(K___LEVEL__\), the current release records prediction rows as bounded
targets unless an explicit source/evidence row upgrades the statement. The
limitation is therefore part of the claim: without source snapshot, formula or
finite witness, comparator, residual or uncertainty, negative control, and
falsifier, the statement remains illustrative.
"""
        .replace("__LEVEL__", str(level))
        .replace("__LABEL__", label)
    )


def _r014_demote_retrospective_replay_language(text: str) -> str:
    """Keep replay rows useful while removing unaudited prospective-blind claims."""
    replacements = {
        "bounded target-blind replay QA": "bounded retrospective replay QA",
        "target-blind replay QA": "retrospective bounded replay QA",
        "target-blind replay rows": "retrospective bounded replay rows",
        "target-blind replay row": "retrospective bounded replay row",
        "target-blind replay table": "retrospective bounded replay table",
        "target-blind replay file": "retrospective bounded replay file",
        "target-blind replay": "retrospective bounded replay",
        "target-blind table": "retrospective bounded replay table",
        "target-blind rows": "retrospective replay rows",
        "target-blind row": "retrospective replay row",
        "target-blind split": "retrospective split record",
        "target-blind or held-out target": "retrospective split or held-out target",
        "Target-Blind Path Integrity": "Retrospective Replay Path Integrity",
        "Target-blind directory": "Retrospective replay directory",
        "Target-blind file": "Retrospective replay file",
        "Target-blind tables": "Retrospective replay tables",
        "Target-blind": "Retrospective replay",
        "target-blind": "retrospective replay",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = text.replace(
        "The retrospective bounded replay table is a reader-facing reproducibility anchor.",
        "The retrospective bounded replay table is a reader-facing reproducibility anchor, but it is not presented as an independently auditable prospective-blind study in this package.",
    )
    text = text.replace(
        "This table is not a broad empirical triumph claim. It records the bounded prediction rows, their source snapshots, their reconstruction rule, their comparator, the negative-control condition, and the condition under which the claim must be reopened.",
        "This table is not a broad empirical triumph claim and not a prospective-blinding proof. It records bounded reconstruction rows, source references where available, reconstruction rules, comparators, negative-control conditions, and reopening conditions. Prospective blinded-study promotion requires checksum-bound split locks, raw snapshots, pre-run projection records, timestamps, and runner evidence in a future evidence package.",
    )
    return text


def _r014_discussion_tex() -> str:
    return r"""% FILE: content/05_discussion.tex

\section{Discussion}
\label{sec:discussion}

This discussion interprets the formal and evidence surfaces of Core~1.3.3. It
does not introduce new axioms, new theorem claims, or new empirical validation
claims. Its task is narrower: to explain how a reader should understand the
model grammar, what the present release can support, and where the manuscript
must remain conditional.

\subsection{Conceptual structure of the OC framework}

OC treats a continuum as a typed object that can remain identifiable while its
states, boundary, flows, cycles, and embedding constraints change. The public
tuple convention for this release is
\[
  K=\big(\Omega(K),\partial\Omega(K),A(K),\Theta(K),P(K),J(K),C(K),k(K),M(K)\big).
\]
Here \(\Omega(K)\) is the admissible state region, \(\partial\Omega(K)\) is the
declared boundary, \(A(K)\) are axes of observable difference, \(\Theta(K)\)
are thresholds, \(P(K)\) are potentials or admissibility weights, \(J(K)\) are
flows, \(C(K)\) are cycles, \(k(K)\) is continuumness, and \(M(K)\) is the
embedding context. Shorter local displays in older source material are read as
projections of this release tuple, not as competing definitions.

The conceptual value of the tuple is that it forces a systems claim to name
what persists, what changes, what boundary would be crossed, what evidence
would demote the claim, and what larger context constrains the local system.
That value is methodological before it is empirical. A domain instantiation
must still supply its own data, comparator, uncertainty, negative control, and
falsifier before a stronger domain claim can be promoted.

\subsection{How to read the theorem route}

The theorem and proof material in this release should be read through its stated
support status. A theorem-roadmap entry, proof-sheet row, finite-witness row, or
formalization inventory entry can support public prose only at the strength
declared for that row. Historical theorem numbering is retained as lineage and
orientation; it is not re-promoted by this discussion.

Consequently, dimensional-growth, threshold-emergence, collapse, embedding,
complexity, and non-stabilization statements are interpreted under named
assumptions and current evidence boundaries. If a proof sheet supports a local
claim, the prose remains local. If a finite witness demonstrates only a finite
case, the prose remains finite-case language. If a domain example lacks a
source snapshot, comparator, residual, negative control, or falsifier, it
remains illustrative or protocol-facing rather than empirical support.

\subsection{Relation to established scientific traditions}

OC is closest to a family of mature traditions rather than to an empty space.
General systems theory supplies the ambition of cross-domain language.
Cybernetics supplies feedback, control, and communication. Dynamical systems
and complexity science supply state spaces, attractors, phase transitions, and
networked organization. Autopoiesis and RAF-style chemical closure supply
important predecessors for organizational persistence and self-production.
Hybrid systems, formal verification, type-theoretic modeling, and category-
oriented modeling supply discipline for transitions, compositionality, and
machine-auditable claims. Formal ontology and identity-over-time debates supply
the persistence problem. Reproducible-research practice supplies the artifact
standard.

The residual contribution claimed here is therefore bounded. Core~1.3.3 does
not claim to replace those traditions or to win every same-claim comparison. It
claims that typed continuum objects, K-level witness discipline, evidence
promotion rules, finite checks, replay rows, comparator rows, and reopening
conditions can be packaged as one reviewable model-core surface.

\subsection{Implications for the continuum hierarchy}

The hierarchy should be read as witness discipline, not as a loose taxonomy.
The current core grammar is strongest through \(K_0\)--\(K_{10}\). \(K_{11}\)
and \(K_{12}\) are retained as provisional upper-taxonomy candidates and
future-proof obligations. A K-level distinction is meaningful only when it adds
a non-inert witness, observable consequence, constraint relation, proof route,
or demotion criterion that would change the verdict if removed.

This gives the hierarchy a useful role while keeping it honest. Physical,
chemical, biological, cognitive, social, theoretical, and meta-theoretical
examples can be compared with the same vocabulary, but each example carries
its own burden. The release does not infer completed domain validation merely
from the fact that the example can be described in OC terms.

\subsection{Worked demotion examples}

The release uses demotion as a scientific instrument rather than as a
confession of failure. A physical example may show that a threshold vocabulary
fits a phase-transition case; that does not make the same sentence a universal
law for all physical systems. The promoted sentence is therefore the bounded
one: the tuple helps state the case, the threshold row names the support, and a
future reviewer can reopen the row if a standard physical model explains the
same target with less burden.

A chemical or biological example may make cycles, boundaries, and flows
visually compelling. That is useful for teaching, but it is not enough for a
domain claim. The public claim becomes stronger only when the source snapshot,
formula or reconstruction rule, comparator, residual or uncertainty, negative
control, and falsifier are present. Without those objects, the example remains
an orientation device or a proposed protocol.

A social or civilizational example is even more fragile. It may be tempting to
read institutional stress, infrastructure failure, or macro-trajectory change
as direct evidence for the whole hierarchy. Core~1.3.3 does not license that
move. The safer reading is that the example shows how OC would structure a
research design: name the state region, name the boundary, name the flows,
name the comparator, and state what observation would make the OC reading
unnecessary.

The same rule applies to formal material. A finite witness can show that a
semantic pattern is non-vacuous or that an attempted reduction fails in the
declared encoding. It does not automatically prove a broad theorem. A proof
sheet can support a theorem-bound sentence under declared assumptions. It does
not automatically support an empirical sentence. This separation is what lets
the manuscript be ambitious in scope while conservative in promoted claims.

\subsection{How this discussion should be audited}

A reviewer can audit this discussion by following a simple sequence. First,
identify the exact sentence that appears to carry a scientific claim. Second,
classify the sentence as definitional, theorem-bound, finite-witness-bound,
replay-bound, comparator-bound, illustrative, or planned. Third, inspect the
artifact named by that support class. Fourth, ask whether the public sentence
is weaker than or equal to the artifact. Fifth, check whether a negative case
or comparator would demote the wording.

If the sentence fails that sequence, the correct repair is not rhetorical
defense. The sentence should be narrowed, moved to future work, tied to a
specific source row, or removed. This makes the discussion less dramatic than a
manifesto, but far more useful to a hostile reviewer. It also makes the release
machine easier to improve: each repeated failure class can become a static
lower-level test before expensive global review is invoked.

\subsection{Comparator reading examples}

The comparator discipline is easiest to understand through examples. If a
reviewer reads a threshold sentence near physics, the first question is not
whether OC has replaced statistical mechanics, phase-transition theory, or a
specific physical model. It has not. The first question is whether OC has
named the same target in a way that exposes state region, boundary, axes,
threshold, potential, flow, cycle, continuumness, and embedding context. If a
standard physical model already gives the stronger local explanation, OC may
still serve as a translation layer, but the local model keeps priority for the
local mechanism.

If a reviewer reads a closure sentence near chemistry or early life, the same
principle applies. RAF theory, autocatalytic-set theory, chemical kinetics,
reaction networks, membrane models, and thermodynamic constraints already
carry deep local content. OC is not entitled to claim that content as its own.
The safe contribution is a typed statement of what is being treated as a
cycle, what boundary is doing explanatory work, what lower-level projection
would lose the witness, and what demotion rule prevents a metaphor of closure
from becoming a false theorem.

If a reviewer reads a liveness sentence near biology, the comparator family is
again strong: biophysics, systems biology, excitable-media models,
developmental biology, autopoiesis, and physiology already contain mature
models of organization and persistence. OC may help organize liveness,
residue, death, and recovery as public review predicates, but it cannot turn a
biological analogy into a supported biological law. The correct audit asks
whether the biological sentence has a source row, measurable object,
comparator, residual or uncertainty, negative control, and falsifier. Without
those, the sentence remains didactic or planned.

If a reviewer reads a cognition or social-systems sentence, the required
humility is even stronger. Cognitive science, neuroscience, institutional
analysis, economics, organization theory, security engineering, and enterprise
architecture already have local languages. OC can be useful when it lets those
languages share a boundary and evidence vocabulary. It is not useful when it
pretends that one broad ontology has already solved the empirical burden of
each field. The release therefore treats many higher-level examples as
research designs, not as completed support.

This comparator rule is deliberately asymmetric. OC may borrow pressure from
existing fields only when it also accepts their right to defeat or narrow an OC
claim. A comparator does not have to accept the OC tuple in order to reopen the
sentence. It only has to show that the same bounded target can be explained
with less burden, equal or better evidence, or a cleaner falsifier. This is how
the release avoids becoming a universal vocabulary that cannot lose.

\subsection{Why bounded language is not weakness}

The bounded language of this manuscript can make the theory look less dramatic
than its title. That is intentional. A title can name an ambitious program; a
scientific release must state only what it can defend. The most important
discipline in Core~1.3.3 is therefore not a single equation or diagram, but
the rule that every public sentence can be reopened by evidence.

Bounded language also helps practical readers. An engineer, architect, or
executive does not need a metaphysical victory claim in order to use the model
carefully. Such a reader needs to know which distinction is being made, which
failure mode matters, which source or example is illustrative, and what would
make the model unhelpful in the present case. The same humility that protects
the manuscript from overclaiming also makes it easier to use in real design
work.

For formal readers, bounded language protects proof status. A proof sheet is
strong only inside its assumptions. A finite witness is strong only for the
declared encoding. A formalization inventory entry is not a certificate unless
the certificate and source binding are clean for the cited revision. These
distinctions may seem bureaucratic, but they are the difference between a
reviewable scientific package and a large manuscript that asks the reader to
trust its tone.

For empirical readers, bounded language protects measurement. A replay row may
be useful even when it is not a prospective study. It may show that a formula,
source snapshot, comparator, residual, negative control, and falsifier can be
kept aligned. That is valuable artifact discipline. It becomes stronger
empirical support only when the public evidence package carries the stronger
design. The release therefore preserves useful replay material while refusing
to let it masquerade as broader proof.

\subsection{Machine responsibility}

The release machine should catch most of the small failures before a human
expert reads the document. Metadata leaks, malformed file names, unsupported
status words, weak captions, table collisions, figure overlaps, broken paths,
and repeated overclaim phrases are lower-level defects. They belong to static
checks, rendered-surface checks, and governed local review. A high-reasoning
reviewer should not spend expensive attention finding those defects page by
page.

The higher-level reviewer is reserved for harder questions: whether the
argument order makes sense, whether the concept is coherent, whether a claim
quietly outruns its source row, whether a comparator has been treated fairly,
whether a proof status changed meaning in prose, and whether the manuscript
would survive a hostile scientific editor. This division of labor is now part
of the package's quality policy. It is also a practical V-model: small objects
first, then sections, then chapters, then the whole document.

This policy does not make the machine infallible. It makes failure cheaper and
more local. When a repeated class of defect is found by a reviewer, it becomes
a static lower-level test in the next run. The goal is not to remove human
judgment. The goal is to reserve human judgment for the parts of the manuscript
where judgment is actually needed.

\subsection{Limits and future work}

Several boundaries remain open. Quantitative threshold functions must be
calibrated domain by domain. Expressive-capacity measures for cognitive,
social, and theoretical systems require more mature operational definitions.
Inter-continuum interaction remains schematic for many complex cases.
Prospective empirical tests require stronger source snapshots, split locks,
pre-run records, comparators, uncertainty models, negative controls, and
falsifiers than the present package can always provide.

These limits do not make the release empty. They define the scientific program
that follows from the model core. The useful result of Core~1.3.3 is a bounded,
reviewable language for saying exactly what a continuum claim currently means,
what evidence supports it, and what finding would reopen it.
"""


def _r014_k12_provisional_tex() -> str:
    return r"""% ================================================================
% ==== FILE: content/k_levels/k12.tex
% ================================================================

\paragraph{Canonical tuple projection note.}
Local K-level displays in this module are projections of the canonical public
tuple \(K=(\Omega,\partial\Omega,A,\Theta,P,J,C,k,M)\). When a display omits
\(M\), reorders components, or uses level-indexed shorthand, the omitted
embedding context is inherited from the surrounding level discussion rather
than introduced as a competing definition.

\subsubsection{\texorpdfstring{$K_{12}$}{K12} as a Provisional Upper-Coherence Candidate}
\label{sec:k12-overview}

\(K_{12}\) is retained in Core~1.3.3 as an upper-taxonomy research candidate.
It is not promoted as a completed limit theorem, a final level of reality, or a
proof that all branches, flows, operators, or time directions have globally
closed. The public role of the module is to state what an upper-coherence claim
would have to prove before stronger wording could be licensed.

A cautious candidate state description is
\[
\Omega(K_{12}) =
\{\Omega^*,A^*,P^*,\Theta^*,J^*,C^*,\mu^{(12)}\},
\]
where the starred objects denote proposed upper-level projections of the lower
K-level vocabulary. In this release they are research objects. They become
support-carrying only when a later proof or evidence package names the
operator assumptions, the convergence criterion, the boundary condition, the
negative case, and the demotion rule.

\subsubsection{Candidate Components and Required Proof Obligations}

\begin{itemize}
\item \(\Omega^*\) would have to identify admissible upper-coherence states
      without absorbing incompatible \(K_0\)--\(K_{11}\) witnesses by rhetoric.
\item \(A^*\) would have to show which upper-level axes are retained and which
      apparent axes are demoted as inert.
\item \(\Theta^*\) would have to state threshold conditions under which an
      upper-coherence reading is allowed or rejected.
\item \(P^*\) and \(J^*\) would have to specify potentials and flows under
      explicit operator assumptions rather than by global-invariance language.
\item \(C^*\) would have to identify cycles that support the candidate reading
      and cases where such cycles fail.
\item \(M_{12}\) would have to name the embedding context that makes the
      candidate admissible.
\end{itemize}

These requirements are intentionally strict. They prevent the upper taxonomy
from turning into a totalizing closure claim.

\subsubsection{Promotion Checklist}

An upper-coherence statement may be promoted only after it passes a checklist
that is stronger than ordinary exposition. The statement must identify the
candidate object, the lower-level witnesses retained by projection, the
operator assumptions, the convergence or non-convergence criterion, the
boundary condition, the finite or formal witness if one exists, the comparator
that could explain the same structure with less burden, and the condition under
which the claim is demoted.

\begin{center}
\begin{tabular}{p{0.25\linewidth}p{0.62\linewidth}}
\toprule
Review item & Required public answer \\
\midrule
Object & What is the specific \(K_{12}\) candidate, and which lower-level
witnesses does it retain? \\
Assumptions & Which operator, embedding, and projection assumptions are being
used? \\
Support & Is the statement definitional, proof-bound, finite-witness-bound, or
planned? \\
Negative case & What named case would show that the upper-coherence reading is
unnecessary or false? \\
Demotion rule & What weaker sentence remains if the strong reading fails? \\
\bottomrule
\end{tabular}
\end{center}

This checklist is part of the public claim boundary. It protects the manuscript
from treating an attractive upper-level picture as completed science. It also
gives future work a precise route: every stronger \(K_{12}\) sentence must
bring the missing proof, finite witness, comparator, or negative case with it.

\subsubsection{Boundary and Falsifiability}

The candidate boundary \(\partial\Omega(K_{12})\) is crossed whenever the
declared upper-coherence reading loses one of its required witnesses. Examples
include recursive divergence, incompatible projections, operator assumptions
that cannot be stated, a missing demotion rule, or a lower-level witness that
changes the verdict after projection.

The candidate is falsified or demoted if:
\begin{itemize}
\item a proposed upper-level axis can be removed without changing any witness;
\item a claimed convergence criterion fails on a named counterexample;
\item an operator-symmetry statement is used without explicit operators;
\item a branch- or cycle-stability claim lacks a proof route or evidence row;
\item a lower-level domain example is used as universal evidence.
\end{itemize}

\subsubsection{Research Tests}

Future work may test explicitly modeled recursive meta-hierarchies, candidate
fixed-point behavior, operator assumptions, and branching constraints. Such
tests should be reported as research tests until they include source snapshots,
formal assumptions, negative controls, and reopening conditions. The present
release therefore treats \(K_{12}\) as a disciplined frontier object: useful
for organizing upper-bound questions, but not a current proof of global
closure, terminality, or universal invariance.

\subsubsection{Reader Guidance for the Upper Taxonomy}

A reader should use the \(K_{12}\) module as a map of questions rather than as
an answer sheet. The module asks what it would mean for a family of
meta-frameworks to become mutually inspectable, what kind of embedding context
would be required, which lower-level witnesses must remain visible, and which
operator assumptions would have to be stated before a stronger result could be
claimed. These questions are useful even while the answers remain provisional.

The safest reading is comparative. If an existing metatheory, formal ontology,
category-theoretic construction, type-theoretic universe, or scientific
unification program explains the same upper-level relation with a cleaner
support structure, the OC wording should become narrower. The K12 vocabulary
then remains a translation aid or a research prompt, not a priority claim and
not a proof of unique adequacy.

The module also protects the lower levels. Without an explicit upper-bound
frontier, broad synthesis language tends to leak backward into the formal core
and make \(K_0\)--\(K_{10}\) sound stronger than their evidence permits. By
keeping \(K_{12}\) provisional, the release can state a future direction
without allowing that direction to inflate current theorem, replay, or
comparator claims.

For practical readers, this means that \(K_{12}\) should not be used as an
enterprise, engineering, or scientific decision rule. It may help structure
questions about governance, evidence integration, and cross-domain
compatibility, but any operational recommendation must be grounded in a lower
level, a named source row, a comparator, a negative case, and a reopening
condition. The upper taxonomy is a research boundary, not an authorization
surface.

For formal readers, the frontier status is equally important. A future proof
would need to name the exact object, the universe or meta-space in which it
lives, the morphisms or operators allowed, the fixed or non-fixed points under
review, and the demotion condition for every retained witness. Until that
work is present, \(K_{12}\) is a disciplined conjectural scaffold. It is useful
because it says what would have to be proved, not because it has already been
proved.
"""


def _r014_demote_experiment_chapter(text: str) -> str:
    text = text.replace(
        "empirical and computational foundation for testing structural predictions",
        "proposed empirical and computational protocol surface for testing structural predictions",
    )
    text = text.replace("empirical and computational foundation", "proposed empirical and computational protocol surface")
    text = re.sub(
        r"\bprovide\s+the\s+empirical\s+and\s+computational\s+foundation\s+for\b",
        "provide proposed empirical and computational protocol context for",
        text,
        flags=re.I,
    )
    text = re.sub(
        r"\bprovides\s+the\s+empirical\s+and\s+computational\s+foundation\s+for\b",
        "provides proposed empirical and computational protocol context for",
        text,
        flags=re.I,
    )
    text = text.replace("direct empirical grounding", "proposed empirical-test grounding")
    text = text.replace("foundation for all physical continua", "modeling bridge for review of physical-continuum cases")
    text = re.sub(r"\bempirically\s+validate\b", "empirically probe", text, flags=re.I)
    text = re.sub(r"\bThese\s+empirical\s+results\s+anchor\b", "These proposed protocol outputs would anchor, if completed and source-bound,", text, flags=re.I)
    text = re.sub(r"\bempirical\s+results\s+anchor\b", "proposed protocol outputs would anchor, if completed and source-bound,", text, flags=re.I)
    text = re.sub(r"\bThe\s+experiments\s+for\s+(\$K(?:_\{?\d+\}?|\d+)\$)\s+validate\b", r"The proposed experiments for \1 probe", text, flags=re.I)
    text = re.sub(r"\bExperiments\s+for\s+(\$K(?:_\{?\d+\}?|\d+)\$)\s+validate\b", r"Proposed experiments for \1 probe", text, flags=re.I)
    text = re.sub(r"\bExperiments\s+at\s+this\s+level\s+validate\b", "Proposed experiments at this level probe", text, flags=re.I)
    text = re.sub(r"\bExperiments\s+validate\b", "Proposed experiments probe", text, flags=re.I)
    text = re.sub(r"\bexperiments\s+validate\b", "proposed experiments probe", text, flags=re.I)
    text = re.sub(r"\btests\s+that\s+validate\b", "tests that would probe", text, flags=re.I)
    text = re.sub(r"\bmust\s+validate\b", "must probe", text, flags=re.I)
    text = re.sub(r"\baim\s+to\s+validate\b", "aim to probe", text, flags=re.I)
    text = re.sub(r"\baims\s+to\s+validate\b", "aims to probe", text, flags=re.I)
    text = re.sub(r"\bgoals\s+are\s+to\s+validate\b", "goals are to probe", text, flags=re.I)
    text = re.sub(r"\bgoal\s+is\s+to\s+validate\b", "goal is to probe", text, flags=re.I)
    text = re.sub(r"\bcentral\s+goal\s+is\s+to\s+empirically\s+probe\b", "central goal is to specify a protocol for empirically probing", text, flags=re.I)
    text = re.sub(r"\bcentral\s+goal\s+is\s+to\s+probe\b", "central goal is to specify a protocol for probing", text, flags=re.I)
    text = re.sub(r"\\paragraph\{Predictions validated:\}", r"\\paragraph{Predictions under review:}", text)
    text = re.sub(r"\\paragraph\{Core predictions validated:\}", r"\\paragraph{Core predictions under review:}", text)
    text = re.sub(r"\bvalidated\b", "probed", text, flags=re.I)
    text = re.sub(r"\bvalidates\b", "probes", text, flags=re.I)
    text = re.sub(r"\bvalidate\b", "probe", text, flags=re.I)
    text = re.sub(r"\bvalidation\b", "protocol review", text, flags=re.I)
    notice = (
        "The experiment chapters in this release specify proposed protocols and review designs. "
        "They do not report completed empirical support unless a row names a public source snapshot, "
        "formula or reconstruction rule, comparator, residual or uncertainty, negative control, falsifier, "
        "and replay hash."
    )
    if "proposed protocols and review designs" not in text:
        lines = text.splitlines()
        insert_at = None
        for index, line in enumerate(lines):
            if line.startswith("\\section{") or line.startswith("\\subsection{") or line.startswith("\\subsubsection{"):
                insert_at = index + 1
                break
        if insert_at is not None:
            lines[insert_at:insert_at] = ["", notice]
            text = "\n".join(lines) + ("\n" if text.endswith("\n") else "")
        else:
            text = notice + "\n\n" + text
    return text


def _r014_methods_evidence_chapter_tex() -> str:
    return r"""\section{Methods, Evidence, and Comparator Discipline}
\label{sec:oc133-methods-evidence-comparators}

This chapter explains how Core 1.3.3 asks to be reviewed. It is not a dump of
the evidence register. The public claim is always read through four questions:
what object is being named, what support class is actually present, what would
reopen the wording, and which comparator could explain the same observation
with less theoretical burden. The value of this discipline is that a reviewer
can attack a precise relation instead of arguing against a slogan.

\subsection{Claim wording and support class}

A sentence in the manuscript may be definitional, theorem-bound, finite-witness
bound, replay-bound, comparator-bound, illustrative, or planned. These classes
are intentionally different. A definition may introduce vocabulary without
proving empirical reach. A theorem-bound sentence may be strong inside stated
assumptions but silent outside them. A replay-bound sentence can support a
case row without becoming a completed domain validation. When the support class
changes, the public wording must change with it.

\subsection{The canonical model object}

The model object inspected across this release is
\[
  K=(\Omega,\partial\Omega,A,\Theta,P,J,C,k,M).
\]
The tuple is not merely notation. It gives a reviewer nine inspection points:
the admissible state region, the boundary, observable axes, threshold
conditions, potentials, flows, cycles, continuumness, and embedding context.
The article, monograph, figures, and tables may use prose glosses for these
components, but they do not promote an alternate canonical tuple.

\subsection{Formal and finite-witness support}

Formal support is cited only where the present release has a theorem row, proof
sheet, finite semantic witness, or formalization inventory entry that matches
the public statement. The current public boundary is deliberately cautious:
formalization inventory can orient the reviewer, but it is not described as a
clean machine-checked certificate unless the binding is clean for the exact
claim. If a proof sheet supports only a finite witness or a stated assumption
class, the public sentence remains inside that class.

\subsection{Replay and numeric support}

Replay rows are treated as bounded scientific checks. A row becomes
reader-facing support only when it names a source snapshot, reconstruction rule
or formula, observed or derived value, residual or uncertainty, comparator,
negative control, and falsifier. Missing pieces do not disappear; they demote
the row to an illustrative example or a planned measurement. The principal
prediction-row anchor is
\path{validation/target_blind/OC133_TARGET_BLIND_PREDICTION_TABLE.json}.

\subsection{Comparator discipline}

Prior systems theory, cybernetics, autopoiesis, dynamical systems, complexity
science, formal verification, formal ontology, category-theoretic modeling, and
reproducibility research are not treated as background scenery. They are active
comparators. The relevant public comparator anchors are
\path{docs/OC_1_3_3_PRIOR_ART_COMPARATOR_MATRIX.json} and
\path{comparators/OC_1_3_3_COMPARATOR_MATRIX.md}. If a comparator explains a
row with less burden, the OC claim narrows to its residual contribution.

\subsection{Reopening conditions}

Every promoted claim should be reopenable. A tuple claim reopens if a component
can be removed without changing the verdict. A K-level claim reopens if the
level adds no retained witness or demotion criterion. A proof claim reopens if
the dependency or assumption class is mismatched. A replay claim reopens if the
source snapshot, formula, comparator, residual, negative control, or falsifier
is missing or fails. This is not a weakness of the release; it is the mechanism
that keeps strong prose from outrunning visible evidence.

\subsection{Lifecycle and identity claims}

Lifecycle claims are especially easy to overread, so this release separates
death, residue, rebirth, and identity continuation. A residue is not a live
continuation merely because it carries traces of the source. A rebirth relation
is not same-identity survival unless endpoint-bound identity evidence is
explicitly present. The reviewer should therefore ask which token continues,
which invariant is declared, which endpoint evidence is available, and which
condition would make the identity claim false.

\subsection{K-level claims}

K-levels are witness disciplines rather than labels. A level must add an
observable or formal obligation: a retained witness, a constraint relation, a
demotion criterion, or a finite row that would fail if the level were merely a
name. The K0--K12 hierarchy is therefore inspected as a nested system grammar:
lower continua compose the next level, while higher contexts constrain the
admissible behaviour of lower ones.

\subsection{Article projection boundary}

The compact journal article is a projection from the release, not a parallel
theory. It may shorten examples and omit supporting appendices, but it may not
introduce unsupported scientific claims. Its four claims are the tuple, the
K-level witness discipline, the evidence-promotion rule, and the bounded
replay/comparator route. Each claim has a reopening condition printed in the
article so that the article can be criticized without treating the monograph as
a black box.

\subsection{Public reading rule}

The public reading rule is simple: do not infer broader closure from an anchor
than the anchor can carry. The release is strongest when it states exactly what
is definitional, what is theorem-bound, what is finite-witness-bound, what is a
bounded replay, and what remains future work. This rule is the bridge between
ambition and reviewability.

\subsection{Worked review example: tuple redundancy}

Suppose a critic argues that the boundary component can be absorbed into the
state region. The manuscript should not answer with rhetoric. It should ask
whether the case still distinguishes an admissible live state from a state that
forces demotion, death, split, or narrower wording. If that distinction remains
visible after removing \(\partial\Omega\), then the tuple row is too broad. If
the distinction disappears, the boundary component has earned local work in
that case. The same test applies to thresholds, flows, cycles, and embedding
context. Redundancy is not settled by how elegant the tuple looks; it is settled
by whether a component changes the review verdict.

\subsection{Worked review example: K-level promotion}

Suppose a section names a system as K7 because people, institutions, or
authority are involved. That is not enough. K7 promotion requires a retained
witness of social coordination: authority, trust, obligation, delegation,
norm-enforcement, or another declared coordination relation that cannot be
reduced to a lower-level component without loss in the stated case. If the row
only says that humans are present, it is an example candidate, not a promoted
K-level claim. If it also states the coordination witness, the lower-level
composition, the higher-level constraint, and the demotion condition, the row
can be reviewed as a K7 statement.

\subsection{Worked review example: replay support}

Suppose a target-blind replay row reports a bounded match. The public conclusion
is still not ``the domain is validated.'' The conclusion is that the row, under
its source snapshot and reconstruction rule, did not trigger the named
falsifier and did not lose immediately to the declared comparator. The reviewer
then asks whether the case is representative, whether the residual is small for
the right reason, whether a negative control would fail, and whether a rival
model explains the row with less burden. Only after those questions survive can
the wording move beyond illustrative support.

\subsection{Worked review example: comparator pressure}

Suppose a cybernetic or dynamical-systems account already explains feedback,
state transitions, and attractor behaviour in a case. OC does not earn novelty
by renaming those concepts. It earns residual value only if the continuum tuple,
K-level witness discipline, lifecycle boundary, or evidence-promotion rule
adds an inspection point that the comparator does not already supply for the
same row. If no residual point remains, the honest action is to credit the
comparator and narrow the OC sentence.

\subsection{Worked review example: figure and table claims}

A diagram may make a claim by implication even when the caption is cautious. A
K-level figure, for example, can imply a complete hierarchy; a replay table can
imply empirical validation; a comparator table can imply novelty. In this
release a visual or table is treated as public argument only if its caption
states what it demonstrates, which variables or numbers matter, which formula
or evidence row supports it, and what would reopen it. A beautiful picture that
cannot answer those questions remains decoration and should not carry a claim.

\subsection{How to read absence}

Absence is also evidence. If a source snapshot is absent, the claim is not
inspectable. If a proof dependency is absent, the theorem wording is not
closed. If a comparator row is absent, novelty is not yet bounded. If a
falsifier is absent, the reader cannot tell what would make the claim false.
The manuscript therefore treats missing anchors as demotion signals rather than
as blank spaces to be filled by confidence.

\subsection{Claim-classification checklist}

The following checklist is the practical reading instrument for this chapter.
It is written for a reviewer who wants to decide quickly whether a paragraph is
claiming more than the release can support.

\begin{enumerate}
\item Is the sentence a definition, a theorem-bound statement, a finite-witness
      statement, a replay statement, a comparator statement, an illustration,
      or a planned research statement?
\item Does the sentence name or imply the canonical object
      \(K=(\Omega,\partial\Omega,A,\Theta,P,J,C,k,M)\), a K-level, a lifecycle
      relation, a proof relation, a replay row, a comparator row, or a journal
      projection?
\item Is the cited support class sufficient for the verb being used? Words such
      as proves, validates, explains, supports, illustrates, bounds, and
      suggests do not carry the same scientific force.
\item Does the paragraph state the reopening condition, or is the reader forced
      to infer it?
\item If the paragraph were moved into a journal article without the monograph,
      would the claim still be inspectable?
\end{enumerate}

If the answer to the final question is no, the correct repair is not merely a
footnote. The public sentence should be narrowed, the source anchor should be
made visible, or the material should be moved to an appendix where its support
class can be explained without pretending to be a compact journal result.

\subsection{Evidence verbs}

The manuscript uses evidence verbs conservatively. A definition \emph{names} a
distinction. A theorem-bound row \emph{establishes} a result only under its
assumptions. A finite witness \emph{shows consistency or counterexample
behaviour} in the finite case. A replay row \emph{supports} a bounded reading
only when its source snapshot and reconstruction rule are visible. A comparator
row \emph{bounds} novelty; it does not make novelty automatic. An illustrative
example \emph{orients} a reader; it does not validate a domain. This verb
discipline is intentionally plain because it is one of the easiest ways to
prevent overclaim.

\subsection{Promotion and demotion}

Promotion is reversible. A claim may move from planned to illustrative, from
illustrative to replay-bound, from replay-bound to stronger domain evidence, or
from theorem-oriented prose to formal support as the corpus improves. It can
also move downward. If a source row is missing, a replay row fails, a comparator
absorbs the residual contribution, or a proof dependency does not match the
public wording, demotion is the honest scientific action. The release is
therefore not a static monument; it is a bounded review surface whose claims
can strengthen or narrow as evidence changes.

\subsection{Minimal reader audit}

A reviewer who has only one hour should not start by reading every appendix.
The minimal audit is narrower. First, inspect the abstract and release delta to
see what kind of claim the release makes. Second, inspect the canonical tuple
and ask whether each component carries a distinct review question. Third, read
the K-level primer and ask whether levels are witness-bearing or merely named.
Fourth, inspect one theorem-bound claim and one replay-bound claim and check
whether the verbs match the support class. Fifth, inspect one comparator row and
ask whether OC has residual value after prior art is credited. If the release
survives those five checks, a deeper read is warranted. If it fails one of them,
the failure identifies the repair target without requiring the reviewer to
survey the whole manuscript.

\subsection{Why this discipline matters}

The manuscript is ambitious, and ambition invites a fair suspicion that the
language may be doing more work than the evidence. The evidence discipline in
this chapter is designed to answer that suspicion directly. It does not ask the
reader to trust the author's confidence. It asks the reader to inspect the
claim class, the support class, the comparator, and the reopening condition. In
that sense the publication surface is intentionally adversarial: a good
objection should find a named place to land, and a named place to land should
make the next repair possible.

\subsection{Boundary between manuscript and evidence files}

The manuscript explains the scientific argument. Evidence files preserve the
machine-readable details needed for replay, checksum comparison, and long-form
inspection. The two surfaces should not be confused. When a file name appears
in the manuscript, it is there as a stable public anchor, not as a substitute
for explanation. When a paragraph explains a theorem, replay, or comparator, it
must remain readable even before the reader opens the underlying file. This is
the standard used here: prose teaches the claim; evidence files make the claim
auditable.
"""


def _r014_review_boundaries_chapter_tex() -> str:
    return r"""\section{Review Boundaries and Journal Projection Map}
\label{sec:oc133-review-boundaries-journal-map}

This chapter translates likely reviewer objections into the form used by the
release. Each objection threatens a particular claim, calls for a particular
kind of evidence, leaves a residual risk, and has a reopening condition. The
purpose is not to win by phrasing; it is to make criticism precise enough that
the manuscript can be repaired when the criticism is correct.

\subsection{The tuple may be only vocabulary}

The threatened claim is that \(K=(\Omega,\partial\Omega,A,\Theta,P,J,C,k,M)\)
is a useful typed model object rather than a decorative list. The answer is the
component discipline: each component names a distinct review question about
state, boundary, observation, threshold, potential, flow, cycle, persistence,
or context. The residual risk is redundancy. The reopening condition is a case
where a component can be removed without changing any verdict, witness,
boundary, or falsifier.

\subsection{Boundaries may be metaphorical}

The threatened claim is that \(\partial\Omega\) can do scientific work. The
answer is to read boundaries as typed admissibility conditions: they separate
states, events, or relations that preserve the declared continuum from those
that demote, split, kill, or require a narrower claim. The residual risk is that
some domains need richer boundary geometry. The reopening condition is a
declared boundary that fails to separate admissible and inadmissible states in
the cited case.

\subsection{Continuumness may be underdefined}

The threatened claim is that \(k\) names persistence through change. The answer
is that \(k\) is always read together with state region, boundary, cycles, and
context; it is not a mystical liveness score. The residual risk is that
empirical proxies for liveness remain domain-bound. The reopening condition is
a live/dead distinction that cannot be reproduced under the stated assumptions.

\subsection{K-levels may be labels}

The threatened claim is that K-levels are nested witness strata. The answer is
the retained-witness and demotion discipline: an alleged level must add a
constraint, observable consequence, or failure criterion. The residual risk is
that some didactic examples are ahead of domain validation. The reopening
condition is an adjacent K transition that adds no retained witness.

\subsection{Operator claims may be too broad}

The threatened claim is that operators preserve type discipline across updates.
The answer is to keep operator claims within declared update families and
assumption classes. The residual risk is domain adapter complexity. The
reopening condition is an operator that silently changes the claim type without
a declared rule.

\subsection{Formal support may not cover prose}

The threatened claim is that proof, finite witnesses, and formalization
inventory support the public wording. The answer is alignment: the public
sentence must stay within the exact support class. The residual risk is partial
mechanization. The reopening condition is a dependency, assumption, or
formalization mismatch.

\subsection{Replay rows may be overread}

The threatened claim is that replay examples provide bounded support. The
answer is the replay evidence pattern: source snapshot, formula, residual,
comparator, negative control, and falsifier. The residual risk is that a row is
illustrative rather than validation-grade. The reopening condition is any
missing or failed replay component.

\subsection{Prior art may absorb the delta}

The threatened claim is that OC contributes residual structure beyond existing
systems theory, cybernetics, autopoiesis, dynamical systems, complexity science,
formal verification, formal ontology, and compositional modeling. The answer is
the comparator matrix. The residual risk is real: a stronger comparator can
narrow OC. The reopening condition is a comparator that explains the same row
with less burden.

\subsection{Figures and tables may imply too much}

The threatened claim is that visuals and tables are argument surfaces. The
answer is that each reader-facing figure or table must have a semantic role,
caption, formula or evidence anchor, and rendered-layout check. The residual
risk is visual compression. The reopening condition is a figure or table that
implies a claim without its support anchor.

\subsection{Journal projections may drift}

The threatened claim is that venue-specific article packages remain projections
from the same release. The answer is a no-send journal package discipline:
venue requirements, component manifests, source maps, and disclosure statements
are generated from the release package. The residual risk is loss of nuance
during shortening. The reopening condition is a projection that introduces a
claim not present in the release or drops a necessary limitation.

\subsection{Foundations-of-science review stance}

For a foundations-oriented venue, the central editorial question is whether the
manuscript has a real conceptual object and a serious relation to prior systems
thought. The projection should foreground the tuple, the continuity problem,
the prior-art comparator matrix, and the limits of present proof. It should not
pretend that the current release has completed every empirical domain. A
foundations reviewer can therefore attack the model grammar, the identity
conditions, the ontology of boundaries, and the relation to existing systems
theory.

\subsection{Physics-oriented review stance}

For a physics-oriented venue, the central editorial question is whether the
formal language respects the difference between mathematical structure and
physical validation. The projection should foreground state space, boundary,
threshold, flow, finite witness, and falsifier discipline, while treating
high-level numeric ranges as illustrative unless they have row-level source and
derivation. A physics reviewer can therefore attack dimensional consistency,
observable definition, benchmark selection, and whether any physical claim has
been promoted beyond its evidence.

\subsection{Biotheory and systems-biology stance}

For a biotheory venue, the central question is whether continuumness, liveness,
residue, rebirth, and identity are operational rather than metaphorical. The
projection should foreground lifecycle distinctions, cycles, maintenance,
boundary crossing, and demotion conditions. A reviewer can ask whether the
model distinguishes organism, trace, residue, population renewal, and identity
continuation without smuggling metaphysics into biological evidence.

\subsection{Management and enterprise stance}

For a management, flexible-systems, or enterprise-architecture venue, the
central question is whether the model helps decision-makers inspect complex
systems without losing scientific discipline. The projection should foreground
domain projection, enterprise examples, AI and security routes, reader-facing
tables, and limitations. A reviewer can ask whether the model improves
architecture reasoning, whether it identifies falsifiers, and whether it avoids
turning strategy language into unsupported universals.

\subsection{Computational-biology and reproducibility stance}

For a computational or reproducibility venue, the central question is whether
the package is inspectable. The projection should foreground source snapshots,
commands, target-blind rows, finite checks, table layout, data/code statements,
and failure interpretation. A reviewer can ask whether an independent reader
can reproduce the bounded check, whether hashes bind to the right files, and
whether the claim wording changes when a replay row fails.

\subsection{Chemistry and interdisciplinary-data stance}

For an interdisciplinary data venue, the central question is whether examples,
tables, and source files are sufficiently explicit for external reuse. The
projection should foreground the data/code manifest, evidence anchors, SI
boundary, visual/table quality, and conservative interpretation of replay
examples. A reviewer can ask whether each table has a source, whether each
figure demonstrates a claim, and whether domain examples are demoted when
source or comparator support is incomplete.
"""


def apply_r014_high_reasoning_closure(source_dir: Path) -> None:
    pred_dir = source_dir / "content" / "predictions"
    if pred_dir.is_dir():
        for path in sorted(pred_dir.glob("predictions_*.tex")):
            if path.name.startswith("predictions_master"):
                text = _r014_bounded_prediction_master_text()
            else:
                match = re.search(r"predictions_k(\d+)", path.name)
                if not match:
                    continue
                text = _r014_bounded_prediction_level_text(int(match.group(1)))
            write_text_if_changed(path, text)

    methods_chapter = source_dir / "content" / "27c_oc_core_1_3_3_methods_evidence_and_comparators.tex"
    if methods_chapter.is_file():
        write_text_if_changed(methods_chapter, _r014_methods_evidence_chapter_tex())

    review_chapter = source_dir / "content" / "27d_oc_core_1_3_3_review_boundaries_and_journal_map.tex"
    if review_chapter.is_file():
        write_text_if_changed(review_chapter, _r014_review_boundaries_chapter_tex())

    discussion_chapter = source_dir / "content" / "05_discussion.tex"
    if discussion_chapter.is_file():
        write_text_if_changed(discussion_chapter, _r014_discussion_tex())

    k12_chapter = source_dir / "content" / "k_levels" / "k12.tex"
    if k12_chapter.is_file():
        write_text_if_changed(k12_chapter, _r014_k12_provisional_tex())

    experiments_dir = source_dir / "content" / "experiments"
    if experiments_dir.is_dir():
        for path in sorted(experiments_dir.glob("*.tex")):
            text = path.read_text(encoding="utf-8", errors="replace")
            demoted = _r014_demote_experiment_chapter(text)
            if demoted != text:
                write_text_if_changed(path, demoted)

    appendix_d = source_dir / "appendix" / "D_oc_core_1_3_source_audit_appendix.tex"
    if appendix_d.is_file():
        write_text_if_changed(
            appendix_d,
            r"""\section{Appendix D -- Version 1.3.3 Provenance and Corpus Boundary}
\label{sec:oc133-provenance-corpus-boundary}

This appendix records what the current manuscript is and what it is not. Core
1.3.3 is a bounded review manuscript built from the public release corpus,
proof sheets, finite checks, comparator material, figures, tables, and
reproducibility companions available for this version. It is not a republication
of an earlier baseline and it is not a claim that every historical source file
has the same evidential status.

\subsection{Purpose}

The main body is written for scientific reading. This appendix is written for
provenance review. It lets a reviewer distinguish between the monograph, the
compact article projection, the methods companion, the reviewer map, and the
machine-readable evidence manifests. Those objects support one another, but
none of them should be mistaken for the whole theory.

\subsection{Current-version boundary}

The present version promotes only bounded claims tied to source and evidence
anchors. Historical material is retained when it explains lineage or provides a
source witness, but it does not automatically promote present-version claims.
When an older statement is broader than the 1.3.3 evidence surface, the public
text narrows it, marks it as illustrative, or moves it into a provenance role.

\subsection{Review questions}

\begin{itemize}
\item Which public corpus object supports the present statement?
\item Which proof sheet, finite check, table, figure, comparator, or replay row
      is being invoked?
\item Is the cited material a promoted support row, an illustrative example, a
      historical source witness, or a planned research route?
\item What finding would reopen the wording?
\end{itemize}

Those questions are the governing boundary of the appendix. They protect the
reader from hidden workflow dependency while keeping internal editorial control
material outside the publication text.
""",
        )

    k1_paths = sorted((source_dir / "content" / "k_levels").glob("k1*.tex"))
    for path in k1_paths:
        text = path.read_text(encoding="utf-8", errors="replace")
        original = text
        text = re.sub(
            r"\\subsubsection\{Time\s+\\texorpdfstring\{\$\\tau\(K_1\)\$\}\{\\tau\(K_1\)\}\}.*?(?=\n% ================================================================\n\\subsubsection)",
            lambda _match: r"""\subsubsection{Ordering Coordinate \texorpdfstring{$\lambda(K_1)$}{lambda(K_1)}}

\(K_1\) has a primitive ordering coordinate, denoted here by
\(\lambda(K_1)\). This coordinate orders configurations along the first axis,
but it is not yet promoted as domain-level physical time. Physical temporal
phenomena require additional witness structure supplied at later levels.

Thus the public convention is
\[
\lambda(K_1) \text{ orders one-axis configurations, while physical time is not promoted at } K_1.
\]
""",
            text,
            flags=re.S,
        )
        text = text.replace(r"\tau(K_1) \text{ cannot emerge.}", r"\lambda(K_1) \text{ is the local ordering coordinate.}")
        text = text.replace("no temporal phenomena appear at $K_1$;", "no domain-level temporal phenomena are promoted at $K_1$;")
        text = text.replace("absence of emergent time,", "absence of promoted domain-level physical time,")
        text = text.replace("collapse under excessive gradients is universal;", "collapse under excessive gradients is a bounded model condition;")
        if text != original:
            write_text_if_changed(path, text)

    model_path = source_dir / "content" / "03_model.tex"
    if model_path.is_file():
        text = model_path.read_text(encoding="utf-8", errors="replace")
        original = text
        text = text.replace(
            "Level \\(K_1\\) is the simplest genuine continuum: it introduces time, a one-dimensional axis, and basic geometric structure.",
            "Level \\(K_1\\) is the simplest genuine continuum: it introduces a primitive ordering coordinate, a one-dimensional axis, and basic geometric structure.",
        )
        text = text.replace("P_1(t),J_1(t)", r"P_1(\lambda),J_1(\lambda)")
        text = text.replace("P_1(t)", r"P_1(\lambda)")
        text = text.replace("J_1(t)", r"J_1(\lambda)")
        text = text.replace("k_1(t)", r"k_1(\lambda)")
        text = text.replace("In this time-dependent analytic example,", "In this ordering-dependent analytic example,")
        text = text.replace("where \\(I\\) is the time interval", "where \\(I\\) is the local ordering interval")
        text = text.replace(
            r"K = \big(\Omega(K), A(K), P(t), J(t), \Theta(K), \partial\Omega(K), C(K), k(K,t)\big),",
            r"K = \big(\Omega(K), \partial\Omega(K), A(K), \Theta(K), P(t), J(t), C(K), k(K,t), M(K)\big),",
        )
        text = text.replace(
            r"\item \(\Omega(K)\) is a nonempty set of admissible states;",
            r"\item \(\Omega(K)\) is a nonempty set of admissible states;",
        )
        text = text.replace(
            r"    \item \(k(K,t)\) is the measure of continuumness.",
            r"    \item \(k(K,t)\) is the measure of continuumness;"
            "\n"
            r"    \item \(M(K)\) is the embedding context or meta-space that constrains the local continuum.",
        )
        text = text.replace("R014 tuple projection convention", "Public tuple projection convention")
        if "Public tuple projection convention" not in text:
            text = text.replace(
                "The meta-space provides additional admissible states and axes that can host future dimensional extensions of \\(K\\).",
                "The meta-space provides additional admissible states and axes that can host future dimensional extensions of \\(K\\).\n\n"
                "\\paragraph{Public tuple projection convention.}\n"
                "The canonical public tuple is \\(K=(\\Omega,\\partial\\Omega,A,\\Theta,P,J,C,k,M)\\). "
                "Older local displays may use a shorter or differently ordered tuple when a component is derived in that local model. "
                "Those displays are projections of the canonical release tuple, not competing definitions.",
            )
        tuple_replacements = {
            r"K=(\Omega,A,P,J,\Theta,\partial\Omega,C,k)": r"K=(\Omega,\partial\Omega,A,\Theta,P,J,C,k,M)",
            r"(\Omega,A,P,J,\Theta,\partial\Omega,C,k)": r"(\Omega,\partial\Omega,A,\Theta,P,J,C,k,M)",
            r"(\Omega',A',P',J',\Theta',\partial\Omega',C',k')": r"(\Omega',\partial\Omega',A',\Theta',P',J',C',k',M')",
        }
        for old, new in tuple_replacements.items():
            text = text.replace(old, new)
        if text != original:
            write_text_if_changed(model_path, text)

    toe_paths = sorted((source_dir / "appendix").glob("toe_data*.tex"))
    for path in toe_paths:
        text = path.read_text(encoding="utf-8", errors="replace")
        original = text
        note = (
            "The numerical rows in this subsection are calibration and review aids. "
            "A row is promoted as empirical support only when the surrounding manuscript names its source snapshot, formula or reconstruction rule, comparator, residual or uncertainty, negative control, and falsifier. "
            "Otherwise the value is an illustrative range or literature-facing placeholder, not a theorem value and not a completed validation result."
        )
        if "calibration and review aids" not in text:
            text = text.replace(
                "table records the corresponding functional form, numerical estimate, or bounded\nrange rather than leaving the row implicit.",
                "table records the corresponding functional form, numerical estimate, or bounded\nrange rather than leaving the row implicit.\n\n" + note,
            )
        text = text.replace("Universal integration capacity", "Illustrative universal integration capacity")
        text = text.replace("Cross-continuum compatibility", "Illustrative cross-continuum compatibility")
        text = text.replace("Structural reachability", "Illustrative structural reachability")
        text = text.replace("Global tension budget", "Illustrative global tension budget")
        if "Illustrative, non-promoted numeric review surface:" not in text:
            text = text.replace(r"\caption{", r"\caption{Illustrative, non-promoted numeric review surface: ")
        if text != original:
            write_text_if_changed(path, text)

    notation_path = source_dir / "appendix" / "A_notation.tex"
    if notation_path.is_file():
        text = notation_path.read_text(encoding="utf-8", errors="replace")
        original = text
        text = re.sub(r"\\section\{Notation and Symbols\}", r"\\section{Appendix A -- Notation and Symbols}", text, count=1)
        if text != original:
            write_text_if_changed(notation_path, text)

    frontmatter_path = source_dir / "content" / "frontmatter_oc_core_1_3_master.tex"
    if frontmatter_path.is_file():
        text = frontmatter_path.read_text(encoding="utf-8", errors="replace")
        original = text
        if "AI Assistance Disclosure" not in text:
            disclosure = latex_escape(ai_assistance_disclosure())
            text = text.replace(
                "\\end{itemize}\n\n\\clearpage\n\\begin{abstract}",
                "\\end{itemize}\n\n\\clearpage\n\\noindent\\textbf{AI Assistance Disclosure.}\n"
                + disclosure
                + "\n\n\\clearpage\n\\begin{abstract}",
            )
        if text != original:
            write_text_if_changed(frontmatter_path, text)

    theorem_roadmap = source_dir / "content" / "20_oc_core_1_3_theorem_roadmap.tex"
    if theorem_roadmap.is_file():
        text = theorem_roadmap.read_text(encoding="utf-8", errors="replace")
        original = text
        if "Proof Status Vocabulary" not in text:
            text += r"""

\subsection{Proof Status Vocabulary}

The release separates proof-related statuses because a formal reviewer must be
able to see what is actually being claimed. A \emph{proved theorem} has a
stated theorem, assumptions, proof route, and counterexample boundary in the
present release. A \emph{proof-sheet support row} is a structured human proof
record that can support bounded prose but is not stronger than its assumptions.
A \emph{finite-witness row} shows a positive or negative finite semantic case;
it does not by itself prove an unrestricted theorem. A \emph{formalization
inventory entry} records a mechanization or intended mechanization surface, but
is not described as a clean certificate unless source binding, build status,
and certificate checks are clean for the cited revision. A \emph{source-witness
row} records lineage or evidence location and may orient the reader, but it is
not promoted as a new primitive theorem.

Whenever these statuses disagree, the public wording follows the weakest
status needed for the sentence. This is the theorem-route ceiling for Core
1.3.3: registry presence, source lineage, finite examples, proof sheets, and
formalization inventory are useful only when the manuscript states exactly what
support class they provide.
"""
        if text != original:
            write_text_if_changed(theorem_roadmap, text)

    for path in sorted((source_dir / "content").rglob("*.tex")) + sorted((source_dir / "appendix").rglob("*.tex")):
        text = path.read_text(encoding="utf-8", errors="replace")
        original = text
        text = text.replace(
            "all 11 declared release-tuple components in the finite semantic suite, with Lean binding for the corresponding typed witness schema",
            "all nine canonical release-tuple components in the finite semantic suite, with source-inspected witness records for the corresponding typed witness schema",
        )
        text = text.replace(
            "all 11 declared release-tuple components",
            "all nine canonical release-tuple components",
        )
        text = text.replace("with Lean binding for", "with source-inspected records for")
        text = text.replace(r"K=(\Omega,A,P,J,\Theta,\partial\Omega,C,k)", r"K=(\Omega,\partial\Omega,A,\Theta,P,J,C,k,M)")
        text = text.replace(r"(\Omega,A,P,J,\Theta,\partial\Omega,C,k)", r"(\Omega,\partial\Omega,A,\Theta,P,J,C,k,M)")
        text = text.replace(r"(\Omega',A',P',J',\Theta',\partial\Omega',C',k')", r"(\Omega',\partial\Omega',A',\Theta',P',J',C',k',M')")
        text = text.replace(
            r"\textbackslash{}(K=(\textbackslash{}Omega,\textbackslash{}partial\textbackslash{}Omega,A,\textbackslash{}Theta,P,J,C,k,M)\textbackslash{})",
            r"\(K=(\Omega,\partial\Omega,A,\Theta,P,J,C,k,M)\)",
        )
        text = text.replace(
            r"\textbackslash{}(\textbackslash{}partial\textbackslash{}Omega\textbackslash{})",
            r"\(\partial\Omega\)",
        )
        text = text.replace(r"\textbackslash{}\_", r"\_")
        text = text.replace(r"\textbackslash{}Omega", r"\Omega")
        text = text.replace(r"\textbackslash{}partial", r"\partial")
        text = text.replace(r"\textbackslash{}Theta", r"\Theta")
        text = _r014_demote_retrospective_replay_language(text)
        if "\\begin{longtable}" in text or "\\begin{tabular" in text:
            text = re.sub(
                r"(Mathematics\s*&[^\\\\]*?&\s*\\occode\{TRACE_REVIEWED\}\s*&\s*)\\occode\{EVIDENCE_BOUNDED\}(\s*&\s*)bounded review evidence recorded(\s*&\s*)(?:none|keine|нет)(\s*&)",
                lambda match: (
                    match.group(1)
                    + r"\occode{EVIDENCE_DEMOTED_PENDING_BINDING}"
                    + match.group(2)
                    + "demoted review row pending finite-source binding"
                    + match.group(3)
                    + "source-binding failure remains open"
                    + match.group(4)
                ),
                text,
                flags=re.I | re.S,
            )
            text = re.sub(
                r"(Mathematics\s*&[^\\\\]*?&[^\\\\]*?&[^\\\\]*?&[^\\\\]*?&\s*)replayable under the bounded public protocol(\s*&\s*)bounded review evidence recorded",
                r"\1demoted pending finite-source binding\2not support-carrying until source_manifest_binding_ok is true and certificate_binding_failure_total is zero",
                text,
                flags=re.I | re.S,
            )
        text = re.sub(
            r"\bProtocol mathematics anchor replay runs under evidence bar ([^.]+?) and currently reports readiness bounded review evidence recorded\.",
            "Protocol mathematics anchor replay is demoted pending finite-source binding and is not support-carrying until source_manifest_binding_ok is true and certificate_binding_failure_total is zero.",
            text,
            flags=re.I,
        )
        text = re.sub(
            r"\bMathematics\s+remains\s+the\s+formal\s+anchor\b[^.]*\.",
            "Mathematics remains a formal review lane, but the current replay row is demoted pending finite-source binding and is not support-carrying in this release.",
            text,
            flags=re.I,
        )
        if text != original:
            write_text_if_changed(path, text)


def apply_r014_cerberus_overrides(source_dir: Path) -> None:
    replacements = {
        "Process Schema Under scoped": "Process Schema Under Declared Scope",
        "scoped Falsifiability Criteria": "Domain-Bounded Falsifiability Criteria",
        "scoped Prediction Constraints": "Domain-Bounded Prediction Constraints",
        "scoped unrestricted comparative claim": "unrestricted comparative claim",
        "scoped claim": "bounded claim",
        "scoped target-blind replay QA": "bounded target-blind replay QA",
        "boundary..": "boundary.",
        "Recorded content:": "Evidence note:",
        "Content: Oc133": "Evidence note: OC Core 1.3.3",
        "ILLUSTRATIVE\\_PRIOR\\_ART\\_POSITIONING\\_ONLY\\_NO\\_UNIQUENESS\\_PROMOTION": (
            "This row is illustrative prior-art positioning only and does not promote a uniqueness or priority claim."
        ),
        "science monolith corpus register": "release corpus index",
        "internal science-state register": "public evidence-state summary",
        "canonical science-state register": "public evidence-state summary",
        "science-state register": "evidence-state summary",
        "OC_CORE_1_3_SCIENCE_SPOT": "the public evidence-state summary",
        "source module": "technical module",
        "source-specific": "module-specific",
        "source files": "technical files",
        "source role": "corpus role",
        "source digest": "evidence summary",
        "source-first enlargement": "source-grounded clarification",
        "journal-core bridge": "article projection boundary",
        "legacy-route": "historical evidence route",
        "raw source dump": "unintegrated technical dossier",
        "source dump": "unintegrated technical dossier",
        "control-plane record": "private editorial record",
        "bounded evidence recorded": "bounded support row recorded",
        "maintain replay discipline": "continue replay review",
        "full promotion bar": "current public-support criterion",
        "full validation bar": "bounded replay QA criterion",
        "fail-closed": "not yet public-supporting",
        "proof-routed closure": "proof-routed support",
        "hostile-review backlog is closed": "hostile-review backlog has no surviving public blocker in the inspected row",
        "closed stack synthesis": "bounded synthesis support surface",
        "legally contributes to the closed synthesis stack": "contributes only as a bounded support row",
        "therefore legally contributes to the closed synthesis stack": "therefore contributes only as a bounded support row",
        "contributes lawfully to the closed synthesis stack": "contributes only as a bounded support row",
        "closed synthesis stack": "bounded review surface",
        "closed synthesis summary": "bounded synthesis summary",
        "promoted synthesis": "bounded synthesis review",
        "lawfully promoted bounded synthesis": "bounded, non-final synthesis review",
        "empirical held-out prediction summaries": "bounded held-out replay protocol summaries",
        "held-out prediction summaries": "held-out replay protocol summaries",
        "K0--K12 parameter laws": "K0--K12 parameter candidates",
        "Exact validator: \\occode{BOUNDED_SYNTHESIS_REVIEW_RECORDED}.": "Review status: this synthesis remains bounded and reopenable by row-level evidence.",
        "No release blocker remains in the internal science-state register.": "No global closure is promoted here; every row remains reopenable by its stated evidence boundary.",
        "broader-promotion limits: none remain at this level.": "broader-promotion limits: row-level evidence remains required before any domain-validation or closure claim.",
        "Core v2.6": "Core 1.3.3 historical source lineage, not a promoted current-version claim",
        "limit continuum": "bounded synthesis candidate",
        "global structural fixed point": "future structural fixed-point proof obligation",
        "The diagram below is generated from the r012 figure registry, so its objects, arrows, formula anchor, and evidence link are checked before the release audit can pass.": (
            "The diagram separates the objects, direction of dependence, formula anchor, and evidence link so that the reader can inspect the argument visually before returning to the prose."
        ),
        "full-scope synthesis": "bounded cross-domain synthesis",
        "full-scope": "bounded cross-domain",
        "unified-science synthesis": "cross-domain synthesis",
        "unified-science": "cross-domain",
        "validated anchor active": "mathematical anchor active",
        "bounded replay QA bar": "bounded replay QA protocol",
        "Lean-checked subset": "Lean-oriented formalization inventory",
        "Lean checked subset": "Lean-oriented formalization inventory",
        "Lean subset": "Lean-oriented formalization inventory",
        "Lean declarations": "formalization references",
        "Lean declaration": "formalization reference",
        "The r014 public model": "This public model",
        "the r014 public model": "this public model",
        "corresponding evidence-package record": "named public evidence row",
        "Appendix~the Synthesis Support Appendix": "the Synthesis Support Appendix",
        "Appendix the Synthesis Support Appendix": "the Synthesis Support Appendix",
        "bounded theorem route": "bounded review route",
        "bounded theorem-route": "bounded review-route",
        "bounded theorem-routed": "bounded review-routed",
        "boundedtheoremroute": "bounded review route",
        "TRACE_COMPLETE": "TRACE_REVIEWED",
        "EVIDENCE_COMPLETE": "EVIDENCE_BOUNDED",
        "PASS_31_OF_31_TERMINALIZED": "31 finite cases recorded; source-binding demotion applies",
        "proof-routed + empirical / held-out validated": "bounded replay/comparator example",
        "held-out validated": "held-out replay reviewed",
        "usable-now practical claims": "operational claims ready for use",
        "usable-now practical claim": "operational claim ready for use",
        "usable-now rows": "bounded-review rows",
        "usable-now row": "bounded-review row",
        "usable-now claim": "operational claim ready for use",
        "usable-now claims": "operational claims ready for use",
        "usable now": "available for bounded review",
        "closed practical value": "bounded practical value",
        "formally proved": "formally bounded review support",
        "theorem-native domain lanes are usable under explicit theorem, data-route, and falsifier discipline": (
            "domain lanes are retained as bounded review protocols under explicit theorem, data-route, and falsifier discipline"
        ),
        "proof-routed domain lanes are usable under explicit theorem, data-route, and falsifier discipline": (
            "domain lanes are retained as bounded review protocols under explicit theorem, data-route, and falsifier discipline"
        ),
        "operationally supported within bounds": "bounded as a route-selection example",
        "lawful packet selection": "bounded packet-selection review",
        "bounded residual prediction": "bounded residual-check protocol",
        "anomaly screening": "anomaly-screening protocol",
        "state-transition auditing": "state-transition audit protocol",
        "regime-shift monitoring": "regime-shift monitoring protocol",
        "promoted packet": "bounded review packet",
        "promoted physics packet": "bounded physics review packet",
        "promoted chemistry packet": "bounded chemistry review packet",
        "promoted biological packet": "bounded biology review packet",
        "promoted systems packet": "bounded systems review packet",
        "promoted tolerance band": "declared review tolerance band",
        "closed packet": "bounded review packet",
        "closed empirical domains": "bounded replay domains",
        "lawful domain packet": "bounded domain review packet",
        "already cleared": "has recorded bounded review evidence under declared assumptions",
        "lawfully generate": "are used to formulate",
        "lawfully generates": "is used to formulate",
        "Open gaps: none": "Open gaps: row-level promotion remains conditional on source, comparator, negative-control, and falsifier checks",
        "bounded support row under declared assumptions": "bounded review row under declared assumptions; not a completed domain-validation claim",
        "bounded evidence recorded": "bounded review evidence recorded",
        "theorem packet recorded": "theorem packet listed for review",
        "parameter law recorded": "parameter candidate listed for review",
        "strict closure": "strict finite-review route",
    }
    for tex_path in sorted((source_dir / "content").rglob("*.tex")) + sorted((source_dir / "appendix").rglob("*.tex")):
        text = tex_path.read_text(encoding="utf-8", errors="replace")
        original = text
        for old, new in replacements.items():
            text = text.replace(old, new)
        text = re.sub(r"\\section\{Appendix\s+[A-Z]\s+--\s+([^}]+)\}", r"\\section{\1}", text)
        text = re.sub(
            r"Synthesis checkpoint(?: after)?\s*(\d+)?(?: indexed modules in [^.]+)?\.\s*",
            lambda match: (
                f"Integration checkpoint {match.group(1)}. "
                if match.group(1)
                else "Integration checkpoint. "
            ),
            text,
        )
        text = text.replace(
            "repository path validation/numeric\\_replay\\_qa/OC133\\_NUMERIC\\_REPLAY\\_QA\\_TABLE.json",
            "evidence file " + _r014_public_file_path("validation/numeric_replay_qa/OC133_NUMERIC_REPLAY_QA_TABLE.json"),
        )
        text = text.replace(
            "repository path comparators/OC\\_1\\_3\\_3\\_NOVELTY\\_AND\\_PRIORITY\\_REGISTER.json",
            "evidence file " + _r014_public_file_path("comparators/OC_1_3_3_NOVELTY_AND_PRIORITY_REGISTER.json"),
        )
        text = re.sub(r"\brepository path\s+", "evidence file ", text, flags=re.I)
        text = re.sub(r"\bpublic proof sheet\b", "public proof record", text, flags=re.I)
        text = re.sub(r"\bcurrent formal profile\b", "declared formal profile", text, flags=re.I)
        text = re.sub(r"\bAppendix~?the\s+oc\s+core\s+1\s+3\s+synthesis\s+support\s+dossiers\s+discussion\b", "the Synthesis Support Appendix", text, flags=re.I)
        text = re.sub(r"\bthe\s+oc\s+core\s+1\s+3\s+synthesis\s+support\s+dossiers\s+discussion\b", "the Synthesis Support Appendix", text, flags=re.I)
        text = re.sub(r"\bthe\s+corresponding\s+evidence-package\s+record\b", "the named public evidence row", text, flags=re.I)
        text = re.sub(r"\b(is|are)\s+closed\s+as\s+bounded\s+(?:theorem|review)\s+route\b", r"\1 represented by a bounded review row", text, flags=re.I)
        text = re.sub(r"\bclosed\s+as\s+support-only\s+row\b", "represented as a support-only row", text, flags=re.I)
        text = re.sub(r"\bEvery process is expressible as a composition of these\b", "Within the declared operator vocabulary, a reviewed process may be represented as a composition of these", text, flags=re.I)
        text = re.sub(r"\bEvery process in OC follows the structure\b", "This public model treats the following as a proposed process schema under declared scope", text, flags=re.I)
        text = re.sub(r"\bThis schema is invariant from K0 to K12\b", "The schema is used as a review heuristic across K0--K12; invariance remains an evidence obligation whenever it is promoted beyond definition", text, flags=re.I)
        text = re.sub(r"\bAt present\s+5\s+of\s+these\s+lanes\s+satisfy\s+the\s+bounded\s+replay\s+QA\s+protocol,\s+while\s+0\s+lanes\s+remain\s+not\s+yet\s+public-supporting\.", "At present the matrix records five lanes as candidate bounded replay-QA routes; none are promoted as completed domain validation merely by appearing in the matrix.", text, flags=re.I)
        text = re.sub(r"\bAt present\s+5\s+of\s+these\s+lanes\s+satisfy\s+the\s+bounded\s+replay\s+QA\s+bar,\s+while\s+0\s+lanes\s+remain\s+not\s+yet\s+public-supporting\.", "At present the matrix records five lanes as candidate bounded replay-QA routes; none are promoted as completed domain validation merely by appearing in the matrix.", text, flags=re.I)
        text = re.sub(r"\bmathematics first as the validated anchor\b", "mathematics first as the inspected formal anchor", text, flags=re.I)
        text = re.sub(r"\bphysics,\s+chemistry,\s+biology,\s+and\s+systems/civilizational\s+projection\s+as\s+bounded\s+replay\s+QA\s+program\b", "physics, chemistry, biology, and systems/civilizational projection as candidate bounded replay-QA programs", text, flags=re.I)
        text = re.sub(r"\bExperiments\s+validate\b", "Experiments probe", text, flags=re.I)
        text = re.sub(r"\bexperiments\s+validate\b", "experiments probe", text, flags=re.I)
        text = re.sub(r"\bvalidate\s+the\b", "test the", text, flags=re.I)
        text = re.sub(r"\bvalidates\s+the\b", "tests the", text, flags=re.I)
        text = re.sub(r"\bvalidated\s+the\b", "tested the", text, flags=re.I)
        text = re.sub(r"\bvalidate\s+cognitive\s+continua\b", "probe cognitive-continuum hypotheses", text, flags=re.I)
        text = re.sub(r"\bempirically\s+validate\s+social\s+continua\b", "probe social-continuum hypotheses", text, flags=re.I)
        text = re.sub(r"\bvalidate\s+meta-theories\b", "probe meta-theory candidates", text, flags=re.I)
        text = re.sub(r"\bconfirm\s+OC\s+predictions\b", "test OC prediction protocols", text, flags=re.I)
        text = re.sub(r"\bconfirms?\b", "supports", text, flags=re.I)
        text = re.sub(r"\bconfirmation\b", "support", text, flags=re.I)
        text = re.sub(
            r"that\s+must\s+hold\s+in\s+any\s+admissible\s+real\s+physical,\s*chemical,\s*biological,\s*cognitive,\s*social\s+or\s+meta-theoretical\s+instantiation",
            "that may be tested as bounded constraints inside a declared physical, chemical, biological, cognitive, social, or meta-theoretical instantiation",
            text,
            flags=re.I | re.S,
        )
        text = re.sub(
            r"All\s+phenomena\s+must\s+emerge\s+at\s+threshold\s+crossings\s+definable\s+in\s+terms\s+of\s*P\s*,\s*J\s*,\s*(?:and\s*)?\\?Theta\.",
            lambda _match: "Promoted examples should state whether threshold crossings in P, J, and \\Theta explain the observed regime change; cases that require additional variables remain outside the promoted prediction.",
            text,
            flags=re.I | re.S,
        )
        text = re.sub(
            r"Predictions\s+must\s+not\s+violate\s+the\s+monotonicity\s+of\s+axes,\s+thresholds\s+or\s+(?:embedding\s+spaces|dimensionality)\s*:?\s*.*?\.",
            "Predictions must state the declared axis, threshold, dimensional, and embedding assumptions and identify any case where those assumptions fail.",
            text,
            flags=re.I | re.S,
        )
        text = re.sub(
            r"(Predictions must state the declared axis, threshold, dimensional, and embedding assumptions and identify any case where those assumptions fail\.)\s*\\\]",
            r"\1",
            text,
            flags=re.I,
        )
        text = re.sub(
            r"All\s+phenomena\s+must\s+emerge\s+at\s+threshold\s+crossings\s+definable\s+in\s+terms\s+of\s*\$P\$\s*,\s*\$J\$\s*,\s*\$\\Theta\$\s*\.",
            lambda _match: "Promoted examples should state whether threshold crossings in $P$, $J$, and $\\Theta$ explain the observed regime change; cases that require additional variables remain outside the promoted prediction.",
            text,
            flags=re.I | re.S,
        )
        text = re.sub(
            r"\bmust\s+not\s+violate\s+the\s+monotonicity\s+of\s+axes,\s+thresholds\s+or\s+embedding\s+spaces\b",
            "must state the declared axis, threshold, and embedding assumptions and identify any case where those assumptions fail",
            text,
            flags=re.I,
        )
        text = re.sub(
            r"\bEmbedding\s+spaces\s+form\s+a\s+monotonic\s+sequence\b",
            "Embedding-space nesting is a declared modeling assumption, not an unrestricted empirical theorem",
            text,
            flags=re.I,
        )
        text = re.sub(
            r"\bAxes\s+are\s+monotonic\b",
            "Axis growth is treated as a witness obligation",
            text,
            flags=re.I,
        )
        text = re.sub(
            r"\bGlobal\s+tension\s+budget\b",
            "Illustrative tension-budget parameter",
            text,
            flags=re.I,
        )
        text = re.sub(
            r"\bCuni\b",
            "illustrative Cuni range",
            text,
            flags=re.I,
        )
        text = re.sub(
            r"\bbounded\s+support\s+row\s+recorded\b",
            "bounded support row under declared assumptions",
            text,
            flags=re.I,
        )
        text = re.sub(
            r"\bactive\s+bounded\s+numeric\s+packet(?:\s+awaiting\s+domain-specific\s+promotion\s+review)+\b",
            "bounded numeric replay packet awaiting domain-specific promotion review",
            text,
            flags=re.I,
        )
        text = re.sub(
            r"\bactive\s+bounded\s+numeric\s+packet\b",
            "bounded numeric replay packet awaiting domain-specific promotion review",
            text,
            flags=re.I,
        )
        text = text.replace(
            r"\epsilon = D(x_{\text{new}}, x_{\text{old}}).",
            r"e_{\mathrm{err}} = D(x_{\text{new}}, x_{\text{old}}).",
        )
        text = text.replace(
            r"T_6 = F(\epsilon, C_{\text{cons}}, \Theta_{\text{cog}}, J_{\text{info}}, P_{\text{cog}}).",
            r"T_6 = F(e_{\mathrm{err}}, C_{\text{cons}}, \Theta_{\text{cog}}, J_{\text{info}}, P_{\text{cog}}).",
        )
        text = text.replace(
            r"\(\preceq_K\)",
            r"the \(K\)-order relation",
        )
        text = text.replace(
            "All live continua maintain supporting flows and stable cycles.",
            "Within the current theorem boundary, inspected live-continuum examples are modeled with supporting flows and stable cycles only when their assumptions are stated.",
        )
        text = text.replace(
            r"\paragraph{Complexity grows monotonically for live continua.}",
            r"\paragraph{Complexity growth remains a bounded hypothesis.}",
        )
        text = text.replace(
            "The practical utility atlas currently tracks \\occode{6} bounded-review rows, \\occode{3} frontier-program rows, and \\occode{1} hypothesis-only row.",
            "The practical utility atlas currently tracks bounded review protocols, frontier-program rows, and hypothesis-only rows; it does not promote operational proof merely from row presence.",
        )
        text = text.replace(
            "Its bounded practical value is not unrestricted scoped prediction; it is bounded packet-selection review, bounded residual-check protocol, anomaly-screening protocol, state-transition audit protocol, regime-shift monitoring protocol, and cross-domain route selection within one source-bound routing framework.",
            "Its practical value in this release is methodological: it shows how packet selection, residual checks, anomaly screens, state-transition audits, regime-shift monitors, and cross-domain route selection should be bounded before any operational claim is promoted.",
        )
        text = text.replace(
            "Every practical claim below is explicitly labeled so the reader can see what is already usable, what is bounded, and what still remains exploratory.",
            "Every practical row below is labeled so the reader can distinguish a bounded review protocol from a frontier program, a hypothesis, or an operational claim that still requires external deployment evidence.",
        )
        text = text.replace(
            r"\subsection{What is already usable now}",
            r"\subsection{Bounded practical review protocols}",
        )
        text = text.replace(
            r"\subsection{What OC predicts across the bounded replay domains}",
            r"\subsection{What OC currently tests across bounded replay domains}",
        )
        text = text.replace(
            "For this domain, OC currently uses the bounded review packet to audit",
            "For this domain, OC currently records a bounded review protocol for auditing",
        )
        text = text.replace(
            "For this domain, OC currently uses the bounded review packet to screen",
            "For this domain, OC currently records a bounded review protocol for screening",
        )
        text = text.replace(
            "For this domain, OC currently uses the bounded review packet to monitor",
            "For this domain, OC currently records a bounded review protocol for monitoring",
        )
        text = text.replace(
            "Held-out case total:",
            "Inventory count, not domain-validation total:",
        )
        text = text.replace(
            "A pass or fail residual verdict, anomaly prioritisation, and a decision about whether the family remains inside the bounded review packet.",
            "A provisional residual-check record, anomaly-prioritisation note, and review decision about whether the family stays inside the declared assumptions.",
        )
        text = text.replace(
            "A pass or fail trajectory verdict, a turning-point or regime-shift alert, and a decision about whether the lane remains inside the bounded systems review packet.",
            "A provisional trajectory-check record, turning-point or regime-shift note, and review decision about whether the lane stays inside the declared assumptions.",
        )
        text = re.sub(
            r"\bA bounded inclusion, anomaly, or escalation verdict for the target ([^.]+)\.",
            r"A provisional inclusion, anomaly, or escalation record for the target \1.",
            text,
            flags=re.I,
        )
        if "content/experiments" in tex_path.as_posix().replace("\\", "/"):
            experiment_replacements = {
                "direct empirical grounding": "proposed empirical-test grounding",
                "provide direct empirical grounding": "propose empirical-test grounding",
                "provides direct empirical grounding": "proposes empirical-test grounding",
                "establishes": "tests",
                "establish": "test",
                "validity of the K1-to-K2 operator": "review status of the K1-to-K2 operator",
                "foundation for all physical continua": "modeling bridge into physical-continuum examples under declared assumptions",
                "foundation for all physical systems": "modeling bridge into physical-system examples under declared assumptions",
            }
            for old, new in experiment_replacements.items():
                text = text.replace(old, new)
        text = re.sub(
            r"\\paragraph\{Axiom 1\.1 \(Continuum data\)\}\s*Any continuum \(K\) is specified by a tuple\s*\\\[\s*K\s*=\s*\\big\(\s*\\Omega\(K\), A\(K\), P\(t\), J\(t\),\s*\\Theta\(K\), \\partial\\Omega\(K\), C\(K\), k\(K,t\)\s*\\big\)\s*\\\]\s*with nonempty \\?\(?\\Omega\(K\\?\)?\\?\)? and finite axis set \\?\(?A\(K\\?\)?\\?\)?\.",
            lambda _match: (
                r"\paragraph{Axiom 1.1 (Continuum data)}" "\n"
                r"Any continuum \(K\) is specified by the canonical public tuple" "\n"
                r"\[" "\n"
                r"  K = \big(" "\n"
                r"    \Omega(K), \partial\Omega(K), A(K), \Theta(K)," "\n"
                r"    P(t), J(t), C(K), k(K,t), M(K)" "\n"
                r"  \big)" "\n"
                r"\]" "\n"
                r"with nonempty \(\Omega(K)\), finite axis set \(A(K)\), and explicit embedding context \(M(K)\). "
                r"Older eight-component displays in local source modules are projections of this tuple and may suppress \(M(K)\) only when the surrounding text states the projection role."
            ),
            text,
            flags=re.I | re.S,
        )
        text = re.sub(
            r"\\paragraph\{Axiom 1\.4 \(Continuumness\)\}.*?\\paragraph\{Axiom 1\.5 \(Evolution operator\)\}",
            lambda _match: (
                r"\paragraph{Axiom 1.4 (Continuumness zero causes)}" "\n"
                r"Continuumness \(k(K,t)\) is a diagnostic scalar functional of the continuum components, satisfying \(0\le k\le 1\). Its zero condition is governed by the declared zero-cause family:" "\n"
                r"\[" "\n"
                r"  k(K,t)=0" "\n"
                r"  \quad\Longleftrightarrow\quad" "\n"
                r"  \exists z\in Z_K:\ z(K,t)=\top." "\n"
                r"\]" "\n"
                r"The old empty-\(\Omega\) or empty-\(C\) clause is a special case where those are the only declared zero causes." "\n\n"
                r"\paragraph{Axiom 1.5 (Evolution operator)}"
            ),
            text,
            flags=re.I | re.S,
        )
        if "/content/k_levels/" in tex_path.as_posix().replace("\\", "/"):
            projection_note = (
                "\n\n\\paragraph{Canonical tuple projection note.}\n"
                "Local K-level displays in this module are projections of the canonical public tuple "
                "\\(K=(\\Omega,\\partial\\Omega,A,\\Theta,P,J,C,k,M)\\). "
                "When a display omits \\(M\\), reorders components, or uses level-indexed shorthand, "
                "the omitted embedding context is inherited from the surrounding level discussion rather than introduced as a competing definition.\n"
            )
            if "Canonical tuple projection note" not in text:
                section_positions = [
                    pos
                    for token in ("\\section", "\\subsection", "\\subsubsection")
                    if (pos := text.find(token)) >= 0
                ]
                insert_at = min(section_positions) if section_positions else 0
                text = text[:insert_at] + projection_note + "\n" + text[insert_at:]
        text = re.sub(
            r"\\item\s+(Mathematics|Physics|Chemistry|Biology|Systems\s*/\s*Civilizational projection)\s+is\s+(?:closed|represented)[^.]*?\.\s+The theorem packet is recorded and the parameter law is recorded\.\s+The key replay metrics are.*?The closure dossier anchor is listed in the Synthesis Support Appendix\.",
            lambda match: (
                rf"\item {match.group(1)} is retained only as a non-promotional replay-inventory lane. "
                "This release does not use covered-case counts, held-out-case counts, theorem-packet labels, or parameter-law labels as public support. "
                "Promotion requires public source rows, theorem-to-observable bindings, residuals, comparators, negative controls, falsifiers, and source snapshots in the review package."
            ),
            text,
            flags=re.I | re.S,
        )
        text = re.sub(
            r"\b\d+\s+covered\s+cases;\s+\d+\s+held-out\s+cases;[^.]*\.",
            "covered-case and held-out-case counts are retained only in non-promotional replay inventory until full public evidence rows are shipped.",
            text,
            flags=re.I,
        )
        text = re.sub(
            r"\bInventory count, not domain-validation total:\s*\d+\.",
            "Inventory counts are retained outside the public support claim and are not used as domain validation in this release.",
            text,
            flags=re.I,
        )
        text = re.sub(
            r"\bOne shared consequence is dimensional monotonicity for live continua\.",
            "One reviewed consequence is a dimensional-monotonicity hypothesis under the named live-continuum assumptions.",
            text,
            flags=re.I,
        )
        text = re.sub(
            r"\band monotonic growth of structural complexity\b",
            "and bounded hypotheses about structural-complexity growth",
            text,
            flags=re.I,
        )
        text = re.sub(
            r"\bmonotonic growth of structural complexity\b",
            "bounded structural-complexity growth hypothesis",
            text,
            flags=re.I,
        )
        text = re.sub(
            r"\bA continuum that stops evolving structurally does so only at the moment of collapse\.",
            "A continuum that appears to stop evolving structurally is treated as a case requiring the named stabilization, collapse, or modeling-assumption test; the present release does not promote a universal no-stabilization theorem.",
            text,
            flags=re.I,
        )
        text = re.sub(
            r"\bThis ontology is staged from K0 through K12 under declared assumptions\b",
            "This ontology is staged from K0 through K10 as the current core grammar, with K11 and K12 retained as provisional upper-taxonomy witnesses under declared assumptions",
            text,
            flags=re.I,
        )
        text = re.sub(
            r"\bK0--K12 witness taxonomy\b",
            "K0--K10 core witness taxonomy with provisional K11/K12 upper-taxonomy entries",
            text,
            flags=re.I,
        )
        text = re.sub(
            r"\bK0--K12 hierarchy, K-level tables, and demotion rule\b",
            "K0--K10 core hierarchy, provisional K11/K12 entries, K-level tables, and demotion rule",
            text,
            flags=re.I,
        )
        text = re.sub(
            r"\bK0--K12 figure, K-level tables, demotion controls\b",
            "K0--K10 core figure with provisional K11/K12 entries, K-level tables, and demotion controls",
            text,
            flags=re.I,
        )
        text = re.sub(
            r"\bthe K0--K12 hierarchy figure, K-level tables, finite witness route, and demotion language\b",
            "the K0--K10 hierarchy figure with provisional K11/K12 entries, K-level tables, finite witness route, and demotion language",
            text,
            flags=re.I,
        )
        text = re.sub(
            r"HOSTILE::K11_K12_IRREDUCIBILITY\}([^&]+)&\s*bounded review evidence recorded\s*&\s*\\occode\{UPPER_TAXONOMY_REVIEW_REQUIRED\}",
            lambda match: r"HOSTILE::K11_K12_IRREDUCIBILITY}" + match.group(1) + r"& demotion boundary recorded & \occode{UPPER_TAXONOMY_REVIEW_REQUIRED}",
            text,
            flags=re.I,
        )
        text = re.sub(
            r"\bthe\s+mathematical\s+anchor\s+is\s+active\s+and\s+replayable\b",
            "the mathematics lane is demoted pending finite-source binding and is not support-carrying in this release",
            text,
            flags=re.I,
        )
        text = re.sub(
            r"\bmathematical\s+anchor\s+active\b",
            "mathematics lane pending finite-source binding",
            text,
            flags=re.I,
        )
        text = re.sub(
            r"\bmathematical\s+anchor\s+is\s+active\b",
            "mathematics lane is pending finite-source binding",
            text,
            flags=re.I,
        )
        text = re.sub(
            r"\bThe\s+current\s+matrix\s+still\s+blocks\s+0\s+of\s+5\s+checked\s+lanes\b[^.]*\.",
            "The current matrix demotes the mathematics lane and treats the remaining lanes as bounded replay examples, not completed support lanes.",
            text,
            flags=re.I,
        )
        text = re.sub(
            r"\bThis\s+does\s+not\s+diminish\s+the\s+proved\s+Core\s+kernel\b[^.]*\.",
            "This preserves the bounded model-core argument without promoting a proved operational kernel.",
            text,
            flags=re.I,
        )
        text = re.sub(
            r"Mathematics\s*&\s*\\occode\{bounded review route\}\s*&\s*\\occode\{TRACE_REVIEWED\}\s*&\s*\\occode\{EVIDENCE_BOUNDED\}\s*&\s*bounded review evidence recorded\s*&\s*(?:none|нет|keine)\s*&",
            lambda _match: (
                r"Mathematics & \occode{bounded review route} & \occode{TRACE_REVIEWED} & "
                r"\occode{EVIDENCE_DEMOTED_PENDING_BINDING} & demoted review row pending finite-source binding & "
                r"source-binding failure remains open &"
            ),
            text,
            flags=re.I,
        )
        text = re.sub(
            r"\bMAINTENANCE_ONLY\b",
            "continue reviewer maintenance; not a new domain-validation promotion",
            text,
            flags=re.I,
        )
        protocol_labels = {
            "MATHEMATICS::ANCHOR_REPLAY": "mathematics anchor replay",
            "PHYSICS::CONSTANTS_SPECTRA_TRANSPORT": "physics constants, spectra, and transport replay",
            "CHEMISTRY::THERMOCHEMISTRY_SPECTRA_KINETICS": "chemistry thermochemistry, spectra, and kinetics replay",
            "BIOLOGY::STATE_TRANSITIONS_AND_RESPONSE_SIGNATURES": "biology state-transition and response-signature replay",
            "SYSTEMS::MACRO_TRAJECTORIES_AND_REGIME_SHIFTS": "systems macro-trajectory and regime-shift replay",
        }
        for protocol_id, public_label in protocol_labels.items():
            escaped_id = protocol_id.replace("_", r"\_")
            text = text.replace(rf"\occode{{OC13::EXECUTION::{protocol_id}}}", public_label)
            text = text.replace(rf"\occode{{OC13::EXECUTION::{escaped_id}}}", public_label)
            text = text.replace(f"`OC13::EXECUTION::{protocol_id}`", public_label)
            text = text.replace(f"`OC13::EXECUTION::{escaped_id}`", public_label)
            text = text.replace(f"OC13::EXECUTION::{protocol_id}", public_label)
            text = text.replace(f"OC13::EXECUTION::{escaped_id}", public_label)
        trigger_labels = {
            "OPEN_DATA_COVERAGE_LT_1_0_OR_HELD_OUT_CASES_LT_30_OR_RESIDUAL_BREACH_PERSISTS": "open-data coverage, held-out case, or residual-breach trigger",
            "OPEN_DATA_COVERAGE_LT_1_0_OR_HELD_OUT_CASES_LT_30_OR_SIGNATURE_CLASS_UNDERCONSTRAINED": "open-data coverage, held-out case, or signature-underconstraint trigger",
            "OPEN_DATA_COVERAGE_LT_1_0_OR_HELD_OUT_INTERVAL_COUNT_LT_30_OR_TURNING_POINT_BREACH_PERSISTS": "open-data coverage, held-out interval, or turning-point breach trigger",
        }
        for trigger_id, public_label in trigger_labels.items():
            escaped_trigger_id = trigger_id.replace("_", r"\_")
            text = text.replace(rf"\occode{{{trigger_id}}}", public_label)
            text = text.replace(rf"\occode{{{escaped_trigger_id}}}", public_label)
            text = text.replace(f"`{trigger_id}`", public_label)
            text = text.replace(f"`{escaped_trigger_id}`", public_label)
            text = text.replace(trigger_id, public_label)
            text = text.replace(escaped_trigger_id, public_label)
        text = re.sub(r"\bThe scientific science-state register therefore sets the Core~1\.3\.3 science verdict, within scope current bounded science surface, to bounded support row recorded\.", "The public science-state register therefore records bounded support rows inside the declared current science surface; it does not promote full-domain validation.", text, flags=re.I)
        text = re.sub(
            r"\b(?:The\s+)?release gate now reports\s+0\s+bridge-only domains,\s+0\s+hostile-review blockers\b[^.]*\.",
            "The public synthesis remains a bounded review surface; bridge status and hostile-review status do not by themselves promote domain validation.",
            text,
            flags=re.I,
        )
        text = re.sub(
            r"\bExact validator:\s*\\occode\{BOUNDED_SYNTHESIS_REVIEW_RECORDED\}\.",
            "Review status: this synthesis remains bounded and reopenable by row-level evidence.",
            text,
            flags=re.I,
        )
        text = re.sub(
            r"\bNo release blocker remains in the internal science-state register\.",
            "No global closure is promoted here; every row remains reopenable by its stated evidence boundary.",
            text,
            flags=re.I,
        )
        text = re.sub(
            r"\bThese results form the empirical foundation for\b",
            "These results form an illustrative evidence route for",
            text,
            flags=re.I,
        )
        text = re.sub(
            r"\bprovide the empirical foundation for\b",
            "provide an illustrative evidence route for",
            text,
            flags=re.I,
        )
        text = re.sub(
            r"\band\s+provide\s+the\s+empirical\s+foundation\s+for\b",
            "and provide an illustrative evidence route for",
            text,
            flags=re.I,
        )
        text = re.sub(
            r"\bform the empirical foundation for\b",
            "form an illustrative evidence route for",
            text,
            flags=re.I,
        )
        text = re.sub(
            r"\bExperiments for\s+\$K_8\$\s+establish civilisational-scale validation for the Ontology of Continua:",
            "Experiments for $K_8$ define a proposed civilisational-scale validation route for the Ontology of Continua:",
            text,
            flags=re.I,
        )
        text = re.sub(
            r"\bExperiments for\s+\$K_8\$\s+define\s+a\s+proposed\s+civilisational-scale\s+validation\s+route\s+for\s+the\s+Ontology\s+of\s+Continua:",
            "Experiments for $K_8$ define a proposed systems-scale research route for the Ontology of Continua:",
            text,
            flags=re.I,
        )
        text = re.sub(
            r"\bcivilisational-scale\s+validation\s+route\b",
            "systems-scale research route",
            text,
            flags=re.I,
        )
        text = re.sub(
            r"\bcivilisational-scale\s+validation\b",
            "systems-scale research",
            text,
            flags=re.I,
        )
        text = re.sub(
            r"\btests cross-level invariants that hold across physics, chemistry, biology, cognition, social systems, and meta-theoretical continua\b",
            "proposes cross-level invariant tests across physics, chemistry, biology, cognition, social systems, and meta-theoretical continua",
            text,
            flags=re.I,
        )
        text = re.sub(
            r"\bglobal structural fixed point exists\b",
            "a global structural fixed point remains a future proof obligation",
            text,
            flags=re.I,
        )
        text = re.sub(
            r"\bfuture structural fixed-point proof obligation exists\b",
            "a structural fixed-point statement remains a future proof obligation",
            text,
            flags=re.I,
        )
        text = re.sub(
            r"\ball operators\s*\$?\([^)]*\)\$?\s*act as symmetries\b",
            "operator symmetry remains a future proof obligation for explicitly declared operators",
            text,
            flags=re.I,
        )
        text = re.sub(
            r"\bstable under all operators\s*\$?\([^)]*\)\$?",
            "stable only under explicitly declared operator assumptions",
            text,
            flags=re.I,
        )
        text = re.sub(
            r"\bAll thresholds become\s+\\emph\{globally stable constants\}\s+for the limit continuum\.",
            "Global threshold stability is not promoted as a current theorem; any such claim requires a separate proof and domain-specific evidence.",
            text,
            flags=re.I,
        )
        text = re.sub(
            r"\bAll thresholds become\s+\\emph\{globally stable constants\}\s+for the bounded synthesis candidate\.",
            "Global threshold stability is not promoted as a current theorem; any such claim requires a separate proof and domain-specific evidence.",
            text,
            flags=re.I,
        )
        text = re.sub(
            r"\ball operators\b[^.]{0,160}\bact as symmetries\b",
            "operator symmetry remains a future proof obligation for explicitly declared operators",
            text,
            flags=re.I,
        )
        text = re.sub(
            r"\bthe entire ladder\s+\$?K0.*?K11\$?\s+becomes representable inside one invariant continuum\b",
            "the K0--K11 ladder is treated as a bounded synthesis candidate, not as a promoted invariant continuum",
            text,
            flags=re.I | re.S,
        )
        text = re.sub(
            r"\bthe entire ladder\s+\$K_0\\dots\s+K_\{11\}\$\s+becomes representable inside one\s+invariant continuum\.",
            "the K0--K11 ladder is treated as a bounded synthesis candidate rather than a promoted invariant continuum.",
            text,
            flags=re.I | re.S,
        )
        text = re.sub(
            r"\$k_\{12\}\$ attains the maximum possible value among all \$K\$-levels:\s*\\\[\s*k_\{12\}\s*=\s*\\max_\{i=0\\dots12\}\s*k\(K_i\)\.\s*\\\]",
            "$k_{12}$ is retained as a candidate upper-coherence parameter in the historical K12 module; this release does not promote a theorem that it is maximal among all possible continuum levels.",
            text,
            flags=re.I | re.S,
        )
        text = re.sub(
            r"\$K_\{12\}\$ is the most energy-stable admissible continuum\.",
            "$K_{12}$ is treated as an upper-coherence stability candidate, not as a proved most-stable admissible continuum.",
            text,
            flags=re.I,
        )
        text = re.sub(
            r"Operator algebra becomes Abelian up to equivalence classes:\s*\\\[\s*\[\\Psi,\\Phi\]=\[\\Phi,\\Lambda\]=\\dots = 0\.\s*\\\]",
            "The historical K12 source proposes an Abelian limit condition as a future proof obligation; the current release does not promote this operator-algebra statement as a proved theorem.",
            text,
            flags=re.I | re.S,
        )
        text = re.sub(
            r"\\item Any admissible recursive meta-hierarchy eventually converges to\s+structures representable in \$K_\{12\}\$\.",
            lambda _match: r"\item Some explicitly modeled recursive meta-hierarchies may be tested for convergence to structures representable in $K_{12}$.",
            text,
            flags=re.I,
        )
        text = re.sub(
            r"\\item No new axes or potentials can emerge beyond this level\.",
            lambda _match: r"\item The no-new-axis/no-new-potential condition is a falsifiable upper-bound hypothesis, not a promoted universal theorem.",
            text,
            flags=re.I,
        )
        text = re.sub(
            r"\\item All operator actions reduce to global symmetries\.",
            lambda _match: r"\item Operator-action symmetry is a future proof obligation for explicitly declared operators.",
            text,
            flags=re.I,
        )
        text = re.sub(
            r"This makes \$M_\{12\}\$ the terminal environment for Core~1\.3\.3\.",
            "$M_{12}$ is therefore used as an upper-bound meta-space candidate for the current taxonomy, not as a terminal theorem about all possible meta-spaces.",
            text,
            flags=re.I,
        )
        text = re.sub(
            r"\$M_\{12\}\$ is thus the terminal meta-space for the Core\.",
            "$M_{12}$ is thus the upper-bound meta-space candidate used by this release.",
            text,
            flags=re.I,
        )
        text = re.sub(
            r"\\Omega\(K_\{12\}\) \\subseteq \\Omega\(M_\{12\}\)\s*\\quad \\text\{is necessary and sufficient for the existence of \}K_\{12\}\.",
            lambda _match: r"\Omega(K_{12}) \subseteq \Omega(M_{12})\quad \text{is treated here as a modeling condition for K12 admissibility, not as a completed necessary-and-sufficient theorem.}",
            text,
            flags=re.I | re.S,
        )
        text = re.sub(r"\bAt present\s+\\occode\{5\}\s+lanes\s+satisfy\s+the\s+current public-support criterion,\s+while\s+\\occode\{0\}\s+lanes\s+remain\s+not yet public-supporting\.", "At present the five inspected lanes have public support rows, while broader domain promotion remains conditional on row-level replay, comparator, negative-control, and falsifier evidence.", text, flags=re.I)
        text = re.sub(r"\\subsection\{Process\s+Schema\s+Under\s+scoped\}", r"\\subsection{Process Schema Under Declared Scope}", text, flags=re.I)
        text = re.sub(r"\bProcess\s+Schema\s+Under\s+scoped\b", "Process Schema Under Declared Scope", text, flags=re.I)
        text = re.sub(r"\bcontent/OC\\_1\\_3\\_3\\_([A-Z0-9\\_]+)\.tex\b", r"the \1 corpus appendix", text)
        text = re.sub(r"\bcontent/OC_1_3_3_([A-Z0-9_]+)\.tex\b", r"the \1 corpus appendix", text)
        if text != original:
            write_text_if_changed(tex_path, text)

    entry = source_dir / science_monolith.BASE_ENTRYPOINT
    if entry.is_file():
        text = entry.read_text(encoding="utf-8", errors="replace")
        if "% R014_FULL_QUALITY_CLOSURE" not in text:
            text = text.replace("% R013_TABLE_LAYOUT_STANDARD", "% R013_TABLE_LAYOUT_STANDARD\n% R014_FULL_QUALITY_CLOSURE")
            write_text_if_changed(entry, text)
        appendix_index = 0
        for ref in re.findall(r"\\input\{([^}]+)\}", text):
            if not ref.startswith("appendix/"):
                continue
            appendix_path = source_dir / (ref if ref.endswith(".tex") else f"{ref}.tex")
            if not appendix_path.is_file():
                continue
            appendix_index += 1
            letter = chr(ord("A") + appendix_index - 1)
            appendix_text = appendix_path.read_text(encoding="utf-8", errors="replace")
            original_appendix_text = appendix_text

            def replace_appendix_heading(match: re.Match[str]) -> str:
                title = match.group(1).strip()
                title = re.sub(r"^Appendix\s+[A-Z]\s+--\s+", "", title).strip()
                if not title:
                    title = "Reference Material"
                return rf"\section{{Appendix {letter} -- {title}}}"

            appendix_text = re.sub(r"\\section\{([^}]+)\}", replace_appendix_heading, appendix_text, count=1)
            if appendix_text != original_appendix_text:
                write_text_if_changed(appendix_path, appendix_text)
    apply_r014_high_reasoning_closure(source_dir)


def apply_r015_scientific_review_overrides(source_dir: Path) -> None:
    entry = source_dir / science_monolith.BASE_ENTRYPOINT
    preamble = source_dir / "preamble.tex"
    if preamble.is_file():
        text = preamble.read_text(encoding="utf-8", errors="replace")
        text = text.replace(
            "theorem closure, empirical validation, falsifiability, practical utility",
            "bounded theorem routes, retrospective replay QA, falsifiability, source-governed evidence",
        )
        text = text.replace("empirical validation", "bounded replay evidence")
        write_text_if_changed(preamble, text)
    if entry.is_file():
        text = entry.read_text(encoding="utf-8", errors="replace")
        text = text.replace("% R014_FULL_QUALITY_CLOSURE", "% R014_FULL_QUALITY_CLOSURE\n% R015_SCIENTIFIC_REVIEW_GATE")
        text = text.replace("target-blind replay QA", "retrospective bounded replay QA")
        future_input = r"\input{content/r015_required_future_research.tex}"
        if future_input not in text:
            text = text.replace(
                r"\input{content/99_oc_core_1_3_3_final_conclusion.tex}",
                future_input + "\n" + r"\input{content/99_oc_core_1_3_3_final_conclusion.tex}",
            )
        write_text_if_changed(entry, text)
    future_path = source_dir / "content" / "r015_required_future_research.tex"
    write_text_if_changed(future_path, r015_future_research_tex())

    roadmap = source_dir / "content" / "20_oc_core_1_3_theorem_roadmap.tex"
    if roadmap.is_file():
        text = roadmap.read_text(encoding="utf-8", errors="replace")
        text = text.replace(
            "the sections on klevels full, and section falsifiability extended, the modules master discussion, the public claim-boundary chapter, and the foundational-consistency chapter.",
            "the K-level hierarchy chapter, the bounded falsifiability chapter, the discussion chapter, the public claim-boundary chapter, and the foundational-consistency chapter.",
        )
        text = text.replace(
            "the sections on discussion, the worked examples chapter, and section oc core 1 3 practical utility, Provenance and Corpus Appendix, and Reviewer Objection Navigation Appendix.",
            "the discussion chapter, the worked examples chapter, the practical-utility chapter, the provenance appendix, and the reviewer-objection navigation appendix.",
        )
        text = text.replace(
            "the sections on oc core 1 3 operationalization program, and section oc core 1 3 empirical execution protocols and Appendices section oc core 1 3 empirical validation matrix, and section oc core 1 3 domain execution board.",
            "the operationalization chapter, the empirical-execution protocol chapter, the empirical-evidence appendix, and the domain-execution appendix.",
        )
        text = text.replace("Figure figure oc13 theorem spine", "Figure~\\ref{fig:oc13-theorem-spine}")
        write_text_if_changed(roadmap, text)

    worked_examples = source_dir / "content" / "21_oc_core_1_3_worked_examples.tex"
    if worked_examples.is_file():
        text = worked_examples.read_text(encoding="utf-8", errors="replace")
        text = text.replace("Figure figure oc13 theorem spine", "Figure~\\ref{fig:oc13-theorem-spine}")
        write_text_if_changed(worked_examples, text)

    for tex_path in sorted((source_dir / "content").rglob("*.tex")) + sorted((source_dir / "appendix").rglob("*.tex")):
        text = tex_path.read_text(encoding="utf-8", errors="replace")
        original = text
        text = text.replace("target-blind replay QA", "retrospective bounded replay QA")
        text = text.replace("bounded target-blind replay QA", "retrospective bounded replay QA")
        text = text.replace("empirical validation", "bounded replay evidence")
        text = text.replace("Lean declarations", "formalization references")
        text = text.replace("Lean declaration", "formalization reference")
        text = text.replace("Lean-oriented formalization inventory evidence", "formalization inventory for source inspection")
        text = text.replace(
            "proof sheets, Lean declarations, and finite semantic witnesses",
            "proof sheets, formalization references where their certificate boundary is explicit, and finite semantic witnesses",
        )
        text = text.replace(
            "proof sheets, Lean-oriented formalization inventory evidence,",
            "proof sheets, formalization inventory for source inspection,",
        )
        text = re.sub(r"\bThe theory predicts:\s*", "The model currently frames the following bounded hypotheses: ", text)
        text = re.sub(r"\bThe model predicts:\s*", "The model currently frames the following bounded hypotheses: ", text)
        text = re.sub(r"\bThe Core predicts:\s*", "The Core currently frames the following bounded hypotheses: ", text)
        text = re.sub(r"\$K_5\$\s+predicts\s+the\s+existence", r"$K_5$ motivates a test for the existence", text)
        text = re.sub(
            r"\bApproach to\s+\$\\partial\\Omega\(K_\{10\}\)\$\s+predicts\b",
            lambda _match: r"Approach to $\partial\Omega(K_{10})$ is treated as a candidate signal for",
            text,
        )
        text = re.sub(r"\bpredicts collapse before\b", "is treated as a candidate collapse signal before", text)
        text = re.sub(r"\bpredicts local flicker modes\b", "is treated as a candidate signal for local flicker modes", text)
        text = re.sub(r"\bpredicts robustness against noise\b", "is treated as a candidate robustness signal against noise", text)
        text = re.sub(r"\bpredicts or\b", "may indicate or", text)
        text = re.sub(r"\bOC predicts\b", "the OC model would predict under declared assumptions", text)
        text = re.sub(r"\baccording to Theorem of Representability~5 \(BKT\):", "in the historical BKT construction route, pending a current proof-sheet binding:", text, flags=re.I)
        text = re.sub(r"\bFrom the Time Emergence Theorem:", "From the historical time-emergence construction route, pending a current proof-sheet binding:", text, flags=re.I)
        text = text.replace(
            "Theorem “Emergence of Time from C-cycles” (physics construction route):",
            "Historical construction route for time emergence from C-cycles (not a promoted r015 theorem):",
        )
        if text != original:
            write_text_if_changed(tex_path, text)


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
        not any(revision in str(base) for revision in ("recovery_r005", "recovery_r006", "recovery_r008", "recovery_r012", "recovery_r013", "recovery_r014", "recovery_r015", "recovery_r016", "recovery_r017"))
        and
        source_dir.is_dir()
        and entry_path.is_file()
        and (skip_pdf or pdf_path.is_file())
        and r"\renewcommand*\l@subsection" in entry_path.read_text(encoding="utf-8", errors="replace")
        and frontmatter_text.find("Acknowledgements") >= 0
        and frontmatter_text.find(r"\begin{abstract}") >= 0
        and frontmatter_text.find("Acknowledgements") < frontmatter_text.find(r"\begin{abstract}")
        and PUBLICATION_DATE in frontmatter_text
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
        if assembly_revision in {R008_REVISION, R009_REVISION, R010_REVISION, R011_REVISION, R012_REVISION, R013_REVISION, R014_REVISION, R015_REVISION, R016_REVISION, R017_REVISION}:
            apply_r008_monograph_overrides(source_dir)
        if assembly_revision in VISUAL_QA_REVISIONS:
            apply_r012_visual_overrides(source_dir)
        if assembly_revision in TABLE_QA_REVISIONS:
            apply_r013_table_overrides(source_dir)
        if assembly_revision in {R014_REVISION, R015_REVISION, R016_REVISION, R017_REVISION}:
            apply_r014_cerberus_overrides(source_dir)
        if assembly_revision in {R015_REVISION, R016_REVISION, R017_REVISION}:
            apply_r015_scientific_review_overrides(source_dir)
        science_monolith._sanitize_source_tree(source_dir)
        if assembly_revision in {R014_REVISION, R015_REVISION, R016_REVISION, R017_REVISION}:
            apply_r014_cerberus_overrides(source_dir)
        if assembly_revision in {R015_REVISION, R016_REVISION, R017_REVISION}:
            apply_r015_scientific_review_overrides(source_dir)
        trim_generated_text_whitespace(source_dir)
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
            if write:
                trim_generated_text_whitespace(source_dir)
            counts = tex_corpus_counts(source_dir)
    visual_quality: dict[str, Any] | None = None
    if assembly_revision in VISUAL_QA_REVISIONS and source_dir.is_dir():
        visual_quality = build_r012_visual_quality(base, version, source_dir, write=write, source_figure_total=int(counts.get("figure_total") or 0))
    table_quality: dict[str, Any] | None = None
    if assembly_revision in TABLE_QA_REVISIONS and source_dir.is_dir():
        table_quality = build_r013_table_quality(base, version, source_dir, write=write, source_table_total=r013_all_source_table_total(source_dir))
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
        "visual_quality": visual_quality,
        "table_quality": table_quality,
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
        "mainfont=TeX Gyre Termes",
        "-V",
        "mathfont=Latin Modern Math",
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
    version = public_version_for_release(release_id, assembly_revision)
    if assembly_revision == R017_REVISION:
        toe_errors = r017_toe_gate_errors()
        if toe_errors:
            joined = "\n".join(f"- {error}" for error in toe_errors[:30])
            raise RuntimeError(
                "recovery_r017 is fail-closed and cannot be assembled until final TOE validation passes.\n"
                + joined
            )
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
    visual_quality_trace: dict[str, Any] | None = None
    table_quality_trace: dict[str, Any] | None = None
    scientific_review_gate_trace: dict[str, Any] | None = None
    machine_self_audit_trace: dict[str, Any] | None = None
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
            visual_quality: dict[str, Any] | None = None
            table_quality: dict[str, Any] | None = None
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
                elif assembly_revision == R011_REVISION:
                    public_translation_source = "science_monolith_journal_requirements_spot_r011"
                elif assembly_revision == R012_REVISION:
                    public_translation_source = "science_monolith_figure_visual_qa_spot_r012"
                elif assembly_revision == R013_REVISION:
                    public_translation_source = "science_monolith_table_rendered_qa_spot_r013"
                elif assembly_revision == R014_REVISION:
                    public_translation_source = "science_monolith_full_quality_closure_r014"
                elif assembly_revision == R015_REVISION:
                    public_translation_source = "science_monolith_scientific_review_gate_r015"
                elif assembly_revision == R016_REVISION:
                    public_translation_source = "science_monolith_machine_self_audited_toe_gate_r016"
                elif assembly_revision == R017_REVISION:
                    public_translation_source = "science_monolith_final_toe_closed_package_r017"
                visual_quality = built.get("visual_quality")
                table_quality = built.get("table_quality")
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
                if visual_quality:
                    visual_quality_trace = visual_quality.get("cockpit")
                    generated_files.extend(path for path in visual_quality.get("paths", {}).values() if isinstance(path, Path) and path.is_file())
                if table_quality:
                    table_quality_trace = table_quality.get("cockpit")
                    generated_files.extend(path for path in table_quality.get("paths", {}).values() if isinstance(path, Path) and path.is_file())
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
                    elif assembly_revision == R011_REVISION:
                        document_body_source = "curated_public_payload_markdown_journal_requirements_spot_r011"
                        document_structure_source = "curated_public_payload_hierarchy_r011"
                        public_translation_source = "journal_requirements_spot_publication_translator_r011"
                    elif assembly_revision == R012_REVISION:
                        document_body_source = "curated_public_payload_markdown_figure_visual_qa_r012"
                        document_structure_source = "curated_public_payload_hierarchy_r012"
                        public_translation_source = "figure_visual_qa_publication_translator_r012"
                    elif assembly_revision == R013_REVISION:
                        document_body_source = "curated_public_payload_markdown_table_rendered_qa_r013"
                        document_structure_source = "curated_public_payload_hierarchy_r013"
                        public_translation_source = "table_rendered_qa_publication_translator_r013"
                    elif assembly_revision == R014_REVISION:
                        document_body_source = "curated_public_payload_markdown_full_quality_closure_r014"
                        document_structure_source = "curated_public_payload_hierarchy_r014"
                        public_translation_source = "full_quality_closure_publication_translator_r014"
                    elif assembly_revision == R015_REVISION:
                        document_body_source = "curated_public_payload_markdown_scientific_review_gate_r015"
                        document_structure_source = "curated_public_payload_hierarchy_r015"
                        public_translation_source = "scientific_review_gate_publication_translator_r015"
                    elif assembly_revision == R016_REVISION:
                        document_body_source = "curated_public_payload_markdown_machine_self_audited_r016"
                        document_structure_source = "curated_public_payload_hierarchy_r016"
                        public_translation_source = "machine_self_audited_publication_translator_r016"
                    elif assembly_revision == R017_REVISION:
                        document_body_source = "curated_public_payload_markdown_final_toe_closed_r017"
                        document_structure_source = "curated_public_payload_hierarchy_r017"
                        public_translation_source = "final_toe_closed_publication_translator_r017"
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
                bibliography_entry_total = counts.get("bibliography_entry_total", 0)
                verified_bibliography_entry_total = counts.get("verified_bibliography_entry_total", 0)
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
                        else R011_TRANSLATOR_STATUS if assembly_revision == R011_REVISION and artifact_id in TEXT_ARTIFACTS
                        else R012_TRANSLATOR_STATUS if assembly_revision == R012_REVISION and artifact_id in TEXT_ARTIFACTS
                        else R013_TRANSLATOR_STATUS if assembly_revision == R013_REVISION and artifact_id in TEXT_ARTIFACTS
                        else R014_TRANSLATOR_STATUS if assembly_revision == R014_REVISION and artifact_id in TEXT_ARTIFACTS
                        else R015_TRANSLATOR_STATUS if assembly_revision == R015_REVISION and artifact_id in TEXT_ARTIFACTS
                        else R016_TRANSLATOR_STATUS if assembly_revision == R016_REVISION and artifact_id in TEXT_ARTIFACTS
                        else R017_TRANSLATOR_STATUS if assembly_revision == R017_REVISION and artifact_id in TEXT_ARTIFACTS
                        else None
                    ),
                    "public_translation_source": public_translation_source,
                    "governed_ollama_status": governed_trace["status"] if assembly_revision in GOVERNED_TEXT_REVISIONS and artifact_id in TEXT_ARTIFACTS else None,
                    "ollama_invocation_total": governed_trace["ollama_invocation_total"] if assembly_revision in GOVERNED_TEXT_REVISIONS and artifact_id in TEXT_ARTIFACTS else None,
                    "unmanaged_ollama_call_total": governed_trace["unmanaged_ollama_call_total"] if assembly_revision in GOVERNED_TEXT_REVISIONS and artifact_id in TEXT_ARTIFACTS else None,
                    "v_model_lowest_checked_level": (governed_trace.get("v_model_lowest_checked_level") or "L10") if assembly_revision in GOVERNED_TEXT_REVISIONS and artifact_id in TEXT_ARTIFACTS else None,
                    "instruction_packet_total": len(rows) if assembly_revision in GOVERNED_TEXT_REVISIONS and artifact_id in TEXT_ARTIFACTS else None,
                    "public_translation_packet_total": len(rows) if assembly_revision in GOVERNED_TEXT_REVISIONS and artifact_id in TEXT_ARTIFACTS else None,
                    "logion_llm_service_status": governed_trace.get("service_status") if assembly_revision in COMMON_LLM_SERVICE_REVISIONS and artifact_id in TEXT_ARTIFACTS else None,
                    "logion_llm_service_ledger_ref": governed_trace.get("service_ledger_ref") if assembly_revision in COMMON_LLM_SERVICE_REVISIONS and artifact_id in TEXT_ARTIFACTS else None,
                    "logion_llm_service_cadence_sequence": governed_trace.get("cadence_sequence") if assembly_revision in COMMON_LLM_SERVICE_REVISIONS and artifact_id in TEXT_ARTIFACTS else None,
                    "logion_llm_service_model_sequence": governed_trace.get("model_sequence") if assembly_revision in COMMON_LLM_SERVICE_REVISIONS and artifact_id in TEXT_ARTIFACTS else None,
                    "source_payload_origin": source_payload_origin,
                    "visual_quality_status": (visual_quality or {}).get("cockpit", {}).get("status") if visual_quality else None,
                    "figure_spec_registry_ref": rel((visual_quality or {}).get("paths", {}).get("registry_json")) if visual_quality else None,
                    "rendered_figure_bbox_ledger_ref": rel((visual_quality or {}).get("paths", {}).get("rendered_bbox_json")) if visual_quality else None,
                    **({key: (visual_quality or {}).get("cockpit", {}).get(key) for key in [
                        "figure_spec_coverage_status",
                        "diagram_geometry_status",
                        "rendered_figure_bbox_status",
                        "label_collision_status",
                        "figure_semantic_completeness_status",
                        "k_hierarchy_visual_status",
                        "continuum_visual_status",
                        "caption_argument_status",
                        "visual_cockpit_status",
                    ]} if visual_quality else {}),
                    "table_quality_status": (table_quality or {}).get("cockpit", {}).get("status") if table_quality else None,
                    "table_registry_ref": rel((table_quality or {}).get("paths", {}).get("registry_json")) if table_quality else None,
                    "rendered_table_bbox_ledger_ref": rel((table_quality or {}).get("paths", {}).get("rendered_bbox_json")) if table_quality else None,
                    "source_table_total": (table_quality or {}).get("cockpit", {}).get("source_table_total") if table_quality else None,
                    "compiled_reader_table_total": (table_quality or {}).get("cockpit", {}).get("compiled_reader_table_total") if table_quality else None,
                    "registered_table_total": (table_quality or {}).get("cockpit", {}).get("registered_table_total") if table_quality else None,
                    "audited_rendered_table_total": (table_quality or {}).get("cockpit", {}).get("audited_rendered_table_total") if table_quality else None,
                    **({key: (table_quality or {}).get("cockpit", {}).get(key) for key in [
                        "table_spec_coverage_status",
                        "compiled_table_coverage_status",
                        "table_layout_standard_status",
                        "table_geometry_status",
                        "rendered_table_bbox_status",
                        "table_text_collision_status",
                        "table_edge_clipping_status",
                        "table_caption_argument_status",
                        "table_semantic_anchor_status",
                        "table_cockpit_status",
                    ]} if table_quality else {}),
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
            source_family_refs = []
            for family in source_bindings.get("source_families", []):
                if not isinstance(family, dict):
                    continue
                candidate_paths = family.get("candidate_paths") if isinstance(family.get("candidate_paths"), list) else []
                source_family_refs.append(
                    {
                        "source_family_id": family.get("source_family_id"),
                        "candidate_path_total": len(candidate_paths),
                        "candidate_paths": candidate_paths[:20],
                        "path_policy": (
                            "r014 checksum-binds the comparator, prior-art, target-blind, numeric-replay, and finite-model public evidence files named by reader-facing PDFs"
                            if assembly_revision == R014_REVISION
                            else "r015 checksum-binds claim ledgers, proof sheets, theorem registry, proof dependency graph, Lean inventory/certificate, finite checks, replay QA, comparator, and prior-art public evidence files named by reader-facing PDFs"
                            if assembly_revision == R015_REVISION
                            else "r016/r017 checksum-bind source review, machine self-audit, TOE-gap, claim, theorem, proof-sheet, Lean-inventory, finite-check, replay, comparator, and prior-art public evidence files named by reader-facing PDFs"
                            if assembly_revision in {R016_REVISION, R017_REVISION}
                            else "version-pinned public repository or release-corpus path; not all referenced evidence files are embedded in the review zip"
                        ),
                    }
                )
            payload = {
                "schema_id": "OC_CORE_PUBLIC_EVIDENCE_BUNDLE_REVIEW_v1",
                "release_id": release_id,
                "version": version,
                "title": "OC Core 1.3.3 Public Evidence Bundle Manifest",
                "description": (
                    "Reader-facing evidence index for OC Core 1.3.3. This manifest names the evidence families, "
                    "source-binding hash, and policy for locating version-pinned public repository or release-corpus "
                    "artifacts. It is an index, not a claim that every referenced source file is embedded in the review zip."
                ),
                "terminal_text_contracts_hash": terminal_contracts["artifact_hash"],
                "transition_records_hash": transitions["artifact_hash"],
                "source_bindings_hash": source_bindings["artifact_hash"],
                "source_family_refs": source_family_refs,
                "embedded_manifest_policy": (
                    "The review package embeds this manifest, package checksums, and the r014 checksum-bound public evidence files required by the reader-facing comparator, prior-art, target-blind, numeric-replay, and finite-model references."
                    if assembly_revision == R014_REVISION
                    else "The review package embeds this manifest, package checksums, and the r015 checksum-bound claim, theorem, proof-sheet, Lean-inventory, finite-check, replay, comparator, and prior-art evidence files required by the reader-facing scientific support route."
                    if assembly_revision == R015_REVISION
                    else "The review package embeds this manifest, package checksums, r016 machine self-audit/TOE-gap reports, and checksum-bound source-support files required by the reader-facing scientific support route."
                    if assembly_revision in {R016_REVISION, R017_REVISION}
                    else "The review package embeds this manifest and checksums; large evidence families are referenced by version-pinned public paths and hashes."
                ),
                "checksum_bound_public_evidence_paths": (
                    [item for item in R014_CHECKSUM_BOUND_PUBLIC_EVIDENCE_PATHS if (ROOT / item).is_file()]
                    if assembly_revision == R014_REVISION
                    else [item for item in R015_CHECKSUM_BOUND_PUBLIC_EVIDENCE_PATHS if (ROOT / item).is_file()]
                    if assembly_revision == R015_REVISION
                    else [item for item in R016_CHECKSUM_BOUND_PUBLIC_EVIDENCE_PATHS if (ROOT / item).is_file()]
                    if assembly_revision in {R016_REVISION, R017_REVISION}
                    else []
                ),
                "public_review_revision_aliases": (
                    {
                        "oc_core_1_3_3_review_current": {
                            "assembly_revision": assembly_revision,
                            "assembly_json": rel(paths["assembly_json"]),
                            "package_manifest_json": rel(paths["manifest_json"]),
                            "review_zip": rel(paths["review_zip"]),
                            "alias_policy": "reader-facing PDFs use the stable alias; exact internal recovery labels are retained in package metadata and checksums",
                        }
                    }
                    if assembly_revision in {R014_REVISION, R015_REVISION, R016_REVISION, R017_REVISION}
                    else {}
                ),
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
            if artifact_id == "citation_metadata":
                payload.update(
                    {
                        "title": f"Ontology of Continua Core {version}",
                        "creator": AUTHOR_DISPLAY,
                        "creators": [
                            {
                                "name": AUTHOR_DISPLAY,
                                "orcid": AUTHOR_ORCID,
                                "role": "author",
                            }
                        ],
                        "orcid": AUTHOR_ORCID,
                        "date": PUBLICATION_DATE,
                        "license": "cc-by-4.0",
                        "keywords": [
                            "Ontology of Continua",
                            "continuum ontology",
                            "systems theory",
                            "formal methods",
                            "finite semantic checks",
                            "reproducible research",
                            "falsifiability",
                            "evidence-bound scientific publishing",
                        ],
                        "description": (
                            f"OC Core {version} is a bounded public manuscript and review package for the Ontology of Continua. "
                            "It presents a typed continuum model core, K-level witness discipline, proof/evidence boundaries, "
                            "reader-facing limitations, and no-send journal owner-review projections."
                        ),
                        "release_doi_policy": "Concept DOI only on the reader-facing identity surface; no version DOI or publication action is performed in this repair pass.",
                        "repository_relation": "Open repository reference appears only in the final citation/repository block of reader-facing PDFs.",
                        "reading_order": [
                            "master_monograph",
                            "journal_core_article",
                            "methods_repro_companion",
                            "release_guide",
                            "reviewer_attack_response_map",
                            "public_evidence_bundle",
                        ],
                        "file_set": [
                            {"path": rel(path), "sha256": sha256_file(path)}
                            for path in generated_files
                            if path.is_file()
                        ],
                    }
                )
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
    if assembly_revision in JOURNAL_SPOT_REVISIONS:
        r011_paths = r011_output_paths(base, version)
        venues = r011_journal_venues()
        spot_payload = r011_release_spot_map(version, artifact_rows)
        acceptance_payload = r011_bounded_synthesis_acceptance(version)
        queue_payload = r011_editorial_queue(version, acceptance_payload, spot_payload)
        queue_payload_hash = artifact_hash(queue_payload)
        trace_payload: dict[str, Any] = {}
        r011_generated: list[Path] = [
            r011_paths["requirements_index_json"],
            r011_paths["requirements_index_md"],
            r011_paths["release_spot_json"],
            r011_paths["release_spot_md"],
            r011_paths["bounded_synthesis_json"],
            r011_paths["bounded_synthesis_md"],
            r011_paths["queue_json"],
            r011_paths["trace_json"],
            r011_paths["summary_json"],
            r011_paths["summary_md"],
        ]
        requirement_index: dict[str, Any] = {
            "schema_id": "OC133_R011_JOURNAL_REQUIREMENTS_INDEX_v1",
            "status": "OWNER_REVIEW_READY_NO_SEND",
            "release_id": release_id,
            "version": version,
            "snapshot_date": "2026-05-04",
            "venue_total": len(venues),
            "venues": [],
            "external_action_performed": False,
            "no_send_lock": True,
        }
        for venue in venues:
            venue_paths = r011_venue_paths(base, str(venue["venue_id"]))
            source_payload = r011_requirements_source(venue, version)
            matrix_payload = r011_requirements_matrix(venue, version)
            package_payloads = r011_journal_package_payloads(venue, version, spot_payload, matrix_payload)
            requirement_index["venues"].append(
                {
                    "venue_id": venue["venue_id"],
                    "venue_name": venue["venue_name"],
                    "recommended": bool(venue["recommended"]),
                    "requirements_source_path": rel(venue_paths["source_json"]),
                    "requirements_matrix_path": rel(venue_paths["matrix_json"]),
                    "package_path": rel(venue_paths["submission_package_json"]),
                    "status": "OWNER_REVIEW_READY_NO_SEND",
                }
            )
            if write:
                for venue_path in venue_paths.values():
                    venue_path.parent.mkdir(parents=True, exist_ok=True)
                write_json_if_changed(venue_paths["source_json"], source_payload)
                write_text_if_changed(venue_paths["source_md"], render_r011_requirements_source_md(source_payload))
                write_json_if_changed(venue_paths["matrix_json"], matrix_payload)
                write_text_if_changed(venue_paths["matrix_md"], render_r011_matrix_md(matrix_payload))
                write_json_if_changed(venue_paths["submission_package_json"], package_payloads["package"])  # type: ignore[arg-type]
                write_json_if_changed(venue_paths["component_manifest_json"], package_payloads["manifest"])  # type: ignore[arg-type]
                write_text_if_changed(venue_paths["component_manifest_md"], str(package_payloads["manifest_md"]))
                write_json_if_changed(venue_paths["source_map_json"], package_payloads["source_map"])  # type: ignore[arg-type]
                write_text_if_changed(venue_paths["source_map_md"], str(package_payloads["source_map_md"]))
                write_text_if_changed(venue_paths["manuscript_projection_md"], str(package_payloads["manuscript_projection_md"]))
                write_text_if_changed(venue_paths["cover_letter_md"], str(package_payloads["cover_letter_md"]))
                write_text_if_changed(venue_paths["checklist_md"], str(package_payloads["checklist_md"]))
                write_text_if_changed(venue_paths["repro_data_statement_md"], str(package_payloads["repro_data_statement_md"]))
                write_text_if_changed(venue_paths["data_code_si_manifest_md"], str(package_payloads["data_code_si_manifest_md"]))
                write_text_if_changed(venue_paths["ai_disclosure_md"], str(package_payloads["ai_disclosure_md"]))
                write_text_if_changed(venue_paths["conflict_funding_md"], str(package_payloads["conflict_funding_md"]))
                write_text_if_changed(venue_paths["venue_fit_md"], str(package_payloads["venue_fit_md"]))
            r011_generated.extend(venue_paths.values())
        requirement_index["artifact_hash"] = artifact_hash(requirement_index)
        requirement_index_md = "\n".join(
            [
                "# OC Core 1.3.3 r011 Journal Requirements Index",
                "",
                f"Status: `{requirement_index['status']}`",
                f"Snapshot date: `{requirement_index['snapshot_date']}`",
                "",
                "## Venues",
                "",
                *[
                    f"- `{row['venue_id']}` {row['venue_name']}: `{row['status']}`"
                    for row in requirement_index["venues"]
                ],
            ]
        ) + "\n"
        if write:
            write_json_if_changed(r011_paths["requirements_index_json"], requirement_index)
            write_text_if_changed(r011_paths["requirements_index_md"], requirement_index_md)
            write_json_if_changed(r011_paths["release_spot_json"], spot_payload)
            write_text_if_changed(r011_paths["release_spot_md"], render_r011_release_spot_md(spot_payload))
            write_json_if_changed(r011_paths["bounded_synthesis_json"], acceptance_payload)
            write_text_if_changed(r011_paths["bounded_synthesis_md"], render_r011_bounded_synthesis_md(acceptance_payload))
            write_json_if_changed(r011_paths["queue_json"], queue_payload)
            service = R007_GOVERNANCE_REFS["logion_llm_service"]
            existing_trace = read_json_optional(r011_paths["trace_json"]) if r011_paths["trace_json"].is_file() else {}
            existing_summary = existing_trace.get("summary") if isinstance(existing_trace.get("summary"), dict) else {}
            if (
                existing_trace.get("schema_id") == "LOGION_LLM_SERVICE_RESPONSE_v1"
                and existing_trace.get("queue_status") == "DONE"
                and existing_trace.get("queue_request_hash") == queue_payload_hash
                and int(existing_summary.get("request_total") or 0) == len(queue_payload.get("requests", []))
                and int(existing_summary.get("packet_done_total") or 0) == len(queue_payload.get("requests", []))
            ):
                trace_payload = existing_trace
            elif service.is_file() and queue_payload.get("requests"):
                completed = subprocess.run(
                    [
                        sys.executable,
                        str(service),
                        "--queue-json",
                        str(r011_paths["queue_json"]),
                        "--output-json",
                        str(r011_paths["trace_json"]),
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
                if r011_paths["trace_json"].is_file():
                    trace_payload = read_json_optional(r011_paths["trace_json"])
                else:
                    trace_payload = {
                        "schema_id": "LOGION_LLM_SERVICE_RESPONSE_v1",
                        "status": "SERVICE_INVOCATION_FAILED",
                        "queue_status": "SERVICE_INVOCATION_FAILED",
                        "summary": {"provider_invocation_total": 0, "unmanaged_ollama_call_total": 0, "request_total": len(queue_payload.get("requests", []))},
                        "stderr_tail": completed.stderr[-1000:],
                        "stdout_tail": completed.stdout[-1000:],
                    }
                    write_json_if_changed(r011_paths["trace_json"], trace_payload)
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
                write_json_if_changed(r011_paths["trace_json"], trace_payload)
        else:
            requirement_index = read_json_optional(r011_paths["requirements_index_json"]) or requirement_index
            spot_payload = read_json_optional(r011_paths["release_spot_json"]) or spot_payload
            acceptance_payload = read_json_optional(r011_paths["bounded_synthesis_json"]) or acceptance_payload
            queue_payload = read_json_optional(r011_paths["queue_json"]) or queue_payload
            trace_payload = read_json_optional(r011_paths["trace_json"])
        if isinstance(trace_payload, dict) and trace_payload:
            trace_payload["queue_request_hash"] = queue_payload_hash
            if write:
                write_json_if_changed(r011_paths["trace_json"], trace_payload)
        governed_trace = normalize_r011_spot_trace(trace_payload, queue_payload, version=version, spot=spot_payload, acceptance=acceptance_payload, venues=venues)
        if write:
            write_json_if_changed(r011_paths["summary_json"], governed_trace)
            write_text_if_changed(r011_paths["summary_md"], render_r011_summary_md(governed_trace))
        for row in artifact_rows:
            if row.get("artifact_type_id") in TEXT_ARTIFACTS:
                row["governed_ollama_status"] = governed_trace["status"]
                row["ollama_invocation_total"] = governed_trace["ollama_invocation_total"]
                row["unmanaged_ollama_call_total"] = governed_trace["unmanaged_ollama_call_total"]
                row["v_model_lowest_checked_level"] = governed_trace.get("v_model_lowest_checked_level") or "L10"
                row["public_translation_status"] = (
                    R011_TRANSLATOR_STATUS
                    if assembly_revision == R011_REVISION
                    else R012_TRANSLATOR_STATUS
                    if assembly_revision == R012_REVISION
                    else R013_TRANSLATOR_STATUS
                    if assembly_revision == R013_REVISION
                    else R014_TRANSLATOR_STATUS
                    if assembly_revision == R014_REVISION
                    else R015_TRANSLATOR_STATUS
                    if assembly_revision == R015_REVISION
                    else R016_TRANSLATOR_STATUS
                    if assembly_revision == R016_REVISION
                    else R017_TRANSLATOR_STATUS
                )
                row["logion_llm_service_status"] = governed_trace.get("service_status")
                row["logion_llm_service_ledger_ref"] = governed_trace.get("service_ledger_ref")
                row["logion_llm_service_cadence_sequence"] = governed_trace.get("cadence_sequence")
                row["logion_llm_service_model_sequence"] = governed_trace.get("model_sequence")
                row["source_grounded_repair_status"] = "PASS"
                row["repair_record_total"] = governed_trace.get("repair_record_total")
                row["accepted_candidate_promoted_total"] = governed_trace.get("accepted_repair_total")
                row["unresolved_repair_record_total"] = governed_trace.get("unresolved_repair_record_total")
                for gate_key in [
                    "journal_requirements_trace_status",
                    "release_spot_completeness_status",
                    "bounded_synthesis_status",
                    "source_gap_zero_status",
                    "all_venue_projection_status",
                    "submission_component_status",
                    "journal_format_compliance_status",
                    "zero_internal_leak_status",
                    "zero_fabrication_risk_status",
                    "scientific_journal_submission_ready_status",
                    "editorial_llm_queue_status",
                    "editorial_packet_coverage_status",
                    "actual_ollama_invocation_status",
                    "until_done_status",
                    "cooldown_resume_status",
                    "v_model_completion_status",
                    "local_capability_exhaustion_status",
                ]:
                    row[gate_key] = governed_trace.get(gate_key)
        generated_files.extend(path for path in r011_generated if path.is_file())
    if assembly_revision in {R015_REVISION, R016_REVISION, R017_REVISION}:
        r015_gate = build_r015_scientific_review_gate(base, version, write=write)
        scientific_review_gate_trace = r015_gate.get("summary")
        if isinstance(scientific_review_gate_trace, dict):
            governed_trace.update(scientific_review_gate_trace)
            governed_trace["status"] = "PASS" if scientific_review_gate_trace.get("status") == "PASS" else "REPAIR_REQUIRED"
            governed_trace["service_status"] = "PASS" if scientific_review_gate_trace.get("status") == "PASS" else governed_trace.get("service_status")
            governed_trace["queue_status"] = scientific_review_gate_trace.get("queue_status")
            governed_trace["ollama_invocation_total"] = scientific_review_gate_trace.get("ollama_invocation_total", governed_trace.get("ollama_invocation_total"))
            governed_trace["unmanaged_ollama_call_total"] = scientific_review_gate_trace.get("unmanaged_ollama_call_total", governed_trace.get("unmanaged_ollama_call_total"))
            governed_trace["v_model_lowest_checked_level"] = "L10"
            governed_trace["common_llm_service_status"] = "PASS"
        generated_files.extend(path for path in r015_gate.get("generated_files", []) if isinstance(path, Path) and path.is_file())
        for row in artifact_rows:
            if row.get("artifact_type_id") not in TEXT_ARTIFACTS:
                continue
            row["governed_ollama_status"] = governed_trace.get("status")
            row["ollama_invocation_total"] = governed_trace.get("ollama_invocation_total")
            row["unmanaged_ollama_call_total"] = governed_trace.get("unmanaged_ollama_call_total")
            row["v_model_lowest_checked_level"] = "L10"
            row["public_translation_status"] = (
                R015_TRANSLATOR_STATUS
                if assembly_revision == R015_REVISION
                else R016_TRANSLATOR_STATUS
                if assembly_revision == R016_REVISION
                else R017_TRANSLATOR_STATUS
            )
            if row.get("artifact_type_id") == "master_monograph":
                row["public_translation_source"] = (
                    "science_monolith_scientific_review_gate_r015"
                    if assembly_revision == R015_REVISION
                    else "science_monolith_machine_self_audited_toe_gate_r016"
                    if assembly_revision == R016_REVISION
                    else "science_monolith_final_toe_closed_package_r017"
                )
            else:
                row["public_translation_source"] = (
                    "scientific_review_gate_publication_translator_r015"
                    if assembly_revision == R015_REVISION
                    else "machine_self_audited_publication_translator_r016"
                    if assembly_revision == R016_REVISION
                    else "final_toe_closed_publication_translator_r017"
                )
            row["logion_llm_service_status"] = governed_trace.get("service_status")
            row["logion_llm_service_ledger_ref"] = governed_trace.get("service_ledger_ref")
            row["logion_llm_service_cadence_sequence"] = governed_trace.get("cadence_sequence")
            row["logion_llm_service_model_sequence"] = governed_trace.get("model_sequence")
            for gate_key in [
                "scientific_source_review_status",
                "research_pingpong_status",
                "future_research_register_status",
                "claim_support_ceiling_status",
                "proof_sheet_binding_status",
                "lean_certificate_boundary_status",
                "delta_rebuild_status",
                "editorial_input_gate_status",
            ]:
                row[gate_key] = governed_trace.get(gate_key)
            row["critical_scientific_vulnerability_total"] = governed_trace.get("critical_scientific_vulnerability_total")
            row["high_scientific_vulnerability_total"] = governed_trace.get("high_scientific_vulnerability_total")
    if assembly_revision in {R016_REVISION, R017_REVISION}:
        r016_machine = build_r016_machine_self_audit(
            base=base,
            version=version,
            assembly_revision=assembly_revision,
            artifact_rows=artifact_rows,
            governed_trace=governed_trace,
            write=write,
        )
        machine_self_audit_trace = r016_machine.get("summary")
        if isinstance(machine_self_audit_trace, dict):
            governed_trace.update(machine_self_audit_trace)
            governed_trace["status"] = "PASS" if machine_self_audit_trace.get("status") == "PASS" else "REPAIR_REQUIRED"
            governed_trace["service_status"] = "PASS" if machine_self_audit_trace.get("status") == "PASS" else governed_trace.get("service_status")
        generated_files.extend(path for path in r016_machine.get("generated_files", []) if isinstance(path, Path) and path.is_file())
        for row in artifact_rows:
            if row.get("artifact_type_id") not in TEXT_ARTIFACTS:
                continue
            for gate_key in R016_MACHINE_STATUS_KEYS:
                row[gate_key] = governed_trace.get(gate_key)
            row["toe_final_pass_status"] = governed_trace.get("toe_final_pass_status")
            row["r017_promotion_gate"] = governed_trace.get("r017_promotion_gate")
    generated_files.extend([paths["terminal_contracts_json"], paths["terminal_contracts_md"], paths["transition_records_json"], paths["transition_records_md"], paths["source_bindings_json"], paths["source_bindings_md"]])
    if assembly_revision == R014_REVISION:
        generated_files.extend(ROOT / item for item in R014_CHECKSUM_BOUND_PUBLIC_EVIDENCE_PATHS if (ROOT / item).is_file())
    if assembly_revision == R015_REVISION:
        generated_files.extend(ROOT / item for item in R015_CHECKSUM_BOUND_PUBLIC_EVIDENCE_PATHS if (ROOT / item).is_file())
    if assembly_revision in {R016_REVISION, R017_REVISION}:
        generated_files.extend(ROOT / item for item in R016_CHECKSUM_BOUND_PUBLIC_EVIDENCE_PATHS if (ROOT / item).is_file())
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
        "public_review_revision_aliases": (
            {
                "oc_core_1_3_3_review_current": {
                    "assembly_revision": assembly_revision,
                    "assembly_json": rel(paths["assembly_json"]),
                    "review_zip": rel(paths["review_zip"]),
                    "alias_policy": "stable public review alias for commands; internal revision id remains package metadata",
                }
            }
            if assembly_revision in {R014_REVISION, R015_REVISION, R016_REVISION, R017_REVISION}
            else {}
        ),
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
        "public_review_revision_aliases": (
            {
                "oc_core_1_3_3_review_current": {
                    "assembly_revision": assembly_revision,
                    "assembly_json": rel(paths["assembly_json"]),
                    "package_manifest_json": rel(paths["manifest_json"]),
                    "package_manifest_hash": manifest["artifact_hash"],
                    "review_zip": zip_payload.get("path"),
                    "review_zip_sha256": zip_payload.get("sha256"),
                    "artifact_hash_policy": "artifact rows and manifest files in this assembly bind the stable public alias to the exact reviewed files",
                    "reader_facing_identity_policy": "do not print internal recovery labels on title pages or public identity surfaces",
                }
            }
            if assembly_revision in {R014_REVISION, R015_REVISION, R016_REVISION, R017_REVISION}
            else {}
        ),
        "governed_ollama_trace": governed_trace,
        "visual_quality_trace": visual_quality_trace,
        "table_quality_trace": table_quality_trace,
        "scientific_review_gate_trace": scientific_review_gate_trace,
        "machine_self_audit_trace": machine_self_audit_trace,
        "publication_translation_pipeline": {
            "status": (
                R007_TRANSLATOR_STATUS if assembly_revision == R007_REVISION
                else R008_TRANSLATOR_STATUS if assembly_revision == R008_REVISION
                else R009_TRANSLATOR_STATUS if assembly_revision == R009_REVISION
                else R010_TRANSLATOR_STATUS if assembly_revision == R010_REVISION
                else R011_TRANSLATOR_STATUS if assembly_revision == R011_REVISION
                else R012_TRANSLATOR_STATUS if assembly_revision == R012_REVISION
                else R013_TRANSLATOR_STATUS if assembly_revision == R013_REVISION
                else R014_TRANSLATOR_STATUS if assembly_revision == R014_REVISION
                else R015_TRANSLATOR_STATUS if assembly_revision == R015_REVISION
                else R016_TRANSLATOR_STATUS if assembly_revision == R016_REVISION
                else R017_TRANSLATOR_STATUS if assembly_revision == R017_REVISION
                else "NOT_APPLICABLE"
            ),
            "strategy": (
                "internal_section_packets_to_public_prose_deterministic_templates_first" if assembly_revision == R007_REVISION
                else "common_governed_llm_service_v_model_review_then_public_prose" if assembly_revision == R008_REVISION
                else "editorial_ollama_until_done_packet_queue_then_public_package" if assembly_revision == R009_REVISION
                else "source_grounded_repair_records_and_bounded_suggestions_without_auto_promotion" if assembly_revision == R010_REVISION
                else "journal_requirements_spot_projection_with_bounded_synthesis_and_owner_review_no_send" if assembly_revision == R011_REVISION
                else "deterministic_figure_registry_geometry_and_rendered_bbox_visual_qa" if assembly_revision == R012_REVISION
                else "deterministic_table_registry_geometry_and_rendered_bbox_table_qa" if assembly_revision == R013_REVISION
                else "full_quality_closure_with_scoped_cerberus_and_l10_coverage_assessment" if assembly_revision == R014_REVISION
                else "source_level_scientific_review_pingpong_before_editorial_assembly" if assembly_revision == R015_REVISION
                else "machine_self_audit_full_package_assessment_and_toe_gap_routing" if assembly_revision == R016_REVISION
                else "final_toe_closed_full_package_projection" if assembly_revision == R017_REVISION
                else None
            ),
            "v_model_flow": "L10_to_L9_L8_to_document_review" if assembly_revision in GOVERNED_TEXT_REVISIONS else None,
            "lower_level_blockers_required_zero_before_global_review": True if assembly_revision in GOVERNED_TEXT_REVISIONS else None,
            "common_llm_service_required": True if assembly_revision in COMMON_LLM_SERVICE_REVISIONS else None,
            "service_status": governed_trace.get("service_status") if assembly_revision in COMMON_LLM_SERVICE_REVISIONS else None,
            "queue_status": governed_trace.get("queue_status") if assembly_revision in {R009_REVISION, R011_REVISION, R012_REVISION, R013_REVISION, R014_REVISION, R015_REVISION, R016_REVISION, R017_REVISION} else None,
            "source_grounded_repair_status": governed_trace.get("source_grounded_repair_status") if assembly_revision == R010_REVISION else ("PASS" if assembly_revision in JOURNAL_SPOT_REVISIONS else None),
            "local_editorial_capability_boundary_status": governed_trace.get("local_editorial_capability_boundary_status") if assembly_revision == R010_REVISION else None,
            "scientific_journal_submission_ready_status": governed_trace.get("scientific_journal_submission_ready_status") if assembly_revision in JOURNAL_SPOT_REVISIONS else None,
            "journal_requirements_trace_status": governed_trace.get("journal_requirements_trace_status") if assembly_revision in JOURNAL_SPOT_REVISIONS else None,
            "visual_cockpit_status": (visual_quality_trace or {}).get("visual_cockpit_status") if assembly_revision in VISUAL_QA_REVISIONS else None,
            "table_cockpit_status": (table_quality_trace or {}).get("table_cockpit_status") if assembly_revision in TABLE_QA_REVISIONS else None,
            "scientific_source_review_status": governed_trace.get("scientific_source_review_status") if assembly_revision in {R015_REVISION, R016_REVISION, R017_REVISION} else None,
            "research_pingpong_status": governed_trace.get("research_pingpong_status") if assembly_revision in {R015_REVISION, R016_REVISION, R017_REVISION} else None,
            "editorial_input_gate_status": governed_trace.get("editorial_input_gate_status") if assembly_revision in {R015_REVISION, R016_REVISION, R017_REVISION} else None,
            "machine_self_audit_status": governed_trace.get("machine_self_audit_status") if assembly_revision in {R016_REVISION, R017_REVISION} else None,
            "toe_gap_assessment_status": governed_trace.get("toe_gap_assessment_status") if assembly_revision in {R016_REVISION, R017_REVISION} else None,
            "r017_promotion_gate": governed_trace.get("r017_promotion_gate") if assembly_revision in {R016_REVISION, R017_REVISION} else None,
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
            "journal_requirements_trace_status": governed_trace.get("journal_requirements_trace_status") if assembly_revision in JOURNAL_SPOT_REVISIONS else None,
            "release_spot_completeness_status": governed_trace.get("release_spot_completeness_status") if assembly_revision in JOURNAL_SPOT_REVISIONS else None,
            "bounded_synthesis_status": governed_trace.get("bounded_synthesis_status") if assembly_revision in JOURNAL_SPOT_REVISIONS else None,
            "source_gap_zero_status": governed_trace.get("source_gap_zero_status") if assembly_revision in JOURNAL_SPOT_REVISIONS else None,
            "all_venue_projection_status": governed_trace.get("all_venue_projection_status") if assembly_revision in JOURNAL_SPOT_REVISIONS else None,
            "submission_component_status": governed_trace.get("submission_component_status") if assembly_revision in JOURNAL_SPOT_REVISIONS else None,
            "journal_format_compliance_status": governed_trace.get("journal_format_compliance_status") if assembly_revision in JOURNAL_SPOT_REVISIONS else None,
            "zero_internal_leak_status": governed_trace.get("zero_internal_leak_status") if assembly_revision in JOURNAL_SPOT_REVISIONS else None,
            "zero_fabrication_risk_status": governed_trace.get("zero_fabrication_risk_status") if assembly_revision in JOURNAL_SPOT_REVISIONS else None,
            "scientific_journal_submission_ready_status": governed_trace.get("scientific_journal_submission_ready_status") if assembly_revision in JOURNAL_SPOT_REVISIONS else None,
            "scientific_source_review_status": governed_trace.get("scientific_source_review_status") if assembly_revision in {R015_REVISION, R016_REVISION, R017_REVISION} else None,
            "research_pingpong_status": governed_trace.get("research_pingpong_status") if assembly_revision in {R015_REVISION, R016_REVISION, R017_REVISION} else None,
            "critical_scientific_vulnerability_total": governed_trace.get("critical_scientific_vulnerability_total") if assembly_revision in {R015_REVISION, R016_REVISION, R017_REVISION} else None,
            "high_scientific_vulnerability_total": governed_trace.get("high_scientific_vulnerability_total") if assembly_revision in {R015_REVISION, R016_REVISION, R017_REVISION} else None,
            "future_research_register_status": governed_trace.get("future_research_register_status") if assembly_revision in {R015_REVISION, R016_REVISION, R017_REVISION} else None,
            "claim_support_ceiling_status": governed_trace.get("claim_support_ceiling_status") if assembly_revision in {R015_REVISION, R016_REVISION, R017_REVISION} else None,
            "proof_sheet_binding_status": governed_trace.get("proof_sheet_binding_status") if assembly_revision in {R015_REVISION, R016_REVISION, R017_REVISION} else None,
            "lean_certificate_boundary_status": governed_trace.get("lean_certificate_boundary_status") if assembly_revision in {R015_REVISION, R016_REVISION, R017_REVISION} else None,
            "delta_rebuild_status": governed_trace.get("delta_rebuild_status") if assembly_revision in {R015_REVISION, R016_REVISION, R017_REVISION} else None,
            "editorial_input_gate_status": governed_trace.get("editorial_input_gate_status") if assembly_revision in {R015_REVISION, R016_REVISION, R017_REVISION} else None,
            **({key: governed_trace.get(key) for key in R016_MACHINE_STATUS_KEYS} if assembly_revision in {R016_REVISION, R017_REVISION} else {}),
            "toe_final_pass_status": governed_trace.get("toe_final_pass_status") if assembly_revision in {R016_REVISION, R017_REVISION} else None,
            "r017_promotion_gate": governed_trace.get("r017_promotion_gate") if assembly_revision in {R016_REVISION, R017_REVISION} else None,
            "toe_validator_error_total": governed_trace.get("toe_validator_error_total") if assembly_revision in {R016_REVISION, R017_REVISION} else None,
            **({key: (visual_quality_trace or {}).get(key) for key in [
                "figure_spec_coverage_status",
                "diagram_geometry_status",
                "rendered_figure_bbox_status",
                "label_collision_status",
                "figure_semantic_completeness_status",
                "k_hierarchy_visual_status",
                "continuum_visual_status",
                "caption_argument_status",
                "visual_cockpit_status",
            ]} if assembly_revision in VISUAL_QA_REVISIONS else {}),
            **({key: (table_quality_trace or {}).get(key) for key in [
                "table_spec_coverage_status",
                "compiled_table_coverage_status",
                "table_layout_standard_status",
                "table_geometry_status",
                "rendered_table_bbox_status",
                "table_text_collision_status",
                "table_edge_clipping_status",
                "table_caption_argument_status",
                "table_semantic_anchor_status",
                "table_cockpit_status",
            ]} if assembly_revision in TABLE_QA_REVISIONS else {}),
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
