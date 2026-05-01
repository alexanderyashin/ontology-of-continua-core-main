from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools import oc133_systems_wdi_predictive_search_v2_factory as factory
from validation.grand_science import evidence_pack_factory as grand_factory


REPO_ROOT = Path(__file__).resolve().parents[1]


def write_small_requirements(root: Path, minimum_n: int = 4) -> None:
    path = root / factory.REQUIREMENTS_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_id": "OC133_GRAND_EMPIRICAL_DOMAIN_REQUIREMENTS_v1",
                "release_id": "oc_core_1_3_3",
                "capability_owner": "Research/EmpiricalScience",
                "minimum_per_domain_n": minimum_n,
                "required_domains": ["systems"],
                "required_source_separation_modes": ["prospective", "target_blind"],
                "criteria": {
                    "source_separation_required": True,
                    "target_hidden_until_scoring_required": True,
                    "pre_target_lock_required": True,
                    "comparator_baseline_required": True,
                    "uncertainty_interval_required": True,
                    "residual_superiority_required": True,
                    "negative_control_rejection_required": True,
                    "falsifier_required": True,
                    "grand_toe_support_allowed_must_be_explicit": True,
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )


def source_separation() -> dict[str, object]:
    return {
        "mode": "target_blind",
        "pre_target_lock": True,
        "target_hidden_until_scoring": True,
        "declared_before_scoring": True,
        "lock_id": "mock-wdi-v2-pre-target-lock",
        "lock_timestamp": "2026-04-01T00:00:00Z",
    }


def wdi_payload(values: list[float], *, include_source_separation: bool = True) -> list[object]:
    metadata: dict[str, object] = {
        "page": 1,
        "pages": 1,
        "per_page": 1000,
        "total": len(values),
        "sourceid": "2",
        "lastupdated": "2026-04-08",
    }
    if include_source_separation:
        metadata["oc133_source_separation"] = source_separation()
    rows: list[dict[str, object]] = []
    for offset, value in enumerate(values):
        year = 2000 + offset
        rows.append(
            {
                "indicator": {"id": "NY.GDP.MKTP.CD", "value": "GDP (current US$)"},
                "country": {"id": "TST", "value": "Testland"},
                "countryiso3code": "TST",
                "date": str(year),
                "value": value,
                "unit": "",
                "obs_status": "",
                "decimal": 0,
            }
        )
    return [metadata, rows]


def write_snapshot(root: Path, payload: object, rel_path: str = "validation/heldout/mock_wdi_snapshot.json") -> str:
    path = root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return rel_path


