from __future__ import annotations

import json
import hashlib
import tempfile
import unittest
from pathlib import Path

from tools import oc133_chemistry_pubchem_formula_batch_factory as factory
from tools import oc133_official_readonly_acquisition_runner as runner
from tools import oc133_target_projection_lock_factory as projection_factory


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
        "criteria": {
            "current_target_blind_reconstructions_are_bounded_baseline_only": True,
        },
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


def pubchem_numeric_record(cid: int, formula: str) -> dict:
    row = pubchem_record(cid, formula)
    row["MolecularWeight"] = float(row["MolecularWeight"])
    return row


def nontrivial_comparator(pre_registered: bool = True, **overrides: object) -> dict:
    contract = factory.comparator_preregistration_contract()
    return {**contract, "pre_registered": pre_registered, **overrides}


def zero_da_comparator(pre_registered: bool = True, **overrides: object) -> dict:
    return {
        "kind": "constant_zero_da",
        "name": "zero-Da molecular-weight null baseline",
        "prediction_rule": "predict zero molecular weight for every PubChem compound",
        "pre_registered": pre_registered,
        **overrides,
    }


def pubchem_batch_snapshot(
    row_count: int,
    comparator_pre_registered: bool = True,
    comparator_baseline: dict | None = None,
) -> dict:
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
        "comparator_baseline": comparator_baseline
        if comparator_baseline is not None
        else nontrivial_comparator(pre_registered=comparator_pre_registered),
        "PropertyTable": {"Properties": rows},
    }


def legacy_seed_snapshot(metadata: dict | None = None) -> dict:
    row = pubchem_record(962, "H2O")
    if metadata is not None:
        row["legacy_seed_lock"] = metadata
    return {"PropertyTable": {"Properties": [row]}}


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


def projection_declaration(lock_id: str, snapshot_ref: str, target_fields: list[str] | None = None) -> dict:
    return {
        "schema_id": "TEST_CHEMISTRY_TARGET_PROJECTION_DECLARATION_v1",
        "lock_id": lock_id,
        "snapshot_ref": snapshot_ref,
        "snapshot_format": "json",
        "row_path": "PropertyTable.Properties",
        "row_id_field": "CID",
        "visible_fields": ["CID", "MolecularFormula"],
        "target_fields": target_fields or ["MolecularWeight"],
        "row_inclusion_rule": {"include_all": True},
        "model_declaration": {"kind": "constant", "value": 0},
        "comparator_declaration": {"kind": "constant", "value": 0},
        "residual_metric": "mae",
        "uncertainty_policy": {"max_model_residual": 100000.0, "min_model_advantage": 0.0},
        "negative_controls": [{"control_id": "chemistry-visible-only-null", "kind": "visible-only"}],
        "locks": dict(projection_factory.NO_SEND_LOCKS),
    }


def write_projection_lock_fixture(
    root: Path,
    acquisition_id: str,
    snapshot_ref: str,
    *,
    target_fields: list[str] | None = None,
) -> dict:
    declaration_ref = f"{factory.OUTPUT_ROOT_REL}/target_projection_declarations/{acquisition_id}.json"
    declaration_path = root / declaration_ref
    write_json(root, declaration_ref, projection_declaration(acquisition_id, snapshot_ref, target_fields))
    report, records = projection_factory.build_report_with_locks(root, [declaration_path])
    projection_factory.write_outputs(root, report, records)
    record = records[0]
    return {
        "declaration_ref": record["declaration_ref"],
        "declaration_sha256": record["declaration_sha256"],
        "snapshot_sha256": record["snapshot_sha256"],
        "visible_projection_lock_ref": record["visible_lock_ref"],
        "visible_projection_lock_sha256": record["visible_projection_sha256"],
        "prediction_materialization_lock_ref": record["prediction_lock_ref"],
        "prediction_materialization_lock_sha256": record["prediction_materialization_sha256"],
        "target_projection_lock_ref": record["target_lock_ref"],
        "target_projection_lock_sha256": record["target_projection_sha256"],
    }


