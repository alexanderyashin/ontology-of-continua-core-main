from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tests.test_empirical_capability_registry import write_json, write_text
from tools import oc133_grand_evidence_repair_router as router
from tools import oc133_grand_evidence_registry_sync_factory as sync


class GrandEvidenceRepairRouterTests(unittest.TestCase):
    def test_routes_work_orders_to_available_capabilities(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_text(
                root,
                "tools/oc133_biology_ncbi_batch_factory.py",
                "\n".join(
                    [
                        "from __future__ import annotations",
                        "CAPABILITY_OWNER = \"Research/EmpiricalScience\"",
                        "REPORT_REL = \"validation/heldout/grand_science/biology/ncbi_batch/report.json\"",
                    ]
                ),
            )
            write_json(
                root,
                "validation/heldout/grand_science/biology/ncbi_batch/report.json",
                {"verdict": "BLOCKED", "open_blocker_total": 1, "candidate_pack_total": 1, "valid_pack_total": 0},
            )
            write_json(
                root,
                sync.WORK_ORDERS_REL,
                {
                    "schema_id": sync.WORK_ORDER_SCHEMA_ID,
                    "rows": [
                        {
                            "work_order_id": "WO-BIO-N",
                            "domain": "biology",
                            "failure_class": "insufficient_sample_size",
                            "owner_capability": "Research/EmpiricalScience",
                        }
                    ],
                },
            )

            payload = router.build_payload(root, write=True)

            self.assertEqual(payload["verdict"], "REPAIR_ROUTE_READY")
            self.assertEqual(payload["missing_capability_total"], 0)
            self.assertEqual(payload["rows"][0]["preferred_component_ref"], "tools/oc133_biology_ncbi_batch_factory.py")
            self.assertTrue((root / router.REPORT_JSON_REL).exists())

    def test_missing_capability_remains_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(
                root,
                sync.WORK_ORDERS_REL,
                {
                    "schema_id": sync.WORK_ORDER_SCHEMA_ID,
                    "rows": [
                        {
                            "work_order_id": "WO-CHEM-N",
                            "domain": "chemistry",
                            "failure_class": "insufficient_sample_size",
                            "owner_capability": "Research/EmpiricalScience",
                        }
                    ],
                },
            )

            payload = router.build_payload(root, write=False)

            self.assertEqual(payload["verdict"], "REPAIR_ROUTE_BLOCKED_CAPABILITIES_MISSING")
            self.assertEqual(payload["missing_capability_refs"], ["tools/oc133_chemistry_pubchem_formula_batch_factory.py"])

    def test_capability_repair_profile_calls_router(self) -> None:
        source = Path("tools/oc133_capability_repair_executor.py").read_text(encoding="utf-8")
        self.assertIn("tools/oc133_grand_evidence_repair_router.py", source)


if __name__ == "__main__":
    unittest.main()
