from __future__ import annotations

import json
import unittest
import zipfile

from release_machine import core
from release_machine import complete


class ReleaseMachineTests(unittest.TestCase):
    def test_fake_pass_prevention(self) -> None:
        with self.assertRaises(ValueError):
            core.gate_result("gate_x", "fake", "PASS", executed=False)

    def test_blocked_credentials_are_blocked(self) -> None:
        result = core.credential_gate_result("ZENODO_TOKEN", "")
        self.assertEqual(result["state"], "BLOCKED")
        self.assertEqual(result["severity"], "HIGH")

    def test_owner_approval_resets_when_hash_changes(self) -> None:
        self.assertFalse(core.owner_approval_valid({"approved": True, "artifact_freeze_hash": "old"}, "new"))

    def test_critical_high_waivers_are_rejected(self) -> None:
        self.assertFalse(core.waiver_allowed("CRITICAL"))
        self.assertFalse(core.waiver_allowed("HIGH"))
        self.assertTrue(core.waiver_allowed("MEDIUM"))

    def test_publish_impossible_without_owner_approval(self) -> None:
        summary = core.evaluate_release("oc_core_1_3_2", "all", "dry-run", write=True)
        self.assertEqual(summary["release_state"], "RELEASE_READY_NO_SEND")
        self.assertFalse(summary["publish_allowed"])
        self.assertTrue(summary["owner_approval_required"])

    def test_completed_gate_set_has_24_hard_gates(self) -> None:
        summary = core.evaluate_release("oc_core_1_3_2", "all", "pre_publish", write=True)
        self.assertEqual(summary["master_verdict"], "PASS")
        self.assertEqual(summary["gate_counts"]["PASS"], 24)
        self.assertEqual(summary["finding_total"], 0)

    def test_missing_swhid_is_owner_action_not_invented_identifier(self) -> None:
        root = complete.repo_root()
        payload = json.loads((root / "releases/oc_core_1_3_2/editorial/OC_CORE_1_3_2_PUBLISH_MANIFEST_DRAFT.json").read_text(encoding="utf-8"))
        swh = payload["software_heritage"]
        self.assertEqual(swh["policy"], "EXISTING_ONLY")
        if swh["swhid"] is None:
            self.assertEqual(swh["status"], "owner_action_required")
            self.assertTrue(swh["owner_exception_required_for_publish"])

    def test_zip_manifest_and_checksums_are_consistent(self) -> None:
        root = complete.repo_root()
        manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
        checksums = (root / "checksums.txt").read_text(encoding="utf-8")
        zip_path = root / "releases/oc_core_1_3_2/artifacts/oc_core_1_3_2_zenodo_release.zip"
        with zipfile.ZipFile(zip_path) as zf:
            names = set(zf.namelist())
        self.assertIn("manifest.json", names)
        self.assertIn("checksums.txt", names)
        for row in manifest["files"][:25]:
            self.assertIn(row["path"], names)
            self.assertIn(row["sha256"], checksums)

    def test_research_packets_are_bounded_no_send_material(self) -> None:
        root = complete.repo_root()
        audit = json.loads((root / "releases/oc_core_1_3_2/editorial/research_packets/PUBLIC_RESEARCH_PACKET_AUDIT_v1.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(audit["packet_total"], 1)
        self.assertEqual(audit["packet_total"], audit["pass_total"])
        self.assertFalse(audit["canonical_claim_ledger_change"])

    def test_v132_tag_absent_and_publish_locked(self) -> None:
        root = complete.repo_root()
        self.assertFalse((root / ".git/refs/tags/v1.3.2").exists())
        manifest = json.loads((root / "releases/oc_core_1_3_2/editorial/OC_CORE_1_3_2_PUBLISH_MANIFEST_DRAFT.json").read_text(encoding="utf-8"))
        self.assertFalse(manifest["publish_allowed"])
        self.assertTrue(manifest["global_no_send_lock"])


if __name__ == "__main__":
    unittest.main()
