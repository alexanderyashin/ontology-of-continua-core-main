from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
FACTORY_PATH = (
    REPO_ROOT
    / "validation"
    / "heldout"
    / "grand_science"
    / "agriculture"
    / "coverage_work_orders"
    / "oc133_agriculture_modern_science_coverage_work_orders.py"
)


def load_factory():
    spec = importlib.util.spec_from_file_location("agriculture_coverage_work_orders", FACTORY_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class AgricultureModernScienceCoverageWorkOrderTests(unittest.TestCase):
    def assert_row_is_fail_closed_executable_spec(self, row: dict) -> None:
        row_id = row["work_order_id"]
        self.assertFalse(row["coverage_closure_allowed"], row["work_order_id"])
        self.assertFalse(row["support_allowed_for_broad_coverage"], row["work_order_id"])
        self.assertNotEqual(row["lane_status"], "PASS", row["work_order_id"])
        self.assertTrue(row["lane_status"].startswith("OPEN_FAIL_CLOSED"), row["work_order_id"])
        self.assertTrue(row["official_sources"], row["work_order_id"])
        self.assertTrue(row["target_variable"]["name"], row["work_order_id"])
        self.assertTrue(row["target_variable"]["target_fields"], row["work_order_id"])
        self.assertTrue(row["target_hidden_split"]["target_hidden_until_scoring"], row["work_order_id"])
        self.assertFalse(row["target_hidden_split"]["target_values_used_for_selection"], row["work_order_id"])
        self.assertTrue(row["formula_model"]["rule"], row["work_order_id"])
        self.assertFalse(row["formula_model"]["target_values_used_for_model_design"], row["work_order_id"])
        self.assertTrue(row["preregistered_comparator"]["prediction_rule"], row["work_order_id"])
        self.assertTrue(row["preregistered_comparator"]["pre_registered"], row["work_order_id"])
        self.assertFalse(row["preregistered_comparator"]["target_values_used_for_baseline_design"], row["work_order_id"])
        self.assertTrue(row["uncertainty_residual_metric"]["residual_metric"], row["work_order_id"])
        self.assertTrue(row["negative_control"]["rejection_predicate"], row["work_order_id"])
        self.assertTrue(row["falsifier"]["triggers"], row["work_order_id"])
        self.assertGreaterEqual(row["minimum_n"], 20, row["work_order_id"])
        self.assertTrue(row["replay_command"], row["work_order_id"])
        self.assertFalse(row["current_evidence_status"]["coverage_closure_allowed"], row["work_order_id"])
        if row_id == "MS-COV-WO-020":
            self.assertTrue(row["current_evidence_status"]["executable_evidence_exists"], row_id)
        else:
            self.assertFalse(row["current_evidence_status"]["executable_evidence_exists"], row_id)
        self.assertTrue(row["current_evidence_status"]["status_code"].startswith("OPEN_FAIL_CLOSED"), row["work_order_id"])
        self.assertIn("NO_BROAD_SUPERIORITY_CERTIFICATION", row["replay_protocol"]["acceptance_predicates"])

    def test_agriculture_work_orders_are_concrete_source_backed_and_fail_closed(self) -> None:
        factory = load_factory()
        payload = factory.build_payload()

        self.assertEqual(factory.validate_payload(payload), [])
        self.assertEqual(factory.check_stored(REPO_ROOT), [])
        self.assertEqual(payload["work_order_total"], 3)
        self.assertFalse(payload["coverage_closure_allowed"])
        self.assertFalse(payload["broad_modern_science_superiority_allowed"])
        self.assertEqual(
            {row["work_order_id"] for row in payload["work_orders"]},
            {"MS-COV-WO-019", "MS-COV-WO-020", "MS-COV-WO-021"},
        )
        self.assertEqual(
            {row["phenomenon_class_id"] for row in payload["work_orders"]},
            {
                "crop_yield_soil_and_trait_observables",
                "food_chemistry_safety_and_nutrition",
                "animal_health_and_production_systems",
            },
        )
        for row in payload["work_orders"]:
            self.assert_row_is_fail_closed_executable_spec(row)

    def test_fooddata_central_lane_is_scorer_ready_but_still_fail_closed(self) -> None:
        factory = load_factory()
        payload = factory.build_payload()
        food = next(row for row in payload["work_orders"] if row["work_order_id"] == "MS-COV-WO-020")

        self.assertEqual(
            food["lane_status"],
            "OPEN_FAIL_CLOSED_SCORER_READY_STRICT_EVIDENCE_PACK_NO_COVERAGE_CLOSURE",
        )
        self.assertTrue(food["current_evidence_status"]["readonly_acquisition_lane_implemented"])
        self.assertTrue(food["current_evidence_status"]["target_hidden_scorer_present"])
        self.assertIn("--score-fdc --write-scoring", food["replay_command"])
        self.assertEqual(food["official_sources"][0]["source_id"], "USDA_FOODDATA_CENTRAL_API")
        self.assertEqual(food["official_sources"][0]["local_snapshot_ref"], factory.FDC_SNAPSHOT_REL)
        self.assertEqual(food["official_sources"][0]["lock_ref"], factory.FDC_LOCK_REL)
        self.assertIn("READONLY_FDC_ACQUISITION_HASH_BOUND", food["replay_protocol"]["acceptance_predicates"])
        self.assertIn("TARGET_HIDDEN_FDC_SODIUM_SCORER_READY", food["replay_protocol"]["acceptance_predicates"])
        self.assertIn("STRICT_FDC_SCORING_PACK_HASH_BOUND", food["replay_protocol"]["acceptance_predicates"])
        self.assertIn("FDC_SODIUM_NEGATIVE_CONTROL_REJECTED", food["replay_protocol"]["acceptance_predicates"])

    def test_fooddata_central_scoring_artifacts_are_hash_consistent_and_not_a_pass(self) -> None:
        factory = load_factory()
        snapshot = factory.read_json(REPO_ROOT / factory.FDC_SNAPSHOT_REL)
        lock = factory.read_json(REPO_ROOT / factory.FDC_LOCK_REL)
        report = factory.read_json(REPO_ROOT / factory.FDC_REPORT_REL)
        task_table = factory.read_json(REPO_ROOT / factory.FDC_TASK_TABLE_REL)
        target_lock = factory.read_json(REPO_ROOT / factory.FDC_HIDDEN_TARGET_LOCK_REL)
        scoring_pack = factory.read_json(REPO_ROOT / factory.FDC_SCORING_PACK_REL)
        expected_scoring = factory.build_fdc_scoring_outputs(snapshot, lock)

        self.assertEqual(factory.validate_fdc_snapshot(snapshot), [])
        self.assertEqual(factory.validate_fdc_lock(snapshot, lock), [])
        self.assertEqual(report, factory.build_fdc_report(snapshot, lock))
        self.assertEqual(task_table, expected_scoring["task_table"])
        self.assertEqual(target_lock, expected_scoring["hidden_target_lock"])
        self.assertEqual(scoring_pack, expected_scoring["scoring_pack"])
        self.assertGreaterEqual(snapshot["row_count"], snapshot["minimum_n_required"])
        self.assertEqual(snapshot["row_count"], 25)
        self.assertFalse(snapshot["coverage_closure_allowed"])
        self.assertFalse(lock["coverage_closure_allowed"])
        self.assertFalse(report["coverage_closure_allowed"])
        self.assertTrue(report["target_hidden_scorer_present"])
        self.assertTrue(report["comparator_scores_present"])
        self.assertTrue(report["negative_control_rejected"])
        self.assertTrue(report["strict_evidence_pack_present"])
        self.assertEqual(
            report["current_evidence_status"],
            "OPEN_FAIL_CLOSED_SCORER_READY_STRICT_EVIDENCE_PACK_NO_COVERAGE_CLOSURE",
        )
        self.assertFalse(task_table["target_values_present"])
        self.assertNotIn("307", task_table["rows"][0]["visible_selected_nutrients"])
        self.assertEqual(scoring_pack["row_count"], 25)
        self.assertTrue(scoring_pack["negative_control"]["rejected"])
        self.assertTrue(scoring_pack["strict_evidence_pack"]["scorer_ready"])
        self.assertFalse(scoring_pack["strict_evidence_pack"]["coverage_closure_allowed"])
        self.assertGreater(scoring_pack["residuals"]["model"]["mean_absolute_error"], 0)
        self.assertGreater(scoring_pack["residuals"]["comparator"]["mean_absolute_error"], 0)
        self.assertGreater(
            scoring_pack["negative_control"]["model_control_residual"]["mean_absolute_error"],
            scoring_pack["residuals"]["model"]["mean_absolute_error"],
        )
        self.assertFalse(scoring_pack["residuals"]["material_margin_met"])

    def test_fooddata_central_missing_scoring_fields_emit_machine_readable_blocker(self) -> None:
        factory = load_factory()
        snapshot = factory.read_json(REPO_ROOT / factory.FDC_SNAPSHOT_REL)
        lock = factory.read_json(REPO_ROOT / factory.FDC_LOCK_REL)
        blocked_snapshot = copy.deepcopy(snapshot)
        del blocked_snapshot["rows"][0]["selected_nutrients"]["207"]

        blocker = factory.build_fdc_scoring_blocker(blocked_snapshot, lock)

        self.assertEqual(
            blocker["blocked_status"],
            "OPEN_FAIL_CLOSED_BLOCKED_MISSING_REQUIRED_FDC_SCORING_FIELDS",
        )
        self.assertFalse(blocker["coverage_closure_allowed"])
        self.assertFalse(blocker["target_hidden_scorer_present"])
        self.assertIn("rows[fdcId=321358].selected_nutrients[207]", blocker["missing_fields"])
        self.assertIn("Re-acquire an official USDA FDC Foundation Foods snapshot", blocker["acquisition_next_action"])


if __name__ == "__main__":
    unittest.main()
