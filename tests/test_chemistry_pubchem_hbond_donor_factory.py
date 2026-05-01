from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools import oc133_chemistry_pubchem_formula_batch_factory as formula_factory
from tools import oc133_chemistry_pubchem_hbond_donor_factory as factory
from tools import oc133_official_readonly_acquisition_runner as acquisition_runner


def write_json(root: Path, ref: str, payload: object) -> None:
    path = root / ref
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8", newline="\n")


def requirements() -> dict[str, object]:
    return {
        "minimum_per_domain_n": 20,
        "required_domains": ["biology", "chemistry", "mathematics", "physics", "systems"],
        "required_source_separation_modes": ["prospective", "target_blind"],
        "criteria": {"current_target_blind_reconstructions_are_bounded_baseline_only": True},
    }


def pubchem_payload(cid: int, formula: str, smiles: str, donors: int) -> dict[str, object]:
    return {
        "PropertyTable": {
            "Properties": [
                {
                    "CID": cid,
                    "MolecularFormula": formula,
                    "CanonicalSMILES": smiles,
                    "ConnectivitySMILES": smiles,
                    "HBondDonorCount": donors,
                }
            ]
        }
    }


FIXTURES = [
    (962, "H2O", "O", 1),
    (702, "C2H6O", "CCO", 1),
    (176, "C2H4O2", "CC(=O)O", 1),
    (180, "C3H6O", "CC(=O)C", 0),
    (241, "C6H6", "C1=CC=CC=C1", 0),
    (887, "CH4O", "CO", 1),
    (284, "CH2O2", "C(=O)O", 1),
    (996, "C6H6O", "C1=CC=C(C=C1)O", 1),
    (6115, "C6H7N", "C1=CC=C(C=C1)N", 1),
    (178, "C2H5NO", "CC(=O)N", 1),
    (8254, "C2H6O", "COC", 0),
    (8857, "C4H8O2", "CCOC(=O)C", 0),
    (1049, "C5H5N", "C1=CC=NC=C1", 0),
    (795, "C3H4N2", "C1=NC=CN1", 1),
    (1176, "CH4N2O", "C(=O)(N)N", 2),
    (6342, "C2H3N", "CC#N", 0),
    (753, "C3H8O3", "C(C(CO)O)O", 3),
    (280, "CO2", "C(=O)=O", 0),
    (222, "H3N", "N", 1),
    (297, "CH4", "C", 0),
]


