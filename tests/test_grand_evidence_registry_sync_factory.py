from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tests.test_grand_empirical_factory import base_requirements, valid_pack
from tools import oc133_grand_evidence_registry_sync_factory as sync
from validation.grand_science import evidence_pack_factory as grand_factory


def write_json(root: Path, rel_path: str, payload: dict) -> None:
    path = root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n")


class GrandEvidenceRegistrySyncFactoryTests(unittest.TestCase):
    def _minimal_root(self, root: Path, domains: list[str]) -> None:
        write_json(root, grand_factory.REQUIREMENTS_REL, base_requirements(domains))
        write_json(
            root,
            grand_factory.REGISTRY_REL,
            {
                "schema_id": "OC133_GRAND_SCIENCE_HELDOUT_REGISTRY_v1",
                "release_id": "oc_core_1_3_3",
                "capability_owner": "Research/EmpiricalScience",
                "evidence_pack_refs": [],
            },
        )

    def test_write_registers_only_strictly_valid_discovered_packs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._minimal_root(root, ["physics"])
            pack_ref = "validation/heldout/physics_pack.json"
            write_json(root, pack_ref, valid_pack("physics"))

            payload = sync.build_payload(root, write=True)
            registry = json.loads((root / grand_factory.REGISTRY_REL).read_text(encoding="utf-8"))

            self.assertEqual(payload["verdict"], "REGISTRY_SYNC_APPLIED_VALID_PACKS")
            self.assertEqual(payload["new_valid_refs"], [pack_ref])
            self.assertEqual(registry["evidence_pack_refs"], [pack_ref])
            self.assertEqual(payload["blocked_domain_total_after_sync"], 0)
            self.assertTrue((root / sync.REPORT_JSON_REL).exists())
            self.assertTrue((root / sync.WORK_ORDERS_REL).exists())

    def test_write_binds_registry_reports_and_work_orders_to_same_gate_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._minimal_root(root, ["physics"])
            pack_ref = "validation/heldout/physics_pack.json"
            write_json(root, pack_ref, valid_pack("physics"))

            payload = sync.build_payload(root, write=True)
            registry = json.loads((root / grand_factory.REGISTRY_REL).read_text(encoding="utf-8"))
            grand_report = json.loads((root / grand_factory.REPORT_JSON_REL).read_text(encoding="utf-8"))
            work_orders = json.loads((root / sync.WORK_ORDERS_REL).read_text(encoding="utf-8"))

            run_ids = {
                payload["sync_run_id"],
                registry["sync_run_id"],
                grand_report["sync_run_id"],
                work_orders["sync_run_id"],
            }
            source_hashes = {
                payload["source_artifact_set_sha256"],
                registry["source_artifact_set_sha256"],
                grand_report["source_artifact_set_sha256"],
                work_orders["source_artifact_set_sha256"],
            }
            self.assertEqual(len(run_ids), 1)
            self.assertEqual(len(source_hashes), 1)
            self.assertEqual(registry["evidence_pack_refs"], [pack_ref])
            self.assertEqual(grand_report["selected_valid_evidence_pack_refs"], [pack_ref])
            self.assertEqual(sync.check_stored(root), [])

    def test_checker_compares_present_sync_identity_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._minimal_root(root, ["physics"])
            pack_ref = "validation/heldout/physics_pack.json"
            write_json(root, pack_ref, valid_pack("physics"))

            sync.build_payload(root, write=True)
            grand_report = json.loads((root / grand_factory.REPORT_JSON_REL).read_text(encoding="utf-8"))
            for key in ("sync_run_id", "gate_run_id", "source_artifact_set_sha256", "source_artifact_hashes"):
                grand_report.pop(key, None)
            write_json(root, grand_factory.REPORT_JSON_REL, grand_report)

            self.assertEqual(sync.check_stored(root), [])

            work_orders = json.loads((root / sync.WORK_ORDERS_REL).read_text(encoding="utf-8"))
            original_run_id = work_orders["sync_run_id"]
            work_orders["sync_run_id"] = "OC133-GRAND-GATE-DIVERGED"
            write_json(root, sync.WORK_ORDERS_REL, work_orders)

            errors = sync.check_stored(root)

            self.assertTrue(any("sync_run_id mismatch across artifacts" in error for error in errors))

            work_orders["sync_run_id"] = original_run_id
            work_orders["source_artifact_set_sha256"] = "diverged-source-artifact-set-sha256"
            write_json(root, sync.WORK_ORDERS_REL, work_orders)

            errors = sync.check_stored(root)

            self.assertTrue(
                any("source_artifact_set_sha256 mismatch across artifacts" in error for error in errors)
            )

    def test_invalid_pack_is_not_registered_and_becomes_repair_work_order(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._minimal_root(root, ["physics"])
            pack = valid_pack("physics")
            pack["n"] = 3
            pack["source_separation"]["target_sources"] = ["training-snapshot-a"]
            pack["grand_toe_support_allowed"] = False
            write_json(root, "validation/heldout/bad_physics_pack.json", pack)

            payload = sync.build_payload(root, write=True)
            registry = json.loads((root / grand_factory.REGISTRY_REL).read_text(encoding="utf-8"))
            work_orders = json.loads((root / sync.WORK_ORDERS_REL).read_text(encoding="utf-8"))
            failure_classes = {row["failure_class"] for row in work_orders["rows"]}

            self.assertEqual(payload["verdict"], "REGISTRY_SYNC_BLOCKED_PENDING_VALID_PACKS")
            self.assertEqual(registry["evidence_pack_refs"], [])
            self.assertIn("insufficient_sample_size", failure_classes)
            self.assertIn("source_separation_failure", failure_classes)
            self.assertIn("grand_support_not_authorized", failure_classes)
            self.assertGreater(payload["open_repair_work_order_total"], 0)

    def test_checker_catches_registry_extra_ref_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._minimal_root(root, ["physics"])
            pack_ref = "validation/heldout/physics_pack.json"
            stale_ref = "validation/heldout/stale_physics_pack.json"
            write_json(root, pack_ref, valid_pack("physics"))
            stale = valid_pack("physics")
            stale["evidence_pack_id"] = "PACK-PHYSICS-STALE"
            stale["n"] = 3
            stale["grand_toe_support_allowed"] = False
            write_json(root, stale_ref, stale)

            sync.build_payload(root, write=True)
            registry = json.loads((root / grand_factory.REGISTRY_REL).read_text(encoding="utf-8"))
            registry["evidence_pack_refs"].append(stale_ref)
            write_json(root, grand_factory.REGISTRY_REL, registry)

            errors = sync.check_stored(root)

            self.assertTrue(any("registry refs not selected by grand report" in error for error in errors))

    def test_checker_catches_report_valid_ref_missing_from_registry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._minimal_root(root, ["physics"])
            pack_ref = "validation/heldout/physics_pack.json"
            write_json(root, pack_ref, valid_pack("physics"))

            sync.build_payload(root, write=True)
            registry = json.loads((root / grand_factory.REGISTRY_REL).read_text(encoding="utf-8"))
            registry["evidence_pack_refs"] = []
            write_json(root, grand_factory.REGISTRY_REL, registry)

            errors = sync.check_stored(root)

            self.assertTrue(any("grand report selected valid refs missing from registry" in error for error in errors))

    def test_checker_catches_open_work_order_for_valid_non_blocked_domain(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._minimal_root(root, ["physics"])
            pack_ref = "validation/heldout/physics_pack.json"
            write_json(root, pack_ref, valid_pack("physics"))

            sync.build_payload(root, write=True)
            work_orders = json.loads((root / sync.WORK_ORDERS_REL).read_text(encoding="utf-8"))
            work_orders["rows"] = [
                {
                    "work_order_id": "WO-DRIFT-PHYSICS",
                    "domain": "physics",
                    "failure_class": "insufficient_sample_size",
                    "status": "OPEN",
                    "candidate_refs": [pack_ref],
                    "candidate_artifacts": [
                        {
                            "source_ref": pack_ref,
                            "candidate_sha256": "fixture-hash",
                        }
                    ],
                }
            ]
            write_json(root, sync.WORK_ORDERS_REL, work_orders)

            errors = sync.check_stored(root)

            self.assertTrue(any("non-blocked domain physics" in error for error in errors))
            self.assertTrue(any("already valid registered refs" in error for error in errors))

    def test_dry_run_does_not_mutate_registry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._minimal_root(root, ["physics"])
            write_json(root, "validation/heldout/physics_pack.json", valid_pack("physics"))

            payload = sync.build_payload(root, write=False)
            registry = json.loads((root / grand_factory.REGISTRY_REL).read_text(encoding="utf-8"))

            self.assertEqual(payload["verdict"], "REGISTRY_SYNC_VALID_PACKS_AVAILABLE")
            self.assertEqual(registry["evidence_pack_refs"], [])
            self.assertFalse((root / sync.REPORT_JSON_REL).exists())

    def test_sync_registers_current_successor_not_superseded_stale_pack(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._minimal_root(root, ["physics"])

            stale_ref = "validation/heldout/stale_physics_pack.json"
            stale = valid_pack("physics")
            stale["evidence_pack_id"] = "PACK-PHYSICS-STALE"
            stale["evidence_family"] = "physics-heldout-route"
            stale["pack_version"] = "1.0"
            stale["n"] = 3
            stale["grand_toe_support_allowed"] = False
            write_json(root, stale_ref, stale)

            successor_ref = "validation/heldout/current_physics_pack.json"
            successor = valid_pack("physics")
            successor["evidence_pack_id"] = "PACK-PHYSICS-CURRENT"
            successor["evidence_family"] = "physics-heldout-route"
            successor["pack_version"] = "2.0"
            successor["supersedes"] = ["PACK-PHYSICS-STALE", stale_ref]
            write_json(root, successor_ref, successor)

            payload = sync.build_payload(root, write=True)
            registry = json.loads((root / grand_factory.REGISTRY_REL).read_text(encoding="utf-8"))

            self.assertEqual(payload["new_valid_refs"], [successor_ref])
            self.assertEqual(registry["evidence_pack_refs"], [successor_ref])
            self.assertEqual(payload["candidate_total"], 2)
            self.assertEqual(payload["current_candidate_total"], 1)
            self.assertEqual(payload["superseded_candidate_total"], 1)
            self.assertEqual(payload["current_invalid_candidate_total"], 0)
            self.assertEqual(payload["blocked_domain_total_after_sync"], 0)

    def test_sync_blocks_invalid_successor_and_keeps_stale_invalid_pack_active(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._minimal_root(root, ["physics"])

            old_ref = "validation/heldout/old_invalid_physics_pack.json"
            old = valid_pack("physics")
            old["evidence_pack_id"] = "PACK-PHYSICS-OLD"
            old["evidence_family"] = "physics-heldout-route"
            old["pack_version"] = "1.0"
            old["n"] = 3
            old["grand_toe_support_allowed"] = False
            write_json(root, old_ref, old)

            successor = valid_pack("physics")
            successor["evidence_pack_id"] = "PACK-PHYSICS-CURRENT"
            successor["evidence_family"] = "physics-heldout-route"
            successor["pack_version"] = "2.0"
            successor["supersedes"] = ["PACK-PHYSICS-OLD", old_ref]
            successor["n"] = 19
            write_json(root, "validation/heldout/current_physics_pack.json", successor)

            payload = sync.build_payload(root, write=True)
            registry = json.loads((root / grand_factory.REGISTRY_REL).read_text(encoding="utf-8"))

            self.assertEqual(payload["verdict"], "REGISTRY_SYNC_BLOCKED_PENDING_VALID_PACKS")
            self.assertEqual(payload["new_valid_refs"], [])
            self.assertEqual(registry["evidence_pack_refs"], [])
            self.assertEqual(payload["valid_candidate_total"], 0)
            self.assertEqual(payload["current_invalid_candidate_total"], 2)
            self.assertEqual(payload["superseded_candidate_total"], 0)
            self.assertEqual(payload["blocked_domain_total_after_sync"], 1)

    def test_sync_keeps_unrelated_invalid_candidate_as_repair_work_order(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._minimal_root(root, ["physics"])

            current_ref = "validation/heldout/current_pubchem_physics_pack.json"
            current = valid_pack("physics")
            current["evidence_pack_id"] = "PACK-PHYSICS-PUBCHEM-CURRENT"
            current["source_separation"]["training_sources"] = [
                "validation/heldout/grand_science/physics/pubchem_batch/acquisition.json::visible-fields"
            ]
            current["source_separation"]["target_sources"] = [
                "validation/heldout/grand_science/physics/pubchem_batch/acquisition.json::target-field"
            ]
            write_json(root, current_ref, current)

            unrelated_ref = "validation/heldout/unrelated_nist_physics_pack.json"
            unrelated = valid_pack("physics")
            unrelated["evidence_pack_id"] = "PACK-PHYSICS-NIST-INDEPENDENT"
            unrelated["source_separation"]["training_sources"] = [
                "validation/_raw/physics_nist_constants.txt::visible-fields"
            ]
            unrelated["source_separation"]["target_sources"] = [
                "validation/_raw/physics_nist_constants.txt::target-field"
            ]
            unrelated["n"] = 3
            unrelated["grand_toe_support_allowed"] = False
            write_json(root, unrelated_ref, unrelated)

            payload = sync.build_payload(root, write=True)
            registry = json.loads((root / grand_factory.REGISTRY_REL).read_text(encoding="utf-8"))
            work_orders = json.loads((root / sync.WORK_ORDERS_REL).read_text(encoding="utf-8"))
            work_order_refs = {
                candidate_ref
                for row in work_orders["rows"]
                for candidate_ref in row.get("candidate_refs", [])
            }

            self.assertEqual(payload["new_valid_refs"], [current_ref])
            self.assertEqual(registry["evidence_pack_refs"], [current_ref])
            self.assertEqual(payload["current_invalid_candidate_total"], 1)
            self.assertEqual(payload["blocked_domain_total_after_sync"], 1)
            self.assertIn(unrelated_ref, work_order_refs)


if __name__ == "__main__":
    unittest.main()
