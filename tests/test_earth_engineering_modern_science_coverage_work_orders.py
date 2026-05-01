from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
EARTH_FACTORY_PATH = (
    REPO_ROOT
    / "validation"
    / "heldout"
    / "grand_science"
    / "earth_space"
    / "coverage_work_orders"
    / "oc133_earth_space_modern_science_coverage_work_orders.py"
)
ENGINEERING_FACTORY_PATH = (
    REPO_ROOT
    / "validation"
    / "heldout"
    / "grand_science"
    / "engineering"
    / "coverage_work_orders"
    / "oc133_engineering_modern_science_coverage_work_orders.py"
)


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class EarthEngineeringModernScienceCoverageWorkOrderTests(unittest.TestCase):
    def assert_spec_is_executable_and_fail_closed(self, row: dict) -> None:
        self.assertFalse(row["coverage_closure_allowed"], row["work_order_id"])
        self.assertFalse(row["support_allowed_for_broad_coverage"], row["work_order_id"])
        self.assertNotEqual(row["lane_status"], "PASS", row["work_order_id"])
        spec = row["executable_spec"]

        for field in (
            "official_source",
            "target_variable",
            "target_hidden_split",
            "formula_or_model",
            "preregistered_comparator",
            "uncertainty_and_residual",
            "negative_control",
            "falsifier",
            "N",
            "replay_command",
            "fail_closed_current_evidence",
        ):
            self.assertTrue(spec[field], f"{row['work_order_id']}::{field}")

        self.assertTrue(spec["official_source"]["source_authority"], row["work_order_id"])
        self.assertTrue(spec["official_source"]["official_documentation_url"].startswith("https://"))
        self.assertTrue(spec["official_source"]["official_endpoint_url"].startswith("https://"))
        self.assertTrue(spec["target_variable"]["target_fields"], row["work_order_id"])
        self.assertTrue(spec["target_hidden_split"]["hidden_target_fields"], row["work_order_id"])
        self.assertTrue(spec["target_hidden_split"]["target_hidden_until_scoring"], row["work_order_id"])
        self.assertFalse(spec["target_hidden_split"]["target_values_used_for_selection"], row["work_order_id"])
        self.assertTrue(spec["formula_or_model"]["rule"], row["work_order_id"])
        self.assertFalse(spec["formula_or_model"]["target_values_may_be_used_for_model_design"], row["work_order_id"])
        self.assertTrue(spec["preregistered_comparator"]["prediction_rule"], row["work_order_id"])
        self.assertTrue(spec["preregistered_comparator"]["pre_registered"], row["work_order_id"])
        self.assertFalse(spec["preregistered_comparator"]["target_values_used_for_baseline_design"], row["work_order_id"])
        self.assertTrue(spec["uncertainty_and_residual"]["residual_metric"], row["work_order_id"])
        self.assertTrue(spec["uncertainty_and_residual"]["uncertainty_method"], row["work_order_id"])
        self.assertTrue(spec["negative_control"]["rejection_predicate"], row["work_order_id"])
        self.assertTrue(spec["falsifier"]["triggers"], row["work_order_id"])
        self.assertGreaterEqual(spec["N"]["minimum_n"], 20, row["work_order_id"])
        self.assertTrue(spec["replay_command"]["commands"], row["work_order_id"])
        self.assertIn("NO_BROAD_SUPERIORITY_CERTIFICATION", spec["replay_command"]["acceptance_predicates"])
        evidence = spec["fail_closed_current_evidence"]
        self.assertFalse(evidence["coverage_closure_allowed"], row["work_order_id"])
        self.assertFalse(evidence["broad_modern_science_superiority_allowed"], row["work_order_id"])
        self.assertFalse(evidence["scientific_pass"], row["work_order_id"])
        if row["work_order_id"] == "MS-COV-WO-011":
            self.assertTrue(evidence["executable_evidence_exists"], row["work_order_id"])
            self.assertTrue(evidence["target_hidden_scorer_present"], row["work_order_id"])
            self.assertEqual(
                evidence["exact_blocker"],
                "COMPARATOR_BASELINE_NOT_BEATEN_WITH_UNCERTAINTY",
                row["work_order_id"],
            )
        else:
            self.assertFalse(evidence["executable_evidence_exists"], row["work_order_id"])

    def test_earth_space_work_orders_are_executable_fail_closed_specs(self) -> None:
        factory = load_module(EARTH_FACTORY_PATH, "earth_space_coverage_work_orders")
        payload = factory.build_payload(REPO_ROOT)

        self.assertEqual(factory.validate_payload(payload), [])
        self.assertEqual(factory.check_stored(REPO_ROOT), [])
        self.assertEqual(payload["work_order_total"], 3)
        self.assertFalse(payload["coverage_closure_allowed"])
        self.assertEqual(payload["official_api_hash_bound_lane_total"], 1)
        self.assertEqual(
            {row["work_order_id"] for row in payload["work_orders"]},
            {"MS-COV-WO-010", "MS-COV-WO-011", "MS-COV-WO-012"},
        )
        self.assertEqual(
            {row["phenomenon_class_id"] for row in payload["work_orders"]},
            {
                "climate_weather_geophysical_time_series",
                "geochemistry_and_hydrology_observables",
                "remote_sensing_and_planetary_measurements",
            },
        )
        for row in payload["work_orders"]:
            self.assert_spec_is_executable_and_fail_closed(row)

        hydrology = next(row for row in payload["work_orders"] if row["work_order_id"] == "MS-COV-WO-011")
        api_lane = hydrology["official_api_lane"]
        self.assertTrue(api_lane["source_snapshot_hash_bound"])
        self.assertTrue(api_lane["target_hidden_scorer_present"])
        self.assertFalse(api_lane["strict_scientific_predicates_pass"])
        self.assertEqual(api_lane["remaining_blocker"], "COMPARATOR_BASELINE_NOT_BEATEN_WITH_UNCERTAINTY")
        self.assertGreaterEqual(api_lane["value_row_count"], 20)
        self.assertEqual(
            hydrology["executable_spec"]["fail_closed_current_evidence"]["current_status"],
            "SCORER_READY_FAIL_CLOSED_STRICT_EVIDENCE_NOT_MET",
        )

        scorer_pack = factory.build_usgs_hydrology_scorer_pack(REPO_ROOT)
        self.assertEqual(factory.validate_usgs_hydrology_scorer_pack(scorer_pack, REPO_ROOT), [])
        self.assertEqual(factory.check_usgs_hydrology_scorer_stored(REPO_ROOT), [])
        self.assertTrue(scorer_pack["scorer_ready"])
        self.assertFalse(scorer_pack["strict_predicates_all_pass"])
        self.assertFalse(scorer_pack["scientific_pass"])
        self.assertFalse(scorer_pack["coverage_closure_allowed"])
        self.assertEqual(scorer_pack["exact_blocker"], "COMPARATOR_BASELINE_NOT_BEATEN_WITH_UNCERTAINTY")
        self.assertEqual(scorer_pack["pretarget_declaration"]["split_policy"]["training_row_count"], 20)
        self.assertEqual(scorer_pack["pretarget_declaration"]["split_policy"]["hidden_row_count"], 20)
        self.assertEqual(scorer_pack["scoring_results"]["hidden_row_count"], 20)
        aggregate = scorer_pack["scoring_results"]["aggregate"]
        self.assertGreater(aggregate["model_mae_plus_uncertainty_cfs"], aggregate["comparator_mae_cfs"])
        self.assertFalse(aggregate["residual_superiority_pass"])
        self.assertTrue(scorer_pack["negative_control"]["rejected"])
        self.assertEqual(scorer_pack["falsifier"]["status"], "TRIGGERED")
        self.assertTrue(
            scorer_pack["target_leakage_control"]["predictions_unchanged_under_hidden_target_mutation"]
        )
        self.assertTrue(
            scorer_pack["target_leakage_control"]["target_hashes_changed_under_hidden_target_mutation"]
        )

        tampered = json.loads(json.dumps(scorer_pack, ensure_ascii=True))
        tampered["negative_control"]["rejected"] = False
        self.assertIn(
            "USGS_HYDROLOGY_NEGATIVE_CONTROL_NOT_REJECTED",
            factory.validate_usgs_hydrology_scorer_pack(tampered, REPO_ROOT),
        )

    def test_engineering_work_orders_are_executable_fail_closed_specs(self) -> None:
        factory = load_module(ENGINEERING_FACTORY_PATH, "engineering_coverage_work_orders")
        payload = factory.build_payload()

        self.assertEqual(factory.validate_payload(payload), [])
        self.assertEqual(factory.check_stored(REPO_ROOT), [])
        self.assertEqual(payload["work_order_total"], 3)
        self.assertFalse(payload["coverage_closure_allowed"])
        self.assertEqual(
            {row["work_order_id"] for row in payload["work_orders"]},
            {"MS-COV-WO-022", "MS-COV-WO-023", "MS-COV-WO-024"},
        )
        self.assertEqual(
            {row["phenomenon_class_id"] for row in payload["work_orders"]},
            {
                "materials_property_and_failure_prediction",
                "control_systems_and_signal_measurement",
                "energy_transport_and_manufacturing_processes",
            },
        )
        for row in payload["work_orders"]:
            self.assert_spec_is_executable_and_fail_closed(row)

        authorities = {
            row["executable_spec"]["official_source"]["source_authority"]
            for row in payload["work_orders"]
        }
        self.assertEqual(authorities, {"National Institute of Standards and Technology"})


if __name__ == "__main__":
    unittest.main()
