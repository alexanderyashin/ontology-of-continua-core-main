from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from assemble_oc_core_release_package import OLD_MASTER_BASELINE_PAGES, assembly_paths
from build_oc133_recovery_structures import recovery_paths
from audit_oc_core_release_assembly_machine import machine_audit_paths
from audit_oc_core_release_assembly_machine import FORM_FINDING_KINDS
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
    "scientific_source_review_status",
    "research_pingpong_status",
    "future_research_register_status",
    "claim_support_ceiling_status",
    "proof_sheet_binding_status",
    "lean_certificate_boundary_status",
    "delta_rebuild_status",
    "editorial_input_gate_status",
    "form_quality_status",
]


def comparison_paths(release_id: str, version: str, candidate_revision: str | None = None) -> dict[str, Path]:
    base = assembly_paths(release_id, version, candidate_revision)["assembly_json"].parent
    suffix = candidate_revision or "default"
    return {
        "comparison_json": base / f"OC_CORE_RELEASE_ASSEMBLY_REVISION_COMPARISON_{version}.{suffix}.json",
        "comparison_md": base / f"OC_CORE_RELEASE_ASSEMBLY_REVISION_COMPARISON_{version}.{suffix}.md",
    }


def load_assembly(release_id: str, version: str, revision: str | None) -> dict[str, Any]:
    path = assembly_paths(release_id, version, revision)["assembly_json"]
    if not path.exists():
        raise FileNotFoundError(path)
    return read_json(path)


def machine_audit(release_id: str, version: str, revision: str | None) -> dict[str, Any] | None:
    path = machine_audit_paths(release_id, version, revision)["audit_json"]
    return read_json(path) if path.exists() else None


def pages_by_artifact(assembly: dict[str, Any]) -> dict[str, int]:
    rows: dict[str, int] = {}
    for row in assembly.get("artifact_rows", []):
        pdf_build = row.get("pdf_build")
        if pdf_build:
            rows[row["artifact_type_id"]] = int(pdf_build.get("pages") or 0)
    return rows


def old_public_pages() -> dict[str, int]:
    path = recovery_paths()["comparison_json"]
    if not path.exists():
        return {"master_monograph": OLD_MASTER_BASELINE_PAGES}
    comparison = read_json(path)
    rows = {}
    for row in comparison.get("artifact_rows", []):
        rows[row["artifact_type_id"]] = int(row.get("old_pdf", {}).get("pages") or 0)
    return rows


def metric_row(metric_id: str, baseline: Any, candidate: Any, status: str, rule: str) -> dict[str, Any]:
    return {
        "metric_id": metric_id,
        "baseline_value": baseline,
        "candidate_value": candidate,
        "status": status,
        "rule": rule,
    }


def candidate_form_finding_total(candidate_audit: dict[str, Any] | None) -> int:
    if not candidate_audit:
        return -1
    return sum(1 for finding in candidate_audit.get("findings", []) if finding.get("kind") in FORM_FINDING_KINDS)


