from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
FACTORY_PATH = REPO_ROOT / "tools" / "oc133_modern_science_comparator_factory.py"


def load_factory():
    spec = importlib.util.spec_from_file_location("oc133_modern_science_comparator_factory", FACTORY_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ModernScienceComparatorFactoryTests(unittest.TestCase):
    def test_factory_rebuilds_stored_register_and_report(self) -> None:
        factory = load_factory()
        self.assertEqual(factory.check_stored(REPO_ROOT), [])

    def test_current_strict_pack_refs_are_recognized_and_narrowly_certified(self) -> None:
        factory = load_factory()
        matrix = factory.build_domain_evidence_matrix(REPO_ROOT)
        self.assertEqual({row["domain"] for row in matrix}, set(factory.EMPIRICAL_DOMAINS))

        for row in matrix:
            domain = row["domain"]
            strict_pack = row["strict_evidence_pack"]
            predicates = strict_pack["validation_predicates"]
            self.assertEqual(strict_pack["ref"], factory.CURRENT_PACK_REFS[domain])
            self.assertTrue(strict_pack["sha256"])
            self.assertTrue(strict_pack["source_refs"])
            self.assertTrue(all(predicates.values()), strict_pack["validation_failures"])
            self.assertNotIn("validation/target_blind/OC133_TARGET_BLIND_PREDICTION_TABLE.json", strict_pack["ref"])
            self.assertEqual(row["oc_result"]["result_kind"], "STRICT_BENCHMARK_SCOPED_CANDIDATE_PACK")
            self.assertTrue(row["comparator_result"]["pre_registered"])
            self.assertGreater(row["comparator_result"]["comparator_residual"], row["oc_result"]["model_residual"])
            self.assertTrue(row["certification_verdict"]["benchmark_scoped_superiority"]["certified"])
            self.assertEqual(
                row["certification_verdict"]["benchmark_scoped_superiority"]["label"],
                "CERTIFIED_AGAINST_DECLARED_INCUMBENT_BENCHMARK_BASELINES",
            )
            self.assertFalse(row["certification_verdict"]["broad_modern_science_superiority"]["certified"])

    def test_stale_old_row_refs_fail_closed(self) -> None:
        factory = load_factory()
        register = copy.deepcopy(factory.build_all(REPO_ROOT)[factory.REGISTER_REL])
        register["domain_evidence_matrix"][0]["strict_evidence_pack"]["ref"] = (
            "validation/target_blind/OC133_TARGET_BLIND_PREDICTION_TABLE.json::OC133-TARGETBLIND-PHYSICS-001"
        )

        errors = factory.validate_register_payload(register, REPO_ROOT)

        self.assertTrue(any(error.startswith("STALE_OR_UNREGISTERED_EVIDENCE_PACK_REF::") for error in errors))
        self.assertTrue(any(error.startswith("STALE_OLD_ROW_REF_USED::") for error in errors))

    def test_stale_pack_hash_fails_closed(self) -> None:
        factory = load_factory()
        register = copy.deepcopy(factory.build_all(REPO_ROOT)[factory.REGISTER_REL])
        register["domain_evidence_matrix"][1]["strict_evidence_pack"]["sha256"] = "0" * 64

        errors = factory.validate_register_payload(register, REPO_ROOT)

        self.assertTrue(any(error.startswith("STALE_OR_MISMATCHED_EVIDENCE_PACK_HASH::") for error in errors))

    def test_missing_source_refs_fail_closed(self) -> None:
        factory = load_factory()
        register = copy.deepcopy(factory.build_all(REPO_ROOT)[factory.REGISTER_REL])
        register["domain_evidence_matrix"][2]["strict_evidence_pack"]["source_refs"] = []

        errors = factory.validate_register_payload(register, REPO_ROOT)

        self.assertTrue(any(error.startswith("MISSING_SOURCE_REFS::") for error in errors))

    def test_broad_modern_science_superiority_cannot_pass_without_all_broad_predicates(self) -> None:
        factory = load_factory()
        register = copy.deepcopy(factory.build_all(REPO_ROOT)[factory.REGISTER_REL])
        register["modern_science_comparator_superiority"]["state"] = "PASS"
        register["domain_evidence_matrix"][0]["certification_verdict"]["broad_modern_science_superiority"]["certified"] = True

        errors = factory.validate_register_payload(register, REPO_ROOT)

        self.assertIn("BROAD_MODERN_SCIENCE_SUPERIORITY_PASS_WITH_FAILED_PREDICATES", errors)
        self.assertTrue(any(error.startswith("UNSUPPORTED_BROAD_MODERN_SCIENCE_CERTIFICATION::") for error in errors))

    def test_clean_temp_tree_replay_certificate_closes_independent_predicate(self) -> None:
        factory = load_factory()
        register = factory.build_all(REPO_ROOT)[factory.REGISTER_REL]
        replay = register["independent_clean_checkout_replay"]

        self.assertEqual(replay["status"], "PASS")
        self.assertTrue(replay["satisfies_register_predicate"])
        self.assertTrue(register["broad_claim_predicates"]["independent_clean_checkout_replay_bound_to_register"])
        self.assertEqual(replay["selected_evidence_pack_refs"], factory.CURRENT_PACK_REFS)
        self.assertEqual(replay["selected_evidence_pack_sha256"], factory.get_pack_ref_hashes(REPO_ROOT))
        self.assertTrue(replay["command_results"])
        self.assertFalse(replay["no_send_locks"]["public_release_action_allowed"])
        self.assertFalse(register["broad_claim_predicates"]["coverage_extends_to_all_of_modern_science"])

    def test_clean_temp_tree_replay_hash_mismatch_fails_closed(self) -> None:
        factory = load_factory()
        register = copy.deepcopy(factory.build_all(REPO_ROOT)[factory.REGISTER_REL])
        register["independent_clean_checkout_replay"]["report_sha256"] = "0" * 64

        errors = factory.validate_register_payload(register, REPO_ROOT)

        self.assertIn("INDEPENDENT_REPLAY_CERTIFICATE_HASH_MISMATCH", errors)

    def test_coverage_register_blocks_four_domain_overclaim(self) -> None:
        factory = load_factory()
        payload = factory.build_all(REPO_ROOT)
        coverage = payload[factory.COVERAGE_REGISTER_REL]
        work_orders = payload[factory.COVERAGE_WORK_ORDERS_REL]

        self.assertEqual(coverage["taxonomy_source"]["source_policy"], "internally_declared_coverage_taxonomy")
        self.assertGreater(coverage["required_domain_class_total"], len(factory.EMPIRICAL_DOMAINS))
        self.assertGreater(coverage["coverage_gap_total"], 0)
        self.assertFalse(coverage["coverage_closure_decision"]["coverage_extends_to_all_of_modern_science"])
        self.assertEqual(work_orders["open_work_order_total"], coverage["coverage_gap_total"])
        self.assertEqual(factory.validate_coverage_payload(coverage, work_orders), [])

    def test_coverage_work_orders_are_dispatcher_owned_executable_shape(self) -> None:
        factory = load_factory()
        dispatcher = factory.load_coverage_lane_dispatcher()
        payload = factory.build_all(REPO_ROOT)
        coverage = payload[factory.COVERAGE_REGISTER_REL]
        work_orders = payload[factory.COVERAGE_WORK_ORDERS_REL]

        self.assertEqual(work_orders, dispatcher.build_concrete_work_orders(REPO_ROOT, coverage_register=coverage))
        self.assertEqual(work_orders["automation_ref"], dispatcher.DISPATCHER_REF)
        self.assertEqual(work_orders["executable_work_order_total"], 29)
        self.assertEqual(work_orders["physics_chemistry_executable_work_order_total"], 6)

        rows = {row["work_order_id"]: row for row in work_orders["work_orders"]}
        for index in range(4, 10):
            row = rows[f"MS-COV-WO-{index:03d}"]
            context = dispatcher.stable_lane_id(row)
            self.assertEqual(row["current_status"], "OPEN_FAIL_CLOSED_NO_EXECUTABLE_EVIDENCE")
            self.assertFalse(row["coverage_closure_policy"]["mark_closed_allowed"])
            self.assertIn("EXECUTABLE_LANE_SPEC_DECLARED", row["acceptance_predicates"])
            self.assertIn("FAIL_CLOSED_UNLESS_EXECUTABLE_EVIDENCE_BOUND", row["acceptance_predicates"])
            self.assertEqual(dispatcher.validate_executable_spec(row.get("executable_lane_spec"), context=context), [])

    def test_comparator_expected_work_orders_include_plugin_executable_spec(self) -> None:
        factory = load_factory()
        payload = factory.build_all(REPO_ROOT)
        work_orders = payload[factory.COVERAGE_WORK_ORDERS_REL]
        plugin_rows = [
            row
            for row in work_orders["work_orders"]
            if row["domain_class_id"] == "biological_life_sciences"
            and row["phenomenon_class_id"] == "evolutionary_phylogenetic_patterns"
        ]

        self.assertEqual(len(plugin_rows), 1)
        plugin_row = plugin_rows[0]
        self.assertEqual(plugin_row["current_status"], "OPEN_FAIL_CLOSED_NO_EXECUTABLE_EVIDENCE")
        self.assertFalse(plugin_row["coverage_closure_policy"]["mark_closed_allowed"])
        self.assertEqual(
            plugin_row["executable_lane_spec"]["official_data_source"]["source_id"],
            "biology_ncbi_taxonomy_lca_lineage_v1",
        )
        self.assertIn("EXECUTABLE_LANE_SPEC_DECLARED", plugin_row["acceptance_predicates"])

    def test_missing_dispatcher_executable_spec_fails_coverage_validation(self) -> None:
        factory = load_factory()
        payload = factory.build_all(REPO_ROOT)
        coverage = payload[factory.COVERAGE_REGISTER_REL]
        work_orders = copy.deepcopy(payload[factory.COVERAGE_WORK_ORDERS_REL])
        work_orders["work_orders"][3].pop("executable_lane_spec")

        errors = factory.validate_coverage_payload(coverage, work_orders)

        self.assertIn("COVERAGE_WORK_ORDERS_NOT_SYNCHRONIZED_WITH_DISPATCHER", errors)
        self.assertTrue(any(error.startswith("PHYSICS_CHEMISTRY_EXECUTABLE_SPEC_MISSING::MS-COV-WO-004::") for error in errors))

    def test_coverage_gaps_prevent_broad_pass_even_if_someone_flips_state(self) -> None:
        factory = load_factory()
        register = copy.deepcopy(factory.build_all(REPO_ROOT)[factory.REGISTER_REL])
        register["modern_science_comparator_superiority"]["state"] = "PASS"
        register["broad_claim_predicates"]["coverage_extends_to_all_of_modern_science"] = True

        errors = factory.validate_register_payload(register, REPO_ROOT)

        self.assertIn("BROAD_MODERN_SCIENCE_SUPERIORITY_PASS_WITH_COVERAGE_GAPS", errors)

    def test_coverage_closure_true_with_gaps_fails_closed(self) -> None:
        factory = load_factory()
        payload = factory.build_all(REPO_ROOT)
        coverage = copy.deepcopy(payload[factory.COVERAGE_REGISTER_REL])
        work_orders = payload[factory.COVERAGE_WORK_ORDERS_REL]
        coverage["coverage_closure_decision"]["coverage_extends_to_all_of_modern_science"] = True

        errors = factory.validate_coverage_payload(coverage, work_orders)

        self.assertIn("COVERAGE_EXTENDS_TRUE_WITH_GAPS", errors)


if __name__ == "__main__":
    unittest.main()
