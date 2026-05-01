from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]

FACTORIES = {
    "cs": (
        REPO_ROOT
        / "validation"
        / "heldout"
        / "grand_science"
        / "cs"
        / "coverage_work_orders"
        / "oc133_cs_modern_science_coverage_work_orders.py"
    ),
    "neurobehavioral": (
        REPO_ROOT
        / "validation"
        / "heldout"
        / "grand_science"
        / "neurobehavioral"
        / "coverage_work_orders"
        / "oc133_neurobehavioral_modern_science_coverage_work_orders.py"
    ),
    "operations": (
        REPO_ROOT
        / "validation"
        / "heldout"
        / "grand_science"
        / "operations"
        / "coverage_work_orders"
        / "oc133_operations_modern_science_coverage_work_orders.py"
    ),
}

EXPECTED_WORK_ORDERS = {
    "cs": {
        "MS-COV-WO-025": "program_semantics_and_verification",
        "MS-COV-WO-026": "machine_learning_generalization_and_evaluation",
        "MS-COV-WO-027": "information_network_and_security_observables",
    },
    "neurobehavioral": {
        "MS-COV-WO-028": "neural_recording_and_brain_network_observables",
        "MS-COV-WO-029": "behavioral_task_and_psychometric_prediction",
        "MS-COV-WO-030": "learning_memory_and_perception_dynamics",
    },
    "operations": {
        "MS-COV-WO-033": "multi_agent_system_dynamics",
        "MS-COV-WO-034": "queue_supply_chain_and_operations_observables",
        "MS-COV-WO-035": "resilience_risk_and_intervention_response",
    },
}


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class CSNeuroOperationsModernScienceCoverageWorkOrderTests(unittest.TestCase):
    def assert_fail_closed_executable_spec(self, row: dict) -> None:
        row_id = row["work_order_id"]
        self.assertFalse(row["coverage_closure_allowed"], row_id)
        self.assertFalse(row["support_allowed_for_broad_coverage"], row_id)
        self.assertNotIn("PASS", row["lane_status"], row_id)
        self.assertGreaterEqual(row["minimum_n"], 20, row_id)
        self.assertEqual(row["N"]["minimum_required"], row["minimum_n"], row_id)
        self.assertIsNone(row["N"]["observed"], row_id)
        self.assertEqual(row["N"]["status"], "NOT_ACQUIRED_PROTOCOL_ONLY", row_id)

        self.assertTrue(row["official_sources"], row_id)
        for source in row["official_sources"]:
            self.assertTrue(source["official_url"].startswith("https://"), row_id)
            self.assertTrue(source["source_authority"], row_id)

        target = row["target_variable"]
        self.assertTrue(target["name"], row_id)
        self.assertTrue(target["target_field"], row_id)
        self.assertTrue(target["target_fields"], row_id)
        self.assertTrue(target["target_hidden_until_scoring"], row_id)

        split = row["split"]
        self.assertTrue(split["train"], row_id)
        self.assertTrue(split["validation"], row_id)
        self.assertTrue(split["holdout"], row_id)
        self.assertFalse(split["target_values_visible_during_split"], row_id)

        model = row["formula_or_model"]
        self.assertTrue(model["formula_or_model"], row_id)
        self.assertFalse(model["target_values_used_for_model_design"], row_id)
        self.assertFalse(model["target_values_used_for_selection"], row_id)

        comparator = row["incumbent_comparator"]
        self.assertTrue(comparator["prediction_rule"], row_id)
        self.assertTrue(comparator["pre_registered"], row_id)
        self.assertFalse(comparator["target_values_used_for_baseline_design"], row_id)

        uncertainty = row["uncertainty_and_residual"]
        self.assertTrue(uncertainty["residual_metric"], row_id)
        self.assertTrue(uncertainty["uncertainty_method"], row_id)
        self.assertTrue(uncertainty["superiority_predicate"], row_id)

        self.assertTrue(row["negative_control"]["rejection_predicate"], row_id)
        self.assertTrue(row["falsifier"]["trigger"], row_id)
        self.assertTrue(row["falsifier_predicates"], row_id)
        self.assertTrue(row["acquisition_protocol"]["steps"], row_id)
        self.assertIn("no_network_fetch_performed", row["acquisition_protocol"]["mode"], row_id)

        self.assertTrue(row["replay_command"].startswith("python validation/heldout/grand_science/"), row_id)
        self.assertTrue(row["replay_protocol"]["commands"], row_id)
        self.assertIn("NO_BROAD_SUPERIORITY_CERTIFICATION", row["replay_protocol"]["acceptance_predicates"], row_id)
        self.assertIn("FAIL_CLOSED_UNLESS_EXECUTABLE_EVIDENCE_BOUND", row["replay_protocol"]["acceptance_predicates"], row_id)

        evidence = row["current_evidence_status"]
        self.assertEqual(evidence["status"], "OPEN_FAIL_CLOSED_SPEC_DECLARED_NO_SOURCE_LOCK_NO_STRICT_PACK", row_id)
        self.assertFalse(evidence["executable_evidence_exists"], row_id)
        self.assertFalse(evidence["coverage_closure_allowed"], row_id)
        self.assertFalse(evidence["broad_support_allowed"], row_id)

        locks = row["no_send_locks"]
        self.assertTrue(locks["no_send"], row_id)
        self.assertFalse(locks["publish_allowed"], row_id)
        self.assertFalse(locks["registry_write_allowed"], row_id)
        self.assertFalse(locks["coverage_closure_allowed"], row_id)
        self.assertFalse(locks["broad_modern_science_superiority_allowed"], row_id)

    def test_domain_local_generators_emit_exact_target_work_orders(self) -> None:
        for domain, path in FACTORIES.items():
            with self.subTest(domain=domain):
                factory = load_module(path, f"{domain}_coverage_work_orders")
                payload = factory.build_payload()

                self.assertEqual(factory.validate_payload(payload), [])
                self.assertEqual(factory.check_stored(REPO_ROOT), [])
                self.assertFalse(payload["coverage_closure_allowed"])
                self.assertFalse(payload["broad_modern_science_superiority_allowed"])
                self.assertFalse(payload["official_data_acquired"])
                self.assertEqual(payload["small_deterministic_replay_implemented"], "SPEC_GENERATION_AND_SYNC_CHECK_ONLY")

                expected = EXPECTED_WORK_ORDERS[domain]
                self.assertEqual(payload["work_order_total"], len(expected))
                self.assertEqual(
                    {row["work_order_id"]: row["phenomenon_class_id"] for row in payload["work_orders"]},
                    expected,
                )
                for row in payload["work_orders"]:
                    self.assert_fail_closed_executable_spec(row)

    def test_specs_bind_to_official_or_public_sources_per_domain(self) -> None:
        cs = load_module(FACTORIES["cs"], "cs_coverage_work_orders").build_payload()
        neuro = load_module(FACTORIES["neurobehavioral"], "neuro_coverage_work_orders").build_payload()
        operations = load_module(FACTORIES["operations"], "ops_coverage_work_orders").build_payload()

        self.assertEqual(
            {source["source_id"] for row in cs["work_orders"] for source in row["official_sources"]},
            {
                "NIST_SAMATE_SARD",
                "SV_COMP_SV_BENCHMARKS",
                "OPENML_CC18_BENCHMARK_SUITE",
                "NIST_NVD_CVE_API_2_0",
            },
        )
        self.assertEqual(
            {source["source_id"] for row in neuro["work_orders"] for source in row["official_sources"]},
            {"OPENNEURO_DS000030_CNP"},
        )
        self.assertEqual(
            {source["source_id"] for row in operations["work_orders"] for source in row["official_sources"]},
            {
                "NYC_TLC_TRIP_RECORD_DATA",
                "USDOT_BTS_TRANSTATS_ON_TIME_PERFORMANCE",
                "FEMA_OPENFEMA_DISASTER_DECLARATIONS_V2",
            },
        )


if __name__ == "__main__":
    unittest.main()
