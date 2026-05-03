from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from freeze_oc_core_manuscript_structure_cascade_v1_0 import freeze_paths
from oc133_manuscript_structure_transfer_lib import (
    EDITORIAL,
    MAX_DEPTH,
    artifact_paths,
    sha256_text,
    stable_json,
    write_text_if_changed,
)


ROOT = Path(__file__).resolve().parents[1]
MAPPING_DIR = EDITORIAL / "science_l10_mapping"
ALLOWED_COVERAGE_STATUSES = ["complete", "partial", "planned", "missing", "not_assessed"]

SOURCE_FAMILIES = [
    {
        "id": "formal_model_and_foundation",
        "description": "typed foundation, model definitions, k-level semantics, identity, boundary, and operator material",
        "source_globs": [
            "formal/**",
            "proofs/**",
            "releases/oc_core_1_3_3/**/theorem*",
            "releases/oc_core_1_3_3/**/proof*",
        ],
    },
    {
        "id": "machine_checked_and_finite_semantics",
        "description": "Lean/Lake subset, finite-model semantics, witness cases, and tamper controls",
        "source_globs": [
            "formal/lean/**",
            "proofs/finite_model_checks/**",
            "releases/oc_core_1_3_3/**/finite*",
            "releases/oc_core_1_3_3/**/lean*",
        ],
    },
    {
        "id": "empirical_computational_evidence",
        "description": "validation, target-blind/held-out evidence, simulation, adversarial simulation, and counterexample search material",
        "source_globs": [
            "validation/**",
            "simulations/**",
            "falsification/**",
            "releases/oc_core_1_3_3/**/evidence*",
            "releases/oc_core_1_3_3/**/validation*",
        ],
    },
    {
        "id": "prior_art_novelty_and_comparator",
        "description": "prior art, comparator, novelty, residual-delta, and positioning material",
        "source_globs": [
            "releases/oc_core_1_3_3/**/novelty*",
            "releases/oc_core_1_3_3/**/comparator*",
            "releases/oc_core_1_3_3/**/prior*",
        ],
    },
    {
        "id": "review_attack_response_and_limits",
        "description": "Cerberus, hostile review, claim-boundary, attack matrix, limitation, and failure-mode material",
        "source_globs": [
            "releases/oc_core_1_3_3/**/cerberus*",
            "releases/oc_core_1_3_3/**/attack*",
            "releases/oc_core_1_3_3/**/review*",
            "releases/oc_core_1_3_3/**/limits*",
        ],
    },
    {
        "id": "reproducibility_governance_and_artifacts",
        "description": "artifact inventory, checksums, replay protocol, metadata, release governance, and traceability material",
        "source_globs": [
            "releases/oc_core_1_3_3/**/manifest*",
            "releases/oc_core_1_3_3/**/checksum*",
            "releases/oc_core_1_3_3/**/reproduc*",
            "tools/oc133_*",
            "tools/verify_oc133_*",
            "tools/logion_project_controller.py",
            "tools/logion_delta_queue.py",
            "tools/logion_process_coherence_guard.py",
        ],
    },
    {
        "id": "didactic_synthesis_and_reader_guidance",
        "description": "worked examples, figures/tables, reader tracks, synthesis, and external-use guidance",
        "source_globs": [
            "releases/oc_core_1_3_3/**/didactic*",
            "releases/oc_core_1_3_3/**/figure*",
            "releases/oc_core_1_3_3/**/guide*",
            "releases/oc_core_1_3_3/**/synthesis*",
        ],
    },
]

ROLE_TO_SOURCE_FAMILIES = {
    "definition_model": [
        "formal_model_and_foundation",
        "prior_art_novelty_and_comparator",
        "didactic_synthesis_and_reader_guidance",
    ],
    "proof_evidence": [
        "formal_model_and_foundation",
        "machine_checked_and_finite_semantics",
        "empirical_computational_evidence",
        "reproducibility_governance_and_artifacts",
    ],
    "limits_falsifier": [
        "review_attack_response_and_limits",
        "empirical_computational_evidence",
        "prior_art_novelty_and_comparator",
    ],
    "synthesis_transition": [
        "didactic_synthesis_and_reader_guidance",
        "reproducibility_governance_and_artifacts",
        "review_attack_response_and_limits",
    ],
}


