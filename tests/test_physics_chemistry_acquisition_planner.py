from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools import oc133_physics_chemistry_acquisition_planner as planner

REPO_ROOT = Path(__file__).resolve().parents[1]


def write_json(root: Path, rel: str, payload: dict) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(root: Path, rel: str, value: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8", newline="\n")


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk.replace(b"\r\n", b"\n"))
    return h.hexdigest()


def bounded_rows(domain: str, snapshot_ref: str, snapshot_sha: str, count: int) -> list[dict]:
    return [
        {
            "claim_id": f"OC133-TB-{domain.upper()}-{idx:03d}",
            "lane": domain,
            "dataset_snapshot_ref": snapshot_ref,
            "target_blind_split": "withheld target values",
            "formula": "reconstruction_formula",
            "predicted_value": float(idx + 1),
            "observed_value": float(idx + 1),
            "uncertainty": 0.1,
            "comparator_baseline": f"{domain} reconstruction control",
            "comparator_prediction": float(idx + 2),
            "residual": 0.0,
            "comparator_residual": 1.0,
            "negative_control": "replace target with control and require larger residual",
            "falsifier": "residual exceeds uncertainty or control is not worse",
            "support_scope": "target-blind reconstruction of a held-out baseline",
            "snapshot_sha256": snapshot_sha,
            "prediction_support_allowed": True,
            "empirical_support_allowed": True,
            "negative_control_rejected": True,
        }
        for idx in range(count)
    ]


