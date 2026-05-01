from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools import oc133_target_projection_lock_factory as factory


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8", newline="\n")


def strict_locks() -> dict[str, object]:
    return dict(factory.NO_SEND_LOCKS)


def base_snapshot() -> list[dict[str, object]]:
    return [
        {"id": "a", "split": "holdout", "x": 1, "y": 3},
        {"id": "b", "split": "holdout", "x": 2, "y": 5},
        {"id": "c", "split": "train", "x": 99, "y": 999},
    ]


def base_declaration(snapshot_ref: str = "snapshots/official.json") -> dict[str, object]:
    return {
        "schema_id": "TEST_TARGET_PROJECTION_DECLARATION_v1",
        "lock_id": "unit-linear-lock",
        "snapshot_ref": snapshot_ref,
        "snapshot_format": "auto",
        "row_id_field": "id",
        "visible_fields": ["id", "split", "x"],
        "target_fields": ["y"],
        "row_inclusion_rule": {"field": "split", "equals": "holdout"},
        "model_declaration": {
            "kind": "linear",
            "intercept": 1,
            "terms": [{"field": "x", "coefficient": 2}],
        },
        "comparator_declaration": {"kind": "constant", "value": 0},
        "residual_metric": "mae",
        "uncertainty_policy": {"max_model_residual": 0.0, "min_model_advantage": 0.0},
        "negative_controls": [{"control_id": "declared-null-control", "kind": "locked-visible-only"}],
        "locks": strict_locks(),
    }


def ncbi_list_length_declaration(snapshot_ref: str = "snapshots/ncbi.json") -> dict[str, object]:
    return {
        "schema_id": "TEST_TARGET_PROJECTION_DECLARATION_v1",
        "lock_id": "unit-list-length-lock",
        "snapshot_ref": snapshot_ref,
        "snapshot_format": "auto",
        "row_id_field": "id",
        "visible_fields": ["id", "esearchresult.idlist"],
        "target_fields": ["esearchresult.retmax"],
        "row_inclusion_rule": {"include_all": True},
        "model_declaration": {"kind": "list_length", "field": "esearchresult.idlist"},
        "comparator_declaration": {"kind": "constant", "value": 0},
        "residual_metric": "mae",
        "uncertainty_policy": {"max_model_residual": 0.0, "min_model_advantage": 0.0},
        "negative_controls": [{"control_id": "zero-length-control", "kind": "locked-visible-only"}],
        "locks": strict_locks(),
    }


def pubchem_formula_declaration(snapshot_ref: str = "snapshots/pubchem.json") -> dict[str, object]:
    return {
        "schema_id": "TEST_TARGET_PROJECTION_DECLARATION_v1",
        "lock_id": "unit-formula-weight-lock",
        "snapshot_ref": snapshot_ref,
        "snapshot_format": "auto",
        "row_id_field": "CID",
        "visible_fields": ["CID", "MolecularFormula"],
        "target_fields": ["MolecularWeight"],
        "row_inclusion_rule": {"include_all": True},
        "model_declaration": {
            "kind": "chemical_formula_weight",
            "formula_field": "MolecularFormula",
            "atomic_weights": {"H": 1.008, "C": 12.011, "N": 14.007, "O": 15.999},
        },
        "comparator_declaration": {"kind": "constant", "value": 0},
        "residual_metric": "mae",
        "uncertainty_policy": {"max_model_residual": 0.001, "min_model_advantage": 0.0},
        "negative_controls": [{"control_id": "zero-da-control", "kind": "locked-visible-only"}],
        "locks": strict_locks(),
    }


