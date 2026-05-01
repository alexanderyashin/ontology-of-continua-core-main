from __future__ import annotations

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

    def test_domain_matrix_separates_required_roles_without_certifying_superiority(self) -> None:
        factory = load_factory()
        matrix = factory.build_domain_evidence_matrix(REPO_ROOT)
        self.assertEqual({row["domain"] for row in matrix}, set(factory.REQUIRED_DOMAINS))
        required_roles = set(factory.DISTINCTION_ROLES)

        for row in matrix:
            self.assertEqual(set(row["distinction_roles_present"]), required_roles)
            self.assertTrue(row["incumbent_modern_science_source"]["source_refs"])
            self.assertEqual(row["oc_result"]["result_kind"], "BOUNDED_TARGET_BLIND_RECONSTRUCTION_NOT_SUPERIORITY")
            self.assertTrue(row["oc_result"]["result_ref"].startswith(factory.TARGET_BLIND_REL))
            self.assertTrue(row["comparator_result"]["baseline_name"])
            self.assertIsNotNone(row["comparator_result"]["comparator_residual"])
            self.assertTrue(row["benchmark_predicate"]["certification_predicates"])
            self.assertIn("BLOCKED", row["benchmark_predicate"]["current_verdict"])
            self.assertEqual(row["uncertainty_fairness"]["fairness_verdict"], "BOUNDED_FAIRNESS_INSUFFICIENT_FOR_SUPERIORITY")
            self.assertTrue(row["blocker_reason"]["blocked_by"])
            self.assertEqual(row["superiority_decision"]["status"], "NOT_CERTIFIED")
            self.assertFalse(row["superiority_decision"]["certified"])
            self.assertTrue(row["work_order_decomposition"])


if __name__ == "__main__":
    unittest.main()