def mapping_paths() -> dict[str, Path]:
    return {
        "inventory_json": MAPPING_DIR / "OC_CORE_1_3_3_SCIENCE_INVENTORY_FOR_L10_MAPPING.json",
        "inventory_md": MAPPING_DIR / "OC_CORE_1_3_3_SCIENCE_INVENTORY_FOR_L10_MAPPING.md",
        "ontology_json": MAPPING_DIR / "OC_CORE_1_3_3_SCIENCE_MAPPING_OBJECT_ONTOLOGY.json",
        "ontology_md": MAPPING_DIR / "OC_CORE_1_3_3_SCIENCE_MAPPING_OBJECT_ONTOLOGY.md",
        "rules_json": MAPPING_DIR / "OC_CORE_1_3_3_SCIENCE_TO_L10_MAPPING_RULES_V1_0.json",
        "rules_md": MAPPING_DIR / "OC_CORE_1_3_3_SCIENCE_TO_L10_MAPPING_RULES_V1_0.md",
        "binding_json": MAPPING_DIR / "OC_CORE_1_3_3_SCIENCE_TO_L10_BINDING_CANDIDATES.json",
        "binding_md": MAPPING_DIR / "OC_CORE_1_3_3_SCIENCE_TO_L10_BINDING_CANDIDATES.md",
        "transform_json": MAPPING_DIR / "OC_CORE_1_3_3_SCIENCE_TO_TEXT_TRANSFORMATION_RULES.json",
        "transform_md": MAPPING_DIR / "OC_CORE_1_3_3_SCIENCE_TO_TEXT_TRANSFORMATION_RULES.md",
        "mapping_json": MAPPING_DIR / "OC_CORE_1_3_3_SCIENCE_TO_L10_MAPPING.json",
        "mapping_md": MAPPING_DIR / "OC_CORE_1_3_3_SCIENCE_TO_L10_MAPPING.md",
        "audit_json": MAPPING_DIR / "OC_CORE_1_3_3_SCIENCE_TO_L10_MAPPING_AUDIT.json",
        "audit_md": MAPPING_DIR / "OC_CORE_1_3_3_SCIENCE_TO_L10_MAPPING_AUDIT.md",
    }


