from __future__ import annotations

import json
import hashlib
import tempfile
import unittest
from pathlib import Path

from tools import oc133_chemistry_pubchem_formula_batch_factory as factory
from tools import oc133_official_readonly_acquisition_runner as runner


REPO_ROOT = Path(__file__).resolve().parents[1]


def write_json(root: Path, rel_path: str, payload: dict) -> None:
    path = root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_bytes(root: Path, rel_path: str, payload: bytes) -> None:
    path = root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def requirements(minimum_n: int = 20) -> dict:
    return {
        "schema_id": "OC133_GRAND_EMPIRICAL_DOMAIN_REQUIREMENTS_v1",
        "release_id": "oc_core_1_3_3",
        "capability_owner": "Research/EmpiricalScience",
        "minimum_per_domain_n": minimum_n,
        "required_domains": ["biology", "chemistry", "mathematics", "physics", "systems"],
        "required_source_separation_modes": ["prospective", "target_blind"],
    }


def batch_source_separation() -> dict:
    return {
        "mode": "target_blind",
        "kind": "target_blind_pubchem_formula_holdout_batch",
        "pre_target_lock": True,
        "target_hidden_until_scoring": True,
        "declared_before_scoring": True,
        "training_sources": ["mock-pubchem://formula-training-manifest-v1"],
        "target_sources": ["mock-pubchem://molecular-weight-target-manifest-v1"],
    }


def molecular_weight_text(formula: str) -> str:
    composition = factory.parse_formula(formula)
    weight, _trace = factory.formula_weight(composition)
    return f"{weight:.3f}"


def pubchem_record(cid: int, formula: str) -> dict:
    return {
        "CID": cid,
        "MolecularFormula": formula,
        "MolecularWeight": molecular_weight_text(formula),
        "CanonicalSMILES": f"mock-{cid}",
        "InChIKey": f"MOCKKEY{cid}",
    }


def pubchem_batch_snapshot(row_count: int, comparator_pre_registered: bool = True) -> dict:
    formulas = [
        "H2O",
        "CO2",
        "CH4",
        "C2H6O",
        "C6H12O6",
        "NH3",
        "NaCl",
        "C8H10N4O2",
        "C9H8O4",
        "C3H8O",
        "C2H4O2",
        "C7H8",
        "C10H14N2",
        "C4H10",
        "C5H12",
        "C6H6",
        "C12H22O11",
        "C2H6",
        "C3H6O",
        "C4H8O2",
    ]
    cids = [int(cid) for cid in factory.DEFAULT_CID_PLAN]
    rows = [pubchem_record(cids[idx], formulas[idx]) for idx in range(row_count)]
    return {
        "source_separation": batch_source_separation(),
        "snapshot_provenance": {
            "official_source": "PubChem PUG REST",
            "official_url": factory.pubchem_property_url(",".join(str(row["CID"]) for row in rows)),
        },
        "comparator_baseline": {
            "name": "zero-Da molecular-weight null baseline",
            "prediction_rule": "predict zero molecular weight for every PubChem compound",
            "pre_registered": comparator_pre_registered,
        },
        "PropertyTable": {"Properties": rows},
    }


def acquisition_request(idx: int, cid: str) -> dict:
    return {
        "request_id": f"OC133-CHEM-PUBCHEM-FORMULA-ACQ-{idx:03d}",
        "cid": cid,
        "method": "GET",
        "official_endpoint_url": factory.pubchem_property_url(cid),
        "expected_local_snapshot_ref": f"{factory.OUTPUT_ROOT_REL}/raw/pubchem_cid_{cid}_properties.json",
        "required_fields": factory.OFFICIAL_PUG_PROPERTY_FIELDS.split(","),
        "target_field": "MolecularWeight",
        "visible_training_fields": ["CID", "MolecularFormula"],
        "no_send_lock": True,
    }


