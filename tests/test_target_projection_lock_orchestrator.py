from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools import oc133_target_projection_lock_factory as lock_factory
from tools import oc133_target_projection_lock_orchestrator as orchestrator


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8", newline="\n")


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def biology_packet(acquisition_id: str) -> dict[str, object]:
    return {
        "schema_id": "OC133_BIOLOGY_NCBI_BATCH_ACQUISITION_PACKET_v1",
        "release_id": "oc_core_1_3_3",
        "status": "ACQUISITION_REQUIRED",
        "source_acquisition_requests": [
            {
                "acquisition_id": acquisition_id,
                "official_source": "NCBI E-utilities ESearch",
                "expected_local_snapshot_ref": "validation/_raw/ncbi.json",
                "required_fields": [
                    "header.type",
                    "esearchresult.retmax",
                    "esearchresult.retstart",
                    "esearchresult.idlist",
                    "esearchresult.querytranslation",
                ],
                "no_send_lock": True,
            }
        ],
        "target_projection_lock": {"required": True, "valid": False, "failures": ["old"]},
        "no_send": True,
        "publish_allowed": False,
    }


def chemistry_packet(acquisition_id: str) -> dict[str, object]:
    return {
        "schema_id": "OC133_CHEMISTRY_PUBCHEM_FORMULA_BATCH_ACQUISITION_PACKET_v1",
        "release_id": "oc_core_1_3_3",
        "status": "ACQUISITION_REQUIRED",
        "source_acquisition_requests": [
            {
                "request_id": acquisition_id,
                "acquisition_id": acquisition_id,
                "cid": "962",
                "required_fields": ["MolecularFormula", "MolecularWeight"],
                "target_field": "MolecularWeight",
                "visible_training_fields": ["CID", "MolecularFormula"],
                "no_send_lock": True,
            }
        ],
        "no_send": True,
        "publish_allowed": False,
    }


def write_fixture_repo(root: Path) -> tuple[str, str]:
    biology_id = "OC133-NCBI-GEO-OFFICIAL-SNAPSHOT-0001"
    chemistry_id = "OC133-CHEM-PUBCHEM-FORMULA-ACQ-001"
    write_json(root / orchestrator.BIOLOGY_PACKET_REL, biology_packet(biology_id))
    write_json(root / orchestrator.CHEMISTRY_PACKET_REL, chemistry_packet(chemistry_id))
    write_json(
        root / orchestrator.official_snapshot_ref(biology_id),
        {
            "header": {"type": "esearch", "version": "0.3"},
            "esearchresult": {
                "retmax": "2",
                "retstart": "0",
                "idlist": ["111", "222"],
                "querytranslation": "GPL96[Accession]",
            },
        },
    )
    write_json(
        root / orchestrator.official_snapshot_ref(chemistry_id),
        {
            "PropertyTable": {
                "Properties": [
                    {
                        "CID": 962,
                        "MolecularFormula": "H2O",
                        "MolecularWeight": "18.02",
                    }
                ]
            }
        },
    )
    return biology_id, chemistry_id


def strip_target_projection_lock(value: object) -> object:
    if isinstance(value, dict):
        return {key: strip_target_projection_lock(item) for key, item in value.items() if key != "target_projection_lock"}
    if isinstance(value, list):
        return [strip_target_projection_lock(item) for item in value]
    return value