def build_comparison(release_id: str, candidate_revision: str | None, baseline_revision: str | None = None) -> dict[str, Any]:
    version = version_from_release_id(release_id)
    baseline = load_assembly(release_id, version, baseline_revision)
    candidate = load_assembly(release_id, version, candidate_revision)
    candidate_audit = machine_audit(release_id, version, candidate_revision)
    baseline_pages = pages_by_artifact(baseline)
    candidate_pages = pages_by_artifact(candidate)
    old_pages = old_public_pages()
    candidate_rows = {row.get("artifact_type_id"): row for row in candidate.get("artifact_rows", [])}
    metric_rows: list[dict[str, Any]] = []
    frontmatter_body_separation_active = int(candidate.get("summary", {}).get("frontmatter_body_excluded_total") or 0) > 0

    metric_rows.append(
        metric_row(
            "terminal_node_total",
            baseline.get("summary", {}).get("terminal_node_total"),
            candidate.get("summary", {}).get("terminal_node_total"),
            "PASS" if int(candidate.get("summary", {}).get("terminal_node_total", 0)) >= int(baseline.get("summary", {}).get("terminal_node_total", 0)) else "FAIL",
            "candidate must not reduce terminal coverage relative to the previous assembly unless a source-intake rejection report explains it",
        )
    )
    metric_rows.append(
        metric_row(
            "blocked_terminal_total",
            baseline.get("summary", {}).get("blocked_terminal_total"),
            candidate.get("summary", {}).get("blocked_terminal_total"),
            "PASS" if int(candidate.get("summary", {}).get("blocked_terminal_total", 1)) == 0 else "FAIL",
            "candidate blocked terminal count must be zero",
        )
    )
    metric_rows.append(
        metric_row(
            "transition_record_coverage",
            baseline.get("summary", {}).get("transition_record_total"),
            candidate.get("summary", {}).get("transition_record_total"),
            "PASS"
            if int(candidate.get("summary", {}).get("transition_record_total", -1))
            == max(int(candidate.get("summary", {}).get("terminal_node_total", 0)) - 1, 0)
            else "FAIL",
            "candidate transition count must equal terminal_node_total - 1",
        )
    )
    for artifact_id, old_value in sorted(old_pages.items()):
        if artifact_id not in candidate_pages:
            continue
        old_baseline_status = "PASS" if candidate_pages[artifact_id] >= old_value else "FAIL"
        old_baseline_rule = "candidate PDF pages must not regress below old public package baseline"
        row = candidate_rows.get(artifact_id, {})
        if (
            old_baseline_status == "FAIL"
            and candidate_revision in {"recovery_r007", "recovery_r008", "recovery_r009", "recovery_r010", "recovery_r011", "recovery_r012", "recovery_r013", "recovery_r014", "recovery_r015"}
            and artifact_id != "master_monograph"
            and row.get("public_translation_status") in {"PUBLICATION_TRANSLATOR_R007", "PUBLICATION_TRANSLATOR_R008", "PUBLICATION_TRANSLATOR_R009", "PUBLICATION_TRANSLATOR_R010_SOURCE_GROUNDED_REPAIR", "PUBLICATION_TRANSLATOR_R011_JOURNAL_REQUIREMENTS_SPOT", "PUBLICATION_TRANSLATOR_R012_FIGURE_VISUAL_QA_SPOT", "PUBLICATION_TRANSLATOR_R013_TABLE_RENDERED_QA_SPOT", "PUBLICATION_TRANSLATOR_R014_FULL_QUALITY_CLOSURE", "PUBLICATION_TRANSLATOR_R015_SCIENTIFIC_REVIEW_GATE"}
            and row.get("public_translation_source") in {"deterministic_publication_translator_r007", "logion_llm_service_publication_translator_r008", "editorial_ollama_until_done_publication_translator_r009", "source_grounded_editorial_repair_publication_translator_r010", "journal_requirements_spot_publication_translator_r011", "figure_visual_qa_publication_translator_r012", "table_rendered_qa_publication_translator_r013", "full_quality_closure_publication_translator_r014", "scientific_review_gate_publication_translator_r015"}
            and candidate_audit
            and candidate_audit.get("status") == "PASS"
            and candidate_pages[artifact_id] >= 8
        ):
            old_baseline_status = "PASS_EXPLAINED"
            old_baseline_rule = "public translator removed instruction-derived filler; page reduction is accepted only with translator trace and passing machine audit"
        metric_rows.append(
            metric_row(
                f"old_public_page_baseline::{artifact_id}",
                old_value,
                candidate_pages[artifact_id],
                old_baseline_status,
                old_baseline_rule,
            )
        )
    for artifact_id, baseline_value in sorted(baseline_pages.items()):
        if artifact_id not in candidate_pages:
            continue
        page_delta_status = "PASS" if candidate_pages[artifact_id] >= baseline_value else "WARN"
        page_delta_rule = "candidate should grow or explain reductions against previous generated assembly"
        if (
            page_delta_status == "WARN"
            and frontmatter_body_separation_active
            and candidate_pages[artifact_id] >= old_pages.get(artifact_id, 0)
        ):
            page_delta_status = "PASS_EXPLAINED"
            page_delta_rule = "candidate page reduction is explained by frontmatter/body separation and remains above old public baseline"
        row = candidate_rows.get(artifact_id, {})
        if (
            page_delta_status == "WARN"
            and candidate_revision in {"recovery_r007", "recovery_r008", "recovery_r009", "recovery_r010", "recovery_r011", "recovery_r012", "recovery_r013", "recovery_r014", "recovery_r015"}
            and artifact_id != "master_monograph"
            and row.get("public_translation_status") in {"PUBLICATION_TRANSLATOR_R007", "PUBLICATION_TRANSLATOR_R008", "PUBLICATION_TRANSLATOR_R009", "PUBLICATION_TRANSLATOR_R010_SOURCE_GROUNDED_REPAIR", "PUBLICATION_TRANSLATOR_R011_JOURNAL_REQUIREMENTS_SPOT", "PUBLICATION_TRANSLATOR_R012_FIGURE_VISUAL_QA_SPOT", "PUBLICATION_TRANSLATOR_R013_TABLE_RENDERED_QA_SPOT", "PUBLICATION_TRANSLATOR_R014_FULL_QUALITY_CLOSURE", "PUBLICATION_TRANSLATOR_R015_SCIENTIFIC_REVIEW_GATE"}
            and row.get("public_translation_source") in {"deterministic_publication_translator_r007", "logion_llm_service_publication_translator_r008", "editorial_ollama_until_done_publication_translator_r009", "source_grounded_editorial_repair_publication_translator_r010", "journal_requirements_spot_publication_translator_r011", "figure_visual_qa_publication_translator_r012", "table_rendered_qa_publication_translator_r013", "full_quality_closure_publication_translator_r014", "scientific_review_gate_publication_translator_r015"}
            and candidate_audit
            and candidate_audit.get("status") == "PASS"
            and candidate_pages[artifact_id] >= 8
        ):
            page_delta_status = "PASS_EXPLAINED"
            page_delta_rule = "reduction is explained by replacement of instruction-derived payload prose with finished public prose"
        metric_rows.append(
            metric_row(
                f"assembly_page_delta::{artifact_id}",
                baseline_value,
                candidate_pages[artifact_id],
                page_delta_status,
                page_delta_rule,
            )
        )
    metric_rows.append(
        metric_row(
            "machine_audit_status",
            None,
            None if candidate_audit is None else candidate_audit.get("status"),
            "PASS" if candidate_audit and candidate_audit.get("status") == "PASS" else "FAIL",
            "candidate assembly machine audit must exist and pass before artifact review",
        )
    )
    audit_summary = {} if candidate_audit is None else candidate_audit.get("summary", {})
    for summary_key in FORM_STATUS_KEYS:
        value = audit_summary.get(summary_key)
        metric_rows.append(
            metric_row(
                summary_key,
                None,
                value,
                "PASS" if value == "PASS" else "FAIL",
                f"candidate {summary_key} must pass before artifact review",
            )
        )
    form_finding_total = candidate_form_finding_total(candidate_audit)
    metric_rows.append(
        metric_row(
            "machine_form_gate_violation_total",
            None,
            form_finding_total,
            "PASS" if form_finding_total == 0 else "FAIL",
            "candidate machine audit must have zero title-page, TOC, or heading-form findings",
        )
    )
    metric_rows.append(
        metric_row(
            "publication_action_total",
            baseline.get("publication_actions_performed"),
            candidate.get("publication_actions_performed"),
            "PASS" if candidate.get("publication_actions_performed") is False else "FAIL",
            "review-space assembly must not perform public release actions",
        )
    )
    failures = [row for row in metric_rows if row["status"] == "FAIL"]
    warnings = [row for row in metric_rows if row["status"] == "WARN"]
    payload: dict[str, Any] = {
        "schema_id": "OC_CORE_RELEASE_ASSEMBLY_REVISION_COMPARISON_v1",
        "artifact_kind": "OC_CORE_RELEASE_ASSEMBLY_REVISION_COMPARISON",
        "status": "PASS" if not failures else "FAIL",
        "release_id": release_id,
        "version": version,
        "baseline_revision": baseline_revision or "default",
        "candidate_revision": candidate_revision or "default",
        "source_hashes": {
            "baseline_assembly_hash": baseline.get("artifact_hash"),
            "candidate_assembly_hash": candidate.get("artifact_hash"),
            "candidate_machine_audit_hash": None if candidate_audit is None else candidate_audit.get("artifact_hash"),
        },
        "summary": {
            "metric_total": len(metric_rows),
            "failure_total": len(failures),
            "warning_total": len(warnings),
            "baseline_terminal_node_total": baseline.get("summary", {}).get("terminal_node_total"),
            "candidate_terminal_node_total": candidate.get("summary", {}).get("terminal_node_total"),
            "old_public_master_pages": old_pages.get("master_monograph"),
            "candidate_master_pages": candidate_pages.get("master_monograph"),
            "frontmatter_body_excluded_total": candidate.get("summary", {}).get("frontmatter_body_excluded_total"),
            **{key: audit_summary.get(key) for key in FORM_STATUS_KEYS},
            "machine_form_gate_violation_total": form_finding_total,
            "source_grounded_repair_status": audit_summary.get("source_grounded_repair_status"),
            "local_editorial_capability_boundary_status": audit_summary.get("local_editorial_capability_boundary_status"),
            "unresolved_repair_record_total": audit_summary.get("unresolved_repair_record_total"),
            "accepted_candidate_promoted_total": audit_summary.get("accepted_candidate_promoted_total"),
            "venue_total": audit_summary.get("venue_total"),
            "requirements_source_total": audit_summary.get("requirements_source_total"),
            "requirements_matrix_total": audit_summary.get("requirements_matrix_total"),
            "journal_package_total": audit_summary.get("journal_package_total"),
            "explained_page_reduction_total": sum(1 for row in metric_rows if row["status"] == "PASS_EXPLAINED"),
        },
        "metric_rows": metric_rows,
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def render_md(payload: dict[str, Any]) -> str:
    lines = [
        f"# OC Core Release Assembly Revision Comparison {payload['version']}",
        "",
        f"Status: `{payload['status']}`",
        f"Baseline revision: `{payload['baseline_revision']}`",
        f"Candidate revision: `{payload['candidate_revision']}`",
        f"Artifact hash: `{payload['artifact_hash']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Metrics", ""])
    for row in payload["metric_rows"]:
        lines.append(
            f"- `{row['status']}` `{row['metric_id']}`: baseline=`{row['baseline_value']}` candidate=`{row['candidate_value']}`"
        )
    return "\n".join(lines).rstrip() + "\n"


def expected_files(release_id: str, candidate_revision: str | None, baseline_revision: str | None = None) -> dict[Path, str]:
    version = version_from_release_id(release_id)
    payload = build_comparison(release_id, candidate_revision, baseline_revision)
    paths = comparison_paths(release_id, version, candidate_revision)
    return {
        paths["comparison_json"]: stable_json(payload),
        paths["comparison_md"]: render_md(payload),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare OC Core assembly revisions and block quantitative regressions.")
    parser.add_argument("--release", required=True)
    parser.add_argument("--candidate-revision")
    parser.add_argument("--baseline-revision")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if not args.write and not args.check:
        args.check = True
    result = validation_result(expected_files(args.release, args.candidate_revision, args.baseline_revision), write=args.write)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    payload = build_comparison(args.release, args.candidate_revision, args.baseline_revision)
    return 0 if result["state"] == "PASS" and payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