def write_official_lock_fixture(root: Path, idx: int, cid: str, formula: str) -> None:
    acquisition_id = f"OC133-CHEM-PUBCHEM-FORMULA-ACQ-{idx:03d}"
    snapshot_ref = f"{factory.OFFICIAL_ACQUISITION_SNAPSHOTS_REL}/{acquisition_id}.json"
    lock_ref = f"{factory.OFFICIAL_ACQUISITION_LOCKS_REL}/{acquisition_id}.lock.json"
    payload = json.dumps(
        {"PropertyTable": {"Properties": [pubchem_record(int(cid), formula)]}},
        ensure_ascii=True,
        separators=(",", ":"),
    ).encode("utf-8") + b"\n"
    digest = hashlib.sha256(payload).hexdigest()
    expected_ref = f"{factory.OUTPUT_ROOT_REL}/raw/pubchem_cid_{cid}_properties.json"
    write_bytes(root, snapshot_ref, payload)
    write_json(
        root,
        lock_ref,
        {
            "schema_id": "OC133_OFFICIAL_READONLY_ACQUISITION_NO_SEND_LOCK_v1",
            "release_id": "oc_core_1_3_3",
            "acquisition_id": acquisition_id,
            "official_endpoint_url": factory.pubchem_property_url(cid),
            "expected_local_snapshot_ref": expected_ref,
            "snapshot_ref": snapshot_ref,
            "snapshot_sha256": digest,
            "byte_count": len(payload),
            "http_status": 200,
            "hash_policy": factory.OFFICIAL_ACQUISITION_HASH_POLICY,
            "locks": {"no_send": True, "publish_allowed": False, "registry_write_allowed": False},
            "scientific_pass": False,
        },
    )