class SystemsWdiPredictiveSearchV2FactoryTests(unittest.TestCase):
    def test_linear_fixture_can_pass_only_when_schema_and_controls_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_small_requirements(root, minimum_n=4)
            snapshot_ref = write_snapshot(root, wdi_payload([100.0 + 5.0 * idx for idx in range(14)]))

            payload = factory.build_payload(root, snapshot_ref=snapshot_ref)
            report = payload["report"]
            pack = payload["candidate_pack"]
            source_lock = payload["source_lock"]
            declaration = payload["source_lock_declaration"]

            self.assertEqual(report["verdict"], "READY_FOR_PARENT_REGISTRY_REVIEW")
            self.assertTrue(report["grand_toe_support_allowed"])
            self.assertEqual(report["strict_schema_failures"], [])
            self.assertEqual(report["exact_failure_rows"], [])
            self.assertEqual(report["source_lock_failures"], [])
            self.assertTrue(source_lock["declared_before_scoring"])
            self.assertTrue(source_lock["declaration_excludes_target_values"])
            self.assertEqual(source_lock["declaration_sha256"], factory.sha256_object(declaration))
            self.assertEqual(
                source_lock["target_row_count"],
                len(declaration["target_rows_declared_before_scoring"]),
            )
            self.assertEqual(report["negative_control_rejected_total"], report["negative_control_total"])
            self.assertEqual(report["formula_search"]["selected_formula_counts"], {"linear_last_slope": report["candidate_n"]})
            self.assertEqual(grand_factory.pack_failure_reasons(pack, factory.load_requirements(root)[0]), [])

    def test_source_lock_tamper_detection_blocks_support(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_small_requirements(root, minimum_n=4)
            snapshot_ref = write_snapshot(root, wdi_payload([100.0 + 5.0 * idx for idx in range(14)]))

            payload = factory.build_payload(root, snapshot_ref=snapshot_ref)
            tampered = json.loads(json.dumps(payload, ensure_ascii=False))
            tampered["source_lock_declaration"]["target_rows_declared_before_scoring"][0]["heldout_year"] = 9999

            failures = factory.strict_schema_failures(tampered)

            self.assertIn("STRICT_SOURCE_LOCK_DECLARATION_HASH_MISMATCH", failures)
            self.assertIn("STRICT_SOURCE_LOCK_DECLARED_TARGET_ROWS_DO_NOT_MATCH_SCORED_ROWS", failures)

            tampered_lock = json.loads(json.dumps(payload, ensure_ascii=False))
            tampered_lock["source_lock"]["candidate_formulas_sha256"] = "0" * 64
            lock_failures = factory.strict_schema_failures(tampered_lock)
            self.assertIn("STRICT_SOURCE_LOCK_CANDIDATE_FORMULAS_HASH_MISMATCH", lock_failures)

    def test_target_mutation_does_not_change_selection_or_prediction(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_small_requirements(root, minimum_n=4)
            raw_payload = wdi_payload([100.0 + 5.0 * idx for idx in range(14)])
            snapshot_ref = write_snapshot(root, raw_payload)

            payload = factory.build_payload(root, snapshot_ref=snapshot_ref)
            rows = payload["tasks"]["rows"]
            self.assertTrue(rows)
            row = rows[-1]
            mutated = factory.mutate_target_value(raw_payload, "TST", "NY.GDP.MKTP.CD", int(row["heldout_year"]), 1000000.0)
            rebuilt = factory.rebuild_matching_row(mutated, snapshot_ref, row)

            self.assertIsNotNone(rebuilt)
            assert rebuilt is not None
            self.assertEqual(rebuilt["selected_formula_id"], row["selected_formula_id"])
            self.assertEqual(rebuilt["predicted_value"], row["predicted_value"])
            self.assertNotEqual(rebuilt["row_hash"], row["row_hash"])
            self.assertTrue(all(year < row["heldout_year"] for year in row["training_years"]))
            for score in row["formula_selection"]["scores"]:
                self.assertTrue(all(year < row["heldout_year"] for year in score["scoring_years"]))
            leakage_test = [
                test
                for test in payload["report"]["tamper_tests"]
                if test["test_id"] == "systems-wdi-predictive-search-v2-selection-target-leakage-control"
            ][0]
            self.assertTrue(leakage_test["passed"])

    def test_negative_control_failure_blocks_with_exact_rows_no_fake_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_small_requirements(root, minimum_n=4)
            snapshot_ref = write_snapshot(root, wdi_payload([100.0 for _ in range(14)]))

            payload = factory.build_payload(root, snapshot_ref=snapshot_ref)
            report = payload["report"]
            pack = payload["candidate_pack"]

            self.assertEqual(report["verdict"], "BLOCKED")
            self.assertFalse(report["grand_toe_support_allowed"])
            self.assertFalse(pack["grand_toe_support_allowed"])
            self.assertTrue(report["exact_failure_rows"])
            self.assertTrue(report["negative_control_failure_rows"])
            self.assertTrue(any("NEGATIVE_CONTROL_NOT_REJECTED" in item for item in report["blockers"]))
            self.assertIn("GRAND_TOE_SUPPORT_NOT_ALLOWED", report["blockers"])
            self.assertEqual(report["valid_pack_total"], 0)

    def test_source_lock_metadata_required_even_when_residuals_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_small_requirements(root, minimum_n=4)
            snapshot_ref = write_snapshot(
                root,
                wdi_payload([100.0 + 5.0 * idx for idx in range(14)], include_source_separation=False),
            )

            report = factory.build_payload(root, snapshot_ref=snapshot_ref)["report"]

            self.assertEqual(report["verdict"], "BLOCKED")
            self.assertFalse(report["grand_toe_support_allowed"])
            self.assertIn("SOURCE_SEPARATION_MODE_NOT_ALLOWED::snapshot_replay", report["blockers"])
            self.assertIn("PRE_TARGET_LOCK_REQUIRED", report["blockers"])
            self.assertIn("DECLARED_BEFORE_SCORING_REQUIRED", report["blockers"])
            self.assertIn("PRE_TARGET_LOCK_ID_REQUIRED", report["blockers"])
            self.assertTrue(any(item.startswith("SOURCE_LOCK_PREDICATE_NOT_TRUE") for item in report["blockers"]))
            self.assertIn("SOURCE_LOCK_EXTERNAL_ID_REQUIRED", report["blockers"])

    def test_official_snapshot_remains_blocked_and_check_outputs_are_deterministic(self) -> None:
        payload = factory.build_payload(REPO_ROOT)
        report = payload["report"]

        self.assertEqual(report["snapshot_ref"], factory.DEFAULT_SNAPSHOT_REF)
        self.assertEqual(report["verdict"], "BLOCKED")
        self.assertFalse(report["grand_toe_support_allowed"])
        self.assertGreaterEqual(report["candidate_n"], 20)
        self.assertEqual(report["negative_control_rejected_total"], report["negative_control_total"])
        self.assertEqual(report["exact_failure_rows"], [])
        self.assertIn("DECLARED_BEFORE_SCORING_REQUIRED", report["blockers"])
        self.assertIn("SOURCE_LOCK_EXTERNAL_ID_REQUIRED", report["blockers"])
        self.assertTrue(report["next_work_orders"])

    def test_official_target_mutation_controls_cover_every_replay_row(self) -> None:
        payload = factory.build_payload(REPO_ROOT)
        report = payload["report"]
        tamper_by_id = {test["test_id"]: test for test in report["tamper_tests"]}

        leakage = tamper_by_id["systems-wdi-predictive-search-v2-selection-target-leakage-control"]
        row_hashes = tamper_by_id["systems-wdi-predictive-search-v2-target-mutation-changes-row-hashes"]
        payload_hashes = tamper_by_id["systems-wdi-predictive-search-v2-target-mutation-changes-payload-hashes"]

        self.assertEqual(leakage["sample_total"], report["candidate_n"])
        self.assertEqual(row_hashes["sample_total"], report["candidate_n"])
        self.assertEqual(payload_hashes["sample_total"], report["candidate_n"])
        self.assertTrue(leakage["passed"])
        self.assertTrue(row_hashes["passed"])
        self.assertTrue(payload_hashes["passed"])
        self.assertEqual(leakage["failed_observation_ids"], [])

    def test_write_outputs_materializes_only_v2_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_small_requirements(root, minimum_n=4)
            snapshot_ref = write_snapshot(root, wdi_payload([100.0 + 5.0 * idx for idx in range(14)]))

            payload = factory.write_outputs(root, snapshot_ref=snapshot_ref)

            self.assertTrue(payload["report"]["grand_toe_support_allowed"])
            self.assertEqual(factory.check_stored(root, snapshot_ref=snapshot_ref), [])
            output_root = root / factory.OUTPUT_ROOT_REL
            self.assertEqual(
                sorted(path.name for path in output_root.iterdir()),
                sorted(
                    [
                        "OC133_SYSTEMS_WDI_PREDICTIVE_SEARCH_V2_CANDIDATE_PACK.json",
                        "OC133_SYSTEMS_WDI_PREDICTIVE_SEARCH_V2_PROTOCOL.json",
                        "OC133_SYSTEMS_WDI_PREDICTIVE_SEARCH_V2_REPORT.json",
                        "OC133_SYSTEMS_WDI_PREDICTIVE_SEARCH_V2_SOURCE_LOCK.json",
                        "OC133_SYSTEMS_WDI_PREDICTIVE_SEARCH_V2_SOURCE_LOCK_DECLARATION.json",
                        "OC133_SYSTEMS_WDI_PREDICTIVE_SEARCH_V2_TASKS.json",
                        "README.md",
                    ]
                ),
            )


if __name__ == "__main__":
    raise SystemExit(unittest.main())