def relative(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def payload_without_hash(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if key != "artifact_hash"}


def expand_glob(pattern: str) -> list[str]:
    excluded_name_fragments = (
        "place" + "holder",
        "sandbox",
        "tmp",
    )
    paths = [
        relative(path)
        for path in ROOT.glob(pattern)
        if path.is_file()
        and ".git" not in path.parts
        and "__pycache__" not in path.parts
        and not any(fragment in path.name.lower() for fragment in excluded_name_fragments)
    ]
    return sorted(paths)[:50]


def build_inventory_payload() -> dict[str, Any]:
    families = []
    for family in SOURCE_FAMILIES:
        matched_paths = []
        for pattern in family["source_globs"]:
            matched_paths.extend(expand_glob(pattern))
        matched_paths = sorted(set(matched_paths))
        families.append(
            {
                **family,
                "matched_path_total": len(matched_paths),
                "matched_paths_sample": matched_paths[:50],
                "inventory_status": "HAS_CANDIDATES" if matched_paths else "NO_CANDIDATES_YET",
            }
        )
    payload: dict[str, Any] = {
        "artifact_kind": "OC_CORE_1_3_3_SCIENCE_INVENTORY_FOR_L10_MAPPING",
        "body_prose_included": False,
        "status": "DRAFT_INVENTORY_NOT_COVERAGE_ASSESSED",
        "inventory_policy": {
            "records_candidate_science_sources_only": True,
            "does_not_claim_complete_fill": True,
            "used_by_mapping_rules": True,
        },
        "source_families": families,
    }
    payload["artifact_hash"] = sha256_text(stable_json(payload_without_hash(payload)))
    return payload


def build_object_ontology_payload() -> dict[str, Any]:
    object_classes = [
        {
            "class_id": "science_source_family",
            "meaning": "A curated class of existing OC science artifacts that can support L10 slots.",
            "external_surface": "Not directly exposed; only sanitized source bindings may enter manuscripts.",
        },
        {
            "class_id": "l10_terminal_slot",
            "meaning": "A frozen paragraph-slot obligation in the manuscript structure.",
            "external_surface": "Not exposed as prose; used to guide later drafting.",
        },
        {
            "class_id": "binding_candidate",
            "meaning": "A possible source-family-to-L10 connection pending exact path binding in fill-control.",
            "external_surface": "Internal planning only.",
        },
        {
            "class_id": "transformation_rule",
            "meaning": "A rule for turning science material into future prose without performing the transformation now.",
            "external_surface": "Internal editorial method unless later summarized.",
        },
        {
            "class_id": "coverage_status",
            "meaning": "A reserved maturity value for future fill assessment.",
            "external_surface": "May be summarized only after fill assessment audit.",
        },
    ]
    relations = [
        {
            "relation_id": "source_family_supports_l10_role",
            "from": "science_source_family",
            "to": "l10_terminal_slot",
            "rule": "Support is mediated by argument_role, not by accidental file proximity.",
        },
        {
            "relation_id": "binding_candidate_precedes_transformation",
            "from": "binding_candidate",
            "to": "transformation_rule",
            "rule": "Exact source binding must exist before any science-to-text transformation is executed.",
        },
        {
            "relation_id": "coverage_status_is_not_claim",
            "from": "coverage_status",
            "to": "l10_terminal_slot",
            "rule": "Coverage statuses guide work; they are not scientific claims.",
        },
    ]
    payload: dict[str, Any] = {
        "artifact_kind": "OC_CORE_1_3_3_SCIENCE_MAPPING_OBJECT_ONTOLOGY",
        "body_prose_included": False,
        "status": "ACTIVE_MAPPING_ONTOLOGY_V1_0",
        "object_classes": object_classes,
        "relations": relations,
    }
    payload["artifact_hash"] = sha256_text(stable_json(payload_without_hash(payload)))
    return payload


def build_transformation_rules_payload() -> dict[str, Any]:
    rules = [
        {
            "rule_id": "TRANSFORM_DEFINITION_MODEL",
            "argument_role": "definition_model",
            "general_rule": "Turn definitions, model objects, assumptions, and notation anchors into reader-facing explanatory prose with explicit scope boundaries.",
            "must_include": ["term being defined", "why it is needed", "formal or conceptual source", "boundary of use"],
            "must_not_include": ["new empirical claims", "unsupported universality", "unbound jargon"],
        },
        {
            "rule_id": "TRANSFORM_PROOF_EVIDENCE",
            "argument_role": "proof_evidence",
            "general_rule": "Turn proof/data/simulation evidence into claim-support prose that identifies source, method, result type, and limitation.",
            "must_include": ["claim being supported", "source artifact class", "verification route", "uncertainty or proof boundary"],
            "must_not_include": ["proof theater", "evidence-free promotion", "hidden source dependency"],
        },
        {
            "rule_id": "TRANSFORM_LIMITS_FALSIFIER",
            "argument_role": "limits_falsifier",
            "general_rule": "Turn failures, caveats, negative controls, and demotion rules into explicit limits and falsification prose.",
            "must_include": ["attack surface", "what would falsify or demote", "current status", "research-only boundary where relevant"],
            "must_not_include": ["cosmetic caveats", "buried blockers", "stronger claims than evidence supports"],
        },
        {
            "rule_id": "TRANSFORM_SYNTHESIS_TRANSITION",
            "argument_role": "synthesis_transition",
            "general_rule": "Turn local results into synthesis and next-step prose that closes the chapter obligation and hands off to the next node.",
            "must_include": ["what was established", "what remains open", "next dependency", "reader orientation"],
            "must_not_include": ["new unbacked results", "duplicate summary walls", "broken narrative jumps"],
        },
    ]
    payload: dict[str, Any] = {
        "artifact_kind": "OC_CORE_1_3_3_SCIENCE_TO_TEXT_TRANSFORMATION_RULES",
        "body_prose_included": False,
        "status": "ACTIVE_TRANSFORMATION_RULES_NO_TRANSFORMATION_EXECUTED",
        "rules": rules,
    }
    payload["artifact_hash"] = sha256_text(stable_json(payload_without_hash(payload)))
    return payload


def build_rules_payload() -> dict[str, Any]:
    freeze_json, _ = freeze_paths()
    freeze = read_json(freeze_json)
    inventory = build_inventory_payload()
    ontology = build_object_ontology_payload()
    transform = build_transformation_rules_payload()
    payload: dict[str, Any] = {
        "artifact_kind": "OC_CORE_1_3_3_SCIENCE_TO_L10_MAPPING_RULES",
        "body_prose_included": False,
        "status": "ACTIVE_MAPPING_RULES_V1_0",
        "source_inventory_hash": inventory["artifact_hash"],
        "mapping_object_ontology_hash": ontology["artifact_hash"],
        "transformation_rules_hash": transform["artifact_hash"],
        "source_cascade_freeze": {
            "json": relative(freeze_json),
            "artifact_hash": freeze["artifact_hash"],
            "frozen_node_manifest_hash": freeze["frozen_node_manifest_hash"],
        },
        "allowed_coverage_statuses": ALLOWED_COVERAGE_STATUSES,
        "source_families": SOURCE_FAMILIES,
        "role_to_source_families": ROLE_TO_SOURCE_FAMILIES,
        "mapping_policy": {
            "mapping_is_separate_from_l10_template": True,
            "mapping_does_not_assess_fill_yet": True,
            "current_release_aggregator_must_consume_mapping_not_raw_l10": True,
            "concrete_release_toc_is_downstream_of_aggregator_and_version_resolver": True,
            "manuscript_prose_generation_not_authorized": True,
        },
    }
    payload["artifact_hash"] = sha256_text(stable_json(payload_without_hash(payload)))
    return payload


def family_rows_for_role(role: str, inventory_by_id: dict[str, dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    by_id = {family["id"]: family for family in SOURCE_FAMILIES}
    rows = []
    for family_id in ROLE_TO_SOURCE_FAMILIES.get(role, []):
        row = dict(by_id[family_id])
        inventory_row = (inventory_by_id or {}).get(family_id)
        if inventory_row:
            row["matched_path_total"] = inventory_row["matched_path_total"]
            row["matched_paths_sample"] = inventory_row["matched_paths_sample"]
            row["inventory_status"] = inventory_row["inventory_status"]
        else:
            row["matched_path_total"] = 0
            row["matched_paths_sample"] = []
            row["inventory_status"] = "NOT_INVENTORIED"
        rows.append(row)
    return rows


def build_mapping_payload() -> dict[str, Any]:
    rules = build_rules_payload()
    inventory = build_inventory_payload()
    inventory_by_id = {family["id"]: family for family in inventory["source_families"]}
    transform = build_transformation_rules_payload()
    transform_by_role = {rule["argument_role"]: rule for rule in transform["rules"]}
    l10_payload = read_json(artifact_paths(MAX_DEPTH)[0])
    terminal_nodes = [
        node
        for node in l10_payload["own_expansion_nodes"]
        if int(node["level"]) == MAX_DEPTH
    ]
    mapping_rows = []
    for node in terminal_nodes:
        metadata = node.get("metadata") or {}
        role = metadata.get("argument_role", "unknown")
        source_families = family_rows_for_role(role, inventory_by_id)
        mapping_rows.append(
            {
                "mapping_id": "MAP-" + node["node_id"],
                "l10_node_id": node["node_id"],
                "outline_number": node["outline_number"],
                "l10_title": node["title"],
                "chapter_title": metadata.get("chapter_title"),
                "argument_role": role,
                "reader_task": metadata.get("reader_task"),
                "claim_boundary": metadata.get("claim_boundary"),
                "coverage_status": "not_assessed",
                "source_families": source_families,
                "source_candidates_from_recovered_corpus": metadata.get("source_candidates", []),
                "binding_candidate_rule": "Bind exact file paths and source fragments only during fill-control; this row records eligible source families and recovered candidates.",
                "transformation_rule": transform_by_role.get(role),
                "extraction_rule": "Collect candidate source fragments from listed source families, then bind exact artifact paths during fill-control.",
                "integration_rule": "Integrate only material that supports this L10 role; demote unsupported material to planned or missing coverage.",
                "verification_rule": "Before prose generation, require at least one exact source binding or an explicit planned/missing status with reason.",
            }
        )

    payload: dict[str, Any] = {
        "artifact_kind": "OC_CORE_1_3_3_SCIENCE_TO_L10_MAPPING",
        "body_prose_included": False,
        "status": "DRAFT_MAPPING_NOT_FILL_ASSESSED",
        "rules_hash": rules["artifact_hash"],
        "source_l10_artifact_hash": l10_payload["artifact_hash"],
        "source_l10_combined_hash": l10_payload["combined_hash"],
        "source_inventory_hash": inventory["artifact_hash"],
        "mapping_object_ontology_hash": build_object_ontology_payload()["artifact_hash"],
        "transformation_rules_hash": transform["artifact_hash"],
        "mapping_row_total": len(mapping_rows),
        "mapping_rows": mapping_rows,
    }
    payload["artifact_hash"] = sha256_text(stable_json(payload_without_hash(payload)))
    return payload


def validate_rules_payload(payload: dict[str, Any]) -> list[str]:
    failures = []
    if payload.get("source_inventory_hash") != build_inventory_payload()["artifact_hash"]:
        failures.append("source_inventory_hash_mismatch")
    if payload.get("mapping_object_ontology_hash") != build_object_ontology_payload()["artifact_hash"]:
        failures.append("mapping_object_ontology_hash_mismatch")
    if payload.get("transformation_rules_hash") != build_transformation_rules_payload()["artifact_hash"]:
        failures.append("transformation_rules_hash_mismatch")
    family_ids = {family["id"] for family in payload.get("source_families", [])}
    for role, families in payload.get("role_to_source_families", {}).items():
        if not families:
            failures.append(f"role_without_source_families::{role}")
        for family in families:
            if family not in family_ids:
                failures.append(f"role_unknown_source_family::{role}::{family}")
    if payload.get("mapping_policy", {}).get("mapping_is_separate_from_l10_template") is not True:
        failures.append("mapping_separation_policy_missing")
    if payload.get("artifact_hash") != sha256_text(stable_json(payload_without_hash(payload))):
        failures.append("rules_hash_mismatch")
    return failures


def validate_mapping_payload(payload: dict[str, Any], rules: dict[str, Any]) -> list[str]:
    failures = []
    l10_payload = read_json(artifact_paths(MAX_DEPTH)[0])
    l10_terminal_ids = {
        node["node_id"]
        for node in l10_payload["own_expansion_nodes"]
        if int(node["level"]) == MAX_DEPTH
    }
    row_ids = {row.get("l10_node_id") for row in payload.get("mapping_rows", [])}
    if row_ids != l10_terminal_ids:
        failures.append("mapping_l10_terminal_set_mismatch")
    if payload.get("rules_hash") != rules.get("artifact_hash"):
        failures.append("mapping_rules_hash_mismatch")
    if payload.get("source_inventory_hash") != build_inventory_payload()["artifact_hash"]:
        failures.append("mapping_inventory_hash_mismatch")
    if payload.get("mapping_object_ontology_hash") != build_object_ontology_payload()["artifact_hash"]:
        failures.append("mapping_ontology_hash_mismatch")
    if payload.get("transformation_rules_hash") != build_transformation_rules_payload()["artifact_hash"]:
        failures.append("mapping_transform_hash_mismatch")
    if payload.get("source_l10_artifact_hash") != l10_payload.get("artifact_hash"):
        failures.append("mapping_l10_artifact_hash_mismatch")
    for row in payload.get("mapping_rows", []):
        if row.get("coverage_status") not in ALLOWED_COVERAGE_STATUSES:
            failures.append(f"bad_coverage_status::{row.get('mapping_id')}")
        for key in ["source_families", "extraction_rule", "integration_rule", "verification_rule", "claim_boundary", "reader_task"]:
            if not row.get(key):
                failures.append(f"mapping_row_missing_{key}::{row.get('mapping_id')}")
        if not row.get("transformation_rule"):
            failures.append(f"mapping_row_missing_transformation_rule::{row.get('mapping_id')}")
        if not row.get("binding_candidate_rule"):
            failures.append(f"mapping_row_missing_binding_candidate_rule::{row.get('mapping_id')}")
    if payload.get("artifact_hash") != sha256_text(stable_json(payload_without_hash(payload))):
        failures.append("mapping_hash_mismatch")
    return failures


def build_audit_payload(rules: dict[str, Any], mapping: dict[str, Any]) -> dict[str, Any]:
    failures = []
    inventory = build_inventory_payload()
    ontology = build_object_ontology_payload()
    transform = build_transformation_rules_payload()
    failures.extend(f"rules::{item}" for item in validate_rules_payload(rules))
    failures.extend(f"mapping::{item}" for item in validate_mapping_payload(mapping, rules))
    status_counts = {}
    for row in mapping["mapping_rows"]:
        status_counts[row["coverage_status"]] = status_counts.get(row["coverage_status"], 0) + 1
    role_counts = {}
    for row in mapping["mapping_rows"]:
        role_counts[row["argument_role"]] = role_counts.get(row["argument_role"], 0) + 1
    payload: dict[str, Any] = {
        "artifact_kind": "OC_CORE_1_3_3_SCIENCE_TO_L10_MAPPING_AUDIT",
        "body_prose_included": False,
        "status": "PASS" if not failures else "FAIL",
        "failure_total": len(failures),
        "failures": failures,
        "inventory_hash": inventory["artifact_hash"],
        "ontology_hash": ontology["artifact_hash"],
        "transformation_rules_hash": transform["artifact_hash"],
        "rules_hash": rules["artifact_hash"],
        "mapping_hash": mapping["artifact_hash"],
        "mapping_row_total": mapping["mapping_row_total"],
        "source_family_inventory": {
            family["id"]: {
                "matched_path_total": family["matched_path_total"],
                "inventory_status": family["inventory_status"],
            }
            for family in inventory["source_families"]
        },
        "coverage_status_counts": status_counts,
        "argument_role_counts": role_counts,
    }
    payload["artifact_hash"] = sha256_text(stable_json(payload_without_hash(payload)))
    return payload


def render_rules_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# OC Core 1.3.3 Science to L10 Mapping Rules v1.0",
        "",
        f"Status: {payload['status']}",
        f"Artifact hash: `{payload['artifact_hash']}`",
        "",
        "This is a mapping-rule artifact. It is separate from the L10 template and does not assess fill.",
        "",
        "## Source Families",
        "",
    ]
    for family in payload["source_families"]:
        lines.append(f"- {family['id']}: {family['description']} ({'; '.join(family['source_globs'])})")
    lines.extend(["", "## Role To Source Families", ""])
    for role, families in payload["role_to_source_families"].items():
        lines.append(f"- {role}: {', '.join(families)}")
    return "\n".join(lines) + "\n"


def render_inventory_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# OC Core 1.3.3 Science Inventory For L10 Mapping",
        "",
        f"Status: {payload['status']}",
        f"Artifact hash: `{payload['artifact_hash']}`",
        "",
        "This inventory records candidate science-source families for later fill-control. It does not assess coverage.",
        "",
        "## Source Families",
        "",
    ]
    for family in payload["source_families"]:
        lines.append(
            f"- {family['id']}: {family['inventory_status']} "
            f"paths={family['matched_path_total']} - {family['description']}"
        )
    return "\n".join(lines) + "\n"


def render_ontology_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# OC Core 1.3.3 Science Mapping Object Ontology",
        "",
        f"Status: {payload['status']}",
        f"Artifact hash: `{payload['artifact_hash']}`",
        "",
        "## Object Classes",
        "",
    ]
    for item in payload["object_classes"]:
        lines.append(f"- {item['class_id']}: {item['meaning']} External surface: {item['external_surface']}")
    lines.extend(["", "## Relations", ""])
    for relation in payload["relations"]:
        lines.append(f"- {relation['relation_id']}: {relation['from']} -> {relation['to']}. {relation['rule']}")
    return "\n".join(lines) + "\n"


