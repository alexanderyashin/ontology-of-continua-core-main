from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from build_oc_core_release_package_cascade import package_paths
from build_oc_core_text_fill_rules import rules_paths
from oc_core_release_assembly_lib import ASSEMBLY_ROOT, artifact_hash, read_json, stable_json, validation_result


ARTIFACT_GENERATION_DIR = ASSEMBLY_ROOT / "artifact_generation"
CONCEPT_DOI = "10.5281/zenodo.17899134"
RULE_STATUS = "OC_CORE_ARTIFACT_GENERATION_RULES_READY"


def generation_paths() -> dict[str, Path]:
    return {
        "terminal_rules_json": ARTIFACT_GENERATION_DIR / "OC_CORE_TERMINAL_TEXT_GENERATION_RULES.json",
        "terminal_rules_md": ARTIFACT_GENERATION_DIR / "OC_CORE_TERMINAL_TEXT_GENERATION_RULES.md",
        "transition_rules_json": ARTIFACT_GENERATION_DIR / "OC_CORE_TRANSITION_RULES.json",
        "transition_rules_md": ARTIFACT_GENERATION_DIR / "OC_CORE_TRANSITION_RULES.md",
        "profile_json": ARTIFACT_GENERATION_DIR / "OC_CORE_RELEASE_ARTIFACT_GENERATION_PROFILE.json",
        "profile_md": ARTIFACT_GENERATION_DIR / "OC_CORE_RELEASE_ARTIFACT_GENERATION_PROFILE.md",
        "build_graph_json": ARTIFACT_GENERATION_DIR / "OC_CORE_RELEASE_PACKAGE_BUILD_GRAPH.json",
        "build_graph_md": ARTIFACT_GENERATION_DIR / "OC_CORE_RELEASE_PACKAGE_BUILD_GRAPH.md",
        "audit_json": ARTIFACT_GENERATION_DIR / "OC_CORE_ARTIFACT_GENERATION_RULES_AUDIT.json",
        "audit_md": ARTIFACT_GENERATION_DIR / "OC_CORE_ARTIFACT_GENERATION_RULES_AUDIT.md",
    }


