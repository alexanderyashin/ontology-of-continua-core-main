from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from validation.grand_science import evidence_pack_factory as factory


def write_json(root: Path, rel_path: str, payload: dict) -> None:
    path = root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def base_requirements(domains: list[str]) -> dict:
    return {
        "schema_id": "OC133_GRAND_EMPIRICAL_DOMAIN_REQUIREMENTS_v1",
        "release_id": "oc_core_1_3_3",
        "capability_owner": "Research/EmpiricalScience",
        "minimum_per_domain_n": 20,
        "required_domains": domains,
        "required_source_separation_modes": ["prospective", "target_blind"],
        "candidate_evidence_pack_roots": ["validation/heldout", "validation/grand_science"],
        "criteria": {
            "source_separation_required": True,
            "target_hidden_until_scoring_required": True,
            "pre_target_lock_required": True,
            "comparator_baseline_required": True,
            "uncertainty_interval_required": True,
            "residual_superiority_required": True,
            "negative_control_rejection_required": True,
            "falsifier_required": True,
            "grand_toe_support_allowed_must_be_explicit": True,
        },
        "support_policy": "fixture policy",
    }


def valid_pack(domain: str = "physics") -> dict:
    return {
        "schema_id": "OC133_GRAND_EMPIRICAL_EVIDENCE_v1",
        "release_id": "oc_core_1_3_3",
        "capability_owner": "Research/EmpiricalScience",
        "evidence_pack_id": f"PACK-{domain.upper()}-001",
        "domain": domain,
        "source_separation": {
            "mode": "target_blind",
            "pre_target_lock": True,
            "target_hidden_until_scoring": True,
            "training_sources": ["training-snapshot-a"],
            "target_sources": ["target-snapshot-b"],
        },
        "n": 20,
        "model_under_test": "pre-registered OC scoring rule",
        "comparator_baseline": {
            "name": "pre-registered comparator",
            "prediction_rule": "comparator scoring rule",
            "pre_registered": True,
        },
        "uncertainty": {
            "metric": "absolute residual",
            "method": "pre-registered interval",
            "interval": [0.0, 0.1],
        },
        "residuals": {
            "model": 0.05,
            "comparator": 0.15,
            "superiority_margin": 0.1,
        },
        "negative_controls": [
            {
                "control_id": "permuted-targets",
                "description": "permuted target labels must fail",
                "rejected": True,
            }
        ],
        "falsifiers": ["model residual exceeds uncertainty interval"],
        "grand_toe_support_allowed": True,
    }


class GrandEmpiricalFactoryTests(unittest.TestCase):
    def _minimal_root(self, root: Path, domains: list[str]) -> None:
        write_json(root, factory.REQUIREMENTS_REL, base_requirements(domains))
        write_json(
            root,
            factory.REGISTRY_REL,
            {
                "schema_id": "OC133_GRAND_SCIENCE_HELDOUT_REGISTRY_v1",
                "release_id": "oc_core_1_3_3",
                "capability_owner": "Research/EmpiricalScience",
                "evidence_pack_refs": [],
            },
        )

    def test_empty_registry_builds_decomposition_queue_and_keeps_blocker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._minimal_root(root, ["physics", "chemistry"])
            sample = valid_pack("physics")
            sample["evidence_pack_id"] = "SAMPLE_ONLY_DO_NOT_REGISTER"
            write_json(root, factory.SAMPLE_PACK_REL, sample)

            payload = factory.build_grand_empirical_payload(root)

            self.assertEqual(payload["verdict"], "BLOCKED_PENDING_GENUINE_PER_DOMAIN_EVIDENCE")
            self.assertFalse(payload["grand_toe_support_allowed"])
            self.assertEqual(payload["evidence_pack_total"], 0)
            self.assertEqual(payload["blocked_domain_total"], 2)
            self.assertEqual(payload["decomposition_queue_total"], 2)
            self.assertTrue(all(row["blocker_id"] == "grand_toe_empirical_superiority" for row in payload["decomposition_queue"]))

    def test_valid_registered_pack_satisfies_single_domain_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._minimal_root(root, ["physics"])
            write_json(root, "validation/heldout/physics_pack.json", valid_pack("physics"))
            write_json(
                root,
                factory.REGISTRY_REL,
                {
                    "schema_id": "OC133_GRAND_SCIENCE_HELDOUT_REGISTRY_v1",
                    "release_id": "oc_core_1_3_3",
                    "capability_owner": "Research/EmpiricalScience",
                    "evidence_pack_refs": ["validation/heldout/physics_pack.json"],
                },
            )

            payload = factory.build_grand_empirical_payload(root)

            self.assertEqual(payload["blocked_domain_total"], 0)
            self.assertTrue(payload["grand_toe_support_allowed"])
            self.assertEqual(payload["valid_evidence_pack_total"], 1)
            self.assertEqual(payload["domains"][0]["valid_n"], 20)
            self.assertEqual(payload["decomposition_queue_total"], 0)

    def test_invalid_candidate_reports_strict_failure_reasons(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._minimal_root(root, ["physics"])
            pack = valid_pack("physics")
            pack["n"] = 19
            pack["source_separation"]["target_sources"] = ["training-snapshot-a"]
            pack["residuals"] = {"model": 0.2, "comparator": 0.1, "superiority_margin": -0.1}
            pack["negative_controls"][0]["rejected"] = False
            pack["grand_toe_support_allowed"] = False
            write_json(root, "validation/heldout/bad_physics_pack.json", pack)

            payload = factory.build_grand_empirical_payload(root)
            failures = payload["candidate_rows"][0]["failures"]

            self.assertIn("N_BELOW_MINIMUM::20", failures)
            self.assertIn("TRAINING_TARGET_SOURCE_OVERLAP", failures)
            self.assertIn("COMPARATOR_NOT_WORSE_THAN_MODEL", failures)
            self.assertIn("NEGATIVE_CONTROL_NOT_REJECTED::0", failures)
            self.assertIn("GRAND_TOE_SUPPORT_NOT_ALLOWED", failures)
            self.assertEqual(payload["blocked_domain_total"], 1)
            self.assertFalse(payload["grand_toe_support_allowed"])

    def test_discovery_ignores_operational_status_reports_that_are_not_packs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._minimal_root(root, ["physics"])
            write_json(
                root,
                "validation/heldout/status_report.json",
                {
                    "schema_id": "SOME_OPERATIONAL_REPORT",
                    "release_id": "oc_core_1_3_3",
                    "grand_toe_support_allowed": False,
                    "verdict": "BLOCKED",
                },
            )

            payload = factory.build_grand_empirical_payload(root)

            self.assertEqual(payload["evidence_pack_total"], 0)
            self.assertEqual(payload["evidence_pack_failure_total"], 0)


if __name__ == "__main__":
    unittest.main()