def render_transformation_rules_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# OC Core 1.3.3 Science To Text Transformation Rules",
        "",
        f"Status: {payload['status']}",
        f"Artifact hash: `{payload['artifact_hash']}`",
        "",
        "These are rules for later transformation. They do not execute transformation and contain no manuscript prose.",
        "",
        "## Rules",
        "",
    ]
    for rule in payload["rules"]:
        lines.append(f"- {rule['rule_id']} [{rule['argument_role']}]: {rule['general_rule']}")
    return "\n".join(lines) + "\n"


def render_mapping_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# OC Core 1.3.3 Science to L10 Mapping",
        "",
        f"Status: {payload['status']}",
        f"Artifact hash: `{payload['artifact_hash']}`",
        f"Rows: {payload['mapping_row_total']}",
        "",
        "Every L10 terminal slot is mapped to science source families and fill-control rules. No fill status is assessed here.",
        "",
        "## Mapping Rows",
        "",
    ]
    for row in payload["mapping_rows"]:
        families = ", ".join(family["id"] for family in row["source_families"])
        lines.append(
            f"- {row['outline_number']} {row['l10_title']} [{row['argument_role']}]: "
            f"coverage={row['coverage_status']}; sources={families}; transform={row['transformation_rule']['rule_id'] if row['transformation_rule'] else 'NONE'}"
        )
    return "\n".join(lines) + "\n"