class TargetProjectionLockFactoryTests(unittest.TestCase):
    def test_builds_target_blind_projection_locks_and_pass_verdict(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot = root / "snapshots/official.json"
            declaration = root / "declarations/lock.json"
            write_json(snapshot, base_snapshot())
            write_json(declaration, base_declaration())

            report, records = factory.build_report_with_locks(root, [declaration])

            self.assertEqual(report["record_total"], 1)
            self.assertEqual(report["locked_pass_total"], 1)
            self.assertEqual(report["open_blocker_total"], 0)
            self.assertNotIn("grand_toe_support_allowed", json.dumps(report))

            record = records[0]
            self.assertEqual(record["verdict"], "LOCKED_PASS")
            self.assertEqual(record["residual_summary"]["model_residual"], 0.0)
            self.assertEqual(record["visible_projection_lock"]["row_count"], 2)
            self.assertEqual(record["target_projection_lock"]["row_count"], 2)
            self.assertTrue(record["tamper_controls"]["target_opened_after_prediction_materialization"])
            self.assertFalse(
                record["prediction_materialization_lock"]["algorithmic_target_separation"][
                    "target_projection_read_before_prediction_materialization"
                ]
            )
            self.assertEqual(record["prediction_materialization_lock"]["prediction_rows"][0]["model_prediction"], 3.0)
            self.assertEqual(record["target_projection_lock"]["rows"][0]["target"]["y"], 3)
            self.assertEqual(record["target_projection_lock"]["locks"], factory.NO_SEND_LOCKS)

    def test_fails_closed_when_target_field_is_visible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot = root / "snapshots/official.json"
            declaration = root / "declarations/lock.json"
            payload = base_declaration()
            payload["visible_fields"] = ["id", "split", "x", "y"]
            write_json(snapshot, base_snapshot())
            write_json(declaration, payload)

            report = factory.build_report(root, [declaration])

            self.assertEqual(report["blocked_total"], 1)
            self.assertIn("TARGET_FIELD_IN_VISIBLE_PROJECTION::y", report["blockers"])

    def test_fails_closed_when_declaration_contains_target_value(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot = root / "snapshots/official.json"
            declaration = root / "declarations/lock.json"
            payload = base_declaration()
            payload["forbidden_target_values"] = [3]
            write_json(snapshot, base_snapshot())
            write_json(declaration, payload)

            report = factory.build_report(root, [declaration])

            self.assertEqual(report["blocked_total"], 1)
            self.assertTrue(
                any(blocker.startswith("DECLARATION_CONTAINS_TARGET_VALUE::") for blocker in report["blockers"])
            )

    def test_fails_closed_when_no_send_locks_are_missing_or_weak(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot = root / "snapshots/official.json"
            declaration = root / "declarations/lock.json"
            payload = base_declaration()
            payload["locks"] = {"no_send": True, "publish_allowed": True}
            write_json(snapshot, base_snapshot())
            write_json(declaration, payload)

            report = factory.build_report(root, [declaration])

            self.assertEqual(report["blocked_total"], 1)
            self.assertIn("NO_SEND_LOCK_MISSING_OR_WEAK::publish_allowed", report["blockers"])
            self.assertIn("NO_SEND_LOCK_MISSING_OR_WEAK::push_allowed", report["blockers"])

    def test_fails_closed_on_declared_projection_hash_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot = root / "snapshots/official.json"
            declaration = root / "declarations/lock.json"
            payload = base_declaration()
            payload["expected_target_projection_sha256"] = "not-the-real-target-lock-hash"
            write_json(snapshot, base_snapshot())
            write_json(declaration, payload)

            report = factory.build_report(root, [declaration])

            self.assertEqual(report["blocked_total"], 1)
            self.assertIn("TARGET_PROJECTION_HASH_MISMATCH", report["blockers"])

    def test_ndjson_write_check_and_tamper_detection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot_ref = "snapshots/official.ndjson"
            snapshot = root / snapshot_ref
            declaration = root / "declarations/lock.json"
            write_text(snapshot, "".join(json.dumps(row, sort_keys=True) + "\n" for row in base_snapshot()))
            write_json(declaration, base_declaration(snapshot_ref))

            exit_code = factory.main(
                ["--root", str(root), "--declaration", declaration.relative_to(root).as_posix(), "--write"]
            )
            self.assertEqual(exit_code, 0)
            self.assertEqual(
                factory.main(["--root", str(root), "--declaration", declaration.relative_to(root).as_posix(), "--check"]),
                0,
            )

            visible_lock = root / factory.lock_paths("unit-linear-lock")["visible_lock_ref"]
            tampered = json.loads(visible_lock.read_text(encoding="utf-8"))
            tampered["rows"][0]["visible"]["x"] = 100
            write_json(visible_lock, tampered)

            failures = factory.check_stored(root, [declaration])
            self.assertIn(f"mismatch::{factory.lock_paths('unit-linear-lock')['visible_lock_ref']}", failures)

    def test_materializes_list_length_prediction_from_visible_field(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot = root / "snapshots/ncbi.json"
            declaration = root / "declarations/list_length.json"
            write_json(
                snapshot,
                [{"id": "page-1", "esearchresult": {"idlist": ["11", "12", "13"], "retmax": 3}}],
            )
            write_json(declaration, ncbi_list_length_declaration())

            report, records = factory.build_report_with_locks(root, [declaration])

            self.assertEqual(report["open_blocker_total"], 0)
            self.assertEqual(records[0]["verdict"], "LOCKED_PASS")
            self.assertEqual(
                records[0]["prediction_materialization_lock"]["prediction_rows"][0]["model_prediction"],
                3,
            )

    def test_list_length_fails_closed_when_field_absent_or_not_list(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing_snapshot = root / "snapshots/missing.json"
            scalar_snapshot = root / "snapshots/scalar.json"
            missing_declaration = root / "declarations/list_length_missing.json"
            scalar_declaration = root / "declarations/list_length_scalar.json"
            write_json(missing_snapshot, [{"id": "page-1", "esearchresult": {"retmax": 3}}])
            write_json(scalar_snapshot, [{"id": "page-1", "esearchresult": {"idlist": "11,12,13", "retmax": 3}}])
            write_json(missing_declaration, ncbi_list_length_declaration("snapshots/missing.json"))
            write_json(scalar_declaration, ncbi_list_length_declaration("snapshots/scalar.json"))

            report = factory.build_report(root, [missing_declaration, scalar_declaration])

            self.assertEqual(report["blocked_total"], 2)
            self.assertIn("MODEL_REFERENCES_NON_VISIBLE_FIELD::esearchresult.idlist::row_page-1", report["blockers"])
            self.assertIn("MODEL_FIELD_NOT_LIST::esearchresult.idlist::row_page-1", report["blockers"])

    def test_materializes_chemical_formula_weight_prediction_from_visible_formula(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot = root / "snapshots/pubchem.json"
            declaration = root / "declarations/formula_weight.json"
            write_json(snapshot, [{"CID": 962, "MolecularFormula": "H2O", "MolecularWeight": 18.015}])
            write_json(declaration, pubchem_formula_declaration())

            report, records = factory.build_report_with_locks(root, [declaration])

            self.assertEqual(report["open_blocker_total"], 0)
            self.assertEqual(records[0]["verdict"], "LOCKED_PASS")
            self.assertAlmostEqual(
                records[0]["prediction_materialization_lock"]["prediction_rows"][0]["model_prediction"],
                18.015,
                places=6,
            )

    def test_chemical_formula_weight_allows_hg_public_atomic_weight_target_match(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot = root / "snapshots/pubchem_hg.json"
            declaration = root / "declarations/formula_weight_hg.json"
            payload = pubchem_formula_declaration("snapshots/pubchem_hg.json")
            payload["model_declaration"] = {
                "kind": "chemical_formula_weight",
                "formula_field": "MolecularFormula",
                "atomic_weights": {"Hg": 200.59},
            }
            write_json(snapshot, [{"CID": 23931, "MolecularFormula": "Hg", "MolecularWeight": 200.59}])
            write_json(declaration, payload)

            report, records = factory.build_report_with_locks(root, [declaration])

            self.assertEqual(report["open_blocker_total"], 0)
            self.assertEqual(records[0]["verdict"], "LOCKED_PASS")
            expected_exemption = {
                "path": "$.model_declaration.atomic_weights.Hg",
                "kind": "chemical_formula_weight_public_atomic_weight",
                "table": "model_declaration.atomic_weights",
            }
            self.assertEqual(records[0]["public_constant_exemptions"], [expected_exemption])
            self.assertEqual(records[0]["target_projection_lock"]["public_constant_exemptions"], [expected_exemption])
            self.assertEqual(
                report["public_constant_exemptions"],
                [{"lock_id": "unit-formula-weight-lock", **expected_exemption}],
            )

    def test_chemical_formula_weight_rejects_same_target_value_outside_atomic_weights(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot = root / "snapshots/pubchem_hg.json"
            declaration = root / "declarations/formula_weight_hg_leaky.json"
            payload = pubchem_formula_declaration("snapshots/pubchem_hg.json")
            payload["model_declaration"] = {
                "kind": "chemical_formula_weight",
                "formula_field": "MolecularFormula",
                "atomic_weights": {"Hg": 200.59},
                "leaky_target_value": 200.59,
            }
            write_json(snapshot, [{"CID": 23931, "MolecularFormula": "Hg", "MolecularWeight": 200.59}])
            write_json(declaration, payload)

            report, records = factory.build_report_with_locks(root, [declaration])

            self.assertEqual(report["blocked_total"], 1)
            self.assertIn(
                "DECLARATION_CONTAINS_TARGET_VALUE::$.model_declaration.leaky_target_value",
                report["blockers"],
            )
            self.assertEqual(
                records[0]["public_constant_exemptions"][0]["path"],
                "$.model_declaration.atomic_weights.Hg",
            )

    def test_chemical_formula_weight_invalid_atomic_weights_fail_closed_without_exemption(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot = root / "snapshots/pubchem_hg.json"
            zero_declaration = root / "declarations/formula_weight_hg_zero.json"
            string_declaration = root / "declarations/formula_weight_hg_string.json"
            zero_payload = pubchem_formula_declaration("snapshots/pubchem_hg.json")
            zero_payload["model_declaration"] = {
                "kind": "chemical_formula_weight",
                "formula_field": "MolecularFormula",
                "atomic_weights": {"Hg": 0},
            }
            string_payload = pubchem_formula_declaration("snapshots/pubchem_hg.json")
            string_payload["model_declaration"] = {
                "kind": "chemical_formula_weight",
                "formula_field": "MolecularFormula",
                "atomic_weights": {"Hg": "200.59"},
            }
            write_json(snapshot, [{"CID": 23931, "MolecularFormula": "Hg", "MolecularWeight": 200.59}])
            write_json(zero_declaration, zero_payload)
            write_json(string_declaration, string_payload)

            report, records = factory.build_report_with_locks(root, [zero_declaration, string_declaration])

            self.assertEqual(report["blocked_total"], 2)
            self.assertEqual([record["public_constant_exemptions"] for record in records], [[], []])
            self.assertIn("MODEL_ATOMIC_WEIGHT_NOT_POSITIVE::Hg::row_23931", report["blockers"])

    def test_chemical_formula_weight_fails_closed_on_unknown_element_or_bad_formula(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unknown_snapshot = root / "snapshots/unknown.json"
            bad_snapshot = root / "snapshots/bad.json"
            unknown_declaration = root / "declarations/formula_unknown.json"
            bad_declaration = root / "declarations/formula_bad.json"
            write_json(unknown_snapshot, [{"CID": 1, "MolecularFormula": "Xe2", "MolecularWeight": 263.0}])
            write_json(bad_snapshot, [{"CID": 2, "MolecularFormula": "H2O+", "MolecularWeight": 18.015}])
            write_json(unknown_declaration, pubchem_formula_declaration("snapshots/unknown.json"))
            write_json(bad_declaration, pubchem_formula_declaration("snapshots/bad.json"))

            report = factory.build_report(root, [unknown_declaration, bad_declaration])

            self.assertEqual(report["blocked_total"], 2)
            self.assertIn("MODEL_UNKNOWN_ATOMIC_WEIGHT::Xe::row_1", report["blockers"])
            self.assertIn("MODEL_BAD_CHEMICAL_FORMULA::MolecularFormula::row_2", report["blockers"])

    def test_chemical_formula_weight_fails_closed_when_formula_field_references_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot = root / "snapshots/pubchem.json"
            declaration = root / "declarations/formula_target_ref.json"
            payload = pubchem_formula_declaration()
            payload["model_declaration"] = {
                "kind": "chemical_formula_weight",
                "formula_field": "MolecularWeight",
                "atomic_weights": {"H": 1.008, "O": 15.999},
            }
            write_json(snapshot, [{"CID": 962, "MolecularFormula": "H2O", "MolecularWeight": 18.015}])
            write_json(declaration, payload)

            report = factory.build_report(root, [declaration])

            self.assertEqual(report["blocked_total"], 1)
            self.assertEqual(report["public_constant_exemptions"], [])
            self.assertIn("MODEL_DECLARATION_REFERENCES_TARGET_FIELD::MolecularWeight", report["blockers"])


if __name__ == "__main__":
    unittest.main()