def packet_target_projection_status(projection_refs: dict) -> dict:
    return {
        "required": True,
        "verified": True,
        "valid": True,
        "source_separation_derived": True,
        "generated_by": "tools/oc133_target_projection_lock_orchestrator.py",
        "standard_factory": "tools/oc133_target_projection_lock_factory.py",
        "refs": {
            "declaration_ref": projection_refs["declaration_ref"],
            "visible_projection_lock_ref": projection_refs["visible_projection_lock_ref"],
            "prediction_materialization_lock_ref": projection_refs["prediction_materialization_lock_ref"],
            "target_projection_lock_ref": projection_refs["target_projection_lock_ref"],
        },
        "hashes": {
            "declaration_sha256": projection_refs["declaration_sha256"],
            "snapshot_sha256": projection_refs["snapshot_sha256"],
            "visible_projection_lock_sha256": projection_refs["visible_projection_lock_sha256"],
            "prediction_materialization_lock_sha256": projection_refs["prediction_materialization_lock_sha256"],
            "target_projection_lock_sha256": projection_refs["target_projection_lock_sha256"],
        },
        "failures": [],
        "locks": dict(projection_factory.NO_SEND_LOCKS),
    }


def write_official_lock_with_projection_fixture(
    root: Path,
    idx: int,
    cid: str,
    formula: str,
    *,
    declare_projection: bool = True,
    target_fields: list[str] | None = None,
) -> None:
    acquisition_id = f"OC133-CHEM-PUBCHEM-FORMULA-ACQ-{idx:03d}"
    snapshot_ref = f"{factory.OFFICIAL_ACQUISITION_SNAPSHOTS_REL}/{acquisition_id}.json"
    lock_ref = f"{factory.OFFICIAL_ACQUISITION_LOCKS_REL}/{acquisition_id}.lock.json"
    payload = json.dumps(
        {"PropertyTable": {"Properties": [pubchem_numeric_record(int(cid), formula)]}},
        ensure_ascii=True,
        separators=(",", ":"),
    ).encode("utf-8") + b"\n"
    digest = hashlib.sha256(payload).hexdigest()
    expected_ref = f"{factory.OUTPUT_ROOT_REL}/raw/pubchem_cid_{cid}_properties.json"
    write_bytes(root, snapshot_ref, payload)
    projection_refs = (
        write_projection_lock_fixture(root, acquisition_id, snapshot_ref, target_fields=target_fields)
        if declare_projection
        else {}
    )
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
            "locks": dict(projection_factory.NO_SEND_LOCKS),
            "scientific_pass": False,
            **projection_refs,
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

    def test_target_projection_lock_derives_target_hidden_source_separation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(root, factory.REQUIREMENTS_REL, requirements(minimum_n=1))
            write_json(
                root,
                factory.ACQUISITION_REL,
                {
                    "schema_id": factory.ACQUISITION_SCHEMA_ID,
                    "exact_acquisition_requests": [acquisition_request(1, "702")],
                    "no_send": True,
                },
            )
            write_official_lock_with_projection_fixture(root, 1, "702", "C2H6O")

            payload = factory.build_payload(root)
            report = payload["report"]
            source = report["source_separation"]

            self.assertFalse(report["grand_toe_support_allowed"])
            self.assertEqual(source["mode"], "target_blind")
            self.assertEqual(source["kind"], "target_projection_lock_verified_pubchem_formula_batch")
            self.assertTrue(source["target_hidden_until_scoring"])
            self.assertTrue(source["derived_from_target_projection_lock"])
            self.assertEqual(payload["tasks"]["rows"][0]["comparator_baseline_kind"], factory.COMPARATOR_BASELINE_KIND)
            self.assertTrue(payload["tasks"]["rows"][0]["comparator_material_margin_met"])
            self.assertTrue(payload["tasks"]["rows"][0]["nontrivial_negative_controls_rejected"])
            self.assertTrue(payload["tasks"]["rows"][0]["target_projection_lock_verified"])
            self.assertNotIn("TARGET_HIDDEN_UNTIL_SCORING_REQUIRED", report["blockers"])
            self.assertNotIn("TARGET_PROJECTION_LOCK_REQUIRED_FOR_SOURCE_SEPARATION", report["blockers"])
            self.assertIn(factory.BOUNDED_REPLAY_BLOCKER, report["blockers"])
            self.assertEqual(payload["work_order"]["status"], "OPEN_STRONGER_CHEMISTRY_TARGET_REQUIRED")

    def test_packet_attached_target_projection_lock_is_used_when_official_lock_has_no_projection_refs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            acquisition_id = "OC133-CHEM-PUBCHEM-FORMULA-ACQ-001"
            snapshot_ref = f"{factory.OFFICIAL_ACQUISITION_SNAPSHOTS_REL}/{acquisition_id}.json"
            write_json(root, factory.REQUIREMENTS_REL, requirements(minimum_n=1))
            write_official_lock_fixture(root, 1, "702", "C2H6O")
            projection_refs = write_projection_lock_fixture(root, acquisition_id, snapshot_ref)
            write_json(
                root,
                factory.ACQUISITION_REL,
                {
                    "schema_id": factory.ACQUISITION_SCHEMA_ID,
                    "exact_acquisition_requests": [
                        {
                            **acquisition_request(1, "702"),
                            "target_projection_lock": packet_target_projection_status(projection_refs),
                        }
                    ],
                    "no_send": True,
                },
            )

            payload = factory.build_payload(root)
            report = payload["report"]
            blocker_text = " ".join(report["blockers"])

            self.assertFalse(report["grand_toe_support_allowed"])
            self.assertTrue(payload["tasks"]["rows"][0]["target_projection_lock_verified"])
            self.assertEqual(payload["tasks"]["rows"][0]["target_projection_lock_hashes"]["target_projection_lock_sha256"], projection_refs["target_projection_lock_sha256"])
            self.assertNotIn("TARGET_PROJECTION_LOCK_REF_MISSING", blocker_text)
            self.assertNotIn("TARGET_PROJECTION_LOCK_REQUIRED_FOR_SOURCE_SEPARATION", report["blockers"])
            self.assertIn(factory.BOUNDED_REPLAY_BLOCKER, report["blockers"])

    def test_invalid_packet_attached_target_projection_lock_does_not_close_chemistry_lock(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            acquisition_id = "OC133-CHEM-PUBCHEM-FORMULA-ACQ-001"
            snapshot_ref = f"{factory.OFFICIAL_ACQUISITION_SNAPSHOTS_REL}/{acquisition_id}.json"
            write_json(root, factory.REQUIREMENTS_REL, requirements(minimum_n=1))
            write_official_lock_fixture(root, 1, "702", "C2H6O")
            projection_refs = write_projection_lock_fixture(root, acquisition_id, snapshot_ref)
            status = packet_target_projection_status(projection_refs)
            status["hashes"]["target_projection_lock_sha256"] = "0" * 64
            write_json(
                root,
                factory.ACQUISITION_REL,
                {
                    "schema_id": factory.ACQUISITION_SCHEMA_ID,
                    "exact_acquisition_requests": [
                        {
                            **acquisition_request(1, "702"),
                            "target_projection_lock": status,
                        }
                    ],
                    "no_send": True,
                },
            )

            report = factory.build_payload(root)["report"]
            blocker_text = " ".join(report["blockers"])

            self.assertFalse(report["grand_toe_support_allowed"])
            self.assertIn("TARGET_PROJECTION_LOCK_HASH_MISMATCH::OC133-CHEM-PUBCHEM-FORMULA-ACQ-001", blocker_text)
            self.assertIn("TARGET_PROJECTION_LOCK_REQUIRED_FOR_SOURCE_SEPARATION", report["blockers"])
            self.assertIn("GRAND_TOE_SUPPORT_NOT_ALLOWED", report["blockers"])

    def test_tampered_wrong_target_projection_field_keeps_pack_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(root, factory.REQUIREMENTS_REL, requirements(minimum_n=1))
            write_json(
                root,
                factory.ACQUISITION_REL,
                {
                    "schema_id": factory.ACQUISITION_SCHEMA_ID,
                    "exact_acquisition_requests": [acquisition_request(1, "702")],
                    "no_send": True,
                },
            )
            write_official_lock_with_projection_fixture(root, 1, "702", "C2H6O", target_fields=["CanonicalSMILES"])

            report = factory.build_payload(root)["report"]
            blocker_text = " ".join(report["blockers"])

            self.assertFalse(report["grand_toe_support_allowed"])
            self.assertIn("TARGET_PROJECTION_FIELDS_MISMATCH::OC133-CHEM-PUBCHEM-FORMULA-ACQ-001", blocker_text)
            self.assertIn("TARGET_HIDDEN_UNTIL_SCORING_REQUIRED", report["blockers"])
            self.assertIn("GRAND_TOE_SUPPORT_NOT_ALLOWED", report["blockers"])

    def test_target_projection_artifact_exists_does_not_close_without_declared_lock(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            acquisition_id = "OC133-CHEM-PUBCHEM-FORMULA-ACQ-001"
            snapshot_ref = f"{factory.OFFICIAL_ACQUISITION_SNAPSHOTS_REL}/{acquisition_id}.json"
            write_json(root, factory.REQUIREMENTS_REL, requirements(minimum_n=1))
            write_json(
                root,
                factory.ACQUISITION_REL,
                {
                    "schema_id": factory.ACQUISITION_SCHEMA_ID,
                    "exact_acquisition_requests": [acquisition_request(1, "702")],
                    "no_send": True,
                },
            )
            write_official_lock_with_projection_fixture(root, 1, "702", "C2H6O", declare_projection=False)
            write_projection_lock_fixture(root, acquisition_id, snapshot_ref)

            report = factory.build_payload(root)["report"]
            blocker_text = " ".join(report["blockers"])

            self.assertFalse(report["grand_toe_support_allowed"])
            self.assertIn("TARGET_PROJECTION_LOCK_REF_MISSING::OC133-CHEM-PUBCHEM-FORMULA-ACQ-001", blocker_text)
            self.assertIn("TARGET_PROJECTION_LOCK_REQUIRED_FOR_SOURCE_SEPARATION", report["blockers"])
            self.assertIn("GRAND_TOE_SUPPORT_NOT_ALLOWED", report["blockers"])

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
        self.assertTrue(tasks["rows"][0]["declared_before_scoring_lock"])
        self.assertTrue(tasks["rows"][0]["target_projection_lock_verified"])
        self.assertTrue(tasks["rows"][0]["lock_ref"].startswith(factory.LEGACY_SEED_LOCK_ROOT_REL))
        self.assertTrue(tasks["rows"][0]["comparator_pre_registered"])

        blocker_text = " ".join(report["blockers"])
        self.assertNotIn("SOURCE_SEPARATION_MODE_NOT_ALLOWED::snapshot_replay", blocker_text)
        self.assertNotIn("TARGET_HIDDEN_UNTIL_SCORING_REQUIRED", blocker_text)
        self.assertNotIn("DECLARED_BEFORE_SCORING_LOCK_REQUIRED", blocker_text)
        self.assertNotIn("COMPARATOR_BASELINE_NOT_PREREGISTERED", blocker_text)
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

    def test_missing_seed_lock_metadata_auto_upgrades_valid_legacy_seed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot_ref = "validation/_raw/chemistry_pubchem_water.txt"
            write_json(root, factory.REQUIREMENTS_REL, requirements(minimum_n=1))
            write_json(root, snapshot_ref, legacy_seed_snapshot())

            payload = factory.build_payload(root, snapshot_refs=[snapshot_ref])
            report = payload["report"]
            row = payload["tasks"]["rows"][0]

            self.assertFalse(report["grand_toe_support_allowed"])
            self.assertEqual(report["candidate_n"], 1)
            self.assertTrue(row["declared_before_scoring_lock"])
            self.assertTrue(row["target_projection_lock_verified"])
            self.assertTrue(row["lock_ref"].startswith(factory.LEGACY_SEED_LOCK_ROOT_REL))
            self.assertTrue(row["comparator_pre_registered"])
            self.assertEqual(report["source_separation"]["kind"], "target_projection_lock_verified_pubchem_formula_batch")
            self.assertIn(factory.BOUNDED_REPLAY_BLOCKER, report["blockers"])
            self.assertEqual(payload["work_order"]["status"], "OPEN_STRONGER_CHEMISTRY_TARGET_REQUIRED")

    def test_tampered_seed_lock_hash_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot_ref = "validation/_raw/chemistry_pubchem_water.txt"
            write_json(root, factory.REQUIREMENTS_REL, requirements(minimum_n=1))
            write_json(root, snapshot_ref, legacy_seed_snapshot({"lock_sha256": "0" * 64}))

            payload = factory.build_payload(root, snapshot_refs=[snapshot_ref])
            report = payload["report"]
            row = payload["tasks"]["rows"][0]
            blocker_text = " ".join(report["blockers"])

            self.assertFalse(report["grand_toe_support_allowed"])
            self.assertFalse(row["target_projection_lock_verified"])
            self.assertIn(f"LEGACY_SEED_LOCK_HASH_MISMATCH::{snapshot_ref}::1", blocker_text)
            self.assertIn("GRAND_TOE_SUPPORT_NOT_ALLOWED", report["blockers"])

    def test_stale_legacy_seed_comparator_baseline_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot_ref = "validation/_raw/chemistry_pubchem_water.txt"
            write_json(root, factory.REQUIREMENTS_REL, requirements(minimum_n=1))
            write_json(root, snapshot_ref, legacy_seed_snapshot({"comparator_baseline_sha256": "0" * 64}))

            payload = factory.build_payload(root, snapshot_refs=[snapshot_ref])
            report = payload["report"]
            row = payload["tasks"]["rows"][0]
            blocker_text = " ".join(report["blockers"])

            self.assertFalse(report["grand_toe_support_allowed"])
            self.assertFalse(row["target_projection_lock_verified"])
            self.assertIn(f"LEGACY_SEED_COMPARATOR_BASELINE_STALE::{snapshot_ref}::1", blocker_text)
            self.assertIn("GRAND_TOE_SUPPORT_NOT_ALLOWED", report["blockers"])

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

    def test_trivial_zero_da_comparator_alone_blocks_grand_support(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot_ref = "validation/_raw/pubchem_formula_batch_zero_comparator.json"
            write_json(root, factory.REQUIREMENTS_REL, requirements())
            write_json(root, snapshot_ref, pubchem_batch_snapshot(row_count=20, comparator_baseline=zero_da_comparator()))

            payload = factory.build_payload(root, snapshot_refs=[snapshot_ref])
            report = payload["report"]
            row = payload["tasks"]["rows"][0]

            self.assertFalse(report["grand_toe_support_allowed"])
            self.assertEqual(row["comparator_prediction"], 0.0)
            self.assertIn("TRIVIAL_COMPARATOR_BASELINE_NOT_ALLOWED", report["blockers"])
            self.assertIn("NONTRIVIAL_COMPARATOR_REQUIRED", report["blockers"])
            self.assertIn("GRAND_TOE_SUPPORT_NOT_ALLOWED", report["blockers"])

    def test_comparator_target_leakage_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot_ref = "validation/_raw/pubchem_formula_batch_target_leakage.json"
            write_json(root, factory.REQUIREMENTS_REL, requirements())
            write_json(
                root,
                snapshot_ref,
                pubchem_batch_snapshot(
                    row_count=20,
                    comparator_baseline=nontrivial_comparator(
                        uses_target_values=True,
                        prediction_inputs=["MolecularFormula", "MolecularWeight"],
                    ),
                ),
            )

            report = factory.build_payload(root, snapshot_refs=[snapshot_ref])["report"]

            self.assertFalse(report["grand_toe_support_allowed"])
            self.assertIn("COMPARATOR_TARGET_LEAKAGE", report["blockers"])
            self.assertIn("GRAND_TOE_SUPPORT_NOT_ALLOWED", report["blockers"])

    def test_stale_nontrivial_comparator_preregistration_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot_ref = "validation/_raw/pubchem_formula_batch_stale_comparator.json"
            write_json(root, factory.REQUIREMENTS_REL, requirements())
            write_json(
                root,
                snapshot_ref,
                pubchem_batch_snapshot(
                    row_count=20,
                    comparator_baseline=nontrivial_comparator(baseline_sha256="0" * 64),
                ),
            )

            report = factory.build_payload(root, snapshot_refs=[snapshot_ref])["report"]

            self.assertFalse(report["grand_toe_support_allowed"])
            self.assertIn("COMPARATOR_BASELINE_PREREGISTRATION_STALE", report["blockers"])
            self.assertIn("GRAND_TOE_SUPPORT_NOT_ALLOWED", report["blockers"])


if __name__ == "__main__":
    raise SystemExit(unittest.main())
