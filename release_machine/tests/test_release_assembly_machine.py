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


if __name__ == "__main__":
    unittest.main()