class PhysicsChemistryAcquisitionPlannerTests(unittest.TestCase):
    def test_current_repo_plan_is_blocked_and_does_not_emit_support_true(self) -> None:
        payload = planner.build_plan_payload(REPO_ROOT, check_official_sources=False)

        self.assertTrue(payload["open_blocker_total"] > 0)
        self.assertFalse(payload["grand_toe_support_allowed"])
        self.assertEqual(payload["protocol"]["verdict"], "BLOCKED")

        protocol_rows = {row["domain"]: row for row in payload["protocol"]["rows"]}
        for row in payload["domains"]:
            self.assertIn(row["domain"], planner.DOMAINS)
            self.assertFalse(row["grand_toe_support_allowed"])
            self.assertEqual(row["status"], "BLOCKED_PENDING_GENUINE_ACQUISITION")
            self.assertEqual(row["required_n"], 20)
            self.assertEqual(row["minimum_n"], 20)
            self.assertTrue(row["missing_n"] >= 20)
            self.assertFalse(row["check_official_sources"])

            blocker_text = " ".join(row["blockers"])
            self.assertIn("CURRENT_TARGET_BLIND_RECONSTRUCTION_BOUNDARY", blocker_text)
            self.assertIn("NO_NEGATIVE_CONTROLS", blocker_text)
            self.assertIn("NO_FALSIFIERS", blocker_text)
            self.assertIn("NUMERIC_REPLAY_QUARANTINED_NOT_DOMAIN_EVIDENCE", blocker_text)

            protocol = protocol_rows[row["domain"]]
            self.assertFalse(protocol["grand_toe_support_allowed"])
            self.assertEqual(protocol["status"], row["status"])
            self.assertEqual(protocol["current_n"], row["genuine_target_row_total"])
            self.assertEqual(protocol["missing_n"], row["missing_n"])
            self.assertEqual(protocol["required_n"], row["required_n"])
            self.assertIn("required_protocol_steps", protocol)
            self.assertIn("required_pack_fields", protocol)

        blocker_text = " ".join(payload["open_blocker_ids"])
        self.assertIn("SOURCE_ENDPOINT_CHECK_SKIPPED", blocker_text)
        self.assertIn("NUMERIC_REPLAY_QUARANTINED_NOT_DOMAIN_EVIDENCE", blocker_text)
        self.assertLess(sum(row["genuine_target_row_total"] for row in payload["domains"]), 40)

    def test_protocol_is_checkable_and_deterministic(self) -> None:
        first = planner.build_plan_payload(REPO_ROOT, check_official_sources=False)
        second = planner.build_plan_payload(REPO_ROOT, check_official_sources=False)
        self.assertEqual(first["plan_hash"], second["plan_hash"])
        self.assertEqual(first["protocol"]["protocol_hash"], second["protocol"]["protocol_hash"])
        self.assertEqual(first["protocol"]["verdict"], "BLOCKED")

    def test_build_and_check_in_temp_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(
                root,
                planner.REQUIREMENTS_REL,
                {
                    "schema_id": "OC133_GRAND_EMPIRICAL_DOMAIN_REQUIREMENTS_v1",
                    "release_id": "oc_core_1_3_3",
                    "capability_owner": "Research/EmpiricalScience",
                    "minimum_per_domain_n": 20,
                    "required_source_separation_modes": ["prospective", "target_blind"],
                    "criteria": {
                        "pre_target_lock_required": True,
                        "target_hidden_until_scoring_required": True,
                        "negative_control_rejection_required": True,
                        "falsifier_required": True,
                        "uncertainty_interval_required": True,
                        "current_target_blind_reconstructions_are_bounded_baseline_only": True,
                    },
                },
            )
            write_json(
                root,
                planner.EVIDENCE_SCHEMA_REL,
                {
                    "required": [
                        "schema_id",
                        "release_id",
                        "capability_owner",
                        "evidence_pack_id",
                        "domain",
                        "source_separation",
                        "n",
                        "model_under_test",
                        "comparator_baseline",
                        "uncertainty",
                        "residuals",
                        "negative_controls",
                        "falsifiers",
                        "grand_toe_support_allowed",
                    ]
                },
            )
            write_json(root, "validation/grand_science/grand_empirical_protocol.schema.json", {})

            physics_snapshot = "validation/_raw/physics_nist_constants.txt"
            chemistry_snapshot = "validation/_raw/chemistry_pubchem_water.txt"
            chemistry_webbook_snapshot = "validation/_raw/chemistry_nist_webbook_water.txt"
            write_text(root, physics_snapshot, "c    299792458.0\n")
            write_text(root, chemistry_snapshot, "MolecularWeight=18.015\n")
            write_text(root, chemistry_webbook_snapshot, "Webbook water molecular_weight=18.0153\n")

            physics_sha = file_sha256(root / physics_snapshot)
            chem_pubchem_sha = file_sha256(root / chemistry_snapshot)
            chem_webbook_sha = file_sha256(root / chemistry_webbook_snapshot)
            write_json(
                root,
                planner.MANIFEST_REL,
                {
                    "rows": [
                        {
                            "source_id": "physics_nist_constants",
                            "url": "https://physics.nist.gov/cuu/Constants/Table/allascii.txt",
                            "status": "FETCHED",
                            "bytes": 17,
                            "sha256": physics_sha,
                            "source_sha256": physics_sha,
                            "local_snapshot": physics_snapshot,
                        },
                        {
                            "source_id": "chemistry_pubchem_water",
                            "url": "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/962/property/MolecularFormula,MolecularWeight,CanonicalSMILES,InChIKey/JSON",
                            "status": "FETCHED",
                            "bytes": 17,
                            "sha256": chem_pubchem_sha,
                            "source_sha256": chem_pubchem_sha,
                            "local_snapshot": chemistry_snapshot,
                        },
                        {
                            "source_id": "chemistry_nist_webbook_water",
                            "url": "https://webbook.nist.gov/cgi/cbook.cgi?ID=C7732185&Units=SI",
                            "status": "FETCHED",
                            "bytes": 17,
                            "sha256": chem_webbook_sha,
                            "source_sha256": chem_webbook_sha,
                            "local_snapshot": chemistry_webbook_snapshot,
                        },
                    ]
                },
            )

            write_json(
                root,
                planner.TARGET_BLIND_REL,
                {
                    "rows": bounded_rows("physics", physics_snapshot, physics_sha, 20)
                    + bounded_rows("chemistry", chemistry_snapshot, chem_pubchem_sha, 20),
                },
            )
            write_json(
                root,
                planner.NUMERIC_REPLAY_REL,
                {
                    "rows": [
                        {
                            "lane": "physics",
                            "claim_id": "OC133-NUM-PHY-001",
                            "numeric_replay": True,
                            "replay_value": 1.0,
                            "prediction_support_allowed": False,
                            "empirical_support_allowed": False,
                            "quarantine_reason": "QA only",
                        },
                        {
                            "lane": "chemistry",
                            "claim_id": "OC133-NUM-CHEM-001",
                            "numeric_replay": True,
                            "replay_value": 1.0,
                            "prediction_support_allowed": False,
                            "empirical_support_allowed": False,
                            "quarantine_reason": "QA only",
                        },
                    ]
                },
            )

            payload = planner.write_outputs(root, check_official_sources=False)
            self.assertFalse(payload["grand_toe_support_allowed"])
            self.assertEqual(payload["protocol"]["verdict"], "BLOCKED")
            self.assertTrue((root / planner.PLAN_JSON_REL).exists())
            self.assertTrue((root / planner.PROTOCOL_JSON_REL).exists())
            self.assertTrue((root / planner.PLAN_MD_REL).exists())
            self.assertEqual(planner.check_stored(root), [])

            for row in payload["domains"]:
                self.assertFalse(row["grand_toe_support_allowed"])
                self.assertEqual(row["genuine_target_row_total"], 0)
                self.assertEqual(row["required_n"], 20)
                self.assertGreater(len(row["bounded_rows"]), 0)
                self.assertLess(len(row["genuine_rows"]), row["required_n"])
                self.assertIn("CURRENT_TARGET_BLIND_RECONSTRUCTION_BOUNDARY", " ".join(row["blockers"]))

            payload_two = planner.build_plan_payload(root, check_official_sources=False)
            self.assertEqual(payload["plan_hash"], payload_two["plan_hash"])
            self.assertEqual(payload["protocol"]["protocol_hash"], payload_two["protocol"]["protocol_hash"])


if __name__ == "__main__":
    raise SystemExit(unittest.main())
