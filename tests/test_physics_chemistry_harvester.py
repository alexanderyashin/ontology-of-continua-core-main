from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from validation.heldout.harvesters import physics_chemistry_harvester as harvester


REPO_ROOT = Path(__file__).resolve().parents[1]


def copy_fixture(root: Path, rel_path: str) -> None:
    source = REPO_ROOT / rel_path
    target = root / rel_path
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def copy_required(root: Path) -> None:
    copy_fixture(root, harvester.TARGET_BLIND_REL)
    copy_fixture(root, harvester.REQUIREMENTS_REL)


class PhysicsChemistryHarvesterTests(unittest.TestCase):
    def test_current_target_blind_rows_emit_only_blocker_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            copy_required(root)

            report = harvester.build_report(root)
            self.assertEqual(harvester.build_payload(root), report)

            self.assertEqual(report["candidate_pack_total"], 0)
            self.assertEqual(report["valid_pack_total"], 0)
            self.assertFalse(report["grand_toe_support_allowed"])
            self.assertEqual(report["minimum_per_domain_n"], 20)
            self.assertEqual(report["grand_eligible_row_total"], 0)
            self.assertEqual(report["current_target_blind_row_total"], 2)
            self.assertIn("N<20", " ".join(report["explanation"]))
            self.assertIn("bounded baseline reconstructions, not grand evidence", " ".join(report["explanation"]))
            self.assertTrue(report["no_send"])
            self.assertFalse(report["publish_allowed"])

            by_domain = {row["domain"]: row for row in report["domains"]}
            self.assertEqual(set(by_domain), {"physics", "chemistry"})
            for row in by_domain.values():
                self.assertEqual(row["candidate_pack_total"], 0)
                self.assertEqual(row["valid_pack_total"], 0)
                self.assertFalse(row["grand_toe_support_allowed"])
                self.assertIn("GENUINE_EVIDENCE_N_BELOW_MINIMUM::0/20", row["blockers"])
                self.assertIn(
                    "CURRENT_TARGET_BLIND_ROWS_ARE_BOUNDED_BASELINE_NOT_GRAND_EVIDENCE",
                    row["blockers"],
                )
                self.assertEqual(row["bounded_baseline_row_total"], 1)
                self.assertEqual(row["baseline_rows"][0]["grand_n_credit"], 0)

    def test_write_outputs_materializes_harvested_blocker_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            copy_required(root)

            report = harvester.write_outputs(root)

            report_path = root / harvester.REPORT_REL
            self.assertTrue(report_path.is_file())
            stored = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(stored, report)
            self.assertEqual(stored["output_ref"], harvester.REPORT_REL)
            self.assertEqual(stored["valid_candidate_pack_total"], 0)

    def test_report_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            copy_required(root)

            first = harvester.build_report(root)
            second = harvester.build_report(root)

            self.assertEqual(first, second)
            self.assertEqual(first["report_sha256"], second["report_sha256"])


if __name__ == "__main__":
    unittest.main()
