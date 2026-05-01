from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from tools import oc133_physics_chemistry_official_batch_factory as factory
from validation.grand_science import evidence_pack_factory as grand_factory


REPO_ROOT = Path(__file__).resolve().parents[1]


def copy_fixture(root: Path, rel_path: str) -> None:
    source = REPO_ROOT / rel_path
    target = root / rel_path
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def copy_required_inputs(root: Path) -> None:
    for rel_path in (
        factory.REQUIREMENTS_REL,
        factory.MANIFEST_REL,
        factory.PHYSICS_NIST_CONSTANTS_REF,
        factory.CHEMISTRY_PUBCHEM_WATER_REF,
        factory.CHEMISTRY_NIST_WEBBOOK_WATER_REF,
    ):
        copy_fixture(root, rel_path)


def target_blind_source(rows: list[dict]) -> dict:
    return {
        "mode": "target_blind",
        "pre_target_lock": True,
        "target_hidden_until_scoring": True,
        "declared_before_scoring": True,
        "training_sources": [str(row["training_source"]) for row in rows],
        "target_sources": [str(row["target_source"]) for row in rows],
    }


class PhysicsChemistryOfficialBatchFactoryTests(unittest.TestCase):
    def test_current_repo_builds_blocked_acquisition_ready_packet(self) -> None:
        payload = factory.build_payload(REPO_ROOT)
        report = payload["report"]
        tasks = payload["tasks"]

        self.assertEqual(report["verdict"], "BLOCKED_ACQUISITION_READY_NO_SEND")
        self.assertFalse(report["grand_toe_support_allowed"])
        self.assertTrue(report["no_send"])
        self.assertFalse(report["publish_allowed"])
        self.assertFalse(report["registry_integration_allowed"])

        by_domain = {row["domain"]: row for row in report["domains"]}
        self.assertEqual(set(by_domain), {"physics", "chemistry"})
        self.assertGreaterEqual(by_domain["physics"]["candidate_n"], 20)
        self.assertEqual(by_domain["physics"]["grand_eligible_n"], 0)
        self.assertEqual(by_domain["physics"]["missing_n"], 0)
        self.assertEqual(by_domain["chemistry"]["candidate_n"], 12)
        self.assertEqual(by_domain["chemistry"]["missing_n"], 8)
        self.assertEqual(by_domain["chemistry"]["grand_eligible_n"], 0)

        blocker_text = " ".join(report["blockers"])
        self.assertIn("SOURCE_SEPARATION_MODE_NOT_ALLOWED::official_snapshot_replay", blocker_text)
        self.assertIn("PRE_TARGET_LOCK_REQUIRED", blocker_text)
        self.assertIn("TARGET_HIDDEN_UNTIL_SCORING_REQUIRED", blocker_text)
        self.assertIn("N_BELOW_MINIMUM::chemistry::12/20", blocker_text)

        self.assertTrue(all(row["sha256_match"] for row in report["snapshot_records"]))
        physics_rows = tasks["domains"][0]["rows"]
        chemistry_rows = tasks["domains"][1]["rows"]
        self.assertTrue(all(row["row_hash"] for row in physics_rows[:5]))
        self.assertTrue(all(row["negative_control_rejected"] for row in physics_rows))
        self.assertTrue(all(row["negative_control_rejected"] for row in chemistry_rows))

        missing_ids = {
            item["source_id"]
            for row in report["domains"]
            for item in row["missing_official_snapshots"]
        }
        self.assertIn("physics_nist_constants_pre_target_lock_manifest_v1", missing_ids)
        self.assertIn("physics_nist_asd_hydrogen_balmer_lines_v1", missing_ids)
        self.assertIn("chemistry_pubchem_20_compound_properties_v1", missing_ids)
        self.assertIn("chemistry_nist_webbook_water_gas_thermo_v1", missing_ids)

    def test_candidate_packs_remain_invalid_under_grand_gate(self) -> None:
        payload = factory.build_payload(REPO_ROOT)
        requirements, _ = factory.load_requirements(REPO_ROOT)

        physics_pack = payload[factory.PHYSICS_PACK_REL]
        chemistry_pack = payload[factory.CHEMISTRY_PACK_REL]

        self.assertFalse(physics_pack["grand_toe_support_allowed"])
        self.assertFalse(chemistry_pack["grand_toe_support_allowed"])
        physics_failures = grand_factory.pack_failure_reasons(physics_pack, requirements)
        chemistry_failures = grand_factory.pack_failure_reasons(chemistry_pack, requirements)

        self.assertIn("SOURCE_SEPARATION_MODE_NOT_ALLOWED", physics_failures)
        self.assertIn("PRE_TARGET_LOCK_REQUIRED", physics_failures)
        self.assertIn("TARGET_HIDDEN_UNTIL_SCORING_REQUIRED", physics_failures)
        self.assertIn("GRAND_TOE_SUPPORT_NOT_ALLOWED", physics_failures)
        self.assertIn("N_BELOW_MINIMUM::20", chemistry_failures)
        self.assertIn("GRAND_TOE_SUPPORT_NOT_ALLOWED", chemistry_failures)

    def test_even_valid_physics_source_override_does_not_create_global_pass_without_chemistry_n20(self) -> None:
        base_payload = factory.build_payload(REPO_ROOT)
        physics_rows = base_payload["tasks"]["domains"][0]["rows"]
        chemistry_rows = base_payload["tasks"]["domains"][1]["rows"]
        payload = factory.build_payload(
            REPO_ROOT,
            source_separation_overrides={
                "physics": target_blind_source(physics_rows),
                "chemistry": target_blind_source(chemistry_rows),
            },
        )
        by_domain = {row["domain"]: row for row in payload["report"]["domains"]}

        self.assertTrue(by_domain["physics"]["grand_toe_support_allowed"])
        self.assertTrue(payload[factory.PHYSICS_PACK_REL]["grand_toe_support_allowed"])
        self.assertFalse(by_domain["chemistry"]["grand_toe_support_allowed"])
        self.assertFalse(payload["report"]["grand_toe_support_allowed"])
        self.assertIn("N_BELOW_MINIMUM::chemistry::12/20", by_domain["chemistry"]["blockers"])

    def test_write_outputs_materializes_only_official_batch_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            copy_required_inputs(root)

            report = factory.write_outputs(root)

            self.assertFalse(report["grand_toe_support_allowed"])
            for rel_path in (
                factory.PHYSICS_PACK_REL,
                factory.CHEMISTRY_PACK_REL,
                factory.TASKS_REL,
                factory.PROTOCOL_REL,
                factory.REPORT_REL,
                factory.README_REL,
            ):
                self.assertTrue((root / rel_path).is_file(), rel_path)
                self.assertTrue(rel_path.startswith(factory.OUTPUT_ROOT_REL) or rel_path.startswith("validation/heldout/grand_science/physics_chemistry/official_batch"))
            self.assertEqual(factory.check_stored(root), [])


if __name__ == "__main__":
    unittest.main()
