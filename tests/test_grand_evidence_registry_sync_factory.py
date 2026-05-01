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


if __name__ == "__main__":
    unittest.main()
