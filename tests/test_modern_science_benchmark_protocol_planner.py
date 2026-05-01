from __future__ import annotations

import copy
import unittest
from pathlib import Path

from tools import oc133_modern_science_benchmark_protocol_planner as planner


REPO_ROOT = Path(__file__).resolve().parents[1]

DOMAINS = ("physics", "chemistry", "biology", "systems", "mathematics")


def expected_protocol_rel(domain: str) -> str:
    return f"{planner.PROTOCOL_DIR_REL}/{planner.protocol_file_name(domain)}"


class ModernScienceBenchmarkProtocolPlannerTests(unittest.TestCase):
    def test_stored_protocols_are_synchronized_with_deterministic_builder(self) -> None:
        payloads = planner.build_all(REPO_ROOT)
        self.assertEqual(len([key for key in payloads if key.startswith(f"{planner.PROTOCOL_DIR_REL}/OC133_MODERN_SCIENCE_BENCHMARK_PROTOCOL_")]), 5)
        self.assertEqual(len(payloads[f"{planner.PROTOCOL_DIR_REL}/index.json"]["protocol_rows"]), 5)
        self.assertEqual(planner.check_stored(REPO_ROOT), [])

    def test_protocols_emit_required_superiority_obligations(self) -> None:
        payloads = planner.build_all(REPO_ROOT)
        index = payloads[f"{planner.PROTOCOL_DIR_REL}/index.json"]
        self.assertEqual(index["protocol_total"], len(DOMAINS))
        self.assertEqual({row["domain"] for row in index["protocol_rows"]}, set(DOMAINS))

        for domain in DOMAINS:
            protocol = payloads[expected_protocol_rel(domain)]
            self.assertEqual(protocol["domain"], domain)
            self.assertFalse(protocol["superiority_decision"]["superiority_certified"])
            self.assertEqual(protocol["schema_id"], planner.SCHEMA_ID)
            self.assertEqual(protocol["superiority_decision"]["release_promotion_allowed"], False)
            self.assertIn("incumbent_comparator", protocol)
            self.assertIn("oc_model_under_test", protocol)
            self.assertIn("heldout_or_prospective_split", protocol)
            self.assertIn("fairness_criteria", protocol)
            self.assertIn("uncertainty", protocol)
            self.assertIn("residual_metric", protocol)
            self.assertIn("negative_controls", protocol)
            self.assertIn("falsifiers", protocol)
            self.assertIn("blocker_predicates", protocol)
            self.assertIn("required_result_refs", protocol)
            if domain == "mathematics":
                self.assertEqual(protocol["route_type"], "FORMAL_ROUTE_PROTOCOL_ONLY")
                self.assertEqual(protocol["required_result_refs"], [])
                self.assertTrue(protocol["formal_route"]["protocol_only"])
                self.assertFalse(protocol["formal_route"]["empirical_protocol_required"])
                self.assertFalse(protocol["oc_model_under_test"]["prediction_support_allowed"])
                self.assertFalse(protocol["oc_model_under_test"]["empirical_support_allowed"])
            else:
                self.assertNotEqual(protocol.get("route_type"), "FORMAL_ROUTE_PROTOCOL_ONLY")
                self.assertTrue(protocol["required_result_refs"])
            self.assertIsInstance(protocol["fairness_criteria"], list)
            for criterion in protocol["fairness_criteria"]:
                self.assertIn("predicate", criterion)
                self.assertIn("required", criterion)
                self.assertIn("status", criterion)

    def test_protocol_cannot_certify_without_actual_result_refs_and_zero_blockers(self) -> None:
        payloads = planner.build_all(REPO_ROOT)
        protocol = copy.deepcopy(payloads[expected_protocol_rel("physics")])

        # Missing result refs cannot certify.
        protocol["required_result_refs"] = []
        protocol["superiority_decision"]["blocker_predicates"] = []
        protocol["superiority_decision"]["blocker_total"] = 0
        for criterion in protocol["fairness_criteria"]:
            criterion["status"] = True
        protocol["superiority_decision"]["can_be_certified_within_current_artifact_scope"] = planner.can_certify_superiority(protocol)
        self.assertFalse(planner.can_certify_superiority(protocol))
        self.assertFalse(protocol["superiority_decision"]["can_be_certified_within_current_artifact_scope"])

        # Result refs present but blocker predicates still block certification.
        protocol["required_result_refs"] = ["validation/target_blind/OC133_TARGET_BLIND_PREDICTION_TABLE.json::OC133-TARGETBLIND-PHYSICS-001"]
        protocol["superiority_decision"]["blocker_predicates"] = ["independent_replay_passes_from_clean_checkout"]
        protocol["superiority_decision"]["blocker_total"] = 1
        protocol["superiority_decision"]["can_be_certified_within_current_artifact_scope"] = planner.can_certify_superiority(protocol)
        self.assertFalse(planner.can_certify_superiority(protocol))
        self.assertFalse(protocol["superiority_decision"]["can_be_certified_within_current_artifact_scope"])

    def test_can_certify_when_refs_and_predicates_are_present_and_no_blockers(self) -> None:
        payloads = planner.build_all(REPO_ROOT)
        protocol = copy.deepcopy(payloads[expected_protocol_rel("physics")])
        protocol["required_result_refs"] = ["validation/target_blind/OC133_TARGET_BLIND_PREDICTION_TABLE.json::OC133-TARGETBLIND-PHYSICS-001"]
        protocol["superiority_decision"]["blocker_predicates"] = []
        protocol["superiority_decision"]["blocker_total"] = 0
        for criterion in protocol["fairness_criteria"]:
            criterion["status"] = True
        protocol["superiority_decision"]["can_be_certified_within_current_artifact_scope"] = planner.can_certify_superiority(protocol)
        self.assertTrue(protocol["superiority_decision"]["can_be_certified_within_current_artifact_scope"])
        self.assertFalse(protocol["superiority_decision"]["superiority_certified"])


if __name__ == "__main__":
    unittest.main()