def build_terminal_rules_payload() -> dict[str, Any]:
    role_contracts = {
        "definition_model": {
            "paragraph_purpose": "define the local object, vocabulary, or reader task before claims are promoted",
            "required_source_use": "use source bindings as explanatory support, not as a raw inventory",
            "claim_boundary": "may introduce terms and scope; may not promote empirical or universal strength",
        },
        "proof_evidence": {
            "paragraph_purpose": "bind the local claim to proof, evidence, replay, example, or source support",
            "required_source_use": "name the support route in prose and keep exact paths in the source trace",
            "claim_boundary": "may promote only the exact bounded claim supported by the named route",
        },
        "limits_falsifier": {
            "paragraph_purpose": "state limits, falsifiers, negative controls, or reopening conditions",
            "required_source_use": "turn reviewer and failure-mode sources into explicit scientific boundaries",
            "claim_boundary": "must prevent unsupported TOE, all-domain, or superiority inflation",
        },
        "synthesis_transition": {
            "paragraph_purpose": "synthesize the local route and hand the reader to the next obligation",
            "required_source_use": "summarize only established local support and state the next reading move",
            "claim_boundary": "may connect results; may not add new unsupported claims",
        },
    }
    payload: dict[str, Any] = {
        "schema_id": "OC_CORE_TERMINAL_TEXT_GENERATION_RULES_v1",
        "artifact_kind": "OC_CORE_TERMINAL_TEXT_GENERATION_RULES",
        "body_prose_included": False,
        "status": RULE_STATUS,
        "terminal_contract_fields": [
            "aggregator_node_id",
            "target_node_id",
            "reader_task",
            "argument_role",
            "claim_boundary",
            "source_refs",
            "source_hashes",
            "transformation_rule",
            "transition_in",
            "transition_out",
            "quality_scorer_hooks",
        ],
        "role_contracts": role_contracts,
        "fail_closed_rules": [
            "block terminal generation when reader_task is missing",
            "block terminal generation when claim_boundary is missing",
            "block terminal generation when source route is empty",
            "block terminal generation when no transformation rule exists for the argument role",
            "block terminal generation when text would expose raw ledger rows as prose",
        ],
        "style_policy": {
            "voice": "clear scientific prose, continuous and reader-oriented",
            "forbidden_voice": ["machine list voice", "route sheet voice", "control-plane status voice"],
            "source_trace_location": "metadata/source trace fields, not dumped inside reader-facing paragraphs",
        },
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def build_transition_rules_payload() -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_id": "OC_CORE_TRANSITION_RULES_v1",
        "artifact_kind": "OC_CORE_TRANSITION_RULES",
        "body_prose_included": False,
        "status": RULE_STATUS,
        "canonical_argument_sequence": [
            "identity",
            "scope",
            "problem",
            "prior_art",
            "method",
            "model",
            "proof",
            "evidence",
            "limits",
            "novelty",
            "didactics",
            "review",
            "reproducibility",
            "governance",
            "synthesis",
        ],
        "role_sequence": ["definition_model", "proof_evidence", "limits_falsifier", "synthesis_transition"],
        "transition_levels": ["terminal", "paragraph_group", "chapter", "block", "artifact"],
        "templates": {
            "definition_model->proof_evidence": "Having named the object, the manuscript now makes the support route explicit.",
            "proof_evidence->limits_falsifier": "The support route is useful only when its boundary and falsifier are visible.",
            "limits_falsifier->synthesis_transition": "With the boundary stated, the section can synthesize the local consequence without overclaiming.",
            "synthesis_transition->definition_model": "The next obligation starts by naming the next object before asking for proof or evidence.",
        },
        "gate_rules": [
            "every adjacent terminal pair must have a transition record",
            "chapter transitions must not skip from evidence to synthesis without a limits/falsifier route where applicable",
            "artifact transitions must state reading order and reader payoff",
            "transition text must not contain source paths, checksums, approval locks, or publication-control language",
        ],
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def build_profile_payload() -> dict[str, Any]:
    package = read_json(package_paths()["cascade_json"])
    rules = read_json(rules_paths()["rules_json"])
    artifact_profiles: list[dict[str, Any]] = []
    for artifact in package["artifact_types"]:
        artifact_id = artifact["artifact_type_id"]
        output_kind = {
            "public_evidence_bundle": "zip_bundle",
            "integrity_manifest": "manifest_and_checksums",
            "citation_metadata": "metadata",
            "release_notes_changelog": "markdown",
        }.get(artifact_id, "markdown_and_pdf")
        artifact_profiles.append(
            {
                "artifact_type_id": artifact_id,
                "label": artifact["label"],
                "output_kind": output_kind,
                "purpose": artifact["purpose"],
                "requires_frontmatter": output_kind in {"markdown_and_pdf", "markdown", "metadata"},
                "requires_terminal_text": output_kind == "markdown_and_pdf",
                "requires_source_trace": True,
                "requires_quality_rows": True,
                "concept_doi_for_pdf": CONCEPT_DOI if output_kind == "markdown_and_pdf" else None,
                "publication_record_doi_allowed_in_package_build": False,
            }
        )
    payload: dict[str, Any] = {
        "schema_id": "OC_CORE_RELEASE_ARTIFACT_GENERATION_PROFILE_v1",
        "artifact_kind": "OC_CORE_RELEASE_ARTIFACT_GENERATION_PROFILE",
        "body_prose_included": False,
        "status": RULE_STATUS,
        "source_hashes": {
            "package_cascade_hash": package["artifact_hash"],
            "text_fill_rules_hash": rules["artifact_hash"],
        },
        "concept_doi_policy": {
            "pdf_doi": CONCEPT_DOI,
            "release_record_doi_is_publication_layer_only": True,
            "package_build_must_not_invent_release_record_doi": True,
        },
        "artifact_profiles": artifact_profiles,
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def build_graph_payload(profile: dict[str, Any], terminal_rules: dict[str, Any], transition_rules: dict[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_id": "OC_CORE_RELEASE_PACKAGE_BUILD_GRAPH_v1",
        "artifact_kind": "OC_CORE_RELEASE_PACKAGE_BUILD_GRAPH",
        "body_prose_included": False,
        "status": RULE_STATUS,
        "source_hashes": {
            "artifact_generation_profile_hash": profile["artifact_hash"],
            "terminal_text_rules_hash": terminal_rules["artifact_hash"],
            "transition_rules_hash": transition_rules["artifact_hash"],
        },
        "stages": [
            "resolve_versioned_release_instance",
            "load_current_release_aggregator",
            "bind_science_sources_to_terminal_nodes",
            "generate_terminal_contracts",
            "generate_terminal_text_fragments",
            "generate_transition_records",
            "assemble_artifact_sources",
            "build_review_space_pdfs_and_bundles",
            "write_manifest_checksums_and_metadata",
            "run_quality_and_public_surface_audits",
        ],
        "hard_boundaries": {
            "no_publication_actions": True,
            "no_github_release_update": True,
            "no_zenodo_deposit": True,
            "no_tag_movement": True,
            "no_journal_submission": True,
        },
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def validate_payloads(payloads: dict[str, dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    for name, payload in payloads.items():
        if payload.get("status") != RULE_STATUS:
            failures.append(f"{name}_bad_status")
        if payload.get("body_prose_included") is not False:
            failures.append(f"{name}_body_prose_flag_mismatch")
        if payload.get("artifact_hash") != artifact_hash(payload):
            failures.append(f"{name}_hash_mismatch")
    terminal = payloads["terminal_rules"]
    for field in ["reader_task", "claim_boundary", "source_refs", "transition_in", "transition_out"]:
        if field not in terminal.get("terminal_contract_fields", []):
            failures.append(f"terminal_rules_missing_contract_field::{field}")
    profile = payloads["profile"]
    if profile.get("concept_doi_policy", {}).get("pdf_doi") != CONCEPT_DOI:
        failures.append("profile_concept_doi_mismatch")
    for artifact in profile.get("artifact_profiles", []):
        if artifact.get("output_kind") == "markdown_and_pdf" and artifact.get("publication_record_doi_allowed_in_package_build") is not False:
            failures.append(f"artifact_allows_publication_doi::{artifact.get('artifact_type_id')}")
    return sorted(set(failures))


def build_audit_payload(payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    failures = validate_payloads(payloads)
    payload: dict[str, Any] = {
        "schema_id": "OC_CORE_ARTIFACT_GENERATION_RULES_AUDIT_v1",
        "artifact_kind": "OC_CORE_ARTIFACT_GENERATION_RULES_AUDIT",
        "body_prose_included": False,
        "status": "PASS" if not failures else "FAIL",
        "failure_total": len(failures),
        "failures": failures,
        "terminal_text_rules_hash": payloads["terminal_rules"]["artifact_hash"],
        "transition_rules_hash": payloads["transition_rules"]["artifact_hash"],
        "artifact_generation_profile_hash": payloads["profile"]["artifact_hash"],
        "release_package_build_graph_hash": payloads["build_graph"]["artifact_hash"],
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def render_simple_md(title: str, payload: dict[str, Any]) -> str:
    lines = [f"# {title}", "", f"Status: `{payload['status']}`", f"Artifact hash: `{payload['artifact_hash']}`", ""]
    if "concept_doi_policy" in payload:
        lines.extend(["## Concept DOI Policy", ""])
        for key, value in payload["concept_doi_policy"].items():
            lines.append(f"- {key}: `{value}`")
        lines.append("")
    if "terminal_contract_fields" in payload:
        lines.extend(["## Terminal Contract Fields", ""])
        lines.extend(f"- `{field}`" for field in payload["terminal_contract_fields"])
        lines.append("")
    if "role_contracts" in payload:
        lines.extend(["## Role Contracts", ""])
        for role, contract in payload["role_contracts"].items():
            lines.append(f"### `{role}`")
            for key, value in contract.items():
                lines.append(f"- {key}: {value}")
            lines.append("")
    if "templates" in payload:
        lines.extend(["## Transition Templates", ""])
        for key, value in payload["templates"].items():
            lines.append(f"- `{key}`: {value}")
        lines.append("")
    if "artifact_profiles" in payload:
        lines.extend(["## Artifact Profiles", ""])
        for artifact in payload["artifact_profiles"]:
            lines.append(f"- `{artifact['artifact_type_id']}`: {artifact['output_kind']} / concept DOI `{artifact.get('concept_doi_for_pdf')}`")
        lines.append("")
    if "stages" in payload:
        lines.extend(["## Build Stages", ""])
        lines.extend(f"{index}. {stage}" for index, stage in enumerate(payload["stages"], start=1))
    return "\n".join(lines).rstrip() + "\n"


def expected_files() -> dict[Path, str]:
    terminal_rules = build_terminal_rules_payload()
    transition_rules = build_transition_rules_payload()
    profile = build_profile_payload()
    build_graph = build_graph_payload(profile, terminal_rules, transition_rules)
    payloads = {
        "terminal_rules": terminal_rules,
        "transition_rules": transition_rules,
        "profile": profile,
        "build_graph": build_graph,
    }
    audit = build_audit_payload(payloads)
    if audit["status"] != "PASS":
        raise RuntimeError(f"Artifact generation rules audit failed: {audit['failures']}")
    paths = generation_paths()
    return {
        paths["terminal_rules_json"]: stable_json(terminal_rules),
        paths["terminal_rules_md"]: render_simple_md("OC Core Terminal Text Generation Rules", terminal_rules),
        paths["transition_rules_json"]: stable_json(transition_rules),
        paths["transition_rules_md"]: render_simple_md("OC Core Transition Rules", transition_rules),
        paths["profile_json"]: stable_json(profile),
        paths["profile_md"]: render_simple_md("OC Core Release Artifact Generation Profile", profile),
        paths["build_graph_json"]: stable_json(build_graph),
        paths["build_graph_md"]: render_simple_md("OC Core Release Package Build Graph", build_graph),
        paths["audit_json"]: stable_json(audit),
        paths["audit_md"]: render_simple_md("OC Core Artifact Generation Rules Audit", audit),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build generic OC Core artifact generation and transition rules.")
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
