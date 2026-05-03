from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ASSEMBLY = ROOT / "operations" / "release_assembly" / "oc_core"


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
        self.assertEqual(profile["concept_doi_policy"]["pdf_doi"], "10.5281/zenodo.17899134")
        self.assertTrue(profile["concept_doi_policy"]["release_record_doi_is_publication_layer_only"])
        for field in ["reader_task", "claim_boundary", "source_refs", "transition_in", "transition_out"]:
            self.assertIn(field, terminal["terminal_contract_fields"])
        self.assertIn("definition_model->proof_evidence", transitions["templates"])

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


if __name__ == "__main__":
    unittest.main()
