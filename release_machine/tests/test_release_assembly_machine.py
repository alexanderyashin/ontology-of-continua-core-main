from __future__ import annotations

import json
import importlib.util
import re
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[2]
ASSEMBLY = ROOT / "operations" / "release_assembly" / "oc_core"
R005_FORM_STATUS_KEYS = [
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
    "technical_prose_leak_status",
    "reader_facing_reference_status",
    "didactic_density_status",
    "form_quality_status",
]
R006_FORM_STATUS_KEYS = R005_FORM_STATUS_KEYS + [
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
]
R007_FORM_STATUS_KEYS = R006_FORM_STATUS_KEYS + [
    "publication_translation_status",
    "instruction_prose_leak_status",
    "page17_internal_leak_status",
    "figure_pedagogy_status",
    "k_hierarchy_figure_status",
    "all_reader_pdf_translation_status",
    "governed_ollama_status",
    "v_model_audit_status",
]
R008_FORM_STATUS_KEYS = R007_FORM_STATUS_KEYS + [
    "common_llm_service_status",
    "llm_service_governance_status",
    "llm_service_cadence_status",
    "llm_service_thermal_monitor_status",
    "llm_service_no_bypass_status",
    "llm_service_vmodel_status",
    "local_ollama_capability_status",
]
R009_FORM_STATUS_KEYS = R008_FORM_STATUS_KEYS + [
    "editorial_llm_queue_status",
    "editorial_packet_coverage_status",
    "actual_ollama_invocation_status",
    "until_done_status",
    "cooldown_resume_status",
    "v_model_completion_status",
    "local_capability_exhaustion_status",
]
R010_FORM_STATUS_KEYS = R009_FORM_STATUS_KEYS
R011_FORM_STATUS_KEYS = R010_FORM_STATUS_KEYS + [
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
]
R012_FORM_STATUS_KEYS = R011_FORM_STATUS_KEYS + [
    "figure_spec_coverage_status",
    "diagram_geometry_status",
    "rendered_figure_bbox_status",
    "label_collision_status",
    "figure_semantic_completeness_status",
    "k_hierarchy_visual_status",
    "continuum_visual_status",
    "caption_argument_status",
    "visual_cockpit_status",
]
R013_FORM_STATUS_KEYS = R012_FORM_STATUS_KEYS + [
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
]
R014_FORM_STATUS_KEYS = R013_FORM_STATUS_KEYS + [
    "cerberus_static_leak_status",
    "methods_path_integrity_status",
    "reviewer_map_argument_status",
    "r014_quality_closure_status",
]
R015_FORM_STATUS_KEYS = R014_FORM_STATUS_KEYS + [
    "scientific_source_review_status",
    "research_pingpong_status",
    "future_research_register_status",
    "claim_support_ceiling_status",
    "proof_sheet_binding_status",
    "lean_certificate_boundary_status",
    "delta_rebuild_status",
    "editorial_input_gate_status",
]
R016_FORM_STATUS_KEYS = R015_FORM_STATUS_KEYS + [
    "machine_self_audit_status",
    "filter_regression_status",
    "reviewer_routing_status",
    "cockpit_observability_status",
    "artifact_precision_status",
    "journal_projection_consistency_status",
    "zenodo_readiness_assessment_status",
    "toe_gap_assessment_status",
    "r017_final_gate_status",
]


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class ReleaseAssemblyMachineTests(unittest.TestCase):
    def test_common_aggregator_is_not_versioned_release_toc(self) -> None:
        path = ASSEMBLY / "current_release_aggregator" / "OC_CORE_CURRENT_RELEASE_AGGREGATOR.json"
        payload = read_json(path)
        text = json.dumps(payload, ensure_ascii=False)
        self.assertEqual(payload["artifact_kind"], "OC_CORE_CURRENT_RELEASE_AGGREGATOR")
        self.assertNotRegex(text, re.compile(r"\b1\.3\.3\b"))
        self.assertNotIn("github", text.lower())
        self.assertNotIn("zenodo", text.lower())
        self.assertNotIn(".pdf", text.lower())
        self.assertNotIn(".zip", text.lower())
        self.assertGreater(payload["node_total"], 5000)

    def test_package_cascade_has_standard_artifact_set(self) -> None:
        path = ASSEMBLY / "package_structure" / "OC_CORE_RELEASE_PACKAGE_CASCADE.json"
        payload = read_json(path)
        self.assertEqual(payload["artifact_type_total"], 9)
        for artifact in payload["artifact_types"]:
            self.assertTrue(artifact["standard_package_member"])
            self.assertGreaterEqual(len(artifact["mini_cascade"]), 3)
            self.assertTrue(artifact["purpose"])
            self.assertTrue(artifact["known_error_classes_prevented"])

    def test_text_fill_rules_are_positive_and_negative(self) -> None:
        path = ASSEMBLY / "text_fill_rules" / "OC_CORE_TEXT_FILL_RULES.json"
        payload = read_json(path)
        text = json.dumps(payload, ensure_ascii=False)
        for phrase in ["reader payoff", "claim", "source trace", "raw ledgers", "control-plane", "unsupported overclaims"]:
            self.assertIn(phrase, text)
        self.assertEqual(len(payload["standard_sources"]), 3)

    def test_versioned_instance_assigns_release_number_downstream(self) -> None:
        instance_path = ROOT / "releases" / "oc_core_1_3_3" / "editorial" / "release_assembly" / "OC_CORE_RELEASE_INSTANCE_1.3.3.json"
        payload = read_json(instance_path)
        self.assertEqual(payload["release_identity"]["version"], "1.3.3")
        self.assertTrue(payload["release_identity"]["version_assigned_at_instance_layer"])
        self.assertEqual(
            payload["source_hashes"]["current_release_aggregator_hash"],
            read_json(ASSEMBLY / "current_release_aggregator" / "OC_CORE_CURRENT_RELEASE_AGGREGATOR.json")["artifact_hash"],
        )

    def test_old_versioned_toc_is_not_canonical(self) -> None:
        old_dir = ROOT / "releases" / "oc_core_1_3_3" / "editorial" / "oc_core_1_3_3_release_table_of_content"
        self.assertFalse(old_dir.exists())

    def test_quality_metric_catalog_covers_required_families(self) -> None:
        payload = read_json(ASSEMBLY / "quality_parameterization" / "OC_CORE_QUALITY_METRIC_CATALOG.json")
        families = {metric["family"] for metric in payload["metrics"]}
        for family in [
            "scientific_validity",
            "claim_evidence_trace",
            "formal_proof",
            "empirical_support",
            "didactics",
            "style",
            "structure",
            "figures_tables",
            "bibliography_prior_art",
            "artifact_hygiene",
            "public_surface_safety",
            "reproducibility",
            "reviewer_resilience",
        ]:
            self.assertIn(family, families)
        self.assertGreaterEqual(payload["metric_total"], 15)
        self.assertEqual(len(payload["standard_sources"]), 4)

    def test_l10_quality_projection_matrix_is_complete_and_waived(self) -> None:
        matrix = read_json(ASSEMBLY / "quality_parameterization" / "OC_CORE_L10_QUALITY_PROJECTION_MATRIX.json")
        self.assertEqual(matrix["projection_row_total"], matrix["terminal_l10_node_total"] * matrix["metric_total"])
        self.assertGreater(matrix["applicable_projection_total"], matrix["terminal_l10_node_total"])
        self.assertGreater(matrix["waived_projection_total"], 0)
        required = {
            "coverage.target_obligation",
            "trace.exact_source_binding",
            "claim.boundary_discipline",
            "didactic.reader_task_payoff",
            "structure.sequence_transition",
            "public.no_overclaim_surface",
        }
        by_node: dict[str, set[str]] = {}
        for row in matrix["projection_rows"]:
            if row["applicable"]:
                by_node.setdefault(row["aggregator_node_id"], set()).add(row["metric_id"])
            else:
                self.assertTrue(row["non_applicability_reason"])
        for metrics in by_node.values():
            self.assertTrue(required.issubset(metrics))

    def test_release_quality_audit_does_not_fake_full_coverage(self) -> None:
        audit_path = ROOT / "releases" / "oc_core_1_3_3" / "editorial" / "quality_validation" / "OC_CORE_RELEASE_QUALITY_AUDIT_1.3.3.json"
        audit = read_json(audit_path)
        self.assertEqual(audit["status"], "QUALITY_REPAIR_REQUIRED")
        self.assertEqual(audit["summary"]["not_assessed_l10_total"], 0)
        self.assertGreater(audit["summary"]["scientific_coverage_not_assessed_l10_total"], 0)
        self.assertFalse(audit["summary"]["quality_claim_allowed"])
        self.assertFalse(audit["summary"]["scientific_full_coverage_claim_allowed"])
        self.assertIn("VULN-CERB-001", audit["vulnerability_ids"])

    def test_vulnerability_protocol_and_delta_are_scoped(self) -> None:
        base = ROOT / "releases" / "oc_core_1_3_3" / "editorial" / "quality_validation"
        protocol = read_json(base / "OC_CORE_RELEASE_VULNERABILITY_PROTOCOL_1.3.3.json")
        delta = read_json(base / "OC_CORE_RELEASE_REMEDIATION_DELTA_1.3.3.r001.json")
        self.assertGreaterEqual(protocol["blocking_vulnerability_total"], 1)
        for row in protocol["vulnerabilities"]:
            self.assertTrue(row["vulnerability_id"])
            self.assertTrue(row["severity"])
            self.assertTrue(row["verification_rule"])
            self.assertTrue(row["affected_artifacts"] or row["affected_node_ids"])
        self.assertEqual(delta["parent_hashes"]["vulnerability_protocol_hash"], protocol["artifact_hash"])
        self.assertEqual(delta["remediation_revision"], "r001")
        self.assertTrue(delta["affected_artifacts"] or delta["affected_node_ids"])

    def test_artifact_generation_rules_exist_and_keep_doi_layer_separate(self) -> None:
        base = ASSEMBLY / "artifact_generation"
        profile = read_json(base / "OC_CORE_RELEASE_ARTIFACT_GENERATION_PROFILE.json")
        terminal = read_json(base / "OC_CORE_TERMINAL_TEXT_GENERATION_RULES.json")
        transitions = read_json(base / "OC_CORE_TRANSITION_RULES.json")
        governance = read_json(base / "OC_CORE_RELEASE_ASSEMBLY_MACHINE_GOVERNANCE.json")
        self.assertEqual(profile["concept_doi_policy"]["pdf_doi"], "10.5281/zenodo.17899134")
        self.assertTrue(profile["concept_doi_policy"]["release_record_doi_is_publication_layer_only"])
        for field in ["reader_task", "claim_boundary", "source_refs", "transition_in", "transition_out"]:
            self.assertIn(field, terminal["terminal_contract_fields"])
        for artifact in profile["artifact_profiles"]:
            if artifact["output_kind"] in {"markdown_and_pdf", "markdown"}:
                self.assertTrue(artifact["frontmatter_profile_required"])
                self.assertFalse(artifact["frontmatter_l10_nodes_rendered_as_body_allowed"])
                self.assertEqual(
                    artifact["frontmatter_required_sections"],
                    [
                        "title_page",
                        "dedication_to_maria",
                        "acknowledgements",
                        "abstract",
                        "reader_contract",
                        "table_of_contents",
                    ],
                )
        self.assertIn("definition_model->proof_evidence", transitions["templates"])
        self.assertGreaterEqual(len(governance["cheap_first_ladder"]), 5)
        metric_ids = {row["metric_id"] for row in governance["quantitative_regression_metrics"]}
        self.assertIn("pdf_engine_warning_total", metric_ids)
        self.assertIn("public_surface_leak_total", metric_ids)
        self.assertIn("frontmatter_body_leak_total", metric_ids)
        self.assertTrue(governance["known_error_management"])
        known_error_classes = {row["class"] for row in governance["known_error_management"]}
        self.assertIn("frontmatter_obligation_rendered_as_body_prose", known_error_classes)

    def test_generated_release_package_is_review_space_only(self) -> None:
        base = ROOT / "releases" / "oc_core_1_3_3" / "editorial" / "generated_artifacts"
        assembly = read_json(base / "package_assembly" / "OC_CORE_RELEASE_PACKAGE_ASSEMBLY_1.3.3.json")
        audit = read_json(base / "package_assembly" / "OC_CORE_RELEASE_PACKAGE_ASSEMBLY_AUDIT_1.3.3.json")
        self.assertEqual(audit["status"], "PASS")
        self.assertFalse(assembly["publication_actions_performed"])
        self.assertIsNone(assembly["release_record_doi"])
        self.assertEqual(assembly["concept_doi"], "10.5281/zenodo.17899134")
        self.assertEqual(assembly["summary"]["terminal_node_total"], 656)
        self.assertEqual(assembly["summary"]["blocked_terminal_total"], 0)
        self.assertEqual(assembly["summary"]["transition_record_total"], 655)
        for row in assembly["artifact_rows"]:
            self.assertTrue(row["output_paths"])
            for output in row["output_paths"]:
                self.assertTrue((ROOT / output).exists(), output)

    def test_recovery_structures_filter_source_intake_before_l10c(self) -> None:
        base = ROOT / "releases" / "oc_core_1_3_3" / "editorial" / "recovery"
        source_intake = read_json(base / "OC_CORE_1_3_3_SOURCE_INTAKE_AUDIT.json")
        l10c = read_json(base / "OC_CORE_1_3_3_TOC_L10C_RECOVERED.json")
        self.assertEqual(source_intake["status"], "PASS")
        self.assertEqual(source_intake["summary"]["raw_recovered_candidate_total"], 9607)
        self.assertEqual(source_intake["summary"]["accepted_recovered_candidate_total"], 4730)
        self.assertEqual(source_intake["summary"]["rejected_recovered_candidate_total"], 4877)
        self.assertEqual(l10c["current_l10_node_total"], 656)
        self.assertEqual(l10c["recovered_l10b_node_total"], 4730)
        self.assertEqual(l10c["node_total"], 5386)
        text = json.dumps(l10c, ensure_ascii=False)
        self.assertNotRegex(text, re.compile(r"[\u0400-\u04ff]"))
        self.assertNotIn("Import:", text)

    def test_recovered_release_package_passes_machine_and_regression_gates(self) -> None:
        base = ROOT / "releases" / "oc_core_1_3_3" / "editorial" / "generated_artifacts_recovered" / "recovery_r001"
        assembly = read_json(base / "package_assembly" / "OC_CORE_RELEASE_PACKAGE_ASSEMBLY_1.3.3.json")
        machine = read_json(base / "package_assembly" / "OC_CORE_RELEASE_ASSEMBLY_MACHINE_AUDIT_1.3.3.json")
        comparison = read_json(base / "package_assembly" / "OC_CORE_RELEASE_ASSEMBLY_REVISION_COMPARISON_1.3.3.recovery_r001.json")
        self.assertEqual(assembly["structure_source"], "recovered_l10c")
        self.assertEqual(assembly["assembly_revision"], "recovery_r001")
        self.assertEqual(assembly["summary"]["terminal_node_total"], 5386)
        self.assertEqual(assembly["summary"]["blocked_terminal_total"], 0)
        pages = {row["artifact_type_id"]: (row.get("pdf_build") or {}).get("pages") for row in assembly["artifact_rows"]}
        self.assertEqual(pages["master_monograph"], 1023)
        self.assertGreaterEqual(pages["master_monograph"], 650)
        self.assertEqual(machine["status"], "PASS")
        self.assertEqual(machine["summary"]["finding_total"], 0)
        self.assertEqual(comparison["status"], "PASS")
        self.assertEqual(comparison["summary"]["failure_total"], 0)
        self.assertEqual(comparison["summary"]["warning_total"], 0)
        self.assertFalse(assembly["publication_actions_performed"])

    def test_recovered_quality_audit_keeps_science_gates_honest(self) -> None:
        audit = read_json(
            ROOT
            / "releases"
            / "oc_core_1_3_3"
            / "editorial"
            / "quality_validation"
            / "recovery_r001"
            / "OC_CORE_RELEASE_QUALITY_AUDIT_1.3.3.json"
        )
        self.assertEqual(audit["summary"]["release_package_structure_source"], "recovered_l10c")
        self.assertEqual(audit["summary"]["release_package_assembly_revision"], "recovery_r001")
        self.assertTrue(audit["summary"]["recovered_master_baseline_pass"])
        self.assertEqual(audit["summary"]["recovered_master_pages"], 1023)
        self.assertEqual(audit["summary"]["artifact_failure_total"], 0)
        self.assertIn("VULN-CERB-001", audit["vulnerability_ids"])

    def test_recovery_r002_frontmatter_governance_is_hardened(self) -> None:
        base = ROOT / "releases" / "oc_core_1_3_3" / "editorial" / "generated_artifacts_recovered" / "recovery_r002"
        assembly = read_json(base / "package_assembly" / "OC_CORE_RELEASE_PACKAGE_ASSEMBLY_1.3.3.json")
        machine = read_json(base / "package_assembly" / "OC_CORE_RELEASE_ASSEMBLY_MACHINE_AUDIT_1.3.3.json")
        self.assertEqual(assembly["structure_source"], "recovered_l10c")
        self.assertEqual(assembly["assembly_revision"], "recovery_r002")
        self.assertEqual(assembly["summary"]["terminal_node_total"], 5386)
        self.assertEqual(assembly["summary"]["blocked_terminal_total"], 0)
        self.assertGreater(assembly["summary"]["frontmatter_body_excluded_total"], 0)
        self.assertEqual(machine["status"], "FAIL")
        self.assertEqual(machine["summary"]["form_quality_status"], "FAIL")
        self.assertGreater(machine["summary"]["form_finding_total"], 0)
        finding_kinds = {finding["kind"] for finding in machine["findings"]}
        for kind in [
            "frontmatter_forbidden_heading_prefix",
            "frontmatter_form_technical_toc_entry",
            "pdf_title_page_not_primary",
        ]:
            self.assertIn(kind, finding_kinds)
        pages = {row["artifact_type_id"]: (row.get("pdf_build") or {}).get("pages") for row in assembly["artifact_rows"]}
        self.assertGreaterEqual(pages["master_monograph"], 650)
        self.assertGreater(pages["master_monograph"], 1023)
        self.assertFalse(assembly["publication_actions_performed"])
        terminal = read_json(base / "terminal_text" / "OC_CORE_TERMINAL_TEXT_CONTRACTS_1.3.3.json")
        frontmatter_rows = [row for row in terminal["terminal_contracts"] if row.get("frontmatter_document_layer")]
        self.assertGreater(len(frontmatter_rows), 0)
        self.assertEqual(terminal["document_frontmatter_terminal_total"], len(frontmatter_rows))
        for row in frontmatter_rows:
            self.assertEqual(row["build_state"], "DOCUMENT_FRONTMATTER_RENDERED")
            self.assertEqual(row["generated_text"], "")

    def test_recovery_r002_reader_sources_have_real_frontmatter_not_body_frontmatter(self) -> None:
        base = ROOT / "releases" / "oc_core_1_3_3" / "editorial" / "generated_artifacts_recovered" / "recovery_r002" / "sources"
        required = [
            "## Publication Identity",
            "## Dedication",
            "Dedicated to my dear wife Maria, without whom this work would have been impossible.",
            "## Acknowledgements",
            "G. V. Apostolov",
            "Eduard Fadeev",
            "Gennady Alekseevich Nosov",
            "Sergey Shpadyrev",
            "Stanislav Tsukrov",
            "## Abstract",
            "## Reader Contract",
            "## Table of Contents",
            "# Body",
        ]
        forbidden = [
            "Define Title Page",
            "Define Dedication",
            "Define Table of Contents",
            "not a GitHub or Zenodo publication action",
            "review-space artifact is assembled",
        ]
        for path in sorted(base.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            if path.name == "release_notes_changelog_1.3.3.md":
                continue
            frontmatter_end = text.index("# Body")
            for needle in required:
                self.assertIn(needle, text, path.name)
            self.assertLess(text.index("## Dedication"), frontmatter_end)
            self.assertLess(text.index("## Acknowledgements"), frontmatter_end)
            self.assertLess(text.index("## Abstract"), frontmatter_end)
            self.assertLess(text.index("## Reader Contract"), frontmatter_end)
            self.assertLess(text.index("## Table of Contents"), frontmatter_end)
            for needle in forbidden:
                self.assertNotIn(needle, text, path.name)

    def test_recovery_r002_quality_audit_uses_recovered_package(self) -> None:
        audit = read_json(
            ROOT
            / "releases"
            / "oc_core_1_3_3"
            / "editorial"
            / "quality_validation"
            / "recovery_r002"
            / "OC_CORE_RELEASE_QUALITY_AUDIT_1.3.3.json"
        )
        self.assertEqual(audit["summary"]["release_package_structure_source"], "recovered_l10c")
        self.assertEqual(audit["summary"]["release_package_assembly_revision"], "recovery_r002")
        self.assertTrue(audit["summary"]["recovered_master_baseline_pass"])
        self.assertGreaterEqual(audit["summary"]["recovered_master_pages"], 650)
        self.assertGreater(audit["summary"]["artifact_failure_total"], 0)
        self.assertEqual(audit["summary"]["form_quality_status"], "FAIL")
        self.assertGreater(audit["summary"]["machine_form_gate_finding_total"], 0)
        self.assertIn("VULN-MA-001", audit["vulnerability_ids"])

    def test_recovery_r003_publication_gates_reject_bad_package(self) -> None:
        base = ROOT / "releases" / "oc_core_1_3_3" / "editorial" / "generated_artifacts_recovered" / "recovery_r003"
        assembly = read_json(base / "package_assembly" / "OC_CORE_RELEASE_PACKAGE_ASSEMBLY_1.3.3.json")
        machine = read_json(base / "package_assembly" / "OC_CORE_RELEASE_ASSEMBLY_MACHINE_AUDIT_1.3.3.json")
        self.assertEqual(assembly["structure_source"], "recovered_l10c")
        self.assertEqual(assembly["assembly_revision"], "recovery_r003")
        self.assertEqual(assembly["summary"]["terminal_node_total"], 5386)
        self.assertEqual(assembly["summary"]["blocked_terminal_total"], 0)
        self.assertGreater(assembly["summary"]["frontmatter_body_excluded_total"], 0)
        self.assertEqual(machine["status"], "FAIL")
        for key in [
            "title_page_publication_status",
            "acknowledgements_status",
            "abstract_depth_status",
            "release_delta_status",
            "reader_contract_status",
            "toc_hierarchy_status",
            "content_richness_status",
            "technical_prose_leak_status",
            "form_quality_status",
        ]:
            self.assertEqual(machine["summary"][key], "FAIL", key)
        finding_kinds = {finding["kind"] for finding in machine["findings"]}
        for kind in [
            "publication_reader_internal_instrument_leak",
            "publication_technical_prose_leak",
            "publication_release_delta_missing",
            "publication_body_source_not_corpus",
            "publication_master_missing_richness_anchor",
            "pdf_toc_page_cap_violation",
        ]:
            self.assertIn(kind, finding_kinds)
        pages = {row["artifact_type_id"]: (row.get("pdf_build") or {}).get("pages") for row in assembly["artifact_rows"]}
        self.assertGreaterEqual(pages["master_monograph"], 650)
        self.assertGreater(pages["master_monograph"], 1023)
        self.assertFalse(assembly["publication_actions_performed"])

    def test_recovery_r003_reader_sources_preserve_failure_evidence(self) -> None:
        base = ROOT / "releases" / "oc_core_1_3_3" / "editorial" / "generated_artifacts_recovered" / "recovery_r003" / "sources"
        master = (base / "master_monograph_1.3.3.md").read_text(encoding="utf-8")
        self.assertIn("Logion is the research-instrument", master)
        self.assertIn("Reader Contract is introduced here as a reader-facing obligation", master)
        self.assertNotIn("# Version 1.3.3 Release Delta", master)
        self.assertNotIn("release_machine.science_monolith.integrated_tex_corpus", master)

    def test_recovery_r004_publication_package_passes_document_machine(self) -> None:
        base = ROOT / "releases" / "oc_core_1_3_3" / "editorial" / "generated_artifacts_recovered" / "recovery_r004"
        assembly = read_json(base / "package_assembly" / "OC_CORE_RELEASE_PACKAGE_ASSEMBLY_1.3.3.json")
        machine = read_json(base / "package_assembly" / "OC_CORE_RELEASE_ASSEMBLY_MACHINE_AUDIT_1.3.3.json")
        comparison = read_json(base / "package_assembly" / "OC_CORE_RELEASE_ASSEMBLY_REVISION_COMPARISON_1.3.3.recovery_r004.json")
        self.assertEqual(assembly["structure_source"], "recovered_l10c")
        self.assertEqual(assembly["assembly_revision"], "recovery_r004")
        self.assertEqual(machine["status"], "PASS")
        self.assertEqual(machine["summary"]["finding_total"], 0)
        for key in [
            "title_page_publication_status",
            "acknowledgements_status",
            "abstract_depth_status",
            "release_delta_status",
            "reader_contract_status",
            "toc_hierarchy_status",
            "content_richness_status",
            "technical_prose_leak_status",
            "form_quality_status",
        ]:
            self.assertEqual(machine["summary"][key], "PASS", key)
            self.assertEqual(comparison["summary"][key], "PASS", key)
        self.assertEqual(comparison["status"], "PASS")
        self.assertEqual(comparison["summary"]["failure_total"], 0)
        rows = {row["artifact_type_id"]: row for row in assembly["artifact_rows"]}
        master = rows["master_monograph"]
        self.assertEqual(master["source_format"], "latex")
        self.assertEqual(master["document_body_source"], "release_machine.science_monolith.integrated_tex_corpus")
        self.assertGreaterEqual((master.get("pdf_build") or {}).get("pages"), 650)
        self.assertGreaterEqual(master["figure_total"], 30)
        self.assertGreaterEqual(master["table_total"], 4)
        self.assertGreaterEqual(master["formula_marker_total"], 500)
        self.assertLessEqual(master["toc_page_total"], 20)
        for artifact_id in ["release_guide", "journal_core_article", "methods_repro_companion", "reviewer_attack_response_map"]:
            self.assertEqual(rows[artifact_id]["document_body_source"], "curated_public_payload_markdown")
            self.assertLessEqual(rows[artifact_id]["toc_page_total"], 4)
        self.assertFalse(assembly["publication_actions_performed"])

    def test_recovery_r004_frontmatter_and_reader_pdfs_are_publication_surfaces(self) -> None:
        base = ROOT / "releases" / "oc_core_1_3_3" / "editorial" / "generated_artifacts_recovered" / "recovery_r004"
        guide = (base / "sources" / "release_guide_1.3.3.md").read_text(encoding="utf-8")
        for needle in [
            "Dedicated to my dear wife Maria, without whom this work would have been impossible.",
            "# Acknowledgements {.unnumbered}",
            "reviewers and critics whose questions",
            "# Abstract {.unnumbered}",
            "# Version 1.3.3 Release Delta {.unnumbered}",
            "# Reader Contract {.unnumbered}",
            "Dear reader,",
            "\\tableofcontents",
        ]:
            self.assertIn(needle, guide)
        self.assertLess(guide.index("# Acknowledgements"), guide.index("# Abstract"))
        self.assertLess(guide.index("# Abstract"), guide.index("# Version 1.3.3 Release Delta"))
        self.assertLess(guide.index("# Version 1.3.3 Release Delta"), guide.index("# Reader Contract"))
        forbidden = re.compile(r"\b(Logion|ESTRA|definition_model|generated terminal prose|Block\s+\d+)\b", re.I)
        for path in sorted((base / "sources").glob("*.md")):
            if path.name == "release_notes_changelog_1.3.3.md":
                continue
            self.assertNotRegex(path.read_text(encoding="utf-8"), forbidden, path.name)

    def test_recovery_r004_quality_audit_form_gates_pass_with_known_cerberus_blocker(self) -> None:
        audit = read_json(
            ROOT
            / "releases"
            / "oc_core_1_3_3"
            / "editorial"
            / "quality_validation"
            / "recovery_r004"
            / "OC_CORE_RELEASE_QUALITY_AUDIT_1.3.3.json"
        )
        self.assertEqual(audit["summary"]["release_package_structure_source"], "recovered_l10c")
        self.assertEqual(audit["summary"]["release_package_assembly_revision"], "recovery_r004")
        self.assertTrue(audit["summary"]["recovered_master_baseline_pass"])
        self.assertGreaterEqual(audit["summary"]["recovered_master_pages"], 650)
        self.assertEqual(audit["summary"]["artifact_failure_total"], 0)
        self.assertEqual(audit["summary"]["machine_audit_status"], "PASS")
        self.assertEqual(audit["summary"]["form_quality_status"], "PASS")
        self.assertEqual(audit["summary"]["machine_form_gate_finding_total"], 0)
        self.assertIn("VULN-CERB-001", audit["vulnerability_ids"])
        self.assertNotIn("VULN-MA-001", audit["vulnerability_ids"])

    def test_recovery_r004_fails_recovery_r005_machine_when_reaudited(self) -> None:
        tools_dir = ROOT / "tools"
        if str(tools_dir) not in sys.path:
            sys.path.insert(0, str(tools_dir))
        from audit_oc_core_release_assembly_machine import build_audit

        audit = build_audit("oc_core_1_3_3", "recovery_r004")
        self.assertEqual(audit["status"], "FAIL")
        for key in [
            "frontmatter_identity_status",
            "reader_routes_status",
            "toc_visual_hierarchy_status",
            "layout_quality_status",
            "inline_figure_distribution_status",
            "caption_quality_status",
            "bibliography_depth_status",
            "reader_facing_reference_status",
            "didactic_density_status",
            "form_quality_status",
        ]:
            self.assertEqual(audit["summary"][key], "FAIL", key)
        finding_kinds = {finding["kind"] for finding in audit["findings"]}
        for kind in [
            "publication_frontmatter_identity_clutter",
            "publication_title_page_date_stale",
            "publication_reader_routes_missing_group",
            "publication_toc_visual_hierarchy_missing",
            "publication_layout_standard_missing",
            "publication_inline_figure_distribution_too_low",
            "publication_bibliography_verified_shortfall",
        ]:
            self.assertIn(kind, finding_kinds)

    def test_recovery_r005_publication_package_passes_document_machine(self) -> None:
        base = ROOT / "releases" / "oc_core_1_3_3" / "editorial" / "generated_artifacts_recovered" / "recovery_r005"
        assembly = read_json(base / "package_assembly" / "OC_CORE_RELEASE_PACKAGE_ASSEMBLY_1.3.3.json")
        machine = read_json(base / "package_assembly" / "OC_CORE_RELEASE_ASSEMBLY_MACHINE_AUDIT_1.3.3.json")
        comparison = read_json(base / "package_assembly" / "OC_CORE_RELEASE_ASSEMBLY_REVISION_COMPARISON_1.3.3.recovery_r005.json")
        quality = read_json(
            ROOT
            / "releases"
            / "oc_core_1_3_3"
            / "editorial"
            / "quality_validation"
            / "recovery_r005"
            / "OC_CORE_RELEASE_QUALITY_AUDIT_1.3.3.json"
        )
        self.assertEqual(assembly["structure_source"], "recovered_l10c")
        self.assertEqual(assembly["assembly_revision"], "recovery_r005")
        self.assertEqual(machine["status"], "PASS")
        self.assertEqual(machine["summary"]["finding_total"], 0)
        self.assertEqual(comparison["status"], "PASS")
        self.assertEqual(comparison["summary"]["failure_total"], 0)
        self.assertEqual(quality["summary"]["artifact_failure_total"], 0)
        self.assertEqual(quality["summary"]["machine_audit_status"], "PASS")
        for key in R005_FORM_STATUS_KEYS:
            self.assertEqual(machine["summary"][key], "PASS", key)
            self.assertEqual(comparison["summary"][key], "PASS", key)
            self.assertEqual(quality["summary"][key], "PASS", key)

        rows = {row["artifact_type_id"]: row for row in assembly["artifact_rows"]}
        master = rows["master_monograph"]
        self.assertEqual(master["source_format"], "latex")
        self.assertEqual(master["document_body_source"], "release_machine.science_monolith.integrated_tex_corpus")
        self.assertEqual(master["document_structure_source"], "science_monolith_canonical_tex_hierarchy")
        self.assertGreaterEqual((master.get("pdf_build") or {}).get("pages"), 650)
        self.assertLessEqual(master["toc_page_total"], 20)
        self.assertGreaterEqual(master["inline_figure_total"], 36)
        self.assertEqual(master["figure_atlas_included"], 0)
        self.assertGreaterEqual(master["figure_total"], 36)
        self.assertGreaterEqual(master["table_total"], 4)
        self.assertGreaterEqual(master["formula_marker_total"], 500)
        self.assertGreaterEqual(master["bibliography_entry_total"], 120)
        self.assertGreaterEqual(master["verified_bibliography_entry_total"], 120)
        self.assertGreaterEqual(master["appendix_named_total"], 10)
        self.assertEqual(master["appendix_letter_only_total"], 0)
        for artifact_id in ["release_guide", "journal_core_article", "methods_repro_companion", "reviewer_attack_response_map"]:
            self.assertEqual(rows[artifact_id]["document_body_source"], "curated_public_payload_markdown")
            self.assertEqual(rows[artifact_id]["document_structure_source"], "curated_public_payload_hierarchy")
            self.assertLessEqual(rows[artifact_id]["toc_page_total"], 4)
        self.assertFalse(assembly["publication_actions_performed"])

    def test_recovery_r005_frontmatter_identity_reader_routes_and_backmatter(self) -> None:
        base = ROOT / "releases" / "oc_core_1_3_3" / "editorial" / "generated_artifacts_recovered" / "recovery_r005"
        guide = (base / "sources" / "release_guide_1.3.3.md").read_text(encoding="utf-8")
        frontmatter = (
            base / "b" / "base_source" / "content" / "frontmatter_oc_core_1_3_master.tex"
        ).read_text(encoding="utf-8")
        entrypoint = (base / "b" / "base_source" / "oc_core_1_3_master_monograph.tex").read_text(encoding="utf-8")
        for text in [guide, frontmatter]:
            for needle in [
                "Dedicated to my dear wife Maria, without whom this work would have been impossible.",
                "3 May 2026",
                "Concept DOI",
                "Reader Routes",
                "Scientific reviewers and formal critics",
                "Systems theorists, philosophers, and interested theoretical readers",
                "AI builders, engineers, architects, and applied researchers",
                "CIO, CEO, enterprise architects, and strategy readers",
                "Reproducibility auditors, evidence reviewers, and benchmark readers",
            ]:
                self.assertIn(needle, text)
            for forbidden in ["Version DOI", "Zenodo Record", "GitHub Release", "Logion", "ESTRA"]:
                self.assertNotIn(forbidden, text)
        self.assertLess(guide.index("# Acknowledgements"), guide.index("# Abstract"))
        self.assertLess(guide.index("# Abstract"), guide.index("# Version 1.3.3 Release Delta"))
        self.assertLess(guide.index("# Version 1.3.3 Release Delta"), guide.index("# Reader Routes"))
        self.assertLess(guide.index("\\tableofcontents"), guide.index("# Reading Map"))
        self.assertIn("```{=latex}", guide)
        self.assertIn("% R005_TOC_VISUAL_HIERARCHY", guide)
        self.assertIn("% R005_LAYOUT_STANDARD", (base / "b" / "base_source" / "preamble.tex").read_text(encoding="utf-8"))
        self.assertIn("\\section*{Keywords and Citation Route}", entrypoint)
        self.assertIn("github.com/alexanderyashin/ontology-of-continua-core-main", entrypoint)
        self.assertNotIn("Concept DOI: \\href", entrypoint)

    def test_recovery_r005_fails_recovery_r006_machine_when_reaudited(self) -> None:
        tools_dir = ROOT / "tools"
        if str(tools_dir) not in sys.path:
            sys.path.insert(0, str(tools_dir))
        from audit_oc_core_release_assembly_machine import build_audit

        audit = build_audit("oc_core_1_3_3", "recovery_r005")
        self.assertEqual(audit["status"], "FAIL")
        for key in [
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
            "form_quality_status",
        ]:
            self.assertEqual(audit["summary"][key], "FAIL", key)
        finding_kinds = {finding["kind"] for finding in audit["findings"]}
        for kind in [
            "publication_visible_recovery_revision",
            "publication_title_page_date_stale",
            "publication_release_policy_too_short",
            "publication_reader_routes_tone_imperative",
            "publication_reader_orientation_duplicate",
            "publication_internal_block_metadata_leak",
            "publication_figure_table_list_visible",
            "publication_didactic_spine_order_violation",
            "publication_motivation_too_short",
            "publication_k_primer_missing",
            "publication_duplicate_structure_section",
        ]:
            self.assertIn(kind, finding_kinds)

    def test_recovery_r006_publication_package_passes_didactic_machine(self) -> None:
        base = ROOT / "releases" / "oc_core_1_3_3" / "editorial" / "generated_artifacts_recovered" / "recovery_r006"
        assembly = read_json(base / "package_assembly" / "OC_CORE_RELEASE_PACKAGE_ASSEMBLY_1.3.3.json")
        machine = read_json(base / "package_assembly" / "OC_CORE_RELEASE_ASSEMBLY_MACHINE_AUDIT_1.3.3.json")
        comparison = read_json(base / "package_assembly" / "OC_CORE_RELEASE_ASSEMBLY_REVISION_COMPARISON_1.3.3.recovery_r006.json")
        quality = read_json(
            ROOT
            / "releases"
            / "oc_core_1_3_3"
            / "editorial"
            / "quality_validation"
            / "recovery_r006"
            / "OC_CORE_RELEASE_QUALITY_AUDIT_1.3.3.json"
        )
        self.assertEqual(assembly["structure_source"], "recovered_l10c")
        self.assertEqual(assembly["assembly_revision"], "recovery_r006")
        self.assertEqual(machine["status"], "PASS")
        self.assertEqual(machine["summary"]["finding_total"], 0)
        self.assertEqual(comparison["status"], "PASS")
        self.assertEqual(comparison["summary"]["failure_total"], 0)
        self.assertEqual(comparison["summary"]["warning_total"], 0)
        self.assertEqual(quality["summary"]["artifact_failure_total"], 0)
        self.assertEqual(quality["summary"]["machine_audit_status"], "PASS")
        self.assertEqual(quality["summary"]["form_quality_status"], "PASS")
        self.assertIn("VULN-CERB-001", quality["vulnerability_ids"])
        for key in R006_FORM_STATUS_KEYS:
            self.assertEqual(machine["summary"][key], "PASS", key)
            self.assertEqual(comparison["summary"][key], "PASS", key)
            self.assertEqual(quality["summary"][key], "PASS", key)

        rows = {row["artifact_type_id"]: row for row in assembly["artifact_rows"]}
        master = rows["master_monograph"]
        self.assertEqual(master["source_format"], "latex")
        self.assertEqual(master["document_body_source"], "release_machine.science_monolith.integrated_tex_corpus")
        self.assertEqual(master["document_structure_source"], "science_monolith_canonical_tex_hierarchy")
        self.assertGreaterEqual((master.get("pdf_build") or {}).get("pages"), 650)
        self.assertLessEqual(master["toc_page_total"], 20)
        self.assertGreaterEqual(master["inline_figure_total"], 36)
        self.assertGreaterEqual(master["figure_total"], 36)
        self.assertEqual(master["figure_atlas_included"], 0)
        self.assertGreaterEqual(master["table_total"], 4)
        self.assertGreaterEqual(master["formula_marker_total"], 500)
        self.assertGreaterEqual(master["bibliography_entry_total"], 120)
        self.assertGreaterEqual(master["verified_bibliography_entry_total"], 120)
        self.assertGreaterEqual(master["appendix_named_total"], 10)
        self.assertEqual(master["appendix_letter_only_total"], 0)
        for artifact_id in ["release_guide", "journal_core_article", "methods_repro_companion", "reviewer_attack_response_map"]:
            self.assertEqual(rows[artifact_id]["document_body_source"], "curated_public_payload_markdown")
            self.assertEqual(rows[artifact_id]["document_structure_source"], "curated_public_payload_hierarchy")
            self.assertLessEqual(rows[artifact_id]["toc_page_total"], 4)
        self.assertFalse(assembly["publication_actions_performed"])

    def test_recovery_r006_master_frontmatter_and_spine_are_publication_surfaces(self) -> None:
        base = ROOT / "releases" / "oc_core_1_3_3" / "editorial" / "generated_artifacts_recovered" / "recovery_r006"
        guide = (base / "sources" / "release_guide_1.3.3.md").read_text(encoding="utf-8")
        source_base = base / "b" / "base_source"
        frontmatter = (source_base / "content" / "frontmatter_oc_core_1_3_master.tex").read_text(encoding="utf-8")
        entrypoint = (source_base / "oc_core_1_3_master_monograph.tex").read_text(encoding="utf-8")
        preamble = (source_base / "preamble.tex").read_text(encoding="utf-8")
        part_i = (source_base / "content" / "r006" / "01_why_continuum_ontology.tex").read_text(encoding="utf-8")
        part_ii = (source_base / "content" / "r006" / "02_first_concepts_and_k_primer.tex").read_text(encoding="utf-8")
        auto_core = (source_base / "content" / "_auto_core_inputs_1_3_3_integrated.tex").read_text(encoding="utf-8")

        for text in [guide, frontmatter]:
            for needle in [
                "Dedicated to my dear wife Maria, without whom this work would have been impossible.",
                "4 May 2026",
                "Concept DOI",
                "Reader Routes",
                "Scientific reviewers and formal critics",
                "Systems theorists, philosophers, and interested theoretical readers",
            ]:
                self.assertIn(needle, text)
            for needle in [
                "AI builders",
                "engineers",
                "CIO",
                "CEO",
                "enterprise architects",
                "Reproducibility auditors",
                "benchmark readers",
            ]:
                self.assertRegex(text, re.compile(re.escape(needle), re.I))
            for forbidden in ["recovery_r006", "Version DOI", "Zenodo Record", "GitHub Release", "Logion", "ESTRA"]:
                self.assertNotIn(forbidden, text)

        self.assertLess(guide.index("# Acknowledgements"), guide.index("# Abstract"))
        self.assertLess(guide.index("# Abstract"), guide.index("# Version 1.3.3 Release Delta"))
        self.assertLess(guide.index("# Version 1.3.3 Release Delta"), guide.index("# Reader Routes"))
        self.assertLess(guide.index("# Reader Routes"), guide.index("\\tableofcontents"))
        self.assertIn("% R006_TOC_VISUAL_HIERARCHY", guide)
        self.assertIn("% R006_LAYOUT_STANDARD", preamble)

        forbidden_surface = [
            "recovery_r006",
            "\\listoffigures",
            "\\listoftables",
            "\\ocvolumeblock",
            "Reader Orientation",
            "Reader Routes and Scientific Route",
            "Complete Scientific Argument",
            "Scientific Closure",
            "This block presents",
            "content/17_oc_core_1_3_reader_guide",
            "content/01_intro.tex",
            "content/02_background.tex",
            "unrestricted unrestricted",
        ]
        joined_surface = "\n".join([entrypoint, frontmatter, part_i, part_ii, auto_core])
        for forbidden in forbidden_surface:
            self.assertNotIn(forbidden, joined_surface)

        self.assertLess(entrypoint.index("\\input{content/frontmatter_oc_core_1_3_master.tex}"), entrypoint.index("\\tableofcontents"))
        self.assertLess(entrypoint.index("\\tableofcontents"), entrypoint.index("\\input{content/r006/01_why_continuum_ontology.tex}"))
        self.assertLess(entrypoint.index("\\input{content/r006/01_why_continuum_ontology.tex}"), entrypoint.index("\\input{content/r006/02_first_concepts_and_k_primer.tex}"))
        self.assertLess(entrypoint.index("\\input{content/r006/02_first_concepts_and_k_primer.tex}"), entrypoint.index("\\input{content/_auto_core_inputs_1_3_3_integrated.tex}"))
        self.assertLess(entrypoint.index("\\input{content/_auto_core_inputs_1_3_3_integrated.tex}"), entrypoint.index("Part VI -- Limits, Prior Art, and Closure"))
        self.assertLess(entrypoint.index("Part VI -- Limits, Prior Art, and Closure"), entrypoint.index("Appendices -- Evidence, Proof, and Reference Support"))
        self.assertLess(entrypoint.index("Appendices -- Evidence, Proof, and Reference Support"), entrypoint.index("Keywords and Citation Route"))
        self.assertLess(auto_core.index("Part III -- Formal Core"), auto_core.index("Part IV -- Evidence, Proof, and Falsifiability"))
        self.assertLess(auto_core.index("Part IV -- Evidence, Proof, and Falsifiability"), auto_core.index("Part V -- Domain and Practical Routes"))

        motivation = re.search(
            r"\\section\{Motivation: Why a Shared Systems Language Is Needed\}(.*?)\\section\{Scope of OC Core 1\.3\.3\}",
            part_i,
            re.S,
        )
        self.assertIsNotNone(motivation)
        self.assertGreaterEqual(len(re.findall(r"[A-Za-z][A-Za-z'-]*", motivation.group(1))), 700)
        for needle in [
            "agentic AI",
            "fragmentation",
            "silo pattern",
            "compression without loss of meaning",
            "shared systems language",
        ]:
            self.assertRegex(part_i, re.compile(re.escape(needle), re.I))
        self.assertIn("\\begin{figure}", part_i)
        self.assertIn("fig:r006-continuum-template", part_i)
        part_ii_norm = re.sub(r"\s+", " ", part_ii)
        for needle in [
            "Continua are composed of continua",
            "Kontinuum",
            "enterprise",
        ]:
            self.assertRegex(part_ii_norm, re.compile(re.escape(needle), re.I))
        for needle in [
            "K=\\bigl(\\Omega,\\partial\\Omega,A,\\Theta,P,J,C,k,M\\bigr)",
            "tab:r006-k-primer",
            "fig:r006-nested-k-levels",
        ]:
            self.assertIn(needle, part_ii)

    def test_recovery_r006_fails_recovery_r007_machine_when_reaudited(self) -> None:
        tools_dir = ROOT / "tools"
        if str(tools_dir) not in sys.path:
            sys.path.insert(0, str(tools_dir))
        from audit_oc_core_release_assembly_machine import build_audit

        audit = build_audit("oc_core_1_3_3", "recovery_r006")
        self.assertEqual(audit["status"], "FAIL")
        for key in [
            "publication_translation_status",
            "instruction_prose_leak_status",
            "page17_internal_leak_status",
            "k_hierarchy_figure_status",
            "all_reader_pdf_translation_status",
            "governed_ollama_status",
            "v_model_audit_status",
            "form_quality_status",
        ]:
            self.assertEqual(audit["summary"][key], "FAIL", key)
        finding_kinds = {finding["kind"] for finding in audit["findings"]}
        for kind in [
            "publication_translation_missing",
            "publication_all_reader_pdf_translation_missing",
            "publication_instruction_prose_leak",
            "publication_page17_internal_leak",
            "publication_k_hierarchy_figure_incomplete",
            "publication_ollama_governance_trace_missing",
            "publication_v_model_trace_missing",
        ]:
            self.assertIn(kind, finding_kinds)

    def test_recovery_r007_governed_publication_translator_package_passes(self) -> None:
        base = ROOT / "releases" / "oc_core_1_3_3" / "editorial" / "generated_artifacts_recovered" / "recovery_r007"
        assembly = read_json(base / "package_assembly" / "OC_CORE_RELEASE_PACKAGE_ASSEMBLY_1.3.3.json")
        machine = read_json(base / "package_assembly" / "OC_CORE_RELEASE_ASSEMBLY_MACHINE_AUDIT_1.3.3.json")
        comparison = read_json(base / "package_assembly" / "OC_CORE_RELEASE_ASSEMBLY_REVISION_COMPARISON_1.3.3.recovery_r007.json")
        quality = read_json(
            ROOT
            / "releases"
            / "oc_core_1_3_3"
            / "editorial"
            / "quality_validation"
            / "recovery_r007"
            / "OC_CORE_RELEASE_QUALITY_AUDIT_1.3.3.json"
        )

        self.assertEqual(assembly["assembly_revision"], "recovery_r007")
        self.assertEqual(assembly["governed_ollama_trace"]["status"], "OLLAMA_SKIPPED_BY_GOVERNANCE")
        self.assertEqual(assembly["governed_ollama_trace"]["ollama_invocation_total"], 0)
        self.assertEqual(assembly["governed_ollama_trace"]["unmanaged_ollama_call_total"], 0)
        self.assertEqual(assembly["governed_ollama_trace"]["max_workers"], 1)
        self.assertEqual(assembly["publication_translation_pipeline"]["status"], "PUBLICATION_TRANSLATOR_R007")
        self.assertEqual(machine["status"], "PASS")
        self.assertEqual(machine["summary"]["finding_total"], 0)
        self.assertEqual(comparison["status"], "PASS")
        self.assertEqual(comparison["summary"]["failure_total"], 0)
        self.assertEqual(comparison["summary"]["warning_total"], 0)
        self.assertGreaterEqual(comparison["summary"]["explained_page_reduction_total"], 4)
        self.assertEqual(quality["summary"]["artifact_failure_total"], 0)
        self.assertEqual(quality["summary"]["machine_audit_status"], "PASS")
        self.assertEqual(quality["summary"]["form_quality_status"], "PASS")
        for key in R007_FORM_STATUS_KEYS:
            self.assertEqual(machine["summary"][key], "PASS", key)
            self.assertEqual(comparison["summary"][key], "PASS", key)
            self.assertEqual(quality["summary"][key], "PASS", key)

        rows = {row["artifact_type_id"]: row for row in assembly["artifact_rows"]}
        master = rows["master_monograph"]
        self.assertEqual(master["public_translation_source"], "science_monolith_publication_translator_r007")
        self.assertGreaterEqual((master.get("pdf_build") or {}).get("pages"), 650)
        self.assertLessEqual(master["toc_page_total"], 20)
        self.assertGreaterEqual(master["inline_figure_total"], 36)
        for artifact_id in ["release_guide", "journal_core_article", "methods_repro_companion", "reviewer_attack_response_map"]:
            row = rows[artifact_id]
            self.assertEqual(row["public_translation_source"], "deterministic_publication_translator_r007")
            self.assertEqual(row["public_translation_status"], "PUBLICATION_TRANSLATOR_R007")
            self.assertEqual(row["governed_ollama_status"], "OLLAMA_SKIPPED_BY_GOVERNANCE")
            self.assertEqual(row["v_model_lowest_checked_level"], "L10")

    def test_recovery_r007_public_surfaces_are_translation_not_instruction_packets(self) -> None:
        base = ROOT / "releases" / "oc_core_1_3_3" / "editorial" / "generated_artifacts_recovered" / "recovery_r007"
        source_base = base / "b" / "base_source"
        entrypoint = (source_base / "oc_core_1_3_master_monograph.tex").read_text(encoding="utf-8")
        preamble = (source_base / "preamble.tex").read_text(encoding="utf-8")
        part_i = (source_base / "content" / "r007" / "01_why_continuum_ontology.tex").read_text(encoding="utf-8")
        part_ii = (source_base / "content" / "r007" / "02_first_concepts_and_k_primer.tex").read_text(encoding="utf-8")
        auto_core = (source_base / "content" / "_auto_core_inputs_1_3_3_integrated.tex").read_text(encoding="utf-8")
        guide = (base / "sources" / "release_guide_1.3.3.md").read_text(encoding="utf-8")

        self.assertIn("% R007_TOC_VISUAL_HIERARCHY", entrypoint)
        self.assertIn("% R007_LAYOUT_STANDARD", preamble)
        self.assertIn("PUBLICATION_TRANSLATOR_R007", guide)
        self.assertIn("fig:r007-continuum-demonstrator", part_i)
        self.assertIn("fig:r007-k0-k12-hierarchy", part_ii)
        self.assertIn("R007_K_LEVELS_PRESENT: K0 K1 K2 K3 K4 K5 K6 K7 K8 K9 K10 K11 K12", part_ii)
        for needle in ["upward composition", "downward constraint", "falsifier", "formal tuple"]:
            self.assertRegex(part_i + "\n" + part_ii, re.compile(re.escape(needle), re.I))

        joined_public_source = "\n".join([entrypoint, part_i, part_ii, auto_core, guide])
        for forbidden in [
            "Scientific Reading Protocol",
            "Evidence Coverage Map",
            "Figure Route and Design Logic",
            "Model integration payoff",
            "Proof integration payoff",
            "Empirical integration payoff",
            "machine register",
            "current maturity vector",
            "This section is included so",
            "Audience.",
            "Purpose.",
            "Construction.",
            "Didactic rule.",
            "recovery_r007",
            "Version DOI",
            "Zenodo Record",
            "GitHub Release",
            "Logion",
            "ESTRA",
        ]:
            self.assertNotIn(forbidden, joined_public_source)

    def test_logion_llm_service_cadence_and_cooldown_protocol(self) -> None:
        service_path = (
            ROOT.parent.parent.parent
            / "estra-private-work"
            / "logion"
            / "k3"
            / "execution"
            / "scripts"
            / "logion_llm"
            / "logion_llm_service_v1.py"
        )
        spec = importlib.util.spec_from_file_location("logion_llm_service_v1", service_path)
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module)
        batch = {
            "schema_id": "LOGION_LLM_SERVICE_BATCH_REQUEST_v1",
            "caller_id": "unit_test",
            "batch_id": "cadence",
            "run_mode": "safe_exhaustive",
            "requests": [
                {"task_id": f"l10_{idx}", "level": "L10", "operation_type": "micro_check", "prompt": "ok", "allow_7b": True, "use_cache": False}
                for idx in range(4)
            ],
        }
        host = {"status": "GREEN", "summary": {"gpu_temp_c": 50.0}, "evaluation": {"status": "GREEN", "gpu_temp_c": 50.0}}
        bridge = {"host_gpu_allowed": True, "effective_max_workers": 1, "host_safety_next_action": "RUN_WITH_REQUESTED_BOUNDS", "llm_budget_remaining": 10}
        response = module.service_run(batch, write=False, allow_provider=False, host_state_override=host, bridge_state_override=bridge)
        self.assertEqual(response["status"], "PASS")
        self.assertEqual(response["summary"]["model_sequence"], ["qwen2.5-coder:7b", "qwen2.5-coder:3b", "qwen2.5-coder:3b", "qwen2.5-coder:7b"])
        self.assertIn("thermal_debt_cheap_model_2", response["summary"]["cadence_sequence"])
        self.assertIn("thermal_debt_cheap_model_1", response["summary"]["cadence_sequence"])
        self.assertEqual(response["summary"]["unmanaged_ollama_call_total"], 0)

        queue = {
            "schema_id": "LOGION_LLM_SERVICE_QUEUE_REQUEST_v1",
            "caller_id": "unit_test",
            "queue_id": "until_done_cadence",
            "run_mode": "safe_exhaustive_until_done",
            "requests": [
                {"task_id": f"l10_{idx}", "level": "L10", "operation_type": "micro_check", "prompt": "ok", "allow_7b": True, "use_cache": False, "sequence_index": idx}
                for idx in range(4)
            ],
        }
        queue_response = module.service_queue_run(queue, write=False, until_done=True, allow_provider=False, host_state_override=host, bridge_state_override=bridge)
        self.assertEqual(queue_response["queue_status"], "DONE")
        self.assertEqual(queue_response["summary"]["model_sequence"], ["qwen2.5-coder:7b", "qwen2.5-coder:3b", "qwen2.5-coder:3b", "qwen2.5-coder:7b"])
        self.assertEqual(queue_response["summary"]["packet_done_total"], queue_response["summary"]["request_total"])
        self.assertEqual(queue_response["summary"]["unmanaged_ollama_call_total"], 0)
        self.assertEqual(queue_response["rows"][0]["output_text"], "{}")
        self.assertEqual(queue_response["rows"][0]["validation_result"]["status"], "SIMULATED")

    def test_logion_editorial_workbench_simulated_writer_checker(self) -> None:
        workbench_path = (
            ROOT.parent.parent.parent
            / "estra-private-work"
            / "logion"
            / "k3"
            / "execution"
            / "scripts"
            / "logion_llm"
            / "logion_editorial_workbench_v1.py"
        )
        if str(workbench_path.parent) not in sys.path:
            sys.path.insert(0, str(workbench_path.parent))
        spec = importlib.util.spec_from_file_location("logion_editorial_workbench_v1", workbench_path)
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module)
        queue = {
            "schema_id": "LOGION_LLM_SERVICE_QUEUE_REQUEST_v1",
            "queue_id": "unit_editorial_queue",
            "batch_id": "unit_editorial_queue",
            "requests": [
                {
                    "task_id": f"packet_{idx}",
                    "level": "L10",
                    "operation_type": "editorial_packet_review",
                    "artifact_type_id": "unit_artifact",
                    "prompt": f"Packet text:\nFinished public prose packet {idx} with a claim, intuition, example, evidence anchor, and limitation.",
                    "page_range": [idx + 1, idx + 1],
                    "sequence_index": idx,
                }
                for idx in range(2)
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            queue_path = tmp_path / "queue.json"
            queue_path.write_text(json.dumps(queue), encoding="utf-8")
            out_dir = tmp_path / "workbench"
            payload = module.run_workbench(
                SimpleNamespace(
                    input_queue_json=str(queue_path),
                    output_dir=str(out_dir),
                    until_done=True,
                    write=True,
                    simulate_provider=True,
                    max_packets=2,
                    cheap_only=True,
                    strict_extractive=False,
                    refresh_only=False,
                )
            )
            self.assertEqual(payload["status"], "PASS")
            self.assertEqual(payload["summary"]["writer"]["queue_status"], "DONE")
            self.assertEqual(payload["summary"]["checker"]["queue_status"], "DONE")
            self.assertEqual(payload["summary"]["unmanaged_ollama_call_total"], 0)
            self.assertEqual(payload["policy"]["profile"], "cheap_only_fallback")
            self.assertTrue((out_dir / "LOGION_EDITORIAL_WORKBENCH_COCKPIT.md").is_file())

    def test_recovery_r007_fails_recovery_r008_machine_when_reaudited(self) -> None:
        tools_dir = ROOT / "tools"
        if str(tools_dir) not in sys.path:
            sys.path.insert(0, str(tools_dir))
        from audit_oc_core_release_assembly_machine import build_audit

        audit = build_audit("oc_core_1_3_3", "recovery_r007")
        finding_kinds = {finding["kind"] for finding in audit["findings"]}
        self.assertIn("publication_common_llm_service_missing", finding_kinds)
        self.assertEqual(audit["summary"]["common_llm_service_status"], "FAIL")
        self.assertEqual(audit["summary"]["llm_service_vmodel_status"], "FAIL")

    def test_recovery_r008_logion_llm_service_package_passes(self) -> None:
        base = ROOT / "releases" / "oc_core_1_3_3" / "editorial" / "generated_artifacts_recovered" / "recovery_r008"
        assembly = read_json(base / "package_assembly" / "OC_CORE_RELEASE_PACKAGE_ASSEMBLY_1.3.3.json")
        machine = read_json(base / "package_assembly" / "OC_CORE_RELEASE_ASSEMBLY_MACHINE_AUDIT_1.3.3.json")
        comparison = read_json(base / "package_assembly" / "OC_CORE_RELEASE_ASSEMBLY_REVISION_COMPARISON_1.3.3.recovery_r008.json")
        quality = read_json(
            ROOT
            / "releases"
            / "oc_core_1_3_3"
            / "editorial"
            / "quality_validation"
            / "recovery_r008"
            / "OC_CORE_RELEASE_QUALITY_AUDIT_1.3.3.json"
        )

        trace = assembly["governed_ollama_trace"]
        self.assertEqual(assembly["assembly_revision"], "recovery_r008")
        self.assertEqual(trace["schema_id"], "OC_CORE_R008_LOGION_LLM_SERVICE_TRACE_v1")
        self.assertEqual(trace["common_llm_service_status"], "PASS")
        self.assertEqual(trace["max_workers"], 1)
        self.assertEqual(trace["unmanaged_ollama_call_total"], 0)
        self.assertIn(trace["status"], {"PASS", "SKIPPED_BY_GOVERNANCE", "LOCAL_OLLAMA_CAPABILITY_EXHAUSTED"})
        self.assertEqual(assembly["publication_translation_pipeline"]["status"], "PUBLICATION_TRANSLATOR_R008")
        self.assertEqual(machine["status"], "PASS")
        self.assertEqual(comparison["status"], "PASS")
        self.assertEqual(quality["summary"]["artifact_failure_total"], 0)
        for key in R008_FORM_STATUS_KEYS:
            self.assertEqual(machine["summary"][key], "PASS", key)
            self.assertEqual(comparison["summary"][key], "PASS", key)
            self.assertEqual(quality["summary"][key], "PASS", key)

        rows = {row["artifact_type_id"]: row for row in assembly["artifact_rows"]}
        self.assertEqual(rows["master_monograph"]["public_translation_source"], "science_monolith_logion_llm_service_translator_r008")
        for artifact_id in ["release_guide", "journal_core_article", "methods_repro_companion", "reviewer_attack_response_map"]:
            row = rows[artifact_id]
            self.assertEqual(row["public_translation_status"], "PUBLICATION_TRANSLATOR_R008")
            self.assertEqual(row["public_translation_source"], "logion_llm_service_publication_translator_r008")
            self.assertTrue(row["logion_llm_service_ledger_ref"])
            self.assertIsInstance(row["logion_llm_service_cadence_sequence"], list)

    def test_recovery_r008_public_surfaces_use_service_trace_not_public_internal_prose(self) -> None:
        base = ROOT / "releases" / "oc_core_1_3_3" / "editorial" / "generated_artifacts_recovered" / "recovery_r008"
        source_base = base / "b" / "base_source"
        entrypoint = (source_base / "oc_core_1_3_master_monograph.tex").read_text(encoding="utf-8")
        preamble = (source_base / "preamble.tex").read_text(encoding="utf-8")
        part_i = (source_base / "content" / "r008" / "01_why_continuum_ontology.tex").read_text(encoding="utf-8")
        part_ii = (source_base / "content" / "r008" / "02_first_concepts_and_k_primer.tex").read_text(encoding="utf-8")
        guide = (base / "sources" / "release_guide_1.3.3.md").read_text(encoding="utf-8")
        service_trace = read_json(base / "package_assembly" / "OC133_R008_LOGION_LLM_SERVICE_TRACE_1.3.3.json")

        self.assertIn("% R008_TOC_VISUAL_HIERARCHY", entrypoint)
        self.assertIn("% R008_LAYOUT_STANDARD", preamble)
        self.assertIn("PUBLICATION_TRANSLATOR_R008", guide)
        self.assertIn("fig:r008-continuum-demonstrator", part_i)
        self.assertIn("fig:r008-k0-k12-hierarchy", part_ii)
        self.assertIn("R008_K_LEVELS_PRESENT: K0 K1 K2 K3 K4 K5 K6 K7 K8 K9 K10 K11 K12", part_ii)
        self.assertEqual(service_trace["schema_id"], "LOGION_LLM_SERVICE_RESPONSE_v1")
        for needle in ["upward composition", "downward constraint", "falsifier anchor", "formal anchor"]:
            self.assertRegex(part_i + "\n" + part_ii, re.compile(re.escape(needle), re.I))
        for forbidden in ["Logion", "ESTRA", "Figure Route and Design Logic", "Evidence Coverage Map", "route sheet", "machine register", "recovery_r008"]:
            self.assertNotIn(forbidden, entrypoint + "\n" + part_i + "\n" + part_ii + "\n" + guide)

    def test_recovery_r008_fails_recovery_r009_machine_when_reaudited(self) -> None:
        tools_dir = ROOT / "tools"
        if str(tools_dir) not in sys.path:
            sys.path.insert(0, str(tools_dir))
        from audit_oc_core_release_assembly_machine import build_audit

        audit = build_audit("oc_core_1_3_3", "recovery_r008")
        finding_kinds = {finding["kind"] for finding in audit["findings"]}
        self.assertIn("publication_editorial_llm_queue_not_done", finding_kinds)
        self.assertIn("publication_actual_ollama_invocation_missing", finding_kinds)
        self.assertEqual(audit["summary"]["editorial_llm_queue_status"], "FAIL")
        self.assertEqual(audit["summary"]["actual_ollama_invocation_status"], "FAIL")

    def test_recovery_r009_until_done_editorial_ollama_package_passes(self) -> None:
        base = ROOT / "releases" / "oc_core_1_3_3" / "editorial" / "generated_artifacts_recovered" / "recovery_r009"
        assembly = read_json(base / "package_assembly" / "OC_CORE_RELEASE_PACKAGE_ASSEMBLY_1.3.3.json")
        machine = read_json(base / "package_assembly" / "OC_CORE_RELEASE_ASSEMBLY_MACHINE_AUDIT_1.3.3.json")
        comparison = read_json(base / "package_assembly" / "OC_CORE_RELEASE_ASSEMBLY_REVISION_COMPARISON_1.3.3.recovery_r009.json")
        quality = read_json(
            ROOT
            / "releases"
            / "oc_core_1_3_3"
            / "editorial"
            / "quality_validation"
            / "recovery_r009"
            / "OC_CORE_RELEASE_QUALITY_AUDIT_1.3.3.json"
        )
        queue = read_json(base / "package_assembly" / "OC133_R009_EDITORIAL_LLM_PACKET_QUEUE_1.3.3.json")
        trace = assembly["governed_ollama_trace"]

        self.assertEqual(assembly["assembly_revision"], "recovery_r009")
        self.assertEqual(trace["schema_id"], "OC_CORE_R009_LOGION_LLM_SERVICE_UNTIL_DONE_TRACE_v1")
        self.assertEqual(trace["queue_status"], "DONE")
        self.assertEqual(trace["editorial_llm_queue_status"], "PASS")
        self.assertEqual(trace["actual_ollama_invocation_status"], "PASS")
        self.assertGreater(trace["ollama_invocation_total"], 0)
        self.assertEqual(trace["packet_done_total"], trace["packet_total"])
        self.assertEqual(trace["unmanaged_ollama_call_total"], 0)
        service_trace = read_json(base / "package_assembly" / "OC133_R009_LOGION_LLM_SERVICE_UNTIL_DONE_TRACE_1.3.3.json")
        completed_rows = [row for row in service_trace["rows"] if row.get("model")]
        self.assertEqual(len(completed_rows), trace["packet_total"])
        self.assertTrue(all("output_text" in row and row.get("validation_result") for row in completed_rows))
        self.assertEqual(assembly["publication_translation_pipeline"]["status"], "PUBLICATION_TRANSLATOR_R009")
        self.assertEqual(machine["status"], "PASS")
        self.assertEqual(comparison["status"], "PASS")
        self.assertEqual(quality["summary"]["artifact_failure_total"], 0)
        for key in R009_FORM_STATUS_KEYS:
            self.assertEqual(machine["summary"][key], "PASS", key)
            self.assertEqual(comparison["summary"][key], "PASS", key)
            self.assertEqual(quality["summary"][key], "PASS", key)

        expected_artifacts = {"master_monograph", "release_guide", "journal_core_article", "methods_repro_companion", "reviewer_attack_response_map"}
        self.assertGreaterEqual(set(queue["artifact_packet_counts"]), expected_artifacts)
        self.assertEqual(set(trace["artifact_packet_counts"]), expected_artifacts)
        self.assertGreaterEqual(queue["l10_packet_total"], len(expected_artifacts))
        self.assertIn("L10", {request["level"] for request in queue["requests"]})
        self.assertIn("L9", {request["level"] for request in queue["requests"]})
        self.assertIn("L8", {request["level"] for request in queue["requests"]})

        rows = {row["artifact_type_id"]: row for row in assembly["artifact_rows"]}
        self.assertEqual(rows["master_monograph"]["public_translation_source"], "science_monolith_editorial_ollama_until_done_translator_r009")
        for artifact_id in ["release_guide", "journal_core_article", "methods_repro_companion", "reviewer_attack_response_map"]:
            row = rows[artifact_id]
            self.assertEqual(row["public_translation_status"], "PUBLICATION_TRANSLATOR_R009")
            self.assertEqual(row["public_translation_source"], "editorial_ollama_until_done_publication_translator_r009")
            self.assertEqual(row["editorial_llm_queue_status"], "PASS")
            self.assertGreater(row["ollama_invocation_total"], 0)
            self.assertEqual(row["unmanaged_ollama_call_total"], 0)

    def test_recovery_r010_source_grounded_repair_loop_records_capability_boundary(self) -> None:
        base = ROOT / "releases" / "oc_core_1_3_3" / "editorial" / "generated_artifacts_recovered" / "recovery_r010"
        assembly = read_json(base / "package_assembly" / "OC_CORE_RELEASE_PACKAGE_ASSEMBLY_1.3.3.json")
        machine = read_json(base / "package_assembly" / "OC_CORE_RELEASE_ASSEMBLY_MACHINE_AUDIT_1.3.3.json")
        comparison = read_json(base / "package_assembly" / "OC_CORE_RELEASE_ASSEMBLY_REVISION_COMPARISON_1.3.3.recovery_r010.json")
        quality = read_json(
            ROOT
            / "releases"
            / "oc_core_1_3_3"
            / "editorial"
            / "quality_validation"
            / "recovery_r010"
            / "OC_CORE_RELEASE_QUALITY_AUDIT_1.3.3.json"
        )
        records = read_json(base / "editorial_repair" / "OC133_R010_SOURCE_GROUNDED_REPAIR_RECORDS_1.3.3.json")
        queue = read_json(base / "editorial_repair" / "OC133_R010_SOURCE_GROUNDED_REPAIR_QUEUE_1.3.3.json")
        trace = read_json(base / "editorial_repair" / "OC133_R010_SOURCE_GROUNDED_REPAIR_TRACE_1.3.3.json")
        summary = read_json(base / "editorial_repair" / "OC133_R010_SOURCE_GROUNDED_REPAIR_SUMMARY_1.3.3.json")

        self.assertEqual(assembly["assembly_revision"], "recovery_r010")
        self.assertEqual(assembly["publication_translation_pipeline"]["status"], "PUBLICATION_TRANSLATOR_R010_SOURCE_GROUNDED_REPAIR")
        self.assertEqual(summary["status"], "PASS")
        self.assertEqual(summary["source_grounded_repair_status"], "REPAIR_REQUIRED")
        self.assertEqual(summary["local_editorial_capability_boundary_status"], "LOCAL_EDITORIAL_CAPABILITY_EXHAUSTED")
        self.assertGreater(summary["repair_record_total"], 0)
        self.assertEqual(summary["accepted_candidate_promoted_total"], 0)
        self.assertEqual(summary["unresolved_repair_record_total"], summary["repair_record_total"])
        self.assertEqual(summary["unmanaged_ollama_call_total"], 0)
        self.assertEqual(trace["queue_status"], "DONE")
        self.assertEqual((trace["summary"] or {})["packet_done_total"], len(queue["requests"]))
        self.assertEqual(summary["repair_ollama_invocation_total"], len(queue["requests"]))
        self.assertEqual(records["summary"]["repair_record_total"], len(records["records"]))
        self.assertTrue(all(record["promotion_status"] == "NOT_PROMOTED_LOCAL_REPAIR_REQUIRED" for record in records["records"]))

        self.assertEqual(machine["status"], "PASS")
        self.assertEqual(comparison["status"], "PASS")
        self.assertEqual(quality["summary"]["artifact_failure_total"], 0)
        self.assertEqual(machine["summary"]["source_grounded_repair_status"], "REPAIR_REQUIRED")
        self.assertEqual(machine["summary"]["unresolved_repair_record_total"], summary["repair_record_total"])
        self.assertEqual(quality["summary"]["source_grounded_repair_status"], "REPAIR_REQUIRED")
        for key in R010_FORM_STATUS_KEYS:
            self.assertEqual(machine["summary"][key], "PASS", key)
            self.assertEqual(comparison["summary"][key], "PASS", key)
            self.assertEqual(quality["summary"][key], "PASS", key)

        rows = {row["artifact_type_id"]: row for row in assembly["artifact_rows"]}
        self.assertEqual(rows["master_monograph"]["public_translation_source"], "science_monolith_source_grounded_editorial_repair_r010")
        for artifact_id in ["release_guide", "journal_core_article", "methods_repro_companion", "reviewer_attack_response_map"]:
            row = rows[artifact_id]
            self.assertEqual(row["public_translation_status"], "PUBLICATION_TRANSLATOR_R010_SOURCE_GROUNDED_REPAIR")
            self.assertEqual(row["public_translation_source"], "source_grounded_editorial_repair_publication_translator_r010")
            self.assertEqual(row["source_grounded_repair_status"], "REPAIR_REQUIRED")
            self.assertEqual(row["accepted_candidate_promoted_total"], 0)

    def test_recovery_r011_journal_requirements_spot_is_owner_review_ready(self) -> None:
        r010_base = ROOT / "releases" / "oc_core_1_3_3" / "editorial" / "generated_artifacts_recovered" / "recovery_r010"
        r010_summary = read_json(r010_base / "editorial_repair" / "OC133_R010_SOURCE_GROUNDED_REPAIR_SUMMARY_1.3.3.json")
        self.assertEqual(r010_summary["source_grounded_repair_status"], "REPAIR_REQUIRED")
        self.assertGreater(r010_summary["unresolved_repair_record_total"], 0)
        self.assertFalse((r010_base / "journal_requirements_spot").exists())

        base = ROOT / "releases" / "oc_core_1_3_3" / "editorial" / "generated_artifacts_recovered" / "recovery_r011"
        assembly = read_json(base / "package_assembly" / "OC_CORE_RELEASE_PACKAGE_ASSEMBLY_1.3.3.json")
        machine = read_json(base / "package_assembly" / "OC_CORE_RELEASE_ASSEMBLY_MACHINE_AUDIT_1.3.3.json")
        comparison = read_json(base / "package_assembly" / "OC_CORE_RELEASE_ASSEMBLY_REVISION_COMPARISON_1.3.3.recovery_r011.json")
        quality = read_json(
            ROOT
            / "releases"
            / "oc_core_1_3_3"
            / "editorial"
            / "quality_validation"
            / "recovery_r011"
            / "OC_CORE_RELEASE_QUALITY_AUDIT_1.3.3.json"
        )
        spot_root = base / "journal_requirements_spot"
        index = read_json(spot_root / "OC133_R011_JOURNAL_REQUIREMENTS_INDEX_1.3.3.json")
        spot = read_json(spot_root / "OC133_R011_RELEASE_SPOT_MAP_1.3.3.json")
        acceptance = read_json(spot_root / "OC133_R011_BOUNDED_SYNTHESIS_ACCEPTANCE_1.3.3.json")
        queue = read_json(spot_root / "OC133_R011_JOURNAL_REQUIREMENTS_SPOT_QUEUE_1.3.3.json")
        trace = read_json(spot_root / "OC133_R011_JOURNAL_REQUIREMENTS_SPOT_TRACE_1.3.3.json")
        summary = read_json(spot_root / "OC133_R011_JOURNAL_REQUIREMENTS_SPOT_SUMMARY_1.3.3.json")

        self.assertEqual(assembly["assembly_revision"], "recovery_r011")
        self.assertEqual(assembly["publication_translation_pipeline"]["status"], "PUBLICATION_TRANSLATOR_R011_JOURNAL_REQUIREMENTS_SPOT")
        self.assertEqual(summary["scientific_journal_submission_ready_status"], "SCIENTIFIC_JOURNAL_SUBMISSION_READY_NO_SEND")
        self.assertEqual(summary["status"], "PASS")
        self.assertEqual(summary["venue_total"], 8)
        self.assertEqual(summary["requirements_source_total"], 8)
        self.assertEqual(summary["requirements_matrix_total"], 8)
        self.assertEqual(summary["journal_package_total"], 8)
        self.assertEqual(summary["unresolved_repair_record_total"], 0)
        self.assertEqual(summary["fabrication_risk_total"], 0)
        self.assertEqual(summary["unmanaged_ollama_call_total"], 0)
        self.assertGreater(summary["ollama_invocation_total"], 0)
        self.assertEqual(trace["queue_status"], "DONE")
        self.assertEqual((trace["summary"] or {})["packet_done_total"], len(queue["requests"]))
        self.assertEqual(index["venue_total"], 8)
        self.assertEqual(spot["status"], "SPOT_READY")
        self.assertEqual(acceptance["status"], "PASS")
        self.assertEqual(acceptance["unresolved_repair_record_total"], 0)

        expected_venues = {
            "FOUNDATIONS_OF_SCIENCE",
            "SYNTHESE",
            "FOUNDATIONS_OF_PHYSICS",
            "ACTA_BIOTHEORETICA",
            "GLOBAL_JOURNAL_OF_FLEXIBLE_SYSTEMS_MANAGEMENT",
            "PHYSICAL_REVIEW_RESEARCH",
            "ACS_OMEGA",
            "PLOS_COMPUTATIONAL_BIOLOGY",
        }
        self.assertEqual({venue["venue_id"] for venue in index["venues"]}, expected_venues)
        venue_rows = {venue["venue_id"]: venue for venue in index["venues"]}
        for venue_id in expected_venues:
            source = ROOT / venue_rows[venue_id]["requirements_source_path"]
            matrix = ROOT / venue_rows[venue_id]["requirements_matrix_path"]
            package = ROOT / venue_rows[venue_id]["package_path"]
            manifest = package.parent / "REQUIRED_COMPONENT_MANIFEST.json"
            self.assertTrue(source.is_file(), venue_id)
            self.assertTrue(matrix.is_file(), venue_id)
            self.assertTrue(package.is_file(), venue_id)
            self.assertTrue(manifest.is_file(), venue_id)
            package_payload = read_json(package)
            self.assertEqual(package_payload["status"], "OWNER_REVIEW_READY_NO_SEND")
            self.assertTrue(package_payload["no_send_lock"])
            self.assertFalse(package_payload["external_action_performed"])

        self.assertEqual(machine["status"], "PASS")
        self.assertEqual(comparison["status"], "PASS")
        self.assertEqual(quality["summary"]["artifact_failure_total"], 0)
        self.assertEqual(machine["summary"]["scientific_journal_terminal_state"], "SCIENTIFIC_JOURNAL_SUBMISSION_READY_NO_SEND")
        for key in R011_FORM_STATUS_KEYS:
            self.assertEqual(machine["summary"][key], "PASS", key)
            self.assertEqual(comparison["summary"][key], "PASS", key)
            self.assertEqual(quality["summary"][key], "PASS", key)

        rows = {row["artifact_type_id"]: row for row in assembly["artifact_rows"]}
        self.assertEqual(rows["master_monograph"]["public_translation_source"], "science_monolith_journal_requirements_spot_r011")
        for artifact_id in ["release_guide", "journal_core_article", "methods_repro_companion", "reviewer_attack_response_map"]:
            row = rows[artifact_id]
            self.assertEqual(row["public_translation_status"], "PUBLICATION_TRANSLATOR_R011_JOURNAL_REQUIREMENTS_SPOT")
            self.assertEqual(row["public_translation_source"], "journal_requirements_spot_publication_translator_r011")
            self.assertEqual(row["source_gap_zero_status"], "PASS")
            self.assertEqual(row["scientific_journal_submission_ready_status"], "SCIENTIFIC_JOURNAL_SUBMISSION_READY_NO_SEND")

    def test_recovery_r011_fails_recovery_r012_visual_machine_when_reaudited(self) -> None:
        tools_dir = ROOT / "tools"
        if str(tools_dir) not in sys.path:
            sys.path.insert(0, str(tools_dir))
        from audit_oc_core_release_assembly_machine import build_audit

        audit = build_audit("oc_core_1_3_3", "recovery_r011")
        finding_kinds = {finding["kind"] for finding in audit["findings"]}
        for kind in [
            "publication_r012_figure_spec_missing",
            "publication_r012_geometry_failed",
            "publication_r012_rendered_bbox_failed",
            "publication_r012_visual_cockpit_failed",
        ]:
            self.assertIn(kind, finding_kinds)
        for key in [
            "figure_spec_coverage_status",
            "diagram_geometry_status",
            "rendered_figure_bbox_status",
            "visual_cockpit_status",
            "form_quality_status",
        ]:
            self.assertEqual(audit["summary"][key], "FAIL", key)

    def test_recovery_r012_visual_qa_package_passes(self) -> None:
        base = ROOT / "releases" / "oc_core_1_3_3" / "editorial" / "generated_artifacts_recovered" / "recovery_r012"
        assembly = read_json(base / "package_assembly" / "OC_CORE_RELEASE_PACKAGE_ASSEMBLY_1.3.3.json")
        machine = read_json(base / "package_assembly" / "OC_CORE_RELEASE_ASSEMBLY_MACHINE_AUDIT_1.3.3.json")
        comparison = read_json(base / "package_assembly" / "OC_CORE_RELEASE_ASSEMBLY_REVISION_COMPARISON_1.3.3.recovery_r012.json")
        quality = read_json(
            ROOT
            / "releases"
            / "oc_core_1_3_3"
            / "editorial"
            / "quality_validation"
            / "recovery_r012"
            / "OC_CORE_RELEASE_QUALITY_AUDIT_1.3.3.json"
        )
        visual_root = base / "visual_quality"
        registry = read_json(visual_root / "OC133_R012_FIGURE_REGISTRY_1.3.3.json")
        geometry = read_json(visual_root / "OC133_R012_FIGURE_GEOMETRY_LEDGER_1.3.3.json")
        rendered = read_json(visual_root / "OC133_R012_RENDERED_FIGURE_BBOX_LEDGER_1.3.3.json")
        cockpit = read_json(visual_root / "OC133_R012_VISUAL_QA_COCKPIT_1.3.3.json")

        self.assertEqual(assembly["assembly_revision"], "recovery_r012")
        self.assertEqual(assembly["publication_translation_pipeline"]["status"], "PUBLICATION_TRANSLATOR_R012_FIGURE_VISUAL_QA_SPOT")
        self.assertEqual(cockpit["status"], "PASS")
        self.assertGreaterEqual(registry["figure_total"], 36)
        self.assertGreaterEqual(registry["deterministic_tikz_spec_total"], 38)
        self.assertEqual(geometry["status"], "PASS")
        self.assertEqual(rendered["status"], "PASS")
        self.assertFalse(rendered["technical_probe_pdf_in_public_package"])
        self.assertFalse((visual_root / "probe").exists())
        labels = {figure["label"] for figure in registry["figures"]}
        self.assertIn("fig:r012-continuum-demonstrator", labels)
        self.assertIn("fig:r012-k0-k12-hierarchy", labels)
        for index in range(13):
            self.assertIn(f"K{index}", json.dumps(registry, ensure_ascii=False))

        rows = {row["artifact_type_id"]: row for row in assembly["artifact_rows"]}
        master = rows["master_monograph"]
        self.assertEqual(master["visual_cockpit_status"], "PASS")
        self.assertEqual(master["public_translation_source"], "science_monolith_figure_visual_qa_spot_r012")
        for key in R012_FORM_STATUS_KEYS:
            self.assertEqual(machine["summary"][key], "PASS", key)
            self.assertEqual(comparison["summary"][key], "PASS", key)
            self.assertEqual(quality["summary"][key], "PASS", key)
        self.assertEqual(machine["status"], "PASS")
        self.assertEqual(comparison["status"], "PASS")
        self.assertEqual(quality["summary"]["artifact_failure_total"], 0)

    def test_recovery_r012_fails_recovery_r013_table_machine_when_reaudited(self) -> None:
        tools_dir = ROOT / "tools"
        if str(tools_dir) not in sys.path:
            sys.path.insert(0, str(tools_dir))
        from audit_oc_core_release_assembly_machine import build_audit

        audit = build_audit("oc_core_1_3_3", "recovery_r012")
        finding_kinds = {finding["kind"] for finding in audit["findings"]}
        for kind in [
            "publication_r013_table_spec_missing",
            "publication_r013_table_geometry_failed",
            "publication_r013_rendered_table_bbox_failed",
            "publication_r013_table_cockpit_failed",
        ]:
            self.assertIn(kind, finding_kinds)
        for key in [
            "table_spec_coverage_status",
            "table_geometry_status",
            "rendered_table_bbox_status",
            "table_cockpit_status",
            "table_readability_status",
            "form_quality_status",
        ]:
            self.assertEqual(audit["summary"][key], "FAIL", key)

    def test_recovery_r013_table_qa_package_passes(self) -> None:
        base = ROOT / "releases" / "oc_core_1_3_3" / "editorial" / "generated_artifacts_recovered" / "recovery_r013"
        assembly = read_json(base / "package_assembly" / "OC_CORE_RELEASE_PACKAGE_ASSEMBLY_1.3.3.json")
        machine = read_json(base / "package_assembly" / "OC_CORE_RELEASE_ASSEMBLY_MACHINE_AUDIT_1.3.3.json")
        comparison = read_json(base / "package_assembly" / "OC_CORE_RELEASE_ASSEMBLY_REVISION_COMPARISON_1.3.3.recovery_r013.json")
        quality = read_json(
            ROOT
            / "releases"
            / "oc_core_1_3_3"
            / "editorial"
            / "quality_validation"
            / "recovery_r013"
            / "OC_CORE_RELEASE_QUALITY_AUDIT_1.3.3.json"
        )
        table_root = base / "table_quality"
        registry = read_json(table_root / "OC133_R013_TABLE_REGISTRY_1.3.3.json")
        geometry = read_json(table_root / "OC133_R013_TABLE_GEOMETRY_LEDGER_1.3.3.json")
        rendered = read_json(table_root / "OC133_R013_RENDERED_TABLE_BBOX_LEDGER_1.3.3.json")
        cockpit = read_json(table_root / "OC133_R013_TABLE_QA_COCKPIT_1.3.3.json")

        self.assertEqual(assembly["assembly_revision"], "recovery_r013")
        self.assertEqual(assembly["publication_translation_pipeline"]["status"], "PUBLICATION_TRANSLATOR_R013_TABLE_RENDERED_QA_SPOT")
        self.assertEqual(cockpit["status"], "PASS")
        self.assertGreaterEqual(registry["compiled_reader_table_total"], 8)
        self.assertEqual(registry["table_total"], cockpit["registered_table_total"])
        self.assertEqual(geometry["status"], "PASS")
        self.assertEqual(rendered["status"], "PASS")
        self.assertFalse(rendered["technical_probe_pdf_in_public_package"])
        self.assertFalse((table_root / "probe").exists())
        labels = {table["label"] for table in registry["tables"]}
        self.assertIn("tab:klevels-overview", labels)
        self.assertIn("tab:r013-operationalization-program", labels)
        self.assertIn("tab:r013-execution-protocol-matrix", labels)

        rows = {row["artifact_type_id"]: row for row in assembly["artifact_rows"]}
        master = rows["master_monograph"]
        self.assertEqual(master["visual_cockpit_status"], "PASS")
        self.assertEqual(master["table_cockpit_status"], "PASS")
        self.assertEqual(master["public_translation_source"], "science_monolith_table_rendered_qa_spot_r013")
        self.assertEqual(master["compiled_reader_table_total"], master["registered_table_total"])
        for key in R013_FORM_STATUS_KEYS:
            self.assertEqual(machine["summary"][key], "PASS", key)
            self.assertEqual(comparison["summary"][key], "PASS", key)
            self.assertEqual(quality["summary"][key], "PASS", key)
        self.assertEqual(machine["status"], "PASS")
        self.assertEqual(comparison["status"], "PASS")
        self.assertEqual(quality["summary"]["artifact_failure_total"], 0)

    def test_recovery_r014_fails_recovery_r015_scientific_gate_when_reaudited(self) -> None:
        tools_dir = ROOT / "tools"
        if str(tools_dir) not in sys.path:
            sys.path.insert(0, str(tools_dir))
        from audit_oc_core_release_assembly_machine import build_audit

        audit = build_audit("oc_core_1_3_3", "recovery_r014")
        finding_kinds = {finding["kind"] for finding in audit["findings"]}
        self.assertIn("publication_r015_scientific_review_missing", finding_kinds)
        for key in [
            "scientific_source_review_status",
            "research_pingpong_status",
            "form_quality_status",
        ]:
            self.assertEqual(audit["summary"][key], "FAIL", key)

    def test_recovery_r015_scientific_review_gate_package_passes(self) -> None:
        base = ROOT / "releases" / "oc_core_1_3_3" / "editorial" / "generated_artifacts_recovered" / "recovery_r015"
        assembly = read_json(base / "package_assembly" / "OC_CORE_RELEASE_PACKAGE_ASSEMBLY_1.3.3.json")
        machine = read_json(base / "package_assembly" / "OC_CORE_RELEASE_ASSEMBLY_MACHINE_AUDIT_1.3.3.json")
        comparison = read_json(base / "package_assembly" / "OC_CORE_RELEASE_ASSEMBLY_REVISION_COMPARISON_1.3.3.recovery_r015.json")
        quality = read_json(
            ROOT
            / "releases"
            / "oc_core_1_3_3"
            / "editorial"
            / "quality_validation"
            / "recovery_r015"
            / "OC_CORE_RELEASE_QUALITY_AUDIT_1.3.3.json"
        )
        cerberus = read_json(
            ROOT
            / "releases"
            / "oc_core_1_3_3"
            / "editorial"
            / "quality_validation"
            / "recovery_r015"
            / "cerberus"
            / "OC133_EDITORIAL_CERBERUS_SUMMARY.json"
        )
        review_root = base / "scientific_review"
        terminal = read_json(review_root / "OC133_R015_SCIENTIFIC_REVIEW_TERMINAL_REPORT_1.3.3.json")
        future = read_json(review_root / "OC133_R015_REQUIRED_FUTURE_RESEARCH_REGISTER_1.3.3.json")
        queue = read_json(review_root / "OC133_R015_SCIENTIFIC_SOURCE_REVIEW_QUEUE_1.3.3.json")
        trace = read_json(review_root / "OC133_R015_SCIENTIFIC_SOURCE_REVIEW_TRACE_1.3.3.json")
        manifest = read_json(base / "package" / "OC_CORE_RELEASE_PACKAGE_MANIFEST_1.3.3.json")

        self.assertEqual(assembly["assembly_revision"], "recovery_r015")
        self.assertEqual(assembly["publication_translation_pipeline"]["status"], "PUBLICATION_TRANSLATOR_R015_SCIENTIFIC_REVIEW_GATE")
        self.assertEqual(machine["status"], "PASS")
        self.assertEqual(comparison["status"], "PASS")
        self.assertEqual(quality["status"], "QUALITY_VALIDATION_PASS")
        self.assertEqual(quality["summary"]["blocking_vulnerability_total"], 0)
        self.assertEqual(quality["summary"]["vulnerability_total"], 0)
        self.assertEqual(quality["summary"]["artifact_failure_total"], 0)
        self.assertEqual(quality["summary"]["scientific_coverage_not_assessed_l10_total"], 0)
        self.assertTrue(quality["summary"]["scientific_full_coverage_claim_allowed"])

        self.assertEqual(cerberus["state"], "PASS")
        self.assertEqual(cerberus["critical_open_total"], 0)
        self.assertEqual(cerberus["high_open_total"], 0)
        self.assertEqual(cerberus["parse_failure_total"], 0)
        self.assertEqual(cerberus["external_reasoning_run_status"], "SOURCE_LEVEL_SCIENTIFIC_REVIEW_GATE_CONSUMED")

        self.assertEqual(terminal["status"], "PASS")
        self.assertEqual(terminal["scientific_source_review_status"], "PASS")
        self.assertEqual(terminal["research_pingpong_status"], "PASS")
        self.assertEqual(terminal["critical_scientific_vulnerability_total"], 0)
        self.assertEqual(terminal["high_scientific_vulnerability_total"], 0)
        self.assertEqual(terminal["queue_status"], "DONE")
        self.assertGreater(terminal["ollama_invocation_total"], 0)
        self.assertEqual(terminal["unmanaged_ollama_call_total"], 0)
        self.assertEqual(trace["queue_status"], "DONE")
        self.assertEqual((trace["summary"] or {})["packet_done_total"], len(queue["requests"]))
        self.assertEqual(queue["requests"][0]["level"], "L10")
        self.assertEqual(queue["requests"][-1]["level"], "L8")

        self.assertEqual(future["status"], "PASS")
        self.assertGreaterEqual(future["future_research_total"], 4)
        required_fields = {"future_research_id", "title", "description", "goal", "hypothesis", "method", "possible_outcomes", "blocker_reason", "linked_claims"}
        for row in future["rows"]:
            self.assertTrue(required_fields.issubset(row), row)
            self.assertNotIn(str(row["blocker_reason"]).strip().lower(), {"", "no time yet", "todo"})

        manifest_paths = {row["path"] for row in manifest["files"]}
        self.assertIn("proofs/PROOF_DEPENDENCY_GRAPH_1_3_3.json", manifest_paths)
        self.assertIn("formal/lean/LEAN_BUILD_CERTIFICATE_1_3_3.json", manifest_paths)
        self.assertTrue(any(path.startswith("proofs/proof_sheets/T133-") for path in manifest_paths))

        future_tex = (base / "b" / "base_source" / "content" / "r015_required_future_research.tex").read_text(encoding="utf-8")
        self.assertIn("Required Future Research and Experiments", future_tex)
        self.assertIn("Prospective K-Level Prediction Battery", future_tex)
        self.assertIn("Clean Lean Certificate Binding", future_tex)

        rows = {row["artifact_type_id"]: row for row in assembly["artifact_rows"]}
        self.assertEqual(rows["master_monograph"]["public_translation_source"], "science_monolith_scientific_review_gate_r015")
        for artifact_id in ["release_guide", "journal_core_article", "methods_repro_companion", "reviewer_attack_response_map"]:
            row = rows[artifact_id]
            self.assertEqual(row["public_translation_status"], "PUBLICATION_TRANSLATOR_R015_SCIENTIFIC_REVIEW_GATE")
            self.assertEqual(row["public_translation_source"], "scientific_review_gate_publication_translator_r015")
            self.assertEqual(row["scientific_source_review_status"], "PASS")
            self.assertEqual(row["research_pingpong_status"], "PASS")

        for key in R015_FORM_STATUS_KEYS:
            self.assertEqual(machine["summary"][key], "PASS", key)
            self.assertEqual(comparison["summary"][key], "PASS", key)
            self.assertEqual(quality["summary"][key], "PASS", key)

    def test_recovery_r015_fails_recovery_r016_machine_self_audit_when_reaudited(self) -> None:
        tools_dir = ROOT / "tools"
        if str(tools_dir) not in sys.path:
            sys.path.insert(0, str(tools_dir))
        from audit_oc_core_release_assembly_machine import build_audit

        audit = build_audit("oc_core_1_3_3", "recovery_r015")
        finding_kinds = {finding["kind"] for finding in audit["findings"]}
        self.assertIn("publication_r016_machine_self_audit_missing", finding_kinds)
        for key in [
            "machine_self_audit_status",
            "filter_regression_status",
            "toe_gap_assessment_status",
            "form_quality_status",
        ]:
            self.assertEqual(audit["summary"][key], "FAIL", key)

    def test_recovery_r016_machine_self_audit_package_passes_and_blocks_r017(self) -> None:
        base = ROOT / "releases" / "oc_core_1_3_3" / "editorial" / "generated_artifacts_recovered" / "recovery_r016"
        assembly = read_json(base / "package_assembly" / "OC_CORE_RELEASE_PACKAGE_ASSEMBLY_1.3.3.json")
        machine = read_json(base / "package_assembly" / "OC_CORE_RELEASE_ASSEMBLY_MACHINE_AUDIT_1.3.3.json")
        comparison = read_json(base / "package_assembly" / "OC_CORE_RELEASE_ASSEMBLY_REVISION_COMPARISON_1.3.3.recovery_r016.json")
        quality = read_json(
            ROOT
            / "releases"
            / "oc_core_1_3_3"
            / "editorial"
            / "quality_validation"
            / "recovery_r016"
            / "OC_CORE_RELEASE_QUALITY_AUDIT_1.3.3.json"
        )
        cerberus = read_json(
            ROOT
            / "releases"
            / "oc_core_1_3_3"
            / "editorial"
            / "quality_validation"
            / "recovery_r016"
            / "cerberus"
            / "OC133_EDITORIAL_CERBERUS_SUMMARY.json"
        )
        cockpit = read_json(base / "machine_self_audit" / "OC133_R016_MACHINE_SELF_AUDIT_COCKPIT_1.3.3.json")
        work_orders = read_json(base / "machine_self_audit" / "OC133_R016_TOE_GAP_WORK_ORDERS_1.3.3.json")

        self.assertEqual(assembly["assembly_revision"], "recovery_r016")
        self.assertEqual(assembly["publication_translation_pipeline"]["status"], "PUBLICATION_TRANSLATOR_R016_MACHINE_SELF_AUDITED_TOE_GATE")
        self.assertEqual(machine["status"], "PASS")
        self.assertEqual(comparison["status"], "PASS")
        self.assertEqual(quality["status"], "QUALITY_VALIDATION_PASS")
        self.assertEqual(cerberus["state"], "PASS")
        self.assertEqual(cockpit["status"], "PASS")
        self.assertEqual(cockpit["machine_self_audit_status"], "PASS")
        self.assertEqual(cockpit["journal_package_total"], 8)
        self.assertEqual(cockpit["toe_gap_assessment_status"], "PASS")
        self.assertEqual(cockpit["toe_final_pass_status"], "FAIL")
        self.assertEqual(cockpit["r017_promotion_gate"], "R017_BLOCKED_BY_TOE_VALIDATOR")
        self.assertFalse(cockpit["r017_promotion_allowed"])
        self.assertGreater(cockpit["toe_validator_error_total"], 0)
        self.assertGreaterEqual(work_orders["work_order_total"], work_orders["toe_validator_error_total"])
        self.assertTrue(any(row["work_order_id"] == "R016-TOE-AI-001" for row in work_orders["rows"]))
        self.assertTrue(any(row["work_order_id"] == "R016-TOE-EA-001" for row in work_orders["rows"]))
        for key in R016_FORM_STATUS_KEYS:
            self.assertEqual(machine["summary"][key], "PASS", key)
            self.assertEqual(comparison["summary"][key], "PASS", key)
            self.assertEqual(quality["summary"][key], "PASS", key)

    def test_final_toe_projection_lanes_block_r017_unless_ai_ea_are_anchored(self) -> None:
        tools_dir = ROOT / "tools"
        if str(tools_dir) not in sys.path:
            sys.path.insert(0, str(tools_dir))
        from oc_core_1_3_science_spot_lib import (
            FINAL_TOE_PROJECTION_LANE_TARGETS,
            validate_final_toe_grand_science_scorecard,
            validate_final_toe_projection_lanes,
        )

        errors = validate_final_toe_projection_lanes(ROOT)
        self.assertTrue(FINAL_TOE_PROJECTION_LANE_TARGETS["AI"].exists())
        self.assertTrue(FINAL_TOE_PROJECTION_LANE_TARGETS["ENTERPRISE_ARCHITECTURE"].exists())
        self.assertEqual(errors, [])
        for lane_id in ["AI", "ENTERPRISE_ARCHITECTURE"]:
            payload = read_json(FINAL_TOE_PROJECTION_LANE_TARGETS[lane_id])
            self.assertEqual(payload["status"], "PASS")
            self.assertEqual(payload["closure_verdict"], "PASS")
            self.assertTrue(payload["final_toe_support_allowed"])
            row = payload["rows"][0]
            self.assertEqual(row["closure_verdict"], "PASS")
            self.assertTrue(row["lean_refs"])
            self.assertTrue(row["finite_case_refs"])
            self.assertTrue(row["evidence_or_simulation_refs"])
            self.assertTrue(row["comparator_refs"])
            self.assertTrue(row["falsifier_refs"])
            self.assertFalse("BLOCKER" in row["claim_id"])
            self.assertEqual(row["support_checks"]["lean_refs_exist"], True)
            self.assertEqual(row["support_checks"]["finite_case_refs_present"], True)
        scorecard_errors = validate_final_toe_grand_science_scorecard(ROOT)
        self.assertTrue(any("grand_toe_claim_ledger_evidence is not PASS" in error for error in scorecard_errors))
        self.assertTrue(any("modern_science_comparator_superiority is not PASS" in error for error in scorecard_errors))

    def test_r017_toe_closure_factory_emits_fail_closed_obligations_lanes_and_cockpit(self) -> None:
        factory_path = ROOT / "tools" / "oc133_toe_closure_factory.py"
        spec = importlib.util.spec_from_file_location("oc133_toe_closure_factory", factory_path)
        module = importlib.util.module_from_spec(spec)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        spec.loader.exec_module(module)

        errors = module.current_validator_errors(ROOT)
        parts = module.current_validator_error_parts(ROOT)
        obligations = module.build_obligations(ROOT, errors, generated_at="TEST")
        lanes = module.build_lane_results(ROOT, generated_at="TEST")
        subwork = module.build_lane_subwork_orders(ROOT, errors, generated_at="TEST")
        root_causes = module.build_root_cause_ledger(ROOT, errors, [], generated_at="TEST")
        backlog = module.build_capability_backlog(ROOT, root_causes, subwork, generated_at="TEST")
        delta_trace = module.build_validator_delta_trace([], root_causes, backlog, generated_at="TEST")
        cockpit = module.build_cockpit(
            ROOT,
            obligations,
            lanes,
            errors,
            [],
            validator_parts=parts,
            root_causes=root_causes,
            capability_backlog=backlog,
            subwork_orders=subwork,
            delta_trace=delta_trace,
            generated_at="TEST",
        )

        self.assertGreaterEqual(len(errors), 1)
        self.assertEqual(obligations["status"], "OPEN")
        self.assertFalse(obligations["r017_promotion_allowed"])
        self.assertGreaterEqual(obligations["work_order_total"], len(errors))
        finding_classes = {row["finding_class"] for row in obligations["rows"]}
        for finding_class in [
            "AI_DOMAIN_TOE_PROJECTION_LANE",
            "ENTERPRISE_ARCHITECTURE_DOMAIN_TOE_PROJECTION_LANE",
            "GRAND_TOE_CLAIM_LEDGER_EVIDENCE",
            "MODERN_SCIENCE_COMPARATOR_SUPERIORITY",
            "CERBERUS_RELEASE_REVIEW_GATE",
        ]:
            self.assertIn(finding_class, finding_classes)
        for row in obligations["rows"]:
            self.assertTrue(row["blocks_r017"])
            self.assertTrue(row["fake_closure_rejected"])
            self.assertTrue(row["closure_condition"])
            self.assertTrue(row["validator_binding"])
            self.assertTrue(row["root_cause_class"])
            self.assertTrue(row["why_it_failed"])
            self.assertTrue(row["repair_strategy"])
            self.assertTrue(row["required_capability"])

        lane_rows = {row["lane_id"]: row for row in lanes["rows"]}
        for lane_id in ["AI", "ENTERPRISE_ARCHITECTURE"]:
            self.assertIn(lane_id, lane_rows)
            self.assertEqual(lane_rows[lane_id]["status"], "PASS")
            self.assertEqual(lane_rows[lane_id]["closure_verdict"], "PASS")
            self.assertTrue(lane_rows[lane_id]["final_toe_support_allowed"])
        for lane_id in [
            "GRAND_TOE_CLAIM_LEDGER_EVIDENCE",
            "MODERN_SCIENCE_COMPARATOR_SUPERIORITY",
            "CERBERUS_RELEASE_REVIEW_GATE",
        ]:
            self.assertIn(lane_id, lane_rows)
            self.assertEqual(lane_rows[lane_id]["status"], "FAIL")
            self.assertEqual(lane_rows[lane_id]["closure_verdict"], "FAIL_CLOSED")
            self.assertFalse(lane_rows[lane_id]["final_toe_support_allowed"])

        self.assertEqual(cockpit["status"], "OPEN")
        self.assertEqual(cockpit["current_promotion_gate"], "R017_BLOCKED_BY_TOE_CLOSURE_FACTORY")
        self.assertFalse(cockpit["r017_promotion_allowed"])
        self.assertEqual(cockpit["latest_execution_status"], "NOT_RUN")
        self.assertEqual(cockpit["fail_lane_total"], 3)
        self.assertEqual(cockpit["root_cause_coverage_status"], "PASS")
        self.assertGreater(cockpit["root_cause_total"], 0)
        self.assertGreater(cockpit["capability_backlog_total"], 0)
        self.assertGreater(cockpit["lane_subwork_order_total"], 0)
        self.assertEqual(cockpit["toe_problem_explainability_status"], "PASS")
        self.assertTrue(cockpit["no_progress_creates_backlog"])
        self.assertEqual(cockpit["proof_data_simulation_coverage_status"], "INCOMPLETE")
        self.assertGreater(cockpit["science_validator_error_total"], 0)
        self.assertGreater(cockpit["cerberus_error_total"], 0)

    def test_r017_toe_closure_factory_rejects_future_research_or_demoted_rows_as_closure(self) -> None:
        factory_path = ROOT / "tools" / "oc133_toe_closure_factory.py"
        spec = importlib.util.spec_from_file_location("oc133_toe_closure_factory", factory_path)
        module = importlib.util.module_from_spec(spec)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        spec.loader.exec_module(module)

        tools_dir = ROOT / "tools"
        if str(tools_dir) not in sys.path:
            sys.path.insert(0, str(tools_dir))
        from oc_core_1_3_science_spot_lib import FINAL_TOE_PROJECTION_LANE_TARGETS

        for lane_id in ["AI", "ENTERPRISE_ARCHITECTURE"]:
            payload = read_json(FINAL_TOE_PROJECTION_LANE_TARGETS[lane_id])
            self.assertEqual(payload["status"], "PASS")
            self.assertEqual(payload["closure_verdict"], "PASS")
            self.assertTrue(payload["final_toe_support_allowed"])
            result = module.evaluate_projection_lane(ROOT, lane_id, FINAL_TOE_PROJECTION_LANE_TARGETS[lane_id])
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["closure_verdict"], "PASS")
            self.assertTrue(result["final_toe_support_allowed"])
            self.assertEqual(result["finding_total"], 0)
            row = payload["rows"][0]
            self.assertNotIn("BLOCKER", row["claim_id"])
            self.assertNotIn("future", json.dumps(row, ensure_ascii=False).lower())
            self.assertNotIn("demoted", json.dumps(row, ensure_ascii=False).lower())

    def test_r017_toe_closure_factory_registry_is_decision_complete_and_no_fake_pass(self) -> None:
        factory_dir = ROOT / "operations" / "logion_release_mission" / "oc_core_1_3_3" / "toe_closure_factory"
        registry = read_json(factory_dir / "OC133_TOE_LANE_CAPABILITY_REGISTRY.json")
        state = read_json(factory_dir / "OC133_TOE_CLOSURE_STATE.json")

        self.assertEqual(registry["status"], "PASS")
        rows = {row["lane_id"]: row for row in registry["rows"]}
        for lane_id in [
            "AI",
            "ENTERPRISE_ARCHITECTURE",
            "GRAND_TOE_CLAIM_LEDGER_EVIDENCE",
            "MODERN_SCIENCE_COMPARATOR_SUPERIORITY",
            "CERBERUS_RELEASE_REVIEW_GATE",
        ]:
            self.assertIn(lane_id, rows)
            row = rows[lane_id]
            self.assertTrue(row["closure_condition"])
            self.assertTrue(row["required_artifacts"])
            self.assertTrue(row["execution_command"])
            self.assertTrue(row["validator_binding"])
            self.assertTrue(row["pass_predicate"])
            self.assertTrue(row["no_fake_closure_policy"])

        self.assertIn(state["status"], {"OPEN", "LOCAL_CAPABILITY_EXHAUSTED"})
        self.assertFalse(state["r017_promotion_allowed"])
        self.assertEqual(state["lane_registry_status"], "PASS")
        self.assertGreater(state["science_validator_error_total"], 0)
        self.assertGreater(state["cerberus_error_total"], 0)

    def test_r017_toe_closure_factory_ai_ea_lane_attempts_execute_diagnostics_instead_of_passing(self) -> None:
        factory_path = ROOT / "tools" / "oc133_toe_closure_factory.py"
        spec = importlib.util.spec_from_file_location("oc133_toe_closure_factory", factory_path)
        module = importlib.util.module_from_spec(spec)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        spec.loader.exec_module(module)

        for lane_id in ["AI", "ENTERPRISE_ARCHITECTURE"]:
            result = module.execute_lane_attempt(ROOT, lane_id, timeout=1)
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["execution_state"], "EXECUTED_PROJECTION_CAPABILITY")
            self.assertEqual(result["command_results"][0]["returncode"], 0)
            self.assertIn("subwork_order_total", result["command_results"][0]["stdout_tail"])
            self.assertIn("artifact_refs", result["command_results"][0]["stdout_tail"])
            self.assertTrue(json.loads(result["command_results"][0]["stdout_tail"])["projection_write_performed"])
            self.assertTrue(result["lane_result"]["final_toe_support_allowed"])
            self.assertIn("cannot count as TOE closure", result["no_fake_closure_policy"])

    def test_r017_toe_closure_factory_emits_root_cause_backlog_subwork_delta_trace_and_explainability_gate(self) -> None:
        factory_dir = ROOT / "operations" / "logion_release_mission" / "oc_core_1_3_3" / "toe_closure_factory"
        root_causes = read_json(factory_dir / "OC133_TOE_ROOT_CAUSE_LEDGER.json")
        backlog = read_json(factory_dir / "OC133_TOE_CAPABILITY_BACKLOG.json")
        subwork = read_json(factory_dir / "OC133_TOE_LANE_SUBWORK_ORDERS.json")
        delta = read_json(factory_dir / "OC133_TOE_VALIDATOR_DELTA_TRACE.json")
        explainability = read_json(factory_dir / "OC133_TOE_PROBLEM_EXPLAINABILITY_GATE.json")

        self.assertEqual(root_causes["root_cause_coverage_status"], "PASS")
        self.assertEqual(root_causes["toe_problem_explainability_status"], "PASS")
        self.assertGreater(root_causes["root_cause_total"], 0)
        self.assertEqual(root_causes["incomplete_root_cause_total"], 0)
        required = {
            "problem_id",
            "symptom",
            "root_cause_class",
            "root_cause_evidence",
            "why_it_failed",
            "repair_strategy",
            "required_capability",
            "execution_command",
            "pass_predicate",
            "expected_validator_delta",
            "actual_validator_delta",
            "next_escalation",
        }
        for row in root_causes["rows"]:
            self.assertTrue(required.issubset(row))
            for field in required:
                self.assertIsNotNone(row[field], field)
            self.assertTrue(row["why_it_failed"])
            self.assertTrue(row["repair_strategy"])

        self.assertEqual(backlog["status"], "OPEN")
        self.assertEqual(backlog["toe_problem_explainability_status"], "PASS")
        self.assertGreater(backlog["capability_total"], 0)
        for row in backlog["rows"]:
            if row["status"] != "PASS":
                for field in ["why_it_failed", "repair_strategy", "required_capability", "execution_command", "pass_predicate", "next_escalation"]:
                    self.assertTrue(row[field], field)
        backlog_capabilities = {row["required_capability"] for row in backlog["rows"]}
        self.assertIn("Research/FormalScience", backlog_capabilities)
        self.assertIn("Research/PriorArt", backlog_capabilities)

        self.assertEqual(subwork["status"], "OPEN")
        self.assertEqual(subwork["toe_problem_explainability_status"], "PASS")
        self.assertGreater(subwork["subwork_order_total"], 0)
        for row in subwork["rows"]:
            if row["status"] != "PASS":
                for field in ["why_it_failed", "repair_strategy", "required_capability", "execution_command", "pass_predicate", "next_escalation"]:
                    self.assertTrue(row[field], field)
        subwork_ids = {row["subwork_order_id"] for row in subwork["rows"]}
        self.assertTrue(any(row_id.startswith("R017-GRAND-") for row_id in subwork_ids))
        self.assertFalse(any(row_id.startswith("R017-FINITE-FAILURE-") for row_id in subwork_ids))
        self.assertTrue(any(row_id.startswith("R017-COMPARATOR-COVERAGE-GAP-") for row_id in subwork_ids))
        self.assertEqual(delta["no_progress_creates_backlog"], True)
        self.assertEqual(delta["toe_problem_explainability_status"], "PASS")
        self.assertEqual(explainability["toe_problem_explainability_status"], "PASS")
        self.assertEqual(explainability["missing_total"], 0)

    def test_r017_toe_closure_factory_materializes_executable_lane_artifacts(self) -> None:
        factory_dir = ROOT / "operations" / "logion_release_mission" / "oc_core_1_3_3" / "toe_closure_factory"
        ai = read_json(factory_dir / "lane_execution" / "AI" / "OC133_AI_PROJECTION_CAPABILITY_REPORT.json")
        ea = read_json(factory_dir / "lane_execution" / "ENTERPRISE_ARCHITECTURE" / "OC133_EA_PROJECTION_CAPABILITY_REPORT.json")
        grand = read_json(factory_dir / "lane_execution" / "GRAND_TOE_CLAIM_LEDGER_EVIDENCE" / "OC133_GRAND_PROMOTION_SUBLANE_DIAGNOSIS.json")
        comparator = read_json(factory_dir / "lane_execution" / "MODERN_SCIENCE_COMPARATOR_SUPERIORITY" / "OC133_MODERN_SCIENCE_BROAD_COVERAGE_WORK_ORDERS.json")
        comparator_execution = read_json(
            factory_dir
            / "lane_execution"
            / "MODERN_SCIENCE_COMPARATOR_SUPERIORITY"
            / "OC133_MODERN_SCIENCE_BROAD_COVERAGE_EXECUTION_REPORT.json"
        )

        for payload, lane_id in [(ai, "AI"), (ea, "ENTERPRISE_ARCHITECTURE")]:
            self.assertEqual(payload["lane_id"], lane_id)
            self.assertEqual(payload["status"], "PASS")
            self.assertTrue(payload["projection_write_performed"])
            refs = payload["artifact_refs"]
            for ref in [
                "claim_ledger_ref",
                "formal_boundary_map_ref",
                "proof_sheet_ref",
                "evidence_pack_ref",
                "evidence_or_simulation_pack_ref",
                "comparator_baselines_ref",
                "falsifier_ref",
                "falsifier_rows_ref",
                "candidate_projection_ref",
                "guarded_writer_report_ref",
                "source_mining_report_ref",
                "source_intake_work_orders_ref",
                "projection_support_pack_ref",
            ]:
                self.assertTrue((ROOT / refs[ref]).exists(), ref)
            self.assertTrue(payload["support_checks"]["claim_not_blocker"])
            self.assertTrue(payload["support_checks"]["source_mined_candidate_available"])
            self.assertTrue(payload["support_checks"]["lean_refs_exist"])
            self.assertTrue(payload["support_checks"]["finite_case_refs_present"])
            self.assertEqual(payload["source_intake_work_order_total"], 0)
            self.assertEqual(payload["missing_support_keys"], [])
            source_mining = read_json(ROOT / refs["source_mining_report_ref"])
            source_intake = read_json(ROOT / refs["source_intake_work_orders_ref"])
            support_pack = read_json(ROOT / refs["projection_support_pack_ref"])
            self.assertEqual(source_mining["status"], "PASS")
            self.assertGreater(source_mining["candidate_total"], 0)
            self.assertTrue(source_mining["deterministic_projection_template_enabled"])
            self.assertEqual(source_intake["status"], "PASS")
            self.assertEqual(source_intake["open_work_order_total"], 0)
            self.assertEqual(support_pack["status"], "PASS")
            self.assertGreater(support_pack["support_pass_candidate_total"], 0)
            for row in source_intake["rows"]:
                short_work_order_id = row["work_order_id"].replace(
                    "R017-ENTERPRISE_ARCHITECTURE-SOURCE-INTAKE-", "R017-EA-SI-"
                ).replace("R017-AI-SOURCE-INTAKE-", "R017-AI-SI-")
                execution_ref = (
                    factory_dir
                    / "lane_execution"
                    / lane_id
                    / "source_intake_executions"
                    / f"{short_work_order_id}.json"
                )
                self.assertTrue(execution_ref.exists(), row["work_order_id"])
                execution = read_json(execution_ref)
                self.assertEqual(execution["work_order_id"], row["work_order_id"])
                self.assertIn(execution["status"], {"SOURCE_GAP_OPEN", "PASS"})
                self.assertTrue((ROOT / execution["support_pack_ref"]).exists())

        self.assertEqual(grand["status"], "FAIL_CLOSED")
        self.assertEqual(grand["finite_regression_guard_status"], "PASS")
        self.assertEqual(grand["finite_failure_total"], 0)
        self.assertEqual(grand["finite_failure_ids"], [])
        self.assertTrue((ROOT / grand["promotion_execution_plan_ref"]).exists())
        self.assertTrue((ROOT / grand["promotion_derivation_report_ref"]).exists())
        grand_plan = read_json(ROOT / grand["promotion_execution_plan_ref"])
        grand_derivation = read_json(ROOT / grand["promotion_derivation_report_ref"])
        self.assertEqual(grand_plan["status"], "FAIL_CLOSED")
        self.assertEqual(grand_derivation["status"], "FAIL_CLOSED")
        self.assertFalse(grand_derivation["scorecard_write_performed"])
        self.assertGreater(grand_plan["open_prerequisite_total"], 0)
        self.assertTrue(any(row["predicate_id"] == "AI_projection_pass" and row["status"] == "PASS" for row in grand_plan["rows"]))
        self.assertTrue(any(row["predicate_id"] == "enterprise_architecture_projection_pass" and row["status"] == "PASS" for row in grand_plan["rows"]))
        self.assertTrue(any(row["predicate_id"] == "modern_science_superiority_certified" and row["status"] == "OPEN" for row in grand_plan["rows"]))
        self.assertEqual(comparator["status"], "OPEN")
        self.assertEqual(comparator["coverage_gap_total"], 35)
        self.assertTrue((ROOT / comparator["execution_report_ref"]).exists())
        self.assertEqual(comparator_execution["status"], "OPEN")
        self.assertEqual(comparator_execution["domain_job_total"], 12)
        self.assertEqual(comparator_execution["open_domain_job_total"], 12)
        self.assertEqual(comparator_execution["coverage_gap_total"], 35)
        self.assertEqual(comparator_execution["open_gap_total"], 35)
        self.assertFalse(comparator_execution["broad_pass_allowed"])
        for job in comparator_execution["job_rows"]:
            self.assertEqual(job["status"], "OPEN")
            self.assertFalse(job["source_capsule_verified"])
            self.assertFalse(job["benchmark_case_bound"])
            self.assertFalse(job["incumbent_comparator_bound"])
            self.assertFalse(job["oc_scoring_bound"])
            self.assertFalse(job["uncertainty_bound"])
            self.assertFalse(job["falsifier_bound"])
            self.assertFalse(job["replay_record_bound"])
            domain_job_ref = (
                factory_dir
                / "lane_execution"
                / "MODERN_SCIENCE_COMPARATOR_SUPERIORITY"
                / "domain_jobs"
                / f"{job['job_id']}.json"
            )
            self.assertTrue(domain_job_ref.exists(), job["job_id"])
            domain_job = read_json(domain_job_ref)
            self.assertEqual(domain_job["job_id"], job["job_id"])
            self.assertEqual(domain_job["status"], "OPEN")
            self.assertGreater(domain_job["open_gap_total"], 0)
            self.assertFalse(domain_job["broad_pass_allowed"])
            self.assertTrue(domain_job["missing_artifacts_by_gap"])
            self.assertTrue(domain_job["gap_execution_refs"])
            for gap_ref in domain_job["gap_execution_refs"].values():
                self.assertTrue((ROOT / gap_ref).exists(), gap_ref)
                gap_payload = read_json(ROOT / gap_ref)
                self.assertEqual(gap_payload["status"], "OPEN")
                self.assertGreater(gap_payload["missing_artifact_total"], 0)
                self.assertTrue(gap_payload["artifact_rows"])
        self.assertFalse(comparator["broad_claim_predicates"]["coverage_extends_to_all_of_modern_science"])

    def test_r017_modern_science_benchmark_scoped_superiority_does_not_count_as_broad_pass(self) -> None:
        register = read_json(ROOT / "comparators" / "OC_1_3_3_MODERN_SCIENCE_SUPERIORITY_REGISTER.json")
        self.assertEqual(register["modern_science_comparator_superiority"]["state"], "FAIL")
        self.assertEqual(register["benchmark_scoped_superiority_certified_total"], 4)
        self.assertEqual(register["broad_modern_science_superiority_certified_total"], 0)
        self.assertFalse(register["broad_claim_predicates"]["coverage_extends_to_all_of_modern_science"])

    def test_r017_toe_research_wave_executes_dependency_order_and_records_validator_deltas(self) -> None:
        factory_dir = ROOT / "operations" / "logion_release_mission" / "oc_core_1_3_3" / "toe_closure_factory"
        wave = read_json(factory_dir / "OC133_TOE_RESEARCH_WAVE_EXECUTION.json")

        self.assertEqual(wave["schema_id"], "OC133_TOE_RESEARCH_WAVE_EXECUTION_v1")
        self.assertEqual(wave["status"], "CAPABILITY_BACKLOG_OPEN")
        self.assertEqual(wave["toe_problem_explainability_status"], "PASS")
        self.assertGreater(wave["before_validator_error_total"], 0)
        self.assertGreater(wave["after_validator_error_total"], 0)
        self.assertFalse(wave["r017_promotion_allowed"])
        self.assertEqual(wave["supervisor_state"], "INTERNAL_RUN_STATE_CAPABILITY_BACKLOG_OPEN")
        self.assertGreaterEqual(wave["research_wave_step_total"], 10)

        purposes = [row["purpose"] for row in wave["rows"]]
        self.assertEqual(
            purposes[:10],
            [
                "sync_spot_before_research_wave",
                "ai_research_lane",
                "enterprise_architecture_research_lane",
                "modern_science_comparator_superiority_research_lane",
                "grand_toe_claim_ledger_evidence_research_lane",
                "sync_spot_after_research_lanes",
                "grand_science_scorecard_sync",
                "science_validator_before_cerberus",
                "canonical_cerberus_after_science_clear",
                "final_validator",
            ],
        )

        required = {
            "research_wave_step_id",
            "before_validator_error_total",
            "after_validator_error_total",
            "validator_error_delta",
            "changed_artifact_total",
            "changed_artifacts",
            "why_it_failed",
            "repair_strategy",
            "required_capability",
            "execution_command",
            "pass_predicate",
            "next_escalation",
        }
        for row in wave["rows"]:
            self.assertTrue(required.issubset(row))
            self.assertIsInstance(row["changed_artifacts"], list)
            self.assertIsNotNone(row["before_validator_error_total"])
            self.assertIsNotNone(row["after_validator_error_total"])
            self.assertIsNotNone(row["validator_error_delta"])
            if row["status"] != "PASS":
                for field in ["why_it_failed", "repair_strategy", "required_capability", "execution_command", "pass_predicate", "next_escalation"]:
                    self.assertTrue(row[field], field)

        rows = {row["purpose"]: row for row in wave["rows"]}
        self.assertEqual(rows["ai_research_lane"]["status"], "FAIL_CLOSED")
        self.assertFalse(rows["ai_research_lane"]["result"]["lane_result"]["final_toe_support_allowed"])
        self.assertEqual(rows["enterprise_architecture_research_lane"]["status"], "FAIL_CLOSED")
        self.assertFalse(rows["enterprise_architecture_research_lane"]["result"]["lane_result"]["final_toe_support_allowed"])
        self.assertEqual(rows["grand_toe_claim_ledger_evidence_research_lane"]["status"], "FAIL_CLOSED")
        grand_stdout = "\n".join(command["stdout_tail"] for command in rows["grand_toe_claim_ledger_evidence_research_lane"]["result"]["command_results"])
        self.assertIn('"finite_failure_ids": []', grand_stdout)
        self.assertIn('"diagnostic_status": "FAIL_CLOSED"', grand_stdout)
        comparator_stdout = "\n".join(command["stdout_tail"] for command in rows["modern_science_comparator_superiority_research_lane"]["result"]["command_results"])
        self.assertIn('"coverage_gap_total": 35', comparator_stdout)
        self.assertEqual(rows["canonical_cerberus_after_science_clear"]["status"], "SKIPPED_DETERMINISTIC_SCIENCE_BLOCKERS_REMAIN")
        self.assertIn("science validator remains red", rows["canonical_cerberus_after_science_clear"]["result"]["stderr_tail"])

    def test_r017_toe_closure_factory_artifacts_are_idempotent_and_checked(self) -> None:
        factory_dir = ROOT / "operations" / "logion_release_mission" / "oc_core_1_3_3" / "toe_closure_factory"
        cockpit = read_json(factory_dir / "OC133_TOE_CLOSURE_COCKPIT.json")
        obligations = read_json(factory_dir / "OC133_TOE_CLOSURE_OBLIGATIONS.json")
        lanes = read_json(factory_dir / "OC133_TOE_LANE_RESULTS.json")
        registry = read_json(factory_dir / "OC133_TOE_LANE_CAPABILITY_REGISTRY.json")
        state = read_json(factory_dir / "OC133_TOE_CLOSURE_STATE.json")
        root_causes = read_json(factory_dir / "OC133_TOE_ROOT_CAUSE_LEDGER.json")
        backlog = read_json(factory_dir / "OC133_TOE_CAPABILITY_BACKLOG.json")
        subwork = read_json(factory_dir / "OC133_TOE_LANE_SUBWORK_ORDERS.json")
        delta = read_json(factory_dir / "OC133_TOE_VALIDATOR_DELTA_TRACE.json")
        explainability = read_json(factory_dir / "OC133_TOE_PROBLEM_EXPLAINABILITY_GATE.json")
        research_wave = read_json(factory_dir / "OC133_TOE_RESEARCH_WAVE_EXECUTION.json")

        self.assertEqual(cockpit["current_promotion_gate"], "R017_BLOCKED_BY_TOE_CLOSURE_FACTORY")
        self.assertFalse(cockpit["r017_promotion_allowed"])
        self.assertEqual(obligations["status"], "OPEN")
        self.assertEqual(lanes["status"], "FAIL")
        self.assertEqual(registry["status"], "PASS")
        self.assertEqual(root_causes["root_cause_coverage_status"], "PASS")
        self.assertEqual(backlog["status"], "OPEN")
        self.assertEqual(subwork["status"], "OPEN")
        self.assertIn(delta["status"], {"PROGRESS_REMAINS_BLOCKED", "CAPABILITY_BACKLOG_OPEN"})
        self.assertEqual(explainability["toe_problem_explainability_status"], "PASS")
        self.assertEqual(research_wave["toe_problem_explainability_status"], "PASS")
        self.assertEqual(cockpit["research_wave_status"], research_wave["status"])
        self.assertEqual(cockpit["research_wave_step_total"], research_wave["research_wave_step_total"])
        self.assertEqual(cockpit["research_wave_validator_delta"], research_wave["validator_error_delta"])
        self.assertIn(state["status"], {"OPEN", "LOCAL_CAPABILITY_EXHAUSTED"})
        self.assertEqual(cockpit["validator_error_total"], obligations["validator_error_total"])
        self.assertEqual(cockpit["open_obligation_total"], obligations["open_work_order_total"])
        self.assertEqual(cockpit["fail_lane_total"], lanes["fail_lane_total"])
        self.assertEqual(cockpit["science_validator_error_total"], state["science_validator_error_total"])
        self.assertEqual(cockpit["cerberus_error_total"], state["cerberus_error_total"])
        self.assertEqual(cockpit["root_cause_total"], root_causes["root_cause_total"])
        self.assertEqual(cockpit["capability_backlog_total"], backlog["capability_total"])
        self.assertEqual(cockpit["lane_subwork_order_total"], subwork["subwork_order_total"])
        self.assertEqual(cockpit["toe_problem_explainability_status"], "PASS")
        if cockpit["execution_step_total"]:
            trace_rows = list(cockpit["execution_trace"])
            if trace_rows and trace_rows[0]["purpose"].startswith("until_final_pass_iteration_"):
                trace_rows = trace_rows[0]["result"]["cycle_trace"]
            if trace_rows and trace_rows[0]["purpose"].startswith("research_wave"):
                trace_rows = trace_rows[0]["result"]["wave_trace"]
            trace_by_purpose = {row["purpose"]: row for row in trace_rows}
            self.assertIn("science_validator_before_cerberus", trace_by_purpose)
            self.assertIn("canonical_cerberus_after_science_clear", trace_by_purpose)
            self.assertEqual(trace_by_purpose["science_validator_before_cerberus"]["status"], "FAIL_CLOSED")
            self.assertEqual(
                trace_by_purpose["canonical_cerberus_after_science_clear"]["status"],
                "SKIPPED_DETERMINISTIC_SCIENCE_BLOCKERS_REMAIN",
            )
            self.assertIn(
                "expensive Cerberus/LLM gate is not run",
                trace_by_purpose["canonical_cerberus_after_science_clear"]["result"]["stderr_tail"],
            )

    def test_r017_autonomous_supervisor_keeps_zero_delta_run_open_and_escalates(self) -> None:
        supervisor_dir = (
            ROOT
            / "operations"
            / "logion_release_mission"
            / "oc_core_1_3_3"
            / "toe_closure_factory"
            / "autonomous_supervisor"
        )
        state = read_json(supervisor_dir / "OC133_TOE_AUTONOMOUS_SUPERVISOR_STATE.json")
        cockpit = read_json(supervisor_dir / "OC133_TOE_AUTONOMOUS_COCKPIT.json")
        waves = read_json(supervisor_dir / "OC133_TOE_AUTONOMOUS_WAVE_LEDGER.json")
        queue = read_json(supervisor_dir / "OC133_TOE_AUTONOMOUS_NEXT_ACTION_QUEUE.json")
        escalation = read_json(supervisor_dir / "OC133_TOE_AUTONOMOUS_CAPABILITY_ESCALATION_LEDGER.json")
        capability_development = read_json(supervisor_dir / "OC133_TOE_AUTONOMOUS_CAPABILITY_DEVELOPMENT_LEDGER.json")
        frontier = read_json(supervisor_dir / "OC133_TOE_AUTONOMOUS_FRONTIER_HASHES.json")
        terminal = read_json(supervisor_dir / "OC133_TOE_AUTONOMOUS_TERMINAL_VALIDATION_REPORT.json")
        heartbeat = read_json(supervisor_dir / "OC133_TOE_AUTONOMOUS_HEARTBEAT.json")
        factory_dir = ROOT / "operations" / "logion_release_mission" / "oc_core_1_3_3" / "toe_closure_factory"
        registry = read_json(factory_dir / "OC133_TOE_CAPABILITY_IMPLEMENTATION_REGISTRY.json")
        frontier_science = read_json(factory_dir / "OC133_TOE_SCIENTIFIC_FRONTIER.json")

        self.assertEqual(state["schema_id"], "OC133_TOE_AUTONOMOUS_SUPERVISOR_STATE_v1")
        self.assertEqual(state["status"], "INTERNAL_AUTONOMOUS_RUN_STATE_OPEN")
        self.assertFalse(state["r017_promotion_allowed"])
        self.assertFalse(state["terminal_stop_on_zero_delta"])
        self.assertEqual(state["zero_delta_continue_policy"], "PASS")
        self.assertGreaterEqual(state["iteration_total"], 1)
        self.assertEqual(state["graph_resolver_status"], "PASS")
        self.assertIsNotNone(state["current_graph_node_id"])
        self.assertIsNotNone(state["active_executor"])
        self.assertEqual(state["last_validator_delta"], 0)
        self.assertEqual(cockpit["current_promotion_gate"], "R017_BLOCKED_BY_TOE_AUTONOMOUS_SUPERVISOR")
        self.assertEqual(cockpit["validator_error_total"], state["validator_error_total"])
        self.assertEqual(cockpit["worktree_gate_status"], "PASS")
        self.assertEqual(cockpit["current_graph_node_id"], state["current_graph_node_id"])
        self.assertEqual(cockpit["active_executor"], state["active_executor"])

        self.assertEqual(waves["schema_id"], "OC133_TOE_AUTONOMOUS_WAVE_LEDGER_v1")
        self.assertGreaterEqual(waves["wave_total"], 1)
        self.assertFalse(waves["terminal_stop_on_zero_delta"])
        self.assertTrue(all(row["validator_error_delta"] == 0 for row in waves["rows"][:2]))
        self.assertTrue(all(row["terminal_gate"] == "R017_BLOCKED_BY_TOE_AUTONOMOUS_SUPERVISOR" for row in waves["rows"]))
        self.assertTrue(any(row["selected_action_ids"] for row in waves["rows"]))
        self.assertTrue(any(row["selected_graph_node_ids"] for row in waves["rows"]))
        self.assertTrue(all(row["executor_selected"] == "graph_resolver" for row in waves["rows"]))
        self.assertTrue(any(
            validation["status"] == "SKIPPED_DETERMINISTIC_SCIENCE_BLOCKERS_REMAIN"
            for row in waves["rows"]
            for validation in row["validation_rows"]
            if validation["purpose"] == "canonical_cerberus_after_science_clear"
        ))

        self.assertEqual(queue["schema_id"], "OC133_TOE_AUTONOMOUS_NEXT_ACTION_QUEUE_v1")
        self.assertEqual(queue["status"], "OPEN")
        self.assertEqual(queue["planner_mode"], "GRAPH_RESOLVER")
        self.assertGreater(queue["graph_candidate_node_total"], 0)
        self.assertTrue(queue["selected_graph_node_ids"])
        self.assertGreater(queue["action_total"], 0)
        self.assertTrue(any(row["lane_id"] == "MODERN_SCIENCE_COMPARATOR_SUPERIORITY" for row in queue["rows"]))
        subartifact_batch = read_json(
            factory_dir
            / "lane_execution"
            / "MODERN_SCIENCE_COMPARATOR_SUPERIORITY"
            / "OC133_MODERN_SCIENCE_COMPARATOR_SCORING_SUBARTIFACT_BATCH.json"
        )
        self.assertEqual(subartifact_batch["schema_id"], "OC133_MODERN_SCIENCE_COMPARATOR_SCORING_SUBARTIFACT_BATCH_v1")
        self.assertGreater(subartifact_batch["subartifact_execution_total"], 0)
        self.assertFalse(any(row["lane_id"] == "AI" and row.get("status") != "PASS" for row in queue["rows"]))
        self.assertFalse(any(row["lane_id"] == "ENTERPRISE_ARCHITECTURE" and row.get("status") != "PASS" for row in queue["rows"]))
        self.assertTrue(any(row["lane_id"] == "MODERN_SCIENCE_COMPARATOR_SUPERIORITY" for row in queue["rows"]))
        self.assertTrue(all(row["planner_mode"] == "GRAPH_RESOLVER" for row in queue["rows"]))
        self.assertTrue(all(row.get("graph_node_id") for row in queue["rows"]))
        self.assertFalse(queue["terminal_stop_on_zero_delta"])

        self.assertEqual(escalation["status"], "OPEN")
        self.assertGreater(escalation["capability_escalation_total"], 0)
        self.assertTrue(escalation["zero_delta_creates_capability_work"])
        for row in escalation["rows"]:
            self.assertIn(row["status"], {"OPEN", "PASS"})
            if row["status"] == "PASS":
                self.assertTrue(
                    row.get("superseded_by_current_validator")
                    or row.get("superseded_by_research_artifact")
                    or row.get("superseded_by_research_artifact_packet")
                    or row.get("superseded_by_scoring_work_order")
                    or row.get("superseded_by_scoring_subartifact_execution")
                    or row.get("superseded_by_grand_promotion_derivation_report")
                    or row.get("superseded_by_source_executor_work_order")
                    or row.get("superseded_by_source_implementation_backlog")
                    or row.get("superseded_by_source_implementation_report")
                    or row.get("superseded_by_domain_scorer_implementation_backlog")
                    or row.get("superseded_by_domain_scorer_implementation_report")
                    or row.get("superseded_by_domain_model_repair_backlog")
                    or row.get("superseded_by_domain_model_repair_report")
                    or row.get("superseded_by_domain_model_component_implementation_backlog")
                    or row.get("superseded_by_domain_model_component_implementation_report")
                    or row.get("superseded_by_component_source_obligation_backlog")
                    or row.get("superseded_by_component_source_obligation_report")
                )
            for field in ["why_it_failed", "repair_strategy", "required_capability", "execution_command", "pass_predicate", "next_escalation"]:
                self.assertIn(field, row)
                self.assertIsNotNone(row[field])

        self.assertEqual(capability_development["schema_id"], "OC133_TOE_AUTONOMOUS_CAPABILITY_DEVELOPMENT_LEDGER_v1")
        self.assertEqual(capability_development["status"], "OPEN")
        self.assertGreater(capability_development["capability_development_total"], 0)
        self.assertTrue(capability_development["zero_delta_creates_capability_work"])
        keys = [row["capability_development_key"] for row in capability_development["rows"]]
        self.assertEqual(len(keys), len(set(keys)))
        for row in capability_development["rows"]:
            self.assertIn(row["status"], {"OPEN", "PASS"})
            if row["status"] == "PASS":
                self.assertTrue(
                    row.get("superseded_by_current_validator")
                    or row.get("superseded_by_research_artifact")
                    or row.get("superseded_by_research_artifact_packet")
                    or row.get("superseded_by_scoring_work_order")
                    or row.get("superseded_by_scoring_subartifact_execution")
                    or row.get("superseded_by_grand_promotion_derivation_report")
                    or row.get("superseded_by_source_executor_work_order")
                    or row.get("superseded_by_source_implementation_backlog")
                    or row.get("superseded_by_source_implementation_report")
                    or row.get("superseded_by_domain_scorer_implementation_backlog")
                    or row.get("superseded_by_domain_scorer_implementation_report")
                    or row.get("superseded_by_domain_model_repair_backlog")
                    or row.get("superseded_by_domain_model_repair_report")
                    or row.get("superseded_by_domain_model_component_implementation_backlog")
                    or row.get("superseded_by_domain_model_component_implementation_report")
                    or row.get("superseded_by_component_source_obligation_backlog")
                    or row.get("superseded_by_component_source_obligation_report")
                )
            for field in ["source_graph_node_id", "missing_artifact_type", "capability_development_key", "why_it_failed", "repair_strategy", "required_capability", "execution_command", "implementation_command", "pass_predicate", "next_escalation", "validator_binding"]:
                self.assertIn(field, row)
                self.assertIsNotNone(row[field], field)
        self.assertTrue(any(row["capability_executor_ready"] for row in capability_development["rows"]))
        self.assertEqual(registry["schema_id"], "OC133_TOE_CAPABILITY_IMPLEMENTATION_REGISTRY_v1")
        self.assertGreater(registry["compiled_capability_total"], 0)
        self.assertEqual(registry["compiled_capability_total"], registry["ready_capability_total"] + registry["blocked_capability_total"])
        for row in registry["rows"]:
            self.assertEqual(row["capability_id"], row["compiled_capability_id"])
            self.assertEqual(row["capability_class"], row["executor_type"])
            self.assertTrue(row["capability_id"].startswith("R017-CAPDEV-"))
            self.assertTrue(row["capability_class"])
        self.assertTrue(any(row["capability_class"] in {"comparator_scoring_work_order", "comparator_source_implementation_obligation", "comparator_research_artifact_repair", "comparator_domain_scorer_implementation", "comparator_domain_model_repair", "comparator_domain_model_component_backlog", "comparator_domain_model_component", "comparator_domain_model_component_implementation_backlog", "comparator_domain_model_component_implementation", "comparator_component_source_obligation_backlog", "comparator_component_source_obligation"} for row in registry["rows"]))
        self.assertEqual(frontier_science["schema_id"], "OC133_TOE_SCIENTIFIC_FRONTIER_v1")
        self.assertIn("excludes supervisor bookkeeping", frontier_science["frontier_policy"])

        self.assertEqual(frontier["status"], "PASS")
        self.assertEqual(frontier["frontier_row_total"], waves["wave_total"])
        self.assertEqual(heartbeat["schema_id"], "OC133_TOE_AUTONOMOUS_HEARTBEAT_v1")
        self.assertEqual(heartbeat["current_graph_node_id"], state["current_graph_node_id"])
        self.assertEqual(heartbeat["active_executor"], state["active_executor"])
        self.assertEqual(terminal["status"], "BLOCKED")
        self.assertFalse(terminal["final_validator_passed"])
        self.assertFalse(terminal["r017_assembly_attempted"])

    def test_r017_autonomous_supervisor_materializes_blocking_graph_and_support_index(self) -> None:
        factory_dir = ROOT / "operations" / "logion_release_mission" / "oc_core_1_3_3" / "toe_closure_factory"
        graph = read_json(factory_dir / "OC133_TOE_BLOCKING_GRAPH.json")
        support = read_json(factory_dir / "OC133_TOE_SUPPORT_REFERENCE_INDEX.json")
        scientific_frontier = read_json(factory_dir / "OC133_TOE_SCIENTIFIC_FRONTIER.json")
        capability_registry = read_json(factory_dir / "OC133_TOE_CAPABILITY_IMPLEMENTATION_REGISTRY.json")
        cockpit = read_json(factory_dir / "autonomous_supervisor" / "OC133_TOE_AUTONOMOUS_COCKPIT.json")
        queue = read_json(factory_dir / "autonomous_supervisor" / "OC133_TOE_AUTONOMOUS_NEXT_ACTION_QUEUE.json")
        capability_development = read_json(factory_dir / "autonomous_supervisor" / "OC133_TOE_AUTONOMOUS_CAPABILITY_DEVELOPMENT_LEDGER.json")

        self.assertEqual(support["schema_id"], "OC133_TOE_SUPPORT_REFERENCE_INDEX_v1")
        self.assertEqual(support["status"], "PASS")
        self.assertGreater(support["lean_symbol_total"], 0)
        self.assertGreater(support["indexed_lean_ref_total"], 0)
        self.assertGreater(support["bound_lean_ref_total"], 0)
        self.assertGreater(support["finite_case_total"], 0)
        self.assertGreater(support["passing_finite_case_total"], 0)
        self.assertGreater(support["existing_source_ref_total"], 0)
        self.assertIn("no fake", support["no_fake_closure_policy"].lower())
        self.assertEqual(scientific_frontier["schema_id"], "OC133_TOE_SCIENTIFIC_FRONTIER_v1")
        self.assertGreater(scientific_frontier["validator_error_total"], 0)
        self.assertEqual(capability_registry["schema_id"], "OC133_TOE_CAPABILITY_IMPLEMENTATION_REGISTRY_v1")
        self.assertGreater(capability_registry["compiled_capability_total"], 0)
        self.assertTrue(all(row["execution_command"] for row in capability_registry["rows"]))
        self.assertTrue(all(row["self_test_command"] for row in capability_registry["rows"]))
        self.assertTrue(all(row["capability_id"] == row["compiled_capability_id"] for row in capability_registry["rows"]))
        self.assertTrue(all(row["capability_class"] == row["executor_type"] for row in capability_registry["rows"]))
        self.assertTrue(any(row["capability_class"] in {"comparator_scoring_work_order", "comparator_source_implementation_obligation", "comparator_research_artifact_repair", "comparator_domain_scorer_implementation", "comparator_domain_model_repair", "comparator_domain_model_component_backlog", "comparator_domain_model_component", "comparator_domain_model_component_implementation_backlog", "comparator_domain_model_component_implementation", "comparator_component_source_obligation_backlog", "comparator_component_source_obligation"} for row in capability_registry["rows"]))

        self.assertEqual(graph["schema_id"], "OC133_TOE_BLOCKING_GRAPH_v1")
        self.assertEqual(graph["status"], "OPEN")
        self.assertGreater(graph["validator_error_total"], 0)
        self.assertGreater(graph["open_node_total"], 0)
        self.assertGreater(graph["edge_total"], 0)
        self.assertFalse(cockpit["r017_promotion_allowed"])
        self.assertEqual(cockpit["blocking_graph_status"], graph["status"])
        self.assertEqual(cockpit["blocking_graph_open_node_total"], graph["open_node_total"])
        self.assertEqual(cockpit["blocking_graph_frontier_hash"], graph["graph_frontier_hash"])
        self.assertEqual(cockpit["support_reference_index_status"], "PASS")
        self.assertEqual(queue["blocking_graph_ref"], "operations/logion_release_mission/oc_core_1_3_3/toe_closure_factory/OC133_TOE_BLOCKING_GRAPH.json")

        node_types = {row["node_type"] for row in graph["nodes"]}
        for node_type in ["validator_error", "closure_lane", "required_artifact", "executor_capability", "capability_development", "generated_evidence", "r017_promotion_gate"]:
            self.assertIn(node_type, node_types)
        edge_types = {row["edge_type"] for row in graph["edges"]}
        for edge_type in ["blocks", "requires", "produces", "validated_by", "needs_capability"]:
            self.assertIn(edge_type, edge_types)
        self.assertIn("supersedes", edge_types)
        open_nodes = [row for row in graph["nodes"] if row["status"] != "PASS"]
        self.assertTrue(open_nodes)
        for row in open_nodes:
            for field in ["why_it_failed", "repair_strategy", "required_capability", "execution_command", "pass_predicate", "next_escalation", "validator_binding"]:
                self.assertIn(field, row)
                self.assertIsNotNone(row[field], field)
        self.assertTrue(any(
            row["node_type"] == "required_artifact"
            and str(row["node_id"]).startswith("required_artifact:MODERN_SCIENCE_COMPARATOR_SUPERIORITY:")
            for row in graph["nodes"]
        ))
        self.assertTrue(any(
            str(node_id).startswith("required_artifact:MODERN_SCIENCE_COMPARATOR_SUPERIORITY:")
            or str(node_id).startswith("capability_development:")
            or str(node_id).startswith("capability:AUTO-R017-COMPARATOR-GAP-")
            or str(node_id).startswith("capability:AUTO-capability_development-")
            for node_id in graph["next_executable_node_ids"]
        ))
        self.assertTrue(any(str(row["node_id"]).startswith("capability_development:") for row in graph["nodes"]))
        self.assertEqual(capability_development["open_capability_development_total"], cockpit["open_capability_development_total"])
        self.assertTrue(any(row["lane_id"] == "CERBERUS_RELEASE_REVIEW_GATE" for row in graph["nodes"] if row["node_type"] == "closure_lane"))

    def test_r017_autonomous_supervisor_graph_resolver_does_not_repeat_same_frontier_action(self) -> None:
        tools_dir = ROOT / "tools"
        if str(tools_dir) not in sys.path:
            sys.path.insert(0, str(tools_dir))
        import oc133_toe_autonomous_supervisor as supervisor

        frontier_hash = supervisor.semantic_frontier_hash(ROOT)
        initial_queue = supervisor.plan_next_actions(ROOT, {"attempted_action_signatures": []}, frontier_hash)
        action_ids = [row["action_id"] for row in initial_queue["rows"] if row.get("execution_command")]
        self.assertTrue(action_ids)
        repeated_state = {
            "attempted_action_signatures": [f"{frontier_hash}::{action_id}" for action_id in action_ids],
        }
        repeated_queue = supervisor.plan_next_actions(ROOT, repeated_state, frontier_hash)
        selected = supervisor.select_actions(repeated_queue, 12)

        self.assertEqual(repeated_queue["planner_mode"], "GRAPH_RESOLVER")
        self.assertTrue(all(row["already_attempted_on_frontier"] for row in repeated_queue["rows"] if row.get("execution_command")))
        self.assertFalse(selected)
        self.assertTrue(any(row["status"] == "CAPABILITY_ESCALATION_REQUIRED" for row in repeated_queue["rows"]))

    def test_medical_modern_science_gaps_have_executable_fail_closed_specs(self) -> None:
        queue = read_json(ROOT / "reports" / "OC_CORE_1_3_3_MODERN_SCIENCE_COVERAGE_LANE_QUEUE.json")
        backlog = read_json(
            ROOT
            / "operations"
            / "logion_release_mission"
            / "oc_core_1_3_3"
            / "toe_closure_factory"
            / "lane_execution"
            / "MODERN_SCIENCE_COMPARATOR_SUPERIORITY"
            / "OC133_MODERN_SCIENCE_COMPARATOR_SCORING_EXECUTOR_BACKLOG.json"
        )
        medical_lanes = [
            row
            for row in queue["lanes"]
            if row["domain_class_id"] == "medical_health_sciences"
        ]

        self.assertEqual(len(medical_lanes), 3)
        for row in medical_lanes:
            spec = row.get("executable_work_order")
            self.assertIsInstance(spec, dict)
            self.assertEqual(spec["domain_class_id"], "medical_health_sciences")
            self.assertTrue(str(spec["coverage_closure_status"]).startswith("OPEN_FAIL_CLOSED"))
            self.assertFalse(spec["current_evidence"]["executable_evidence_exists"])
            self.assertEqual(row["execution_state"], "FAIL_CLOSED_EXECUTABLE_SPEC_READY_EVIDENCE_MISSING")
            self.assertIn("EXECUTABLE_LANE_SPEC_DECLARED", row["expected_acceptance_predicates"])
            self.assertIn("FAIL_CLOSED_UNLESS_EXECUTABLE_EVIDENCE_BOUND", row["expected_acceptance_predicates"])

        medical_root_causes = {
            row["root_cause_class"]
            for row in backlog["rows"]
            if row["domain_class_id"] == "medical_health_sciences"
        }
        self.assertEqual(medical_root_causes, {"SCORING_EVIDENCE_NOT_MATERIALIZED"})
        self.assertNotIn("EXECUTABLE_SPEC_MISSING_FOR_SCORING", backlog["root_cause_counts"])
        for row in backlog["rows"]:
            if row["missing_artifact_type"] == "oc_prediction_scoring_row":
                self.assertIn("--execute-comparator-scoring-work-order", row["execution_command"])
            self.assertIn("scoring_subartifact_id", row)
            self.assertIn("--execute-comparator-scoring-work-order", row["execution_command"])

        artifact_root = ROOT / "validation" / "heldout" / "grand_science" / "modern_science_coverage_artifacts"
        open_replay_records = [
            read_json(path)
            for path in artifact_root.glob("*/replay_record.json")
            if read_json(path).get("status") == "OPEN"
        ]
        self.assertTrue(open_replay_records)
        self.assertTrue(all(row.get("validation") for row in open_replay_records))

    def test_r017_comparator_source_implementation_frontier_is_concrete_and_fail_closed(self) -> None:
        factory_root = (
            ROOT
            / "operations"
            / "logion_release_mission"
            / "oc_core_1_3_3"
            / "toe_closure_factory"
            / "lane_execution"
            / "MODERN_SCIENCE_COMPARATOR_SUPERIORITY"
        )
        backlog = read_json(factory_root / "SOURCE_IMPL_BACKLOG.json")
        registry = read_json(factory_root / "SOURCE_IMPLEMENTATION_REGISTRY.json")
        batch = read_json(factory_root / "OC133_MODERN_SCIENCE_COMPARATOR_SOURCE_IMPLEMENTATION_BATCH.json")
        report_rows = [
            read_json(path)
            for path in (factory_root / "source_implementations").glob("*.json")
        ]

        self.assertEqual(backlog["schema_id"], "OC133_MODERN_SCIENCE_COMPARATOR_SOURCE_IMPLEMENTATION_BACKLOG_v1")
        self.assertIn(backlog["status"], {"OPEN", "PASS"})
        for row in backlog["rows"]:
            self.assertIn("implementation_id", row)
            self.assertIn("domain_class_id", row)
            self.assertIn("phenomenon_class_id", row)
            self.assertIn("scoring_subartifact_id", row)
            self.assertIn("--execute-comparator-source-implementation", row["execution_command"])
            self.assertIn("no_fake_closure_policy", row)

        self.assertEqual(registry["schema_id"], "OC133_MODERN_SCIENCE_COMPARATOR_SOURCE_IMPLEMENTATION_REGISTRY_v1")
        self.assertEqual(registry["implementation_total"], backlog["implementation_work_order_total"])
        self.assertEqual(registry["open_implementation_total"], len([row for row in registry["rows"] if row["status"] != "PASS"]))
        self.assertEqual(batch["schema_id"], "OC133_MODERN_SCIENCE_COMPARATOR_SOURCE_IMPLEMENTATION_BATCH_v1")
        self.assertIn("never promotes broad superiority", batch["no_fake_closure_policy"])

        concrete_reports = [
            row
            for row in report_rows
            if row.get("status") == "PASS" and row.get("implementation_command_class") == "CONCRETE_SOURCE_EXECUTOR"
        ]
        self.assertGreater(len(concrete_reports), 0)
        self.assertTrue(all(row.get("scientific_closure_status") in {"PASS", "OPEN"} for row in concrete_reports))
        capability_gaps = [
            row
            for row in report_rows
            if row.get("status") == "CAPABILITY_DEVELOPMENT_REQUIRED"
        ]
        self.assertEqual(len(capability_gaps), 0)
        self.assertTrue(all(row.get("implementation_command_class") == "MISSING_CONCRETE_SOURCE_EXECUTOR" for row in capability_gaps))
        self.assertTrue(all(row.get("scientific_closure_status") == "OPEN" for row in capability_gaps))
        self.assertTrue(any(row.get("scientific_closure_status") == "OPEN" for row in concrete_reports))
        self.assertTrue(all(row.get("no_fake_closure_policy") for row in report_rows))

    def test_r017_comparator_domain_scorer_implementation_frontier_is_exact_and_fail_closed(self) -> None:
        factory_root = (
            ROOT
            / "operations"
            / "logion_release_mission"
            / "oc_core_1_3_3"
            / "toe_closure_factory"
            / "lane_execution"
            / "MODERN_SCIENCE_COMPARATOR_SUPERIORITY"
        )
        backlog = read_json(factory_root / "DOMAIN_SCORER_IMPLEMENTATION_BACKLOG.json")
        batch = read_json(factory_root / "DOMAIN_SCORER_IMPLEMENTATION_BATCH.json")
        reports = [
            read_json(path)
            for path in (factory_root / "domain_scorer_implementations").glob("*.json")
        ]

        self.assertEqual(backlog["schema_id"], "OC133_MODERN_SCIENCE_COMPARATOR_DOMAIN_SCORER_IMPLEMENTATION_BACKLOG_v1")
        self.assertEqual(backlog["status"], "OPEN")
        self.assertGreater(backlog["domain_scorer_implementation_total"], 0)
        self.assertEqual(backlog["open_domain_scorer_implementation_total"], len([row for row in backlog["rows"] if row["status"] != "PASS"]))
        for row in backlog["rows"]:
            self.assertIn("implementation_id", row)
            self.assertIn("domain_scoring_id", row)
            self.assertIn("expected_script_ref", row)
            self.assertIn("missing_domain_scorer_elements", row)
            self.assertIn("--execute-comparator-domain-scorer-implementation", row["execution_command"])
            self.assertTrue(row["no_fake_closure_policy"])

        self.assertEqual(batch["schema_id"], "OC133_MODERN_SCIENCE_COMPARATOR_DOMAIN_SCORER_IMPLEMENTATION_BATCH_v1")
        self.assertEqual(batch["executed_total"], backlog["domain_scorer_implementation_total"])
        self.assertIn("never promotes broad superiority", batch["no_fake_closure_policy"])
        self.assertEqual(len(reports), backlog["domain_scorer_implementation_total"])
        self.assertTrue(all(row["status"] in {"PASS", "CAPABILITY_DEVELOPMENT_REQUIRED", "EVIDENCE_REPAIR_ATTEMPTED_REMAINS_OPEN", "FAIL_CLOSED"} for row in reports))
        self.assertTrue(all(row.get("implementation_command_class") for row in reports))
        self.assertTrue(all(row.get("domain_scoring_status") in {"PASS", "CAPABILITY_DEVELOPMENT_REQUIRED", "EVIDENCE_REPAIR_ATTEMPTED_REMAINS_OPEN", "FAIL_CLOSED"} for row in reports))
        self.assertTrue(all(row.get("scoring_artifact_status") in {"PASS", "OPEN"} for row in reports))
        self.assertTrue(any(row.get("status") == "EVIDENCE_REPAIR_ATTEMPTED_REMAINS_OPEN" for row in reports))
        self.assertTrue(
            all(
                row.get("status") != "PASS"
                or row.get("scoring_artifact_status") == "PASS"
                for row in reports
            )
        )
        self.assertTrue(
            any(
                row.get("root_cause_class") == "DOMAIN_SCORER_MODEL_OR_COMPARATOR_REPAIR_REQUIRED"
                for row in reports
            )
        )
        self.assertTrue(any(row.get("root_cause_class") in {"DOMAIN_SCORER_SCRIPT_ROUTE_MISSING", "DOMAIN_SCORER_FLAGS_MISSING", "DOMAIN_SCORER_MODEL_OR_COMPARATOR_REPAIR_REQUIRED"} for row in reports))
        self.assertTrue(all(row.get("no_fake_closure_policy") for row in reports))

    def test_r017_comparator_domain_model_repair_frontier_is_componentized(self) -> None:
        factory_root = (
            ROOT
            / "operations"
            / "logion_release_mission"
            / "oc_core_1_3_3"
            / "toe_closure_factory"
            / "lane_execution"
            / "MODERN_SCIENCE_COMPARATOR_SUPERIORITY"
        )
        model_backlog = read_json(factory_root / "DOMAIN_MODEL_REPAIR_BACKLOG.json")
        model_batch = read_json(factory_root / "DOMAIN_MODEL_REPAIR_BATCH.json")
        component_backlog = read_json(factory_root / "DOMAIN_MODEL_COMPONENT_BACKLOG.json")
        component_batch = read_json(factory_root / "DOMAIN_MODEL_COMPONENT_BATCH.json")
        model_reports = [read_json(path) for path in (factory_root / "domain_model_repairs").glob("*.json")]
        component_reports = [read_json(path) for path in (factory_root / "domain_model_components").glob("*.json")]
        supervisor_queue = read_json(
            ROOT
            / "operations"
            / "logion_release_mission"
            / "oc_core_1_3_3"
            / "toe_closure_factory"
            / "autonomous_supervisor"
            / "OC133_TOE_AUTONOMOUS_NEXT_ACTION_QUEUE.json"
        )

        self.assertEqual(model_backlog["schema_id"], "OC133_MODERN_SCIENCE_COMPARATOR_DOMAIN_MODEL_REPAIR_BACKLOG_v1")
        self.assertEqual(model_backlog["status"], "OPEN")
        self.assertGreater(model_backlog["domain_model_repair_total"], 0)
        self.assertEqual(model_batch["schema_id"], "OC133_MODERN_SCIENCE_COMPARATOR_DOMAIN_MODEL_REPAIR_BATCH_v1")
        self.assertEqual(model_batch["executed_total"], model_backlog["domain_model_repair_total"])
        self.assertTrue(model_reports)
        self.assertTrue(all(row.get("status") in {"PASS", "EVIDENCE_REPAIR_ATTEMPTED_REMAINS_OPEN", "FAIL_CLOSED"} for row in model_reports))
        self.assertTrue(any(row.get("component_open_total", 0) > 0 for row in model_reports))
        self.assertTrue(all(row.get("no_fake_closure_policy") for row in model_reports))

        self.assertEqual(component_backlog["schema_id"], "OC133_MODERN_SCIENCE_COMPARATOR_DOMAIN_MODEL_COMPONENT_BACKLOG_v1")
        self.assertEqual(component_backlog["status"], "OPEN")
        self.assertGreater(component_backlog["domain_model_component_total"], model_backlog["domain_model_repair_total"])
        self.assertEqual(component_batch["schema_id"], "OC133_MODERN_SCIENCE_COMPARATOR_DOMAIN_MODEL_COMPONENT_BATCH_v1")
        self.assertGreater(component_batch["executed_total"], 0)
        self.assertTrue(component_reports)
        self.assertTrue(all(row.get("status") in {"PASS", "CAPABILITY_DEVELOPMENT_REQUIRED", "FAIL_CLOSED"} for row in component_reports))
        self.assertTrue(all(row.get("component_id") for row in component_reports))
        self.assertTrue(all(row.get("implementation_blueprint") for row in component_reports))
        self.assertTrue(all(row.get("no_fake_closure_policy") for row in component_reports))
        self.assertTrue(any(row.get("executor_type") in {"comparator_domain_model_component", "comparator_domain_model_component_implementation", "comparator_component_source_obligation"} for row in supervisor_queue["rows"]))

    def test_r017_comparator_domain_model_component_implementation_frontier_runs_commands(self) -> None:
        factory_root = (
            ROOT
            / "operations"
            / "logion_release_mission"
            / "oc_core_1_3_3"
            / "toe_closure_factory"
            / "lane_execution"
            / "MODERN_SCIENCE_COMPARATOR_SUPERIORITY"
        )
        component_backlog = read_json(factory_root / "DOMAIN_MODEL_COMPONENT_BACKLOG.json")
        implementation_backlog = read_json(factory_root / "DOMAIN_MODEL_COMPONENT_IMPLEMENTATION_BACKLOG.json")
        registry = read_json(factory_root / "DOMAIN_MODEL_COMPONENT_IMPLEMENTATION_REGISTRY.json")
        batch = read_json(factory_root / "DOMAIN_MODEL_COMPONENT_IMPLEMENTATION_BATCH.json")
        reports = [read_json(path) for path in (factory_root / "component_impls").glob("*.json")]
        supervisor_queue = read_json(
            ROOT
            / "operations"
            / "logion_release_mission"
            / "oc_core_1_3_3"
            / "toe_closure_factory"
            / "autonomous_supervisor"
            / "OC133_TOE_AUTONOMOUS_NEXT_ACTION_QUEUE.json"
        )

        self.assertEqual(implementation_backlog["schema_id"], "OC133_MODERN_SCIENCE_COMPARATOR_DOMAIN_MODEL_COMPONENT_IMPLEMENTATION_BACKLOG_v1")
        self.assertEqual(implementation_backlog["status"], "OPEN")
        self.assertEqual(
            implementation_backlog["domain_model_component_implementation_total"],
            component_backlog["domain_model_component_total"],
        )
        self.assertGreater(implementation_backlog["domain_model_component_implementation_total"], 0)
        self.assertTrue(any(row["concrete_command_available"] for row in implementation_backlog["rows"]))

        self.assertEqual(registry["schema_id"], "OC133_MODERN_SCIENCE_COMPARATOR_DOMAIN_MODEL_COMPONENT_IMPLEMENTATION_REGISTRY_v1")
        self.assertEqual(registry["implementation_total"], implementation_backlog["domain_model_component_implementation_total"])
        self.assertEqual(registry["open_implementation_total"], len([row for row in registry["rows"] if row["status"] != "PASS"]))
        self.assertGreater(registry["command_available_total"], 0)

        self.assertEqual(batch["schema_id"], "OC133_MODERN_SCIENCE_COMPARATOR_DOMAIN_MODEL_COMPONENT_IMPLEMENTATION_BATCH_v1")
        self.assertEqual(batch["executed_total"], implementation_backlog["domain_model_component_implementation_total"])
        self.assertGreater(batch["unique_command_total"], 0)
        self.assertIn("never promotes broad superiority", batch["no_fake_closure_policy"])

        self.assertTrue(reports)
        self.assertTrue(all(row.get("status") in {"PASS", "CAPABILITY_DEVELOPMENT_REQUIRED", "EVIDENCE_REPAIR_ATTEMPTED_REMAINS_OPEN", "FAIL_CLOSED"} for row in reports))
        self.assertTrue(all(row.get("implementation_command_class") for row in reports))
        self.assertTrue(all(row.get("command_result_total", 0) >= 0 for row in reports))
        self.assertTrue(all(row.get("no_fake_closure_policy") for row in reports))
        self.assertTrue(any(row.get("status") == "EVIDENCE_REPAIR_ATTEMPTED_REMAINS_OPEN" for row in reports))
        self.assertTrue(any(row.get("executor_type") in {"comparator_domain_model_component_implementation", "comparator_component_source_obligation"} for row in supervisor_queue["rows"]))

    def test_r017_comparator_component_source_obligation_frontier_is_narrowed(self) -> None:
        factory_root = (
            ROOT
            / "operations"
            / "logion_release_mission"
            / "oc_core_1_3_3"
            / "toe_closure_factory"
            / "lane_execution"
            / "MODERN_SCIENCE_COMPARATOR_SUPERIORITY"
        )
        backlog = read_json(factory_root / "COMPONENT_SOURCE_OBLIGATION_BACKLOG.json")
        registry = read_json(factory_root / "COMPONENT_SOURCE_OBLIGATION_REGISTRY.json")
        batch = read_json(factory_root / "COMPONENT_SOURCE_OBLIGATION_BATCH.json")
        reports = [
            read_json(path)
            for path in (factory_root / "component_src").glob("*.json")
        ]
        supervisor_queue = read_json(
            ROOT
            / "operations"
            / "logion_release_mission"
            / "oc_core_1_3_3"
            / "toe_closure_factory"
            / "autonomous_supervisor"
            / "OC133_TOE_AUTONOMOUS_NEXT_ACTION_QUEUE.json"
        )

        self.assertEqual(backlog["schema_id"], "OC133_MODERN_SCIENCE_COMPARATOR_COMPONENT_SOURCE_OBLIGATION_BACKLOG_v1")
        self.assertEqual(backlog["status"], "OPEN")
        self.assertGreater(backlog["component_source_obligation_total"], 0)
        self.assertEqual(backlog["open_component_source_obligation_total"], len([row for row in backlog["rows"] if row["status"] != "PASS"]))
        for row in backlog["rows"]:
            self.assertIn("obligation_id", row)
            self.assertIn("implementation_id", row)
            self.assertIn("component_id", row)
            self.assertIn("missing_source_evidence_fields", row)
            self.assertIn("official_data_source", row)
            self.assertIn("target_variable", row)
            self.assertIn("--execute-comparator-component-source-obligation", row["execution_command"])
            self.assertTrue(row["no_fake_closure_policy"])

        self.assertEqual(registry["schema_id"], "OC133_MODERN_SCIENCE_COMPARATOR_COMPONENT_SOURCE_OBLIGATION_REGISTRY_v1")
        self.assertEqual(registry["component_source_obligation_total"], backlog["component_source_obligation_total"])
        self.assertEqual(registry["open_component_source_obligation_total"], len([row for row in registry["rows"] if row["status"] != "PASS"]))
        self.assertEqual(batch["schema_id"], "OC133_MODERN_SCIENCE_COMPARATOR_COMPONENT_SOURCE_OBLIGATION_BATCH_v1")
        self.assertIn("never promotes broad superiority", batch["no_fake_closure_policy"])

        self.assertTrue(reports)
        self.assertTrue(all(row.get("status") in {"PASS", "CAPABILITY_DEVELOPMENT_REQUIRED", "SOURCE_BOUND_SCORING_MATERIALIZATION_REMAINS_OPEN", "FAIL_CLOSED"} for row in reports))
        self.assertTrue(all(row.get("missing_source_evidence_fields") is not None for row in reports))
        self.assertTrue(all(row.get("no_fake_closure_policy") for row in reports))
        self.assertTrue(any(row.get("status") == "SOURCE_BOUND_SCORING_MATERIALIZATION_REMAINS_OPEN" for row in reports))
        self.assertTrue(any(row.get("executor_type") == "comparator_component_source_obligation" for row in supervisor_queue["rows"]))

    def test_r017_comparator_open_research_artifacts_have_repair_frontier(self) -> None:
        factory_root = (
            ROOT
            / "operations"
            / "logion_release_mission"
            / "oc_core_1_3_3"
            / "toe_closure_factory"
            / "lane_execution"
            / "MODERN_SCIENCE_COMPARATOR_SUPERIORITY"
        )
        backlog = read_json(factory_root / "RESEARCH_ARTIFACT_REPAIR_BACKLOG.json")
        batch = read_json(factory_root / "REPAIR_BATCH.json")
        repair_rows = [read_json(path) for path in (factory_root / "repairs").glob("*.json")]
        supervisor_queue = read_json(
            ROOT
            / "operations"
            / "logion_release_mission"
            / "oc_core_1_3_3"
            / "toe_closure_factory"
            / "autonomous_supervisor"
            / "OC133_TOE_AUTONOMOUS_NEXT_ACTION_QUEUE.json"
        )

        self.assertEqual(backlog["schema_id"], "OC133_MODERN_SCIENCE_COMPARATOR_RESEARCH_ARTIFACT_REPAIR_BACKLOG_v1")
        self.assertEqual(backlog["status"], "OPEN")
        self.assertGreater(backlog["repair_work_order_total"], 0)
        self.assertTrue(all(row["research_artifact_status"] == "OPEN" for row in backlog["rows"]))
        self.assertTrue(all(row["execution_command"] for row in backlog["rows"]))
        self.assertTrue(all(row["no_fake_closure_policy"] for row in backlog["rows"]))
        self.assertEqual(batch["schema_id"], "OC133_MODERN_SCIENCE_COMPARATOR_RESEARCH_ARTIFACT_REPAIR_BATCH_v1")
        self.assertIn("never promotes broad superiority", batch["no_fake_closure_policy"])
        self.assertTrue(repair_rows)
        self.assertTrue(all(row["status"] in {"PASS", "CAPABILITY_DEVELOPMENT_REQUIRED", "EVIDENCE_REPAIR_ATTEMPTED_REMAINS_OPEN", "FAIL_CLOSED"} for row in repair_rows))
        self.assertTrue(all(row["refreshed_research_artifact_status"] in {"PASS", "OPEN"} for row in repair_rows))
        self.assertTrue(any(row.get("executor_type") == "capability_development" for row in supervisor_queue["rows"]))
        self.assertTrue(any(row.get("missing_artifact_type") in {"oc_prediction_scoring_row", "replay_record"} for row in supervisor_queue["rows"]))

    def test_recovery_r017_is_fail_closed_until_final_toe_validator_passes(self) -> None:
        tools_dir = ROOT / "tools"
        if str(tools_dir) not in sys.path:
            sys.path.insert(0, str(tools_dir))
        from assemble_oc_core_release_package import assemble_release

        with self.assertRaisesRegex(RuntimeError, "recovery_r017 is fail-closed"):
            assemble_release(
                "oc_core_1_3_3",
                write=False,
                structure_source="recovered_l10c",
                assembly_revision="recovery_r017",
            )


if __name__ == "__main__":
    unittest.main()