def render_binding_candidates_markdown(mapping: dict[str, Any]) -> str:
    lines = [
        "# OC Core 1.3.3 Science to L10 Binding Candidates",
        "",
        f"Mapping hash: `{mapping['artifact_hash']}`",
        "",
        "Binding candidates state where exact source binding should be looked for later. They do not bind final prose sources yet.",
        "",
        "## Binding Candidate Rows",
        "",
    ]
    for row in mapping["mapping_rows"]:
        families = ", ".join(family["id"] for family in row["source_families"])
        recovered = len(row["source_candidates_from_recovered_corpus"])
        lines.append(
            f"- {row['mapping_id']}: {row['l10_title']} sources={families}; recovered_candidates={recovered}"
        )
    return "\n".join(lines) + "\n"


def render_audit_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# OC Core 1.3.3 Science to L10 Mapping Audit",
        "",
        f"Status: {payload['status']}",
        f"Artifact hash: `{payload['artifact_hash']}`",
        f"Rows: {payload['mapping_row_total']}",
        f"Failures: {payload['failure_total']}",
        "",
        "## Coverage Status Counts",
        "",
    ]
    for status, total in sorted(payload["coverage_status_counts"].items()):
        lines.append(f"- {status}: {total}")
    lines.extend(["", "## Argument Role Counts", ""])
    for role, total in sorted(payload["argument_role_counts"].items()):
        lines.append(f"- {role}: {total}")
    lines.extend(["", "## Source Family Inventory", ""])
    for family_id, item in sorted(payload["source_family_inventory"].items()):
        lines.append(f"- {family_id}: {item['inventory_status']} paths={item['matched_path_total']}")
    if payload["failures"]:
        lines.extend(["", "## Failures", ""])
        for failure in payload["failures"]:
            lines.append(f"- {failure}")
    return "\n".join(lines) + "\n"


