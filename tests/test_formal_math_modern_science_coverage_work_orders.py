from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
FACTORY_PATH = (
    REPO_ROOT
    / "validation"
    / "heldout"
    / "grand_science"
    / "formal_mathematics"
    / "coverage_work_orders"
    / "oc133_formal_mathematics_modern_science_coverage_work_orders.py"
)
DISPATCHER_PATH = REPO_ROOT / "benchmarks" / "modern_science" / "coverage_lane_dispatcher.py"


def load_factory():
    spec = importlib.util.spec_from_file_location("formal_math_coverage_work_orders", FACTORY_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_dispatcher():
    spec = importlib.util.spec_from_file_location("coverage_lane_dispatcher", DISPATCHER_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class FormalMathModernScienceCoverageWorkOrderTests(unittest.TestCase):
    def assert_formal_work_order_is_executable_and_fail_closed(self, row: dict) -> None:
        self.assertTrue(row["formal_route_only"], row["work_order_id"])
        self.assertFalse(row["coverage_closure_allowed"], row["work_order_id"])
        self.assertFalse(row["support_allowed_for_broad_coverage"], row["work_order_id"])
        self.assertFalse(row["empirical_numeric_prediction_allowed"], row["work_order_id"])
        self.assertNotEqual(row["lane_status"], "PASS")

        self.assertTrue(row["source_proof_corpus"]["corpus_id"], row["work_order_id"])
        self.assertTrue(row["source_proof_corpus"]["artifacts"], row["work_order_id"])
        self.assertEqual(row["source_proof_corpus"]["minimum_formal_case_count"], 20)
        self.assertNotEqual(row["source_proof_corpus"]["source_kind"], "empirical_observation_table")

        self.assertTrue(row["target_theorem_or_property"]["target_statement"], row["work_order_id"])
        self.assertTrue(row["target_theorem_or_property"]["target_fields"], row["work_order_id"])
        self.assertGreaterEqual(row["target_theorem_or_property"]["minimum_target_rows"], 20)

        withheld = row["hidden_target_or_formal_withheld_aggregate_policy"]
        self.assertIn(withheld["mode"], {"target_blind_formal_replay", "formal_withheld_aggregate"})
        self.assertFalse(withheld["target_values_used_for_proof_design"], row["work_order_id"])
        self.assertTrue(withheld["withheld_until_scoring"], row["work_order_id"])

        self.assertEqual(row["proof_or_model"]["route"], "formal", row["work_order_id"])
        self.assertFalse(row["proof_or_model"]["empirical_numeric_prediction"], row["work_order_id"])
        self.assertTrue(row["proof_or_model"]["checker_refs"], row["work_order_id"])
        self.assertTrue(row["comparator_baseline"]["pre_registered"], row["work_order_id"])
        self.assertFalse(row["comparator_baseline"]["target_values_used_for_baseline_design"], row["work_order_id"])
        self.assertFalse(row["residual_or_error_notion"]["empirical_numeric_prediction"], row["work_order_id"])
        self.assertTrue(row["negative_control"]["rejection_predicate"], row["work_order_id"])
        self.assertTrue(row["falsifier"]["trigger_predicates"], row["work_order_id"])
        self.assertTrue(row["replay_protocol"]["commands"], row["work_order_id"])
        self.assertIn("EMPIRICAL_NUMERIC_PREDICTION_NOT_ASSERTED", row["replay_protocol"]["acceptance_predicates"])
        self.assertIn("NO_BROAD_SUPERIORITY_CERTIFICATION", row["replay_protocol"]["acceptance_predicates"])
        self.assertFalse(row["current_evidence_status"]["coverage_closure_allowed"], row["work_order_id"])
        self.assertTrue(row["current_evidence_status"]["remaining_blockers"], row["work_order_id"])

    def test_formal_math_work_orders_are_synchronized_and_fail_closed(self) -> None:
        factory = load_factory()
        payload = factory.build_payload(REPO_ROOT)

        self.assertEqual(factory.validate_payload(payload), [])
        self.assertEqual(factory.check_stored(REPO_ROOT), [])
        self.assertEqual(payload["work_order_total"], 3)
        self.assertFalse(payload["coverage_closure_allowed"])
        self.assertFalse(payload["empirical_numeric_prediction_allowed"])
        self.assertEqual(
            {row["work_order_id"] for row in payload["work_orders"]},
            {"MS-COV-WO-001", "MS-COV-WO-002", "MS-COV-WO-003"},
        )
        self.assertEqual(
            {row["phenomenon_class_id"] for row in payload["work_orders"]},
            {
                "formal_theorem_reconstruction",
                "statistical_inference_identifiability",
                "computational_complexity_and_algorithmic_proof",
            },
        )
        for row in payload["work_orders"]:
            self.assert_formal_work_order_is_executable_and_fail_closed(row)

    def test_theorem_reconstruction_uses_existing_lean_finite_corpus_but_stays_fail_closed(self) -> None:
        factory = load_factory()
        payload = factory.build_payload(REPO_ROOT)
        row = next(item for item in payload["work_orders"] if item["work_order_id"] == "MS-COV-WO-001")

        self.assertTrue(row["source_proof_corpus"]["candidate_artifact_set_present"])
        self.assertFalse(row["source_proof_corpus"]["exact_evidence_exists"])
        self.assertFalse(row["current_evidence_status"]["exact_evidence_exists"])
        self.assertTrue(row["lane_status"].startswith("FAIL_CLOSED"))
        self.assertFalse(row["coverage_closure_allowed"])
        self.assertIn(
            "MATHEMATICS_FORMAL_EVIDENCE_REPLAY_CHECK_NOT_PASSING_IN_THIS_WORKTREE",
            row["current_evidence_status"]["remaining_blockers"],
        )
        self.assertIn("FORMAL_COVERAGE_SCOPE_REVIEW_NOT_PERFORMED", row["current_evidence_status"]["remaining_blockers"])

        artifact_refs = {artifact["ref"] for artifact in row["source_proof_corpus"]["artifacts"]}
        self.assertIn(factory.MATH_PACK_REL, artifact_refs)
        self.assertIn(factory.FINITE_INPUT_REL, artifact_refs)
        self.assertIn(factory.FINITE_OUTPUT_REL, artifact_refs)
        self.assertIn(factory.LEAN_SOURCE_REL, artifact_refs)
        self.assertTrue(all(artifact["exists"] and artifact["sha256"] for artifact in row["source_proof_corpus"]["artifacts"]))

    def test_statistics_probability_and_complexity_specs_require_future_exact_formal_corpora(self) -> None:
        factory = load_factory()
        payload = factory.build_payload(REPO_ROOT)
        rows = {
            row["work_order_id"]: row
            for row in payload["work_orders"]
            if row["work_order_id"] in {"MS-COV-WO-002", "MS-COV-WO-003"}
        }

        self.assertEqual(set(rows), {"MS-COV-WO-002", "MS-COV-WO-003"})
        for row in rows.values():
            self.assertFalse(row["source_proof_corpus"]["exact_evidence_exists"], row["work_order_id"])
            self.assertFalse(row["current_evidence_status"]["exact_evidence_exists"], row["work_order_id"])
            self.assertTrue(row["lane_status"].startswith("FAIL_CLOSED"), row["work_order_id"])
            self.assertFalse(row["coverage_closure_allowed"], row["work_order_id"])
            exact_required = [
                artifact
                for artifact in row["source_proof_corpus"]["artifacts"]
                if artifact["exact_evidence_required"]
            ]
            self.assertTrue(exact_required, row["work_order_id"])
            self.assertTrue(any(not artifact["exists"] for artifact in exact_required), row["work_order_id"])
            self.assertIn("numeric", row["source_proof_corpus"]["scope_boundary"].lower())
            self.assertFalse(row["residual_or_error_notion"]["empirical_numeric_prediction"])

    def test_plugin_specs_are_thin_formal_fail_closed_bridge_when_plugin_dir_exists(self) -> None:
        factory = load_factory()
        dispatcher = load_dispatcher()
        if not factory.plugin_specs_enabled(REPO_ROOT):
            self.skipTest("coverage executable spec plugin directory is not present")

        outputs = factory.build_all(REPO_ROOT)
        plugin_outputs = {
            rel: payload
            for rel, payload in outputs.items()
            if rel.startswith(factory.PLUGIN_DIR_REL + "/formal_mathematics_and_logic")
        }

        self.assertEqual(set(plugin_outputs), set(factory.PLUGIN_SPEC_RELS.values()))
        for rel, expected in plugin_outputs.items():
            actual = json.loads((REPO_ROOT / rel).read_text(encoding="utf-8"))
            self.assertEqual(actual, expected)
            self.assertEqual(actual["spec_schema_id"], factory.PLUGIN_SPEC_SCHEMA_ID)
            self.assertEqual(dispatcher.validate_executable_spec(actual, context=rel), [])
            self.assertTrue(actual["formal_route_only"], rel)
            self.assertFalse(actual["coverage_closure_allowed"], rel)
            self.assertFalse(actual["empirical_numeric_prediction_allowed"], rel)
            self.assertEqual(actual["source_domain_class_id"], "formal_mathematics_and_logic")
            self.assertTrue(actual["phenomenon_class_id"].endswith(factory.FORMAL_SPEC_REGISTRY_SUFFIX), rel)
            self.assertTrue(actual["official_data_source"]["official_documentation_url"].startswith("https://"))
            self.assertTrue(actual["target_variable"]["target_fields"], rel)
            self.assertFalse(actual["current_evidence"]["executable_evidence_exists"], rel)
            self.assertFalse(actual["current_evidence"]["coverage_closure_allowed"], rel)
            for predicate in factory.DISPATCHER_CLOSURE_PREDICATES:
                self.assertIn(predicate, actual["closure_predicates_required"], rel)
            self.assertIn("EMPIRICAL_NUMERIC_PREDICTION_NOT_ASSERTED", actual["closure_predicates_required"])
            self.assertIn("NO_BROAD_SUPERIORITY_CERTIFICATION", actual["closure_predicates_required"])


if __name__ == "__main__":
    unittest.main()
