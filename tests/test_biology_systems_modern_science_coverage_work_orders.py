from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
BIOLOGY_FACTORY_PATH = (
    REPO_ROOT
    / "validation"
    / "heldout"
    / "grand_science"
    / "biology"
    / "coverage_work_orders"
    / "oc133_biology_modern_science_coverage_work_orders.py"
)
SYSTEMS_FACTORY_PATH = (
    REPO_ROOT
    / "validation"
    / "heldout"
    / "grand_science"
    / "systems"
    / "coverage_work_orders"
    / "oc133_systems_civilizational_modern_science_coverage_work_orders.py"
)


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class BiologySystemsModernScienceCoverageWorkOrderTests(unittest.TestCase):
    def assert_work_order_is_executable_and_fail_closed(self, row: dict) -> None:
        self.assertFalse(row["coverage_closure_allowed"], row["work_order_id"])
        self.assertFalse(row["support_allowed_for_broad_coverage"], row["work_order_id"])
        self.assertNotEqual(row["lane_status"], "PASS")
        self.assertTrue(row["official_sources"], row["work_order_id"])
        self.assertTrue(row["acquisition_requests"], row["work_order_id"])
        self.assertTrue(row["target_variable"]["name"], row["work_order_id"])
        self.assertTrue(row["target_variable"]["target_field"], row["work_order_id"])
        self.assertTrue(row["prediction_formula"]["rule"], row["work_order_id"])
        self.assertFalse(row["prediction_formula"]["target_values_used_for_selection"], row["work_order_id"])
        self.assertTrue(row["incumbent_comparator"]["prediction_rule"], row["work_order_id"])
        self.assertTrue(row["incumbent_comparator"]["pre_registered"], row["work_order_id"])
        self.assertTrue(row["uncertainty_and_residual"]["residual_metric"], row["work_order_id"])
        self.assertTrue(row["uncertainty_and_residual"]["uncertainty_method"], row["work_order_id"])
        self.assertTrue(row["negative_control"]["rejection_predicate"], row["work_order_id"])
        self.assertTrue(row["falsifier_predicates"], row["work_order_id"])
        self.assertTrue(row["replay_protocol"]["commands"], row["work_order_id"])
        self.assertTrue(row["replay_protocol"]["required_artifacts"], row["work_order_id"])
        self.assertIn("NO_BROAD_SUPERIORITY_CERTIFICATION", row["replay_protocol"]["acceptance_predicates"])

    def test_biology_uncovered_phenomena_emit_concrete_fail_closed_work_orders(self) -> None:
        factory = load_module(BIOLOGY_FACTORY_PATH, "bio_coverage_work_orders")
        payload = factory.build_payload()

        self.assertEqual(factory.validate_payload(payload), [])
        self.assertEqual(factory.check_stored(REPO_ROOT), [])
        self.assertEqual(payload["work_order_total"], 3)
        self.assertFalse(payload["coverage_closure_allowed"])
        self.assertEqual(
            {row["phenomenon_class_id"] for row in payload["work_orders"]},
            {
                "evolutionary_phylogenetic_patterns",
                "cellular_developmental_regulatory_dynamics",
                "ecology_population_and_biodiversity_observables",
            },
        )
        for row in payload["work_orders"]:
            self.assert_work_order_is_executable_and_fail_closed(row)

        cellular = next(
            row
            for row in payload["work_orders"]
            if row["phenomenon_class_id"] == "cellular_developmental_regulatory_dynamics"
        )
        self.assertEqual(cellular["lane_status"], "READY_FOR_REPLAY_REVIEW_NOT_COVERAGE_CLOSED")
        self.assertIn(factory.TARGET_EVIDENCE_PACK_REL, cellular["existing_official_lane_refs"])

    def test_systems_civilizational_uncovered_phenomena_emit_concrete_fail_closed_work_orders(self) -> None:
        factory = load_module(SYSTEMS_FACTORY_PATH, "systems_coverage_work_orders")
        payload = factory.build_payload()

        self.assertEqual(factory.validate_payload(payload), [])
        self.assertEqual(factory.check_stored(REPO_ROOT), [])
        self.assertEqual(payload["work_order_total"], 5)
        self.assertFalse(payload["coverage_closure_allowed"])
        self.assertEqual(
            {row["phenomenon_class_id"] for row in payload["work_orders"]},
            {
                "economic_indicator_and_market_observables",
                "institutional_social_network_and_policy_outcomes",
                "multi_agent_system_dynamics",
                "queue_supply_chain_and_operations_observables",
                "resilience_risk_and_intervention_response",
            },
        )
        for row in payload["work_orders"]:
            self.assert_work_order_is_executable_and_fail_closed(row)

        economic = next(
            row
            for row in payload["work_orders"]
            if row["phenomenon_class_id"] == "economic_indicator_and_market_observables"
        )
        self.assertEqual(economic["lane_status"], "FAIL_CLOSED_PENDING_GENERALIZED_WDI_INDICATOR_REPLAY")
        self.assertIn(factory.WDI_POPULATION_PACK_REL, economic["existing_official_lane_refs"])
        self.assertTrue(any(request["indicator"] == "NY.GDP.MKTP.CD" for request in economic["acquisition_requests"]))


if __name__ == "__main__":
    unittest.main()