class TargetProjectionLockOrchestratorTests(unittest.TestCase):
    def test_writes_no_send_declarations_and_fail_closed_locks_until_factory_kinds_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _biology_id, chemistry_id = write_fixture_repo(root)

            report = orchestrator.run(root, write=True, attach=True)

            self.assertEqual(report["locks"], lock_factory.NO_SEND_LOCKS)
            self.assertNotIn('"grand_toe_support_allowed": true', json.dumps(report))
            self.assertTrue((root / orchestrator.BIOLOGY_DECLARATION_REL).is_file())
            self.assertTrue(
                (root / f"{orchestrator.CHEMISTRY_DECLARATION_DIR_REL}/{chemistry_id}.json").is_file()
            )
            biology_declaration = read_json(root / orchestrator.BIOLOGY_DECLARATION_REL)
            chemistry_declaration = read_json(root / f"{orchestrator.CHEMISTRY_DECLARATION_DIR_REL}/{chemistry_id}.json")
            self.assertEqual(biology_declaration["model_declaration"]["kind"], "list_length")
            self.assertEqual(chemistry_declaration["model_declaration"]["kind"], "chemical_formula_weight")
            self.assertEqual(biology_declaration["locks"], lock_factory.NO_SEND_LOCKS)
            self.assertEqual(chemistry_declaration["locks"], lock_factory.NO_SEND_LOCKS)

            supports_biology = orchestrator.model_declaration_supported("list_length")
            supports_chemistry = orchestrator.model_declaration_supported("chemical_formula_weight")
            if supports_biology and supports_chemistry:
                self.assertEqual(report["factory_summary"]["open_blocker_total"], 0)
                self.assertTrue(report["biology"]["verified"])
                self.assertEqual(report["chemistry"]["verified_total"], 1)
            else:
                self.assertGreater(report["factory_summary"]["open_blocker_total"], 0)
                blocker_text = " ".join(report["factory_summary"]["blockers"])
                if not supports_biology:
                    self.assertIn("MODEL_DECLARATION_KIND_UNSUPPORTED::list_length", blocker_text)
                    self.assertFalse(report["biology"]["verified"])
                if not supports_chemistry:
                    self.assertIn("MODEL_DECLARATION_KIND_UNSUPPORTED::chemical_formula_weight", blocker_text)
                    self.assertEqual(report["chemistry"]["verified_total"], 0)

    def test_attach_changes_only_target_projection_lock_fields_in_packets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _biology_id, chemistry_id = write_fixture_repo(root)
            biology_before = read_json(root / orchestrator.BIOLOGY_PACKET_REL)
            chemistry_before = read_json(root / orchestrator.CHEMISTRY_PACKET_REL)

            report = orchestrator.run(root, write=True, attach=True)

            biology_after = read_json(root / orchestrator.BIOLOGY_PACKET_REL)
            chemistry_after = read_json(root / orchestrator.CHEMISTRY_PACKET_REL)
            self.assertEqual(strip_target_projection_lock(biology_after), strip_target_projection_lock(biology_before))
            self.assertEqual(strip_target_projection_lock(chemistry_after), strip_target_projection_lock(chemistry_before))

            biology_status = biology_after["target_projection_lock"]
            chemistry_status = chemistry_after["source_acquisition_requests"][0]["target_projection_lock"]
            for status in (biology_status, chemistry_status):
                self.assertEqual(status["locks"], lock_factory.NO_SEND_LOCKS)
                self.assertTrue(status["refs"]["declaration_ref"].startswith(orchestrator.OUTPUT_ROOT_REL))
                self.assertTrue(status["refs"]["target_projection_lock_ref"].startswith(orchestrator.OUTPUT_ROOT_REL))
                self.assertRegex(status["hashes"]["target_projection_lock_sha256"], r"^[0-9a-f]{64}$")
                self.assertFalse(status.get("grand_toe_support_allowed", False))
            self.assertEqual(
                chemistry_status["refs"]["declaration_ref"],
                f"{orchestrator.CHEMISTRY_DECLARATION_DIR_REL}/{chemistry_id}.json",
            )
            self.assertEqual(report["chemistry"]["request_total"], 1)

    def test_check_stored_detects_tampered_lock(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_fixture_repo(root)
            report = orchestrator.run(root, write=True, attach=True)
            write_json(root / orchestrator.ORCHESTRATOR_REPORT_REL, report)
            self.assertEqual(orchestrator.check_stored(root), [])

            target_ref = report["biology"]["refs"]["target_projection_lock_ref"]
            target_path = root / target_ref
            payload = read_json(target_path)
            payload["row_count"] = 999
            write_json(target_path, payload)

            self.assertIn(f"mismatch::{target_ref}", orchestrator.check_stored(root))


if __name__ == "__main__":
    unittest.main()
