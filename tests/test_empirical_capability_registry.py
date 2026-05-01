from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools import oc133_empirical_capability_registry as registry


def write_json(root: Path, rel_path: str, payload: dict[str, object]) -> None:
    path = root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_text(root: Path, rel_path: str, text: str) -> None:
    path = root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text + "\n", encoding="utf-8")


class EmpiricalCapabilityRegistryTests(unittest.TestCase):
    def _seed_component_suite(self, root: Path) -> None:
        write_text(
            root,
            "tools/oc133_alpha_empirical_factory.py",
            "\n".join(
                [
                    "from __future__ import annotations",
                    "REPORT_REL = \"validation/heldout/alpha/ALPHA_FACTORY_REPORT.json\"",
                    "CAPABILITY_OWNER = \"Research/EmpiricalScience\"",
                ]
            ),
        )
        write_json(
            root,
            "validation/heldout/alpha/ALPHA_FACTORY_REPORT.json",
            {"verdict": "BLOCKED", "open_blocker_total": 7, "candidate_pack_total": 9, "valid_pack_total": 0},
        )

        write_text(
            root,
            "validation/heldout/harvesters/test_harvester.py",
            "\n".join(
                [
                    "from __future__ import annotations",
                    "CAPABILITY_OWNER = \"Research/EmpiricalScience\"",
                ]
            ),
        )

        write_text(
            root,
            "validation/heldout/domain_evidence/test_evidence_executor.py",
            "\n".join(
                [
                    "from __future__ import annotations",
                    "CAPABILITY_OWNER = \"Research/EmpiricalScience\"",
                ]
            ),
        )

        write_text(
            root,
            "tools/oc133_test_acquisition_planner.py",
            "\n".join(
                [
                    "from __future__ import annotations",
                    "CAPABILITY_OWNER = \"Logion IT/Research\"",
                ]
            ),
        )

        write_json(
            root,
            registry.HARVESTER_RUN_REPORT_REL,
            {
                "results": [
                    {
                        "harvester_ref": "validation/heldout/harvesters/test_harvester.py",
                        "parsed_payload": {
                            "verdict": "BLOCKED",
                            "open_blocker_total": 4,
                            "candidate_pack_total": 3,
                            "valid_pack_total": 0,
                        },
                    }
                ]
            },
        )
        write_json(
            root,
            registry.EXECUTOR_RUN_REPORT_REL,
            {
                "results": [
                    {
                        "executor_ref": "validation/heldout/domain_evidence/test_evidence_executor.py",
                        "effective_payload": {
                            "verdict": "BLOCKED",
                            "open_blocker_total": 2,
                            "candidate_pack_total": 3,
                            "valid_pack_total": 0,
                        },
                    }
                ]
            },
        )
        write_json(
            root,
            registry.PLANNER_RUN_REPORT_REL,
            {
                "results": [
                    {
                        "planner_ref": "tools/oc133_test_acquisition_planner.py",
                        "parsed_payload": {
                            "verdict": "BLOCKED",
                            "open_blocker_total": 1,
                            "candidate_pack_total": 1,
                            "valid_pack_total": 0,
                        },
                    }
                ]
            },
        )

    def test_registry_discovers_empirical_components_and_orders_by_unblock_value(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._seed_component_suite(root)
            payload = registry.build_payload(root, write=False)
            self.assertEqual(payload["component_type_totals"]["factory"], 1)
            self.assertEqual(payload["component_type_totals"]["harvester"], 1)
            self.assertEqual(payload["component_type_totals"]["executor"], 1)
            self.assertEqual(payload["component_type_totals"]["planner"], 1)
            self.assertEqual(payload["component_total"], 4)
            self.assertEqual(payload["blocked_component_total"], 4)
            self.assertEqual(payload["next_action_queue"][0]["component_ref"], "tools/oc133_alpha_empirical_factory.py")
            self.assertEqual(payload["next_action_queue"][1]["component_ref"], "validation/heldout/harvesters/test_harvester.py")
            self.assertEqual(payload["next_action_queue"][2]["component_ref"], "validation/heldout/domain_evidence/test_evidence_executor.py")
            self.assertEqual(payload["next_action_queue"][3]["component_ref"], "tools/oc133_test_acquisition_planner.py")
            for row in payload["components"]:
                self.assertTrue(row["no_send"])
                self.assertFalse(row["publish_allowed"])
                self.assertFalse(row["journal_submissions_allowed"])
                self.assertFalse(row["external_network_allowed"])
                self.assertFalse(row["automatic_dispatch_allowed"])
                self.assertTrue(row["compute_degradation_notes"])
            self.assertTrue(payload["no_send_locks"]["no_send"])
            self.assertFalse(payload["no_send_locks"]["external_network_allowed"])
            self.assertFalse(payload["automatic_dispatch_allowed"])
            self.assertTrue(payload["compute_degradation_notes"])

    def test_next_action_queue_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._seed_component_suite(root)
            first = registry.build_payload(root, write=False)
            second = registry.build_payload(root, write=False)
            self.assertEqual(first["next_action_queue"], second["next_action_queue"])

    def test_registry_writes_json_and_markdown_reports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._seed_component_suite(root)
            payload = registry.build_payload(root, write=True)
            json_path = root / registry.REPORT_JSON_REL
            md_path = root / registry.REPORT_MD_REL
            self.assertTrue(json_path.exists())
            self.assertTrue(md_path.exists())
            written = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(written["next_action_total"], payload["next_action_total"])
            self.assertEqual(written["component_total"], payload["component_total"])
            report_md = md_path.read_text(encoding="utf-8")
            self.assertIn("# OC Core 1.3.3 Empirical Capability Registry", report_md)
            self.assertIn("## Cockpit Locks", report_md)
            self.assertIn("## Compute-Degradation Notes", report_md)

    def test_registry_treats_sync_repair_work_orders_as_blockers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_text(
                root,
                "tools/oc133_grand_evidence_registry_sync_factory.py",
                "\n".join(
                    [
                        "from __future__ import annotations",
                        "REPORT_JSON_REL = \"reports/OC_CORE_1_3_3_GRAND_EVIDENCE_REGISTRY_SYNC.json\"",
                        "CAPABILITY_OWNER = \"Research/EmpiricalScience\"",
                    ]
                ),
            )
            write_json(
                root,
                "reports/OC_CORE_1_3_3_GRAND_EVIDENCE_REGISTRY_SYNC.json",
                {
                    "schema_id": "OC133_GRAND_EVIDENCE_REGISTRY_SYNC_v1",
                    "verdict": "REGISTRY_SYNC_BLOCKED_PENDING_VALID_PACKS",
                    "candidate_total": 10,
                    "valid_candidate_total": 0,
                    "invalid_candidate_total": 10,
                    "blocked_domain_total_after_sync": 5,
                    "open_repair_work_order_total": 15,
                },
            )

            payload = registry.build_payload(root, write=False)
            row = payload["components"][0]

            self.assertTrue(row["is_blocked"])
            self.assertEqual(row["open_blocker_total"], 15)
            self.assertEqual(row["blocked_domain_total"], 5)
            self.assertEqual(row["blocked_candidate_pack_total"], 10)
            self.assertEqual(payload["next_action_queue"][0]["component_ref"], "tools/oc133_grand_evidence_registry_sync_factory.py")

    def test_registry_discovers_official_readonly_acquisition_runner(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_text(
                root,
                "tools/oc133_official_readonly_acquisition_runner.py",
                "\n".join(
                    [
                        "from __future__ import annotations",
                        "CAPABILITY_OWNER = \"Research/EmpiricalScience\"",
                        "REPORT_JSON_REL = \"reports/OC_CORE_1_3_3_OFFICIAL_READONLY_ACQUISITION_RUN.json\"",
                    ]
                ),
            )
            write_json(
                root,
                "reports/OC_CORE_1_3_3_OFFICIAL_READONLY_ACQUISITION_RUN.json",
                {
                    "schema_id": "OC133_OFFICIAL_READONLY_ACQUISITION_RUN_v1",
                    "verdict": "ACQUISITION_DRY_RUN_READY",
                    "open_blocker_total": 3,
                    "candidate_pack_total": 3,
                    "valid_pack_total": 0,
                },
            )

            payload = registry.build_payload(root, write=False)

            self.assertEqual(payload["component_type_totals"]["planner"], 1)
            self.assertEqual(payload["components"][0]["component_ref"], "tools/oc133_official_readonly_acquisition_runner.py")
            self.assertEqual(
                payload["components"][0]["command"],
                "python tools/oc133_official_readonly_acquisition_runner.py --write --allow-blocked-exit-zero",
            )


if __name__ == "__main__":
    raise SystemExit(unittest.main())