class ChemistryPubchemFormulaBatchFactoryTests(unittest.TestCase):
    def test_fixed_atomic_table_covers_acquired_heavy_and_metal_formula_cases(self) -> None:
        self.assertEqual(factory.ATOMIC_WEIGHT_TABLE_ID, "OC133_FIXED_AVERAGE_ATOMIC_WEIGHTS_v2")
        self.assertEqual(
            factory.sha256_object(factory.ATOMIC_WEIGHTS),
            "cc92ae968fff602cd8309a231261e8a7629694d95ba91ccb3714f78ce0c4e118",
        )
        self.assertIn("mercury", factory.ATOMIC_WEIGHT_SOURCE_NOTE.lower())

        cases = [
            ("ClNa", {"Cl": 1, "Na": 1}, 58.44276928),
            ("Hg", {"Hg": 1}, 200.59),
        ]
        for formula, expected_composition, expected_weight in cases:
            with self.subTest(formula=formula):
                composition = factory.parse_formula(formula)
                weight, trace = factory.formula_weight(composition)
                self.assertEqual(composition, expected_composition)
                self.assertAlmostEqual(weight, expected_weight, places=8)
                self.assertEqual({item["element"] for item in trace}, set(expected_composition))

    def test_official_acquisition_heavy_and_metal_formulas_are_scorable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(root, factory.REQUIREMENTS_REL, requirements())
            write_json(
                root,
                factory.ACQUISITION_REL,
                {
                    "schema_id": factory.ACQUISITION_SCHEMA_ID,
                    "exact_acquisition_requests": [
                        acquisition_request(1, "5234"),
                        acquisition_request(2, "23931"),
                    ],
                    "no_send": True,
                },
            )
            write_official_lock_fixture(root, 1, "5234", "ClNa")
            write_official_lock_fixture(root, 2, "23931", "Hg")

            payload = factory.build_payload(root)
            rows_by_formula = {row["molecular_formula"]: row for row in payload["tasks"]["rows"]}
            blocker_text = " ".join(payload["report"]["blockers"])

            self.assertEqual(payload["report"]["candidate_n"], 2)
            self.assertNotIn("FORMULA_PARSE_FAILED", blocker_text)
            self.assertAlmostEqual(rows_by_formula["ClNa"]["predicted_value"], 58.44276928, places=8)
            self.assertAlmostEqual(rows_by_formula["Hg"]["predicted_value"], 200.59, places=8)
            self.assertTrue(rows_by_formula["Hg"]["negative_control_rejected"])
            self.assertEqual(rows_by_formula["Hg"]["falsifier_status"], "NOT_TRIGGERED")

    def test_current_water_snapshot_blocks_and_emits_exact_acquisition_requests(self) -> None:
        payload = factory.build_payload(REPO_ROOT, snapshot_refs=[factory.DEFAULT_SNAPSHOT_REF])
        report = payload["report"]
        tasks = payload["tasks"]
        acquisition = payload["acquisition_packet"]
        pack = payload["candidate_pack"]

        self.assertFalse(report["grand_toe_support_allowed"])
        self.assertEqual(report["verdict"], "BLOCKED_ACQUISITION_READY_PUBCHEM_FORMULA_BATCH")
        self.assertEqual(report["candidate_n"], 1)
        self.assertEqual(report["missing_n"], 19)
        self.assertEqual(acquisition["request_total"], 19)
        self.assertEqual(acquisition["request_total"], report["missing_n"])
        self.assertEqual(acquisition["missing_official_snapshot_total"], report["missing_n"])
        self.assertEqual(acquisition["missing_official_snapshots"], acquisition["exact_acquisition_requests"])
        self.assertFalse(pack["grand_toe_support_allowed"])
        self.assertFalse(acquisition["publish_allowed"])
        self.assertFalse(acquisition["registry_write_allowed"])
        self.assertTrue(tasks["rows"][0]["row_hash"])
        self.assertEqual(tasks["rows"][0]["molecular_formula"], "H2O")
        self.assertAlmostEqual(tasks["rows"][0]["predicted_value"], 18.01528, places=5)
        self.assertIn("formula_evaluation_trace", tasks["rows"][0])
        self.assertEqual(tasks["atomic_weight_table"]["table_id"], factory.ATOMIC_WEIGHT_TABLE_ID)

        blocker_text = " ".join(report["blockers"])
        self.assertIn("SOURCE_SEPARATION_MODE_NOT_ALLOWED::snapshot_replay", blocker_text)
        self.assertIn("TARGET_HIDDEN_UNTIL_SCORING_REQUIRED", blocker_text)
        self.assertIn("DECLARED_BEFORE_SCORING_LOCK_REQUIRED", blocker_text)
        self.assertIn("COMPARATOR_BASELINE_NOT_PREREGISTERED", blocker_text)
        self.assertIn("N_BELOW_MINIMUM::1/20", blocker_text)
        self.assertIn("GRAND_TOE_SUPPORT_NOT_ALLOWED", blocker_text)

        first_request = acquisition["exact_acquisition_requests"][0]
        self.assertEqual(first_request["method"], "GET")
        self.assertEqual(first_request["cid"], "702")
        self.assertEqual(
            first_request["expected_local_snapshot_ref"],
            f"{factory.OUTPUT_ROOT_REL}/raw/pubchem_cid_702_properties.json",
        )
        self.assertIn("pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid", first_request["official_endpoint_url"])
        self.assertEqual(first_request["required_fields"], factory.OFFICIAL_PUG_PROPERTY_FIELDS.split(","))
        self.assertTrue(first_request["no_send_lock"])
        runner_rows = runner.packet_acquisition_rows(acquisition)
        self.assertEqual(len(runner_rows), report["missing_n"])
        self.assertEqual(runner_rows[0]["acquisition_id"], first_request["acquisition_id"])
        self.assertTrue(all(row["no_send_lock"] for row in runner_rows))
        self.assertTrue(all(runner.allowlist_match(row["official_endpoint_url"])[0] for row in runner_rows))
        self.assertTrue(
            all(row["expected_local_snapshot_ref"].startswith(f"{factory.OUTPUT_ROOT_REL}/raw/") for row in runner_rows)
        )

    def test_fixture_pubchem_acquisition_locks_are_scored_without_fake_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(root, factory.REQUIREMENTS_REL, requirements())
            write_json(
                root,
                factory.ACQUISITION_REL,
                {
                    "schema_id": factory.ACQUISITION_SCHEMA_ID,
                    "exact_acquisition_requests": [
                        acquisition_request(1, "702"),
                        acquisition_request(2, "241"),
                        acquisition_request(3, "180"),
                    ],
                    "no_send": True,
                },
            )
            write_official_lock_fixture(root, 1, "702", "C2H6O")
            write_official_lock_fixture(root, 2, "241", "CO2")

            payload = factory.write_outputs(root)
            report = payload["report"]
            pack = payload["candidate_pack"]
            acquisition = payload["acquisition_packet"]

            self.assertEqual(factory.check_stored(root), [])
            self.assertFalse(report["grand_toe_support_allowed"])
            self.assertEqual(report["candidate_n"], 2)
            self.assertEqual(pack["n"], 2)
            self.assertIn("TARGET_HIDDEN_UNTIL_SCORING_REQUIRED", report["blockers"])
            self.assertTrue(pack["comparator_baseline"]["pre_registered"])
            self.assertEqual(acquisition["request_total"], 18)
            self.assertEqual(acquisition["missing_official_snapshot_total"], 18)
            self.assertEqual(
                runner.packet_acquisition_rows(acquisition),
                acquisition["missing_official_snapshots"],
            )
            self.assertEqual(acquisition["exact_acquisition_requests"][0]["acquisition_id"], "OC133-CHEM-PUBCHEM-FORMULA-ACQ-003")
            self.assertTrue(all(row["declared_before_scoring_lock"] for row in payload["tasks"]["rows"]))
            self.assertTrue(all(row["lock_ref"].endswith(".lock.json") for row in payload["tasks"]["rows"]))
            self.assertEqual(payload["tasks"]["rows"][0]["negative_control_status"], "REJECTED")
            self.assertTrue((root / factory.TASKS_REL).is_file())
            self.assertTrue((root / factory.PROTOCOL_REL).is_file())
            self.assertTrue((root / factory.CANDIDATE_PACK_REL).is_file())
            self.assertTrue((root / factory.REPORT_REL).is_file())
            self.assertTrue((root / factory.ACQUISITION_REL).is_file())
            self.assertTrue((root / factory.HASHES_REL).is_file())
            self.assertTrue((root / factory.README_REL).is_file())

    def test_nineteen_pubchem_rows_remain_blocked_without_fake_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot_ref = "validation/_raw/pubchem_formula_batch_19.json"
            write_json(root, factory.REQUIREMENTS_REL, requirements())
            write_json(root, snapshot_ref, pubchem_batch_snapshot(row_count=19))

            payload = factory.build_payload(root, snapshot_refs=[snapshot_ref])
            report = payload["report"]

            self.assertFalse(report["grand_toe_support_allowed"])
            self.assertIn("N_BELOW_MINIMUM::19/20", report["blockers"])
            self.assertIn("GRAND_TOE_SUPPORT_NOT_ALLOWED", report["blockers"])
            self.assertEqual(payload["acquisition_packet"]["request_total"], 1)
            self.assertEqual(payload["acquisition_packet"]["missing_official_snapshot_total"], 1)
            self.assertEqual(
                runner.packet_acquisition_rows(payload["acquisition_packet"]),
                payload["acquisition_packet"]["missing_official_snapshots"],
            )
            self.assertEqual(payload["candidate_pack"]["n"], 19)

    def test_empty_snapshot_set_emits_twenty_exact_pubchem_requests(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(root, factory.REQUIREMENTS_REL, requirements())

            payload = factory.build_payload(root, snapshot_refs=[])
            report = payload["report"]
            acquisition = payload["acquisition_packet"]

            self.assertFalse(report["grand_toe_support_allowed"])
            self.assertIn("NO_LOCAL_PUBCHEM_PUG_REST_SNAPSHOTS_DISCOVERED", report["blockers"])
            self.assertEqual(acquisition["request_total"], 20)
            self.assertEqual(acquisition["missing_official_snapshot_total"], 20)
            self.assertEqual(len(runner.packet_acquisition_rows(acquisition)), 20)
            self.assertEqual(acquisition["exact_acquisition_requests"][0]["cid"], factory.DEFAULT_CID_PLAN[0])
            self.assertEqual(
                acquisition["exact_acquisition_requests"][0]["official_endpoint_url"],
                factory.pubchem_property_url(factory.DEFAULT_CID_PLAN[0]),
            )

    def test_unregistered_comparator_blocks_otherwise_valid_batch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot_ref = "validation/_raw/pubchem_formula_batch_unregistered_comparator.json"
            write_json(root, factory.REQUIREMENTS_REL, requirements())
            write_json(root, snapshot_ref, pubchem_batch_snapshot(row_count=20, comparator_pre_registered=False))

            report = factory.build_payload(root, snapshot_refs=[snapshot_ref])["report"]

            self.assertFalse(report["grand_toe_support_allowed"])
            self.assertIn("COMPARATOR_BASELINE_NOT_PREREGISTERED", report["blockers"])
            self.assertIn("GRAND_TOE_SUPPORT_NOT_ALLOWED", report["blockers"])


if __name__ == "__main__":
    raise SystemExit(unittest.main())