def write_acquired_fixture(root: Path, index: int, cid: int, formula: str, smiles: str, donors: int) -> None:
    request_id = factory.acquisition_id(index)
    snapshot_ref = f"{acquisition_runner.SNAPSHOT_ROOT_REL}/{request_id}.json"
    lock_ref = f"{acquisition_runner.LOCK_ROOT_REL}/{request_id}.lock.json"
    payload = pubchem_payload(cid, formula, smiles, donors)
    snapshot_path = root / snapshot_ref
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(payload, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
    snapshot_path.write_bytes(raw)
    sha = factory.sha256_bytes(raw)
    lock = {
        "schema_id": "OC133_OFFICIAL_READONLY_ACQUISITION_NO_SEND_LOCK_v1",
        "release_id": factory.RELEASE_ID,
        "acquisition_id": request_id,
        "official_endpoint_url": factory.pubchem_property_url(str(cid)),
        "expected_local_snapshot_ref": f"{factory.OUTPUT_ROOT_REL}/raw/pubchem_cid_{cid}_hbond_donor.json",
        "snapshot_ref": snapshot_ref,
        "snapshot_sha256": sha,
        "source_bytes_sha256": sha,
        "byte_count": len(raw),
        "http_status": 200,
        "hash_policy": acquisition_runner.HASH_POLICY,
        "pre_target_sequence_proof": {
            "source_snapshot_locked_before_scoring": True,
            "source_snapshot_pre_target_lock": True,
            "target_hidden_until_scoring": True,
            "target_projection_unsealed_for_scoring": False,
            "scoring_started": False,
            "prediction_materialization_required_before_scoring": True,
            "target_projection_read_before_prediction_materialization": False,
        },
        "locks": factory.NO_SEND_LOCKS,
    }
    write_json(root, lock_ref, lock)


def write_formula_fixture(root: Path, idx: int, cid: int, formula: str) -> None:
    payload = {
        "PropertyTable": {
            "Properties": [
                {
                    "CID": cid,
                    "MolecularFormula": formula,
                    "MolecularWeight": formula_factory.formula_weight(formula_factory.parse_formula(formula))[0],
                    "CanonicalSMILES": "C",
                    "InChIKey": f"TEST-{idx}",
                }
            ]
        }
    }
    write_json(root, f"validation/_raw/formula_mass_only_{idx:03d}.json", payload)


class ChemistryPubChemHbondDonorFactoryTests(unittest.TestCase):
    def test_smiles_donor_model_and_formula_comparator_support_pass_on_official_fixtures(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(root, factory.REQUIREMENTS_REL, requirements())
            for index, fixture in enumerate(FIXTURES, start=1):
                write_acquired_fixture(root, index, *fixture)

            payload = factory.build_payload(root)

            self.assertTrue(payload["report"]["grand_toe_support_allowed"])
            self.assertEqual(payload["candidate_pack"]["n"], 20)
            self.assertEqual(payload["report"]["residuals"]["model"], 0.0)
            self.assertGreaterEqual(payload["report"]["residuals"]["superiority_margin"], factory.MIN_COMPARATOR_ADVANTAGE)
            self.assertEqual(payload["report"]["blockers"], [])

    def test_formula_mass_only_support_remains_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(root, formula_factory.REQUIREMENTS_REL, requirements())
            snapshot_refs = []
            for index, (cid, formula, _smiles, _donors) in enumerate(FIXTURES, start=1):
                write_formula_fixture(root, index, cid, formula)
                snapshot_refs.append(f"validation/_raw/formula_mass_only_{index:03d}.json")

            payload = formula_factory.build_payload(root, snapshot_refs=snapshot_refs)

            self.assertFalse(payload["report"]["grand_toe_support_allowed"])
            self.assertIn(formula_factory.BOUNDED_REPLAY_BLOCKER, payload["report"]["blockers"])
            self.assertFalse(payload["candidate_pack"]["grand_toe_support_allowed"])

    def test_target_leakage_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(root, factory.REQUIREMENTS_REL, requirements())
            for index, fixture in enumerate(FIXTURES, start=1):
                write_acquired_fixture(root, index, *fixture)

            payload = factory.build_payload(root, visible_fields=[*factory.VISIBLE_FIELDS, factory.TARGET_FIELD])

            self.assertFalse(payload["report"]["grand_toe_support_allowed"])
            self.assertIn("TARGET_LEAKAGE_VISIBLE_FIELD", payload["report"]["blockers"])

    def test_trivial_comparator_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(root, factory.REQUIREMENTS_REL, requirements())
            for index, fixture in enumerate(FIXTURES, start=1):
                write_acquired_fixture(root, index, *fixture)

            payload = factory.build_payload(
                root,
                comparator_baseline={
                    "kind": "constant_zero",
                    "name": "constant zero donor-count comparator",
                    "prediction_rule": "predict constant zero donor count",
                    "pre_registered": True,
                    "value": 0,
                },
            )

            self.assertFalse(payload["report"]["grand_toe_support_allowed"])
            self.assertIn("TRIVIAL_COMPARATOR_BASELINE_NOT_ALLOWED", payload["report"]["blockers"])

    def test_n_below_20_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(root, factory.REQUIREMENTS_REL, requirements())
            for index, fixture in enumerate(FIXTURES[:19], start=1):
                write_acquired_fixture(root, index, *fixture)

            payload = factory.build_payload(root)

            self.assertFalse(payload["report"]["grand_toe_support_allowed"])
            self.assertIn("N_BELOW_MINIMUM::19/20", payload["report"]["blockers"])


if __name__ == "__main__":
    raise SystemExit(unittest.main())
