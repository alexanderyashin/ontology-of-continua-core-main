from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
DISPATCHER_PATH = REPO_ROOT / "benchmarks" / "modern_science" / "coverage_lane_dispatcher.py"


def load_dispatcher():
    spec = importlib.util.spec_from_file_location("coverage_lane_dispatcher", DISPATCHER_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ModernScienceCoverageLaneDispatcherTests(unittest.TestCase):
    def test_queue_is_deterministic_and_has_all_coverage_gaps(self) -> None:
        dispatcher = load_dispatcher()
        queue = dispatcher.build_queue(REPO_ROOT)
        lanes = queue["lanes"]

        self.assertEqual(queue["queue_size"], 35)
        self.assertEqual(queue["open_lane_total"], 35)
        self.assertEqual(queue["no_send_locked_lane_total"], 35)
        self.assertEqual(queue["executable_lane_total"], 29)
        self.assertEqual(dispatcher.validate_queue(queue), [])

        expected = [
            row["stable_id"]
            for row in [
                dispatcher.build_dispatch_row(index, work_order, {})
                for index, work_order in enumerate(
                    dispatcher.sorted_work_orders(dispatcher.build_concrete_work_orders(REPO_ROOT)["work_orders"]),
                    start=1,
                )
            ]
        ]
        self.assertEqual([row["stable_id"] for row in lanes], expected)

    def test_every_lane_keeps_no_send_and_no_closure_locks(self) -> None:
        dispatcher = load_dispatcher()
        queue = dispatcher.build_queue(REPO_ROOT)

        for lane in queue["lanes"]:
            locks = lane["no_send_locks"]
            self.assertTrue(locks["no_send"])
            self.assertFalse(locks["public_release_action_allowed"])
            self.assertFalse(locks["publish_allowed"])
            self.assertFalse(locks["push_allowed"])
            self.assertFalse(locks["registry_write_allowed"])
            self.assertFalse(locks["broad_modern_science_superiority_allowed"])
            self.assertFalse(lane["coverage_closure"]["mark_closed_allowed"])
            self.assertIn("NO_BROAD_SUPERIORITY_CERTIFICATION", lane["expected_acceptance_predicates"])

    def test_physics_chemistry_gaps_have_executable_specs_and_fail_closed_status(self) -> None:
        dispatcher = load_dispatcher()
        queue = dispatcher.build_queue(REPO_ROOT)
        lanes = [
            row
            for row in queue["lanes"]
            if row["domain_class_id"] in {"physical_sciences", "chemical_sciences"}
        ]

        self.assertEqual(queue["physics_chemistry_executable_lane_total"], 6)
        self.assertEqual(len(lanes), 6)
        self.assertEqual(
            {row["executable_work_order"]["official_data_source"]["source_id"] for row in lanes},
            {
                "physics_jpl_horizons_state_vectors_earth_sun_v1",
                "physics_nist_jarvis_dft_bandgap_v1",
                "physics_nasa_exoplanet_archive_pscomppars_kepler_v1",
                "chemistry_nist_kinetics_water_v1",
                "chemistry_nist_webbook_water_gas_thermo_v1",
                "chemistry_nist_webbook_water_ir_spectrum_v1",
            },
        )

        required_roles = {
            "official_data_source",
            "target_variable",
            "formula_or_model",
            "incumbent_comparator",
            "uncertainty_policy",
            "residual_metric",
            "negative_control",
            "falsifier",
        }
        for lane in lanes:
            spec = lane["executable_work_order"]
            self.assertEqual(spec["spec_schema_id"], dispatcher.EXECUTABLE_SPEC_SCHEMA_ID)
            self.assertEqual(dispatcher.validate_executable_spec(spec, context=lane["stable_id"]), [])
            self.assertEqual(lane["coverage_closure"]["current_status"], "OPEN_FAIL_CLOSED_NO_EXECUTABLE_EVIDENCE")
            self.assertFalse(lane["coverage_closure"]["mark_closed_allowed"])
            self.assertFalse(lane["evidence_gate"]["executable_evidence_exists"])
            self.assertFalse(lane["evidence_gate"]["closure_allowed"])
            self.assertTrue(
                spec["official_data_source"]["official_endpoint_url"].startswith("https://"),
                lane["stable_id"],
            )
            self.assertTrue(spec["target_variable"]["target_fields"])
            self.assertIn("formula_or_model", spec["formula_requirement"])
            self.assertTrue(required_roles.issubset({row["lane_role"] for row in lane["required_data_lanes"]}))
            self.assertIn("EXECUTABLE_LANE_SPEC_DECLARED", lane["expected_acceptance_predicates"])
            self.assertIn("FAIL_CLOSED_UNLESS_EXECUTABLE_EVIDENCE_BOUND", lane["expected_acceptance_predicates"])

    def test_json_plugin_specs_are_loaded_and_kept_fail_closed(self) -> None:
        dispatcher = load_dispatcher()
        queue = dispatcher.build_queue(REPO_ROOT)
        lanes = [
            row
            for row in queue["lanes"]
            if row["domain_class_id"] == "biological_life_sciences"
            and row["phenomenon_class_id"] == "evolutionary_phylogenetic_patterns"
        ]

        self.assertEqual(len(lanes), 1)
        lane = lanes[0]
        spec = lane["executable_work_order"]
        self.assertEqual(queue["executable_lane_total"], 29)
        self.assertEqual(queue["physics_chemistry_executable_lane_total"], 6)
        self.assertEqual(spec["domain_class_id"], "biological_life_sciences")
        self.assertEqual(spec["phenomenon_class_id"], "evolutionary_phylogenetic_patterns")
        self.assertEqual(spec["official_data_source"]["source_id"], "biology_ncbi_taxonomy_lca_lineage_v1")
        self.assertEqual(dispatcher.validate_executable_spec(spec, context=lane["stable_id"]), [])
        self.assertEqual(lane["coverage_closure"]["current_status"], "OPEN_FAIL_CLOSED_NO_EXECUTABLE_EVIDENCE")
        self.assertFalse(lane["evidence_gate"]["executable_evidence_exists"])
        self.assertFalse(lane["evidence_gate"]["closure_allowed"])

    def test_domain_local_evidence_is_lifted_into_central_queue_without_closure(self) -> None:
        dispatcher = load_dispatcher()
        queue = dispatcher.build_queue(REPO_ROOT)
        lanes = [
            row
            for row in queue["lanes"]
            if row["domain_class_id"] == "agricultural_food_sciences"
            and row["phenomenon_class_id"] == "food_chemistry_safety_and_nutrition"
        ]

        self.assertEqual(len(lanes), 1)
        lane = lanes[0]
        spec = lane["executable_work_order"]
        bridge = spec["domain_local_bridge"]

        self.assertEqual(spec["official_data_source"]["source_id"], "USDA_FOODDATA_CENTRAL_API")
        self.assertTrue(spec["current_evidence"]["executable_evidence_exists"])
        self.assertEqual(
            spec["current_evidence"]["executable_evidence_ref"],
            "validation/heldout/grand_science/agriculture/coverage_work_orders/OC133_AGRICULTURE_FDC_SODIUM_SCORING_PACK.json",
        )
        self.assertTrue(bridge["artifact_exists_is_not_closure"])
        self.assertFalse(bridge["coverage_closure_allowed"])
        self.assertEqual(lane["evidence_gate"]["status"], "EVIDENCE_BOUND_PENDING_REVIEW")
        self.assertFalse(lane["evidence_gate"]["closure_allowed"])
        self.assertFalse(lane["coverage_closure"]["mark_closed_allowed"])

    def test_registry_rejects_conflicting_duplicate_specs_but_allows_identical_duplicates(self) -> None:
        dispatcher = load_dispatcher()
        key = ("physical_sciences", "dynamical_laws_and_conservation")
        builtin_spec = dispatcher.build_builtin_executable_spec_registry()[key]

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            specs_dir = root / dispatcher.COVERAGE_EXECUTABLE_SPECS_REL
            specs_dir.mkdir(parents=True)
            (specs_dir / "identical.json").write_text(json.dumps(builtin_spec, indent=2) + "\n", encoding="utf-8")
            registry = dispatcher.load_executable_spec_registry(root)
            self.assertEqual(registry[key], builtin_spec)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            specs_dir = root / dispatcher.COVERAGE_EXECUTABLE_SPECS_REL
            specs_dir.mkdir(parents=True)
            conflicting = copy.deepcopy(builtin_spec)
            conflicting["official_data_source"]["source_id"] = "conflicting_duplicate_source"
            (specs_dir / "conflict.json").write_text(json.dumps(conflicting, indent=2) + "\n", encoding="utf-8")
            with self.assertRaises(dispatcher.ExecutableSpecRegistryError) as raised:
                dispatcher.load_executable_spec_registry(root)
            self.assertIn("EXECUTABLE_SPEC_DUPLICATE_CONFLICT", "\n".join(raised.exception.errors))

    def test_registry_rejects_placeholder_plugin_specs(self) -> None:
        dispatcher = load_dispatcher()
        key = ("biological_life_sciences", "evolutionary_phylogenetic_patterns")
        sample_spec = dispatcher.load_executable_spec_registry(REPO_ROOT)[key]
        placeholder_spec = copy.deepcopy(sample_spec)
        placeholder_spec["official_data_source"]["source_name"] = "TBD"

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            specs_dir = root / dispatcher.COVERAGE_EXECUTABLE_SPECS_REL
            specs_dir.mkdir(parents=True)
            (specs_dir / "placeholder.json").write_text(json.dumps(placeholder_spec, indent=2) + "\n", encoding="utf-8")
            with self.assertRaises(dispatcher.ExecutableSpecRegistryError) as raised:
                dispatcher.load_executable_spec_registry(root)
            self.assertIn("PLACEHOLDER_TOKEN_IN_EXECUTABLE_SPEC", "\n".join(raised.exception.errors))

    def test_mathematics_gaps_are_formal_route_protocol_only(self) -> None:
        dispatcher = load_dispatcher()
        queue = dispatcher.build_queue(REPO_ROOT)
        math_lanes = [row for row in queue["lanes"] if row["domain_class_id"] == "formal_mathematics_and_logic"]

        self.assertEqual(len(math_lanes), 3)
        for lane in math_lanes:
            self.assertEqual(lane["lane_route"], "FORMAL_ROUTE_PROTOCOL_ONLY")
            self.assertIn("NO_EMPIRICAL_PROTOCOL_OR_PREDICTION_SUPPORT_ASSERTED", lane["expected_acceptance_predicates"])
            self.assertFalse(any(item["lane_role"] == "target_acquisition" for item in lane["required_data_lanes"]))
            self.assertEqual(lane["resource_estimate"]["minimum_evidence_pack_n"], "formal-equivalent review only; no empirical n asserted")

    def test_telemetry_blocks_broad_superiority_while_gaps_remain(self) -> None:
        dispatcher = load_dispatcher()
        queue = dispatcher.build_queue(REPO_ROOT)
        telemetry = dispatcher.build_telemetry(queue)

        self.assertTrue(telemetry["coverage_gaps_remain"])
        self.assertFalse(telemetry["broad_modern_science_superiority_certified"])
        self.assertFalse(telemetry["release_promotion_allowed"])
        self.assertEqual(len(telemetry["top_planned_lanes"]), 5)

    def test_stored_work_orders_are_concrete_and_synchronized(self) -> None:
        dispatcher = load_dispatcher()
        work_orders = dispatcher.load_json(REPO_ROOT / dispatcher.WORK_ORDERS_REL)
        expected = dispatcher.build_concrete_work_orders(REPO_ROOT)

        self.assertEqual(work_orders, expected)
        self.assertEqual(work_orders["executable_work_order_total"], 29)
        self.assertEqual(work_orders["physics_chemistry_executable_work_order_total"], 6)
        self.assertEqual(dispatcher.validate_work_orders_payload(work_orders), [])
        self.assertEqual(dispatcher.check_stored(REPO_ROOT), [])


if __name__ == "__main__":
    unittest.main()
