from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from build_oc_core_current_release_aggregator import aggregator_paths
from build_oc_core_l10_quality_projection_matrix import projection_paths
from build_oc_core_quality_metric_catalog import metric_catalog_paths
from build_oc_core_release_instance import instance_paths
from build_oc_core_release_package_cascade import package_paths
from build_oc_core_text_fill_rules import rules_paths
from assemble_oc_core_release_package import OLD_MASTER_BASELINE_PAGES, assembly_paths
from audit_oc_core_release_assembly_machine import FORM_FINDING_KINDS, machine_audit_paths
from oc_core_release_assembly_lib import ROOT, artifact_hash, read_json, stable_json, validation_result

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from release_machine.versioning import version_from_release_id

FORM_STATUS_KEYS = [
    "title_page_status",
    "toc_semantic_status",
    "heading_hygiene_status",
    "title_page_publication_status",
    "acknowledgements_status",
    "abstract_depth_status",
    "release_delta_status",
    "reader_contract_status",
    "frontmatter_identity_status",
    "reader_routes_status",
    "toc_visual_hierarchy_status",
    "uniform_document_hierarchy_status",
    "appendix_naming_status",
    "layout_quality_status",
    "table_readability_status",
    "inline_figure_distribution_status",
    "caption_quality_status",
    "bibliography_depth_status",
    "prediction_falsifiability_status",
    "reader_facing_reference_status",
    "toc_hierarchy_status",
    "content_richness_status",
    "technical_prose_leak_status",
    "didactic_density_status",
    "title_identity_public_status",
    "frontmatter_depth_status",
    "release_policy_status",
    "reader_routes_tone_status",
    "single_reader_orientation_status",
    "no_internal_block_metadata_status",
    "no_fig_table_lists_status",
    "didactic_spine_order_status",
    "motivation_depth_status",
    "k_primer_status",
    "duplicate_structure_status",
    "publication_translation_status",
    "instruction_prose_leak_status",
    "page17_internal_leak_status",
    "figure_pedagogy_status",
    "k_hierarchy_figure_status",
    "all_reader_pdf_translation_status",
    "governed_ollama_status",
    "v_model_audit_status",
    "common_llm_service_status",
    "llm_service_governance_status",
    "llm_service_cadence_status",
    "llm_service_thermal_monitor_status",
    "llm_service_no_bypass_status",
    "llm_service_vmodel_status",
    "local_ollama_capability_status",
    "editorial_llm_queue_status",
    "editorial_packet_coverage_status",
    "actual_ollama_invocation_status",
    "until_done_status",
    "cooldown_resume_status",
    "v_model_completion_status",
    "local_capability_exhaustion_status",
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
    "figure_spec_coverage_status",
    "diagram_geometry_status",
    "rendered_figure_bbox_status",
    "label_collision_status",
    "figure_semantic_completeness_status",
    "k_hierarchy_visual_status",
    "continuum_visual_status",
    "caption_argument_status",
    "visual_cockpit_status",
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
    "cerberus_static_leak_status",
    "methods_path_integrity_status",
    "reviewer_map_argument_status",
    "r014_quality_closure_status",
    "form_quality_status",
]


QUALITY_VALIDATION_STATUS_FAIL = "QUALITY_REPAIR_REQUIRED"
QUALITY_VALIDATION_STATUS_PASS = "QUALITY_VALIDATION_PASS"
DELTA_REVISION = "r001"


def quality_dir(release_id: str, assembly_revision: str | None = None) -> Path:
    base = ROOT / "releases" / release_id / "editorial" / "quality_validation"
    return base / assembly_revision if assembly_revision else base


def quality_paths(release_id: str, version: str, assembly_revision: str | None = None) -> dict[str, Path]:
    directory = quality_dir(release_id, assembly_revision)
    return {
        "audit_json": directory / f"OC_CORE_RELEASE_QUALITY_AUDIT_{version}.json",
        "audit_md": directory / f"OC_CORE_RELEASE_QUALITY_AUDIT_{version}.md",
        "protocol_json": directory / f"OC_CORE_RELEASE_VULNERABILITY_PROTOCOL_{version}.json",
        "protocol_md": directory / f"OC_CORE_RELEASE_VULNERABILITY_PROTOCOL_{version}.md",
        "delta_json": directory / f"OC_CORE_RELEASE_REMEDIATION_DELTA_{version}.{DELTA_REVISION}.json",
        "delta_md": directory / f"OC_CORE_RELEASE_REMEDIATION_DELTA_{version}.{DELTA_REVISION}.md",
    }


def editorial_cerberus_path(release_id: str = "oc_core_1_3_3", assembly_revision: str | None = None) -> Path:
    if assembly_revision:
        return quality_dir(release_id, assembly_revision) / "cerberus" / "OC133_EDITORIAL_CERBERUS_SUMMARY.json"
    return ROOT / "reviews" / "oc133_llm_cerberus" / "editorial_release_review" / "OC133_EDITORIAL_CERBERUS_SUMMARY.json"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def expected_cerberus_pdf_hashes(package_assembly: dict[str, Any] | None) -> dict[str, str]:
    if not package_assembly:
        return {}
    artifact_to_key = {
        "release_guide": "guide",
        "master_monograph": "master",
        "journal_core_article": "journal",
        "methods_repro_companion": "methods",
        "reviewer_attack_response_map": "reviewer",
    }
    hashes: dict[str, str] = {}
    for row in package_assembly.get("artifact_rows", []):
        key = artifact_to_key.get(str(row.get("artifact_type_id")))
        if not key:
            continue
        pdf_path = ROOT / str(row.get("pdf_path") or "")
        if pdf_path.is_file():
            hashes[key] = sha256_file(pdf_path)
    return hashes