def expected_files() -> dict[Path, str]:
    inventory = build_inventory_payload()
    ontology = build_object_ontology_payload()
    transform = build_transformation_rules_payload()
    rules = build_rules_payload()
    rule_failures = validate_rules_payload(rules)
    if rule_failures:
        raise RuntimeError(f"Mapping rules validation failed: {rule_failures}")
    mapping = build_mapping_payload()
    mapping_failures = validate_mapping_payload(mapping, rules)
    if mapping_failures:
        raise RuntimeError(f"Science-to-L10 mapping validation failed: {mapping_failures}")
    audit = build_audit_payload(rules, mapping)
    if audit["status"] != "PASS":
        raise RuntimeError(f"Science-to-L10 mapping audit failed: {audit['failures']}")
    paths = mapping_paths()
    return {
        paths["inventory_json"]: stable_json(inventory),
        paths["inventory_md"]: render_inventory_markdown(inventory),
        paths["ontology_json"]: stable_json(ontology),
        paths["ontology_md"]: render_ontology_markdown(ontology),
        paths["rules_json"]: stable_json(rules),
        paths["rules_md"]: render_rules_markdown(rules),
        paths["binding_json"]: stable_json(
            {
                "artifact_kind": "OC_CORE_1_3_3_SCIENCE_TO_L10_BINDING_CANDIDATES",
                "body_prose_included": False,
                "status": "DRAFT_BINDING_CANDIDATES_FROM_MAPPING",
                "mapping_hash": mapping["artifact_hash"],
                "binding_candidate_rows": [
                    {
                        "mapping_id": row["mapping_id"],
                        "l10_node_id": row["l10_node_id"],
                        "source_family_ids": [family["id"] for family in row["source_families"]],
                        "source_candidates_from_recovered_corpus": row["source_candidates_from_recovered_corpus"],
                        "binding_candidate_rule": row["binding_candidate_rule"],
                    }
                    for row in mapping["mapping_rows"]
                ],
            }
        ),
        paths["binding_md"]: render_binding_candidates_markdown(mapping),
        paths["transform_json"]: stable_json(transform),
        paths["transform_md"]: render_transformation_rules_markdown(transform),
        paths["mapping_json"]: stable_json(mapping),
        paths["mapping_md"]: render_mapping_markdown(mapping),
        paths["audit_json"]: stable_json(audit),
        paths["audit_md"]: render_audit_markdown(audit),
    }


def check_files(files: dict[Path, str]) -> dict[str, Any]:
    missing = []
    changed = []
    for path, text in files.items():
        if not path.exists():
            missing.append(relative(path))
        elif path.read_text(encoding="utf-8", errors="replace") != text:
            changed.append(relative(path))
    return {"state": "PASS" if not missing and not changed else "FAIL", "missing": missing, "changed": changed}


def write_files(files: dict[Path, str]) -> list[str]:
    changed = []
    for path, text in files.items():
        if write_text_if_changed(path, text):
            changed.append(relative(path))
    return changed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build OC133 science-to-L10 mapping complex.")
    parser.add_argument("--write", action="store_true", help="Write mapping artifacts if changed.")
    parser.add_argument("--check", action="store_true", help="Check mapping artifacts without writing.")
    args = parser.parse_args(argv)
    if not args.write and not args.check:
        args.check = True
    files = expected_files()
    result = {"changed": write_files(files), "missing": [], "state": "PASS"} if args.write else check_files(files)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["state"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