def _projection_by_node(matrix: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in matrix.get("projection_rows", []):
        grouped[row["aggregator_node_id"]].append(row)
    return grouped


def _release_package_assembly(release_id: str, assembly_revision: str | None = None) -> dict[str, Any] | None:
    version = version_from_release_id(release_id)
    path = assembly_paths(release_id, version, assembly_revision)["assembly_json"]
    return read_json(path) if path.exists() else None


def _release_machine_audit(release_id: str, assembly_revision: str | None = None) -> dict[str, Any] | None:
    version = version_from_release_id(release_id)
    path = machine_audit_paths(release_id, version, assembly_revision)["audit_json"]
    return read_json(path) if path.exists() else None


def _machine_form_findings(machine_audit: dict[str, Any] | None, artifact_type_id: str | None = None) -> list[dict[str, Any]]:
    if not machine_audit:
        return []
    findings = [finding for finding in machine_audit.get("findings", []) if finding.get("kind") in FORM_FINDING_KINDS]
    if artifact_type_id is None:
        return findings
    return [finding for finding in findings if finding.get("artifact_type_id") == artifact_type_id]


def _machine_form_summary(machine_audit: dict[str, Any] | None) -> dict[str, Any]:
    if not machine_audit:
        missing = {
            "machine_audit_status": "MISSING",
            "machine_form_gate_finding_total": 0,
        }
        missing.update({key: "FAIL" for key in FORM_STATUS_KEYS})
        return missing
    summary = machine_audit.get("summary", {})
    payload = {
        "machine_audit_status": machine_audit.get("status"),
        "machine_form_gate_finding_total": len(_machine_form_findings(machine_audit)),
        "source_grounded_repair_status": summary.get("source_grounded_repair_status"),
        "local_editorial_capability_boundary_status": summary.get("local_editorial_capability_boundary_status"),
        "unresolved_repair_record_total": summary.get("unresolved_repair_record_total"),
        "accepted_candidate_promoted_total": summary.get("accepted_candidate_promoted_total"),
        "venue_total": summary.get("venue_total"),
        "requirements_source_total": summary.get("requirements_source_total"),
        "requirements_matrix_total": summary.get("requirements_matrix_total"),
        "journal_package_total": summary.get("journal_package_total"),
    }
    payload.update({key: summary.get(key) for key in FORM_STATUS_KEYS})
    return payload


def _artifact_scores(
    review_package: dict[str, Any],
    assembly: dict[str, Any] | None = None,
    machine_audit: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    if assembly:
        rows: list[dict[str, Any]] = []
        for artifact in assembly.get("artifact_rows", []):
            output_paths = artifact.get("output_paths", [])
            missing = [path for path in output_paths if not (ROOT / path).is_file()]
            pdf_build = artifact.get("pdf_build")
            pdf_ok = True if pdf_build is None else bool(pdf_build.get("ok"))
            recovery_baseline = None
            baseline_ok = True
            if assembly.get("structure_source") == "recovered_l10c" and artifact.get("artifact_type_id") == "master_monograph":
                pages = int((pdf_build or {}).get("pages") or 0)
                baseline_ok = pages >= OLD_MASTER_BASELINE_PAGES
                recovery_baseline = {
                    "old_public_master_baseline_pages": OLD_MASTER_BASELINE_PAGES,
                    "recovered_master_pages": pages,
                    "pass": baseline_ok,
                }
            artifact_form_findings = _machine_form_findings(machine_audit, artifact.get("artifact_type_id"))
            machine_required = artifact.get("output_kind") == "markdown_and_pdf"
            form_ok = (not machine_required) or (machine_audit is not None and machine_audit.get("status") == "PASS" and not artifact_form_findings)
            state = "PASS" if output_paths and not missing and pdf_ok and baseline_ok and form_ok else "FAIL"
            rows.append(
                {
                    "artifact_type_id": artifact["artifact_type_id"],
                    "label": artifact["artifact_type_id"].replace("_", " ").title(),
                    "candidate_asset_total": len(output_paths),
                    "existing_candidate_asset_total": len(output_paths) - len(missing),
                    "score": 1.0 if state == "PASS" else 0.0,
                    "state": state,
                    "candidate_assets": [{"path": path, "exists_now": (ROOT / path).is_file()} for path in output_paths],
                    "metric_family": "artifact_hygiene",
                    "source": "generated_release_package_assembly",
                    "recovery_baseline": recovery_baseline,
                    "form_quality_status": "PASS" if form_ok else "FAIL",
                    "machine_form_gate_finding_total": len(artifact_form_findings),
                }
            )
        return rows
    rows: list[dict[str, Any]] = []
    for artifact in review_package.get("artifact_rows", []):
        candidate_total = int(artifact.get("candidate_asset_total", 0))
        existing_total = int(artifact.get("existing_candidate_asset_total", 0))
        rows.append(
            {
                "artifact_type_id": artifact["artifact_type_id"],
                "label": artifact["label"],
                "candidate_asset_total": candidate_total,
                "existing_candidate_asset_total": existing_total,
                "score": 1.0 if candidate_total > 0 and candidate_total == existing_total else 0.0,
                "state": "PASS" if candidate_total > 0 and candidate_total == existing_total else "FAIL",
                "candidate_assets": artifact.get("candidate_assets", []),
                "metric_family": "artifact_hygiene",
            }
        )
    return rows


def _terminal_contracts_by_node(assembly: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not assembly:
        return {}
    terminal_hash = assembly.get("source_hashes", {}).get("terminal_text_contracts_hash")
    release_id = assembly.get("release_identity", {}).get("release_id", "")
    version = assembly.get("release_identity", {}).get("version", "")
    if not release_id or not version:
        return {}
    path = assembly_paths(release_id, version, assembly.get("assembly_revision"))["terminal_contracts_json"]
    if not path.exists():
        return {}
    payload = read_json(path)
    if terminal_hash and payload.get("artifact_hash") != terminal_hash:
        return {}
    return {row["aggregator_node_id"]: row for row in payload.get("terminal_contracts", [])}


def _contract_quality_score(contract: dict[str, Any] | None, missing_required: list[str]) -> tuple[float | None, str, dict[str, Any]]:
    if not contract:
        return None, "NOT_ASSESSED", {"reason": "no generated terminal contract"}
    evidence = {
        "build_state": contract.get("build_state"),
        "source_ref_total": len(contract.get("source_refs", [])),
        "has_reader_task": bool(contract.get("reader_task")),
        "has_claim_boundary": bool(contract.get("claim_boundary")),
        "has_generated_text": bool(contract.get("generated_text")),
        "has_transition_out": bool(contract.get("transition_out")),
        "frontmatter_document_layer": bool(contract.get("frontmatter_document_layer")),
    }
    if contract.get("build_state") == "DOCUMENT_FRONTMATTER_RENDERED":
        return 1.0, "SCORED", evidence
    if contract.get("build_state") != "BUILDABLE":
        return 0.0, "FAIL", evidence
    if missing_required:
        return 0.65, "FAIL", evidence
    score = 0.0
    score += 0.18 if evidence["source_ref_total"] else 0.0
    score += 0.18 if evidence["has_reader_task"] else 0.0
    score += 0.18 if evidence["has_claim_boundary"] else 0.0
    score += 0.24 if evidence["has_generated_text"] else 0.0
    score += 0.12 if evidence["has_transition_out"] else 0.0
    score += 0.10
    return round(min(score, 1.0), 3), "SCORED", evidence


def _l10_quality_rows(aggregator: dict[str, Any], matrix: dict[str, Any], assembly: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    by_node = _projection_by_node(matrix)
    contracts_by_node = _terminal_contracts_by_node(assembly)
    rows: list[dict[str, Any]] = []
    for node in aggregator.get("nodes", []):
        if node.get("terminal_l10") is not True:
            continue
        projections = by_node.get(node["aggregator_node_id"], [])
        applicable = [row for row in projections if row.get("applicable")]
        required_ids = {
            "coverage.target_obligation",
            "trace.exact_source_binding",
            "claim.boundary_discipline",
            "didactic.reader_task_payoff",
            "structure.sequence_transition",
            "public.no_overclaim_surface",
        }
        applicable_ids = {row["metric_id"] for row in applicable}
        missing_required = sorted(required_ids - applicable_ids)
        coverage_status = str(node.get("coverage_status") or "not_assessed")
        contract = contracts_by_node.get(node["aggregator_node_id"])
        computed_score, quality_state, evidence = _contract_quality_score(contract, missing_required)
        rows.append(
            {
                "aggregator_node_id": node["aggregator_node_id"],
                "target_node_id": node["target_node_id"],
                "order_label": node["order_label"],
                "title": node["title"],
                "argument_role": node.get("argument_role"),
                "coverage_status": coverage_status,
                "parameterized_metric_total": len(applicable),
                "waived_metric_total": len(projections) - len(applicable),
                "missing_required_metric_ids": missing_required,
                "parameterization_score": 0.0 if missing_required else 1.0,
                "computed_quality_score": computed_score,
                "quality_state": quality_state,
                "scientific_coverage_status": coverage_status,
                "generation_evidence": evidence,
            }
        )
    return rows


def _recovery_regression_summary(package_assembly: dict[str, Any] | None) -> dict[str, Any]:
    if not package_assembly or package_assembly.get("structure_source") != "recovered_l10c":
        return {"applicable": False}
    master_rows = [
        row for row in package_assembly.get("artifact_rows", [])
        if row.get("artifact_type_id") == "master_monograph"
    ]
    pdf_build = (master_rows[0].get("pdf_build") if master_rows else {}) or {}
    pages = int(pdf_build.get("pages") or 0)
    return {
        "applicable": True,
        "old_public_master_baseline_pages": OLD_MASTER_BASELINE_PAGES,
        "recovered_master_pages": pages,
        "pass": pages >= OLD_MASTER_BASELINE_PAGES,
    }


def _cerberus_vulnerability(
    release_id: str,
    assembly_revision: str | None = None,
    package_assembly: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    path = editorial_cerberus_path(release_id, assembly_revision)
    if not path.exists():
        return {
            "vulnerability_id": "VULN-CERB-000",
            "root_class": "editorial_cerberus_summary_missing",
            "severity": "CRITICAL",
            "release_blocking": True,
            "affected_node_ids": [],
            "affected_artifacts": [str(path.relative_to(ROOT))],
            "finding_total": 1,
            "findings": [],
            "required_repair": "Run mandatory editorial Cerberus review and materialize structured summary.",
            "verification_rule": "Editorial Cerberus summary must exist with critical_open_total=0, high_open_total=0, parse_failure_total=0, all required roles present, and current PDF hashes.",
        }
    summary = read_json(path)
    required_roles = {
        "scientific_copyeditor",
        "technical_editor",
        "journal_editor",
        "layout_toc_page_flow_reviewer",
        "hostile_reader",
        "bibliography_metadata_editor",
        "claim_evidence_prosecutor",
    }
    role_ids = set(summary.get("role_ids") or [])
    missing_roles = sorted(required_roles - role_ids)
    expected_hashes = expected_cerberus_pdf_hashes(package_assembly)
    observed_hashes = summary.get("pdf_hashes") if isinstance(summary.get("pdf_hashes"), dict) else {}
    hash_mismatch = {
        key: {"expected": expected, "observed": observed_hashes.get(key)}
        for key, expected in sorted(expected_hashes.items())
        if observed_hashes.get(key) != expected
    }
    revision_mismatch = None
    if assembly_revision and summary.get("assembly_revision") != assembly_revision:
        revision_mismatch = {"expected": assembly_revision, "observed": summary.get("assembly_revision")}
    parse_failure_total = int(summary.get("parse_failure_total", 0))
    require_priority_routing = assembly_revision == "recovery_r014"
    local_first = summary.get("local_first_review") if isinstance(summary.get("local_first_review"), dict) else {}
    routing = summary.get("cerberus_priority_routing") if isinstance(summary.get("cerberus_priority_routing"), dict) else {}
    local_first_mismatch = None
    if require_priority_routing:
        if local_first.get("state") != "PASS":
            local_first_mismatch = {"expected": "PASS", "observed": local_first.get("state")}
        elif routing.get("external_review_enabled") is not True:
            local_first_mismatch = {"expected": "external_review_enabled true", "observed": routing.get("external_review_enabled")}
    if (
        summary.get("state") == "PASS"
        and int(summary.get("critical_open_total", 0)) == 0
        and int(summary.get("high_open_total", 0)) == 0
        and parse_failure_total == 0
        and not missing_roles
        and not hash_mismatch
        and not revision_mismatch
        and not local_first_mismatch
    ):
        return None
    findings = summary.get("findings", [])
    artifacts = sorted({finding.get("artifact", "unknown") for finding in findings})
    return {
        "vulnerability_id": "VULN-CERB-001",
        "root_class": "editorial_cerberus_open_findings",
        "severity": "CRITICAL" if int(summary.get("critical_open_total", 0)) else "HIGH",
        "release_blocking": True,
        "affected_node_ids": [],
        "affected_artifacts": sorted(set(artifacts + [str(path.relative_to(ROOT))])),
        "finding_total": len(findings)
        + len(missing_roles)
        + len(hash_mismatch)
        + (1 if revision_mismatch else 0)
        + (1 if local_first_mismatch else 0)
        + parse_failure_total,
        "critical_open_total": summary.get("critical_open_total", 0),
        "high_open_total": summary.get("high_open_total", 0),
        "parse_failure_total": parse_failure_total,
        "missing_roles": missing_roles,
        "hash_mismatch": hash_mismatch,
        "revision_mismatch": revision_mismatch,
        "local_first_mismatch": local_first_mismatch,
        "findings": findings,
        "required_repair": "Convert open editorial/Cerberus findings into minimal release remediation deltas, regenerate affected artifacts only, and rerun the affected roles.",
        "verification_rule": "Fresh editorial Cerberus summary must pass with zero critical/high findings, zero parse failures, all required roles, and current artifact hashes.",
    }


def build_audit_payload(release_id: str, assembly_revision: str | None = None) -> dict[str, Any]:
    version = version_from_release_id(release_id)
    paths = instance_paths(release_id, version)
    instance = read_json(paths["instance_json"])
    review_package = read_json(paths["review_package_json"])
    aggregator = read_json(aggregator_paths()["aggregator_json"])
    catalog = read_json(metric_catalog_paths()["catalog_json"])
    matrix = read_json(projection_paths()["matrix_json"])
    package = read_json(package_paths()["cascade_json"])
    rules = read_json(rules_paths()["rules_json"])
    package_assembly = _release_package_assembly(release_id, assembly_revision)
    machine_audit = _release_machine_audit(release_id, assembly_revision) if package_assembly else None
    if package_assembly:
        machine_form_summary = _machine_form_summary(machine_audit)
    else:
        machine_form_summary = {"machine_audit_status": None, "machine_form_gate_finding_total": 0}
        machine_form_summary.update({key: None for key in FORM_STATUS_KEYS})
    recovery_regression = _recovery_regression_summary(package_assembly)
    l10_rows = _l10_quality_rows(aggregator, matrix, package_assembly)
    artifact_rows = _artifact_scores(review_package, package_assembly, machine_audit)
    not_assessed_nodes = [row["aggregator_node_id"] for row in l10_rows if row["quality_state"] == "NOT_ASSESSED"]
    scientific_not_assessed_nodes = [row["aggregator_node_id"] for row in l10_rows if row.get("scientific_coverage_status") == "not_assessed"]
    missing_metric_rows = [row for row in l10_rows if row["missing_required_metric_ids"]]
    artifact_failures = [row for row in artifact_rows if row["state"] != "PASS"]
    vulnerabilities = build_vulnerability_rows(
        release_id,
        l10_rows,
        artifact_rows,
        recovery_regression,
        assembly_revision=assembly_revision,
        package_assembly=package_assembly,
    )
    blocking_total = sum(1 for row in vulnerabilities if row["release_blocking"])
    family_counts: Counter[str] = Counter()
    for row in matrix["projection_rows"]:
        if row["applicable"]:
            family_counts[row["metric_family"]] += 1
    payload: dict[str, Any] = {
        "schema_id": "OC_CORE_RELEASE_QUALITY_AUDIT_v1",
        "artifact_kind": "OC_CORE_RELEASE_QUALITY_AUDIT",
        "body_prose_included": False,
        "status": QUALITY_VALIDATION_STATUS_FAIL if blocking_total else QUALITY_VALIDATION_STATUS_PASS,
        "release_identity": instance["release_identity"],
        "assembly_revision": assembly_revision,
        "release_package_structure_source": (package_assembly or {}).get("structure_source"),
        "source_hashes": {
            "release_instance_hash": instance["artifact_hash"],
            "review_package_hash": review_package["artifact_hash"],
            "release_package_assembly_hash": (package_assembly or {}).get("artifact_hash"),
            "release_assembly_machine_audit_hash": (machine_audit or {}).get("artifact_hash"),
            "current_release_aggregator_hash": aggregator["artifact_hash"],
            "metric_catalog_hash": catalog["artifact_hash"],
            "l10_projection_matrix_hash": matrix["artifact_hash"],
            "package_cascade_hash": package["artifact_hash"],
            "text_fill_rules_hash": rules["artifact_hash"],
        },
        "summary": {
            "release_package_assembly_revision": assembly_revision,
            "release_package_structure_source": (package_assembly or {}).get("structure_source"),
            "terminal_l10_node_total": len(l10_rows),
            "metric_total": catalog["metric_total"],
            "projection_row_total": matrix["projection_row_total"],
            "applicable_projection_total": matrix["applicable_projection_total"],
            "not_assessed_l10_total": len(not_assessed_nodes),
            "scientific_coverage_not_assessed_l10_total": len(scientific_not_assessed_nodes),
            "missing_required_metric_node_total": len(missing_metric_rows),
            "artifact_type_total": len(artifact_rows),
            "artifact_failure_total": len(artifact_failures),
            **machine_form_summary,
            "recovered_package_regression_applicable": recovery_regression["applicable"],
            "old_public_master_baseline_pages": recovery_regression.get("old_public_master_baseline_pages"),
            "recovered_master_pages": recovery_regression.get("recovered_master_pages"),
            "recovered_master_baseline_pass": recovery_regression.get("pass"),
            "blocking_vulnerability_total": blocking_total,
            "vulnerability_total": len(vulnerabilities),
            "quality_claim_allowed": blocking_total == 0 and not not_assessed_nodes,
            "scientific_full_coverage_claim_allowed": False if scientific_not_assessed_nodes else blocking_total == 0,
        },
        "applicable_metric_family_counts": dict(sorted(family_counts.items())),
        "l10_quality_rows": l10_rows,
        "artifact_quality_rows": artifact_rows,
        "release_package_regression": recovery_regression,
        "vulnerability_ids": [row["vulnerability_id"] for row in vulnerabilities],
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def build_vulnerability_rows(
    release_id: str,
    l10_rows: list[dict[str, Any]],
    artifact_rows: list[dict[str, Any]],
    recovery_regression: dict[str, Any] | None = None,
    *,
    assembly_revision: str | None = None,
    package_assembly: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    vulnerabilities: list[dict[str, Any]] = []
    not_assessed = [row["aggregator_node_id"] for row in l10_rows if row["quality_state"] == "NOT_ASSESSED"]
    if not_assessed:
        vulnerabilities.append(
            {
                "vulnerability_id": "VULN-QA-001",
                "root_class": "l10_quality_scores_not_assessed",
                "severity": "HIGH",
                "release_blocking": True,
                "affected_node_ids": not_assessed,
                "affected_node_total": len(not_assessed),
                "affected_artifacts": [f"releases/{release_id}/editorial/quality_validation"],
                "finding_total": len(not_assessed),
                "required_repair": "Run or implement scorers for the L10 projection matrix and replace not_assessed with explicit complete/partial/planned/missing statuses plus evidence.",
                "verification_rule": f"python tools/audit_oc_core_release_quality.py --release {release_id} --check must report not_assessed_l10_total=0 before final quality promotion.",
            }
        )
    missing_required = [row for row in l10_rows if row["missing_required_metric_ids"]]
    if missing_required:
        vulnerabilities.append(
            {
                "vulnerability_id": "VULN-QA-002",
                "root_class": "l10_required_metric_projection_missing",
                "severity": "CRITICAL",
                "release_blocking": True,
                "affected_node_ids": [row["aggregator_node_id"] for row in missing_required],
                "affected_node_total": len(missing_required),
                "affected_artifacts": ["operations/release_assembly/oc_core/quality_parameterization/OC_CORE_L10_QUALITY_PROJECTION_MATRIX.json"],
                "finding_total": len(missing_required),
                "required_repair": "Repair projection rules so every L10 terminal node has required positive, traceability, didactic, structure, and safety metrics.",
                "verification_rule": "python tools/build_oc_core_l10_quality_projection_matrix.py --check must pass with no node_missing_required_metrics failures.",
            }
        )
    scientific_not_assessed = [row["aggregator_node_id"] for row in l10_rows if row.get("scientific_coverage_status") == "not_assessed"]
    if scientific_not_assessed:
        vulnerabilities.append(
            {
                "vulnerability_id": "VULN-QA-003",
                "root_class": "l10_scientific_coverage_not_assessed",
                "severity": "CRITICAL",
                "release_blocking": True,
                "affected_node_ids": scientific_not_assessed,
                "affected_node_total": len(scientific_not_assessed),
                "affected_artifacts": [f"releases/{release_id}/editorial/quality_validation"],
                "finding_total": len(scientific_not_assessed),
                "required_repair": "Replace blanket scientific coverage not_assessed values with deterministic complete/partial/planned/missing assessments and source/evidence notes.",
                "verification_rule": f"python tools/audit_oc_core_release_quality.py --release {release_id} --assembly-revision {assembly_revision or '<revision>'} --check must report scientific_coverage_not_assessed_l10_total=0.",
            }
        )
    form_failed_artifacts = [row for row in artifact_rows if row.get("form_quality_status") == "FAIL"]
    failed_artifacts = [row for row in artifact_rows if row["state"] != "PASS" and row.get("form_quality_status") != "FAIL"]
    if form_failed_artifacts:
        vulnerabilities.append(
            {
                "vulnerability_id": "VULN-MA-001",
                "root_class": "release_artifact_form_gate_failure",
                "severity": "CRITICAL",
                "release_blocking": True,
                "affected_node_ids": [],
                "affected_artifacts": [row["artifact_type_id"] for row in form_failed_artifacts],
                "finding_total": sum(int(row.get("machine_form_gate_finding_total") or 0) for row in form_failed_artifacts),
                "required_repair": "Repair the generated title page, table of contents, or visible heading hierarchy and rerun the assembly machine audit.",
                "verification_rule": f"python tools/audit_oc_core_release_assembly_machine.py --release {release_id} --check must show form_quality_status=PASS and form_finding_total=0.",
            }
        )
    if failed_artifacts:
        vulnerabilities.append(
            {
                "vulnerability_id": "VULN-ASSET-001",
                "root_class": "release_artifact_role_or_existence_failure",
                "severity": "HIGH",
                "release_blocking": True,
                "affected_node_ids": [],
                "affected_artifacts": [row["artifact_type_id"] for row in failed_artifacts],
                "finding_total": len(failed_artifacts),
                "required_repair": "Repair release profile or generate missing artifact candidates so every package artifact role has existing assets.",
                "verification_rule": f"python tools/build_oc_core_release_instance.py --release {release_id} --check and quality audit must show artifact_failure_total=0.",
            }
        )
    if recovery_regression and recovery_regression.get("applicable") and not recovery_regression.get("pass"):
        vulnerabilities.append(
            {
                "vulnerability_id": "VULN-RECOVERY-001",
                "root_class": "recovered_master_regresses_below_old_public_baseline",
                "severity": "CRITICAL",
                "release_blocking": True,
                "affected_node_ids": [],
                "affected_artifacts": ["master_monograph"],
                "finding_total": 1,
                "old_public_master_baseline_pages": recovery_regression.get("old_public_master_baseline_pages"),
                "recovered_master_pages": recovery_regression.get("recovered_master_pages"),
                "required_repair": "Recover additional historical/source-bound nodes or repair PDF assembly so the recovered master monograph does not regress below the old public baseline.",
                "verification_rule": f"python tools/assemble_oc_core_release_package.py --release {release_id} --structure-source recovered_l10c --assembly-revision recovery_r001 --check must pass and recovered_master_pages must be >= {OLD_MASTER_BASELINE_PAGES}.",
            }
        )
    cerberus = _cerberus_vulnerability(release_id, assembly_revision, package_assembly)
    if cerberus:
        vulnerabilities.append(cerberus)
    return vulnerabilities


def build_protocol_payload(release_id: str, audit: dict[str, Any]) -> dict[str, Any]:
    l10_rows = audit["l10_quality_rows"]
    artifact_rows = audit["artifact_quality_rows"]
    assembly_revision = audit.get("assembly_revision")
    package_assembly = _release_package_assembly(release_id, assembly_revision)
    vulnerabilities = build_vulnerability_rows(
        release_id,
        l10_rows,
        artifact_rows,
        audit.get("release_package_regression"),
        assembly_revision=assembly_revision,
        package_assembly=package_assembly,
    )
    severity_counts = Counter(row["severity"] for row in vulnerabilities)
    payload: dict[str, Any] = {
        "schema_id": "OC_CORE_RELEASE_VULNERABILITY_PROTOCOL_v1",
        "artifact_kind": "OC_CORE_RELEASE_VULNERABILITY_PROTOCOL",
        "body_prose_included": False,
        "status": "OPEN_VULNERABILITIES" if vulnerabilities else "NO_OPEN_VULNERABILITIES",
        "release_identity": audit["release_identity"],
        "source_hashes": {
            "release_quality_audit_hash": audit["artifact_hash"],
            **audit["source_hashes"],
        },
        "vulnerability_total": len(vulnerabilities),
        "blocking_vulnerability_total": sum(1 for row in vulnerabilities if row["release_blocking"]),
        "severity_counts": dict(sorted(severity_counts.items())),
        "vulnerabilities": vulnerabilities,
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def build_delta_payload(release_id: str, audit: dict[str, Any], protocol: dict[str, Any]) -> dict[str, Any]:
    blocking = [row for row in protocol["vulnerabilities"] if row["release_blocking"]]
    affected_nodes = sorted({node for row in blocking for node in row.get("affected_node_ids", [])})
    affected_artifacts = sorted({artifact for row in blocking for artifact in row.get("affected_artifacts", [])})
    delta_items: list[dict[str, Any]] = []
    qa_ids = [row["vulnerability_id"] for row in blocking if row["root_class"] == "l10_quality_scores_not_assessed"]
    scientific_qa_ids = [row["vulnerability_id"] for row in blocking if row["root_class"] == "l10_scientific_coverage_not_assessed"]
    if qa_ids:
        delta_items.append(
            {
                "delta_item_id": "DELTA-r001-QA-SCORING",
                "source_vulnerability_ids": qa_ids,
                "minimal_source_delta": "Implement or run L10 scorers against the existing projection matrix; do not rewrite prose unless a scorer localizes a concrete content defect.",
                "expected_output_delta": "Refresh quality audit statuses from not_assessed to explicit complete/partial/planned/missing values with evidence.",
                "verification_commands": [
                    f"python tools/build_oc_core_l10_quality_projection_matrix.py --check",
                    f"python tools/audit_oc_core_release_quality.py --release {release_id} --check",
                ],
                "closure_evidence": "not_assessed_l10_total becomes 0 or each remaining not_assessed row is justified by an explicit blocker protocol row.",
            }
        )
    if scientific_qa_ids:
        delta_items.append(
            {
                "delta_item_id": "DELTA-r001-SCIENTIFIC-COVERAGE",
                "source_vulnerability_ids": scientific_qa_ids,
                "minimal_source_delta": "Assess each terminal L10 scientific coverage row deterministically from existing source and evidence anchors; demote unsupported public claims instead of overclaiming.",
                "expected_output_delta": "scientific_coverage_not_assessed_l10_total becomes 0 and scientific_full_coverage_claim_allowed becomes true only when no blocking rows remain.",
                "verification_commands": [
                    f"python tools/audit_oc_core_release_quality.py --release {release_id} --check",
                ],
                "closure_evidence": "All L10 coverage statuses are complete, partial, planned, or missing with no promoted missing claims.",
            }
        )
    cerb_ids = [row["vulnerability_id"] for row in blocking if row["root_class"].startswith("editorial_cerberus")]
    if cerb_ids:
        delta_items.append(
            {
                "delta_item_id": "DELTA-r001-CERBERUS-EDITORIAL",
                "source_vulnerability_ids": cerb_ids,
                "minimal_source_delta": "Repair only artifact/source sections named by editorial Cerberus findings, then rerun the missing/current editorial roles.",
                "expected_output_delta": "Fresh editorial Cerberus summary with current hashes and zero critical/high findings.",
                "verification_commands": [
                    f"python tools/audit_oc_core_release_quality.py --release {release_id} --check",
                    "python tools\\oc133_public_release_payload.py --generic-assembly-check",
                ],
                "closure_evidence": "VULN-CERB rows disappear from the vulnerability protocol.",
            }
        )
    payload: dict[str, Any] = {
        "schema_id": "OC_CORE_RELEASE_REMEDIATION_DELTA_v1",
        "artifact_kind": "OC_CORE_RELEASE_REMEDIATION_DELTA",
        "body_prose_included": False,
        "status": "DELTA_REPAIR_REQUIRED" if blocking else "NO_DELTA_REQUIRED",
        "release_identity": audit["release_identity"],
        "remediation_revision": DELTA_REVISION,
        "parent_hashes": {
            "release_instance_hash": audit["source_hashes"]["release_instance_hash"],
            "release_quality_audit_hash": audit["artifact_hash"],
            "vulnerability_protocol_hash": protocol["artifact_hash"],
        },
        "affected_node_total": len(affected_nodes),
        "affected_node_ids": affected_nodes,
        "affected_artifacts": affected_artifacts,
        "delta_items": delta_items,
        "allowed_write_scope": [
            f"releases/{release_id}/editorial/quality_validation",
            "reviews/oc133_llm_cerberus/editorial_release_review",
            "only artifact source files explicitly named by a vulnerability row",
        ],
        "forbidden_write_scope": ["GitHub Release", "Zenodo", "tag movement", "DOI minting", "journal submission"],
        "rollback_or_block_rule": "If a proposed delta touches nodes or artifacts not named here, block it and create a new owner-reviewed delta revision.",
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def validate_protocol(protocol: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    for row in protocol.get("vulnerabilities", []):
        for key in ["vulnerability_id", "root_class", "severity", "release_blocking", "affected_artifacts", "required_repair", "verification_rule"]:
            if key not in row or row.get(key) in (None, ""):
                failures.append(f"vulnerability_missing_{key}::{row.get('vulnerability_id')}")
        if not row.get("affected_artifacts") and not row.get("affected_node_ids"):
            failures.append(f"vulnerability_missing_affected_scope::{row.get('vulnerability_id')}")
    if protocol.get("artifact_hash") != artifact_hash(protocol):
        failures.append("protocol_hash_mismatch")
    return failures


def validate_delta(delta: dict[str, Any], protocol: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if delta.get("parent_hashes", {}).get("vulnerability_protocol_hash") != protocol.get("artifact_hash"):
        failures.append("delta_protocol_hash_mismatch")
    if delta.get("status") == "DELTA_REPAIR_REQUIRED" and not delta.get("affected_artifacts") and not delta.get("affected_node_ids"):
        failures.append("delta_missing_affected_scope")
    for item in delta.get("delta_items", []):
        for key in ["delta_item_id", "minimal_source_delta", "expected_output_delta", "verification_commands", "closure_evidence"]:
            if not item.get(key):
                failures.append(f"delta_item_missing_{key}::{item.get('delta_item_id')}")
    if delta.get("artifact_hash") != artifact_hash(delta):
        failures.append("delta_hash_mismatch")
    return failures


def validate_audit(audit: dict[str, Any], protocol: dict[str, Any], delta: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    summary = audit.get("summary", {})
    if summary.get("not_assessed_l10_total", 0) > 0 and audit.get("status") == QUALITY_VALIDATION_STATUS_PASS:
        failures.append("audit_claims_pass_with_not_assessed_l10")
    if summary.get("blocking_vulnerability_total") != protocol.get("blocking_vulnerability_total"):
        failures.append("audit_protocol_blocking_total_mismatch")
    failures.extend(validate_protocol(protocol))
    failures.extend(validate_delta(delta, protocol))
    if audit.get("artifact_hash") != artifact_hash(audit):
        failures.append("audit_hash_mismatch")
    return failures


def render_audit_md(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        f"# OC Core Release Quality Audit {payload['release_identity']['version']}",
        "",
        f"Status: `{payload['status']}`",
        f"Artifact hash: `{payload['artifact_hash']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Metric Families", ""])
    for family, count in payload["applicable_metric_family_counts"].items():
        lines.append(f"- `{family}`: {count}")
    lines.extend(["", "## L10 Status Counts", ""])
    counts = Counter(row["quality_state"] for row in payload["l10_quality_rows"])
    for state, count in sorted(counts.items()):
        lines.append(f"- `{state}`: {count}")
    return "\n".join(lines)


def render_protocol_md(payload: dict[str, Any]) -> str:
    lines = [
        f"# OC Core Release Vulnerability Protocol {payload['release_identity']['version']}",
        "",
        f"Status: `{payload['status']}`",
        f"Artifact hash: `{payload['artifact_hash']}`",
        f"Vulnerabilities: `{payload['vulnerability_total']}`",
        f"Blocking: `{payload['blocking_vulnerability_total']}`",
        "",
    ]
    for row in payload["vulnerabilities"]:
        lines.append(f"## `{row['vulnerability_id']}` {row['root_class']}")
        lines.append("")
        lines.append(f"- Severity: `{row['severity']}`")
        lines.append(f"- Blocking: `{row['release_blocking']}`")
        lines.append(f"- Affected nodes: `{len(row.get('affected_node_ids', []))}`")
        lines.append(f"- Affected artifacts: {', '.join(row.get('affected_artifacts', []))}")
        lines.append(f"- Required repair: {row['required_repair']}")
        lines.append(f"- Verification: {row['verification_rule']}")
        lines.append("")
    return "\n".join(lines)


def render_delta_md(payload: dict[str, Any]) -> str:
    lines = [
        f"# OC Core Release Remediation Delta {payload['release_identity']['version']}.{payload['remediation_revision']}",
        "",
        f"Status: `{payload['status']}`",
        f"Artifact hash: `{payload['artifact_hash']}`",
        f"Affected nodes: `{payload['affected_node_total']}`",
        "",
        "## Delta Items",
        "",
    ]
    for item in payload["delta_items"]:
        lines.append(f"### `{item['delta_item_id']}`")
        lines.append(f"- Source vulnerabilities: {', '.join(item['source_vulnerability_ids']) or 'none'}")
        lines.append(f"- Minimal source delta: {item['minimal_source_delta']}")
        lines.append(f"- Expected output delta: {item['expected_output_delta']}")
        lines.append(f"- Closure evidence: {item['closure_evidence']}")
        lines.append("")
    return "\n".join(lines)


def expected_files(release_id: str, assembly_revision: str | None = None) -> dict[Path, str]:
    version = version_from_release_id(release_id)
    audit = build_audit_payload(release_id, assembly_revision)
    protocol = build_protocol_payload(release_id, audit)
    delta = build_delta_payload(release_id, audit, protocol)
    failures = validate_audit(audit, protocol, delta)
    if failures:
        raise RuntimeError(f"Release quality audit validation failed: {failures[:20]}")
    paths = quality_paths(release_id, version, assembly_revision)
    return {
        paths["audit_json"]: stable_json(audit),
        paths["audit_md"]: render_audit_md(audit),
        paths["protocol_json"]: stable_json(protocol),
        paths["protocol_md"]: render_protocol_md(protocol),
        paths["delta_json"]: stable_json(delta),
        paths["delta_md"]: render_delta_md(delta),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit OC Core release quality and emit vulnerability/delta protocols.")
    parser.add_argument("--release", required=True, help="Release id such as oc_core_1_3_3.")
    parser.add_argument("--assembly-revision")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if not args.write and not args.check:
        args.check = True
    result = validation_result(expected_files(args.release, args.assembly_revision), write=args.write)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["state"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
